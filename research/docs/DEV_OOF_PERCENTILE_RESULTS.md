# Đối chứng phân vị OOF trên DEV — 15/11/2026

Chỉ thay chuẩn hóa mean/SD bằng midrank percentile của cùng20điểmOOF; detector/full-profile/CV và probe giữ chung. Thiết kế đã ghi trước scoring;4/4test tổng hợp đạt,khóa code/input/env trước run. Chia42DEV thành28calibration/14evaluation theo thứ tự đã chốt. **Đây là phát triển trên DEV đã xem**, không nguồn kiểm chứng mới hoặc test14người chưa biết.

Hiệu chỉnh ngưỡng riêng từng nhánh theo cùng ngân sách FARcalibration≤5%, không chia ties. Thang điểm khác nhau nên không so trị số ngưỡng trực tiếp. Ngưỡng và kết quảTEST21mã của thí nghiệmGREYC cũ không sửa/chấm lại.

Kết quả candidate−baseline: **ΔFRR macro −1,4886điểm phần trăm**, **ΔFAR macro +0,9890điểm phần trăm**. Chỉ **2/14**mã giảmFRR màFARkhôngtăng. Không đạt tiêu chíFRRgiảm/FARkhôngtăng hoặc lợiđa số.

| Nhánh | FAR macro | FRR macro | Nhận nhầm | Genuine bị từ chối | Nhận nhầm calibration |
|---|---:|---:|---:|---:|---:|
| Baseline | 3,08% | 74,03% | 56/1820 | 923/1125 | 378/7560 =5,00% |
| Phân vị OOF | 4,07% | 72,54% | 74/1820 | 897/1125 | 296/7560 =3,92% |

Candidate dùng ít hơn ngân sách calibration do điểm trùng/thang rời rạc; không nới ngưỡng hoặc chia ties để ép đủ5%. Cùng ngân sách không đồng nghĩa FARcalibration hai nhánh bằng nhau. Số đếmgenuine làpooled, khác tỷ lệmacro do mỗi mã có sốlượt khác nhau. Không so trực tiếp baseline14DEVnày với baseline21TESTởnghiêncứucũ.

Do đó **giữ baseline sản phẩm**, không tune công thức phân vị/ngưỡng từ kết quả vừa xem. Phân vị có bão hòa ngoài khoảngOOF và lượng20điểm gây thang rời rạc; đó là giới hạn thiết kế, chưa chứng minh là nguyên nhân đánh đổi quan sát. Không suy rằng mọi chuẩn hóa theo phân vị đều kém hơn.

Artifact đầy đủ: `results/dev_oof_percentile_results.json` chứa counts từngmã/grid3×3/quantile/macro/pooled; `checks.json` chứa bảng tóm tắt và phép tính độc lập từ số đếm; `account_deltas.csv` công bố đủ14mã; `freeze.json`, `tests.json`, `started.json` giữ chronology/hash. Test synthetic kiểm ties/out-of-range/monotonic/affineinvariance/baselineparity. Kiểm số đếm14cặp/phân sốmacro và chronology đạt.

Kiểm integrity: `python scripts/dev_oof_percentile.py --check`; không chạy lại --run để ghi đè. Không thayreport6/37/40,raw/model/config/TEST hoặc điểm sau100. Khôngpush/deploy/DBwrite.

Hướng tiếp nên chuyển sang rà độ tương thích biểu diễn feature/thiết bị bằng metadataDEV và tái lập nguồn, trước khi chọn thêm công thức chuẩn hóa. Không tiếp tục dò công thức chỉ để tạo kết quả thuận lợi; bất kỳ thay đổi nào cần protocol và đánh giá tách biệt phù hợp.
