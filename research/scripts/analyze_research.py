"""Diagnose saved experiments without changing thresholds, raw data or selection."""
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
from keyguard.diagnostics import account_diagnostic, threshold_jackknife
from keyguard.research import VARIANTS, BASELINE, score_accounts, combine


def write_csv(name, rows):
    with (ROOT / 'results' / name).open('w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main():
    source_path = ROOT / 'results/research_summary.json'
    source_bytes = source_path.read_bytes()
    source = json.loads(source_bytes)
    config = ROOT / 'models/model_config.json'
    assert hashlib.sha256(config.read_bytes()).hexdigest() == source['protocol']['config_sha256']
    manifest = json.loads((ROOT / 'data/collected_manifest.json').read_text(encoding='utf-8'))
    for entry in manifest['files']:
        assert hashlib.sha256((ROOT / entry['path']).read_bytes()).hexdigest() == entry['sha256']
    df, _ = load_collected(str(ROOT / 'data/collected/*.jsonl'), duplicate_policy='exclude-all',
                           require_timestamp=True, order='timestamp')
    data = {pid: np.vstack(group.x.to_list()) for pid, group in df.groupby('participant_id')}
    output = {'schema_version': 1, 'date': '2026-11-13',
              'source_summary_sha256': hashlib.sha256(source_bytes).hexdigest(),
              'config_sha256': source['protocol']['config_sha256'],
              'diagnostics_code_sha256': hashlib.sha256((ROOT / 'keyguard/diagnostics.py').read_bytes()).hexdigest(),
              'scope': 'Descriptive diagnosis only; no new threshold/variant selected',
              'variants': [], 'pipelines': {}}
    account_csv, pair_csv, jackknife_csv = [], [], []
    for variant in VARIANTS:
        saved = next(v for v in source['variants'] if v['id'] == variant.name)
        cache = score_accounts(data, variant, source['protocol']['enrollment'])
        variant_rows = {'id': variant.name, 'folds': []}
        for fold in saved['folds']:
            split = source['selection_by_fold'][fold['fold'] - 1]
            ids = split['test_ids']
            row = {'fold': fold['fold'], 'accounts': {}, 'pairs': {}}
            for policy, threshold, expected in (
                    ('dev', fold['threshold'], fold['test']),
                    ('cmu', source['protocol']['baseline_threshold'], fold['fixed_cmu'])):
                accounts, pairs = [], []
                for pid in ids:
                    account, account_pairs = account_diagnostic(data, cache, variant, pid, ids, threshold)
                    accounts.append(account)
                    pairs.extend(account_pairs)
                    flat = {k: v for k, v in account.items() if not isinstance(v, list)}
                    account_csv.append({'variant': variant.name, 'fold': fold['fold'], 'policy': policy, **flat})
                    pair_csv.extend({'variant': variant.name, 'fold': fold['fold'], 'policy': policy, **p}
                                    for p in account_pairs)
                assert combine(accounts) == expected, (variant.name, fold['fold'], policy)
                row['accounts'][policy], row['pairs'][policy] = accounts, pairs
            jackknife = threshold_jackknife(cache, split['dev_ids'], source['protocol']['target_dev_far'])
            row['dev_jackknife'] = jackknife
            jackknife_csv.extend({'variant': variant.name, 'fold': fold['fold'], **entry} for entry in jackknife)
            variant_rows['folds'].append(row)
        output['variants'].append(variant_rows)
    by_name = {v['id']: v for v in output['variants']}
    for name, mode in [('baseline_fixed', 'cmu'), ('baseline_recalibrated', 'dev'), ('nested_selected', 'dev')]:
        accounts, pairs, folds = [], [], []
        for j, split in enumerate(source['selection_by_fold']):
            variant = split['selected_variant'] if name == 'nested_selected' else BASELINE
            row = by_name[variant]['folds'][j]
            accounts.extend({'fold': j + 1, 'variant': variant, **a} for a in row['accounts'][mode])
            pairs.extend({'fold': j + 1, 'variant': variant, **p} for p in row['pairs'][mode])
            totals = combine(row['accounts'][mode])
            folds.append({'fold': j + 1, 'variant': variant, **totals})
        assert combine(accounts) == source[name]
        output['pipelines'][name] = {
            'accounts': accounts, 'pairs': pairs, 'folds': folds,
            'top_far': sorted(accounts, key=lambda a: (-a['far'], a['participant_id']))[:5],
            'top_frr': sorted(accounts, key=lambda a: (-a['frr'], a['participant_id']))[:5],
            'worst_pairs': sorted(pairs, key=lambda p: (-p['accepted'], p['target'], p['impostor']))[:8],
        }
    assert source_path.read_bytes() == source_bytes
    assert hashlib.sha256(config.read_bytes()).hexdigest() == source['protocol']['config_sha256']
    encoded = json.dumps(output, ensure_ascii=False, indent=2, allow_nan=False)
    (ROOT / 'results/research_diagnostics.json').write_text(encoded + '\n', encoding='utf-8')
    (ROOT / 'explorer/diagnostics-data.js').write_text(
        'window.KEYGUARD_DIAGNOSTICS = ' + json.dumps(output, ensure_ascii=False, allow_nan=False) + ';\n', encoding='utf-8')
    write_csv('research_account_errors.csv', account_csv)
    write_csv('research_pair_errors.csv', pair_csv)
    write_csv('research_threshold_jackknife.csv', jackknife_csv)
    print('PASS:', len(account_csv), 'account rows;', len(pair_csv), 'pair rows;', len(jackknife_csv), 'jackknife rows')
    for key, pipeline in output['pipelines'].items():
        print(key, 'FAR', [(a['participant_id'], a['impostor_accepted'], a['far']) for a in pipeline['top_far'][:3]],
              'FRR', [(a['participant_id'], a['genuine_rejected'], a['frr']) for a in pipeline['top_frr'][:3]])


if __name__ == '__main__':
    main()
