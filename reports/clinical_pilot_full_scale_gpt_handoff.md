# GPT Research Handoff: Pilot-to-Full-Scale Clinical Trial Pair Sources

Date: 2026-04-27

## Objective

We are trying to find more clinical sources like Ying 2023: a pilot, feasibility, preliminary, phase II, or otherwise small early clinical trial that later scaled into a larger definitive trial, phase III trial, full-scale RCT, or closely linked confirmatory study.

The output we need is not just a bibliography. We need row-ready or nearly row-ready original-vs-follow-up pairs for a D-vs-N plot:

- Pilot/original side: sample size and effect estimate, or enough raw statistics to compute an effect.
- Full-scale/follow-up side: sample size and effect estimate on the same outcome and contrast, or enough raw statistics to compute it.
- Same clinical question: same intervention, comparator, population class, and endpoint as closely as possible.
- Larger follow-up: full-scale N must be larger than pilot N.
- Minimum N: both sides need N >= 10.
- Metric: ideally Cohen's d / Hedges g, odds ratio, risk ratio, log hazard ratio, mean difference with SD/SE/CI, event counts, responder counts, or means/SDs. If not directly D, it must be convertible or worth staging in a native-metric lane.

We already have many generic clinical-trial corpora. What we do not have enough of is explicit pilot-to-definitive pair linkage with both effect/N sides.

## Current Plot Gate

A row is promotable to the current strict pairs plot if it has:

1. `N_original` and `N_replication`.
2. `D_original` and `D_replication`, or inputs for a documented conversion to the same D-like axis.
3. Follow-up/full-scale N larger than pilot/original N.
4. Both sample sizes at least 10.
5. A defensible match between the pilot and full-scale endpoint.
6. No double counting of nested rows unless explicitly allowed. For example, do not include both country-level rows and a pooled aggregate from the same replication unless the analysis treats them as separate non-independent panels.

Rows that have a real pair but only native metrics should be staged, not discarded. Examples: log hazard ratios, adjusted mean differences without SD, cluster-adjusted effects, survival outcomes, or one-arm objective response rates.

## Current Local Closeout

As of the local rebuild on 2026-04-27, the clinical pilot/full-scale queue has been taken as far as the available local files allow.

```text
strict/promoted clinical additions:
  Ying 2023 partial reconstruction: 5 promoted rows
  Kerschbaumer 2020 rheumatology ACR20: 41 promoted rows before endpoint/family aggregation

staged/native clinical sources:
  Kerschbaumer 2020 ACR20/50/70 source table: 205 staged rows
  Li 2024 PD-1/PD-L1 early-phase vs phase III ORR: 51 staged rows
  Wils 2023 IBD phase II vs phase III response/remission: 37 staged rows
  Ying 2023 partial reconstruction: 7 staged rows, including TAT and pediatric-depression native/sensitivity rows

current blocker class:
  no remaining known local PDF supplied by the user needs parsing
  no immediate browser URL remains from this queue
  remaining work requires author/contact access, restricted article tables, or a policy decision for native-metric rows
```

## What We Already Have for Ying 2023

Source family: `Ying 2023 pilot-full-scale trials`.

Local status:

- Audit status: `integrated_live`.
- Current Ying live contribution: 5 promoted rows.
- Roster size: 248 pilot-to-full-scale pairs.
- Main blocker: the dissertation gives citation-level pair linkage, not effect/N rows.

Important local files:

- `data/raw/YING-DISSERTATION-2023.pdf`
- `data/raw/replication_projects/ying_2023/YING-DISSERTATION-2023.txt`
- `data/raw/replication_projects/ying_2023/YING-DISSERTATION-2023.tsv`
- `data/derived/replication_pairs/harvest/staged/ying_2023_pair_roster__stage.csv`
- `data/derived/replication_pairs/harvest/staged/ying_2023_partial_reconstruction__stage.csv`
- `data/derived/replication_pairs/harvest/promoted/ying_2023_partial_reconstruction__promoted_pairs.csv`
- `data/raw/replication_projects/lead_harvest/ying_2023/epmc_abstracts/`

Useful scripts:

- `scripts/extract_ying_pair_roster.py`
- `scripts/ingest_ying_partial_reconstruction.py`

The Ying roster file has 248 rows and these fields:

```text
source_dataset
source_paper
pair_id
pair_number
pilot_citation_text
pilot_doi
full_scale_citation_text
full_scale_doi
start_page_num
stage_status
analytic_row_status
public_source_path
```

The first 60 Ying pairs already have cached Europe PMC abstract JSON under:

```text
data/raw/replication_projects/lead_harvest/ying_2023/epmc_abstracts/
```

The abstract scan gets us part of the way, but it usually misses arm denominators, SDs, or endpoint-compatible full-scale estimates.

## Ying Rows Already Promoted

### Ying pair 003: Lung screening positivity

Promoted row:

