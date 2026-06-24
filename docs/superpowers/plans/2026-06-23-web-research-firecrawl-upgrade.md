# web-research Firecrawl-Inspired Upgrade — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Upgrade the `web-research` Cline skill with Firecrawl-grade web reading/searching (clean Markdown, JS rendering, PDF, full-content search, site map/crawl) while requiring no API key and no MCP.

**Architecture:** Introduce an internal `lib/` package (env, http, engines, extract, pdf) that every script shares; rewrite the two existing scripts and add three new ones (`doctor`, `web_map`, `web_crawl`) as thin CLIs over `lib/`. All heavy capabilities degrade gracefully when their optional dependency is absent.

**Tech Stack:** Python 3.10+ (stdlib `unittest` for tests), requests, beautifulsoup4, lxml, ddgs, trafilatura, markdownify, plus optional playwright and pypdf.

---

## Conventions for this plan

- **No commits, no branches** (user instruction). Where a normal plan commits, this plan has a
  **Checkpoint** step: run the tests / smoke-check and pause for review. Do not run `git commit` or
  `git checkout -b`.
- **Tests use `unittest`** (stdlib — no install needed to run the runner). Tests that need a
  third-party package use `@unittest.skipUnless(...)` so they skip cleanly when the dep is absent on
  the dev machine and run when it is present.
- **Run all tests with:** `python -m unittest discover -s .cline/skills/web-research/tests -v`
  (replace `python` with the interpreter that reports Python >= 3.10).
- The package dir is `.cline/skills/web-research/lib/`. Scripts and tests put the **skill dir** on
  `sys.path[0]` then `from lib import ...`, so the local package always wins.
- Paths below are relative to the repo root `/Users/hoanganh/Workspace/web-searching`.

## File structure (what each file owns)

```
.cline/skills/web-research/
├── SKILL.md                      # rewritten: setup steps, tools, workflow (no MCP/key wording)
├── requirements.txt              # baseline deps: core + search + extract
├── reference/
│   ├── search-strategy.md        # kept (existing)
│   └── capabilities.md           # NEW: full CLI flag reference
├── lib/
│   ├── __init__.py               # marks package
│   ├── env.py                    # dep groups, dep check, skill-dir probe
│   ├── http.py                   # shared GET (headers, SSL fallback, retry)
│   ├── extract.py                # HTML→Markdown, metadata, links, truncate
│   ├── engines.py                # fetch + playwright engines, get_html, actions
│   └── pdf.py                    # PDF detect + extract
├── scripts/
│   ├── doctor.py                 # env + dep report
│   ├── web_search.py             # rewritten: lib-based + --fetch
│   ├── web_read.py               # rewritten: lib-based + render/pdf/actions
│   ├── web_map.py                # NEW
│   └── web_crawl.py              # NEW
└── tests/
    ├── test_env.py
    ├── test_extract.py
    └── test_pdf.py
```

---

## Task 1: Package scaffold + `lib/env.py`

**Files:**
- Create: `.cline/skills/web-research/lib/__init__.py`
- Create: `.cline/skills/web-research/lib/env.py`
- Test: `.cline/skills/web-research/tests/test_env.py`

- [ ] **Step 1: Write the failing test**

Create `.cline/skills/web-research/tests/test_env.py`:

```python
import os
import sys
import tempfile
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.dirname(HERE)
if SKILL_DIR not in sys.path:
    sys.path.insert(0, SKILL_DIR)

from lib import env  # noqa: E402


class TestDepGroups(unittest.TestCase):
    def test_core_group_maps_bs4_to_beautifulsoup4(self):
        names = dict(env.DEP_GROUPS["core"])
        self.assertEqual(names["bs4"], "beautifulsoup4")

    def test_missing_pip_packages_returns_pip_names(self):
        with mock.patch.object(env, "_is_installed", return_value=False):
            missing = env.missing_pip_packages(["core"])
        self.assertIn("beautifulsoup4", missing)
        self.assertNotIn("bs4", missing)

    def test_check_deps_reports_all_groups(self):
        result = env.check_deps()
        self.assertEqual(set(result), set(env.DEP_GROUPS))


class TestFindSkillDir(unittest.TestCase):
    def test_finds_project_cline_skills(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = os.path.join(tmp, ".cline", "skills", env.SKILL_NAME)
            os.makedirs(target)
            with mock.patch("os.getcwd", return_value=tmp), \
                 mock.patch("os.path.expanduser", return_value=os.path.join(tmp, "nohome")):
                self.assertEqual(env.find_skill_dir(), target)

    def test_returns_none_when_absent(self):
        with tempfile.TemporaryDirectory() as tmp:
            with mock.patch("os.getcwd", return_value=tmp), \
                 mock.patch("os.path.expanduser", return_value=os.path.join(tmp, "nohome")):
                self.assertIsNone(env.find_skill_dir())


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest discover -s .cline/skills/web-research/tests -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'lib'` (package not created yet).

- [ ] **Step 3: Create the package and implementation**

Create `.cline/skills/web-research/lib/__init__.py` (empty file):

```python
```

