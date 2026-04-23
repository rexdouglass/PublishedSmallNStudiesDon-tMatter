# Direct Publication-Bias Denominator Sprint

Last updated: 2026-04-20

This pass chased the newer suggestions that actually target publication bias:
a known denominator of conducted, registered, submitted, or regulatory trials,
plus publication status and a focal/primary effect with sample size.

## Bottom Line

The strongest immediate dataset is Cipriani GRISELDA 2018. It is open, local,
and has enough arm-level data to compute drug-vs-placebo effects separately for
published and unpublished antidepressant trials.

The strongest scaffold for a large biomedical build is now the Nordic trial
reporting dataset plus IntoValue and the local CliniFact x CT.gov bridge. The
Nordic/IntoValue files give trial denominators and publication links; the
bridge adds NCT-linked PMIDs, registry-side primary-outcome rows, enrollment,
and p-values. A first-pass abstract extractor now adds journal-side p-values,
sample-size candidates, CIs, and common effect metrics for the result-PMID
subset. It is still not a final journal-side effect table, but it is now a
real intermediate object rather than only a plan.

The strongest social-science denominator is the AEA RCT Registry. The current
registry CSV is local and has primary outcomes plus planned sample sizes, but
not journal-output coding or effect estimates. Leight/Asri/Imai appear to have
the right output-tracking dataset, but I did not find a public row-level release.

## D-Ready Rows Built

Output files:

- `data/derived/publication_bias_direct/direct_publication_bias_d_ready_rows.csv`
- `data/derived/publication_bias_direct/direct_publication_bias_d_ready_rows.parquet`
- `data/derived/publication_bias_direct/direct_publication_bias_summary.csv`
- `data/derived/publication_bias_direct/direct_publication_bias_study_collapsed_rows.csv`
- `data/derived/publication_bias_direct/direct_publication_bias_study_collapsed_rows.parquet`
- `data/derived/publication_bias_direct/direct_publication_bias_study_collapsed_summary.csv`

Current extraction has 1,021 raw D/N rows and 723 study-collapsed rows. The
strict count of explicit journal-reported result rows is 100: 35 Turner 2022
newer antidepressant rows, 19 Turner 2012 antipsychotic rows, and 46 Roest
2015 anxiety-disorder rows.

There are also 607 Cipriani rows from published-source trials, but these are
network-meta-analysis extraction rows from a published/unpublished trial
denominator, not direct journal-vs-FDA paired journal effect rows.

| Dataset | Status | Rows | Study IDs | Median N | Median D | % above p<.10 | Log-log slope |
|---|---|---:|---:|---:|---:|---:|---:|
| Cipriani continuous endpoint | published | 293 | 196 | 218 | 0.312 | 69.3 | -0.269 |
| Cipriani continuous endpoint | unpublished | 95 | 57 | 163 | 0.163 | 26.3 | -0.276 |
| Cipriani response endpoint | published | 312 | 216 | 214 | 0.273 | 62.5 | -0.295 |
| Cipriani response endpoint | unpublished | 95 | 56 | 177 | 0.120 | 20.0 | -0.200 |
| Roest 2015 anxiety disorders | journal-published | 46 | 46 | 273 | 0.385 | 91.3 | -0.150 |
| Roest 2015 anxiety disorders | FDA/regulatory, published trials | 49 | 49 | 262 | 0.370 | 83.7 | -0.164 |
| Roest 2015 anxiety disorders | FDA/regulatory, unpublished trials | 8 | 8 | 165 | 0.139 | 25.0 | -0.032 |
| Turner 2012 antipsychotics | journal-published | 19 | 19 | 297 | 0.421 | 94.7 | -0.119 |
| Turner 2012 antipsychotics | FDA/regulatory, published trials | 19 | 19 | 297 | 0.416 | 94.7 | -0.093 |
| Turner 2012 antipsychotics | FDA/regulatory, unpublished trials | 4 | 4 | 156 | 0.226 | 25.0 | NA |
| Turner 2022 newer antidepressants | journal-published | 35 | 35 | 397 | 0.286 | 80.0 | 0.105 |
| Turner 2022 newer antidepressants | FDA/regulatory | 41 | 29 | 397 | 0.268 | 65.9 | 0.931 |

