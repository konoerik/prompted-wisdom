#!/usr/bin/env python3
"""
format.py — Strip formatting violations from generated content files.

Fixes disallowed markdown in chapter bodies (per ADR-2):
  - Top-level headings (# heading) — removed entirely
  - Bold-only lines (**text**) — removed entirely
  - Inline bold (**text** within prose) — markers stripped, text kept
  - List items (- item or 1. item) — prefix stripped, line kept as prose
  - Nested headings (### heading) — removed entirely

Flags but does not modify (counted in markdown_issues, needs manual review):
  - book-reference — "this book/guide/chapter" in prose
  - cross-chapter-reference — forward/backward essay references

Detects but does not modify (counted separately as italic_count):
  - Inline italic (*text*) — allowed per v1.5b; rendered by app.js

For each modified file:
  - Recomputes word count
  - Updates word_count, markdown_issues, and italic_count in frontmatter
  - Appends a log entry to meta/format-log.json
  - sha256 is intentionally left unchanged (hash of original AI output)

Run via: python3 scripts/format.py [--dry-run] [--model SLUG]
"""

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

ROOT        = Path(__file__).resolve().parent.parent
CONTENT_DIR = ROOT / "content"
FORMAT_LOG  = ROOT / "meta" / "format-log.json"

# ── Violation rules ────────────────────────────────────────────────────────────

BOOK_REF_RE = re.compile(
    r'\b(this book|this chapter|these chapters)\b',
    re.IGNORECASE,
)

CROSS_REF_RE = re.compile(
    r'\b(as I mentioned|as mentioned earlier|in the next essay|in another essay|'
    r'in a later essay|as we\'ll explore|as we explore|earlier in this|'
    r'later in this|the previous essay|the next chapter|in another chapter)\b',
    re.IGNORECASE,
)


def _check_violations(body_lines: "list[str]") -> "list[dict]":
    """Return a list of violations found in body_lines."""
    violations = []
    for i, line in enumerate(body_lines):
        stripped = line.rstrip()
        if re.match(r'^# .+', stripped):
            violations.append({"line": i, "type": "top-level-heading", "original": stripped})
        elif re.match(r'^\*\*[^*]+\*\*$', stripped):
            violations.append({"line": i, "type": "bold-only-line", "original": stripped})
        elif '**' in stripped and not re.match(r'^\*\*[^*]+\*\*$', stripped):
            violations.append({"line": i, "type": "inline-bold", "original": stripped})
        elif re.match(r'^- .+', stripped):
            violations.append({"line": i, "type": "list-item", "original": stripped})
        elif re.match(r'^\d+\. .+', stripped):
            violations.append({"line": i, "type": "numbered-list", "original": stripped})
        elif re.match(r'^### .+', stripped):
            violations.append({"line": i, "type": "nested-heading", "original": stripped})
        else:
            m = BOOK_REF_RE.search(stripped)
            if m:
                violations.append({"line": i, "type": "book-reference", "original": stripped, "matched": m.group(0)})
            m = CROSS_REF_RE.search(stripped)
            if m:
                violations.append({"line": i, "type": "cross-chapter-reference", "original": stripped, "matched": m.group(0)})
            for m in re.finditer(r'(?<!\*)\*(?!\*)([^*\n]+)(?<!\*)\*(?!\*)', stripped):
                violations.append({"line": i, "type": "inline-italic", "original": stripped, "matched": m.group(1)})
    return violations


def _fix_line(line: str, violation_type: str) -> Optional[str]:
    """Apply fix for a violation. Returns fixed line or None if line should be removed."""
    stripped = line.rstrip()
    if violation_type in ("top-level-heading", "bold-only-line", "nested-heading"):
        return None  # remove entirely
    elif violation_type == "inline-bold":
        return re.sub(r'\*\*([^*]+)\*\*', r'\1', stripped)
    elif violation_type == "list-item":
        return re.sub(r'^- ', '', stripped)
    elif violation_type == "numbered-list":
        return re.sub(r'^\d+\. ', '', stripped)
    elif violation_type in ("inline-italic", "book-reference", "cross-chapter-reference"):
        return line  # detected and logged but not modified — needs manual review
    return line


