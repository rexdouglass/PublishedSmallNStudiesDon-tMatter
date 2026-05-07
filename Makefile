PYTHON ?= python3
VENV ?= .venv
QUARTO ?= quarto
QUARTO_PYTHON := $(CURDIR)/$(VENV)/bin/python
DOC ?=
SCHEMA_PILOT_N ?= 300
SCHEMA_PILOT_SEED ?= 20260429
REVIEW_CUE_ID ?= figure1_search_leads
REVIEW_CUE_BATCH ?= batch001
REVIEW_CUE_MODE ?= both
REVIEW_CUE_CODEX_OFFSET ?= 0
REVIEW_CUE_GPT_OFFSET ?= 0
REVIEW_CUE_DECISION_FILE ?=
FIGURE1_SEARCH_PER_QUERY ?= 8
FIGURE1_SEARCH_EXTRA_ARGS ?=
CLUSTER_REVIEW_BATCH ?= clustered001
CLUSTER_REVIEW_OFFSET ?= 0
CLUSTER_REVIEW_BATCH_SIZE ?= 8
CLUSTER_REVIEW_DECISION_FILE ?=
RESULT_ARTIFACT_PLOT ?= figure1

.PHONY: setup render preview clean check-quarto check-venv bibliography paper-assets figure1-arrow-plot-current figure1-html-review-assets provenance-codebook provenance-pipeline-graph provenance-search-plan figure1-corpora-search-all figure1-corpora-search-expanded figure1-corpora-search-provider-expanded figure1-corpora-search-sourcefamily-expanded figure1-corpora-search-alternate-vocab figure1-corpora-search-link-graph figure1-corpora-search-gpt-coverage figure1-corpora-search-known-good-recall figure1-special-source-surfaces figure1-repository-directory-search figure1-corpora-search-yield figure1-corpora-search-recall figure1-cluster-search-leads figure1-cluster-review-cue apply-cluster-review-cue result-artifact-acquisition-queue figure1-result-artifact-acquisition-queue figure2-result-artifact-acquisition-queue figure3-result-artifact-acquisition-queue figure1-result-artifact-acquisition-strategies figure1-result-artifact-acquisition-filter-tabular figure1-result-artifact-acquisition-filter-documents figure1-result-artifact-acquisition-filter-remaining-downloadable figure1-result-artifact-acquisition-mirror-sample figure1-result-artifact-acquisition-mirror-tabular-first figure1-result-artifact-acquisition-mirror-documents figure1-result-artifact-acquisition-mirror-remaining-downloadable figure1-result-artifact-acquisition-parser-queue figure1-result-artifact-acquisition-parser-queue-documents figure1-result-artifact-acquisition-parser-queue-remaining-downloadable figure1-result-artifact-followup-cues figure1-result-artifact-codex-repair-queue figure1-result-artifact-codex-repair-strategies figure1-result-artifact-codex-repair-mirror-sample figure1-result-artifact-codex-repair-parser-queue figure1-result-artifact-codex-decisions figure1-result-artifact-codex-local-proposals figure1-result-artifact-codex-local-mirror-sample figure1-result-artifact-codex-local-parser-queue figure1-codex-local-corpus-results-extract figure1-codex-local-high-inspect-extract source-family-artifact-inventory source-artifact-mirror-sample source-artifact-parser-queue figure1-corpus-results-extract figure1-raw-viability-summary figure1-gpt-candidate-batch2-mine figure1-remaining-local-mine figure1-research-followup-mirror figure1-research-followup-triage figure1-corpus-dn-check figure1-replication-pairs-table figure1-universe-coverage-diagnostics figure1-rejected-alternate-route-recheck figure1-coverage-loss-accounting figure1-corpus-dataset-closure figure1-individual-replication-search-batch001 figure1-individual-replication-mirror-batch001 figure1-individual-replication-value-scan-batch001 cluster-review-worklists review-cue apply-review-cue review-cue-routing-table corpora-table-update-proposal schema-pilot validate-schema-pilot ground-schema-pilot level5-schema-pilot level6-schema-pilot ctgov-version-drift-pilot level6-extraction-worklist-pilot level6-text-candidates-pilot artifact-snapshot-audit-pilot wayback-manual-tasks-pilot original-pdf-acquisition-pilot original-pdf-identity-pilot original-pdf-promote-pilot source-object-candidates-pilot full-article-text-pilot

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

