# Figure 1 Search Strategy: Current Plan, Constraints, and Open Questions

This memo summarizes our current search strategy for Figure 1 and the way we are operationalizing it now. It is written as a self-contained handoff for asking GPT for suggestions. The core point is that we are no longer treating Figure 1 discovery as a one-time manual literature search or a global scraper. We are treating it as a staged provenance pipeline: define the universe, search for possible source families, preserve every search attempt as a target file, deterministically reject or route obvious non-targets, use Codex for bounded triage, use GPT only for occasional source-aware field coding or larger outside review, and only then propose updates to the root corpus/database table.

The operating constraints matter. We are doing this "free-ish." That means we have Codex in the repo, public APIs, local scripts, already-mirrored files, browser/manual inspection when necessary, and rare copy/paste handoffs to GPT. We are not assuming a paid discovery platform, a licensed bulk bibliographic index, paid web search API quotas, enterprise screening software, or a large human review team. We also do not want a brittle global web scraper that runs across everything and produces a pile of unauditable state. The plan must be cheap, resumable, transparent, and robust to interruption.

The immediate target is Figure 1 only. We are explicitly not throwing away sources that might support later figures, but the current top-of-pipeline work is focused on finding corpora, databases, repositories, source tables, and replication-project sources that could expose Figure 1 original/replication pairs. Later figures may reuse sources or define different inclusion criteria, but the current search funnel is for Figure 1 source discovery.

## 1. What Figure 1 Needs

Figure 1 is about original/replication or original/follow-up pairs. The key unit is not simply a paper and not simply a result. It is a relationship between an original study/result and a later replication, reproduction, follow-up, registered replication report, multi-lab replication, or similar attempt that lets us compare effect sizes and sample sizes. The plot shows pairs. For this universe, we do not require that the replication be a conventional published journal article. We only require that the source exposes or can lead us to a replication/follow-up relationship and enough information to eventually recover D and N or native inputs that can be converted to D and N.

That design choice affects search. If the plot requires pairs, it is usually more efficient to search for replications first and then resolve the original, rather than starting with all possible original papers and asking whether they were ever replicated. In the first pass we mostly did this by hand, drawing on known replication projects and datasets. Now we want an extensible search system that can keep expanding the universe without losing track of what has already been tried.

The top-level strategy is therefore corpus/database first. We search for collections that may already contain many pair rows: replication databases, reproducibility projects, registered replication report collections, multi-lab projects, OSF projects with coded data, Dataverse packages, DataCite dataset records, known source families like RPP or RP:CB, and local table/code artifacts that already contain pair-like fields. Individual replication papers are not ignored, but they are routed to a separate worklist. For the current step, a source that only describes one replication paper should not be allowed to pollute the corpus/database table unless it is itself a route to a multi-row source family or package.

The main positive inclusion idea for Figure 1 source discovery is:

- The source may contain multiple studies, papers, claims, trials, replication attempts, or pair rows.
- The source may expose original/replication relationship fields, D/N fields, p-values, standard errors, means/SDs, outcome labels, or conversion inputs.
- The source has a retrievable lead: a URL, DOI, repository page, local path, code package, article, appendix, supplement, or file inventory.
- The source can plausibly be inventoried and parsed later without relying on memory or an ephemeral browser session.

The main negative routing idea is:

- A single individual replication paper should be routed to an individual-paper worklist, not accepted as a corpus/database.
- A methods paper, review, editorial, or conceptual article should be kept as context only unless it names a source table, package, or corpus.
- A repository package for one ordinary paper should be routed away unless it contains a reusable multi-row database or pair table.
- A false positive, such as database-systems replication or unrelated software/database terminology, should be rejected deterministically and retained as a record of the failed search.

We keep rejected and routed items because search attempts are part of provenance. A future worker should be able to tell why a search string was tried, what it found, what was rejected, and what should not be re-reviewed.

