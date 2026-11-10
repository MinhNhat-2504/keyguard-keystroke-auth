import numpy as np
import pytest

from keyguard.evaluation import equal_error_rate, threshold_at_far


@pytest.mark.parametrize("genuine,impostor,expected", [
    ([0, 1], [2, 3], 0.0),
    ([2, 3], [0, 1], 1.0),
    ([1, 1], [1, 1, 1], 0.5),
    ([0, 2], [1, 3, 4], 1 / 3),
])
def test_eer_known_roc_crossings(genuine, impostor, expected):
    assert equal_error_rate(genuine, impostor) == pytest.approx(expected)


@pytest.mark.parametrize("scores,target,accepted", [
    ([1, 1, 1, 2], 0.5, 0),  # nhận nhóm 1 sẽ vượt 50%
    ([1, 2, 2, 3], 0.5, 1),
    ([1, 2, 3], 0.0, 0),
    ([1, 2, 3], 0.2, 0),  # số mẫu hữu hạn, ngân sách < 1
    ([1, 2, 3], 1.0, 3),
    ([1, 2, 3, 4], 0.5, 2),
])
def test_threshold_respects_budget_and_ties(scores, target, accepted):
    scores = np.asarray(scores)
    tau = threshold_at_far(scores, target)
    assert np.count_nonzero(scores <= tau) == accepted
    assert np.mean(scores <= tau) <= target


@pytest.mark.parametrize("scores,target", [([], 0.05), ([np.nan], 0.05),
                                                   ([1], -0.1), ([1], 1.1)])
def test_threshold_rejects_invalid_input(scores, target):
    with pytest.raises(ValueError):
        threshold_at_far(scores, target)
