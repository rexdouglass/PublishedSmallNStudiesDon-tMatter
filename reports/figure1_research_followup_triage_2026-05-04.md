# Figure 1 Research Follow-up Triage

Generated: 2026-05-04

## Summary

I processed the follow-up research batch against the current strict Figure 1 rule:

- both sides need numeric D;
- both sides need numeric N;
- both N values must be at least 10;
- replication/follow-up N must be larger than original N;
- rows should come from mirrorable source bytes, not just a landing-page description.

Result: **0 rows promoted** from this batch.

This does not mean the leads are irrelevant. It means the public bytes available in this pass did not expose a clean, deduped, multi-row D/N table that can be safely added now.

Current Figure 1 counts remain:

- Root pair rows: **2,430**
- Included rows: **1,678**
- Source-family labels: **40**

## Public Mirroring

The mirror pass attempted 14 URLs and mirrored 10.

Working mirrored routes included:

- FORRT Replications & Reversals: `https://forrt.org/reversals/`
- RCT-DUPLICATE GitHub raw CSVs:
  - `all_trials_results.csv`
  - `all_trials_results_corrected.csv`
  - `all_trials_covariates.csv`
  - `margins.csv`
- Childhood obesity RGB article landing: `https://doi.org/10.1186/s12966-020-0918-y`
- Adult obesity RGB Cambridge repository landing: `https://www.repository.cam.ac.uk/handle/1810/330818`
- Health-behavior RGB PubMed/Research Square pages
- Physical activity scale-up PMC page

Blocked routes in this environment:

- Ying BMJ EBM DOI route: HTTP 403
- Ying JHU dissertation route: HTTP 403
- Ying JAMA Network Open route: HTTP 403
- Nutrition scale-up DOI route: HTTP 403

Machine-readable mirror status:

- `steps/source_inventory/figure1/research_followup_20260504/mirror-status.tsv`

## Candidate Outcomes

### FORRT Replications & Reversals

Decision: **not promoted; candidate scan only**

The HTML database is mirrorable and contains many narrative replication/reversal entries. A conservative parser found:

- 431 narrative entries with original/replication-effect sections.
- 10 entries where the parser found exactly one original N, one replication N, one original d, and one replication d.
- 8 of those 10 would pass the larger-N check.

The 8 larger-N conservative candidates were:

- Fluency priming
- Sex differences in implicit maths attitudes
- Door-in-the-face effect
- Left-cradling bias
- Handedness differences in schizophrenia
- Eye movements and false memories
- Conjunction bias
- Right-bias in chimpanzee hand use

Why not promoted:

- High overlap with FReD and already-integrated direct-replication rows.
- Narrative entries often contain multiple original studies, multiple critiques, meta-analytic estimates, or mixed effect/N references.
- Promotion would need dedupe against FReD/current rows and better field alignment.

Artifacts:

- `steps/corpus_results/figure1/research_followup_20260504/forrt-reversals-conservative-candidate-scan.tsv`

### RCT-DUPLICATE

Decision: **not promoted; public result files lack N columns**

Mirrored GitHub CSVs expose trial names, result strings, covariates, and margins. The result files contain effect-like fields such as `pe_95ci`, but no clean original/RWE sample-size columns.

Why not promoted:

- No original and RWE/emulation N fields in the public CSVs inspected.
- This is also RWE emulation rather than independent randomized replication, so it would need the same kind of labeling caution used for REPEAT.

Artifacts:

- `steps/corpus_results/figure1/research_followup_20260504/rct-duplicate-schema-scan.tsv`

### Ying / Ehrhardt Pilot-to-Full-Scale Trial Datasets

Decision: **not promoted; request/access-only for now**

The research lead is strong: it may contain hundreds of pilot/full-scale pairs. But in this environment, the DOI/JHU/JAMA public routes were blocked or landing-page-only, and no public D/N master workbook was obtained.

Why not promoted:

- No mirrorable public D/N table found.
- The likely row-level data appear to require author request or manual access.

### Beets / von Klinggraeff RGB Health-Behavior Family

Decision: **not promoted; no public master table mirrored**

The public text confirms the family is relevant:

- Childhood obesity RGB: pilot/larger-trial pairs and SMD comparisons.
- Adult obesity RGB: larger pilot/larger-trial corpus.
- Broader health-behavior RGB: 69 pairs, 47 analyzed pairs, 156 effects.

Why not promoted:

- Mirrored pages confirm the article/preprint claims, but this pass did not obtain a CSV/XLSX/workbook with original SMD, larger-trial SMD, original N, and larger-trial N.
- This remains a high-value author-data or supplement-recovery target.

### Scale-up Reviews

Decision: **not promoted; context only**

The physical activity and nutrition scale-up reviews compare pre-scale and scale-up effects, but they are lower-yield and may violate the same-estimand/or same-intervention assumptions for Figure 1.

Why not promoted:

- No clean D/N table was obtained.
- The conceptual match is weaker than pilot/full-scale or direct-replication corpora.

## Practical Interpretation

This research reinforces the current posterior:

- There probably is not another giant public psychology-style D/N corpus waiting to be mirrored.
- The remaining high-yield path is health/clinical pilot-to-full-scale data, especially Ying/Ehrhardt and RGB-family datasets.
- Those high-yield sources are likely not public-byte-passable without author data or manual supplemental recovery.
- FORRT/Awesome/FReD-style aggregators can still add small numbers of rows, but they need dedupe and provenance alignment before promotion.

## Repeatable Commands

Mirror this batch:

```bash
make figure1-research-followup-mirror
```

Triage the mirrored files:

```bash
make figure1-research-followup-triage
```

Outputs:

- `steps/source_inventory/figure1/research_followup_20260504/mirror-status.tsv`
- `steps/corpus_results/figure1/research_followup_20260504/research-followup-triage.tsv`
- `steps/corpus_results/figure1/research_followup_20260504/forrt-reversals-conservative-candidate-scan.tsv`
- `steps/corpus_results/figure1/research_followup_20260504/rct-duplicate-schema-scan.tsv`

## Next Useful Action

The best next action is not another generic web search. It is a targeted acquisition request or manual recovery for:

1. Ying/Ehrhardt pilot-to-full-scale efficacy dataset.
2. Childhood/adult obesity RGB extraction workbooks.
3. Broader health-behavior RGB extraction workbook.
4. Hagen Cumulative Science Project backing Google Sheet or archived export.

If those cannot be obtained, the likely public-byte-only gain under current rules is small.
