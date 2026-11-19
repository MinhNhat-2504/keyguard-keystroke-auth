"""Export standalone figures for enrollment and paired contamination studies."""
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

ROOT=Path(__file__).resolve().parents[1]


def main():
    e=json.loads((ROOT/'results/enrollment_study.json').read_text(encoding='utf-8'))
    c=json.loads((ROOT/'results/contamination_study.json').read_text(encoding='utf-8'))
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10})
    fig,ax=plt.subplots(figsize=(9,4.6),layout='constrained')
    names=['Giữ 20\nMean/Std','Giữ 20\nMedian/MAD','Giữ 20\nMedian/IQR',
           'Lọc robust\nMean/Std','Lọc robust\nMedian/MAD','Lọc robust\nMedian/IQR','Chọn qua\nvòng trong']
    rows=[v['overall'] for v in e['variants']]+[e['nested_selected']]
    x=np.arange(len(rows))
    for offset,key,color,label in [(-.18,'far','#007e77','FAR'),(.18,'frr','#365fc0','FRR')]:
        bars=ax.bar(x+offset,[100*r[key] for r in rows],.34,label=label,color=color)
        ax.bar_label(bars,fmt='%.1f',padding=3,fontsize=8)
    ax.set_xticks(x,names,fontsize=8.5);ax.set_ylim(0,85);ax.set_ylabel('Tỷ lệ lỗi (%)')
    ax.set_title('Khảo sát 6 phương án; chọn phương án chỉ qua vòng trong')
    ax.spines[['top','right']].set_visible(False);ax.legend(frameon=False)
    fig.savefig(ROOT/'figures/research/enrollment_quality.png',dpi=200);plt.close(fig)
    fig,axes=plt.subplots(1,2,figsize=(9,4.2),layout='constrained')
    colors={'static':'#64748b','accept':'#365fc0','fallback':'#007e77','verified_only':'#b17d19'}
    names={'static':'Cố định','accept':'Nhận → cập nhật','fallback':'Fallback','verified_only':'Xác minh mọi cập nhật'}
    for s in c['summaries']:
        points=s['arms']['injected']['checkpoints']
        control=s['arms']['control']['checkpoints']
        axes[0].plot([r['genuine_seen'] for r in points],[100*r['probe_accepted']/r['probe_trials'] for r in points],
                     marker='o',label=names[s['policy']],color=colors[s['policy']])
        axes[1].plot([r['genuine_seen'] for r in points],
                     [100*(a['probe_accepted']-b['probe_accepted'])/a['probe_trials'] for a,b in zip(points,control)],
                     marker='o',label=names[s['policy']],color=colors[s['policy']])
    axes[0].set_title('Probe riêng được nhận · có xen mẫu')
    axes[0].set_ylabel('Tỷ lệ trên 150 probe (%)')
    axes[1].set_title('Chênh lệch có xen − không xen')
    axes[1].set_ylabel('Điểm phần trăm');axes[1].axhline(0,color='#aab5c0',linewidth=.8)
    for ax in axes:
        ax.set_xlabel('Số lượt genuine đã xử lý');ax.set_xticks([0,50,100,150,200]);ax.spines[['top','right']].set_visible(False)
    axes[0].legend(fontsize=8,frameon=False)
    fig.savefig(ROOT/'figures/research/contamination_paired.png',dpi=200);plt.close(fig)
    print('Rendered 2 enrollment/update figures')


if __name__=='__main__':main()
