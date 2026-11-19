"""Prospective per-target benefit criteria; exact count arithmetic, no fitting."""
from fractions import Fraction

METRICS = {'far': ('impostor_accepted', 'impostor_trials'),
           'frr': ('genuine_rejected', 'genuine_trials')}


def sign(value):
    return 'negative' if value < 0 else 'positive' if value > 0 else 'zero'


def nearest_rank(values, numerator, denominator):
    if not values or not 0 < numerator <= denominator:
        raise ValueError('Nonempty sample and 0 < p <= 1 required')
    index = (numerator * len(values) + denominator - 1) // denominator - 1
    return sorted(values)[index]


def analyze_accounts(baseline, candidate):
    def keyed(rows):
        indexed = {}
        for r in rows:
            pid = r['participant_id']
            if pid in indexed:
                raise ValueError('Duplicate target')
            for n, d in METRICS.values():
                if type(r[n]) is not int or type(r[d]) is not int or not 0 <= r[n] <= r[d] or r[d] <= 0:
                    raise ValueError('Integer counts and positive denominators required')
            indexed[pid] = r
        return indexed
    b, c = keyed(baseline), keyed(candidate)
    if not b or set(b) != set(c):
        raise ValueError('Nonempty matching target sets required')
    grid = {a: {z: 0 for z in ('negative', 'zero', 'positive')} for a in ('negative', 'zero', 'positive')}
    accounts = []
    for pid in sorted(b):
        delta = {}
        for m, (n, d) in METRICS.items():
            if b[pid][d] != c[pid][d]:
                raise ValueError('Same trial denominators required')
            delta[m] = Fraction(c[pid][n], c[pid][d]) - Fraction(b[pid][n], b[pid][d])
        grid[sign(delta['far'])][sign(delta['frr'])] += 1
        accounts.append({'participant_id': pid, 'delta_far': delta['far'], 'delta_frr': delta['frr'],
                         'guarded_frr_benefit': delta['frr'] < 0 and delta['far'] <= 0,
                         'any_error_increased': delta['far'] > 0 or delta['frr'] > 0})
    count = len(accounts)
    macro = {m: sum((a['delta_' + m] for a in accounts), Fraction()) / count for m in METRICS}
    benefits = sum(a['guarded_frr_benefit'] for a in accounts)
    primary = macro['frr'] < 0 and macro['far'] <= 0
    pooled = {method: {m: Fraction(sum(r[n] for r in rows), sum(r[d] for r in rows))
                       for m, (n, d) in METRICS.items()} for method, rows in (('baseline', baseline), ('candidate', candidate))}
    distribution = {}
    for m in METRICS:
        values = [a['delta_' + m] for a in accounts]
        distribution[m] = {'min': min(values), 'q25': nearest_rank(values, 1, 4),
                           'median': nearest_rank(values, 1, 2), 'q75': nearest_rank(values, 3, 4), 'max': max(values)}
    return {'n_targets': count, 'delta_macro': macro, 'pooled': pooled,
            'sign_grid_far_rows_frr_columns': grid, 'guarded_frr_benefit_count': benefits,
            'any_error_increased_count': sum(a['any_error_increased'] for a in accounts),
            'primary_met': primary, 'broad_benefit_met': primary and 2 * benefits > count,
            'distribution_nearest_rank': distribution, 'accounts': accounts}
