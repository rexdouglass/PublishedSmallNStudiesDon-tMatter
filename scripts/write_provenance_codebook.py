#!/usr/bin/env python3
"""Write the source-result provenance codebook, data dictionary, and TSV templates."""

from __future__ import annotations

import csv
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
DERIVED = ROOT / "data" / "derived" / "effect_inflation_dataset"
TEMPLATE_DIR = DERIVED / "schema_templates"
REPORTS = ROOT / "reports"

CODEBOOK_TSV = DERIVED / "provenance_codebook.tsv"
DATA_DICTIONARY_TSV = DERIVED / "provenance_data_dictionary.tsv"
VOCAB_DICTIONARY_TSV = DERIVED / "provenance_vocab_dictionary.tsv"
CODEBOOK_MD = REPORTS / "evidence_dataset_codebook.md"
LLM_CONTRACT_MD = REPORTS / "llm_extraction_contract.md"
ROOT_SCHEMA_YML = ROOT / "PROVENANCE_DATABASE_TABLES_AND_SCHEMAS.yml"
ROOT_SCHEMA_MD = ROOT / "PROVENANCE_DATABASE_TABLES_AND_SCHEMAS.md"
ROOT_TABLES_TSV = ROOT / "PROVENANCE_DATABASE_TABLES.tsv"
ROOT_FIELDS_TSV = ROOT / "PROVENANCE_DATABASE_FIELDS.tsv"


TABLES = [
    {
        "table_name": "source.tsv",
        "grain": "One citeable or computational source object.",
        "primary_key": "source_id",
        "required_for_promotion": "Required for every promoted source-result row.",
        "description": "Papers, registry records, corpora, databases, repositories, PDFs, reports, raw files, and derived source tables.",
    },
    {
        "table_name": "source_access.tsv",
        "grain": "One route to the bytes for one source.",
        "primary_key": "access_id",
        "required_for_promotion": "Required unless the source is intentionally bibliographic-only and not used for extraction.",
        "description": "Direct URL/API/local path/checksum/access status records.",
    },
    {
        "table_name": "source_access_attempt.tsv",
        "grain": "One resolver/download/API attempt for one source.",
        "primary_key": "attempt_id",
        "required_for_promotion": "Recommended for all newly resolved sources; required when a source required multiple routes, paywall/CAPTCHA handling, or OA/preprint discovery.",
        "description": "Append-only acquisition attempts for DOI landing pages, OpenAlex/Unpaywall/Semantic Scholar candidates, PubMed/PMC bridges, registry APIs, repository files, paywalls, abstracts, and failures.",
    },
    {
        "table_name": "source_file.tsv",
        "grain": "One mirrored byte artifact or extracted file/member for one source.",
        "primary_key": "source_file_id",
        "required_for_promotion": "Required when bytes are mirrored or used as source evidence.",
        "description": "Content-addressed inventory of PDFs, XML, HTML, registry JSON, supplements, datasets, code, screenshots, archive files, and extracted archive members.",
    },
    {
        "table_name": "source_version.tsv",
        "grain": "One version assertion for one source.",
        "primary_key": "source_version_id",
        "required_for_promotion": "Recommended whenever a source may have VOR, preprint, registry, repository, dataset, or code versions.",
        "description": "Version labels and relationships for VORs, accepted manuscripts, preprints, registry records, dataset/code versions, and updates.",
    },
    {
        "table_name": "source_access_right.tsv",
        "grain": "One access-rights or mirroring decision for one source/file.",
        "primary_key": "access_right_id",
        "required_for_promotion": "Required for mirrored source files and publisher/repository/manual access routes.",
        "description": "License, terms, TDM, robots, storage, text-extraction, redistribution, institutional-access, and review decisions.",
    },
    {
        "table_name": "source_identifier.tsv",
        "grain": "One external identifier, resolver key, or stable URL for one source.",
        "primary_key": "source_id + identifier_type + identifier_value",
        "required_for_promotion": "Recommended for every source with more than one identifier or URL; required when identifiers were resolved separately from source.tsv.",
        "description": "DOI, PMID, PMCID, NCT, AEA, EGAP, RIDIE, OSF, Dataverse, Zenodo, OpenAlex, Semantic Scholar, repository, and URL identifiers.",
    },
    {
        "table_name": "source_classification.tsv",
        "grain": "One classification assertion for one source.",
        "primary_key": "source_id + classification_source",
        "required_for_promotion": "Recommended for plot filtering, source-family displays, field counts, and paper/data-paper tables.",
        "description": "Field, subfield, source family, study design, publication type, and venue classification with provenance.",
    },
    {
        "table_name": "search_lead.tsv",
        "grain": "One discovered lead under one search track or plot universe.",
        "primary_key": "search_lead_id",
        "required_for_promotion": "Recommended before a new corpus, database, project, registry record, paper, or replication-paper lead is promoted to source/source_result rows.",
        "description": "Top-of-pipeline candidates found during universe search, including corpus/database leads and individual replication-paper leads.",
    },
    {
        "table_name": "source_result.tsv",
        "grain": "One result asserted or exposed by one extraction source.",
        "primary_key": "source_result_id",
        "required_for_promotion": "Required for every plotted or staged result.",
        "description": "The lowest-level evidence row: verbatim source text, parsed native values, standardized D/N, and transformation notes.",
    },
    {
        "table_name": "canonical_result.tsv",
        "grain": "One deduplicated result selected or summarized from one or more source-result rows.",
        "primary_key": "canonical_result_id",
        "required_for_promotion": "Required for plotting and paper-level summaries.",
        "description": "Preferred result rows and paper/project-level collapses such as median, min, and max.",
    },
    {
        "table_name": "canonical_result_membership.tsv",
        "grain": "One source-result row's membership in one canonical plotted/staged result.",
        "primary_key": "canonical_result_id + source_result_id",
        "required_for_promotion": "Required whenever canonical_result.source_result_count is greater than one; recommended for all canonical results.",
        "description": "Explicit child rows used in median/min/max/preferred-source collapse decisions.",
    },
    {
        "table_name": "source_result_support.tsv",
        "grain": "One source/access object supporting one source-result field or decision.",
        "primary_key": "source_result_id + source_id + access_id + support_role",
        "required_for_promotion": "Recommended for all rows; required when multiple objects support one result, such as paper plus supplement plus registry plus code output.",
        "description": "Links result rows to source objects for effect text, N text, selector text, conversion inputs, raw data, code, and recomputed outputs.",
    },
    {
        "table_name": "plot_universe.tsv",
        "grain": "One reusable plot, panel, statistic set, diagnostic view, or future plot context.",
        "primary_key": "plot_universe_id",
        "required_for_promotion": "Recommended when a plot build snapshots YAML-defined criteria into table artifacts.",
        "description": "Context definitions for Figure 1, Figure 2, Figure 3, diagnostics, sensitivity views, and future plots.",
    },
    {
        "table_name": "plot_criterion.tsv",
        "grain": "One reusable inclusion, exclusion, or context criterion.",
        "primary_key": "criterion_id",
        "required_for_promotion": "Recommended when a plot build snapshots YAML-defined criteria into table artifacts.",
        "description": "Reusable criteria such as ever-published, explicit original/replication pair, D/N availability, prereg selector, and non-retraction checks.",
    },
    {
        "table_name": "plot_membership.tsv",
        "grain": "One canonical result's inclusion/exclusion status in one plot or statistic set.",
        "primary_key": "plot_id + canonical_result_id",
        "required_for_promotion": "Required for public plots once a canonical result can appear in more than one plot, diagnostic view, or sensitivity view.",
        "description": "Plot inclusion, statistics inclusion, field/source-family display labels, render-order groups, and exclusion reasons.",
    },
    {
        "table_name": "source_source_mapping.tsv",
        "grain": "One directed relationship between two sources.",
        "primary_key": "mapping_id",
        "required_for_promotion": "Required whenever extraction source and represented source differ, or for corpus-parent mappings.",
        "description": "Relationships such as corpus contains paper, database reports paper result, registry preregisters study.",
    },
    {
        "table_name": "extraction_event.tsv",
        "grain": "One action or failed action used to obtain, parse, or verify source bytes.",
        "primary_key": "event_id",
        "required_for_promotion": "Required for new extraction work; pilot retrace rows may have partial historical events.",
        "description": "Downloads, user uploads, unzip steps, API calls, table extraction, code execution, manual PDF checks, blocked access.",
    },
    {
        "table_name": "extraction_problem.tsv",
        "grain": "One quality or provenance problem for one source-result or source object.",
        "primary_key": "problem_id",
        "required_for_promotion": "Required when any promotion gate is not met or requires manual follow-up.",
        "description": "Machine-actionable error and rework queue.",
    },
    {
        "table_name": "manual_acquisition_task.tsv",
        "grain": "One human/manual acquisition or verification task.",
        "primary_key": "manual_task_id",
        "required_for_promotion": "Required when automated acquisition fails or manual/library access is needed.",
        "description": "Prioritized human workflow for missing source objects, PDFs, supplements, prereg artifacts, result text, and license/access review.",
    },
]


CONTROLLED_VOCABS = {
    "source_type": [
        "paper",
        "registry_record",
        "corpus",
        "database",
        "repository_or_package",
        "pdf",
        "report",
        "website",
        "raw_data_file",
        "code_file",
        "local_derived_table",
        "other",
    ],
    "source_status": ["primary", "sidecar", "support_only", "blocked", "deprecated"],
    "search_lead_type": [
        "corpus_or_database",
        "registry_record",
        "paper_or_article",
        "individual_replication_paper",
        "replication_project",
        "preregistration_or_pap",
        "repository_package",
        "candidate_result_table",
        "raw_data_or_code_package",
        "manual_source_suggestion",
    ],
    "search_lead_status": [
        "not_started",
        "seeded_from_existing_artifact",
        "candidate_found",
        "candidate_rejected",
        "staged_for_parser",
        "promoted_to_result_target",
        "blocked_access",
        "blocked_no_result_fields",
        "blocked_scope_mismatch",
        "deprecated_duplicate",
    ],
    "lead_decision": [
        "not_triaged",
        "promote_to_source",
        "promote_to_source_result",
        "stage_for_parser",
        "catalog_only",
        "reject_scope_mismatch",
        "reject_duplicate",
        "blocked_access",
        "blocked_missing_fields",
        "manual_review_required",
    ],
    "plot_scope_role": [
        "current_figure",
        "current_diagnostic",
        "catalog_only_future_plot_seed",
        "future_plot_candidate",
        "sensitivity_view",
        "deprecated",
    ],
    "eligibility_status": [
        "included",
        "excluded",
        "catalog_only",
        "diagnostic_only",
        "sensitivity_only",
        "pending",
        "blocked",
    ],
    "decision_context_type": [
        "current_plot",
        "diagnostic_view",
        "sensitivity_view",
        "future_plot_draft",
        "manual_review",
        "automated_rule",
    ],
    "identifier_type": [
        "doi",
        "pmid",
        "pmcid",
        "nct",
        "aea_trial",
        "egap_registration",
        "ridie",
        "osf",
        "dataverse_doi",
        "zenodo_doi",
        "openicpsr",
        "openalex",
        "semantic_scholar",
        "arxiv",
        "ssrn",
        "url",
        "other",
    ],
    "access_role": [
        "landing_page",
        "direct_download",
        "api",
        "mirrored_file",
        "file_member",
        "source_file_or_catalog",
        "user_upload",
        "derived_table",
    ],
    "retrieval_method": [
        "automated_download",
        "api_download",
        "osf_clone",
        "dataverse_api",
        "github_clone",
        "user_upload",
        "browser_manual_download",
        "existing_local_file",
        "code_execution_output",
        "not_retrieved",
    ],
    "access_status": [
        "local_file_found",
        "downloaded",
        "remote_url_not_cached",
        "local_path_missing",
        "login_required",
        "access_denied",
        "missing_locator",
        "unresolved_locator",
        "blocked",
        "not_applicable",
    ],
    "attempt_decision": [
        "source_object_mirrored",
        "metadata_only",
        "abstract_or_landing_only",
        "paywall_or_login",
        "captcha_or_bot_block",
        "access_denied",
        "blocked",
        "not_retrieved",
        "manual_review",
        "candidate_rejected",
    ],
    "access_strategy": [
        "registry_clinicaltrials",
        "pubmed_bridge",
        "pmc_fulltext",
        "crossref_metadata",
        "datacite_metadata",
        "unpaywall_metadata",
        "openalex_metadata",
        "semantic_scholar_metadata",
        "europepmc_metadata",
        "oa_candidate_url",
        "preprint_repository_candidate",
        "direct_journal_or_doi_landing",
        "stable_url",
        "other",
    ],
    "source_byte_class": [
        "full_article_pdf",
        "full_article_xml",
        "full_article_html",
        "author_manuscript_fulltext",
        "supplement_file",
        "dataset_file",
        "code_file",
        "registry_record_full",
        "pmc_fulltext_xml",
        "pubmed_record_or_abstract",
        "metadata_record",
        "publisher_landing_or_abstract",
        "paywall_or_login_page",
        "captcha_page",
        "access_denied_page",
        "blocked_no_source_object",
        "source_object_unclassified",
        "not_retrieved",
    ],
    "license_category": ["open", "restricted", "subscription", "unknown", "not_applicable"],
    "source_version": [
        "version_of_record",
        "accepted_manuscript",
        "author_manuscript",
        "preprint",
        "supplement",
        "registry_record",
        "dataset",
        "code",
        "metadata",
        "unknown",
    ],
    "file_role": [
        "full_article",
        "author_manuscript",
        "preprint",
        "registry_record",
        "supplement",
        "dataset",
        "code",
        "metadata",
        "screenshot",
        "abstract_page",
        "landing_page",
        "derived_table",
        "archive",
        "archive_member",
        "other",
    ],
    "file_origin": [
        "automated_download",
        "api_response",
        "repository_file",
        "publisher_file",
        "existing_local_file",
        "user_upload",
        "manual_browser",
        "code_execution_output",
        "internal_derived",
        "archive_member",
        "unknown",
    ],
    "rights_decision": [
        "open_allowed",
        "internal_only",
        "restricted",
        "subscription_required",
        "not_applicable",
        "unknown",
        "needs_review",
    ],
    "target_acquisition_state": [
        "unanchored",
        "external_assertion_only",
        "target_identity_known",
        "target_located",
        "source_object_mirrorable",
        "source_object_mirrored",
        "text_or_data_extracted",
    ],
    "value_verification_state": [
        "not_checked",
        "corpus_assertion_only",
        "source_object_obtained_not_parsed",
        "text_or_data_extracted",
        "value_bearing_source_text_found",
        "d_n_verified_from_source",
    ],
    "manual_task_status": ["open", "in_progress", "blocked", "closed", "not_needed"],
    "needed_artifact_type": [
        "original_source_object",
        "full_article",
        "registry_record",
        "supplement",
        "dataset_or_code",
        "prereg_artifact",
        "replication_evidence",
        "effect_text",
        "n_text",
        "license_review",
        "identity_disambiguation",
        "other",
    ],
    "relationship_type": [
        "extraction_source_reports_result_for_represented_source",
        "corpus_contains_paper",
        "database_reports_paper_result",
        "repository_supports_paper",
        "registry_preregisters_study",
        "registry_links_publication",
        "pre_analysis_plan_supports_study",
        "registered_report_protocol_for_paper",
        "publication_reports_registered_study",
        "replication_of",
        "computational_reproduction_of",
        "robustness_reanalysis_of",
        "meta_analysis_includes_study",
        "corpus_asserts_result_for_paper",
        "corpus_asserts_preregistration_for_paper",
        "paper_uses_dataset",
        "source_derives_from_source",
        "duplicate_of",
        "parent_collection_contains_child",
    ],
    "relationship_subtype": [
        "preregistration",
        "pre_analysis_plan",
        "meta_analysis_pre_analysis_plan",
        "registered_report_stage1_protocol",
        "registered_report_stage2_results",
        "trial_registry_record",
        "data_or_code_package",
        "paper_supplement",
        "direct_replication",
        "conceptual_replication",
        "computational_reproduction",
        "robustness_reanalysis",
        "extension_study",
        "pilot_full_scale_pair",
        "pooled_round_component",
        "corpus_child_paper",
        "database_child_result",
        "citation_or_link_only",
        "unknown",
    ],
    "relationship_timing": [
        "pre_data_collection",
        "pre_analysis",
        "post_data_pre_results",
        "post_results",
        "not_applicable",
        "unknown",
    ],
    "mapping_evidence_type": [
        "verbatim_text",
        "metadata_field",
        "doi_link",
        "registry_link",
        "citation_match",
        "title_author_year_match",
        "code_or_package_manifest",
        "manual_judgment",
        "unknown",
    ],
    "replication_role": [
        "none",
        "original_study",
        "replication_study",
        "computational_reproduction",
        "robustness_check",
        "corpus_replication_assertion",
        "unknown",
    ],
    "support_role": [
        "effect_text",
        "n_text",
        "outcome_text",
        "selector_text",
        "conversion_input",
        "raw_data",
        "analytic_data",
        "code",
        "recomputed_output",
        "bibliographic_identity",
        "access_grounding",
        "relationship_evidence",
        "other",
    ],
    "membership_role": ["preferred", "child", "excluded_child", "duplicate", "sensitivity_only"],
    "classification_type": [
        "field",
        "subfield",
        "source_family",
        "study_design",
        "publication_type",
        "journal_or_venue",
        "other",
    ],
    "native_effect_metric": [
        "mean_difference",
        "standardized_mean_difference",
        "odds_ratio",
        "log_odds_ratio",
        "risk_difference",
        "correlation",
        "regression_coefficient",
        "t_statistic",
        "z_statistic",
        "f_statistic",
        "p_value_only",
        "hazard_ratio",
        "rate_ratio",
        "count_difference",
        "native_ate",
        "elasticity",
        "unknown",
    ],
    "standardized_effect_metric": [
        "d",
        "hedges_g",
        "smd",
        "chinn_log_or_to_d",
        "r_to_d",
        "fisher_z_to_d",
        "t_to_d",
        "z_to_d",
        "d_proxy",
        "native_only",
        "not_promoted",
    ],
    "d_conversion_method": [
        "reported_d",
        "reported_g",
        "reported_smd",
        "chinn_log_or_to_d",
        "event_counts_to_log_or_to_d",
        "r_to_d",
        "fisher_z_to_r_to_d",
        "standardized_outcome_coefficient",
        "source_provided_d_proxy",
        "paper_median_of_child_d",
        "no_d_native_metric",
        "blocked_missing_inputs",
    ],
    "prereg_status": [
        "prereg_confirmed_pre_data",
        "prereg_confirmed_pre_analysis",
        "registered_report",
        "proposal_pre_fielding_not_full_prereg",
        "registry_metadata_only",
        "registry_record_timing_not_audited",
        "prereg_asserted_by_corpus_no_artifact",
        "not_preregistered",
        "unknown",
    ],
    "selector_status": [
        "pap_primary",
        "pap_secondary",
        "registry_primary",
        "article_primary",
        "first_confirmatory_hypothesis",
        "median_across_preregistered_primaries",
        "corpus_focal_claim",
        "database_primary_outcome",
        "not_focal",
        "no_focal_selector",
    ],
    "confidence": ["high", "medium", "low", "blocked"],
    "human_check_status": [
        "source_cells_recovered",
        "n_only_recovered",
        "plot_summary_only",
        "needs_pdf_check",
        "needs_code_execution",
        "verified_by_human",
    ],
    "coding_status": [
        "fully_coded",
        "coded_with_schema_gaps",
        "staged_native_metric",
        "blocked_missing_d_or_n",
        "blocked_access",
        "excluded",
        "duplicate_existing",
    ],
    "evidence_level_name": [
        "unanchored_number",
        "internal_trace_only",
        "external_source_assertion",
        "external_assertion_with_target_source",
        "target_source_independently_grounded",
        "original_source_obtained",
        "original_number_extracted",
        "recomputed_from_raw",
    ],
    "citation_status": ["real_citation", "generated_internal", "missing"],
    "problem_code": [
        "missing_verbatim_effect_text",
        "missing_verbatim_n_text",
        "missing_source_locator",
        "source_is_derived_not_original_text",
        "access_blocked",
        "needs_pdf_check",
        "needs_code_execution",
        "conversion_not_defensible",
        "duplicate_needs_resolution",
        "missing_bibliographic_key",
    ],
    "severity": ["high", "medium", "low"],
    "resolution_status": [
        "single_source_result",
        "preferred_source_selected",
        "multiple_source_results_need_resolution",
        "duplicate_existing",
        "blocked",
    ],
}


