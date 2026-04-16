#!/usr/bin/env python3
"""
generate.py — Prompted Wisdom content generator

Usage:
  python3 scripts/generate.py --chapter greatest-thinkers
  python3 scripts/generate.py --chapter greatest-thinkers --model claude-sonnet-4

Reads:
  PROMPT.md           — core persona and chapter prompts
  meta/models.json    — approved model registry

Writes:
  content/<model-slug>/<chapter-slug>.md
"""

import argparse
import hashlib
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

# ── Config ────────────────────────────────────────────────────────────

ROOT       = Path(__file__).resolve().parent.parent
PROMPT_MD  = ROOT / "PROMPT.md"
MODELS_JSON = ROOT / "meta" / "models.json"

GENERATION_PARAMS = {
    "temperature": 0,
    "max_tokens":  1500,
}

# Chapter metadata: slug → (title, chapter number)
CHAPTERS = {
    "greatest-thinkers":        ("What the Greatest Thinkers Taught Us", 1),
    "knowing-yourself":         ("On Knowing Yourself",                   2),
    "virtue-and-character":     ("On Virtue and Character",               3),
    "relationships-and-love":   ("On Relationships and Love",             4),
    "work-and-purpose":         ("On Work and Purpose",                   5),
    "desire-and-attachment":    ("On Desire and Attachment",              6),
    "suffering-and-resilience": ("On Suffering and Resilience",           7),
    "time-and-mortality":       ("On Time and Mortality",                 8),
    "society-and-place":        ("On Society and Your Place in It",       9),
    "happiness":                ("On Happiness",                          10),
    "meaning":                  ("On Meaning",                            11),
    "letter-to-you":            ("A Letter to You",                       12),
}

# ── Prompt parsing ────────────────────────────────────────────────────

def extract_block(text, name):
    """Extract content between <!-- BEGIN:name --> and <!-- END:name -->."""
    pattern = rf"<!--\s*BEGIN:{re.escape(name)}\s*-->(.*?)<!--\s*END:{re.escape(name)}\s*-->"
    match = re.search(pattern, text, re.DOTALL)
    if not match:
        raise ValueError(f"Block '{name}' not found in PROMPT.md")
    return match.group(1).strip()

def build_prompt(chapter_slug, core_block="core"):
    text = PROMPT_MD.read_text(encoding="utf-8")
    core    = extract_block(text, core_block)
    chapter = extract_block(text, chapter_slug)
    return f"{core}\n\n{chapter}"

# ── Model registry ────────────────────────────────────────────────────

def load_model(slug):
    registry = json.loads(MODELS_JSON.read_text(encoding="utf-8"))
    for m in registry["models"]:
        if m["slug"] == slug and m.get("approved"):
            return m
    raise ValueError(f"Model '{slug}' not found or not approved in models.json")

def generation_params(model):
    """Return GENERATION_PARAMS with any per-model overrides applied."""
    params = GENERATION_PARAMS.copy()
    if "max_tokens" in model:
        params["max_tokens"] = model["max_tokens"]
    return params

# ── Generation ────────────────────────────────────────────────────────

def generate(prompt, model_id, api_key, params=None, retries=3):
    if params is None:
        params = GENERATION_PARAMS
    client = OpenAI(
        api_key=api_key,
        base_url="https://openrouter.ai/api/v1",
        default_headers={"HTTP-Referer": "https://github.com/prompted-wisdom"},
    )
    for attempt in range(1, retries + 1):
        try:
            response = client.chat.completions.create(
                model=model_id,  # openrouter_id
                messages=[{"role": "user", "content": prompt}],
                **params,
            )
            body       = response.choices[0].message.content.strip()
            input_tok  = response.usage.prompt_tokens
            output_tok = response.usage.completion_tokens
            return body, input_tok, output_tok
        except Exception as e:
            if attempt == retries:
                raise
            wait = 10 * attempt
            print(f"  Attempt {attempt} failed ({e.__class__.__name__}). Retrying in {wait}s…")
            time.sleep(wait)

# ── Moderation ────────────────────────────────────────────────────────

