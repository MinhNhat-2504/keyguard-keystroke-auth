'use strict';
const data = window.KEYGUARD_RESEARCH;
const $ = id => document.getElementById(id);
const pct = value => (value * 100).toLocaleString('vi-VN', {minimumFractionDigits: 2, maximumFractionDigits: 2}) + '%';
const num = value => value.toLocaleString('vi-VN', {maximumFractionDigits: 6});
const modelNames = {mean_mad: 'Trung bình', median_mad: 'Trung vị'};
const featureNames = {all: '31 đặc trưng', H: 'Giữ phím H', DD: 'Khoảng nhấn DD', UD: 'Nhả–nhấn UD'};
const normNames = {raw: 'Thời gian gốc', duration: 'Chia tổng thời gian', median_hold: 'Chia trung vị giữ phím'};
const qualityNames = {keep_all:'Giữ 20 mẫu',robust_filter:'Lọc robust · tối đa 20%'};
const calibrationNames = {mean_std:'Mean/Std',median_mad:'Median/MAD',median_iqr:'Median/IQR'};
const label = v => `${modelNames[v.model]} · ${featureNames[v.features]} · ${normNames[v.normalization]}`;
const nearest = (points, value) => points.reduce((best, p, i) => Math.abs(p.threshold - value) < Math.abs(points[best].threshold - value) ? i : best, 0);
let current, fold, points;

function renderPipelines() {
  const pipelines = [['Ngưỡng CMU giữ nguyên', data.baseline_fixed], ['Hiệu chỉnh ngưỡng · baseline', data.baseline_recalibrated], ['Chọn phương án qua vòng trong', data.nested_selected]];
  $('pipeline-summary').innerHTML = pipelines.map(([name, r]) => `<article class="pipeline"><h3>${name}</h3><div class="rates"><div><small>FAR</small><b>${pct(r.far)}</b><small>${r.impostor_accepted}/${r.impostor_trials} lượt</small></div><div><small>FRR</small><b>${pct(r.frr)}</b><small>${r.genuine_rejected}/${r.genuine_trials} lượt</small></div></div></article>`).join('');
}

function renderTable() {
  $('variants-table').innerHTML = data.variants.map(v => `<tr class="${v.id === current.id ? 'active-row' : ''}"><td><button type="button" class="variant-link" data-variant="${v.id}">${label(v)}</button></td><td>${pct(v.overall.far)}</td><td>${pct(v.overall.frr)}</td><td>${pct(v.mean_fold_eer)}</td><td>${v.mean_fold_auc.toFixed(3)}</td></tr>`).join('');
}

function selectedVariantChanged() {
  const key = `${$('model').value}__${$('features').value}__${$('normalization').value}`;
  current = data.variants.find(v => v.id === key);
  fold = current.folds[Number($('fold').value)];
  points = fold.test_curve.points;
  $('threshold').max = points.length - 1;
  if ($('policy').value === 'explore') $('policy').value = 'dev';
  applyPolicy();
  const split = data.selection_by_fold[fold.fold - 1];
  $('partition-info').innerHTML = `<p><b>Nhóm phát triển:</b> ${split.dev_ids.join(', ')}</p><p><b>Nhóm đánh giá:</b> ${split.test_ids.join(', ')}</p><p><b>Phương án vòng trong chọn:</b> ${label(data.variants.find(v => v.id === split.selected_variant))}</p>`;
  $('variant-note').textContent = current.id === data.baseline_id ? 'Baseline dùng Scaled Manhattan và 31 đặc trưng gốc; hồ sơ cố định sau đăng ký.' : 'Đây là biến thể nghiên cứu. Ngưỡng CMU chỉ là tham chiếu, chưa được hiệu chỉnh cho biến thể này.';
  renderTable();
  renderDiagnostics();
}