Create `.cline/skills/web-research/lib/env.py`:

```python
"""Environment helpers: dependency groups, dependency checks, skill-dir discovery."""
import importlib.util
import os

SKILL_NAME = "web-research"

# group -> list of (import_name, pip_package_name)
DEP_GROUPS = {
    "core":    [("requests", "requests"), ("bs4", "beautifulsoup4"), ("lxml", "lxml")],
    "search":  [("ddgs", "ddgs")],
    "extract": [("trafilatura", "trafilatura"), ("markdownify", "markdownify")],
    "render":  [("playwright", "playwright")],
    "pdf":     [("pypdf", "pypdf")],
}

# Project- and home-level roots Cline scans for skills (incl. cross-agent .agents).
_PROJECT_ROOTS = (".cline", ".clinerules", ".claude", ".agents")
_HOME_ROOTS = (".cline", ".agents", ".claude")


def _candidate_dirs():
    cwd = os.getcwd()
    home = os.path.expanduser("~")
    dirs = [os.path.join(cwd, r, "skills", SKILL_NAME) for r in _PROJECT_ROOTS]
    dirs += [os.path.join(home, r, "skills", SKILL_NAME) for r in _HOME_ROOTS]
    return dirs


def find_skill_dir():
    """Return the absolute path of the installed skill dir, or None if not found."""
    for d in _candidate_dirs():
        if os.path.isdir(d):
            return d
    return None


def _is_installed(import_name):
    return importlib.util.find_spec(import_name) is not None


def check_deps():
    """Return {group: {pip_name: installed_bool}} for every group."""
    return {
        group: {pip: _is_installed(imp) for imp, pip in members}
        for group, members in DEP_GROUPS.items()
    }


def missing_pip_packages(groups=None):
    """Return the pip package names that are not importable for the given groups."""
    groups = groups or list(DEP_GROUPS)
    missing = []
    for group in groups:
        for imp, pip in DEP_GROUPS[group]:
            if not _is_installed(imp):
                missing.append(pip)
    return missing
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m unittest discover -s .cline/skills/web-research/tests -v`
Expected: PASS (5 tests in test_env.py).

- [ ] **Step 5: Checkpoint** — tests green; no commit (per user instruction). Pause for review.

---

## Task 2: `lib/http.py` (shared GET with SSL fallback + retry)

**Files:**
- Create: `.cline/skills/web-research/lib/http.py`

No new unit test (network I/O; the SSL/retry behaviour is exercised by the live smoke tests in
Task 12). Keep it small.

- [ ] **Step 1: Write the implementation**

Create `.cline/skills/web-research/lib/http.py`:

```python
"""Shared HTTP GET: realistic headers, automatic SSL-verify fallback, retry with backoff."""
import logging
import time

import requests

logger = logging.getLogger("web-research.http")

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9,vi;q=0.8",
}

# Disabled automatically on the first SSLError (common behind corporate proxies).
_verify_ssl = True


def get(url, timeout=30, retries=3):
    """GET a URL, returning a requests.Response. Retries connection/timeout errors with backoff."""
    global _verify_ssl
    last_error = None
    for attempt in range(1, retries + 1):
        try:
            resp = requests.get(
                url, headers=DEFAULT_HEADERS, timeout=timeout,
                allow_redirects=True, verify=_verify_ssl,
            )
            resp.raise_for_status()
            return resp
        except requests.exceptions.SSLError as e:
            if _verify_ssl:
                logger.warning("SSL verification failed for %s; retrying without verification.", url)
                _verify_ssl = False
                continue
            last_error = e
            break
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
            last_error = e
            if attempt < retries:
                wait = attempt * 2
                logger.warning("Attempt %d/%d failed for %s: %s. Retrying in %ds.",
                               attempt, retries, url, e, wait)
                time.sleep(wait)
                continue
            break
        except requests.exceptions.HTTPError:
            raise
    raise last_error
```

- [ ] **Step 2: Verify it imports** (only if `requests` is installed; otherwise this step is
  expected to be deferred until deps are installed — do **not** install without asking the user).

Run: `python -c "import sys; sys.path.insert(0, '.cline/skills/web-research'); from lib import http; print('ok')"`
Expected: prints `ok` if `requests` is installed; `ModuleNotFoundError: requests` otherwise (fine —
this module is only needed at runtime once deps are present).

- [ ] **Step 3: Checkpoint** — no commit. Pause for review.

---

## Task 3: `lib/extract.py` (HTML → Markdown, metadata, links)

**Files:**
- Create: `.cline/skills/web-research/lib/extract.py`
- Test: `.cline/skills/web-research/tests/test_extract.py`

- [ ] **Step 1: Write the failing test**

Create `.cline/skills/web-research/tests/test_extract.py`:

