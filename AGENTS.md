# Agent Instructions

## Replicability Standard

This repository prioritizes maximum replicability over compactness. Any agent that adds, promotes, or changes evidence rows must preserve enough information for a future worker to retrace the row from raw source bytes to final plotted values.

Minimum standard for new extraction work:

1. Mirror the source locally whenever access allows it. Store repo-relative paths under `data/raw/`, `data/cache/`, or another documented data directory. Do not rely on a browser tab, a dynamic website, or memory of a download step.
2. Record bibliographic identity separately from computational access. A paper, registry record, corpus, database, PDF, zip file, and extracted CSV can all be sources.
3. Preserve original text before parsing. Keep verbatim effect, N, p-value, CI, outcome, table row, or API field text in TSV-safe one-line fields before creating cleaned numeric values.
4. Record parsing and transformation steps explicitly. A row must explain how native text became `D`, `N`, standard errors, or native ATE fields. Include formulas or named conversions when used.
5. Keep source-result rows even when the same underlying result appears in several places. Use canonical result IDs and mapping tables to deduplicate later; do not erase alternate source assertions.
6. Use repo-relative paths and checksums for mirrored files when practical. If a file required user/manual download, login, or browser-only access, record that as an access event rather than hiding it.
7. Generated HTML tables must be projections of TSV/CSV artifacts on disk. If a rendered table has a grain not represented by an existing TSV, add the TSV first.

## Preferred Evidence Tables

Use this conceptual model for new provenance work:

- `source.tsv`: citeable or computational source objects, including papers, datasets, repositories, registries, corpora, and reports.
- `source_access.tsv`: exact access routes and local mirrors, including URLs, API endpoints, local paths, checksums, content type, access barriers, and retrieval method.
- `source_access_attempt.tsv`: append-only acquisition attempts, including DOI/publisher/OA/preprint/API routes, candidate URLs, redirects, blockers, match decisions, and next actions.
- `source_file.tsv`: content-addressed mirrored artifacts such as PDFs, XML, HTML, registry JSON, supplements, datasets, code files, screenshots, archives, and extracted members.
- `source_version.tsv`: VOR, accepted manuscript, preprint, registry, repository, dataset, code, and update/version assertions.
- `source_access_right.tsv`: license, TDM, robots, mirroring, text-extraction, redistribution, and institutional-access decisions.
- `source_result.tsv`: one row per result asserted by one extraction source, with verbatim text, parsed native values, standardized values, and transformation explanation.
- `source_result_support.tsv`: field-level support snippets and locators for effect text, N text, selector text, conversion inputs, relationship evidence, raw data, code, or recomputed outputs.
- `canonical_result.tsv`: deduplicated result chosen or summarized from one or more source-result rows.
- `canonical_result_membership.tsv`: explicit source-result children used in canonical/collapsed plotted dots.
- `plot_membership.tsv`: plot/statistics inclusion, field/source-family labels, and render-order counts.
- `source_source_mapping.tsv`: relationships such as corpus contains paper, database reports paper result, registry preregisters study, or package supports paper.
- `extraction_event.tsv`: actions used to obtain or parse bytes, including automatic download, manual user upload, PDF/table extraction, code execution, and failures.
- `manual_acquisition_task.tsv`: prioritized human follow-up for missing source objects, value text, prereg artifacts, replication evidence, or rights review.

Mapping rows need specifics, not bare booleans. For preregistration/PAP/registered-report links, record registry name, registration ID, URL, filing/amendment dates, timing, locator, and verbatim selector text. For replication/reproduction links, record the original source, replicating source, replication kind, target claim, original/replicating result IDs when known, and outcome/design/sample relation. Result rows should reference these mappings with `prereg_mapping_id`, `replication_mapping_id`, `selector_mapping_id`, and `source_mapping_ids`.

The current pilot implementation lives in:

- `scripts/write_provenance_codebook.py`
- `scripts/pilot_source_result_schema.py`
- `scripts/retrace_schema_pilot_sample.py`
- `scripts/build_codebook_pilot_sample.py`
- `scripts/validate_schema_pilot_against_codebook.py`
- `scripts/resolve_schema_pilot_real_world_sources.py`
- `scripts/push_schema_pilot_to_level5.py`
- `reports/evidence_dataset_codebook.md`
- `reports/llm_extraction_contract.md`
- `data/derived/effect_inflation_dataset/provenance_data_dictionary.tsv`
- `data/derived/effect_inflation_dataset/schema_templates/`
- `data/derived/effect_inflation_dataset/schema_pilot/`

Run `make provenance-codebook` after changing the source-result schema. Run `make schema-pilot` after changing the pilot/retrace/codebook-pilot code. Run `make validate-schema-pilot` to check the 300-row codebook-shaped pilot against the codebook. Run `make ground-schema-pilot` to resolve the 300-row pilot to DOI/PMID/PMCID/NCT/AEA/Crossref/source-bibliography handles. Run `make level5-schema-pilot` to attempt strict level-5 source-object acquisition for grounded rows. Use `SCHEMA_PILOT_N=<n>` only for quick debugging; the current benchmark is 300.

## Review Cue Workflow

Some steps intentionally produce bounded review cues for Codex, humans, or GPT
instead of immediately changing root tables. The reusable cue builder is:

