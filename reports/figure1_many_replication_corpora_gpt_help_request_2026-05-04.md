# Figure 1 Many-Replication Corpus Search: What We Did, Why It Fell Short, And What We Need GPT To Find

Date: 2026-05-04

This note is a handoff for GPT or another research assistant. It explains the current Figure 1 corpus-search work, defines the terminology, summarizes what we tried, explains why the new research did not substantially increase the plotted pair count, and asks for targeted help finding many-replication corpora or databases that can actually pass our inclusion requirements.

The short version is that we did not merely search for more papers. We tried to build a reproducible local pipeline for finding, triaging, mirroring, and checking source families that might contain many original-vs-replication result pairs. That pipeline did find more material, but much of it failed one of three hard gates: it was not really a database of replications, it did not expose both effect-size and sample-size information, or it duplicated corpora already represented in the current Figure 1 table.

We should keep looking, but the next search should be much narrower. We need corpora, databases, registries, challenge result sets, or curated repositories that enumerate many replications or reproductions, not isolated one-off replication papers. More importantly, we need sources that can be mirrored locally and checked from raw bytes. A candidate is only useful for Figure 1 if it can get us from source bytes to rows with an original result, a replication or follow-up result, an effect measure or convertible test statistic, and sample sizes for both sides.

## Definitions

This section defines the main terms used in the pipeline and in the request to GPT.

**Figure 1** means the target evidence figure in this repository. The figure compares effect estimates from original studies against effect estimates from later replication or follow-up studies. We are not just counting whether authors said a replication succeeded. We need extractable numerical result pairs.

**Corpus** means a reusable collection that contains multiple studies, claims, findings, effects, replications, reproductions, or follow-up tests. A corpus can be a published project, a database, a Dataverse collection, an OSF project, a GitHub repository, a journal special collection, a challenge venue, or a curated table. In this note, corpus and source family are nearly interchangeable. The key point is that the object should contain many potential result pairs, not just one article.

**Source family** means the parent source object that owns many child artifacts. For example, the Reproducibility Project: Psychology is a source family. Its article, OSF project, GitHub repository, CSV files, R scripts, and converted data files are child source artifacts. We want to keep those relationships explicit so that a future worker can trace every plotted row back to the source family and then to the exact file or table cell.

**Artifact** means a concrete file or retrievable object. Examples include a CSV table, XLSX workbook, RDS file, Stata file, PDF supplement, zip archive, API JSON response, code file, or HTML page. A source family can have many artifacts.

**Mirror** means a local copy of a source artifact. The repository standard is that important evidence should be downloaded or otherwise preserved under `data/raw/`, `data/cache/`, or another documented data path. A link in a chat transcript is not enough. A dynamic browser page is not enough. A metadata landing page is useful for provenance, but it is not evidence of the actual plotted values unless the page itself contains those values.

**Pair** means one original result matched to one replication or follow-up result. A valid Figure 1 pair needs a relationship between the two sides. It should be clear that the replication side is testing the same claim, effect, outcome, or target result as the original side. A row that only describes an original article, or only describes a replication article without a target, is not a pair.

**D** means the standardized effect value used for the Figure 1 comparison. In many psychology sources this is Cohen's d or a close standardized mean-difference analogue. In other sources it can be transformed from test statistics, p-values, correlations, odds ratios, or other reported values if the transformation is documented. We should not silently convert values. The source text and formula or named conversion need to be preserved.

**N** means the sample size attached to the effect. For Figure 1 we need an original N and a replication or follow-up N. The current inclusion logic also checks whether the replication side has at least the minimum sample size and whether it is larger than the original side. Some high-value sources fail because they have effects but no clean N, because they have N but no effect, or because the follow-up N is not larger.

**D/N check** means the pipeline stage that asks whether a corpus can supply enough information for Figure 1: an effect value or convertible effect text and an N for both the original and replication sides. Passing this check does not mean every row is perfect. It means the source has enough structured signal to continue into extraction and verification.

**Strict support** means stronger provenance than just a derived row. A strict row has verbatim or field-level source support for the effect and sample-size values. The current root pair table contains many numeric rows, but fewer rows are ready for promotion into the stricter source-result schema because many still need verbatim source support.

**Ordinary replication package** means a common false positive. In many fields, especially economics and political science, "replication data" or "replication files" often means the data and code needed to reproduce the tables in the original paper. That is computational reproducibility material for one original article. It is not necessarily an independent replication or follow-up study. These records can be useful for other parts of the project, but they do not automatically belong in Figure 1.

