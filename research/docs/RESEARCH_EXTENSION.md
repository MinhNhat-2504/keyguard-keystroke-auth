# Nghiên cứu mở rộng KeyGuard — 13/11/2026

Thực hiện theo thứ tự người dùng yêu cầu: (1) khảo sát đặc trưng/chuẩn hóa; (2) hiệu chỉnh ngưỡng có tách nhóm mã; (3) trang khám phá kết quả offline. Chưa làm tiếp phần Thư, chưa cập nhật cấu hình sản phẩm hoặc push GitHub.

## Dữ liệu và phạm vi

- Snapshot `44a610b`: 601 dòng/15 mã; xác minh SHA-256 của 15 file trước khi chạy. Chính sách chính không đổi: loại cả hai dòng khóa P10 mơ hồ và hai dòng thiếu timestamp, còn **597 mẫu**. Sắp theo `collected_at` UTC, 20 mẫu đầu mỗi tài khoản dùng đăng ký.
- Bộ dữ liệu đã được xem và phân tích ở các lượt trước. Đây là nghiên cứu khám phá, không gọi là test mới chưa từng thấy. Mã tham gia không tự xác minh danh tính độc lập. Chủ yếu một phiên; thử nghiệm nhiều ngày vẫn là hướng phát triển.
- Không thay raw, dữ liệu live test, bảng kết quả cũ hay `models/model_config.json`. Các điểm số mới không được đưa vào cấu hình triển khai tự động.

## 1. Khảo sát 24 phương án

| Thành phần | Phương án |
|---|---|
| Detector | Scaled Manhattan dùng trung bình và độ lệch tuyệt đối trung bình (baseline); Manhattan dùng trung vị và độ lệch tuyệt đối trung vị |
| Đặc trưng | Toàn bộ 31; H giữ phím 11; DD nhấn–nhấn 10; UD nhả–nhấn 10 |
| Chuẩn hóa từng lượt | Thời gian gốc; chia tổng thời gian từ nhấn phím đầu đến nhả Enter; chia trung vị H của 11 phím |

Phép chia thực hiện trên 31 đặc trưng trước khi chọn nhóm; UD âm được giữ nguyên. Không lấy thống kê từ toàn bộ tập đánh giá để chuẩn hóa. Tổng thời gian bằng tổng 10 DD cộng H cuối; mẫu có mẫu số không dương hoặc không hữu hạn bị từ chối. Mỗi detector dùng sàn độ phân tán `1e-9`; điểm z lấy trung bình/độ lệch chuẩn của kiểm định chéo 5-fold trên 20 mẫu đăng ký, độ lệch chuẩn tối thiểu `1e-6`, giống quy ước baseline.

Chỉ hai biến thể Manhattan được khảo sát mới. Bốn họ mô hình của benchmark cũ vẫn là kết quả riêng; không trình bày rằng SVM/Isolation Forest/Random Forest đã được chạy lại trong thí nghiệm này.

## 2. Tách nhóm và chọn ngưỡng

1. Chia 15 mã thành **3 vòng ngoài**, mỗi vòng 5 mã đánh giá / 10 mã phát triển, seed 42. Mỗi mã chỉ xuất hiện một lần ở nhóm đánh giá ngoài.
2. Trong mỗi phân vùng, người đóng vai impostor cũng chỉ lấy từ các mã **cùng phân vùng** với tài khoản đích. Không dùng người của nhóm đánh giá làm dữ liệu impostor khi chọn ngưỡng.
3. Hồ sơ cố định sau 20 mẫu đăng ký. Genuine là 18–20 mẫu tiếp theo của từng mã; impostor là 5 lượt đầu và 5 lượt cuối của mỗi mã khác. Không chèn impostor vào hồ sơ hoặc giả định đã có OTP thật.
4. Trong 10 mã phát triển, 2 vòng trong (seed `42 + chỉ số vòng ngoài`) chọn phương án có trung bình `(FAR + FRR)/2` nhỏ nhất; hòa thì thứ tự tên phương án. Ở mỗi vòng trong, ngưỡng chọn trên impostor của nhóm huấn luyện trong, đánh giá trên nhóm xác thực trong. Không dùng điểm ngoài để chọn đặc trưng/chuẩn hóa/detector.
5. Với phương án đã chọn, chọn lại ngưỡng trên cả 10 mã phát triển, giữ FAR thực nghiệm ≤5%. Chấp nhận khi `z <= tau`; ngưỡng không tách nhóm điểm bằng nhau. Đánh giá trên 5 mã ngoài.
6. Đồng thời công bố toàn bộ 24 phương án qua cùng vòng ngoài để khảo sát, không dùng bảng này chọn mô hình tốt nhất rồi gọi đó là đánh giá không thiên lệch. Ngưỡng tham chiếu CMU chỉ là baseline có ý nghĩa triển khai với đúng Scaled Manhattan/31 chiều gốc; trên biến thể khác nó chỉ phục vụ quan sát.

