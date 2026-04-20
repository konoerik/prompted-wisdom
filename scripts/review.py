#!/usr/bin/env python3
"""
review.py — Semi-automated first pass on meta/review-notes.md.

Pass 1: Auto-classify clear paraphrases as [~] (indirect speech patterns).
Pass 2: For remaining entries, extract the key phrase, find the thinker,
        and fuzzy-match against Wikiquote. Report best match for human decision.

Output: annotated review-notes.md printed to stdout (pipe to file or use --apply).

Run via:
  .venv/bin/python3 scripts/review.py           # dry-run, prints report
  .venv/bin/python3 scripts/review.py --apply   # writes results back to review-notes.md
"""

import argparse
import re
import sys
import time
import urllib.parse
from pathlib import Path
from typing import Optional

import httpx

ROOT        = Path(__file__).resolve().parent.parent
REVIEW_FILE = ROOT / "meta" / "review-notes.md"

# ── Indirect speech → auto [~] ─────────────────────────────────────────────────

PARAPHRASE_RE = re.compile(
    r'\b('
    r'wrote that|said that|argued that|insisted that|observed that|'
    r'noted that|taught that|concluded that|held that|believed that|'
    r'understood that|claimed that|'
    r'something remarkably (similar|close)|'
    r'functionally the same|something similar|'
    r'is not a feeling|did not say|did not mean'
    r')\b',
    re.IGNORECASE,
)

# Override: even if indirect speech, these direct-quote signals win
DIRECT_QUOTE_RE = re.compile(
    r'(wrote:|said:|put it[^:]*:|wrote in his[^:]*:)\s+[*"\u201c]',
    re.IGNORECASE,
)

# ── Thinker → Wikiquote page ───────────────────────────────────────────────────

THINKERS = {
    'Epictetus':           'Epictetus',
    'Marcus Aurelius':     'Marcus Aurelius',
    'Montaigne':           'Michel de Montaigne',
    'Aristotle':           'Aristotle',
    'Seneca':              'Seneca the Younger',
    'Heraclitus':          'Heraclitus',
    'Camus':               'Albert Camus',
    'Sartre':              'Jean-Paul Sartre',
    'Frankl':              'Viktor Frankl',
    'Viktor Frankl':       'Viktor Frankl',
    'Simone Weil':         'Simone Weil',
    'Weil':                'Simone Weil',
    'Yamamoto Tsunetomo':  'Yamamoto Tsunetomo',
    'Tsunetomo':           'Yamamoto Tsunetomo',
    'Confucius':           'Confucius',
    'Epicurus':            'Epicurus',
    'Nietzsche':           'Friedrich Nietzsche',
    'Socrates':            'Socrates',
    'Buddha':              'Gautama Buddha',
}

_wq_cache: dict[str, list[str]] = {}


def fetch_wikiquote(page: str) -> list[str]:
    if page in _wq_cache:
        return _wq_cache[page]

    url = (
        'https://en.wikiquote.org/w/api.php?action=query'
        '&prop=revisions&rvprop=content&rvslots=main&format=json'
        f'&titles={urllib.parse.quote(page)}'
    )
    try:
        r = httpx.get(url, headers={'User-Agent': 'prompted-wisdom/review.py'}, timeout=10)
        data = r.json()
        pages = data['query']['pages']
        content = next(iter(pages.values()))['revisions'][0]['slots']['main']['*']
    except Exception as e:
        print(f'  [wikiquote] failed for {page}: {e}', file=sys.stderr)
        _wq_cache[page] = []
        return []

    quotes = []
    in_about_section = False
    for line in content.splitlines():
        # Stop collecting at "Quotes about X" sections — those are third-party commentary
        if re.match(r'==\s*Quotes about', line, re.IGNORECASE):
            in_about_section = True
        if re.match(r'==\s*(?!Quotes about)', line, re.IGNORECASE):
            in_about_section = False
        if in_about_section:
            continue
        s = line.strip()
        if not s.startswith('*') or s.startswith('**'):
            continue
        q = s[1:].strip()
        q = re.sub(r'\[\[(?:[^|\]]*\|)?([^\]]*)\]\]', r'\1', q)  # [[link|text]]
        q = re.sub(r"'{2,3}", '', q)                               # bold/italic wiki markup
        q = re.sub(r'<[^>]+>', '', q)                              # HTML tags
        q = q.strip()
        if len(q) > 15:
            quotes.append(q)

    _wq_cache[page] = quotes
    time.sleep(0.25)
    return quotes


