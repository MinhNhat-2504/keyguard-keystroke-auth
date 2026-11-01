# Các lỗi đã sửa theo bảng chấm (phần Thư, TV2)

Không động vào `keyguard/` (code của Nhật). Phần khảo sát / thử nghiệm thực tế (2.2, 2.5, 2.6) chưa làm.

## P0
- **A. Hợp đồng dữ liệu**: đăng ký/đăng nhập dùng chung `static/keycapture.js`, ghi sự kiện `{key, type, t}` bằng `performance.now()`,
  kết thúc lần gõ sau khi nhả **Enter**, khóa ô nhập khi đang gửi, tự reset khi sai/lỗi. Đăng ký gửi `samples: [events_1..events_n]`.
  Số lần đăng ký lấy từ `models/model_config.json` (`n_enroll` = 20) và backend kiểm tra lại, không chỉ UI.
- **B. Cấu hình mô hình**: thêm `models/model_config.json` (bản Nhật gửi). Thiếu file thì API trả JSON lỗi rõ ràng.
- **C. Chặn đường dẫn / ghi đè**: mã người tham gia chỉ nhận `P01`..; hồ sơ lưu bằng ID nội bộ ngẫu nhiên (uuid), kiểm tra đường dẫn
  sau resolve; đăng ký trùng tên (không phân biệt hoa/thường) trả 409, hồ sơ cũ giữ nguyên.

## P1
- **D. OTP mô phỏng + cập nhật hồ sơ**: chấp nhận -> `update()` + lưu. Không khớp -> server tạo OTP (hiệu lực 5 phút, tối đa 3 lần thử, lưu dạng băm),
  lần gõ chỉ được đưa vào hồ sơ khi `/api/verify-otp` xác nhận OTP đúng. OTP "gửi" ra console server và hiện như tin nhắn SMS giả lập trên trang
  (đặt `KEYGUARD_SHOW_OTP=0` để không trả OTP về trình duyệt).
- **E. Thu nhiều phiên**: `/api/get-id` giữ chỗ mã (khóa file, hai người cùng lúc không trùng); có ô "quay lại bằng mã đã có" để thu phiên 2/3;
  server tự đánh số lần gõ theo (người, phiên) nên không trùng và tối đa 40/phiên; đổi phiên đọc lại tiến độ từ server;
  mỗi mẫu lưu thêm `collected_at`. Kiểm tra phân biệt hoa/thường (`R` hoa) trước khi chuẩn hóa phím.
- **F. Lỗi giao diện/API**: link "Quay lại đăng nhập" -> `/login`, có link giữa 3 trang; đăng ký chỉ báo thành công khi `success=true`;
  không còn `NaN%`; xử lý lỗi mạng; mọi lỗi `/api/*` (kể cả body `[]`, JSON hỏng, 404/405) trả 4xx JSON `{success:false, message}`.
  Kiểm tra tên đã tồn tại ngay từ đầu để khỏi gõ 20 lần rồi mới bị từ chối.

## P2
- Bỏ `keyguard/__pycache__` khỏi Git, thêm `.gitignore` (cache, venv, dữ liệu hồ sơ/OTP).
- Giá trị từ Flask (`{{ }}`) đưa vào thuộc tính `data-` của `<body>` thay vì viết trong thẻ `<script>`, để VS Code không báo lỗi cú pháp.
- Dùng `logging` thay `print` (hết lỗi UnicodeEncodeError trên Windows). `debug` chỉ bật khi `FLASK_DEBUG=1`.
- Sửa `Procfile`: `gunicorn app:app` (trước là `app:appflask`).

## Chạy
    pip install -r requirements.txt
    python app.py        # http://127.0.0.1:5000  (/ , /register , /login)
