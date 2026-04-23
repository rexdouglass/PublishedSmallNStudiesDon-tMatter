# Replication Pair Source Catalog

This catalog records every source pulled in the latest replication-pair sweep, including overlap files and near-hits.

| Project | Source dataset | Classification | Integrated | File rows | Usable pair rows | Notes |
|---|---|---|---:|---:|---:|---|
| Multi-project | I4R public workbook | inspected public workbook / not yet pair-buildable for D-vs-N | no | 6719 | 0 | Public workbook is real and current, but the estimate-level sheet is a robustness-check coefficient/SE table rather than a standardized effect-size pair table. |
| Multi-project | FReD filtered pair table | harmonized effect-level pair table | yes | 2164 | 843 | Build keeps only FReD rows whose original and replication effect types can be converted to the common D-like axis, while excluding obvious legacy-overlap prefixes and rows that look like secondary-data, syntax/output, reanalysis, or other non-new-sample replications. |
| Registered Replication Reports | Vaidis 2024 prepared data subset | participant-level direct replication converted to per-lab pair rows | yes | 4898 | 1 | Public prepared-data CSV is filtered with the project analysis-script exclusions and converted into one HC-CE vs LC-CE Cohen's d row per lab, anchored to the original Croyle & Cooper (1983) effect. |
| Registered Replication Reports | Stoevenbelt 2025 combined lab csv | participant-level direct replication converted to per-lab pair rows | yes | 1709 | 1 | Public combined participant CSV is filtered with the registered exclusion logic, converted into women-only stereotype-threat versus low-threat control Cohen's d rows per lab, and anchored to the original Johns, Schmader, & Martens (2005) effect reported in the public preprint. |
| Sports science replications | Sports science supplemental outcomes table | public supplemental pair table joined to public sample-size workbook | yes | 25 | 19 | Build joins the public reported-effect supplemental table to the public sample-size workbook and retains only rows with numeric original and replication effect values; partial eta squared is converted onto the common D-like axis and standardized-mean-difference variants are preserved on that scale. |
| Multi-project | Appendix D supplemental | canonical hand-built pair table / floor source | yes | 555 | 555 | Used as a floor source for undercovered project families in the Figure 2 rule and plotted subsets. |
| Multi-project | Manual paper-grounded pairs | manual primary-source recovery | yes | 26 | 26 | Manual rows grounded to fetched supplements, stable DOI targets, local project records, or downloaded papers where the automated project tables still missed the appendix-aligned pair. |
| OSC 2015 | RPP converted | direct pair table | no | 168 | 0 | Legacy converted workbook retained as a local schema cross-check; build now uses the canonical raw CSV instead. |
| OSC 2015 | RPP canonical OSF csv | overlap / schema-variant mirror | yes | 168 | 96 | Canonical raw CSV; build now reads the `T_r..O.`/`T_r..R.` and `T_N..O.`/`T_N..R.` columns directly. |
| OSC 2015 | RPP jtLeek mirror | overlap / archival mirror | no | 168 | 0 | Archival mirror of the canonical OSF CSV. |
| SSRP | ReplicationSuccess SSRP.rda | direct pair table | yes | 21 | 21 | Full 21-row SSRP object with original and replication r, Fisher-z, p-values, and Ns. |
| SSRP | SSRP D3 | project-specific CSV / cross-check | no | 21 | 0 | Public SSRP CSV retained as a cross-check against the packaged 21-row harmonized object. |
| SSRP | SSRP D6 beliefs | auxiliary / beliefs only | no | 21 | 0 | Prediction-market / beliefs sidecar, not a pair table. |
| EERP / EPRP / RPP / SSRP | ReplicationSuccess RProjects.rda | overlap / harmonized cross-check | no | 143 | 0 | Contains 18 EERP, 31 EPRP, 73 psychology, 21 social-science rows; retained as cross-check. |
| Many Labs 1 | Altmejd harmonized Many Labs 1 | harmonized aggregated pair table | yes | 16 | 10 | Used because the ML1 summary workbook does not expose a clean original-N row for every effect. |
| Many Labs 1 | ML1 summary workbook | pair-buildable / cross-check | no | 26 | 0 | Pulled and inspected; strong cross-check for aggregated ES, but not used as the direct pair table. |
| Many Labs 2 | Many Labs 2 public join | project-specific joined pair table | yes | 28 | 28 | Built from public replication summary plus original-effects files. |
| Many Labs 3 | Altmejd harmonized Many Labs 3 | harmonized aggregated pair table | yes | 10 | 10 | Used because the ML3 manuscript tables expose ES cleanly but not a ready original-N row structure. |
| Many Labs 3 | ML3 manuscript tables bundle | pair-buildable / cross-check | no | 10 | 0 | Pulled txt/pdf/xlsx/zip bundle and verified the project-level effect table. |
| Many Labs 4 | ML4 public site results | replication-side near-hit | no | 17 | 0 | Site-level replication results and meta objects are public; original-side pair row still needs a clean source. |
| Many Labs 5 | Many Labs 5 overarching analyses | direct pair-buildable | yes | 20 | 20 | Build uses `ML5FigureData.csv` for ES and the single-effects file for version-specific Ns; adds ML5 RP:P and ML5 Revised arrows. |
| EPRP | EPRP complete data | direct pair table | yes | 40 | 34 | Direct project CSV; effect sizes are parsed directly or recovered from numeric analysis strings. |
| EERP | ReplicationSuccess RProjects.rda | harmonized project-specific pair table | yes | 18 | 18 | Uses the Experimental Economics subset of the harmonized 143-row RProjects object. |
| EERP | EERP effectdata.py | project-specific code route / cross-check | no | 18 | 0 | Parsed and verified locally; retained as a cross-check on the EERP subset from RProjects. |
| EERP | EERP marketdata.zip | auxiliary market / survey data | no | 6 | 0 | Public zip is real but carries market/survey side data, not a richer pair table. |
| RPCB | RPCB | direct effect-level pair table | yes | 188 | 118 | Still the canonical local effect-level replication file. |
| SCORE | SCORE analyst join | direct version-of-record claim join | yes | 309 | 282 | Built from `orig_outcomes.csv` joined to version-of-record rows in `repli_outcomes.csv`; reproduces the 282-row appendix-style join exactly. |
| Decision-Market Replication Project | Decision-market pair table | direct pair table | yes | 41 | 26 | Uses the harmonized public decision-market replication table with original and replication d and N columns. |
| LOOPR | LOOPR coding workbook | direct pair-buildable workbook | yes | 121 | 118 | Integrated from the public coding workbook using outcome-level Fisher-z columns first, then bounded numeric effect fallbacks. |
| Student Replication Projects | Boyce student replication corpus | direct pair corpus | yes | 176 | 114 | Current integration is conservative: only rows with explicit `target_d_calc`, `rep_d_calc`, and both sample sizes are used. |
| 251 Rescue Projects | 251 Rescue parsed data | direct triplet-derived pair table | yes | 57 | 30 | Built from parsed and combined rescue files, then de-duplicated against exact Boyce overlap keys before integration. |
| Clinical highly cited replications | Clinical published replication workbook | direct pair workbook | yes | 10 | 7 | Limited to rows with convertible `OR`, `RR`, or `HR` outcomes plus both original and replication sample sizes. |
| Brazilian Reproducibility Initiative | BRI primary t experiment table | generated project-specific experiment table | yes | 45 | 45 | Built from the public BRI repo plus locally generated primary-analysis output; excludes `ALT*` sensitivity variants and preserves the project-native experiment effect metric (`ROM`/`MD`). |
| Pipeline Project | Pipeline supplement + packet data | direct project supplement plus packet-level cross-check | yes | 10 | 10 | Nine rows are converted from supplement-reported key-test statistics; Intuitive Economics uses the packet CSV to recover the replication-side correlation directly. |
| Multi-project | PooledMarketR PM_data.Rdata | overlap / market metadata | no | 111 | 0 | Outcome / market / survey metadata for EERP, ML2, RPP, and SSRP; not a richer pair table. |
| Registered Replication Reports | Alogna 2014 table 1 site counts | harvest-promoted pair table | yes | 1 | 1 | Auto-discovered promoted harvested lead source. |
| Other direct replications | Awesome lie-language paired raw csvs | harvest-promoted pair table | yes | 1 | 1 | Auto-discovered promoted harvested lead source. |
| Other direct replications | Awesome mind-body paired raw csvs | harvest-promoted pair table | yes | 2 | 2 | Auto-discovered promoted harvested lead source. |
| Other direct replications | Awesome replicability paired raw csvs | harvest-promoted pair table | yes | 9 | 9 | Auto-discovered promoted harvested lead source. |
| Other direct replications | COVID online experiments YCLS summaries | harvest-promoted pair table | yes | 26 | 26 | Auto-discovered promoted harvested lead source. |
| Other direct replications | Communication privacy SEM paths | harvest-promoted pair table | yes | 30 | 30 | Auto-discovered promoted harvested lead source. |
| Other direct replications | Communication privacy SEM/spec-curve paths | harvest-promoted pair table | yes | 1 | 1 | Auto-discovered promoted harvested lead source. |
| Other direct replications | Contextual bias in verbal credibility (OSF raw) | harvest-promoted pair table | yes | 6 | 6 | Auto-discovered promoted harvested lead source. |
| Other direct replications | Deceptive intentions verbal credibility (OSF raw) | harvest-promoted pair table | yes | 1 | 1 | Auto-discovered promoted harvested lead source. |
| Other direct replications | Doyen et al. 2012 article (manual) | harvest-promoted pair table | yes | 1 | 1 | Auto-discovered promoted harvested lead source. |
| EERP | EERP 2016 supplement (manual) | harvest-promoted pair table | yes | 7 | 7 | Auto-discovered promoted harvested lead source. |
| Other direct replications | EQIPD stagewise open-field lab contrasts | harvest-promoted pair table | yes | 7 | 7 | Auto-discovered promoted harvested lead source. |
| Registered Replication Reports | Eerland 2016 Intention_attribution.csv | harvest-promoted pair table | yes | 1 | 1 | Auto-discovered promoted harvested lead source. |
| Registered Replication Reports | Eerland 2016 Intentionality.csv | harvest-promoted pair table | yes | 1 | 1 | Auto-discovered promoted harvested lead source. |
| Registered Replication Reports | Eerland 2016 imagery.csv | harvest-promoted pair table | yes | 1 | 1 | Auto-discovered promoted harvested lead source. |
| Other direct replications | Galak et al. 2012 psi meta-analysis (manual) | harvest-promoted pair table | yes | 1 | 1 | Auto-discovered promoted harvested lead source. |
| Other direct replications | Greed x SES meta-analysis script | harvest-promoted pair table | yes | 1 | 1 | Auto-discovered promoted harvested lead source. |
| Registered Replication Reports | Hagger 2016 RTV.csv | harvest-promoted pair table | yes | 1 | 1 | Auto-discovered promoted harvested lead source. |
| Other direct replications | Linguistic frame liability clean csvs | harvest-promoted pair table | yes | 6 | 6 | Auto-discovered promoted harvested lead source. |
| Management Science Replication Project | MSRP Chen et al. 2013 report table | harvest-promoted pair table | yes | 3 | 3 | Auto-discovered promoted harvested lead source. |
| Management Science Replication Project | MSRP Croson and Donohue 2006 report | harvest-promoted pair table | yes | 1 | 1 | Auto-discovered promoted harvested lead source. |
| Management Science Replication Project | MSRP Engelbrecht-Wiggans & Katok 2008 report table | harvest-promoted pair table | yes | 4 | 4 | Auto-discovered promoted harvested lead source. |
| Management Science Replication Project | MSRP Ho & Zhang 2008 report table | harvest-promoted pair table | yes | 2 | 2 | Auto-discovered promoted harvested lead source. |
| Management Science Replication Project | MSRP Kremer & Debo 2016 report table | harvest-promoted pair table | yes | 2 | 2 | Auto-discovered promoted harvested lead source. |
| Management Science Replication Project | MSRP Schweitzer & Cachon 2000 report | harvest-promoted pair table | yes | 2 | 2 | Auto-discovered promoted harvested lead source. |
| Management Science Replication Project | MSRP Shunko et al. 2018 report table | harvest-promoted pair table | yes | 2 | 2 | Auto-discovered promoted harvested lead source. |
| Many Labs 4 | Many Labs 4 local meta-analysis (manual) | harvest-promoted pair table | yes | 1 | 1 | Auto-discovered promoted harvested lead source. |
| Marek 2022 BWAS | Marek 2022 BWAS paper (manual) | harvest-promoted pair table | yes | 1 | 1 | Auto-discovered promoted harvested lead source. |
| Registered Replication Reports | O'Donnell 2018 site-level meta csvs | harvest-promoted pair table | yes | 1 | 1 | Auto-discovered promoted harvested lead source. |
| Other direct replications | Online image credibility README equivalence table | harvest-promoted pair table | yes | 11 | 11 | Auto-discovered promoted harvested lead source. |
| Other direct replications | PSA-002 object orientation lab rows | harvest-promoted pair table | yes | 2 | 2 | Auto-discovered promoted harvested lead source. |
| Other direct replications | PSA-006 trolley country rows | harvest-promoted pair table | yes | 90 | 90 | Auto-discovered promoted harvested lead source. |
| Other direct replications | Protzko NHB asymmetry writeup | harvest-promoted pair table | yes | 1 | 1 | Auto-discovered promoted harvested lead source. |
| Other direct replications | Protzko NHB labels writeup | harvest-promoted pair table | yes | 1 | 1 | Auto-discovered promoted harvested lead source. |
| Other direct replications | Protzko NHB referrals writeup | harvest-promoted pair table | yes | 1 | 1 | Auto-discovered promoted harvested lead source. |
| OSC 2015 | RPP project record alias (manual) | harvest-promoted pair table | yes | 4 | 4 | Auto-discovered promoted harvested lead source. |
| Registered Replication Reports | RRR Alogna 2014 (manual) | harvest-promoted pair table | yes | 2 | 2 | Auto-discovered promoted harvested lead source. |
| Registered Replication Reports | RRR Bouwmeester 2017 (manual) | harvest-promoted pair table | yes | 1 | 1 | Auto-discovered promoted harvested lead source. |
| Registered Replication Reports | RRR Bouwmeester 2017 site csvs | harvest-promoted pair table | yes | 21 | 21 | Auto-discovered promoted harvested lead source. |
| Registered Replication Reports | RRR Cheung 2016 site csvs | harvest-promoted pair table | yes | 1 | 1 | Auto-discovered promoted harvested lead source. |
| Registered Replication Reports | RRR Elliott 2021 aggregate table rows | harvest-promoted pair table | yes | 3 | 3 | Auto-discovered promoted harvested lead source. |
| Registered Replication Reports | RRR Hagger 2016 (manual) | harvest-promoted pair table | yes | 1 | 1 | Auto-discovered promoted harvested lead source. |
| Registered Replication Reports | RRR McCarthy 2018 site csvs | harvest-promoted pair table | yes | 2 | 2 | Auto-discovered promoted harvested lead source. |
| Registered Replication Reports | RRR Verschuere 2018 site csv | harvest-promoted pair table | yes | 1 | 1 | Auto-discovered promoted harvested lead source. |
| Other direct replications | Ranehill 2015 power posing (manual) | harvest-promoted pair table | yes | 1 | 1 | Auto-discovered promoted harvested lead source. |
| OSC 2015 | ReplicationSuccess SSRP alias (manual) | harvest-promoted pair table | yes | 3 | 3 | Auto-discovered promoted harvested lead source. |
| Other direct replications | Retrieval-extinction rats xlsx | harvest-promoted pair table | yes | 3 | 3 | Auto-discovered promoted harvested lead source. |
| SSRP | SSRP 2018 supplement (manual) | harvest-promoted pair table | yes | 2 | 2 | Auto-discovered promoted harvested lead source. |
| Registered Replication Reports | Srull-Wyer RRR paper (manual) | harvest-promoted pair table | yes | 1 | 1 | Auto-discovered promoted harvested lead source. |
| Other direct replications | Transparent Psi Project combined raw | harvest-promoted pair table | yes | 1 | 1 | Auto-discovered promoted harvested lead source. |
| Registered Replication Reports | Wagenmakers 2016 site csv | harvest-promoted pair table | yes | 1 | 1 | Auto-discovered promoted harvested lead source. |
| Other direct replications | Wood scaffolding participant csv | harvest-promoted pair table | yes | 2 | 2 | Auto-discovered promoted harvested lead source. |