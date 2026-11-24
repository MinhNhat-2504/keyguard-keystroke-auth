"""Frozen retrospective routing analysis of saved decisions; no model scoring."""
import argparse
import csv
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys

from keyguard.calibration_preflight import CalibrationAudit,FoldFloorEvent
from keyguard.calibration_routing import summarize_routes

ROOT=Path(__file__).resolve().parents[1]
PREFIX='results/calibration_routing_20261124_'
FILES=['keyguard/calibration_preflight.py','keyguard/calibration_routing.py',
       'scripts/run_calibration_routing_20261124.py','tests/test_calibration_routing.py',
       'docs/CALIBRATION_ROUTING_PLAN_20261124.md','results/calibration_preflight_20261124_results.json',
       'results/usn_transfer_20261124_decisions.csv','results/usn_transfer_20261124_results.json']
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
now=lambda:datetime.now(timezone.utc).isoformat()
def save(suffix,value):
    with (ROOT/(PREFIX+suffix)).open('x',encoding='utf-8') as stream:
        json.dump(value,stream,ensure_ascii=False,indent=2);stream.write('\n')
def freeze():
    assert not (ROOT/(PREFIX+'freeze.json')).exists()
    test=subprocess.run([sys.executable,'-m','pytest','tests/test_calibration_routing.py','-q'],cwd=ROOT,capture_output=True,text=True)
    if test.returncode:raise RuntimeError(test.stdout+'\n'+test.stderr)
    assert '11 passed' in test.stdout
    save('synthetic_tests.json',{'completed_at_utc':now(),'returncode':test.returncode,'stdout':test.stdout,'stderr':test.stderr})
    save('freeze.json',{'frozen_at_utc':now(),'source_sha256':{n:sha(ROOT/n) for n in FILES},
                        'synthetic_tests_sha256':sha(ROOT/(PREFIX+'synthetic_tests.json')),
                        'scope':'Retrospective accounting after USN and preflight were viewed; not independent validation'})
    print('ROUTING CODE FROZEN; 11 synthetic tests passed')
def check():
    lock=json.loads((ROOT/(PREFIX+'freeze.json')).read_text(encoding='utf-8'))
    for n,h in lock['source_sha256'].items():assert sha(ROOT/n)==h,n
    assert sha(ROOT/(PREFIX+'synthetic_tests.json'))==lock['synthetic_tests_sha256']
    return lock
def run():
    check();assert not (ROOT/(PREFIX+'results.json')).exists()
    preflight=json.loads((ROOT/'results/calibration_preflight_20261124_results.json').read_text(encoding='utf-8'))
    original=json.loads((ROOT/'results/usn_transfer_20261124_results.json').read_text(encoding='utf-8'))
    audits={}
    for p in preflight['profiles']:
        events=tuple(FoldFloorEvent(e['fold'],e['feature_index'],tuple(e['held_rows_1based']),
                                   e['maximum_held_deviation'],e['maximum_contribution']) for e in p['floor_extrapolations'])
        audit=CalibrationAudit(p['feature_count'],p['cv_center'],p['cv_std_unfloored'],p['cv_scale'],
                               tuple(p['oof_scores']),events,p['cv_std_at_floor'])
        assert audit.review_required==p['review_required']
        audits[(p['phrase'],p['participant_id'])]=audit
    with (ROOT/'results/usn_transfer_20261124_decisions.csv').open(encoding='utf-8',newline='') as stream:
        result=summarize_routes(csv.DictReader(stream),audits,original['threshold'])
    assert result['overall']['genuine_trials']==5400 and result['overall']['attack_trials']==10210
    result.update(completed_at_utc=now(),freeze_sha256=sha(ROOT/(PREFIX+'freeze.json')),
                  threshold=original['threshold'],model_fit_performed=False,raw_read=False,
                  original_decision_count=15610,independent_trials_claim=False)
    check();save('results.json',result)
    with (ROOT/(PREFIX+'profiles.csv')).open('x',encoding='utf-8',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(result['profiles'][0]));writer.writeheader();writer.writerows(result['profiles'])
    print(json.dumps({k:v for k,v in result.items() if k!='profiles'}))
if __name__=='__main__':
    parser=argparse.ArgumentParser();group=parser.add_mutually_exclusive_group(required=True)
    for mode in ('freeze','check','run'):group.add_argument('--'+mode,action='store_true')
    args=parser.parse_args()
    if args.freeze:freeze()
    elif args.check:check();print('ROUTING FROZEN FILES MATCH')
    else:run()
