# Dữ liệu

## 1. CMU Keystroke Dynamics Benchmark (`data/raw/`, không commit)

- 51 người, mỗi người gõ câu `.tie5Roanl` + Enter 400 lần, chia 8 phiên (50 lần/phiên), các phiên cách nhau ít nhất một ngày.
- 31 đặc trưng thời gian (giây): giữ phím (H), nhấn–nhấn (DD), nhả–nhấn (UD).
- Tải về:

  ```bash
  curl -L -o data/raw/DSL-StrongPasswordData.csv https://www.cs.cmu.edu/~keystroke/DSL-StrongPasswordData.csv
  ```

- Trích dẫn: K. S. Killourhy and R. A. Maxion, "Comparing Anomaly-Detection Algorithms for Keystroke Dynamics," in *Proc. IEEE/IFIP International Conference on Dependable Systems and Networks (DSN)*, 2009, pp. 125–134.

## 2. Dữ liệu nhóm tự thu (`data/collected/`)

- Thu qua trang web `collector/` (TV2 phụ trách), cùng câu `.tie5Roanl` + Enter.
- Mỗi dòng JSONL là một lần gõ:

  ```json
  {"participant_id": "P07", "session": 2, "rep": 15,
   "events": [{"key": ".", "type": "down", "t": 0.0}, {"key": ".", "type": "up", "t": 92.4}]}
  ```

  `t` tính bằng mili-giây. `participant_id` là mã ngẫu nhiên.
- Chỉ commit dữ liệu đã ẩn danh. Danh sách đối chiếu mã ↔ tên và mẫu đồng ý có chữ ký **không** đưa lên repo.

## 3. Dữ liệu mẫu (`data/sample/`)

`sample_from_cmu.jsonl` được dựng lại từ CMU bằng `scripts/make_sample_jsonl.py`, đúng định dạng JSONL ở trên. Chỉ dùng để chạy thử quy trình và web demo, không dùng làm kết quả.

## 4. Kiểm tra chất lượng trước đánh giá

```powershell
python scripts/audit_collected.py --input "data/collected/*.jsonl"
python scripts/evaluate_collected.py --input "data/collected/*.jsonl" --data-kind collected
```

Audit xuất `results/collected_audit.json`, đếm theo người/phiên và ghi lý do của dòng JSON hỏng, schema sai, đặc trưng không hữu hạn hoặc trùng `(participant_id, session, rep)`; mẫu lỗi/trùng không được đếm vào số hợp lệ. Yêu cầu phân công tối thiểu: 15 người × 2 phiên × 40 mẫu. Cần nhật ký ẩn danh để xác minh khác ngày, thiết bị và đồng ý; không đưa danh tính/chữ ký lên repo.

Đánh giá yêu cầu ≥25 mẫu/người (20 enroll + ≥5 lượt test); nếu không ai đủ, chương trình dừng mà không sinh kết quả FAR/FRR. CLI yêu cầu ghi nhãn `--data-kind collected|cmu-derived|synthetic`. Với mẫu CMU dựng lại, dùng `--data-kind cmu-derived --out-prefix pipeline_test_sample`, không trình bày bảng này như thử nghiệm thu thật. Ghi rõ các kịch bản early/late có thể trùng mẫu nếu dữ liệu ít.

Mốc 01/11/2026: audit hai file của nhánh web ghi nhận 2 mẫu hợp lệ/2 mã, chưa đủ enroll/test; xem `results/review_collected_audit.json`. Số mã không xác nhận số người thật.

## 5. Snapshot và protocol sơ bộ ngày 10/11/2026

Đã nhập nguyên byte15 file/601 dòng từ commit `44a610bd120b09e2838e76073cb164c3ce6cac36` của thu-branch; `collected_manifest.json` ghi SHA-256 và nguồn. Không chỉnh sửa raw. Có mẫu đồng ý tại docs/mau_dong_y.docx của nhánh nguồn; chưa đối chiếu xác nhận theo từng mã. Repo này không sao chép danh tính/chữ ký hoặc tài khoản demo.

Audit tổng quát:600 khóa duy nhất,15 mã,0 mã đủ2 phiên40 lượt. P10 có hai rep29 (dòng29,39) và thiếu rep39;2 mẫu cũ thiếu timestamp. Phân tích chính loại cả hai dòng trùng cùng2 mẫu thiếu timestamp →597 dòng, sắp collected_at UTC, enroll20 còn297 genuine test. Tất cả mẫu giữ lại có session1; P10 cùng session trải hai ngày. Không đánh số lại hoặc gán ngày giả. `evaluate_collected.py` mặc định dùng protocol này; audit mặc định first giữ dòng đầu chỉ để thống kê quy mô, nên số600 trong audit khác597 trong phân tích có chủ đích. Cần metadata thiết bị/ngày/đồng ý bổ sung.

Hướng dẫn đủ lệnh và kết quả, kèm độ nhạy xử lý khóa trùng: [docs/COLLECTED_PRELIMINARY.md](../docs/COLLECTED_PRELIMINARY.md). Sau import, dữ liệu hiện đủ đánh giá sơ bộ trong phiên, chưa đáp ứng toàn bộ yêu cầu thu nhiều ngày. Các ghi chú ở mục cũ là lịch sử, không coi hiện tại chỉ có2 mẫu.

Gói main không theo dõi/push thư mục collected hay bảng genuine từng lượt; cả hai giữ local/ignore. Manifest vẫn có nguồn và SHA-256 để đối chiếu sau import. Chỉ công bố bảng tổng hợp, hình và report ở lần bàn giao này; không tự xác nhận việc repo nguồn đã có raw đồng nghĩa mọi người đã đồng ý công khai.
