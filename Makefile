PYTHON ?= python3
VENV ?= .venv
QUARTO ?= quarto
QUARTO_PYTHON := $(CURDIR)/$(VENV)/bin/python
DOC ?=

.PHONY: setup render preview clean check-quarto check-venv bibliography paper-assets

setup:
	$(PYTHON) -m venv $(VENV)
	$(QUARTO_PYTHON) -m pip install --upgrade pip
	$(QUARTO_PYTHON) -m pip install -r requirements.txt

check-quarto:
	@command -v $(QUARTO) >/dev/null || { echo "Quarto CLI not found. Install Quarto, then rerun make render."; exit 1; }

check-venv:
	@test -x "$(QUARTO_PYTHON)" || { echo "Python venv not found. Run make setup first."; exit 1; }

bibliography: check-venv
	$(QUARTO_PYTHON) scripts/build_bibliography.py

paper-assets: check-venv bibliography
	$(QUARTO_PYTHON) scripts/build_paper_assets.py

render: check-quarto check-venv paper-assets
	QUARTO_PYTHON="$(QUARTO_PYTHON)" $(QUARTO) render $(DOC)

preview: check-quarto check-venv
	QUARTO_PYTHON="$(QUARTO_PYTHON)" $(QUARTO) preview docs --no-browser

clean:
	rm -rf .quarto docs/*_files docs/*_cache
