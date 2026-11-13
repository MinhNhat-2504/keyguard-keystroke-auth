# Chuẩn bị PostgreSQL — chưa triển khai Render

Nhánh local `storage/postgres-local`, nền web3bcd919. Đã thêm backend PostgreSQL, công cụ nhập dữ liệu cũ và private backup/restore. Không đổi `keyguard/`,model_config,templates/staticUI hoặc kết quả nghiên cứu. Đã liên kết Neon, khởi tạo schema và nhập ZIP lịch sử 601 mẫu; chưa push hoặc thay dịch vụ Render. Xem [kế hoạch chuyển](NEON_MIGRATION_PLAN.md) để biết trạng thái mới nhất.

## Dữ liệu được lưu

| Bảng | Nội dung |
|---|---|
|kg_documents|Registry người tham gia/tài khoản, JSON profile hiện có, challenge OTP gồm hash/salt/thời hạn/mẫu chờ; không lưu OTP plaintext|
|kg_samples|Một hàng JSONB cho mỗi mẫu, ID nội bộ tăng dần để giữ thứ tự|
|kg_attempts|Nhật ký verify/OTP theo schemaCSV hiện có, không tên tài khoản/mẫu gõ/OTP|
|kg_imports|Hash nguồn đã nhập để tránh nhập lại trùng|
|kg_schema|Phiên bản schema1; phiên bản khác cần migration riêng|

Giữ hợp đồng JSON/profile của mô hình. Tài khoản/profile/challenge hiện lưu thành các documentregistry, không thiết kế lại thành mô hình quan hệ chi tiết trong bước này. Khóa advisory theo transaction toàn ứng dụng giữ an toàn read-modify-write giữa các worker; đây là thiết kế ưu tiên đúng đắn cho quy mô bài tập lớn, chưa tối ưu throughput lớn.

Mỗi requestAPI/admin dùng một connection/transaction. Đăng ký, cập nhật profile và ghi log cùng commit hoặc rollback khi lỗi500; OTPwrong401 vàlocked429 vẫn commit số lần thử/xóa challenge. Cấu hình PG lỗi hoặc thiếu schema sẽ dừng, **không fallback vào file**. Chưa chuyển rate limit từ RAM sangdatabase: giới hạn verify vẫn đếm riêng mỗi worker như trước. OTP mô phỏng và các giới hạn thuật toán không thay đổi; logexpired chưa có đủ mapping nếu challenge bịpurge vẫn là giới hạn cũ.

## Chọn backend

- Không cóDATABASE_URL vàkhôngKEYGUARD_STORAGE: backendfile cũ.
- `KEYGUARD_STORAGE=postgres` và`DATABASE_URL` của database: PostgreSQL. CóDATABASE_URL màkhông chỉ định backend cũng chọnPG.
- `KEYGUARD_STORAGE=file`: file local; không dùng lựa chọn này để né lỗi database trênRender.
- `KEYGUARD_DATA_DIR` chỉ áp dụng filebackend và làm namespace tên tương đối cho PG; chế độPG không cần tạo/ghi thư mụcdata/.

Ứng dụng không tạo schema hoặc nhập file tự động lúc khởi động, không copy601mẫu Git vào database mới. Cần init và migration chủ động trước đổibackend. Không inDATABASE_URL vào log hoặc yêu cầu dánURL/mật khẩu trongchat.

## Chạy local bằng Docker Compose

```powershell
docker compose -f compose.storage.yml up -d db
docker compose -f compose.storage.yml build web
docker compose -f compose.storage.yml run --rm web python scripts/storage_admin.py init
docker compose -f compose.storage.yml up -d web
docker compose -f compose.storage.yml port web 8000
```

Cổng localhost được chọn ngẫu nhiên để tránh dải cổng Windows bịreserved; mở cổng vừa in để dùngweb. Password trongcompose là fixturelocal, không dùng production. PostgreSQL local dùngvolume riêng; `docker compose ... stop` chỉ dừng, không xóa dữ liệu. Không chạy down-v nếu muốn giữvolume.

Dockerfile chỉcopy code/modelconfig/UI cầnthiết, không đưa raw,docs/log,backup hoặc.envvào image. Chạy `storage_admin.py status` qua cùngcompose để xem sốđếm, không in tài khoản/profile.

## Nhập bản dữ liệu cũ

Trong môi trường Python córequirements vàDATABASE_URL đã cấu hình an toàn:

```powershell
python scripts/storage_admin.py init
# Mặc định chỉ đọc nguồn, đếm/hash, không ghi database:
python scripts/storage_admin.py import-files --source PATH_TO_PRIVATE_DATA_DIRECTORY
# Chỉ sau khi đối chiếu nguồn, target rỗng và backup:
python scripts/storage_admin.py import-files --source PATH_TO_PRIVATE_DATA_DIRECTORY --apply
```

