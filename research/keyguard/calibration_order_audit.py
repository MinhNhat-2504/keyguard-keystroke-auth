"""Fixed enrollment-only perturbations of CV partitions, not a new policy."""
import math
import numpy as np
from keyguard.calibration_preflight import audit_calibration
from keyguard.detectors import ScaledManhattan

def fixed_orders():
    base=np.arange(20)
    return {'original':base,'reverse_control':base[::-1],
            'rotate1':np.roll(base,-1),'rotate2':np.roll(base,-2),'rotate3':np.roll(base,-3)}

def audit_orderings(enrollment,threshold):
    if not math.isfinite(threshold):raise ValueError('Finite fixed threshold required')
    x=np.asarray(enrollment,dtype=float)
    original=audit_calibration(x)
    full=ScaledManhattan().fit(x);cases=[]
    for name,indices in fixed_orders().items():
        audit=original if name=='original' else audit_calibration(x[indices])
        aligned=np.empty(20);aligned[indices]=audit.oof_scores
        candidate=ScaledManhattan().fit(x[indices])
        events=[]
        for e in audit.floor_extrapolations:
            events.append({'fold':e.fold,'feature_index':e.feature_index,
                           'held_original_rows_1based':[int(indices[i-1])+1 for i in e.held_rows_1based]})
        cases.append({'ordering':name,'indices_0based':indices.tolist(),
                      'review_required':audit.review_required,'cv_std_at_floor':audit.cv_std_at_floor,
                      'floor_events':events,'cv_center':audit.cv_center,'cv_scale':audit.cv_scale,
                      'oof_scores_original_order':aligned.tolist(),
                      'raw_acceptance_limit':audit.cv_center+threshold*audit.cv_scale,
                      'full_pool_parameters_close':bool(np.allclose(candidate.mean_,full.mean_,rtol=1e-12,atol=1e-12) and np.allclose(candidate.mad_,full.mad_,rtol=1e-12,atol=1e-12))})
    reverse=cases[1]
    control=bool(np.allclose(reverse['oof_scores_original_order'],original.oof_scores,rtol=1e-10,atol=1e-9)
                 and reverse['review_required']==original.review_required)
    limits=[c['raw_acceptance_limit'] for c in cases]
    return {'cases':cases,'reverse_control_close':control,
            'warning_changes_across_orderings':any(c['review_required']!=original.review_required for c in cases),
            'raw_limit_min':min(limits),'raw_limit_max':max(limits),
            'raw_limit_max_min_ratio':max(limits)/min(limits) if min(limits)>0 else None}