```python
import importlib.util
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.dirname(HERE)
if SKILL_DIR not in sys.path:
    sys.path.insert(0, SKILL_DIR)

from lib import extract  # noqa: E402

HAS_BS4 = importlib.util.find_spec("bs4") is not None

SAMPLE = """
<html><head><title>Hello Title</title></head>
<body>
  <nav>menu</nav>
  <article><h1>Heading</h1><p>First paragraph.</p>
  <a href="/docs">Docs</a><a href="https://x.test/page">External</a></article>
  <footer>footer</footer>
</body></html>
"""


class TestTruncate(unittest.TestCase):
    def test_truncate_marks_cut(self):
        out, cut = extract.truncate("abcdef", 3)
        self.assertTrue(cut)
        self.assertTrue(out.startswith("abc"))

    def test_truncate_noop_when_short(self):
        out, cut = extract.truncate("abc", 10)
        self.assertFalse(cut)
        self.assertEqual(out, "abc")


@unittest.skipUnless(HAS_BS4, "beautifulsoup4 not installed")
class TestLinksAndText(unittest.TestCase):
    def test_extract_links_absolutizes(self):
        links = extract.extract_links(SAMPLE, "https://x.test/")
        urls = [l["url"] for l in links]
        self.assertIn("https://x.test/docs", urls)
        self.assertIn("https://x.test/page", urls)

    def test_to_document_text_drops_nav_footer(self):
        doc = extract.to_document(SAMPLE, "https://x.test/", fmt="text")
        self.assertIn("First paragraph", doc["content"])
        self.assertNotIn("menu", doc["content"])
        self.assertEqual(doc["title"], "Hello Title")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest discover -s .cline/skills/web-research/tests -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'lib.extract'`.

- [ ] **Step 3: Write the implementation**

Create `.cline/skills/web-research/lib/extract.py`:

```python
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
    raw = trafilatura.extract(html, url=url, output_format="json", include_links=False)
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m unittest discover -s .cline/skills/web-research/tests -v`
Expected: PASS. `TestTruncate` always runs; `TestLinksAndText` runs if bs4 is installed, else skips.

- [ ] **Step 5: Checkpoint** — no commit. Pause for review.

---

## Task 4: `lib/pdf.py` (PDF detection + extraction)

**Files:**
- Create: `.cline/skills/web-research/lib/pdf.py`
- Test: `.cline/skills/web-research/tests/test_pdf.py`

- [ ] **Step 1: Write the failing test**

Create `.cline/skills/web-research/tests/test_pdf.py`:

```python
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.dirname(HERE)
if SKILL_DIR not in sys.path:
    sys.path.insert(0, SKILL_DIR)

from lib import pdf  # noqa: E402


class TestLooksLikePdf(unittest.TestCase):
    def test_by_magic_bytes(self):
        self.assertTrue(pdf.looks_like_pdf("https://x.test/file", "", b"%PDF-1.7\n..."))

    def test_by_content_type(self):
        self.assertTrue(pdf.looks_like_pdf("https://x.test/file", "application/pdf", b""))

    def test_by_url_extension(self):
        self.assertTrue(pdf.looks_like_pdf("https://x.test/report.pdf", "", b""))

    def test_html_is_not_pdf(self):
        self.assertFalse(pdf.looks_like_pdf("https://x.test/", "text/html", b"<html>"))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest discover -s .cline/skills/web-research/tests -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'lib.pdf'`.

- [ ] **Step 3: Write the implementation**

Create `.cline/skills/web-research/lib/pdf.py`:

```python
"""Detect and extract text from PDF responses. Extraction needs the optional `pypdf` package."""
import io


def looks_like_pdf(url, content_type, first_bytes):
    if first_bytes[:5] == b"%PDF-":
        return True
    if "application/pdf" in (content_type or "").lower():
        return True
    return url.lower().split("?")[0].endswith(".pdf")


def extract_pdf(content_bytes):
    """Return {title, author, content, pages}. Raises RuntimeError with a hint if pypdf is missing."""
    try:
        from pypdf import PdfReader
    except ImportError:
        raise RuntimeError(
            "Reading PDFs needs the 'pypdf' package. Install it with:  pip install pypdf"
        )
    reader = PdfReader(io.BytesIO(content_bytes))
    meta = reader.metadata or {}
    pages = [(p.extract_text() or "") for p in reader.pages]
    return {
        "title": (meta.get("/Title") or "") if hasattr(meta, "get") else "",
        "author": (meta.get("/Author") or "") if hasattr(meta, "get") else "",
        "content": "\n\n".join(pages).strip(),
        "pages": len(reader.pages),
    }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m unittest discover -s .cline/skills/web-research/tests -v`
Expected: PASS (4 PDF tests; pypdf not needed for detection tests).

- [ ] **Step 5: Checkpoint** — no commit. Pause for review.

---

## Task 5: `lib/engines.py` (fetch + Playwright engines, actions, selection)

**Files:**
- Create: `.cline/skills/web-research/lib/engines.py`

Network/browser I/O — covered by live smoke tests in Task 12, not unit tests.

- [ ] **Step 1: Write the implementation**

Create `.cline/skills/web-research/lib/engines.py`:

