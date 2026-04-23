# Corpus Suggestion Tracker

Last updated: 2026-04-21

This is a living decision log for datasets suggested as inputs to the
published-paper `D` versus `N` project.

The target object is narrow:

1. Published original papers or original studies.
2. Paper/study identifiers.
3. Usable sample size `N`.
4. A statistic or effect estimate convertible to a Cohen-d-like `D`.
5. Broad enough `N` range for a log-log slope.
6. Preferably a main-treatment, primary-outcome, or treatment-of-interest flag.
7. Clear provenance: journal paper, registry, review extraction, replication, etc.

The working conversion for z-like results is:

```text
D = 2 * |z| / sqrt(N)
```

For standardized mean differences we use the native effect size where
appropriate. For log odds/risk/hazard ratios we use rough conversions only as
comparators. This is a boundary-plot diagnostic, not a claim that every source is
a clean two-arm independent-groups experiment.

## Status Legend

- `not tried`: Suggested but not yet downloaded/parsed locally.
- `blocked`: We tried access and hit a real obstacle.
- `worked`: We built an analyzable D-vs-N object locally.
- `working comparator`: Locally useful, but not the main published-paper target.
- `partial`: Some useful fields/rows exist, but the source is incomplete for the target.
- `rejected for main`: We have enough information to avoid it as a main corpus.

## Current Priority Queue: Still Needing Work After Normalization

Most of the high-value leads have now been downloaded, parsed, and normalized
into `data/derived/corpus_candidates/`. This queue is only for sources that
still need manual access, a deeper raw-data audit, or a second-pass parser to
answer the main published-paper D-vs-N question more cleanly.

| Rank | Source | Status | Why it is promising | Main caveat | First action |
|---:|---|---|---|---|---|
| 1 | DARPA SCORE / COS extracted claims | worked; parser caveats | Parser now yields 2,893 free-text claim rows plus 791 structured `orig_outcomes` rows with D/N. Paper-level slopes: free-text `-0.426`, structured `-0.317`; p<.10 shares about 97%. | Paper frame is stratified random, but the single-trace claim frame is explicitly a positive quantitative outcome tied to the abstract. This is not a random result within the paper. Many p-threshold rows are lower-bound D proxies. | Audit parser precision on a hand sample and decide whether to use free-text rows, structured rows, or both. |
| 2 | FORRT Replication Database / FReD | worked; parser caveats | Parser now yields 1,969 original-claim rows across 762 original-paper DOI units. Paper-level slope `-0.421`; p<.10 share about 94%. | Not a random journal-paper sample. Rows are original findings selected into replication projects/databases or submitted as replications, so this is a replication-target/focal-claim frame. Not all rows are treatment/intervention effects. | Audit effect-type conversions, especially p-only and eta-squared rows. |
| 3 | AACT x PubMed primary-outcome derivation | not started | Potentially large medical proxy: primary-outcome registry result rows linked to PMIDs. | It is registry-posted primary outcome data linked to articles, not journal-extracted article results; registry-publication disagreement is expected. | Build AACT query pipeline only if we accept it as a proxy/comparator, not as direct journal provenance. |
| 4 | Olivier 2024 cardiovascular RCT primary endpoints | author-request target | Very clean primary-endpoint cardiovascular RCT object; article reports 344 included trials and 263 superiority-trial effect-size rows. | Public supplements are methods/formulas plus a data-sharing statement; row-level data are by author request. | Draft author email requesting row-level data. |
| 5 | Rothwell/Julious/Cooper 2018 HTA RCT primary endpoints | author-request target | Clean continuous-primary-endpoint RCT object with observed effect size, achieved/evaluable N, p/CI fields. | Article appendix lists variables, but no linked row-level dataset; small and author request. | Draft author email requesting row-level data. |
| 6 | Allan 2017 cardiovascular RCT primary outcomes | partial/manual target | Primary cardiovascular outcomes in major journals; included-study supplement is local. | Public supplement gives citations/significance classification, not full numeric event/effect/N extraction table. | Reconstruct from articles or request extraction table. |
| 7 | Lawrence 2018 oncology phase III primary endpoints | partial/manual target | Phase III oncology primary OS/PFS/TTP endpoints; article confirms observed HR/p/CI extraction for 213 trials. | Public supplement only has aggregate framework cross-tabs, not row-level HR/N. | Reconstruct from articles or request extraction table. |
| 8 | Nadler 2024 oncology FDA approval endpoints | partial/manual target | FDA-approval oncology endpoints; article reports 75 approvals and 94 endpoints. | Public supplements are approval list and aggregate sensitivity/regression tables, not endpoint-level HR/N rows. | Author request or reconstruct from approval trial papers. |
| 9 | Wayant 2018 major-journal phase III RCT p-values | author-request target | Major-journal primary endpoints with N and p-values. | Article gives aggregate results only; p+N rather than signed D; row-level data not public. | Treat as p-boundary author request. |
| 10 | Szucs & Ioannidis 2017 cognitive neuroscience / psychology | row-level worked; grouping needed | 26,796 `t`/`df` rows normalized. | Paper/journal grouping is stored in MATLAB table-ish fields that still need decoding; not main-result selected. | Decode grouping so it can enter paper-level slopes rather than row-level only. |
| 11 | Yun et al. 2024 numerical RCT extraction | worked; selector needed | 401 usable published-RCT ICO rows normalized from arm counts or means/SDs. | Small, and primary outcome is not explicit. | Add first/main/primary ICO selector using Evidence Inference/SPIRIT cues. |
| 12 | Turner 2022 antidepressants | worked; join needed | 35 journal rows and 41 FDA regulatory rows normalized from S18. | Need tighter join to S13 publication/spin/classification flags. | Combine `s013` trial status with `s018` effect-size sheets. |
| 13 | NHGRI-EBI GWAS Catalog | worked comparator; excluded from strict journal-result set | 1,090,919 association rows normalized; paper-level slope `-0.470`. | Rows are curated genome-wide-significant association hits linked to papers, not sampled article-level journal results or treatment-of-interest rows. | Keep only as a threshold-selection comparator; add explicit genome-wide threshold curves if used. |
| 14 | metaBUS open subset | worked; N method caveat | 169,135 correlation rows normalized across 1,999 articles. | N is inferred as article-level median matrix N, not row-local pairwise N; not treatment effects. | Audit whether variable-level pairwise N can be recovered more exactly. |
| 15 | Havranek / meta-analysis.cz economics series | worked; dedup/filter needed | EIS, substitution, sigma, Armington, Frisch, and gasoline normalized. | Meta-analysis-mediated; EIS/substitution overlap and publication flags differ by dataset. | Deduplicate overlap and document working-paper/publication filters. |
| 16 | Nakagawa/Yang ecology and evolution | partial | Repos cloned, but processed files expose SE/variance rather than clean N. | May not support D-vs-N without raw constituent sample sizes. | Audit raw constituent folders for sample-size columns or mark as SE-only comparator. |
| 17 | AidGrade v1.5 development economics | partial | Public page only yielded v1.1 CSV with lower/ES/upper and citation fields. | No N/SE in public v1.1 file. | Find v1.5 or contact AidGrade; current file is not enough. |
| 18 | Brodeur et al. 2016 "Star Wars" economics | blocked | OpenICPSR file paths found, but command-line download attempts returned 403. | Even if downloaded, N may be absent. | Download manually through browser/account and inspect for sample size. |
| 19 | Fanelli, Costas & Ioannidis 2017 PNAS | blocked | PNAS direct supplement URLs returned 403; PMC supplement links hit NCBI proof-of-work page. | May overlap Cochrane and may not have primary-study N. | Download supplements manually in browser, then inspect. |
| 20 | Vorland et al. protocols/results dataset | blocked | JAMA page returned 403 to command-line access; no public data file found. | Not numeric D/N even if accessed. | Browser/manual supplement download or author email. |

