# Figure 1 GPT Candidate Batch 2 Mining Summary

Generated on 2026-05-04.

## Definitions

- **Promoted pair row**: a candidate result row written to `data/derived/replication_pairs/harvest/promoted/` so the Figure 1 D/N pipeline can ingest it.
- **Current Figure 1 D/N rule**: both sides have numeric D and N, both N values are at least 10, and the replication/follow-up N is larger than the original N.
- **Mirrored source**: source bytes were downloaded under `data/raw/` and can be rehydrated by script instead of relying on a browser tab.

## Outcome

| Candidate | Mining decision | Promoted rows | Rows passing current Figure 1 D/N rule | Notes |
|---|---:|---:|---:|---|
| REPEAT Initiative | promoted_to_result_table | 106 | 60 | Primary HR/OR/RR/rate-ratio rows from Supplementary Data 6 were converted with `abs(log(ratio) * sqrt(3) / pi)` and labeled as same-data real-world-evidence reproductions. |
| Hagen Cumulative Science Project I | blocked_access_route | 0 | 0 | GitHub Shiny app is mirrorable, but the referenced Google Sheet backing data returned deleted/gone in this environment. |
| Many Smiles Collaboration | mirrored_context_not_promoted | 0 | 0 | OSF data zip and Nature article are mirrored, but this pass did not find a defensible original benchmark effect plus original N table in the mirrored files. |

## Resulting Root Counts

- `FIGURE1_REPLICATION_PAIRS.tsv` rows: 2,412
- Rows included by the current Figure 1 D/N rule: 1,660
- Delta from the previous root build in this mining pass: +106 root rows, +60 included rows

## Key Artifacts

- Promoter script: `scripts/promote_gpt_candidate_batch2_pairs.py`
- Mirror script with batch-two source routes: `scripts/mirror_figure1_gpt_many_replication_candidates.py`
- REPEAT promoted pair CSV: `data/derived/replication_pairs/harvest/promoted/repeat_rwe_reproductions__promoted_pairs.csv`
- Batch-two audit TSV: `steps/corpus_results/figure1/gpt_candidate_pair_mining/gpt_candidate_batch2_pair_mining.tsv`
- Batch-two mining status TSV: `steps/corpus_results/figure1/gpt_candidate_pair_mining/gpt_candidate_batch2_mining_status.tsv`
- Mirror status ledger: `steps/source_inventory/figure1/gpt_many_replication_candidates_20260504/mirror-status.tsv`

## Working URLs Recorded

- REPEAT OSF project: `https://osf.io/my5gn/`
- REPEAT Supplementary Data 6 zip: `https://osf.io/download/w64jq/`
- REPEAT Nature article: `https://www.nature.com/articles/s41467-022-32310-3`
- Hagen GitHub archive: `https://github.com/pandorica-opens/Hagen-Cumulative-Science-Project-I/archive/refs/heads/master.zip`
- Hagen OSF landing page: `https://osf.io/d7za8/`
- Many Smiles OSF data zip: `https://osf.io/download/qd2s3/`
- Many Smiles Nature article: `https://www.nature.com/articles/s41562-022-01458-9`

## Blocked URLs Recorded

- Hagen Shiny data Google Sheet: `https://docs.google.com/spreadsheets/d/1VBnEGbanAt5yLXkpMGRGJWZeuw1TLNVudksgXyksHq0/edit?ts=5beae9fc#gid=0` returned HTTP 410.
- Many Smiles project site: `https://manysmilescollaboration.com/` failed DNS resolution in this environment; the OSF and Nature routes worked.
