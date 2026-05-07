# Figure 1 Local Mining Completion And Manual To-Do

Generated: 2026-05-04

## Definitions

For this pass, a **pair** means one original result matched to one replication, reproduction, or larger follow-up result.

The strict Figure 1 **D/N gate** means:

- `D_original` and `D_replication` are numeric standardized effects.
- `N_original` and `N_replication` are numeric sample sizes.
- both sample sizes are at least 10.
- the replication or follow-up sample size is larger than the original sample size.

**Promoted** means rows were written into the Figure 1 pair-table harvest pipeline and then rebuilt into `FIGURE1_REPLICATION_PAIRS.tsv`.

**Manual acquisition** means the source probably matters, but the local bytes do not currently contain enough row-level D/N information. A human needs to obtain a workbook, supplement, author-shared dataset, archived file, or make a scope/conversion decision.

## Current State

After rerunning the local mining and pair-table build, the root table is:

- `FIGURE1_REPLICATION_PAIRS.tsv`

Current counts:

- Root pair rows: **2,431**
- Included by the current Figure 1 D/N rule: **1,679**
- Excluded by the current Figure 1 D/N rule: **752**
- Source-family labels represented: **40**
- Duplicate `figure1_replication_pair_id` values: **0**

Exclusion blockers:

- `blocked_replication_N_le_original_N`: **647**
- `blocked_N_lt_10`: **69**
- `blocked_N_lt_10 | blocked_replication_N_le_original_N`: **36**

Source-result promotion state:

- `needs_verbatim_source_result_support`: **2,285**
- `ready_for_source_result_side_promotion`: **138**
- `needs_pair_alignment_to_strict_side_rows`: **8**

The last full local command succeeded:

```bash
make figure1-gpt-candidate-batch2-mine figure1-remaining-local-mine figure1-research-followup-triage figure1-raw-viability-summary figure1-corpus-dn-check figure1-replication-pairs-table
```

## What Local Mining Added

The main final local additions were:

- **REPEAT real-world evidence reproductions:** 106 rows promoted, 60 included by the current D/N rule.
- **Transparent Replications by Clearer Thinking:** 18 rows promoted, 18 included by the current D/N rule.
- **FORRT Reversals source-object extraction:** 1 row promoted and included after confirming mirrored source objects.

The current included rows by large source-family label are:

| Included rows | Source family |
|---:|---|
| 378 | FReD other additions |
| 171 | SCORE |
| 104 | LOOPR |
| 90 | Other direct replications |
| 82 | FReD CORE |
| 80 | FReD OpenMKT |
| 71 | OSC 2015 |
| 70 | FReD CurateScience |
| 61 | FReD SoSci submissions |
| 60 | REPEAT real-world evidence reproductions |
| 38 | Sensory-marketing replications |
| 35 | Student Replication Projects |
| 35 | Coppock 2019 generalizability corpus |
| 33 | RPCB |
| 32 | Clinical phase II to phase III pairs |
| 28 | Many Labs 2 |
| 28 | EPRP |
| 26 | Decision-Market Replication Project |
| 25 | Registered Replication Reports |
| 21 | Brazilian Reproducibility Initiative |
| 20 | SSRP |
| 20 | Many Labs 5 |
| 20 | Management Science Replication Project |
| 18 | Transparent Replications by Clearer Thinking |
| 18 | EERP |

## Local Sources Checked But Not Promoted

The remaining local/staged scan checked 65 staged harvest files. No unpromoted staged file had obvious complete original/replication D/N columns under the current parser.

Status artifacts:

- `steps/corpus_results/figure1/remaining_local_mining/remaining-local-mining-status.tsv`
- `steps/corpus_results/figure1/remaining_local_mining/staged-unpromoted-scan.tsv`
- `steps/corpus_results/figure1/research_followup_20260504/research-followup-triage.tsv`
- `steps/corpus_results/figure1/result_table/figure1-replication-pairs-summary.md`

