# Kiểm chứng nguồn độc lập — kế hoạch trước khi tính kết quả

Ngày lập: 13/11/2026. Mục tiêu: kiểm chứng phương pháp trên KeyRecs fixed-text do nhóm Dias và cộng sự công bố, chưa được dùng để phát triển các quy tắc của dự án này. Không dùng lại CMU/bộ tự thu và gọi là dữ liệu mới. Đây là kiểm chứng nội bộ của nhóm trên nguồn ngoài, không phải tái lập bởi một nhóm nghiên cứu độc lập hoặc đăng ký trước công khai.

Nguồn dự kiến: Zenodo record **7886743**, DOI10.5281/zenodo.7886743, tệp fixed-text.csv. Metadata nguồn và bài dữ liệu phải được lưu/đối chiếu; không tải demographics hoặc free-text vì không cần. Chỉ lưu raw ở data/raw được ignore, công bố manifest/hash và số liệu tổng hợp. Nếu giấy phép hoặc định dạng không phù hợp, dừng trước tính kết quả, ghi rõ nguyên nhân; không tìm nguồn thay thế chỉ vì kết quả xấu.

## Các quyết định đóng băng trước đánh giá

1. **Phương pháp không sửa:** dùng giữ mẫu/lọc cứng/trọng số mềm × Mean-Std/Median-MAD/Median-IQR (9 phương án) như code đã có. Mềm có sàn0,25, cutoff median+3robustsigma; lọc tối đa20%; CV5 trên20 enrollment, fit quy tắc chỉ trong train fold. Không thêm hằng số hoặc chọn theo tên người/mã.
2. **Chuyển định dạng:** giữ mọi cột thời gian dạng digraph do nguồn cung cấp theo thứ tự tệp; không đưa participant/session/repetition hoặc demographics vào vector. Số chiều có thể khác CMU31; đây là kiểm chứng phương pháp dimension-agnostic trên câu/thiết bị khác, không chuyển nguyên profile/tau CMU sang nguồn khác. Chỉ kiểm tra schema, số dòng, thiếu dữ liệu và khóa trước khi chấm; chưa tính EER/FAR/FRR.
3. **Chất lượng raw định trước:** loại dòng timing không hữu hạn hoặc metadata không hợp lệ; loại cả nhóm trùng khóa participant/session/repetition nếu có. Không cắt ngoại lệ thời gian hữu hạn, không bỏ người vì số đo mô hình xấu. Giữ thứ tự session/repetition; không tự sửa rep hoặc điền số.
4. **Điều kiện đủ:** mỗi mã có ít nhất25 mẫu hợp lệ phiên1 (20 enrollment+≥5 dev-genuine) và ít nhất10 mẫu phiên2 (đủ10 probe không trùng). Chốt danh sách chỉ theo metadata sau audit trước khi đánh giá; không dựa trên điểm mô hình.
5. **Chia mã cố định:** sắp mã hợp lệ, hoán vị NumPy RNG seed42; lấy floor(2N/3) mã làm dev, còn lại test. Vai trò tài khoản và impostor đều chỉ lấy trong cùng phân vùng. Không đổi seed hoặc chia lại khi đã xem kết quả. Không giả định chắc người tham gia không trùng với mọi nghiên cứu khác; chỉ xác nhận nguồn/dữ liệu dự án chưa dùng.
6. **Ngưỡng và lựa chọn:**20 mẫu đầu phiên1 tạo hồ sơ cố định. Dùng phần còn lại phiên1 của dev làm genuine validation; impostor dev là5 đầu+5 cuối phiên1 của các mã dev khác. Chọn chuẩn hóa trong hard-family/soft-family/all9 bằng2-fold mã trong dev, BER và tie-break theo tên như trước. Chọn lại ngưỡng FAR dev≤5% trên cả dev. Không dùng session2 của dev hoặc bất kỳ test-score để lựa chọn.
7. **Đánh giá nguồn ngoài:** mọi genuine phiên2 của mã test; impostor là5 đầu+5 cuối phiên2 của các mã test khác. Giữ cả9 phương án ở bảng mô tả, phân biệt với4 quy trình lựa chọn baseline/hard/soft/all. Không chọn phương án từ bảng test để tuyên bố thắng. Tính tử số/mẫu số, FAR/FRR, EER/AUC và sai số theo mã; chênh lệch so baseline cùng protocol. Không gộp mẫu số với nghiên cứu cũ.
8. **Thích nghi:** giữ static/window50/decay20 và CV lịch sử quá khứ như code cũ. Chấm ngưỡng mỗi phương pháp trên impostor dev tại mốc ngay sau20 enrollment phiên1. Đối với window/decay, warm-up bằng genuine còn lại phiên1 rồi chấm/cập nhật tuần tự phiên2; chỉ tính genuine phiên2 vào kết quả ngoài. Chấm10 probe của mỗi mã khác ở đầu phiên2, không cập nhật từ probe. Mọi genuine giả định được xác minh độc lập trước cập nhật, không coi đây là đo OTP/chống nhiễm. Không chỉnh half-life hoặc window theo nguồn mới.
9. **Bảo toàn kết quả:** lưu cả kết quả không thuận lợi, không thêm seed/phương án sau khi xem test. Khóa JSON protocol và SHA code/dependencies/schema/dataset trước lần đánh giá đầu; evaluator phải kiểm tra chúng. Nếu phát hiện lỗi triển khai, giữ kết quả/nhật ký cũ và nêu sửa lỗi, không âm thầm thay quy tắc. Tái chạy cùng protocol chỉ để tái lập xác định, không gọi là kiểm chứng mới.

