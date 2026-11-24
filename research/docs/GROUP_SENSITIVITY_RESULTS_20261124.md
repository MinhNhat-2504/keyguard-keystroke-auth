# Kết quả phụ thuộc nhóm trên USN

Phân tích hồi cứu giữ nguyên ngưỡng, cảnh báo và toàn bộ quyết định đã có. Không học lại mô hình hoặc loại nhóm khỏi kết quả chính. Bảng tổng hợp gốc vẫn có 1.394/10.210 lượt attack qua nhịp gõ trước quy tắc và 374/10.210 sau quy tắc chuyển tuyến; genuine cần xác minh thêm tăng từ 1.772/5.400 lên 2.312/5.400. Đây là định tuyến giả định, chưa là FAR sau OTP.

Điểm cần làm rõ là toàn bộ thay đổi 1.020 lượt attack và 540 lượt genuine nằm ở ba hồ sơ của câu Ob$erv3r. Khi bỏ riêng câu này khỏi phép cộng, cả trước và sau còn 371/8.510 lượt attack qua trực tiếp (4,36%) và 1.470/4.500 lượt genuine cần xác minh thêm (32,67%). Như vậy quy tắc hiện tại xử lý một ngoại lệ của một câu; chưa có bằng chứng nó cải thiện năm câu còn lại. Các dòng giữ câu Ob$erv3r vẫn thể hiện thay đổi do chính ngoại lệ đó, không phải sáu lần tái lập độc lập.

Khi lần lượt bỏ từng mã hồ sơ đích, tỷ lệ attack qua trực tiếp sau quy tắc dao động 0,84–4,58%; tỷ lệ genuine cần xác minh thêm 40,32–48,06%. Bỏ mã đích participant5 còn 69/8.168 lượt attack qua (0,84%); không được dùng tập con này thay kết quả đủ nhóm. Bỏ mã đích chỉ bỏ các hồ sơ được chấm vào mã đó, không loại mọi lần xuất hiện của một người hoặc học lại mô hình theo leave-one-person-out CV.

Đủ 5 trường hợp bỏ mã đích và 6 trường hợp bỏ câu được lưu trong `results/group_sensitivity_20261124_results.json`; cũng giữ bảng gộp đủ nhóm và thống kê từng nhóm. Khoảng min–max là mô tả ảnh hưởng nhóm trong mẫu hiện có, không là khoảng tin cậy. Năm mã đích, các câu cùng người và các lượt attack dùng lại không cho phép coi hàng nghìn quyết định là quan sát độc lập.

11 kiểm thử dữ liệu giả đạt trước khi khóa mã và input. Bộ kiểm riêng dùng 15.610 quyết định gốc và map cảnh báo cộng lại đủ 23 tập con, khớp số đếm và tỷ lệ của runner. Kiểm bằng `python scripts/verify_group_sensitivity_20261124.py`; kiểm khóa bằng `python -m scripts.run_group_sensitivity_20261124 --check`. Không có kết luận thuật toán mới hoặc cải thiện hiệu quả toàn hệ thống từ phân tích này.
