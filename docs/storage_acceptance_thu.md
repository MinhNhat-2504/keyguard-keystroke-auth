# Biên bản kiểm chứng bảo toàn dữ liệu PostgreSQL (B2)

* **Người thực hiện:** Thư

* **Thời gian thực hiện:** Rạng sáng ngày 15/11/2026 (từ 00:55 đến 01:22)

## 1. Môi trường thực hiện

* **Hệ điều hành:** Windows (Docker Desktop)

* **Phiên bản Docker:** `Docker version 29.3.0, build 5927d80`

* **Database & Web Image:** `postgres:17-alpine` và `python:3.11-slim`

* **Nhánh Git thực hiện:** `storage/postgres-local` (cập nhật từ `origin/storage/postgres-local`, commit `cee1cbb`)

## 2. Phần 1: Khởi động PostgreSQL, tạo dữ liệu và kiểm chứng qua Restart

### 2.1. Khởi động dịch vụ và xử lý lỗi thiếu schema ban đầu

* Lúc **00:55:03**, tôi khởi động container PostgreSQL (`db`) và build image `web`:

```
docker compose -f compose.storage.yml up -d db
docker compose -f compose.storage.yml build web

```

* Lúc **00:56:46**, tôi chạy `docker compose -f compose.storage.yml up -d web` nhưng container `web` tự thoát ngay sau khi khởi động. Kiểm tra log lúc **00:59:13** (`docker compose -f compose.storage.yml logs web`) phát hiện lỗi do chưa khởi tạo bảng dữ liệu:

```
RuntimeError: PostgreSQL schema not ready; run storage_admin.py init

```

* Lúc **01:00:54**, tôi chạy lệnh khởi tạo schema và khởi động lại dịch vụ `web` thành công (mở cổng cục bộ `127.0.0.1:56900`):

```
docker compose -f compose.storage.yml run --rm web python scripts/storage_admin.py init
docker compose -f compose.storage.yml up -d web
docker compose -f compose.storage.yml port web 8000

```

Kết quả khởi tạo:

```
PostgreSQL schema initialized; no legacy data imported

```

### 2.2. Tạo tài khoản thử và đối chiếu trước/sau khi Restart ứng dụng Web

* Sau khi truy cập giao diện web qua cổng `56900`, tôi tiến hành đăng ký mới **1 tài khoản thử nghiệm** có tên đăng nhập là `test_b2_thu` (lưu trữ dưới dạng bản ghi người dùng trong PostgreSQL, chưa thu mẫu gõ phím).

* **Trước khi restart (lúc 01:07:21):** Kiểm tra trạng thái database bằng lệnh `status`:

```
docker compose -f compose.storage.yml run --rm web python scripts/storage_admin.py status

```

Kết quả:

```
{"kg_documents": 2, "kg_samples": 0, "kg_attempts": 0, "kg_imports": 0}

```

Đồng thời gọi API `http://127.0.0.1:56900/api/check-username?username=test_b2_thu` trên trình duyệt (đã lưu ảnh chụp màn hình minh chứng):

```
{"available":false,"success":true,"username":"test_b2_thu"}

```

*(Ghi chú: theo `POSTGRES_STORAGE.md` của Nhật, bảng `kg_documents` chứa sổ đăng ký tài khoản/người tham gia, hồ sơ nhịp gõ và thử thách OTP. Tôi không đọc nội dung từng tài liệu nên không xác định cụ thể 2 tài liệu này là gì.)*

* **Thực hiện Restart container `web` (từ 01:08:06 đến 01:08:38):** Tôi chỉ dừng và khởi động lại container ứng dụng `web` (giữ nguyên container `db` và volume dữ liệu):

```
docker compose -f compose.storage.yml stop web
docker compose -f compose.storage.yml up -d web
docker compose -f compose.storage.yml port web 8000

```

Sau khi khởi động lại, container `web` chạy trên cổng mới `127.0.0.1:62179`.

* **Sau khi restart (lúc 01:09:48):** Kiểm tra lại trạng thái database bằng lệnh `status`:

```
docker compose -f compose.storage.yml run --rm web python scripts/storage_admin.py status

```

Kết quả:

```
{"kg_documents": 2, "kg_samples": 0, "kg_attempts": 0, "kg_imports": 0}

```

Gọi lại API trên cổng mới `http://127.0.0.1:62179/api/check-username?username=test_b2_thu` trên trình duyệt (đã lưu ảnh chụp màn hình minh chứng):

