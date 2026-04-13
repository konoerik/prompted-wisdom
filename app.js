// app.js — Prompted Wisdom

const MODEL   = 'claude-sonnet-4';
const CHAPTERS = [
  { slug: 'greatest-thinkers',        title: 'What the Greatest Thinkers Taught Us', n: 1  },
  { slug: 'knowing-yourself',         title: 'On Knowing Yourself',                   n: 2  },
  { slug: 'virtue-and-character',     title: 'On Virtue and Character',               n: 3  },
  { slug: 'relationships-and-love',   title: 'On Relationships and Love',             n: 4  },
  { slug: 'work-and-purpose',         title: 'On Work and Purpose',                   n: 5  },
  { slug: 'desire-and-attachment',    title: 'On Desire and Attachment',              n: 6  },
  { slug: 'suffering-and-resilience', title: 'On Suffering and Resilience',           n: 7  },
  { slug: 'time-and-mortality',       title: 'On Time and Mortality',                 n: 8  },
  { slug: 'society-and-place',        title: 'On Society and Your Place in It',       n: 9  },
  { slug: 'happiness',                title: 'On Happiness',                          n: 10 },
  { slug: 'meaning',                  title: 'On Meaning',                            n: 11 },
  { slug: 'letter-to-you',            title: 'A Letter to You',                       n: 12 },
];

let chartsReady = false;

// ── Router ──────────────────────────────────────────────────────────

function route() {
  const hash  = location.hash || '#welcome';
  const parts = hash.replace(/^#/, '').split('/');
  const view  = parts[0] || 'welcome';

  switch (view) {
    case 'welcome': showStatic('welcome'); break;
    case 'about':   showStatic('about');   break;
    case 'stats':
      showStatic('stats');
      if (!chartsReady) { initCharts(); chartsReady = true; }
      break;
    case 'resources': showStatic('resources'); break;
    case 'chapter': {
      const slug = parts[1];
      if (slug) {
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
  ['welcome', 'about', 'stats', 'resources', 'chapter'].forEach(v => {
    document.getElementById('view-' + v).style.display = v === name ? '' : 'none';
  });
}

// ── Chapter loading and rendering ────────────────────────────────────

async function loadChapter(slug) {
  showStatic('chapter');
  const el = document.getElementById('view-chapter');
  el.innerHTML = '<p style="padding:2rem;font-family:var(--font-ui);font-size:0.85rem;color:var(--text-secondary)">Loading\u2026</p>';

  try {
    const res = await fetch(`content/${MODEL}/${slug}.md`);
    if (!res.ok) throw new Error(res.status);
    const raw = await res.text();
    renderChapter(raw, slug);
  } catch (_) {
    renderNotAvailable(slug);
  }
}

function renderChapter(raw, slug) {
  const fmMatch = raw.match(/^---\n([\s\S]*?)\n---\n([\s\S]*)$/);
  if (!fmMatch) { renderNotAvailable(slug); return; }

  const fm      = jsyaml.load(fmMatch[1]);
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
  `;
}

function renderNotAvailable(slug) {
  const chapter = CHAPTERS.find(c => c.slug === slug);
  const title   = chapter ? chapter.title : slug;
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

function buildResourcesHtml(resources) {
  if (!resources) return '';
  const groups = [
    { key: 'read',      label: 'Read' },
    { key: 'listen',    label: 'Listen' },
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
  'Claude':  '#2563eb',
  'GPT-4o':  '#7c3aed',
  'Gemini':  '#0891b2',
  'Mistral': '#059669',
};

async function initCharts() {
  const res   = await fetch('meta/stats.json');
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
  document.getElementById('stat-models').textContent   = stats.summary.models;
  document.getElementById('stat-chapters').textContent = stats.summary.chapters;
  document.getElementById('stat-tokens').textContent   = stats.summary.total_output_tokens.toLocaleString();
  document.getElementById('stat-avg-words').textContent = stats.summary.avg_words_per_chapter;

  const isDark     = document.documentElement.dataset.theme === 'dark';
  const gridColor  = isDark ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.06)';
  const labelColor = isDark ? '#8a8a80' : '#6b6b63';

  Chart.defaults.font.family = "'Inter', system-ui, sans-serif";
  Chart.defaults.font.size   = 12;
  Chart.defaults.color       = labelColor;

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
        data:            stats.by_model.map(m => m.avg_words),
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
        y: { beginAtZero: true, grid: { color: gridColor },
             ticks: { callback: v => v + ' w' } }
      }
    }
  });

  // Chart 2: word count by chapter, grouped by model
  new Chart(document.getElementById('chart-chapters'), {
    type: 'bar',
    data: {
      labels: stats.chapters.map(c => c.label),
      datasets: stats.by_model.map(m => ({
        label:           m.display,
        data:            stats.chapters.map(c => c.word_counts[m.display] ?? 0),
        backgroundColor: MODEL_COLORS[m.display] || '#94a3b8',
        borderRadius: 3,
        borderSkipped: false,
      }))
    },
    options: {
      responsive: true,
      plugins: {
        legend: { position: 'top', align: 'start',
                  labels: { boxWidth: 10, boxHeight: 10, padding: 16 } }
      },
      scales: {
        x: { grid: { display: false } },
        y: { beginAtZero: true, grid: { color: gridColor },
             ticks: { callback: v => v + ' w' } }
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

  window.addEventListener('hashchange', route);
  route();
}

document.addEventListener('DOMContentLoaded', init);
