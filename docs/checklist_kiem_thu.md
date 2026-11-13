# Checklist kiểm thử toàn luồng (task 2.5)

Mục đích: ghi mỗi ca thử, kết quả mong đợi và bằng chứng. Ca ghi "Chưa thử" chưa được chạy. Ngày và giờ ghi theo giờ Việt Nam (log máy chủ ghi UTC, giờ VN = UTC + 7).

Cấu hình liên quan (theo `app.py`): OTP có hiệu lực 5 phút, tối đa 3 lần nhập sai mỗi mã. Đăng ký cần đủ 20 lần gõ.

Tất cả ảnh dưới đây được chụp lại ngày 13/11/2026. Phiên bản code: ảnh chụp trên bản chạy của nhóm, không gắn với một commit xác định; các commit chứa ảnh và tài liệu là `d4a51f1` và `a2e7f5f`. Commit `3bcd919` sau đó chỉ đổi bố cục giao diện, chức năng không đổi. Mỗi ảnh dưới đây nằm trong `docs/screenshots/`.

## 1. Ca thử và bằng chứng

| # | Ca thử | Cách thử | Mong đợi | Ảnh (docs/screenshots/) | Thực tế | Ngày/giờ chụp |
|---|---|---|---|---|---|---|
| 1 | Mở trang thu dữ liệu | Vào trang collector | Hiện mã người tham gia, ô gõ câu cố định | `trang thu dữ liệu.jpg` | Trang KeyGuard Data Collector hiện mã định danh `P16`, chọn Phiên 1 (`0/40 mẫu`) và ô nhập câu cố định `.tie5Roanl`. | 13/11/2026 |
| 2 | Đăng ký, đang gõ, chưa đủ 20 lần | Gõ ít hơn 20 lần | Hiện tiến độ n/20, chưa có nút nộp | `tiến độ đăng ký.jpg` | Hiện `Tiến độ: Lần 5 / 20`, thông báo xanh "Thành công! Tiếp tục lần tiếp theo.", chưa có nút nộp. | 13/11/2026 |
| 3 | Đăng ký đủ 20 lần | Gõ đủ 20 lần | Đăng ký thành công | `đăng ký thành công.jpg` | Màn hình báo "Hoàn tất! Đăng ký tài khoản vidu thành công!" kèm liên kết tới trang Đăng nhập. | 13/11/2026 |
| 4 | Đăng ký trùng tên tài khoản | Đăng ký lại tên đã có | Báo trùng, không ghi đè hồ sơ | `tài khoản đăng ký bị trùng.jpg` | Nhập tên `vidu` đã có, hệ thống báo lỗi đỏ: "Tên tài khoản đã tồn tại, vui lòng chọn tên khác." và giữ nguyên hồ sơ cũ. | 13/11/2026 |
| 5 | Đăng nhập được chấp nhận | Chủ gõ đúng nhịp | Hiện điểm tin cậy, chấp nhận | `đăng nhập thành công.jpg` | Tài khoản `vidu` gõ khớp nhịp: hiện thông báo xanh "Đăng nhập thành công! Nhịp gõ khớp. Hồ sơ đã được cập nhật. Điểm tin cậy: 75.2%". | 13/11/2026 |
| 6 | Đăng nhập bị yêu cầu OTP | Gõ lệch nhịp | Không chấp nhận ngay, yêu cầu OTP | `xác minh OTP.jpg` | Chủ tài khoản gõ sai nhịp, hệ thống không chấp nhận ngay và hiện ô nhập OTP. | 13/11/2026 |
| 7 | Kẻ gian bị yêu cầu OTP | Người khác gõ vào tài khoản (vai kẻ gian) | Không chấp nhận ngay, yêu cầu OTP | `yêu cầu mã OTP kẻ gian.jpg` | Vai kẻ gian, mã người thử T01: nhịp gõ không khớp (điểm tin cậy 0,1%), không chấp nhận ngay, hiện ô nhập OTP. | 13/11/2026 |
| 8 | OTP đúng | Nhập đúng mã từ console máy chủ | Đăng nhập thành công, hồ sơ cập nhật | `xác minh OTP thành công.jpg` | Nhập đúng mã OTP, hệ thống xác nhận đăng nhập thành công và cập nhật hồ sơ. | 13/11/2026 |
| 9 | OTP sai | Nhập mã sai | Báo sai, hiện số lần còn lại | `xác minh OTP thất bại.jpg` | Nhập mã OTP không khớp, hệ thống từ chối và báo lỗi đỏ kèm số lần thử còn lại. | 13/11/2026 |
| 10 | OTP bị khóa (sai quá số lần) | Nhập sai liên tiếp trên cùng một mã | Bị khóa, phải gõ lại để nhận mã mới | `gõ sai 3 lần.jpg`; log `docs/kiem_thu_otp_20261113.csv` (tài khoản `935c64e2`) | Giao diện báo đỏ: "Nhập sai OTP quá số lần cho phép. Vui lòng gõ lại để nhận mã mới." Log ghi `wrong` 15:06:23, `wrong` 15:06:27, `locked` 15:06:28 (13/11/2026). | 13/11/2026 15:06 |
| 11 | OTP hết hạn | Yêu cầu OTP, đợi hơn 5 phút rồi nhập | Báo hết hạn, không cập nhật hồ sơ | `mã OTP hết hạn.jpg` | Đợi quá 5 phút rồi nhập mã, giao diện báo đỏ: "OTP đã hết hạn hoặc không tồn tại. Vui lòng gõ lại để nhận mã mới." | 13/11/2026 |
| 12 | Nhập lại mã OTP cũ | Nhập lại mã đã dùng hoặc đã bị thay | Bị từ chối, không cập nhật hồ sơ | `lỗi vì gõ lại mã OTP cũ.jpg` | Gõ lại để sinh challenge mới rồi nhập lại mã OTP cũ đã bị thay thế: hệ thống từ chối, báo đỏ "OTP không đúng. Còn 2 lần thử." | 13/11/2026 |
| 13 | Gõ sai câu | Gõ sai câu mẫu rồi Enter | Báo lỗi, lượt gõ không được tính | `gõ sai chuỗi.jpg` | Giao diện báo đỏ: "Gõ sai chuỗi, vui lòng gõ lại từ đầu rồi nhấn Enter.", không hiện hộp OTP. | 13/11/2026 |
| 14 | Vai kẻ gian thiếu mã người thử | `/login?test=1`, chọn kẻ gian, để trống mã | Báo "cần có mã người thử" | `kẻ giản phải có mã thử.jpg` | Chọn vai "Tôi đóng vai kẻ gian", để trống ô mã người thử: báo đỏ "Vai kẻ gian cần có mã người thử (ví dụ T01)." | 13/11/2026 |

Ca 10: log lấy từ lần thử tài khoản demo `935c64e2` (log 07:55 đến 08:06 UTC, tức 14:55 đến 15:06 giờ VN), tách riêng khỏi dữ liệu live test (tài khoản `0e26d890`), không đưa vào bảng FAR/FRR.

## 2. Giới hạn đã biết

- Ca đăng ký thiếu mẫu không thử được qua giao diện vì nút nộp chỉ hiện khi đủ 20 lần. Việc máy chủ từ chối khi thiếu mẫu (lỗi 400) do người chấm kiểm tra bằng API, nhóm không tự thử qua giao diện.
- Kiểm tra `tester_id` bắt buộc hiện chỉ ở giao diện. Gọi API trực tiếp với vai kẻ gian và mã trống vẫn được chấp nhận.
- Nếu OTP đã bị xóa khỏi bộ nhớ khi hết hạn, log không ghi event "expired". Thiếu dòng "expired" trong log không có nghĩa là chưa chạy ca 11, hãy đối chiếu với cột "Thực tế" và ảnh.
- Log ca 10 (`docs/kiem_thu_otp_20261113.csv`) là tài khoản khác với live test, không gộp vào 33 lượt FAR/FRR.