```python
"""Page-fetching engines and selection.

- fetch_html: static fetch via requests (lib.http).
- render_html: JS rendering + optional actions via Playwright (optional dependency).
- get_html: chooses an engine ("auto"/"never"/"always") with graceful fallback.
"""
import importlib.util
import logging

from lib import http

logger = logging.getLogger("web-research.engines")

# Heuristic: below this many chars of visible text, an auto fetch may be a JS shell.
_JS_TEXT_THRESHOLD = 200


class RenderUnavailable(RuntimeError):
    """Raised when Playwright rendering is requested but the package is not installed."""


def _playwright_installed():
    return importlib.util.find_spec("playwright") is not None


def fetch_html(url):
    resp = http.get(url)
    resp.encoding = resp.apparent_encoding or "utf-8"
    return {
        "html": resp.text,
        "final_url": str(resp.url),
        "content_type": resp.headers.get("Content-Type", ""),
        "content_bytes": resp.content,
        "engine_used": "fetch",
    }


def _run_actions(page, actions):
    for act in actions or []:
        kind = act.get("type")
        if kind == "click":
            page.click(act["selector"])
        elif kind == "write":
            page.fill(act["selector"], act.get("text", ""))
        elif kind == "press":
            page.keyboard.press(act["key"])
        elif kind == "scroll":
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        elif kind == "wait":
            if act.get("selector"):
                page.wait_for_selector(act["selector"])
            else:
                page.wait_for_timeout(int(act.get("ms", 1000)))


def render_html(url, wait_for=None, scroll=0, actions=None, screenshot=None, timeout_ms=30000):
    if not _playwright_installed():
        raise RenderUnavailable(
            "JS rendering needs Playwright. Install it with:  "
            "pip install playwright  &&  playwright install chromium"
        )
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        try:
            page = browser.new_page(user_agent=http.DEFAULT_HEADERS["User-Agent"])
            page.goto(url, wait_until="networkidle", timeout=timeout_ms)
            if wait_for:
                page.wait_for_selector(wait_for, timeout=timeout_ms)
            for _ in range(scroll):
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                page.wait_for_timeout(800)
            _run_actions(page, actions)
            if screenshot:
                page.screenshot(path=screenshot, full_page=True)
            html = page.content()
            final_url = page.url
        finally:
            browser.close()
    return {
        "html": html, "final_url": final_url, "content_type": "text/html",
        "content_bytes": html.encode("utf-8", "ignore"), "engine_used": "playwright",
    }


def _visible_text_len(html):
    from lib import extract
    return len(extract.to_document(html, "", fmt="text")["content"])


def get_html(url, render="auto", wait_for=None, scroll=0, actions=None,
             screenshot=None, timeout_ms=30000):
    """Return a fetch/render result dict plus 'suggest_render' (True if a render would likely help).

    render: "never" (fetch only), "always" (render), "auto" (fetch, render if it looks JS-gated).
    """
    if render == "always" or actions or wait_for or screenshot:
        result = render_html(url, wait_for, scroll, actions, screenshot, timeout_ms)
        result["suggest_render"] = False
        return result

    fetched = fetch_html(url)
    if render == "never":
        fetched["suggest_render"] = False
        return fetched

    # auto
    looks_thin = _visible_text_len(fetched["html"]) < _JS_TEXT_THRESHOLD
    if looks_thin and _playwright_installed():
        try:
            rendered = render_html(url, scroll=scroll, timeout_ms=timeout_ms)
            rendered["suggest_render"] = False
            return rendered
        except Exception as e:  # fall back to the fetched HTML
            logger.warning("Render fallback failed for %s: %s", url, e)
    fetched["suggest_render"] = looks_thin and not _playwright_installed()
    return fetched
```

- [ ] **Step 2: Verify import structure** (only meaningful once `requests` is installed):

Run: `python -c "import sys; sys.path.insert(0, '.cline/skills/web-research'); import lib.engines; print('ok')"`
Expected: `ok` if requests is installed; otherwise a `ModuleNotFoundError` for requests (deferred
until deps are installed — do not install without asking).

- [ ] **Step 3: Checkpoint** — no commit. Pause for review.

---

## Task 6: `scripts/doctor.py` (environment + dependency report)

**Files:**
- Create: `.cline/skills/web-research/scripts/doctor.py`

- [ ] **Step 1: Write the implementation**

Create `.cline/skills/web-research/scripts/doctor.py`:

