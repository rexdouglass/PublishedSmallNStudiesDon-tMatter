# Next Search Brief

Last updated: 2026-04-20

This is the current handoff brief for the next external search pass. The goal
is to avoid re-searching generic publication-bias literature and instead target
the specific missing data objects.

## What We Need

There are two distinct targets.

### Type A: Published Focal-Result Cloud

A random or transparent sample of peer-reviewed journal articles where each row
is the paper's focal or main result, with enough information to compute `D`
and `N`.

### Type B: Direct Publication-Bias Denominator

A known denominator of conducted, registered, submitted, or regulatory studies,
plus publication status and a focal or primary outcome with enough information
to compute `D` and `N`. Best case is a paired journal-versus-registry/FDA/CSR
row for the same study and same primary outcome.

## What We Already Have

### Published Focal-Result Side

- `Kuhberger 2014`: 472 usable paper-level main-question rows.
- `Linden 2024 focal`: 158 usable focal-effect rows.
- `Schäfer & Schwarz 2019 without preregistration`: 682 usable key-question rows.
- `Schäfer & Schwarz 2019 with preregistration`: 89 usable key-question rows.
- `Motyl 2017 critical hypothesized tests`: 1,305 usable study-level rows across
  540 paper units after paper-level collapse.
- `Linden 2024 random`: 158 usable random-effect rows.

These solve the old complaint that statcheck/Szucs-style corpora are full of
arbitrary reported tests. We now have a real published-only focal/key-result
sample.

Strict one-row-per-paper focal/key-effect total: 1,401 paper units
(`Kuhberger + Linden focal + Schäfer without prereg + Schäfer with prereg`).

Broader focal/critical-test total: 1,941 paper units if `Motyl 2017` is
counted after paper-level collapse.

### Direct Denominator Side

- `direct_publication_bias_d_ready_rows.csv`: 1,021 raw rows.
- `direct_publication_bias_study_collapsed_rows.csv`: 723 study-collapsed rows.
- Strict explicit journal-result rows: 100 total.
  - Roest 2015: 46
  - Turner 2012: 19
  - Turner 2022: 35
- Cipriani GRISELDA adds a larger published-vs-unpublished antidepressant trial
  denominator, but it is a meta-analysis extraction rather than clean paired
  journal-vs-regulatory data.

### CliniFact x CT.gov Bridge

This is the main local denominator scaffold now.

- 1,970 CliniFact claim-publication rows
- 992 unique NCT IDs
- 718 NCT overlaps with parsed CT.gov rows
- 1,319 best-match publication-registry rows
- 1,317 on CT.gov primary outcomes
- 1,286 with registry p-values and registry-side D proxies

Journal-side abstract extraction now gives:

- 738 result-PMID rows
- 668 plausible result-report rows
- 477 journal p-values
- 539 abstract-selected sample sizes
- 364 journal D proxies from abstract p+N
- 162 confidence intervals
- 117 effect estimates

Paired journal-vs-registry file:

- 668 plausible publication-registry rows
- 431 with paired journal and registry p-values
- 431 with paired journal and registry D proxies
- 74 with matched journal/registry effect families
- significance agreement: 0.807 at `p < .05`, 0.803 at `p < .10`

Triage pass:

- 412 high/medium pair rows triaged
- 42 cleaned manual-audit rows
- 152 likely non-comparable rows
- 33 cleaned rows still significance-discordant at `p < .05`
- 23 cleaned rows with `abs_d_delta >= 0.25`

Interpretation: the broad bridge now exists. The remaining gap is not linkage.
The remaining gap is journal-side numeric extraction or public paired row-level
datasets.

PMC full-text pass on the 42-row cleaned queue:

- 16 rows have PMCID
- only 5 yield article-like PMC HTML
- 11 PMCID rows hit PMC challenge pages
- 26 rows have no PMCID
- 5 rows yield full-text p-values
- 2 rows resolve toward the registry result after full text
- 2 rows still support the abstract-side disagreement after full text
- 1 row gets a larger gap after full text

Interpretation: the local PMC route is mostly exhausted. The remaining missing
data are mostly outside PMC or behind challenge-blocked access.

### Public Audit Infrastructure

- `COMPare Trials Project`: verified public row-level audit CSV with 72
  published-trial assessments and fields for trial/journal URLs, protocol and
  registry links, counts of prespecified outcomes, counts correctly reported,
  novel outcomes, and letter-publication workflow.

Interpretation: this is useful public outcome-switching infrastructure, but it
is not D-ready and not a true conducted-study denominator.

## What We Have Already Tried And Why It Fell Short

These are known partials or dead ends unless someone can point to a real row-
level release:

- `Olivier 2024`: public supplement is methods plus data-sharing statement; row
  table appears to be author-request only.
- `Rothwell 2018`: article describes the extracted variables, but no public row
  table was found.
- `Chen 2019`: public supplement does not expose the claimed row-level OR/N
  comparisons.
- `Allan 2017`: public supplement is mainly included-study/significance list.
- `Lawrence 2018`: public supplement has aggregate ASCO/ESMO cross-tabs, not
  row-level HR/N.
- `Nadler 2024`: public supplements list approvals and aggregate sensitivity
  tables, not endpoint-level HR/N rows.
- `Wayant 2018`: article clearly had row-level p+N, but no public release found.
- `Riveros 2013`, `Hartung 2014`, `Schwartz 2016`, `Chan 2004`: conceptually
  excellent, but we have not found a public row-level numeric release.
