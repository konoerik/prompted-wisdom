# Prompted Wisdom

A small experiment in ancient wisdom and modern AI. The same carefully constructed prompt is given to several leading language models — under identical conditions — and each one writes a concise guide across ten themes drawn from 2,500 years of human thought. The results are presented side by side for comparison.

## Prompt versions and git tags

Each major prompt revision is tagged in this repository. The tag name matches the prompt version recorded in each content file's `prompt_version` frontmatter field. To read the site as it was at any prompt version, check out the corresponding tag and open it locally:

```bash
git checkout v1.0      # content generated with the initial prompt
git checkout v1.3b     # content generated with the current canonical prompt
```

The full version history and rationale for each change is in [PROMPT.md](PROMPT.md).

## Running locally

No build step required. Open `index.html` directly in a browser, or serve it locally if you need fetch to work for loading content files:

```bash
npx serve          # Node (no install needed)
python3 -m http.server  # Python alternative
```

## Content structure

Generated chapters live in `content/<model-slug>/<chapter-slug>.md`. Each file has YAML front matter followed by the chapter body:

```
content/
  claude-sonnet-4/
    greatest-thinkers.md
    knowing-yourself.md
    ...
  gpt-4o/
    greatest-thinkers.md
    ...
```

Front matter fields: `title`, `chapter`, `model`, `model_display`, `generated_at`, `prompt_version`, `resources`.

The full generation prompt and API parameters are documented in [PROMPT.md](PROMPT.md).

## Tech stack

- Vanilla HTML, CSS, JavaScript — no build step
- Dependencies via CDN: [Chart.js](https://www.chartjs.org), [js-yaml](https://github.com/nodeca/js-yaml)
- Fonts via Google Fonts: Lora, Inter

## License

[CC BY 4.0](LICENSE) — Erikton Konomi

