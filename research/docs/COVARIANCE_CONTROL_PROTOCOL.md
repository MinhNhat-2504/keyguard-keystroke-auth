# Đối chứng mô hình: tương quan giữa các timing — 15/11/2026

## Động lực và câu hỏi hẹp

Audit cho thấy các timing PP/PR/RP/RR có quan hệ đại số và dùng chung timestamp. Chỉ biết điều đó chưa chứng minh chúng gây FRR cao. Thử một câu hỏi hẹp: **giữ cùng tâm, độ lệch từng chiều, quy tắc fit và chuẩn hóa điểm; giữ hoặc bỏ các phần tử ngoài đường chéo của cùng ma trận covariance co rút có làm giảm FRR macro mà FAR macro không tăng không?**

Đây là mô hình khoảng cách mới trong dự án, không thử thêm λ của shrink25 hay công thức phân vị. Tìm kiếm source hiện có không thấy Mahalanobis/LedoitWolf đã triển khai. Đối chứng chính là full-covariance với diagonal-covariance, không gọi diagonal này là Scaled Manhattan sản phẩm.

## Ba nhánh cố định, không search

1. `diag_lw`: tâm mean và scale MAD từng chiều từ đúng phần training; chuẩn hóa residual `(X−mean)/max(MAD,1e−9)`. Fit `LedoitWolf(assume_centered=True, store_precision=False)` của scikit-learn trên residual. Giữ đúng diagonal của covariance đó, thêm ridge `1e−9*I`, score = căn bậc hai khoảng cách Mahalanobis bình phương.
2. `full_lw`: dùng **chính covariance LedoitWolf trên cùng residual training**, giữ cả off-diagonal; cùng ridge và score căn Mahalanobis. Trọng số shrinkage do estimator tính từ dữ liệu training, không tối ưu theo genuine/impostor hay evaluation. Hai nhánh dùng cùng mean/MAD/covariance fit; khác duy nhất việc giữ phần tử ngoài đường chéo.
3. `scaled_manhattan`: nhánh tham chiếu sản phẩm tĩnh, cùng mean/MAD, tổng residual tuyệt đối. Chỉ báo cáo mô tả; không đưa nhánh này vào quy tắc chọn phương pháp để né tiêu chí chính.

Mỗi profile full fit20enrollment. OOF5fold liên tiếp, mỗi fold fit16 gồm cả mean/MAD/covariance; điểm giữ ra không tham gia fit. Chuẩn hóa mean/populationSD OOF, floor1e−6, riêng mỗi nhánh. Không PCA, không bỏ feature, không đổi raw/ghép lại event, không update/warmup. Thử nghiệm đo tác động off-diagonal trong toàn pipeline gồm score/CV/calibration; không tách thành tác động nhân quả của tương quan lên lỗi.

## Tách phát triển và kiểm chứng

**Giai đoạn A — DEV phát triển:** chỉ projection42DEV GREYC đã xem. Giữ split28calibration/14evaluation như đối chứngDEV trước, không thử seed khác. Calibration: first5+last5enrollment của các mã calibration khác; chọn ngưỡng riêng từng nhánh với FAR≤5%, accept khi score≤tau, giữ ties. Evaluation: mọi genuine ngày sau của14mã vàfirst5+last5ngàysau của13mã evaluation khác. Không dùng ngày sau calibration hoặc probeevaluation để chọn ngưỡng. Không chạm21TESTcũ;14evaluationDEV đã xem không phải holdout mới.

Tiêu chí chính candidate(full_lw)−control(diag_lw): **ΔmacroFRR<0 và ΔmacroFAR≤0**. Tuyên bố lợi đa số chỉ nếu tiêu chí chính đạt và hơn7/14mã giảmFRR/FARkhôngtăng. Báo đủ counts/macro/pooled,3×3/quantile,tham sốshrinkage/rank/conditioning mô tả. Không CI/p-value từ lượt impostor phụ thuộc.

**Cổng chuyển sang B:** chỉ đi tiếp tìm/khóa nguồn kiểm chứng nếu đồng thời đạt tiêu chí chính và lợi đa số trên A. Nếu không đạt, dừng candidate ở nghiên cứu phát triển, giữ kết quả bất lợi; không thử estimator/ridge/feature/split/ngưỡng khác để cứu kết quả. Cổng này là lựa chọn kế hoạch nghiên cứu, không kiểm định thống kê.

**Giai đoạn B — nguồn ngoài chưa phát triển:** CMU, KeyRecs, GREYC và bộ tự thu đều đã xem, không dùng lại để gọi test mới. Phải xác minh điều kiện sử dụng/schema, nguồn cùng fixed-text đủ20enrollment và≥10probe ngày/phiên muộn hơn, split2DEV/1TESTtheoID, tối thiểu10DEV/5TEST. Trước scoring ghi bổ sung adapter/split/rawhash và giữ nguyên3nhánh/tiêu chí. Fit parameters vàthreshold chỉDEVnguồnmới;test enrollment chỉfitprofile của chính tài khoản. Không hạ điều kiện theo điểm. Chưa có nguồnBđược tải/chọn trong protocol này; không tuyên bố đã kiểm chứng B. Không gửi email/nhận thỏa thuận dữ liệu thay người dùng.

## Kiểm thử, khóa và báo cáo

Test synthetic: công thức ma trận,diagonal/fullđồngnhấtnếucovdiagonal, tính hữu hạn khi n<d vàđặctrưnglặp/constant,khôngfitheldout,khôngsửainput,Manhattanparity,calibration/evaluationIDs disjoint vàtie/validation. Khóa protocol/code/dependencies/DEVprojection/protected trước scoringA;ghi started,khôngghiđèresults. Covariance implementation theo [tài liệu chính thức LedoitWolf](https://scikit-learn.org/stable/modules/generated/sklearn.covariance.LedoitWolf.html); không cài nâng cấp môi trường đã khóa.

Mọi kết quảA gắn nhãn phát triển, không triển khai hoặc đổi cấu hình. Giữreport6/37/40/phụlục3trang vàZIPv3đãchốt;điểm100nộibộkhôngđổi. Khôngpush/deploy/DBwrite.
