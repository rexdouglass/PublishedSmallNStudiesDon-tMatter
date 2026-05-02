# Evidence Dataset Codebook

This repository treats plotted and staged results as a proper auditable dataset. The governing principle is: a row is not trustworthy because it appears in a plot; it is trustworthy when a human can retrace it from raw source bytes, through verbatim copied text, through native parsing, through transformation, into a canonical plotted or staged result.

## Required Tables

| Table | Grain | Primary key | Promotion requirement |
| --- | --- | --- | --- |
| source.tsv | One citeable or computational source object. | source_id | Required for every promoted source-result row. |
| source_access.tsv | One route to the bytes for one source. | access_id | Required unless the source is intentionally bibliographic-only and not used for extraction. |
| source_access_attempt.tsv | One resolver/download/API attempt for one source. | attempt_id | Recommended for all newly resolved sources; required when a source required multiple routes, paywall/CAPTCHA handling, or OA/preprint discovery. |
| source_file.tsv | One mirrored byte artifact or extracted file/member for one source. | source_file_id | Required when bytes are mirrored or used as source evidence. |
| source_version.tsv | One version assertion for one source. | source_version_id | Recommended whenever a source may have VOR, preprint, registry, repository, dataset, or code versions. |
| source_access_right.tsv | One access-rights or mirroring decision for one source/file. | access_right_id | Required for mirrored source files and publisher/repository/manual access routes. |
| source_identifier.tsv | One external identifier, resolver key, or stable URL for one source. | source_id + identifier_type + identifier_value | Recommended for every source with more than one identifier or URL; required when identifiers were resolved separately from source.tsv. |
| source_classification.tsv | One classification assertion for one source. | source_id + classification_source | Recommended for plot filtering, source-family displays, field counts, and paper/data-paper tables. |
| search_lead.tsv | One discovered lead under one search track or plot universe. | search_lead_id | Recommended before a new corpus, database, project, registry record, paper, or replication-paper lead is promoted to source/source_result rows. |
| source_result.tsv | One result asserted or exposed by one extraction source. | source_result_id | Required for every plotted or staged result. |
| canonical_result.tsv | One deduplicated result selected or summarized from one or more source-result rows. | canonical_result_id | Required for plotting and paper-level summaries. |
| canonical_result_membership.tsv | One source-result row's membership in one canonical plotted/staged result. | canonical_result_id + source_result_id | Required whenever canonical_result.source_result_count is greater than one; recommended for all canonical results. |
| source_result_support.tsv | One source/access object supporting one source-result field or decision. | source_result_id + source_id + access_id + support_role | Recommended for all rows; required when multiple objects support one result, such as paper plus supplement plus registry plus code output. |
| plot_universe.tsv | One reusable plot, panel, statistic set, diagnostic view, or future plot context. | plot_universe_id | Recommended when a plot build snapshots YAML-defined criteria into table artifacts. |
| plot_criterion.tsv | One reusable inclusion, exclusion, or context criterion. | criterion_id | Recommended when a plot build snapshots YAML-defined criteria into table artifacts. |
| plot_membership.tsv | One canonical result's inclusion/exclusion status in one plot or statistic set. | plot_id + canonical_result_id | Required for public plots once a canonical result can appear in more than one plot, diagnostic view, or sensitivity view. |
| source_source_mapping.tsv | One directed relationship between two sources. | mapping_id | Required whenever extraction source and represented source differ, or for corpus-parent mappings. |
| extraction_event.tsv | One action or failed action used to obtain, parse, or verify source bytes. | event_id | Required for new extraction work; pilot retrace rows may have partial historical events. |
| extraction_problem.tsv | One quality or provenance problem for one source-result or source object. | problem_id | Required when any promotion gate is not met or requires manual follow-up. |
| manual_acquisition_task.tsv | One human/manual acquisition or verification task. | manual_task_id | Required when automated acquisition fails or manual/library access is needed. |

## Dictionary Snapshot

| Table | Columns | Grain |
| --- | --- | --- |
| source.tsv | 13 | One citeable or computational source object. |
| source_access.tsv | 33 | One route to the bytes for one source. |
| source_access_attempt.tsv | 51 | One resolver/download/API attempt for one source. |
| source_file.tsv | 31 | One mirrored byte artifact or extracted file/member for one source. |
| source_version.tsv | 18 | One version assertion for one source. |
| source_access_right.tsv | 20 | One access-rights or mirroring decision for one source/file. |
| source_identifier.tsv | 8 | One external identifier, resolver key, or stable URL for one source. |
| source_classification.tsv | 6 | One classification assertion for one source. |
| search_lead.tsv | 27 | One discovered lead under one search track or plot universe. |
| source_result.tsv | 74 | One result asserted or exposed by one extraction source. |
| canonical_result.tsv | 19 | One deduplicated result selected or summarized from one or more source-result rows. |
| canonical_result_membership.tsv | 8 | One source-result row's membership in one canonical plotted/staged result. |
| source_result_support.tsv | 22 | One source/access object supporting one source-result field or decision. |
| plot_universe.tsv | 10 | One reusable plot, panel, statistic set, diagnostic view, or future plot context. |
| plot_criterion.tsv | 10 | One reusable inclusion, exclusion, or context criterion. |
| plot_membership.tsv | 20 | One canonical result's inclusion/exclusion status in one plot or statistic set. |
| source_source_mapping.tsv | 32 | One directed relationship between two sources. |
| extraction_event.tsv | 14 | One action or failed action used to obtain, parse, or verify source bytes. |
| extraction_problem.tsv | 11 | One quality or provenance problem for one source-result or source object. |
| manual_acquisition_task.tsv | 24 | One human/manual acquisition or verification task. |

## Column Families

The TSVs are organized by purpose. This table is the fastest way to decide where a fact belongs.