## 2. The Cheap, Resumable Operating Model

The most important process rule is that every concrete search attempt writes a target file. The target files live under:

```text
steps/searches/figure1/
```

They are named in a human-readable way, for example:

```text
corporasearch-repository-osf-dataverse-replication-project-effect-size.json
corporasearch-bibliographic-openalex-crossref-replication-database-effect-size.json
corporasearch-citation-snowball-known-replication-corpora.json
corporasearch-domain-multifield-replication-database-effect-size.json
corporasearch-code-local-original-replication-fields.json
corporasearch-repository-expanded-replication-corpus-database-package.json
corporasearch-bibliographic-expanded-replication-corpus-database.json
corporasearch-citation-expanded-known-replication-databases.json
corporasearch-domain-expanded-crossfield-replication-datasets.json
corporasearch-code-expanded-local-pair-field-signatures.json
```

The file path itself is part of the workflow. If the exact target file exists, the step is considered done and skipped by default. If we intentionally want to rerun the same step, we use `--replace` or the make target/environment equivalent. This is a core design constraint. We do not want hidden notebooks, in-memory runs, or vague "I searched for this yesterday" states. We want target-file existence to answer the question, "Has this search been run?"

The implementation currently centers on the script:

```text
scripts/search_figure1_corpora_databases.py
```

It queries free/public-ish sources and local files. The current surfaces include OSF, Dataverse, DataCite metadata, OpenAlex, Crossref, Europe PMC, ClinicalTrials.gov for registry-like searches, Wayback CDX for archive recovery, and local file scans over raw/derived corpus candidate directories. This is intentionally modest. These APIs are public and rate-limited, but usable for targeted searches. We use a small per-query cap by default. We use descriptive query batches, not a brute-force global crawl.

The Makefile now has explicit targets:

```text
make figure1-corpora-search-expanded
make figure1-corpora-search-yield
```

The first runs the expanded search set. The second summarizes marginal yield across saved search manifests. The root YAML, `PROVENANCE_PIPELINE_SINGLE_SOURCE_OF_TRUTH.yml`, defines the search tracks, target-file contract, review cue, and DAG edges. The YAML is meant to be the central human/LLM-readable source of truth. Scripts should implement what the YAML says, and when they diverge we should update the YAML or the script.

This setup is deliberately not a full automatic ingestion system. Search outputs are not immediately promoted as accepted sources. They become manifests with raw results, classified candidates, routed/rejected leads, and errors. The system then stages the next decision rather than mutating the root table blindly.

## 3. Why We Use `CORPORA_AND_DATABASES.tsv`

The root table for this layer is:

```text
CORPORA_AND_DATABASES.tsv
```

This is the first consolidated intake table. Anything that looks like a source family, corpus, database, repository package, result table, registry database, or candidate multi-row source can be represented there. It can be blocked, rejected, staged, raw-only, integrated, duplicate, or future-use. It does not need to be fully parsed before it enters the inventory, but it does need enough fields to be auditable.

This table exists because early in the project we had too many ad hoc source lists spread across code, reports, raw directories, derived tables, and memory. The table is a single place to enumerate discovered source families before doing row-level extraction. We need it because Figure 1 search is not just "find papers." It is source-family discovery. A single source family may include a paper, OSF project, component, downloadable zip, workbook, code package, and derived table. We need to track that before we try to parse pair rows.

The table contains fields like source name, record kind, inventory status, source family, domain/field, description, why relevant, plot universe IDs, Figure 1 relevance, discovery source/path, source key, URLs, local raw paths, backing files, expected rows, known rows, known pair rows, result field status, D/N availability, pair mapping availability, parser status, blockers, next action, and notes.

This table should not be treated as a list of confirmed usable corpora. It is an inventory. Some rows are real sources ready for parsing, some are raw leads, some are rejected, and some are routed to other worklists. That distinction is critical. We currently need more discipline around not interpreting "candidate_count" as "new real corpus count."

