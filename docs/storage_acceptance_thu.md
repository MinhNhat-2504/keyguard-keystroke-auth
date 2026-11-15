# Biên bản kiểm chứng bảo toàn dữ liệu PostgreSQL (B2)

* **Người thực hiện:** Thư
* **Thời gian thực hiện:** Rạng sáng ngày 15/11/2026 (từ 00:55 đến 01:22) và bổ sung chiều ngày 15/11/2026 (từ 15:07 đến 15:18)

## 1. Môi trường thực hiện

* **Hệ điều hành:** Windows (Docker Desktop)
* **Phiên bản Docker:** `Docker version 29.3.0, build 5927d80`
* **Database & Web Image:** `postgres:17-alpine` và `python:3.11-slim`
* **Nhánh Git thực hiện:** `storage/postgres-local` (cập nhật từ `origin/storage/postgres-local`, commit `cee1cbb`)

## 2. Phần 1: Khởi động PostgreSQL, tạo dữ liệu và kiểm chứng qua Restart

### 2.1. Khởi động dịch vụ và xử lý lỗi thiếu schema ban đầu

* Lúc **00:55:03**, tôi khởi động container PostgreSQL (`db`) và build image `web`:

```powershell
docker compose -f compose.storage.yml up -d db
docker compose -f compose.storage.yml build web
```

* Lúc **00:56:46**, tôi chạy `docker compose -f compose.storage.yml up -d web` nhưng container `web` tự thoát ngay sau khi khởi động. Kiểm tra log lúc **00:59:13** (`docker compose -f compose.storage.yml logs web`) phát hiện lỗi do chưa khởi tạo bảng dữ liệu:

```text
RuntimeError: PostgreSQL schema not ready; run storage_admin.py init
```

* Lúc **01:00:54**, tôi chạy lệnh khởi tạo schema và khởi động lại dịch vụ `web` thành công (mở cổng cục bộ `127.0.0.1:56900`):

```powershell
docker compose -f compose.storage.yml run --rm web python scripts/storage_admin.py init
docker compose -f compose.storage.yml up -d web
docker compose -f compose.storage.yml port web 8000
```

Kết quả khởi tạo:

```text
PostgreSQL schema initialized; no legacy data imported
```

### 2.2. Tạo tài khoản thử và đối chiếu trước/sau khi Restart ứng dụng Web

* Sau khi truy cập giao diện web qua cổng `56900`, tôi tiến hành đăng ký mới **1 tài khoản thử nghiệm** có tên đăng nhập là `test_b2_thu` (chưa thu mẫu trên trang collector).

* **Trước khi restart (lúc 01:07:21):** Kiểm tra trạng thái database bằng lệnh `status`:

```powershell
docker compose -f compose.storage.yml run --rm web python scripts/storage_admin.py status
```

Kết quả:

```json
{"kg_documents": 2, "kg_samples": 0, "kg_attempts": 0, "kg_imports": 0}
```

Đồng thời gọi API `http://127.0.0.1:56900/api/check-username?username=test_b2_thu` trên trình duyệt (ảnh chụp màn hình lưu tại `docs/screenshots/b2_check_username_truoc.jpg`):

```json
{"available":false,"success":true,"username":"test_b2_thu"}
```

*(Ghi chú: theo `POSTGRES_STORAGE.md` của Nhật, bảng `kg_samples` lưu các mẫu thu từ collector, còn bảng `kg_documents` lưu sổ đăng ký tài khoản/người tham gia, hồ sơ nhịp gõ và thử thách OTP. Vì chưa đọc payload từng dòng nên tôi không khẳng định cụ thể nội dung 2 tài liệu trong `kg_documents` chỉ từ số đếm.)*

* **Thực hiện Restart container `web` (từ 01:08:06 đến 01:08:38):** Tôi chỉ dừng và khởi động lại container ứng dụng `web` (giữ nguyên container `db` và volume dữ liệu):

```powershell
docker compose -f compose.storage.yml stop web
docker compose -f compose.storage.yml up -d web
docker compose -f compose.storage.yml port web 8000
```

Sau khi khởi động lại, container `web` chạy trên cổng mới `127.0.0.1:62179`.

* **Sau khi restart (lúc 01:09:48):** Kiểm tra lại trạng thái database bằng lệnh `status`:

```powershell
docker compose -f compose.storage.yml run --rm web python scripts/storage_admin.py status
```

