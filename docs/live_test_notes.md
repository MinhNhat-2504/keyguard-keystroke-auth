# Ghi chú thử nghiệm thực tế (task 2.6)

## 1. Thiết lập (lần thử mới nhất)

| Mục | Nội dung |
|---|---|
| Ngày thử | 13/11/2026, từ 04:34 đến 04:54 giờ Việt Nam (log ghi giờ UTC: 12/11/2026 21:34:23 đến 21:54:10; giờ Việt Nam = UTC + 7 giờ) |
| Tài khoản đích | 1 tài khoản, đã đăng ký đủ 20 lần gõ (mã ẩn danh `account_ref`: `0e26d890`) |
| Nơi chạy web demo | Render (web chạy trên mạng), gói miễn phí, địa chỉ https://keyguard-keystroke-auth.onrender.com. |
| Thiết bị của người tổ chức (chủ tài khoản) | Laptop Asus, Windows, trình duyệt Chrome (không ghi phiên bản). |
| Thiết bị của kẻ gian | Laptop cá nhân của từng người tham gia, gồm các hãng Dell, HP và Asus, không ghi lại từng lượt gõ trên máy nào. Windows, trình duyệt Chrome. |
| Mô hình và ngưỡng | `keyguard/` và `models/model_config.json` đồng bộ theo bản `main` của TV1 (commit `674dfdc`), ngưỡng tau = 0,2720094565. Cấu hình không đổi trong lúc thử, và `keyguard/` cùng `models/` vẫn giống hệt `main` ở commit `d6218af` (kiểm tra bằng `git diff`). |
| Commit bàn giao | `d4a51f1` và `a2e7f5f` (tài liệu, ảnh, dữ liệu). Commit `3bcd919` sau đó chỉ đổi giao diện (3 template và `static/ui.css`); backend, mô hình và cấu hình không đổi. Live test chạy trước `3bcd919`. |
| Nguồn dữ liệu | `docs/attempts_original.csv` (xem mục 2b), chuyển thành `docs/live_test.csv` bằng `scripts/make_live_test.py` |

## 2. Cách tiến hành

- **Chủ tài khoản (genuine):** 23 lượt đăng nhập, chọn vai "Tôi là chủ tài khoản" trong chế độ thử nghiệm (`/login?test=1`), trong 1 buổi thử.
- **Kẻ gian (impostor):** 10 lượt, mỗi mã người thử đúng 1 lượt, gõ đúng chuỗi `.tie5Roanl` rồi Enter vào tài khoản trên, chọn vai "Tôi đóng vai kẻ gian".
- **Mã người thử:** người thử tự nhập vào ô "Mã người thử" trên trang (T01 đến T10, giữ nguyên như đã nhập, không sửa dữ liệu). Mã người thử không theo thứ tự thời gian. Script đếm được 10 mã khác nhau.
- Lượt gõ sai câu không được ghi log. Log lần này không có lượt nào ở chế độ "Dùng bình thường" (0 lượt bị loại khỏi thống kê).
- Mã người thử là mã được ghi trên log, do người thử tự nhập. Nhóm không có cách kiểm chứng độc lập rằng 10 mã là 10 người khác nhau.
- Kẻ gian không nhập OTP: mã OTP chỉ hiện ở console của máy chủ (mô phỏng tin nhắn gửi vào điện thoại chủ tài khoản), kẻ gian không xem được console nên không lấy được mã.
- Hồ sơ tài khoản tự cập nhật mỗi khi lượt gõ được chấp nhận hoặc OTP đúng, nên hồ sơ của chủ có thể thay đổi nhẹ trong suốt buổi thử.

## 2b. Nguồn gốc dữ liệu thử

