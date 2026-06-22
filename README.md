# web-research — Agent Skill tìm kiếm & đọc web (KHÔNG cần MCP)

Skill giúp Claude/Cline **tìm kiếm web** và **đọc nội dung trang web** mà không cần MCP — phù hợp
khi bản Cline fork của công ty chặn MCP và không có sẵn web tools. Agent gọi 2 script Python qua
terminal (`execute_command`), còn `SKILL.md` dạy agent **search đúng, không bừa**.

Skill này tuân theo chuẩn **Agent Skills** của Anthropic (thư mục có `SKILL.md` + frontmatter +
progressive disclosure). Có MCP dùng được? Xem nhánh `claude/cline-search-web-skills-yc36cf` (bản MCP server).

## Cấu trúc (chuẩn Agent Skill)

```
web-research/                 # đơn vị shareable — copy nguyên thư mục này là dùng được
├── SKILL.md                  # frontmatter (name, description) + hướng dẫn chính, súc tích
├── reference/
│   └── search-strategy.md    # chi tiết: thiết kế truy vấn, ví dụ Tốt/Tệ, kiểm chứng, bảo mật
├── scripts/
│   ├── web_search.py         # tìm kiếm (DuckDuckGo, fallback Google) — không cần API key
│   └── web_read.py           # đọc & trích nội dung chính (trafilatura + BeautifulSoup)
├── requirements.txt
└── setup.sh
.clinerules                   # pointer để Cline tự đọc SKILL.md khi cần
```

Cơ chế progressive disclosure: chỉ `name` + `description` được nạp sẵn; `SKILL.md` chỉ đọc khi
skill được kích hoạt; `reference/search-strategy.md` chỉ đọc khi cần — tiết kiệm context.

## Cài đặt

```bash
cd web-research
bash setup.sh        # tạo .venv và cài thư viện (chỉ chạy 1 lần)

# Test
.venv/bin/python scripts/web_search.py "python 3.13 release date" -n 3
.venv/bin/python scripts/web_read.py "https://example.com"
```

Yêu cầu: Python 3.10+, có internet, **không cần API key**.

## Cách dùng theo từng môi trường

**Cline:** copy thư mục `web-research/` và file `.clinerules` vào gốc workspace, chạy
`bash web-research/setup.sh`. Cline đọc `.clinerules` → tự mở `SKILL.md` khi cần search/đọc/verify.
Hoặc dán nội dung `.clinerules` vào **Global Rules** (Cline → Settings → Rules) để áp cho mọi dự án.

**Claude Code:** copy thư mục `web-research/` vào `.claude/skills/` (theo dự án) hoặc
`~/.claude/skills/` (cá nhân). Claude Code tự phát hiện skill qua frontmatter.

**Claude API / claude.ai:** upload skill theo hướng dẫn Agent Skills của Anthropic.

## Dùng thế nào (sau khi cài)

Không cần gọi tay — chat bình thường, agent tự dùng theo `SKILL.md`:

- *"Phiên bản ổn định mới nhất của thư viện X?"* → search trang Releases, đọc, trả lời kèm link.
- *"Kiểm chứng giúp: React 19 đã bỏ forwardRef…"* → tách từng tuyên bố, search docs chính thức,
  gắn nhãn ĐÚNG/SAI + URL.
- *"Đọc & tóm tắt trang này: <URL>"* → `web_read` rồi tóm tắt.

## Chạy script trực tiếp (tham khảo)

```bash
cd web-research
python3 scripts/web_search.py "<query>" -n 5
python3 scripts/web_search.py "<query>" --news            # tin tức
python3 scripts/web_search.py "<query>" --region vn-vi    # vùng Việt Nam
python3 scripts/web_read.py "<url>"
python3 scripts/web_read.py "<url>" --selector "article"  # đúng phần theo CSS
python3 scripts/web_read.py "<url>" --links               # liệt kê link
```

## Cơ chế "search không bừa"

`SKILL.md` ép agent theo quy trình: bóc tách yêu cầu → quyết định *có thực sự cần search không* →
mỗi truy vấn một mục tiêu, dùng thuật ngữ chính xác + toán tử (`"..."`, `site:`) → đọc **nguồn gốc**
chứ không tin đoạn trích → đối chiếu ≥2 nguồn khi quan trọng → kết luận kèm URL và phán quyết
**ĐÚNG/SAI/CẦN CẬP NHẬT**. Chi tiết + ví dụ Tốt/Tệ + lưu ý bảo mật truy vấn: `reference/search-strategy.md`.

## Dependencies
`ddgs`, `requests`, `beautifulsoup4`, `trafilatura`, `lxml`. Không cần `mcp`.
