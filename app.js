// app.js — Prompted Wisdom

const MODELS = [
  { slug: 'claude-opus-4-6', display: 'Claude' },
  { slug: 'gpt-5', display: 'GPT-5' },
  { slug: 'gemini-2-5-pro', display: 'Gemini' },
  { slug: 'mistral-large-3', display: 'Mistral' },
];

let activeModel = 'claude-opus-4-6';
let activeSlug = null;

const CHAPTERS = [
  { slug: 'greatest-thinkers', title: 'What the Greatest Thinkers Taught Us', n: 1 },
  { slug: 'knowing-yourself', title: 'On Knowing Yourself', n: 2 },
  { slug: 'virtue-and-character', title: 'On Virtue and Character', n: 3 },
  { slug: 'relationships-and-love', title: 'On Relationships and Love', n: 4 },
  { slug: 'work-and-purpose', title: 'On Work and Purpose', n: 5 },
  { slug: 'desire-and-attachment', title: 'On Desire and Attachment', n: 6 },
  { slug: 'suffering-and-resilience', title: 'On Suffering and Resilience', n: 7 },
  { slug: 'time-and-mortality', title: 'On Time and Mortality', n: 8 },
  { slug: 'society-and-place', title: 'On Society and Your Place in It', n: 9 },
  { slug: 'happiness', title: 'On Happiness', n: 10 },
  { slug: 'meaning', title: 'On Meaning', n: 11 },
  { slug: 'letter-to-you', title: 'A Letter to You', n: 12 },
];

let chartsReady = false;

// ── Router ──────────────────────────────────────────────────────────

function route() {
  const hash = location.hash || '#welcome';
  const parts = hash.replace(/^#/, '').split('/');
  const view = parts[0] || 'welcome';

  switch (view) {
    case 'welcome': showStatic('welcome'); break;
    case 'about': showStatic('about'); break;
    case 'stats':
      showStatic('stats');
      if (!chartsReady) { initCharts(); chartsReady = true; }
      break;
    case 'resources': showStatic('resources'); break;
    case 'commentary': showStatic('commentary'); break;
    case 'methodology':
      showStatic('methodology');
      renderMethodologyPage();
      break;
    case 'chapter': {
      const slug = parts[1];
      const modelSlug = parts[2];

      // Normalize old-format URLs (no model slug) → redirect
      if (slug && !modelSlug) {
        location.hash = `#chapter/${slug}/${activeModel}`;
        return;
      }

      if (modelSlug && MODELS.find(m => m.slug === modelSlug)) {
        activeModel = modelSlug;
        updateModelButtons();
        updateChapterHrefs();
      }

      if (slug) {
        activeSlug = slug;
        loadChapter(slug);
      } else {
        showStatic('welcome');
      }
      break;
    }
    default:
      showStatic('welcome');
  }

  updateSidebar(hash);
}

// ── Static views ────────────────────────────────────────────────────

function showStatic(name) {
  ['welcome', 'about', 'stats', 'resources', 'commentary', 'methodology', 'chapter'].forEach(v => {
    document.getElementById('view-' + v).style.display = v === name ? '' : 'none';
  });
}

// ── Model selector ───────────────────────────────────────────────────

function updateChapterHrefs() {
  document.querySelectorAll('a[data-slug]').forEach(a => {
    a.href = `#chapter/${a.dataset.slug}/${activeModel}`;
  });
}

function updateModelButtons() {
  document.querySelectorAll('.model-btn').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.model === activeModel);
  });
}

function setActiveModel(slug) {
  if (!MODELS.find(m => m.slug === slug)) return;
  activeModel = slug;
  updateModelButtons();
  updateChapterHrefs();
  if (activeSlug) {
    location.hash = `#chapter/${activeSlug}/${activeModel}`;
  }
}

// ── Prompt loading ───────────────────────────────────────────────────

let promptMdCache = null;
let formatLogCache = null;

async function fetchPromptMd() {
  if (promptMdCache) return promptMdCache;
  try {
    const res = await fetch('PROMPT.md');
    promptMdCache = res.ok ? await res.text() : '';
  } catch (_) {
    promptMdCache = '';
  }
  return promptMdCache;
}

