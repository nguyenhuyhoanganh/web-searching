#!/usr/bin/env python3
"""Discover URLs of a website from its sitemap(s) and homepage links.

Examples:
    python web_map.py "https://docs.python.org" --limit 100
    python web_map.py "https://example.com" --search blog --json
"""
import argparse
import gzip
import json
import os
import re
import sys
from urllib.parse import urljoin, urlparse

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if SKILL_DIR not in sys.path:
    sys.path.insert(0, SKILL_DIR)

from lib import env, extract, http  # noqa: E402

env.force_utf8()

_LOC_RE = re.compile(r"<loc>\s*([^<\s]+)\s*</loc>", re.I)
_SITEMAP_RE = re.compile(r"(?im)^\s*Sitemap:\s*(\S+)\s*$")
_MAX_SITEMAPS = 20


def _sitemaps_from_robots(text):
    """Return the sitemap URLs listed in a robots.txt body (Sitemap: directives)."""
    return _SITEMAP_RE.findall(text or "")


def _decode_sitemap(content_bytes, url):
    """Decode sitemap bytes to text, gunzipping when the URL ends in .gz."""
    if url.lower().endswith(".gz"):
        content_bytes = gzip.decompress(content_bytes)
    return content_bytes.decode("utf-8", "replace")


def _sitemap_text(url):
    return _decode_sitemap(http.get(url).content, url)


def _same_site(url, host, include_subdomains):
    netloc = urlparse(url).netloc.lower()
    if include_subdomains:
        return netloc == host or netloc.endswith("." + host)
    return netloc == host


def _collect_sitemap(start_url, host, include_subdomains, seen_maps):
    """Recursively read sitemap.xml / sitemap indexes, returning page URLs."""
    if start_url in seen_maps or len(seen_maps) >= _MAX_SITEMAPS:
        return []
    seen_maps.add(start_url)
    try:
        text = _sitemap_text(start_url)
    except Exception:
        return []
    locs = _LOC_RE.findall(text)
    pages, nested = [], []
    for loc in locs:
        (nested if loc.lower().endswith(".xml") else pages).append(loc)
    for nested_map in nested:
        pages.extend(_collect_sitemap(nested_map, host, include_subdomains, seen_maps))
    return [u for u in pages if _same_site(u, host, include_subdomains)]


def map_site(start_url, include_subdomains=False, limit=200, search=None):
    parsed = urlparse(start_url)
    host = parsed.netloc.lower()
    origin = f"{parsed.scheme}://{parsed.netloc}"
    urls, seen = [], set()

    def add(u):
        if u not in seen and _same_site(u, host, include_subdomains):
            if not search or search.lower() in u.lower():
                seen.add(u)
                urls.append(u)

    sitemap_roots = [urljoin(origin, "/sitemap.xml")]
    try:
        sitemap_roots += _sitemaps_from_robots(http.get(urljoin(origin, "/robots.txt")).text)
    except Exception:
        pass
    seen_maps = set()
    for root in sitemap_roots:
        for u in _collect_sitemap(root, host, include_subdomains, seen_maps):
            add(u)
    try:
        home = http.get(start_url)
        for link in extract.extract_links(home.text, start_url):
            add(link["url"])
    except Exception:
        pass
    return urls[:limit]


def main():
    parser = argparse.ArgumentParser(description="Map a website's URLs.")
    parser.add_argument("url")
    parser.add_argument("--search", help="Only keep URLs containing this substring")
    parser.add_argument("--limit", type=int, default=200)
    parser.add_argument("--include-subdomains", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    try:
        urls = map_site(args.url, args.include_subdomains, args.limit, args.search)
        if args.json:
            print(json.dumps(urls, ensure_ascii=False, indent=2))
        else:
            print(f"Found {len(urls)} URL(s):")
            for u in urls:
                print(f"  {u}")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