VOCAB_VALUE_DEFINITIONS = {
    "source_type": {
        "paper": ("A journal article, working paper, preprint, book chapter, or report-like scholarly paper.", "Use for the citeable work itself, not for a downloaded PDF file when the file is merely an access route."),
        "registry_record": ("A trial, preregistration, PAP, protocol, or registration record.", "Use for ClinicalTrials.gov, AEA, EGAP, RIDIE, OSF registration, and similar records."),
        "corpus": ("A curated collection that indexes or codes many papers/results.", "Use for SCORE, FReD, RPP, Metabus, or meta-research corpora."),
        "database": ("A structured source with rows of results or metadata.", "Use when the source is a database/table rather than a scholarly corpus paper."),
        "repository_or_package": ("A repository, Dataverse, OSF, Zenodo, OpenICPSR, GitHub, zip, or replication package.", "Use for source packages that contain files supporting papers/results."),
        "pdf": ("A standalone PDF file used as a source object.", "Prefer paper/report when the PDF represents a citeable work; use pdf for file-level sources."),
        "report": ("A policy, technical, institutional, or project report.", "Use when the source is not a journal/working paper but is still a citeable report."),
        "website": ("A web page used as an extraction or relationship source.", "Use only when the page itself is the source object."),
        "raw_data_file": ("A raw or analytic data file.", "Use for CSV, TSV, DTA, RDS, SAV, XLSX, or similar data objects."),
        "code_file": ("A code or script file.", "Use for R, Stata, Python, shell, notebook, or script output sources."),
        "local_derived_table": ("A table produced inside this repository.", "Use for internal audit/staging tables; this alone is not original-source evidence."),
        "other": ("A source object that does not fit another category.", "Use sparingly and explain in source.notes."),
    },
    "identifier_type": {
        "doi": ("Digital Object Identifier for an article, report, dataset, package, or other DOI object.", "Normalize without https://doi.org/ in identifier_value; put full resolver URL in identifier_url."),
        "pmid": ("PubMed identifier.", "Use numeric PMID only."),
        "pmcid": ("PubMed Central identifier.", "Use PMC-prefixed identifier when available."),
        "nct": ("ClinicalTrials.gov NCT identifier.", "Use NCT######## format."),
        "aea_trial": ("AEA RCT Registry trial identifier.", "Use trials/#### or AEARCTR form if available."),
        "egap_registration": ("EGAP registration or PAP identifier.", "Use the most stable EGAP/OSF registration identifier available."),
        "ridie": ("RIDIE registration identifier.", "Use the source-native RIDIE ID."),
        "osf": ("OSF project, registration, preprint, or file identifier.", "Use the OSF GUID or stable URL."),
        "dataverse_doi": ("Dataverse dataset or file DOI.", "Use for Dataverse persistent IDs."),
        "zenodo_doi": ("Zenodo DOI or record DOI.", "Use DOI value; record URL can go in identifier_url."),
        "openicpsr": ("OpenICPSR project or version identifier.", "Use project/version ID or stable URL."),
        "openalex": ("OpenAlex work/source identifier.", "Use OpenAlex ID or URL."),
        "semantic_scholar": ("Semantic Scholar paper identifier.", "Use S2 paper ID or URL."),
        "arxiv": ("arXiv identifier.", "Use arXiv ID without URL wrapper when possible."),
        "ssrn": ("SSRN identifier.", "Use SSRN abstract/paper ID."),
        "url": ("Stable URL that is not better represented by a narrower identifier type.", "Prefer DOI/registry/repository identifiers when available."),
        "other": ("Other external identifier.", "Explain identifier system in notes."),
    },
    "access_strategy": {
        "registry_clinicaltrials": ("ClinicalTrials.gov API or registry route.", "Use for NCT JSON/XML/HTML records and related registry result pulls."),
        "pubmed_bridge": ("PubMed metadata or ID-bridging route.", "Use when PMID metadata is used to discover DOI/PMCID/full text; this is not full text by itself."),
        "pmc_fulltext": ("PubMed Central full-text route.", "Use for PMC OA XML, BioC, OAI, PDF, or OA package retrieval."),
        "crossref_metadata": ("Crossref metadata route.", "Use for DOI metadata, license, references, and TDM/full-text candidate links."),
        "datacite_metadata": ("DataCite metadata route.", "Use for dataset/repository DOI metadata and file discovery."),
        "unpaywall_metadata": ("Unpaywall OA discovery route.", "Use for OA location/PDF/manuscript candidate discovery."),
        "openalex_metadata": ("OpenAlex metadata/OA discovery route.", "Use for DOI/PMID/PMCID resolution and OA location discovery."),
        "semantic_scholar_metadata": ("Semantic Scholar metadata/OA discovery route.", "Use for external IDs, openAccessPdf, and candidate URLs."),
        "europepmc_metadata": ("Europe PMC metadata/OA discovery route.", "Use for life-science metadata, PMCID bridging, and full-text candidate URLs."),
        "oa_candidate_url": ("A candidate open-access URL discovered by a resolver.", "Use for the candidate route; classify the bytes separately with source_byte_class."),
        "preprint_repository_candidate": ("A preprint, author manuscript, institutional repository, or repository copy candidate.", "Use when the candidate may be a lawful non-VOR source object."),
        "direct_journal_or_doi_landing": ("Direct request to DOI redirect or publisher landing page.", "Use for final-host page attempts, including paywall/abstract/CAPTCHA outcomes."),
        "stable_url": ("A stable URL route not covered by a specialized resolver.", "Use for official project pages, direct dataset URLs, or stable archive URLs."),
        "other": ("An access route not covered by the controlled list.", "Explain the route in access_notes."),
    },
    "source_byte_class": {
        "full_article_pdf": ("Full article PDF bytes for the target work.", "Level 5 eligible if identity matches and access/mirroring is lawful."),
        "full_article_xml": ("Full article XML/JATS/NLM-style bytes for the target work.", "Level 5 eligible if identity matches and the value could plausibly appear there."),
        "full_article_html": ("Full article HTML bytes, not just a landing page or abstract.", "Level 5 eligible only when actual full text is present."),
        "author_manuscript_fulltext": ("Author accepted manuscript, preprint, or repository manuscript full text.", "Level 5 eligible but flag source_version as manuscript/preprint when available."),
        "supplement_file": ("Supplementary material used to support extraction.", "Level 5 eligible if it could contain the value, table, appendix, or methods."),
        "dataset_file": ("Data or analytic table file.", "Level 5 eligible if it can support the value or recomputation."),
        "code_file": ("Script, notebook, log, or code output.", "Level 5 eligible if it generates or contains the value."),
        "registry_record_full": ("Full registry/API record.", "Level 5 eligible when the registry record is the source for the value or selector."),
        "pmc_fulltext_xml": ("PMC full-text XML/BioC/OAI record.", "Level 5 eligible under PMC OA/usage constraints."),
        "pubmed_record_or_abstract": ("PubMed citation/abstract metadata.", "Usually level 4/metadata only; level 5 only if the plotted value is actually in the abstract/record."),
        "metadata_record": ("Metadata-only API response.", "Use for grounding and resolver provenance; not level 5 for D/N values."),
        "publisher_landing_or_abstract": ("Publisher landing page, title page, or abstract page.", "Not level 5 unless the exact plotted value appears on that page."),
        "paywall_or_login_page": ("Paywall, subscription, sign-in, or institutional-access page.", "Never promote as value-bearing evidence; keep as access evidence."),
        "captcha_page": ("CAPTCHA, bot-check, or anti-automation page.", "Never promote; stop automated retries for the route."),
        "access_denied_page": ("403/access-denied page or equivalent.", "Never promote; record blocker."),
        "blocked_no_source_object": ("No usable object was obtained.", "Use with extraction_problem/manual to-do."),
        "source_object_unclassified": ("Bytes were obtained but not classified.", "Manual review required before promotion."),
        "not_retrieved": ("No bytes were retrieved for this access row.", "Use when the row documents a locator or attempted route only."),
    },
    "license_category": {
        "open": ("Open or public license/access appears to allow local mirroring for this use.", "Still preserve license_url and policy notes when available."),
        "restricted": ("Access is public or obtained, but reuse/storage terms are restricted or unclear.", "Use when manual/legal review may be needed."),
        "subscription": ("Access appears to require subscription/institutional entitlement.", "Do not treat as open mirroring."),
        "unknown": ("License or storage policy has not been determined.", "Default when no policy was captured."),
        "not_applicable": ("License category is not applicable to this access row.", "Use for failed/nonretrieved routes or purely internal derived files."),
    },
    "attempt_decision": {
        "source_object_mirrored": ("A value-bearing source object was mirrored or already exists locally.", "Can support level 5 after identity and policy checks."),
        "metadata_only": ("Only metadata was obtained.", "Supports grounding/resolution, not original-number verification unless metadata contains the value."),
        "abstract_or_landing_only": ("Only an abstract or publisher/detail landing page was obtained.", "Use as proof of location; promote only if the value appears there."),
        "paywall_or_login": ("The route reached a paywall, subscription, or login artifact.", "Keep as blocker evidence and do not promote as value-bearing bytes."),
        "captcha_or_bot_block": ("The route reached a CAPTCHA or bot-check artifact.", "Stop automated retries for this route/host."),
        "access_denied": ("The route returned access denied, 403, or equivalent.", "Record as blocked unless another lawful route succeeds."),
        "blocked": ("The attempt was blocked by policy, robots, missing permissions, missing key, or similar.", "Needs manual review or different route."),
        "not_retrieved": ("No network/file retrieval was attempted or completed.", "Use for locator-only rows."),
        "manual_review": ("Attempt outcome needs human judgment.", "Use for ambiguous candidates or multiple possible targets."),
        "candidate_rejected": ("Candidate route was checked and rejected.", "Explain mismatch or rejection in decision_reason."),
    },
    "source_version": {
        "version_of_record": ("Publisher version of record.", "Use for final published article/full text."),
        "accepted_manuscript": ("Accepted manuscript after peer review but before publisher formatting.", "Flag as not VOR."),
        "author_manuscript": ("Author manuscript or institutional repository copy.", "Flag as not VOR."),
        "preprint": ("Preprint or working-paper version.", "Flag as pre-publication/non-VOR."),
        "supplement": ("Supplementary material associated with another source.", "Use for appendices and supporting files."),
        "registry_record": ("Registry/API record version.", "Use for NCT/AEA/EGAP/RIDIE/OSF registry records."),
        "dataset": ("Dataset or data table version.", "Use for source data files."),
        "code": ("Code/script/output version.", "Use for computational source objects."),
        "metadata": ("Metadata-only record.", "Not value-bearing unless the value appears in metadata."),
        "unknown": ("Source version has not been determined.", "Use until a narrower version can be coded."),
    },
    "file_role": {
        "full_article": ("Full article object.", "Use for VOR/AAM/preprint article files when narrower manuscript/preprint roles are not used."),
        "author_manuscript": ("Author manuscript or accepted manuscript artifact.", "Flag version/source separately."),
        "preprint": ("Preprint artifact.", "Record preprint version when available."),
        "registry_record": ("Registry/API record artifact.", "Use for NCT/AEA/EGAP/RIDIE/OSF registry JSON/XML/pages."),
        "supplement": ("Supplementary material or appendix file.", "Use for article supplements and supporting packages."),
        "dataset": ("Data or analysis table artifact.", "Use for CSV/TSV/DTA/RDS/XLSX/SAV and similar files."),
        "code": ("Code, notebook, log, or generated output artifact.", "Use for scripts and code execution outputs."),
        "metadata": ("Metadata-only artifact.", "Grounding/resolution only unless values are present in metadata."),
        "screenshot": ("Screenshot artifact.", "Use for manual visual capture of pages/tables/blockers."),
        "abstract_page": ("Abstract-only page artifact.", "Do not promote unless exact value is present."),
        "landing_page": ("Landing page artifact.", "Use for DOI/publisher/repository landing pages."),
        "derived_table": ("Internal derived table artifact.", "Useful for corpus assertions but not original-source evidence."),
        "archive": ("Archive file such as zip/tar/tgz.", "Inventory extracted members separately when used."),
        "archive_member": ("File member inside an archive.", "Set parent_file_id to the archive file."),
        "other": ("Other artifact role.", "Explain in notes."),
    },
    "file_origin": {
        "automated_download": ("Automatically downloaded from a URL/API.", "Record attempt/access route."),
        "api_response": ("API response stored as an artifact.", "Use for registry/metadata JSON/XML."),
        "repository_file": ("Downloaded from a repository platform.", "Examples: OSF, Dataverse, Zenodo, Figshare, openICPSR."),
        "publisher_file": ("Downloaded from a publisher route.", "Use only for lawful/allowed access."),
        "existing_local_file": ("File already existed locally before this run.", "Preserve checksum and path."),
        "user_upload": ("Provided manually by the user.", "Keep original path/source when known."),
        "manual_browser": ("Manually obtained through a browser.", "Record operator/access notes and rights decision."),
        "code_execution_output": ("Generated by running analysis code.", "Record command in extraction_event."),
        "internal_derived": ("Produced by this repo's derived-data pipeline.", "Not original-source evidence unless backed by support rows."),
        "archive_member": ("Extracted from an archive artifact.", "Link to parent_file_id."),
        "unknown": ("Origin not yet determined.", "Use until backfilled."),
    },
    "rights_decision": {
        "open_allowed": ("Mirroring/text extraction appears allowed for this project use.", "Keep license/terms evidence."),
        "internal_only": ("Local/internal use only; do not redistribute bytes.", "Expose metadata/snippets only as allowed."),
        "restricted": ("Access/reuse is restricted or unclear.", "Manual/legal review may be needed."),
        "subscription_required": ("Source appears to require subscription/institutional entitlement.", "Do not treat as public OA."),
        "not_applicable": ("Rights decision is not applicable.", "Use for failed attempts or internal derived artifacts."),
        "unknown": ("Rights have not been assessed.", "Default for pilot backfills."),
        "needs_review": ("Rights need human review before promotion/use.", "Use for publisher/repository/manual routes with unclear terms."),
    },
    "target_acquisition_state": {
        "unanchored": ("No external target identity has been established.", "Danger level: number cannot be tied to a real source."),
        "external_assertion_only": ("An external corpus/database asserts the row, but target identity is weak or incomplete.", "Needs source identification before acquisition."),
        "target_identity_known": ("The represented source can be identified bibliographically or by registry/repository ID.", "Identity exists but source object not yet located/mirrored."),
        "target_located": ("A DOI, registry, repository, or landing page locates the target.", "Located is not mirrored."),
        "source_object_mirrorable": ("A lawful/plausible source object route appears available.", "Next action is selective mirroring."),
        "source_object_mirrored": ("A plausible source object has been mirrored with checksum/path.", "Next action is extraction/verification."),
        "text_or_data_extracted": ("Text/data were extracted from a mirrored object.", "Next action is value-specific verification."),
    },
    "value_verification_state": {
        "not_checked": ("Value has not been checked against source text/data.", "Default for unanchored or unresolved rows."),
        "corpus_assertion_only": ("Value is currently supported only by corpus/database assertion.", "Do not count as original-source verification."),
        "source_object_obtained_not_parsed": ("A source object was obtained but not yet parsed for the value.", "Level 5 but not level 6."),
        "text_or_data_extracted": ("Text/data were extracted but exact D/N support is not confirmed.", "Needs value search and support rows."),
        "value_bearing_source_text_found": ("Relevant text/table/data for the value was found.", "Needs parsed transformation check."),
        "d_n_verified_from_source": ("D/N or native values were verified from source text/data.", "Strict level 6/7 depending on recomputation."),
    },
    "relationship_type": {
        "extraction_source_reports_result_for_represented_source": ("The extraction source directly reports a result about the represented source/work.", "Default direct assertion relationship when no narrower type applies."),
        "corpus_contains_paper": ("A corpus or collection includes a paper.", "Use for paper membership independent of a specific result value."),
        "database_reports_paper_result": ("A database/registry row reports a result or metadata for a paper/study/trial.", "Use when the database is the literal source of copied numbers/text."),
        "repository_supports_paper": ("A package/repository supplies data, code, outputs, or supplements for a paper.", "Use for replication-package support links."),
        "registry_preregisters_study": ("A registry record preregisters or records the study/trial/protocol.", "Use for actual registry/PAP artifacts, not vague corpus claims."),
        "registry_links_publication": ("A registry record links to a paper/report/results source.", "Use for post-trial publication/data/program URLs."),
        "pre_analysis_plan_supports_study": ("A PAP/MPAP/protocol supports the study/result selector.", "Use when a PAP artifact is available outside a registry row."),
        "registered_report_protocol_for_paper": ("A registered-report Stage 1/protocol source supports the final paper.", "Use for registered-report protocol relationships."),
        "publication_reports_registered_study": ("A publication reports results for a registered study.", "Use from article to registry when the article itself documents registration."),
        "replication_of": ("A source or result is a replication of another source/result.", "Use when original and replication sources are known, not only corpus-level assertion."),
        "computational_reproduction_of": ("A source/result computationally reproduces another paper/result.", "Use for same-data/code reproduction relationships."),
        "robustness_reanalysis_of": ("A source/result reanalyzes robustness of another result.", "Use for alternative specifications/checks rather than new-sample replication."),
        "meta_analysis_includes_study": ("A meta-analysis or pooled round includes a component study/result.", "Use for pooled/component hierarchies."),
        "corpus_asserts_result_for_paper": ("A corpus/database asserts that a represented paper/result has specific numbers.", "Use when we are taking the corpus row as the immediate evidence source."),
        "corpus_asserts_preregistration_for_paper": ("A corpus asserts preregistration but no registry/PAP artifact has been obtained.", "Keep confidence low unless the artifact is later resolved."),
        "paper_uses_dataset": ("A paper uses or analyzes a dataset/source.", "Use for paper-data source relationships."),
        "source_derives_from_source": ("One source object is derived from another.", "Use for extracted tables, converted files, and generated outputs."),
        "duplicate_of": ("Two sources/results represent the same object or claim.", "Use for dedupe mapping; do not double-count both."),
        "parent_collection_contains_child": ("A parent collection contains a child source/result.", "Use for corpus, database, or pooled-round parent-child membership."),
    },
    "relationship_subtype": {
        "preregistration": ("General preregistration relationship.", "Use when a more specific PAP/registered-report/trial subtype is unavailable."),
        "pre_analysis_plan": ("Pre-analysis plan artifact.", "Use for PAP documents and PAP sections."),
        "meta_analysis_pre_analysis_plan": ("Meta-analysis pre-analysis plan artifact.", "Use for MPAPs such as Metaketa pooled analysis plans."),
        "registered_report_stage1_protocol": ("Stage 1 registered-report protocol.", "Use for accepted protocols before results."),
        "registered_report_stage2_results": ("Stage 2 registered-report results paper.", "Use when mapping protocol to final registered-report paper."),
        "trial_registry_record": ("Trial or study registry record.", "Use for NCT/AEA/RIDIE/EGAP/OSF-style registry records."),
        "data_or_code_package": ("Data/code/package support relationship.", "Use for repository/package mappings."),
        "paper_supplement": ("Supplementary paper file relationship.", "Use for appendices, supplements, and supplemental tables."),
        "direct_replication": ("Replication intended to repeat the same claim/design closely.", "Use for same-claim original/replication pairs."),
        "conceptual_replication": ("Replication of a construct using different operationalization/design.", "Use when source says conceptual replication or design differs materially."),
        "computational_reproduction": ("Same-data/code reproduction.", "Use for computational reproducibility checks."),
        "robustness_reanalysis": ("Alternative analysis/specification check.", "Use for robustness projects."),
        "extension_study": ("Replication plus extension or new conditions.", "Use when extension is material."),
        "pilot_full_scale_pair": ("Pilot/smaller study paired with later full-scale/larger study.", "Use for pilot-to-main-study pairs."),
        "pooled_round_component": ("Component study included in pooled round/meta-analysis.", "Use for Metaketa and similar pooled designs."),
        "corpus_child_paper": ("Paper included as a child of a corpus.", "Use for membership without result-level numbers."),
        "database_child_result": ("Result row included as child of a database/corpus.", "Use for row-level source assertions."),
        "citation_or_link_only": ("Relationship inferred only from citation/link metadata.", "Use when no value/selector evidence has been copied."),
        "unknown": ("Subtype is not yet known.", "Use only while staged; add an extraction_problem if it matters for promotion."),
    },
    "prereg_status": {
        "prereg_confirmed_pre_data": ("Preregistration/PAP confirmed before data collection.", "Use only with date/timing evidence."),
        "prereg_confirmed_pre_analysis": ("Preregistration/PAP confirmed before analysis/results but not necessarily before data collection.", "Use only with timing evidence."),
        "registered_report": ("Registered-report workflow evidence exists.", "Use with protocol/stage mapping details."),
        "proposal_pre_fielding_not_full_prereg": ("A proposal/design was locked before fielding but lacks full preregistration/PAP elements.", "Useful for TESS-like cases; do not overstate as PAP-confirmed."),
        "registry_metadata_only": ("A registry record exists but timing/selector/details are not fully audited.", "Use until filing date and selector text are verified."),
        "registry_record_timing_not_audited": ("A registry record is identified and sourceable, but its preregistration timing has not been audited.", "Use for registry-derived rows until dates/amendments are checked."),
        "prereg_asserted_by_corpus_no_artifact": ("A corpus or source label says preregistered, but no registry/PAP artifact URL has been obtained.", "Low-confidence prereg evidence; must not become PAP-confirmed without artifact."),
        "not_preregistered": ("Evidence indicates no preregistration.", "Use only when source/corpus explicitly classifies it as not preregistered."),
        "unknown": ("Preregistration status has not been determined.", "Use as default outside prereg panels."),
    },
    "replication_role": {
        "none": ("No replication/reproduction relationship is asserted for this result.", "Default for ordinary result rows."),
        "original_study": ("This result is the original/target side of a replication pair.", "Use when paired to later replication/reproduction."),
        "replication_study": ("This result is the replicating/follow-up side.", "Use for new-sample/direct/conceptual replication rows."),
        "computational_reproduction": ("This result is a computational reproduction of a prior result.", "Use for same-data/code reproduction."),
        "robustness_check": ("This result is a robustness reanalysis of a prior result.", "Use for alternative specifications/checks."),
        "corpus_replication_assertion": ("The row asserts a replication relationship, but side/source details are incomplete.", "Stage until original/replication sides are resolved."),
        "unknown": ("Role is not yet known.", "Use only temporarily and add a problem if relevant."),
    },
    "support_role": {
        "effect_text": ("Support object contains or asserts the effect/statistic text.", "Use when this object is the literal source of verbatim_effect_text."),
        "n_text": ("Support object contains or asserts the N/sample-size text.", "Use when this object is the literal source of verbatim_n_text."),
        "outcome_text": ("Support object contains or asserts the outcome label/text.", "Use when outcome wording comes from a different source than the effect."),
        "selector_text": ("Support object contains prereg/PAP/focal-selector text.", "Use for registry/PAP/MPAP selector support."),
        "conversion_input": ("Support object contains inputs needed for D/native conversion.", "Use for SDs, control means, event counts, arm Ns, SEs, or formulas."),
        "raw_data": ("Support object is raw data for recomputation.", "Use for row-level or participant-level data files."),
        "analytic_data": ("Support object is cleaned/analytic data.", "Use when recomputation starts from prepared analysis data."),
        "code": ("Support object is code/script/notebook.", "Use for scripts that produce or transform values."),
        "recomputed_output": ("Support object is generated output from rerunning code.", "Use for logs, tables, or saved model outputs."),
        "bibliographic_identity": ("Support object grounds the identity of the represented work.", "Use for DOI/Crossref/PubMed/OpenAlex records and title metadata."),
        "access_grounding": ("Support object proves route/access status but not the number.", "Use for abstracts, landing pages, paywalls, and blocked attempts."),
        "relationship_evidence": ("Support object asserts a mapping between sources.", "Use for prereg, replication, package, and corpus-membership relationships."),
        "other": ("Other support role.", "Explain in notes."),
    },
    "coding_status": {
        "fully_coded": ("All applicable promotion gates pass.", "Only use when source identity, access, locator, verbatim text, parse, transformation, selector, and dedupe are complete."),
        "coded_with_schema_gaps": ("Useful staged row with known provenance gaps.", "Keep visible and non-promoted until gaps are resolved."),
        "staged_native_metric": ("Native effect/SE/N are meaningful, but D conversion is not defensible.", "Use for clustered/policy/administrative effects lacking D inputs."),
        "blocked_missing_d_or_n": ("Source exists but effect, N, or conversion inputs are missing.", "Add extraction_problem with exact missing field."),
        "blocked_access": ("Access barrier prevents source acquisition or verification.", "Record route, barrier, and manual action needed."),
        "excluded": ("Row is intentionally excluded from plotting/analysis.", "Explain why in notes/problem row."),
        "duplicate_existing": ("Row duplicates another represented result.", "Map duplicate and ensure canonical_result does not double-count it."),
    },
    "evidence_level_name": {
        "unanchored_number": ("A number exists but cannot be tied to an external source or represented work.", "Level 0; never public-promote."),
        "internal_trace_only": ("The row traces only to this repo's derived/intermediate files.", "Level 1; useful for debugging, not public evidence."),
        "external_source_assertion": ("An external source asserts the number but does not identify the represented target robustly.", "Level 2; corpus assertion without durable child grounding."),
        "external_assertion_with_target_source": ("An external source asserts the number and provides enough info to find the target source.", "Level 3; current minimum floor for public diagnostic plotting."),
        "target_source_independently_grounded": ("The represented target source was resolved independently by DOI/PMID/PMCID/NCT/registry/URL/citation database.", "Level 4; identity grounded, number not yet verified from original."),
        "original_source_obtained": ("Value-bearing source object bytes were obtained or mirrored.", "Level 5; metadata/paywall/abstract-only pages do not count unless value is present."),
        "original_number_extracted": ("We copied/extracted the exact number/supporting text from original or authoritative source bytes.", "Level 6; source-text verification achieved."),
        "recomputed_from_raw": ("We recomputed the number from raw data/code and preserved outputs.", "Level 7; strongest computational provenance."),
    },
    "d_conversion_method": {
        "reported_d": ("Source directly reports Cohen's d.", "Use directly; document whether signed/absolute and any correction."),
        "reported_g": ("Source directly reports Hedges' g.", "Use directly or store as g; document if converted to d-like axis."),
        "reported_smd": ("Source directly reports standardized mean difference.", "Use when the standardization is source-defined."),
        "chinn_log_or_to_d": ("Log odds ratio converted to d by Chinn formula.", "Require log OR and enough context to justify latent-scale conversion."),
        "event_counts_to_log_or_to_d": ("Arm event counts converted to log OR then d.", "Require treatment/control event and non-event counts; record continuity correction if used."),
        "r_to_d": ("Correlation converted to d.", "Use d = 2r/sqrt(1-r^2)."),
        "fisher_z_to_r_to_d": ("Fisher z converted to r then d.", "Use r = tanh(z), then r_to_d."),
        "standardized_outcome_coefficient": ("Regression coefficient on a documented standardized outcome.", "Use only when outcome standardization source is documented."),
        "source_provided_d_proxy": ("A source/corpus provides a D-like proxy but original conversion is not fully verified.", "Flag as proxy and avoid claiming original-source conversion."),
        "paper_median_of_child_d": ("Paper-level/canonical D is the median of eligible child result Ds.", "Preserve child rows and aggregation rule."),
        "no_d_native_metric": ("No defensible D conversion; native metric only.", "Use for native panel rows."),
        "blocked_missing_inputs": ("D/native conversion is blocked because inputs are missing.", "Add extraction_problem and to-do."),
    },
    "mapping_evidence_type": {
        "verbatim_text": ("Relationship is supported by copied text.", "Preferred when an article/registry/PAP explicitly states the relationship."),
        "metadata_field": ("Relationship is supported by a structured metadata field.", "Use for corpus/database/API columns."),
        "doi_link": ("Relationship is supported by DOI matching/linking.", "Use when DOI itself is the relationship evidence."),
        "registry_link": ("Relationship is supported by registry link/ID.", "Use for NCT/AEA/EGAP/RIDIE/OSF registry relationships."),
        "citation_match": ("Relationship is supported by citation matching.", "Use when title/author/year/citation identifies the target."),
        "title_author_year_match": ("Relationship is supported by title/author/year matching.", "Use when no durable ID is available."),
        "code_or_package_manifest": ("Relationship is supported by package manifest, file path, or code metadata.", "Use for replication packages and package-derived rows."),
        "manual_judgment": ("Relationship currently depends on manual coding judgment.", "Use sparingly and keep confidence low/medium."),
        "unknown": ("Evidence type not yet known.", "Use only while staged."),
    },
    "relationship_timing": {
        "pre_data_collection": ("Relationship/artifact predates data collection.", "Use only when timing evidence supports this."),
        "pre_analysis": ("Relationship/artifact predates analysis/results but data may already exist.", "Use for PAPs, protocols, or registered reports when analysis timing is verified."),
        "post_data_pre_results": ("Relationship/artifact was created after data collection but before results were known or reported.", "Use when this distinction is documented."),
        "post_results": ("Relationship/artifact was created after results were known or public.", "Do not use as preregistered confirmatory evidence."),
        "not_applicable": ("Timing is not meaningful for this relationship.", "Use for corpus membership, duplicate, and many package-support relationships."),
        "unknown": ("Timing has not been audited or cannot be determined.", "Use honestly rather than guessing."),
    },
    "confidence": {
        "high": ("Evidence is direct, specific, and low ambiguity.", "Use when source text/metadata clearly supports the coded value or relationship."),
        "medium": ("Evidence is plausible but has unresolved details or relies on structured corpus/database interpretation.", "Use for most corpus assertions before original-source verification."),
        "low": ("Evidence is weak, indirect, incomplete, or needs manual confirmation.", "Use for title-only/corpus-only assertions and ambiguous matches."),
        "blocked": ("Evidence cannot currently be checked because access or identifiers are blocked.", "Use with extraction_problem and manual to-do."),
    },
}


