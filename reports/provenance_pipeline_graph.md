# Provenance Pipeline Graph

- Generated: 2026-05-02T02:34:38.126772+00:00
- Spec: `PROVENANCE_PIPELINE_SINGLE_SOURCE_OF_TRUTH.yml`
- Spec root: `PROVENANCE_PIPELINE_SINGLE_SOURCE_OF_TRUTH`
- Schema version: `0.1.0`
- Strategies: 19
- Node types: 18
- Edge types: 19
- Execution DAGs: 1

## Operating Principles

- `search_is_provenance`: Universe search is part of provenance. Search spaces, queries, seed inventories, rejected leads, and promotion decisions should be recorded before locating or acquisition strategies run.

- `leads_before_location`: A possible corpus, paper, registry entry, repository, or project should first become a typed search lead. It should not enter locating or source acquisition until it passes a universe-specific lead-to-target gate.

- `typed_targets`: Treat result targets, represented sources, and evidence objects as different node types. A strategy that discovers one type should not silently promote another type.

- `append_only_attempts`: Search, acquisition, rejection, and manual-access events are evidence. Preserve attempts and decisions instead of overwriting earlier state.

- `source_text_first`: Preserve verbatim source text or source fields before parsing cleaned numeric values.

- `identity_before_acquisition`: Identity-blocked rows need crosswalk or bibliographic repair before more download attempts.

- `strict_level5`: Metadata pages, abstracts, paywalls, CAPTCHA pages, and access-denied pages are acquisition evidence, but they are not level-5 source objects unless they actually contain the plotted value.

- `zotero_is_capture_not_authority`: Zotero can help discover and capture files, but accepted evidence comes only after local hashing, identity review, and source_file/source_access promotion.

- `catalog_everything_but_focus_current_figures`: Do not discard leads, sources, candidates, sidecars, comparators, or excluded rows. Catalog and enumerate them with status and reason, while keeping active build focus on the three current figures.


## Current Figure Focus

| Figure | Universe | Role | Plain English |
| --- | --- | --- | --- |
| 1 | plot1_replication_pairs | current_figure | Larger-N replication or follow-up results paired to their original results. |
| 2 | plot2_published_paper_d_vs_n | current_figure | Eventually published paper/result endpoints with recoverable D/N. |
| 3 | plot3_preregistered_results | current_figure | Eventually published preregistered, registered, PAP, or planned results with recoverable D/N. |

| Catalog Universe | Role |
| --- | --- |
| plot4_all_source_dn_dump | catalog_only_future_plot_seed |

Catalog policy:

- Every discovered lead should be represented as a typed search lead, source row, candidate row, manual task, or explicit rejection.
- Excluded, comparator, sidecar, duplicate, metadata-only, and not-yet-parseable sources stay in catalogs with a reason; they are not deleted.
- Future plot ideas should consume cataloged sources later instead of changing the admission rules for the three active figures now.
- The all-source D/N dump is a diagnostic catalog and future-plot seed, not an active fourth figure for the current scope.

## Database Schema Contract

Keep the database adaptable as we test different plot universes and later define new figures. Durable facts about sources, files, mappings, and result assertions are stored once. Plot-specific choices are stored as context-scoped memberships and decisions, so a future plot can use different criteria without rewriting or deleting the underlying evidence.


Operating rules:

- Search leads are not sources yet. A lead is a possible corpus, database, project, registry record, paper, replication paper, or file discovered under a search context.

- Sources are citeable or computational objects. Corpora, databases, papers, registries, repositories, packages, PDFs, raw files, and derived tables can all be sources.

- Source relationships are first-class rows. Use mappings for corpus contains paper, database reports result, registry links publication, preregistration supports study, replication of, and repository supports paper.

- Source results are assertions at the lowest useful result grain. A source_result row says one extraction source exposed one result about one represented source.

- Canonical results resolve duplicates or collapse child rows, but they should not decide whether a row belongs to a particular figure.

- Plot membership is the context layer. The same canonical result can be included, excluded, diagnostic-only, or sensitivity-only under different plot_universe criteria.

- Failed, excluded, duplicate, sidecar, comparator, and catalog-only rows remain in the database with status and reasons. Plot exclusion is never deletion.


| Layer | Context Sensitivity | Tables | Grains |
| --- | --- | --- | --- |
| search_context | context_scoped | search_lead.tsv, provenance_search_plan.tsv | search_lead.tsv: One discovered lead under one search track or universe., provenance_search_plan.tsv: One search track for one plot universe. |
| source_catalog | mostly_context_free | source.tsv, source_identifier.tsv, source_classification.tsv | source.tsv: One citeable or computational source object., source_identifier.tsv: One external identifier for one source., source_classification.tsv: One classification assertion for one source. |
| access_and_files | context_free_attempt_log | source_access.tsv, source_access_attempt.tsv, source_file.tsv, source_version.tsv, source_access_right.tsv | source_access.tsv: One usable or documented access route for one source., source_access_attempt.tsv: One attempted resolver, route, query, download, browser, or file action., source_file.tsv: One mirrored byte artifact or extracted archive member., source_version.tsv: One version assertion for one source., source_access_right.tsv: One rights or storage decision for one source/file. |
| relationship_graph | reusable_evidence | source_source_mapping.tsv | source_source_mapping.tsv: One directed relationship between two sources. |
| result_assertions | reusable_evidence | source_result.tsv, source_result_support.tsv | source_result.tsv: One result asserted or exposed by one extraction source., source_result_support.tsv: One field-level support locator for one source-result decision. |
| canonicalization | reusable_with_policy_id | canonical_result.tsv, canonical_result_membership.tsv | canonical_result.tsv: One deduplicated or policy-collapsed result., canonical_result_membership.tsv: One source-result member of one canonical result. |
| plot_context | context_scoped | plot_universe.tsv, plot_criterion.tsv, plot_membership.tsv | plot_universe.tsv: One reusable plot or statistic-set context., plot_criterion.tsv: One reusable inclusion, exclusion, or context criterion., plot_membership.tsv: One canonical result evaluated under one plot universe. |
| work_audit | append_only_or_queue | extraction_event.tsv, extraction_problem.tsv, manual_acquisition_task.tsv | extraction_event.tsv: One action or failed action., extraction_problem.tsv: One quality/provenance problem., manual_acquisition_task.tsv: One human/manual acquisition or verification task. |

300-sample lessons:

- The corpus/paper/result split is right, but it needs a search-lead layer above it so corpus databases and individual replication papers can enter the pipeline before we know whether they produce usable result rows.

- The same real-world source can play multiple roles: a corpus can be an extraction source, a paper can be a represented source, a registry can be both source object and preregistration mapping, and a repository can be relationship evidence plus bytes.