```text
pair_id: ying_2023_pair_003_screen_positivity
pilot DOI: 10.1016/j.lungcan.2004.06.007
full-scale DOI: 10.1056/NEJMoa1209120
pilot title: Final results of the Lung Screening Study, a randomized feasibility study of spiral CT versus Chest X-ray screening for lung cancer
full-scale title: Results of initial low-dose computed tomographic screening for lung cancer
outcome: initial screening positivity / detection yield for low-dose CT versus chest X-ray
N_pilot: 3318
N_full: 53439
D_pilot: 0.714
D_full: 0.729
status: promoted
important caveat: this is screening positivity/detection yield, not mortality benefit
```

### Ying pair 006: Adult ADHD CBT response

Promoted row:

```text
pair_id: ying_2023_pair_006_adhd_cbt
pilot DOI: 10.1016/j.brat.2004.07.001
full-scale DOI: 10.1001/jama.2010.1192
pilot title: Cognitive-behavioral therapy for ADHD in medication-treated adults with continued symptoms
full-scale title: Cognitive behavioral therapy vs relaxation with educational support for medication-treated adults with ADHD and persistent symptoms
outcome: adult ADHD symptom severity / clinical response
N_pilot: 31
N_full: 86
D_pilot: 1.1705355327869313
D_full: 0.8029978560265689
status: promoted
conversion: responder counts converted with Chinn log(OR) * sqrt(3) / pi
```

### Ying pair 010: Neutropenic diet infection

Promoted row:

```text
pair_id: ying_2023_pair_010_neutropenic_diet
pilot DOI: 10.1097/01.mph.0000210412.33630.fb
full-scale DOI: 10.1002/pbc.26711
pilot title: Feasibility and safety of a pilot randomized trial of infection rate: neutropenic diet versus standard food safety guidelines
full-scale title: A randomized trial of the effectiveness of the neutropenic diet versus food safety guidelines on infection rate in pediatric oncology patients
outcome: febrile neutropenia / neutropenic infection
N_pilot: 19
N_full: 150
D_pilot: 0.10051870707149112
D_full: 0.05379907252256151
status: promoted
conversion: event counts converted with Chinn log(OR) * sqrt(3) / pi
inputs: pilot ND 4/9 vs FSG 4/10; full-scale ND+FSG 27/77 vs FSG 24/73
important caveat: positive direction is harm/infection, so lower values mean less infection inflation on a benefit-positive axis
```

## Additional Ying Rows Promoted or Staged

These are the best immediate row-rescue targets still inside the known 248-pair roster.

### Ying pair 012: OTCH stroke care-home occupational therapy

```text
pair_id: ying_2023_pair_012_otch_barthel
pilot DOI: 10.1161/01.Str.0000237124.20596.92
full-scale DOI: 10.1136/bmj.h468
outcome: Barthel Index of Activities of Daily Living at 3 months
N_pilot: 118
N_full: 1042
status: promoted sensitivity row
what we verified locally: pilot PDF gives intervention n=63 and control n=55 randomized; Barthel change at 3 months among survivors was +0.6 SD 3.9, n=59 versus -0.9 SD 2.2, n=46. Full-scale BMJ/PMC Table 3 gives adjusted Barthel mean difference 0.19, 95% CI -0.33 to 0.70, table Ns 540/436, from 1042 randomized residents.
D_original: 0.456 using pilot change-score pooled SD
D_replication: 0.047 inferred from the adjusted mean-difference CI and table Ns
caveat: sensitivity-grade row because the replication D is model/CI-derived, not a clean arm-SD SMD
```

### Ying pair 014: Postpartum sleep intervention

```text
pair_id: ying_2023_pair_014_postpartum_sleep
pilot DOI: 10.1093/sleep/29.12.1609
full-scale DOI: 10.1136/bmj.f1164
outcome: maternal nocturnal sleep duration in early postpartum
N_pilot: 30
N_full: 246
status: promoted sensitivity row
what we verified locally: pilot PDF gives sleep intervention n=15 and control sleep-outcome n=14; maternal nocturnal sleep was 433 versus 376 minutes, mean difference +57 minutes, 95% CI +6 to +107. Full-scale BMJ/PMC gives complete-case sleep Ns of intervention n=110 and control n=105; adjusted MD +5.97 minutes, 95% CI -7.55 to +19.5.
D_original: 0.799 by CI-derived Hedges g
D_replication: 0.118 by CI-derived Hedges g
caveat: sensitivity-grade row because both D estimates are inferred from reported mean-difference CIs rather than arm-level SDs
```

### Ying pair 017: Tapas Acupressure Technique weight maintenance

```text
pair_id: ying_2023_pair_017_tat_weight_maintenance
pilot DOI: 10.1089/acm.2006.6237
full-scale DOI: 10.1186/1472-6882-12-19
outcome: weight-loss maintenance / weight regain
N_pilot: 92
N_full: 285
status: stage_native_metric
blocker: staged with D-compatible estimates, but not strict enough for the promoted D plot
what we verified locally: pilot PDF gives SDS n=31, TAT n=30, qigong n=31 randomized; 24-week Table 3 adjusted TAT-SDS difference -1.22 kg, SDE 0.71. The definitive trial paper reports the pilot contrast as 0.1 versus 1.2 kg regain, SD=2.3, Cohen's d=0.48. Full-scale paper gives TAT n=142 and social-support n=143, adjusted TAT-SS difference -1.24 kg with SE=0.74.
current staged values: native kg mean difference; D_original 0.48; D_replication about 0.198 if the adjusted model SE is treated as the between-arm SE
reason not promoted: pilot endpoint is 24 weeks while the full-scale primary endpoint is 12 months, and the replication D is model-SE-derived
```

