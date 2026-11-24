"""Independent brute-force AUC/count check of all saved USN profiles."""
from collections import Counter
import csv,hashlib,json,math,statistics
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1];P='results/usn_residual_diagnostic_20261124_'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
    lock=json.loads((ROOT/(P+'freeze.json')).read_text(encoding='utf-8'))
    result=json.loads((ROOT/(P+'results.json')).read_text(encoding='utf-8'))
    assert sha(ROOT/(P+'freeze.json'))==result['freeze_sha256']
    for name,h in lock['source_sha256'].items():assert sha(ROOT/name)==h,name
    assert sha(ROOT/(P+'synthetic_tests.json'))==lock['tests_sha256']
    audit=json.loads((ROOT/'results/calibration_preflight_20261124_results.json').read_text(encoding='utf-8'))
    warnings={(p['phrase'],p['participant_id']):p['review_required'] for p in audit['profiles']}
    groups={key:{'genuine':[],'attack':[]} for key in warnings};pairs=Counter();seen=set()
    with (ROOT/'results/usn_transfer_20261124_decisions.csv').open(encoding='utf-8',newline='') as stream:
        for row in csv.DictReader(stream):
            key=(row['phrase'],row['target']);role=row['role'];z=float(row['z'])
            identity=(*key,role,int(row['source_line']));assert identity not in seen;seen.add(identity)
            assert row['accepted']==str(z<=result['threshold'])
            groups[key][role].append(z)
            if role=='attack' and not warnings[key] and row['accepted']=='True':pairs[(*key,row['attack_subject'])]+=1
    comparisons=0
    for account in result['accounts']:
        key=(account['phrase'],account['target']);g=groups[key]['genuine'];a=groups[key]['attack']
        wins=sum(x>y for x in a for y in g);ties=sum(x==y for x in a for y in g)
        comparisons+=len(g)*len(a)
        assert account['auc_twice_wins_plus_ties']==2*wins+ties
        assert account['auc_twice_pair_count']==2*len(g)*len(a)
        assert account['auc']==(2*wins+ties)/(2*len(g)*len(a))
        assert account['genuine_nonmatches_original']==sum(z>result['threshold'] for z in g)
        assert account['attack_behavioral_passes_original']==sum(z<=result['threshold'] for z in a)
        assert account['attack_behavioral_passes_after_guard']==(0 if warnings[key] else account['attack_behavioral_passes_original'])
        for role,values in [('genuine',g),('attack',a)]:
            assert account[role+'_z_min']==min(values) and account[role+'_z_max']==max(values)
            assert account[role+'_z_median']==statistics.median(values)
    assert len(result['accounts'])==len(groups)==30
    for phrase in result['phrases']:
        subset=[a for a in result['accounts'] if a['phrase']==phrase['phrase']]
        assert phrase['remaining_attack_behavioral_passes']==sum(a['attack_behavioral_passes_after_guard'] for a in subset)
        assert math.isclose(phrase['macro_auc'],sum(a['auc'] for a in subset)/len(subset),rel_tol=1e-12)
    expected={(p['phrase'],p['target'],p['attack_subject_code']):p['remaining_behavioral_passes'] for p in result['residual_pairs']}
    assert expected==dict(pairs) and sum(pairs.values())==result['remaining_attack_behavioral_passes']==374
    for suffix,key in [('accounts.csv','accounts'),('phrases.csv','phrases'),('pairs.csv','residual_pairs')]:
        with (ROOT/(P+suffix)).open(encoding='utf-8',newline='') as stream:rows=list(csv.DictReader(stream))
        assert len(rows)==len(result[key])
        for a,b in zip(rows,result[key]):assert all(a[k]==str(v) for k,v in b.items())
    assert len(seen)==result['decisions_count']==15610
    assert not result['new_threshold_chosen'] and not result['model_fit_performed']
    record={'status':'passed','profiles_reconciled':30,'saved_decisions_reconciled':len(seen),
            'brute_force_pairwise_comparisons':comparisons,'remaining_attack_behavioral_passes':374,
            'new_threshold_chosen':False,'model_rerun':False,
            'scope':'Independent descriptive AUC/count check, not independent efficacy validation'}
    (ROOT/(P+'saved_audit.json')).write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(record))
if __name__=='__main__':main()
