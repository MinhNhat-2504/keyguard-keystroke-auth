"""Enrollment quality/calibration study, preserving prior protocols and config."""
import csv
import hashlib
import json
from pathlib import Path
import sys
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
sys.stdout.reconfigure(encoding='utf-8')
from keyguard.collected import load_collected
from keyguard.enrollment_study import VARIANTS,enrollment_caches
from keyguard.evaluation import threshold_at_far
from keyguard.research import pool,counts,choose_variant,combine,roc


def main():
    original=(ROOT/'results/research_summary.json').read_bytes()
    reference=json.loads(original)
    config=(ROOT/'models/model_config.json').read_bytes()
    assert hashlib.sha256(config).hexdigest()==reference['protocol']['config_sha256']
    manifest=json.loads((ROOT/'data/collected_manifest.json').read_text(encoding='utf-8'))
    for entry in manifest['files']:
        assert hashlib.sha256((ROOT/entry['path']).read_bytes()).hexdigest()==entry['sha256']
    df,issues=load_collected(str(ROOT/'data/collected/*.jsonl'),duplicate_policy='exclude-all',
                             require_timestamp=True,order='timestamp')
    data={pid:np.vstack(g.x.to_list()) for pid,g in df.groupby('participant_id')}
    caches,diagnostics={},[]
    for variant in VARIANTS:
        cache,diag=enrollment_caches(data,variant)
        caches[variant.name]=cache
        diagnostics.extend(diag)
    output={'date':'2026-11-13','protocol':{
        'samples':len(df),'excluded':len(issues),'enrollment':20,'profile':'static',
        'source_research_sha256':hashlib.sha256(original).hexdigest(),
        'code_sha256':hashlib.sha256((ROOT/'keyguard/enrollment_study.py').read_bytes()).hexdigest(),
        'config_sha256':hashlib.sha256(config).hexdigest(),
        'predeclared_quality_rule':'row median robust deviations > median + 3 robust sigma, remove <=20%',
        'cv_quality_fitted_inside_training_fold':True,
        'score_cv':'all 20 held-out enrollment scores, including flagged samples',
        'calibrations':['mean/std','median/1.4826 MAD','median/IQR divided by 1.349'],
        'limitations':['exploratory on previously inspected data','predominantly one session',
                       'no account-specific test-derived rules','no config changes']},
        'selection_by_fold':[],'variants':[],'enrollment_diagnostics':diagnostics}
    for j,split in enumerate(reference['selection_by_fold']):
        selected,ranking=choose_variant(caches,split['dev_ids'],.05,seed=42+j)
        output['selection_by_fold'].append({**{k:split[k] for k in ('fold','dev_ids','test_ids')},
                                           'selected_variant':selected,'inner_ranking':ranking})
    rows=[]
    for variant in VARIANTS:
        cache=caches[variant.name]
        result={'id':variant.name,'quality':variant.quality,'calibration':variant.calibration,'folds':[]}
        for j,split in enumerate(output['selection_by_fold']):
            dg,di=pool(cache,split['dev_ids']);tg,ti=pool(cache,split['test_ids'])
            tau=threshold_at_far(di,.05)
            _,_,_,eer,auc=roc(tg,ti)
            accounts=[]
            for pid in split['test_ids']:
                g=cache[pid]['genuine']
                imp=np.concatenate([cache[pid]['impostors'][other][s] for other in split['test_ids']
                                    if other!=pid for s in ('early','late')])
                accounts.append({'participant_id':pid,**counts(g,imp,tau)})
            row={'fold':j+1,'threshold':tau,'dev':counts(dg,di,tau),'test':counts(tg,ti,tau),
                 'eer':eer,'auc':auc,'accounts':accounts}
            assert row['dev']['far']<=.05
            assert combine(accounts)==row['test']
            result['folds'].append(row)
            rows.append({'variant':variant.name,'fold':j+1,'threshold':tau,**row['test'],'eer':eer,'auc':auc})
        result['overall']=combine([r['test'] for r in result['folds']])
        result['mean_eer']=float(np.mean([r['eer'] for r in result['folds']]))
        result['mean_auc']=float(np.mean([r['auc'] for r in result['folds']]))
        output['variants'].append(result)
    by_name={v['id']:v for v in output['variants']}
    output['nested_selected']=combine([by_name[split['selected_variant']]['folds'][j]['test']
                                      for j,split in enumerate(output['selection_by_fold'])])
    output['baseline']=by_name['keep_all__mean_std']['overall']
    assert output['baseline']==reference['baseline_recalibrated']
    assert original==(ROOT/'results/research_summary.json').read_bytes()
    assert config==(ROOT/'models/model_config.json').read_bytes()
    (ROOT/'results/enrollment_study.json').write_text(json.dumps(output,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    with (ROOT/'results/enrollment_comparison.csv').open('w',encoding='utf-8',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    (ROOT/'explorer/enrollment-data.js').write_text('window.KEYGUARD_ENROLLMENT = '+json.dumps(output,ensure_ascii=False,allow_nan=False)+';\n',encoding='utf-8')
    print(json.dumps({'baseline':output['baseline'],'nested_selected':output['nested_selected'],
                      'selected':[s['selected_variant'] for s in output['selection_by_fold']],
                      'quality_removed':[(r['participant_id'],r['kept']) for r in diagnostics
                                         if r['variant']=='robust_filter__mean_std' and r['kept']<20]},indent=2))


if __name__=='__main__':main()
