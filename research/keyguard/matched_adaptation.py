"""Paired S1/S2 adaptation comparison; existing frozen core remains unchanged."""
from fractions import Fraction

import numpy as np

from keyguard.evaluation import threshold_at_far
from keyguard.research import combine, counts
from keyguard.session_adaptation import fit_history


ARMS = ('window50', 'decay20')


def validate_data(data, dev_ids, test_ids, features):
    """Metadata/finite-value audit only, never model selection from S2."""
    if (len(dev_ids) < 2 or len(test_ids) < 2 or
            len(set(dev_ids)) != len(dev_ids) or len(set(test_ids)) != len(test_ids) or
            set(dev_ids) & set(test_ids) or set(data) != set(dev_ids) | set(test_ids)):
        raise ValueError('Invalid/disjoint identity partitions required')
    for sessions in data.values():
        if set(sessions) != {1, 2}:
            raise ValueError('Only sessions 1 and 2 are permitted')
        for session, minimum in ((1, 25), (2, 10)):
            x = np.asarray(sessions[session])
            if (x.ndim != 2 or x.shape[1] != features or len(x) < minimum or
                    not np.isfinite(x).all()):
                raise ValueError('Invalid matrix/session length/features/nonfinite values')
    return {
        'dev_impostor_trials': len(dev_ids) * (len(dev_ids) - 1) * 10,
        'test_genuine_trials': sum(len(data[pid][2]) for pid in test_ids),
        'test_impostor_trials': len(test_ids) * (len(test_ids) - 1) * 10,
    }


def probe_matrix(session_arrays, ids, target):
    others = [pid for pid in ids if pid != target]
    if not others:
        raise ValueError('Need other identities for probes')
    rows = []
    for pid in others:
        x = np.asarray(session_arrays[pid])
        if len(x) < 10:
            raise ValueError('First/last five probes must be disjoint')
        rows.append(np.vstack((x[:5], x[-5:])))
    return np.vstack(rows), others


def calibrate_dev(dev_session1, method):
    """Accept S1 arrays only: neither S2 nor a test partition is an input."""
    if method not in ARMS or len(dev_session1) < 2:
        raise ValueError('Invalid method/dev partition')
    ids = list(dev_session1)
    scores = []
    for pid in ids:
        enrollment = np.asarray(dev_session1[pid])[:20]
        if len(enrollment) != 20:
            raise ValueError('Need twenty enrollment rows')
        model, center, scale = fit_history(enrollment, method)
        probes, _ = probe_matrix(dev_session1, ids, pid)
        scores.append((model.score(probes) - center) / scale)
    pooled = np.concatenate(scores)
    if not np.isfinite(pooled).all():
        raise ValueError('Nonfinite dev scores')
    threshold = threshold_at_far(pooled, .05)
    accepted = int(np.count_nonzero(pooled <= threshold))
    if accepted > int(np.floor(.05 * len(pooled))):
        raise RuntimeError('Dev FAR budget exceeded')
    return {'threshold': threshold, 'impostor_accepted': accepted,
            'impostor_trials': len(pooled), 'far': accepted / len(pooled)}


def score_account(session1, session2, probes, method):
    """Oracle warm-up, one probe checkpoint, then prequential genuine scoring."""
    if method not in ARMS:
        raise ValueError('Invalid method')
    # No warm-up decisions enter the primary FRR. Oracle updates are independent
    # of those decisions, so only the final past-history fit is needed here.
    history = np.asarray(session1, dtype=float)[-50:].copy()
    model, center, scale = fit_history(history, method)
    impostor_scores = (model.score(probes) - center) / scale
    genuine_scores = []
    for row in np.asarray(session2):
        genuine_scores.append(float((model.score(row[None, :])[0] - center) / scale))
        history = np.vstack((history, row))[-50:]
        model, center, scale = fit_history(history, method)
    genuine_scores = np.asarray(genuine_scores)
    if not np.isfinite(np.r_[genuine_scores, impostor_scores]).all():
        raise ValueError('Nonfinite test scores')
    return genuine_scores, impostor_scores


