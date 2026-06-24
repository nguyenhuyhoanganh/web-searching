#!/usr/bin/env python3
"""Read a URL and output clean Markdown (or text/JSON). Renders JS pages and parses PDFs.

Examples:
    python web_read.py "https://docs.python.org/3/library/asyncio.html"
    python web_read.py "<url>" --render always --scroll 3
    python web_read.py "<url>" --links
    python web_read.py "<url>" --selector "article" --format text
"""
import argparse
import json
import os
import sys

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if SKILL_DIR not in sys.path:
    sys.path.insert(0, SKILL_DIR)

from lib import engines, env, extract, http, pdf  # noqa: E402

env.force_utf8()

MAX_CONTENT_LENGTH = 50_000


def _format_doc(doc, output_json, suggest_render):
    if output_json:
        return json.dumps(doc, ensure_ascii=False, indent=2)
    out = []
    for key in ("title", "author", "date", "sitename", "language", "keywords"):
        if doc.get(key):
            out.append(f"{key.capitalize()}: {doc[key]}")
    out.append(f"URL: {doc.get('url', '')}")
    out.append(f"Extraction: {doc.get('method', 'unknown')}")
    out.append("-" * 80)
    out.append(doc.get("content", "No content."))
    if doc.get("truncated"):
        out.append("\n[content was truncated]")
    if suggest_render:
        out.append("\n[note] This page returned little content and may be JavaScript-rendered. "
                   "Rendering with Playwright would likely return the full page.")
    return "\n".join(out)


def main():
    parser = argparse.ArgumentParser(description="Read a web page as Markdown.")
    parser.add_argument("url")
    parser.add_argument("--format", choices=["markdown", "text", "json"], default="markdown")
    parser.add_argument("--render", choices=["auto", "never", "always"], default="auto")
    parser.add_argument("--js", action="store_true", help="Alias for --render always")
    parser.add_argument("--wait-for", help="CSS selector to wait for (implies render)")
    parser.add_argument("--scroll", type=int, default=0, help="Scroll-to-bottom passes (lazy load)")
    parser.add_argument("--actions", help="JSON list of Playwright actions")
    parser.add_argument("--selector", "-s", help="CSS selector (forces plain-text extraction)")
    parser.add_argument("--max-length", "-m", type=int, default=MAX_CONTENT_LENGTH)
    parser.add_argument("--links", action="store_true", help="List links instead of content")
    parser.add_argument("--screenshot", help="Save a full-page screenshot to this path (needs render)")
    parser.add_argument("--impersonate", action="store_true",
                        help="Use curl_cffi (real Chrome TLS fingerprint) to bypass TLS-based bot blocks")
    parser.add_argument("--raw", action="store_true", help="BeautifulSoup plain text only")
    parser.add_argument("--proxy", help="Proxy URL (e.g. http://host:port); or set WEB_RESEARCH_PROXY")
    parser.add_argument("--allow-local", action="store_true",
                        help="Allow fetching private/loopback addresses (default: refuse)")
    parser.add_argument("--json", action="store_true", help="Output JSON")
    args = parser.parse_args()
    http.set_proxy(args.proxy)
    http.set_allow_local(args.allow_local)

    render = "always" if args.js else args.render
    actions = json.loads(args.actions) if args.actions else None

    try:
        result = engines.get_html(
            args.url, render=render, wait_for=args.wait_for, scroll=args.scroll,
            actions=actions, screenshot=args.screenshot, impersonate=args.impersonate,
        )
    except (engines.RenderUnavailable, engines.ImpersonateUnavailable) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(2)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    html = result["html"]
    url = result.get("final_url", args.url)

    if args.links:
        links = extract.extract_links(html, url)
        if args.json:
            print(json.dumps(links, ensure_ascii=False, indent=2))
        else:
            print("No links found." if not links else
                  "\n".join(f"[{i}] {l['text']}\n    {l['url']}" for i, l in enumerate(links, 1)))
        return

    if pdf.looks_like_pdf(url, result.get("content_type", ""), result.get("content_bytes", b"")):
        try:
            doc = pdf.extract_pdf(result["content_bytes"])
            doc["method"] = "pdf"
        except RuntimeError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(2)
    else:
        fmt = "text" if args.raw else args.format
        doc = extract.to_document(html, url, fmt=fmt, selector=args.selector)

    doc["url"] = url
    doc["content"], doc["truncated"] = extract.truncate(doc.get("content", ""), args.max_length)
    print(_format_doc(doc, args.json or args.format == "json", result.get("suggest_render", False)))


if __name__ == "__main__":
    main()
