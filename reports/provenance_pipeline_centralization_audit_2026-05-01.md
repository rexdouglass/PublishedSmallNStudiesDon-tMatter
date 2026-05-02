# Provenance Pipeline Centralization Audit

Date: 2026-05-01

This audit enumerates the repo surfaces that need to be centralized so
`PROVENANCE_PIPELINE_SINGLE_SOURCE_OF_TRUTH.yml` can become the human- and LLM-editable source
of truth for the provenance graph. The point is not to rewrite every extractor
immediately. The point is to stop letting route names, promotion criteria,
queue buckets, byte classes, plot ownership rules, and performance claims live
as isolated script-local facts.

## Current Shape

The new pipeline YAML already defines the core graph contract:

- plot universes
- node types
- edge types
- stages
- evidence ladder
- target/value state vocabularies
- strategy contract
- strategy registry
- promotion gates
- current benchmark pointers

The rest of the repo still carries many parallel definitions. Some are
conceptual standards, some are executable rules, and some are dated Markdown
reports with old counts. The cleanup should make the YAML authoritative, then
make scripts either read from it or emit outputs explicitly mapped to strategy
IDs in it.

## Priority Centralization Targets

### 1. Table And Vocabulary Registry

Current owners:

- `scripts/write_provenance_codebook.py`
- `reports/provenance_schema_standard.md`
- `reports/evidence_dataset_codebook.md`
- `reports/llm_extraction_contract.md`
- `data/derived/effect_inflation_dataset/provenance_data_dictionary.tsv`
- `data/derived/effect_inflation_dataset/provenance_vocab_dictionary.tsv`
- `data/derived/effect_inflation_dataset/schema_templates/`

What is scattered:

- canonical table list
- table grains
- primary keys
- required fields
- controlled vocabularies
- examples
- promotion requirements

Cleanup:

- Move table definitions and controlled vocabularies into the YAML, or into
  YAML sections referenced by the root pipeline file.
- Make `scripts/write_provenance_codebook.py` render codebook TSV/Markdown and
  empty templates from YAML rather than defining `TABLES` and
  `CONTROLLED_VOCABS` itself.
- Add `source_object_candidate.tsv` to the formal codebook/templates. It exists
  as `source_object_candidate_codebook_sample_300.tsv` and as a YAML node type,
  but it is not currently generated as a schema template.
- Treat generated TSV/Markdown dictionaries as projections, not independent
  standards.

YAML sections needed:

- `tables`
- `fields`
- `controlled_vocabularies`
- `table_templates`
- `required_fields_by_gate`

### 2. Evidence Ladder And State Transitions

Current owners:

- `PROVENANCE_PIPELINE_SINGLE_SOURCE_OF_TRUTH.yml`
- `scripts/build_codebook_pilot_sample.py`
- `scripts/resolve_schema_pilot_real_world_sources.py`
- `scripts/promote_original_pdfs_to_source_file_pilot.py`
- `scripts/resolve_full_article_text_candidates_pilot.py`
- `scripts/verify_schema_pilot_level6_values.py`
- dated reports under `reports/`

What is scattered:

- evidence level names
- level assignment logic
- target acquisition state assignments
- value verification state assignments
- promotion gate rules
- old evidence distributions in reports

Cleanup:

- Keep the ladder names and state vocabularies in YAML.
- Move each level transition into a named gate with required inputs,
  eligible source byte classes, disqualifying byte classes, and state updates.
- Replace script-local assignments like `evidence_level = 5`,
  `evidence_level_name = original_source_obtained`,
  `target_acquisition_state = source_object_mirrored`, and
  `value_verification_state = source_object_obtained_not_parsed` with a shared
  promotion helper that reads the YAML gate.
- Make reports compute counts dynamically from current TSVs, or mark dated
  count reports as historical snapshots.

YAML sections needed:

- `evidence_ladder`
- `state_vocabularies`
- `promotion_gates`
- `promotion_events`
- `historical_reports`

### 3. Strategy And Route Registry

Current owners:

- `PROVENANCE_PIPELINE_SINGLE_SOURCE_OF_TRUTH.yml`
- `scripts/push_schema_pilot_to_level5.py`
- `scripts/acquire_original_pdfs_pilot.py`
- `scripts/resolve_full_article_text_candidates_pilot.py`
- `scripts/query_wayback_for_manual_tasks.py`
- `scripts/run_zotero_automated_fulltext_pilot.py`
- `scripts/ingest_zotero_storage_fulltext_pilot.py`
- `scripts/harvest_replication_leads.py`
- Makefile targets

