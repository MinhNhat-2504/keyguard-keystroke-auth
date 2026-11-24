# Độ nhạy kết quả và chẩn đoán chuẩn hóa USN

Đây là phân tích hồi cứu trên kết quả USN đã xem. Giữ nguyên toàn bộ điểm đánh giá, ngưỡng 0,2720094565367825 và bảng chính; không loại người hoặc câu để tạo tỷ lệ chính mới. Script tổng hợp không fit mô hình. Phần chẩn đoán CV tính lại chỉ trên 20 mẫu đăng ký và tái lập đúng thống kê CV của cả 30 hồ sơ.

## Theo người và thành phần dữ liệu

Gộp đủ sáu câu theo từng người, FAR lần lượt là 16,65%; 17,43%; 18,32%; 0,93%; 14,94%, FRR là 36,11%; 32,69%; 33,24%; 40,19%; 21,85%. Như vậy một người có FAR thấp vẫn có FRR cao. Mỗi tổng hợp chỉ mô tả sáu hồ sơ của một người, không phải đánh giá sáu cá nhân độc lập.

Khi bỏ lần lượt từng người chỉ khỏi bước tổng hợp, FAR gộp còn lại từ 12,49% đến 16,83%, FRR từ 30,97% đến 35,56%. Kết luận ngưỡng này chưa cho mức lỗi thấp không chỉ do một người duy nhất. Khi bỏ lần lượt từng câu, FAR biến động 4,36–16,15%; việc bỏ đúng Ob$erv3r cho tỷ lệ thấp nhất. Đó là độ nhạy với thành phần câu, không phải lý do hợp lệ để xóa câu khỏi kết quả chính.

Nếu xét toàn bộ 27 dòng attack bị loại như 135 quyết định chưa biết trên 5 hồ sơ, FAR gộp trong kịch bản giữ mọi dòng raw nằm từ 1.394/10.345 = 13,48% đến 1.529/10.345 = 14,78%. Không điểm nào được tạo hoặc điền. Cận chỉ là đại số trên các dòng raw, gồm cả khóa trùng mơ hồ, không coi chúng là các mẫu độc lập. Dưới cả hai cực trị, kết luận FAR cao vẫn còn. Không thay chính sách loại khóa trùng của bảng chính.

## Vì sao có hồ sơ nhận mọi lượt giả mạo

Ba hồ sơ participant1–3 trên Ob$erv3r nhận 340/340 lượt giả mạo và không từ chối chính chủ. Đối chiếu mẫu đăng ký cho thấy ở một fold CV của mỗi hồ sơ, cột `down to down '#CTRL#' => '#ALT#'` có MAD bằng 0 trên 16 mẫu học. Mẫu giữ ra lệch 0,001 giây; chia cho sàn 10⁻⁹ tạo đóng góp 1.000.000. Ở các mẫu đó, một cột đóng góp hơn 99,99% tổng điểm OOF. Hồ sơ học đủ 20 mẫu không nhất thiết có cùng tình trạng chạm sàn; cần phân biệt biến thiên trong fold với thống kê toàn pool.

| Hồ sơ Ob$erv3r | Trung bình OOF | SD OOF | Nhận nhầm | Chính chủ từ chối |
|---|---:|---:|---:|---:|
| participant1 | 50.038,95 | 217.949,99 | 340/340 | 0/180 |
| participant2 | 50.052,95 | 217.940,50 | 340/340 | 0/180 |
| participant3 | 50.039,21 | 217.949,48 | 340/340 | 0/180 |
| participant4 | 39,54 | 11,57 | 0/340 | 165/180 |
| participant5 | 40,50 | 9,95 | 3/340 | 137/180 |

Với ba hồ sơ đầu, ngưỡng z cố định tương ứng giới hạn điểm thô khoảng 109.323–109.335. Điểm z của mọi lượt attack nằm trong khoảng âm −0,230 đến −0,194, đều dưới ngưỡng +0,272. Đây là cơ chế số học có thể tái lập giải thích sự dễ nhận của chính những hồ sơ này; không chứng minh toàn bộ FAR/FRR hoặc khác biệt giữa câu đều có chung nguyên nhân. Không kết luận người gõ hoặc bộ dữ liệu là sai.

Kết quả cho thấy cần kiểm độ nhạy của scale ở từng fold và mức phân giải thời gian khi phát triển quy tắc tiếp theo. Nghiên cứu cũ chỉ thấy không chạm sàn trên hồ sơ đủ mẫu chưa đủ để loại khả năng chạm sàn trong CV ở nguồn khác. Muốn kiểm một cách sửa phải đặt đối chứng trên DEV và dùng nguồn chưa xem để xác nhận; không sửa sàn hoặc cắt điểm CV trên chính USN rồi gọi là kiểm chứng độc lập.

7 test số học tổng hợp và 4 test chẩn đoán CV đạt bằng dữ liệu giả trước khi chạy phân tích tương ứng. Nguồn đầy đủ/hash ở `results/usn_sensitivity_20261124.json`, `results/usn_sensitivity_20261124_people.csv`, `results/usn_oof_diagnostic_20261124.json`. Mã `scripts/usn_sensitivity_20261124.py` và `scripts/usn_oof_diagnostic_20261124.py`. Không thay chương trình hoặc kết quả của lượt chấm USN đã khóa.
