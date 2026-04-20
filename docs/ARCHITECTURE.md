# Architecture

## Quick Reference
**Stack:** HTML, CSS, vanilla JS — no build step
**Entry point:** `index.html`
**Styles:** `style.css`
**Logic:** `app.js`
**Libraries:** Chart.js 4.x (CDN), js-yaml 4.x (CDN), wordcloud2.js 1.x (CDN)
**Scripts:** `scripts/generate.py` (content generation), `scripts/stats.py` (aggregates stats.json from content files)
**Data:** `meta/stats.json` fetched at runtime by `app.js`; `content/<model-slug>/<chapter-slug>.md` fetched on chapter navigation; `meta/models.json` read by Python scripts only
**Dev tooling:** `Makefile` (install, serve, stats, estimate, generate, freeze targets); `requirements.txt` (pinned Python deps for scripts)
**Key constraint:** CDN imports only; run via `make serve` or `python3 -m http.server` if loading local files

**Generation costs** (OpenRouter, last checked 2026-04-15 — update `meta/models.json` pricing fields when rates change, then `make estimate` reflects the new numbers automatically):

| Model | Slug | In $/1M | Out $/1M | 12 chapters |
|---|---|---|---|---|
| Claude Opus 4.6 | `claude-opus-4-6` | $5.00 | $25.00 | ~$0.17 |
| GPT-5.4 | `gpt-5` | $2.50 | $15.00 | ~$0.10 |
| Gemini 2.5 Pro | `gemini-2-5-pro` | $1.25 | $10.00 | ~$0.26 |
| Mistral Large 3 | `mistral-large-3` | $0.50 | $1.50 | ~$0.01 |

Full 48-chapter run: **~$0.54** · Run `make estimate` before each regeneration to confirm with live model config.


## Decisions (ADRs)
<!-- Append new ADRs with /log -->

### ADR-9: Italic rendering split — format.py detects, app.js converts
**Date:** 2026-04-20
**Context:** v1.5b permitted `*italic*` in model output for titles, foreign terms, and light emphasis. The existing pipeline had format.py converting `*italic*` → `<em>italic</em>` and writing that HTML back into the `.md` files, with app.js un-escaping it at render time. This stored HTML fragments inside markdown files, conflating post-processing with the content storage format and making the files harder to read as plain text.
**Decision:** format.py detects italic instances and logs them (counted as `italic_count` in frontmatter, recorded in `format-log.json`) but leaves `.md` files untouched. app.js converts `*italic*` → `<em>italic</em>` at render time via a single regex. Content files remain pure markdown throughout the pipeline.
**Alternatives considered:** Keep format.py converting to `<em>` and storing HTML in `.md` files — rejected: conflates storage format with display concerns, files no longer readable as plain markdown. Use `marked.js` (CDN markdown renderer) in app.js — rejected: would render all markdown including disallowed elements (headings, lists, bold), undermining format.py's structural violation guard. Move conversion to a separate build step — rejected: project has no build step by design (ADR-2).
**Consequences:** SHA-256 hashes remain valid against the stored body since format.py no longer modifies italic lines. format.py's role is cleanly split: fix structural violations, detect-but-preserve permitted elements. Any future permitted markdown element should follow the same pattern — detect and count in format.py, render in app.js. The `italic_count` frontmatter field is separate from `markdown_issues` to reflect this distinction.

### ADR-8: SHA-256 provenance — original AI output hash, never rewritten by post-processing
**Date:** 2026-04-18
**Context:** `format.py` was recomputing `sha256` after every formatting fix (stripping structural markdown violations, converting `*italic*` to `<em>`), replacing the hash of the original AI output with a hash of the cleaned body. This broke the provenance guarantee: the `sha256` field is meant to let readers verify exactly what the model produced, not what the site chooses to display.
**Decision:** `sha256` is set once by `generate.py` on the raw API response body (`.strip()`-trimmed) and is never touched again. `format.py` may edit the body for readability but must not update `sha256`. `word_count` is still updated by `format.py` (it is a convenience field, not a provenance claim). The generation-time sha256 for all v1.4 chapters is anchored at commit `ac65665` (or `23b8b02` for the three chapters regenerated due to truncation).
**Alternatives considered:** Update sha256 to reflect the canonical/formatted body — rejected: conflates "what the AI said" with "what we chose to display", undermining the integrity proof. Add a parallel `sha256_canonical` field for the post-processed version — rejected: unnecessary complexity; the body in the file is the readable truth and the hash is the provenance proof, they serve different purposes and need not match.
**Consequences:** The sha256 in a file will not match the current body byte-for-byte after formatting edits. Verification requires fetching the original body from git at the generation commit (`git show ac65665:content/<model>/<chapter>.md`). Any future post-processing script must be written with this constraint in mind — editing the body is permitted, updating sha256 is not.

