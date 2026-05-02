# Original PDF Identity Check

- PDF candidate rows checked: 11
- Source-result rows checked: 11
- Accepted as matching represented source: 11
- Rejected as wrong source: 0
- Needs manual identity check: 0
- Projected level >=5 after accepted promotions only: 194/300

## Decision Counts

- `accepted_pdf_identity`: 11

## Accepted Routes

- `unpaywall_pdf`: 7
- `crossref_tdm_pdf`: 2
- `europepmc_pdf`: 1
- `semantic_scholar_openaccess_pdf`: 1

## Rejected Examples

- None.

## Interpretation

- This is the gate between PDF acquisition and source_file promotion. A row can download a PDF and still be rejected here if the route came from a non-primary DOI or another weak lead.
- Primary DOIs come from `source.tsv` and primary `source_identifier` rows only. Non-primary grounding URLs are preserved as leads, but they do not count as identity anchors.
- Manual rows are not failures; they need human confirmation because the represented source has a weak/synthetic title, no primary DOI, or an incomplete text signal.

## Output Files

- `data/derived/effect_inflation_dataset/schema_pilot/original_pdf_identity_check_sample_300.tsv`
- `data/derived/effect_inflation_dataset/schema_pilot/original_pdf_identity_check_summary_sample_300.tsv`
