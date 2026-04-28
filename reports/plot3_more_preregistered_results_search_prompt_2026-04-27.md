# Research Prompt: Find More Strict Plot 3 Preregistered Confirmatory D/N Rows

Date: 2026-04-27

## Copy/Paste Prompt

We are building a D-vs-N evidence map. Plot 3 is the strict preregistered-confirmatory-results layer. It currently has only **156** plotted rows, which is too small to be satisfying. Your job is to find additional public, auditable, row-ready or near-row-ready sources that can expand Plot 3 without weakening the row definition.

This is not a bibliography task. We need candidate corpora or row rescues that expose:

- a preregistered, pre-analysis-plan, Registered Report, protocol-locked, or otherwise precommitted confirmatory result/hypothesis row;
- a focal/main-result selector that identifies which row(s) are confirmatory, not merely exploratory table tests;
- sample size `N` for the row;
- effect size `D`, or enough statistics to compute a D-like effect on the shared axis;
- source URLs and exact file names/codebooks.

The target output is a research memo that tells us what to add, what to stage, what to keep as sidecar-only, and what to ignore.

## Current Strict Plot 3 Universe

Strict Plot 3 currently has 156 rows:

| Source family | Rows in Plot 3 | Current status |
| --- | ---: | --- |
| Schäfer/Schwarz preregistered psychology articles | 89 | included as preregistered key-question effects with D/N |
| Scheel et al. Registered Reports / preregistered-hypotheses corpus | 32 | included D/N-ready subset of 71 coded hypotheses |
| SCORE/COS preregistration-indicated original papers | 31 | included paper-level rows from preregistration-indicated SCORE papers with D/N |
| Dorison et al. PSA-CR001 pooled preregistered rows | 4 | included pooled primary confirmatory outcomes |

Current local files to treat as state of the world:

```text
data/derived/effect_inflation_dataset/plot3_preregistered_results.csv
data/derived/effect_inflation_dataset/plot3_preregistered_source_catalog.csv
data/derived/effect_inflation_dataset/plot3_preregistered_sensitivity_sidecar_rows.csv
data/derived/effect_inflation_dataset/plot3_ctgov_phase2plus_primary_randomized_sidecar_rows.csv
data/derived/paper_tables/table_40_preregistered_hypotheses_scheel_2021_psa_cr001_corpus.csv
data/derived/paper_tables/table_41_added_preregistered_rows_from_psa_cr001_dorison_et_al_2022.csv
data/derived/corpus_candidates/candidate_d_n_papers.csv
data/derived/corpus_candidates/candidate_d_n_rows.csv.gz
docs/_generated/plot3_preregistered_sources.qmd
```

## Strict Plot 3 Admission Gate

A candidate row can enter strict Plot 3 only if:

1. The row represents a preregistered confirmatory result or hypothesis, not a post hoc exploratory result.
2. The source gives a defensible row selector: first preregistered hypothesis, primary outcome, main confirmatory test, Registered Report hypothesis, pooled primary endpoint, or equivalent.
3. `D` and `N` are recoverable at the result-row level.
4. The source is public or otherwise locally auditable.
5. The row is not already consumed as original-vs-replication evidence in Plot 1, unless it is clearly a separate standalone preregistered result layer and you flag the double-counting issue.
6. Admission does **not** depend on whether the result was supported or significant.
7. The source is not retracted.

Important: "registered somewhere" is not enough. Trial registration, OSF registration, or an article-level preregistration flag is only admissible if the exact plotted row is tied to a prespecified analytic outcome/hypothesis or a source-provided focal result selector.

## Effect and N Standards

Acceptable effect inputs:

- means, SDs, and arm Ns for standardized mean differences;
- mean difference plus SE/CI and arm Ns, with derivation documented;
- event counts and arm Ns, convertible through log odds ratio or log risk ratio; Chinn-style OR-to-d is acceptable if flagged;
- correlations and N, convertible to `d`;
- t/F/chi-square/z statistics with clear df/N and direction;
- reported Cohen's d, Hedges g, standardized mean difference, or equivalent;
- pooled primary outcome estimates with N and enough information to put on the shared `D` axis.

Stage, but do not force into strict D, if the coherent metric is native:

