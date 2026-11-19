# Chẩn đoán lỗi nghiên cứu — 13/11/2026

Phân tích tiếp các trường hợp có FAR/FRR cao theo yêu cầu người dùng. **Không chọn ngưỡng mới**, không đổi phương án ở vòng trong, cấu hình sản phẩm, dữ liệu hoặc kết quả nghiên cứu trước. Không làm tiếp task Thư. Protocol gốc tại [RESEARCH_EXTENSION.md](RESEARCH_EXTENSION.md).

## Phạm vi và kiểm chứng

Chẩn đoán đủ 24 phương án × 3 vòng ngoài × 2 ngưỡng đã lưu (dev và tham chiếu CMU): **720 dòng tài khoản**, **2.880 dòng cặp có hướng**. Mỗi tài khoản có 40 lượt impostor = 4 mã khác cùng vòng × 10 lượt (5 đầu, 5 cuối). Có thêm **720 lượt bỏ từng mã dev** = 24 phương án × 3 vòng × 10 mã; chỉ tính lại ngưỡng trên phần dev còn lại, không chọn bằng lỗi test.

Mọi số đếm theo tài khoản và cặp được cộng lại, đối chiếu khớp cả 144 tổ hợp với JSON nghiên cứu đã lưu. Snapshot và config kiểm tra SHA-256; SHA của JSON gốc được lưu trong kết quả chẩn đoán, kiểm tra không bị thay đổi. Đây là mô tả trên dữ liệu đã phân tích, không phải bằng chứng tổng quát hóa mới.

## 1. Nhận nhầm tập trung ở vòng 1 và P10

Baseline hiệu chỉnh ngưỡng có kết quả:

| Vòng | Ngưỡng dev | Nhận nhầm | Genuine cần xác minh |
|---|---:|---:|---:|
| 1 | −0,403847 | 38/200 = 19,00% | 44/98 = 44,90% |
| 2 | −0,656054 | 5/200 = 2,50% | 64/100 = 64,00% |
| 3 | −0,665157 | 3/200 = 1,50% | 85/99 = 85,86% |

Vòng 1 chiếm **38/46 = 82,61%** lượt nhận nhầm của baseline hiệu chỉnh. Riêng P10 nhận **24/40** lượt impostor, tức **24/46 = 52,17%** tổng nhận nhầm; đồng thời 10/18 genuine cần xác minh. Mã P01 thử vào tài khoản P10 được nhận **9/10**; P04 và P08 thử vào P10 cùng **6/10**. Đây là cặp có hướng: không đổi vị trí tài khoản đích và người thử.

Ở P10, trung vị z impostor **−0,4693**, thấp hơn genuine **−0,2604**; điểm càng thấp càng dễ nhận. Phân bố chồng lấn và thứ tự trung vị này cho thấy chỉ dịch một ngưỡng chưa giải quyết được phân biệt. Trung vị thời gian cả câu genuine đánh giá bằng **1,94 lần** phần đăng ký, là dấu hiệu khác biệt trong bộ hiện có; không đủ cơ sở xác nhận nguyên nhân do thiết bị, người gõ hoặc drift nhiều ngày. Chưa sửa khóa trùng P10; hai dòng mơ hồ vẫn bị loại theo chính sách cũ.

## 2. FRR cao là vấn đề khác với FAR tập trung

| Tài khoản | Vòng | Nhận nhầm | Genuine cần xác minh |
|---|---:|---:|---:|
| P10 | 1 | 24/40 | 10/18 |
| P09 | 3 | 0/40 | **20/20** |
| P03 | 2 | 0/40 | **19/20** |
| P12 | 2 | 0/40 | **19/20** |

Ngưỡng vòng 2–3 nằm dưới trung vị điểm genuine của các mã FRR cao. P09 có trung vị genuine −0,2581 so với ngưỡng −0,6652, P03 có −0,2997 so với −0,6561, P12 có 0,4584 so với −0,6561. Ngưỡng chặt làm chính chủ thường xuyên cần bước bổ sung; FAR thấp không đồng nghĩa sử dụng thuận tiện.

Trong baseline raw/31 chiều, **0 chiều chạm sàn MAD 1e−9** ở cả 15 hồ sơ. Vì vậy chưa thấy cơ sở quy các lỗi đang xét cho sàn độ phân tán. Thống kê chuẩn hóa điểm từ 20 mẫu đăng ký vẫn có biến thiên giữa mã; đây là đối tượng nghiên cứu tiếp, chưa phải nguyên nhân được xác nhận.

## 3. Vì sao quy trình chọn phương án có thêm 14 nhận nhầm?

