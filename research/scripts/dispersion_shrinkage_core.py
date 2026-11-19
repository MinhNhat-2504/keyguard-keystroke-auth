"""Static-profile MAD shrinkage; no mutation of frozen detector code."""
import numpy as np

from keyguard.detectors import ScaledManhattan
from keyguard.evaluation import threshold_at_far
from keyguard.matched_adaptation import compare_arms, probe_matrix
from keyguard.research import combine, counts

ARMS = {'baseline': 0.0, 'shrink25': 0.25}


def matrix(x):
    x = np.asarray(x, dtype=float)
    if x.ndim != 2 or len(x) < 2 or not x.shape[1] or not np.isfinite(x).all():
        raise ValueError('Finite 2D matrix with at least two rows required')
    return x


def prior_from_enrollment(enrollments, exclude=None):
    matrices = [matrix(x)[:20] for pid, x in enrollments.items() if pid != exclude]
    if not matrices or any(len(x) != 20 or x.shape[1] != matrices[0].shape[1] for x in matrices):
        raise ValueError('Other identities with twenty enrollment rows required')
    return np.maximum(np.median([np.abs(x - x.mean(axis=0)).mean(axis=0) for x in matrices], axis=0), 1e-9)


def detector(x, prior, weight):
    x = matrix(x)
    if weight not in (0.0, 0.25):
        raise ValueError('Only the locked baseline/shrink25 arms are allowed')
    model = ScaledManhattan().fit(x)
    if weight:
        prior = np.asarray(prior, dtype=float)
        if prior.shape != (x.shape[1],) or not np.isfinite(prior).all() or np.any(prior <= 0):
            raise ValueError('Finite positive feature prior required')
        local = np.abs(x - model.mean_).mean(axis=0)
        model.mad_ = np.maximum(.75 * local + .25 * prior, 1e-9)
    return model


def fit_profile(enrollment, prior, weight):
    x = matrix(enrollment)
    if len(x) != 20:
        raise ValueError('Exactly twenty enrollment rows required')
    scores = []
    for held in np.array_split(np.arange(20), 5):
        keep = np.ones(20, dtype=bool)
        keep[held] = False
        scores.append(detector(x[keep], prior, weight).score(x[held]))
    oof = np.concatenate(scores)
    return detector(x, prior, weight), float(oof.mean()), float(max(oof.std(), 1e-6))


def z_scores(state, x):
    model, center, scale = state
    values = (model.score(x) - center) / scale
    if not np.isfinite(values).all():
        raise ValueError('Nonfinite z scores')
    return values


def calibrate(dev_s1, arm):
    weight = ARMS[arm]
    scores = []
    for pid in dev_s1:
        prior = prior_from_enrollment(dev_s1, exclude=pid)
        state = fit_profile(dev_s1[pid][:20], prior, weight)
        probes, _ = probe_matrix(dev_s1, list(dev_s1), pid)
        scores.append(z_scores(state, probes))
    scores = np.concatenate(scores)
    threshold = threshold_at_far(scores, .05)
    accepted = int(np.count_nonzero(scores <= threshold))
    if accepted > int(np.floor(.05 * len(scores))):
        raise ValueError('Dev FAR budget exceeded')
    return {'threshold': threshold, 'impostor_trials': len(scores), 'impostor_accepted': accepted,
            'far': accepted / len(scores)}


def evaluate(test, prior, arm, calibration):
    accounts = []
    s2 = {pid: x[2] for pid, x in test.items()}
    for pid in test:
        state = fit_profile(test[pid][1][:20], prior, ARMS[arm])
        probes, _ = probe_matrix(s2, list(test), pid)
        accounts.append({'participant_id': pid, **counts(z_scores(state, s2[pid]),
                                                        z_scores(state, probes), calibration['threshold'])})
    from keyguard.matched_adaptation import macro
    return {'method': arm, 'calibration': calibration, 'accounts': accounts,
            'overall': combine(accounts), 'macro_far': float(macro(accounts, 'far')),
            'macro_frr': float(macro(accounts, 'frr'))}


def run_dataset(data, dev_ids, test_ids):
    if set(dev_ids) & set(test_ids) or set(data) != set(dev_ids) | set(test_ids):
        raise ValueError('Disjoint, exhaustive identity partitions required')
    dev_s1 = {pid: data[pid][1] for pid in dev_ids}
    prior = prior_from_enrollment(dev_s1)
    calibrations = {arm: calibrate(dev_s1, arm) for arm in ARMS}
    test = {pid: data[pid] for pid in test_ids}
    arms = [evaluate(test, prior, arm, calibrations[arm]) for arm in ARMS]
    return {'arms': arms, 'comparison': compare_arms(*arms), 'prior': prior.tolist()}


def diagnose(dev_s1):
    """Enrollment-only DEV diagnostic; no test probes or candidate scores."""
    records = []
    for pid in dev_s1:
        x = matrix(dev_s1[pid])[:20]
        prior = prior_from_enrollment(dev_s1, exclude=pid)
        local = np.abs(x - x.mean(axis=0)).mean(axis=0)
        contributions = []
        for held in np.array_split(np.arange(20), 5):
            keep = np.ones(20, dtype=bool)
            keep[held] = False
            model = detector(x[keep], None, 0.0)
            contributions.append(np.abs(x[held] - model.mean_) / model.mad_)
        values = np.vstack(contributions)
        shares = values / np.maximum(values.sum(axis=1, keepdims=True), 1e-9)
        for j in range(x.shape[1]):
            records.append({'participant_id': pid, 'feature_index': j, 'local_mad': float(local[j]),
                            'prior': float(prior[j]), 'local_to_prior_ratio': float(local[j] / prior[j]),
                            'floor_active': bool(local[j] <= 1e-9),
                            'oof_mean_raw_contribution': float(values[:, j].mean()),
                            'oof_mean_score_share': float(shares[:, j].mean())})
    return records
