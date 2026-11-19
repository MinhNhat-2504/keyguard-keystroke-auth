# Phân bố điểm CV của p013 và độ nhạy chuẩn hóa

## Nghiên cứu và cải tiến mô hình liên hệ thế nào?

Hướng hiện tại là **nghiên cứu cải tiến pipeline mô hình**: đã thay cách gán trọng số cho mẫu, học tâm/độ phân tán hồ sơ và chuẩn hóa điểm. Họ detector vẫn là Scaled Manhattan; chưa thay bằng một thuật toán phân loại mới. Việc chẩn đoán CV lần này là tìm cơ sở cho lựa chọn tiếp theo, bản thân nó chưa tạo cải tiến hoặc chứng minh FAR/FRR tốt hơn.

Đổi họ thuật toán và nghiên cứu phương pháp là hai khía cạnh khác nhau. Có thể cải tiến mô hình trong cùng họ bằng một thay đổi có kiểm soát; cần đánh giá lợi ích và đánh đổi trên cùng giao thức, thay vì đổi tên thuật toán rồi suy là tốt hơn.

## Dữ liệu và cách kiểm tra

Tái dựng đúng50 mẫu cuối S1 của p013 tại đầu S2,47 đặc trưng, cùng core đã đóng băng. Năm khối held-out liên tiếp, mỗi khối10 mẫu, học bằng40 mẫu còn lại. Window dùng trọng số đều; decay dùng trọng số tuổi như trước, giới hạn vào các vị trí train. Cả50 điểm giữ ra đều được tổng hợp **không trọng số** bằng mean và SD population (`ddof=0`). Không dùng S2 để tính hoặc chọn chuẩn hóa.

CV này dùng các mẫu ở hai phía của khối giữ ra **trong lịch sử S1 đã có**, không phải kiểm định cuốn chiếu theo thời gian. “Cũ/mới” trong hình là vị trí trong50 mẫu lịch sử; không suy thành khác ngày hoặc thiết bị. Không có dữ liệu S2 tương lai tham gia hồ sơ checkpoint này.

## Phân bố tổng thể

| Thống kê của50 điểm CV | Window50 | Decay20 |
|---|---:|---:|
| Mean |54,3783|61,2316|
| SD population |21,7840|27,8382|
| Median |46,9332|54,5510|
| Q25 |38,2514|40,9960|
| Q75 |67,1847|74,9834|
| Min–max |26,1137–130,5759|22,5120–155,6908|

Mean tăng6,8533, median cũng tăng7,6178; vì vậy không chỉ có thay đổi của một điểm lớn nhất. Mean cao hơn median ở cả hai nhánh; không áp giả định phân phối chuẩn hoặc tự gắn nhãn mẫu sai từ các thống kê này.

![Phân bố CV và độ nhạy tổng hợp điểm](../figures/research/p013_cv_diagnostics.png)

Hình có bản SVG cùng tên. Thanh SD mô tả độ phân tán điểm, không phải sai số chuẩn hoặc khoảng tin cậy.

## Thay đổi tập trung ở đâu?

| Khối giữ ra, từ cũ đến mới | Mean window | Mean decay | Δmean của khối | Đóng góp vào Δmean toàn bộ |
|---|---:|---:|---:|---:|
|1: vị trí1–10|55,8093|65,0984|+9,2891|+1,8578|
|2: vị trí11–20|60,3622|75,2219|+14,8598|+2,9720|
|3: vị trí21–30|62,7269|74,6386|+11,9118|+2,3824|
|4: vị trí31–40|47,3705|47,6361|+0,2655|+0,0531|
|5: vị trí41–50|45,6227|43,5630|−2,0598|−0,4120|

Ba khối cũ hơn đóng góp khoảng+7,2121 vào thay đổi mean; hai khối cuối bù khoảng−0,3588, tổng+6,8533. Mô hình train ưu tiên mẫu mới hơn nhưng việc tổng hợp50 điểm CV vẫn coi các điểm cũ/mới ngang nhau. Đây là một đầu mối về sự tương tác giữa trọng số detector và cách chuẩn hóa, chưa chứng minh một cách tổng hợp khác sẽ tốt hơn.

