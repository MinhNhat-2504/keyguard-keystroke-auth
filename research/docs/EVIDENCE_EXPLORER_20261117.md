# Trang đọc bằng chứng và độ bất định — 17/11/2026

Mở `explorer/index.html` bằng trình duyệt, chọn **Bằng chứng & độ bất định** hoặc dùng `index.html#evidence`. Trang chạy từ file local, không cần server, credentials hoặc kết nối Render/Neon.

## Nội dung mới

- 11 nhóm/35 dòng kết quả từ bản tổng hợp đã chốt. Lọc nhóm và nguồn, đọc giao thức/kết luận, phân biệt vai trò đối chứng, phương án thử, tham chiếu mô tả và so sánh lịch sử. Không xếp hạng hoặc cộng tỉ lệ giữa các giao thức.
- Bảng ghi cách tính macro/pooled/trung bình 10 cách chia; số lỗi và mẫu số đi cùng hàng khi có. SD qua cách chia được ghi rõ không phải CI. Mỗi dòng có link artifact, JSON pointer và SHA-256.
- Bộ chọn riêng cho 5 phân tích khoảng theo tài khoản, hiển thị 30 đại lượng từ kết quả hồi cứu đã lưu. Tỉ lệ tuyệt đối có đơn vị %, hiệu candidate–control có đơn vị điểm phần trăm; dấu âm là giảm lỗi. Bộ chọn này độc lập với bảng 35 dòng.
- Hai CSV: các dòng đang lọc (giữ đủ trường nguồn, far/frr ở thang 0–1) và đủ 30 đại lượng khoảng (thang %/điểm phần trăm). CSV giữ độ chính xác gốc; màn hình làm tròn để đọc.
- Bảng hỗ trợ cuộn trong vùng riêng, có focus bàn phím; khi chỉ xem một nhóm, ẩn cột nhóm lặp lại. Không thêm hiệu ứng hoặc chọn mô hình tự động.

Giữ nguyên cảnh báo: khoảng bootstrap là mô tả có điều kiện trên dữ liệu/cấu hình đã cố định; chưa mô hình hóa đủ phụ thuộc chéo do cùng impostor, không bảo đảm bao phủ 95% ở người mới. Không kiểm định/cứu candidate bằng khoảng chứa hoặc không chứa 0. Covariance chưa chạy nguồn ngoài B vì cổng phát triển không đạt. Baseline được giữ để bảo toàn phiên bản, chưa đủ bằng chứng triển khai.

## Nguồn và kiểm tra

`scripts/build_evidence_explorer.py` chỉ xuất từ `results/research_decision_20261115.json` và `results/account_uncertainty_20261115.json` sau kiểm source hashes. Không raw, fit, scoring hoặc thay ngưỡng. `scripts/validate_evidence_explorer.py` đối chiếu độc lập object xuất với nguồn: 35 dòng/11 nhóm/30 đại lượng đúng nguyên giá trị.

`node scripts/check_evidence_explorer.mjs` dùng Chrome headless: 33 trạng thái lọc/140 lượt kiểm dòng, 30 khoảng, 8 tab và giữ lựa chọn. Kiểm hồi quy 144 cặp tài khoản ở mục đối chứng cũ. Tải thật 2 CSV; đã dùng Python csv đối chiếu 35 dòng/30 đại lượng với nguồn. Không có lỗi JS, yêu cầu mạng ngoài hoặc tràn ngang ở 320/390/1440 px. Xem ảnh desktop/mobile trong `report/preview/evidence-*-20261117.png`.

Artifact: `results/evidence_explorer_export_20261117.json`, `evidence_explorer_checks_20261117.json`, `evidence_explorer_browser_checks_20261117.json`, `evidence_explorer_csv_checks_20261117.json`, `evidence_explorer_preservation_20261117.json`.

Các data JS và logic nghiên cứu cũ giữ hash. Báo cáo/gói v4 giữ nguyên; trang mới chưa đưa vào ZIP v4. Thay đổi còn ở workspace nghiên cứu, chưa push. Checkout web và phần triển khai/backup của Thư không bị thay đổi trong lượt này. Khung dừng đề xuất ngày16/11 đã qua; tài liệu này không xác nhận đã dừng thu hoặc đã triển khai Render.
