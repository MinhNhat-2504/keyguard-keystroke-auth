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
