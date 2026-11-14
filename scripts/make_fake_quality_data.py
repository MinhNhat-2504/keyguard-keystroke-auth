#!/usr/bin/env python3
"""Tạo DỮ LIỆU GIẢ để kiểm chứng script check_data_quality.py (task B1).

Đây là dữ liệu TỔNG HỢP, không phải của người thật. Mỗi file cố ý chứa một nhóm lỗi:
  FAKE01  sạch về lỗi (nhưng không có thiết bị: chỉ là thông tin chưa ghi nhận)
  FAKE02  trùng khóa (người, phiên, rep) và thiếu số rep
  FAKE03  một dòng thiếu collected_at
  FAKE04  sự kiện không hợp lệ: gõ r thường thay R hoa, thiếu keyup, t không phải số
  FAKE05  dòng không phải JSON, dòng thiếu trường, dòng sai participant_id

Chạy:  python scripts/make_fake_quality_data.py            (ghi vào tests/fake_quality_data/)
Kỳ vọng số vấn đề được ghi trong tests/fake_quality_data/EXPECTED.json.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tests" / "fake_quality_data"

KEYS = [".", "t", "i", "e", "5", "R", "o", "a", "n", "l", "Enter"]
BASE_HOLD = [0.09, 0.08, 0.10, 0.09, 0.11, 0.10, 0.09, 0.08, 0.10, 0.09, 0.12]
BASE_GAP = [0.22, 0.18, 0.20, 0.25, 0.30, 0.19, 0.21, 0.17, 0.20, 0.23]


def sample(rng: np.random.Generator) -> list[dict]:
    events, t = [], 0.0
    for i, key in enumerate(KEYS):
        hold = BASE_HOLD[i] * (1 + rng.normal(0, 0.05))
        events.append({"key": key, "type": "down", "t": round(t * 1000, 3)})
        events.append({"key": key, "type": "up", "t": round((t + hold) * 1000, 3)})
        if i < len(BASE_GAP):
            t += max(BASE_GAP[i] * (1 + rng.normal(0, 0.05)), hold + 0.02)
    return sorted(events, key=lambda e: e["t"])


def rec(pid, session, rep, events, with_time=True):
    r = {"participant_id": pid, "session": session, "rep": rep}
    if with_time:
        r["collected_at"] = "2026-01-01T10:00:00+00:00"
    r["events"] = events
    return r


def write(name, lines):
    (OUT / name).write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    rng = np.random.default_rng(7)
    OUT.mkdir(parents=True, exist_ok=True)
    j = lambda r: json.dumps(r, ensure_ascii=False)  # noqa: E731

    write("FAKE01.jsonl", [j(rec("FAKE01", 1, n, sample(rng))) for n in (1, 2, 3)])
    # FAKE02: rep 2 hai lần (khóa trùng) và thiếu rep 3 (nhảy cách)
    write("FAKE02.jsonl", [j(rec("FAKE02", 1, 1, sample(rng))), j(rec("FAKE02", 1, 2, sample(rng))),
                           j(rec("FAKE02", 1, 2, sample(rng))), j(rec("FAKE02", 1, 4, sample(rng)))])
    write("FAKE03.jsonl", [j(rec("FAKE03", 1, 1, sample(rng))), j(rec("FAKE03", 1, 2, sample(rng), with_time=False))])
    bad_case = [dict(e, key="r") if e["key"] == "R" else e for e in sample(rng)]
    no_up = [e for e in sample(rng) if not (e["key"] == "l" and e["type"] == "up")]
    bad_t = sample(rng)
    bad_t[0] = dict(bad_t[0], t="abc")
    write("FAKE04.jsonl", [j(rec("FAKE04", 1, 1, bad_case)), j(rec("FAKE04", 1, 2, no_up)), j(rec("FAKE04", 1, 3, bad_t))])
    missing = {"participant_id": "FAKE05", "session": 1, "collected_at": "2026-01-01T10:00:00+00:00"}  # thiếu rep, events
    write("FAKE05.jsonl", ["{không phải json", j(missing), j(rec("FAKE99", 1, 1, sample(rng)))])

    expected = {
        "CHUA_GHI_NHAN/THIEU_THIET_BI": 5,       # mỗi file một dòng
        "CHUA_GHI_NHAN/THIEU_THOI_GIAN": 1,      # chỉ FAKE03 (1 dòng)
        "LOI/KHOA_TRUNG": 2,
        "LOI/REP_KHONG_LIEN_TUC": 1,
        "LOI/SU_KIEN_KHONG_HOP_LE": 3,
        "LOI/JSON_KHONG_DOC_DUOC": 1,
        "LOI/THIEU_TRUONG": 1,
        "LOI/SAI_MA_NGUOI": 1,
    }
    (OUT / "EXPECTED.json").write_text(json.dumps(expected, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Đã tạo dữ liệu giả trong {OUT}")


if __name__ == "__main__":
    sys.exit(main())
