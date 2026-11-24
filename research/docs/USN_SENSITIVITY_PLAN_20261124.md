# Phân tích độ nhạy hồi cứu của kết quả USN

Ngày 24/11/2026. Điểm và bảng kết quả USN đã được xem. Phần này là kiểm tra hồi cứu, không gọi là giả thuyết được đăng ký trước hoặc kiểm chứng dữ liệu mới. Không fit lại mô hình, chọn ngưỡng hay loại tài khoản khỏi kết quả chính.

Các phân tích được cố định trước khi tính bảng bổ sung: tổng hợp cả sáu câu theo từng người chính chủ; liệt kê đầy đủ 5 phép bỏ một người và 6 phép bỏ một câu để xem phạm vi tỷ lệ còn lại; tính cận cho ảnh hưởng của toàn bộ 27 dòng attack bị loại vì thiếu dữ liệu/trùng khóa.

FAR/FRR phải báo cả tỷ lệ gộp và trung bình theo hồ sơ. Mẫu số giữ vai trò lượt chấm, không chuyển thành số người độc lập. Bỏ một người/câu chỉ là phân tích độ nhạy của tổng hợp, không được chọn phép bỏ có lợi để công bố tỷ lệ chính mới. Giữ nguyên 1.394/10.210 và 1.772/5.400 trong bảng chính. Không gán nguyên nhân cho người, câu gõ, ký tự hoặc thiết bị từ bảng này.

Cận missing-data xét câu có 27 dòng attack bị loại: mỗi dòng nếu hoàn chỉnh sẽ được chấm trên 5 hồ sơ, tạo 135 quyết định chưa biết. Cận thấp coi cả 135 bị từ chối; cận cao coi cả 135 được nhận. Đây là cận đại số trên các dòng, không điền vector, không tạo điểm giả, không coi các dòng trùng là 27 mẫu độc lập thực sự. Cận mô tả kịch bản giữ mọi dòng raw, khác với chính sách loại khóa mơ hồ của phân tích chính.

Tính đúng số đếm từ account CSV, đối chiếu decision CSV trước khi tổng hợp. Thử dữ liệu giả cho tình huống lỗi tập trung, trung bình khác tỷ lệ gộp và cận không có dòng thiếu. Lưu code, kế hoạch, hashes nguồn và cả mọi trường hợp không thuận lợi.
