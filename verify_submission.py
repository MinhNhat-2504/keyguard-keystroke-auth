"""Check this submission's saved sources using Python standard library only."""
import csv
import hashlib
import io
import json
from pathlib import Path,PurePosixPath
import re
import sys
import xml.etree.ElementTree as ET
import zipfile

ROOT=Path(__file__).resolve().parent
NS={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main','m':'http://schemas.openxmlformats.org/officeDocument/2006/math'}

def require(ok,message):
    if not ok:raise ValueError(message)

def document(path):
    with zipfile.ZipFile(path) as z:return ET.fromstring(z.read('word/document.xml'))

def paragraph_text(xml):
    return [''.join(n.text or '' for n in p.iter('{'+NS['w']+'}t')) for p in xml.iter('{'+NS['w']+'}p')]

def referenced_files(paragraphs):
    pattern=r'(?<![\w/])(?:research/|web/)?(?:docs|results|scripts|keyguard|models|explorer|data)/[A-Za-z0-9_./-]+\.[A-Za-z0-9_]+'
    names=set()
    for text in paragraphs:
        for name in re.findall(pattern,text):
            alias=re.fullmatch(r'(.+)\.(json|csv)/\.(json|csv)',name)
            if alias:
                names.add(alias[1]+'.'+alias[2]);names.add(alias[1]+'.'+alias[3])
            else:names.add(name)
    return sorted(names)

def check(root=ROOT):
    root=Path(root);manifest=json.loads((root/'SOURCE_MANIFEST.json').read_text(encoding='utf-8'))
    for name,expected in manifest['files'].items():
        p=PurePosixPath(name)
        require(not p.is_absolute() and '..' not in p.parts and ':' not in name and '\\' not in name,'Unsafe manifest path')
        require(not any(x in name.lower() for x in ('.private-backup','.storage-test/','.env','/data/collected/','consent/','cham_diem')),'Private file in manifest')
        require((root/name).resolve().is_relative_to(root.resolve()),'Outside source tree')
        require(hashlib.sha256((root/name).read_bytes()).hexdigest()==expected,'Hash differs: '+name)
    primary=manifest.get('primary_report','reports/KeyGuard_BaoCao_Nop_20261120.docx')
    require(primary in manifest['files'],'Primary report absent from manifest')
    current=root/primary;xml=document(current);paragraphs=paragraph_text(xml)
    require(len(xml.findall('.//m:oMath',NS))==7,'Native equation count differs')
    require(len(xml.findall('.//w:tbl',NS))==34,'Report table count differs')
    refs=[int(re.match(r'^\[(\d+)\]',p)[1]) for p in paragraphs if re.match(r'^\[\d+\]',p)]
    require(refs==list(range(1,19)),'Bibliography order differs')
    paths=referenced_files(paragraphs);missing=[]
    for n in paths:
        if not any((root/base/n).is_file() for base in ('','research','web')):missing.append(n)
    require(not missing,'Missing report references: '+', '.join(missing))
    summary=json.loads((root/'research/results/collected_preliminary_summary.json').read_text(encoding='utf-8-sig'))
    require((summary['valid_samples'],summary['logins'],summary['genuine_rejected'])==(597,297,49),'Self-collected counts differ')
    require((summary['impostor_accepted_early'],summary['impostor_accepted_late'],summary['impostor_trials_early'],summary['impostor_trials_late'])==(284,331,1050,1050),'Impostor counts differ')
    cfg=json.loads((root/'research/models/model_config.json').read_text(encoding='utf-8-sig'))
    require(hashlib.sha256(json.dumps(cfg,sort_keys=True).encode()).hexdigest()==summary['config_sha256'],'Canonical config hash differs')
    with (root/'research/results/threshold_selection.csv').open(newline='',encoding='utf-8-sig') as stream:rows=list(csv.DictReader(stream))
    fallback=next(r for r in rows if r['policy']=='fallback')
    require(float(fallback['threshold'])==cfg['threshold']==summary['threshold'],'Saved threshold differs')
    for n,h in manifest.get('web_runtime_sha256',{}).items():require(hashlib.sha256((root/'web'/n).read_bytes()).hexdigest()==h,'Reviewed web runtime changed: '+n)
    synthesis=json.loads((root/'research/results/research_decision_20261115.json').read_text(encoding='utf-8-sig'))
    with (root/'research/results/research_decision_20261115.csv').open(encoding='utf-8-sig',newline='') as stream:rows=list(csv.DictReader(stream))
    require(len(rows)==len(synthesis['rows'])==35,'Synthesis count differs')
    for a,b in zip(rows,synthesis['rows']):require(all(a[k]==('' if v is None else str(v)) for k,v in b.items()),'Synthesis JSON/CSV differ')
    uncertainty=json.loads((root/'research/results/account_uncertainty_20261115.json').read_text(encoding='utf-8-sig'))
    require(len(uncertainty['comparisons'])==5,'Uncertainty comparisons differ')
    for artifact in (synthesis,uncertainty):
        for n,h in artifact['source_sha256'].items():require(hashlib.sha256((root/'research'/n).read_bytes()).hexdigest()==h,'Saved source differs: '+n)
    for target in re.findall(r'\]\(([^)]+)\)',(root/'README.md').read_text(encoding='utf-8')):
        if target.startswith(('https:','http:','#')):continue
        require((root/target.split('#',1)[0]).exists(),'README link missing: '+target)
    return {'status':'passed','manifest_files':len(manifest['files']),'report_referenced_files':len(paths),'missing_report_references':0,'native_equations':7,'report_tables':34,'references':18,'self_collected_samples':597,'synthesis_rows':35,'uncertainty_comparisons':5,'scope':'Integrity and reconciliation of stored sources; not a model rerun or production acceptance'}

if __name__=='__main__':
    try:print(json.dumps(check(),ensure_ascii=True))
    except Exception as exc:print('FAIL: '+str(exc));sys.exit(1)
