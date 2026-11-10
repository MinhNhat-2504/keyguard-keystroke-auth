# Bàn giao phần mô hình của Nhật cho Thư

## Các file cần tích hợp

- `keyguard/` và `models/model_config.json` từ cùng phiên bản main. Giữ cấu hình được script sinh ra; không tự đặt ngưỡng khác để demo dễ qua.
- API chuẩn: `enroll(samples)`, `verify(profile, events)`, `update(profile, events)`. Profile là dict JSON. `confidence` là điểm hiển thị logistic, **không phải xác suất danh tính đã được hiệu chuẩn**.
- `n_enroll` và `min_enroll` trong cấu hình đều là 20. Mỗi sample là danh sách down/up cho `.tie5Roanl` **và Enter**, kết thúc sau keyup Enter. `t` tính bằng mili giây lấy từ `performance.now()`.

Payload enroll:

```json
{"username": "demo01", "samples": [[{"key": ".", "type": "down", "t": 0}, {"key": ".", "type": "up", "t": 100}]]}
```

Đoạn JSON chỉ minh họa shape, cố ý rút gọn: phải có đủ các phím và 20 danh sách samples mới hợp lệ. Có dữ liệu đầy đủ trong `data/sample/sample_from_cmu.jsonl`, nhãn nguồn CMU dựng lại, không phải dữ liệu thu thật. Không gửi `events: [{attempt_index, events}]` cho enroll hoặc sự kiện dạng `{down_time, up_time}`.

```python
from keyguard.model import enroll, verify, update, InvalidSampleError

profile = enroll(samples)  # ít nhất 20 lượt hợp lệ
try:
    confidence, accepted = verify(profile, events)
except InvalidSampleError:
    # trả 400: gõ sai/thiếu sự kiện; không update
    raise
if accepted:
    profile = update(profile, events)
else:
    # tạo challenge phía backend, gắn tài khoản và mẫu đang chờ
    # chỉ sau khi backend xác nhận OTP đúng/chưa hết hạn:
    # profile = update(profile, pending_events)
    pass
# lưu profile bằng JSON sau cập nhật, chống ghi đè tài khoản trái phép
```

Backend phải chặn ID chứa đường dẫn, tài khoản trùng, JSON sai kiểu; không tin cờ `otp_ok` do client tự gửi. Hàm update không tự kiểm tra quyền hoặc OTP. Main hiện là thư viện; API/OTP thuộc nhánh web, ví dụ này không xác nhận web đã hoàn thành.

## Dữ liệu cần bàn giao để Nhật hoàn thành 1.5 và report

1. JSONL ẩn danh đúng schema, không trùng người/phiên/rep, ≥15 người, ≥2 phiên khác ngày, ≥40 lượt mỗi phiên. Gửi kèm nhật ký chỉ chứa mã người, số phiên, ngày, loại bàn phím/thiết bị, số mẫu hợp lệ/lỗi và xác nhận đã xin đồng ý. Không commit danh tính hay chữ ký.
2. Ảnh thật các màn hình collector, đăng ký đủ 20, đăng nhập thành công, yêu cầu OTP và xác minh thành công/thất bại. Ghi commit web, lệnh chạy và thiết bị chụp.
3. CSV live test có ≥10 impostor và ≥20 lượt chính chủ; lưu vai trò ẩn danh, accepted trước OTP, confidence, kết quả OTP, thời điểm và tài khoản đích ẩn danh. Không ghi mã OTP.

Lệnh nhận dữ liệu (PowerShell, chạy từ root main):

```powershell
./.venv/Scripts/python.exe scripts/audit_collected.py --input "data/collected/*.jsonl"
./.venv/Scripts/python.exe scripts/evaluate_collected.py --input "data/collected/*.jsonl" --data-kind collected
```

Không copy hai dòng dữ liệu hiện có thành nhiều lượt để đủ điều kiện. Nhật có thể chuẩn bị công cụ/phân tích nhưng chưa thể kết luận độ chính xác thực tế khi chưa có dữ liệu.
