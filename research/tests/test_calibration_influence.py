import math
import statistics
import pytest
from keyguard.calibration_influence import single_outlier_example,standardize_example

@pytest.mark.parametrize('n',[2,5,20,50])
@pytest.mark.parametrize('outlier',[.001,1000000.])
def test_closed_form_matches_population_statistics(n,outlier):
    example=single_outlier_example(n,outlier,.272)
    values=[0.]*(n-1)+[outlier]
    assert math.isclose(example['center'],statistics.mean(values),rel_tol=1e-14)
    assert math.isclose(example['population_sd'],statistics.pstdev(values),rel_tol=1e-14)
    assert math.isclose(example['raw_acceptance_limit'],statistics.mean(values)+.272*statistics.pstdev(values),rel_tol=1e-14)

def test_std_floor_is_not_ignored_for_tiny_outlier():
    example=single_outlier_example(20,1e-9,.272)
    assert example['scale_floor_active'] and example['used_scale']==1e-6
    assert example['raw_acceptance_limit']==example['center']+.272e-6

@pytest.mark.parametrize('n,raw_score',[(2,0.),(2,50.),(20,0.),(20,50.)])
def test_fixed_raw_score_converges_to_negative_limit(n,raw_score):
    early=single_outlier_example(n,1e9,.272)
    late=single_outlier_example(n,1e15,.272)
    target=-1/math.sqrt(n-1)
    if raw_score:
        assert abs(standardize_example(raw_score,late)-target)<abs(standardize_example(raw_score,early)-target)
    assert math.isclose(standardize_example(raw_score,late),target,abs_tol=1e-11)

@pytest.mark.parametrize('n,outlier,threshold',[(1,1.,0.),(True,1.,0.),(20,0.,0.),(20,-1.,0.),(20,float('inf'),0.),(20,1.,float('nan'))])
def test_invalid_examples_fail(n,outlier,threshold):
    with pytest.raises(ValueError):single_outlier_example(n,outlier,threshold)
