# Bàn giao phần Nhật — cập nhật 10/11/2026

## Đã hoàn tất độc lập

Trạng thái hiện tại ở phần cập nhật10/11 cuối file; các mốc01/11 bên dưới giữ lịch sử. Phần ghi “chưa có dữ liệu thật” và điểm43/50 thuộc lần trước.

- Task 1.1–1.2: cấu trúc, thư viện và hướng dẫn; 31 đặc trưng, loader và roundtrip CMU.
- Task 1.3: EER nội suy, bốn họ mô hình (năm biến thể), chạy lại 30 cấu hình × 51 người; ROC, AUC, EER, bảng/hình/timing cùng lần chạy. RF dùng một worker để chạy trên Windows bị hạn chế tạo pipe. Log: `results/benchmark_run.log`.
- Task 1.4: chọn tau theo dev với nhóm điểm trùng và phép accept <= tau; kiểm tra FAR dev sau chọn. Sửa lịch thử impostor theo số lượt đăng nhập sau enrollment. Chạy lại đủ ba chính sách, có kết quả theo 15 người test và ngưỡng mới. Log: `results/select_threshold.log`.
- Công cụ cho 1.5: audit JSONL/số người/phiên/mẫu, bắt dòng hỏng/trùng; đánh giá có nhãn nguồn dữ liệu rõ ràng. Đã chạy pipeline CMU-derived và thử dữ liệu hiện có từ nhánh web: hai mẫu hợp lệ, không ai đủ 25 mẫu, evaluator dừng đúng. Không tạo bảng kết quả thu thật.
- Phần report có đủ dữ kiện: cập nhật phương pháp/kết quả, sơ đồ kiến trúc từ source, AUC, phân tích lỗi theo từng người, giới hạn split và giả định OTP. Có script tạo lại từ template. Đã xuất Word/PDF 6 trang bằng Word 16.0, kiểm tra PDF và xem trực quan; còn các nhãn CHỜ TV2.
- Đã sửa phụ lục trang 5–6 về định dạng hai cột theo thân bài, căn lại hình/bảng theo khổ cột và kiểm tra cả hai cột có nội dung. Bản Word/PDF sau sửa vẫn 6 trang; script tạo lại đã giữ định dạng này.
- 26 test đạt, không lỗi/skip; XML ở `results/test_results.xml`. Smoke mô hình với cấu hình thực: enroll20 → verify → update21 và JSON roundtrip đạt; nguồn CMU-derived, không phải test HTTP/OTP. Bảng 1.530 dòng/30 summary, 45 dòng theo người/chính sách và cấu hình khớp nhau.

## Chưa thể hoàn tất trước khi có đầu vào thật

- Task 1.5: cần dữ liệu người tham gia đủ quy mô, nhật ký ngày/thiết bị và xác nhận đồng ý; sau đó đánh giá, lập bảng/hình theo người/phiên và phân tích lỗi thực tế.
- Task 1.6: cần ảnh thật và kết quả live test/OTP của web đã sửa tích hợp; thay nhãn chờ, chỉnh lại bố cục 6 trang sau khi thêm hình/bảng. Bản Word hiện là bản thảo trung thực, chưa phải bản nộp cuối.
- Chi tiết giao nhận: `docs/TV1_HANDOFF.md`. Không thay số liệu thiếu bằng dữ liệu dựng lại; không nhận điểm phần thực nghiệm chưa có.

## Số liệu đã thay thế bản cũ

Fallback: tau=0,2720094565, FAR test=1,488095%, FRR test=19,210526%. Static: FRR75,035088%; accept: tau0,8, FAR2,773810%, FRR48,385965%. Lịch checkpoint cũ đếm theo chỉ số toàn chuỗi làm số cũ khác, nên đã cập nhật đồng bộ CSV/JSON/hình/report/README.

FAR tổng không phản ánh mọi người: s018 có FAR30/560=5,36%; s002 có FRR93/380=24,47%. Đây là phân tích CMU dưới giả định fallback, không suy ra chất lượng dữ liệu thu thật hay thay ngưỡng theo test.

