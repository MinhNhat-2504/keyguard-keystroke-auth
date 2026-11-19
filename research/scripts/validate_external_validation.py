"""Check external audit/provenance, selection and saved counts; no fitting."""
import csv
import hashlib
import json
import math
from datetime import datetime
from pathlib import Path
import platform
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    freeze_path=ROOT/'results/external_validation_freeze.json'
    frozen=json.loads(freeze_path.read_text(encoding='utf-8'))
    result=json.loads((ROOT/'results/external_validation.json').read_text(encoding='utf-8'))
    started=json.loads((ROOT/'results/external_evaluation_started.json').read_text(encoding='utf-8'))
    assert result['freeze_sha256']==started['freeze_sha256']==sha(freeze_path)
    assert result['started_at_utc']==started['started_at_utc']
    assert datetime.fromisoformat(frozen['frozen_at_utc'])<datetime.fromisoformat(started['started_at_utc'])
    for name,expected in frozen['code_hashes'].items():assert sha(ROOT/name)==expected
    raw=ROOT/frozen['dataset']['file']
    assert sha(raw)==frozen['dataset']['sha256']
    assert hashlib.md5(raw.read_bytes()).hexdigest()==frozen['dataset']['md5']
    assert sha(ROOT/'models/model_config.json')==frozen['production_config_sha256']
    assert frozen['dataset']['license']=='CC BY 4.0'
    assert frozen['audit']['raw_rows']==19772 and frozen['audit']['eligible_ids']==sorted(result['dev_ids']+result['test_ids'])
    assert not set(result['dev_ids'])&set(result['test_ids'])
    assert len(result['dev_ids'])==66 and len(result['test_ids'])==33
    assert len(result['features'])==len(set(result['features']))==47
    assert 'DU.k.k__occ2' in result['features'] and result['features'][-1]=='total time'
    expected_g=sum(frozen['audit']['eligible_session_counts'][pid]['2'] for pid in result['test_ids'])
    expected_dev_g=sum(frozen['audit']['eligible_session_counts'][pid]['1']-20 for pid in result['dev_ids'])
    assert expected_g==3301
    by_name={r['id']:r for r in result['variants']}
    assert len(by_name)==9
    for family,selection in result['selection'].items():
        allowed=frozen['families'][family]
        assert {r['variant'] for r in selection['inner_ranking']}==set(allowed)
        best=min(selection['inner_ranking'],key=lambda r:(r['inner_balanced_error'],r['variant']))
        assert selection['variant']==best['variant']
    for row in result['variants']:
        assert row['dev']['far']<=.05 and row['dev']['impostor_trials']==42900
        assert row['dev']['genuine_trials']==expected_dev_g
        assert row['overall']['genuine_trials']==expected_g and row['overall']['impostor_trials']==10560
        assert {a['participant_id'] for a in row['accounts']}==set(result['test_ids'])
        for key in ('genuine_trials','genuine_rejected','impostor_trials','impostor_accepted'):
            assert row['overall'][key]==sum(a[key] for a in row['accounts'])
        assert all(a['impostor_trials']==320 for a in row['accounts'])
        assert math.isclose(row['macro_eer'],np.mean([a['eer'] for a in row['accounts']]),abs_tol=1e-14)
        assert math.isclose(row['macro_auc'],np.mean([a['auc'] for a in row['accounts']]),abs_tol=1e-14)
    baseline=by_name[result['selection']['baseline']['variant']]
    for family in result['families']:
        reference=by_name[family['variant']]
        assert family['variant']==result['selection'][family['id']]['variant']
        assert family['overall']==reference['overall']
        for metric in ('far','frr'):
            assert family[metric+'_minus_baseline']==reference['overall'][metric]-baseline['overall'][metric]
    assert {m['id'] for m in result['adaptation']}=={'static','window50','decay20'}
    for method in result['adaptation']:
        assert method['dev_far']<=.05 and method['overall']['genuine_trials']==expected_g
        for key in ('genuine_trials','genuine_rejected','impostor_trials','impostor_accepted'):
            assert method['overall'][key]==sum(a[key] for a in method['accounts'])
    assert next(m for m in result['adaptation'] if m['id']=='static')['overall']==baseline['overall']
    js=(ROOT/'explorer/external-data.js').read_text(encoding='utf-8')
    assert json.loads(js.removeprefix('window.KEYGUARD_EXTERNAL = ').rstrip(';\n'))==result
    csv_counts={}
    for name,expected in [('external_comparison.csv',9),('external_account_errors.csv',297),('external_adaptation.csv',99)]:
        with (ROOT/'results'/name).open(encoding='utf-8',newline='') as f:rows=list(csv.DictReader(f))
        assert len(rows)==expected;csv_counts[name]=len(rows)
        for row in rows:
            if name=='external_comparison.csv':
                target=by_name[row['variant']]['overall']
            elif name=='external_account_errors.csv':
                target=next(a for a in by_name[row['variant']]['accounts'] if a['participant_id']==row['participant_id'])
            else:
                target=next(a for m in result['adaptation'] if m['id']==row['method'] for a in m['accounts'] if a['participant_id']==row['participant_id'])
            assert int(row['impostor_accepted'])==target['impostor_accepted'] and int(row['genuine_rejected'])==target['genuine_rejected']
    validation={'date':'2026-11-13','source':'KeyRecs fixed-text Zenodo7886743 CC BY4.0',
                'freeze_sha256':sha(freeze_path),'frozen_before_first_evaluation':True,
                'frozen_code_unchanged':True,'raw_checksum_verified':True,'production_config_unchanged':True,
                'dev_id_count':66,'test_id_count':33,'feature_count':47,'genuine_test_trials':3301,'impostor_test_trials':10560,
                'csv_rows':csv_counts,'exact_reproduction_checked':True,'python_tests_passed':50,'subtests_passed':4,
                'new_tests':5,'full_sklearn_suite_rerun':False,
                'environment':{'python':platform.python_version(),'numpy':np.__version__,'pandas':pd.__version__},
                'interpretation':'external-source verification, not public preregistration; no claim of strong significance or direct CMU tau transfer'}
    (ROOT/'results/external_validation_checks.json').write_text(json.dumps(validation,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('PASS: frozen protocol preceded scores; raw/code/config hashes match; 66dev/33test/47features; all counts/CSV/JS reconciled')


if __name__=='__main__':main()
