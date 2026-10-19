"""Tạo file JSONL mẫu từ CMU, đúng định dạng dữ liệu web thu được.

Chỉ dùng để chạy thử quy trình (evaluate_collected.py, web demo) khi chưa có dữ liệu
thật. KHÔNG dùng kết quả chạy trên file này làm kết quả trong báo cáo.

Chạy:  python scripts/make_sample_jsonl.py
Kết quả: data/sample/sample_from_cmu.jsonl (6 người x 3 phiên x 40 lần gõ)
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.stdout.reconfigure(encoding="utf-8")  # in tiếng Việt trên console Windows

from keyguard.features import FEATURE_NAMES, features_to_events, load_cmu  # noqa: E402

SUBJECTS = ["s002", "s003", "s004", "s005", "s007", "s008"]
SESSIONS = [1, 2, 3]
REPS_PER_SESSION = 40


def main() -> None:
    df = load_cmu(ROOT / "data/raw/DSL-StrongPasswordData.csv")
    out = ROOT / "data/sample/sample_from_cmu.jsonl"
    out.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with open(out, "w", encoding="utf-8") as f:
        for i, s in enumerate(SUBJECTS, 1):
            for sess in SESSIONS:
                rows = df[(df.subject == s) & (df.sessionIndex == sess)].sort_values("rep").head(REPS_PER_SESSION)
                for rep, x in enumerate(rows[FEATURE_NAMES].to_numpy(), 1):
                    rec = {"participant_id": f"SAMPLE{i:02d}", "session": sess, "rep": rep, "events": features_to_events(x)}
                    f.write(json.dumps(rec) + "\n")
                    n += 1
    print(f"Đã ghi {n} dòng vào {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
