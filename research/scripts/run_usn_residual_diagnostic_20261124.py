"""Fixed retrospective description of every saved USN profile, without raw."""
import argparse,csv,hashlib,json,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path
from keyguard.residual_score_diagnostic import summarize_saved_scores

ROOT=Path(__file__).resolve().parents[1];P='results/usn_residual_diagnostic_20261124_'
CODE=['keyguard/residual_score_diagnostic.py','tests/test_residual_score_diagnostic.py',
      'scripts/run_usn_residual_diagnostic_20261124.py','docs/USN_RESIDUAL_DIAGNOSTIC_PROTOCOL_20261124.md',
      'results/usn_transfer_20261124_decisions.csv','results/usn_transfer_20261124_results.json',
      'results/usn_oof_diagnostic_20261124.json','results/calibration_preflight_20261124_results.json']
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
now=lambda:datetime.now(timezone.utc).isoformat()
def save(suffix,value):
    with (ROOT/(P+suffix)).open('x',encoding='utf-8') as stream:json.dump(value,stream,ensure_ascii=False,indent=2,allow_nan=False);stream.write('\n')
def freeze():
    assert not (ROOT/(P+'freeze.json')).exists()
    tests=subprocess.run([sys.executable,'-m','pytest','tests/test_residual_score_diagnostic.py','-q'],cwd=ROOT,capture_output=True,text=True)
    if tests.returncode:raise RuntimeError(tests.stdout+tests.stderr)
    assert '12 passed' in tests.stdout
    save('synthetic_tests.json',{'completed_at_utc':now(),'returncode':tests.returncode,'stdout':tests.stdout})
    save('freeze.json',{'frozen_at_utc':now(),'source_sha256':{n:sha(ROOT/n) for n in CODE},
                        'tests_sha256':sha(ROOT/(P+'synthetic_tests.json')),'scope':'Retrospective description, no threshold search or independent validation'})
    print('RESIDUAL DIAGNOSTIC FROZEN; 12 synthetic tests passed')
def check():
    lock=json.loads((ROOT/(P+'freeze.json')).read_text(encoding='utf-8'))
    for name,h in lock['source_sha256'].items():assert sha(ROOT/name)==h,name
    assert sha(ROOT/(P+'synthetic_tests.json'))==lock['tests_sha256']
    return lock
def run():
    check();assert not (ROOT/(P+'results.json')).exists()
    read=lambda n:json.loads((ROOT/n).read_text(encoding='utf-8'))
    audits=read('results/calibration_preflight_20261124_results.json')
    oof=read('results/usn_oof_diagnostic_20261124.json')
    original=read('results/usn_transfer_20261124_results.json')
    warnings={(a['phrase'],a['participant_id']):a['review_required'] for a in audits['profiles']}
    prior={(a['phrase'],a['participant_id']):a for a in oof['profiles']}
    with (ROOT/'results/usn_transfer_20261124_decisions.csv').open(encoding='utf-8',newline='') as stream:
        result=summarize_saved_scores(csv.DictReader(stream),warnings,original['threshold'],prior)
    assert result['decisions_count']==15610 and result['remaining_attack_behavioral_passes']==374
    check();result.update(completed_at_utc=now(),freeze_sha256=sha(ROOT/(P+'freeze.json')),
                         threshold=original['threshold'],new_threshold_chosen=False,raw_read=False,
                         model_fit_performed=False,production_changed=False,independent_trials_claim=False,
                         scope='Descriptive retrospective rank/operating-point diagnosis on all saved profiles')
    save('results.json',result)
    for suffix,rows in [('accounts.csv',result['accounts']),('phrases.csv',result['phrases']),('pairs.csv',result['residual_pairs'])]:
        with (ROOT/(P+suffix)).open('x',encoding='utf-8',newline='') as stream:
            writer=csv.DictWriter(stream,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    print(json.dumps({'decisions_count':result['decisions_count'],'remaining':374,'phrases':result['phrases'],
                      'accounts':[{'phrase':a['phrase'],'target':a['target'],'auc':a['auc'],
                                   'remaining':a['attack_behavioral_passes_after_guard'],'largest_oof_share':a['largest_oof_share']}
                                  for a in sorted(result['accounts'],key=lambda a:-a['attack_behavioral_passes_after_guard'])[:6]]}))
if __name__=='__main__':
    parser=argparse.ArgumentParser();group=parser.add_mutually_exclusive_group(required=True)
    for mode in ('freeze','check','run'):group.add_argument('--'+mode,action='store_true')
    args=parser.parse_args()
    if args.freeze:freeze()
    elif args.check:check();print('RESIDUAL FROZEN FILES MATCH')
    else:run()
