#!/usr/bin/env python3
"""MCP server "web-skills": web search & web page reading tools.

Chạy:
    python server.py            # stdio transport (mặc định, cho Cline)
    python server.py --port 8080  # SSE transport

Cấu hình trong Cline MCP settings:
    {
      "mcpServers": {
        "web-skills": {
          "command": "/path/to/.venv/bin/python",
          "args": ["/path/to/mcp-server/server.py"],
          "disabled": false
        }
      }
    }
"""

import argparse
import json
import logging
import re
import sys
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

# stdio transport dùng stdout cho giao thức JSON-RPC. Mọi log phải ra stderr.
logging.basicConfig(level=logging.WARNING, stream=sys.stderr)

# Giới hạn ký tự cho mỗi kết quả tool trả về (best practice MCP: cắt ngắn có kiểm soát).
CHARACTER_LIMIT = 25_000

# Trần cứng để tránh request quá tải.
MAX_SEARCH_RESULTS = 20
MAX_PAGES_TO_READ = 5
HTTP_TIMEOUT = 30
SEARCH_TIMEOUT = 15

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9,vi;q=0.8",
}

mcp = FastMCP("web-skills")


# --------------------------------------------------------------------------- #
# Search backends (DuckDuckGo API → DuckDuckGo HTML → Google HTML fallback)
# --------------------------------------------------------------------------- #

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
    resp = requests.get(
        f"https://html.duckduckgo.com/html/?q={quote_plus(query)}",
        headers=DEFAULT_HEADERS, timeout=SEARCH_TIMEOUT,
    )
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
    resp = requests.get(
        f"https://www.google.com/search?q={quote_plus(query)}&num={max_results}",
        headers=DEFAULT_HEADERS, timeout=SEARCH_TIMEOUT,
    )
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    results = []
    for g in soup.select("div.g, div[data-sokoban-container]"):
        link = g.find("a", href=True)
        if not link or not link["href"].startswith("http"):
            continue
        title_el = g.find("h3")
        title = title_el.get_text(strip=True) if title_el else ""
        snippet_el = g.find("div", class_="VwiC3b") or g.find("span", class_="aCOpRe")
        snippet = snippet_el.get_text(strip=True) if snippet_el else ""
        if title:
            results.append({"title": title, "url": link["href"], "snippet": snippet})
        if len(results) >= max_results:
            break
    return results


def _do_search(query: str, max_results: int, region: str) -> list[dict]:
    """Tìm kiếm web với fallback nhiều tầng. Raise nếu mọi backend đều hỏng."""
    errors = []
    if HAS_DDGS:
        try:
            return _search_ddgs(query, max_results, region)
        except Exception as e:  # noqa: BLE001 - gom lỗi để fallback
            errors.append(f"DuckDuckGo API: {e}")
    for name, fn in (("DuckDuckGo HTML", _search_duckduckgo_html), ("Google HTML", _search_google_html)):
        try:
            return fn(query, max_results)
        except Exception as e:  # noqa: BLE001
            errors.append(f"{name}: {e}")
    raise RuntimeError("Mọi backend tìm kiếm đều thất bại → " + "; ".join(errors))


# --------------------------------------------------------------------------- #
# Content extraction
# --------------------------------------------------------------------------- #

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
        content = (
            "\n\n".join(el.get_text(separator="\n", strip=True) for el in elements)
            if elements else f"Selector '{selector}' không khớp element nào."
        )
    else:
        main = (
            soup.find("article") or soup.find("main")
            or soup.find(attrs={"role": "main"})
            or soup.find("div", class_=re.compile(r"content|article|post|entry", re.I))
            or soup.body or soup
        )
        content = main.get_text(separator="\n", strip=True)
    content = "\n".join(line.strip() for line in content.splitlines() if line.strip())
    return {"title": title, "content": content}


def _fetch(url: str, timeout: int = HTTP_TIMEOUT) -> str:
    resp = requests.get(url, headers=DEFAULT_HEADERS, timeout=timeout, allow_redirects=True)
    resp.raise_for_status()
    resp.encoding = resp.apparent_encoding or "utf-8"
    return resp.text


def _clamp(content: str, limit: int) -> str:
    """Cắt ngắn có hướng dẫn (best practice: nói cho model biết cách lấy thêm)."""
    limit = min(limit, CHARACTER_LIMIT)
    if len(content) <= limit:
        return content
    return (
        content[:limit]
        + f"\n\n... [Đã cắt ở {limit} ký tự. Dùng `selector` để lấy đúng phần cần, "
        "hoặc tăng `max_length` nếu thật sự cần nhiều hơn.]"
    )


