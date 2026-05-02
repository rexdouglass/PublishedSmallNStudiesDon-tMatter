# Provenance Database Tables And Schemas

Root-level schema index for the provenance database.

Canonical generated files at repo root:

- `PROVENANCE_DATABASE_TABLES_AND_SCHEMAS.yml`: all tables and columns in YAML.
- `PROVENANCE_DATABASE_TABLES.tsv`: one row per table.
- `PROVENANCE_DATABASE_FIELDS.tsv`: one row per field.

Pipeline shape:

```text
search_lead
  -> source / source_access / source_file
  -> source_source_mapping
  -> source_result
  -> canonical_result
  -> plot_membership under plot_universe and plot_criterion
```

## Tables

| Table | Grain | Primary Key | Columns |
| --- | --- | --- | --- |
| source.tsv | One citeable or computational source object. | source_id | 13 |
| source_access.tsv | One route to the bytes for one source. | access_id | 33 |
| source_access_attempt.tsv | One resolver/download/API attempt for one source. | attempt_id | 51 |
| source_file.tsv | One mirrored byte artifact or extracted file/member for one source. | source_file_id | 31 |
| source_version.tsv | One version assertion for one source. | source_version_id | 18 |
| source_access_right.tsv | One access-rights or mirroring decision for one source/file. | access_right_id | 20 |
| source_identifier.tsv | One external identifier, resolver key, or stable URL for one source. | source_id + identifier_type + identifier_value | 8 |
| source_classification.tsv | One classification assertion for one source. | source_id + classification_source | 6 |
| search_lead.tsv | One discovered lead under one search track or plot universe. | search_lead_id | 27 |
| source_result.tsv | One result asserted or exposed by one extraction source. | source_result_id | 74 |
| canonical_result.tsv | One deduplicated result selected or summarized from one or more source-result rows. | canonical_result_id | 19 |
| canonical_result_membership.tsv | One source-result row's membership in one canonical plotted/staged result. | canonical_result_id + source_result_id | 8 |
| source_result_support.tsv | One source/access object supporting one source-result field or decision. | source_result_id + source_id + access_id + support_role | 22 |
| plot_universe.tsv | One reusable plot, panel, statistic set, diagnostic view, or future plot context. | plot_universe_id | 10 |
| plot_criterion.tsv | One reusable inclusion, exclusion, or context criterion. | criterion_id | 10 |
| plot_membership.tsv | One canonical result's inclusion/exclusion status in one plot or statistic set. | plot_id + canonical_result_id | 20 |
| source_source_mapping.tsv | One directed relationship between two sources. | mapping_id | 32 |
| extraction_event.tsv | One action or failed action used to obtain, parse, or verify source bytes. | event_id | 14 |
| extraction_problem.tsv | One quality or provenance problem for one source-result or source object. | problem_id | 11 |
| manual_acquisition_task.tsv | One human/manual acquisition or verification task. | manual_task_id | 24 |

The nested generated copies remain under `data/derived/effect_inflation_dataset/` for pipelines that already read those paths.
