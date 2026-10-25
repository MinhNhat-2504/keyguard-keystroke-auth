"""Vẽ hình cho report theo khổ một cột của template IEEE (rộng ~8,8 cm, font Times New Roman).

Chỉ đọc lại các file kết quả đã có, không chạy lại thí nghiệm:
    results/benchmark_cmu_summary.csv     (scripts/run_benchmark.py)
    results/threshold_grid_dev.csv        (scripts/select_threshold.py)
    results/threshold_selection.csv
    results/frr_by_session.csv
Riêng hình thời gian gõ theo phiên đọc trực tiếp bộ CMU và ghi results/typing_time_by_session.csv.

Chạy:  python scripts/make_report_figures.py
Kết quả: figures/report/*.png
"""

from __future__ import annotations

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

from keyguard.features import FEATURE_NAMES, load_cmu  # noqa: E402

OUT = ROOT / "figures/report"
COL_W = 3.45  # inch, vừa một cột IEEE
COLORS = {
    "ScaledManhattan": "tab:blue",
    "OneClassSVM": "tab:orange",
    "IsolationForest": "tab:green",
    "RandomForest": "tab:red",
    "RandomForest-early": "tab:purple",
}
LABELS = {
    "ScaledManhattan": "Scaled Manhattan",
    "OneClassSVM": "One-Class SVM",
    "IsolationForest": "Isolation Forest",
    "RandomForest": "Random Forest",
    "RandomForest-early": "Random Forest (mẫu chưa quen tay)",
}
POLICY_STYLE = {
    "static": ("tab:grey", "Không cập nhật"),
    "accept": ("tab:orange", "Cập nhật khi được chấp nhận"),
    "fallback": ("tab:green", "Cập nhật cả sau OTP"),
}

plt.rcParams.update({
    "font.family": "Times New Roman",
    "mathtext.fontset": "stix",
    "font.size": 8,
    "axes.titlesize": 8,
    "axes.labelsize": 8,
    "legend.fontsize": 7,
    "xtick.labelsize": 7,
    "ytick.labelsize": 7,
    "axes.grid": True,
    "grid.alpha": 0.3,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
    "savefig.pad_inches": 0.02,
})


def fig_eer_vs_enrollment() -> None:
    s = pd.read_csv(ROOT / "results/benchmark_cmu_summary.csv")
    fig, ax = plt.subplots(figsize=(COL_W, 2.4))
    for name in COLORS:
        g = s[s.detector == name].sort_values("n_train")
        ax.errorbar(g.n_train, g.eer_mean, yerr=g.eer_std / np.sqrt(g.n_users), marker="o", markersize=3,
                    capsize=2, linewidth=1, color=COLORS[name], label=LABELS[name])
    ax.set_xscale("log")
    ax.set_xticks(sorted(s.n_train.unique()))
    ax.get_xaxis().set_major_formatter(matplotlib.ticker.ScalarFormatter())
    ax.set_xlabel("Số lần gõ khi đăng ký (n)")
    ax.set_ylabel("EER trung bình")
    ax.legend(ncol=2, loc="upper center", bbox_to_anchor=(0.45, -0.22), frameon=False)
    fig.savefig(OUT / "fig_eer_vs_enrollment.png")
    plt.close(fig)


def fig_typing_time() -> None:
    df = load_cmu(ROOT / "data/raw/DSL-StrongPasswordData.csv")
    dd = [c for c in FEATURE_NAMES if c.startswith("DD.")]
    df = df.assign(total=df[dd].sum(axis=1) + df["H.Return"])
    per_user = df.groupby(["subject", "sessionIndex"])["total"].median().reset_index()
    t = per_user.groupby("sessionIndex")["total"].agg(["mean", "std", "count"]).reset_index()
    t.to_csv(ROOT / "results/typing_time_by_session.csv", index=False)
    fig, ax = plt.subplots(figsize=(COL_W, 1.9))
    se = t["std"] / np.sqrt(t["count"])
    ax.plot(t.sessionIndex, t["mean"], marker="o", markersize=3, color="tab:blue")
    ax.fill_between(t.sessionIndex, t["mean"] - se, t["mean"] + se, color="tab:blue", alpha=0.2)
    ax.set_xlabel("Phiên (mỗi phiên cách nhau ít nhất một ngày)")
    ax.set_ylabel("Thời gian gõ cả câu (giây)")
    ax.set_xticks(t.sessionIndex)
    fig.savefig(OUT / "fig_typing_time.png")
    plt.close(fig)
    print("Thời gian gõ trung bình theo phiên:", t["mean"].round(2).tolist())


