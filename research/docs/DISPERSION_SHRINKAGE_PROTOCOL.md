# Đối chứng co độ phân tán đặc trưng — 15/11/2026

## Giả thuyết và phạm vi khóa trước scoring

Candidate giảm FRR macro và không tăng FAR macro so Scaled Manhattan baseline khi cùng hồ sơ cố định 20 mẫu, feature, split, probe và ngân sách FAR dev 5%. Hai nguồn xét riêng; chỉ ghi ủng hộ nhất quán nếu cả hai đạt từ phân số trước làm tròn. Không CI/p-value hoặc kết luận holdout mới: cả CMU và KeyRecs đã được xem. Không thay mô hình/ngưỡng sản phẩm.

## Thay đổi duy nhất của detector

Baseline: tâm = mean, local MAD = mean(abs(X − mean)), floor 1e−9. Candidate giữ tâm và phép cộng khoảng cách nhưng dùng `scale_j=max(0.75*local_MAD_j+0.25*prior_j,1e-9)`.

Prior theo từng đặc trưng = median của MAD enrollment 20 mẫu đầu của các mã dev trong cùng nguồn, không lấy biến thiên giữa tâm của các mã. Khi hiệu chỉnh một tài khoản dev, loại toàn bộ tài khoản đó khỏi nhóm tính prior (leave-one-identity-out). Khi chấm test, prior chỉ từ toàn bộ dev. Không dùng enrollment của test, S1 sau mẫu20 hoặc S2 để fit prior. Baseline không dùng prior. Trong CV5fold của tài khoản, tâm/MAD local chỉ fit16 mẫu training, prior ngoài tài khoản giữ cố định; mean/SD population của OOF như baseline, floor SD1e−6.

λ=0.25 duy nhất, chọn trước chẩn đoán/scoring. Không search λ, feature subset, prior estimator, seed hoặc ngưỡng theo test. Không lọc mẫu, chuẩn hóa tốc độ, trọng số theo tuổi, warm-up hoặc cập nhật hồ sơ.

## Dữ liệu và đánh giá

Giữ dev/test IDs từ matched_adaptation_plan.json: CMU36dev/15test/31 chiều, KeyRecs66dev/33test/47 chiều. Raw và thứ tự được khóa theo SHA. Mỗi tài khoản đăng ký đúng20 mẫu đầuS1. Hiệu chỉnh từng nhánh trên first5+last5S1 của các tài khoản dev khác, chọn threshold_at_far với accept z<=tau và không tách điểm trùng; FAR dev<=5%. Các probe dev có thể trùng enrollment của mã nguồn: dùng cho hiệu chỉnh dev, không gọi dev holdout độc lập.

Test genuine = toàn bộ S2, không update. Impostor = first5+last5S2 của các mã test khác. CMU750genuine/2100impostor; KeyRecs3301/10560. Macro theo mã là chính; pooled có số đếm riêng. Không so trực tiếp với phép matched/decay có warm-up và cập nhật.

Baseline phải khớp build_profile/profile_z trên dữ liệu giả; trên KeyRecs phải tái lập baseline static của external_validation.json (909/10560 và2450/3301), không candidate nào được chấm trước khi hai ngưỡng dev đã chọn.

## Chẩn đoán trước lượt candidate

Chỉ dùng20 enrollment của DEV: báo localMAD/prior theo feature, floor activation, tỷ lệMAD/prior<0.1 và đóng góp tuyệt đối OOF baseline theo feature. Prior mỗi mã loại chính mã đó. Đây là kiểm tra cơ chế giả thuyết, không kết luận MAD nhỏ gây lỗi test hay thay đổi thiết kế sau quan sát. Không dùng scores/test/S2 để chẩn đoán. Kết quả thuận/bất lợi đều giữ.

## Thứ tự và bảo toàn

Ghi plan/protocol → kiểm thử dữ liệu giả → khóa code/env/raw/thiết kế và artifact cũ → chạy --diagnose → chạy --run → đối chiếu số đếm/CSV/chronology. Exclusive creation: không overwrite kết quả hoặc khóa lại sau scoring. Thay đổi tiếp cần protocol và tên artifact khác.

Giữ toàn bộ keyguard core, các freeze/kết quả cũ, model_config, bốn báo cáo gốc, bản37trang và gói handover_v2. UI chỉ sửa presentation ngoài code/data thí nghiệm; không dùng nghiên cứu này làm task bù B1–B3 của Thư.
