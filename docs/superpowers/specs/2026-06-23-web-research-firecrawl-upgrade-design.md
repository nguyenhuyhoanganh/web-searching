# web-research skill — Firecrawl-inspired upgrade (design)

Date: 2026-06-23
Status: approved (pending written-spec review)

## Goal

Take everything good from Firecrawl that helps an AI agent **search**, **read**, and
**understand** the web, and fold it into the existing `web-research` Cline skill — **without**
requiring any API key or MCP server, and without any paid/hosted infrastructure. The skill keeps its
"don't search blindly" discipline; the new code makes the *data it returns* dramatically better for
an LLM (clean Markdown, JS-rendered pages, PDFs, full-content search, site map/crawl).

The skill runs primarily on **Windows**. The agent that drives it is Cline (an LLM), so the
"intelligence" layer (structured extraction, summarisation, judgement) stays with the agent — the
scripts only deliver clean, faithful content.

## Constraints (hard requirements)

1. **No API key, no MCP.** Nothing in the skill may require either.
2. **The skill must not mention MCP or keys at all.** SKILL.md, reference docs, and script output
   describe only what the skill *does*, never what it deliberately leaves out.
3. **Windows-first.** All environment detection must work in `cmd` and PowerShell, not just bash.
4. **Ask before installing.** Scripts/agent self-check dependencies first. If something is missing,
   the agent tells the user exactly what and the `pip`/`npm` command, and installs **only after the
   user agrees**. Scripts never auto-install; they only print the command.
5. **Graceful degradation.** Core stays tiny (requests + bs4 + lxml). Every advanced capability
   (Playwright, PDF, markdown libs) is optional and the tool falls back when it is absent — mirroring
   Firecrawl's engine-fallback philosophy.
