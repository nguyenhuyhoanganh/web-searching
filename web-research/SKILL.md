---
name: web-research
description: Searches the web and reads web pages to find and fact-check current information. Use whenever the user shares content to verify, asks about latest versions/releases/news/prices, provides a URL to read or summarize, hits an error message to look up, or mentions a library, framework, or term that should be checked against up-to-date sources instead of answered from memory.
---

# Web Research

Search the web and read page content to find or verify information, using the two scripts in
`scripts/`. Invoke them from the terminal (`execute_command`) — no MCP and no API key required.

**Core principle: do not search blindly.** Every search must answer a specific question. If you
cannot state "exactly what am I trying to find," do not search.

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

Run from this skill directory. Prefer the `.venv` interpreter if you ran `bash setup.sh`; otherwise
use `python3`.

```bash
# Search
python3 scripts/web_search.py "Spring Boot latest version Java 21 support" -n 5
python3 scripts/web_search.py "<query>" --news          # news
python3 scripts/web_search.py "<query>" --region vn-vi  # Vietnam content
python3 scripts/web_search.py "<query>" --json          # JSON for parsing

# Read a page
python3 scripts/web_read.py "https://..."               # extract main content
python3 scripts/web_read.py "<url>" --selector "article" # extract a specific part via CSS
python3 scripts/web_read.py "<url>" --max-length 5000
python3 scripts/web_read.py "<url>" --links             # list links on the page
```

`web_search`: `-n/--max-results` (default 5), `-r/--region`, `--news`, `--answers`, `--json`.
`web_read`: `-s/--selector`, `-m/--max-length` (default 50000), `--raw`, `--links`, `--json`.

Note: `web_read` only reads static HTML — JavaScript-rendered pages may come back incomplete.

## Query privacy

Queries are sent to an external search engine. **Never** put secrets, tokens, customer names,
internal hostnames, or proprietary code into a query — search only with public, generic terms.

## Presenting results

Cite the source (URL) for every fact taken from the web; state the *date* when the information is
time-sensitive; lead with the conclusion, then details. Do not fabricate — if nothing is found, say
so plainly ("insufficient evidence").
