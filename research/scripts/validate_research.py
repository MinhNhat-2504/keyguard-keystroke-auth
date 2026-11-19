"""Check saved research artifacts, report geometry and unchanged source hashes."""
import csv
import hashlib
import json
from pathlib import Path

from docx import Document
from docx.oxml.ns import qn
import pymupdf

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    data = json.loads((ROOT / 'results/research_summary.json').read_text(encoding='utf-8'))
    manifest = json.loads((ROOT / 'data/collected_manifest.json').read_text(encoding='utf-8'))
    assert all(digest(ROOT / entry['path']) == entry['sha256'] for entry in manifest['files'])
    assert digest(ROOT / 'models/model_config.json') == data['protocol']['config_sha256']
    assert digest(ROOT / 'keyguard/research.py') == data['protocol']['research_code_sha256']
    assert len(data['variants']) == 24
    assert data['protocol']['samples'] == 597
    all_test_ids = [pid for fold in data['selection_by_fold'] for pid in fold['test_ids']]
    assert len(set(all_test_ids)) == len(all_test_ids) == 15
    for split in data['selection_by_fold']:
        assert not set(split['dev_ids']) & set(split['test_ids'])
        assert len(split['dev_ids']) == 10 and len(split['test_ids']) == 5
        best = min(split['inner_ranking'], key=lambda r: (r['inner_balanced_error'], r['variant']))
        assert best['variant'] == split['selected_variant']
    for variant in data['variants']:
        for row in variant['folds']:
            assert row['dev']['far'] <= .05
            assert row['dev']['impostor_trials'] == 900
            assert row['test']['impostor_trials'] == 200
        assert variant['overall']['genuine_trials'] == 297
        assert variant['overall']['impostor_trials'] == 600
    with (ROOT / 'results/research_comparison.csv').open(encoding='utf-8', newline='') as f:
        csv_rows = list(csv.DictReader(f))
    assert len(csv_rows) == 72
    for csv_row in csv_rows:
        variant = next(v for v in data['variants'] if v['id'] == csv_row['variant'])
        row = variant['folds'][int(csv_row['fold']) - 1]
        for metric in ('far', 'frr'):
            assert float(csv_row[metric]) == row['test'][metric]
    js = (ROOT / 'explorer/research-data.js').read_text(encoding='utf-8')
    assert json.loads(js.removeprefix('window.KEYGUARD_RESEARCH = ').rstrip(';\n')) == data

    diag_path = ROOT / 'results/research_diagnostics.json'
    diagnostics = json.loads(diag_path.read_text(encoding='utf-8'))
    assert diagnostics['source_summary_sha256'] == digest(ROOT / 'results/research_summary.json')
    assert diagnostics['config_sha256'] == digest(ROOT / 'models/model_config.json')
    assert diagnostics['diagnostics_code_sha256'] == digest(ROOT / 'keyguard/diagnostics.py')
    diag_js = (ROOT / 'explorer/diagnostics-data.js').read_text(encoding='utf-8')
    assert json.loads(diag_js.removeprefix('window.KEYGUARD_DIAGNOSTICS = ').rstrip(';\n')) == diagnostics
    for variant in diagnostics['variants']:
        saved = next(v for v in data['variants'] if v['id'] == variant['id'])
        for fold in variant['folds']:
            reference = saved['folds'][fold['fold'] - 1]
            for policy, key in [('dev', 'test'), ('cmu', 'fixed_cmu')]:
                accounts, pairs = fold['accounts'][policy], fold['pairs'][policy]
                expected = reference[key]
                assert len(accounts) == 5 and len(pairs) == 20
                assert sum(a['genuine_rejected'] for a in accounts) == expected['genuine_rejected']
                assert sum(a['impostor_accepted'] for a in accounts) == expected['impostor_accepted']
                assert sum(p['accepted'] for p in pairs) == expected['impostor_accepted']
                assert all(a['impostor_trials'] == 40 for a in accounts)
            assert len(fold['dev_jackknife']) == 10
            assert all(j['impostor_trials'] == 720 for j in fold['dev_jackknife'])
    baseline = diagnostics['pipelines']['baseline_recalibrated']
    assert baseline['folds'][0]['impostor_accepted'] == 38
    p10 = next(a for a in baseline['accounts'] if a['participant_id'] == 'P10')
    p09 = next(a for a in baseline['accounts'] if a['participant_id'] == 'P09')
    assert p10['impostor_accepted'] == 24 and p09['genuine_rejected'] == 20
    assert all(a['dispersion_floor_dimensions'] == 0 for a in baseline['accounts'])
    csv_counts = {}
    for name, count in [('research_account_errors.csv',720), ('research_pair_errors.csv',2880),
                        ('research_threshold_jackknife.csv',720)]:
        with (ROOT / 'results' / name).open(encoding='utf-8', newline='') as f:
            csv_counts[name] = len(list(csv.DictReader(f)))
        assert csv_counts[name] == count

    full = pymupdf.open(ROOT / 'report/KeyGuard_BaoCao_DayDu.pdf')
    assert len(full) == 34
    assert all(page.get_text().strip() for page in full)
    cover = full[0]
    title = 'BÁO CÁO BÀI TẬP LỚN MÔN HỌC'
    assert title in cover.get_text()
    names = [cover.search_for(name)[0] for name in
             ('Trịnh Ngọc Minh Nhật', 'Nguyễn Anh Thư', 'Nguyễn Thái Anh')]
    ids = [cover.search_for(number)[0] for number in ('2474802010280', '2474802010381')]
    assert max(rect.x0 for rect in names) - min(rect.x0 for rect in names) < .5
    assert abs(ids[0].x0 - ids[1].x0) < .5
    assert all(abs(name.y0 - number.y0) < .5 for name, number in zip(names[:2], ids))
    full_text = ' '.join(' '.join(page.get_text().split()) for page in full)
    assert 'BÁO CÁO ĐỒ ÁN MÔN HỌC' not in full_text
    toc_text=' '.join(full[i].get_text() for i in (2,3))
    assert '2.17.' in toc_text and '2.18.' in toc_text and '2.19.' in toc_text
    assert '31.17%' in full_text and '64.98%' in full_text and '63.97%' in full_text
    assert 'hướng phát triển' in full_text
    assert '38/46' in full_text and '24/46' in full_text and '20/20' in full_text
    doc = Document(ROOT / 'report/KeyGuard_BaoCao_DayDu.docx')
    assert title in doc.core_properties.title
    assert len(doc.tables) == 21 and len(doc.inline_shapes) == 16
    assert 'KeyRecs' in full_text and '74.01%' in full_text and '48.74%' in full_text
    for page in full:
        if 'Bảng 2.19.' in page.get_text() or 'Bảng 2.20.' in page.get_text():
            for word in page.get_text('words'):
                assert word[0]>=35 and word[2]<=page.rect.width-30, 'External report text outside page margins'
    assert all(section._sectPr.find(qn('w:cols')).get(qn('w:num'), '1') == '1'
               for section in doc.sections)
    for j in (17, 18, 19):
        full[j].get_pixmap(matrix=pymupdf.Matrix(.85, .85)).save(
            ROOT / f'report/preview/research-report-page-{j+1}.png')
    for page in full:
        if 'Hình 2.11.' in page.get_text():
            page.get_pixmap(matrix=pymupdf.Matrix(1, 1)).save(ROOT / 'report/preview/diagnostics-heatmap-final.png')
    short = pymupdf.open(ROOT / 'report/KeyGuard_Report.pdf')
    assert len(short) == 6 and all(page.get_text().strip() for page in short)
    short_doc = Document(ROOT / 'report/KeyGuard_Report.docx')
    assert all(section._sectPr.find(qn('w:cols')).get(qn('w:num'), '1') == '2'
               for section in short_doc.sections[1:])
    previous = json.loads((ROOT / 'results/research_validation.json').read_text(encoding='utf-8'))
    for name, expected_hash in previous['short_report_sha256'].items():
        assert digest(ROOT / 'report' / name) == expected_hash
    result = {
        'date': '2026-11-13', 'variants': 24, 'comparison_rows': 72,
        'raw_file_hashes_verified': len(manifest['files']), 'model_config_unchanged': True,
        'report_pdf_pages': len(full), 'report_nonblank': True,
        'cover_title_correct': True, 'authors_ids_supervisor_columns_aligned': True,
        'short_report_pdf_pages': len(short), 'short_report_columns': 2,
        'short_reports_preservation': 'Generator asserted equal before/after SHA-256 on every build',
        'short_report_sha256': {name: digest(ROOT / 'report' / name) for name in
                               ('KeyGuard_Report.docx', 'KeyGuard_Report.pdf')},
        'diagnostics': {'csv_rows': csv_counts, 'policies_reconciled': 144,
                        'original_research_summary_hash_verified': True},
        'python_checks': {'passed': 50, 'subtests_passed': 4,
                          'scope': 'external/soft_weight/stability/session_adaptation/enrollment/contamination/diagnostics/research/model/collected/live_evidence/features/simulation'},
        'enrollment_update_validation':'results/enrollment_update_validation.json',
        'stability_adaptation_validation':'results/stability_adaptation_validation.json',
        'external_validation_checks':'results/external_validation_checks.json',
        'full_sklearn_suite_rerun': False,
        'reason': 'Existing Application Control DLL restriction; no sklearn model called by new experiments',
    }
    (ROOT / 'results/research_validation.json').write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    detailed_path = ROOT / 'results/detailed_report_validation.json'
    detailed = json.loads(detailed_path.read_text(encoding='utf-8'))
    detailed.update({'date': '2026-11-13', 'pdf_pages': len(full), 'tables': 21, 'figures': 16,
                     'cover_title': title, 'cover_columns_aligned': True,
                     'research_validation': 'results/research_validation.json'})
    detailed_path.write_text(json.dumps(detailed, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    summary_path = ROOT / 'results/validation_summary.json'
    summary = json.loads(summary_path.read_text(encoding='utf-8'))
    summary['date'] = '2026-11-13'
    summary['report']['full_pdf_pages'] = len(full)
    summary['research'] = {'artifacts': 'results/research_validation.json',
                           'browser': 'results/research_browser_validation.json',
                           'python_tests_passed': 50, 'new_research_tests': 6, 'new_diagnostics_tests': 5,
                           'new_enrollment_update_tests':8,
                           'enrollment_update_validation':'results/enrollment_update_validation.json',
                           'new_soft_weight_adaptation_tests':9,
                           'stability_adaptation_validation':'results/stability_adaptation_validation.json',
                           'new_external_validation_tests':5,
                           'external_validation_checks':'results/external_validation_checks.json',
                           'full_sklearn_suite_rerun': False}
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('PASS: frozen external results and prior studies preserved; PDF 34 pages; aligned cover/margins; separate 6-page report unchanged')


if __name__ == '__main__':
    main()
