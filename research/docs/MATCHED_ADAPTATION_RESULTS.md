# Kết quả so sánh thích nghi trong cùng điều kiện

Đã chạy `scripts/run_matched_adaptation.py --run` sau khi `--check` đạt, theo kế hoạch `MATCHED_ADAPTATION_PROTOCOL.md` và manifest runner đã khóa. Không thay code, half-life, split, ngưỡng mục tiêu hay tiêu chí sau khi xem kết quả. **Giả thuyết chưa được ủng hộ nhất quán trên cả hai nguồn:** CMU giảm cả FAR/FRR; KeyRecs giảm FRR nhưng tăng FAR.

## 1. So sánh chính theo kế hoạch

Baseline `window50` và candidate `decay20` cùng cửa sổ50, CV5/Mean-Std, chọn ngưỡng riêng theo FAR dev≤5%. Cả hai dùng20 enrollment S1, warm-up phần S1 còn lại, genuine S2 chấm trước/cập nhật sau, probe chỉ một lần đầu S2. Genuine giả định được xác minh độc lập; probe không cập nhật. Chỉ xét phiên1–2, không trộn với CMU8phiên cũ.

Chỉ số chính là trung bình không trọng số theo mã (**macro**); Δ = decay − window, đơn vị điểm phần trăm. Điều kiện mô tả đã khóa: `ΔFRR < 0` và `ΔFAR ≤ 0`, xét trước làm tròn.

| Nguồn | Nhánh | FAR macro | FRR macro | ΔFAR | ΔFRR |
|---|---|---:|---:|---:|---:|
| CMU,15 mã test | Window50 |3,38%|32,27%|—|—|
| CMU,15 mã test | Decay20 |2,95%|26,80%|−0,429|−5,467|
| KeyRecs,33 mã test | Window50 |4,16%|55,71%|—|—|
| KeyRecs,33 mã test | Decay20 |4,27%|48,71%|+0,114|−7,006|

- **CMU:** đạt chiều giả thuyết ở mức mô tả trong protocol này. Không suy “tốt hơn cho mọi mã” hoặc có ý nghĩa thống kê.
- **KeyRecs:** không đạt điều kiện FAR không tăng; kết luận là **đánh đổi**. Dù mức tăng FAR nhỏ, không thêm dung sai sau kết quả để đổi thành đạt.
- **Hai nguồn:** điều kiện nhất quán không đạt. Không gộp mẫu số, chọn nguồn thuận lợi hoặc thay chỉ tiêu chính bằng pooled/EER/AUC.

## 2. Tử số/mẫu số và ngưỡng để truy vết

| Nguồn | Nhánh | Ngưỡng dev | Dev nhận nhầm | Test nhận nhầm | Test genuine không nhận |
|---|---|---:|---:|---:|---:|
| CMU | Window50 |−0,1004558579|630/12.600|71/2.100|242/750|
| CMU | Decay20 |−0,0932779063|630/12.600|62/2.100|201/750|
| KeyRecs | Window50 |−0,3582252078|2.145/42.900|439/10.560|1.840/3.301|
| KeyRecs | Decay20 |−0,3549230950|2.145/42.900|451/10.560|1.609/3.301|