provenance-codebook: check-venv
	$(QUARTO_PYTHON) scripts/write_provenance_codebook.py

provenance-pipeline-graph: check-venv
	$(QUARTO_PYTHON) scripts/render_provenance_pipeline_graph.py

provenance-search-plan: check-venv
	$(QUARTO_PYTHON) scripts/render_provenance_search_plan.py

figure1-corpora-search-all: check-venv
	$(QUARTO_PYTHON) scripts/search_figure1_corpora_databases.py --strategy all --strategy expanded --per-query $(FIGURE1_SEARCH_PER_QUERY) $(FIGURE1_SEARCH_EXTRA_ARGS)

figure1-corpora-search-expanded: check-venv
	$(QUARTO_PYTHON) scripts/search_figure1_corpora_databases.py --strategy expanded --per-query $(FIGURE1_SEARCH_PER_QUERY) $(FIGURE1_SEARCH_EXTRA_ARGS)

figure1-corpora-search-provider-expanded: check-venv
	$(QUARTO_PYTHON) scripts/search_figure1_corpora_databases.py --strategy repository_provider_expanded --per-query $(FIGURE1_SEARCH_PER_QUERY) $(FIGURE1_SEARCH_EXTRA_ARGS)

figure1-corpora-search-sourcefamily-expanded: check-venv
	$(QUARTO_PYTHON) scripts/search_figure1_corpora_databases.py --strategy source_family_expanded --per-query $(FIGURE1_SEARCH_PER_QUERY) $(FIGURE1_SEARCH_EXTRA_ARGS)

figure1-corpora-search-alternate-vocab: check-venv
	$(QUARTO_PYTHON) scripts/search_figure1_corpora_databases.py --strategy alternate_vocab_expanded --per-query $(FIGURE1_SEARCH_PER_QUERY) $(FIGURE1_SEARCH_EXTRA_ARGS)

figure1-corpora-search-link-graph: check-venv
	$(QUARTO_PYTHON) scripts/search_figure1_corpora_databases.py --strategy link_graph --per-query $(FIGURE1_SEARCH_PER_QUERY) $(FIGURE1_SEARCH_EXTRA_ARGS)

figure1-corpora-search-gpt-coverage: check-venv
	$(QUARTO_PYTHON) scripts/search_figure1_corpora_databases.py --strategy gpt_coverage_expanded --per-query $(FIGURE1_SEARCH_PER_QUERY) $(FIGURE1_SEARCH_EXTRA_ARGS)

figure1-corpora-search-known-good-recall: check-venv
	$(QUARTO_PYTHON) scripts/search_figure1_corpora_databases.py --strategy known_good_recall --per-query $(FIGURE1_SEARCH_PER_QUERY) $(FIGURE1_SEARCH_EXTRA_ARGS)

figure1-special-source-surfaces: check-venv
	$(QUARTO_PYTHON) scripts/search_figure1_special_source_surfaces.py

figure1-repository-directory-search: check-venv
	$(QUARTO_PYTHON) scripts/search_figure1_repository_directories.py

figure1-corpora-search-yield: check-venv
	$(QUARTO_PYTHON) scripts/summarize_figure1_search_yield.py --replace

figure1-corpora-search-recall: check-venv
	$(QUARTO_PYTHON) scripts/audit_figure1_search_recall.py --replace

figure1-cluster-search-leads: check-venv
	$(QUARTO_PYTHON) scripts/cluster_figure1_search_leads.py --replace

figure1-cluster-review-cue: check-venv
	$(QUARTO_PYTHON) scripts/build_clustered_review_cue.py --batch-id $(CLUSTER_REVIEW_BATCH) --batch-size $(CLUSTER_REVIEW_BATCH_SIZE) --offset $(CLUSTER_REVIEW_OFFSET) --replace

apply-cluster-review-cue: check-venv
	$(QUARTO_PYTHON) scripts/apply_clustered_review_decisions.py --batch-id $(CLUSTER_REVIEW_BATCH) $(if $(CLUSTER_REVIEW_DECISION_FILE),--decision-file $(CLUSTER_REVIEW_DECISION_FILE),) --replace

result-artifact-acquisition-queue: check-venv
	$(QUARTO_PYTHON) scripts/build_result_artifact_acquisition_queue.py --plot-label $(RESULT_ARTIFACT_PLOT) --replace

