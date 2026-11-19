# Chẩn đoán FRR baseline trên DEV GREYC-Web — 15/11/2026

Phân tích hậu nghiệm chỉ42tài khoản DEV, giữ baseline và ngưỡng calibration gốc. Không chấm lại TEST, thử candidate hoặc gọi hàm chọn ngưỡng.

Ngưỡng z cố định **-0.453469916239**, accept khi z≤ngưỡng. Tái lập impostor DEV đúng **861/17220=5%**. Đây là calibration trên probe enrollment của mã khác, không phải DEV holdout độc lập.

## Genuine bị từ chối ở đâu?

| Nhóm genuine DEV | Từ chối / lượt | FRR macro | FRR pooled |
|---|---:|---:|---:|
|Enrollment, chấm lại full-profile20|409/840|48,69%|48,69%|
|OOF20, profile16 mỗi fold|538/840|64,05%|64,05%|
|Ngày sau enrollment, profile20|2777/3565|70,28%|77,90%|

Enrollment resubstitution lạc quan; OOF đã dùng để chuẩn hóa nên không là validation độc lập. OOF và ngày sau cũng khác số mẫu fit16/20, không quy mọi chênh lệch cho thời gian.

FRR đã cao ngay ở OOF (64,05%), nên không thể giải thích toàn bộ vấn đề chỉ bằng thay đổi ở ngày sau. Quy tắc z chuẩn hóa mean/SD không bảo đảm tỷ lệ genuine được nhận ở ngưỡng đã hiệu chỉnh theo impostor. Đây là quan sát tại ngưỡng cố định, không chứng minh một cách chuẩn hóa khác sẽ tốt hơn.

Median z ngày sau lớn hơn median OOF ở **29/42** mã. FRR ngày sau cao hơn OOF ở **29/42** mã. Đây là dấu hiệu phân bố điểm thay đổi, chưa tách được thời gian, thiết bị/browser, số mẫu fit hay các yếu tố thu thập.

## Có phải SD/MAD chạm sàn?

- SD OOF chạm sàn1e−6: **0/42**. MAD full-profile chạm sàn1e−9: **0/882** feature-cells.
- SD OOF min/median/max: **7.003 / 14.435 / 39.746** (đơn vị điểm khoảng cách gốc).
- Raw cutoff âm: **0/42**. Kiểm tra raw_score>mean_OOF+tau×SD_OOF cho đúng quyết định z>tau ở mọi lượt.
- Vì không chạm sàn, dữ liệu này không ủng hộ giải thích FRR cao do kích hoạt sàn. Không loại trừ các kiểu nhạy chuẩn hóa khác; chưa có phép đối chứng thay chuẩn hóa trong task này.

## Theo ngày lịch sau enrollment

| Khoảng ngày | Mã có dữ liệu | Từ chối / lượt | FRR macro | FRR pooled |
|---|---:|---:|---:|---:|
|1-7|17|97/162|60,41%|59,88%|
|8-30|33|447/638|67,75%|70,06%|
|31+|34|2233/2765|77,50%|80,76%|

Các khoảng đã chốt trước chạy. Thành phần mã và số lượt khác nhau; bảng không chứng minh FRR tăng do thời gian. Macro và pooled chênh nhau vì trọng số tài khoản khác nhau.

## Đóng góp nhóm timing nguồn

| Nhóm | Số chiều | Tỷ phần trung bình/lượt, mọi genuine ngày sau | Tỷ phần trên genuine bị từ chối |
|---|---:|---:|---:|
|PP|5|22,39%|22,45%|
|PR|6|33,26%|32,96%|
|RP|5|22,28%|22,55%|
|RR|5|22,07%|22,03%|

Tỷ phần là đóng góp khoảng cách tuyệt đối chia tổng khoảng cách trên từng lượt, sau đó lấy trung bình; không phải tỷ phần nguyên nhân lỗi. PR có6chiều, nhóm khác5chiều nên so sánh tổng nhóm có ảnh hưởng số chiều. Không suy ra nên bỏ PR hoặc chọn lại feature. PR/RP giữ định nghĩa nguồn, chưa gán thành hold của cùng phím.

## Phân bố toàn bộ tài khoản DEV

