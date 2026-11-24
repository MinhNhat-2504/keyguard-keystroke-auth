"""Retrospective sensitivity on saved outcomes; standard library, no model fit."""
from collections import Counter,defaultdict
import csv
from datetime import datetime,timezone
from fractions import Fraction
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
P='results/usn_sensitivity_20261124'

def aggregate(rows):
    if not rows:raise ValueError('Nonempty account rows required')
    counts={k:sum(int(r[k]) for r in rows) for k in ('genuine_trials','genuine_rejected','impostor_trials','impostor_accepted')}
    if min(counts['genuine_trials'],counts['impostor_trials'])<=0:raise ValueError('Positive denominators required')
    return {**counts,'profiles':len(rows),'pooled_far':float(Fraction(counts['impostor_accepted'],counts['impostor_trials'])),
            'pooled_frr':float(Fraction(counts['genuine_rejected'],counts['genuine_trials'])),
            'macro_far':float(sum((Fraction(int(r['impostor_accepted']),int(r['impostor_trials'])) for r in rows),Fraction())/len(rows)),
            'macro_frr':float(sum((Fraction(int(r['genuine_rejected']),int(r['genuine_trials'])) for r in rows),Fraction())/len(rows)),
            'profiles_far_above_5pct':sum(int(r['impostor_accepted'])*20>int(r['impostor_trials']) for r in rows)}

def missing_bounds(accepted,trials,missing_decisions):
    if not (0<=accepted<=trials and trials>0 and missing_decisions>=0):raise ValueError('Invalid counts')
    denominator=trials+missing_decisions
    return {'retained_accepted':accepted,'retained_trials':trials,'additional_unknown_decisions':missing_decisions,
            'raw_row_scenario_trials':denominator,'lower':float(Fraction(accepted,denominator)),
            'upper':float(Fraction(accepted+missing_decisions,denominator))}

def analyze(rows,excluded_attack_rows):
    ids=sorted({r['participant_id'] for r in rows});phrases=sorted({r['phrase'] for r in rows})
    if len(ids)<2 or len(phrases)<2:raise ValueError('Multiple people and phrases required')
    overall=aggregate(rows)
    people={p:aggregate([r for r in rows if r['participant_id']==p]) for p in ids}
    leave_people={p:aggregate([r for r in rows if r['participant_id']!=p]) for p in ids}
    leave_phrases={p:aggregate([r for r in rows if r['phrase']!=p]) for p in phrases}
    ranking=sorted(rows,key=lambda r:(-int(r['impostor_accepted']),r['participant_id'],r['phrase']))
    return {'overall':overall,'by_person':people,'leave_one_person':leave_people,'leave_one_phrase':leave_phrases,
            'highest_fa_profile':{'participant_id':ranking[0]['participant_id'],'phrase':ranking[0]['phrase'],
                                  'impostor_accepted':int(ranking[0]['impostor_accepted']),
                                  'impostor_trials':int(ranking[0]['impostor_trials']),
                                  'fraction_of_all_false_accepts':int(ranking[0]['impostor_accepted'])/overall['impostor_accepted'] if overall['impostor_accepted'] else 0},
            'excluded_attack_decision_bounds':missing_bounds(overall['impostor_accepted'],overall['impostor_trials'],excluded_attack_rows*len(ids))}

def main():
    paths=['results/usn_transfer_20261124_accounts.csv','results/usn_transfer_20261124_decisions.csv',
           'results/usn_transfer_20261124_results.json','results/usn_schema_audit_20261124.json',
           'docs/USN_SENSITIVITY_PLAN_20261124.md','scripts/usn_sensitivity_20261124.py','tests/test_usn_sensitivity.py']
    with (ROOT/paths[0]).open(encoding='utf-8',newline='') as s:rows=list(csv.DictReader(s))
    totals=Counter()
    with (ROOT/paths[1]).open(encoding='utf-8',newline='') as stream:
        for r in csv.DictReader(stream):
            accepted=r['accepted']=='True'
            if r['accepted'] not in ('True','False'):raise ValueError('Invalid decision')
            totals[(r['phrase'],r['target'],r['role'],'n')]+=1
            totals[(r['phrase'],r['target'],r['role'],'error')]+=int(accepted if r['role']=='attack' else not accepted)
    for r in rows:
        for role,num,den in [('attack','impostor_accepted','impostor_trials'),('genuine','genuine_rejected','genuine_trials')]:
            assert totals[(r['phrase'],r['participant_id'],role,'n')]==int(r[den])
            assert totals[(r['phrase'],r['participant_id'],role,'error')]==int(r[num])
    audit=json.loads((ROOT/paths[3]).read_text(encoding='utf-8'))
    excluded=sum(len(f['excluded']) for f in audit['files'] if f['unique_attack_ids'] is not None)
    result=analyze(rows,excluded)
    old=json.loads((ROOT/paths[2]).read_text(encoding='utf-8'))
    for key in ('impostor_accepted','impostor_trials','genuine_rejected','genuine_trials','macro_far','macro_frr'):
        assert abs(result['overall'][key]-old['overall'][key])<1e-12
    output={'completed_at_utc':datetime.now(timezone.utc).isoformat(),'scope':'Retrospective sensitivity; no fitting, threshold changes, independent-validation or causal claim',
            'plan_sha256':hashlib.sha256((ROOT/paths[4]).read_bytes()).hexdigest(),
            'source_sha256':{n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in paths},'results':result}
    with (ROOT/(P+'.json')).open('x',encoding='utf-8') as s:json.dump(output,s,indent=2);s.write('\n')
    table=[{'participant_id':p,**m} for p,m in result['by_person'].items()]
    with (ROOT/(P+'_people.csv')).open('x',encoding='utf-8',newline='') as s:
        w=csv.DictWriter(s,fieldnames=list(table[0]));w.writeheader();w.writerows(table)
    print(json.dumps(result))

if __name__=='__main__':main()