async function fetchFormatLog() {
  if (formatLogCache) return formatLogCache;
  try {
    const res = await fetch('meta/format-log.json');
    formatLogCache = res.ok ? await res.json() : [];
  } catch (_) {
    formatLogCache = [];
  }
  return formatLogCache;
}

function parsePromptBlock(text, slug) {
  const m = text.match(new RegExp(`<!-- BEGIN:${slug} -->([\\s\\S]*?)<!-- END:${slug} -->`));
  return m ? m[1].trim() : null;
}

// ── Chapter loading and rendering ────────────────────────────────────

async function loadChapter(slug) {
  window.scrollTo(0, 0);
  showStatic('chapter');
  const el = document.getElementById('view-chapter');
  el.innerHTML = '<p style="padding:2rem;font-family:var(--font-ui);font-size:0.85rem;color:var(--text-secondary)">Loading\u2026</p>';

  try {
    const [res, promptMd, formatLog] = await Promise.all([
      fetch(`content/${activeModel}/${slug}.md`),
      fetchPromptMd(),
      fetchFormatLog(),
    ]);
    if (!res.ok) throw new Error(res.status);
    const raw = await res.text();
    renderChapter(raw, slug, promptMd, formatLog);
  } catch (_) {
    renderNotAvailable(slug);
  }
}

