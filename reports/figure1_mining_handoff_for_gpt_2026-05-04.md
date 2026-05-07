# Figure 1 Replication-Corpora Mining Handoff for GPT

Generated: 2026-05-04

## Purpose

We are trying to build Figure 1 from many-replication corpora/databases, not from one-off papers. A useful source is a reusable collection, project, database, repository, workbook, article supplement, or data package that can yield multiple original-vs-replication/follow-up result pairs.

The working Figure 1 row is:

- One original result and one replication/follow-up/reproduction result.
- `D_original`: standardized original-side effect size.
- `N_original`: original-side sample size.
- `D_replication`: standardized replication/follow-up-side effect size.
- `N_replication`: replication/follow-up-side sample size.

The current inclusion rule is strict:

- Both D values are numeric.
- Both N values are numeric.
- Both N values are at least 10.
- The replication/follow-up N is larger than the original N.

We are not relaxing requirements for this pass. If a source only gives success/failure labels, qualitative reproducibility judgments, a registry link, or computational same-data robustness checks without a defensible D/N mapping, it does not add Figure 1 rows under the current rule.

## Current State

The current root table is `FIGURE1_REPLICATION_PAIRS.tsv`.

Current counts:

- Total root pair rows: 2,430.
- Included by the current Figure 1 D/N rule: 1,678.
- Excluded by the current rule: 752.
- Source-family labels represented: 40.

The recent mining phase added 124 total root rows and 78 included rows:

- REPEAT real-world evidence reproductions: 106 total rows, 60 included.
- Transparent Replications by Clearer Thinking: 18 total rows, 18 included.

Before this recent GPT-candidate mining phase, the table had 2,306 root rows and 1,600 included rows. After REPEAT it had 2,412 root rows and 1,660 included rows. After Transparent Replications it has 2,430 root rows and 1,678 included rows.

## Included Rows by Source Family

These are the current included-row counts by source-family label:

| Source family | Included rows |
|---|---:|
| FReD other additions | 378 |
| SCORE | 171 |
| LOOPR | 104 |
| Other direct replications | 89 |
| FReD CORE | 82 |
| FReD OpenMKT | 80 |
| OSC 2015 | 71 |
| FReD CurateScience | 70 |
| FReD SoSci submissions | 61 |
| REPEAT real-world evidence reproductions | 60 |
| Sensory-marketing replications | 38 |
| Coppock 2019 generalizability corpus | 35 |
| Student Replication Projects | 35 |
| RPCB | 33 |
| Clinical phase II to phase III pairs | 32 |
| Many Labs 2 | 28 |
| EPRP | 28 |
| Decision-Market Replication Project | 26 |
| Registered Replication Reports | 25 |
| Brazilian Reproducibility Initiative | 21 |
| SSRP | 20 |
| Management Science Replication Project | 20 |
| Many Labs 5 | 20 |
| EERP | 18 |
| Transparent Replications by Clearer Thinking | 18 |
| 251 Rescue Projects | 17 |
| Sports science replications | 16 |
| Experimental asset-market replications | 14 |
| Many Labs 1 | 13 |
| FReD FORRT | 11 |
| Many Labs 3 | 10 |
| Pipeline Project | 10 |
| Clinical highly cited replications | 7 |
| Eyewitness memory distortion in ten countries | 5 |
| Ying 2023 pilot-full-scale trials | 5 |
| FReD new RRR | 3 |
| Marek 2022 BWAS | 1 |
| Many Labs 4 | 1 |
| PSA 004 JTB Turri | 1 |
| DellaVigna-Linos 2022 | 1 |

## What Worked

### Existing psychology and metascience corpora

The classic psychology/metascience sources are the main reason Figure 1 already has many rows. They include FReD-derived rows, OSC/RPP, Many Labs projects, Registered Replication Reports, SSRP, EERP, SCORE, LOOPR, OpenMKT/FReD marketing entries, CurateScience/FReD entries, and other direct-replication datasets. These are already represented in the root table. GPT should not return them as "new" unless it finds a specific row-level table, supplement, or source file that would add rows not already represented.

The current bottleneck for most of these is provenance hardening, not mining. Many rows are numeric-builder checked but still need field-level support rows later.

### REPEAT Initiative

Outcome: promoted.

Working URLs:

- `https://osf.io/my5gn/`
- `https://osf.io/download/w64jq/`
- `https://www.nature.com/articles/s41467-022-32310-3`

Local mirror:

- `data/raw/replication_projects/lead_harvest/gpt_many_replication_candidates_20260504/repeat_initiative/b669f1bbabd4__w64jq.bin`

Rows:

- 106 promoted rows.
- 60 included rows under the current D/N rule.

Why it worked:

