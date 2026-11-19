"""Check exported UI bytes against saved source objects, independently of builder."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def main():
    raw=(ROOT/'explorer/evidence-data.js').read_text(encoding='utf-8')
    prefix='window.KEYGUARD_EVIDENCE = '
    assert raw.startswith(prefix) and raw.endswith(';\n')
    data=json.loads(raw[len(prefix):-2])
    original=json.loads((ROOT/data['synthesis_artifact']).read_text(encoding='utf-8'))
    ci=json.loads((ROOT/data['uncertainty_artifact']).read_text(encoding='utf-8'))
    assert data['rows']==original['rows'] and data['groups']==original['groups']
    assert data['comparisons']==ci['comparisons']
    assert len({(r['group'],r['source'],r['variant']) for r in data['rows']})==35
    for k,v in data['bootstrap'].items():assert v==ci[k]
    for name,h in data['source_sha256'].items():
        assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==h,name
    for row in data['rows']:
        assert row['group'] in data['groups']
        assert row['metric_basis'] in {'macro_accounts','pooled','mean_across_splits'}
        assert row['artifact'] in data['source_sha256']
        assert 0<=row['far']<=1 and 0<=row['frr']<=1
    for c in data['comparisons']:
        assert len(c['metrics'])==6 and c['accounts']>=2
        for m in c['metrics'].values():assert -100<=m['lower_pp']<=m['upper_pp']<=100
    result={'status':'passed','source_rows_exact':35,'source_groups_exact':11,'conditional_interval_metrics_exact':30,
            'no_new_scoring':True,'new_validation_claim':False,
            'data_sha256':hashlib.sha256((ROOT/'explorer/evidence-data.js').read_bytes()).hexdigest()}
    (ROOT/'results/evidence_explorer_checks_20261117.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))


if __name__=='__main__':main()
