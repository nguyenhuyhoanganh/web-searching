#!/usr/bin/env python3
"""
MCP Server cung cấp Web Search & Web Read tools cho Cline.

Cách chạy:
    python server.py                    # stdio transport (default cho Cline)
    python server.py --port 8080        # SSE transport

Cấu hình trong Cline MCP settings:
    {
        "mcpServers": {
            "web-skills": {
                "command": "python",
                "args": ["/path/to/mcp-server/server.py"],
                "disabled": false
            }
        }
    }
"""

import argparse
import json
import re
import textwrap
from urllib.parse import quote_plus, urljoin

import requests
from bs4 import BeautifulSoup
from mcp.server.fastmcp import FastMCP

try:
    from ddgs import DDGS
    HAS_DDGS = True
except ImportError:
    HAS_DDGS = False

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

mcp = FastMCP("web-skills")


# --- Search helpers ---

def _search_ddgs(query: str, max_results: int, region: str) -> list[dict]:
    with DDGS() as ddgs:
        raw = list(ddgs.text(query, region=region, max_results=max_results))
    return [
        {"title": r.get("title", ""), "url": r.get("href", ""), "snippet": r.get("body", "")}
        for r in raw
    ]


def _search_ddgs_news(query: str, max_results: int, region: str) -> list[dict]:
    with DDGS() as ddgs:
        raw = list(ddgs.news(query, region=region, max_results=max_results))
    return [
        {
            "title": r.get("title", ""),
            "url": r.get("url", ""),
            "snippet": r.get("body", ""),
            "date": r.get("date", ""),
            "source": r.get("source", ""),
        }
        for r in raw
    ]


def _search_ddgs_answers(query: str) -> list[dict]:
    with DDGS() as ddgs:
        raw = list(ddgs.answers(query))
    return [
        {"text": r.get("text", ""), "url": r.get("url", ""), "source": r.get("source", "")}
        for r in raw
    ]


def _search_duckduckgo_html(query: str, max_results: int) -> list[dict]:
    url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
    resp = requests.get(url, headers=DEFAULT_HEADERS, timeout=15)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    results = []
    for div in soup.select("div.result"):
        link = div.find("a", class_="result__a")
        if not link:
            continue
        title = link.get_text(strip=True)
        href = link.get("href", "")
        snippet_el = div.find("a", class_="result__snippet")
        snippet = snippet_el.get_text(strip=True) if snippet_el else ""
        if title and href:
            results.append({"title": title, "url": href, "snippet": snippet})
        if len(results) >= max_results:
            break
    return results


def _search_google_html(query: str, max_results: int) -> list[dict]:
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


def _do_search(query: str, max_results: int, region: str) -> list[dict]:
    errors = []
    if HAS_DDGS:
        try:
            return _search_ddgs(query, max_results, region)
        except Exception as e:
            errors.append(f"DDGS API: {e}")
    try:
        return _search_duckduckgo_html(query, max_results)
    except Exception as e:
        errors.append(f"DDG HTML: {e}")
    try:
        return _search_google_html(query, max_results)
    except Exception as e:
        errors.append(f"Google HTML: {e}")
    raise RuntimeError("; ".join(errors))


# --- Content extraction helpers ---

def _extract_trafilatura(html: str, url: str) -> dict | None:
    if not HAS_TRAFILATURA:
        return None
    content = trafilatura.extract(
        html, url=url, include_links=True, include_tables=True,
        include_comments=False, output_format="txt",
    )
    if not content:
        return None
    meta = {}
    meta_json = trafilatura.extract(html, url=url, output_format="json", include_links=False)
    if meta_json:
        try:
            meta = json.loads(meta_json)
        except json.JSONDecodeError:
            pass
    return {
        "title": meta.get("title", ""),
        "author": meta.get("author", ""),
        "date": meta.get("date", ""),
        "content": content,
    }


