# Audit bộ ghép trên toàn DEV GREYC-Web — 15/11/2026

Áp nguyên bộ ghép same-key đã kiểm10test lên toàn4.405capture của42DEV:840enrollment và3.565lượt ngày sau. Không thay policy modifier, không chọn thứ tựFIFO/LIFO cho ca mơ hồ, không đọc/chấmTEST hoặc sửa vector nguồn.

## Độ bao phủ

| Chỉ số | Số capture | Tỷ lệ / toàn DEV |
|---|---:|---:|
|Ghép xác định|4404|99,9773%|
|Chưa ghép đầy đủ|1|0,0227%|
|Ghép xác định và tất cả vector nguồn khớp|4403|99,9546%|
|Ghép xác định nhưng khác ít nhất1vector|1|0,0227%|
|Capture có modifier tách riêng|4|0,0908%|

Trong các capture ghép xác định, tỷ lệ khác vector là **0,0227%**. Nhómmodifier có thể trùng nhóm vector khớp; không cộng mọi hàng bảng thành tổng.

| Nhóm | Capture | Ghép được | Chưa ghép | Khác vector nguồn | Có modifier |
|---|---:|---:|---:|---:|---:|
|enrollment|840|840|0|0|1|
|later_dev|3565|3564|1|1|3|

## Các phát hiện

- Không phát hiện thêm ca chưa ghép/khác vector ngoài các ngoại lệ đã công bố. Bộ ghép toànDEV làm rõ độ bao phủ, không biến6ngoại lệ thành6lỗi dữ liệu độc lập.
- Bốn captureShift16 có vector nguồn khớp sau táchmodifier; không cần sửa feature cho những ca này.
- user_050,ngày sau:releasehai phím cuối đảo thứ tự. PPkhớp;PR/RP/RRkhác khi căn theo đúng mãphím. Nguồn dùng thứ tựevent, nên đây là khácngữ nghĩa, không tự gọi nguồn hỏng.
- user_102,ngày sau:press255khôngcórelease;capturegiữunresolved. Không bỏ255theo đoán hoặc coi6cặpcòn lại là xác minh toàncapture.
- Các mã lặp có nhiều cách ghép hợp lệ được coi mơ hồ theo rule đãtest; toàn tập lần này không phát sinh nhóm mơ hồ mới.

## Toàn bộ42mã DEV

| Mã | Capture | Ghép được | Chưa ghép | Khác vector | Có modifier |
|---|---:|---:|---:|---:|---:|
|user_001|30|30|0|0|0|
|user_002|219|219|0|0|0|
|user_004|223|223|0|0|0|
|user_005|89|89|0|0|1|
|user_007|40|40|0|0|0|
|user_011|40|40|0|0|0|
|user_016|50|50|0|0|0|
|user_019|202|202|0|0|0|
|user_021|109|109|0|0|0|
|user_022|92|92|0|0|0|
|user_025|30|30|0|0|0|
|user_026|98|98|0|0|0|
|user_030|370|370|0|0|0|
|user_031|86|86|0|0|0|
|user_033|220|220|0|0|0|
|user_034|59|59|0|0|0|
|user_037|137|137|0|0|2|
|user_039|75|75|0|0|0|
|user_041|261|261|0|0|0|
|user_044|78|78|0|0|0|
|user_046|132|132|0|0|0|
|user_047|109|109|0|0|0|
|user_050|100|100|0|1|0|
|user_052|108|108|0|0|1|
|user_055|39|39|0|0|0|
|user_057|153|153|0|0|0|
|user_060|30|30|0|0|0|
|user_062|118|118|0|0|0|
|user_065|118|118|0|0|0|
|user_067|30|30|0|0|0|
|user_069|35|35|0|0|0|
|user_075|117|117|0|0|0|
|user_078|240|240|0|0|0|
|user_084|69|69|0|0|0|
|user_087|218|218|0|0|0|
|user_089|40|40|0|0|0|
|user_102|30|29|1|0|0|
|user_104|30|30|0|0|0|
|user_111|30|30|0|0|0|
|user_112|68|68|0|0|0|
|user_116|53|53|0|0|0|
|user_117|30|30|0|0|0|

## Kết luận và giới hạn

1. Khác biệt biểu diễn chỉ xuất hiện ở1/4.404captureghépđược; có1/4.405capturechưa ghép. Chưa tính ảnh hưởng điểmFRR/FAR, nên không kết luận sửa chúng sẽ cải thiện mô hình hoặc giải thích FRRcao.
2. Chưa có động lực sửa toàn bộ chuẩn hóa chỉ từ các ngoại lệ này. Giữ adapter/mô hình/ngưỡng và kết quảTEST. Nếu thử biểu diễn khác phải dùng protocolphiênbảnmới, công bố mọi loại bỏ và mức ảnh hưởng riêng.
3. Có thể chốt audit này thành phụ lục dữ liệu/bản bàn giao tiếp theo. Mã255 vẫn cần định nghĩa collector gốc; không suy từ keycode sang bànphím/ngườigõ.

Matcher chỉ xác minh cặp event theo code/timestamp và công thứcvector; không chứng minh đúng văn bản Unicode/thiết bị/danh tính. Mã phím phụ thuộc browser/layout; chưa kiểm nhân quả theo điều kiện thu.

## Kiểm tra và artifact

`scripts/audit_greyc_dev_full_pairing.py` áp matcher đãtest10/10,giữ hash/time/trạngthái trước audit. `scripts/validate_greyc_dev_full_pairing.py` kiểm độc lập bằng hoán vị ghép cùngcode trên cả4.405capture,so pairs/vector/delta/count/protectedhash;khônggọimatcherđểtựxácminh.

`results/greyc_dev_full_pairing.json`, `started.json`, `checks.json`, `captures.csv`, `accounts.csv` cùngprefix. CSVcapture chỉmãẩn/cohort/case/index/flag/delta,khôngtimestamp/raw. Inputraw/pairing chi tiết ởprivateignored. Khôngpush/deploy/DBwrite,khôngsửareport6/37/40/ZIPv2. Điểm100nộibộgiữnguyên.
