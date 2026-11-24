# Chẩn đoán phần nhận nhầm còn lại sau cảnh báo

Phân tích hồi cứu trên USN đã xem, sau audit DEV. Giữ toàn bộ score, ngưỡng, quy tắc cảnh báo và 30 hồ sơ. Không thử ngưỡng mới, EER tối ưu, công thức chấm khác hoặc giả định kết quả OTP. Không đọc raw hay fit mô hình.

Đọc CSV 15.610 quyết định đã lưu và map cảnh báo thuộc đúng hồ sơ. Đếm đủ 374 quyết định giả mạo còn qua nhịp gõ, theo câu, hồ sơ và mã attack_subject của nguồn. Mã này không tự chứng minh danh tính thật hoặc trùng mã participant. Báo cả các hồ sơ không có nhận nhầm để tránh chỉ giữ trường hợp thuận lợi.

Tính AUC phân biệt điểm attack lớn hơn điểm genuine cho từng hồ sơ trong đủ 30 hồ sơ: AUC = [2 × số cặp (z_attack > z_genuine) + số cặp bằng nhau] / [2 × NG × NI]. Bằng nhau được hiểu theo giá trị float đã lưu. Báo AUC cùng các số đếm và min/trung vị/max của hai nhóm điểm; không dùng AUC để chọn lại ngưỡng. Đây là thước đo xếp hạng, không phải FAR/FRR ở ngưỡng hiện tại hoặc kiểm chứng ưu thế.

Chuẩn hóa affine có scale dương giữ thứ tự trong cùng hồ sơ về mặt đại số. Vì vậy AUC mô tả mức tách thứ tự của điểm hiện có, còn FAR/FRR mô tả quyết định tại ngưỡng đang dùng. Các điểm đánh giá và nhãn đã được xem nên diễn giải chỉ là chẩn đoán, không phải dữ liệu mới. AUC từ score lưu không xác định nguyên nhân nhân quả, mức khó của người thật hoặc một phương án sửa có hiệu quả.

Đối chiếu thêm thống kê OOF cũ ở từng hồ sơ: trung bình/SD và tỷ trọng điểm OOF lớn nhất trong tổng điểm. Tỷ trọng chỉ là mô tả liên tục; không tạo ngưỡng cảnh báo mới từ nó. Các kết quả không cảnh báo nhưng còn nhận nhầm phải được giữ.

Kiểm bằng dữ liệu giả và khóa code/input/test trước tổng hợp: hướng AUC, tie bằng nửa cặp, AUC đảo chiều, bất biến affine dương, đầu vào không hữu hạn, bảo toàn số lượt và không đếm trùng. Bộ độc lập sẽ đếm AUC bằng so trực tiếp từng cặp, không dùng thuật toán bisect của runner. Không coi các cặp hoặc quyết định dùng lại mẫu là quan sát độc lập để tính ý nghĩa thống kê.