STOPWORDS = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to',
             'for', 'of', 'with', 'by', 'from', 'is', 'it', 'its', 'as',
             'be', 'are', 'was', 'were', 'that', 'this', 'he', 'she', 'we',
             'you', 'i', 'not', 'no', 'if', 'so', 'do', 'his', 'her', 'our',
             'their', 'which', 'who', 'what', 'when', 'how', 'all', 'has',
             'have', 'had', 'can', 'will', 'would', 'could', 'should', 'may'}


def key_words(text: str) -> set:
    return {w for w in re.findall(r'\w+', text.lower()) if w not in STOPWORDS and len(w) > 2}


def phrase_coverage(phrase: str, quote: str) -> float:
    """Fraction of phrase's key words that appear in the quote."""
    pw = key_words(phrase)
    qw = key_words(quote)
    if not pw:
        return 0.0
    return len(pw & qw) / len(pw)


def best_wikiquote_match(phrase: str, page: str) -> "tuple[Optional[str], float]":
    quotes = fetch_wikiquote(page)
    phrase_lower = phrase.lower()
    best, score = None, 0.0
    for q in quotes:
        # Strong signal: 4+ consecutive words from phrase appear verbatim in quote
        words = re.findall(r'\w+', phrase_lower)
        verbatim = any(
            ' '.join(words[i:i+4]).lower() in q.lower()
            for i in range(len(words) - 3)
        ) if len(words) >= 4 else False

        s = phrase_coverage(phrase, q)
        # Boost score significantly for verbatim substring matches
        if verbatim:
            s = max(s, 0.7)
        if s > score:
            score, best = s, q
    return (best, score) if score >= 0.5 else (None, score)


# ── Phrase extraction ──────────────────────────────────────────────────────────

def extract_phrase(text: str) -> "Optional[str]":
    """Pull the most quote-like phrase from the passage."""
    # Text in *asterisks* (original markup in review-notes.md)
    stars = re.findall(r'\*(?!\*)([^*\n]{10,})\*(?!\*)', text)
    if stars:
        return ' '.join(stars)
    # Text after a colon + capital letter (direct speech signal)
    m = re.search(r':\s+([A-Z][^.]{15,}[.!?])', text)
    if m:
        return m.group(1)
    # "said/wrote/put [phrase]" without colon — e.g. "Nietzsche said what does not kill me..."
    m = re.search(r'\b(?:said|wrote|put)\s+([a-z][^.]{15,}[.!?])', text, re.IGNORECASE)
    if m:
        candidate = m.group(1)
        # Skip if it's clearly indirect speech ("said that X")
        if not re.match(r'that\b', candidate, re.IGNORECASE):
            return candidate
    # Quoted text with em-dashes or distinctive attribution ("X, as Y put it")
    m = re.search(r'"([^"]{15,})"', text)
    if m:
        return m.group(1)
    return None


def detect_thinkers(text: str) -> list[str]:
    """Return unique Wikiquote page titles for thinkers named in text."""
    seen: set[str] = set()
    result = []
    for name, page in THINKERS.items():
        if name in text and page not in seen:
            seen.add(page)
            result.append(page)
    return result


# ── Entry classification ───────────────────────────────────────────────────────

def classify(text: str) -> dict:
    """
    Returns a dict with keys:
      verdict  : '~' | 'x' | '?'
      reason   : short string
      quote    : best Wikiquote match (str or None)
      score    : similarity score (float)
      source   : Wikiquote page title (str or None)
    """
    has_direct = bool(DIRECT_QUOTE_RE.search(text))
    has_indirect = bool(PARAPHRASE_RE.search(text))

    if has_indirect and not has_direct:
        return {'verdict': '~', 'reason': 'indirect speech', 'quote': None, 'score': 0.0, 'source': None}

    phrase = extract_phrase(text)
    thinkers = detect_thinkers(text)

    if not phrase:
        return {'verdict': '?', 'reason': 'no extractable phrase — needs manual review', 'quote': None, 'score': 0.0, 'source': None}

    if not thinkers:
        return {'verdict': '?', 'reason': f'phrase found but thinker unknown — check: "{phrase[:60]}"', 'quote': None, 'score': 0.0, 'source': None}

    best_match, best_score, best_source = None, 0.0, None
    for page in thinkers:
        match, score = best_wikiquote_match(phrase, page)
        if score > best_score:
            best_score, best_match, best_source = score, match, page

    if best_match:
        return {'verdict': 'x', 'reason': f'Wikiquote match (score {best_score:.2f}) on {best_source}',
                'quote': best_match, 'score': best_score, 'source': best_source}

    return {'verdict': '?', 'reason': f'no Wikiquote match — verify: "{phrase[:60]}"',
            'quote': None, 'score': best_score, 'source': best_source}