What is scattered:

- strategy IDs
- route family names
- resolver names
- route-to-strategy mapping
- output file names
- stop conditions
- retry and candidate limits
- environment variable names
- route eligibility

Examples:

- `STRATEGY_GROUPS` in `push_schema_pilot_to_level5.py`
- `ROUTES` in `acquire_original_pdfs_pilot.py`
- route functions such as `europepmc_candidates`,
  `crossref_candidates`, `openalex_candidates`, `core_candidates`,
  `semantic_scholar_candidates`, `openaire_candidates`, `hal_candidates`,
  `arxiv_candidates`, `biorxiv_medrxiv_candidates`, `osf_candidates`, and
  `wayback_candidates`
- Zotero routes: `zotero_save_item`, `zotero_connector_save_page`,
  `zotero_translation_server`, `zotero_storage_reingest`

Cleanup:

- Make every executable pass declare one `strategy_id` from YAML.
- Move route families and route modules into YAML with stable IDs.
- Give each route an input node type, output node type, route family, expected
  byte classes, blocker classes, and stop condition.
- Make scripts emit `strategy_id`, `route_id`, and `route_family` columns
  consistently.
- Link Makefile targets to strategy IDs in YAML.

YAML sections needed:

- `strategies`
- `route_families`
- `routes`
- `resolver_modules`
- `make_targets`
- `run_profiles`

### 4. External Resolver And Network Policy Registry

Current owners:

- `scripts/push_schema_pilot_to_level5.py`
- `scripts/acquire_original_pdfs_pilot.py`
- `scripts/resolve_full_article_text_candidates_pilot.py`
- `scripts/build_bibliography.py`
- `scripts/query_wayback_for_manual_tasks.py`
- `scripts/verify_schema_pilot_level6_values.py`
- `scripts/harvest_replication_leads.py`

What is scattered:

- endpoint URLs
- API key environment variables
- host-specific delays
- user-agent strings
- contact email rules
- max bytes
- request timeouts
- resolver-specific accept headers
- enabled/disabled route flags

Resolvers currently hard-coded across scripts include Crossref, DataCite,
OpenAlex, Unpaywall, Semantic Scholar, Europe PMC, PubMed, PMC OA,
ClinicalTrials.gov, OpenAIRE, CORE, OSF, Dataverse, Wayback, HAL, arXiv,
bioRxiv/medRxiv, Zotero, and Paperclip.

Cleanup:

- Centralize resolver metadata in YAML.
- Keep credentials out of YAML, but declare environment variable names,
  optional/required status, and redaction rules.
- Put host delay and max-byte policy in one place.
- Make route attempts record the resolver ID from the registry.

YAML sections needed:

- `resolvers`
- `network_policy`
- `environment_variables`
- `redaction_policy`

### 5. Source Byte Classes, File Roles, And Eligibility Rules

Current owners:

- `scripts/write_provenance_codebook.py`
- `scripts/build_codebook_pilot_sample.py`
- `scripts/push_schema_pilot_to_level5.py`
- `scripts/resolve_full_article_text_candidates_pilot.py`
- `scripts/promote_original_pdfs_to_source_file_pilot.py`
- `scripts/plan_level6_source_object_extraction.py`

What is scattered:

- source byte class vocabulary
- file role vocabulary
- file origin vocabulary
- level-5 eligibility
- extraction readiness
- parser routing by byte class

Cleanup:

- Centralize `source_byte_class`, `file_role`, and `file_origin` vocabularies.
- Attach properties to byte classes: `level5_eligible`,
  `article_fulltext_yn`, `metadata_only_yn`, `blocker_yn`,
  `default_file_role`, `default_parser_route`, and `rights_required_yn`.
- Replace script-local sets such as `ARTICLE_CLASSES` and repeated
  value-bearing class sets with YAML-derived helpers.

YAML sections needed:

- `source_byte_classes`
- `file_roles`
- `file_origins`
- `eligibility_rules`
- `parser_plans`

### 6. Identity Gates And Scoring Rules

Current owners:

- `scripts/resolve_schema_pilot_real_world_sources.py`
- `scripts/build_bibliography.py`
- `scripts/check_original_pdf_identity_pilot.py`
- `scripts/resolve_full_article_text_candidates_pilot.py`
- `scripts/build_tail_resolution_queues.py`
- `reports/current_step_by_step_strategy_and_gpt_prompt_sample_300_2026-05-01.md`

