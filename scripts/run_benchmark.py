"""Việc 1.3: so sánh các bộ phát hiện trên CMU Keystroke Benchmark.

Cách chia dữ liệu cho mỗi người dùng u (51 người, mỗi người 400 lần gõ, 8 phiên):
- Học: n lần gõ đầu của u (n <= 200, thuộc phiên 1-4).
- Kiểm tra chủ tài khoản: 200 lần gõ sau của u (phiên 5-8, các ngày sau).
- 50 người còn lại chia ngẫu nhiên (theo seed) thành hai nhóm 25 người:
    nhóm A: mỗi người 10 lần gõ, chỉ Random Forest dùng làm ví dụ kẻ gian khi học;
    nhóm B: làm kẻ gian lúc kiểm tra, theo hai kịch bản:
      - chưa quen tay: 5 lần gõ đầu tiên của mỗi người (giao thức của Killourhy & Maxion);
      - đã quen tay  : 5 lần gõ cuối cùng (phiên 8), như kẻ gian đã luyện gõ mật khẩu.
  Kẻ gian lúc kiểm tra không bao giờ xuất hiện khi học.
- Random Forest chạy hai biến thể, khác nhau ở 10 lần gõ lấy từ nhóm A:
    RandomForest       : 10 lần gõ ngẫu nhiên ở mọi phiên;
    RandomForest-early : 10 lần gõ đầu tiên, cùng mức "chưa quen tay" với kẻ gian lúc kiểm tra.

Chạy:  python scripts/run_benchmark.py
Kết quả: results/benchmark_cmu_*.csv, figures/roc_cmu.png, figures/eer_vs_enrollment.png,
         figures/eer_practiced_impostors.png
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.stdout.reconfigure(encoding="utf-8")  # in tiếng Việt trên console Windows

from keyguard.detectors import DETECTORS  # noqa: E402
from keyguard.evaluation import FAR_GRID, auc, equal_error_rate, tar_on_grid  # noqa: E402
from keyguard.features import FEATURE_NAMES, load_cmu  # noqa: E402

N_TRAIN_MAX = 200
N_IMPOSTOR_TRAIN_PER_SUBJECT = 10
N_IMPOSTOR_TEST_PER_SUBJECT = 5

# (tên hiển thị, lớp trong DETECTORS, khóa dữ liệu kẻ gian khi học hoặc None)
MODELS = [
    ("ScaledManhattan", "ScaledManhattan", None),
    ("OneClassSVM", "OneClassSVM", None),
    ("IsolationForest", "IsolationForest", None),
    ("RandomForest", "RandomForest", "impostor_train"),
    ("RandomForest-early", "RandomForest", "impostor_train_early"),
]
COLORS = {
    "ScaledManhattan": "tab:blue",
    "OneClassSVM": "tab:orange",
    "IsolationForest": "tab:green",
    "RandomForest": "tab:red",
    "RandomForest-early": "tab:purple",
}


def build_splits(df: pd.DataFrame, seed: int) -> dict:
    """Chuẩn bị dữ liệu học/kiểm tra cố định cho từng người dùng."""
    subjects = sorted(df["subject"].unique())
    by_subject = {
        s: g.sort_values(["sessionIndex", "rep"])[FEATURE_NAMES].to_numpy() for s, g in df.groupby("subject")
    }
    splits = {}
    for idx, s in enumerate(subjects):
        rng = np.random.default_rng(seed + idx)
        others = [o for o in subjects if o != s]
        rng.shuffle(others)
        group_a, group_b = others[:25], others[25:]
        imp_train = np.vstack(
            [by_subject[o][rng.choice(len(by_subject[o]), N_IMPOSTOR_TRAIN_PER_SUBJECT, replace=False)] for o in group_a]
        )
        imp_test = np.vstack([by_subject[o][:N_IMPOSTOR_TEST_PER_SUBJECT] for o in group_b])
        imp_test_practiced = np.vstack([by_subject[o][-N_IMPOSTOR_TEST_PER_SUBJECT:] for o in group_b])
        splits[s] = {
            "train": by_subject[s][:N_TRAIN_MAX],
            "genuine_test": by_subject[s][N_TRAIN_MAX:],
            "impostor_train": imp_train,
            "impostor_train_early": np.vstack([by_subject[o][:N_IMPOSTOR_TRAIN_PER_SUBJECT] for o in group_a]),
            "impostor_test": imp_test,
            "impostor_test_practiced": imp_test_practiced,
        }
    return splits


def run(df: pd.DataFrame, n_list: list[int], seed: int):
    splits = build_splits(df, seed)
    rows, roc_curves = [], {}
    for name, det_name, imp_key in MODELS:
        cls = DETECTORS[det_name]
        for n in n_list:
            tars = []
            for s, sp in splits.items():
                det = cls(random_state=seed) if det_name in ("IsolationForest", "RandomForest") else cls()
                X_train = sp["train"][:n]
                t0 = time.perf_counter()
                if det.needs_impostors:
                    det.fit(X_train, sp[imp_key])
                else:
                    det.fit(X_train)
                fit_ms = (time.perf_counter() - t0) * 1000
                t0 = time.perf_counter()
                g = det.score(sp["genuine_test"])
                i = det.score(sp["impostor_test"])
                score_ms = (time.perf_counter() - t0) * 1000 / (len(g) + len(i))
                i_practiced = det.score(sp["impostor_test_practiced"])
                rows.append(
                    {
                        "detector": name,
                        "n_train": n,
                        "subject": s,
                        "eer": equal_error_rate(g, i),
                        "auc": auc(g, i),
                        "eer_practiced": equal_error_rate(g, i_practiced),
                        "fit_ms": fit_ms,
                        "score_ms_per_sample": score_ms,
                    }
                )
                if n == max(n_list):
                    tars.append(tar_on_grid(g, i))
            if tars:
                roc_curves[name] = np.mean(tars, axis=0)
            last = pd.DataFrame(rows).query("detector == @name and n_train == @n")
            print(f"{name:18s} n={n:3d}  EER={last.eer.mean():.3f} ± {last.eer.std():.3f}  AUC={last.auc.mean():.3f}"
                  f"  EER(kẻ gian quen tay)={last.eer_practiced.mean():.3f}")
    return pd.DataFrame(rows), roc_curves


def summarize(per_user: pd.DataFrame) -> pd.DataFrame:
    return (
        per_user.groupby(["detector", "n_train"])
        .agg(
            eer_mean=("eer", "mean"),
            eer_std=("eer", "std"),
            auc_mean=("auc", "mean"),
            auc_std=("auc", "std"),
            eer_practiced_mean=("eer_practiced", "mean"),
            eer_practiced_std=("eer_practiced", "std"),
            fit_ms_mean=("fit_ms", "mean"),
            score_ms_per_sample=("score_ms_per_sample", "mean"),
            n_users=("subject", "count"),
        )
        .reset_index()
    )


def plot(summary: pd.DataFrame, roc_curves: dict, n_max: int, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(5.5, 4.5))
    for name, tar in roc_curves.items():
        ax.plot(FAR_GRID, 1 - tar, color=COLORS[name], label=name)
    ax.plot([0, 1], [0, 1], ":", color="grey", linewidth=0.8, label="FAR = FRR")
    ax.set_xlabel("FAR (tỉ lệ kẻ gian lọt qua)")
    ax.set_ylabel("FRR (tỉ lệ chủ tài khoản bị từ chối)")
    ax.set_xlim(0, 0.5)
    ax.set_ylim(0, 0.5)
    ax.set_title(f"Đánh đổi FAR–FRR trung bình trên 51 người (n = {n_max})")
    ax.grid(alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(out_dir / "roc_cmu.png", dpi=200)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(5.5, 4.5))
    for name, *_ in MODELS:
        g = summary[summary.detector == name]
        ax.errorbar(g["n_train"], g["eer_mean"], yerr=g["eer_std"] / np.sqrt(g["n_users"]), marker="o", capsize=3,
                    color=COLORS[name], label=name)
    ax.set_xscale("log")
    ax.set_xticks(sorted(summary["n_train"].unique()))
    ax.get_xaxis().set_major_formatter(matplotlib.ticker.ScalarFormatter())
    ax.set_xlabel("Số lần gõ khi đăng ký (n)")
    ax.set_ylabel("EER trung bình (± sai số chuẩn)")
    ax.set_title("EER theo số lần gõ khi đăng ký")
    ax.grid(alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(out_dir / "eer_vs_enrollment.png", dpi=200)
    plt.close(fig)

    ns = [n for n in (20, n_max) if n in set(summary["n_train"])]
    fig, axes = plt.subplots(1, len(ns), figsize=(5 * len(ns), 4.2), sharey=True, squeeze=False)
    names = [m[0] for m in MODELS]
    x = np.arange(len(names))
    for ax, n in zip(axes[0], ns):
        g = summary[summary.n_train == n].set_index("detector").loc[names]
        ax.bar(x - 0.2, g["eer_mean"], 0.4, color=[COLORS[k] for k in names], alpha=0.45, label="Kẻ gian chưa quen tay")
        ax.bar(x + 0.2, g["eer_practiced_mean"], 0.4, color=[COLORS[k] for k in names], label="Kẻ gian đã quen tay")
        ax.set_xticks(x, names, rotation=25, ha="right")
        ax.set_title(f"n = {n} lần gõ khi đăng ký")
        ax.grid(axis="y", alpha=0.3)
    axes[0][0].set_ylabel("EER trung bình")
    axes[0][0].legend()
    fig.tight_layout()
    fig.savefig(out_dir / "eer_practiced_impostors.png", dpi=200)
    plt.close(fig)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data", default=str(ROOT / "data/raw/DSL-StrongPasswordData.csv"))
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--n-list", default="5,10,20,50,100,200")
    args = ap.parse_args()

    n_list = [int(v) for v in args.n_list.split(",")]
    df = load_cmu(args.data)
    print(f"Đã đọc {len(df)} lần gõ của {df.subject.nunique()} người.")

    per_user, roc_curves = run(df, n_list, args.seed)
    summary = summarize(per_user)

    (ROOT / "results").mkdir(exist_ok=True)
    per_user.to_csv(ROOT / "results/benchmark_cmu_per_user.csv", index=False)
    summary.to_csv(ROOT / "results/benchmark_cmu_summary.csv", index=False)
    pd.DataFrame({"far": FAR_GRID, **{f"tar_{k}": v for k, v in roc_curves.items()}}).to_csv(
        ROOT / "results/roc_cmu.csv", index=False
    )
    plot(summary, roc_curves, max(n_list), ROOT / "figures")

    print("\nBảng tổng hợp (n lớn nhất):")
    print(summary[summary.n_train == max(n_list)].round(4).to_string(index=False))


if __name__ == "__main__":
    main()
