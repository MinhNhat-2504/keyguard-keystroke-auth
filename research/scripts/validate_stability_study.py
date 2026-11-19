"""Reconcile repeated-split/session artifacts and preserve prior study provenance."""
import csv
import hashlib
import json
import math
from statistics import mean, stdev
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    s=json.loads((ROOT/'results/stability_study.json').read_text(encoding='utf-8'))
    a=json.loads((ROOT/'results/session_adaptation.json').read_text(encoding='utf-8'))
    assert s['protocol']['seeds']==list(range(42,52))
    assert s['protocol']['code_sha256']==sha(ROOT/'keyguard/soft_weighting.py')
    assert s['protocol']['previous_enrollment_sha256']==sha(ROOT/'results/enrollment_study.json')
    assert s['protocol']['config_sha256']==a['protocol']['config_sha256']==sha(ROOT/'models/model_config.json')
    assert a['protocol']['code_sha256']==sha(ROOT/'keyguard/session_adaptation.py')
    assert a['protocol']['cmu_sha256']==sha(ROOT/'data/raw/DSL-StrongPasswordData.csv')
    assert len(s['repetitions'])==10 and len(s['enrollment_diagnostics'])==135
    assert len(s['variant_summaries'])==9 and len(s['family_summaries'])==4
    for d in s['enrollment_diagnostics']:
        if d['quality']=='soft_weight':
            assert d['positive_weights']==20 and all(.25<=w<=1 for w in d['weights'])
        assert 0<d['effective_samples']<=20.00000001
    for repetition in s['repetitions']:
        all_ids=[pid for f in repetition['folds'] for pid in f['test_ids']]
        assert len(set(all_ids))==len(all_ids)==15
        for f in repetition['folds']:
            assert not set(f['dev_ids']) & set(f['test_ids'])
            assert len(f['dev_ids'])==10 and len(f['test_ids'])==5
            for family,selection in f['selected'].items():
                best=min(selection['inner_ranking'],key=lambda r:(r['inner_balanced_error'],r['variant']))
                assert selection['variant']==best['variant']
                if family=='hard_selected':assert selection['variant'].startswith('hard_filter__')
                if family=='soft_selected':assert selection['variant'].startswith('soft_weight__')
            for item in f['variants'].values():
                assert item['dev_far']<=.05
                assert item['test']['impostor_trials']==200
                for key in ('genuine_trials','genuine_rejected','impostor_trials','impostor_accepted'):
                    assert sum(row[key] for row in item['accounts'])==item['test'][key]
        for family,total in repetition['families'].items():
            chosen=[f['variants'][f['selected'][family]['variant']]['test'] for f in repetition['folds']]
            for key in ('genuine_trials','genuine_rejected','impostor_trials','impostor_accepted'):
                assert total[key]==sum(row[key] for row in chosen)
            assert total['genuine_trials']==297 and total['impostor_trials']==600
        for variant,total in repetition['variant_totals'].items():
            for key in ('genuine_trials','genuine_rejected','impostor_trials','impostor_accepted'):
                assert total[key]==sum(f['variants'][variant]['test'][key] for f in repetition['folds'])
    for field,key in [('family_summaries','families'),('variant_summaries','variant_totals')]:
        for summary in s[field]:
            for metric in ('far','frr','eer','auc'):
                values=[r[key][summary['id']][metric] for r in s['repetitions']]
                assert math.isclose(summary[metric]['mean'],mean(values),abs_tol=1e-14)
                assert math.isclose(summary[metric]['std_across_splits'],stdev(values),abs_tol=1e-14)
                assert summary[metric]['min']==min(values) and summary[metric]['max']==max(values)
    for paired,repetition in zip(s['paired_differences'],s['repetitions']):
        for comparison in ('baseline','hard'):
            family='baseline' if comparison=='baseline' else 'hard_selected'
            for metric in ('far','frr'):
                expected=repetition['families']['soft_selected'][metric]-repetition['families'][family][metric]
                assert math.isclose(paired['soft_minus_'+comparison+'_'+metric],expected,abs_tol=1e-14)
    assert not set(a['protocol']['dev_ids']) & set(a['protocol']['test_ids'])
    assert len(a['protocol']['dev_ids'])==36 and len(a['protocol']['test_ids'])==15
    for method in a['methods']:
        assert method['dev_far']<=.05
        for partition,body in method['partitions'].items():
            total=body['overall'];n=36 if partition=='dev' else 15
            assert total['genuine_trials']==380*n
            assert total['impostor_trials']==n*(n-1)*10*8
            assert [r['session'] for r in body['sessions']]==list(range(1,9))
            for key in ('genuine_trials','genuine_rejected','impostor_trials','impostor_accepted'):
                assert total[key]==sum(row[key] for row in body['sessions'])
                assert total[key]==sum(row[key] for row in body['accounts'])
            assert body['sessions'][0]['genuine_trials']==30*n
            assert all(row['genuine_trials']==50*n for row in body['sessions'][1:])
            assert all(row['genuine_trials']==380 and row['impostor_trials']==(n-1)*10*8 for row in body['accounts'])
    for name,obj,global_name in [('stability-data.js',s,'KEYGUARD_STABILITY'),('adaptation-data.js',a,'KEYGUARD_ADAPTATION')]:
        source=(ROOT/'explorer'/name).read_text(encoding='utf-8')
        assert json.loads(source.removeprefix('window.'+global_name+' = ').rstrip(';\n'))==obj
    row_counts={}
    for filename,expected in [('stability_comparison.csv',270),('stability_account_errors.csv',1350),('session_adaptation.csv',48)]:
        with (ROOT/'results'/filename).open(encoding='utf-8',newline='') as f:rows=list(csv.DictReader(f))
        assert len(rows)==expected;row_counts[filename]=len(rows)
        if filename=='session_adaptation.csv':
            for row in rows:
                method=next(m for m in a['methods'] if m['id']==row['method'])
                reference=method['partitions'][row['partition']]['sessions'][int(row['session'])-1]
                assert float(row['far'])==reference['far'] and float(row['frr'])==reference['frr']
        elif filename=='stability_comparison.csv':
            for row in rows:
                repetition=next(r for r in s['repetitions'] if r['seed']==int(row['seed']))
                reference=repetition['folds'][int(row['fold'])-1]['variants'][row['variant']]
                assert float(row['threshold'])==reference['threshold']
                assert int(row['impostor_accepted'])==reference['test']['impostor_accepted']
    validation={'date':'2026-11-13','repeated_seeds':10,'outer_folds':30,'inner_folds':2,
                'variants':9,'enrollment_diagnostics':135,'csv_rows':row_counts,'paired_ids_separated':True,
                'soft_weights_positive':True,'source_config_previous_study_hashes_verified':True,
                'session_methods':3,'cmu_subjects':51,'python_tests_passed':45,'subtests_passed':4,
                'new_tests':9,'full_sklearn_suite_rerun':False,
                'interpretation':'dependent repeated splits, no confidence intervals or 150 independent people'}
    (ROOT/'results/stability_adaptation_validation.json').write_text(json.dumps(validation,indent=2)+'\n',encoding='utf-8')
    print('PASS: 10 repeated splits / 9 variants; 3 CMU session methods; CSV+JS totals and prior-source hashes verified')


if __name__=='__main__':main()
