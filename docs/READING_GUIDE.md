# Hướng dẫn đọc báo cáo

Nên bắt đầu từ Tóm tắt, mục 1.2 và Bảng 3.1 để nắm bài toán, phần nhóm thực hiện và kết quả tương ứng. Sau đó đọc các phép đánh giá dưới đây. [Báo cáo đầy đủ](../reports/KeyGuard_BaoCao_NopLai_v9_20261124.pdf) có bảng, hình và tài liệu tham khảo.

## Đọc theo câu hỏi nghiên cứu

| Câu hỏi | Vị trí trong báo cáo | Bằng chứng để mở cùng |
|---|---|---|
| Cấu hình CMU có giữ mức lỗi trên bộ tự thu không? | Mục 2.7–2.8 | [Tổng hợp 597 mẫu](../research/results/collected_preliminary_summary.json) |
| Từng thay đổi có tốt hơn đối chứng trong cùng điều kiện không? | Mục 2.15–2.30, Bảng 2.29 | [Đối chứng chọn mẫu đăng ký](../research/docs/ENROLLMENT_SELECTION_RESULTS_20261124.md) |
| Quy tắc cố định hoạt động ra sao trên nguồn khác? | Mục 2.31 | [Protocol USN](../research/docs/USN_TRANSFER_PROTOCOL_20261124.md) và [kết quả](../research/docs/USN_TRANSFER_RESULTS_20261124.md) |
| Vì sao chuẩn hóa CV có thể quá dễ nhận? | Bảng 2.33, Phụ lục D | [Chẩn đoán](../research/docs/USN_SENSITIVITY_RESULTS_20261124.md), [giải thích đại số](../research/docs/CALIBRATION_INFLUENCE_NOTE_20261124.md) |
| Bước cảnh báo đổi luồng xác minh như thế nào? | Phụ lục E | [Kiểm tra đăng ký](../research/docs/CALIBRATION_PREFLIGHT_RESULTS_20261124.md), [đếm tuyến xử lý](../research/docs/CALIBRATION_ROUTING_RESULTS_20261124.md) |

## Những khái niệm cần phân biệt

Với chuỗi chính gồm 10 ký tự và Enter, thư viện tạo 11 thời gian giữ phím, 10 khoảng nhấn–nhấn và 10 khoảng nhả–nhấn: tổng cộng 31 chiều. Khoảng nhả–nhấn có thể âm khi hai phím chồng nhau. Các nguồn khác có schema và số chiều riêng; khi chuyển quy tắc chấm, nhóm học hồ sơ theo dữ liệu nguồn đó.

Scaled Manhattan đo độ lệch so với tâm và độ biến thiên của mẫu đăng ký. Trong baseline, MAD là độ lệch tuyệt đối **trung bình** quanh trung bình; một số biến thể robust dùng trung vị. Hai định nghĩa này khác nhau. Điểm thô được chuẩn hóa bằng điểm OOF từ các mẫu đăng ký giữ ra trong CV, rồi so với ngưỡng z. Điểm hoặc confidence hiển thị chưa phải xác suất danh tính đã hiệu chuẩn.

FAR đo việc nhận nhầm người khác; FRR ở các bảng chấm nhịp gõ đo chính chủ không được nhận trực tiếp. EER/AUC nói về nhiều ngưỡng, còn FAR/FRR được báo tại ngưỡng cụ thể. Muốn so sánh hai hàng phải xem cùng cách chia dữ liệu, lịch cập nhật, đối tượng và cách gộp tỷ lệ.

Trong mô phỏng fallback, việc cập nhật mẫu genuine dùng giả định xác minh bổ sung đáng tin cậy. Web chỉ có OTP mô phỏng. Các kết quả này có phạm vi khác với việc đánh giá một dịch vụ xác minh thật.

## Kết quả đáng chú ý

Bộ tự thu có 49/297 lượt chính chủ cần bước thêm, đồng thời nhận nhầm 284/1.050 hoặc 331/1.050 tùy kịch bản. Nhận được phần lớn chính chủ chưa đủ để kết luận mức nhận nhầm thấp. Dữ liệu kiểm lưu trữ và tài khoản thử được tách khỏi 597 mẫu nghiên cứu.

USN chỉ có 5 người chính chủ gõ sáu câu, tạo 30 hồ sơ người–câu. 2.042 dòng attack được chấm lại trên năm hồ sơ tương ứng; 10.210 quyết định không phải 10.210 người độc lập. Thứ tự dòng không tự chứng minh thời gian thu hoặc nhiều ngày. Các quy tắc phát triển sau khi xem USN được ghi là hồi cứu.

Hình D.1 biểu diễn điểm OOF từ mẫu đăng ký và ngưỡng thô tương đương, không phải điểm attack. Một chiều Ctrl–Alt chạm sàn trong fold tạo điểm OOF rất lớn ở ba hồ sơ. Ví dụ đại số giải thích ảnh hưởng lên mean/SD, với điều kiện sàn SD và điểm thô được nêu rõ. Ví dụ nhân tạo không thay các điểm thật thành số 0 và không phải thuật toán mới.

Bảng E.1 cho thấy 1.020 quyết định giả mạo chuyển sang xác minh nhưng thêm 540 lượt chính chủ cũng phải xác minh. Còn 374 quyết định giả mạo qua nhịp gõ. Tỷ lệ 3,66% qua nhịp gõ chưa phải FAR toàn hệ thống; 42,81% chính chủ cần xác minh chưa phải FRR cuối cùng vì chưa có kết quả bước bổ sung. Không cảnh báo cũng chưa chứng minh hồ sơ an toàn.

## Đối chiếu trước khi nộp

Đọc Bảng 3.1 và chỉ ra được bằng chứng của từng mục tiêu. Các đối chứng không đạt vẫn trả lời câu hỏi nghiên cứu nếu mô tả đúng điều kiện và kết quả; chúng chưa xác lập một cải tiến đồng thời FAR–FRR nhất quán.

Mở các tệp được dẫn để kiểm lại số đếm, thay vì chỉ nhớ tỷ lệ trong báo cáo. Ví dụ: tính 49/297 và 284/1.050 từ tệp tổng hợp tự thu. [Hướng dẫn chạy và đối chiếu](RUNNING_AND_REPRODUCIBILITY.md) giúp kiểm phần công khai; dữ liệu raw và kết quả xác minh thật vẫn là các giới hạn riêng.
