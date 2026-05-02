# Full Article Text Acquisition Pass

- Targets considered: 74
- Route attempt rows: 137
- Newly accepted full-article text objects: 21
- Rows with represented full article after pass: 158/300
- Paper/other represented rows with full article after pass: 157

## Accepted Rows

- `sr_e74bda715816` -> `file_d0c3e223f3ae` via `openalex_location_url`; `data/cache/full_article_text_acquisition/sample_300/sr_e74bda715816__openalex_location_url__f95579ec87be.html`
- `sr_f339c0254923` -> `file_3d19d321bfda` via `openalex_location_url`; `data/cache/full_article_text_acquisition/sample_300/sr_f339c0254923__openalex_location_url__a64eb856195d.html`
- `sr_b0fb1425aea4` -> `file_5bbf756a53fe` via `openalex_location_url`; `data/cache/full_article_text_acquisition/sample_300/sr_b0fb1425aea4__openalex_location_url__110e2f6ee035.html`
- `sr_553821bb35af` -> `file_d8204ee7aacb` via `openalex_location_url`; `data/cache/full_article_text_acquisition/sample_300/sr_553821bb35af__openalex_location_url__9ba40276cc6d.html`
- `sr_fbb29ff3b4c7` -> `file_433f07d801e7` via `openalex_location_url`; `data/cache/full_article_text_acquisition/sample_300/sr_fbb29ff3b4c7__openalex_location_url__9f077c0dd150.html`
- `sr_0832a411bca2` -> `file_fc6b52dea719` via `openalex_location_url`; `data/cache/full_article_text_acquisition/sample_300/sr_0832a411bca2__openalex_location_url__0a9381f9f998.html`
- `sr_6c3663410cb7` -> `file_372df1547914` via `openalex_location_url`; `data/cache/full_article_text_acquisition/sample_300/sr_6c3663410cb7__openalex_location_url__b3c658325765.html`
- `sr_5b1a0fc622e3` -> `file_1eba9d2547c2` via `openalex_location_url`; `data/cache/full_article_text_acquisition/sample_300/sr_5b1a0fc622e3__openalex_location_url__f69293990e9c.html`
- `sr_581b0190b9f5` -> `file_f3873f3ca03e` via `wayback_cdx_html`; `data/cache/full_article_text_acquisition/sample_300/sr_581b0190b9f5__wayback_cdx_html__fc35d25d4d39.html`
- `sr_9eeaae2c75a9` -> `file_8e12c9de0ebe` via `openalex_location_url`; `data/cache/full_article_text_acquisition/sample_300/sr_9eeaae2c75a9__openalex_location_url__44d78dec4ff6.html`
- `sr_a1c0077f9cb0` -> `file_9816cf4d4318` via `openalex_location_url`; `data/cache/full_article_text_acquisition/sample_300/sr_a1c0077f9cb0__openalex_location_url__f23145a7ff65.html`
- `sr_ef6a224b8b86` -> `file_508711899f3e` via `openalex_location_url`; `data/cache/full_article_text_acquisition/sample_300/sr_ef6a224b8b86__openalex_location_url__6362233f3b57.html`
- `sr_026ab716fdc2` -> `file_3bfba30961bd` via `openalex_location_url`; `data/cache/full_article_text_acquisition/sample_300/sr_026ab716fdc2__openalex_location_url__15d3576be481.html`
- `sr_d19dc790ebd7` -> `file_eb06e19fcd4e` via `openalex_location_url`; `data/cache/full_article_text_acquisition/sample_300/sr_d19dc790ebd7__openalex_location_url__578421f97d89.html`
- `sr_de1c92df2ed9` -> `file_ffbe65966db3` via `openalex_location_url`; `data/cache/full_article_text_acquisition/sample_300/sr_de1c92df2ed9__openalex_location_url__742c9563a07c.html`
- `sr_09896453a68e` -> `file_102f736528b6` via `openalex_location_url`; `data/cache/full_article_text_acquisition/sample_300/sr_09896453a68e__openalex_location_url__5418d120c55d.html`
- `sr_7432aa117bcb` -> `file_8042e20d6f3b` via `openalex_location_url`; `data/cache/full_article_text_acquisition/sample_300/sr_7432aa117bcb__openalex_location_url__0ea3f602ca2a.html`
- `sr_5d9a9531214b` -> `file_b9f0436d7e0b` via `openalex_location_url`; `data/cache/full_article_text_acquisition/sample_300/sr_5d9a9531214b__openalex_location_url__c711572777ae.html`
- `sr_14b1bfc72686` -> `file_5a06dd481ed4` via `openalex_location_url`; `data/cache/full_article_text_acquisition/sample_300/sr_14b1bfc72686__openalex_location_url__2e79a4e8460a.html`
- `sr_4adf6fd2310b` -> `file_66ebbcc1053c` via `openalex_location_url`; `data/cache/full_article_text_acquisition/sample_300/sr_4adf6fd2310b__openalex_location_url__a5d2b0995cc6.html`
- `sr_09538e441d8b` -> `file_77648f4156e2` via `crossref_relation_doi`; `data/cache/full_article_text_acquisition/sample_300/sr_09538e441d8b__crossref_relation_doi__e201b7f70aef.html`

## Failure Profile

- `http_403_blocked`: 80
- `full_article_text_obtained`: 21
- `captcha_or_bot_block`: 12
- `unknown_or_non_article_bytes`: 12
- `identity_or_plausibility_failed`: 10
- `login_or_paywall_html`: 1
- `html_not_full_article`: 1

## Notes

- This pass accepts PDF, XML/JATS, or full-article HTML when the primary DOI/title identity gate passes.
- Repository and archive routes are treated as candidate generators. Landing pages and metadata-only hits stay in the candidate ledger and do not promote.
- CORE and BASE are not included here because CORE is currently rate-limiting/key-gated in this environment and BASE requires whitelisting.

## Output Files

- `data/derived/effect_inflation_dataset/schema_pilot/full_article_text_acquisition_attempts_sample_300_no_key_expansion.tsv`
- `data/derived/effect_inflation_dataset/schema_pilot/full_article_text_acquisition_summary_sample_300_no_key_expansion.tsv`
- `data/derived/effect_inflation_dataset/schema_pilot/source_object_candidate_codebook_sample_300.tsv`
- `data/derived/effect_inflation_dataset/schema_pilot/source_file_codebook_sample_300.tsv`
- `data/derived/effect_inflation_dataset/schema_pilot/source_result_codebook_sample_300.tsv`
