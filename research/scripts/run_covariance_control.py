"""One locked DEV covariance control; validation source is gated, not reused TEST."""
import argparse
from datetime import datetime,timezone
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.covariance_control_core import profiles,z_scores,ARMS
from scripts.account_benefit_summary import analyze_accounts
from scripts.run_matched_adaptation import environment
from scripts.run_greyc_web_account_benefit import check as prior_check,serialize
from keyguard.evaluation import threshold_at_far

PREFIX='results/covariance_control_'
CACHE='report/preview/greyc-dev-frr-20261115/dev-only.json'


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def now():return datetime.now(timezone.utc).isoformat()
def create(suffix,data):
    with (ROOT/(PREFIX+suffix)).open('x',encoding='utf-8') as f:json.dump(data,f,default=serialize,indent=2,allow_nan=False);f.write('\n')


def partition(ids,forbidden):
    if len(set(ids))!=len(ids) or set(ids)&set(forbidden):raise ValueError('DEV/TEST identities must be disjoint')
    return [p for i,p in enumerate(ids) if i%3!=2],[p for i,p in enumerate(ids) if i%3==2]


def freeze():
    _,old=prior_check()
    assert not (ROOT/(PREFIX+'freeze.json')).exists()
    code=['scripts/covariance_control_core.py','scripts/run_covariance_control.py','tests/test_covariance_control.py',
          'scripts/account_benefit_summary.py','keyguard/detectors.py','keyguard/evaluation.py',
          'docs/COVARIANCE_CONTROL_PROTOCOL.md',CACHE]
    hashes={n:sha(ROOT/n) for n in code}
    tests=subprocess.run([sys.executable,'-m','unittest','discover','-s','tests','-p','test_covariance_control.py','-v'],
                         cwd=ROOT,capture_output=True,text=True)
    assert tests.returncode==0,tests.stderr
    create('tests.json',{'completed_at_utc':now(),'exit_code':tests.returncode,'output':tests.stdout+tests.stderr})
    protected={n:sha(ROOT/n) for n in old['protected_sha256']}
    for p in list((ROOT/'report').glob('*.docx'))+list((ROOT/'report').glob('*.pdf'))+list((ROOT/'handover').glob('*.zip')):
        protected[p.relative_to(ROOT).as_posix()]=sha(p)
    for n in ['results/greyc_web_account_benefit_results.json','results/dev_oof_percentile_results.json']:
        protected[n]=sha(ROOT/n)
    assert all(sha(ROOT/n)==h for n,h in hashes.items())
    create('freeze.json',{'frozen_at_utc':now(),'input_code_protocol_sha256':hashes,'protected_sha256':protected,
                          'environment':environment(),'tests_sha256':sha(ROOT/(PREFIX+'tests.json')),
                          'real_control_scoring_before_freeze':False,'validation_stage_b_source':None})
    (ROOT/(PREFIX+'freeze.sha256')).write_text(sha(ROOT/(PREFIX+'freeze.json'))+'\n')
    print('FROZEN: synthetic tests passed; no covariance DEV scoring')


def check():
    plan,_=prior_check()
    f=json.loads((ROOT/(PREFIX+'freeze.json')).read_text())
    assert sha(ROOT/(PREFIX+'freeze.json'))==(ROOT/(PREFIX+'freeze.sha256')).read_text().strip()
    assert f['environment']==environment() and f['tests_sha256']==sha(ROOT/(PREFIX+'tests.json'))
    for n,h in {**f['input_code_protocol_sha256'],**f['protected_sha256']}.items():assert sha(ROOT/n)==h,n
    return plan


def run():
    plan=check()
    for suffix in ('started.json','results.json'):assert not (ROOT/(PREFIX+suffix)).exists(),'Refuse overwrite'
    data=json.loads((ROOT/CACHE).read_text());assert set(data)==set(plan['dev_ids'])
    calibration,evaluation=partition(plan['dev_ids'],plan['test_ids']);assert (len(calibration),len(evaluation))==(28,14)
    create('started.json',{'started_at_utc':now(),'freeze_sha256':sha(ROOT/(PREFIX+'freeze.json')),
                           'calibration_ids':calibration,'evaluation_dev_ids':evaluation,'original_test_used':False})
    state={p:profiles(data[p]['enrollment']) for p in data}
    def probes(pid,ids,field):
        return np.vstack([np.vstack((np.array(data[o][field])[:5],np.array(data[o][field])[-5:])) for o in ids if o!=pid])
    arms=[]
    for arm in ARMS:
        score=np.concatenate([z_scores(state[p],probes(p,calibration,'enrollment'),arm) for p in calibration])
        tau=float(threshold_at_far(score,.05));accepted=int(np.count_nonzero(score<=tau))
        assert accepted/len(score)<=.05
        accounts=[]
        for p in evaluation:
            g=z_scores(state[p],data[p]['test'],arm);i=z_scores(state[p],probes(p,evaluation,'test'),arm)
            accounts.append({'participant_id':p,'genuine_trials':len(g),'genuine_rejected':int(np.count_nonzero(g>tau)),
                             'impostor_trials':len(i),'impostor_accepted':int(np.count_nonzero(i<=tau))})
        arms.append({'method':arm,'threshold':tau,'calibration_trials':len(score),'calibration_accepted':accepted,'accounts':accounts})
    # Reproduce previously observed static reference, without revising its results.
    old=json.loads((ROOT/'results/dev_oof_percentile_results.json').read_text())['arms'][0]
    assert arms[2]['accounts']==old['accounts'] and np.isclose(arms[2]['threshold'],old['threshold'],rtol=0,atol=1e-12)
    summary=analyze_accounts(arms[0]['accounts'],arms[1]['accounts'])
    gate=summary['primary_met'] and summary['broad_benefit_met']
    diagnostics=[{'participant_id':pid,'shrinkage':s[0]['shrinkage'],'residual_rank':s[0]['residual_rank'],
                  'full_condition_number':s[0]['full_condition_number'],'diagonal_condition_number':s[0]['diagonal_condition_number']} for pid,s in state.items()]
    check()
    create('results.json',{'completed_at_utc':now(),'freeze_sha256':sha(ROOT/(PREFIX+'freeze.json')),
                           'scope':'StageA previously-viewed DEV only; not independent validation',
                           'arms':arms,'primary_comparison':'full_lw minus diag_lw',
                           'account_benefit':summary,'stage_b_gate_passed':gate,
                           'stage_b_status':'source_selection_not_started' if gate else 'not_started_gate_failed',
                           'covariance_diagnostics':diagnostics,'manhattan_reference_reproduced':True,'original_test_used':False})
    print(json.dumps({'primary_met':summary['primary_met'],'broad_benefit_met':summary['broad_benefit_met'],
                      'benefit_count':summary['guarded_frr_benefit_count'],'stage_b_gate_passed':gate,
                      'delta_macro':summary['delta_macro']},default=serialize))


if __name__=='__main__':
    p=argparse.ArgumentParser();g=p.add_mutually_exclusive_group(required=True)
    for option in ('freeze','check','run'):g.add_argument('--'+option,action='store_true')
    args=p.parse_args()
    if args.freeze:freeze()
    elif args.check:check();print('CHECK PASSED')
    else:run()
