# Kiểm chứng shrink25 trên GREYC-Web — 15/11/2026

Protocol lợi/hại được khóa trước khi tải/audit nguồn mới; adapter và code được khóa sau kiểm thử, trước scoring. Nguồn này chưa được dùng phát triển quy tắc trong dự án. Không phải đăng ký trước công khai hoặc bằng chứng triển khai.

## Dữ liệu và phạm vi

- Nguồn tác giả: https://www.labri.fr/perso/rgiot/resources/webgreycdb/ ; Giot, El-Abed, Rosenberger, IIHMSP 2012. SQLite GREYC2009 bị403 nên dùng archiveGREYC-Web, không gọi hai bộ là một.
- Archive thực tế có 10656 thư mục capture common-password được audit; 8148 hợp lệ theo adapter, 2508 bị loại do độ dài vector hoặc giá trị không hữu hạn. Số bản phát hành này khác số mô tả trên trang; không tự ép khớp số liệu lịch sử.
- 63 mã đủ điều kiện: 42 DEV/21 TEST; 54 mã có capture hợp lệ nhưng thiếu enrollment20 hoặc test10 ở ngày muộn hơn.
- Chỉ password chung sésame, 21 timing nguồn PP/PR/RP/RR, không dùng thông tin nhân khẩu, login hay mật khẩu riêng. Không mặc định PR/RP nguồn là hold-time cùng phím.
- Enrollment20 có thể trải qua nhiều ngày; test chỉ ngày lịch muộn hơn enrollment. Không kiểm soát thiết bị/browser; không gọi đây là sao chép nguyên protocol CMU/KeyRecs.
- Các loại bỏ do schema xảy ra trước scoring; tỷ lệ loại lớn có thể gây thiên lệch độ bao phủ. Kết luận chỉ áp dụng tập đã qua điều kiện, không áp cho mọi người trong nguồn.

## Kết quả toàn tập

| Nhánh | FAR macro | FRR macro | FRR pooled | Nhận nhầm | Genuine bị từ chối |
|---|---:|---:|---:|---:|---:|
|baseline|2,24%|78,06%|80,55%|94/4200|2141/2658|
|shrink25|2,33%|78,34%|81,26%|98/4200|2160/2658|

ΔFAR macro **+0,0952 đpt**, ΔFRR macro **+0,2768 đpt**. 'đpt' là điểm phần trăm, không phải phần trăm thay đổi tương đối.
Tiêu chí toàn tập đạt: **False**. Tuyên bố lợi ích đa số đạt: **False**.

## Lợi/hại theo tài khoản

**3/21** mã giảm FRR mà FAR không tăng; **10/21** có ít nhất một loại lỗi tăng. Không coi hòa là được lợi. Hai nhóm không bao phủ hết: còn các mã hòa hoặc chỉ giảm FAR.

| ΔFAR \ ΔFRR | Giảm | Không đổi | Tăng |
|---|---:|---:|---:|
|Giảm|0|2|3|
|Không đổi|3|6|4|
|Tăng|2|1|0|

| Mã đích | ΔFAR (đpt) | ΔFRR (đpt) | Giảm FRR, FAR không tăng |
|---|---:|---:|---|
|user_003|+0,0000|+0,0000|Không|
|user_006|+0,0000|+0,6309|Không|
|user_013|+0,0000|-2,1505|Có|
|user_020|+0,0000|+0,0000|Không|
|user_023|-2,5000|+0,0000|Không|
|user_028|-0,5000|+5,7471|Không|
|user_032|+0,5000|+0,0000|Không|
|user_035|+0,0000|+0,0000|Không|
|user_040|+2,0000|-4,0000|Không|
|user_045|+0,0000|+0,0000|Không|
|user_049|+0,0000|+1,8237|Không|
|user_054|+0,0000|-4,0404|Có|
|user_059|-0,5000|+5,2632|Không|
|user_064|+0,0000|+0,0000|Không|
|user_068|+0,0000|+0,0000|Không|
|user_077|+0,0000|+5,4545|Không|
|user_085|+0,0000|+2,0833|Không|
|user_096|-1,0000|+0,0000|Không|
|user_105|-1,0000|+3,3333|Không|
|user_114|+0,0000|-3,3333|Có|
|user_118|+5,0000|-5,0000|Không|

Phân bố hiệu số theo tài khoản (đpt, nearest-rank; không phải khoảng tin cậy):

| Chỉ số | Min | Q25 | Median | Q75 | Max |
|---|---:|---:|---:|---:|---:|
|FAR|-2,5000|+0,0000|+0,0000|+0,0000|+5,0000|
|FRR|-5,0000|+0,0000|+0,0000|+1,8237|+5,7471|

## Kết luận và giới hạn

- Cả FAR và FRR macro tăng; shrink25 không đạt tiêu chí định trước. Không thay baseline, dò lại λ, bỏ mã bất lợi hoặc điều chỉnh ngưỡng sau kết quả.
- Baseline FRR cũng cao trong protocol này. Chưa có bằng chứng phương pháp phù hợp sử dụng thực tế ở mức FAR đã chọn; không suy diễn từ FAR thấp sang độ tin cậy chung.
- Kết quả nguồn mới củng cố việc chưa chấp nhận shrink25 trong những điều kiện đã kiểm; không bác bỏ mọi shrinkage hoặc chứng minh kém hơn ở mọi quần thể.
- Sau lượt chạy này GREYC-Web đã được xem. Mọi thay đổi dựa trên kết quả này là phát triển; chạy lại cùng nguồn không phải kiểm chứng mới.
- Không CI/p-value, không giả định mọi lượt impostor độc lập. Định nghĩa account là tài khoản đích, không bảo đảm danh tính không trùng giữa các nguồn.
- Raw/derived timing nằm trong thư mục ignored, không phân phối lại. Báo cáo6/37/40trang, mô hình sản phẩm và các kết quả cũ giữ nguyên.

## Tái lập/đối chiếu

`python scripts/run_greyc_web_account_benefit.py --check` và `python scripts/validate_greyc_web_account_benefit.py` không tính lại điểm. Runner từ chối ghi đè started/results bằng --run. Môi trường/raw/code phải khớp freeze.

Artifact: `results/greyc_web_account_benefit_results.json`, `accounts.csv`, `account_deltas.csv`, `freeze.json`, `synthetic_tests.json` cùng prefix. JSON chứa bảng dấu3×3, quantile nearest-rank và toàn bộ tài khoản; CSV giữ phân số và số đếm.
