# Figure 1 Individual Replication batch005 Closeout

batch005 is closed for row-finding. Remaining work is either manual acquisition/source extraction or a future policy/native-route question.

## Outputs

- Manual acquisition tasks: `steps/individual_replication_papers/figure1/individual-paper-manual-acquisition-task-batch005.tsv` (4 rows)
- Dedupe baseline: `steps/individual_replication_papers/figure1/individual-paper-dedupe-baseline-batch005.tsv` (343 rows)
- batch006 dedupe seed: `steps/individual_replication_papers/figure1/individual-paper-batch006-dedupe-seed.tsv` (343 rows)

## Manual Acquisition Queue

- `original_n_needed`: 1
- `value_bearing_source_object_needed`: 3

### Tasks

- `api_candidate_c49eb133d5977b06` (medium, original_n_needed): manual_acquisition_of_rabbitt_1968_original_or_authoritative_table_with_original_n
- `api_candidate_d98523e0ce3e5e0d` (medium, value_bearing_source_object_needed): manual_acquisition_if_this_2025_communication_replication_is_prioritized
- `api_candidate_710fd7eb55fc9d77` (medium, value_bearing_source_object_needed): manual_acquisition_of_original_scopolamine_article_or_authoritative_value_table
- `api_candidate_7c25e95e83db7d9a` (medium, value_bearing_source_object_needed): manual_acquisition_if_clinical_real_world_validation_rows_are_in_scope

## Dedupe Status

- `already_in_current_root_table`: 22
- `not_row_rejected_after_value_scan`: 49
- `not_row_rejected_or_duplicate`: 252
- `not_row_rejected_seed_or_non_pair`: 9
- `not_row_source_blocked_or_manual_acquisition`: 4
- `promoted_to_current_root_row`: 7

## batch006 Use

Use `individual-paper-batch006-dedupe-seed.tsv` as an exclusion/manual-acquisition seed before screening new paper-level hits.
