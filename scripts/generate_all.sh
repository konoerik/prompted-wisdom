#!/usr/bin/env bash
# generate_all.sh — regenerate all 48 chapters with v1.5b prompt
# Runs all 4 models in parallel per chapter, then moves to the next.

set -euo pipefail

PROMPT_VERSION="v1.5b"
MODELS=(claude-opus-4-6 gpt-5 gemini-2-5-pro mistral-large-3)
CHAPTERS=(
  greatest-thinkers
  knowing-yourself
  virtue-and-character
  relationships-and-love
  work-and-purpose
  desire-and-attachment
  suffering-and-resilience
  time-and-mortality
  society-and-place
  happiness
  meaning
  letter-to-you
)

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LOG_DIR="$ROOT/logs"
mkdir -p "$LOG_DIR"
LOG="$LOG_DIR/generate_all_$(date +%Y%m%d_%H%M%S).log"

echo "Starting full generation — prompt $PROMPT_VERSION" | tee "$LOG"
echo "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" | tee -a "$LOG"
echo "─────────────────────────────────────────" | tee -a "$LOG"

TOTAL=0
FAILED=0

for chapter in "${CHAPTERS[@]}"; do
  echo "" | tee -a "$LOG"
  echo "▶ $chapter" | tee -a "$LOG"

  pids=()
  model_names=()

  for model in "${MODELS[@]}"; do
    python3 "$ROOT/scripts/generate.py" \
      --chapter "$chapter" \
      --model "$model" \
      --prompt-version "$PROMPT_VERSION" \
      --skip-moderation \
      >> "$LOG" 2>&1 &
    pids+=($!)
    model_names+=("$model")
  done

  # Wait for all 4 and collect exit codes
  for i in "${!pids[@]}"; do
    if wait "${pids[$i]}"; then
      echo "  ✓ ${model_names[$i]}" | tee -a "$LOG"
      ((TOTAL++)) || true
    else
      echo "  ✗ ${model_names[$i]} FAILED" | tee -a "$LOG"
      ((FAILED++)) || true
    fi
  done
done

echo "" | tee -a "$LOG"
echo "─────────────────────────────────────────" | tee -a "$LOG"
echo "Done. $TOTAL succeeded, $FAILED failed." | tee -a "$LOG"
echo "Log: $LOG"

if [ "$FAILED" -gt 0 ]; then
  exit 1
fi
