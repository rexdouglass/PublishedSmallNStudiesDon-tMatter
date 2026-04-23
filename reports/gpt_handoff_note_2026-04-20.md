# GPT Handoff Note

Last updated: 2026-04-20

This note is a standalone handoff for the next GPT search pass. It is long on
purpose. The goal is to stop wasting cycles on generic publication-bias
literature and instead search against the actual missing data object.

## What We Are Actually Trying To Build

We are not just trying to show that published small studies have inflated
effects. We are trying to build datasets that support one or both of these
tasks:

### Type A: Published Focal-Result Cloud

A transparent sample of peer-reviewed journal articles where each row is the
paper’s focal or main result and includes enough information to compute sample
size `N` and an effect or test statistic that can be normalized to something
like:

```text
D = 2 * |z| / sqrt(N)
```

For Type A, published-only is fine. This does **not** measure the file drawer
directly, but it does answer:

- what the selected published literature looks like,
- whether focal published results have a steep negative `D`-vs-`N` slope,
- whether small published studies report implausibly large effects.

### Type B: Direct Publication-Bias Denominator

A known denominator of conducted, registered, submitted, or regulatory studies,
plus publication status and a primary/focal result with enough information to
compute `N` and an effect/test statistic. Best case is a paired row comparing:

- registry / FDA / CSR / protocol / less-filtered result
- versus
- peer-reviewed journal result

for the same study and same primary outcome.

This is the object needed to measure the selection process rather than only the
selected literature.

## What Counts As Success

For a dataset to be genuinely useful, it should have as many of these as
possible:

1. one row per study/trial/paper/result,
2. clear identifiers: DOI, PMID, NCT ID, EudraCT, FDA trial ID, etc.,
3. sample size `N` or arm-level sample sizes,
4. effect estimate, test statistic, p-value, CI, SE, or raw arm-level data,
5. focal / primary / headline / treatment-of-interest result rather than an
   arbitrary secondary test,
6. peer-reviewed publication status if it is a denominator cohort,
7. source provenance: journal article, registry, FDA, CSR, etc.

## What We Already Have That Actually Worked

The local work is now in much better shape than it was at the start. We are no
longer stuck with only arbitrary test-statistic clouds and tiny Turner-style
examples. We now have:

1. a real published-only focal-result sample,
2. a real direct-denominator sample,
3. a registry-to-publication bridge with numeric fields,
4. a cleaned unresolved set that defines the real remaining gap.

### 1. Published Focal-Result Sample: This Worked

#### Kuhberger, Fritz & Scherndl 2014

This is the best new published-only Type A dataset we found.

It is a random psychology-paper sample where they tried to code one result per
paper answering the main research question rather than scraping arbitrary tests
from the results section. That makes it much more relevant than statcheck or
Szucs-style corpora for the “what does the selected focal-result literature
look like?” question.

Current local result:

- 472 usable paper-level rows
- one main-question result per paper code
- slope about `-0.381`
- median `D ≈ 0.723`
- median `N ≈ 94`

Why it matters:

- it directly answers the objection that published-only corpora like statcheck
  are full of arbitrary tests,
- it is article-level,
- it is focal-result selected,
- it is public and locally parsed.

What it does **not** do:

- it is not a denominator cohort,
- it is psychology, not medicine,
- it is not treatment-only.

Still, it worked and should stay in the stack.

#### Linden, Pollet & Honekopp 2024

This is the best validation companion to Kuhberger.

What makes it valuable is not the size, it is the design: it distinguishes
focal effects from random effects within sampled psychology papers. That lets
us directly test whether focusing on the paper’s central effect changes the
`D`-vs-`N` relationship.

Current local result:

- 158 focal rows
- 158 random rows
- focal slope about `-0.320`
- random slope about `-0.202`
- focal effects have larger median `D` than random effects at similar `N`

Why it matters:

- it confirms that the slope gets steeper when you use focal results rather
  than arbitrary reported effects,
- it validates the concern about statcheck/Szucs-type published corpora,
- it gives a useful sanity check for future Type A datasets.

What it does **not** do:

- it is not a denominator cohort,
- it is not medical,
- it is still small.