figure1-result-artifact-acquisition-queue: check-venv
	$(QUARTO_PYTHON) scripts/build_result_artifact_acquisition_queue.py --plot-label figure1 --replace

figure2-result-artifact-acquisition-queue: check-venv
	$(QUARTO_PYTHON) scripts/build_result_artifact_acquisition_queue.py --plot-label figure2 --replace

figure3-result-artifact-acquisition-queue: check-venv
	$(QUARTO_PYTHON) scripts/build_result_artifact_acquisition_queue.py --plot-label figure3 --replace

figure1-result-artifact-acquisition-strategies: check-venv
	$(QUARTO_PYTHON) scripts/run_result_artifact_acquisition_strategies.py --plot-label figure1 --replace

figure1-result-artifact-acquisition-filter-tabular: check-venv
	$(QUARTO_PYTHON) scripts/filter_source_artifact_proposal.py --input steps/source_inventory/figure1/result_artifact_acquisition/figure1-result-artifact-acquisition-artifacts-proposal.tsv --output steps/source_inventory/figure1/result_artifact_acquisition/figure1-result-artifact-acquisition-artifacts-proposal-tabular-first.tsv --json-output steps/source_inventory/figure1/result_artifact_acquisition/figure1-result-artifact-acquisition-artifacts-proposal-tabular-first.json --summary steps/source_inventory/figure1/result_artifact_acquisition/figure1-result-artifact-acquisition-artifacts-proposal-tabular-first-summary.tsv --replace

figure1-result-artifact-acquisition-filter-documents: check-venv
	$(QUARTO_PYTHON) scripts/filter_source_artifact_proposal.py --input steps/source_inventory/figure1/result_artifact_acquisition/figure1-result-artifact-acquisition-artifacts-proposal.tsv --output steps/source_inventory/figure1/result_artifact_acquisition/figure1-result-artifact-acquisition-artifacts-proposal-documents.tsv --json-output steps/source_inventory/figure1/result_artifact_acquisition/figure1-result-artifact-acquisition-artifacts-proposal-documents.json --summary steps/source_inventory/figure1/result_artifact_acquisition/figure1-result-artifact-acquisition-artifacts-proposal-documents-summary.tsv --mode document-first --replace

figure1-result-artifact-acquisition-filter-remaining-downloadable: check-venv
	$(QUARTO_PYTHON) scripts/filter_source_artifact_proposal.py --input steps/source_inventory/figure1/result_artifact_acquisition/figure1-result-artifact-acquisition-artifacts-proposal.tsv --output steps/source_inventory/figure1/result_artifact_acquisition/figure1-result-artifact-acquisition-artifacts-proposal-remaining-downloadable.tsv --json-output steps/source_inventory/figure1/result_artifact_acquisition/figure1-result-artifact-acquisition-artifacts-proposal-remaining-downloadable.json --summary steps/source_inventory/figure1/result_artifact_acquisition/figure1-result-artifact-acquisition-artifacts-proposal-remaining-downloadable-summary.tsv --mode remaining-downloadable --replace

figure1-result-artifact-acquisition-mirror-sample: check-venv
	$(QUARTO_PYTHON) scripts/mirror_and_sample_source_artifacts.py --proposal steps/source_inventory/figure1/result_artifact_acquisition/figure1-result-artifact-acquisition-artifacts-proposal.tsv --output-root steps/source_inventory/figure1/result_artifact_acquisition/mirror_sample --mirror-root data/raw/source_artifacts/figure1_acquisition --replace

figure1-result-artifact-acquisition-mirror-tabular-first: check-venv
	$(QUARTO_PYTHON) scripts/mirror_and_sample_source_artifacts.py --proposal steps/source_inventory/figure1/result_artifact_acquisition/figure1-result-artifact-acquisition-artifacts-proposal-tabular-first.tsv --output-root steps/source_inventory/figure1/result_artifact_acquisition/mirror_sample_tabular_first --mirror-root data/raw/source_artifacts/figure1_acquisition_tabular_first --max-bytes 26214400 --timeout 12 --replace

figure1-result-artifact-acquisition-mirror-documents: check-venv
	$(QUARTO_PYTHON) scripts/mirror_and_sample_source_artifacts.py --proposal steps/source_inventory/figure1/result_artifact_acquisition/figure1-result-artifact-acquisition-artifacts-proposal-documents.tsv --output-root steps/source_inventory/figure1/result_artifact_acquisition/mirror_sample_documents --mirror-root data/raw/source_artifacts/figure1_acquisition_documents --max-bytes 20971520 --timeout 12 --replace