- `scripts/build_review_cue.py`
- configured by `review_cues` in `PROVENANCE_PIPELINE_SINGLE_SOURCE_OF_TRUTH.yml`
- materialized under `steps/review_cue/<cue_id>/`

When explicitly asked to work on a cue or to do background review work, start by
running:

```text
make review-cue REVIEW_CUE_ID=figure1_search_leads
```

Then inspect the generated `reviewcue-index-<cue_id>.md` and take a bounded
batch, usually the Codex batch of about 20 leads. Codex may investigate source
URLs, metadata, local files, and manifests, but should not edit root target
tables directly from review alone. Write decisions as the JSON file named in the
batch prompt. Apply decisions only to per-lead receipt target files, not to root
tables:

```text
make apply-review-cue REVIEW_CUE_ID=figure1_search_leads REVIEW_CUE_DECISION_FILE=steps/review_cue/figure1_search_leads/reviewcue-decisions-figure1_search_leads-codex-batch001.json
```

Receipt files live under `steps/review_cue/<cue_id>/receipts/<decision>/`.
Future cue builds skip reviewed leads by checking those receipt files. If
uncertain, mark `needs_more_evidence` and include a compact
`user_gpt_prompt_request`; do not guess.

For Figure 1, do not advance a single pilot, trial, paper, or repository
package merely because it could theoretically have a later replication. The
`route_to_individual_replication_paper_worklist` decision requires affirmative
replication-relation evidence in `route_payload`: a self-described replication,
metadata linking original and replication, or a source table containing an
original/replication mapping. Otherwise use `reject_irrelevant`,
`keep_as_context_source`, or `needs_more_evidence`.

After applying decisions, regenerate the machine-readable routing table:

```text
make review-cue-routing-table REVIEW_CUE_ID=figure1_search_leads
```

Downstream steps should consume `reviewcue-routing-table-<cue_id>.tsv` or
`.json`, not the Markdown summary.

GPT Pro handoff prompts are generated as Markdown files in the same cue
directory, usually with larger batches around 50 leads. If the user asks what to
send to GPT, point them to the relevant `reviewcue-gpt-*-prompt.md` file. After
the user returns GPT JSON, save it as the requested `reviewcue-decisions-*.json`
artifact. A separate decision-application step should validate and apply those
decisions later.

## Coding Discipline

When adding new rows, distinguish:

- `extraction_source_id`: where the literal number/text came from.
- `represented_source_id`: the paper/study/trial/result that the number is about.
- `access_id`: the exact retrievable object used.
- `source_file_id`: the mirrored byte artifact used when support is tied to a local file.
- `source_locator`: table, page, row ID, JSON path, file member, script output, or other precise locator.
- `result_label` / `outcome_label`: descriptive labels only. Do not use these as substitutes for copied source-result text.
- `verbatim_source_row_text` / `verbatim_effect_text` / `verbatim_n_text`: direct source evidence cells or excerpts.
- generated dot-level citations such as `dot_plot_...`: internal audit records only, not bibliographic references for represented works.

For plot inclusion, treat evidence level 3 as the current minimum provenance floor: a row should at least be an external source assertion with an identified represented work. Levels 0-2 are audit/worklist material until the represented source is resolved.

Use the stricter evidence ladder consistently:

- Level 3 means an external corpus/source assertion names enough bibliographic or registry information that the target paper/study/trial can theoretically be found.
- Level 4 means that target source has been independently grounded in the wider world through DOI, PMID, PMCID, NCT, AEA, Dataverse, Crossref, another citation database, or a stable independent URL.
- Level 5 means the original source object or bytes were actually obtained or mirrored locally.
- Level 6 means the exact effect/N values were extracted from that original or authoritative source object.
- Level 7 means the value was recomputed from raw data/code.

For level 5, be strict: full article PDF/XML/HTML, PMC full text XML, full registry JSON/HTML, supplements, data/code files, and other value-bearing source objects can qualify after identity review. Metadata records, DOI resolver responses, publisher landing/abstract pages, login/paywall pages, CAPTCHA pages, and access-denied pages are acquisition artifacts only; they do not qualify as level 5 unless the plotted value is actually present on that page.

When trying to acquire source objects, record each route separately. The level-5 pilot status table uses `strategy_direct_journal_or_doi_landing_*`, `strategy_oa_candidate_url_*`, and `strategy_preprint_repository_candidate_*` columns, plus `abstract_or_detail_*` and blocker flags. Abstracts, titles, and landing-page details are allowed as proof that a target was found, but keep them as grounding/detail evidence unless they contain the plotted value or point to mirrored value-bearing bytes.

Use the current acquisition-state distinction explicitly:

- `target_acquisition_state`: unanchored, external assertion only, target identity known, target located, source object mirrorable, source object mirrored, or text/data extracted.
- `value_verification_state`: not checked, corpus assertion only, source object obtained but not parsed, text/data extracted, value-bearing source text found, or D/N verified from source.

Do not store successful files only in `source_access` or `source_access_attempt`. Every mirrored byte object that might be evidence needs a `source_file.tsv` row with checksum/path/version/rights links. Every route tried, including paywall, CAPTCHA, metadata-only, abstract-only, and rejected candidates, belongs in `source_access_attempt.tsv`.

Never overwrite the original text with a cleaned value. Add cleaned and standardized values in additional columns.
