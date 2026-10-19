"""Việc 1.4: chọn ngưỡng chung và cách cập nhật hồ sơ cho web demo, bằng mô phỏng đăng nhập.

Khác với run_benchmark.py (EER dùng ngưỡng lý tưởng riêng cho từng người), ở đây mô
phỏng đúng cách sản phẩm chạy, dùng chính các hàm trong keyguard/model.py:

- Chia người dùng theo seed: 36 người "phát triển" để chọn ngưỡng tau, 15 người "kiểm tra"
  không tham gia chọn tau.
- Mỗi người đăng ký bằng n lần gõ đầu tiên, sau đó "đăng nhập" lần lượt bằng các lần gõ
  còn lại theo đúng thứ tự thời gian (đến lần thứ 400, phiên 8).
- Kẻ gian: 5 lần gõ đầu của từng người khác trong cùng nhóm, thử đăng nhập tại các mốc
  sau mỗi 50 lần đăng nhập của chủ tài khoản. Lần thử của kẻ gian không cập nhật hồ sơ.
- Ba chính sách cập nhật hồ sơ (giữ tối đa `window` lần gõ gần nhất):
    static   : hồ sơ giữ nguyên sau khi đăng ký;
    accept   : chỉ thêm lần gõ được nhịp gõ chấp nhận;
    fallback : xác thực theo rủi ro. Nhịp gõ không khớp thì hỏi thêm một bước xác minh
               (ví dụ OTP); chủ tài khoản qua được bước đó nên lần gõ nào của chủ cũng
               được thêm vào hồ sơ. Khi đó FRR = tỉ lệ lần đăng nhập phải xác minh thêm.
- tau: ngưỡng lớn nhất mà FAR trên nhóm phát triển không vượt mục tiêu (mặc định 5%).

Chạy:  python scripts/select_threshold.py
Kết quả: results/threshold_selection.csv, results/threshold_grid_dev.csv,
         results/frr_by_session.csv, figures/update_policies.png, models/model_config.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.stdout.reconfigure(encoding="utf-8")  # in tiếng Việt trên console Windows

from keyguard.features import FEATURE_NAMES, PHRASE, load_cmu  # noqa: E402
from keyguard.simulation import POLICIES, POLICY_LABELS, simulate_user  # noqa: E402

N_IMPOSTOR_PER_SUBJECT = 5
CHECKPOINT_EVERY = 50
REPS_PER_SESSION = 50

POLICY_COLORS = {"static": "tab:grey", "accept": "tab:orange", "fallback": "tab:green"}


def simulate_group(by_subject: dict, users: list, cfg: dict, tau: float, policy: str) -> dict:
    out = {}
    for u in users:
        imp_X = np.vstack([by_subject[o][:N_IMPOSTOR_PER_SUBJECT] for o in users if o != u])
        out[u] = simulate_user(by_subject[u], imp_X, cfg, tau, policy, CHECKPOINT_EVERY)
    return out


def rates(sim: dict, tau: float) -> tuple[float, float]:
    zg = np.concatenate([g for g, _ in sim.values()])
    zi = np.concatenate([i for _, i in sim.values()])
    return float(np.mean(zi <= tau)), float(np.mean(zg > tau))


def frr_by_session(sim: dict, tau: float, n: int) -> pd.Series:
    zg = np.vstack([g for g, _ in sim.values()])
    session = (np.arange(n, n + zg.shape[1]) // REPS_PER_SESSION) + 1
    return pd.Series({s: float(np.mean(zg[:, session == s] > tau)) for s in np.unique(session)})


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data", default=str(ROOT / "data/raw/DSL-StrongPasswordData.csv"))
    ap.add_argument("--n-enroll", type=int, default=20)
    ap.add_argument("--window", type=int, default=50)
    ap.add_argument("--cv-folds", type=int, default=5)
    ap.add_argument("--target-far", type=float, default=0.05)
    ap.add_argument("--dev-size", type=int, default=36)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--tau-grid", default="-1.0:3.0:0.1", help="lưới ngưỡng cho chính sách accept: đầu:cuối:bước")
    ap.add_argument("--deploy-policy", default="fallback", choices=POLICIES)
    args = ap.parse_args()

    df = load_cmu(args.data)
    by_subject = {
        s: g.sort_values(["sessionIndex", "rep"])[FEATURE_NAMES].to_numpy() for s, g in df.groupby("subject")
    }
    rng = np.random.default_rng(args.seed)
    perm = rng.permutation(np.array(sorted(by_subject)))
    dev_users, test_users = sorted(perm[: args.dev_size]), sorted(perm[args.dev_size :])
    print(f"Nhóm phát triển: {len(dev_users)} người, nhóm kiểm tra: {len(test_users)} người")

    cfg = {"detector": "ScaledManhattan", "n_enroll": args.n_enroll, "window": args.window, "cv_folds": args.cv_folds}

    # static và fallback: hồ sơ cập nhật không tùy vào việc chấp nhận, nên z không phụ thuộc tau:
    # chạy một lần rồi quét tau. accept: tau quyết định lần nào được cập nhật, phải chạy lại cho từng tau.
    fixed_dev = {p: simulate_group(by_subject, dev_users, cfg, 0.0, p) for p in ["static", "fallback"]}
    start, stop, step = (float(v) for v in args.tau_grid.split(":"))
    grid_rows = []
    for tau in np.round(np.arange(start, stop + step / 2, step), 4):
        row = {"tau": tau}
        for p in POLICIES:
            sim = fixed_dev[p] if p in fixed_dev else simulate_group(by_subject, dev_users, cfg, tau, p)
            row[f"far_{p}"], row[f"frr_{p}"] = rates(sim, tau)
        grid_rows.append(row)
        print(f"tau={tau:5.2f}  " + "  ".join(f"{p}: FAR={row[f'far_{p}']:.3f} FRR={row[f'frr_{p}']:.3f}" for p in POLICIES))
    grid_df = pd.DataFrame(grid_rows)

    rows, sessions, taus = [], {}, {}
    for p in POLICIES:
        if p in fixed_dev:  # z cố định: chọn tau đúng bằng phân vị, không phụ thuộc lưới
            zi = np.concatenate([i for _, i in fixed_dev[p].values()])
            tau = float(np.quantile(zi, args.target_far, method="lower"))
            dev = fixed_dev[p]
        else:
            feasible = grid_df[grid_df[f"far_{p}"] <= args.target_far]
            if feasible.empty:
                raise SystemExit(f"{p}: không có tau nào trong lưới đạt FAR mục tiêu; hãy mở rộng --tau-grid.")
            tau = float(feasible.tau.max())
            dev = simulate_group(by_subject, dev_users, cfg, tau, p)
        test = simulate_group(by_subject, test_users, cfg, tau, p)
        taus[p] = tau
        far_dev, frr_dev = rates(dev, tau)
        far_te, frr_te = rates(test, tau)
        rows.append({
            "detector": cfg["detector"], "policy": p, "n_enroll": args.n_enroll, "window": args.window,
            "threshold": tau, "far_dev": far_dev, "frr_dev": frr_dev, "far_test": far_te, "frr_test": frr_te,
        })
        sessions[p] = frr_by_session(test, tau, args.n_enroll)
        print(f"\n{p:8s} tau={tau:.2f}  dev FAR={far_dev:.3f} FRR={frr_dev:.3f}  test FAR={far_te:.3f} FRR={frr_te:.3f}")

    (ROOT / "results").mkdir(exist_ok=True)
    res = pd.DataFrame(rows)
    res.to_csv(ROOT / "results/threshold_selection.csv", index=False)
    grid_df.to_csv(ROOT / "results/threshold_grid_dev.csv", index=False)
    sess_df = pd.DataFrame(sessions).rename_axis("session").reset_index()
    sess_df.to_csv(ROOT / "results/frr_by_session.csv", index=False)
    print("\nFRR theo phiên trên nhóm kiểm tra:\n" + sess_df.round(3).to_string(index=False))

    chosen = res[res.policy == args.deploy_policy].iloc[0]
    config = {
        "phrase": PHRASE,
        "detector": cfg["detector"],
        "policy": args.deploy_policy,
        "n_enroll": args.n_enroll,
        "min_enroll": args.n_enroll,
        "window": args.window,
        "cv_folds": args.cv_folds,
        "threshold": float(chosen.threshold),
        "target_far": args.target_far,
        "test_far": float(chosen.far_test),
        "test_frr": float(chosen.frr_test),
        "seed": args.seed,
        "dev_users": [str(u) for u in dev_users],
        "test_users": [str(u) for u in test_users],
        "created_by": "scripts/select_threshold.py",
    }
    (ROOT / "models").mkdir(exist_ok=True)
    with open(ROOT / "models/model_config.json", "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
    print(f"\nĐã ghi models/model_config.json ({args.deploy_policy}, tau = {config['threshold']:.2f})")

    (ROOT / "figures").mkdir(exist_ok=True)
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.0), sharey=True)
    for p in POLICIES:
        axes[0].plot(grid_df[f"far_{p}"], grid_df[f"frr_{p}"], color=POLICY_COLORS[p], label=POLICY_LABELS[p])
        r = res[res.policy == p].iloc[0]
        axes[0].plot(r.far_dev, r.frr_dev, "o", color=POLICY_COLORS[p])
    axes[0].axvline(args.target_far, color="black", linewidth=0.8, linestyle="--", label=f"FAR mục tiêu {args.target_far:.0%}")
    axes[0].set_xlim(0, 0.5)
    axes[0].set_xlabel("FAR (kẻ gian qua được)")
    axes[0].set_ylabel("FRR (chủ bị từ chối / phải xác minh thêm)")
    axes[0].set_title("Đánh đổi FAR–FRR, nhóm phát triển")
    axes[0].grid(alpha=0.3)
    axes[0].legend(fontsize=8)
    for p in POLICIES:
        axes[1].plot(sess_df.session, sess_df[p], marker="o", color=POLICY_COLORS[p],
                     label=f"{POLICY_LABELS[p]} (τ = {taus[p]:.2f})")
    axes[1].set_xlabel("Phiên (mỗi phiên cách nhau ít nhất một ngày)")
    axes[1].set_title("FRR theo thời gian, nhóm kiểm tra")
    axes[1].set_ylim(0, 1)
    axes[1].grid(alpha=0.3)
    axes[1].legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(ROOT / "figures/update_policies.png", dpi=200)
    plt.close(fig)


if __name__ == "__main__":
    main()
