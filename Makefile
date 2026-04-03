# ============================================================
# AI Decision Intelligence System — Makefile
# ============================================================

PYTHON      := python3
PIP         := pip
VENV        := venv
VENV_BIN    := $(VENV)/bin
PORT        := 8000

.PHONY: help setup install run demo html api test lint clean reset

# ── Default ──────────────────────────────────────────────────────────────────
help:
	@echo ""
	@echo "  AI Decision Intelligence System"
	@echo "  ================================"
	@echo ""
	@echo "  make setup      Create virtualenv and install all dependencies"
	@echo "  make install    Install dependencies into current environment"
	@echo "  make run        Run the full pipeline (rich CLI output)"
	@echo "  make demo       Run pipeline + save HTML executive brief"
	@echo "  make html       Run pipeline, save HTML, open in browser"
	@echo "  make api        Start the FastAPI server on port $(PORT)"
	@echo "  make test       Run pytest suite with coverage"
	@echo "  make lint       Run code quality checks"
	@echo "  make clean      Remove generated data files and outputs"
	@echo "  make reset      Full reset: delete data + re-generate synthetic dataset"
	@echo ""

# ── Environment ──────────────────────────────────────────────────────────────
setup:
	$(PYTHON) -m venv $(VENV)
	$(VENV_BIN)/pip install --upgrade pip
	$(VENV_BIN)/pip install -r requirements.txt
	@echo ""
	@echo "  Setup complete. Activate with: source $(VENV)/bin/activate"
	@echo "  Then run: make run"
	@echo ""

install:
	$(PIP) install -r requirements.txt

# ── Pipeline ─────────────────────────────────────────────────────────────────
run:
	$(PYTHON) run_pipeline.py

demo:
	$(PYTHON) run_pipeline.py --html

html:
	$(PYTHON) run_pipeline.py --html
	@echo "Opening latest HTML report..."
	@open outputs/$$(ls -t outputs/*.html | head -1) 2>/dev/null || \
	 xdg-open outputs/$$(ls -t outputs/*.html | head -1) 2>/dev/null || \
	 echo "  Report saved to outputs/ — open manually."

json:
	$(PYTHON) run_pipeline.py --json-only | python3 -m json.tool

# ── API ───────────────────────────────────────────────────────────────────────
api:
	@echo "Starting AI Decision Intelligence API on http://localhost:$(PORT)"
	@echo "  Docs: http://localhost:$(PORT)/docs"
	uvicorn src.api.main:app --host 0.0.0.0 --port $(PORT) --reload

# ── Testing ───────────────────────────────────────────────────────────────────
test:
	pytest -v --cov=src --cov-report=term-missing tests/

test-fast:
	pytest -v tests/ -x

# ── Code quality ─────────────────────────────────────────────────────────────
lint:
	@$(PYTHON) -m py_compile src/ingestion/ingest.py && echo "  ingest.py       OK"
	@$(PYTHON) -m py_compile src/processing/transform.py && echo "  transform.py    OK"
	@$(PYTHON) -m py_compile src/anomaly/detect.py && echo "  detect.py       OK"
	@$(PYTHON) -m py_compile src/root_cause/analyze.py && echo "  analyze.py      OK"
	@$(PYTHON) -m py_compile src/forecasting/forecast.py && echo "  forecast.py     OK"
	@$(PYTHON) -m py_compile src/recommendation/recommend.py && echo "  recommend.py    OK"
	@$(PYTHON) -m py_compile src/llm/explain.py && echo "  explain.py      OK"
	@$(PYTHON) -m py_compile src/reporting/cli_output.py && echo "  cli_output.py   OK"
	@$(PYTHON) -m py_compile src/reporting/html_report.py && echo "  html_report.py  OK"
	@$(PYTHON) -m py_compile run_pipeline.py && echo "  run_pipeline.py OK"
	@echo ""
	@echo "  All modules compiled successfully."

# ── Utilities ────────────────────────────────────────────────────────────────
clean:
	rm -f data/raw/source.csv
	rm -f data/processed/processed.csv
	rm -rf outputs/*.html
	rm -rf __pycache__ src/**/__pycache__ tests/__pycache__
	find . -name "*.pyc" -delete

reset: clean
	$(PYTHON) -c "from src.ingestion.ingest import _generate_synthetic_dataset; \
	               import pandas as pd; \
	               df = _generate_synthetic_dataset(); \
	               df.to_csv('data/raw/source.csv', index=False); \
	               print(f'  Generated {len(df)} rows of synthetic enterprise data')"