Nguồn cần thưmục `collected/`, cácJSONaccounts/participants/challenges,profiles/ vàattempts.csv nếu còn. Registryaccount trỏprofile thiếu bị từchối; không nhập một accountđãmấthồsơ rồi gọi làkhôi phục. ZIPexport601mẫu hiệncó chỉ khôi phục được collected,khôngtựtạolạiaccount/profile/logkhôngcótrongZIP.

Nhập mộttransaction vào **targetrỗng**; dữliệu đangcó với nguồnkhác bịtừchối, khôngmerge/ghiđè. Nhập lại cùng nguồn hash trảalready_imported,khôngnhânđôi; không bảođảm tựkhôi phục cácrow bịai xóa sauimport. RawP10khóa trùng được giữcảhaihàng, khôngđánhrep mới hoặc thay protocolnghiêncứu. JSONB giữgiátrị/thứtựhàng, khôngbảo toànbyte/whitespace; rawZIP gốc vẫn phải giữ riêng.

## Hai kiểu export khác nhau

`/admin/export` giữ phạm vi nghiên cứu cũ: collected/participants/attempts, **không tênaccount/profile/challenge**. Lấy từPGnếuđangchạyPG, vẫn kiểmadminheader/keynhưtrước. Không tựkhắcphụcvấnđềkhóaquảntrịđãlộ; thaykhóatrênRenderlàbướcproductionriêng.

Backup đầy đủ chỉ dùng CLI riêng, có dữ liệu nhạy cảm:

```powershell
python scripts/storage_admin.py backup --out LOCAL.private-backup.json
python scripts/storage_admin.py restore --source LOCAL.private-backup.json
python scripts/storage_admin.py restore --source LOCAL.private-backup.json --apply
```

Backup chứaaccounts/profile/challenges vàkhôngđượcpush;filekhôngbịghiđè, patternprivate-backup.jsonđãgitignore. Restore chỉtargetrỗng vàcókiểmtraformat/reference;khôngphảiđườngHTTPadminmới. Filebackupkhôngmãhóatựđộng, cầnlưuởnơitrêng cókiểmsoát/quyềntruycập vàbảovệphùhợp.

## Kiểm thử đã chạy

PostgreSQL17Dockerthật vàLinuxPython3.11,psycopg3.3.9;source mountread-only, dữliệu tổnghợp trongschema testngẫunhiên/loopbackdatabasekeyguard_local. **16testđạt**,khôngskip:

- Register20/accepted21/OTPđúng22; OTPsai/replaykhôngupdate,locked401/401/429cóghi sốlần vàxóachallenge.
- 8requestcấpmã/song song khôngtrùng;8requestsubmitcùngmã córep1–8;đăngkýtrùngsong song200/409khôngoverwrite.
- Log lỗi làmrollbackprofile;updateOTP lỗi khôngmấtchallenge;import lỗi rollbacktoànbatch.
- Account/profile/challengeđangchờ đọcđượcquaPythonprocessmới;HTTPthậtGunicorn2workerrestartvẫnđọcaccount/progress vàxácnhậnOTP→22mẫu.
- Export/statsPG đúngcount/phạmvi;privatebackuprestoretừtargetrỗngkhớp;importgiữduplicates vàidempotent.
- Filebackendvẫnghisample/progressđược;DBkhôngcó/khôngkếtnối khôngghi filefallback.

Đây là kiểmthử lưu trữ/luồngứngdụng,khôngFAR/FRRhoặcngườithật. WindowsdriverbịApplicationControlchặnDLL nên chạy suiteLinuxDocker,khôngtắtchínhsáchbảovệ. KhôngclaimdriverWindowsđãchạyđược. TestrefuseURLkhôngloopback/databasekhác;khôngchochạysuitetrênRender.

## Trước triển khai thật

Đã chọn Neon Free và liên kết project bằng Neon CLI. Chuỗi kết nối nằm trong `.env.local` ignored. Theo yêu cầu tiếp tục, đã tạo schema và nhập 601 mẫu/15 mã lịch sử, đối chiếu hàng/thứ tự và export HTTP khớp; nhập lại không nhân đôi, có backup trước/sau. Năm ca tích hợp trên Neon đạt, gồm HTTP Gunicorn hai worker restart; restore backup 601 mẫu sang schema rỗng khớp. Schema thử đã dọn hết, dữ liệu chính không đổi. Ca ghi dùng direct/TLS, pooled mới kiểm đọc. ZIP không có tài khoản/profile/log nên không tự tái tạo các phần đó. Trước chuyển dịch vụ cần đối chiếu nguồn mới nhất từ Render và chốt chính sách backup. Chưa đổi ENV/khóa hoặc deploy Render. `.env.local` không tự được Flask/Gunicorn nạp; xem kế hoạch chuyển để biết cách đưa biến vào process. DB bên ngoài không tự bảo đảm dữ liệu tồn tại vĩnh viễn.