| Family | Table(s) | Main columns | Purpose |
| --- | --- | --- | --- |
| Search leads | `search_lead.tsv` | `plot_universe_id`, `search_track_id`, `lead_type`, `lead_title`, `candidate_artifact_path_or_url`, `triage_status`, `lead_decision` | Top-of-pipeline candidates found before they become sources or source-result rows. |
| Source identity | `source.tsv` | `source_id`, `source_type`, `title`, `citation_key`, `doi`, `pmid`, `registry_id`, `url` | Identifies the real-world or computational object. |
| Access and mirroring | `source_access.tsv` | `remote_url`, `api_url`, `local_path`, `file_sha256`, `access_strategy`, `source_byte_class`, `level5_eligible` | Documents exactly how we got or failed to get source bytes. |
| Access attempts | `source_access_attempt.tsv` | `resolver_strategy`, `candidate_url`, `final_url`, `decision`, `decision_reason`, blocker and abstract/preprint fields | Append-only record of DOI/publisher/OA/preprint/API routes tried before choosing an access object. |
| File artifacts | `source_file.tsv` | `source_file_id`, `local_path`, `sha256`, `file_role`, `file_origin`, `source_byte_class`, `level5_eligible` | Content-addressed inventory of actual mirrored or local byte objects. |
| Version and rights | `source_version.tsv` and `source_access_right.tsv` | `version_label`, `is_version_of_record`, `license_url`, `mirror_allowed_yn`, `rights_decision` | Keeps VOR/preprint/registry/dataset versions and lawful mirroring decisions separate from attempts. |
| Verbatim extraction | `source_result.tsv` | `verbatim_source_row_text`, `verbatim_outcome_text`, `verbatim_effect_text`, `verbatim_n_text`, `verbatim_p_text`, `verbatim_ci_text` | Human-checkable copied text before parsing. |
| Native parsing | `source_result.tsv` | `native_effect_value`, `native_effect_metric`, `native_standard_error`, `native_n_total`, arm Ns, cluster N | Parsed values in source-native units. |
| Standardization | `source_result.tsv` | `standardized_effect_value`, `standardized_n`, `d`, `d_conversion_method`, `d_conversion_inputs`, `transformation_explanation` | How source-native values became D/N or native-panel values. |
| Focal selector | `source_result.tsv` and `source_source_mapping.tsv` | `selector_status`, `selector_rule`, `selector_mapping_id`, prereg selector fields | Why this result is the plotted/canonical result. |
| Preregistration | `source_result.tsv` and `source_source_mapping.tsv` | `prereg_status`, `prereg_mapping_id`, registry/PAP fields, selector text | Specific evidence for prereg/PAP/registered-report claims. |
| Replication | `source_result.tsv` and `source_source_mapping.tsv` | `replication_mapping_id`, `replication_role`, `replication_pair_id`, `replication_kind`, target-claim fields | Specific evidence for original/replication/reproduction relationships. |
| Canonical plotting | `canonical_result.tsv` | `source_result_count`, `aggregation_rule`, `D_min`, `D_median`, `D_max`, `N_min`, `N_median`, `N_max` | One plotted/collapsed row selected from source-result rows. |
| Plot contexts | `plot_universe.tsv`, `plot_criterion.tsv`, and `plot_membership.tsv` | `plot_universe_id`, `criterion_id`, `eligibility_status`, `passed_criteria_ids`, `failed_criteria_ids` | Context-specific inclusion/exclusion decisions for current figures, diagnostics, sensitivities, and future plots. |
| Problems/events | `extraction_event.tsv` and `extraction_problem.tsv` | `event_step`, `command_or_tool`, `problem_code`, `severity`, `suggested_rework` | Audit trail and rework queue. |

## Promotion Gates

Rows can be plotted on the main D-axis only after all applicable gates pass. Rows may be staged in the native panel or blocked with explicit problems before then.

| Gate | Criterion |
| --- | --- |
| G1 source identity | source_id, source_type, title, and stable citation or URL are present. |
| G2 byte access | source_access row gives direct URL/API or local path; mirrored files have size and checksum, or an access barrier is explicit. |
| G3 locator | source_result.source_locator is precise enough to find the source row/table/page/API field again. |
| G4 verbatim evidence | verbatim source row plus effect/statistic and N text are copied before parsing, unless row is explicitly blocked/staged. |
| G5 native parse | native values are parsed without changing metric, with arm/cluster Ns split when available. |
| G6 transformation | D/N or native-panel values have a named method, inputs, and transformation explanation. |
| G7 focal selector | paper/project rows document why this result is focal or how multiple eligible results were collapsed. |
| G8 bibliographic mapping | extraction source and represented source citations are separated; generated dot citations are internal only. |
| G9 deduplication | canonical_result records source_result_count and aggregation/resolution rule. |
| G10 human check | A human can open local_path, use source_locator, see verbatim text, and recalculate final D/N or native value. |

## Coding Rules

1. Mirror the source locally whenever access allows it; store exact local paths and checksums.
2. Separate bibliographic identity from computational access. A paper, registry record, corpus, database, zip file, extracted CSV, and script output can all be different sources.
3. Separate labels from evidence. `result_label` and `outcome_label` are display labels; they are not verbatim source text.
4. Copy original source text before parsing. Use one-line TSV-safe verbatim fields for source row text, outcome text, effect/statistic text, N text, p/CI text, and any notes needed to check the row.
5. Parse native values without changing their metric. Store regression coefficients, risk differences, event counts, standard errors, Ns, and cluster counts in native fields before any D conversion.
6. Do not force Cohen's d. Use D only for reported d/g/SMD or defensible conversions with documented inputs. Clustered field experiments, arbitrary LPMs, policy ATEs, and outcomes without SD/baseline/event counts should go to the native panel.
7. Preserve multiple source assertions. If the same result appears in a paper, corpus, and database, keep separate `source_result` rows and resolve them later in `canonical_result`.
8. Track parent-child relationships. Corpora and collections can contain thousands of child papers/results; record those mappings rather than pretending the corpus itself is one paper.
9. Record extraction events and failures. Manual uploads, login walls, PDF extraction, script execution, and failed downloads are dataset facts.
10. If a field is missing, leave it blank and add an `extraction_problem` row. Do not hide missing evidence in prose notes.

