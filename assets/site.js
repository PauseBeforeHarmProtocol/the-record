
(() => {
  const toggle = document.querySelector('.nav-toggle');
  const nav = document.querySelector('.primary-nav');
  if (toggle && nav) {
    toggle.addEventListener('click', () => {
      const open = nav.classList.toggle('open');
      toggle.setAttribute('aria-expanded', String(open));
    });
  }

  const search = document.querySelector('[data-record-search]');
  if (search) {
    const cards = [...document.querySelectorAll('[data-searchable]')];
    const count = document.querySelector('.search-count');
    const scopeButtons = [...document.querySelectorAll('[data-week-filter]')];
    let activeScope = 'all';
    const apply = () => {
      const q = search.value.trim().toLowerCase();
      let visible = 0;
      for (const card of cards) {
        const matchesText = !q || card.dataset.searchable.includes(q);
        const matchesScope = activeScope === 'all' || card.dataset.scope === activeScope;
        const ok = matchesText && matchesScope;
        card.hidden = !ok;
        if (ok) visible += 1;
      }
      if (count) count.textContent = `${visible} / ${cards.length} shown`;
    };
    search.addEventListener('input', apply);
    for (const button of scopeButtons) {
      button.addEventListener('click', () => {
        activeScope = button.dataset.weekFilter || 'all';
        for (const candidate of scopeButtons) {
          const selected = candidate === button;
          candidate.setAttribute('aria-pressed', String(selected));
          candidate.classList.toggle('button--primary', selected);
          candidate.classList.toggle('button--ghost', !selected);
        }
        apply();
      });
    }
    apply();
  }

  const toast = document.querySelector('.toast');
  const showToast = (msg) => {
    if (!toast) return;
    toast.textContent = msg;
    toast.classList.add('show');
    setTimeout(() => toast.classList.remove('show'), 1800);
  };

  document.querySelectorAll('.copy-link').forEach((button) => {
    button.addEventListener('click', async () => {
      const fragment = button.dataset.copy || '';
      const url = `${location.href.split('#')[0]}${fragment}`;
      try {
        await navigator.clipboard.writeText(url);
        showToast('Entry link copied');
      } catch {
        showToast('Copy unavailable in this browser');
      }
    });
  });
})();
