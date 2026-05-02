# Source Object Candidate Ledger

- Candidate rows written: 865
- Result rows represented in candidate ledger: 113
- Identity-accepted source-object candidates: 11
- Block/paywall/bot candidate rows logged: 241
- Metadata-only candidate rows logged: 588
- Rows still below level 5 after PDF promotion: 106/300

## Why This Exists

This ledger is the staging layer between discovery routes and `source_file` promotion. Future OpenAIRE, CORE, BASE, Fatcat/Wayback, OSF, Dataverse, Zenodo, Figshare, AACT, Paperclip, and manual-capture resolvers should append rows here first. A row does not promote just because a route found metadata or a URL; it promotes only after mirrored bytes pass the relevant identity gate.

## Candidate Evidence Classes

- `level4_metadata_candidate`: 568
- `no_promotion`: 255
- `level4_or_blocker_no_source_bytes`: 31
- `level5_candidate_full_article`: 11

## Route Families

- `crossref`: 239
- `unpaywall`: 143
- `semantic_scholar`: 128
- `openalex`: 126
- `europepmc`: 114
- `doi_accept`: 112
- `pubmed`: 3

## Next Resolver Modules To Add

1. OpenAIRE/CORE/BASE repository candidates for DOI-grounded level-4 rows.
2. Fatcat/Wayback candidates for 403/404/dead publisher and repository URLs.
3. Crossref/DataCite related-object candidates for supplements, datasets, and preprints.
4. OSF/PsyArXiv/SocArXiv candidates for psychology/social-science preprints and project files.
5. AACT historical snapshot candidates for registry-version drift.
6. Manual/Zotero capture candidates for rows still blocked after repository/archive routes.

## Output Files

- `data/derived/effect_inflation_dataset/schema_pilot/source_object_candidate_codebook_sample_300.tsv`
- `data/derived/effect_inflation_dataset/schema_pilot/source_object_candidate_summary_sample_300.tsv`
