"""One frozen source-transfer evaluation, no source-specific parameter fitting."""
import argparse
import csv
from datetime import datetime,timezone
import hashlib
from importlib import metadata
import json
from pathlib import Path
import platform
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
P='results/usn_transfer_20261124_'
PROTOCOL='docs/USN_TRANSFER_PROTOCOL_20261124.md'
CODE=['scripts/usn_fixed_text_adapter.py','scripts/usn_transfer_core.py','scripts/run_usn_transfer_20261124.py',
      'tests/test_usn_fixed_text.py','keyguard/detectors.py']
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def now():return datetime.now(timezone.utc).isoformat()
def read(s):return json.loads((ROOT/(P+s)).read_text(encoding='utf-8'))
def write(s,x):
    with (ROOT/(P+s)).open('x',encoding='utf-8') as out:json.dump(x,out,ensure_ascii=False,indent=2,allow_nan=False);out.write('\n')
def verify(hashes):
    for name,h in hashes.items():
        if sha(ROOT/name)!=h:raise RuntimeError('Frozen file differs: '+name)
def environment():return {'python':sys.version,'platform':platform.platform(),'packages':{p:metadata.version(p) for p in ('numpy','pytest')}}

def freeze():
    source=json.loads((ROOT/'results/usn_source_manifest_20261124.json').read_text(encoding='utf-8'))
    assert source['license']['name']=='CC BY 4.0' and source['version']==1
    raw={f['file']:f['sha256'] for f in source['files']};verify(raw)
    hashes={n:sha(ROOT/n) for n in CODE}
    t=subprocess.run([sys.executable,'-m','pytest','tests/test_usn_fixed_text.py','-q','-p','no:cacheprovider'],cwd=ROOT,capture_output=True,text=True,encoding='utf-8')
    print(t.stdout+t.stderr)
    if t.returncode:raise RuntimeError('Synthetic tests failed')
    verify(hashes)
    protected={p.relative_to(ROOT).as_posix():sha(p) for p in (ROOT/'report').glob('*') if p.suffix in ('.docx','.pdf') and not p.name.startswith('~$')}
    protected.update({n:sha(ROOT/n) for n in ('models/model_config.json','results/enrollment_selection_20261124_results.json')})
    write('synthetic_tests.json',{'completed_at_utc':now(),'exit_code':0,'stdout':t.stdout,'stderr':t.stderr})
    write('freeze.json',{'frozen_at_utc':now(),'protocol':PROTOCOL,'protocol_sha256':sha(ROOT/PROTOCOL),
                        'source_manifest_sha256':sha(ROOT/'results/usn_source_manifest_20261124.json'),
                        'schema_audit_sha256':sha(ROOT/'results/usn_schema_audit_20261124.json'),
                        'code_sha256':hashes,'raw_sha256':raw,'protected_sha256':protected,'environment':environment(),
                        'threshold':.2720094565367825,'enrollment':20,'folds':5,'updates':False,
                        'scoring_before_freeze':False,'test_report_sha256':sha(ROOT/(P+'synthetic_tests.json'))})
    with (ROOT/(P+'freeze.sha256')).open('x') as out:out.write(sha(ROOT/(P+'freeze.json'))+'\n')
    print('FROZEN; no USN model scores computed')

def check():
    f=read('freeze.json')
    assert sha(ROOT/(P+'freeze.json'))==(ROOT/(P+'freeze.sha256')).read_text().strip()
    assert f['environment']==environment()
    verify({**f['code_sha256'],**f['raw_sha256'],**f['protected_sha256'],f['protocol']:f['protocol_sha256'],
            'results/usn_source_manifest_20261124.json':f['source_manifest_sha256'],
            'results/usn_schema_audit_20261124.json':f['schema_audit_sha256'],P+'synthetic_tests.json':f['test_report_sha256']})
    return f

def run():
    import numpy as np
    from scripts.usn_fixed_text_adapter import load_source
    from scripts.usn_transfer_core import evaluate_account
    f=check()
    for s in ('started.json','results.json','accounts.csv','decisions.csv'):
        if (ROOT/(P+s)).exists():raise RuntimeError('Refuse repeat or overwrite')
    write('started.json',{'started_at_utc':now(),'freeze_sha256':sha(ROOT/(P+'freeze.json'))})
    data,audit=load_source(ROOT/'data/raw/usn_fixed_text_v1')
    assert audit['raw_rows']==8069 and audit['retained_rows']==8042 and audit['excluded_rows']==27
    rows=[];decisions=[]
    for phrase,item in data.items():
        attack=np.asarray([r['x'] for r in item['attack']])
        for pid,records in item['genuine'].items():
            x=np.asarray([r['x'] for r in records])
            a=evaluate_account(x[:20],x[20:],attack,f['threshold'])
            row={'phrase':phrase,'participant_id':pid,'feature_count':len(item['header']),'enrollment_samples':20,
                 **{k:v for k,v in a.items() if not k.endswith('_decisions')}}
            row['far']=row['impostor_accepted']/row['impostor_trials'];row['frr']=row['genuine_rejected']/row['genuine_trials'];rows.append(row)
            for role,original,scored in [('genuine',records[20:],a['genuine_decisions']),('attack',item['attack'],a['impostor_decisions'])]:
                for r,s in zip(original,scored):decisions.append({'phrase':phrase,'target':pid,'role':role,'source_line':r['line'],'attack_subject':r['subject'] if role=='attack' else '', 'z':s['z'],'accepted':s['accepted']})
    def summary(items):
        counts={key:sum(r[key] for r in items) for key in ('genuine_trials','genuine_rejected','impostor_trials','impostor_accepted')}
        return {**counts,'accounts':len(items),'pooled_far':counts['impostor_accepted']/counts['impostor_trials'],
                'pooled_frr':counts['genuine_rejected']/counts['genuine_trials'],
                'macro_far':float(np.mean([r['far'] for r in items])),'macro_frr':float(np.mean([r['frr'] for r in items])),
                'accounts_far_above_5pct':sum(r['impostor_accepted']*20>r['impostor_trials'] for r in items)}
    result={'completed_at_utc':now(),'freeze_sha256':sha(ROOT/(P+'freeze.json')),'threshold':f['threshold'],
            'by_phrase':{p:summary([r for r in rows if r['phrase']==p]) for p in data},'overall':summary(rows),
            'unique_genuine_people':5,'account_phrase_profiles':30,'unique_attack_rows':2042,
            'independent_trials_claim':False,'multi_day_validation':False,'chronological_order_verified':False,
            'candidate_selection_tested':False,'new_source_first_scoring':True,'source_specific_tuning':False,'production_changed':False,
            'scope':'Fixed static scoring/threshold rule on a previously unscored source; descriptive, not a model-improvement or production claim'}
    assert result['overall']['genuine_trials']==5400 and result['overall']['impostor_trials']==10210
    check()
    for suffix,values in [('accounts.csv',rows),('decisions.csv',decisions)]:
        with (ROOT/(P+suffix)).open('x',encoding='utf-8',newline='') as out:
            w=csv.DictWriter(out,fieldnames=list(values[0]));w.writeheader();w.writerows(values)
    write('results.json',result)
    print(json.dumps(result))

if __name__=='__main__':
    p=argparse.ArgumentParser();g=p.add_mutually_exclusive_group(required=True)
    for op in ('freeze','check','run'):g.add_argument('--'+op,action='store_true')
    args=p.parse_args()
    if args.freeze:freeze()
    elif args.check:check();print('FROZEN FILES MATCH')
    else:run()