The Turner/Roest slopes are not meaningful as stand-alone slope estimates
because row counts are tiny and the N ranges are narrow. The level comparisons,
and especially the published-vs-unpublished p-threshold fractions, are the
useful signal.

## Corpus Notes

### Cipriani GRISELDA 2018

Downloaded from Mendeley Data DOI `10.17632/83rthbp8ys.2`.

The workbook has 522 StudyIDs and 1,199 arm rows. The key surprise is that
`Year_Published` is also a publication-status field: rows can be a year or
`unpublished`. That gives 93 unpublished StudyIDs and 429 published StudyIDs.

Fields available: StudyID, drug, randomized N, responders, remitters, dropout
counts, endpoint mean, endpoint SD, endpoint N, scale, and weeks.

Current parser pairs every non-placebo arm to the largest placebo arm in the
same StudyID. It creates a response log-OR row and, where possible, a continuous
SMD row. Multiple active arms/doses remain multiple rows. Before using in a
figure, collapse to one comparison per StudyID or define a dose rule.

### Turner 2022 Antidepressants

Downloaded PLOS Medicine supplements. `s013` contains 104 trial rows with FDA
positive/negative status, journal outcome, publication indicator, and spin.
`s018` contains newer-antidepressant FDA and journal Hedges-g, SE, and N.

The parser now joins `s013` onto `s018`, so FDA rows split into published and
unpublished trials rather than `unknown`, and the row-level output preserves
publication/spin metadata. The current raw extraction has 35 journal rows,
36 FDA rows for published trials, and 5 FDA rows for unpublished trials. The
study-collapsed output keeps one preferred row per study and result source,
favoring narrow-dose rows over broad-dose duplicates.

### Turner 2012 Antipsychotics

Downloaded PLOS supplements and article table images. S2/S3 contain FDA and
journal Hedges-g with CIs. Article Table 1 contains arm sample sizes. I
transcribed the usable FDA-approved drug-vs-placebo Ns and publication status
into the parser. The current output has 19 FDA/journal paired published rows and
4 FDA-only unpublished rows. Active-comparator rows and the risperidone 204
Canada/US split rows are intentionally skipped because the table does not expose
clean comparable Ns for the split rows.

### Roest 2015 Anxiety Disorders

Downloaded the JAMA Psychiatry supplement, table image, and figures. The table
gives 57 FDA-reviewed trials, publication status, drug, indication, and
sample-size information. The public figures/supplement give FDA and journal
Hedges-g values with confidence intervals. I transcribed the usable trial-level
effect and N values into the parser.

The current output has 46 journal-published rows, 49 FDA/regulatory rows for
published trials, and 8 FDA/regulatory rows for unpublished trials. This is now
the cleanest non-antidepressant Turner-style extension in the local build.

### Chen 2019 Registry-vs-Publication Primary Outcomes

Downloaded the JAMA Network Open supplement from PMC after solving the NCBI
proof-of-work challenge. The public supplement is not the promised row-level
effect table. It contains search strategies, yearly hit counts, and an eTable 4
list of included RCTs with primary-outcome change classification. The article
reports 338 quantitative RCTs and 487 registry-vs-publication comparisons, but
the public supplement does not expose OR/N rows. Treat this as a high-value
author-request or reconstruction lead, not D-ready local data.

### CliniFact x CT.gov Bridge

Built with `scripts/build_clinifact_ctgov_bridge.py`.

Output files:

- `data/derived/publication_bias_direct/clinifact_ctgov_bridge_candidate_matches.csv.gz`
- `data/derived/publication_bias_direct/clinifact_ctgov_bridge_candidate_matches.parquet`
- `data/derived/publication_bias_direct/clinifact_ctgov_bridge_best_matches.csv`
- `data/derived/publication_bias_direct/clinifact_ctgov_bridge_best_matches.parquet`
- `data/derived/publication_bias_direct/clinifact_ctgov_bridge_summary.md`

This joins the processed CliniFact publication dataset to the parsed CT.gov KG
by exact NCT ID, then ranks registry-side candidate rows using outcome-title
and arm-label similarity. The current bridge yields:

- 1,970 CliniFact claim-publication rows
- 992 unique NCT IDs
- 1,540 unique PMIDs
- 718 exact NCT overlaps with the CT.gov KG
- 1,319 overlapping claim rows
- 12,777 candidate merged rows
- 1,319 best-match rows
- 1,317 best matches on CT.gov primary outcomes
- 1,286 best matches with registry p-values and D proxies

Best-match quality looks good enough to use as a scaffold:

- 1,261 `high_exactish`
- 36 `high_outcome`
- 4 `medium`
- 18 `weak`

This is still not direct publication-bias evidence in the strong sense because
the journal side contributes PMIDs, abstracts, and claim labels rather than a
numeric journal result. But it is now a concrete bridge object for extracting
or auditing the linked journal-side primary outcome against a registry-side
primary outcome row with enrollment and p-value already attached.

### CliniFact Journal-Side Numeric Extract

Built with `scripts/build_clinifact_publication_numeric_extract.py`.

Output files:

- `data/derived/publication_bias_direct/clinifact_publication_numeric_extract.csv`
- `data/derived/publication_bias_direct/clinifact_publication_numeric_extract.parquet`
- `data/derived/publication_bias_direct/clinifact_publication_numeric_extract_plausible.csv`
- `data/derived/publication_bias_direct/clinifact_publication_numeric_extract_summary.md`
- `data/derived/publication_bias_direct/clinifact_publication_registry_pairs.csv`
- `data/derived/publication_bias_direct/clinifact_publication_registry_pairs.parquet`
- `data/derived/publication_bias_direct/clinifact_publication_registry_pairs_summary.md`

This pass uses the bridge best-match table plus CliniFact abstracts. It keeps
only CliniFact rows with `claim_support_label` in `{positive, inconclusive}`,
because those are the result-PMID rows; `no_info` rows are background PMIDs and
are not journal-result references.

Current extractor counts:

- 738 result-PMID rows processed
- 675 rows with plausible publication year (`publication_year + 1 >= completion_year`)
- 682 rows with trial-design markers in the title or abstract
- 668 rows classified as plausible result reports
- 477 rows with abstract-side journal p-values
- 539 rows with abstract-selected N
- 364 rows with both journal p and abstract-selected N
- 477 rows with journal D proxies using registry enrollment as fallback
- 143 rows with extracted confidence intervals
- 117 rows with extracted effect estimates

For the plausible-result subset only:

- 440 rows have journal p-values
- 489 rows have abstract-selected N
- 339 rows have journal D proxies using abstract-selected N

This is still an abstract-only journal-side scaffold, not a finished
publication-bias corpus. The remaining hard step is article-level audit or
full-text extraction for the plausible subset.

### CliniFact Journal-vs-Registry Pairs

Built with `scripts/build_clinifact_publication_registry_pairs.py`.

This takes the plausible-result subset from the journal-side abstract extractor
and pairs it directly to the matched CT.gov primary-outcome row. It defines a
preferred journal-side D proxy, significance-discordance flags, and basic
registry-vs-journal comparison fields.

Current counts:

- 668 plausible publication rows
- 431 rows with paired journal and registry p-values
- 431 rows with paired journal and registry D proxies
- 74 rows with matched journal and registry effect families

Current agreement/inflation summary:

- agreement at `p < .05`: 0.807
- agreement at `p < .10`: 0.803
- median preferred journal D proxy: 0.334
- median registry D proxy: 0.281
- median journal minus registry D proxy: 0.000
- median journal / registry D ratio: 1.000

Quality tiers in the current paired file:

- 163 `high`
- 249 `medium`
- 220 `low`
- 36 `possible`

The paired file is useful now for audit and targeted follow-up. It is not yet a
final publication-bias estimate because the journal side still comes from
abstract extraction rather than article-audited or full-text numeric extraction.

### CliniFact Audit Queue

Built with `scripts/build_clinifact_pair_audit_queue.py`.

Output files:

- `data/derived/publication_bias_direct/clinifact_publication_registry_audit_queue.csv`
- `data/derived/publication_bias_direct/clinifact_publication_registry_audit_top200.csv`
- `data/derived/publication_bias_direct/clinifact_publication_registry_audit_summary.md`

This is a manual-review queue drawn from the `high` and `medium` paired rows.
It prioritizes significance discordance, large D-proxy gaps, and registry-vs-
journal effect-family mismatches.

