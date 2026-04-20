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
SITE_OUTPUT  = ROOT / "meta" / "site.json"

STOP_WORDS = frozenset({
    # Articles, conjunctions, prepositions
    'the','a','an','and','or','but','in','on','at','to','for','of','with',
    'by','from','into','onto','upon','about','above','below','between',
    'through','during','before','after','against','along','among','around',
    'near','over','under','until','within','without','toward','towards',
    # Pronouns
    'i','me','my','we','our','you','your','he','him','his','she','her',
    'it','its','they','them','their','this','that','these','those',
    'what','which','who','whom','whose','myself','yourself','himself',
    'herself','itself','ourselves','themselves',
    # Common verbs
    'is','are','was','were','be','been','being','have','has','had','do',
    'does','did','will','would','could','should','may','might','must',
    'shall','can','let','get','gets','got','make','makes','made','take',
    'takes','took','come','comes','came','give','gives','gave','know',
    'knows','knew','think','thinks','thought','see','sees','saw','find',
    'finds','found','want','say','says','said','tell','told','put','use',
    'uses','go','goes','went','ask','try','tried','mean','means','meant',
    'keep','keeps','kept','show','shows','seem','seems','seemed','become',
    'becomes','became','feel','feels','felt','leave','left','call','calls',
    'called','turn','begin','began','move','moves','moved','bring','brought',
    'hold','holds','held','believe','believes','believed','set','sets',
    'sets','learn','change','changes','follow','follows','stop','create',
    # Adverbs, conjunctions, common adjectives
    'not','no','nor','so','yet','both','either','neither','than','as',
    'if','when','where','how','why','all','any','each','every','more',
    'most','other','some','such','up','out','here','there','very','just',
    'also','even','only','own','same','too','much','well','often','always',
    'never','perhaps','simply','already','away','back','still','again',
    'then','once','really','however','therefore','thus','whether','rather',
    'though','although','because','since','while','moreover','indeed',
    'certainly','probably','actually','especially','generally','usually',
    'sometimes','merely','quite','enough','truly',
    # Contraction fragments (apostrophe splits "isn't" → "isn" + "t"; "t" filtered by len)
    'isn','don','didn','won','can','couldn','wouldn','shouldn','doesn',
    'wasn','weren','haven','hasn','hadn','that','they','i\'ve','we\'ve',
    # Past participles of filtered verbs
    'seen','gone','done','been','come','taken','given','known','thought',
    'said','told','left','found','made','kept','held','brought','shown',
    'become','used','called','turned','followed','led','set','tried',
    # Numbers / quantifiers
    'one','two','three','four','five','six','seven','eight','nine','ten',
    'first','second','third','last','many','few','several','another',
    # Generic nouns too vague to be interesting
    'thing','things','something','nothing','everything','anything',
    'someone','everyone','anyone','nobody','somebody','kind','kinds',
    'part','parts','place','places','point','fact','sense','case',
    'example','form','forms','word','words','reason','reasons',
    'number','lot','bit','question','answer',
})

def extract_word_freq(body, top_n=80):
    """Top-N word frequencies from body text, excluding stop words."""
    words = re.findall(r'\b[a-z]{3,}\b', body.lower())
    counts = {}
    for w in words:
        if w not in STOP_WORDS:
            counts[w] = counts.get(w, 0) + 1
    ranked = sorted(counts.items(), key=lambda x: x[1], reverse=True)
    return [{'word': w, 'count': c} for w, c in ranked[:top_n]]