def _extract_beautifulsoup(html: str, selector: str | None = None) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    title = soup.title.get_text(strip=True) if soup.title else ""
    for tag in soup(["script", "style", "nav", "footer", "header", "aside", "iframe", "noscript"]):
        tag.decompose()
    if selector:
        elements = soup.select(selector)
        if elements:
            content = "\n\n".join(el.get_text(separator="\n", strip=True) for el in elements)
        else:
            content = f"Selector '{selector}' không tìm thấy element nào."
    else:
        main = (
            soup.find("article") or soup.find("main")
            or soup.find(attrs={"role": "main"})
            or soup.find("div", class_=re.compile(r"content|article|post|entry", re.I))
            or soup.body or soup
        )
        content = main.get_text(separator="\n", strip=True)
    lines = [line.strip() for line in content.splitlines()]
    content = "\n".join(line for line in lines if line)
    return {"title": title, "content": content}


def _truncate(content: str, max_length: int) -> tuple[str, bool]:
    if len(content) > max_length:
        return content[:max_length] + "\n\n... [Nội dung bị cắt ngắn]", True
    return content, False


def _format_search_results(results: list[dict]) -> str:
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


# --- MCP Tools ---

@mcp.tool()
def web_search(
    query: str,
    max_results: int = 5,
    region: str = "wt-wt",
    search_type: str = "web",
) -> str:
    """Tìm kiếm thông tin trên web sử dụng DuckDuckGo (có fallback qua Google).

    Args:
        query: Từ khóa tìm kiếm. Có thể là câu hỏi hoặc từ khóa.
        max_results: Số kết quả tối đa (mặc định 5, tối đa 20).
        region: Vùng tìm kiếm. VD: "vn-vi" cho Việt Nam, "us-en" cho Mỹ, "wt-wt" cho toàn cầu.
        search_type: Loại tìm kiếm - "web" (mặc định), "news" (tin tức), "answers" (câu trả lời nhanh).
    """
    max_results = min(max_results, 20)
    try:
        if search_type == "news" and HAS_DDGS:
            try:
                results = _search_ddgs_news(query, max_results, region)
                return _format_search_results(results)
            except Exception:
                pass

        if search_type == "answers" and HAS_DDGS:
            try:
                results = _search_ddgs_answers(query)
                return _format_search_results(results)
            except Exception:
                pass

        results = _do_search(query, max_results, region)
        return _format_search_results(results)
    except Exception as e:
        return f"Lỗi tìm kiếm: {str(e)}"


@mcp.tool()
def web_read(
    url: str,
    max_length: int = 50000,
    selector: str | None = None,
    extract_links: bool = False,
) -> str:
    """Đọc và trích xuất nội dung chính từ một trang web.

    Sử dụng tool này để:
    - Đọc nội dung bài viết, documentation, blog post
    - Verify thông tin từ một URL cụ thể
    - Trích xuất nội dung từ trang web bằng CSS selector
    - Lấy danh sách links từ trang web

    Args:
        url: URL trang web cần đọc.
        max_length: Độ dài tối đa nội dung trả về (mặc định 50000 ký tự).
        selector: CSS selector để trích xuất phần cụ thể (VD: "article", "div.content", "#main").
        extract_links: Nếu True, trả về danh sách links thay vì nội dung.
    """
    try:
        resp = requests.get(url, headers=DEFAULT_HEADERS, timeout=30, allow_redirects=True)
        resp.raise_for_status()
        resp.encoding = resp.apparent_encoding or "utf-8"
        html = resp.text
    except requests.exceptions.HTTPError as e:
        return f"HTTP Error: {e}"
    except requests.exceptions.ConnectionError:
        return f"Connection Error: Không thể kết nối tới {url}"
    except requests.exceptions.Timeout:
        return f"Timeout: Trang web {url} không phản hồi trong 30 giây"
    except Exception as e:
        return f"Lỗi: {str(e)}"

    if extract_links:
        soup = BeautifulSoup(html, "html.parser")
        links = []
        seen = set()
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if href.startswith("#") or href.startswith("javascript:"):
                continue
            if href.startswith("/"):
                href = urljoin(url, href)
            text = a.get_text(strip=True)
            if href not in seen and text:
                links.append(f"[{len(links)+1}] {text}\n    {href}")
                seen.add(href)
        if not links:
            return "Không tìm thấy link nào trên trang."
        return f"Tìm thấy {len(links)} links:\n\n" + "\n".join(links)

    if HAS_TRAFILATURA and not selector:
        result = _extract_trafilatura(html, url)
        if result and result["content"]:
            content, truncated = _truncate(result["content"], max_length)
            output = []
            if result.get("title"):
                output.append(f"Title: {result['title']}")
            if result.get("author"):
                output.append(f"Author: {result['author']}")
            if result.get("date"):
                output.append(f"Date: {result['date']}")
            output.append(f"URL: {url}")
            output.append("-" * 80)
            output.append(content)
            return "\n".join(output)

    result = _extract_beautifulsoup(html, selector)
    content, truncated = _truncate(result.get("content", ""), max_length)
    output = []
    if result.get("title"):
        output.append(f"Title: {result['title']}")
    output.append(f"URL: {url}")
    output.append("-" * 80)
    output.append(content)
    return "\n".join(output)


