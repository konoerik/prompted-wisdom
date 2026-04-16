# Plan

## Active
<!-- Current sprint items. Keep this short — 5-10 items max.
     If it grows beyond that, move lower-priority items to Backlog. -->

### Phase 2: Frontier model upgrade + full regeneration

**Model decisions (locked ✓):**
- Claude slot: Claude Opus 4.6 (`claude-opus-4-6`)
- GPT slot: GPT-5.4 (`gpt-5`)
- Gemini slot: Gemini 2.5 Pro (`gemini-2-5-pro`); max_tokens=8000 in models.json
- Mistral slot: Mistral Large 3 (`mistral-large-3`)

**Generation parameters (locked ✓):**
- Prompt: v1.4 (chapter list; no further changes for this run)
- Temperature: 0 for all models including Gemini 2.5 Pro
- Word targets: 900 / 700 / 450 (unchanged from v1.3b)
- Max tokens: 1500 default; 8000 for Gemini 2.5 Pro

**Recurring issues documented from v1.3b/v1.4 testing:**
- Gemini 2.0 Flash: deterministic opening pattern ("X. It's a..."), near-identical structure across chapters, short word count, no improvement with chapter list
- GPT-4o: default textbook-survey shape ("common thread emerges"), chapter list had marginal effect, quotes used as decoration not argument
- Mistral Large 2411: verbose, Frankl/meaning bled into unrelated chapters, excess word count
- All resolved or significantly improved in frontier model versions

**Regeneration tasks:**
- Run `make estimate` first — confirm cost and that account has sufficient funds
- Regenerate all 48 chapters (12 × 4 models) with v1.4 prompt
- Update Commentary v1.4 with per-model notes after reading output
- Re-run stats.py and update stats.json
- Tag v1.4 content in git

**Pricing reference (OpenRouter, per 1M tokens):**

| Model | In $/1M | Out $/1M | 12 chapters |
|---|---|---|---|
| Claude Sonnet 4.5 (current) | $3.00 | $15.00 | $0.098 |
| Claude Sonnet 4.6 | $3.00 | $15.00 | $0.098 |
| Claude Opus 4.6 | $5.00 | $25.00 | $0.176 |
| GPT-4o (current) | $2.50 | $10.00 | $0.065 |
| GPT-5.4 | $2.50 | $15.00 | $0.098 |
| Gemini 2.0 Flash (current) | $0.10 | $0.40 | $0.002 |
| Gemini 2.5 Pro | $1.25 | $10.00 | $0.258 |
| Mistral Large 2411 (current) | $2.00 | $6.00 | $0.055 |
| Mistral Large 3 | $0.50 | $1.50 | $0.012 |

Full frontier run (Sonnet 4.6): ~$0.47 · Full frontier run (Opus 4.6): ~$0.54

## Backlog
<!-- Accepted but not yet active. Load this section only when planning or prioritizing. -->
- Visual exploration of thinkers and ideas — format TBD: geographic map, timeline, or chart showing relationships/progression across traditions; would complement the chapter content as an at-a-glance reference
- Community insights page — readers post thoughts via GitHub (issue or discussion), author curates and adds them to a page; no backend needed; format TBD
- Methodology page: add "Decisions and trade-offs" section covering — no system prompt (transparency + verifiability), separate prompts per chapter not one session (equal treatment per theme, continuity via shared persona), frontier models only (open-source would dilute framing), single canonical run (no editorial selection between runs), temperature zero (minimise within-model variation), OpenRouter (single interface across models, adds one indirection layer noted in caveats)
- Open-source model tier: add a separate comparison track for strong open-source models (e.g. Llama, Mistral) — kept distinct from the frontier tier so the comparison framing stays clean
- DeepSeek V3 (China): interesting for Buddhist/Confucian chapters specifically — evaluate once core four models have real content to compare against


## Done
<!-- Completed items land here temporarily.
     The stop hook archives these to .claude/archive/YYYY-MM.md and clears this section. -->