## 4. The Current Search Tracks

The Figure 1 search plan currently has several tracks.

First is local inventory refresh. This checks existing local artifacts: the plot1 replication source catalog, raw replication project directories, lead registries, derived replication pair worklists, corpus candidates, reports, and suggestion trackers. This is the highest-value track because it searches things we already have. It also turns ad hoc local state into explicit inventory rows. If a source is already mirrored locally, we should not be spending API calls rediscovering it.

Second is repository search. This searches OSF, Dataverse, and dataset metadata surfaces for phrases like direct replication, original study, replication project, registered replication report, Many Labs, Reproducibility Project, original/replication effect fields, and sample-size fields. Repository search is valuable because real pair data often live in OSF components, Dataverse packages, zipped supplements, or code repositories. The downside is that repository metadata is noisy. "Replication package" often means code for one paper, not a replication corpus. "Original" and "effect size" can appear in unrelated contexts.

Third is bibliographic search. This uses OpenAlex, Crossref, and Europe PMC to find papers that may describe or release corpora/databases. Examples include "replication database", "database of replication studies", "large-scale replication dataset", and "reproducibility project effect sizes." This is useful for discovering source families through papers, but it is also noisy because many papers discuss replication without exposing row-level data.

Fourth is citation/name snowball search. This starts from known or named source families: FReD, FORRT, SCORE, LOOPR, RPP, Many Labs, Social Science Replication Project, Experimental Economics Replication Project, Reproducibility Project: Cancer Biology, and registered replication report collections. It searches citing/cited neighborhoods and named-source strings. This is a high-recall approach for finding adjacent source families and articles, but again not every paper around a known source family is itself a data source.

Fifth is domain-specific search. This uses field-specific phrases: psychology, behavioral science, management, operations, economics, political science, clinical trials, neuroscience, education, preclinical science, language acquisition, ecology/evolution, software engineering, sports/exercise, and related domains. This helps us avoid being trapped in psychology-only replication projects. It is useful for breadth, but field-specific queries produce many isolated papers and method papers.

Sixth is code and file-name search. This searches local raw and derived files for signatures like `original_N`, `replication_N`, `original_effect`, `replication_effect`, `study_pair_id`, and similar fields. This is one of the most promising routes because file names, headers, and code often reveal real pair tables. It also requires careful filtering because local directories contain derived outputs, hidden MacOS files, unpacked intermediate files, and artifacts that may not be source-family leads. We added deterministic skips for `__MACOSX` and `._` files after they started clogging the review queue.

Seventh is registry/pilot-fullscale search. This is more speculative for Figure 1. It looks for registry/database sources that could produce pilot/full-scale or original/follow-up pairs. We have learned to be careful here. A single pilot or feasibility study is not automatically relevant. We should only route it forward when there is affirmative evidence that it is itself a replication/follow-up of an identifiable original, or when a registry/database can systematically expose many such pairs.

Eighth is archive recovery. This uses Wayback CDX and local/dead-link evidence to recover source pages or old repository URLs. This is not a broad search method. It is best for known source families with dead links or old supplementary pages.

Ninth is manual suggestion capture. This harvests named source suggestions from our notes and reports. It is a cheap way to preserve expert memory and user suggestions, but it needs the same downstream triage as any other source.

We then added expanded tracks: expanded repository, expanded bibliographic, expanded citation/name snowball, expanded cross-field/domain, and expanded local code/file signatures. These are not replacements for baseline tracks. They write separate target files so we can measure marginal yield.

## 5. What the Expanded Search Found

The current yield summary is:

```text
baseline raw results: 1267
baseline classified leads: 428
baseline candidate leads: 166
baseline routed/rejected: 262
baseline errors: 8

expanded raw results: 1572
expanded classified leads: 765
expanded candidate leads: 142
expanded candidates new to root table by deterministic keys: 67
expanded routed/rejected: 623
expanded errors: 0
```