## Trình tự dự kiến

Tra nguồn/giấy phép → tải file và kiểm checksum công bố → audit schema/metadata (không chấm mô hình) → hoàn thiện adapter/evaluator và test bằng dữ liệu giả lập → ghi manifest đóng băng với SHA/timestamp → đánh giá một lần → đối chiếu artifact → cập nhật báo cáo và trang khám phá. Không merge nhánh Thư, push GitHub hoặc thay cấu hình sản phẩm trong lượt này.

## Làm rõ schema sau audit, trước mọi kết quả mô hình

Tệp version1.0.0 được xác minh MD5 `f3c2ef3a42625f4df7183ea36d4543db`; metadata Zenodo khai giấy phép CC BY4.0. Có19.772 dòng dữ liệu (19.773 dòng kể header),99 mã,phiên1 có9.878 dòng/phiên2 có9.894. Không phát hiện khóa trùng hoặc timing không hữu hạn;99 mã đều đạt điều kiện đủ. Các số này chỉ là metadata, không phải điểm mô hình.

Giữ **47 timing descriptors =46 cột digraph + total time**, không chỉ nhóm digraph; đây là làm rõ adapter trước khi chấm, không chọn đặc trưng theo kết quả. Tên `DU.k.k` xuất hiện hai lần do hai vị trí trong chuỗi; giữ cả hai theo thứ tự, lần thứ hai đặt tên canonical `DU.k.k__occ2`. Không tính lại hold/DD/UD theo câu CMU và không gộp mất một cột. Không tải demographics/free-text. Chia mã theo quy tắc trên cho66 dev/33 test.

Chín phương án và ba phương pháp thích nghi dùng code đã có, tổng thể lựa chọn được khóa trong `results/external_validation_freeze.json` cùng SHA code,raw,schema và timestamp trước khi gọi evaluator. Chỉ báo cáo cải thiện toàn diện nếu FAR/FRR không xấu hơn và macro EER/AUC cũng không xấu hơn baseline cùng protocol; nếu có chỉ số xấu hơn thì nêu đánh đổi. Không điều chỉnh tiêu chí sau khi biết kết quả.
