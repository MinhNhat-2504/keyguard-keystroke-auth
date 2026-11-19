"""One frozen external evaluation; reproductions must explicitly opt in."""
import argparse
import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
import sys
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.stdout.reconfigure(encoding='utf-8')
from keyguard.external_validation import read_keyrecs, external_cache, evaluate_partition
from keyguard.evaluation import threshold_at_far
from keyguard.research import pool, choose_variant, counts, combine
from keyguard.session_adaptation import METHODS, score_session_stream


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def check_freeze(frozen):
    for name, expected in frozen['code_hashes'].items():
        if sha(ROOT/name) != expected:
            raise RuntimeError(f'Frozen code/protocol changed: {name}')
    assert sha(ROOT/frozen['dataset']['file']) == frozen['dataset']['sha256']
    assert sha(ROOT/'models/model_config.json') == frozen['production_config_sha256']


def csv_output(name, rows):
    with (ROOT/'results'/name).open('w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--reproduce', action='store_true', help='Recompute exactly the already-frozen evaluation, not a new validation')
    args = parser.parse_args()
    freeze_path = ROOT/'results/external_validation_freeze.json'
    frozen = json.loads(freeze_path.read_text(encoding='utf-8'))
    check_freeze(frozen)
    output_path = ROOT/'results/external_validation.json'
    if output_path.exists() and not args.reproduce:
        raise RuntimeError('Evaluation already exists; use --reproduce only for exact reproducibility, never to retune')
    started = ROOT/'results/external_evaluation_started.json'
    if not started.exists():
        started.write_text(json.dumps({'started_at_utc': datetime.now(timezone.utc).isoformat(),
                                        'freeze_sha256': sha(freeze_path)}, indent=2)+'\n', encoding='utf-8')
    start = json.loads(started.read_text(encoding='utf-8'))
    assert start['freeze_sha256'] == sha(freeze_path)
    data, audit = read_keyrecs(ROOT/frozen['dataset']['file'])
    assert audit == frozen['audit']
    dev_ids, test_ids = frozen['dev_ids'], frozen['test_ids']
    dev_data = {pid: data[pid] for pid in dev_ids}
    test_data = {pid: data[pid] for pid in test_ids}
    names = frozen['families']['all_selected']
    dev_caches, dev_evaluations = {}, {}
    for name in names:
        quality, calibration = name.split('__')
        dev_caches[name] = external_cache(dev_data, quality, calibration, 1)
        genuine, impostors = pool(dev_caches[name], dev_ids)
        tau = threshold_at_far(impostors, .05)
        dev_evaluations[name] = {'threshold': tau, 'dev': counts(genuine, impostors, tau)}
        assert dev_evaluations[name]['dev']['far'] <= .05
    selected = {}
    for family, allowed in frozen['families'].items():
        name, ranking = choose_variant({k: dev_caches[k] for k in allowed}, dev_ids, .05, seed=42)
        selected[family] = {'variant': name, 'inner_ranking': ranking}
    print('Dev session1 selection and thresholds complete; now scoring held-out test session2', flush=True)
    result = {'date': '2026-11-13', 'freeze_sha256': sha(freeze_path),
               'started_at_utc': start['started_at_utc'], 'source': frozen['dataset'],
               'dev_ids': dev_ids, 'test_ids': test_ids, 'features': audit['feature_names'],
               'selection': selected, 'variants': [], 'families': [], 'adaptation': [],
               'interpretation': ['External-source evaluation after locally frozen protocol/code, not public preregistration',
                                  'KeyRecs features47 and password differ from CMU31, verifies procedure not existing profile/tau',
                                  'Dev is external session1; test identities and session2 not used for selection',
                                  'All results retained; no retuning after test, no production config change']}
    account_rows, comparison_rows = [], []
    for name in names:
        quality, calibration = name.split('__')
        cache = external_cache(test_data, quality, calibration, 2)
        tau = dev_evaluations[name]['threshold']
        evaluated = evaluate_partition(cache, test_ids, tau)
        row = {'id': name, **dev_evaluations[name], **evaluated}
        result['variants'].append(row)
        comparison_rows.append({'variant': name, 'threshold': tau, 'dev_far': row['dev']['far'],
                                 **row['overall'], 'macro_eer': row['macro_eer'], 'macro_auc': row['macro_auc']})
        account_rows.extend({'variant': name, **a} for a in row['accounts'])
    by_name = {r['id']: r for r in result['variants']}
    baseline = by_name[selected['baseline']['variant']]
    for family, selection in selected.items():
        row = by_name[selection['variant']]
        result['families'].append({'id': family, 'variant': row['id'], 'overall': row['overall'],
                                    'macro_eer': row['macro_eer'], 'macro_auc': row['macro_auc'],
                                    'far_minus_baseline': row['overall']['far']-baseline['overall']['far'],
                                    'frr_minus_baseline': row['overall']['frr']-baseline['overall']['frr']})
    adaptation_rows = []
    for method in METHODS:
        # Dev session2 is never used: only the initial session1 checkpoint chooses tau.
        dev_impostor_scores = []
        for pid in dev_ids:
            others = np.vstack([dev_data[o][1][indices] for o in dev_ids if o != pid
                                for indices in (slice(0,5),slice(-5,None))])
            stream = score_session_stream(dev_data[pid][1], np.ones(len(dev_data[pid][1]), dtype=int), others, method)
            dev_impostor_scores.append(stream['impostor'][0]['scores'])
        dev_scores = np.concatenate(dev_impostor_scores)
        tau = threshold_at_far(dev_scores, .05)
        accounts = []
        for pid in test_ids:
            s1, s2 = test_data[pid][1], test_data[pid][2]
            X = np.vstack([s1,s2]); sessions = np.r_[np.ones(len(s1),dtype=int),np.full(len(s2),2)]
            probes = np.vstack([test_data[o][2][indices] for o in test_ids if o != pid
                                for indices in (slice(0,5),slice(-5,None))])
            stream = score_session_stream(X, sessions, probes, method)
            genuine = np.array([p['z'] for p in stream['genuine'] if p['session'] == 2])
            impostors = next(p['scores'] for p in stream['impostor'] if p['session'] == 2)
            accounts.append({'participant_id': pid, **counts(genuine, impostors, tau)})
        item = {'id': method, 'threshold': tau, 'dev_far': float(np.mean(dev_scores<=tau)),
                 'overall': combine(accounts), 'accounts': accounts}
        assert item['dev_far'] <= .05
        result['adaptation'].append(item)
        adaptation_rows.extend({'method':method,'threshold':tau,**a} for a in accounts)
        print('External adaptation completed:', method, flush=True)
    assert result['adaptation'][0]['overall'] == baseline['overall']
    check_freeze(frozen)
    if output_path.exists():
        old = json.loads(output_path.read_text(encoding='utf-8'))
        assert old == result, 'Exact reproduction differs; preserve original and investigate, do not overwrite'
    else:
        output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False)+'\n', encoding='utf-8')
    csv_output('external_comparison.csv', comparison_rows)
    csv_output('external_account_errors.csv', account_rows)
    csv_output('external_adaptation.csv', adaptation_rows)
    (ROOT/'explorer/external-data.js').write_text('window.KEYGUARD_EXTERNAL = '+json.dumps(result, ensure_ascii=False,allow_nan=False)+';\n', encoding='utf-8')
    print(json.dumps({'families':result['families'], 'adaptation':[{r['id']:r['overall']} for r in result['adaptation']]}, indent=2))


if __name__ == '__main__': main()
