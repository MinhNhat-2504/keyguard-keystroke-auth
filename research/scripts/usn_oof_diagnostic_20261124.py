"""Reproduce enrollment-only CV to explain large saved scales; no threshold search."""
import csv
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
def diagnose(enrollment):
    x=np.asarray(enrollment,dtype=float)
    if x.ndim!=2 or len(x)!=20 or not np.isfinite(x).all():raise ValueError('Exactly twenty finite samples required')
    oof=np.empty(20);floors=[];dominant=[]
    for fi,held in enumerate(np.array_split(np.arange(20),5),1):
        train=np.delete(x,held,axis=0);center=train.mean(axis=0)
        mad=np.abs(train-center).mean(axis=0);scale=np.maximum(mad,1e-9)
        contributions=np.abs(x[held]-center)/scale
        oof[held]=contributions.sum(axis=1)
        for j in np.flatnonzero(mad<=1e-9):
            floors.append({'fold':fi,'feature_index':int(j),'held_rows_1based':(held+1).tolist(),
                           'max_held_absolute_deviation':float(np.abs(x[held,j]-center[j]).max()),
                           'max_score_contribution':float(contributions[:,j].max())})
        for k,row in enumerate(contributions):
            j=int(np.argmax(row));total=float(row.sum())
            dominant.append({'held_row_1based':int(held[k]+1),'largest_feature_index':j,
                             'largest_contribution':float(row[j]),'score':total,'fraction':float(row[j]/total) if total else 0})
    final_mad=np.abs(x-x.mean(axis=0)).mean(axis=0)
    return {'cv_center':float(oof.mean()),'cv_scale':float(max(oof.std(),1e-6)),
            'oof_scores':oof.tolist(),'floored_training_features':floors,
            'largest_oof':max(dominant,key=lambda d:d['score']),
            'full_enrollment_floored_feature_indices':np.flatnonzero(final_mad<=1e-9).tolist()}

def main():
    from scripts.usn_fixed_text_adapter import load_source
    source,audit=load_source(ROOT/'data/raw/usn_fixed_text_v1')
    path=ROOT/'results/usn_transfer_20261124_accounts.csv'
    with path.open(encoding='utf-8',newline='') as s:accounts=list(csv.DictReader(s))
    result=[]
    for phrase,item in source.items():
        for pid,rows in item['genuine'].items():
            d=diagnose([r['x'] for r in rows[:20]])
            old=next(a for a in accounts if a['phrase']==phrase and a['participant_id']==pid)
            assert np.isclose(d['cv_center'],float(old['cv_center']),rtol=1e-12,atol=1e-12)
            assert np.isclose(d['cv_scale'],float(old['cv_scale']),rtol=1e-12,atol=1e-12)
            for f in d['floored_training_features']:f['feature_name']=item['header'][f['feature_index']]
            d['largest_oof']['feature_name']=item['header'][d['largest_oof']['largest_feature_index']]
            d['equivalent_raw_score_limit']=d['cv_center']+.2720094565367825*d['cv_scale']
            result.append({'phrase':phrase,'participant_id':pid,**d})
    files=['scripts/usn_oof_diagnostic_20261124.py','scripts/usn_fixed_text_adapter.py','results/usn_transfer_20261124_accounts.csv','results/usn_source_manifest_20261124.json','tests/test_usn_oof_diagnostic.py']
    output={'completed_at_utc':datetime.now(timezone.utc).isoformat(),
            'scope':'Retrospective enrollment-only CV reproduction; original test decisions and threshold unchanged',
            'all_30_saved_cv_summaries_reproduced':True,'profiles':result,
            'source_sha256':{n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in files}}
    with (ROOT/'results/usn_oof_diagnostic_20261124.json').open('x',encoding='utf-8') as s:json.dump(output,s,indent=2);s.write('\n')
    print(json.dumps([{'phrase':d['phrase'],'person':d['participant_id'],'cv_center':d['cv_center'],'cv_scale':d['cv_scale'],'largest_oof':d['largest_oof'],'raw_limit':d['equivalent_raw_score_limit']} for d in result if d['phrase']=='Ob-dollar-erv3r']))

if __name__=='__main__':main()
