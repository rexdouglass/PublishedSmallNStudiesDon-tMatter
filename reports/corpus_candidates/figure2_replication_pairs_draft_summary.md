# Draft Figure 2 Summary

- All on-hand source-recovered pair rows with usable original and replication D/N: **2,130**
- Source-recovered Figure 2 subset before Appendix D backfill: **1,445**
- Figure 2 subset after Appendix D backfill: **1,451**
- Source-recovered plotted subset before Appendix D backfill: **1,445**
- Plotted subset after Appendix D backfill: **1,451**
- Appendix D rows added to the rule subset: **6**
- Appendix D rows added to the plotted subset: **6**
- Projects represented in the plotted subset: **31**

## All usable pairs by project

- FReD other additions: **504**
- SCORE: **282**
- Other direct replications: **205**
- RPCB: **118**
- LOOPR: **118**
- Student Replication Projects: **114**
- OSC 2015: **103**
- FReD CORE: **85**
- FReD SoSci submissions: **84**
- FReD OpenMKT: **82**
- FReD CurateScience: **74**
- Brazilian Reproducibility Initiative: **45**
- Registered Replication Reports: **42**
- EPRP: **34**
- 251 Rescue Projects: **30**
- Many Labs 2: **28**
- Decision-Market Replication Project: **26**
- EERP: **25**
- SSRP: **23**
- Many Labs 5: **20**
- Sports science replications: **19**
- Management Science Replication Project: **16**
- FReD FORRT: **11**
- Pipeline Project: **10**
- Many Labs 1: **10**
- Many Labs 3: **10**
- Clinical highly cited replications: **7**
- FReD new RRR: **3**
- Marek 2022 BWAS: **1**
- Many Labs 4: **1**

## Rule-qualified subset by project

- FReD other additions: **378**
- SCORE: **171**
- LOOPR: **104**
- FReD CORE: **82**
- FReD OpenMKT: **80**
- Other direct replications: **80**
- OSC 2015: **71**
- FReD CurateScience: **70**
- FReD SoSci submissions: **61**
- Student Replication Projects: **35**
- RPCB: **33**
- Many Labs 2: **28**
- EPRP: **28**
- Decision-Market Replication Project: **26**
- Brazilian Reproducibility Initiative: **21**
- Registered Replication Reports: **21**
- Many Labs 5: **20**
- SSRP: **20**
- EERP: **18**
- 251 Rescue Projects: **17**
- Sports science replications: **16**
- Management Science Replication Project: **14**
- Many Labs 1: **13**
- FReD FORRT: **11**
- Many Labs 3: **10**
- Pipeline Project: **10**
- Clinical highly cited replications: **7**
- FReD new RRR: **3**
- DellaVigna-Linos 2022: **1**
- Marek 2022 BWAS: **1**
- Many Labs 4: **1**

## Plotted subset by project

- FReD other additions: **378**
- SCORE: **171**
- LOOPR: **104**
- FReD CORE: **82**
- FReD OpenMKT: **80**
- Other direct replications: **80**
- OSC 2015: **71**
- FReD CurateScience: **70**
- FReD SoSci submissions: **61**
- Student Replication Projects: **35**
- RPCB: **33**
- Many Labs 2: **28**
- EPRP: **28**
- Decision-Market Replication Project: **26**
- Brazilian Reproducibility Initiative: **21**
- Registered Replication Reports: **21**
- Many Labs 5: **20**
- SSRP: **20**
- EERP: **18**
- 251 Rescue Projects: **17**
- Sports science replications: **16**
- Management Science Replication Project: **14**
- Many Labs 1: **13**
- FReD FORRT: **11**
- Many Labs 3: **10**
- Pipeline Project: **10**
- Clinical highly cited replications: **7**
- FReD new RRR: **3**
- DellaVigna-Linos 2022: **1**
- Marek 2022 BWAS: **1**
- Many Labs 4: **1**

## Rule-Qualified Arrow Categories

- shrunk, still significant: **569**
- shrunk below p < .05: **613**
- grew: **269**

## Pair Origins In The Plotted Subset

- source_recovered: **1,445**
- appendix_backfill: **6**

## Notes

