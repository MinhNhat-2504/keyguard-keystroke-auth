"""Prepare/freeze/check/run one fixed-budget selection control on existing DEV."""
import argparse
import csv
from datetime import datetime, timezone
import hashlib
from importlib import metadata
import json
from pathlib import Path
import platform
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
PREFIX='results/enrollment_selection_20261124_'
PROTOCOL='docs/ENROLLMENT_SELECTION_PROTOCOL_20261124.md'
CODE=['keyguard/enrollment_selection.py','scripts/run_enrollment_selection_20261124.py',
      'tests/test_enrollment_selection.py','keyguard/detectors.py','keyguard/evaluation.py',
      'keyguard/features.py','keyguard/external_validation.py','keyguard/soft_weighting.py',
      'keyguard/enrollment_study.py']

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def now():return datetime.now(timezone.utc).isoformat()
def write(suffix,value):
    with (ROOT/(PREFIX+suffix)).open('x',encoding='utf-8') as out:
        json.dump(value,out,ensure_ascii=False,indent=2,allow_nan=False);out.write('\n')
def read(suffix):return json.loads((ROOT/(PREFIX+suffix)).read_text(encoding='utf-8'))
def hashes(paths):return {p:sha(ROOT/p) for p in paths}
def verify(values):
    for name,expected in values.items():
        if sha(ROOT/name)!=expected:raise RuntimeError('Frozen file changed: '+name)
def environment():
    return {'python':sys.version,'platform':platform.platform(),
            'packages':{p:metadata.version(p) for p in ('numpy','pandas','pytest')}}

def prepare():
    from keyguard.enrollment_selection import split_existing_dev
    old=json.loads((ROOT/'results/matched_adaptation_plan.json').read_text(encoding='utf-8'))
    datasets=[]
    for name in ('CMU','KeyRecs'):
        source=next(d for d in old['datasets'] if d['name'].startswith(name))
        calibration,evaluation=split_existing_dev(source['dev_ids'])
        datasets.append({'name':name,'raw_file':source['raw_file'],'raw_sha256':source['raw_sha256'],
                         'existing_dev_ids':source['dev_ids'],'excluded_old_test_ids':source['test_ids'],
                         'calibration_ids':calibration,'evaluation_ids':evaluation})
    plan={'created_at_utc':now(),'protocol':PROTOCOL,'protocol_sha256':sha(ROOT/PROTOCOL),
          'arms':['first10','last10','cover10'],'pool':20,'stored':10,'folds':5,'far_budget':.05,
          'split_seed':20261124,'datasets':datasets,'prior_exposure':'Existing DEV only; not independent new data',
          'new_source_candidate_status':'Provenance/version/usage unresolved; timing not downloaded or scored',
          'new_source_candidate':'https://github.com/sparkins01/keystroke/tree/446aca544357eeba33200f4b749342f29f7b779c',
          'continuation':'Both comparisons on both DEV sources must pass primary and majority benefit gates',
          'scoring_before_freeze':False}
    verify({d['raw_file']:d['raw_sha256'] for d in datasets})
    write('plan.json',plan)
    print('PREPARED metadata-only split; no model scoring')

def freeze():
    plan=read('plan.json');verify({PROTOCOL:plan['protocol_sha256']})
    code=hashes(CODE)
    test=subprocess.run([sys.executable,'-m','pytest','tests/test_enrollment_selection.py','-q','-p','no:cacheprovider'],cwd=ROOT,capture_output=True,text=True,encoding='utf-8')
    print(test.stdout+test.stderr)
    if test.returncode:raise RuntimeError('Synthetic tests failed; no freeze or real-data scoring')
    verify(code)
    protected=[p.relative_to(ROOT).as_posix() for p in (ROOT/'report').glob('*') if p.suffix in ('.docx','.pdf')]
    protected += ['models/model_config.json','results/matched_adaptation_plan.json',
                  'results/dispersion_shrinkage_results.json','results/cv_aggregation_control_results.json']
    write('synthetic_tests.json',{'completed_at_utc':now(),'returncode':test.returncode,'stdout':test.stdout,'stderr':test.stderr})
    write('freeze.json',{'frozen_at_utc':now(),'plan_sha256':sha(ROOT/(PREFIX+'plan.json')),
                        'protocol_sha256':plan['protocol_sha256'],'code_sha256':code,
                        'raw_sha256':{d['raw_file']:d['raw_sha256'] for d in plan['datasets']},
                        'protected_sha256':hashes(protected),'environment':environment(),
                        'test_report_sha256':sha(ROOT/(PREFIX+'synthetic_tests.json')),'real_scoring_before_freeze':False})
    with (ROOT/(PREFIX+'freeze.sha256')).open('x') as out:out.write(sha(ROOT/(PREFIX+'freeze.json'))+'\n')
    print('FROZEN; ready for --run, no real-data scoring yet')