- File gốc app ghi ra là `attempts.csv` trên máy chủ Render. File này được tải về qua trang quản trị ngay sau buổi thử.
- `docs/attempts_original.csv` là bản đã **qua trình soạn thảo (Excel)**; tên "original" chỉ là tên tệp trong repo, không có nghĩa là bản xuất nguyên byte từ máy chủ. Bản này có 38 dòng dữ liệu, không ngoặc kép, `confidence` dạng `0.xxxx`, xuống dòng kiểu CRLF.
- Dòng cuối của file từng bị xóa nhầm khi chỉnh. Dòng này được **khôi phục bằng tay** theo bản sao còn lại (`attempt_id` `f108bdf6a8fe`, `confidence` 0.0156). 37 dòng còn lại khớp 100% với bản sao đã qua Excel.
- Tệp `attempts.csv` và `attempts_fixed.csv` (nếu còn trong repo) là của đợt nộp trước: `attempts.csv` có `confidence` ngoài khoảng [0,1] do lỗi định dạng khi qua trình soạn thảo, nên không dùng làm nguồn. Nguồn dùng để tạo bảng kết quả là `attempts_original.csv`.
- Bản xuất nguyên byte từ máy chủ không còn được lưu, nên nguồn gốc dữ liệu chưa khép kín hoàn toàn; đây là giới hạn của nhóm.
- Không có dòng nào bị sửa theo phỏng đoán: không sửa giờ, không điền `tester_id` bù, không đổi vai.
- Kiểm tra lặp lại: chạy `python scripts/make_live_test.py docs/attempts_original.csv -o docs/live_test_check2.csv` rồi so với `docs/live_test.csv` bằng `fc.exe`. Kết quả (13/11/2026): không có khác biệt, 33/33 dòng khớp.

## 3. Kết quả

| Chỉ số | Kết quả |
|---|---|
| Số mã người thử đóng kẻ gian | 10 (T01, T02,..) |
| Số lượt kẻ gian | 10 |
| Số lượt chủ tài khoản | 23 |
| FAR (kẻ gian được nhận ngay) | 0/10 = 0,0% |
| FRR (chủ bị yêu cầu OTP) | 5/23 = 21,7% |
| Chủ bị từ chối nhưng qua được OTP | 5/5 |
| Kẻ gian nhập OTP | Không áp dụng (kẻ gian không có OTP, xem lưu ý đầu tiên bên dưới) |

Lưu ý khi đọc kết quả:
- **Về OTP của kẻ gian:** khi nhịp gõ không khớp, mã OTP chỉ được gửi tới chủ tài khoản (trong demo là hiện ở console của máy chủ), kẻ gian không có mã này nên không thể nhập đúng. Đây là hệ quả của thiết kế demo, không phải kết quả thí nghiệm: không có lượt nhập OTP nào của kẻ gian trong log, nên không có số liệu về việc kẻ gian đoán OTP.
- Mẫu nhỏ: FAR 0/10 có khoảng tin cậy 95% rộng (FAR thật có thể lên tới khoảng 28%), nên không chứng minh FAR bằng 0. FRR 5/23 có khoảng tin cậy 95% (Wilson) khoảng 10% đến 42%.

## 4. Ẩn danh dữ liệu

Log không lưu tên tài khoản (chỉ mã băm `account_ref`), không lưu mẫu gõ của lượt thử và không lưu mã OTP. Mã người thử là mã tự đặt (T01, T02, ...), không chứa tên, email hay số điện thoại. Không có thông tin cá nhân của người thử trong repo.

## 5. Hạn chế

- Mẫu nhỏ: 10 lượt kẻ gian, mỗi mã chỉ 1 lượt. 10 mã là mã được ghi, không được kiểm chứng là 10 người độc lập.
- `attempts_original.csv` đã qua trình soạn thảo và có một dòng khôi phục bằng tay (xem mục 2b).
- Một buổi thử, chưa kiểm tra chủ tài khoản đăng nhập ở các ngày khác nhau.
- Thiết bị và điều kiện gõ chưa được kiểm soát chặt, có thể khác với bộ dữ liệu CMU.

## 6. Lần thử trước (10/11/2026, ngưỡng cũ)

Giữ lại để đối chiếu với báo cáo của TV1 nếu báo cáo còn dùng số này:
- Ngưỡng tau = 0,2503148687 (`models/model_config.json` bản cũ), mã người thử không được ghi.
- 24 lượt chủ (6 lượt bị yêu cầu OTP, FRR 6/24 = 25,0%), 10 lượt kẻ gian (FAR 0/10).
- Bộ log và CSV của lần này đã được thay bằng lần thử mới ở mục 1–3.