What is scattered:

- DOI normalization
- title token coverage thresholds
- Crossref bibliographic scoring
- Metabus journal/volume/issue/page parsing
- PDF identity acceptance rules
- full-article identity acceptance rules
- manual review classifications

Cleanup:

- Define named identity gates in YAML, for example:
  `doi_exact_in_file`, `primary_doi_route_plus_title`,
  `title_author_year_manual_review`, `metabus_bibliographic_score`,
  `registry_id_exact`, and `zotero_attachment_identity_gate`.
- Put score thresholds, required fields, competing-candidate rules, and
  rejection rules in the registry.
- Make identity gate decisions use a shared helper and write `identity_gate_id`.
- Promote Metabus parsing from tail-queue helper/report prose into a real
  crosswalk strategy.

YAML sections needed:

- `identity_gates`
- `identity_scores`
- `crosswalk_patterns`
- `normalizers`

### 7. Queue And Worklist Definitions

Current owners:

- `scripts/build_tail_resolution_queues.py`
- `data/derived/effect_inflation_dataset/schema_pilot/tail_resolution_queue_sample_300.tsv`
- `data/derived/effect_inflation_dataset/schema_pilot/manual_capture_queue_sample_300.tsv`
- `data/derived/effect_inflation_dataset/schema_pilot/manual_or_library_followup_queue_sample_300.tsv`
- `data/derived/effect_inflation_dataset/schema_pilot/manual_acquisition_task_codebook_sample_300.tsv`
- `data/derived/effect_inflation_dataset/schema_pilot/level6_source_object_extraction_worklist_sample_300.tsv`

What is scattered:

- tail buckets
- ranks
- problem families
- manual route types
- stop conditions
- generated queue fields
- manual task fields
- level-6 worklist parser priorities

Cleanup:

- Move `BUCKET_CONFIG` from `build_tail_resolution_queues.py` into YAML.
- Make tail queues generated projections of YAML queue definitions plus current
  source-result state.
- Reconcile `manual_capture_queue_*` with formal
  `manual_acquisition_task.tsv`. The manual queue has operational fields that
  should either become task fields or be represented as a task subtype.
- Treat worklists as node instances of `manual_task`, `strategy_attempt`, or
  `source_result_support`, not standalone schemas with private meanings.

YAML sections needed:

- `queues`
- `queue_buckets`
- `manual_route_types`
- `worklist_generators`

### 8. Plot Universe, Source Family, And Collapse Rules

Current owners:

- `scripts/build_paper_assets.py`
- `scripts/analyze_replication_pairs.py`
- `scripts/build_candidate_d_vs_n.py`
- `scripts/build_published_paper_d_vs_n.py`
- `scripts/build_plot3_rescue_candidates.py`
- plot catalog/status CSVs under `data/derived/effect_inflation_dataset/`
- source catalogs under `reports/corpus_candidates/`

What is scattered:

- source family labels
- source inclusion statuses
- plot ownership rules
- paper-level collapse rules
- source-family-to-field mappings
- candidate row status vocabularies
- source-specific parsers and candidate rules

Examples:

- `plot1_owns_replication_pairs`
- `plot2_owns_nonprereg_published_endpoints`
- `plot3_owns_preregistered_confirmatory_units`
- `within_paper_median_collapse`
- `plot4_is_not_mutually_exclusive`
- source family mappings in `build_paper_assets.py`

Cleanup:

- Move plot ownership and collapse rules into YAML.
- Add a source-family registry: source family ID, label, plot universe,
  represented source kind, extractor script, raw inputs, source-result grain,
  collapse rule, and current status.
- Require candidate/provisional source-family scripts to emit `source_family_id`
  and `strategy_id`.
- Let `build_paper_assets.py` render plot catalogs from registry-backed source
  family metadata rather than hard-coded prose and mappings.

YAML sections needed:

- `plot_universes`
- `plot_ownership_rules`
- `collapse_rules`
- `source_families`
- `source_family_statuses`

### 9. Source-Specific Promotion And Rescue Scripts

Current owners:

- many `scripts/promote_*.py`
- `scripts/build_plot3_rescue_candidates.py`
- `scripts/harvest_replication_leads.py`
- `scripts/unlock_political_science_sources.py`
- `scripts/ingest_ying_partial_reconstruction.py`
- `scripts/build_clinifact_*`
- `scripts/parse_*`