CMU giảm9 lượt nhận nhầm và41 lượt genuine không được nhận. KeyRecs giảm231 lượt genuine không được nhận nhưng tăng12 lượt nhận nhầm. Ngưỡng và số đếm pooled/**từng mã** KeyRecs khớp kết quả thích nghi đã công bố trước; đây là đối chiếu lại nguồn đã xem, không phải kiểm chứng mới.

CMU mỗi mã có50 genuine S2 nên FRR macro bằng pooled. KeyRecs số genuine giữa các mã khác nhau: FRR pooled là **55,74% → 48,74%**, còn macro là **55,71% → 48,71%**. Hai cách tổng hợp đều lưu, không dùng số pooled để âm thầm thay tiêu chí chính. FAR macro bằng pooled trong từng nguồn vì mọi mã đích có cùng số probe.

## 3. Khác biệt giữa các mã

| Nguồn | FRR giảm / bằng / tăng | FAR giảm / bằng / tăng | Mã có FRR giảm và FAR không tăng |
|---|---:|---:|---:|
| CMU |14 / 0 / 1|4 / 9 / 2|12/15|
| KeyRecs |32 / 1 / 0|8 / 13 / 12|20/33|

Ở CMU, s018 giảm8 nhận nhầm nhưng tăng1 genuine không được nhận; s012 tăng5 nhận nhầm dù giảm4 genuine không được nhận. s041 giảm5 nhận nhầm và1 genuine không được nhận. Số trung bình tốt hơn không có nghĩa mọi tài khoản cùng được lợi.

Ở KeyRecs, p015 tăng13 nhận nhầm, p009 tăng8; ngược lại p045 giảm7 và p090 giảm4. Đây là đóng góp số đếm theo **tài khoản đích**, chưa phải quy nguyên nhân cho thiết bị, một đặc trưng hoặc một người nguồn cụ thể. Không đặt quy tắc riêng theo các mã đã xem để làm kết quả đẹp hơn. CSV cặp có hướng được giữ để chẩn đoán tiếp, không dùng chọn lại ngưỡng.

## 4. Mức kết luận được phép

Thay lịch hiệu chỉnh/lịch chấm CMU bằng cùng quy tắc S1→S2 đã dùng ở KeyRecs vẫn cho hai chiều kết quả khác nhau: decay giảm cả hai lỗi trên CMU nhưng chỉ giảm FRR trên KeyRecs. Điều này giúp tránh so hai protocol lịch sử khác nhau rồi gọi là cùng điều kiện. Tuy nhiên, hai nguồn vẫn khác người, câu gõ, số chiều, số lượng và điều kiện thu; chưa cô lập nguyên nhân khác biệt theo nguồn hoặc trọng số tuổi.

So sánh là pipeline trọng số tuổi, gồm ảnh hưởng lên detector và chuẩn hóa CV, ở ngưỡng mỗi nhánh chọn từ dev. Không phải thí nghiệm chỉ đổi tâm hồ sơ hoặc ép cùng ngưỡng số. Chưa đo OTP thật, chống nhiễm hồ sơ, chi phí người dùng hoặc chất lượng vận hành. Các lượt/cặp có phụ thuộc; kế hoạch chưa định phương pháp suy luận bất định nên không bổ sung CI/p-value sau khi biết số liệu.

CMU và KeyRecs đều đã được dùng phát triển/đánh giá trước đó. Kết quả này là **nghiên cứu phát triển với protocol chốt trước runner mới**, không phải preregistration công khai, holdout mới hay khẳng định tổng quát hóa. Giữ nguyên cấu hình chính và các kết quả cũ; chưa có cơ sở kết luận decay là thay thế tốt hơn nhất quán.

## 5. Artifact và kiểm tra

- `results/matched_adaptation_runner_freeze.json/.sha256`: code/test/môi trường và mốc đóng băng.
- `results/matched_adaptation_started.json`: mốc bắt đầu gắn hash manifest.
- `results/matched_adaptation_results.json`: kết quả cả hai nguồn/hai nhánh và quyết định theo kế hoạch.
- `matched_adaptation_accounts.csv`:96 dòng; `matched_adaptation_pairs.csv`:2.532 dòng; `matched_adaptation_deltas.csv`:48 dòng.
- `scripts/validate_matched_adaptation.py`, `results/matched_adaptation_checks.json`: kiểm tra thứ tự freeze→start→complete, SHA, mẫu số, macro/tổng lỗi, CSV và tái lập số đếm KeyRecs. Không fit mô hình lại khi chạy validator.

Sau chạy, khóa code/môi trường còn khớp; code/protocol đã đóng băng cũ, raw/config/kết quả cũ và cả hai bộ báo cáo Word/PDF giữ nguyên hash. Không sửa báo cáo hoặc trang khám phá trong lượt phân tích riêng này. 19 test giả lập là bằng chứng bước chuẩn bị, không nhận đã chạy lại toàn suite ở lượt scoring.

Ưu tiên tiếp: phân tích các cặp gây tăng FAR ở KeyRecs với điểm và trạng thái hồ sơ đã khóa, chỉ để chẩn đoán, không tự chỉnh ngưỡng. Nếu phát triển quy tắc khác, cần kế hoạch phiên bản riêng và kiểm chứng sau đó trên dữ liệu thực sự chưa dùng phát triển.
