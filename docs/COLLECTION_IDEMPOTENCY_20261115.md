# Chống lưu trùng khi gửi lại mẫu — 15/11/2026

Đã làm trên checkout `storage/postgres-local` và chốt commit local theo [checklist ngày 16/11](WEB_RELEASE_CHECKLIST_20261116.md), **chưa push/deploy**. Áp cho collector, không thay đăng ký/đăng nhập, mô hình hoặc ngưỡng.

## API và lưu trữ

Mỗi lần gõ mới có `request_id` gồm đúng 32 ký tự hex thường, tạo bằng `crypto.getRandomValues`. `POST /api/submit-sample` bắt buộc có trường này cùng mã người tham gia, phiên, thiết bị và sự kiện. Thiếu/sai mã trả 400, không âm thầm lưu theo kiểu cũ. Backend và các file JS/template phải triển khai cùng phiên bản.

Mã được xét trong phạm vi **một participant_id**, trên tất cả phiên của mã đó. Cùng request_id và cùng payload đã kiểm tra trả 200, `replayed=true`, `rep` của mẫu gốc và `count` hiện tại; không ghi dòng mới và không đổi thời điểm mẫu gốc. Vì vậy count có thể khác rep. Gửi lại mẫu đã có vẫn thành công khi phiên đủ 40 mẫu.

Cùng mã nhưng đổi phiên, thiết bị hoặc sự kiện trả 409 `request_id_payload_conflict`. Lịch sử có mã yêu cầu trùng hoặc hash không khớp bản ghi trả 409 để rà, không ghi đè. Hash SHA-256 tính trên JSON chuẩn hóa của session/device/events đã kiểm; đây là đối chiếu nội dung, không phải chữ ký hoặc xác minh danh tính.

Mẫu mới lưu `request_id`, `request_payload_sha256`, `collection_schema_version=3` cùng timestamp UTC server. Không thêm bảng hoặc nâng database schema: payload JSONB hiện tại đã đủ. Các bản ghi version2/legacy vẫn đọc nguyên trạng, không bù request_id hoặc metadata cho lịch sử.

Việc tìm mã cũ và ghi mẫu mới cùng nằm trong khóa file hoặc giao dịch/advisory lock PostgreSQL đang có. Mã chống trùng nằm **cùng bản ghi mẫu**, không chỉ nằm trong RAM, nên app restart vẫn nhận ra lần gửi lại. Nếu PostgreSQL insert rồi request lỗi trước commit, transaction rollback cả mẫu và mã; gửi lại có thể lưu mới đúng một lần. Đây là bảo đảm qua luồng ứng dụng đã khóa; không ngăn tác động của người sửa database trực tiếp.

## Trình duyệt mất kết nối

Trình duyệt chốt nguyên participant/session/device/events/request_id trước khi gửi. Một mẫu chỉ có một mã, mọi lần retry giữ nguyên mã và nội dung. Payload đang chờ lưu trong **sessionStorage của tab**, xóa sau xác nhận đúng request_id; không đưa raw vào localStorage lâu dài. Người dùng không đổi người/phiên/thiết bị hoặc gõ mẫu mới khi còn mẫu chưa xác nhận.

Mỗi lượt bấm thử tối đa hai lần, mỗi lần timeout 15 giây. Mất phản hồi, 5xx, 408 hoặc 429 giữ mẫu; hiện nút **Gửi lại mẫu đang chờ** khi chưa xác nhận. Nếu tải lại cùng tab, khôi phục đúng mã/phiên/thiết bị và gửi lại mẫu cũ trước. Không dùng số đếm tiến độ để đoán mẫu nào đã được lưu. 409 cần đối chiếu vẫn giữ mẫu chờ; lỗi từ chối đầu vào rõ ràng cho phép sửa và gõ lại.

Nếu sessionStorage bị chặn, vẫn retry an toàn trong RAM của tab và có thông báo đừng tải lại/đóng tab khi chưa xác nhận. **Đóng tab, xóa dữ liệu trình duyệt hoặc mất storage có thể mất payload chờ**; chưa có hàng đợi offline lâu dài. Hai lần gõ mới có hai request_id khác nhau vẫn là hai mẫu; không tự gộp chỉ vì timing giống nhau.

## Bằng chứng kiểm thử

- **44/44 test Linux, PostgreSQL thật, không skip**: 16 hồi quy, 13 file API, 15 PostgreSQL API. Có 8 POST cùng mã đồng thời chỉ một insert; hai nội dung khác cùng mã chỉ một bên thành công; rollback sau insert; replay lúc phiên đầy; app reimport và Gunicorn hai worker restart vẫn trả mẫu gốc.
- Windows file API 13/13 đạt. Backend file cũng lưu request_id vào JSONL, không phụ thuộc cache trong process.
- Chrome và Flask localhost thật: một phản hồi bị mất sau commit được tự gửi lại; mất cả hai phản hồi rồi reload vẫn chỉ một mẫu; mất kết nối trước gửi rồi bấm retry lưu một mẫu; giả lập 429 sau commit không tạo bản ghi phụ. Mẫu đang chờ khóa đúng controls. Tổng 5 mẫu mới trong kịch bản, 5 request_id duy nhất; không lỗi JS hoặc tràn ngang ở 320/390/1440 px.
- Fault injection ở lớp fetch phía client để làm mất phản hồi/giả lập 429, server và ghi file vẫn chạy thật. Đây là kiểm thử lỗi có kiểm soát trên localhost, không phải quan sát sự cố mạng thực ngoài Internet.

Chạy `python -m pytest tests/test_postgres_storage.py tests/test_collection_api.py -q -p no:cacheprovider` trong Linux với PostgreSQL thử loopback/database keyguard_local. Script browser: `node scripts/check_idempotency_browser.mjs` (Windows, Chrome và venv nghiên cứu hiện có). Cấu hình test không đọc URL Neon hoặc env production.

Artifact ở checkout nghiên cứu: `results/collection_idempotency_validation_20261115.json`, `results/collection_idempotency_browser_checks_20261115.json`; XML/log/fixture riêng trong preview. Container PostgreSQL thử đã dừng, giữ volume. Báo cáo/ZIPv4/dữ liệu thật/ngưỡng/điểm không đổi.

**Render chưa có tính năng này.** Cơ chế chỉ tồn tại chừng nào bản ghi được giữ; backend file trên ổ tạm vẫn có thể mất cả mẫu lẫn mã khi môi trường bị thay. Cutover PostgreSQL vẫn cần chủ dịch vụ backup/đối chiếu/chốt tài khoản như hướng dẫn trước.