- Supplementary Data 6 and OSF files provide original and reproduced measures of association plus original and reproduction sample sizes.
- HR/OR/RR/rate-ratio effects were converted with `abs(log(ratio) * sqrt(3) / pi)`.

Caveat:

- This is real-world-evidence same-database reproduction, not independent new-data replication in the psychology sense. We kept it because it has explicit original/reproduction effect and N fields, but it should be labeled distinctly.

### Transparent Replications by Clearer Thinking

Outcome: promoted.

Local source:

- `data/raw/replication_projects/lead_harvest/gpt_many_replication_candidates_20260504/transparent_replications_clearer_thinking/`

Rows:

- 18 promoted rows.
- 18 included rows.

Why it worked:

- Mirrored report HTML pages contain tables with original and Clearer Thinking replication results.
- Several rows provide reported `d`, reported `r`/rank-biserial/correlation-like effects, `t(df)`, or chi-square with N.
- Conversions used:
  - reported `d`: used directly.
  - `r` or correlation-like effect: `d = 2r / sqrt(1-r^2)`.
  - `t(df)`: `d = abs(2*t/sqrt(df))`.
  - chi-square with N: `phi = sqrt(chi2/N)`, then `d = 2phi/sqrt(1-phi^2)`.

Caveat:

- This is mining only. Later provenance hardening should split multi-stat table cells into stronger field-level source-result support.

### Sensory Marketing Replications

Outcome: already promoted before this final pass.

Rows:

- 38 included rows.

Why it worked:

- The source provides article/table-level original-vs-replication effect-size and sample-size information for ten sensory-marketing replications. Some rows expand by outcome/effect rather than one row per article.

### Experimental Asset-Market Replications

Outcome: already promoted before this final pass.

Rows:

- 14 included rows.

Why it worked:

- The replication project exposes effect/result rows for preregistered experimental asset-market replications. These could be mapped to original and replication effects plus N.

### Management Science Replication Project

Outcome: already promoted before this final pass.

Rows:

- 26 total rows.
- 20 included rows.

Why it worked partially:

- The project has per-study pages and data/analysis/stimuli packages.
- The data are heterogeneous and need custom parsing, but enough rows were extractable under the current D/N rule.

### Brazilian Reproducibility Initiative

Outcome: already represented.

Rows:

- 45 total rows.
- 21 included rows.

Why it worked partially:

- Local BRI analysis outputs expose original-vs-replication biomedical effect estimates and sample information for some rows.

Caveat:

- Biomedical assays require careful row-grain and D-definition choices. Some rows do not pass the current larger-N or complete-D/N rules.

### Clinical phase II to phase III pairs

Outcome: already represented.

Rows:

- 32 included rows.

Why it worked:

- Phase II/phase III clinical-pair sources provide enough response/effect and N fields for a subset with defensible conversions.

### Clinical highly cited replications

Outcome: partially promoted.

Rows:

- 7 included rows.

Why it worked partially:

- Existing builder promotes OR/RR/HR rows from the local workbook.

Why no more rows were added:

- Remaining workbook rows use ORR, an objective response rate / one-arm response proportion. We did not convert one-arm ORR rows to D under the current rule.

## What Did Not Work or Did Not Add Rows

### Hagen Cumulative Science Project I

Outcome: blocked.

Working/mirrored URL:

- `https://github.com/pandorica-opens/Hagen-Cumulative-Science-Project-I/archive/refs/heads/master.zip`

Blocked route:

- The mirrored Shiny app points to Google Sheets `1VBnEG...` and `1f5QYC...`.
- Both Google export routes returned deleted/gone/HTTP 410 in this environment.

Why it did not add rows:

- The source likely has useful original/replication effect and N information, but the apparent backing tables are not currently retrievable from the mirrored app.

What GPT should do if revisiting:

- Find an alternate archived export, OSF file, paper supplement, package data object, or Wayback-recoverable CSV for the Hagen Shiny data. A landing page alone is not enough.

### Many Smiles Collaboration

Outcome: mirrored context, not promoted.

Working URLs:

- `https://osf.io/download/qd2s3/`
- `https://www.nature.com/articles/s41562-022-01458-9`

Blocked/nonworking URL:

- `https://manysmilescollaboration.com/` failed DNS resolution in this environment.

Why it did not add rows:

- The mirrored OSF data zip exposes replication data, but this pass did not find a clean table with original benchmark effect plus original N.
- The project often compares to a previous original or meta-analytic benchmark. Under the current rule, we need a defensible original-side D and N for the exact plotted pair.

What GPT should do if revisiting:

- Find the exact supplement/table/code that gives the original benchmark effect and original N for each Many Smiles task/outcome. Do not just point to raw replication data.

### Student Replication Projects / Boyce-style corpus

Outcome: already represented in root table as Student Replication Projects.

Rows:

- 114 total rows.
- 35 included rows.

Why it did not add more in the final pass:

