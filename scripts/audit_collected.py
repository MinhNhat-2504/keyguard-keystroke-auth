"""Kiểm tra dữ liệu bàn giao trước khi đánh giá, không sinh thêm dữ liệu."""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

from keyguard.collected import audit_collected, load_collected


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--input", default=str(ROOT / "data/collected/*.jsonl"))
    ap.add_argument("--output", default=str(ROOT / "results/collected_audit.json"))
    args = ap.parse_args()
    try:
        df, issues = load_collected(args.input)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    audit = audit_collected(df, issues)
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in audit.items() if k not in ("sessions", "issues")}, ensure_ascii=False, indent=2))
    print(f"Chi tiết người/phiên và dòng lỗi: {out}")


if __name__ == "__main__":
    main()
