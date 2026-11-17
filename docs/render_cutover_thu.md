# Biên bản chuyển Render sang PostgreSQL (Neon) — Thư thực hiện

> Khung và phần tổng hợp bằng chứng do Claude hỗ trợ soạn từ kết quả Thư báo lại khi thao tác (Thư tự chạy lệnh, tự thao tác trên Render/DevTools). Phần "Giải thích bằng lời của Thư" do Thư tự viết.
> KHÔNG ghi DATABASE_URL, khóa admin, mật khẩu hay token ở bất kỳ đâu trong file này. Che secret trong ảnh.
> Ô còn `[điền]` là chưa có số liệu hoặc chưa làm xong; không điền khi chưa có bằng chứng thật.

- Người thao tác: Thư (tài khoản vận hành Render)
- Ngày giờ bắt đầu: 16/11/2026, khoảng 19:14 (tải backup đầu tiên); deploy xong 19:39 (giờ VN)
- Dịch vụ: keyguard-keystroke-auth (repo MinhNhat-2504/keyguard-keystroke-auth), service ID srv-dbko82nb9u1s738099kg
- Full SHA commit Nhật đã review (nhánh storage/postgres-local): b0bd22e13fd4f1c56ca2e638936daaa5f0767e39
- Khoảng dừng thu/test đã chốt: Nhật đề xuất 20:00–22:00 ngày 16/11; thực tế Thư deploy sớm hơn (xem "Sự cố"). Hạn hoàn tất D: trước bảo trì Render 09:00 18/11/2026.

## B. Trước khi chuyển
| # | Việc | Bằng chứng (ảnh/lệnh/giá trị) | Xong |
|---|---|---|---|
| B1 | Nhật push đúng nhánh; remote có SHA | `git fetch` rồi kiểm tra: origin/storage/postgres-local = b0bd22e13fd4f1c56ca2e638936daaa5f0767e39 (khớp SHA Nhật gửi) | [x] |
| B2 | Vào đúng dịch vụ và URL | `evid/B2_render_services` (render services, đúng service keyguard-keystroke-auth) | [x] |
| B3 | Chốt khoảng dừng; mẫu đang chờ đã xác nhận | Nhật chốt cửa sổ 20:00–22:00 16/11; [điền: xác nhận không còn mẫu đang chờ] | [ ] |
| B4 | Backup Render nguyên byte + checksum; đối chiếu Neon | `D:\backup_keyguard\keyguard_render_truoc_deploy.zip`, 109.974 byte, SHA-256 `b61c118b243a88b8b45f2849d2c676722189af6d31d34a23f8c3726abc034c5d`, tải 19:14 16/11 bằng khóa admin cũ. 601 dòng mẫu; P01 SHA khớp bản trong repo; 4 lượt attempts khớp log OTP test 13/11 (`fc.exe`: không khác biệt). | [x] |
| B5 | Tài khoản/profile/OTP; phương án tài khoản cũ; backup Neon | [điền: Nhật chốt gì, ngày giờ] (Nhật quyết định đăng ký tài khoản mới) | [ ] |

## C. Cấu hình và deploy
| # | Việc | Bằng chứng | Xong |
|---|---|---|---|
| C1 | Đặt KEYGUARD_STORAGE=postgres, DATABASE_URL, khóa admin; giữ biến cũ | Ảnh Environment (giá trị đã che): KEYGUARD_STORAGE=postgres, DATABASE_URL (Neon, TLS), KEYGUARD_ADMIN_KEY (mới), KEYGUARD_VERIFY_LIMIT=60, PYTHON_VERSION=3.11.9 | [x] |
| C2 | Save only; chọn đúng nhánh/commit; deploy cả commit | **Không đúng quy trình:** Thư chọn "Save, rebuild, and deploy" thay vì "Save only" (19:35), rồi đổi nhánh 19:37. Xem "Sự cố". Kết quả cuối: nhánh storage/postgres-local, commit b0bd22e. | [x] (có sự cố) |
| C3 | Dockerfile có collection_quality.py hoặc Python build đúng | Render build Python 3.11.9 (PYTHON_VERSION), Gunicorn `app:app --workers 1 --threads 4`; [điền: xác nhận với Nhật nếu cần] | [ ] |
| C4 | Events báo Live: full deploy SHA, giờ, trạng thái; khớp SHA đã review | `render deploys list`: dep-dbtfi9utlv9c73f7oqd0, tạo 12:37:59Z, xong 12:39:15Z (19:37–19:39 VN), trạng thái Live, commit b0bd22e13fd4f1c56ca2e638936daaa5f0767e39. Khớp SHA đã review: **Có**. Ảnh: `C2_C4_events_branch_updated_b0bd22e_live`, `C4_render_deploys_list_full_SHA_b0bd22e`. | [x] |
| C5 | Tải lại collector; /static/pending-sample.js và /static/readability.css trả 200 | `curl -I` cả hai URL trả HTTP 200; trang collector tải lại có `pending-sample.js`, `readability.css` trong Network | [x] |