Kết quả:

```json
{"kg_documents": 2, "kg_samples": 0, "kg_attempts": 0, "kg_imports": 0}
```

Gọi lại API trên cổng mới `http://127.0.0.1:62179/api/check-username?username=test_b2_thu` trên trình duyệt (ảnh chụp màn hình lưu tại `docs/screenshots/b2_check_username_sau.jpg`):

```json
{"available":false,"success":true,"username":"test_b2_thu"}
```

* **Kết luận Phần 1:** Dữ liệu tài khoản `test_b2_thu` và trạng thái hệ thống trước và sau khi khởi động lại ứng dụng `web` hoàn toàn giống nhau (`kg_documents: 2` và `available: false`), chứng minh dữ liệu được lưu bền vững trong PostgreSQL thay vì mất đi theo bộ nhớ tiến trình web.

## 3. Phần 2: Kiểm chứng Backup và Restore sang Database rỗng

### 3.1. Quy tắc đối chiếu

1. **Đối chiếu số lượng bản ghi:** So sánh số dòng từng bảng dữ liệu (`kg_documents`, `kg_samples`, `kg_attempts`) giữa database nguồn (`keyguard_local`) và database đích (`keyguard_restore`) thông qua công cụ `storage_admin.py status`. Bảng `kg_imports` được loại khỏi phép so sánh vì đây là bảng ghi chú việc nhập (xem giải thích ở 3.3).
2. **Đối chiếu nội dung (Hash SHA-256):** Xuất file backup từ database nguồn (`source.private-backup.json`) và xuất lại file backup từ database đích sau khi restore (`target.private-backup.json`), sau đó tính mã băm SHA-256 bằng `certutil`. Hai mã băm giống nhau nghĩa là hai file có nội dung giống hệt nhau. *(Các file `.private-backup.json` được lưu ở thư mục cục bộ `D:\b2_backup`, không đưa lên GitHub).*

### 3.2. Các lệnh thực hiện Backup và Restore

* **Ghi số liệu nguồn và xuất backup từ database nguồn (lệnh `status` nguồn lúc 01:14:30 và lệnh `backup` lúc 01:15:04):**

```powershell
docker compose -f compose.storage.yml run --rm web python scripts/storage_admin.py status
mkdir D:\b2_backup
docker compose -f compose.storage.yml run --rm -v "D:\b2_backup:/backup" web python scripts/storage_admin.py backup --out /backup/source.private-backup.json
```

Kết quả:

```text
{"kg_documents": 2, "kg_samples": 0, "kg_attempts": 0, "kg_imports": 0}
Private backup written; includes accounts/profiles/challenges. Keep out of GitHub.
```

* **Tạo database đích rỗng `keyguard_restore`, định nghĩa biến kết nối `$T` và khởi tạo schema (từ 01:16:34 đến 01:20:36):**

```powershell
docker compose -f compose.storage.yml exec db psql -U postgres -c "CREATE DATABASE keyguard_restore;"
docker compose -f compose.storage.yml exec db psql -U postgres -d keyguard_restore -c "\dt"
$T = "postgresql://postgres:<mật-khẩu>@db:5432/keyguard_restore"
docker compose -f compose.storage.yml run --rm -e "DATABASE_URL=$T" web python scripts/storage_admin.py init
docker compose -f compose.storage.yml run --rm -e "DATABASE_URL=$T" web python scripts/storage_admin.py status
```

Kết quả kiểm tra database đích trước khi restore (hoàn toàn rỗng):

```text
Did not find any relations.
PostgreSQL schema initialized; no legacy data imported
{"kg_documents": 0, "kg_samples": 0, "kg_attempts": 0, "kg_imports": 0}
```

* **Chạy thử (Dry-run) và nạp dữ liệu (Restore --apply) vào database đích (từ 01:20:51 đến 01:21:29):**

```powershell
docker compose -f compose.storage.yml run --rm -e "DATABASE_URL=$T" -v "D:\b2_backup:/backup" web python scripts/storage_admin.py restore --source /backup/source.private-backup.json
docker compose -f compose.storage.yml run --rm -e "DATABASE_URL=$T" -v "D:\b2_backup:/backup" web python scripts/storage_admin.py restore --source /backup/source.private-backup.json --apply
docker compose -f compose.storage.yml run --rm -e "DATABASE_URL=$T" web python scripts/storage_admin.py status
```