function renderChapter(raw, slug, promptMd, formatLog) {
  const fmMatch = raw.match(/^---\n([\s\S]*?)\n---\n([\s\S]*)$/);
  if (!fmMatch) { renderNotAvailable(slug); return; }

  const fm = jsyaml.load(fmMatch[1]);
  const chapter = CHAPTERS.find(c => c.slug === slug);

  // Strip leading title line some models emit (markdown h1 or plain text matching chapter title)
  const body = fmMatch[2].trim()
    .replace(/^#[^\n]*\n+/, '')          // e.g. "# What the Greatest Thinkers..."
    .replace(/^[A-Z][^\n]{0,80}\n+(?=[A-Z])/, '');  // plain title line before first real paragraph

  const paragraphs = body
    .split(/\n\n+/)
    .map((p, i) => `<p${i === 0 ? ' class="lead"' : ''}>${escapeHtml(p.trim())}</p>`)
    .join('\n');

  const el = document.getElementById('view-chapter');
  el.innerHTML = `
    <header class="chapter-header">
      <div class="chapter-eyebrow">Chapter ${fm.chapter ?? (chapter?.n ?? '')}</div>
      <h1 class="chapter-title">${escapeHtml(fm.title)}</h1>
      <div class="chapter-meta">${escapeHtml(fm.model_display)} · ${formatDate(fm.generated_at)}</div>
    </header>
    <div class="chapter-body">${paragraphs}</div>
    ${buildResourcesHtml(fm.resources)}
    ${buildChapterNavHtml(slug)}
    ${buildMetaPanel(slug, fm, body, promptMd, formatLog)}
  `;
}

function renderNotAvailable(slug) {
  const chapter = CHAPTERS.find(c => c.slug === slug);
  const title = chapter ? chapter.title : slug;
  document.getElementById('view-chapter').innerHTML = `
    <header class="chapter-header">
      <h1 class="chapter-title">${escapeHtml(title)}</h1>
      <div class="chapter-meta" style="color:var(--text-placeholder)">Not yet generated.</div>
    </header>
    <div class="chapter-body">
      <p>This chapter has not been generated yet. Check back later.</p>
    </div>
  `;
}

async function renderMethodologyPage() {
  const el = document.getElementById('view-methodology');
  const promptMd = await fetchPromptMd();
  if (!promptMd) {
    el.innerHTML = '<p style="padding:2rem;font-family:var(--font-ui);font-size:0.85rem;color:var(--text-secondary)">Could not load prompt.</p>';
    return;
  }

  const core = parsePromptBlock(promptMd, 'core');

  // Build chapter table rows — extract word target from each block
  const chapterRows = CHAPTERS.map(c => {
    const text = parsePromptBlock(promptMd, c.slug) || '';
    const match = text.match(/Aim for approximately (\d+) words/);
    const words = match ? `~${match[1]}` : '—';
    return `<tr>
      <td>${c.n}</td>
      <td>${escapeHtml(c.title)}</td>
      <td>${words}</td>
    </tr>`;
  }).join('');

  // letter-to-you has a unique instruction beyond the shared template
  const letterBlock = parsePromptBlock(promptMd, 'letter-to-you') || '';

  el.innerHTML = `
    <div class="welcome-wordmark">Methodology</div>
    <h1 class="welcome-hero">How the chapters were made.</h1>
    <div class="welcome-body">
      <p>Each chapter is the output of a single API call: the core persona below, followed by a chapter-specific instruction. No system prompt, no retries, no editorial selection between runs.</p>
    </div>

    <h2 class="about-heading">Generation parameters</h2>
    <div class="model-table-wrap" style="margin-bottom:2rem">
      <table class="model-table">
        <thead><tr><th>Parameter</th><th>Value</th></tr></thead>
        <tbody>
          <tr><td>Temperature</td><td>0</td></tr>
          <tr><td>Max tokens</td><td>1,500 default; per-model overrides (GPT-5 and Mistral: 2,000; Gemini: 8,000 to clear thinking token budget)</td></tr>
          <tr><td>System prompt</td><td><span class="tooltip" data-tip="APIs allow a separate privileged instruction layer before the user message. Not using one means the full prompt is a single transparent user message — identical and verifiable across all models.">None</span></td></tr>
          <tr><td>Runs per chapter</td><td>1 canonical + 1 verification</td></tr>
          <tr><td>API routing</td><td>OpenRouter</td></tr>
        </tbody>
      </table>
    </div>

    <h2 class="about-heading">Core persona</h2>
    <p class="stats-caption">Sent at the start of every call, for every model, for every chapter.</p>
    <div class="prompt-block" style="margin-bottom:2rem">
      <p class="prompt-block-text">${escapeHtml(core || '')}</p>
    </div>

    <h2 class="about-heading">Chapter instructions</h2>
    <p class="stats-caption">Appended after the persona. Chapters 1–11 share the same structure — write a continuous essay, no markdown, follow the thread of influence — varying only in title and word target. Chapter 12 carries a unique closing instruction.</p>
    <div class="model-table-wrap" style="margin-bottom:1.5rem">
      <table class="model-table">
        <thead><tr><th>#</th><th>Chapter</th><th>Word target</th></tr></thead>
        <tbody>${chapterRows}</tbody>
      </table>
    </div>

    <h2 class="about-heading">Chapter 12 — unique instruction</h2>
    <div class="prompt-block" style="margin-bottom:2rem">
      <p class="prompt-block-text">${escapeHtml(letterBlock)}</p>
    </div>

    <h2 class="about-heading">Provenance</h2>
    <ul class="about-method-list">
      <li>Every response stored with model version, generation timestamp, token counts, and a SHA-256 hash of the body</li>
      <li>Hash covers the body only — resources can be updated without invalidating the generation record</li>
      <li>Structural markdown violations (stray headings, bold formatting) are stripped post-generation and every change is logged in <code>meta/format-log.json</code> with the original text preserved</li>
      <li>All prompts version-controlled in <code>PROMPT.md</code> — changes require a new version</li>
      <li>Source code and all content publicly available on <a href="https://github.com/konoerik/prompted-wisdom" target="_blank" rel="noopener">GitHub</a></li>
    </ul>
  `;
}

const THINKER_LIST = [
  'Aristotle', 'Plato', 'Socrates', 'Epictetus', 'Marcus Aurelius', 'Seneca',
  'Confucius', 'Buddha', 'Lao Tzu', 'Zhuangzi', 'Montaigne', 'Epicurus',
  'Nietzsche', 'Camus', 'Sartre', 'Frankl', 'Heidegger', 'Simone Weil',
  'Thoreau', 'Hesiod', 'Aeschylus', 'Hume', 'William James', 'Augustine',
  'Aquinas', 'Spinoza', 'Kant', 'Schopenhauer', 'Kierkegaard',
];

function detectThinkers(body) {
  return THINKER_LIST.filter(name => {
    const escaped = name.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    return new RegExp(`\\b${escaped}\\b`, 'i').test(body);
  });
}

function buildMetaPanel(slug, fm, body, promptMd, formatLog) {
  // ── Full prompt ──
  const core = promptMd ? parsePromptBlock(promptMd, 'core') : null;
  const instruction = promptMd ? parsePromptBlock(promptMd, slug) : null;
  const promptHtml = (core && instruction) ? `
    <div class="meta-prompt-block">
      <div class="meta-prompt-label">Core persona</div>
      <p class="meta-prompt-text">${escapeHtml(core)}</p>
    </div>
    <div class="meta-prompt-block" style="margin-top:0.75rem">
      <div class="meta-prompt-label">Chapter instruction</div>
      <p class="meta-prompt-text">${escapeHtml(instruction)}</p>
    </div>` : '<p class="meta-dim">Prompt unavailable.</p>';

  // ── Statistics ──
  const thinkers = detectThinkers(body);
  const genDate = fm.generated_at ? formatDate(fm.generated_at) : '—';
  const statsHtml = `
    <table class="meta-stats-table">
      <tr><td>Words</td><td>${fm.word_count ?? '—'}</td></tr>
      <tr><td>Tokens in / out</td><td>${fm.token_count_input ?? '—'} / ${fm.token_count_output ?? '—'}</td></tr>
      <tr><td>Model</td><td>${escapeHtml(fm.model ?? '—')}</td></tr>
      <tr><td>Generated</td><td>${genDate}</td></tr>
      <tr><td>Temperature</td><td>${fm.temperature ?? '—'}</td></tr>
      <tr><td>Max tokens</td><td>${fm.max_tokens ?? '—'}</td></tr>
      <tr><td>Prompt version</td><td>${escapeHtml(fm.prompt_version ?? '—')}</td></tr>
      <tr><td>SHA-256</td><td class="meta-hash">${escapeHtml((fm.sha256 ?? '').slice(0, 16))}…</td></tr>
    </table>
    ${thinkers.length ? `<p class="meta-thinkers"><span class="meta-dim">Thinkers mentioned:</span> ${escapeHtml(thinkers.join(', '))}</p>` : ''}`;

  // ── Scorecard ──
  const modelSlug = activeModel;
  const entries = (formatLog || []).filter(e => e.model === modelSlug && e.chapter === slug);
  const scorecardHtml = entries.length
    ? entries.map(e => `<div class="meta-scorecard-item meta-scorecard-item--warn">
        <span class="meta-scorecard-type">${escapeHtml(e.violation)}</span>
        <span class="meta-dim">line ${e.line} — </span>${escapeHtml(e.original)}
      </div>`).join('')
    : '<div class="meta-scorecard-item meta-scorecard-item--ok">No issues logged.</div>';

  return `
    <div class="chapter-meta-panel">
      <details class="meta-section">
        <summary class="meta-summary">prompt</summary>
        <div class="meta-content">${promptHtml}</div>
      </details>
      <details class="meta-section">
        <summary class="meta-summary">statistics</summary>
        <div class="meta-content">${statsHtml}</div>
      </details>
      <details class="meta-section">
        <summary class="meta-summary">scorecard</summary>
        <div class="meta-content">${scorecardHtml}</div>
      </details>
    </div>`;
}

function buildChapterNavHtml(slug) {
  const idx = CHAPTERS.findIndex(c => c.slug === slug);
  const prev = CHAPTERS[idx - 1];
  const next = CHAPTERS[idx + 1];

  if (!prev && !next) return '';

  const prevHtml = prev
    ? `<a class="chapter-nav-card chapter-nav-card--prev" href="#chapter/${prev.slug}/${activeModel}">
        <span class="chapter-nav-label">← Previous</span>
        <span class="chapter-nav-title">${escapeHtml(prev.title)}</span>
      </a>`
    : '<span></span>';

  const nextHtml = next
    ? `<a class="chapter-nav-card chapter-nav-card--next" href="#chapter/${next.slug}/${activeModel}">
        <span class="chapter-nav-label">Next →</span>
        <span class="chapter-nav-title">${escapeHtml(next.title)}</span>
      </a>`
    : '<span></span>';

  return `<nav class="chapter-nav">${prevHtml}${nextHtml}</nav>`;
}

function buildResourcesHtml(resources) {
  if (!resources) return '';
  const groups = [
    { key: 'read', label: 'Read' },
    { key: 'listen', label: 'Listen' },
    { key: 'reference', label: 'Essays &amp; References' },
  ];

  const groupsHtml = groups
    .filter(g => resources[g.key]?.length)
    .map(g => `
      <div class="resource-group">
        <div class="resource-group-label">${g.label}</div>
        <ul class="resource-list">
          ${resources[g.key].map(r =>
      `<li><a href="${r.url}" target="_blank" rel="noopener">${escapeHtml(r.title)}</a>` +
      `<span class="resource-source">${escapeHtml(r.source)}</span></li>`
    ).join('')}
        </ul>
      </div>
    `).join('');

  if (!groupsHtml.trim()) return '';
  return `
    <aside class="resources">
      <div class="resources-heading">Go deeper</div>
      <div class="resources-grid">${groupsHtml}</div>
    </aside>
  `;
}

// ── Sidebar active state ─────────────────────────────────────────────

function updateSidebar(hash) {
  document.querySelectorAll('.chapter-item').forEach(li => {
    const a = li.querySelector('a');
    if (!a) return;
    const href = a.getAttribute('href');
    li.classList.toggle('active', href === hash);
  });
}

// ── Theme ────────────────────────────────────────────────────────────

function toggleTheme() {
  const next = document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark';
  document.documentElement.dataset.theme = next;
  localStorage.setItem('pw-theme', next);
}

// ── Charts (statistics page) ─────────────────────────────────────────

const MODEL_COLORS = {
  'Claude': '#2563eb',
  'GPT-4o': '#7c3aed',
  'Gemini': '#0891b2',
  'Mistral': '#059669',
};

async function initCharts() {
  const res = await fetch('meta/stats.json');
  const stats = await res.json();

  // Populate model registry table
  const tbody = document.getElementById('model-registry-body');
  tbody.innerHTML = stats.by_model.map(m => `
    <tr>
      <td class="model-table-name">${escapeHtml(m.display)}</td>
      <td class="model-table-id">${escapeHtml(m.model_id)}</td>
      <td>${escapeHtml(m.provider)}</td>
      <td>${m.avg_words} w</td>
    </tr>
  `).join('');

  // Populate summary cards
  document.getElementById('stat-models').textContent = stats.summary.models;
  document.getElementById('stat-chapters').textContent = stats.summary.chapters;
  document.getElementById('stat-tokens').textContent = stats.summary.total_output_tokens.toLocaleString();
  document.getElementById('stat-avg-words').textContent = stats.summary.avg_words_per_chapter;

  const isDark = document.documentElement.dataset.theme === 'dark';
  const gridColor = isDark ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.06)';
  const labelColor = isDark ? '#8a8a80' : '#6b6b63';

  Chart.defaults.font.family = "'Inter', system-ui, sans-serif";
  Chart.defaults.font.size = 12;
  Chart.defaults.color = labelColor;

  // Word clouds
  const wcGrid = document.getElementById('wordcloud-grid');
  wcGrid.innerHTML = stats.by_model.map(m =>
    `<div class="wordcloud-panel">
       <div class="wordcloud-model">${escapeHtml(m.display)}</div>
       <canvas class="wordcloud-canvas" data-model="${escapeHtml(m.slug)}"></canvas>
     </div>`
  ).join('');

  const wcIsDark = document.documentElement.dataset.theme === 'dark';
  stats.by_model.forEach(m => {
    const canvas = wcGrid.querySelector(`canvas[data-model="${m.slug}"]`);
    if (!canvas || !m.word_freq?.length) return;
    const w = canvas.parentElement.clientWidth - 40;
    canvas.width = w;
    canvas.height = 240;
    const totalWords = m.word_counts.reduce((s, n) => s + n, 0) || 1;
    WordCloud(canvas, {
      list: m.word_freq.map(({ word, count }) => [word, count / totalWords * 10000]),
      gridSize: 8,
      weightFactor: w / 480,
      fontFamily: 'Inter, system-ui, sans-serif',
      color: wcIsDark ? 'random-light' : 'random-dark',
      rotateRatio: 0.3,
      rotationSteps: 2,
      backgroundColor: 'transparent',
    });
  });

  // Populate entity grid
  document.getElementById('entities-grid').innerHTML = stats.by_model.map(m => `
    <div class="entities-col">
      <div class="entities-model">${escapeHtml(m.display)}</div>
      <ol class="entities-list">
        ${m.top_entities.map(e => `
          <li class="entities-item">
            <span class="entities-name">${escapeHtml(e.name)}</span>
            <span class="entities-count">${e.count}</span>
          </li>
        `).join('')}
      </ol>
    </div>
  `).join('');

  // Chart 1: average words per model
  new Chart(document.getElementById('chart-avg'), {
    type: 'bar',
    data: {
      labels: stats.by_model.map(m => m.display),
      datasets: [{
        data: stats.by_model.map(m => m.avg_words),
        backgroundColor: stats.by_model.map(m => MODEL_COLORS[m.display] || '#94a3b8'),
        borderRadius: 4,
        borderSkipped: false,
      }]
    },
    options: {
      responsive: true,
      plugins: { legend: { display: false } },
      scales: {
        x: { grid: { display: false } },
        y: {
          beginAtZero: true, grid: { color: gridColor },
          ticks: { callback: v => v + ' w' }
        }
      }
    }
  });

  // Chart 2: word count by chapter, grouped horizontal bars
  new Chart(document.getElementById('chart-chapters'), {
    type: 'bar',
    data: {
      labels: stats.chapters.map(c => c.label),
      datasets: stats.by_model.map(m => ({
        label: m.display,
        data: stats.chapters.map(c => c.word_counts[m.display] ?? 0),
        backgroundColor: MODEL_COLORS[m.display] || '#94a3b8',
        borderRadius: 2,
        borderSkipped: false,
        barThickness: 6,
      }))
    },
    options: {
      indexAxis: 'y',
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'top', align: 'start',
          labels: { boxWidth: 10, boxHeight: 10, padding: 16 }
        }
      },
      scales: {
        x: {
          beginAtZero: true, grid: { color: gridColor },
          ticks: { callback: v => v + ' w' }
        },
        y: { grid: { display: false } }
      }
    }
  });
}

