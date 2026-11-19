# Runner đối chứng chỉ thay tổng hợp CV

Triển khai riêng `scripts/cv_aggregation_core.py`, `scripts/run_cv_aggregation_control.py` theo `CV_AGGREGATION_CONTROL_PROTOCOL.md`. Không sửa core/protocol hoặc runner đóng băng trước đây.

## Dùng chung detector và điểm CV

Mỗi trạng thái lịch sử fit một lần:5 detector train-fold và1 detector cuối, đều là decay20. Một vector OOF không ghi được và một bộ trọng số tuổi dùng chung tạo hai bộ center/scale. Mỗi batch mẫu chỉ gọi detector score một lần rồi áp hai bộ chuẩn hóa. Không fit lại detector theo nhánh.

Chuỗi genuine chỉ có một lịch sử tối đa50 mẫu, cập nhật oracle sau chấm bất kể quyết định của hai nhánh. Probe không cập nhật, warm-up không vào FRR chính. Hai nhánh luôn dùng chung tau đã trích từ decay20 matched, không có bộ chọn ngưỡng hoặc ép candidate đạt FARdev5%.

`uniform_cv` giữ chính xác phép mean/std population của core cũ. `age_weighted_cv` dùng mean và phương sai population trọng số tuổi20, sàn scale1e−6. Công thức thay center/scale chung; chưa tách tác động riêng của mean với SD.

## Chế độ

```powershell
# Audit metadata, chạy riêng test giả lập, khóa code/test/môi trường.
./.venv/Scripts/python.exe scripts/run_cv_aggregation_control.py --freeze

# Chỉ đọc kiểm tra khóa, không scoring hoặc cập nhật manifest.
./.venv/Scripts/python.exe scripts/run_cv_aggregation_control.py --check

# Bước chạy thật sau này; chưa gọi trong lượt chuẩn bị này.
./.venv/Scripts/python.exe scripts/run_cv_aggregation_control.py --run
```

Không có chế độ mặc định chạy mô hình. Freeze từ chối khi đã có manifest/sidecar/JUnit. Run yêu cầu khóa khớp, audit mọi nguồn trước scoring, ghi journal trước fit và từ chối nếu có bất kỳ journal/kết quả cũ. Không force/resume/ghi đè để che lần chạy dở.

Trước công bố kết quả candidate, baseline phải khớp decay20 matched ở cả hai nguồn: ngưỡng, pooled, từng mã, cặp và FARdev tại ngưỡng cố định. Nếu lệch, dừng, giữ journal và điều tra; không sửa kết quả cũ. Hash được kiểm tra lại trước ghi CSV/JSON. Các file không được ghi theo một giao dịch nguyên tử; lỗi giữa chừng giữ file dở và lần chạy sau bị chặn.

## Bằng chứng và kiểm tra

- `results/cv_aggregation_control_runner_freeze.json/.sha256`: code/core/test, Python và thư viện, raw, kế hoạch/protocol, hai tau cố định và mốcUTC khóa.
- `results/cv_aggregation_control_synthetic_tests.xml`: JUnit chỉ của17test giả lập mới; không cộng với các mốc test lịch sử để nhận đã chạy toàn suite.
- `tests/test_cv_aggregation_control.py`: công thức trọng số/phương sai/sàn; trọng số đều khớp Mean/Std; uniform khớp core decay20 ở20/21/49/50 mẫu và31/47chiều; train không có held-row/age đúng vị trí; chỉ6fit mỗi trạng thái và1score mỗi batch cho cảhai nhánh; probe/future không cập nhật quá khứ; hai nhánh khác quyết định vẫn chung lịch sử; dev không đọcS2/test; đếm cặp/chuyển quyết định; macro khác pooled; tiêu chí FARưu tiên và chênh nhỏ trước làm tròn; guard ngưỡng/code/môi trường/manifest/ghi đè.

Freeze/check chỉ đọc metadata/schema/raw hash và các số đếm đã lưu; mô hình trong test chỉ học dữ liệu giả. Chưa tính điểm candidate trên dữ liệu thật trong bước này. Các file kế hoạch ban đầu giữ nguyên trạng thái lịch sử “chưa có runner”; manifest riêng ghi trạng thái triển khai mới, không sửa kế hoạch sau khi đã khóa.

Khi chuyển sang đánh giá, đầu ra riêng gồm `cv_aggregation_control_started.json`, `results.json`, `accounts.csv`, `pairs.csv`, `deltas.csv`, `transitions.csv` dưới `results/`. Không lưu raw timing hoặc vector hồ sơ vào các CSV. Kết quả ghi FARdev quan sát, macro/pooled riêng, và tiêu chí đã định `Δmacro_FAR<0`, `Δmacro_FRR≤0`. Không chọn lại tau hay thêm dung sai sau khi thấy số liệu.

CMU/KeyRecs đã được xem. Đây là kiểm soát quy tắc chuẩn hóa tại cùng ngưỡngz baseline, không so hai nhánh cùng FARdev hoặc chứng minh tổng quát hóa trên dữ liệu mới. Báo cáo, cấu hình, kết quả lịch sử và điểm rubric chưa thay đổi; chưa push.

## Cập nhật sau yêu cầu chạy

Đã `--check`/`--run` theo khóa. Baseline khớp decay20 cũ cảhai nguồn; candidate CMU giảmFAR/tăngFRR, KeyRecs tăngcảhai nênkhôngđạt tiêu chí. Xem `CV_AGGREGATION_CONTROL_RESULTS.md`, validator `scripts/validate_cv_aggregation_control.py` vàlogchecks. Journal/kếtquả đã tồn tại, không chạy lại để ghiđè. Code/plan/freeze giữ nguyên, kếtquả cũ vàhai bộbáocáo khôngđổi; giao diện chưa sửa.