figure1-result-artifact-acquisition-mirror-remaining-downloadable: check-venv
	$(QUARTO_PYTHON) scripts/mirror_and_sample_source_artifacts.py --proposal steps/source_inventory/figure1/result_artifact_acquisition/figure1-result-artifact-acquisition-artifacts-proposal-remaining-downloadable.tsv --output-root steps/source_inventory/figure1/result_artifact_acquisition/mirror_sample_remaining_downloadable --mirror-root data/raw/source_artifacts/figure1_acquisition_remaining_downloadable --max-bytes 20971520 --timeout 12 --replace

figure1-result-artifact-acquisition-parser-queue: check-venv
	$(QUARTO_PYTHON) scripts/build_source_artifact_parser_queue.py --status steps/source_inventory/figure1/result_artifact_acquisition/mirror_sample_tabular_first/source-artifact-mirror-sample-status.tsv --replace

figure1-result-artifact-acquisition-parser-queue-documents: check-venv
	$(QUARTO_PYTHON) scripts/build_source_artifact_parser_queue.py --status steps/source_inventory/figure1/result_artifact_acquisition/mirror_sample_documents/source-artifact-mirror-sample-status.tsv --output-root steps/source_inventory/figure1/result_artifact_acquisition/parser_queue_documents --replace

figure1-result-artifact-acquisition-parser-queue-remaining-downloadable: check-venv
	$(QUARTO_PYTHON) scripts/build_source_artifact_parser_queue.py --status steps/source_inventory/figure1/result_artifact_acquisition/mirror_sample_remaining_downloadable/source-artifact-mirror-sample-status.tsv --output-root steps/source_inventory/figure1/result_artifact_acquisition/parser_queue_remaining_downloadable --replace

figure1-result-artifact-followup-cues: check-venv
	$(QUARTO_PYTHON) scripts/build_result_artifact_followup_cues.py --plot-label figure1 --replace

figure1-result-artifact-codex-repair-queue: check-venv
	$(QUARTO_PYTHON) scripts/build_result_artifact_repair_queue.py --plot-label figure1 --replace

figure1-result-artifact-codex-repair-strategies: check-venv
	$(QUARTO_PYTHON) scripts/run_result_artifact_acquisition_strategies.py --plot-label figure1 --queue steps/source_inventory/figure1/result_artifact_acquisition/repair/figure1-result-artifact-codex-repair-queue.tsv --output-root steps/source_inventory/figure1/result_artifact_acquisition/repair --output-prefix figure1-result-artifact-codex-repair --replace

figure1-result-artifact-codex-repair-mirror-sample: check-venv
	$(QUARTO_PYTHON) scripts/mirror_and_sample_source_artifacts.py --proposal steps/source_inventory/figure1/result_artifact_acquisition/repair/figure1-result-artifact-codex-repair-artifacts-proposal.tsv --output-root steps/source_inventory/figure1/result_artifact_acquisition/repair/mirror_sample --mirror-root data/raw/source_artifacts/figure1_acquisition_repair --max-bytes 20971520 --timeout 12 --replace

figure1-result-artifact-codex-repair-parser-queue: check-venv
	$(QUARTO_PYTHON) scripts/build_source_artifact_parser_queue.py --status steps/source_inventory/figure1/result_artifact_acquisition/repair/mirror_sample/source-artifact-mirror-sample-status.tsv --output-root steps/source_inventory/figure1/result_artifact_acquisition/repair/parser_queue --replace

figure1-result-artifact-codex-decisions: check-venv
	$(QUARTO_PYTHON) scripts/build_codex_result_artifact_decisions.py --plot-label figure1 --replace

figure1-result-artifact-codex-local-proposals: check-venv
	$(QUARTO_PYTHON) scripts/build_codex_local_result_artifact_proposals.py --plot-label figure1 --replace

figure1-result-artifact-codex-local-mirror-sample: check-venv
	$(QUARTO_PYTHON) scripts/mirror_and_sample_source_artifacts.py --proposal steps/source_inventory/figure1/result_artifact_acquisition/codex_local/figure1-result-artifact-codex-local-source-artifacts-proposal.tsv --output-root steps/source_inventory/figure1/result_artifact_acquisition/codex_local/mirror_sample --mirror-root data/raw/source_artifacts/figure1_acquisition_codex_local --max-bytes 52428800 --timeout 12 --replace

