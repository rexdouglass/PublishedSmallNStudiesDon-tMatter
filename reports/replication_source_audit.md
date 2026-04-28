# Replication Source Audit

This report is a reconciliation pass across every current tracking surface, not just the harvest manifest.
The evidence inventory is intentionally non-lossy. The consolidated audit is alias-reconciled at the source-family level.

- Audit rows: **107**
- Evidence inventory rows: **346**

## Audit status counts

| Audit status | Rows |
|---|---:|
| catalog_integrated | 2 |
| catalog_not_integrated | 12 |
| integrated_live | 68 |
| raw_artifact_only | 1 |
| staged_only | 24 |

## Evidence surface counts

| Evidence kind | Rows |
|---|---:|
| live_pair_source | 89 |
| manifest_lead | 1 |
| promoted_file | 29 |
| queue_status | 1 |
| raw_lead_dir | 64 |
| source_catalog_row | 97 |
| staged_file | 65 |

## Normalized blocker codes

| Blocker code | Rows |
|---|---:|
| access_restriction | 1 |
| conversion_policy_missing | 6 |
| cross_check_only | 6 |
| metric_not_on_shared_d_axis | 13 |
| missing_machine_readable_pair_results | 5 |
| needs_primary_pdf_confirmation | 1 |
| original_side_missing | 4 |
| parser_not_implemented | 12 |
| roster_only | 1 |
| source_not_pair_buildable | 10 |

## Raw payload status codes

| Raw payload status | Rows |
|---|---:|
| downloaded_payload_present | 47 |
| landing_probe_only | 8 |

## Reconciled source families with blockers

