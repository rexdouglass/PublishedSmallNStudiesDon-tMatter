# Codebook Pilot Learning Report

This report is generated from the 300-row retrace pilot after backfilling recovered source cells into codebook-shaped tables.

## What Improved

- The 300-row pilot now has codebook-shaped source, access, file/artifact, support, mapping, plot-membership, and manual-task tables.
- Synthetic repo-generated citations are kept in `generated_result_*` fields and are not used as represented-source citations.
- Every retrace step has an `extraction_event` row with path, checksum where available, and matching method.

## What Is Still Hard

- Most rows are recoverable only to an upstream derived row, not to the original paper or registry table text.
- Collapsed paper-level rows need child-result rows preserved at extraction time; reconstructing after plotting requires source-corpus/unit-id matching.
- Registry-derived rows can expose p values and enrollment cleanly, but not always a native effect estimate.

## Summary

| Metric | Value |
| --- | --- |
| source_result_rows | 300 |
| source_rows | 331 |
| source_access_rows | 55 |
| source_access_attempt_rows | 1711 |
| source_file_rows | 249 |
| source_version_rows | 331 |
| source_access_right_rows | 249 |
| source_identifier_rows | 829 |
| source_classification_rows | 949 |
| canonical_result_membership_rows | 300 |
| source_result_support_rows | 1544 |
| plot_membership_rows | 300 |
| extraction_event_rows | 1708 |
| extraction_problem_rows | 267 |
| manual_acquisition_task_rows | 263 |
| source_results_with_verbatim_effect_text | 298 |
| source_results_with_verbatim_n_text | 300 |
| source_results_with_verbatim_source_row_text | 300 |
| source_results_with_prereg_mapping | 100 |
| source_results_with_prereg_artifact_url | 93 |
| source_results_with_prereg_selector_text | 100 |
| source_results_with_replication_mapping | 54 |
| source_results_with_replication_pair_id | 54 |
| source_results_marked_fully_coded | 38 |
| source_results_marked_coded_with_schema_gaps | 262 |
| source_directness::candidate_child_numeric_row | 211 |
| source_directness::plot_row_only | 2 |
| source_directness::political_science_component_rows | 1 |
| source_directness::raw_ctgov_registry_row | 37 |
| source_directness::replication_pair_source_row | 48 |
| source_directness::staged_replication_pair_source_row | 1 |
| source_text_extraction_status::n_only_recovered | 2 |
| source_text_extraction_status::source_cells_recovered | 298 |
| evidence_level_name::external_source_assertion | 19 |
| evidence_level_name::original_number_extracted | 88 |
| evidence_level_name::original_source_obtained | 95 |
| evidence_level_name::target_source_independently_grounded | 98 |
| target_acquisition_state::source_object_mirrored | 95 |
| target_acquisition_state::target_identity_known | 19 |
| target_acquisition_state::target_located | 98 |
| target_acquisition_state::text_or_data_extracted | 88 |
| value_verification_state::corpus_assertion_only | 117 |
| value_verification_state::d_n_verified_from_source | 88 |
| value_verification_state::source_object_obtained_not_parsed | 95 |
| prereg_status::prereg_asserted_by_corpus_no_artifact | 7 |
| prereg_status::registry_metadata_only | 1 |
| prereg_status::registry_record_timing_not_audited | 92 |
| prereg_status::unknown | 200 |
| replication_role::none | 246 |
| replication_role::original_study | 31 |
| replication_role::replication_study | 23 |
| mapping_relationship_type::corpus_asserts_preregistration_for_paper | 7 |
| mapping_relationship_type::corpus_asserts_result_for_paper | 259 |
| mapping_relationship_type::database_reports_paper_result | 92 |
| mapping_relationship_type::extraction_source_reports_result_for_represented_source | 2 |
| mapping_relationship_type::registry_preregisters_study | 93 |
| mapping_relationship_type::repository_supports_paper | 1 |
| mapping_relationship_subtype::data_or_code_package | 1 |
| mapping_relationship_subtype::database_child_result | 151 |
| mapping_relationship_subtype::direct_replication | 100 |
| mapping_relationship_subtype::pilot_full_scale_pair | 8 |
| mapping_relationship_subtype::preregistration | 8 |
| mapping_relationship_subtype::trial_registry_record | 184 |
| mapping_relationship_subtype::unknown | 2 |
| identifier_type::aea_trial | 1 |
| identifier_type::doi | 106 |
| identifier_type::nct | 93 |
| identifier_type::pmcid | 3 |
| identifier_type::pmid | 36 |
| identifier_type::url | 590 |
| access_attempt_decision::abstract_or_landing_only | 123 |
| access_attempt_decision::access_denied | 1 |
| access_attempt_decision::blocked | 330 |
| access_attempt_decision::captcha_or_bot_block | 105 |
| access_attempt_decision::manual_review | 53 |
| access_attempt_decision::metadata_only | 644 |
| access_attempt_decision::not_retrieved | 199 |
| access_attempt_decision::paywall_or_login | 62 |
| access_attempt_decision::source_object_mirrored | 194 |
| source_file_role::archive | 1 |
| source_file_role::dataset | 2 |
| source_file_role::derived_table | 52 |
| source_file_role::full_article | 88 |
| source_file_role::other | 1 |
| source_file_role::registry_record | 104 |
| source_file_role::supplement | 1 |
| rights_decision::needs_review | 197 |
| rights_decision::not_applicable | 52 |
| manual_needed_artifact::effect_text | 2 |
| manual_needed_artifact::original_source_object | 115 |
| manual_needed_artifact::other | 146 |
| classification_type::field | 302 |
| classification_type::source_family | 349 |
| classification_type::study_design | 298 |
| support_role::access_grounding | 192 |
| support_role::conversion_input | 300 |
| support_role::effect_text | 298 |
| support_role::n_text | 300 |
| support_role::outcome_text | 300 |
| support_role::relationship_evidence | 54 |
| support_role::selector_text | 100 |
| plot_membership::plot1_replication | 26 |
| plot_membership::plot2_published | 56 |
| plot_membership::plot3_preregistered | 24 |
| plot_membership::plot4_all_sources | 194 |
| source_is_original::false | 117 |
| source_is_original::true | 183 |
| number_verified_by_us::false | 212 |
| number_verified_by_us::true | 88 |
| represented_work_identified::false | 19 |
| represented_work_identified::true | 281 |
| source_is_external::false | 4 |
| source_is_external::true | 296 |
| requires_manual_review::false | 88 |
| requires_manual_review::true | 212 |
| conversion_verified::false | 212 |
| conversion_verified::true | 88 |
| problem::missing_source_locator | 3 |
| problem::missing_verbatim_effect_text | 2 |
| problem::source_is_derived_not_original_text | 262 |

