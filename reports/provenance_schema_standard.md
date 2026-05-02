# Provenance Schema Standard

The dataset should be reproducible from raw source bytes to plotted rows. The working rule is: every plotted value should be traceable through a source-result row, an access record, and an extraction event.

The formal codebook is `reports/evidence_dataset_codebook.md`; the LLM-facing extraction contract is `reports/llm_extraction_contract.md`; the machine-readable field dictionary is `data/derived/effect_inflation_dataset/provenance_data_dictionary.tsv`; the controlled-vocabulary dictionary is `data/derived/effect_inflation_dataset/provenance_vocab_dictionary.tsv`; and empty table templates live in `data/derived/effect_inflation_dataset/schema_templates/`. Regenerate those artifacts with `make provenance-codebook`.

## Core Entities

`source.tsv` records citeable or computational objects: papers, registry records, corpora, databases, PDFs, repositories, replication packages, and reports.

`source_access.tsv` records the most direct route to the bytes: URL/API URL, repo-relative local path, content type, checksum, retrieval method, access barrier, and notes.

`source_access_attempt.tsv` records each route tried before or during acquisition: DOI/publisher landing pages, Crossref/DataCite/OpenAlex/Unpaywall/Semantic Scholar/Europe PMC/PMC/PubMed/ClinicalTrials.gov/repository routes, Paperclip/GXL literature-index searches when available, abstracts, paywalls, bot blocks, rejected candidates, and manual-review outcomes.

`source_file.tsv` is the content-addressed artifact manifest. Successful files do not “live” in `source_access`; every mirrored PDF, XML, HTML, registry JSON, supplement, dataset, code file, screenshot, archive, or extracted archive member gets its own `source_file` row with path, checksum, byte class, origin, version, and level-5 eligibility.

`source_version.tsv` records version assertions such as version of record, accepted manuscript, preprint, registry snapshot, dataset/package version, and update/correction relationships.

`source_access_right.tsv` records license, TDM, robots, storage/mirroring, text-extraction, redistribution, share-scope, and institutional-access decisions. Successful download is not the same as mirroring permission.

`source_result.tsv` is the lowest-level evidence table. One row means one extraction source directly asserts or exposes one result. Descriptive labels are not enough: `result_label` / `outcome_label` should be separated from verbatim source cells such as the copied table row, effect, standard error, p-value, and N.

`source_result_support.tsv` links exact fields/decisions in a source-result row to a source, access route, and optional `source_file` artifact. Use it for effect text, N text, selector text, conversion inputs, relationship evidence, raw data, code, and recomputed outputs.

`canonical_result.tsv` chooses or summarizes across source-result rows when the same underlying result appears in several places.

`canonical_result_membership.tsv` records which source-result children contributed to a canonical/paper-level dot, including preferred, child, duplicate, excluded, and sensitivity roles.

`plot_membership.tsv` records whether a canonical result is included in a plot/statistics set, plus field/source-family labels and render-order group counts.

`source_source_mapping.tsv` records relationships among sources: a corpus contains a paper, a database reports a paper result, a registry preregisters a trial, or a package supports a paper.

Relationship rows must carry specifics, not just flags. For preregistration this means the PAP/registry source, registry name, registration ID, URL, registration/amendment dates, timing relative to data/analysis/results, locator, and verbatim primary-outcome or hypothesis text when it is used as a selector. For replication/reproduction this means original source, replicating source, replication kind, target claim, original/replicating result IDs when known, outcome/design/sample relation, assertion locator, and verbatim relationship evidence. Result rows should reference these with `prereg_mapping_id`, `replication_mapping_id`, `selector_mapping_id`, and `source_mapping_ids`.

`extraction_event.tsv` records the hoops: download, manual user upload, unzip, PDF extraction, table extraction, OCR, script execution, or blocked access.

`manual_acquisition_task.tsv` is the human workflow queue for missing source objects, value text, preregistration artifacts, replication evidence, identity disambiguation, and rights review.

Synthetic dot-level audit citations are not bibliographic references to the represented study. If a generated citation key such as `dot_plot_...` exists, store it in `generated_result_citation_key` / `generated_result_citation_rendered`. Keep `represented_source_citation_key` blank unless it is a real citation for the represented paper, registry record, trial, report, or dataset.

## Required Source-Result Blocks

Verbatim fields should be copied as directly as possible from the source:

```text
verbatim_source_row_text
verbatim_outcome_text
verbatim_effect_text
verbatim_se_text
verbatim_n_text
verbatim_p_text
verbatim_ci_text
source_locator
```

Parsed native fields store cleaned numbers without changing the metric:

```text
native_effect_value
native_effect_metric
native_standard_error
native_ci_low
native_ci_high
native_p_value
native_n_total
native_n_treatment
native_n_control
native_cluster_n
```

Standardized fields store derived plotting values:

```text
standardized_effect_value
standardized_effect_metric
standardized_n
d
d_conversion_method
d_conversion_inputs
transformation_explanation
transformation_confidence
```

Acquisition and verification state fields keep the funnel explicit:

```text
target_acquisition_state
value_verification_state
```

`target_acquisition_state` separates target identity, target located, source object mirrored, and text/data extracted. `value_verification_state` separates corpus assertion, source object obtained but not parsed, value-bearing text found, and D/N verified from source.

## Pilot Result

