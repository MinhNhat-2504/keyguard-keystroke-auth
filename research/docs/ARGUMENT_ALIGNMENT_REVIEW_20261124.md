# Đối chiếu câu hỏi, kết quả và quyết định

Lượt này biên tập lập luận trong Tóm tắt, mục 1.2, 3.1 và 3.4; không chạy thêm mô hình hoặc thay số liệu, bảng, hình và công thức. Ba câu hỏi đã được nêu trong báo cáo, không nhận là giả thuyết mới được đăng ký từ đầu dự án.

| Câu hỏi | Phép kiểm và kết quả dùng trong kết luận | Quyết định tương ứng |
|---|---|---|
| Cấu hình CMU giữ được mức lỗi ở bộ tự thu? | FAR CMU 1,49%; bộ tự thu 27,05–31,52%, FRR 19,21% và 16,50%; điều kiện và lịch chấm khác nhau | Cần đánh giá trên dữ liệu phù hợp; không quy chênh lệch cho riêng thiết bị hoặc lấy tỷ lệ CMU làm cam kết |
| Quy tắc cải tiến có giảm cả hai loại lỗi trong cùng điều kiện? | Đối chứng CV giữ chung detector/điểm/ngưỡng z: CMU nhận nhầm 62→43/2.100 nhưng genuine không được nhận 201→213/750; KeyRecs 451→515/10.560 và 1.609→1.697/3.301 | Không đạt tiêu chí của quy tắc đã thử; giữ baseline, không suy mọi quy tắc chuẩn hóa đều vô ích |
| Lợi ích giữ qua nhóm và nguồn? | Quy tắc cảnh báo USN chỉ thay tuyến ở P1–P3 Ob$erv3r, 1.020 attack và 540 genuine cần thêm; vẫn có 349/2.042 mẫu qua ít nhất một trong năm đích, tạo 374 quyết định | Giữ prototype nghiên cứu, chưa xem là cải thiện toàn luồng hoặc hiệu quả trên các câu khác |

Số đếm đối chứng CV lấy từ `results/cv_aggregation_control_results.json`, đồng thời đã có ở Bảng 2.22 và tài liệu nguồn [9]. Các chỉ số còn lại dùng đúng artifact đã dẫn trong báo cáo. Bảng 3.1 tiếp tục đối chiếu đủ sáu mục tiêu triển khai/đánh giá với bằng chứng; không dùng số test chức năng thay bằng chứng FAR/FRR.

Phần đóng góp được viết theo những việc nhóm tự thực hiện: thư viện, ứng dụng, đối chứng giữ điều kiện và chẩn đoán số học có thể kiểm lại. Không nhận là thuật toán đầu tiên hoặc kết quả mới của toàn lĩnh vực. Tóm tắt tập trung vào câu trả lời và giới hạn; các kiểm tra phụ vẫn ở thân bài/phụ lục để tránh lấn át kết quả chính.
