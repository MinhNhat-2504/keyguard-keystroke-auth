"""Standard-library reconciliation of the saved enrollment-only preflight."""
import hashlib
import json
import math
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PREFIX='results/calibration_preflight_20261124_'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
    freeze=json.loads((ROOT/(PREFIX+'freeze.json')).read_text(encoding='utf-8'))
    result=json.loads((ROOT/(PREFIX+'results.json')).read_text(encoding='utf-8'))
    previous=json.loads((ROOT/'results/usn_oof_diagnostic_20261124.json').read_text(encoding='utf-8'))
    assert result['freeze_sha256']==sha(ROOT/(PREFIX+'freeze.json'))
    for name,h in freeze['source_sha256'].items():assert sha(ROOT/name)==h,name
    assert sha(ROOT/(PREFIX+'synthetic_tests.json'))==freeze['synthetic_tests_sha256']
    tests=json.loads((ROOT/(PREFIX+'synthetic_tests.json')).read_text(encoding='utf-8'))
    assert tests['returncode']==0 and '18 passed' in tests['stdout']
    assert len(result['profiles'])==len(previous['profiles'])==result['profile_count']==30
    warning_count=0;counts={}
    for row,old in zip(result['profiles'],previous['profiles']):
        assert (row['participant_id'],row['phrase'])==(old['participant_id'],old['phrase'])
        assert all(math.isclose(row[k],old[k],rel_tol=1e-12,abs_tol=1e-12) for k in ('cv_center','cv_scale'))
        assert all(math.isclose(a,b,rel_tol=1e-12,abs_tol=1e-12) for a,b in zip(row['oof_scores'],old['oof_scores']))
        assert len(row['oof_scores'])==len(old['oof_scores'])==20
        expected=[(e['fold'],e['feature_index']) for e in old['floored_training_features'] if e['max_held_absolute_deviation']>1e-9]
        actual=[(e['fold'],e['feature_index']) for e in row['floor_extrapolations']]
        assert actual==expected
        assert row['review_required']==(bool(expected) or row['cv_std_at_floor'])
        if row['review_required']:
            warning_count+=1;counts[row['phrase']]=counts.get(row['phrase'],0)+1
    assert warning_count==result['review_required_count']==3
    assert counts==result['warning_counts_by_phrase']
    assert result['enrollment_rows_parsed']==600 and result['test_rows_parsed']==0
    assert not result['test_decisions_changed'] and not result['production_changed']
    record={'status':'passed','profile_summaries_reconciled':30,'review_required_count':warning_count,
            'synthetic_test_cases_passed':18,'raw_rechecked':False,'model_rerun':False,
            'scope':'Saved artifact/code reconciliation only; no efficacy, OTP or deployment acceptance'}
    (ROOT/'results/calibration_preflight_20261124_saved_audit.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(record))
if __name__=='__main__':main()
