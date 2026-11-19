# Chẩn đoán các cặp tăng FAR trên KeyRecs

Kết luận: mức tăng ròng **12 nhận nhầm** đến từ nhiều thay đổi quyết định theo cặp; không có một cơ chế đồng nhất cho mọi cặp. Đã tái dựng đúng hồ sơ đầu phiên2 và đối chiếu đủ1.056 cặp/10.560 probe ở hai ngưỡng đã khóa. **Không chọn lại ngưỡng, sửa mô hình hoặc chạy lại chuỗi genuine.** Đây là chẩn đoán mô tả sau khi đã xem kết quả, không phải kiểm chứng mới.

## 1. Cặp tăng/giảm và từng lượt đổi quyết định

| Quyết định trên cùng probe | Số lượt |
|---|---:|
| Window từ chối, decay nhận: nhận nhầm mới |50|
| Window nhận, decay từ chối: thu hồi nhận nhầm |38|
| Cả hai cùng nhận |401|
| Cả hai cùng từ chối |10.071|

Tổng nhận nhầm window là401+38=439; decay là401+50=451; chênh ròng **50−38=12**, tương ứng FAR4,1572%→4,2708%. Có37 cặp tăng số nhận nhầm,30 cặp giảm và989 cặp giữ nguyên. Tổng tăng ròng trong các cặp tăng là48, tổng giảm trong các cặp giảm là36; không nhầm các số này với50/38 lượt đổi quyết định.

Hai cặp p088→p036 và p014→p045 giữ nguyên số nhận nhầm nhưng mỗi cặp có1 nhận nhầm mới và1 lượt được thu hồi. Vì vậy chỉ nhìn số đếm theo cặp sẽ bỏ sót thay đổi ở từng probe.

Trong tài liệu này, **nguồn → đích** nghĩa là mã nguồn gõ thử vào hồ sơ tài khoản đích; đây là cặp có hướng, không suy vai trò ngược lại tương đương. Mỗi cặp có10 probe,5 đầu+5 cuối phiên2.

## 2. Các cặp tăng nhiều nhất

| Nguồn → đích | Window nhận /10 | Decay nhận /10 | Tăng ròng |
|---|---:|---:|---:|
| p032 → p009 |2|5|+3|
| p017 → p013 |2|5|+3|
| p065 → p009 |1|3|+2|
| p088 → p009 |1|3|+2|
| p007 → p015 |2|4|+2|
| p031 → p015 |5|7|+2|
| p032 → p015 |4|6|+2|
| p088 → p015 |3|5|+2|
| p045 → p065 |4|6|+2|

Đây là toàn bộ9 cặp có tăng ròng ít nhất2; các cặp khác tăng1. Chẩn đoán vẫn lưu đủ1.056 cặp, không chỉ chọn ca xấu. Xét tài khoản đích: p015 tăng59→72 (+13), p009 tăng23→31 (+8); phần tăng này được bù một phần bởi các tài khoản giảm FAR nên toàn nguồn chỉ tăng12. Không diễn giải p015 đóng góp13/12 như một tỷ lệ phần trăm nguyên nhân.

## 3. Vì sao các probe đổi quyết định?

Giữ nguyên `τ_window = −0,3582252078262172` và `τ_decay = −0,35492309501165314`. Với điểm detector r, trung bình/độ lệch chuẩn điểm CV là c/s, định nghĩa margin `m=(r−c)/s−τ`. Margin≤0 được nhận. Margin không phải xác suất danh tính.

Để giải thích phép tính, dùng phân rã theo thứ tự cố định:

`m_decay − m_window = (r_decay−r_window)/s_window`

`+ (c_window−c_decay)/s_window`

`+ (r_decay−c_decay)×(1/s_decay−1/s_window)`

`+ (τ_window−τ_decay)`

Bốn số hạng lần lượt được gọi là detector, tâm CV, scale CV và ngưỡng. Đây là **đồng nhất thức đại số có phụ thuộc thứ tự**, không phải ước lượng nhân quả hoặc bốn thành phần độc lập. Không fit/nghiệm thu một phương pháp dùng các tổ hợp trung gian này.

Trung bình chỉ trên50 probe nhận nhầm mới:

| Thành phần | Thay đổi margin trung bình |
|---|---:|
| Detector ở scale window |−0,05758|
| Tâm điểm CV |−0,05665|
| Scale điểm CV |+0,00966|
| Hai ngưỡng vốn đã khóa |−0,00330|
| Tổng thay đổi |−0,10787|

Margin trung bình chuyển từ+0,05478 sang−0,05309. Số hạng âm hướng về nhận; số hạng dương hướng về từ chối trong phân rã này. Các trung bình có điều kiện trên nhóm đổi quyết định, không mô tả toàn bộ10.560 probe, không chứng minh điều chỉnh một thành phần riêng sẽ sửa FAR.

