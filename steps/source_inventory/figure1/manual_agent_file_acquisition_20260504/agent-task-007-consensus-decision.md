# Agent Task 007 Consensus: Clinical One-Arm ORR Conversion

Generated: 2026-05-04

## Decision

Do **not** convert single-arm ORR/proportion endpoints into the main Figure 1 D-like effect-size lane.

Rows affected:

- `clinical_highly_cited_orr_rows`: keep excluded.
- future single-arm ORR/proportion rows: stage native-only unless a separate clinical proportion lane is explicitly created.

## Reason

Across the returned agent reviews, the methods evidence points in the same direction:

- Chinn/log-OR-to-SMD conversion requires a two-arm odds-ratio contrast.
- Probit transformations require two proportions or a specified comparator/reference proportion.
- Cohen's h can compare a single observed proportion to a hypothesized/reference proportion, but the reference choice is arbitrary unless externally justified.
- Freeman-Tukey, logit, and related one-sample proportion transforms stabilize or model a single proportion; they do not create a treatment contrast comparable to Cohen's d or SMD.

## Figure 1 Consequence

No new Figure 1 rows are added from task 007.

The current D/N gate remains unchanged:

- no single-arm ORR-to-D conversion;
- no promotion of one-arm proportion rows into the main D axis;
- native staging is allowed later if the project wants a separate clinical-proportion analysis lane.

## Citation Caveat

The pasted agent responses include placeholder or blank citations. This consensus is an internal scope decision. Before using these method claims in manuscript prose, verify and cite primary methods sources directly.

