# Kế hoạch phân tích luồng xác minh sau cảnh báo

Phân tích hồi cứu trên USN đã xem, sau khi bộ kiểm tra chuẩn hóa được viết từ chẩn đoán nguồn này. Không gọi đây là kiểm chứng độc lập, không chọn lại quy tắc cảnh báo, score hoặc ngưỡng. Mục đích là lượng hóa chi phí xác minh bổ sung mà bản v7 chưa đo, cùng số lượt giả mạo không còn đi thẳng qua bước nhịp gõ.

Dùng đủ 15.610 quyết định đã lưu và cùng ngưỡng z của lượt USN gốc. Nhánh trước chỉ xét z <= ngưỡng; nhánh sau dùng hàm `behavioral_acceptance_allowed` của prototype đã khóa và audit thuộc đúng hồ sơ. Với mỗi lượt, chỉ có hai tuyến: qua bước nhịp gõ hoặc cần xác minh bổ sung. Không mô phỏng kết quả OTP hoặc gọi tuyến thứ hai là từ chối cuối cùng.

Đếm riêng 5.400 lượt chính chủ và 10.210 quyết định giả mạo, giữ nguyên mẫu số trước–sau. Báo số chuyển tuyến của hai nhóm, bảng theo người–câu, và toàn bộ 30 hồ sơ. Không loại câu lỗi cao, hồ sơ không cảnh báo hoặc dòng bất lợi. Các quyết định không độc lập; không coi 15.610 lượt là 15.610 người để tính ý nghĩa thống kê.

Với luồng hai bước giả định chỉ nhận nhịp gõ hoặc chuyển xác minh, số nhận giả mạo cuối cùng nằm giữa số đi thẳng qua nhịp gõ và toàn bộ lượt attack; số chính chủ bị từ chối cuối cùng nằm giữa 0 và số cần xác minh. Đây chỉ là cận khi chưa biết kết quả xác minh. Không gọi tỷ lệ đi thẳng qua nhịp gõ là FAR của toàn hệ thống; không gọi tỷ lệ chính chủ cần xác minh là FRR cuối cùng.

Kiểm thử bằng dữ liệu giả trước khi khóa mã và chạy tổng hợp: dùng đúng hàm gate; điểm ở ngưỡng; cảnh báo không bị bỏ qua bởi điểm thấp; bảo toàn mẫu số; không chuyển tuyến xác minh thành nhận bằng nhịp gõ; dữ liệu trùng, score không hữu hạn, nhãn sai, thiếu audit hoặc cờ quyết định cũ không khớp ngưỡng phải báo lỗi. Giữ nguyên input và artifact trước đó.
