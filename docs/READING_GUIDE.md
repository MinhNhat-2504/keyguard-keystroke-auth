# Hướng dẫn đọc báo cáo

Nên bắt đầu từ Tóm tắt, mục 1.2 và Bảng 3.1 để nắm bài toán, phần nhóm thực hiện và kết quả tương ứng. Sau đó đọc các phép đánh giá dưới đây. [Báo cáo đầy đủ](../reports/KeyGuard_BaoCao_NopLai_v13_20261124.pdf) có bảng, hình và tài liệu tham khảo.

## Đọc theo câu hỏi nghiên cứu

| Câu hỏi | Vị trí trong báo cáo | Bằng chứng để mở cùng |
|---|---|---|
| Cấu hình CMU có giữ mức lỗi trên bộ tự thu không? | Mục 2.7–2.8 | [Tổng hợp 597 mẫu](../research/results/collected_preliminary_summary.json) |
| Từng thay đổi có tốt hơn đối chứng trong cùng điều kiện không? | Mục 2.15–2.30, Bảng 2.29 | [Đối chứng chọn mẫu đăng ký](../research/docs/ENROLLMENT_SELECTION_RESULTS_20261124.md) |
| Quy tắc cố định hoạt động ra sao trên nguồn khác? | Mục 2.31 | [Protocol USN](../research/docs/USN_TRANSFER_PROTOCOL_20261124.md) và [kết quả](../research/docs/USN_TRANSFER_RESULTS_20261124.md) |
| Vì sao chuẩn hóa CV có thể quá dễ nhận? | Bảng 2.33, Phụ lục D | [Chẩn đoán](../research/docs/USN_SENSITIVITY_RESULTS_20261124.md), [giải thích đại số](../research/docs/CALIBRATION_INFLUENCE_NOTE_20261124.md) |
| Bước cảnh báo đổi luồng xác minh như thế nào? | Phụ lục E | [Kiểm tra đăng ký](../research/docs/CALIBRATION_PREFLIGHT_RESULTS_20261124.md), [đếm tuyến xử lý](../research/docs/CALIBRATION_ROUTING_RESULTS_20261124.md) |
| Cảnh báo có xuất hiện trên DEV của nguồn khác không? | Phụ lục E | [Audit 102 hồ sơ DEV](../research/docs/PREFLIGHT_DEV_AUDIT_RESULTS_20261124.md) |
| Phần nhận nhầm còn lại tập trung ở đâu? | Mục 3.1, Phụ lục E | [Chẩn đoán đủ 30 hồ sơ USN](../research/docs/USN_RESIDUAL_DIAGNOSTIC_RESULTS_20261124.md) |
| Cùng tập mẫu, đổi biên fold có làm thang CV thay đổi không? | Mục 2.31 | [Độ nhạy trên 132 hồ sơ](../research/docs/CALIBRATION_ORDER_RESULTS_20261124.md) |

## Những khái niệm cần phân biệt

Với chuỗi chính gồm 10 ký tự và Enter, thư viện tạo 11 thời gian giữ phím, 10 khoảng nhấn–nhấn và 10 khoảng nhả–nhấn: tổng cộng 31 chiều. Khoảng nhả–nhấn có thể âm khi hai phím chồng nhau. Các nguồn khác có schema và số chiều riêng; khi chuyển quy tắc chấm, nhóm học hồ sơ theo dữ liệu nguồn đó.

Scaled Manhattan đo độ lệch so với tâm và độ biến thiên của mẫu đăng ký. Trong baseline, MAD là độ lệch tuyệt đối **trung bình** quanh trung bình; một số biến thể robust dùng trung vị. Hai định nghĩa này khác nhau. Điểm thô được chuẩn hóa bằng điểm OOF từ các mẫu đăng ký giữ ra trong CV, rồi so với ngưỡng z. Điểm hoặc confidence hiển thị chưa phải xác suất danh tính đã hiệu chuẩn.

FAR đo việc nhận nhầm người khác; FRR ở các bảng chấm nhịp gõ đo chính chủ không được nhận trực tiếp. EER/AUC nói về nhiều ngưỡng, còn FAR/FRR được báo tại ngưỡng cụ thể. Muốn so sánh hai hàng phải xem cùng cách chia dữ liệu, lịch cập nhật, đối tượng và cách gộp tỷ lệ.

Trong mô phỏng chọn ngưỡng, fallback cập nhật mọi mẫu genuine theo giả định xác minh bổ sung thành công. Probe giả mạo chỉ được chấm, không cập nhật kể cả khi được nhận; vì vậy kết quả này chưa mô tả nhiễm hồ sơ. Mục 2.15 xét riêng trường hợp attack được nhận có thể cập nhật. FRR của mô phỏng là tỷ lệ chính chủ cần bước thêm tại nhịp gõ, chưa là tỷ lệ từ chối cuối cùng. Web chỉ có OTP mô phỏng, chưa đo giao mã hoặc hiệu quả của một dịch vụ xác minh thật.

