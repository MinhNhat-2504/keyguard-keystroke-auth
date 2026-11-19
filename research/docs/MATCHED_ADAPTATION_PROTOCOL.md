# Kế hoạch so sánh thích nghi trong cùng điều kiện

Ngày lập: 13/11/2026. Trạng thái: **chốt thiết kế trước khi viết/chạy runner so sánh mới; chưa có kết quả mới**. Đây là kế hoạch phát triển trên dữ liệu đã xem, không phải preregistration công khai hoặc kiểm chứng trên holdout mới. Các kết quả CMU/KeyRecs cũ đã ảnh hưởng việc chọn câu hỏi này; việc lưu hash bây giờ không xóa lịch sử đó.

## 1. Một giả thuyết chính

**Trong giao thức bên dưới, thay trọng số đều bằng trọng số giảm theo tuổi trong cửa sổ 50 mẫu sẽ giảm FRR mà không tăng FAR, khi cả hai pipeline chọn ngưỡng theo cùng quy tắc FAR dev ≤ 5%.**

Baseline là `window50`; phương án so sánh là `decay20`, trọng số `0.5 ** (age / 20)`, tuổi tính bằng số genuine mới hơn trong lịch sử. Không tìm half-life, cửa sổ, đặc trưng hoặc chuẩn hóa khác. Mỗi phương pháp có ngưỡng số riêng do cùng thủ tục chọn trên dev tạo ra; không ép chung một số ngưỡng cho hai thang điểm khác nhau. Vì trọng số ảnh hưởng detector và chuẩn hóa CV, kết luận thuộc **pipeline trọng số tuổi**, chưa cô lập riêng tác động của tâm hồ sơ.

## 2. Những gì phải giữ giống nhau trong từng nguồn

| Thành phần | Quyết định cố định cho cả hai nhánh |
|---|---|
| Dữ liệu và phân vùng | Giữ nguyên các mã dev/test đã lưu, không chia lại seed |
| Đặc trưng | Toàn bộ 31 timing CMU hoặc 47 timing KeyRecs; không metadata predictor |
| Đăng ký | 20 mẫu đầu phiên 1, theo thứ tự nguồn |
| Detector | Scaled Manhattan; cửa sổ tối đa 50; chỉ trọng số mẫu khác nhau |
| Chuẩn hóa điểm | Mean/Std của 5-fold trên lịch sử quá khứ; sàn 1e−6; cách chia fold giống nhau |
| Ngưỡng | Probe dev phiên 1 ngay sau 20 enrollment; FAR dev ≤ 5%, không chia nhóm điểm bằng nhau |
| Warm-up test | Cập nhật bằng mọi genuine còn lại phiên 1; không tính các lượt này vào FRR chính |
| Genuine test | Mọi genuine phiên 2: chấm trước, cập nhật sau |
| Impostor test | 5 đầu + 5 cuối phiên 2 của mỗi mã khác cùng test; chỉ chấm tại đầu phiên 2, trước genuine đầu tiên |
| Cập nhật | Mọi genuine giả định đã qua xác minh độc lập; probe không cập nhật |
| Phạm vi phiên | Chỉ phiên 1–2, không lấy phiên 3–8 CMU vào so sánh chính |

Probe dev lấy 5 đầu + 5 cuối phiên 1 của các mã dev khác, tại trạng thái ngay sau enrollment. Ngưỡng riêng từng nhánh được cố định trước warm-up/chấm test, không dùng genuine phiên 2 hoặc probe test để chọn. Không dùng phiên 2 của dev. Lịch sử tuổi chỉ chứa dữ liệu đã đến; trong mỗi fold lấy phần trọng số của các vị trí train, giống `fit_history` hiện có.

Hai nhánh dùng chính xác cùng account, genuine, cặp target–impostor và thứ tự. Điều kiện giống nhau **trong mỗi nguồn**; hai nguồn vẫn khác người, câu gõ và schema, nên chưa tách riêng được nguyên nhân khác biệt giữa nguồn.

## 3. Tập dữ liệu và mẫu số cần đối chiếu trước scoring

- **CMU:** giữ 36 dev/15 test từ `models/model_config.json`. Mỗi mã có 50 mẫu/phiên: enrollment 20, warm-up 30, test genuine phiên 2 là 50. Kỳ vọng 750 genuine và 2.100 probe test mỗi nhánh; probe dev là 12.600 lượt. Đây là đổi protocol so với kết quả CMU cũ, vốn dùng 8 phiên và ngưỡng probe dev gộp các phiên.
- **KeyRecs:** giữ 66 dev/33 test từ `results/external_validation_freeze.json`, schema/raw/split cũ. Kỳ vọng 3.301 genuine và 10.560 probe test; probe dev là 42.900 lượt. Giao thức này đã được chạy cho KeyRecs trong lượt kiểm chứng cũ, nên các kết quả đó đã biết. Tái dùng/tái lập chúng chỉ để đối chiếu cùng giao thức, không phải phát hiện hay kiểm chứng mới.
- Không đưa bộ tự thu chủ yếu một phiên vào phép thử qua phiên. Không tạo phiên giả, không cần chờ Thư thu thêm.

