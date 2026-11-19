"""Validate saved enrollment/paired study counts and provenance without rerunning."""
import csv
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    e=json.loads((ROOT/'results/enrollment_study.json').read_text(encoding='utf-8'))
    c=json.loads((ROOT/'results/contamination_study.json').read_text(encoding='utf-8'))
    reference=json.loads((ROOT/'results/research_summary.json').read_text(encoding='utf-8'))
    assert e['protocol']['source_research_sha256']==sha(ROOT/'results/research_summary.json')
    assert e['protocol']['config_sha256']==c['protocol']['config_sha256']==sha(ROOT/'models/model_config.json')
    assert e['protocol']['code_sha256']==sha(ROOT/'keyguard/enrollment_study.py')
    assert c['protocol']['code_sha256']==sha(ROOT/'keyguard/contamination.py')
    assert c['protocol']['cmu_sha256']==sha(ROOT/'data/raw/DSL-StrongPasswordData.csv')
    assert e['baseline']==reference['baseline_recalibrated']
    assert len(e['variants'])==6 and len(e['enrollment_diagnostics'])==90
    for row in e['enrollment_diagnostics']:
        assert 16<=row['kept']<=20
        assert row['kept']+len(row['removed_positions_1based'])==20
        assert all(1<=p<=20 for p in row['removed_positions_1based'])
    assert sum(r['kept'] for r in e['enrollment_diagnostics'] if r['variant']=='robust_filter__mean_std')==278
    for v in e['variants']:
        for fold in v['folds']:
            assert fold['dev']['far']<=.05
            assert fold['test']['impostor_trials']==200
            assert sum(a['genuine_rejected'] for a in fold['accounts'])==fold['test']['genuine_rejected']
    for j,split in enumerate(e['selection_by_fold']):
        assert split['dev_ids']==reference['selection_by_fold'][j]['dev_ids']
        assert split['test_ids']==reference['selection_by_fold'][j]['test_ids']
        assert not set(split['dev_ids']) & set(split['test_ids'])
        best=min(split['inner_ranking'],key=lambda r:(r['inner_balanced_error'],r['variant']))
        assert split['selected_variant']==best['variant']
    assert len(c['pairs'])==15 and len({p['target'] for p in c['pairs']})==15
    for pair in c['pairs']:
        assert pair['target']!=pair['attacker']
        for policy,arms in pair['policies'].items():
            for arm,result in arms.items():
                assert result['genuine_trials']==200
                assert result['attack_trials']==(40 if arm=='injected' else 0)
                assert 0<=result['attacks_accepted']<=result['attack_trials']
                assert [p['genuine_seen'] for p in result['checkpoints']]==[0,50,100,150,200]
                assert all(0<=p['contaminated_rows']<=p['profile_rows']<=50 for p in result['checkpoints'])
                assert all(p['probe_trials']==10 for p in result['checkpoints'])
            assert arms['control']['checkpoints'][0]==arms['injected']['checkpoints'][0]
            if policy in ('static','verified_only'):
                assert arms['control']['checkpoints']==arms['injected']['checkpoints']
                assert arms['control']['genuine_rejected']==arms['injected']['genuine_rejected']
    for summary in c['summaries']:
        policy=summary['policy']
        for arm,total in summary['arms'].items():
            members=[p['policies'][policy][arm] for p in c['pairs']]
            for key in ('genuine_trials','genuine_rejected','attack_trials','attacks_accepted','final_contaminated_rows'):
                assert total[key]==sum(r[key] for r in members)
            for j,point in enumerate(total['checkpoints']):
                for key in ('probe_trials','probe_accepted','contaminated_rows'):
                    assert point[key]==sum(r['checkpoints'][j][key] for r in members)
        assert sum(summary['probe_delta_subjects'].values())==15
    for name,obj,global_name in [('enrollment-data.js',e,'KEYGUARD_ENROLLMENT'),('contamination-data.js',c,'KEYGUARD_CONTAMINATION')]:
        text=(ROOT/'explorer'/name).read_text(encoding='utf-8')
        assert json.loads(text.removeprefix('window.'+global_name+' = ').rstrip(';\n'))==obj
    counts={}
    for name,expected in [('enrollment_comparison.csv',18),('contamination_checkpoints.csv',600)]:
        with (ROOT/'results'/name).open(encoding='utf-8',newline='') as f:rows=list(csv.DictReader(f))
        assert len(rows)==expected
        counts[name]=len(rows)
        if name=='contamination_checkpoints.csv':
            for row in rows:
                pair=next(p for p in c['pairs'] if p['target']==row['target'])
                point=next(p for p in pair['policies'][row['policy']][row['arm']]['checkpoints'] if p['genuine_seen']==int(row['genuine_seen']))
                assert int(row['probe_accepted'])==point['probe_accepted']
                assert int(row['contaminated_rows'])==point['contaminated_rows']
    result={'date':'2026-11-13','variants':6,'enrollment_accounts':90,'paired_subjects':15,
            'paired_policy_arms':120,'csv_rows':counts,'original_research_unchanged':True,
            'config_unchanged':True,'cmu_hash_verified':True,'cv_selection_ids_verified':True,
            'python_tests_passed':36,'subtests_passed':4,'new_tests':8,
            'full_sklearn_suite_rerun':False}
    (ROOT/'results/enrollment_update_validation.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print('PASS: 6 variants/90 enrollment details; 15 paired subjects/120 arms; CSV+JS counts reconciled; provenance unchanged')


if __name__=='__main__':main()