What is scattered:

- corpus-specific assumptions
- source-specific row grains
- conversion formulas
- preregistration/replication logic
- local raw-file locations
- hand-curated source URLs
- hard-coded notes that should become extraction events or mappings

Cleanup:

- Do not rewrite all of these first. First register them.
- Add a YAML entry per extractor/promoter with:
  `script`, `strategy_id`, `source_family_id`, `input_files`, `output_files`,
  `result_grain`, `conversion_methods`, `relationship_mappings`, and
  `known_limitations`.
- Move conversion method IDs and formula names into shared vocabulary.
- Require future promotion scripts to emit source-result/support/mapping rows
  directly instead of only plotting-ready CSV rows.

YAML sections needed:

- `extractors`
- `source_families`
- `conversion_methods`
- `relationship_mapping_rules`

### 10. L6 Parser And Verification Contracts

Current owners:

- `scripts/plan_level6_source_object_extraction.py`
- `scripts/extract_level6_text_candidates.py`
- `scripts/verify_schema_pilot_level6_values.py`
- `scripts/resolve_ctgov_registry_version_drift.py`
- `reports/level6_source_object_extraction_worklist_sample_300_2026-04-30.md`
- `reports/level6_text_candidate_snippets_sample_300_2026-04-30.md`
- `reports/level6_value_verification_sample_300_2026-04-30.md`

What is scattered:

- parser routes
- parser priority order
- candidate snippet statuses
- CT.gov verification statuses
- exact-match criteria
- source-version drift rules
- level-6 promotion fields

Cleanup:

- Move parser plans and parser route definitions into YAML.
- Define L6 candidate statuses and L6 verified statuses centrally.
- Make candidate extraction write `parser_route_id`, `verification_gate_id`,
  and `support_role` from YAML.
- Split "candidate snippet found" from "verified level 6" in both schema and
  reports.

YAML sections needed:

- `parser_plans`
- `verification_gates`
- `support_roles`
- `candidate_statuses`
- `verification_statuses`

### 11. Report Registry And Staleness Control

Current owners:

- dated Markdown reports under `reports/`
- generated report logic in many scripts
- `reports/provenance_pipeline_graph.md`
- `README.md`

What is scattered:

- performance claims
- old sample counts
- old tail counts
- GPT prompts
- process notes
- "current" claims that later became historical

Examples:

- `reports/provenance_pilot_300_lessons_2026-04-29.md` has older evidence
  counts.
- `reports/full_article_acquisition_process_and_help_prompt_2026-04-30.md`
  has a mid-run distribution.
- `reports/full_article_after_core_sample_300_2026-05-01.md` has 47 tail rows,
  before Zotero storage reingest reduced the active tail to 45.
- `reports/current_step_by_step_strategy_and_gpt_prompt_sample_300_2026-05-01.md`
  is the current narrative but should not become another unmanaged authority.

Cleanup:

- Add report metadata to YAML: report ID, generator script, source TSVs,
  snapshot date, current/stale/historical status, and strategy IDs covered.
- Make dynamic "current status" reports read TSVs and avoid hand-edited counts.
- Add a small generated report index that marks dated reports as snapshots.

YAML sections needed:

- `reports`
- `report_statuses`
- `benchmark_metrics`

### 12. Shared Utility Layer

Current owners:

- repeated helper functions in many scripts

What is scattered:

- `safe_text`
- repo-relative path normalization
- SHA-256 helpers
- stable ID/hash helpers
- TSV readers/writers
- DOI normalization
- source text one-line cleanup
- URL redaction

The audit found repeated helper definitions across more than twenty scripts.

Cleanup:

- Add a small shared module, for example `scripts/provenance_common.py`.
- Add a pipeline registry loader, for example
  `scripts/provenance_pipeline_registry.py`.
- Keep helpers boring and stable: text cleaning, path normalization, hash IDs,
  DOI normalization, TSV IO, YAML loading, and schema validation.
- Migrate new scripts first; then migrate older scripts opportunistically.

YAML sections needed:

- not a YAML section, but helper functions should validate against YAML
  vocabularies and gates.

### 13. Output Naming, Run IDs, And Artifact Lineage

Current owners:

