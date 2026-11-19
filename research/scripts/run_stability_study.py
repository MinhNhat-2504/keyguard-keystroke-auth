"""Nine estimators, ten prespecified repeated identity splits, no tuning on outer test."""
import csv
import hashlib
import json
from pathlib import Path
import sys
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.stdout.reconfigure(encoding='utf-8')
from keyguard.collected import load_collected
from keyguard.evaluation import threshold_at_far
from keyguard.research import identity_folds, choose_variant, pool, counts, combine, roc
from keyguard.soft_weighting import QUALITIES, CALIBRATIONS, build_caches, descriptive

SEEDS = list(range(42, 52))


def main():
    config = (ROOT/'models/model_config.json').read_bytes()
    previous = (ROOT/'results/enrollment_study.json').read_bytes()
    manifest = json.loads((ROOT/'data/collected_manifest.json').read_text(encoding='utf-8'))
    for entry in manifest['files']:
        assert hashlib.sha256((ROOT/entry['path']).read_bytes()).hexdigest() == entry['sha256']
    df, _ = load_collected(str(ROOT/'data/collected/*.jsonl'), duplicate_policy='exclude-all', require_timestamp=True, order='timestamp')
    data = {pid: np.vstack(g.x.to_list()) for pid, g in df.groupby('participant_id')}
    caches, diagnostics = {}, []
    for quality in QUALITIES:
        for calibration in CALIBRATIONS:
            cache, diag = build_caches(data, quality, calibration)
            caches[f'{quality}__{calibration}'] = cache
            diagnostics.extend(diag)
    families = {'baseline': ['keep_all__mean_std'],
                'hard_selected': [k for k in caches if k.startswith('hard_filter__')],
                'soft_selected': [k for k in caches if k.startswith('soft_weight__')],
                'all_selected': list(caches)}
    result = {'date': '2026-11-13', 'protocol': {
        'seeds': SEEDS, 'samples': len(df), 'identities': len(data), 'outer_folds': 3, 'inner_folds': 2,
        'enrollment': 20, 'genuine_per_repeat': 297, 'impostor_per_repeat': 600,
        'soft_rule': 'weight = clip(cutoff / robust row deviation, 0.25, 1), cutoff=median+3robustsigma',
        'fit_weights_inside_cv_training': True, 'score_calibration': list(CALIBRATIONS),
        'quality_rules': list(QUALITIES), 'dev_target_far': .05,
        'config_sha256': hashlib.sha256(config).hexdigest(),
        'previous_enrollment_sha256': hashlib.sha256(previous).hexdigest(),
        'code_sha256': hashlib.sha256((ROOT/'keyguard/soft_weighting.py').read_bytes()).hexdigest(),
        'limitations': ['same 15 identities repeated, not 150 independent identities',
                       'std/range across dependent splits, not confidence interval',
                       'previously inspected data, exploratory only',
                       'no account-specific rules, no deployment selection from outer scores']},
        'enrollment_diagnostics': diagnostics, 'repetitions': [], 'variant_summaries': [], 'family_summaries': []}
    csv_rows, account_rows = [], []
    for seed in SEEDS:
        folds = identity_folds(list(data), seed=seed)
        repetition = {'seed': seed, 'folds': [], 'variant_totals': {}, 'families': {}}
        evaluated = {k: [] for k in caches}
        for j, test in enumerate(folds):
            dev = sorted(set(data)-set(test))
            fold = {'fold': j+1, 'dev_ids': dev, 'test_ids': test, 'selected': {}, 'variants': {}}
            for family, names in families.items():
                selected, ranking = choose_variant({k: caches[k] for k in names}, dev, .05, seed=seed+j)
                fold['selected'][family] = {'variant': selected, 'inner_ranking': ranking}
            for name, cache in caches.items():
                _, di = pool(cache, dev)
                tau = threshold_at_far(di, .05)
                tg, ti = pool(cache, test)
                _, _, _, eer, auc = roc(tg, ti)
                dev_far = float(np.mean(di <= tau))
                assert dev_far <= .05
                rows = []
                for pid in test:
                    imp = np.concatenate([cache[pid]['impostors'][other][s] for other in test if other != pid for s in ('early','late')])
                    rows.append({'participant_id': pid, **counts(cache[pid]['genuine'], imp, tau)})
                item = {'threshold': tau, 'dev_far': dev_far, 'test': counts(tg, ti, tau), 'eer': eer, 'auc': auc, 'accounts': rows}
                assert combine(rows) == item['test']
                fold['variants'][name] = item
                evaluated[name].append(item)
                csv_rows.append({'seed': seed, 'fold': j+1, 'variant': name, 'threshold': tau, 'dev_far': dev_far,
                                 **item['test'], 'eer': eer, 'auc': auc})
                account_rows.extend({'seed':seed,'fold':j+1,'variant':name,**row} for row in rows)
            repetition['folds'].append(fold)
        for name, rows in evaluated.items():
            repetition['variant_totals'][name] = {**combine([r['test'] for r in rows]),
                                                   'eer': float(np.mean([r['eer'] for r in rows])),
                                                   'auc': float(np.mean([r['auc'] for r in rows]))}
        for family in families:
            selected_rows = [f['variants'][f['selected'][family]['variant']] for f in repetition['folds']]
            repetition['families'][family] = {**combine([r['test'] for r in selected_rows]),
                                               'eer': float(np.mean([r['eer'] for r in selected_rows])),
                                               'auc': float(np.mean([r['auc'] for r in selected_rows]))}
        result['repetitions'].append(repetition)
        print('Completed split seed', seed, flush=True)
    for kind, names, field in [('variant_summaries', list(caches), 'variant_totals'), ('family_summaries', list(families), 'families')]:
        for name in names:
            result[kind].append({'id': name, **{metric: descriptive([r[field][name][metric] for r in result['repetitions']])
                                               for metric in ('far','frr','eer','auc')}})
    paired = []
    for r in result['repetitions']:
        baseline = r['families']['baseline']; soft = r['families']['soft_selected']; hard = r['families']['hard_selected']
        paired.append({'seed':r['seed'], 'soft_minus_baseline_far': soft['far']-baseline['far'],
                       'soft_minus_baseline_frr':soft['frr']-baseline['frr'],
                       'soft_minus_hard_far':soft['far']-hard['far'], 'soft_minus_hard_frr':soft['frr']-hard['frr']})
    result['paired_differences'] = paired
    result['paired_summary'] = {metric: descriptive([r[metric] for r in paired]) for metric in paired[0] if metric != 'seed'}
    first = result['repetitions'][0]['variant_totals']['keep_all__mean_std']
    assert all(first[k] == json.loads(previous)['baseline'][k] for k in ('far','frr','genuine_rejected','impostor_accepted'))
    assert config == (ROOT/'models/model_config.json').read_bytes() and previous == (ROOT/'results/enrollment_study.json').read_bytes()
    (ROOT/'results/stability_study.json').write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False)+'\n',encoding='utf-8')
    for name, rows in [('stability_comparison.csv',csv_rows),('stability_account_errors.csv',account_rows)]:
        with (ROOT/'results'/name).open('w',encoding='utf-8',newline='') as f:
            writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    (ROOT/'explorer/stability-data.js').write_text('window.KEYGUARD_STABILITY = '+json.dumps(result,ensure_ascii=False,allow_nan=False)+';\n',encoding='utf-8')
    print(json.dumps(result['family_summaries'],indent=2))


if __name__=='__main__':main()
