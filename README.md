# web-research — web search & read skill for Cline (no MCP)

A skill that lets Cline **search the web** and **read web pages** without MCP — useful when a
forked Cline build blocks MCP and ships no web tools. The agent calls two Python scripts through the
terminal (`execute_command`), and `SKILL.md` teaches the agent to **search precisely, not blindly**.

Can you use MCP? See branch `claude/cline-search-web-skills-yc36cf` (the MCP server variant).

## Structure

```
.cline/skills/web-research/         # Cline auto-discovers skills in .cline/skills/
├── SKILL.md                        # frontmatter (name, description) + main instructions
├── reference/
│   └── search-strategy.md          # detail: query design, good/bad examples, verification, privacy
├── scripts/
│   ├── web_search.py               # search (DuckDuckGo, Google fallback) — no API key
│   └── web_read.py                 # extract main content (trafilatura + BeautifulSoup)
└── requirements.txt
.clinerules                         # pointer so Cline reads SKILL.md when needed
```

Cline loads skills from `.cline/skills/` automatically — the skill name and description are
preloaded at startup; the full `SKILL.md` is read only when the skill activates; and
`reference/search-strategy.md` is read only when needed — keeping context lean.

## Install

```bash
pip install requests beautifulsoup4 ddgs trafilatura lxml

# Test
python3 .cline/skills/web-research/scripts/web_search.py "python 3.13 release date" -n 3
python3 .cline/skills/web-research/scripts/web_read.py "https://example.com"
```

Requires Python 3.10+, internet access, **no API key**.

No `setup.sh` needed — `SKILL.md` instructs the agent to check and install deps automatically on
first use.

## Sharing with your team

Copy the `.cline/skills/web-research/` directory and the `.clinerules` file into any workspace.
Cline will auto-detect the skill and install dependencies on first use.

Alternatively, copy `web-research/` to `~/.cline/skills/` (global) so it applies to all projects.

## Robustness

- **Dependency checking**: scripts detect missing packages on startup and print install instructions
- **Retry logic**: `web_read` retries connection errors up to 3 times with exponential backoff (2s, 4s)
- **Logging**: all scripts log to stderr with timestamps for debugging
- **Search fallback chain**: DDGS API → DuckDuckGo HTML scrape → Google HTML scrape
- **Python alias detection**: SKILL.md guides Cline to detect `python3` / `python` / `py` automatically
- **Dynamic path resolution**: SKILL.md teaches Cline to find scripts relative to the skill directory

## How it behaves (after install)

No manual calls needed — chat normally and the agent uses it per `SKILL.md`:

- *"What's the latest stable version of library X?"* → search the Releases page, read it, answer with a link.
- *"Verify this: React 19 removed forwardRef…"* → split into claims, search official docs, label TRUE/FALSE + URL.
- *"Read & summarize this page: <URL>"* → `web_read` then summarize.

## Running the scripts directly (reference)

```bash
SKILL_DIR=".cline/skills/web-research"
python3 "$SKILL_DIR/scripts/web_search.py" "<query>" -n 5
python3 "$SKILL_DIR/scripts/web_search.py" "<query>" --news            # news
python3 "$SKILL_DIR/scripts/web_search.py" "<query>" --region vn-vi    # Vietnam region
python3 "$SKILL_DIR/scripts/web_read.py" "<url>"
python3 "$SKILL_DIR/scripts/web_read.py" "<url>" --selector "article"  # specific part via CSS
python3 "$SKILL_DIR/scripts/web_read.py" "<url>" --links               # list links
```

## The "don't search blindly" mechanism

`SKILL.md` enforces a workflow: decompose the request → decide *whether a search is even needed* →
one goal per query with precise terms + operators (`"..."`, `site:`) → read the **original source**,
not the snippet → cross-check 2+ sources when it matters → conclude with the URL and a
**TRUE/FALSE/OUTDATED** verdict. Details + good/bad examples + query-privacy notes: `reference/search-strategy.md`.

## Dependencies

- `requests` — HTTP client (required)
- `beautifulsoup4` — HTML parsing (required)
- `ddgs` — DuckDuckGo search (optional — falls back to HTML scraping)
- `trafilatura` — smart content extraction (optional — falls back to BeautifulSoup)
- `lxml` — fast HTML parser for trafilatura
