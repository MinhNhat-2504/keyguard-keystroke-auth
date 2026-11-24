import copy
import pytest

from keyguard.calibration_preflight import CalibrationAudit
from keyguard.calibration_routing import summarize_routes

def audit(warning):
    return CalibrationAudit(1,0.,1.,1.,tuple([1.]*20),(),warning)
def rows():
    return [{'phrase':'p','target':'a','role':role,'source_line':str(i+2),'z':str(z),'accepted':str(z<=.25)}
            for i,(role,z) in enumerate([('genuine',.25),('genuine',.3),('attack',-2),('attack',2)])]

def test_warned_profile_changes_only_existing_behavioral_passes():
    result=summarize_routes(rows(),{('p','a'):audit(True)},.25)['overall']
    assert result['genuine_trials']==result['attack_trials']==2
    assert result['genuine_behavioral_before']==result['attack_behavioral_before']==1
    assert result['genuine_behavioral_after']==result['attack_behavioral_after']==0
    assert result['genuine_moved_to_verification']==result['attack_moved_to_verification']==1
    assert result['final_attack_acceptance_count_bounds_after']==[0,2]
    assert result['final_genuine_rejection_count_bounds_after']==[0,2]

def test_no_warning_preserves_boundary_and_all_routes_without_mutating_input():
    data=rows();old=copy.deepcopy(data)
    result=summarize_routes(data,{('p','a'):audit(False)},.25)['overall']
    assert result['genuine_behavioral_after']==result['attack_behavioral_after']==1
    assert result['genuine_moved_to_verification']==result['attack_moved_to_verification']==0
    assert data==old

@pytest.mark.parametrize('change',[
    {'role':'other'},{'target':'missing'},{'z':'nan'},{'z':'inf'},
    {'accepted':'true'},{'accepted':'False'},
])
def test_invalid_saved_decision_is_not_silently_ignored(change):
    data=rows();data[0].update(change)
    with pytest.raises(ValueError):summarize_routes(data,{('p','a'):audit(False)},.25)

def test_duplicate_decision_fails_instead_of_inflating_denominator():
    data=rows();data.append(dict(data[0]))
    with pytest.raises(ValueError):summarize_routes(data,{('p','a'):audit(False)},.25)

def test_unused_profile_or_missing_role_fails():
    with pytest.raises(ValueError):summarize_routes(rows(),{('p','a'):audit(False),('p','b'):audit(True)},.25)
    with pytest.raises(ValueError):summarize_routes(rows()[:2],{('p','a'):audit(False)},.25)

def test_two_profiles_keep_paired_denominators():
    data=rows()+[{**r,'target':'b'} for r in rows()]
    result=summarize_routes(data,{('p','a'):audit(False),('p','b'):audit(True)},.25)
    assert result['profile_count']==2
    total=result['overall']
    assert total['genuine_trials']==total['attack_trials']==4
    assert total['genuine_behavioral_before']==total['attack_behavioral_before']==2
    assert total['genuine_behavioral_after']==total['attack_behavioral_after']==1
