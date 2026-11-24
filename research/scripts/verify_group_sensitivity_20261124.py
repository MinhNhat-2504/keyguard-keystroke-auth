"""Recount every subset directly from saved decisions, without runner imports."""
import csv,hashlib,json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
def main():
    path=ROOT/'results/group_sensitivity_20261124_results.json'
    result=json.loads(path.read_text(encoding='utf-8'))
    preflight=json.loads((ROOT/'results/calibration_preflight_20261124_results.json').read_text(encoding='utf-8'))
    warnings={(r['phrase'],r['participant_id']):r['review_required'] for r in preflight['profiles']}
    with (ROOT/'results/usn_transfer_20261124_decisions.csv').open(encoding='utf-8',newline='') as f:decisions=list(csv.DictReader(f))
    checks=[('overall',None,None,result['overall'])]
    for axis in ('target','phrase'):
        checks += [('include',axis,r['group'],r) for r in result['by_'+axis]]
        checks += [('exclude',axis,r['excluded'],r) for r in result['leave_one_'+axis+'_out']]
    count=0
    for mode,axis,value,saved in checks:
        totals=dict(genuine_trials=0,attack_trials=0,genuine_additional_verification_before=0,
                    genuine_additional_verification_after=0,attack_behavioral_before=0,attack_behavioral_after=0)
        profiles=set()
        for row in decisions:
            if mode=='include' and row[axis]!=value:continue
            if mode=='exclude' and row[axis]==value:continue
            key=row['phrase'],row['target'];profiles.add(key)
            accepted=row['accepted']=='True';review=warnings[key]
            if row['role']=='genuine':
                totals['genuine_trials']+=1
                totals['genuine_additional_verification_before']+=not accepted
                totals['genuine_additional_verification_after']+=not accepted or review
            elif row['role']=='attack':
                totals['attack_trials']+=1
                totals['attack_behavioral_before']+=accepted
                totals['attack_behavioral_after']+=accepted and not review
            else:raise ValueError('Unknown role')
        totals['profiles']=len(profiles)
        totals['attack_moved_to_extra']=totals['attack_behavioral_before']-totals['attack_behavioral_after']
        totals['genuine_moved_to_extra']=totals['genuine_additional_verification_after']-totals['genuine_additional_verification_before']
        for arm in ('before','after'):
            totals['attack_direct_rate_'+arm]=totals['attack_behavioral_'+arm]/totals['attack_trials']
            totals['genuine_extra_rate_'+arm]=totals['genuine_additional_verification_'+arm]/totals['genuine_trials']
        for k,v in totals.items():assert saved[k]==v,(mode,axis,value,k,saved[k],v)
        count+=1
    record=dict(status='passed',subsets_recounted=count,decisions_read=len(decisions),
                runner_module_imported=False,new_model_experiment=False,
                source_sha256=hashlib.sha256(path.read_bytes()).hexdigest())
    (ROOT/'results/group_sensitivity_20261124_checks.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(record))
if __name__=='__main__':main()