VOCAB_ALIASES = {
    "transformation_confidence": "confidence",
    "extraction_confidence": "confidence",
    "relationship_confidence": "confidence",
    "prereg_timing": "relationship_timing",
    "replication_kind": "relationship_subtype",
}


def vocab(name: str) -> str:
    return " | ".join(CONTROLLED_VOCABS[name])


def field(
    table_name: str,
    column_name: str,
    data_type: str,
    required_level: str,
    definition: str,
    coding_rules: str,
    allowed_values: str = "",
    example: str = "",
    qa_checks: str = "",
) -> dict[str, str]:
    return {
        "table_name": table_name,
        "column_name": column_name,
        "data_type": data_type,
        "required_level": required_level,
        "allowed_values": allowed_values,
        "definition": definition,
        "coding_rules": coding_rules,
        "example": example,
        "qa_checks": qa_checks,
    }


def default_qa_checks(row: dict[str, str]) -> str:
    checks: list[str] = []
    required_level = row.get("required_level", "")
    data_type = row.get("data_type", "")
    allowed_values = row.get("allowed_values", "")
    column_name = row.get("column_name", "")

    if required_level in {"required", "required_for_promotion", "required_for_plot", "required_for_d_or_native"}:
        checks.append("Must be nonblank when the row is promoted or used for the relevant plot/panel.")
    if allowed_values:
        checks.append("If nonblank, must be one of allowed_values exactly.")
    if data_type in {"number", "integer"}:
        checks.append("If nonblank, must parse as a numeric value.")
    if data_type == "boolean":
        checks.append("Use lowercase true/false.")
    if data_type == "url":
        checks.append("Use a stable URL; prefer DOI/registry/repository/API URLs over search pages.")
    if data_type == "path":
        checks.append("Use repo-relative paths when possible; verify existence when access_status implies local bytes.")
    if column_name.endswith("_id") or column_name.endswith("_ids"):
        checks.append("IDs should be stable; foreign keys should match the referenced table when applicable.")
    if "verbatim" in column_name:
        checks.append("Must be copied from source text/fields, not a display label or paraphrase.")
    if "citation_key" in column_name:
        checks.append("Generated dot keys are internal only; real source citations must map to a bibliography entry.")
    if not checks:
        checks.append("Review for consistency with the field definition and coding rules.")
    return " ".join(checks)


def field_rows_with_defaults() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for row in FIELDS:
        updated = dict(row)
        if not updated.get("qa_checks"):
            updated["qa_checks"] = default_qa_checks(updated)
        rows.append(updated)
    return rows


def vocab_definition_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for field_name, values in CONTROLLED_VOCABS.items():
        definitions = VOCAB_VALUE_DEFINITIONS.get(field_name, {})
        for value in values:
            definition, coding_notes = definitions.get(
                value,
                (
                    f"Controlled value `{value}` for `{field_name}`.",
                    "Use only when this exact status/category applies; otherwise leave blank or use unknown/blocked as appropriate.",
                ),
            )
            rows.append(
                {
                    "field_name": field_name,
                    "allowed_value": value,
                    "definition": definition,
                    "coding_notes": coding_notes,
                }
            )
    existing = {(row["field_name"], row["allowed_value"]) for row in rows}
    for field in FIELDS:
        allowed_values = field.get("allowed_values", "")
        if not allowed_values:
            continue
        field_name = field["column_name"]
        if field_name in CONTROLLED_VOCABS:
            continue
        source_vocab_name = VOCAB_ALIASES.get(field_name)
        source_definitions = VOCAB_VALUE_DEFINITIONS.get(source_vocab_name or "", {})
        for value in [part.strip() for part in allowed_values.split("|") if part.strip()]:
            key = (field_name, value)
            if key in existing:
                continue
            definition, coding_notes = source_definitions.get(
                value,
                (
                    f"Controlled value `{value}` for `{field_name}`.",
                    "Use only when this exact status/category applies; otherwise leave blank or use unknown/blocked as appropriate.",
                ),
            )
            rows.append(
                {
                    "field_name": field_name,
                    "allowed_value": value,
                    "definition": definition,
                    "coding_notes": coding_notes,
                }
            )
            existing.add(key)
    return rows


