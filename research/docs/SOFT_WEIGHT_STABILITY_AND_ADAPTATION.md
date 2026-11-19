# Trọng số mềm, độ ổn định và thích nghi theo phiên — 13/11/2026

Thực hiện theo yêu cầu làm cả ba hướng, ưu tiên **1–2 trước**. Mục tiêu là cải tiến phương pháp và bằng chứng của bài tập lớn, **không chốt mục tiêu vận hành demo**. Các chức năng khám phá chỉ để đọc kết quả nghiên cứu. Không làm task Thư, sửa raw/config hoặc thay thế các kết quả trước.

## 1. Giảm ảnh hưởng mẫu khác biệt, không loại hẳn

Giữ nguyên 597 mẫu/15 mã, 20 enrollment và lịch đánh giá của nghiên cứu trước. Ba cách xử lý enrollment:

- `keep_all`: giữ đều các mẫu, baseline Scaled Manhattan.
- `hard_filter`: quy tắc robust trước đây, loại tối đa 20%, giữ ít nhất16/20.
- `soft_weight`: giữ **mọi mẫu với trọng số dương**. Tính độ lệch robust theo mẫu và cutoff giống bước cũ: tâm median/scale1,4826MAD theo chiều, độ lệch mẫu là median độ lệch chuẩn hóa trên31 chiều; cutoff=median điểm+3robust sigma. Trọng số `clip(cutoff/deviation, 0.25, 1)`, dùng sàn mẫu số1e−9. Không thử nhiều mức sàn hay số mũ rồi chọn bằng test.

Với trọng số w, tâm theo chiều là `sum(w*x)/sum(w)`, MAD theo chiều là `sum(w*abs(x-center))/sum(w)`, sàn1e−9. Khoảng cách của mẫu mới là tổng độ lệch tuyệt đối chia MAD này. Trọng số **không phải xác suất mẫu đúng/sai**. Cỡ mẫu hiệu dụng `(sum w)^2/sum(w^2)` chỉ mô tả phân bố trọng số, không tạo thêm mẫu/người độc lập.

Trọng số/cờ mẫu được fit lại trên phần train của mỗi fold CV; mẫu giữ ra không tham gia tính tâm/scale/cutoff/trọng số. Toàn bộ20 điểm held-out dùng để chuẩn hóa điểm bằng Mean/Std, Median/MAD hoặc Median/IQR như trước. Trọng số cuối fit lại trên toàn bộ20 enrollment; không nhìn các genuine sau enrollment để đặt trọng số.

## 2. Mười cách chia mã đã định trước

**9 phương án = 3 cách xử lý × 3 chuẩn hóa điểm.** Seed **42,43,…,51** được cố định trước khi chạy loạt này, không chọn subset sau khi xem số. Mỗi seed dùng3 vòng ngoài (10 mã dev/5 mã test),2 vòng trong để lựa chọn phương án. Tài khoản và impostor đều chỉ lấy trong cùng phân vùng; 5 lượt đầu+5 lượt cuối của4 mã khác trong nhóm test, tổng297 genuine/600 impostor mỗi seed.

So sánh bốn quy trình có điều kiện lựa chọn khác nhau:

| Quy trình | Tập phương án được vòng trong xem |
|---|---|
| Baseline | Giữ20/Mean-Std cố định |
| Hard-selected | Chỉ3 chuẩn hóa của lọc cứng |
| Soft-selected | Chỉ3 chuẩn hóa của trọng số mềm |
| All-selected | Cả9 phương án |

Vòng trong chọn theo BER=(FAR+FRR)/2, hòa theo tên; ngưỡng chỉ lấy impostor train/dev tương ứng, FAR dev≤5% và không tách nhóm điểm bằng nhau. Chọn lại một ngưỡng trên10 mã dev rồi chấm5 mã ngoài. Không chọn seed tốt nhất, không tự đặt quy tắc theo P10/P09, không chọn từ bảng9 phương án ở outer-test.

### Kết quả tổng hợp

Đơn vị FAR/FRR/EER là%; SD là độ lệch chuẩn mẫu (`ddof=1`) giữa10 cách chia phụ thuộc, **không phải CI hay sai số chuẩn của10 thí nghiệm độc lập**.