## D. Kiểm ghi dữ liệu
Người tham gia test riêng: **P16** (tên nhập MAY01), không dùng cho nghiên cứu, loại khỏi dữ liệu huấn luyện/đánh giá.

| # | Việc | Bằng chứng | Xong |
|---|---|---|---|
| D1 | Mẫu test: timestamp UTC, metadata version3, request_id, hash | P16/MAY01, rep 1, request_id `f69882c2f4bf0235bd4a581538f6eebe`, response `replayed:false`. Ảnh: `D1_payload_P16_MAY01_request_f69882c2`, `D1_response_rep1_replayed_false`. [điền: timestamp UTC, metadata version3 và hash nếu có trong payload] | [x] (cần bổ sung chi tiết payload) |
| D2 | Gửi lại đúng request_id+payload: replayed=true, count không tăng; sửa payload cùng ID → 409 | (a) Mẫu 3, request `5b68d3d7…6718`: lần đầu `replayed:false`, gửi lại bằng Copy as fetch → `replayed:true`, cùng rep, count không tăng. Ảnh `D2a_*`. (b) Sửa payload cùng request_id → HTTP 409 `request_id_payload_conflict`. Ảnh `D2b_409_conflict.png`, `D2b_response_request_id_payload_conflict.png`. | [x] |
| D3 | Ngắt kết nối / gửi lại / tải lại cùng tab: mẫu và request_id khớp | DevTools Offline: gửi mẫu 6 thất bại 3 lần (`Failed to fetch`), trang hiện "Gửi lại mẫu đang chờ"; bỏ Offline, gửi lại thành công cùng request_id `f82881fd132cc74cefd3c10fb9967199` → rep 6, count 6 (không nhân đôi). Trước đó đã gửi rep 4 (`37ac9f07b212b145ae1c7b7a9640abe9`) và rep 5 (`f20ecd209fde41599da1e22525ee25b2`). Ảnh `D3_1_offline_failed_network_console`, `D3_2_trang_cho_gui_lai`, `D3_3_payload_dong_loi_request_f82881fd`. Lưu ý: log Network bị mất khi tải lại trang nên ảnh D3 gồm cả ảnh chụp lại cùng request_id (xem "Sự cố"). | [x] |
| D4 | Restart app Render (không restart DB): tài khoản test, tiến độ, replay vẫn đúng | Trước restart (17/11 17:58): P16 6 mẫu, tổng 607, attempts 4. Restart bằng `render restart srv-dbko82nb9u1s738099kg` lúc 18:00; Events: "Service restarted by you", commit b0bd22e vẫn Live, **không có deploy mới**. Sau restart (18:06): P16 6, tổng 607 (giống hệt). Gửi mẫu mới → rep 7, count 7 (đếm tiếp từ 6), request `a0d58fa4e82a081e8d18954f6dd67ee8`, `replayed:false`; gửi lại cùng request → `replayed:true`, rep 7, count 7. Stats cuối (18:19): P16 7 mẫu (1 phiên), tổng 608 (P01 41 + P02–P15 14×40 + P16 7), attempts 4. Ảnh: `D4_*`, `stats_truoc_restart.txt`, `stats_sau_restart.txt`, `stats_cuoi_D4.txt`. | [x] |
| D5 | Backup sau chuyển; restore vào DB rỗng khác; đối chiếu số lượng/nội dung/hash | Đã làm (17/11 18:22): tải backup `D:\backup_keyguard\keyguard_sau_D4.zip`, 114.062 byte, SHA-256 `2bddbb6478eb437aa132118d920033bab2a2e7243b72118c07ecf163cd0078a2`; giải nén có 16 file `Pxx.jsonl` (P01 41, P02–P15 mỗi file 40, P16 7) = 608 dòng, khớp stats cuối. **Chưa làm:** Nhật restore vào DB Neon rỗng riêng và đối chiếu số lượng/nội dung/hash: [điền sau]. | [ ] |
| D6 | Lưu bằng chứng đã che secret; xong mới mở lại thu dữ liệu | Ảnh/text trong `docs/screenshots/` (danh sách ở trên); [điền sau D5]. Chưa mở lại thu dữ liệu cho tới khi D5 xong. | [ ] |