Checked but not promoted:

| Candidate | Local outcome |
|---|---|
| Clinical highly cited workbook | Existing builder already promotes 7 OR/RR/HR rows. The remaining 3 ORR rows are one-arm response-rate rows and are not converted to D under the current rule. |
| Hagen Cumulative Science Project | Still blocked. The mirrored Shiny app points to Google Sheets backing data routes that now return gone/410. |
| Many Smiles | Mirrored replication-side data do not expose a clean original benchmark effect plus original N table. |
| FORRT Replications & Reversals | Conservative scan found 10 D/N-like narrative entries, 8 with larger replication N. One row was promoted after source-object extraction: Houben et al. 2018 / van Schie and Leer 2019 on eye movements and misinformation answers. Four candidates were duplicates or alternate-grain assertions, two failed the larger-N rule, and three remain held for source support. |
| RCT-DUPLICATE | Mirrored public GitHub CSVs expose effect-like fields but no clean original/RWE sample-size columns. |
| Ying/Ehrhardt pilot-to-full-scale datasets | Strong research lead, but routes were blocked or landing-only here. No public row-level D/N table was mirrored. |
| Beets/von Klinggraeff RGB health-behavior family | Article/preprint pages confirm relevant pair/effect counts, but no public master D/N workbook or CSV was obtained. |
| Scale-up intervention reviews | Context only for now. No D/N table obtained, and same-estimand fit is weaker. |

## Manual To-Do

### 1. Acquire Ying/Ehrhardt Pilot-To-Full-Scale Treatment-Effect Data

Priority: high

Why: This is the clearest likely source of additional clinical/public-health rows. Current local data only yield 5 Ying-family rows, but the research lead suggests roughly 248 pilot/full-scale trial pairs.

Need:

- row-level pilot and full-scale treatment-effect estimates;
- effect metric and enough information to convert to D under the existing rule;
- pilot N and full-scale N;
- citation/identifier for each original pilot and larger trial.

Known routes:

- DOI `10.1136/bmjebm-2023-112358`
- JHU dissertation record for "Role of Pilot Trials in RCT Quality and Feasibility"
- DOI `10.1001/jamanetworkopen.2023.33642`

Manual action:

- Try institutional/browser access to the BMJ EBM and JHU/JAMA routes.
- If no supplement contains the extraction table, park this under the current no-author-request policy.
- Do not promote feasibility-only outcomes unless the project explicitly decides those are Figure 1 estimands.

### 2. Acquire RGB Pilot-Vs-Larger-Trial Extraction Workbooks

Priority: high

Why: The childhood obesity, adult obesity, and broader health-behavior RGB family appears highly aligned with the Figure 1 question: preliminary/pilot effects compared with larger efficacy/effectiveness trials, often using SMDs.

Need:

- original/preliminary SMD or convertible effect;
- larger-trial SMD or convertible effect;
- original/preliminary N;
- larger-trial N;
- row labels tying effects to the same construct/outcome.

Known routes:

- Childhood obesity: DOI `10.1186/s12966-020-0918-y`
- Adult obesity: DOI `10.1111/obr.13369`; Cambridge repository DOI `10.17863/CAM.78261`
- Broader health-behavior RGB: PubMed `38464006`; Research Square `10.21203/rs.3.rs-3897976/v1`

Manual action:

- Check publisher supplements and repository attachments manually.
- If extraction workbooks are not public, park this under the current no-author-request policy.
- Keep construct-level and individual-effect-level rows distinct; dedupe later through canonical IDs.

### 3. Recover Hagen HCSP Backing Data

Priority: medium-high

Why: The mirrored GitHub/Shiny material suggests a real multi-replication source, but the backing Google Sheets route is gone.

Need:

- the Shiny backing dataset or an archived export;
- original effect and original N;
- replication effect and replication N;
- target-paper/study identifiers.

