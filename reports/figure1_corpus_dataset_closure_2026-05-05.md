# Figure 1 Corpus/Dataset Closure Pass - 2026-05-05

## Bottom Line

This pass closes the remaining corpus/dataset-level mining tasks before moving to individual-paper extraction. It promoted 0 new strict Figure 1 rows. The current locally observable state remains 1679 strict Figure 1A rows, 752 D/N rows blocked by current gates, 88 D-equivalent clinical/binary diagnostic rows, 91 native-effect diagnostic rows, 248 roster-only rows without public values, and 172 effect-present rows missing public N.

The remaining work is not bulk corpus mining. It is either provenance hardening for rows already represented, source-owner/user-file acquisition for request-only datasets, or individual source-object extraction.

## Closure Summary

| Closure bucket | Decision | Records reviewed | Strict included | Strict blocked | D-equivalent | Native | Roster/coverage | Effect no N | Duplicate risk | False positives | Promoted here |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| already_represented | closed_no_new_corpus_rows | 91 | 28 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| already_represented_or_current_rule_blocked | closed_no_new_corpus_rows | 923 | 379 | 228 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| alternate_subplot_staged | closed_staged_for_figure1b_not_figure1a | 88 | 0 | 0 | 88 | 0 | 0 | 0 | 0 | 0 | 0 |
| alternate_subplot_staged | closed_staged_for_native_panel_not_figure1a | 91 | 0 | 0 | 0 | 91 | 0 | 0 | 0 | 0 | 0 |
| blocked_access_route | closed_until_archived_sheet_or_user_file | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| duplicate_risk_or_support_only | closed_no_bulk_promotion | 431 | 1 | 0 | 0 | 0 | 0 | 0 | 10 | 0 | 0 |
| effect_present_n_missing | closed_missing_public_n_columns | 172 | 0 | 0 | 0 | 0 | 0 | 172 | 0 | 0 | 0 |
| false_positive_context_table | closed_parser_false_positive | 271 | 4 | 86 | 0 | 0 | 0 | 0 | 0 | 271 | 0 |
| missing_original_benchmark | closed_until_original_benchmark_table_found | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| no_obvious_complete_dn_columns | closed_no_bulk_rows | 65 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 56 | 0 |
| no_public_value_table | closed_until_public_or_user_supplied_data | 248 | 5 | 0 | 0 | 0 | 248 | 0 | 0 | 0 | 0 |

## Corpus Decisions

