"""Freeze/check the matched runner; real-data scoring requires explicit --run."""
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
import tempfile
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from keyguard.external_validation import read_keyrecs
from keyguard.features import FEATURE_NAMES, load_cmu
from keyguard.matched_adaptation import run_dataset, validate_data


PLAN = 'results/matched_adaptation_plan.json'
FREEZE = 'results/matched_adaptation_runner_freeze.json'
FREEZE_SHA = 'results/matched_adaptation_runner_freeze.sha256'
TEST_REPORT = 'results/matched_adaptation_synthetic_tests.xml'
OUTPUTS = ('results/matched_adaptation_started.json',
           'results/matched_adaptation_results.json',
           'results/matched_adaptation_accounts.csv',
           'results/matched_adaptation_pairs.csv',
           'results/matched_adaptation_deltas.csv')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def environment():
    return {'python': sys.version, 'implementation': platform.python_implementation(),
            'platform': platform.platform(),
            'packages': {name: metadata.version(name) for name in
                         ('numpy', 'pandas', 'scipy', 'scikit-learn', 'pytest')}}


def verify_hashes(root, hashes):
    for name, expected in hashes.items():
        if sha(root / name) != expected:
            raise RuntimeError(f'Hash mismatch: {name}')


def load_plan(root):
    path = root / PLAN
    expected = (root / 'results/matched_adaptation_plan.sha256').read_text().split()[0]
    if sha(path) != expected:
        raise RuntimeError('Plan SHA mismatch')
    plan = json.loads(path.read_text(encoding='utf-8'))
    verify_hashes(root, {plan['protocol_file']: plan['protocol_sha256']})
    verify_hashes(root, plan['provenance']['existing_core_and_preserved_artifact_sha256'])
    verify_hashes(root, {d['raw_file']: d['raw_sha256'] for d in plan['datasets']})
    if (plan['plan_id'] != 'matched-adaptation-s1-s2-v1' or
            plan['arms'] != {'baseline': 'window50', 'candidate': 'decay20'} or
            plan['fixed']['window'] != 50 or plan['fixed']['half_life_in_genuine_samples'] != 20 or
            plan['fixed']['enrollment_first_session1'] != 20 or
            plan['fixed']['cv_folds'] != 5 or plan['fixed']['calibration'] != 'mean_std' or
            plan['fixed']['dev_far_budget'] != .05 or plan['fixed']['sessions_used'] != [1, 2]):
        raise RuntimeError('Runner does not implement this plan')
    return plan


def expected_counts(spec):
    return {key: spec['expected_' + key] for key in
            ('dev_impostor_trials', 'test_genuine_trials', 'test_impostor_trials')}


def load_inputs(root, plan):
    """Audit all inputs/counts BEFORE any model is fitted."""
    loaded = []
    original = json.loads((root / 'results/external_validation_freeze.json').read_text(encoding='utf-8'))
    config = json.loads((root / 'models/model_config.json').read_text(encoding='utf-8'))
    for spec in plan['datasets']:
        if spec['name'] == 'CMU':
            if spec['dev_ids'] != config['dev_users'] or spec['test_ids'] != config['test_users']:
                raise RuntimeError('CMU partitions differ from original config')
            frame = load_cmu(root / spec['raw_file'])
            keys = frame[['subject', 'sessionIndex', 'rep']]
            if keys.duplicated().any():
                raise RuntimeError('Ambiguous CMU keys')
            data = {pid: {s: group.loc[group.sessionIndex == s].sort_values('rep')[FEATURE_NAMES].to_numpy()
                          for s in (1, 2)} for pid, group in frame.groupby('subject')}
            if any(len(sessions[s]) != 50 for sessions in data.values() for s in (1, 2)):
                raise RuntimeError('CMU S1/S2 must have 50 rows per identity')
        elif spec['name'] == 'KeyRecs fixed-text':
            if spec['dev_ids'] != original['dev_ids'] or spec['test_ids'] != original['test_ids']:
                raise RuntimeError('KeyRecs partitions differ from original freeze')
            data, audit = read_keyrecs(root / spec['raw_file'])
            if audit != original['audit']:
                raise RuntimeError('KeyRecs audit/schema differs from original freeze')
        else:
            raise RuntimeError('Unexpected source; do not substitute datasets')
        actual = validate_data(data, spec['dev_ids'], spec['test_ids'], spec['features'])
        if actual != expected_counts(spec):
            raise RuntimeError(f'Counts mismatch for {spec["name"]}')
        loaded.append((spec, data))
    return loaded


