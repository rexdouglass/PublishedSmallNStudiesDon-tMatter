# Level-5 Push Probe For 300-Row Provenance Pilot

This probe tries to mirror strict level-5 source objects for rows that were already at level 4 (`target_source_independently_grounded`). It does not promote rows automatically; it writes auditable fetch attempts.

## Result

- Rows already at level >=5 before the probe: 43/300 (14.3%)
- Level-4 rows attempted: 242
- Rows with at least one strict level-5-eligible source object mirrored: 140/242 (57.9%)
- Rows still below level 5 after this probe: 102/242 (42.1%)
- Projected level >=5 after review/promotion of strict candidates: 183/300 (61.0%)

Row-level quality:

- strict level-5 source object obtained: 140
- noneligible bytes obtained: 102
- not obtained: 0

By identifier route:

- doi_article::not_obtained: 98
- doi_article::obtained: 44
- nct_registry::obtained: 52
- other_url::not_obtained: 1
- pmc_fulltext::obtained: 4
- pmid_record::not_obtained: 3
- pmid_record::obtained: 40

## Files

- `data/derived/effect_inflation_dataset/schema_pilot/level5_fetch_attempts_sample_300.tsv`
- `data/derived/effect_inflation_dataset/schema_pilot/level5_fetch_summary_sample_300.tsv`
- `data/derived/effect_inflation_dataset/schema_pilot/level5_row_status_sample_300.tsv`
- `data/derived/effect_inflation_dataset/schema_pilot/level5_remaining_todos_sample_300.tsv`
- mirrored bytes under `data/cache/provenance_level5/sample_300/`

## Route Strategy Columns

The row-status TSV records acquisition routes separately instead of flattening every fetch into one status:

- `strategy_direct_journal_or_doi_landing_*`: direct DOI/publisher attempt, including paywall, abstract page, bot block, or HTTP block.
- `strategy_oa_candidate_url_*`: candidate full-text/PDF/XML URLs exposed by Crossref, OpenAlex, Semantic Scholar, Europe PMC, or Unpaywall-style metadata.
- `strategy_preprint_repository_candidate_*`: repository, preprint, author-manuscript, or institutional-archive candidates discovered through metadata routes.
- `abstract_or_detail_*`: short abstract, title, description, registry summary, or other lawful detail text extracted from metadata or returned landing pages. This is grounding evidence only; it does not make a row level 5 unless the object itself is value-bearing.
- `paywall_or_login_seen`, `captcha_or_bot_block_seen`, `blocked_http_status_seen`, and `publisher_landing_or_abstract_seen`: blocker flags for manual follow-up.

## Summary

- existing_rows_level5_or_higher_before_probe: 43
- level4_rows_attempted: 242
- rows_with_strict_level5_source_object_obtained: 140
- rows_with_noneligible_bytes_only: 102
- rows_still_below_level5_after_probe: 102
- rows_with_no_bytes_at_all: 0
- strict_total_level5_or_higher_after_review: 183
- fetch_attempts: 1656
- rows_with_abstract_or_detail_obtained: 242
- rows_with_detail_containing_number: 170
- rows_with_detail_containing_effect_term: 60
- rows_with_detail_containing_n_term: 99
- rows_with_paywall_or_login_seen: 32
- rows_with_captcha_or_bot_block_seen: 74
- rows_with_preprint_or_repository_candidate_seen: 12
- by_kind::doi_article::obtained_False: 98
- by_kind::doi_article::obtained_True: 44
- by_kind::nct_registry::obtained_True: 52
- by_kind::other_url::obtained_False: 1
- by_kind::pmc_fulltext::obtained_True: 4
- by_kind::pmid_record::obtained_False: 3
- by_kind::pmid_record::obtained_True: 40
- strategy_attempts::crossref_metadata: 185
- strategy_attempts::datacite_metadata: 133
- strategy_attempts::direct_journal_or_doi_landing: 98
- strategy_attempts::europepmc_metadata: 118
- strategy_attempts::oa_candidate_url: 628
- strategy_attempts::openalex_metadata: 133
- strategy_attempts::pmc_fulltext: 32
- strategy_attempts::preprint_repository_candidate: 14
- strategy_attempts::pubmed_bridge: 86
- strategy_attempts::registry_clinicaltrials: 104
- strategy_attempts::semantic_scholar_metadata: 124
- strategy_attempts::stable_url: 1
- direct_journal_status::abstract_or_detail_obtained: 50
- direct_journal_status::blocked_http_status: 39
- direct_journal_status::landing_or_abstract_obtained: 1
- direct_journal_status::not_tried: 144
- direct_journal_status::paywall_or_login: 8
- preprint_repository_status::abstract_or_detail_obtained: 1
- preprint_repository_status::captcha_or_bot_block: 1
- preprint_repository_status::landing_or_abstract_obtained: 2
- preprint_repository_status::level5_source_object_obtained: 5
- preprint_repository_status::not_tried: 230
- preprint_repository_status::paywall_or_login: 2
- preprint_repository_status::request_failed: 1
- fetch_status::blocked_access_denied_text: 1
- fetch_status::blocked_bot_or_captcha: 105
- fetch_status::blocked_http_status: 330
- fetch_status::landing_or_abstract_obtained: 123
- fetch_status::landing_or_paywall_obtained: 62
- fetch_status::request_failed: 199
- fetch_status::source_object_obtained: 192
- fetch_status::support_metadata_obtained: 644
