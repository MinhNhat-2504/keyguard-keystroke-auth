# Kiểm chứng ngoài: lợi/hại theo tài khoản — 15/11/2026

## Chốt trước khi chấm nguồn mới

So sánh duy nhất Scaled Manhattan baseline với shrink25 đã có. Giữ λ=0,25, tâm mean, local MAD = mean absolute deviation, prior median MAD trong DEV, CV 5 fold/20 enrollment, chuẩn hóa mean/population SD và quy tắc chọn ngưỡng FAR DEV ≤5%. Không dò hệ số, detector, đặc trưng hoặc ngưỡng theo kết quả nguồn mới. Đây là khóa nội bộ, không phải đăng ký trước công khai.

**Tiêu chí toàn tập giữ nguyên:** ΔFRR macro <0 và ΔFAR macro ≤0, candidate−baseline, tính từ phân số chưa làm tròn. Hai nguồn cũ không được gọi là nguồn ngoài mới và không dùng để chốt lại phương pháp.

**Tuyên bố lợi ích rộng được xét riêng, định trước:** chỉ được ghi “cải thiện cho đa số tài khoản trong tập kiểm chứng” khi đồng thời đạt tiêu chí toàn tập và số tài khoản có ΔFRR<0, ΔFAR≤0 lớn hơn N/2. Không tính tài khoản hòa vào nhóm được lợi. Không đạt điều kiện này thì chỉ mô tả kết quả, kể cả trung bình thuận lợi. Đây là điều kiện của tuyên bố cụ thể, không thay tiêu chí toàn tập cũ.

## Đầu ra bắt buộc

- Đủ số đếm genuine/impostor và mẫu số theo từng đích ở cả hai nhánh; đối chiếu cùng probe, không cập nhật profile trong test.
- Macro và pooled ghi riêng; hiệu số theo từng mã, bảng 3×3 dấu ΔFAR/ΔFRR (âm, bằng 0, dương), số được lợi theo định nghĩa trên, số gặp ít nhất một lỗi tăng.
- Median, min/max và các quantile 25/75% của hiệu số theo quy tắc nearest-rank (ceil(p*N), không nội suy), chỉ mô tả các tài khoản đã quan sát.
- Bảng đầy đủ mọi mã, không chỉ top thuận lợi; phép bỏ một tài khoản đích là phân tích độ nhạy phụ, không lựa chọn tập con để đạt tiêu chí. Không gọi phép bỏ hàng đích là LOSO toàn danh tính.
- Không bootstrap từng lượt như độc lập; không CI/p-value hoặc suy luận nhân quả trong phiên bản này. Tài khoản đích và impostor có thể dùng chung danh tính.

## Chọn nguồn và audit trước scoring

Ưu tiên GREYC-KeyStroke 2009, bản SQLite trên trang của tác giả Romain Giot: https://www.labri.fr/perso/rgiot/resources/greycdb/ ; tải được liên kết tại https://www.labri.fr/perso/rgiot/pub/keystroke.db . Trang nêu chỉ dùng nghiên cứu học thuật, yêu cầu trích Giot, El-Abed, Rosenberger, BTAS 2009. Không công bố lại raw hay dùng cho hệ thống thương mại trong task này. Đây là nguồn mới đối với dự án, không bảo đảm không có người trùng giữa các nghiên cứu.

Buffalo/CITeR cần quy trình cấp dữ liệu theo release agreement; không tự gửi email hay nhận thỏa thuận thay người dùng. Bộ longitudinal sparkins01 có mô tả hỗ trợ tái lập bài đi kèm, chưa xác nhận phạm vi dùng cho nghiên cứu khác; không ưu tiên khi đã có nguồn cho phép nghiên cứu học thuật rõ hơn. Không tải bản mirror đã lọc mà không biết quy tắc.

Audit SQLite chỉ đọc schema, số lượng, tính đầy đủ, các mốc thời gian/phiên và định dạng timing, không tính điểm detector. Bổ sung adapter và quy tắc phiên sau audit **trước** mọi scoring. Không giả chia một phiên thành hai ngày. GREYC thu nhiều bàn phím, số mẫu một phiên có thể chưa đủ20; nếu phải gom enrollment qua các phiên thật thì nêu đây là protocol chuyển nguồn, không gọi là lặp nguyên điều kiện S1 của CMU/KeyRecs.

Quy tắc khả dụng định trước: mỗi tài khoản dùng20 enrollment theo thời gian; test phải ở các phiên/ngày thật muộn hơn điểm kết thúc enrollment và có ít nhất10 mẫu hợp lệ. Nếu schema không xác nhận được thứ tự/phiên, dừng và ghi chưa đủ điều kiện; không dùng thứ tự dòng SQLite thay cho thời gian. Không loại tài khoản theo kết quả mô hình. Cùng câu gõ và thứ tự đặc trưng cho tất cả tài khoản; không trộn thiết bị mà giấu điều kiện. Chốt lựa chọn thiết bị, session boundary và feature từ schema/metadata trước điểm số.

Sau eligibility: sắp ID nguồn theo số nếu là số, chia từng nhóm3: hai DEV, một TEST, không thử seed khác. Cần tối thiểu10 DEV và5 TEST; nếu thiếu thì ghi không đủ theo thiết kế, không hạ mức sau khi xem điểm. Prior/threshold chỉ fit DEV; test enrollment chỉ fit profile của chính tài khoản. Probe impostor DEV và TEST lấy tối đa first5+last5 không chồng lặp của mỗi mã khác trong phần tương ứng.

## Thứ tự và bảo toàn

Lưu SHA/timestamp protocol → tải và hash raw/điều kiện sử dụng → audit metadata chỉ đọc → khóa adapter/split/features/protocol cụ thể → kiểm dữ liệu giả → freeze code/dependencies/inputs → chạy một lần → đối chiếu kết quả và phân bố tài khoản. Không scoring trước freeze, không chọn nguồn theo tỷ lệ lỗi.

Giữ nguyên báo cáo6/37/40 trang, mô hình sản phẩm, dữ liệu cũ và gói bàn giao v2. Không làm task B2 thay Thư, không đổi điểm hoặc triển khai dịch vụ trong lượt này. Nếu không có nguồn đạt điều kiện thì vẫn bàn giao protocol/checker đã kiểm thử và báo rõ kiểm chứng chưa chạy.