## Mapping Detail Rules

Use `source_source_mapping.tsv` for relationship evidence, not just yes/no flags. A preregistered result should point to a mapping row with the registry/PAP source, URL, registration date, timing, locator, and verbatim selector text. A replication result should point to a mapping row with the original source, replicating source, replication kind, target claim, outcome/design/sample relation, and assertion evidence. Corpus/database rows should map the corpus source to the represented paper/result with the corpus row ID or locator and any external child identifiers.

Use `source_result.tsv` columns such as `prereg_mapping_id`, `prereg_selector_verbatim_text`, `replication_mapping_id`, `replication_pair_id`, and `source_mapping_ids` to connect result rows back to those detailed mappings. These columns should contain IDs and copied source text, not vague notes like "yes" or "replication".

## Minimum Row Sets

Different evidence types require different rows. These are minimums, not maximums.

| Case | Minimum tables | Requirements |
| --- | --- | --- |
| New corpus/database or individual replication-paper lead | `search_lead.tsv` | Record search context, lead type, URL/path/artifact, expected fields, triage status, decision, blockers, and next action before promotion. |
| Direct paper/registry result | `source`, `source_access`, `source_result`, `canonical_result` | Needs value-bearing source bytes, locator, verbatim effect/N text, native parse, transformation, and citation. |
| Corpus/database result about another paper | `source`, `source_access`, `source_result`, `source_source_mapping`, `canonical_result` | Keep extraction source and represented source separate; map the corpus row to the child paper/result; do not treat corpus numbers as original-source verification. |
| Preregistered result | `source_result` plus prereg mapping row | Needs prereg status, direct artifact URL when available, timing, selector locator/text, and mapping evidence. Corpus-only prereg claims must be coded as `prereg_asserted_by_corpus_no_artifact`. |
| Replication/reproduction result | `source_result` plus replication mapping row | Needs role, pair ID, kind, target claim, original/replicating result IDs when available, and assertion evidence. |
| Collapsed paper/project row | `canonical_result` plus child `source_result` rows | Needs source_result_count, aggregation rule, min/median/max fields when relevant, and child rows preserved. |
| Blocked/staged row | `source`, `source_access`, `source_result`, `extraction_problem` | Leave missing fields blank, state blocker, and record exact rework action/URL/path. |
| Manual acquisition task | `manual_acquisition_task.tsv` | Create when automated attempts leave missing source objects, value text, prereg artifacts, replication evidence, or rights review. |

## Evidence Levels

Every `source_result` gets a numeric `evidence_level` and a controlled `evidence_level_name`.

| Level | Name | Meaning |
| --- | --- | --- |
| 0 | unanchored_number | A D/N or native number exists, but no real-world source assertion or represented source can be identified. |
| 1 | internal_trace_only | The row retraces only to this repository's internal derived/intermediate files. |
| 2 | external_source_assertion | A real external corpus/database/registry asserts the number, but the represented paper/study is not durably identified. |
| 3 | external_assertion_with_target_source | An external source asserts the number and gives enough bibliographic/registry information that the represented target source could theoretically be found. |
| 4 | target_source_independently_grounded | We resolved the represented target source in the wider world via DOI, PMID, PMCID, NCT, AEA, Dataverse, Crossref, or another independent URL/citation database. |
| 5 | original_source_obtained | We obtained or mirrored value-bearing source bytes that could plausibly contain the plotted value, such as full article PDF/XML/HTML, registry record, supplement, data/code package, or author manuscript, with path/checksum when possible. Metadata records, abstract pages, paywalls, CAPTCHA pages, and access-denied pages are not level 5 unless the plotted value is present there. |
| 6 | original_number_extracted | We extracted/copied the exact effect/N/supporting text ourselves from the original source bytes or authoritative registry/API/table. |
| 7 | recomputed_from_raw | We recomputed the number from raw data/code and preserved the output. |

## Controlled Vocabularies

