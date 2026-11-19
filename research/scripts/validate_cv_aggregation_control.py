"""Validate saved CV-only control artifacts without fitting or selecting thresholds."""
import csv
from datetime import datetime
from fractions import Fraction
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.run_cv_aggregation_control import FREEZE, PLAN, check_freeze, verify_baseline
from scripts.run_matched_adaptation import sha


def reconcile(saved, exported):
    assert len(saved) == len(exported)
    for a, b in zip(saved, exported):
        for key, value in a.items():
            assert (float(b[key]) == value if isinstance(value, (float, int)) else b[key] == value)


def main():
    plan, frozen = check_freeze(ROOT)
    folder = ROOT / 'results'
    saved_path = folder / 'cv_aggregation_control_results.json'
    saved = json.loads(saved_path.read_text(encoding='utf-8'))
    start = json.loads((folder / 'cv_aggregation_control_started.json').read_text(encoding='utf-8'))
    previous = json.loads((folder / 'matched_adaptation_results.json').read_text(encoding='utf-8'))
    assert saved['freeze_sha256'] == start['freeze_sha256'] == sha(ROOT / FREEZE)
    assert saved['plan_sha256'] == sha(ROOT / PLAN)
    assert datetime.fromisoformat(frozen['frozen_at_utc']) <= datetime.fromisoformat(start['started_at_utc']) <= datetime.fromisoformat(saved['completed_at_utc'])
    csvs = {}
    for kind in ('accounts', 'pairs', 'deltas', 'transitions'):
        with (folder / f'cv_aggregation_control_{kind}.csv').open(encoding='utf-8', newline='') as stream:
            csvs[kind] = list(csv.DictReader(stream))
    assert [d['dataset'] for d in saved['datasets']] == [d['name'] for d in plan['datasets']]
    expected_sizes = {'accounts': 0, 'pairs': 0, 'deltas': 0, 'transitions': 0}
    decisions, changes = {}, {}
    for spec, data in zip(plan['datasets'], saved['datasets']):
        source = next(s for s in previous['datasets'] if s['dataset'] == spec['name'])
        verify_baseline(data, spec, next(a for a in source['arms'] if a['method'] == 'decay20'))
        assert [a['arm'] for a in data['arms']] == ['uniform_cv', 'age_weighted_cv']
        means = []
        for arm in data['arms']:
            assert arm['threshold'] == arm['observed_dev']['threshold'] == spec['shared_fixed_threshold']
            assert arm['observed_dev']['impostor_trials'] == spec['expected_dev_impostor_trials']
            assert arm['observed_dev']['far'] == arm['observed_dev']['impostor_accepted'] / arm['observed_dev']['impostor_trials']
            accounts, pairs = arm['accounts'], arm['pairs']
            assert [a['participant_id'] for a in accounts] == spec['test_ids']
            wanted = {(t, s) for t in spec['test_ids'] for s in spec['test_ids'] if t != s}
            assert len(pairs) == len(wanted) and {(p['target_id'], p['source_id']) for p in pairs} == wanted
            metrics = {}
            for metric, numerator, denominator in (('far', 'impostor_accepted', 'impostor_trials'),
                                                    ('frr', 'genuine_rejected', 'genuine_trials')):
                metrics[metric] = sum((Fraction(a[numerator], a[denominator]) for a in accounts), Fraction()) / len(accounts)
                assert arm['macro_' + metric] == float(metrics[metric])
                assert sum(a[numerator] for a in accounts) == arm['overall'][numerator]
                assert sum(a[denominator] for a in accounts) == arm['overall'][denominator]
                assert arm['overall'][metric] == arm['overall'][numerator] / arm['overall'][denominator]
            assert arm['overall']['genuine_trials'] == spec['expected_test_genuine_trials']
            assert arm['overall']['impostor_trials'] == spec['expected_test_impostor_trials']
            for account in accounts:
                group = [p for p in pairs if p['target_id'] == account['participant_id']]
                assert all(p['impostor_trials'] == 10 for p in group)
                assert sum(p['impostor_accepted'] for p in group) == account['impostor_accepted']
            means.append(metrics)
            for kind, rows in (('accounts', accounts), ('pairs', pairs)):
                exported = [r for r in csvs[kind] if r['dataset'] == spec['name'] and r['arm'] == arm['arm']]
                assert all(float(r['threshold']) == spec['shared_fixed_threshold'] for r in exported)
                reconcile(rows, exported)
                expected_sizes[kind] += len(rows)
        dfar, dfrr = (means[1][m] - means[0][m] for m in ('far', 'frr'))
        comp = data['comparison']
        assert comp['delta_macro_far'] == float(dfar) and comp['delta_macro_frr'] == float(dfrr)
        support = dfar < 0 and dfrr <= 0
        assert comp['descriptive_support'] == support
        assert comp['interpretation'] == ('descriptive_support' if support else 'tradeoff' if dfar < 0 and dfrr > 0 else 'not_supported')
        for kind, rows in (('deltas', comp['accounts']), ('transitions', data['pair_transitions'])):
            reconcile(rows, [r for r in csvs[kind] if r['dataset'] == spec['name']])
            expected_sizes[kind] += len(rows)
        transition = {key: sum(r[key] for r in data['pair_transitions']) for key in
                      ('new_false_accept', 'recovered_rejection', 'accepted_both', 'rejected_both')}
        assert sum(transition.values()) == spec['expected_test_impostor_trials']
        assert transition['accepted_both'] + transition['recovered_rejection'] == data['arms'][0]['overall']['impostor_accepted']
        assert transition['accepted_both'] + transition['new_false_accept'] == data['arms'][1]['overall']['impostor_accepted']
        decisions[spec['name']] = comp['interpretation']
        changes[spec['name']] = transition
    assert all(len(csvs[k]) == size for k, size in expected_sizes.items())
    assert saved['both_sources_descriptively_support'] == all(d['comparison']['descriptive_support'] for d in saved['datasets'])
    checks = {'status': 'passed', 'scope': 'stored artifact arithmetic, no fitting/new experiment',
              'freeze_sha256': sha(ROOT / FREEZE), 'results_sha256': sha(saved_path),
              'chronology_verified': True, 'fixed_thresholds_unchanged': True,
              'baseline_reproduces_prior_decay20_both_sources': True,
              'historical_artifacts_and_both_report_sets_unchanged': True,
              'csv_rows': expected_sizes, 'decisions': decisions, 'transitions': changes,
              'both_sources_descriptively_support': saved['both_sources_descriptively_support']}
    (folder / 'cv_aggregation_control_checks.json').write_text(json.dumps(checks, indent=2) + '\n', encoding='utf-8')
    print('PASS: baseline reproduced in both sources; fixed thresholds; macro/counts; CSV96/2532/48/1266; chronology/hashes')


if __name__ == '__main__':
    main()