| Corpus/dataset | Decision | Key counts | Why closed | Next step |
| --- | --- | --- | --- | --- |
| Reproducibility Project: Cancer Biology / raw_corpus:rpcb | closed_no_new_corpus_rows | root=118; included=33; blocked=85; D*=0; native=0; roster=0; effect-no-N=0; duplicate-risk=0; false-positive=0 | Local RPCB effect-level bytes were parsed (381 native rows with effect/N/pair context; 294 strict side rows with copied effect and N). The current D/N table already carries 118 RPCB pairs; 33 pass the current strict rule and 85 are blocked by N gates. The remaining raw assertions are missing SMD/N on at least one side, duplicate aliases, or source-support material for provenance hardening. | none_for_corpus_mining; resume source_result/source_result_support hardening later |
| Many Labs 2 | closed_no_new_corpus_rows | root=28; included=28; blocked=0; D*=0; native=0; roster=0; effect-no-N=0; duplicate-risk=0; false-positive=0 | The ML2 public join yields 28 D/N pairs, all 28 passing the current rule. Strict side output contains 56 original/replication side assertions. The larger 91-row masterkey includes metadata/original-effect rows not all used by the Figure 1 pair join. | none_for_corpus_mining |
| PSA-006 trolley | closed_parser_false_positive | root=90; included=4; blocked=86; D*=0; native=0; roster=0; effect-no-N=0; duplicate-risk=0; false-positive=271 | The 271-row table flagged in raw viability is trolley_infosheet.csv, an author/contribution/context table. It has no effect/N evidence. The actual PSA-006 country-level result rows are already represented separately in the root table. | none_for_corpus_mining |
| FORRT Replications and Reversals | closed_no_bulk_promotion | root=1; included=1; blocked=0; D*=0; native=0; roster=0; effect-no-N=0; duplicate-risk=10; false-positive=0 | The conservative HTML scan found 10 D/N-looking entries and 8 with larger replication N. One source-object-backed row is already in the root table; the remaining entries are narrative/aggregate assertions with high duplication risk against FReD/current rows. | none; any remaining FORRT entries require individual source-object extraction, not corpus mining |
| Comparative clinical/binary rows | closed_staged_for_figure1b_not_figure1a | root=0; included=0; blocked=0; D*=88; native=0; roster=0; effect-no-N=0; duplicate-risk=0; false-positive=0 | Rows with comparative binary counts can be expressed as D-equivalent using the documented log(OR)*sqrt(3)/pi route. They remain separate from strict Figure 1A because they are conversion-tier rows rather than direct D/SMD rows. | none_for_corpus_mining; use Figure 1B/diagnostic route if plotted |
| Native response-rate rows | closed_staged_for_native_panel_not_figure1a | root=0; included=0; blocked=0; D*=0; native=91; roster=0; effect-no-N=0; duplicate-risk=0; false-positive=0 | Native response-rate rows have N on both sides but no defensible treatment-effect D conversion under the current rule. They are retained for a native-scale diagnostic or denominator accounting, not promoted to Figure 1A. | none_for_corpus_mining |
| Ying/Ehrhardt pilot-to-full-scale clinical datasets | closed_until_public_or_user_supplied_data | root=5; included=5; blocked=0; D*=0; native=0; roster=248; effect-no-N=0; duplicate-risk=0; false-positive=0 | Public local bytes identify the pilot/full-scale family and pair roster scale, but the row-level effect/N dataset is not publicly mirrored here. Research triage decision: not_promoted_request_or_access_only. | none; request-only data is out of scope unless the user supplies files |
| RCT-DUPLICATE RWE emulations | closed_missing_public_n_columns | root=0; included=0; blocked=0; D*=0; native=0; roster=0; effect-no-N=172; duplicate-risk=0; false-positive=0 | Public CSVs expose trial/result effect strings and covariates but not clean original RCT or RWE-emulation sample-size columns. Research triage decision: not_promoted_no_public_n_columns. | none; needs N recovery from restricted/source-specific materials before any row can plot |
| RGB pilot-vs-larger-trial health-behavior family | closed_until_public_or_user_supplied_data | root=0; included=0; blocked=0; D*=0; native=0; roster=0; effect-no-N=0; duplicate-risk=0; false-positive=0 | Article/preprint pages confirm relevant pilot/larger-trial pair and effect-count claims, but no public master workbook/CSV with D/N rows was obtained. Research triage decision: not_promoted_no_public_master_table_mirrored. | none; request/source-owner acquisition only |
| Hagen Cumulative Science Project I | closed_until_archived_sheet_or_user_file | root=0; included=0; blocked=0; D*=0; native=0; roster=0; effect-no-N=0; duplicate-risk=0; false-positive=0 | The public code/app route was mirrored, but the Google Sheet backing data route is deleted/gone and only a codebook is accessible. Local status: blocked_access_route. | none; needs archived backing sheet or maintainer-provided data |
| Many Smiles Collaboration | closed_until_original_benchmark_table_found | root=0; included=0; blocked=0; D*=0; native=0; roster=0; effect-no-N=0; duplicate-risk=0; false-positive=0 | Mirrored replication-side data do not expose a clean original benchmark effect plus original N table. Local status: not_promoted_requires_original_benchmark_choice. | none; needs a source-object with original benchmark D and N before plotting |
| SCORE | closed_no_new_corpus_rows | root=282; included=171; blocked=111; D*=0; native=0; roster=0; effect-no-N=0; duplicate-risk=0; false-positive=0 | The source family is already represented in the current root pair table. Remaining local artifact review is provenance/source-object hardening or rule-blocked accounting, not a new corpus mining step. | none_for_corpus_mining |
| Sports Science Replication Centre | closed_no_new_corpus_rows | root=19; included=16; blocked=3; D*=0; native=0; roster=0; effect-no-N=0; duplicate-risk=0; false-positive=0 | The source family is already represented in the current root pair table. Remaining local artifact review is provenance/source-object hardening or rule-blocked accounting, not a new corpus mining step. | none_for_corpus_mining |
| LOOPR | closed_no_new_corpus_rows | root=118; included=104; blocked=14; D*=0; native=0; roster=0; effect-no-N=0; duplicate-risk=0; false-positive=0 | The source family is already represented in the current root pair table. Remaining local artifact review is provenance/source-object hardening or rule-blocked accounting, not a new corpus mining step. | none_for_corpus_mining |
| Many Labs 5 | closed_no_new_corpus_rows | root=20; included=20; blocked=0; D*=0; native=0; roster=0; effect-no-N=0; duplicate-risk=0; false-positive=0 | The source family is already represented in the current root pair table. Remaining local artifact review is provenance/source-object hardening or rule-blocked accounting, not a new corpus mining step. | none_for_corpus_mining |
| Coppock/COVID online generalizability corpus | closed_no_new_corpus_rows | root=50; included=35; blocked=15; D*=0; native=0; roster=0; effect-no-N=0; duplicate-risk=0; false-positive=0 | The source family is already represented in the current root pair table. Remaining local artifact review is provenance/source-object hardening or rule-blocked accounting, not a new corpus mining step. | none_for_corpus_mining |
| Previously staged one-row source leads | closed_no_bulk_rows | root=0; included=0; blocked=0; D*=0; native=0; roster=0; effect-no-N=0; duplicate-risk=0; false-positive=56 | The staged-unpromoted scan reviewed 65 staged lead files; 56 unpromoted leads had no obvious complete D/N columns. Any further value extraction is individual-paper/source-specific. | none_for_corpus_mining |

## Generated Artifacts

- `steps/corpus_results/figure1/corpus_closure/figure1-corpus-dataset-closure-actions.tsv`
- `steps/corpus_results/figure1/corpus_closure/figure1-corpus-dataset-closure-summary.tsv`
- `reports/figure1_corpus_dataset_closure_2026-05-05.md`

This report is an audit projection only. It does not alter `FIGURE1_REPLICATION_PAIRS.tsv`, `source_result.tsv`, or any canonical result table.
