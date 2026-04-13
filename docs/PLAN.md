# Plan

## Active
<!-- Current sprint items. Keep this short — 5-10 items max.
     If it grows beyond that, move lower-priority items to Backlog. -->


## Backlog
<!-- Accepted but not yet active. Load this section only when planning or prioritizing. -->
- Open-source model tier: add a separate comparison track for strong open-source models (e.g. Llama, Mistral) — kept distinct from the frontier tier so the comparison framing stays clean
- DeepSeek V3 (China): interesting for Buddhist/Confucian chapters specifically — evaluate once core four models have real content to compare against


## Done
<!-- Completed items land here temporarily.
     The stop hook archives these to .claude/archive/YYYY-MM.md and clears this section. -->
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
