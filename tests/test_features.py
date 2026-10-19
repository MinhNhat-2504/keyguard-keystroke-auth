from pathlib import Path

import numpy as np
import pytest

from keyguard.features import (
    FEATURE_NAMES,
    InvalidSampleError,
    extract_features,
    features_to_events,
    load_cmu,
)

CMU_PATH = Path(__file__).resolve().parents[1] / "data/raw/DSL-StrongPasswordData.csv"


def valid_vector(hold=0.1, down_down=0.25):
    """Vector hợp lệ: UD = DD - H."""
    x = []
    for name in FEATURE_NAMES:
        x.append(hold if name.startswith("H.") else down_down if name.startswith("DD.") else down_down - hold)
    return np.array(x)


def test_feature_count():
    assert len(FEATURE_NAMES) == 31


@pytest.mark.skipif(not CMU_PATH.exists(), reason="chưa tải bộ dữ liệu CMU")
def test_roundtrip_matches_cmu_rows():
    df = load_cmu(CMU_PATH)
    rows = df.sample(200, random_state=0)[FEATURE_NAMES].to_numpy()
    for x in rows:
        assert np.allclose(extract_features(features_to_events(x)), x, atol=1e-5)


def test_shift_and_modifiers_are_ignored():
    x = valid_vector()
    events = features_to_events(x)
    r_down = next(e for e in events if e["key"] == "R" and e["type"] == "down")
    r_up = next(e for e in events if e["key"] == "R" and e["type"] == "up")
    events += [
        {"key": "Shift", "type": "down", "t": r_down["t"] - 30},
        {"key": "Shift", "type": "up", "t": r_up["t"] + 10},
    ]
    # Trình duyệt có thể báo keyup là "r" thường nếu Shift được nhả trước.
    r_up["key"] = "r"
    assert np.allclose(extract_features(events), x)


def test_wrong_phrase_is_rejected():
    events = features_to_events(valid_vector())
    events = [e for e in events if e["key"] != "5"]
    with pytest.raises(InvalidSampleError):
        extract_features(events)


def test_missing_keyup_is_rejected():
    events = features_to_events(valid_vector())
    events = [e for e in events if not (e["key"] == "a" and e["type"] == "up")]
    with pytest.raises(InvalidSampleError):
        extract_features(events)
