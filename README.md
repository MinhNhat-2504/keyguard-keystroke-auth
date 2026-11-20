# KeyGuard — Bài tập lớn Học máy Ứng dụng

Trịnh Ngọc Minh Nhật · Nguyễn Anh Thư  
Giảng viên hướng dẫn: Nguyễn Thái Anh  
Bài tập lớn môn Học máy Ứng dụng — Trường Đại học Văn Lang

Bản nộp gồm **PDF báo cáo đầy đủ và link GitHub**, theo hướng dẫn của giảng viên. Word được giữ để chỉnh sửa. Báo cáo cập nhật ngày 20/11/2026; hạn nộp nhóm xác nhận là hết ngày 22/11/2026, giờ Việt Nam. Nhánh này là bản bàn giao riêng, không thay nhánh đang triển khai dịch vụ.

## Đọc báo cáo

- [Báo cáo nộp — PDF đầy đủ 45 trang](reports/KeyGuard_BaoCao_Nop_20261120.pdf) · [Word cùng phiên bản](reports/KeyGuard_BaoCao_Nop_20261120.docx).
- [Bản tóm tắt 6 trang trước đó](reports/KeyGuard_BaoCao_Chinh_6Trang_20261119.pdf) được giữ để tham khảo, không thay PDF đầy đủ khi nộp email.
- [Bản nghiên cứu 47 trang trước chỉnh sửa](reports/KeyGuard_BaoCao_NghienCuu_20261119.pdf) là bản lịch sử; các bản Word/PDF cũ vẫn có trong [reports/](reports/).

Các công thức của bản nộp là Equation Word; có bảng đối chiếu mục tiêu–kết quả và nguồn tham khảo phân biệt tài liệu khoa học với hồ sơ thực nghiệm của nhóm. [Ghi chú đọc hiểu](docs/READING_GUIDE.md) giải thích những khái niệm cần tự kiểm tra trước khi nộp.

Thư mục `research/` chứa thư viện, runner, protocol, kết quả cố định và Explorer. Thư mục `web/` giữ code runtime đúng commit **b0bd22e13fd4f1c56ca2e638936daaa5f0767e39**, kèm helpers B1/B3 và dữ liệu giả đã kiểm. `evidence/` có ảnh/log đã rà và biên bản vận hành từ `thu-branch` **004bf1d847791fdd59126efbeda64755222fd0c8**, cùng kết quả đối chiếu độc lập. `SOURCE_MANIFEST.json` ghi hash từng tệp và nguồn snapshot.

Các nguồn tổng hợp được báo cáo dẫn gồm [kết quả 597 mẫu tự thu](research/results/collected_preliminary_summary.json), [bảng ngưỡng CMU](research/results/threshold_selection.csv) và [cấu hình nghiên cứu](research/models/model_config.json). Đã bổ sung các script/tài liệu được báo cáo dẫn; không bổ sung raw riêng tư hoặc chạy lại mô hình để thay số liệu.

`config_sha256` trong summary tính từ `json.dumps(cfg, sort_keys=True)` như code đánh giá gốc. Đây là hash biểu diễn JSON đã sắp khóa, khác hash byte của file trong manifest; hai loại được kiểm riêng.

`research/results/live_test_summary.json` là đợt lịch sử ngày 11/11: 34 lượt verify có role và 6 event OTP. Đợt 33 verify ngày 13/11 được báo cáo riêng; không ghép hai mốc. `research/results/test_results.xml` lưu lần chạy 27 test lịch sử, không phải kết quả kiểm checkout sạch hiện tại.

Giải nén toàn bộ repo rồi mở `research/explorer/index.html#evidence` để xem bảng offline. Các đường dẫn `results/...`, `docs/...`, `scripts/...` trong phần nghiên cứu được hiểu từ thư mục `research/`. Các đường dẫn lịch sử trong biên bản người vận hành được giữ để truy vết; ảnh tương ứng đặt tại `evidence/screenshots/`.

## Phạm vi kết luận

