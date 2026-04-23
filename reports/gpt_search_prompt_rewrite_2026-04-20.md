I need help finding **publication-bias article-audit datasets** and **row-level reusable corpora**, not another generic literature review.

The key correction is this:

I do **not** believe the right claim is “nobody ever randomly sampled published articles and counted null results.” That would be absurd and almost certainly false. Publication bias is an old, large field. Of course people have done things like:

- randomly sample published journal articles,
- sample specific journals or journal issues,
- sample one year per journal,
- code whether the main result was positive/null/significant,
- compare protocols/registrations to publications,
- audit outcome switching,
- compare published vs unpublished trials,
- compare registry/FDA/regulatory records to journal publications.

So the search task is **not** to tell me that publication-bias research exists. I know that. The search task is to find the **datasets** behind that work, or to prove that the work exists but the row-level data were never publicly released.

Right now the numbers we have are implausibly small if interpreted as “all sampled published focal-result corpora that exist”:

- strict denominator-linked explicit journal-result rows: **100**, all psychopharmacology,
- strict one-row-per-paper focal/key-effect rows: **1,401**, still mostly psychology,
- broader published focal/critical-test paper units: **1,941** if a cautious Motyl 2017 paper-level collapse is included.

I think that means one of two things:

1. there really are many sampled article-audit studies but their row-level data were never released publicly, or
2. we are still missing public supplements / repos / appendices / archived files / Dataverse entries / hidden OSF components / Dryad / Mendeley / journal supplement ZIPs.

I want you to search specifically for that missing middle.

## What I need you to find

Please search for **three separate buckets**, and keep them separate in your answer.

### Bucket 1: Sampled published-article audits with positive/null/significant coding

These do **not** need to be D-ready. I want these because I refuse to believe the field never built them.

Examples of acceptable designs:

- random sample of journal articles,
- one issue per year per journal,
- all articles in specific journal years,
- random sample of PubMed/PsycINFO/Web of Science papers,
- coding whether the paper’s main result or abstract result was positive/null/significant.

For these, I want to know:

1. paper name,
2. exact sampling frame,
3. number of articles,
4. whether they coded main/focal result or just “any significant result,”
5. whether row-level data are public,
6. exact link to public data if yes,
7. if no public data, whether the article/supplement clearly implies such a table existed.

These studies matter even if they only code positive/null. They establish whether the field actually did the sampling work, even if the data are not reusable for effect-size analysis.

### Bucket 2: Sampled published-article corpora that are actually reusable for D-vs-N

This is the harder target.

I want sampled or transparent published-article corpora where each row is the **focal/main/headline result**, with enough information for `N` plus effect size / test statistic / p-value / CI.

Target row:

```text
published peer-reviewed article × focal/main result × N × effect/test statistic
```

These are **Type A** datasets.

Needed fields:

- peer-reviewed journal article,
- transparent sampling frame,
- focal/main/headline/primary result,
- sample size `N`,
- effect estimate, or z/t/F/r/chi-square/p/CI/SE, or raw arm-level data,
- ideally DOI/PMID/title/journal/year.

I already know about these, so do **not** present them as new unless you find extra public files we missed:

- Kühberger, Fritz & Scherndl 2014,
- Linden, Pollet & Honekopp 2024,
- Schäfer & Schwarz 2019,
- Motyl et al. 2017,
- COMPare Trials Project,
- statcheck,
- Szucs & Ioannidis 2017,
- SCORE / DARPA COS claims,
- FORRT/FReD,
- Reproducibility Project / Many Labs / SSRP / EERP,
- CHI meta-study,
- van den Akker preregistered vs non-preregistered.

For each new candidate in Bucket 2, report:

1. exact data URL,
2. number of rows/papers,
3. sampling frame,
4. whether the coded result is clearly focal/main,
5. whether `N` is present,
6. whether effect/z/p/CI is present,
7. whether row-level article identifiers are present,
8. whether the data are public and directly downloadable.

### Bucket 3: Denominator cohorts that can directly measure publication bias

This is the real end goal.

Target row:

```text
conducted/registered/submitted/regulatory study × publication status × primary/focal result × N × effect/test statistic × provenance
```

These are **Type B** datasets.

Examples:

- FDA trial sets,
- EMA / Health Canada / CSR datasets,
- ClinicalTrials.gov / AACT cohorts with publication linkage,
- EUCTR / EudraCT cohorts with publication linkage,
- IRB / ethics committee inception cohorts,
- registered social-science experiments,
- AEA RCT Registry cohorts,
- TESS cohorts,
- Registered Report cohorts,
- journal-submission cohorts.

I already know about these, so do **not** present them as new unless you find row-level public files we missed:

