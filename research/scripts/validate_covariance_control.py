"""Recompute stored control arithmetic and progression gate; no model scoring."""
import csv
from datetime import datetime
from fractions import Fraction as F
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.run_covariance_control import check,sha,PREFIX


def main():
    check()
    d=json.loads((ROOT/(PREFIX+'results.json')).read_text())
    f=json.loads((ROOT/(PREFIX+'freeze.json')).read_text())
    s=json.loads((ROOT/(PREFIX+'started.json')).read_text())
    tests=json.loads((ROOT/(PREFIX+'tests.json')).read_text())
    assert tests['exit_code']==0 and 'Ran 9 tests' in tests['output']
    assert d['freeze_sha256']==s['freeze_sha256']==sha(ROOT/(PREFIX+'freeze.json'))
    timestamps=[tests['completed_at_utc'],f['frozen_at_utc'],s['started_at_utc'],d['completed_at_utc']]
    assert list(map(datetime.fromisoformat,timestamps))==sorted(map(datetime.fromisoformat,timestamps))
    assert len(s['calibration_ids'])==28 and len(s['evaluation_dev_ids'])==14
    assert not set(s['calibration_ids'])&set(s['evaluation_dev_ids'])
    summaries=[];csvrows=[];macros={}
    for a in d['arms']:
        assert {r['participant_id'] for r in a['accounts']}==set(s['evaluation_dev_ids'])
        assert len(a['accounts'])==14
        assert F(a['calibration_accepted'],a['calibration_trials'])<=F(1,20)
        summary={'method':a['method'],'threshold':a['threshold']}
        macros[a['method']]={}
        for m,n,den in [('far','impostor_accepted','impostor_trials'),('frr','genuine_rejected','genuine_trials')]:
            for r in a['accounts']:assert 0<=r[n]<=r[den] and r[den]>0
            num=sum(r[n] for r in a['accounts']);total=sum(r[den] for r in a['accounts'])
            macro=sum((F(r[n],r[den]) for r in a['accounts']),F())/14
            macros[a['method']][m]=macro
            summary.update({n:num,den:total,'macro_'+m:float(macro),'pooled_'+m:num/total})
        summaries.append(summary)
        csvrows.extend({'method':a['method'],**r} for r in a['accounts'])
    b,c=d['arms'][:2];benefits=0
    for x,y,r in zip(b['accounts'],c['accounts'],d['account_benefit']['accounts']):
        assert x['participant_id']==y['participant_id']==r['participant_id']
        deltas={}
        for m,n,den in [('far','impostor_accepted','impostor_trials'),('frr','genuine_rejected','genuine_trials')]:
            assert x[den]==y[den]
            deltas[m]=F(y[n]-x[n],x[den]);assert deltas[m]==F(r['delta_'+m]['fraction'])
        benefit=deltas['far']<=0 and deltas['frr']<0
        assert r['guarded_frr_benefit']==benefit;benefits+=benefit
    delta={m:macros['full_lw'][m]-macros['diag_lw'][m] for m in ('far','frr')}
    for m in delta:assert delta[m]==F(d['account_benefit']['delta_macro'][m]['fraction'])
    primary=delta['frr']<0 and delta['far']<=0
    broad=primary and benefits>7
    assert d['account_benefit']['primary_met']==primary
    assert d['account_benefit']['broad_benefit_met']==broad
    assert d['stage_b_gate_passed']==(primary and broad)
    assert d['stage_b_status']=='not_started_gate_failed' and not primary
    with (ROOT/(PREFIX+'accounts.csv')).open('w',encoding='utf-8',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(csvrows[0]));writer.writeheader();writer.writerows(csvrows)
    lines=['# Kết quả đối chứng covariance — 15/11/2026','',
           '**Giai đoạnA: phát triển trênDEVđãxem**,28calibration/14evaluation từ42DEVGREYC. Khôngchấm21TESTcũ;chưa cógiaiđoạnB kiểmchứngngoài. Thiếtkế/code/dependencies/inputkhóatrướcrun sau9/9tests.', '',
           'Hai nhánh chính cùng mean/MAD/covarianceLedoitWolf vàruleOOF;chỉ giữ hoặc bỏ off-diagonal. Shrinkage tự tính từ training,khôngsearchtheolabel. Fullscore vàdiagonalscoređều cănkhoảngcáchMahalanobis,khôngnhầmcontrolnàyvớiManhattan.', '',
           '| Nhánh | FAR macro | FRR macro | Nhận nhầm | Genuine bị từ chối |','|---|---:|---:|---:|---:|']
    for r in summaries:
        lines.append(f"|{r['method']}|{100*r['macro_far']:.2f}%|{100*r['macro_frr']:.2f}%|{r['impostor_accepted']}/{r['impostor_trials']}|{r['genuine_rejected']}/{r['genuine_trials']}|")
    lines+=['',f"Phép chính full_lw−diag_lw: ΔFARmacro **{100*float(delta['far']):+.4f}đpt**, ΔFRRmacro **{100*float(delta['frr']):+.4f}đpt**. "
            f"Có **{benefits}/14** mã giảmFRR/FARkhôngtăng. Primary vàlợiđa sốđềukhôngđạt.", '',
            'So với diagonal,full giảm39genuine bịtừchối nhưngtăng15nhậnnhầm. CổngđiBkhôngđạt:khôngtảinguồnkhácđểcứuphươngpháp,khôngthửridge/estimator/seedkhác,giữbấtlợi.', '',
            'So với ScaledManhattan,nhánhfullcó54vs56falseaccept và853vs923genuinereject; đây làthamchiếumôtảđãđịnhkhôngphảitiêuchíchọn. Khôngđổiđốichứngchínhsaukhixemthamsốhoặctuyênbốđãcảitiếnđộclập. MuốnđánhgiáfullvsManhattanlàcâuhỏimớicầnprotocolmới;14DEVnàykhôngthànhholdoutmới.', '',
            '## Chẩn đoán fit','',
            f"Full-enrollment residual rank min/max **{min(r['residual_rank'] for r in d['covariance_diagnostics'])}/{max(r['residual_rank'] for r in d['covariance_diagnostics'])}** trên21chiều; phùhợpviệccácvectorcóquanhệđạisố,khôngchứngminhlànguyênnhânlỗi. "
            f"Shrinkage training trong42DEV: {min(r['shrinkage'] for r in d['covariance_diagnostics']):.4f}–{max(r['shrinkage'] for r in d['covariance_diagnostics']):.4f};khôngđượctunedtheoevaluation.", '',
            '9synthetictestskiểmmatrixformula,diagidentity,n<d/constant/duplicate,trainingfold16/full20,Manhattanparity,noinputmutation/affinescaling,invalidinputvàDEV/TESTdisjoint. NhánhManhattan đã táilập đúngcounts/ngưỡng củaDEVpercentilecũ. Validatorđộclậptínhlạiphânsốmacro/pooled/counts/benefit/gate/chronologytừartifact,khônggọiscoring.', '',
            'Nguồn implementation: [scikit-learnLedoitWolf](https://scikit-learn.org/stable/modules/generated/sklearn.covariance.LedoitWolf.html). '
            'Protocol: COVARIANCE_CONTROL_PROTOCOL.md. Artifact: results/covariance_control_{freeze,tests,started,results,accounts,checks} vàfreeze.sha256. '
            '`python scripts/run_covariance_control.py --check` và `python scripts/validate_covariance_control.py` kiểmkhôngtínhđiểm. Runner từchốighiđèrun.', '',
            '**Giữ cấu hình sản phẩm.** KhôngđổiTEST/raw/report6/37/40/phụlục3trang/ZIPv3/điểm100nộibộ;khôngpush/deploy/DBwrite. KếtquảAkhôngủnghộtiếnBtheocổngđịnhtrước;chưakhẳngđịnhmọiMahalanobisđềukém.','']
    (ROOT/'docs/COVARIANCE_CONTROL_RESULTS.md').write_text('\n'.join(lines),encoding='utf-8')
    checks={'status':'passed','synthetic_tests_passed':9,'accounts_checked_per_arm':14,'arms':3,
            'chronology_verified':True,'stage_b_gate_passed':primary and broad,'stage_b_not_run':True,
            'original_test_used':False,'summary':summaries,'source_result_sha256':sha(ROOT/(PREFIX+'results.json'))}
    (ROOT/(PREFIX+'checks.json')).write_text(json.dumps(checks,indent=2)+'\n')
    check();print(json.dumps(checks))


if __name__=='__main__':main()