- Bộ nghiên cứu tự thu: 601 dòng ban đầu/15 mã, 597 mẫu sau loại bảo thủ; chủ yếu một phiên. Giữ giới hạn P10/metadata và provenance log live cũ. Không dựng phiên/ngày hoặc metadata thiếu.
- Bản backup cuối dùng kiểm lưu trữ có 609 mẫu = 601 cũ + 8 P16 thử; thêm tài khoản test. P16/tài khoản test không được đưa vào kết quả nghiên cứu hoặc live33 lượt.
- Không thay detector/ngưỡng hoặc chọn lại mô hình. Các kết quả bất lợi và đối chứng không đạt vẫn được giữ; bootstrap theo tài khoản là mô tả hồi cứu có điều kiện, không phải kiểm chứng trên dữ liệu mới.
- D1–D6 được nghiệm thu trong phạm vi hồ sơ ảnh/log và kiểm độc lập đã nêu. D4 dựa trên hồ sơ restart Render của người vận hành; D5 đã restore backup thực nhận vào PostgreSQL local rỗng, so toàn bộ nội dung/hash và nhập lại không nhân đôi. GET web/static200 và khóa admin cũ404 được kiểm riêng. Không tuyên bố đã tự chạy toàn bộ production hoặc bảo đảm an toàn lâu dài.
- Sự cố deploy sớm và thiếu xác nhận mẫu chờ trong lịch sử được công bố; không đánh dấu như chưa từng có sự cố. Mở lại thu là quyết định vận hành riêng, không điều kiện nộp bài.

## Chạy mã local

Dùng Python 3.11 và môi trường ảo riêng; cài `requirements.txt` trong thư mục tương ứng. Để kiểm toàn bộ các lệnh dưới đây trong cùng môi trường local, có thể cài cả `research/requirements.txt` và `web/requirements.txt`; các phiên bản thư viện nghiên cứu vẫn được giữ nguyên. Không nâng dependency để ép các phép kiểm freeze qua.

Sau khi clone, chạy `python verify_submission.py` ở gốc repo. Lệnh này chỉ cần Python standard library: kiểm manifest, các tham chiếu tệp trong báo cáo, cặp JSON/CSV và số đếm nguồn. Nó không huấn luyện lại mô hình hoặc ghi database.

Ví dụ PowerShell tại `web/` sau khi cài dependency:

```powershell
$env:PYTHONUTF8='1'
$env:KEYGUARD_STORAGE='file'
$env:DATABASE_URL=''
$env:KEYGUARD_DATA_DIR=Join-Path $PWD 'local-test-data'
python app.py
```

Mở `http://127.0.0.1:5000`. Enroll cần 20 lượt hợp lệ của `.tie5Roanl` + Enter; OTP là mô phỏng. File storage chỉ dùng local. Collector cần mã thiết bị tự khai báo; trình duyệt tự tạo request_id và giữ mẫu chờ trong tab để retry.

Test local trong `web/`:

```text
python -X utf8 -m unittest tests.test_collection_api.FileCollectionAPI
python -X utf8 -m unittest discover -s tests -p test_data_quality_thu.py
python -X utf8 tests/test_otp_boundaries_thu.py
```

Test logic dữ liệu giả trong `research/`:

```text
python -X utf8 -m unittest discover -s tests -p test_greyc_key_pairing.py
python -X utf8 -m unittest discover -s tests -p test_covariance_control.py
python -X utf8 -m unittest discover -s tests -p test_account_benefit_summary.py
python -X utf8 -m unittest discover -s tests -p test_account_uncertainty.py
```

Các runner thực nghiệm cần đúng CMU/KeyRecs/GREYC, nguồn và điều kiện sử dụng ghi trong protocol/data README. Raw tự thu và private backup không công bố; không hướng dẫn chạy toàn bộ test lịch sử khi thiếu các đầu vào này. Đọc CSV/checksum không đồng nghĩa đã chạy lại mô hình. PostgreSQL test/restore chỉ chạy trên database local riêng rỗng; không dùng thông tin kết nối dịch vụ thật.

Repo không chứa `.env`, DATABASE_URL thật, khóa, account/profile/challenge thực, private backup, raw tự thu, consent, lịch sử chấm điểm nội bộ hoặc môi trường ảo. Có số liệu theo mã giả danh trong artifact công khai và dữ liệu giả được ghi nhãn. Không gửi credential qua issue, ảnh nộp hoặc commit.
