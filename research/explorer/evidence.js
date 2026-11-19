'use strict';
(() => {
  const data=window.KEYGUARD_EVIDENCE;
  const $=id=>document.getElementById(id);
  const group=$('evidence-group'),source=$('evidence-source'),comparison=$('evidence-comparison');
  const percent=x=>(100*x).toFixed(2).replace('.',',')+'%';
  const pp=x=>x.toFixed(3).replace('.',',');
  const basis={macro_accounts:'Macro · trung bình theo tài khoản',pooled:'Pooled · cộng số đếm',mean_across_splits:'Trung bình 10 cách chia'};
  const roles={control:'Đối chứng',candidate:'Phương án thử',descriptive_reference:'Tham chiếu mô tả',historical_comparison:'So sánh lịch sử'};
  const phases={development_seen_dev:'Phát triển trên DEV đã xem',development_seen_sources:'Phát triển trên nguồn đã xem',
    first_use_new_source_after_method_lock:'Lượt đầu trên nguồn mới, phương pháp đã khóa',
    historical_development_or_initial_external_as_documented:'Mốc lịch sử · xem giao thức nguồn'};
  function options(select,items){
    const previous=select.value;
    select.replaceChildren(...items.map(([value,text])=>{const o=document.createElement('option');o.value=value;o.textContent=text;return o;}));
    if(items.some(([v])=>v===previous))select.value=previous;
  }
  function cell(tr,text){const td=document.createElement('td');td.textContent=text;tr.append(td);return td;}
  function link(name,text){const a=document.createElement('a');a.href='../'+name;a.textContent=text;a.target='_blank';a.rel='noopener noreferrer';return a;}
  function rows(){return data.rows.filter(r=>(group.value==='all'||r.group===group.value)&&(source.value==='all'||r.source===source.value));}
  function render(){
    const selected=rows();
    $('evidence-count').textContent=`${selected.length}/35 dòng kết quả · 11 nhóm có giao thức riêng, không phải 35 thí nghiệm độc lập.`;
    $('evidence-download').textContent=`Tải CSV ${selected.length} dòng đang xem`;
    const groups=Object.entries(data.groups).filter(([k])=>selected.some(r=>r.group===k));
    $('evidence-table').closest('table').classList.toggle('single-group',groups.length===1);
    $('evidence-protocols').replaceChildren(...groups.map(([key,g])=>{
      const details=document.createElement('details');details.open=groups.length===1;
      const summary=document.createElement('summary');summary.textContent=g.title;
      const protocol=document.createElement('p');protocol.textContent=g.protocol;
      const conclusion=document.createElement('p');conclusion.textContent='Kết luận đã chốt: '+g.conclusion;
      details.append(summary,protocol,conclusion);return details;
    }));
    $('evidence-table').replaceChildren(...selected.map(r=>{
      const tr=document.createElement('tr');
      cell(tr,data.groups[r.group].title);cell(tr,r.source);cell(tr,r.variant);
      cell(tr,roles[r.role]);cell(tr,basis[r.metric_basis]);cell(tr,percent(r.far));cell(tr,percent(r.frr));
      const counts=r.genuine_trials===null?'Không cộng qua các cách chia':
        `FA ${r.impostor_accepted}/${r.impostor_trials}; FR ${r.genuine_rejected}/${r.genuine_trials}`;
      cell(tr,counts);
      const provenance=cell(tr,'');provenance.append(link(r.artifact,'Xem kết quả nguồn'));
      const details=document.createElement('details'),summary=document.createElement('summary');summary.textContent='Điều kiện & truy vết';
      const text=document.createElement('p');
      text.textContent=`${phases[r.phase]}. JSON pointer: ${r.pointer}. SHA-256: ${data.source_sha256[r.artifact]}`;
      details.append(summary,text);
      if(r.sd_far!==null){const sd=document.createElement('p');sd.textContent=`SD qua cách chia: FAR ${percent(r.sd_far)}, FRR ${percent(r.sd_frr)}; đây không phải khoảng tin cậy.`;details.append(sd);}
      provenance.append(details);return tr;
    }));
  }
  function groupChanged(){
    const selected=data.rows.filter(r=>group.value==='all'||r.group===group.value);
    options(source,[['all','Tất cả nguồn trong nhóm'],...[...new Set(selected.map(r=>r.source))].map(s=>[s,s])]);render();
  }
  function renderComparison(){
    const c=data.comparisons.find(c=>c.comparison===comparison.value);
    $('evidence-pair').textContent=`${c.comparison} · ${c.accounts} tài khoản đích. Đối chứng: ${c.control}; phương án thử: ${c.candidate}.`;
    const labels={control_far:'FAR đối chứng',control_frr:'FRR đối chứng',candidate_far:'FAR phương án thử',
      candidate_frr:'FRR phương án thử',delta_far:'ΔFAR · phương án thử − đối chứng',delta_frr:'ΔFRR · phương án thử − đối chứng'};
    $('evidence-interval-table').replaceChildren(...Object.entries(c.metrics).map(([key,m])=>{
      const tr=document.createElement('tr');cell(tr,labels[key]);cell(tr,pp(m.estimate_pp));
      cell(tr,`[${pp(m.lower_pp)}; ${pp(m.upper_pp)}]`);
      cell(tr,key.startsWith('delta')?'Điểm phần trăm · âm là giảm lỗi':'Phần trăm');return tr;
    }));
    $('evidence-ci-source').replaceChildren(link(data.uncertainty_artifact,'Kết quả khoảng và toàn bộ hash nguồn'));
  }
  function download(name,records){
    const text=records.map(row=>row.map(v=>'"'+String(v===null?'':v).replaceAll('"','""')+'"').join(',')).join('\r\n')+'\r\n';
    const url=URL.createObjectURL(new Blob(['\ufeff'+text],{type:'text/csv;charset=utf-8'}));
    const a=document.createElement('a');a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
  }
  $('evidence-download').addEventListener('click',()=>{
    const fields=Object.keys(data.rows[0]);download('keyguard-evidence-current-view.csv',[fields,...rows().map(r=>fields.map(k=>r[k]))]);
  });
  $('evidence-ci-download').addEventListener('click',()=>{
    const records=[['comparison','control','candidate','accounts','metric','estimate_pp','lower_pp','upper_pp','artifact']];
    for(const c of data.comparisons)for(const [metric,m]of Object.entries(c.metrics))
      records.push([c.comparison,c.control,c.candidate,c.accounts,metric,m.estimate_pp,m.lower_pp,m.upper_pp,data.uncertainty_artifact]);
    download('keyguard-conditional-intervals.csv',records);
  });
  options(group,[['all','Toàn bộ 11 nhóm'],...Object.entries(data.groups).map(([key,g])=>[key,g.title])]);
  group.value='covariance';group.addEventListener('change',groupChanged);source.addEventListener('change',render);
  options(comparison,data.comparisons.map(c=>[c.comparison,c.comparison]));comparison.addEventListener('change',renderComparison);
  groupChanged();renderComparison();
})();
