"""Locked retrospective preflight audit; parse enrollment rows only, no test scoring."""
import argparse
from collections import Counter
import csv
from datetime import datetime, timezone
import hashlib
from itertools import islice
import json
from pathlib import Path
import subprocess
import sys

import numpy as np
from keyguard.calibration_preflight import audit_calibration

ROOT=Path(__file__).resolve().parents[1]
PREFIX='results/calibration_preflight_20261124_'
FILES=['keyguard/calibration_preflight.py','keyguard/detectors.py',
       'scripts/run_calibration_preflight_20261124.py','tests/test_calibration_preflight.py',
       'docs/CALIBRATION_PREFLIGHT_PLAN_20261124.md',
       'results/usn_source_manifest_20261124.json','results/usn_oof_diagnostic_20261124.json']
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
now=lambda:datetime.now(timezone.utc).isoformat()
def save(suffix,value):
    with (ROOT/(PREFIX+suffix)).open('x',encoding='utf-8') as stream:
        json.dump(value,stream,ensure_ascii=False,indent=2);stream.write('\n')
def freeze():
    assert not (ROOT/(PREFIX+'freeze.json')).exists()
    test=subprocess.run([sys.executable,'-m','pytest','tests/test_calibration_preflight.py','-q'],
                        cwd=ROOT,capture_output=True,text=True)
    if test.returncode:raise RuntimeError(test.stdout+'\n'+test.stderr)
    assert '18 passed' in test.stdout
    save('synthetic_tests.json',{'completed_at_utc':now(),'returncode':test.returncode,
                               'stdout':test.stdout,'stderr':test.stderr})
    source=json.loads((ROOT/'results/usn_source_manifest_20261124.json').read_text(encoding='utf-8'))
    raw={r['file']:r['sha256'] for r in source['files'] if Path(r['file']).name.startswith('participant')}
    assert len(raw)==30
    save('freeze.json',{'frozen_at_utc':now(),'source_sha256':{n:sha(ROOT/n) for n in FILES},
                        'raw_sha256':raw,'numpy_version':np.__version__,
                        'synthetic_tests_sha256':sha(ROOT/(PREFIX+'synthetic_tests.json')),
                        'scope':'Retrospective engineering rule after USN was viewed; not preregistered efficacy testing'})
    print('PREFLIGHT CODE FROZEN; 18 synthetic tests passed')
def check():
    lock=json.loads((ROOT/(PREFIX+'freeze.json')).read_text(encoding='utf-8'))
    assert lock['numpy_version']==np.__version__
    for n,h in {**lock['source_sha256'],**lock['raw_sha256']}.items():assert sha(ROOT/n)==h,n
    assert sha(ROOT/(PREFIX+'synthetic_tests.json'))==lock['synthetic_tests_sha256']
    return lock
def run():
    lock=check()
    assert not (ROOT/(PREFIX+'results.json')).exists()
    old=json.loads((ROOT/'results/usn_oof_diagnostic_20261124.json').read_text(encoding='utf-8'))
    profiles=[]
    for previous in old['profiles']:
        pid,phrase=previous['participant_id'],previous['phrase']
        name=f'data/raw/usn_fixed_text_v1/{pid} - {phrase}.csv'
        assert name in lock['raw_sha256']
        with (ROOT/name).open(encoding='utf-8-sig',newline='') as stream:
            reader=csv.reader(stream);header=next(reader);fields=list(islice(reader,20))
        assert len(fields)==20 and all(len(row)==len(header) for row in fields)
        result=audit_calibration([[float(v) for v in row] for row in fields])
        assert np.isclose(result.cv_center,previous['cv_center'],rtol=1e-12,atol=1e-12)
        assert np.isclose(result.cv_scale,previous['cv_scale'],rtol=1e-12,atol=1e-12)
        row={'participant_id':pid,'phrase':phrase,**result.to_dict()}
        for event in row['floor_extrapolations']:event['feature_name']=header[event['feature_index']]
        profiles.append(row)
    warnings=[p for p in profiles if p['review_required']]
    check()
    output={'completed_at_utc':now(),'freeze_sha256':sha(ROOT/(PREFIX+'freeze.json')),
            'profile_count':len(profiles),'review_required_count':len(warnings),
            'warning_counts_by_phrase':dict(sorted(Counter(p['phrase'] for p in warnings).items())),
            'fold_extrapolation_profile_count':sum(bool(p['floor_extrapolations']) for p in profiles),
            'degenerate_cv_profile_count':sum(p['cv_std_at_floor'] for p in profiles),
            'enrollment_rows_parsed':20*len(profiles),'test_rows_parsed':0,
            'original_cv_summaries_reproduced':True,'test_decisions_changed':False,
            'production_changed':False,'no_warning_is_safety_certificate':False,
            'scope':'Retrospective enrollment-only warning coverage; no new FAR/FRR, OTP success or security claim',
            'profiles':profiles}
    save('results.json',output)
    print(json.dumps({k:v for k,v in output.items() if k!='profiles'}))
if __name__=='__main__':
    parser=argparse.ArgumentParser();group=parser.add_mutually_exclusive_group(required=True)
    for mode in ('freeze','check','run'):group.add_argument('--'+mode,action='store_true')
    args=parser.parse_args()
    if args.freeze:freeze()
    elif args.check:check();print('PREFLIGHT FROZEN FILES MATCH')
    else:run()
