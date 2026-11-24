"""Freeze, then summarize all predetermined group deletions of saved USN counts."""
import argparse,hashlib,json,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path
from keyguard.group_sensitivity import summarize_groups

ROOT=Path(__file__).resolve().parents[1];P='results/group_sensitivity_20261124_'
FILES=['keyguard/group_sensitivity.py','tests/test_group_sensitivity.py',
       'scripts/run_group_sensitivity_20261124.py','docs/GROUP_SENSITIVITY_PROTOCOL_20261124.md',
       'results/calibration_routing_20261124_results.json',
       'results/usn_transfer_20261124_decisions.csv','results/calibration_preflight_20261124_results.json']
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
now=lambda:datetime.now(timezone.utc).isoformat()
def save(suffix,value):
    with (ROOT/(P+suffix)).open('x',encoding='utf-8') as f:
        json.dump(value,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
def freeze():
    assert not (ROOT/(P+'freeze.json')).exists()
    tests=subprocess.run([sys.executable,'-m','pytest','tests/test_group_sensitivity.py','-q'],cwd=ROOT,capture_output=True,text=True)
    if tests.returncode:raise RuntimeError(tests.stdout+tests.stderr)
    assert '11 passed' in tests.stdout,tests.stdout
    save('synthetic_tests.json',dict(completed_at_utc=now(),returncode=tests.returncode,stdout=tests.stdout))
    save('freeze.json',dict(frozen_at_utc=now(),source_sha256={n:sha(ROOT/n) for n in FILES},
                           tests_sha256=sha(ROOT/(P+'synthetic_tests.json'))))
    print('GROUP AUDIT FROZEN; 11 synthetic tests passed')
def check():
    lock=json.loads((ROOT/(P+'freeze.json')).read_text(encoding='utf-8'))
    for n,h in lock['source_sha256'].items():assert sha(ROOT/n)==h,n
    assert sha(ROOT/(P+'synthetic_tests.json'))==lock['tests_sha256']
def run():
    check();assert not (ROOT/(P+'results.json')).exists()
    source=json.loads((ROOT/'results/calibration_routing_20261124_results.json').read_text(encoding='utf-8'))
    result=summarize_groups(source['profiles'])
    assert result['overall']['profiles']==30 and len(result['targets'])==5 and len(result['phrases'])==6
    for k in ('genuine_trials','attack_trials','genuine_additional_verification_before','genuine_additional_verification_after','attack_behavioral_before','attack_behavioral_after'):
        assert result['overall'][k]==source['overall'][k],k
    check();result.update(completed_at_utc=now(),freeze_sha256=sha(ROOT/(P+'freeze.json')),
                         scope='Retrospective target/phrase deletion sensitivity; not refitting, confidence intervals, or new validation',
                         model_fit_performed=False,new_threshold_chosen=False,independent_trials_claim=False)
    save('results.json',result)
    print(json.dumps({k:v for k,v in result.items() if k in ('overall','leave_one_target_out','leave_one_phrase_out')}))
if __name__=='__main__':
    parser=argparse.ArgumentParser();g=parser.add_mutually_exclusive_group(required=True)
    for mode in ('freeze','check','run'):g.add_argument('--'+mode,action='store_true')
    a=parser.parse_args()
    if a.freeze:freeze()
    elif a.check:check();print('GROUP AUDIT LOCK MATCHES')
    else:run()