## Generated Tables

- `data/derived/effect_inflation_dataset/schema_pilot/source_codebook_sample_300.tsv`
- `data/derived/effect_inflation_dataset/schema_pilot/source_access_codebook_sample_300.tsv`
- `data/derived/effect_inflation_dataset/schema_pilot/source_access_attempt_codebook_sample_300.tsv`
- `data/derived/effect_inflation_dataset/schema_pilot/source_file_codebook_sample_300.tsv`
- `data/derived/effect_inflation_dataset/schema_pilot/source_version_codebook_sample_300.tsv`
- `data/derived/effect_inflation_dataset/schema_pilot/source_access_right_codebook_sample_300.tsv`
- `data/derived/effect_inflation_dataset/schema_pilot/source_identifier_codebook_sample_300.tsv`
- `data/derived/effect_inflation_dataset/schema_pilot/source_classification_codebook_sample_300.tsv`
- `data/derived/effect_inflation_dataset/schema_pilot/source_result_codebook_sample_300.tsv`
- `data/derived/effect_inflation_dataset/schema_pilot/canonical_result_codebook_sample_300.tsv`
- `data/derived/effect_inflation_dataset/schema_pilot/canonical_result_membership_codebook_sample_300.tsv`
- `data/derived/effect_inflation_dataset/schema_pilot/source_result_support_codebook_sample_300.tsv`
- `data/derived/effect_inflation_dataset/schema_pilot/plot_membership_codebook_sample_300.tsv`
- `data/derived/effect_inflation_dataset/schema_pilot/source_source_mapping_codebook_sample_300.tsv`
- `data/derived/effect_inflation_dataset/schema_pilot/extraction_event_codebook_sample_300.tsv`
- `data/derived/effect_inflation_dataset/schema_pilot/extraction_problem_codebook_sample_300.tsv`
- `data/derived/effect_inflation_dataset/schema_pilot/manual_acquisition_task_codebook_sample_300.tsv`