| Field | Allowed values |
| --- | --- |
| source_type | paper \| registry_record \| corpus \| database \| repository_or_package \| pdf \| report \| website \| raw_data_file \| code_file \| local_derived_table \| other |
| source_status | primary \| sidecar \| support_only \| blocked \| deprecated |
| search_lead_type | corpus_or_database \| registry_record \| paper_or_article \| individual_replication_paper \| replication_project \| preregistration_or_pap \| repository_package \| candidate_result_table \| raw_data_or_code_package \| manual_source_suggestion |
| search_lead_status | not_started \| seeded_from_existing_artifact \| candidate_found \| candidate_rejected \| staged_for_parser \| promoted_to_result_target \| blocked_access \| blocked_no_result_fields \| blocked_scope_mismatch \| deprecated_duplicate |
| lead_decision | not_triaged \| promote_to_source \| promote_to_source_result \| stage_for_parser \| catalog_only \| reject_scope_mismatch \| reject_duplicate \| blocked_access \| blocked_missing_fields \| manual_review_required |
| plot_scope_role | current_figure \| current_diagnostic \| catalog_only_future_plot_seed \| future_plot_candidate \| sensitivity_view \| deprecated |
| eligibility_status | included \| excluded \| catalog_only \| diagnostic_only \| sensitivity_only \| pending \| blocked |
| decision_context_type | current_plot \| diagnostic_view \| sensitivity_view \| future_plot_draft \| manual_review \| automated_rule |
| identifier_type | doi \| pmid \| pmcid \| nct \| aea_trial \| egap_registration \| ridie \| osf \| dataverse_doi \| zenodo_doi \| openicpsr \| openalex \| semantic_scholar \| arxiv \| ssrn \| url \| other |
| access_role | landing_page \| direct_download \| api \| mirrored_file \| file_member \| source_file_or_catalog \| user_upload \| derived_table |
| retrieval_method | automated_download \| api_download \| osf_clone \| dataverse_api \| github_clone \| user_upload \| browser_manual_download \| existing_local_file \| code_execution_output \| not_retrieved |
| access_status | local_file_found \| downloaded \| remote_url_not_cached \| local_path_missing \| login_required \| access_denied \| missing_locator \| unresolved_locator \| blocked \| not_applicable |
| attempt_decision | source_object_mirrored \| metadata_only \| abstract_or_landing_only \| paywall_or_login \| captcha_or_bot_block \| access_denied \| blocked \| not_retrieved \| manual_review \| candidate_rejected |
| access_strategy | registry_clinicaltrials \| pubmed_bridge \| pmc_fulltext \| crossref_metadata \| datacite_metadata \| unpaywall_metadata \| openalex_metadata \| semantic_scholar_metadata \| europepmc_metadata \| oa_candidate_url \| preprint_repository_candidate \| direct_journal_or_doi_landing \| stable_url \| other |
| source_byte_class | full_article_pdf \| full_article_xml \| full_article_html \| author_manuscript_fulltext \| supplement_file \| dataset_file \| code_file \| registry_record_full \| pmc_fulltext_xml \| pubmed_record_or_abstract \| metadata_record \| publisher_landing_or_abstract \| paywall_or_login_page \| captcha_page \| access_denied_page \| blocked_no_source_object \| source_object_unclassified \| not_retrieved |
| license_category | open \| restricted \| subscription \| unknown \| not_applicable |
| source_version | version_of_record \| accepted_manuscript \| author_manuscript \| preprint \| supplement \| registry_record \| dataset \| code \| metadata \| unknown |
| file_role | full_article \| author_manuscript \| preprint \| registry_record \| supplement \| dataset \| code \| metadata \| screenshot \| abstract_page \| landing_page \| derived_table \| archive \| archive_member \| other |
| file_origin | automated_download \| api_response \| repository_file \| publisher_file \| existing_local_file \| user_upload \| manual_browser \| code_execution_output \| internal_derived \| archive_member \| unknown |
| rights_decision | open_allowed \| internal_only \| restricted \| subscription_required \| not_applicable \| unknown \| needs_review |
| target_acquisition_state | unanchored \| external_assertion_only \| target_identity_known \| target_located \| source_object_mirrorable \| source_object_mirrored \| text_or_data_extracted |
| value_verification_state | not_checked \| corpus_assertion_only \| source_object_obtained_not_parsed \| text_or_data_extracted \| value_bearing_source_text_found \| d_n_verified_from_source |
| manual_task_status | open \| in_progress \| blocked \| closed \| not_needed |
| needed_artifact_type | original_source_object \| full_article \| registry_record \| supplement \| dataset_or_code \| prereg_artifact \| replication_evidence \| effect_text \| n_text \| license_review \| identity_disambiguation \| other |
| relationship_type | extraction_source_reports_result_for_represented_source \| corpus_contains_paper \| database_reports_paper_result \| repository_supports_paper \| registry_preregisters_study \| registry_links_publication \| pre_analysis_plan_supports_study \| registered_report_protocol_for_paper \| publication_reports_registered_study \| replication_of \| computational_reproduction_of \| robustness_reanalysis_of \| meta_analysis_includes_study \| corpus_asserts_result_for_paper \| corpus_asserts_preregistration_for_paper \| paper_uses_dataset \| source_derives_from_source \| duplicate_of \| parent_collection_contains_child |
| relationship_subtype | preregistration \| pre_analysis_plan \| meta_analysis_pre_analysis_plan \| registered_report_stage1_protocol \| registered_report_stage2_results \| trial_registry_record \| data_or_code_package \| paper_supplement \| direct_replication \| conceptual_replication \| computational_reproduction \| robustness_reanalysis \| extension_study \| pilot_full_scale_pair \| pooled_round_component \| corpus_child_paper \| database_child_result \| citation_or_link_only \| unknown |
| relationship_timing | pre_data_collection \| pre_analysis \| post_data_pre_results \| post_results \| not_applicable \| unknown |
| mapping_evidence_type | verbatim_text \| metadata_field \| doi_link \| registry_link \| citation_match \| title_author_year_match \| code_or_package_manifest \| manual_judgment \| unknown |
| replication_role | none \| original_study \| replication_study \| computational_reproduction \| robustness_check \| corpus_replication_assertion \| unknown |
| support_role | effect_text \| n_text \| outcome_text \| selector_text \| conversion_input \| raw_data \| analytic_data \| code \| recomputed_output \| bibliographic_identity \| access_grounding \| relationship_evidence \| other |
| membership_role | preferred \| child \| excluded_child \| duplicate \| sensitivity_only |
| classification_type | field \| subfield \| source_family \| study_design \| publication_type \| journal_or_venue \| other |
| native_effect_metric | mean_difference \| standardized_mean_difference \| odds_ratio \| log_odds_ratio \| risk_difference \| correlation \| regression_coefficient \| t_statistic \| z_statistic \| f_statistic \| p_value_only \| hazard_ratio \| rate_ratio \| count_difference \| native_ate \| elasticity \| unknown |
| standardized_effect_metric | d \| hedges_g \| smd \| chinn_log_or_to_d \| r_to_d \| fisher_z_to_d \| t_to_d \| z_to_d \| d_proxy \| native_only \| not_promoted |
| d_conversion_method | reported_d \| reported_g \| reported_smd \| chinn_log_or_to_d \| event_counts_to_log_or_to_d \| r_to_d \| fisher_z_to_r_to_d \| standardized_outcome_coefficient \| source_provided_d_proxy \| paper_median_of_child_d \| no_d_native_metric \| blocked_missing_inputs |
| prereg_status | prereg_confirmed_pre_data \| prereg_confirmed_pre_analysis \| registered_report \| proposal_pre_fielding_not_full_prereg \| registry_metadata_only \| registry_record_timing_not_audited \| prereg_asserted_by_corpus_no_artifact \| not_preregistered \| unknown |
| selector_status | pap_primary \| pap_secondary \| registry_primary \| article_primary \| first_confirmatory_hypothesis \| median_across_preregistered_primaries \| corpus_focal_claim \| database_primary_outcome \| not_focal \| no_focal_selector |
| confidence | high \| medium \| low \| blocked |
| human_check_status | source_cells_recovered \| n_only_recovered \| plot_summary_only \| needs_pdf_check \| needs_code_execution \| verified_by_human |
| coding_status | fully_coded \| coded_with_schema_gaps \| staged_native_metric \| blocked_missing_d_or_n \| blocked_access \| excluded \| duplicate_existing |
| evidence_level_name | unanchored_number \| internal_trace_only \| external_source_assertion \| external_assertion_with_target_source \| target_source_independently_grounded \| original_source_obtained \| original_number_extracted \| recomputed_from_raw |
| citation_status | real_citation \| generated_internal \| missing |
| problem_code | missing_verbatim_effect_text \| missing_verbatim_n_text \| missing_source_locator \| source_is_derived_not_original_text \| access_blocked \| needs_pdf_check \| needs_code_execution \| conversion_not_defensible \| duplicate_needs_resolution \| missing_bibliographic_key |
| severity | high \| medium \| low |
| resolution_status | single_source_result \| preferred_source_selected \| multiple_source_results_need_resolution \| duplicate_existing \| blocked |

