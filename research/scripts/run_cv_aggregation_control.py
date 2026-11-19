"""Freeze/test the CV-only control; scoring requires an explicit --run."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.cv_aggregation_core import evaluate_dataset
from scripts.run_matched_adaptation import (
    check_freeze as check_previous_freeze, csv_new, environment, expected_counts,
    load_inputs, sha, verify_hashes, write_json_new,
)

PLAN = 'results/cv_aggregation_control_plan.json'
FREEZE = 'results/cv_aggregation_control_runner_freeze.json'
FREEZE_SHA = 'results/cv_aggregation_control_runner_freeze.sha256'
TESTS = 'results/cv_aggregation_control_synthetic_tests.xml'
OUTPUTS = tuple('results/cv_aggregation_control_' + suffix for suffix in (
    'started.json', 'results.json', 'accounts.csv', 'pairs.csv', 'deltas.csv', 'transitions.csv'))


def load_plan(root):
    _, previous = check_previous_freeze(root)
    path = root / PLAN
    if sha(path) != (root / 'results/cv_aggregation_control_plan.sha256').read_text().split()[0]:
        raise RuntimeError('CV control plan SHA mismatch')
    plan = json.loads(path.read_text(encoding='utf-8'))
    verify_hashes(root, {plan['protocol_file']: plan['protocol_sha256']})
    verify_hashes(root, plan['provenance']['protected_artifact_sha256'])
    verify_hashes(root, {d['raw_file']: d['raw_sha256'] for d in plan['datasets']})
    fixed = plan['fixed']
    if (plan['plan_id'] != 'cv-aggregation-control-v1' or
            plan['arms'] != {'baseline': 'uniform_cv', 'candidate': 'age_weighted_cv'} or
            fixed['detector'] != 'decay20' or fixed['window'] != 50 or
            fixed['cv_folds'] != 5 or fixed['detector_half_life_genuine_samples'] != 20 or
            fixed['aggregation_half_life_genuine_samples'] != 20 or fixed['scale_floor'] != 1e-6 or
            fixed['threshold_selection'] is not False):
        raise RuntimeError('Runner does not implement this design')
    saved = json.loads((root / 'results/matched_adaptation_results.json').read_text(encoding='utf-8'))
    for spec in plan['datasets']:
        source = next(d for d in saved['datasets'] if d['dataset'] == spec['name'])
        baseline = next(a for a in source['arms'] if a['method'] == 'decay20')
        if (spec['shared_fixed_threshold'] != baseline['calibration']['threshold'] or
                spec['baseline_expected_overall'] != baseline['overall'] or
                spec['baseline_expected_accounts'] != baseline['accounts']):
            raise RuntimeError('Declared baseline differs from prior decay20 result')
    return plan, previous


def guard_outputs(root):
    if any((root / p).exists() for p in OUTPUTS):
        raise RuntimeError('Evaluation/journal exists; never overwrite or resume silently')


def freeze_runner(root):
    if any((root / p).exists() for p in (FREEZE, FREEZE_SHA, TESTS)):
        raise RuntimeError('Freeze evidence exists; use --check, do not silently re-freeze')
    guard_outputs(root)
    plan, previous = load_plan(root)
    load_inputs(root, plan)  # Audit only; no detector fitting or candidate scoring.
    sources = sorted(set(previous['code_sha256']) | {
        'scripts/cv_aggregation_core.py', 'scripts/run_cv_aggregation_control.py',
        'tests/test_cv_aggregation_control.py'})
    hashes = {name: sha(root / name) for name in sources}
    env = environment()
    with tempfile.TemporaryDirectory(prefix='keyguard-cv-control-tests-') as folder:
        report = Path(folder) / 'tests.xml'
        process = subprocess.run([sys.executable, '-m', 'pytest',
                                  'tests/test_cv_aggregation_control.py', '-q', '-p', 'no:cacheprovider',
                                  '--junitxml', str(report)], cwd=root)
        if process.returncode:
            raise RuntimeError('Synthetic tests failed; no freeze created')
        suites = list(ET.parse(report).getroot().iter('testsuite'))
        totals = {k: sum(int(s.get(k, 0)) for s in suites) for k in ('tests', 'failures', 'errors', 'skipped')}
        if not totals['tests'] or any(totals[k] for k in ('failures', 'errors', 'skipped')):
            raise RuntimeError('Incomplete synthetic evidence')
        verify_hashes(root, hashes)
        load_plan(root)
        if env != environment():
            raise RuntimeError('Environment changed during tests')
        with (root / TESTS).open('xb') as stream:
            stream.write(report.read_bytes())
    manifest = {'schema_version': 1,
                'state': 'frozen_after_synthetic_tests_before_real_candidate_scoring',
                'frozen_at_utc': datetime.now(timezone.utc).isoformat(),
                'plan_sha256': sha(root / PLAN), 'protocol_sha256': plan['protocol_sha256'],
                'code_sha256': hashes, 'environment': env,
                'synthetic_tests': {**totals, 'file': TESTS, 'sha256': sha(root / TESTS)},
                'raw_sha256': {d['raw_file']: d['raw_sha256'] for d in plan['datasets']},
                'thresholds': {d['name']: d['shared_fixed_threshold'] for d in plan['datasets']},
                'real_candidate_scores_computed_at_freeze': False,
                'interpretation': 'Internal traceability on previously viewed data, not public preregistration'}
    write_json_new(root / FREEZE, manifest)
    with (root / FREEZE_SHA).open('x', encoding='ascii') as stream:
        stream.write(sha(root / FREEZE) + '  cv_aggregation_control_runner_freeze.json\n')
    print(f'FROZEN: {totals["tests"]} synthetic tests; no real candidate scoring')


def check_freeze(root):
    plan, _ = load_plan(root)
    if sha(root / FREEZE) != (root / FREEZE_SHA).read_text().split()[0]:
        raise RuntimeError('CV control runner manifest SHA mismatch')
    frozen = json.loads((root / FREEZE).read_text(encoding='utf-8'))
    if sha(root / PLAN) != frozen['plan_sha256'] or plan['protocol_sha256'] != frozen['protocol_sha256']:
        raise RuntimeError('Design differs from runner freeze')
    verify_hashes(root, frozen['code_sha256'])
    verify_hashes(root, frozen['raw_sha256'])
    tests = frozen['synthetic_tests']
    verify_hashes(root, {tests['file']: tests['sha256']})
    if environment() != frozen['environment']:
        raise RuntimeError('Environment differs from freeze')
    if frozen['thresholds'] != {d['name']: d['shared_fixed_threshold'] for d in plan['datasets']}:
        raise RuntimeError('Shared thresholds changed')
    return plan, frozen


def verify_baseline(result, spec, reference):
    baseline = result['arms'][0]
    if baseline['threshold'] != spec['shared_fixed_threshold']:
        raise RuntimeError('Fixed threshold changed')
    if baseline['overall'] != spec['baseline_expected_overall'] or baseline['accounts'] != spec['baseline_expected_accounts']:
        raise RuntimeError('Uniform baseline no longer reproduces decay20 account/pooled results')
    if baseline['pairs'] != reference['pairs'] or baseline['observed_dev'] != reference['calibration']:
        raise RuntimeError('Uniform baseline pair/dev counts differ from saved decay20')


def run_frozen(root):
    guard_outputs(root)
    plan, _ = check_freeze(root)
    inputs = load_inputs(root, plan)
    prior = json.loads((root / 'results/matched_adaptation_results.json').read_text(encoding='utf-8'))
    write_json_new(root / OUTPUTS[0], {'started_at_utc': datetime.now(timezone.utc).isoformat(),
                                     'freeze_sha256': sha(root / FREEZE)})
    datasets, accounts, pairs, deltas, transitions = [], [], [], [], []
    for spec, data in inputs:
        print(f'SCORING: {spec["name"]}; fixed shared threshold; viewed data', flush=True)
        result = evaluate_dataset(data, spec['dev_ids'], spec['test_ids'], spec['features'],
                                  expected_counts(spec), spec['shared_fixed_threshold'])
        source = next(d for d in prior['datasets'] if d['dataset'] == spec['name'])
        verify_baseline(result, spec, next(a for a in source['arms'] if a['method'] == 'decay20'))
        result['dataset'] = spec['name']
        datasets.append(result)
        for arm in result['arms']:
            label = {'dataset': spec['name'], 'arm': arm['arm'], 'threshold': arm['threshold']}
            accounts.extend({**label, **row} for row in arm['accounts'])
            pairs.extend({**label, **row} for row in arm['pairs'])
        deltas.extend({'dataset': spec['name'], **r} for r in result['comparison']['accounts'])
        transitions.extend({'dataset': spec['name'], **r} for r in result['pair_transitions'])
    check_freeze(root)
    for file, rows in zip(OUTPUTS[2:], (accounts, pairs, deltas, transitions)):
        csv_new(root / file, rows)
    write_json_new(root / OUTPUTS[1], {'completed_at_utc': datetime.now(timezone.utc).isoformat(),
        'freeze_sha256': sha(root / FREEZE), 'plan_sha256': sha(root / PLAN), 'datasets': datasets,
        'both_sources_descriptively_support': all(d['comparison']['descriptive_support'] for d in datasets),
        'interpretation': 'Normalization rule at fixed baseline z threshold; not equal-dev-FAR or fresh holdout; no inferential claim'})
    print('COMPLETE: new control outputs only; historical artifacts preserved')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--freeze', action='store_true', help='Metadata audit, synthetic tests, code/environment freeze; no real scoring')
    mode.add_argument('--check', action='store_true', help='Read-only verify freeze')
    mode.add_argument('--run', action='store_true', help='Explicit real-data evaluation after freeze')
    args = parser.parse_args(argv)
    if args.freeze:
        freeze_runner(ROOT)
    elif args.check:
        check_freeze(ROOT)
        print('PASS: code/tests/environment/design/inputs/shared thresholds match; no scoring')
    else:
        run_frozen(ROOT)


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    main()
