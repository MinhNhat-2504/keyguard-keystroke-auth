"""Các chỉ số đánh giá xác thực.

- FAR (False Acceptance Rate): tỉ lệ mẫu kẻ gian bị chấp nhận nhầm. Đo bảo mật.
- FRR (False Rejection Rate): tỉ lệ mẫu chủ tài khoản bị từ chối nhầm. Đo tiện dụng.
- EER (Equal Error Rate): mức lỗi tại ngưỡng mà FAR = FRR. Càng thấp càng tốt.

Mọi hàm nhận điểm bất thường: chấp nhận khi điểm <= ngưỡng.
"""

from __future__ import annotations

import numpy as np
from sklearn.metrics import roc_auc_score, roc_curve

FAR_GRID = np.linspace(0.0, 1.0, 201)


def _roc(genuine_scores: np.ndarray, impostor_scores: np.ndarray):
    genuine_scores = _validated_scores(genuine_scores)
    impostor_scores = _validated_scores(impostor_scores)
    y = np.r_[np.ones(len(genuine_scores)), np.zeros(len(impostor_scores))]
    s = -np.r_[genuine_scores, impostor_scores]  # đổi dấu: điểm cao = giống chủ tài khoản
    far, tar, _ = roc_curve(y, s)
    return far, tar, y, s


def equal_error_rate(genuine_scores: np.ndarray, impostor_scores: np.ndarray) -> float:
    """EER nội suy tuyến tính giữa hai điểm ROC kẹp FAR = FRR.

    Đây là chỉ số tổng kết ROC, không phải ngưỡng triển khai được chọn trên test.
    """
    far, tar, _, _ = _roc(genuine_scores, impostor_scores)
    frr = 1.0 - tar
    delta = frr - far
    right = int(np.flatnonzero(delta <= 0)[0])
    if delta[right] == 0:
        return float(far[right])
    left = right - 1
    weight = delta[left] / (delta[left] - delta[right])
    return float(far[left] + weight * (far[right] - far[left]))


def _validated_scores(scores: np.ndarray) -> np.ndarray:
    scores = np.asarray(scores, dtype=float)
    if scores.ndim != 1 or not len(scores) or not np.isfinite(scores).all():
        raise ValueError("Điểm phải là mảng một chiều hữu hạn và không rỗng.")
    return scores


def threshold_at_far(impostor_scores: np.ndarray, target_far: float) -> float:
    """Ngưỡng cho accept <= tau, bảo đảm FAR thực nghiệm <= target_far.

    Không tách nhóm điểm bằng nhau: tau nằm ngay dưới điểm đầu tiên mà
    việc chấp nhận nó sẽ vượt ngân sách lỗi. Không bảo đảm FAR trên người mới.
    """
    scores = np.sort(_validated_scores(impostor_scores))
    if not np.isfinite(target_far) or not 0 <= target_far <= 1:
        raise ValueError("target_far phải nằm trong [0, 1].")
    allowed = int(np.floor(target_far * len(scores)))
    if allowed == len(scores):
        return float(scores[-1])
    return float(np.nextafter(scores[allowed], -np.inf))


def auc(genuine_scores: np.ndarray, impostor_scores: np.ndarray) -> float:
    _, _, y, s = _roc(genuine_scores, impostor_scores)
    return float(roc_auc_score(y, s))


def tar_on_grid(genuine_scores: np.ndarray, impostor_scores: np.ndarray) -> np.ndarray:
    """Tỉ lệ chấp nhận đúng (1 - FRR) tại các mức FAR trong FAR_GRID, để lấy trung bình ROC giữa người dùng."""
    far, tar, _, _ = _roc(genuine_scores, impostor_scores)
    return np.interp(FAR_GRID, far, tar)


def far_frr_at(genuine_scores: np.ndarray, impostor_scores: np.ndarray, threshold: float) -> tuple[float, float]:
    far = float(np.mean(np.asarray(impostor_scores) <= threshold))
    frr = float(np.mean(np.asarray(genuine_scores) > threshold))
    return far, frr
