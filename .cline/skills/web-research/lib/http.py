"""Shared HTTP GET: realistic headers, automatic SSL-verify fallback, retry with backoff."""
import logging
import time

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


def get(url, timeout=30, retries=3):
    """GET a URL, returning a requests.Response. Retries connection/timeout errors with backoff."""
    global _verify_ssl
    last_error = None
    for attempt in range(1, retries + 1):
        try:
            resp = requests.get(
                url, headers=DEFAULT_HEADERS, timeout=timeout,
                allow_redirects=True, verify=_verify_ssl,
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
