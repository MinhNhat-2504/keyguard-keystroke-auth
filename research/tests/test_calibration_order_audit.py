import numpy as np
import pytest
from keyguard.calibration_order_audit import fixed_orders,audit_orderings
from keyguard.calibration_preflight import audit_calibration

def varying():return np.column_stack([np.arange(20)/100,np.sin(np.arange(20))])

def test_orders_are_fixed_complete_permutations():
    orders=fixed_orders()
    assert list(orders)==['original','reverse_control','rotate1','rotate2','rotate3']
    assert all(sorted(v.tolist())==list(range(20)) for v in orders.values())
    assert orders['rotate1'].tolist()==list(range(1,20))+[0]

def test_reverse_control_and_original_rows_are_preserved():
    x=varying();copy=x.copy();result=audit_orderings(x,.272)
    assert np.array_equal(x,copy) and result['reverse_control_close']
    assert all(c['full_pool_parameters_close'] for c in result['cases'])
    assert result['cases'][0]['cv_center']==audit_calibration(x).cv_center
    assert np.allclose(result['cases'][0]['oof_scores_original_order'],result['cases'][1]['oof_scores_original_order'])

def test_two_rare_values_can_change_warning_when_fold_boundary_moves():
    rare=np.zeros(20);rare[[0,3]]=.001
    result=audit_orderings(np.column_stack([varying(),rare]),.272)
    flags={c['ordering']:c['review_required'] for c in result['cases']}
    assert flags['original'] and flags['reverse_control'] and not flags['rotate1']
    assert result['warning_changes_across_orderings']

def test_one_unique_value_warns_under_every_order():
    rare=np.zeros(20);rare[0]=.001
    result=audit_orderings(np.column_stack([varying(),rare]),.272)
    assert all(c['review_required'] for c in result['cases'])
    assert not result['warning_changes_across_orderings']

@pytest.mark.parametrize('x',[np.zeros((19,2)),np.full((20,2),float('nan'))])
def test_invalid_enrollment_fails(x):
    with pytest.raises(ValueError):audit_orderings(x,.272)

def test_nonfinite_threshold_fails():
    with pytest.raises(ValueError):audit_orderings(varying(),float('nan'))