**Derived aggregator** means a table or repository that reuses already-known replication projects. For example, a meta-analysis of RPP, Many Labs, or EERP may contain original and replication effects, but if those rows are already covered by the canonical project sources, adding the aggregator as another corpus would double-count the same results. Derived aggregators can be valuable for cross-checking, deduplication, or finding missing metadata, but they should not be promoted blindly as new Figure 1 rows.

## Current State

The current Figure 1 work has three useful summary outputs.

The D/N check report is:

`steps/corpus_results/figure1/dn_check/figure1-corpus-dn-check.md`

The root pair table is:

`FIGURE1_REPLICATION_PAIRS.tsv`

The raw viability summary is:

`steps/corpus_results/figure1/figure1-raw-viability-summary.md`

As of this handoff, the D/N check reports 36 local project labels with numeric D/N pairs. Across those labels, the root table has 2,254 numeric pair rows. Of those, 1,548 currently pass the minimum sample-size and larger-replication-N checks used for Figure 1 inclusion. The strictest support layer is much smaller: 160 strict verbatim pair rows, with 60 passing the same sample-size checks.

The root pair table has 2,254 rows and 36 project or source-family labels. It currently marks 1,548 rows as included under the current Figure 1 D/N rule. It also marks 138 rows as ready for source-result side promotion. Most rows, 2,108 of them, still need verbatim source-result support before they would satisfy the more rigorous evidence-table standard.

The raw viability summary is more conservative because it starts from mirrored source artifacts and asks whether generic parsing found rows with effect text, N text, and pair context. It checked 16 parent source-family keys, saw 1,869 local or mirrored artifacts, and recorded 199 newly downloaded artifacts. A generic parser emitted 796 native rows, but only 421 rows currently have both effect text and N text. Only two parent keys passed the raw-data viability gate by generic parsing: `raw_corpus:rpcb` and `many_labs_2 | doi:10.1177/2515245918810225`.

That mismatch is important. The root Figure 1 table is bigger because it uses project-specific builders and legacy extractions. The raw viability stage is stricter and more generic. It asks whether the mirrored raw files, without project-specific assumptions, expose the values we need. Many existing corpora can be made usable with custom parsers, but the generic mirror-and-check stage only confirms a smaller subset automatically.

## What We Did

We started by trying to recover from a failed Codex session that ran out of context while clearing the Figure 1 review queue. The queue contained candidate source-family leads from search and review-cue outputs. The goal was to finish triaging those leads, record decisions in file-based artifacts instead of chat, regenerate the routing table, mirror the relevant source artifacts locally, and then check whether the raw data could support Figure 1.

The relevant review-cue machinery is configured in `PROVENANCE_PIPELINE_SINGLE_SOURCE_OF_TRUTH.yml`. The workflow produces bounded review batches under `steps/review_cue/<cue_id>/`. The specific cue for this work is `figure1_search_leads`. The review cue produces Markdown indexes and JSON decision files. Decisions are supposed to be applied to per-lead receipt files, not directly to root tables. After application, the machine-readable routing table is regenerated and downstream steps consume that table.

We incorporated returned GPT-style research decisions from the user. Those decisions classified clusters into categories such as `keep_source_family_candidate`, `inventory_source_family_artifacts`, `route_cluster_to_result_table_worklist`, `route_cluster_to_individual_replication_paper_worklist`, `keep_cluster_as_context`, and `no_public_artifact_found`. The important distinction is that not every interesting source should become a Figure 1 corpus. Some are context sources, some are individual papers, some are child artifacts under an existing parent, and some are duplicates.

We then focused on the source families and corpora that looked most relevant to Figure 1. The pipeline mirrored or inspected many local artifacts and newly downloaded artifacts. Mirroring means we tried to preserve the files locally so that later extraction does not depend on a live web page or a browser session. The instructions in `AGENTS.md` emphasize that evidence rows must be retraceable from raw bytes to final plotted values. That standard shaped the whole effort.

We built or regenerated the D/N check stage for corpora relevant to Figure 1. The D/N check is not the final extraction. It is the viability test. It asks: does this source have original and replication values with effect information and sample-size information? For each parent source family, it tries to determine whether the data are merely mirrored, parsed but missing D/N signal, parsed with D/N signal, or already covered by another parsed parent.

