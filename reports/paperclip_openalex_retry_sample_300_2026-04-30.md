# Paperclip/OpenAlex Retry on 300-Row Provenance Pilot

Date: 2026-04-30

This pass used Paperclip after authentication plus targeted OpenAlex and direct landing-page retries against the rows that remained below level 4 after the earlier provenance passes.

## Outputs

- `data/derived/effect_inflation_dataset/schema_pilot/paperclip_exact_doi_attempts_remaining_lt4.tsv`
- `data/derived/effect_inflation_dataset/schema_pilot/paperclip_lookup_doi_attempts_remaining_lt4.tsv`
- `data/derived/effect_inflation_dataset/schema_pilot/openalex_details_remaining_resolved_lt4.tsv`
- `data/derived/effect_inflation_dataset/schema_pilot/direct_landing_retry_remaining_apa_lww.tsv`
- `data/derived/effect_inflation_dataset/schema_pilot/flattened_confirmation_scale_sample_300_after_paperclip_openalex_retry.tsv`
- `data/derived/effect_inflation_dataset/schema_pilot/flattened_confirmation_blockers_lt4_sample_300_after_paperclip_openalex_retry.tsv`
- `data/derived/effect_inflation_dataset/schema_pilot/remaining_lt4_resolution_attempts_after_paperclip_openalex_retry.tsv`

Raw cached Paperclip and API artifacts are under:

- `data/cache/provenance_level5/sample_300_targeted/paperclip/`
- `data/cache/provenance_level5/sample_300_targeted/paperclip_exact/`
- `data/cache/provenance_level5/sample_300_targeted/paperclip_lookup/`
- `data/cache/provenance_level5/sample_300_targeted/openalex_remaining/`
- `data/cache/provenance_level5/sample_300_targeted/direct_landing_retry/`

## Updated Level Counts

| Level | Label | Rows |
|---:|---|---:|
| 2 | corpus_assertion_with_citation | 11 |
| 3 | target_independently_resolved | 3 |
| 4 | target_landing_or_abstract_obtained | 100 |
| 5 | independent_nonpaper_result_record_obtained | 52 |
| 6 | preprint_or_author_manuscript_obtained | 7 |
| 7 | final_paper_obtained | 84 |
| 8 | supplement_or_replication_package_obtained | 6 |
| 9 | value_verified_in_source | 37 |

Thresholds after this pass:

| Minimum level | Rows | Percent |
|---:|---:|---:|
| >=4 | 286 | 95.3% |
| >=5 | 186 | 62.0% |
| >=7 | 127 | 42.3% |
| >=9 | 37 | 12.3% |

## What Worked

Paperclip was useful as a hosted literature index for quick abstract-corpus checks. It promoted six rows in the prior Paperclip pass where the hit matched the known DOI exactly. In this retry, exact DOI lookup also helped reject bad candidate DOIs: several Schaefer/Schwarz low-similarity DOI guesses resolve to arXiv/math-physics papers, so those rows remain unpromoted.

OpenAlex supplied an abstract for `sr_60c2a469e71e` (`10.1037/0021-9010.81.5.587`), moving that row from level 3 to level 4. OpenAlex still reports it as closed with no repository full text, so it is not level 5.

## What Did Not Work

Direct APA DOI landing retries still returned Incapsula/bot-block pages for the remaining APA targets. The LWW/ASA Monitor DOI still returned a Cloudflare challenge. These are logged as access artifacts, not evidence.

The Schaefer/Schwarz OSF workbooks and coding PDF remain anonymized. They expose study IDs, year, subdiscipline, N, and effect values, but no article title, DOI, author, URL, or row-to-paper crosswalk. The Linden Study 2 SAV likewise exposes `Year`, `Paper`, `d_random`, and `N_random`, but no paper-title or DOI crosswalk.

## Remaining Below Level 4

Fourteen rows remain below level 4:

- 9 Schaefer/Schwarz anonymized corpus rows needing an ID-to-paper crosswalk.
- 2 Linden random-paper rows needing the Study 2 `Year`/`Paper` index-to-paper crosswalk.
- 2 APA Journal of Applied Psychology rows where metadata confirms the target but no abstract/source object was obtained.
- 1 LWW/ASA Monitor row where metadata confirms the target but the publisher route is bot-blocked and no abstract/source object was obtained.

The manual worklist with exact URLs and next actions is:

`data/derived/effect_inflation_dataset/schema_pilot/remaining_lt4_resolution_attempts_after_paperclip_openalex_retry.tsv`

