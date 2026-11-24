# Kết quả đối chứng chọn mẫu đăng ký

Đã chạy một lần sau khi khóa protocol, runner và dữ liệu. 13 ca kiểm thử dữ liệu giả đạt trước khóa; bộ đối chiếu độc lập đạt 1.034 kiểm tra sau chạy. Các tệp báo cáo, cấu hình và kết quả lịch sử trong khóa giữ nguyên hash.

Mỗi nhánh có cùng 20 lượt đăng ký ứng viên và học hồ sơ từ 10 lượt; dùng cùng Scaled Manhattan, CV và cách chọn ngưỡng. Tập hiệu chỉnh/đối chứng là 24/12 mã trong DEV CMU và 44/22 mã trong DEV KeyRecs. Lượt chính chủ và giả mạo lấy ở phiên 2; không cập nhật hồ sơ. Các TEST cũ không được chấm. Đây là đối chứng mới trên DEV đã xem, không phải kiểm chứng dữ liệu độc lập.

| Nguồn DEV | Cách giữ mẫu | FAR trung bình (%) | FRR trung bình (%) | Nhận nhầm | Chính chủ bị từ chối |
|---|---|---:|---:|---:|---:|
| CMU | 10 lượt đầu | 0,53 | 79,83 | 7/1.320 | 479/600 |
| CMU | 10 lượt cuối | 0,98 | 51,50 | 13/1.320 | 309/600 |
| CMU | Đại diện 10/20 | 0,91 | 78,83 | 12/1.320 | 473/600 |
| KeyRecs | 10 lượt đầu | 7,38 | 79,09 | 341/4.620 | 1.739/2.197 |
| KeyRecs | 10 lượt cuối | 5,45 | 58,51 | 252/4.620 | 1.286/2.197 |
| KeyRecs | Đại diện 10/20 | 8,18 | 78,37 | 378/4.620 | 1.723/2.197 |

Tỷ lệ chính lấy trung bình theo tài khoản, số đếm gộp theo lượt. KeyRecs có số lượt chính chủ không bằng nhau nên FRR trung bình và tỷ lệ tính từ tổng số đếm khác nhau. Không so mức lỗi này với các bảng cũ do khác số mẫu hồ sơ, phân vùng và lịch hiệu chỉnh.

| So sánh đại diện trừ mốc | ΔFAR (điểm %) | ΔFRR (điểm %) | Tài khoản có lợi | Tài khoản có hại |
|---|---:|---:|---:|---:|
| CMU, mốc đầu | +0,379 | −1,000 | 4/12 | 6/12 |
| CMU, mốc cuối | −0,076 | +27,333 | 1/12 | 11/12 |
| KeyRecs, mốc đầu | +0,801 | −0,728 | 4/22 | 15/22 |
| KeyRecs, mốc cuối | +2,727 | +19,854 | 1/22 | 21/22 |

Lợi là FRR giảm và FAR không tăng; hại là FAR hoặc FRR tăng. Cả bốn so sánh đều không đạt tiêu chí chính; cũng không có lợi cho đa số tài khoản. Bán kính phủ hình học giảm trên hai nguồn nhưng không chuyển thành lợi ích nhận dạng theo tiêu chí, cho thấy mục tiêu phủ tập ứng viên không thay được mục tiêu xác thực. Kết quả không đủ để khẳng định nguyên nhân là luyện quen, thiết bị hay riêng một đặc trưng.

Khoảng mô tả bootstrap cặp theo tài khoản được lưu trong JSON. Ví dụ CMU so mốc cuối có ΔFRR +27,333 điểm %, khoảng +17,667 đến +36,833. KeyRecs so mốc cuối có ΔFRR +19,854 điểm %, khoảng +10,258 đến +30,045. Đây là mô tả có điều kiện, chưa mô hình hóa việc dùng chung người giả mạo và không phải khẳng định ưu thế quần thể.

Theo cổng tiếp tục đã khóa, không mở kiểm chứng nguồn mới và không sửa quy tắc để chạy lại. Nguồn nhiều tuần chỉ mới được rà metadata công khai, còn vấn đề xuất xứ phiên bản/điều kiện dùng; không có timing của nguồn đó được tải hoặc chấm. Không có kết quả kiểm chứng độc lập mới để báo cáo. Cấu hình sản phẩm vẫn giữ 20 mẫu đăng ký và detector/ngưỡng cũ.

Mã: `keyguard/enrollment_selection.py`, runner `scripts/run_enrollment_selection_20261124.py`, kiểm thử `tests/test_enrollment_selection.py`. Hồ sơ: `results/enrollment_selection_20261124_plan.json`, `_freeze.json`, `_synthetic_tests.json`, `_started.json`, `_results.json`, `_accounts.csv`, `_audit.json`. Bộ audit không import model để tính lại chỉ số; nó đối chiếu số đếm, phân vùng và dữ liệu phiên 2.