The expanded repository search was the strongest marginal source by deterministic novelty:

```text
repository expanded: 152 raw, 34 candidates, 30 candidates new to root, 24 routed/rejected
```

Expanded code/file search was also useful, but noisy:

```text
code expanded: 384 raw, 23 candidates, 16 candidates new to root, 361 routed/rejected
```

Expanded bibliographic and citation searches generated many plausible titles but many are likely context or individual-paper sources:

```text
bibliographic expanded: 271 raw, 37 candidates, 10 new to root, 91 routed/rejected
citation expanded: 269 raw, 28 candidates, 9 new to root, 58 routed/rejected
domain expanded: 496 raw, 20 candidates, 2 new to root, 89 routed/rejected
```

The results show both value and diminishing returns. The expanded search did find new leads, especially repository/package leads and local file artifacts. But the broad bibliographic/citation/domain tracks produce lots of "replication language" that does not necessarily mean "source contains a usable original/replication pair table." The names visible in the expanded lead list include genuine-looking sources such as Reproducibility Project: Cancer Biology data files, Many Labs tables, promoted pair tables, multi-lab replication sources, and replication project packages. They also include methods papers, individual registered replication reports, reviews, comments, and articles that should probably become context or individual-paper worklist items.

This is exactly why the plan cannot stop at search. Search gives us leads. It does not make inclusion decisions.

## 6. Deterministic Classification and Its Limits

The search script does a first-pass classification. It scores raw hits using replication phrases, pair terms, data terms, provider context, and obvious irrelevant patterns. It then assigns record kinds such as:

```text
candidate_corpus_or_database
candidate_repository_package
candidate_result_table
candidate_bibliographic_paper
candidate_context_or_methods_paper
candidate_individual_paper_or_package
rejected_irrelevant_search_hit
```

This deterministic pass is essential because we cannot ask Codex or GPT to think deeply about every raw result. For the expanded search alone, there were 1,572 raw hits. Reviewing all of those intelligently is not realistic. The deterministic layer must reject low-relevance hits, route obvious individual papers, and keep only the moderate-ambiguity items for review.

However, the current classifier is still too permissive. It is good enough to create an auditable queue, not good enough to make final source decisions. We already saw specific failure modes:

- Registered replication report titles were initially advanced as corpus/database candidates because they contain strong replication language.
- Some repository hits were generic packages that matched "original" or "effect size" without actually being replication sources.
- Local file scans surfaced hidden `._` and `__MACOSX` files until we added deterministic skips.
- Broad bibliographic results include methods papers about assessing replication success, forecasting replication, or measuring reproducibility, which may be useful context but should not be treated as corpus rows unless they expose data.
- "Replication package" often means computational reproducibility package for one article, not original/replication pair data.

We tightened some of this. We added a guard that requires replication or reproducibility language for repository/bibliographic/citation/domain/registry hits. We added individual-report title patterns so obvious single registered/direct replication reports can route away. We added local skip rules for MacOS unpacking artifacts. We also changed the review cue so `discovered_search_lead` rows that look root-relevant still get Codex review rather than being skipped prematurely.

The remaining open issue is that the classifier still confuses "paper about replication" with "source that contains pair data." The deterministic layer probably needs a stronger distinction between:

```text
mentions replication
describes a replication study
describes a replication project
releases a dataset
exposes row-level pair table
names another source that might expose row-level pair table
```

Those are very different pipeline states.

## 7. Review Cue and Receipt Strategy

After deterministic classification, unresolved leads enter a review cue:

```text
steps/review_cue/figure1_search_leads/
```

The active queue currently has:

```text
open review items: 798
total input leads: 858
already in root target: 13
already reviewed: 20
deterministically skipped: 27
```

The open queue by record kind is approximately:

