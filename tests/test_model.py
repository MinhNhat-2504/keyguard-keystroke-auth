import json

import numpy as np
import pytest

from keyguard.features import FEATURE_NAMES, InvalidSampleError, features_to_events
from keyguard.model import enroll, update, verify

CONFIG = {"detector": "ScaledManhattan", "n_enroll": 20, "min_enroll": 20, "cv_folds": 5, "threshold": 1.5, "window": 50}


def typist(rng, base_hold, base_dd, n, jitter=0.01):
    """Sinh n lần gõ hợp lệ quanh một nhịp gõ riêng (UD = DD - H)."""
    samples = []
    for _ in range(n):
        h = base_hold + rng.normal(0, jitter, 11)
        dd = base_dd + rng.normal(0, jitter, 10)
        x, hi, di = [], 0, 0
        for name in FEATURE_NAMES:
            if name.startswith("H."):
                x.append(h[hi])
                hi += 1
            elif name.startswith("DD."):
                x.append(dd[di])
            else:
                x.append(dd[di] - h[di])
                di += 1
        samples.append(features_to_events(np.array(x)))
    return samples


def test_owner_accepted_impostor_rejected():
    rng = np.random.default_rng(0)
    owner = typist(rng, np.full(11, 0.09), np.full(10, 0.20), 30)
    impostor = typist(rng, np.full(11, 0.14), np.full(10, 0.35), 10)
    profile = enroll(owner[:20], CONFIG)
    json.dumps(profile)  # hồ sơ phải lưu được bằng JSON
    owner_ok = [verify(profile, s, CONFIG)[1] for s in owner[20:]]
    imp_ok = [verify(profile, s, CONFIG)[1] for s in impostor]
    assert np.mean(owner_ok) >= 0.8
    assert not any(imp_ok)
    conf, _ = verify(profile, owner[20], CONFIG)
    assert 0.0 <= conf <= 1.0


def test_too_few_samples():
    rng = np.random.default_rng(1)
    owner = typist(rng, np.full(11, 0.09), np.full(10, 0.20), 5)
    with pytest.raises(ValueError):
        enroll(owner, CONFIG)


def test_wrong_phrase_raises():
    rng = np.random.default_rng(2)
    owner = typist(rng, np.full(11, 0.09), np.full(10, 0.20), 21)
    profile = enroll(owner[:20], CONFIG)
    bad = [e for e in owner[20] if e["key"] != "t"]
    with pytest.raises(InvalidSampleError):
        verify(profile, bad, CONFIG)


def test_update_keeps_window_and_follows_drift():
    rng = np.random.default_rng(3)
    cfg = dict(CONFIG, window=25)
    early = typist(rng, np.full(11, 0.10), np.full(10, 0.24), 20)
    static = profile = enroll(early, cfg)
    # Người dùng gõ nhanh dần; chỉ cập nhật khi được chấp nhận, đúng như web demo.
    for step in range(100):
        s = typist(rng, np.full(11, 0.10 - 0.0001 * step), np.full(10, 0.24 - 0.0002 * step), 1)[0]
        _, ok = verify(profile, s, cfg)
        if ok:
            profile = update(profile, s, cfg)
    assert len(profile["samples"]) == 25
    late = typist(rng, np.full(11, 0.09), np.full(10, 0.22), 20)
    adaptive_rate = np.mean([verify(profile, s, cfg)[1] for s in late])
    static_rate = np.mean([verify(static, s, cfg)[1] for s in late])
    assert adaptive_rate > static_rate
