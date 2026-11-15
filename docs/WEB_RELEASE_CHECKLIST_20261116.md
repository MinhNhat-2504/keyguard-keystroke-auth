# Checklist triển khai web đồng bộ — 16/11/2026

Mốc phát hành: **collector-request-id-v3-20261116**. Commit chứa tài liệu này là bản web cần review; lấy full SHA bằng `git log -1 --format=%H -- docs/WEB_RELEASE_CHECKLIST_20261116.md`. Commit cha `cee1cbb...` chưa có kiểm tra collector/mã thiết bị/request_id mới. Không suy commit GitHub là commit đang chạy trên Render.

**Trạng thái hiện tại: chuẩn bị local, chưa push/deploy.** Những ô dịch vụ thật dưới đây để trống đến khi có bằng chứng. Người thao tác Render theo lựa chọn của Nhật là Thư; tài khoản CLI hiện có của trợ lý không quản lý KeyGuard.

## Nội dung phải đi cùng phiên bản

- `app.py`, `collection_quality.py`, `Dockerfile.storage`.
- `templates/index.html`, `static/script.js`, `static/pending-sample.js` và các asset đang được template sử dụng. `static/readability.css` đi cùng ba template index/login/register để không tạo liên kết CSS thiếu.
- API mới bắt buộc `device_id` và `request_id` cho mẫu collector; frontend cũ sẽ nhận 400. Mẫu mới có metadata version3; PostgreSQL schema vẫn là 1, không có migration/backfill trong bản này.
- Mô hình, ngưỡng, keycapture và dữ liệu nghiên cứu không thay. `request_id` nằm cùng mẫu, không có dịch vụ queue/cache cần cấu hình thêm.

## A. Kiểm bản local trước khi công bố

- [x] Kiểm 44 ca Linux/PostgreSQL thật, không skip; có đồng thời, rollback, phiên đầy và restart Gunicorn hai worker.
- [x] Chrome → Flask localhost thật: lỗi truyền phản hồi sau commit, reload tab, mất kết nối trước gửi và 429 không nhân đôi mẫu; giữ đúng mã chờ và controls.
- [x] Mẫu do trình duyệt/API tạo đạt preflight độc lập. Kiểm CSS ở 320/390/1440 px không tràn ngang.
- [x] Có bằng chứng công khai không chứa secret/raw tại `docs/evidence/collection_idempotency_validation_20261115.json` và `docs/evidence/collection_idempotency_browser_checks_20261115.json`.
- [x] Bản sao runtime lấy từ Git index đạt lại 44/44 test. `docs/evidence/web_release_20261116.json` ghi hash byte đã stage; hash workspace CRLF trong bằng chứng cũ được giữ riêng, nội dung mã khớp sau chuẩn hóa LF.

Kiểm thử thực nghiệm, log XML và fixture private vẫn giữ riêng trong workspace. Chạy test Python: `python -m pytest tests/test_postgres_storage.py tests/test_collection_api.py -q -p no:cacheprovider`, chỉ với PostgreSQL loopback/database `keyguard_local` như guard trong tests. Script browser dùng Chrome/venv của workspace được mô tả trong [biên bản idempotency](COLLECTION_IDEMPOTENCY_20261115.md).

## B. Trước khi chuyển dịch vụ thật

- [ ] Review commit, push đúng nhánh `storage/postgres-local`, ghi full SHA sau push và xác nhận remote chứa SHA đó. Không push raw, `.env`, backup hoặc cả workspace.
- [ ] Chủ dịch vụ vào đúng KeyGuard: repo `MinhNhat-2504/keyguard-keystroke-auth`, URL `https://keyguard-keystroke-auth.onrender.com`.
- [ ] Chốt khoảng dừng thu/test. Đợi mẫu đang chờ được xác nhận khi dịch vụ cũ còn hoạt động; không yêu cầu xóa sessionStorage hoặc đóng tab để bỏ mẫu chưa xác nhận.
- [ ] Xuất backup Render mới nhất nguyên byte, lưu checksum riêng tư. Đối chiếu mẫu/log với Neon và nhập phần chênh lệch theo lô đã review nếu có. Chưa đối chiếu thì chưa deploy.
- [ ] Kiểm tài khoản/profile/OTP còn giữ được. Nếu không có backup đầy đủ, Nhật phải chốt rõ phương án tài khoản cũ; không tự hiểu việc chọn Thư thao tác là đồng ý bỏ tài khoản.
- [ ] Backup Neon trước chuyển. Khi cần thử restore, dùng target rỗng khác; không restore đè database đang dùng. Bản sao Neon cũ không thay backup Render mới nhất.