def check():
    f=read('freeze.json')
    assert sha(ROOT/(PREFIX+'freeze.json'))==(ROOT/(PREFIX+'freeze.sha256')).read_text().strip()
    assert f['plan_sha256']==sha(ROOT/(PREFIX+'plan.json'))
    assert f['test_report_sha256']==sha(ROOT/(PREFIX+'synthetic_tests.json'))
    assert f['environment']==environment()
    verify({**f['code_sha256'],**f['raw_sha256'],**f['protected_sha256'],PROTOCOL:f['protocol_sha256']})
    return read('plan.json'),f

def run():
    import numpy as np
    from keyguard.enrollment_selection import run_dataset
    from keyguard.external_validation import read_keyrecs
    plan,lock=check()
    for suffix in ('started.json','results.json','accounts.csv'):
        if (ROOT/(PREFIX+suffix)).exists():raise RuntimeError('Refuse repeated or overwritten run')
    write('started.json',{'started_at_utc':now(),'freeze_sha256':sha(ROOT/(PREFIX+'freeze.json'))})
    results={};records=[]
    for d in plan['datasets']:
        allowed=set(d['existing_dev_ids'])
        if d['name']=='CMU':
            rows={p:{1:[],2:[]} for p in allowed}
            with (ROOT/d['raw_file']).open(encoding='utf-8-sig',newline='') as stream:
                reader=csv.DictReader(stream);features=[x for x in reader.fieldnames if x not in ('subject','sessionIndex','rep')]
                assert len(features)==31
                ordered=sorted(reader,key=lambda r:(r['subject'],int(r['sessionIndex']),int(r['rep'])))
                for r in ordered:
                    if r['subject'] in allowed and int(r['sessionIndex']) in (1,2):
                        rows[r['subject']][int(r['sessionIndex'])].append([float(r[f]) for f in features])
            sessions={p:{s:np.asarray(x) for s,x in ss.items()} for p,ss in rows.items()}
        else:
            all_data,audit=read_keyrecs(ROOT/d['raw_file'])
            assert not audit['excluded']
            sessions={p:all_data[p] for p in allowed}
        data={p:{'pool':ss[1][:20],'future':ss[2]} for p,ss in sessions.items()}
        assert not set(data)&set(d['excluded_old_test_ids'])
        result=run_dataset(data,d['calibration_ids'],d['evaluation_ids'])
        results[d['name']]=result
        for arm,a in result['arms'].items():
            for row in a['accounts']:
                records.append({'dataset':d['name'],'arm':arm,**row,
                                'selected_positions_1based':' '.join(map(str,row['selected_positions_1based']))})
    check()
    with (ROOT/(PREFIX+'accounts.csv')).open('x',encoding='utf-8',newline='') as out:
        writer=csv.DictWriter(out,fieldnames=list(records[0]));writer.writeheader();writer.writerows(records)
    gate=all(d['continuation_gate_met'] for d in results.values())
    write('results.json',{'completed_at_utc':now(),'freeze_sha256':sha(ROOT/(PREFIX+'freeze.json')),
                          'datasets':results,'continuation_gate_met':gate,
                          'new_source_scored':False,'new_source_status':'DEV gate passed; source acceptance still pending' if gate else 'Not opened because the locked DEV continuation gate failed',
                          'production_changed':False,'scope':'Fixed-budget enrollment selection control on previously viewed DEV; no independent validation claim'})
    print(json.dumps({'continuation_gate_met':gate,'datasets':{n:r['cover10_minus_controls'] for n,r in results.items()}}))

if __name__=='__main__':
    parser=argparse.ArgumentParser();group=parser.add_mutually_exclusive_group(required=True)
    for option in ('prepare','freeze','check','run'):group.add_argument('--'+option,action='store_true')
    args=parser.parse_args()
    if args.prepare:prepare()
    elif args.freeze:freeze()
    elif args.check:check();print('FROZEN FILES MATCH')
    elif args.run:run()
