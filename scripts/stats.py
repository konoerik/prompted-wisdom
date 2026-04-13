#!/usr/bin/env python3
"""
stats.py — Prompted Wisdom statistics aggregator

Reads all generated content files and writes meta/stats.json.
Run this after any new chapters are generated.

Usage:
  python3 scripts/stats.py
"""

import json
import re
from pathlib import Path

ROOT         = Path(__file__).resolve().parent.parent
CONTENT_DIR  = ROOT / "content"
MODELS_JSON  = ROOT / "meta" / "models.json"
OUTPUT       = ROOT / "meta" / "stats.json"

# Curated entity list: (canonical display name, list of forms to match)
ENTITIES = [
    ("Epictetus",      ["epictetus"]),
    ("Marcus Aurelius",["marcus aurelius", "aurelius"]),
    ("Seneca",         ["seneca"]),
    ("Plato",          ["plato"]),
    ("Aristotle",      ["aristotle"]),
    ("Socrates",       ["socrates"]),
    ("Confucius",      ["confucius"]),
    ("Buddha",         ["buddha", "the buddha"]),
    ("Laozi",          ["laozi", "lao tzu", "lao-tzu"]),
    ("Montaigne",      ["montaigne"]),
    ("Spinoza",        ["spinoza"]),
    ("Nietzsche",      ["nietzsche"]),
    ("Frankl",         ["frankl"]),
    ("Stoicism",       ["stoic", "stoics", "stoicism"]),
    ("Buddhism",       ["buddhist", "buddhists", "buddhism"]),
    ("Confucianism",   ["confucian", "confucians", "confucianism"]),
    ("Taoism",         ["taoist", "taoists", "taoism", "daoist"]),
]

def count_entities(text):
    """Count curated entity mentions in a body of text (case-insensitive, whole-word)."""
    text_lower = text.lower()
    counts = {}
    for display, forms in ENTITIES:
        total = 0
        for form in forms:
            total += len(re.findall(rf"\b{re.escape(form)}\b", text_lower))
        if total:
            counts[display] = total
    return counts

CHAPTERS = [
    ("greatest-thinkers",        "Greatest Thinkers"),
    ("knowing-yourself",         "Knowing Yourself"),
    ("virtue-and-character",     "Virtue & Character"),
    ("relationships-and-love",   "Relationships & Love"),
    ("work-and-purpose",         "Work & Purpose"),
    ("desire-and-attachment",    "Desire & Attachment"),
    ("suffering-and-resilience", "Suffering & Resilience"),
    ("time-and-mortality",       "Time & Mortality"),
    ("society-and-place",        "Society & Place"),
    ("happiness",                "Happiness"),
    ("meaning",                  "Meaning"),
    ("letter-to-you",            "Letter to You"),
]

def parse_frontmatter(text, field):
    m = re.search(rf"^{field}:\s*(.+)$", text, re.MULTILINE)
    return m.group(1).strip().strip('"') if m else None

def main():
    registry = json.loads(MODELS_JSON.read_text(encoding="utf-8"))
    models   = [m for m in registry["models"] if m.get("approved")]

    total_output_tokens = 0
    total_words         = 0
    total_files         = 0

    by_model   = []
    chapters   = []

    for m in models:
        model_words   = []
        model_tokens  = 0
        entity_totals = {}

        for slug, _ in CHAPTERS:
            path = CONTENT_DIR / m["slug"] / f"{slug}.md"
            if not path.exists():
                model_words.append(None)
                continue
            text = path.read_text(encoding="utf-8")
            # Strip frontmatter before counting
            body = re.sub(r"^---\n.*?\n---\n", "", text, flags=re.DOTALL)
            wc   = int(parse_frontmatter(text, "word_count") or 0)
            tok  = int(parse_frontmatter(text, "token_count_output") or 0)
            model_words.append(wc)
            model_tokens         += tok
            total_output_tokens  += tok
            total_words          += wc
            total_files          += 1
            for entity, count in count_entities(body).items():
                entity_totals[entity] = entity_totals.get(entity, 0) + count

        top_entities = sorted(entity_totals.items(), key=lambda x: x[1], reverse=True)[:5]
        present = [w for w in model_words if w is not None]
        by_model.append({
            "slug":        m["slug"],
            "display":     m["display"],
            "model_id":    m["id"],
            "provider":    m.get("provider", ""),
            "via":         m.get("via", ""),
            "avg_words":   round(sum(present) / len(present)) if present else 0,
            "word_counts": model_words,
            "top_entities": [{"name": name, "count": count} for name, count in top_entities],
        })

    for i, (slug, label) in enumerate(CHAPTERS):
        word_counts = {}
        for m, entry in zip(models, by_model):
            wc = entry["word_counts"][i]
            if wc is not None:
                word_counts[entry["display"]] = wc
        chapters.append({
            "slug":        slug,
            "label":       label,
            "word_counts": word_counts,
        })

    stats = {
        "summary": {
            "models":               len(models),
            "chapters":             len(CHAPTERS),
            "total_output_tokens":  total_output_tokens,
            "avg_words_per_chapter": round(total_words / total_files) if total_files else 0,
        },
        "by_model":  by_model,
        "chapters":  chapters,
    }

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(stats, indent=2), encoding="utf-8")
    print(f"Written: {OUTPUT.relative_to(ROOT)}")
    print(f"  Models:        {stats['summary']['models']}")
    print(f"  Chapters:      {stats['summary']['chapters']}")
    print(f"  Output tokens: {stats['summary']['total_output_tokens']:,}")
    print(f"  Avg words:     {stats['summary']['avg_words_per_chapter']}")
    for entry in by_model:
        print(f"  {entry['display']:10} avg {entry['avg_words']} words")

if __name__ == "__main__":
    main()
