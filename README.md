# Published Small N Studies Don't Matter

This repository is set up for a Python-backed Quarto note in `docs/` that renders to HTML.

## Requirements

- Python 3.13, or another recent Python 3 version compatible with the packages in `requirements.txt`
- Quarto CLI available on `PATH`

## Setup

```sh
make setup
```

This creates `.venv/` and installs the Python packages Quarto needs to execute Python cells.

## Render

```sh
make render
```

The rendered note is written to `docs/index.html`. The Makefile sets `QUARTO_PYTHON` so Quarto executes code with the repository virtual environment.

For a local preview server:

```sh
make preview
```

