# Figure 1 Raw Viability Summary

Definitions:

- Corpus/source family: a reusable collection of replication or follow-up results, not just one paper.
- Artifact: a concrete file, archive member, repository object, manifest, or provider record under that source family.
- Mirror: a local copy or already-local raw file with a path recorded on disk.
- Native result row: one copied row from a source table before converting values to D/N.
- D/N: the later Figure 1 plotting fields; D is the standardized effect and N is the relevant sample size.

Checked 16 parent source-family keys, 1869 local/mirrored artifacts, and 199 newly downloaded artifacts.
The generic parser emitted 796 native rows; 421 of those rows currently have both effect text and N text.
2 parent keys currently pass the raw-data viability gate for Figure 1 mapping.

Status counts:

- `parsed_result_rows_with_effect_n_and_pair_context`: 2
- `alias_covered_by_parsed_result_parent`: 1
- `mirrored_high_priority_non_table_artifacts_need_custom_review`: 7
- `mirrored_lower_priority_artifacts_need_review`: 4
- `parsed_rows_but_no_effect_n_signal`: 1
- `mirrored_or_metadata_only_no_result_signal`: 1

Top parent keys by current viability:

| parent | status | native rows | effect+N rows | candidate tables | representative files |
| --- | --- | ---: | ---: | ---: | --- |
| `raw_corpus:rpcb` | `parsed_result_rows_with_effect_n_and_pair_context` | 434 | 381 | 2 | RP_CB Final Analysis - Effect level data.csv / RP_CB Final Analysis - Effect level data.csv / osf_06__RP_CB_Final_Analysis_-_Effect_level_data.csv / RP_CB Final Analysis - Experiment level data dictionary.csv / RP_CB Final Analysis - Experiment level data.csv / RP_CB Final Analysis - Experiment level data.csv / osf_05__RP_CB_Final_Analysis_-_Experiment_level_data.csv / ... +6 more |
| `many_labs_2 | doi:10.1177/2515245918810225` | `parsed_result_rows_with_effect_n_and_pair_context` | 91 | 40 | 1 | Data_Figure_NOweird_oriEffects.csv / ML2_OriginalEffects.csv / ML2_OrignalEffects_Masterkey.csv |
| `rpcb | doi:10.7554/eLife.71601` | `alias_covered_by_parsed_result_parent` | 0 | 0 | 0 | RP_CB Final Analysis - Effect level data.csv / RP_CB Final Analysis - Effect level data.csv / osf_06__RP_CB_Final_Analysis_-_Effect_level_data.csv / RP_CB Final Analysis - Experiment level data dictionary.csv / RP_CB Final Analysis - Experiment level data.csv / RP_CB Final Analysis - Experiment level data.csv / osf_05__RP_CB_Final_Analysis_-_Experiment_level_data.csv / ... +5 more |
| `raw_corpus:brodeur_star_wars_openicpsr` | `mirrored_high_priority_non_table_artifacts_need_custom_review` | 0 | 0 | 0 | aer_100_4.csv / aer_101_2.csv / aer_101_4.csv / aer_101_5.csv / aer_101_6.csv / ... +79 more |
| `score` | `mirrored_high_priority_non_table_artifacts_need_custom_review` | 0 | 0 | 0 | Analysis-ready Data__Correlations Paper__corr_ksu_bibliometric.csv / Analysis-ready Data__Correlations Paper__corr_multi100.csv / Analysis-ready Data__Replication and Reproduction Papers__paper_status_tracking.csv / Analysis-ready Data__Replication and Reproduction Papers__pr_outcomes.csv / Change Logs__changes_pr_data-form.csv / ... +41 more |
| `lead_harvest:covid_online_2021` | `mirrored_high_priority_non_table_artifacts_need_custom_review` | 0 | 0 | 0 | est_study_1.rds / est_study_10.rds / est_study_11.rds / est_study_12.rds / est_study_2.rds / ... +7 more |
| `raw_corpus:nakagawa_yang` | `mirrored_high_priority_non_table_artifacts_need_custom_review` | 0 | 0 | 0 | dat_processed_SMD.csv / dat_processed_Zr.csv / dat_processed_lnRR.csv / ft089.csv / ft143.csv / ... +3 more |
| `raw_corpus:political_science_unlock` | `mirrored_high_priority_non_table_artifacts_need_custom_review` | 0 | 0 | 0 | aea_trials.csv / experimental-analyses.Rds / master_sheet_input.tab / master_sheet_output.tab |
| `corpus_db_many_labs_5_overarching_analyses` | `mirrored_high_priority_non_table_artifacts_need_custom_review` | 0 | 0 | 0 | Summary Effect Sizes - Single Effects (including Orig and RPP).csv |
| `family::ying_2023_pilot_full_scale_trials` | `mirrored_high_priority_non_table_artifacts_need_custom_review` | 0 | 0 | 0 | ying_epmc_abstract_scan_first60.csv |
| `corpus_db_loopr_coding_workbook` | `mirrored_lower_priority_artifacts_need_review` | 0 | 0 | 0 |  |
| `corpus_db_sports_science_supplemental_outcomes_table` | `mirrored_lower_priority_artifacts_need_review` | 0 | 0 | 0 |  |
| `github:ying531/awesome-replicability-data` | `mirrored_lower_priority_artifacts_need_review` | 0 | 0 | 0 |  |
| `zenodo:15552808` | `mirrored_lower_priority_artifacts_need_review` | 0 | 0 | 0 |  |
| `lead_harvest:psa_006_trolley` | `parsed_rows_but_no_effect_n_signal` | 271 | 0 | 0 | trolley_infosheet.csv |
| `doi:10.31222/osf.io/8psw2` | `mirrored_or_metadata_only_no_result_signal` | 0 | 0 | 0 |  |

Parsed tables that should not be treated as Figure 1 result rows without repair:

- `lead_harvest:psa_006_trolley` / `trolley_infosheet.csv`: Rows parsed, but the copied fields do not contain effect and N evidence.
- `raw_corpus:rpcb` / `RP_CB Final Analysis - Paper level data.csv | osf_03__RP_CB_Final_Analysis_-_Paper_level_data.csv`: Rows parsed, but the copied fields do not contain effect and N evidence.

Outputs:

- `steps/corpus_results/figure1/figure1-raw-viability-summary.tsv`
- `steps/corpus_results/figure1/figure1-raw-viability-table-detail.tsv`
