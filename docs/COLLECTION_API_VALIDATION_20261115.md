# Tích hợp kiểm tra mẫu và mã thiết bị — 15/11/2026

**Cập nhật tiếp theo:** đã thêm [chống ghi trùng theo request_id](COLLECTION_IDEMPOTENCY_20261115.md), metadata mẫu mới version3 và 44 test. Phần kiểm thử/version2 bên dưới ghi mốc tích hợp ban đầu.

Đã tích hợp vào checkout web `storage/postgres-local` và chốt commit local theo [checklist ngày 16/11](WEB_RELEASE_CHECKLIST_20261116.md), **chưa push/deploy**. Không phải nội dung có sẵn trong commit `cee1cbb...` đã bàn giao trước đây. Khi triển khai phần này phải đưa backend, module `collection_quality.py`, collector JS và template mới cùng phiên bản; frontend/API cũ không gửi `device_id` sẽ nhận 400.

## Hợp đồng ghi mới

`POST /api/submit-sample` nhận `participant_id`, `session`, **`device_id`**, `events`. Mã thiết bị gồm 1–40 ký tự ASCII: chữ, số, gạch ngang/gạch dưới, ký tự đầu là chữ hoặc số. Mã do người thu đặt cho bộ máy/bàn phím đang dùng, không có tên người; đổi mã khi đổi thiết bị. Không tự nhận dạng hoặc xác minh phần cứng. Collector nhớ mã trong localStorage khi trình duyệt cho phép; nếu không, người dùng nhập lại.

Trước ghi, backend kiểm danh sách sự kiện hữu hạn/không âm, đúng thứ tự, đủ cặp nhấn–nhả, không lặp down, đúng câu và hoa/thường. Modifier được kiểm cân bằng nhưng không tính vào câu. Gõ chồng tạo flight âm vẫn hợp lệ; keyup của R có thể thành r. Có `code` hợp lệ thì kiểm ghép theo code và giữ code trong bản ghi; keycapture hiện tại vẫn gửi key/type/t như trước. Không đổi bộ trích đặc trưng hoặc mô hình đăng ký/đăng nhập.

Mẫu mới lưu thêm `device_id`, `collection_schema_version=2`. `collected_at` vẫn do server tạo theo UTC; `rep` do server cấp. Giá trị client tự gửi cho các trường server không được dùng. PostgreSQL schema database vẫn là 1 vì payload JSONB đã hỗ trợ trường bổ sung, không cần sửa bảng hoặc nhập lại dữ liệu.

## Lượt bị khuyết và lịch sử lỗi

Trong khóa ghi hiện có (file lock hoặc transaction/advisory lock PostgreSQL), backend đọc lịch sử và cấp `max(rep)+1` cho đúng phiên. `count` trả về là số mẫu, khác `rep` khi lịch sử có khoảng khuyết. Ví dụ lượt 1,3 thì ghi lượt 4 và trả count=3. Giới hạn 40 áp theo số mẫu. Không đánh lại số lịch sử cho liền mạch.

Nếu phiên cũ có khóa trùng hoặc rep không hợp lệ, trả 409 với `collection_history_needs_review`, không thêm dòng hoặc đoán sửa. Với backend file, dòng JSON hỏng cũng chặn ghi; không lặng lẽ bỏ dòng để tính lượt. File JSONL thiếu newline cuối được nối bằng newline trước mẫu mới. Dữ liệu cũ thiếu device_id vẫn đọc/thu tiếp được nếu khóa hợp lệ; không bù metadata cũ và không đổi tập đánh giá hoặc điểm.

Ở mốc tích hợp ban đầu chưa có idempotency request. Phần này đã được bổ sung ở tài liệu mới liên kết đầu trang: cùng mã yêu cầu/nội dung không tạo lượt mới. Cơ chế không chứng minh hai lần gõ đến từ người khác nhau.

## Kiểm tra đã chạy

- **31/31 test trên Linux/PostgreSQL 17 thật**: 16 hồi quy persistence và 15 ca collector mới trên hai backend (8 file, 7 PostgreSQL), không skip. Có ghi đồng thời, export/import/backup, rollback, đăng ký/OTP, Gunicorn hai worker và restart. Sau restart, mẫu vẫn giữ `device_id` và phiên bản metadata.
- Backend file trên Windows cũng đạt 8/8 ca; dữ liệu giả ở thư mục riêng.
- Chrome headless gọi Flask localhost thật, không mock fetch: thiếu mã không ghi mẫu; gõ 22 sự kiện lưu thành công; tải lại giữ mã người tham gia, mã thiết bị và tiến độ. Không lỗi JavaScript; không tràn ngang ở 320/390/1440 px.
- Mẫu do Chrome/API tạo được checker preflight v4 kiểm độc lập: 1 mẫu đạt, 0 dòng cần xem; kiểm cú pháp JS và `git diff --check` đạt.

Lệnh hồi quy trong môi trường Linux có PostgreSQL thử riêng: `python -m pytest tests/test_postgres_storage.py tests/test_collection_api.py -q -p no:cacheprovider`. Bộ test chỉ nhận URL loopback của database `keyguard_local`, tạo/xóa schema thử của chính nó. Không dùng URL Neon hoặc dữ liệu thật. Container PostgreSQL thử riêng đã dừng, volume giữ lại.

Artifact kiểm thử trong checkout nghiên cứu: `results/collection_api_validation_20261115.json`, `results/collection_browser_checks_20261115.json`; XML và ảnh nằm trong preview. Report/gói v4/mô hình/ngưỡng giữ nguyên. Chưa ghi dữ liệu lên Neon/Render, chưa đưa thay đổi vào bản deploy đang chạy.

Ưu tiên tiếp: bổ sung mã yêu cầu để xử lý việc gửi lại sau mất mạng, có đối chứng đồng thời và restart trên local; chuyển Render vẫn phụ thuộc backup/đối chiếu/phương án tài khoản do chủ dịch vụ thực hiện.
