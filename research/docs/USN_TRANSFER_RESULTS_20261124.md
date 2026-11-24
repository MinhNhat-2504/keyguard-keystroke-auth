# Kết quả kiểm tra quy tắc cố định trên USN

Đã chấm nguồn USN phiên bản 1 sau khi audit schema và khóa protocol/mã/raw/ngưỡng. 10 kiểm thử giả lập đạt trước khóa; chưa có điểm mô hình USN được xem ở bước đặt kế hoạch. Giữ ngưỡng CMU 0,2720094565367825 và học hồ sơ riêng cho từng người–câu từ 20 dòng đầu, không cập nhật, không chọn lại ngưỡng hoặc câu thuận lợi sau khi có kết quả.

| Câu gõ theo tên tệp nguồn | Chiều | Nhận nhầm | FAR (%) | Chính chủ từ chối | FRR (%) | Hồ sơ FAR >5% |
|---|---:|---:|---:|---:|---:|---:|
| flying automatic monster | 73 | 34/1.700 | 2,00 | 194/900 | 21,56 | 1/5 |
| Gigab-exclm-t R3ceiver | 58 | 27/1.610 | 1,68 | 182/900 | 20,22 | 0/5 |
| gigabit receiver | 49 | 144/1.750 | 8,23 | 346/900 | 38,44 | 2/5 |
| Ob-dollar-erv3r | 34 | 1.023/1.700 | 60,18 | 302/900 | 33,56 | 3/5 |
| observer | 25 | 146/1.750 | 8,34 | 400/900 | 44,44 | 1/5 |
| repetition learn machine thinker | 97 | 20/1.700 | 1,18 | 348/900 | 38,67 | 1/5 |

Mỗi câu có cùng số lượt trong 5 hồ sơ nên FAR/FRR trung bình theo hồ sơ bằng tỷ lệ gộp theo câu. Tổng quan sát có 1.394/10.210 quyết định giả mạo được nhận, FAR gộp 13,65%; FAR trung bình 30 hồ sơ là 13,60%. Lượt chính chủ bị từ chối 1.772/5.400, FRR 32,81%. Có 8/30 hồ sơ vượt mức FAR tham chiếu 5%. Không có việc chọn ngưỡng USN theo các kết quả này.

Câu Ob$erv3r chiếm 1.023 trong 1.394 quyết định nhận nhầm dù chỉ có 1.700 trong 10.210 lượt chấm giả mạo. Sự tập trung này cho thấy cần báo riêng từng câu/tài khoản thay vì chỉ một tỷ lệ chung. Nó không xác định nguyên nhân là ký tự đặc biệt hoặc độ dài: còn khác người gõ, độ quen và phân bố mẫu; thí nghiệm không tách các yếu tố đó. Phạm vi chỉ là quy tắc và ngưỡng đang kiểm tra, không phải kết luận mọi mô hình nhịp gõ đều có lỗi tương tự.

Một số câu có FAR thấp hơn 5% nhưng FRR vẫn từ khoảng 20% đến gần 39%. Như vậy nhìn riêng FAR thuận lợi sẽ bỏ qua gánh nặng từ chối chính chủ. Ngược lại, dữ liệu có cùng máy/PS2 vẫn cho kết quả rất khác theo câu và hồ sơ, nên việc khống chế thiết bị chưa đủ để bảo đảm ngưỡng chung phù hợp. Không dùng những quan sát này để gọi phương pháp mới tốt hơn hoặc đưa hệ thống vào sử dụng.

Kho nguồn được bài chính thức DOI 10.1007/s12243-024-01039-z dẫn trực tiếp, có phiên bản DOI10.23642/usn.23790858.v1/CC BY4.0 và toàn bộ MD5 khớp. Tuy vậy, chỉ 5 người chính chủ gõ 6 câu tạo 30 hồ sơ, không phải 30 người. 2.042 dòng attack được chấm lại ở 5 hồ sơ tương ứng nên 10.210 quyết định không độc lập. Mỗi câu thu một phiên, tệp chính chủ không có timestamp; chia đầu/cuối chỉ theo thứ tự tệp, không chứng minh thứ tự thời gian hoặc nhiều ngày. Không chuyển nguyên hồ sơ/vector CMU, mà kiểm quy tắc trên 25–97 đặc trưng nguồn giữ cả Shift.

Nhánh chọn mẫu đại diện không được chấm trên USN vì đã trượt cổng DEV. Đánh giá này là câu hỏi khác: kiểm quy tắc cố định hiện có trên một nguồn trước đó chưa chấm. Sau lượt này, USN đã được xem; các thay đổi tiếp theo dùng kết quả USN phải gọi là phát triển tiếp. Không gọi phép đánh giá là tái lập kết quả tác giả vì detector, ngưỡng và cách chia khác bài gốc.

Nguồn và dữ liệu loại ghi trong `results/usn_source_manifest_20261124.json`, `results/usn_schema_audit_20261124.json`; hồ sơ khóa/kết quả/score có prefix `results/usn_transfer_20261124_`. Script audit độc lập `scripts/audit_usn_transfer_20261124.py` áp lại ngưỡng cho toàn bộ quyết định rồi cộng bảng theo tài khoản/câu. Không công khai raw hoặc thông tin kết nối. Cấu hình ứng dụng và các kết quả lịch sử giữ nguyên.
