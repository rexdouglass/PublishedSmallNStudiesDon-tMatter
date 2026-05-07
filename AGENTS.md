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

## Figure 1 Current Handoff - 2026-05-06

Meta-goal: Figure 1 is an auditable original-vs-larger-replication D/N
dataset. The repository is not merely making a striking plot; it is building a
defensible empirical map of how reported effects change when early findings are
tested in larger, more rigorous follow-up studies. Every plotted point must be
retraceable from source bytes through bibliographic identity, extraction text,
transformations, inclusion decisions, and plot membership.

Current state as of 2026-05-06:

- `FIGURE1_REPLICATION_PAIRS.tsv` has 2,458 root rows.
- The current Figure 1 D/N rule includes 1,706 plotted rows.
- `data/derived/replication_pairs/harvest/promoted/individual_replication_papers__promoted_pairs.csv` has 27 promoted individual-replication rows.
- The latest GPT blocker prompt has 33 unresolved candidates: 27 `needs_more_evidence`, 3 `native_only`, and 3 `reject`/second-check items.

Rows promoted in the latest 2026-05-06 individual-replication pass. Do not redo
these unless new evidence shows an error:

- Approximate arithmetic training:
  Park and Brannon (2013) Experiment 2, DOI `10.1177/0956797613482944`,
  versus Szkudlarek, Park, and Brannon (2020) Experiment 3, DOI
  `10.1016/j.cognition.2020.104521`. Promoted as
  `D_original = 0.846`, `N_original = 30`, `D_replication = 0.19`,
  `N_replication = 89`. Original D was computed from the mirrored PMC text as
  `2.313 * sqrt(1/16 + 1/14)`. Value-bearing source paths include
  `data/raw/replication_projects/individual_auto_mining_blockers/api_candidate_0eb40892da116803/original_attempts/park_brannon_2013_pmc3797151.html`
  and the mirrored replication PMC HTML under the same candidate directory.
- Status motivation and green product choice:
  Griskevicius, Tybur, and Van den Bergh (2010) Experiment 1, DOI
  `10.1037/a0018589`, versus Lazarevic et al. (2025) collaborative registered
  replication, DOI `10.1525/collabra.143773`. Promoted as
  `D_original = 0.47`, `N_original = 168`, `D_replication = 0.03`,
  `N_replication = 3774`. The replication source reported signed internal
  meta-analytic effect `-0.03`; Figure 1 stores the nonnegative magnitude
  `0.03`. Value-bearing source paths include
  `data/raw/replication_projects/individual_auto_mining_blockers/api_candidate_a939357d526cdfa3/original_attempts/griskevicius_2010_going_green_pdf.pdf`
  and
  `data/raw/replication_projects/individual_auto_mining_blockers/api_candidate_a939357d526cdfa3/article_attempts/osf_sfmz8_preprint.txt`.

Non-negotiable Figure 1 row rules:

- Do not promote metadata-only leads.
- Do not promote from a title, abstract, DOI landing page, paywall page,
  CAPTCHA page, access-denied page, or ordinary citation unless that object
  itself contains the exact value-bearing text.
- A plotted row needs affirmative replication/follow-up relationship evidence,
  a matched original and replication outcome/contrast/timepoint, original
  N/effect, replication N/effect, conversion notes, and local source paths.
- D is plotted as a nonnegative magnitude. Preserve signed source values in
  verbatim support and notes, but promote Figure 1 D as a magnitude unless a
  future explicit policy says otherwise.
- Do not collapse multiple outcomes, multiple target studies, multiple labs, or
  pooled vs single-study estimates unless the aggregation level is explicit and
  defensible.
- Keep `needs_more_evidence`, `native_only`, `coverage_only`, and `reject`
  decisions as artifacts. Do not silently drop failed or blocked leads.

Active files for the individual-replication workstream:

- GPT blocker prompt to send:
  `reports/figure1_individual_replication_blocker_unblock_prompt_2026-05-06.md`
- Same prompt under the work step:
  `steps/individual_replication_papers/figure1/auto_mining/individual-paper-gpt-blocker-unblock-prompt-2026-05-06.md`
- Raw blocker candidate payload:
  `steps/individual_replication_papers/figure1/auto_mining/individual-paper-gpt-blocker-unblock-candidates-2026-05-06.json`
- GPT decisions receipt from the prior auto-mining batch:
  `steps/individual_replication_papers/figure1/auto_mining/individual-paper-gpt-decisions-after-auto-mining-2026-05-06.tsv`
- Current value scan:
  `steps/individual_replication_papers/figure1/individual-paper-value-scan-batch001.tsv`