def write_json_new(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n')


def guard_new_outputs(root):
    existing = [name for name in OUTPUTS if (root / name).exists()]
    if existing:
        raise RuntimeError(f'Refusing to overwrite or resume existing evaluation: {existing}')


def freeze_runner(root):
    if any((root / name).exists() for name in (FREEZE, FREEZE_SHA, TEST_REPORT)):
        raise RuntimeError('Freeze/test evidence already exists; use --check, never re-freeze silently')
    guard_new_outputs(root)
    plan = load_plan(root)
    load_inputs(root, plan)  # metadata/schema only; no fitted model or scores
    code_names = sorted(str(p.relative_to(root)).replace('\\', '/') for p in (root / 'keyguard').glob('*.py'))
    code_names += ['scripts/run_matched_adaptation.py', 'tests/test_matched_adaptation.py']
    before = {name: sha(root / name) for name in code_names}
    env = environment()
    # Tests are exclusively synthetic; their CLI checks mock scoring/freezing.
    with tempfile.TemporaryDirectory(prefix='keyguard-matched-tests-') as folder:
        report = Path(folder) / 'synthetic.xml'
        result = subprocess.run([sys.executable, '-m', 'pytest',
                                 'tests/test_matched_adaptation.py', '-q',
                                 '-p', 'no:cacheprovider', '--junitxml', str(report)], cwd=root)
        if result.returncode != 0:
            raise RuntimeError('Synthetic tests failed; runner was not frozen')
        suites = list(ET.parse(report).getroot().iter('testsuite'))
        totals = {key: sum(int(s.get(key, '0')) for s in suites)
                  for key in ('tests', 'failures', 'errors', 'skipped')}
        if totals['tests'] == 0 or any(totals[k] for k in ('failures', 'errors', 'skipped')):
            raise RuntimeError('Incomplete synthetic test evidence')
        verify_hashes(root, before)
        load_plan(root)
        if env != environment():
            raise RuntimeError('Environment changed during synthetic tests')
        # Exclusive creation: do not overwrite previous evidence.
        with (root / TEST_REPORT).open('xb') as target:
            target.write(report.read_bytes())
    manifest = {'schema_version': 1, 'state': 'runner_frozen_synthetic_tests_passed_real_scoring_not_started',
                'frozen_at_utc': datetime.now(timezone.utc).isoformat(),
                'plan_sha256': sha(root / PLAN), 'protocol_sha256': plan['protocol_sha256'],
                'code_sha256': before, 'environment': env,
                'synthetic_tests': {**totals, 'file': TEST_REPORT, 'sha256': sha(root / TEST_REPORT)},
                'raw_sha256': {d['raw_file']: d['raw_sha256'] for d in plan['datasets']},
                'no_new_real_scores_at_freeze': True,
                'limitations': 'Existing sources already seen; internal freeze, not public preregistration'}
    write_json_new(root / FREEZE, manifest)
    with (root / FREEZE_SHA).open('x', encoding='ascii') as stream:
        stream.write(sha(root / FREEZE) + '  matched_adaptation_runner_freeze.json\n')
    print(f'FROZEN: {totals["tests"]} synthetic tests; no real-data scoring', flush=True)


def check_freeze(root):
    plan = load_plan(root)
    if sha(root / FREEZE) != (root / FREEZE_SHA).read_text().split()[0]:
        raise RuntimeError('Runner manifest SHA mismatch')
    frozen = json.loads((root / FREEZE).read_text(encoding='utf-8'))
    if sha(root / PLAN) != frozen['plan_sha256'] or plan['protocol_sha256'] != frozen['protocol_sha256']:
        raise RuntimeError('Plan/protocol differs from runner freeze')
    verify_hashes(root, frozen['code_sha256'])
    verify_hashes(root, frozen['raw_sha256'])
    tests = frozen['synthetic_tests']
    verify_hashes(root, {tests['file']: tests['sha256']})
    if frozen['environment'] != environment():
        raise RuntimeError('Environment differs from freeze')
    return plan, frozen


def csv_new(path, rows):
    with path.open('x', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def run_frozen(root):
    guard_new_outputs(root)
    plan, frozen = check_freeze(root)
    datasets = load_inputs(root, plan)
    write_json_new(root / OUTPUTS[0], {'started_at_utc': datetime.now(timezone.utc).isoformat(),
                                     'freeze_sha256': sha(root / FREEZE)})
    results, accounts, pairs, deltas = [], [], [], []
    for spec, data in datasets:
        print(f'SCORING: {spec["name"]}; previously viewed data, development only', flush=True)
        result = run_dataset(data, spec['dev_ids'], spec['test_ids'], spec['features'], expected_counts(spec))
        if spec['existing_schedule_matches']:
            old = json.loads((root / 'results/external_validation.json').read_text(encoding='utf-8'))
            for arm in result['arms']:
                reference = next(item for item in old['adaptation'] if item['id'] == arm['method'])
                for key in ('genuine_trials', 'genuine_rejected', 'impostor_trials', 'impostor_accepted'):
                    if arm['overall'][key] != reference['overall'][key]:
                        raise RuntimeError('KeyRecs count differs from historical run; keep started journal and investigate')
                if arm['calibration']['threshold'] != reference['threshold']:
                    raise RuntimeError('KeyRecs threshold differs from historical run')
                original_accounts = {a['participant_id']: a for a in reference['accounts']}
                for account in arm['accounts']:
                    previous = original_accounts[account['participant_id']]
                    for key in ('genuine_trials', 'genuine_rejected', 'impostor_trials', 'impostor_accepted'):
                        if account[key] != previous[key]:
                            raise RuntimeError('KeyRecs per-account count differs from historical run')
        result['dataset'] = spec['name']
        results.append(result)
        for arm in result['arms']:
            label = {'dataset': spec['name'], 'method': arm['method'], 'threshold': arm['calibration']['threshold']}
            accounts.extend({**label, **row} for row in arm['accounts'])
            pairs.extend({**label, **row} for row in arm['pairs'])
        deltas.extend({'dataset': spec['name'], **row} for row in result['comparison']['accounts'])
    # Recheck before publishing artifacts; leave journal if interrupted/invalid.
    check_freeze(root)
    output = {'freeze_sha256': sha(root / FREEZE), 'plan_sha256': sha(root / PLAN),
              'completed_at_utc': datetime.now(timezone.utc).isoformat(), 'datasets': results,
              'both_sources_descriptively_support': all(r['comparison']['descriptive_support'] for r in results),
              'interpretation': 'Development on viewed data; no inferential/new-holdout claim; no pooling across sources'}
    csv_new(root / OUTPUTS[2], accounts)
    csv_new(root / OUTPUTS[3], pairs)
    csv_new(root / OUTPUTS[4], deltas)
    write_json_new(root / OUTPUTS[1], output)
    print('COMPLETE: separate matched artifacts saved; historical artifacts preserved')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument('--freeze', action='store_true', help='Audit metadata, run synthetic tests, freeze code/environment; no real scores')
    modes.add_argument('--check', action='store_true', help='Read-only verify frozen code/tests/inputs/environment')
    modes.add_argument('--run', action='store_true', help='Explicitly score viewed datasets using the verified freeze')
    args = parser.parse_args(argv)
    if args.freeze:
        freeze_runner(ROOT)
    elif args.check:
        check_freeze(ROOT)
        print('PASS: runner freeze, plan, tests, raw inputs and environment match; no scoring')
    else:
        run_frozen(ROOT)


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    main()
