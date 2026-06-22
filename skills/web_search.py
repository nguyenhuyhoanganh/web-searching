#!/usr/bin/env python3
"""
Web Search Skill for Cline
Tìm kiếm thông tin trên web sử dụng DuckDuckGo (không cần API key).
Có fallback qua Google HTML search nếu DuckDuckGo bị rate-limit.

Usage:
    python web_search.py "query" [--max-results N] [--region vn-vi]
    python web_search.py "query" --news
    python web_search.py "query" --answers

Examples:
    python web_search.py "Python asyncio tutorial"
    python web_search.py "latest Spring Boot release" --max-results 10
    python web_search.py "Vietnam tech news" --news --region vn-vi
"""

import argparse
import json
import sys
import textwrap
from urllib.parse import quote_plus, urljoin

import requests
from bs4 import BeautifulSoup

try:
    from ddgs import DDGS
    HAS_DDGS = True
except ImportError:
    HAS_DDGS = False

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


def _search_ddgs(query: str, max_results: int, region: str) -> list[dict]:
    with DDGS() as ddgs:
        results = list(ddgs.text(query, region=region, max_results=max_results))
    return [
        {"title": r.get("title", ""), "url": r.get("href", ""), "snippet": r.get("body", "")}
        for r in results
    ]


def _search_ddgs_news(query: str, max_results: int, region: str) -> list[dict]:
    with DDGS() as ddgs:
        results = list(ddgs.news(query, region=region, max_results=max_results))
    return [
        {
            "title": r.get("title", ""),
            "url": r.get("url", ""),
            "snippet": r.get("body", ""),
            "date": r.get("date", ""),
            "source": r.get("source", ""),
        }
        for r in results
    ]


def _search_ddgs_answers(query: str) -> list[dict]:
    with DDGS() as ddgs:
        results = list(ddgs.answers(query))
    return [
        {"text": r.get("text", ""), "url": r.get("url", ""), "source": r.get("source", "")}
        for r in results
    ]


def _search_google_fallback(query: str, max_results: int) -> list[dict]:
    """Fallback: parse Google search HTML khi DuckDuckGo bị rate-limit."""
    url = f"https://www.google.com/search?q={quote_plus(query)}&num={max_results}"
    resp = requests.get(url, headers=DEFAULT_HEADERS, timeout=15)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    results = []
    for g in soup.select("div.g, div[data-sokoban-container]"):
        link = g.find("a", href=True)
        if not link:
            continue
        href = link["href"]
        if not href.startswith("http"):
            continue
        title_el = g.find("h3")
        title = title_el.get_text(strip=True) if title_el else ""
        snippet_el = g.find("div", class_="VwiC3b") or g.find("span", class_="aCOpRe")
        snippet = snippet_el.get_text(strip=True) if snippet_el else ""
        if title:
            results.append({"title": title, "url": href, "snippet": snippet})
        if len(results) >= max_results:
            break

    return results


def _search_duckduckgo_html_fallback(query: str, max_results: int) -> list[dict]:
    """Fallback: parse DuckDuckGo HTML search."""
    url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
    resp = requests.get(url, headers=DEFAULT_HEADERS, timeout=15)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    results = []
    for result_div in soup.select("div.result"):
        link = result_div.find("a", class_="result__a")
        if not link:
            continue
        title = link.get_text(strip=True)
        href = link.get("href", "")
        snippet_el = result_div.find("a", class_="result__snippet")
        snippet = snippet_el.get_text(strip=True) if snippet_el else ""
        if title and href:
            results.append({"title": title, "url": href, "snippet": snippet})
        if len(results) >= max_results:
            break

    return results


def search_web(query: str, max_results: int = 5, region: str = "wt-wt") -> list[dict]:
    errors = []

    if HAS_DDGS:
        try:
            return _search_ddgs(query, max_results, region)
        except Exception as e:
            errors.append(f"DDGS: {e}")

    try:
        return _search_duckduckgo_html_fallback(query, max_results)
    except Exception as e:
        errors.append(f"DDG HTML: {e}")

    try:
        return _search_google_fallback(query, max_results)
    except Exception as e:
        errors.append(f"Google: {e}")

    raise RuntimeError(f"Tất cả phương thức tìm kiếm đều thất bại: {'; '.join(errors)}")


def search_news(query: str, max_results: int = 5, region: str = "wt-wt") -> list[dict]:
    if HAS_DDGS:
        try:
            return _search_ddgs_news(query, max_results, region)
        except Exception as e:
            pass

    return search_web(f"{query} news", max_results, region)


def search_answers(query: str) -> list[dict]:
    if HAS_DDGS:
        try:
            return _search_ddgs_answers(query)
        except Exception:
            pass
    return search_web(query, 3)


def format_results(results: list[dict], mode: str = "text") -> str:
    if mode == "json":
        return json.dumps(results, ensure_ascii=False, indent=2)

    if not results:
        return "Không tìm thấy kết quả nào."

    output = []
    for i, r in enumerate(results, 1):
        output.append(f"[{i}] {r.get('title', r.get('text', 'N/A'))}")
        url = r.get("url", "")
        if url:
            output.append(f"    URL: {url}")
        snippet = r.get("snippet", r.get("text", ""))
        if snippet:
            wrapped = textwrap.fill(snippet, width=100, initial_indent="    ", subsequent_indent="    ")
            output.append(wrapped)
        if r.get("date"):
            output.append(f"    Date: {r['date']}")
        if r.get("source"):
            output.append(f"    Source: {r['source']}")
        output.append("")
    return "\n".join(output)


def main():
    parser = argparse.ArgumentParser(description="Web Search Skill for Cline")
    parser.add_argument("query", help="Search query")
    parser.add_argument("--max-results", "-n", type=int, default=5, help="Number of results (default: 5)")
    parser.add_argument("--region", "-r", default="wt-wt", help="Region code, e.g. vn-vi, us-en (default: wt-wt)")
    parser.add_argument("--news", action="store_true", help="Search news instead of web")
    parser.add_argument("--answers", action="store_true", help="Get instant answers")
    parser.add_argument("--json", action="store_true", help="Output as JSON")

    args = parser.parse_args()
    output_mode = "json" if args.json else "text"

    try:
        if args.answers:
            results = search_answers(args.query)
        elif args.news:
            results = search_news(args.query, args.max_results, args.region)
        else:
            results = search_web(args.query, args.max_results, args.region)

        print(format_results(results, output_mode))
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
