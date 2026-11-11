# Ghi chú thử nghiệm thực tế (task 2.6)

> Các chỗ có `[ĐIỀN: ...]` là thông tin chỉ người thử mới biết. Điền đúng sự thật rồi xóa dấu ngoặc.

## 1. Thiết lập

| Mục | Nội dung |
|---|---|
| Ngày thử | 10/11/2026 (giờ trong log theo UTC, giờ Việt Nam cộng 7 giờ) |
| Tài khoản đích | 1 tài khoản (mã ẩn danh `a7aa4e21`), đã đăng ký đủ 20 lần gõ |
| Nơi chạy web demo | [ĐIỀN: máy local / Render, nếu Render thì ghi gói miễn phí] |
| Thiết bị của chủ tài khoản | [ĐIỀN: laptop gì, hệ điều hành, trình duyệt] |
| Thiết bị của kẻ gian | [ĐIỀN: mỗi người dùng thiết bị riêng hay dùng chung, trình duyệt] |
| Mô hình và ngưỡng | Dùng cấu hình trong `models/model_config.json`, [ĐIỀN: xác nhận không đổi trong lúc thử] |
| Nguồn dữ liệu | `data/attempts.csv` do app tự ghi, chuyển thành `docs/live_test.csv` bằng `scripts/make_live_test.py` |

## 2. Cách tiến hành

- **Chủ tài khoản (genuine):** 24 lượt đăng nhập, chọn vai "Tôi là chủ tài khoản" trong chế độ thử nghiệm (`/login?test=1`), trong 1 buổi.
- **Kẻ gian (impostor):** 10 lượt từ 10 người khác nhau, mỗi người gõ 1 lượt đúng chuỗi `.tie5Roanl` rồi Enter vào tài khoản trên, chọn vai "Tôi đóng vai kẻ gian". Do gói Render miễn phí có thể bị ngủ hoặc reset, các bạn cùng hẹn thử trong một khoảng thời gian ngắn, nên các lượt dồn trong khoảng 2 phút.
- Mã người thử không được điền lúc thử, nên **số người (10) do nhóm khai theo trí nhớ**, không do app ghi lại.
- Lượt gõ sai câu không được ghi log. Lượt dùng thử ở chế độ "Dùng bình thường" (1 lượt) bị loại khỏi thống kê.
- Kẻ gian không nhập OTP: OTP chỉ hiện ở console server, mô phỏng tin nhắn gửi vào điện thoại chủ tài khoản.
- Hồ sơ tài khoản tự cập nhật mỗi khi lượt gõ được chấp nhận hoặc OTP đúng, nên hồ sơ của chủ có thể thay đổi nhẹ trong suốt buổi thử.

## 3. Kết quả

| Chỉ số | Kết quả |
|---|---|
| Số người đóng kẻ gian | 10 (theo trí nhớ, tester_id không được ghi) |
| Số lượt kẻ gian | 10 |
| Số lượt chủ tài khoản | 24 |
| FAR (kẻ gian được nhận ngay) | 0/10 = 0,0% |
| FRR (chủ bị yêu cầu OTP) | 6/24 = 25,0% |
| Chủ bị từ chối nhưng qua được OTP | 6/6 |
| Kẻ gian qua được OTP | 0/10 |

Lưu ý khi đọc kết quả:
- FAR và FRR trước OTP là chỉ số đo năng lực của mô hình nhịp gõ.
- Kết quả OTP là hệ quả thiết kế: kẻ gian không nhận được mã nên không thể vượt qua, chỉ cho thấy lớp xác minh thứ hai hoạt động, không dùng để so sánh mô hình.
- Mẫu nhỏ: FAR 0/10 có khoảng tin cậy 95% rộng (FAR thật có thể lên tới khoảng 28%).

## 4. Ẩn danh dữ liệu

Log không lưu tên tài khoản (chỉ mã băm `account_ref`), không lưu mẫu gõ của lượt thử và không lưu mã OTP. Không có tên, email hay số điện thoại người thử trong repo.

## 5. Hạn chế

- Mẫu nhỏ: 10 lượt kẻ gian, mỗi người chỉ 1 lượt.
- Một buổi thử, chưa kiểm tra chủ tài khoản đăng nhập ở các ngày khác nhau.
- Mã người thử không ghi lại, số người dựa trên lời khai của nhóm.
- Thiết bị và điều kiện gõ chưa được kiểm soát chặt, có thể khác với bộ dữ liệu CMU.