- Phase 2 infrastructure: models.json updated (4 frontier models approved, 4 retired); generate.py per-model max_tokens override; Commentary v1.4 experiment block added; ADR-6 recorded; all generation parameters locked
- v1.4 prompt experiment: chapter list added to core persona; 4 test chapters × 7 model candidates evaluated; frontier models selected (ADR-6)
- Commentary page — built card layout, version block template, per-version notes for all four models across v1.3b; v1.3a block added; "Author's Commentary" heading; CSS card styling
- Methodology page: prompt (persona + chapter table), generation parameters, provenance; trimmed About; in-chapter prompt disclosure; CSS tooltip on system prompt
- Verified and fixed all 8 broken LibriVox links on Resources page
- Mobile layout: collapsible hamburger nav; `make serve-mobile` added for local network testing
- Next/previous chapter navigation cards (two-column, themed, with chapter title)
- Word cloud on Statistics page: packed canvas layout via wordcloud2.js (CDN); frequencies pre-computed in stats.py, no runtime cost
- Deployed to GitHub Pages: added .nojekyll to fix .md fetch interception by Jekyll; site live at konoerik.github.io/prompted-wisdom
- GitHub Pages readiness: favicon (SVG), meta description, Open Graph + Twitter card tags, robots index
- Added Makefile (install, serve, stats, generate, freeze) and requirements.txt
- Fixed Resources page stubs: direct Gutenberg ebook IDs + best-guess LibriVox slugs (manual check pending)
- Refactored stats chart to grouped horizontal bars; fixed maintainAspectRatio gap; tuned bar thickness
- Added Foreword section to About page with warm amber styling; formatted and spell-checked author's text
- Dropped "ten themes" count from Welcome copy
- Implemented hybrid model toggle: sidebar selector + model slug in URL (`#chapter/slug/model-slug`); select once to read all chapters in a model; shareable per-model links; old-format URLs auto-redirect
- Updated statistics page with real data: stats.py script, stats.json, model registry table, thinker/tradition entity grid
- Updated About page caveats: all-model non-determinism, instruction-following failures documented
- Reviewed and updated welcome page (shortened, broadened scope beyond ancient wisdom)
- Reviewed and updated about page (personal note placeholder, trimmed methodology to bullets, added limitations & caveats, removed contributing placeholder)
- Reviewed and restructured chapter listing to 12 chapters (added virtue-and-character, split happiness/meaning, renamed desire-and-attachment)
- Built Resources page with compact one-line entries and emoji icon links
- Generated all 48 chapters (12 × 4 models: Claude, GPT-4o, Gemini, Mistral)
- Added links to book resources (Resources page)
- Chose modern clean theme (Inter + Lora, CSS custom properties); parchment prototype parked
- Locked content format: .md files with YAML frontmatter, SHA-256 hash of body only
- Locked prompt storage: Option A — verbatim prompts in PROMPT.md with HTML comment delimiters
- Locked generation methodology: temp=0, max_tokens=1500, validate.py + generate.py in /scripts
- Locked model approval registry: models.json controls which models can contribute
- Built Welcome view integrated into sidebar as default entry point
- Built About page as sidebar nav item grouped with Welcome
- Set subtitle to "Ancient ideas, machine-rendered."
- Recorded ADR-1 (theme), ADR-2 (content format/methodology), ADR-3 (scripts/validation)
- Built statistics page with Chart.js — summary cards, two charts, placeholder data
- Locked core prompt and all 10 chapter prompts into PROMPT.md with HTML comment delimiters
- Decided: no section headings, continuous essay, influence-thread vector for all chapters
- Closing letter gets distinct instruction (synthesising address, not a chapter)
- Set up GitHub repo (konoerik/prompted-wisdom); added README, CC BY 4.0 LICENSE, .gitignore
- Filled About page GitHub link and author name (Erikton Konomi); removed parchment prototype files
- Removed model-switcher feature entirely; simplified to Claude-only with `#chapter/slug` URLs
