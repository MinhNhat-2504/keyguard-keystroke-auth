"""Reconcile all orderings; optionally recompute CV using Python statistics.

Raw mode shares the previously validated enrollment reader, not the CV math.
"""
import argparse,hashlib,json,math,statistics,sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1];P='results/calibration_order_20261124_'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
close=lambda a,b:math.isclose(a,b,rel_tol=1e-9,abs_tol=1e-8)
def main(raw):
    result=json.loads((ROOT/(P+'results.json')).read_text(encoding='utf-8'))
    lock=json.loads((ROOT/(P+'freeze.json')).read_text(encoding='utf-8'))
    assert sha(ROOT/(P+'freeze.json'))==result['freeze_sha256']
    for name,h in lock['source_sha256'].items():assert sha(ROOT/name)==h,name
    assert sha(ROOT/(P+'synthetic_tests.json'))==lock['tests_sha256']
    pools={}
    if raw:
        for name,h in lock['raw_sha256'].items():assert sha(ROOT/name)==h,name
        sys.path.insert(0,str(ROOT))
        from scripts.run_calibration_order_20261124 import load_enrollment
        pools={(d,p,pid):x.tolist() for d,p,pid,x,_ in load_enrollment()}
    assert len(result['profiles'])==result['profile_count']==132
    identities=set();cases_checked=recomputed=0
    for profile in result['profiles']:
        identity=(profile['dataset'],profile['phrase'],profile['participant_id'])
        assert identity not in identities;identities.add(identity)
        cases=profile['cases'];assert [c['ordering'] for c in cases]==['original','reverse_control','rotate1','rotate2','rotate3']
        expected_orders=[list(range(20)),list(reversed(range(20)))]+[list(range(k,20))+list(range(k)) for k in (1,2,3)]
        for case,expected in zip(cases,expected_orders):
            assert case['indices_0based']==expected
            scores=case['oof_scores_original_order'];assert len(scores)==20
            mu=statistics.mean(scores);scale=max(statistics.pstdev(scores),1e-6)
            assert close(mu,case['cv_center']) and close(scale,case['cv_scale'])
            assert close(mu+result['threshold']*scale,case['raw_acceptance_limit'])
            assert case['review_required']==(bool(case['floor_events']) or case['cv_std_at_floor'])
            if raw:
                original=pools[identity];x=[original[i] for i in expected]
                rebuilt=[0.]*20;events=[]
                for fold in range(5):
                    held=list(range(4*fold,4*fold+4));train=[row for i,row in enumerate(x) if i not in held]
                    center=[statistics.mean(col) for col in zip(*train)]
                    mad=[statistics.mean(abs(row[j]-center[j]) for row in train) for j in range(len(center))]
                    for i in held:rebuilt[expected[i]]=sum(abs(x[i][j]-center[j])/max(mad[j],1e-9) for j in range(len(center)))
                    for j,v in enumerate(mad):
                        if v<=1e-9 and max(abs(x[i][j]-center[j]) for i in held)>1e-9:
                            events.append({'fold':fold+1,'feature_index':j,'held_original_rows_1based':[expected[i]+1 for i in held]})
                assert all(close(a,b) for a,b in zip(rebuilt,scores)),(identity,case['ordering'])
                assert events==case['floor_events'],(identity,case['ordering'])
                recomputed+=1
            cases_checked+=1
        limits=[c['raw_acceptance_limit'] for c in cases]
        assert profile['raw_limit_min']==min(limits) and profile['raw_limit_max']==max(limits)
        assert close(profile['raw_limit_max_min_ratio'],max(limits)/min(limits))
        assert profile['warning_changes_across_orderings']==any(c['review_required']!=cases[0]['review_required'] for c in cases)
        control=all(math.isclose(a,b,rel_tol=1e-10,abs_tol=1e-9) for a,b in zip(cases[0]['oof_scores_original_order'],cases[1]['oof_scores_original_order'])) and cases[0]['review_required']==cases[1]['review_required']
        assert profile['reverse_control_close']==control
    for summary in result['summaries']:
        rows=[p for p in result['profiles'] if p['dataset']==summary['dataset']]
        assert len(rows)==summary['profiles']
        for i,name in enumerate(['original','reverse_control','rotate1','rotate2','rotate3']):
            assert summary['warning_counts_by_ordering'][name]==sum(p['cases'][i]['review_required'] for p in rows)
        assert summary['warning_changed_profiles']==sum(p['warning_changes_across_orderings'] for p in rows)
        ratios=[p['raw_limit_max_min_ratio'] for p in rows]
        assert summary['raw_limit_ratio_median']==statistics.median(ratios)
        assert summary['raw_limit_ratio_max']==max(ratios)
    assert cases_checked==result['ordering_case_count']==660 and result['enrollment_samples']==2640
    assert result['test_decisions_scored']==0 and not result['threshold_or_policy_changed']
    record={'status':'passed','profiles_reconciled':132,'ordering_cases_reconciled':cases_checked,
            'raw_cv_cases_recomputed':recomputed,'raw_hashes_checked':raw,
            'shared_previously_validated_enrollment_reader':raw,'test_decisions_scored':0,
            'scope':'Enrollment sensitivity consistency; not independent validation of authentication efficacy'}
    suffix='raw_audit.json' if raw else 'saved_audit.json'
    (ROOT/(P+suffix)).write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8');print(json.dumps(record))
if __name__=='__main__':
    parser=argparse.ArgumentParser();group=parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--check-raw',action='store_true');group.add_argument('--saved-only',action='store_true')
    args=parser.parse_args();main(args.check_raw)
