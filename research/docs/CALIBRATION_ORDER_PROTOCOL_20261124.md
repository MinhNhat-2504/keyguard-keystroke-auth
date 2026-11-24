# Độ nhạy của CV với cách đặt biên fold

Phân tích hồi cứu, chỉ dùng cùng 20 mẫu đăng ký của 36 DEV CMU, 66 DEV KeyRecs và 30 hồ sơ USN đã xem. Không mở TEST, đọc quyết định đánh giá, chọn ngưỡng mới hoặc đổi quy tắc cảnh báo. Không tạo phiên/ngày mới bằng đổi thứ tự; các phép đổi thứ tự chỉ kiểm cấu trúc fold của CV, không mô phỏng sử dụng theo thời gian.

Định trước đúng năm cách: thứ tự gốc; đảo toàn bộ 20 hàng để kiểm soát (giữ các tập fold, đổi thứ tự trình bày); dịch vòng sang trái 1, 2 và 3 hàng rồi chia năm khối liên tiếp, mỗi khối bốn hàng. Ba cách dịch làm thay đổi biên fold. Đây không phải mọi phân hoạch có thể có, không dùng random seed hoặc chọn kết quả thuận lợi.

Giữ Scaled Manhattan, sàn MAD 1e-9, sàn SD 1e-6, 5 fold và ngưỡng đã lưu. Mỗi cách chạy đúng hàm `audit_calibration`. Báo cảnh báo, mean/SD OOF, điểm OOF đưa về vị trí hàng gốc và ngưỡng thô tương đương. So tham số hồ sơ học đủ 20 mẫu để phân biệt thay đổi do phân hoạch CV với thay đổi dữ liệu. Đảo thứ tự là kiểm soát kỳ vọng tương đương trong sai số float; mọi sai khác phải được báo, không loại.

Báo đủ 132 hồ sơ và năm cách, số cảnh báo theo nguồn/cách, hồ sơ đổi trạng thái cảnh báo, khoảng và tỷ số lớn nhất/nhỏ nhất của ngưỡng thô. Các thống kê mô tả không tạo cách gộp cảnh báo hoặc chọn thứ tự mới cho hệ thống. Không tính FAR/FRR mới từ các thang chuẩn hóa vừa có; ngưỡng/thang dùng trong kết quả lịch sử được giữ nguyên. Tỷ lệ cảnh báo không phải false-positive rate hoặc chứng nhận an toàn.

Kiểm dữ liệu giả trước khi khóa và chạy: đảo thứ tự giữ phân hoạch; một ngoại lệ đơn lẻ; hai ngoại lệ cùng fold bị tách khi dịch; đầu vào không bị sửa; vị trí OOF được trả về hàng gốc; dữ liệu sai dạng/không hữu hạn phải lỗi. Khóa mã/test/protocol/input/môi trường và không ghi đè. Đối chiếu raw bằng phép tính mean/MAD/CV thuần Python; input reader DEV dùng lại bản đã được kiểm độc lập trước đó, không tự nhận hai pipeline hoàn toàn độc lập.
