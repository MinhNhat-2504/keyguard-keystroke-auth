# Kiểm tra quy tắc cố định trên dữ liệu USN

Kế hoạch được ghi sau audit cấu trúc, trước lần chấm mô hình trên USN. Đây là đánh giá bổ sung một quy tắc đã có, không tiếp tục nhánh cover10 đã trượt cổng DEV. Không dùng nguồn mới để sửa nhánh đó.

## Nguồn và câu hỏi

Nguồn là USN Research Data Archive, phiên bản 1, DOI 10.23642/usn.23790858.v1, tác giả Halvor Nybø Risto và Olaf Hallan Graven, phát hành 12/09/2023, giấy phép CC BY 4.0. Bài “Fixed-text keystroke dynamics authentication data set—collection and analysis,” Annals of Telecommunications 79, 731–743 (2024), DOI 10.1007/s12243-024-01039-z dẫn trực tiếp DOI bộ dữ liệu. Đã tải 37 tệp từ kho chính thức, đối chiếu toàn bộ MD5 công bố; SHA-256/URL/kích thước lưu trong `results/usn_source_manifest_20261124.json`. Raw giữ local, không cần đưa vào snapshot công khai.

Câu hỏi hẹp là quy tắc Scaled Manhattan, chuẩn hóa CV và ngưỡng CMU đã chọn cho mức lỗi thế nào trên nguồn thu có sáu câu gõ khác nhau, cùng thiết bị và có lượt thử giả mạo riêng. Không thử thuật toán mới, không chọn ngưỡng USN và không xếp hạng tối ưu theo nguồn. Không coi kết quả thấp ở một câu là chứng minh ưu thế chung.

## Audit trước chấm

README mô tả 5 người chính chủ, mỗi người gõ mỗi câu 200 lần, cùng máy và bàn phím PS/2 với nhóm giả mạo. Mỗi câu của chính chủ được thu trong một phiên. Tệp chính chủ không có ngày/phiên/timestamp hoặc số lượt gốc, do đó chỉ gọi là chia theo thứ tự dòng tệp, không xác nhận thứ tự thời gian hoặc kiểm chứng nhiều ngày. Các mã số trong attack không được đồng nhất với số người chính chủ trong tên tệp.

Tệp có 25, 34, 49, 58, 73 hoặc 97 cột thời gian tùy câu gõ; giữ cả Shift như schema nguồn. Metadata `subject`, `rep` của tệp attack bị tách khỏi vector. Đơn vị giây; không đổi tên/ép vector về 31 chiều CMU, không tuyên bố đang chuyển nguyên hồ sơ CMU sang câu khác. Audit quan hệ DD = H + UD phù hợp sai số số thực; không có hold âm trong dữ liệu giữ lại.

Trong 8.069 dòng, giữ 8.042 dòng: 6.000 chính chủ và 2.042 attack. Loại 9 dòng timing rỗng và toàn bộ 18 dòng có khóa subject–rep trùng mơ hồ trong tệp attack câu có tên `Gigab-exclm-t R3ceiver`. Không điền dữ liệu thiếu, không sửa khóa và không cắt bỏ timing hữu hạn lớn. Danh sách dòng/reason lưu audit. Không chấm trước khi khóa.

## Quy tắc cố định

Mỗi tài khoản–câu gõ tạo hồ sơ từ 20 dòng đầu của tệp chính chủ; 180 dòng còn lại chỉ dùng đánh giá. Giữ Scaled Manhattan như code dự án: mean/MAD trung bình, sàn 10⁻⁹; OOF 5 phần trên đúng 20 dòng đăng ký; trung bình/SD population, sàn 10⁻⁶. Mô hình cuối học đủ 20 dòng. Không cập nhật hồ sơ từ chính chủ hoặc attack khi chấm, vì không có bằng chứng xác minh/tiến trình thời gian để mô phỏng thích nghi hợp lệ.

Giữ đúng ngưỡng z = 0,2720094565367825 trong cấu hình CMU hiện có. Chấp nhận khi z≤ngưỡng, không tách điểm trùng. Không dùng attack để chọn ngưỡng, không phân DEV/TEST USN để fit tham số. Vì có câu gõ/số chiều khác nhau, đây là phép chuyển quy tắc tính điểm và ngưỡng chuẩn hóa sang hồ sơ học tại USN, không chuyển trực tiếp vector/hồ sơ CMU. Mức FAR 5% từng dùng ở DEV CMU không là bảo đảm USN.

Mỗi hồ sơ dùng toàn bộ attack hợp lệ của cùng câu làm lượt giả mạo. Tệp attack được dùng lại để chấm 5 hồ sơ chính chủ; phải phân biệt 2.042 dòng attack gốc với 10.210 quyết định hồ sơ–attack. Tương tự có 30 hồ sơ nhưng chỉ 5 người chính chủ, không phải 30 người độc lập. Lượt chính chủ đánh giá là 5.400, 600 dòng đăng ký loại khỏi mẫu số.

## Đầu ra và diễn giải

Lưu score z/accept theo dòng cho cả genuine và attack; không lưu vector raw vào kết quả công khai. Lưu bảng theo từng hồ sơ và từng câu: số lỗi/mẫu số, FAR/FRR gộp, FAR/FRR trung bình theo tài khoản và số hồ sơ FAR vượt mức tham chiếu 5%. Mức tham chiếu chỉ là đối chiếu với ngân sách cũ, không phải một tiêu chí mới để tuyên bố triển khai an toàn. Không suy ra nguyên nhân độ dài/cấu trúc mật khẩu từ các tỷ lệ quan sát vì ít người và các yếu tố chưa được tách.

Không áp dụng bootstrap theo 30 hồ sơ để giả định độc lập, không diễn giải các lượt attack dùng lại là người mới độc lập. Độ ổn định nhiều ngày, OTP, tấn công bắt chước chủ động và an toàn sản phẩm không được kiểm chứng. USN là nguồn chưa dùng chấm mô hình trong dự án trước lượt này; kiểm schema trước khóa không tương đương xem chỉ số mô hình. Sau khi xem kết quả, USN không còn là nguồn chưa xem cho các thay đổi tiếp theo.

Chạy một lần theo khóa hash protocol/code/raw/config/audit/môi trường sau khi test giả đạt. Từ chối ghi đè, kiểm hash trước và sau; giữ báo cáo/kết quả cũ. Nếu không đạt mức lỗi mong muốn, báo nguyên kết quả, không chọn câu thuận lợi hoặc hiệu chỉnh lại ngưỡng trong cùng lượt.