def _format_search_results(results: list[dict], query: str) -> str:
    if not results:
        return (
            f'Không có kết quả cho "{query}". '
            "Thử đổi từ khóa, bỏ bớt qualifier, hoặc dùng thuật ngữ tiếng Anh."
        )
    lines = [f'Tìm thấy {len(results)} kết quả cho "{query}":', ""]
    for i, r in enumerate(results, 1):
        lines.append(f"[{i}] {r.get('title', r.get('text', 'N/A'))}")
        if r.get("url"):
            lines.append(f"    URL: {r['url']}")
        snippet = r.get("snippet") or r.get("text") or ""
        if snippet:
            lines.append(textwrap.fill(snippet, width=100, initial_indent="    ", subsequent_indent="    "))
        if r.get("date"):
            lines.append(f"    Date: {r['date']}")
        if r.get("source"):
            lines.append(f"    Source: {r['source']}")
        lines.append("")
    return "\n".join(lines)


# --------------------------------------------------------------------------- #
# MCP tools
# --------------------------------------------------------------------------- #

@mcp.tool(
    annotations={
        "title": "Web Search",
        "readOnlyHint": True,
        "openWorldHint": True,
    }
)
def web_search(
    query: str,
    max_results: int = 5,
    region: str = "wt-wt",
    search_type: str = "web",
) -> str:
    """Tìm kiếm trên web và trả về danh sách tiêu đề + URL + đoạn trích.

    Dùng khi cần tìm thông tin cập nhật, kiểm chứng một dữ kiện, hoặc tra cứu lỗi.
    KHÔNG kết luận chỉ từ đoạn trích — mở `web_read` trên URL đáng tin nhất để xác nhận.

    Args:
        query: Từ khóa tìm kiếm. Hỗ trợ toán tử "cụm chính xác" và site:domain.
        max_results: Số kết quả (1–20, mặc định 5).
        region: Mã vùng, vd "vn-vi" (Việt Nam), "us-en" (Mỹ), "wt-wt" (toàn cầu).
        search_type: "web" (mặc định), "news" (tin tức), hoặc "answers" (dữ kiện nhanh).

    Returns:
        Danh sách kết quả dạng text, mỗi mục có tiêu đề, URL và đoạn trích.
    """
    if not query.strip():
        return "Lỗi: `query` rỗng."
    max_results = max(1, min(max_results, MAX_SEARCH_RESULTS))
    if search_type not in ("web", "news", "answers"):
        return "Lỗi: `search_type` phải là 'web', 'news', hoặc 'answers'."

    try:
        if search_type == "news" and HAS_DDGS:
            try:
                return _clamp(_format_search_results(_search_ddgs_news(query, max_results, region), query), CHARACTER_LIMIT)
            except Exception:  # noqa: BLE001 - rơi về web search thường
                pass
        if search_type == "answers" and HAS_DDGS:
            try:
                return _clamp(_format_search_results(_search_ddgs_answers(query), query), CHARACTER_LIMIT)
            except Exception:  # noqa: BLE001
                pass
        results = _do_search(query, max_results, region)
        return _clamp(_format_search_results(results, query), CHARACTER_LIMIT)
    except Exception as e:  # noqa: BLE001
        return f"Lỗi tìm kiếm: {e}"


