
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
    const cards = [...document.querySelectorAll('.record-card')];
    const count = document.querySelector('.search-count');
    const apply = () => {
      const q = search.value.trim().toLowerCase();
      let visible = 0;
      for (const card of cards) {
        const ok = !q || card.dataset.searchable.includes(q);
        card.hidden = !ok;
        if (ok) visible += 1;
      }
      if (count) count.textContent = `${visible} / ${cards.length} shown`;
    };
    search.addEventListener('input', apply);
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