- Plot criteria should be versioned context decisions. Figure 1, Figure 2, Figure 3, diagnostics, and future plots should reuse the same source and result rows while changing only plot_universe, plot_criterion, and plot_membership decisions.


## Execution DAGs

### `figure1_corpora_database_intake_dag`

- Scope: `plot1_replication_pairs`
- Status: `active_foundation`
- Principle: Keep top-of-pipeline corpus/database intake acyclic by treating generated artifacts as versioned snapshots. The previous CORPORA_AND_DATABASES.tsv snapshot may be read as merge context; the current CORPORA_AND_DATABASES.tsv snapshot is the output of the merge step. There is no table-to-itself edge.

- Topological order: pipeline_spec_root_yml -> local_seed_artifacts -> corpora_databases_previous_snapshot -> codex_triage_previous_decisions -> review_cue_previous_receipts -> render_search_plan_step -> figure1_corpora_search_runner_step -> source_artifacts_schema -> provenance_search_plan_artifacts -> concrete_new_source_search_outputs -> corpora_databases_consolidation_step -> corpora_databases_master_table -> corpora_databases_schema -> search_yield_summary_step -> deterministic_triage_queue_step -> search_yield_summary_artifacts -> codex_triage_queue_artifact -> codex_triage_batch_artifact -> gpt_triage_batch_artifact -> alias_cluster_step -> codex_triage_decisions -> alias_cluster_artifacts -> review_cue_decision_application -> clustered_review_cue_step -> downstream_corpus_triage_and_parsing -> review_cue_receipts -> review_cue_routing_table -> clustered_review_cue_artifacts -> corpora_table_update_proposal_step -> clustered_review_decisions -> corpora_table_update_proposal_artifacts -> gpt_field_coding_prompt_artifact -> clustered_review_decision_application -> clustered_review_routing_artifacts -> source_family_artifact_inventory_queue -> clustered_review_worklist_fanout_step -> source_family_artifact_inventory_step -> clustered_review_worklist_artifacts -> source_artifacts_proposal