function renderDiagnostics() {
  const diagnostics = window.KEYGUARD_DIAGNOSTICS;
  if (!diagnostics) {
    $('account-detail').textContent = 'Chưa có chẩn đoán. Chạy python scripts/analyze_research.py rồi mở lại trang.';
    return;
  }
  const variant = diagnostics.variants.find(v => v.id === current.id);
  const row = variant.folds[fold.fold - 1];
  const mode = $('diagnostic-policy').value;
  const accounts = row.accounts[mode];
  const previous = $('diagnostic-account').value;
  const defaultId = [...accounts].sort((a,b) => b.far-a.far || b.frr-a.frr)[0].participant_id;
  $('diagnostic-account').innerHTML = accounts.map(a => `<option value="${a.participant_id}">${a.participant_id}</option>`).join('');
  $('diagnostic-account').value = accounts.some(a => a.participant_id === previous) ? previous : defaultId;
  $('account-errors').innerHTML = accounts.map(a => `<tr><td>${a.participant_id}</td><td>${a.impostor_accepted}/${a.impostor_trials}</td><td>${pct(a.far)}</td><td>${a.genuine_rejected}/${a.genuine_trials}</td><td>${pct(a.frr)}</td></tr>`).join('');
  $('pair-errors').innerHTML = [...row.pairs[mode]].sort((a,b) => b.accepted-a.accepted || a.target.localeCompare(b.target) || a.impostor.localeCompare(b.impostor)).map(p => `<tr><td>${p.target}</td><td>${p.impostor}</td><td>${p.accepted_early}</td><td>${p.accepted_late}</td><td>${p.accepted}/${p.trials}</td></tr>`).join('');
  const thresholds = row.dev_jackknife.map(j => j.threshold);
  $('jackknife-detail').textContent = `Ngưỡng dev hiện tại ${num(fold.threshold)}; bỏ từng mã dev khỏi cả vai trò tài khoản và impostor cho khoảng ${num(Math.min(...thresholds))} đến ${num(Math.max(...thresholds))}. Mỗi lần còn 9 mã / 720 lượt impostor. Không dùng khoảng này để chọn ngưỡng mới.`;
  const baseline = diagnostics.pipelines.baseline_recalibrated;
  const worstFold = [...baseline.folds].sort((a,b) => b.impostor_accepted-a.impostor_accepted)[0];
  const worstAccount = baseline.top_far[0];
  const total = baseline.accounts.reduce((sum,a) => sum+a.impostor_accepted,0);
  $('error-concentration').textContent = `Toàn bộ baseline hiệu chỉnh: vòng ${worstFold.fold} chiếm ${worstFold.impostor_accepted}/${total} lượt nhận nhầm; riêng tài khoản ${worstAccount.participant_id} chiếm ${worstAccount.impostor_accepted}/${total}. Xem từng mã để tránh kết luận từ tỷ lệ trung bình.`;
  renderAccountDetail();
}

function renderAccountDetail() {
  const row = window.KEYGUARD_DIAGNOSTICS?.variants.find(v => v.id === current.id)?.folds[fold.fold - 1];
  if (!row) return;
  const account = row.accounts[$('diagnostic-policy').value].find(a => a.participant_id === $('diagnostic-account').value);
  const featureText = account.rejected_genuine_top_features.map(f => `${f.feature}: ${pct(f.share)}`).join(' · ') || 'Không có lượt genuine bị từ chối tại ngưỡng này.';
  $('account-detail').innerHTML = `<h3>${account.participant_id} · Ngưỡng ${num(account.threshold)}</h3><dl><dt>Trung vị z chính chủ / impostor</dt><dd>${num(account.genuine_z_q10_q50_q90[1])} / ${num(account.impostor_z_q10_q50_q90[1])}</dd><dt>Thời gian gõ trung vị đăng ký / đánh giá</dt><dd>${num(account.duration_enrollment_median)} s / ${num(account.duration_genuine_median)} s (${account.duration_ratio_test_enrollment.toFixed(2)} ×)</dd><dt>Chuẩn hóa điểm từ 20 mẫu đăng ký</dt><dd>μ = ${num(account.enrollment_cv_mean)} · σ = ${num(account.enrollment_cv_std)}</dd><dt>Chiều chạm sàn độ phân tán</dt><dd>${account.dispersion_floor_dimensions}/${account.feature_dimensions}</dd></dl><p><b>Tỷ trọng khoảng cách ở các lượt genuine bị từ chối:</b> ${featureText}</p>`;
}

