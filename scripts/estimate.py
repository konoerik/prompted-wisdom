#!/usr/bin/env python3
"""
estimate.py — Print projected cost for a full content regeneration.

Reads approved models from meta/models.json and uses their pricing and
expected_output_tokens fields to compute per-model and total costs.

Run via: make estimate
"""

import json
from pathlib import Path

ROOT        = Path(__file__).resolve().parent.parent
MODELS_JSON = ROOT / "meta" / "models.json"

CHAPTERS      = 12
INPUT_TOKENS  = 430   # approximate input tokens per chapter (core persona + chapter prompt)

def main():
    registry = json.loads(MODELS_JSON.read_text(encoding="utf-8"))
    models   = [m for m in registry["models"] if m.get("approved")]

    if not models:
        print("No approved models found in meta/models.json")
        return

    retrieved_dates = sorted({m.get("pricing", {}).get("retrieved", "unknown") for m in models})

    print()
    print("  Full regeneration cost estimate")
    print(f"  {CHAPTERS} chapters × {len(models)} models = {CHAPTERS * len(models)} API calls")
    print("  " + "─" * 54)

    total = 0.0
    for m in models:
        p       = m.get("pricing", {})
        inp     = float(p.get("input_per_1m", 0))
        out     = float(p.get("output_per_1m", 0))
        out_tok = m.get("expected_output_tokens", 500)
        cost    = (inp * INPUT_TOKENS + out * out_tok) / 1_000_000 * CHAPTERS
        total  += cost
        label   = f"{m['display']} ({m['slug']})"
        print(f"  {label:<38}  ${cost:.4f}")

    print("  " + "─" * 54)
    print(f"  {'TOTAL':<38}  ${total:.4f}")
    print()
    print(f"  Prices retrieved: {', '.join(retrieved_dates)}")
    print("  Update meta/models.json pricing fields if rates have changed.")
    print()

if __name__ == "__main__":
    main()
