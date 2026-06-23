#!/usr/bin/env python3
"""Crawl pages within one domain (bounded) and output Markdown for each.

Examples:
    python web_crawl.py "https://docs.example.com/guide" --max-pages 15 --max-depth 2
    python web_crawl.py "https://example.com" --search api --format json
"""
import argparse
import json
import os
import sys
import time
from collections import deque
from urllib.parse import urlparse

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if SKILL_DIR not in sys.path:
    sys.path.insert(0, SKILL_DIR)

from lib import engines, env, extract  # noqa: E402

env.force_utf8()


def _same_site(url, host, include_subdomains):
    netloc = urlparse(url).netloc.lower()
    if include_subdomains:
        return netloc == host or netloc.endswith("." + host)
    return netloc == host


def crawl(start_url, max_pages=20, max_depth=2, include_subdomains=False,
          search=None, render="never", delay_ms=0):
    host = urlparse(start_url).netloc.lower()
    queue = deque([(start_url, 0)])
    seen = {start_url}
    pages = []
    while queue and len(pages) < max_pages:
        url, depth = queue.popleft()
        try:
            result = engines.get_html(url, render=render)
        except Exception as e:
            pages.append({"url": url, "title": "", "markdown": f"[error: {e}]"})
            continue
        doc = extract.to_document(result["html"], url, fmt="markdown")
        if not search or search.lower() in (doc.get("content", "") + url).lower():
            pages.append({"url": url, "title": doc.get("title", ""), "markdown": doc.get("content", "")})
        if depth < max_depth:
            for link in extract.extract_links(result["html"], url):
                nxt = link["url"].split("#")[0]
                if nxt not in seen and _same_site(nxt, host, include_subdomains):
                    seen.add(nxt)
                    queue.append((nxt, depth + 1))
        if delay_ms:
            time.sleep(delay_ms / 1000)
    return pages


def main():
    parser = argparse.ArgumentParser(description="Bounded same-domain crawl to Markdown.")
    parser.add_argument("url")
    parser.add_argument("--max-pages", type=int, default=20)
    parser.add_argument("--max-depth", type=int, default=2)
    parser.add_argument("--include-subdomains", action="store_true")
    parser.add_argument("--search", help="Only keep pages whose URL/content contains this substring")
    parser.add_argument("--render", choices=["auto", "never", "always"], default="never")
    parser.add_argument("--delay", type=int, default=0, help="Delay between requests (ms)")
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    args = parser.parse_args()
    try:
        pages = crawl(args.url, args.max_pages, args.max_depth, args.include_subdomains,
                      args.search, args.render, args.delay)
        if args.format == "json":
            print(json.dumps(pages, ensure_ascii=False, indent=2))
        else:
            for p in pages:
                print(f"\n{'=' * 80}\n# {p['title'] or p['url']}\nURL: {p['url']}\n{'=' * 80}")
                print(p["markdown"])
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
