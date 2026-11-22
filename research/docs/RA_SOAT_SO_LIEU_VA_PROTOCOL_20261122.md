# Rà soát số liệu và protocol trước khi nộp

Ngày rà: 22/11/2026. Hạn hiện hành do nhóm thông báo: hết ngày 24/11/2026. Phần này đối chiếu kết quả đã lưu và cách triển khai; không chạy thí nghiệm mô hình mới, không chọn ngưỡng mới và không tạo thêm dữ liệu.

Kết luận: chưa phát hiện sai lệch trong các phép đối chiếu số học đã chạy. Các quyết định ban đầu về thích nghi, tổng hợp CV và shrink25 vẫn giữ nguyên khi tính chênh lệch từ phân số theo tài khoản. Rà code và các kiểm thử giả lập được chọn chưa phát hiện TEST tham gia chọn ngưỡng trong các runner được kiểm. Kết luận này có phạm vi cụ thể, không chứng minh toàn dự án không có mọi dạng rò rỉ hoặc nguồn gốc dữ liệu được xác minh độc lập.

## Số liệu được tính lại ở mức nào

Runner `scripts/audit_results_independent_20261122.py` chỉ dùng thư viện chuẩn Python, không gọi hàm tính metric hoặc model của thí nghiệm. Bản ghi `results/independent_numeric_audit_20261122.json` lưu hash các đầu vào, số phép đối chiếu và kết quả tính lại. Số phép đối chiếu là số mệnh đề trong audit, không phải số test hay cỡ mẫu nghiên cứu.

| Phạm vi | Bằng chứng và phép đối chiếu | Giới hạn |
|---|---|---|
| Tự thu, loại toàn bộ khóa trùng | Áp lại `z > tau` trên 297 dòng genuine; 49 bị từ chối, FRR 49/297 = 16,50%. Cộng số đếm từng mã: FAR đầu 284/1050 = 27,05%, FAR cuối 331/1050 = 31,52%. | Chỉ FRR được tính lại từ điểm từng lượt; FAR được cộng từ số đếm tài khoản. |
| Nhạy cảm với giữ dòng đầu | Áp lại quyết định trên 298 dòng genuine và đối chiếu summary/per-user/by-session. | 298 dòng này dùng lại phần lớn mẫu của phương án chính. Tổng 595 quyết định kiểm lại không phải 595 mẫu độc lập. |
| CMU chọn ngưỡng | Cộng 45 dòng tài khoản của ba chính sách và đối chiếu FAR/FRR TEST trong threshold_selection.csv. | Không tái tạo điểm impostor, không chạy lại chọn ngưỡng. |
| Khảo sát đặc trưng, enrollment, 10 cách chia | Cộng các fold, kiểm lựa chọn từ inner ranking; tính lại trung bình/SD qua split. | Cách chia lặp dùng cùng 15 mã; SD không phải CI. |
| KeyRecs và CMU nhiều phiên | Cộng tài khoản/phiên; đối chiếu baseline, family được chọn và số đếm tổng. | Không áp lại ngưỡng trên mọi raw score vì hồ sơ không lưu toàn bộ điểm đó. |
| Matched/CV | Cộng cặp impostor về tài khoản cho 192 nhóm; kiểm không có target làm impostor của chính nó. | Đây là số nhóm kiểm, không phải số tài khoản độc lập mới. |
| Shrink25, GREYC, phân vị OOF, covariance | Tính lại pooled và macro từ số đếm tài khoản; kiểm các bảng tổng hợp có phân biệt hai cách tính. | Không fit lại model hay kiểm chứng mới trên nguồn ngoài. |
| Benchmark và biểu đồ | Tính lại EER/AUC trung bình và SD theo mã từ CSV; kiểm nguồn số liệu trong script vẽ và giữ nguyên ảnh khoa học khi sửa báo cáo. | Không tính lại ROC/EER từ điểm gốc, không đọc ngược giá trị từ pixel biểu đồ. |

Audit đã đối chiếu 325 nhóm tài khoản và 192 nhóm cặp–tài khoản; các nhóm có thể dùng lại cùng tài khoản ở nhiều phương án. Trên KeyRecs cố định hồ sơ, baseline có 909/10560 nhận nhầm và 2450/3301 genuine bị từ chối; soft được chọn từ DEV có 904/10560 và 2443/3301. Chênh lệch 5 và 7 lượt là mô tả, không tự chứng minh lợi ích chắc chắn thống kê.

## Rà đường đi dữ liệu trong code

