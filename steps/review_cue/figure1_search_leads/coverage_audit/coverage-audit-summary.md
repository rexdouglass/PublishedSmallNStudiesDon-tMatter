# Figure 1 Coverage Audit, 2026-05-02

This folder normalizes returned GPT research from the Figure 1 replication-corpora coverage audit prompt:

- `../gpt-figure1-replication-corpora-coverage-audit-prompt.md`

The two returned cluster-decision batches were already present and applied as:

- `../reviewcue-clustered-decisions-figure1_search_leads-codex-clustered004.json`
- `../reviewcue-clustered-decisions-figure1_search_leads-codex-clustered005.json`
- `../reviewcue-clustered-routing-table-figure1_search_leads.tsv`

This coverage audit is intentionally advisory. It should seed future search and review work, but it should not directly edit `CORPORA_AND_DATABASES.tsv`.

## Assessment

- Confidence that major psychology sources have been found: medium.
- Confidence that the cross-field long tail has been found: low.

Main blind spots:

- Psychology famous-project coverage is decent, but explicit FORRT/FReD-adjacent project families still need stronger source-family review, including CORE JDM, Data Replicada, Sports Sciences Replications, Hagen Cumulative Science Project, REPEAT, CREP, ReproSci, and Experimental Philosophy.
- Cross-field source-family objects in economics, political science, healthcare-database research, computational reproducibility, machine learning, experimental philosophy, sports science, ecology/evolution, and preclinical biomedicine are not reliably found by psychology-centered aliases.
- Ordinary "replication data/files/package" records are high-noise because they often mean reproducibility materials for the original article rather than independent replication or follow-up results.
- Many long-tail sources live behind project lists, challenge venues, journal gateways, GitHub/package inventories, and funder project databases rather than standard scholarly metadata.
- Search vocabulary should include reproduction, computational reproducibility, robustness reproducibility, direct replication, conceptual replication, validation, reanalysis, repeatability, repeat study, many-lab, multi-site, multicenter, follow-up, claim verification, and benchmark.

## Normalized Outputs

- `missing-source-families.tsv`: named undersearched source families and triage routes.
- `new-search-surfaces.tsv`: public search surfaces and APIs to add or strengthen.
- `query-families.tsv`: non-generic query families and promotion gates.
- `triage-rules.tsv`: deterministic routing gates to add to future search triage.
- `manual-followup-targets.tsv`: high-value manual investigation targets.
