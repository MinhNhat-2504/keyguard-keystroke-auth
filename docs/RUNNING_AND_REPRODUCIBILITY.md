# Chạy local và đối chiếu kết quả

Các lệnh dưới đây dành cho PowerShell và Python 3.11. Bắt đầu từ gốc repo, trên nhánh `submission/final-20261119`.

## Kiểm bản nộp bằng Python có sẵn

```powershell
python verify_submission.py
```

Lệnh chỉ dùng thư viện chuẩn. Nó kiểm hash trong manifest, các tệp được báo cáo dẫn, số đếm đã lưu, bảng và công thức tương ứng. Kết quả này xác nhận tính nhất quán của phần công khai; không huấn luyện lại mô hình hoặc kiểm toàn bộ dịch vụ đang chạy.

## Tạo môi trường riêng

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r validation/requirements-tested.txt
```

[requirements-tested.txt](../validation/requirements-tested.txt) giữ các phiên bản đã kiểm trên Windows/Python 3.11, gồm thư viện nghiên cứu và Flask. Dependency riêng của nghiên cứu và ứng dụng cũng được ghi trong từng thư mục. Các runner có khóa cần đúng môi trường và đầu vào của phép thử.

## Chạy ứng dụng web

```powershell
cd web
$env:PYTHONUTF8 = '1'
$env:KEYGUARD_STORAGE = 'file'
$env:DATABASE_URL = ''
$env:KEYGUARD_DATA_DIR = Join-Path $PWD 'local-test-data'
..\.venv\Scripts\python.exe app.py
```

Mở `http://127.0.0.1:5000`. Dữ liệu local nằm trong `web/local-test-data/`; OTP chỉ là mô phỏng. Đăng ký cần 20 lượt hợp lệ của `.tie5Roanl` kèm Enter. Bộ kiểm tra chuẩn hóa trong `research/` là prototype nghiên cứu riêng, chưa tích hợp vào ứng dụng này.

Ví dụ kiểm thử API local, chạy tại `web/`:

```powershell
..\.venv\Scripts\python.exe -X utf8 -m unittest tests.test_collection_api.FileCollectionAPI
..\.venv\Scripts\python.exe -X utf8 -m unittest discover -s tests -p test_data_quality_thu.py
..\.venv\Scripts\python.exe -X utf8 tests/test_otp_boundaries_thu.py
```

## Kiểm logic bằng dữ liệu giả

Từ gốc repo, chuyển vào `research/` và chạy nhóm kiểm thử chuẩn hóa:

```powershell
cd research
..\.venv\Scripts\python.exe -m pytest tests/test_calibration_preflight.py tests/test_calibration_routing.py tests/test_calibration_influence.py -q
```

Các ca này kiểm điều kiện cảnh báo, tuyến quyết định, mẫu số và ví dụ đại số; không tạo bằng chứng về hiệu quả trên người dùng mới. Những nhóm kiểm thử khác được giữ trong `research/tests/` và `web/tests/`; một số ca lịch sử cần dữ liệu riêng.

Hai audit bổ sung có nhóm kiểm thử reader và thống kê xếp hạng riêng, gồm ca giữ hai cột trùng tên ở KeyRecs:

```powershell
..\.venv\Scripts\python.exe -m pytest tests/test_dev_enrollment_audit.py tests/test_dev_enrollment_columns.py tests/test_residual_score_diagnostic.py -q
..\.venv\Scripts\python.exe -m pytest tests/test_calibration_order_audit.py -q
..\.venv\Scripts\python.exe -m pytest tests/test_group_sensitivity.py -q
..\.venv\Scripts\python.exe -m pytest tests/test_attack_exposure.py -q
```

## Đối chiếu kết quả đã lưu

Tại `research/`, các lệnh sau dùng thư viện chuẩn và chạy được với phần công khai:

