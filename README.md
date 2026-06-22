# Web Skills for Cline

Bộ skills tìm kiếm web và đọc nội dung trang web cho Cline extension. Dành cho bản Cline fork không có sẵn web tools.

## Features

| Tool | Mô tả |
|------|--------|
| `web_search` | Tìm kiếm web qua DuckDuckGo (không cần API key). Hỗ trợ web, news, instant answers |
| `web_read` | Đọc và trích xuất nội dung chính từ URL. Hỗ trợ CSS selector, extract links |
| `search_and_read` | Kết hợp search + read: tìm kiếm và tự động đọc top kết quả |

## Quick Start

### Cách 1: MCP Server (Khuyến nghị)

MCP server cho phép Cline sử dụng web skills như native tools.

```bash
# 1. Setup
bash setup_mcp.sh

# 2. Thêm vào Cline MCP settings (Ctrl+Shift+P → "Cline: MCP Settings")
```

Cấu hình MCP settings:

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

### Cách 2: CLI Scripts (Fallback)

Nếu Cline fork không hỗ trợ MCP, Cline vẫn có thể chạy các scripts qua terminal.

```bash
# 1. Setup
bash skills/setup.sh

# 2. Sử dụng
source .venv/bin/activate
python skills/web_search.py "python asyncio tutorial"
python skills/web_read.py "https://docs.python.org/3/library/asyncio.html"
```

## CLI Usage

### web_search.py

```bash
# Tìm kiếm cơ bản
python skills/web_search.py "Spring Boot 3 migration guide"

# Nhiều kết quả hơn
python skills/web_search.py "React hooks best practices" --max-results 10

# Tìm kiếm tin tức
python skills/web_search.py "Java 21 release" --news

# Tìm kiếm vùng Việt Nam
python skills/web_search.py "lập trình Python" --region vn-vi

# Instant answers
python skills/web_search.py "Python datetime format" --answers

# Output JSON
python skills/web_search.py "query" --json
```

### web_read.py

```bash
# Đọc nội dung trang web
python skills/web_read.py "https://spring.io/blog/2024/11/21/spring-boot-3-4-0-available-now"

# Giới hạn độ dài nội dung
python skills/web_read.py "https://docs.python.org/3/tutorial/" --max-length 5000

# Trích xuất phần cụ thể bằng CSS selector
python skills/web_read.py "https://example.com" --selector "article.post-content"

# Lấy danh sách links
python skills/web_read.py "https://example.com" --links

# Chỉ dùng BeautifulSoup (bỏ qua trafilatura)
python skills/web_read.py "https://example.com" --raw

# Output JSON
python skills/web_read.py "https://example.com" --json
```

## MCP Tools Reference

Khi dùng qua MCP server, Cline có thể gọi trực tiếp:

### `web_search`

| Parameter | Type | Default | Mô tả |
|-----------|------|---------|--------|
| `query` | string | (required) | Từ khóa tìm kiếm |
| `max_results` | int | 5 | Số kết quả (max 20) |
| `region` | string | "wt-wt" | Vùng tìm kiếm |
| `search_type` | string | "web" | "web", "news", hoặc "answers" |

### `web_read`

| Parameter | Type | Default | Mô tả |
|-----------|------|---------|--------|
| `url` | string | (required) | URL trang web |
| `max_length` | int | 50000 | Độ dài nội dung tối đa |
| `selector` | string | null | CSS selector |
| `extract_links` | bool | false | Chỉ lấy links |

### `search_and_read`

| Parameter | Type | Default | Mô tả |
|-----------|------|---------|--------|
| `query` | string | (required) | Từ khóa tìm kiếm |
| `max_results` | int | 3 | Số trang đọc (max 5) |
| `max_content_length` | int | 10000 | Độ dài mỗi trang |
| `region` | string | "wt-wt" | Vùng tìm kiếm |

## Cách hoạt động với Cline

File `.clinerules` đã được cấu hình để hướng dẫn Cline:

- **Tự động tìm kiếm** khi user cung cấp thông tin cần verify
- **Tự động đọc** khi user cung cấp URL
- **Suy luận query** thông minh dựa trên ngữ cảnh cuộc trò chuyện
- **Trích dẫn nguồn** khi trả lời từ kết quả web

## Requirements

- Python 3.10+
- Không cần API key (sử dụng DuckDuckGo)
- Cần kết nối internet

## Dependencies

- `duckduckgo-search` - Tìm kiếm DuckDuckGo
- `requests` - HTTP client
- `beautifulsoup4` - HTML parsing
- `trafilatura` - Trích xuất nội dung thông minh
- `mcp[cli]` - MCP SDK (chỉ cho MCP server)
