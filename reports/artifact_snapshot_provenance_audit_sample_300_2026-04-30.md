# Artifact Snapshot Provenance Audit

- Sample rows: 300
- Source-file artifacts audited: 249
- Local byte files present: 249/249
- SHA-256 values matching local bytes: 249/249
- Minimum local replay fields complete: 249/249
- Upstream snapshot/version metadata present: 0/249
- Strict source-version replay fields complete: 0/249

## Interpretation

- The pilot already has local byte fixity for most artifacts through `source_file.sha256`; the field is named `sha256`, not `bytes_sha256`.
- The larger scaling gap is upstream source-version provenance: most rows use local source-version placeholders, not concrete AACT/OpenAlex/Unpaywall/S2/PubMed/Crossref snapshot identifiers.
- `extractor_version` is not an artifact-level field yet. It should be recorded on parser/extraction events and source-result support rows when a parser creates value evidence.

## Top Gap Patterns

- `upstream_snapshot_id_or_version_date_missing|extractor_version_missing_until_value_parser_runs`: 249

## Output Files

- `data/derived/effect_inflation_dataset/schema_pilot/artifact_snapshot_provenance_audit_sample_300.tsv`
- `data/derived/effect_inflation_dataset/schema_pilot/artifact_snapshot_provenance_audit_summary_sample_300.tsv`
