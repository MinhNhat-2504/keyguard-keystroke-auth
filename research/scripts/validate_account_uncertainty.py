"""Independently check saved account means and bootstrap bounds with SciPy."""
import csv
import hashlib
import json
from pathlib import Path
import sys
import numpy as np
from scipy.stats import bootstrap

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.account_uncertainty import inputs


def main():
    path=ROOT/'results/account_uncertainty_20261115.json'
    result=json.loads(path.read_text())
    assert result['replicates']==20000 and result['seed']==20261115
    for name,h in result['source_sha256'].items():
        assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==h,name
    flat=[]
    for saved,(name,control,candidate,rows,field) in zip(result['comparisons'],inputs()):
        a={r['participant_id']:r for r in rows if r[field]==control}
        b={r['participant_id']:r for r in rows if r[field]==candidate}
        assert set(a)==set(b) and len(a)==saved['accounts']
        columns=[]
        for group in (a,b):
            for num,den in [('impostor_accepted','impostor_trials'),('genuine_rejected','genuine_trials')]:
                columns.append(np.array([int(group[k][num])/int(group[k][den]) for k in sorted(group)]))
        def statistic(fa,fr,ca,cr,axis=-1):
            return np.array([fa.mean(axis),fr.mean(axis),ca.mean(axis),cr.mean(axis),
                             (ca-fa).mean(axis),(cr-fr).mean(axis)])*100
        ref=bootstrap(tuple(columns),statistic,vectorized=True,paired=True,method='percentile',
                      n_resamples=20000,rng=np.random.default_rng(20261115))
        points=statistic(*columns)
        for i,(metric,item) in enumerate(saved['metrics'].items()):
            np.testing.assert_allclose([item['estimate_pp'],item['lower_pp'],item['upper_pp']],
                [points[i],ref.confidence_interval.low[i],ref.confidence_interval.high[i]],atol=1e-10,rtol=0)
            flat.append(dict(comparison=name,accounts=len(a),metric=metric,**item))
    out=ROOT/'results/account_uncertainty_20261115.csv'
    with out.open('w',encoding='utf-8',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(flat[0]));writer.writeheader();writer.writerows(flat)
    checks={'status':'passed','comparisons':len(result['comparisons']),'metrics':len(flat),
            'independent_scipy_paired_bootstrap':True,'source_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
            'not_population_coverage_proof':True}
    (ROOT/'results/account_uncertainty_checks_20261115.json').write_text(json.dumps(checks,indent=2)+'\n')
    print(json.dumps(checks))


if __name__=='__main__':main()