Kết quả:

```text
Dry-run: backup parsed, not imported; --apply validates references and writes only to empty target
imported
{"kg_documents": 2, "kg_samples": 0, "kg_attempts": 0, "kg_imports": 1}
```

* **Xuất lại backup từ database đích (lúc 01:21:36):**

```powershell
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

```powershell
certutil -hashfile D:\b2_backup\source.private-backup.json SHA256
certutil -hashfile D:\b2_backup\target.private-backup.json SHA256
```

| Tệp tin backup | Kích thước | Mã băm SHA-256 |
| :--- | :---: | :--- |
| `source.private-backup.json` | 14,623 bytes | `987b719844d5beefdfb4b575578a36c8eb3020860c2f8af2ca9bc9e162b9d6ac` |
| `target.private-backup.json` | 14,623 bytes | `987b719844d5beefdfb4b575578a36c8eb3020860c2f8af2ca9bc9e162b9d6ac` |

* **Kết luận Phần 2:** Số dòng của ba bảng dữ liệu khớp, và hai mã băm SHA-256 trùng nhau (`987b719844d5beefdfb4b575578a36c8eb3020860c2f8af2ca9bc9e162b9d6ac`). Điều này cho thấy nội dung mà công cụ backup xuất ra từ database nguồn và từ database đích sau khi khôi phục giống hệt nhau. Kết luận chỉ áp dụng trong phạm vi những gì file backup chứa (xem mục 4).

## 4. Giới hạn kiểm thử (đợt chạy đầu)

* **Quy mô dữ liệu thử nhỏ:** Ở đợt chạy đầu chỉ kiểm thử với 1 tài khoản thử nghiệm (`test_b2_thu`, `kg_documents = 2`, `kg_samples = 0`), chưa có dữ liệu thu từ trang collector.
* **Hai bảng rỗng:** `kg_samples` và `kg_attempts` đều có 0 dòng ở cả nguồn và đích ở đợt đầu, nên việc "khớp" ở hai bảng này chưa chứng minh được sao lưu và khôi phục mẫu gõ phím collector hay nhật ký lượt thử. *(Phần kiểm chứng mẫu collector qua restart đã được bổ sung ở Mục 5 bên dưới).*
* **Hash so file do chính công cụ xuất:** Hai mã băm là của hai file backup do cùng công cụ `storage_admin.py` xuất. Tôi chưa kiểm tra database ở mức từng byte, cũng chưa đọc nội dung từng bảng.
* **Môi trường cùng container/máy cục bộ:** Database nguồn (`keyguard_local`) và database đích (`keyguard_restore`) nằm chung trên một container PostgreSQL cục bộ trong Docker Desktop, chưa thực hiện khôi phục sang một máy chủ độc lập hoặc môi trường cloud thực tế (như Render).
* **Phạm vi restart:** Mới chỉ kiểm thử khởi động lại container ứng dụng `web` (`docker compose stop/up web`), chưa thực hiện kịch bản khởi động lại hoặc xóa/tạo lại container `db` để kiểm tra gắn kết Docker Volume.

## 5. Bổ sung ngày 15/11/2026: đối chiếu mẫu collector qua restart

*Mục này thêm sau khi nghiệm thu B2 lần đầu, để đối chiếu mẫu thu từ trang collector qua restart. Số liệu và kết quả ở các mục 1–4 phía trên giữ nguyên; chỉ cập nhật dòng thời gian thực hiện ở đầu file và đánh lại số mục Cam kết thành mục 6.*

Mã `P01` dưới đây là mã thử trên database local, không liên quan đến participant P01 trong `data/collected/`. Phần này chạy trên nhánh `storage/postgres-local`, dùng lại database của lần chạy trước.

### 5.1. Trước restart

* Trên trang collector (cổng `53941`, lấy từ lệnh `docker compose port web 8000`), tôi gõ 3 lượt cho mã `P01`, phiên 1. Trang báo `"Phiên 1: đã có 3/40 mẫu"` (ảnh `docs/screenshots/bb2_samples_truoc.png`; ảnh chỉ chụp phần trang, không có thanh địa chỉ).
* Kiểm tra trạng thái database (`status`):

```powershell
docker compose -f compose.storage.yml run --rm web python scripts/storage_admin.py status
```

Kết quả:

```json
{"kg_documents": 3, "kg_samples": 3, "kg_attempts": 0, "kg_imports": 0}
```

* `kg_documents` tăng từ 2 lên 3 sau khi dùng collector; tôi chưa đọc nội dung nên chưa xác định document mới là gì.
* Backup `samples_truoc.private-backup.json` (ghi lúc `15:07`): **19,082 bytes**, SHA-256:

```text
9759af363442ab9dbaf44ff9655ad4221ba8162f65edf6726e4feb95dc68ac3c
```

### 5.2. Restart (15:08:10 đến 15:08:38)

```powershell
docker compose -f compose.storage.yml stop web
docker compose -f compose.storage.yml up -d web
docker compose -f compose.storage.yml port web 8000
```

* Cổng đổi từ `53941` sang `62354`. Lệnh `up -d web` chạy thêm lần nữa lúc `15:08:38` báo container đang `Running`, không làm gì thêm.

### 5.3. Sau restart

* Mở trang ở cổng mới (`62354`), trang tự hiện mã `P02`; tôi dùng ô `"Mã đã có"` quay lại `P01` và thấy `"đã có 3/40 mẫu"` (ảnh `docs/screenshots/b2_samples_sau.png).
* Kiểm tra lại `status` (cùng lệnh như trước):

