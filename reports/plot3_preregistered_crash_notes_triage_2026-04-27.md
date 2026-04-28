# Plot 3 Preregistered Evidence Crash-Notes Triage

Date: 2026-04-27

> Superseded status note: this triage has now been executed into the generated source catalog. The current strict layer is 172 rows, including ManyBabies 1 Bilingual, and the new rescue queues are in `plot3_scheel_quote_stat_rescue_candidates.csv`, `plot3_vandenakker_first_stat_candidates.csv`, and `plot3_rpcb_preclinical_paper_level_candidates.csv`.

These notes reconcile the crashed research output against the current repo state. The main correction is that the notes mix strict rows, native-metric sidecars, already-consumed replication evidence, and large rescue queues. I did not treat any new row as strict without a verified focal selector, D-like effect, and analytic N.

## Full-Memo Corrections

The later full memo is directionally useful, but several `promote_now` labels should be read as `download_and_parse_now`, not `append_now`.

| Memo claim | Local check | Current decision |
| --- | --- | --- |
| SCORE `g5sny` is a turnkey focal-claim D/N CSV | Downloaded `analysis data and code package 15 Dec 2025 1708.zip`; it contains `analyst data.RData`, not a simple `effect_size_original`/`n_original` CSV. The RData has 825 original-outcome rows across 306 papers and 427 replication-outcome rows. A naive direct `orig_conv_r` plus effective-N filter is sparse, so the rescue requires the same metric-specific parser/join work as the existing SCORE pipeline. | High-priority rescue queue, not blind append. |
| SCORE master `dtzx4` can promote the remaining 214 immediately | Local flat files confirm effect-size, effective-N, and preregistration-indicator information, but they are split across claim-level and paper-level tables. | Keep the existing 31 strict-ish paper-level rows; rescue the rest only after claim-paper-prereg joins are audited. |
| RPCB can enter strict Plot 3 directly | Local RPCB effect-level CSV has D/N-rich Registered Report replication effects, but the same evidence is already used in Plot 1 RPCB replication pairs. | Stage separately or add a preclinical/preregistered-replication lane; do not silently append to the main strict Plot 3 layer. |
| EGAP Metaketa I/III/IV are direct D rows | Local Metaketa I table verifies native adjusted ATEs, not standardized D. Metaketa III/IV staged files are native field-experiment estimate packages. | Strong native/PAP sidecar; promote only if source SMDs or a defensible ATE-to-D policy are extracted and documented. |
| PSA-CR002 Loss-Gain Framing, Dorison 2022 | Dorison 2022 is the PSA-CR001 Affective Science source already represented by four pooled rows. The current PSA-CR002 addition is Wang et al. cognitive reappraisal with 12 preregistered hypothesis rows. | Treat the memo label as a source-identity conflict; no row change. |
| ManyClasses 1 N is about 38,000 student-assignments | Current strict row uses the paper-level participating-student N = 2,081 and the pooled Delta-z estimate. | No row change without a principled choice to use observations/assignments rather than participants. |

## Already Handled In Strict Plot 3

| Source | Current repo status | Note |
| --- | ---: | --- |
| ManyBabies 1 | included, 1 row | Pooled IDS-vs-ADS row already added with reported d = 0.35 and N = 2,329. |
| ManyClasses 1 | included, 1 row | Pooled immediate-vs-delayed-feedback row already added with Delta-z = 0.002 and N = 2,081. |
| PSA-CR002 | included, 12 rows | Current repo uses the article's 12 preregistered hypothesis rows, not the crash note's "4 outcomes" shorthand. |
| Scheel et al. 2021 | included, 32 of 71 rows | The missing 39 remain a manual PDF/supplement extraction queue. |
| Schafer/Schwarz 2019 | included, 89 of 93 preregistered rows | The missing 4 remain a small ambiguity/manual-extraction queue. |
| SCORE/COS | included, 31 of 245 preregistration-indicated paper IDs | The remaining 214 are not bulk-promoted because SCORE effect-size, effective-N, and preregistration flags are split across claim and paper levels. |

## New Or Clarified Staged Sources

