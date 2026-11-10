"""Kiểm tra hợp đồng enroll/verify/update bằng mẫu dựng từ CMU, không phải web/OTP."""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.stdout.reconfigure(encoding="utf-8")

from keyguard.model import enroll, load_config, update, verify


def main():
    cfg = load_config()
    rows = [json.loads(line) for line in (ROOT / "data/sample/sample_from_cmu.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    pid = rows[0]["participant_id"]
    rows = sorted([r for r in rows if r["participant_id"] == pid], key=lambda r: (r["session"], r["rep"]))
    n = cfg["n_enroll"]
    profile = enroll([r["events"] for r in rows[:n]])
    profile = json.loads(json.dumps(profile))
    confidence, accepted = verify(profile, rows[n]["events"])
    # Ground truth của dữ liệu mẫu đã biết: chỉ kiểm tra update lưu được JSON.
    updated = json.loads(json.dumps(update(profile, rows[n]["events"])))
    if not 0 <= confidence <= 1 or len(updated["samples"]) != min(n + 1, cfg["window"]):
        raise RuntimeError("Hợp đồng mô hình không đạt.")
    result = {"source_kind": "cmu-derived", "enroll_samples": len(profile["samples"]),
              "confidence": confidence, "accepted": bool(accepted), "updated_samples": len(updated["samples"]),
              "json_roundtrip": True, "otp_tested": False, "api_http_tested": False}
    out = ROOT / "results/model_smoke.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
