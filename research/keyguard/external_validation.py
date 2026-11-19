"""KeyRecs adapter and frozen-method evaluation; metadata are never predictors."""
import collections
import csv
import hashlib
from pathlib import Path
import re
import numpy as np

from keyguard.soft_weighting import fit_calibrated
from keyguard.research import counts, combine, roc


def read_keyrecs(path):
    with Path(path).open(encoding='utf-8-sig', newline='') as stream:
        reader = csv.reader(stream)
        header = next(reader)
        if header[:3] != ['participant', 'session', 'repetition']:
            raise ValueError('Unexpected KeyRecs metadata schema')
        if len(header) != 50 or header[-1] != 'total time':
            raise ValueError('Unexpected fixed-text timing schema')
        if not all(re.fullmatch(r'[DU]{2}\.[^.]+\.[^.]+', name) for name in header[3:-1]):
            raise ValueError('Non-timing column in feature matrix')
        occurrences = collections.Counter()
        names = []
        for name in header[3:]:
            occurrences[name] += 1
            names.append(name if occurrences[name] == 1 else f'{name}__occ{occurrences[name]}')
        rows, excluded, raw_count = [], [], 0
        for line, fields in enumerate(reader, 2):
            raw_count += 1
            try:
                if len(fields) != len(header):
                    raise ValueError('wrong column count')
                pid = fields[0]
                session, rep = int(fields[1]), int(fields[2])
                x = np.array(fields[3:], dtype=float)
                if not re.fullmatch(r'p[0-9]+', pid) or session not in (1, 2) or rep < 1:
                    raise ValueError('invalid metadata')
                if not np.isfinite(x).all():
                    raise ValueError('nonfinite timing')
                rows.append({'participant': pid, 'session': session, 'rep': rep, 'x': x, 'line': line})
            except (ValueError, OverflowError) as error:
                excluded.append({'line': line, 'reason': str(error)})
    keys = collections.Counter((r['participant'], r['session'], r['rep']) for r in rows)
    retained = []
    for row in rows:
        if keys[row['participant'], row['session'], row['rep']] > 1:
            excluded.append({'line': row['line'], 'reason': 'ambiguous duplicate key, exclude all'})
        else:
            retained.append(row)
    grouped = {}
    for row in sorted(retained, key=lambda r: (r['participant'], r['session'], r['rep'])):
        grouped.setdefault(row['participant'], {1: [], 2: []})[row['session']].append(row['x'])
    eligible = {pid: {s: np.vstack(v) for s, v in sessions.items()}
                for pid, sessions in grouped.items() if len(sessions[1]) >= 25 and len(sessions[2]) >= 10}
    audit = {'raw_rows': raw_count, 'retained_rows': len(retained), 'excluded': excluded,
             'participant_count': len(grouped), 'eligible_ids': sorted(eligible),
             'ineligible_ids': sorted(set(grouped)-set(eligible)), 'feature_count': len(names),
             'raw_feature_names': header[3:], 'feature_names': names,
             'header_duplicate_names': {k: v for k, v in occurrences.items() if v > 1},
             'session_rows': {str(s): sum(len(v[s]) for v in grouped.values()) for s in (1, 2)},
             'eligible_session_counts': {pid: {str(s): len(v[s]) for s in (1, 2)} for pid, v in eligible.items()},
    }
    return eligible, audit


def fixed_split(ids, seed=42):
    shuffled = np.random.default_rng(seed).permutation(sorted(ids))
    cut = (2 * len(shuffled)) // 3
    dev, test = sorted(shuffled[:cut].tolist()), sorted(shuffled[cut:].tolist())
    if len(dev) < 4 or len(test) < 2:
        raise ValueError('Insufficient eligible identities')
    return dev, test


def external_cache(data, quality, calibration, evaluation_session):
    if evaluation_session not in (1, 2):
        raise ValueError('Invalid evaluation session')
    result = {}
    for pid, sessions in data.items():
        model, center, scale, _ = fit_calibrated(sessions[1][:20], quality, calibration)
        genuine = sessions[1][20:] if evaluation_session == 1 else sessions[2]
        result[pid] = {'genuine': (model.score(genuine)-center)/scale,
                       'impostors': {other: {stage: (model.score(other_sessions[evaluation_session][indices])-center)/scale
                                            for stage, indices in [('early', slice(0, 5)), ('late', slice(-5, None))]}
                                     for other, other_sessions in data.items() if other != pid}}
    return result


def evaluate_partition(cache, ids, threshold):
    accounts = []
    for pid in ids:
        genuine = cache[pid]['genuine']
        impostors = np.concatenate([cache[pid]['impostors'][other][stage] for other in ids
                                     if other != pid for stage in ('early', 'late')])
        _, _, _, eer, auc = roc(genuine, impostors)
        accounts.append({'participant_id': pid, **counts(genuine, impostors, threshold), 'eer': eer, 'auc': auc})
    return {'overall': combine(accounts), 'accounts': accounts,
            'macro_eer': float(np.mean([a['eer'] for a in accounts])),
            'macro_auc': float(np.mean([a['auc'] for a in accounts]))}