Current queue counts:

- 357 audit rows total
- 200 top-priority rows
- 77 rows with `sig_discordant_05`
- 52 rows with `abs_d_delta >= 0.25`

This gives a practical next manual step: inspect the top-priority disagreements
rather than treating all 668 plausible rows as equally urgent.

### CliniFact Triage Pass

Built with `scripts/triage_clinifact_pair_audit_queue.py`.

Output files:

- `data/derived/publication_bias_direct/clinifact_publication_registry_triage.csv`
- `data/derived/publication_bias_direct/clinifact_publication_registry_clean_audit_queue.csv`
- `data/derived/publication_bias_direct/clinifact_publication_registry_likely_noncomparable.csv`
- `data/derived/publication_bias_direct/clinifact_publication_registry_triage_summary.md`

The audit queue was still inflated by obvious abstract-selection errors:
objective/method sentences, endpoint-description sentences, baseline-only
sentences, conclusion paraphrases without a p-value, and wrong-outcome matches.
The triage pass strips leading whitespace, flags those obvious non-result or
non-comparable sentence types, and deduplicates repeated claim rows.

Current triage counts:

- 412 `high`/`medium` pair rows triaged
- 42 cleaned manual-audit rows
- 152 likely non-comparable rows
- 33 cleaned rows with `sig_discordant_05`
- 23 cleaned rows with `abs_d_delta >= 0.25`

The cleaned queue covers 41 unique `nctId`s and 40 unique `PMID`s. It is still
mixed quality, but it is now much closer to a true manual-audit target than the
raw 357-row queue. The dominant false-positive reasons in the discarded rows
are:

- `structural_nonresult_sentence`
- `wrong_outcome_sentence`
- `baseline_within_group`
- `conclusion_without_p`
- `multi_p_ambiguous`

The current gap is no longer "find any registry-publication bridge." That
bridge now exists locally. The remaining gap is either article-level audit/full-
text extraction for the cleaned CliniFact set, or public row-level paired
primary-endpoint datasets from papers such as Chen 2019, Riveros 2013, Hartung
2014, Schwartz 2016, Chan 2004, Olivier 2024, and Rothwell 2018.

### CliniFact PMC Full-Text Enrichment

Built with `scripts/build_clinifact_pmc_fulltext_extract.py`.

Output files:

- `data/derived/publication_bias_direct/clinifact_pmc_fulltext_extract.csv`
- `data/derived/publication_bias_direct/clinifact_pmc_fulltext_extract.parquet`
- `data/derived/publication_bias_direct/clinifact_pmc_fulltext_resolved.csv`
- `data/derived/publication_bias_direct/clinifact_pmc_fulltext_unresolved.csv`
- `data/derived/publication_bias_direct/clinifact_pmc_fulltext_summary.md`

This pass takes the 42-row cleaned CliniFact audit queue and tries one more
local step: if the linked PMID has a PMCID, fetch the PMC article HTML, score
candidate full-text result windows for the primary outcome, and extract a
full-text p-value/effect where possible.

Current counts:

- 42 cleaned audit rows in
- 40 unique PMIDs
- 16 rows with PMCID
- 5 rows with article-like PMC HTML accessible
- 11 rows with PMCID but PMC challenge/blocked pages
- 26 rows with no PMCID
- 5 rows with full-text p-values recovered
- 2 rows resolved toward the registry result after full text
- 2 rows where full text supports the abstract-side disagreement
- 1 row where the full-text gap is larger than the abstract-side gap

The two resolved rows are:

- `PMID 19879973` / `NCT00911612`
- `PMID 21652735` / `NCT00595868`

So the remaining unresolved CliniFact rows are now split into three buckets:

1. `no_pmc_fulltext` (26 rows)
2. `pmc_access_blocked` (11 rows)
3. rows where full text was available and still supports the abstract-side
   disagreement or a larger gap (3 rows total)

That means the local limit is now clear. The next useful work is either:

- article-audit/full-text extraction outside PMC for the unresolved rows, or
- public row-level paired datasets from external sources.

### Olivier 2024 Cardiovascular RCTs

