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
