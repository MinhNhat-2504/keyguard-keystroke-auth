"""Render publication figures from checked research aggregates, no rerun models."""
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]


def main():
    data = json.loads((ROOT / 'results/research_summary.json').read_text(encoding='utf-8'))
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 10})
    fig, ax = plt.subplots(figsize=(8.5, 3.6), layout='constrained')
    keys = ('baseline_fixed', 'baseline_recalibrated', 'nested_selected')
    names = ['Ngưỡng CMU\ngiữ nguyên', 'Hiệu chỉnh ngưỡng\nbaseline', 'Chọn phương án\nqua vòng trong']
    x = np.arange(3)
    for offset, metric, label, color in [(-.18, 'far', 'FAR', '#007e77'), (.18, 'frr', 'FRR', '#365fc0')]:
        values = [100 * data[k][metric] for k in keys]
        bars = ax.bar(x + offset, values, .34, label=label, color=color)
        ax.bar_label(bars, fmt='%.2f%%', padding=3, fontsize=9)
    ax.set_xticks(x, names)
    ax.set_ylabel('Tỷ lệ lỗi (%)')
    ax.set_ylim(0, 80)
    ax.set_title('Cùng protocol: hồ sơ cố định, 297 genuine / 600 impostor')
    ax.legend(frameon=False)
    ax.spines[['top', 'right']].set_visible(False)
    out = ROOT / 'figures/research'
    out.mkdir(exist_ok=True)
    fig.savefig(out / 'pipeline_comparison.png', dpi=200)
    plt.close(fig)
    fig, ax = plt.subplots(figsize=(9, 5.6), layout='constrained')
    base = data['variants'][:12]
    x = np.arange(4)
    for j, (normalization, title, color) in enumerate([
            ('raw', 'Thời gian gốc', '#007e77'),
            ('duration', 'Chia tổng thời gian', '#365fc0'),
            ('median_hold', 'Chia trung vị giữ phím', '#d49b38')]):
        values = [100 * next(v for v in base if v['features'] == f and v['normalization'] == normalization)['mean_fold_eer']
                  for f in ('all', 'H', 'DD', 'UD')]
        bars = ax.bar(x + (j - 1) * .24, values, .23, color=color, label=title)
        ax.bar_label(bars, fmt='%.1f', padding=2, fontsize=8)
    ax.set_xticks(x, ['31 đặc trưng', 'H · 11 chiều', 'DD · 10 chiều', 'UD · 10 chiều'])
    ax.set_ylabel('EER trung bình 3 vòng (%)')
    ax.set_ylim(0, 42)
    ax.set_title('Scaled Manhattan: khảo sát đặc trưng và chuẩn hóa')
    ax.legend(frameon=False, loc='upper left')
    ax.spines[['top', 'right']].set_visible(False)
    fig.savefig(out / 'feature_ablation.png', dpi=200)
    plt.close(fig)
    print('Rendered 2 research figures')


if __name__ == '__main__':
    main()
