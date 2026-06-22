# Web Skills for Cline (MCP server)

Web search and web-page reading tools for the Cline extension — for forked Cline builds that ship no
web tools. This branch provides an **MCP server**; the agent calls the tools natively. A blocked-MCP,
skill-only variant lives on branch `claude/cline-web-skill-no-mcp`.

## Features

| Tool | Description |
|------|-------------|
| `web_search` | Web search via DuckDuckGo (no API key). Supports web, news, instant answers |
| `web_read` | Fetch a URL and extract the main content. Supports CSS selector and link extraction |
| `search_and_read` | Combine search + read: search and auto-read the top results |

## Quick Start

### Option 1: MCP server (recommended)

The MCP server lets Cline use the web skills as native tools.

```bash
# 1. Setup
bash setup_mcp.sh

# 2. Add to Cline MCP settings (Ctrl+Shift+P -> "Cline: MCP Settings")
```

MCP settings:

```json
{
    "mcpServers": {
        "web-skills": {
            "command": "/absolute/path/to/.venv/bin/python",
            "args": ["/absolute/path/to/mcp-server/server.py"],
            "disabled": false
        }
    }
}
```

### Option 2: CLI scripts (fallback)

If your Cline build does not support MCP, Cline can still run the scripts via the terminal.

```bash
# 1. Setup
bash skills/setup.sh

# 2. Use
source .venv/bin/activate
python skills/web_search.py "python asyncio tutorial"
python skills/web_read.py "https://docs.python.org/3/library/asyncio.html"
```

## CLI Usage

### web_search.py

```bash
python skills/web_search.py "Spring Boot 3 migration guide"
python skills/web_search.py "React hooks best practices" --max-results 10
python skills/web_search.py "Java 21 release" --news
python skills/web_search.py "Python programming" --region vn-vi
python skills/web_search.py "Python datetime format" --answers
python skills/web_search.py "query" --json
```

### web_read.py

```bash
python skills/web_read.py "https://spring.io/blog/..."
python skills/web_read.py "https://docs.python.org/3/tutorial/" --max-length 5000
python skills/web_read.py "https://example.com" --selector "article.post-content"
python skills/web_read.py "https://example.com" --links
python skills/web_read.py "https://example.com" --raw      # BeautifulSoup only
python skills/web_read.py "https://example.com" --json
```

## MCP Tools Reference

When used via the MCP server, Cline can call these directly:

### `web_search`

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `query` | string | (required) | Search query |
| `max_results` | int | 5 | Number of results (max 20) |
| `region` | string | "wt-wt" | Search region |
| `search_type` | string | "web" | "web", "news", or "answers" |

### `web_read`

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `url` | string | (required) | Web page URL |
| `max_length` | int | 25000 | Max content length (also the hard cap) |
| `selector` | string | null | CSS selector |
| `extract_links` | bool | false | Return links only |

### `search_and_read`

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `query` | string | (required) | Search query |
| `max_results` | int | 3 | Pages to read (max 5) |
| `max_content_length` | int | 8000 | Content length per page |
| `region` | string | "wt-wt" | Search region |

All tools are read-only and carry MCP annotations (`readOnlyHint`, `openWorldHint`). Each result is
capped at 25000 characters with guided truncation.

## How it works with Cline

`.clinerules` instructs Cline to:

- **Search automatically** when the user provides content to verify
- **Read automatically** when the user provides a URL
- **Derive the query** intelligently from the conversation context (one goal per query, precise terms)
- **Cite the source** when answering from web results, with a TRUE/FALSE/OUTDATED verdict

## Robustness

- **Dependency checking**: scripts detect missing packages on startup and print install instructions
- **Retry logic**: `web_read` and the MCP server retry connection errors up to 3 times with exponential backoff (2s, 4s)
- **Logging**: all scripts log to stderr with timestamps for debugging (`[INFO]` for normal operations, `[WARNING]` for retries, `[ERROR]` for failures)
- **Search fallback chain**: DDGS API → DuckDuckGo HTML scrape → Google HTML scrape
- **Python alias detection**: `.clinerules` guides Cline to detect `python3` / `python` / `py` automatically

## Requirements

- Python 3.10+
- No API key (uses DuckDuckGo)
- Internet access

## Dependencies

- `ddgs` — DuckDuckGo search (optional — falls back to HTML scraping)
- `requests` — HTTP client (required)
- `beautifulsoup4` — HTML parsing (required)
- `trafilatura` — smart content extraction (optional — falls back to BeautifulSoup)
- `lxml` — fast HTML parser for trafilatura
- `mcp[cli]` — MCP SDK (MCP server only)
