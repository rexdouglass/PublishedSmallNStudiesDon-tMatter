# Plot 3 Aggregation Audit - 2026-04-28

Purpose: verify that the plotted preregistered-results layer is not inflated by component-level political-science contrasts or by stale source-catalog bookkeeping.

## Current plotted layer

- `plot3_preregistered_results.csv`: 3,546 plotted rows across 8 fields and 47 source families.
- Political science: 55 plotted paper/project median rows across 36 source families.
- Political-science audit source: 1,213 extracted pre-collapse political rows feed 55 paper/project median rows in `plot3_political_science_paper_project_medians.csv`.

## Consistency checks

- Plot rows: 3,546.
- Included source-catalog rows contributed: 3,546.
- Criteria-matrix included rows: 3,546.
- Plot source families: 47.
- Included source-catalog families: 47.
- Missing source families in catalog: 0.
- Catalog families absent from plot: 0.
- Duplicate `point_id` values: 0.
- Plotted component/contrast `row_unit` values: 0.
- Missing or nonpositive `D`: 0.
- Missing or nonpositive `N`: 0.
- ClinicalTrials.gov rows: 3,149 unique NCT IDs, 0 duplicate NCT rows.

## Unit policy now enforced

- Political-science package extractions can retain component rows only in audit files.
- The plotted political-science layer is one median row per paper/project, except Brodeur and SCORE rows that were already paper-level corpus rows.
- Singleton political-science component rows are relabeled to paper/project rows in the plotted CSV to avoid ambiguous component semantics.
- The Plot 3 source catalog is reconciled against the actual plotted CSV, so newly added source families cannot silently appear in the plot without catalog rows.

## Verification commands run

- `.venv/bin/python -m py_compile scripts/build_paper_assets.py scripts/build_bibliography.py`
- `make render`
- Final CSV audit comparing `plot3_preregistered_results.csv`, `plot3_preregistered_source_catalog.csv`, `plot3_preregistered_criteria_matrix.csv`, and `plot3_political_science_paper_project_medians.csv`.

Known warning: the build emits a Stata UTF-8 fallback warning while reading a downloaded `.dta` archive. The build completes and the numeric row checks above pass.
