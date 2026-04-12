<!-- This project uses claudify — a Claude Code configuration kit.
     Commands: /continue, /save, /log, /prep, /pulse
     To update kit files: /claudify update
     Learn more: https://github.com/konoerik/claudify -->

## Context Loading

Read on every session:
- `docs/CONTEXT.md` — current focus, last decisions, next action

Read when the user mentions tasks, features, bugs, or current work:
- `docs/PLAN.md` — `## Active` section only

Read when writing or editing code:
- `docs/CONVENTIONS.md` — canonical style reference; pattern-match before writing

Read when touching code structure, architecture, or making structural decisions:
- `docs/ARCHITECTURE.md` — `## Quick Reference` first; full file only if needed

Load only when explicitly asked about goals or priorities:
- `docs/ROADMAP.md`

Never auto-load:
- `.claude/archive/`

## Behavior Rules
- Prefer editing existing files over creating new ones
- Do not create `BACKLOG.md`, `TASKS.md`, `TODO.md`, or similar — use `PLAN.md`
- When making an architectural decision, record it with `/log` before ending the session
- Keep `PLAN.md ## Active` short — if it exceeds 10 items, triage before adding more
- Never commit or push without explicit instruction — `/save` and `/prep` are the checkpoints before that happens