# Curated entity list: (canonical display name, list of forms to match)
ENTITIES = [
    # Greek & Roman
    ("Socrates",        ["socrates"]),
    ("Plato",           ["plato"]),
    ("Aristotle",       ["aristotle"]),
    ("Epicurus",        ["epicurus", "epicurean", "epicureans", "epicureanism"]),
    ("Heraclitus",      ["heraclitus"]),
    ("Diogenes",        ["diogenes"]),
    ("Cicero",          ["cicero"]),
    ("Seneca",          ["seneca"]),
    ("Epictetus",       ["epictetus"]),
    ("Marcus Aurelius", ["marcus aurelius", "aurelius"]),
    # Asian traditions
    ("Confucius",       ["confucius"]),
    ("Mencius",         ["mencius"]),
    ("Laozi",           ["laozi", "lao tzu", "lao-tzu"]),
    ("Zhuangzi",        ["zhuangzi", "chuang tzu"]),
    ("Buddha",          ["buddha", "the buddha"]),
    ("Thich Nhat Hanh", ["thich nhat hanh", "nhat hanh"]),
    ("Dogen",           ["dogen"]),
    # Medieval & early modern
    ("Augustine",       ["augustine"]),
    ("Montaigne",       ["montaigne"]),
    ("Spinoza",         ["spinoza"]),
    ("Pascal",          ["pascal"]),
    ("Rousseau",        ["rousseau"]),
    # Modern European
    ("Kant",            ["kant"]),
    ("Hegel",           ["hegel"]),
    ("Schopenhauer",    ["schopenhauer"]),
    ("Nietzsche",       ["nietzsche"]),
    ("Kierkegaard",     ["kierkegaard"]),
    ("Heidegger",       ["heidegger"]),
    ("Sartre",          ["sartre"]),
    ("Camus",           ["camus"]),
    ("de Beauvoir",     ["de beauvoir", "beauvoir"]),
    ("Simone Weil",     ["simone weil"]),
    # Anglophone
    ("Mill",            ["mill", "john stuart mill"]),
    ("Locke",           ["locke"]),
    ("Thoreau",         ["thoreau"]),
    ("William James",   ["william james"]),
    # Other
    ("Rumi",            ["rumi"]),
    ("Frankl",          ["frankl"]),
    ("Jung",            ["jung"]),
    ("Fromm",           ["fromm"]),
    # Traditions
    ("Stoicism",        ["stoic", "stoics", "stoicism"]),
    ("Buddhism",        ["buddhist", "buddhists", "buddhism"]),
    ("Confucianism",    ["confucian", "confucians", "confucianism"]),
    ("Taoism",          ["taoist", "taoists", "taoism", "daoist", "daoism"]),
    ("Existentialism",  ["existentialist", "existentialists", "existentialism"]),
    ("Zen",             ["zen"]),
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
        model_text    = ""

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
            model_text           += " " + body
            for entity, count in count_entities(body).items():
                entity_totals[entity] = entity_totals.get(entity, 0) + count

        top_entities = sorted(entity_totals.items(), key=lambda x: x[1], reverse=True)
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
            "word_freq":   extract_word_freq(model_text),
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

    # Read prompt_version from the first available content file
    prompt_version = ""
    for m in models:
        for slug, _ in CHAPTERS:
            path = CONTENT_DIR / m["slug"] / f"{slug}.md"
            if path.exists():
                v = parse_frontmatter(path.read_text(encoding="utf-8"), "prompt_version")
                if v:
                    prompt_version = v
                    break
        if prompt_version:
            break

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(stats, indent=2), encoding="utf-8")
    SITE_OUTPUT.write_text(json.dumps({"prompt_version": prompt_version}, indent=2), encoding="utf-8")
    print(f"Written: {OUTPUT.relative_to(ROOT)}")
    print(f"Written: {SITE_OUTPUT.relative_to(ROOT)}")
    print(f"  Models:        {stats['summary']['models']}")
    print(f"  Chapters:      {stats['summary']['chapters']}")
    print(f"  Output tokens: {stats['summary']['total_output_tokens']:,}")
    print(f"  Avg words:     {stats['summary']['avg_words_per_chapter']}")
    for entry in by_model:
        print(f"  {entry['display']:10} avg {entry['avg_words']} words")

if __name__ == "__main__":
    main()
