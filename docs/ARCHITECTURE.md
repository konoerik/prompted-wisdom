# Architecture

## Quick Reference
**Stack:** HTML, CSS, vanilla JS — no build step
**Entry point:** `index.html`
**Styles:** `style.css`
**Logic:** `app.js`
**Libraries:** Chart.js 4.x (CDN), js-yaml 4.x (CDN)
**Scripts:** `scripts/generate.py` (content generation), `scripts/stats.py` (aggregates stats.json from content files)
**Data:** `meta/stats.json` fetched at runtime by `app.js`; `content/<model-slug>/<chapter-slug>.md` fetched on chapter navigation; `meta/models.json` read by Python scripts only
**Key constraint:** CDN imports only; run via `npx serve` or `python3 -m http.server` if loading local files


## Decisions (ADRs)
<!-- Append new ADRs with /log -->

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
