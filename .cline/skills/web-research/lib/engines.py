"""Page-fetching engines and selection.

- fetch_html: static fetch via requests (lib.http).
- render_html: JS rendering + optional actions via Playwright (optional dependency).
- get_html: chooses an engine ("auto"/"never"/"always") with graceful fallback.
"""
import importlib.util
import logging

import requests

from lib import http

logger = logging.getLogger("web-research.engines")

# Heuristic: below this many chars of visible text, an auto fetch may be a JS shell.
_JS_TEXT_THRESHOLD = 200


class RenderUnavailable(RuntimeError):
    """Raised when Playwright rendering is requested but the package is not installed."""


class ImpersonateUnavailable(RuntimeError):
    """Raised when TLS impersonation is requested but curl_cffi is not installed."""


def _playwright_installed():
    return importlib.util.find_spec("playwright") is not None


def _curl_cffi_installed():
    return importlib.util.find_spec("curl_cffi") is not None


def _fetch_with_curl(url):
    """Fetch with curl_cffi impersonating a real Chrome TLS/HTTP2 fingerprint (bypasses many blocks)."""
    from curl_cffi import requests as cffi_requests
    proxy = http.current_proxy()
    proxies = {"http": proxy, "https": proxy} if proxy else None
    resp = cffi_requests.get(
        url, impersonate="chrome", timeout=30, allow_redirects=True,
        headers={"Accept-Language": "en-US,en;q=0.9"}, proxies=proxies,
    )
    resp.raise_for_status()
    return {
        "html": resp.text,
        "final_url": str(resp.url),
        "content_type": resp.headers.get("Content-Type", ""),
        "content_bytes": resp.content,
        "engine_used": "curl_cffi",
    }


def fetch_html(url, impersonate=False):
    """Static fetch. With impersonate=True use curl_cffi; otherwise requests, auto-falling back to
    curl_cffi on a 403/429 (likely bot-block) when it is installed."""
    if impersonate:
        if not _curl_cffi_installed():
            raise ImpersonateUnavailable(
                "TLS impersonation needs curl_cffi. Install it with:  pip install curl_cffi"
            )
        return _fetch_with_curl(url)
    try:
        resp = http.get(url)
    except requests.exceptions.HTTPError as e:
        status = getattr(e.response, "status_code", None)
        if status in (403, 429) and _curl_cffi_installed():
            logger.info("HTTP %s for %s; retrying with curl_cffi impersonation.", status, url)
            return _fetch_with_curl(url)
        raise
    resp.encoding = resp.apparent_encoding or "utf-8"
    return {
        "html": resp.text,
        "final_url": str(resp.url),
        "content_type": resp.headers.get("Content-Type", ""),
        "content_bytes": resp.content,
        "engine_used": "fetch",
    }


def _run_actions(page, actions):
    for act in actions or []:
        kind = act.get("type")
        if kind == "click":
            page.click(act["selector"])
        elif kind == "write":
            page.fill(act["selector"], act.get("text", ""))
        elif kind == "press":
            page.keyboard.press(act["key"])
        elif kind == "scroll":
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        elif kind == "wait":
            if act.get("selector"):
                page.wait_for_selector(act["selector"])
            else:
                page.wait_for_timeout(int(act.get("ms", 1000)))


def render_html(url, wait_for=None, scroll=0, actions=None, screenshot=None, timeout_ms=30000):
    if not _playwright_installed():
        raise RenderUnavailable(
            "JS rendering needs Playwright. Install it with:  "
            "pip install playwright  &&  playwright install chromium"
        )
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, proxy=http.playwright_proxy())
        try:
            page = browser.new_page(user_agent=http.DEFAULT_HEADERS["User-Agent"])
            page.goto(url, wait_until="networkidle", timeout=timeout_ms)
            if wait_for:
                page.wait_for_selector(wait_for, timeout=timeout_ms)
            for _ in range(scroll):
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                page.wait_for_timeout(800)
            _run_actions(page, actions)
            if screenshot:
                page.screenshot(path=screenshot, full_page=True)
            html = page.content()
            final_url = page.url
        finally:
            browser.close()
    return {
        "html": html, "final_url": final_url, "content_type": "text/html",
        "content_bytes": html.encode("utf-8", "ignore"), "engine_used": "playwright",
    }


def _visible_text_len(html):
    from lib import extract
    return len(extract.to_document(html, "", fmt="text")["content"])


def get_html(url, render="auto", wait_for=None, scroll=0, actions=None,
             screenshot=None, timeout_ms=30000, impersonate=False):
    """Return a fetch/render result dict plus 'suggest_render' (True if a render would likely help).

    render: "never" (fetch only), "always" (render), "auto" (fetch, render if it looks JS-gated).
    impersonate: use curl_cffi (real Chrome TLS fingerprint) for the static fetch.
    """
    if render == "always" or actions or wait_for or screenshot:
        result = render_html(url, wait_for, scroll, actions, screenshot, timeout_ms)
        result["suggest_render"] = False
        return result

    fetched = fetch_html(url, impersonate=impersonate)
    if render == "never":
        fetched["suggest_render"] = False
        return fetched

    # auto
    looks_thin = _visible_text_len(fetched["html"]) < _JS_TEXT_THRESHOLD
    if looks_thin and _playwright_installed():
        try:
            rendered = render_html(url, scroll=scroll, timeout_ms=timeout_ms)
            rendered["suggest_render"] = False
            return rendered
        except Exception as e:  # fall back to the fetched HTML
            logger.warning("Render fallback failed for %s: %s", url, e)
    fetched["suggest_render"] = looks_thin and not _playwright_installed()
    return fetched
