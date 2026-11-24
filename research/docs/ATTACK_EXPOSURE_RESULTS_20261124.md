# Một mẫu giả mạo được nhận ở bao nhiêu hồ sơ?

USN có 2.042 mẫu giả mạo khác nhau theo khóa (câu, dòng nguồn). Mỗi mẫu được chấm với đúng năm hồ sơ đích, tạo 10.210 quyết định. Kiểm đủ ma trận không có dòng trùng, hồ sơ thiếu hoặc mã nguồn bất nhất. Không thay score, ngưỡng, cảnh báo hoặc hồ sơ mô hình.

Trước quy tắc chuyển tuyến, 686/2.042 mẫu (33,59%) qua ít nhất một hồ sơ; sau quy tắc là 349/2.042 mẫu (17,09%). Trong số 349 mẫu sau quy tắc, 324 mẫu qua một hồ sơ và 25 qua hai hồ sơ, nên số quyết định được nhận là 324 + 2×25 = 374. Các mẫu còn lại không qua trực tiếp hồ sơ nào trong năm hồ sơ đã xét.

Hai cách đếm khác nhau: 374/10.210 = 3,66% là tỷ lệ quyết định đích được nhận, còn 349/2.042 = 17,09% là tỷ lệ mẫu qua ít nhất một trong năm đích. Không dùng chỉ số sau thay FAR một tài khoản hoặc kết quả sau OTP. Đây là kịch bản tĩnh với số hồ sơ cố định, không mô phỏng chiến lược thử lặp, giới hạn thử của web hoặc khả năng chọn tài khoản trong thực tế.

Trước quy tắc, Ob$erv3r có 337 mẫu qua ba hồ sơ và 3 mẫu qua bốn hồ sơ; sau quy tắc chỉ còn 3 mẫu qua một hồ sơ. Năm câu khác không đổi. Sau quy tắc, số mẫu qua ít nhất một đích theo câu là Gigab!t R3ceiver 23/322, Ob$erv3r 3/340, flying automatic monster 34/340, gigabit receiver 135/350, observer 134/350, repetition learn machine thinker 20/340. Giữ đủ sáu câu; không loại câu khỏi kết quả chính.

11 ca dữ liệu giả đạt trước khóa mã/input. Bộ kiểm riêng dựng vector Boolean đủ năm đích cho mỗi mẫu, đếm bằng phép OR và khớp đủ bảy bảng tổng hợp, histogram và 10.210 quyết định. Artifact prefix `results/attack_exposure_20261124_`; kiểm bằng `python scripts/verify_attack_exposure_20261124.py`, kiểm khóa bằng `python -m scripts.run_attack_exposure_20261124 --check`.

Đây là phân tích hồi cứu trên nguồn đã xem. Cùng người/câu và các mẫu attack dùng lại vẫn có phụ thuộc; 2.042 mẫu cũng không được coi là 2.042 người độc lập. Phân tích làm rõ đơn vị đo và phạm vi đe dọa, chưa chứng minh cải thiện mô hình, giảm rủi ro toàn hệ thống hoặc tổng quát sang số tài khoản khác.