Phương sai giữa mean các khối tăng46,6644→177,4899; phương sai trong khối trung bình tăng427,8793→597,4745. Tổng hai thành phần khớp phương sai toàn bộ. Đây là phân rã số học trên năm khối bằng nhau, không phải ANOVA kiểm định hoặc bằng chứng nhân quả.

## Độ nhạy của bước tổng hợp điểm

Giữ nguyên50 điểm CV đã tính, lần lượt bỏ10 **điểm khỏi phép tổng hợp để chẩn đoán**; không bỏ mẫu raw, không fit lại fold, không dùng bộ chuẩn hóa40 điểm này để quyết định nhận/từ chối.

- Mean của40 điểm còn lại ở window nằm52,2912–56,5672, độ rộng4,2760.
- Ở decay nằm57,7340–65,6487, độ rộng7,9147.

Trong phép kiểm tra cụ thể này, mean của decay biến thiên nhiều hơn theo khối điểm được tính vào tổng hợp. Khoảng này không phải CI, không dùng chọn khối cần bỏ, không chứng minh sự bất ổn trên quần thể hoặc qua ngày. Kết quả xác thực cũ không thay đổi.

## Liên hệ với các nhận nhầm đã quan sát

Ở mỗi nhánh, ranh giới tương đương trong điểm detector riêng là `c + τs`:

- Window: `54,3783 + (−0,3582252078)×21,7840 = 46,5747`.
- Decay: `61,2316 + (−0,3549230950)×27,8382 = 51,3512`.

Hai τ **giữ nguyên** từ lần chạy trước. Ranh giới tăng4,7765 nhưng detector cũng đổi tâm/MAD, nên không coi đây là một ngưỡng raw chung hoặc suy mọi probe đều dễ nhận hơn. Với ba probe nhận nhầm mới của p017→p013 đã chẩn đoán riêng, điểm detector tăng nhưng thay đổi chuẩn hóa vẫn đưa margin qua0. Kết quả này nhất quán với phân bố CV tăng ở trên; không quy nguyên nhân cho người/thiết bị.

## Trạng thái và bước cải tiến có thể nghiên cứu

Đã đủ cơ sở để đặt câu hỏi hẹp tiếp theo: cách tổng hợp điểm CV có cần phù hợp hơn với trọng số tuổi của detector hay không? Phép đối chứng sau nên **giữ detector decay, lịch chấm và nguồn dữ liệu giống nhau, chỉ đổi một quy tắc tổng hợp CV đã định trước**. Đây vẫn là cải tiến một thành phần của pipeline mô hình. Chưa chọn hoặc thử một chuẩn hóa mới trong lượt này; không đặt quy tắc riêng theo p013.

`scripts/diagnose_p013_cv.py` tạo JSON, hình và điểm CV localignore. `results/p013_cv_diagnostics.json` ghi fold/thống kê/độ nhạy và hash; `results/p013_cv_diagnostic_checks.json` đối chiếu50 điểm/5khối, chuẩn hóa khớp checkpoint cũ và hash đầu vào. **4 test giả lập đạt**, gồm tương đương core31/47chiều, train không có held-row, trọng số tuổi đúng vị trí, phép bỏ khối chỉ là tổng hợp và sàn số học. Không nhận đã chạy toàn suite.

Điểm từng mẫu ở `report/preview/p013-cv-scores.csv` được gitignore. Frozen code/protocol, ngưỡng, raw/config/kết quả cũ và hai bộ báo cáo Word/PDF giữ nguyên. Chưa cập nhật báo cáo/explorer hoặc push; điểm rubric không đổi. Đây là phân tích sau khi xem kết quả, không phải bằng chứng xác nhận từ dữ liệu mới.
