# Tổng hợp đối chứng và chốt hướng nghiên cứu — 15/11/2026

Tổng hợp **11 nhóm nghiên cứu,35 dòng kết quả đã lưu**. Không chạy thí nghiệm mới, không lựa chọn lại ngưỡng hoặc gộp các nguồn thành một FAR/FRR. Mỗi dòng CSV/JSON có artifact và JSON pointer truy vết. Đây không phải35 thí nghiệm độc lập; một số dòng là nhiều nhánh của cùng phép so sánh.

## Quyết định hiện tại

**Giữ baseline sản phẩm và dừng vòng dò mô hình/chuẩn hóa trên các nguồn đã xem.** Có kết quả thuận lợi cục bộ, nhưng chưa có bằng chứng nhất quán đủ để thay cấu hình hiện tại. Baseline được giữ để bảo toàn phiên bản đã đánh giá, không được coi là đã đủ tốt cho triển khai thực tế.

## Bản đồ các nhóm đối chứng

| Nhóm | Điều kiện cần nhớ | Kết luận trong đúng phạm vi |
|---|---|---|
|Khảo sát đặc trưng và chuẩn hóa|Bộ tự thu, 3 vòng ngoài; tổng 297 genuine/600 impostor.|Chọn qua vòng trong không cải thiện đồng thời FAR/FRR so baseline hiệu chỉnh; dữ liệu đã xem.|
|Chất lượng enrollment và chuẩn hóa|Cùng bộ tự thu; 6 phương án, chọn qua vòng trong.|Giảm FRR nhưng tăng FAR; không thay cấu hình chính.|
|Trọng số mềm qua 10 cách chia|Trung bình 10 cách chia trên cùng 15 mã; không phải 150 người.|Soft có FAR/FRR trung bình thấp hơn baseline; SD theo cách chia không phải CI, không bảo đảm chuyển nguồn.|
|Thích nghi CMU qua 8 phiên|Pooled 5.700 genuine/16.800 impostor, lịch checkpoint cũ.|Decay giảm hai lỗi so window trong phép thử này; không so trực tiếp với lịch probe phiên 2 bên dưới.|
|Kiểm chứng KeyRecs cố định hồ sơ|3.301 genuine/10.560 impostor, 47 chiều; phương pháp khóa trước lượt chấm đầu.|Soft giảm 5 nhận nhầm và 7 genuine bị từ chối; lợi ích nhỏ, FRR còn khoảng 74%, không có suy luận thống kê mới.|
|Đối chứng thích nghi cùng điều kiện|CMU và KeyRecs: cùng lịch phiên 2; mỗi nhánh hiệu chỉnh riêng trên dev FAR 5%.|CMU thuận lợi mô tả; KeyRecs giảm FRR nhưng tăng FAR. Không ủng hộ nhất quán cả hai nguồn.|
|Chỉ thay quy tắc tổng hợp CV|Cùng detector decay20, điểm OOF và ngưỡng z baseline; không phải cùng FAR dev.|CMU đánh đổi FAR–FRR; KeyRecs cả hai lỗi tăng. Cả hai nguồn không đạt giả thuyết đã định.|
|Co MAD về prior DEV (shrink25)|Hồ sơ tĩnh20, CV5fold; cùng ngân sách FAR DEV5%; CMU/KeyRecs đã xem.|Không nguồn nào đạt tiêu chí. CMU cả hai lỗi tăng; KeyRecs giảm FRR nhưng tăng FAR.|
|Kiểm chứng shrink25 cố định trên GREYC-Web|42DEV/21TEST, 21 timing nguồn; ngưỡng riêng từng nhánh theo DEV5%. Phương pháp/tiêu chí khóa trước scoring nguồn mới.|FAR và FRR macro đều tăng;3/21 mã được lợi có guard. Không đạt. GREYC đã được xem sau lượt này.|
|Phân vị OOF thay mean/SD|28calibration/14evaluation từ42DEV đã xem; same detector/probe, cùng ngân sách FAR≤5%, không chia ties.|FRR giảm nhưng FAR tăng;2/14 mã được lợi có guard. Không đạt; giữ kết quả bất lợi.|
|Giữ/bỏ off-diagonal covariance|28/14DEV, cùng LedoitWolf/mean/MAD/CV; full vs diag là chính, Manhattan chỉ tham chiếu.|Full giảm FRR nhưng tăng FAR so diag;4/14 mã được lợi có guard. Cổng B không đạt; chưa chạy nguồn ngoài B.|

## Bảng kết quả theo từng protocol

