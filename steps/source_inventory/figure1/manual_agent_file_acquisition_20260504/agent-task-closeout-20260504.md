# Manual Agent Acquisition Closeout - 2026-05-04

Checked all seven manual follow-up tasks that were active for the Figure 1 D/N mining pass.

## Result

One new Figure 1 row is promotable from this batch under the current strict rule:

- both original and replication/follow-up effect values must be present or defensibly convertible to D;
- both original and replication/follow-up N values must be present;
- both N values must be at least 10;
- replication/follow-up N must be larger than original N;
- one-arm ORR/proportion endpoints are not converted into the main D-like lane.

The promoted row is the FORRT Reversals eye-movements / false-memories row, after local source-object extraction of the van Schie and Leer 2019 replication PDF, replication JASP archive, and already mirrored Houben original clean CSV.

The current Figure 1 table is now at 2,431 candidate pairs, with 1,679 included by the current D/N rule and 752 excluded.

## Task Outcomes

- `agent_file_acquisition_001`: Ying/Ehrhardt pilot-to-full-scale clinical trials. Public supplements did not contain row-level D/N data; data-sharing route is author request only. No rows.
- `agent_file_acquisition_002`: RGB health-behavior pilot/larger-trial workbooks. No public extraction workbook found; sources point to reasonable request. No rows.
- `agent_file_acquisition_003`: Hagen Cumulative Science Project. Public codebook found and mirrored; actual data sheet is deleted. No rows.
- `agent_file_acquisition_004`: FORRT Replications & Reversals. One source-confirmed row was promoted: Houben et al. 2018 / van Schie and Leer 2019 on misinformation answers after lateral eye movements. Four candidates were duplicates or alternate-grain source assertions, two failed the larger-N rule, and three remain held for source-object support.
- `agent_file_acquisition_005`: RCT-DUPLICATE / HTE-in-RWE. Public CSVs have HR estimates/CIs and covariates, but no RCT or RWE N columns. No rows.
- `agent_file_acquisition_006`: Many Smiles. Public data archive has replication-side raw data and replication N, but no original benchmark D/N table. No rows.
- `agent_file_acquisition_007`: Single-arm ORR/proportion conversion. Consensus is to keep these excluded from the main D-like lane unless a separately justified comparator/reference lane is built. No rows.

## Remaining Manual Work

Nothing needs user download right now. The only remaining paths are request-only, deleted-source recovery, or lower-priority bespoke source-object extraction tasks:

- request-only clinical/health-behavior datasets;
- recover the deleted Hagen backing sheet from maintainers or archives;
- source-confirm the remaining three held FORRT Reversals candidates before treating them as source-result assertions;
- build a separate Many Smiles original-benchmark extraction from Strack 1988 / Coles 2019 if the project later wants that row-grain.

These are not public-byte blockers that can be solved by the current local mirror scripts.
