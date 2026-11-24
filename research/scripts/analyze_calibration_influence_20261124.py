"""Save a checked illustrative calculation; never fit or score a real profile."""
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import statistics
import subprocess
import sys

from keyguard.calibration_influence import single_outlier_example,standardize_example

ROOT=Path(__file__).resolve().parents[1]
OUTPUT=ROOT/'results/calibration_influence_20261124.json'
def main():
    assert not OUTPUT.exists(),'Preserve the existing illustrative calculation'
    tests=subprocess.run([sys.executable,'-m','pytest','tests/test_calibration_influence.py','-q'],cwd=ROOT,capture_output=True,text=True)
    if tests.returncode:raise RuntimeError(tests.stdout+'\n'+tests.stderr)
    assert '19 passed' in tests.stdout
    source=json.loads((ROOT/'results/usn_transfer_20261124_results.json').read_text(encoding='utf-8'))
    example=single_outlier_example(20,1000000.,source['threshold'])
    direct=[0.]*19+[1000000.]
    assert example['center']==statistics.mean(direct)
    assert abs(example['population_sd']-statistics.pstdev(direct))<1e-9
    old=json.loads((ROOT/'results/usn_oof_diagnostic_20261124.json').read_text(encoding='utf-8'))
    real=[{'participant_id':p['participant_id'],'raw_acceptance_limit':p['equivalent_raw_score_limit']}
          for p in old['profiles'] if p['phrase']=='Ob-dollar-erv3r' and p['participant_id'] in ('participant1','participant2','participant3')]
    files=['keyguard/calibration_influence.py','tests/test_calibration_influence.py',
           'scripts/analyze_calibration_influence_20261124.py','docs/CALIBRATION_INFLUENCE_NOTE_20261124.md',
           'results/usn_transfer_20261124_results.json','results/usn_oof_diagnostic_20261124.json']
    result={'completed_at_utc':datetime.now(timezone.utc).isoformat(),'example':example,
            'fixed_raw_score_example':50.,'standardized_example':standardize_example(50.,example),
            'real_profile_limits_already_saved':real,'comparison_is_illustrative_not_equivalence':True,
            'equation_text_nodes':[
                ['μ = ','M','n','; σ = ','M√(n−1)','n','; q = ','M(1+τ√(n−1))','n'],
                ['z(s) = ','s−μ','σ',' → ','−1','√(n−1)',' ≈ −0,2294']],
            'synthetic_test_cases_passed':19,'test_stdout':tests.stdout,'test_returncode':tests.returncode,
            'source_sha256':{name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in files},
            'model_or_test_decisions_changed':False,'production_changed':False,
            'scope':'Elementary mean/population-SD illustration with fixed bounded raw score; not an algorithm novelty or efficacy claim'}
    with OUTPUT.open('x',encoding='utf-8') as stream:json.dump(result,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('source_sha256','test_stdout','equation_text_nodes')}))
if __name__=='__main__':main()