```
{"available":false,"success":true,"username":"test_b2_thu"}

```

* **Kết luận Phần 1:** Dữ liệu tài khoản `test_b2_thu` và trạng thái hệ thống trước và sau khi khởi động lại ứng dụng `web` hoàn toàn giống nhau (`kg_documents: 2` và `available: false`), chứng minh dữ liệu được lưu bền vững trong PostgreSQL thay vì mất đi theo bộ nhớ tiến trình web.

## 3. Phần 2: Kiểm chứng Backup và Restore sang Database rỗng

### 3.1. Quy tắc đối chiếu

1. **Đối chiếu số lượng bản ghi:** So sánh số dòng từng bảng dữ liệu (`kg_documents`, `kg_samples`, `kg_attempts`) giữa database nguồn (`keyguard_local`) và database đích (`keyguard_restore`) thông qua công cụ `storage_admin.py status`. Bảng `kg_imports` được loại khỏi phép so sánh vì đây là bảng ghi chú việc nhập (xem giải thích ở 3.3).

2. **Đối chiếu nội dung (Hash SHA-256):** Xuất file backup từ database nguồn (`source.private-backup.json`) và xuất lại file backup từ database đích sau khi restore (`target.private-backup.json`), sau đó tính mã băm SHA-256 bằng `certutil`. Hai mã băm giống nhau nghĩa là hai file có nội dung giống hệt nhau. *(Các file `.private-backup.json` được lưu ở thư mục cục bộ `D:\b2_backup`, không đưa lên GitHub).*

### 3.2. Các lệnh thực hiện Backup và Restore

* **Ghi số liệu nguồn và xuất backup từ database nguồn (lệnh `status` nguồn lúc 01:14:30 và lệnh `backup` lúc 01:15:04):**

```
docker compose -f compose.storage.yml run --rm web python scripts/storage_admin.py status
mkdir D:\b2_backup
docker compose -f compose.storage.yml run --rm -v "D:\b2_backup:/backup" web python scripts/storage_admin.py backup --out /backup/source.private-backup.json

```

Kết quả:

```
{"kg_documents": 2, "kg_samples": 0, "kg_attempts": 0, "kg_imports": 0}
Private backup written; includes accounts/profiles/challenges. Keep out of GitHub.

```

* **Tạo database đích rỗng `keyguard_restore` và khởi tạo schema (từ 01:16:34 đến 01:20:36):**

```
docker compose -f compose.storage.yml exec db psql -U postgres -c "CREATE DATABASE keyguard_restore;"
docker compose -f compose.storage.yml exec db psql -U postgres -d keyguard_restore -c "\dt"
docker compose -f compose.storage.yml run --rm -e "DATABASE_URL=$T" web python scripts/storage_admin.py init
docker compose -f compose.storage.yml run --rm -e "DATABASE_URL=$T" web python scripts/storage_admin.py status

```

Kết quả kiểm tra database đích trước khi restore (hoàn toàn rỗng):

```
Did not find any relations.
PostgreSQL schema initialized; no legacy data imported
{"kg_documents": 0, "kg_samples": 0, "kg_attempts": 0, "kg_imports": 0}

```

* **Chạy thử (Dry-run) và nạp dữ liệu (Restore --apply) vào database đích (từ 01:20:51 đến 01:21:29):**

```
docker compose -f compose.storage.yml run --rm -e "DATABASE_URL=$T" -v "D:\b2_backup:/backup" web python scripts/storage_admin.py restore --source /backup/source.private-backup.json
docker compose -f compose.storage.yml run --rm -e "DATABASE_URL=$T" -v "D:\b2_backup:/backup" web python scripts/storage_admin.py restore --source /backup/source.private-backup.json --apply
docker compose -f compose.storage.yml run --rm -e "DATABASE_URL=$T" web python scripts/storage_admin.py status

```

Kết quả:

```
Dry-run: backup parsed, not imported; --apply validates references and writes only to empty target
imported
{"kg_documents": 2, "kg_samples": 0, "kg_attempts": 0, "kg_imports": 1}

```

* **Xuất lại backup từ database đích (lúc 01:21:36):**

```
docker compose -f compose.storage.yml run --rm -e "DATABASE_URL=$T" -v "D:\b2_backup:/backup" web python scripts/storage_admin.py backup --out /backup/target.private-backup.json

```

### 3.3. Bảng đối chiếu Nguồn và Đích

