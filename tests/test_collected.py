import json

import numpy as np

from keyguard.collected import audit_collected, load_collected
from keyguard.features import FEATURE_NAMES, features_to_events


def test_loader_reports_bad_rows_and_duplicates_without_inflating_data(tmp_path):
    x = np.array([0.1 if n.startswith("H.") else 0.25 if n.startswith("DD.") else 0.15
                  for n in FEATURE_NAMES])
    row = {"participant_id": "P01", "session": 1, "rep": 1, "events": features_to_events(x)}
    rows = [json.dumps(row), json.dumps(row), "{broken", "[]", json.dumps(dict(row, rep=-1))]
    (tmp_path / "P01.jsonl").write_text("\n".join(rows), encoding="utf-8")
    df, issues = load_collected(str(tmp_path / "*.jsonl"))
    assert len(df) == 1
    assert len(issues) == 4
    assert [r["line"] for r in issues] == [2, 3, 4, 5]
    audit = audit_collected(df, issues)
    assert not audit["structural_ready"]
    assert audit["qualified_participants"] == 0


def test_audit_does_not_certify_days_or_consent_even_with_enough_rows(tmp_path):
    (tmp_path / "empty.jsonl").write_text("", encoding="utf-8")
    df, issues = load_collected(str(tmp_path / "*.jsonl"))
    assert df.empty
    audit = audit_collected(df, issues)
    assert not audit["different_days_verified"]
    assert not audit["consent_verified"]
    assert not audit["structural_ready"]