## Giải thích bằng lời của Thư
(Thư tự viết, ngắn gọn bằng lời của mình)
- **Vì sao dùng Save only trước khi deploy:** Để lưu cấu hình biến môi trường (như `KEYGUARD_STORAGE=postgres`, `DATABASE_URL`) trước mà chưa kích hoạt deploy ngay trên nhánh code cũ. Nhờ vậy em có thời gian đổi sang đúng nhánh `storage/postgres-local` (commit `b0bd22e`) rồi mới deploy một lần cho khớp giữa code mới và cấu hình mới, tránh chạy nhầm bản code cũ.
- **Vì sao gửi lại cùng request_id thì count không tăng:** Vì hệ thống kiểm tra tính trùng lặp (idempotency) theo `request_id` và nội dung payload. Nếu nhận lại đúng `request_id` và payload đã lưu trước đó, server chỉ trả về kết quả cũ (`replayed: true`) chứ không ghi thêm bản ghi mới vào database, giúp tránh nhân đôi dữ liệu khi mạng chập chờn hoặc người dùng bấm gửi lại.
- **Vì sao restart app chứ không restart database:** Để kiểm chứng rằng dữ liệu thực sự nằm tách biệt bên ngoài ứng dụng web (trên Neon) chứ không ăn theo vòng đời của server app. Khi chỉ khởi động lại service app trên Render mà database vẫn giữ nguyên, mọi tài khoản, tiến độ mẫu (`count`) và trạng thái chống trùng lặp (`request_id`) không bị reset.
- **Vì sao Render free tier mất dữ liệu và PostgreSQL ngoài (Neon) giải quyết thế nào:** Render gói miễn phí dùng ổ đĩa tạm thời (ephemeral disk), nên mỗi lần app deploy lại, restart hoặc ngủ đông rồi bật lại thì file lưu cục bộ (file JSON) sẽ bị xóa sạch về trạng thái gốc của repo. Chuyển sang dùng PostgreSQL trên Neon giúp tách phần lưu trữ ra một dịch vụ database độc lập bên ngoài, đảm bảo dữ liệu luôn được giữ an toàn qua mọi lần app khởi động lại hay cập nhật code.

## Sự cố và giới hạn
- **19:35 16/11 chọn sai nút:** lưu biến môi trường bằng "Save, rebuild, and deploy" thay vì "Save only", nên Render deploy sớm (commit e396685 Live lúc 19:36), trước cửa sổ 20:00 đã chốt. Chưa mất dữ liệu: backup 19:14 và dữ liệu trong repo giống hệt (601 mẫu).
- **19:37 đổi nhánh sớm** sang storage/postgres-local; deploy b0bd22e Live lúc 19:39. Hai bước này vẫn nằm trong thời gian chưa mở thu dữ liệu, không có người tham gia thật gửi mẫu trong khoảng đó.
- **Mẫu test thêm:** P16 có 7 mẫu (rep 2, 4, 5, 7 là mẫu thử thêm trong lúc kiểm D3/D4); P16 là người test, loại khỏi dữ liệu nghiên cứu. Tổng 608 = 601 + 7.
- **Gõ nhầm khóa khi tải/ xem stats:** vài lần nhập chữ giữ chỗ hoặc biến trống nên server trả 404 (file 61 byte `{"message":"Không tìm thấy.","success":false}`); chạy lại với khóa đúng thì thành công. Không ảnh hưởng dữ liệu.
- **Mất log Network khi tải lại trang (D3):** một số ảnh D3 chụp lại từ lần gửi cùng request_id; nội dung request_id/rep/count khớp response thật.
- **Lộ khóa trong khi làm:** khóa admin và chuỗi cấu hình đã dán vào chat/terminal; **cần Nhật đổi khóa admin và mật khẩu Neon sau khi xong D**.
- **Giới hạn:** tab cũ dùng frontend cũ sẽ nhận 400 (thiếu device_id/request_id); P10 rep 29 trùng (601→597 mẫu sạch) do Nhật quyết định; D5 (restore) chưa làm lúc lập biên bản này.
- **Công cụ hỗ trợ:** Claude hướng dẫn lệnh và soạn khung/tổng hợp; mọi thao tác trên Render/DevTools và số liệu do Thư chạy và báo lại.