## Critical Vocabulary Definitions

The full machine-readable vocabulary dictionary is `data/derived/effect_inflation_dataset/provenance_vocab_dictionary.tsv`. The critical values below are included here because they affect promotion, plotting, preregistration, replication, and level-5 evidence decisions.

| Field | Value | Definition | Coding notes |
| --- | --- | --- | --- |
| search_lead_type | corpus_or_database | Controlled value `corpus_or_database` for `search_lead_type`. | Use only when this exact status/category applies; otherwise leave blank or use unknown/blocked as appropriate. |
| search_lead_type | registry_record | Controlled value `registry_record` for `search_lead_type`. | Use only when this exact status/category applies; otherwise leave blank or use unknown/blocked as appropriate. |
| search_lead_type | paper_or_article | Controlled value `paper_or_article` for `search_lead_type`. | Use only when this exact status/category applies; otherwise leave blank or use unknown/blocked as appropriate. |
| search_lead_type | individual_replication_paper | Controlled value `individual_replication_paper` for `search_lead_type`. | Use only when this exact status/category applies; otherwise leave blank or use unknown/blocked as appropriate. |
| search_lead_type | replication_project | Controlled value `replication_project` for `search_lead_type`. | Use only when this exact status/category applies; otherwise leave blank or use unknown/blocked as appropriate. |
| search_lead_type | preregistration_or_pap | Controlled value `preregistration_or_pap` for `search_lead_type`. | Use only when this exact status/category applies; otherwise leave blank or use unknown/blocked as appropriate. |
| search_lead_type | repository_package | Controlled value `repository_package` for `search_lead_type`. | Use only when this exact status/category applies; otherwise leave blank or use unknown/blocked as appropriate. |
| search_lead_type | candidate_result_table | Controlled value `candidate_result_table` for `search_lead_type`. | Use only when this exact status/category applies; otherwise leave blank or use unknown/blocked as appropriate. |
| search_lead_type | raw_data_or_code_package | Controlled value `raw_data_or_code_package` for `search_lead_type`. | Use only when this exact status/category applies; otherwise leave blank or use unknown/blocked as appropriate. |
| search_lead_type | manual_source_suggestion | Controlled value `manual_source_suggestion` for `search_lead_type`. | Use only when this exact status/category applies; otherwise leave blank or use unknown/blocked as appropriate. |
| lead_decision | not_triaged | Controlled value `not_triaged` for `lead_decision`. | Use only when this exact status/category applies; otherwise leave blank or use unknown/blocked as appropriate. |
| lead_decision | promote_to_source | Controlled value `promote_to_source` for `lead_decision`. | Use only when this exact status/category applies; otherwise leave blank or use unknown/blocked as appropriate. |
| lead_decision | promote_to_source_result | Controlled value `promote_to_source_result` for `lead_decision`. | Use only when this exact status/category applies; otherwise leave blank or use unknown/blocked as appropriate. |
| lead_decision | stage_for_parser | Controlled value `stage_for_parser` for `lead_decision`. | Use only when this exact status/category applies; otherwise leave blank or use unknown/blocked as appropriate. |
| lead_decision | catalog_only | Controlled value `catalog_only` for `lead_decision`. | Use only when this exact status/category applies; otherwise leave blank or use unknown/blocked as appropriate. |
| lead_decision | reject_scope_mismatch | Controlled value `reject_scope_mismatch` for `lead_decision`. | Use only when this exact status/category applies; otherwise leave blank or use unknown/blocked as appropriate. |
| lead_decision | reject_duplicate | Controlled value `reject_duplicate` for `lead_decision`. | Use only when this exact status/category applies; otherwise leave blank or use unknown/blocked as appropriate. |
| lead_decision | blocked_access | Controlled value `blocked_access` for `lead_decision`. | Use only when this exact status/category applies; otherwise leave blank or use unknown/blocked as appropriate. |
| lead_decision | blocked_missing_fields | Controlled value `blocked_missing_fields` for `lead_decision`. | Use only when this exact status/category applies; otherwise leave blank or use unknown/blocked as appropriate. |
| lead_decision | manual_review_required | Controlled value `manual_review_required` for `lead_decision`. | Use only when this exact status/category applies; otherwise leave blank or use unknown/blocked as appropriate. |
| eligibility_status | included | Controlled value `included` for `eligibility_status`. | Use only when this exact status/category applies; otherwise leave blank or use unknown/blocked as appropriate. |
| eligibility_status | excluded | Controlled value `excluded` for `eligibility_status`. | Use only when this exact status/category applies; otherwise leave blank or use unknown/blocked as appropriate. |
| eligibility_status | catalog_only | Controlled value `catalog_only` for `eligibility_status`. | Use only when this exact status/category applies; otherwise leave blank or use unknown/blocked as appropriate. |
| eligibility_status | diagnostic_only | Controlled value `diagnostic_only` for `eligibility_status`. | Use only when this exact status/category applies; otherwise leave blank or use unknown/blocked as appropriate. |
| eligibility_status | sensitivity_only | Controlled value `sensitivity_only` for `eligibility_status`. | Use only when this exact status/category applies; otherwise leave blank or use unknown/blocked as appropriate. |
| eligibility_status | pending | Controlled value `pending` for `eligibility_status`. | Use only when this exact status/category applies; otherwise leave blank or use unknown/blocked as appropriate. |
| eligibility_status | blocked | Controlled value `blocked` for `eligibility_status`. | Use only when this exact status/category applies; otherwise leave blank or use unknown/blocked as appropriate. |
| attempt_decision | source_object_mirrored | A value-bearing source object was mirrored or already exists locally. | Can support level 5 after identity and policy checks. |
| attempt_decision | metadata_only | Only metadata was obtained. | Supports grounding/resolution, not original-number verification unless metadata contains the value. |
| attempt_decision | abstract_or_landing_only | Only an abstract or publisher/detail landing page was obtained. | Use as proof of location; promote only if the value appears there. |
| attempt_decision | paywall_or_login | The route reached a paywall, subscription, or login artifact. | Keep as blocker evidence and do not promote as value-bearing bytes. |
| attempt_decision | captcha_or_bot_block | The route reached a CAPTCHA or bot-check artifact. | Stop automated retries for this route/host. |
| attempt_decision | access_denied | The route returned access denied, 403, or equivalent. | Record as blocked unless another lawful route succeeds. |
| attempt_decision | blocked | The attempt was blocked by policy, robots, missing permissions, missing key, or similar. | Needs manual review or different route. |
| attempt_decision | not_retrieved | No network/file retrieval was attempted or completed. | Use for locator-only rows. |
| attempt_decision | manual_review | Attempt outcome needs human judgment. | Use for ambiguous candidates or multiple possible targets. |
| attempt_decision | candidate_rejected | Candidate route was checked and rejected. | Explain mismatch or rejection in decision_reason. |
| source_byte_class | full_article_pdf | Full article PDF bytes for the target work. | Level 5 eligible if identity matches and access/mirroring is lawful. |
| source_byte_class | full_article_xml | Full article XML/JATS/NLM-style bytes for the target work. | Level 5 eligible if identity matches and the value could plausibly appear there. |
| source_byte_class | full_article_html | Full article HTML bytes, not just a landing page or abstract. | Level 5 eligible only when actual full text is present. |
| source_byte_class | author_manuscript_fulltext | Author accepted manuscript, preprint, or repository manuscript full text. | Level 5 eligible but flag source_version as manuscript/preprint when available. |
| source_byte_class | supplement_file | Supplementary material used to support extraction. | Level 5 eligible if it could contain the value, table, appendix, or methods. |
| source_byte_class | dataset_file | Data or analytic table file. | Level 5 eligible if it can support the value or recomputation. |
| source_byte_class | code_file | Script, notebook, log, or code output. | Level 5 eligible if it generates or contains the value. |
| source_byte_class | registry_record_full | Full registry/API record. | Level 5 eligible when the registry record is the source for the value or selector. |
| source_byte_class | pmc_fulltext_xml | PMC full-text XML/BioC/OAI record. | Level 5 eligible under PMC OA/usage constraints. |
| source_byte_class | pubmed_record_or_abstract | PubMed citation/abstract metadata. | Usually level 4/metadata only; level 5 only if the plotted value is actually in the abstract/record. |
| source_byte_class | metadata_record | Metadata-only API response. | Use for grounding and resolver provenance; not level 5 for D/N values. |
| source_byte_class | publisher_landing_or_abstract | Publisher landing page, title page, or abstract page. | Not level 5 unless the exact plotted value appears on that page. |
| source_byte_class | paywall_or_login_page | Paywall, subscription, sign-in, or institutional-access page. | Never promote as value-bearing evidence; keep as access evidence. |
| source_byte_class | captcha_page | CAPTCHA, bot-check, or anti-automation page. | Never promote; stop automated retries for the route. |
| source_byte_class | access_denied_page | 403/access-denied page or equivalent. | Never promote; record blocker. |
| source_byte_class | blocked_no_source_object | No usable object was obtained. | Use with extraction_problem/manual to-do. |
| source_byte_class | source_object_unclassified | Bytes were obtained but not classified. | Manual review required before promotion. |
| source_byte_class | not_retrieved | No bytes were retrieved for this access row. | Use when the row documents a locator or attempted route only. |
| relationship_type | extraction_source_reports_result_for_represented_source | The extraction source directly reports a result about the represented source/work. | Default direct assertion relationship when no narrower type applies. |
| relationship_type | corpus_contains_paper | A corpus or collection includes a paper. | Use for paper membership independent of a specific result value. |
| relationship_type | database_reports_paper_result | A database/registry row reports a result or metadata for a paper/study/trial. | Use when the database is the literal source of copied numbers/text. |
| relationship_type | repository_supports_paper | A package/repository supplies data, code, outputs, or supplements for a paper. | Use for replication-package support links. |
| relationship_type | registry_preregisters_study | A registry record preregisters or records the study/trial/protocol. | Use for actual registry/PAP artifacts, not vague corpus claims. |
| relationship_type | registry_links_publication | A registry record links to a paper/report/results source. | Use for post-trial publication/data/program URLs. |
| relationship_type | pre_analysis_plan_supports_study | A PAP/MPAP/protocol supports the study/result selector. | Use when a PAP artifact is available outside a registry row. |
| relationship_type | registered_report_protocol_for_paper | A registered-report Stage 1/protocol source supports the final paper. | Use for registered-report protocol relationships. |
| relationship_type | publication_reports_registered_study | A publication reports results for a registered study. | Use from article to registry when the article itself documents registration. |
| relationship_type | replication_of | A source or result is a replication of another source/result. | Use when original and replication sources are known, not only corpus-level assertion. |
| relationship_type | computational_reproduction_of | A source/result computationally reproduces another paper/result. | Use for same-data/code reproduction relationships. |
| relationship_type | robustness_reanalysis_of | A source/result reanalyzes robustness of another result. | Use for alternative specifications/checks rather than new-sample replication. |
| relationship_type | meta_analysis_includes_study | A meta-analysis or pooled round includes a component study/result. | Use for pooled/component hierarchies. |
| relationship_type | corpus_asserts_result_for_paper | A corpus/database asserts that a represented paper/result has specific numbers. | Use when we are taking the corpus row as the immediate evidence source. |
| relationship_type | corpus_asserts_preregistration_for_paper | A corpus asserts preregistration but no registry/PAP artifact has been obtained. | Keep confidence low unless the artifact is later resolved. |
| relationship_type | paper_uses_dataset | A paper uses or analyzes a dataset/source. | Use for paper-data source relationships. |
| relationship_type | source_derives_from_source | One source object is derived from another. | Use for extracted tables, converted files, and generated outputs. |
| relationship_type | duplicate_of | Two sources/results represent the same object or claim. | Use for dedupe mapping; do not double-count both. |
| relationship_type | parent_collection_contains_child | A parent collection contains a child source/result. | Use for corpus, database, or pooled-round parent-child membership. |
| relationship_subtype | preregistration | General preregistration relationship. | Use when a more specific PAP/registered-report/trial subtype is unavailable. |
| relationship_subtype | pre_analysis_plan | Pre-analysis plan artifact. | Use for PAP documents and PAP sections. |
| relationship_subtype | meta_analysis_pre_analysis_plan | Meta-analysis pre-analysis plan artifact. | Use for MPAPs such as Metaketa pooled analysis plans. |
| relationship_subtype | registered_report_stage1_protocol | Stage 1 registered-report protocol. | Use for accepted protocols before results. |
| relationship_subtype | registered_report_stage2_results | Stage 2 registered-report results paper. | Use when mapping protocol to final registered-report paper. |
| relationship_subtype | trial_registry_record | Trial or study registry record. | Use for NCT/AEA/RIDIE/EGAP/OSF-style registry records. |
| relationship_subtype | data_or_code_package | Data/code/package support relationship. | Use for repository/package mappings. |
| relationship_subtype | paper_supplement | Supplementary paper file relationship. | Use for appendices, supplements, and supplemental tables. |
| relationship_subtype | direct_replication | Replication intended to repeat the same claim/design closely. | Use for same-claim original/replication pairs. |
| relationship_subtype | conceptual_replication | Replication of a construct using different operationalization/design. | Use when source says conceptual replication or design differs materially. |
| relationship_subtype | computational_reproduction | Same-data/code reproduction. | Use for computational reproducibility checks. |
| relationship_subtype | robustness_reanalysis | Alternative analysis/specification check. | Use for robustness projects. |
| relationship_subtype | extension_study | Replication plus extension or new conditions. | Use when extension is material. |
| relationship_subtype | pilot_full_scale_pair | Pilot/smaller study paired with later full-scale/larger study. | Use for pilot-to-main-study pairs. |
| relationship_subtype | pooled_round_component | Component study included in pooled round/meta-analysis. | Use for Metaketa and similar pooled designs. |
| relationship_subtype | corpus_child_paper | Paper included as a child of a corpus. | Use for membership without result-level numbers. |
| relationship_subtype | database_child_result | Result row included as child of a database/corpus. | Use for row-level source assertions. |
| relationship_subtype | citation_or_link_only | Relationship inferred only from citation/link metadata. | Use when no value/selector evidence has been copied. |
| relationship_subtype | unknown | Subtype is not yet known. | Use only while staged; add an extraction_problem if it matters for promotion. |
| replication_role | none | No replication/reproduction relationship is asserted for this result. | Default for ordinary result rows. |
| replication_role | original_study | This result is the original/target side of a replication pair. | Use when paired to later replication/reproduction. |
| replication_role | replication_study | This result is the replicating/follow-up side. | Use for new-sample/direct/conceptual replication rows. |
| replication_role | computational_reproduction | This result is a computational reproduction of a prior result. | Use for same-data/code reproduction. |
| replication_role | robustness_check | This result is a robustness reanalysis of a prior result. | Use for alternative specifications/checks. |
| replication_role | corpus_replication_assertion | The row asserts a replication relationship, but side/source details are incomplete. | Stage until original/replication sides are resolved. |
| replication_role | unknown | Role is not yet known. | Use only temporarily and add a problem if relevant. |
| d_conversion_method | reported_d | Source directly reports Cohen's d. | Use directly; document whether signed/absolute and any correction. |
| d_conversion_method | reported_g | Source directly reports Hedges' g. | Use directly or store as g; document if converted to d-like axis. |
| d_conversion_method | reported_smd | Source directly reports standardized mean difference. | Use when the standardization is source-defined. |
| d_conversion_method | chinn_log_or_to_d | Log odds ratio converted to d by Chinn formula. | Require log OR and enough context to justify latent-scale conversion. |
| d_conversion_method | event_counts_to_log_or_to_d | Arm event counts converted to log OR then d. | Require treatment/control event and non-event counts; record continuity correction if used. |
| d_conversion_method | r_to_d | Correlation converted to d. | Use d = 2r/sqrt(1-r^2). |
| d_conversion_method | fisher_z_to_r_to_d | Fisher z converted to r then d. | Use r = tanh(z), then r_to_d. |
| d_conversion_method | standardized_outcome_coefficient | Regression coefficient on a documented standardized outcome. | Use only when outcome standardization source is documented. |
| d_conversion_method | source_provided_d_proxy | A source/corpus provides a D-like proxy but original conversion is not fully verified. | Flag as proxy and avoid claiming original-source conversion. |
| d_conversion_method | paper_median_of_child_d | Paper-level/canonical D is the median of eligible child result Ds. | Preserve child rows and aggregation rule. |
| d_conversion_method | no_d_native_metric | No defensible D conversion; native metric only. | Use for native panel rows. |
| d_conversion_method | blocked_missing_inputs | D/native conversion is blocked because inputs are missing. | Add extraction_problem and to-do. |
| prereg_status | prereg_confirmed_pre_data | Preregistration/PAP confirmed before data collection. | Use only with date/timing evidence. |
| prereg_status | prereg_confirmed_pre_analysis | Preregistration/PAP confirmed before analysis/results but not necessarily before data collection. | Use only with timing evidence. |
| prereg_status | registered_report | Registered-report workflow evidence exists. | Use with protocol/stage mapping details. |
| prereg_status | proposal_pre_fielding_not_full_prereg | A proposal/design was locked before fielding but lacks full preregistration/PAP elements. | Useful for TESS-like cases; do not overstate as PAP-confirmed. |
| prereg_status | registry_metadata_only | A registry record exists but timing/selector/details are not fully audited. | Use until filing date and selector text are verified. |
| prereg_status | registry_record_timing_not_audited | A registry record is identified and sourceable, but its preregistration timing has not been audited. | Use for registry-derived rows until dates/amendments are checked. |
| prereg_status | prereg_asserted_by_corpus_no_artifact | A corpus or source label says preregistered, but no registry/PAP artifact URL has been obtained. | Low-confidence prereg evidence; must not become PAP-confirmed without artifact. |
| prereg_status | not_preregistered | Evidence indicates no preregistration. | Use only when source/corpus explicitly classifies it as not preregistered. |
| prereg_status | unknown | Preregistration status has not been determined. | Use as default outside prereg panels. |
| coding_status | fully_coded | All applicable promotion gates pass. | Only use when source identity, access, locator, verbatim text, parse, transformation, selector, and dedupe are complete. |
| coding_status | coded_with_schema_gaps | Useful staged row with known provenance gaps. | Keep visible and non-promoted until gaps are resolved. |
| coding_status | staged_native_metric | Native effect/SE/N are meaningful, but D conversion is not defensible. | Use for clustered/policy/administrative effects lacking D inputs. |
| coding_status | blocked_missing_d_or_n | Source exists but effect, N, or conversion inputs are missing. | Add extraction_problem with exact missing field. |
| coding_status | blocked_access | Access barrier prevents source acquisition or verification. | Record route, barrier, and manual action needed. |
| coding_status | excluded | Row is intentionally excluded from plotting/analysis. | Explain why in notes/problem row. |
| coding_status | duplicate_existing | Row duplicates another represented result. | Map duplicate and ensure canonical_result does not double-count it. |
| evidence_level_name | unanchored_number | A number exists but cannot be tied to an external source or represented work. | Level 0; never public-promote. |
| evidence_level_name | internal_trace_only | The row traces only to this repo's derived/intermediate files. | Level 1; useful for debugging, not public evidence. |
| evidence_level_name | external_source_assertion | An external source asserts the number but does not identify the represented target robustly. | Level 2; corpus assertion without durable child grounding. |
| evidence_level_name | external_assertion_with_target_source | An external source asserts the number and provides enough info to find the target source. | Level 3; current minimum floor for public diagnostic plotting. |
| evidence_level_name | target_source_independently_grounded | The represented target source was resolved independently by DOI/PMID/PMCID/NCT/registry/URL/citation database. | Level 4; identity grounded, number not yet verified from original. |
| evidence_level_name | original_source_obtained | Value-bearing source object bytes were obtained or mirrored. | Level 5; metadata/paywall/abstract-only pages do not count unless value is present. |
| evidence_level_name | original_number_extracted | We copied/extracted the exact number/supporting text from original or authoritative source bytes. | Level 6; source-text verification achieved. |
| evidence_level_name | recomputed_from_raw | We recomputed the number from raw data/code and preserved outputs. | Level 7; strongest computational provenance. |

## Files

- Machine-readable table codebook: `data/derived/effect_inflation_dataset/provenance_codebook.tsv`
- Machine-readable data dictionary: `data/derived/effect_inflation_dataset/provenance_data_dictionary.tsv`
- Machine-readable controlled-vocabulary dictionary: `data/derived/effect_inflation_dataset/provenance_vocab_dictionary.tsv`
- Empty TSV templates: `data/derived/effect_inflation_dataset/schema_templates/`
- LLM extraction contract: `reports/llm_extraction_contract.md`

## Current Pilot Benchmark

The 300-row pilot is intentionally a stress test, not a final claim that every old row is fully provenanced. Current extractor rewrites should try to reduce `plot_row_only`, `n_only_recovered`, and `source_is_derived_not_original_text` by writing these source-result fields at extraction time. Public plotting should require evidence level 3 or higher unless a plot is explicitly labeled as a diagnostic/worklist view.
