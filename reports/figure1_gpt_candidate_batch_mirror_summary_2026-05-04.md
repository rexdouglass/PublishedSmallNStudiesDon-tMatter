# Figure 1 GPT Candidate Batch Mirror Summary

Date: 2026-05-04

This report summarizes the user-supplied GPT candidate batch for Figure 1 many-replication corpora/databases. The batch has been turned into a rerunnable mirror manifest in `scripts/mirror_figure1_gpt_many_replication_candidates.py`.

Large mirrored files are intentionally stored under:

`data/raw/replication_projects/lead_harvest/gpt_many_replication_candidates_20260504/`

That directory is covered by the repository's raw-data gitignore rule. Compact tracked ledgers are under:

`steps/source_inventory/figure1/gpt_many_replication_candidates_20260504/`

## Generated Ledgers

- `candidate-intake-ledger.tsv`: one row per candidate in the GPT batch, including priority and initial classification.
- `mirror-status.tsv`: exact URL attempts, HTTP status, content type, local path, file size, and SHA-256 for focused mirrored candidates.
- `provider-metadata-status.tsv`: OSF/Zenodo API inventory attempts.
- `discovered-download-urls.tsv`: concrete download URLs discovered from OSF, Zenodo, or mirrored HTML pages.

The final focused run excluded already-covered and duplicate-support branches, so it did not spend extraction time on BRI, EPRP, Management Science, Sports, or FReD. Earlier interrupted broad runs did leave additional ignored raw bytes under the same raw directory, including BRI and FReD OSF members; those are not represented in the focused status ledger.

## Already Covered In Current Figure 1 Build

Several of the GPT "mirror first" suggestions were not actually net-new for this repository:

- Experimental Philosophy Replicability Project / X-Phi: already mirrored as `data/raw/replication_projects/eprp/XPhiReplicability_CompleteData.csv`; current root pair table has 34 EPRP rows, 27 included by the current D/N rule, plus one Appendix D supplemental row.
- Brazilian Reproducibility Initiative: already mirrored and integrated from the public primary-analysis experiment table; current root pair table has 45 BRI rows, 21 included.
- Sports Science Replication Centre: already mirrored as sports workbooks/supplemental tables; current root pair table has 19 sports rows, 16 included.
- Management Science Replication Project: already mirrored from project reports and integrated; current root pair table has 26 MSRP rows, 20 included.

These sources remain valuable for support/provenance work, but they should not be counted as net-new corpus discoveries.

## Net-New Leads That Look Actionable

### Experimental Asset-Market Replications

Candidate key: `asset_market_replications`

Focused mirror result:

- OSF node `uxrgk` worked through the OSF API.
- OSF node `aepxt` returned 404 through the API but the landing page was mirrored.
- SSRN/DOI pages returned 403 from automated download.
- Three OSF files were mirrored:
  - `Experimental_instructions.pdf`
  - `InternetAppendix.pdf`
  - `Manuscript.pdf`

Why it matters:

The Internet Appendix appears genuinely Figure 1-relevant. It reports direct replication hypothesis tests for 17 key results and includes original and replication effect estimates in Cohen's d units plus sample sizes. The PDF text explicitly states that the original and replication columns report effect-size estimates in Cohen's d units, with `d = 2 * t / sqrt(n)`, and reports `n` for replication tests.

Current assessment:

`likely_pass_after_pdf_table_parser`. This is probably the strongest net-new lead in the batch. It needs a PDF table extractor or manual table parser for Appendix H and the underlying replication-hypothesis sections.

Expected pair count:

About 17 target results, before any robustness/sensitivity rows are excluded.

### Sensory-Marketing Replications

Candidate key: `sensory_marketing_replications`

Focused mirror result:

- OSF node `tnmvq` worked through the OSF API.
- 32 OSF download URLs were discovered and mirrored.
- Mirrored files include per-study R scripts, replication-analysis XLSX workbooks, Qualtrics survey PDFs, the article landing page, and a Frontiers full-text HTML mirror.

Important mirrored files include:

- `Chae_Hoegg_analysis.xlsx`
- `klink_analysis.xlsx`
- `shrum_analysis.xlsx`
- `saturation_analysis.xlsx`
- `Romero_analysis.xlsx`
- `yorkston_menon_analysis.xlsx`
- `Elder_Krishna_analysis.xlsx`
- `Jian_analysis.xlsx`
- `Cian_analysis.xlsx`
- `Madzharov_Block_analysis.xlsx`

Why it matters:

The mirrored Frontiers article contains extractable HTML tables. Table 0 lists the ten original studies and original sample sizes/effects. Table 4 contains original and replication effect sizes, lower/upper confidence intervals, power, and estimated sample sizes. The OSF workbooks hold replication-side raw or analysis data; most have 823 rows, which appears to be the common replication sample size for several studies.

Current assessment:

`likely_pass_after_custom_parser`. This can probably contribute either 10 study-level rows or up to 48 hypothesis/dependent-variable rows, depending on the row-grain decision. A custom parser should preserve the article's r-scale values and convert to the common D axis using the repository's existing `r_to_d` helper, with source text retained.