We also generated the root pair table. This is the obvious table at the repository root, `FIGURE1_REPLICATION_PAIRS.tsv`, that collects the current pair-level outputs. This table is intentionally not the end of provenance. It is a root-level working table that can be used to see what pairs the figure currently has. The stricter provenance model still expects source tables, access tables, file tables, source-result rows, support rows, canonical-result rows, and plot-membership rows. The root table is a practical bridge so we can see progress and counts while the deeper provenance system matures.

During the work we checked several specific candidate corpora that looked promising in the new research. We inspected the COVID-era online experiment generalizability package, the Brodeur/Cook/Mikola statistical reproducibility material, the ecological and evolutionary in-silico replication dataset, Political Science Unlock materials, and the Heyard/Held heterogeneity-in-replication-projects Zenodo/GitLab repository. The outcome was mixed: several were real and interesting, but they did not add many new eligible Figure 1 rows under the current criteria.

We also repaired one concrete bug in the COVID/YCLS promotion script. The script is `scripts/promote_covid_online_summary_pairs.py`. Two Press et al. strike outcomes were not being promoted because the mapping looked for outcome groups that were missing in the standardized rows. The usable labels were in the `outcome` field. We mapped `psv_retrospective_approve_binary_s` to `Approve Strike (Nuclear)` and `psv_retrospective_ethical_binary_s` to `Ethical Strike (Nuclear)`. We added support fields for the N source file, verbatim original N text, verbatim replication N text, and a D/N transformation note in the generated promoted CSV.

After that fix, the root row count increased from 2,252 to 2,254. The two restored rows were `covid_online_approve_strike_nuclear` and `covid_online_ethical_strike_nuclear`. They have usable D and N values, but both are excluded by the larger-N rule because the replication-side N is smaller than the original-side N. This is a good example of why the work can improve correctness without increasing the plotted count.

## Why It Fell Short

The main reason the effort fell short is that discovery and eligibility are different problems. Discovery asks whether we can find candidate sources that look relevant to replication. Eligibility asks whether those sources contain many original-vs-replication pairs with D and N values that meet the Figure 1 rules. The new search work found many candidates, but many of them were not eligible after inspection.

The first failure mode is lexical false positives. The word "replication" appears in many source titles, repository names, and data archives, but it does not always mean independent replication of a published result. In data repositories, "replication files" often means the files needed to reproduce the original article's tables. For Figure 1, that is not enough. A computational reproduction package may have code, data, and even effect estimates, but if it does not contain a later replication or follow-up result matched to the original result, it does not give us a Figure 1 pair.

The second failure mode is one-off papers. Many sources are genuine replication papers, but they contain one original finding and one replication attempt, or a small number of outcomes from one replication package. Those are not useless. They may belong in an individual replication-paper worklist. But the current request is specifically about corpora and databases of many replications. We should not spend the next GPT search on one-off papers unless they are part of a larger source family that has a reusable multi-row table.

The third failure mode is source-family pages with no extractable table. Some projects have excellent landing pages, descriptions, preregistrations, or publication lists, but no public file inventory, no downloadable table, no result workbook, or no raw data that can be mirrored. Under this repository's replicability standard, a web page saying the project exists is not enough. We need source bytes that a future worker can retrace.

The fourth failure mode is missing D or missing N. Some databases have success/failure labels, qualitative replication assessments, p-values without enough context, or original/replication links without sample sizes. These sources may be valuable for discovery or deduplication, but they do not pass the D/N check unless we can compute or extract the missing values from a reliable source. Figure 1 needs numerical effect and sample-size information. A database with 500 replication labels but no extractable D and N is not a direct pass.

The fifth failure mode is the larger-N rule. Some sources have original and replication values, but the follow-up sample is not larger than the original sample. The COVID/YCLS strike rows are a concrete example. They were restored into the root pair table, but they did not increase the included count because the replication N was smaller.

The sixth failure mode is duplicate coverage. Several new candidates are derived aggregators over projects we already know: RPP, Many Labs, EERP, SSRP, RRR, and related large-scale psychology projects. These sources can be very useful as cross-checks, but we cannot count the same underlying original-replication pairs again merely because another paper or repository reanalyzed them. We need canonical result IDs and mapping tables to deduplicate later. Until then, new aggregators should be treated cautiously.