| Canonical source | Audit status | Blocker codes | Linked datasets | Status explanation |
|---|---|---|---|---|
| EERP effectdata.py | catalog_not_integrated | cross_check_only | EERP effectdata.py | source catalog knows this source but it is not integrated in the current build |
| ML1 summary workbook | catalog_not_integrated | cross_check_only | ML1 summary workbook | source catalog knows this source but it is not integrated in the current build |
| ML4 public site results | catalog_not_integrated | cross_check_only | ML4 public site results | source catalog knows this source but it is not integrated in the current build |
| RPP converted | catalog_not_integrated | cross_check_only | RPP converted | source catalog knows this source but it is not integrated in the current build |
| ReplicationSuccess RProjects.rda | catalog_not_integrated | cross_check_only | ReplicationSuccess RProjects.rda | source catalog knows this source but it is not integrated in the current build |
| SSRP D3 | catalog_not_integrated | cross_check_only | SSRP D3 | source catalog knows this source but it is not integrated in the current build |
| Awesome replicability-data repository | integrated_live | original_side_missing | source_not_pair_buildable | Awesome lie-language paired raw csvs | Awesome mind-body paired raw csvs | Awesome replicability paired raw csvs | included in live build with 12 integrated pair rows; family also retains pre-promotion artifacts; other artifact notes: promotion_blocker=original_side_missing|source_not_pair_buildable |
| COVID online experiment replications | integrated_live | metric_not_on_shared_d_axis | COVID online experiments YCLS summaries | included in live build with 26 integrated pair rows; family also retains pre-promotion artifacts; other artifact notes: promotion_blocker=non_d_metric |
| Communication privacy replication corpus | integrated_live | conversion_policy_missing | Communication privacy SEM paths | Communication privacy SEM/spec-curve paths | included in live build with 31 integrated pair rows; family also retains pre-promotion artifacts; other artifact notes: promotion_blocker=effect_conversion_policy_missing |
| Contextual bias in verbal credibility assessment | integrated_live | parser_not_implemented | Contextual bias in verbal credibility (OSF raw) | included in live build with 6 integrated pair rows; family also retains pre-promotion artifacts; other artifact notes: promotion_blocker=parser_family_not_implemented |
| Deceptive intentions verbal credibility replication | integrated_live | parser_not_implemented | Deceptive intentions verbal credibility (OSF raw) | included in live build with 1 integrated pair rows; family also retains pre-promotion artifacts; other artifact notes: promotion_blocker=parser_family_not_implemented |
| Eyewitness memory distortion in ten countries | integrated_live | missing_machine_readable_pair_results | Eyewitness ten-country paper table rescue | included in live build with 5 integrated pair rows; family also retains pre-promotion artifacts; other artifact notes: promotion_blocker=missing_machine_readable_pair_results |
| Greed by SES replications | integrated_live | parser_not_implemented | Greed x SES meta-analysis script | included in live build with 1 integrated pair rows; family also retains pre-promotion artifacts; other artifact notes: promotion_blocker=parser_family_not_implemented |
| Linguistic frame effect on blame and liability | integrated_live | parser_not_implemented | Linguistic frame liability clean csvs | included in live build with 6 integrated pair rows; family also retains pre-promotion artifacts; other artifact notes: promotion_blocker=parser_family_not_implemented |
| PSA 002 object orientation | integrated_live | parser_not_implemented | PSA-002 object orientation lab rows | included in live build with 2 integrated pair rows; family also retains pre-promotion artifacts; other artifact notes: promotion_blocker=parser_family_not_implemented |
| PSA 004 JTB Turri | integrated_live | missing_machine_readable_pair_results | PSA 004 Turri article table rescue | included in live build with 1 integrated pair rows; family also retains pre-promotion artifacts; other artifact notes: promotion_blocker=replication_payload_missing|missing_machine_readable_pair_results |
| PSA 006 trolley Greene | integrated_live | conversion_policy_missing | PSA-006 trolley country rows | included in live build with 90 integrated pair rows; family also retains pre-promotion artifacts; other artifact notes: promotion_blocker=effect_conversion_policy_missing |
| Protzko 2023 NHB | integrated_live | parser_not_implemented | Protzko NHB asymmetry writeup | Protzko NHB labels writeup | Protzko NHB referrals writeup | included in live build with 3 integrated pair rows; family also retains pre-promotion artifacts; other artifact notes: parser_family_not_implemented |
| RRR Bouwmeester 2017 | integrated_live | parser_not_implemented | RRR Bouwmeester 2017 (manual) | RRR Bouwmeester 2017 site csvs | included in live build with 22 integrated pair rows; family also retains pre-promotion artifacts; other artifact notes: promotion_blocker=parser_family_not_implemented |
| RRR Cheung 2016 | integrated_live | parser_not_implemented | RRR Cheung 2016 site csvs | included in live build with 1 integrated pair rows; family also retains pre-promotion artifacts; other artifact notes: promotion_blocker=parser_family_not_implemented |
| RRR Elliott 2021 | integrated_live | parser_not_implemented | RRR Elliott 2021 aggregate table rows | included in live build with 3 integrated pair rows; family also retains pre-promotion artifacts; other artifact notes: promotion_blocker=parser_family_not_implemented |
| RRR McCarthy 2018 | integrated_live | parser_not_implemented | RRR McCarthy 2018 site csvs | included in live build with 2 integrated pair rows; family also retains pre-promotion artifacts; other artifact notes: promotion_blocker=parser_family_not_implemented |
| RRR Verschuere 2018 | integrated_live | parser_not_implemented | RRR Verschuere 2018 site csv | included in live build with 1 integrated pair rows; family also retains pre-promotion artifacts; other artifact notes: promotion_blocker=parser_family_not_implemented |
| Retrieval extinction fear conditioning in rats | integrated_live | parser_not_implemented | Retrieval-extinction rats xlsx | included in live build with 3 integrated pair rows; family also retains pre-promotion artifacts; other artifact notes: promotion_blocker=parser_family_not_implemented |
| Wood scaffolding direct replication | integrated_live | conversion_policy_missing | Wood scaffolding participant csv | included in live build with 2 integrated pair rows; family also retains pre-promotion artifacts; other artifact notes: promotion_blocker=effect_conversion_policy_missing |
| Ying 2023 pilot-full-scale trials | integrated_live | roster_only | Ying 2023 manual partial reconstruction | ying_2023_dissertation_pair_roster | included in live build with 5 integrated pair rows; family also retains pre-promotion artifacts; other artifact notes: promotion_decision=promote_live:3; promote_sensitivity:2; hold_stage_only:2; analytic_status=usable_d_pair:1; usable_binary_response_pair:1; usable_binary_event_pair:1; usable_mixed_smd_sensitivity:1; usable_ci_derived_smd_sensitivity:1; d_values_recovered_but_timepoint_model_caveat:1; native_log_hazard_ratio_pair:1 |
| Marcus Four Lab Replication Hcmv7 | raw_artifact_only |  |  | raw lead-harvest directory exists but no structured staged/promoted linkage was found |
| Angrist learning-curve replication corpus | staged_only | metric_not_on_shared_d_axis | source_not_pair_buildable |  | staged artifact exists but not promoted; blocker/status: promotion_blocker=metric_not_on_shared_d_axis|source_not_pair_buildable |
| Border 2019 candidate gene replication | staged_only | metric_not_on_shared_d_axis | needs_primary_pdf_confirmation |  | staged artifact exists but not promoted; blocker/status: promotion_blocker=metric_not_on_shared_d_axis|needs_primary_pdf_confirmation |
| Coppock 2019 generalizability corpus | staged_only |  |  | staged artifact exists but not promoted |
| EEF regrants systematic replication candidates | staged_only | source_not_pair_buildable |  | staged artifact exists but not promoted; blocker/status: promotion_blocker=source_not_pair_buildable |
| EGAP Metaketa I | staged_only | metric_not_on_shared_d_axis |  | staged artifact exists but not promoted; blocker/status: promotion_blocker=metric_not_on_shared_d_axis |
| EGAP Metaketa III | staged_only | metric_not_on_shared_d_axis | source_not_pair_buildable |  | staged artifact exists but not promoted; blocker/status: promotion_blocker=metric_not_on_shared_d_axis|source_not_pair_buildable |
| EGAP Metaketa IV | staged_only | metric_not_on_shared_d_axis | source_not_pair_buildable |  | staged artifact exists but not promoted; blocker/status: promotion_blocker=metric_not_on_shared_d_axis|source_not_pair_buildable |
| ERN Pe RRR OpenNeuro | staged_only | metric_not_on_shared_d_axis | original_side_missing |  | staged artifact exists but not promoted; blocker/status: promotion_blocker=metric_not_on_shared_d_axis|original_side_missing |
| IBL reproducible electrophysiology | staged_only | metric_not_on_shared_d_axis | source_not_pair_buildable |  | staged artifact exists but not promoted; blocker/status: promotion_blocker=metric_not_on_shared_d_axis|source_not_pair_buildable |
| IES systematic replication awards | staged_only | source_not_pair_buildable |  | staged artifact exists but not promoted; blocker/status: promotion_blocker=source_not_pair_buildable |
| Jaljuli Kafkafi multi lab rodent replication | staged_only | conversion_policy_missing |  | staged artifact exists but not promoted; blocker/status: promotion_blocker=effect_conversion_policy_missing |
| Kerschbaumer 2020 rheumatology phase II/III | staged_only |  | Kerschbaumer 2020 rheumatology phase II/III | staged artifact exists but not promoted |
| Li 2024 PD-1/PD-L1 phase II/III oncology | staged_only |  | Li 2024 PD-1/PD-L1 phase II/III oncology | staged artifact exists but not promoted; blocker/status: promotion_decision=stage_native_metric:51; analytic_status=native_one_arm_orr_not_randomized_treatment_contrast:51 |
| ManyBabies 3 | staged_only | missing_machine_readable_pair_results |  | staged artifact exists but not promoted; blocker/status: promotion_blocker=missing_machine_readable_pair_results |
| ManyClasses 2 | staged_only | metric_not_on_shared_d_axis | original_side_missing | source_not_pair_buildable |  | staged artifact exists but not promoted; blocker/status: promotion_blocker=original_side_missing|metric_not_on_shared_d_axis|source_not_pair_buildable |
| Media priming direct replication | staged_only | access_restriction | missing_machine_readable_pair_results |  | staged artifact exists but not promoted; blocker/status: promotion_blocker=access_restriction|missing_machine_readable_pair_results |
| Mullinix Leeper Druckman Freese 2015 | staged_only | metric_not_on_shared_d_axis |  | staged artifact exists but not promoted; blocker/status: promotion_blocker=metric_not_on_shared_d_axis |
| Musicianship EEG multi site replication | staged_only | metric_not_on_shared_d_axis | original_side_missing | source_not_pair_buildable |  | staged artifact exists but not promoted; blocker/status: promotion_blocker=original_side_missing|metric_not_on_shared_d_axis|source_not_pair_buildable |
| News discernment replication | staged_only | source_not_pair_buildable |  | staged artifact exists but not promoted; blocker/status: promotion_blocker=not_original_replication_pair_table |
| Nieuwland 2018 DeLong replication | staged_only | conversion_policy_missing |  | staged artifact exists but not promoted; blocker/status: promotion_blocker=effect_conversion_policy_missing |
| Self control neuroimaging replication | staged_only | metric_not_on_shared_d_axis | missing_machine_readable_pair_results |  | staged artifact exists but not promoted; blocker/status: promotion_blocker=missing_machine_readable_pair_results|metric_not_on_shared_d_axis |
| Strategy situation fit replication | staged_only | conversion_policy_missing |  | staged artifact exists but not promoted; blocker/status: promotion_blocker=effect_conversion_policy_missing |
| Wils 2023 IBD phase II/III | staged_only |  | Wils 2023 IBD phase II/III | staged artifact exists but not promoted; blocker/status: promotion_decision=stage_native_metric:37; analytic_status=native_treatment_arm_response_rate_not_treatment_contrast:37 |
| Wood and Porter elusive backfire effect | staged_only | metric_not_on_shared_d_axis |  | staged artifact exists but not promoted; blocker/status: promotion_blocker=metric_not_on_shared_d_axis |

