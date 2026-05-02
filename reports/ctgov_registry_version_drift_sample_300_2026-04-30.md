# CT.gov Registry Version Drift Ledger

- Sample rows: 300
- CT.gov level-6 verifier failures with NCT IDs: 1
- Local child rows requiring historical-source handling: 2

## Status Counts

- `same_outcome_title_different_analysis_values`: 2

## Rows

- `sr_8b7d83b63310` / `NCT04524598` / `ctgovkg_47524`: same_outcome_title_different_analysis_values; local p=0.023, local param=t -2.306; current same-title analyses: analysis=1; p=0.06; z=1.8807936081512504; param=t -1.911; method=Mixed Models Analysis; N_enrollment=227.0 || analysis=2; p=0.01; z=2.5758293035489; param=t -2.546; method=Mixed Models Analysis; N_enrollment=227.0
- `sr_8b7d83b63310` / `NCT04524598` / `ctgovkg_108156`: same_outcome_title_different_analysis_values; local p=0.076, local param=F 3.152; current same-title analyses: analysis=1; p=0.06; z=1.8807936081512504; param=t -1.911; method=Mixed Models Analysis; N_enrollment=227.0 || analysis=2; p=0.01; z=2.5758293035489; param=t -2.546; method=Mixed Models Analysis; N_enrollment=227.0

## Interpretation

- This ledger is not a failed acquisition list. The current registry JSON was mirrored successfully.
- A row marked `same_outcome_title_different_analysis_values` means the represented trial/outcome exists, but the current registry values do not reproduce the local corpus values. It needs a historical AACT/ClinicalTrials.gov version before promotion.
- The next scalable implementation is an AACT snapshot comparator keyed by NCT ID, outcome title, analysis p-value/statistic, group codes, and enrollment.

## Output Files

- `data/derived/effect_inflation_dataset/schema_pilot/ctgov_registry_version_drift_sample_300.tsv`
- `data/derived/effect_inflation_dataset/schema_pilot/ctgov_registry_version_drift_summary_sample_300.tsv`
