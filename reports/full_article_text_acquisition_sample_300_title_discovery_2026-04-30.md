# Full Article Text Acquisition Pass

- Targets considered: 53
- Route attempt rows: 72
- Newly accepted full-article text objects: 4
- Rows with represented full article after pass: 162/300
- Paper/other represented rows with full article after pass: 161

## Accepted Rows

- `sr_60360366c47c` -> `file_3e77a4af8f2c` via `openalex_location_url`; `data/cache/full_article_text_acquisition/sample_300/sr_60360366c47c__openalex_location_url__30985e6199e3.html`
- `sr_68c0e5067d4b` -> `file_a7bc63853e70` via `semantic_scholar_openaccess_pdf`; `data/cache/full_article_text_acquisition/sample_300/sr_68c0e5067d4b__semantic_scholar_openaccess_pdf__512fa01f70af.html`
- `sr_6d53289e06ab` -> `file_9e62a32926cb` via `openalex_location_url`; `data/cache/full_article_text_acquisition/sample_300/sr_6d53289e06ab__openalex_location_url__9bbe512b56ec.html`
- `sr_b55639792416` -> `file_8985e92a12d5` via `openalex_location_url`; `data/cache/full_article_text_acquisition/sample_300/sr_b55639792416__openalex_location_url__769a45aa2148.html`

## Failure Profile

- `http_403_blocked`: 40
- `unknown_or_non_article_bytes`: 11
- `identity_or_plausibility_failed`: 10
- `captcha_or_bot_block`: 5
- `full_article_text_obtained`: 4
- `login_or_paywall_html`: 1
- `html_not_full_article`: 1

## Notes

- This pass accepts PDF, XML/JATS, or full-article HTML when the primary DOI/title identity gate passes.
- Repository and archive routes are treated as candidate generators. Landing pages and metadata-only hits stay in the candidate ledger and do not promote.
- CORE and BASE are not included here because CORE is currently rate-limiting/key-gated in this environment and BASE requires whitelisting.

## Output Files

- `data/derived/effect_inflation_dataset/schema_pilot/full_article_text_acquisition_attempts_sample_300_title_discovery.tsv`
- `data/derived/effect_inflation_dataset/schema_pilot/full_article_text_acquisition_summary_sample_300_title_discovery.tsv`
- `data/derived/effect_inflation_dataset/schema_pilot/source_object_candidate_codebook_sample_300.tsv`
- `data/derived/effect_inflation_dataset/schema_pilot/source_file_codebook_sample_300.tsv`
- `data/derived/effect_inflation_dataset/schema_pilot/source_result_codebook_sample_300.tsv`