FAR/FRR trong bảng tuân theo cột “Cách tổng hợp”; không xếp hạng các dòng khác protocol. “Mean qua split” không có một mẫu số duy nhất; SD không phải CI. Nhánh tham chiếu không được đổi thành đối chứng chính sau khi thấy số liệu.

| Nhóm | Nguồn | Nhánh | Cách tổng hợp | FAR | FRR | Vai trò |
|---|---|---|---|---:|---:|---|
|features|Bộ tự thu|Baseline/ngưỡng CMU|Pooled|31.17%|15.82%|historical_comparison|
|features|Bộ tự thu|Baseline/hiệu chỉnh dev|Pooled|7.67%|64.98%|historical_comparison|
|features|Bộ tự thu|Chọn phương án qua vòng trong|Pooled|10.00%|63.97%|historical_comparison|
|enrollment|Bộ tự thu|Baseline|Pooled|7.67%|64.98%|historical_comparison|
|enrollment|Bộ tự thu|Chọn enrollment/chuẩn hóa|Pooled|8.67%|60.61%|historical_comparison|
|stability|Bộ tự thu|baseline|Mean qua split|8.60%|65.82%|historical_comparison|
|stability|Bộ tự thu|hard_selected|Mean qua split|9.08%|57.04%|historical_comparison|
|stability|Bộ tự thu|soft_selected|Mean qua split|8.03%|60.03%|historical_comparison|
|stability|Bộ tự thu|all_selected|Mean qua split|9.90%|57.95%|historical_comparison|
|cmu_sessions|CMU/8 phiên|static|Pooled|3.52%|71.42%|historical_comparison|
|cmu_sessions|CMU/8 phiên|window50|Pooled|2.14%|21.11%|historical_comparison|
|cmu_sessions|CMU/8 phiên|decay20|Pooled|2.06%|19.26%|historical_comparison|
|external|KeyRecs|baseline|Pooled|8.61%|74.22%|historical_comparison|
|external|KeyRecs|hard_selected|Pooled|9.96%|69.25%|historical_comparison|
|external|KeyRecs|soft_selected|Pooled|8.56%|74.01%|historical_comparison|
|external|KeyRecs|all_selected|Pooled|9.96%|69.25%|historical_comparison|
|matched|CMU|window50|Macro theo mã|3.38%|32.27%|historical_comparison|
|matched|CMU|decay20|Macro theo mã|2.95%|26.80%|historical_comparison|
|matched|KeyRecs fixed-text|window50|Macro theo mã|4.16%|55.71%|historical_comparison|
|matched|KeyRecs fixed-text|decay20|Macro theo mã|4.27%|48.71%|historical_comparison|
|cv|CMU|uniform_cv|Macro theo mã|2.95%|26.80%|historical_comparison|
|cv|CMU|age_weighted_cv|Macro theo mã|2.05%|28.40%|historical_comparison|
|cv|KeyRecs fixed-text|uniform_cv|Macro theo mã|4.27%|48.71%|historical_comparison|
|cv|KeyRecs fixed-text|age_weighted_cv|Macro theo mã|4.88%|51.37%|historical_comparison|
|mad_shrink|CMU|baseline|Macro theo mã|5.52%|55.47%|control|
|mad_shrink|CMU|shrink25|Macro theo mã|5.62%|56.27%|candidate|
|mad_shrink|KeyRecs fixed-text|baseline|Macro theo mã|8.61%|74.28%|control|
|mad_shrink|KeyRecs fixed-text|shrink25|Macro theo mã|8.65%|73.18%|candidate|
|greyc_fixed|GREYC-Web|baseline|Macro theo mã|2.24%|78.06%|control|
|greyc_fixed|GREYC-Web|shrink25|Macro theo mã|2.33%|78.34%|candidate|
|percentile|GREYC DEV|baseline|Macro theo mã|3.08%|74.03%|control|
|percentile|GREYC DEV|oof_percentile|Macro theo mã|4.07%|72.54%|candidate|
|covariance|GREYC DEV|diag_lw|Macro theo mã|2.14%|69.15%|control|
|covariance|GREYC DEV|full_lw|Macro theo mã|2.97%|68.74%|candidate|
|covariance|GREYC DEV|scaled_manhattan|Macro theo mã|3.08%|74.03%|descriptive_reference|

## Không đánh tráo tiêu chí

