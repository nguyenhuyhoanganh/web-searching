# Script Capabilities — web_search.py & web_read.py

Complete reference for every flag and feature of both scripts. Use this when you need to
pick the right options for a search or page-read task.

---

## web_search.py

Search the web via DuckDuckGo (primary), with automatic fallback to DuckDuckGo HTML scraping
and Google HTML scraping when the API is rate-limited. No API key required.

### Usage

```
python3 .cline/skills/web-research/scripts/web_search.py "<query>" [options]
```

### Positional argument

| Argument | Description |
|----------|-------------|
| `query`  | The search query string. Supports DuckDuckGo search operators (`"exact phrase"`, `site:domain`). |

### Flags

| Flag | Short | Default | Description |
|------|-------|---------|-------------|
| `--max-results N` | `-n N` | `5` | Number of results to return. Increase for broad surveys (e.g. `-n 10`), keep low for targeted lookups. |
| `--region CODE` | `-r CODE` | `wt-wt` | Region/language code for localized results. Examples: `vn-vi` (Vietnam/Vietnamese), `us-en` (US/English), `jp-jp` (Japan/Japanese), `de-de` (Germany/German). `wt-wt` = worldwide, no region bias. |
| `--news` | — | off | Search news articles instead of general web. Returns results with `date` and `source` fields. Useful for recent events, announcements, releases. |
| `--answers` | — | off | Get instant answers (e.g. definitions, quick facts). Returns fewer but more direct results. Ignores `--max-results` and `--region`. |
| `--json` | — | off | Output results as JSON instead of human-readable text. Useful when you need to parse results programmatically. |

### Output fields

**Text search** (`--max-results`, default mode):

| Field | Description |
|-------|-------------|
| `title` | Page title |
| `url` | Page URL |
| `snippet` | Short excerpt from the page |

**News search** (`--news`):

| Field | Description |
|-------|-------------|
| `title` | Article headline |
| `url` | Article URL |
| `snippet` | Article excerpt |
| `date` | Publication date |
| `source` | News source name |

**Instant answers** (`--answers`):

| Field | Description |
|-------|-------------|
| `text` | The answer text |
| `url` | Source URL |
| `source` | Source name |

### Fallback chain

1. **DDGS API** (via `ddgs` package) — fastest, most reliable.
2. **DuckDuckGo HTML scrape** — if DDGS API fails or `ddgs` is not installed.
3. **Google HTML scrape** — last resort if DuckDuckGo is also blocked.

If all three fail, the script exits with an error listing each failure.

### SSL handling

On first `SSLError` (common behind corporate proxies), the script automatically retries
with SSL verification disabled for the rest of the session. A warning is logged to stderr.

### Examples

```bash
# Basic search
python3 .cline/skills/web-research/scripts/web_search.py "Python 3.13 new features"

# More results
python3 .cline/skills/web-research/scripts/web_search.py "React server components" -n 10

# Region-specific
python3 .cline/skills/web-research/scripts/web_search.py "thời tiết Hà Nội" --region vn-vi

# News
python3 .cline/skills/web-research/scripts/web_search.py "OpenAI latest announcement" --news

# Instant answer
python3 .cline/skills/web-research/scripts/web_search.py "Python list comprehension" --answers

# JSON output
python3 .cline/skills/web-research/scripts/web_search.py "Spring Boot 3.4" --json

# Combine flags
python3 .cline/skills/web-research/scripts/web_search.py "Vietnam AI startup" --news --region vn-vi -n 10
```

---

## web_read.py

Fetch a URL and extract the main readable content. Uses trafilatura for smart extraction
with BeautifulSoup as fallback. No API key required.

### Usage

```
python3 .cline/skills/web-research/scripts/web_read.py "<url>" [options]
```

### Positional argument

| Argument | Description |
|----------|-------------|
| `url`    | The full URL to fetch and read (must include `https://` or `http://`). |

### Flags