## Direct Publication-Bias Denominator Leads

After reframing the target as *publication bias* rather than only a published
literature D-vs-N slope, the target object is stricter: a known denominator of
conducted/registered/regulatory/submitted studies, publication status, and an
effect/N pair for the same focal or primary outcome. The sources below are the
new direct-denominator pass.

Key local output from this pass:

- `data/derived/publication_bias_direct/direct_publication_bias_d_ready_rows.csv`
- `data/derived/publication_bias_direct/direct_publication_bias_d_ready_rows.parquet`

Current D-ready direct-denominator extraction: 1,280 raw D/N rows and 982
collapsed study-level rows. The strict explicit-journal-result subset is now
221 rows: 35 Turner 2022 newer antidepressant rows, 19 Turner 2012
antipsychotic rows, 46 Roest 2015 anxiety-disorder rows, and 121 Amarilyo 2016
rheumatoid-arthritis biologic rows. The broader published-status subset has
1,067 rows, mostly Cipriani plus the new Amarilyo FDA/journal pairs.

Current sampled published focal/key-result side:

- strict one-row-per-paper focal/key-effect units: 1,818 paper units
  - Kühberger 2014: 472
  - Linden 2024 focal: 158
  - Schäfer & Schwarz 2019 without preregistration: 682
  - Schäfer & Schwarz 2019 with preregistration: 89
  - Olsson & Sundell 2023 primary-outcome rows: 250
  - Esarey & Wu 2016 main findings: 167
- broader published focal/critical-test paper units: 1,941 if Motyl 2017
  critical hypothesized tests are included after paper-level collapse.

