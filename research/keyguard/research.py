"""Exploratory feature/threshold experiments; no change to deployed profiles.

Outer folds separate both target and impostor identities. Enrollment always uses
the first 20 chronological samples. Sample normalization never fits on test data.
"""
from __future__ import annotations

from dataclasses import dataclass
import numpy as np

from keyguard.detectors import ScaledManhattan
from keyguard.evaluation import threshold_at_far
from keyguard.features import FEATURE_NAMES
from keyguard.model import genuine_score_stats

GROUPS = {name: np.array([i for i, f in enumerate(FEATURE_NAMES)
                         if name == 'all' or f.startswith(name + '.')])
          for name in ('all', 'H', 'DD', 'UD')}
NORMALIZATIONS = ('raw', 'duration', 'median_hold')
MODELS = ('mean_mad', 'median_mad')


@dataclass(frozen=True)
class Variant:
    model: str
    features: str
    normalization: str

    @property
    def name(self):
        return f'{self.model}__{self.features}__{self.normalization}'


VARIANTS = [Variant(m, f, n) for m in MODELS for f in GROUPS for n in NORMALIZATIONS]
BASELINE = Variant('mean_mad', 'all', 'raw').name


class MedianManhattan:
    """Median center / median absolute deviation, with the baseline's floor."""
    def fit(self, X):
        self.center = np.median(X, axis=0)
        self.scale = np.maximum(np.median(np.abs(X - self.center), axis=0), 1e-9)
        return self

    def score(self, X):
        return np.sum(np.abs(np.atleast_2d(X) - self.center) / self.scale, axis=1)


def transform(X, variant):
    X = np.asarray(X, dtype=float)
    if X.ndim != 2 or X.shape[1] != 31 or not np.isfinite(X).all():
        raise ValueError('Expected finite N x 31 features')
    if variant.normalization == 'raw':
        denominator = np.ones(len(X))
    elif variant.normalization == 'duration':
        # down(last)-down(first) + hold(last), in seconds; UD can be negative.
        denominator = X[:, GROUPS['DD']].sum(axis=1) + X[:, -1]
    elif variant.normalization == 'median_hold':
        denominator = np.median(X[:, GROUPS['H']], axis=1)
    else:
        raise ValueError('Unknown normalization')
    if np.any(denominator <= 0):
        raise ValueError('Nonpositive sample duration/median hold')
    return (X / denominator[:, None])[:, GROUPS[variant.features]]


def score_accounts(data, variant, n_enroll=20):
    if len(data) < 4 or any(len(X) < n_enroll + 5 for X in data.values()):
        raise ValueError('Need >=4 identities and enrollment + 5 genuine trials each')
    transformed = {pid: transform(X, variant) for pid, X in data.items()}
    detector_cls = ScaledManhattan if variant.model == 'mean_mad' else MedianManhattan
    if variant.model not in MODELS:
        raise ValueError('Unknown model')
    result = {}
    for pid, X in transformed.items():
        enrollment = X[:n_enroll]
        mu, sigma = genuine_score_stats(detector_cls, enrollment, 5)
        detector = detector_cls().fit(enrollment)
        result[pid] = {
            'genuine': (detector.score(X[n_enroll:]) - mu) / sigma,
            'impostors': {
                other: {
                    'early': (detector.score(Y[:5]) - mu) / sigma,
                    'late': (detector.score(Y[-5:]) - mu) / sigma,
                } for other, Y in transformed.items() if other != pid
            },
        }
    return result


def pool(cache, ids, scenario='both'):
    if len(ids) < 2 or len(set(ids)) != len(ids):
        raise ValueError('Need >=2 distinct identities per partition')
    scenarios = ('early', 'late') if scenario == 'both' else (scenario,)
    genuine = np.concatenate([cache[pid]['genuine'] for pid in ids])
    impostors = np.concatenate([cache[pid]['impostors'][other][s]
                               for pid in ids for other in ids if other != pid
                               for s in scenarios])
    return genuine, impostors


def counts(genuine, impostors, threshold):
    return {
        'genuine_trials': len(genuine),
        'genuine_rejected': int(np.count_nonzero(genuine > threshold)),
        'impostor_trials': len(impostors),
        'impostor_accepted': int(np.count_nonzero(impostors <= threshold)),
        'far': float(np.mean(impostors <= threshold)),
        'frr': float(np.mean(genuine > threshold)),
    }


def roc(genuine, impostors):
    """Full empirical ROC at tied score boundaries, accept score <= threshold."""
    g, i = np.sort(genuine), np.sort(impostors)
    if not len(g) or not len(i) or not np.isfinite(np.r_[g, i]).all():
        raise ValueError('Scores must be finite and nonempty')
    unique = np.unique(np.r_[g, i])
    thresholds = np.r_[np.nextafter(unique[0], -np.inf), unique]
    far = np.searchsorted(i, thresholds, side='right') / len(i)
    tar = np.searchsorted(g, thresholds, side='right') / len(g)
    delta = 1 - tar - far
    right = int(np.flatnonzero(delta <= 0)[0])
    if delta[right] == 0:
        eer = far[right]
    else:
        left = right - 1
        weight = delta[left] / (delta[left] - delta[right])
        eer = far[left] + weight * (far[right] - far[left])
    return thresholds, far, tar, float(eer), float(np.trapezoid(tar, far))


def curve(genuine, impostors, extra=()):
    """Bounded display grid; counts at every displayed threshold are exact."""
    thresholds, _, _, eer, auc = roc(genuine, impostors)
    idx = np.unique(np.linspace(0, len(thresholds) - 1, min(121, len(thresholds))).astype(int))
    thresholds = np.unique(np.r_[thresholds[idx], extra])
    points = [{'threshold': float(t), **counts(genuine, impostors, t)} for t in thresholds]
    return {'eer': eer, 'auc': auc, 'points': points}


def identity_folds(ids, n_folds=3, seed=42):
    if len(set(ids)) != len(ids) or len(ids) < n_folds * 2:
        raise ValueError('Need >=2 distinct identities per fold')
    shuffled = np.random.default_rng(seed).permutation(sorted(ids))
    return [sorted(str(x) for x in fold) for fold in np.array_split(shuffled, n_folds)]


def choose_variant(caches, dev_ids, target_far=0.05, seed=42):
    """Inner identity CV; no access to outer-test identities or their scores."""
    folds = identity_folds(dev_ids, n_folds=2, seed=seed)
    rows = []
    for name, cache in caches.items():
        errors = []
        for val in folds:
            train = sorted(set(dev_ids) - set(val))
            _, impostors = pool(cache, train)
            tau = threshold_at_far(impostors, target_far)
            g, i = pool(cache, val)
            rates = counts(g, i, tau)
            errors.append((rates['far'] + rates['frr']) / 2)
        rows.append({'variant': name, 'inner_balanced_error': float(np.mean(errors))})
    rows.sort(key=lambda row: (row['inner_balanced_error'], row['variant']))
    return rows[0]['variant'], rows


def combine(rows):
    totals = {key: sum(r[key] for r in rows) for key in (
        'genuine_trials', 'genuine_rejected', 'impostor_trials', 'impostor_accepted')}
    totals['far'] = totals['impostor_accepted'] / totals['impostor_trials']
    totals['frr'] = totals['genuine_rejected'] / totals['genuine_trials']
    return totals
