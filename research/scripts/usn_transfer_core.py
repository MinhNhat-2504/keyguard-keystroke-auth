"""Fixed static Scaled Manhattan rule, no source-specific parameter search."""
import hashlib
import json
import numpy as np
from keyguard.detectors import ScaledManhattan

def finite(x):
    x=np.asarray(x,dtype=float)
    if x.ndim!=2 or not len(x) or not x.shape[1] or not np.isfinite(x).all():raise ValueError('Finite nonempty matrix required')
    return x

def evaluate_account(enrollment,genuine,impostors,tau):
    e,g,i=map(finite,(enrollment,genuine,impostors))
    if len(e)!=20 or len({x.shape[1] for x in (e,g,i)})!=1 or not np.isfinite(tau):raise ValueError('Invalid locked profile dimensions')
    scores=[]
    for held in np.array_split(np.arange(20),5):
        scores.extend(ScaledManhattan().fit(np.delete(e,held,axis=0)).score(e[held]).tolist())
    center=float(np.mean(scores));scale=float(max(np.std(scores),1e-6))
    model=ScaledManhattan().fit(e)
    g_scores=(model.score(g)-center)/scale;i_scores=(model.score(i)-center)/scale
    if not np.isfinite(g_scores).all() or not np.isfinite(i_scores).all():raise ValueError('Nonfinite normalized scores')
    state={'detector':model.to_dict(),'cv_center':center,'cv_scale':scale,'threshold':tau}
    decisions=lambda values:[{'z':float(v),'accepted':bool(v<=tau)} for v in values]
    return {'genuine_trials':len(g),'genuine_rejected':int(np.count_nonzero(g_scores>tau)),
            'impostor_trials':len(i),'impostor_accepted':int(np.count_nonzero(i_scores<=tau)),
            'profile_sha256':hashlib.sha256(json.dumps(state,sort_keys=True).encode()).hexdigest(),
            'cv_center':center,'cv_scale':scale,'genuine_decisions':decisions(g_scores),'impostor_decisions':decisions(i_scores)}
