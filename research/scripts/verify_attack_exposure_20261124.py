"""Independently recount the fixed five-target matrix with Boolean vectors."""
import csv,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
    source=ROOT/'results/attack_exposure_20261124_results.json'
    result=json.loads(source.read_text(encoding='utf-8'))
    preflight=json.loads((ROOT/'results/calibration_preflight_20261124_results.json').read_text(encoding='utf-8'))
    warnings={(r['phrase'],r['participant_id']):r['review_required'] for r in preflight['profiles']}
    targets=sorted({t for p,t in warnings});vectors={};subjects={};n=0
    with (ROOT/'results/usn_transfer_20261124_decisions.csv').open(encoding='utf-8',newline='') as f:
        for row in csv.DictReader(f):
            if row['role']!='attack':continue
            key=(row['phrase'],int(row['source_line']));position=targets.index(row['target'])
            if key not in vectors:
                vectors[key]=[[None]*len(targets),[None]*len(targets)];subjects[key]=row['attack_subject']
            assert subjects[key]==row['attack_subject'] and vectors[key][0][position] is None
            accepted=row['accepted']=='True'
            vectors[key][0][position]=accepted
            vectors[key][1][position]=accepted and not warnings[(key[0],row['target'])];n+=1
    for matrices in vectors.values():assert all(v is not None for vector in matrices for v in vector)
    assert len(vectors)==2042 and n==10210 and len(targets)==result['target_count_per_sample']==5
    for name,expected in [(None,result['overall'])]+[(r['phrase'],r) for r in result['by_phrase']]:
        rows=[v for k,v in vectors.items() if name is None or k[0]==name]
        assert expected['distinct_attack_samples']==len(rows) and expected['target_decisions']==len(rows)*5
        for arm,index in (('before',0),('after',1)):
            histogram=[sum(sum(v[index])==k for v in rows) for k in range(6)]
            assert histogram==expected['targets_passed_histogram_'+arm]
            assert sum(any(v[index]) for v in rows)==expected['samples_any_target_'+arm]
            assert sum(sum(v[index]) for v in rows)==expected['accepted_target_decisions_'+arm]
            assert sum(any(v[index]) for v in rows)/len(rows)==expected['samples_any_target_rate_'+arm]
    record=dict(status='passed',distinct_samples=len(vectors),attack_decisions=n,
                summaries_recounted=7,runner_module_imported=False,
                result_sha256=hashlib.sha256(source.read_bytes()).hexdigest())
    (ROOT/'results/attack_exposure_20261124_checks.json').write_bytes((json.dumps(record,indent=2)+'\n').encode('utf-8'))
    print(json.dumps(record))
if __name__=='__main__':main()
