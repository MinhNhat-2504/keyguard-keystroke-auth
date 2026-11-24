# Kết quả kiểm tra cảnh báo trên DEV

Giữ nguyên quy tắc cảnh báo đã xây từ chẩn đoán USN. Audit dùng đủ 36 hồ sơ DEV CMU và 66 hồ sơ DEV KeyRecs theo kế hoạch phân vùng cũ; các nguồn này đã được xem nên đây không phải kiểm chứng độc lập mới. Mỗi hồ sơ dùng 20 mẫu đầu session 1 theo repetition, tổng cộng 2.040 mẫu. Không chấm TEST hoặc session 2, không chọn lại ngưỡng và không chạy xác minh OTP.

| Nguồn | Hồ sơ DEV | Mẫu đăng ký | Hồ sơ cảnh báo |
|---|---:|---:|---:|
| CMU | 36 | 720 | 0 |
| KeyRecs | 66 | 1.320 | 0 |
| Tổng | 102 | 2.040 | 0 |

Không hồ sơ nào có ngoại suy qua sàn trong fold hoặc độ lệch chuẩn OOF chạm sàn theo quy tắc cố định. Đây là độ bao phủ cảnh báo trên phần đăng ký, không phải tỷ lệ false positive bằng 0, FAR bằng 0 hoặc chứng nhận 102 tài khoản an toàn. Audit chưa đo số lượt xác minh khi có đăng nhập thực tế. Nó cũng không loại khả năng các kiểu lỗi khác gây nhận nhầm dù không xuất hiện cảnh báo này.

Trước lượt audit, 9 ca reader và 18 ca preflight cũ đạt; mã/protocol/input/môi trường được khóa. Reader được kiểm để chỉ chuyển timing của 20 mẫu DEV session 1 thành số, kể cả khi timing TEST hoặc session 2 trong fixture bị hỏng. Toàn tệp vẫn được đọc để kiểm hash và lọc metadata. Các cột KeyRecs trùng tên được giữ riêng theo vị trí, đúng adapter cũ.

Bộ kiểm độc lập ban đầu dùng tên cột ở KeyRecs nên gộp các cột trùng và báo lệch. Sau khi sửa bộ đối chiếu sang alias vị trí, phép tính thuần Python từ raw tái lập điểm OOF của cả 102 hồ sơ trong sai số float đã định. Kết quả runner chính không thay đổi. Một regression bổ sung về hai cột trùng tên có giá trị khác nhau đạt sau audit; không tính ca này thành kiểm thử trước khóa mã. Record `raw_audit.json` xác nhận hash raw và tính CV lại; `saved_audit.json` chỉ đối chiếu artifact khi không có raw.

Artifact prefix `results/preflight_dev_audit_20261124_`. Runner: `python -m scripts.run_preflight_dev_audit_20261124 --check`; `--run` từ chối ghi đè. Kiểm công khai: `python scripts/verify_preflight_dev_audit_20261124.py --saved-only`. Kiểm raw local: thay bằng `--check-raw`. Không sửa detector, cảnh báo, báo cáo lịch sử, kết quả USN hoặc dịch vụ thật.