```text
candidate_result_table: 400
candidate_bibliographic_paper: 144
candidate_corpus_or_database: 141
candidate_individual_paper_or_package: 47
candidate_context_or_methods_paper: 42
candidate_repository_package: 24
```

This is a large queue, but it is still a manageable staged queue compared with unstructured search. The problem is no longer "what did we search?" It is "which of these leads deserve intelligence, in what order, and what machine-readable decision should be written?"

The review cue produces bounded Codex batches, usually 20 leads. This is intentional. Codex can investigate sources, but quality drops if we ask it to classify hundreds at once. GPT Pro can potentially handle larger batches, but only through user-mediated prompt files. We do not want GPT prose to become hidden pipeline input. If GPT reviews something, the output must be pasted back as JSON in the expected schema.

The review decisions are not append-only prose logs. They become receipt files under decision-specific directories:

```text
steps/review_cue/figure1_search_leads/receipts/
```

This is how we avoid spending intelligence twice. A future queue build checks for receipt target files and skips reviewed items by stable lead key, review ID, canonical source key, or duplicate marker. This is more aligned with the user's preferred target-file workflow than a pure append log. We still have decision JSON artifacts, but durable skip state is represented by per-lead receipt files.

Allowed review decisions include:

```text
keep_in_corpora_and_databases
promote_to_corpora_and_databases
route_to_result_table_worklist
route_to_individual_replication_paper_worklist
keep_as_context_source
reject_irrelevant
needs_more_evidence
```

The important discipline is that routing to the individual replication paper worklist requires affirmative evidence. We explicitly reject the earlier bad behavior where a source could be routed forward simply because a later full-scale trial or replication might exist someday. For individual-paper routing, we need evidence that the source is itself a replication/reproduction/follow-up of an identifiable original, or that metadata links original and replication, or that the source contains pair mapping.

## 8. Last-Mile Proposal and GPT Field Coding

The review cue does not directly mutate `CORPORA_AND_DATABASES.tsv`. Decisions go through:

```text
scripts/apply_review_cue_decisions.py
scripts/build_review_cue_routing_table.py
scripts/build_corpora_table_update_proposal.py
```

The proposal step writes:

```text
steps/review_cue/figure1_search_leads/apply_to_CORPORA_AND_DATABASES/corpora-table-update-proposal.tsv
steps/review_cue/figure1_search_leads/apply_to_CORPORA_AND_DATABASES/corpora-table-update-validation.tsv
steps/review_cue/figure1_search_leads/apply_to_CORPORA_AND_DATABASES/corpora-table-updated-preview.tsv
steps/review_cue/figure1_search_leads/apply_to_CORPORA_AND_DATABASES/gpt-field-coding-needed.tsv
steps/review_cue/figure1_search_leads/apply_to_CORPORA_AND_DATABASES/gpt-field-coding-prompt-*.md
```

This is another key design decision. Even after Codex decides that a lead belongs in the root table, many fields still require source-aware prose or semantic coding. For example, "source_family", "domain_or_field", "why_relevant", "result_fields_available", "has_n", "has_replication_pair_mapping", and "parser_family" may require web lookup or file inventory. We do not want Codex to fill those fields casually from search terms alone.

The GPT field-coding workflow just had a useful test case: "Reproducibility Project - Psychology: Design" at OSF node `i68pe`. GPT coded it conservatively. It said the OSF component is real and related to the broader Reproducibility Project: Psychology, but that surface metadata only exposed a PPTX presentation file for this component, not a verified data table. It therefore set result fields, D availability, N availability, pair mapping, and publication links to `unknown`, and assigned `osf_project_inventory` as the parser family. That is exactly the behavior we want. It recognizes source-family relevance without inventing extractable fields.

The saved response is:

```text
steps/review_cue/figure1_search_leads/apply_to_CORPORA_AND_DATABASES/gpt-field-coding-response-reset001.json
```

This is the model for using GPT in this pipeline: ask for bounded field coding, require JSON, require evidence basis and confidence, and require `unknown` when file-level inspection has not occurred.

