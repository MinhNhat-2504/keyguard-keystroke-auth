# Đếm mẫu giả mạo khác nhau khi chấm nhiều hồ sơ

Phân tích hồi cứu sau khi đã xem các nguồn, không là cải tiến mô hình hoặc kiểm chứng mới. Giữ nguyên score, ngưỡng và map cảnh báo; không học lại, tìm ngưỡng hoặc chọn tài khoản thuận lợi. Chỉ đọc artifact USN đã lưu.

Đơn vị nhóm là (phrase, source_line) trong tệp quyết định. Mỗi mẫu attack phải có đúng một quyết định ở mỗi hồ sơ đích trong cùng câu, mã nguồn attack_subject nhất quán và đủ cả năm hồ sơ. Mã dòng giống nhau ở hai câu là hai nhóm khác nhau. Kiểm đủ các câu và từ chối dòng trùng hoặc thiếu hồ sơ; không tự điền quyết định thiếu.

Giữ đủ sáu câu, báo trước/sau bước chuyển tuyến: số mẫu khác nhau, số quyết định đích, số mẫu qua ít nhất một đích và histogram số đích được nhận (0 đến 5). Tổng trọng số histogram phải tái lập số quyết định attack được nhận trong bảng định tuyến. Câu hỏi “qua ít nhất một trong năm hồ sơ” là kịch bản tĩnh với năm hồ sơ đã xét, không là FAR của một tài khoản, không chứng minh hành vi kẻ tấn công thực tế và không phải xác suất sau OTP. Không ngoại suy sang số tài khoản khác hoặc coi các mẫu cùng người/câu là độc lập.

Kiểm thử dữ liệu giả rồi khóa mã/input trước tổng hợp. Runner từ chối ghi đè kết quả. Bộ kiểm riêng dùng phép OR các quyết định theo mẫu và đếm histogram để đối chiếu, không import module runner. Không báo khoảng tin cậy, kiểm định hay hiệu quả xác minh bổ sung từ phép đếm này.
