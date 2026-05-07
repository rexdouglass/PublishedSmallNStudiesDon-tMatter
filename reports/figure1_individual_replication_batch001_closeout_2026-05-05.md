# Figure 1 Individual Replication Batch 001 Closeout

Batch 001 is closed for row-finding. Remaining work is either manual acquisition/source extraction or a future policy/native-route question.

## Outputs

- Manual acquisition tasks: `steps/individual_replication_papers/figure1/individual-paper-manual-acquisition-task-batch001.tsv` (10 rows)
- Dedupe baseline: `steps/individual_replication_papers/figure1/individual-paper-dedupe-baseline-batch001.tsv` (109 rows)
- Batch-002 dedupe seed: `steps/individual_replication_papers/figure1/individual-paper-batch002-dedupe-seed.tsv` (109 rows)

## Manual Acquisition Queue

- `event_counts_or_trial_source_needed`: 3
- `original_n_needed`: 1
- `value_bearing_source_object_needed`: 6

### Tasks

- `api_candidate_b9cdb8cc6a76d362` (medium, value_bearing_source_object_needed): manual_acquisition_or_library_access_for_value_bearing_article_and_supplement
- `api_candidate_786cc2f5ecc3de84` (medium, value_bearing_source_object_needed): mirror_elsevier_article_or_osf_data_and_extract_matched_effects
- `api_candidate_c49eb133d5977b06` (medium, original_n_needed): manual_acquisition_of_rabbitt_1968_original_or_authoritative_table_with_original_n
- `api_candidate_fbe05a26e9edabb8` (medium, value_bearing_source_object_needed): manual_acquisition_of_full_article_or_preprint_with_study_values
- `IND-015` (medium, value_bearing_source_object_needed): manual_acquisition_of_hogrefe_article_or_author_manuscript
- `IND-017` (high, value_bearing_source_object_needed): manual_acquisition_of_pnas_article_supplement_or_data_code_for_values
- `IND-019` (medium, value_bearing_source_object_needed): manual_acquisition_of_jep_general_article_and_supplement
- `IND-022` (high, event_counts_or_trial_source_needed): mirror_open_trial_reports_or_registry_records_and_extract_event_counts
- `IND-023` (high, event_counts_or_trial_source_needed): resolve_nejm_or_open_source_routes_and_extract_mortality_counts
- `IND-024` (high, event_counts_or_trial_source_needed): resolve_nejm_or_open_source_routes_and_extract_mortality_counts

## Dedupe Status

- `already_in_current_root_table`: 33
- `held_not_row_source_blocked_or_manual_acquisition`: 10
- `not_row_rejected_after_value_scan`: 9
- `not_row_rejected_seed_or_non_pair`: 7
- `not_row_unresolved_original_target`: 39
- `promoted_to_current_root_row`: 11

## Batch 002 Use

Use `individual-paper-batch002-dedupe-seed.tsv` as an exclusion/manual-acquisition seed before screening new paper-level hits.
