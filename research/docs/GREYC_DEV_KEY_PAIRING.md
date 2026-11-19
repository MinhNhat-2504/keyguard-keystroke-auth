# Ghép sự kiện theo mã phím — các ngoại lệ DEV GREYC-Web

Ngày15/11/2026. Hoàn tất bộ ghép và áp dụng riêng6ngoại lệ thứ tự/số lượng sự kiện đã phát hiện trên42DEV. Không sửa raw,adapter đãkhóa,ngưỡng hoặc điểm mô hình; không đọc/chấm tài khoảnTEST.

## Quy tắc đã kiểm trước dữ liệu ngoại lệ

Ghép press/release **cùng mã phím**, chỉ cho phép release timestamp≥press timestamp. Mỗi phím được xét tất cả ghép khả thi; chỉ chấp nhận khi có đúng một cách ghép. Nhấn lặp cùng mã mà nhiều cách ghép đều hợp lệ được báo mơ hồ, không mặc định FIFO/LIFO. Giữ thứ tự nhấn để tính vector chẩn đoán; thứ tự nhả có thể khác.

Modifier tách riêng theo danh sách cụ thể16/17/18/91/92/93. Không áp dụng quy tắc “mã lạ thì bỏ”:255vẫn là mã chưa biết, thiếu release thì unresolved. Việc bỏ modifier chỉ xảy ra trong phép đối chiếu chẩn đoán, không xóa sự kiện nguồn hoặc sửa dữ liệu đánh giá.

10/10test synthetic đạt trước áp ngoại lệ: phím lặp không chồng, nhả đảo thứ tự, modifier thiếu up, mã255khôngtựbỏ, phím lặp chồng mơ hồ, release trước press, zero-holdtie, thiếu up/down, schema/nonfinite/order và không sửa input. Code và outputtest được lưu hash/timestamp trước lần chạy ngoại lệ.

## Kết quả6ca

| Ca | Mã DEV | Nhóm | Kết quả ghép | Đối chiếu vector nguồn |
|---|---|---|---|---|
|1|user_005|Ngày sau|6cặp, tách Shift16|PP/PR/RP/RR đều khớp|
|2|user_037|Enrollment|6cặp, tách Shift16|PP/PR/RP/RR đều khớp|
|3|user_037|Ngày sau|6cặp, tách Shift16|PP/PR/RP/RR đều khớp|
|4|user_050|Ngày sau|6cặp, hai release cuối đảo thứ tự|PP khớp; PR/RP/RR khác khi căn đúng mã phím|
|5|user_052|Ngày sau|6cặp, tách Shift16|PP/PR/RP/RR đều khớp|
|6|user_102|Ngày sau|6cặp thông thường + press255thiếuup|Chưa giải quyết toàn capture; không tự bỏ255|

Như vậy5/6ca có ghép xác định theo quy tắc;4ca hoàn toàn khớp vector sau tách Shift. Ca4 là khác biệt **ngữ nghĩa ghép chỉ số với ghép phím**, không tự kết luận là lỗi file nguồn: nguồn có thể định nghĩa timing theo thứ tự event, khác cách diễn giải hold của cùng phím. Ca6 vẫn chưa được xác minh đầy đủ.

Audit trước có4.400capture6press/6release khớp công thức theo chỉ số;ca4 nằm trong nhóm này, nhưng trước đó code-order đã báo khác. Vì vậy “khớp công thức chỉ số” không đồng nghĩa “mọi PR là hold cùng phím”. Bốn caShiftbổ sung làm rõ4/5ca lệch độ dài trước đó;khôngnhầm thành đã xác minh toàn4.405capturebằngmatcher này.

## Tác động và quyết định

- Giữ nguyên mọi vector và kết quả đã công bố. Chưa tính mức ảnh hưởng lên FRR/FAR, không nói6ca giải thích FRRcao hoặc sửa là tăng hiệu quả.
- Không tự loạiuser_050/user_102 hoặc đưa dữ liệu ghép lại vào evaluator cũ. Nếu nghiên cứu biểu diễn theo phím, phải tạo adapter/protocolphiênbảnmới và áp quy tắc chung choDEV; công bố khác biệt với vector nguồn.
- Mã255 cần thêm bằng chứng định nghĩa collector gốc; không coi làShift hoặc phím lỗi chỉ từ giá trị. Chưa có bằng chứng để sửa.
- Bước tiếp phù hợp: audit cùng bộ ghép trên toànDEV để đo độ bao phủ và tần suất khác biệt biểu diễn, chưa scoring. Chỉ sau đó mới cân nhắc phép đối chứng feature cùng điều kiện.

## Artifact và phạm vi xác minh

- `scripts/greyc_key_pairing.py`, `tests/test_greyc_key_pairing.py`:matcher và10test.
- `scripts/audit_greyc_dev_pairing.py`:streamtar42DEV, chỉ áp matcher6ca ngoại lệ;timestamp/raw chi tiết giữprivate ignored.
- `results/greyc_dev_key_pairing_freeze.json`, `greyc_dev_key_pairing.json`, `greyc_dev_key_pairing_checks.json`:hash/chronology/kết quảẩn danh.
- `scripts/validate_greyc_dev_pairing.py`:kiểm độc lập bằng liệt kê hoán vị hợp lệ cho từng mã,đối chiếu6case/pairs/holds/vector/hash. Không gọi matcher để tự xác minh chính nó.

Không push/deploy/DBwrite;source/core/config/TEST/report6/37/40/ZIPv2 và điểm100nộibộ giữ nguyên.