## 9. Current Strengths of the Plan

The strongest part of the plan is reproducibility. Every search attempt is represented by a named target file. Every output can be regenerated or skipped. The root YAML documents the plan, scripts implement the plan, and generated reports summarize the plan. This directly addresses the earlier problem of a million ad hoc things spread across the repo.

The second strength is separation of concerns. Search is separate from triage. Triage is separate from root-table proposal. Root-table proposal is separate from source inventory. Source inventory is separate from pair/result extraction. This matters because Figure 1 discovery is inherently messy. A single source may be a paper, repository, OSF component, workbook, code file, dataset, or derived table. If we collapse those steps, we will either lose provenance or overclaim.

The third strength is cost control. Public APIs and local scans are cheap. Codex is used where bounded reasoning is helpful. GPT is only invoked when we need broader review or source-aware field coding. Manual copying is rare and structured. We are not asking a human or GPT to screen thousands of raw hits.

The fourth strength is auditability. Search manifests keep raw results, candidates, routed/rejected leads, scores, reasons, provider, query, source key, URL, and errors. Review decisions are machine-readable. Receipts become durable skip artifacts. The proposal step writes validation and preview tables rather than silently editing root data.

The fifth strength is adaptability. Because the search plan is YAML-driven and target-file based, we can add new search tracks without rewriting the whole system. We can add a new API, a new query family, a new field-specific search, or a new review cue. We can also tune heuristics and rerun only the affected target manifests.

## 10. Current Weaknesses and Failure Modes

The first weakness is semantic precision. The current classifier is still too easily impressed by replication language. It needs better distinction between actual data sources and papers about replication. This is especially important for bibliographic and citation search, where abstracts often contain strong replication terms but no usable table.

The second weakness is duplicate detection. Current novelty counts are deterministic and conservative. They catch exact title, URL, DOI, source key, and similar matches, but they do not yet fully collapse aliases across OSF components, papers, source families, and local mirrors. For example, an OSF file, a local downloaded CSV, a paper, and a source-family name may all represent the same underlying project. We need alias mapping, not just lead dedupe.

The third weakness is source-family granularity. Sometimes the right row is the broad project, not the individual OSF component. Sometimes the right row is the individual component because it contains the exact table. The RP:P Design example shows this. We need clearer rules for when a component becomes its own root row versus an artifact under a broader source-family row.

The fourth weakness is local artifact interpretation. The local code/file search is valuable but messy. It can find already-promoted derived outputs, unpacked intermediate files, hidden files, or row-level outputs that are not source-family leads. We need stronger rules for local paths: raw candidate files can be sources, derived/promoted outputs may be evidence of a source but should not automatically become new corpus rows, and generated tables should route to result-table or parser worklists rather than root source inventory unless they identify a new source family.

The fifth weakness is queue prioritization. The current open queue is large. It includes many result-table and bibliographic items. We should prioritize likely multi-row source families and repository packages before context papers. We also need a way to process obvious source-family clusters together, such as all RP:CB files, all Many Labs files, all RRR site-row files, instead of making item-by-item decisions that miss the family relationship.

The sixth weakness is lack of a fully implemented apply step. The proposal layer exists, but final root-table mutation after validation and field coding still needs an explicit apply script/flag. This is by design, but it means the pipeline currently stops at proposal unless we manually apply changes.

## 11. How We Should Judge Diminishing Returns

We should not judge search success by raw hits. Raw hits mostly measure API breadth and query noise. We also should not judge success by candidate count alone, because the classifier still admits many ambiguous sources.

Better metrics are:

```text
raw hits
classified leads
deterministically rejected/routed
candidate leads new to root by deterministic keys
candidate leads accepted by Codex/GPT review
accepted rows with completed field coding
accepted rows with file/source inventory completed
accepted rows exposing actual pair rows
pair rows promoted into source_result/canonical_result workflow
```

