# Figure 1 Individual Replication batch002 Closeout

batch002 is closed for row-finding. Remaining work is either manual acquisition/source extraction or a future policy/native-route question.

## Outputs

- Manual acquisition tasks: `steps/individual_replication_papers/figure1/individual-paper-manual-acquisition-task-batch002.tsv` (2 rows)
- Dedupe baseline: `steps/individual_replication_papers/figure1/individual-paper-dedupe-baseline-batch002.tsv` (122 rows)
- batch003 dedupe seed: `steps/individual_replication_papers/figure1/individual-paper-batch003-dedupe-seed.tsv` (122 rows)

## Manual Acquisition Queue

- `original_n_needed`: 1
- `value_bearing_source_object_needed`: 1

### Tasks

- `api_candidate_c49eb133d5977b06` (medium, original_n_needed): manual_acquisition_of_rabbitt_1968_original_or_authoritative_table_with_original_n
- `api_candidate_710fd7eb55fc9d77` (medium, value_bearing_source_object_needed): manual_acquisition_of_original_scopolamine_article_or_authoritative_value_table

## Dedupe Status

- `already_in_current_root_table`: 16
- `not_row_rejected_after_value_scan`: 19
- `not_row_rejected_or_duplicate`: 41
- `not_row_rejected_seed_or_non_pair`: 7
- `not_row_source_blocked_or_manual_acquisition`: 2
- `not_row_unresolved_original_target`: 35
- `promoted_to_current_root_row`: 2

## Batch 002 Use

Use `individual-paper-batch003-dedupe-seed.tsv` as an exclusion/manual-acquisition seed before screening new paper-level hits.