# ── Parsing and updating review-notes.md ──────────────────────────────────────

ENTRY_RE = re.compile(r'^(- )\[ \]( .+)$', re.MULTILINE)


def process(text: str, apply: bool) -> tuple[str, list[dict]]:
    """
    Process the review-notes.md text. Returns (updated_text, report_rows).
    """
    report = []
    offset = 0
    parts = []

    for m in ENTRY_RE.finditer(text):
        parts.append(text[offset:m.start()])
        offset = m.end()

        entry_text = m.group(2)
        result = classify(entry_text)
        v = result['verdict']

        # Build replacement line
        marker = f'[{v}]'
        new_line = f'{m.group(1)}{marker}{entry_text}'

        # Append Wikiquote evidence as a sub-bullet when there's a match
        if v == 'x' and result['quote']:
            new_line += f'\n  - Wikiquote ({result["source"]}): "{result["quote"][:120]}"'
        elif v == '?':
            new_line += f'\n  - Note: {result["reason"]}'

        if apply:
            parts.append(new_line)
        else:
            parts.append(m.group(0))  # leave original unchanged

        report.append({
            'line': entry_text[:80].strip(),
            **result,
        })

    parts.append(text[offset:])
    return ''.join(parts), report


def print_report(rows: list[dict]) -> None:
    counts = {'~': 0, 'x': 0, '?': 0}
    for r in rows:
        counts[r['verdict']] += 1

    print(f"\n  {'~':>3}  auto-paraphrase   {counts['~']}")
    print(f"  {'x':>3}  quote (Wikiquote)  {counts['x']}")
    print(f"  {'?':>3}  needs review       {counts['?']}")
    print()

    for v_filter, label in [('x', 'QUOTE CANDIDATES (Wikiquote match)'), ('?', 'NEEDS MANUAL REVIEW')]:
        matches = [r for r in rows if r['verdict'] == v_filter]
        if not matches:
            continue
        print(f'── {label} ──')
        for r in matches:
            print(f'  {r["line"][:80]}')
            print(f'  → {r["reason"]}')
            if r['quote']:
                print(f'  → Wikiquote: "{r["quote"][:100]}"')
            print()


# ── Inject editorial entries into format-log.json ─────────────────────────────

# Maps review-notes.md status markers to format-log violation type strings
VERDICT_TO_VIOLATION = {
    'Q': 'unquoted-attribution',
    'F': 'factual-concern',
    '?': 'unverified-attribution',
}

SECTION_RE   = re.compile(r'^##\s+(.+)$',  re.MULTILINE)
CHAPTER_RE   = re.compile(r'^###\s+(.+)$', re.MULTILINE)
EDITORIAL_RE = re.compile(r'^- \[([QF?])\] \*\*L(\d+):\*\*(.+)$', re.MULTILINE)


