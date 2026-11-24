"""Recount all saved routes with stdlib, independently of the routing module."""
from collections import Counter
import csv
import hashlib
import json
import math
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PREFIX='results/calibration_routing_20261124_'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
    lock=json.loads((ROOT/(PREFIX+'freeze.json')).read_text(encoding='utf-8'))
    result=json.loads((ROOT/(PREFIX+'results.json')).read_text(encoding='utf-8'))
    assert result['freeze_sha256']==sha(ROOT/(PREFIX+'freeze.json'))
    for name,h in lock['source_sha256'].items():assert sha(ROOT/name)==h,name
    assert sha(ROOT/(PREFIX+'synthetic_tests.json'))==lock['synthetic_tests_sha256']
    tests=json.loads((ROOT/(PREFIX+'synthetic_tests.json')).read_text(encoding='utf-8'))
    assert tests['returncode']==0 and '11 passed' in tests['stdout']
    audits=json.loads((ROOT/'results/calibration_preflight_20261124_results.json').read_text(encoding='utf-8'))
    warnings={(p['phrase'],p['participant_id']):p['review_required'] for p in audits['profiles']}
    expected={key:Counter() for key in warnings};seen=set();tau=result['threshold']
    with (ROOT/'results/usn_transfer_20261124_decisions.csv').open(encoding='utf-8',newline='') as stream:
        for row in csv.DictReader(stream):
            key=(row['phrase'],row['target']);role=row['role'];z=float(row['z'])
            assert key in warnings and role in ('genuine','attack') and math.isfinite(z)
            identity=(*key,role,row['source_line']);assert identity not in seen;seen.add(identity)
            before=z<=tau;assert row['accepted']==str(before)
            after=before and not warnings[key]
            c=expected[key];c[role+'_trials']+=1
            for arm,accepted in [('before',before),('after',after)]:
                c[role+'_behavioral_'+arm]+=int(accepted)
                c[role+'_additional_verification_'+arm]+=int(not accepted)
            c[role+'_moved_to_verification']+=int(before and not after)
    total=Counter()
    assert len(result['profiles'])==len(expected)==result['profile_count']==30
    for row in result['profiles']:
        key=(row['phrase'],row['target']);c=expected[key]
        assert row['review_required']==warnings[key]
        for name,count in c.items():assert row[name]==count,(key,name)
        total.update(c)
    for name,count in total.items():assert result['overall'][name]==count,name
    assert len(seen)==result['original_decision_count']==15610
    assert result['overall']['final_attack_acceptance_count_bounds_after']==[total['attack_behavioral_after'],total['attack_trials']]
    assert result['overall']['final_genuine_rejection_count_bounds_after']==[0,total['genuine_additional_verification_after']]
    with (ROOT/(PREFIX+'profiles.csv')).open(encoding='utf-8',newline='') as stream:
        csv_rows=list(csv.DictReader(stream))
    assert len(csv_rows)==30
    for saved,row in zip(csv_rows,result['profiles']):assert all(saved[k]==str(v) for k,v in row.items())
    assert not any(result[k] for k in ('production_changed','scores_or_threshold_changed','otp_success_assumed','model_fit_performed','raw_read','independent_trials_claim'))
    record={'status':'passed','saved_decisions_reconciled':len(seen),'profiles_reconciled':30,
            'attack_moved_to_verification':total['attack_moved_to_verification'],
            'genuine_moved_to_verification':total['genuine_moved_to_verification'],
            'remaining_attack_behavioral_passes':total['attack_behavioral_after'],
            'model_rerun':False,'otp_outcomes_measured':False,
            'scope':'Independent recount of retrospective saved routes, not final authentication efficacy'}
    (ROOT/(PREFIX+'saved_audit.json')).write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(record))
if __name__=='__main__':main()