Main blocker:

The table grain needs a decision. Some studies have several hypotheses or dependent variables. We should avoid inflating counts by treating dependent-variable variants as independent findings unless the original article/project clearly intended those as separate target effects.

## Real But Lower-Priority Or Methodologically Risky

### Transparent Replications

Candidate key: `transparent_replications_clearer_thinking`

Focused mirror result:

- Three Zenodo records worked through the Zenodo API.
- Three Zenodo report PDFs were mirrored with distinct URL-hash filenames:
  - `TransparentReplications2023pnas120-30.pdf`
  - `TransparentReplications2022psci33-8.pdf`
  - `TransparentReplications2022pnas119-34.pdf`
- The Clearer Thinking site also exposed many report pages and support pages, which were mirrored as HTML.

Why it matters:

Some reports contain enough source text for individual Figure 1 pairs. For example, the Litovsky et al. report includes original chi-square/N/Phi text and replication chi-square/N text. The Devine et al. report includes original and replication N and beta/SE values, though the replication N is smaller than the original N. The Ceylan et al. report is an evaluation/reproduction problem report rather than an actual replication.

Current assessment:

`individual_report_worklist`, not a clean corpus-table pass. This is a real source family, but no master pair table was confirmed. It needs report-by-report parsing and eligibility screening. Some reports will fail because they are evaluations, not replications; others may fail the larger-N rule.

### REPEAT Initiative

Candidate key: `repeat_initiative`

Focused mirror result:

- OSF node `my5gn` worked through the OSF API.
- Mirrored files include Supplementary Data XLSX/DOCX files, a tables/figures workbook, and zip archives.
- Important mirrored files include:
  - `Supplementary Data 5 List of reproduced studies.xlsx`
  - `REPEAT_03_tables_figures.xlsx`
  - `Supplementary Data 6 Analysis file, code, data dictionary.zip`
  - `Supplementary Data 4 Study specific author contact files with details of implementation.zip`

Why it matters:

REPEAT is a large, structured reproducibility project with around 150 healthcare-database reproductions. It has measures of association and study-size information.

Current assessment:

`methodology_review_before_figure1`. It is strong structured evidence, but it is probably outside the strict current Figure 1 definition because it is same-database real-world-evidence reproduction rather than independent new-sample replication, and because HR/RR/OR-to-D conversion plus cohort-size interpretation needs explicit approval.

### Replicability Project: Health Behavior

Candidate key: `replicability_project_health_behavior`

Focused mirror result:

- COS `https://www.cos.io/rphb` page mirrored.
- The older COS initiatives URL returned 404.
- OSF API for `pxmj9` returned 401 unauthorized.
- Public OSF landing page was mirrored but no result files were accessible through the API route.

Current assessment:

`context_only_pending_public_results`. This should be rechecked when public final results are available, but it does not currently pass the mirrorable D/N table gate.

## False Positives / Context Sources

The focused mirror also preserved lightweight context for several likely recurring false positives:

- CREP: OSF page/API metadata mirrored, but no aggregate D/N export confirmed.
- 3ie Replication Paper Series: useful index of internal/same-data replications, but not a clean many-row original-vs-new-replication D/N table.
- I4R / Replication Games: useful discovery surface, but current metadata is dominated by computational reproduction and robustness checks.
- ReplicationWiki: registry/discovery source; no effect/N fields confirmed and automated access had issues.
- ML Reproducibility Challenge: many reports but benchmark-metric/N mismatch under current Figure 1 rules.
- ReScience C: many computational replications but not a D/N original-vs-larger-N corpus under current rules.

## Recommended Next Work

1. Build an asset-market parser from the mirrored `InternetAppendix.pdf`.
   - Target Appendix H plus replication-hypothesis sections.
   - Extract original d, original N where present, replication d, replication N, p-value, and target-result label.
   - Expected yield: about 17 rows.

2. Build a sensory-marketing parser from the mirrored Frontiers HTML and OSF workbooks.
   - Extract article Table 0 and Table 4.
   - Decide whether the row grain is 10 target studies or 48 hypothesis/dependent-variable rows.
   - Convert r to D using the existing helper and preserve r-scale verbatim source values.
   - Expected yield: 10 to 48 rows depending on grain.

3. Put Transparent Replications into an individual-report extraction queue.
   - It is not a clean corpus table, but several reports have enough D/N-like evidence for one-off rows.
   - Do not batch-promote without report-level eligibility review.

4. Keep REPEAT as methodology-review material.
   - It is well mirrored and structured, but should not enter Figure 1 unless the scope explicitly includes same-database reproductions and ratio-measure conversion.

5. Do not spend more Figure 1 corpus time on EPRP, BRI, MSRP, Sports, or FReD as "new" sources.
   - They are already covered or duplicate/support material.
   - Future work there should be source-result support/provenance hardening, not new pair discovery.