```python
#!/usr/bin/env python3
"""Print the skill location, Python version, and dependency status with exact install commands.

Run this after locating the skill dir. It self-reports its own directory via __file__, so it works
regardless of the current working directory.
"""
import os
import sys

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if SKILL_DIR not in sys.path:
    sys.path.insert(0, SKILL_DIR)

from lib import env  # noqa: E402

# pip command per group, in the order a user would install them.
GROUP_HINTS = {
    "core": "pip install requests beautifulsoup4 lxml",
    "search": "pip install ddgs",
    "extract": "pip install trafilatura markdownify",
    "render": "pip install playwright   (then: playwright install chromium)",
    "pdf": "pip install pypdf",
}


def main():
    print(f"Skill directory : {SKILL_DIR}")
    print(f"Python          : {sys.version.split()[0]}  (executable: {sys.executable})")
    ok_py = sys.version_info >= (3, 10)
    print(f"Python >= 3.10  : {'yes' if ok_py else 'NO — please use Python 3.10+'}")
    print("")
    status = env.check_deps()
    for group, members in status.items():
        present = [pip for pip, ok in members.items() if ok]
        missing = [pip for pip, ok in members.items() if not ok]
        label = "OK " if not missing else "MISSING"
        print(f"[{label}] {group:8s} present={present or '-'} missing={missing or '-'}")
        if missing:
            print(f"          install:  {GROUP_HINTS[group]}")
    print("")
    print("Note: only the 'core' group is required. Others are optional and used on demand.")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run it**

Run: `python .cline/skills/web-research/scripts/doctor.py`
Expected: prints the skill dir, Python version, and a per-group status table (most groups MISSING on
the dev machine — that is correct; doctor never installs anything).

- [ ] **Step 3: Checkpoint** — no commit. Pause for review.

---

## Task 7: Rewrite `scripts/web_read.py`

**Files:**
- Modify (full rewrite): `.cline/skills/web-research/scripts/web_read.py`

- [ ] **Step 1: Replace the file with the lib-based implementation**

Overwrite `.cline/skills/web-research/scripts/web_read.py`:

```python
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

from lib import engines, extract, pdf  # noqa: E402

MAX_CONTENT_LENGTH = 50_000


def _format_doc(doc, output_json, suggest_render):
    if output_json:
        return json.dumps(doc, ensure_ascii=False, indent=2)
    out = []
    for key in ("title", "author", "date", "sitename"):
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
    parser.add_argument("--raw", action="store_true", help="BeautifulSoup plain text only")
    parser.add_argument("--json", action="store_true", help="Output JSON")
    args = parser.parse_args()

    render = "always" if args.js else args.render
    actions = json.loads(args.actions) if args.actions else None

    try:
        result = engines.get_html(
            args.url, render=render, wait_for=args.wait_for, scroll=args.scroll,
            actions=actions, screenshot=args.screenshot,
        )
    except engines.RenderUnavailable as e:
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
```

- [ ] **Step 2: Verify the help screen renders** (no network, but needs core deps importable;
  if deps are missing, defer — do not install without asking):

Run: `python .cline/skills/web-research/scripts/web_read.py --help`
Expected: argparse help listing the flags above (requires requests/bs4 importable).

- [ ] **Step 3: Checkpoint** — no commit. Confirm the old `setup.sh` line is gone (the file was fully
  replaced). Pause for review.

---

## Task 8: Rewrite `scripts/web_search.py` (+ `--fetch` full content)

**Files:**
- Modify (full rewrite): `.cline/skills/web-research/scripts/web_search.py`

- [ ] **Step 1: Replace the file**

Overwrite `.cline/skills/web-research/scripts/web_search.py`:

```python
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
```

- [ ] **Step 2: Verify the help screen** (needs core deps importable; defer if missing):

Run: `python .cline/skills/web-research/scripts/web_search.py --help`
Expected: argparse help including `--fetch` and `--fetch-count`. Confirm no `setup.sh` text remains.

- [ ] **Step 3: Checkpoint** — no commit. Pause for review.

---

## Task 9: `scripts/web_map.py` (discover a site's URLs)

**Files:**
- Create: `.cline/skills/web-research/scripts/web_map.py`

- [ ] **Step 1: Write the implementation**

Create `.cline/skills/web-research/scripts/web_map.py`:

```python
#!/usr/bin/env python3
"""Discover URLs of a website from its sitemap(s) and homepage links.

Examples:
    python web_map.py "https://docs.python.org" --limit 100
    python web_map.py "https://example.com" --search blog --json
"""
import argparse
import json
import os
import re
import sys
from urllib.parse import urljoin, urlparse

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if SKILL_DIR not in sys.path:
    sys.path.insert(0, SKILL_DIR)

from lib import extract, http  # noqa: E402

_LOC_RE = re.compile(r"<loc>\s*([^<\s]+)\s*</loc>", re.I)
_MAX_SITEMAPS = 20


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
        text = http.get(start_url).text
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

    for u in _collect_sitemap(urljoin(origin, "/sitemap.xml"), host, include_subdomains, set()):
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
```

- [ ] **Step 2: Verify the help screen** (defer if core deps missing):

Run: `python .cline/skills/web-research/scripts/web_map.py --help`
Expected: argparse help listing `--search`, `--limit`, `--include-subdomains`, `--json`.

- [ ] **Step 3: Checkpoint** — no commit. Pause for review.

---

## Task 10: `scripts/web_crawl.py` (bounded same-domain crawl)

**Files:**
- Create: `.cline/skills/web-research/scripts/web_crawl.py`

- [ ] **Step 1: Write the implementation**

Create `.cline/skills/web-research/scripts/web_crawl.py`:

```python
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

