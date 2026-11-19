'use strict';
(() => {
  const data = window.KEYGUARD_CONTROLS;
  const $ = id => document.getElementById(id);
  const studySelect = $('control-study'), sourceSelect = $('control-source');
  const accountSelect = $('control-account'), basisSelect = $('control-basis');
  const pct = value => (value * 100).toFixed(2).replace('.', ',') + '%';
  const delta = value => (value > 0 ? '+' : '') + (value * 100).toFixed(3).replace('.', ',') + ' điểm %';
  const count = (arm, numerator, denominator) => `${arm[numerator]}/${arm[denominator]}`;
  const labels = {window50:'Cửa sổ 50',decay20:'Trọng số tuổi 20',uniform_cv:'CV đều',age_weighted_cv:'CV theo tuổi',baseline:'MAD gốc',shrink25:'Co MAD 25%'};
  function options(select, rows) {
    const previous = select.value;
    select.replaceChildren(...rows.map(([value, text]) => { const o = document.createElement('option'); o.value = value; o.textContent = text; return o; }));
    if (rows.some(([value]) => value === previous)) select.value = previous;
  }
  function row(values) {
    const tr = document.createElement('tr');
    for (const value of values) { const td = document.createElement('td'); td.textContent = value; tr.append(td); }
    return tr;
  }
  function state() {
    const study = data.studies.find(s => s.key === studySelect.value);
    return {study, dataset: study.datasets.find(d => d.name === sourceSelect.value)};
  }
  function renderAccount() {
    const {dataset} = state();
    const selected = dataset.arms.map(a => ({key:a.key, data:a.accounts.find(x => x.participant_id === accountSelect.value)}));
    $('control-account-table').replaceChildren(...selected.map(a => row([
      labels[a.key] || a.key, count(a.data,'impostor_accepted','impostor_trials'),pct(a.data.far),
      count(a.data,'genuine_rejected','genuine_trials'),pct(a.data.frr)])));
    $('control-account-caption').textContent = `Tài khoản ${accountSelect.value} · cùng mã và mẫu số ở hai nhánh. Khác biệt từng mã không thay tiêu chí chung.`;
  }
  function render() {
    const {study, dataset} = state();
    const c = dataset.comparison, macro = basisSelect.value === 'macro';
    $('control-protocol').textContent = study.protocol;
    $('control-criterion').textContent = `Tiêu chí đã khóa: ${study.primary_rule}. Chọn pooled chỉ đổi cách hiển thị, không đổi tiêu chí hoặc kết luận.`;
    $('control-status').textContent = (c.descriptive_support ? 'Nguồn này đạt chiều cải thiện mô tả.' : 'Nguồn này không đạt tiêu chí đã khóa.') +
      (study.both_sources_support ? ' Cả hai nguồn cùng đạt chiều mô tả.' : ' Chưa có lợi ích nhất quán qua cả hai nguồn.') +
      ' Không có kết luận độ chắc chắn thống kê hoặc hiệu quả triển khai.';
    $('control-status').className = 'status' + (c.descriptive_support ? '' : ' warn');
    $('control-delta').textContent = `Candidate − baseline, luôn theo macro: ΔFAR ${delta(c.delta_macro_far)}; ΔFRR ${delta(c.delta_macro_frr)}. Giảm là ít lỗi hơn.`;
    $('control-basis-label').textContent = macro ? 'Tỉ lệ hiển thị: trung bình theo tài khoản (macro); số đếm là pooled.' : 'Tỉ lệ hiển thị: cộng tử số/mẫu số (pooled). Không gộp giữa nguồn hoặc phép thử.';
    $('control-summary-table').replaceChildren(...dataset.arms.map((a, i) => row([
      `${i===0?'Baseline':'Candidate'} · ${labels[a.key] || a.key}`,
      pct(macro?a.macro_far:a.overall.far),pct(macro?a.macro_frr:a.overall.frr),
      count(a.overall,'impostor_accepted','impostor_trials'), count(a.overall,'genuine_rejected','genuine_trials'),
      String(a.threshold)])));
    options(accountSelect,dataset.arms[0].accounts.map(a => [a.participant_id,a.participant_id]));
    renderAccount();
    $('control-source-link').href = '../' + study.artifact;
    $('control-source-link').textContent = study.artifact;
    $('control-source-hash').textContent = 'SHA-256: ' + study.sha256;
  }
  function selectStudy() {
    const study = data.studies.find(s => s.key === studySelect.value);
    options(sourceSelect,study.datasets.map(d => [d.name,d.name]));
    render();
  }
  options(studySelect,data.studies.map(s => [s.key,s.title]));
  studySelect.addEventListener('change',selectStudy);
  sourceSelect.addEventListener('change',render);
  basisSelect.addEventListener('change',render);
  accountSelect.addEventListener('change',renderAccount);
  $('control-download').addEventListener('click',() => {
    const csv = [['experiment','source','arm','far_macro','frr_macro','far_pooled','frr_pooled','impostor_accepted','impostor_trials','genuine_rejected','genuine_trials','threshold']];
    for (const s of data.studies) for (const d of s.datasets) for (const a of d.arms)
      csv.push([s.key,d.name,a.key,a.macro_far,a.macro_frr,a.overall.far,a.overall.frr,
        a.overall.impostor_accepted,a.overall.impostor_trials,a.overall.genuine_rejected,a.overall.genuine_trials,a.threshold]);
    const text = csv.map(r => r.map(v => '"' + String(v).replaceAll('"','""') + '"').join(',')).join('\r\n')+'\r\n';
    const url=URL.createObjectURL(new Blob(['\ufeff'+text],{type:'text/csv;charset=utf-8'}));
    const link=document.createElement('a');link.href=url;link.download='keyguard-controlled-comparisons.csv';link.click();
    setTimeout(()=>URL.revokeObjectURL(url),1000);
  });
  selectStudy();
})();