### 2. Direct Publication-Bias Denominator: This Worked, But It Is Still Small

Current direct-denominator outputs:

- `data/derived/publication_bias_direct/direct_publication_bias_d_ready_rows.csv`
- `data/derived/publication_bias_direct/direct_publication_bias_study_collapsed_rows.csv`

Current counts:

- 1,021 raw D/N rows
- 723 study-collapsed rows
- 100 strict explicit journal-result rows

Breakdown of the strict journal-result rows:

- Roest 2015: 46
- Turner 2012: 19
- Turner 2022: 35

That is the hard truth: the strict paired journal-result subset is still tiny.

#### Cipriani GRISELDA 2018

This is currently the strongest open denominator dataset.

Why it worked:

- row-level arm data,
- published and unpublished trial status,
- randomized N,
- responder counts,
- continuous endpoint means/SDs,
- enough to compute active-vs-placebo effects.

Current local result:

- 522 StudyIDs
- 1,199 arm rows
- published and unpublished trial flags via `Year_Published`
- hundreds of active-vs-placebo effect rows from response and continuous data

Why it matters:

- it gives a real published vs unpublished contrast,
- it is open,
- it has enough numeric structure to compute effect size and N.

What it does **not** do:

- it is a meta-analysis extraction, not a clean paired FDA-vs-journal table for
  every trial,
- multiple dose arms create multiple rows per study,
- it is antidepressants only.

Still, this is one of the very few things that genuinely gives a denominator
plus numeric outcomes in public form.

#### Turner 2022 newer antidepressants

This worked and is conceptually very strong.

Why it worked:

- public PLOS supplements,
- FDA and journal effect sizes,
- standard errors and sample sizes,
- publication/spin/status fields in accompanying supplement tables.

Current local result:

- 41 FDA/regulatory rows
- 35 journal rows

What it is good for:

- small but very clean FDA-vs-journal calibration,
- direct publication-bias evidence,
- source-provenance comparison.

What it does **not** do:

- enough rows for a stable broad slope,
- enough breadth beyond psychiatry.

#### Turner 2012 antipsychotics

This worked through manual transcription from public tables/figures.

Current local result:

- 19 FDA/journal paired published rows
- 4 FDA-only unpublished rows

Why it matters:

- another Turner-style regulatory-vs-journal cohort,
- outside antidepressants,
- still public enough to reconstruct.

Limitation:

- transcription-dependent,
- small,
- antipsychotics only.

#### Roest 2015 anxiety-disorder antidepressants

This also worked through public article/supplement transcription.

Current local result:

- 46 journal rows
- 49 FDA/regulatory rows for published trials
- 8 FDA/regulatory rows for unpublished trials

Why it matters:

- very similar logic to Turner,
- a real published-vs-unpublished denominator within FDA-reviewed trials,
- one of the cleanest small direct-bias calibration sets we have.

Limitation:

- still small,
- psychiatry-specific,
- transcription should eventually be audited.

### 3. Registry-to-Publication Bridge: This Worked Better Than Expected

This is the most important engineering result from the latest pass.

The bridge is not a final corpus, but it is no longer hypothetical. We now have
a real intermediate object linking registry-side primary outcomes to published
articles and first-pass journal-side numerics.

Core outputs:

- `clinifact_ctgov_bridge_best_matches.csv`
- `clinifact_publication_numeric_extract.csv`
- `clinifact_publication_registry_pairs.csv`
- `clinifact_publication_registry_clean_audit_queue.csv`
- `clinifact_pmc_fulltext_extract.csv`

#### CliniFact x CT.gov bridge

Current counts:

- 1,970 CliniFact claim-publication rows
- 992 unique NCT IDs
- 1,540 unique PMIDs
- 718 exact NCT overlaps with parsed CT.gov rows
- 1,319 best-match rows
- 1,317 best matches on CT.gov primary outcomes
- 1,286 best matches with registry p-values and D proxies

This means we now have a registry-side primary outcome row with linked PMID for
a large subset of trials.

That is the real denominator scaffold.

#### Abstract-side journal numeric extraction

We then extracted first-pass journal-side numerics from the publication-linked
abstracts.

