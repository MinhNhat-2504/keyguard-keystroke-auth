# Bàn giao chuyển Render sang PostgreSQL

## Trạng thái đã kiểm tra ngày 13/11/2026

- GitHub `thu-branch` vẫn ở 3bcd919, chưa có cập nhật mới của Thư trong lần fetch này. Backend PostgreSQL được chuẩn bị trên nhánh riêng `storage/postgres-local`; không push vào nhánh đang auto-deploy khi chưa sao lưu runtime.
- Neon đã có schema và 601 mẫu/15 mã lịch sử, source hash khóa trong `migrate_verified_neon.py`. Tài khoản/profile/log không có trong ZIP nên không tự tạo lại. 16/16 kiểm thử local và 5/5 ca Neon đạt; backup/restore và dữ liệu chính sau test đã đối chiếu.
- Render CLI chính thức 2.36.0 đã được đăng nhập bằng trình duyệt. Workspace thấy được chỉ chứa `chess-xai-tutor`, `nali-dental-ai`, `nali-dental-web`, không có dịch vụ KeyGuard. Không sửa bất kỳ dịch vụ nào trong ba dịch vụ này.
- Downloads chưa có export mới hơn `keyguard_data_20261113_114958.zip`. Chưa lấy được backup runtime mới nhất, chưa xác định tài khoản/profile/log còn giữ được hiện tại.

Đăng nhập CLI thành công không đồng nghĩa có quyền trên KeyGuard. Cần cấp quyền bằng tài khoản/workspace thật sự quản lý `keyguard-keystroke-auth`, hoặc chủ dịch vụ bàn giao bản export mới và phối hợp đổi ENV/deploy. Không yêu cầu gửi mật khẩu/chuỗi kết nối vào chat.

## Điều kiện trước triển khai

1. Xác minh đúng service: URL `https://keyguard-keystroke-auth.onrender.com`, repo `MinhNhat-2504/keyguard-keystroke-auth`, nhánh/commit hiện tại, plan/vùng và trạng thái deploy. Không dựa vào tên workspace giống nhau để chọn.
2. Chốt khoảng ngừng nhận ghi. Lấy export hiện tại trước mọi thay đổi ENV, branch hoặc deploy; lưu nguyên ZIP, hash, thời điểm và đối chiếu đầy đủ file/hàng với Neon. Nếu khác, giữ riêng để review, không dùng import target-rỗng để ghi đè DB đã nhập.
3. API export hiện tại chỉ gồm collected/participants/attempts khi còn; không có accounts/profiles/challenges. Render Free không có Shell. Nếu không lấy được bản sao riêng của các phần đó, ghi là **chưa sao lưu/không truy cập được**, không kết luận chắc đã mất. Không redeploy để thêm export mới rồi gọi dữ liệu sau redeploy là trạng thái cũ.
4. Nếu không thể bảo toàn tài khoản/profile hiện tại, cần chủ dự án chốt cụ thể việc tài khoản đăng ký lại trước lượt chuyển có thể làm mất runtime. Chưa thực hiện quyết định đó trong bản bàn giao này.

## Cấu hình sẽ áp dụng sau khi đủ điều kiện

Giữ mọi biến hiện có trừ các thay đổi có chủ đích dưới đây:

| Biến | Giá trị/nguồn |
|---|---|
|`KEYGUARD_STORAGE`|`postgres`|
|`DATABASE_URL`|Giá trị direct của `DATABASE_URL_UNPOOLED` trong `.env.local` riêng tư; đã thử các ca ghi trên direct/TLS|
|`KEYGUARD_ADMIN_KEY`|Khóa mới chỉ đặt sau sao lưu, không đưa vào Git/chat/log|
|`KEYGUARD_VERIFY_LIMIT`|Giữ giá trị thật của dịch vụ, không đoán từ ảnh bị che|
|`PYTHON_VERSION`|Kiểm tra phiên bản hỗ trợ requirements hiện có trước deploy|

Build giữ quy ước Python hiện tại (`pip install -r requirements.txt` nếu đang dùng); start giữ Gunicorn của dịch vụ. Không thêm lệnh import tự động vào Build/Start, không ghi secret vào các lệnh này. Schema đã init trên Neon. Gói ứng dụng phải có `pg_storage.py` và `psycopg[binary]`; không đưa `.env*`, raw, backup hoặc profile vào artifact.

Chuẩn bị ENV và nguồn commit trước, rồi triển khai một lượt có kiểm soát; tránh đổi ENV nhiều lần khiến redeploy bản file cũ. Không mua gói trả phí, tạo dịch vụ khác hoặc gắn DB ngoài vào dịch vụ NaLi/chess để thay thế KeyGuard.

## Kiểm tra sau triển khai

