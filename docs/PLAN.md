# Plan

## Active
<!-- Current sprint items. Keep this short — 5-10 items max.
     If it grows beyond that, move lower-priority items to Backlog. -->

### Phase 2: Post-generation polish

**Remaining tasks:**
- Consolidate scripts under Makefile / admin.py — wire generate-all into Make, dynamic prompt version, delete orphaned review.py, clean tests/ retired models, add CLAUDE.md Makefile-first convention (Task #7)

## Backlog
<!-- Accepted but not yet active. Load this section only when planning or prioritizing. -->
- **v1.5 prompt rethink:** revise the output instruction to specify desired markup explicitly (e.g. allow `*italic*` for emphasis, reconsider `##` heading stripping) so format.py post-processing is no longer needed or is scoped only to genuine structural violations — **resolved in v1.5b**
- **Fabricated quotes:** models occasionally invent plausible-sounding but unverifiable direct quotations. Options explored: softening the persona's quotation invitation, adding a self-policing instruction ("quote only if certain, otherwise paraphrase"). Risk of overcorrection — defer until post-generation review reveals true frequency.
- Visual exploration of thinkers and ideas — format TBD: geographic map, timeline, or chart showing relationships/progression across traditions; would complement the chapter content as an at-a-glance reference
- Community insights page — readers post thoughts via GitHub (issue or discussion), author curates and adds them to a page; no backend needed; format TBD
- Methodology page: add "Decisions and trade-offs" section covering — no system prompt (transparency + verifiability), separate prompts per chapter not one session (equal treatment per theme, continuity via shared persona), frontier models only (open-source would dilute framing), single canonical run (no editorial selection between runs), temperature zero (minimise within-model variation), OpenRouter (single interface across models, adds one indirection layer noted in caveats)
- Open-source model tier: add a separate comparison track for strong open-source models (e.g. Llama, Mistral) — kept distinct from the frontier tier so the comparison framing stays clean
- DeepSeek V3 (China): interesting for Buddhist/Confucian chapters specifically — evaluate once core four models have real content to compare against


## Done
<!-- Completed items land here temporarily.
     The stop hook archives these to .claude/archive/YYYY-MM.md and clears this section. -->
- "Compare" framing audited across all pages — replaced "side by side" / "comparison" language with "four independent perspectives" framing
- Chapter × entity heatmap added to Statistics page — stats.py extended with entity_by_chapter; CSS grid heatmap with model tabs
- Manual quote scan across 48 chapters — fabricated quotes flagged in retired models (Gemini 2.0 Flash, Mistral Large); frontier models clean; Commentary updated with attribution notes; v1.5b tagged as full generation
- CLAUDE.md Makefile-first convention added
- v1.5a + v1.5b prompt shipped; all 48 chapters regenerated with frontier models
- format.py extended: numbered-list, book-reference, cross-chapter-reference detection; italic_count separated from markdown_issues
- Scorecard fixed: generated_at filter + deduplication across format runs
- Entity list expanded (Sartre, Camus, Existentialism, etc.); unique entity count added to stats
- meta/review-notes.md scrapped — violation tracking consolidated into format-log.json
- Commentary v1.4 per-model notes written, fact-checked, and formatted (seven-candidate count corrected, typos fixed)
- Sidebar nav restructured into three sections (intro / chapters / extras); Welcome page "Where to go next" nav added with all six destinations
- Word cloud frequencies normalized by total word count per model (client-side in app.js)
- Phase 2 full delivery: 48 chapters regenerated with frontier models; 3 truncated chapters fixed (max_tokens raised to 2000 for gpt-5/mistral-large-3); sidebar updated to new slugs; static pages audited and updated; scripts/format.py built (strips violations, logs to format-log.json); chapter metadata panel added (collapsible prompt/stats/scorecard, after nav, low-profile — ADR-7); meta/review-notes.md generated (32 flagged attribution passages); published to GitHub Pages
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
