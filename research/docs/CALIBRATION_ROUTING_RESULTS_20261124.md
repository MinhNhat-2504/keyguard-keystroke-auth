# Lợi ích và chi phí theo tuyến xử lý

Đây là phân tích hồi cứu trên cùng 15.610 quyết định USN đã lưu. Quy tắc cảnh báo đã được xây từ lỗi biết trên USN; kết quả dưới đây chưa là kiểm chứng độc lập. Giữ nguyên toàn bộ score, ngưỡng 0,2720094565367825, 30 hồ sơ, 5.400 lượt chính chủ và 10.210 quyết định giả mạo. Không fit hoặc chấm lại mô hình, không đọc raw. Bộ tổng hợp dùng đúng hàm `behavioral_acceptance_allowed` của prototype v7 và audit tương ứng mỗi hồ sơ.

| Tuyến xử lý | Chỉ xét z | Thêm kiểm tra đăng ký |
|---|---:|---:|
| Chính chủ qua nhịp gõ | 3.628/5.400 | 3.088/5.400 |
| Chính chủ cần xác minh | 1.772/5.400 | 2.312/5.400 |
| Giả mạo qua nhịp gõ | 1.394/10.210 | 374/10.210 |
| Giả mạo cần xác minh | 8.816/10.210 | 9.836/10.210 |

Có 1.020 quyết định giả mạo chuyển sang xác minh bổ sung, đồng thời thêm 540 lượt chính chủ cần xác minh. Các lượt thay đổi đều thuộc ba hồ sơ cảnh báo đã biết; 27 hồ sơ còn lại giữ nguyên tuyến. Các mẫu số không bị giảm khi chuyển tuyến. Tỷ lệ giả mạo qua bước nhịp gõ thay đổi 13,65% → 3,66%, còn tỷ lệ chính chủ cần xác minh 32,81% → 42,81%. Đây là tỷ lệ tuyến xử lý trên benchmark, không phải FAR/FRR cuối cùng của hệ thống và không phải ước lượng tải thực tế với tỷ lệ chính chủ/giả mạo ngoài đời.

374 quyết định giả mạo vẫn đi qua bước nhịp gõ, nên một bước xác minh hoàn hảo chỉ áp cho tuyến còn lại cũng không xử lý được các lượt đã qua này. Trong mô hình hai tuyến giả định, khi chưa biết kết quả xác minh, số nhận giả mạo cuối cùng có cận 374–10.210 và số từ chối chính chủ cuối cùng có cận 0–2.312. Cận rộng cho thấy chưa đủ dữ liệu để báo tỷ lệ lỗi toàn luồng; không tự giả định OTP thành công với chính chủ hoặc thất bại với giả mạo.

Quy tắc cảnh báo chỉ hạn chế tập lượt đi qua bước nhịp gõ, vì vậy không có lượt từ tuyến xác minh được chuyển thành nhận bằng nhịp gõ. Tính chất này không tự chứng minh bảo mật hoặc tính hữu dụng: nếu buộc mọi người xác minh thì cũng giảm đường nhận trực tiếp nhưng tăng chi phí. Chưa đo thời gian, trải nghiệm, lỗi bước bổ sung hoặc hiệu quả trên nguồn chưa xem.

11 ca kiểm thử dữ liệu giả đạt trước khóa mã và tổng hợp, gồm bảo toàn mẫu số, ngưỡng biên, dùng đúng gate, đầu vào không hợp lệ và chống đếm trùng. `scripts/verify_calibration_routing_20261124.py` chỉ dùng thư viện chuẩn, đếm lại độc lập đủ 15.610 lượt và đối chiếu 30 dòng theo hồ sơ. Artifact prefix `results/calibration_routing_20261124_`; runner `python -m scripts.run_calibration_routing_20261124 --check`. `--run` từ chối ghi đè. Không thay kết quả USN gốc, code preflight đã khóa hoặc backend.
