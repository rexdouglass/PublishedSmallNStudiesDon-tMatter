# Figure 1 Search Lead Review Summary: Codex Batch 001

This is an intermediate review product for the Figure 1 corpus/database search cue. It records Codex triage decisions for the first 20 ambiguous leads and points to the receipt file for each decision.

The decisions below do not directly edit `CORPORA_AND_DATABASES.tsv`. They create per-lead receipt targets under `steps/review_cue/figure1_search_leads/receipts/` so future queue builds can skip already-reviewed items and downstream scripts can route accepted items explicitly.

## Queue State After Applying This Batch

- Reviewed in this batch: 20
- Open review items after applying receipts: 210
- Rebuilt queue skip counts: `already_root_candidate=117`, `deterministically_skipped=7`, `already_in_root_target=4`, `already_reviewed=20`

## Decision Counts

| Decision | Count | Interpretation |
| --- | ---: | --- |
| `keep_in_corpora_and_databases` | 1 | Advances as a root corpus/database candidate. |
| `route_to_individual_replication_paper_worklist` | 1 | Does not belong in the corpus/database table as such, but is itself a replication lead that may become an individual Figure 1 pair. |
| `route_to_result_table_worklist` | 2 | Does not create a new corpus/database row, but may support extraction from an already-cataloged source family. |
| `keep_as_context_source` | 8 | Useful context or later-figure source, but does not advance to Figure 1 pair intake now. |
| `reject_irrelevant` | 8 | Stop for this route/lead. |

## Advances

| Lead | Decision | Confidence | Why it advances | Receipt |
| --- | --- | --- | --- | --- |
| Reproducibility Project Psychology: Design | `keep_in_corpora_and_databases` | high | Real RPP OSF project/source-family lead. Keep in the root corpus/database inventory, then file-inventory it for pair tables or crosswalks. | `receipts/keep_in_corpora_and_databases/title_reproducibility_project_psychology_design.json` |
| Stroop Replication Study Dataset | `route_to_individual_replication_paper_worklist` | medium | Single replication dataset. Low-priority individual pair candidate if original and replication D/N can be reconstructed. | `receipts/route_to_individual_replication_paper_worklist/title_stroop_replication_study_dataset.json` |
| `0_Master.do` | `route_to_result_table_worklist` | high | Local master Stata script for an already-cataloged political-science source family. Useful for file-level provenance, not a new root corpus row. | `receipts/route_to_result_table_worklist/title_0_master.json` |
| `3-replication-package_ufvur.zip` | `route_to_result_table_worklist` | high | Local Zenodo replication package already tied to an existing political-science source family. Useful artifact-level support, not a new root corpus row. | `receipts/route_to_result_table_worklist/title_3_replication_package_ufvur.json` |

## Stops Or Context Only

