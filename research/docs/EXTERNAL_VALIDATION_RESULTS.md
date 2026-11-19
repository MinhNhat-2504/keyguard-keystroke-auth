# Kết quả kiểm chứng nguồn ngoài KeyRecs — 13/11/2026

Đã tiếp tục task kiểm chứng trên dữ liệu chưa dùng phát triển quy tắc của dự án. Chọn **KeyRecs fixed-text v1.0.0**, một nguồn khác CMU và bộ nhóm tự thu. Không chọn lại nguồn,seed,feature hoặc phương án sau khi thấy kết quả. Bản kế hoạch trước chấm ở [EXTERNAL_VALIDATION_PROTOCOL.md](EXTERNAL_VALIDATION_PROTOCOL.md) giữ nguyên hash; tài liệu này tách riêng kết quả sau chấm.

## Nguồn và điều kiện sử dụng

Dias,T., Vitorino,J., Maia,E., Sousa,O., Praça,I. (2023), *KeyRecs: A keystroke dynamics and typing pattern recognition dataset*, Data in Brief50,109509, [DOI10.1016/j.dib.2023.109509](https://doi.org/10.1016/j.dib.2023.109509). Dữ liệu [Zenodo7886743](https://zenodo.org/records/7886743), DOI10.5281/zenodo.7886743; metadata chính thức khai **[CC BY4.0](https://creativecommons.org/licenses/by/4.0/)** và yêu cầu trích dẫn bài dữ liệu. Attribution được ghi ở báo cáo/trang khám phá/manifest.

Chỉ tải `fixed-text.csv` (5.676.298 byte), **không tải demographics/free-text**. Raw giữ nguyên trong `data/raw/keyrecs/` đã ignore, không đưa raw lên GitHub trong lượt này. MD5 công bố **f3c2ef3a42625f4df7183ea36d4543db** khớp; SHA-256 lưu trong freeze/manifest. Để tái lập, `scripts/download_keyrecs.py` xác minh checksum và từ chối ghi đè file khác phiên bản.

Audit trước chấm: **19.772 dòng dữ liệu**,99 mã,phiên1 có9.878 dòng/phiên2 có9.894. Đếm cả header là19.773 dòng; không tự thêm mẫu để khớp mô tả nguồn. Không có khóa participant/session/repetition trùng hoặc timing không hữu hạn;99 mã đều có≥25 mẫu phiên1 và≥10 phiên2. Số mẫu mỗi phiên không đồng đều, giữ hết các mẫu hợp lệ theo protocol.

Vector **47 chiều =46 cột digraph + total time**. Tên `DU.k.k` xuất hiện hai vị trí; adapter giữ cả hai, tên canonical lần2 là `DU.k.k__occ2`. Không dùng ID/phiên/rep làm predictor. Câu gõ và schema khác CMU31; kiểm chứng **quy trình học/chọn ngưỡng**, không chuyển nguyên profile hoặc tau CMU. Không cắt ngoại lệ thời gian hữu hạn sau khi xem kết quả.

## Đóng băng và cách chia

Manifest `results/external_validation_freeze.json` được ghi **trước lần chấm mô hình đầu**, hash:

`be80e8833994e388d27a814aa4e525a7bf29cef09308ed5286caa7c3e4e9288a`

Gồm SHA raw,protocol,code evaluator và các module phụ thuộc; timestamp bắt đầu đánh giá ở `external_evaluation_started.json` muộn hơn freeze. Đây là **đóng băng nội bộ có truy vết**, không phải đăng ký trước công khai hoặc đánh giá bởi nhóm nghiên cứu độc lập.

- Seed42 duy nhất,66 mã dev/33 test,cả hai vai trò target/impostor chỉ lấy trong cùng phân vùng. Không đổi seed hoặc thêm nhiều cách chia để chọn kết quả đẹp.
- 20 mẫu đầu phiên1 tạo hồ sơ. Chỉ dev phiên1 dùng chọn ngưỡng và chuẩn hóa/quality rule qua2 vòng mã trong dev; không dùng phiên2 của dev để chọn.
- Test là toàn bộ genuine phiên2 của33 mã; impostor là5 đầu+5 cuối phiên2 của32 mã khác trong test. **3.301 genuine/10.560 impostor**. Mẫu enrollment của test dùng xây hồ sơ của chính tài khoản, không chọn quy tắc/ngưỡng chung.
- Giữ nguyên9 phương án và4 quy trình baseline/hard/soft/all. Ngưỡng mỗi phương án từ dev FAR≤5%,tie-aware. Chọn phương án theo BER/tie-break tên chỉ trong dev, không chọn từ outer-table.

Đã tái chạy với **`--reproduce`** và đối chiếu đối tượng kết quả khớp bản đầu,không thay kết quả gốc. Lần này chỉ kiểm tra tái lập xác định, không gọi là lượt kiểm chứng mới.

## Kết quả cố định hồ sơ

EER/AUC là trung bình theo33 tài khoản test; FAR/FRR cộng tử số/mẫu số toàn test. Không so trực tiếp macro EER này với mean-fold pooled EER của nghiên cứu trước.

| Quy trình | Phương án dev chọn | FAR | FRR | Macro EER | Macro AUC |
|---|---|---:|---:|---:|---:|
| Baseline | Giữ mẫu/Mean-Std |909/10.560=8,61%|2.450/3.301=74,22%|26,12%|0,783|
| Hard-selected | Lọc cứng/Mean-Std |1.052/10.560=9,96%|2.286/3.301=69,25%|25,44%|0,793|
| Soft-selected | Trọng số mềm/Mean-Std |904/10.560=8,56%|2.443/3.301=74,01%|25,76%|0,787|
| All-selected | Lọc cứng/Mean-Std |1.052/10.560=9,96%|2.286/3.301=69,25%|25,44%|0,793|

**Mềm giảm5 nhận nhầm và7 genuine cần xác minh**, tương ứng−0,047 và−0,212 điểm phần trăm so baseline. EER/AUC cũng nhích thuận lợi. Tuy vậy,chênh nhỏ vàFRR vẫn khoảng74%; **không có bằng chứng độ chắc chắn thống kê hay hiệu quả thực tế đủ mạnh để tuyên bố thắng toàn diện**. Không thêm CI/p-value giả định các lượt độc lập để làm mức cải thiện trông chắc chắn hơn.

Lọc cứng giảm164 genuine cần xác minh nhưng tăng143 nhận nhầm; kết quả này vẫn được giữ. Toàn bộ9 phương án,chi tiết từng tài khoản và bảng source ngoài đều được xuất,không chọn phương án theo test.

## Thích nghi trên KeyRecs

Giữ static/window50/decay20 từ code trước. Dev threshold chỉ dùng probe phiên1 ngay sau20 enrollment; không dùng phiên2dev. Với test,window/decay warm-up bằng genuine còn lại phiên1,sau đó chấm trước–cập nhật sau ở phiên2. Mọi genuine giả định có xác minh độc lập;probe phiên2 chỉ chấm ở đầu phiên2 và không cập nhật. Chu kỳ bán rã20 lượt/cửa sổ50 không được tune trên nguồn mới.

| Phương pháp | FAR probe đầu phiên2 | FRR genuine tuần tự phiên2 |
|---|---:|---:|
| Static |909/10.560=8,61%|2.450/3.301=74,22%|
| Window50 |439/10.560=4,16%|1.840/3.301=55,74%|
| Decay20 |451/10.560=4,27%|1.609/3.301=48,74%|

Static khớp đúng baseline cố định,có kiểm tra trong evaluator. **Decay giảm231 genuine cần xác minh nhưng tăng12 nhận nhầm so window đều**. Lợi thế đồng thời FAR/FRR trên CMU không lặp lại trên nguồn này. Không dùng kết quả này làm bảo đảm về OTP,chống nhiễm hồ sơ hoặc cùng hiệu quả ở bộ tự thu. Không gộp với lịch checkpoint8 phiên CMU để tính một FAR tổng.

## Artifact và tái lập

```powershell
./.venv/Scripts/python.exe scripts/download_keyrecs.py
# Bản freeze đã có: chỉ xác minh nó, không sửa/khóa lại sau khi xem test.
./.venv/Scripts/python.exe scripts/prepare_external_validation.py
./.venv/Scripts/python.exe scripts/run_external_validation.py --reproduce
./.venv/Scripts/python.exe scripts/plot_external_validation.py
./.venv/Scripts/python.exe scripts/validate_external_validation.py
```

Evaluator mặc định từ chối chạy nếu kết quả đã tồn tại; `--reproduce` chỉ cho cùng hash và phải khớp bản đầu. Nếu phát hiện lỗi hoặc muốn phát triển quy tắc khác, giữ nguyên bản freeze/kết quả này và ghi nhánh nghiên cứu tiếp,không âm thầm ghi đè protocol. Sau lượt này KeyRecs đã được dự án xem,không gọi các chỉnh sửa tiếp trên nó là kiểm chứng mới chưa dùng.

- `data/keyrecs_manifest.json`: nguồn,license,credit,checksum và mô tả adapter.
- `results/external_validation_freeze.json`, `external_evaluation_started.json`: kế hoạch/code hash và thứ tự thời gian.
- `results/external_validation.json`: kết quả4 quy trình/9 phương án/3 cách thích nghi.
- `external_comparison.csv`:9 dòng; `external_account_errors.csv`:297 dòng; `external_adaptation.csv`:99 dòng.
- `results/external_validation_checks.json`: đối chiếu schema,phân vùng,tổng số đếm,CSV/JS/provenance và môi trường chạy.
- Explorer mục09: chọn quy trình/tài khoản để xem kết quả; nguồn/citation và hash đóng băng hiển thị rõ.

**50 test liên quan đạt,4 subtest**, gồm5 test adapter/split/dev không đọc phiên2 và không giả định31 chiều. Chrome đối chiếu132 chi tiết tài khoản–quy trình ngoài các mục cũ,mobile390px không tràn. Raw/config và các artifact nghiên cứu cũ không đổi; chưa làm task Thư,tích hợp liveb23 hoặc push GitHub.

**Kết luận:** đã có kiểm chứng nguồn ngoài với phương pháp đóng băng; lợi ích mềm rất nhỏ và kết quả thích nghi vẫn có đánh đổi. Nên viết kết luận về giới hạn chuyển miền theo đúng bằng chứng,không thêm quy tắc để khớp KeyRecs rồi tiếp tục gọi nó là test mới.