### Ying pair 033: Pediatric depression relapse prevention

```text
pair_id: ying_2023_pair_033_pediatric_depression_relapse
pilot DOI: 10.1097/CHI.0b013e31818914a1
full-scale DOI: 10.1176/appi.ajp.2014.13111460
outcome: time to relapse during continuation treatment after response to fluoxetine
N_pilot: 46
N_full: 144
status: stage_native_metric
blocker: native log hazard-ratio pair, not D
what we know: PMC full texts expose Cox HRs. Pilot HR=8.80 for MM versus MM+CBT, abs(log HR)=2.175. Full-scale HR=0.313 for MM+CBT versus MM, abs(log HR)=1.162.
rescue request: only revisit for D-like conversion if relapse event counts/timepoint proportions become available; otherwise keep in a documented survival-metric lane
```

## Primary Request for GPT

Please find more sources that look like Ying 2023 or can expand Ying 2023.

Priority 1: rescue more rows from the existing Ying 248-pair roster.

Priority 2: find additional public rosters or datasets of pilot-to-definitive clinical trial pairs.

Priority 3: find adjacent small-early-trial-to-larger-later-evidence datasets where the linkage is explicit enough to construct pairs.

Do not spend much time on generic clinical-trial registries unless there is a pairing variable or a known dataset linking pilot trials to definitive trials.

## Inbound Research Update: 2026-04-27

The latest research pass found one strong non-Ying public source and several Ying row rescues. Treat this section as the current action queue.

### Parsed New Source: Kerschbaumer 2020 Rheumatology Phase II/III

```text
source_name: Kerschbaumer et al. 2020, Efficacy outcomes in phase 2 and phase 3 randomized controlled trials in rheumatology
source_type: supplement | article_table
landing_url: https://www.nature.com/articles/s41591-020-0833-4
direct_data_url_or_api: https://static-content.springer.com/esm/art%3A10.1038%2Fs41591-020-0833-4/MediaObjects/41591_2020_833_MOESM1_ESM.pdf
local_file: data/raw/replication_projects/pilot_full_scale_inbound/kerschbaumer_2020_natmed_supp.pdf
local_text: data/raw/replication_projects/pilot_full_scale_inbound/kerschbaumer_2020_natmed_supp.txt
access_status: public; downloaded locally
pair_definition: phase 2 and phase 3 randomized, double-blind trials of targeted DMARDs in rheumatoid arthritis and psoriatic arthritis, matched by regimen and timepoint
why_possible_candidate: Supplement tables S4 and S5 expose phase 2 N, phase 3 N, and ACR20/ACR50/ACR70 responder counts for matched regimens.
effect_fields_available: ACR20, ACR50, ACR70 responder counts and denominators
N_fields_available: phase 2 n and phase 3 n
D_axis_promotable: yes, for active-vs-placebo/control binary ACR20 response rows using Chinn log(OR) * sqrt(3) / pi
local_parser: scripts/parse_kerschbaumer_2020_rheumatology.py
stage_output: data/derived/replication_pairs/harvest/staged/kerschbaumer_2020_rheumatology_phase2_phase3__stage.csv
promoted_output: data/derived/replication_pairs/harvest/promoted/kerschbaumer_2020_rheumatology_phase2_phase3_acr20__promoted_pairs.csv
stage_rows_written: 205
promoted_rows_written: 41
current_plot_rows_after_generic_endpoint_aggregation: 32
current_status: parsed locally; ACR20 active-vs-placebo/control rows promoted; ACR50/ACR70 and unmatched native response-rate rows staged only
```

This is the strongest new source because it has explicit numerator/denominator data rather than only narrative comparisons. It is now parsed locally. The text extraction confirms the key table rule:

```text
Table S4: Studies investigating rheumatoid arthritis patients included as well as outcomes used in the analyses. Endpoints were matched based on the same regimen and the same timepoint.
```

Example confirmed rows in the extracted text:

```text
Abatacept 10mg/kg + MTX:
phase 2 n=115, phase 3 n=156
ACR20: 69/115 vs 104/156
ACR50: 42/115 vs 63/156
ACR70: 19/115 vs 32/156

Adalimumab 40 mg q2w + MTX:
phase 2 n=67, phase 3 n=207
ACR20: 45/67 vs 131/207
ACR50: 37/67 vs 81/207
ACR70: 18/67 vs 43/207
```

Implemented parser policy:

- Promoted ACR20 only to avoid tripling non-independent ACR20/50/70 rows.
- Kept ACR50/ACR70 in the staged file.
- Positive direction is response benefit.
- Promoted only active-vs-placebo/control rows where a matched placebo/control row was available in both phase 2 and phase 3.
- Computed active-vs-placebo/control odds ratios within each phase and converted each to Chinn d.
- Preserved regimen/study keys and family keys in the staged file for later de-duplication or non-independence handling.

