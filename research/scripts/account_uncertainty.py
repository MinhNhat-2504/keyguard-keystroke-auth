"""Paired target-account percentile bootstrap of saved, fixed outcomes only."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SEED = 20261115
REPLICATES = 20000
FIELDS = ('impostor_accepted', 'impostor_trials', 'genuine_rejected', 'genuine_trials')


def paired_rates(control, candidate):
    def keyed(rows):
        result = {}
        for row in rows:
            pid = row['participant_id']
            if not isinstance(pid, str) or not pid or pid in result:
                raise ValueError('Missing or duplicate account')
            vals = []
            for field in FIELDS:
                v = row[field]
                if isinstance(v, bool) or not isinstance(v, (str, int)):
                    raise ValueError('Counts must be integers')
                value = int(v)
                if isinstance(v, str) and str(value) != v:
                    raise ValueError('Noncanonical integer count')
                vals.append(value)
            fa, ni, fr, ng = vals
            if ni <= 0 or ng <= 0 or not 0 <= fa <= ni or not 0 <= fr <= ng:
                raise ValueError('Invalid trial counts')
            result[pid] = vals
        return result
    a, b = keyed(control), keyed(candidate)
    if set(a) != set(b) or len(a) < 2:
        raise ValueError('Need at least two matching accounts')
    ids = sorted(a)
    for pid in ids:
        if a[pid][1::2] != b[pid][1::2]:
            raise ValueError('Trial denominators differ between arms')
    return np.array([[a[p][0]/a[p][1], a[p][2]/a[p][3],
                      b[p][0]/b[p][1], b[p][2]/b[p][3]] for p in ids])


def summarize(rates, replicates=REPLICATES, seed=SEED):
    rates = np.asarray(rates, dtype=float)
    if rates.ndim != 2 or rates.shape[1] != 4 or len(rates) < 2:
        raise ValueError('Expected n-by-4 paired account rates')
    if not np.isfinite(rates).all() or (rates < 0).any() or (rates > 1).any():
        raise ValueError('Invalid rates')
    if type(replicates) is not int or replicates < 100:
        raise ValueError('Need at least 100 bootstrap replicates')
    # One index matrix shared by all arms/metrics; never resample trials separately.
    indices = np.random.default_rng(seed).integers(0, len(rates), (replicates, len(rates)))
    samples = rates[indices].mean(axis=1) * 100
    points = rates.mean(axis=0) * 100
    values = np.column_stack((samples, samples[:, 2]-samples[:, 0], samples[:, 3]-samples[:, 1]))
    points = np.r_[points, points[2]-points[0], points[3]-points[1]]
    names = ('control_far', 'control_frr', 'candidate_far', 'candidate_frr', 'delta_far', 'delta_frr')
    bounds = np.quantile(values, [.025, .975], axis=0, method='linear')
    return {name: {'estimate_pp': float(points[i]), 'lower_pp': float(bounds[0, i]),
                   'upper_pp': float(bounds[1, i])} for i, name in enumerate(names)}


def inputs(root=ROOT):
    def rows(name):
        with (root/'results'/name).open(encoding='utf-8-sig', newline='') as f:
            return list(csv.DictReader(f))
    shrink = rows('dispersion_shrinkage_accounts.csv')
    greyc = rows('greyc_web_account_benefit_accounts.csv')
    cov = rows('covariance_control_accounts.csv')
    dev = json.loads((root/'results/dev_oof_percentile_results.json').read_text())['arms']
    jobs = []
    for dataset in ('CMU', 'KeyRecs'):
        selected = [r for r in shrink if r['dataset'] == dataset]
        # Source labels may include protocol descriptions; exact source schema checked below.
        if not selected:
            selected = [r for r in shrink if r['dataset'].startswith(dataset)]
        jobs.append((dataset+' shrink25', 'baseline', 'shrink25', selected, 'arm'))
    jobs += [('GREYC shrink25', 'baseline', 'shrink25', greyc, 'arm'),
             ('GREYC DEV percentile', 'baseline', 'oof_percentile',
              [dict(r, method=a['method']) for a in dev for r in a['accounts']], 'method'),
             ('GREYC DEV covariance', 'diag_lw', 'full_lw', cov, 'method')]
    return jobs


def run(root=ROOT):
    sources = ['results/dispersion_shrinkage_accounts.csv', 'results/greyc_web_account_benefit_accounts.csv',
               'results/covariance_control_accounts.csv', 'results/dev_oof_percentile_results.json',
               'docs/ACCOUNT_UNCERTAINTY_PLAN_20261115.md', 'scripts/account_uncertainty.py']
    output = {'scope': 'Retrospective conditional target-account descriptive intervals; not new validation',
              'seed': SEED, 'replicates': REPLICATES, 'nominal_percentile_interval': 95,
              'unit': 'percentage points', 'cross_account_impostor_dependence_modelled': False,
              'thresholds_or_original_gates_changed': False,
              'source_sha256': {n: hashlib.sha256((root/n).read_bytes()).hexdigest() for n in sources}, 'comparisons': []}
    for name, control, candidate, rows, armfield in inputs(root):
        rates = paired_rates([r for r in rows if r[armfield] == control],
                             [r for r in rows if r[armfield] == candidate])
        output['comparisons'].append({'comparison': name, 'control': control, 'candidate': candidate,
                                      'accounts': len(rates), 'metrics': summarize(rates)})
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, default=ROOT/'results/account_uncertainty_20261115.json')
    args = parser.parse_args()
    result = run()
    args.out.write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({'comparisons': len(result['comparisons']), 'accounts': [c['accounts'] for c in result['comparisons']],
                      'source_only': True, 'model_rerun': False}))


if __name__ == '__main__':
    main()