- The corpus is already represented. More work here is likely deduplication/provenance hardening rather than discovering a new source.

What GPT should do if revisiting:

- Only suggest this if it can point to a different machine-readable supplement/export that adds rows not already covered.

### EPRP / X-Phi Replicability Project

Outcome: already represented as EPRP.

Rows:

- 35 total rows.
- 28 included rows.

Why it did not add more in the final pass:

- The source is already in the root table. Some candidate discussion pointed to OSF/project pages and ReplicationSuccess package data. That is not new unless there is a better master table or missing child-project rows.

### CREP

Outcome: context / discovery source, not a clean new mining source in this pass.

Why it did not add rows:

- CREP is fragmented across OSF child projects and student/meta-analysis outputs.
- Much of it appears already captured through FReD, CORE, student-replication, or related sources.
- No single master D/N table was confirmed during this pass.

What GPT should do if revisiting:

- Find a downloadable CREP aggregate table with original effect, replication effect, original N, replication N, and target-study IDs. A project page or "completed replication" list is not enough.

### FReD / FORRT Replication Database

Outcome: already deeply represented and useful as support/dedupe, not net-new.

Why it matters:

- FReD is one of the largest structured replication databases and already contributes many rows through multiple source-family labels.

Why it did not count as new:

- It overlaps heavily with existing rows. Its best use now is crosswalk, support, and provenance hardening.

What GPT should do if revisiting:

- Only return a FReD route if it identifies a newer export or subset with rows absent from the current table.

### OpenMKT

Outcome: already represented through FReD OpenMKT and sensory-marketing/promoted marketing rows.

Rows:

- FReD OpenMKT: 80 included rows.
- Sensory-marketing replications: 38 included rows.

Why it did not add more in the final pass:

- The tracker itself has many sample sizes and success labels, but not always inline effect sizes. Linked articles are needed for D.

### REPEAT-like same-data or robustness projects

Outcome: mostly context unless they expose explicit effect/N pairs and we choose to include same-data reproductions.

Examples:

- Institute for Replication / I4R.
- Brodeur/Cook/Mikola 110-article reproducibility and robustness project.
- ReplicationWiki.
- 3ie Replication Paper Series.
- Computational reproducibility and robustness projects.

Why most failed:

- They often reproduce original analyses using the same data.
- They emphasize robustness checks, code execution, or alternative specifications.
- They do not expose a clean original-vs-reproduction D/N table suitable for Figure 1.

REPEAT was an exception because it exposes structured original/reproduced measures plus sample sizes and was promoted with explicit labeling.

### ReplicationWiki

Outcome: context/discovery only.

Why it failed:

- It is a registry/bibliographic database of studies, materials, and replication classifications.
- We did not confirm downloadable effect-size and N fields.

### ML Reproducibility Challenge and ReScience C

Outcome: context/exclusion for current Figure 1.

Why they failed:

- They are large computational reproducibility sources, but their rows are usually benchmark metrics, model scores, simulation outputs, or task-specific values.
- There is no consistent D/N schema.
- "N" is often a dataset/test-set size, not the participant/sample size used in the current Figure 1 concept.

### ReproSci Fly Immunity

Outcome: context only.

Why it failed:

- It is a claim-verification/conceptual-replication workspace.
- It uses claim statuses and comments rather than extractable original/replication D/N rows.

### Ecology/evolution in-silico replication

Outcome: context only.

Why it failed:

- It estimates replicability from meta-analytic or in-silico distributions.
- It does not provide explicit original-vs-replication pairs in the current Figure 1 sense.

### NARPS / ManyAnalysts / Breznau / ManyEcoEvo / Perignon-style analyst-variability sources

Outcome: explicit exclusions.

Why they failed:

- These are same-data analyst-variability studies.
- Multiple teams analyze one dataset; that is not an original-vs-larger-N replication/follow-up pair under the current rule.

### GWAS Catalog and genetics replication-cohort ideas

Outcome: not promoted.

Why it remains unresolved:

- There may be discovery/replication cohort fields, OR/beta effects, and sample sizes.
- But the unit is often SNP-trait association rather than a study-level original-replication pair.
- Conversion to D and interpretation of N need a methodology decision before mining.

### ManyBabies and Many Smiles style multi-lab benchmark projects

Outcome: not promoted unless a source gives exact original benchmark D and original N.

Why they are hard:

- They often compare a large multi-lab estimate to a meta-analytic benchmark or a famous original finding.
- The replication-side data are usually available.
- The original-side D/N is not always available as a clean exact pair table.

### Clinical Neves/Boyce/re-replication style leads

Outcome: some related clinical and student-replication material is already represented; no confirmed additional table was mined in this final pass.

Why they remain only possible future work:

- Some sources are small, paper-specific, or may include meta-analytic replications that overlap the original study.
- They need exact supplements and row-level D/N tables, not just article abstracts.

