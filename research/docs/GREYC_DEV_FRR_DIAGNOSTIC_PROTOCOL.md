# Chẩn đoán FRR baseline trên DEV GREYC-Web — 15/11/2026

Mục đích: mô tả nơi xuất hiện genuine rejection và kiểm tra cơ chế chuẩn hóa trên **42 tài khoản DEV đã khóa**, trước khi đề xuất cải tiến. Đây là chẩn đoán hậu nghiệm, không phép thử giả thuyết mới hay kiểm chứng độc lập.

- Chỉ baseline Scaled Manhattan, profile tĩnh20 mẫu, cùng CV5fold và chuẩn hóa mean/population SD; không candidate, cập nhật profile, dò λ hay thử ngưỡng khác.
- Ngưỡng lấy nguyên giá trị calibration baseline đã lưu. Tính lại số impostor DEV được nhận tại ngưỡng đó để kiểm tái lập; **không gọi hàm chọn ngưỡng**.
- Tạo bản chiếu dữ liệu DEV riêng trong thư mục ignored, chỉ chọn mã ở dev_ids. Không gọi evaluator TEST, không đọc điểm theo tài khoản TEST để phân nhóm hoặc thiết kế cải tiến. Loader có kiểm disjoint dev/test và từ chối mã ngoài DEV trong hàm chẩn đoán.
- Ba nhóm genuine báo riêng: enrollment chấm trên full-profile (resubstitution, lạc quan), điểm OOF20 (profile16 mẫu, đã dùng chuẩn hóa), và capture DEV ở ngày lịch muộn hơn enrollment (profile20 mẫu). Không gọi enrollment/OOF là validation độc lập; không suy FRR DEV thành FRR TEST.
- Theo từng mã: số mẫu/lỗi và FRR, phân vị raw/z, OOF mean/SD, SD chạm sàn1e−6, raw cutoff tương đương `mean_OOF + tau*SD_OOF`, MAD full-profile chạm sàn1e−9. Không thay cutoff này; nó chỉ là cách viết lại cùng quyết định.
- Theo thời gian: các khoảng1–7,8–30,≥31 ngày lịch kể từ ngày mẫu enrollment20, chốt trước chạy. Báo số mã có dữ liệu, pooled và macro trên mã có dữ liệu trong mỗi khoảng. Thành phần mã khác nhau giữa khoảng nên không kết luận quan hệ nhân quả theo tuổi hồ sơ.
- Theo đặc trưng: bốn nhóm nguồn PP/PR/RP/RR, số chiều5/6/5/5; chia sẻ đóng góp tuyệt đối theo tổng khoảng cách, và dịch chuyển median feature ở ngày sau chia local MAD. Giữ nghĩa vector nguồn, không gán mỗi nhóm thành hold cùng phím. Dịch chuyển chuẩn hóa không chứng minh nguyên nhân; không chọn nhóm bỏ đi từ kết quả này.
- Lưu đủ42 mã, không chỉ các mã lỗi lớn; điểm từng lượt/raw vector giữ local ignored. Biểu đồ hoặc bảng chỉ mô tả, không CI/p-value/causal attribution.

Giới hạn: bộ DEV đã dùng hiệu chỉnh impostor, các probe DEV từ enrollment của mã khác; enrollment có thể nhiều ngày, loại bỏ schema và thiết bị không kiểm soát như audit gốc. Thay đổi được nghĩ ra từ chẩn đoán này là **phát triển**, cần protocol riêng trước scoring; GREYC-Web/CMU/KeyRecs đã xem không trở thành test mới.

Bảo toàn source/model/config, freeze/results TEST, raw, báo cáo6/37/40trang và ZIPv2; không sửa điểm, push, deploy hoặc DB. Đầu ra mới dùng prefix `greyc_dev_frr_`; không ghi đè thí nghiệm cũ.