The seventh failure mode is generic parsing limits. Some mirrored source families are real and probably usable, but their values are embedded in RDS files, Stata files, scripts, zip archives, custom model outputs, or non-obvious table structures. A generic parser may say "no effect/N signal" even when a project-specific parser could extract the values. This means the raw viability report is not the final truth. It is a conservative automated check. However, from the GPT-search perspective, this limitation matters because a new candidate is much more useful if it exposes a clear table with obvious original and replication fields.

The eighth failure mode is criteria mismatch across fields. Machine learning reproducibility challenges, healthcare database reproducibility projects, computational reproducibility studies, and in-silico replication projects may be large and important, but their result measures may not map cleanly to D. They may report accuracy, AUC, benchmark score, hazard ratio, regression coefficient, p-value reproducibility, or qualitative robustness. Some of those could be transformed with enough information, but many would require relaxing Figure 1's current assumptions. The user explicitly asked not to relax requirements, so those sources remain questionable unless they have a defensible D-like effect and N on both sides.

## What Passed, What Was Already Covered, And What Did Not Add Rows

The current root table already contains 36 project or source-family labels with numeric D/N pairs. The exact label list lives in `FIGURE1_REPLICATION_PAIRS.tsv` and the D/N report. The important conceptual point is that the project is not starting from only 11 known collections anymore. The stricter raw mirror viability stage confirmed fewer parents automatically, but the root pair table reflects many more project-specific extractions and legacy builders.

Known or partially covered source families include large psychology and metascience projects such as the Reproducibility Project: Psychology, Registered Replication Reports, Many Labs projects, Many Labs 5, SCORE-related material, LOOPR, FReD-adjacent or curated psychology replication rows, decision-market replication material, experimental economics and social-science replication projects, and several field-specific corpora. Some of these are cleanly integrated. Others are represented but still need stricter source-result support before they meet the highest provenance standard.

The Reproducibility Project: Cancer Biology remains one of the strongest raw-data passes. Its final analysis data include paper-level, experiment-level, and effect-level tables with dictionaries. It is a real many-replication source family and has source artifacts that can be mirrored and inspected locally.

Many Labs 2 also passed the raw-data viability gate. It is a large-scale replication source family with many samples and target effects. It has structured data and code resources that can support D/N extraction.

The COVID online experiment package was already covered by a project-specific promoter. The repair restored two missing numeric rows, but those rows do not pass the larger-N inclusion rule. The package still matters because it shows that custom parsers can rescue rows the generic raw viability stage may not fully understand.

The Brodeur/Cook/Mikola statistical reproducibility material looked promising because it is large and cross-field. But inspection showed that the relevant Stata table is about statistical reproducibility and robustness of economics and political-science articles. It contains fields such as coefficients, p-values, standard deviations, t-statistics, and observations by article. It is same-data reproduction or robustness evidence, not a direct independent original-vs-larger-N replication pair table. It should not be promoted to Figure 1 as new pairs without relaxing the concept of replication.

The ecological and evolutionary in-silico replication dataset looked promising because it is large and effect-oriented. It contains meta-analysis and in-silico replication effect rows, with fields such as effect size, variance, standard error, and z. But it does not appear to provide a direct independent original-vs-larger-N replication pair table in the sense required for Figure 1. It may be relevant to a separate figure or broader discussion of replicability, but not this strict pair table without additional methodological decisions.

Political Science Unlock contains many Dataverse and GitHub artifacts. Some are metadata, some are code, and some are workbooks. But much of the political-science "replication data" universe means reproduction packages for original articles. One inspected master sheet had rows labeled as original studies and no replication rows. Other files were planned or registered trials, or ordinary article replication packages. We did not find a direct many-row original-vs-replication D/N table there.

The Heyard/Held heterogeneity repository on Zenodo is a strong derived aggregator. It contains a data table with original and replication effect sizes, p-values, and sample sizes for projects including Many Labs 1, Many Labs 3, RPP, and EERP. The table has hundreds of rows and many pass the larger-N check. However, these are not new source-family rows if the underlying projects are already represented. This source should be used as a cross-check and dedupe aid, not as a new plotted corpus unless we identify rows that are missing from the canonical project sources.

## What We Need GPT To Find Now

The next GPT search should be targeted at many-replication corpora or databases that are not already represented and that can plausibly pass the D/N check. We should not ask GPT for "more replication papers" in general. We should ask for source-family objects with downloadable or inspectable data.

