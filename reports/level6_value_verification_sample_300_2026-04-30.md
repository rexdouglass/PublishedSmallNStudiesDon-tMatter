# Level-6 value verification pass

- Sample rows: 300
- CT.gov registry-result rows attempted: 89
- CT.gov rows already level 6 at verifier start: 88
- Rows whose plotted D/N were recomputed from ClinicalTrials.gov API JSON: 88
- Rows currently below level 6 but promotable from this run: 0
- Rows not promotable from this route: 1

## Verification Status

- `verified_plot_d_n_from_registry_json`: 51
- `verified_single_registry_outcome_from_json`: 37
- `partial_child_values_verified_from_registry_json`: 1

## Remaining Blockers

- `sr_8b7d83b63310` / `NCT04524598`: partial_child_values_verified_from_registry_json; ctgovkg_47524:registry_outcome_found_but_matching_p_value_not_found; ctgovkg_108156:registry_outcome_found_but_matching_p_value_not_found
- The observed blocker is not access. It is source-version disagreement: the local CT.gov KG/AACT-derived p-values for the selected outcomes do not match the current ClinicalTrials.gov API JSON, so this row needs the exact registry snapshot/source version mirrored before promotion.

## Lessons Learned

- For CT.gov paper-level dots, the plotted D/N is often the median across several registry outcome rows. A same-title child row is not enough; the verifier must use NCT ID first, validate each child row from the registry JSON, then recompute the median.
- The retrace logic was corrected to prefer paper/unit identifiers before outcome titles. Outcome-title-only matching can attach values from another NCT with the same label.
- Level-5 acquisition paths should be treated as cached hints. The level-6 verifier re-derives the NCT from the upstream row and refuses paths whose NCT does not match.
- The registry JSON contains the necessary p-values and protocol enrollment counts for this route, so CT.gov rows are a good high-yield target for value verification.

## Output Files

- `data/derived/effect_inflation_dataset/schema_pilot/level6_value_verification_attempts_sample_300.tsv`
- `data/derived/effect_inflation_dataset/schema_pilot/level6_value_verification_summary_sample_300.tsv`
