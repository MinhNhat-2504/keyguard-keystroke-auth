from copy import deepcopy
import pytest
from keyguard.attack_exposure import summarize_exposure

def fixture():
    warnings={(p,t):t=='a' for p in ('x','y') for t in ('a','b')}
    rows=[dict(phrase=p,target=t,role='attack',source_line=str(i),attack_subject='s',z=str(z),accepted=str(z<=0))
          for p in ('x','y') for i,values in ((2,(-1,-1)),(3,(1,-1))) for t,z in zip(('a','b'),values)]
    return rows,warnings

def test_union_and_decision_denominators_differ():
    rows,w=fixture();r=summarize_exposure(rows,w,0)['overall']
    assert r['distinct_attack_samples']==4 and r['target_decisions']==8
    assert r['targets_passed_histogram_before']==[0,2,2]
    assert r['targets_passed_histogram_after']==[0,4,0]
    assert r['samples_any_target_before']==r['samples_any_target_after']==4
    assert r['accepted_target_decisions_before']==6 and r['accepted_target_decisions_after']==4

def test_all_warning_profiles_divert_without_claiming_otp_success():
    rows,w=fixture();r=summarize_exposure(rows,{k:True for k in w},0)['overall']
    assert r['samples_any_target_after']==0 and r['targets_passed_histogram_after']==[4,0,0]

def test_same_line_numbers_in_different_phrases_remain_distinct():
    rows,w=fixture();r=summarize_exposure(rows,w,0)
    assert len(r['by_phrase'])==2 and all(x['distinct_attack_samples']==2 for x in r['by_phrase'])

def test_order_independent_and_inputs_unchanged():
    rows,w=fixture();old=deepcopy(rows)
    assert summarize_exposure(rows,w,0)==summarize_exposure(reversed(rows),w,0) and rows==old

@pytest.mark.parametrize('kind',['missing','duplicate','subject','flag','nan','unknown','no_attacks'])
def test_invalid_attack_matrix_rejected(kind):
    rows,w=fixture()
    if kind=='missing':rows.pop()
    if kind=='duplicate':rows.append(dict(rows[0]))
    if kind=='subject':rows[0]['attack_subject']='other'
    if kind=='flag':rows[0]['accepted']='False'
    if kind=='nan':rows[0]['z']='nan'
    if kind=='unknown':rows[0]['target']='z'
    if kind=='no_attacks':rows=[]
    with pytest.raises(ValueError):summarize_exposure(rows,w,0)
