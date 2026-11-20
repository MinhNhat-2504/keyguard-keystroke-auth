# Chất lượng đăng ký, chuẩn hóa điểm và cập nhật hồ sơ — 13/11/2026

Triển khai cả ba hướng người dùng đã chọn, độc lập với task Thư. Chỉ thêm nghiên cứu offline, số liệu tổng hợp và giao diện khám phá; **không đổi mô hình/ngưỡng sản phẩm, raw, kết quả cũ hoặc bản báo cáo 6 trang**. Không phải đánh giá mới trên dữ liệu chưa từng được xem.

## 1. Kiểm tra chất lượng 20 mẫu đăng ký

Giữ nguyên snapshot và chính sách lọc trước: 601 dòng gốc → 597 mẫu/15 mã, loại hai dòng khóa trùng P10 và hai dòng thiếu timestamp; sắp UTC. Mỗi mã luôn có 20 mẫu đầu làm enrollment, các mẫu sau vẫn chấm đủ 297 genuine. Không xóa tài khoản hoặc loại mẫu genuine đánh giá vì điểm xấu.

So sánh hai quy tắc định trước:

- **Giữ cả 20 mẫu.** Baseline không đổi.
- **Lọc robust trên enrollment:** tâm theo chiều là median, scale là `max(1.4826 × MAD, 1e-9)`. Điểm mỗi mẫu là median của 31 độ lệch tuyệt đối đã chuẩn hóa. Cờ khi điểm lớn hơn `median(điểm) + 3 × max(1.4826 × MAD(điểm), 1e-9)`. Bỏ tối đa 20% số mẫu; nếu vượt ngân sách, lấy các điểm lớn nhất, hòa giữ thứ tự ổn định. Không ép loại nếu không có mẫu vượt ngưỡng.

Giữ tối thiểu **16/20** ở lần fit cuối. Trong mỗi fold CV, quy tắc được tính lại **chỉ trên các mẫu huấn luyện fold đó** và vẫn giữ ít nhất 80% số có sẵn. Mẫu validation không dùng để chọn mẫu, tâm hoặc scale của fold. Tính điểm held-out cho **toàn bộ 20 mẫu**, kể cả mẫu bị cờ ở fit cuối, tránh tự bỏ điểm khó khi hiệu chỉnh.

Quy tắc giữ **278/300** mẫu đăng ký trên 15 mã; P10 giữ 16/20, P03/P04 giữ 18/20, P12 giữ 17/20 và các mã khác 19/20. Raw vẫn nguyên vẹn. Mẫu bị cờ chỉ là bất thường theo quy tắc định nghĩa, không xác nhận sai thao tác, khác người hoặc sai thiết bị. Vị trí được ghi theo thứ tự trong 20 mẫu enrollment, không phải rep gốc.

## 2. Chuẩn hóa điểm ổn định hơn

Mọi phương án dùng Scaled Manhattan/31 đặc trưng thời gian gốc. Điểm CV enrollment dùng 5 fold liên tiếp theo thứ tự mẫu (cùng baseline); không phải kiểm định drift theo thời gian. So sánh:

| Cách | Tâm | Độ phân tán |
|---|---|---|
| Mean/Std | mean điểm CV | std tổng thể, ddof=0 |
| Median/MAD | median điểm CV | 1,4826 × median độ lệch tuyệt đối |
| Median/IQR | median điểm CV | (Q75−Q25)/1,349, quantile tuyến tính mặc định NumPy |

Sàn độ phân tán điểm là `1e-6` như baseline. Các hệ số là quy ước định trước để khảo sát scale, không khẳng định điểm có phân phối chuẩn. Không sử dụng genuine test để chuẩn hóa hoặc chọn ngưỡng.

**6 phương án = 2 quy tắc chất lượng × 3 chuẩn hóa điểm.** Giữ phân vùng 3 vòng ngoài (10 mã dev/5 test) và 2 vòng trong từ nghiên cứu cũ; impostor chỉ lấy trong cùng phân vùng. 20 mẫu đầu enrollment, hồ sơ cố định; 5 đầu và 5 cuối của 4 mã khác → 40 impostor/tài khoản test. Tổng **297 genuine/600 impostor**.

Vòng trong chọn phương án bằng trung bình `(FAR+FRR)/2`; hòa theo tên. Ngưỡng từng lần chỉ lấy từ impostor dev, giữ FAR thực nghiệm ≤5%, không tách điểm trùng. Chọn lại ngưỡng trên toàn bộ 10 mã dev rồi đánh giá nhóm ngoài. Không chọn phương án theo bảng outer-test.

