"""Export reviewed synthesis and conditional intervals; no raw, fitting or cloud."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SYNTHESIS='results/research_decision_20261115.json'
UNCERTAINTY='results/account_uncertainty_20261115.json'


def main():
    synthesis=json.loads((ROOT/SYNTHESIS).read_text(encoding='utf-8'))
    uncertainty=json.loads((ROOT/UNCERTAINTY).read_text(encoding='utf-8'))
    assert len(synthesis['rows'])==35 and len(synthesis['groups'])==11
    assert len(uncertainty['comparisons'])==5
    sources={**synthesis['source_sha256'],**uncertainty['source_sha256']}
    for name,h in sources.items():
        assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==h,name
    sources.update({name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in (SYNTHESIS,UNCERTAINTY)})
    payload={'date':'2026-11-17','scope':'Read-only reviewed results; no ranking across protocols or new validation',
             'synthesis_artifact':SYNTHESIS,'uncertainty_artifact':UNCERTAINTY,
             'groups':synthesis['groups'],'rows':synthesis['rows'],
             'comparisons':uncertainty['comparisons'],'bootstrap':{k:uncertainty[k] for k in
             ('seed','replicates','nominal_percentile_interval','unit','cross_account_impostor_dependence_modelled')},
             'source_sha256':sources,'model_or_threshold_changes':False,'raw_or_cloud_access':False}
    output=ROOT/'explorer/evidence-data.js'
    output.write_text('window.KEYGUARD_EVIDENCE = '+json.dumps(payload,ensure_ascii=False,separators=(',',':'),allow_nan=False)+';\n',encoding='utf-8')
    (ROOT/'results/evidence_explorer_export_20261117.json').write_text(json.dumps({
        'status':'exported','rows':35,'groups':11,'comparisons':5,'data_sha256':hashlib.sha256(output.read_bytes()).hexdigest(),
        'source_sha256':sources,'raw_or_cloud_access':False,'model_scoring':False},indent=2)+'\n')
    print('EXPORTED 35 rows / 11 groups / 5 paired comparisons')


if __name__=='__main__':main()