Nếu metadata, hash, số lượng hoặc điều kiện đủ không khớp, dừng trước scoring và ghi lỗi. Không loại mã vì mô hình có lỗi cao; không thay split hoặc nguồn vì kết quả không thuận lợi.

## 4. Chỉ số và quy tắc diễn giải định trước

Đơn vị so sánh chính là **cùng mã tài khoản**. Với mỗi mã, tính FRR genuine phiên 2 và FAR probe đầu phiên 2 cho cả hai nhánh. Lấy trung bình không trọng số theo mã trong từng nguồn, rồi tính:

`ΔFRR = macro_FRR(decay20) − macro_FRR(window50)`

`ΔFAR = macro_FAR(decay20) − macro_FAR(window50)`

- Chiều giả thuyết được ủng hộ **ở mức mô tả trong một nguồn** khi `ΔFRR < 0` và `ΔFAR ≤ 0`, dùng tỷ lệ chưa làm tròn. Không có biên dung sai chọn sau khi xem kết quả.
- Nếu FRR giảm nhưng FAR tăng: ghi **đánh đổi**, không ghi “cải thiện đồng thời”. Nếu không giảm FRR: giả thuyết không được ủng hộ ở nguồn đó. Nếu hai nguồn khác chiều: công bố khác biệt; không chọn nguồn đẹp làm kết luận chung.
- Muốn nói chiều giả thuyết nhất quán trên cả hai nguồn, cả hai phải đạt điều kiện trên. Vẫn chỉ là mô tả trên dữ liệu đã dùng phát triển, không phải bằng chứng xác nhận độc lập hoặc ý nghĩa thống kê.
- Báo cáo thêm tử số/mẫu số pooled, Δ theo từng mã, số mã tốt hơn/bằng/kém hơn và toàn bộ cặp target–impostor. Các bảng phụ không được dùng để thay tiêu chí chính hoặc chọn half-life/nhóm người.
- Macro FRR có thể khác FRR pooled đã công bố khi số genuine giữa các mã khác nhau. Giữ cả hai và ghi rõ tên; không thay bảng kết quả lịch sử bằng cách tổng hợp mới. Không cần EER/AUC để quyết định giả thuyết này.

Không cộng hai nguồn thành một mẫu số. Các lượt genuine, probe và cặp có phụ thuộc; không làm CI/p-value bằng giả định từng lượt độc lập, không coi SD theo mã là CI. Lượt thiết kế này chưa chốt một phương pháp suy luận đã được kiểm tra cho phụ thuộc target/source và chọn ngưỡng dev; do đó **không đưa ngưỡng “có ý nghĩa thống kê” vào quyết định**. Đánh giá xác nhận về độ chắc chắn cần một kế hoạch suy luận riêng trước khi mở kết quả của dữ liệu mới.

## 5. Cách triển khai sau bước lập kế hoạch

1. Thêm runner riêng, tái dùng core hiện có; không sửa các file code/protocol đã đóng băng của KeyRecs. Test bằng dữ liệu giả để kiểm tra chấm trước cập nhật sau, probe không cập nhật, giới hạn phiên và dev không đọc phiên 2/test.
2. Trước scoring mới, lưu hash runner/test, môi trường, raw/schema/split và bản kế hoạch này; trạng thái kế hoạch hiện tại không nhận là đã khóa code chưa tồn tại. Nếu thay thiết kế, lưu bản sửa và lý do trước scoring, không ghi đè để che lịch sử.
3. Chạy hai nhánh trên cùng dữ liệu của từng nguồn; lưu riêng `matched_adaptation_*`, không ghi đè `session_adaptation.json`, `external_validation.json` hoặc cấu hình chính. Đối chiếu KeyRecs với số đếm cũ cho cả hai nhánh; macro là phép tổng hợp mới có nhãn rõ.
4. Xuất báo cáo riêng cả kết quả không thuận lợi, sau đó mới cập nhật bản đầy đủ/trang khám phá nếu phù hợp. Bản sáu trang và điểm rubric giữ nguyên.

Artifact tối thiểu: manifest kế hoạch/code, JSON protocol + kết quả cả hai nhánh, CSV theo mã và cặp có hướng, nhật ký kiểm tra. Kế hoạch máy đọc tại `results/matched_adaptation_plan.json`; hash bản kế hoạch ở `results/matched_adaptation_plan.sha256`.

## 6. Phân biệt nghiên cứu tiếp với kiểm chứng mới

CMU/KeyRecs đã xem chỉ giúp chẩn đoán một câu hỏi hẹp trong giao thức đồng nhất. Để kiểm chứng xác nhận tiếp, cần chọn nguồn hoặc tập mới thực sự chưa dùng phát triển; kiểm tra điều kiện sử dụng, phiên/schema và tính đủ mẫu trước scoring, rồi khóa adapter, phân vùng, tiêu chí và phương pháp ước lượng bất định riêng. Không gọi việc chia lại các mã đã xem là holdout mới. Chưa có nguồn mới được chọn hoặc tải trong bước lập kế hoạch này.