- This draft now uses source-recovered rows for OSC 2015, SSRP, Many Labs 1-5, EPRP, EERP, RPCB, SCORE, the Pipeline Project, the Decision-Market Replication Project, LOOPR, the Boyce student-replication corpus, the de-duplicated 251 Rescue rows, and the clinical highly cited-replication workbook, plus a manual paper-grounded tail for the remaining unresolved appendix aliases.
- Vaidis et al. 2024 now contributes per-lab rows for the HC-CE vs LC-CE induced-compliance contrast, anchored to the original Croyle & Cooper (1983) effect and replacing the pooled FReD row for that replication.
- Stoevenbelt et al. 2025 now contributes one women-only stereotype-threat-versus-control effect-size row per lab, reconstructed from the public combined participant CSV and anchored to the original Johns, Schmader, & Martens (2005) contrast reported in the public preprint.
- The sports-science replication corpus now contributes study-level original-versus-replication pairs recovered from the public supplemental outcomes table joined to the public sample-size workbook; only rows with numeric original and replication effect values are retained.
- FReD now contributes only rows whose original and replication effect metrics can be converted defensibly onto the common `D` axis, after excluding obvious legacy-overlap prefixes plus rows that read as secondary-data, syntax/output, reanalysis, or otherwise non-new-sample replications.
- The currently pulled I4R Meta Database workbook is intentionally left out of the Figure 2 build path because the public workbook is dominated by computational-reproduction and robustness-check coefficient/SE tables rather than new-sample direct-replication effect-size pairs.
- EERP is now built from the `Experimental Economics` subset of `ReplicationSuccess::RProjects`, with `effectdata.py` retained as a local cross-check.
- SSRP is now built from the full `ReplicationSuccess::SSRP` object, with the public project CSV retained as a cross-check.
- EPRP rows fall back to test-statistic parsing when the effect-size field is blank but the analysis string is numeric enough to recover D.
- ML1 and ML3 are integrated from the public Altmejd harmonized file because the project summary tables do not expose a ready one-row original-N structure.
- ML5 contributes two new replication arrows per original: `ML5 RP:P` and `ML5 Revised`.
- Pipeline contributes 10 project-level rows recovered from the public supplement and packet files; nine use supplement-reported test statistics and Intuitive Economics uses the packet CSV to recover the replication correlation directly.
- SCORE contributes the version-of-record analyst join: `309` merged claim rows, `282` usable rows after requiring original and replication `N` plus converted `r` on both sides.
- The Decision-Market corpus adds the harmonized 26-row `data_to_use.csv` table directly from OSF.
- LOOPR is integrated conservatively from the public coding workbook using the outcome-level Fisher-z columns first and only falling back to bounded numeric effect estimates when the Fisher-z field is blank.
- The Boyce student-replication corpus currently uses only rows with explicit `target_d_calc` and `rep_d_calc`; raw-stat and `*_ES` fallbacks are not used unless they are already standardized and unambiguous.
- The 251 Rescue rows are merged from `parsed_data.csv` and `combined_data.csv` and then de-duplicated against exact Boyce overlap keys before entering the corpus.
- Clinical highly cited-replication rows are limited to `OR`, `RR`, and `HR` outcomes from the public workbook; `OR` is converted to a d-like scale and `RR`/`HR` are preserved as absolute log-ratio magnitudes.
- The Brazilian Reproducibility Initiative is integrated from the public primary-analysis experiment table generated from the public repo; it excludes `ALT*` sensitivity variants and preserves the project-native experiment effect metric (`ROM`/`MD`) rather than forcing a d conversion.
- The current all-pairs count is broader than the hand-built Appendix D table for some families, especially RPCB and ML5, so use the appendix coverage report for apples-to-apples comparison against `555`.
- The build now collapses obvious site-level repeats to one row per original-paper × replication-study × endpoint anchor, using summed replication `N` and an `N`-weighted replication `D`; it does not use within-paper medians.
- The Figure 2 rule keeps all recovered endpoint pairs with `N_replication > N_original` and `N >= 10` on both sides.
- Category statistics and legend percentages use the full rule-qualified larger-`N` subset (`N >= 10` on both sides), not just what is easy to see inside the plotting window.
- The plotted figure uses a visual window of `10 <= N <= 100k` and `0.02 <= D <= 5`; pairs outside that window are clipped to the nearest plot edge rather than dropped.
- Undercovered project families now preserve any recovered source rows first and use Appendix D only for the unresolved residual gap.
- Zero-effect rows are retained in the rule-qualified statistics and are shown at the lower plot boundary when they fall below the log-scale floor.