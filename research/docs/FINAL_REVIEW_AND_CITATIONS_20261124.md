# Rà phản biện và trích dẫn trước nộp

## Lập luận và quyết định thiết kế

Đã đối chiếu lý do chọn Scaled Manhattan với phần so sánh mô hình, mã detector và cấu hình. Báo cáo nêu rõ cả Isolation Forest và RF-early có EER thấp hơn ở20mẫu. Scaled Manhattan được dùng làm mốc vì tham số từng chiều dễ kiểm tra/lưu và cập nhật từ mẫu chính chủ; đây là lựa chọn triển khai phục vụ nghiên cứu thích nghi, không phải thắng EER. Giữ baseline là giữ mốc so sánh khi các nhánh chưa đạt tiêu chí, không phải chứng nhận cấu hình tối ưu hoặc mức lỗi thấp trên mọi nguồn.

Ba câu hỏi ở 1.2 được trả lời lần lượt ở 3.1; sáu mục tiêu vẫn được đối chiếu ở Bảng 3.1. Các đối chứng phân biệt việc thay detector, đổi chuẩn hóa hoặc đổi lịch sử hồ sơ. Kết quả bất lợi được giữ; không dùng phép bỏ nhóm thay bảng đủ nhóm và không gọi các lần đếm lại artifact là kiểm chứng mới. OTP mô phỏng, FRR tại bước nhịp gõ và kết quả sau xác minh được phân biệt.

## Nguồn ngoài đã đối chiếu

Rà metadata và những mệnh đề quan trọng đang được dẫn, không nhận đã tái lập tất cả thí nghiệm trong các bài gốc. Nguồn thư viện dùng để kiểm khái niệm/API; phiên bản chạy thực nghiệm vẫn theo khóa của dự án, không thay bằng phiên bản stable hiện nay.

| Tài liệu | Nguồn chính | Nội dung đối chiếu |
|---|---|---|
| [1] Killourhy–Maxion | https://www.cs.cmu.edu/~keystroke/KillourhyMaxion09.pdf ; https://www.cs.cmu.edu/~keystroke/ | Tên bài, tác giả, trang125–134; mục5.5 định nghĩa mean absolute deviation; 51 người/400 lượt/8 phiên và đặc trưng H/DD/UD. Thiết kế nhóm khác protocol gốc và được ghi riêng |
| [2] OneClassSVM | https://scikit-learn.org/stable/modules/generated/sklearn.svm.OneClassSVM.html | Nu liên quan giới hạn lỗi học/support vectors, không bảo đảm FAR/FRR test bằng nu; RBF/chuẩn hóa là cấu hình code nhóm |
| [3] IsolationForest | https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.IsolationForest.html | Cơ chế chia ngẫu nhiên và hướng score; 200 cây/seed là lựa chọn của nhóm |
| [4] RandomForestClassifier | https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.RandomForestClassifier.html | Bộ phân loại và trọng số balanced; cách tạo lớp đối lập nằm trong protocol nhóm |
| [7] KeyRecs | https://api.crossref.org/works/10.1016/j.dib.2023.109509 ; https://zenodo.org/records/7886743 | Crossref xác nhận đủ năm tác giả gồm Orlando Sousa, bài Data in Brief50/109509. Version1.0.0 và nguồn bài được Zenodo dẫn |
| [12] SciPy bootstrap | https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.bootstrap.html | paired=True dùng cùng chỉ số lấy mẫu; percentile là phương pháp được nhóm chọn, không phải mặc định BCa |
| [15] Teh và cộng sự | https://onlinelibrary.wiley.com/doi/10.1155/2013/408280 | Tác giả, năm2013/408280; dwell/flight, các hướng biểu diễn và đánh giá |
| [16] Monrose–Rubin | https://www.cs.columbia.edu/4180/hw/keystroke.pdf | Tên bài, hai tác giả, FGCS16/351–359/2000; xác thực từ hành vi và thời gian gõ |
| [17] LedoitWolf | https://scikit-learn.org/stable/modules/generated/sklearn.covariance.LedoitWolf.html | Shrinkage covariance; dẫn đúng Ledoit–Wolf, JMVA88(2)/365–411/2004. Không đồng nhất với công thức shrink25 do nhóm thiết kế |
| [18] GREYC-Web | https://www.labri.fr/perso/rgiot/resources/webgreycdb/ | Trang tác giả dẫn IIHMSP2012; dữ liệu cập nhật sau bài, common passphrases và thứ tự captures được mô tả |
| [19] Gonzalez | https://www.cs.columbia.edu/~verma/classes/uml/ref/clustering_minimize_intercluster_distance_gonzalez.pdf | Tên bài, TCS38/293–306/1985 và chọn điểm xa nhất. Không suy bảo đảm hình học thành bảo đảm nhận dạng |
| [21] Risto–Graven | https://link.springer.com/article/10.1007/s12243-024-01039-z | Hai tác giả, Annals79/731–743/2024, 5 chính chủ/sáu câu và thu đơn phiên; bài dẫn DOI bộ dữ liệu |
| [22] USN v1 | https://api.figshare.com/v2/articles/23790858/versions/1 | Đủ hai tác giả, tiêu đề có dấu hai chấm sau “for”, phiên bản1, DOI10.23642/usn.23790858.v1, ngày công bố2023-09-12 và CC BY4.0 |

Metadata gọn của [7]/[22] được lưu ở `results/final_primary_metadata_20261124.json`. Một số trang DOI/PMC chặn truy cập tự động; dùng bản tác giả, trang nhà xuất bản truy cập được hoặc API metadata chính thức nêu trên, không suy nguồn giả từ lỗi HTTP.

Các nguồn nội bộ [5], [6], [8]–[11], [13], [14], [20], [23], [24] là mã/protocol/artifact của nhóm, không đóng vai bài báo khoa học bên ngoài. Checker nhánh nộp kiểm đường dẫn, hash, số đếm và quan hệ giữa artifact. Không dùng số test chức năng làm bằng chứng hiệu quả mô hình.

## Sửa trong báo cáo

Làm rõ lý do baseline và tách công thức Scaled Manhattan kế thừa với sàn số học10⁻⁹ của bản cài đặt. Tài liệu [1] trỏ thẳng PDF tác giả, [22] sửa dấu hai chấm theo metadata. Sửa ba lỗi chữ nhỏ: “. lượt chính chủ”, “mẫu mẫu” và “vàtotal”. Không đổi số đo, công thức, bảng hoặc hình.
