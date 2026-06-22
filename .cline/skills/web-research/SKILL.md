---
name: web-research
description: Searches the web and reads web pages to find and fact-check current information. Use whenever the user shares content to verify, asks about latest versions/releases/news/prices, provides a URL to read or summarize, hits an error message to look up, or mentions a library, framework, or term that should be checked against up-to-date sources instead of answered from memory.
---

# Web Research

Search the web and read page content to find or verify information, using the two scripts in
`scripts/`. Invoke them from the terminal (`execute_command`) — no MCP and no API key required.

**Core principle: do not search blindly.** Every search must answer a specific question. If you
cannot state "exactly what am I trying to find," do not search.

## Before first use — check environment, install if needed

**You MUST run these checks the first time you use the skill in a session.** Do not skip this.

### Step 1: Detect the Python command

```bash
python3 --version 2>/dev/null || python --version 2>/dev/null || py --version 2>/dev/null
```

Use the first command that succeeds and has version >= 3.10. Store it — e.g. `PYTHON_CMD=python3`.

### Step 2: Locate the skill directory

```bash
SKILL_DIR="$(git rev-parse --show-toplevel)/.cline/skills/web-research"
```

If `git` is unavailable: `find . -path "*/.cline/skills/web-research/scripts/web_search.py" -print -quit 2>/dev/null`

### Step 3: Check dependencies — install if missing

Run this **one command** to check all required + recommended packages at once:

```bash
$PYTHON_CMD -c "import requests; from bs4 import BeautifulSoup; from ddgs import DDGS; import trafilatura; print('ALL OK')"
```

**If it prints `ALL OK`** → skip to "Running the scripts" below.

**If it fails** → install everything in one go:

```bash
$PYTHON_CMD -m pip install requests beautifulsoup4 ddgs trafilatura lxml
```

Then re-run the check command above to confirm.

> **Do not skip installation.** `ddgs` provides the primary search engine; `trafilatura` provides
> accurate content extraction. Without them the scripts fall back to less reliable methods and will
> print warnings on every run.

## When to use — when not to

Use it when: information changes over time (latest version, release, price, news); a specific
fact/number/API you are not 100% sure of; the user gives content to verify; the user gives a URL to
read; an error message to look up; a technology or term you only vaguely remember.

Do NOT use it (answer directly) when: stable knowledge you are confident about; the answer is
already in the codebase/context (read the file instead of searching); pure reasoning or computation.

## Workflow (in order)

1. **Decompose the request**: list the claims to verify, entities, versions, and time markers.
2. **Decide whether a search is even needed.** If not, answer directly.
3. **Design the query** — one goal per query (details: `reference/search-strategy.md`).
4. **Run `web_search`** and read the results: prefer authoritative sources, note the *date* and *domain*.
5. **`web_read` the most trustworthy source** to confirm — never conclude from snippets alone.
6. **Cross-check 2+ sources** when the information is important or sources disagree.
7. **Refine and iterate** if results are weak (change keywords/qualifiers/source, ~3 rounds max).
8. **Conclude and cite (URL)**, with an explicit verdict: **TRUE / FALSE / OUTDATED / INSUFFICIENT EVIDENCE**.

When the user pastes content to verify, or you need to craft a good query, read
`reference/search-strategy.md` (good-vs-bad examples, search operators, a claim-verification
workflow, and query-privacy guidance).

## Running the scripts

Use the detected Python command and resolved script directory from the setup section above.

```bash
# Search
$PYTHON_CMD "$SKILL_DIR/scripts/web_search.py" "Spring Boot latest version Java 21 support" -n 5
$PYTHON_CMD "$SKILL_DIR/scripts/web_search.py" "<query>" --news          # news
$PYTHON_CMD "$SKILL_DIR/scripts/web_search.py" "<query>" --region vn-vi  # Vietnam content
$PYTHON_CMD "$SKILL_DIR/scripts/web_search.py" "<query>" --json          # JSON for parsing

# Read a page
$PYTHON_CMD "$SKILL_DIR/scripts/web_read.py" "https://..."               # extract main content
$PYTHON_CMD "$SKILL_DIR/scripts/web_read.py" "<url>" --selector "article" # CSS selector
$PYTHON_CMD "$SKILL_DIR/scripts/web_read.py" "<url>" --max-length 5000
$PYTHON_CMD "$SKILL_DIR/scripts/web_read.py" "<url>" --links             # list links
```

`web_search`: `-n/--max-results` (default 5), `-r/--region`, `--news`, `--answers`, `--json`.
`web_read`: `-s/--selector`, `-m/--max-length` (default 50000), `--raw`, `--links`, `--json`.

Note: `web_read` only reads static HTML — JavaScript-rendered pages may come back incomplete.
Connection errors are retried automatically up to 3 times with backoff. Check stderr for logs.

## Query privacy

Queries are sent to an external search engine. **Never** put secrets, tokens, customer names,
internal hostnames, or proprietary code into a query — search only with public, generic terms.

## Presenting results

Cite the source (URL) for every fact taken from the web; state the *date* when the information is
time-sensitive; lead with the conclusion, then details. Do not fabricate — if nothing is found, say
so plainly ("insufficient evidence").
