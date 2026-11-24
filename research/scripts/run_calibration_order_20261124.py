"""Freeze/run five fixed orderings on existing enrollment pools only."""
import argparse,csv,hashlib,json,platform,statistics,subprocess,sys
from datetime import datetime,timezone
from itertools import islice
from pathlib import Path
import numpy as np
from keyguard.calibration_order_audit import audit_orderings
from keyguard.dev_enrollment_audit import read_dev_enrollment

ROOT=Path(__file__).resolve().parents[1];P='results/calibration_order_20261124_'
CODE=['keyguard/calibration_order_audit.py','keyguard/calibration_preflight.py','keyguard/detectors.py',
      'keyguard/dev_enrollment_audit.py','tests/test_calibration_order_audit.py','scripts/run_calibration_order_20261124.py',
      'docs/CALIBRATION_ORDER_PROTOCOL_20261124.md','results/preflight_dev_audit_20261124_freeze.json',
      'results/preflight_dev_audit_20261124_results.json','results/calibration_preflight_20261124_freeze.json',
      'results/calibration_preflight_20261124_results.json','results/usn_transfer_20261124_results.json']
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
now=lambda:datetime.now(timezone.utc).isoformat()
read=lambda n:json.loads((ROOT/n).read_text(encoding='utf-8'))
def save(suffix,obj):
    with (ROOT/(P+suffix)).open('x',encoding='utf-8') as stream:json.dump(obj,stream,ensure_ascii=False,indent=2,allow_nan=False);stream.write('\n')
def freeze():
    assert not (ROOT/(P+'freeze.json')).exists()
    tests=subprocess.run([sys.executable,'-m','pytest','tests/test_calibration_order_audit.py','-q'],cwd=ROOT,capture_output=True,text=True)
    if tests.returncode:raise RuntimeError(tests.stdout+tests.stderr)
    assert '7 passed' in tests.stdout
    save('synthetic_tests.json',{'completed_at_utc':now(),'returncode':tests.returncode,'stdout':tests.stdout})
    dev=read('results/preflight_dev_audit_20261124_freeze.json')
    usn=read('results/calibration_preflight_20261124_freeze.json')
    raw=dict(usn['raw_sha256']);raw.update({d['raw_file']:d['raw_sha256'] for d in dev['datasets']})
    save('freeze.json',{'frozen_at_utc':now(),'source_sha256':{n:sha(ROOT/n) for n in CODE},'raw_sha256':raw,
                        'tests_sha256':sha(ROOT/(P+'synthetic_tests.json')),'numpy_version':np.__version__,
                        'python_version':platform.python_version(),'scope':'Viewed enrollment only; sensitivity audit, not new validation or policy'})
    check();print('ORDER AUDIT FROZEN; 7 synthetic tests passed')
def check():
    lock=read(P+'freeze.json');assert lock['numpy_version']==np.__version__
    assert lock['python_version']==platform.python_version()
    for name,h in {**lock['source_sha256'],**lock['raw_sha256']}.items():assert sha(ROOT/name)==h,name
    assert sha(ROOT/(P+'synthetic_tests.json'))==lock['tests_sha256']
    return lock
def load_enrollment():
    dev=read('results/preflight_dev_audit_20261124_freeze.json')
    old=read('results/preflight_dev_audit_20261124_results.json');pools=[]
    for d,previous in zip(dev['datasets'],old['datasets']):
        values,_=read_dev_enrollment(ROOT/d['raw_file'],d['name'],d['dev_ids'])
        prior={p['participant_id']:p for p in previous['profiles']}
        for pid,x in values.items():pools.append((d['name'],'',pid,x,prior[pid]))
    usn=read('results/calibration_preflight_20261124_results.json')
    for p in usn['profiles']:
        file=ROOT/f"data/raw/usn_fixed_text_v1/{p['participant_id']} - {p['phrase']}.csv"
        with file.open(encoding='utf-8-sig',newline='') as stream:
            reader=csv.reader(stream);header=next(reader);rows=list(islice(reader,20))
        assert len(rows)==20 and all(len(row)==len(header) for row in rows)
        pools.append(('USN',p['phrase'],p['participant_id'],np.asarray(rows,dtype=float),p))
    return pools
def run():
    check();assert not (ROOT/(P+'results.json')).exists()
    tau=read('results/usn_transfer_20261124_results.json')['threshold'];profiles=[]
    for dataset,phrase,pid,x,prior in load_enrollment():
        result=audit_orderings(x,tau);base=result['cases'][0]
        assert np.isclose(base['cv_center'],prior['cv_center'],rtol=1e-12,atol=1e-12)
        assert np.isclose(base['cv_scale'],prior['cv_scale'],rtol=1e-12,atol=1e-12)
        assert base['review_required']==prior['review_required']
        profiles.append({'dataset':dataset,'phrase':phrase,'participant_id':pid,**result})
    summaries=[]
    for name in ('CMU','KeyRecs','USN'):
        rows=[r for r in profiles if r['dataset']==name];ratios=[r['raw_limit_max_min_ratio'] for r in rows if r['raw_limit_max_min_ratio'] is not None]
        summaries.append({'dataset':name,'profiles':len(rows),
                          'warning_counts_by_ordering':{c['ordering']:sum(r['cases'][i]['review_required'] for r in rows) for i,c in enumerate(rows[0]['cases'])},
                          'warning_changed_profiles':sum(r['warning_changes_across_orderings'] for r in rows),
                          'reverse_control_close_profiles':sum(r['reverse_control_close'] for r in rows),
                          'raw_limit_ratio_median':statistics.median(ratios),'raw_limit_ratio_max':max(ratios)})
    check();result={'completed_at_utc':now(),'freeze_sha256':sha(ROOT/(P+'freeze.json')),
                    'threshold':tau,'profiles':profiles,'summaries':summaries,'profile_count':len(profiles),
                    'ordering_case_count':sum(len(p['cases']) for p in profiles),'enrollment_samples':20*len(profiles),
                    'test_decisions_scored':0,'threshold_or_policy_changed':False,'production_changed':False,
                    'independent_validation_claim':False,'scope':'Fixed enrollment-only sensitivity audit; original scoring decisions unchanged'}
    assert len(profiles)==132 and result['ordering_case_count']==660
    save('results.json',result)
    print(json.dumps({'summaries':summaries,'changed_profiles':[{'dataset':p['dataset'],'phrase':p['phrase'],'participant_id':p['participant_id'],
                                                              'flags':{c['ordering']:c['review_required'] for c in p['cases']},'ratio':p['raw_limit_max_min_ratio']}
                                                             for p in profiles if p['warning_changes_across_orderings']]}))
if __name__=='__main__':
    parser=argparse.ArgumentParser();group=parser.add_mutually_exclusive_group(required=True)
    for mode in ('freeze','check','run'):group.add_argument('--'+mode,action='store_true')
    args=parser.parse_args()
    if args.freeze:freeze()
    elif args.check:check();print('ORDER AUDIT FROZEN FILES MATCH')
    else:run()
