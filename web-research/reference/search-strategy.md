# Search Strategy — thiết kế truy vấn & kiểm chứng

Tài liệu chi tiết cho skill `web-research`. Đọc khi cần đặt truy vấn tốt hoặc kiểm chứng nội dung.

## Contents
- Thiết kế truy vấn
- Toán tử tìm kiếm
- Ví dụ Tốt vs Tệ
- Ưu tiên nguồn
- Quy trình kiểm chứng nội dung user dán
- Bảo mật truy vấn

## Thiết kế truy vấn

- **Bóc từ khóa cốt lõi**, bỏ từ thừa ("làm thế nào", "cho tôi", "bạn nghĩ").
- **Trích thực thể + phiên bản chính xác**: `<tên> <phiên bản> <thuật ngữ official>`.
- **Chủ đề kỹ thuật → dùng tiếng Anh** (tài liệu gốc hầu hết tiếng Anh).
- **Thêm qualifier theo ý định**: `latest`, `release notes`, `changelog`, `documentation`,
  `vs`, `deprecated`, `migration guide`, kèm năm nếu cần mốc thời gian.
- **Một truy vấn một ý.** Cần nhiều thứ → chạy nhiều truy vấn riêng.

## Toán tử tìm kiếm

Truyền nguyên văn trong chuỗi `query`:

- `"cụm chính xác"` — giữ nguyên cụm/tên/thông báo lỗi.
- `site:domain` — giới hạn nguồn, vd `site:docs.python.org`, `site:github.com`.
- Thông báo lỗi: để **nguyên văn trong ngoặc kép**, bỏ phần biến động (đường dẫn tuyệt đối, số dòng,
  địa chỉ bộ nhớ) để khớp nhiều trường hợp hơn.

## Ví dụ Tốt vs Tệ

| Yêu cầu của user | ❌ Query tệ | ✅ Query tốt |
|---|---|---|
| "Spring Boot mới nhất hỗ trợ Java 21 chưa?" | `spring boot java` | `Spring Boot latest version Java 21 support site:spring.io` → rồi đọc trang release notes |
| Lỗi `NoClassDefFoundError: javax/xml/bind/JAXBException` trên Java 11 | `java jaxb error` | `"NoClassDefFoundError" "javax/xml/bind/JAXBException" Java 11 fix` |
| "React 19 bỏ forwardRef đúng không?" | `react forwardRef` | `React 19 forwardRef deprecated site:react.dev` → đọc blog/docs → phán quyết ĐÚNG/SAI |
| "Thư viện X bản nào ổn định nhất?" | `X library` | `<X> latest stable release` + `site:github.com <X> releases` → đọc trang Releases |
| "So sánh Postgres vs MySQL cho phân tích" | `postgres mysql` | `PostgreSQL vs MySQL OLAP analytical workload comparison` → đọc 2 nguồn, đối chiếu |

## Ưu tiên nguồn

1. Tài liệu/website chính thức (docs, trang chủ dự án, release notes, RFC, spec).
2. Repo GitHub gốc (README, CHANGELOG, issues, releases).
3. Nguồn uy tín (MDN, Stack Overflow upvote cao, blog của chính tác giả/tổ chức).
4. Còn lại: tham khảo, cần đối chiếu thêm.

Cảnh giác nội dung SEO rác, bài AI-generated, tài liệu cũ. Luôn nhìn **ngày xuất bản**.

## Quy trình kiểm chứng nội dung user dán

1. **Tách thành từng tuyên bố factual** (mỗi câu khẳng định một dữ kiện riêng).
2. Mỗi tuyên bố → một lần `web_search` riêng → `web_read` nguồn gốc.
3. Gắn nhãn từng tuyên bố: **ĐÚNG / SAI / CẦN CẬP NHẬT / KHÔNG ĐỦ BẰNG CHỨNG** + URL nguồn.
4. Nếu SAI → nêu thông tin đúng kèm nguồn. Nếu nguồn mâu thuẫn → trình bày cả hai phía.
5. **Không bịa.** Không tìm được thì nói rõ, đừng đoán.

## Bảo mật truy vấn

Truy vấn rời máy và tới công cụ tìm kiếm bên ngoài. **Không** đưa secret, token, API key, tên khách
hàng, hostname/tên service nội bộ, hay đoạn code độc quyền vào query. Chỉ tìm bằng thuật ngữ công
khai. Nếu thông tin cần tra cứu bản thân nó là dữ liệu mật thì không nên search — search web cũng
không giúp được gì cho dữ liệu nội bộ.
