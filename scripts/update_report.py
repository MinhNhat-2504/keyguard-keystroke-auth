"""Cập nhật bản thảo Word từ template và artifact, không giả lập ảnh/dữ liệu thật.

Chạy sau benchmark, select_threshold và make_report_figures.
Cần requirements-report.txt. Template giữ định dạng IEEE của bản gốc.
"""

from pathlib import Path
import sys
import json
import xml.etree.ElementTree as ET

import pandas as pd
from docx import Document
from docx.shared import Inches

ROOT = Path(__file__).resolve().parents[1]
sys.stdout.reconfigure(encoding="utf-8")


def number(v, digits=3):
    return f"{v:.{digits}f}".replace(".", ",")


def main():
    doc = Document(ROOT / "report/templates/KeyGuard_Template.docx")
    p = doc.paragraphs
    if len(p) != 108 or not p[42].text.startswith("Cách xây"):
        raise RuntimeError("Template đã đổi cấu trúc; cần đối chiếu lại vị trí nội dung.")
    s = pd.read_csv(ROOT / "results/benchmark_cmu_summary.csv").set_index(["detector", "n_train"])
    policies = pd.read_csv(ROOT / "results/threshold_selection.csv").set_index("policy")
    fallback = policies.loc["fallback"]
    far, frr = number(100 * fallback.far_test, 1), number(100 * fallback.frr_test, 1)
    edits = {
        7: f"Tóm tắt—KeyGuard nghiên cứu xác thực bằng nhịp gõ phím trên bộ CMU (51 người, 20.400 lượt, 8 phiên). Bốn họ mô hình được so sánh bằng EER nội suy và AUC; một biến thể Random Forest kiểm soát mức quen tay được bổ sung. Mô phỏng đăng nhập tuần tự với Scaled Manhattan, đăng ký 20 lượt và hồ sơ 50 lượt cho FAR {far}% và tỉ lệ yêu cầu xác minh thêm {frr}% trên 15 người không dùng để chọn ngưỡng. Nhóm này đã tham gia benchmark trước đó, nên không phải holdout độc lập cho toàn quy trình. Kết quả phụ thuộc giả định chính chủ luôn vượt xác minh bổ sung. Thư viện mô hình đã kiểm thử; bản web và dữ liệu thu thật còn đang hoàn thiện. Báo cáo phân biệt các kết quả CMU với những phần chưa có minh chứng thực tế.",
        13: "Một quy trình trích 31 đặc trưng và đánh giá có thể chạy lại trên CMU [3], với sự khác biệt protocol được công bố rõ.",
        14: "So sánh bốn họ mô hình và khảo sát ảnh hưởng của mức quen tay; kết quả cho thấy giả thuyết nhiễu do kinh nghiệm gõ cần được kiểm soát, chưa chứng minh quan hệ nhân quả.",
        16: "Thư viện Python cung cấp enroll, verify, update, công cụ kiểm tra chất lượng JSONL và tài liệu hợp đồng tích hợp cho web demo.",
        23: "Web collector trên thu-branch ghi keydown/keyup bằng performance.now(), xuất JSONL gồm participant_id, session, rep và events. Thư viện dùng cùng phép trích đặc trưng cho CMU dựng lại và sự kiện trình duyệt. Test roundtrip kiểm tra 200 dòng CMU đạt sai số cho phép. Quy trình thu thật phải xin đồng ý, dùng mã ẩn danh và không công khai bảng đối chiếu danh tính; sự tồn tại của một mã không tự chứng minh một người tham gia thật.",
        24: "Tại mốc kiểm tra 01/11/2026, nhánh web có 2 mẫu hợp lệ thuộc 2 mã, mỗi mã chỉ 1 mẫu. Audit không ghi nhận mã nào đủ 2 phiên × 40 lượt và chưa xác minh ngày thu/đồng ý. Chưa thể dùng các mẫu này đánh giá FAR/FRR. Nhật chờ TV2 bàn giao dữ liệu đủ quy mô, nhật ký thiết bị/ngày thu và xác nhận đồng ý; không thay bằng mẫu giả.",
        33: "Mỗi người học từ n lượt đầu (5–200), kiểm tra genuine bằng 200 lượt cuối. 50 người khác chia A/B, mỗi nhóm 25 theo seed 42; RF chỉ học impostor từ A và mọi mô hình test trên B. Kịch bản impostor dùng 5 lượt đầu hoặc 5 lượt cuối/người. Protocol CMU gốc [3] dùng cả 50 impostor, nên các số gần nhau chỉ là đối chiếu. EER nội suy tuyến tính tại giao điểm FAR=FRR trên ROC từng người rồi lấy trung bình 51 người; AUC tính với dấu điểm đảo lại. Không dùng ngưỡng EER từ test làm ngưỡng web.",
        37: "μg và σg được ước lượng bằng kiểm định chéo 5 phần trên mẫu đăng ký. Ngưỡng nhận z ≤ τ chọn trên 36 người dev; 15 người test không tham gia chọn τ nhưng đã xuất hiện trong benchmark so sánh mô hình. Static/fallback chọn ranh giới trước nhóm điểm làm vượt ngân sách floor(0,05 × số mẫu), dùng nextafter để giữ nguyên quy tắc ≤ khi điểm trùng. Accept quét lưới định trước, chọn τ khả thi lớn nhất. Code kiểm tra lại FAR dev sau chọn; không bảo đảm FAR của quần thể mới.",
        38: "Mỗi người đăng ký 20 lượt rồi đăng nhập 380 lượt còn lại; impostor thử ngay sau đăng ký và sau mỗi 50 lượt genuine, không cập nhật hồ sơ. Ba chính sách: static giữ hồ sơ; accept chỉ cập nhật mẫu được nhận; fallback cập nhật genuine cả sau xác minh bổ sung [4], [5], với cửa sổ 50 lượt. Fallback giả định mọi genuine đều qua bước bổ sung; FRR do đó đo tỉ lệ phải xác minh thêm, không đo thất bại OTP thực tế. Việc cập nhật mẫu impostor bị nhận nhầm chưa được mô phỏng.",
        39: "Hình 1 mô tả luồng thiết kế với fallback. Thực nghiệm dùng build_profile/profile_z trong cùng thư viện với API mô hình; hình này không phải minh chứng OTP đã hoạt động trong bản web.",
        41: "Luồng mô hình dự kiến; nhánh OTP cần được xác nhận bằng thử nghiệm web.",
        43: "Hình 2 mô tả kiến trúc dựa trên source: HTML/CSS/JavaScript ghi sự kiện, Flask cung cấp route và thư viện keyguard xử lý đặc trưng/mô hình. Hồ sơ dict JSON giữ tối đa 50 mẫu cùng tham số detector và thống kê chuẩn hóa. model_config.json do script chọn ngưỡng sinh ra; bản thư viện main đã có cấu hình, nhánh web được kiểm tra còn thiếu file tích hợp này.",
        45: "Kiến trúc tích hợp; OTP và gọi update trên web là phần chưa hoàn thành.",
        46: "Hợp đồng bàn giao yêu cầu enroll nhận samples là 20 danh sách sự kiện {key,type,t}; verify nhận một danh sách và trả confidence/accepted. Khi accepted hoặc backend xác nhận OTP đúng, API mới gọi update rồi lưu hồ sơ. update không tự kiểm tra OTP. Confidence là điểm logistic hiển thị, không phải xác suất danh tính đã hiệu chuẩn. Chi tiết và payload mẫu trong docs/TV1_HANDOFF.md.",
        47: "Web hiện dùng Flask, Jinja templates và JavaScript thuần; app.py lưu collected JSONL và profile JSON trên đĩa. Đánh giá source/API của thu-branch bb88874 cho thấy đăng ký gửi events trong khi backend đọc samples, chỉ thu 5 lượt và schema sai; thiếu OTP/cập nhật hồ sơ. Các lỗi này phải được TV2 sửa trước demo. Không mô tả luồng thiết kế như một tính năng đã nghiệm thu.",
        48: "Repo github.com/MinhNhat-2504/keyguard-keystroke-auth lưu script, cấu hình, CSV và hình. Bộ test gồm trường hợp roundtrip CMU, ROC/EER, ngưỡng có điểm trùng, lịch checkpoint và JSONL lỗi/trùng. Các test kiểm tra tình huống cụ thể, không chứng minh toàn bộ hệ thống an toàn hay thay thế thử nghiệm người dùng.",
        51: "Dùng Python 3.11; tạo .venv và pip install -r requirements.txt. Tải CMU theo data/README.md. Chạy pytest, run_benchmark.py, select_threshold.py rồi make_report_figures.py. Audit dữ liệu bằng audit_collected.py --input \"data/collected/*.jsonl\"; khi đủ, chạy evaluate_collected.py --data-kind collected. Tạo report bằng pip install -r requirements-report.txt và python scripts/update_report.py. Script Word dùng template, cập nhật bảng/số liệu và hình; cần kiểm tra lại bố cục sau mỗi lần thay nội dung.",
        53: "Để khảo sát bản web hiện có: tại checkout thu-branch, cài requirements rồi python app.py; mở http://127.0.0.1:5000/ (collector), /register và /login. Đây là hướng dẫn khởi động từ source, chưa phải xác nhận toàn luồng chạy được. Sau khi tích hợp đúng cấu hình/payload, thực hiện các bước nghiệm thu dưới đây.",
        54: "Bước 1 (yêu cầu nghiệm thu) — Đăng ký: nhập mã tài khoản demo, gõ .tie5Roanl + Enter đủ 20 lượt hợp lệ. Chờ keyup Enter trước khi gửi. Mẫu sai bị báo rõ và không tăng bộ đếm. Đăng ký trùng không được ghi đè hồ sơ người khác.",
        55: "[CHỜ TV2: ảnh đăng ký thực tế sau khi sửa đủ 20 lượt; không dùng ảnh dựng làm bằng chứng.]",
        56: "Minh chứng màn hình đăng ký chưa được bàn giao.",
        57: "Bước 2 (yêu cầu nghiệm thu) — Đăng nhập: gửi sự kiện của một lượt hoàn chỉnh, hiển thị confidence và accepted. Sai schema/sai câu phải báo lỗi, không hiển thị NaN% hoặc báo thành công giả. Gõ tự nhiên trên cùng bàn phím như lúc đăng ký.",
        58: "[CHỜ TV2: ảnh đăng nhập thành công và ảnh nhịp gõ bị yêu cầu xác minh thêm.]",
        59: "Minh chứng màn hình đăng nhập chưa được bàn giao.",
        60: "Bước 3 (yêu cầu nghiệm thu) — Xác minh bổ sung: OTP đúng và còn hạn mới cho phép cập nhật mẫu đang chờ của đúng tài khoản. OTP sai/hết hạn không cập nhật hồ sơ. Backend phải quản lý challenge; không tin cờ thành công do client tự khai.",
        61: "[CHỜ TV2: ảnh OTP thật, log kiểm thử OTP đúng/sai/hết hạn và hồ sơ trước/sau cập nhật.]",
        62: "OTP chưa có trong nhánh web được kiểm tra; không có ảnh sử dụng thực tế.",
        63: "Hướng dẫn trên mô tả tiêu chí sử dụng sau tích hợp, chưa phải kết quả kiểm thử toàn luồng. Ảnh thật và kết quả live test sẽ được đưa vào bản cuối; không công bố bản thảo hiện tại là sản phẩm hoàn chỉnh.",
        66: "Bảng I và Hình 6 dùng artifact chạy lại với EER nội suy. Mỗi cấu hình đánh giá đủ 51 người; RF-early là biến thể thứ năm của bốn họ mô hình. Scaled Manhattan n=200 có EER gần số công bố [3], nhưng protocol impostor khác nên không gọi là tái lập chính xác. EER trung bình giảm khi tăng số lượt đăng ký; AUC được lưu ở benchmark_cmu_summary.csv. Timing đo trên cùng lần chạy, RF dùng một worker.",
        72: "Thời gian gõ cả câu trung bình theo người giảm từ 3,06 giây ở phiên 1 còn 2,19 giây ở phiên 8 (khoảng 28%; Hình 7). RF học từ impostor mọi phiên kém hơn biến thể lấy impostor đầu chuỗi khi n=20. Đây là dấu hiệu cần kiểm soát mức quen tay; tương quan này chưa chứng minh mô hình chỉ học tốc độ thay cho danh tính.",
        75: "Kịch bản impostor đã luyện làm tăng EER của một số mô hình, cho thấy kết quả phụ thuộc cách xây tập tấn công. Scaled Manhattan thay đổi ít hơn ở n=20, học nhanh và lưu JSON được nên dùng cho thiết kế thích nghi. Tuy nhiên lựa chọn mô hình đã xem benchmark cả 51 người; không diễn giải phép tách 36/15 sau đó như một kiểm định mô hình hoàn toàn độc lập. Cần xác nhận trên người/thiết bị mới.",
        77: f"Bảng II và Hình 8 trình bày lần chạy lại sau khi sửa mốc impostor thành mỗi 50 lần đăng nhập kể từ enrollment. Static có FRR {number(100*policies.loc['static'].frr_test,1)}%, accept {number(100*policies.loc['accept'].frr_test,1)}%, fallback {frr}%. Fallback có FAR {far}%, với τ={number(fallback.threshold)} chọn theo dev. Các số này thay thế kết quả cũ dùng mốc tuyệt đối trong chuỗi; không được trộn bảng cũ với cấu hình mới.",
        82: "Hình 9 cho thấy fallback giữ FRR khoảng 12–23% theo phiên, thấp hơn static/accept ở các phiên muộn. FAR test là ước lượng trên 15 người, chịu phụ thuộc giữa những lần thử cùng người/hồ sơ; không xem mọi lượt là độc lập để suy ra độ tin cậy quá hẹp. Mục tiêu FAR 5% áp dụng dev, không phải chứng nhận an toàn cho web.",
        86: "Audit hai file JSONL hiện có ghi nhận 2 mẫu hợp lệ, mỗi mã chỉ 1 lượt; chưa ai đủ tối thiểu 25 lượt (20 enroll + 5 test) của công cụ đánh giá. evaluate_collected.py dừng rõ ràng và không sinh bảng FAR/FRR giả. Script hiện loại JSON sai, sự kiện không hữu hạn và trùng người/phiên/rep, đồng thời xuất lý do theo dòng. Chưa có kết quả đánh giá dữ liệu thu thật hoặc phân tích chênh lệch thiết bị/ngày thu.",
        87: "[CHỜ TV2: dữ liệu đủ quy mô, nhật ký ẩn danh và live_test.csv với ít nhất 10 impostor/20 lượt chính chủ.] Bản cuối cần FAR/FRR theo người/phiên, số lượng tử số/mẫu số và phân tích lỗi. Kết quả pipeline trên data/sample dựng từ CMU chỉ xác minh công cụ chạy, không thay thế thử nghiệm thực tế.",
        91: "Giới hạn bổ sung: mô hình đã được so sánh trên cả 51 người; thiếu đánh giá trên người hoàn toàn mới, thiết bị mới và kiểm tra chất lượng OTP. Chính sách/ngưỡng không được chọn lại theo test; cập nhật sau sửa lịch mô phỏng là sửa protocol, không phải tối ưu theo kết quả test. Bản cuối cần thu thật và test web trước khi kết luận tính dùng được của sản phẩm.",
        93: f"Trên CMU, mô phỏng fallback với Scaled Manhattan đạt FAR {far}% và tỉ lệ cần xác minh thêm {frr}% ở nhóm không dùng để chọn ngưỡng. Đây là bằng chứng cho thiết kế mô phỏng dưới giả định xác minh bổ sung thành công, chưa chứng minh hiệu quả web thực tế. Phần độc lập của thư viện, công cụ đánh giá và tài liệu bàn giao đã có; dữ liệu thật, ảnh và live test là các đầu vào còn thiếu để hoàn tất báo cáo nhóm.",
    }
    collected = json.loads((ROOT / "results/collected_preliminary_summary.json").read_text(encoding="utf-8"))
    sensitivity = json.loads((ROOT / "results/collected_sensitivity_first_summary.json").read_text(encoding="utf-8"))
    cfar1, cfar2, cfrr = (number(100*collected[k], 2) for k in ("far_early_pooled", "far_late_pooled", "frr_pooled"))
    edits.update({
        45: "Kiến trúc nhánh web44a610b; OTP/update đã có, chưa nghiệm thu trình duyệt/live test.",
        7: f"Tóm tắt—KeyGuard nghiên cứu xác thực nhịp gõ trên CMU và bộ thu qua trình duyệt. Bốn họ mô hình được so sánh bằng EER nội suy/AUC. Với cấu hình Scaled Manhattan chọn trên CMU, mô phỏng fallback cho FAR {far}%, FRR {frr}% ở15 người không dùng chọn ngưỡng, nhưng đã tham gia benchmark trước đó. Snapshot tự thu gồm601 dòng/15 mã; sau loại4 dòng mơ hồ/thiếu thời gian còn597 mẫu,297 genuine test. Giữ nguyên cấu hình CMU cho FAR {cfar1}% (5 lượt đầu của người khác), {cfar2}% (5 lượt cuối) và FRR {cfrr}%. FAR cao cho thấy cấu hình chưa chuyển tốt sang miền dữ liệu mới. Dữ liệu chủ yếu một phiên, chưa đánh giá drift nhiều ngày; fallback giả định genuine vượt xác minh bổ sung. Web có API/OTP nhưng ảnh và live test chưa được bàn giao.",
        24: "Snapshot ngày10/11 từ thu-branch44a610b có601 dòng ở15 mã (nguồn tác giả mô tả15 người). Audit thấy600 khóa duy nhất; P10/session1/rep29 trùng2 dòng, thiếu rep39;2 mẫu cũ không có thời gian. Giữ nguyên raw và SHA-256, phân tích chính loại cả2 dòng khóa mơ hồ cùng2 mẫu thiếu timestamp. Còn597 mẫu, mỗi mã38–40, sắp collected_at UTC. Chưa mã nào đủ2 phiên40 lượt khác ngày; metadata thiết bị và xác nhận đồng ý từng mã chưa được đối chiếu.",
        47: "Web44a610b đã có API/OTP/update;39 kiểm tra HTTP/API đạt, chưa thử toàn luồng trình duyệt. Ngưỡng web cũ0,250315 khác bản CMU sửa protocol0,272009 dùng trong phân tích; cần đồng bộ khi triển khai, không tự đổi theo bộ thu.",
        48: "Repo github.com/MinhNhat-2504/keyguard-keystroke-auth lưu script, cấu hình, kết quả và test; xem docs/TV1_HANDOFF.md và docs/COLLECTED_PRELIMINARY.md để tái lập. Test không thay bằng chứng người dùng thật.",
        51: "Dùng Python3.11, cài requirements.txt; tải CMU theo data/README.md. Chạy pytest, run_benchmark.py, select_threshold.py. Nhập snapshot bằng import_collected.py; đánh giá sơ bộ theo lệnh ở phụ lụcB. requirements-report.txt và update_report.py tạo Word, render_report.ps1 dùng Word xuất PDF; kiểm tra bố cục sau mỗi lần cập nhật.",
        55: "[CHỜ TV2: ảnh đăng ký20 lượt trên trình duyệt; backend đã kiểm tra bằng HTTP, chưa có ảnh nghiệm thu.]",
        62: "API OTP đã được kiểm tra logic; ảnh sử dụng thực tế chưa bàn giao.",
        66: "Bảng I và Hình6 dùng benchmark EER nội suy (51 người/cấu hình). RF-early là biến thể thứ5 của4 họ mô hình. EER Scaled Manhattan n200 gần công bố[3] nhưng khác số impostor nên chỉ đối chiếu. AUC trung bình n20: SM0,853; OCSVM0,867; IF0,897; RF0,632; RF-early0,879. Timing cùng lần chạy, RF một worker. EER thấp không chứng minh FAR thấp tại ngưỡng chung khi đổi miền dữ liệu.",
        86: f"Bộ tự thu giữ597 mẫu, enroll20/mã còn297 genuine. Giữ tau={number(collected['threshold'])}:49/297 genuine cần xác minh={cfrr}%. Impostor nhận284/1050={cfar1}% đầu,331/1050={cfar2}% cuối. Mỗi tài khoản chỉ18–20 genuine nên impostor chỉ thử ngay sau enroll, chưa đạt mốc50. Chi tiết mẫu loại và kết quả theo mã ở phụ lụcA; chưa phải live test.",
        87: "FAR vượt5%; không chỉnh tau theo test. Giữ dòng đầu khóa trùng thay vì loại cả nhóm cho598 mẫu/298 genuine,FRR16,44%,FAR không đổi. [CHỜ TV2: phiên/ngày bổ sung, ảnh thật, live test≥10 impostor/≥20 lượt genuine.]",
        91: "Bộ mới chủ yếu cùng phiên; P10 cùng session trải2 ngày, chưa đủ2 phiên40 lượt. Chưa đối chiếu thiết bị/danh tính từ mã. Chênh lệch giữa nguồn chỉ mô tả, không suy ra nhân quả; các điểm cùng người phụ thuộc. Hiệu chỉnh mới cần dev riêng và test chưa dùng.",
        93: f"FAR từ {far}% trên CMU tăng lên {cfar1}%/{cfar2}% ở bộ thu sơ bộ, cho thấy cấu hình chưa chuyển tốt sang miền trình duyệt. Đã có provenance, protocol lọc, bảng/hình và độ nhạy; còn thiếu nhiều phiên, ảnh và live test để kết luận hiệu quả sản phẩm. Không chỉnh ngưỡng theo bộ đã xem.",
    })
    for i, text in edits.items():
        p[i].text = text
    # Không để tiêu đề bảng nằm một mình cuối trang trước bảng.
    for i in (67, 68, 78, 79):
        p[i].paragraph_format.keep_with_next = True
    p[44].clear()
    p[44].add_run().add_picture(str(ROOT / "figures/report/fig_architecture.png"), width=Inches(3.35))
    names = ["ScaledManhattan", "OneClassSVM", "IsolationForest", "RandomForest", "RandomForest-early"]
    for row, name in zip(doc.tables[0].rows[2:], names):
        a, b = s.loc[(name, 20)], s.loc[(name, 200)]
        for col, v in enumerate([a.eer_mean, a.eer_practiced_mean, b.eer_mean,
                                 b.eer_practiced_mean, a.fit_ms_mean], 1):
            row.cells[col].text = number(v, 2 if col == 5 else 3)
    for row, name in zip(doc.tables[1].rows[1:], ["static", "accept", "fallback"]):
        r = policies.loc[name]
        for cell, text in zip(row.cells[1:], [number(r.threshold, 2), number(100*r.far_test,1)+"%", number(100*r.frr_test,1)+"%"]):
            cell.text = text
    # Các ảnh đã nhúng từ bản gốc cần được thay bằng artifact mới, không chỉ đổi file ngoài.
    figures = ["fig_pipeline.png", "fig_eer_vs_enrollment.png", "fig_typing_time.png",
               "fig_policy_tradeoff.png", "fig_frr_by_session.png"]
    for i, filename in zip([40, 69, 73, 80, 83], figures):
        p[i].clear()
        p[i].add_run().add_picture(str(ROOT / "figures/report" / filename), width=Inches(3.35))
    # Hai trang phụ lục bổ sung minh chứng có thật, không điền ảnh demo giả.
    from docx.enum.section import WD_SECTION_START
    from docx.oxml.ns import qn
    doc.sections[-1].start_type = WD_SECTION_START.NEW_PAGE
    columns = doc.sections[-1]._sectPr.find(qn("w:cols"))
    columns.set(qn("w:num"), "2")
    columns.set(qn("w:space"), "360")
    doc.add_heading("Phụ lục A — Lỗi trên dữ liệu tự thu", level=1)
    users = pd.read_csv(ROOT / "results/collected_preliminary_per_user.csv")
    genuine_n = int(users.n_logins.sum())
    impostor_n = int(users.impostor_trials_early.sum())
    doc.add_paragraph(
        f"Lần chạy fallback gồm {genuine_n:,} lượt genuine và {impostor_n:,} lượt impostor tại các mốc hồ sơ, "
        f"với {int(users.genuine_rejected.sum()):,} genuine cần xác minh thêm và "
        f"{int(users.impostor_accepted_early.sum())}/{int(users.impostor_accepted_late.sum())} impostor được nhận (đầu/cuối). "
        "Nguồn: results/collected_preliminary_per_user.csv; các lượt cùng người/hồ sơ có phụ thuộc. "
        "Không có mẫu loại nào được đánh số lại; xem exclusions JSON và manifest SHA-256.", style="Body Text")
    doc.add_picture(str(ROOT / "figures/report/fig_collected_errors.png"), width=Inches(3.35))
    doc.add_paragraph("Lỗi theo15 mã, ngưỡng CMU giữ nguyên; đầu/cuối chỉ thứ tự mẫu, không xác nhận mức luyện gõ.", style="figure caption")
    from docx.enum.text import WD_BREAK
    doc.add_paragraph().add_run().add_break(WD_BREAK.COLUMN)
    worst_frr = users.loc[users.frr.idxmax()]
    worst_far = users.loc[users.far_late.idxmax()]
    doc.add_paragraph(
        f"FRR cao nhất: {worst_frr.participant_id}, {int(worst_frr.genuine_rejected)}/{int(worst_frr.n_logins)} "
        f"({number(100*worst_frr.frr,1)}%). FAR cuối cao nhất: {worst_far.participant_id}, "
        f"{int(worst_far.impostor_accepted_late)}/70 ({number(100*worst_far.far_late,2)}%). "
        "P10 có FAR61/70 ở cả hai kịch bản; P15 có55/70 và56/70. FRR thấp ởP13/P15 đi cùng FAR rất cao, "
        "không đồng nghĩa nhận diện tốt. Không chọn ngưỡng cá nhân theo các kết quả test này.",
        style="Body Text")
    doc.add_paragraph("Tổng hợp phân tích chính (597 mẫu/15 mã)", style="table head")
    auc_table = doc.add_table(rows=1, cols=3)
    for cell, text in zip(auc_table.rows[0].cells, ["Chỉ số", "Tử/mẫu", "Tỉ lệ"]):
        cell.text = text
    for values in [["FRR", "49/297", cfrr+"%"], ["FAR đầu", "284/1050", cfar1+"%"],
                   ["FAR cuối", "331/1050", cfar2+"%"],
                   ["EER đầu TB", "15 mã", number(100*collected['eer_early_mean'],2)+"%"],
                   ["EER cuối TB", "15 mã", number(100*collected['eer_late_mean'],2)+"%"]]:
        for cell, text in zip(auc_table.add_row().cells, values):
            cell.text = text
    doc.add_paragraph(
        "EER nội suy chỉ mô tả xếp hạng: genuine chấm theo hồ sơ cập nhật còn impostor chỉ ở enrollment; "
        "không phải ROC một hồ sơ tĩnh hay ngưỡng triển khai. Thời gian gõ trung vị theo mã khoảng2,56–9,64 giây; "
        "chưa có metadata để gán nguyên nhân do thiết bị. Bản phụ giữ dòng đầu khóa trùng cóFRR16,44%, "
        "FAR không đổi: kết luận lỗi chuyển miền không phụ thuộc hai cách xử lý đã công bố.", style="Body Text")

    # Section hai cột mới để Word cân hai cột của phụ lục A trước sang trang.
    doc.add_section(WD_SECTION_START.NEW_PAGE)
    doc.add_heading("Phụ lục B — Tái lập và tiêu chí bàn giao", level=1)
    suite = ET.parse(ROOT / "results/test_results.xml").getroot().find("testsuite")
    smoke = json.loads((ROOT / "results/model_smoke.json").read_text(encoding="utf-8"))
    doc.add_paragraph(
        f"Môi trường kiểm tra Python 3.11; {suite.attrib['tests']} test, "
        f"{suite.attrib['failures']} failure, {suite.attrib['errors']} error, {suite.attrib['skipped']} skip. "
        "requirements.txt chốt thư viện số; requirements-report.txt thêm python-docx. "
        "Benchmark/chọn ngưỡng đã chạy lại, log ở results/benchmark_run.log và select_threshold.log. "
        "Kiểm tra hiện tại dùng môi trường sẵn có, không tuyên bố đã thử cài sạch trên mọi máy.", style="Body Text")
    check_table = doc.add_table(rows=1, cols=2)
    for cell, text in zip(check_table.rows[0].cells, ["Nhóm kiểm tra", "Điều kiện được kiểm chứng"]):
        cell.text = text
    checks = [
        ("Đặc trưng", "Roundtrip 200 dòng CMU; bỏ Shift; sai câu và thiếu keyup bị loại."),
        ("ROC/EER và ngưỡng", "ROC giao nhau, tách hoàn toàn, điểm bằng nhau, ngân sách <1 mẫu; điểm không hữu hạn bị từ chối."),
        ("Mô hình", "Enroll đủ mẫu, profile lưu JSON, nhận/từ chối mẫu giả lập; window theo drift."),
        ("Mô phỏng", "Mốc impostor đếm từ sau enrollment, không từ đầu chuỗi."),
        ("Dữ liệu JSONL", "Dòng hỏng và trùng người/phiên/rep được ghi lý do, không tăng số mẫu."),
    ]
    for label, detail in checks:
        for cell, text in zip(check_table.add_row().cells, [label, detail]):
            cell.text = text
    doc.add_paragraph(
        f"Smoke hợp đồng với mẫu dựng từ CMU: enroll {smoke['enroll_samples']} lượt, "
        f"verify confidence {number(smoke['confidence'])}, accepted={smoke['accepted']}; "
        f"update tạo {smoke['updated_samples']} mẫu và JSON roundtrip đạt. "
        "Đây là kiểm tra thư viện với nhãn genuine đã biết; không thử HTTP, OTP hay người dùng thật.", style="Body Text")
    doc.add_paragraph().add_run().add_break(WD_BREAK.COLUMN)
    doc.add_paragraph("Lệnh kiểm tra chính (chạy từ root repo)", style="Heading 2")
    for command in ["python -m pytest -q --junitxml=results/test_results.xml",
                    "python scripts/run_benchmark.py",
                    "python scripts/select_threshold.py",
                    "python scripts/smoke_model.py",
                    'python scripts/audit_collected.py --input "data/collected/*.jsonl"',
                    "python scripts/evaluate_collected.py --data-kind collected --out-prefix collected_preliminary",
                    "python scripts/analyze_collected.py"]:
        doc.add_paragraph(command, style="Body Text")
    doc.add_paragraph(
        "Đã nhận snapshot601 dòng và đánh giá sơ bộ; còn chờ TV2 bổ sung đủ phiên/ngày, xác nhận đồng ý, thiết bị; "
        "ảnh đăng ký/đăng nhập/OTP thật; live_test.csv của ít nhất 10 impostor và 20 lượt chính chủ. "
        "Sau nhận, chạy audit/đánh giá lại theo protocol công bố và thay phần chờ; "
        "không dùng dữ liệu sample hay ảnh sơ đồ để thay minh chứng. Hợp đồng tích hợp và checklist nằm ở docs/TV1_HANDOFF.md.",
        style="Body Text")
    # Giữ font bảng theo khổ IEEE khi thay text.
    from docx.shared import Pt
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    for table_no, table in enumerate(doc.tables):
        if table_no >= 2:
            table.autofit = False
            widths = [1.55, 0.95, 0.85] if table_no == 2 else [0.95, 2.40]
            for column, width in zip(table.columns, widths):
                column.width = Inches(width)
            for row in table.rows:
                for cell, width in zip(row.cells, widths):
                    cell.width = Inches(width)
            borders = OxmlElement("w:tblBorders")
            for side in ("top", "left", "bottom", "right", "insideH", "insideV"):
                border = OxmlElement(f"w:{side}")
                border.set(qn("w:val"), "single")
                border.set(qn("w:sz"), "4")
                border.set(qn("w:color"), "B0B0B0")
                borders.append(border)
            table._tbl.tblPr.append(borders)
        for row in table.rows:
            for cell in row.cells:
                for paragraph in cell.paragraphs:
                    for run in paragraph.runs:
                        run.font.name = "Times New Roman"
                        run.font.size = Pt(8)
    for paragraph in doc.paragraphs[108:]:
        if paragraph.style.name == "Body Text":
            paragraph.paragraph_format.line_spacing = 1.0
            paragraph.paragraph_format.space_after = Pt(3)
            for run in paragraph.runs:
                run.font.size = Pt(10)
    doc.core_properties.title = "KeyGuard — Bản thảo đã kiểm chứng phần TV1, chờ minh chứng TV2"
    doc.core_properties.comments = "Cập nhật artifact từ source; không dùng mẫu CMU dựng lại làm dữ liệu thu thật."
    doc.save(ROOT / "report/KeyGuard_Report.docx")
    print("Updated report/KeyGuard_Report.docx; các mục CHỜ TV2 giữ rõ trong nội dung.")


if __name__ == "__main__":
    main()
