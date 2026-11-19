# Đối chứng chỉ thay quy tắc tổng hợp điểm CV

Ngày lập: 13/11/2026. Trạng thái: **chốt thiết kế, chưa triển khai/chạy nhánh chuẩn hóa mới**. Đây là nghiên cứu phát triển sau các kết quả CMU/KeyRecs và chẩn đoán p013 đã xem; không phải kiểm chứng độc lập trên dữ liệu mới hoặc đăng ký trước công khai. Kế hoạch này tách riêng khỏi các protocol/code đã đóng băng trước đó.

## 1. Câu hỏi và giả thuyết hẹp

Giữ nguyên detector decay20 và mọi điểm CV, thay duy nhất cách tổng hợp các điểm đó: từ Mean/SD đều sang Mean/SD có trọng số tuổi. **Giả thuyết định hướng: giảm FAR macro mà không tăng FRR macro so với tổng hợp đều, tại cùng ngưỡng z của baseline đã có.** Ưu tiên FAR ở đây vì phép đối chứng xuất phát từ các nhận nhầm tăng trên KeyRecs; không giả định nhánh mới sẽ đạt.

Đây là thay một quy tắc chuẩn hóa gồm cả tâm và độ phân tán, chưa tách riêng tác động của mean với SD. Detector vẫn cùng họ Scaled Manhattan và giữ nguyên trọng số tuổi trong cả hai nhánh. Không dùng tên p013 hoặc mã cụ thể để chọn công thức.

## 2. Hai nhánh và công thức duy nhất thay đổi

Tại mỗi trạng thái lịch sử, có n mẫu theo thứ tự cũ→mới, `20 ≤ n ≤ 50`. Tuổi `age_i=n−1−i`; trọng số `w_i=0.5 ** (age_i/20)`. Detector cuối và từng detector CV đều giữ nguyên `fit_history(..., 'decay20')`: CV5 chia khối liên tiếp, train lấy đúng phần trọng số của các vị trí train. Mỗi điểm OOF `q_i` được tính đúng một lần và dùng chung cho hai nhánh. Không dùng điểm in-sample thay OOF.

| Nhánh | Tâm chuẩn hóa | Độ phân tán chuẩn hóa |
|---|---|---|
| Baseline: `uniform_cv` | `c_u = sum(q_i)/n` | `s_u = max(sqrt(sum((q_i−c_u)^2)/n), 1e−6)` |
| Candidate: `age_weighted_cv` | `c_w = sum(w_i*q_i)/sum(w_i)` | `s_w = max(sqrt(sum(w_i*(q_i−c_w)^2)/sum(w_i)), 1e−6)` |

Đây là phương sai population có trọng số, không hiệu chỉnh Bessel/cỡ mẫu hiệu dụng. Half-life tổng hợp cố định20 lượt như detector; không thử/chọn half-life khác. Không bỏ mẫu, thay fold, lấy median/MAD, lọc ngoại lệ hoặc thêm một phương án thứ ba.

Điểm detector `r(x)` cũng được tính một lần rồi dùng chung: `z_u=(r−c_u)/s_u`, `z_w=(r−c_w)/s_w`. Nhận khi `z ≤ τ_source`.

## 3. Giữ chung ngưỡng để cô lập chuẩn hóa

Hai nhánh dùng **cùng số ngưỡng z đã có của decay20** trong nghiên cứu matched:

| Nguồn | Ngưỡng dùng chung, lấy nguyên float trong artifact |
|---|---:|
| CMU |−0,09327790626776133|
| KeyRecs fixed-text |−0,35492309501165314|

Nguồn: `results/matched_adaptation_results.json`, nhánh `decay20`. Các ngưỡng này đã chọn bằng probe dev S1 ngay sau enrollment với FAR dev5% cho chuẩn hóa đều. **Không chọn lại ngưỡng cho nhánh có trọng số**. Vì z thay đổi, FAR dev của candidate không được bảo đảm5%; phải báo cáo giá trị quan sát, không bỏ nhánh hoặc điều chỉnh cho đạt ngân sách.

Đây là đối chứng chuẩn hóa ở cùng ngưỡng z baseline, không phải so sánh hai hệ thống cùng FAR dev hoặc cùng mức rủi ro vận hành. Muốn so ở cùng ngân sách dev sẽ cần protocol riêng vì phải thêm bước chọn lại ngưỡng. Không trộn hai loại kết luận.

## 4. Dữ liệu và lịch chấm giữ nguyên

