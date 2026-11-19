# Kiểm tra dữ liệu trước khi phân tích lần thu mới

Đây là công cụ local kiểm tra file JSONL, chưa tích hợp vào web/Render. Không thay bộ trích đặc trưng hoặc quy tắc loại mẫu đã khóa cho nghiên cứu cũ.

```powershell
python scripts/collection_preflight.py duong-dan/P01.jsonl duong-dan/P02.jsonl --out duong-dan-rieng/preflight.json
```

Mã thoát 0: không phát hiện lỗi theo checklist; 2: cần xem lại. Không suy ra đã có đồng ý tham gia, danh tính thật, phần cứng đã xác minh hoặc đủ nhiều ngày. File rỗng cũng cần xem lại. Không đặt output trùng input.

Checklist cho **lần thu mới**:

- `participant_id`: mã giả danh không rỗng; `session`, `rep`: số nguyên dương, không nhận boolean. Khóa mã–phiên–lượt phải duy nhất trên tất cả file kiểm cùng lúc. Đánh dấu **mọi dòng** trong nhóm trùng, kể cả dòng có lỗi khác; không chọn giữ dòng đầu/cuối.
- `collected_at`: ISO 8601 có múi giờ. Chỉ kiểm định dạng, không chứng minh đây là giờ server đáng tin. `device_id`: mã thiết bị giả danh không rỗng, nên được cấp nhất quán cho cùng bộ máy/bàn phím trong đợt thu; không dùng tên người hoặc user-agent làm bằng chứng phần cứng.
- `events`: danh sách theo thứ tự thời gian, thời gian ms hữu hạn không âm, loại down/up hoặc keydown/keyup. Kiểm down thiếu up, up không có down, lặp down và chuỗi `.tie5Roanl` + Enter đúng hoa/thường ở lúc nhấn. Modifier không tính vào câu nhưng vẫn kiểm cân bằng sự kiện. Có `code` thì ghép theo code; nếu không có thì ghép theo key chuẩn hóa. Chữ R lúc nhả có thể thành r khi Shift đã nhả. Thời gian flight âm do gõ chồng là hợp lệ, không tự đánh lỗi.
- JSON lỗi, NaN/Infinity hoặc trường JSON lặp cũng bị đánh dấu; không lặng lẽ lấy giá trị cuối.

Báo cáo ghi số thứ tự input, dòng, mã lỗi và hash nguồn, không chép participant_id, raw events hay secret. Giữ báo cáo có liên hệ đến dữ liệu thật riêng tư. Đọc danh sách `review_rows`, đối chiếu bản xuất nguyên byte; nếu không đủ bằng chứng thì ghi thiếu thông tin. Không tự bù giờ/thiết bị, đánh lại rep hoặc tạo phiên.

Collector hiện tại ghi `participant_id/session/rep/collected_at/events`, chưa có `device_id` từng mẫu. Vì vậy file cũ có thể bị đánh dấu thiếu thiết bị theo checklist mới; **không hồi tố đổi tập đánh giá, kết quả hoặc điểm đã chốt**. Việc thêm trường vào API/web cần thay đổi riêng có kiểm thử, rồi mới áp dụng cho lượt thu tương lai. Bộ kiểm tra local giúp phát hiện trước phân tích, chưa ngăn được việc server nhận dữ liệu xấu.
