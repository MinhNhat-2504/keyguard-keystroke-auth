# Mã nguồn và phân công thực hiện

Nhóm gồm Trịnh Ngọc Minh Nhật và Nguyễn Anh Thư. Báo cáo nộp lại ngày24/11 trình bày ý tưởng, mục tiêu, cách đánh giá và kết quả. Các thuật toán nền là phương pháp có sẵn; phần nhóm thực hiện gồm thư viện nhịp gõ, ứng dụng thu/xác thực, các phép đối chứng và phân tích kết quả trên nhiều nguồn.

| Phần việc | Người phụ trách theo phân công nhóm | Vị trí mã nguồn |
|---|---|---|
| Đặc trưng và mô hình | Nhật | `research/keyguard/features.py`, `research/keyguard/detectors.py`, `research/keyguard/model.py` |
| So sánh mô hình, chọn ngưỡng và phân tích | Nhật | `research/scripts/run_benchmark.py`, `research/scripts/select_threshold.py`, `research/scripts/evaluate_collected.py`, các runner nghiên cứu |
| Thu mẫu, giao diện và API | Thư; Nhật tham gia phần kiểm tra và lưu trữ bổ sung | `web/app.py`, `web/templates/`, `web/static/` |
| Kiểm thử sử dụng và hồ sơ vận hành | Thư | `web/tests/`, `evidence/render_cutover_thu.md`, `evidence/screenshots/` |
| Báo cáo và tổng hợp kết quả | Nhật; hai thành viên đối chiếu phần việc của mình | `reports/`, `research/results/` |

Thư viện nghiên cứu và ứng dụng web được lưu riêng vì chúng tương ứng với những phiên bản đã đánh giá. Bản web dùng mã runtime `b0bd22e13fd4f1c56ca2e638936daaa5f0767e39`; hồ sơ vận hành lấy từ `thu-branch` tại `004bf1d847791fdd59126efbeda64755222fd0c8`. Snapshot nộp bài giữ nguồn gốc đó, không thay đổi lịch sử đóng góp của các nhánh.

Từ gốc repo, chạy `python verify_submission.py` để kiểm các tệp công khai, số đếm và tham chiếu trong báo cáo. Lệnh này chỉ dùng thư viện chuẩn Python. Cách cài môi trường và chạy ứng dụng nằm trong README. Các thử nghiệm dùng dữ liệu giả có thể chạy theo những lệnh đã ghi; chạy lại toàn bộ nghiên cứu cần đúng dữ liệu gốc và phiên bản thư viện.

Raw tự thu, tài khoản, hồ sơ cá nhân, OTP và thông tin kết nối cơ sở dữ liệu không có trong repo public. Các bảng công khai đủ để đối chiếu kết quả đã lưu, nhưng không thay thế dữ liệu gốc khi cần tính lại điểm từng lượt. Nội dung báo cáo giữ giới hạn này và không coi kết quả OTP mô phỏng là bằng chứng bảo mật của một dịch vụ thật.
