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
    y = np.r_[np.ones(len(genuine_scores)), np.zeros(len(impostor_scores))]
    s = -np.r_[genuine_scores, impostor_scores]  # đổi dấu: điểm cao = giống chủ tài khoản
    far, tar, _ = roc_curve(y, s)
    return far, tar, y, s


def equal_error_rate(genuine_scores: np.ndarray, impostor_scores: np.ndarray) -> float:
    far, tar, _, _ = _roc(genuine_scores, impostor_scores)
    frr = 1.0 - tar
    i = int(np.nanargmin(np.abs(frr - far)))
    return float((far[i] + frr[i]) / 2.0)


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