Manual action:

- Try repository history, web archive snapshots, or any local old cache.
- Park maintainer/contact routes under the current no-author-request policy.
- If recovered, parse into a staged harvest table first, then dedupe against FReD and existing JDM rows.

### 4. Held FORRT Replications & Reversals Source-Object Candidates

Priority: medium

Why: The local HTML mirror is parseable and contained a small number of conservative D/N candidates. The only source-confirmed public-byte row from this pass was promoted. The remaining possible additions are held because exact value-bearing source-object support is incomplete.

Already resolved:

- Promoted: eye movements and false memories.
- Duplicate/alternate-grain: fluency priming, sex differences in implicit maths attitudes, door-in-the-face effect, conjunction bias.
- Larger-N rule failed: red impairs cognitive performance, foot-in-the-door.

Held candidate labels:

- Left-cradling bias
- Handedness differences in schizophrenia
- Right-bias in chimpanzee hand use

Local artifact:

- `steps/corpus_results/figure1/research_followup_20260504/forrt-reversals-conservative-candidate-scan.tsv`
- `steps/source_inventory/figure1/manual_agent_file_acquisition_20260504/forrt-reversals-source-object-extraction.tsv`

Manual action:

- Promote only if exact original and replication result text or source data support the D/N values, not just the FORRT narrative.
- Preserve the FORRT narrative text as support if a held row is later promoted, because the HTML entries mix original studies, critiques, meta-analytic values, and replications.

### 5. Decide Whether One-Arm Response-Rate Rows Can Enter Figure 1

Priority: medium

Why: The clinical highly cited workbook has 3 remaining ORR rows that are currently excluded. Similar clinical sources may contain many one-arm response-rate or proportion endpoints.

Current rule:

- Do not convert one-arm ORR/proportion rows to D.

Manual action:

- Either keep the current rule, in which case these stay excluded.
- Or define a documented conversion and minimum support fields for one-arm binary/proportion outcomes. If this changes, rerun clinical mining and update the schema notes.

### 6. RCT-DUPLICATE Only If N Can Be Recovered

Priority: low-medium

Why: The GitHub files are mirrorable and effect-like fields exist, but the public CSVs inspected do not contain clean original and emulation N fields.

Local artifact:

- `steps/corpus_results/figure1/research_followup_20260504/rct-duplicate-schema-scan.tsv`

Manual action:

- Only continue if a human can obtain or reconstruct original RCT N and RWE emulation cohort N.
- Label separately from independent randomized replication if included.

### 7. Many Smiles Only If Original Benchmark Rows Are Recovered

Priority: low-medium

Why: Replication data are not the blocker; the blocker is a defensible original benchmark effect plus original N for each target.

Manual action:

- Find an exact source table for the original benchmark D and N.
- Do not promote lab-level replication rows against a meta-analytic benchmark unless the project explicitly approves that row grain.

### 8. Provenance Hardening Later

Priority: later, not part of current mining

The pair table is now broad but still needs source-result hardening:

- 2,285 rows need verbatim source-result support.
- 138 rows are ready for source-result side promotion.
- 8 rows need strict pair-ID alignment.

This is not a remaining mining source. It is the next evidence-quality step once the row universe is stable.

## Bottom Line

Under the current strict D/N rule, I found and promoted one more locally available row. I do not see additional locally available rows that can be promoted safely right now.

The remaining meaningful yield is mostly outside the current public-byte policy:

- Ying/Ehrhardt pilot-to-full-scale clinical data, if a public workbook appears.
- RGB pilot-vs-larger-trial health-behavior extraction workbooks, if public files appear.
- Hagen HCSP backing data, if an archive/local cache can recover the deleted sheet.
- The three held FORRT Reversals source-object candidates, if exact source support can be recovered.

If those cannot be obtained, the public-byte-only Figure 1 table is probably close to saturated under the current rules.
