"""Static/sliding/decayed history on CMU, dev-only threshold selection."""
import csv
import hashlib
import json
from pathlib import Path
import sys
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.stdout.reconfigure(encoding='utf-8')
from keyguard.features import load_cmu, FEATURE_NAMES
from keyguard.evaluation import threshold_at_far
from keyguard.research import counts, combine, roc
from keyguard.session_adaptation import METHODS, score_session_stream


def main():
    config_bytes = (ROOT/'models/model_config.json').read_bytes(); cfg = json.loads(config_bytes)
    cmu_path = ROOT/'data/raw/DSL-StrongPasswordData.csv'
    df = load_cmu(cmu_path)
    subjects = {pid: g.sort_values(['sessionIndex','rep']) for pid,g in df.groupby('subject')}
    result = {'date':'2026-11-13','protocol':{
        'dev_ids': cfg['dev_users'], 'test_ids': cfg['test_users'],
        'enrollment':'first20 in session1','genuine':'all remaining380 ordered by session/rep',
        'impostors':'first5+last5 of every other subject IN SAME partition, once at each session start',
        'checkpoints':'session1 after enrollment, then starts of sessions2..8; probes never update',
        'updates':'only genuine after scoring; all genuine assumed independently verified, no impostor injection',
        'methods':list(METHODS), 'window':50,'decay_half_life_genuine_samples':20,
        'calibration':'mean/std of 5-fold scores on current past history; age weights restricted to train indices',
        'threshold':'one per method on pooled DEV impostor scores with FAR<=5%, frozen over test sessions',
        'config_sha256':hashlib.sha256(config_bytes).hexdigest(),
        'cmu_sha256':hashlib.sha256(cmu_path.read_bytes()).hexdigest(),
        'code_sha256':hashlib.sha256((ROOT/'keyguard/session_adaptation.py').read_bytes()).hexdigest(),
        'limitations':['all CMU subjects previously benchmarked; exploratory split, not fresh holdout',
                       'oracle verification, not measured OTP quality',
                       'repeated impostor probes dependent, no per-trial independence CI',
                       'not directly comparable to previous checkpoint protocols, no production config changes']},
        'methods':[]}
    csv_rows = []
    for method in METHODS:
        partitions = {}
        for name, ids in [('dev',cfg['dev_users']),('test',cfg['test_users'])]:
            streams = {}
            for pid in ids:
                g = subjects[pid]
                others = [subjects[other][FEATURE_NAMES].to_numpy()[indices]
                          for other in ids if other != pid for indices in (slice(0,5),slice(-5,None))]
                streams[pid] = score_session_stream(g[FEATURE_NAMES].to_numpy(),g.sessionIndex.to_numpy(),np.vstack(others),method)
            partitions[name] = streams
            print(method,name,len(streams),'subjects completed',flush=True)
        dev_imp = np.concatenate([point['scores'] for stream in partitions['dev'].values() for point in stream['impostor']])
        tau = threshold_at_far(dev_imp,.05)
        item = {'id':method,'threshold':tau,'dev_far':float(np.mean(dev_imp<=tau)), 'partitions':{}}
        assert item['dev_far']<=.05
        for name, streams in partitions.items():
            accounts, by_session = [], []
            for pid, stream in streams.items():
                g = np.array([p['z'] for p in stream['genuine']])
                i = np.concatenate([p['scores'] for p in stream['impostor']])
                accounts.append({'participant_id':pid,**counts(g,i,tau)})
            for session in range(1,9):
                g = np.array([p['z'] for stream in streams.values() for p in stream['genuine'] if p['session']==session])
                i = np.concatenate([p['scores'] for stream in streams.values() for p in stream['impostor'] if p['session']==session])
                _,_,_,eer,auc = roc(g,i)
                row={'session':session,**counts(g,i,tau),'eer':eer,'auc':auc}
                by_session.append(row)
                csv_rows.append({'method':method,'partition':name,'threshold':tau,**row})
            aggregate = combine(accounts)
            assert aggregate == combine(by_session)
            item['partitions'][name] = {'overall':aggregate,'sessions':by_session,'accounts':accounts}
        result['methods'].append(item)
    assert config_bytes == (ROOT/'models/model_config.json').read_bytes()
    (ROOT/'results/session_adaptation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    with (ROOT/'results/session_adaptation.csv').open('w',encoding='utf-8',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(csv_rows[0]));writer.writeheader();writer.writerows(csv_rows)
    (ROOT/'explorer/adaptation-data.js').write_text('window.KEYGUARD_ADAPTATION = '+json.dumps(result,ensure_ascii=False,allow_nan=False)+';\n',encoding='utf-8')
    print(json.dumps([{r['id']:r['partitions']['test']['overall']} for r in result['methods']],indent=2))


if __name__=='__main__':main()
