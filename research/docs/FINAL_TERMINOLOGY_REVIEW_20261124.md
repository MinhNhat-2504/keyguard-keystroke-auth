# Rà giả định và thuật ngữ trước khi nộp

Lượt này chỉ sửa diễn đạt theo code đã có, không chạy lại mô hình hoặc thay dữ liệu/kết quả. Mục tiêu là giúp người đọc phân biệt các đại lượng và thiết kế đang cùng xuất hiện trong báo cáo.

| Điểm cần làm rõ | Bằng chứng trong mã | Cách diễn đạt trong báo cáo |
|---|---|---|
| FRR của mô phỏng fallback | `keyguard/simulation.py`: ghi z của genuine trước cập nhật; fallback cập nhật mọi mẫu genuine trong stream, giả định bước bổ sung thành công | Tỷ lệ chính chủ cần xác minh thêm tại bước nhịp gõ, chưa là tỷ lệ từ chối cuối cùng sau OTP |
| Probe trong lịch chọn ngưỡng | `simulate_user` chỉ chấm `imp_X` tại checkpoint; không thêm probe vào profile | Cả ba chính sách trong lịch này đều không bị cập nhật bởi probe giả mạo, kể cả probe được nhận |
| Vì sao static/fallback có thể chọn ngưỡng trực tiếp | Static giữ profile; fallback cập nhật toàn bộ genuine theo giả định, trong khi probe không cập nhật | Tính chất phụ thuộc chính lịch không xen mẫu, không suy rộng sang luồng có giả mạo cập nhật |
| Phép thử nhiễm hồ sơ | `keyguard/contamination.py`: fallback cập nhật genuine hoặc attack được nhận; verified_only là đối chứng lý tưởng | Là một thiết kế riêng, giải thích rủi ro mà lịch probe không cập nhật không đo |
| Confidence | `keyguard/model.py`: biến đổi đơn điệu từ z và ngưỡng, bằng 0,5 tại ngưỡng | Điểm hiển thị, chưa là xác suất danh tính đã hiệu chuẩn |
| OTP và bằng chứng web | Web dùng challenge/OTP mô phỏng, không có provider SMS/email trong luồng này | Event chứng minh bước xử lý của bản mô phỏng, không là bằng chứng giao OTP thật hoặc an toàn của dịch vụ xác minh |
| Đối chiếu tính toán và dữ liệu mới | Các validator đọc lại artifact; kiểm raw CV dùng reader được công bố rõ | Mã tính khác giúp kiểm số học, không biến dữ liệu đã xem thành tập kiểm chứng độc lập |

Báo cáo được sửa ở phần chỉ số, mô phỏng chọn ngưỡng, caption confidence và hướng phát triển. Sửa các chỗ viết hoa/thiếu khoảng trắng rõ ràng mà không đổi số đo, biểu đồ, bảng hoặc công thức. README và hướng dẫn đọc chỉ bổ sung điều kiện cốt lõi; giữ cấu trúc gọn, không thêm lịch sử phiên bản.
