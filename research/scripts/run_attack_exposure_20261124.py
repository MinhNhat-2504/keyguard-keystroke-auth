"""Freeze and count distinct attack samples using fixed saved decisions."""
import argparse,csv,hashlib,json,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path
from keyguard.attack_exposure import summarize_exposure

ROOT=Path(__file__).resolve().parents[1];P='results/attack_exposure_20261124_'
FILES=['keyguard/attack_exposure.py','tests/test_attack_exposure.py','scripts/run_attack_exposure_20261124.py',
       'docs/ATTACK_EXPOSURE_PROTOCOL_20261124.md','results/usn_transfer_20261124_decisions.csv',
       'results/usn_transfer_20261124_results.json','results/calibration_preflight_20261124_results.json',
       'results/calibration_routing_20261124_results.json']
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
now=lambda:datetime.now(timezone.utc).isoformat()
def save(suffix,value):
    with (ROOT/(P+suffix)).open('x',encoding='utf-8') as f:
        json.dump(value,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
def freeze():
    assert not (ROOT/(P+'freeze.json')).exists()
    test=subprocess.run([sys.executable,'-m','pytest','tests/test_attack_exposure.py','-q'],cwd=ROOT,capture_output=True,text=True)
    if test.returncode:raise RuntimeError(test.stdout+test.stderr)
    assert '11 passed' in test.stdout,test.stdout
    save('synthetic_tests.json',dict(completed_at_utc=now(),returncode=test.returncode,stdout=test.stdout))
    save('freeze.json',dict(frozen_at_utc=now(),source_sha256={n:sha(ROOT/n) for n in FILES},tests_sha256=sha(ROOT/(P+'synthetic_tests.json'))))
    print('ATTACK EXPOSURE FROZEN; 11 synthetic tests passed')
def check():
    lock=json.loads((ROOT/(P+'freeze.json')).read_text(encoding='utf-8'))
    for name,h in lock['source_sha256'].items():assert sha(ROOT/name)==h,name
    assert sha(ROOT/(P+'synthetic_tests.json'))==lock['tests_sha256']
def run():
    check();assert not (ROOT/(P+'results.json')).exists()
    read=lambda n:json.loads((ROOT/n).read_text(encoding='utf-8'))
    warnings={(p['phrase'],p['participant_id']):p['review_required'] for p in read('results/calibration_preflight_20261124_results.json')['profiles']}
    with (ROOT/'results/usn_transfer_20261124_decisions.csv').open(encoding='utf-8',newline='') as f:
        r=summarize_exposure(csv.DictReader(f),warnings,read('results/usn_transfer_20261124_results.json')['threshold'])
    original=read('results/calibration_routing_20261124_results.json')['overall']
    assert r['overall']['distinct_attack_samples']==2042 and r['overall']['target_decisions']==10210 and r['target_count_per_sample']==5
    for arm in ('before','after'):assert r['overall']['accepted_target_decisions_'+arm]==original['attack_behavioral_'+arm]
    check();r.update(completed_at_utc=now(),freeze_sha256=sha(ROOT/(P+'freeze.json')),
                     model_fit_performed=False,new_threshold_chosen=False,independent_trials_claim=False,
                     scope='Retrospective fixed five-target any-profile exposure; not single-target FAR or post-OTP success')
    save('results.json',r);print(json.dumps(r))
if __name__=='__main__':
    parser=argparse.ArgumentParser();g=parser.add_mutually_exclusive_group(required=True)
    for mode in ('freeze','check','run'):g.add_argument('--'+mode,action='store_true')
    a=parser.parse_args()
    if a.freeze:freeze()
    elif a.check:check();print('EXPOSURE LOCK MATCHES')
    else:run()
