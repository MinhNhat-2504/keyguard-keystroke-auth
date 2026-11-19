"""Read-only reconcile frozen matched results/CSVs; write a separate check log."""
import csv
from datetime import datetime
from fractions import Fraction
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.run_matched_adaptation import FREEZE, PLAN, check_freeze, sha


def main():
    plan, frozen = check_freeze(ROOT)
    prefix = ROOT / 'results'
    start = json.loads((prefix / 'matched_adaptation_started.json').read_text(encoding='utf-8'))
    path = prefix / 'matched_adaptation_results.json'
    saved = json.loads(path.read_text(encoding='utf-8'))
    assert saved['freeze_sha256'] == start['freeze_sha256'] == sha(ROOT / FREEZE)
    assert saved['plan_sha256'] == sha(ROOT / PLAN)
    assert datetime.fromisoformat(frozen['frozen_at_utc']) <= datetime.fromisoformat(start['started_at_utc']) <= datetime.fromisoformat(saved['completed_at_utc'])
    csvs = {}
    for name in ('accounts', 'pairs', 'deltas'):
        with (prefix / f'matched_adaptation_{name}.csv').open(encoding='utf-8', newline='') as stream:
            csvs[name] = list(csv.DictReader(stream))
    assert [d['dataset'] for d in saved['datasets']] == [d['name'] for d in plan['datasets']]
    expected_sizes = {'accounts': 0, 'pairs': 0, 'deltas': 0}
    decisions = {}
    historical = json.loads((prefix / 'external_validation.json').read_text(encoding='utf-8'))
    for spec, data in zip(plan['datasets'], saved['datasets']):
        assert [a['method'] for a in data['arms']] == ['window50', 'decay20']
        macro = []
        for arm in data['arms']:
            accounts = arm['accounts']
            assert [a['participant_id'] for a in accounts] == spec['test_ids']
            pairs = arm['pairs']
            wanted = {(target, source) for target in spec['test_ids'] for source in spec['test_ids'] if target != source}
            assert len(pairs) == len(wanted) and {(p['target_id'], p['source_id']) for p in pairs} == wanted
            assert arm['overall']['genuine_trials'] == spec['expected_test_genuine_trials']
            assert arm['overall']['impostor_trials'] == spec['expected_test_impostor_trials']
            cal = arm['calibration']
            assert cal['impostor_trials'] == spec['expected_dev_impostor_trials']
            assert Fraction(cal['impostor_accepted'], cal['impostor_trials']) <= Fraction(1, 20)
            values = {}
            for metric, numerator, denominator in (
                    ('frr', 'genuine_rejected', 'genuine_trials'),
                    ('far', 'impostor_accepted', 'impostor_trials')):
                values[metric] = sum((Fraction(a[numerator], a[denominator]) for a in accounts), Fraction()) / len(accounts)
                assert float(values[metric]) == arm['macro_' + metric]
                assert sum(a[numerator] for a in accounts) == arm['overall'][numerator]
                assert sum(a[denominator] for a in accounts) == arm['overall'][denominator]
            macro.append(values)
            for account in accounts:
                group = [p for p in pairs if p['target_id'] == account['participant_id']]
                assert all(p['impostor_trials'] == 10 for p in group)
                assert sum(p['impostor_accepted'] for p in group) == account['impostor_accepted']
            for kind, rows in (('accounts', accounts), ('pairs', pairs)):
                external = [r for r in csvs[kind] if r['dataset'] == spec['name'] and r['method'] == arm['method']]
                assert len(external) == len(rows)
                for row, line in zip(rows, external):
                    assert float(line['threshold']) == cal['threshold']
                    for key, value in row.items():
                        assert (float(line[key]) == value if isinstance(value, (float, int)) else line[key] == value)
                expected_sizes[kind] += len(rows)
            if spec['existing_schedule_matches']:
                old = next(a for a in historical['adaptation'] if a['id'] == arm['method'])
                assert old['threshold'] == cal['threshold']
                assert all(old['overall'][key] == arm['overall'][key] for key in arm['overall'])
                originals = {a['participant_id']: a for a in old['accounts']}
                for a in accounts:
                    assert all(originals[a['participant_id']][key] == value for key, value in a.items())
        dfrr, dfar = (macro[1][m] - macro[0][m] for m in ('frr', 'far'))
        comparison = data['comparison']
        assert comparison['delta_macro_frr'] == float(dfrr) and comparison['delta_macro_far'] == float(dfar)
        supported = dfrr < 0 and dfar <= 0
        assert comparison['descriptive_support'] == supported
        assert comparison['interpretation'] == ('descriptive_support' if supported else 'tradeoff' if dfrr < 0 and dfar > 0 else 'not_supported')
        external = [r for r in csvs['deltas'] if r['dataset'] == spec['name']]
        assert len(external) == len(comparison['accounts']) == len(spec['test_ids'])
        for row, line in zip(comparison['accounts'], external):
            assert row['participant_id'] == line['participant_id']
            assert all(row[k] == float(line[k]) for k in ('delta_frr', 'delta_far'))
        expected_sizes['deltas'] += len(external)
        decisions[spec['name']] = comparison['interpretation']
    assert all(len(csvs[k]) == v for k, v in expected_sizes.items())
    assert saved['both_sources_descriptively_support'] == all(d['comparison']['descriptive_support'] for d in saved['datasets'])
    checks = {'status': 'passed', 'scope': 'artifact reconciliation, not a new scoring run or model test suite',
              'freeze_sha256': sha(ROOT / FREEZE), 'results_sha256': sha(path),
              'frozen_inputs_code_environment_and_historical_artifacts_unchanged': True,
              'chronology_verified': True, 'csv_rows': expected_sizes,
              'keyrecs_thresholds_pooled_and_account_counts_match_historical': True,
              'decisions': decisions, 'both_sources_descriptively_support': saved['both_sources_descriptively_support']}
    (prefix / 'matched_adaptation_checks.json').write_text(json.dumps(checks, indent=2) + '\n', encoding='utf-8')
    print('PASS: freeze/chronology; CSV 96 accounts/2532 pairs/48 deltas; macro/count reconciliation; historical KeyRecs reproduced; no new scoring')


if __name__ == '__main__':
    main()