figure1-result-artifact-codex-local-parser-queue: check-venv
	$(QUARTO_PYTHON) scripts/build_source_artifact_parser_queue.py --status steps/source_inventory/figure1/result_artifact_acquisition/codex_local/mirror_sample/source-artifact-mirror-sample-status.tsv --output-root steps/source_inventory/figure1/result_artifact_acquisition/codex_local/parser_queue --replace

figure1-codex-local-corpus-results-extract: check-venv
	$(QUARTO_PYTHON) scripts/extract_corpus_results_from_artifacts.py --parser-queue steps/source_inventory/figure1/result_artifact_acquisition/codex_local/parser_queue/source-artifact-parser-candidate-queue.tsv --status steps/source_inventory/figure1/result_artifact_acquisition/codex_local/mirror_sample/source-artifact-mirror-sample-status.tsv --output-root steps/corpus_results/figure1/codex_local --replace

figure1-codex-local-high-inspect-extract: check-venv
	$(QUARTO_PYTHON) scripts/extract_corpus_results_from_artifacts.py --parser-queue steps/source_inventory/figure1/result_artifact_acquisition/codex_local/parser_queue/source-artifact-parser-candidate-queue.tsv --status steps/source_inventory/figure1/result_artifact_acquisition/codex_local/mirror_sample/source-artifact-mirror-sample-status.tsv --output-root steps/corpus_results/figure1/codex_local_high_inspect --scope inspect_sample_for_result_fields --min-parser-priority high --replace

source-family-artifact-inventory: check-venv
	$(QUARTO_PYTHON) scripts/inventory_source_family_artifacts.py --fetch-network --replace

source-artifact-mirror-sample: check-venv
	$(QUARTO_PYTHON) scripts/mirror_and_sample_source_artifacts.py --replace

source-artifact-parser-queue: check-venv
	$(QUARTO_PYTHON) scripts/build_source_artifact_parser_queue.py --replace

figure1-corpus-results-extract: check-venv
	$(QUARTO_PYTHON) scripts/extract_corpus_results_from_artifacts.py --parser-queue steps/source_inventory/figure1/parser_queue/source-artifact-parser-candidate-queue.tsv --status steps/source_inventory/figure1/mirror_sample/source-artifact-mirror-sample-status.tsv --replace

figure1-raw-viability-summary: check-venv
	$(QUARTO_PYTHON) scripts/summarize_figure1_raw_viability.py --replace

figure1-gpt-candidate-batch2-mine: check-venv
	$(QUARTO_PYTHON) scripts/promote_gpt_candidate_batch2_pairs.py

figure1-remaining-local-mine: check-venv
	$(QUARTO_PYTHON) scripts/promote_remaining_local_figure1_mining.py

figure1-research-followup-mirror: check-venv
	$(QUARTO_PYTHON) scripts/mirror_figure1_research_followup_candidates.py

figure1-research-followup-triage: check-venv
	$(QUARTO_PYTHON) scripts/triage_figure1_research_followup_candidates.py

figure1-corpus-dn-check: check-venv
	$(QUARTO_PYTHON) scripts/check_figure1_corpus_dn.py --replace

figure1-replication-pairs-table: check-venv
	$(QUARTO_PYTHON) scripts/build_figure1_replication_pairs_table.py --replace

.PHONY: figure1-rehydration-manifest figure1-rehydrate-source-artifacts

figure1-rehydration-manifest: check-venv
	$(QUARTO_PYTHON) scripts/build_figure1_rehydration_manifest.py --replace

figure1-rehydrate-source-artifacts: check-venv
	$(QUARTO_PYTHON) scripts/rehydrate_figure1_source_artifacts.py --manifest steps/source_inventory/figure1/rehydration/figure1-rehydration-manifest.tsv

figure1-universe-coverage-diagnostics: check-venv
	$(QUARTO_PYTHON) scripts/build_figure1_universe_coverage_diagnostics.py --replace

figure1-rejected-alternate-route-recheck: check-venv
	$(QUARTO_PYTHON) scripts/recheck_figure1_rejected_for_alternative_routes.py --replace

figure1-corpus-alternate-route-audit: check-venv
	$(QUARTO_PYTHON) scripts/audit_figure1_corpus_alternate_routes.py --replace