* **So sánh số lượng bản ghi:**

| Chỉ số bảng | Database Nguồn (`keyguard_local`) | Database Đích (`keyguard_restore` sau restore) | Trạng thái | 
| :--- | :---: | :---: | :--- | 
| `kg_documents` | 2 | 2 | Khớp | 
| `kg_samples` | 0 | 0 | Khớp (cùng rỗng) | 
| `kg_attempts` | 0 | 0 | Khớp (cùng rỗng) | 
| `kg_imports` | 0 | 1 | Khác, có giải thích bên dưới | 

* **Giải thích sự khác biệt ở `kg_imports`:** Theo `POSTGRES_STORAGE.md` của Nhật, bảng `kg_imports` lưu hash của nguồn đã nhập để tránh nhập lặp trùng. Ở database nguồn giá trị là `0` vì dữ liệu được tạo trực tiếp qua web. Ở database đích giá trị là `1` sau khi chạy `restore --apply`, nên tôi hiểu đây là bản ghi của lần nhập này. Đây là suy luận từ tài liệu và từ con số, tôi không đọc nội dung bảng.

* **So sánh mã băm SHA-256 của file backup:**

```
certutil -hashfile D:\b2_backup\source.private-backup.json SHA256
certutil -hashfile D:\b2_backup\target.private-backup.json SHA256

```

| Tệp tin backup | Kích thước | Mã băm SHA-256 | 
| :--- | :---: | :--- | 
| `source.private-backup.json` | 14,623 bytes | `987b719844d5beefdfb4b575578a36c8eb3020860c2f8af2ca9bc9e162b9d6ac` | 
| `target.private-backup.json` | 14,623 bytes | `987b719844d5beefdfb4b575578a36c8eb3020860c2f8af2ca9bc9e162b9d6ac` | 

* **Kết luận Phần 2:** Số dòng của ba bảng dữ liệu khớp, và hai mã băm SHA-256 trùng nhau (`987b719844d5beefdfb4b575578a36c8eb3020860c2f8af2ca9bc9e162b9d6ac`). Điều này cho thấy nội dung mà công cụ backup xuất ra từ database nguồn và từ database đích sau khi khôi phục giống hệt nhau. Kết luận chỉ áp dụng trong phạm vi những gì file backup chứa (xem mục 4).

## 4. Giới hạn kiểm thử

* **Quy mô dữ liệu thử nhỏ:** Chỉ kiểm thử với 1 tài khoản thử nghiệm (`test_b2_thu`, `kg_documents = 2`, `kg_samples = 0`), chưa kiểm thử với khối lượng dữ liệu lớn hoặc nhiều lượt thu mẫu gõ phím liên tiếp.

* **Hai bảng rỗng:** `kg_samples` và `kg_attempts` đều có 0 dòng ở cả nguồn và đích, nên việc "khớp" ở hai bảng này chưa chứng minh được sao lưu và khôi phục mẫu gõ phím hay nhật ký lượt thử.

* **Hash so file do chính công cụ xuất:** Hai mã băm là của hai file backup do cùng công cụ `storage_admin.py` xuất. Tôi chưa kiểm tra database ở mức từng byte, cũng chưa đọc nội dung từng bảng.

* **Môi trường cùng container/máy cục bộ:** Database nguồn (`keyguard_local`) và database đích (`keyguard_restore`) nằm chung trên một container PostgreSQL cục bộ trong Docker Desktop, chưa thực hiện khôi phục sang một máy chủ độc lập hoặc môi trường cloud thực tế (như Render).

* **Phạm vi restart:** Mới chỉ kiểm thử khởi động lại container ứng dụng `web` (`docker compose stop/up web`), chưa thực hiện kịch bản khởi động lại hoặc xóa/tạo lại container `db` để kiểm tra gắn kết Docker Volume.

## 5. Cam kết thực hiện

* Tôi tự tay thiết lập môi trường Docker, trực tiếp gõ và thực thi toàn bộ các lệnh kiểm thử, tự tạo dữ liệu thử và đối chiếu kết quả trên máy cá nhân.

* Trong quá trình thực hiện, tôi có sử dụng trợ lý AI để giải thích ý nghĩa các câu lệnh Docker/PostgreSQL, hỗ trợ gỡ lỗi thiếu bước `init` schema ban đầu, rà soát cấu trúc trình bày và chỉnh sửa một số câu chữ của biên bản này (các số liệu và kết quả lệnh là của tôi).