FIELDS = [
    field("source.tsv", "source_id", "string", "required", "Stable unique source ID.", "Prefix by source type when useful; do not recycle IDs.", example="src_ctgov_kg"),
    field("source.tsv", "source_type", "category", "required", "Kind of source object.", "Use the narrowest true object type.", vocab("source_type"), "database"),
    field("source.tsv", "title", "string", "required", "Human-readable title of the source.", "Use source title, registry title, repository title, or file title."),
    field("source.tsv", "citation_key", "string", "conditional", "BibTeX key for this source.", "Blank only when no real bibliographic source exists. Never use generated dot keys as represented-source citations."),
    field("source.tsv", "citation_rendered", "string", "conditional", "Rendered citation text copied from the bibliography process.", "Keep even when a BibTeX split later changes."),
    field("source.tsv", "bibtex_file", "path", "conditional", "Repo-relative path to the BibTeX file containing citation_key.", "Usually docs/references.bib or plot_dot_references.bib."),
    field("source.tsv", "doi", "string", "recommended", "Digital Object Identifier if available.", "Normalize without https://doi.org/ when possible."),
    field("source.tsv", "pmid", "string", "optional", "PubMed ID if available.", "Use numeric PMID only."),
    field("source.tsv", "registry_id", "string", "conditional", "Registry identifier such as NCT, AEARCTR, EGAP, RIDIE, OSF.", "Required for registry records."),
    field("source.tsv", "url", "url", "recommended", "Stable landing URL.", "Prefer DOI, registry, repository, or official landing page."),
    field("source.tsv", "publication_year", "integer", "optional", "Publication or release year.", "Leave blank if unknown."),
    field("source.tsv", "source_status", "category", "required", "Role of this source in the dataset.", "Use primary for sources that can support extraction rows.", vocab("source_status"), "primary"),
    field("source.tsv", "notes", "string", "optional", "Concise source-level notes.", "Do not store result extraction details here; use source_result/extraction_event."),
    field("source_access.tsv", "access_id", "string", "required", "Stable unique access ID.", "One source can have multiple access rows."),
    field("source_access.tsv", "source_id", "string", "required", "Foreign key to source.tsv.", "Must match source.source_id."),
    field("source_access.tsv", "access_role", "category", "required", "Role of this access route.", "Use file_member for files inside archives.", vocab("access_role"), "direct_download"),
    field("source_access.tsv", "remote_url", "url", "conditional", "Direct web URL when available.", "Prefer direct file/API URL over landing page when it can reproduce bytes."),
    field("source_access.tsv", "api_url", "url", "optional", "API URL used to fetch metadata or files.", "Use when data came from API rather than browser."),
    field("source_access.tsv", "final_url", "url", "optional", "Final URL after redirects.", "Keep distinct from remote_url so DOI/publisher redirect chains remain auditable."),
    field("source_access.tsv", "http_status", "string", "optional", "HTTP status code or API status from retrieval attempt.", "Use numeric HTTP status when available; leave blank for local-only files."),
    field("source_access.tsv", "redirect_chain", "string", "optional", "Redirect chain observed during acquisition.", "Use pipe-delimited URLs or compact JSON; keep TSV-safe."),
    field("source_access.tsv", "host", "string", "optional", "Host/domain of final retrieval route.", "Useful for per-host retry, policy, and blocker audits."),
    field("source_access.tsv", "local_path", "path", "conditional", "Repo-relative local mirror path.", "Required when file is mirrored locally."),
    field("source_access.tsv", "file_member_path", "path", "conditional", "Path of a file inside a zip/tar/repository.", "Use for archive members or package internal files."),
    field("source_access.tsv", "content_type", "string", "recommended", "File or response type.", "Examples: csv, tsv, pdf, zip, html, json, dta, rds."),
    field("source_access.tsv", "file_sha256", "string", "conditional", "SHA-256 checksum of local file.", "Required for mirrored files unless impractical."),
    field("source_access.tsv", "file_size_bytes", "integer", "conditional", "Size of local file.", "Required for mirrored files unless impractical."),
    field("source_access.tsv", "retrieved_at", "datetime", "recommended", "ISO date/time of retrieval.", "Use local current date if exact timestamp unavailable."),
    field("source_access.tsv", "retrieved_by", "string", "recommended", "Who or what retrieved the file.", "Use codex, user, script name, or unknown."),
    field("source_access.tsv", "retrieval_method", "category", "required", "How bytes were obtained.", "Record manual downloads honestly.", vocab("retrieval_method"), "automated_download"),
    field("source_access.tsv", "access_status", "category", "required", "Whether the access path is usable.", "Blocked/gated sources still get rows.", vocab("access_status"), "local_file_found"),
    field("source_access.tsv", "access_strategy", "category", "recommended", "Resolver or acquisition route tried for this access row.", "Keep direct journal, OA candidate, preprint/repository, registry, and metadata routes separate.", vocab("access_strategy"), "preprint_repository_candidate"),
    field("source_access.tsv", "source_byte_class", "category", "recommended", "Class of bytes or artifact obtained.", "Do not count metadata, abstract pages, paywall pages, CAPTCHA pages, or access-denied pages as level 5 unless the plotted value is present on that page.", vocab("source_byte_class"), "publisher_landing_or_abstract"),
    field("source_access.tsv", "level5_eligible", "boolean", "recommended", "Whether this access object can qualify as strict level 5 after identity review.", "True only for value-bearing source objects such as full article, registry record, supplement, data/code, or repository manuscript.", example="false"),
    field("source_access.tsv", "license_url", "url", "optional", "URL or source of license/reuse information.", "Use license links from Crossref, repository metadata, PMC, publisher pages, or data package metadata."),
    field("source_access.tsv", "license_category", "category", "recommended", "Coarse access/reuse category.", "Use open only when mirroring/reuse appears allowed; otherwise use restricted, subscription, unknown, or not_applicable.", vocab("license_category"), "unknown"),
    field("source_access.tsv", "storage_allowed", "boolean_or_unknown", "recommended", "Whether local storage/mirroring is allowed for project use.", "Use true/false/unknown; do not infer true from successful download alone.", example="unknown"),
    field("source_access.tsv", "source_version", "category", "recommended", "Version/class of the retrieved object.", "Distinguish VOR, accepted manuscript, preprint, registry record, supplement, dataset, code, and metadata.", vocab("source_version"), "version_of_record"),
    field("source_access.tsv", "retrieval_policy_notes", "string", "optional", "Notes on rate limits, TDM policy, license limits, or manual access constraints.", "Keep policy facts here; detailed attempts belong in extraction_event."),
    field("source_access.tsv", "abstract_or_detail_text", "string", "optional", "Short abstract, title, description, registry summary, or landing-page detail extracted during acquisition.", "Grounding evidence only; do not treat as original-number verification unless it contains the exact plotted value.", example="Publisher abstract captured from paywalled DOI page."),
    field("source_access.tsv", "abstract_or_detail_source_url", "url", "optional", "URL from which abstract_or_detail_text was extracted.", "Use the final URL after redirects when available."),
    field("source_access.tsv", "paywall_or_login_seen", "boolean", "recommended", "Whether this route returned a paywall or login artifact.", "Use with access_barrier and extraction_problem for manual follow-up.", example="true"),
    field("source_access.tsv", "captcha_or_bot_block_seen", "boolean", "recommended", "Whether this route triggered a CAPTCHA or bot-check artifact.", "Stop automated retries for that host/object and record as blocked.", example="false"),
    field("source_access.tsv", "preprint_or_repository_candidate", "boolean", "recommended", "Whether this route was a preprint, author manuscript, repository, or institutional archive candidate.", "Usually discovered through OpenAlex, Semantic Scholar, Unpaywall, Crossref, Europe PMC, or repository metadata.", example="true"),
    field("source_access.tsv", "access_barrier", "string", "conditional", "Barrier if not locally accessible.", "Examples: login, license, JS-only, 403, missing file."),
    field("source_access.tsv", "access_notes", "string", "optional", "Extra access details.", "Keep concise; use extraction_event for procedural details."),
    field("source_access_attempt.tsv", "attempt_id", "string", "required", "Stable unique attempt ID.", "One row per resolver/API/download attempt or cache hit."),
    field("source_access_attempt.tsv", "source_id", "string", "required", "Foreign key to source.tsv.", "The source being resolved or acquired."),
    field("source_access_attempt.tsv", "access_id", "string", "conditional", "Foreign key to source_access.tsv when the attempt produced or checked a source access row.", "Leave blank only for rejected candidates not represented in source_access."),
    field("source_access_attempt.tsv", "attempt_group_id", "string", "recommended", "ID grouping attempts for one resolver pass/source target.", "Use to connect Crossref/OpenAlex/Unpaywall/etc. fanout for one source."),
    field("source_access_attempt.tsv", "attempt_order", "integer", "recommended", "Order of this attempt within the source resolver chain.", "Start at 1 for each source when possible."),
    field("source_access_attempt.tsv", "resolver_name", "string", "recommended", "Resolver/plugin name.", "Examples: crossref_metadata, openalex_work, unpaywall_doi, pmc_oa."),
    field("source_access_attempt.tsv", "resolver_version", "string", "optional", "Resolver/plugin version or code commit.", "Keep stable enough to reproduce route behavior."),
    field("source_access_attempt.tsv", "resolver_strategy", "category", "required", "Resolver/acquisition strategy tried.", "Use the same controlled vocabulary as source_access.access_strategy.", vocab("access_strategy"), "openalex_metadata"),
    field("source_access_attempt.tsv", "candidate_rank", "integer", "optional", "Rank of candidate within resolver output.", "Use 1 for top candidate after ranking."),
    field("source_access_attempt.tsv", "candidate_rank_reason", "string", "optional", "Why this candidate was ranked here.", "Use match scores, route priority, and license/source-object class."),
    field("source_access_attempt.tsv", "candidate_url", "url", "conditional", "Candidate URL requested or considered.", "Use DOI/API/OA/preprint/repository URL as attempted."),
    field("source_access_attempt.tsv", "candidate_url_source", "string", "optional", "Where the candidate URL came from.", "Examples: Crossref link, OpenAlex best_oa_location, Unpaywall oa_location, manual."),
    field("source_access_attempt.tsv", "final_url", "url", "optional", "Final URL after redirects.", "Keep paywall/landing-page final URL for blockers."),
    field("source_access_attempt.tsv", "host", "string", "optional", "Host/domain reached.", "Useful for per-host policies and blockers."),
    field("source_access_attempt.tsv", "method", "string", "optional", "HTTP/API/file method.", "Examples: GET, API JSON, local_file_check."),
    field("source_access_attempt.tsv", "http_status", "string", "optional", "HTTP/API status code.", "Leave blank for local-only checks."),
    field("source_access_attempt.tsv", "redirect_chain", "string", "optional", "Redirect chain observed for this attempt.", "Use compact JSON or pipe-delimited URLs."),
    field("source_access_attempt.tsv", "cache_key", "string", "optional", "Cache key for this request or candidate.", "Use deterministic key based on method, canonical URL, and resolver version."),
    field("source_access_attempt.tsv", "cache_hit_yn", "boolean", "recommended", "Whether this attempt used cached data.", "Use true/false."),
    field("source_access_attempt.tsv", "retry_count", "integer", "optional", "Number of retries for this attempt.", "Use 0 for first successful/terminal attempt."),
    field("source_access_attempt.tsv", "retry_after_seconds", "number", "optional", "Retry-After delay if returned by host.", "Store header value when available."),
    field("source_access_attempt.tsv", "content_type_header", "string", "optional", "Raw content-type header if known.", "Use exact header when available."),
    field("source_access_attempt.tsv", "content_type_sniffed", "string", "optional", "Content type inferred from bytes, file extension, or classifier.", "Examples: pdf, html, json, csv."),
    field("source_access_attempt.tsv", "byte_count", "integer", "optional", "Number of bytes obtained.", "Use local file size where known."),
    field("source_access_attempt.tsv", "sha256", "string", "conditional", "SHA-256 checksum for bytes obtained.", "Required when mirrored bytes are kept and practical."),
    field("source_access_attempt.tsv", "local_path", "path", "conditional", "Repo-relative local mirror path produced or checked by this attempt.", "Leave blank for metadata-only unresolved candidates."),
    field("source_access_attempt.tsv", "source_byte_class", "category", "recommended", "Class of bytes/artifact obtained by this attempt.", "Use paywall/abstract/metadata classes honestly.", vocab("source_byte_class"), "metadata_record"),
    field("source_access_attempt.tsv", "access_status", "category", "required", "Usability status of this attempt.", "Use blocked/access_denied/login_required rather than overwriting with success.", vocab("access_status"), "downloaded"),
    field("source_access_attempt.tsv", "access_barrier", "string", "conditional", "Barrier hit by this attempt.", "Examples: paywall, login, captcha, 403, no_oa_copy, missing_api_key."),
    field("source_access_attempt.tsv", "abstract_or_detail_text", "string", "optional", "Abstract/detail/title/description text captured from this route.", "Grounding text only unless it contains the exact coded value."),
    field("source_access_attempt.tsv", "paywall_or_login_seen", "boolean", "recommended", "Whether this attempt hit a paywall/login artifact.", "Use true for publisher paywalls and sign-in pages.", example="false"),
    field("source_access_attempt.tsv", "captcha_or_bot_block_seen", "boolean", "recommended", "Whether this attempt hit a CAPTCHA/bot-check artifact.", "Stop automated retries for that route.", example="false"),
    field("source_access_attempt.tsv", "preprint_or_repository_candidate", "boolean", "recommended", "Whether the attempted URL is a preprint/repository/manuscript candidate.", "Typically discovered via OpenAlex, Unpaywall, Semantic Scholar, Europe PMC, or manual search.", example="true"),
    field("source_access_attempt.tsv", "license_url", "url", "optional", "License or reuse-policy URL discovered for this attempt.", "Use repository/publisher/API license when available."),
    field("source_access_attempt.tsv", "license_category", "category", "recommended", "Coarse license/access category for this attempt.", "Use unknown when not assessed.", vocab("license_category"), "unknown"),
    field("source_access_attempt.tsv", "storage_allowed", "boolean_or_unknown", "recommended", "Whether this attempt's bytes may be stored locally.", "Use unknown unless policy is clear."),
    field("source_access_attempt.tsv", "robots_status", "string", "optional", "robots.txt or crawl-policy status for this candidate.", "Examples: allowed, disallowed, unknown, not_checked."),
    field("source_access_attempt.tsv", "tdm_policy_status", "string", "optional", "TDM policy status observed for host/route.", "Examples: allowed, restricted, subscription_required, unknown."),
    field("source_access_attempt.tsv", "title_match_score", "number", "optional", "Similarity score between candidate title and target title.", "Use 0-1 when available."),
    field("source_access_attempt.tsv", "doi_match_score", "number", "optional", "DOI/identifier match score.", "Use 1 for exact DOI match, 0 for mismatch, blank if not checked."),
    field("source_access_attempt.tsv", "author_year_match_score", "number", "optional", "Author/year match score.", "Use 0-1 when available."),
    field("source_access_attempt.tsv", "identity_decision", "string", "optional", "Candidate identity decision.", "Examples: accepted_exact_doi, accepted_title_year, rejected_mismatch, needs_review."),
    field("source_access_attempt.tsv", "identity_decision_reason", "string", "optional", "Reason for candidate identity decision.", "Record mismatch or confidence basis."),
    field("source_access_attempt.tsv", "retrieval_method", "category", "required", "How this attempt was made.", "Record manual and API routes distinctly.", vocab("retrieval_method"), "api_download"),
    field("source_access_attempt.tsv", "retrieved_at", "datetime", "recommended", "ISO date/time attempted.", "Use batch timestamp when exact time unavailable."),
    field("source_access_attempt.tsv", "retrieved_by", "string", "recommended", "Tool/person that performed attempt.", "Examples: codex, user, source resolver script."),
    field("source_access_attempt.tsv", "decision", "category", "required", "Outcome decision for this attempt.", "Do not equate metadata/abstract bytes with value-bearing source objects.", vocab("attempt_decision"), "metadata_only"),
    field("source_access_attempt.tsv", "decision_reason", "string", "recommended", "Why this decision was assigned.", "Explain access blockers, mismatch, or successful mirror."),
    field("source_access_attempt.tsv", "stop_reason", "string", "optional", "Terminal stop reason for this route.", "Examples: success, paywall, captcha, no_oa_copy, mismatch, rate_limited."),
    field("source_access_attempt.tsv", "next_action", "string", "optional", "Next action when unresolved.", "Examples: try_pmc, try_unpaywall, manual_library_access, parse_pdf, no_action."),
    field("source_access_attempt.tsv", "notes", "string", "optional", "Attempt-level notes.", "Keep route-specific comments here; source-level conclusions go in source_access/source_result."),
    field("source_file.tsv", "source_file_id", "string", "required", "Stable unique file/artifact ID.", "Prefer content-addressed IDs when practical."),
    field("source_file.tsv", "source_id", "string", "required", "Foreign key to source.tsv.", "The source this artifact belongs to."),
    field("source_file.tsv", "access_id", "string", "conditional", "Foreign key to source_access.tsv.", "Required when artifact came through a known access route."),
    field("source_file.tsv", "attempt_id", "string", "conditional", "Foreign key to source_access_attempt.tsv.", "Required when artifact was produced by an acquisition attempt."),
    field("source_file.tsv", "source_version_id", "string", "conditional", "Foreign key to source_version.tsv.", "Use when artifact version is known or inferred."),
    field("source_file.tsv", "file_role", "category", "required", "Role of artifact.", "Use dataset/code/supplement/full_article/etc.; do not call internal derived tables original source evidence.", vocab("file_role"), "dataset"),
    field("source_file.tsv", "file_origin", "category", "required", "How artifact originated.", "Distinguish repository, publisher, API, user upload, existing local, and internal derived artifacts.", vocab("file_origin"), "existing_local_file"),
    field("source_file.tsv", "source_byte_class", "category", "required", "Class of bytes/artifact.", "Same vocabulary as access attempts.", vocab("source_byte_class"), "dataset_file"),
    field("source_file.tsv", "url", "url", "conditional", "Original URL for artifact.", "Use direct file/API URL when available."),
    field("source_file.tsv", "final_url", "url", "optional", "Final URL after redirects.", "Keep distinct from original URL."),
    field("source_file.tsv", "storage_uri", "path", "conditional", "Project storage URI/path.", "May equal local_path for local file storage."),
    field("source_file.tsv", "local_path", "path", "conditional", "Repo-relative local path.", "Required for mirrored bytes stored in repo/workspace."),
    field("source_file.tsv", "filename_original", "string", "optional", "Original filename if known.", "Use download filename or archive member name."),
    field("source_file.tsv", "filename_normalized", "string", "optional", "Normalized project filename.", "Useful after de-duplication or extraction."),
    field("source_file.tsv", "media_type_reported", "string", "optional", "Reported media/content type.", "Header or metadata value."),
    field("source_file.tsv", "media_type_sniffed", "string", "optional", "Inferred file/media type.", "Use extension/magic-byte classifier."),
    field("source_file.tsv", "byte_size", "integer", "conditional", "Artifact size in bytes.", "Required when local file exists and size is practical to compute."),
    field("source_file.tsv", "sha256", "string", "conditional", "Computed SHA-256 checksum.", "Required for mirrored bytes unless impractical."),
    field("source_file.tsv", "provider_checksum_type", "string", "optional", "Provider checksum type.", "Examples: md5, sha1, sha256, etag."),
    field("source_file.tsv", "provider_checksum_value", "string", "optional", "Provider checksum value.", "Keep provider value even when not SHA-256."),
    field("source_file.tsv", "content_fingerprint", "string", "optional", "Secondary fingerprint for extracted text/content.", "Useful for de-duplicating normalized text."),
    field("source_file.tsv", "text_sha256", "string", "optional", "SHA-256 of extracted text.", "Populate after text extraction."),
    field("source_file.tsv", "archive_member_path", "path", "conditional", "Path inside archive.", "Use for zip/tar member files."),
    field("source_file.tsv", "parent_file_id", "string", "conditional", "Parent archive/source_file ID.", "Required for extracted archive members when parent is tracked."),
    field("source_file.tsv", "page_count", "integer", "optional", "Page count for PDF/image artifacts.", "Populate after parsing when possible."),
    field("source_file.tsv", "word_count", "integer", "optional", "Extracted word count.", "Populate after text extraction when possible."),
    field("source_file.tsv", "extraction_ready_yn", "boolean", "recommended", "Whether artifact is ready for text/data extraction.", "Use false for paywall pages, blocked artifacts, or unsupported binaries.", example="true"),
    field("source_file.tsv", "level5_eligible", "boolean", "recommended", "Whether artifact can qualify as strict level 5.", "Requires plausible value-bearing source object and lawful/local mirror.", example="false"),
    field("source_file.tsv", "created_at", "datetime", "recommended", "When artifact row/file was created or observed.", "Use retrieval time or batch timestamp."),
    field("source_file.tsv", "fixity_checked_at", "datetime", "conditional", "When checksum/fixity was checked.", "Use retrieval time if checksum was computed then."),
    field("source_file.tsv", "notes", "string", "optional", "Artifact notes.", "Explain internal derived artifacts or unresolved versioning."),
    field("source_version.tsv", "source_version_id", "string", "required", "Stable version ID.", "One version assertion per source/version."),
    field("source_version.tsv", "source_id", "string", "required", "Foreign key to source.tsv.", "The versioned source."),
    field("source_version.tsv", "version_label", "string", "required", "Human-readable version label.", "Examples: version_of_record, preprint v2, registry snapshot 2026-04-30."),
    field("source_version.tsv", "version_number", "string", "optional", "Source-native version number.", "Examples: arXiv v2, Dataverse V3, Zenodo record version."),
    field("source_version.tsv", "version_date", "datetime", "optional", "Version date.", "Use source-native date where known."),
    field("source_version.tsv", "version_source", "string", "recommended", "Where version information came from.", "Examples: source_access, repository metadata, Crossref relation, manual."),
    field("source_version.tsv", "is_version_of_source_id", "string", "conditional", "Source ID of another version of the same work.", "Use for preprint/VOR/source relationships."),
    field("source_version.tsv", "is_version_of_identifier", "string", "conditional", "External identifier of related version/work.", "Use DOI/arXiv/PMCID/etc. when source row not created yet."),
    field("source_version.tsv", "is_version_of_record", "boolean", "recommended", "Whether this version is the publisher version of record.", "Use true/false/unknown if needed.", example="false"),
    field("source_version.tsv", "preprint_version_yn", "boolean", "recommended", "Whether this is a preprint version.", "Use true/false."),
    field("source_version.tsv", "accepted_manuscript_yn", "boolean", "recommended", "Whether this is an accepted manuscript.", "Use true/false."),
    field("source_version.tsv", "published_vor_yn", "boolean", "recommended", "Whether this is a published VOR.", "Use true/false."),
    field("source_version.tsv", "registry_version_yn", "boolean", "recommended", "Whether this is a registry/snapshot version.", "Use true/false."),
    field("source_version.tsv", "repository_version_yn", "boolean", "recommended", "Whether this is a repository dataset/package version.", "Use true/false."),
    field("source_version.tsv", "correction_or_update_type", "string", "optional", "Correction/update/retraction relationship type.", "Examples: correction, retraction, expression_of_concern, updated_registry."),
    field("source_version.tsv", "superseded_by_source_version_id", "string", "conditional", "Version that supersedes this version.", "Use when known."),
    field("source_version.tsv", "version_evidence_file_id", "string", "conditional", "Source file supporting version assertion.", "Foreign key to source_file.tsv when available."),
    field("source_version.tsv", "version_evidence_text", "string", "optional", "Text supporting version assertion.", "Use repository/publisher/version statement."),
    field("source_access_right.tsv", "access_right_id", "string", "required", "Stable access-right decision ID.", "One rights decision per source/file/scope."),
    field("source_access_right.tsv", "source_id", "string", "required", "Foreign key to source.tsv.", "The source whose rights are assessed."),
    field("source_access_right.tsv", "source_file_id", "string", "conditional", "Foreign key to source_file.tsv.", "Required when decision concerns mirrored bytes."),
    field("source_access_right.tsv", "rights_scope", "string", "required", "Scope of rights decision.", "Examples: metadata, source_file, local_mirror, text_extract, redistribute."),
    field("source_access_right.tsv", "license_name", "string", "optional", "License name.", "Use source-native name or SPDX when available."),
    field("source_access_right.tsv", "license_spdx", "string", "optional", "SPDX license identifier.", "Leave blank if unknown."),
    field("source_access_right.tsv", "license_url", "url", "optional", "License URL.", "Use repository/publisher/API license evidence."),
    field("source_access_right.tsv", "license_category", "category", "recommended", "Coarse license/access category.", "Use same vocabulary as access rows.", vocab("license_category"), "unknown"),
    field("source_access_right.tsv", "terms_url", "url", "optional", "Terms/TDM/policy URL.", "Use host/publisher/repository policy URL when known."),
    field("source_access_right.tsv", "tdm_policy_url", "url", "optional", "Text/data-mining policy URL.", "Use if separate from license/terms."),
    field("source_access_right.tsv", "robots_status", "string", "optional", "robots.txt/crawl status.", "Examples: allowed, disallowed, unknown, not_checked."),
    field("source_access_right.tsv", "mirror_allowed_yn", "boolean_or_unknown", "recommended", "Whether local mirroring is allowed.", "Use unknown until reviewed."),
    field("source_access_right.tsv", "text_extract_allowed_yn", "boolean_or_unknown", "recommended", "Whether text extraction is allowed.", "Use unknown until reviewed."),
    field("source_access_right.tsv", "redistribution_allowed_yn", "boolean_or_unknown", "recommended", "Whether artifact can be redistributed.", "Use false/internal-only for subscription/manual files."),
    field("source_access_right.tsv", "share_scope", "string", "optional", "Allowed sharing scope.", "Examples: public, internal_only, metadata_only, snippets_only."),
    field("source_access_right.tsv", "institutional_license_yn", "boolean", "recommended", "Whether access used institutional entitlement.", "Use false if not used or unknown in pilot.", example="false"),
    field("source_access_right.tsv", "reviewed_by", "string", "recommended", "Reviewer/tool for rights decision.", "Examples: codex, user, librarian."),
    field("source_access_right.tsv", "reviewed_at", "datetime", "recommended", "Review timestamp/date.", "Use batch timestamp for generated unknown decisions."),
    field("source_access_right.tsv", "rights_decision", "category", "required", "Rights/mirroring decision.", "Use needs_review rather than assuming open from a successful download.", vocab("rights_decision"), "needs_review"),
    field("source_access_right.tsv", "rights_decision_reason", "string", "recommended", "Reason for rights decision.", "State license evidence, internal-only rule, or unknown status."),
    field("source_identifier.tsv", "source_id", "string", "required", "Foreign key to source.tsv.", "Every identifier row must attach to one source."),
    field("source_identifier.tsv", "identifier_type", "category", "required", "Identifier system or URL type.", "Use the narrowest applicable identifier type.", vocab("identifier_type"), "doi"),
    field("source_identifier.tsv", "identifier_value", "string", "required", "Identifier value in source-native form.", "Normalize consistently but preserve enough to resolve it."),
    field("source_identifier.tsv", "identifier_url", "url", "conditional", "Resolver URL for identifier.", "Use DOI/registry/repository resolver URL where available."),
    field("source_identifier.tsv", "identifier_source", "string", "recommended", "Where this identifier was observed or resolved.", "Examples: source.tsv, Crossref, PubMed, OpenAlex, real_world_grounding_sample."),
    field("source_identifier.tsv", "is_primary", "boolean", "required", "Whether this is the preferred identifier for resolving the source.", "Use true for DOI/NCT/registry URL selected as primary grounding route; otherwise false."),
    field("source_identifier.tsv", "confidence", "category", "required", "Confidence that the identifier belongs to this source.", "High for exact metadata/registry values; medium/low for inferred matches.", vocab("confidence"), "high"),
    field("source_identifier.tsv", "notes", "string", "optional", "Identifier notes.", "Explain ambiguous identifiers or nonstandard formats."),
    field("source_classification.tsv", "source_id", "string", "required", "Foreign key to source.tsv.", "Classify the source, not a plot dot, unless the source is a dot-level internal row."),
    field("source_classification.tsv", "classification_type", "category", "required", "Kind of classification.", "Use separate rows for field, subfield, source_family, study_design, publication_type, and venue when needed.", vocab("classification_type"), "field"),
    field("source_classification.tsv", "classification_value", "string", "required", "Classification value.", "Use display-stable values such as Political science, Clinical medicine, SCORE/COS, survey experiment."),
    field("source_classification.tsv", "classification_source", "string", "required", "Source/process that assigned the classification.", "Examples: plot row field, source family catalog, manual coding, registry metadata."),
    field("source_classification.tsv", "classification_confidence", "category", "required", "Confidence in classification.", "Use high for source-provided categories, medium for inferred catalog categories, low for uncertain labels.", vocab("confidence"), "medium"),
    field("source_classification.tsv", "notes", "string", "optional", "Classification notes.", "Explain ambiguous or multi-field sources."),
    field("search_lead.tsv", "search_lead_id", "string", "required", "Stable unique search lead ID.", "Use deterministic IDs within a search track; do not recycle IDs."),
    field("search_lead.tsv", "plot_universe_id", "string", "recommended", "Plot universe or future plot context that motivated this lead.", "Use the YAML plot_universe ID when known; blank only for general catalog leads."),
    field("search_lead.tsv", "search_track_id", "string", "recommended", "Search track or plan row that produced this lead.", "Use provenance_search_plan.search_track_id or a stable equivalent."),
    field("search_lead.tsv", "lead_type", "category", "required", "Kind of lead discovered.", "Distinguish corpus/database leads from individual replication-paper leads before promotion.", vocab("search_lead_type"), "corpus_or_database"),
    field("search_lead.tsv", "lead_title", "string", "required", "Human-readable lead title.", "Use source/project/paper title or a concise descriptive handle."),
    field("search_lead.tsv", "lead_source_family", "string", "recommended", "Source-family label or project family.", "Examples: FReD, SCORE, Many Labs, individual_replication_paper."),
    field("search_lead.tsv", "lead_url", "url", "conditional", "Landing URL, DOI URL, repository URL, registry URL, or project URL for the lead.", "Prefer stable project/repository/article URLs over search result URLs."),
    field("search_lead.tsv", "lead_source_path", "path", "conditional", "Repo-relative path where the lead was found or staged.", "Use for local inventories, mirrored raw payloads, staged files, or manual PDFs."),
    field("search_lead.tsv", "query_or_seed", "string", "recommended", "Query, seed artifact, or manual search term that produced the lead.", "Keep exact enough to repeat the search."),
    field("search_lead.tsv", "discovered_by", "string", "recommended", "Tool/person/process that found the lead.", "Examples: codex, user, rg_local_repo, OSF API, Crossref."),
    field("search_lead.tsv", "discovered_at", "datetime", "recommended", "Discovery timestamp/date.", "Use ISO date/time or at least YYYY-MM-DD."),
    field("search_lead.tsv", "candidate_artifact_path_or_url", "string", "conditional", "File, page, dataset, package, or paper artifact to inspect next.", "May be URL or repo-relative path; promote to source/source_access after triage."),
    field("search_lead.tsv", "expected_result_count", "integer", "optional", "Expected number of result rows the lead may emit.", "Use rough count when available; blank if unknown."),
    field("search_lead.tsv", "expected_pair_count", "integer", "optional", "Expected number of original/replication pairs for replication leads.", "Use for Plot 1 source planning."),
    field("search_lead.tsv", "result_fields_available", "string", "recommended", "Known or suspected result fields available in the lead.", "Examples: D|N, native_effect|SE|N, original_d|replication_d|original_N|replication_N."),
    field("search_lead.tsv", "original_source_hint", "string", "conditional", "Original paper/study/source hint if the lead appears to involve a replication pair.", "For Plot 1, fill after a replication lead exposes or implies an original target."),
    field("search_lead.tsv", "replication_or_followup_source_hint", "string", "conditional", "Replication, reproduction, robustness, extension, or follow-up source hint.", "For individual replication-paper leads, this is usually the lead paper itself."),
    field("search_lead.tsv", "pair_relationship_basis", "string", "conditional", "Evidence that the lead contains or asserts an original/replication relationship.", "Use verbatim wording or field names where possible."),
    field("search_lead.tsv", "publication_link_hint", "string", "conditional", "Publication link or eventual-publication hint.", "Useful for Figure 2/3 and future contexts; not required for Figure 1."),
    field("search_lead.tsv", "triage_status", "category", "required", "Current search-lead status.", "Keep blocked/excluded/duplicate leads rather than deleting them.", vocab("search_lead_status"), "candidate_found"),
    field("search_lead.tsv", "lead_decision", "category", "required", "Current decision for this lead.", "Decide whether to promote, stage, catalog, reject, or send to manual review.", vocab("lead_decision"), "not_triaged"),
    field("search_lead.tsv", "decision_basis", "string", "recommended", "Why the lead decision was made.", "Cite fields, URLs, files, scope criteria, or blocker facts."),
    field("search_lead.tsv", "blocker_codes", "string", "conditional", "Pipe-delimited blockers if lead is not promotable now.", "Examples: access_blocked|missing_D_N|scope_mismatch|duplicate."),
    field("search_lead.tsv", "promoted_source_id", "string", "conditional", "Source ID created from this lead.", "Fill when the lead becomes a source.tsv row."),
    field("search_lead.tsv", "promoted_source_result_ids", "string", "conditional", "Pipe-delimited source_result IDs emitted from this lead.", "Fill when parser or manual extraction creates result rows."),
    field("search_lead.tsv", "next_action", "string", "recommended", "Next action needed for this lead.", "Examples: download_package, parse_workbook, resolve_original, manual_pdf_check, no_action."),
    field("search_lead.tsv", "notes", "string", "optional", "Lead-level notes.", "Keep concise; do not store final extraction evidence here."),
    field("source_result.tsv", "source_result_id", "string", "required", "Stable unique assertion/result ID.", "One extraction source asserting one result. Do not merge alternate sources here."),
    field("source_result.tsv", "canonical_result_id", "string", "recommended", "Foreign key to canonical_result.tsv.", "May be blank until resolution."),
    field("source_result.tsv", "extraction_source_id", "string", "required", "Source where literal extracted text/number came from.", "May be a database, paper, PDF, result CSV, or package output."),
    field("source_result.tsv", "represented_source_id", "string", "required", "Source/study/paper that the result is about.", "Same as extraction_source_id only when extracting directly from the represented work."),
    field("source_result.tsv", "access_id", "string", "required", "Foreign key to exact access route.", "Must point to retrievable bytes or documented barrier."),
    field("source_result.tsv", "source_locator", "string", "required", "Precise locator inside source.", "Use table/page/row/API JSON path/file member/script output; labels alone are insufficient."),
    field("source_result.tsv", "result_label", "string", "required", "Human label for the result/dot.", "Descriptive only; not evidence text."),
    field("source_result.tsv", "outcome_label", "string", "recommended", "Human outcome label.", "Descriptive only; not a substitute for verbatim outcome text."),
    field("source_result.tsv", "verbatim_source_row_text", "string", "required_for_promotion", "Source row/table/API text copied as directly as practical.", "This is the human-checkable evidence string; one-line TSV safe."),
    field("source_result.tsv", "verbatim_outcome_text", "string", "recommended", "Exact outcome text from source.", "Use source wording, not cleaned labels."),
    field("source_result.tsv", "verbatim_effect_text", "string", "required_for_d_or_native", "Exact effect/statistic text from source.", "Do not put D here unless source itself reports D."),
    field("source_result.tsv", "verbatim_se_text", "string", "conditional", "Exact SE text from source.", "Required when native SE is used."),
    field("source_result.tsv", "verbatim_n_text", "string", "required_for_promotion", "Exact N/sample-size text from source.", "Must identify whether respondent, arm, cluster, enrollment, or analytic N."),
    field("source_result.tsv", "verbatim_p_text", "string", "conditional", "Exact p/t/z/F text from source.", "Required if conversion uses a significance statistic."),
    field("source_result.tsv", "verbatim_ci_text", "string", "conditional", "Exact CI text from source.", "Required if conversion uses CI."),
    field("source_result.tsv", "native_effect_value", "number", "conditional", "Parsed native effect value.", "Parse without changing metric."),
    field("source_result.tsv", "native_effect_metric", "category", "conditional", "Metric of native_effect_value.", "Required when native effect is present.", vocab("native_effect_metric")),
    field("source_result.tsv", "native_standard_error", "number", "conditional", "Parsed native standard error.", "Do not back-calculate if source used adjusted/clustered models unless documented."),
    field("source_result.tsv", "native_ci_low", "number", "conditional", "Parsed native CI lower bound.", "Only if source reports CI."),
    field("source_result.tsv", "native_ci_high", "number", "conditional", "Parsed native CI upper bound.", "Only if source reports CI."),
    field("source_result.tsv", "native_p_value", "number_or_string", "conditional", "Parsed p-value, allowing inequalities.", "Preserve '<0.001' in verbatim field; clean numeric companion may be blank."),
    field("source_result.tsv", "native_n_total", "number", "required_for_promotion", "Parsed total N for the result.", "Use analytic N when clear; store respondent/cluster split separately."),
    field("source_result.tsv", "native_n_treatment", "number", "conditional", "Treatment-arm N.", "Required for event-count/log-OR conversions when available."),
    field("source_result.tsv", "native_n_control", "number", "conditional", "Control-arm N.", "Required for event-count/log-OR conversions when available."),
    field("source_result.tsv", "native_cluster_n", "number", "conditional", "Cluster count.", "Required for clustered designs when reported."),
    field("source_result.tsv", "unit_of_randomization", "string", "recommended", "Randomization unit.", "Examples: individual, village, school, paper, trial, precinct."),
    field("source_result.tsv", "unit_of_analysis", "string", "recommended", "Analysis/sample unit.", "Examples: respondent, cluster, trial arm, claim, paper."),
    field("source_result.tsv", "standardized_effect_value", "number", "conditional", "Final standardized effect for D-axis or proxy.", "Blank for native-only rows."),
    field("source_result.tsv", "standardized_effect_metric", "category", "conditional", "Metric for standardized_effect_value.", "Use native_only when not D-promotable.", vocab("standardized_effect_metric")),
    field("source_result.tsv", "standardized_n", "number", "required_for_plot", "N used for plotting/statistics.", "Must explain cluster-vs-respondent choice in transformation_explanation."),
    field("source_result.tsv", "d", "number", "conditional", "Cohen's d or D-axis value.", "Only populate when conversion is defensible."),
    field("source_result.tsv", "d_conversion_method", "category", "required_for_promotion", "Method used to get D or reason no D exists.", "Do not force linear-probability ATEs to d without baseline/SD/event counts.", vocab("d_conversion_method")),
    field("source_result.tsv", "d_conversion_inputs", "string", "conditional", "Inputs used for D conversion.", "List formulas and source fields, e.g. logOR=-0.4; d=logOR*sqrt(3)/pi."),
    field("source_result.tsv", "transformation_explanation", "string", "required_for_promotion", "Plain-language explanation from verbatim/native fields to final D/N/native panel row.", "Must be enough for a human to recalculate."),
    field("source_result.tsv", "transformation_confidence", "category", "required_for_promotion", "Confidence in transformation.", "High only when source fields and formula are explicit.", vocab("confidence")),
    field("source_result.tsv", "prereg_status", "category", "conditional", "Pre-registration status for confirmatory panels.", "Required for preregistered plots.", vocab("prereg_status")),
    field("source_result.tsv", "prereg_mapping_id", "string", "conditional", "Mapping row that links the represented study/result to its preregistration, registry record, PAP, MPAP, or registered-report protocol.", "Required for preregistered panels when a prereg/PAP relationship exists. Use source_source_mapping.mapping_id.", example="map_aearctr_0000685_pap_to_good_politicians"),
    field("source_result.tsv", "prereg_source_id", "string", "conditional", "Source ID of the preregistration/PAP/registered-report protocol used for this result.", "Use the source that actually contains or asserts the preregistered selector."),
    field("source_result.tsv", "prereg_url", "url", "conditional", "Direct URL to preregistration/PAP/registered-report protocol.", "Prefer registry/PAP URL over a general article page."),
    field("source_result.tsv", "prereg_registered_at", "date_or_datetime", "conditional", "Registration, PAP filing, or Stage-1 acceptance date/time.", "Use ISO date/time when available; leave blank and add a problem if prereg timing is claimed but not dated."),
    field("source_result.tsv", "prereg_timing", "category", "conditional", "Timing of the prereg/PAP relative to data/results.", "Must be specific, not just yes/no.", vocab("relationship_timing"), "pre_analysis"),
    field("source_result.tsv", "prereg_selector_locator", "string", "conditional", "Locator of the preregistered hypothesis/outcome/analysis rule.", "Examples: PAP p. 4 H1; registry primary_outcomes[2]; OSF file PAP.pdf section 2.1."),
    field("source_result.tsv", "prereg_selector_verbatim_text", "string", "conditional", "Verbatim preregistered selector text for the outcome/hypothesis/analysis rule.", "Required when a row is selected because it was preregistered. Do not summarize only."),
    field("source_result.tsv", "prereg_hypothesis_id", "string", "optional", "Preregistered hypothesis ID or label.", "Examples: H1a, Primary Outcome 1, MPAP family vote_choice."),
    field("source_result.tsv", "prereg_outcome_id", "string", "optional", "Preregistered outcome ID or label.", "Use source-native ID if present."),
    field("source_result.tsv", "selector_status", "category", "conditional", "How focal result was selected.", "Required for paper-level/corpus-level rows.", vocab("selector_status")),
    field("source_result.tsv", "selector_rule", "string", "conditional", "Rule used to pick/collapse this result from eligible results.", "Examples: PAP primary outcome; median across preregistered primary outcomes; first confirmatory result; database primary outcome."),
    field("source_result.tsv", "selector_mapping_id", "string", "optional", "Mapping row that supports the focal-result selector when separate from prereg_mapping_id.", "Use when a corpus/database identifies a focal claim or when a paper maps PAP outcomes to final tables."),
    field("source_result.tsv", "replication_mapping_id", "string", "conditional", "Mapping row that links this result/source to an original, replication, computational reproduction, or robustness target.", "Use source_source_mapping.mapping_id; required when replication status is asserted."),
    field("source_result.tsv", "replication_role", "category", "conditional", "Role of this result in a replication/reproduction relationship.", "Do not use a boolean; specify whether this is original, replication, reproduction, robustness check, or corpus assertion.", vocab("replication_role"), "replication_study"),
    field("source_result.tsv", "replication_pair_id", "string", "conditional", "Stable ID joining original and replication results/papers.", "Required when original and replication dots are paired or compared."),
    field("source_result.tsv", "replication_kind", "category", "conditional", "Kind of replication/reproduction relationship.", "Use the same controlled vocabulary as source_source_mapping.relationship_subtype.", vocab("relationship_subtype"), "direct_replication"),
    field("source_result.tsv", "replication_target_claim", "string", "conditional", "Claim, hypothesis, or result that the replication/reproduction targets.", "Copy or closely preserve source wording where available."),
    field("source_result.tsv", "source_mapping_ids", "string", "optional", "Pipe-delimited source_source_mapping IDs relevant to this result.", "Use for corpus membership, database-result mapping, paper-package support, preregistration, replication, and publication links."),
    field("source_result.tsv", "extraction_confidence", "category", "required", "Confidence in extraction from source.", "Low if PDF/table parse is uncertain.", vocab("confidence")),
    field("source_result.tsv", "human_check_status", "category", "required", "Human-check readiness.", "Must not call source cells recovered unless verbatim source evidence is present.", vocab("human_check_status")),
    field("source_result.tsv", "coding_status", "category", "required", "Current row disposition.", "Rows can be staged or blocked without being plotted.", vocab("coding_status")),
    field("source_result.tsv", "evidence_level", "integer", "required", "Numeric provenance/evidence level from 0 to 7.", "0 blocks the row; public plots should require at least 3; publication-grade paper claims should usually require at least 5.", example="3"),
    field("source_result.tsv", "evidence_level_name", "category", "required", "Named provenance/evidence level.", "Use the seven-level ladder; do not treat corpus assertions as original-source extraction.", vocab("evidence_level_name"), "external_assertion_with_target_source"),
    field("source_result.tsv", "target_acquisition_state", "category", "recommended", "State of target identity/location/mirroring/acquisition.", "Located is not mirrored; mirrored is not verified.", vocab("target_acquisition_state"), "target_located"),
    field("source_result.tsv", "value_verification_state", "category", "recommended", "State of D/N or native value verification against source objects.", "Use corpus_assertion_only until original source text/data are checked.", vocab("value_verification_state"), "corpus_assertion_only"),
    field("source_result.tsv", "source_is_original", "boolean", "required", "Whether the extraction source is the original paper/registry/API/table for the represented result.", "False for corpus/database assertions about another paper.", example="false"),
    field("source_result.tsv", "number_verified_by_us", "boolean", "required", "Whether we directly verified/copied or recomputed the plotted number from original/authoritative source text/output.", "False when taking an external corpus's word for the represented paper's number.", example="false"),
    field("source_result.tsv", "represented_work_identified", "boolean", "required", "Whether the represented paper/trial/study has a durable identifier or high-confidence resolved source.", "True for DOI, PMID, PMCID, NCT, AEA/RIDIE/EGAP ID, Dataverse DOI, or high-confidence Crossref resolution.", example="true"),
    field("source_result.tsv", "source_is_external", "boolean", "required", "Whether the extraction source is an external real-world source rather than only our internal derived file.", "True for mirrored corpus/database/registry/paper/package sources; false for internal-only derived tables.", example="true"),
    field("source_result.tsv", "requires_manual_review", "boolean", "required", "Whether the row still needs human review before final promotion.", "True for low-confidence Crossref, source gaps, unresolved represented work, or unverified original-source numbers.", example="true"),
    field("source_result.tsv", "conversion_verified", "boolean", "required", "Whether the native-to-D/native transformation has been verified against source inputs.", "False if D is a proxy or inherited from corpus without original-source recalculation.", example="false"),
    field("source_result.tsv", "citation_status", "category", "required", "Citation status for this source-result row.", "Use real_citation for real source bibliography; generated_internal is only an audit placeholder.", vocab("citation_status"), "real_citation"),
    field("source_result.tsv", "source_citation_key", "string", "conditional", "Citation key for extraction source.", "May cite a corpus/database/package."),
    field("source_result.tsv", "represented_source_citation_key", "string", "conditional", "Citation key for represented work.", "Required when known. Do not use generated dot keys."),
    field("source_result.tsv", "represented_source_citation_rendered", "string", "conditional", "Rendered citation for represented source.", "Store as TSV text for spreadsheet checking."),
    field("source_result.tsv", "generated_result_citation_key", "string", "optional", "Internal generated citation key for the dot/result row.", "Internal audit only; not bibliographic evidence."),
    field("source_result.tsv", "generated_result_citation_rendered", "string", "optional", "Rendered internal generated result citation.", "Must be labeled synthetic if present."),
    field("source_result.tsv", "notes", "string", "optional", "Concise row notes.", "Do not hide missing fields here; add extraction_problem rows."),
    field("canonical_result.tsv", "canonical_result_id", "string", "required", "Stable unique canonical result ID.", "Maps one or more source_result rows to one plotted/staged result."),
    field("canonical_result.tsv", "represented_source_id", "string", "required", "Foreign key to represented source.", "Usually the paper/study/trial."),
    field("canonical_result.tsv", "preferred_source_result_id", "string", "required", "Chosen source-result row.", "Must be one of the child source_result IDs."),
    field("canonical_result.tsv", "result_label", "string", "required", "Canonical result label.", "Keep brief and human-readable."),
    field("canonical_result.tsv", "D", "number", "conditional", "D-axis value used in plot.", "Blank for native-only canonical rows."),
    field("canonical_result.tsv", "N", "number", "required_for_plot", "N used in plot/statistics.", "Should match standardized_n in preferred source_result or aggregation rule."),
    field("canonical_result.tsv", "effect_metric_for_plot", "string", "required", "Metric shown by plotted/staged row.", "Examples: d, native_ate, log_or, risk_difference."),
    field("canonical_result.tsv", "panel", "string", "required", "Destination panel/plot.", "Examples: d_axis, native_panel, plot1, plot2, plot3, plot4."),
    field("canonical_result.tsv", "row_unit", "string", "required", "Unit represented by canonical row.", "Examples: paper, project, trial, result, pooled_round, component_study."),
    field("canonical_result.tsv", "source_result_count", "integer", "required", "Number of source-result rows represented.", "Use to expose collapsed thousand-row corpora."),
    field("canonical_result.tsv", "aggregation_rule", "string", "required", "How source-result rows were selected/collapsed.", "Examples: single row, median across planned primaries, paper median, preferred direct source."),
    field("canonical_result.tsv", "D_min", "number", "conditional", "Minimum D among children.", "Required for multi-result paper/project summaries when D exists."),
    field("canonical_result.tsv", "D_median", "number", "conditional", "Median D among children.", "Required for multi-result paper/project summaries when D exists."),
    field("canonical_result.tsv", "D_max", "number", "conditional", "Maximum D among children.", "Required for multi-result paper/project summaries when D exists."),
    field("canonical_result.tsv", "N_min", "number", "conditional", "Minimum N among children.", "Required for multi-result summaries."),
    field("canonical_result.tsv", "N_median", "number", "conditional", "Median N among children.", "Required for multi-result summaries."),
    field("canonical_result.tsv", "N_max", "number", "conditional", "Maximum N among children.", "Required for multi-result summaries."),
    field("canonical_result.tsv", "resolution_status", "category", "required", "Deduplication/resolution status.", "Do not silently plot unresolved duplicates.", vocab("resolution_status")),
    field("canonical_result.tsv", "resolution_notes", "string", "recommended", "Why this source/result was preferred or how collapse was done.", "Required for source_result_count > 1."),
    field("canonical_result_membership.tsv", "canonical_result_id", "string", "required", "Foreign key to canonical_result.tsv.", "Every membership row belongs to one canonical result."),
    field("canonical_result_membership.tsv", "source_result_id", "string", "required", "Foreign key to source_result.tsv.", "Every child/member must be an explicit source_result row."),
    field("canonical_result_membership.tsv", "membership_role", "category", "required", "Role of the source-result in the canonical result.", "Use preferred for the preferred direct source, child for included child rows, excluded_child for rejected candidates, duplicate for duplicates, sensitivity_only for sensitivity rows.", vocab("membership_role"), "preferred"),
    field("canonical_result_membership.tsv", "included_in_collapse", "boolean", "required", "Whether this source-result contributed to min/median/max/preferred collapse.", "Use false for duplicate, excluded, or sensitivity-only rows."),
    field("canonical_result_membership.tsv", "included_in_statistics", "boolean", "required", "Whether this source-result contributes to reported statistics.", "Usually false when canonical_result itself is the plotted/statistical unit."),
    field("canonical_result_membership.tsv", "aggregation_role", "string", "recommended", "Role in aggregation rule.", "Examples: median_child, min_child, max_child, preferred_source, source_assertion_only."),
    field("canonical_result_membership.tsv", "weight", "number", "optional", "Weight used in aggregation, if any.", "Leave blank for unweighted median/preferred-source decisions."),
    field("canonical_result_membership.tsv", "notes", "string", "optional", "Membership notes.", "Explain exclusions, duplicate handling, or child-row provenance gaps."),
    field("source_result_support.tsv", "source_result_id", "string", "required", "Foreign key to source_result.tsv.", "The result row being supported."),
    field("source_result_support.tsv", "source_id", "string", "required", "Foreign key to source.tsv.", "The source object providing support."),
    field("source_result_support.tsv", "access_id", "string", "conditional", "Foreign key to source_access.tsv.", "Required when support is tied to a specific file/API/page route."),
    field("source_result_support.tsv", "source_file_id", "string", "conditional", "Foreign key to source_file.tsv.", "Use when support is tied to a mirrored artifact/file."),
    field("source_result_support.tsv", "support_role", "category", "required", "What the support object provides.", "Use effect_text, n_text, selector_text, conversion_input, raw_data, code, relationship_evidence, etc.", vocab("support_role"), "effect_text"),
    field("source_result_support.tsv", "support_locator", "string", "conditional", "Locator inside the support source.", "Use table/page/row/API path/script output locator."),
    field("source_result_support.tsv", "support_locator_type", "string", "optional", "Type of locator.", "Examples: csv_row, json_path, pdf_page, table_cell, xpath, script_output, plot_row."),
    field("source_result_support.tsv", "page_number", "integer", "optional", "Page number for PDF/page artifacts.", "Use 1-indexed page when available."),
    field("source_result_support.tsv", "section_heading", "string", "optional", "Section heading near support text.", "Use Methods, Results, Appendix, etc. when available."),
    field("source_result_support.tsv", "table_number", "string", "optional", "Table identifier.", "Examples: Table 1, Appendix Table S3."),
    field("source_result_support.tsv", "figure_number", "string", "optional", "Figure identifier.", "Examples: Figure 2, Fig. S1."),
    field("source_result_support.tsv", "cell_locator", "string", "optional", "Cell/row/column locator inside table or dataset.", "Use row id, column name, sheet name, or API field path."),
    field("source_result_support.tsv", "char_start", "integer", "optional", "Character start offset in extracted text.", "Populate after text extraction."),
    field("source_result_support.tsv", "char_end", "integer", "optional", "Character end offset in extracted text.", "Populate after text extraction."),
    field("source_result_support.tsv", "xml_xpath", "string", "optional", "XML XPath for support.", "Use for JATS/PMC/XML artifacts."),
    field("source_result_support.tsv", "html_css_selector", "string", "optional", "HTML CSS selector for support.", "Use for full HTML/landing page artifacts."),
    field("source_result_support.tsv", "pdf_bbox", "string", "optional", "PDF bounding box for support.", "Use compact JSON or x0,y0,x1,y1,page."),
    field("source_result_support.tsv", "support_verbatim_text", "string", "conditional", "Copied support text from this source.", "Required when the support role is effect_text, n_text, selector_text, conversion_input, or relationship_evidence and text is available."),
    field("source_result_support.tsv", "verbatim_snippet_hash", "string", "optional", "Hash of support_verbatim_text.", "Useful for long-term fixity without relying on display text."),
    field("source_result_support.tsv", "copied_text_allowed_yn", "boolean_or_unknown", "recommended", "Whether the copied support text can be shared.", "Use unknown for pilot rows and restricted sources."),
    field("source_result_support.tsv", "support_confidence", "category", "required", "Confidence in this support relationship.", "Use high only when the support text/locator is explicit.", vocab("confidence"), "medium"),
    field("source_result_support.tsv", "notes", "string", "optional", "Support notes.", "Explain why this object supports the result or why text is unavailable."),
    field("plot_universe.tsv", "plot_universe_id", "string", "required", "Stable plot universe/context ID.", "Use IDs from PROVENANCE_PIPELINE_SINGLE_SOURCE_OF_TRUTH.yml."),
    field("plot_universe.tsv", "figure_label", "string", "recommended", "Figure, panel, diagnostic, or future plot label.", "Examples: Figure 1, Figure 2, diagnostic_all_source_dn."),
    field("plot_universe.tsv", "current_scope_role", "category", "recommended", "Role of this universe in the current project scope.", "Distinguish current figures from catalog-only future seeds.", vocab("plot_scope_role"), "current_figure"),
    field("plot_universe.tsv", "result_target_kind", "string", "required", "Kind of result target this universe evaluates.", "Examples: replication_pair, paper_result, preregistered_result, diagnostic_source_result."),
    field("plot_universe.tsv", "publication_requirement", "string", "recommended", "Publication requirement for this universe.", "Examples: not_required, required_eventually_published, mixed_or_not_universal."),
    field("plot_universe.tsv", "output_unit", "string", "required", "Unit emitted by this plot universe.", "Examples: one original/replication pair, one paper-level D/N result."),
    field("plot_universe.tsv", "criteria_version", "string", "recommended", "Version or date of the criteria snapshot.", "Use YAML schema_version/date or a build-specific criteria version."),
    field("plot_universe.tsv", "universe_definition_source", "string", "recommended", "Where the definition came from.", "Usually PROVENANCE_PIPELINE_SINGLE_SOURCE_OF_TRUTH.yml."),
    field("plot_universe.tsv", "active_yn", "boolean", "recommended", "Whether this universe is active in the current build.", "Use false for future plots or deprecated contexts.", example="true"),
    field("plot_universe.tsv", "notes", "string", "optional", "Universe-level notes.", "Keep row-specific decisions in plot_membership.tsv."),
    field("plot_criterion.tsv", "criterion_id", "string", "required", "Stable reusable criterion ID.", "Use IDs from PROVENANCE_PIPELINE_SINGLE_SOURCE_OF_TRUTH.yml."),
    field("plot_criterion.tsv", "criterion_label", "string", "recommended", "Short human-readable criterion label.", "Use a concise display name."),
    field("plot_criterion.tsv", "gate_type", "string", "required", "Criterion gate type.", "Examples: include_if_true, exclude_if_true, required_context."),
    field("plot_criterion.tsv", "applies_to_grain", "string", "recommended", "The grain this criterion evaluates.", "Examples: search_lead, source, source_result, canonical_result, represented_result, plot_membership."),
    field("plot_criterion.tsv", "rule_text", "string", "required", "Plain-language criterion rule.", "Copy from YAML so the table snapshot is understandable without code."),
    field("plot_criterion.tsv", "accept_if", "string", "conditional", "Pipe-delimited or compact text acceptance examples.", "Use for nontrivial include criteria."),
    field("plot_criterion.tsv", "reject_if", "string", "conditional", "Pipe-delimited or compact text rejection examples.", "Use for nontrivial exclusion criteria."),
    field("plot_criterion.tsv", "evidence_fields", "string", "recommended", "Pipe-delimited evidence fields used by this criterion.", "Keep in sync with source/source_result/plot_membership fields where possible."),
    field("plot_criterion.tsv", "reusable_in_plot_universe_ids", "string", "optional", "Pipe-delimited plot universes where this criterion can be reused.", "Future plots can reuse criteria without rewriting source/result rows."),
    field("plot_criterion.tsv", "status", "string", "recommended", "Criterion status.", "Examples: active, draft, deprecated."),
    field("plot_membership.tsv", "plot_id", "string", "required", "Stable plot or statistic-set ID.", "Examples: plot1_replication, plot2_published, plot3_preregistered, plot4_all_sources, diagnostic_level5."),
    field("plot_membership.tsv", "plot_universe_id", "string", "recommended", "Plot universe/context used to evaluate this canonical result.", "Use the YAML plot_universe ID; one plot_id may have multiple statistic or sensitivity contexts."),
    field("plot_membership.tsv", "canonical_result_id", "string", "required", "Foreign key to canonical_result.tsv.", "The canonical result being plotted, staged, or excluded."),
    field("plot_membership.tsv", "criteria_version", "string", "recommended", "Criteria version used for this decision.", "Required for reproducible future plots and sensitivity analyses."),
    field("plot_membership.tsv", "decision_context_type", "category", "recommended", "Kind of context that made this decision.", "Distinguish current plots, diagnostics, sensitivity views, future drafts, manual reviews, and automated rules.", vocab("decision_context_type"), "current_plot"),
    field("plot_membership.tsv", "eligibility_status", "category", "recommended", "Overall eligibility decision under this plot universe.", "Use included/excluded/catalog_only/diagnostic_only/sensitivity_only/pending/blocked.", vocab("eligibility_status"), "included"),
    field("plot_membership.tsv", "included_in_plot", "boolean", "required", "Whether this canonical result is shown in the plot.", "Use false for explicit exclusions or statistics-only memberships."),
    field("plot_membership.tsv", "included_in_statistics", "boolean", "required", "Whether this canonical result contributes to plot summary statistics.", "Use false for visual-only, excluded, or diagnostic-only points."),
    field("plot_membership.tsv", "passed_criteria_ids", "string", "recommended", "Pipe-delimited criteria passed by this canonical result.", "Use criterion IDs from plot_criterion/YAML."),
    field("plot_membership.tsv", "failed_criteria_ids", "string", "conditional", "Pipe-delimited criteria failed by this canonical result.", "Required when included_in_plot or included_in_statistics is false due to criteria failure."),
    field("plot_membership.tsv", "caveat_criteria_ids", "string", "optional", "Pipe-delimited criteria allowed only with caveat.", "Use for sensitivity or diagnostic contexts."),
    field("plot_membership.tsv", "decision_basis", "string", "recommended", "Plain-language basis for membership decision.", "Summarize the decisive criteria and source fields."),
    field("plot_membership.tsv", "decision_source", "string", "recommended", "Script, YAML, manual review, or artifact that made the decision.", "Examples: build_codebook_pilot_sample.py, PROVENANCE_PIPELINE_SINGLE_SOURCE_OF_TRUTH.yml."),
    field("plot_membership.tsv", "decided_at", "datetime", "recommended", "Decision timestamp/date.", "Use build date when exact timestamp is unavailable."),
    field("plot_membership.tsv", "plot_field", "string", "recommended", "Field/category displayed in the plot legend or grouping.", "Examples: Clinical medicine, Psychology/health, Political science."),
    field("plot_membership.tsv", "plot_source_family", "string", "recommended", "Source-family label displayed or used for grouping.", "Examples: ClinicalTrials.gov, SCORE/COS, EGAP Metaketa."),
    field("plot_membership.tsv", "render_order_group_count", "integer", "optional", "Group count used for draw order.", "Use to plot high-count groups first and smaller-count groups later/on top."),
    field("plot_membership.tsv", "style_group", "string", "optional", "Visual style group.", "Use for color/shape/alpha decisions when relevant."),
    field("plot_membership.tsv", "exclusion_reason", "string", "conditional", "Reason this canonical result is not included.", "Required when included_in_plot=false or included_in_statistics=false for a non-obvious reason."),
    field("plot_membership.tsv", "notes", "string", "optional", "Plot membership notes.", "Keep plot-only decisions out of source_result provenance."),
    field("source_source_mapping.tsv", "mapping_id", "string", "required", "Stable relationship ID.", "One directed relationship per row."),
    field("source_source_mapping.tsv", "from_source_id", "string", "required", "Source ID for parent/asserting/deriving source.", "Must match source.tsv."),
    field("source_source_mapping.tsv", "to_source_id", "string", "required", "Source ID for child/represented/derived-from source.", "Must match source.tsv."),
    field("source_source_mapping.tsv", "relationship_type", "category", "required", "Relationship between sources.", "Use controlled vocabulary.", vocab("relationship_type")),
    field("source_source_mapping.tsv", "relationship_subtype", "category", "recommended", "Specific relationship subtype.", "Use this to distinguish direct replication, conceptual replication, PAP, MPAP, registered report protocol, corpus child paper, package support, etc.", vocab("relationship_subtype"), "pre_analysis_plan"),
    field("source_source_mapping.tsv", "mapping_assertion_source_id", "string", "conditional", "Source that asserts or documents this relationship.", "Can equal from_source_id, but do not assume. Example: a corpus asserts Paper B reports Paper A; a registry page links final publication."),
    field("source_source_mapping.tsv", "mapping_assertion_access_id", "string", "conditional", "Access row for the file/page/API response where this relationship was observed.", "Use source_access.access_id when available."),
    field("source_source_mapping.tsv", "mapping_assertion_locator", "string", "conditional", "Locator inside the assertion source.", "Examples: CSV row ID, registry field paper_url, PAP p. 3, OSF file list, article footnote."),
    field("source_source_mapping.tsv", "mapping_assertion_url", "url", "conditional", "Most direct URL documenting the relationship.", "Use direct registry, DOI, OSF, Dataverse, package, corpus row, or article URL."),
    field("source_source_mapping.tsv", "mapping_assertion_verbatim_text", "string", "conditional", "Verbatim text/field that asserts the relationship.", "Required when the relation is not obvious from source IDs alone; one-line TSV-safe."),
    field("source_source_mapping.tsv", "mapping_evidence_type", "category", "recommended", "Type of evidence used to assert the mapping.", "Prefer verbatim_text or metadata_field over manual_judgment when possible.", vocab("mapping_evidence_type"), "metadata_field"),
    field("source_source_mapping.tsv", "external_relationship_id", "string", "optional", "External ID for the relationship.", "Examples: AEARCTR-0000685, NCT ID, OSF registration GUID, SCORE claim ID, Metaketa project ID."),
    field("source_source_mapping.tsv", "external_relationship_url", "url", "optional", "External URL for the relationship or mapping record.", "Use when different from mapping_assertion_url."),
    field("source_source_mapping.tsv", "relationship_date", "date_or_datetime", "optional", "Primary relationship date.", "For preregistration this is filing/registration date; for replication this can be replication publication/registration date."),
    field("source_source_mapping.tsv", "relationship_updated_at", "date_or_datetime", "optional", "Update, amendment, or version date.", "Use for registry updates, PAP amendments, OSF version timestamps, package versions."),
    field("source_source_mapping.tsv", "relationship_timing", "category", "conditional", "Timing of this relationship relative to data collection/analysis/results.", "Required for preregistration and registered-report mappings.", vocab("relationship_timing"), "pre_data_collection"),
    field("source_source_mapping.tsv", "prereg_registry_name", "string", "conditional", "Registry or preregistration platform name.", "Examples: AEA RCT Registry, EGAP, OSF Registries, ClinicalTrials.gov, RIDIE."),
    field("source_source_mapping.tsv", "prereg_registration_id", "string", "conditional", "Registry/PAP/registered-report identifier.", "Examples: AEARCTR-0000685, EGAP registration/736, NCT02818036, OSF GUID."),
    field("source_source_mapping.tsv", "prereg_document_type", "category_or_string", "conditional", "Specific preregistration document type.", "Examples: registry_metadata, PAP, MPAP, Stage 1 registered report, protocol, amendment."),
    field("source_source_mapping.tsv", "prereg_primary_outcome_text", "string", "conditional", "Verbatim primary outcome/family text from preregistration/PAP.", "Use when the mapping supports a focal selector."),
    field("source_source_mapping.tsv", "prereg_hypothesis_text", "string", "conditional", "Verbatim hypothesis text from preregistration/PAP.", "Use when available; do not replace with article wording."),
    field("source_source_mapping.tsv", "replication_kind", "category", "conditional", "Specific replication/reproduction type.", "Required when relationship_type is replication_of, computational_reproduction_of, or robustness_reanalysis_of.", vocab("relationship_subtype"), "direct_replication"),
    field("source_source_mapping.tsv", "replication_target_claim", "string", "conditional", "Claim/result/hypothesis being replicated or reproduced.", "Copy source wording when available."),
    field("source_source_mapping.tsv", "replication_original_result_id", "string", "optional", "Original source_result_id targeted by the replication.", "Fill when original result row exists in source_result.tsv."),
    field("source_source_mapping.tsv", "replication_replicating_result_id", "string", "optional", "Replication/reproduction source_result_id.", "Fill when replication result row exists in source_result.tsv."),
    field("source_source_mapping.tsv", "replication_outcome_match", "string", "conditional", "How closely the replication outcome matches the original.", "Examples: identical measure, same construct, different operationalization, unknown."),
    field("source_source_mapping.tsv", "replication_sample_relation", "string", "conditional", "How replication sample relates to original.", "Examples: independent sample, same data recomputed, subset, extension sample, unknown."),
    field("source_source_mapping.tsv", "replication_design_relation", "string", "conditional", "How replication design relates to original.", "Examples: same design, close protocol, conceptual extension, computational rerun, robustness specification."),
    field("source_source_mapping.tsv", "collection_role", "string", "optional", "Role in a corpus/collection mapping.", "Examples: parent corpus, child paper, child result, pooled round, component study."),
    field("source_source_mapping.tsv", "dedupe_group_id", "string", "optional", "Group ID for sources/results that should not be double-counted together.", "Use for pooled/component Metaketa rows, corpus-child rows, and original/replication pair families."),
    field("source_source_mapping.tsv", "relationship_confidence", "category", "required", "Confidence in relationship.", "Use blocked only when relation is suspected but unverified.", vocab("confidence")),
    field("source_source_mapping.tsv", "notes", "string", "optional", "Relationship notes.", "Keep concise."),
    field("extraction_event.tsv", "event_id", "string", "required", "Stable event ID.", "One extraction/retrieval/check action."),
    field("extraction_event.tsv", "source_result_id", "string", "conditional", "Source-result affected by event.", "Blank only for source-level access events."),
    field("extraction_event.tsv", "access_id", "string", "conditional", "Access row involved.", "Required for download/mirror events."),
    field("extraction_event.tsv", "event_step", "string", "required", "Step name.", "Examples: download, unzip, parse_table, run_script, manual_pdf_check, blocked_login."),
    field("extraction_event.tsv", "timestamp", "datetime", "recommended", "ISO timestamp/date.", "At least YYYY-MM-DD."),
    field("extraction_event.tsv", "performed_by", "string", "recommended", "Actor/tool.", "Examples: codex, user, script name."),
    field("extraction_event.tsv", "command_or_tool", "string", "conditional", "Command, script, API client, or manual action.", "Include enough to repeat when practical."),
    field("extraction_event.tsv", "path", "path", "conditional", "Path touched by event.", "Repo-relative where possible."),
    field("extraction_event.tsv", "path_exists", "boolean", "recommended", "Whether path existed at check time.", "Use true/false."),
    field("extraction_event.tsv", "file_size_bytes", "integer", "conditional", "File size after event.", "Required for downloaded/mirrored files."),
    field("extraction_event.tsv", "file_sha256", "string", "conditional", "Checksum after event.", "Required for downloaded/mirrored files."),
    field("extraction_event.tsv", "status", "string", "required", "Outcome of event.", "Examples: found, downloaded, parsed, failed, blocked."),
    field("extraction_event.tsv", "match_method", "string", "conditional", "How a source row was matched.", "Examples: DOI exact, NCT_ID + outcome title, title + D/N."),
    field("extraction_event.tsv", "notes", "string", "optional", "Event details.", "For failures, state exact blocker."),
    field("extraction_problem.tsv", "problem_id", "string", "required", "Stable problem ID.", "One problem per row."),
    field("extraction_problem.tsv", "source_result_id", "string", "conditional", "Affected source-result row.", "Blank only for source-level problems."),
    field("extraction_problem.tsv", "table_name", "string", "recommended", "Table containing problem.", "Use codebook table name."),
    field("extraction_problem.tsv", "column_name", "string", "conditional", "Column containing problem.", "Use when field-specific."),
    field("extraction_problem.tsv", "problem_code", "category", "required", "Machine-actionable problem code.", "Use controlled vocabulary.", vocab("problem_code")),
    field("extraction_problem.tsv", "severity", "category", "required", "Severity.", "High blocks promotion.", vocab("severity")),
    field("extraction_problem.tsv", "detail", "string", "required", "Human-readable issue.", "State what is missing or ambiguous."),
    field("extraction_problem.tsv", "suggested_rework", "string", "recommended", "How to fix.", "Give URL/path/action if known."),
    field("extraction_problem.tsv", "resolved", "boolean", "required", "Whether problem is resolved.", "Use false until fixed."),
    field("extraction_problem.tsv", "resolved_by", "string", "conditional", "Who resolved it.", "Required if resolved=true."),
    field("extraction_problem.tsv", "resolved_at", "datetime", "conditional", "Resolution date/time.", "Required if resolved=true."),
    field("manual_acquisition_task.tsv", "manual_task_id", "string", "required", "Stable manual task ID.", "One row per human acquisition/review task."),
    field("manual_acquisition_task.tsv", "source_result_id", "string", "conditional", "Source-result needing manual work.", "Blank only for source-level tasks."),
    field("manual_acquisition_task.tsv", "canonical_result_id", "string", "conditional", "Canonical result affected by task.", "Use when task affects a plotted/statistical dot."),
    field("manual_acquisition_task.tsv", "represented_source_id", "string", "conditional", "Represented source requiring acquisition.", "Use source_result.represented_source_id when available."),
    field("manual_acquisition_task.tsv", "extraction_source_id", "string", "conditional", "Current extraction source.", "Use source_result.extraction_source_id when relevant."),
    field("manual_acquisition_task.tsv", "needed_artifact_type", "category", "required", "Artifact/review type needed.", "Use the narrowest missing item.", vocab("needed_artifact_type"), "original_source_object"),
    field("manual_acquisition_task.tsv", "needed_value_fields", "string", "recommended", "Fields needed from manual work.", "Examples: effect_text|n_text|source_object|license_review."),
    field("manual_acquisition_task.tsv", "priority_score", "number", "recommended", "Priority score for manual queue.", "Higher means more useful/tractable."),
    field("manual_acquisition_task.tsv", "priority_reason", "string", "recommended", "Why this task has this priority.", "Use evidence level, plot membership, identifiers, and likely upgrade value."),
    field("manual_acquisition_task.tsv", "failed_route_summary", "string", "recommended", "Summary of automated routes already tried.", "Use source_access_attempt decisions and extraction problems."),
    field("manual_acquisition_task.tsv", "best_candidate_urls", "string", "conditional", "Candidate URLs for human to try.", "Pipe-delimit DOI/registry/repository/publisher URLs."),
    field("manual_acquisition_task.tsv", "acceptable_manual_routes", "string", "recommended", "Allowed manual routes.", "Examples: library access, repository request, author manuscript search, PDF parse."),
    field("manual_acquisition_task.tsv", "library_access_needed_yn", "boolean", "recommended", "Whether library/institutional access may be needed.", "Use true/false/unknown when possible."),
    field("manual_acquisition_task.tsv", "ill_needed_yn", "boolean", "recommended", "Whether interlibrary loan may be needed.", "Use true/false."),
    field("manual_acquisition_task.tsv", "author_contact_needed_yn", "boolean", "recommended", "Whether author contact may be needed.", "Use true/false."),
    field("manual_acquisition_task.tsv", "repository_access_request_needed_yn", "boolean", "recommended", "Whether repository access request may be needed.", "Use true/false."),
    field("manual_acquisition_task.tsv", "assigned_to", "string", "optional", "Human/task owner.", "Blank until assigned."),
    field("manual_acquisition_task.tsv", "status", "category", "required", "Manual task status.", "Use open until completed or ruled out.", vocab("manual_task_status"), "open"),
    field("manual_acquisition_task.tsv", "opened_at", "datetime", "recommended", "Task creation timestamp/date.", "Use batch timestamp."),
    field("manual_acquisition_task.tsv", "closed_at", "datetime", "conditional", "Task close timestamp/date.", "Required if status=closed."),
    field("manual_acquisition_task.tsv", "human_outcome", "string", "optional", "Outcome after human work.", "Examples: pdf_downloaded, paywalled, no_source_found, value_verified."),
    field("manual_acquisition_task.tsv", "created_source_file_id", "string", "conditional", "Source file created by manual work.", "Foreign key to source_file.tsv when available."),
    field("manual_acquisition_task.tsv", "created_support_ids", "string", "conditional", "Support rows created by manual work.", "Pipe-delimit source_result_support IDs if introduced later."),
    field("manual_acquisition_task.tsv", "manual_notes", "string", "optional", "Manual task notes.", "Keep concise, actionable, and safe to share."),
]


