---
name: web-research
description: Searches the web and reads web pages into clean Markdown to find and fact-check current information. Renders JavaScript pages, parses PDFs, fetches full content for search results, and can map or crawl a site. Use whenever the user shares content to verify, asks about latest versions/releases/news/prices, gives a URL to read or summarize, hits an error to look up, or mentions a library/framework/term that should be checked against up-to-date sources instead of answered from memory.
---

# Web Research

Search the web and turn pages into clean Markdown using the scripts in `scripts/`. Run them from the
terminal. Everything you need is in this file — there are no separate reference docs to open.

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

### Step 4 — Install what's needed, and ask first
The needed baseline is the `core`, `search`, and `extract` groups — install them so the skill works
well (ask the user, then run):
`<PY> -m pip install requests beautifulsoup4 lxml ddgs trafilatura markdownify`
Every other group is optional and installed only when a task actually needs it — ask the user each
time before installing: `render` (Playwright — JS pages/actions), `pdf` (pypdf), `office`
(mammoth, openpyxl — DOCX/XLSX), `impersonate` (curl_cffi — bypass bot blocks). Always name the exact
packages and the command, and install only after the user agrees. Never install without asking.

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
curl_cffi first if needed. `web_read` also parses PDF/DOCX/XLSX automatically and can dump a page's
JSON-LD with `--jsonld`; fetches to private/loopback addresses are refused unless you pass
`--allow-local`. The complete flag list for every tool is in **Full flag reference** below.

## Full flag reference

Every tool also accepts `--proxy URL` (or set the `WEB_RESEARCH_PROXY` / `HTTPS_PROXY` env var) to
route requests through a proxy. Private/loopback addresses are refused by default; add `--allow-local`
to permit them.

### doctor.py
`<PY> "<SKILL>/scripts/doctor.py"` — prints skill dir, Python version, and per-group dependency
status with exact install commands. Installs nothing.

### web_search.py
`<PY> "<SKILL>/scripts/web_search.py" "<query>" [flags]`
- `-n/--max-results N` (default 5)
- `-r/--region CODE` (e.g. `vn-vi`, `us-en`; default `wt-wt`)
- `--news` — news results
- `--fetch` / `--scrape` — fetch full Markdown of the top results
- `--fetch-count K` (default 3) — how many results to fetch content for
- `--json` — JSON output

Backends: DDGS API → DuckDuckGo HTML → Google HTML (automatic fallback).

### web_read.py
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
- `--impersonate` — use curl_cffi (real Chrome TLS fingerprint) to bypass TLS-based bot blocks
- `--jsonld` — dump JSON-LD (schema.org) structured data instead of content
- `--allow-local` — allow private/loopback addresses (refused by default)
- `--raw` — BeautifulSoup plain text only
- `--json`

PDF, DOCX and XLSX files are detected automatically and parsed (pypdf / mammoth / openpyxl; asks to
install if missing). A plain fetch that hits HTTP 403/429 auto-retries with curl_cffi impersonation
when it is installed.

### web_map.py
`<PY> "<SKILL>/scripts/web_map.py" "<url>" [flags]`
- `--search SUBSTR` — keep only URLs containing this substring
- `--limit N` (default 200)
- `--include-subdomains`
- `--json`

Sources: `<origin>/sitemap.xml`, sitemaps listed in `robots.txt`, nested sitemap indexes and
gzipped (`.gz`) sitemaps, plus homepage links — same-domain only.

### web_crawl.py
`<PY> "<SKILL>/scripts/web_crawl.py" "<start-url>" [flags]`
- `--max-pages N` (default 20)
- `--max-depth D` (default 2)
- `--include-subdomains`
- `--search SUBSTR` — keep only pages whose URL/content contains this substring
- `--render auto|never|always` (default never)
- `--delay MS` — politeness delay between requests
- `--ignore-robots` — crawl URLs even if robots.txt disallows them (default: respect robots.txt)
- `--format markdown|json` (default markdown)

