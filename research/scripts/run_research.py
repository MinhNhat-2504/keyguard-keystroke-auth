"""Run all 24 predeclared exploratory variants and build the offline explorer."""
from __future__ import annotations

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
from keyguard.research import (VARIANTS, BASELINE, score_accounts, pool, counts,
                               curve, identity_folds, choose_variant, combine)


def main():
    config_path = ROOT / 'models/model_config.json'
    config_bytes = config_path.read_bytes()
    cfg = json.loads(config_bytes)
    manifest_path = ROOT / 'data/collected_manifest.json'
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    for entry in manifest['files']:
        if hashlib.sha256((ROOT / entry['path']).read_bytes()).hexdigest() != entry['sha256']:
            raise ValueError(f"Raw snapshot hash mismatch: {entry['path']}")
    df, issues = load_collected(str(ROOT / 'data/collected/*.jsonl'),
                               duplicate_policy='exclude-all', require_timestamp=True,
                               order='timestamp')
    data = {pid: np.vstack(group.x.to_list()) for pid, group in df.groupby('participant_id')}
    caches = {v.name: score_accounts(data, v, cfg['n_enroll']) for v in VARIANTS}
    folds = identity_folds(list(data))
    output = {
        'schema_version': 1, 'date': '2026-11-13',
        'protocol': {
            'kind': 'exploratory_nested_identity_cv', 'seed': 42,
            'samples': len(df), 'identities': len(data), 'excluded_rows': len(issues),
            'enrollment': cfg['n_enroll'], 'profile': 'frozen after enrollment',
            'outer_folds': folds, 'inner_folds': 2, 'target_dev_far': cfg['target_far'],
            'selection': 'minimum inner mean balanced error; variant name breaks ties',
            'impostors': 'first 5 and last 5 samples of other identities IN THE SAME partition',
            'baseline_threshold': cfg['threshold'],
            'limitations': ['Dữ liệu đã được phân tích trước; đây là nghiên cứu khám phá.',
                            'Chủ yếu một phiên; không kết luận ổn định qua ngày.',
                            'Các lượt cùng mã/hồ sơ phụ thuộc; không coi là độc lập.',
                            'Không chọn phương án triển khai từ bảng xếp hạng outer-test.',
                            'Không phải live test; không cập nhật cấu hình sản phẩm.'],
            'config_sha256': hashlib.sha256(config_bytes).hexdigest(),
            'data_manifest_sha256': hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
            'raw_file_hashes_verified': len(manifest['files']),
            'python': sys.version.split()[0], 'numpy': np.__version__,
            'research_code_sha256': hashlib.sha256((ROOT / 'keyguard/research.py').read_bytes()).hexdigest(),
        },
        'variants': [], 'selection_by_fold': [],
    }
    selected_by_fold = []
    for fold_index, test_ids in enumerate(folds):
        dev_ids = sorted(set(data) - set(test_ids))
        selected, ranking = choose_variant(caches, dev_ids, cfg['target_far'], seed=42 + fold_index)
        selected_by_fold.append(selected)
        output['selection_by_fold'].append({
            'fold': fold_index + 1, 'dev_ids': dev_ids, 'test_ids': test_ids,
            'selected_variant': selected, 'inner_ranking': ranking,
        })
    csv_rows = []
    for variant in VARIANTS:
        cache = caches[variant.name]
        result = {'id': variant.name, 'model': variant.model, 'features': variant.features,
                  'normalization': variant.normalization, 'folds': []}
        for fold_index, test_ids in enumerate(folds):
            dev_ids = sorted(set(data) - set(test_ids))
            dg, di = pool(cache, dev_ids)
            tg, ti = pool(cache, test_ids)
            tau = threshold_at_far(di, cfg['target_far'])
            row = {'fold': fold_index + 1, 'threshold': tau,
                   'selected_by_inner_cv': variant.name == selected_by_fold[fold_index],
                   'dev': counts(dg, di, tau), 'test': counts(tg, ti, tau),
                   'fixed_cmu': counts(tg, ti, cfg['threshold']),
                   'test_early': counts(*pool(cache, test_ids, 'early'), tau),
                   'test_late': counts(*pool(cache, test_ids, 'late'), tau),
                   'dev_curve': curve(dg, di, (tau, cfg['threshold'])),
                   'test_curve': curve(tg, ti, (tau, cfg['threshold']))}
            assert row['dev']['far'] <= cfg['target_far']
            result['folds'].append(row)
            csv_rows.append({'variant': variant.name, 'fold': fold_index + 1,
                             'threshold': tau, 'dev_far': row['dev']['far'],
                             **row['test'], 'eer': row['test_curve']['eer'],
                             'auc': row['test_curve']['auc']})
        result['overall'] = combine([r['test'] for r in result['folds']])
        result['overall_fixed_cmu'] = combine([r['fixed_cmu'] for r in result['folds']])
        result['mean_fold_eer'] = float(np.mean([r['test_curve']['eer'] for r in result['folds']]))
        result['mean_fold_auc'] = float(np.mean([r['test_curve']['auc'] for r in result['folds']]))
        output['variants'].append(result)
    by_name = {v['id']: v for v in output['variants']}
    selected_rows = [by_name[name]['folds'][j]['test'] for j, name in enumerate(selected_by_fold)]
    output['nested_selected'] = combine(selected_rows)
    output['baseline_fixed'] = by_name[BASELINE]['overall_fixed_cmu']
    output['baseline_recalibrated'] = by_name[BASELINE]['overall']
    output['baseline_id'] = BASELINE
    assert config_path.read_bytes() == config_bytes
    result_dir = ROOT / 'results'
    (result_dir / 'research_summary.json').write_text(
        json.dumps(output, ensure_ascii=False, indent=2, allow_nan=False) + '\n', encoding='utf-8')
    with (result_dir / 'research_comparison.csv').open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=list(csv_rows[0]))
        writer.writeheader()
        writer.writerows(csv_rows)
    explorer = ROOT / 'explorer'
    explorer.mkdir(exist_ok=True)
    (explorer / 'research-data.js').write_text(
        'window.KEYGUARD_RESEARCH = ' + json.dumps(output, ensure_ascii=False, allow_nan=False) + ';\n',
        encoding='utf-8')
    print(json.dumps({key: output[key] for key in
                      ('baseline_fixed', 'baseline_recalibrated', 'nested_selected')}, indent=2))
    print(f'PASS: {len(VARIANTS)} variants, {len(folds)} outer folds; config unchanged')


if __name__ == '__main__':
    main()