PROMOTION_GATES = [
    ("G1 source identity", "source_id, source_type, title, and stable citation or URL are present."),
    ("G2 byte access", "source_access row gives direct URL/API or local path; mirrored files have size and checksum, or an access barrier is explicit."),
    ("G3 locator", "source_result.source_locator is precise enough to find the source row/table/page/API field again."),
    ("G4 verbatim evidence", "verbatim source row plus effect/statistic and N text are copied before parsing, unless row is explicitly blocked/staged."),
    ("G5 native parse", "native values are parsed without changing metric, with arm/cluster Ns split when available."),
    ("G6 transformation", "D/N or native-panel values have a named method, inputs, and transformation explanation."),
    ("G7 focal selector", "paper/project rows document why this result is focal or how multiple eligible results were collapsed."),
    ("G8 bibliographic mapping", "extraction source and represented source citations are separated; generated dot citations are internal only."),
    ("G9 deduplication", "canonical_result records source_result_count and aggregation/resolution rule."),
    ("G10 human check", "A human can open local_path, use source_locator, see verbatim text, and recalculate final D/N or native value."),
]


def write_tsv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def markdown_table(headers: list[str], rows: list[list[str]]) -> str:
    def cell(value: str) -> str:
        return str(value).replace("|", "\\|").replace("\n", " ")

    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    lines.extend("| " + " | ".join(cell(value) for value in row) + " |" for row in rows)
    return "\n".join(lines)