## Raw-only leads

| Canonical source | Raw payload status | Landing status codes | Raw provider hints | Status explanation |
|---|---|---|---|---|
| Marcus Four Lab Replication Hcmv7 | downloaded_payload_present |  |  | raw lead-harvest directory exists but no structured staged/promoted linkage was found |

## Top worklist items

| Priority | Canonical source | Next step | Rationale |
|---:|---|---|---|
| 90 | Marcus Four Lab Replication Hcmv7 | stage_downloaded_payload | Public files appear downloaded but have not been staged into a structured source artifact. |
| 85 | Ying 2023 pilot-full-scale trials | complete_partial_manual_reconstruction | Source family is already live but still has unresolved manual reconstruction work. |
| 70 | Border 2019 candidate gene replication | consider_native_metric_lane | Source is real but blocked by the current shared-D policy. |
| 70 | EGAP Metaketa I | consider_native_metric_lane | Source is real but blocked by the current shared-D policy. |
| 70 | ERN Pe RRR OpenNeuro | consider_native_metric_lane | Source is real but blocked by the current shared-D policy. |
| 70 | Mullinix Leeper Druckman Freese 2015 | consider_native_metric_lane | Source is real but blocked by the current shared-D policy. |
| 70 | Wood and Porter elusive backfire effect | consider_native_metric_lane | Source is real but blocked by the current shared-D policy. |
| 55 | ManyBabies 3 | locate_machine_readable_payload | The checked public materials do not currently expose a machine-readable pair-results payload. |
| 55 | Self control neuroimaging replication | locate_machine_readable_payload | The checked public materials do not currently expose a machine-readable pair-results payload. |
| 45 | Media priming direct replication | resolve_access_block | The source appears relevant but the needed payload is restricted or failed with an access error. |