Current counts:

- 738 result-PMID rows
- 668 plausible result-report rows
- 477 journal p-values
- 539 abstract-selected sample sizes
- 364 journal D proxies from abstract p+N
- 162 confidence intervals
- 117 effect estimates

Important detail:

CliniFact rows with `claim_support_label = no_info` are not result PMIDs. They
are background references. We explicitly excluded those. That cleaned up the
bridge substantially.

#### Paired journal-vs-registry comparison file

Current paired counts:

- 668 plausible publication-vs-registry rows
- 431 rows with paired journal and registry p-values
- 431 rows with paired journal and registry D proxies
- 74 rows with matched journal/registry effect families

Agreement:

- significance agreement at `p < .05`: about `0.807`
- significance agreement at `p < .10`: about `0.803`

Interpretation:

This is a real paired scaffold, but abstract-only numerics are noisy.

### 4. Audit Queue: This Worked, And It Clarified The Real Bottleneck

The raw disagreement queue was badly inflated by garbage:

- objective sentences,
- methods sentences,
- endpoint-description sentences,
- baseline-only within-group sentences,
- wrong-outcome sentence picks,
- multi-p-value ambiguity,
- conclusion paraphrases with no numeric result.

We built a triage layer to strip those out.

Current triage result:

- 412 high/medium pair rows triaged
- 42 cleaned manual-audit rows
- 152 likely non-comparable rows
- 33 cleaned rows still discordant at `p < .05`
- 23 cleaned rows with `abs_d_delta >= 0.25`

This changed the whole search problem.

Before triage, it looked like we needed a better bridge. After triage, it
became clear that the bridge exists and the real remaining problem is access to
article-level numeric results.

### 5. PMC Full-Text Pass: This Mostly Established The Ceiling

We tried one more local step on the 42-row cleaned queue: full-text enrichment
through PMC.

Current result:

- 42 rows in
- 16 rows have PMCID
- only 5 yield article-like PMC HTML
- 11 PMCID rows hit challenge pages
- 26 rows have no PMCID
- 5 rows yield full-text p-values
- 2 resolve toward the registry result
- 40 remain unresolved

Unresolved split:

- 26 `no_pmc_fulltext`
- 11 `pmc_access_blocked`
- 2 `supports_abstract_disagreement`
- 1 `larger_gap_after_fulltext`

Interpretation:

This is important because it tells us the local route is mostly exhausted.
After the bridge, abstract parse, triage, and PMC pass, most of what remains is
not a parsing problem. It is an access problem or a missing-public-data
problem.

## What We Tried That Did Not Deliver Public Row-Level Data

This is the part GPT needs to take seriously. We have already looked at many
papers that sound perfect conceptually. The main issue is that the public
supplements usually do **not** include the row-level trial table.

### Olivier et al. 2024

Why it looked promising:

- major cardiovascular RCTs,
- primary endpoints,
- event-rate and effect-size estimation,
- 344 trials, 263 superiority-trial effect-size rows,
- JAMA Network Open, open access.

What actually happened:

- public supplements are methods/formulas plus a data-sharing statement,
- row-level data are by author request,
- no public CSV was found.

Verdict:

- conceptually excellent,
- not public row-level data.

### Rothwell, Julious & Cooper 2018

Why it looked promising:

- HTA RCTs,
- continuous primary endpoints,
- achieved/evaluable N,
- observed effect size,
- p-value and CI fields explicitly described.

What actually happened:

- article appendix lists extracted variables,
- no public row-level data file linked,
- appears to be author-request only.

Verdict:

- excellent fit,
- no public row table found.

### Chen et al. 2019

Why it looked promising:

- direct registry-versus-publication primary outcome comparison,
- 338 quantitative RCTs,
- 487 comparisons,
- sample size and effect comparisons clearly described.

What actually happened:

- public supplement does not expose the row-level comparison table,
- it has search strategy and classification material,
- no public OR/N or arm-level rows found.

Verdict:

- one of the most important targets conceptually,
- still not a public row-level dataset.

### Allan et al. 2017

Why it looked promising:

- major-journal cardiovascular RCTs,
- primary outcomes,
- event/effect extraction described.

