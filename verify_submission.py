"""Check this submission's saved sources using Python standard library only."""
import csv
from fractions import Fraction
import hashlib
import io
import json
import math
import statistics
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
    require(len(xml.findall('.//m:oMath',NS))==manifest.get('native_equations',7),'Native equation count differs')
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
    if manifest.get('calibration_order_audit'):
        ordering=json.loads((root/manifest['calibration_order_audit']).read_text(encoding='utf-8'))
        freeze_path=root/'research/results/calibration_order_20261124_freeze.json'
        freeze=json.loads(freeze_path.read_text(encoding='utf-8'))
        require(hashlib.sha256(freeze_path.read_bytes()).hexdigest()==ordering['freeze_sha256'],'Order freeze changed')
        for name,h in freeze['source_sha256'].items():
            require(hashlib.sha256((root/'research'/name).read_bytes()).hexdigest()==h,'Order source changed: '+name)
        tests=root/'research/results/calibration_order_20261124_synthetic_tests.json'
        require(hashlib.sha256(tests.read_bytes()).hexdigest()==freeze['tests_sha256'],'Order test record changed')
        require(len(ordering['profiles'])==ordering['profile_count']==132,'Order profile count differs')
        require(sum(len(p['cases']) for p in ordering['profiles'])==ordering['ordering_case_count']==660,'Order case count differs')
        for p in ordering['profiles']:
            for case in p['cases']:
                require(sorted(case['indices_0based'])==list(range(20)),'Order sample permutation differs')
                require(math.isclose(case['cv_center']+ordering['threshold']*case['cv_scale'],case['raw_acceptance_limit'],rel_tol=1e-12),'Order equivalent limit differs')
        require(ordering['test_decisions_scored']==0 and not ordering['threshold_or_policy_changed'],'Order audit scope differs')
    for result_key,prefix in [('preflight_dev_audit','preflight_dev_audit_20261124_'),('usn_residual_diagnostic','usn_residual_diagnostic_20261124_')]:
        if not manifest.get(result_key):continue
        audit_result=json.loads((root/manifest[result_key]).read_text(encoding='utf-8'))
        freeze_path=root/'research/results'/(prefix+'freeze.json')
        lock=json.loads(freeze_path.read_text(encoding='utf-8'))
        require(hashlib.sha256(freeze_path.read_bytes()).hexdigest()==audit_result['freeze_sha256'],'Follow-up freeze changed')
        for name,h in lock['source_sha256'].items():
            require(hashlib.sha256((root/'research'/name).read_bytes()).hexdigest()==h,'Follow-up source changed: '+name)
        tests=root/'research/results'/(prefix+'synthetic_tests.json')
        require(hashlib.sha256(tests.read_bytes()).hexdigest()==lock['tests_sha256'],'Follow-up test record changed')
        if result_key=='preflight_dev_audit':
            require(audit_result['profile_count']==102 and audit_result['enrollment_rows_parsed']==2040,'DEV enrollment count differs')
            require(audit_result['test_decisions_scored']==0 and not audit_result['threshold_changed'],'DEV audit scope differs')
            for dataset,source in zip(audit_result['datasets'],lock['datasets']):
                require({p['participant_id'] for p in dataset['profiles']}==set(source['dev_ids']),'DEV identities differ')
                require(not set(source['dev_ids'])&set(source['excluded_test_ids']),'DEV/TEST identity overlap')
                require(sum(p['review_required'] for p in dataset['profiles'])==dataset['review_required_count'],'DEV warning count differs')
        else:
            require(len(audit_result['accounts'])==30 and audit_result['decisions_count']==15610,'Residual scope differs')
            require(sum(a['attack_behavioral_passes_after_guard'] for a in audit_result['accounts'])==audit_result['remaining_attack_behavioral_passes']==374,'Residual count differs')
            for a in audit_result['accounts']:
                require(a['auc_twice_pair_count']==2*a['genuine_trials']*a['attack_trials'],'AUC denominator differs')
                require(a['auc']==a['auc_twice_wins_plus_ties']/a['auc_twice_pair_count'],'AUC fraction differs')
            require(not audit_result['new_threshold_chosen'] and not audit_result['model_fit_performed'],'Residual tuning overclaim')
    if manifest.get('attack_exposure'):
        exposure_path=root/manifest['attack_exposure']
        exposure=json.loads(exposure_path.read_text(encoding='utf-8'))
        lock_path=root/'research/results/attack_exposure_20261124_freeze.json'
        lock=json.loads(lock_path.read_text(encoding='utf-8'))
        require(hashlib.sha256(lock_path.read_bytes()).hexdigest()==exposure['freeze_sha256'],'Exposure lock differs')
        for name,h in lock['source_sha256'].items():
            require(hashlib.sha256((root/'research'/name).read_bytes()).hexdigest()==h,'Exposure source changed: '+name)
        test_path=root/'research/results/attack_exposure_20261124_synthetic_tests.json'
        require(hashlib.sha256(test_path.read_bytes()).hexdigest()==lock['tests_sha256'],'Exposure tests changed')
        require(exposure['target_count_per_sample']==5 and len(exposure['by_phrase'])==6,'Exposure matrix scope differs')
        for row in [exposure['overall']]+exposure['by_phrase']:
            require(row['target_decisions']==5*row['distinct_attack_samples'],'Exposure denominator differs')
            for arm in ('before','after'):
                h=row['targets_passed_histogram_'+arm]
                require(len(h)==6 and sum(h)==row['distinct_attack_samples'],'Exposure histogram differs')
                require(sum(i*n for i,n in enumerate(h))==row['accepted_target_decisions_'+arm],'Exposure decision count differs')
                require(sum(h[1:])==row['samples_any_target_'+arm],'Exposure union count differs')
                require(row['samples_any_target_rate_'+arm]==sum(h[1:])/sum(h),'Exposure union rate differs')
        require((exposure['overall']['samples_any_target_before'],exposure['overall']['samples_any_target_after'])==(686,349),'Exposure union totals differ')
        figure=json.loads((root/'research/results/attack_exposure_figure_20261124.json').read_text(encoding='utf-8'))
        require(hashlib.sha256(exposure_path.read_bytes()).hexdigest()==figure['result_sha256'],'Exposure figure source differs')
        for arm in ('before','after'):require(figure[arm]==exposure['overall']['targets_passed_histogram_'+arm],'Exposure plotted values differ')
        image_hash=hashlib.sha256((root/'research'/figure['figure']).read_bytes()).hexdigest()
        require(image_hash==figure['figure_sha256'],'Exposure figure hash differs')
        with zipfile.ZipFile(current) as archive:
            images=[hashlib.sha256(archive.read(n)).hexdigest() for n in archive.namelist() if n.startswith('word/media/')]
        require(image_hash in images,'Exposure figure missing from report')
        require(not exposure['model_fit_performed'] and not exposure['new_threshold_chosen'],'Exposure scope overclaim')
    if manifest.get('group_sensitivity'):
        grouped=json.loads((root/manifest['group_sensitivity']).read_text(encoding='utf-8'))
        lock_path=root/'research/results/group_sensitivity_20261124_freeze.json'
        lock=json.loads(lock_path.read_text(encoding='utf-8'))
        require(hashlib.sha256(lock_path.read_bytes()).hexdigest()==grouped['freeze_sha256'],'Group lock changed')
        for name,h in lock['source_sha256'].items():
            require(hashlib.sha256((root/'research'/name).read_bytes()).hexdigest()==h,'Group source changed: '+name)
        tests=root/'research/results/group_sensitivity_20261124_synthetic_tests.json'
        require(hashlib.sha256(tests.read_bytes()).hexdigest()==lock['tests_sha256'],'Group tests changed')
        require(len(grouped['leave_one_target_out'])==5 and len(grouped['leave_one_phrase_out'])==6,'Group deletion scope differs')
        require(not grouped['model_fit_performed'] and not grouped['new_threshold_chosen'],'Group analysis tuning overclaim')
        routing=json.loads((root/'research/results/calibration_routing_20261124_results.json').read_text(encoding='utf-8'))
        keys=('genuine_trials','attack_trials','genuine_additional_verification_before','genuine_additional_verification_after','attack_behavioral_before','attack_behavioral_after')
        for axis in ('target','phrase'):
            require({r['excluded'] for r in grouped['leave_one_'+axis+'_out']}=={r[axis] for r in routing['profiles']},'Group omission differs')
            for row in grouped['leave_one_'+axis+'_out']:
                subset=[r for r in routing['profiles'] if r[axis]!=row['excluded']]
                for key in keys:require(row[key]==sum(r[key] for r in subset),'Group subtotal differs')
        tables=xml.findall('.//w:tbl',NS)
        rows=tables[38].findall('w:tr',NS)
        require(len(rows)==7,'Group table rows differ')
        for saved,row in zip(grouped['leave_one_phrase_out'],rows[1:]):
            cells=row.findall('w:tc',NS)
            for ci,(key,den) in enumerate((('attack_behavioral_before','attack_trials'),('attack_behavioral_after','attack_trials'),('genuine_additional_verification_before','genuine_trials'),('genuine_additional_verification_after','genuine_trials')),1):
                text=''.join(n.text or '' for n in cells[ci].iter('{'+NS['w']+'}t'))
                require(text==f"{saved[key]}/{saved[den]}",'Group report number differs')
    if manifest.get('calibration_influence'):
        influence=json.loads((root/manifest['calibration_influence']).read_text(encoding='utf-8'))
        for name,h in influence['source_sha256'].items():
            require(hashlib.sha256((root/'research'/name).read_bytes()).hexdigest()==h,'Influence source changed: '+name)
        sample=influence['example'];values=[0.]*(sample['n']-1)+[sample['outlier']]
        require(math.isclose(statistics.mean(values),sample['center'],rel_tol=1e-14),'Illustrative mean differs')
        require(math.isclose(statistics.pstdev(values),sample['population_sd'],rel_tol=1e-14),'Illustrative population SD differs')
        require(math.isclose(sample['center']+sample['threshold']*sample['used_scale'],sample['raw_acceptance_limit'],rel_tol=1e-14),'Illustrative limit differs')
        for node,texts in zip(xml.findall('.//m:oMath',NS)[7:],influence['equation_text_nodes']):
            require([n.text for n in node.findall('.//m:t',NS)]==texts,'Illustrative native equation differs')
    if manifest.get('calibration_routing'):
        routing=json.loads((root/manifest['calibration_routing']).read_text(encoding='utf-8'))
        lock_path=root/'research/results/calibration_routing_20261124_freeze.json'
        lock=json.loads(lock_path.read_text(encoding='utf-8'))
        require(hashlib.sha256(lock_path.read_bytes()).hexdigest()==routing['freeze_sha256'],'Routing lock changed')
        for name,h in lock['source_sha256'].items():
            require(hashlib.sha256((root/'research'/name).read_bytes()).hexdigest()==h,'Routing source changed: '+name)
        tests=(root/'research/results/calibration_routing_20261124_synthetic_tests.json').read_bytes()
        require(hashlib.sha256(tests).hexdigest()==lock['synthetic_tests_sha256'],'Routing test record changed')
        require(len(routing['profiles'])==routing['profile_count']==30,'Routing profile count differs')
        for role,total in [('genuine',5400),('attack',10210)]:
            require(sum(p[role+'_trials'] for p in routing['profiles'])==routing['overall'][role+'_trials']==total,'Routing denominator differs')
            for arm in ('before','after'):
                fields=[role+'_behavioral_'+arm,role+'_additional_verification_'+arm]
                require(sum(routing['overall'][k] for k in fields)==total,'Routing does not conserve counts')
        require(not any(routing[k] for k in ('production_changed','scores_or_threshold_changed','otp_success_assumed','model_fit_performed')),'Routing scope overclaim')
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
    return {'status':'passed','manifest_files':len(manifest['files']),'report_referenced_files':len(paths),'missing_report_references':0,'native_equations':len(xml.findall('.//m:oMath',NS)),'report_tables':len(xml.findall('.//w:tbl',NS)),'references':len(refs),'self_collected_samples':597,'synthesis_rows':35,'uncertainty_comparisons':5,'enrollment_selection_reconciled':bool(manifest.get('enrollment_selection_study')),'usn_transfer_reconciled':bool(manifest.get('usn_transfer_study')),'usn_diagnostics_reconciled':bool(manifest.get('usn_diagnostics')),'scope':'Integrity and reconciliation of stored sources; not a model rerun or production acceptance'}

if __name__=='__main__':
    try:print(json.dumps(check(),ensure_ascii=True))
    except Exception as exc:print('FAIL: '+str(exc));sys.exit(1)