from lib import engines, extract  # noqa: E402


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
```

- [ ] **Step 2: Verify the help screen** (defer if core deps missing):

Run: `python .cline/skills/web-research/scripts/web_crawl.py --help`
Expected: argparse help listing `--max-pages`, `--max-depth`, `--search`, `--render`, `--format`.

- [ ] **Step 3: Checkpoint** — no commit. Pause for review.

---

## Task 11: Update `requirements.txt`, rewrite `SKILL.md`, add `reference/capabilities.md`, clean `README.md`

**Files:**
- Modify: `.cline/skills/web-research/requirements.txt`
- Modify (full rewrite): `.cline/skills/web-research/SKILL.md`
- Create: `.cline/skills/web-research/reference/capabilities.md`
- Modify (full rewrite): `README.md`

- [ ] **Step 1: Update `requirements.txt`**

Overwrite `.cline/skills/web-research/requirements.txt`:

```
# Recommended baseline (core + search + extract). Optional extras installed on demand:
#   playwright  -> JS rendering / actions   (then: playwright install chromium)
#   pypdf       -> reading PDFs
requests>=2.31.0
beautifulsoup4>=4.12.0
lxml>=5.0.0
ddgs>=7.0.0
trafilatura>=2.0.0
markdownify>=0.13.0
```

- [ ] **Step 2: Rewrite `SKILL.md`**

Overwrite `.cline/skills/web-research/SKILL.md`:

```markdown
---
name: web-research
description: Searches the web and reads web pages into clean Markdown to find and fact-check current information. Renders JavaScript pages, parses PDFs, fetches full content for search results, and can map or crawl a site. Use whenever the user shares content to verify, asks about latest versions/releases/news/prices, gives a URL to read or summarize, hits an error to look up, or mentions a library/framework/term that should be checked against up-to-date sources instead of answered from memory.
---

# Web Research

Search the web and turn pages into clean Markdown using the scripts in `scripts/`. Run them from the
terminal.

**Core principle: do not search blindly.** Every search must answer a specific question. If you
cannot state "exactly what am I trying to find," do not search.

## First-time setup (do this once per session, in order)

### Step 1 — Find the Python command
Try these one at a time and read the actual output. Use the FIRST that prints a real `Python 3.x`
version (3.10 or newer). On Windows prefer `py`. Ignore a command that prints nothing or opens the
Microsoft Store (that is a non-functional stub). Do not chain them with `||` or redirect with
`2>/dev/null` — that fails in Windows shells.

1. `py -3 --version`
2. `python --version`
3. `python3 --version`

Use whichever worked as `<PY>` for every command below.

### Step 2 — Locate this skill's folder
The skill may be installed in the workspace or in your home folder. Find it with one command:

`<PY> -c "import os;n='web-research';cwd=os.getcwd();h=os.path.expanduser('~');c=[os.path.join(cwd,a,'skills',n) for a in ('.cline','.clinerules','.claude','.agents')]+[os.path.join(h,a,'skills',n) for a in ('.cline','.agents','.claude')];print(next((p for p in c if os.path.isdir(p)),'NOTFOUND'))"`

It prints the skill folder. Use it as `<SKILL>` below.

### Step 3 — Check the environment
Run: `<PY> "<SKILL>/scripts/doctor.py"`
It reports Python and which dependency groups are installed or missing, with the exact install
command for each.

### Step 4 — Install only what is needed, and ask first
Only the `core` group is required. `search` and `extract` make results much better; `render`
(Playwright) and `pdf` are used on demand. If something needed is missing, tell the user exactly
which packages and the command, and install only after they agree. For example:
`<PY> -m pip install requests beautifulsoup4 lxml ddgs trafilatura markdownify`
Never install without asking.

## When to use — when not to

Use it when: information changes over time (latest version, release, price, news); a specific
fact/number/API you are not 100% sure of; the user gives content to verify or a URL to read; an
error message to look up; a technology or term you only vaguely remember.

Do NOT use it (answer directly) when: stable knowledge you are confident about; the answer is already
in the codebase/context (read the file instead); pure reasoning or computation.

## Tools

```bash
# Search (add --fetch to pull full Markdown of the top results)
<PY> "<SKILL>/scripts/web_search.py" "Spring Boot latest version Java 21" -n 5
<PY> "<SKILL>/scripts/web_search.py" "<query>" --news --region vn-vi
<PY> "<SKILL>/scripts/web_search.py" "<query>" --fetch --fetch-count 3

# Read one page as Markdown
<PY> "<SKILL>/scripts/web_read.py" "https://..."
<PY> "<SKILL>/scripts/web_read.py" "<url>" --render always --scroll 3   # JS page / lazy load
<PY> "<SKILL>/scripts/web_read.py" "<url>" --selector "article" --format text
<PY> "<SKILL>/scripts/web_read.py" "<url>" --links

# Discover a site's URLs
<PY> "<SKILL>/scripts/web_map.py" "https://docs.example.com" --search guide

# Crawl a section of a site (bounded)
<PY> "<SKILL>/scripts/web_crawl.py" "https://docs.example.com/guide" --max-pages 15 --max-depth 2
```

If a read returns very little content, the page is probably JavaScript-rendered: re-run with
`--render always` (offer to install Playwright first if it is not installed). Full flag reference:
`reference/capabilities.md`.

## Workflow (in order)