def fig_policies() -> None:
    grid = pd.read_csv(ROOT / "results/threshold_grid_dev.csv")
    sel = pd.read_csv(ROOT / "results/threshold_selection.csv")
    sess = pd.read_csv(ROOT / "results/frr_by_session.csv")

    fig, ax = plt.subplots(figsize=(COL_W, 2.3))
    for p, (c, lab) in POLICY_STYLE.items():
        ax.plot(grid[f"far_{p}"], grid[f"frr_{p}"], color=c, linewidth=1.2, label=lab)
        r = sel[sel.policy == p].iloc[0]
        ax.plot(r.far_dev, r.frr_dev, "o", color=c, markersize=4)
    ax.axvline(0.05, color="black", linewidth=0.8, linestyle="--", label="FAR mục tiêu 5%")
    ax.set_xlim(0, 0.4)
    ax.set_ylim(0, 1)
    ax.set_xlabel("FAR (kẻ gian qua được)")
    ax.set_ylabel("FRR")
    ax.legend(loc="upper right")
    fig.savefig(OUT / "fig_policy_tradeoff.png")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(COL_W, 2.1))
    for p, (c, lab) in POLICY_STYLE.items():
        tau = sel[sel.policy == p].threshold.iloc[0]
        ax.plot(sess.session, sess[p], marker="o", markersize=3, color=c, label=f"{lab} (τ = {tau:.2f})")
    ax.set_xlabel("Phiên")
    ax.set_ylabel("FRR, nhóm kiểm tra")
    ax.set_ylim(0, 1)
    ax.set_xticks(sess.session)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.24), frameon=False)
    fig.savefig(OUT / "fig_frr_by_session.png")
    plt.close(fig)


def fig_pipeline() -> None:
    """Sơ đồ một lần đăng nhập: sự kiện phím -> đặc trưng -> điểm -> chuẩn hóa -> quyết định -> cập nhật hồ sơ."""
    from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

    fig, ax = plt.subplots(figsize=(COL_W, 3.1))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10.6)
    ax.axis("off")
    fs = 6.8

    def box(x, y, w, h, text, color="#e8f0fb", edge="tab:blue"):
        ax.add_patch(FancyBboxPatch((x - w / 2, y - h / 2), w, h, boxstyle="round,pad=0.06,rounding_size=0.15",
                                    facecolor=color, edgecolor=edge, linewidth=0.8))
        ax.text(x, y, text, ha="center", va="center", fontsize=fs, linespacing=1.2)

    def arrow(x1, y1, x2, y2, text=None, dx=0.15):
        ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>", mutation_scale=7, linewidth=0.8, color="0.25"))
        if text:
            ax.text((x1 + x2) / 2 + dx, (y1 + y2) / 2, text, fontsize=6.3, va="center", color="0.25")

    X, W = 3.4, 6.2
    box(X, 9.9, W, 0.85, "Gõ “.tie5Roanl” + Enter (keydown/keyup)")
    box(X, 8.45, W, 0.85, "31 đặc trưng H, DD, UD — công thức (1)")
    box(X, 7.0, W, 0.85, r"Điểm bất thường $s(\mathbf{x})$ — công thức (2)")
    box(X, 5.55, W, 0.85, r"Chuẩn hóa $z = (s-\mu_g)/\sigma_g$ — công thức (3)")
    box(X, 4.1, 2.6, 0.85, r"$z \leq \tau$ ?", color="#fdf3e1", edge="tab:orange")
    box(1.5, 2.45, 2.5, 0.85, "Vào thẳng", color="#e6f4e6", edge="tab:green")
    box(5.3, 2.45, 3.1, 0.85, "Xác minh thêm (OTP)", color="#fdecea", edge="tab:red")
    box(X, 0.75, W, 0.85, "Cập nhật hồ sơ, giữ 50 lần gõ gần nhất", color="#f1ecf8", edge="tab:purple")
    box(8.75, 6.3, 2.3, 2.3, "Hồ sơ\n(JSON):\n50 lần gõ,\n" + r"$\mu$, $a$, $\mu_g$, $\sigma_g$", color="#f1ecf8",
        edge="tab:purple")

    for y1, y2 in [(9.45, 8.9), (8.0, 7.45), (6.55, 6.0), (5.1, 4.55)]:
        arrow(X, y1, X, y2)
    arrow(2.5, 3.65, 1.7, 2.9, "đúng", dx=-0.85)
    arrow(4.3, 3.65, 5.1, 2.9, "sai", dx=0.15)
    arrow(1.5, 2.0, 2.3, 1.2)
    arrow(5.3, 2.0, 4.5, 1.2, "qua OTP", dx=0.25)
    arrow(6.55, 0.75, 8.75, 5.1)
    arrow(7.58, 6.8, 6.55, 7.0)
    arrow(7.58, 5.8, 6.55, 5.55)
    fig.savefig(OUT / "fig_pipeline.png")
    plt.close(fig)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    fig_pipeline()
    fig_eer_vs_enrollment()
    fig_typing_time()
    fig_policies()
    print("Đã ghi:", ", ".join(sorted(p.name for p in OUT.glob("*.png"))))


if __name__ == "__main__":
    main()