def evaluate_test(test_data, method, calibration):
    """Threshold already fixed; scores do not change calibration."""
    ids = list(test_data)
    s2 = {pid: test_data[pid][2] for pid in ids}
    tau = calibration['threshold']
    accounts, pairs = [], []
    for pid in ids:
        probes, others = probe_matrix(s2, ids, pid)
        genuine, impostors = score_account(test_data[pid][1], s2[pid], probes, method)
        account = {'participant_id': pid, **counts(genuine, impostors, tau)}
        accounts.append(account)
        for index, other in enumerate(others):
            accepted = int(np.count_nonzero(impostors[index * 10:(index + 1) * 10] <= tau))
            pairs.append({'target_id': pid, 'source_id': other,
                          'impostor_accepted': accepted, 'impostor_trials': 10,
                          'far': accepted / 10})
        if sum(p['impostor_accepted'] for p in pairs if p['target_id'] == pid) != account['impostor_accepted']:
            raise RuntimeError('Pair/account counts disagree')
    return {'method': method, 'calibration': dict(calibration),
            'overall': combine(accounts), 'macro_frr': float(macro(accounts, 'frr')),
            'macro_far': float(macro(accounts, 'far')), 'accounts': accounts, 'pairs': pairs}


def rate(row, metric):
    numerator, denominator = (('genuine_rejected', 'genuine_trials') if metric == 'frr'
                              else ('impostor_accepted', 'impostor_trials'))
    return Fraction(row[numerator], row[denominator])


def macro(accounts, metric):
    return sum((rate(a, metric) for a in accounts), Fraction()) / len(accounts)


def compare_arms(baseline, candidate):
    left = {a['participant_id']: a for a in baseline['accounts']}
    right = {a['participant_id']: a for a in candidate['accounts']}
    if set(left) != set(right):
        raise ValueError('Unpaired account identities')
    rows = []
    for pid, a in left.items():
        b = right[pid]
        if any(a[k] != b[k] for k in ('genuine_trials', 'impostor_trials')):
            raise ValueError('Unpaired denominators')
        rows.append({'participant_id': pid,
                     'delta_frr': float(rate(b, 'frr') - rate(a, 'frr')),
                     'delta_far': float(rate(b, 'far') - rate(a, 'far'))})
    # Exact rational arithmetic prevents tiny floating-point artifacts from
    # changing the predeclared directional rule at zero.
    dfrr = macro(candidate['accounts'], 'frr') - macro(baseline['accounts'], 'frr')
    dfar = macro(candidate['accounts'], 'far') - macro(baseline['accounts'], 'far')
    supported = dfrr < 0 and dfar <= 0
    return {'delta_macro_frr': float(dfrr), 'delta_macro_far': float(dfar),
            'descriptive_support': supported,
            'interpretation': ('descriptive_support' if supported else
                               'tradeoff' if dfrr < 0 and dfar > 0 else 'not_supported'),
            'accounts': rows,
            'direction_counts': {metric: {
                'better': sum(row['delta_' + metric] < 0 for row in rows),
                'equal': sum(row['delta_' + metric] == 0 for row in rows),
                'worse': sum(row['delta_' + metric] > 0 for row in rows),
            } for metric in ('frr', 'far')}}


def run_dataset(data, dev_ids, test_ids, features, expected):
    actual = validate_data(data, dev_ids, test_ids, features)
    if actual != expected:
        raise ValueError(f'Pre-scoring sample counts mismatch: {actual} != {expected}')
    dev_s1 = {pid: data[pid][1] for pid in dev_ids}
    # Calibrate BOTH arms before any test scoring, never reselect thresholds.
    calibrations = {method: calibrate_dev(dev_s1, method) for method in ARMS}
    test = {pid: data[pid] for pid in test_ids}
    arms = [evaluate_test(test, method, calibrations[method]) for method in ARMS]
    return {'arms': arms, 'comparison': compare_arms(*arms), 'counts': actual}