| Source | Status | What we found locally | Publication-bias usefulness | Caveat / next step |
|---|---|---|---|---|
| Cipriani GRISELDA 2018 antidepressants | worked; strongest open denominator | Downloaded Mendeley workbook. It has 522 StudyIDs and 1,199 arm rows with `Year_Published`, drug, randomized N, responders/remitters/dropouts, and continuous endpoint mean/SD/N. `Year_Published` includes `unpublished`: 93 unpublished StudyIDs and 429 published StudyIDs. Derived 410 response-based and 390 continuous active-vs-placebo D/N rows. | Best open row-level published-vs-unpublished treatment-effect denominator found so far. Median response-derived native d: published 0.308 vs unpublished 0.123; median continuous SMD: published 0.315 vs unpublished 0.141. | It is a network-meta-analysis extraction, not paired journal-vs-regulatory extraction for every trial. Multiple active arms/doses create multiple rows per trial; collapse rules still needed. |
| Turner 2022 antidepressants | worked | PLOS supplements already local. S13 has 104 trial rows with FDA positive/negative, journal outcome, publication, and spin fields. S18 has FDA and journal Hedges-g, SE, and drug/placebo N for newer antidepressants. Derived 41 FDA and 35 journal D/N rows from S18. | Clean small FDA-vs-journal calibration cohort. | Need join S13 status/spin to S18 effects and bring in older-trial effect tables where available. |
| Turner 2012 antipsychotics | worked via transcription | Downloaded PLOS supplements S1-S5 plus article table images. S2 and S3 contain trial-level FDA and journal Hedges-g with CIs. Article Table 1 contains arm N. Usable FDA-approved drug-vs-placebo Ns and publication status are transcribed into the parser. | Good Turner-style calibration outside antidepressants: 19 FDA/journal paired published rows and 4 FDA-only unpublished rows. | Active-comparator rows and split rows without clean Ns are skipped; keep skip log with the output. |
| Roest 2015 anxiety-disorder antidepressants | worked via transcription | Downloaded JAMA Psychiatry supplement, article table image, and figures. The table gives 57 FDA-reviewed trials and publication status; figures/supplement give FDA and journal Hedges-g with CIs. Usable N/effect rows are transcribed into the parser. | Best non-antidepressant Turner-style extension in the local build: 46 journal rows, 49 FDA/regulatory rows for published trials, and 8 FDA/regulatory unpublished rows. | Manual transcription should be audited before final publication. |
| Amarilyo et al. 2016 RA biologics | worked | Downloaded the public PLOS workbook and added a parser to `build_publication_bias_direct.py`. The two sheets expose FDA and journal arm-event counts and denominators for `ACR20` and `WdAE`. | Strong new paired FDA-vs-journal addition: 259 D-ready rows, including 121 journal rows, 135 FDA rows for published trials, and 3 FDA rows for unpublished trials. | Useful direct-provenance expansion, but not a broad publication-status denominator because almost all trials were published. |
| Lindner et al. 2018 rheumatoid-arthritis productivity | worked as scaffold | Downloaded the public PLOS supplement. | 114-row trial table with `NCT ID`, `PubMed ID`, positive/negative outcome coding, publication status, publication year, and citation/activity fields. | Real denominator/status scaffold, not numeric Type B. |
| Van Heteren et al. 2019 otology CT.gov publication-status dataset | worked as scaffold | Downloaded the public PLOS workbook. | 419 trial rows with registry ID, enrollment, results-posting status, dates, and study URL. | Real denominator/status scaffold, not numeric Type B. |
| Papageorgiou et al. 2017 orthodontic trial publication-status dataset | worked as scaffold | Downloaded the public PLOS workbook. | 80 trial rows with registry ID, enrollment, registration/publication timing, publication-status flags, and positive-result coding. | Real denominator/status scaffold, not numeric Type B. |
| Howard et al. 2017 neurology selective reporting bias audit | worked as tracker-only | Recovered the public Figshare files through the Figshare API after the plain download route had looked WAF-blocked. | Main workbook has a 186-row `Registry` sheet with registered primary/secondary outcomes and sample size, a 181-row `Publications` sheet with published outcomes and sample size in study, and a 186-row `Data` sheet with primary/secondary discrepancy flags and major-discrepancy counts. | Real public registry-vs-publication discrepancy audit. Useful tracker infrastructure, but not numeric Type B because there is no focal effect/test-statistic layer. |
| Wayant et al. 2017 hematology selective reporting bias audit | worked as tracker-only | Recovered the public Figshare files through the Figshare API after the direct route had looked WAF-blocked. | Workbook has a 110-row `Base Sheet` with funding, registry status, primary/secondary discrepancy flags, major-discrepancy indicator/count, and p-value significance fields. | Real public discrepancy-audit workbook and no longer a blocked lead. Still not D/N-ready because the released file has no effect-size/test-statistic layer. |
| Brodeur / Carrell / Figlio / Lusher 2023 JHR submissions | worked as z/p comparator; not D/N-ready | Downloaded the full openICPSR package and extracted the public de-identified files. `paper-estimate level data.dta` has 20,206 estimate rows over 540 initial manuscripts: 171 desk rejections, 207 referee rejections, and 162 accepted initial drafts. Rejected papers carry later-publication flags (`gs_publish` / `neverpub`), with 225 later published elsewhere and 153 never published. The package also includes `referee-estimate level data.dta`, the survey file `round2-final.dta`, and the thin Elliott-test CSV slices such as `accepted_final.csv`. | Strong submission-denominator design with test-statistic rows and accepted/rejected strata. | Public release is still only a de-identified z/p comparator, not a D/N source: the raw coefficient/SE + characteristic file is explicitly withheld in the README, and the public `awn` field behaves like an equal-paper weight rather than a true sample-size variable. |
| Chen 2019 registry-vs-publication primary outcomes | downloaded but not D-ready | Downloaded the JAMA Network Open supplement after solving the NCBI proof-of-work challenge. It contains search strategies, hit counts, and included-trial primary-outcome change classifications. | Very high-fit conceptually; article reports 338 quantitative RCTs and 487 registry-vs-publication comparisons. | Public supplement does not expose row-level OR/N data; author request or reconstruction needed. |
| Nordic trial reporting dataset | worked as scaffold | Cloned `cathrineaxfors/nordic-trial-reporting`. Final publication file has 2,112 eligible trials with manually adjudicated `has_publication`, DOI, PMID, publication date/type; trial sample has enrollment, NCT/EUCTR, phase/status. | Excellent publication-status denominator and validation scaffold for AACT/EUCTR. | README explicitly says they did not assess whether publications reported the registered primary outcomes. No effect sizes. Needs AACT/registry and article extraction layer. |
| IntoValue trial-publication linkage | worked as scaffold | Cloned `maia-sh/intovalue-data`. `trials.csv` has 3,788 rows, enrollment, NCT/DRKS IDs, DOI/PMID, publication type, summary-results flag, and publication timing. 2,621 rows have `publication_type = journal publication`; 511 have summary results. | Clean NCT/DRKS-to-PMID/DOI linkage scaffold. | No effect sizes or primary-outcome numeric extraction. |
| AEA RCT Registry | worked as denominator scaffold | Downloaded current registry CSV from `socialscienceregistry.org/site/csv`: 11,945 trials with status, primary outcomes, sample-size fields, PAP/data/program/relevant-paper fields. Dataverse snapshots are also accessible by API, but file download needs further API handling. | Best economics/social-science pre-publication denominator. | Registry has planned outcomes and sample sizes, but not publication-output coding or result effects. Need Leight/Asri/Imai output data or build searches/extraction. |
| Leight/Asri/Imai AEA publication-tracking paper | paper downloaded; data not found | Downloaded working paper PDF. It describes 898 field trials from 2013-2016, 85% with public output, about 60% peer-reviewed, and abstract-coded primary-outcome/null reporting. | Conceptually excellent direct publication-bias study for economics. | I found the paper and preanalysis OSF link, but not a public row-level output dataset. Likely author-request or not yet posted. |
| Rising 2008 FDA NDA cohort | downloaded but not D-ready | Downloaded PLOS Table S1. It lists NDAs, number of FDA trials, and number of published trials by drug. | Broad FDA approval-denominator context. | Supplement obtained so far is drug-level publication counts, not trial-level D/N. |
| Wieseler 2013 CSR-vs-public reporting | downloaded but not D-ready | Downloaded six PLOS supplement tables. They summarize completeness of outcome reporting in journal publications and registry reports versus CSRs. | Strong evidence about missing/incomplete outcome reporting. | Tables are aggregate reporting-completeness counts, not trial-level effect sizes. |
| Omae 2019 immune checkpoint inhibitors | downloaded but not D-ready | Downloaded BMC/PMC article and three supplements. Supplements are regression tables; article has aggregate table values. | Useful oncology FDA publication-status context. | No row-level effect/N table in supplements; not the D-ready table suggested by the external answer. |
| Olivier 2024 cardiovascular RCTs | downloaded but author-request only | Downloaded public JAMA Network Open supplements. They provide methods/formulas and a data-sharing statement. | Very high-fit primary-endpoint cardiovascular RCT anchor. | Row-level data are not public; request from corresponding author. |
| Rothwell 2018 HTA RCTs | article downloaded; author-request | Article reports 107 RCTs and lists extracted fields in the appendix. | High-fit continuous-primary-endpoint corpus. | No public row-level dataset linked. |
| Allan 2017 cardiovascular RCTs | downloaded but not D-ready | Downloaded BMC supplement. It is an included-study/significance list. | Useful reconstruction list. | Numeric extraction table absent from public supplement. |
| Lawrence 2018 oncology phase III RCTs | downloaded but not D-ready | Downloaded PMC article and supplementary DOCX after solving NCBI proof-of-work. | Article confirms 213 trials and observed primary-endpoint HR/p/CI extraction. | Public supplement only aggregate cross-tabs. |
| Nadler 2024 oncology FDA approvals | downloaded but not D-ready | Downloaded both Scientific Reports DOCX supplements. | Article reports 75 approvals and 94 endpoints. | Public supplements do not include endpoint-level HR/N rows. |
| Wayant 2018 major-journal phase III RCTs | article verified; author-request | Article reports 203 trials and 272 primary endpoint p-values with sample-size metadata. | Useful p+N threshold lead. | No public row-level supplement found; command-line JAMA access returned 403. |
| Hart/Lundh/Bero 2012 BMJ | blocked | BMJ article path returns a Cloudflare challenge in this environment. | Conceptually useful FDA-vs-published meta-analysis reanalysis. | Manual browser download or author request; likely meta-analysis-level, not direct trial D/N. |
| AACT x PubMed | not built yet | AACT remains the scalable biomedical denominator route; Nordic and IntoValue now provide better seed scaffolds. | Potentially the large direct publication-bias build. | Requires AACT database download/query plus publication linkage and journal/registry primary-outcome extraction. |

## Candidate Normalization Pass

`scripts/build_candidate_d_vs_n.py` now builds a shared row-level D/N file for
the newly acquired corpora. `scripts/analyze_candidate_d_vs_n.py` computes
paper-level log-log slopes and a comparison plot.

Key outputs:

- `data/derived/corpus_candidates/candidate_d_n_rows.csv.gz`
- `data/derived/corpus_candidates/candidate_d_n_papers.csv`
- `data/derived/corpus_candidates/candidate_d_n_corpus_summary.csv`
- `data/derived/corpus_candidates/candidate_d_n_loglog_slopes.csv`
- `reports/corpus_candidates/candidate_d_n_slopes.md`
- `reports/corpus_candidates/candidate_published_paper_d_vs_n.png`

Current build totals: 1,428,213 usable D/N rows, 220,631
published-original-candidate rows, 25,450 collapsed paper units, and 10,076
published-original-candidate paper units.

## Sampling-Frame Checks For The New Focal-Claim Corpora

The 97%+ p<.10 share in the new SCORE rows should not be interpreted as a
surprising consequence of randomly sampling arbitrary results from journal
articles.

### DARPA SCORE / COS