def write_templates() -> None:
    TEMPLATE_DIR.mkdir(parents=True, exist_ok=True)
    rows = field_rows_with_defaults()
    for table in TABLES:
        table_name = table["table_name"]
        columns = [row["column_name"] for row in rows if row["table_name"] == table_name]
        (TEMPLATE_DIR / table_name).write_text("\t".join(columns) + "\n", encoding="utf-8")


def table_schema_rows(field_rows: list[dict[str, str]]) -> list[dict[str, object]]:
    rows_by_table: dict[str, list[dict[str, str]]] = {}
    for row in field_rows:
        rows_by_table.setdefault(row["table_name"], []).append(row)

    schemas: list[dict[str, object]] = []
    for table in TABLES:
        table_name = table["table_name"]
        columns = [
            {
                "name": row["column_name"],
                "data_type": row["data_type"],
                "required_level": row["required_level"],
                "allowed_values": row["allowed_values"],
                "definition": row["definition"],
                "coding_rules": row["coding_rules"],
                "example": row["example"],
            }
            for row in rows_by_table.get(table_name, [])
        ]
        schemas.append(
            {
                "table_name": table_name,
                "grain": table["grain"],
                "primary_key": table["primary_key"],
                "required_for_promotion": table["required_for_promotion"],
                "description": table["description"],
                "columns": columns,
            }
        )
    return schemas


