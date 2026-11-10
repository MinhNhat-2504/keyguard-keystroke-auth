import numpy as np

from keyguard.simulation import simulate_user


def test_impostor_checkpoints_count_logins_after_enrollment(monkeypatch):
    # Dùng đặc trưng làm chỉ số thời gian để phân biệt đếm từ enrollment
    # với lỗi đếm từ đầu toàn bộ chuỗi.
    def build(X, cfg):
        return {"samples": X, "last": X[-1, 0]}

    def score(profile, X):
        return np.full(len(np.atleast_2d(X)), profile["last"])

    monkeypatch.setattr("keyguard.simulation.build_profile", build)
    monkeypatch.setattr("keyguard.simulation.profile_z", score)
    zg, zi = simulate_user(np.arange(121).reshape(-1, 1), np.array([[999]]),
                           {"n_enroll": 20}, 0, "fallback", checkpoint_every=50)
    assert len(zg) == 101
    assert zi.tolist() == [19, 69, 119]
