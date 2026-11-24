import pytest
from scripts.usn_sensitivity_20261124 import aggregate,analyze,missing_bounds

def row(person,phrase,fa,ni,fr=1,ng=10):
    return {'participant_id':person,'phrase':phrase,'impostor_accepted':fa,'impostor_trials':ni,'genuine_rejected':fr,'genuine_trials':ng}

def test_pooled_and_macro_distinguished():
    r=aggregate([row('a','x',1,10),row('b','x',0,100)])
    assert r['macro_far']==.05 and r['pooled_far']==1/110

def test_each_person_and_phrase_removed_exactly_once():
    data=[row('a','x',9,10),row('a','y',1,10),row('b','x',0,10),row('b','y',0,10)]
    r=analyze(data,2)
    assert set(r['leave_one_person'])=={'a','b'} and set(r['leave_one_phrase'])=={'x','y'}
    assert r['leave_one_person']['a']['impostor_accepted']==0
    assert r['overall']['impostor_accepted']==10 and r['highest_fa_profile']['fraction_of_all_false_accepts']==.9
    assert r['excluded_attack_decision_bounds']['additional_unknown_decisions']==4

def test_bounds_are_not_imputation():
    r=missing_bounds(4,10,2)
    assert r['lower']==4/12 and r['upper']==6/12 and r['retained_accepted']==4

def test_zero_missing_has_equal_bounds():
    r=missing_bounds(4,10,0);assert r['lower']==r['upper']==.4

@pytest.mark.parametrize('counts',[(11,10,1),(0,0,1),(2,10,-1)])
def test_invalid_counts_rejected(counts):
    with pytest.raises(ValueError):missing_bounds(*counts)
