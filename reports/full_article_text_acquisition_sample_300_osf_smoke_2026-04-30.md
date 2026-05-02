# Full Article Text Acquisition Pass

- Targets considered: 1
- Route attempt rows: 1
- Newly accepted full-article text objects: 1
- Rows with represented full article after pass: 137/300
- Paper/other represented rows with full article after pass: 136

## Accepted Rows

- `sr_4018aa63d523` -> `file_5034ec1ffe2d` via `osf_file_download`; `data/cache/full_article_text_acquisition/sample_300/sr_4018aa63d523__osf_file_download__10c6c6957365.pdf`

## Failure Profile

- `full_article_text_obtained`: 1

## Notes

- This pass accepts PDF, XML/JATS, or full-article HTML when the primary DOI/title identity gate passes.
- Repository and archive routes are treated as candidate generators. Landing pages and metadata-only hits stay in the candidate ledger and do not promote.
- CORE and BASE are not included here because CORE is currently rate-limiting/key-gated in this environment and BASE requires whitelisting.

## Output Files

- `data/derived/effect_inflation_dataset/schema_pilot/full_article_text_acquisition_attempts_sample_300_osf_smoke.tsv`
- `data/derived/effect_inflation_dataset/schema_pilot/full_article_text_acquisition_summary_sample_300_osf_smoke.tsv`
- `data/derived/effect_inflation_dataset/schema_pilot/source_object_candidate_codebook_sample_300.tsv`
- `data/derived/effect_inflation_dataset/schema_pilot/source_file_codebook_sample_300.tsv`
- `data/derived/effect_inflation_dataset/schema_pilot/source_result_codebook_sample_300.tsv`
