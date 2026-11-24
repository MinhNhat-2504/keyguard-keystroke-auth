"""Count distinct saved attack samples across a fixed set of target profiles."""
from collections import Counter,defaultdict
import math

def summarize_exposure(decisions,warnings,threshold):
    if not math.isfinite(threshold) or not warnings:raise ValueError('Finite threshold and profile map required')
    targets=defaultdict(set)
    for phrase,target in warnings:targets[phrase].add(target)
    if any(type(v) is not bool for v in warnings.values()):raise ValueError('Boolean warnings required')
    if len({len(v) for v in targets.values()})!=1:raise ValueError('Fixed target count required')
    n=next(iter(map(len,targets.values())))
    if n<2:raise ValueError('At least two targets required')
    grouped={};seen=set()
    for row in decisions:
        if row['role']=='genuine':continue
        if row['role']!='attack':raise ValueError('Unknown role')
        key=(row['phrase'],int(row['source_line']));target=row['target'];identity=(*key,target)
        if key[0] not in targets or target not in targets[key[0]] or identity in seen:raise ValueError('Invalid or duplicate attack decision')
        seen.add(identity);z=float(row['z'])
        if not math.isfinite(z) or row['accepted'] not in ('True','False') or (row['accepted']=='True')!=(z<=threshold):
            raise ValueError('Invalid score or acceptance flag')
        if not row['attack_subject']:raise ValueError('Attack source code required')
        item=grouped.setdefault(key,dict(subject=row['attack_subject'],before=set(),after=set(),targets=set()))
        if item['subject']!=row['attack_subject']:raise ValueError('Inconsistent source code')
        item['targets'].add(target)
        if row['accepted']=='True':
            item['before'].add(target)
            if not warnings[(key[0],target)]:item['after'].add(target)
    if not grouped or {k[0] for k in grouped}!=set(targets):raise ValueError('All phrases required')
    for (phrase,_),item in grouped.items():
        if item['targets']!=targets[phrase]:raise ValueError('Missing target decision for source sample')
    def summary(items):
        items=list(items);result={'distinct_attack_samples':len(items),'target_decisions':len(items)*n}
        for arm in ('before','after'):
            histogram=Counter(len(item[arm]) for item in items)
            result['targets_passed_histogram_'+arm]=[histogram[k] for k in range(n+1)]
            result['samples_any_target_'+arm]=len(items)-histogram[0]
            result['samples_any_target_rate_'+arm]=(len(items)-histogram[0])/len(items)
            result['accepted_target_decisions_'+arm]=sum(k*v for k,v in histogram.items())
        return result
    return {'target_count_per_sample':n,'overall':summary(grouped.values()),
            'by_phrase':[{'phrase':phrase,**summary(v for k,v in grouped.items() if k[0]==phrase)} for phrase in sorted(targets)]}