The expanded search gives early evidence of diminishing returns. It found 67 candidates new to the root table by deterministic keys, but many of those are probably not true corpora/databases. The real yield will be smaller. Repository and local-file searches seem more promising than broad bibliographic/domain searches. Citation/name snowball remains useful around known source families, but broad replication terms produce context articles and individual studies.

The next diminishing-returns test should be after Codex review of a batch or two. If 20 reviewed leads produce only one or two actual root-source additions, broad search is saturated and should shift to source-family inventory. If they produce many new usable source families, we should keep expanding targeted repository/name searches.

## 12. Practical Next Steps

The immediate next step is to clear the first expanded Codex review batch and write machine-readable decisions. That will tell us whether the expanded search is producing actual new sources or just plausible titles. The batch currently contains mostly candidate corpus/database items and one repository package. Codex should be conservative: keep true multi-row source families, route individual papers, keep methods/review papers as context, and reject irrelevant or generic packages.

The second step is to apply reviewed decisions as receipt files and regenerate the routing table. This will shrink the queue and prevent re-review.

The third step is to run the proposal step and generate GPT field-coding prompts only for accepted rows whose semantic fields are undercoded. GPT should not be asked to decide everything. It should be asked to fill bounded fields with evidence and `unknown` where artifact inspection is required.

The fourth step is to build source-family inventory parsers for the accepted high-value repository sources. OSF inventory is likely first: enumerate components, files, titles, file types, URLs, checksums where mirrored, and candidate parser routes. The RP:P, RP:CB, Many Labs, RRR, SCORE, FReD, and similar source families should become structured inventories before row extraction.

The fifth step is to separate individual replication paper search from corpus/database search. Individual papers matter for Figure 1, but they should flow through a different table/worklist. This prevents corpus discovery from being swamped by paper-level hits.

The sixth step is to improve clustering and aliasing. We need a way to say that multiple leads are the same source family, or that a paper points to a repository, or that a local file is an artifact under a source family. This likely belongs in source-source mapping later, but even at the root inventory layer we need alias notes and preferred corpus/database IDs.

The seventh step is to add better deterministic gates. Good candidates for additional gates include:

- Require data/package/table language for bibliographic hits before treating them as corpus/database candidates.
- Route titles beginning with "Registered Replication Report", "Registered report:", "A replication of", or "A multi-lab replication of" to individual-paper review unless the metadata also mentions dataset/database/source data.
- Penalize "method", "comment", "tutorial", "scoping review", "systematic review", "metric", "forecasting", or "sample size planning" when no dataset route is visible.
- Treat "replication package" as ambiguous, not automatically relevant.
- Prefer provider/file evidence over title evidence.
- Treat local derived/promoted outputs as pointers to known source families rather than new root leads.

## 13. What We Want GPT To Help With

We should ask GPT for critique, not for hidden decisions. The useful GPT tasks are:

- Suggest additional free/public APIs or sources we have not considered.
- Critique the search tracks and query families for missing domains or obvious blind spots.
- Suggest stronger deterministic triage rules for separating corpora/databases from papers about replication.
- Suggest a better source-family/component granularity policy.
- Suggest prioritization for the current review queue.
- Suggest a cheap way to cluster aliases across title/URL/DOI/OSF/local-file leads.
- Suggest metrics for diminishing returns that are meaningful before full parsing.
- Suggest how to split individual replication paper search from corpus/database search while preserving a shared provenance model.

We should not ask GPT to produce final root-table rows from memory. We should not ask GPT to invent file contents. We should not ask GPT to screen hundreds of leads unless it returns strict JSON decisions and we validate them. GPT's role is advisory, field coding, or bounded review. Codex's role is repo-aware implementation and smaller interactive triage. Scripts and target files remain the authority.

## Prompt To Give GPT

