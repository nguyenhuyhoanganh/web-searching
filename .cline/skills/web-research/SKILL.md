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

`<PY> -c "import os;n='web-research';cwd=os.getcwd();h=os.path.expanduser('~');c=[os.path.join(cwd,a,'skills',n) for a in ('.cline','.clinerules','.claude','.agent')]+[os.path.join(h,a,'skills',n) for a in ('.cline','.agent','.claude')];print(next((p for p in c if os.path.isdir(p)),'NOTFOUND'))"`

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
`--render always` (offer to install Playwright first if it is not installed). If a page is blocked as
a bot (HTTP 403 or a challenge wall), try `--impersonate` (curl_cffi, real Chrome TLS fingerprint) or
route through a proxy with `--proxy <url>` / the `WEB_RESEARCH_PROXY` env var — offer to install
curl_cffi first if needed. Full flag reference: [reference/capabilities.md](reference/capabilities.md).

## Reference docs

Read these bundled files when relevant. They sit in this skill's `reference/` folder — if a bare
relative path does not resolve (for example the skill is installed globally and the workspace is a
different folder), read them at `<SKILL>/reference/` instead.

- [reference/search-strategy.md](reference/search-strategy.md) — query design, search operators,
  good vs bad examples, source priority, and a claim-verification workflow. Read before crafting a
  query or verifying pasted content.
- [reference/capabilities.md](reference/capabilities.md) — the full CLI flag reference for every tool.

## Workflow (in order)

1. **Decompose the request**: list the claims to verify, entities, versions, time markers.
2. **Decide whether a search is even needed.** If not, answer directly.
3. **Design the query** — one goal per query (see [reference/search-strategy.md](reference/search-strategy.md)).
4. **Run `web_search`** and read results: prefer authoritative sources, note the *date* and *domain*.
5. **`web_read` the most trustworthy source** to confirm — never conclude from snippets alone.
6. **Cross-check 2+ sources** when the information is important or sources disagree.
7. **Refine and iterate** if results are weak (~3 rounds max).
8. **Conclude and cite (URL)** with a verdict: **TRUE / FALSE / OUTDATED / INSUFFICIENT EVIDENCE**.

When the user pastes content to verify, or you need to craft a good query, read
[reference/search-strategy.md](reference/search-strategy.md).

## Query privacy

Queries are sent to an external search engine. Never put secrets, tokens, customer names, internal
hostnames, or proprietary code into a query — search only with public, generic terms.

## Presenting results

Cite the source (URL) for every fact taken from the web; state the *date* when the information is
time-sensitive; lead with the conclusion, then details. Do not fabricate — if nothing is found, say
so plainly ("insufficient evidence").
