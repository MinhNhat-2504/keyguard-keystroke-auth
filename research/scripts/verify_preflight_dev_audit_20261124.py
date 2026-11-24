"""Stdlib check of stored DEV statistics; optional independent raw CV calculation."""
import argparse,csv,hashlib,json,math,statistics
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1];P='results/preflight_dev_audit_20261124_'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
close=lambda a,b:math.isclose(a,b,rel_tol=1e-10,abs_tol=1e-9)
def main(raw):
    lock=json.loads((ROOT/(P+'freeze.json')).read_text(encoding='utf-8'))
    result=json.loads((ROOT/(P+'results.json')).read_text(encoding='utf-8'))
    assert sha(ROOT/(P+'freeze.json'))==result['freeze_sha256']
    for name,h in lock['source_sha256'].items():assert sha(ROOT/name)==h,name
    assert sha(ROOT/(P+'synthetic_tests.json'))==lock['tests_sha256']
    total=warnings=recomputed=0
    for source,dataset in zip(lock['datasets'],result['datasets']):
        assert dataset['name']==source['name']
        expected=set(source['dev_ids']);assert not expected&set(source['excluded_test_ids'])
        assert {p['participant_id'] for p in dataset['profiles']}==expected
        assert len(dataset['profiles'])==dataset['profile_count']==len(expected)
        names=dataset['source_audit']['feature_names']
        assert len(names)==(31 if source['name']=='CMU' else 47)
        enrollment={}
        if raw:
            assert sha(ROOT/source['raw_file'])==source['raw_sha256']
            records={pid:[] for pid in expected}
            with (ROOT/source['raw_file']).open(encoding='utf-8-sig',newline='') as stream:
                header=next(csv.reader(stream));assert header[3:]==names
                # Unique positional aliases keep repeated KeyRecs column names distinct.
                aliases=[f'column_{i}' for i in range(len(header))]
                reader=csv.DictReader(stream,fieldnames=aliases)
                pid_key,session_key,rep_key=aliases[:3]
                for row in reader:
                    if row[pid_key] in expected and row[session_key]=='1':records[row[pid_key]].append(row)
            for pid,rows in records.items():
                rows=sorted(rows,key=lambda r:int(r[rep_key]))[:20]
                assert len(rows)==20
                enrollment[pid]=[[float(row[f]) for f in aliases[3:]] for row in rows]
        local_warn=0
        for profile in dataset['profiles']:
            scores=profile['oof_scores'];assert len(scores)==20
            assert close(statistics.mean(scores),profile['cv_center'])
            assert close(statistics.pstdev(scores),profile['cv_std_unfloored'])
            assert close(max(statistics.pstdev(scores),1e-6),profile['cv_scale'])
            assert profile['review_required']==(bool(profile['floor_extrapolations']) or profile['cv_std_at_floor'])
            if raw:
                x=enrollment[profile['participant_id']];independent=[];events=[]
                for fold in range(5):
                    held=list(range(4*fold,4*fold+4));train=[r for i,r in enumerate(x) if i not in held]
                    centers=[statistics.mean(c) for c in zip(*train)]
                    mad=[statistics.mean(abs(r[j]-centers[j]) for r in train) for j in range(len(names))]
                    for i in held:independent.append(sum(abs(x[i][j]-centers[j])/max(mad[j],1e-9) for j in range(len(names))))
                    for j,v in enumerate(mad):
                        if v<=1e-9 and max(abs(x[i][j]-centers[j]) for i in held)>1e-9:events.append((fold+1,j))
                assert all(close(a,b) for a,b in zip(independent,scores)),profile['participant_id']
                assert events==[(e['fold'],e['feature_index']) for e in profile['floor_extrapolations']]
                recomputed+=1
            local_warn+=int(profile['review_required'])
        assert local_warn==dataset['review_required_count']
        assert dataset['source_audit']['enrollment_rows_parsed']==20*len(expected)
        total+=len(expected);warnings+=local_warn
    assert total==result['profile_count']==102 and warnings==result['review_required_count']==0
    assert result['enrollment_rows_parsed']==2040 and result['test_decisions_scored']==0
    record={'status':'passed','profiles_reconciled':total,'warnings':warnings,
            'raw_hashes_checked':raw,'profile_cv_recomputed_from_raw':recomputed,
            'test_decisions_scored':0,'scope':'Enrollment-only consistency and optional raw recomputation; not authentication accuracy'}
    suffix='raw_audit.json' if raw else 'saved_audit.json'
    (ROOT/(P+suffix)).write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(record))
if __name__=='__main__':
    parser=argparse.ArgumentParser();group=parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--check-raw',action='store_true');group.add_argument('--saved-only',action='store_true')
    args=parser.parse_args();main(args.check_raw)
