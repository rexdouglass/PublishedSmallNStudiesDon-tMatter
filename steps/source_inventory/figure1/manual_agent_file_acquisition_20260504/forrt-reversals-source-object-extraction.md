# FORRT Reversals Source-Object Extraction Closeout

Date: 2026-05-04

Scope: conservative FORRT Reversals rows that exposed original and replication D/N-like values in `steps/corpus_results/figure1/research_followup_20260504/forrt-reversals-conservative-candidate-scan.tsv`.

Outcome:

- Promoted 1 new Figure 1 pair: Houben et al. 2018 lateral eye movements / false memories, replicated by van Schie and Leer 2019.
- Did not promote 4 rows because they were duplicates or alternate-grain assertions of already included rows: fluency priming, sex differences in implicit maths attitudes, door-in-the-face, and conjunction bias.
- Did not promote 2 rows because they fail the current larger-N rule: red impairs cognitive performance and foot-in-the-door.
- Held 3 rows because FORRT supplies numeric D/N text but exact source-object extraction is still incomplete: left-cradling bias, handedness in schizophrenia, and chimpanzee hand use.

The promoted row has mirrored value-bearing sources:

- Replication PDF: `data/raw/replication_projects/lead_harvest/forrt_reversals_source_objects_20260504/eye_movements_false_memories/van_schie_leer_2019_repub.pdf`
- Original cleaned data: `data/raw/replication_projects/lead_harvest/awesome_emdr_misinfo/github_01__original_clean.csv`
- Replication analysis archive: `data/raw/replication_projects/lead_harvest/forrt_reversals_source_objects_20260504/eye_movements_false_memories/van_schie_leer_results.jasp`

Promoted values:

- Original D: `0.7669097512387202`, recomputed as absolute Cohen's d from `totalmisinfo` by `condition` in the original clean CSV.
- Original N: `82`, from the original clean CSV row count; the replication PDF also states Houben et al. 2018 showed 82 undergraduates the stimulus.
- Replication D: `0.063`, from van Schie and Leer 2019, misinformation answers result.
- Replication N: `206`, from the replication PDF abstract and participants section.

Exact per-candidate decisions are in `forrt-reversals-source-object-extraction.tsv`.
