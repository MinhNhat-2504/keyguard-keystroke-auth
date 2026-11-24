# Độ nhạy của bảng tổng hợp USN theo nhóm

Phân tích hồi cứu sau khi đã xem USN và các chẩn đoán trước. Chỉ đọc số đếm định tuyến đã lưu; không fit mô hình, đổi ngưỡng, thay cảnh báo hoặc chấm dữ liệu mới. Không chọn phương án từ phân tích này.

Giữ đủ 30 hồ sơ (5 mã đích × 6 câu). Tổng hợp theo cả năm mã đích và cả sáu câu; sau đó lần lượt bỏ từng mã đích hoặc từng câu khỏi phép cộng. Mỗi trường hợp có mẫu số riêng. Báo cả trước và sau quy tắc chuyển sang xác minh bổ sung: số attack qua trực tiếp và số genuine cần xác minh thêm. Dùng tỷ lệ gộp theo số lượt, không gọi là trung bình không trọng số theo hồ sơ.

Bỏ mã đích chỉ loại các quyết định chấm vào hồ sơ đích đó; không loại mọi dữ liệu của một người, không học lại mô hình và không là leave-one-person-out cross-validation. Giữ cả 5 và 6 trường hợp loại nhóm, không bỏ riêng nhóm lỗi cao để công bố kết quả tốt hơn. Khoảng nhỏ nhất–lớn nhất chỉ mô tả ảnh hưởng nhóm trong bộ đã có, không là khoảng tin cậy hoặc bằng chứng chuyển sang quần thể mới. Cùng mẫu attack có thể được chấm cho nhiều đích.

Kiểm thử dữ liệu giả trước khi khóa code và input. Runner từ chối ghi đè. Đối chiếu độc lập đọc các quyết định gốc cùng map cảnh báo để cộng lại từng trường hợp bằng vòng lặp riêng; không gọi hàm tổng hợp của runner. Không suy diễn tỷ lệ qua sau chuyển tuyến thành FAR toàn hệ thống, vì chưa đo kết quả xác minh bổ sung.
