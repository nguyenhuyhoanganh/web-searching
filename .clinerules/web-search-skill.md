# SKILL: Web Search & Web Read (no MCP)

Bạn (Cline) có 2 script chạy qua terminal để **tìm kiếm web** và **đọc nội dung trang web**.
Đây KHÔNG phải MCP — bạn gọi chúng bằng tool `execute_command` có sẵn của Cline.

Mục tiêu của skill này: khi cần thông tin ngoài kiến thức/đã cũ/cần kiểm chứng, bạn **tự suy ra
truy vấn đúng**, tìm, đọc nguồn thật, đối chiếu, rồi trả lời kèm trích dẫn. **Tuyệt đối không
search bừa.**

---

## 1. KHI NÀO search — KHI NÀO KHÔNG

### Phải search khi:
- Thông tin thay đổi theo thời gian: phiên bản mới nhất, release date, giá, tin tức, "hiện tại".
- Sự kiện / con số / API / cú pháp cụ thể mà bạn **không chắc chắn 100%**.
- User dán nội dung và (ngầm hoặc rõ) muốn **kiểm chứng** tính đúng/sai.
- User đưa URL và muốn bạn đọc/nắm nội dung.
- Lỗi/bug cụ thể, thông báo lỗi nguyên văn cần tìm cách xử lý.
- Công nghệ/thư viện/thuật ngữ bạn chưa từng biết hoặc nhớ mơ hồ.

### KHÔNG search (trả lời thẳng) khi:
- Kiến thức ổn định, phổ thông mà bạn chắc chắn (cú pháp cơ bản, khái niệm chung).
- Câu trả lời đã nằm trong **codebase / file / ngữ cảnh** hiện có → đọc file thay vì search.
- Yêu cầu thuần suy luận/tính toán, không phụ thuộc dữ kiện ngoài.

> Nguyên tắc vàng: **mỗi lần search phải có một câu hỏi cụ thể cần trả lời.** Nếu bạn không nói
> được "mình đang đi tìm chính xác điều gì", thì đừng search.

---

## 2. QUY TRÌNH BẮT BUỘC (theo đúng thứ tự)

1. **Bóc tách request.** Liệt kê trong đầu: các *mệnh đề cần kiểm chứng* (claims), *thực thể*
   (tên lib/sản phẩm/người), *phiên bản*, *mốc thời gian*, *ràng buộc* (ngôn ngữ, OS, framework).
2. **Quyết định có cần search không** (theo mục 1). Không cần → trả lời luôn.
3. **Thiết kế truy vấn** cho từng điều cần biết (xem mục 4). Một truy vấn = một mục tiêu.
4. **Chạy `web_search`**, đọc danh sách kết quả: ưu tiên nguồn chính thống, để ý *ngày* và *domain*.
5. **`web_read` nguồn đáng tin nhất** để xác nhận. **Không kết luận chỉ dựa trên snippet.**
6. **Đối chiếu ≥ 2 nguồn** nếu thông tin quan trọng hoặc các nguồn mâu thuẫn.
7. **Tinh chỉnh & lặp** nếu kết quả kém: đổi từ khóa, thêm/bớt qualifier, đổi nguồn (tối đa ~3 vòng).
8. **Kết luận + trích dẫn.** Mỗi khẳng định quan trọng kèm URL. Nêu rõ phán quyết:
   **ĐÚNG / SAI / CẦN CẬP NHẬT / KHÔNG ĐỦ BẰNG CHỨNG**.

---

## 3. ƯU TIÊN NGUỒN
1. Tài liệu/website chính thức (docs, trang chủ dự án, release notes, RFC, spec).
2. Repo GitHub gốc (README, CHANGELOG, issues, releases).
3. Nguồn uy tín (MDN, Stack Overflow có upvote cao, blog của chính tác giả/tổ chức).
4. Còn lại: tham khảo, cần đối chiếu thêm.

Cảnh giác: nội dung SEO rác, bài AI-generated, tài liệu cũ. Luôn nhìn **ngày xuất bản**.

---

## 4. THIẾT KẾ TRUY VẤN — search THÔNG MINH

Cách biến một request lộn xộn thành query chính xác:

- **Bóc từ khóa cốt lõi**, bỏ từ thừa ("làm thế nào", "cho tôi", "bạn nghĩ").
- **Trích thực thể + phiên bản chính xác**: `<tên> <phiên bản> <thuật ngữ official>`.
- **Chủ đề kỹ thuật → dùng tiếng Anh** (tài liệu gốc hầu hết tiếng Anh).
- **Thêm qualifier theo ý định**: `latest`, `2026`, `release notes`, `changelog`,
  `documentation`, `vs`, `deprecated`, `migration guide`.
