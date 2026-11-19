# Tương thích đặc trưng và điều kiện thu trên DEV GREYC-Web

Ngày15/11/2026. Rà42tài khoản DEV,840enrollment và3.565capture ngày sau. Đối chiếu raw sự kiện/timing và metadataUser-Agent, không fit detector mới, không chấm TEST hoặc chọn lại ngưỡng. Dùng nhãn từ chối DEV đã lưu trong chẩn đoán trước.

## Ý nghĩa vector đã kiểm từ raw

Gọi dᵢ là thời điểm nhấn và uᵢ là thời điểm nhả theo thứ tự sự kiện nguồn. Đơn vị timestamp và vector đều milliseconds; không nhân/chia đơn vị trong adapter.

| Vector nguồn | Số chiều | Công thức khớp raw | Capture đối chiếu khớp |
|---|---:|---|---:|
|p_pp|5|dᵢ₊₁ − dᵢ (DD)|4400/4405|
|p_pr|6|uᵢ − dᵢ (cùng chỉ số nguồn)|4400/4405|
|p_rp|5|uᵢ₊₁ − dᵢ (DU kế tiếp)|4400/4405|
|p_rr|5|uᵢ₊₁ − uᵢ (UU)|4400/4405|

**p_rp không phải dᵢ₊₁−uᵢ (UD của CMU).** Tên vector không đủ để suy ra công thức. Adapter đã dùng nguyên21timing nguồn từ đầu, không gán thành31featureCMU, nên không có bằng chứng lỗi đảo vector/đổi đơn vị ở4.400capture đã đối chiếu. Tuy nhiên biểu diễn hai nguồn khác nhau; không khẳng định chuyển miền cùng feature.

Có3capture cho PP và RR trùng giá trị, nên có nhiều công thức khớp tại những hàng đó; không suy ra hai vector luôn đồng nghĩa.

## Ngoại lệ cần giữ trong hồ sơ audit

- 5capture có7press/6release, chưa đối chiếu được bằng ghép chỉ số đơn giản; không tự loại, sửa raw hoặc ghi lại kết quả mô hình.
- Tổng6capture có thứ tự mã phím press/release không khớp. Có chồng lặp với nhóm5capture trên; không cộng thành11capture độc lập. Ghép cùng chỉ số không đủ chứng minh hold-time cùng phím cho những ca này.
- Keycode ở vị trí ký tự có dấu thay đổi:50/191/201 và một ca83; một số capture có mã bổ trợ16hoặc255. Không gán những khác biệt này thành lỗi người tham gia hoặc khác bàn phím khi chưa ghép sự kiện.
- Bản audit giữ toàn bộ kết quả cũ. Các tuyên bố “đã khớp raw” ở đây chỉ áp4.400capture;5capture còn lại là chưa xác minh, không coi đạt chỉ vì vector đã hữu hạn/đúng chiều.

## User-Agent và lỗi DEV

User-Agent được đọc chỉ cho DEV và phân lớp browser/OS; không xuất chuỗiUA gốc hoặc hashfingerprinttừngngười. “Đã thấy” nghĩa chuỗiUA đầy đủ từng xuất hiện trong20enrollment của chính mã; “chưa thấy” chỉ khác chuỗi, có thể do cập nhật phiên bản, không chứng minh đổi máy/bàn phím.

| Nhóm ngày sau | Genuine bị từ chối / lượt | FRR pooled |
|---|---:|---:|
|UA đã thấy trong enrollment|562/791|71,05%|
|UA chưa thấy trong enrollment|2215/2774|79,85%|

Có **21/42** mã có nhiều chuỗiUA ngay trong enrollment. NhómUAđãthấy vẫn cóFRRcao;khônggiảithíchmọilỗibằngđổibrowser.
Trong **22** mã có cả hai nhóm ngày sau, hiệu số FRR 'UAchưa thấy − UAđãthấy' trung bình theo mã là **+12.46điểm phần trăm**; 17 mã tăng và 5 mã giảm. Đây là mô tả hậu nghiệm, không kiểm định hoặc tác động nhân quả của browser.

Nhóm tài khoản, ngày lịch và số lượt khác nhau;UAđổi có thể đi cùng tuổi hồ sơ. Dù đối chiếu trong cùng mã vẫn chưa kiểm soát thời gian/thiết bị/thói quen gõ. Không dùng bảng này để chọn loại browser khỏi đánh giá.

## Quyết định

1. Giữ baseline/ngưỡng và kết quả TEST. Không thử công thức chuẩn hóa mới trong lượt audit.
2. Trước khi thử lại feature, cần bộ ghép raw theo mã phím có xử lý modifier và audit thứ tựpress/release, kiểm bằng dữ liệu giả rồi ápDEV. Không tự sửa adapter đãfreeze; nếu thay biểu diễn phải tạo phiên bản/protocol mới và công bố tác động dữ liệu.
3. Các phân tích thiết bị nên dùng metadata có thể xác minh;User-Agent hiện chỉ là proxybrowser/OS. GREYC-Web đã xem là nguồnpháttriển,khôngtestmới.

## Artifact và xác minh

`scripts/audit_greyc_dev_compatibility.py` chỉ đọc nhánhpassphrases42DEV trong tar,khôngextractall/đọc profiletên/tuổi. `results/greyc_dev_compatibility_audit.json` lưu mapping/ngoạilệ/tổng hợp; CSVaccounts/conditions/paired_ua giữ đủ mã và số đếm. `scripts/validate_greyc_dev_compatibility.py` kiểm bảo toànhash,đối chiếu42mã với countsDEVđãlưu vàphân sốUA; không gọi scoring.4/4test synthetic kiểm công thức/negativeinterval/rawschema/UAclassification.

Các kiểm tra hash/chia nhóm không thay thế lần đối chiếu raw; chưa viết bộ xử lý5ca ngoại lệ. Báo cáo6/37/40trang,ZIPv2,raw/core/config,điểm100nộibộ vàkếtquảTESTgiữnguyên.Khôngpush/deploy/DBwrite.