| Source | Crash-note claim | Repo interpretation |
| --- | --- | --- |
| van den Akker selective hypothesis reporting | 459-study preregistered psychology sample, possibly 150-300 usable rows | Separate from the 193-study preregistration-in-practice sample. Local `Data SHR.xlsx` audit shows 484 PSP IDs, 446 included PSP IDs, 5,723 filled preregistered-hypothesis cells among included PSP IDs, and 3,342 matched-publication cells. It is a high-yield rescue queue, not a strict D/N table yet. |
| EGAP Metaketa I | gold-standard PAP field experiments | Local table verifies pooled vote-choice ATE = 0.003, SE = 0.010, observations = 25,820. This is native ATE evidence, not a source-provided standardized D row. |
| EGAP Metaketa III | 30 native field-experiment rows | Local staged package exists with site-estimate payloads. Keep native metric/staged. |
| EGAP Metaketa IV | 36 native field-experiment rows | Local staged package exists with study/meta estimate RDS outputs. Keep native metric/staged. |
| RPCB | 17-158 preregistered confirmatory effects | Local effect-level table has 188 rows, 159 replication SMD effects with replication N, and 135 original SMD effects. These are eLife Registered Report replication effects, but they already serve Plot 1 RPCB evidence and are not independent strict Plot 3 rows. |
| Allen and Mehler 2019 | 113 Registered Reports | Public article/supporting data count support/null outcomes for RR hypotheses. Useful RR universe evidence, but no row-level D/N payload. |

## Additional Full-Memo Queues Not Yet Added To The Main Catalog

These are reasonable future work items, but they still require source downloads and manual effect/N extraction before the strict gate can be applied.

| Queue | Working interpretation |
| --- | --- |
| Toth et al. 2021 management preregistration corpus | Potential first-hypothesis-per-paper rescue source; needs supplementary download, DOI deduplication, and D/N extraction. |
| Heirene et al. 2024 gambling preregistration corpus | Small domain-specific rescue queue; needs article-level D/N extraction. |
| Claesen et al. 2021 preregistration-adherence corpus | Likely overlaps heavily with Schafer/Schwarz; process only after DOI dedupe. |
| Ofosu and Posner PAP corpus | PAP/focal-selector candidate in political science; effect sizes are not in the meta-research CSV and require paper extraction. |
| NIHR HTA, clinical Registered Reports, RIAT, COVID platform trials | Plausible clinical SAP/protocol-locked manual extraction queues; should go to a clinical side file/domain first. |
| ManyBabies 1 Bilingual, ManyBabies 2, PSA002 | Big-team/RR-style row rescues, but each needs final source effect/N verification before strict append. |

## Clinical And Registry Notes

The clinical crash note is useful as a boundary condition, not an ingestion source. The current conclusion stands: no compact public dataset was found that pairs SAP-locked primary outcomes with arm-level effect sizes and analytic N at scale. NIHR HTA monographs, COVID adaptive platform trials, clinical Registered Reports, and RIAT reanalyses are plausible manual extraction queues, but they are not a strict Plot 3 bulk source in the current repo.

ClinicalTrials.gov/AACT, CliniFact, and COMPare remain documented as sidecars or blocked sources because they provide registry/outcome structure or publication linkages without proving exact analytic preregistration plus D/N on the shared axis.

## Immediate Extraction Priorities

1. Scheel missing 39: highest confidence because the row selector is already accepted.
2. SCORE missing 214: highest potential among already-included families, but needs claim-paper-prereg mapping and D/N joins.
3. van den Akker selective hypothesis reporting: largest psychology rescue queue, but needs focal-hypothesis selection, statistic parsing, N recovery, and DOI deduplication.
4. Schafer/Schwarz missing 4: small manual cleanup queue.
5. RPCB: only if a separate preregistered-replication side lane is created; do not silently add to strict Plot 3.
6. EGAP Metaketa I/III/IV: only if a native field-experiment lane or a defensible ATE-to-D policy is added.

## Source URLs

- ManyBabies 1: https://manybabies.org/MB1/
- ManyClasses 1: https://www.manyclasses.org/projects/many-classes-1/
- PSA-CR002: https://psysciacc.org/projects/cr002.html
- SCORE/COS Nature dataset repository: https://doi.org/10.17605/OSF.IO/G5SNY
- SCORE/COS local source hub previously used: https://osf.io/dtzx4/
- van den Akker selective hypothesis reporting paper: https://doi.org/10.1177/25152459231187988
- van den Akker preregistration-in-practice OSF project: https://osf.io/pqnvr/
- EGAP Metaketa I: https://github.com/egap/metaketa-i
- EGAP Metaketa III: https://osf.io/knje7/
- EGAP Metaketa IV: https://osf.io/tzy82/
- RPCB final data: https://osf.io/e5nvr/
- Allen and Mehler 2019: https://doi.org/10.1371/journal.pbio.3000246