# ── Frontmatter helpers ────────────────────────────────────────────────────────

def _split_frontmatter(text: str) -> tuple[str, str]:
    """Split file text into (frontmatter_block, body). frontmatter_block includes --- delimiters."""
    if not text.startswith('---'):
        return ('', text)
    second = text.index('---', 3)
    end = second + 3
    # consume trailing newline after closing ---
    if end < len(text) and text[end] == '\n':
        end += 1
    return (text[:end], text[end:])


def _update_frontmatter_field(fm: str, key: str, value) -> str:
    """Replace a scalar field in YAML frontmatter block."""
    pattern = rf'^({re.escape(key)}:\s*).*$'
    replacement = rf'\g<1>{value}'
    new_fm, n = re.subn(pattern, replacement, fm, count=1, flags=re.MULTILINE)
    if n == 0:
        raise ValueError(f"Field '{key}' not found in frontmatter")
    return new_fm


def _upsert_frontmatter_field(fm: str, key: str, value) -> str:
    """Update a scalar field in YAML frontmatter, or insert it before the closing --- if absent."""
    pattern = rf'^({re.escape(key)}:\s*).*$'
    new_fm, n = re.subn(pattern, rf'\g<1>{value}', fm, count=1, flags=re.MULTILINE)
    if n == 0:
        close = fm.rfind('\n---')
        new_fm = fm[:close] + f'\n{key}: {value}' + fm[close:]
    return new_fm


def _word_count(body: str) -> int:
    return len(body.split())


def _sha256(body: str) -> str:
    return hashlib.sha256(body.encode('utf-8')).hexdigest()


# ── Core logic ─────────────────────────────────────────────────────────────────

def process_file(path: Path, dry_run: bool) -> "Optional[list[dict]]":
    """
    Check and fix one content file. Returns list of log entries for changes made,
    or None if file was clean.
    """
    text = path.read_text(encoding='utf-8')
    fm_block, body = _split_frontmatter(text)

    fm_data = {}
    for line in fm_block.splitlines():
        if ':' in line and not line.startswith('---'):
            k, _, v = line.partition(':')
            fm_data[k.strip()] = v.strip().strip('"')
    prompt_version = fm_data.get('prompt_version', '')

    body_lines = body.splitlines(keepends=True)
    violations = _check_violations([l.rstrip('\n') for l in body_lines])

    italic_entries   = [v for v in violations if v["type"] == "inline-italic"]
    violation_entries = [v for v in violations if v["type"] != "inline-italic"]

    if not violation_entries and not italic_entries:
        if 'markdown_issues:' not in fm_block:
            new_fm = _upsert_frontmatter_field(fm_block, 'markdown_issues', 0)
            new_fm = _upsert_frontmatter_field(new_fm, 'italic_count', 0)
            if not dry_run:
                path.write_text(new_fm + body, encoding='utf-8')
        return None

    log_entries = []
    new_lines = list(body_lines)
    # Process in reverse so line indices stay valid when removing lines
    for v in reversed(violations):
        i = v["line"]
        original_line = new_lines[i].rstrip('\n')
        entry = {
            "model": path.parent.name,
            "chapter": path.stem,
            "type": v["type"],
            "line": i + 1,
            "prompt_version": prompt_version,
        }
        if v["type"] == "inline-italic":
            entry["matched"] = v["matched"]
            log_entries.append(entry)
            # no fix applied — italics are allowed, detected for statistics only
        elif v["type"] in ("book-reference", "cross-chapter-reference"):
            entry["matched"] = v["matched"]
            entry["original"] = original_line
            entry["fixed"] = "(flagged — manual review)"
            log_entries.append(entry)
            # no fix applied — mid-sentence, needs manual correction
        else:
            fixed = _fix_line(original_line, v["type"])
            entry["original"] = original_line
            entry["fixed"] = fixed if fixed is not None else "(removed)"
            log_entries.append(entry)
            if fixed is None:
                del new_lines[i]
            else:
                ending = '\n' if body_lines[i].endswith('\n') else ''
                new_lines[i] = fixed + ending

    # Collapse multiple blank lines left by removals
    cleaned_lines = []
    blank_streak = 0
    for line in new_lines:
        if line.strip() == '':
            blank_streak += 1
            if blank_streak <= 1:
                cleaned_lines.append(line)
        else:
            blank_streak = 0
            cleaned_lines.append(line)
    new_body = ''.join(cleaned_lines)

    n_violations = len([e for e in log_entries if e["type"] != "inline-italic"])
    n_italics    = len([e for e in log_entries if e["type"] == "inline-italic"])

    # Update frontmatter — sha256 intentionally left unchanged (hash of original AI output)
    new_wc  = _word_count(new_body)
    new_fm  = fm_block
    new_fm  = _update_frontmatter_field(new_fm, 'word_count', new_wc)
    new_fm  = _upsert_frontmatter_field(new_fm, 'markdown_issues', n_violations)
    new_fm  = _upsert_frontmatter_field(new_fm, 'italic_count', n_italics)

    if not dry_run:
        path.write_text(new_fm + new_body, encoding='utf-8')

    return log_entries