Điểm tiến độ tự đánh giá có minh chứng: **43/50 (8,6/10)**, chi tiết từng task trong `../../CHAM_DIEM.md`: 3 + 7 + 15 + 3 + 3 + 12. Giữ lại 7 điểm của phần chưa có đầu vào/kiểm chứng thực tế; điểm không chính thức.

## Kết quả mới ngày 10/11 — đánh giá sơ bộ đã hoàn thành

- Đã nhập nguyên byte15 JSONL/601 dòng từ commit44a610bd120b09e2838e76073cb164c3ce6cac36, manifest SHA-256. Phân tích chính loại cả2 dòng trùng P10/session1/rep29 và2 mẫu thiếu timestamp →597 mẫu; sắp UTC,20 enroll/mã,297 genuine test. Raw không sửa; file exclusions ghi lý do/dòng nguồn.
- Giữ cấu hình CMU tau0,2720094565, không tinh chỉnh theo test. Genuine49/297 cần xác minh=16,50%; FAR đầu284/1050=27,05%, cuối331/1050=31,52%. EER trung bình15,81%/18,90%. Impostor chỉ thử ở enrollment vì mỗi người dưới50 lượt genuine; không gọi là live test hoặc người mới độc lập.
- Có bảng theo mã, phiên, genuine từng lượt, thống kê thời gian/score enrollment, hình và tài liệu docs/COLLECTED_PRELIMINARY.md. Độ nhạy giữ dòng đầu khóa trùng cho598 mẫu/298 genuine,FRR16,44%,FAR không đổi; không chọn policy dữ liệu theo kết quả đẹp.
- P10/P13/P15 FAR rất cao, P12 FRR55%, P14 FRR45%; dữ liệu chủ yếu cùng phiên và thiếu metadata nên chưa kết luận nguyên nhân hoặc bảo mật web. FAR cao là kết quả cần công bố, không sửa số/giảm ngưỡng theo chính bộ đã xem.
- Report Word/PDF đã cập nhật dữ liệu thật, trạng thái web và giới hạn, giữ6 trang/hai cột; vẫn chờ ảnh và live test.27 test đạt, không fail/error/skip, thêm test loại cả nhóm trùng và sắp theo timestamp. Kết quả CMU trước đây giữ nguyên, không chạy lại khi code mô hình/ngưỡng không đổi trong bước này.

**Điểm tiến độ Nhật đề xuất mới:47/50=9,4/10**, phân bổ3+7+15+3+6+13. Task1.5 từ3→6/7: đã đánh giá dữ liệu thực nhưng chưa đủ chứng minh nhiều phiên/ngày. Task1.6 từ12→13/15: có kết quả/hình/phân tích thật, còn ảnh sử dụng và live test, chưa phải bản nộp cuối. Thư giữ36/50, tổng83/100. Không cộng đủ điểm khi chưa đủ bằng chứng; điểm không chính thức.

Để tái lập, xem docs/COLLECTED_PRELIMINARY.md. Cấu hình này khác bản web tau0,250315 ở nhánh nguồn; khi tích hợp cần dùng cả thư viện/cấu hình cùng phiên bản, không trộn số liệu. Bản main tập trung phần Nhật, không merge hay sửa nhánh Thư.

Phạm vi push: repo public; raw601 mẫu và bảng genuine từng lượt giữ local/ignore, chỉ bàn giao code/manifest/tổng hợp/hình/report. Lần push ban đầu chứa raw bị auto-review chặn; đã bỏ raw khỏi commit mới, không thay đổi hay xóa file dữ liệu local.

Đã bàn giao commit chức năng `674dfdccbad4125b173a3ca19ca247296da3781b` lên GitHub main, xác minh bằng ref remote và commit API. Report6 trang hai cột,27 test đạt, kết quả sơ bộ/giới hạn và điểm47/50 như trên.
