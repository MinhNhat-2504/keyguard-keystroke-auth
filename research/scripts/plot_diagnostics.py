"""Plot descriptive account errors, keeping all original decisions unchanged."""
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]


def main():
    data = json.loads((ROOT / 'results/research_diagnostics.json').read_text(encoding='utf-8'))
    keys = ('baseline_fixed', 'baseline_recalibrated', 'nested_selected')
    names = ['Ngưỡng\nCMU', 'Hiệu chỉnh\nbaseline', 'Chọn qua\nvòng trong']
    reference = data['pipelines']['baseline_recalibrated']['accounts']
    ids = [a['participant_id'] for a in reference]
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 11})
    fig, axes = plt.subplots(1, 2, figsize=(8.5, 7.3), layout='constrained')
    for ax, metric, title, cmap in zip(axes, ('far', 'frr'), ('FAR theo tài khoản (%)', 'FRR theo tài khoản (%)'), ('OrRd', 'Blues')):
        values = np.array([[100 * next(a for a in data['pipelines'][key]['accounts']
                                       if a['participant_id'] == pid)[metric] for key in keys] for pid in ids])
        image = ax.imshow(values, cmap=cmap, vmin=0, vmax=100, aspect='auto')
        ax.set_xticks(range(3), names, fontsize=9.5)
        ax.set_yticks(range(len(ids)), [f"{a['participant_id']} · vòng {a['fold']}" for a in reference])
        ax.set_title(title)
        for i in range(len(ids)):
            for j in range(3):
                ax.text(j, i, f'{values[i,j]:.1f}', ha='center', va='center',
                        color='white' if values[i,j] > 60 else '#17283d', fontsize=10.5)
        fig.colorbar(image, ax=ax, fraction=.04, pad=.02)
    path = ROOT / 'figures/research/account_error_heatmap.png'
    fig.savefig(path, dpi=200)
    plt.close(fig)
    print('Rendered account error heatmap')


if __name__ == '__main__':
    main()
