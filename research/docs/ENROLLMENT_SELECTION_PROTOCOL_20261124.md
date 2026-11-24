# Đối chứng chọn mẫu đăng ký với ngân sách cố định

Ngày lập 24/11/2026. Đây là hướng phát triển tiếp trên dữ liệu đã xem. Kế hoạch này được lưu trước lần chạy phương án chọn mẫu mới; không phải đăng ký công khai từ đầu dự án.

## Câu hỏi và giả thuyết

Một hồ sơ lấy các lượt đầu có thể chưa thể hiện đủ biến thiên ngay trong phần đăng ký. Nhóm kiểm tra liệu việc giữ những mẫu phủ được nhiều vùng của tập đăng ký có giảm từ chối chính chủ mà không tăng nhận nhầm hay không. Quy tắc chọn mẫu có thể giữ cả mẫu ở rìa và làm tăng nhận nhầm; kết quả đó cũng phải được công bố.

Mỗi tài khoản cung cấp đúng 20 mẫu ứng viên theo thứ tự thời gian. Mỗi nhánh chỉ giữ 10 mẫu để học detector, cùng dùng 20 mẫu cho quy trình kiểm định chéo. Hai mốc là 10 mẫu đầu và 10 mẫu cuối; nhánh mới chọn 10 mẫu đại diện. Mốc cuối giúp kiểm tra lợi ích có đơn giản đến từ mẫu gần thời điểm đánh giá hơn không. Việc lưu 10 từ 20 là một đối chứng nghiên cứu; không sửa yêu cầu 20 mẫu hay cấu hình của ứng dụng hiện tại.

## Quy tắc duy nhất được thử

Trên ma trận ứng viên của chính tài khoản, tính trung vị và MAD trung vị từng chiều, nhân MAD với 1,4826 và chặn dưới ở 10⁻⁹. Khoảng cách chọn mẫu là trung bình độ lệch tuyệt đối đã chia scale theo chiều. Mẫu đầu tiên có tổng khoảng cách đến các mẫu còn lại nhỏ nhất; sau đó lần lượt thêm mẫu có khoảng cách đến mẫu đã chọn gần nhất lớn nhất, cho tới đủ 10. Nếu hòa, dùng vị trí thời gian xuất hiện trước. Sắp các mẫu đã chọn theo thứ tự gốc trước khi học.

Đây là ứng dụng một cách chọn tham lam theo ý tưởng farthest-first/k-center, không phải thuật toán mới của nhóm. Nguồn nền: T. F. Gonzalez, “Clustering to minimize the maximum intercluster distance,” Theoretical Computer Science 38, 293–306, 1985, DOI 10.1016/0304-3975(85)90224-5. Mục tiêu phủ khoảng cách không bảo đảm tối ưu FAR/FRR.

Giữ Scaled Manhattan, trung bình/MAD trung bình và sàn detector 10⁻⁹ như hiện tại. Chuẩn hóa điểm bằng trung bình/độ lệch chuẩn OOF, sàn 10⁻⁶. Chia 20 mẫu thành 5 phần liên tiếp. Trong mỗi lần CV, mọi thống kê chọn mẫu và việc chọn 10 mẫu đều được tính lại chỉ trên 16 mẫu phần học; 4 mẫu giữ ra chỉ được chấm. Không chọn tập 10 trên toàn bộ 20 rồi mang nguyên tập đó vào CV. Mô hình cuối học 10 mẫu chọn từ toàn bộ 20.

## Dữ liệu và so sánh cùng điều kiện

Chỉ dùng danh sách DEV hiện có của CMU (36 mã) và KeyRecs (66 mã), lấy từ kế hoạch matched_adaptation đã lưu. Giữ nguyên raw và bộ đọc đã kiểm tra. Mỗi người có pool là 20 mẫu đầu phiên 1, lượt chính chủ đánh giá là toàn bộ phiên 2; không cập nhật hồ sơ. Các TEST cũ không được chấm trong phép thử này.

Trong từng DEV, xếp mã theo SHA-256 của chuỗi `20261124:` cộng mã người; hai phần ba đầu là tập hiệu chỉnh, phần còn lại là tập đối chứng. CMU có 24/12 mã và KeyRecs có 44/22 mã. Đây là phân chia mới bên trong DEV đã xem, không được gọi là dữ liệu mới độc lập.