## C. Cấu hình và deploy nguyên commit

- [ ] Trong Render, cấu hình `KEYGUARD_STORAGE=postgres`, `DATABASE_URL` đúng Neon/TLS và khóa admin mới qua kênh riêng. Giữ các biến verify/Python đang dùng. Không chép giá trị secret vào ảnh, Git hoặc chat.
- [ ] Chọn Save only khi chuẩn bị ENV, tránh triển khai backend cũ giữa các bước cấu hình. Chọn đúng branch/commit đã review; triển khai toàn bộ tree của commit, không chép JS hoặc backend riêng lẻ.
- [ ] Với Docker, dùng Dockerfile có `collection_quality.py`; với build Python, kiểm requirements của nhánh và start Gunicorn hiện có. Không tự init/import database lúc web startup.
- [ ] Đợi Events báo Live, ghi **full deploy SHA, thời điểm và trạng thái**; SHA phải khớp bản đã review. Đối chiếu trước khi thực hiện test có ghi dữ liệu.
- [ ] Mở mới hoặc tải lại đầy đủ collector. Kiểm `/static/pending-sample.js` và `/static/readability.css` trả 200, không lỗi import hoặc JavaScript. Các tab dùng frontend cũ cần chuyển sang bản mới trước khi tiếp tục thu.

## D. Kiểm ghi dữ liệu sau khi đã xác nhận đúng deploy

- [ ] Dùng mã người tham gia test riêng và mã thiết bị tự khai báo. Gõ một mẫu; kiểm timestamp UTC server, metadata version3, request_id và hash trong export/backup riêng tư.
- [ ] Gửi lại **đúng request_id và payload đó**: trả `replayed=true`, rep cũ, count không tăng. Không tạo ID mới khi retry. Cùng ID nhưng sửa thiết bị/phiên/sự kiện phải 409 và không đổi mẫu gốc.
- [ ] Thử ngắt kết nối trong lượt test, dùng nút gửi lại hoặc reload **cùng tab**; chỉ xác nhận đạt khi số mẫu và request_id đối chiếu khớp. Thử nghiệm localhost trước đây không thay minh chứng dịch vụ thật.
- [ ] Trong khoảng dừng đã chốt, restart ứng dụng Render; tài khoản test, tiến độ và replay của request cũ vẫn hoạt động. Không dùng restart database production để thay phép thử này.
- [ ] Backup sau chuyển, thử restore vào target rỗng khác; đối chiếu counts/nội dung/hash theo biên bản, không chỉ ảnh “thành công”.
- [ ] Lưu bằng chứng đã ẩn secret: full SHA Live, backend, checksum backup trước/sau, xử lý tài khoản, mẫu/ID/count trước–sau restart và kết quả restore. Sau đối chiếu mới mở lại thu dữ liệu.

## Khi có lỗi

Giữ thu mẫu tạm dừng và giữ nguyên dữ liệu/backup/log để phân tích. Không đổi về backend file để che lỗi kết nối PostgreSQL, không xóa schema hoặc restore bản cũ đè lên dữ liệu mới. Nếu cần rollback code, phải review tính tương thích trước; bản cha chưa hiểu request_id nên không được mở lại collector với frontend mới. Không thông báo cutover hoàn tất khi còn ô kiểm thực tế chưa có bằng chứng.

## Giới hạn giữ nguyên

SessionStorage chỉ hỗ trợ mẫu chờ trong tab; đóng tab/xóa bộ nhớ có thể mất payload. Nếu browser chặn storage, còn retry trong RAM và cảnh báo không đóng/tải lại khi chưa xác nhận. File backend trên ổ tạm vẫn có thể mất cả mẫu và mã yêu cầu; việc chốt commit không thay cho chuyển PostgreSQL đúng quy trình.