function applyPolicy() {
  const tau = $('policy').value === 'cmu' ? data.protocol.baseline_threshold : fold.threshold;
  if ($('policy').value !== 'explore') $('threshold').value = nearest(points, tau);
  renderThreshold();
}

function renderThreshold() {
  const point = points[Number($('threshold').value)];
  const atDevThreshold = point.threshold === fold.threshold;
  $('threshold-value').textContent = num(point.threshold);
  $('far').textContent = pct(point.far);
  $('frr').textContent = pct(point.frr);
  $('far-count').textContent = `${point.impostor_accepted}/${point.impostor_trials} lượt impostor được nhận`;
  $('frr-count').textContent = `${point.genuine_rejected}/${point.genuine_trials} lượt genuine cần xác minh`;
  $('dev-status').className = 'status' + (atDevThreshold ? '' : ' warn');
  $('dev-status').textContent = atDevThreshold ? `Tại ngưỡng đã chọn: FAR nhóm phát triển ${pct(fold.dev.far)}. FAR nhóm đánh giá có thể vượt 5%.` : 'Đang khảo sát ngưỡng tham chiếu hoặc thủ công. Không dùng kết quả trên nhóm đánh giá để chọn lại phương án.';
  $('curve-summary').textContent = `Nhóm đánh giá vòng ${fold.fold}: EER ${pct(fold.test_curve.eer)} · AUC ${fold.test_curve.auc.toFixed(3)}. EER nội suy mô tả đường ROC, không phải ngưỡng triển khai.`;
  renderRoc(point);
}

function renderRoc(point) {
  const left = 55, top = 18, width = 395, height = 265;
  const xy = (x, y) => `${left + width * x},${top + height * (1 - y)}`;
  const path = curve => 'M' + curve.points.map(p => xy(p.far, 1 - p.frr)).join(' L');
  let svg = '';
  for (let k = 0; k <= 5; k++) {
    const t = k / 5, x = left + width * t, y = top + height * (1 - t);
    svg += `<path d="M${x},${top} V${top + height} M${left},${y} H${left + width}" stroke="#e2e9f0" fill="none"/><text x="${x}" y="${top + height + 20}" text-anchor="middle" font-size="11" fill="#617183">${Math.round(t * 100)}%</text><text x="${left - 9}" y="${y + 4}" text-anchor="end" font-size="11" fill="#617183">${Math.round(t * 100)}%</text>`;
  }
  svg += `<path d="M${xy(0, 0)} L${xy(1, 1)}" stroke="#adbaca" stroke-dasharray="4 5" fill="none"/><path d="${path(fold.dev_curve)}" stroke="#007e77" stroke-width="2.5" fill="none"/><path d="${path(fold.test_curve)}" stroke="#365fc0" stroke-width="2.5" fill="none"/>`;
  const [tx, ty] = xy(point.far, 1 - point.frr).split(',');
  svg += `<circle cx="${tx}" cy="${ty}" r="5" fill="#365fc0" stroke="white" stroke-width="2"><title>FAR ${pct(point.far)}, FRR ${pct(point.frr)}</title></circle><text x="250" y="330" text-anchor="middle" font-size="12" fill="#4a5c70">FAR · Tỷ lệ nhận nhầm</text><text transform="translate(14,155) rotate(-90)" text-anchor="middle" font-size="12" fill="#4a5c70">TAR · Tỷ lệ nhận đúng</text>`;
  $('roc').innerHTML = svg;
}

