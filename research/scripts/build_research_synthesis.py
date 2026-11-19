"""Summarize stored experiments without fitting, recalibrating or changing old artifacts."""
import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCES = ['research_summary', 'enrollment_study', 'stability_study', 'session_adaptation',
           'external_validation', 'matched_adaptation_results', 'cv_aggregation_control_results']
GROUPS = {
    'features': ('Khảo sát đặc trưng và chuẩn hóa', 'Bộ tự thu, 3 vòng ngoài; tổng 297 genuine/600 impostor.',
                 'Chọn qua vòng trong không cải thiện đồng thời FAR/FRR so baseline hiệu chỉnh; dữ liệu đã xem.'),
    'enrollment': ('Chất lượng enrollment và chuẩn hóa', 'Cùng bộ tự thu; 6 phương án, chọn qua vòng trong.',
                   'Giảm FRR nhưng tăng FAR; không thay cấu hình chính.'),
    'stability': ('Trọng số mềm qua 10 cách chia', 'Trung bình 10 cách chia trên cùng 15 mã; không phải 150 người.',
                  'Soft có FAR/FRR trung bình thấp hơn baseline; SD theo cách chia không phải CI, không bảo đảm chuyển nguồn.'),
    'cmu_sessions': ('Thích nghi CMU qua 8 phiên', 'Pooled 5.700 genuine/16.800 impostor, lịch checkpoint cũ.',
                     'Decay giảm hai lỗi so window trong phép thử này; không so trực tiếp với lịch probe phiên 2 bên dưới.'),
    'external': ('Kiểm chứng KeyRecs cố định hồ sơ', '3.301 genuine/10.560 impostor, 47 chiều; phương pháp khóa trước lượt chấm đầu.',
                 'Soft giảm 5 nhận nhầm và 7 genuine bị từ chối; lợi ích nhỏ, FRR còn khoảng 74%, không có suy luận thống kê mới.'),
    'matched': ('Đối chứng thích nghi cùng điều kiện', 'CMU và KeyRecs: cùng lịch phiên 2; mỗi nhánh hiệu chỉnh riêng trên dev FAR 5%.',
                'CMU thuận lợi mô tả; KeyRecs giảm FRR nhưng tăng FAR. Không ủng hộ nhất quán cả hai nguồn.'),
    'cv': ('Chỉ thay quy tắc tổng hợp CV', 'Cùng detector decay20, điểm OOF và ngưỡng z baseline; không phải cùng FAR dev.',
           'CMU đánh đổi FAR–FRR; KeyRecs cả hai lỗi tăng. Cả hai nguồn không đạt giả thuyết đã định.'),
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pointer(data, path):
    for part in path.strip('/').split('/'):
        data = data[int(part)] if isinstance(data, list) else data[part]
    return data


def build_rows():
    loaded = {name: json.loads((ROOT / f'results/{name}.json').read_text(encoding='utf-8')) for name in SOURCES}
    rows = []

    def add(group, source, label, artifact, path, basis='pooled', arm=None):
        stats = pointer(loaded[artifact], path)
        record = {'group': group, 'source': source, 'variant': label, 'metric_basis': basis,
                  'artifact': f'results/{artifact}.json', 'pointer': path,
                  'genuine_trials': None, 'genuine_rejected': None, 'impostor_trials': None,
                  'impostor_accepted': None, 'far': None, 'frr': None,
                  'pooled_far': None, 'pooled_frr': None, 'sd_far': None, 'sd_frr': None}
        if basis == 'mean_across_splits':
            record.update(far=stats['far']['mean'], frr=stats['frr']['mean'],
                          sd_far=stats['far']['std_across_splits'], sd_frr=stats['frr']['std_across_splits'])
        else:
            for key in ('genuine_trials', 'genuine_rejected', 'impostor_trials', 'impostor_accepted'):
                record[key] = stats[key]
            assert abs(stats['far'] - stats['impostor_accepted'] / stats['impostor_trials']) < 1e-12
            assert abs(stats['frr'] - stats['genuine_rejected'] / stats['genuine_trials']) < 1e-12
            record.update(far=stats['far'], frr=stats['frr'], pooled_far=stats['far'], pooled_frr=stats['frr'])
            if arm is not None:
                record.update(far=arm['macro_far'], frr=arm['macro_frr'])
        rows.append(record)

    for key, label in [('baseline_fixed', 'Baseline/ngưỡng CMU'), ('baseline_recalibrated', 'Baseline/hiệu chỉnh dev'),
                       ('nested_selected', 'Chọn phương án qua vòng trong')]:
        add('features', 'Bộ tự thu', label, 'research_summary', '/' + key)
    for key, label in [('baseline', 'Baseline'), ('nested_selected', 'Chọn enrollment/chuẩn hóa')]:
        add('enrollment', 'Bộ tự thu', label, 'enrollment_study', '/' + key)
    for i, family in enumerate(loaded['stability_study']['family_summaries']):
        add('stability', 'Bộ tự thu', family['id'], 'stability_study', f'/family_summaries/{i}', 'mean_across_splits')
    for i, method in enumerate(loaded['session_adaptation']['methods']):
        add('cmu_sessions', 'CMU/8 phiên', method['id'], 'session_adaptation', f'/methods/{i}/partitions/test/overall')
    for i, family in enumerate(loaded['external_validation']['families']):
        add('external', 'KeyRecs', family['id'], 'external_validation', f'/families/{i}/overall')
    for group, artifact in [('matched', 'matched_adaptation_results'), ('cv', 'cv_aggregation_control_results')]:
        for di, dataset in enumerate(loaded[artifact]['datasets']):
            for ai, arm in enumerate(dataset['arms']):
                add(group, dataset['dataset'], arm.get('method', arm.get('arm')), artifact,
                    f'/datasets/{di}/arms/{ai}/overall', 'macro_accounts', arm)
    assert len(rows) == 24
    return loaded, rows


def pct(value):
    return f'{100 * value:.2f}%'.replace('.', ',')


def main():
    loaded, rows = build_rows()
    result = {'date': '2026-11-14', 'scope': 'Synthesis of stored results only; no new experiment',
              'source_sha256': {f'results/{n}.json': sha(ROOT / f'results/{n}.json') for n in SOURCES},
              'groups': {k: {'title': v[0], 'protocol': v[1], 'conclusion': v[2]} for k, v in GROUPS.items()},
              'rows': rows,
              'limitations': ['No pooling across protocols or sources', 'Macro, pooled and split means explicitly distinct',
                              'CMU/KeyRecs already viewed after original external check; later controls are development',
                              'No new confidence intervals, p-values, threshold selection or production configuration change']}
    (ROOT / 'results/research_synthesis_20261114.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    with (ROOT / 'results/research_synthesis_20261114.csv').open('w', encoding='utf-8-sig', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    lines = ['# Tổng hợp đối chứng nghiên cứu — 14/11/2026', '',
             '24 dòng tổng hợp từ bảy artifact gốc. Không fit lại, đổi ngưỡng hoặc chọn lại candidate. '
             'Mỗi dòng CSV/JSON có đường dẫn nguồn và JSON pointer; chỉ so trực tiếp trong cùng nhóm/protocol.', '']
    for group, (title, protocol, conclusion) in GROUPS.items():
        lines += [f'## {title}', '', protocol, '', '| Nguồn | Phương án | Cách tổng hợp | FAR | FRR |', '|---|---|---|---:|---:|']
        for row in rows:
            if row['group'] == group:
                basis = {'pooled': 'Cộng số đếm', 'macro_accounts': 'Trung bình theo mã', 'mean_across_splits': 'Trung bình 10 cách chia'}[row['metric_basis']]
                lines.append(f"|{row['source']}|{row['variant']}|{basis}|{pct(row['far'])}|{pct(row['frr'])}|")
        lines += ['', conclusion, '']
    lines += ['## Diễn giải và phạm vi', '',
              'Giữ cấu hình triển khai hiện tại. Kết quả có chiều thuận lợi ở một nguồn không đủ để tuyên bố thắng nhất quán. '
              'Kiểm chứng KeyRecs ban đầu đã khóa phương pháp trước chấm; các đối chứng tiếp theo trên nguồn đã xem là phát triển phương pháp. '
              'Không chuyển profile/ngưỡng CMU sang vector KeyRecs 47 chiều. Không gộp bộ tự thu chủ yếu một phiên, CMU nhiều phiên và KeyRecs thành một FAR/FRR tổng.', '',
              'Bảng mean theo cách chia không có số đếm duy nhất và SD không phải CI. Hai đối chứng mới dùng chỉ tiêu chính macro; pooled vẫn lưu trong CSV/JSON. '
              'CMU có mẫu số genuine bằng nhau nên macro bằng pooled; KeyRecs khác số mẫu theo mã nên FRR có thể khác. '
              'Chưa có kết luận thống kê về độ chắc chắn hoặc nguyên nhân theo thiết bị/nhân khẩu học.', '',
              'Nguồn: các JSON trong source_sha256 của results/research_synthesis_20261114.json; protocol và freeze gốc giữ nguyên.']
    (ROOT / 'docs/RESEARCH_SYNTHESIS_20261114.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    plot_controls(rows)
    print('SYNTHESIS: 24 rows / 7 protocol groups; arithmetic checked against stored counts')


def plot_controls(rows):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(2, 2, figsize=(9.4, 6.5), constrained_layout=True)
    for ri, (group, label) in enumerate([('matched', 'Cùng điều kiện: window50 → decay20'),
                                        ('cv', 'Cùng ngưỡng z: CV đều → CV theo tuổi')]):
        for ci, source in enumerate(['CMU', 'KeyRecs fixed-text']):
            ax = axes[ri, ci]
            pair = [r for r in rows if r['group'] == group and r['source'] == source]
            for offset, metric in enumerate(['far', 'frr']):
                a, b = [100 * r[metric] for r in pair]
                ax.plot([a, b], [offset, offset], color='#8290a1', lw=3, zorder=1)
                ax.scatter([a], [offset], s=60, color='#245b91', label='Baseline' if offset == 0 else None, zorder=2)
                ax.scatter([b], [offset], s=60, color='#bf5b28', marker='D', label='Candidate' if offset == 0 else None, zorder=3)
                ax.annotate(f'{a:.2f} → {b:.2f}%', ((a+b)/2, offset), xytext=(0, 12), textcoords='offset points', ha='center', fontsize=9)
            ax.set_yticks([0, 1], ['FAR', 'FRR'])
            ax.set_ylim(-.4, 1.65)
            ax.set_xlim(-2, 64)
            ax.set_title(source.replace(' fixed-text', ''), fontsize=11)
            ax.set_xlabel('Macro theo mã (%); thấp hơn là ít lỗi hơn')
            ax.grid(axis='x', alpha=.2)
            ax.text(0, 1.10, label, transform=ax.transAxes, fontsize=9)
            ax.spines[['top', 'right']].set_visible(False)
    axes[0, 0].legend(loc='upper right', fontsize=8)
    fig.suptitle('Hai đối chứng có kiểm soát: giữ cả kết quả đánh đổi/bất lợi', fontsize=13)
    for suffix in ('png', 'pdf'):
        fig.savefig(ROOT / f'figures/research_controls_20261114.{suffix}', dpi=180)
    plt.close(fig)


if __name__ == '__main__':
    main()