What actually happened:

- public supplement mostly gives included-study/significance list,
- no row-level event/effect/N table.

Verdict:

- good reconstruction lead,
- not plug-and-play.

### Lawrence et al. 2018

Why it looked promising:

- 213 oncology phase III trials,
- observed primary-endpoint HR/p/CI data reportedly extracted.

What actually happened:

- public supplement is aggregate cross-tabs only,
- no row-level HR/N table.

Verdict:

- conceptually very good,
- not public row-level.

### Nadler et al. 2024

Why it looked promising:

- FDA-approval oncology trials,
- 75 approvals, 94 endpoints,
- endpoint-level design and effect-size logic.

What actually happened:

- public supplements list approvals and aggregate sensitivity tables,
- no endpoint-level row table.

Verdict:

- context, not a usable table.

### Wayant et al. 2018

Why it looked promising:

- major-journal RCTs,
- primary endpoints,
- p-values and sample-size metadata.

What actually happened:

- article clearly extracted row-level p+N,
- no public row-level supplement found.

Verdict:

- still a good lead,
- but no public data found.

### Riveros 2013, Hartung 2014, Schwartz 2016, Chan 2004

These are conceptually excellent because they compare registry/protocol/FDA
information to published reports.

What actually happened:

- we have article-level evidence they did the relevant work,
- we have not found public row-level numeric files.

Verdict:

- still high-value search targets,
- but currently unresolved.

## What Did Not Work Conceptually Even When Data Existed

This is equally important. Some datasets are large and usable for some
questions, but they do **not** solve the missing problem.

### Generic p-value scrape corpora

Examples:

- PubMed abstract p-value scrapes,
- Chavalarias / Head / Barnett-Wren / similar biomedical p-value corpora.

Why they fail:

- often no `N`,
- not focal results,
- often not treatment effects,
- published-only,
- no denominator.

### statcheck / Szucs-style corpora

Why they fail for the focal-result question:

- rows are arbitrary reported tests,
- can include controls, manipulation checks, robustness tests, placebo tests,
  subgroup tests, nuisance coefficients,
- not main treatment results.

They are still useful comparators, but GPT should not present them as solving
the focal-result problem.

### GWAS Catalog

Why it fails:

- a catalog of association hits,
- threshold-selected,
- not a sample of article focal treatment results,
- not a denominator.

### Cochrane / review-derived rows

Why they fail:

- review extraction is not the same as a peer-reviewed journal article result,
- source provenance is mixed,
- not article-level publication-bias denominator.

### Generic meta-analysis corpora

Why they fail:

- second-hand selection via meta-analyst inclusion,
- often mixed publication types,
- often no clean journal-result provenance,
- no conducted-study denominator.

### Trialstreamer alone / AACT alone / CT.gov alone

Why they fail:

- useful scaffolds,
- not enough by themselves.

Without journal-side extraction or publication tracking, they do not answer the
actual question.

## What The Search Should Focus On Now

At this point, the search should be much narrower.

Do **not** search for “publication bias datasets” in the abstract. That route
mostly returns:

- generic literature reviews,
- p-value scrape corpora,
- replication corpora,
- meta-analysis databases,
- registry-only or review-only objects.

Instead, search for one of these three exact missing objects.

### Search Target 1: Public row-level paired journal-vs-registry / FDA / CSR tables

Highest-priority targets:

1. Chen 2019
2. Riveros 2013
3. Hartung 2014
4. Schwartz 2016
5. Chan 2004

What to look for:

- journal supplement PDFs with tables hidden in appendices,
- Figshare / Zenodo / Dryad / OSF / Dataverse / GitHub,
- institutional repositories,
- mirrored supplements,
- file names that do not match the paper title exactly.

### Search Target 2: Public row-level primary-endpoint extraction tables from papers that already did the work

Highest-priority targets:

1. Olivier 2024
2. Rothwell 2018
3. Allan 2017
4. Lawrence 2018
5. Nadler 2024
6. Wayant 2018

What to look for:

- repositories outside the article page,
- data deposits mentioned only in data-availability statements,
- supplemental XLS/XLSX/CSV with non-obvious names,
- institutional repository mirrors,
- journal-hosted but non-indexed attachments.