| Mã | FRR OOF | Ngày sau: lỗi/lượt | FRR ngày sau | SD OOF | Median z OOF | Median z ngày sau |
|---|---:|---:|---:|---:|---:|---:|
|user_001|55,00%|10/10|100,00%|14.435|-0.405|0.138|
|user_002|50,00%|160/199|80,40%|15.608|-0.463|-0.193|
|user_004|50,00%|193/203|95,07%|12.190|-0.488|0.918|
|user_005|90,00%|48/69|69,57%|39.746|-0.340|-0.404|
|user_007|70,00%|17/20|85,00%|16.725|-0.341|-0.154|
|user_011|75,00%|19/20|95,00%|32.780|-0.349|-0.189|
|user_016|65,00%|25/30|83,33%|12.463|-0.274|0.047|
|user_019|55,00%|103/182|56,59%|11.382|-0.240|-0.378|
|user_021|60,00%|70/89|78,65%|17.148|-0.358|-0.119|
|user_022|95,00%|70/72|97,22%|29.776|-0.326|-0.215|
|user_025|60,00%|1/10|10,00%|21.230|-0.411|-0.753|
|user_026|60,00%|66/78|84,62%|11.086|-0.253|0.078|
|user_030|75,00%|332/350|94,86%|18.204|-0.330|0.400|
|user_031|50,00%|58/66|87,88%|17.429|-0.478|-0.044|
|user_033|65,00%|183/200|91,50%|11.945|-0.207|0.350|
|user_034|60,00%|24/39|61,54%|14.391|-0.404|-0.367|
|user_037|70,00%|90/117|76,92%|16.078|-0.285|-0.185|
|user_039|60,00%|45/55|81,82%|18.267|-0.429|-0.190|
|user_041|70,00%|237/241|98,34%|28.967|-0.389|0.196|
|user_044|55,00%|36/58|62,07%|17.663|-0.347|-0.100|
|user_046|70,00%|89/112|79,46%|15.255|-0.337|0.079|
|user_047|70,00%|65/89|73,03%|7.003|0.035|0.231|
|user_050|55,00%|42/80|52,50%|12.177|-0.345|-0.446|
|user_052|75,00%|52/88|59,09%|26.169|-0.312|-0.414|
|user_055|60,00%|4/19|21,05%|14.188|-0.391|-0.577|
|user_057|65,00%|117/133|87,97%|37.489|-0.394|-0.264|
|user_060|65,00%|7/10|70,00%|7.499|-0.197|-0.330|
|user_062|60,00%|54/98|55,10%|10.267|-0.370|-0.392|
|user_065|60,00%|75/98|76,53%|11.586|-0.306|0.013|
|user_067|45,00%|8/10|80,00%|15.092|-0.517|-0.261|
|user_069|75,00%|7/15|46,67%|10.763|-0.347|-0.476|
|user_075|50,00%|12/97|12,37%|15.552|-0.473|-0.774|
|user_078|65,00%|137/220|62,27%|10.520|-0.428|-0.340|
|user_084|55,00%|49/49|100,00%|15.944|-0.313|0.608|
|user_087|60,00%|175/198|88,38%|10.859|-0.327|0.279|
|user_089|70,00%|13/20|65,00%|12.024|-0.331|-0.175|
|user_102|65,00%|9/10|90,00%|14.231|-0.262|-0.092|
|user_104|60,00%|4/10|40,00%|9.988|-0.387|-0.590|
|user_111|60,00%|2/10|20,00%|14.172|-0.367|-0.680|
|user_112|65,00%|36/48|75,00%|27.036|-0.361|-0.290|
|user_116|85,00%|32/33|96,97%|36.273|-0.426|-0.176|
|user_117|65,00%|1/10|10,00%|7.954|-0.294|-1.113|

## Quyết định sau chẩn đoán

1. Giữ baseline/ngưỡng và kết quả TEST. Chưa đủ bằng chứng quy FRR cao cho sàn MAD/SD, một nhóm feature hay riêng tuổi hồ sơ.
2. Hướng đối chứng tiếp đáng xem xét là kiểm độ nhạy của ngưỡng z chung giữa các tài khoản trên DEV, với ngân sách FAR và đánh giá genuine cùng điều kiện. Cần chốt trước một thay đổi duy nhất và kiểm leakage trước chạy; chưa chọn quy tắc hoặc ngưỡng mới trong task này.
3. GREYC-Web đã được dùng phát triển/chẩn đoán; các kết quả cải tiến tiếp trên nguồn này phải gắn nhãn phát triển. Không dùng lại TEST đã xem như kiểm chứng độc lập mới.

## Artifact và tái lập

Hình: [DEV FRR](../figures/greyc_dev_frr_diagnostics_20261115.png). Dữ liệu tổng hợp: `results/greyc_dev_frr_results.json`, `accounts.csv`, `day_bins.csv`, `feature_groups.csv`, `checks.json` cùng prefix. Protocol: `GREYC_DEV_FRR_DIAGNOSTIC_PROTOCOL.md`. Điểm từng lượt và projection DEV ở thư mục ignored.

Kiểm tra bằng `python scripts/validate_greyc_dev_frr.py`. Runner `diagnose_greyc_dev_frr.py` từ chối ghi đè kết quả đã có. 5/5 test tổng hợp kiểm cách ly TEST, ranh giới ngày, raw/z tie, sàn SD/MAD và tổng đóng góp; validator tính lại OOF/full-profile bằng công thức độc lập trên42DEV. Báo cáo6/37/40trang, ZIPv2, source/config và kết quả cũ giữ hash. Không push/deploy/ghiDB hoặc đổi điểm.
