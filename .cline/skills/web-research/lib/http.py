"""Shared HTTP GET: realistic headers, automatic SSL-verify fallback, retry with backoff.

Optional proxy: set the WEB_RESEARCH_PROXY (or standard HTTPS_PROXY) environment variable, or pass
--proxy on the CLI. The proxy is applied to requests, curl_cffi, and Playwright alike.

By default fetches to private/loopback/link-local IPs are refused (SSRF guard); pass --allow-local
to permit them (e.g. to read an internal dev server).
"""
import ipaddress
import logging
import os
import socket
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


# SSRF guard: refuse private/loopback/link-local targets unless explicitly allowed.
_allow_local = False


class BlockedURLError(RuntimeError):
    """Raised when a URL resolves to a private/loopback address and --allow-local was not set."""


def set_allow_local(value):
    global _allow_local
    _allow_local = bool(value)


def _is_public_ip(ip_str):
    try:
        ip = ipaddress.ip_address(ip_str)
    except ValueError:
        return False
    return not (
        ip.is_private or ip.is_loopback or ip.is_link_local
        or ip.is_reserved or ip.is_multicast or ip.is_unspecified
    )


def assert_allowed(url):
    """Raise BlockedURLError if the URL host resolves only to non-public addresses."""
    if _allow_local:
        return
    host = urlparse(url).hostname
    if not host:
        return
    try:
        addresses = {info[4][0] for info in socket.getaddrinfo(host, None)}
    except socket.gaierror:
        return  # let the real request surface a normal DNS error
    if addresses and not any(_is_public_ip(addr) for addr in addresses):
        raise BlockedURLError(
            f"Refusing to fetch {host} -> {sorted(addresses)} (private/loopback address). "
            "Use --allow-local to override."
        )


def get(url, timeout=30, retries=3):
    """GET a URL, returning a requests.Response. Retries connection/timeout errors with backoff."""
    assert_allowed(url)
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
