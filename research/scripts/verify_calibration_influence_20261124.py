"""Reconcile the illustrative algebra with population statistics, using stdlib."""
import hashlib
import json
import math
from pathlib import Path
import statistics

ROOT=Path(__file__).resolve().parents[1]
def main():
    data=json.loads((ROOT/'results/calibration_influence_20261124.json').read_text(encoding='utf-8'))
    for name,h in data['source_sha256'].items():
        assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==h,name
    assert data['test_returncode']==0 and '19 passed' in data['test_stdout']
    example=data['example'];n=example['n'];outlier=example['outlier'];tau=example['threshold']
    vector=[0.]*(n-1)+[outlier]
    center=statistics.mean(vector);sigma=statistics.pstdev(vector)
    assert math.isclose(center,example['center'],rel_tol=1e-14)
    assert math.isclose(sigma,example['population_sd'],rel_tol=1e-14)
    assert math.isclose(center+tau*max(sigma,1e-6),example['raw_acceptance_limit'],rel_tol=1e-14)
    assert not example['scale_floor_active'] and sigma>1e-6
    expected=(data['fixed_raw_score_example']-center)/sigma
    assert math.isclose(expected,data['standardized_example'],rel_tol=1e-14)
    big=[0.]*(n-1)+[1e15]
    numerical_limit=(data['fixed_raw_score_example']-statistics.mean(big))/statistics.pstdev(big)
    assert math.isclose(numerical_limit,example['fixed_raw_score_limit_z'],abs_tol=1e-11)
    previous=json.loads((ROOT/'results/usn_oof_diagnostic_20261124.json').read_text(encoding='utf-8'))
    for record in data['real_profile_limits_already_saved']:
        row=next(p for p in previous['profiles'] if p['phrase']=='Ob-dollar-erv3r' and p['participant_id']==record['participant_id'])
        assert record['raw_acceptance_limit']==row['equivalent_raw_score_limit']
    assert not data['model_or_test_decisions_changed'] and not data['production_changed']
    record={'status':'passed','illustrative_population_statistics_reconciled':True,
            'fixed_raw_score_limit_checked_numerically':True,'saved_real_limits_reconciled':3,
            'synthetic_test_cases_passed':19,'model_rerun':False,
            'scope':'Elementary illustrative arithmetic, not novel algorithm or independent model validation'}
    (ROOT/'results/calibration_influence_20261124_saved_audit.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(record))
if __name__=='__main__':main()