- every script that writes TSV/Markdown/cache files
- Makefile
- environment variables such as `SCHEMA_PILOT_N`, `FULL_ARTICLE_RUN_LABEL`,
  `ORIGINAL_PDF_MAX_ROWS`, `LEVEL6_TEXT_CANDIDATE_ROUTES`

What is scattered:

- output paths
- dated report names
- run labels
- cache directories
- sample size and seed conventions
- checkpoint behavior

Cleanup:

- Put output conventions in YAML by strategy.
- Require each run to emit a `run_id`, `strategy_id`, `input_tables`,
  `output_tables`, `cache_dirs`, `started_at`, `completed_at`, and
  `git/tree context` if practical.
- Standardize historical append-only attempt outputs versus replacement
  current-state codebook tables.

YAML sections needed:

- `run_profiles`
- `outputs`
- `cache_locations`
- `artifact_lineage`

### 14. Zotero-Specific Configuration

Current owners:

- `scripts/run_zotero_automated_fulltext_pilot.py`
- `scripts/ingest_zotero_storage_fulltext_pilot.py`
- `scripts/install_zotero_oa_bridge_plugin.sh`
- `tools/zotero-oa-bridge/`
- `reports/zotero_strategy_sample_300_2026-05-01.md`

What is scattered:

- Zotero profile paths
- bridge/plugin status
- attempt names
- storage reingest rules
- accepted file handling
- late-download recovery rules

Cleanup:

- Represent Zotero as route family `zotero_capture_assist`, not as authority.
- Put dedicated profile paths, storage roots, attempt names, and reingest
  timing rules into YAML.
- Record bridge endpoint status as experimental until the plugin reliably loads.
- Make storage reingest produce normal source-object candidate and source-file
  rows with `route_id = zotero_storage_reingest`.

YAML sections needed:

- `zotero`
- `routes`
- `manual_route_types`

### 15. Manual Acquisition And Rights Workflow

Current owners:

- `scripts/build_tail_resolution_queues.py`
- manual queue TSVs
- codebook `manual_acquisition_task.tsv`
- source access right rows
- reports and prompts

What is scattered:

- manual browser route labels
- institutional access flags
- ILL/author/publisher route labels
- storage rights note conventions
- internal audit flags
- redistribution flags

Cleanup:

- Make manual route types controlled vocabulary.
- Make rights/storage fields required for L5 manual promotion.
- Have manual capture update formal `manual_acquisition_task.tsv` instead of
  a separate queue-only schema.
- Keep "manual no access" as an attempt/event, not as missing data.

YAML sections needed:

- `manual_route_types`
- `rights_policy`
- `manual_task_fields`
- `promotion_gates.l4_to_l5`

### 16. Validation Beyond Column Presence

Current owners:

- `scripts/validate_schema_pilot_against_codebook.py`
- `scripts/render_provenance_pipeline_graph.py`
- codebook validation reports

What is scattered:

- field-level requiredness validation
- YAML strategy validation
- queue file existence warnings
- promotion gate validation mostly implicit in scripts

Cleanup:

- Extend the YAML renderer/validator to check:
  - all script-declared strategy IDs exist
  - all emitted route IDs exist
  - all status values are known vocab values
  - all source byte classes have eligibility metadata
  - promotion rows satisfy YAML gates
  - report files claiming "current" use dynamic TSV inputs
- Keep codebook column validation, but add graph-level validation.

YAML sections needed:

- `validation_rules`
- `script_contracts`
- `status_vocabularies`

## Files That Should Be Mapped First

This is the first migration set. These files define shared concepts and should
either read YAML or become generated projections from YAML:

| File | Why it matters | Cleanup target |
|---|---|---|
| `scripts/write_provenance_codebook.py` | Owns table list and controlled vocabularies. | Render from YAML. |
| `scripts/build_codebook_pilot_sample.py` | Assigns levels, states, byte classes, file roles, support rows, and manual tasks. | Use YAML gates/vocab/helpers. |
| `scripts/resolve_schema_pilot_real_world_sources.py` | Owns identity grounding logic and source-specific mappings. | Use YAML identity gates and crosswalk definitions. |
| `scripts/push_schema_pilot_to_level5.py` | Owns broad route families, byte classification, blocker classes, and row status columns. | Use YAML routes/resolvers/byte classes. |
| `scripts/resolve_full_article_text_candidates_pilot.py` | Owns full-article route modules, identity gate, candidate ledger, and promotion logic. | Use YAML routes, identity gates, and promotion helper. |
| `scripts/acquire_original_pdfs_pilot.py` | Owns PDF route list and identifier policy. | Use YAML route profile. |
| `scripts/check_original_pdf_identity_pilot.py` | Owns PDF identity gate. | Use YAML identity gate. |
| `scripts/promote_original_pdfs_to_source_file_pilot.py` | Writes L5 state transitions directly. | Use YAML promotion helper. |
| `scripts/build_tail_resolution_queues.py` | Owns active tail bucket definitions. | Move bucket config to YAML. |
| `scripts/plan_level6_source_object_extraction.py` | Owns parser plan and priority. | Move parser plan to YAML. |
| `scripts/extract_level6_text_candidates.py` | Owns candidate statuses and parser routes. | Use YAML parser/verification status vocab. |
| `scripts/verify_schema_pilot_level6_values.py` | Owns CT.gov L6 verification statuses and promotion rule. | Use YAML verification gates. |
| `scripts/build_paper_assets.py` | Owns plot ownership, source-family labels, source catalogs, and collapse rules. | Move plot/source-family rules to YAML. |
| `Makefile` | Exposes strategy runs but does not declare strategy IDs. | Map targets to YAML strategies. |
| `README.md` | Points users at standards but not migration status. | Link current registry/report index. |

## Files That Should Be Registered, Not Immediately Rewritten

These scripts are source-specific or plot-building code. They should be mapped
to YAML entries before anyone tries a broad refactor:

- `scripts/promote_*.py`
- `scripts/parse_*.py`
- `scripts/build_clinifact_*.py`
- `scripts/build_plot3_rescue_candidates.py`
- `scripts/harvest_replication_leads.py`
- `scripts/unlock_political_science_sources.py`
- `scripts/analyze_replication_pairs.py`
- `scripts/build_candidate_d_vs_n.py`
- `scripts/build_published_paper_d_vs_n.py`
- `scripts/build_bibliography.py`

For each one, record:

- source family ID
- strategy ID
- raw input files
- generated output files
- result grain
- conversion method IDs
- relationship mapping IDs used or created
- current limitations

## Concrete Backlog

### P0: Make YAML Match The Current Formal Schema

- Add `tables`, `fields`, and `controlled_vocabularies` to YAML.
- Add missing `source_object_candidate.tsv` template/codebook definition.
- Move `BUCKET_CONFIG` and parser plan definitions into YAML.
- Add byte-class eligibility metadata.
- Add route IDs for current L5/full-article/PDF/Zotero/Wayback routes.

### P1: Add Shared Registry Loader And Validators

- Add `scripts/provenance_common.py`.
- Add `scripts/provenance_pipeline_registry.py`.
- Extend `render_provenance_pipeline_graph.py` to validate table/vocab/route IDs.
- Add a validator that checks current TSV values against YAML vocabularies.

### P2: Make Promotion Code Use YAML Gates

- Refactor PDF promotion and full-article promotion to call a shared L4->L5
  promotion helper.
- Refactor CT.gov verification to call a shared L5->L6 promotion helper.
- Require emitted promotion events to include `promotion_gate_id`.

### P3: Normalize Attempts And Candidates

- Make all acquisition scripts write common `strategy_id`, `route_id`,
  `route_family`, `identity_gate_id`, `source_byte_class`, `decision`, and
  `next_action` values.
- Reconcile full-article attempts, original-PDF attempts, Zotero attempts,
  Wayback attempts, and `source_object_candidate_codebook_sample_300.tsv`.

### P4: Move Plot And Source-Family Rules Into YAML

- Register plot ownership rules now hard-coded in `build_paper_assets.py`.
- Register source families and source-specific scripts.
- Keep the plot-building scripts running, but make their labels and rules
  registry-backed.

### P5: Report Index And Staleness Pass

- Add a generated report index.
- Mark old reports as historical snapshots.
- Keep only `provenance_pipeline_graph.md` and future generated status reports
  as current dynamic status.

## Rule Of Thumb For Migration

If a value answers "what kind of node, edge, route, gate, status, byte class,
queue bucket, source family, plot universe, parser route, or report is this?",
it belongs in YAML.

If a value answers "what happened in this specific run?", it belongs in an
attempt/event/task/output TSV with a `strategy_id` and `route_id` that point
back to YAML.

If a value answers "how do I transform or parse this specific source file?",
the code may implement it, but the conversion method, parser route, and
promotion gate should still be registered in YAML.
