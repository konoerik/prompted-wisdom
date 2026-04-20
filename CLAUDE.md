# CLAUDE.md

## Project Overview
<!-- One paragraph: what this app does and who it's for. -->

## Tech Stack
- **Languages:** HTML, CSS, vanilla JavaScript
- **Libraries:** <!-- e.g. Chart.js 4.x (CDN), Alpine.js 3.x (CDN) — list what you use -->
- **Build step:** None — CDN imports only

## Key Conventions
- Single page: `index.html`, `style.css`, `app.js`
- All dependencies loaded via CDN `<script>` tags — no npm, no bundler
- Keep `app.js` focused on behaviour; avoid inline scripts in HTML
- <!-- e.g. data loaded from data.json; DOM structure follows ... -->

## Development Workflow
```bash
# Open directly in browser (no local data files)
open index.html

# Serve locally (required if loading local JSON or using ES modules)
npx serve          # Node — no install needed
python3 -m http.server  # Python alternative
```

## Scripts and Automation
- **Always check the Makefile first** before writing a new script or one-off command — if the operation exists, use it; if it's missing, add a target rather than reaching for a bare Python/shell script
- The Makefile is the single entry point for all generation, formatting, and stats operations (`make regen`, `make generate`, `make format`, `make stats`, `make estimate`)
- If a task outgrows Make (complex flags, multi-step orchestration, interactive prompts), consolidate into `scripts/admin.py` as a subcommand CLI — do not add more standalone wrapper scripts

## Behavior Rules
- No build step — if a library isn't available via CDN, discuss before adding a bundler
- When making a structural decision (adding a library, splitting into multiple pages), record it with `/log`
<!-- Add project-specific rules here. Workflow rules (context loading, commits, plan hygiene) live in .claude/claudify.md. -->
