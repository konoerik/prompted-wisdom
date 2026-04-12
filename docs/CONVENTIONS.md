# Conventions

> Reference style — pattern-match against these before writing or editing code.
> Modify to reflect actual project choices.

## JS module structure

```js
// app.js — single entry point; import helpers from separate modules if needed

const state = {
  data: [],
};

async function init() {
  await loadData();
  render();
  bindEvents();
}

async function loadData() {
  const response = await fetch("data.json");
  if (!response.ok) throw new Error(`Failed to load data: ${response.status}`);
  state.data = await response.json();
}

function render() {
  const list = document.querySelector("#item-list");
  list.innerHTML = state.data
    .map((item) => `<li class="item" data-id="${item.id}">${item.name}</li>`)
    .join("");
}

function bindEvents() {
  document.querySelector("#item-list").addEventListener("click", (e) => {
    const item = e.target.closest(".item");
    if (!item) return;
    handleSelect(item.dataset.id);
  });
}

function handleSelect(id) {
  const item = state.data.find((d) => String(d.id) === id);
  if (!item) return;
  document.querySelector("#detail").textContent = item.name;
}

document.addEventListener("DOMContentLoaded", init);
```

## CSS conventions

```css
/* Use BEM-style class names: block__element--modifier */
/* Variables at :root, no magic numbers */

:root {
  --color-primary: #2563eb;
  --color-text: #1f2937;
  --space-md: 1rem;
  --radius: 0.375rem;
}

.item {
  padding: var(--space-md);
  border-radius: var(--radius);
  cursor: pointer;
}

.item--selected {
  background: var(--color-primary);
  color: white;
}
```

## HTML structure

```html
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>App</title>
    <link rel="stylesheet" href="style.css" />
  </head>
  <body>
    <main>
      <ul id="item-list"></ul>
      <div id="detail"></div>
    </main>
    <script src="app.js"></script>
  </body>
</html>
```
