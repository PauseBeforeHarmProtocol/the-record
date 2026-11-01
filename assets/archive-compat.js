/* Small presentation/search repairs for the preserved historical application.
 * Loaded with defer: the historical functions and data exist before this runs,
 * and their DOMContentLoaded initialization uses the repaired functions.
 * No canonical record text, dates, IDs or review states are changed.
 */
(() => {
  if (window.__theRecordArchiveCompatInstalled) return;
  if (typeof window.filtered !== 'function' || typeof window.buildEntry !== 'function') return;
  window.__theRecordArchiveCompatInstalled = true;

  const originalFiltered = window.filtered;
  const searchText = (entry) => {
    const sources = Array.isArray(entry.src) ? entry.src : [];
    return [
      entry.current_id, entry.legacy_id, entry.sort, entry.date, entry.text,
      entry.sig, entry.goal, entry.mt,
      ...(Array.isArray(entry.tags) ? entry.tags : []),
      ...(Array.isArray(entry.institutions) ? entry.institutions : []),
      ...sources.flatMap((source) => typeof source === 'string'
        ? [source]
        : source && typeof source === 'object'
          ? [source.t, source.title, source.name, source.url]
          : []),
    ].filter((value) => value != null).join(' ').toLowerCase();
  };

  window.filtered = function filteredWithStableIDs() {
    const query = srch;
    if (!query) return originalFiltered();
    const words = String(query).trim().toLowerCase()
      .replace(/^#(?=(?:nat|leg)-)/, '').split(/\s+/).filter((word) => word.length > 1);
    // Reuse all original era/year/tag/significance/week filters and ordering.
    // Suppress only the incomplete old text haystack, then restore query state
    // even when the underlying filter fails.
    let candidates;
    try {
      srch = '';
      candidates = originalFiltered();
    } finally {
      srch = query;
    }
    return candidates.filter((entry) => {
      const haystack = searchText(entry);
      return words.every((word) => haystack.includes(word));
    });
  };

  const originalBuildEntry = window.buildEntry;
  window.buildEntry = function buildEntryWithCompleteDate(entry) {
    // The preserved renderer inserts the old tokenized date without escaping.
    // Give it an empty presentation-only copy, then insert the complete escaped
    // label; a label containing </div> must not break the replacement boundary.
    let html = originalBuildEntry({ ...entry, date: '' });
    // Display the explicit stored review state. A correction is not an
    // unreviewed legacy import, and a current ID alone is not proof of review.
    const reviewLabels = {
      'current-standard-reviewed': 'Current-standard reviewed',
      'corrected': 'Corrected · reviewed',
      'current-source-reviewed': 'Source reviewed · Maybe / Therefore pending',
      'in-review': 'In review · not revalidated',
      'needs-sourcing': 'Needs sourcing · not revalidated',
      'legacy-unreviewed': 'Legacy · not revalidated',
      'superseded': 'Superseded duplicate · excluded',
    };
    const state = entry.review_status;
    const reviewed = ['current-standard-reviewed', 'corrected', 'current-source-reviewed'].includes(state);
    const reviewBadge = `<span class="eqastate ${reviewed ? 'reviewed' : 'legacy'}">${escapeHTML(reviewLabels[state] || 'Review state not recorded')}</span>`;
    html = html.replace(/<span class="eqastate [^"]*">[\s\S]*?<\/span>/, () => reviewBadge);
    const label = String(entry.date || entry.sort || '').trim();
    const day = /^([A-Za-z]+)\s+(\d{1,2}),\s*(\d{4})$/.exec(label);
    const approx = entry.dprec && entry.dprec !== 'day'
      ? `<span class="eapprox">≈ ${escapeHTML(entry.dprec)}</span>` : '';
    const body = day
      ? `<span class="eday">${escapeHTML(day[2])}</span>${escapeHTML(day[1])}<br>${escapeHTML(day[3])}`
      : `<span class="edaterange">${escapeHTML(label)}</span>`;
    const badge = `<div class="edate" title="${escapeAttr(label)}">${body}${approx}</div>`;
    return html.replace(/<div class="edate">[\s\S]*?<\/div>/, () => badge);
  };

  if (typeof window.jumpToHash === 'function') {
    window.jumpToHash = function jumpToHashBounded() {
      const fragment = window.location.hash;
      let requestedHash;
      try { requestedHash = decodeURIComponent(fragment.slice(1)); } catch { return; }
      if (!requestedHash) return;
      const superseded = SUPERSEDED_REDIRECTS[requestedHash];
      const hash = superseded?.target || requestedHash;
      const views = ['home', 'topics', 'years', 'timeline', 'politicians', 'ai', 'feed', 'stats', 'methodology', 'about', 'ask'];
      if (views.includes(hash)) { switchView(hash); return; }
      const match = E.find((entry) => (entry.current_id || entry.legacy_id) === hash || `${entry.sort}_${entry._idx}` === hash);
      if (!match) return;

      resetFilters();
      // Keep the original view/filter/count initialization, but suppress its
      // default first-page render. Rendering every preceding page just to reach
      // an old stable ID can create thousands of full cards and freeze phones.
      const originalRenderPage = window.renderPage;
      window.renderPage = () => {};
      try {
        if (currentView !== 'timeline') switchView('timeline');
        else renderStatic();
      } finally {
        window.renderPage = originalRenderPage;
        // Keep the requested fragment even if view initialization fails.
        if (window.location.hash !== fragment) history.replaceState(null, null, fragment);
      }
      const index = currentFiltered.indexOf(match);
      if (index < 0) return;
      currentPage = Math.floor(index / PAGE_SIZE);
      const output = document.getElementById('static');
      output.innerHTML = '';
      renderPage(); // One bounded target page; normal Load more continues here.

      const targetId = match.current_id || match.legacy_id || hash;
      const context = document.createElement('div');
      context.className = 'integrity-note';
      context.innerHTML = `<p>Opened at timeline page ${currentPage + 1} of ${Math.ceil(currentFiltered.length / PAGE_SIZE)} around <code>${escapeHTML(targetId)}</code>. Load more continues from this page.</p>`;
      const start = document.createElement('button');
      start.type = 'button';
      start.className = 'backbtn';
      start.textContent = 'Start of timeline';
      start.addEventListener('click', () => switchView('timeline'));
      context.appendChild(start);
      output.prepend(context);

      document.getElementById('supersededNotice')?.remove();
      const target = document.getElementById(`e-${targetId}`);
      if (!target) return;
      if (superseded) {
        const notice = document.createElement('div');
        notice.id = 'supersededNotice';
        notice.className = 'integrity-note';
        notice.innerHTML = `<h2>Retired duplicate permalink</h2><p><code>${escapeHTML(requestedHash)}</code> remains preserved as a tombstone and is excluded from counts and search. Its canonical record is <a href="#${escapeAttr(targetId)}"><code>${escapeHTML(targetId)}</code></a>. ${escapeHTML(superseded.reason || '')}</p>`;
        target.before(notice);
      }
      target.scrollIntoView({ behavior: 'auto', block: 'center' });
      target.classList.add('permalink-hl');
      setTimeout(() => target.classList.remove('permalink-hl'), 3000);
    };
  }

  const style = document.createElement('style');
  style.textContent = '.edate .edaterange{display:block;font-size:.68rem;line-height:1.5;overflow-wrap:anywhere;white-space:normal}';
  document.head.appendChild(style);
})();
