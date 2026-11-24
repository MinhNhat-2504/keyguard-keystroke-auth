"""Elementary one-outlier example; explanatory arithmetic, not an estimator."""
import math

def single_outlier_example(n: int, outlier: float, threshold: float) -> dict:
    """OOF vector has n-1 zeros and one positive M; population SD (ddof=0)."""
    if isinstance(n,bool) or not isinstance(n,int) or n<2:
        raise ValueError('Integer n >= 2 required')
    if not math.isfinite(outlier) or outlier<=0 or not math.isfinite(threshold):
        raise ValueError('Positive finite outlier and finite threshold required')
    center=outlier/n
    sigma=center*math.sqrt(n-1)
    scale=max(sigma,1e-6)
    limit=center+threshold*scale
    if not all(math.isfinite(v) for v in (center,sigma,scale,limit)):
        raise ValueError('Finite example arithmetic required')
    return {'n':n,'outlier':outlier,'threshold':threshold,'center':center,
            'population_sd':sigma,'used_scale':scale,'raw_acceptance_limit':limit,
            'scale_floor_active':sigma<=1e-6,'fixed_raw_score_limit_z':-1/math.sqrt(n-1)}

def standardize_example(raw_score: float, example: dict) -> float:
    if not math.isfinite(raw_score):raise ValueError('Finite raw score required')
    z=(raw_score-example['center'])/example['used_scale']
    if not math.isfinite(z):raise ValueError('Finite standardized score required')
    return z