- Cipriani GRISELDA 2018,
- Turner 2022 newer antidepressants,
- Turner 2012 antipsychotics,
- Roest 2015 anxiety antidepressants,
- CliniFact,
- Shi & Du 2024 CT.gov result representation,
- AACT / CT.gov / Trialstreamer / Evidence Inference as generic scaffolds,
- Riveros 2013,
- Hartung 2014,
- Schwartz 2016,
- Chan 2004,
- Nordic trial reporting,
- IntoValue,
- AEA RCT Registry,
- Leight / Asri / Imai,
- TESS / Moniz / Druckman / Freese,
- Scheel / Registered Reports,
- Cochrane / BEAR / meta-analysis-derived corpora,
- GWAS Catalog.

For Bucket 3, I need you to be extremely concrete:

1. Is there a public row-level dataset?
2. Does it include unpublished/nonpublished studies or only published ones?
3. Does it include publication status?
4. Does it include the primary/focal result?
5. Does it include `N`?
6. Does it include effect/z/p/CI/SE/raw arm data?
7. Does it pair journal results with registry/FDA/CSR results?
8. What exact columns exist?
9. Direct URL to the downloadable data, not just the article.

If the answer is “the paper clearly extracted the right fields but did not publicly release them,” say that explicitly. That is a useful answer.

## What we have already done, so you don’t repeat it

We have already pushed local extraction quite far.

### Current direct publication-bias build

- raw D/N rows: **1,021**
- study-collapsed rows: **723**
- strict explicit journal-result rows: **100**

Breakdown of those 100 strict journal rows:

- Roest 2015: **46**
- Turner 2012: **19**
- Turner 2022: **35**

All of those are essentially in **psychopharmacology**.

### Current published focal-result build

- Kühberger 2014: **472** published paper-level main-result rows
- Linden 2024 focal effects: **158**
- Schäfer & Schwarz 2019 without preregistration: **682**
- Schäfer & Schwarz 2019 with preregistration: **89**

That gives **1,401** strict one-row-per-paper focal/key-effect rows, still mostly psychology.

If counting `Motyl 2017` after paper-level collapse:

- Motyl 2017 critical hypothesized tests: **540** paper units from **1,305** usable study-level rows

Then the broader published focal/critical-test set is **1,941** paper units.

### Current CliniFact x CT.gov bridge

We built a registry-to-publication bridge locally:

- **1,319** best NCT-to-PMID matches,
- **668** plausible publication-result rows,
- **431** rows with paired journal and registry p-values,
- **42** cleaned audit rows after triage,
- **40** unresolved after PMC/full-text pass.

This means we do **not** need suggestions like “use AACT” or “use CT.gov” in the abstract. We already did that. What we need are either:

1. public paired row tables that already solved the journal-side extraction problem, or
2. public sampled article-audit datasets we have not surfaced yet.

## What counts as a good answer

The best answer is **not** a broad essay about publication bias.

The best answer is a table of candidates, separated into Buckets 1, 2, and 3, where each row says:

- dataset/paper name,
- direct data link,
- sample size / article count / trial count,
- what was sampled,
- whether row-level data are public,
- whether the result is focal/main,
- whether N/effect/p/CI are present,
- whether publication status is present,
- why it does or does not satisfy the target.

## What to avoid

Do **not** give me:

- another general literature review,
- another explanation of funnel plots / p-curve / trim-and-fill / Egger tests,
- generic p-value scrape corpora,
- GWAS catalog suggestions,
- Cochrane pooled or review-derived rows,
- generic meta-analysis corpora unless they truly isolate published-article focal results,
- generic registry suggestions without publication-linked numeric results,
- datasets I already listed above unless you found a real public row-level file we missed.

## What I suspect is true

I suspect the real situation is this:

- there are many publication-bias studies based on sampled audits of published articles,
- many of them probably coded positive/null or main-result significance,
- but only a small minority publicly released row-level reusable data,
- and an even smaller minority released `N + effect/test statistic + focal-result + publication-status` in a reusable table.

I want you to test that suspicion directly.

## Deliverable format

Please answer in this order:

1. **Bucket 1:** sampled article audits with positive/null/significant coding,
2. **Bucket 2:** sampled published focal-result D-ready corpora,
3. **Bucket 3:** denominator cohorts for direct publication-bias measurement,
4. **Bottom line:** what probably exists versus what probably never got publicly released.

For each bucket, give me the strongest candidates first.

## If helpful, use searches like:

- "random sample of journal articles publication bias dataset"
- "sampled psychology articles significant results dataset"
- "publication bias random journal issue coding null results data"
- "main result positive null coded article dataset"
- "phase III RCT primary endpoint p value supplement csv"
- "ClinicalTrials.gov publication comparison row-level data"
- "registry publication outcome comparison supplementary dataset"
- "ethics committee publication bias dataset row level"
- "journal issue sampled articles significance coding dataset"
- "publication bias audit dataset positive null papers"

If you cannot find public row-level data, I still want the study listed, but label it clearly as:

```text
study exists, sampling exists, row-level public data not found
```

That is still useful, because it tells me the field did the sampling work but did not build public reusable infrastructure.