figure1-coverage-loss-accounting: check-venv figure1-universe-coverage-diagnostics figure1-rejected-alternate-route-recheck
	$(QUARTO_PYTHON) scripts/build_figure1_coverage_loss_accounting.py --replace

figure1-corpus-dataset-closure: check-venv
	$(QUARTO_PYTHON) scripts/close_figure1_corpus_dataset_pass.py --replace

.PHONY: figure1-individual-replication-search-strategy figure1-individual-replication-vast-search-batch001 figure1-individual-replication-vast-search-batch002 figure1-individual-replication-search-intake figure1-individual-replication-search-intake-batch002 figure1-individual-replication-promote-ready figure1-individual-replication-row-disposition-batch001 figure1-individual-replication-close-batch001 figure1-individual-replication-mirror-batch002 figure1-individual-replication-value-scan-current

figure1-individual-replication-search-strategy: check-venv
	$(QUARTO_PYTHON) scripts/build_individual_replication_search_strategy.py --replace

figure1-individual-replication-vast-search-batch001: check-venv figure1-individual-replication-search-strategy
	$(QUARTO_PYTHON) scripts/execute_individual_replication_vast_search.py --replace

figure1-individual-replication-vast-search-batch002: check-venv figure1-individual-replication-search-strategy
	$(QUARTO_PYTHON) scripts/execute_individual_replication_vast_search.py --batch-id batch002 --rows-per-query 12 --max-query-priority 3 --replace

figure1-individual-replication-search-intake: check-venv figure1-bibtex-dedupe-map figure1-individual-replication-search-strategy
	$(QUARTO_PYTHON) scripts/triage_individual_replication_search_manifests.py --replace

figure1-individual-replication-search-intake-batch002: check-venv figure1-bibtex-dedupe-map figure1-individual-replication-vast-search-batch002
	$(QUARTO_PYTHON) scripts/triage_individual_replication_search_manifests.py --batch-id batch002 --manifest-glob individualrepsearch-api-batch002.json --prior-seed steps/individual_replication_papers/figure1/individual-paper-batch002-dedupe-seed.tsv --replace

figure1-individual-replication-search-batch001: figure1-individual-replication-search-intake

figure1-individual-replication-mirror-batch001: check-venv figure1-individual-replication-search-intake
	$(QUARTO_PYTHON) scripts/mirror_individual_replication_batch001_sources.py --replace

figure1-individual-replication-mirror-batch002: check-venv figure1-individual-replication-search-intake-batch002
	$(QUARTO_PYTHON) scripts/mirror_individual_replication_batch001_sources.py --batch-id batch002 --replace

figure1-individual-replication-value-scan-batch001: check-venv figure1-individual-replication-mirror-batch001
	$(QUARTO_PYTHON) scripts/scan_individual_replication_batch001_values.py --replace

figure1-individual-replication-value-scan-current: check-venv
	$(QUARTO_PYTHON) scripts/scan_individual_replication_batch001_values.py --replace

figure1-individual-replication-promote-ready: check-venv figure1-individual-replication-value-scan-current
	$(QUARTO_PYTHON) scripts/promote_individual_replication_value_scan.py --replace

figure1-individual-replication-row-disposition-batch001: check-venv
	$(MAKE) figure1-individual-replication-promote-ready
	$(MAKE) figure1-corpus-dn-check figure1-replication-pairs-table
	$(QUARTO_PYTHON) scripts/finalize_individual_replication_row_dispositions.py --replace

figure1-individual-replication-close-batch001: check-venv figure1-individual-replication-row-disposition-batch001
	$(QUARTO_PYTHON) scripts/close_individual_replication_batch001.py --replace

.PHONY: figure1-pair-chase-worklist

figure1-pair-chase-worklist: check-venv
	$(QUARTO_PYTHON) scripts/build_figure1_pair_chase_worklist.py --replace

.PHONY: figure1-individual-study-map

figure1-individual-study-map: check-venv figure1-pair-chase-worklist
	$(QUARTO_PYTHON) scripts/build_figure1_individual_study_map.py --replace

.PHONY: figure1-bibtex-dedupe-map

figure1-bibtex-dedupe-map: check-venv figure1-individual-study-map bibliography
	$(QUARTO_PYTHON) scripts/build_figure1_bibtex_dedupe_map.py --replace

.PHONY: figure1-identity-disambiguation-worklist