def moderate(text, api_key):
    """Check content against OpenAI moderation endpoint (free)."""
    client = OpenAI(api_key=api_key)
    result = client.moderations.create(input=text)
    flagged = result.results[0].flagged
    if flagged:
        categories = [k for k, v in result.results[0].categories.model_dump().items() if v]
        raise ValueError(f"Content flagged by moderation API: {categories}")

# ── Output ────────────────────────────────────────────────────────────

def word_count(text):
    return len(text.split())

def sha256(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def write_output(chapter_slug, model, body, input_tok, output_tok, test=False, prompt_version="v1.2", params=None):
    if params is None:
        params = GENERATION_PARAMS
    chapter  = CHAPTERS.get(chapter_slug)
    title    = chapter[0] if chapter else chapter_slug.replace("-", " ").title()
    chapter_n = chapter[1] if chapter else None
    ts       = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    wc       = word_count(body)
    checksum = sha256(body)

    chapter_line = f"chapter: {chapter_n}\n" if chapter_n else ""
    frontmatter = f"""---
title: "{title}"
slug: {chapter_slug}
{chapter_line}model: {model['id']}
model_display: {model['display']}
prompt_version: {prompt_version}
generated_at: "{ts}"
word_count: {wc}
token_count_input: {input_tok}
token_count_output: {output_tok}
temperature: {params['temperature']}
max_tokens: {params['max_tokens']}
sha256: "{checksum}"
---"""

    base_dir = ROOT / ("tests" if test else "content")
    out_dir  = base_dir / model["slug"]
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{chapter_slug}.md"

    out_path.write_text(f"{frontmatter}\n\n{body}\n", encoding="utf-8")
    return out_path, checksum, wc

# ── Main ──────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Generate a chapter for Prompted Wisdom")
    parser.add_argument("--chapter", required=True,
                        help="Chapter slug to generate (or test slug with --test)")
    parser.add_argument("--model", default="claude-opus-4-6",
                        help="Model slug from models.json (default: claude-opus-4-6)")
    parser.add_argument("--core", default="core",
                        help="Core persona block name in PROMPT.md (default: core)")
    parser.add_argument("--test", action="store_true",
                        help="Write output to tests/<model>/ instead of content/<model>/")
    parser.add_argument("--skip-moderation", action="store_true",
                        help="Skip the OpenAI moderation check")
    parser.add_argument("--prompt-version", default="v1.2",
                        help="Prompt version string recorded in frontmatter (default: v1.2)")
    args = parser.parse_args()

    if not args.test and args.chapter not in CHAPTERS:
        print(f"Error: '{args.chapter}' is not a known chapter. Use --test for test slugs.", file=sys.stderr)
        sys.exit(1)

    load_dotenv(ROOT / ".env")
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        print("Error: OPENROUTER_API_KEY not set", file=sys.stderr)
        sys.exit(1)

    print(f"Loading model: {args.model}")
    model = load_model(args.model)

    print(f"Building prompt for: {args.chapter} (core: {args.core})")
    prompt = build_prompt(args.chapter, args.core)

    params = generation_params(model)
    if params["max_tokens"] != GENERATION_PARAMS["max_tokens"]:
        print(f"  (max_tokens overridden to {params['max_tokens']} for this model)")

    print(f"Calling {model['id']} via OpenRouter…")
    body, input_tok, output_tok = generate(prompt, model["openrouter_id"], api_key, params=params)

    if not args.skip_moderation:
        openai_key = os.environ.get("OPENAI_API_KEY")
        if openai_key:
            print("Running moderation check…")
            moderate(body, openai_key)
        else:
            print("Skipping moderation (OPENAI_API_KEY not set)")

    out_path, checksum, wc = write_output(args.chapter, model, body, input_tok, output_tok, test=args.test, prompt_version=args.prompt_version, params=params)

    print(f"\nDone.")
    print(f"  File:   {out_path.relative_to(ROOT)}")
    print(f"  Words:  {wc}")
    print(f"  Tokens: {input_tok} in / {output_tok} out")
    print(f"  SHA256: {checksum}")

if __name__ == "__main__":
    main()