- `Leight/Asri/Imai`: excellent economics denominator paper, but no public row-
  level output dataset found.
- `TESS`: useful file-drawer mechanism cohort, but we have not found a public
  row-level effect-size/N table.

## What Not To Suggest Again

Do not send generic:

- p-value scrape corpora
- Trialstreamer alone
- AACT alone
- ClinicalTrials.gov alone
- GWAS Catalog
- Cochrane pooled rows
- generic meta-analysis corpora
- generic replication corpora

Those are useful comparators or scaffolds, but they do not answer the missing
question unless they come with a concrete row-level path to focal journal
results or a pre-publication denominator.

## Highest-Value Search Targets

### Priority 1: Public Row-Level Paired Journal-vs-Registry/FDA Data

Please look specifically for row-level downloadable files, supplements, or
archived replication packages for:

1. `Chen et al. 2019`
2. `Riveros et al. 2013`
3. `Hartung et al. 2014`
4. `Schwartz et al. 2016`
5. `Chan et al. 2004`

The question is not whether these papers exist. It is whether the row-level
numeric tables were ever posted somewhere public:

- journal supplement
- institutional repository
- OSF
- Figshare
- Zenodo
- Dryad
- Dataverse
- author website
- GitHub repo

### Priority 2: High-Fit Author-Request Datasets

Find direct author-contact paths or hidden data deposits for:

1. `Olivier 2024`
2. `Rothwell 2018`
3. `Allan 2017`
4. `Lawrence 2018`
5. `Nadler 2024`
6. `Wayant 2018`

What matters:

- corresponding author email
- explicit data availability statement wording
- whether row-level data were deposited somewhere outside the article
- whether a replication package exists under a different title

There is now also a local author-request batch with the contacts we were able
to confirm:

- `reports/author_request_targets_2026-04-20.md`

### Priority 3: Economics / Social-Science Denominator Datasets

Look for public row-level data for:

1. `Leight / Asri / Imai` publication-tracking of AEA RCT registry studies
2. `TESS` publication-bias / file-drawer datasets with effect sizes and sample
   sizes, not just publish/writeup categories
3. journal-submission denominator datasets that include effect sizes or focal
   results, not only editorial outcomes

## What A Good Answer Looks Like

For each candidate, report:

1. Exact dataset or supplement name.
2. Direct URL to the file, not just the paper.
3. Number of row-level studies or rows.
4. Whether it is Type A or Type B.
5. Whether it includes unpublished or nonpublished studies.
6. Whether it includes peer-reviewed publication status.
7. Whether it includes focal or primary results.
8. Whether it includes N.
9. Whether it includes effect, z, p, CI, SE, or raw arm-level data.
10. Whether the journal and registry/FDA/CSR results are paired.
11. Exact useful columns.
12. Why it does or does not satisfy the target.

## Paste-Ready External Search Prompt

I am looking for row-level datasets that either:

1. give a random or transparent sample of peer-reviewed journal articles with a
   focal/main result plus N and effect/test statistic, or
2. give a direct publication-bias denominator: conducted/registered/regulatory
   studies plus publication status and a primary/focal result with N and
   effect/test statistic.

I already have broad published-only comparators and registry scaffolds. Do not
suggest generic p-value scrapes, Trialstreamer alone, AACT alone,
ClinicalTrials.gov alone, GWAS Catalog, Cochrane pooled rows, or generic
meta-analysis corpora unless you can point to a concrete row-level path to
focal journal results or a real denominator cohort.

Current local state:

- Published focal-result datasets already found:
  - Kuhberger 2014: 472 paper-level main-question rows
  - Linden 2024 focal: 158 rows
  - Linden 2024 random: 158 rows
- Direct denominator rows already found:
  - 1,021 raw rows
  - 723 study-collapsed rows
  - 100 strict explicit journal-result rows from Roest 2015, Turner 2012, and
    Turner 2022
- CliniFact x CT.gov bridge already built:
  - 1,319 publication-registry best matches
  - 668 plausible publication-result rows
  - 431 paired journal and registry p-value rows
  - 42 cleaned manual-audit rows after triage
  - PMC pass on those 42 rows:
    - 16 with PMCID
    - 5 with usable article-like PMC HTML
    - 11 PMC challenge/blocked
    - 26 without PMCID
    - 2 locally resolved toward registry
    - 40 still unresolved

The missing thing is not another generic publication-bias literature review.
The missing thing is one of:

- a public row-level paired journal-vs-registry/FDA/CSR primary-outcome table,
- a public row-level primary-endpoint extraction table from a paper that already
  did the work,
- a way to access article-level numeric results for the 40 unresolved cleaned
  CliniFact rows that are outside usable PMC full text,
- or a denominator dataset in economics/social science with publication status,
  focal outcomes, N, and numeric effects.

High-priority targets:

- Chen 2019
- Riveros 2013
- Hartung 2014
- Schwartz 2016
- Chan 2004
- Olivier 2024
- Rothwell 2018
- Allan 2017
- Lawrence 2018
- Nadler 2024
- Wayant 2018
- Leight/Asri/Imai
- TESS with numeric outcomes

For each candidate, give the direct data URL, row count, whether it is Type A
or Type B, whether it has publication status, whether it has focal/primary
results, whether it has N, whether it has effect/z/p/CI/SE/raw data, and
whether journal and registry/FDA results are paired.