## Search strategy — query design & verification

Use this when crafting a query or verifying pasted content.

### Query design

- **Extract the core keywords**, drop filler ("how do I", "please", "what do you think").
- **Use exact entities + versions**: `<name> <version> <official term>`.
- **Technical topics → use English** (primary documentation is mostly in English).
- **Add intent qualifiers**: `latest`, `release notes`, `changelog`, `documentation`, `vs`,
  `deprecated`, `migration guide`, plus a year if you need a time anchor.
- **One goal per query.** Need several things → run several separate queries.

### Search operators

Pass these literally inside the `query` string:

- `"exact phrase"` — keep a phrase/name/error message intact.
- `site:domain` — restrict the source, e.g. `site:docs.python.org`, `site:github.com`.
- Error messages: keep them **verbatim in quotes**, but strip the volatile parts (absolute paths,
  line numbers, memory addresses) so the query matches more cases.

### Good vs Bad examples

| User request | ❌ Bad query | ✅ Good query |
|---|---|---|
| "Does the latest Spring Boot support Java 21?" | `spring boot java` | `Spring Boot latest version Java 21 support site:spring.io` → then read the release notes page |
| Error `NoClassDefFoundError: javax/xml/bind/JAXBException` on Java 11 | `java jaxb error` | `"NoClassDefFoundError" "javax/xml/bind/JAXBException" Java 11 fix` |
| "Did React 19 remove forwardRef?" | `react forwardRef` | `React 19 forwardRef deprecated site:react.dev` → read the blog/docs → TRUE/FALSE verdict |
| "Which version of library X is most stable?" | `X library` | `<X> latest stable release` + `site:github.com <X> releases` → read the Releases page |
| "Compare Postgres vs MySQL for analytics" | `postgres mysql` | `PostgreSQL vs MySQL OLAP analytical workload comparison` → read 2 sources, cross-check |

### Source priority

1. Official documentation / website (docs, project home, release notes, RFC, spec).
2. The upstream GitHub repo (README, CHANGELOG, issues, releases).
3. Reputable sources (MDN, highly-upvoted Stack Overflow, the author's/org's own blog).
4. Everything else: treat as a lead, cross-check before trusting.

Beware SEO spam, AI-generated filler, and stale docs. Always check the **publication date**.

### Verifying user-pasted content

1. **Split into individual factual claims** (one asserted fact per statement).
2. For each claim → one `web_search` → `web_read` the original source.
3. Label each claim: **TRUE / FALSE / OUTDATED / INSUFFICIENT EVIDENCE** + source URL.
4. If FALSE → give the correct information with a source. If sources conflict → present both sides.
5. **Do not fabricate.** If nothing is found, say so; do not guess.

## Workflow (in order)

1. **Decompose the request**: list the claims to verify, entities, versions, time markers.
2. **Decide whether a search is even needed.** If not, answer directly.
3. **Design the query** — one goal per query (see **Search strategy** above).
4. **Run `web_search`** and read results: prefer authoritative sources, note the *date* and *domain*.
5. **`web_read` the most trustworthy source** to confirm — never conclude from snippets alone.
6. **Cross-check 2+ sources** when the information is important or sources disagree.
7. **Refine and iterate** if results are weak (~3 rounds max).
8. **Conclude and cite (URL)** with a verdict: **TRUE / FALSE / OUTDATED / INSUFFICIENT EVIDENCE**.

## Query privacy

Queries leave the machine and reach an external search engine. Do **not** put secrets, tokens, API
keys, customer names, internal hostnames/service names, or proprietary code into a query. Search only
with public, generic terms. If the information you need to look up is itself confidential, do not
search for it — a web search cannot help with internal data anyway.

## Presenting results

Cite the source (URL) for every fact taken from the web; state the *date* when the information is
time-sensitive; lead with the conclusion, then details. Do not fabricate — if nothing is found, say
so plainly ("insufficient evidence").