| Phương án khảo sát | Nhận nhầm / 600 | Genuine cần xác minh / 297 |
|---|---:|---:|
| Giữ20, Mean/Std — baseline | 46 = **7,67%** | 193 = **64,98%** |
| Giữ20, Median/MAD | 39 = **6,50%** | 199 = **67,00%** |
| Giữ20, Median/IQR | 33 = **5,50%** | 203 = **68,35%** |
| Lọc robust, Mean/Std | 36 = **6,00%** | 182 = **61,28%** |
| Lọc robust, Median/MAD | 25 = **4,17%** | 175 = **58,92%** |
| Lọc robust, Median/IQR | 29 = **4,83%** | 178 = **59,93%** |
| **Chọn qua vòng trong** | **52 = 8,67%** | **180 = 60,61%** |

Vòng trong lần lượt chọn `keep_all__mean_std`, `robust_filter__median_iqr`, `robust_filter__mean_std`. Quy trình chọn giảm 13 lượt genuine cần xác minh nhưng tăng 6 nhận nhầm so với baseline, chưa cải thiện đồng thời. Biến thể lọc/Median-MAD đáng nghiên cứu vì kết quả mô tả tốt hơn trên bộ này; **không dùng chính bảng đã xem để tuyên bố đã chọn được mô hình triển khai có đánh giá độc lập**. Không tự sửa ngưỡng theo P10/P09.

Đáng chú ý: cùng biến thể lọc/Median-MAD, **P10 có FRR18/18=100%**, tăng so với baseline10/18, dù FAR của mã này giảm24/40 xuống0/40. Vì vậy cải thiện số tổng không bảo đảm mọi tài khoản dùng tốt hơn; không coi mẫu bị cờ là mẫu sai để xóa vĩnh viễn hoặc tự thay cấu hình đăng ký. Cần đánh giá cả chất lượng sử dụng theo mã khi xem phương án mới.

## 3. Mô phỏng rủi ro cập nhật hồ sơ bằng CMU

Thử hoàn toàn trên ma trận CMU, không gửi request đến ứng dụng hoặc website thật. Dùng 15 mã `test_users` có sẵn trong config; các mã này đã tham gia benchmark, không phải holdout mới. Tập gồm 15 cặp có hướng: tài khoản đích là từng mã, impostor là mã kế tiếp theo thứ tự tên (vòng lại ở cuối), **không chọn theo điểm hoặc tỷ lệ nhận nhầm**.

- Enrollment: 20 mẫu đầu phiên 1 của tài khoản đích.
- Genuine: 200 mẫu phiên 5–8 của tài khoản đích, theo phiên/rep. Không dùng 180 mẫu còn lại phiên 1–4 trong thí nghiệm này; đây không phải cùng lịch genuine của các mô phỏng cũ.
- Mẫu xen: 40 mẫu đầu phiên 1 của mã impostor, mỗi 5 genuine xen đúng một mẫu, không tối ưu hoặc chọn thích nghi theo phản hồi.
- Probe riêng: 10 mẫu cuối phiên 8 của mã impostor, không trùng mẫu xen, không cập nhật hồ sơ. Chấm ở mốc 0/50/100/150/200 genuine, sau mẫu xen ở mốc tương ứng. Các probe lặp lại không được cộng thành mẫu độc lập mới.
- Nhánh đối chứng chạy cùng chuỗi genuine nhưng không xử lý mẫu xen. Cùng 20 enrollment, window50 và ngưỡng nguồn **0,2720094565367825**, không chỉnh ngưỡng trong thí nghiệm này.

| Chính sách | Quy tắc cập nhật |
|---|---|
| Static | Không cập nhật |
| Accept | Mọi lượt được nhịp gõ nhận, kể cả impostor |
| Fallback | Mọi genuine được cập nhật vì giả định qua bước bổ sung; impostor cũng cập nhật nếu được nhịp gõ nhận |
| Verified-only | Chỉ genuine được cập nhật sau **bộ xác minh độc lập lý tưởng ở mọi lần cập nhật**; impostor không cập nhật dù nhịp gõ nhận |

Verified-only là đối chứng lý tưởng để cô lập đường cập nhật, không phải tuyên bố OTP thực tế xác nhận được nhãn. Giả định genuine luôn qua OTP ở fallback vẫn là giả định, không đo OTP trên người thật.

| Chính sách | Mẫu xen được nhận / 600 | Genuine cần xác minh có/không xen, mỗi nhánh 3.000 | Hồ sơ từng chứa impostor | Mẫu impostor còn cuối |
|---|---:|---:|---:|---:|
| Static | 71 | 1.813 / 1.813 | 0/15 | 0 |
| Accept | 13 | 1.557 / 1.566 | 3/15 | 0 |
| Fallback | 20 | 557 / 556 | 4/15 | 7 trong 1 hồ sơ |
| Verified-only | 21 | 556 / 556 | 0/15 | 0 |