- log hazard ratios;
- regression/ATE coefficients without standardizing denominator;
- SEM/path coefficients;
- one-arm objective response rates;
- odds/risk ratios where arm denominators are missing;
- cluster-adjusted estimates where the effective N/variance mapping is not defensible.

## Highest-Yield Search Order

Do the search in this order. The fastest win is probably rescuing missing rows from already trusted sources, not finding an entirely new universe.

### Track A: Rescue Rows From Already Included Sources

1. **Scheel et al. 2021 Registered Reports corpus**
   - Current: 71 coded preregistered hypotheses, only 32 D/N-ready rows.
   - Goal: recover D/N for the missing 39 rows from article PDFs, supplements, OSF pages, or local tables.
   - Need: study title, journal, hypothesis label, N, effect/statistic, conversion method, URL/PDF/supplement source.
   - This is the cleanest possible expansion because the rows already pass the preregistered-hypothesis gate.

2. **SCORE/COS preregistration-indicated original papers**
   - Current: 245 unique SCORE paper IDs marked `prereg=True`; only 31 deduplicated positive D/N rows enter.
   - Goal: determine whether the other 214 IDs have extractable D/N in SCORE files, paper PDFs, or supplements.
   - Need: paper ID/title/DOI, prereg flag evidence, focal claim/result selector, N, D/statistic, conversion method.
   - Caveat: the SCORE prereg flag is paper-level. Promote only if the focal claim/result can reasonably be tied to the preregistered paper-level result; otherwise stage.

3. **Schäfer/Schwarz preregistered psychology articles**
   - Current: 93 preregistered coded rows, 89 D/N-ready rows.
   - Goal: inspect the 4 missing rows and determine whether D/N can be recovered.
   - This is small but clean.

4. **PSA-CR001**
   - Current: 4 pooled primary rows.
   - Goal: verify whether any additional preregistered primary confirmatory outcomes or source-approved pooled effects exist without duplicating nested country rows.

### Track B: New Registered Report / Preregistered-Hypothesis Corpora

Search for datasets, appendices, and codebooks that extend Scheel-style Registered Report coding beyond the current 71 rows.

Promising keywords and phrases:

```text
"Registered Reports" dataset hypotheses effect sizes sample size
"Registered Reports" meta-analysis support hypothesis data
"Registered Reports" "Cohen's d" "sample size" hypothesis
"Registered Reports" "support" "hypotheses" "data"
"registered report" "first hypothesis" "effect size" "sample size"
"preregistered hypotheses" corpus "effect size"
"registered reports" OSF "hypotheses" "effect size"
"Scheel" "Schijen" "Lakens" replication data registered reports
"Registered Reports" "Comprehensive Results in Social Psychology" "effect size"
"Peer Community In Registered Reports" data hypotheses effect sizes
```

Candidate source types to check:

- Registered Reports databases or bibliographies with coded hypotheses and result statistics;
- follow-up datasets to Scheel et al. 2021;
- journal-specific Registered Report collections with result tables;
- meta-research papers on Registered Reports that have supplemental coded datasets;
- RR special issues in psychology, neuroscience, education, medicine, and social science.

Promotion rule: one row per preregistered hypothesis/result if D/N exists; otherwise row-rescue list.

### Track C: Preregistered Psychology / Behavioral-Science Article Samples

Find Schaefer/Schwarz-like samples where authors coded published articles for preregistration and extracted a key effect.

Search phrases:

```text
"preregistered" psychology articles "effect size" dataset
"preregistration" "effect size" "sample size" psychology "data"
"preregistered studies" "Cohen's d" "supplementary data"
"preregistration" "key result" "effect size" "sample size"
"preregistration" "focal effect" dataset
"open science" "preregistration" "effect sizes" "psychology"
"preregistration" "statistical power" "effect size" "sample size" "coded"
```

Accept only if the source has a focal/key result selector. Article-level preregistration flags alone are not enough if the extracted rows are all table tests.

### Track D: Big-Team Preregistered Projects With Pooled Primary Results

Hunt for standalone preregistered big-team projects that report pooled primary outcomes with N and effect sizes, especially if they are not already Plot 1 original-vs-replication pair rows.

Candidate families:

- Psychological Science Accelerator projects beyond PSA-CR001;
- ManyBabies projects;
- ManyClasses projects;
- Many Labs projects only if there is a standalone preregistered pooled result not already used as a Plot 1 replication row;
- Registered Replication Reports only if a separate Plot 3 lane is explicitly defensible and double-counting is flagged;
- CREP / collaborative replication education projects if they have preregistered pooled results with D/N.

Search phrases:

```text
"Psychological Science Accelerator" "preregistered" "primary outcome" "effect size"
"PSA" "pooled" "preregistered" "Cohen's d" "sample size"
"ManyBabies" "preregistered" "effect size" "sample size" data
"ManyClasses" "preregistered" "effect size" "sample size"
"CREP" "preregistered" replication "effect size" "sample size"
"registered replication report" "pooled effect" "sample size" "Cohen"
```

Known local side notes:

- PSA replication-pair rows are already Plot 1 evidence unless a project has standalone non-pair primary rows.
- ManyBabies 3 has preregistered materials locally but no confirmed final machine-readable site-level D/N payload.
- ManyClasses 2 has materials locally but no compact D/N parser yet.
- ERN/Pe and self-control fMRI have preregistered materials but no compact D/N table.

### Track E: Social-Science PAP / Field-Experiment Sources

Search for pre-analysis-plan corpora where primary outcomes and estimates are mapped to exact PAPs.

Candidate families:

- EGAP Metaketa projects;
- AEA RCT Registry projects with PAPs and public result datasets;
- TESS experiments with PAPs and public data;
- OSF Registries projects with linked published results;
- 3ie / World Bank / IPA / J-PAL field-experiment repositories, if primary outcome estimates and Ns are exposed.

Search phrases:

```text
"pre-analysis plan" "primary outcome" "effect size" "sample size" dataset
"AEA RCT Registry" "primary outcome" "effect size" "sample size"
"EGAP Metaketa" "pre-analysis plan" "effect size" "sample size"
"TESS" "pre-analysis plan" experiment "effect size" "sample size"
"OSF Registries" "primary outcome" "effect size" "sample size"
"J-PAL" "pre-analysis plan" "primary outcome" "standardized effect"
"IPA" "pre-analysis plan" "primary outcome" "standardized effect"
```

Promotion rule: exact PAP-primary or prespecified main-outcome rows can be promoted if D/N is available. Broad published table-test harvests from PAP papers remain sidecar-only.

### Track F: Clinical / Medical Protocol-Locked Sources

ClinicalTrials.gov alone is not enough, but clinical sources may still enter strict Plot 3 if they provide actual protocol/SAP-locked primary outcome results with effect/N.

Search for:

- datasets linking protocols/SAPs to published primary outcomes with arm-level results;
- trial reports where protocols/SAPs are public and the primary endpoint result is extractable;
- registered reports or protocol-first clinical trials with published primary outcomes and exact arm statistics.

Search phrases:

```text
"statistical analysis plan" "primary outcome" "effect size" "sample size" dataset
"protocol" "primary outcome" "effect size" "sample size" randomized trial dataset
"registered clinical trial" "statistical analysis plan" "primary endpoint" "effect size"
"published protocol" "primary outcome" "mean difference" "sample size" RCT
"COMPare" "prespecified outcomes" "effect size" "sample size"
```

Known exclusions:

- Broad ClinicalTrials.gov/AACT rows remain sidecar-only unless matched to locked protocol/SAP analyses.
- CliniFact and AACT primary outcomes are useful comparators but currently lack analytic-preregistration proof.
- COMPare has prespecified outcome status but no D/N fields in the local parse.

## Known Sources Already Considered

Do not rediscover these without adding new row-ready information:

