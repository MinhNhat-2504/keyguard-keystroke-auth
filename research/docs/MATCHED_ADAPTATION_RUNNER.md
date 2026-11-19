# Runner riêng cho so sánh thích nghi

Runner `scripts/run_matched_adaptation.py` thực hiện thiết kế tại `MATCHED_ADAPTATION_PROTOCOL.md`, kế hoạch máy đọc `results/matched_adaptation_plan.json`. Thêm module `keyguard/matched_adaptation.py` và test riêng; không sửa code/protocol cũ đã đóng băng.

## Ba chế độ tách biệt

```powershell
# Audit metadata/hash; chạy test bằng dữ liệu giả; khóa code/test/môi trường.
# Không chấm mô hình trên dữ liệu CMU/KeyRecs thật.
./.venv/Scripts/python.exe scripts/run_matched_adaptation.py --freeze

# Kiểm tra khóa hiện có, chỉ đọc, không scoring hoặc ghi lại manifest.
./.venv/Scripts/python.exe scripts/run_matched_adaptation.py --check

# Bước đánh giá sau này: chỉ chạy khi đã chuyển sang bước chạy dữ liệu thật.
./.venv/Scripts/python.exe scripts/run_matched_adaptation.py --run
```

Không truyền chế độ sẽ dừng với hướng dẫn, không tự chạy mô hình. `--freeze` từ chối nếu đã có manifest, sidecar hoặc bằng chứng test; không âm thầm khóa lại sau khi sửa code. `--run` yêu cầu hash code, test report, raw, kế hoạch/protocol, artifact được bảo toàn và phiên bản môi trường đều khớp. Manifest/hash chỉ phục vụ truy vết nội bộ, không phải chữ ký chống sửa hoặc đăng ký trước công khai.

## Bằng chứng trước scoring

- `results/matched_adaptation_runner_freeze.json/.sha256`: SHA-256 code thư viện, runner, test; Python/OS và NumPy, pandas, SciPy, scikit-learn, pytest; hash dữ liệu và kế hoạch; mốc UTC đóng băng.
- `results/matched_adaptation_synthetic_tests.xml`: JUnit của riêng bộ test giả lập. Không cộng với số test lịch sử để gọi là đã chạy lại toàn suite.
- `tests/test_matched_adaptation.py`: tách dev/test, không dùng S2 để hiệu chỉnh, cả hai ngưỡng được chọn trước test, chấm trước cập nhật sau, probe không vào hồ sơ, cửa sổ50, warm-up không vào FRR, tổng cặp khớp tài khoản, macro khác pooled, quyết định trước làm tròn, không ghi đè kết quả, phát hiện code/môi trường/manifest đổi.
- So sánh bằng dữ liệu giả 31/47 chiều với core `score_session_stream` xác nhận phép warm-up không cần lưu quyết định vẫn tạo đúng điểm S2 của phép chấm/cập nhật tuần tự cũ. Đây là kiểm tra thuật toán trên dữ liệu giả, không phải tái chạy KeyRecs thật.

Freeze chỉ audit raw/schema/split/số lượng trước scoring; kiểm thử sử dụng dữ liệu tạo bằng NumPy và thư mục tạm. Runner chọn ngưỡng với hàm nhận **chỉ các mảng S1 dev**; không truyền S2 hoặc test vào hiệu chỉnh. Hai ngưỡng đều được cố định trước chấm test. Hai nguồn được audit xong trước khi lần chạy thật bắt đầu.

## Kết quả dành cho bước chạy sau

Runner chỉ tạo các file dưới đây khi gọi `--run`, không tạo chúng khi freeze/check:

- `matched_adaptation_started.json`: nhật ký bắt đầu, hash manifest.
- `matched_adaptation_results.json`: kết quả hai nhánh/từng nguồn và diễn giải mô tả theo kế hoạch.
- `matched_adaptation_accounts.csv`, `matched_adaptation_pairs.csv`, `matched_adaptation_deltas.csv`: số đếm theo mã, cặp có hướng, chênh ghép theo mã.

Nếu có bất kỳ file nào trong nhóm này, runner dừng để tránh ghi đè hoặc chạy lại sau lỗi mà che lịch sử; không có cờ force/resume. Khi lỗi, giữ nhật ký và điều tra riêng. Trước ghi kết quả, kiểm tra hash lần nữa; JSON kết quả chỉ được ghi sau các CSV. Đây không phải giao dịch nhiều file nguyên tử: nếu ghi dở, các file/journal được giữ và lần chạy tiếp sẽ bị chặn.

Lần chạy thật phải đối chiếu ngưỡng và số đếm pooled/từng mã KeyRecs với kết quả đã có của window50/decay20. Lệch sẽ dừng, không tự sửa kết quả cũ. Macro được ghi riêng với pooled; chiều giả thuyết dùng phân số chính xác từ số đếm trước khi làm tròn. Không gộp hai nguồn hoặc thêm CI/p-value theo từng lượt độc lập.

## Trạng thái của bước triển khai

Đã viết runner/test; chỉ thực hiện kiểm thử giả lập, audit và freeze/check ở bước này. Không gọi `--run`; báo cáo, ngưỡng chính, kết quả lịch sử và điểm rubric giữ nguyên. CMU/KeyRecs đã xem, do đó các kết quả từ runner này sau này vẫn là phát triển phương pháp.

### Cập nhật sau khi người dùng yêu cầu chạy

Đã kiểm tra khóa rồi gọi `--run`, hoàn tất và đối chiếu artifact bằng `scripts/validate_matched_adaptation.py`. Kết quả/phân tích tại `MATCHED_ADAPTATION_RESULTS.md`: CMU giảm FAR/FRR, KeyRecs giảm FRR nhưng tăng FAR; chưa đạt tiêu chí nhất quán trên hai nguồn. Journal và các file kết quả đã tồn tại, vì vậy không gọi lại `--run` để ghi đè. Code/plan/freeze và kết quả lịch sử giữ nguyên; báo cáo/trang khám phá chưa được cập nhật bằng kết quả này.
