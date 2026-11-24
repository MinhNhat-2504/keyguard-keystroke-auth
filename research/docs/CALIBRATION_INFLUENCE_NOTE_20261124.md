# Vì sao một điểm CV lớn có thể làm ngưỡng dễ nhận hơn

Đây là phép diễn giải đại số cho mean/SD, không phải thuật toán mới hoặc kết quả trên một bộ dữ liệu khác. Dùng một ví dụ nhân tạo gồm n−1 điểm OOF bằng 0 và một điểm M > 0. Những số 0 chỉ đơn giản hóa phép tính, không thay hoặc mô tả chính xác các điểm USN. SD là độ lệch chuẩn quần thể (ddof=0), đúng quy ước code hiện tại.

Trung bình là μ = M/n. Tổng bình phương sai lệch là M²(n−1)/n, nên phương sai quần thể bằng M²(n−1)/n² và σ = M√(n−1)/n. Khi σ lớn hơn sàn 1e-6, ngưỡng điểm thô tương đương với z <= τ là q = μ + τσ = M(1+τ√(n−1))/n. Nếu σ chạm sàn, phải dùng max(σ, 1e-6); biểu thức q theo M ở trên không còn áp dụng nguyên dạng.

Giữ n cố định và điểm đánh giá thô s hữu hạn, không tăng theo M. Khi M tăng vô hạn, (s−μ)/σ tiến đến −1/√(n−1). Với n=20, giới hạn khoảng −0,2294, nằm dưới ngưỡng dương 0,2720. Vì vậy trong điều kiện ví dụ này, làm một điểm OOF tăng cực lớn có thể khiến mọi điểm thô cố định cuối cùng nằm dưới ngưỡng z. Đây là ảnh hưởng của phép chuẩn hóa, không phải bằng chứng detector phân biệt người gõ tốt hơn.

Với n=20, M=1.000.000 và ngưỡng đã lưu, ngưỡng thô trong ví dụ khoảng 109 nghìn. Ba hồ sơ USN thực có các điểm OOF còn lại khác 0, nên không đồng nhất ví dụ với dữ liệu thật. Chẩn đoán thực nghiệm đã tái lập CV riêng và cho giới hạn thô khoảng 109.323–109.335. Điểm thô của mô hình học đủ mẫu cũng có thể thay đổi; giới hạn trên chỉ áp dụng khi s được giữ hữu hạn độc lập với M. Không dùng nó để khẳng định mọi ngoại lệ CV hoặc mọi hồ sơ đều sẽ nhận nhầm.

Phép tính được kiểm bằng `statistics.mean`/`statistics.pstdev`, gồm trường hợp sàn SD và giới hạn của điểm thô cố định. Mã `keyguard/calibration_influence.py`, kiểm thử `tests/test_calibration_influence.py`, artifact `results/calibration_influence_20261124.json`. Không sửa score, ngưỡng, detector, quy tắc cảnh báo, kết quả USN hoặc luồng web. Hướng xử lý cụ thể vẫn cần đối chứng và nguồn chưa xem; không rút một cách sửa đã có hiệu quả từ ví dụ này.