## Kết quả đáng chú ý

Bộ tự thu có 49/297 lượt chính chủ cần bước thêm, đồng thời nhận nhầm 284/1.050 hoặc 331/1.050 tùy kịch bản. Nhận được phần lớn chính chủ chưa đủ để kết luận mức nhận nhầm thấp. Dữ liệu kiểm lưu trữ và tài khoản thử được tách khỏi 597 mẫu nghiên cứu.

USN chỉ có 5 người chính chủ gõ sáu câu, tạo 30 hồ sơ người–câu. 2.042 dòng attack được chấm lại trên năm hồ sơ tương ứng; 10.210 quyết định không phải 10.210 người độc lập. Thứ tự dòng không tự chứng minh thời gian thu hoặc nhiều ngày. Các quy tắc phát triển sau khi xem USN được ghi là hồi cứu.

Hình D.1 biểu diễn điểm OOF từ mẫu đăng ký và ngưỡng thô tương đương, không phải điểm attack. Một chiều Ctrl–Alt chạm sàn trong fold tạo điểm OOF rất lớn ở ba hồ sơ. Ví dụ đại số giải thích ảnh hưởng lên mean/SD, với điều kiện sàn SD và điểm thô được nêu rõ. Ví dụ nhân tạo không thay các điểm thật thành số 0 và không phải thuật toán mới.

Bảng E.1 cho thấy 1.020 quyết định giả mạo chuyển sang xác minh nhưng thêm 540 lượt chính chủ cũng phải xác minh. Còn 374 quyết định giả mạo qua nhịp gõ. Tỷ lệ 3,66% qua nhịp gõ chưa phải FAR toàn hệ thống; 42,81% chính chủ cần xác minh chưa phải FRR cuối cùng vì chưa có kết quả bước bổ sung. Không cảnh báo cũng chưa chứng minh hồ sơ an toàn.

## Đối chiếu trước khi nộp

Bảng E.2 giữ đủ sáu trường hợp bỏ câu khỏi phép cộng. Khi bỏ Ob$erv3r, cả trước và sau quy tắc đều còn 371/8.510 lượt giả mạo qua trực tiếp và 1.470/4.500 lượt chính chủ cần xác minh thêm. Đây là bằng chứng tác động hiện tại tập trung ở một câu, chưa là cải thiện trên các câu khác. Việc bỏ nhóm chỉ thay bảng cộng, không học lại mô hình hoặc thay kết quả chính. [Kết quả và giới hạn](../research/docs/GROUP_SENSITIVITY_RESULTS_20261124.md).

Năm cách đặt cùng 20 mẫu cho cảnh báo không đổi ở 132 hồ sơ, nhưng tỷ số ngưỡng thô max/min trong một hồ sơ đạt tới 2,57 ở KeyRecs. Cảnh báo ổn định và thang hiệu chỉnh ổn định là hai khía cạnh khác nhau. Đảo thứ tự là kiểm soát giữ tập fold; dịch vòng làm thay đổi biên fold. Năm cách không chứng minh mọi phân hoạch đều như nhau; trong dữ liệu giả, tách hai giá trị hiếm sang fold khác có thể đổi cảnh báo. Không chấm lại FAR/FRR bằng thang mới.

Audit bổ sung không có cảnh báo ở 36 hồ sơ CMU và 66 hồ sơ KeyRecs, chỉ dùng mẫu đăng ký DEV; điều này chưa chứng minh các hồ sơ an toàn. Sau khi giữ nguyên bước cảnh báo, 305/374 quyết định giả mạo còn qua nhịp gõ thuộc hồ sơ đích participant5. AUC hai hồ sơ lớn nhất là 0,9424 và 0,8670; khả năng xếp hạng và tỷ lệ nhận nhầm tại ngưỡng hiện tại là hai khía cạnh khác nhau. Không dùng các số vừa thấy để chọn ngưỡng rồi gọi là kiểm chứng độc lập mới.

Đọc Bảng 3.1 và chỉ ra được bằng chứng của từng mục tiêu. Các đối chứng không đạt vẫn trả lời câu hỏi nghiên cứu nếu mô tả đúng điều kiện và kết quả; chúng chưa xác lập một cải tiến đồng thời FAR–FRR nhất quán.

Mở các tệp được dẫn để kiểm lại số đếm, thay vì chỉ nhớ tỷ lệ trong báo cáo. Ví dụ: tính 49/297 và 284/1.050 từ tệp tổng hợp tự thu. [Hướng dẫn chạy và đối chiếu](RUNNING_AND_REPRODUCIBILITY.md) giúp kiểm phần công khai; dữ liệu raw và kết quả xác minh thật vẫn là các giới hạn riêng.