Tổng cộng **297 genuine và 600 impostor** ở các vòng ngoài. Protocol hồ sơ cố định và tập impostor trong từng nhóm khác mô phỏng cập nhật hồ sơ trước đó (1.050 impostor đầu và 1.050 cuối), nên chỉ so sánh trực tiếp các quy trình mới với nhau. FAR/FRR cộng tử số và mẫu số; EER/AUC tính đường ROC đủ các mốc điểm trùng rồi lấy trung bình theo vòng. Không suy ra khoảng tin cậy bằng cách coi mọi lượt cùng người là độc lập.

## Kết quả và quyết định

| Quy trình trên cùng phép thử | FAR | FRR |
|---|---:|---:|
| Baseline 31 chiều gốc, giữ ngưỡng CMU | 187/600 = **31,17%** | 47/297 = **15,82%** |
| Baseline, hiệu chỉnh ngưỡng từ nhóm phát triển | 46/600 = **7,67%** | 193/297 = **64,98%** |
| Chọn phương án qua vòng trong, rồi hiệu chỉnh ngưỡng | 60/600 = **10,00%** | 190/297 = **63,97%** |

Các vòng trong chọn baseline ở vòng ngoài 1 và 3; vòng ngoài 2 chọn Manhattan trung vị/toàn bộ đặc trưng/chia tổng thời gian. Quy trình chọn phương án không cải thiện đồng thời hai loại lỗi. Hiệu chỉnh ngưỡng giảm nhận nhầm nhưng làm tăng mạnh số lượt chính chủ cần xác minh bổ sung; giới hạn FAR trên dev không bảo đảm FAR trên nhóm khác. **Chưa có cơ sở đổi cấu hình sản phẩm.**

Trên khảo sát Scaled Manhattan, bỏ bớt nhóm đặc trưng hoặc chuẩn hóa tốc độ không mặc nhiên cải thiện EER. Giữ toàn bộ số liệu không thuận lợi trong CSV/JSON; không chỉ chọn hình có kết quả tốt.

## 3. Trang khám phá offline

Mở `explorer/index.html` bằng Chrome/Edge. Không cần chạy server, không tải CDN hoặc gửi dữ liệu ra ngoài. Chọn detector, đặc trưng, chuẩn hóa và vòng ngoài; xem ngưỡng chọn trên dev, ngưỡng tham chiếu hoặc kéo thanh khảo sát. Trang hiển thị FAR/FRR kèm tử số/mẫu số, ROC dev/test, phân vùng mã, phương án vòng trong chọn và bảng 24 phương án có tải CSV.

Dữ liệu tổng hợp trong `explorer/research-data.js`, tái tạo từ cùng pipeline với `results/research_summary.json`. Thanh ngưỡng dùng tối đa 121 mốc điểm trải đều theo thứ tự cộng các ngưỡng đã chọn/tham chiếu; số đếm ở mốc hiển thị chính xác. Đường ROC hiển thị được rút gọn, còn EER/AUC tính trên đường đầy đủ. Thao tác ngưỡng không huấn luyện lại hoặc ghi cấu hình.

## Tái lập và kiểm chứng

```powershell
./.venv/Scripts/python.exe scripts/run_research.py
./.venv/Scripts/python.exe scripts/plot_research.py
./.venv/Scripts/python.exe -m unittest discover -s tests -p test_research.py -v
node scripts/check_explorer.mjs
```

Không cần cài thư viện mới cho bộ thí nghiệm: phần tính toán dùng NumPy và loader pandas hiện có. Detector sklearn và hàm ROC cũ nay import sklearn khi thực sự được gọi; Scaled Manhattan không phải nạp thư viện của những detector không dùng. Không vô hiệu hóa chính sách Application Control. SVM/Isolation Forest/Random Forest và suite có gọi sklearn vẫn phụ thuộc môi trường cho phép DLL.

Kiểm tra mới gồm các đáp án EER/AUC biết trước và điểm trùng, chuẩn hóa bất biến theo tốc độ, baseline khớp `build_profile/profile_z`, tách người impostor đúng nhóm và chọn phương án không đọc điểm ngoài. Chrome kiểm tra đủ 72 tổ hợp, hai đầu thanh ngưỡng, ngưỡng tham chiếu, điều hướng từ bảng, tải 24 dòng CSV và màn hình rộng 390 px không tràn ngang. Kết quả trình duyệt tại `results/research_browser_validation.json`.

Ưu tiên tiếp theo: xem trường hợp FAR cao/FRR cao theo từng vòng để thiết kế thí nghiệm mới; chỉ cân nhắc cấu hình khác sau khi có tiêu chí sử dụng và phép đánh giá phù hợp. Dữ liệu nhiều ngày và kiểm thử sử dụng của Thư vẫn theo phạm vi đã chốt riêng.

**Đã hoàn thành bước chẩn đoán tiếp theo trong ngày13/11:** xem [RESEARCH_ERROR_ANALYSIS.md](RESEARCH_ERROR_ANALYSIS.md). Trang khám phá mục04 có bảng theo mã/cặp và độ nhạy ngưỡng dev; bộ nghiên cứu gốc và config giữ nguyên. Khi tái tạo toàn bộ báo cáo, chạy thêm `scripts/analyze_research.py` và `scripts/plot_diagnostics.py` sau pipeline nghiên cứu trước khi build Word/PDF. Báo cáo đầy đủ hiện26 trang; mốc23 trang là bản trước khi thêm chẩn đoán.