- **Toán tử tìm kiếm** (script hỗ trợ truyền nguyên văn):
  - `"cụm chính xác"` — giữ nguyên cụm/tên/thông báo lỗi.
  - `site:domain` — giới hạn nguồn, vd `site:docs.python.org`, `site:github.com`.
  - Thông báo lỗi để **nguyên văn trong ngoặc kép**, bỏ phần biến động (đường dẫn, số dòng).
- **Một truy vấn một ý.** Cần nhiều thứ → nhiều truy vấn riêng.

### Ví dụ TỐT vs TỆ

| Request của user | ❌ Query tệ | ✅ Query tốt |
|---|---|---|
| "Spring Boot mới nhất hỗ trợ Java 21 chưa?" | `spring boot java` | `Spring Boot latest version Java 21 support site:spring.io` → rồi `web_read` trang release notes |
| Lỗi `NoClassDefFoundError: javax/xml/bind/JAXBException` trên Java 11 | `java jaxb error` | `"NoClassDefFoundError" "javax/xml/bind/JAXBException" Java 11 fix` |
| "React 19 bỏ forwardRef đúng không?" | `react forwardRef` | `React 19 forwardRef deprecated site:react.dev` → `web_read` trang blog/docs → phán quyết ĐÚNG/SAI |
| "Thư viện X bản nào ổn định nhất bây giờ?" | `X library` | `<X> latest stable release` + `site:github.com <X> releases` → đọc trang Releases |
| "So sánh Postgres với MySQL cho phân tích" | `postgres mysql` | `PostgreSQL vs MySQL analytical workload OLAP comparison` → đọc 2 nguồn, đối chiếu |

---

## 5. KHI USER DÁN NỘI DUNG ĐỂ "VERIFY"

1. **Tách thành từng tuyên bố factual** (mỗi câu khẳng định một dữ kiện riêng).
2. Với mỗi tuyên bố → 1 truy vấn riêng → `web_search` → `web_read` nguồn gốc.
3. Gắn nhãn từng tuyên bố: **ĐÚNG / SAI / CẦN CẬP NHẬT / KHÔNG ĐỦ BẰNG CHỨNG** + URL nguồn.
4. Nếu SAI → nêu thông tin đúng kèm nguồn. Nếu nguồn mâu thuẫn → trình bày cả hai phía.
5. **Không bịa.** Không tìm được thì nói rõ "không tìm thấy bằng chứng", đừng đoán.

---

## 6. CÁCH CHẠY SCRIPT (qua execute_command)

Ưu tiên dùng Python trong venv của skill nếu có (`<SKILL_DIR>/.venv/bin/python`),
nếu không thì dùng `python3`. `<SKILL_DIR>` là thư mục chứa skill này (nơi có folder `skills/`).

### Tìm kiếm
```bash
python3 skills/web_search.py "Spring Boot latest version Java 21 support" -n 5
python3 skills/web_search.py "Java 21 LTS release" --news        # tin tức
python3 skills/web_search.py "lập trình bất đồng bộ" --region vn-vi
python3 skills/web_search.py "<query>" --json                    # output JSON để bạn tự parse
```
Tham số: `-n/--max-results` (mặc định 5), `-r/--region` (vd `vn-vi`, `us-en`, `wt-wt`),
`--news`, `--answers`, `--json`.

### Đọc trang web
```bash
python3 skills/web_read.py "https://spring.io/blog/..."          # trích nội dung chính
python3 skills/web_read.py "<url>" --max-length 5000             # giới hạn độ dài
python3 skills/web_read.py "<url>" --selector "article.content"  # lấy đúng phần theo CSS
python3 skills/web_read.py "<url>" --links                       # liệt kê links trên trang
python3 skills/web_read.py "<url>" --json
```
Tham số: `-s/--selector`, `-m/--max-length` (mặc định 50000), `--raw` (chỉ BeautifulSoup),
`--links`, `--json`.

> Lần đầu dùng trong một máy/dự án: chạy `bash skills/setup.sh` để tạo `.venv` và cài thư viện.
> Sau đó thay `python3` bằng `<SKILL_DIR>/.venv/bin/python` cho chắc chắn có đủ dependency.

---

## 7. QUY TẮC TRÌNH BÀY KẾT QUẢ
- Luôn **trích nguồn (URL)** cho mỗi dữ kiện lấy từ web.
- Nói rõ **mức độ chắc chắn** và **ngày** của thông tin khi nó nhạy cảm về thời gian.
- Ngắn gọn, đi thẳng kết luận trước, chi tiết/nguồn sau.
- Nếu đã search mà không đủ bằng chứng → nói thẳng, đề xuất truy vấn/nguồn tiếp theo.
