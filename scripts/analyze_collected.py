"""Phân tích lỗi/độ nhạy, vẽ hình từ kết quả cố định; không chọn lại mô hình/ngưỡng."""

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
sys.stdout.reconfigure(encoding="utf-8")

from keyguard.collected import load_collected
from keyguard.features import FEATURE_NAMES
from keyguard.model import build_profile, load_config


def main():
    users = pd.read_csv(ROOT / "results/collected_preliminary_per_user.csv")
    df, _ = load_collected(str(ROOT / "data/collected/*.jsonl"), duplicate_policy="exclude-all",
                           require_timestamp=True, order="timestamp")
    cfg = load_config()
    rows = []
    for pid, g in df.groupby("participant_id"):
        X = np.vstack(g.x)
        profile = build_profile(X[:cfg["n_enroll"]], cfg)
        duration = X[:, [i for i, name in enumerate(FEATURE_NAMES) if name.startswith("DD.")]].sum(axis=1) + X[:, -1]
        rows.append({"participant_id": pid, "samples": len(X), "median_duration_seconds": np.median(duration),
                     "enrollment_score_mean": profile["score_mean"], "enrollment_score_std": profile["score_std"],
                     "enrollment_duration_median_seconds": np.median(duration[:20])})
    diagnostic = pd.DataFrame(rows).merge(users, on="participant_id")
    diagnostic.to_csv(ROOT / "results/collected_diagnostics.csv", index=False)
    plt.rcParams.update({"font.family": "Times New Roman", "font.size": 8, "savefig.dpi": 250,
                         "savefig.bbox": "tight"})
    fig, axes = plt.subplots(1, 2, figsize=(6.7, 3.3), sharey=True)
    ordered = users.sort_values("far_late")
    axes[0].barh(ordered.participant_id, ordered.far_early * 100, color="tab:orange", label="5 lượt đầu")
    axes[0].plot(ordered.far_late * 100, ordered.participant_id, "o", color="tab:red", markersize=3, label="5 lượt cuối")
    axes[0].axvline(5, color="black", linestyle="--", linewidth=.7, label="Mốc tham chiếu 5%")
    axes[0].set_xlabel("FAR (%) — cấu hình CMU giữ nguyên")
    axes[0].legend(fontsize=6)
    axes[1].barh(ordered.participant_id, ordered.frr * 100, color="tab:blue")
    axes[1].set_xlabel("FRR / cần xác minh thêm (%)")
    for ax in axes:
        ax.grid(axis="x", alpha=.2)
    fig.tight_layout()
    fig.savefig(ROOT / "figures/collected_preliminary.png")
    plt.close(fig)
    # Hình một cột cho report, không thu nhỏ hình hai panel gây khó đọc.
    fig, ax = plt.subplots(figsize=(3.35, 3.0))
    ax.barh(ordered.participant_id, ordered.far_early*100, color="tab:orange", label="FAR đầu")
    ax.plot(ordered.far_late*100, ordered.participant_id, "o", markersize=3, color="tab:red", label="FAR cuối")
    ax.plot(ordered.frr*100, ordered.participant_id, "x", markersize=3, color="tab:blue", label="FRR")
    ax.set_xlabel("Tỉ lệ (%) — đánh giá sơ bộ bộ tự thu")
    ax.legend(loc="upper center", bbox_to_anchor=(.5, -.15), ncol=3, fontsize=6)
    ax.grid(axis="x", alpha=.2)
    fig.tight_layout()
    fig.savefig(ROOT / "figures/report/fig_collected_errors.png")
    plt.close(fig)
    summaries = []
    for prefix in ("collected_preliminary", "collected_sensitivity_first"):
        r = json.loads((ROOT / f"results/{prefix}_summary.json").read_text())
        summaries.append({"analysis": prefix, **{k:r[k] for k in ["valid_samples", "logins", "frr_pooled", "far_early_pooled", "far_late_pooled"]}})
    pd.DataFrame(summaries).to_csv(ROOT / "results/collected_sensitivity.csv", index=False)
    print(diagnostic[["participant_id", "frr", "far_early", "far_late", "median_duration_seconds"]].round(3).to_string(index=False))


if __name__ == "__main__":
    main()