### Other New Source Leads from Inbound Research

These are worth keeping, but they are behind Kerschbaumer in priority.

```text
source_name: Li et al. 2024 PD-1/PD-L1 early-phase versus phase III oncology pairs
landing_url: https://jitc.bmj.com/content/12/1/e007959
direct_data_url_or_api: https://jitc.bmj.com/content/jitc/12/1/e007959/DC3/embed/inline-supplementary-material-3.pdf?download=true
local_file: data/raw/replication_projects/pilot_full_scale_inbound/li_2024_pd1_pdl1/inline-supplementary-material-3.pdf
access_status: public in browser; user-supplied PDF downloaded locally
row_count_claimed: 51 matched early-phase/phase III pairs
row_count_verified: 51 parsed rows
likely_metric: ORR native lane
local_parser: scripts/parse_li_2024_pd1_pdl1_phase_pairs.py
stage_output: data/derived/replication_pairs/harvest/staged/li_2024_pd1_pdl1_phase2_phase3_orr__stage.csv
stage_rows_written: 51
current_status: parsed locally and staged as a native one-arm objective-response-rate source
blocker: rows expose matched early-phase/phase-III ORR responder counts, but these are one-arm oncology activity rates rather than randomized active-vs-control treatment effects; do not promote to the strict D plot without a separate native ORR policy
```

```text
source_name: Hanzel et al. 2023 IBD phase II/III paired induction studies
landing_url: https://journals.lww.com/ctg/fulltext/2023/08000/outcomes_in_phase_2_and_phase_3_trials_of.12.aspx
direct_data_url_or_api: http://links.lww.com/CTG/A993
local_file: data/raw/replication_projects/pilot_full_scale_inbound/hanzel_2023_ctg_ibd_phase2_phase3_supp.docx
access_status: downloaded locally
row_count_claimed: 22 Crohn's disease studies and 30 ulcerative colitis studies
current_status: parsed/inspected locally; no row-level effect/N payload found in the downloaded DOCX
blocker: local supplement contains search strategies and outcome-definition tables, not phase II/III matched effect rows or arm-level counts
```

```text
source_name: Wils et al. 2023 IBD phase II versus phase III review
landing_url: https://pmc.ncbi.nlm.nih.gov/articles/PMC10576605/
direct_data_url_or_api:
  https://onlinelibrary.wiley.com/action/downloadSupplement?doi=10.1002%2Fueg2.12455&file=ueg212455-sup-0001-suppl-data.docx
  https://onlinelibrary.wiley.com/action/downloadSupplement?doi=10.1002%2Fueg2.12455&file=ueg212455-sup-0002-table_s1.docx
  https://onlinelibrary.wiley.com/action/downloadSupplement?doi=10.1002%2Fueg2.12455&file=ueg212455-sup-0003-fig_s1.pdf
pmc_direct_assets:
  https://pmc.ncbi.nlm.nih.gov/articles/instance/10576605/bin/UEG2-11-797-s003.docx
  https://pmc.ncbi.nlm.nih.gov/articles/instance/10576605/bin/UEG2-11-797-s002.docx
  https://pmc.ncbi.nlm.nih.gov/articles/instance/10576605/bin/UEG2-11-797-s001.pdf
access_status: PMC direct assets require a proof-of-work cookie, but this was solved locally; files downloaded
row_count_claimed: 14 phase 2 trials and 24 phase 3 trials; includes a 1:1 matching sensitivity analysis
local_files:
  data/raw/replication_projects/pilot_full_scale_inbound/wils_2023_ibd/UEG2-11-797-s002.docx
  data/raw/replication_projects/pilot_full_scale_inbound/wils_2023_ibd/UEG2-11-797-s003.docx
  data/raw/replication_projects/pilot_full_scale_inbound/wils_2023_ibd/UEG2-11-797-s001.pdf
local_parser: scripts/parse_wils_2023_ibd_phase2_phase3.py
stage_output: data/derived/replication_pairs/harvest/staged/wils_2023_ibd_phase2_phase3_response_rates__stage.csv
stage_rows_written: 37
current_status: parsed locally and staged as a native treatment-arm response-rate source
blocker: tables expose treatment-arm response/remission rates, not active-vs-placebo/control effects; do not promote to strict D plot without a separate native metric policy
```

```text
source_name: Liang et al. 2019 randomized phase II/III oncology pairs
landing_url: https://pubmed.ncbi.nlm.nih.gov/31526874/
access_status: article abstract public; no public row-level data found
row_count_claimed: 57 matched phase II/phase III pairs
likely_metric: native survival logHR lane
current_status: conceptually strong but lower utility unless article/supplement has public row-level table
blocker: no direct public data file found
```

```text
source_name: Vreman et al. 2020 oncology phase II/III matches
landing_url: https://pmc.ncbi.nlm.nih.gov/articles/PMC7318994/
access_status: public article
row_count_claimed: 81 phase II/III matches from 252 oncology trials
likely_metric: ORR, median PFS, median OS, native oncology lane
current_status: stage target from article tables; no direct supplement file found from the PMC page during local probe
blocker: many outcomes are one-arm ORR or median survival, not strict treatment-vs-control D
```

