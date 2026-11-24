import numpy as np
import pytest
from scripts.usn_oof_diagnostic_20261124 import diagnose

def test_constant_train_dimension_can_amplify_one_held_sample():
    x=np.ones((20,2));x[0,0]+=.001
    d=diagnose(x)
    assert d['largest_oof']['held_row_1based']==1
    assert d['largest_oof']['largest_contribution']==pytest.approx(1e6)
    assert d['cv_center']==pytest.approx(np.mean(d['oof_scores']))
    assert any(f['feature_index']==0 and f['max_held_absolute_deviation']>0 for f in d['floored_training_features'])
    assert 0 not in d['full_enrollment_floored_feature_indices']

def test_identical_samples_do_not_create_outlier():
    d=diagnose(np.ones((20,3)))
    assert d['cv_center']==0 and d['cv_scale']==1e-6 and max(d['oof_scores'])==0

def test_no_input_mutation_and_reproducibility():
    x=np.random.default_rng(4).normal(size=(20,4));copy=x.copy()
    assert diagnose(x)==diagnose(x) and np.array_equal(x,copy)

def test_invalid_input_rejected():
    with pytest.raises(ValueError):diagnose(np.ones((19,3)))