A candidate should have a stable landing page and at least one concrete acquisition route. Examples of acquisition routes include an OSF project with public files, a Dataverse dataset or collection with files, a Zenodo record with a zip archive, a Figshare or Dryad record with downloadable files, a GitHub repository with data tables, an OpenReview venue export with report metadata, or a project website with downloadable CSV/XLSX/R/Stata files.

A candidate should have many target studies, findings, claims, effects, or replication reports. "Many" does not need to mean thousands. A source family with 20 clean pairs can matter if it fills a gap. But a single replication paper with one pair should not be proposed for this specific task.

A candidate should provide evidence of original-replication mapping. This can be explicit columns such as original DOI and replication DOI, target study and replication study, original effect and replication effect, claim ID and replication report ID, or original paper title and replication paper title. Narrative descriptions are weaker but may be acceptable if the source contains a structured table.

A candidate should provide effect and N evidence. Ideal columns are `original_effect`, `replication_effect`, `original_n`, and `replication_n`, or close variants. Acceptable alternatives include test statistics, standard errors, p-values with enough degrees of freedom, correlations, odds ratios with sample sizes, raw data and code sufficient to compute D, or codebooks that explain how to compute them. A candidate with only success/failure labels is not enough.

A candidate should not merely rehost already-known projects unless it adds missing rows, missing source support, or a better canonical table. If a source is a derived aggregator over RPP, Many Labs, EERP, SSRP, RRR, SCORE, RPCB, or FReD, GPT should say so explicitly and explain whether it appears to add new source-family content or only duplicates existing rows.

A candidate should distinguish independent replication from computational reproduction. We can include computational reproduction only if the project definition and Figure 1 criteria allow it and if the result has a comparable original and reproduced estimate with sample size. For now, the safer instruction is to prioritize independent replication, new-data replication, registered replication, large-scale replication, or explicit follow-up tests.

## Known Sources To Avoid Duplicating Unless There Is A Missing Table

GPT should not spend most of its effort rediscovering the famous projects unless it can identify a specific missing table or missing subset. Already-known or partially covered families include:

- Reproducibility Project: Psychology / Open Science Collaboration / RPP.
- Reproducibility Project: Cancer Biology / RP:CB.
- Registered Replication Reports in psychology.
- Many Labs 1, Many Labs 2, Many Labs 3, Many Labs 4, and Many Labs 5.
- Experimental Economics Replication Project / EERP.
- Social Sciences Replication Project / SSRP.
- SCORE and SCORE-adjacent outputs.
- FReD, CurateScience, CORE, Data Replicada, and FORRT-adjacent psychology replication collections, to the extent already represented or routed.
- LOOPR and related psychology large-scale replication projects already in the root pair table.
- Brazilian Reproducibility Initiative if GPT only finds the same already-known public project pages; however, GPT should still look for a master table with more complete effect/N fields if our current extraction is incomplete.
- Sports Science Replication Centre if GPT only finds the same project page; however, GPT should look for additional downloadable pair-level data beyond what is already integrated.
- Decision-market replication data if GPT only finds the already-known Nature Human Behaviour/OSF project.
- COVID-era online experiment generalizability package if GPT only finds the same Dataverse package.
- Awesome Replicability Data / Ying curated datasets if GPT only finds the same GitHub repository without new eligible pair tables.
- Clinical phase II/III or highly cited clinical replication datasets already represented in current project-specific builders.

If GPT finds one of these sources, it should not simply report "found." It should answer: does this source contain rows that are missing from our current root table, or does it provide better source-result support for rows we already have?

## High-Value Targets Still Worth Checking

The following targets are worth a focused pass because they are plausible many-replication source families but may not yet be fully confirmed as D/N-passing corpora.

FReD / FORRT Replication Database remains high value. The key question is whether there is a downloadable export or R package with original and replication effects, sample sizes, source-family labels, and stable identifiers. If it only provides a web interface, GPT should identify whether any export is available and whether the data license permits mirroring.

Institute for Replication / I4R / Replication Games is high value but risky. It may contain many reproductions and robustness checks rather than independent replications. GPT should look for a structured index of reports and, more importantly, a table linking original article, reproduction or replication report, effect estimate, standard error or p-value, and sample size. If the output is mostly same-data robustness checks, it should be classified as not a Figure 1 pass unless a specific subset has independent follow-up data.

Brazilian Reproducibility Initiative remains worth checking for completeness. We need to know whether public OSF, GitHub, Dataverse, or NLM records contain a master effect table with original and replication sample sizes and effect estimates. If there is a table beyond what we already mirrored, GPT should report exact URLs and file names.

