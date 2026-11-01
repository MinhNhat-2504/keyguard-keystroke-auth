"""Giao diện cho web demo: enroll(), verify(), update().

Ví dụ:

    from keyguard.model import enroll, verify, update, InvalidSampleError

    profile = enroll(list_of_samples)            # đăng ký: n lần gõ
    confidence, accepted = verify(profile, new_sample)
    if accepted:
        profile = update(profile, new_sample)     # cập nhật mẫu thích nghi, rồi lưu lại profile

Một "sample" là danh sách sự kiện của một lần gõ ".tie5Roanl" + Enter:
    [{"key": ".", "type": "down", "t": 0.0}, {"key": ".", "type": "up", "t": 92.4}, ...]
với t tính bằng mili-giây. Lần gõ sai câu sẽ ném InvalidSampleError.

Cách tính:
1. Hồ sơ người dùng giữ tối đa `window` lần gõ gần nhất của chủ tài khoản. Bộ phát hiện
   (Scaled Manhattan) học từ các lần gõ này. Điểm bất thường "bình thường" của chính chủ
   (trung bình mu, độ lệch chuẩn sigma) được ước lượng bằng kiểm định chéo k-fold.
2. Đăng nhập: z = (điểm - mu) / sigma. Chấp nhận khi z <= tau, với tau là ngưỡng chung
   chọn trong scripts/select_threshold.py và lưu ở models/model_config.json.
   Độ tin cậy hiển thị = 1 / (1 + exp(z - tau)), bằng 0.5 đúng tại ngưỡng.
3. Sau mỗi lần đăng nhập được chấp nhận, update() thêm lần gõ đó vào hồ sơ và bỏ lần gõ
   cũ nhất khi vượt quá `window`. Nhờ vậy hồ sơ theo kịp việc người dùng gõ ngày càng quen tay.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np

from keyguard.detectors import ScaledManhattan
from keyguard.features import InvalidSampleError, extract_features  # noqa: F401  (xuất lại cho web demo)

CONFIG_PATH = Path(__file__).resolve().parents[1] / "models" / "model_config.json"
PROFILE_VERSION = 2

# Các bộ phát hiện lưu được hồ sơ người dùng dưới dạng JSON.
SERIALIZABLE = {"ScaledManhattan": ScaledManhattan}


def load_config(path: str | Path | None = None) -> dict:
    with open(path or CONFIG_PATH, encoding="utf-8") as f:
        return json.load(f)


def genuine_score_stats(detector_cls, X: np.ndarray, k: int) -> tuple[float, float]:
    """Điểm bất thường của chính chủ trên dữ liệu chưa thấy, ước lượng bằng k-fold trên mẫu đăng ký."""
    n = len(X)
    k = max(2, min(k, n))
    folds = np.array_split(np.arange(n), k)
    scores = []
    for idx in folds:
        mask = np.ones(n, dtype=bool)
        mask[idx] = False
        scores.append(detector_cls().fit(X[mask]).score(X[idx]))
    scores = np.concatenate(scores)
    return float(scores.mean()), float(max(scores.std(), 1e-6))


def normalized_scores(detector, mu: float, sigma: float, X: np.ndarray) -> np.ndarray:
    return (detector.score(X) - mu) / sigma


def build_profile(X: np.ndarray, cfg: dict) -> dict:
    """Tạo hồ sơ từ ma trận đặc trưng (mỗi dòng một lần gõ, theo thứ tự thời gian)."""
    X = np.asarray(X, dtype=float)[-cfg["window"]:]
    detector_cls = SERIALIZABLE[cfg["detector"]]
    mu, sigma = genuine_score_stats(detector_cls, X, cfg["cv_folds"])
    return {
        "version": PROFILE_VERSION,
        "detector": cfg["detector"],
        "state": detector_cls().fit(X).to_dict(),
        "score_mean": mu,
        "score_std": sigma,
        "samples": X.tolist(),
    }


def profile_z(profile: dict, X: np.ndarray) -> np.ndarray:
    detector = SERIALIZABLE[profile["detector"]].from_dict(profile["state"])
    return normalized_scores(detector, profile["score_mean"], profile["score_std"], np.atleast_2d(X))


def enroll(samples: list[list[dict]], config: dict | None = None) -> dict:
    """Tạo hồ sơ người dùng từ n lần gõ. Hồ sơ là dict lưu được bằng JSON."""
    cfg = config or load_config()
    if len(samples) < cfg["min_enroll"]:
        raise ValueError(f"Cần ít nhất {cfg['min_enroll']} lần gõ hợp lệ để đăng ký, mới có {len(samples)}.")
    return build_profile(np.vstack([extract_features(s) for s in samples]), cfg)


def verify(profile: dict, events: list[dict], config: dict | None = None) -> tuple[float, bool]:
    """Trả về (độ tin cậy 0–1, chấp nhận hay không) cho một lần gõ mới."""
    cfg = config or load_config()
    z = float(profile_z(profile, extract_features(events))[0])
    tau = cfg["threshold"]
    confidence = 1.0 / (1.0 + math.exp(min(z - tau, 50.0)))
    return confidence, z <= tau


def update(profile: dict, events: list[dict], config: dict | None = None) -> dict:
    """Thêm một lần gõ ĐÃ ĐƯỢC CHẤP NHẬN vào hồ sơ, trả về hồ sơ mới. Không gọi khi bị từ chối."""
    cfg = config or load_config()
    X = np.vstack([np.asarray(profile["samples"]), extract_features(events)])
    return build_profile(X, cfg)
