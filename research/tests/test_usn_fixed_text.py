import csv
import numpy as np
import pytest
from scripts.usn_fixed_text_adapter import read_file

HEADER=["hold time 'A'","down to down 'A' => '#ENTER#'","up to down 'A' => '#ENTER#'","hold time '#ENTER#'"]
def file(tmp_path,rows,attack=True,header=None):
    path=tmp_path/'source.csv'
    with path.open('w',newline='',encoding='utf-8') as out:
        w=csv.writer(out);w.writerow(header or ((['subject','rep'] if attack else [])+HEADER));w.writerows(rows)
    return path

def test_metadata_removed_and_negative_ud_retained(tmp_path):
    h,rows,a=read_file(file(tmp_path,[[77,1,.2,.1,-.1,.15]]),True)
    assert len(rows[0]['x'])==4 and rows[0]['subject']==77 and rows[0]['x'][2]==-.1
    assert a['max_dd_minus_h_ud_abs']<1e-12

def test_missing_and_nonfinite_not_imputed(tmp_path):
    _,rows,a=read_file(file(tmp_path,[[1,1,'',.2,.1,.1],[1,2,'nan',.2,.1,.1],[1,3,.1,.2,.1,.1]]),True)
    assert len(rows)==1 and len(a['excluded'])==2 and a['raw_rows']==3

def test_ambiguous_duplicate_key_excludes_all(tmp_path):
    _,rows,a=read_file(file(tmp_path,[[1,1,.1,.2,.1,.1],[1,1,.2,.3,.1,.1],[1,2,.1,.2,.1,.1]]),True)
    assert [r['rep'] for r in rows]==[2] and len(a['excluded'])==2

def test_genuine_order_retained_without_timestamp_claim(tmp_path):
    _,rows,a=read_file(file(tmp_path,[[.2,.3,.1,.1],[.1,.2,.1,.1]],attack=False),False)
    assert [r['rep'] for r in rows]==[1,2] and rows[0]['x'][0]==.2
    assert not a['has_session_or_timestamp']

def test_reject_metadata_as_predictor_schema(tmp_path):
    with pytest.raises(ValueError):read_file(file(tmp_path,[],header=['participant','rep']+HEADER),True)

def test_no_test_fit_or_mutation():
    from scripts.usn_transfer_core import evaluate_account
    rng=np.random.default_rng(123)
    enrollment=rng.normal(2,.2,(20,4));future=rng.normal(2,.4,(180,4));attack=rng.normal(3,.4,(30,4))
    before=enrollment.copy()
    a=evaluate_account(enrollment,future,attack,.2720094565367825)
    b=evaluate_account(enrollment,future+100,attack,.2720094565367825)
    assert np.array_equal(before,enrollment) and a['profile_sha256']==b['profile_sha256']
    assert a['impostor_accepted']==b['impostor_accepted'] and a['genuine_trials']==180

def test_saved_decisions_match_counts_and_threshold_ties():
    from scripts.usn_transfer_core import evaluate_account
    x=np.ones((20,4));a=evaluate_account(x,np.ones((10,4)),np.ones((9,4)),0)
    assert a['genuine_rejected']==0 and a['impostor_accepted']==9
    assert sum(not r['accepted'] for r in a['genuine_decisions'])==a['genuine_rejected']

@pytest.mark.parametrize('shape',[(19,4),(21,4),(20,0)])
def test_exact_enrollment_budget(shape):
    from scripts.usn_transfer_core import evaluate_account
    with pytest.raises(ValueError):evaluate_account(np.ones(shape),np.ones((2,4)),np.ones((2,4)),.2)