- Promotion proposal/receipt:
  `steps/individual_replication_papers/figure1/individual-paper-promotion-proposal.tsv`
- Promoted individual-replication pair contract:
  `data/derived/replication_pairs/harvest/promoted/individual_replication_papers__promoted_pairs.csv`
- Row disposition summaries:
  `steps/individual_replication_papers/figure1/individual-paper-row-disposition-batch001.tsv`
  and
  `steps/individual_replication_papers/figure1/individual-paper-result-option-disposition-batch001.tsv`
- Generator for the GPT blocker prompt:
  `scripts/build_individual_replication_blocker_gpt_prompt.py`

Fresh-session restart checklist:

1. Read this `Figure 1 Current Handoff - 2026-05-06` section before touching
   rows.
2. Confirm current counts, because later sessions may have advanced the repo:

   ```text
   python - <<'PY'
   import pandas as pd
   for path in [
       'FIGURE1_REPLICATION_PAIRS.tsv',
       'data/derived/replication_pairs/harvest/promoted/individual_replication_papers__promoted_pairs.csv',
       'steps/individual_replication_papers/figure1/auto_mining/individual-paper-gpt-blocker-unblock-candidates-2026-05-06.json',
   ]:
       sep = '\t' if path.endswith('.tsv') else ','
       if path.endswith('.json'):
           import json
           data = json.load(open(path, encoding='utf-8'))
           print(path, data.get('candidate_count', len(data.get('candidates', []))))
       else:
           print(path, len(pd.read_csv(path, sep=sep)))
   PY
   ```

3. If the user wants GPT help, send the whole Markdown prompt at
   `reports/figure1_individual_replication_blocker_unblock_prompt_2026-05-06.md`.
   It is complete end-to-end and already contains the candidate JSON; do not
   paste a placeholder.
4. If the user returns GPT JSON, save it as a new dated artifact such as
   `steps/individual_replication_papers/figure1/auto_mining/individual-paper-gpt-blocker-decisions-YYYY-MM-DD.json`.
   There is not yet a fully automated applier for this blocker prompt; verify
   `ready_for_row` decisions against mirrored or newly acquired bytes before
   editing the value-scan script.
5. Before finalizing after any row changes, run the canonical commands and
   report both total `FIGURE1_REPLICATION_PAIRS.tsv` rows and current D/N
   included rows from `steps/corpus_results/figure1/result_table/figure1-replication-pairs-summary.md`.

Canonical commands for this workstream:

```text
python scripts/build_individual_replication_blocker_gpt_prompt.py
python scripts/scan_individual_replication_batch001_values.py --replace
python scripts/promote_individual_replication_value_scan.py --replace
make figure1-corpus-dn-check figure1-replication-pairs-table
make figure1-arrow-plot-current figure1-html-review-assets
make figure1-individual-replication-row-disposition-batch001
```

Decision ladder for GPT/Codex/human review:

- `ready_for_row`: source-backed values and mapping are good enough to promote
  after local verification.
- `needs_more_evidence`: relation is plausible or real, but exact source
  object, matched values, N, or conversion route is missing.
- `native_only`: relation is real and values may exist, but the metric is not
  defensibly convertible to current Figure 1 D/SMD or binary d-equivalent.
- `coverage_only`: relation is real, but public source objects or values are
  missing/inaccessible.
- `reject`: no valid matched row under current policy.

Known failure modes to guard against:

- A title says replication, but the original target is ambiguous.
- Original and replication use different contrasts or outcomes.
- Replication N is larger overall but smaller for the focal matched contrast.
- A power-analysis or planning D is mistaken for the original source result.
- DOI/landing pages are treated as full text.
- Pooled or meta-analytic replication effects are used without clear mapping to
  the original target and aggregation level.
- Signed negative effects are passed into D/N checks instead of nonnegative
  magnitudes, causing valid magnitude rows to be dropped.

Next workflow after GPT returns blocker JSON:

1. Save the returned JSON as a dated receipt artifact under
   `steps/individual_replication_papers/figure1/auto_mining/`.
2. Verify only `ready_for_row` candidates against local or newly mirrored
   value-bearing bytes.
3. Mirror any newly found source objects under `data/raw/` or the documented
   workstep raw directory, with checksums when practical.
4. Patch `scripts/scan_individual_replication_batch001_values.py` with
   source-backed row entries or explicit held/rejected/native decisions.
5. Run the canonical commands above to regenerate the promoted contract,
   Figure 1 root table, D/N checks, row dispositions, and plot assets.
6. Report the exact row-count delta and which candidates moved, held, or were
   rejected.

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
