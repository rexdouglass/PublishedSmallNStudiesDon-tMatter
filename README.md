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

## Provenance And Replicability

New extraction work should follow the source-result provenance standard in [AGENTS.md](AGENTS.md), [reports/provenance_schema_standard.md](reports/provenance_schema_standard.md), [reports/evidence_dataset_codebook.md](reports/evidence_dataset_codebook.md), and [reports/llm_extraction_contract.md](reports/llm_extraction_contract.md). The short version is: mirror sources locally when possible, keep verbatim source text before parsing, record transformations into `D`/`N`, and keep HTML tables as projections of TSV/CSV artifacts on disk.

Regenerate the machine-readable codebook, data dictionary, and empty TSV templates with:

```sh
make provenance-codebook
```

The current pipeline graph registry lives at the repo root in `PROVENANCE_PIPELINE_SINGLE_SOURCE_OF_TRUTH.yml` under the root key `PROVENANCE_PIPELINE_SINGLE_SOURCE_OF_TRUTH`.
Render its human-readable index, including current 300-row benchmark counts, with:

```sh
make provenance-pipeline-graph
```

Render the top-of-pipeline universe search plan with:

```sh
make provenance-search-plan
```

That target projects `universe_search_plans` from `PROVENANCE_PIPELINE_SINGLE_SOURCE_OF_TRUTH.yml` into `data/derived/effect_inflation_dataset/provenance_search_plan.tsv` and `reports/provenance_universe_search_plan.md`.

The current 300-row provenance pilot can be regenerated with:

```sh
make schema-pilot
```

That target creates diagnostic retrace files plus codebook-shaped tables under `data/derived/effect_inflation_dataset/schema_pilot/`, including `source_result_codebook_sample_300.tsv`, `source_access_codebook_sample_300.tsv`, `extraction_event_codebook_sample_300.tsv`, and `extraction_problem_codebook_sample_300.tsv`. Override the sample size with `make schema-pilot SCHEMA_PILOT_N=100` when debugging.

Validate that pilot against the formal codebook with:

```sh
make validate-schema-pilot
```

Resolve the same sampled rows to real-world DOI/PMID/PMCID/NCT/AEA/Crossref/source-bibliography handles with:

```sh
make ground-schema-pilot
```

For a local preview server:

```sh
make preview
```
