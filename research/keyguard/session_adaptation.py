"""Ordered-session adaptation, with verified genuine updates as an oracle assumption."""
import numpy as np
from keyguard.detectors import ScaledManhattan
from keyguard.soft_weighting import WeightedManhattan

METHODS = ('static', 'window50', 'decay20')


def fit_history(X, method):
    if method not in METHODS:
        raise ValueError('Unknown adaptation method')
    X = np.asarray(X, dtype=float)
    if X.ndim != 2 or len(X) < 10 or not np.isfinite(X).all():
        raise ValueError('Need >=10 finite history rows')
    if method != 'static':
        X = X[-50:]
    weights = np.power(.5, (len(X)-1-np.arange(len(X)))/20) if method == 'decay20' else np.ones(len(X))
    cv_scores = np.empty(len(X))
    for held in np.array_split(np.arange(len(X)), 5):
        keep = np.ones(len(X), dtype=bool); keep[held] = False
        detector = (WeightedManhattan().fit(X[keep], weights[keep]) if method == 'decay20'
                    else ScaledManhattan().fit(X[keep]))
        cv_scores[held] = detector.score(X[held])
    detector = WeightedManhattan().fit(X, weights) if method == 'decay20' else ScaledManhattan().fit(X)
    return detector, float(cv_scores.mean()), float(max(cv_scores.std(), 1e-6))


def score_session_stream(X, sessions, impostors, method):
    X = np.asarray(X, dtype=float)
    sessions = np.asarray(sessions)
    if method not in METHODS or len(X) != len(sessions) or len(X) < 25:
        raise ValueError('Invalid method/stream')
    if np.any(np.diff(sessions) < 0) or np.any(sessions[:20] != sessions[0]):
        raise ValueError('Sessions must be ordered; enrollment must be within first session')
    history = X[:20].copy()
    model, center, scale = fit_history(history, method)
    result = {'genuine': [], 'impostor': []}
    for index in range(20, len(X)):
        session = int(sessions[index])
        if index == 20 or sessions[index] != sessions[index-1]:
            probe = (model.score(impostors)-center)/scale
            result['impostor'].append({'session': session, 'scores': probe})
        z = float((model.score(X[index])[0]-center)/scale)
        result['genuine'].append({'session': session, 'z': z})
        if method != 'static':
            # Updates use only the already-scored genuine sample, never a future sample/probe.
            history = np.vstack([history, X[index]])[-50:]
            model, center, scale = fit_history(history, method)
    return result
