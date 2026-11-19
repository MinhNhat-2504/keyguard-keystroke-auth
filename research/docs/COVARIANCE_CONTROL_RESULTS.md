# Kết quả đối chứng covariance — 15/11/2026

**Giai đoạnA: phát triển trênDEVđãxem**,28calibration/14evaluation từ42DEVGREYC. Khôngchấm21TESTcũ;chưa cógiaiđoạnB kiểmchứngngoài. Thiếtkế/code/dependencies/inputkhóatrướcrun sau9/9tests.

Hai nhánh chính cùng mean/MAD/covarianceLedoitWolf vàruleOOF;chỉ giữ hoặc bỏ off-diagonal. Shrinkage tự tính từ training,khôngsearchtheolabel. Fullscore vàdiagonalscoređều cănkhoảngcáchMahalanobis,khôngnhầmcontrolnàyvớiManhattan.

| Nhánh | FAR macro | FRR macro | Nhận nhầm | Genuine bị từ chối |
|---|---:|---:|---:|---:|
|diag_lw|2.14%|69.15%|39/1820|892/1125|
|full_lw|2.97%|68.74%|54/1820|853/1125|
|scaled_manhattan|3.08%|74.03%|56/1820|923/1125|

Phép chính full_lw−diag_lw: ΔFARmacro **+0.8242đpt**, ΔFRRmacro **-0.4086đpt**. Có **4/14** mã giảmFRR/FARkhôngtăng. Primary vàlợiđa sốđềukhôngđạt.

So với diagonal,full giảm39genuine bịtừchối nhưngtăng15nhậnnhầm. CổngđiBkhôngđạt:khôngtảinguồnkhácđểcứuphươngpháp,khôngthửridge/estimator/seedkhác,giữbấtlợi.

So với ScaledManhattan,nhánhfullcó54vs56falseaccept và853vs923genuinereject; đây làthamchiếumôtảđãđịnhkhôngphảitiêuchíchọn. Khôngđổiđốichứngchínhsaukhixemthamsốhoặctuyênbốđãcảitiếnđộclập. MuốnđánhgiáfullvsManhattanlàcâuhỏimớicầnprotocolmới;14DEVnàykhôngthànhholdoutmới.

## Chẩn đoán fit

Full-enrollment residual rank min/max **11/11** trên21chiều; phùhợpviệccácvectorcóquanhệđạisố,khôngchứngminhlànguyênnhânlỗi. Shrinkage training trong42DEV: 0.3228–0.9041;khôngđượctunedtheoevaluation.

9synthetictestskiểmmatrixformula,diagidentity,n<d/constant/duplicate,trainingfold16/full20,Manhattanparity,noinputmutation/affinescaling,invalidinputvàDEV/TESTdisjoint. NhánhManhattan đã táilập đúngcounts/ngưỡng củaDEVpercentilecũ. Validatorđộclậptínhlạiphânsốmacro/pooled/counts/benefit/gate/chronologytừartifact,khônggọiscoring.

Nguồn implementation: [scikit-learnLedoitWolf](https://scikit-learn.org/stable/modules/generated/sklearn.covariance.LedoitWolf.html). Protocol: COVARIANCE_CONTROL_PROTOCOL.md. Artifact: results/covariance_control_{freeze,tests,started,results,accounts,checks} vàfreeze.sha256. `python scripts/run_covariance_control.py --check` và `python scripts/validate_covariance_control.py` kiểmkhôngtínhđiểm. Runner từchốighiđèrun.

**Giữ cấu hình sản phẩm.** KhôngđổiTEST/raw/report6/37/40/phụlục3trang/ZIPv3/điểm100nộibộ;khôngpush/deploy/DBwrite. KếtquảAkhôngủnghộtiếnBtheocổngđịnhtrước;chưakhẳngđịnhmọiMahalanobisđềukém.