@mcp.tool(
    annotations={
        "title": "Read Web Page",
        "readOnlyHint": True,
        "openWorldHint": True,
    }
)
def web_read(
    url: str,
    max_length: int = CHARACTER_LIMIT,
    selector: str | None = None,
    extract_links: bool = False,
) -> str:
    """Tải một URL và trích nội dung chính (bỏ menu/quảng cáo/footer).

    Dùng để đọc bài viết, tài liệu, blog, hoặc xác minh thông tin từ một nguồn cụ thể.
    Lưu ý: chỉ đọc HTML tĩnh — trang render bằng JavaScript có thể thiếu nội dung.

    Args:
        url: Địa chỉ trang web (http/https).
        max_length: Số ký tự tối đa trả về (mặc định và trần là 25000).
        selector: CSS selector để lấy đúng phần (vd "article", "div.content", "#main").
        extract_links: Nếu True, trả về danh sách link trên trang thay vì nội dung.

    Returns:
        Tiêu đề + URL + nội dung đã trích, hoặc danh sách link, hoặc thông báo lỗi.
    """
    if not url.startswith(("http://", "https://")):
        return "Lỗi: `url` phải bắt đầu bằng http:// hoặc https://"

    try:
        html = _fetch(url)
    except requests.exceptions.HTTPError as e:
        return f"Lỗi HTTP khi tải {url}: {e} (trang có thể chặn bot hoặc cần đăng nhập)"
    except requests.exceptions.ConnectionError:
        return f"Lỗi kết nối: không tới được {url}"
    except requests.exceptions.Timeout:
        return f"Hết thời gian chờ: {url} không phản hồi trong {HTTP_TIMEOUT}s"
    except Exception as e:  # noqa: BLE001
        return f"Lỗi khi tải {url}: {e}"

    if extract_links:
        soup = BeautifulSoup(html, "html.parser")
        links, seen = [], set()
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if href.startswith(("#", "javascript:")):
                continue
            if href.startswith("/"):
                href = urljoin(url, href)
            text = a.get_text(strip=True)
            if href not in seen and text:
                links.append(f"[{len(links) + 1}] {text}\n    {href}")
                seen.add(href)
        if not links:
            return "Không tìm thấy link nào trên trang."
        return _clamp(f"Tìm thấy {len(links)} link:\n\n" + "\n".join(links), CHARACTER_LIMIT)

    result = None
    if HAS_TRAFILATURA and not selector:
        result = _extract_trafilatura(html, url)
    if not result or not result.get("content"):
        result = _extract_beautifulsoup(html, selector)

    header = []
    if result.get("title"):
        header.append(f"Title: {result['title']}")
    if result.get("author"):
        header.append(f"Author: {result['author']}")
    if result.get("date"):
        header.append(f"Date: {result['date']}")
    header.append(f"URL: {url}")
    body = _clamp(result.get("content", ""), max_length)
    return "\n".join(header) + "\n" + "-" * 60 + "\n" + body


@mcp.tool(
    annotations={
        "title": "Search And Read",
        "readOnlyHint": True,
        "openWorldHint": True,
    }
)
def search_and_read(
    query: str,
    max_results: int = 3,
    max_content_length: int = 8000,
    region: str = "wt-wt",
) -> str:
    """Tìm kiếm web RỒI tự động đọc nội dung các trang kết quả đầu — gộp 1 bước.

    Hữu ích khi cần nghiên cứu sâu hoặc đối chiếu nhiều nguồn cho một câu hỏi.
    Mỗi truy vấn nên có một mục tiêu rõ ràng; tránh nhồi nhiều ý vào một query.

    Args:
        query: Từ khóa tìm kiếm (hỗ trợ "cụm chính xác", site:domain).
        max_results: Số trang sẽ đọc (1–5, mặc định 3).
        max_content_length: Số ký tự tối đa mỗi trang (mặc định 8000).
        region: Mã vùng tìm kiếm.

    Returns:
        Với mỗi trang: tiêu đề, URL, đoạn trích và nội dung đã trích.
    """
    if not query.strip():
        return "Lỗi: `query` rỗng."
    max_results = max(1, min(max_results, MAX_PAGES_TO_READ))

    try:
        results = _do_search(query, max_results, region)
    except Exception as e:  # noqa: BLE001
        return f"Lỗi tìm kiếm: {e}"
    if not results:
        return f'Không có kết quả cho "{query}".'

    out = [f'Nghiên cứu "{query}" — đọc {len(results)} trang đầu:\n']
    for i, sr in enumerate(results, 1):
        out += ["=" * 60, f"[{i}] {sr.get('title', 'N/A')}", f"URL: {sr.get('url', '')}"]
        if sr.get("snippet"):
            out.append(f"Snippet: {sr['snippet']}")
        out.append("-" * 30)
        page_url = sr.get("url", "")
        if not page_url:
            out.append("(không có URL)")
            continue
        try:
            html = _fetch(page_url, timeout=SEARCH_TIMEOUT)
            content = None
            if HAS_TRAFILATURA:
                content = trafilatura.extract(
                    html, url=page_url, include_links=True, include_tables=True, output_format="txt"
                )
            if not content:
                content = _extract_beautifulsoup(html).get("content", "")
            out.append(_clamp(content, max_content_length) if content else "(không trích được nội dung)")
        except Exception as e:  # noqa: BLE001
            out.append(f"(lỗi đọc trang: {e})")
    return _clamp("\n".join(out), CHARACTER_LIMIT)


def main():
    parser = argparse.ArgumentParser(description="web-skills MCP server")
    parser.add_argument("--port", type=int, default=None, help="Port cho SSE transport (mặc định: stdio)")
    args = parser.parse_args()
    if args.port:
        mcp.run(transport="sse", sse_params={"port": args.port})
    else:
        mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
