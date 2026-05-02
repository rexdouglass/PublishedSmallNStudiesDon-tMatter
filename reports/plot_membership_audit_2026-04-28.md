# Cross-Plot Paper/Unit Membership Audit - 2026-04-28

This audit makes the Plot 1/2/3 ownership contract explicit on disk. The main outputs are TSVs in `data/derived/effect_inflation_dataset/`.

## Files

- `plot_paper_membership.tsv`: 15,858 paper/unit membership rows across Plots 1-3.
- `plot_paper_exclusivity_audit.tsv`: 14,833 normalized paper/unit keys with overlap and weak-key flags.
- `plot_source_family_membership.tsv`: 225 source-family/catalog membership rows across Plots 1-4.
- `plot_assignment_rules.tsv`: six current rules for mutually exclusive Plot 1/2/3 ownership and nonexclusive Plot 4 usage.

## Current Membership Counts

- Plot 1: 1,805 paper-side membership rows from replication pairs.
- Plot 2: 10,507 published endpoint rows.
- Plot 3: 3,546 preregistered confirmatory rows.

## Large Collapse Documentation

Large component sets are no longer implicit. For example, the Hewitt campaign-ad persuasion archive is recorded as:

- `plot_paper_membership.tsv`: one Plot 3 membership row with `rows_represented = 1008`, `row_unit = paper_median_of_preregistered_results`, citation key `hewittCampaignExperimentsDataverse`, and the collapse rule/source file.
- `plot3_political_science_paper_project_medians.csv`: one detailed median row with `rows_collapsed = 1008`, median D/N, N range, example labels, and source files.
- `plot3_preregistered_source_catalog.csv`: one source-level row with `rows_considered = 1008`, `rows_contributed = 1`, and explanation.

## Overlap Flags Found

The new audit found 496 normalized paper/title keys appearing in more than one of Plots 1-3:

- 426 keys appear in both Plot 1 and Plot 2.
- 70 keys appear in both Plot 2 and Plot 3.

These are now explicit in `plot_paper_exclusivity_audit.tsv` as `cross_plot_overlap_needs_manual_review`. I did not silently remove them from any plot in this pass because the current figures were built from plot-specific CSVs; changing ownership should be a deliberate dedupe pass.

Rows with `paper_key_quality = source_row_fallback` are also flagged for manual review because they lack a DOI/title-like identifier and cannot be reliably cross-matched.
