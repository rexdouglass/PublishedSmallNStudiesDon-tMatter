# Full Article Text Acquisition Pass

- Targets considered: 49
- Route attempt rows: 88
- Newly accepted full-article text objects: 2
- Rows with represented full article after pass: 164/300
- Paper/other represented rows with full article after pass: 163

## Accepted Rows

- `sr_612caed0e0da` -> `file_4ea80abba16c` via `core_fulltext_url`; `data/cache/full_article_text_acquisition/sample_300/sr_612caed0e0da__core_fulltext_url__a7b646aca02f.pdf`
- `sr_dc8fc4fdac47` -> `file_e198dd7c6b04` via `core_fulltext_url`; `data/cache/full_article_text_acquisition/sample_300/sr_dc8fc4fdac47__core_fulltext_url__be3599e5ea1c.html`

## Failure Profile

- `http_403_blocked`: 55
- `identity_or_plausibility_failed`: 11
- `unknown_or_non_article_bytes`: 11
- `captcha_or_bot_block`: 3
- `http_404`: 2
- `full_article_text_obtained`: 2
- `request_error`: 2
- `login_or_paywall_html`: 1
- `html_not_full_article`: 1

## Notes

- This pass accepts PDF, XML/JATS, or full-article HTML when the primary DOI/title identity gate passes.
- Repository and archive routes are treated as candidate generators. Landing pages and metadata-only hits stay in the candidate ledger and do not promote.
- CORE and BASE are not included here because CORE is currently rate-limiting/key-gated in this environment and BASE requires whitelisting.

## Output Files

- `data/derived/effect_inflation_dataset/schema_pilot/full_article_text_acquisition_attempts_sample_300_core_key.tsv`
- `data/derived/effect_inflation_dataset/schema_pilot/full_article_text_acquisition_summary_sample_300_core_key.tsv`
- `data/derived/effect_inflation_dataset/schema_pilot/source_object_candidate_codebook_sample_300.tsv`
- `data/derived/effect_inflation_dataset/schema_pilot/source_file_codebook_sample_300.tsv`
- `data/derived/effect_inflation_dataset/schema_pilot/source_result_codebook_sample_300.tsv`
