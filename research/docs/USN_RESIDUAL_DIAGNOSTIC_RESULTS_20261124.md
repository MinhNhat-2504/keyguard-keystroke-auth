# Chẩn đoán 374 quyết định giả mạo còn qua nhịp gõ

Phân tích giữ nguyên toàn bộ 15.610 quyết định USN, ngưỡng z và map cảnh báo. Không đọc raw, không fit/chấm lại mô hình hoặc thử ngưỡng mới. Mọi số dưới đây là mô tả hồi cứu trên nguồn đã xem; chưa đo kết quả OTP hoặc cải thiện xác thực toàn luồng.

## Lỗi tập trung ở đâu

| Câu | Quyết định giả mạo còn qua nhịp gõ |
|---|---:|
| observer | 146 |
| gigabit receiver | 144 |
| flying automatic monster | 34 |
| Gigab!t R3ceiver | 27 |
| repetition learn machine thinker | 20 |
| Ob$erv3r | 3 |
| Tổng | 374 |

Hai câu đầu chiếm 290/374, khoảng 77,54%. Gộp theo mã hồ sơ đích, participant1 có 0, participant2 có 16, participant3 có 34, participant4 có 19 và participant5 có 305. Như vậy 305/374, khoảng 81,55%, thuộc các hồ sơ đích mang mã participant5; không suy diễn đây là mã người tấn công hoặc quy lỗi cho một cá nhân.

## Phân biệt xếp hạng với ngưỡng đang dùng

AUC được tính cho đủ 30 hồ sơ, theo xác suất điểm attack lớn hơn điểm genuine và cộng nửa trọng số cho tie theo giá trị float lưu. Đây là AUC của điểm đã có; không dùng để chọn ngưỡng khác. Cùng hồ sơ, chuẩn hóa affine có scale dương giữ thứ tự về mặt đại số, còn tỷ lệ nhận nhầm phụ thuộc ngưỡng đang dùng.

| Hồ sơ đích | Qua nhịp gõ / attack | Genuine không khớp | AUC | Tỷ trọng OOF lớn nhất |
|---|---:|---:|---:|---:|
| participant5, observer | 127/350 | 9/180 | 0,9424 | 0,3226 |
| participant5, gigabit receiver | 113/350 | 26/180 | 0,8670 | 0,1421 |

Hai hồ sơ này chiếm 240/374, khoảng 64,17%, và không có cảnh báo ngoại suy qua sàn theo quy tắc cố định. AUC observer cao hơn gigabit receiver, nhưng vẫn có nhiều lượt qua nhịp gõ tại ngưỡng hiện tại. Kết quả giúp tách khả năng xếp hạng với quyết định tại ngưỡng và cho thấy cảnh báo sàn chỉ xử lý một dạng rủi ro. Nó chưa xác định đầy đủ nguyên nhân của số nhận nhầm còn lại hoặc chứng minh chọn lại ngưỡng sẽ giảm đồng thời hai loại lỗi.

Trung vị z genuine/attack ở observer là −0,1678/0,4010; ở gigabit receiver là −0,3446/0,5016. Các khoảng min–max của hai nhóm có chồng lấp. Các số này chỉ mô tả phân bố của những lượt đã có, không thay một phép đối chứng về cách hiệu chỉnh hay đánh giá trên người/nguồn chưa dùng. Tỷ trọng OOF là thống kê liên tục, không tạo quy tắc cảnh báo mới từ các giá trị vừa thấy.

## Kiểm tra và giới hạn

12 ca dữ liệu giả đạt trước khóa mã và tổng hợp. Bộ kiểm độc lập tính AUC bằng so trực tiếp 1.837.800 cặp score, khác thuật toán bisect của runner; số đếm và AUC của đủ 30 hồ sơ khớp. Mỗi cặp hoặc lượt chấm dùng lại mẫu không phải quan sát độc lập, nên không báo ý nghĩa thống kê từ các cặp này. Không chọn riêng hồ sơ thuận lợi; CSV/JSON giữ đủ cả 30 hồ sơ, sáu câu và các nhóm mã attack_subject có nhận nhầm còn lại.

Artifact prefix `results/usn_residual_diagnostic_20261124_`. Kiểm bằng `python scripts/verify_usn_residual_diagnostic_20261124.py`; khóa bằng `python -m scripts.run_usn_residual_diagnostic_20261124 --check`. Dữ liệu này chưa là cơ sở để chỉnh ngưỡng và gọi kết quả là kiểm chứng mới. Hướng phát triển cần đặt phép đối chứng hiệu chỉnh trên DEV và đánh giá trên nguồn chưa dùng phát triển, đồng thời đo chi phí xác minh.