### Ying Row Rescue Update from Inbound Research

The inbound notes improved the triage status of five Ying rows. Pair 010 has now been verified against local PDFs and promoted; the other rows remain staged or native-metric targets until their claimed variance fields are verified.

```text
row_id: ying_2023_pair_010_neutropenic_diet
new_status: promoted locally
verified_inputs:
  pilot: ND 4/9 vs FSG 4/10
  full-scale: ND+FSG 27/77 vs FSG 24/73
recommended_metric: binary event counts to OR, then Chinn d
axis_used: harm-positive infection effect; convert sign if plotting benefit-positive outcomes
local_outputs:
  data/derived/replication_pairs/harvest/staged/ying_2023_partial_reconstruction__stage.csv
  data/derived/replication_pairs/harvest/promoted/ying_2023_partial_reconstruction__promoted_pairs.csv
verification_source: PubMed abstract for pilot events, local neutropenic-diet meta-analysis PDF for pilot arm denominators, local Moody 2018 PDF for full-scale counts
```

```text
row_id: ying_2023_pair_012_otch_barthel
new_status: promoted locally as a sensitivity row
verified_inputs:
  pilot: intervention n=63, control n=55 randomized; Barthel change +0.6 SD 3.9, n=59 versus -0.9 SD 2.2, n=46 at 3 months
  full-scale: N randomized 1042; BMJ/PMC Table 3 adjusted Barthel mean difference 0.19, 95% CI -0.33 to 0.70, table Ns 540 intervention and 436 control
recommended_D_original: 0.456 using pilot change-score pooled SD
recommended_D_replication: 0.047 inferred from the adjusted mean-difference CI and table Ns
local_sources:
  data/raw/replication_projects/pilot_full_scale_inbound/ying_rescues/otch_pilot.pdf
  data/raw/replication_projects/pilot_full_scale_inbound/ying_rescues/otch_pmc.html
local_outputs:
  data/derived/replication_pairs/harvest/staged/ying_2023_partial_reconstruction__stage.csv
  data/derived/replication_pairs/harvest/promoted/ying_2023_partial_reconstruction__promoted_pairs.csv
caveat: sensitivity-grade row because the follow-up estimate is adjusted/cluster-model based and D is inferred from the reported CI rather than arm-level SDs
```

```text
row_id: ying_2023_pair_014_postpartum_sleep
new_status: promoted locally as a CI-derived sensitivity row
verified_inputs:
  pilot: sleep intervention n=15, control sleep-outcome n=14; maternal nocturnal sleep 433 versus 376 minutes; mean difference +57 minutes, 95% CI +6 to +107
  full-scale: complete-case sleep Ns intervention n=110, control n=105; adjusted MD +5.97 minutes, 95% CI -7.55 to +19.5
recommended_D_original: 0.799 by CI-derived Hedges g
recommended_D_replication: 0.118 by CI-derived Hedges g
local_sources:
  data/raw/replication_projects/pilot_full_scale_inbound/ying_rescues/postpartum_sleep_pilot.pdf
  data/raw/replication_projects/pilot_full_scale_inbound/ying_rescues/postpartum_pmc.html
local_outputs:
  data/derived/replication_pairs/harvest/staged/ying_2023_partial_reconstruction__stage.csv
  data/derived/replication_pairs/harvest/promoted/ying_2023_partial_reconstruction__promoted_pairs.csv
caveat: this is a sensitivity row because both D estimates are inferred from reported mean-difference CIs rather than arm-level SDs
```

```text
row_id: ying_2023_pair_017_tat_weight_maintenance
new_status: staged with D-compatible estimates recovered, not promoted
verified_inputs:
  pilot: N=92 randomized; SDS n=31, TAT n=30, qigong n=31; 24-week Table 3 adjusted TAT-SDS difference -1.22 kg, SDE 0.71; definitive-trial paper also reports the pilot contrast as 0.1 versus 1.2 kg regain, SD=2.3, Cohen's d=0.48
  full-scale: N=285 randomized; TAT n=142, social support n=143; adjusted TAT-SS weight-regain difference -1.24 kg with SE=0.74
recommended_metric: native kg mean difference; possible sensitivity D only
recommended_D_original: 0.48 from the full-scale paper's pilot-study design paragraph
recommended_D_replication: about 0.198 if the adjusted model SE is treated as the between-arm SE
local_sources:
  data/raw/replication_projects/pilot_full_scale_inbound/ying_rescues/tat_weight_maintenance_pilot.pdf
  data/raw/replication_projects/pilot_full_scale_inbound/ying_rescues/tat_full_pmc.html
blocker: held out of the promoted D plot because the pilot endpoint is 24 weeks while the full-scale primary endpoint is 12 months, and the replication D is model-SE-derived
```

```text
row_id: ying_2023_pair_033_pediatric_depression_relapse
new_status: stage_native_metric
claimed_new_inputs:
  pilot: HR=8.80 for MM vs MM+CBT, abs(logHR)=2.175
  full-scale: HR around 0.31 for CBT+MM vs MM, abs(logHR)=about 1.16
recommended_metric: native survival logHR
blocker: do not force to D without a documented survival-to-SMD policy
```

