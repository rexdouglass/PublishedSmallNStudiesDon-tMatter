# Plot 3 Sidecar Comparability Decision - 2026-04-27

## Decision

Neither sidecar is promoted into strict Plot 3.

- **ClinicalTrials.gov:** keep as registry sensitivity evidence. Build a cleaner sub-sidecar, but do not treat it as strict preregistered confirmatory evidence until rows are matched to pre-measurement protocol/SAP or equivalent analytic-prespecification evidence.
- **Brodeur economics:** keep as table-test sensitivity evidence. The flags are not enough to turn every coefficient row into a preregistered confirmatory hypothesis.

## Local CT.gov Audit

The local source is the finer-grained ClinicalTrials.gov results corpus:

```text
data/raw/corpus_candidates/ctgov_kg/efficacy_df.csv
```

Local file fields include `study_type`, `allocation`, `trial_phase`, `completion_year`, `outcome_type`, `groups`, `p_value`, `param_type`, `param_value`, and `enrollment_num`.

Raw local counts from the current file:

| Filter | Rows | Trials |
| --- | ---: | ---: |
| Valid p-value and enrollment | 108,196 | 7,722 |
| Primary + interventional + randomized + two groups + completed | 18,116 | 7,033 |
| Same, restricted to phase 2/3/4 or phase 2/3 / phase 3/4 | 14,494 | 5,800 |
| Phase-2+ subset with exactly one eligible primary row per trial | 3,149 | 3,149 |

The implemented cleaner sub-sidecar uses the last row above: phase-2+ randomized interventional trials with exactly one locally eligible primary two-group registry outcome. It is one row per trial and avoids selecting among multiple primary outcomes by significance or arbitrary order.

Output:

```text
data/derived/effect_inflation_dataset/plot3_ctgov_phase2plus_primary_randomized_sidecar_rows.csv
docs/_generated/figures/plot3_ctgov_phase2plus_primary_randomized_sidecar.png
```

Still excluded from strict Plot 3 because the current `D` is computed as a registry p-value/enrollment proxy rather than a direct arm-level D, and the row is not matched to a locked protocol/SAP or publication endpoint audit.

## Local Brodeur Audit

The current local Brodeur sidecar comes from:

```text
data/derived/corpus_candidates/candidate_d_n_rows.csv.gz
```

Current local facts:

| Quantity | Count |
| --- | ---: |
| Extracted economics table-test rows | 10,071 |
| D/N-ready rows with any prereg/PAP/PAP-power flag | 3,724 |
| Papers represented by flagged rows | 70 |

The incoming research notes that the published Brodeur et al. JPE Micro corpus reports a larger universe than the local subset, so the local file should not be assumed to be the full Dataverse corpus. No local focal-result selector has been found yet. Unless a true test-level variable such as `prereg_test` is recovered from the source archive and mapped into the normalized rows, the honest row unit remains "published table tests from preregistered/PAP-tagged papers."

## Catalog Language

ClinicalTrials.gov exclusion language:

> ClinicalTrials.gov / AACT outcome-analysis rows are excluded from strict Plot 3 because the registry enforces registration-level prespecification of primary outcome labels and time frames, not analytic-level locking of the exact statistical test producing each D/N row. The local cleaner subset is useful, but it remains a sidecar until exact row-level prespecification and direct arm-level effect construction are audited.

Brodeur exclusion language:

> Brodeur et al. preregistered/PAP economics rows are excluded from strict Plot 3 because the local rows are extracted published table tests. The preregistration, pre-analysis-plan, and PAP-power indicators are not sufficient to prove that each coefficient/test is the exact prespecified confirmatory hypothesis. Without a focal/test-level selector, the source remains a sensitivity sidecar.