```json
{"kg_documents": 3, "kg_samples": 3, "kg_attempts": 0, "kg_imports": 0}
```

* Backup `samples_sau.private-backup.json` (ghi lúc `15:17`): **19,134 bytes**, SHA-256:

```text
3bbc9053f1978de76844c033e3a99281118793bb33a7aca033852603976b0a00
```

### 5.4. Kết quả đối chiếu

* Số bản ghi trong `kg_samples` (3 mẫu) và tiến độ `P01`, phiên 1 (`3/40`) giống hệt trước restart.
* **Hai hash toàn file không trùng**, kích thước chênh **52 bytes**.
* So sánh nội dung bằng Python: chỉ lệch đúng khóa `/documents/participants.json/P02`; toàn bộ phần còn lại của backup, gồm phần `samples` (3 mẫu của `P01`) và các khóa khác, trùng khớp hoàn toàn (hai backup giống hệt nhau sau khi bỏ `P02`). Phân tích phụ sau đó cho kết quả:

```text
P02 trong truoc: False | P02 trong sau: True
Sau khi bo P02 khoi file sau, hai backup giong het: True
```

* Phép loại `P02` để so phần còn lại là phân tích phụ tôi làm sau khi thấy hash lệch, không phải quy tắc đặt trước.

### 5.5. Kết luận và giới hạn phần bổ sung

* Dữ liệu mẫu và hồ sơ của `P01` được giữ nguyên qua restart `web`. Hash toàn file khác nhau vì có thêm mục `P02` trong sổ người tham gia, do trang cấp mã mới khi tôi mở lại. Việc `P02` do trang tự cấp khi tải là nhận định từ quan sát của tôi và từ khớp 52 bytes, tôi chưa đọc mã nguồn để xác nhận.
* **Giới hạn:** chỉ 3 mẫu thử; so sánh làm trên nội dung JSON của backup, không phải từng byte trong database; chỉ restart `web`, không restart `db`. Hai file backup nằm ngoài repo (`D:\b2_backup`).

## 6. Cam kết thực hiện

* Tôi tự tay thiết lập môi trường Docker, trực tiếp gõ và thực thi toàn bộ các lệnh kiểm thử ở cả hai đợt (rạng sáng và chiều ngày 15/11/2026), tự tạo dữ liệu thử và đối chiếu kết quả trên máy cá nhân.
* Trong quá trình thực hiện, tôi có sử dụng trợ lý AI để giải thích ý nghĩa các câu lệnh Docker/PostgreSQL, hỗ trợ gỡ lỗi thiếu bước `init` schema ban đầu, rà soát cấu trúc trình bày và chỉnh sửa một số câu chữ của biên bản này (các số liệu và kết quả lệnh là của tôi).

* Ở đợt chiều (mục 5), trợ lý AI hướng dẫn trình tự lệnh, gợi ý khung trình bày và rà soát câu chữ; tôi tự chạy các lệnh trên máy, tự gõ 3 mẫu trên trang collector, tự chụp ảnh và ghi số liệu từ terminal của mình.