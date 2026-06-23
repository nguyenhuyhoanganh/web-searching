"""Convert fetched HTML into clean Markdown (+ metadata) for LLM consumption.

Preference order: trafilatura (best) -> markdownify -> BeautifulSoup plain text.
Only BeautifulSoup is a required (core) dependency.
"""
import importlib.util
import json
import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup

_EMPTY_DOC = {"title": "", "author": "", "date": "", "sitename": "", "description": "", "content": ""}


def _has(mod):
    return importlib.util.find_spec(mod) is not None


def truncate(content, max_length):
    """Return (possibly-truncated content, was_truncated)."""
    if len(content) > max_length:
        return content[:max_length] + "\n\n... [content truncated]", True
    return content, False


def _trafilatura_doc(html, url):
    import trafilatura
    content = trafilatura.extract(
        html, url=url, output_format="markdown",
        include_links=True, include_tables=True, include_comments=False,
    )
    if not content:
        return None
    meta = {}
    raw = trafilatura.extract(html, url=url, output_format="json", with_metadata=True,
                              include_links=False)
    if raw:
        try:
            meta = json.loads(raw)
        except json.JSONDecodeError:
            meta = {}
    doc = dict(_EMPTY_DOC)
    doc.update({
        "title": meta.get("title", ""), "author": meta.get("author", ""),
        "date": meta.get("date", ""), "sitename": meta.get("sitename", ""),
        "description": meta.get("description", ""), "content": content,
    })
    return doc


def _main_node(soup):
    return (
        soup.find("article") or soup.find("main") or soup.find(attrs={"role": "main"})
        or soup.find("div", class_=re.compile(r"content|article|post|entry", re.I))
        or soup.body or soup
    )


def _markdownify_doc(html, url):
    from markdownify import markdownify
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header", "aside", "iframe", "noscript"]):
        tag.decompose()
    content = markdownify(str(_main_node(soup))).strip()
    if not content:
        return None
    doc = dict(_EMPTY_DOC)
    doc["title"] = soup.title.get_text(strip=True) if soup.title else ""
    doc["content"] = content
    return doc


def _bs4_text_doc(html, selector=None):
    soup = BeautifulSoup(html, "html.parser")
    title = soup.title.get_text(strip=True) if soup.title else ""
    for tag in soup(["script", "style", "nav", "footer", "header", "aside", "iframe", "noscript"]):
        tag.decompose()
    if selector:
        nodes = soup.select(selector)
        text = "\n\n".join(n.get_text(separator="\n", strip=True) for n in nodes) \
            if nodes else f"Selector '{selector}' matched no elements."
    else:
        text = _main_node(soup).get_text(separator="\n", strip=True)
    lines = [ln.strip() for ln in text.splitlines()]
    doc = dict(_EMPTY_DOC)
    doc["title"] = title
    doc["content"] = "\n".join(ln for ln in lines if ln)
    return doc


def to_document(html, url, fmt="markdown", selector=None):
    """Return {title, author, date, sitename, description, content, method}.

    fmt: "markdown" (default), "text", or "json" (caller serialises). selector forces BS4 text.
    """
    if fmt != "text" and not selector:
        if _has("trafilatura"):
            doc = _trafilatura_doc(html, url)
            if doc:
                doc["method"] = "trafilatura"
                return doc
        if _has("markdownify"):
            doc = _markdownify_doc(html, url)
            if doc:
                doc["method"] = "markdownify"
                return doc
    doc = _bs4_text_doc(html, selector)
    doc["method"] = "bs4-text"
    return doc


def extract_links(html, base_url):
    """Return [{text, url}] of absolute, de-duplicated, non-anchor links."""
    soup = BeautifulSoup(html, "html.parser")
    links, seen = [], set()
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if href.startswith(("#", "javascript:", "mailto:")):
            continue
        href = urljoin(base_url, href)
        text = a.get_text(strip=True)
        if href not in seen and text:
            links.append({"text": text, "url": href})
            seen.add(href)
    return links
