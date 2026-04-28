# Research Prompt: Are Plot 3 Sidecar Sources Comparable to the Strict Preregistered Universe?

Date: 2026-04-27

## Copy/Paste Prompt

We are building a D-vs-N evidence map. Plot 3 is currently the strict preregistered-confirmatory-results layer. It contains only rows that look like standalone preregistered confirmatory result rows, with a result-level effect size `D` and sample size `N`.

The sidecar sources look visually different from the strict Plot 3 universe. That may mean they are genuinely different populations, or it may mean we are plotting overbroad versions of the sources and should identify cleaner subsets. Your task is to determine whether any sidecar subset is comparable enough to enter Plot 3, or whether these sources should remain separate sensitivity panels.

## Current Strict Plot 3 Universe

Strict Plot 3 currently has 156 plotted rows:

| Source family | Rows |
| --- | ---: |
| Schaefer/Schwarz preregistered psychology articles | 89 |
| Scheel et al. Registered Reports/preregistered-hypotheses corpus | 32 |
| SCORE/COS preregistration-indicated original papers | 31 |
| Dorison et al. PSA-CR001 pooled preregistered rows | 4 |

Current gate for entering strict Plot 3:

1. The row is an analytically preregistered confirmatory result or hypothesis row.
2. `D` and `N` are recoverable at the result-row level.
3. The row has public/local audit backing.
4. The row is not only registry metadata, publication-linkage metadata, or meta-research coding metadata.
5. The row is not already consumed as original-vs-replication pair evidence in Plot 1.
6. The row is not from a retracted source.
7. Admission does not depend on whether the result was supported/significant.

Important: "registered somewhere" is not automatically enough. We need the result row itself to be tied to a prespecified analytic outcome/hypothesis, or we need a defensible main-result selector that creates a comparable row unit.

## Current Sidecar Sources

The sidecar file has 11,446 rows:

| Sidecar source | Rows | Current reason for sidecar status |
| --- | ---: | --- |
| ClinicalTrials.gov registry-result D/N comparator | 7,722 | Registered registry-result rows with local D/N, but not yet confirmed as article-level analytic preregistered confirmatory rows. |
| Brodeur et al. 2024 preregistered/PAP economics table tests | 3,724 | Rows have real preregistration / pre-analysis-plan / PAP-power flags, but they are extracted published table tests without a known focal-result selector. |

Local files to treat as current-state evidence:

```text
data/derived/effect_inflation_dataset/plot3_preregistered_results.csv
data/derived/effect_inflation_dataset/plot3_preregistered_sensitivity_sidecar_rows.csv
data/derived/effect_inflation_dataset/plot3_preregistered_source_catalog.csv
data/derived/corpus_candidates/candidate_d_n_papers.csv
data/derived/corpus_candidates/candidate_d_n_rows.csv.gz
data/raw/corpus_candidates/ctgov_kg/
data/raw/corpus_candidates/brodeur_star_wars/
data/raw/corpus_candidates/brodeur_star_wars_openicpsr/
```

## Research Questions

### 1. ClinicalTrials.gov sidecar comparability

Determine exactly what the 7,722 ClinicalTrials.gov rows are.

Answer these questions:

- Are these rows primary outcomes, secondary outcomes, all posted registry result rows, or trial-level medians across outcomes?
- Does the source preserve an outcome type field such as primary/secondary/other?
- Does it preserve trial design fields such as interventional/observational, allocation, randomized, intervention model, masking, phase, enrollment, completion status, and results-posting date?
- Are the D/N values computed from exact arm-level result tables, p-values, summary statistics, or proxy conversions?
- Are posted ClinicalTrials.gov result outcomes demonstrably prespecified before outcome measurement, or could they reflect post hoc / edited registry results?
- Can we identify a clean subset such as:
  - randomized interventional completed trials only;
  - phase 2/3/4 or phase 3/4 trials only;
  - primary outcomes only;
  - primary outcomes with two-arm comparator structure only;
  - registry rows linked to a PubMed publication where the article primary endpoint matches the registry endpoint;
  - one row per trial using a prespecified primary outcome rather than a median across all outcomes.

Report whether any such subset is comparable to strict Plot 3. If yes, give exact inclusion rule, expected row count, fields used, and why it passes. If no, state the blocker.

### 2. Brodeur economics sidecar comparability

Determine exactly what the 3,724 Brodeur rows are and whether a cleaner subset can be recovered.

Current local facts:

- Source corpus: `economics_brodeur_2024`.
- Local extracted table-test rows: 10,071.
- Preregistration/PAP/PAP-power flagged D/N rows: 3,724.
- Flagged rows span 70 papers.
- Flags are parsed from row notes: `prereg`, `preanalysisplan`, and `pap_power`.
- Row unit appears to be an extracted published table test, not a source-selected main hypothesis.

Answer these questions:

- What is the exact Brodeur et al. source, paper/data archive, codebook, and intended unit of analysis?
- Are the flags article-level, experiment-level, table-level, or test-level?
- Does `prereg=1`, `preanalysisplan=1`, or `pap_power=1` mean the exact test was prespecified, or only that the paper had a preregistration/PAP somewhere?
- Is there a variable identifying main outcomes, primary hypotheses, first-stage/focal table, abstracts, stars, table number, outcome family, hypothesis number, or any focal-result selector?
- Are the rows all RCTs, or is `method=RCT` only a row/paper label that needs filtering?
- Is there a way to link rows to actual pre-analysis plans, AEA RCT registry records, trial registrations, or paper appendices?
- Can we build cleaner subsets such as:
  - papers with preregistration plus pre-analysis plan plus PAP-power;
  - PAP-power rows only;
  - one row per paper collapsed by a documented focal selector;
  - one row per hypothesis/outcome family if the source has hypothesis IDs;
  - table tests that are explicitly marked as primary outcomes or main specifications;
  - AEA RCT registry-linked outcomes with primary outcome labels.

Report whether any subset can honestly be called preregistered confirmatory result rows. If the best possible subset is still "published table tests from preregistered papers," say that clearly and recommend retaining sidecar status.

### 3. Comparability diagnostics

For any candidate subset from either sidecar, compare it to the strict Plot 3 universe on these dimensions:

| Dimension | What to check |
| --- | --- |
| Row unit | hypothesis/result row, trial outcome row, table test, paper median, or paper-level collapse |
| Preregistration evidence | analytic preregistration of exact row vs registry existence vs paper-level flag |
| Main-result selector | explicit primary/focal selector vs all tests/outcomes |
| Multiplicity | one row per study/hypothesis vs many non-independent rows per study |
| D/N quality | direct effect conversion vs p-value proxy vs median across rows |
| Publication filter | published paper results vs registry results vs table tests |
| Field/domain mix | psychology/social science/economics/medicine comparability |
| Visual difference explanation | whether different D/N distribution is likely substantive or an artifact of row construction |

The visual sidecar difference is itself a warning signal. Do not explain it away without checking row-unit and selection mechanics.

### 4. Required output format

Return a concise research memo with these sections:

1. **Decision Summary**
   - `clinicaltrials_to_strict_plot3: yes/no/maybe`
   - `brodeur_to_strict_plot3: yes/no/maybe`
   - one sentence explaining each decision.

2. **Candidate Subsets**

Use this table:

| Source | Candidate subset | Row count | Row unit | Exact prereg evidence | Main-result selector | D/N quality | Recommendation |
| --- | ---: | ---: | --- | --- | --- | --- | --- |

3. **Evidence and URLs**
   - Give source URLs, archive URLs, codebook URLs, and exact file names.
   - If a field exists, name the field.
   - If a field does not exist, say "not found" rather than guessing.

4. **Implementation Guidance**
   - Exact local filtering rule if a subset should be added.
   - Whether it should enter strict `plot3_preregistered_results.csv`, remain in `plot3_preregistered_sensitivity_sidecar_rows.csv`, or become a new separate sidecar.
   - Whether the figure should show the subset as one row per study, one row per outcome, or one row per table test.

5. **Do Not Promote Because...**
   - If no clean subset exists, write the exclusion language that should go into the source catalog.

## Important Constraints

- Do not use statistical significance/support to decide admission.
- Do not treat all ClinicalTrials.gov rows as preregistered confirmatory analytic results unless the exact outcome/result row is linked to prespecification.
- Do not treat all table tests in a preregistered paper as preregistered hypotheses unless the source identifies them as such.
- Do not mix trial registry outcomes, economics table tests, and Registered Report hypotheses in the same inferential layer unless row-unit comparability is established.
- If the best answer is "keep sidecar but add cleaner sub-sidecars," say that.

## Success Criterion

The research is successful if it lets us make one of these decisions for each sidecar source:

1. Promote a narrowly defined subset into strict Plot 3.
2. Keep the source as a named sensitivity sidecar with a cleaner subset plotted separately.
3. Exclude from Plot 3 entirely and document why the visual difference reflects non-comparable row construction.

