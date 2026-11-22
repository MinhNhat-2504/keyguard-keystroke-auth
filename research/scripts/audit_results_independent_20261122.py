"""Reconcile saved evidence without importing the experiment's metric/model code.

Standard library only. No fitting, threshold selection, raw data or cloud access.
"""
import csv
import hashlib
import json
import math
import statistics
from collections import defaultdict
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COUNTS = ('genuine_trials', 'genuine_rejected', 'impostor_trials', 'impostor_accepted')
SOURCES = ['collected_preliminary_summary.json', 'collected_sensitivity_first_summary.json',
           'research_summary.json', 'enrollment_study.json', 'stability_study.json',
           'session_adaptation.json', 'external_validation.json', 'matched_adaptation_results.json',
           'cv_aggregation_control_results.json', 'dispersion_shrinkage_results.json',
           'greyc_web_account_benefit_results.json', 'dev_oof_percentile_results.json',
           'covariance_control_results.json', 'research_decision_20261115.json']


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class Audit:
    def __init__(self, root=ROOT):
        self.root = Path(root)
        self.inputs = {}
        self.checks = 0
        self.metrics = []
        self.account_groups = 0
        self.trial_decisions = 0
        self.pair_groups = 0
        self.splits = []

    def path(self, name):
        path = self.root / 'results' / name
        self.inputs['results/' + name] = digest(path)
        return path

    def load(self, name):
        return json.loads(self.path(name).read_text(encoding='utf-8-sig'))

    def csv(self, name):
        with self.path(name).open(encoding='utf-8-sig', newline='') as stream:
            return list(csv.DictReader(stream))

    def equal(self, actual, expected, label):
        self.checks += 1
        if isinstance(actual, (float, Fraction)) or isinstance(expected, (float, Fraction)):
            if not math.isclose(float(actual), float(expected), rel_tol=1e-11, abs_tol=1e-12):
                raise AssertionError((label, actual, expected))
        elif actual != expected:
            raise AssertionError((label, actual, expected))

    def totals(self, rows):
        result = {k: sum(int(r[k]) for r in rows) for k in COUNTS}
        result['far'] = Fraction(result['impostor_accepted'], result['impostor_trials'])
        result['frr'] = Fraction(result['genuine_rejected'], result['genuine_trials'])
        return result

    def compare_totals(self, rows, saved, label):
        result = self.totals(rows)
        for key in (*COUNTS, 'far', 'frr'):
            if key in saved:
                self.equal(result[key], saved[key], label + '/' + key)
        return result

    def walk(self, value, label):
        if isinstance(value, list):
            for i, item in enumerate(value):
                self.walk(item, label + '/' + str(i))
        elif isinstance(value, dict):
            if all(k in value and value[k] is not None for k in COUNTS):
                for numerator, denominator, metric in [('genuine_rejected', 'genuine_trials', 'frr'),
                                                        ('impostor_accepted', 'impostor_trials', 'far')]:
                    n, d = value[numerator], value[denominator]
                    if not (isinstance(n, int) and isinstance(d, int) and 0 <= n <= d and d > 0):
                        raise AssertionError((label, 'invalid counts'))
                    field = 'pooled_' + metric if value.get('metric_basis') == 'macro_accounts' else metric
                    if field in value:
                        self.equal(Fraction(n, d), value[field], label + '/' + field)
            if isinstance(value.get('accounts'), list) and value['accounts'] and all(all(k in a for k in COUNTS) for a in value['accounts']):
                rows = value['accounts']
                self.equal(len({r['participant_id'] for r in rows}), len(rows), label + '/unique_accounts')
                total = self.compare_totals(rows, value.get('overall', {}), label + '/overall')
                for metric in ('far', 'frr'):
                    numerator, denominator = ('impostor_accepted', 'impostor_trials') if metric == 'far' else ('genuine_rejected', 'genuine_trials')
                    macro = sum((Fraction(a[numerator], a[denominator]) for a in rows), Fraction()) / len(rows)
                    if 'macro_' + metric in value:
                        self.equal(macro, value['macro_' + metric], label + '/macro_' + metric)
                    total['macro_' + metric] = macro
                self.metrics.append({'evidence': label, 'accounts': len(rows), **{k: float(v) if isinstance(v, Fraction) else v for k, v in total.items()}})
                self.account_groups += 1
            for left, right in [('dev_ids', 'test_ids'), ('calibration_ids', 'evaluation_dev_ids')]:
                if left in value and right in value:
                    a, b = value[left], value[right]
                    self.equal(len(a), len(set(a)), label + '/unique_' + left)
                    self.equal(len(b), len(set(b)), label + '/unique_' + right)
                    self.equal(bool(set(a) & set(b)), False, label + '/disjoint')
                    self.splits.append({'evidence': label, 'left': left, 'right': right, 'sizes': [len(a), len(b)], 'overlap': 0})
            for k, item in value.items():
                self.walk(item, label + '/' + k)

    def collected(self, prefix):
        summary = self.load(prefix + '_summary.json')
        users = self.csv(prefix + '_per_user.csv')
        trials = self.csv(prefix + '_genuine_trials.csv')
        by_pid = defaultdict(list)
        tau = summary['threshold']
        for row in trials:
            z = float(row['z'])
            if not math.isfinite(z):
                raise AssertionError('nonfinite saved score')
            rejected = z > tau
            self.equal(rejected, row['rejected'].lower() == 'true', prefix + '/saved_decision')
            by_pid[row['participant_id']].append(rejected)
        for row in users:
            decisions = by_pid[row['participant_id']]
            self.equal(len(decisions), int(row['n_logins']), prefix + '/account_trials')
            self.equal(sum(decisions), int(row['genuine_rejected']), prefix + '/account_rejections')
        self.equal(len(trials), summary['logins'], prefix + '/genuine_trials')
        self.equal(sum(sum(v) for v in by_pid.values()), summary['genuine_rejected'], prefix + '/rejections')
        self.equal(sum(int(r['n_valid']) for r in users), summary['valid_samples'], prefix + '/valid_samples')
        self.equal(Fraction(summary['genuine_rejected'], len(trials)), summary['frr_pooled'], prefix + '/FRR')
        for stage in ('early', 'late'):
            n = sum(int(r['impostor_accepted_' + stage]) for r in users)
            d = sum(int(r['impostor_trials_' + stage]) for r in users)
            self.equal(n, summary['impostor_accepted_' + stage], prefix + '/FA_' + stage)
            self.equal(d, summary['impostor_trials_' + stage], prefix + '/I_' + stage)
            self.equal(Fraction(n, d), summary['far_' + stage + '_pooled'], prefix + '/FAR_' + stage)
        sessions = self.csv(prefix + '_by_session.csv')
        for row in sessions:
            selected = [t for t in trials if t['session'] == row['session']]
            self.equal(len(selected), int(row['logins']), prefix + '/session_trials')
            self.equal(sum(t['rejected'].lower() == 'true' for t in selected), int(row['rejected']), prefix + '/session_rejections')
        self.trial_decisions += len(trials)

    def pair_accounts(self, prefix, arm_key):
        accounts = self.csv(prefix + '_accounts.csv')
        pairs = self.csv(prefix + '_pairs.csv')
        groups = defaultdict(list)
        for row in pairs:
            if row['target_id'] == row['source_id']:
                raise AssertionError('Target used as own impostor')
            groups[(row['dataset'], row[arm_key], row['target_id'])].append(row)
        for account in accounts:
            key = (account['dataset'], account[arm_key], account['participant_id'])
            rows = groups.pop(key)
            self.equal(len(rows), len({r['source_id'] for r in rows}), prefix + '/unique_pairs')
            for column in ('impostor_trials', 'impostor_accepted'):
                self.equal(sum(int(r[column]) for r in rows), int(account[column]), prefix + '/' + column)
            self.pair_groups += 1
        self.equal(bool(groups), False, prefix + '/extra_pairs')

    def run(self):
        docs = {name: self.load(name) for name in SOURCES}
        for name, doc in docs.items():
            self.walk(doc, name)
        self.collected('collected_preliminary')
        self.collected('collected_sensitivity_first')
        self.pair_accounts('matched_adaptation', 'method')
        self.pair_accounts('cv_aggregation_control', 'arm')
        threshold_rows = self.csv('threshold_selection.csv')
        users = self.csv('threshold_test_per_user.csv')
        for row in threshold_rows:
            accounts = [r for r in users if r['policy'] == row['policy']]
            total = self.totals(accounts)
            self.equal(total['far'], float(row['far_test']), 'CMU/' + row['policy'] + '/FAR')
            self.equal(total['frr'], float(row['frr_test']), 'CMU/' + row['policy'] + '/FRR')
            self.metrics.append({'evidence': 'CMU_threshold/' + row['policy'], 'accounts': len(accounts), **{k: float(v) if isinstance(v, Fraction) else v for k,v in total.items()}})
        # Verify summaries driving benchmark figures from the per-account metric table.
        benchmark = self.csv('benchmark_cmu_per_user.csv')
        for row in self.csv('benchmark_cmu_summary.csv'):
            group = [r for r in benchmark if (r['detector'], r['n_train']) == (row['detector'], row['n_train'])]
            self.equal(len(group), int(row['n_users']), 'benchmark/n_users')
            for metric in ('eer', 'auc', 'eer_practiced', 'fit_ms'):
                self.equal(statistics.mean(float(r[metric]) for r in group), float(row[metric + '_mean']), 'benchmark/' + metric)
            for metric in ('eer', 'eer_practiced'):
                self.equal(statistics.stdev(float(r[metric]) for r in group), float(row[metric + '_std']), 'benchmark/SD_' + metric)
        # Fold selection is checked from saved rankings, without loading test scores.
        for name in ('research_summary.json', 'enrollment_study.json'):
            doc = docs[name]
            for selection in doc['selection_by_fold']:
                best = min(selection['inner_ranking'], key=lambda r: (r['inner_balanced_error'], r['variant']))
                self.equal(best['variant'], selection['selected_variant'], name + '/inner_selection')
            for variant in doc['variants']:
                self.compare_totals([f['test'] for f in variant['folds']], variant['overall'], name + '/' + variant['id'])
            selected = [next(v for v in doc['variants'] if v['id'] == s['selected_variant'])['folds'][s['fold']-1]['test'] for s in doc['selection_by_fold']]
            self.compare_totals(selected, doc['nested_selected'], name + '/nested')
        external = docs['external_validation.json']
        for family, selection in external['selection'].items():
            ranking = selection['inner_ranking']
            self.equal(min(ranking, key=lambda r: (r['inner_balanced_error'], r['variant']))['variant'], selection['variant'], 'external/' + family + '/selection')
        for family in external['families']:
            variant = next(v for v in external['variants'] if v['id'] == family['variant'])
            self.compare_totals(variant['accounts'], family['overall'], 'external/family/' + family['id'])
        for method in docs['session_adaptation.json']['methods']:
            for part, values in method['partitions'].items():
                self.compare_totals(values['sessions'], values['overall'], 'CMU_sessions/' + method['id'] + '/' + part)
        stability = docs['stability_study.json']
        for repetition in stability['repetitions']:
            for variant, saved in repetition['variant_totals'].items():
                self.compare_totals([f['variants'][variant]['test'] for f in repetition['folds']], saved, 'stability/' + str(repetition['seed']) + '/' + variant)
        for summary in stability['family_summaries']:
            rows = [rep['families'][summary['id']] for rep in stability['repetitions']]
            for metric in ('far', 'frr'):
                values = [r[metric] for r in rows]
                self.equal(statistics.mean(values), summary[metric]['mean'], 'stability/' + summary['id'] + '/' + metric)
                self.equal(statistics.stdev(values), summary[metric]['std_across_splits'], 'stability/' + summary['id'] + '/SD_' + metric)
        for row in docs['research_decision_20261115.json']['rows']:
            source = json.loads((self.root / row['artifact']).read_text(encoding='utf-8-sig'))
            value = source
            for token in row['pointer'].strip('/').split('/'):
                value = value[int(token)] if isinstance(value, list) else value[token]
            for metric in ('far', 'frr'):
                # Macro/mean rows are already verified from their account groups or split summaries.
                if row['metric_basis'] == 'pooled' and all(k in value for k in COUNTS):
                    self.equal(Fraction(value['impostor_accepted'], value['impostor_trials']) if metric == 'far' else Fraction(value['genuine_rejected'], value['genuine_trials']), row[metric], 'decision/' + row['variant'] + '/' + metric)
        # Reapply each study's ORIGINAL directional gate, using exact account fractions.
        decisions = []
        for name in ('matched_adaptation_results.json', 'cv_aggregation_control_results.json', 'dispersion_shrinkage_results.json'):
            supported = []
            for dataset in docs[name]['datasets']:
                left, right = dataset['arms']
                def macro(arm, metric):
                    num, den = ('impostor_accepted', 'impostor_trials') if metric == 'far' else ('genuine_rejected', 'genuine_trials')
                    return sum((Fraction(a[num], a[den]) for a in arm['accounts']), Fraction()) / len(arm['accounts'])
                dfar = macro(right, 'far') - macro(left, 'far')
                dfrr = macro(right, 'frr') - macro(left, 'frr')
                passed = dfar < 0 and dfrr <= 0 if name.startswith('cv_') else dfrr < 0 and dfar <= 0
                self.equal(passed, dataset['comparison']['descriptive_support'], name + '/gate')
                supported.append(passed)
                decisions.append({'study': name, 'dataset': dataset['dataset'], 'delta_macro_far': float(dfar), 'delta_macro_frr': float(dfrr), 'original_gate_met': passed})
            self.equal(all(supported), docs[name]['both_sources_descriptively_support'], name + '/both_sources')
        for name, expected in self.inputs.items():
            self.equal(digest(self.root / name), expected, 'input_preserved/' + name)
        return {'status': 'passed', 'date': '2026-11-22', 'checks': self.checks,
                'genuine_decisions_recomputed_from_scores': self.trial_decisions,
                'account_groups_reaggregated': self.account_groups, 'pair_to_account_groups': self.pair_groups,
                'identity_partition_checks': self.splits, 'metrics': self.metrics, 'original_gate_rechecks': decisions, 'input_sha256': self.inputs,
                'limitations': ['Only saved genuine-score CSVs permit per-trial threshold reapplication.',
                    'Impostor and other studies are reconciled from account/pair/session counts, not raw scores.',
                    'Benchmark EER/AUC checked as account means/SD; ROC was not recalculated from scores.',
                    'Arithmetic reconciliation does not independently establish provenance or absence of all leakage.'],
                'model_fit': False, 'new_threshold_selection': False, 'cloud_access': False}


if __name__ == '__main__':
    result = Audit().run()
    path = ROOT / 'results/independent_numeric_audit_20261122.json'
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: v for k, v in result.items() if k not in ('metrics', 'input_sha256', 'identity_partition_checks', 'limitations')}))