figure1-identity-disambiguation-worklist: check-venv figure1-bibtex-dedupe-map
	$(QUARTO_PYTHON) scripts/build_figure1_identity_disambiguation_worklist.py --replace

.PHONY: figure1-identity-disambiguation-resolve

figure1-identity-disambiguation-resolve: check-venv figure1-identity-disambiguation-worklist
	$(QUARTO_PYTHON) scripts/resolve_figure1_identity_disambiguation.py --replace

.PHONY: figure1-prior-pair-work-audit

figure1-prior-pair-work-audit: check-venv figure1-identity-disambiguation-resolve
	$(QUARTO_PYTHON) scripts/audit_figure1_prior_pair_work.py --replace

cluster-review-worklists: check-venv
	$(QUARTO_PYTHON) scripts/build_cluster_review_worklists.py --replace

review-cue: check-venv
	$(QUARTO_PYTHON) scripts/build_review_cue.py --cue-id $(REVIEW_CUE_ID) --batch-id $(REVIEW_CUE_BATCH) --mode $(REVIEW_CUE_MODE) --codex-offset $(REVIEW_CUE_CODEX_OFFSET) --gpt-offset $(REVIEW_CUE_GPT_OFFSET)

apply-review-cue: check-venv
	$(QUARTO_PYTHON) scripts/apply_review_cue_decisions.py --cue-id $(REVIEW_CUE_ID) $(if $(REVIEW_CUE_DECISION_FILE),--decision-file $(REVIEW_CUE_DECISION_FILE),)

review-cue-routing-table: check-venv
	$(QUARTO_PYTHON) scripts/build_review_cue_routing_table.py --cue-id $(REVIEW_CUE_ID) --replace

corpora-table-update-proposal: check-venv
	$(QUARTO_PYTHON) scripts/build_corpora_table_update_proposal.py --cue-id $(REVIEW_CUE_ID) --batch-id $(REVIEW_CUE_BATCH) --replace

paper-assets: check-venv bibliography provenance-codebook figure1-arrow-plot-current
	$(QUARTO_PYTHON) scripts/build_paper_assets.py

figure1-arrow-plot-current: check-venv
	$(QUARTO_PYTHON) scripts/build_current_figure1_arrow_plot.py

figure1-html-review-assets: check-venv figure1-coverage-loss-accounting
	$(QUARTO_PYTHON) scripts/build_figure1_html_review_assets.py

schema-pilot: check-venv provenance-codebook
	SCHEMA_PILOT_N=$(SCHEMA_PILOT_N) SCHEMA_PILOT_SEED=$(SCHEMA_PILOT_SEED) $(QUARTO_PYTHON) scripts/pilot_source_result_schema.py
	SCHEMA_PILOT_N=$(SCHEMA_PILOT_N) SCHEMA_PILOT_SEED=$(SCHEMA_PILOT_SEED) $(QUARTO_PYTHON) scripts/retrace_schema_pilot_sample.py
	SCHEMA_PILOT_N=$(SCHEMA_PILOT_N) SCHEMA_PILOT_SEED=$(SCHEMA_PILOT_SEED) $(QUARTO_PYTHON) scripts/build_codebook_pilot_sample.py
	SCHEMA_PILOT_N=$(SCHEMA_PILOT_N) SCHEMA_PILOT_SEED=$(SCHEMA_PILOT_SEED) $(QUARTO_PYTHON) scripts/resolve_schema_pilot_real_world_sources.py
	SCHEMA_PILOT_N=$(SCHEMA_PILOT_N) SCHEMA_PILOT_SEED=$(SCHEMA_PILOT_SEED) $(QUARTO_PYTHON) scripts/build_codebook_pilot_sample.py

validate-schema-pilot: check-venv provenance-codebook
	SCHEMA_PILOT_N=$(SCHEMA_PILOT_N) SCHEMA_PILOT_SEED=$(SCHEMA_PILOT_SEED) $(QUARTO_PYTHON) scripts/validate_schema_pilot_against_codebook.py

ground-schema-pilot: check-venv provenance-codebook
	SCHEMA_PILOT_N=$(SCHEMA_PILOT_N) SCHEMA_PILOT_SEED=$(SCHEMA_PILOT_SEED) $(QUARTO_PYTHON) scripts/resolve_schema_pilot_real_world_sources.py
	SCHEMA_PILOT_N=$(SCHEMA_PILOT_N) SCHEMA_PILOT_SEED=$(SCHEMA_PILOT_SEED) $(QUARTO_PYTHON) scripts/build_codebook_pilot_sample.py