SCORE's article frame is strong: 3,900 papers were randomly sampled from
27,407 papers published from 2009 to 2018 in 62 social-behavioral journals.
The SCORE documentation describes this as a stratified random sample, with
stratification by journal and publication year.

The claim/result frame is much more selected. The SCORE program extracted
one claim trace per paper for most papers, and the working definition was a
specific finding supported by a statistically significant test result, or by
evidence amenable to statistical hypothesis testing. Later documentation is
even more direct: for most papers, SCORE extracted a single positive,
quantitative outcome associated with a claim in the abstract. For 200 papers
they also extracted a "bushel" of quantitative claims linked to abstract claims.

So the right interpretation is:

- Random/representative at the paper level.
- Selected/focal/positive at the claim level.
- Useful for "published paper abstract-linked positive claims."
- Not useful as "all tests in sampled papers" or "randomly sampled results."

Our parser results are consistent with that source design. Among raw
`extracted_claims.csv` rows with parseable coded p-values, about 96% are
significant at p<.05 and about 99.8% meet p<.10 when inequality-coded p-values
are handled as significant at their stated threshold.

### FORRT FReD

FReD has a different selection mechanism. It is a living replication database,
not a randomly sampled journal article corpus. Its paper describes the database
as aggregating and expanding large-scale replication attempts, public lists of
replications, and individual replications. Its inclusion criterion requires a
replication study to specify which original study it planned to replicate.

Each row represents a phenomenon/effect paired between an original finding and
a replication finding. That makes FReD closer to the question "what original
claims did replication projects choose to test?" than to "what do journal
articles report in general?"

The right interpretation is:

- Selected because someone attempted a replication.
- Usually focal, because replications target named findings.
- Not a random sample of papers, and not necessarily a random sample of effects
  within the original paper.
- Good focal-claim comparator, but not a publication-bias sampling frame by
  itself.

In the raw FReD file, about 83% of original findings with parseable p-values
are significant at p<.05 and about 88% meet p<.10. Our D/N-normalized subset is
more selected again, because it keeps rows with enough numeric information to
compute D.

## Worked Or Useful Locally

These sources produced local outputs or are useful comparators. They are below
the untried priority queue because we already know what they can and cannot do.

