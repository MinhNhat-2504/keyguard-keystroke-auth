# Dữ liệu tự thu — KeyGuard

Thư mục `collected/` chứa nhịp gõ phím của **15 người tham gia** (mã ẩn danh P01 đến P15), tổng **601 mẫu**.

## 1. Nội dung thu
- Mọi người gõ lặp lại **câu cố định `.tie5Roanl`** rồi nhấn Enter (giống bộ CMU Keystroke Benchmark).
- Mỗi dòng trong `Pxx.jsonl` là một lần gõ, gồm: `participant_id`, `session`, `rep` (số lần gõ trong phiên), `collected_at` (giờ server ghi) và `events` (danh sách `{key, type: down|up, t}`, `t` tính bằng mili giây từ `performance.now()`).
- Mẫu chỉ được ghi khi người gõ nhập đúng câu cố định (phân biệt hoa thường) và kết thúc bằng Enter.

## 2. Quy mô
Số liệu đếm trực tiếp từ các file trong `collected/`.

| Mã | Số mẫu | Phiên | Số mẫu theo ngày (server ghi) |
|---|---|---|---|
| P01 | 41 | phiên 1: 40, phiên 2: 1 | 09/11: 40, không có thời gian: 1 |
| P02 | 40 | phiên 1: 40 | 10/11: 39, không có thời gian: 1 |
| P03 | 40 | phiên 1: 40 | 04/11: 40 |
| P04 | 40 | phiên 1: 40 | 07/11: 40 |
| P05 | 40 | phiên 1: 40 | 10/11: 40 |
| P06 | 40 | phiên 1: 40 | 10/11: 40 |
| P07 | 40 | phiên 1: 40 | 10/11: 40 |
| P08 | 40 | phiên 1: 40 | 10/11: 40 |
| P09 | 40 | phiên 1: 40 | 07/11: 40 |
| P10 | 40 | phiên 1: 40 | 07/11: 12, 10/11: 28 |
| P11 | 40 | phiên 1: 40 | 10/11: 40 |
| P12 | 40 | phiên 1: 40 | 10/11: 40 |
| P13 | 40 | phiên 1: 40 | 10/11: 40 |
| P14 | 40 | phiên 1: 40 | 10/11: 40 |
| P15 | 40 | phiên 1: 40 | 10/11: 40 |

Các ngày có thu dữ liệu: 04/11, 07/11, 09/11, 10/11.

## 3. Ẩn danh
- Mỗi người chỉ có một **mã ẩn danh** (P01, P02, ...) do server cấp tự động.
- Dữ liệu không chứa tên, email, số điện thoại hay nội dung gõ nào khác ngoài câu cố định.
- Bảng đối chiếu mã với danh tính thật không được lưu trong repo.

## 4. Đồng ý tham gia
Người tham gia được mời tự nguyện và được cho biết dữ liệu chỉ ghi thời gian gõ phím, dùng cho đồ án. Mẫu đồng ý nằm ở `docs/mau_dong_y.docx` (hoặc file tương ứng trong repo).

## 5. Lưu ý về dữ liệu và hạn chế
- **Chủ yếu 1 phiên mỗi người.** Do hạn chế thời gian và khó mời người tham gia, phần lớn người chỉ gõ một phiên khoảng 40 lần, thay cho 2 đến 3 phiên ở các ngày khác nhau như kế hoạch. Vì vậy chưa đánh giá được độ ổn định nhịp gõ qua nhiều ngày.
- **Hai mẫu thu bằng bản collector đầu tiên:** mẫu đầu của P01 (phiên 2) và P02 (phiên 1, lần 1) do người thu gõ từ trước ngày 04/11, nên **không có `collected_at`**. Các mẫu còn lại đều do server ghi thời gian.
- **Dữ liệu từng bị mất và thu lại.** Server demo chạy trên gói miễn phí của Render, ổ đĩa tạm thời nên dữ liệu bị xóa khi khởi động lại. Một số người đã gõ lại sau khi mất dữ liệu; vì vậy ngày thu của một số mã không trùng với ngày tạo mã trong `participants.json`.
- **P10** có dữ liệu ở hai ngày (07/11 và 10/11) do thu tiếp sau khi mất dữ liệu.
- Số người (15) nằm trong khoảng 15 đến 20 theo kế hoạch; quy mô còn nhỏ nên kết quả đánh giá chỉ mang tính tham khảo.