| Quy trình | FAR TB ± SD | FRR TB ± SD | EER TB | AUC TB |
|---|---:|---:|---:|---:|
| Baseline | 8,60 ±3,83 | 65,82 ±2,30 | 21,94 | 0,853 |
| Hard-selected | 9,08 ±2,80 | 57,04 ±3,14 | 23,50 | 0,842 |
| Soft-selected | 8,03 ±3,41 | 60,03 ±2,49 | 24,08 | 0,844 |
| All-selected | 9,90 ±4,36 | 57,95 ±3,42 | 23,58 | 0,841 |

Soft-selected giảm đồng thời FAR và FRR so baseline ở **7/10** seed, không phải10/10. So sánh ghép theo cùng seed:

- So baseline: FAR trung bình giảm **0,57 điểm phần trăm**, FRR giảm **5,79 điểm**; FAR chênh từ−2,50 đến+3,67 điểm, FRR chênh từ−10,77 đến0 điểm.
- So hard-selected: FAR giảm trung bình **1,05 điểm** nhưng FRR **tăng3,00 điểm**.
- EER/AUC trung bình của mềm **chưa tốt hơn baseline**, nên không nói khả năng phân biệt đã cải thiện toàn diện. Các ngưỡng và lựa chọn phương án khác nhau tạo ra các điểm đánh đổi khác nhau.

FAR của mềm qua seed nằm **4,50–15,50%**, FRR **55,89–65,32%**. Seed42 riêng cho44/600 nhận nhầm,182/297 genuine cần xác minh; không dùng con số riêng này thay kết quả10 seed.

Mười lần chia dùng lại **cùng15 mã**, không thành150 người độc lập; không cộng mẫu số thành6.000 impostor rồi diễn giải độ chắc chắn như thu mới. Dữ liệu đã được khảo sát trước khi thiết kế quy tắc, nên đây vẫn là nghiên cứu khám phá. Việc thêm vòng trong không xóa lịch sử đã xem dữ liệu.

## 3. Thích nghi qua các phiên CMU

Dùng36 mã dev và15 mã test từ cấu hình CMU nguồn, tách mã cả hai vai trò target/impostor; các mã đều đã được benchmark trước đây, không gọi là holdout mới. Mỗi mã có400 mẫu/8 phiên:

1. Đăng ký20 mẫu đầu phiên1.
2. Chấm380 genuine còn lại theo session/rep, **chấm trước cập nhật sau**. Phiên1 còn30 genuine, phiên2–8 có50/mã.
3. Probe là5 đầu+5 cuối của mọi mã khác **trong cùng phân vùng**, chấm sau enrollment và đầu các phiên2–8, không cập nhật hồ sơ.
4. Mọi genuine được giả định có xác minh độc lập trước khi thêm vào lịch sử, kể cả khi nhịp gõ từ chối. Không xen impostor vào hồ sơ ở thí nghiệm này; giả định này không phải chất lượng OTP đã đo.

Ba phương pháp, hằng số cố định trước khi chạy:

| Phương pháp | Lịch sử và trọng số |
|---|---|
| Static | Cố định20 enrollment |
| Window50 | Tối đa50 genuine gần nhất, trọng số đều |
| Decay20 | Cùng50 mẫu, trọng số `0.5 ** (age / 20)`, age đếm số lượt genuine mới hơn |

Decay20 là chu kỳ bán rã **20 lượt genuine**, không phải20 ngày hoặc20 phiên. Tâm/MAD tính có trọng số tuổi. Chuẩn hóa điểm Mean/Std từ5-fold của lịch sử hiện tại; ở train lấy đúng phần trọng số tuổi của các vị trí train, không lấy mẫu tương lai. Không dùng ngưỡng từ test để chọn half-life.

Điểm probe dev có quỹ đạo không phụ thuộc ngưỡng vì cập nhật dùng nhãn genuine lý tưởng. Chọn **một ngưỡng riêng cho từng phương pháp** trên impostor dev gộp các phiên, FAR dev≤5%, rồi đóng băng qua8 phiên test. Không chỉnh theo từng phiên test. Có13.680 genuine/100.800 probe dev,5.700 genuine/16.800 probe test; probe được lặp nên số lượt không độc lập.

| Phương pháp | Ngưỡng dev | FAR test | FRR test |
|---|---:|---:|---:|
| Static | −0,052930 | 592/16.800 = **3,52%** | 4.071/5.700 = **71,42%** |
| Window50 | 0,197413 | 360/16.800 = **2,14%** | 1.203/5.700 = **21,11%** |
| Decay20 | 0,205582 | 346/16.800 = **2,06%** | 1.098/5.700 = **19,26%** |