REPEAT Initiative is potentially important for healthcare database research. The key question is whether the public outputs include a 150-study or similar table with original and reproduced measures of association, sample sizes, and target publication identifiers. If it only provides project descriptions or qualitative reproducibility status, it does not pass.

Sports Science Replication Centre is worth checking for a project-level result table. GPT should look for downloadable data files, supplements, or OSF tables listing target studies, original effects, replication effects, and sample sizes. If the public material is only a paper and a project page, it should be marked as needing manual acquisition.

X-Phi Replicability Project could be useful if a master table exists. A web page listing replications by original paper is useful for mapping, but Figure 1 needs numerical effect and N fields. GPT should check Yale pages, OSF pages, supplements, and any project data archive.

CORE Judgment and Decision Making, Data Replicada, CREP, and Hagen Cumulative Science Project should be checked only for multi-row exports or structured tables. These projects are likely real replication sources, but they may be fragmented into individual OSF projects, blog posts, student reports, or FReD rows. A source-family table would be valuable; a list of one-off project pages is less useful.

ReplicationWiki may be useful as a source-family database, but it might lack effect sizes or sample sizes. GPT should determine whether it has structured fields for replication outcomes, original publications, replication publications, and quantitative results. If it is mainly a bibliographic registry, it can support discovery but may not pass D/N.

ML Reproducibility Challenge and ReScience C are interesting but need careful handling. They are many-report source families, but their outcomes are often benchmark metrics rather than D-like effects. GPT should only propose them as Figure 1 passes if it can identify normalized original-vs-reproduced metrics with N or sample-size analogues that can be defensibly transformed. Otherwise they should be context or separate-figure candidates.

## Specific Prompt To Give GPT

Use the following prompt as the next GPT handoff. The point is to get candidates that can pass our strict Figure 1 requirements, not a broad literature review.

```text
We are building a Figure 1 dataset of original-vs-replication or original-vs-follow-up result pairs. We need help finding many-replication corpora, databases, registries, project repositories, challenge datasets, or curated tables that can actually pass our extraction rules.

Definitions:

- A corpus/source family is a reusable source object that contains many replication or follow-up results, such as an OSF project, Dataverse collection, Zenodo/Figshare/Dryad record, GitHub repository, database, registry, challenge venue, or downloadable project table.
- A pair is one original result matched to one replication or follow-up result for the same claim, finding, outcome, or target effect.
- D means a standardized effect value, or a value that can be defensibly converted to one with a documented formula.
- N means the sample size for the original result and for the replication/follow-up result.
- A candidate passes only if it can plausibly provide original and replication/follow-up effect information and sample-size information for many pairs, or raw data/code sufficient to compute them.

Do not give us ordinary "replication data for [article]" packages unless the article is itself a replication/follow-up study or the package contains multiple original-vs-replication pairs. In many fields "replication data" just means data/code for reproducing the original article's own tables; that is not enough.

Do not give us one-off replication papers for this task. We are specifically looking for corpora/databases/source families of many replications.

Do not give us already-covered famous projects unless you find a missing downloadable table or missing subset. Already-known or partially covered examples include RPP/Open Science Collaboration, Reproducibility Project: Cancer Biology, Registered Replication Reports, Many Labs 1/2/3/4/5, EERP, SSRP, SCORE, FReD/CurateScience/CORE/Data Replicada/FORRT-adjacent psychology sources, LOOPR, Brazilian Reproducibility Initiative, Sports Science Replication Centre, Decision Markets, COVID online experiment generalizability data, Ying/Awesome Replicability Data, and clinical phase II/III replication datasets.

Task:

Find 10 to 20 candidate many-replication corpora/databases/source families that are most likely to pass the Figure 1 D/N requirements and are not simply duplicates of the sources above. For each candidate, check the actual landing pages, repository files, data records, supplements, or API metadata. Prefer sources with downloadable tables, file inventories, codebooks, or archives. If a source fails, include it only if it is a high-profile false positive we should explicitly exclude.

For each candidate, return valid JSON with these fields:

- candidate_name
- domain
- source_family_type: database, corpus, registry, project, challenge_venue, repository, journal_gateway, derived_aggregator, or other
- source_family_url
- stable_identifier: DOI, OSF GUID, Dataverse DOI, Zenodo DOI, GitHub repo, OpenReview group, registry ID, or other stable ID
- data_download_urls: list exact download or file-list URLs that appear to work
- evidence_it_has_many_replications: compact explanation with source citations
- evidence_of_original_replication_mapping: describe columns, tables, report fields, or page text that links original and replication/follow-up targets
- evidence_of_effect_fields: describe effect-size, statistic, p-value, estimate, standard-error, or raw-data fields
- evidence_of_n_fields: describe sample-size fields for original and replication/follow-up sides
- estimated_pair_count
- already_covered_risk: low, medium, high
- likely_pass_decision: likely_pass, maybe_pass_after_custom_parser, context_only, duplicate, or likely_fail
- failure_reason_if_any
- exact_files_to_mirror_first
- sources_checked: list URLs checked
- next_local_mirror_action

Prioritize sources where the exact files can be downloaded or mirrored locally. Be skeptical. Do not infer that a source passes from a title alone. If a candidate only has success/failure labels and no effect or N fields, mark it likely_fail or context_only. If it is a derived aggregator over already-known projects, mark duplicate unless it clearly adds missing rows or better source support.
```

