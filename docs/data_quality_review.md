# Biên bản kiểm tra chất lượng dữ liệu (B1)

* **Người thực hiện:** Thư.
* **Ngày giờ chạy:** 14/11/2026.
* **Môi trường:** Windows, Python 3.12, thiết lập biến môi trường `$env:PYTHONUTF8 = "1"` để hiển thị đúng tiếng Việt.
* **Ghi chú:** Script và bộ test do Claude viết theo yêu cầu của tôi; tôi tự chạy trên máy cá nhân, tự kiểm tra kết quả và tự viết biên bản này.

## 1. Lệnh đã chạy

1. **Chạy kiểm thử tự động trên dữ liệu giả (synthetic data):**
   ```powershell
   $env:PYTHONUTF8 = "1"
   cmd /c "python tests/test_data_quality_thu.py > docs\data_quality\test_run.txt 2>&1"
   ```
   * **Kết quả:** 5/5 ca đạt (`OK`), `exit code = 0`.

2. **Chạy kiểm tra chất lượng trên bộ dữ liệu tự thu thật:**
   ```powershell
   cmd /c "python scripts/check_data_quality.py > docs\data_quality\check_run.txt 2>&1"
   ```
   * **Kết quả:** Đã quét xong 15 file (601 dòng JSON hợp lệ), `exit code = 1` (do phát hiện có lỗi mức error trong dữ liệu thật).

## 2. Kết quả kiểm thử trên dữ liệu giả

Bộ dữ liệu giả được tách riêng tại thư mục `tests/fake_quality_data/` nhằm chứng minh công cụ nhận diện chính xác từng nhóm vấn đề khác nhau.

| Nhóm vấn đề / Lỗi | Phân loại | Số lượng phát hiện |
| :--- | :--- | :---: |
| `CHUA_GHI_NHAN/THIEU_THIET_BI` | Chưa ghi nhận | 5 |
| `CHUA_GHI_NHAN/THIEU_THOI_GIAN` | Chưa ghi nhận | 1 |
| `LOI/SU_KIEN_KHONG_HOP_LE` | Lỗi dữ liệu | 3 |
| `LOI/KHOA_TRUNG` | Lỗi dữ liệu | 2 |
| `LOI/JSON_KHONG_DOC_DUOC` | Lỗi dữ liệu | 1 |
| `LOI/REP_KHONG_LIEN_TUC` | Cảnh báo | 1 |
| `LOI/SAI_MA_NGUOI` | Lỗi dữ liệu | 1 |
| `LOI/THIEU_TRUONG` | Lỗi dữ liệu | 1 |

**Tổng kết kiểm thử:** 5/5 ca test đạt yêu cầu, chứng minh script phân biệt rạch ròi giữa lỗi nghiêm trọng, cảnh báo và thông tin chưa ghi nhận.

## 3. Kết quả kiểm tra trên dữ liệu thật

Quá trình quét toàn bộ 15 file (601 dòng) trong thư mục dữ liệu thu thập thực tế ghi nhận kết quả như sau:

| Chỉ số / Loại vấn đề | Kết quả thực tế | Ghi chú chi tiết |
| :--- | :---: | :--- |
| Tổng số file & dòng hợp lệ | 15 file / 601 dòng | 100% dòng đọc được định dạng JSON |
| `LOI/KHOA_TRUNG` | **2** (mức error) | Xảy ra ở người tham gia **P10**: nhãn `rep 29` xuất hiện ở 2 dòng khác nhau (dòng 29 và dòng 39). Chi tiết xem `data_quality_issues.csv`. |
| `LOI/REP_KHONG_LIEN_TUC` | **1** (mức warning) | Xảy ra ở **P10**: thiếu số thứ tự `rep 39`. |
| `CHUA_GHI_NHAN/THIEU_THIET_BI` | **15** | Cả 15 mã người tham gia đều chưa có trường thông tin thiết bị/bàn phím trong file raw. |
| `CHUA_GHI_NHAN/THIEU_THOI_GIAN` | **2** | Một dòng ở P01 và một dòng ở P02 (mẫu thu đời đầu) chưa có trường mốc thời gian `collected_at`. Chi tiết xem `data_quality_issues.csv`. |