Trong protocol này, decay giảm14 probe nhận nhầm và105 genuine cần xác minh so window đều. Đây là so sánh phương pháp **kèm cách chuẩn hóa và ngưỡng dev tương ứng**, không cô lập nhân quả thuần của trọng số tuổi. Cả hai cách cập nhật tốt hơn hồ sơ cố định trong lịch phiên này; không khẳng định cùng hiệu quả ở bộ trình duyệt chủ yếu một phiên.

Không so trực tiếp các tỷ lệ trên với lịch checkpoint50 lượt ở mô phỏng cũ hoặc thí nghiệm xen mẫu. Không suy khả năng chống nhiễm hồ sơ: phép thử ở đây không đưa impostor vào cập nhật, còn nghiên cứu nhiễm trước đó đã đo một giả định khác. Không thay `models/model_config.json` bằng các ngưỡng nghiên cứu.

## Artifact và kiểm chứng

```powershell
./.venv/Scripts/python.exe scripts/run_stability_study.py
./.venv/Scripts/python.exe scripts/run_session_adaptation.py
./.venv/Scripts/python.exe scripts/plot_stability_study.py
./.venv/Scripts/python.exe scripts/validate_stability_study.py
./.venv/Scripts/python.exe -m pytest tests/test_soft_weighting.py tests/test_enrollment_study.py tests/test_diagnostics.py tests/test_research.py tests/test_model.py tests/test_collected.py tests/test_live_evidence.py tests/test_features.py tests/test_simulation.py -q
node scripts/check_explorer.mjs
```

- `results/stability_study.json`:9 phương án,10 seed,30 vòng ngoài,4 quy trình và135 chi tiết trọng số enrollment.
- `stability_comparison.csv`:270 dòng theo seed/vòng/phương án; `stability_account_errors.csv`:1.350 dòng theo mã, giữ đủ kết quả không thuận lợi.
- `results/session_adaptation.json`, `.csv`:3 phương pháp×2 phân vùng×8 phiên=48 dòng CSV; chi tiết theo mã và tổng số đếm.
- `figures/research/soft_weight_stability.png`, `session_adaptation.png`: hình xuất riêng cho báo cáo.
- Explorer **mục07** xem thống kê phụ thuộc, seed/quy trình/mã/trọng số; **mục08** xem phương pháp/dev-test/lỗi từng phiên. Chỉ đọc số liệu tính sẵn.

**45 test liên quan đạt,4 subtest**, thêm9 test về trọng số đơn vị khớp baseline, giảm ảnh hưởng outlier nhưng không xóa, CV train-only, không đọc genuine/test ngoài khi fit/chọn, SD không bị nhầm SEM, chấm trước cập nhật, không dùng tương lai và probe không làm thay đổi lịch sử. Chrome đối chiếu600 chi tiết seed–quy trình–mã và6 tổ hợp phương pháp–phân vùng, ngoài các mục cũ; mobile390px không tràn. Không chạy lại benchmark4 họ hoặc full suite sklearn.

**Kết luận nghiên cứu:** trọng số mềm thay đổi đánh đổi FAR/FRR có ích trong một số cách chia, nhưng không thắng EER/AUC; giảm trọng số theo tuổi có kết quả thích nghi tốt hơn cửa sổ đều trong protocol CMU đã nêu. Giữ nguyên dữ liệu/cấu hình/kết quả cũ. Bước tiếp theo phù hợp là định trước giả thuyết so sánh và kiểm chứng trên nguồn hoặc phép chia chưa dùng phát triển quy tắc; không yêu cầu chốt mục tiêu demo.

**Bước kiểm chứng nguồn ngoài đã hoàn thành sau mốc này:** xem [EXTERNAL_VALIDATION_RESULTS.md](EXTERNAL_VALIDATION_RESULTS.md). KeyRecs được audit rồi đóng băng protocol/code trước chấm;giữ các kết quả không thuận lợi. Báo cáo đầy đủ hiện34 trang,mốc32 trang là lịch sử của phần nghiên cứu này. Không sửa code/phương pháp đã đóng băng để khớp kết quả nguồn ngoài.