6. **Process constraints for this work:** stay on branch `claude/cline-web-skill-no-mcp`; **do not
   commit and do not create branches.** (Overrides the brainstorming skill's "commit the spec" step.)

## Skill install locations & path resolution

A skill directory named `web-research` may live in any of these (confirmed against Cline docs, plus
`.agent/` which Cline also reads for cross-agent skills):

- Project: `<workspace>/.cline/skills/`, `.clinerules/skills/`, `.claude/skills/`, `.agent/skills/`
- Global: `~/.cline/skills/`, `~/.agent/skills/`, `~/.claude/skills/`
  (on Windows `~` ⇒ `C:\Users\USERNAME`)

**Problem:** the agent must run the *right* copy of a script, but it cannot assume the terminal's CWD
is the skill dir. **Solution:** locate the skill dir with one cross-platform Python probe (Python's
`os.path.expanduser("~")` resolves `%USERPROFILE%` on Windows; `os.getcwd()` is the workspace root):

```
<PY> -c "import os;n='web-research';cwd=os.getcwd();h=os.path.expanduser('~');c=[os.path.join(cwd,a,'skills',n) for a in ('.cline','.clinerules','.claude','.agent')]+[os.path.join(h,a,'skills',n) for a in ('.cline','.agent','.claude')];print(next((p for p in c if os.path.isdir(p)),'NOTFOUND'))"
```

It prints the absolute skill dir; the agent uses that as the base path for every `scripts/...` call.
Independently, **every script resolves its own `lib/` package via `__file__`** (not CWD), so scripts
run correctly no matter where they are invoked from.

## The three fixes requested

1. **Remove `setup.sh`.** Delete the two `"Or run the setup script: bash setup.sh"` lines in
   `web_search.py` and `web_read.py`. `setup.sh` no longer exists; the import-error message instead
   prints the exact `pip install ...` command only.
2. **Fix Windows Python detection.** The current
   `python3 --version 2>/dev/null || python --version 2>/dev/null || py --version 2>/dev/null` breaks
   in `cmd`/PowerShell (`2>/dev/null` and `||` are bash-isms) and mis-handles the Microsoft Store
   stub. New approach in SKILL.md: try the commands **individually, reading the real output**, in
   this order, and use the first that prints a genuine `Python 3.x` (>= 3.10):
   `py -3 --version` → `python --version` → `python3 --version`. Ignore a command that prints nothing
   or opens the Microsoft Store (the Store stub prints nothing to stdout). No shell redirection or
   `||` chaining anywhere.
3. **Robust script-path resolution.** The Python probe above + `__file__`-based `lib/` resolution.

## Architecture

```
.cline/skills/web-research/
├── SKILL.md                  # concise, AI-facing; never mentions MCP/keys
├── requirements.txt          # recommended baseline deps (core + search + extract)
├── reference/
│   ├── search-strategy.md    # kept, lightly refined
│   └── capabilities.md       # NEW: full flag reference for every tool
├── lib/                      # internal shared package (resolved via __file__)
│   ├── __init__.py
│   ├── env.py                # dep groups, dep-check, skill-dir probe (importable)
│   ├── http.py               # shared GET: headers, SSL fallback, retry/backoff
│   ├── engines.py            # fetch (requests) + playwright engines, fallback chain, actions
│   ├── extract.py            # HTML→Markdown + metadata + links (trafilatura→markdownify→bs4)
│   └── pdf.py                # PDF detection + text extraction (optional pypdf)
└── scripts/
    ├── doctor.py             # prints skill dir + python + per-dep status + pip commands
    ├── web_search.py         # search (+ optional full-content fetch of results)
    ├── web_read.py           # one URL → Markdown (engine fallback, JS render, PDF, actions)
    ├── web_map.py            # NEW: discover a site's URLs (sitemap + same-domain links)
    └── web_crawl.py          # NEW: bounded same-domain crawl → Markdown per page
```

### Dependency groups (single source of truth in `lib/env.py`)

| Group | pip packages | Purpose | If missing |
|---|---|---|---|
| CORE (required) | `requests`, `beautifulsoup4`, `lxml` | HTTP + HTML parsing | nothing works — must install |
| SEARCH | `ddgs` | primary search backend | fall back to DDG/Google HTML scrape |
| EXTRACT | `trafilatura`, `markdownify` | clean Markdown + metadata | fall back: trafilatura→markdownify→bs4 text |
| RENDER | `playwright` (+ `playwright install chromium`) | JS-rendered pages, actions, screenshots | fall back to requests (static HTML only) |
| PDF | `pypdf` | extract text from PDFs | report that PDF needs pypdf |

Import-name→pip-name mapping (e.g. `bs4`→`beautifulsoup4`) lives in `env.py`. `requirements.txt`
lists CORE + SEARCH + EXTRACT (the recommended baseline); RENDER and PDF are installed on demand.

## Components

### lib/env.py
- `DEP_GROUPS`: dict of group → list of (import_name, pip_name).
- `find_skill_dir() -> str`: the probe logic, importable and reused by `doctor.py`.
- `check_deps() -> dict`: `{group: {pip_name: bool}}` by attempting imports.
- `missing_install_commands() -> list[str]`: exact `pip install ...` lines for missing groups.

### lib/http.py
- `DEFAULT_HEADERS` (realistic desktop UA).
- `get(url, timeout=30, retries=3) -> requests.Response`: SSL-verify fallback on `SSLError`
  (verify once, retry without on failure), exponential backoff (2s, 4s) on Connection/Timeout,
  raise on HTTP errors. Centralises logic currently duplicated across the two scripts.
- `head_content_type(url) -> str | None` (best-effort, for PDF detection).

### lib/engines.py
- `fetch_html(url) -> {html, final_url, content_type, status}` via `http.get`.
- `render_html(url, wait_for=None, scroll=0, actions=None, screenshot=None, timeout=30000) -> {html, ...}`
  via Playwright sync API (headless Chromium): `goto(wait_until="networkidle")`, optional
  `wait_for` selector, optional `scroll` (N scroll-to-bottom passes for lazy content), optional
  `actions` list, optional screenshot. Raises `RenderUnavailable` with an install hint if Playwright
  isn't installed.
- `actions` schema (all key-free, Firecrawl-style): list of
  `{type: "click"|"write"|"press"|"scroll"|"wait", selector?, text?, key?, ms?}`.
- `get_html(url, render="auto"|"never"|"always", ...)`: engine selection. `never`→fetch only.
  `always`→render. `auto`→fetch first; if the page looks JS-gated (extracted text below a threshold,
  or an empty-ish body with heavy scripts), try render **if available**; otherwise return the fetched
  HTML plus a `suggest_render` flag so the caller can advise installing Playwright. Returns
  `{html, engine_used, suggest_render}`.

### lib/extract.py
- `to_document(html, url, fmt="markdown") -> dict`:
  `{title, author, date, sitename, description, content, method}`.
  - trafilatura present: `extract(html, url=url, output_format="markdown", include_links=True,
    include_tables=True, include_comments=False)` for content; metadata via a JSON extract pass.
  - else markdownify present: pick main node (article/main/[role=main]/heuristic) via bs4 →
    `markdownify(...)`.
  - else: bs4 text (current behaviour). `fmt="text"` forces plain text; `fmt="json"` returns the dict.
- `extract_links(html, base_url) -> list[{text, url}]` (moved out of web_read).
- `truncate(content, max_length)` helper (keeps the `... [content truncated]` marker).

### lib/pdf.py
- `looks_like_pdf(url, content_type, first_bytes) -> bool` (`.pdf`, `application/pdf`, `%PDF` magic).
- `extract_pdf(content_bytes) -> {title, author, content, pages}` via pypdf; raise with install hint
  if pypdf missing.

### scripts/doctor.py
Prints: the skill dir (from `__file__`), Python version + whether >= 3.10, and for each dep group:
present/missing with the exact `pip install` command for anything missing; for RENDER, also note
`playwright install chromium` may be required. One concise human+agent-readable report. Exit 0 always
(it's a report, not a gate).

### scripts/web_read.py
Flags: `url`, `--format markdown|text|json` (default `markdown`), `--render auto|never|always`
(`--js` = `always`), `--wait-for SELECTOR`, `--scroll N`, `--actions JSON`, `--selector CSS`,
`--max-length` (default 50000), `--links`, `--screenshot PATH`, `--raw` (bs4 text).
Pipeline: `get_html` (engine) → if PDF → `pdf.extract_pdf` → else `extract.to_document` → print a
metadata header (title/author/date/url/engine) then content. If `get_html` returned `suggest_render`,
print a one-line hint that the page may be JS-rendered and Playwright would help (agent decides
whether to ask the user to install).

### scripts/web_search.py
Existing behaviour (DDGS → DDG HTML → Google HTML fallback chain, `--news`, `--answers`, `--region`,
`-n`, `--json`) **plus**: `--fetch` (a.k.a. `--scrape`) to `web_read` the top results and include
their Markdown, `--fetch-count K` (default 3), `--format`. Reuses `engines`/`extract`. Remove the
`setup.sh` line from the import-error message.

### scripts/web_map.py (new)
`url`, `--search TERM` (substring filter), `--limit N` (default 200), `--include-subdomains`,
`--json`. Logic: fetch `<origin>/sitemap.xml` (+ bounded sitemap-index recursion), parse `<loc>`;
also fetch the homepage and collect same-domain links; merge, dedupe, filter; print the URL list.

### scripts/web_crawl.py (new)
`url` (start), `--max-pages N` (default 20, hard cap), `--max-depth D` (default 2),
`--include-subdomains`, `--search TERM`, `--format markdown|json`, `--delay MS` (politeness),
`--render auto|never|always`. BFS within the same domain via the engine layer; extract Markdown per
page; optionally seed from sitemap. Output: concatenated Markdown (with per-page headers) or JSON
list of `{url, title, markdown}`. Bounded so it can't run away.

## SKILL.md rewrite (structure)

1. Frontmatter: `name: web-research`; `description` updated to mention clean Markdown, JS pages,
   PDFs, full-content search, and site map/crawl — framed around research & fact-checking. No
   mention of MCP/keys.
2. Core principle: "do not search blindly" (kept).
3. **First-time setup** (mandatory, in order):
   - Step 1 — detect Python (Windows-aware, the three commands tried individually, no redirection).
   - Step 2 — locate the skill dir (the probe one-liner).
   - Step 3 — run `doctor.py` to see Python + dependency status.
   - Step 4 — **ask-before-install** policy spelled out: if CORE is missing, tell the user what's
     missing + the pip command and ask before installing; for optional groups (RENDER/PDF), ask only
     when the current task needs them.
4. **Tools**: web_search, web_read, web_map, web_crawl with their key flags and one example each.
5. JS note: if a read returns little content, the page may be JS-rendered — offer to install
   Playwright (ask the user first).
6. Workflow (the disciplined decompose→search→read-source→cross-check→verdict flow, kept).
7. Query privacy (kept — it's about not leaking secrets into queries, unrelated to MCP/keys).
8. Presenting results (kept).

## README.md cleanup

Remove all "no-MCP"/"no API key" selling points and the "Can you use MCP? See branch …" line.
Reframe as a powerful local web-research skill for Cline. Update the structure diagram, the tool
list (add map/crawl, Markdown, JS rendering, PDF), the dependency section (core vs optional), and the
install/usage examples. Keep it accurate to the new code.

## Testing

Network- and install-free unit tests for the pure logic (run on the dev machine):
- `extract.to_document` on a fixed HTML string → expected Markdown/metadata.
- `extract_links` and sitemap/`<loc>` parsing on fixed inputs.
- `pdf.looks_like_pdf` on magic bytes / content-types / URLs.
- `env.find_skill_dir` against a temp dir layout; import→pip name mapping.
- Python-name selection logic (the >=3.10 / Store-stub rule), as a documented checklist for the
  agent (it's agent behaviour, not a script function).

Network-dependent behaviour (live search, render, crawl) is covered by a short manual smoke-test
checklist in the spec/README, run after the user approves installing the optional deps.

## Out of scope (needs a key/LLM or heavy infra — deliberately excluded, and not mentioned in SKILL.md)

LLM JSON-extraction, summarisation, deep-research, paid rotating proxies, persistent change-tracking.
The agent (Cline) performs any LLM-shaped step on the clean Markdown the skill returns.
