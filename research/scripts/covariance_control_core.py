"""Matched diagonal/full shrink-covariance metrics; training-only preprocessing."""
import numpy as np
from keyguard.detectors import ScaledManhattan

ARMS=('diag_lw','full_lw','scaled_manhattan')


def matrix(x):
    x=np.asarray(x,dtype=float)
    if x.ndim!=2 or len(x)<2 or not x.shape[1] or not np.isfinite(x).all():
        raise ValueError('Finite two-dimensional training matrix required')
    return x


def fit_metrics(training):
    from sklearn.covariance import LedoitWolf
    x=matrix(training)
    center=x.mean(axis=0);mad=np.maximum(np.abs(x-center).mean(axis=0),1e-9)
    residual=(x-center)/mad
    fitted=LedoitWolf(assume_centered=True,store_precision=False).fit(residual)
    covariance=fitted.covariance_
    ridge=np.eye(x.shape[1])*1e-9
    full=covariance+ridge;diagonal=np.diag(np.diag(covariance))+ridge
    return {'center':center,'mad':mad,'full_covariance':full,'diagonal_covariance':diagonal,
            'full_precision':np.linalg.inv(full),'diagonal_precision':np.diag(1/np.diag(diagonal)),
            'shrinkage':float(fitted.shrinkage_),'residual_rank':int(np.linalg.matrix_rank(residual)),
            'full_condition_number':float(np.linalg.cond(full)),
            'diagonal_condition_number':float(np.linalg.cond(diagonal))}


def quadratic_score(residual,precision):
    value=np.einsum('ij,jk,ik->i',residual,precision,residual)
    if np.min(value)<-1e-7:raise ValueError('Negative squared distance beyond numerical tolerance')
    return np.sqrt(np.maximum(value,0))


def score(state,rows,arm):
    if arm not in ARMS:raise ValueError('Unknown locked arm')
    x=np.atleast_2d(np.asarray(rows,dtype=float))
    if x.ndim!=2 or x.shape[1]!=len(state['center']) or not np.isfinite(x).all():
        raise ValueError('Finite scoring rows with matching features required')
    residual=(x-state['center'])/state['mad']
    if arm=='scaled_manhattan':return np.abs(residual).sum(axis=1)
    return quadratic_score(residual,state['full_precision' if arm=='full_lw' else 'diagonal_precision'])


def profiles(enrollment):
    x=matrix(enrollment)
    if len(x)!=20:raise ValueError('Exactly20 enrollment rows required')
    oof={a:np.empty(20) for a in ARMS}
    for held in np.array_split(np.arange(20),5):
        keep=np.ones(20,dtype=bool);keep[held]=False
        state=fit_metrics(x[keep])
        for arm in ARMS:oof[arm][held]=score(state,x[held],arm)
    state=fit_metrics(x)
    normalization={a:{'mean':float(oof[a].mean()),'sd':max(float(oof[a].std()),1e-6)} for a in ARMS}
    return state,normalization,oof


def z_scores(profile,rows,arm):
    state,norm,_=profile
    values=(score(state,rows,arm)-norm[arm]['mean'])/norm[arm]['sd']
    if not np.isfinite(values).all():raise ValueError('Nonfinite normalized score')
    return values
