"""Recompute the new study's summaries from saved counts, without model imports."""
from collections import Counter
import argparse
import csv
from datetime import datetime
from fractions import Fraction
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
P='results/enrollment_selection_20261124_'

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--saved-only',action='store_true',help='Audit public counts; explicitly report absent raw and historical reports')
    args=parser.parse_args()
    def read(s):return json.loads((ROOT/(P+s)).read_text(encoding='utf-8'))
    plan,lock,result,started=map(read,['plan.json','freeze.json','results.json','started.json'])
    checks=0
    def require(value):
        nonlocal checks
        assert value
        checks+=1
    require(datetime.fromisoformat(lock['frozen_at_utc']) < datetime.fromisoformat(started['started_at_utc']) < datetime.fromisoformat(result['completed_at_utc']))
    unavailable=[]
    for name,h in {**lock['code_sha256'],**lock['raw_sha256'],**lock['protected_sha256']}.items():
        if args.saved_only and name in lock['protected_sha256']:
            unavailable.append({'path':name,'reason':'Local historical preservation check is outside saved-count mode','present':(ROOT/name).exists()});continue
        if not (ROOT/name).exists() and args.saved_only and name not in lock['code_sha256']:
            unavailable.append({'path':name,'reason':'Raw unavailable in this checkout','present':False});continue
        require(hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==h)
    with (ROOT/(P+'accounts.csv')).open(encoding='utf-8',newline='') as stream:csv_rows=list(csv.DictReader(stream))
    datasets={};all_gates=[]
    for d in plan['datasets']:
        name=d['name'];data=result['datasets'][name]
        require(not set(d['calibration_ids'])&set(d['evaluation_ids']))
        require(not (set(d['calibration_ids'])|set(d['evaluation_ids']))&set(d['excluded_old_test_ids']))
        genuine=Counter()
        raw_available=(ROOT/d['raw_file']).exists()
        if raw_available:
            with (ROOT/d['raw_file']).open(encoding='utf-8-sig',newline='') as stream:
                for r in csv.DictReader(stream):
                    pid=r['subject'] if name=='CMU' else r['participant']
                    session=r['sessionIndex'] if name=='CMU' else r['session']
                    if pid in d['evaluation_ids'] and int(session)==2:genuine[pid]+=1
        else:require(args.saved_only)
        for arm,a in data['arms'].items():
            rows=[r for r in csv_rows if r['dataset']==name and r['arm']==arm]
            require([r['participant_id'] for r in rows]==d['evaluation_ids'])
            require(a['calibration_impostor_trials']==len(d['calibration_ids'])*(len(d['calibration_ids'])-1)*10)
            require(Fraction(a['calibration_impostor_accepted'],a['calibration_impostor_trials'])<=Fraction(1,20))
            for saved,row in zip(a['accounts'],rows):
                for f in ('genuine_trials','genuine_rejected','impostor_trials','impostor_accepted','stored_samples','candidate_pool'):
                    require(saved[f]==int(row[f]))
                selected=list(map(int,row['selected_positions_1based'].split()))
                require(selected==saved['selected_positions_1based'] and len(set(selected))==10 and all(1<=x<=20 for x in selected))
                if raw_available:require(int(row['genuine_trials'])==genuine[row['participant_id']])
                require(int(row['impostor_trials'])==(len(d['evaluation_ids'])-1)*10)
            for metric,num,den in [('far','impostor_accepted','impostor_trials'),('frr','genuine_rejected','genuine_trials')]:
                total=sum(int(r[num]) for r in rows);trials=sum(int(r[den]) for r in rows)
                macro=sum((Fraction(int(r[num]),int(r[den])) for r in rows),Fraction())/len(rows)
                require(a['metrics'][num]==total and a['metrics'][den]==trials)
                require(abs(a['metrics']['pooled_'+metric]-float(Fraction(total,trials)))<1e-14)
                require(abs(a['metrics']['macro_'+metric]-float(macro))<1e-14)
        gates=[]
        for control,c in data['cover10_minus_controls'].items():
            rows=data['arms'][control]['accounts'];candidate=data['arms']['cover10']['accounts']
            deltas=[]
            for a,b in zip(rows,candidate):
                deltas.append((Fraction(b['impostor_accepted']-a['impostor_accepted'],a['impostor_trials']),Fraction(b['genuine_rejected']-a['genuine_rejected'],a['genuine_trials'])))
            df,dr=[sum((v[i] for v in deltas),Fraction())/len(deltas) for i in (0,1)]
            benefits=sum(a<=0 and b<0 for a,b in deltas)
            gate=df<=0 and dr<0 and benefits*2>len(deltas)
            require(str(df)==c['delta_macro_far_exact'] and str(dr)==c['delta_macro_frr_exact'])
            require(benefits==c['benefited_accounts'] and gate==c['continuation_gate_met'])
            gates.append(bool(gate))
        require(data['continuation_gate_met']==all(gates));all_gates.extend(gates)
        datasets[name]={'evaluation_accounts':len(d['evaluation_ids']),'genuine_trials':data['arms']['first10']['metrics']['genuine_trials'],'raw_metadata_counts_checked':raw_available,'impostor_trials_per_arm':len(d['evaluation_ids'])*(len(d['evaluation_ids'])-1)*10,'continuation_gate_met':all(gates)}
    require(result['continuation_gate_met']==all(all_gates))
    record={'status':'passed','independent_count_checks':checks,'datasets':datasets,'source':'Saved account CSV/JSON with raw metadata when present; no model or metric-core import','archives_not_checked':unavailable,'new_source_scored':False}
    (ROOT/(P+('audit_saved.json' if args.saved_only else 'audit.json'))).write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(record))

if __name__=='__main__':main()
