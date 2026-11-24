# Kiểm tra độ bao phủ cảnh báo trên DEV hiện có

Giữ nguyên `calibration_preflight.py`, sàn MAD 1e-9, sàn SD 1e-6 và cách chia 5 fold. Đây là audit bổ sung sau khi đã biết lỗi USN, trên các nguồn CMU/KeyRecs đã được xem; không gọi là kiểm chứng độc lập, không chọn lại detector, ngưỡng hoặc quy tắc cảnh báo.

Lấy toàn bộ DEV trong `matched_adaptation_plan.json`: 36 CMU và 66 KeyRecs. Kiểm hash raw theo kế hoạch cũ. Chỉ chuyển sang số đúng 20 dòng session 1 đầu theo repetition của từng mã DEV, giữ nguyên thứ tự cột của nguồn và đơn vị đã dùng trong các runner cũ. Mã thuộc TEST cũ không được đưa vào `audit_calibration`; session 2 và các dòng ngoài 20 mẫu không dùng để học hoặc chấm. Hash kiểm toàn tệp và CSV reader vẫn đọc metadata để lọc, nên không mô tả đây là không truy cập byte của phần còn lại.

Báo đủ 102 hồ sơ, danh sách cảnh báo và nguyên nhân; giữ mọi kết quả dù nhiều hoặc ít cảnh báo. Một hồ sơ cảnh báo là hồ sơ cần xem lại chuẩn hóa theo quy tắc này, không phải một false positive đã xác minh. Không cảnh báo không chứng minh an toàn; không tính FAR/FRR hoặc số lượt đăng nhập/OTP từ audit chỉ có mẫu đăng ký. Không so sánh tỷ lệ cảnh báo giữa các nguồn như tỷ lệ lỗi xác thực.

Reader mới phải kiểm bằng dữ liệu giả trước lượt audit: lọc đúng DEV/session 1; bỏ qua timing hỏng của TEST/session 2; chọn đúng 20 repetition đầu dù file đảo thứ tự; không parse timing ngoài 20 mẫu; báo lỗi trùng repetition, thiếu mẫu, schema sai hoặc số không hữu hạn. Khóa code, test, protocol, split, raw hash và môi trường trước khi chạy; không ghi đè kết quả.