### Ying Master Dataset Status

The inbound research did not find a public Ying master effect/N spreadsheet. Current best status:

```text
source_name: Ying 2023 pilot/full-scale master data
landing_url: https://jamanetwork.com/journals/jamanetworkopen/fullarticle/2809388
access_status: restricted/contact-on-request
row_count_claimed: 249 in article; local dissertation roster has 248
data_sharing_statement: available by request from first author, xying5@jh.edu according to inbound research
current_status: do not re-add as a public data source unless contact yields a spreadsheet
```

## Exact Search Target

Look for datasets, supplements, dissertations, GitHub repositories, OSF projects, Dataverse deposits, Zenodo records, Figshare records, publisher supplements, or PubMed Central tables that contain one of these structures:

- Pilot trial citation linked to later definitive RCT citation.
- Feasibility trial linked to full-scale trial.
- External pilot linked to main trial.
- Phase II randomized trial linked to phase III randomized trial.
- Early small clinical study linked to later larger confirmatory trial with same primary endpoint.
- Meta-epidemiologic review of pilot-to-full-scale RCTs with row-level data.
- Trial-program dataset with both pilot and definitive trial identifiers.

Search terms that should be used directly:

```text
"pilot trial" "full-scale trial" dataset effect size sample size
"pilot trial" "definitive trial" "effect size" "sample size"
"feasibility trial" "definitive RCT" dataset
"external pilot" "main trial" randomized controlled trial dataset
"pilot trial characteristics" "full-scale trials" data
"postpilot design modifications" "full-scale trials" data
"pilot trial" "definitive trial" "mean difference" "standard deviation"
"pilot trial" "definitive trial" "odds ratio"
"pilot study" "full-scale randomized trial" "supplementary data"
"phase II" "phase III" paired trials effect size sample size
"phase 2" "phase 3" randomized trial paired dataset
"meta-epidemiological" "pilot trial" "definitive trial"
"NIHR" "pilot" "definitive trial" dataset
"CONSORT extension" "pilot trials" "definitive trial" data
"feasibility studies" "progression to full-scale trial" dataset
```

Potential source families to check:

- JAMA Network Open and JHU dissertation follow-ups to Ying 2023.
- BMJ Evidence-Based Medicine or BMJ Open pilot/full-scale trial reviews.
- NIHR Journals Library and HTA reports.
- Trials journal supplements.
- Pilot and Feasibility Studies journal supplements.
- CONSORT pilot/feasibility extension papers and their cited datasets.
- PubMed Central articles with supplementary Excel/CSV.
- OSF/Dataverse/Zenodo/Figshare records linked from meta-epidemiology articles.
- Oncology phase II to phase III paired-trial reviews, but only if row-level phase II and phase III effect/N values are exposed.

## Output Schema Requested from GPT

For every candidate source, provide this table. Do not hide URLs behind Markdown link text; include raw URLs.

```text
source_name:
source_type: roster | dataset | supplement | dissertation | repository | article_table | registry_linkage | other
landing_url:
direct_data_url_or_api:
file_name_and_format:
access_status: public | restricted | login_required | dead_link | unclear
row_count_claimed:
row_count_verified:
pair_definition:
why_possible_candidate:
what_exact_pair_fields_exist:
pilot_identifiers_available: DOI | PMID | NCT | citation | other
full_scale_identifiers_available: DOI | PMID | NCT | citation | other
effect_fields_available:
N_fields_available:
same_endpoint_evidence:
D_axis_promotable: yes | no | maybe
if_not_promotable_blocker:
best_next_command_or_download:
notes:
```

For specific row rescues, provide row-level entries:

```text
row_id:
source_dataset:
pilot_title:
pilot_doi:
pilot_pmid_or_nct:
full_scale_title:
full_scale_doi:
full_scale_pmid_or_nct:
outcome:
pilot_N_total:
pilot_arm_Ns:
full_scale_N_total:
full_scale_arm_Ns:
pilot_effect:
pilot_effect_inputs:
full_scale_effect:
full_scale_effect_inputs:
conversion_needed:
recommended_D_original:
recommended_D_replication:
confidence: high | moderate | low
promotion_recommendation: promote | stage_native_metric | hold_needs_pdf | reject
reason:
urls:
```

## What Has Already Been Investigated Locally

### Ying 2023 dissertation and JAMA/BMJ companion articles

Where it landed:

- Very valuable but not a machine-readable effect/N dataset.
- We extracted the 248-pair roster from the dissertation appendix.
- We promoted 5 rows and staged the best remaining native/sensitivity candidates.
- The rest of the 248 probably requires primary-paper-by-primary-paper PDF/table extraction.

What GPT should still do:

- Search for an author-posted Ying master dataset, appendix spreadsheet, OSF/Dataverse/Zenodo/Figshare deposit, or dissertation supplement that has the 248 pairs with effect/N/variance.
- If no master dataset exists, target high-yield rows from the 248 roster where abstracts/PMC/full text expose arm Ns and compatible effects.

What GPT should not do:

- Do not report only the JAMA Network Open article page or dissertation PDF as if that solves the problem. We already have them.
- Do not report the 248-pair roster unless it includes effect/N fields.

### `data/raw/replication_projects/clinical_replication/`

Local files:

```text
data - published.xlsx
data - reanalyzed.xlsx
Replications reasons - summary spreadsheet.xlsx
outline.Rmd
```

Where it landed:

- Promising adjacent source.
- This is a dataset about reproducibility of highly cited medical articles and later replications/meta-analyses.
- It is not specifically pilot-to-full-scale.
- It has structured fields that may be useful for a separate clinical replication lane:
  - highly cited article title/DOI/evidence level
  - replication article title/DOI/evidence level
  - `N.HC`, `N.REP.Total`, `N.REP.Specific`, `N.Before`
  - `Estimate.HC`, `CI.lower.HC`, `CI.upper.HC`, `p.value.HC`
  - `Estimate.REP`, `CI.lower.REP`, `CI.upper.REP`, `p.value.REP`
  - `Risk.Measure`
  - replication-status fields

Why it is not enough for the current request:

- The relationship is usually "highly cited clinical finding versus later evidence", not "pilot trial versus scaled-up definitive trial".
- Many rows are meta-analyses or later reviews, not single larger full-scale trials.
- It needs a metric policy for proportions, ORR, RR, HR, OR, and one-arm outcomes.

What GPT should do:

- Search for the paper/dataset provenance and whether there is a public codebook defining all columns.
- Identify whether any rows are explicitly pilot/phase I/phase II to phase III/full-scale and could be subsetted.

### Compare Trials corpus

Local folder:

```text
data/raw/corpus_candidates/compare_trials/
```

Key files:

```text
compare_trials.csv
compare_trials_outcome_rows.csv
assessments/study_*.csv
```

Where it landed:

- Good for protocol/registry versus publication outcome reporting.
- Not an original-vs-full-scale effect-size pair source.
- It tracks outcome switching and reporting differences, not pilot-to-definitive pair linkage.

What GPT should not do:

- Do not return Compare Trials as a solution unless a separate file links pilot trials to definitive trials and provides effects/N.

### BEAR, Cochrane, ClinicalTrials.gov, and EUCTR corpora

Local folders include:

```text
data/raw/bear/
data/derived/bear/
data/raw/cochrane_packages/
data/interim/bear/
```

Where they landed:

- Useful clinical D/N provenance and registry/review effect-size corpora.
- Not explicit pilot-to-full-scale pair sources.
- Cochrane packages can contain small trial effects and larger trial effects in the same review, but they do not provide a pilot/main-trial linkage by default.
- ClinicalTrials.gov and EUCTR rows provide registry outcomes, but no automatic "this pilot scaled into that definitive RCT" relation.

What GPT should do:

- Only revisit this path if there is a known pairing/linkage method, such as NCT related-studies fields, trial acronyms that connect pilot and definitive trials, or a review dataset explicitly marking pilot versus definitive studies.

### Publication-bias and regulatory direct-denominator datasets

Already worked or partly worked:

- Cipriani/GRISELDA antidepressants.
- Turner antidepressants.
- Turner antipsychotics.
- Roest anxiety.
- Amarilyo rheumatoid arthritis biologics.

Where they landed:

- These are valuable publication-bias or regulatory-submission datasets.
- They are not pilot-to-full-scale pair sources.
- Do not return them as "more like Ying" unless a subset explicitly links pilot trials to later definitive trials.

### Clinical primary-endpoint suggestion tracker

Local file:

```text
reports/corpus_suggestion_tracker.md
```

High-fit clinical leads already identified there:

- Olivier 2024 cardiovascular RCT primary endpoints.
- Rothwell/Julious/Cooper 2018 HTA RCT primary endpoints.
- Allan 2017 cardiovascular RCT primary outcomes.
- Lawrence 2018 oncology phase III RCTs.
- Nadler 2024 oncology FDA approvals.
- Wayant 2018 major-journal phase III RCT p-values.

Where they landed:

- Mostly primary-endpoint clinical trial datasets or review cohorts.
- Not confirmed pilot-to-full-scale.
- Some may provide useful later large-trial endpoints, but they lack the pilot side unless linked to another source.

## Potential New Source Types Worth Searching

### Meta-epidemiology of pilot-to-definitive trial progression

Best fit. We need datasets where authors assembled a roster of pilot trials and the resulting definitive RCTs.

Look for:

- Excel/CSV supplements with one row per pilot-full pair.
- Trial DOI/PMID/NCT for both sides.
- "primary outcome in pilot" and "primary outcome in definitive trial".
- N per side and effect estimate/variance.

### Phase II to phase III paired-trial datasets

Useful if the clinical question and outcome are comparable. Be careful:

- Oncology phase II often uses one-arm objective response rate; phase III often uses survival HR versus comparator. That is not a strict same-axis pair unless both sides report a shared endpoint.
- A single-arm phase II ORR and later phase III ORR can be staged in a native-metric lane if N and response proportions exist.
- Do not mix phase II tumor response with phase III overall survival unless explicitly labeled as exploratory/native metric.