## Suggested Search Strategy For GPT

Start with source-object terms instead of paper terms. Use phrases such as "replication database original replication effect size", "replication workbook original_n replication_n", "replicability codebook original study replication study", "many-lab replication data effect size", "replication registry sample size effect", and "reproducibility challenge original paper results table".

Then search specific surfaces where many-replication corpora are likely to live:

- OSF project pages and OSF file inventories.
- Dataverse datasets and Dataverse collections.
- Zenodo, Figshare, and Dryad records with downloadable files.
- GitHub repositories with data directories, codebooks, CSVs, RDS files, Stata files, or notebooks.
- OpenReview venue/group pages for challenge datasets.
- RePEc, I4R, and economics reproduction project pages.
- NLM Dataset Catalog, Europe PMC, and project pages for biomedical reproducibility initiatives.
- FORRT and FReD-related pages for psychology source-family discovery.
- Journal special collections only when they expose a structured table or project-level data archive.

Use negative filters aggressively. Exclude computer-system replication, database backup replication, DNA/RNA/viral/cell replication, manufacturing replication, and ordinary article reproduction packages. In biomedical searching, the word replication is especially noisy because it often refers to biological replication rather than replication of scientific findings.

For every promising source, GPT should open or inspect enough material to answer one concrete question: where is the table or raw-data route that would let us mirror bytes and extract original D, original N, replication D, and replication N? If that route is absent, the source may still be useful, but it should not be labeled as a pass.

## What A Good Answer Would Look Like

A good GPT answer would not be a list of 50 vaguely relevant projects. It would be a short, skeptical list of candidates with exact files and pass/fail reasoning.

For example, a strong candidate would say something like: this Dataverse dataset has a CSV named `replication_results.csv`; the codebook defines `orig_d`, `orig_n`, `rep_d`, `rep_n`, `target_doi`, and `replication_doi`; the landing page says it contains 75 direct replications; the download URL is stable; and it does not appear to overlap with RPP, Many Labs, EERP, SSRP, SCORE, or RPCB. That is likely to pass.

A maybe-pass candidate would say: this project has 120 reports and a GitHub repository; the reports identify original papers and reproduced metrics; however, sample sizes are embedded in PDFs or notebooks and the metric may not convert to D. That would require a custom parser and methodological review.

A useful negative candidate would say: this collection has hundreds of "replication data" deposits, but they are journal reproduction packages for original articles and do not contain independent replication results. That should be excluded from Figure 1 and perhaps kept only as context.

The main thing GPT can add is not generic web search. It can add source-specific judgment. We need it to verify whether a candidate has the right grain: many rows, original and replication sides, effect information, sample-size information, stable identifiers, and mirrorable files.

## Bottom Line

The pipeline did not fail because it found nothing. It found a lot of relevant-looking material. It fell short because the stricter Figure 1 rules are doing their job. Many candidates are context, one-off papers, ordinary reproduction packages, source-family pages without data, missing-D/N sources, not-larger-N pairs, or derived duplicates of already-covered projects.

The next step is therefore not "search broader." It is "search more selectively." We should ask GPT to find many-replication corpora or databases with exact downloadable files and explicit original/replication D/N evidence. Anything else can be routed to context, individual-paper review, manual acquisition, or dedupe support, but it should not be counted as a new Figure 1 source family until it passes the same gates.
