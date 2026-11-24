"""Descriptive group deletion of fixed routing counts, without model fitting."""
from itertools import product

KEYS=('genuine_trials','attack_trials','genuine_additional_verification_before',
      'genuine_additional_verification_after','attack_behavioral_before','attack_behavioral_after')

def totals(rows):
    rows=list(rows)
    if not rows:raise ValueError('Empty subset')
    result={key:sum(r[key] for r in rows) for key in KEYS}
    result['profiles']=len(rows)
    for arm in ('before','after'):
        result['attack_direct_rate_'+arm]=result['attack_behavioral_'+arm]/result['attack_trials']
        result['genuine_extra_rate_'+arm]=result['genuine_additional_verification_'+arm]/result['genuine_trials']
    result['attack_moved_to_extra']=result['attack_behavioral_before']-result['attack_behavioral_after']
    result['genuine_moved_to_extra']=result['genuine_additional_verification_after']-result['genuine_additional_verification_before']
    return result

def summarize_groups(rows):
    rows=[dict(r) for r in rows]
    if not rows:raise ValueError('No profiles')
    seen=set()
    for r in rows:
        identity=(r['target'],r['phrase'])
        if not all(isinstance(x,str) and x for x in identity) or identity in seen:
            raise ValueError('Invalid or duplicate profile')
        seen.add(identity)
        for key in KEYS:
            if type(r[key]) is not int or r[key]<0:raise ValueError('Nonnegative integer counts required')
        if not r['genuine_trials'] or not r['attack_trials']:raise ValueError('Both roles required')
        for arm in ('before','after'):
            if r['genuine_additional_verification_'+arm]>r['genuine_trials'] or r['attack_behavioral_'+arm]>r['attack_trials']:
                raise ValueError('Numerator exceeds denominator')
        if r['attack_behavioral_after']>r['attack_behavioral_before'] or r['genuine_additional_verification_after']<r['genuine_additional_verification_before']:
            raise ValueError('Guard must only divert to extra verification')
    targets=sorted({r['target'] for r in rows});phrases=sorted({r['phrase'] for r in rows})
    if len(targets)<2 or len(phrases)<2 or seen!=set(product(targets,phrases)):
        raise ValueError('Complete target by phrase grid required')
    result={'overall':totals(rows),'targets':targets,'phrases':phrases}
    for axis,names in (('target',targets),('phrase',phrases)):
        result['by_'+axis]=[{'group':name,**totals(r for r in rows if r[axis]==name)} for name in names]
        result['leave_one_'+axis+'_out']=[{'excluded':name,**totals(r for r in rows if r[axis]!=name)} for name in names]
    return result
