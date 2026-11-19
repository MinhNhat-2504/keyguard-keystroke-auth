# Kết quả đối chứng chỉ thay cách tổng hợp điểm CV

Đã kiểm tra khóa và chạy `scripts/run_cv_aggregation_control.py --run` theo thiết kế đã lưu. Baseline tổng hợp đều tái lập đúng decay20 matched ở cả hai nguồn: ngưỡng, số đếm pooled, từng mã, cặp và dev. **Nhánh tổng hợp theo tuổi không đạt giả thuyết ở nguồn nào:** CMU có đánh đổi FAR–FRR; KeyRecs cả hai lỗi đều tăng.

## 1. Kết quả chính theo tiêu chí đã khóa

Hai nhánh dùng chung detector decay20, điểm raw/OOF, lịch sử và ngưỡngz trong mỗi nguồn. Chỉ thay mean/SD tổng hợp đều bằng mean/SD population có trọng số tuổi20. Tiêu chí chính: `Δmacro_FAR < 0` và `Δmacro_FRR ≤ 0`; Δ là candidate−baseline, xét từ phân số số đếm trước làm tròn.

| Nguồn | Tổng hợp CV | FAR macro | FRR macro | ΔFAR, điểm % | ΔFRR, điểm % |
|---|---|---:|---:|---:|---:|
| CMU | Đều |2,95%|26,80%|—|—|
| CMU | Theo tuổi |2,05%|28,40%|−0,905|+1,600|
| KeyRecs | Đều |4,27%|48,71%|—|—|
| KeyRecs | Theo tuổi |4,88%|51,37%|+0,606|+2,667|

CMU giảm FAR nhưng tăng FRR nên là **đánh đổi**, không đạt điều kiện FRR không tăng. KeyRecs không đạt điều kiện FAR giảm và cũng không đạt FRR không tăng. Không thêm dung sai, chọn nguồn thuận lợi hoặc đổi sang tiêu chí chỉ giảm FAR để tuyên bố cải thiện. Không được ủng hộ nhất quán trên hai nguồn.

## 2. Số đếm và FAR dev quan sát

| Nguồn | Nhánh | Dev nhận nhầm | Test nhận nhầm | Genuine S2 không được nhận |
|---|---|---:|---:|---:|
| CMU | Đều |630/12.600 =5,00%|62/2.100|201/750|
| CMU | Theo tuổi |492/12.600 =3,90%|43/2.100|213/750|
| KeyRecs | Đều |2.145/42.900 =5,00%|451/10.560|1.609/3.301|
| KeyRecs | Theo tuổi |1.522/42.900 =3,55%|515/10.560|1.697/3.301|

CMU giảm19 nhận nhầm nhưng tăng12 genuine không được nhận. KeyRecs tăng64 nhận nhầm và88 genuine không được nhận. Ngưỡng dùng chung giữ nguyên: CMU−0,09327790626776133, KeyRecs−0,35492309501165314. Không hiệu chỉnh lại candidate để ép FARdev5%.

FAR dev candidate giảm ở cả hai nguồn nhưng FAR test KeyRecs lại tăng. Vì vậy không lấy dev thuận lợi làm bằng chứng test tốt hơn. Đây là đối chứng tại cùng ngưỡngz baseline, **không phải so hai hệ thống cùng FARdev**. Nếu muốn so sau hiệu chỉnh riêng cần protocol khác, không sửa ngưỡng trong kết quả này.

FRR macro KeyRecs48,71→51,37% khác FRR pooled48,74→51,41% vì số genuine từng mã khác nhau. CMU có cùng50 genuine/mã nên macro bằng pooled. Giữ cả hai cách tổng hợp với nhãn riêng.

## 3. Các lượt và tài khoản đổi quyết định

| Nguồn | Nhận nhầm mới | Thu hồi nhận nhầm | Cả hai cùng nhận | Cả hai cùng từ chối |
|---|---:|---:|---:|---:|
| CMU |0|19|43|2.038|
| KeyRecs |96|32|419|10.013|

Trên CMU, FAR giảm ở7/15 mã và không tăng ở mã nào; FRR tăng9 mã, giảm5 mã và bằng1 mã. Trên KeyRecs, FAR giảm9 mã, tăng9 và bằng15; FRR tăng27 mã, giảm2 và bằng4. Trung bình không đủ để suy mọi tài khoản đều cùng chiều.

Ca p013 đã định là phân tích phụ: nhận nhầm giảm39→28/320, genuine không được nhận tăng40→41/100. Cải thiện FAR của riêng p013 không thay đánh giá toàn nguồn, và riêng mã này vẫn có đánh đổi FRR. Trong khi đó p045 tăng32 nhận nhầm, p012 tăng25 vàp009 tăng10. Không đặt ngoại lệ hoặc lựa chọn theo tên các mã này.

## 4. Kết luận được phép và hướng tiếp

Phép đối chứng dùng chung detector/điểm/lịch sử nên tách được tác động của **quy tắc tổng hợp mean/SD chung** trong pipeline tại ngưỡngz cố định. Chưa tách riêng mean với SD, chưa đánh giá sau hiệu chỉnh lại ngưỡng và chưa chứng minh nguyên nhân theo thiết bị hoặc người. Kết quả cụ thể không cho thấy quy tắc trọng số tuổi này cải thiện theo tiêu chí đã đặt; không suy mọi cách chuẩn hóa có trọng số đều không hiệu quả.

Giữ cấu hình hiện tại và toàn bộ kết quả bất lợi. Không đưa candidate vào cấu hình chính. Chẩn đoán p013 là động lực nghiên cứu, không đủ để chọn cải tiến áp dụng cho cả nguồn. CMU/KeyRecs đã xem nên đây là phát triển phương pháp; không CI/p-value hoặc tuyên bố holdout mới.

Ưu tiên tiếp là tổng hợp kết quả đối chứng và kết luận hạn chế vào bản báo cáo đầy đủ, giữ bản sáu trang riêng. Nếu tiếp tục một quy tắc khác, lập kế hoạch riêng và kiểm chứng trên dữ liệu chưa dùng phát triển, không tiếp tục chỉnh theo các mã test đã thấy.

## 5. Bằng chứng và bảo toàn

- `results/cv_aggregation_control_runner_freeze.json/.sha256`: code/test/môi trường/đầu vào và ngưỡng trước chạy.
- `cv_aggregation_control_started.json`, `cv_aggregation_control_results.json`: chronology, hai nhánh/hai nguồn và quyết định theo kế hoạch.
- CSV96 dòng tài khoản,2.532 cặp theo nhánh,48 chênh theo mã,1.266 cặp chuyển quyết định.
- `scripts/validate_cv_aggregation_control.py`, `results/cv_aggregation_control_checks.json`: đối chiếu baseline cũ, macro/tổng số đếm, CSV/transitions, ngưỡng và hash/thứ tự thời gian. Validator không fit hoặc chọn ngưỡng.

17test giả lập là bằng chứng chuẩn bị đã lưu, không nhận đã chạy lại toàn suite ở lượt scoring. Code/plan/freeze và kết quả lịch sử, raw/config, cả hai bộ Word/PDF giữ nguyên hash. Lượt này lưu phân tích riêng, chưa sửa báo cáo hoặc giao diện, chưa làm task Thư/push. Điểm rubric giữ nguyên.