- Đối chiếu đúng commit, schema và số đếm trước khi mở nhận ghi.
- Dùng mã/tài khoản thử tách biệt để kiểm tra collector/resume, enroll, verify, OTP sai/đúng/replay và log. Giữ test riêng khỏi tập FAR–FRR.
- Restart Render rồi đọc lại tài khoản/tiến độ/OTP đang chờ. Đây là kiểm thử Render còn chưa làm; không suy từ kết quả Gunicorn local.
- Sao lưu PostgreSQL sau đợt kiểm tra. Nếu lỗi, ngừng ghi và sửa bản web dùng cùng DB; không quay về file mode để tiếp tục nhận dữ liệu thành hai bộ trạng thái.

Các bước triển khai và kiểm tra trên vẫn chờ đúng quyền truy cập và bản sao runtime. Tài liệu này không xác nhận production đã được chuyển sang PostgreSQL.

## Đợt bàn giao bổ sung ngày 14/11/2026

Người dùng đã yêu cầu thực hiện bước 1 và 2 theo phạm vi dữ liệu hiện có. Đã nhận `participants.json` (15 mã) và `attempts.csv` (9 dòng: 4 verify, 5 OTP). CSV khớp theo trường với `docs/kiem_thu_otp_20261113.csv` trong cập nhật Thư c516c32; đây là log ca biên riêng, không nhập vào bộ 33 lượt live nghiên cứu. Không có backup account/profile; không kết luận trạng thái filesystem hiện tại đã mất chỉ từ việc thiếu file.

Đã nhập bổ sung vào Neon bằng `scripts/import_handover_batch.py`, nguồn khóa hash và mặc định dry-run. Transaction chỉ ghi khi 601 mẫu còn đúng bản gốc và chưa có registry/account/log khác. Sau nhập: kg_samples=601, kg_documents=1, kg_attempts=9, kg_imports=2. Registry giữ nguyên timestamp P11/P12 sai định dạng; không sửa hồi cứu. Nhập lại không nhân đôi, export HTTP khớp; backup đầy đủ sau nhập đã restore thử trên PostgreSQL local và khớp. Kết quả công khai trong checkout nghiên cứu `results/neon_handover_validation.json`.

Đã merge origin/thu-branch c516c32 vào nhánh storage để giữ hai commit mới của Thư; backend/model/UI không đổi qua merge. Kiểm tra lại Render CLI vẫn không thấy KeyGuard trong workspace hiện tại, chưa đổi ENV hoặc deploy.

### Các thao tác cho chủ dịch vụ KeyGuard

1. Mở [Render Dashboard](https://dashboard.render.com/), chọn đúng dịch vụ có URL `keyguard-keystroke-auth.onrender.com`. Tạm ngừng thu/test trong lượt chuyển. Nếu còn dữ liệu runtime khác cần giữ, xuất riêng trước mọi thay đổi; đợt bàn giao trên không khẳng định đầy đủ trạng thái hiện tại.
2. Trên máy dự án, mở tệp riêng tư `.storage-test/render-keyguard.env`. Tệp đã chuẩn bị URL direct/TLS của Neon và khóa admin mới nhưng chưa áp dụng; không gửi nội dung vào chat/Git/ảnh. Người dùng quản lý việc cung cấp riêng tư cho chủ dịch vụ, không tự công khai hoặc gửi qua công cụ chat.
3. Trong dịch vụ → **Environment** → **Add from .env**, thêm đúng ba biến trong tệp. Thay giá trị admin key cũ; giữ `KEYGUARD_VERIFY_LIMIT`, `PYTHON_VERSION` và các biến khác. Chọn **Save only**, chưa deploy build cũ với ENV mới. Render hỗ trợ tùy chọn này theo [tài liệu ENV chính thức](https://render.com/docs/configure-environment-variables).
4. Trong **Settings** → **Build & Deploy** → **Branch**, chuyển sang `storage/postgres-local` đã chứa backend và cập nhật mới của Thư. Không chọn nhánh main nghiên cứu. Xác nhận Build vẫn cài requirements và Start dùng Gunicorn. Lưu cấu hình; nếu Render chưa tự triển khai thì dùng **Manual Deploy → Deploy latest commit**. Bản triển khai phải là commit mới nhất của nhánh storage, không phải build cũ 3bcd919/c516c32.
5. Chờ Events báo **Live**, ghi commit SHA và thời điểm. Tài khoản/profile cũ chưa phục hồi trong Neon nên sẽ cần đăng ký lại theo phạm vi chuyển hiện có. Không nhầm dữ liệu gõ lịch sử với profile đăng nhập.
6. Gửi trạng thái/commit deploy để đối chiếu (không gửi secret). Sau đó mới kiểm tra ghi bằng mã/tài khoản thử và restart Render để xác nhận dữ liệu còn trong DB. Chưa đánh dấu bước này hoàn thành từ kết quả local.

Nếu không có quyền đổi ENV/Branch của KeyGuard, dừng ở bước chuẩn bị và yêu cầu chủ dịch vụ thực hiện. Không dùng quyền trên dịch vụ khác hoặc chỉ push thu-branch để thay thế việc cấu hình PostgreSQL.
