"""Enrollment-only soft weighting; research estimators separate from production."""
import numpy as np

from keyguard.detectors import ScaledManhattan
from keyguard.enrollment_study import calibration_stats, quality_mask

QUALITIES = ('keep_all', 'hard_filter', 'soft_weight')
CALIBRATIONS = ('mean_std', 'median_mad', 'median_iqr')


def soft_weights(X):
    X = np.asarray(X, dtype=float)
    if X.ndim != 2 or len(X) < 5 or not np.isfinite(X).all():
        raise ValueError('Need >=5 finite enrollment samples')
    center = np.median(X, axis=0)
    scale = np.maximum(1.4826 * np.median(np.abs(X - center), axis=0), 1e-9)
    deviations = np.median(np.abs(X - center) / scale, axis=1)
    median = np.median(deviations)
    cutoff = median + 3 * max(1.4826 * np.median(np.abs(deviations - median)), 1e-9)
    # Prespecified continuous shrinkage above the cutoff; no row ever has zero weight.
    return np.maximum(.25, np.minimum(1., cutoff / np.maximum(deviations, 1e-9)))


class WeightedManhattan:
    def fit(self, X, weights):
        X = np.asarray(X, dtype=float)
        weights = np.asarray(weights, dtype=float)
        if X.ndim != 2 or weights.shape != (len(X),) or not np.isfinite(X).all() or not np.isfinite(weights).all() or np.any(weights <= 0):
            raise ValueError('Finite samples and positive weights required')
        self.mean_ = np.average(X, axis=0, weights=weights)
        self.mad_ = np.maximum(np.average(np.abs(X - self.mean_), axis=0, weights=weights), 1e-9)
        return self

    def score(self, X):
        return (np.abs(np.atleast_2d(X) - self.mean_) / self.mad_).sum(axis=1)


def fit_quality(X, quality):
    if quality == 'keep_all':
        return ScaledManhattan().fit(X), np.ones(len(X))
    if quality == 'hard_filter':
        mask = quality_mask(X, 'robust_filter')
        return ScaledManhattan().fit(X[mask]), mask.astype(float)
    if quality == 'soft_weight':
        weights = soft_weights(X)
        return WeightedManhattan().fit(X, weights), weights
    raise ValueError('Unknown quality rule')


def fit_calibrated(X, quality, calibration):
    X = np.asarray(X, dtype=float)
    if X.ndim != 2 or len(X) < 10 or not np.isfinite(X).all():
        raise ValueError('Need >=10 finite enrollment samples')
    scores = np.empty(len(X))
    for held in np.array_split(np.arange(len(X)), 5):
        training = np.delete(X, held, axis=0)
        detector, _ = fit_quality(training, quality)
        scores[held] = detector.score(X[held])
    center, scale = calibration_stats(scores, calibration)
    detector, weights = fit_quality(X, quality)
    return detector, center, scale, weights


def build_caches(data, quality, calibration):
    cache, diagnostics = {}, []
    for pid, X in data.items():
        detector, center, scale, weights = fit_calibrated(X[:20], quality, calibration)
        cache[pid] = {
            'genuine': (detector.score(X[20:]) - center) / scale,
            'impostors': {other: {stage: (detector.score(Y[index]) - center) / scale
                                   for stage, index in [('early', slice(0, 5)), ('late', slice(-5, None))]}
                          for other, Y in data.items() if other != pid},
        }
        diagnostics.append({'participant_id': pid, 'quality': quality, 'calibration': calibration,
                            'weights': weights.tolist(), 'positive_weights': int(np.count_nonzero(weights)),
                            'effective_samples': float(weights.sum() ** 2 / np.sum(weights ** 2)),
                            'score_center': center, 'score_scale': scale})
    return cache, diagnostics


def descriptive(values):
    values = np.asarray(values, dtype=float)
    return {'mean': float(values.mean()), 'std_across_splits': float(values.std(ddof=1)) if len(values) > 1 else 0.,
            'min': float(values.min()), 'max': float(values.max())}