Khác nhau về số nhận nhầm giữa các chính sách xuất hiện vì lịch sử hồ sơ khác. Không lấy việc FRR nhánh có xen giảm nhẹ ở accept làm bằng chứng tốt hơn, vì mẫu người khác đã lọt vào hồ sơ.

Probe cuối: static **19/150** ở cả hai nhánh; accept/fallback/verified-only cùng **0/150** ở cả hai nhánh. Không tài khoản nào có số probe được nhận ở mốc cuối tăng hay giảm do xen trong kịch bản này. Ở mốc 50, fallback nhánh xen nhận 10/150 probe so với 8/150 ở đối chứng; có thể có khác biệt tạm thời. Không suy ra có mẫu impostor trong hồ sơ thì chắc chắn chiếm tài khoản, cũng không suy probe cuối 0 là an toàn. Tỷ lệ chỉ có điều kiện theo 15 mã impostor đã ghép, không so trực tiếp với FAR của tất cả mã khác ở thí nghiệm cũ.

**Kết luận:** đã quan sát đường cập nhật có thể đưa mẫu người khác vào hồ sơ, nhưng chưa thấy khuếch đại nhận probe ở cuối với lịch xen cố định này. Không thêm kịch bản tối ưu tấn công sau khi xem kết quả để tìm một con số lớn hơn. Mọi khảo sát mở rộng cần định trước lịch và phép đo, giữ đối chứng cùng genuine.

## Artifact, giao diện và tái lập

```powershell
./.venv/Scripts/python.exe scripts/run_enrollment_study.py
./.venv/Scripts/python.exe scripts/run_contamination.py
./.venv/Scripts/python.exe scripts/plot_enrollment_study.py
./.venv/Scripts/python.exe -m pytest tests/test_enrollment_study.py tests/test_diagnostics.py tests/test_research.py tests/test_model.py tests/test_collected.py tests/test_live_evidence.py tests/test_features.py tests/test_simulation.py -q
node scripts/check_explorer.mjs
```

- `results/enrollment_study.json`, `enrollment_comparison.csv`: 6 phương án/18 hàng theo vòng, 90 chẩn đoán enrollment; lưu SHA config/code/nghiên cứu gốc và quy tắc.
- `results/contamination_study.json`, `contamination_checkpoints.csv`: 15 cặp × 4 chính sách × 2 nhánh × 5 mốc = **600 hàng**; lưu SHA config/code/CMU. Nhãn mẫu trong cửa sổ được theo dõi để đếm nhiễm; probe không bao giờ được thêm vào hồ sơ.
- `explorer/index.html` mục05: chọn phương án/tài khoản để xem số mẫu giữ/cờ và sai số. Mục06: chọn chính sách/tài khoản để so sánh hai nhánh theo mốc. Chỉ đọc dữ liệu tổng hợp tính sẵn, không thay mô hình.
- Hai hình riêng ở `figures/research/enrollment_quality.png`, `contamination_paired.png`, có thể dùng cho báo cáo.

**Kiểm chứng:** 36 test liên quan đạt, 4 subtest; 8 test mới gồm baseline khớp profile cũ, quy tắc lọc có trần/không đọc test, lọc lại trong từng fold, scale khi điểm trùng, truth table cập nhật, đối chứng static/verified không đổi và cửa sổ chứa mẫu impostor. Chrome kiểm tra 90 chi tiết đăng ký và 64 tổ hợp chính sách–tài khoản cùng các mục nghiên cứu cũ, mobile390px không tràn. Không chạy lại benchmark 4 họ hoặc suite sklearn.

Thư vẫn theo các việc đã chấm ở mục17 file chấm, không làm thay trong lượt này. Điểm rubric gốc không tự tăng vì thêm nghiên cứu. Bước thực tế tiếp theo là chốt mức FAR/FRR chấp nhận được cho demo và thiết kế phép kiểm chứng mới trước khi cân nhắc cấu hình; chưa tự triển khai phương án có số đẹp nhất.

**Điều chỉnh mục tiêu theo người dùng sau mốc này:** không có mục tiêu vận hành demo; phần phát triển tiếp ưu tiên cải tiến phương pháp và thực nghiệm. Đã làm trọng số mềm,10 cách chia mã và thích nghi theo phiên tại [SOFT_WEIGHT_STABILITY_AND_ADAPTATION.md](SOFT_WEIGHT_STABILITY_AND_ADAPTATION.md). Báo cáo đầy đủ hiện32 trang; các mốc29 trang/36 test ở tài liệu này là lịch sử trước nghiên cứu tiếp.
