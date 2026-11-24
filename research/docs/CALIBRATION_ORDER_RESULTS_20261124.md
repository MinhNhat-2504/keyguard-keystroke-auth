# Cảnh báo ổn định trong năm cách, thang CV vẫn thay đổi

Phép kiểm dùng cùng 20 mẫu đăng ký ở 36 DEV CMU, 66 DEV KeyRecs và 30 hồ sơ USN. Các nguồn đã được xem. Giữ nguyên detector, cảnh báo, sàn số học và ngưỡng z; không chấm TEST, đọc quyết định đánh giá hoặc chọn thứ tự mới để sử dụng. Có năm cách định trước: gốc, đảo kiểm soát và dịch vòng 1/2/3 hàng trước khi chia năm khối bốn hàng.

## Kết quả trên 132 hồ sơ

| Nguồn | Hồ sơ | Cảnh báo: gốc / đảo / dịch 1 / 2 / 3 | Tỷ số ngưỡng thô max/min trung vị | Tỷ số max/min lớn nhất trong một hồ sơ |
|---|---:|---|---:|---:|
| CMU | 36 | 0 / 0 / 0 / 0 / 0 | 1,0768 | 1,6779 |
| KeyRecs | 66 | 0 / 0 / 0 / 0 / 0 | 1,0969 | 2,5652 |
| USN | 30 | 3 / 3 / 3 / 3 / 3 | 1,0474 | 1,2028 |

Không hồ sơ nào đổi trạng thái cảnh báo trong năm cách. Đảo kiểm soát giữ các tập fold và tái lập điểm OOF trong sai số kiểm tra ở đủ 132 hồ sơ. Tham số hồ sơ học đủ 20 mẫu khớp trong kiểm tra ở 660/660 trường hợp. Kết quả phân biệt thay đổi thang hiệu chỉnh do biên fold với thay đổi tập mẫu đăng ký; không tự chứng minh xác thực ổn định.

Cùng ngưỡng z, ngưỡng điểm thô tương đương thay đổi theo mean/SD OOF. Trường hợp biến động tỷ số lớn nhất của CMU là s032: 40,6734–68,2464; KeyRecs là p071: 1.470,7740–3.772,8668; USN là participant1 ở Gigab!t R3ceiver: 87,2861–104,9900. Tỷ số được tính trong cùng hồ sơ qua năm cách, không lấy hồ sơ này chia hồ sơ khác. Cỡ nhóm và đặc trưng các nguồn khác nhau nên không dùng cực trị để xếp hạng mức an toàn giữa nguồn.

## Diễn giải và giới hạn

Cảnh báo sàn không đổi chưa có nghĩa độ nhạy hiệu chỉnh đã nhỏ. Tại KeyRecs, một hồ sơ không cảnh báo vẫn có ngưỡng thô thay đổi tới khoảng 2,57 lần khi chỉ dịch biên fold, trong khi mô hình học đủ mẫu tương đương theo kiểm tra. Phép kiểm này chưa đo thay đổi FAR/FRR hoặc chi phí xác minh từ những thang mới; mọi quyết định và thang dùng trong kết quả lịch sử được giữ nguyên.

Năm cách không bao phủ mọi phân hoạch. Ca dữ liệu giả có hai giá trị hiếm cùng nằm trong một fold cho cảnh báo; dịch để tách chúng sang các fold khác có thể làm cảnh báo biến mất. Ca này cho thấy quy tắc không bất biến theo mọi thứ tự một cách tổng quát, dù dữ liệu thực ở năm cách đã thử không đổi cảnh báo. Dữ liệu giả không được tính thành hồ sơ người dùng hoặc bằng chứng cải thiện mô hình.

Đổi thứ tự ở đây chỉ là nhiễu cấu trúc CV. Nó không tạo phiên/ngày mới, không mô phỏng quá trình dùng tài khoản và không giải quyết giới hạn dữ liệu tự thu chủ yếu một phiên. Hướng phát triển tiếp cần đặt đối chứng hiệu chỉnh trên DEV và kiểm bằng nguồn chưa dùng phát triển; không chọn một trong năm thứ tự vì số liệu thuận lợi.

## Kiểm tra

7 ca dữ liệu giả đạt trước khóa mã/input/protocol/môi trường. Runner giữ đủ 132 hồ sơ × 5 cách = 660 trường hợp, dùng tổng cộng 2.640 mẫu đăng ký gốc. Bộ đối chiếu tính CV lại bằng mean/MAD thuần Python từ raw và khớp đủ 660 trường hợp trong sai số đã định; nó dùng lại input reader DEV đã được kiểm độc lập trước đó, không nhận là hai pipeline hoàn toàn độc lập. Kiểm saved-only chỉ đối chiếu artifact, không đọc raw.

Artifact prefix `results/calibration_order_20261124_`. Lệnh kiểm khóa: `python -m scripts.run_calibration_order_20261124 --check`. Kiểm công khai: `python scripts/verify_calibration_order_20261124.py --saved-only`; kiểm raw local dùng `--check-raw` với dependency nghiên cứu. `--run` từ chối ghi đè. Không thay detector, ngưỡng z, cảnh báo, backend hoặc cấu hình triển khai.