| Node | Kind | Materialized As | Role | Dedupe Order |
| --- | --- | --- | --- | --- |
| pipeline_spec_root_yml | specification | PROVENANCE_PIPELINE_SINGLE_SOURCE_OF_TRUTH.yml | Defines plot universes, search tracks, target contracts, and DAG edges. |  |
| render_search_plan_step | script_step | scripts/render_provenance_search_plan.py | Renders top-of-pipeline search tracks from the root YAML. |  |
| provenance_search_plan_artifacts | generated_artifacts | data/derived/effect_inflation_dataset/provenance_search_plan.tsv, reports/provenance_universe_search_plan.md | Human-readable and machine-readable search plan. |  |
| local_seed_artifacts | input_artifact_set | data/derived/effect_inflation_dataset/plot1_replication_source_catalog.csv, data/raw/replication_projects/lead_registry.csv, data/derived/replication_pairs/replication_source_worklist.csv, data/raw/corpus_candidates, data/raw/replication_projects, reports/corpus_suggestion_tracker.md, reports/corpus_candidates/replication_lead_queue.md | Existing local evidence that should flow directly into the root corpus/database table. |  |
| concrete_new_source_search_outputs | optional_input_artifact_set | steps/searches/figure1/corporasearch-*.{tsv,csv,json} | Concrete query/search outputs, one file per method plus search-term/scope combination. These are not mirrors of the root table.  |  |
| figure1_corpora_search_runner_step | script_step | scripts/search_figure1_corpora_databases.py, make figure1-corpora-search-expanded | Writes skip-safe Figure 1 search target manifests. Baseline and expanded searches use distinct corporasearch-* filenames so exact searches can be skipped by file existence unless --replace is set.  |  |
| search_yield_summary_step | script_step | scripts/summarize_figure1_search_yield.py, make figure1-corpora-search-yield | Diagnostic fan-in over saved search manifests. It compares baseline and expanded search manifests against each other and the current root table to reveal marginal yield and diminishing returns.  |  |
| search_yield_summary_artifacts | generated_artifacts | steps/searches/figure1/searchyield-figure1-corpusdb-summary.tsv, steps/searches/figure1/searchyield-figure1-corpusdb-expanded-new-leads.tsv, steps/searches/figure1/searchyield-figure1-corpusdb-summary.md | Machine-readable and human-readable search-yield diagnostics. These files do not use the corporasearch-* prefix and are not consumed as root-table lead manifests.  |  |
| source_artifacts_schema | schema_placeholder | SOURCE_ARTIFACTS_SCHEMA.yml, SOURCE_ARTIFACTS.tsv | Root-level placeholder schema/table for child artifacts under source-family rows. It keeps CORPORA_AND_DATABASES.tsv at the source-family grain while concrete OSF components, repository files, workbooks, local mirrors, and parser candidates can be inventoried separately.  |  |
| alias_cluster_step | script_step | scripts/cluster_figure1_search_leads.py, make figure1-cluster-search-leads | Read-only bridge from search leads to source-family review. It consumes the root table, corporasearch manifests, review queue, and receipt targets, then groups exact identifiers and high-confidence source-family hints into cluster/priority artifacts.  |  |
| alias_cluster_artifacts | generated_artifacts | steps/searches/figure1/alias-clusters-leads-artifacts-root-v001.json, steps/review_cue/figure1_search_leads/clustered-priority-queue.tsv, steps/review_cue/figure1_search_leads/clustered-priority-queue-summary.tsv | Machine-readable alias/source-family clusters and a review-priority queue. These artifacts are not root-table mutations; they tell Codex/GPT which cluster representative and aliases to review first.  |  |
| clustered_review_cue_step | script_step | scripts/build_clustered_review_cue.py, make figure1-cluster-review-cue | Builds a bounded Codex prompt over source-family clusters instead of isolated leads. The output is a review handoff artifact; it does not apply decisions or edit root tables.  |  |
| clustered_review_cue_artifacts | generated_artifacts | steps/review_cue/figure1_search_leads/reviewcue-clustered-codex-*-figure1_search_leads.json, steps/review_cue/figure1_search_leads/reviewcue-clustered-codex-*-figure1_search_leads-prompt.md | Cluster-level review batches showing representative source-family leads plus linked aliases/artifacts. Decisions from these batches still need a later application adapter before they can write receipt targets.  |  |
| clustered_review_decisions | optional_human_llm_artifact_set | steps/review_cue/figure1_search_leads/reviewcue-clustered-decisions-figure1_search_leads-codex-*.json | Cluster-level Codex/GPT/human decisions. These decide whether a source-family cluster should become an artifact-inventory task, remain a source-family candidate, route to result-table or individual-paper worklists, or stop as context.  |  |
| clustered_review_decision_application | script_step | scripts/apply_clustered_review_decisions.py, make apply-cluster-review-cue | Applies clustered decisions without editing root tables. It writes one receipt target per reviewed cluster, a clustered routing table, and a source-family artifact inventory queue.  |  |
| clustered_review_routing_artifacts | generated_artifacts | steps/review_cue/figure1_search_leads/cluster_receipts/*/*.json, steps/review_cue/figure1_search_leads/reviewcue-clustered-routing-table-figure1_search_leads.tsv, steps/review_cue/figure1_search_leads/reviewcue-clustered-routing-table-figure1_search_leads.json | Machine-readable cluster-level routing fan-in. Downstream steps can consume these artifacts instead of re-spending review attention on the same cluster.  |  |
| source_family_artifact_inventory_queue | generated_artifact | steps/source_inventory/figure1/source-family-artifact-inventory-queue.tsv, steps/source_inventory/figure1/source-family-artifact-inventory-queue.json | Queue of source families whose child artifacts need inventory, dedupe, parser assignment, and later SOURCE_ARTIFACTS.tsv proposals.  |  |
| source_family_artifact_inventory_step | script_step | scripts/inventory_source_family_artifacts.py, make source-family-artifact-inventory | Proposal-only inventory step. It consumes reviewed source-family inventory tasks, fingerprints local mirrors, records provider manifest entries, assigns coarse parser families, and writes SOURCE_ARTIFACTS.tsv-shaped proposals without editing the root artifact table.  |  |
| source_artifacts_proposal | generated_artifacts | steps/source_inventory/figure1/source-artifacts-proposal.tsv, steps/source_inventory/figure1/source-artifacts-proposal.json, steps/source_inventory/figure1/source-artifact-inventory-summary.tsv, steps/source_inventory/figure1/source-artifacts-proposal-validation.tsv, steps/source_inventory/figure1/*/inventory-source-artifacts-proposal-*.tsv, steps/source_inventory/figure1/*/inventory-source-artifacts-proposal-*.json | Machine-readable SOURCE_ARTIFACTS.tsv proposal outputs. These separate source-family parent rows from concrete child artifacts such as CSVs, workbooks, provider manifests, download metadata, scripts, PDFs, and archive files.  |  |
| clustered_review_worklist_fanout_step | script_step | scripts/build_cluster_review_worklists.py, make cluster-review-worklists | Fans non-inventory clustered decisions into downstream target files so result-table and individual-paper routes are not trapped inside the general clustered routing table.  |  |
| clustered_review_worklist_artifacts | generated_artifacts | steps/result_tables/figure1/result-table-worklist-from-cluster-review.tsv, steps/result_tables/figure1/result-table-worklist-from-cluster-review.json, steps/individual_replication_papers/figure1/individual-paper-worklist-from-cluster-review.tsv, steps/individual_replication_papers/figure1/individual-paper-worklist-from-cluster-review.json | Machine-readable worklists for clusters routed to result-table extraction or individual replication-paper/package review.  |  |
| corpora_databases_previous_snapshot | versioned_prior_artifact | CORPORA_AND_DATABASES.tsv@previous | Optional prior master-table state used only to preserve existing nonblank decisions during safe merge. |  |
| corpora_databases_consolidation_step | script_step | scripts/build_corpora_and_databases_table.py | Fan-in merge step. It reads local seeds plus every steps/searches/figure1/corporasearch-* target file, normalizes rows, dedupes search leads by conservative exact title keys, then by DOI, normalized URL, source key, and corpus ID fallback, then writes the root corpus/database table.  | conservative exact title key for search leads only, DOI found in source_key, landing_url, raw_url, or notes, normalized landing_url or raw_url, source_key, existing corpus_database_id fallback |
| corpora_databases_master_table | generated_artifact | CORPORA_AND_DATABASES.tsv | Single root-level intake table for discovered corpus/database-like sources. |  |
| corpora_databases_schema | generated_artifact | CORPORA_AND_DATABASES_SCHEMA.yml | Human/LLM-readable schema for the root corpus/database table. |  |
| deterministic_triage_queue_step | script_step | scripts/build_review_cue.py --cue-id figure1_search_leads, scripts/build_figure1_codex_triage_batches.py | Reusable review-cue builder. It reads configured manifests and the current root target, skips leads already in target tables or already reviewed, preserves deterministic routed/rejected records, and writes bounded Codex and GPT prompt batches only for unresolved leads. The Figure 1 specific script is retained as a legacy wrapper until decision application is centralized.  |  |
| codex_triage_queue_artifact | generated_artifact | steps/review_cue/figure1_search_leads/reviewcue-queue-figure1_search_leads.json, steps/triage/figure1/codextriage-queue-figure1-search-leads.json | All unresolved reviewable search leads after deterministic skips. |  |
| codex_triage_batch_artifact | generated_artifact | steps/review_cue/figure1_search_leads/reviewcue-codex-*-figure1_search_leads.json, steps/review_cue/figure1_search_leads/reviewcue-codex-*-figure1_search_leads-prompt.md, steps/triage/figure1/codextriage-batch*-figure1-search-leads.json, steps/triage/figure1/codextriage-batch*-figure1-search-leads-prompt.md | Bounded on-demand Codex review batch with prompt and lead records. Codex can investigate sources and return decisions; uncertain cases should include user_gpt_prompt_request text.  |  |
| gpt_triage_batch_artifact | generated_artifact | steps/review_cue/figure1_search_leads/reviewcue-gpt-*-figure1_search_leads.json, steps/review_cue/figure1_search_leads/reviewcue-gpt-*-figure1_search_leads-prompt.md | Larger user-mediated GPT Pro prompt batch. The Markdown prompt is a handoff artifact: copy it into GPT, then paste the JSON result back as a decisions artifact.  |  |
| codex_triage_previous_decisions | versioned_prior_artifact | steps/triage/figure1/codextriage-decisions-figure1-*.json@previous | Prior Codex/human decisions from earlier review batches. These are read only to skip already reviewed leads when building a new queue.  |  |
| review_cue_previous_receipts | versioned_prior_artifact | steps/review_cue/figure1_search_leads/receipts/*/*.json@previous | Prior per-lead receipt target files. These are read only to skip already routed, rejected, kept, or escalated leads when building a new review cue.  |  |
| codex_triage_decisions | optional_human_llm_artifact_set | steps/review_cue/figure1_search_leads/reviewcue-decisions-figure1_search_leads-*.json, steps/triage/figure1/codextriage-decisions-figure1-*.json | Explicit Codex/human decisions that can later promote, route, or reject ambiguous leads. |  |
| review_cue_receipts | generated_artifact | steps/review_cue/figure1_search_leads/receipts/*/*.json | One target-file receipt per reviewed lead. Future review-cue builds skip reviewed leads by these files before spending more human, Codex, or GPT attention.  |  |
| review_cue_routing_table | generated_artifact | steps/review_cue/figure1_search_leads/reviewcue-routing-table-figure1_search_leads.tsv, steps/review_cue/figure1_search_leads/reviewcue-routing-table-figure1_search_leads.json | Machine-readable fan-in table generated from validated receipt targets. This is the artifact downstream scripts consume to see what advances, routes to another worklist, stays context-only, or stops.  |  |
| review_cue_decision_application | script_step | scripts/apply_review_cue_decisions.py, scripts/build_review_cue_routing_table.py, make apply-review-cue, make review-cue-routing-table | Receipt application is active: it consumes Codex/GPT decision JSON and emits per-lead receipt target files, then materializes a machine-readable routing table from those receipts.  |  |
| corpora_table_update_proposal_step | script_step | scripts/build_corpora_table_update_proposal.py, make corpora-table-update-proposal | Last-mile proposal step. It consumes the review-cue routing table, matches decisions to existing CORPORA_AND_DATABASES.tsv rows, writes a proposal, validation table, updated preview, and a GPT field-coding prompt for accepted rows whose prose/semantic fields are still undercoded. It does not mutate the root table.  |  |
| corpora_table_update_proposal_artifacts | generated_artifacts | steps/review_cue/figure1_search_leads/apply_to_CORPORA_AND_DATABASES/corpora-table-update-proposal.tsv, steps/review_cue/figure1_search_leads/apply_to_CORPORA_AND_DATABASES/corpora-table-update-validation.tsv, steps/review_cue/figure1_search_leads/apply_to_CORPORA_AND_DATABASES/corpora-table-updated-preview.tsv | Machine-readable proposed status/field updates and validation preview before any root-table mutation. |  |
| gpt_field_coding_prompt_artifact | generated_artifact | steps/review_cue/figure1_search_leads/apply_to_CORPORA_AND_DATABASES/gpt-field-coding-needed.tsv, steps/review_cue/figure1_search_leads/apply_to_CORPORA_AND_DATABASES/gpt-field-coding-prompt-*.md | User-mediated GPT cue for accepted rows whose prose/semantic target fields need source-aware coding. |  |
| downstream_corpus_triage_and_parsing | future_step_family | future source/source_result/mapping tables | Later steps that split accepted corpus/database rows into detailed provenance tables. |  |

| From | To | Edge Kind |
| --- | --- | --- |
| pipeline_spec_root_yml | render_search_plan_step | defines |
| render_search_plan_step | provenance_search_plan_artifacts | writes |
| provenance_search_plan_artifacts | concrete_new_source_search_outputs | guides_future_searches |
| pipeline_spec_root_yml | figure1_corpora_search_runner_step | defines_queries_and_targets |
| figure1_corpora_search_runner_step | concrete_new_source_search_outputs | writes |
| concrete_new_source_search_outputs | search_yield_summary_step | input_to |
| corpora_databases_master_table | search_yield_summary_step | novelty_context_for |
| search_yield_summary_step | search_yield_summary_artifacts | writes |
| pipeline_spec_root_yml | source_artifacts_schema | defines_child_artifact_placeholder |
| pipeline_spec_root_yml | alias_cluster_step | defines_cluster_targets |
| concrete_new_source_search_outputs | alias_cluster_step | input_to |
| corpora_databases_master_table | alias_cluster_step | input_to |
| codex_triage_queue_artifact | alias_cluster_step | priority_context_for |
| review_cue_previous_receipts | alias_cluster_step | reviewed_context_for |
| alias_cluster_step | alias_cluster_artifacts | writes |
| alias_cluster_artifacts | clustered_review_cue_step | input_to |
| clustered_review_cue_step | clustered_review_cue_artifacts | writes |
| clustered_review_cue_artifacts | clustered_review_decisions | reviewed_into |
| clustered_review_decisions | clustered_review_decision_application | input_to |
| clustered_review_decision_application | clustered_review_routing_artifacts | writes |
| clustered_review_decision_application | source_family_artifact_inventory_queue | writes |
| clustered_review_routing_artifacts | clustered_review_worklist_fanout_step | input_to |
| clustered_review_worklist_fanout_step | clustered_review_worklist_artifacts | writes |
| source_family_artifact_inventory_queue | source_family_artifact_inventory_step | input_to |
| source_artifacts_schema | source_family_artifact_inventory_step | defines_output_shape |
| source_family_artifact_inventory_step | source_artifacts_proposal | writes |
| pipeline_spec_root_yml | corpora_databases_consolidation_step | defines_schema_and_merge_rules |
| local_seed_artifacts | corpora_databases_consolidation_step | normalized_into |
| concrete_new_source_search_outputs | corpora_databases_consolidation_step | optional_input_to |
| corpora_databases_previous_snapshot | corpora_databases_consolidation_step | optional_merge_context |
| corpora_databases_consolidation_step | corpora_databases_master_table | writes |
| corpora_databases_consolidation_step | corpora_databases_schema | writes |
| concrete_new_source_search_outputs | deterministic_triage_queue_step | secondary_triage_input_to |
| corpora_databases_master_table | deterministic_triage_queue_step | skip_already_in_target_context |
| codex_triage_previous_decisions | deterministic_triage_queue_step | skip_already_reviewed_context |
| review_cue_previous_receipts | deterministic_triage_queue_step | skip_already_reviewed_context |
| deterministic_triage_queue_step | codex_triage_queue_artifact | writes |
| deterministic_triage_queue_step | codex_triage_batch_artifact | writes |
| deterministic_triage_queue_step | gpt_triage_batch_artifact | writes |
| codex_triage_batch_artifact | codex_triage_decisions | reviewed_on_demand_into |
| gpt_triage_batch_artifact | codex_triage_decisions | reviewed_on_demand_into |
| codex_triage_decisions | review_cue_decision_application | promotion_or_routing_input |
| review_cue_decision_application | review_cue_receipts | writes |
| review_cue_decision_application | review_cue_routing_table | writes |
| review_cue_routing_table | corpora_table_update_proposal_step | input_to |
| corpora_databases_master_table | corpora_table_update_proposal_step | match_context_for |
| corpora_table_update_proposal_step | corpora_table_update_proposal_artifacts | writes |
| corpora_table_update_proposal_step | gpt_field_coding_prompt_artifact | writes_when_fields_need_prose_coding |
| corpora_databases_master_table | downstream_corpus_triage_and_parsing | feeds |
| source_artifacts_schema | downstream_corpus_triage_and_parsing | defines_child_artifact_grain_for |
| alias_cluster_artifacts | downstream_corpus_triage_and_parsing | prioritizes_source_family_inventory_for |

## Plot Universe Criteria Registry

| Criterion | Gate Type | Rule | Accept If | Reject If | Evidence Fields |
| --- | --- | --- | --- | --- | --- |
| source_family_recorded | required_context | Candidate source rows must carry a canonical source family or source key so inclusion, exclusion, comparator, and duplicate decisions are auditable at source-family grain.  |  |  | source_family, source_key, display_label, citation_key |
| candidate_artifact_or_backing_file_recorded | required_context | The source table, package, workbook, registry export, article, or other artifact that exposed the candidate rows must be named by path or URL.  |  |  | backing_file, backing_path, raw_file, candidate_artifact_path_or_url |
| represented_result_ever_published | include_if_true | The represented result, outcome, claim, trial result, paper result, or project-level planned result has evidence of a citable published report of that same result at some point in the world. The plotted value does not have to be extracted from the publication itself; it may come from a registry record, PAP package, corpus workbook, project table, or source data if the row-level result can be linked to a published report.  | A DOI, PMID, PMCID, publisher URL, Crossref/OpenAlex work, or stable journal article citation is linked to the represented result., A registry record, NCT/AEA/OSF/EGAP/PAP entry, or project package links to a publication and the registered/planned outcome maps to the plotted result., A corpus row supplies article DOI/title/journal/year evidence and the result row is one of the corpus-coded published results., A publication exists for the project and the source table records the plotted row as that publication's planned, primary, focal, matched, or confirmatory result. | The only publication is about the corpus, dataset, registry snapshot, or extraction method rather than the represented result., The only evidence is a registration, PAP, project page, repository package, dataset DOI, conference abstract, or metadata record with no published result report., A paper exists for the study or trial but the plotted outcome/result cannot be mapped to a result reported in that paper., The publication link is only a loose topic/title similarity with no trial ID, DOI, PMID, registry reference, outcome match, or corpus crosswalk. | publication_link_status, published_report_identifier_type, published_report_identifier_value, published_report_doi, published_report_pmid, published_report_pmcid, published_report_url, article_title, journal, publication_year, nct_id, registry_id, publication_link_plausibility, publication_match_quality, result_publication_match_basis |
| result_effect_convertible_to_common_d_axis | include_if_true | The candidate row exposes D directly, a common D/Z-compatible effect, or deterministic conversion inputs that the local parser maps to the common D-like axis.  |  |  | D, D_median, original_d, replication_d, native_statistic_type, conversion_formula_id |
| result_n_available | include_if_true | The candidate row exposes analytic N, arm/group Ns, enrollment N accepted by that plot policy, or deterministic fields from which the plotted N is derived.  |  |  | N, N_median, original_N, replication_N, group1_n, group2_n, enrollment |
| positive_d_and_n | include_if_true | The plotted or diagnostic D/N surface requires positive D and positive N after the source-specific parser and row policy are applied.  |  |  | D, D_median, N, N_median |
| paper_or_study_unit_identified | include_if_true | The candidate can be grouped to a paper, study, trial, registry record, project, or corpus-defined paper/study unit before plotting.  |  |  | unit_id, paper_id, doi, nct_id, registry_id, represented_source_id |
| one_row_per_paper_or_policy_collapse | include_if_true | If a source can emit multiple rows per paper, project, trial, or source unit, the plot has an explicit collapse or selection policy before the row enters the plotted layer.  |  |  | collapse_unit, rows_with_implemented_paper_collapse, rows_currently_plotted, plot_rows_made_in |
| selector_status_recorded | required_context | The source must explicitly record whether the row is a main, focal, primary, planned, matched, critical, treatment-arm, comparator, random, or unknown-selector row. Unknown selector status is allowed only when the plot labels it as a caveat rather than treating it as main-result evidence.  |  |  | main_selector_status, rows_with_explicit_main_selector, selector_evidence_type, status_label, why_in_out |
| explicit_original_followup_pair_mapping | include_if_true | Plot 1 rows must link one original-side result to one replication, follow-up, repeated-study, pilot/full-scale, or otherwise larger-N follow-up-side result.  |  |  | original_source_hint, replication_source_hint, relationship_mapping_basis, source_mapping_ids |
| both_sides_n_at_least_10 | include_if_true | Plot 1 keeps only paired rows where original-side N and replication-side N are both at least 10 after rows missing D/Z or N have already failed.  |  |  | original_N, replication_N, blocked_N_lt_10 |
| followup_n_greater_than_original_n | include_if_true | Plot 1 keeps only paired rows where the replication/follow-up N is strictly larger than the original N.  |  |  | original_N, replication_N, blocked_replication_N_le_original_N |
| aggregate_only_without_row_level_result_excluded | exclude_if_true | Aggregate-only summaries, reviews, or narrative descriptions are out when no row-level result or deterministic row-level reconstruction is available.  |  |  | excluded_reason_code, blocker_codes, why_in_out |
| published_paper_scope_not_registry_only | include_if_true | Plot 2 rows must be published-paper endpoints or paper-linked published source estimates. Registry-only, GWAS-catalog-only, and raw registry-result surfaces are comparators unless they are explicitly bridged to a journal-side paper endpoint.  |  |  | published_scope, rows_with_direct_journal_provenance, plot_inclusion_status, why_in_out |
| not_all_tests_without_selector_or_collapse | exclude_if_true | All-test corpora are out of Plot 2 unless the current build has an implemented paper/result collapse or a defensible focal-result selector. This is why row-level test surfaces such as statcheck remain out even when D/N is technically recoverable.  |  |  | known_test_rows, rows_with_implemented_paper_collapse, rows_with_explicit_main_selector, status_label |
| comparator_only_excluded_from_primary_plot | exclude_if_true | Comparator-only, random-effect, negative-claim, registry-only, sidecar, or sensitivity rows are excluded from a primary plot universe unless that universe is explicitly the all-source diagnostic dump.  |  |  | comparator_only, plot_inclusion_status, inclusion_role, why_in_out |
| explicit_preregistered_confirmatory_selector | include_if_true | Plot 3 rows must be analytically preregistered, registered-primary, matched to a preregistered hypothesis, PAP-governed, registered-report confirmatory, or otherwise preregistered-confirmatory equivalent.  |  |  | rows_preregistered_equivalent, preregistration_timing_status, selector_evidence_type, prereg_mapping_id |
| public_local_backing_for_prereg_row | include_if_true | Plot 3 rows must have public or locally mirrored backing for the registration, source table, package, workbook, registry export, or article-level result assertion used by the parser.  |  |  | rows_with_public_local_backing, backing_file, source_file_id |
| non_retracted_source | include_if_true | Plot 3 excludes rows whose represented source is retracted or otherwise marked as not admissible under the current non-retraction policy.  |  |  | rows_with_non_retracted_source, retraction_status, why_in_out |
| planned_result_median_collapse_allowed | include_if_true | Plot 3 may include multiple planned or matched preregistered results from the same paper/project only after applying the current median collapse policy at the declared paper/project unit.  |  |  | collapse_unit, rows_left_out_within_source, plot_rows_made_in |
| duplicate_nested_or_sidecar_evidence_excluded | exclude_if_true | Rows are out of a primary plot when they duplicate a stricter source, are nested inside an already-counted parent source, or are retained only as sidecar/comparator evidence.  |  |  | duplicate_status, source_mapping_ids, plot_inclusion_status, why_in_out |
| diagnostic_source_family_role_recorded | include_if_true | Plot 4 requires every source family to record whether it is included, included as sidecar, not included because already folded into another source, or retained only as comparator/exclusion context.  |  |  | plot_inclusion_status, inclusion_rule, remaining_caveat |
| not_duplicate_of_parent_dump_source | exclude_if_true | Plot 4 does not separately load rows from a child artifact when those rows are already folded into a parent dump source, because that would double-count the same D/N surface.  |  |  | plot_inclusion_status, inclusion_rule, remaining_caveat |
| staged_sidecar_rows_have_positive_side_dn | include_if_true | Plot 4 may include non-promoted staged sidecar rows only when the staged artifact already exposes a positive D and N for that side.  |  |  | D, N, source_side, inclusion_rule |
| metadata_or_narrative_only_excluded | exclude_if_true | Metadata records, abstracts, landing pages, narrative reviews, access pages, and citation-only leads are out unless the plotted value itself is present or a downstream source-object route emits value-bearing rows.  |  |  | source_byte_class, barrier_class, candidate_status, rejection_reason |

## Plot Universes

| Universe | Figure | Current Scope | Result Target | Publication Required | Publication Policy | Search Direction | Search Policy | Output Unit | Required Criteria | Applicable Criteria | Exclusion Criteria | Represented Sources | Evidence Objects |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| plot1_replication_pairs | Figure 1 | current_figure | replication_pair_result | not_required | Figure 1 is about paired original and replication/follow-up results. It does not require the represented result to have ever been published, because valid pair evidence can come from replication projects, source tables, project packages, or coordinated follow-up datasets.  | replication_first_then_resolve_original | Figure 1 search should start from replication, follow-up, repeated-study, pilot/full-scale, and coordinated replication sources. Do not begin by enumerating ordinary original articles and hoping to find later replications. Once a replication/follow-up lead is found, resolve both sides of the pair: the replication/follow-up result and the original result it targets.  | One original-side result paired to one larger-N replication or follow-up-side result. Approved Appendix D fallback rows can enter only if already plot-ready under the same D/N policy.  | source_family_recorded, candidate_artifact_or_backing_file_recorded, explicit_original_followup_pair_mapping, result_effect_convertible_to_common_d_axis, result_n_available, both_sides_n_at_least_10, followup_n_greater_than_original_n |  | aggregate_only_without_row_level_result_excluded, metadata_or_narrative_only_excluded | original_study, replication_study, replication_project | article_fulltext, replication_project_table, replication_package_code, preregistration_or_protocol |
| plot2_published_paper_d_vs_n | Figure 2 | current_figure | published_paper_result_or_paper_median | required | Figure 2 requires the represented result to have a citable published report. The plotted D/N may come from a corpus, source table, or conversion pipeline, but the row must be linked to a published paper or published paper-level result rather than only to a registry, dataset, repository, or extraction-method publication.  |  |  | One published-paper or corpus-defined paper/study unit after the source-specific paper collapse or focal-result rule is applied.  | source_family_recorded, candidate_artifact_or_backing_file_recorded, represented_result_ever_published, published_paper_scope_not_registry_only, paper_or_study_unit_identified, result_effect_convertible_to_common_d_axis, result_n_available, one_row_per_paper_or_policy_collapse, selector_status_recorded |  | not_all_tests_without_selector_or_collapse, comparator_only_excluded_from_primary_plot, metadata_or_narrative_only_excluded | journal_article, article_level_corpus_source | article_fulltext, corpus_workbook_row, supplement, raw_or_analytic_data |
| plot3_preregistered_results | Figure 3 | current_figure | preregistered_or_registry_result | required | Figure 3 requires the represented preregistered or registered result to have eventually been reported in a citable publication. The publication does not have to be the source object for the plotted D/N; a registry, PAP package, OSF workbook, Dataverse package, or project table can still supply the value if the represented result is mapped to a published report.  |  |  | One preregistered-confirmatory result, registered primary result, or declared paper/project median over explicitly matched planned results.  | source_family_recorded, candidate_artifact_or_backing_file_recorded, represented_result_ever_published, explicit_preregistered_confirmatory_selector, public_local_backing_for_prereg_row, paper_or_study_unit_identified, result_effect_convertible_to_common_d_axis, result_n_available, non_retracted_source, one_row_per_paper_or_policy_collapse | planned_result_median_collapse_allowed | comparator_only_excluded_from_primary_plot, duplicate_nested_or_sidecar_evidence_excluded, metadata_or_narrative_only_excluded | registered_trial, preregistered_study, paper_with_preregistration, pap_or_registry_record | registry_json, registry_html, pre_analysis_plan, article_fulltext, result_table |
| plot4_all_source_dn_dump | not_current_figure | catalog_only_future_plot_seed | source_dump_result | mixed | The all-source D/N dump is a diagnostic catalog, not an active current figure. It should preserve whether each source family is published, unpublished, registry-only, package-backed, sidecar, comparator, or already folded into another source, but publication is not a universal admission gate.  |  |  | One diagnostic D/N row from any source family, including original and follow-up sides from replication pairs, published-paper paper units, preregistered rows, and explicitly admitted sidecar rows.  | source_family_recorded, candidate_artifact_or_backing_file_recorded, positive_d_and_n, diagnostic_source_family_role_recorded | staged_sidecar_rows_have_positive_side_dn | not_duplicate_of_parent_dump_source, metadata_or_narrative_only_excluded | any_source_family | source_dump_row, registry_record, article_fulltext, dataset, code_output |

## Stages

| Rank | Stage | Question | Primary Outputs |
| --- | --- | --- | --- |
| 5 | universe_search | Where do possible result targets for this universe come from? | search_space, search_query, search_lead |
| 10 | universe_definition | What candidate rows belong to this plot or sample? | plot_universe, result_target, canonical_result |
| 20 | retrace_assertion | Where did the current plotted number come from? | extraction_source, result_target |
| 30 | identity_resolution | What real-world represented source is the result about? | represented_source, source_identifier, source_mapping |
| 40 | locating | Where might source bytes or authoritative records be found? | access_route, source_object_candidate |
| 50 | obtaining | Can we lawfully obtain and mirror value-bearing bytes? | source_file, source_access, source_access_attempt |
| 60 | confirmation | Is this candidate the right represented source and an eligible byte class? | source_file, promotion_event |
| 70 | extraction | Where are exact effect, N, selector, or conversion-input fields inside the source object? | source_result_support |
| 80 | verification | Do source text, fields, data, or code verify the plotted D/N? | source_result_support, promotion_event |
| 90 | manual_followup | What requires human access, author contact, library access, rights review, or identity review? | manual_task |

## Node Types

| Node Type | Description | Canonical Tables |
| --- | --- | --- |
| plot_universe | Plot-specific domain of eligible result targets. | plot_universe.tsv, plot_criterion.tsv, plot_membership.tsv |
| search_space | Corpus, index, registry, repository class, local inventory, or literature domain searched for possible result targets. | provenance_search_plan.tsv, extraction_event.tsv |
| search_query | Exact query, API call, local inventory scan, or manual review operation used to search a universe. | provenance_search_plan.tsv, source_access_attempt.tsv, extraction_event.tsv |
| search_lead | Possible source, corpus, registry record, project, paper, or result table found before it becomes a result target. | search_lead.tsv, provenance_search_plan.tsv, manual_acquisition_task.tsv |
| result_target | A candidate or plotted D/N result before deduplication. | source_result.tsv |
| canonical_result | Deduplicated or collapsed plotted result. | canonical_result.tsv, canonical_result_membership.tsv |
| extraction_source | Source object that directly asserted or exposed a result row. | source.tsv, source_result.tsv |
| represented_source | Paper, registry record, study, dataset, or package the result is about. | source.tsv, source_identifier.tsv |
| source_identifier | DOI, PMID, PMCID, NCT, AEA, OpenAlex, Crossref, OSF, Dataverse, or stable URL identity. | source_identifier.tsv |
| source_mapping | Relationship between sources, such as corpus contains paper or registry preregisters trial. | source_source_mapping.tsv |
| access_route | A route to source bytes or metadata. | source_access.tsv |
| strategy_attempt | One attempt by one resolver, search, API, browser, or file route. | source_access_attempt.tsv, extraction_event.tsv |
| source_object_candidate | Candidate byte object or metadata record before acceptance. | source_object_candidate.tsv, source_access_attempt.tsv |
| source_file | Content-addressed mirrored artifact. | source_file.tsv |
| source_result_support | Field-level evidence snippet, locator, conversion input, raw data, code, or recomputed output. | source_result_support.tsv |
| manual_task | Human follow-up item for identity, acquisition, rights, or value verification. | manual_acquisition_task.tsv |
| review_queue | Bounded Codex, GPT, or human review cue for ambiguous leads after deterministic routing. | reviewcue-queue-*.json, reviewcue-*-prompt.md |
| promotion_event | Explicit state transition such as L2 to L4, L4 to L5, or L5 to L6. | extraction_event.tsv |

## Edge Types

| Edge | From | To | Meaning |
| --- | --- | --- | --- |
| defines_search_space | plot_universe | search_space | Plot universe declares a searchable domain or seed inventory. |
| issues_search_query | search_space | search_query | Search space is explored by one exact query, API call, local scan, or manual review operation. |
| returns_search_lead | search_query | search_lead | Search operation yields a possible corpus, source, project, paper, registry record, or result table. |
| triages_lead_to_target | search_lead | result_target | Lead passes a universe-specific gate and emits one or more result targets. |
| samples | plot_universe | result_target | Plot/sample universe includes this result target. |
| asserts_result | extraction_source | result_target | Extraction source directly asserts or exposes this result. |
| canonicalizes | canonical_result | result_target | Canonical result chooses, collapses, or groups source-result rows. |
| represents | result_target | represented_source | Result target is about this paper, registry record, trial, or dataset. |
| identifies | represented_source | source_identifier | Identifier grounds a represented source in the wider world. |
| maps_to | extraction_source | represented_source | Crosswalk or relationship mapping connects a corpus/source row to a represented source. |
| proposes_route | represented_source | access_route | Resolver or human process proposes a route to metadata or bytes. |
| attempts_route | access_route | strategy_attempt | One concrete request, query, browser action, local check, or file action was attempted. |
| produces_candidate | strategy_attempt | source_object_candidate | Attempt yielded a candidate object, metadata record, or blocker artifact. |
| accepts_candidate_as_file | source_object_candidate | source_file | Candidate passed identity and byte-class gates and was mirrored. |
| mirrors_source | source_file | represented_source | Mirrored bytes are a value-bearing source object for the represented source. |
| supports_field | source_file | source_result_support | Mirrored object contains a field-level support snippet or conversion input. |
| verifies_result | source_result_support | result_target | Support verifies D, N, native value, selector, relationship, or conversion input. |
| blocks_to_manual_task | strategy_attempt | manual_task | Failed or blocked attempt creates a human follow-up. |
| promotes_state | promotion_event | result_target | Explicit event changes evidence level or acquisition/verification state. |

## Strategy Registry

| Rank | Strategy | Stage | Status | Inputs | Outputs | Applies When |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | search_plot1_replication_pair_universe | universe_search | active_foundation | plot_universe | search_space, search_query, search_lead | Plot 1 needs new paired original/replication result candidates or legacy replication leads need triage. |
| 2 | search_plot2_published_paper_universe | universe_search | active_foundation | plot_universe | search_space, search_query, search_lead | Plot 2 needs corpus/database/article leads for published-paper D/N rows. |
| 3 | search_plot3_preregistered_universe | universe_search | active_foundation | plot_universe | search_space, search_query, search_lead | Plot 3 needs preregistered, PAP, registry, or registered-report result leads. |
| 4 | search_plot4_all_source_dump_universe | universe_search | active_foundation | plot_universe | search_space, search_query, search_lead | Plot 4 needs diagnostic, comparator, sidecar, and all-source D/N lead coverage. |
| 10 | define_schema_pilot_sample | universe_definition | active | plot_universe | result_target, canonical_result | Fixed benchmark sample or debug sample is requested. |
| 20 | retrace_current_plot_assertions | retrace_assertion | active | result_target | extraction_source, result_target | A plotted or sampled row needs local source assertion recovery. |
| 30 | resolve_represented_source_identity | identity_resolution | active | result_target, extraction_source | represented_source, source_identifier, source_mapping | Result row is below level 4 or has weak represented source identity. |
| 31 | metabus_shorthand_crosswalk | identity_resolution | planned | result_target | represented_source, source_identifier, source_mapping | next_bucket is needs_metabus_or_shorthand_crosswalk, or title/represented_source_id parses as journal-volume-issue-page. |
| 32 | schaefer_schwarz_osf_crosswalk | identity_resolution | planned | result_target | represented_source, source_identifier, source_mapping, source_file | represented_source_id or title contains schaefer_2019_np or schaefer_2019_preg handles. |
| 33 | linden_osf_crosswalk | identity_resolution | planned | result_target | represented_source, source_identifier, source_mapping, source_file | represented_source_id or title contains linden-style year/index handles. |
| 34 | better_identifier_repair | identity_resolution | planned | result_target | represented_source, source_identifier | next_bucket is needs_better_identifier. |
| 40 | strict_level5_probe | locating | active | represented_source, source_identifier | access_route, strategy_attempt, source_object_candidate | Row is level 4 and source object has not been mirrored. |
| 50 | full_article_text_acquisition | obtaining | active | source_object_candidate, represented_source | source_file, source_object_candidate, strategy_attempt | Paper-like represented source has OA, Crossref, OpenAlex, Europe PMC, OpenAIRE, CORE, OSF, Wayback, or repository candidate URLs. |
| 51 | original_pdf_acquisition_and_identity | obtaining | active | represented_source, source_identifier | source_object_candidate, source_file, strategy_attempt | Below-level-5 row has DOI or PDF candidate identifiers and full-article route failed. |
| 52 | zotero_storage_reingest | obtaining | active | represented_source, source_object_candidate | source_file, source_object_candidate, strategy_attempt | Zotero dedicated profile may contain late-downloaded PDF, HTML, XML, or EPUB attachments. |
| 60 | manual_capture | manual_followup | active_queue | manual_task, represented_source | source_object_candidate, source_file, strategy_attempt, manual_task | next_bucket is needs_manual_capture or public_and_core_routes_exhausted. |
| 80 | ctgov_level6_verification | verification | active | source_file, result_target | source_result_support, promotion_event | Represented source is ClinicalTrials.gov registry record and plotted value can be matched to registry fields. |
| 81 | article_level6_candidate_extraction | extraction | active_candidate_generation | source_file, result_target | source_result_support, manual_task | Level-5 article PDF, XML, HTML, or PMC XML has not been checked for exact D/N text or conversion inputs. |
| 90 | recompute_from_raw_data_or_code | verification | future | source_file, result_target | source_result_support, promotion_event | Raw data and code are mirrored and enough environment information exists to rerun or independently recompute. |

## Strategy Counts

### By Status

| Status | Strategies |
| --- | --- |
| active | 8 |
| active_candidate_generation | 1 |
| active_foundation | 4 |
| active_queue | 1 |
| future | 1 |
| planned | 4 |

### By Stage

| Stage | Strategies |
| --- | --- |
| extraction | 1 |
| identity_resolution | 5 |
| locating | 1 |
| manual_followup | 1 |
| obtaining | 3 |
| retrace_assertion | 1 |
| universe_definition | 1 |
| universe_search | 4 |
| verification | 2 |

## Queues

| Queue | Table | Node Type | Description |
| --- | --- | --- | --- |
| provenance_search_plan | data/derived/effect_inflation_dataset/provenance_search_plan.tsv | search_lead | Generated, human-editable top-of-pipeline search tracks for each plot universe. |
| figure1_search_leads_review_cue | steps/review_cue/figure1_search_leads/reviewcue-queue-figure1_search_leads.json | review_queue | Reusable Codex/GPT review cue for unresolved Figure 1 search leads after deterministic routing and skip logic. |
| tail_resolution_queue_sample_300 | data/derived/effect_inflation_dataset/schema_pilot/tail_resolution_queue_sample_300.tsv | manual_task | Active below-level-5 rows, bucketed into identity-blocked and acquisition-blocked work. |
| manual_capture_queue_sample_300 | data/derived/effect_inflation_dataset/schema_pilot/manual_capture_queue_sample_300.tsv | manual_task | Active grounded rows that need lawful browser, Zotero, library, or institutional capture. |
| manual_or_library_followup_queue_sample_300 | data/derived/effect_inflation_dataset/schema_pilot/manual_or_library_followup_queue_sample_300.tsv | manual_task | Manual-capture rows plus public/CORE-exhausted rows needing library, author, or publisher routes. |
| level6_source_object_extraction_worklist_sample_300 | data/derived/effect_inflation_dataset/schema_pilot/level6_source_object_extraction_worklist_sample_300.tsv | manual_task | Level-5 source objects queued for source text, table, and value verification. |

## Promotion Gates

### `l2_to_l4`

- After: `target_source_independently_grounded`
- Required evidence: represented_source_id, independent_identifier_or_stable_url, identity_basis, identity_confidence, source_mapping_or_identifier_row
- Reject if: only_internal_label, ambiguous_candidate_without_resolution, generated_dot_citation_only

### `l4_to_l5`

- After: `original_source_obtained`
- Required evidence: source_file.local_path, source_file.sha256, source_file.source_byte_class, source_access.access_id, source_access_attempt.attempt_id, identity_decision_accepted, rights_or_storage_notes
- Reject if: metadata_only, abstract_only_without_plotted_value, paywall_or_login_page, captcha_page, access_denied_page, wrong_doi_or_title

### `l5_to_l6`

- After: `original_number_extracted`
- Required evidence: source_file_id, precise_source_locator, verbatim_effect_text_or_conversion_inputs, verbatim_n_text_or_exact_n_field, context_match_status, parser_or_human_review_method
- Reject if: effect_without_n, n_without_effect, context_mismatch, statistic_type_unclear, same_number_ambiguous_across_outcomes, source_is_derived_corpus_not_represented_source

### `l6_to_l7`

- After: `recomputed_from_raw`
- Required evidence: raw_or_analytic_data_file, code_or_formula, execution_environment_or_formula_version, recomputed_output, tolerance_rule
- Reject if: missing_data_or_code, nonreproducible_environment, result_mismatch_without_explanation

## Current 300-Row Benchmark

| Minimum Evidence Standard | Rows | Percent |
| --- | --- | --- |
| 2: external_source_assertion | 300 | 100.0% |
| 3: external_assertion_with_target_source | 281 | 93.7% |
| 4: target_source_independently_grounded | 281 | 93.7% |
| 5: original_source_obtained | 183 | 61.0% |
| 6: original_number_extracted | 88 | 29.3% |
| 7: recomputed_from_raw | 0 | 0.0% |

| Current Level | Rows | Percent |
| --- | --- | --- |
| 2: external_source_assertion | 19 | 6.3% |
| 4: target_source_independently_grounded | 98 | 32.7% |
| 5: original_source_obtained | 95 | 31.7% |
| 6: original_number_extracted | 88 | 29.3% |

## Active Tail Queue

| Rank | Bucket | Problem Family | Rows |
| --- | --- | --- | --- |
| 1 | needs_metabus_or_shorthand_crosswalk | identity_blocked | 17 |
| 2 | needs_identity_crosswalk | identity_blocked | 8 |
| 3 | needs_better_identifier | identity_blocked | 3 |
| 4 | needs_manual_capture | acquisition_blocked | 13 |
| 5 | public_and_core_routes_exhausted | acquisition_blocked | 4 |
