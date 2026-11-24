"""Fixed-budget enrollment selection study; independent of production profiles."""
from fractions import Fraction
import hashlib
import numpy as np

from keyguard.detectors import ScaledManhattan
from keyguard.evaluation import threshold_at_far

ARMS = ('first10', 'last10', 'cover10')
POOL = 20
STORED = 10


def matrix(values, minimum=1):
    x = np.asarray(values, dtype=float)
    if x.ndim != 2 or len(x) < minimum or not x.shape[1] or not np.isfinite(x).all():
        raise ValueError('Expected a finite nonempty matrix')
    return x


def distances(pool):
    x = matrix(pool)
    center = np.median(x, axis=0)
    scale = np.maximum(1.4826 * np.median(np.abs(x-center), axis=0), 1e-9)
    normalized = (x-center)/scale
    return np.abs(normalized[:, None]-normalized[None, :]).mean(axis=2)


def select(pool, arm):
    x = matrix(pool, STORED)
    if arm == 'first10':
        return np.arange(STORED)
    if arm == 'last10':
        return np.arange(len(x)-STORED, len(x))
    if arm != 'cover10':
        raise ValueError('Unknown locked selection arm')
    d = distances(x)
    selected = [int(np.argmin(d.sum(axis=1)))]
    while len(selected) < STORED:
        nearest = d[:, selected].min(axis=1)
        nearest[selected] = -np.inf
        selected.append(int(np.argmax(nearest)))
    return np.sort(selected)


def profile(pool, arm):
    x = matrix(pool, POOL)
    if len(x) != POOL:
        raise ValueError('Exactly twenty candidate samples required')
    oof = np.empty(POOL)
    for held in np.array_split(np.arange(POOL), 5):
        train = np.delete(x, held, axis=0)
        support = select(train, arm)
        oof[held] = ScaledManhattan().fit(train[support]).score(x[held])
    chosen = select(x, arm)
    model = ScaledManhattan().fit(x[chosen])
    return {'model': model, 'center': float(oof.mean()), 'scale': float(max(oof.std(), 1e-6)),
            'selected': (chosen+1).tolist(), 'oof': oof,
            'coverage_radius': float(distances(x)[:, chosen].min(axis=1).max())}


def z_score(state, x):
    z = (state['model'].score(matrix(x))-state['center'])/state['scale']
    if not np.isfinite(z).all():
        raise ValueError('Nonfinite normalized score')
    return z


def split_existing_dev(ids):
    ids = sorted(ids)
    if len(ids) < 12 or len(ids) != len(set(ids)):
        raise ValueError('At least twelve unique existing DEV identities required')
    ranked = sorted(ids, key=lambda p: hashlib.sha256(('20261124:'+p).encode()).hexdigest())
    cut = 2*len(ids)//3
    return sorted(ranked[:cut]), sorted(ranked[cut:])


def probes(data, ids, target):
    # Both the source identities and their later-session samples belong to this partition.
    source = [p for p in ids if p != target]
    if not source:
        raise ValueError('Need another identity for impostor probes')
    return np.vstack([np.vstack((data[p]['future'][:5], data[p]['future'][-5:])) for p in source])


def validate_data(data, calibration, evaluation):
    if len(calibration) != len(set(calibration)) or len(evaluation) != len(set(evaluation)):
        raise ValueError('Duplicate partition identity')
    if set(calibration) & set(evaluation) or set(data) != set(calibration) | set(evaluation):
        raise ValueError('Partitions must be disjoint and exhaustive')
    if min(len(calibration), len(evaluation)) < 2:
        raise ValueError('Insufficient identities')
    dimensions = set()
    for item in data.values():
        pool, future = matrix(item['pool'], POOL), matrix(item['future'], 10)
        if len(pool) != POOL or pool.shape[1] != future.shape[1]:
            raise ValueError('Invalid pool or future dimensions')
        dimensions.add(pool.shape[1])
    if len(dimensions) != 1:
        raise ValueError('Feature schema differs across identities')


