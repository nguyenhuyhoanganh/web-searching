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
