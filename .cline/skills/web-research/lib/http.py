"""Shared HTTP GET: realistic headers, automatic SSL-verify fallback, retry with backoff.

Optional proxy: set the WEB_RESEARCH_PROXY (or standard HTTPS_PROXY) environment variable, or pass
--proxy on the CLI. The proxy is applied to requests, curl_cffi, and Playwright alike.
"""
import logging
import os
import time
from urllib.parse import urlparse

import requests

logger = logging.getLogger("web-research.http")

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9,vi;q=0.8",
}

# Disabled automatically on the first SSLError (common behind corporate proxies).
_verify_ssl = True

# Explicit proxy set from the CLI (--proxy); overrides environment variables when present.
_proxy_override = None


def set_proxy(url):
    """Set an explicit proxy URL (CLI). Pass a falsy value to clear it."""
    global _proxy_override
    _proxy_override = url or None


def current_proxy():
    """Return the active proxy URL: CLI override, then WEB_RESEARCH_PROXY / HTTPS_PROXY env."""
    return (
        _proxy_override
        or os.environ.get("WEB_RESEARCH_PROXY")
        or os.environ.get("HTTPS_PROXY")
        or os.environ.get("https_proxy")
        or None
    )


def _requests_proxies():
    proxy = current_proxy()
    return {"http": proxy, "https": proxy} if proxy else None


def playwright_proxy():
    """Return a Playwright proxy dict ({server[, username, password]}) or None."""
    proxy = current_proxy()
    if not proxy:
        return None
    parsed = urlparse(proxy if "://" in proxy else "http://" + proxy)
    server = f"{parsed.scheme}://{parsed.hostname}" + (f":{parsed.port}" if parsed.port else "")
    config = {"server": server}
    if parsed.username:
        config["username"] = parsed.username
        config["password"] = parsed.password or ""
    return config


def get(url, timeout=30, retries=3):
    """GET a URL, returning a requests.Response. Retries connection/timeout errors with backoff."""
    global _verify_ssl
    last_error = None
    for attempt in range(1, retries + 1):
        try:
            resp = requests.get(
                url, headers=DEFAULT_HEADERS, timeout=timeout,
                allow_redirects=True, verify=_verify_ssl, proxies=_requests_proxies(),
            )
            resp.raise_for_status()
            return resp
        except requests.exceptions.SSLError as e:
            if _verify_ssl:
                logger.warning("SSL verification failed for %s; retrying without verification.", url)
                _verify_ssl = False
                continue
            last_error = e
            break
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
            last_error = e
            if attempt < retries:
                wait = attempt * 2
                logger.warning("Attempt %d/%d failed for %s: %s. Retrying in %ds.",
                               attempt, retries, url, e, wait)
                time.sleep(wait)
                continue
            break
        except requests.exceptions.HTTPError:
            raise
    raise last_error
