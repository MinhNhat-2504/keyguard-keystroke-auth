"""Synthesize saved comparisons; never fit, calibrate or replace historical synthesis."""
import csv
from fractions import Fraction as F
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUTPUT='results/research_decision_20261115'


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def at(data,pointer):
    for key in pointer.strip('/').split('/'):data=data[int(key)] if isinstance(data,list) else data[key]
    return data


def main():
    legacy=json.loads((ROOT/'results/research_synthesis_20261114.json').read_text(encoding='utf-8'))
    sources={n:sha(ROOT/n) for n in legacy['source_sha256']}
    for n,h in legacy['source_sha256'].items():assert sources[n]==h
    names=['results/research_synthesis_20261114.json','results/dispersion_shrinkage_results.json',
           'results/greyc_web_account_benefit_results.json','results/dev_oof_percentile_results.json',
           'results/covariance_control_results.json','results/greyc_dev_full_pairing.json']
    sources.update({n:sha(ROOT/n) for n in names})
    protected={p.relative_to(ROOT).as_posix():sha(p) for p in list((ROOT/'report').glob('*.pdf'))+
               list((ROOT/'report').glob('*.docx'))+list((ROOT/'handover').glob('*.zip'))}
    rows=[]
    for original in legacy['rows']:
        rows.append({**original,'phase':'historical_development_or_initial_external_as_documented',
                     'role':'historical_comparison','comparison_rule':'see_group_protocol'})
    groups=dict(legacy['groups'])
    def add(group,source,artifact,pointer,phase,role):
        data=json.loads((ROOT/artifact).read_text());a=at(data,pointer);accounts=a['accounts']
        totals={k:sum(r[k] for r in accounts) for k in ('genuine_trials','genuine_rejected','impostor_trials','impostor_accepted')}
        far=sum((F(r['impostor_accepted'],r['impostor_trials']) for r in accounts),F())/len(accounts)
        frr=sum((F(r['genuine_rejected'],r['genuine_trials']) for r in accounts),F())/len(accounts)
        rows.append({'group':group,'source':source,'variant':a['method'],'metric_basis':'macro_accounts',
                     'artifact':artifact,'pointer':pointer,'genuine_trials':totals['genuine_trials'],
                     'genuine_rejected':totals['genuine_rejected'],'impostor_trials':totals['impostor_trials'],
                     'impostor_accepted':totals['impostor_accepted'],'far':float(far),'frr':float(frr),
                     'pooled_far':totals['impostor_accepted']/totals['impostor_trials'],
                     'pooled_frr':totals['genuine_rejected']/totals['genuine_trials'],'sd_far':None,'sd_frr':None,
                     'phase':phase,'role':role,'comparison_rule':'delta_macro_frr < 0 and delta_macro_far <= 0'})
    shrink='results/dispersion_shrinkage_results.json';d=json.loads((ROOT/shrink).read_text())
    for i,dataset in enumerate(d['datasets']):
        for j,a in enumerate(dataset['arms']):add('mad_shrink',dataset['dataset'],shrink,f'/datasets/{i}/arms/{j}','development_seen_sources','control' if j==0 else 'candidate')
    groups['mad_shrink']={'title':'Co MAD về prior DEV (shrink25)',
        'protocol':'Hồ sơ tĩnh20, CV5fold; cùng ngân sách FAR DEV5%; CMU/KeyRecs đã xem.',
        'conclusion':'Không nguồn nào đạt tiêu chí. CMU cả hai lỗi tăng; KeyRecs giảm FRR nhưng tăng FAR.'}
    external='results/greyc_web_account_benefit_results.json'
    for j in range(2):add('greyc_fixed','GREYC-Web',external,f'/evaluation/arms/{j}','first_use_new_source_after_method_lock','control' if j==0 else 'candidate')
    groups['greyc_fixed']={'title':'Kiểm chứng shrink25 cố định trên GREYC-Web',
        'protocol':'42DEV/21TEST, 21 timing nguồn; ngưỡng riêng từng nhánh theo DEV5%. Phương pháp/tiêu chí khóa trước scoring nguồn mới.',
        'conclusion':'FAR và FRR macro đều tăng;3/21 mã được lợi có guard. Không đạt. GREYC đã được xem sau lượt này.'}
    percentile='results/dev_oof_percentile_results.json'
    for j in range(2):add('percentile','GREYC DEV',percentile,f'/arms/{j}','development_seen_dev','control' if j==0 else 'candidate')
    groups['percentile']={'title':'Phân vị OOF thay mean/SD',
        'protocol':'28calibration/14evaluation từ42DEV đã xem; same detector/probe, cùng ngân sách FAR≤5%, không chia ties.',
        'conclusion':'FRR giảm nhưng FAR tăng;2/14 mã được lợi có guard. Không đạt; giữ kết quả bất lợi.'}
    covariance='results/covariance_control_results.json'
    for j in range(3):add('covariance','GREYC DEV',covariance,f'/arms/{j}','development_seen_dev',('control','candidate','descriptive_reference')[j])
    groups['covariance']={'title':'Giữ/bỏ off-diagonal covariance',
        'protocol':'28/14DEV, cùng LedoitWolf/mean/MAD/CV; full vs diag là chính, Manhattan chỉ tham chiếu.',
        'conclusion':'Full giảm FRR nhưng tăng FAR so diag;4/14 mã được lợi có guard. Cổng B không đạt; chưa chạy nguồn ngoài B.'}
    assert len(rows)==35 and len(groups)==11
    output={'scope':'Saved-artifact synthesis only; not a new experiment or pooled meta-analysis',
            'rows':rows,'groups':groups,'source_sha256':sources,'protected_sha256':protected,
            'decision':'Keep product baseline; stop model/normalizer searches on viewed DEV',
            'release_v3_unchanged':True,'new_data_or_scoring':False}
    (ROOT/(OUTPUT+'.json')).write_text(json.dumps(output,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    with (ROOT/(OUTPUT+'.csv')).open('w',encoding='utf-8',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    lines=['# Tổng hợp đối chứng và chốt hướng nghiên cứu — 15/11/2026','',
           'Tổng hợp **11 nhóm nghiên cứu,35 dòng kết quả đã lưu**. Không chạy thí nghiệm mới, không lựa chọn lại ngưỡng hoặc gộp các nguồn thành một FAR/FRR. Mỗi dòng CSV/JSON có artifact và JSON pointer truy vết. Đây không phải35 thí nghiệm độc lập; một số dòng là nhiều nhánh của cùng phép so sánh.', '',
           '## Quyết định hiện tại','',
           '**Giữ baseline sản phẩm và dừng vòng dò mô hình/chuẩn hóa trên các nguồn đã xem.** Có kết quả thuận lợi cục bộ, nhưng chưa có bằng chứng nhất quán đủ để thay cấu hình hiện tại. Baseline được giữ để bảo toàn phiên bản đã đánh giá, không được coi là đã đủ tốt cho triển khai thực tế.', '',
           '## Bản đồ các nhóm đối chứng','',
           '| Nhóm | Điều kiện cần nhớ | Kết luận trong đúng phạm vi |','|---|---|---|']
    for group,metadata in groups.items():
        lines.append(f"|{metadata['title']}|{metadata['protocol']}|{metadata['conclusion']}|")
    lines+=['','## Bảng kết quả theo từng protocol','',
            'FAR/FRR trong bảng tuân theo cột “Cách tổng hợp”; không xếp hạng các dòng khác protocol. “Mean qua split” không có một mẫu số duy nhất; SD không phải CI. Nhánh tham chiếu không được đổi thành đối chứng chính sau khi thấy số liệu.','',
            '| Nhóm | Nguồn | Nhánh | Cách tổng hợp | FAR | FRR | Vai trò |',
            '|---|---|---|---|---:|---:|---|']
    for r in rows:
        basis={'macro_accounts':'Macro theo mã','pooled':'Pooled','mean_across_splits':'Mean qua split'}.get(r['metric_basis'],r['metric_basis'])
        lines.append(f"|{r['group']}|{r['source']}|{r['variant']}|{basis}|{100*r['far']:.2f}%|{100*r['frr']:.2f}%|{r['role']}|")
    lines+=['','## Không đánh tráo tiêu chí','',
            '- Matched adaptation xét giảm FRR macro và FAR không tăng; CV age-weighted xét giảm FAR macro và FRR không tăng tại cùng ngưỡng z. Hai tiêu chí khác nhau; không dùng một tiêu chí chung để sửa kết luận cũ.',
            '- Shrink25, GREYC fixed, percentile và covariance xét giảm FRR macro/FAR không tăng. Với lợi đa số, đếm tài khoản giảm FRR mà FAR không tăng, không tính hòa là được lợi.',
            '- Full covariance có số đếm thuận lợi hơn Manhattan tham chiếu trên14DEV, nhưng đối chứng chính full−diag không đạt. Chưa có cơ sở đổi câu hỏi sau kết quả rồi gọi là xác nhận cải tiến.',
            '- Khóa code/protocol trước scoring không biến nguồn đã xem thành dữ liệu độc lập mới. GREYC lần đầu dùng cho shrink25 cố định; các chẩn đoán và đối chứng DEV sau đó là phát triển.', '',
            '## Chất lượng dữ liệu và phạm vi suy luận','',
            '- Bộ tự thu601dòng/15mã được đánh giá sơ bộ, chủ yếu một phiên; không có bằng chứng nhiều ngày chỉ vì rubric nội bộ đã đổi task. P10/metadata/provenance vẫn giữ trong báo cáo.',
            '- Audit42DEVGREYC:4.405capture,4.404ghépđược,4.403khớpvector,1mismatch/1unresolved. Tần suất thấp chưa giải thích FRR cao; không sửa raw hoặc loại mã bất lợi.',
            '- UA khác không chứng minh đổi thiết bị; sự phụ thuộc trong người dùng và shared impostor khiến từng lượt không độc lập. Không tạo CI/p-value hoặc kết luận nhân quả từ các bảng mô tả.',
            '- Các protocol static/update/fallback, amount enrollment, lịch probe và cohort khác nhau. Không cộng mẫu số hoặc lấy live0/10 để phủ nhận FAR mô phỏng cao.', '',
            '## Hướng nghiên cứu đã chốt','',
            '1. **Chốt nhánh hiện tại:** v3 vẫn là bản bàn giao đã review; bản tổng hợp này là companion mới ngoài ZIPv3. Không phát sinh mô hình, seed, ngưỡng, estimator hoặc λ khác trong cùng vòng.',
            '2. **Ưu tiên bằng chứng mới hơn công thức mới:** muốn mở lại cải tiến mô hình cần câu hỏi gắn với cơ chế/nhu cầu thực tế, nguồn truy cập hợp lệ và chưa dùng phát triển, protocol/adapter/split/tiêu chí khóa trước scoring. Không hứa kết quả thuận lợi; không gọi CMU/KeyRecs/GREYC đã xem là mới.',
            '3. **Chỉ mở một phép so sánh:** quy định control/candidate, ngân sách FAR, phân bố lợi/hại theo tài khoản và cổng dừng trước. Sau khi thấy điểm, sửa thiết kế nghĩa là phiên bản phát triển mới, phải giữ artifact thất bại.', '',
            'Không có nguồn kiểm chứng mới được chọn hoặc tải trong lượt tổng hợp. Cổng B của covariance đã thất bại nên không tiếp tục nó dưới dạng kiểm chứng. Nếu muốn nghiên cứu full-vs-Manhattan thì là một câu hỏi mới, cần lý do ngoài việc kết quả tham chiếu vừa thuận lợi; không tự triển khai trong lượt này.', '',
            '## Điều kiện mở lại và điểm dừng','',
            '| Điều kiện | Yêu cầu trước khi chấm | Nếu không đủ |','|---|---|---|',
            '|Câu hỏi mới|Có động lực độc lập với bảng điểm vừa xem; một thay đổi kiểm soát được|Giữ kết luận hiện tại|',
            '|Nguồn mới|Điều kiện dùng rõ, provenance/schema phù hợp, đủ enrollment/probe, tách mã/ngày thật|Ghi chưa có bằng chứng, không tạo phiên giả|',
            '|Thử nghiệm|Test giả, freeze code/data/env, acceptance rule/FARbudget/ties/lợi-hại chốt trước|Chưa chạy thật|',
            '|Kết quả|Công bố đầy đủ macro/pooled/counts/mã và mọi bất lợi|Không tune để cứu; không đổi control sau kết quả|',
            '|Triển khai|Có bằng chứng vận hành và hiệu năng phù hợp mục đích|Không suy từ việc chạy local thành đạt thực tế|', '',
            '## Artifact và kiểm tra','',
            'Nguồn vàSHA trong `results/research_decision_20261115.json`;CSV35dòng cópointer tớiartifact. '
            'Tái lập tổng hợp: `python scripts/synthesize_research_decision.py`;kiểm độc lập: `python scripts/validate_research_decision.py`. '
            'Không sửa tổng hợp14/11,report6/37/40/phụlục3trang/ZIPv3. Điểm100nộibộkhôngđổi;khôngpush/deploy/DBwrite.','']
    (ROOT/'docs/RESEARCH_DECISION_20261115.md').write_text('\n'.join(lines),encoding='utf-8')
    assert sources=={n:sha(ROOT/n) for n in sources}
    assert protected=={n:sha(ROOT/n) for n in protected}
    print('SYNTHESIS:11groups/35rows; no fitting or scoring')


if __name__=='__main__':main()