| Source | Status | What we actually did | Result | Current decision |
|---|---|---|---|---|
| Kühberger, Fritz & Scherndl 2014 psychology main-question results | worked | Downloaded the PLOS ONE article and `pone.0105825.s002.sav`, then added a parser to `build_candidate_d_vs_n.py`. The SAV exposes one article-level result row with sample size, p-value, z-value, converted `r`, analysis category, and psychology subfield labels. | 472 usable D/N rows, one row per paper code. Paper-level slope `-0.381`; median paper `D = 0.723`, median paper `N = 94`. | Best new published-only Type A cloud from this sprint. It directly addresses the main-result problem that makes statcheck/Szucs too permissive. The public SAV lacks DOI/title/journal metadata, so local `paper_id` uses the source code only. |
| Linden, Pollet & Hönekopp 2024 focal-vs-random psychology sample | worked | Downloaded the PLOS ONE article, crawled the OSF project via API, pulled `ATJ_Study2_ESs_and_Ns.sav`, and added parser support for focal and random effect rows from 160 sampled papers. | 158 usable focal rows and 158 usable random rows. Focal paper-level slope `-0.320`; random paper-level slope `-0.202`. Median focal `D = 0.63`, `N = 83.5`; median random `D = 0.54`, `N = 82.0`. | Strong Type A validation set. It shows the slope gets steeper when effect selection is focal rather than random, which is exactly the objection to arbitrary-test corpora. Keep focal as a published-original candidate and random as an internal comparator. |
| Schäfer & Schwarz 2019 key-question effect corpus | worked | Queried the OSF API for node `t8uvc`, downloaded the public XLSX/CSV files, and added parser support for both non-preregistered and preregistered samples. | Non-preregistered: 682 usable rows from 900 sampled papers, paper-level slope `-0.316`, median paper `D = 0.772`, median paper `N = 68.5`. Preregistered: 89 usable rows from 93 papers, slope `-0.287`, median paper `D = 0.327`, median paper `N = 268`. | Strong new Type A focal/key-result corpus. It materially expands the published focal-result side and confirms that public row-level reusable data do exist for at least some sampled psychology article audits. |
| Motyl et al. 2017 critical hypothesized tests | worked with caveat | Queried the OSF API for node `he8mu`, downloaded `ScienceStatus_C.csv`, `ListofArticles.xlsx`, `CodingNotes.pdf`, and the analysis script, then added a cautious parser. Coding notes say coders captured the primary analysis for the hypothesized effect. | 1,305 usable study-level D/N rows across 540 paper units after parsing sample size, copied statistics, effect-size text, and exact p-values. Paper-level slope `-0.300`; median paper `D = 0.614`, median paper `N = 93.75`. | Useful published focal/critical-test expansion, but not a strict one-row-per-paper headline-result corpus because papers can contribute multiple study-level critical tests. Treat as a broader Type A-adjacent corpus with explicit caveat. |
| Olsson & Sundell 2023 Swedish social interventions | worked conservatively | Downloaded the public PLOS workbook and added a parser that keeps only rows with numeric `Nanalys`, uses reported `Cohens_d`, and treats coder-flagged primary outcomes as published-original candidates. | 476 usable D/N rows with 250 primary-outcome paper units and 226 nonprimary comparator rows. Paper-level slope for the primary-outcome subset is `-0.452`; median paper `D = 0.431`, median paper `N = 89`. | Real new social-intervention published-result corpus, but it is being treated cautiously because the workbook lacks full bibliographic metadata and not every row is coded as a primary outcome. |
| Esarey & Wu 2016 political-science main findings | worked | Downloaded the author ZIP/PDF, extracted `publication_data_2016-5-29.dta`, and added a parser that follows the authors' own `model == 1` and `number_of_dv == 1` restriction. | 167 usable D/N rows and 167 paper units. Paper-level slope `-0.413`; median paper `D = 0.233`, median paper `N = 722`. | Strong new non-psychology Type A corpus with one main-finding row per paper and DOI/journal/year metadata. |
| CliniFact published primary pairs | worked as conservative medical expansion | Reused the existing derived pair table `data/derived/publication_bias_direct/clinifact_publication_registry_pairs.csv` and added a builder to `build_candidate_d_vs_n.py`. The builder keeps only `plausible_result_report` rows with `pair_quality` in `{high, medium}` plus nonmissing journal-side `N` and p-derived `D`, then chooses one row per PMID using only extraction-quality and match-quality signals: pair quality, metric-family agreement, journal p/N provenance, sentence score, and combined match score. | 339 usable D/N rows and 339 paper units. Median paper `D = 0.331`, median paper `N = 215`, median `|z| = 2.61`. This lifts the plotted `Medicine / Clinical` bucket from 123 to 462 papers and raises its median paper `N` from 137 to 200.5. | Keep as a published medical-paper source, but describe it narrowly: it is a conservative journal/registry-primary-outcome proxy derived from already-local CliniFact bridge outputs, not a standalone public row release. |
| Reproducibility Project: Psychology converted data | partial / overlap cross-check | Downloaded the public CSV/XLSX export with original and replication fields. | 168 replication-target rows, 158 unique original titles, rich original-study columns (`N.O`, p-values, parsed test statistics, converted `T.r.O`). | Real public dataset, but it overlaps FReD heavily and should not be merged without a global dedupe key. |
| ReplicationSuccess package data (`RProjects`, `SSRP`, `protzko2020`) | partial / overlap cross-check | Downloaded the CRAN tarball and extracted the packaged `.rda` objects. | `RProjects`: 143 rows; `SSRP`: 21 rows; `protzko2020`: 80 rows, all with original/replication effect-size and sample-size fields. | Useful for validation and crosswalks across replication projects, but not a clean net-new corpus relative to FReD/RPP. |
| Szucs & Ioannidis 2017 cognitive neuroscience / psychology | worked row-level | Downloaded PLOS Biology S1 Data `.mat`, S1 code, and S1 table; normalized `tvalues`/`df`. | 26,796 usable row-level D/N rows; median `D = 1.07`, median `N = 21`. Paper/journal grouping still needs MATLAB-table decoding. | Keep as row-level comparator now; high-priority grouping task for paper-level slope. |
| NHGRI-EBI GWAS Catalog | worked comparator; rejected for main | Downloaded full associations ZIP/TSV plus studies and ancestry TSVs; parsed p-values and initial sample-size strings. | 1,090,919 association rows; 6,711 PMID paper units; paper-level slope `-0.470`, median paper `D = 0.166`, median paper `N = 4,944`. | Not a strict peer-reviewed journal-result corpus: the rows are catalog-curated significant associations, not article-level treatment/main-result samples. |
| Havranek / meta-analysis.cz economics series | worked | Downloaded EIS, substitution, sigma, Armington, Frisch, and gasoline files; normalized estimates/t-stats and observation counts. | Several datasets now produce paper-level slopes: EIS/substitution `-0.510`, Armington `-0.664`, gasoline `-0.751`, Frisch extensive `-0.418`. | Strong economics expansion; needs overlap deduplication and publication-filter documentation. |
| Yun et al. 2024 / `llm-meta-analysis` | worked | Cloned GitHub repo and normalized binary 2x2 rows plus continuous mean/SD rows. | 401 usable ICO rows from 85 PMCIDs; paper-level slope `-0.326`, median paper `D = 0.290`, median paper `N = 77`. | Best small medical published-RCT pilot; next step is main/primary ICO selection. |
| MetaLab developmental psychology / child language | worked | Cloned `metalabr`, downloaded `metalab.Rdata`, exported with R, and filtered rows with `d` and `n`. | 926 usable rows, 202 study IDs; peer-reviewed rows marked as published candidates; paper-level slope `-0.325`. | Useful developmental psychology comparator, not medicine. |
| metaBUS open Bosco subset | worked | Downloaded open JAP/Personnel Psychology workbook; converted correlations to D and assigned article-level median matrix N. | 169,135 rows across 1,999 articles; paper-level slope `-0.121`, median paper `D = 0.377`, median paper `N = 181`. | Published management/I-O corpus; not treatment effects and N is article-level inferred. |
| DellaVigna & Linos 2022 nudge economics | worked | Found Econometrica article page, downloaded `18709_Data_and_Programs.zip`, and normalized Stata files. | Academic-journal subset: 73 rows, 27 papers, paper-level slope `-0.463`, median paper `D = 0.141`, median paper `N = 1,146`. | Good small published-vs-at-scale calibration set. |
| Turner 2022 antidepressants | worked | Downloaded PLOS Medicine supplements and normalized S18 FDA/journal sheets. | Journal subset: 35 rows, 23 publication units, median `D = 0.295`; FDA comparator: 41 rows. S13 status/spin join remains. | Good small psychiatry publication-filter calibration set, too small for stable slope. |
| Button/Nord neuroscience | worked | Followed OSF link from the Nord reanalysis article and normalized the effect-size workbook. | 688 usable rows; 649 paper/study units; paper-level slope `-0.382`, median paper `D = 0.213`, median paper `N = 107`. | Useful small neuroscience sanity-check corpus. |
| Reproducibility Project: Cancer Biology | working comparator | Used OSF API for node `e5nvr`; downloaded paper-, experiment-, and effect-level CSVs. | Effect-level data include original and replication sample sizes, test statistics, p-values, effect sizes, SEs, and CIs. | Very small biomedical replication comparator, not a main corpus. |
| Finer-grained CT.gov results KG / Shi et al. | working comparator | Cloned GitHub repo, listed Figshare collection, downloaded full `efficacy_df.csv`. | 119,968 efficacy rows from 8,665 NCT IDs; 23,252 primary outcome rows; enrollment, p-values, CIs, parameter values, arm mapping. | Excellent registry comparator; not published-journal data. |
| CliniFact primary-outcome publication benchmark | working comparator | Cloned `CliniFact`, inspected the processed publication dataset, built `scripts/build_clinifact_ctgov_bridge.py` to join it to the parsed CT.gov KG by NCT ID and outcome/arm similarity, built `scripts/build_clinifact_publication_numeric_extract.py` for abstract-side journal numerics, built `scripts/build_clinifact_publication_registry_pairs.py` for direct paired journal-vs-registry rows, built `scripts/build_clinifact_pair_audit_queue.py` for manual follow-up, added `scripts/triage_clinifact_pair_audit_queue.py` to strip obvious non-comparable abstract matches, and refreshed `scripts/build_clinifact_pmc_fulltext_extract.py` so stale PMC challenge pages are refetched from alternate PMC URL variants before classification. | 1,970 rows, 992 unique `nctId`, 1,540 unique `PMID`. The bridge yields 1,319 best-match rows from 718 overlapping NCT IDs; 1,317 are on CT.gov primary outcomes and 1,286 have registry p-values plus D proxies. The journal-side pass keeps 738 result-PMID rows, classifies 668 as plausible result reports, and extracts 477 journal p-values, 539 abstract-selected N values, 364 journal D proxies from abstract p+N, 162 CIs, and 117 effect estimates. The paired file contains 668 plausible rows, including 431 with paired p-values and paired D proxies and 74 with matched effect families. The raw audit queue contains 357 high/medium-priority rows, but the triage pass cuts that to 42 cleaned manual-audit rows and 152 likely non-comparable rows. The refreshed PMC pass materially improved the local ceiling: all 16 PMCID-backed rows now yield article-like PMC HTML, 16 yield full-text p-values, 4 resolve toward the registry result, and 2 more reduce the journal-registry `D` gap, leaving 35 unresolved rows overall. | Strong NCT-PMID bridge with a first-pass journal-side abstract numeric layer, an explicit publication-vs-registry pair table, a cleaned audit queue, and a materially better local full-text resolution pass. The remaining gap is now mostly non-PMC full text or rows with no PMCID/public OA route, not stale PMC challenge pages. |
| SPIRIT-CONSORT-TM | working comparator | Used OSF API for node `8rg4h`; downloaded core corpus tables and term-level files. | Article/sentence/term data for protocol/results publication pairs, including reporting-item labels and PMCIDs. | Strong primary-outcome/reporting selector, not numeric D/N data. |
| Evidence Inference | working comparator | Cloned GitHub repo and inspected annotations. | Prompt files link PMCID to intervention/comparator/outcome; annotations provide directional labels and evidence spans. | Useful selector/training data, not standalone D/N. |
| Trialstreamer | working comparator | Listed Zenodo record 6669532 and downloaded a few PubMed update CSVs. | Rows include PMID, title, abstract, PICO strings, `num_randomized`, punchline text, journal, DOI. | Broad published-RCT sampling frame; requires numerical extraction. |
| Schimmack & Bartos medical p-values OSF Y3GAE | working comparator | Used OSF API, downloaded RDS/R files, inspected with R. | `analysis_data.RDS` has 19,751 p-values with PMID, journal, year, and RCT/CT flags; no N. | Published medical p-value comparator only; not D-vs-N. |
| statcheck psychology papers, 1985-2013 | worked | Downloaded OSF statcheck CSV; parsed `t`, `F(1, df)`, `r`, and chi-square rows; converted to `D`/`N`; collapsed to one row per paper. | 13,889 papers; 163,574 tests; median `N = 62`; median `D = 0.723`; slope `-0.443`; 86.9% above `p < .05` curve. | Core published reported-results corpus. Strong evidence for boundary-hugging, but not main-treatment-only. |
| Brodeur/Cook/Hartley/Heyes 2024 economics Dataverse | worked | Downloaded raw `.dta`; used `myz`/`zstat` and row-level `observations`; converted to `D = 2|z|/sqrt(N)`; collapsed to one row per paper; then pulled the same parser into the shared candidate build. | 217 papers; 10,071 tests; median `N = 2000`; median `D = 0.071`; slope `-0.418`; 33.6% above `p < .05` curve. In the shared published-paper field rollup, this lifts `Economics` from 490 to 707 papers and raises its median paper `N` from 270 to 704. | Useful published-econ comparator and now part of the shared candidate corpus, but still not the same as a strict main-result economics sample. |
| BEAR combined database | working comparator | Built `D_abs_best` where possible and audited every BEAR corpus for D, publication status, treatment-of-interest, and usable filters. | Many rows can get D, but most BEAR corpora are registry, review, replication, scrape, or meta-analysis objects. | Use as comparator/search index, not main backbone. |
| BEAR Cochrane source-type split | working comparator | Used BEAR's Cochrane `group` source type: `published`, `mixed`, `sought`, `unpublished`; focused on SMD/continuous rows. | Published SMD rows have median `|b| ~= 0.405`, slope about `-0.317`; mixed/unpublished do not show dramatic different slope in this slice. | Useful provenance comparator, not strict journal-only corpus. |
| OSF Schwab / van Zwet Cochrane effects line | partial | Used public Cochrane effect rows as baseline object for provenance question. | Good effect/SE/z object, but old extract lacks first-class row-level publication status or numeric-source field. | Useful baseline; insufficient alone for published-vs-unpublished provenance. |
| Local Cochrane RevMan/data-package downloads | partial | Parsed local `.rm5` and ZIP files under `data/raw/cochrane_packages`; extracted numeric rows, study source flags, and references where present. | 10 package files parsed; 501 exact package-to-CDSR raw-data matches; among exact matches, 441 journal-likely/published-only, 57 mixed, 3 nonjournal/unpublished. | Promising for Cochrane provenance, but too small and version-mismatched so far. |
| Current Cochrane/RevMan data packages generally | working comparator | Confirmed the direct route is parsing legally downloaded statistical data packages, not scraping Cochrane pages. | Modern packages expose analysis rows, study data, source flags, and RIS references; legacy `.rm5` files often lack references. | Strong provenance-comparator path, not main published-paper object. |
| ClinicalTrials.gov / AACT through BEAR | working comparator | Used BEAR clinicaltrials rows as registry comparator. | Registry primary-outcome rows with `N`; median `D ~= 0.277`. | Excellent less-filtered comparator, not published-paper main corpus. |
| COMPare Trials Project | working comparator; mined further | Downloaded the public Google Sheets CSV export, then used the assessment URLs in that sheet to bulk-fetch per-trial assessment spreadsheets and parse them into a tidy local outcome table with `scripts/build_compare_trials_assessment_rows.py`. I also downloaded the `Trials` 2019 supplement tracker and materialized it as `data/derived/corpus_candidates/compare_trials/compare_trials_trials2019_tracker.csv`. | Master sheet: 72 trial audits with title, journal, report/registry/protocol URLs, prespecified primary/secondary outcome counts, correct-reporting counts, novel-outcome counts, and letter workflow fields. Assessment layer: 59 public sheets recovered locally (45 direct export URLs plus 14 recovered from Drive-style links), 8 auth-gated sheets still inaccessible, and 1,171 parsed outcome rows in `data/derived/corpus_candidates/compare_trials/compare_trials_outcome_rows.csv` split into 89 prespecified-primary, 660 prespecified-secondary, and 422 non-prespecified publication outcomes. The supplement-backed tracker adds a clean 67-row formal table with assessment URLs, final outcome-count fields, and letter workflow metadata. | Strong public outcome-switching audit infrastructure for already-published trials. Still not D-ready and not a full conducted-study denominator, but now substantially better than a bare trial tracker because there is both a reusable outcome-level corpus for the accessible assessments and a formal supplement-backed tracker for all 67 published trials. |
| Twomey et al. 2021 kinesiology positive-result audit | working comparator | Queried the OSF API for node `nwcx6` and downloaded `raw_coding.csv`, `df_all.csv`, and the analysis materials. | `df_all.csv` is a 300-row article-level table with one DOI per row, support coding, sample size `n`, p-value reporting type/threshold fields, preregistration/open-data flags, and clinical-trial/RCT labels. `raw_coding.csv` has 900 coder-level rows across the same 300 articles. | Strong public Bucket 1 audit dataset and a partial Type A comparator. Keep it out of the main D/N build because the public table stores p-value-format metadata and relative thresholds, not a numeric exact p/test statistic. |
| Lancee et al. 2017 antipsychotic outcome-reporting audit | working comparator | Downloaded the Springer supplementary bundle. The `MOESM433` XLSX turned out to be a small wording crosswalk, while the useful public content is in `MOESM434`-`436` DOCX tables. | Real public registry-vs-publication discrepancy audit with study reference, NCT number, antipsychotic type, publication sample size, funding, region, and primary/secondary discrepancy flags. | Keep as a discrepancy-audit tracker, not a D/N source. The external memo overstated the XLSX as if it were the main tidy numeric dataset. |
| Aczel et al. 2018 null-hypothesis support audit | worked as comparator | Queried the OSF API for node `f2n7c`, downloaded `data.csv`, `Non-significant table.xlsx`, and `analysis.Rmd`, then added a strict parser based on the authors' own analyzable subset rule. | Public table has 175 negative-statement/statistic rows from 137 papers. Restricting to one-sample, paired-samples, and independent-samples t-tests with nonmissing `t` and `N1` yields 62 usable D/N rows across 30 paper units; paper-level slope `-0.491`, median paper `D = 0.176`, median paper `N = 54.5`. | Useful labeled comparator for negative-claim t-tests. It is intentionally excluded from the main published-focal count because the selection rule is narrow and centered on nonsignificant claims rather than general headline results. |
| Farrar et al. 2023 animal-cognition nonsignificant-result audit | working comparator | Queried the OSF API for node `gdp6f` and downloaded `AnimalCogNHSTData.xlsx`, `NHSTanalysis.R`, and the coding guide. | Cleaned workbook has 303 article rows after skipping the repeated header line, with title/abstract/result no-effect coding, result p-value fields, agreement/decision columns, and inclusion flags. | Strong public Bucket 1 audit dataset for nonsignificant-result interpretation. No sample-size field was found, so it is tracker-only rather than a D/N source. |
| Edelsbrunner & Thurn 2024 education nonsignificant-result audit | working comparator | Queried the OSF API for node `b3f68` and downloaded `Codings_analytic_share.xlsx`, the README, and the reproducible syntax file. | `ModelData` has 528 hypothesis rows from 50 education articles with non-significance, two misinterpretation codings, implication coding, and rater fields; `Overlap` has the overlap-check rows. | Public row-level article-audit dataset. Useful Bucket 1 evidence that sampled audits were released openly, but there is no N/effect layer for D/N. |
| Showell et al. 2023 ANZCTR publication-status dataset | working comparator | Downloaded the public PLOS workbook and inspected the registration-level publication and sample-size sheets. | Real public denominator/publication-status scaffold with about 1,980 registrations and a separate sample-size sheet. | Useful as TESS-like publication-status infrastructure, but not a numeric Type B corpus because it lacks effect/test-statistic rows. |
| Moniz-Druckman-Freese 2025 TESS file-drawer dataset | working comparator | Queried the Harvard Dataverse API for DOI `10.7910/DVN/MHE7QH`, downloaded `TESS_applicants.tab` and `README.txt`, and verified the dataset bundle. | 544 researcher-project rows. Fields include accepted/declined status, write-up, journal submission, publication, top-journal placement, and `sig_find_strict`, plus researcher covariates. | Strong public social-science denominator/publication-status dataset. It is a real Bucket 3 asset, but it does not expose study-level N or numeric effect/test statistics, so it stays out of the D/N build. |
| EU Clinical Trials Register / EUCTR through BEAR | working comparator | Used BEAR EUCTR rows as registry comparator. | Registry endpoint rows with `N`; median `D ~= 0.273`. | Comparator only. |
| WWC education through BEAR | partial | Audited BEAR WWC rows. | Intervention findings with D/N; median `D ~= 0.149`; not journal-only and multiple outcomes per study. | Useful nonmedical intervention comparator. |
| Many Labs 2 through BEAR | working comparator | Audited as replication sanity check. | Median `D ~= 0.147`, median `N = 93`. | Good realistic-effects comparator, not original published literature. |
| Open Science Collaboration through BEAR | working comparator | Audited as replication sanity check. | Median `D ~= 0.335`, median `N = 71`. | Good replication comparator. |
| Bartos exercise through BEAR | partial | Audited BEAR rows. | RCT exercise intervention meta-meta rows; median `D ~= 0.281`, median `N = 44`. | Usable with caveats; not strict published-paper primary-result corpus. |
| Metapsy psychotherapy through BEAR | partial | Audited BEAR rows. | Psychotherapy RCT database rows; median `D ~= 0.548`, median `N = 58`. | Useful treatment-domain comparator, but no strict published-only/main-result flag. |
| Barnett/Wren biomedical CI scrape through BEAR | partial | Used rough log-ratio-to-D conversion. | Huge published biomedical CI source; median `D ~= 0.357`, but no sample size and no treatment/main-outcome flag. | Background comparator only unless `N` can be recovered. |
| Costello/Fox ecology through BEAR | partial | Audited because it had high median D. | Median `D ~= 0.771`; no usable `N` in our D-vs-N sense; meta-analysis effect rows. | Do not compare directly to statcheck as published-paper evidence. |
| Yang ecology/evolution through BEAR | partial | Audited BEAR Yang rows. | Median `D ~= 0.473`; raw release may be more useful if it exposes `N`. | Keep as a lead to raw Nakagawa/Yang data. |
| Arel-Bundock political science through BEAR | partial | Used BEAR row-level `z`/`N` proxy. | Median `D ~= 0.174`, median `N = 492`; meta-analysis-derived political science estimates. | Weak for target; possible comparator. |
| Nuijten intelligence through BEAR | partial | Audited BEAR rows. | Median `D ~= 0.255`, median `N = 60`. | Weak for target; psychology/intelligence comparator only. |
| Sladekova psychology through BEAR | partial | Audited BEAR rows. | Median `D ~= 0.464`, median `N = 102`; Fisher-z style effects. | Weak for target; no published-only/focal-treatment flag. |
| psymetadata through BEAR | partial | Audited BEAR rows. | Median `D ~= 0.294`, median `N = 65`. | Weak for target; heterogeneous meta-analysis package. |

