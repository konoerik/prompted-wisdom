# Context
<!-- Updated by /wrap at session end. Edit manually if needed. Keep it under 8 lines. -->

**Current focus:** Phase 2 — regenerate all 48 chapters with frontier models (Opus 4.6, GPT-5.4, Gemini 2.5 Pro, Mistral Large 3) using prompt v1.4. Infrastructure ready; prompt/params locked.
**Last session:** Completed v1.4 experiment; evaluated 7 model candidates; decided on full frontier upgrade (ADR-6); wired models.json + generate.py; added Commentary v1.4 block; all pre-regeneration decisions locked (Opus 4.6, temp=0, 700 words, no prompt changes).
**Blocking:** Nothing — ready to regenerate.
**Next action:** Run `make generate` for all 12 chapters × 4 models, then update Commentary v1.4 per-model notes, re-run stats.py, tag v1.4 in git.
<!-- wrapped: 2026-04-15 -->
