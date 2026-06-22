#!/usr/bin/env python3
"""
Web Read Skill for Cline
Đọc và trích xuất nội dung chính từ trang web.

Usage:
    python web_read.py "https://example.com"
    python web_read.py "https://example.com" --raw
    python web_read.py "https://example.com" --max-length 5000
    python web_read.py "https://example.com" --selector "article"

Examples:
    python web_read.py "https://docs.python.org/3/library/asyncio.html"
    python web_read.py "https://spring.io/blog" --max-length 3000
    python web_read.py "https://example.com" --selector "div.content" --raw
"""

import argparse
import json
import re
import sys
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

try:
    import trafilatura
    HAS_TRAFILATURA = True
except ImportError:
    HAS_TRAFILATURA = False

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9,vi;q=0.8",
}

MAX_CONTENT_LENGTH = 50_000


def fetch_page(url: str, timeout: int = 30) -> str:
    response = requests.get(url, headers=DEFAULT_HEADERS, timeout=timeout, allow_redirects=True)
    response.raise_for_status()
    response.encoding = response.apparent_encoding or "utf-8"
    return response.text


def extract_with_trafilatura(html: str, url: str) -> dict | None:
    if not HAS_TRAFILATURA:
        return None
    result = trafilatura.extract(
        html, url=url, include_links=True, include_tables=True,
        include_comments=False, output_format="txt",
    )
    if not result:
        return None
    metadata = trafilatura.extract(
        html, url=url, output_format="json", include_links=False,
    )
    meta = {}
    if metadata:
        try:
            meta = json.loads(metadata)
        except json.JSONDecodeError:
            pass
    return {
        "title": meta.get("title", ""),
        "author": meta.get("author", ""),
        "date": meta.get("date", ""),
        "content": result,
    }


def extract_with_beautifulsoup(html: str, selector: str | None = None) -> dict:
    soup = BeautifulSoup(html, "html.parser")

    title = ""
    if soup.title:
        title = soup.title.get_text(strip=True)

    for tag in soup(["script", "style", "nav", "footer", "header", "aside", "iframe", "noscript"]):
        tag.decompose()

    if selector:
        elements = soup.select(selector)
        if elements:
            text_parts = [el.get_text(separator="\n", strip=True) for el in elements]
            content = "\n\n".join(text_parts)
        else:
            content = f"Selector '{selector}' không tìm thấy element nào."
    else:
        main_content = (
            soup.find("article")
            or soup.find("main")
            or soup.find(attrs={"role": "main"})
            or soup.find("div", class_=re.compile(r"content|article|post|entry", re.I))
            or soup.body
            or soup
        )
        content = main_content.get_text(separator="\n", strip=True)

    lines = [line.strip() for line in content.splitlines()]
    content = "\n".join(line for line in lines if line)

    return {"title": title, "content": content}


def extract_links(html: str, base_url: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    links = []
    seen = set()
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if href.startswith("#") or href.startswith("javascript:"):
            continue
        if href.startswith("/"):
            href = urljoin(base_url, href)
        text = a.get_text(strip=True)
        if href not in seen and text:
            links.append({"text": text, "url": href})
            seen.add(href)
    return links


def read_webpage(
    url: str,
    selector: str | None = None,
    max_length: int = MAX_CONTENT_LENGTH,
    use_raw: bool = False,
) -> dict:
    html = fetch_page(url)

    if not use_raw and HAS_TRAFILATURA and not selector:
        result = extract_with_trafilatura(html, url)
        if result and result["content"]:
            if len(result["content"]) > max_length:
                result["content"] = result["content"][:max_length] + "\n\n... [Nội dung bị cắt ngắn]"
                result["truncated"] = True
            result["url"] = url
            result["method"] = "trafilatura"
            return result

    result = extract_with_beautifulsoup(html, selector)
    if len(result["content"]) > max_length:
        result["content"] = result["content"][:max_length] + "\n\n... [Nội dung bị cắt ngắn]"
        result["truncated"] = True
    result["url"] = url
    result["method"] = "beautifulsoup"
    return result


def format_result(result: dict, output_json: bool = False) -> str:
    if output_json:
        return json.dumps(result, ensure_ascii=False, indent=2)

    output = []
    if result.get("title"):
        output.append(f"Title: {result['title']}")
    if result.get("author"):
        output.append(f"Author: {result['author']}")
    if result.get("date"):
        output.append(f"Date: {result['date']}")
    output.append(f"URL: {result.get('url', '')}")
    output.append(f"Extraction: {result.get('method', 'unknown')}")
    output.append("-" * 80)
    output.append(result.get("content", "Không có nội dung."))
    if result.get("truncated"):
        output.append(f"\n[Nội dung đã bị cắt ngắn]")
    return "\n".join(output)


def main():
    parser = argparse.ArgumentParser(description="Web Read Skill for Cline")
    parser.add_argument("url", help="URL to read")
    parser.add_argument("--selector", "-s", help="CSS selector to extract specific elements")
    parser.add_argument("--max-length", "-m", type=int, default=MAX_CONTENT_LENGTH,
                        help=f"Max content length (default: {MAX_CONTENT_LENGTH})")
    parser.add_argument("--raw", action="store_true", help="Use BeautifulSoup only (skip trafilatura)")
    parser.add_argument("--links", action="store_true", help="Extract links from the page")
    parser.add_argument("--json", action="store_true", help="Output as JSON")

    args = parser.parse_args()

    try:
        if args.links:
            html = fetch_page(args.url)
            links = extract_links(html, args.url)
            if args.json:
                print(json.dumps(links, ensure_ascii=False, indent=2))
            else:
                if not links:
                    print("Không tìm thấy link nào.")
                else:
                    for i, link in enumerate(links, 1):
                        print(f"[{i}] {link['text']}")
                        print(f"    {link['url']}")
        else:
            result = read_webpage(args.url, args.selector, args.max_length, args.raw)
            print(format_result(result, args.json))
    except requests.exceptions.HTTPError as e:
        print(f"HTTP Error: {e}", file=sys.stderr)
        sys.exit(1)
    except requests.exceptions.ConnectionError:
        print(f"Connection Error: Không thể kết nối tới {args.url}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
