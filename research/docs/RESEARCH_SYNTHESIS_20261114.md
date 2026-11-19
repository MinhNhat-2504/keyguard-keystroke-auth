# Tổng hợp đối chứng nghiên cứu — 14/11/2026

24 dòng tổng hợp từ bảy artifact gốc. Không fit lại, đổi ngưỡng hoặc chọn lại candidate. Mỗi dòng CSV/JSON có đường dẫn nguồn và JSON pointer; chỉ so trực tiếp trong cùng nhóm/protocol.

## Khảo sát đặc trưng và chuẩn hóa

Bộ tự thu, 3 vòng ngoài; tổng 297 genuine/600 impostor.

| Nguồn | Phương án | Cách tổng hợp | FAR | FRR |
|---|---|---|---:|---:|
|Bộ tự thu|Baseline/ngưỡng CMU|Cộng số đếm|31,17%|15,82%|
|Bộ tự thu|Baseline/hiệu chỉnh dev|Cộng số đếm|7,67%|64,98%|
|Bộ tự thu|Chọn phương án qua vòng trong|Cộng số đếm|10,00%|63,97%|

Chọn qua vòng trong không cải thiện đồng thời FAR/FRR so baseline hiệu chỉnh; dữ liệu đã xem.

## Chất lượng enrollment và chuẩn hóa

Cùng bộ tự thu; 6 phương án, chọn qua vòng trong.

| Nguồn | Phương án | Cách tổng hợp | FAR | FRR |
|---|---|---|---:|---:|
|Bộ tự thu|Baseline|Cộng số đếm|7,67%|64,98%|
|Bộ tự thu|Chọn enrollment/chuẩn hóa|Cộng số đếm|8,67%|60,61%|

Giảm FRR nhưng tăng FAR; không thay cấu hình chính.

## Trọng số mềm qua 10 cách chia

Trung bình 10 cách chia trên cùng 15 mã; không phải 150 người.

| Nguồn | Phương án | Cách tổng hợp | FAR | FRR |
|---|---|---|---:|---:|
|Bộ tự thu|baseline|Trung bình 10 cách chia|8,60%|65,82%|
|Bộ tự thu|hard_selected|Trung bình 10 cách chia|9,08%|57,04%|
|Bộ tự thu|soft_selected|Trung bình 10 cách chia|8,03%|60,03%|
|Bộ tự thu|all_selected|Trung bình 10 cách chia|9,90%|57,95%|

Soft có FAR/FRR trung bình thấp hơn baseline; SD theo cách chia không phải CI, không bảo đảm chuyển nguồn.

## Thích nghi CMU qua 8 phiên

Pooled 5.700 genuine/16.800 impostor, lịch checkpoint cũ.

| Nguồn | Phương án | Cách tổng hợp | FAR | FRR |
|---|---|---|---:|---:|
|CMU/8 phiên|static|Cộng số đếm|3,52%|71,42%|
|CMU/8 phiên|window50|Cộng số đếm|2,14%|21,11%|
|CMU/8 phiên|decay20|Cộng số đếm|2,06%|19,26%|

Decay giảm hai lỗi so window trong phép thử này; không so trực tiếp với lịch probe phiên 2 bên dưới.

## Kiểm chứng KeyRecs cố định hồ sơ

3.301 genuine/10.560 impostor, 47 chiều; phương pháp khóa trước lượt chấm đầu.

| Nguồn | Phương án | Cách tổng hợp | FAR | FRR |
|---|---|---|---:|---:|
|KeyRecs|baseline|Cộng số đếm|8,61%|74,22%|
|KeyRecs|hard_selected|Cộng số đếm|9,96%|69,25%|
|KeyRecs|soft_selected|Cộng số đếm|8,56%|74,01%|
|KeyRecs|all_selected|Cộng số đếm|9,96%|69,25%|

Soft giảm 5 nhận nhầm và 7 genuine bị từ chối; lợi ích nhỏ, FRR còn khoảng 74%, không có suy luận thống kê mới.

## Đối chứng thích nghi cùng điều kiện

CMU và KeyRecs: cùng lịch phiên 2; mỗi nhánh hiệu chỉnh riêng trên dev FAR 5%.

| Nguồn | Phương án | Cách tổng hợp | FAR | FRR |
|---|---|---|---:|---:|
|CMU|window50|Trung bình theo mã|3,38%|32,27%|
|CMU|decay20|Trung bình theo mã|2,95%|26,80%|
|KeyRecs fixed-text|window50|Trung bình theo mã|4,16%|55,71%|
|KeyRecs fixed-text|decay20|Trung bình theo mã|4,27%|48,71%|

CMU thuận lợi mô tả; KeyRecs giảm FRR nhưng tăng FAR. Không ủng hộ nhất quán cả hai nguồn.

## Chỉ thay quy tắc tổng hợp CV

Cùng detector decay20, điểm OOF và ngưỡng z baseline; không phải cùng FAR dev.

| Nguồn | Phương án | Cách tổng hợp | FAR | FRR |
|---|---|---|---:|---:|
|CMU|uniform_cv|Trung bình theo mã|2,95%|26,80%|
|CMU|age_weighted_cv|Trung bình theo mã|2,05%|28,40%|
|KeyRecs fixed-text|uniform_cv|Trung bình theo mã|4,27%|48,71%|
|KeyRecs fixed-text|age_weighted_cv|Trung bình theo mã|4,88%|51,37%|

CMU đánh đổi FAR–FRR; KeyRecs cả hai lỗi tăng. Cả hai nguồn không đạt giả thuyết đã định.

## Diễn giải và phạm vi

Giữ cấu hình triển khai hiện tại. Kết quả có chiều thuận lợi ở một nguồn không đủ để tuyên bố thắng nhất quán. Kiểm chứng KeyRecs ban đầu đã khóa phương pháp trước chấm; các đối chứng tiếp theo trên nguồn đã xem là phát triển phương pháp. Không chuyển profile/ngưỡng CMU sang vector KeyRecs 47 chiều. Không gộp bộ tự thu chủ yếu một phiên, CMU nhiều phiên và KeyRecs thành một FAR/FRR tổng.

Bảng mean theo cách chia không có số đếm duy nhất và SD không phải CI. Hai đối chứng mới dùng chỉ tiêu chính macro; pooled vẫn lưu trong CSV/JSON. CMU có mẫu số genuine bằng nhau nên macro bằng pooled; KeyRecs khác số mẫu theo mã nên FRR có thể khác. Chưa có kết luận thống kê về độ chắc chắn hoặc nguyên nhân theo thiết bị/nhân khẩu học.

Nguồn: các JSON trong source_sha256 của results/research_synthesis_20261114.json; protocol và freeze gốc giữ nguyên.
