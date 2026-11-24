# Kiểm tra độ ổn định chuẩn hóa trước khi dùng điểm nhịp gõ

Đây là công việc kỹ thuật xuất phát từ chẩn đoán USN đã xem, không phải giả thuyết được định trước khi xem USN hoặc một thuật toán mới. Không sửa Scaled Manhattan, sàn 1e-9, cách chia 5 fold, ngưỡng z hoặc kết quả chấm cũ. Chưa triển khai ứng dụng thật.

Đầu vào duy nhất là đúng 20 mẫu đăng ký hữu hạn. Không nhận mẫu kiểm tra, nhãn chính chủ/giả mạo, kết quả OTP hoặc ngưỡng học từ USN. Mỗi fold dùng đúng detector hiện tại để tính điểm trên bốn mẫu giữ ra.

Quy tắc cảnh báo cố định: (a) có chiều chạm sàn trong phần học của fold nhưng có mẫu giữ ra lệch khỏi tâm hơn sàn đó; hoặc (b) độ lệch chuẩn OOF chạm sàn 1e-6. Quy tắc (a) chỉ phát hiện sự ngoại suy qua sàn, không khẳng định mọi trường hợp cảnh báo sẽ gây lỗi xác thực. Cũng không bảo đảm mọi trường hợp không cảnh báo là an toàn.

Hàm quyết định thử nghiệm chỉ cho phép dùng kết quả nhịp gõ khi không có cảnh báo và z không vượt ngưỡng đã cấp. Trường hợp còn lại yêu cầu xác minh bổ sung; xác minh bổ sung chưa được giả định thành công, chưa phải đăng nhập thành công. Không gọi việc chặn một đường nhận là cải thiện FAR nếu chưa đánh giá toàn bộ luồng và chi phí xác minh.

Viết kiểm thử dữ liệu giả trước lượt kiểm tra 30 hồ sơ: trường hợp bình thường; mẫu giữ ra biến thiên khi phần học chạm sàn; hằng hoàn toàn; chiều hằng nhưng không ngoại suy; không đổi ma trận đầu vào; điểm và thống kê khớp detector gốc; giá trị không hữu hạn/khác số mẫu/khác số chiều; cảnh báo không bị bỏ qua bởi điểm z thấp; ngưỡng biên.

Sau khi kiểm thử đạt mới chạy audit trên đủ 30 ma trận đăng ký USN. Chỉ công bố số hồ sơ cảnh báo và nguyên nhân, đối chiếu thống kê OOF đã lưu. Không đọc CSV quyết định để thiết kế quy tắc hoặc chạy lại đánh giá test. Đây là kiểm tra hồi cứu phạm vi cảnh báo, không phải đo chất lượng phát hiện độc lập. Mọi cảnh báo, kể cả nhiều hơn ba hồ sơ đã biết, phải giữ nguyên.