```powershell
..\.venv\Scripts\python.exe scripts/audit_usn_transfer_20261124.py --saved-only
..\.venv\Scripts\python.exe scripts/verify_calibration_preflight_20261124.py
..\.venv\Scripts\python.exe scripts/verify_calibration_routing_20261124.py
..\.venv\Scripts\python.exe scripts/verify_calibration_influence_20261124.py
..\.venv\Scripts\python.exe scripts/verify_preflight_dev_audit_20261124.py --saved-only
..\.venv\Scripts\python.exe scripts/verify_usn_residual_diagnostic_20261124.py
..\.venv\Scripts\python.exe scripts/verify_calibration_order_20261124.py --saved-only
..\.venv\Scripts\python.exe scripts/verify_group_sensitivity_20261124.py
..\.venv\Scripts\python.exe scripts/verify_attack_exposure_20261124.py
```

Bộ USN áp lại ngưỡng cho score đã lưu và cộng lại các tỷ lệ; chế độ `--saved-only` báo rõ bỏ qua raw và kho bảo toàn lịch sử local. Các bộ còn lại đối chiếu cảnh báo, đếm tuyến và phép tính minh họa. Chúng không suy ra kết quả OTP hoặc chạy lại toàn bộ mô hình từ đặc trưng gốc.

Audit DEV đối chiếu đủ 102 hồ sơ từ artifact; kiểm lại CV từ raw cần `--check-raw` và đúng hai tệp nguồn có hash trong khóa. Chẩn đoán USN đếm lại AUC bằng so trực tiếp các cặp score đã lưu. Cả hai giữ nguyên quy tắc/điểm/ngưỡng và ghi rõ dữ liệu đã được xem.

Kiểm độ nhạy fold đối chiếu đủ 132 hồ sơ × 5 cách từ artifact. Chế độ `--check-raw` cần raw CMU/KeyRecs/USN cùng dependency nghiên cứu, dùng lại input reader đã kiểm và tính CV bằng Python statistics. Đây là kiểm độ nhạy hiệu chỉnh, không phải phép thử ngưỡng hoặc kết quả OTP mới.

Kiểm ảnh hưởng nhóm cộng lại 23 tập con trực tiếp từ 15.610 quyết định, bao gồm bảng đủ nhóm, từng nhóm và các trường hợp bỏ từng mã đích/câu. Chỉ thay phép cộng; không học lại, đổi ngưỡng hoặc tạo quan sát độc lập mới. Runner `python -m scripts.run_group_sensitivity_20261124 --check` kiểm mã và input đã khóa.

Kiểm mẫu giả mạo dựng ma trận 2.042 mẫu × 5 hồ sơ từ 10.210 quyết định attack, đếm số mẫu qua ít nhất một đích và histogram 0–5 hồ sơ. Kiểm khóa bằng `python -m scripts.run_attack_exposure_20261124 --check`. Kết quả chỉ mô tả kịch bản tĩnh đã xét, không đổi FAR chính hoặc mô phỏng giới hạn thử của web.

Kết quả từng lần kiểm nằm trong [validation/](../validation/) và [research/results/](../research/results/). Mỗi record có phạm vi riêng; một số file là kết quả lịch sử, không phải lần chạy hiện tại.

## Khi cần chạy lại nghiên cứu từ raw

Nguồn và điều kiện sử dụng được ghi ở [data/README.md](../research/data/README.md) cùng protocol của từng phép thử. Với USN, xem [protocol](../research/docs/USN_TRANSFER_PROTOCOL_20261124.md), [manifest nguồn](../research/results/usn_source_manifest_20261124.json) và [kết quả](../research/docs/USN_TRANSFER_RESULTS_20261124.md).

Phải có đúng dữ liệu, mã và môi trường đã khóa. Các runner đã có kết quả từ chối ghi đè; việc thử một phương án khác cần artifact và protocol riêng. Các đường dẫn `docs/`, `results/`, `scripts/` trong phần nghiên cứu được hiểu từ `research/`.

Raw tự thu, private backup và thông tin tài khoản không có trong repo. Vì vậy một bản clone công khai đủ để đối chiếu phần đã lưu nhưng chưa đủ để tái lập mọi điểm số gốc. Các bài kiểm tra PostgreSQL/restore thuộc hồ sơ riêng và dùng database local rỗng; những lệnh trên không chuyển cấu hình Render hoặc Neon.
