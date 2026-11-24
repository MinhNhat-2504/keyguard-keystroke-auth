"""Freeze/run an enrollment-only DEV audit with the unchanged preflight rule."""
import argparse
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import numpy as np
from keyguard.calibration_preflight import audit_calibration
from keyguard.dev_enrollment_audit import read_dev_enrollment

ROOT=Path(__file__).resolve().parents[1];P='results/preflight_dev_audit_20261124_'
CODE=['keyguard/calibration_preflight.py','keyguard/detectors.py','keyguard/dev_enrollment_audit.py',
      'tests/test_dev_enrollment_audit.py','scripts/run_preflight_dev_audit_20261124.py',
      'docs/PREFLIGHT_DEV_AUDIT_PROTOCOL_20261124.md','results/matched_adaptation_plan.json']
sha=lambda path:hashlib.sha256(Path(path).read_bytes()).hexdigest()
now=lambda:datetime.now(timezone.utc).isoformat()
def save(suffix,value):
    with (ROOT/(P+suffix)).open('x',encoding='utf-8') as stream:json.dump(value,stream,ensure_ascii=False,indent=2,allow_nan=False);stream.write('\n')
def freeze():
    assert not (ROOT/(P+'freeze.json')).exists()
    tests=subprocess.run([sys.executable,'-m','pytest','tests/test_dev_enrollment_audit.py','tests/test_calibration_preflight.py','-q'],cwd=ROOT,capture_output=True,text=True)
    if tests.returncode:raise RuntimeError(tests.stdout+tests.stderr)
    assert '27 passed' in tests.stdout
    save('synthetic_tests.json',{'completed_at_utc':now(),'returncode':tests.returncode,'stdout':tests.stdout})
    source=json.loads((ROOT/'results/matched_adaptation_plan.json').read_text(encoding='utf-8'))
    datasets=[]
    for item in source['datasets']:
        kind='CMU' if item['name']=='CMU' else 'KeyRecs'
        assert len(item['dev_ids'])==(36 if kind=='CMU' else 66)
        assert not set(item['dev_ids'])&set(item['test_ids'])
        datasets.append({'name':kind,'dev_ids':item['dev_ids'],'excluded_test_ids':item['test_ids'],
                         'raw_file':item['raw_file'],'raw_sha256':item['raw_sha256']})
    assert len(datasets)==2
    save('freeze.json',{'frozen_at_utc':now(),'source_sha256':{n:sha(ROOT/n) for n in CODE},
                        'datasets':datasets,'numpy_version':np.__version__,
                        'tests_sha256':sha(ROOT/(P+'synthetic_tests.json')),
                        'scope':'Existing viewed DEV, enrollment only; no independent validation claim'})
    check();print('DEV AUDIT FROZEN; 27 synthetic tests passed')
def check():
    lock=json.loads((ROOT/(P+'freeze.json')).read_text(encoding='utf-8'))
    assert np.__version__==lock['numpy_version']
    for name,h in lock['source_sha256'].items():assert sha(ROOT/name)==h,name
    for d in lock['datasets']:assert sha(ROOT/d['raw_file'])==d['raw_sha256'],d['name']
    assert sha(ROOT/(P+'synthetic_tests.json'))==lock['tests_sha256']
    return lock
def run():
    lock=check();assert not (ROOT/(P+'results.json')).exists()
    datasets=[]
    for d in lock['datasets']:
        values,meta=read_dev_enrollment(ROOT/d['raw_file'],d['name'],d['dev_ids'])
        profiles=[{'participant_id':pid,**audit_calibration(x).to_dict()} for pid,x in values.items()]
        datasets.append({'name':d['name'],'profile_count':len(profiles),
                         'review_required_count':sum(p['review_required'] for p in profiles),
                         'floor_extrapolation_profile_count':sum(bool(p['floor_extrapolations']) for p in profiles),
                         'degenerate_cv_profile_count':sum(p['cv_std_at_floor'] for p in profiles),
                         'source_audit':meta,'profiles':profiles})
    check()
    result={'completed_at_utc':now(),'freeze_sha256':sha(ROOT/(P+'freeze.json')),'datasets':datasets,
            'profile_count':sum(d['profile_count'] for d in datasets),
            'review_required_count':sum(d['review_required_count'] for d in datasets),
            'enrollment_rows_parsed':sum(d['source_audit']['enrollment_rows_parsed'] for d in datasets),
            'test_decisions_scored':0,'threshold_changed':False,'production_changed':False,
            'scope':'Warning coverage on previously viewed DEV enrollment; not FAR/FRR or false-positive rate'}
    save('results.json',result)
    print(json.dumps({**{k:v for k,v in result.items() if k!='datasets'},'datasets':[ {k:d[k] for k in ('name','profile_count','review_required_count','floor_extrapolation_profile_count','degenerate_cv_profile_count')} for d in datasets]}))
if __name__=='__main__':
    parser=argparse.ArgumentParser();group=parser.add_mutually_exclusive_group(required=True)
    for mode in ('freeze','check','run'):group.add_argument('--'+mode,action='store_true')
    args=parser.parse_args()
    if args.freeze:freeze()
    elif args.check:check();print('DEV AUDIT FROZEN FILES MATCH')
    else:run()
