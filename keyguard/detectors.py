"""Bốn bộ phát hiện dùng để so sánh.

Quy ước chung: score(X) trả về điểm bất thường, càng cao càng giống kẻ gian.

- Ba bộ một lớp (ScaledManhattan, OneClassSVM, IsolationForest) chỉ học từ mẫu của
  chính chủ, đúng với tình huống thật: lúc đăng ký hệ thống chỉ có mẫu của chủ tài khoản.
- RandomForest là bộ hai lớp: cần thêm mẫu của những người khác làm ví dụ "kẻ gian".
"""

from __future__ import annotations

import numpy as np
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import OneClassSVM


class ScaledManhattan:
    """Killourhy & Maxion (2009): tổng |x - trung bình| chia cho độ lệch tuyệt đối trung bình."""

    needs_impostors = False

    def fit(self, X: np.ndarray) -> "ScaledManhattan":
        self.mean_ = X.mean(axis=0)
        mad = np.abs(X - self.mean_).mean(axis=0)
        self.mad_ = np.where(mad > 1e-9, mad, 1e-9)
        return self

    def score(self, X: np.ndarray) -> np.ndarray:
        return (np.abs(np.atleast_2d(X) - self.mean_) / self.mad_).sum(axis=1)

    def to_dict(self) -> dict:
        return {"mean": self.mean_.tolist(), "mad": self.mad_.tolist()}

    @classmethod
    def from_dict(cls, d: dict) -> "ScaledManhattan":
        obj = cls()
        obj.mean_ = np.asarray(d["mean"], dtype=float)
        obj.mad_ = np.asarray(d["mad"], dtype=float)
        return obj


class OCSVM:
    """One-Class SVM nhân RBF trên đặc trưng đã chuẩn hóa. Siêu tham số giữ cố định."""

    needs_impostors = False

    def __init__(self, nu: float = 0.1, gamma: str | float = "scale"):
        self.nu = nu
        self.gamma = gamma

    def fit(self, X: np.ndarray) -> "OCSVM":
        self.model_ = make_pipeline(StandardScaler(), OneClassSVM(kernel="rbf", nu=self.nu, gamma=self.gamma))
        self.model_.fit(X)
        return self

    def score(self, X: np.ndarray) -> np.ndarray:
        return -self.model_.decision_function(np.atleast_2d(X))


class IForest:
    """Isolation Forest: mẫu càng dễ bị cô lập thì càng bất thường."""

    needs_impostors = False

    def __init__(self, n_estimators: int = 200, random_state: int = 42):
        self.n_estimators = n_estimators
        self.random_state = random_state

    def fit(self, X: np.ndarray) -> "IForest":
        self.model_ = IsolationForest(n_estimators=self.n_estimators, random_state=self.random_state)
        self.model_.fit(X)
        return self

    def score(self, X: np.ndarray) -> np.ndarray:
        return -self.model_.score_samples(np.atleast_2d(X))


class RForest:
    """Random Forest hai lớp: chủ tài khoản (1) và những người khác (0)."""

    needs_impostors = True

    def __init__(self, n_estimators: int = 200, random_state: int = 42):
        self.n_estimators = n_estimators
        self.random_state = random_state

    def fit(self, X_genuine: np.ndarray, X_impostor: np.ndarray) -> "RForest":
        X = np.vstack([X_genuine, X_impostor])
        y = np.r_[np.ones(len(X_genuine)), np.zeros(len(X_impostor))]
        self.model_ = RandomForestClassifier(
            n_estimators=self.n_estimators,
            class_weight="balanced",
            random_state=self.random_state,
            n_jobs=-1,
        )
        self.model_.fit(X, y)
        return self

    def score(self, X: np.ndarray) -> np.ndarray:
        return 1.0 - self.model_.predict_proba(np.atleast_2d(X))[:, 1]


DETECTORS = {
    "ScaledManhattan": ScaledManhattan,
    "OneClassSVM": OCSVM,
    "IsolationForest": IForest,
    "RandomForest": RForest,
}
