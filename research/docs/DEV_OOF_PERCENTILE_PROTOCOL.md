# Đối chứng DEV: phân vị điểm OOF — 15/11/2026

Nghiên cứu phát triển từ chẩn đoán GREYC DEV đã xem; không kiểm chứng độc lập, không đụng TEST21mã hoặc điều chỉnh kết quả cũ. So sánh hai quy tắc chuẩn hóa trên cùng detector Scaled Manhattan,20enrollment,5foldOOF,21feature nguồn,khôngprior/shrink/update.

Baseline z=(raw−meanOOF)/SDOOF như cũ. Candidate duy nhất: **midrank percentile OOF** `u=(count(OOF<raw)+0.5*count(OOF==raw)+0.5)/(20+1)`. Điểm càng lớn càng bất thường. Không thử quantile/ECDF khác sau kết quả. Ties không chia. Candidate bão hòa ngoài min/max OOF, có thể kém phân biệt; giữ hạn chế này nếu thất bại.

Chia42DEV đã khóa theo thứ tự sẵn có: mỗi nhóm3,lấy2calibration/1evaluation→28/14mã. Cảhai nhánh fit cùng fullprofile20 và các profileCV16. Calibration chỉ28mã: probefirst5+last5enrollment của27mãkhác. Chọn ngưỡng riêng từng nhánh bằng đúng threshold_at_far≤5%,acceptscore≤tau,không chia ties. Đây là cùng ngân sách, không giữ số tau giữa thang z và phân vị. Không dùng latergenuine calibration đểchọn cấu hình.

Evaluation14mã: genuine toàn bộ các ngày sau enrollment đã có trong projectionDEV;impostorfirst5+last5later của13mãevaluationkhác,khôngtrùng. KhônggộpcalibrationvàevaluationIDs. Khôngchọnngưỡng từevaluation. Đây chỉ DEV nội bộ đã xem, không gọi14mã là holdout mới chưa biết.

Chốt tiêu chí trước chạy: ΔmacroFRR<0 và ΔmacroFAR≤0. Lợi đa số: đồng thời đạt tiêu chí và hơn7/14mã giảmFRR/FARkhôngtăng. Báo đủ counts/macro/pooled/grid và14mã; không chọn lại phương pháp theo kết quả. Kiểm synthetic(ties,ngoài miền,đơn điệu,baselineparity) rồi khóa code/protocol/input/env trước run,ghi started vàgiữ bấtlợi.

Không sửa source/corefrozen/cấu hình sản phẩm/TEST/report cũ/điểm sau100; phần cải tiến không nhận thêm điểm hoặc bảo đảm tốt hơn. Nếu đạt chỉ cho phép đề xuất nghiên cứu tiếp, chưa triển khai. Không push/deploy/DBwrite.
