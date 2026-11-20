(() => {
  const root = document.querySelector('.site-search');
  if (!root) return;

  const input = root.querySelector('.site-search-input');
  const results = root.querySelector('.site-search-results');
  const indexUrl = root.dataset.searchIndex;
  let indexPromise = null;
  let visible = [];

  const normal = (value) => String(value || '')
    .toLowerCase()
    .replace(/[_.:/-]+/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();

  const raw = (value) => String(value || '').toLowerCase().trim();

  function loadIndex() {
    if (!indexPromise) {
      indexPromise = fetch(indexUrl)
        .then((response) => {
          if (!response.ok) throw new Error('Search index unavailable');
          return response.json();
        })
        .then((data) => data.entries || []);
    }
    return indexPromise;
  }

  function score(entry, query) {
    const qRaw = raw(query);
    const q = normal(query);
    if (!q) return -1;

    const titleRaw = raw(entry.title);
    const title = normal(entry.title);
    const aliases = entry.aliases || [];
    const aliasRaw = aliases.map(raw);
    const aliasText = normal(aliases.join(' '));
    const haystack = normal([
      entry.title,
      entry.summary,
      entry.keywords,
      aliases.join(' '),
    ].join(' '));

    if (titleRaw === qRaw) return 1000;
    if (aliasRaw.includes(qRaw)) return 920;
    if (title.startsWith(q)) return 820;
    if (aliasText.startsWith(q)) return 760;
    if (title.includes(q)) return 680;
    if (aliasText.includes(q)) return 620;
    if (haystack.includes(q)) return 500;

    const words = q.split(' ').filter(Boolean);
    if (words.length && words.every((word) => haystack.includes(word))) {
      return 380 + words.length * 10;
    }
    return -1;
  }

  function closeResults() {
    results.hidden = true;
    results.replaceChildren();
    input.setAttribute('aria-expanded', 'false');
    visible = [];
  }

  function render(entries, query) {
    const ranked = entries
      .map((entry, order) => ({entry, order, score: score(entry, query)}))
      .filter((row) => row.score >= 0)
      .sort((a, b) => b.score - a.score || a.order - b.order)
      .slice(0, 10);

    results.replaceChildren();
    visible = ranked.map((row) => row.entry);
    if (!ranked.length) {
      const empty = document.createElement('p');
      empty.className = 'site-search-empty';
      empty.textContent = 'No documentation found.';
      results.appendChild(empty);
    } else {
      const indexBase = new URL('.', new URL(indexUrl, document.baseURI));
      ranked.forEach(({entry}) => {
        const link = document.createElement('a');
        link.className = 'site-search-result';
        link.href = new URL(entry.url, indexBase).href;

        const heading = document.createElement('span');
        heading.className = 'site-search-result-title';
        heading.textContent = entry.title;

        const kind = document.createElement('span');
        kind.className = 'site-search-result-kind';
        kind.textContent = entry.kind;

        const summary = document.createElement('span');
        summary.className = 'site-search-result-summary';
        summary.textContent = entry.summary;

        link.append(heading, kind, summary);
        results.appendChild(link);
      });
    }
    results.hidden = false;
    input.setAttribute('aria-expanded', 'true');
  }

  async function search() {
    const query = input.value.trim();
    if (!query) {
      closeResults();
      return;
    }
    try {
      render(await loadIndex(), query);
    } catch (_error) {
      results.replaceChildren();
      const empty = document.createElement('p');
      empty.className = 'site-search-empty';
      empty.textContent = 'Search is unavailable.';
      results.appendChild(empty);
      results.hidden = false;
      input.setAttribute('aria-expanded', 'true');
    }
  }

  input.addEventListener('input', search);
  input.addEventListener('focus', () => {
    if (input.value.trim()) search();
  });
  input.addEventListener('keydown', (event) => {
    if (event.key === 'Escape') {
      closeResults();
      input.blur();
    } else if (event.key === 'Enter' && visible.length) {
      event.preventDefault();
      results.querySelector('.site-search-result')?.click();
    }
  });

  document.addEventListener('click', (event) => {
    if (!root.contains(event.target)) closeResults();
  });

  document.addEventListener('keydown', (event) => {
    const target = event.target;
    const typing = target instanceof HTMLInputElement
      || target instanceof HTMLTextAreaElement
      || target instanceof HTMLSelectElement
      || target?.isContentEditable;
    const shortcut = (event.ctrlKey || event.metaKey)
      && event.key.toLowerCase() === 'k';
    const slash = event.key === '/' && !typing && !event.ctrlKey
      && !event.metaKey && !event.altKey;
    if (shortcut || slash) {
      event.preventDefault();
      input.focus();
      input.select();
    }
  });
})();
