"""Descriptive error diagnostics; never select a new threshold from test errors."""
import numpy as np

from keyguard.detectors import ScaledManhattan
from keyguard.evaluation import threshold_at_far
from keyguard.features import FEATURE_NAMES
from keyguard.model import genuine_score_stats
from keyguard.research import GROUPS, MedianManhattan, counts, pool, transform


def score_quantiles(scores):
    return [float(x) for x in np.quantile(scores, [.1, .5, .9])]


def feature_shares(training, samples, variant, limit=5):
    """Contributions to the nonnegative Manhattan distance, not to z or causality."""
    if not len(samples):
        return []
    if variant.model == 'mean_mad':
        center = training.mean(axis=0)
        scale = np.mean(np.abs(training - center), axis=0)
    else:
        center = np.median(training, axis=0)
        scale = np.median(np.abs(training - center), axis=0)
    contribution = (np.abs(samples - center) / np.maximum(scale, 1e-9)).mean(axis=0)
    total = float(contribution.sum())
    order = np.argsort(-contribution, kind='stable')[:limit]
    names = [FEATURE_NAMES[i] for i in GROUPS[variant.features]]
    return [{'feature': names[j], 'share': float(contribution[j] / total) if total else 0.0,
             'mean_distance_component': float(contribution[j])} for j in order]


def account_diagnostic(data, cache, variant, pid, ids, threshold, n_enroll=20):
    if pid not in ids or len(set(ids)) != len(ids) or len(ids) < 2:
        raise ValueError('Target must belong to a partition with distinct identities')
    g = cache[pid]['genuine']
    others = [other for other in ids if other != pid]
    i = np.concatenate([cache[pid]['impostors'][other][stage]
                        for other in others for stage in ('early', 'late')])
    genuine_X = transform(data[pid], variant)
    enrollment = genuine_X[:n_enroll]
    test = genuine_X[n_enroll:]
    impostor_X = np.vstack([transform(data[other], variant)[indices]
                           for other in others for indices in (slice(0, 5), slice(-5, None))])
    detector_cls = ScaledManhattan if variant.model == 'mean_mad' else MedianManhattan
    mu, sigma = genuine_score_stats(detector_cls, enrollment, 5)
    detector = detector_cls().fit(enrollment)
    scale = detector.mad_ if variant.model == 'mean_mad' else detector.scale
    duration = data[pid][:, GROUPS['DD']].sum(axis=1) + data[pid][:, -1]
    row = {
        'participant_id': pid, **counts(g, i, threshold), 'threshold': float(threshold),
        'genuine_z_q10_q50_q90': score_quantiles(g),
        'impostor_z_q10_q50_q90': score_quantiles(i),
        'enrollment_cv_mean': mu, 'enrollment_cv_std': sigma,
        'dispersion_floor_dimensions': int(np.count_nonzero(scale <= 1e-9)),
        'feature_dimensions': len(scale),
        'duration_enrollment_median': float(np.median(duration[:n_enroll])),
        'duration_genuine_median': float(np.median(duration[n_enroll:])),
        'duration_ratio_test_enrollment': float(np.median(duration[n_enroll:]) / np.median(duration[:n_enroll])),
        'rejected_genuine_top_features': feature_shares(enrollment, test[g > threshold], variant),
        'accepted_impostor_top_features': feature_shares(enrollment, impostor_X[i <= threshold], variant),
    }
    pairs = []
    for other in others:
        early = cache[pid]['impostors'][other]['early']
        late = cache[pid]['impostors'][other]['late']
        pairs.append({'target': pid, 'impostor': other,
                      'accepted_early': int(np.count_nonzero(early <= threshold)),
                      'accepted_late': int(np.count_nonzero(late <= threshold)),
                      'accepted': int(np.count_nonzero(np.r_[early, late] <= threshold)),
                      'trials': len(early) + len(late),
                      'median_z': float(np.median(np.r_[early, late]))})
    return row, pairs


def threshold_jackknife(cache, dev_ids, target_far=.05):
    """Remove one dev identity from BOTH target and impostor roles, dev only."""
    if len(dev_ids) < 3:
        raise ValueError('Need >=3 dev identities')
    rows = []
    for removed in dev_ids:
        kept = [pid for pid in dev_ids if pid != removed]
        _, impostors = pool(cache, kept)
        rows.append({'removed_id': removed,
                     'threshold': threshold_at_far(impostors, target_far),
                     'impostor_trials': len(impostors)})
    return rows
