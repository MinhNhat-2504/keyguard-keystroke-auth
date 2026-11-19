# Phân tích bổ sung độ bất định theo tài khoản

Đây là kế hoạch phân tích hồi cứu trên kết quả đã xem, không phải đăng ký trước thí nghiệm. Không chọn lại mô hình, ngưỡng, nguồn hoặc tiêu chí thắng theo khoảng thu được.

- Phạm vi cố định: shrink25–baseline trên CMU, KeyRecs và GREYC; OOF percentile–baseline trên GREYC DEV; full LW–diagonal LW trên GREYC DEV. Manhattan trong thí nghiệm covariance chỉ là tham chiếu, không đổi thành đối chứng chính.
- Đơn vị: tài khoản đích; cùng tập tài khoản và cùng số lượt giữa hai nhánh. Tính FAR/FRR riêng từng tài khoản rồi trung bình không trọng số (macro). Không bootstrap độc lập từng lần gõ.
- Lấy mẫu lại 20.000 lần có hoàn lại, cùng chỉ số tài khoản cho cả hai nhánh và hai chỉ số; seed PCG64 = 20261115. Khoảng percentile 2,5–97,5%, dùng nội suy tuyến tính, đơn vị điểm phần trăm. Ghi cả điểm ước lượng, khoảng của từng nhánh và của hiệu candidate–control.
- Đây là khoảng bootstrap mô tả có điều kiện trên enrollment, calibration, ngưỡng và tập impostor đã cố định. Tài khoản có thể dùng chung người giả mạo; lấy mẫu tài khoản đích không mô hình hóa đầy đủ phụ thuộc chéo đó. Không gọi đây là khoảng bảo đảm bao phủ 95% cho người dùng mới, không thực hiện kiểm định ý nghĩa, không dùng khoảng cắt/không cắt 0 để đảo quyết định cổng cũ. Không có hiệu chỉnh đa so sánh; chỉ mô tả 5 phép so sánh đã nêu.
- Không suy ra nhiều ngày hay danh tính độc lập cho dữ liệu tự thu. Không thêm nguồn tự thu vào bootstrap này vì thiếu thiết kế xác minh danh tính/phiên phù hợp.

Thuật toán percentile và ý nghĩa `paired=True` tham chiếu [tài liệu chính thức SciPy bootstrap](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.bootstrap.html). Runner dùng NumPy; test so sánh độc lập với SciPy trên dữ liệu giả có cùng RNG.
