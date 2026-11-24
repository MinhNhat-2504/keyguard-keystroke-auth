"""Rank and operating-point descriptions of saved scores, without threshold search."""
from bisect import bisect_left,bisect_right
from collections import Counter
import math
from statistics import median

def rank_auc(genuine,attack):
    g=sorted(float(v) for v in genuine);a=[float(v) for v in attack]
    if not g or not a or not all(math.isfinite(v) for v in g+a):raise ValueError('Two finite score groups required')
    wins=ties=0
    for value in a:
        left=bisect_left(g,value);right=bisect_right(g,value)
        wins+=left;ties+=right-left
    numerator=2*wins+ties;denominator=2*len(g)*len(a)
    return {'auc':numerator/denominator,'auc_twice_wins_plus_ties':numerator,
            'auc_twice_pair_count':denominator,'strict_attack_greater_pairs':wins,'equal_pairs':ties}

def summarize_saved_scores(decisions,warnings,threshold,oof_by_profile):
    if not math.isfinite(threshold):raise ValueError('Finite threshold required')
    groups={key:{'genuine':[],'attack':[]} for key in warnings};seen=set();residual=Counter()
    for row in decisions:
        key=(row['phrase'],row['target']);role=row['role'];z=float(row['z'])
        if key not in groups or role not in ('genuine','attack') or not math.isfinite(z):raise ValueError('Invalid saved score')
        if row['accepted'] not in ('True','False') or (row['accepted']=='True')!=(z<=threshold):raise ValueError('Saved flag differs from threshold')
        identity=(*key,role,int(row['source_line']))
        if identity in seen:raise ValueError('Duplicate decision')
        seen.add(identity);groups[key][role].append(z)
        if role=='attack' and z<=threshold and not warnings[key]:residual[(*key,row['attack_subject'])]+=1
    accounts=[]
    for key,scores in groups.items():
        g,a=scores['genuine'],scores['attack']
        if not g or not a:raise ValueError('Both roles required per profile')
        prior=oof_by_profile[key];oof=prior['oof_scores'];total=sum(oof)
        if len(oof)!=20 or not all(math.isfinite(v) and v>=0 for v in oof):raise ValueError('Twenty finite nonnegative OOF scores required')
        row={'phrase':key[0],'target':key[1],'review_required':warnings[key],
             'genuine_trials':len(g),'attack_trials':len(a),
             'genuine_nonmatches_original':sum(v>threshold for v in g),
             'attack_behavioral_passes_original':sum(v<=threshold for v in a),
             'attack_behavioral_passes_after_guard':sum(v<=threshold for v in a) if not warnings[key] else 0,
             **rank_auc(g,a),'cv_center':prior['cv_center'],'cv_scale':prior['cv_scale'],
             'largest_oof_share':max(oof)/total if total else 0.}
        for role,values in scores.items():
            row[role+'_z_min']=min(values);row[role+'_z_median']=median(values);row[role+'_z_max']=max(values)
        accounts.append(row)
    phrases=[]
    for phrase in sorted({key[0] for key in groups}):
        subset=[a for a in accounts if a['phrase']==phrase]
        phrases.append({'phrase':phrase,'profiles':len(subset),
                        'remaining_attack_behavioral_passes':sum(a['attack_behavioral_passes_after_guard'] for a in subset),
                        'genuine_nonmatches_original':sum(a['genuine_nonmatches_original'] for a in subset),
                        'genuine_trials':sum(a['genuine_trials'] for a in subset),
                        'attack_trials':sum(a['attack_trials'] for a in subset),
                        'macro_auc':sum(a['auc'] for a in subset)/len(subset)})
    pairs=[{'phrase':p,'target':t,'attack_subject_code':s,'remaining_behavioral_passes':n}
           for (p,t,s),n in sorted(residual.items(),key=lambda item:(-item[1],item[0]))]
    return {'accounts':accounts,'phrases':phrases,'residual_pairs':pairs,'decisions_count':len(seen),
            'remaining_attack_behavioral_passes':sum(residual.values())}