def append_log(entries: list[dict]) -> None:
    if FORMAT_LOG.exists():
        log = json.loads(FORMAT_LOG.read_text(encoding='utf-8'))
    else:
        log = []

    timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    for e in entries:
        e["timestamp"] = timestamp
        log.append(e)

    FORMAT_LOG.write_text(json.dumps(log, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')


def main():
    parser = argparse.ArgumentParser(description="Strip formatting violations from content files.")
    parser.add_argument('--dry-run', action='store_true', help="Report violations without modifying files")
    parser.add_argument('--model', metavar='SLUG', help="Limit to one model directory")
    args = parser.parse_args()

    if args.model:
        model_dirs = [CONTENT_DIR / args.model]
        if not model_dirs[0].is_dir():
            print(f"Model directory not found: {model_dirs[0]}", file=sys.stderr)
            sys.exit(1)
    else:
        model_dirs = sorted(d for d in CONTENT_DIR.iterdir() if d.is_dir())

    all_entries = []
    files_checked = 0
    files_fixed = 0

    for model_dir in model_dirs:
        for md_file in sorted(model_dir.glob('*.md')):
            files_checked += 1
            entries = process_file(md_file, dry_run=args.dry_run)
            if entries:
                files_fixed += 1
                all_entries.extend(entries)
                label = "[DRY RUN] " if args.dry_run else ""
                for e in entries:
                    if e["type"] == "inline-italic":
                        print(f"  {label}{e['model']}/{e['chapter']}: italic — *{e['matched']}*")
                    elif e["type"] in ("book-reference", "cross-chapter-reference"):
                        print(f"  {label}{e['model']}/{e['chapter']}: {e['type']} — \"{e['matched']}\"")
                        print(f"    context: {e['original'][:100]}")
                    else:
                        action = "would remove" if e.get("fixed") == "(removed)" else "would fix"
                        verb   = action if args.dry_run else action.replace("would ", "")
                        print(f"  {label}{e['model']}/{e['chapter']}: {verb} {e['type']}")
                        print(f"    original: {e['original']}")
                        if e.get("fixed") != "(removed)":
                            print(f"    fixed:    {e['fixed']}")

    n_violations = len([e for e in all_entries if e["type"] != "inline-italic"])
    n_italics    = len([e for e in all_entries if e["type"] == "inline-italic"])

    print()
    print(f"  Files checked: {files_checked}")
    if args.dry_run:
        print(f"  Violations found: {n_violations} across {files_fixed} file(s)")
        print(f"  Italics detected: {n_italics}")
    else:
        print(f"  Files modified: {files_fixed} ({n_violations} violation(s) fixed)")
        print(f"  Italics detected: {n_italics}")
        if all_entries:
            append_log(all_entries)
            print(f"  Log updated: meta/format-log.json")
    print()


if __name__ == "__main__":
    main()
