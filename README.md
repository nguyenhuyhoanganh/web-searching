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
`.agent/skills/`, or the matching `~/...` global folders) automatically. The skill name and
description are preloaded; the full `SKILL.md` is read only when the skill activates.

## Install

```bash
pip install requests beautifulsoup4 lxml ddgs trafilatura markdownify

# Optional extras (installed on demand). Run as two commands (Windows PowerShell 5.1 has no &&):
pip install playwright   # JS rendering / actions
playwright install chromium
pip install pypdf        # reading PDFs
pip install curl_cffi    # bypass TLS-fingerprint bot blocks

# Check your environment
python .cline/skills/web-research/scripts/doctor.py

# Try it
python .cline/skills/web-research/scripts/web_search.py "python 3.13 release date" -n 3
python .cline/skills/web-research/scripts/web_read.py "https://example.com"
```

Requires Python 3.10+ and internet access.

## Capabilities

- **Clean Markdown output** — trafilatura → markdownify → BeautifulSoup fallback chain; strips
  base64 images and ad/cookie/social/consent boilerplate to save tokens.
- **Rich metadata** — title, author, date, site name, language, keywords, og:image (from
  trafilatura plus `og:`/`article:`/meta tags).
- **JavaScript rendering** — optional Playwright engine with actions (click, scroll, wait, write,
  press) and screenshots; automatic fallback to static fetch.
- **PDF parsing** — detected automatically, extracted with pypdf.
- **Full-content search** — `web_search --fetch` returns Markdown for the top results.
- **Map & crawl** — discover a site's URLs (sitemap.xml, robots.txt sitemaps, `.gz`), or crawl a
  bounded section into Markdown; crawling respects robots.txt by default.
- **Access options** — route through a proxy (`--proxy` / `WEB_RESEARCH_PROXY`) and optional curl_cffi
  TLS impersonation (`--impersonate`) to get past corporate proxies and TLS-fingerprint bot blocks.
- **Robust fetching** — shared headers, SSL-verify fallback, retry with backoff. UTF-8 output so
  non-ASCII content prints correctly on Windows.

## Dependencies

| Group | Packages | Purpose |
|---|---|---|
| core (required) | `requests`, `beautifulsoup4`, `lxml` | HTTP + HTML parsing |
| search | `ddgs` | primary search backend (HTML fallback if absent) |
| extract | `trafilatura`, `markdownify` | clean Markdown + metadata |
| render (optional) | `playwright` | JS pages, actions, screenshots |
| pdf (optional) | `pypdf` | read PDFs |
| impersonate (optional) | `curl_cffi` | bypass TLS-fingerprint bot blocks |
| impersonate (optional) | `curl_cffi` | bypass TLS-fingerprint bot blocks |

The scripts check dependencies and fall back gracefully; `SKILL.md` has the agent ask before
installing anything.

## Sharing with your team

Copy the `.cline/skills/web-research/` directory and the `.clinerules` file into any workspace, or
copy `web-research/` to `~/.cline/skills/` (global) so it applies to all projects.
