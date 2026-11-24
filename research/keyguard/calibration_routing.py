"""Paired routing counts from saved scores; no final authentication outcomes."""
from collections import Counter
import math

from keyguard.calibration_preflight import CalibrationAudit, behavioral_acceptance_allowed

def summarize_routes(decisions, audits: dict[tuple[str,str], CalibrationAudit], threshold: float):
    if not math.isfinite(threshold) or not audits:
        raise ValueError('Finite threshold and enrollment audits required')
    profiles={key:Counter() for key in audits};seen=set();used=set()
    for row in decisions:
        key=(row['phrase'],row['target']);role=row['role']
        if key not in audits or role not in ('genuine','attack'):
            raise ValueError('Unknown profile or decision role')
        z=float(row['z'])
        if not math.isfinite(z):raise ValueError('Finite saved score required')
        if row['accepted'] not in ('True','False'):raise ValueError('Strict saved decision flag required')
        baseline=row['accepted']=='True'
        if baseline != (z<=threshold):raise ValueError('Saved decision does not match original threshold')
        identity=(*key,role,int(row['source_line']))
        if identity in seen:raise ValueError('Duplicate saved decision')
        seen.add(identity);used.add(key)
        guarded=behavioral_acceptance_allowed(audits[key],z,threshold)
        if guarded and not baseline:raise ValueError('Preflight must not expand behavioral acceptance')
        c=profiles[key]
        c[role+'_trials']+=1
        c[role+'_behavioral_before']+=int(baseline)
        c[role+'_behavioral_after']+=int(guarded)
        c[role+'_additional_verification_before']+=int(not baseline)
        c[role+'_additional_verification_after']+=int(not guarded)
        c[role+'_moved_to_verification']+=int(baseline and not guarded)
    if used!=set(audits):raise ValueError('Every enrollment profile needs saved decisions')
    output=[];total=Counter()
    for (phrase,target),c in profiles.items():
        for role in ('genuine','attack'):
            if c[role+'_trials']==0:raise ValueError('Both roles required for each profile')
            for arm in ('before','after'):
                assert c[role+'_behavioral_'+arm]+c[role+'_additional_verification_'+arm]==c[role+'_trials']
        output.append({'phrase':phrase,'target':target,'review_required':audits[(phrase,target)].review_required,**dict(c)})
        total.update(c)
    counts=dict(total)
    counts['final_attack_acceptance_count_bounds_after']=[counts['attack_behavioral_after'],counts['attack_trials']]
    counts['final_genuine_rejection_count_bounds_after']=[0,counts['genuine_additional_verification_after']]
    return {'profiles':output,'overall':counts,'profile_count':len(output),
            'scope':'Retrospective behavioral-path routing, not measured final FAR/FRR or OTP outcomes',
            'production_changed':False,'scores_or_threshold_changed':False,'otp_success_assumed':False}
