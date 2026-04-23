# Author Request Targets

Last updated: 2026-04-20

This is the immediate author-request batch for the high-fit papers whose public
supplements do not expose the row-level data we need.

A quick repository search in this pass did not turn up obvious OSF/Figshare/
Zenodo/Dryad row-level deposits for the top JAMA/Trials targets, so author
request is now the pragmatic next move rather than more blind supplement
hunting.

## What To Ask For

The ideal request is for a row-level table with one study/trial/endpoint per
row, including as many of these fields as exist:

- study or trial identifier
- publication identifier (PMID/DOI/title/year)
- primary endpoint or focal outcome name
- sample size or arm-level sample sizes
- effect estimate (HR/OR/RR/MD/SMD/Hedges g)
- standard error, p-value, CI, or raw arm-level event/mean/SD counts
- any publication-status or source-provenance flags

## Priority Targets

### 1. Olivier et al. 2024

- Article: *Accuracy of Event Rate and Effect Size Estimation in Major Cardiovascular Trials: A Systematic Review*
- Journal: JAMA Network Open
- Why high value:
  - major cardiovascular RCTs
  - primary endpoints
  - explicit event-rate/effect-size extraction
  - reported 344 included trials, 263 superiority-trial effect-size rows
- What is missing publicly:
  - row-level trial table
- Corresponding author (official JAMA page):
  - Christoph B. Olivier
  - `christoph.olivier@universitaets-herzzentrum.de`

### 2. Chen et al. 2019

- Article: *Comparison of Clinical Trial Changes in Primary Outcome and Reported Intervention Effect Size Between Trial Registration and Publication*
- Journal: JAMA Network Open
- Why high value:
  - direct registry-versus-publication comparison
  - 338 quantitative RCTs
  - 487 registry/publication comparisons
  - study explicitly says it extracted sample sizes and comparable effect measures
- What is missing publicly:
  - row-level OR/N or arm-level comparison table
- Corresponding authors (official JAMA page/search result):
  - Chao Li
  - `lcxjtu@xjtu.edu.cn`
  - Tao Chen
  - `tao.chen@lstmed.ac.uk`

### 3. Rothwell, Julious & Cooper 2018

- Article: *A study of target effect sizes in randomised controlled trials published in the Health Technology Assessment journal*
- Journal: Trials
- Why high value:
  - continuous primary endpoints
  - achieved/evaluable N
  - observed effect size
  - p-values and confidence intervals
- What is missing publicly:
  - row-level table
- Contact emails recovered from the official Springer page HTML:
  - J. C. Rothwell: `j.c.rothwell@sheffield.ac.uk`
  - Sarah A. Julious: `s.a.julious@sheffield.ac.uk`
  - Cindy L. Cooper: `c.l.cooper@sheffield.ac.uk`

### 4. Allan et al. 2017

- Article: *Are potentially clinically meaningful benefits misinterpreted in cardiovascular randomized trials? A systematic examination of statistical significance, clinical significance, and authors’ conclusions*
- Journal: BMC Medicine
- Why high value:
  - major-journal cardiovascular RCTs
  - primary outcomes
  - public supplement confirms included-study list
- What is missing publicly:
  - row-level event/effect/N extraction table
- Contact recovered from the official Springer page HTML:
  - Michael Allan
  - `michael.allan@ualberta.ca`

### 5. Nadler et al. 2024

- Article: *Magnitude of effect and sample size justification in trials supporting anti-cancer drug approval by the US Food and Drug Administration*
- Journal: Scientific Reports
- Why high value:
  - oncology approval trials
  - primary DFS/PFS/MFS/OS endpoints
  - article reports endpoint-level HR/N extraction
- What is missing publicly:
  - row-level endpoint table
- Contact recovered from the official Nature page HTML:
  - Michelle Nadler
  - `michelle.nadler@uhn.ca`

## Secondary Targets

These remain useful. Two now have a corresponding-author lead, but the rest
still need a clean contact lookup:

### Lawrence et al. 2018

- Article: *Effect Sizes Hypothesized and Observed in Contemporary Phase III Trials of Targeted and Immunological Therapies for Advanced Cancer*
- Journal: JNCI Cancer Spectrum
- Why high value:
  - 213 oncology phase III trials
  - article states that observed primary-endpoint HR/p/CI data were extracted
- What is missing publicly:
  - row-level HR/N table
- Corresponding author recovered from the Oxford page/search snippet:
  - Nicola Lawrence
  - `nicola.lawrence@sydney.edu.au`
  - NHMRC Clinical Trials Centre, University of Sydney

### Wayant et al. 2018

- Article: *Evaluation of Lowering the P Value Threshold for Statistical Significance From .05 to .005 in Previously Published Randomized Clinical Trials in Major Medical Journals*
- Journal: JAMA
- Why high value:
  - 203 major-journal RCT articles
  - 272 primary endpoints
  - article explicitly extracted p-values and sample-size metadata
- What is missing publicly:
  - row-level p+N table
- Corresponding author recovered from the PMC version:
  - Cole Wayant
  - `cole.wayant@okstate.edu`

### Still Missing Clean Contact Capture

- Riveros 2013
- Hartung 2014
- Schwartz 2016
- Chan 2004
- Leight / Asri / Imai

## Paste-Ready Email

Subject: Request for row-level trial data from [paper title]

Hello [name],

I am working on a meta-research project on effect sizes, sample size, and
publication bias. Your paper, [paper title], is one of the closest matches we
have found to the exact object we need.

I wanted to ask whether you would be willing to share the row-level extraction
table underlying the paper. The most useful version would be one row per
study/trial/endpoint, with any of the following fields that exist:

- study or trial identifier
- primary/focal endpoint name
- sample size or arm-level sample sizes
- effect estimate (for example HR, OR, RR, MD, SMD, or Hedges g)
- p-value, confidence interval, or standard error
- publication metadata such as PMID/DOI/year

We are not looking for patient-level data. A derived extraction sheet or the
analysis-ready table used for the paper would be sufficient.

If it helps, we are happy to cite the paper and document the provenance of the
shared table explicitly.

Thank you,

[name]