1. **Decompose the request**: list the claims to verify, entities, versions, time markers.
2. **Decide whether a search is even needed.** If not, answer directly.
3. **Design the query** — one goal per query (details: `reference/search-strategy.md`).
4. **Run `web_search`** and read results: prefer authoritative sources, note the *date* and *domain*.
5. **`web_read` the most trustworthy source** to confirm — never conclude from snippets alone.
6. **Cross-check 2+ sources** when the information is important or sources disagree.
7. **Refine and iterate** if results are weak (~3 rounds max).
8. **Conclude and cite (URL)** with a verdict: **TRUE / FALSE / OUTDATED / INSUFFICIENT EVIDENCE**.

When the user pastes content to verify, or you need to craft a good query, read
`reference/search-strategy.md`.

## Query privacy

Queries are sent to an external search engine. Never put secrets, tokens, customer names, internal
hostnames, or proprietary code into a query — search only with public, generic terms.

## Presenting results

Cite the source (URL) for every fact taken from the web; state the *date* when the information is
time-sensitive; lead with the conclusion, then details. Do not fabricate — if nothing is found, say
so plainly ("insufficient evidence").
```

- [ ] **Step 3: Create `reference/capabilities.md`**

Create `.cline/skills/web-research/reference/capabilities.md`:

```markdown
# Capabilities & flag reference

All commands use `<PY>` (the detected Python) and `<SKILL>` (the located skill folder).

## doctor.py
`<PY> "<SKILL>/scripts/doctor.py"` — prints skill dir, Python version, and per-group dependency
status with exact install commands. Installs nothing.

## web_search.py
`<PY> "<SKILL>/scripts/web_search.py" "<query>" [flags]`
- `-n/--max-results N` (default 5)
- `-r/--region CODE` (e.g. `vn-vi`, `us-en`; default `wt-wt`)
- `--news` — news results
- `--fetch` / `--scrape` — fetch full Markdown of the top results
- `--fetch-count K` (default 3) — how many results to fetch content for
- `--json` — JSON output

Backends: DDGS API → DuckDuckGo HTML → Google HTML (automatic fallback).

## web_read.py
`<PY> "<SKILL>/scripts/web_read.py" "<url>" [flags]`
- `--format markdown|text|json` (default markdown)
- `--render auto|never|always` (default auto) / `--js` (= always)
- `--wait-for SELECTOR` — wait for a CSS selector (implies render)
- `--scroll N` — scroll-to-bottom N times (lazy-loaded content)
- `--actions JSON` — Playwright actions, e.g.
  `'[{"type":"click","selector":"#more"},{"type":"wait","ms":1000}]'`
  (types: `click`, `write` {selector,text}, `press` {key}, `scroll`, `wait` {selector|ms})
- `--selector CSS` / `-s` — extract a specific region as plain text
- `--max-length N` / `-m` (default 50000)
- `--links` — list links instead of content
- `--screenshot PATH` — full-page screenshot (implies render)
- `--raw` — BeautifulSoup plain text only
- `--json`

PDFs are detected automatically and parsed with `pypdf` (asks to install if missing).

## web_map.py
`<PY> "<SKILL>/scripts/web_map.py" "<url>" [flags]`
- `--search SUBSTR` — keep only URLs containing this substring
- `--limit N` (default 200)
- `--include-subdomains`
- `--json`

Sources: `<origin>/sitemap.xml` (+ sitemap indexes) and homepage links, same-domain only.

## web_crawl.py
`<PY> "<SKILL>/scripts/web_crawl.py" "<start-url>" [flags]`
- `--max-pages N` (default 20)
- `--max-depth D` (default 2)
- `--include-subdomains`
- `--search SUBSTR` — keep only pages whose URL/content contains this substring
- `--render auto|never|always` (default never)
- `--delay MS` — politeness delay between requests
- `--format markdown|json` (default markdown)
```

- [ ] **Step 4: Rewrite `README.md`**

Overwrite `README.md`:

```markdown
# web-research — web search & read skill for Cline

A skill that lets Cline **search the web** and **read web pages into clean Markdown**, render
JavaScript pages, parse PDFs, fetch full content for search results, and map or crawl a site. The
agent calls Python scripts from the terminal, and `SKILL.md` teaches it to **search precisely, not
blindly**.

## Structure

```
.cline/skills/web-research/
├── SKILL.md                  # frontmatter + main instructions (setup, tools, workflow)
├── requirements.txt          # recommended baseline deps
├── reference/
│   ├── search-strategy.md    # query design, good/bad examples, verification, privacy
│   └── capabilities.md       # full CLI flag reference
├── lib/                      # shared internals (env, http, engines, extract, pdf)
└── scripts/
    ├── doctor.py             # environment + dependency report
    ├── web_search.py         # search (DDGS → DuckDuckGo/Google HTML), optional full content
    ├── web_read.py           # URL → Markdown (JS render, PDF, actions, links)
    ├── web_map.py            # discover a site's URLs (sitemap + links)
    └── web_crawl.py          # bounded same-domain crawl → Markdown
.clinerules                   # pointer so Cline reads SKILL.md when needed
```

