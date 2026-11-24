import numpy as np
import pytest

from keyguard.calibration_preflight import audit_calibration, behavioral_acceptance_allowed
from keyguard.detectors import ScaledManhattan

def varying():
    return np.column_stack([np.arange(20, dtype=float)/100, np.sin(np.arange(20))+.5])

def isolated_variation():
    x = varying()
    return np.column_stack([x, np.r_[.001, np.zeros(19)]])

def test_healthy_matches_original_cv_and_leaves_input_unchanged():
    x = varying(); original = x.copy()
    result = audit_calibration(x)
    scores=[]
    for held in np.array_split(np.arange(20),5):
        scores.extend(ScaledManhattan().fit(np.delete(x,held,axis=0)).score(x[held]))
    assert result.oof_scores == tuple(scores)
    assert result.cv_center == np.mean(scores)
    assert result.cv_scale == max(np.std(scores),1e-6)
    assert not result.review_required
    assert np.array_equal(x,original)

def test_floor_extrapolation_found_even_when_full_profile_is_not_at_floor():
    x=isolated_variation();result=audit_calibration(x)
    assert ScaledManhattan().fit(x).mad_[2] > 1e-9
    event=result.floor_extrapolations[0]
    assert (event.fold,event.feature_index,event.held_rows_1based)==(1,2,(1,2,3,4))
    assert event.maximum_held_deviation==.001
    assert event.maximum_contribution==1000000
    assert result.review_required

def test_permanently_constant_dimension_does_not_raise_floor_extrapolation():
    result=audit_calibration(np.column_stack([varying(),np.zeros(20)]))
    assert not result.floor_extrapolations
    assert not result.review_required

def test_all_constant_warns_about_degenerate_cv():
    result=audit_calibration(np.ones((20,2)))
    assert not result.floor_extrapolations
    assert result.cv_std_at_floor and result.review_required
    assert result.cv_std_unfloored==0 and result.cv_scale==1e-6

def test_guard_cannot_be_bypassed_with_a_very_low_score():
    audit=audit_calibration(isolated_variation())
    assert not behavioral_acceptance_allowed(audit,-1e20,.272)

def test_guard_keeps_healthy_score_boundary_and_requires_verification_above_it():
    audit=audit_calibration(varying())
    assert behavioral_acceptance_allowed(audit,.272,.272)
    assert not behavioral_acceptance_allowed(audit,.273,.272)

def test_deterministic_and_serializable():
    import json
    assert audit_calibration(isolated_variation())==audit_calibration(isolated_variation())
    result=json.loads(json.dumps(audit_calibration(isolated_variation()).to_dict(),allow_nan=False))
    assert result['review_required'] and result['floor_extrapolations'][0]['fold']==1

@pytest.mark.parametrize('x',[np.zeros((19,2)),np.zeros((21,2)),np.zeros((20,0)),np.zeros(20),[[1,2],[3]]])
def test_rejects_wrong_enrollment_shape(x):
    with pytest.raises(ValueError):audit_calibration(x)

@pytest.mark.parametrize('bad',[float('nan'),float('inf'),float('-inf')])
def test_rejects_nonfinite_enrollment(bad):
    x=varying();x[0,0]=bad
    with pytest.raises(ValueError):audit_calibration(x)

def test_rejects_overflow_instead_of_returning_a_pass():
    with pytest.raises(ValueError):audit_calibration(np.full((20,2),1e308))

@pytest.mark.parametrize('z,tau',[(float('nan'),.272),(0,float('inf'))])
def test_guard_rejects_nonfinite_decision_arguments(z,tau):
    with pytest.raises(ValueError):behavioral_acceptance_allowed(audit_calibration(varying()),z,tau)