| Flag | Short | Default | Description |
|------|-------|---------|-------------|
| `--selector SELECTOR` | `-s SELECTOR` | none | CSS selector to extract specific elements only. Examples: `"article"`, `"div.content"`, `"#main-text"`, `"table.comparison"`. When set, only matching elements are returned. |
| `--max-length N` | `-m N` | `50000` | Maximum character length of extracted content. Content beyond this limit is truncated with a `[content truncated]` marker. Lower it for large pages to save context (e.g. `-m 5000`). |
| `--raw` | — | off | Skip trafilatura and use BeautifulSoup only. Useful when trafilatura misidentifies the main content, or when you want a more literal extraction. |
| `--links` | — | off | Extract all links from the page instead of content. Returns a list of `{text, url}` pairs. Useful for discovering sub-pages, documentation sections, or download links. |
| `--json` | — | off | Output as JSON instead of human-readable text. |

### Output fields (content mode, default)

| Field | Description |
|-------|-------------|
| `title` | Page title (from `<title>` tag or metadata) |
| `author` | Author name (trafilatura only, extracted from metadata) |
| `date` | Publication date (trafilatura only, extracted from metadata) |
| `url` | The fetched URL |
| `method` | Extraction method used: `trafilatura` or `beautifulsoup` |
| `content` | The extracted main text |
| `truncated` | `true` if content was cut at `--max-length` |

### Output fields (links mode, `--links`)

| Field | Description |
|-------|-------------|
| `text` | Link anchor text |
| `url` | Link target URL (relative paths resolved to absolute) |

### Content extraction priority

Without `--selector` or `--raw`:

1. **trafilatura** — smart extraction that identifies the main article content, strips boilerplate (nav, ads, footer). Also extracts metadata (author, date).
2. **BeautifulSoup fallback** — if trafilatura is not installed or returns empty. Looks for content in this order: `<article>` → `<main>` → `[role="main"]` → `div` matching class `content|article|post|entry` → `<body>`.

With `--selector`: always uses BeautifulSoup with the given CSS selector.
With `--raw`: always uses BeautifulSoup (skips trafilatura).

### Retry & SSL handling

- **Connection errors / timeouts**: retried up to 3 times with exponential backoff (2s, 4s).
- **SSL errors**: on first `SSLError`, retries with SSL verification disabled. Does not consume a retry attempt.
- **HTTP errors** (4xx, 5xx): raised immediately, no retry.

### Limitations

- **JavaScript-rendered pages**: the script fetches static HTML only. Pages that require JavaScript to render content (SPAs, client-side rendering) may return incomplete or empty content.
- **Login-protected pages**: cannot access content behind authentication.
- **Rate limiting**: some sites may block or rate-limit requests. The User-Agent header mimics a browser to reduce this.

### Examples

```bash
# Read a page (auto-extract main content)
python3 .cline/skills/web-research/scripts/web_read.py "https://docs.python.org/3/whatsnew/3.13.html"

# Limit content length (useful for large pages)
python3 .cline/skills/web-research/scripts/web_read.py "https://en.wikipedia.org/wiki/Python_(programming_language)" -m 5000

# Extract specific section via CSS selector
python3 .cline/skills/web-research/scripts/web_read.py "https://spring.io/blog" --selector "article"

# Use BeautifulSoup only (skip trafilatura)
python3 .cline/skills/web-research/scripts/web_read.py "https://example.com" --raw

# List all links on a page
python3 .cline/skills/web-research/scripts/web_read.py "https://github.com/user/repo" --links

# JSON output
python3 .cline/skills/web-research/scripts/web_read.py "https://example.com" --json

# Combine: extract links as JSON
python3 .cline/skills/web-research/scripts/web_read.py "https://docs.python.org/3/" --links --json

# Specific selector + limited length
python3 .cline/skills/web-research/scripts/web_read.py "https://news.ycombinator.com" --selector "tr.athing" -m 3000
```