def extract_matched(text: str) -> str:
    """Extract the key attributed phrase from an editorial entry."""
    # <em> tags that span a full sentence (direct quote, not a term)
    em = re.findall(r'<em>([^<]{20,})</em>', text)
    if em:
        return em[-1].strip()

    # "[Phrase], he said, [continuation]" — split attribution embedded in sentence
    # terminator can be punctuation or em-dash (e.g. "life, he said, is not worth living —")
    m = re.search(r'([A-Z][^,—]{8,}),\s+he said[,:]?\s+([^.!?—]{5,})(?=[.!?—])', text)
    if m:
        return f'{m.group(1)} {m.group(2)}'.strip()

    # "[phrase] — [dashes] — [Name Surname] wrote" — phrase before named attribution
    m = re.search(r'—\s+([^—.]{15,}),\s+[A-Z]\w+ [A-Z]\w+ (?:wrote|said)\b', text)
    if m:
        return m.group(1).strip()

    # "as X urged/put it, [phrase]"
    m = re.search(r'as \w[\w\s]* (?:urged|put it),?\s+([^.—]{10,})', text)
    if m:
        return m.group(1).strip()[:80]

    # "put it with ... : [phrase]"
    m = re.search(r'bluntness[^:]*:\s+([a-z][^.]{15,}[.!?])', text, re.IGNORECASE)
    if m:
        return m.group(1).strip()

    # "he said, [phrase]" — stop at em-dash to avoid grabbing run-on continuations
    m = re.search(r'he said,\s+(?:but\s+)?([a-z][^.—]{15,}[.!?])', text)
    if m:
        return m.group(1).strip()

    # After a colon — "he wrote: [phrase]"
    m = re.search(r':\s+([a-z][^.]{15,}[.!?])', text, re.IGNORECASE)
    if m and not re.match(r'that\b', m.group(1), re.IGNORECASE):
        return m.group(1).strip()

    # "said/wrote [phrase]" without colon (require capital letter of person before)
    m = re.search(r'[A-Z]\w+\s+(?:said|wrote)\s+([a-z][^.,]{10,})', text)
    if m and not re.match(r'that\b', m.group(1), re.IGNORECASE):
        return m.group(1).strip()[:80]

    return text.strip()[:80]


def inject_editorial(dry_run: bool = False) -> None:
    import json
    from datetime import datetime, timezone

    text      = REVIEW_FILE.read_text(encoding='utf-8')
    log_path  = ROOT / 'meta' / 'format-log.json'
    log       = json.loads(log_path.read_text(encoding='utf-8')) if log_path.exists() else []

    # Remove any previous editorial entries so re-runs stay idempotent
    log = [e for e in log if e.get('violation') not in VERDICT_TO_VIOLATION.values()]

    timestamp  = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    new_entries = []

    # Walk the file tracking current model/chapter headings
    current_model   = None
    current_chapter = None
    pos = 0

    # Interleave section/chapter/entry matches in document order
    events = []
    for m in SECTION_RE.finditer(text):
        events.append(('model',   m.start(), m.group(1).strip()))
    for m in CHAPTER_RE.finditer(text):
        events.append(('chapter', m.start(), m.group(1).strip()))
    for m in EDITORIAL_RE.finditer(text):
        events.append(('entry',   m.start(), m.group(1), int(m.group(2)), m.group(3)))
    events.sort(key=lambda e: e[1])

    for ev in events:
        if ev[0] == 'model':
            current_model = ev[2]
        elif ev[0] == 'chapter':
            current_chapter = ev[2]
        elif ev[0] == 'entry' and current_model and current_chapter:
            verdict, line_n, entry_text = ev[2], ev[3], ev[4]
            violation = VERDICT_TO_VIOLATION[verdict]
            matched   = extract_matched(entry_text)
            new_entries.append({
                'model':     current_model,
                'chapter':   current_chapter,
                'violation': violation,
                'line':      line_n,
                'matched':   matched,
                'timestamp': timestamp,
            })

    for e in new_entries:
        print(f"  {e['model']}/{e['chapter']} L{e['line']} [{e['violation']}]: {e['matched'][:60]}")

    print(f"\n  {len(new_entries)} editorial entries {'(dry run)' if dry_run else 'injected'}")

    if not dry_run:
        log_path.write_text(
            json.dumps(log + new_entries, indent=2, ensure_ascii=False) + '\n',
            encoding='utf-8',
        )


def main():
    parser = argparse.ArgumentParser(description='Semi-automated review-notes.md classification.')
    parser.add_argument('--apply',  action='store_true', help='Write results back to review-notes.md')
    parser.add_argument('--inject', action='store_true', help='Inject [Q]/[F]/[?] entries into format-log.json')
    parser.add_argument('--dry-run', action='store_true', help='Preview inject without writing')
    args = parser.parse_args()

    if args.inject or args.dry_run:
        inject_editorial(dry_run=args.dry_run)
        return

    text = REVIEW_FILE.read_text(encoding='utf-8')
    updated, report = process(text, apply=args.apply)

    print_report(report)

    if args.apply:
        REVIEW_FILE.write_text(updated, encoding='utf-8')
        print(f'  Written: {REVIEW_FILE}')
    else:
        print('  Run with --apply to write results back to review-notes.md')
    print()


if __name__ == '__main__':
    main()
