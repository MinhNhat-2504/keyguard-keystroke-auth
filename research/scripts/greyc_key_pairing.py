"""Conservative same-key pairing; reject ambiguous overlapping repeated keys."""
from collections import defaultdict
import math

MODIFIERS=frozenset({'16','17','18','91','92','93'})


def parse(text):
    result=[]
    for index,line in enumerate(text.splitlines()):
        if not line.strip():continue
        fields=line.split()
        if len(fields)!=2:raise ValueError('Expected code and timestamp')
        code,t=fields[0],float(fields[1])
        if not code.isdigit() or not math.isfinite(t):raise ValueError('Finite timestamp and numeric code required')
        result.append({'code':code,'t':t,'index':index})
    if any(a['t']>b['t'] for a,b in zip(result,result[1:])):
        raise ValueError('Events within each stream must be chronological')
    return result


def pair_keys(press,release):
    downs,ups=defaultdict(list),defaultdict(list)
    ignored=[]
    for label,events,target in [('press',parse(press),downs),('release',parse(release),ups)]:
        for event in events:
            if event['code'] in MODIFIERS:ignored.append({'kind':label,**event})
            else:target[event['code']].append(event)
    pairs=[];issues=[]
    if not downs and not ups:issues.append({'code':None,'reason':'no_non_modifier_events'})
    for code in sorted(set(downs)|set(ups)):
        d,u=downs[code],ups[code]
        if len(d)!=len(u):
            issues.append({'code':code,'reason':'unbalanced','press_count':len(d),'release_count':len(u)})
            continue
        if len(d)>12:
            issues.append({'code':code,'reason':'too_many_repetitions_for_exact_pairing'});continue
        solutions=[]
        def search(i,remaining,assignment):
            if len(solutions)>=2:return
            if i==len(u):solutions.append(assignment);return
            for j in remaining:
                if d[j]['t']<=u[i]['t']:
                    search(i+1,[k for k in remaining if k!=j],assignment+[(j,i)])
        search(0,list(range(len(d))),[])
        if len(solutions)!=1:
            issues.append({'code':code,'reason':'ambiguous' if solutions else 'release_before_press_or_impossible'})
            continue
        for di,ui in solutions[0]:
            pairs.append({'code':code,'press_t':d[di]['t'],'release_t':u[ui]['t'],
                          'press_index':d[di]['index'],'release_index':u[ui]['index'],
                          'hold':u[ui]['t']-d[di]['t']})
    pairs.sort(key=lambda p:(p['press_t'],p['press_index']))
    return {'status':'resolved' if not issues else 'unresolved','pairs':pairs,'issues':issues,
            'ignored_modifiers':ignored,'modifier_policy':sorted(MODIFIERS)}
