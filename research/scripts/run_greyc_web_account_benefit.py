"""Freeze/check/run fixed shrink25 on new GREYC-Web source, once only."""
import argparse
import csv
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.run_matched_adaptation import environment
from scripts.dispersion_shrinkage_core import run_dataset
from scripts.account_benefit_summary import analyze_accounts

PREFIX = 'results/greyc_web_account_benefit_'


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def now(): return datetime.now(timezone.utc).isoformat()


def write_new(suffix, value):
    with (ROOT / (PREFIX + suffix)).open('x', encoding='utf-8') as stream:
        json.dump(value, stream, default=serialize, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')


def serialize(value):
    if isinstance(value, Fraction): return {'fraction': str(value), 'value': float(value)}
    raise TypeError(type(value).__name__)


def checked_plan():
    p = json.loads((ROOT / (PREFIX+'plan.json')).read_text())
    for name, expected in [(p['raw_file'], p['raw_sha256']), (p['cache_file'], p['cache_sha256']),
                           (p['protocol_file'], p['protocol_sha256']),
                           (p['adapter_protocol_file'], p['adapter_protocol_sha256'])]:
        assert sha(ROOT / name) == expected, name
    assert len(p['dev_ids']) >= 10 and len(p['test_ids']) >= 5
    assert not set(p['dev_ids']) & set(p['test_ids'])
    return p


def freeze():
    assert not (ROOT / (PREFIX+'freeze.json')).exists()
    p = checked_plan()
    code = list((ROOT / 'keyguard').glob('*.py'))
    code += [ROOT / n for n in ('scripts/account_benefit_summary.py',
             'scripts/prepare_greyc_web_account_benefit.py', 'scripts/run_greyc_web_account_benefit.py',
             'scripts/dispersion_shrinkage_core.py', 'scripts/run_matched_adaptation.py',
             'tests/test_account_benefit_summary.py', 'tests/test_greyc_web_adapter.py',
             'tests/test_dispersion_shrinkage.py')]
    code_hash = {x.relative_to(ROOT).as_posix(): sha(x) for x in code}
    tests = ['tests/test_account_benefit_summary.py', 'tests/test_greyc_web_adapter.py', 'tests/test_dispersion_shrinkage.py']
    run = subprocess.run([sys.executable, '-X', 'utf8', '-m', 'pytest', *tests, '-q', '-p', 'no:cacheprovider'],
                         cwd=ROOT, capture_output=True, text=True, encoding='utf-8')
    print(run.stdout + run.stderr)
    assert run.returncode == 0
    protected = list((ROOT / 'report').glob('*.docx')) + list((ROOT / 'report').glob('*.pdf'))
    protected += list((ROOT / 'handover').glob('*.zip'))
    protected += [ROOT / 'results' / n for n in ('dispersion_shrinkage_results.json', 'dispersion_shrinkage_accounts.csv',
                   'cv_aggregation_control_results.json', 'matched_adaptation_results.json')]
    assert all(sha(ROOT / n) == h for n, h in code_hash.items())
    write_new('synthetic_tests.json', {'completed_at_utc': now(), 'exit_code': run.returncode,
              'stdout': run.stdout, 'stderr': run.stderr, 'test_files': tests})
    write_new('freeze.json', {'frozen_at_utc': now(), 'plan_sha256': sha(ROOT / (PREFIX+'plan.json')),
              'environment': environment(), 'code_sha256': code_hash,
              'protected_sha256': {x.relative_to(ROOT).as_posix(): sha(x) for x in protected},
              'test_report_sha256': sha(ROOT / (PREFIX+'synthetic_tests.json')),
              'scoring_before_freeze': False})
    (ROOT / (PREFIX+'freeze.sha256')).write_text(sha(ROOT / (PREFIX+'freeze.json'))+'\n')
    print('FROZEN; no GREYC model scoring')


def check():
    p = checked_plan()
    f = json.loads((ROOT / (PREFIX+'freeze.json')).read_text())
    assert sha(ROOT / (PREFIX+'freeze.json')) == (ROOT / (PREFIX+'freeze.sha256')).read_text().strip()
    assert f['plan_sha256'] == sha(ROOT / (PREFIX+'plan.json'))
    assert f['environment'] == environment()
    assert f['test_report_sha256'] == sha(ROOT / (PREFIX+'synthetic_tests.json'))
    for name, expected in {**f['code_sha256'], **f['protected_sha256']}.items():
        assert sha(ROOT / name) == expected, name
    return p, f


def run():
    import numpy as np
    p, f = check()
    for suffix in ('started.json', 'results.json', 'accounts.csv'):
        assert not (ROOT / (PREFIX+suffix)).exists(), 'Refuse repeat/overwrite'
    cache = json.loads((ROOT / p['cache_file']).read_text())
    assert set(cache) == set(p['dev_ids']) | set(p['test_ids'])
    data = {}
    for pid, item in cache.items():
        e, t = np.array(item['enrollment']), np.array(item['test'])
        assert e.shape == (20, 21) and t.ndim == 2 and t.shape[1] == 21 and len(t) >= 10
        assert np.isfinite(e).all() and np.isfinite(t).all()
        assert max(d[:10] for d in item['enrollment_timestamps']) < min(d[:10] for d in item['test_timestamps'])
        data[pid] = {1: e, 2: t}
    write_new('started.json', {'started_at_utc': now(), 'freeze_sha256': sha(ROOT / (PREFIX+'freeze.json'))})
    result = run_dataset(data, p['dev_ids'], p['test_ids'])
    baseline, candidate = result['arms']
    summary = analyze_accounts(baseline['accounts'], candidate['accounts'])
    assert baseline['overall']['genuine_trials'] == candidate['overall']['genuine_trials'] == p['test_day_captures_in_test_ids']
    assert baseline['overall']['impostor_trials'] == candidate['overall']['impostor_trials'] == p['test_impostor_trials']
    for m in ('far', 'frr'):
        assert abs(float(summary['delta_macro'][m]) - result['comparison']['delta_macro_'+m]) < 1e-12
    records = [{'dataset': 'GREYC-Web common-password', 'arm': a['method'], **r} for a in result['arms'] for r in a['accounts']]
    with (ROOT / (PREFIX+'accounts.csv')).open('x', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(records[0]))
        writer.writeheader(); writer.writerows(records)
    check()
    write_new('results.json', {'completed_at_utc': now(), 'freeze_sha256': sha(ROOT / (PREFIX+'freeze.json')),
              'dataset': 'GREYC-Web common-password', 'evaluation': result, 'account_benefit': summary,
              'scope': 'Previously unused source in this project; prospective fixed method, no public preregistration or production claim'})
    print(json.dumps({'primary_met': summary['primary_met'], 'broad_benefit_met': summary['broad_benefit_met'],
                     'n_targets': summary['n_targets'], 'guarded_frr_benefit_count': summary['guarded_frr_benefit_count'],
                     'delta_macro': summary['delta_macro']}, default=serialize))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    for option in ('freeze', 'check', 'run'): group.add_argument('--'+option, action='store_true')
    args = parser.parse_args()
    if args.freeze: freeze()
    elif args.check: check(); print('CHECK PASSED; no scoring')
    else: run()
