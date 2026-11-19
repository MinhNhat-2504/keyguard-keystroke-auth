'use strict';
(() => {
  const panels = [...document.querySelectorAll('[data-research-panel]')];
  const buttons = [...document.querySelectorAll('[data-research-view]')];
  const all = document.getElementById('show-all');
  const status = document.getElementById('view-status');
  function show(name, updateHash = true) {
    if (name !== 'all' && !panels.some(p => p.dataset.researchPanel === name)) name = 'overview';
    for (const panel of panels) panel.hidden = name !== 'all' && panel.dataset.researchPanel !== name;
    for (const button of buttons) button.setAttribute('aria-pressed', String(button.dataset.researchView === name));
    all.setAttribute('aria-pressed', String(name === 'all'));
    const current = buttons.find(b => b.dataset.researchView === name);
    status.textContent = name === 'all' ? 'Đang xem toàn bộ các mục nghiên cứu.' : `Đang xem: ${current.textContent.trim()}. Các lựa chọn thực nghiệm được giữ khi chuyển mục.`;
    if (updateHash) history.replaceState(null, '', '#' + name);
  }
  for (const button of buttons) button.addEventListener('click', () => show(button.dataset.researchView));
  all.addEventListener('click', () => show(all.getAttribute('aria-pressed') === 'true' ? 'overview' : 'all'));
  document.querySelectorAll('[data-open-view]').forEach(button => button.addEventListener('click', () => {
    show(button.dataset.openView);
    document.querySelector('[data-research-panel]:not([hidden]) h2')?.focus({preventScroll: true});
    document.getElementById('research-navigation').scrollIntoView({block: 'start'});
  }));
  window.addEventListener('hashchange', () => show(location.hash.slice(1), false));
  window.KeyGuardViews = Object.freeze({show});
  show(location.hash.slice(1) || 'overview', false);
})();