function downloadCsv() {
  const header = ['variant', 'far', 'frr', 'genuine_rejected', 'genuine_trials', 'impostor_accepted', 'impostor_trials', 'mean_fold_eer', 'mean_fold_auc'];
  const rows = data.variants.map(v => [v.id, v.overall.far, v.overall.frr, v.overall.genuine_rejected, v.overall.genuine_trials, v.overall.impostor_accepted, v.overall.impostor_trials, v.mean_fold_eer, v.mean_fold_auc]);
  const url = URL.createObjectURL(new Blob(['\ufeff' + [header, ...rows].map(r => r.join(',')).join('\r\n')], {type: 'text/csv;charset=utf-8'}));
  const a = document.createElement('a'); a.href = url; a.download = 'keyguard-research-overall.csv'; a.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

function renderEnrollment() {
  const study=window.KEYGUARD_ENROLLMENT;
  if(!study){$('enrollment-detail').textContent='Chưa có dữ liệu nghiên cứu đăng ký.';return;}
  const label=v=>qualityNames[v.quality]+' · '+calibrationNames[v.calibration];
  $('enrollment-variant').innerHTML=study.variants.map(v=>`<option value="${v.id}">${label(v)}</option>`).join('');
  const ids=study.enrollment_diagnostics.filter(r=>r.variant===study.variants[0].id).map(r=>r.participant_id);
  $('enrollment-account').innerHTML=ids.map(pid=>`<option>${pid}</option>`).join('');
  $('enrollment-summary').innerHTML=[['Baseline hiện tại',study.baseline],['Chọn qua vòng trong · 6 phương án',study.nested_selected]].map(([name,r])=>`<article class="pipeline"><h3>${name}</h3><div class="rates"><div><small>FAR</small><b>${pct(r.far)}</b><small>${r.impostor_accepted}/${r.impostor_trials}</small></div><div><small>FRR</small><b>${pct(r.frr)}</b><small>${r.genuine_rejected}/${r.genuine_trials}</small></div></div></article>`).join('');
  $('enrollment-table').innerHTML=study.variants.map(v=>{
    const kept=study.enrollment_diagnostics.filter(r=>r.variant===v.id).reduce((s,r)=>s+r.kept,0);
    return `<tr><td>${label(v)}</td><td>${v.overall.impostor_accepted}/${v.overall.impostor_trials} · ${pct(v.overall.far)}</td><td>${v.overall.genuine_rejected}/${v.overall.genuine_trials} · ${pct(v.overall.frr)}</td><td>${pct(v.mean_eer)}</td><td>${kept}/300</td></tr>`;
  }).join('');
  $('enrollment-variant').addEventListener('change',renderEnrollmentDetail);
  $('enrollment-account').addEventListener('change',renderEnrollmentDetail);
  renderEnrollmentDetail();
}

function renderEnrollmentDetail(){
  const study=window.KEYGUARD_ENROLLMENT;
  const id=$('enrollment-variant').value,pid=$('enrollment-account').value;
  const diag=study.enrollment_diagnostics.find(r=>r.variant===id&&r.participant_id===pid);
  const variant=study.variants.find(v=>v.id===id);
  const split=study.selection_by_fold.find(r=>r.test_ids.includes(pid));
  const result=variant.folds[split.fold-1].accounts.find(r=>r.participant_id===pid);
  $('enrollment-detail').innerHTML=`<h3>${pid} · ${diag.kept}/20 mẫu giữ lại</h3><p>Vị trí theo thứ tự thời gian trong 20 mẫu đăng ký bị cờ: ${diag.removed_positions_1based.join(', ')||'không có'}. Không phải số rep gốc; không xóa dữ liệu.</p><p>Tâm chuẩn hóa ${num(diag.score_center)} · độ phân tán ${num(diag.score_scale)}. Vòng ngoài ${split.fold}: FAR ${result.impostor_accepted}/${result.impostor_trials} = ${pct(result.far)}; FRR ${result.genuine_rejected}/${result.genuine_trials} = ${pct(result.frr)}.</p>`;
}

function renderContamination(){
  const study=window.KEYGUARD_CONTAMINATION;
  if(!study){$('contamination-note').textContent='Chưa có mô phỏng cập nhật hồ sơ.';return;}
  const policy=$('contamination-policy').value,target=$('contamination-target').value;
  const entry=study.summaries.find(r=>r.policy===policy);
  const pair=study.pairs.find(r=>r.target===target);
  const arms=pair?pair.policies[policy]:entry.arms;
  const control=arms.control,injected=arms.injected;
  const last=injected.checkpoints.at(-1),lastControl=control.checkpoints.at(-1);
  $('contamination-summary').innerHTML=`<div><span>Mẫu xen được nhận</span><strong>${injected.attacks_accepted}/${injected.attack_trials}</strong><small>${pct(injected.attacks_accepted/injected.attack_trials)} · không phải FAR toàn bộ CMU</small></div><div><span>Genuine cần xác minh · có / không xen</span><strong>${injected.genuine_rejected} / ${control.genuine_rejected}</strong><small>Mẫu số mỗi nhánh: ${injected.genuine_trials}</small></div>`;
  $('contamination-table').innerHTML=injected.checkpoints.map((point,j)=>`<tr><td>${point.genuine_seen}</td><td>${control.checkpoints[j].probe_accepted}/${point.probe_trials}</td><td>${point.probe_accepted}/${point.probe_trials}</td><td>${point.contaminated_rows}</td></tr>`).join('');
  $('contamination-note').textContent=(pair?`Tài khoản ${pair.target}, mã đóng vai impostor ${pair.attacker}. `:'Tổng 15 cặp. ')+`Mẫu impostor còn cuối chuỗi: ${injected.final_contaminated_rows}. Probe cuối có/không xen: ${last.probe_accepted}/${last.probe_trials} và ${lastControl.probe_accepted}/${lastControl.probe_trials}. Có mẫu lọt vào hồ sơ không đồng nghĩa bộ probe được nhận tăng; không kết luận an toàn từ một kịch bản cố định.`;
}

const familyNames={baseline:'Baseline · giữ 20/Mean-Std',hard_selected:'Lọc cứng · chọn qua vòng trong',soft_selected:'Trọng số mềm · chọn qua vòng trong',all_selected:'Chọn cả 9 qua vòng trong'};
function setupStability(){
  const study=window.KEYGUARD_STABILITY;
  if(!study){$('stability-detail').textContent='Chưa có dữ liệu khảo sát độ ổn định.';return;}
  const sd=r=>pct(r.mean)+' ± '+pct(r.std_across_splits);
  $('stability-summary').innerHTML=study.family_summaries.map(r=>`<tr><td>${familyNames[r.id]}</td><td>${sd(r.far)}</td><td>${sd(r.frr)}</td><td>${pct(r.eer.mean)}</td><td>${r.auc.mean.toFixed(3)}</td></tr>`).join('');
  $('stability-variants').innerHTML=study.variant_summaries.map(r=>`<tr><td>${r.id}</td><td>${pct(r.far.mean)}</td><td>${pct(r.frr.mean)}</td><td>${pct(r.eer.mean)}</td><td>${r.auc.mean.toFixed(3)}</td></tr>`).join('');
  const wins=study.paired_differences.filter(r=>r.soft_minus_baseline_far<0&&r.soft_minus_baseline_frr<0).length;
  $('stability-paired').textContent=`Trọng số mềm giảm đồng thời FAR và FRR so với baseline trong ${wins}/${study.protocol.seeds.length} cách chia. EER/AUC trung bình chưa tốt hơn baseline. Không kết luận thắng toàn diện hoặc chọn phương án từ các kết quả ngoài đã xem.`;
  $('stability-seed').innerHTML=study.protocol.seeds.map(seed=>`<option>${seed}</option>`).join('');
  const ids=study.enrollment_diagnostics.filter(r=>r.quality==='soft_weight'&&r.calibration==='mean_std').map(r=>r.participant_id);
  $('stability-account').innerHTML=ids.map(pid=>`<option>${pid}</option>`).join('');
  for(const id of ['stability-seed','stability-family','stability-account'])$(id).addEventListener('change',renderStability);
  renderStability();
}

function renderStability(){
  const study=window.KEYGUARD_STABILITY;if(!study)return;
  const repeat=study.repetitions.find(r=>r.seed===Number($('stability-seed').value));
  const family=$('stability-family').value,pid=$('stability-account').value;
  const rows=repeat.folds.flatMap(f=>{
    const selected=f.selected[family].variant;
    return f.variants[selected].accounts.map(a=>({...a,variant:selected,fold:f.fold}));
  });
  $('stability-accounts').innerHTML=rows.map(r=>`<tr><td>${r.participant_id} / ${r.fold}</td><td>${r.variant}</td><td>${r.impostor_accepted}/${r.impostor_trials} · ${pct(r.far)}</td><td>${r.genuine_rejected}/${r.genuine_trials} · ${pct(r.frr)}</td></tr>`).join('');
  const row=rows.find(r=>r.participant_id===pid);
  const [quality,calibration]=row.variant.split('__');
  const diag=study.enrollment_diagnostics.find(r=>r.participant_id===pid&&r.quality===quality&&r.calibration===calibration);
  const aggregate=repeat.families[family];
  $('stability-detail').innerHTML=`<h3>Seed ${repeat.seed} · ${familyNames[family]}</h3><p>FAR ${aggregate.impostor_accepted}/${aggregate.impostor_trials} = ${pct(aggregate.far)}; FRR ${aggregate.genuine_rejected}/${aggregate.genuine_trials} = ${pct(aggregate.frr)}.</p><p>${pid} · ${row.variant}: giữ trọng số dương ${diag.positive_weights}/20 mẫu, cỡ mẫu hiệu dụng ${diag.effective_samples.toFixed(2)} (mô tả trọng số, không thêm người/mẫu độc lập).</p><p>Trọng số theo thứ tự 20 mẫu đăng ký: ${diag.weights.map(w=>w.toFixed(3)).join(' · ')}.</p>`;
}

function renderAdaptation(){
  const study=window.KEYGUARD_ADAPTATION;if(!study){$('adaptation-note').textContent='Chưa có dữ liệu thích nghi theo phiên.';return;}
  const method=study.methods.find(r=>r.id===$('adaptation-method').value);
  const partition=method.partitions[$('adaptation-partition').value];
  const r=partition.overall;
  $('adaptation-summary').innerHTML=`<div><span>FAR · probe đầu phiên</span><strong>${pct(r.far)}</strong><small>${r.impostor_accepted}/${r.impostor_trials}</small></div><div><span>FRR · genuine cần xác minh</span><strong>${pct(r.frr)}</strong><small>${r.genuine_rejected}/${r.genuine_trials}</small></div>`;
  $('adaptation-sessions').innerHTML=partition.sessions.map(s=>`<tr><td>${s.session}</td><td>${s.genuine_rejected}/${s.genuine_trials}</td><td>${pct(s.frr)}</td><td>${s.impostor_accepted}/${s.impostor_trials}</td><td>${pct(s.far)}</td><td>${pct(s.eer)}</td><td>${s.auc.toFixed(3)}</td></tr>`).join('');
  $('adaptation-note').textContent=`Ngưỡng chọn riêng trên dev: ${num(method.threshold)}; FAR dev ${pct(method.dev_far)}. Giữ nguyên ngưỡng này ở cả 8 phiên test, không chọn lại theo lỗi phiên sau. Phiên 1 còn 30 lượt genuine sau enrollment; mỗi phiên 2–8 có 50 lượt/mã.`;
}

function setupExternal(){
  const study=window.KEYGUARD_EXTERNAL;
  if(!study){$('external-account-detail').textContent='Chưa có kết quả kiểm chứng nguồn ngoài.';return;}
  $('external-family-table').innerHTML=study.families.map(f=>{
    const r=f.overall;
    return `<tr><td>${familyNames[f.id]}</td><td>${r.impostor_accepted}/${r.impostor_trials}</td><td>${pct(r.far)}</td><td>${r.genuine_rejected}/${r.genuine_trials}</td><td>${pct(r.frr)}</td><td>${pct(f.macro_eer)}</td><td>${f.macro_auc.toFixed(3)}</td></tr>`;
  }).join('');
  $('external-variants-table').innerHTML=study.variants.map(r=>`<tr><td>${r.id}</td><td>${pct(r.overall.far)}</td><td>${pct(r.overall.frr)}</td><td>${pct(r.macro_eer)}</td><td>${r.macro_auc.toFixed(3)}</td></tr>`).join('');
  $('external-account').innerHTML=study.test_ids.map(pid=>`<option>${pid}</option>`).join('');
  const names={static:'Cố định',window50:'Cửa sổ 50 đều',decay20:'Cửa sổ 50 · bán rã 20'};
  $('external-adaptation-table').innerHTML=study.adaptation.map(m=>`<tr><td>${names[m.id]}</td><td>${m.overall.impostor_accepted}/${m.overall.impostor_trials} · ${pct(m.overall.far)}</td><td>${m.overall.genuine_rejected}/${m.overall.genuine_trials} · ${pct(m.overall.frr)}</td></tr>`).join('');
  const baseline=study.families.find(r=>r.id==='baseline'),soft=study.families.find(r=>r.id==='soft_selected');
  $('external-conclusion').textContent=`Trọng số mềm giảm ${baseline.overall.impostor_accepted-soft.overall.impostor_accepted} lượt nhận nhầm và ${baseline.overall.genuine_rejected-soft.overall.genuine_rejected} lượt genuine cần xác minh so baseline; mức cải thiện nhỏ, FRR vẫn ${pct(soft.overall.frr)}. Không suy ra hiệu quả sử dụng đã tốt hoặc khả năng tổng quát hóa đã được bảo đảm. Decay giảm FRR nhưng FAR nhỉnh hơn window đều ở nguồn này.`;
  $('external-freeze').textContent=`Hash protocol đóng băng: ${study.freeze_sha256}. Chỉ một cách chia mã seed42; ngưỡng được chọn trên dev nguồn mới, không dùng bất kỳ kết quả phiên 2 để chọn lại. Không sửa dữ liệu hoặc cấu hình sản phẩm.`;
  for(const id of ['external-family','external-account'])$(id).addEventListener('change',renderExternalAccount);
  renderExternalAccount();
}

function renderExternalAccount(){
  const study=window.KEYGUARD_EXTERNAL;if(!study)return;
  const family=study.families.find(r=>r.id===$('external-family').value);
  const variant=study.variants.find(r=>r.id===family.variant);
  const account=variant.accounts.find(r=>r.participant_id===$('external-account').value);
  $('external-account-detail').innerHTML=`<h3>${account.participant_id} · ${variant.id}</h3><p>Ngưỡng từ dev phiên 1: ${num(variant.threshold)}. FAR dev ${pct(variant.dev.far)}.</p><p>Test phiên 2: nhận nhầm ${account.impostor_accepted}/${account.impostor_trials} = ${pct(account.far)}; genuine cần xác minh ${account.genuine_rejected}/${account.genuine_trials} = ${pct(account.frr)}.</p><p>EER ${pct(account.eer)} · AUC ${account.auc.toFixed(3)}. Mã và phiên chỉ dùng để chia dữ liệu, không đưa vào vector ${study.features.length} chiều.</p>`;
}

if (!data || data.schema_version !== 1) {
  document.querySelector('main').textContent = 'Không đọc được dữ liệu. Hãy chạy python scripts/run_research.py rồi mở lại trang.';
} else {
  renderPipelines();
  for (const id of ['model', 'features', 'normalization', 'fold']) $(id).addEventListener('change', selectedVariantChanged);
  $('policy').addEventListener('change', applyPolicy);
  $('threshold').addEventListener('input', () => {$('policy').value = 'explore'; renderThreshold();});
  $('variants-table').addEventListener('click', event => {
    const button = event.target.closest('[data-variant]');
    if (!button) return;
    const v = data.variants.find(v => v.id === button.dataset.variant);
    $('model').value = v.model; $('features').value = v.features; $('normalization').value = v.normalization;
    selectedVariantChanged();
    $('experiment-title').scrollIntoView({behavior: 'smooth', block: 'start'});
  });
  $('download').addEventListener('click', downloadCsv);
  $('diagnostic-policy').addEventListener('change', renderDiagnostics);
  $('diagnostic-account').addEventListener('change', renderAccountDetail);
  selectedVariantChanged();
  renderEnrollment();
  if(window.KEYGUARD_CONTAMINATION){
    $('contamination-target').innerHTML+=window.KEYGUARD_CONTAMINATION.pairs.map(r=>`<option value="${r.target}">${r.target} ← ${r.attacker}</option>`).join('');
  }
  $('contamination-policy').addEventListener('change',renderContamination);
  $('contamination-target').addEventListener('change',renderContamination);
  renderContamination();
  setupStability();
  for(const id of ['adaptation-method','adaptation-partition'])$(id).addEventListener('change',renderAdaptation);
  renderAdaptation();
  setupExternal();
}