| Lead | Decision | Confidence | Why it does not advance to Figure 1 pair intake now | Receipt |
| --- | --- | --- | --- | --- |
| AEA RCT Registry | `keep_as_context_source` | high | Real registry/database, useful for preregistration and denominator work, but this lead does not expose Figure 1 original/replication pair rows. | `receipts/keep_as_context_source/title_aea_rct_registry.json` |
| Barnett/Wren biomedical CI scrape through BEAR | `keep_as_context_source` | high | Background comparator unless N can be recovered. Not a Figure 1 original/replication pair corpus. | `receipts/keep_as_context_source/title_barnett_wren_biomedical_ci_scrape_through_bear.json` |
| BEAR combined database | `keep_as_context_source` | high | Useful comparator/search index, but most rows are registry, review, replication, scrape, or meta-analysis objects rather than direct Figure 1 pair rows. | `receipts/keep_as_context_source/title_bear_combined_database.json` |
| Direct replications in the era of open sampling | `keep_as_context_source` | high | OSF metadata describes a discussion/methods project about directness in open sampling, not a row-level replication-pair corpus. | `receipts/keep_as_context_source/title_direct_replications_in_the_era_of_open_sampling.json` |
| Lancee et al. 2017 antipsychotic outcome reporting audit | `keep_as_context_source` | high | Registry-vs-publication discrepancy audit, not a D/N source and not a Figure 1 replication-pair corpus. | `receipts/keep_as_context_source/title_lancee_et_al_2017_antipsychotic_outcome_reporting_audit.json` |
| Leight/Asri/Imai AEA publication tracking paper | `keep_as_context_source` | high | Conceptually useful publication-tracking work, but no row-level output data were found and it is not a Figure 1 original/replication pair source. | `receipts/keep_as_context_source/title_leight_asri_imai_aea_publication_tracking_paper.json` |
| Nordic trial reporting dataset | `keep_as_context_source` | high | Good publication-status scaffold, but no effect sizes and no assessment of registered primary outcome reporting. Not a Figure 1 pair corpus. | `receipts/keep_as_context_source/title_nordic_trial_reporting_dataset.json` |
| SIPS 2017 sample size and effect size workshop | `keep_as_context_source` | high | Workshop materials, slides, examples, and R code. Not a replication-pair corpus or source table. | `receipts/keep_as_context_source/title_sips_2017_sample_size_and_effect_size_workshop.json` |
| Brodeur economics through BEAR | `reject_irrelevant` | high | BEAR version lacks sample size, and a separate raw Brodeur Dataverse/OpenICPSR file is the better route if needed. | `receipts/reject_irrelevant/title_brodeur_economics_through_bear.json` |
| Combining specific task-oriented training with manual therapy to improve balance and mobility in patients after stroke | `reject_irrelevant` | high | Single pilot RCT package with no explicit replication corpus, database, or original-to-replication mapping. Do not advance on speculation that a later trial might exist. | `receipts/reject_irrelevant/title_combining_specific_task_oriented_training_with_manual_therapy_to_improve_balance_and_mobility_in_patients_after_stroke_a.json` |
| Headspace for parents: a pilot randomised controlled trial | `reject_irrelevant` | high | Single pilot RCT lead with no affirmative evidence that it is itself a replication/reproduction/follow-up of an identifiable original. | `receipts/reject_irrelevant/title_headspace_for_parents_a_pilot_randomised_controlled_trial.json` |
| Older Brodeur Methods Matter OpenICPSR file | `reject_irrelevant` | high | Duplicate/stale route to the same recovered package. No further OpenICPSR chase unless a separate sample-size-bearing file exists. | `receipts/reject_irrelevant/title_older_brodeur_methods_matter_openicpsr_file.json` |
| Replication Document Term and Feature Matrices | `reject_irrelevant` | high | Dataverse record is term/feature matrices for text analysis, not original/replication D/N pair rows. | `receipts/reject_irrelevant/title_replication_document_term_and_feature_matrices.json` |
| Stanford Data | `reject_irrelevant` | high | Computational replication package for automated nonparametric content analysis, not a Figure 1 original/replication pair source. | `receipts/reject_irrelevant/title_stanford_data.json` |
| WP1 XP2a Book of N white replication open question | `reject_irrelevant` | high | Preregistered open-question analysis for a specific study. Not a replication-pair corpus and not a likely D/N source. | `receipts/reject_irrelevant/title_wp1_xp2a_book_of_n_white_replication_open_question.json` |
| `2KLNFX` | `reject_irrelevant` | high | Single-paper computational replication package. The word replication here is not the Figure 1 original/replication-pair meaning. | `receipts/reject_irrelevant/title_2klnfx.json` |

## Audit Files

- Decision JSON: `steps/review_cue/figure1_search_leads/reviewcue-decisions-figure1_search_leads-codex-batch001.json`
- Receipt root: `steps/review_cue/figure1_search_leads/receipts/`
- Routing TSV: `steps/review_cue/figure1_search_leads/reviewcue-routing-table-figure1_search_leads.tsv`
- Routing JSON: `steps/review_cue/figure1_search_leads/reviewcue-routing-table-figure1_search_leads.json`
- Rebuilt queue: `steps/review_cue/figure1_search_leads/reviewcue-queue-figure1_search_leads.json`
- Cue index: `steps/review_cue/figure1_search_leads/reviewcue-index-figure1_search_leads.md`