def metrics(rows):
    ni = sum(r['impostor_trials'] for r in rows)
    ng = sum(r['genuine_trials'] for r in rows)
    fa = sum(r['impostor_accepted'] for r in rows)
    fr = sum(r['genuine_rejected'] for r in rows)
    return {'genuine_trials': ng, 'genuine_rejected': fr, 'impostor_trials': ni,
            'impostor_accepted': fa, 'pooled_far': fa/ni, 'pooled_frr': fr/ng,
            'macro_far': float(sum((Fraction(r['impostor_accepted'], r['impostor_trials']) for r in rows), Fraction())/len(rows)),
            'macro_frr': float(sum((Fraction(r['genuine_rejected'], r['genuine_trials']) for r in rows), Fraction())/len(rows))}


def compare(control, candidate):
    if [r['participant_id'] for r in control] != [r['participant_id'] for r in candidate]:
        raise ValueError('Account pairing differs')
    deltas = []
    for a, b in zip(control, candidate):
        if (a['genuine_trials'], a['impostor_trials']) != (b['genuine_trials'], b['impostor_trials']):
            raise ValueError('Trial denominators differ')
        dfa = Fraction(b['impostor_accepted']-a['impostor_accepted'], a['impostor_trials'])
        dfr = Fraction(b['genuine_rejected']-a['genuine_rejected'], a['genuine_trials'])
        deltas.append((dfa, dfr))
    far, frr = [sum((d[i] for d in deltas), Fraction())/len(deltas) for i in range(2)]
    benefit = sum(a <= 0 and b < 0 for a, b in deltas)
    harm = sum(a > 0 or b > 0 for a, b in deltas)
    rng = np.random.default_rng(20261124)
    array = np.array([[float(a), float(b)] for a,b in deltas])
    sampled = array[rng.integers(len(array),size=(10000,len(array)))].mean(axis=1)*100
    intervals = np.quantile(sampled,[.025,.975],axis=0)
    return {'delta_macro_far': float(far), 'delta_macro_frr': float(frr),
            'delta_macro_far_exact': str(far), 'delta_macro_frr_exact': str(frr),
            'accounts': len(deltas), 'benefited_accounts': benefit, 'harmed_accounts': harm,
            'unchanged_accounts': sum(a == 0 and b == 0 for a,b in deltas),
            'primary_met': bool(far <= 0 and frr < 0), 'majority_benefit_met': 2*benefit > len(deltas),
            'continuation_gate_met': bool(far <= 0 and frr < 0 and 2*benefit > len(deltas)),
            'conditional_account_bootstrap_pp': {'delta_far': intervals[:,0].tolist(), 'delta_frr': intervals[:,1].tolist()},
            'interval_scope': 'Paired target-account resampling; cross-target shared-impostor dependence not modelled; descriptive only'}


def run_dataset(data, calibration, evaluation):
    validate_data(data, calibration, evaluation)
    result = {}
    for arm in ARMS:
        states = {p: profile(data[p]['pool'], arm) for p in sorted(data)}
        calibration_scores = np.concatenate([z_score(states[p],probes(data,calibration,p)) for p in calibration])
        tau = threshold_at_far(calibration_scores,.05)
        fa_calibration = int(np.count_nonzero(calibration_scores <= tau))
        if fa_calibration > int(np.floor(.05*len(calibration_scores))):
            raise ValueError('Calibration FAR budget exceeded')
        accounts=[]
        for pid in evaluation:
            genuine=z_score(states[pid],data[pid]['future'])
            impostor=z_score(states[pid],probes(data,evaluation,pid))
            accounts.append({'participant_id':pid, 'genuine_trials':len(genuine),
                             'genuine_rejected':int(np.count_nonzero(genuine > tau)),
                             'impostor_trials':len(impostor), 'impostor_accepted':int(np.count_nonzero(impostor <= tau)),
                             'stored_samples':STORED, 'candidate_pool':POOL,
                             'selected_positions_1based':states[pid]['selected'],
                             'coverage_radius':states[pid]['coverage_radius']})
        result[arm]={'threshold':tau, 'calibration_impostor_trials':len(calibration_scores),
                     'calibration_impostor_accepted':fa_calibration,
                     'accounts':accounts, 'metrics':metrics(accounts)}
    comparisons={name:compare(result[name]['accounts'],result['cover10']['accounts']) for name in ARMS[:2]}
    return {'arms':result, 'cover10_minus_controls':comparisons,
            'continuation_gate_met':all(c['continuation_gate_met'] for c in comparisons.values())}
