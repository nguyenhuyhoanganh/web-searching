#!/usr/bin/env python3
"""Search the web (DDGS API, with DuckDuckGo/Google HTML fallback). Optionally fetch full content.

Examples:
    python web_search.py "Spring Boot latest version Java 21" -n 5
    python web_search.py "<query>" --news --region vn-vi
    python web_search.py "<query>" --fetch --fetch-count 3
"""
import argparse
import json
import logging
import os
import sys
import textwrap
from urllib.parse import quote_plus

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if SKILL_DIR not in sys.path:
    sys.path.insert(0, SKILL_DIR)

from bs4 import BeautifulSoup  # noqa: E402

from lib import engines, extract, http  # noqa: E402

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s", stream=sys.stderr)
logger = logging.getLogger("web-research.search")

try:
    from ddgs import DDGS
    HAS_DDGS = True
except ImportError:
    HAS_DDGS = False
    logger.warning("Package 'ddgs' not installed — using HTML scraping fallback. Install: pip install ddgs")


def _ddgs_text(query, max_results, region):
    with DDGS() as ddgs:
        rows = list(ddgs.text(query, region=region, max_results=max_results))
    return [{"title": r.get("title", ""), "url": r.get("href", ""), "snippet": r.get("body", "")}
            for r in rows]


def _ddgs_news(query, max_results, region):
    with DDGS() as ddgs:
        rows = list(ddgs.news(query, region=region, max_results=max_results))
    return [{"title": r.get("title", ""), "url": r.get("url", ""), "snippet": r.get("body", ""),
             "date": r.get("date", ""), "source": r.get("source", "")} for r in rows]


def _duckduckgo_html(query, max_results):
    resp = http.get(f"https://html.duckduckgo.com/html/?q={quote_plus(query)}")
    soup = BeautifulSoup(resp.text, "html.parser")
    out = []
    for div in soup.select("div.result"):
        a = div.find("a", class_="result__a")
        if not a:
            continue
        snip = div.find("a", class_="result__snippet")
        if a.get_text(strip=True) and a.get("href"):
            out.append({"title": a.get_text(strip=True), "url": a["href"],
                        "snippet": snip.get_text(strip=True) if snip else ""})
        if len(out) >= max_results:
            break
    return out


def _google_html(query, max_results):
    resp = http.get(f"https://www.google.com/search?q={quote_plus(query)}&num={max_results}")
    soup = BeautifulSoup(resp.text, "html.parser")
    out = []
    for g in soup.select("div.g, div[data-sokoban-container]"):
        a = g.find("a", href=True)
        h3 = g.find("h3")
        if not a or not a["href"].startswith("http") or not h3:
            continue
        snip = g.find("div", class_="VwiC3b") or g.find("span", class_="aCOpRe")
        out.append({"title": h3.get_text(strip=True), "url": a["href"],
                    "snippet": snip.get_text(strip=True) if snip else ""})
        if len(out) >= max_results:
            break
    return out


def search_web(query, max_results=5, region="wt-wt", news=False):
    errors = []
    if HAS_DDGS:
        try:
            return _ddgs_news(query, max_results, region) if news else _ddgs_text(query, max_results, region)
        except Exception as e:
            errors.append(f"DDGS: {e}")
            logger.warning("DDGS failed: %s", e)
    for name, fn in (("DDG-HTML", _duckduckgo_html), ("Google-HTML", _google_html)):
        try:
            return fn(query, max_results)
        except Exception as e:
            errors.append(f"{name}: {e}")
            logger.warning("%s failed: %s", name, e)
    raise RuntimeError("All search backends failed: " + "; ".join(errors))


def _attach_content(results, count):
    for r in results[:count]:
        try:
            page = engines.get_html(r["url"], render="auto")
            doc = extract.to_document(page["html"], r["url"], fmt="markdown")
            content, _ = extract.truncate(doc["content"], 5000)
            r["content"] = content
        except Exception as e:
            r["content"] = f"[could not fetch: {e}]"
    return results


def format_results(results, as_json):
    if as_json:
        return json.dumps(results, ensure_ascii=False, indent=2)
    if not results:
        return "No results found."
    out = []
    for i, r in enumerate(results, 1):
        out.append(f"[{i}] {r.get('title', 'N/A')}")
        if r.get("url"):
            out.append(f"    URL: {r['url']}")
        if r.get("snippet"):
            out.append(textwrap.fill(r["snippet"], 100, initial_indent="    ", subsequent_indent="    "))
        if r.get("date"):
            out.append(f"    Date: {r['date']}")
        if r.get("content"):
            out.append("    --- content ---")
            out.append(textwrap.indent(r["content"], "    "))
        out.append("")
    return "\n".join(out)


def main():
    parser = argparse.ArgumentParser(description="Web search.")
    parser.add_argument("query")
    parser.add_argument("--max-results", "-n", type=int, default=5)
    parser.add_argument("--region", "-r", default="wt-wt")
    parser.add_argument("--news", action="store_true")
    parser.add_argument("--fetch", "--scrape", action="store_true", dest="fetch",
                        help="Fetch full Markdown content of the top results")
    parser.add_argument("--fetch-count", type=int, default=3)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    try:
        results = search_web(args.query, args.max_results, args.region, args.news)
        if args.fetch:
            results = _attach_content(results, args.fetch_count)
        print(format_results(results, args.json))
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