**Về trường hợp của P10:** Dữ liệu có hai dòng cùng nhãn `rep 29` (dòng 29 và dòng 39) và thiếu `rep 39`. Theo ghi chú thu thập, P10 được ghép thủ công từ hai lần thu, nhưng nguyên nhân cụ thể chưa được xác minh nên biên bản không đoán và không sửa lại số `rep`.

## 4. Phân biệt giữa "Lỗi dữ liệu" và "Thông tin chưa ghi nhận"

* **Lỗi dữ liệu (`LOI/...`):** Là những sai lệch làm vi phạm tính toàn vẹn và quy tắc cấu trúc của dữ liệu (ví dụ: trùng khóa định danh người–phiên–lượt gõ, sai định dạng JSON, thiếu trường bắt buộc hoặc sự kiện phím không hợp lệ). Những mẫu này cần được phát hiện để loại bỏ hoặc xử lý theo đúng protocol trước khi đưa vào huấn luyện/đánh giá mô hình.
* **Thông tin chưa ghi nhận (`CHUA_GHI_NHAN/...`):** Là các trường metadata bổ sung (như thông tin thiết bị, hệ điều hành hoặc timestamp ở 2 mẫu thu đời đầu) chưa được hệ thống thu thập ghi lại tại thời điểm thu. Đây là **giới hạn về phạm vi thu thập**, không phải lỗi làm hỏng chuỗi sự kiện nhịp gõ nên vẫn được tách riêng để đánh giá trung thực.

## 5. Bảo toàn dữ liệu gốc (Kiểm chứng SHA-256)

* **Kết quả kiểm tra:** `SHA-256 trước = sau: ĐÚNG` trên toàn bộ 15 file dữ liệu thật và dữ liệu giả.
* **Ý nghĩa:** Đảm bảo nguyên tắc bất biến của dữ liệu thô . Công cụ chỉ thực hiện thao tác đọc (read-only) để kiểm tra và xuất báo cáo ra thư mục riêng, tuyệt đối không làm biến đổi, ghi đè hay làm sai lệch bất kỳ byte nào của dữ liệu gốc.

## 6. Vì sao lệnh kiểm tra dữ liệu thật thoát với mã lỗi 1 (`exit code = 1`)

Theo quy ước của chương trình chạy bằng dòng lệnh, `exit code = 0` biểu thị mọi thứ đều sạch sẽ và không có lỗi nghiêm trọng. Khi chạy `check_data_quality.py` trên bộ dữ liệu thật, script phát hiện có **2 lỗi mức `error`** (trùng khóa ở P10). Do đó, việc script chủ động trả về `exit code = 1` là **hành vi hoàn toàn đúng thiết kế** nhằm cảnh báo cho người vận hành biết bộ dữ liệu đang tồn tại lỗi cần lưu ý trước khi sử dụng.

## 7. Giới hạn của công cụ và quy trình

* Script chỉ dừng lại ở mức **phát hiện, thống kê và cảnh báo**, không tự động sửa chữa hay xóa dữ liệu trong các file raw gốc.
* Tuân thủ nguyên tắc trung thực khoa học: không tự ý điền bù thông tin thiết bị, phiên thu hay mốc thời gian phỏng đoán cho các mẫu bị thiếu.
* Đối với trường hợp trùng khóa ở P10, hệ thống chỉ xuất báo cáo ghi nhận hiện trạng không tự ý đổi số `rep`. Việc loại `rep 29` của P10 khi đánh giá mô hình do Nhật quyết định (đang chờ Nhật xác nhận).

## 8. Tệp bằng chứng đính kèm

Toàn bộ kết quả chạy thực tế được lưu trữ đầy đủ tại thư mục `docs/data_quality/`:
1. `docs/data_quality/test_run.txt`: Log kết quả chạy 5 ca kiểm thử tự động trên dữ liệu giả.
2. `docs/data_quality/check_run.txt`: Log kết quả chạy kiểm tra toàn bộ 15 file dữ liệu thật.
3. `docs/data_quality/data_quality_report.json`: Báo cáo tổng hợp chi tiết định dạng JSON (kèm mã kiểm tra SHA-256).
4. `docs/data_quality/data_quality_issues.csv`: Danh sách chi tiết từng dòng lỗi, cảnh báo và thông tin chưa ghi nhận (chỉ sử dụng mã ẩn danh).