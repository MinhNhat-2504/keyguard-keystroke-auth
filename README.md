# KeyGuard — Bản nộp ngày 19/11/2026

Trịnh Ngọc Minh Nhật · Nguyễn Anh Thư  
Giảng viên hướng dẫn: Nguyễn Thái Anh  
Bài tập lớn môn Học máy Ứng dụng — Trường Đại học Văn Lang

Bản nộp gồm **báo cáo Word/PDF và link GitHub**. Không yêu cầu chạy dịch vụ thật hoặc mở lại thu dữ liệu để đọc và chấm bài. Nhánh này là snapshot bàn giao riêng; không thay nhánh đang deploy.

## Đọc báo cáo

- [Báo cáo chính — PDF 6 trang](reports/KeyGuard_BaoCao_Chinh_6Trang_20261119.pdf) · [Word](reports/KeyGuard_BaoCao_Chinh_6Trang_20261119.docx).
- [Bản nghiên cứu bổ sung — PDF 47 trang](reports/KeyGuard_BaoCao_NghienCuu_20261119.pdf) · [Word](reports/KeyGuard_BaoCao_NghienCuu_20261119.docx).

Thư mục `research/` chứa thư viện, runner, protocol, kết quả cố định và Explorer. Thư mục `web/` giữ code runtime đúng commit **b0bd22e13fd4f1c56ca2e638936daaa5f0767e39**, kèm helpers B1/B3 và dữ liệu giả đã kiểm. `evidence/` có ảnh/log đã rà và biên bản vận hành từ `thu-branch` **004bf1d847791fdd59126efbeda64755222fd0c8**, cùng kết quả đối chiếu độc lập. `SOURCE_MANIFEST.json` ghi hash từng tệp và nguồn snapshot.

Giải nén toàn bộ repo rồi mở `research/explorer/index.html#evidence` để xem bảng offline. Các đường dẫn `results/...`, `docs/...`, `scripts/...` trong phần nghiên cứu được hiểu từ thư mục `research/`. Các đường dẫn lịch sử trong biên bản người vận hành được giữ để truy vết; ảnh tương ứng đặt tại `evidence/screenshots/`.

## Phạm vi kết luận

- Bộ nghiên cứu tự thu: 601 dòng ban đầu/15 mã, 597 mẫu sau loại bảo thủ; chủ yếu một phiên. Giữ giới hạn P10/metadata và provenance log live cũ. Không dựng phiên/ngày hoặc metadata thiếu.
- Bản backup cuối dùng kiểm lưu trữ có 609 mẫu = 601 cũ + 8 P16 thử; thêm tài khoản test. P16/tài khoản test không được đưa vào kết quả nghiên cứu hoặc live33 lượt.
- Không thay detector/ngưỡng hoặc chọn lại mô hình. Các kết quả bất lợi và đối chứng không đạt vẫn được giữ; bootstrap theo tài khoản là mô tả hồi cứu có điều kiện, không phải kiểm chứng trên dữ liệu mới.
- D1–D6 được nghiệm thu trong phạm vi hồ sơ ảnh/log và kiểm độc lập đã nêu. D4 dựa trên hồ sơ restart Render của người vận hành; D5 đã restore backup thực nhận vào PostgreSQL local rỗng, so toàn bộ nội dung/hash và nhập lại không nhân đôi. GET web/static200 và khóa admin cũ404 được kiểm riêng. Không tuyên bố đã tự chạy toàn bộ production hoặc bảo đảm an toàn lâu dài.
- Sự cố deploy sớm và thiếu xác nhận mẫu chờ trong lịch sử được công bố; không đánh dấu như chưa từng có sự cố. Mở lại thu là quyết định vận hành riêng, không điều kiện nộp bài.

## Chạy mã local

Dùng Python3.11 và môi trường ảo riêng cho từng phần; cài `requirements.txt` trong thư mục tương ứng. Không nâng dependency để ép các phép kiểm freeze qua. Môi trường chuẩn bị gói đã chạy đạt50test dữ liệu giả/file-mode trên mã đóng gói; không gọi số đó là kiểm production.

Ví dụ PowerShell tại `web/` sau khi cài dependency:

```powershell
$env:PYTHONUTF8='1'
$env:KEYGUARD_STORAGE='file'
$env:DATABASE_URL=''
$env:KEYGUARD_DATA_DIR=Join-Path $PWD 'local-test-data'
python app.py
```

Mở `http://127.0.0.1:5000`. Enroll cần20lượt hợp lệ của `.tie5Roanl` + Enter; OTP là mô phỏng. File storage chỉ dùng local. Collector cần mã thiết bị tự khai báo; trình duyệt tự tạo request_id và giữ mẫu chờ trong tab để retry.

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
