"""Research figures: dependent-split variation and CMU ordered-session errors."""
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

ROOT=Path(__file__).resolve().parents[1]


def main():
    stability=json.loads((ROOT/'results/stability_study.json').read_text(encoding='utf-8'))
    adaptation=json.loads((ROOT/'results/session_adaptation.json').read_text(encoding='utf-8'))
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11})
    fig,axes=plt.subplots(1,2,figsize=(9,4.5),layout='constrained')
    labels=['Baseline','Lọc cứng\nchọn từ dev','Trọng số mềm\nchọn từ dev','Chọn cả 9\ntừ dev']
    for ax,key,title,color in zip(axes,('far','frr'),('FAR (%)','FRR (%)'),('#007e77','#365fc0')):
        means=[100*r[key]['mean'] for r in stability['family_summaries']]
        sd=[100*r[key]['std_across_splits'] for r in stability['family_summaries']]
        bars=ax.bar(np.arange(4),means,yerr=sd,capsize=4,color=color,alpha=.85)
        ax.set_xticks(np.arange(4),labels,fontsize=9);ax.set_ylabel(title)
        ax.set_ylim(0,max(np.array(means)+sd)*1.28)
        for j,(mean,error) in enumerate(zip(means,sd)):ax.text(j,mean+error+ax.get_ylim()[1]*.035,f'{mean:.2f}',ha='center',fontsize=10)
        ax.spines[['top','right']].set_visible(False)
    fig.suptitle('Trung bình ± SD trên 10 cách chia phụ thuộc, không phải khoảng tin cậy',fontsize=11)
    fig.savefig(ROOT/'figures/research/soft_weight_stability.png',dpi=200);plt.close(fig)
    names={'static':'Cố định','window50':'Cửa sổ 50','decay20':'Cửa sổ 50 + bán rã 20'}
    colors={'static':'#64748b','window50':'#365fc0','decay20':'#007e77'}
    fig,axes=plt.subplots(1,2,figsize=(9,4.5),layout='constrained')
    for method in adaptation['methods']:
        rows=method['partitions']['test']['sessions']
        for ax,key in zip(axes,('far','frr')):
            ax.plot([r['session'] for r in rows],[100*r[key] for r in rows],marker='o',label=names[method['id']],color=colors[method['id']])
    for ax,label in zip(axes,('FAR · probe đầu phiên (%)','FRR · genuine cần xác minh (%)')):
        ax.set_xticks(range(1,9));ax.set_xlabel('Phiên CMU');ax.set_ylabel(label);ax.spines[['top','right']].set_visible(False)
    axes[0].legend(frameon=False,fontsize=9)
    fig.suptitle('Ngưỡng chọn riêng trên dev; mọi genuine giả định được xác minh trước cập nhật',fontsize=10.5)
    fig.savefig(ROOT/'figures/research/session_adaptation.png',dpi=200);plt.close(fig)
    print('Rendered 2 soft-weight/session figures')


if __name__=='__main__':main()
