"""Visualize saved CV scores and equivalent limits; never score or fit a model."""
import hashlib
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
from matplotlib import pyplot as plt
from matplotlib.ticker import LogLocator, LogFormatterMathtext

ROOT = Path(__file__).resolve().parents[1]
SOURCE = 'results/usn_oof_diagnostic_20261124.json'
FIGURE = 'figures/usn_normalization_20261124.png'

def main():
    source = json.loads((ROOT / SOURCE).read_text(encoding='utf-8'))
    profiles = [p for p in source['profiles'] if p['phrase'] == 'Ob-dollar-erv3r']
    assert [p['participant_id'] for p in profiles] == [f'participant{i}' for i in range(1,6)]
    plt.rcParams.update({'font.family':'DejaVu Serif', 'font.size':13,
                         'axes.labelsize':13, 'xtick.labelsize':13, 'ytick.labelsize':13,
                         'legend.fontsize':13, 'axes.spines.top':False, 'axes.spines.right':False})
    fig, ax = plt.subplots(figsize=(6.5,4.8))
    points=[]
    for i,p in enumerate(profiles,1):
        x=[i+(j-9.5)*.011 for j in range(20)]
        ax.scatter(x,p['oof_scores'],s=15,facecolors='none',edgecolors='black',linewidths=.7,
                   label='20 điểm OOF / hồ sơ' if i==1 else None,zorder=3)
        ax.scatter([i],[p['equivalent_raw_score_limit']],s=65,marker='D',color='black',
                   label='Ngưỡng thô tương đương' if i==1 else None,zorder=4)
        points.append({'profile':f'P{i}','oof_scores':p['oof_scores'],
                       'equivalent_raw_score_limit':p['equivalent_raw_score_limit']})
    ax.set_yscale('log');ax.set_ylim(10,3e6)
    ax.set_xlim(.55,5.45);ax.set_xticks(range(1,6),[f'P{i}' for i in range(1,6)])
    ax.set_xlabel('Hồ sơ người–câu Ob$erv3r')
    ax.set_ylabel('Điểm thô (trục logarit)')
    ax.yaxis.set_major_locator(LogLocator(base=10,numticks=7))
    ax.yaxis.set_major_formatter(LogFormatterMathtext())
    ax.grid(axis='y',which='major',color='.85',linewidth=.6)
    ax.legend(loc='upper center',bbox_to_anchor=(.5,1.23),frameon=False)
    fig.subplots_adjust(left=.18,right=.98,bottom=.17,top=.78)
    output=ROOT/FIGURE;output.parent.mkdir(parents=True,exist_ok=True)
    fig.savefig(output,dpi=220,facecolor='white');plt.close(fig)
    script='scripts/plot_usn_normalization_20261124.py'
    record={'scope':'Visualization of saved enrollment CV scores; no model fit, new test or correction',
            'phrase':'Ob-dollar-erv3r','profile_count':5,'oof_point_count':100,
            'logarithmic_y_axis':True,'threshold_unchanged':True,
            'font_size_pt_at_6_5_inch_width':13,'figure':FIGURE,
            'figure_sha256':hashlib.sha256(output.read_bytes()).hexdigest(),
            'source_sha256':{n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in (SOURCE,script)},
            'plotted_points':points}
    (ROOT/'results/usn_normalization_figure_20261124.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in record.items() if k!='plotted_points'}))

if __name__=='__main__':main()
