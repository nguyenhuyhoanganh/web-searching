"""Convert fetched HTML into clean Markdown (+ metadata) for LLM consumption.

Preference order: trafilatura (best) -> markdownify -> BeautifulSoup plain text.
Only BeautifulSoup is a required (core) dependency.
"""
import importlib.util
import json
import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup

_EMPTY_DOC = {"title": "", "author": "", "date": "", "sitename": "", "description": "",
              "language": "", "keywords": "", "image": "", "content": ""}


def _has(mod):
    return importlib.util.find_spec(mod) is not None


def truncate(content, max_length):
    """Return (possibly-truncated content, was_truncated)."""
    if len(content) > max_length:
        return content[:max_length] + "\n\n... [content truncated]", True
    return content, False


# Markdown images embedded as base64 data URIs bloat token counts; replace with a placeholder.
_BASE64_IMG_RE = re.compile(r"(!\[[^\]]*\])\(data:image/[^;]+;base64,[^)]*\)")

# Boilerplate tags and CSS selectors stripped before BeautifulSoup/markdownify extraction.
_NOISE_TAGS = ["script", "style", "nav", "footer", "header", "aside", "iframe", "noscript"]
_NOISE_SELECTORS = (
    ".ad", ".ads", ".adsbygoogle", ".advert", ".advertisement",
    ".cookie", ".cookies", ".cookie-banner", ".consent", ".gdpr",
    ".popup", ".modal", ".overlay", ".lightbox",
    ".newsletter", ".subscribe", ".subscription",
    ".social", ".social-share", ".social-links", ".share", ".share-buttons", ".sharing",
    ".breadcrumb", ".breadcrumbs", ".skip-link", ".sr-only",
    "#ad", "#ads", "#cookie", "#cookie-banner", "#consent", "#popup", "#modal", "#newsletter",
    "[role='banner']", "[role='complementary']",
)


def strip_base64_images(markdown):
    """Replace base64 data-URI images in Markdown with a small placeholder to save tokens."""
    return _BASE64_IMG_RE.sub(r"\1(<base64-image-removed>)", markdown)


def _remove_noise(soup):
    """Decompose boilerplate tags and common ad/cookie/social/nav selectors in place."""
    for tag in soup(_NOISE_TAGS):
        tag.decompose()
    for selector in _NOISE_SELECTORS:
        for el in soup.select(selector):
            el.decompose()
    return soup


def _trafilatura_doc(html, url):
    import trafilatura
    content = trafilatura.extract(
        html, url=url, output_format="markdown",
        include_links=True, include_tables=True, include_comments=False,
    )
    if not content:
        return None
    content = strip_base64_images(content)
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
    soup = _remove_noise(BeautifulSoup(html, "html.parser"))
    content = strip_base64_images(markdownify(str(_main_node(soup))).strip())
    if not content:
        return None
    doc = dict(_EMPTY_DOC)
    doc["title"] = soup.title.get_text(strip=True) if soup.title else ""
    doc["content"] = content
    return doc


def _bs4_text_doc(html, selector=None):
    soup = BeautifulSoup(html, "html.parser")
    title = soup.title.get_text(strip=True) if soup.title else ""
    _remove_noise(soup)
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
                return _merge_metadata(doc, html)
        if _has("markdownify"):
            doc = _markdownify_doc(html, url)
            if doc:
                doc["method"] = "markdownify"
                return _merge_metadata(doc, html)
    doc = _bs4_text_doc(html, selector)
    doc["method"] = "bs4-text"
    return _merge_metadata(doc, html)


def extract_metadata(html):
    """Read metadata from <title>, <html lang>, and <meta> tags (og:, article:, keywords)."""
    soup = BeautifulSoup(html, "html.parser")

    def meta(attr, value):
        el = soup.find("meta", attrs={attr: value})
        return el["content"].strip() if el and el.get("content") else ""

    html_tag = soup.find("html")
    return {
        "title": (soup.title.get_text(strip=True) if soup.title else "") or meta("property", "og:title"),
        "description": meta("name", "description") or meta("property", "og:description"),
        "sitename": meta("property", "og:site_name"),
        "image": meta("property", "og:image"),
        "date": meta("property", "article:published_time"),
        "keywords": meta("name", "keywords"),
        "language": (html_tag.get("lang", "").strip() if html_tag else "") or meta("property", "og:locale"),
    }


def _merge_metadata(doc, html):
    """Fill empty metadata fields on doc from <meta> tags (does not overwrite existing values)."""
    meta = extract_metadata(html)
    for key in ("title", "description", "sitename", "date", "language", "keywords", "image"):
        if not doc.get(key):
            doc[key] = meta.get(key, "")
    doc["jsonld"] = extract_jsonld(html)
    return doc


def extract_jsonld(html):
    """Return parsed JSON-LD objects from <script type="application/ld+json"> blocks (schema.org)."""
    soup = BeautifulSoup(html, "html.parser")
    blocks = []
    for tag in soup.find_all("script", attrs={"type": "application/ld+json"}):
        raw = (tag.string or tag.get_text() or "").strip()
        if not raw:
            continue
        try:
            data = json.loads(raw)
        except (json.JSONDecodeError, ValueError):
            continue
        blocks.extend(data if isinstance(data, list) else [data])
    return blocks


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
