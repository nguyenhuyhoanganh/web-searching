# Web Search & Read Skill cho Cline (KHÔNG cần MCP)

Skill giúp Cline **tìm kiếm web** và **đọc nội dung trang web** ngay cả khi bản Cline fork của
công ty **không có web tools và chặn MCP**. Cline gọi 2 script Python qua terminal
(`execute_command` — tool có sẵn, không bị chặn), còn bộ rule dạy Cline **search đúng, không bừa**.

> Có MCP dùng được? Xem nhánh `claude/cline-search-web-skills-yc36cf` (bản MCP server).
> Nhánh này (`claude/cline-web-skill-no-mcp`) là bản **skill thuần, không liên quan MCP** — để share là chạy.

## Skill gồm gì

```
.clinerules/
  web-search-skill.md     # "Bộ não": khi nào search, suy ra query thế nào, đọc & đối chiếu, trích nguồn
skills/
  web_search.py           # Tìm kiếm (DuckDuckGo, fallback Google HTML) — không cần API key
  web_read.py             # Đọc & trích nội dung chính (trafilatura + BeautifulSoup)
  requirements.txt
  setup.sh
```

`web_search` và `web_read` là 2 "tool" bạn lấy lại; `.clinerules/web-search-skill.md` là phần
quan trọng nhất — nó dạy Cline **bóc tách yêu cầu → suy ra cần kiểm chứng gì → đặt truy vấn chính
xác → đọc nguồn thật → đối chiếu → trả lời kèm trích dẫn**.

## Cài đặt

```bash
# 1. Cài thư viện (tạo .venv tại gốc dự án)
bash skills/setup.sh

# 2. Test
.venv/bin/python skills/web_search.py "python 3.13 release date" -n 3
.venv/bin/python skills/web_read.py "https://example.com"
```

Yêu cầu: Python 3.10+, có internet, **không cần API key**.

## Cách share cho đồng nghiệp / sang dự án khác

Skill này tự kích hoạt khi `.clinerules/` nằm ở **gốc workspace** mà Cline đang mở. Có 2 cách:

**A. Theo từng dự án (khuyến nghị):** copy 2 thư mục `.clinerules/` và `skills/` vào gốc dự án,
chạy `bash skills/setup.sh` một lần. Cline sẽ tự đọc rule.

**B. Toàn cục (mọi dự án):** đưa nội dung `.clinerules/web-search-skill.md` vào **Global Rules**
của Cline (Cline → Settings → Rules), và đặt `skills/` ở một nơi cố định (vd `~/cline-web-skill/skills/`).
Sửa đường dẫn script trong rule cho khớp.

## Dùng thế nào (sau khi cài)

Bạn không cần gọi tay. Cứ chat bình thường, Cline sẽ **tự** dùng skill theo rule:

- *"Phiên bản ổn định mới nhất của thư viện X là gì?"* → Cline search trang Releases, đọc, trả lời kèm link.
- *"Kiểm chứng giúp đoạn này: React 19 đã bỏ forwardRef…"* → Cline tách từng tuyên bố, search docs chính thức, gắn nhãn ĐÚNG/SAI + URL.
- *"Đọc trang này tóm tắt cho mình: <URL>"* → Cline `web_read` rồi tóm tắt.

Muốn ép tay, có thể bảo: *"search '<từ khóa>' rồi đọc kết quả đầu"*.

## Tự chạy script (tham khảo)

```bash
# Tìm kiếm
python3 skills/web_search.py "<query>" -n 5
python3 skills/web_search.py "<query>" --news                 # tin tức
python3 skills/web_search.py "<query>" --region vn-vi         # vùng Việt Nam
python3 skills/web_search.py "<query>" --json                 # JSON

# Đọc trang
python3 skills/web_read.py "<url>"
python3 skills/web_read.py "<url>" --selector "article"       # đúng phần theo CSS
python3 skills/web_read.py "<url>" --max-length 5000
python3 skills/web_read.py "<url>" --links                    # liệt kê links
```

## Cơ chế "search không bừa"

Rule ép Cline theo quy trình: bóc tách request → quyết định *có thực sự cần search không* → mỗi
truy vấn một mục tiêu, dùng thuật ngữ chính xác + toán tử (`"..."`, `site:`) → đọc **nguồn gốc**
chứ không tin snippet → đối chiếu ≥2 nguồn khi quan trọng → kết luận kèm phán quyết
**ĐÚNG/SAI/CẦN CẬP NHẬT** và URL. Chi tiết + ví dụ Tốt/Tệ nằm trong `.clinerules/web-search-skill.md`.

## Dependencies
`ddgs`, `requests`, `beautifulsoup4`, `trafilatura`, `lxml`. Không cần `mcp`.