| Source | Current landing |
| --- | --- |
| Schäfer/Schwarz preregistered articles | included, 89 rows |
| Scheel et al. Registered Reports corpus | included, 32/71 rows; missing-row rescue is high priority |
| SCORE/COS preregistration-indicated papers | included, 31/245 prereg-indicated paper IDs; missing-row rescue is high priority |
| PSA-CR001 | included, 4 pooled rows |
| ClinicalTrials.gov / AACT | broad and cleaner sidecars only, not strict Plot 3 |
| Brodeur preregistered/PAP economics table tests | sidecar only unless exact test-level PAP selector is found |
| CliniFact | D/N exists but registry-linked primary outcomes only; already represented in published endpoint surface |
| COMPare | prespecified status exists but no D/N |
| FReD | already Plot 1 / Plot 2 evidence, not standalone preregistered results |
| Many Labs / RRR / PSA replication rows / TPP / retrieval-extinction rats | already Plot 1 replication-pair evidence unless a separate standalone row policy is justified |
| ManyBabies 3 / ManyClasses 2 / ERN-Pe / self-control fMRI | preregistered materials exist but compact D/N result rows not yet found |
| Twomey kinesiology | prereg flags and Ns exist, exact effect statistics missing |
| Linden focal/random sample | D/N exists but preregistration applies to the meta-research coding study, not the sampled source articles |
| Nordic trial linkage | registration-publication metadata exists, no D/N |
| Protzko High-Replicability Research | not included because retraction status blocks it |

## Required Output Format

Return a concise research memo with these sections.

### 1. Decision Summary

List every source family found with one of these labels:

```text
promote_now
row_rescue_promising
stage_native_metric
sidecar_only
duplicate_plot1
blocked_missing_d_or_n
blocked_no_focal_selector
blocked_access
not_plot3_source
```

### 2. Ranked Candidate Sources

Use this table:

| rank | label | source_name | source_type | landing_url | direct_data_url_or_api | file_name_and_format | access_status | row_count_claimed | row_count_verified | row_definition | why_possible_candidate | exact_prereg_evidence | focal_selector | D_fields_available | N_fields_available | D_axis_promotable | blocker_if_any | best_next_command_or_download | notes |
| ---: | --- | --- | --- | --- | --- | --- | --- | ---: | ---: | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |

Be specific. If a source claims 500 preregistered studies but only 37 have D/N, say that.

### 3. Row-Rescue Candidates

For any row-ready or nearly row-ready additions, use this schema:

| row_id | source_family | paper_or_project | prereg_url_or_rr_status | result_label | row_selector | N | effect_metric | effect_value_or_inputs | D_recommended | conversion_method | source_url | promotion_recommendation | confidence | notes |
| --- | --- | --- | --- | --- | --- | ---: | --- | --- | ---: | --- | --- | --- | --- | --- |

### 4. Already-Investigated Confirmation

For each known source you touch, say whether you found:

- more row-ready data;
- only native-metric data;
- only metadata;
- no new public payload;
- or a duplicate of Plot 1 / Plot 2 rows.

### 5. Implementation Guidance

For every promotable source, give:

- exact filtering rule;
- row unit;
- deduplication rule;
- D conversion rule;
- whether to append to `plot3_preregistered_results.csv`, stage in a new file, or keep sidecar-only;
- expected row count after filtering;
- any double-counting risk.

### 6. URLs To Hit Manually

Make a final list of URLs/files that require manual browser access, institutional access, JavaScript, captcha, or user download.

## Do Not Do These Things

- Do not use support/significance as an inclusion criterion.
- Do not count all tests in a preregistered paper as preregistered hypotheses.
- Do not count all registry rows as analytically preregistered.
- Do not silently mix table tests, registry outcomes, lab-level replication cells, and Registered Report hypotheses as if they were exchangeable.
- Do not include both a pooled project row and all nested site/country/lab rows in the same strict layer unless you explicitly propose a non-independent side panel.
- Do not ignore D/N. A source with beautiful preregistration metadata but no effect and N is not Plot 3-ready.

## Success Criteria

The search succeeds if it produces at least one of:

1. More D/N rows from the 39 missing Scheel Registered Reports hypotheses.
2. More D/N rows from the 214 missing SCORE preregistration-indicated paper IDs.
3. A new Registered Reports or preregistered-hypotheses corpus with row-level D/N.
4. A standalone big-team preregistered project with pooled primary outcomes and D/N that is not already consumed by Plot 1.
5. A social-science PAP/primary-outcome source with exact focal rows and D/N.
6. A defensible clinical protocol/SAP primary-outcome source with exact effect/N rows.

The search fails productively if it documents that a source is only registration metadata, only article-level flags, only table-test harvests, or only native metrics.
