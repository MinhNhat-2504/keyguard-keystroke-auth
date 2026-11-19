# Kết quả co MAD về prior dev — 15/11/2026

Thiết kế/code/env/raw được khóa sau 11 kiểm thử giả lập và trước chẩn đoán/scoring. Chỉ thử λ=0,25, không dò lại sau kết quả. Hồ sơ cố định20mẫu, không warm-up/cập nhật; đây là phát triển trên CMU/KeyRecs đã xem, không holdout mới.

## 1. Chẩn đoán enrollment dev

| Nguồn | Mã dev | Cặp mã–feature | MAD chạm sàn | MAD/prior <0,1 |
|---|---:|---:|---:|---:|
|CMU|36|1116|0|0|
|KeyRecs fixed-text|66|3102|0|8|

Không có MAD full-enrollment chạm sàn1e−9. Tỷ lệ nhỏ chỉ xuất hiện8/3102cell KeyRecs theo mốc đã định. Tỷ phần đóng góp trung bình OOF lớn nhất ở một cell là khoảng6,38% trên CMU và4,63% trên KeyRecs; đây là trung bình theo20lượt, không phải chặn trên cho một lượt riêng. Chưa chứng minh một feature chi phối lỗi test hoặc sàn là nguyên nhân. Chẩn đoán chỉ nhận devS1[:20], không dùng probe/test/S2 hay candidate để chọnλ.

## 2. Kết quả cùng protocol tĩnh

Tiêu chí chính: Δmacro_FRR<0 và Δmacro_FAR≤0, candidate−baseline. Mỗi nhánh chọn ngưỡng riêng trên dev FAR≤5%, không tách điểm trùng. Prior median MAD từ các mãdev khác; khi chấm test dùng toàndev, không có test trong prior.

| Nguồn | Nhánh | FAR macro | FRR macro | Nhận nhầm/tổng | Genuine từ chối/tổng |
|---|---|---:|---:|---:|---:|
|CMU|baseline|5,52%|55,47%|116/2100|416/750|
|CMU|shrink25|5,62%|56,27%|118/2100|422/750|
|KeyRecs fixed-text|baseline|8,61%|74,28%|909/10560|2450/3301|
|KeyRecs fixed-text|shrink25|8,65%|73,18%|913/10560|2415/3301|

CMU: nhận nhầm116→118, genuine từ chối416→422; cảhai lỗi tăng. KeyRecs: nhận nhầm909→913, genuine từ chối2450→2415; giảm35lượt genuine bị từ chối nhưng tăng4nhận nhầm, là đánh đổi. Không nguồn nào đạt tiêu chí. Baseline KeyRecs tái lập kết quả static trước (909/10560,2450/3301).

FRR KeyRecs macro baseline74,28% vàcandidate73,18%; pooled tương ứng74,22% và73,16% do mẫu số mỗi mã khác nhau. Không gộp với phép matched/decay có lịch warm-up/update hoặc kết quả nhiều cách chia.

## 3. Quyết định và bảo toàn

Giữ baseline/cấu hình triển khai. Không tìm thêmλ để cứu kết quả, không xóa các mã bất lợi, không thêmCI/p-value. Kết quả không bác bỏ mọi cách shrinkage; nó chỉ không ủng hộ công thức và hệ số đã khóa trong phép thử này. Một bước nghiên cứu khác phải có lý do/thiết kế mới, không trình bày nguồn đã xem là test mới.

Bốn báo cáo gốc, bản37trang, gói_v2, mô hình, raw và mọi artifact đã bảo vệ vẫn đúngSHA. Lưu phân tích mới riêng; không sửa báo cáo/handover đã bàn giao. B1–B3 Thư không được làm thay.

Nguồn: dispersion_shrinkage_plan/freeze/diagnostics/started/results trong results/; CSV96account và4218cell; lệnh `python scripts/run_dispersion_shrinkage.py --check` và `python scripts/validate_dispersion_shrinkage.py`.
