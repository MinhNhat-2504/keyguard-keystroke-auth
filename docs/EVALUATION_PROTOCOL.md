# Giao thức đánh giá và giới hạn kết luận

## Hai thí nghiệm khác nhau

1. `run_benchmark.py`: mỗi người dùng học từ n mẫu đầu (5/10/20/50/100/200), genuine test là 200 mẫu cuối. 50 người còn lại chia A/B, mỗi nhóm 25; RF học mẫu impostor từ A, test dùng B chưa xuất hiện khi học. Ba mô hình một lớp cũng test trên B để so sánh cùng điều kiện. Hai kịch bản: 5 mẫu đầu hoặc 5 mẫu cuối của B. EER nội suy trên ROC theo từng người rồi lấy trung bình; đây là chỉ số đánh giá, không phải ngưỡng triển khai. AUC dùng chiều điểm giống chính chủ = âm điểm bất thường.
2. `select_threshold.py`: split người theo seed 42, 36 dev và 15 test. n=20, window=50, CV 5 fold để chuẩn hóa điểm. Mỗi người có 380 lần đăng nhập; thử impostor ngay sau đăng ký và sau mỗi 50 lần đăng nhập: trước lượt thứ 1/51/101/.../351. Impostor không cập nhật hồ sơ. Static giữ nguyên, accept cập nhật mẫu được nhận, fallback giả định genuine luôn qua xác minh bổ sung. FRR ở fallback là tỉ lệ cần xác minh thêm.

Static/fallback có điểm không phụ thuộc tau: chọn ranh giới dưới nhóm điểm đầu tiên vượt ngân sách `floor(FAR_mục_tiêu × số_điểm)`. Dùng `nextafter` và phép nhận `<= tau`, không chia tách điểm bằng nhau. Accept có điểm phụ thuộc tau: quét lưới định trước, chọn tau lớn nhất thỏa ràng buộc trên dev. Kiểm tra FAR dev sau chọn; mục tiêu 5% chỉ là thực nghiệm trên dev, không phải bảo đảm xác suất trên người mới.

## Diễn giải trung thực

- Benchmark đã dùng cả 51 người khi so sánh mô hình. 15 người test chỉ được tách riêng ở bước chọn ngưỡng, **không phải holdout chưa từng được xem trong toàn bộ quá trình phát triển**. Không điều chỉnh mô hình/chính sách sau khi nhìn test rồi coi là một đánh giá độc lập mới.
- Số gốc của CMU dùng toàn bộ 50 impostor, 5 lượt đầu/người; repo dùng nhóm B gồm 25 người để dành nhóm A cho RF. Vì vậy số gần công bố chỉ là kiểm tra đối chiếu, không chứng minh tái lập đúng cùng protocol. Nguồn chính: [CMU benchmark](https://www.cs.cmu.edu/~keystroke/).
- EER dùng nội suy tuyến tính giữa hai điểm ROC kẹp FAR=FRR. Timing phụ thuộc máy và phiên bản; RF hiện chạy `n_jobs=1` để hỗ trợ môi trường Windows hạn chế quyền tạo pipe. Không so timing mới với log cũ như cùng điều kiện.
- Mẫu trong `data/sample/` dựng từ CMU, chỉ dùng kiểm tra pipeline. CLI yêu cầu `--data-kind`; kết quả của nguồn này không phải thu thật. FAR thử “early/late” trên ít mẫu có thể dùng các tập trùng nhau; cần công bố lượng mẫu và không diễn giải như các quan sát độc lập.
- Fallback là giả định có một kênh xác minh bổ sung đáng tin. Mô phỏng không đo chất lượng OTP hay rủi ro kẻ gian làm lệch hồ sơ sau một lần được nhận nhầm.

## Đánh giá dữ liệu bàn giao

Chạy audit trước: kiểm tra JSONL, schema, giá trị session/rep, mẫu phím hợp lệ/hữu hạn và trùng `(participant_id, session, rep)`. Mẫu trùng/lỗi bị loại và ghi số dòng, không nhân bản để tăng quy mô. Audit đếm ≥15 người × ≥2 phiên × ≥40 mẫu; yêu cầu khác ngày và đồng ý phải đối chiếu nhật ký riêng vì schema chuẩn chưa chứa ngày/đồng ý.

`evaluate_collected.py` yêu cầu mỗi người có ≥25 mẫu hợp lệ: 20 enroll và ≥5 genuine test. Nếu không ai đủ, dừng và không sinh bảng kết quả giả. Mặc định phân tích chính loại TẤT CẢ dòng có khóa trùng, yêu cầu timestamp và sắp theo UTC; audit tổng quát giữ dòng đầu để chỉ ra quy mô, không thay audit cho protocol phân tích. Với CMU-derived không timestamp, phải thêm `--allow-missing-timestamp --order session`. Xuất bảng theo người/phiên, tử số/mẫu số, genuine theo lượt và danh sách loại mẫu. Không tinh chỉnh tau theo test. Protocol/kết quả snapshot10/11 xem [COLLECTED_PRELIMINARY.md](COLLECTED_PRELIMINARY.md); chỉ một checkpoint enrollment vì mọi người có dưới50 genuine logins.
