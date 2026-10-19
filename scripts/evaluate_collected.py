"""Việc 1.5: đánh giá trên dữ liệu nhóm tự thu qua web (định dạng JSONL).

Mỗi dòng của file .jsonl:
    {"participant_id": "P07", "session": 2, "rep": 15, "events": [{"key": ".", "type": "down", "t": 0.0}, ...]}

Đánh giá đúng như sản phẩm chạy, dùng nguyên cấu hình trong models/model_config.json
(chọn trên CMU) để xem cấu hình đó có còn đúng với dữ liệu thu qua trình duyệt không:
- mỗi người đăng ký bằng n lần gõ hợp lệ đầu tiên, rồi "đăng nhập" lần lượt bằng các
  lần gõ còn lại theo thứ tự thời gian, cập nhật hồ sơ theo chính sách trong cấu hình;
- kẻ gian là những người tham gia khác, theo hai kịch bản:
    chưa quen tay: 5 lần gõ hợp lệ đầu tiên của mỗi người,
    đã quen tay  : 5 lần gõ hợp lệ cuối cùng của mỗi người;
  kẻ gian thử tại các mốc sau mỗi 50 lần đăng nhập và không làm thay đổi hồ sơ.
- FRR được tách theo phiên để thấy ảnh hưởng của việc gõ ở ngày khác.

Chạy:  python scripts/evaluate_collected.py --input "data/collected/*.jsonl"
Kết quả: results/collected_per_user.csv, results/collected_by_session.csv, results/collected_summary.json
"""

from __future__ import annotations

import argparse
import glob
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.stdout.reconfigure(encoding="utf-8")  # in tiếng Việt trên console Windows

from keyguard.evaluation import equal_error_rate  # noqa: E402
from keyguard.features import InvalidSampleError, extract_features  # noqa: E402
from keyguard.model import load_config  # noqa: E402
from keyguard.simulation import simulate_user  # noqa: E402

N_IMPOSTOR_PER_PARTICIPANT = 5
MIN_LOGINS = 5


def load_jsonl(pattern: str) -> tuple[pd.DataFrame, dict]:
    records, invalid = [], {}
    files = sorted(glob.glob(pattern))
    if not files:
        raise SystemExit(f"Không tìm thấy file nào khớp {pattern!r}")
    for path in files:
        with open(path, encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                r = json.loads(line)
                pid = str(r["participant_id"])
                try:
                    x = extract_features(r["events"])
                except InvalidSampleError:
                    invalid[pid] = invalid.get(pid, 0) + 1
                    continue
                records.append({"participant_id": pid, "session": int(r["session"]), "rep": int(r["rep"]), "x": x})
    if not records:
        raise SystemExit("Không có lần gõ hợp lệ nào.")
    df = pd.DataFrame(records).sort_values(["participant_id", "session", "rep"]).reset_index(drop=True)
    return df, invalid


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--input", default=str(ROOT / "data/collected/*.jsonl"))
    ap.add_argument("--config", default=None)
    ap.add_argument("--out-prefix", default="collected")
    args = ap.parse_args()

    cfg = load_config(args.config)
    n, tau, policy = cfg["n_enroll"], cfg["threshold"], cfg["policy"]
    df, invalid = load_jsonl(args.input)
    print(f"{len(df)} lần gõ hợp lệ của {df.participant_id.nunique()} người; "
          f"{sum(invalid.values())} lần gõ sai bị loại. Cấu hình: {policy}, n = {n}, tau = {tau:.2f}")

    data = {pid: g.reset_index(drop=True) for pid, g in df.groupby("participant_id")}
    early = {pid: np.vstack(g["x"].to_list()[:N_IMPOSTOR_PER_PARTICIPANT]) for pid, g in data.items()}
    late = {pid: np.vstack(g["x"].to_list()[-N_IMPOSTOR_PER_PARTICIPANT:]) for pid, g in data.items()}
    if len(data) < 2:
        raise SystemExit("Cần ít nhất 2 người tham gia để đo FAR.")

    rows, sess_rows, pooled = [], [], {"g": [], "i_early": [], "i_late": []}
    for pid, g in data.items():
        X = np.vstack(g["x"].to_list())
        if len(X) < n + MIN_LOGINS:
            print(f"Bỏ qua {pid}: chỉ có {len(X)} lần gõ hợp lệ (cần ít nhất {n + MIN_LOGINS}).")
            continue
        others = [o for o in data if o != pid]
        zg, zi_early = simulate_user(X, np.vstack([early[o] for o in others]), cfg, tau, policy)
        _, zi_late = simulate_user(X, np.vstack([late[o] for o in others]), cfg, tau, policy)
        sessions = g["session"].to_numpy()[n:]
        rows.append({
            "participant_id": pid,
            "n_valid": len(X),
            "n_invalid": invalid.get(pid, 0),
            "n_sessions": int(g["session"].nunique()),
            "n_logins": len(zg),
            "frr": float(np.mean(zg > tau)),
            "far_early": float(np.mean(zi_early <= tau)),
            "far_late": float(np.mean(zi_late <= tau)),
            "eer_early": equal_error_rate(zg, zi_early),
            "eer_late": equal_error_rate(zg, zi_late),
        })
        for s in np.unique(sessions):
            sess_rows.append({"participant_id": pid, "session": int(s), "logins": int(np.sum(sessions == s)),
                              "rejected": int(np.sum(zg[sessions == s] > tau))})
        pooled["g"].append(zg)
        pooled["i_early"].append(zi_early)
        pooled["i_late"].append(zi_late)

    if not rows:
        raise SystemExit("Không người tham gia nào đủ dữ liệu.")
    res = pd.DataFrame(rows)
    sess = pd.DataFrame(sess_rows).groupby("session")[["logins", "rejected"]].sum().reset_index()
    sess["frr"] = sess["rejected"] / sess["logins"]
    G, IE, IL = (np.concatenate(pooled[k]) for k in ("g", "i_early", "i_late"))
    summary = {
        "input": args.input,
        "policy": policy,
        "n_enroll": n,
        "threshold": tau,
        "participants": int(len(res)),
        "logins": int(len(G)),
        "frr_pooled": float(np.mean(G > tau)),
        "far_early_pooled": float(np.mean(IE <= tau)),
        "far_late_pooled": float(np.mean(IL <= tau)),
        "eer_early_mean": float(res["eer_early"].mean()),
        "eer_late_mean": float(res["eer_late"].mean()),
        "cmu_test_far": cfg.get("test_far"),
        "cmu_test_frr": cfg.get("test_frr"),
    }
    (ROOT / "results").mkdir(exist_ok=True)
    res.to_csv(ROOT / f"results/{args.out_prefix}_per_user.csv", index=False)
    sess.to_csv(ROOT / f"results/{args.out_prefix}_by_session.csv", index=False)
    with open(ROOT / f"results/{args.out_prefix}_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print(res.round(3).to_string(index=False))
    print("\nFRR theo phiên:\n" + sess.round(3).to_string(index=False))
    print(f"\nTổng hợp: FRR = {summary['frr_pooled']:.3f}; FAR (kẻ gian chưa quen tay) = {summary['far_early_pooled']:.3f}; "
          f"FAR (kẻ gian đã quen tay) = {summary['far_late_pooled']:.3f}")
    print(f"So với CMU (nhóm kiểm tra): FAR = {cfg.get('test_far'):.3f}, FRR = {cfg.get('test_frr'):.3f}")


if __name__ == "__main__":
    main()
