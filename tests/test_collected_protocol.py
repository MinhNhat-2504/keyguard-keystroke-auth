import json

import numpy as np

from keyguard.collected import load_collected
from keyguard.features import FEATURE_NAMES, features_to_events


def test_primary_protocol_excludes_both_ambiguous_rows_and_uses_time(tmp_path):
    x = np.array([0.1 if n.startswith("H.") else 0.25 if n.startswith("DD.") else 0.15
                  for n in FEATURE_NAMES])
    base = {"participant_id": "P01", "session": 1, "events": features_to_events(x)}
    rows = [dict(base, rep=1),
            dict(base, rep=2, collected_at="2026-11-10T01:00:00+00:00"),
            dict(base, rep=2, collected_at="2026-11-10T01:01:00+00:00"),
            dict(base, rep=4, collected_at="2026-11-10T02:00:00+00:00"),
            dict(base, rep=3, collected_at="2026-11-10T03:00:00+00:00")]
    (tmp_path / "P01.jsonl").write_text("\n".join(json.dumps(r) for r in rows), encoding="utf-8")
    df, issues = load_collected(str(tmp_path / "*.jsonl"), duplicate_policy="exclude-all",
                                require_timestamp=True, order="timestamp")
    assert df.rep.tolist() == [4, 3]
    assert {r["line"] for r in issues} == {1, 2, 3}
    # Nhánh độ nhạy giữ bản đầu của khóa trùng, vẫn không đoán ngày mẫu cũ.
    df, issues = load_collected(str(tmp_path / "*.jsonl"), duplicate_policy="first",
                                require_timestamp=True, order="timestamp")
    assert df.rep.tolist() == [2, 4, 3]
    assert len(issues) == 2