Vòng trong chọn baseline ở vòng ngoài 1 và 3, biến thể trung vị/31 chiều/chia tổng thời gian ở vòng ngoài 2. Trong vòng 2:

- P15 tăng từ **4/40 lên 16/40** nhận nhầm, thêm 12.
- P06 tăng từ **0/40 lên 2/40**, thêm 2.
- Các tài khoản còn lại giữ số nhận nhầm. Tổng tăng 14, khớp **60 − 46** của hai quy trình.

Đây là bằng chứng giới hạn của lựa chọn từ nhóm phát triển nhỏ. Detector, chuẩn hóa và ngưỡng cùng thay đổi; không quy kết riêng việc chia tổng thời gian là nguyên nhân. Không đổi sang phương án có số outer-test đẹp hơn sau khi đã xem bảng này.

## 4. Ngưỡng nhạy với thành phần nhóm dev

Với baseline, bỏ từng mã dev khỏi **cả vai trò tài khoản và impostor** cho:

| Vòng | Khoảng ngưỡng khi bỏ từng mã | Mã bị bỏ ở đầu thấp / cao |
|---|---:|---|
| 1 | −0,465052 đến −0,297875 | P09 / P15 |
| 2 | −0,685029 đến −0,458836 | P05 / P10 |
| 3 | −0,701655 đến −0,498471 | P03 / P10 |

Mỗi phép thử còn 9 mã và 720 lượt impostor trong dev. Chỉ mô tả độ nhạy theo thành phần nhóm, **không phải khoảng tin cậy**, không sử dụng điểm test để chọn ngưỡng và không chọn một đầu khoảng để triển khai. Vai trò P10 trong phép thử dev vòng 2–3 khác vai trò test vòng 1.

## Đặc trưng và giới hạn diễn giải

Tỷ trọng đặc trưng là thành phần trung bình của khoảng cách `|x − tâm| / độ phân tán`, chia tổng khoảng cách. Nó không phải tỷ trọng z (z có trừ μ), xác suất danh tính hoặc chứng cứ nhân quả. Top 5 ở genuine bị từ chối được hiển thị theo tài khoản; ví dụ P03 có H.n khoảng 12,50% khoảng cách ở các ca này. Không có một đặc trưng đơn lẻ giải thích toàn bộ lỗi.

Với impostor được nhận, thành phần khoảng cách lớn nhất chỉ mô tả phần khoảng cách còn lại; không được nói rằng thành phần đó làm nhận nhầm. Khả năng nhận nhầm liên quan tổng điểm vẫn thấp hơn ngưỡng.

## Công cụ và tái lập

```powershell
./.venv/Scripts/python.exe scripts/analyze_research.py
./.venv/Scripts/python.exe scripts/plot_diagnostics.py
./.venv/Scripts/python.exe -m pytest tests/test_diagnostics.py tests/test_research.py tests/test_model.py tests/test_collected.py tests/test_live_evidence.py tests/test_features.py tests/test_simulation.py -q
node scripts/check_explorer.mjs
```

- `results/research_diagnostics.json`: chi tiết theo biến thể/vòng/ngưỡng và tổng hợp ba quy trình.
- `results/research_account_errors.csv`, `research_pair_errors.csv`, `research_threshold_jackknife.csv`: các bảng đối chiếu đầy đủ.
- `explorer/index.html`, mục 04: chọn tài khoản/ngưỡng chẩn đoán; xem bảng FAR/FRR, cặp có hướng, điểm, thời gian và thành phần khoảng cách. Chẩn đoán hai ngưỡng cố định độc lập với thanh khảo sát thủ công ở mục 02.
- `figures/research/account_error_heatmap.png`: bản đồ lỗi của cả 15 mã trên ba quy trình.

Kiểm thử: **28 test đạt, 4 subtest** trong tập kiểm tra liên quan, gồm 5 test chẩn đoán mới. Chrome đối chiếu 144 tổ hợp chẩn đoán, 72 tổ hợp thí nghiệm, chọn tài khoản P09/P10, tổng cặp khớp tổng tài khoản, ngưỡng thủ công không đổi nhãn chẩn đoán, CSV và mobile. Chưa chạy lại benchmark hoặc các mô hình sklearn.

**Quyết định:** giữ ngưỡng sản phẩm. Ưu tiên tiếp theo là thiết kế kiểm tra chất lượng mẫu đăng ký và chuẩn hóa điểm ổn định, chỉ dùng enrollment/dev để xây quy tắc. Mọi quy tắc mới phải được đánh giá lại theo protocol khám phá phù hợp; không dùng P10/P09 trong bảng này để gán thủ công ngưỡng riêng rồi tuyên bố đã cải thiện tổng quát hóa.