I am building a provenance pipeline for Figure 1 of a research project. Figure 1 needs original/replication or original/follow-up pairs with D/N or convertible effect/N information. The replication/follow-up does not need to be a published paper. The current search direction is corpus/database first: find replication databases, reproducibility projects, OSF/Dataverse/DataCite packages, multi-lab projects, source tables, and local file artifacts that may contain many original/replication pair rows. Individual replication papers are useful but should be routed to a separate worklist, not treated as corpus/database sources.

Constraints: this is a free-ish workflow. We have Codex in the repo, public APIs, local scripts, local files, public metadata sources, and occasional copy/paste handoffs to GPT. We do not have paid screening tools, paid bibliographic APIs, a large human review team, or a reliable global scraper. Every concrete search attempt must write a target file under `steps/searches/figure1/`; if that target file exists the step skips unless an explicit replace flag is used. We want a DAG-like, auditable pipeline.

Current architecture:

1. Root YAML defines Figure 1 search tracks and DAG edges.
2. `scripts/search_figure1_corpora_databases.py` runs public API/local searches and writes `corporasearch-*.json` manifests.
3. `scripts/summarize_figure1_search_yield.py` summarizes marginal yield.
4. Review cues under `steps/review_cue/figure1_search_leads/` create bounded Codex/GPT batches.
5. Codex/GPT decisions must be machine-readable JSON.
6. Applied decisions become per-lead receipt files so future queue builds skip already reviewed items.
7. A proposal step writes updates/previews for `CORPORA_AND_DATABASES.tsv`; root table mutation is not automatic.

Current search tracks include local inventory refresh, OSF/Dataverse/DataCite repository search, OpenAlex/Crossref/Europe PMC bibliographic search, citation/name snowballing around known replication source families, domain-specific search, local code/file signature search, registry/pilot-fullscale search, archive recovery, manual suggestion capture, and expanded variants of repository/bibliographic/citation/domain/code search.

Current yield:

- Baseline: 1,267 raw results, 428 classified leads, 166 candidate leads, 262 routed/rejected, 8 errors.
- Expanded: 1,572 raw results, 765 classified leads, 142 candidate leads, 67 candidates new to the root table by deterministic keys, 623 routed/rejected, 0 errors.
- Expanded repository looks best: 152 raw, 34 candidates, 30 new to root.
- Expanded local code/file search is useful but noisy: 384 raw, 23 candidates, 16 new to root, 361 routed/rejected.
- Expanded bibliographic/citation/domain search finds many replication-language hits, but many are likely individual papers, methods papers, context papers, or generic packages.

Known failure modes:

- Search terms with "replication" find papers about replication, not necessarily data sources.
- "Registered Replication Report" titles often represent individual papers, not corpora/databases.
- "Replication package" often means one paper's computational package, not original/replication pair data.
- Local file scans can find derived outputs or unpacking junk; we added deterministic skips for `__MACOSX` and `._` files.
- Source-family granularity is hard: an OSF component may be a true source artifact, or it may just be a component under a broader project.
- We need to avoid spending Codex/GPT review twice on already reviewed or already-in-target leads.

Please critique this search strategy. Specifically:

1. What additional free/public search surfaces should we add, if any?
2. What query families are missing for Figure 1 corpus/database discovery?
3. What deterministic triage rules would better separate true corpus/database/package leads from individual papers and context papers?
4. How should we handle source-family vs component-level rows, especially for OSF projects?
5. How should we prioritize the current review queue to maximize actual new pair rows per unit of Codex/GPT/manual attention?
6. What is the best cheap method for alias clustering across papers, OSF components, local files, DOIs, and source-family names?
7. What diminishing-returns metrics should we use before full row-level parsing exists?
8. What should the next two implementation steps be?

Be pragmatic. We need a plan that works with public APIs, Codex, local scripts, occasional GPT copy/paste, and target-file-based reproducibility. Do not propose expensive commercial infrastructure or broad uncontrolled scraping.
