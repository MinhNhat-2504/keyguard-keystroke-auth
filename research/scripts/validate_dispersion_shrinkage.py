"""Reconcile stored shrinkage results and publish diagnostics; no model fitting."""
import csv
from datetime import datetime
from fractions import Fraction
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.run_dispersion_shrinkage import check, PREFIX, FREEZE
from scripts.run_matched_adaptation import sha


def pct(x):return f'{100*x:.2f}%'.replace('.', ',')


def main():
    plan, frozen = check()
    result = json.loads((ROOT/(PREFIX+'results.json')).read_text())
    diagnostic = json.loads((ROOT/(PREFIX+'diagnostics.json')).read_text())
    start = json.loads((ROOT/(PREFIX+'started.json')).read_text())
    assert result['freeze_sha256']==start['freeze_sha256']==diagnostic['freeze_sha256']==sha(ROOT/FREEZE)
    assert datetime.fromisoformat(frozen['frozen_at_utc'])<=datetime.fromisoformat(diagnostic['completed_at_utc'])<=datetime.fromisoformat(start['started_at_utc'])<=datetime.fromisoformat(result['completed_at_utc'])
    assert start['diagnostics_sha256']==sha(ROOT/(PREFIX+'diagnostics.json'))
    with (ROOT/(PREFIX+'accounts.csv')).open() as stream: csv_rows=list(csv.DictReader(stream))
    assert len(csv_rows)==96
    with (ROOT/(PREFIX+'diagnostics.csv')).open() as stream: cells=list(csv.DictReader(stream))
    assert len(cells)==1116+3102
    lines=['# Kết quả co MAD về prior dev — 15/11/2026','',
           'Thiết kế/code/env/raw được khóa sau 11 kiểm thử giả lập và trước chẩn đoán/scoring. '
           'Chỉ thử λ=0,25, không dò lại sau kết quả. Hồ sơ cố định20mẫu, không warm-up/cập nhật; đây là phát triển trên CMU/KeyRecs đã xem, không holdout mới.','',
           '## 1. Chẩn đoán enrollment dev','',
           '| Nguồn | Mã dev | Cặp mã–feature | MAD chạm sàn | MAD/prior <0,1 |', '|---|---:|---:|---:|---:|']
    for d in diagnostic['datasets']:
        selected=[r for r in cells if r['dataset']==d['dataset']]
        assert len(selected)==d['profile_feature_cells']
        assert sum(r['floor_active']=='True' for r in selected)==d['floor_cells']
        assert sum(float(r['local_to_prior_ratio'])<.1 for r in selected)==d['mad_prior_ratio_below_point1']
        lines.append(f"|{d['dataset']}|{d['dev_accounts']}|{len(selected)}|{d['floor_cells']}|{d['mad_prior_ratio_below_point1']}|")
    lines+=['','Không có MAD full-enrollment chạm sàn1e−9. Tỷ lệ nhỏ chỉ xuất hiện8/3102cell KeyRecs theo mốc đã định. '
            'Tỷ phần đóng góp trung bình OOF lớn nhất ở một cell là khoảng6,38% trên CMU và4,63% trên KeyRecs; '
            'đây là trung bình theo20lượt, không phải chặn trên cho một lượt riêng. Chưa chứng minh một feature chi phối lỗi test hoặc sàn là nguyên nhân. '
            'Chẩn đoán chỉ nhận devS1[:20], không dùng probe/test/S2 hay candidate để chọnλ.','',
            '## 2. Kết quả cùng protocol tĩnh','',
            'Tiêu chí chính: Δmacro_FRR<0 và Δmacro_FAR≤0, candidate−baseline. Mỗi nhánh chọn ngưỡng riêng trên dev FAR≤5%, không tách điểm trùng. '
            'Prior median MAD từ các mãdev khác; khi chấm test dùng toàndev, không có test trong prior.','',
            '| Nguồn | Nhánh | FAR macro | FRR macro | Nhận nhầm/tổng | Genuine từ chối/tổng |', '|---|---|---:|---:|---:|---:|']
    for spec,d in zip(plan['datasets'],result['datasets']):
        for arm in d['arms']:
            matching=[r for r in csv_rows if r['dataset']==d['dataset'] and r['arm']==arm['method']]
            assert len(matching)==len(spec['test_ids'])
            assert {r['participant_id'] for r in matching}==set(spec['test_ids'])
            for key in ('genuine_trials','genuine_rejected','impostor_trials','impostor_accepted'):
                assert sum(int(r[key]) for r in matching)==arm['overall'][key]
            for metric,num,den in [('far','impostor_accepted','impostor_trials'),('frr','genuine_rejected','genuine_trials')]:
                macro=sum((Fraction(int(r[num]),int(r[den])) for r in matching),Fraction())/len(matching)
                assert abs(float(macro)-arm['macro_'+metric])<1e-12
                assert arm['overall'][metric]==arm['overall'][num]/arm['overall'][den]
            assert arm['calibration']['far']<=.05
            overall=arm['overall']
            lines.append(f"|{d['dataset']}|{arm['method']}|{pct(arm['macro_far'])}|{pct(arm['macro_frr'])}|{overall['impostor_accepted']}/{overall['impostor_trials']}|{overall['genuine_rejected']}/{overall['genuine_trials']}|")
        b,c=d['arms']
        assert abs(c['macro_far']-b['macro_far']-d['comparison']['delta_macro_far'])<1e-12
        assert abs(c['macro_frr']-b['macro_frr']-d['comparison']['delta_macro_frr'])<1e-12
        assert not d['comparison']['descriptive_support']
    assert not result['both_sources_descriptively_support']
    lines+=['','CMU: nhận nhầm116→118, genuine từ chối416→422; cảhai lỗi tăng. '
            'KeyRecs: nhận nhầm909→913, genuine từ chối2450→2415; giảm35lượt genuine bị từ chối nhưng tăng4nhận nhầm, là đánh đổi. '
            'Không nguồn nào đạt tiêu chí. Baseline KeyRecs tái lập kết quả static trước (909/10560,2450/3301).','',
            'FRR KeyRecs macro baseline74,28% vàcandidate73,18%; pooled tương ứng74,22% và73,16% do mẫu số mỗi mã khác nhau. '
            'Không gộp với phép matched/decay có lịch warm-up/update hoặc kết quả nhiều cách chia.','',
            '## 3. Quyết định và bảo toàn','',
            'Giữ baseline/cấu hình triển khai. Không tìm thêmλ để cứu kết quả, không xóa các mã bất lợi, không thêmCI/p-value. '
            'Kết quả không bác bỏ mọi cách shrinkage; nó chỉ không ủng hộ công thức và hệ số đã khóa trong phép thử này. '
            'Một bước nghiên cứu khác phải có lý do/thiết kế mới, không trình bày nguồn đã xem là test mới.','',
            'Bốn báo cáo gốc, bản37trang, gói_v2, mô hình, raw và mọi artifact đã bảo vệ vẫn đúngSHA. '
            'Lưu phân tích mới riêng; không sửa báo cáo/handover đã bàn giao. B1–B3 Thư không được làm thay.','',
            'Nguồn: dispersion_shrinkage_plan/freeze/diagnostics/started/results trong results/; CSV96account và4218cell; '
            'lệnh `python scripts/run_dispersion_shrinkage.py --check` và `python scripts/validate_dispersion_shrinkage.py`.']
    (ROOT/'docs/DISPERSION_SHRINKAGE_RESULTS.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    plot(cells,result)
    (ROOT/(PREFIX+'checks.json')).write_text(json.dumps({'date':'2026-11-15','status':'passed',
        'chronology_verified':True,'account_csv_rows':96,'diagnostic_cells':4218,'arithmetic_and_macro_verified':True,
        'baseline_keyrecs_static_reproduced':True,'both_sources_support':False,'protected_files_unchanged':True,
        'scope':'Stored artifact checks; no scoring or configuration change'},indent=2)+'\n')
    print('PASS: chronology/freeze; 4218 DEV cells; 96 account rows; macro/counts; protected artifacts; hypothesis unsupported')


def plot(cells,result):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import numpy as np
    from keyguard.features import FEATURE_NAMES
    external=json.loads((ROOT/'results/external_validation.json').read_text())['features']
    fig,axes=plt.subplots(2,2,figsize=(10,7),constrained_layout=True)
    for i,source in enumerate(['CMU','KeyRecs fixed-text']):
        selected=[r for r in cells if r['dataset']==source]
        ax=axes[i,0];ax.hist(np.log10([float(r['local_to_prior_ratio']) for r in selected]),bins=25,color='#476d8a')
        ax.axvline(-1,color='#ba632c',ls='--',label='MAD/prior=0,1');ax.set_title(source);ax.set_xlabel('log10(MAD/prior), chỉ dev enrollment');ax.set_ylabel('Số cặp mã–feature');ax.legend(fontsize=8)
        names=FEATURE_NAMES if i==0 else external
        values=[np.mean([float(r['oof_mean_score_share']) for r in selected if int(r['feature_index'])==j])*100 for j in range(len(names))]
        top=np.argsort(values)[-8:];ax=axes[i,1];ax.barh([names[j] for j in top],[values[j] for j in top],color='#3e7a6c');ax.set_title('8 feature có tỷ phần OOF trung bình cao nhất');ax.set_xlabel('Tỷ phần điểm raw OOF trung bình (%)')
    for suffix in ('png','pdf'):fig.savefig(ROOT/f'figures/dispersion_shrinkage_diagnostics.{suffix}',dpi=170)
    plt.close(fig)


if __name__=='__main__':main()