- Matched adaptation xét giảm FRR macro và FAR không tăng; CV age-weighted xét giảm FAR macro và FRR không tăng tại cùng ngưỡng z. Hai tiêu chí khác nhau; không dùng một tiêu chí chung để sửa kết luận cũ.
- Shrink25, GREYC fixed, percentile và covariance xét giảm FRR macro/FAR không tăng. Với lợi đa số, đếm tài khoản giảm FRR mà FAR không tăng, không tính hòa là được lợi.
- Full covariance có số đếm thuận lợi hơn Manhattan tham chiếu trên14DEV, nhưng đối chứng chính full−diag không đạt. Chưa có cơ sở đổi câu hỏi sau kết quả rồi gọi là xác nhận cải tiến.
- Khóa code/protocol trước scoring không biến nguồn đã xem thành dữ liệu độc lập mới. GREYC lần đầu dùng cho shrink25 cố định; các chẩn đoán và đối chứng DEV sau đó là phát triển.

## Chất lượng dữ liệu và phạm vi suy luận

- Bộ tự thu601dòng/15mã được đánh giá sơ bộ, chủ yếu một phiên; không có bằng chứng nhiều ngày chỉ vì rubric nội bộ đã đổi task. P10/metadata/provenance vẫn giữ trong báo cáo.
- Audit42DEVGREYC:4.405capture,4.404ghépđược,4.403khớpvector,1mismatch/1unresolved. Tần suất thấp chưa giải thích FRR cao; không sửa raw hoặc loại mã bất lợi.
- UA khác không chứng minh đổi thiết bị; sự phụ thuộc trong người dùng và shared impostor khiến từng lượt không độc lập. Không tạo CI/p-value hoặc kết luận nhân quả từ các bảng mô tả.
- Các protocol static/update/fallback, amount enrollment, lịch probe và cohort khác nhau. Không cộng mẫu số hoặc lấy live0/10 để phủ nhận FAR mô phỏng cao.

## Hướng nghiên cứu đã chốt

1. **Chốt nhánh hiện tại:** v3 vẫn là bản bàn giao đã review; bản tổng hợp này là companion mới ngoài ZIPv3. Không phát sinh mô hình, seed, ngưỡng, estimator hoặc λ khác trong cùng vòng.
2. **Ưu tiên bằng chứng mới hơn công thức mới:** muốn mở lại cải tiến mô hình cần câu hỏi gắn với cơ chế/nhu cầu thực tế, nguồn truy cập hợp lệ và chưa dùng phát triển, protocol/adapter/split/tiêu chí khóa trước scoring. Không hứa kết quả thuận lợi; không gọi CMU/KeyRecs/GREYC đã xem là mới.
3. **Chỉ mở một phép so sánh:** quy định control/candidate, ngân sách FAR, phân bố lợi/hại theo tài khoản và cổng dừng trước. Sau khi thấy điểm, sửa thiết kế nghĩa là phiên bản phát triển mới, phải giữ artifact thất bại.

Không có nguồn kiểm chứng mới được chọn hoặc tải trong lượt tổng hợp. Cổng B của covariance đã thất bại nên không tiếp tục nó dưới dạng kiểm chứng. Nếu muốn nghiên cứu full-vs-Manhattan thì là một câu hỏi mới, cần lý do ngoài việc kết quả tham chiếu vừa thuận lợi; không tự triển khai trong lượt này.

## Điều kiện mở lại và điểm dừng

| Điều kiện | Yêu cầu trước khi chấm | Nếu không đủ |
|---|---|---|
|Câu hỏi mới|Có động lực độc lập với bảng điểm vừa xem; một thay đổi kiểm soát được|Giữ kết luận hiện tại|
|Nguồn mới|Điều kiện dùng rõ, provenance/schema phù hợp, đủ enrollment/probe, tách mã/ngày thật|Ghi chưa có bằng chứng, không tạo phiên giả|
|Thử nghiệm|Test giả, freeze code/data/env, acceptance rule/FARbudget/ties/lợi-hại chốt trước|Chưa chạy thật|
|Kết quả|Công bố đầy đủ macro/pooled/counts/mã và mọi bất lợi|Không tune để cứu; không đổi control sau kết quả|
|Triển khai|Có bằng chứng vận hành và hiệu năng phù hợp mục đích|Không suy từ việc chạy local thành đạt thực tế|

## Artifact và kiểm tra

Nguồn vàSHA trong `results/research_decision_20261115.json`;CSV35dòng cópointer tớiartifact. Tái lập tổng hợp: `python scripts/synthesize_research_decision.py`;kiểm độc lập: `python scripts/validate_research_decision.py`. Không sửa tổng hợp14/11,report6/37/40/phụlục3trang/ZIPv3. Điểm100nộibộkhôngđổi;khôngpush/deploy/DBwrite.