@mcp.tool()
def search_and_read(
    query: str,
    max_results: int = 3,
    max_content_length: int = 10000,
    region: str = "wt-wt",
) -> str:
    """Tìm kiếm web VÀ tự động đọc nội dung các trang kết quả hàng đầu.

    Tool này kết hợp web_search + web_read: tìm kiếm query, sau đó đọc nội dung
    của top kết quả. Rất hữu ích khi cần verify thông tin hoặc nghiên cứu chuyên sâu.

    Args:
        query: Từ khóa tìm kiếm.
        max_results: Số trang kết quả sẽ đọc (mặc định 3, tối đa 5).
        max_content_length: Độ dài tối đa nội dung mỗi trang (mặc định 10000).
        region: Vùng tìm kiếm.
    """
    max_results = min(max_results, 5)

    try:
        search_results = _do_search(query, max_results, region)
    except Exception as e:
        return f"Lỗi tìm kiếm: {str(e)}"

    if not search_results:
        return f"Không tìm thấy kết quả nào cho: {query}"

    output = [f"Kết quả tìm kiếm cho: \"{query}\"\n{'=' * 80}\n"]

    for i, sr in enumerate(search_results, 1):
        title = sr.get("title", "N/A")
        page_url = sr.get("url", "")
        snippet = sr.get("snippet", "")

        output.append(f"\n{'=' * 80}")
        output.append(f"[{i}] {title}")
        output.append(f"URL: {page_url}")
        output.append(f"Snippet: {snippet}")
        output.append("-" * 40)

        if not page_url:
            output.append("(Không có URL)")
            continue

        try:
            resp = requests.get(page_url, headers=DEFAULT_HEADERS, timeout=15, allow_redirects=True)
            resp.raise_for_status()
            resp.encoding = resp.apparent_encoding or "utf-8"
            html = resp.text

            content = None
            if HAS_TRAFILATURA:
                content = trafilatura.extract(
                    html, url=page_url, include_links=True,
                    include_tables=True, output_format="txt",
                )
            if not content:
                bs_result = _extract_beautifulsoup(html)
                content = bs_result.get("content", "")

            if content:
                content, _ = _truncate(content, max_content_length)
                output.append(content)
            else:
                output.append("(Không trích xuất được nội dung)")
        except Exception as e:
            output.append(f"(Lỗi đọc trang: {e})")

    return "\n".join(output)


def main():
    parser = argparse.ArgumentParser(description="Web Skills MCP Server")
    parser.add_argument("--port", type=int, default=None, help="Port for SSE transport (default: stdio)")
    args = parser.parse_args()

    if args.port:
        mcp.run(transport="sse", sse_params={"port": args.port})
    else:
        mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