### External pilot to main trial within named trial programs

Very promising. Trial acronyms often expose the linkage:

- LIFE-P -> LIFE.
- UK-HARP-II -> SHARP.
- OTCH pilot -> OTCH full trial.
- Lung Screening Study -> NLST.

Search by terms like "pilot" plus trial acronym plus "full trial" or "main trial".

### NIHR HTA reports

Promising but labor-heavy. Many HTA reports include pilot and main trial chapters, arm Ns, and outcome tables. Need extractable tables or appendices.

### Trial registries with linked NCTs

Potential but not solved locally. Need a pairing key:

- `ClinicalTrials.gov` linked studies or references.
- NCT acronyms shared between pilot and main trial.
- protocol publications that cite the pilot trial.

Do not return raw registry search results unless the pair link is explicit.

## Red Flags and Exclusion Rules

Exclude or mark low priority when:

- The source only says a full-scale trial exists but gives no citation or identifier.
- It has pilot feasibility outcomes only and the later trial has an efficacy endpoint with no common measure.
- It reports only aggregate percentages like "X percent of pilots led to full trials".
- It is a generic trial registry without pair linkage.
- It is a systematic review of pilot studies but does not identify later full trials.
- It is a phase I dose-escalation study with no comparable later endpoint.
- It is an implementation pilot where the full-scale outcome is completely different.
- It has only narrative results and no N/effect/variance fields.

## What Counts as a Good Find

High-value:

- Public spreadsheet or CSV with pilot DOI, full-scale DOI, pilot N, full-scale N, and effect or variance fields.
- Paper supplement with row-level pilot/full pair tables and enough raw outcome data.
- Dissertation appendix with row-level tables beyond citation rosters.
- Repository with extraction code and raw PDFs/tables.
- PMC full text exposing arm Ns and exact event/mean/SD data for both sides of a Ying pair.

Medium-value:

- Pair roster with DOIs plus abstracts/full texts likely to contain extractable endpoints.
- Native-metric pair rows, such as HRs, RRs, ORs, or mean differences, even if not immediately D-convertible.
- Phase II to phase III rows with same endpoint but one-arm versus randomized design differences.

Low-value:

- Roster only, no effect/N.
- Full-scale trial only.
- Pilot trial only.
- Registry-only records with no results.
- Restricted repository with no public fallback.

## Remaining Tasks for GPT or Manual Access

1. Find whether Ying 2023 has a public author dataset beyond the dissertation PDF and JAMA/BMJ supplements. Local status remains restricted/contact-on-request.
2. Search for additional high-yield Ying rows beyond 010/012/014/017/033 where primary papers expose same-endpoint arm Ns and effects.
3. Search additional meta-epidemiologic datasets of pilot-to-definitive RCTs with row-level public data.
4. Search phase II to phase III paired-trial reviews, especially oncology and behavioral medicine, but report only rows with same-outcome effect/N fields.
5. Search NIHR HTA and Trials/Pilot and Feasibility Studies supplements for public Excel/CSV pair rosters.
6. For every candidate, explicitly state whether it has row-level pair linkage and whether both sides contain effect/N data.

## Deliverable Format

Please return:

1. A ranked list of the most promising new sources.
2. A table of all investigated sources, including failures.
3. Direct raw URLs or API URLs for every file.
4. A row-rescue table for any individual pairs that can be promoted or staged.
5. Clear labels:
   - `promote_now`
   - `stage_native_metric`
   - `hold_needs_pdf`
   - `not_pair_source`
   - `restricted`
   - `dead_end`

Be specific about why each source was considered possible. Also be specific about why it failed if it failed: no pair linkage, no effect fields, no N fields, wrong outcome, restricted file, dead link, only aggregate review summary, or not actually pilot-to-full-scale.

## Minimal Example of a Useful Answer

```text
source_name: Example Pilot-to-Definitive RCT Dataset
landing_url: https://...
direct_data_url_or_api: https://...
file_name_and_format: supplement_table_2.xlsx
access_status: public
row_count_claimed: 87
row_count_verified: 87
pair_definition: pilot RCT linked to subsequent definitive RCT by authors
why_possible_candidate: rows contain pilot DOI, definitive DOI, primary endpoint, N, and treatment effect
what_exact_pair_fields_exist: pilot_N, definitive_N, pilot_OR, pilot_OR_CI, definitive_OR, definitive_OR_CI, endpoint_name
D_axis_promotable: maybe
if_not_promotable_blocker: ORs are available but event counts are not; can use Chinn conversion if accepted
best_next_command_or_download: curl -L -o example.xlsx "https://..."
notes: 42 rows have full-scale N > pilot N and both N >= 10
```

## Local Follow-Up Once GPT Returns Leads

Use these scripts after adding new candidate rows or downloads:

```bash
python3 scripts/extract_ying_pair_roster.py
python3 scripts/ingest_ying_partial_reconstruction.py
python3 scripts/analyze_replication_pairs.py
python3 scripts/build_replication_source_audit.py
python3 scripts/build_paper_assets.py
```

Only run the full rebuild after we add or promote rows. This handoff itself is report-only.