Cline loads skills from `.cline/skills/` (and `.clinerules/skills/`, `.claude/skills/`,
`.agents/skills/`, or the matching `~/...` global folders) automatically. The skill name and
description are preloaded; the full `SKILL.md` is read only when the skill activates.

## Install

```bash
pip install requests beautifulsoup4 lxml ddgs trafilatura markdownify

# Optional extras (installed on demand)
pip install playwright && playwright install chromium   # JS rendering / actions
pip install pypdf                                        # reading PDFs

# Check your environment
python .cline/skills/web-research/scripts/doctor.py

# Try it
python .cline/skills/web-research/scripts/web_search.py "python 3.13 release date" -n 3
python .cline/skills/web-research/scripts/web_read.py "https://example.com"
```

Requires Python 3.10+ and internet access.

## Capabilities

- **Clean Markdown output** — trafilatura → markdownify → BeautifulSoup fallback chain.
- **JavaScript rendering** — optional Playwright engine with actions (click, scroll, wait, write,
  press) and screenshots; automatic fallback to static fetch.
- **PDF parsing** — detected automatically, extracted with pypdf.
- **Full-content search** — `web_search --fetch` returns Markdown for the top results.
- **Map & crawl** — discover a site's URLs, or crawl a bounded section into Markdown.
- **Robust fetching** — shared headers, SSL-verify fallback, retry with backoff.

## Dependencies

| Group | Packages | Purpose |
|---|---|---|
| core (required) | `requests`, `beautifulsoup4`, `lxml` | HTTP + HTML parsing |
| search | `ddgs` | primary search backend (HTML fallback if absent) |
| extract | `trafilatura`, `markdownify` | clean Markdown + metadata |
| render (optional) | `playwright` | JS pages, actions, screenshots |
| pdf (optional) | `pypdf` | read PDFs |

The scripts check dependencies and fall back gracefully; `SKILL.md` has the agent ask before
installing anything.

## Sharing with your team

Copy the `.cline/skills/web-research/` directory and the `.clinerules` file into any workspace, or
copy `web-research/` to `~/.cline/skills/` (global) so it applies to all projects.
```

- [ ] **Step 5: Run the full test suite + doctor**

Run: `python -m unittest discover -s .cline/skills/web-research/tests -v`
Expected: all tests pass or skip (none fail).
Run: `python .cline/skills/web-research/scripts/doctor.py`
Expected: a clean report.

- [ ] **Step 6: Checkpoint** — no commit. Confirm no file mentions MCP, API keys, or `setup.sh`:
  `grep -rinE "mcp|api key|api-key|setup\.sh" .cline/skills/web-research README.md`
  Expected: no matches (the word "key" inside other words like "keyword" is fine — review hits).

---

## Task 12: Live smoke test (after deps are installed, with user consent)

**Files:** none (manual verification).

These need network and the baseline deps installed. Run only after the user has approved installing
them. Replace `python` with `<PY>`.

- [ ] **Step 1: Baseline search + read**

```bash
python .cline/skills/web-research/scripts/web_search.py "python 3.13 release date" -n 3
python .cline/skills/web-research/scripts/web_read.py "https://example.com"
```
Expected: search prints titles+URLs; read prints `Extraction: trafilatura` (or markdownify) and the
page text as Markdown.

- [ ] **Step 2: Full-content search + map**

```bash
python .cline/skills/web-research/scripts/web_search.py "firecrawl github" --fetch --fetch-count 1
python .cline/skills/web-research/scripts/web_map.py "https://docs.python.org/3/" --search library --limit 30
```
Expected: search shows a `--- content ---` block; map lists same-domain URLs containing "library".

- [ ] **Step 3: JS render (only if Playwright approved/installed)**

```bash
python .cline/skills/web-research/scripts/web_read.py "https://example.com" --render always
```
Expected: `Extraction: ...` with `engine_used` playwright path exercised (no error).

- [ ] **Step 4: Checkpoint** — report results to the user. No commit.

---

## Self-review notes (author)

- **Spec coverage:** env/doctor (T1,T6), http+SSL/retry (T2), Markdown extract+metadata+links (T3),
  PDF (T4), engines+render+actions+selection (T5), web_read rewrite incl. setup.sh removal (T7),
  web_search +full content +setup.sh removal (T8), map (T9), crawl (T10), requirements+SKILL.md
  (Windows Python fix, path probe incl. `.agents`, ask-before-install, no MCP/key wording)
  +capabilities+README cleanup (T11), live smoke (T12). All spec sections mapped.
- **Type/name consistency:** `find_skill_dir`, `check_deps`, `missing_pip_packages`, `DEP_GROUPS`,
  `SKILL_NAME` (env); `get` (http); `to_document`, `extract_links`, `truncate` (extract);
  `looks_like_pdf`, `extract_pdf` (pdf); `fetch_html`, `render_html`, `get_html`, `RenderUnavailable`
  (engines) — used consistently across scripts.
- **Commits:** intentionally omitted (user instruction); checkpoints used instead.
```