Mỗi nhánh chọn một ngưỡng riêng từ các lượt giả mạo phiên 2 của tập hiệu chỉnh với FAR thực nghiệm không quá 5%, giữ nguyên nhóm điểm bằng nhau. Việc dùng phiên 2 của những mã hiệu chỉnh là học ngưỡng từ dữ liệu phát triển; không dùng phiên 2 của mã đối chứng để chọn ngưỡng hoặc quy tắc. Cùng một tập hiệu chỉnh cho cả ba nhánh. Lịch này khác các bảng CMU/KeyRecs cũ nên không so tỷ lệ lỗi trực tiếp với chúng.

Trong mỗi phân vùng, lượt giả mạo của một tài khoản đích là 5 mẫu đầu và 5 mẫu cuối phiên 2 của từng mã khác trong chính phân vùng đó. Mỗi mã phải có ít nhất 10 mẫu phiên 2 để hai phần không trùng. Không dùng người từ tập đối chứng làm lượt giả mạo hiệu chỉnh. Các nhánh có cùng tài khoản, cùng lượt chính chủ/giả mạo, cùng số mẫu thu và cùng số mẫu giữ.

## Tiêu chí và thứ tự mở bước tiếp

So riêng cover10 với first10 và last10, không chọn mốc thuận lợi sau khi thấy kết quả. Trên từng nguồn, tiêu chí chính là FRR trung bình theo tài khoản giảm và FAR trung bình theo tài khoản không tăng. Lợi ích đa số là hơn một nửa số tài khoản có FRR giảm và FAR không tăng. Các quyết định dùng phân số chính xác từ số đếm để tránh lỗi so sánh float.

Chỉ mở bước kiểm chứng dữ liệu chưa dùng khi cả hai so sánh với hai mốc đều đạt tiêu chí chính và lợi ích đa số trên cả hai nguồn DEV. Nếu không đạt, dừng nhánh chọn mẫu này; không thay k, số mẫu ứng viên, chuẩn hóa hay nới tiêu chí rồi chạy lại. Giữ nguyên cấu hình sản phẩm và dữ liệu kiểm chứng chưa mở. Việc dừng là kết quả của đối chứng DEV, không chứng minh phương pháp vô tác dụng ở mọi điều kiện.

Nguồn nhiều tuần được khảo sát ở bước tìm dữ liệu là repository `sparkins01/keystroke`, commit 446aca544357eeba33200f4b749342f29f7b779c ngày 06/11/2026. Mới đọc README, danh mục và metadata chuỗi, chưa tải timing hoặc chấm mô hình. README mô tả 85 người, trong khi bài IET Biometrics 2023 DOI 10.1049/bme2.12087 mô tả 65; bài cũ không dẫn repository này và bản phát hành chưa có giấy phép dữ liệu cụ thể ngoài phần permitted use. Vì chưa khép được quan hệ phiên bản/xuất xứ và điều kiện dùng cho phép so sánh mới, nguồn này chỉ là ứng viên, chưa được chấp nhận làm kiểm chứng. Nếu qua cổng DEV, phải giải quyết các điểm đó và khóa adapter/tiêu chí nguồn trước khi chạy nguồn mới; không tự nhận đã có kiểm chứng độc lập.

## Báo cáo và bảo toàn kết quả

Lưu FAR/FRR gộp, FAR/FRR trung bình theo tài khoản, ngưỡng, số lượt nhận nhầm/từ chối, vị trí mẫu được chọn và bán kính phủ. Bán kính phủ nhỏ hơn chỉ mô tả mục tiêu hình học, không thay tiêu chí nhận dạng. Báo cả số tài khoản có lợi, có hại hoặc không đổi. Hại là FAR hoặc FRR tăng; lợi là FRR giảm mà FAR không tăng.

Khoảng mô tả chênh lệch dùng bootstrap cặp theo tài khoản, 10.000 lần, seed 20261124, phân vị 2,5–97,5. Phụ thuộc do các tài khoản dùng chung người giả mạo chưa được mô hình hóa nên không gọi đây là kiểm định ưu thế hay bảo đảm cho người mới. Khoảng không được dùng để thay cổng quyết định.

Runner phải kiểm thử bằng dữ liệu giả, khóa hash protocol/code/raw/split/môi trường trước `--run`, từ chối ghi đè và kiểm hash lại sau chạy. Giữ nguyên báo cáo, cấu hình và kết quả lịch sử. Không công khai raw riêng tư hoặc thông tin kết nối dịch vụ.
