"""Independent source/count/pointer verification of the research decision synthesis."""
import csv
from fractions import Fraction as F
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def locate(value,pointer):
    for part in pointer.strip('/').split('/'):value=value[int(part)] if isinstance(value,list) else value[part]
    return value


def main():
    path=ROOT/'results/research_decision_20261115.json'
    decision=json.loads(path.read_text(encoding='utf-8'))
    for name,h in {**decision['source_sha256'],**decision['protected_sha256']}.items():assert sha(ROOT/name)==h,name
    with (ROOT/'results/research_decision_20261115.csv').open(encoding='utf-8',newline='') as stream:csvrows=list(csv.DictReader(stream))
    rows=decision['rows'];assert len(rows)==len(csvrows)==35 and len(decision['groups'])==11
    assert len({(r['group'],r['source'],r['variant']) for r in rows})==len(rows)
    for row,csvrow in zip(rows,csvrows):
        assert all(csvrow[k]==('' if v is None else str(v)) for k,v in row.items())
        source=json.loads((ROOT/row['artifact']).read_text(encoding='utf-8'));value=locate(source,row['pointer'])
        if row['metric_basis']=='mean_across_splits':
            assert row['far']==value['far']['mean'] and row['frr']==value['frr']['mean']
            assert row['sd_far']==value['far']['std_across_splits']
            assert row['sd_frr']==value['frr']['std_across_splits']
            continue
        if 'accounts' in value:
            accounts=value['accounts']
            for metric,n,den in [('far','impostor_accepted','impostor_trials'),('frr','genuine_rejected','genuine_trials')]:
                numerator=sum(a[n] for a in accounts);denominator=sum(a[den] for a in accounts)
                assert numerator==row[n] and denominator==row[den]
                assert abs(float(sum((F(a[n],a[den]) for a in accounts),F())/len(accounts))-row[metric])<1e-12
                assert abs(float(F(numerator,denominator))-row['pooled_'+metric])<1e-12
        else:
            for key in ('genuine_trials','genuine_rejected','impostor_trials','impostor_accepted'):assert row[key]==value[key]
            assert row['pooled_far']==value['impostor_accepted']/value['impostor_trials']
            assert row['pooled_frr']==value['genuine_rejected']/value['genuine_trials']
            if row['metric_basis']=='macro_accounts':
                arm=locate(source,row['pointer'].rsplit('/',1)[0])
                assert row['far']==arm['macro_far'] and row['frr']==arm['macro_frr']
            else:assert row['far']==row['pooled_far'] and row['frr']==row['pooled_frr']
    legacy=json.loads((ROOT/'results/research_synthesis_20261114.json').read_text(encoding='utf-8'))
    assert all(all(row[k]==original[k] for k in original) for row,original in zip(rows[:24],legacy['rows']))
    assert decision['groups']['cv']==legacy['groups']['cv'] and decision['groups']['matched']==legacy['groups']['matched']
    for group in ('percentile','covariance'):
        subset=[r for r in rows if r['group']==group]
        b=next(r for r in subset if r['role']=='control');c=next(r for r in subset if r['role']=='candidate')
        assert c['far']>b['far'] and c['frr']<b['frr']
    covariance=[r for r in rows if r['group']=='covariance'];assert covariance[-1]['role']=='descriptive_reference'
    assert decision['new_data_or_scoring'] is False
    checks={'status':'passed','groups':11,'rows':35,'legacy_rows_preserved':24,'new_rows_independently_recomputed':11,
            'source_files_checked':len(decision['source_sha256']),'protected_files_checked':len(decision['protected_sha256']),
            'no_meta_analysis_or_source_pooling':True,'no_scoring_or_new_data':True,
            'decision_json_sha256':sha(path),'decision_csv_sha256':sha(ROOT/'results/research_decision_20261115.csv')}
    (ROOT/'results/research_decision_checks_20261115.json').write_text(json.dumps(checks,indent=2)+'\n')
    print(json.dumps(checks))


if __name__=='__main__':main()
