# Figure 1 GPT Candidate Pair Mining Summary

Date: 2026-05-04

## Result

Mined two net-new GPT candidate corpora into the generic promoted-pairs pipeline:

| Project | Promoted rows | Rows passing current Figure 1 D/N rule | Main mirrored source |
|---|---:|---:|---|
| Experimental asset-market replications | 14 | 14 | `data/raw/replication_projects/lead_harvest/gpt_many_replication_candidates_20260504/asset_market_replications/abbd67d08a8a__q79e2.bin` |
| Sensory-marketing replications | 38 | 38 | `data/raw/replication_projects/lead_harvest/gpt_many_replication_candidates_20260504/sensory_marketing_replications/ddde4c11a7d9__full.html` |

The Figure 1 root table now has 2,306 rows, with 1,600 included by the current D/N rule. Before this mining pass, the same count was 2,254 rows, with 1,548 included, so the net addition is 52 included rows.

## Files

- Miner script: `scripts/promote_gpt_candidate_asset_sensory_pairs.py`
- Audit/support TSV: `steps/corpus_results/figure1/gpt_candidate_pair_mining/gpt_candidate_asset_sensory_pair_mining.tsv`
- Generated promoted CSVs, ignored by git but rerunnable from the script:
  - `data/derived/replication_pairs/harvest/promoted/asset_market_replications__promoted_pairs.csv`
  - `data/derived/replication_pairs/harvest/promoted/sensory_marketing_replications__promoted_pairs.csv`
- Updated root table: `FIGURE1_REPLICATION_PAIRS.tsv`

## Notes

Asset-market rows use 14 original-significant hypothesis tests from the appendix tables. AOL, KLS, and CDP rows report Cohen's d directly. EF rows report replication correlation and relative effect size, so the script infers original correlation as `replication / relative_effect_size` and maps both correlations to the D axis as `abs(2*r/sqrt(1-r^2))`.

Sensory-marketing rows use article Table 5 original/replication correlations, mapped to the D axis with `abs(2*r/sqrt(1-r^2))`. Original N comes from article Table 1 sample-size or statistic text. Replication N comes from row counts in the mirrored OSF analysis workbooks.

Both new projects still show `numeric_only_needs_verbatim_support` in the root table. The audit TSV preserves verbatim effect and N text, but these rows have not yet been promoted into the stricter `source_result` / `source_result_support` schema.