def write_root_schema_files(field_rows: list[dict[str, str]]) -> None:
    """Write obvious root-level schema artifacts for humans and LLMs."""
    write_tsv(
        ROOT_TABLES_TSV,
        TABLES,
        ["table_name", "grain", "primary_key", "required_for_promotion", "description"],
    )
    write_tsv(
        ROOT_FIELDS_TSV,
        field_rows,
        [
            "table_name",
            "column_name",
            "data_type",
            "required_level",
            "allowed_values",
            "definition",
            "coding_rules",
            "example",
            "qa_checks",
        ],
    )

    schemas = table_schema_rows(field_rows)
    payload = {
        "PROVENANCE_DATABASE_TABLES_AND_SCHEMAS": {
            "status": "generated_from_scripts_write_provenance_codebook_py",
            "purpose": (
                "Root-level, obvious schema index for the provenance database. "
                "It mirrors the formal codebook TSVs so humans and LLMs can find "
                "the tables and fields without digging through data/derived."
            ),
            "pipeline_shape": [
                "search_lead",
                "source / source_access / source_file",
                "source_source_mapping",
                "source_result",
                "canonical_result",
                "plot_membership under plot_universe and plot_criterion",
            ],
            "root_level_files": {
                "tables_tsv": ROOT_TABLES_TSV.name,
                "fields_tsv": ROOT_FIELDS_TSV.name,
                "schemas_yml": ROOT_SCHEMA_YML.name,
                "human_readable_md": ROOT_SCHEMA_MD.name,
            },
            "derived_machine_files": {
                "tables_tsv": str(CODEBOOK_TSV.relative_to(ROOT)),
                "fields_tsv": str(DATA_DICTIONARY_TSV.relative_to(ROOT)),
                "vocabulary_tsv": str(VOCAB_DICTIONARY_TSV.relative_to(ROOT)),
                "empty_templates_dir": str(TEMPLATE_DIR.relative_to(ROOT)),
            },
            "tables": schemas,
        }
    }
    ROOT_SCHEMA_YML.write_text(
        yaml.safe_dump(payload, sort_keys=False, allow_unicode=False, width=100),
        encoding="utf-8",
    )

    table_rows = [
        [
            table["table_name"],
            table["grain"],
            table["primary_key"],
            str(len(table["columns"])),
        ]
        for table in schemas
    ]
    lines = [
        "# Provenance Database Tables And Schemas",
        "",
        "Root-level schema index for the provenance database.",
        "",
        "Canonical generated files at repo root:",
        "",
        f"- `{ROOT_SCHEMA_YML.name}`: all tables and columns in YAML.",
        f"- `{ROOT_TABLES_TSV.name}`: one row per table.",
        f"- `{ROOT_FIELDS_TSV.name}`: one row per field.",
        "",
        "Pipeline shape:",
        "",
        "```text",
        "search_lead",
        "  -> source / source_access / source_file",
        "  -> source_source_mapping",
        "  -> source_result",
        "  -> canonical_result",
        "  -> plot_membership under plot_universe and plot_criterion",
        "```",
        "",
        "## Tables",
        "",
        markdown_table(["Table", "Grain", "Primary Key", "Columns"], table_rows),
        "",
        "The nested generated copies remain under `data/derived/effect_inflation_dataset/` for pipelines that already read those paths.",
        "",
    ]
    ROOT_SCHEMA_MD.write_text("\n".join(lines), encoding="utf-8")


