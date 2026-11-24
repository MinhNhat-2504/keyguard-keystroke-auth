"""Check this submission's saved sources using Python standard library only."""
import csv
from fractions import Fraction
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


def check_table_font(xml, points):
    for table in xml.findall('.//w:tbl',NS):
        for run in table.findall('.//w:r',NS):
            if not ''.join(run.itertext()).strip():continue
            size=run.find('w:rPr/w:sz',NS)
            require(size is not None and size.get('{'+NS['w']+'}val')==str(points*2),'Primary report table font differs')

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
    require(len(xml.findall('.//w:tbl',NS))==manifest.get('primary_report_tables',34),'Report table count differs')
    if manifest.get('body_font_pt'):check_table_font(xml,manifest['body_font_pt'])
    refs=[int(re.match(r'^\[(\d+)\]',p)[1]) for p in paragraphs if re.match(r'^\[\d+\]',p)]
    require(refs==list(range(1,manifest.get('reference_count',18)+1)),'Bibliography order differs')
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
    if manifest.get('enrollment_selection_study'):
        study=json.loads((root/manifest['enrollment_selection_study']).read_text(encoding='utf-8'))
        require(not study['continuation_gate_met'] and not study['new_source_scored'],'Selection-study scope differs')
        for dataset in study['datasets'].values():
            for arm in dataset['arms'].values():
                rows=arm['accounts'];m=arm['metrics']
                for metric,num,den in [('far','impostor_accepted','impostor_trials'),('frr','genuine_rejected','genuine_trials')]:
                    require(sum(r[num] for r in rows)==m[num] and sum(r[den] for r in rows)==m[den],'Selection counts differ')
                    macro=sum((Fraction(r[num],r[den]) for r in rows),Fraction())/len(rows)
                    require(abs(float(macro)-m['macro_'+metric])<1e-12,'Selection macro differs')
                require(all(r['stored_samples']==10 and len(set(r['selected_positions_1based']))==10 for r in rows),'Selection budget differs')
            require(not dataset['continuation_gate_met'],'Selection continuation status differs')
    if manifest.get('usn_transfer_study'):
        usn=json.loads((root/manifest['usn_transfer_study']).read_text(encoding='utf-8'))
        require(usn['threshold']==cfg['threshold'] and usn['source_specific_tuning'] is False,'USN threshold/protocol differs')
        overall=usn['overall'];by_phrase=usn['by_phrase']
        require((usn['unique_genuine_people'],usn['account_phrase_profiles'],usn['unique_attack_rows'])==(5,30,2042),'USN units differ')
        require(not usn['multi_day_validation'] and not usn['candidate_selection_tested'],'USN scope differs')
        for key in ('genuine_trials','genuine_rejected','impostor_trials','impostor_accepted'):
            require(sum(v[key] for v in by_phrase.values())==overall[key],'USN pooled count differs')
        require((overall['genuine_trials'],overall['genuine_rejected'],overall['impostor_trials'],overall['impostor_accepted'])==(5400,1772,10210,1394),'USN counts differ')
    if manifest.get('usn_diagnostics'):
        diagnostic=json.loads((root/manifest['usn_diagnostics']).read_text(encoding='utf-8'))
        require(len(diagnostic['profiles'])==30 and diagnostic['all_30_saved_cv_summaries_reproduced'],'USN CV diagnostic differs')
        sensitivity=json.loads((root/'research/results/usn_sensitivity_20261124.json').read_text(encoding='utf-8'))
        for artifact in (diagnostic,sensitivity):
            for name,h in artifact['source_sha256'].items():require(hashlib.sha256((root/'research'/name).read_bytes()).hexdigest()==h,'USN diagnostic source changed: '+name)
        bounds=sensitivity['results']['excluded_attack_decision_bounds']
        require(bounds['raw_row_scenario_trials']==10345 and bounds['additional_unknown_decisions']==135,'USN sensitivity denominator differs')
    if manifest.get('calibration_preflight'):
        preflight=json.loads((root/manifest['calibration_preflight']).read_text(encoding='utf-8'))
        lock_path=root/'research/results/calibration_preflight_20261124_freeze.json'
        lock=json.loads(lock_path.read_text(encoding='utf-8'))
        require(hashlib.sha256(lock_path.read_bytes()).hexdigest()==preflight['freeze_sha256'],'Preflight lock changed')
        for name,h in lock['source_sha256'].items():
            require(hashlib.sha256((root/'research'/name).read_bytes()).hexdigest()==h,'Preflight source changed: '+name)
        tests=(root/'research/results/calibration_preflight_20261124_synthetic_tests.json').read_bytes()
        require(hashlib.sha256(tests).hexdigest()==lock['synthetic_tests_sha256'],'Preflight tests record changed')
        require(len(preflight['profiles'])==preflight['profile_count']==30,'Preflight profile count differs')
        require(sum(p['review_required'] for p in preflight['profiles'])==preflight['review_required_count'],'Preflight warning count differs')
        require(preflight['enrollment_rows_parsed']==600 and preflight['test_rows_parsed']==0,'Preflight scope differs')
        require(not preflight['production_changed'] and not preflight['test_decisions_changed'],'Preflight deployment/performance overclaim')
    if manifest.get('usn_explanation_figure'):
        figure=json.loads((root/manifest['usn_explanation_figure']).read_text(encoding='utf-8'))
        diagnostic=json.loads((root/manifest['usn_diagnostics']).read_text(encoding='utf-8'))
        profiles=[p for p in diagnostic['profiles'] if p['phrase']==figure['phrase']]
        require(len(profiles)==len(figure['plotted_points'])==5,'Figure profile count differs')
        for source,plotted in zip(profiles,figure['plotted_points']):
            require(source['oof_scores']==plotted['oof_scores'] and len(plotted['oof_scores'])==20,'Figure OOF points differ')
            require(source['equivalent_raw_score_limit']==plotted['equivalent_raw_score_limit'],'Figure equivalent limit differs')
        for name,h in figure['source_sha256'].items():
            require(hashlib.sha256((root/'research'/name).read_bytes()).hexdigest()==h,'Figure source changed: '+name)
        image_hash=hashlib.sha256((root/'research'/figure['figure']).read_bytes()).hexdigest()
        require(image_hash==figure['figure_sha256'],'Figure hash differs')
        with zipfile.ZipFile(current) as archive:
            image_hashes=[hashlib.sha256(archive.read(n)).hexdigest() for n in archive.namelist() if n.startswith('word/media/')]
        require(image_hash in image_hashes,'Source figure missing from report')
    return {'status':'passed','manifest_files':len(manifest['files']),'report_referenced_files':len(paths),'missing_report_references':0,'native_equations':7,'report_tables':len(xml.findall('.//w:tbl',NS)),'references':len(refs),'self_collected_samples':597,'synthesis_rows':35,'uncertainty_comparisons':5,'enrollment_selection_reconciled':bool(manifest.get('enrollment_selection_study')),'usn_transfer_reconciled':bool(manifest.get('usn_transfer_study')),'usn_diagnostics_reconciled':bool(manifest.get('usn_diagnostics')),'scope':'Integrity and reconciliation of stored sources; not a model rerun or production acceptance'}

if __name__=='__main__':
    try:print(json.dumps(check(),ensure_ascii=True))
    except Exception as exc:print('FAIL: '+str(exc));sys.exit(1)