| Thành phần | Điều đã kiểm trong triển khai | Giới hạn cần giữ trong báo cáo |
|---|---|---|
| Benchmark CMU | `scripts/run_benchmark.py::build_splits` lấy genuine train ở 200 mẫu đầu, test ở 200 mẫu sau; impostor train/test tách mã trong mỗi tài khoản. | Các mã này được quan sát trong benchmark trước khi chia DEV/TEST cho ngưỡng. Không gọi toàn tiến trình là holdout chưa xem. RandomForest có dữ liệu impostor train, khác mô hình một lớp. |
| Ngưỡng CMU | `scripts/select_threshold.py` chia mã seed42, chỉ DEV chọn tau; TEST được chấm sau khi tau cố định. `threshold_at_far` giữ ties nguyên nhóm, nhận khi điểm ≤ tau. | FAR DEV là điều kiện hiệu chỉnh, không bảo đảm FAR TEST. Việc các mã TEST từng được dùng ở benchmark vẫn còn. |
| Enrollment và CV | `keyguard/model.py::genuine_score_stats` bỏ held fold trước fit; `keyguard/soft_weighting.py::fit_calibrated` fit lại lọc/trọng số chỉ trong train fold. | CV dùng các mẫu enrollment đã có; không phải rolling-origin CV để dự báo tương lai. Việc dùng enrollment của tài khoản TEST để tạo profile là đúng bài toán đăng ký, khác dùng TEST chọn tham số toàn cục. |
| Khảo sát lồng nhau | `keyguard/research.py::pool/choose_variant` giới hạn target và impostor theo ids của phân vùng; chọn theo balanced error vòng trong, tie-break tên. | Toàn bộ khảo sát trên bộ tự thu đã xem là phát triển. Probe đầu có thể trùng enrollment của tài khoản nguồn; không diễn giải DEV là holdout độc lập. |
| KeyRecs lần đầu | `keyguard/external_validation.py::external_cache` tạo profile từ S1[:20]; runner chỉ đưa DEV S1 vào chọn phương án/tau, TEST S2 vào đánh giá. | Hiệu chỉnh DEV của nguồn mới; không chuyển nguyên ngưỡng CMU. Sau khi xem kết quả, nguồn không còn mới cho cải tiến sau đó. |
| Thích nghi và CV theo tuổi | `keyguard/matched_adaptation.py` và runner `scripts/run_cv_aggregation_control.py`: chấm genuine trước cập nhật, chỉ dùng lịch sử quá khứ; probe không vào profile. Hai ngưỡng matched được chọn trước TEST; CV dùng chung ngưỡng baseline cố định. | Genuine cập nhật theo giả định xác minh lý tưởng. CV cùng ngưỡng z không có nghĩa cùng FAR DEV. Probe S2 dùng cho đánh giá theo protocol, không phải mô phỏng mọi thông tin sẵn có của một dịch vụ theo thời gian thực. |
| Prior shrink25 | `scripts/dispersion_shrinkage_core.py` loại tài khoản DEV đang hiệu chỉnh khỏi prior; prior TEST chỉ từ enrollment của DEV. Fit local MAD trên train fold. | Prior ngoài tài khoản không lấy TEST hay S2. Không so trực tiếp với warm-up/update vì đây là hồ sơ tĩnh20 mẫu. |
| GREYC-Web lần đầu | `scripts/run_greyc_web_account_benefit.py` kiểm DEV/TEST tách mã, enrollment và test nằm ở ngày khác; dùng công thức shrink25 cố định. | Không gọi các đối chứng DEV về sau là kiểm chứng nguồn mới. User-agent không tự chứng minh thiết bị vật lý khác nhau. |
| Phân vị và covariance | Hai runner chỉ đọc cache42 DEV, tách 28calibration/14evaluation, score TEST gốc không được dùng; full–diag là đối chứng chính. | 14 mã vẫn là DEV đã xem, không phải holdout xác nhận mới. Full tốt hơn Manhattan tham chiếu không thay thế tiêu chí full–diag đã định. |

Đã kiểm 104 mục hash code/protocol trong bảy freeze liên quan: tất cả khớp. Việc khớp hash chỉ xác nhận code hiện tại đúng bản đã khóa, không tự chứng minh code đúng hoặc khóa công khai trước thí nghiệm. Các dấu thời gian trong hồ sơ là chứng cứ nội bộ.

## Kiểm thử và quyết định báo cáo

Môi trường sạch chạy đạt 87/87 kiểm thử giả lập, bao gồm tám nhóm kiểm thử hiện có và năm ca mới cho bộ audit. Những ca liên quan kiểm việc held-row không vào fit, TEST/S2 không đổi ngưỡng DEV, score trước update, probe không update, prior loại tài khoản và macro không bị thay bằng pooled. Năm ca mới cố ý đưa sai tỷ lệ, tổng mẫu, overlap và cách tính macro để xác nhận audit từ chối. Bản ghi: `results/protocol_synthetic_clean_audit_20261122.json`.

Lượt thử đầu ở venv cũ có 80 ca đạt và hai ca lỗi do Windows Application Control chặn DLL của scikit-learn, lưu trong XML local. Không sửa code mô hình hoặc bỏ ca lỗi; chạy lại ở venv sạch đã có cho kết quả đầy đủ nêu trên. Đây là kiểm thử giả lập, không phải 87 thí nghiệm dữ liệu thật.

Báo cáo ngày22/11 giữ toàn bộ bảng số liệu và hình khoa học, sửa bảng quyết định 11 nhóm để nêu câu hỏi, điều kiện so sánh và kết luận. Giữ baseline vì chưa có bằng chứng đủ để thay cấu hình trong phạm vi các đối chứng đã làm; không gọi baseline tối ưu hoặc an toàn triển khai. Các bản ngày20/11 và báo cáo sáu trang được giữ lại. Không sửa artifact khoa học đã khóa, không thử thêm hệ số và không tạo phiên thu giả.