## Blocked Or Rejected For The Main Corpus

These are at the bottom because they have already failed the main published
paper D-vs-N requirement, or because access blocked the exact intended source.
Some remain useful as background or supplements.

| Source | Status | Why it is not the main corpus | Remaining use |
|---|---|---|---|
| Brodeur et al. 2016 "Star Wars" economics | worked as p/t comparator | Downloaded the full OpenICPSR package and recovered the previously missing `Data/Temp/export_from_r.dta`, `Data/Final/final_stars_supp.dta`, and the raw article-extraction CSVs. `final_stars_supp.dta` has 50,078 extracted statistics across 641 journal/article groups with coefficient, standard-deviation, t-statistic, p-value, `main` flag, and article/table count weights. | Strong published-economics test-statistics corpus. | Still not D/N-ready because there is no verified study-level sample-size field, only test-statistic extractions and article/table counts. |
| Fanelli, Costas & Ioannidis 2017 PNAS | blocked | Direct PNAS supplementary URLs returned 403, PMC links returned a JavaScript proof-of-work page, and PMC OA utility says the article is not in the OA package. | Manual supplement download, then inspect whether primary-study N exists. |
| Vorland et al. protocols / main-results publication dataset | blocked | JAMA Network Open returned 403 to command-line access and no public data file was located by search. It is also not numeric D/N data. | Browser/manual supplement download or author email; use only for missing-results context. |
| Older Brodeur "Methods Matter" / OpenICPSR file | worked as same recovered package | The older OpenICPSR target turned out to be the recovered 2016 Brodeur/Le/Sangnier/Zylberberg replication package. | Useful as a published-economics p/t comparator. | No further OpenICPSR chase needed here unless a separate sample-size-bearing file exists. |
| Brodeur/Cook/Heyes old draft economics slice | still blocked for exact source | The 2016 package is now local, but the exact later top-25-journal RCT/RDD/DiD/IV slice with usable sample-size information is still not locally available. | Keep temporary replacement as Brodeur 2024 for D/N work. |
| GESIS PubBias / coded submissions and publications | blocked by access gate | Resolved the GESIS dataset record for DOI `10.7802/2942`, downloaded the landing HTML and JSON-LD metadata, and verified named distribution URLs under `access.gesis.org`. | The schema record explicitly lists `PubBias_Analysis dataset.dta`, `PubBias_Raw dataset.xlsx`, the codebook, coding scheme, Stata prep code, and log file. The sharing URLs return HTTP 403 without a GESIS login. | Real file-backed denominator dataset, but not anonymously downloadable. Keep as the strongest yes-login Bucket 3 lead rather than treating it as open-public infrastructure. |
| Gechert-Havranek-Irsova-Kolcunova capital-labor substitution sigma | partial | The meta-analysis.cz sigma file is now local and has `sigma`, `se`, `t`, `nobs`, study ID, and publication/year fields. | Covered by the Havranek parser target rather than treated as a separate blocked source. |
| Havranek household-panel EIS micro subset | partial | EIS/substitution files are now local and have estimate, SE, observations, study ID, publication/year fields. | Covered by the Havranek parser target. |
| Schimmack/Bartos abstract-scraped medical z-values | rejected for main | OSF Y3GAE is now local and has published medical p-values with PMID/journal/RCT flags, but no reliable `N`. | Background p/z comparator only. |
| Chavalarias PubMed p-value scrape through BEAR | rejected for main | Published biomedical p-values, but no D/N in BEAR and no main-treatment flag. | p-curve/z-distribution background only. |
| Head et al. PubMed/Open Access p-values through BEAR | rejected for main | Published p-values, but no `N` and no main-treatment flag. | Background p-curve comparator. |
| Jager/Leek top medical journal abstracts through BEAR | rejected for main | Published medical abstract p-values, but no `N`/`D`; only crude title RCT flag possible. | Background medical p-value comparator. |
| Askarov economics through BEAR | rejected for BEAR version | BEAR lacks sample size, so no D-vs-N from BEAR alone. | Revisit raw inputs if needed. |
| Brodeur economics through BEAR | rejected for BEAR version | BEAR lacks sample size; our separate raw Brodeur 2024 file is better. | Use raw Dataverse instead. |
| Cochrane as primary published-paper corpus | rejected for main | Cochrane's unit is a review-extracted study/effect row, not one journal paper; it intentionally aggregates across source types. | Strong source-provenance comparator. |
| AACT / ClinicalTrials.gov as primary published-paper corpus | rejected for main | Registry source, not journal-published article source. | Less-filtered comparator and NCT-linked validation. |
| EUCTR as primary published-paper corpus | rejected for main | Registry source, not journal-published article source. | Less-filtered comparator. |
| Trialstreamer alone | rejected as numeric corpus | Sampling frame and PICO/result text, not ready numeric effect-size table. | Pair with numerical extraction. |
| Evidence Inference / EBM-NLP alone | rejected as numeric corpus | Directional labels and prompts, not enough effect-size-plus-N rows. | Selector/training/evaluation corpus. |
| SPIRIT-CONSORT-TM alone | rejected as numeric corpus | Reporting-item annotations, not numeric effects. | Primary-outcome/result-location validation. |
| Andrews & Kasy 2019 package | rejected for now | Bundles meta-study datasets but primary-study `N` coverage may be incomplete. | Low priority. |
| Ioannidis, Stanley & Doucouliagos 2017 EJ | rejected for now | No single clean public per-study release; would require stitching many component meta-analyses. | Low priority unless economics gap remains. |
| Pereira, Horwitz & Ioannidis 2012 JAMA | rejected for main | Sources from Cochrane. | Cochrane-adjacent background only. |
| DellaVigna & Pope 2018 | rejected for main | Single megastudy, not a literature corpus. | Conceptual comparator only. |
| Franco, Malhotra & Simonovits 2014 | rejected for main | Categorical result strength, not continuous effect-size-plus-N rows. | File-drawer context only. |
| OpenTrials / EBM DataLab / related trial transparency resources | rejected for main | Useful provenance infrastructure, not direct effect-size-plus-N corpus. | Trial linkage/provenance context. |
| Gerber & Malhotra 2008 | rejected for main | Publication-bias analysis, not a ready D-vs-N source. | Background citation. |
| Senior et al. 2016 ecology | rejected for main | Meta-analysis-level rather than study-level. | Low priority. |

