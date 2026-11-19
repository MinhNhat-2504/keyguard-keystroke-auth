"""Đọc dữ liệu JSONL, loại mẫu lỗi và phát hiện trùng người/phiên/lượt."""

from __future__ import annotations

import glob
import json
from pathlib import Path

import numpy as np
import pandas as pd

from keyguard.features import extract_features


def load_collected(pattern: str, *, duplicate_policy="first", require_timestamp=False,
                   order="session") -> tuple[pd.DataFrame, list[dict]]:
    if duplicate_policy not in {"first", "exclude-all"} or order not in {"session", "timestamp"}:
        raise ValueError("Chính sách dữ liệu không hợp lệ.")
    files = sorted(glob.glob(pattern))
    if not files:
        raise ValueError(f"Không tìm thấy file nào khớp {pattern!r}")
    records, issues, seen = [], [], set()
    for filename in files:
        with open(filename, encoding="utf-8-sig") as stream:
            for line_no, line in enumerate(stream, 1):
                if not line.strip():
                    continue
                pid = None
                try:
                    r = json.loads(line)
                    if not isinstance(r, dict):
                        raise ValueError("Mỗi dòng phải là object JSON.")
                    pid = r.get("participant_id")
                    if not isinstance(pid, str) or not pid.strip():
                        raise ValueError("participant_id phải là chuỗi không rỗng.")
                    for field in ("session", "rep"):
                        if type(r.get(field)) is not int or r[field] < 1:
                            raise ValueError(f"{field} phải là số nguyên dương.")
                    if not isinstance(r.get("events"), list):
                        raise ValueError("events phải là danh sách sự kiện.")
                    x = extract_features(r["events"])
                    if not np.isfinite(x).all():
                        raise ValueError("Đặc trưng chứa NaN hoặc Infinity.")
                    key = (pid, r["session"], r["rep"])
                    if key in seen and duplicate_policy == "first":
                        raise ValueError("Trùng participant_id/session/rep; không đếm hai lần.")
                    seen.add(key)
                    timestamp = r.get("collected_at")
                    if timestamp is not None:
                        timestamp = pd.to_datetime(timestamp, utc=True, errors="raise")
                        if pd.isna(timestamp):
                            raise ValueError("collected_at không hợp lệ.")
                    elif require_timestamp or order == "timestamp":
                        raise ValueError("Thiếu collected_at; không suy đoán thứ tự theo thời gian.")
                    records.append({"participant_id": pid, "session": r["session"], "rep": r["rep"],
                                    "x": x, "collected_at": timestamp,
                                    "source_file": Path(filename).name, "source_line": line_no})
                except (ValueError, KeyError, TypeError, OverflowError) as exc:
                    issues.append({"file": Path(filename).name, "line": line_no,
                                   "participant_id": pid if isinstance(pid, str) else None,
                                   "reason": str(exc)})
    df = pd.DataFrame(records, columns=["participant_id", "session", "rep", "x", "collected_at",
                                       "source_file", "source_line"])
    if duplicate_policy == "exclude-all":
        duplicate = df.duplicated(["participant_id", "session", "rep"], keep=False)
        for row in df[duplicate].itertuples():
            issues.append({"file": row.source_file, "line": row.source_line,
                           "participant_id": row.participant_id,
                           "reason": "Khóa trùng: loại TẤT CẢ dòng cùng participant_id/session/rep."})
        df = df[~duplicate]
    sort = ["participant_id", "collected_at", "source_file", "source_line"] if order == "timestamp" else ["participant_id", "session", "rep"]
    return df.sort_values(sort).reset_index(drop=True), issues


def audit_collected(df: pd.DataFrame, issues: list[dict], min_people=15, min_sessions=2, min_reps=40) -> dict:
    groups = df.groupby(["participant_id", "session"])
    sessions = [{"participant_id": pid, "session": int(s), "valid_reps": len(g),
                 "meets_min_reps": len(g) >= min_reps} for (pid, s), g in groups]
    qualified = sum(sum(row["meets_min_reps"] for row in sessions if row["participant_id"] == pid)
                    >= min_sessions for pid in df.participant_id.unique())
    return {"valid_samples": len(df), "participants": int(df.participant_id.nunique()),
            "rejected_rows": len(issues), "qualified_participants": qualified,
            "requirements": {"min_people": min_people, "min_sessions": min_sessions, "min_reps": min_reps},
            "structural_ready": qualified >= min_people and not issues,
            "different_days_verified": False, "consent_verified": False,
            "timestamped_samples": int(df.collected_at.notna().sum()),
            "note": "collected_at là thời gian server khi có; chưa xác minh đồng ý và đủ phiên khác ngày. Không suy ra người thật từ mã.",
            "sessions": sessions, "issues": issues}
