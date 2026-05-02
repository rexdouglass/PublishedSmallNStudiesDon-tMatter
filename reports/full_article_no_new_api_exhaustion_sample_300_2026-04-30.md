# Full Article No-New-API Exhaustion Summary

- Generated: 2026-05-01T08:09:03.850863+00:00
- Rows with represented full article text: 162/300
- Paper/other rows with represented full article text: 161/210
- Remaining paper/other rows without full article text: 49

## Evidence Levels

- Level 2: 9
- Level 4: 40
- Level 5: 163
- Level 6: 88

## Full Article File Classes

- `full_article_html`: 67
- `full_article_pdf`: 52
- `full_article_xml`: 39
- `pmc_fulltext_xml`: 4

## Accepted Routes Across Full-Article Passes

- `openaire_instance_url`: 26
- `openalex_location_url`: 22
- `crossref_fulltext_link`: 5
- `europepmc_fulltext_xml`: 4
- `europepmc_fulltext_url`: 1
- `wayback_cdx_pdf`: 1
- `wayback_cdx_html`: 1
- `crossref_relation_doi`: 1
- `osf_file_download`: 1
- `semantic_scholar_openaccess_pdf`: 1

## Remaining Buckets

- `needs_metabus_or_shorthand_crosswalk`: 17
- `needs_manual_or_core_base`: 12
- `needs_identity_crosswalk`: 9
- `public_routes_exhausted`: 8
- `needs_better_identifier`: 3

## Output

- `data/derived/effect_inflation_dataset/schema_pilot/remaining_full_article_worklist_no_new_api_sample_300.tsv`

## BASE Decision

BASE was considered after the public-route exhaustion pass, but not added to the current automated run. It requires administrator approval, User-Agent registration, and IP whitelisting rather than a normal API key. That makes it a later infrastructure task, especially if the runner is on dynamic cloud IPs. The next executable route is CORE, which has a usable API key and enough quota for the remaining pilot rows.