## Full BEAR Dataset Inventory

This mirrors the local BEAR audit so every BEAR corpus is named explicitly. The
detailed notes live in `data/derived/bear/bear_corpus_tractability_audit.md`.

| BEAR dataset | Domain | Rows | D status | Median D | Median N | Tracker decision |
|---|---|---:|---|---:|---:|---|
| Cochrane | medicine & health | 39768 | yes_all_rows | 0.346 | 87 | best_available_in_bear |
| ManyLabs2 | psychology | 1414 | yes_all_rows | 0.147 | 93 | not_published_papers_but_good_sanity_check |
| OSC | psychology | 99 | yes_all_rows | 0.335 | 71 | not_published_papers_but_good_sanity_check |
| clinicaltrials | clinical trials | 41338 | yes_all_rows | 0.277 | 172 | not_published_papers_but_good_toi |
| euctr | clinical trials | 8651 | yes_most_rows | 0.273 | 181 | not_published_papers_but_good_toi |
| Chavalarias | biomedicine | 7935864 | no |  |  | not_usable |
| Head | biomedicine | 2010875 | no |  |  | not_usable |
| JagerLeek | biomedicine | 15653 | no |  |  | not_usable |
| Askarov | economics | 21408 | no |  |  | not_usable_without_raw_inputs |
| Brodeur | economics | 8424 | no |  |  | not_usable_without_raw_inputs |
| Bartos | exercise | 2239 | yes_all_rows | 0.281 | 44 | usable_with_caveats |
| Metapsy | psychotherapy | 4395 | yes_all_rows | 0.548 | 58 | usable_with_caveats |
| WWC | education | 12045 | yes_all_rows | 0.149 | 440 | usable_with_caveats |
| ArelBundock | political science | 16649 | yes_all_rows | 0.174 | 492 | weak_for_target |
| BarnettWren | biomedicine | 1306551 | yes_all_rows | 0.357 |  | weak_for_target |
| CostelloFox | ecology & evolution | 88218 | partial | 0.771 |  | weak_for_target |
| Nuijten | intelligence | 2439 | yes_all_rows | 0.255 | 60 | weak_for_target |
| Sladekova | psychology | 11540 | yes_all_rows | 0.464 | 102 | weak_for_target |
| Yang | ecology & evolution | 17638 | partial | 0.473 |  | weak_for_target |
| psymetadata | psychology | 8514 | yes_all_rows | 0.294 | 65 | weak_for_target |

## Local Artifacts

- Published-paper pipeline: `scripts/build_published_paper_d_vs_n.py`
- Published-paper output: `data/derived/published_papers/published_original_paper_d_vs_n.csv`
- Published-paper summary: `data/derived/published_papers/published_original_paper_d_vs_n_summary.md`
- BEAR tractability audit: `data/derived/bear/bear_corpus_tractability_audit.md`
- BEAR D values: `data/derived/bear/bear_d_values.csv.gz`
- BEAR Cochrane source-type analysis: `data/derived/bear/cochrane_bear_source_summary.md`
- Cochrane package pilot: `data/derived/package_probe_summary.md`
- Acquisition sprint log: `reports/acquisition/corpus_acquisition_log.md`
