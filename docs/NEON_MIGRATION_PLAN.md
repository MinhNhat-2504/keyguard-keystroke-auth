# Kế hoạch chuyển lưu trữ sang Neon

Ngày đối chiếu: 13/11/2026. Đã liên kết project Neon, khởi tạo schema KeyGuard và nhập nguồn đã kiểm tra theo yêu cầu tiếp tục của người dùng. **601 mẫu/15 mã đã đối chiếu khớp trên Neon; chưa push hoặc chuyển Render**.

## Lựa chọn

Chọn **Neon Free** cho bài tập lớn: PostgreSQL bên ngoài filesystem tạm của Render, không cần đổi framework hoặc mô hình. Trang giá hiện ghi Free không giới hạn thời gian và không cần thẻ; vẫn có quota và điều khoản sử dụng, cần kiểm tra lại trong Dashboard khi tạo. Không chuyển gói trả phí tự động.

Render Postgres Free không phù hợp để chốt lưu dài hạn: tài liệu ghi hết hạn sau 30 ngày và không hỗ trợ backup. Neon có scale-to-zero cho compute; đây không phải cơ chế sao lưu. Vẫn cần giữ bản sao độc lập, không hứa dữ liệu tồn tại vĩnh viễn.

Nguồn chính thức:

- [Neon pricing](https://neon.com/pricing)
- [Neon scale to zero](https://neon.com/docs/introduction/scale-to-zero)
- [Neon connection strings và TLS](https://neon.com/docs/connect/connect-from-any-app)
- [Render Free: filesystem và thời hạn PostgreSQL](https://render.com/docs/free)

## Dữ liệu đã bảo toàn và giới hạn

Nguồn: `keyguard_data_20261113_114958.zip` đã tải trước đó, SHA-256 `9e195b9338f4d5f2e73341349b5fcc97a6525dce7c9a3016cb857fe11f6779df`.

- Giữ nguyên ZIP trong `report/preview/export-backup/` của checkout nghiên cứu và thêm bản nguyên byte trong `report/preview/postgres-export-rehearsal/`; các đường dẫn này ignored.
- CRC đạt, 15 JSONL, 601 mẫu. Nhập vào PostgreSQL local, đọc lại từng mã theo thứ tự khớp nguồn; nhập lần hai không nhân đôi. Backup CLI rồi restore sang schema rỗng khác khớp; `/admin/export` trả đủ các JSONL có hàng và thứ tự tương đương.
- Giữ hai hàng có cùng khóa P10/session 1/rep 29, không sửa dữ liệu nghiên cứu. JSONB giữ giá trị, không giữ whitespace/byte của JSONL: ZIP gốc vẫn là nguồn đối chiếu.
- ZIP không có accounts, profiles, challenges, participants registry hoặc attempts.csv. Không gọi đây là backup đầy đủ hay nguồn log server nguyên bản. Bản sao cùng ổ đĩa chưa thay thế được backup ngoài máy.
- Kết quả công khai: checkout nghiên cứu `results/postgres_export_rehearsal.json`. Dữ liệu đầy đủ chỉ ở preview ignored; schema diễn tập đã xóa, container DB local đã dừng sau khi kiểm tra.

## Phần cần Thư bàn giao nếu còn

1. Bản xuất server nguyên gốc và thời điểm xuất; nếu không còn thì ghi rõ không còn. Không tái tạo bằng Excel rồi gọi là raw.
2. Nếu còn bản sao `accounts.json`, `profiles/`, `participants.json`, `attempts.csv`: bàn giao riêng tư, không commit tên tài khoản/profile hoặc mật khẩu. Không dùng tài khoản mẫu để thay thế trạng thái đã mất.
3. Nếu không có các phần trên, cần quyết định rõ phạm vi chuyển chỉ gồm 601 mẫu lịch sử và tài khoản bắt đầu lại. Chưa thực hiện quyết định này hoặc thay thế trạng thái production trong lượt chuẩn bị.

## Trình tự trước khi chuyển Render

1. Đã hoàn thành liên kết: dùng project Free người dùng tạo `bitter-resonance-81924970`, tên hiển thị `my-first-project`, nhánh `production`, vùng Oregon theo lựa chọn onboarding. Không tạo project/database mới hoặc chuyển gói trả phí. Các bước dưới là quy trình tham chiếu; trạng thái đã làm ghi ở phần cuối.
2. Chỉ lấy chuỗi kết nối vào nơi cấu hình bí mật. Dùng kết nối direct cho init/import/backup và TLS theo chuỗi Neon cung cấp. Không dán URL hoặc mật khẩu vào chat, repo, ảnh hay log. Chưa sửa ENV Render ở bước này.
3. Đã hoàn thành với nguồn ZIP lịch sử: runner `migrate_verified_neon.py` kiểm tra lại hash/CRC/từng file, dry-run rồi `--apply` vào target rỗng; giữ backup trước/sau. Bộ test local và runner diễn tập vẫn chỉ cho loopback; kiểm tra cloud dùng runner riêng `check_neon_application.py` với schema thử tách biệt.
4. Trước lượt chuyển thật, tạm ngừng nhận mẫu/đăng ký mới trong khoảng sao lưu và chuyển để tránh ghi hai nơi. Lấy bản xuất mới nhất và đối chiếu nguồn lại; bản ZIP đã tải chỉ phản ánh thời điểm cũ. Giữ mọi phần còn lấy được trước khi redeploy hoặc đổi khóa quản trị.
5. Sau khi chốt phạm vi, mới import `--apply` vào DB ngoài rỗng. Đọc lại, đối chiếu thứ tự/giá trị, lấy backup riêng tư đầy đủ và thử restore vào DB kiểm tra riêng, không ghi đè DB chính.
6. Chuẩn bị commit backend PostgreSQL rồi kiểm tra diff; chỉ triển khai khi DB đã được khởi tạo và xác minh. Đổi `KEYGUARD_STORAGE=postgres`, `DATABASE_URL` và khóa quản trị mới trên Render theo cùng kế hoạch. Không ghi secret vào lệnh Start/Build; giữ giá trị `KEYGUARD_VERIFY_LIMIT` đang dùng, không tự suy từ ảnh bị che.
7. Kiểm tra bằng mã/tài khoản thử tách biệt: register, collector/resume, verify/OTP; restart Render rồi đọc lại. Đối chiếu DB đúng, không vô tình quay về file. Không coi kết quả local là kiểm thử Neon đã đạt.
8. Sau khi nhận ghi trên PostgreSQL, nếu bản web có lỗi thì tạm ngừng ghi và sửa bản web dùng cùng DB. Không rollback sang file mode vì sẽ tạo hai bộ trạng thái khác nhau. Giữ DB và các bản backup, không tự xóa để chạy lại.

## Sao lưu vận hành

Backup CLI đầy đủ sau mỗi đợt thu/kiểm thử quan trọng và trước thay đổi cấu hình; lưu ngoài máy ở nơi riêng tư có quyền truy cập phù hợp. Giữ ZIP/JSONL nguồn riêng để bảo toàn byte và lịch sử. Thử restore định kỳ trên target rỗng riêng, không lấy restore thành công làm bằng chứng dữ liệu đầu vào đầy đủ. Chưa thiết lập lịch tự động hoặc backup ngoài máy.

## Trạng thái truy cập

Neon CLI 9.4.0 đã đăng nhập bằng profile riêng `keyguard-local-20261113`. Đã liên kết project `bitter-resonance-81924970` (tên hiển thị `my-first-project`), tổ chức `org-odd-wildflower-77750748`, nhánh `production`. Đây là project người dùng đã tạo trong onboarding, không tạo project khác.

CLI ghi `DATABASE_URL`, `DATABASE_URL_UNPOOLED` cùng ba biến metadata vào `.env.local`. Tệp này và các biến thể `.env.*` được Git bỏ qua, đồng thời loại khỏi Docker build context. Không đưa nội dung bí mật vào tài liệu hoặc kết quả công khai. Đã dùng `neon init`/`neon link` theo [hướng dẫn Neon](https://neon.com/get-started/prompt.md); bỏ thiết lập agent/TypeScript vì ứng dụng đã là Flask và phiên này dùng CLI được xác thực để truy cập.

`scripts/check_neon_connection.py` trước đó xác nhận SELECT/TLS thành công và chưa có `public.kg_schema`; đây là mốc trước khi nhập. Kết quả lịch sử: `results/neon_connection_check.json`. Theo yêu cầu tiếp tục, `scripts/migrate_verified_neon.py` đã kiểm tra lại ZIP/hash/từng file, khởi tạo schema và nhập 601 mẫu vào `public`. Target trước nhập rỗng. Đối chiếu từng mã/thứ tự và export HTTP khớp, nhập lại trả `already_imported`. Trạng thái sau nhập: kg_samples=601, kg_documents=0, kg_attempts=0, kg_imports=1. Không tạo registry/tài khoản/profile/log thay cho dữ liệu không có trong ZIP.

Backup trước/sau tại checkout nghiên cứu `report/preview/neon-migration-20261113/`, tệp `.private-backup.json`, chỉ lưu riêng tư và ignored. Kết quả công khai `results/neon_migration_validation.json`. Đây là bản nguồn lịch sử đã chốt, không khẳng định đã lấy được trạng thái mới nhất từ Render. Render chưa đổi cấu hình; chưa được cấp quyền quản lý Render trong bước này.

Flask/Gunicorn hiện đọc biến môi trường của process, không tự nạp `.env.local`. Khi chạy local phải nạp file qua công cụ quản lý môi trường hoặc Docker `--env-file` sau khi xử lý đúng định dạng dotenv. Trong lượt kiểm tra đã tạo bản env Docker riêng tại `.storage-test/neon-runtime.env`, cũng ignored, chỉ chứa hai biến database. Schema chính hiện đã init; các môi trường mới vẫn phải init trước vì backend cố ý dừng nếu thiếu schema, không fallback về file. Khi chuyển Render sau này cần đặt biến trong Dashboard; việc có `.env.local` trên máy không tự cập nhật Render.

## Kiểm tra ứng dụng trên Neon đã hoàn tất

`scripts/check_neon_application.py` tái sử dụng năm ca tích hợp hiện có, chỉ thay setup sang schema ngẫu nhiên `kg_neon_check_*` trên Neon thật. Không bỏ guard loopback của bộ test local. Kết quả **5/5 đạt, không lỗi**:

- Đăng ký 20 mẫu, nhận trực tiếp lên 21, OTP sai không tăng mẫu, OTP đúng lên 22, dùng lại trả 410.
- Cấp mã đồng thời không trùng; tám lượt ghi đồng thời có thứ tự 1–8.
- Cố ý gây lỗi ghi log trả 500 và rollback profile/nhật ký cùng nhau.
- OTP sai ba lần trả 401/401/429 và giữ đúng trạng thái khóa.
- HTTP thật qua Gunicorn hai worker, khởi động lại ứng dụng vẫn giữ tài khoản/tiến độ và OTP đang chờ, xác nhận thành công và chống dùng lại.

Đã khôi phục backup 601 mẫu vào schema rỗng riêng trên cùng Neon, đối chiếu toàn bộ payload khớp và restore lặp không nhân đôi. Tất cả schema thử đã dọn: còn 0. Backup dữ liệu `public` sau kiểm thử khớp hoàn toàn bản trước kiểm thử, không có mẫu/tài khoản thử lẫn vào 601 mẫu.

Các ca ghi xác thực trên dùng kết nối direct có TLS để tách schema. URL pooled đã đọc và xác nhận cùng dữ liệu; **chưa chạy toàn bộ ca ghi bằng pooled**, chưa đo tải hoặc kiểm thử restart/suspend của chính Neon. Gunicorn chạy trên Linux Docker local kết nối Neon, không phải bản Render. Kết quả công khai trong checkout nghiên cứu: `results/neon_application_checks.json`; hash mã backend vẫn khớp bản đã đạt 16/16 local. Báo cáo nghiên cứu và hai bộ Word/PDF nguyên hash.

Việc còn trước chuyển Render: sao lưu/đối chiếu trạng thái runtime mới nhất và chốt phần tài khoản/profile/log nếu còn; kiểm tra diff backend, chuẩn bị commit cùng cấu hình bí mật, triển khai có kiểm soát và kiểm tra ghi/restart trên Render. Có thể dùng URL direct đã kiểm thử cho bước chuyển đầu tiên với quy mô hiện tại. Xem [bàn giao Render](RENDER_CUTOVER.md): CLI đã đăng nhập nhưng workspace hiện không có KeyGuard, nên chưa lấy được bản backup mới hay đổi cấu hình/deploy dịch vụ. Chưa thiết lập lịch backup tự động.