// ── Helpers ──────────────────────────────────────────────────────────

function escapeHtml(str) {
  if (str == null) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function formatDate(iso) {
  if (!iso) return '';
  const d = new Date(iso);
  return d.toLocaleDateString('en-US', { month: 'long', year: 'numeric' });
}

// ── Init ─────────────────────────────────────────────────────────────

function init() {
  const saved = localStorage.getItem('pw-theme');
  if (saved) document.documentElement.dataset.theme = saved;

  document.querySelector('.theme-toggle').addEventListener('click', toggleTheme);

  const sidebar = document.querySelector('.sidebar');
  const navToggle = document.querySelector('.nav-toggle');
  navToggle.addEventListener('click', () => {
    const open = sidebar.classList.toggle('sidebar--open');
    navToggle.setAttribute('aria-expanded', open);
    navToggle.querySelector('.nav-toggle-icon').textContent = open ? '✕' : '☰';
  });

  document.querySelectorAll('.chapter-item a').forEach(a => {
    a.addEventListener('click', () => {
      sidebar.classList.remove('sidebar--open');
      navToggle.setAttribute('aria-expanded', 'false');
      navToggle.querySelector('.nav-toggle-icon').textContent = '☰';
    });
  });

  document.querySelectorAll('.model-btn').forEach(btn => {
    btn.addEventListener('click', () => setActiveModel(btn.dataset.model));
  });

  updateChapterHrefs(); // Set initial hrefs before first route()

  fetch('meta/site.json')
    .then(r => r.json())
    .then(site => {
      const label = document.querySelector('.prompt-version-label');
      if (label && site.prompt_version) label.textContent = 'prompt ' + site.prompt_version;
    })
    .catch(() => { });

  window.addEventListener('hashchange', route);
  route();
}

document.addEventListener('DOMContentLoaded', init);
