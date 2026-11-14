# Biên bản kiểm thử biên OTP (B3)

- **Người thực hiện:** Thư.
- **Ngày giờ chạy:** 14/11/2026 (22:40).
- **Môi trường:** Windows, Python 3.12.
- **Ghi chú:** Script `tests/test_otp_boundaries_thu.py` do Claude viết theo yêu cầu của tôi; tôi tự chạy trên máy cá nhân, tự kiểm tra kết quả và tự viết biên bản này.

## 1. Lệnh đã chạy
```bash
python tests/test_otp_boundaries_thu.py
```
**Kết quả tổng quát:** 3/3 ca đạt (`OK`), thời gian chạy ~0.184s, `exit code = 0`.

## 2. Chi tiết ba ca kiểm thử

| # | Tình huống kiểm thử | Kết quả mong đợi | Kết quả thực tế |
| :--- | :--- | :--- | :--- |
| 1 | OTP quá hạn (giả lập thời gian vượt quá TTL 5 phút) | HTTP 410, profile không cập nhật | **Đạt (HTTP 410, profile giữ nguyên)** |
| 2 | Dùng lại OTP đã dùng thành công trước đó (replay) | HTTP 410, profile không thay đổi thêm | **Đạt (HTTP 410, chặn replay thành công)** |
| 3 | Nhập sai OTP liên tiếp | HTTP 401 (2 lần đầu), HTTP 429 (lần thứ 3 - khóa tạm thời) | **Đạt (401 -> 401 -> 429, profile giữ nguyên)** |

## 3. Giải thích cơ chế và thiết kế kiểm thử

- **Vì sao ca 1 không đợi thật 5 phút mà giả lập thời gian:** 
  Trong quy trình kiểm thử tự động (unit test), việc bắt hệ thống chờ đợi 5 phút thời gian thực cho một ca test sẽ làm chậm quá trình kiểm tra mã nguồn và không hiệu quả cho CI/CD. Do đó, script tiến hành dịch chuyển mốc thời gian (mock time) vượt quá thời gian sống (TTL) của challenge để xác minh API xử lý đúng trạng thái hết hạn (`410 Gone`).

- **Vì sao replay (dùng lại mã cũ) phải bị từ chối:** 
  Mã OTP chỉ có giá trị xác thực duy nhất một lần (one-time password) cho một phiên giao dịch cụ thể. Nếu kẻ tấn công chặn bắt được mã OTP đã sử dụng và gửi lại (replay attack) sau khi người dùng đã xác thực thành công, hệ thống bắt buộc phải từ chối với mã `410` và không được cập nhật lại hồ sơ người dùng.

- **Vì sao phải khóa/giới hạn sau 3 lần sai:** 
  Nếu không giới hạn số lần nhập sai, kẻ gian có thể dùng công cụ tự động dò mã OTP liên tục (brute-force attack). Việc chặn và trả về mã `429 Too Many Requests` ở lần sai thứ 3 giúp vô hiệu hóa các cuộc tấn công vét cạn và bảo vệ an toàn cho tài khoản.

- **Mỗi ca dùng một tài khoản mới để làm gì:** 
  Việc khởi tạo các tài khoản độc lập (`test_otp_user_1`, `test_otp_user_2`, `test_otp_user_3`) cho từng ca kiểm thử giúp cô lập hoàn toàn trạng thái dữ liệu (state isolation). Điều này đảm bảo việc một tài khoản bị khóa hoặc đã tiêu thụ challenge ở ca trước không làm ảnh hưởng hay gây sai lệch kết quả cho các ca kiểm thử phía sau.

## 4. Giới hạn kiểm thử
- Quá trình kiểm thử được thực hiện hoàn toàn trên môi trường mã nguồn cục bộ (local code) với thư mục tạm, chưa thực hiện trên server triển khai thực tế (Render).
- Sử dụng cơ chế giả lập đồng hồ cho tình huống hết hạn thay vì chờ đợi 5 phút theo thời gian thực.
- Test dùng dữ liệu tổng hợp tạo trong thư mục tạm, không dùng dữ liệu của người tham gia thật.