def write_vocab_dictionary() -> None:
    write_tsv(
        VOCAB_DICTIONARY_TSV,
        vocab_definition_rows(),
        ["field_name", "allowed_value", "definition", "coding_notes"],
    )


def write_markdown_docs() -> None:
    REPORTS.mkdir(parents=True, exist_ok=True)
    table_rows = [[t["table_name"], t["grain"], t["primary_key"], t["required_for_promotion"]] for t in TABLES]
    gate_rows = [[gate, rule] for gate, rule in PROMOTION_GATES]
    vocab_rows = [[name, " | ".join(values)] for name, values in CONTROLLED_VOCABS.items()]
    field_rows = field_rows_with_defaults()
    column_family_rows = [
        ["Search leads", "`search_lead.tsv`", "`plot_universe_id`, `search_track_id`, `lead_type`, `lead_title`, `candidate_artifact_path_or_url`, `triage_status`, `lead_decision`", "Top-of-pipeline candidates found before they become sources or source-result rows."],
        ["Source identity", "`source.tsv`", "`source_id`, `source_type`, `title`, `citation_key`, `doi`, `pmid`, `registry_id`, `url`", "Identifies the real-world or computational object."],
        ["Access and mirroring", "`source_access.tsv`", "`remote_url`, `api_url`, `local_path`, `file_sha256`, `access_strategy`, `source_byte_class`, `level5_eligible`", "Documents exactly how we got or failed to get source bytes."],
        ["Access attempts", "`source_access_attempt.tsv`", "`resolver_strategy`, `candidate_url`, `final_url`, `decision`, `decision_reason`, blocker and abstract/preprint fields", "Append-only record of DOI/publisher/OA/preprint/API routes tried before choosing an access object."],
        ["File artifacts", "`source_file.tsv`", "`source_file_id`, `local_path`, `sha256`, `file_role`, `file_origin`, `source_byte_class`, `level5_eligible`", "Content-addressed inventory of actual mirrored or local byte objects."],
        ["Version and rights", "`source_version.tsv` and `source_access_right.tsv`", "`version_label`, `is_version_of_record`, `license_url`, `mirror_allowed_yn`, `rights_decision`", "Keeps VOR/preprint/registry/dataset versions and lawful mirroring decisions separate from attempts."],
        ["Verbatim extraction", "`source_result.tsv`", "`verbatim_source_row_text`, `verbatim_outcome_text`, `verbatim_effect_text`, `verbatim_n_text`, `verbatim_p_text`, `verbatim_ci_text`", "Human-checkable copied text before parsing."],
        ["Native parsing", "`source_result.tsv`", "`native_effect_value`, `native_effect_metric`, `native_standard_error`, `native_n_total`, arm Ns, cluster N", "Parsed values in source-native units."],
        ["Standardization", "`source_result.tsv`", "`standardized_effect_value`, `standardized_n`, `d`, `d_conversion_method`, `d_conversion_inputs`, `transformation_explanation`", "How source-native values became D/N or native-panel values."],
        ["Focal selector", "`source_result.tsv` and `source_source_mapping.tsv`", "`selector_status`, `selector_rule`, `selector_mapping_id`, prereg selector fields", "Why this result is the plotted/canonical result."],
        ["Preregistration", "`source_result.tsv` and `source_source_mapping.tsv`", "`prereg_status`, `prereg_mapping_id`, registry/PAP fields, selector text", "Specific evidence for prereg/PAP/registered-report claims."],
        ["Replication", "`source_result.tsv` and `source_source_mapping.tsv`", "`replication_mapping_id`, `replication_role`, `replication_pair_id`, `replication_kind`, target-claim fields", "Specific evidence for original/replication/reproduction relationships."],
        ["Canonical plotting", "`canonical_result.tsv`", "`source_result_count`, `aggregation_rule`, `D_min`, `D_median`, `D_max`, `N_min`, `N_median`, `N_max`", "One plotted/collapsed row selected from source-result rows."],
        ["Plot contexts", "`plot_universe.tsv`, `plot_criterion.tsv`, and `plot_membership.tsv`", "`plot_universe_id`, `criterion_id`, `eligibility_status`, `passed_criteria_ids`, `failed_criteria_ids`", "Context-specific inclusion/exclusion decisions for current figures, diagnostics, sensitivities, and future plots."],
        ["Problems/events", "`extraction_event.tsv` and `extraction_problem.tsv`", "`event_step`, `command_or_tool`, `problem_code`, `severity`, `suggested_rework`", "Audit trail and rework queue."],
    ]
    minimum_rows = [
        ["New corpus/database or individual replication-paper lead", "`search_lead.tsv`", "Record search context, lead type, URL/path/artifact, expected fields, triage status, decision, blockers, and next action before promotion."],
        ["Direct paper/registry result", "`source`, `source_access`, `source_result`, `canonical_result`", "Needs value-bearing source bytes, locator, verbatim effect/N text, native parse, transformation, and citation."],
        ["Corpus/database result about another paper", "`source`, `source_access`, `source_result`, `source_source_mapping`, `canonical_result`", "Keep extraction source and represented source separate; map the corpus row to the child paper/result; do not treat corpus numbers as original-source verification."],
        ["Preregistered result", "`source_result` plus prereg mapping row", "Needs prereg status, direct artifact URL when available, timing, selector locator/text, and mapping evidence. Corpus-only prereg claims must be coded as `prereg_asserted_by_corpus_no_artifact`."],
        ["Replication/reproduction result", "`source_result` plus replication mapping row", "Needs role, pair ID, kind, target claim, original/replicating result IDs when available, and assertion evidence."],
        ["Collapsed paper/project row", "`canonical_result` plus child `source_result` rows", "Needs source_result_count, aggregation rule, min/median/max fields when relevant, and child rows preserved."],
        ["Blocked/staged row", "`source`, `source_access`, `source_result`, `extraction_problem`", "Leave missing fields blank, state blocker, and record exact rework action/URL/path."],
        ["Manual acquisition task", "`manual_acquisition_task.tsv`", "Create when automated attempts leave missing source objects, value text, prereg artifacts, replication evidence, or rights review."],
    ]
    critical_vocab_fields = {
        "source_byte_class",
        "attempt_decision",
        "search_lead_type",
        "lead_decision",
        "eligibility_status",
        "relationship_type",
        "relationship_subtype",
        "prereg_status",
        "replication_role",
        "coding_status",
        "evidence_level_name",
        "d_conversion_method",
    }
    critical_vocab_rows = [
        [row["field_name"], row["allowed_value"], row["definition"], row["coding_notes"]]
        for row in vocab_definition_rows()
        if row["field_name"] in critical_vocab_fields
    ]
    dictionary_snapshot_rows = [
        [
            table["table_name"],
            str(sum(1 for row in field_rows if row["table_name"] == table["table_name"])),
            table["grain"],
        ]
        for table in TABLES
    ]
    codebook = f"""# Evidence Dataset Codebook

This repository treats plotted and staged results as a proper auditable dataset. The governing principle is: a row is not trustworthy because it appears in a plot; it is trustworthy when a human can retrace it from raw source bytes, through verbatim copied text, through native parsing, through transformation, into a canonical plotted or staged result.

## Required Tables

{markdown_table(["Table", "Grain", "Primary key", "Promotion requirement"], table_rows)}

## Dictionary Snapshot

{markdown_table(["Table", "Columns", "Grain"], dictionary_snapshot_rows)}

## Column Families

The TSVs are organized by purpose. This table is the fastest way to decide where a fact belongs.

{markdown_table(["Family", "Table(s)", "Main columns", "Purpose"], column_family_rows)}

## Promotion Gates

Rows can be plotted on the main D-axis only after all applicable gates pass. Rows may be staged in the native panel or blocked with explicit problems before then.

{markdown_table(["Gate", "Criterion"], gate_rows)}

## Coding Rules

1. Mirror the source locally whenever access allows it; store exact local paths and checksums.
2. Separate bibliographic identity from computational access. A paper, registry record, corpus, database, zip file, extracted CSV, and script output can all be different sources.
3. Separate labels from evidence. `result_label` and `outcome_label` are display labels; they are not verbatim source text.
4. Copy original source text before parsing. Use one-line TSV-safe verbatim fields for source row text, outcome text, effect/statistic text, N text, p/CI text, and any notes needed to check the row.
5. Parse native values without changing their metric. Store regression coefficients, risk differences, event counts, standard errors, Ns, and cluster counts in native fields before any D conversion.
6. Do not force Cohen's d. Use D only for reported d/g/SMD or defensible conversions with documented inputs. Clustered field experiments, arbitrary LPMs, policy ATEs, and outcomes without SD/baseline/event counts should go to the native panel.
7. Preserve multiple source assertions. If the same result appears in a paper, corpus, and database, keep separate `source_result` rows and resolve them later in `canonical_result`.
8. Track parent-child relationships. Corpora and collections can contain thousands of child papers/results; record those mappings rather than pretending the corpus itself is one paper.
9. Record extraction events and failures. Manual uploads, login walls, PDF extraction, script execution, and failed downloads are dataset facts.
10. If a field is missing, leave it blank and add an `extraction_problem` row. Do not hide missing evidence in prose notes.

## Mapping Detail Rules

Use `source_source_mapping.tsv` for relationship evidence, not just yes/no flags. A preregistered result should point to a mapping row with the registry/PAP source, URL, registration date, timing, locator, and verbatim selector text. A replication result should point to a mapping row with the original source, replicating source, replication kind, target claim, outcome/design/sample relation, and assertion evidence. Corpus/database rows should map the corpus source to the represented paper/result with the corpus row ID or locator and any external child identifiers.

Use `source_result.tsv` columns such as `prereg_mapping_id`, `prereg_selector_verbatim_text`, `replication_mapping_id`, `replication_pair_id`, and `source_mapping_ids` to connect result rows back to those detailed mappings. These columns should contain IDs and copied source text, not vague notes like "yes" or "replication".

## Minimum Row Sets

Different evidence types require different rows. These are minimums, not maximums.

{markdown_table(["Case", "Minimum tables", "Requirements"], minimum_rows)}

## Evidence Levels

Every `source_result` gets a numeric `evidence_level` and a controlled `evidence_level_name`.

{markdown_table(["Level", "Name", "Meaning"], [
    ["0", "unanchored_number", "A D/N or native number exists, but no real-world source assertion or represented source can be identified."],
    ["1", "internal_trace_only", "The row retraces only to this repository's internal derived/intermediate files."],
    ["2", "external_source_assertion", "A real external corpus/database/registry asserts the number, but the represented paper/study is not durably identified."],
    ["3", "external_assertion_with_target_source", "An external source asserts the number and gives enough bibliographic/registry information that the represented target source could theoretically be found."],
    ["4", "target_source_independently_grounded", "We resolved the represented target source in the wider world via DOI, PMID, PMCID, NCT, AEA, Dataverse, Crossref, or another independent URL/citation database."],
    ["5", "original_source_obtained", "We obtained or mirrored value-bearing source bytes that could plausibly contain the plotted value, such as full article PDF/XML/HTML, registry record, supplement, data/code package, or author manuscript, with path/checksum when possible. Metadata records, abstract pages, paywalls, CAPTCHA pages, and access-denied pages are not level 5 unless the plotted value is present there."],
    ["6", "original_number_extracted", "We extracted/copied the exact effect/N/supporting text ourselves from the original source bytes or authoritative registry/API/table."],
    ["7", "recomputed_from_raw", "We recomputed the number from raw data/code and preserved the output."],
])}

## Controlled Vocabularies

{markdown_table(["Field", "Allowed values"], vocab_rows)}

## Critical Vocabulary Definitions

The full machine-readable vocabulary dictionary is `data/derived/effect_inflation_dataset/provenance_vocab_dictionary.tsv`. The critical values below are included here because they affect promotion, plotting, preregistration, replication, and level-5 evidence decisions.

{markdown_table(["Field", "Value", "Definition", "Coding notes"], critical_vocab_rows)}

## Files

- Machine-readable table codebook: `data/derived/effect_inflation_dataset/provenance_codebook.tsv`
- Machine-readable data dictionary: `data/derived/effect_inflation_dataset/provenance_data_dictionary.tsv`
- Machine-readable controlled-vocabulary dictionary: `data/derived/effect_inflation_dataset/provenance_vocab_dictionary.tsv`
- Empty TSV templates: `data/derived/effect_inflation_dataset/schema_templates/`
- LLM extraction contract: `reports/llm_extraction_contract.md`

## Current Pilot Benchmark

The 300-row pilot is intentionally a stress test, not a final claim that every old row is fully provenanced. Current extractor rewrites should try to reduce `plot_row_only`, `n_only_recovered`, and `source_is_derived_not_original_text` by writing these source-result fields at extraction time. Public plotting should require evidence level 3 or higher unless a plot is explicitly labeled as a diagnostic/worklist view.
"""
    CODEBOOK_MD.write_text(codebook, encoding="utf-8")

    contract = """# LLM Extraction Contract

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
"""
    LLM_CONTRACT_MD.write_text(contract, encoding="utf-8")


def main() -> None:
    DERIVED.mkdir(parents=True, exist_ok=True)
    field_rows = field_rows_with_defaults()
    write_tsv(
        CODEBOOK_TSV,
        TABLES,
        ["table_name", "grain", "primary_key", "required_for_promotion", "description"],
    )
    write_tsv(
        DATA_DICTIONARY_TSV,
        field_rows,
        [
            "table_name",
            "column_name",
            "data_type",
            "required_level",
            "allowed_values",
            "definition",
            "coding_rules",
            "example",
            "qa_checks",
        ],
    )
    write_vocab_dictionary()
    write_templates()
    write_markdown_docs()
    write_root_schema_files(field_rows)
    print(f"Wrote {CODEBOOK_TSV.relative_to(ROOT)}")
    print(f"Wrote {DATA_DICTIONARY_TSV.relative_to(ROOT)}")
    print(f"Wrote {VOCAB_DICTIONARY_TSV.relative_to(ROOT)}")
    print(f"Wrote templates to {TEMPLATE_DIR.relative_to(ROOT)}")
    print(f"Wrote {CODEBOOK_MD.relative_to(ROOT)}")
    print(f"Wrote {LLM_CONTRACT_MD.relative_to(ROOT)}")
    print(f"Wrote {ROOT_SCHEMA_YML.relative_to(ROOT)}")
    print(f"Wrote {ROOT_SCHEMA_MD.relative_to(ROOT)}")
    print(f"Wrote {ROOT_TABLES_TSV.relative_to(ROOT)}")
    print(f"Wrote {ROOT_FIELDS_TSV.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
