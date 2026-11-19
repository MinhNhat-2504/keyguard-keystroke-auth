"""One decay20 detector/OOF vector, two aggregation rules, one fixed threshold."""
from dataclasses import dataclass

import numpy as np

from keyguard.matched_adaptation import macro, probe_matrix, rate, validate_data
from keyguard.research import combine, counts
from keyguard.soft_weighting import WeightedManhattan


ARMS = ('uniform_cv', 'age_weighted_cv')


def aggregate(scores, weights):
    scores, weights = np.asarray(scores, dtype=float), np.asarray(weights, dtype=float)
    if (scores.ndim != 1 or scores.shape != weights.shape or not len(scores) or
            not np.isfinite(scores).all() or not np.isfinite(weights).all() or np.any(weights <= 0)):
        raise ValueError('Finite scores and positive matching weights required')
    center = float(np.average(scores, weights=weights))
    scale = float(max(np.sqrt(np.average((scores - center) ** 2, weights=weights)), 1e-6))
    return center, scale


@dataclass(frozen=True)
class SharedState:
    model: WeightedManhattan
    oof_scores: np.ndarray
    weights: np.ndarray
    normalizers: dict

    def score_both(self, rows):
        # Exactly one detector call; both transforms consume the same raw vector.
        raw = self.model.score(np.atleast_2d(rows))
        result = {arm: (raw - center) / scale for arm, (center, scale) in self.normalizers.items()}
        if not np.isfinite(raw).all() or not all(np.isfinite(z).all() for z in result.values()):
            raise ValueError('Nonfinite scores')
        return result


def fit_shared(history):
    history = np.array(history, dtype=float, copy=True)
    if history.ndim != 2 or not 20 <= len(history) <= 50 or not np.isfinite(history).all():
        raise ValueError('Need 20..50 finite past-history rows')
    weights = np.power(.5, (len(history) - 1 - np.arange(len(history))) / 20)
    scores = np.empty(len(history))
    for held in np.array_split(np.arange(len(history)), 5):
        keep = np.ones(len(history), dtype=bool)
        keep[held] = False
        fold_model = WeightedManhattan().fit(history[keep], weights[keep])
        scores[held] = fold_model.score(history[held])
    model = WeightedManhattan().fit(history, weights)
    normalizers = {
        # Same operations as frozen fit_history to preserve exact uniform baseline.
        'uniform_cv': (float(scores.mean()), float(max(scores.std(), 1e-6))),
        'age_weighted_cv': aggregate(scores, weights),
    }
    scores.setflags(write=False)
    weights.setflags(write=False)
    return SharedState(model, scores, weights, normalizers)


def observe_dev(dev_session1, threshold):
    """Observation only; no S2/test parameter and no threshold selector."""
    ids = list(dev_session1)
    if len(ids) < 2 or not np.isfinite(threshold):
        raise ValueError('Invalid dev partition/threshold')
    totals = {arm: {'impostor_accepted': 0, 'impostor_trials': 0} for arm in ARMS}
    for pid in ids:
        state = fit_shared(dev_session1[pid][:20])
        probes, _ = probe_matrix(dev_session1, ids, pid)
        scores = state.score_both(probes)
        for arm in ARMS:
            totals[arm]['impostor_accepted'] += int(np.count_nonzero(scores[arm] <= threshold))
            totals[arm]['impostor_trials'] += len(probes)
    for value in totals.values():
        value['far'] = value['impostor_accepted'] / value['impostor_trials']
        value['threshold'] = threshold
    return totals


def score_test_account(session1, session2, probes):
    # Oracle updates are independent of either decision: one shared history only.
    history = np.asarray(session1, dtype=float)[-50:].copy()
    state = fit_shared(history)
    impostors = state.score_both(probes)
    genuine = {arm: [] for arm in ARMS}
    for row in session2:
        scores = state.score_both(row[None, :])
        for arm in ARMS:
            genuine[arm].append(float(scores[arm][0]))
        history = np.vstack((history, row))[-50:]
        state = fit_shared(history)
    return {arm: np.array(values) for arm, values in genuine.items()}, impostors


def compare(baseline, candidate):
    left, right = baseline['accounts'], candidate['accounts']
    if [a['participant_id'] for a in left] != [a['participant_id'] for a in right]:
        raise ValueError('Unpaired identities')
    deltas = []
    for a, b in zip(left, right):
        if any(a[k] != b[k] for k in ('genuine_trials', 'impostor_trials')):
            raise ValueError('Unpaired denominators')
        deltas.append({'participant_id': a['participant_id'],
                       'delta_far': float(rate(b, 'far') - rate(a, 'far')),
                       'delta_frr': float(rate(b, 'frr') - rate(a, 'frr'))})
    dfar = macro(right, 'far') - macro(left, 'far')
    dfrr = macro(right, 'frr') - macro(left, 'frr')
    support = dfar < 0 and dfrr <= 0
    return {'delta_macro_far': float(dfar), 'delta_macro_frr': float(dfrr),
            'descriptive_support': support,
            'interpretation': 'descriptive_support' if support else 'tradeoff' if dfar < 0 and dfrr > 0 else 'not_supported',
            'accounts': deltas,
            'direction_counts': {metric: {
                'better': sum(r['delta_' + metric] < 0 for r in deltas),
                'equal': sum(r['delta_' + metric] == 0 for r in deltas),
                'worse': sum(r['delta_' + metric] > 0 for r in deltas)} for metric in ('far', 'frr')}}


def evaluate_dataset(data, dev_ids, test_ids, features, expected, threshold):
    actual = validate_data(data, dev_ids, test_ids, features)
    if actual != expected or not np.isfinite(threshold):
        raise ValueError('Invalid counts or threshold; stop before fitting')
    dev = observe_dev({pid: data[pid][1] for pid in dev_ids}, threshold)
    accounts, pairs = {a: [] for a in ARMS}, {a: [] for a in ARMS}
    transitions = []
    s2 = {pid: data[pid][2] for pid in test_ids}
    for pid in test_ids:
        probes, others = probe_matrix(s2, test_ids, pid)
        genuine, impostors = score_test_account(data[pid][1], s2[pid], probes)
        for arm in ARMS:
            accounts[arm].append({'participant_id': pid, **counts(genuine[arm], impostors[arm], threshold)})
        for j, other in enumerate(others):
            masks = {arm: impostors[arm][j * 10:(j + 1) * 10] <= threshold for arm in ARMS}
            for arm in ARMS:
                accepted = int(np.count_nonzero(masks[arm]))
                pairs[arm].append({'target_id': pid, 'source_id': other,
                                   'impostor_accepted': accepted, 'impostor_trials': 10, 'far': accepted / 10})
            a, b = masks['uniform_cv'], masks['age_weighted_cv']
            transitions.append({'target_id': pid, 'source_id': other,
                                'new_false_accept': int(np.count_nonzero(~a & b)),
                                'recovered_rejection': int(np.count_nonzero(a & ~b)),
                                'accepted_both': int(np.count_nonzero(a & b)),
                                'rejected_both': int(np.count_nonzero(~a & ~b))})
    arms = [{'arm': arm, 'threshold': threshold, 'observed_dev': dev[arm],
             'overall': combine(accounts[arm]), 'macro_far': float(macro(accounts[arm], 'far')),
             'macro_frr': float(macro(accounts[arm], 'frr')), 'accounts': accounts[arm], 'pairs': pairs[arm]}
            for arm in ARMS]
    return {'arms': arms, 'counts': actual, 'comparison': compare(*arms), 'pair_transitions': transitions,
            'shared_detector_and_oof_by_construction': True}
