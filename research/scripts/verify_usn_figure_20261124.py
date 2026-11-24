"""Check every plotted value against saved sources, without fitting a model."""
import hashlib
import json
import math
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def main():
    figure=json.loads((ROOT/'results/usn_normalization_figure_20261124.json').read_text(encoding='utf-8'))
    diagnostic=json.loads((ROOT/'results/usn_oof_diagnostic_20261124.json').read_text(encoding='utf-8'))
    for name,h in figure['source_sha256'].items():
        assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==h, name
    assert hashlib.sha256((ROOT/figure['figure']).read_bytes()).hexdigest()==figure['figure_sha256']
    profiles=[p for p in diagnostic['profiles'] if p['phrase']==figure['phrase']]
    assert len(profiles)==len(figure['plotted_points'])==5
    point_count=0
    for i,(source,plot) in enumerate(zip(profiles,figure['plotted_points']),1):
        assert source['participant_id']==f'participant{i}' and plot['profile']==f'P{i}'
        assert source['oof_scores']==plot['oof_scores'] and len(plot['oof_scores'])==20
        assert all(math.isfinite(x) and x>0 for x in plot['oof_scores'])
        expected=source['cv_center']+.2720094565367825*source['cv_scale']
        assert math.isclose(expected,plot['equivalent_raw_score_limit'],rel_tol=1e-12)
        assert plot['equivalent_raw_score_limit']==source['equivalent_raw_score_limit']
        point_count+=len(plot['oof_scores'])
    assert figure['logarithmic_y_axis'] and figure['threshold_unchanged']
    assert figure['font_size_pt_at_6_5_inch_width']==13
    record={'status':'passed','oof_points_reconciled':point_count,'equivalent_limits_reconciled':5,
            'figure_sha256':figure['figure_sha256'],
            'scope':'Saved-source visualization only; not independent model scoring or evidence of correction'}
    (ROOT/'results/usn_figure_validation_20261124.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(record))

if __name__=='__main__':main()
