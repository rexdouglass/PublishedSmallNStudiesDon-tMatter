# Codebook Validation For 300-Row Provenance Pilot

This validates the existing 300-row pilot files against `provenance_data_dictionary.tsv`. It distinguishes retrace reproducibility from full codebook conformance.

## Bottom Line

The 300-row pilot is **not** correctly coded as a fully promotable dataset yet. The codebook-shaped tables exist, but some rows still fail promotion gates such as source locators, verbatim source-result fields, original-source evidence, or explicit problem coding.

## Table Summary

| Table | Rows | Columns | High issue types | Medium | Low | Passes full promotion |
| --- | --- | --- | --- | --- | --- | --- |
| source.tsv | 331 | 13 | 0 | 0 | 0 | True |
| source_access.tsv | 55 | 33 | 0 | 0 | 0 | True |
| source_access_attempt.tsv | 1711 | 51 | 0 | 0 | 0 | True |
| source_file.tsv | 249 | 31 | 0 | 0 | 0 | True |
| source_version.tsv | 331 | 18 | 0 | 0 | 0 | True |
| source_access_right.tsv | 249 | 20 | 0 | 0 | 0 | True |
| source_identifier.tsv | 829 | 8 | 0 | 0 | 0 | True |
| source_classification.tsv | 949 | 6 | 0 | 0 | 0 | True |
| source_result.tsv | 300 | 74 | 4 | 1 | 0 | False |
| canonical_result.tsv | 300 | 19 | 0 | 0 | 0 | True |
| canonical_result_membership.tsv | 300 | 8 | 0 | 0 | 0 | True |
| source_result_support.tsv | 1544 | 22 | 0 | 0 | 0 | True |
| plot_membership.tsv | 300 | 20 | 0 | 0 | 0 | True |
| source_source_mapping.tsv | 454 | 32 | 0 | 0 | 0 | True |
| extraction_event.tsv | 1708 | 14 | 0 | 0 | 0 | True |
| extraction_problem.tsv | 267 | 11 | 0 | 0 | 0 | True |
| manual_acquisition_task.tsv | 263 | 24 | 0 | 0 | 0 | True |

## Issue Type Counts

| Severity | Issue code | Issue type count |
| --- | --- | --- |
| high | blank_promotion_gate_values | 1 |
| high | not_human_checkable_source_cells | 1 |
| high | source_result_not_fully_coded | 2 |
| medium | rows_still_coded_with_schema_gaps | 1 |

## Machine-Readable Outputs

- `data/derived/effect_inflation_dataset/schema_pilot/codebook_validation_summary.tsv`
- `data/derived/effect_inflation_dataset/schema_pilot/codebook_validation_issues.tsv`
