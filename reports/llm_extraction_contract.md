# LLM Extraction Contract

Future LLM or agent extraction work must follow this contract. The goal is full replicability with human interrogation, not just adding dots.

## Before Extracting

1. Identify the represented work: paper, study, trial, registry record, project, or corpus child.
2. Identify the extraction source: the exact file/page/table/API/database row that contains the literal number you will copy.
3. Mirror the extraction source locally when possible.
4. Create or update `source.tsv` and `source_access.tsv` rows before coding result values.
5. Check `provenance_data_dictionary.tsv` and `provenance_vocab_dictionary.tsv` when choosing columns or controlled values.

## During Source Acquisition

For every attempted source route, keep the strategy and artifact class explicit:

- Use `access_strategy` to distinguish direct DOI/publisher hits, OA candidate URLs, preprint/repository candidates, registry APIs, PubMed/PMC bridges, and metadata services such as Crossref, OpenAlex, Semantic Scholar, Europe PMC, DataCite, or Unpaywall.
- Use `source_byte_class` to distinguish value-bearing source objects from metadata records, publisher abstract pages, paywall/login pages, CAPTCHA pages, and access-denied pages.
- Put abstracts, titles, registry summaries, or landing-page descriptions in `abstract_or_detail_text` with `abstract_or_detail_source_url`.
- Set `paywall_or_login_seen`, `captcha_or_bot_block_seen`, and `preprint_or_repository_candidate` honestly.
- Do not promote metadata, abstract pages, paywall pages, or bot-block pages to level 5 unless the plotted value itself is present there.

## During Relationship Mapping

Do not code relationship facts as bare booleans. For preregistration, replication, corpus membership, registry-publication links, paper-package links, and pooled/component relationships, create `source_source_mapping.tsv` rows with:

- `relationship_type` and `relationship_subtype`,
- `mapping_assertion_source_id`, `mapping_assertion_access_id`, `mapping_assertion_locator`, and `mapping_assertion_verbatim_text`,
- stable external IDs/URLs and dates where available,
- preregistration specifics such as registry name, registration ID, document type, timing, primary outcome text, and hypothesis text,
- replication specifics such as replication kind, target claim, original/replicating result IDs, outcome match, sample relation, and design relation.

## During Extraction

For every result, fill `source_result.tsv` at the lowest practical grain:

- Copy source text into `verbatim_source_row_text`, `verbatim_outcome_text`, `verbatim_effect_text`, `verbatim_n_text`, and related verbatim fields.
- Record `source_locator` so a human can find the same text again.
- Link result rows to relationship rows with `prereg_mapping_id`, `replication_mapping_id`, `selector_mapping_id`, and `source_mapping_ids` where applicable.
- Parse native fields separately from standardized fields.
- Explain every transformation into `D`, `N`, or native-panel fields.
- Use `human_check_status=source_cells_recovered` only when the verbatim evidence fields are actually present.

## During Preregistration And Replication Coding

For preregistration:

- `prereg_confirmed_pre_data` and `prereg_confirmed_pre_analysis` require timing evidence, not just a registry URL.
- `registry_record_timing_not_audited` means a registry record exists but filing/amendment timing has not been checked.
- `prereg_asserted_by_corpus_no_artifact` means a corpus or title says preregistered but no PAP/registry artifact has been obtained.
- A preregistered row should have a relationship row with registry/PAP URL, locator, selector text, timing, and confidence.

For replication:

- Use `replication_role` to say whether the row is original, replication, computational reproduction, robustness check, or only a corpus-level assertion.
- Use `replication_kind` to distinguish direct replication, conceptual replication, computational reproduction, robustness reanalysis, extension, and pilot/full-scale pairs.
- Copy the target claim as source text when available; do not invent a generic claim from a title alone.
- Fill original/replicating result IDs when both sides exist in `source_result.tsv`; otherwise leave blank and keep the relationship row.

## Promotion Rules

- `fully_coded`: all applicable promotion gates pass.
- `staged_native_metric`: effect/SE/N are real, but D conversion is not defensible.
- `coded_with_schema_gaps`: useful but missing nonfatal provenance fields.
- `blocked_missing_d_or_n`: source exists but effect or N is unavailable.
- `blocked_access`: source cannot be retrieved without manual access, login, license, or browser-only steps.
- `duplicate_existing`: result is already represented; keep mapping but do not double-count.

## Hard No Rules

- Do not put a title or display label in a `verbatim_*` field.
- Do not use generated `dot_plot_...` citations as bibliographic citations for represented papers.
- Do not treat a corpus row as a paper unless the corpus row directly represents one paper.
- Do not convert clustered LPMs or arbitrary ATEs to d without control probability, event counts, or outcome SD.
- Do not claim a row is human-checkable unless the TSV includes the source path, locator, verbatim text, parsed values, and transformation explanation.

## Required Output For Blocked Work

If you cannot finish a row, still write:

- source/access rows with the best URL and access barrier,
- an `extraction_problem` row with `problem_code`, severity, and suggested rework,
- a to-do item with the exact URL/path and what field is missing.