### Search Target 3: Economics / social-science denominator datasets

Highest-priority targets:

1. Leight / Asri / Imai AEA output tracking
2. TESS file-drawer / publication-bias datasets with numeric outcomes and N
3. journal-submission denominator datasets that include effect sizes or focal
   outcomes, not only accept/reject status

## What A Good GPT Answer Should Look Like

For each candidate, GPT should report:

1. exact dataset or supplement name,
2. direct data URL, not just paper URL,
3. number of rows or studies,
4. whether it is Type A or Type B,
5. whether it includes unpublished/nonpublished studies,
6. whether it includes peer-reviewed publication status,
7. whether it includes focal/primary results,
8. whether it includes `N`,
9. whether it includes effect/z/p/CI/SE/raw data,
10. whether journal and registry/FDA/CSR values are paired,
11. exact useful columns,
12. why it does or does not satisfy the target.

## Paste-Ready Prompt For GPT

I am looking for row-level datasets that solve one of two problems:

1. a published-only focal-result cloud: a random or transparent sample of
   peer-reviewed journal articles where each row is the paper’s focal/main
   result, with N and an effect/test statistic;
2. a direct publication-bias denominator: conducted/registered/regulatory
   studies with publication status and a primary/focal result, with N and an
   effect/test statistic, ideally paired between journal and registry/FDA/CSR.

Do not suggest generic p-value scrapes, Trialstreamer alone, AACT alone,
ClinicalTrials.gov alone, GWAS Catalog, Cochrane pooled rows, or generic
meta-analysis corpora unless you can point to a concrete row-level path to
focal journal results or a real denominator cohort.

Current local state:

- Published focal-result datasets already found:
  - Kuhberger 2014: 472 paper-level main-question rows
  - Linden 2024 focal: 158 rows
  - Schäfer & Schwarz 2019 without preregistration: 682 rows
  - Schäfer & Schwarz 2019 with preregistration: 89 rows
  - Motyl 2017: 1,305 usable study-level critical-test rows across 540 paper units
  - Linden 2024 random: 158 rows
  - strict one-row-per-paper focal/key-effect total: 1,401 paper units
  - broader focal/critical-test total: 1,941 paper units if Motyl is included after paper-level collapse
- Direct denominator datasets already found:
  - 1,021 raw direct-bias rows
  - 723 study-collapsed rows
  - 100 strict explicit journal-result rows from Roest 2015, Turner 2012, and
    Turner 2022
- Cipriani GRISELDA gives a larger published-vs-unpublished antidepressant
  denominator, but it is a meta-analysis extraction, not a clean paired
  journal-vs-regulatory corpus
- CliniFact x CT.gov bridge already built:
  - 1,319 publication-registry best matches
  - 668 plausible publication-result rows
  - 431 paired journal and registry p-value rows
  - raw disagreement queue cut from 357 to 42 cleaned rows
  - PMC full-text pass on those 42 rows:
    - 16 with PMCID
    - 5 with usable article-like PMC HTML
    - 11 challenge-blocked
    - 26 without PMCID
    - 2 resolved toward registry
- Public audit infrastructure already verified:
  - COMPare Trials Project public row-level CSV with 72 published-trial outcome-switching audits
    - 40 still unresolved

So the remaining gap is not linkage. The remaining gap is one of:

- a public row-level paired journal-vs-registry/FDA/CSR table,
- a public row-level primary-endpoint extraction dataset from papers that
  already did the work,
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
- Leight / Asri / Imai
- TESS with numeric outcomes

For each candidate, give the direct data URL, row count, whether it is Type A
or Type B, whether it has publication status, whether it has focal/primary
results, whether it has N, whether it has effect/z/p/CI/SE/raw data, and
whether journal and registry/FDA values are paired.

## Final Bottom Line

The project is no longer failing because we do not know where to look. It is
failing because the most conceptually correct datasets often stop one step short
of public row-level release. The local bridge/triage/full-text work has already
compressed the uncertainty down to a narrow set of unresolved objects.

The next GPT pass should therefore behave like a repository and supplement
hunt, not like a generic literature review.
