---
name: web-research
description: Searches the web and reads web pages to find and fact-check current information. Use whenever the user shares content to verify, asks about latest versions/releases/news/prices, provides a URL to read or summarize, hits an error message to look up, or mentions a library, framework, or term that should be checked against up-to-date sources instead of answered from memory.
---

# Web Research

Tìm kiếm web và đọc nội dung trang để lấy/kiểm chứng thông tin, qua 2 script trong `scripts/`.
Gọi chúng bằng terminal (`execute_command`) — không cần MCP, không cần API key.

**Nguyên tắc cốt lõi: không search bừa.** Mỗi lần search phải trả lời được một câu hỏi cụ thể.
Nếu không nói được "đang đi tìm chính xác điều gì" thì đừng search.

## Khi nào dùng — khi nào không

Dùng khi: thông tin thay đổi theo thời gian (phiên bản mới nhất, release, giá, tin tức); dữ kiện/
con số/API cụ thể bạn không chắc 100%; user đưa nội dung cần kiểm chứng; user đưa URL cần đọc; lỗi/
thông báo lỗi cần tra; công nghệ/thuật ngữ bạn nhớ mơ hồ.

KHÔNG dùng (trả lời thẳng) khi: kiến thức ổn định bạn đã chắc; câu trả lời đã nằm trong codebase/
ngữ cảnh (đọc file thay vì search); yêu cầu thuần suy luận/tính toán.

## Quy trình (theo thứ tự)

1. **Bóc tách yêu cầu**: liệt kê các mệnh đề cần kiểm chứng, thực thể, phiên bản, mốc thời gian.
2. **Quyết định có cần search không.** Không cần → trả lời luôn.
3. **Thiết kế truy vấn** — một truy vấn một mục tiêu (chi tiết: `reference/search-strategy.md`).
4. **Chạy `web_search`**, đọc kết quả: ưu tiên nguồn chính thống, để ý *ngày* và *domain*.
5. **`web_read` nguồn đáng tin nhất** để xác nhận — không kết luận chỉ từ đoạn trích.
6. **Đối chiếu ≥ 2 nguồn** khi thông tin quan trọng hoặc các nguồn mâu thuẫn.
7. **Tinh chỉnh & lặp** nếu kết quả kém (đổi từ khóa/qualifier/nguồn, tối đa ~3 vòng).
8. **Kết luận + trích nguồn (URL)**, kèm phán quyết: **ĐÚNG / SAI / CẦN CẬP NHẬT / KHÔNG ĐỦ BẰNG CHỨNG**.

Khi user dán nội dung để verify hoặc cần thiết kế truy vấn tốt, đọc `reference/search-strategy.md`
(có bảng ví dụ Tốt/Tệ, toán tử tìm kiếm, quy trình kiểm chứng từng tuyên bố, và lưu ý bảo mật).

## Chạy script

Chạy từ thư mục skill này. Ưu tiên `python` trong `.venv` nếu đã `bash setup.sh`; nếu không, dùng `python3`.

```bash
# Tìm kiếm
python3 scripts/web_search.py "Spring Boot latest version Java 21 support" -n 5
python3 scripts/web_search.py "<query>" --news          # tin tức
python3 scripts/web_search.py "<query>" --region vn-vi  # nội dung Việt Nam
python3 scripts/web_search.py "<query>" --json          # JSON để tự parse

# Đọc trang
python3 scripts/web_read.py "https://..."               # trích nội dung chính
python3 scripts/web_read.py "<url>" --selector "article" # lấy đúng phần theo CSS
python3 scripts/web_read.py "<url>" --max-length 5000
python3 scripts/web_read.py "<url>" --links             # liệt kê link trên trang
```

`web_search`: `-n/--max-results` (mặc định 5), `-r/--region`, `--news`, `--answers`, `--json`.
`web_read`: `-s/--selector`, `-m/--max-length` (mặc định 50000), `--raw`, `--links`, `--json`.

Lưu ý: `web_read` chỉ đọc HTML tĩnh — trang render bằng JavaScript có thể thiếu nội dung.

## Bảo mật truy vấn

Truy vấn được gửi tới công cụ tìm kiếm bên ngoài. **Không bao giờ** đưa bí mật, token, tên khách
hàng, hostname nội bộ, hay đoạn code độc quyền vào query — chỉ tìm bằng thuật ngữ công khai, chung.

## Trình bày kết quả

Trích nguồn (URL) cho mỗi dữ kiện lấy từ web; nêu *ngày* khi thông tin nhạy cảm về thời gian; đi
thẳng kết luận trước, chi tiết sau. Không bịa — không tìm thấy thì nói rõ "không đủ bằng chứng".