### ADR-7: Chapter metadata panel — collapsible prompt, statistics, and scorecard
**Date:** 2026-04-16
**Context:** The existing chapter page had a single `<details>` element at the bottom showing only the chapter instruction, with a note pointing readers to the Methodology page for the core persona. This was incomplete and not self-contained: a reader curious about provenance had to navigate away. The phase 2 content also introduced `meta/format-log.json` (post-generation correction log) and an upcoming editorial review pass, making a structured per-chapter scorecard worth surfacing. The goal was to expose full provenance, generation statistics, and issue tracking without disrupting the reading experience.
**Decision:** Replace the single prompt disclosure with a three-section metadata panel placed after the chapter navigation cards (body → resources → nav → panel). Each section is a `<details>` element, all closed by default. The panel renders at 60% opacity and fades to full on hover, keeping it visually subordinate. Sections: (1) **Prompt** — core persona + chapter instruction stacked, both verbatim from `PROMPT.md`; (2) **Statistics** — word count, token counts, model ID, generation date, temperature, max tokens, SHA-256 prefix, and thinkers detected in the chapter body via client-side regex against a curated list; (3) **Scorecard** — filtered entries from `meta/format-log.json` for the current model + chapter, or "No issues logged" if clean. `meta/format-log.json` is fetched once and cached alongside `PROMPT.md`.
**Alternatives considered:** Keeping the single prompt disclosure and adding a separate statistics block — rejected: fragmentary, still doesn't solve the incomplete prompt problem. A dedicated provenance page per chapter — rejected: multiplies page count, breaks the single-page architecture. Embedding statistics in the chapter header — rejected: clutters the reading entry point; metadata belongs at the end.
**Consequences:** `meta/format-log.json` must be kept accurate — it is now reader-visible. The scorecard will be extended with `editorial` violation type once the review pass (Task #4) is complete. Thinker detection is client-side and approximate; it can produce false positives if a thinker's name appears in a different context, but this is acceptable for a metadata panel. The `buildMetaPanel` function in `app.js` is the single place to extend when new scorecard categories are added.

### ADR-6: Phase 2 model lineup — full frontier upgrade
**Date:** 2026-04-15
**Context:** After completing the v1.3b read across all four models and running the v1.4 prompt experiment (chapter list addition), it was clear that structural quality issues in GPT-4o, Gemini 2.0 Flash, and Mistral Large 2411 were not solvable by prompt iteration alone. GPT-4o defaulted to a textbook-survey shape regardless of the chapter list. Gemini 2.0 Flash had a deterministic opening pattern ("X. It's a...") that persisted across all versions and produced near-identical structure between v1.0 and v1.3b. Mistral Large 2411 was verbose, exceeded word targets, and bled Viktor Frankl into chapters where he does not belong. Claude Sonnet 4.5 produced clean output but a newer version (4.6) and a more capable model (Opus 4.6) were available at comparable cost. A full 48-chapter run at frontier pricing costs $0.47–$0.54 total, making cost a non-factor.
**Decision:** Retire all four current models and replace with frontier equivalents for phase 2 content regeneration:
- Claude Sonnet 4.5 → Claude Opus 4.6 (`anthropic/claude-opus-4.6`, slug: `claude-opus-4-6`)
- GPT-4o → GPT-5.4 (`openai/gpt-5.4`, slug: `gpt-5`)
- Gemini 2.0 Flash → Gemini 2.5 Pro (`google/gemini-2.5-pro`, slug: `gemini-2-5-pro`)
- Mistral Large 2411 → Mistral Large 3 (`mistralai/mistral-large-2512`, slug: `mistral-large-3`)

Per-model `max_tokens` override added to `models.json` and honoured in `generate.py` via a new `generation_params(model)` helper. Gemini 2.5 Pro requires `max_tokens: 8000` to clear its internal thinking token budget before producing prose output (default 1500 caused truncation after ~50 words).

**Alternatives considered:** Upgrading only the underperforming models (GPT and Gemini) while keeping Claude Sonnet 4.5 and Mistral Large 2411 — rejected: Sonnet 4.6/Opus 4.6 is a free or near-free upgrade, and Mistral Large 3 is actually 4× cheaper than 2411 while producing better output. Adding new models as a fifth/sixth slot rather than replacing — rejected: the project's four-way comparison framing is a deliberate constraint; expanding the model count would require significant UI work and dilute the focus.

**Consequences:** All 48 chapters must be regenerated. Content directories for retired models (`claude-sonnet-4/`, `gpt-4o/`, `gemini-2-flash/`, `mistral-large/`) will be replaced by new slugs. Commentary page needs v1.4 blocks for all four new models. `stats.py` must be re-run. Git tag should be applied after regeneration. `generate.py` default model arg updated to `claude-opus-4-6`.

### ADR-5: Git tags mark prompt version boundaries
**Date:** 2026-04-14
**Context:** The prompt evolved through several iterations (v1.0 → v1.3b) before content was finalised. Keeping multiple rendered versions of 48+ chapters in the live site would require UI complexity and multiply the content surface. The project needs a way to let readers or contributors compare prompt versions without that overhead.
**Decision:**
- Each time the canonical prompt changes and all chapters are regenerated, a git tag is created whose name matches the `prompt_version` field written into every content file's frontmatter (e.g. `v1.0`, `v1.3b`).
- The live site always reflects the latest canonical prompt. Prior versions are accessible by checking out the corresponding tag and running the site locally (`git checkout v1.0 && npx serve`).
- **Tag before regenerating** — the prior version must be tagged while it is still the HEAD content, so the reference point is never lost.
- Tag names must match exactly the string passed to `generate.py --prompt-version`. No aliases or synonyms.

**Alternatives considered:** Rendering all prompt versions in the UI as a third axis alongside model and chapter — rejected: multiplies rendered content, requires significant UI work, and frames the project as a lab notebook rather than a readable guide. Storing prior content in a separate branch — rejected: harder to discover and checkout than a tag.

**Consequences:** Regeneration is a deliberate, versioned event, not an incremental edit. The `--prompt-version` flag in `generate.py` must be set correctly on every generation run. Anyone cloning the repo can reproduce any prior version of the site exactly.

### ADR-4: Build-time statistics pipeline via stats.py → meta/stats.json
**Date:** 2026-04-12
**Context:** The statistics page needs word counts, token totals, model metadata, and thinker/tradition mention counts derived from all generated content files. Doing this at runtime in the browser would require fetching and parsing 48 markdown files on page load.
**Decision:**
- `scripts/stats.py` reads all content files and `meta/models.json`, aggregates the data, and writes `meta/stats.json`.
- `app.js` fetches `meta/stats.json` once when the statistics view is first opened and drives all cards, charts, and the entity grid from it.
- `stats.py` must be re-run manually after any new chapters are generated. It is not automated.
- Thinker/tradition mention counts use a curated entity list with case-insensitive whole-word matching across chapter bodies (frontmatter excluded). Top 5 per model are stored in `stats.json`.

**Alternatives considered:** Runtime aggregation in the browser — rejected: too slow, requires fetching all 48 content files. Hardcoded values — rejected: breaks every time content is regenerated.

**Consequences:** `meta/stats.json` must be committed alongside content changes or the statistics page will show stale data. The entity list in `stats.py` is the single place to add new thinkers for tracking.

### ADR-3: Generation scripts, validation pipeline, and model approval registry
**Date:** 2026-04-10
**Context:** The project needs a reproducible generation workflow and a trustworthy contribution pipeline, especially if community PRs are accepted. Methodology integrity must be enforced mechanically, not just by convention.
**Decision:**
- **Two scripts** in `/scripts`: `generate.py` (for authors) and `validate.py` (for contributors and CI).
- `generate.py` reads `PROMPT.md` verbatim, calls the API with fixed parameters, hashes the body, writes the `.md` content file including `temperature` and `max_tokens` in frontmatter.
- `validate.py` checks: all required frontmatter fields present; `content_hash` matches actual SHA-256 of the body; `temperature: 0` and `max_tokens: 1500` match expected values; `model_version` is in the approved list in `models.json`; body has a lead paragraph and at least one `##` section; no disallowed markdown (`**bold**`, `- lists`, `###` nested headings).
- `validate.py` runs as a **GitHub Action** on every PR touching `content/` — a failed check blocks the merge automatically.
- **Model approval registry:** `models.json` is the authoritative list of approved models. Contributions from models not in the registry are rejected by the validator. Each entry includes `approved: true` and a `min_capability_note`. Adding a new model is a deliberate editorial act by the maintainer.
- `generate.py` supports a `--list-models` flag showing currently approved models, so contributors don't have to read the JSON directly.

**Alternatives considered:** Trusting contributors to self-report parameters correctly — rejected, too error-prone and undermines provenance. Automated capability scoring — rejected, too complex and subjective; the approved registry is a simpler and more defensible gate.

**Consequences:** `models.json` is a living document — new frontier models are added as they are evaluated; old model versions are never removed (their content is historical). `temperature` and `max_tokens` must be written into every content file by the generation script, making files fully self-documenting.

### ADR-2: Content format, hashing, and prompt methodology
**Date:** 2026-04-10
**Context:** The project makes provenance and reproducibility a first-class concern — content is AI-generated and the methodology needs to be transparent and verifiable by contributors and readers.
**Decision:**
- **Content files:** `.md` with YAML frontmatter. Frontmatter holds metadata and resources; markdown body holds the generated text.
- **Hash:** SHA-256 of the markdown body only (below the `---` block), byte-exact UTF-8. Stored as `content_hash` in frontmatter. Resources are excluded — they can be updated without invalidating the hash.
- **Max tokens:** 1500, uniform across all models and chapters.
- **Temperature:** 0 on every API call.
- **Prompt storage:** Option A — `PROMPT.md` stores all prompts verbatim using HTML comment delimiters (`<!-- BEGIN:slug -->` / `<!-- END:slug -->`). One block for the core persona, one block per chapter slug. The generation script reads directly from this file.
- **Output instruction:** appended to every chapter prompt — "Write the lead paragraph first, with no heading. Use `##` for section headings. Prose only — no bullet points, no bold, no other markdown."
- **Parsed structure:** lead paragraph is implicit (first content before any `##`); sections derived from `##` headings by the generation script.

**Alternatives considered:**
- JSON content files — rejected: string escaping makes diffs unreadable; `raw` field needed to preserve hashable content is redundant with markdown approach.
- Hashing the full file including frontmatter — rejected: resources would need to be frozen, making link maintenance break provenance.
- Option B (separate `prompts.yaml`) — rejected: two files to keep in sync will drift.
- Option C (construct prompts from template) — rejected: exact prompt sent to model is not stored verbatim, weakening the audit trail.

**Consequences:** Requires `js-yaml` via CDN to parse frontmatter in the browser. Generation script reads `PROMPT.md` directly — no copy-pasting of prompts. Temperature=0 is a strong control but not a perfect determinism guarantee; the hash is what anchors each generation event.

### ADR-1: Modern clean theme over dark parchment editorial theme
**Date:** 2026-04-10
**Context:** Two visual prototypes were built to evaluate the aesthetic direction before committing to a full implementation. The spec called for a dark "deep ink" tone but this proved too dark to read comfortably on a MacBook Air in daylight conditions.
**Decision:** Adopt the modern clean theme: Inter for UI chrome, Lora for body text, CSS custom properties with `data-theme="light|dark"` for theming. Working files are `modern.html` and `modern.css`.
**Alternatives considered:** Dark warm parchment theme (Cormorant Garamond + EB Garamond, near-black background, gold accents) — files preserved as `index.html` / `style.css` but not moving forward.
**Consequences:** Full-paragraph italics avoided for lead text (readability); left-border callout style used for lead paragraphs instead. Light/dark toggle architecture is already in place — wiring up the persistent toggle is a future task.


## Detail

### Page structure
<!-- Key sections of index.html — what's in the DOM, how it's organised. -->

### JS organisation
<!-- How is app.js structured? Event listeners, data flow, rendering logic. -->

### Data
<!-- Where does data come from? How is it loaded, transformed, displayed? -->