Downloaded the public JAMA Network Open supplements. The first supplement is
methods/formulas and aggregate sensitivity material; the second is a data-sharing
statement saying row-level data are available from the corresponding author on
reasonable request. This remains one of the highest-fit author-request targets:
major cardiovascular RCTs, primary endpoints, event/effect information, and N,
but no public CSV.

### Allan 2017 Cardiovascular RCTs

Downloaded the BMC Medicine article and supplementary DOCX. The public
supplement is an included-study list plus statistical-significance
classification, not the full numeric extraction table. It is useful for
reconstruction or author request, but not D-ready from public files alone.

### Lawrence 2018 Oncology Phase III Trials

Downloaded the PMC article and supplementary DOCX after solving the NCBI
proof-of-work challenge. The public supplement only provides aggregate ASCO/ESMO
framework cross-tabs. The article confirms that 213 phase III trials were
extracted and that observed primary-endpoint HR/p/CI data were collected, but
those row-level data are not present in the public supplement. This is a
reconstruction or author-request lead.

### Nadler 2024 Oncology FDA Approval Endpoints

Downloaded both Scientific Reports DOCX supplements. The supplements list drugs
and approval indications plus aggregate sensitivity tables. They do not expose
the 94 endpoint-level HR/N rows. The article is useful context for FDA-approval
endpoint sampling, but the public supplement is not D-ready.

### Rothwell 2018 HTA RCTs

Downloaded the article HTML. There is no separate supplementary dataset linked;
the article appendix lists the variables they extracted, including achieved N,
observed effect size, p value, and confidence intervals. This is a high-fit
author-request target, not public row-level data.

### Wayant 2018 Major-Journal Phase III RCT p Values

The JAMA article is visible and reports 203 articles and 272 primary endpoint
p-values. It confirms they extracted primary-endpoint p values, title, journal,
funding, sample size, endpoint type, and design metadata. I did not find a
public row-level supplement; command-line access to the JAMA page returned 403.
This is p+N author-request material, not a direct D-ready source.

### Nordic Trial Reporting

Cloned `cathrineaxfors/nordic-trial-reporting`.

Useful files:

- `publication-information-merged-2023-11-27-corrected-2024-10-16.csv`
- `final-trial-sample-2023-11-09-corrected-2024-10-01.csv`
- `publications-searches-2023-11-27-corrected-2024-10-01.csv`

The publication file has 2,112 eligible trials with publication status and
DOI/PMID/date/type. This is an excellent denominator/publication-linkage
scaffold. The README explicitly says they did not assess whether publications
reported the registered primary outcomes, and the files do not have effect
sizes.

### IntoValue

Cloned `maia-sh/intovalue-data`. `trials.csv` has 3,788 rows, enrollment,
registry IDs, DOI/PMID, publication type, publication timing, and registry
summary-results flags. It has 2,621 journal-publication rows and 511
summary-results rows.

It is a linkage scaffold, not an effect-size dataset.

### AEA RCT Registry

Downloaded current registry CSV from `https://www.socialscienceregistry.org/site/csv`.
It has 11,945 registry rows with RCT ID, status, primary outcomes, sample-size
fields, PAP/data/program flags, and relevant-paper fields.

This is the best social-science pre-publication denominator. It still needs
publication-output coding and effect extraction.

### Leight/Asri/Imai AEA Output Tracking

Downloaded the working paper PDF. It describes the exact kind of linked output
coding we want for 898 AEA field trials. I found the paper and OSF
preanalysis link, but not a public row-level output dataset. Treat as an
author-request target or reproduce from the AEA registry.

### Omae / Rising / Wieseler

These downloaded successfully but are not D-ready:

- Rising 2008: drug/NDA-level counts of FDA trials and published trials.
- Wieseler 2013: aggregate outcome-reporting completeness tables versus CSRs.
- Omae 2019: aggregate tables and regression supplements, no row-level effect
  table in the public supplements.

They are useful citations or context, not the main D-vs-N evidence.

### Hart/Lundh/Bero 2012 BMJ

Tried to access the BMJ article and supplementary path by command line. BMJ is
behind a Cloudflare challenge in this environment. Search snippets confirm the
study is conceptually useful but summarize meta-analysis-level changes after
adding FDA data; I did not obtain row-level trial effect/N files. Manual browser
download or author request is the next step.