### Cặp p032 → p009: điểm detector giảm

Ba nhận nhầm mới có margin trung bình **+0,09791 → −0,10792**. Số hạng detector−0,18681, tâm CV+0,01953, scale−0,03525, ngưỡng−0,00330. Điểm detector trước chuẩn hóa CV giảm; thay đổi tâm CV chống lại một phần, nhưng tổng margin vẫn qua0. Đây là mô tả phép tính tại đúng hồ sơ/probe này.

### Cặp p017 → p013: chuẩn hóa CV đưa điểm qua ngưỡng

Ba nhận nhầm mới có margin trung bình **+0,09938 → −0,05116**. Số hạng detector **+0,05451**: điểm detector trước chuẩn hóa CV thực tế tăng. Tâm CV đổi54,3783→61,2316 tạo số hạng **−0,31460**; scale đổi21,7840→27,8382 tạo+0,11286; ngưỡng−0,00330. Tổng vẫn âm đủ để qua ngưỡng.

Cặp này cho thấy không thể giải thích mọi nhận nhầm mới bằng “hồ sơ giảm trọng số tuổi làm điểm khoảng cách thấp hơn”. Việc chuẩn hóa điểm CV cũng thay đổi cùng pipeline. Chưa kết luận tâm CV mới sai hoặc thiết bị là nguyên nhân.

## 4. Đặc trưng và trạng thái hồ sơ

Trên50 nhận nhầm mới, tổng thay đổi đóng góp từng chiều vào số hạng detector khớp−0,05758. Theo nhóm, DU−0,02735, UU−0,01292, UD−0,00946, DD−0,00829 và total time+0,00044. Các chiều giảm mạnh theo trung bình gồm DU.b.b, DD.k.b, DU.k.b, DU.j.j và DU.u.u. Không coi tổng đóng góp khoảng cách là xác suất/nguyên nhân hoặc bằng chứng cần bỏ các đặc trưng đó. Vị trí DU.k.k trùng tên trong raw vẫn giữ hai cột canonical riêng.

Mỗi hồ sơ checkpoint dùng đúng50 mẫu cuối S1; mọi probe chỉ đọc trạng thái đó. Trọng số đều có cỡ mẫu hiệu dụng50, decay khoảng40,374; đây là mô tả trọng số, không phải thêm/bớt người. Không chiều nào ở66 hồ sơ detector chạm sàn MAD1e−9; scale CV nhỏ nhất khoảng15,406, không chạm sàn1e−6. Chưa thấy hiện tượng chạm sàn giải thích lỗi trong checkpoint này; không suy loại trừ mọi lỗi số học khác hoặc chứng minh các mẫu S1 là sạch.

## 5. Kiểm tra, bảo toàn và giới hạn

- `scripts/diagnose_matched_pairs.py` chỉ dựng lại checkpoint từ S1, chấm probe S2 tại các ngưỡng cũ và đối chiếu từng cặp với kết quả đã khóa. Không gọi bộ chọn ngưỡng hoặc evaluator `--run` lần nữa.
- `results/matched_pair_diagnostics.json/.csv`: đủ cặp, số đếm chuyển quyết định, tổng hợp theo đích, trạng thái CV và đóng góp đặc trưng. `matched_pair_diagnostic_cases.json`: mọi37 cặp tăng ròng và phân rã trung bình của probe nhận nhầm mới.
- Điểm từng probe và vector tham số hồ sơ nằm **local/ignore** trong `report/preview/matched-pair-probe-scores.csv` và `matched-pair-checkpoint-profiles.json`, không đưa vào gói công khai.
- **5 test giả lập đạt** cho phân rã, ranh giới bằng ngưỡng, thứ tự probe, tái dựng checkpoint khớp core và dừng nếu số đếm tham chiếu sai. Không cộng với các bộ test lịch sử để nhận đã chạy toàn suite.
- `scripts/validate_matched_pair_diagnostics.py` đạt, log `results/matched_pair_diagnostic_checks.json`: đủ1.056cặp/10.560probe, ngưỡng/quyết định, số đếm/case CSV, phân rã và hash. Không fit lại mô hình trong validator.
- Code/protocol đã đóng băng, kết quả matched gốc, raw/config, kết quả lịch sử và hai bộ Word/PDF nguyên hash; không sửa báo cáo/trang khám phá, điểm rubric hoặc push trong lượt này.

Ưu tiên nghiên cứu tiếp là kiểm tra phân bố điểm CV của hồ sơ S1 ở các trường hợp như p013 để hiểu độ nhạy chuẩn hóa khi đổi trọng số tuổi. Chẩn đoán hiện tại chưa đủ để chọn quy tắc chuẩn hóa hay ngưỡng mới; mọi cải tiến cần một kế hoạch riêng và kiểm chứng tiếp trên dữ liệu chưa dùng phát triển.
