"""Plots from the frozen external result; never train/select models here."""
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

ROOT=Path(__file__).resolve().parents[1]


def main():
    data=json.loads((ROOT/'results/external_validation.json').read_text(encoding='utf-8'))
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11})
    fig,axes=plt.subplots(1,2,figsize=(9,4.5),layout='constrained')
    x=np.arange(4)
    names=['Baseline','Lọc cứng\nchọn từ dev','Trọng số mềm\nchọn từ dev','Chọn cả9\ntừ dev']
    for ax,metric,color in zip(axes,('far','frr'),('#007e77','#365fc0')):
        values=[100*r['overall'][metric] for r in data['families']]
        bars=ax.bar(x,values,color=color,alpha=.85)
        ax.bar_label(bars,fmt='%.2f',padding=3,fontsize=10)
        ax.set_xticks(x,names,fontsize=9);ax.set_ylabel(metric.upper()+' (%)');ax.set_ylim(0,max(values)*1.22)
        ax.spines[['top','right']].set_visible(False)
    fig.suptitle('KeyRecs: ngưỡng/lựa chọn từ dev phiên1, test33 mã phiên2',fontsize=11)
    fig.savefig(ROOT/'figures/research/external_validation.png',dpi=200);plt.close(fig)
    print('Rendered external verification figure')


if __name__=='__main__':main()
