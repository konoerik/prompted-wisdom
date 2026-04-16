.DEFAULT_GOAL := help

VENV   := .venv
PYTHON := $(VENV)/bin/python3
PIP    := $(VENV)/bin/pip
PORT   ?= 8000
LOCAL_IP := $(shell ipconfig getifaddr en0 2>/dev/null || echo "unavailable")

# ── Help ──────────────────────────────────────────────────────────────
.PHONY: help
help:
	@echo ""
	@echo "  Prompted Wisdom"
	@echo ""
	@echo "  make install              Create venv and install dependencies"
	@echo "  make serve                Start local dev server (default port 8000)"
	@echo "  make serve PORT=8765      Start on a custom port"
	@echo "  make serve-mobile         Serve on local network for iPhone testing (same WiFi required)"
	@echo "  make stats                Rebuild meta/stats.json from content files"
	@echo "  make estimate             Show projected cost for a full 48-chapter regeneration"
	@echo "  make generate CHAPTER=x   Generate a chapter (all models)"
	@echo "  make generate CHAPTER=x MODEL=y  Generate for a specific model"
	@echo "  make freeze               Update requirements.txt from current venv"
	@echo ""

# ── Setup ─────────────────────────────────────────────────────────────
.PHONY: install
install: $(VENV)/bin/activate

$(VENV)/bin/activate: requirements.txt
	python3 -m venv $(VENV)
	$(PIP) install --upgrade pip --quiet
	$(PIP) install -r requirements.txt --quiet
	@echo "✓ venv ready — activate with: source $(VENV)/bin/activate"

# ── Dev server ────────────────────────────────────────────────────────
.PHONY: serve
serve:
	@echo "Serving at http://localhost:$(PORT) — Ctrl+C to stop"
	python3 -m http.server $(PORT)

# ── Mobile testing ───────────────────────────────────────────────────
.PHONY: serve-mobile
serve-mobile:
	@echo "Local IP: $(LOCAL_IP)"
	@echo "Open on iPhone: http://$(LOCAL_IP):$(PORT)  (Mac and iPhone must be on the same WiFi)"
	@echo "Ctrl+C to stop"
	python3 -m http.server $(PORT) --bind 0.0.0.0

# ── Scripts ───────────────────────────────────────────────────────────
.PHONY: estimate
estimate:
	@$(PYTHON) scripts/estimate.py

.PHONY: stats
stats:
	$(PYTHON) scripts/stats.py
	@echo "✓ meta/stats.json updated"

.PHONY: generate
generate:
ifndef CHAPTER
	$(error CHAPTER is required — usage: make generate CHAPTER=knowing-yourself)
endif
	$(PYTHON) scripts/generate.py --chapter $(CHAPTER) $(if $(MODEL),--model $(MODEL),)

# ── Maintenance ───────────────────────────────────────────────────────
.PHONY: freeze
freeze:
	$(PIP) freeze > requirements.txt
	@echo "✓ requirements.txt updated"
