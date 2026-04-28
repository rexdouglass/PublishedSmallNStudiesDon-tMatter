# Plot 3 Preregistered Missing-Points Audit - 2026-04-27

## Current Plot 3 Gate

Plot 3 currently admits standalone preregistered confirmatory result rows when all of these are true:

- the row is an analytically preregistered confirmatory result or hypothesis row;
- `D` and `N` are recoverable at the result-row level;
- the source is public and locally auditable;
- the row is not already consumed as a Plot 1 original-vs-replication pair;
- the source is not retracted;
- the row is not merely registry metadata, publication-linkage metadata, or a meta-research preregistration about how articles were coded.

Under that gate, the plotted corpus is now 156 rows:

| Included source | Rows |
| --- | ---: |
| Schaefer/Schwarz preregistered psychology articles | 89 |
| Scheel et al. Registered Reports/preregistered-hypotheses corpus | 32 |
| SCORE/COS preregistration-indicated original papers | 31 |
| Dorison et al. PSA-CR001 pooled preregistered rows | 4 |

The SCORE/COS recovery uses the OSF-listed `orig_prereg-indicated.csv` file, downloaded locally in this pass. It contributes only the 31 deduplicated paper-level D/N rows among 245 unique SCORE paper IDs marked `prereg=True`. The journal TOP-factor preregistration-policy columns in `paper_metadata.csv` were checked but deliberately not used as inclusion evidence because those fields describe journal policy, not article-level preregistration.

## Missing-Looking Buckets Rechecked

The large local buckets were not absent because they were missed. They were absent because they fail the current narrow gate or belong to another plot layer.

| Bucket | Local rows considered | D/N-ready rows | Current status |
| --- | ---: | ---: | --- |
| ClinicalTrials.gov registry-result comparator | 7,722 | 7,722 | Registry-outcome rows. Strong candidate for a separate registry sensitivity lane, but not standalone published analytic preregistration under current Plot 3 gate. |
| CliniFact published trial primary-outcome rows | 339 | 339 | Already in the published-paper endpoint surface. Registry-linked primary outcomes are close to preregistered work, but article-level analytic preregistration text is not confirmed. |
| COMPare clinical-trial outcome-reporting audit | 1,171 outcome rows across 72 trial reports | 0 | Outcome-level prespecification status is local and verified: 89 prespecified primary, 660 prespecified secondary, and 422 non-prespecified publication outcomes. The parsed rows have no effect/N fields. |
| Nordic trial registration-publication linkage database | 7,461 | 0 | Trial/publication linkage metadata only; no exact effect or `D`/`N` fields. |
| FORRT FReD / Replication Database | 843 pair rows, plus 796 published original-target rows | 843 pair rows | Already represented through Plot 1 and Plot 2. No analytic preregistration flag for each source result. |
| FReD archived workflow workbook / OSF Registries queue | 343 absent-from-current converted/N-complete rows; 425 validated complete rows overall | 343 in archive, but 0 admitted here | Follow-up archive scan found 15 OSF Registries rows and 107 rows with nonempty replication-preregistration fields. Still a replication-pair/workflow rescue queue, not standalone Plot 3 result rows, and needs duplicate handling against current FReD, Many Labs, RRR, and OSF-registries rows. |
| Many Labs 1-5 | 69 | 69 | Already Plot 1 replication-pair evidence. |
| Registered Replication Reports Plot 1 pair rows | 49 | 49 | Already Plot 1 replication-pair evidence. |
| Registered Replication Reports per-lab rows | 205 | 0 in a dedicated Plot 3 table | Real preregistered replication evidence, but a separate lab-level policy is needed to avoid double-counting Plot 1. |
| PSA replication-pair rows | 93 | 93 | Already Plot 1 replication-pair evidence; PSA-CR001 pooled rows are the standalone exception and are included. |
| Transparent Psi Project / Bem | 1 | 1 | Already Plot 1 direct-replication shrinkage row. |
| Communication privacy preregistered replication corpus | 31 | 31 path/SEM-like rows | Real and local, but rows are SEM/path evidence and Plot 1-adjacent; metric policy is not the same as D/N confirmatory rows. |
| Retrieval-extinction rats preregistered replication | 3 | 3 | Already Plot 1 direct-replication rows. |
| ManyBabies 3 | 15 expected | 0 | Public payload has preregistered-report/materials files, not final machine-readable site-level results. |
| ManyClasses 2 | 30 expected | 0 | Public OSF payload has classroom data/scripts but needs a separate parser and classroom metric policy. |
| Self-control fMRI preregistered replication | 4 expected | 0 | Local payload is preregistration/raw neuroimaging/paper material, not a compact D/N result table. |
| ERN/Pe RRR | 1 source family | 0 | Native EEG/OpenNeuro/OSF materials; no compact original-side plus replication-side D/N table. |
| Twomey kinesiology audit | 300 articles; 27 preregistered | 0 | Preregistration and N fields exist, but exact effect/test-statistic fields for D conversion do not. |
| Linden focal/random psychology sample | 316 | 316 | D/N-ready, but preregistration applies to the meta-research coding study rather than the sampled article findings. |
| Schaefer/Schwarz non-preregistered comparator | 900 coded rows | 682 | Explicitly non-preregistered; already useful for Plot 2 comparison. |
| Protzko High-Replicability Research | 48 claimed; 3 local D/N rows | 3 | Excluded by non-retraction gate. |

## Decision

One new standalone Plot 3 subset was promoted: the SCORE/COS preregistration-indicated original-paper subset (`+31` rows). The remaining large buckets are still policy exclusions or missing effect/N fields rather than parser misses under the current definition.

The biggest optional future change is not extraction; it is a scope decision. If Plot 3 is broadened from "published analytic preregistered confirmatory results" to "all preregistered or registered outcomes," then the first new sensitivity lane should be ClinicalTrials.gov registry results (`+7,722` rows) and the second should be CliniFact published registry-linked primary outcomes (`+339` rows).
