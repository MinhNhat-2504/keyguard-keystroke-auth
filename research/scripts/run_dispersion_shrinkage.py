"""Freeze synthetic tests/code before DEV diagnostics and real-data scoring."""
import argparse
import csv
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.run_matched_adaptation import environment, load_inputs, sha, verify_hashes
from scripts.dispersion_shrinkage_core import diagnose, run_dataset

PREFIX = 'results/dispersion_shrinkage_'
PLAN = PREFIX + 'plan.json'
FREEZE = PREFIX + 'freeze.json'
TESTS = PREFIX + 'synthetic_tests.xml'


def now():return datetime.now(timezone.utc).isoformat()


def create(path, data):
    with (ROOT / path).open('x', encoding='utf-8') as stream:
        stream.write(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False)+'\n')


def plan():
    p = json.loads((ROOT / PLAN).read_text(encoding='utf-8'))
    assert sha(ROOT / PLAN) == (ROOT / (PREFIX+'plan.sha256')).read_text().strip()
    verify_hashes(ROOT, {p['protocol_file']:p['protocol_sha256'], **p['protected_sha256']})
    assert p['lambda']==.25 and p['primary_rule']=='delta_macro_frr < 0 and delta_macro_far <= 0'
    return p


def check():
    p = plan()
    f = json.loads((ROOT / FREEZE).read_text())
    assert sha(ROOT / FREEZE)==(ROOT/(PREFIX+'freeze.sha256')).read_text().strip()
    assert f['plan_sha256']==sha(ROOT/PLAN) and f['environment']==environment()
    verify_hashes(ROOT,{**f['code_sha256'],**f['raw_sha256'],TESTS:f['synthetic_tests_sha256']})
    return p,f


def freeze():
    assert not (ROOT/FREEZE).exists() and not (ROOT/TESTS).exists()
    p = plan()
    code = sorted(str(x.relative_to(ROOT)).replace('\\','/') for x in (ROOT/'keyguard').glob('*.py'))
    code += ['scripts/dispersion_shrinkage_core.py','scripts/run_dispersion_shrinkage.py',
             'scripts/run_matched_adaptation.py','tests/test_dispersion_shrinkage.py']
    before={n:sha(ROOT/n) for n in code}
    run=subprocess.run([sys.executable,'-m','pytest','tests/test_dispersion_shrinkage.py','-q',
                        '-p','no:cacheprovider','--junitxml',str(ROOT/TESTS)],cwd=ROOT)
    assert run.returncode==0
    suites=list(ET.parse(ROOT/TESTS).getroot().iter('testsuite'))
    assert sum(int(x.get('tests','0')) for x in suites)==11
    assert not any(int(x.get(k,'0')) for x in suites for k in ('failures','errors','skipped'))
    verify_hashes(ROOT,before)
    create(FREEZE,{'frozen_at_utc':now(),'plan_sha256':sha(ROOT/PLAN),'environment':environment(),
                   'code_sha256':before,'raw_sha256':{s['raw_file']:s['raw_sha256'] for s in p['datasets']},
                   'synthetic_tests':11,'synthetic_tests_sha256':sha(ROOT/TESTS),
                   'real_data_scoring_before_freeze':False})
    (ROOT/(PREFIX+'freeze.sha256')).write_text(sha(ROOT/FREEZE)+'\n')
    print('FROZEN: 11 synthetic tests; no real model scoring')


def diagnostics():
    p,f=check()
    assert not (ROOT/(PREFIX+'diagnostics.json')).exists()
    output=[]; summaries=[]
    for spec,data in load_inputs(ROOT,p):
        records=diagnose({pid:data[pid][1][:20] for pid in spec['dev_ids']})
        output += [{'dataset':spec['name'],**r} for r in records]
        top=sorted(range(spec['features']),key=lambda j:sum(r['oof_mean_score_share'] for r in records if r['feature_index']==j),reverse=True)[:5]
        summaries.append({'dataset':spec['name'],'dev_accounts':len(spec['dev_ids']),
                          'profile_feature_cells':len(records),'floor_cells':sum(r['floor_active'] for r in records),
                          'mad_prior_ratio_below_point1':sum(r['local_to_prior_ratio']<.1 for r in records),
                          'largest_dev_oof_contribution_feature_indices':top})
    with (ROOT/(PREFIX+'diagnostics.csv')).open('x',encoding='utf-8',newline='') as stream:
        w=csv.DictWriter(stream,fieldnames=list(output[0]));w.writeheader();w.writerows(output)
    create(PREFIX+'diagnostics.json',{'completed_at_utc':now(),'freeze_sha256':sha(ROOT/FREEZE),
                                    'scope':'DEV first20 S1 only; no test or candidate scores','datasets':summaries})
    print(json.dumps(summaries))


def run():
    p,f=check()
    diag=json.loads((ROOT/(PREFIX+'diagnostics.json')).read_text())
    assert diag['freeze_sha256']==sha(ROOT/FREEZE)
    for suffix in ('started.json','results.json','accounts.csv'):
        assert not (ROOT/(PREFIX+suffix)).exists(), 'Refuse overwriting a real-data evaluation'
    create(PREFIX+'started.json',{'started_at_utc':now(),'freeze_sha256':sha(ROOT/FREEZE),
                                 'diagnostics_sha256':sha(ROOT/(PREFIX+'diagnostics.json'))})
    datasets=[]; accounts=[]
    old=json.loads((ROOT/'results/external_validation.json').read_text())
    for spec,data in load_inputs(ROOT,p):
        result=run_dataset(data,spec['dev_ids'],spec['test_ids'])
        result['dataset']=spec['name']
        if spec['name']=='KeyRecs fixed-text':
            assert result['arms'][0]['overall']==old['families'][0]['overall'], 'Static KeyRecs baseline must reproduce'
        for arm in result['arms']:
            assert arm['overall']['genuine_trials']==spec['expected_test_genuine_trials']
            assert arm['overall']['impostor_trials']==spec['expected_test_impostor_trials']
            accounts += [{'dataset':spec['name'],'arm':arm['method'],**r} for r in arm['accounts']]
        datasets.append(result)
    with (ROOT/(PREFIX+'accounts.csv')).open('x',encoding='utf-8',newline='') as stream:
        w=csv.DictWriter(stream,fieldnames=list(accounts[0]));w.writeheader();w.writerows(accounts)
    check()
    create(PREFIX+'results.json',{'completed_at_utc':now(),'freeze_sha256':sha(ROOT/FREEZE),
                                 'datasets':datasets,'both_sources_descriptively_support':all(d['comparison']['descriptive_support'] for d in datasets),
                                 'interpretation':'Development on previously viewed sources; no inference/new holdout/production change'})
    print(json.dumps([{k:d[k] for k in ('dataset','comparison')} for d in datasets]))


if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);g=ap.add_mutually_exclusive_group(required=True)
    for option in ('freeze','check','diagnose','run'):g.add_argument('--'+option,action='store_true')
    args=ap.parse_args()
    if args.freeze:freeze()
    elif args.check:check();print('CHECK PASSED: code/design/environment/raw/protected artifacts unchanged')
    elif args.diagnose:diagnostics()
    else:run()
