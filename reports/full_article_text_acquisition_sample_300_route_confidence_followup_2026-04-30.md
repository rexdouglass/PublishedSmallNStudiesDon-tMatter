# Full Article Text Acquisition Pass

- Targets considered: 2
- Route attempt rows: 3
- Newly accepted full-article text objects: 2
- Rows with represented full article after pass: 136/300
- Paper/other represented rows with full article after pass: 135

## Accepted Rows

- `sr_f44201a1b8b4` -> `file_e2518b1cd79b` via `openaire_instance_url`; `data/cache/full_article_text_acquisition/sample_300/sr_f44201a1b8b4__openaire_instance_url__8d993848201c.pdf`
- `sr_80c5ee34e5f4` -> `file_ee69bc6db4da` via `openaire_instance_url`; `data/cache/full_article_text_acquisition/sample_300/sr_80c5ee34e5f4__openaire_instance_url__1817773e556c.pdf`

## Failure Profile

- `full_article_text_obtained`: 2
- `http_403_blocked`: 1

## Notes

- This pass accepts PDF, XML/JATS, or full-article HTML when the primary DOI/title identity gate passes.
- Repository and archive routes are treated as candidate generators. Landing pages and metadata-only hits stay in the candidate ledger and do not promote.
- CORE and BASE are not included here because CORE is currently rate-limiting/key-gated in this environment and BASE requires whitelisting.

## Output Files

- `data/derived/effect_inflation_dataset/schema_pilot/full_article_text_acquisition_attempts_sample_300_route_confidence_followup.tsv`
- `data/derived/effect_inflation_dataset/schema_pilot/full_article_text_acquisition_summary_sample_300_route_confidence_followup.tsv`
- `data/derived/effect_inflation_dataset/schema_pilot/source_object_candidate_codebook_sample_300.tsv`
- `data/derived/effect_inflation_dataset/schema_pilot/source_file_codebook_sample_300.tsv`
- `data/derived/effect_inflation_dataset/schema_pilot/source_result_codebook_sample_300.tsv`