level5-schema-pilot: check-venv
	SCHEMA_PILOT_N=$(SCHEMA_PILOT_N) SCHEMA_PILOT_SEED=$(SCHEMA_PILOT_SEED) $(QUARTO_PYTHON) scripts/push_schema_pilot_to_level5.py

level6-schema-pilot: check-venv
	SCHEMA_PILOT_N=$(SCHEMA_PILOT_N) SCHEMA_PILOT_SEED=$(SCHEMA_PILOT_SEED) $(QUARTO_PYTHON) scripts/verify_schema_pilot_level6_values.py
	SCHEMA_PILOT_N=$(SCHEMA_PILOT_N) SCHEMA_PILOT_SEED=$(SCHEMA_PILOT_SEED) $(QUARTO_PYTHON) scripts/build_codebook_pilot_sample.py

ctgov-version-drift-pilot: check-venv
	SCHEMA_PILOT_N=$(SCHEMA_PILOT_N) SCHEMA_PILOT_SEED=$(SCHEMA_PILOT_SEED) $(QUARTO_PYTHON) scripts/resolve_ctgov_registry_version_drift.py

level6-extraction-worklist-pilot: check-venv
	SCHEMA_PILOT_N=$(SCHEMA_PILOT_N) SCHEMA_PILOT_SEED=$(SCHEMA_PILOT_SEED) $(QUARTO_PYTHON) scripts/plan_level6_source_object_extraction.py

level6-text-candidates-pilot: check-venv
	SCHEMA_PILOT_N=$(SCHEMA_PILOT_N) SCHEMA_PILOT_SEED=$(SCHEMA_PILOT_SEED) $(QUARTO_PYTHON) scripts/extract_level6_text_candidates.py

artifact-snapshot-audit-pilot: check-venv
	SCHEMA_PILOT_N=$(SCHEMA_PILOT_N) SCHEMA_PILOT_SEED=$(SCHEMA_PILOT_SEED) $(QUARTO_PYTHON) scripts/audit_artifact_snapshot_provenance.py

wayback-manual-tasks-pilot: check-venv
	SCHEMA_PILOT_N=$(SCHEMA_PILOT_N) SCHEMA_PILOT_SEED=$(SCHEMA_PILOT_SEED) $(QUARTO_PYTHON) scripts/query_wayback_for_manual_tasks.py

original-pdf-acquisition-pilot: check-venv
	SCHEMA_PILOT_N=$(SCHEMA_PILOT_N) SCHEMA_PILOT_SEED=$(SCHEMA_PILOT_SEED) $(QUARTO_PYTHON) scripts/acquire_original_pdfs_pilot.py

original-pdf-identity-pilot: check-venv
	SCHEMA_PILOT_N=$(SCHEMA_PILOT_N) SCHEMA_PILOT_SEED=$(SCHEMA_PILOT_SEED) $(QUARTO_PYTHON) scripts/check_original_pdf_identity_pilot.py

original-pdf-promote-pilot: check-venv
	SCHEMA_PILOT_N=$(SCHEMA_PILOT_N) SCHEMA_PILOT_SEED=$(SCHEMA_PILOT_SEED) $(QUARTO_PYTHON) scripts/promote_original_pdfs_to_source_file_pilot.py

source-object-candidates-pilot: check-venv
	SCHEMA_PILOT_N=$(SCHEMA_PILOT_N) SCHEMA_PILOT_SEED=$(SCHEMA_PILOT_SEED) $(QUARTO_PYTHON) scripts/build_source_object_candidate_ledger_pilot.py

full-article-text-pilot: check-venv
	SCHEMA_PILOT_N=$(SCHEMA_PILOT_N) SCHEMA_PILOT_SEED=$(SCHEMA_PILOT_SEED) $(QUARTO_PYTHON) scripts/resolve_full_article_text_candidates_pilot.py

render: check-quarto check-venv paper-assets figure1-html-review-assets
	QUARTO_PYTHON="$(QUARTO_PYTHON)" $(QUARTO) render $(DOC)

preview: check-quarto check-venv
	QUARTO_PYTHON="$(QUARTO_PYTHON)" $(QUARTO) preview docs --no-browser

clean:
	rm -rf .quarto docs/*_files docs/*_cache