## Local Exhaustion Check

We scanned the remaining staged harvest files after the final mining pass.

Result:

- 65 staged files scanned.
- 0 unpromoted staged files had obvious complete original/replication D+N columns.

The remaining locally mirrored "maybe" sources are therefore blocked by one of these issues:

- already promoted or already represented;
- same-data robustness/computational reproduction without a clear Figure 1 D/N mapping;
- no confirmed master D/N table;
- dead backing-data route;
- original benchmark effect/N not cleanly recoverable;
- effect measure requires a conversion decision we are not making in this pass.

## Useful Artifacts in the Repo

Main root output:

- `FIGURE1_REPLICATION_PAIRS.tsv`
- `FIGURE1_REPLICATION_PAIRS_SCHEMA.yml`

Current D/N check outputs:

- `steps/corpus_results/figure1/dn_check/figure1-corpus-dn-check-pairs.tsv`
- `steps/corpus_results/figure1/dn_check/figure1-corpus-dn-check-strict-result-sides.tsv`
- `steps/corpus_results/figure1/dn_check/figure1-corpus-dn-check-project-summary.tsv`
- `steps/corpus_results/figure1/dn_check/figure1-corpus-dn-check.md`

Recent mining scripts:

- `scripts/promote_gpt_candidate_batch2_pairs.py`
- `scripts/promote_remaining_local_figure1_mining.py`

Recent mining ledgers:

- `steps/corpus_results/figure1/gpt_candidate_pair_mining/gpt_candidate_batch2_mining_status.tsv`
- `steps/corpus_results/figure1/gpt_candidate_pair_mining/gpt_candidate_batch2_pair_mining.tsv`
- `steps/corpus_results/figure1/remaining_local_mining/remaining-local-mining-status.tsv`
- `steps/corpus_results/figure1/remaining_local_mining/staged-unpromoted-scan.tsv`
- `steps/corpus_results/figure1/remaining_local_mining/transparent_replications_table_rows.tsv`

Raw/mirror ledger:

- `steps/source_inventory/figure1/gpt_many_replication_candidates_20260504/mirror-status.tsv`

Repeatable make targets:

- `make figure1-gpt-candidate-batch2-mine`
- `make figure1-remaining-local-mine`
- `make figure1-corpus-dn-check`
- `make figure1-replication-pairs-table`

## What We Need From GPT Next

Please do not return broad "replication" projects or individual replication papers unless they contain a downloadable multi-row table. We need new many-replication corpora/databases/packages that can actually pass the Figure 1 row gate.

For every suggested source, provide:

1. Candidate name.
2. Domain.
3. Source-family type: database, project, repository, article supplement, registry, workbook, package, challenge, etc.
4. Stable identifier: DOI, OSF GUID, Dataverse DOI, Zenodo/Figshare/Dryad record, GitHub repo, package name, article DOI.
5. Exact working URLs to the data, supplement, code, or file inventory.
6. Evidence that it has multiple original-vs-replication/follow-up rows.
7. Evidence that original and replication effects are both available.
8. Evidence that original and replication N are both available.
9. Estimated pair count.
10. Whether it likely passes the current rule, likely fails, or needs custom parser.
11. Whether it is probably already covered by our current source-family list above.
12. Exact files to mirror first.
13. Failure reason if it probably will not pass.

Prioritize sources that look like:

- master CSV/XLSX/TSV/workbook with columns like `original_effect`, `replication_effect`, `original_n`, `replication_n`;
- article supplements with row-level original and replication effects plus sample sizes;
- OSF/Dataverse/Zenodo/Figshare/Dryad/GitHub repositories with a clear pair-level result table;
- non-psychology many-replication corpora that still report D-convertible effects and N.

Avoid or explicitly mark as false positives:

- ordinary "replication data for [original article]" packages that only reproduce the original article;
- same-data analyst-variability projects;
- computational reproducibility benchmark reports without D/N;
- registries with success labels but no effect/N table;
- claim-verification databases with no quantitative pair rows;
- individual one-off replication papers unless their supplement is itself a multi-row corpus.

Highest-value gaps to search:

- Biomedical/preclinical many-replication corpora outside RPCB and BRI.
- Clinical replication/follow-up datasets with row-level effect and N, not just article-level conclusions.
- Marketing/management/economics corpora with new-data replications rather than same-data robustness.
- Education, sports science, experimental philosophy, and judgment/decision-making projects with downloadable aggregate tables.
- Archived backing data for Hagen Cumulative Science Project.
- Exact original-benchmark effect/N sources for Many Smiles or ManyBabies-style projects.

The bar is not "does this project discuss replication?" The bar is "can we mirror bytes and produce rows with D_original, N_original, D_replication, and N_replication without inventing missing values?"
