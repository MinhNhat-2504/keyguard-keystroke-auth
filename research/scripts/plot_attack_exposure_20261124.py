"""Plot the two saved target-count histograms, keeping all zero bins visible."""
import hashlib,json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
ROOT=Path(__file__).resolve().parents[1]
def main():
    for p in (ROOT/'report/preview/final-audit-20261122/fonts').glob('times*.ttf'):font_manager.fontManager.addfont(str(p))
    plt.rcParams.update({'font.family':'Times New Roman','font.size':14,'axes.labelsize':14,'legend.fontsize':13})
    source=ROOT/'results/attack_exposure_20261124_results.json'
    r=json.loads(source.read_text(encoding='utf-8'))['overall']
    fig,ax=plt.subplots(figsize=(6.5,3.3));x=list(range(6));width=.36
    for label,offset,color,key in [('Trước',-width/2,'#607786','before'),('Sau',width/2,'#9b6c3d','after')]:
        vals=r['targets_passed_histogram_'+key]
        bars=ax.bar([v+offset for v in x],vals,width,label=label,color=color)
        ax.bar_label(bars,labels=[str(v) for v in vals],padding=3 if key=='before' else 15,fontsize=13)
    ax.set_xticks(x);ax.set_ylim(0,1950);ax.set_yticks([0,500,1000,1500])
    ax.set_xlabel('Số hồ sơ nhận trực tiếp một mẫu giả mạo')
    ax.set_ylabel('Số mẫu khác nhau');ax.legend(frameon=False,loc='upper right')
    ax.spines[['top','right']].set_visible(False);fig.tight_layout(pad=.6)
    target=ROOT/'figures/attack_exposure_20261124.png';fig.savefig(target,dpi=220,facecolor='white');plt.close(fig)
    record=dict(figure='figures/'+target.name,figure_sha256=hashlib.sha256(target.read_bytes()).hexdigest(),
                result_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                before=r['targets_passed_histogram_before'],after=r['targets_passed_histogram_after'])
    (ROOT/'results/attack_exposure_figure_20261124.json').write_bytes((json.dumps(record,indent=2)+'\n').encode('utf-8'))
    print(json.dumps(record))
if __name__=='__main__':main()
