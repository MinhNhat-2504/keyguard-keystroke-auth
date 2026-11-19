# Kết quả bổ sung độ bất định theo tài khoản

Phân tích hồi cứu, khoảng percentile danh nghĩa 95%, có điều kiện trên cấu hình và dữ liệu đã cố định. Xem [kế hoạch và giới hạn](ACCOUNT_UNCERTAINTY_PLAN_20261115.md). Không phải kiểm chứng độc lập hay bảo đảm bao phủ quần thể.

| So sánh candidate–control | Số tài khoản | ΔFAR [khoảng] (đpt) | ΔFRR [khoảng] (đpt) |
|---|---:|---:|---:|
| CMU shrink25 | 15 | +0.095 [-0.476; +0.810] | +0.800 [-2.533; +3.467] |
| KeyRecs shrink25 | 33 | +0.038 [-0.568; +0.654] | -1.091 [-3.719; +0.993] |
| GREYC shrink25 | 21 | +0.095 [-0.405; +0.738] | +0.277 [-0.972; +1.523] |
| GREYC DEV percentile | 14 | +0.989 [-0.549; +3.132] | -1.489 [-6.396; +2.708] |
| GREYC DEV covariance | 14 | +0.824 [+0.165; +1.593] | -0.409 [-4.859; +6.553] |

Dấu âm nghĩa là tỷ lệ lỗi giảm. Các khoảng không phải kiểm định đồng thời; không dùng việc có/không chứa 0 để tuyên bố thắng, tương đương hoặc vô hại. Chưa mô hình hóa phụ thuộc chéo do dùng chung impostor, thay đổi calibration, enrollment hoặc nguồn mới.

Giữ quyết định gốc: các candidate không đạt tiêu chí định trước; covariance không đi giai đoạn B. Không chỉnh lại ngưỡng, hệ số hoặc đối chứng theo bảng này.

Kết quả đầy đủ của từng nhánh và hiệu: results/account_uncertainty_20261115.json/.csv. Kiểm 30 chỉ số bằng SciPy paired bootstrap đạt trong results/account_uncertainty_checks_20261115.json.

Tái lập: python scripts/account_uncertainty.py rồi python scripts/validate_account_uncertainty.py (cần NumPy/SciPy của môi trường nghiên cứu). Không cần raw hoặc cloud.