- Giữ split36dev/15test CMU và66dev/33test KeyRecs từ kế hoạch matched; không đổi seed, schema31/47chiều hoặc chính sách raw. Mỗi nguồn diễn giải riêng, không gộp mẫu số.
- Enrollment20 mẫu đầu S1. Chẩn đoán dev: probe5đầu+5cuối S1 của mã dev khác, ngay sau enrollment; chỉ đo FAR cho hai nhánh ở ngưỡng cố định, không chọn công thức/ngưỡng từ kết quả này. Không dùng S2 của dev.
- Test: warm-up mọi genuine S1 còn lại; không tính warm-up vào FRR chính. Lịch sử luôn tối đa50 mẫu. Genuine S2 chấm trước, cập nhật sau. Probe là5đầu+5cuối S2 của mỗi mã test khác, chỉ chấm ở đầu S2 và không cập nhật.
- Mọi genuine giả định được xác minh độc lập và đều cập nhật bất kể quyết định của hai nhánh. Do đó lịch sử, trọng số detector, model parameters, raw score và điểm CV phải giống hệt giữa hai nhánh ở mỗi checkpoint; khác biệt quyết định không được làm phân kỳ lịch sử.
- Chỉ S1–S2; CMU750genuine/2.100probe test, KeyRecs3.301genuine/10.560probe test. Dev probe lần lượt12.600/42.900. Không dùng bộ tự thu một phiên để tạo phiên giả hoặc chờ Thư thu thêm.

## 5. Chỉ tiêu và cách kết luận

Tính FAR/FRR từng mã, lấy trung bình không trọng số theo mã trong mỗi nguồn. Chênh chính `Δ = candidate − uniform_cv`, tính từ số đếm bằng phân số chính xác trước làm tròn.

- Giả thuyết được ủng hộ **ở mức mô tả trong một nguồn** khi `Δmacro_FAR < 0` và `Δmacro_FRR ≤ 0`.
- FAR giảm nhưng FRR tăng: đánh đổi. FAR không giảm: chưa đạt giả thuyết. Công bố cả trường hợp FAR tăng, kể cả FRR giảm; không đổi tiêu chí sang FRR sau kết quả.
- Chỉ gọi nhất quán trên hai nguồn nếu cả hai cùng đạt điều kiện. Không chọn kết quả p013 hoặc nguồn thuận lợi để thay đánh giá toàn bộ.
- Báo cáo thêm pooled tử số/mẫu số, chênh theo mã, bảng cặp có hướng, số probe mới nhận/thu hồi và FAR dev ở ngưỡng cố định. Macro và pooled có nhãn riêng; p013 chỉ là ca phụ mô tả, không có quy tắc riêng.
- Không dùng EER/AUC, cỡ mẫu hiệu dụng hay thống kê ổn định để thay tiêu chí chính. Không thêm dung sai FAR/FRR hoặc bỏ tài khoản sau kết quả.

Không thêm CI/p-value theo giả định mọi probe độc lập. Kế hoạch này chưa khóa phương pháp suy luận về bất định; kết luận chỉ ở mức mô tả trên dữ liệu đã dùng phát triển. Mọi genuine được xác minh là giả định oracle, không đo OTP/chống nhiễm hồ sơ. Không suy kết quả thuận lợi sẽ đủ để vận hành.

## 6. Điều kiện triển khai, kiểm tra và dừng

1. Runner riêng, không sửa core/protocol đã đóng băng. Dùng chung cache gồm detector, raw score và điểm OOF; chỉ tạo hai bộ c/s. Test giả lập phải chứng minh mean/SD đều khớp core decay20 cũ, weighted bằng uniform khi mọi trọng số bằng nhau, công thức phương sai đúng và sàn hoạt động với sai số float.
2. Kiểm tra held-row không vào train, age weights đúng vị trí, dữ liệu S2/test không vào CV/dev, score trước update, probe không update và hai nhánh luôn có raw score/lịch sử giống nhau. Không cho kết quả nhận/từ chối ảnh hưởng cập nhật oracle.
3. Baseline phải khớp ngưỡng, số đếm pooled và từng mã nhánh decay20 matched ở cả hai nguồn. Nếu lệch, dừng và điều tra trước khi diễn giải candidate; không sửa kết quả cũ.
4. Khóa hash runner/test/môi trường và đầu vào sau test, trước scoring mới. Kế hoạch hiện tại chỉ khóa thiết kế, không nhận đã khóa code chưa tồn tại. Giữ mọi sửa đổi thiết kế thành phiên bản có lý do trước scoring.
5. Kết quả mới dùng prefix riêng `cv_aggregation_control_*`; từ chối ghi đè. Không thay cấu hình chính, report, explorer hoặc kết quả matched/external trong bước chuẩn bị. Giữ bản sáu trang và điểm rubric.

Kế hoạch máy đọc: `results/cv_aggregation_control_plan.json/.sha256`. Ngưỡng được trích từ kết quả cũ, không tính thử candidate khi lập kế hoạch. Nguồn/mã đã xem vẫn là phát triển; kiểm chứng xác nhận về sau cần dữ liệu chưa dùng phát triển và kế hoạch suy luận riêng.
