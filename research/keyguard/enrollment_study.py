"""Enrollment-only quality control and robust score calibration, research only."""
from dataclasses import dataclass
import numpy as np

from keyguard.detectors import ScaledManhattan


@dataclass(frozen=True)
class EnrollmentVariant:
    quality: str
    calibration: str

    @property
    def name(self):
        return f'{self.quality}__{self.calibration}'


VARIANTS = [EnrollmentVariant(q, c) for q in ('keep_all', 'robust_filter')
            for c in ('mean_std', 'median_mad', 'median_iqr')]


def quality_mask(X, policy):
    """Predeclared rule: row median robust deviation > median + 3 robust sigma.

    Keep >=80% of available enrollment, never force removal. All statistics come
    from this training matrix; in cross-validation this excludes validation rows.
    """
    X = np.asarray(X, dtype=float)
    if X.ndim != 2 or len(X) < 4 or not np.isfinite(X).all():
        raise ValueError('Need >=4 finite enrollment rows')
    if policy == 'keep_all':
        return np.ones(len(X), dtype=bool)
    if policy != 'robust_filter':
        raise ValueError('Unknown enrollment quality policy')
    center = np.median(X, axis=0)
    scale = np.maximum(1.4826 * np.median(np.abs(X-center), axis=0), 1e-9)
    row_scores = np.median(np.abs(X-center)/scale, axis=1)
    med = np.median(row_scores)
    cutoff = med + 3 * max(1.4826 * np.median(np.abs(row_scores-med)), 1e-9)
    candidates = np.flatnonzero(row_scores > cutoff)
    max_remove = len(X) - int(np.ceil(.8*len(X)))
    order = candidates[np.argsort(-row_scores[candidates], kind='stable')][:max_remove]
    mask = np.ones(len(X), dtype=bool)
    mask[order] = False
    return mask


def calibration_stats(scores, method):
    scores = np.asarray(scores, dtype=float)
    if scores.ndim != 1 or not len(scores) or not np.isfinite(scores).all():
        raise ValueError('Scores must be finite and nonempty')
    if method == 'mean_std':
        center, scale = scores.mean(), scores.std()
    elif method == 'median_mad':
        center = np.median(scores)
        scale = 1.4826 * np.median(np.abs(scores-center))
    elif method == 'median_iqr':
        center = np.median(scores)
        scale = (np.quantile(scores,.75)-np.quantile(scores,.25))/1.349
    else:
        raise ValueError('Unknown calibration method')
    return float(center), float(max(scale, 1e-6))


def fit_enrollment(X, variant):
    X = np.asarray(X, dtype=float)
    quality_mask(X, variant.quality)  # validate before CV
    scores = np.empty(len(X))
    for held in np.array_split(np.arange(len(X)), min(5,len(X))):
        train = np.delete(X, held, axis=0)
        mask = quality_mask(train, variant.quality)
        scores[held] = ScaledManhattan().fit(train[mask]).score(X[held])
    center, scale = calibration_stats(scores, variant.calibration)
    mask = quality_mask(X, variant.quality)
    detector = ScaledManhattan().fit(X[mask])
    return detector, center, scale, mask, scores


def enrollment_caches(data, variant, n_enroll=20):
    result, diagnostics = {}, []
    if len(data)<4 or any(len(X)<n_enroll+5 for X in data.values()):
        raise ValueError('Insufficient identities/samples')
    for pid, X in data.items():
        enrollment = X[:n_enroll]
        detector, center, scale, mask, scores = fit_enrollment(enrollment, variant)
        result[pid] = {
            'genuine': (detector.score(X[n_enroll:])-center)/scale,
            'impostors': {other:{stage:(detector.score(Y[indices])-center)/scale
                                  for stage,indices in [('early',slice(0,5)),('late',slice(-5,None))]}
                          for other,Y in data.items() if other!=pid},
        }
        diagnostics.append({'participant_id':pid, 'variant':variant.name,
                            'enrollment_rows':n_enroll,'kept':int(mask.sum()),
                            'removed_positions_1based':(np.flatnonzero(~mask)+1).tolist(),
                            'score_center':center,'score_scale':scale,
                            'cv_score_min':float(scores.min()),'cv_score_max':float(scores.max())})
    return result, diagnostics