The 300-row schema pilot now has two layers: diagnostic retrace files and codebook-shaped TSVs. It showed that the existing plot breadcrumbs are adequate for reproducing plotted rows, but not yet adequate for original-source-grade provenance:

- all 300 sampled plot rows could be recovered,
- all 300 local ultimate source paths existed,
- 298 rows had upstream effect/statistic text retraced,
- all 300 rows had N text retraced,
- all 300 rows have codebook-shaped `source_result` rows with verbatim source-row text, N text, conversion notes, human-check status, target-acquisition state, and value-verification state,
- the pilot now has first-class artifact/right/task tables: 55 `source_file` rows, 331 `source_version` rows, 55 `source_access_right` rows, and 263 `manual_acquisition_task` rows,
- 38 rows are currently marked `fully_coded`,
- 262 rows are marked `coded_with_schema_gaps` because the best recovered source is a derived/corpus row rather than original paper, database, or registry text.

The main human-check table is `data/derived/effect_inflation_dataset/schema_pilot/source_result_codebook_sample_300.tsv`. The diagnostic retrace table is `data/derived/effect_inflation_dataset/schema_pilot/human_check_source_result_sample_300.tsv`. Future extractor rewrites should reduce the `source_is_derived_not_original_text` count by writing source-result rows at extraction time, before paper-level or corpus-level collapse.

The real-world grounding pass is `scripts/resolve_schema_pilot_real_world_sources.py` and runs with `make ground-schema-pilot`. For the 300-row pilot it recovered a real-world extraction-source URL for all 300 rows, a primary real-world represented-source URL for 298 rows, and evidence level 4 or higher for 285 rows. Under the stricter ladder, 43 rows have the original source object obtained or mirrored, and 37 rows have the exact number extracted from original registry text. The rest remain traceable but still need original paper/API/table numeric verification.

The level-5 source-object probe is `scripts/push_schema_pilot_to_level5.py` and runs with `make level5-schema-pilot`. It attempts rows at level 4 only and writes fetch attempts, row-level status, and manual TODOs. Strict level 5 means a mirrored object that could plausibly contain the plotted value, such as full article PDF/XML/HTML, PMC full text XML, a ClinicalTrials.gov full registry record, a supplement/data/code file, or another value-bearing source object. Metadata records, DOI redirects, publisher landing/abstract pages, paywall/login pages, CAPTCHA pages, and access-denied pages are acquisition evidence but are not level-5 evidence.

The probe records each source-acquisition strategy separately. Direct DOI/publisher attempts live in `strategy_direct_journal_or_doi_landing_*`; OpenAlex/Crossref/Semantic Scholar/Europe PMC/Unpaywall candidate URLs live in `strategy_oa_candidate_url_*`; preprint, repository, author-manuscript, and institutional-archive candidates live in `strategy_preprint_repository_candidate_*`. Landing-page abstracts, metadata abstracts, registry summaries, and page titles are stored in `abstract_or_detail_*` as grounding evidence. These details are useful proof that the target was found, but they remain below level 5 unless the value-bearing source object itself was obtained or the plotted value is actually present in that page/record.

Paperclip/GXL should be coded as a hosted literature-index resolver, not as a generic web search. If used, store the exact `paperclip search` / `grep` / `sql` / `cat` command, returned paper path or result-set ID, DOI/arXiv/PMCID/OpenAlex ID, output snippet, and any mirrored file path. Paperclip metadata or abstract hits can raise confidence that a target exists, but do not promote a row above the corresponding source-object level unless the indexed full text, abstract page, or downloaded artifact actually contains the relevant target/result evidence. Because Paperclip is hosted and authenticated, record it as `acquisition_method=paperclip_hosted_index`, `access_context=authenticated_hosted_service`, and do not store credentials or server-side private result IDs as the only provenance.

For the 300-row pilot, the strict level-5 probe moved 140 of 242 level-4 rows to source-object candidates. Combined with the 43 rows already at level >=5, that projects to 183/300 rows at level >=5 after review and promotion. All 242 attempted rows now have some abstract/detail grounding text, but 102 attempted rows still have only noneligible metadata, landing, paywall, bot-block, or abstract-detail evidence; these stay below level 5 until a value-bearing source object is obtained.

The current 300-row relationship pilot also exercises preregistration and replication coding. It records 97 source-result rows with preregistration mappings, 90 rows with an actual preregistration or registry artifact URL, 7 rows with only corpus-asserted preregistration and no artifact, and 54 rows with replication mappings. Relationship rows are required to carry assertion source, locator, URL, evidence type, confidence, and copied text where possible; bare `pre_reg=true` or `replication=true` flags are not sufficient.

## Promotion Gate Summary

A row is promotable only when the applicable codebook gates pass: source identity, byte access, precise locator, verbatim evidence, native parsing, D/native transformation, focal selector, separated bibliography, deduplication, and human checkability. If a gate fails, preserve the row as staged or blocked and add an `extraction_problem` row rather than silently plotting it.

For current plots, use evidence level 3 as the minimum provenance floor unless a plot is explicitly labeled as a diagnostic/worklist view. Levels 0-2 mean we can trace a number to an internal or corpus source but cannot yet identify the represented work robustly enough for a public dot. Level 4 is independent real-world grounding of the target source, level 5 is source-object access, level 6 is exact-number extraction, and level 7 is recomputation from raw data/code.
