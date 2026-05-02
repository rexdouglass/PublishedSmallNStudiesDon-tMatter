#!/usr/bin/env python3
"""Build codebook-shaped provenance pilot tables from the retraced sample."""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
from pathlib import Path
from urllib.parse import urlparse

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DERIVED = ROOT / "data" / "derived" / "effect_inflation_dataset"
PILOT = DERIVED / "schema_pilot"
DICTIONARY = DERIVED / "provenance_data_dictionary.tsv"
SAMPLE_N = int(os.environ.get("SCHEMA_PILOT_N", "300"))
SAMPLE_SUFFIX = f"sample_{SAMPLE_N}"

SOURCE_IN = PILOT / f"source_{SAMPLE_SUFFIX}.tsv"
ACCESS_IN = PILOT / f"source_access_{SAMPLE_SUFFIX}.tsv"
SOURCE_RESULT_IN = PILOT / f"source_result_{SAMPLE_SUFFIX}.tsv"
CANONICAL_IN = PILOT / f"canonical_result_{SAMPLE_SUFFIX}.tsv"
MAPPING_IN = PILOT / f"source_source_mapping_{SAMPLE_SUFFIX}.tsv"
HUMAN_IN = PILOT / f"human_check_source_result_{SAMPLE_SUFFIX}.tsv"
EVENTS_IN = PILOT / f"retrace_events_{SAMPLE_SUFFIX}.tsv"
PROBLEMS_IN = PILOT / f"retrace_problems_{SAMPLE_SUFFIX}.tsv"
GROUNDING_IN = PILOT / f"real_world_grounding_{SAMPLE_SUFFIX}.tsv"
LEVEL5_STATUS_IN = PILOT / f"level5_row_status_{SAMPLE_SUFFIX}.tsv"
LEVEL5_ATTEMPTS_IN = PILOT / f"level5_fetch_attempts_{SAMPLE_SUFFIX}.tsv"
LEVEL6_VERIFY_IN = PILOT / f"level6_value_verification_attempts_{SAMPLE_SUFFIX}.tsv"

OUT_FILES = {
    "source.tsv": PILOT / f"source_codebook_{SAMPLE_SUFFIX}.tsv",
    "source_access.tsv": PILOT / f"source_access_codebook_{SAMPLE_SUFFIX}.tsv",
    "source_access_attempt.tsv": PILOT / f"source_access_attempt_codebook_{SAMPLE_SUFFIX}.tsv",
    "source_file.tsv": PILOT / f"source_file_codebook_{SAMPLE_SUFFIX}.tsv",
    "source_version.tsv": PILOT / f"source_version_codebook_{SAMPLE_SUFFIX}.tsv",
    "source_access_right.tsv": PILOT / f"source_access_right_codebook_{SAMPLE_SUFFIX}.tsv",
    "source_identifier.tsv": PILOT / f"source_identifier_codebook_{SAMPLE_SUFFIX}.tsv",
    "source_classification.tsv": PILOT / f"source_classification_codebook_{SAMPLE_SUFFIX}.tsv",
    "source_result.tsv": PILOT / f"source_result_codebook_{SAMPLE_SUFFIX}.tsv",
    "canonical_result.tsv": PILOT / f"canonical_result_codebook_{SAMPLE_SUFFIX}.tsv",
    "canonical_result_membership.tsv": PILOT / f"canonical_result_membership_codebook_{SAMPLE_SUFFIX}.tsv",
    "source_result_support.tsv": PILOT / f"source_result_support_codebook_{SAMPLE_SUFFIX}.tsv",
    "plot_membership.tsv": PILOT / f"plot_membership_codebook_{SAMPLE_SUFFIX}.tsv",
    "source_source_mapping.tsv": PILOT / f"source_source_mapping_codebook_{SAMPLE_SUFFIX}.tsv",
    "extraction_event.tsv": PILOT / f"extraction_event_codebook_{SAMPLE_SUFFIX}.tsv",
    "extraction_problem.tsv": PILOT / f"extraction_problem_codebook_{SAMPLE_SUFFIX}.tsv",
    "manual_acquisition_task.tsv": PILOT / f"manual_acquisition_task_codebook_{SAMPLE_SUFFIX}.tsv",
}
OUT_SUMMARY = PILOT / "codebook_pilot_learning_summary.tsv"
OUT_REPORT = PILOT / "codebook_pilot_learning_report.md"

TIMESTAMP = "2026-04-29T00:00:00-07:00"


def safe_text(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and math.isnan(value):
        return ""
    return re.sub(r"\s+", " ", str(value).replace("\t", " ").replace("\r", " ").replace("\n", " ")).strip()


def read_tsv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, sep="\t", dtype=str, keep_default_na=False)


def one_line_frame(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for column in out.columns:
        if pd.api.types.is_object_dtype(out[column]) or pd.api.types.is_string_dtype(out[column]):
            out[column] = out[column].map(safe_text)
    return out


def stable_hash(*parts: object, length: int = 12) -> str:
    payload = "\n".join(safe_text(part) for part in parts)
    return hashlib.sha1(payload.encode("utf-8", errors="ignore")).hexdigest()[:length]


def parse_json_cell(value: object) -> dict[str, str]:
    text = safe_text(value)
    if not text:
        return {}
    try:
        loaded = json.loads(text)
    except Exception:
        return {}
    if not isinstance(loaded, dict):
        return {}
    return {safe_text(key): safe_text(val) for key, val in loaded.items()}


def first_pipe_value(value: object) -> str:
    text = safe_text(value)
    if not text:
        return ""
    return safe_text(text.split("|")[0])


def doi_url(doi: object) -> str:
    text = safe_text(doi)
    if not text:
        return ""
    if text.startswith("http"):
        return text
    return f"https://doi.org/{text}"


def is_social_science_registry_url(value: object) -> bool:
    return "socialscienceregistry.org/trials/" in safe_text(value).lower()


def nct_id_from_row(row: pd.Series) -> str:
    for key in ["nct_list", "primary_real_world_url", "url_list", "result_label"]:
        match = re.search(r"NCT\d{8}", safe_text(row.get(key)), flags=re.I)
        if match:
            return match.group(0).upper()
    return ""


def aea_trial_id_from_url(value: object) -> str:
    match = re.search(r"/trials/(\d+)", safe_text(value))
    return f"trials/{match.group(1)}" if match else ""


def is_prereg_candidate(row: pd.Series) -> bool:
    family = safe_text(row.get("source_family")).lower()
    label = safe_text(row.get("result_label")).lower()
    primary = safe_text(row.get("primary_real_world_url")).lower()
    plot_name = safe_text(row.get("plot_name"))
    return bool(
        nct_id_from_row(row)
        or is_social_science_registry_url(primary)
        or "preregister" in family
        or "pre-register" in family
        or "registered report" in family
        or "preregister" in label
        or plot_name == "Plot 3"
    )


def prereg_kind_for(row: pd.Series) -> tuple[str, str, str, str, str]:
    """Return status, timing, registry/platform, registration id, document type."""
    primary = safe_text(row.get("primary_real_world_url"))
    nct = nct_id_from_row(row)
    family = safe_text(row.get("source_family")).lower()
    label = safe_text(row.get("result_label")).lower()
    plot_name = safe_text(row.get("plot_name"))
    if nct:
        return "registry_record_timing_not_audited", "unknown", "ClinicalTrials.gov", nct, "trial_registry_record"
    if is_social_science_registry_url(primary):
        return "registry_metadata_only", "unknown", "AEA RCT Registry", aea_trial_id_from_url(primary), "registry_metadata"
    if "registered report" in family:
        return "registered_report", "pre_analysis", "", "", "registered_report_protocol"
    if (
        "preregister" in family
        or "pre-register" in family
        or "preregister" in label
        or "pre-register" in label
        or plot_name == "Plot 3"
    ):
        return "prereg_asserted_by_corpus_no_artifact", "unknown", "", "", "corpus_preregistration_indicator"
    return "unknown", "unknown", "", "", ""


def prereg_artifact_url_for(row: pd.Series) -> str:
    nct = nct_id_from_row(row)
    if nct:
        return f"https://clinicaltrials.gov/study/{nct}"
    primary = safe_text(row.get("primary_real_world_url"))
    if is_social_science_registry_url(primary):
        return primary
    return ""


def prereg_source_id_for(row: pd.Series) -> str:
    nct = nct_id_from_row(row)
    primary = safe_text(row.get("primary_real_world_url"))
    if nct or is_social_science_registry_url(primary):
        return safe_text(row.get("represented_source_id"))
    return safe_text(row.get("extraction_source_id"))


def prereg_mapping_id(source_result_id: object) -> str:
    return "map_prereg_" + stable_hash(source_result_id)


def replication_mapping_id_from_pair(pair_id: object, source_result_id: object) -> str:
    key = safe_text(pair_id) or safe_text(source_result_id)
    return "map_replication_" + stable_hash(key)


def row_jsons(row: pd.Series) -> tuple[dict[str, str], dict[str, str]]:
    return parse_json_cell(row.get("upstream_row_json")), parse_json_cell(row.get("plot_row_json"))


def replication_pair_id_for(row: pd.Series) -> str:
    upstream, plot = row_jsons(row)
    return (
        safe_text(upstream.get("pair_id"))
        or safe_text(plot.get("pair_id"))
        or safe_text(plot.get("point_id"))
        or safe_text(row.get("dot_record_id"))
    )


def replication_kind_for(row: pd.Series) -> str:
    family = safe_text(row.get("source_family")).lower()
    upstream, plot = row_jsons(row)
    project = safe_text(upstream.get("project")).lower()
    dot = safe_text(row.get("dot_record_id")).lower()
    if "ying" in family or "pilot" in project or "pilot" in dot or "phase ii" in family or "phase 2" in family:
        return "pilot_full_scale_pair"
    if "computational" in family or "reproduction" in family:
        return "computational_reproduction"
    if "robust" in family:
        return "robustness_reanalysis"
    if "conceptual" in family:
        return "conceptual_replication"
    return "direct_replication"


def replication_role_for(row: pd.Series) -> str:
    upstream, plot = row_jsons(row)
    family = safe_text(row.get("source_family")).lower()
    dot_record_id = safe_text(row.get("dot_record_id")).lower()
    side = safe_text(plot.get("side")).lower() or safe_text(plot.get("__plot1_side")).lower()
    point_id = safe_text(plot.get("point_id")).lower() or safe_text(row.get("dot_record_id")).lower()
    if "originals_bridge" in family or "original-side bridge" in family or "repl_orig" in dot_record_id:
        return "original_study"
    if side in {"original", "smaller_n", "small_n"} or "::original" in point_id:
        return "original_study"
    if side in {"replication", "followup", "larger_n", "large_n"} or "::followup" in point_id or "::replication" in point_id:
        return "replication_study"
    return "corpus_replication_assertion"


def is_replication_candidate(row: pd.Series) -> bool:
    directness = safe_text(row.get("source_directness"))
    family = safe_text(row.get("source_family")).lower()
    dot = safe_text(row.get("dot_record_id")).lower()
    upstream, plot = row_jsons(row)
    return bool(
        directness in {"replication_pair_source_row", "staged_replication_pair_source_row"}
        or "replication" in family
        or "replication" in dot
        or upstream.get("replication_doi")
        or upstream.get("replication_title")
        or plot.get("replication_doi")
        or plot.get("replication_title")
    )


def replication_target_claim_for(row: pd.Series) -> str:
    upstream, plot = row_jsons(row)
    family = safe_text(row.get("source_family")).lower()
    dot_record_id = safe_text(row.get("dot_record_id")).lower()
    if "originals_bridge" in family or "original-side bridge" in family or "repl_orig" in dot_record_id:
        return safe_text(row.get("result_label"))
    return (
        safe_text(upstream.get("outcome"))
        or safe_text(plot.get("outcome"))
        or safe_text(upstream.get("original_title"))
        or safe_text(plot.get("original_title"))
        or safe_text(row.get("result_label"))
    )


def compact_mapping_text(row: pd.Series, max_len: int = 1400) -> str:
    text = (
        safe_text(row.get("human_check_text"))
        or safe_text(row.get("verbatim_source_row_text"))
        or safe_text(row.get("upstream_row_json"))
        or safe_text(row.get("plot_row_json"))
    )
    if len(text) > max_len:
        return text[: max_len - 3].rstrip() + "..."
    return text


def numeric_text(value: object) -> str:
    text = safe_text(value)
    if not text:
        return ""
    match = re.search(r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?", text.replace(",", ""))
    return match.group(0) if match else ""


def table_columns(dictionary: pd.DataFrame, table_name: str) -> list[str]:
    return dictionary.loc[dictionary["table_name"].eq(table_name), "column_name"].tolist()


def conform(df: pd.DataFrame, dictionary: pd.DataFrame, table_name: str) -> pd.DataFrame:
    columns = table_columns(dictionary, table_name)
    out = df.copy()
    for column in columns:
        if column not in out.columns:
            out[column] = ""
    return one_line_frame(out[columns])


def map_source_type(value: object) -> str:
    text = safe_text(value)
    mapping = {
        "database_or_registry": "database",
        "corpus_or_database": "corpus",
        "repository_or_package": "repository_or_package",
        "internal_derived_dataset": "local_derived_table",
        "source_family_or_collection": "corpus",
        "registry_trial_or_result": "registry_record",
        "claim": "other",
        "project_or_study": "other",
        "paper_like_work": "paper",
        "unknown_represented_work": "other",
    }
    allowed = {
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
    }
    return mapping.get(text, text if text in allowed else "other")


def map_retrieval_method(value: object) -> str:
    text = safe_text(value)
    mapping = {
        "existing_local_file_plus_notes": "existing_local_file",
        "mixed_locator_and_notes": "existing_local_file",
        "remote_url": "not_retrieved",
        "catalog_or_prose_locator": "not_retrieved",
        "missing": "not_retrieved",
    }
    allowed = {
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
    }
    return mapping.get(text, text if text in allowed else "not_retrieved")


def source_status_for(row: pd.Series) -> str:
    if safe_text(row.get("source_role_in_sample")) == "represented_source" and safe_text(row.get("title")):
        return "primary"
    if safe_text(row.get("source_role_in_sample")) == "extraction_source":
        return "primary"
    return "support_only"


def native_metric_for(row: pd.Series) -> str:
    directness = safe_text(row.get("source_directness"))
    effect = safe_text(row.get("recovered_verbatim_effect_text"))
    p_value = safe_text(row.get("recovered_verbatim_p_or_z_text"))
    if directness == "raw_ctgov_registry_row" and effect == p_value:
        return "p_value_only"
    if directness in {
        "candidate_child_numeric_row",
        "candidate_paper_numeric_row",
        "replication_pair_source_row",
        "staged_replication_pair_source_row",
        "political_science_component_rows",
    }:
        return "standardized_mean_difference"
    return "unknown"


def conversion_method_for(row: pd.Series) -> str:
    directness = safe_text(row.get("source_directness"))
    transform = safe_text(row.get("recovered_transformation_explanation")).lower()
    if "paper-level candidate row" in transform or "median" in transform or directness == "candidate_paper_numeric_row":
        return "paper_median_of_child_d"
    return "source_provided_d_proxy"


def bool_text(value: bool) -> str:
    return "true" if value else "false"


def optional_grounding() -> pd.DataFrame:
    if GROUNDING_IN.exists():
        return read_tsv(GROUNDING_IN)
    return pd.DataFrame(columns=["source_result_id"])


def optional_level5_status() -> pd.DataFrame:
    if LEVEL5_STATUS_IN.exists():
        return read_tsv(LEVEL5_STATUS_IN)
    return pd.DataFrame(columns=["source_result_id"])


def optional_level5_attempts() -> pd.DataFrame:
    if LEVEL5_ATTEMPTS_IN.exists():
        return read_tsv(LEVEL5_ATTEMPTS_IN)
    return pd.DataFrame(columns=["source_result_id"])


def optional_level6_verification() -> pd.DataFrame:
    if not LEVEL6_VERIFY_IN.exists():
        return pd.DataFrame(columns=["source_result_id"])
    # The verifier is run after retracing. Ignore it after a fresh retrace until
    # it is regenerated, otherwise stale source-result IDs can over-promote rows.
    if HUMAN_IN.exists() and LEVEL6_VERIFY_IN.stat().st_mtime < HUMAN_IN.stat().st_mtime:
        return pd.DataFrame(columns=["source_result_id"])
    return read_tsv(LEVEL6_VERIFY_IN)


def strict_level5_source_result_ids() -> set[str]:
    status = optional_level5_status()
    if status.empty:
        return set()
    return set(
        status.loc[
            status.get("any_level5_obtained", "").map(safe_text).eq("True")
            | status.get("level5_candidate_quality", "").map(safe_text).eq("strict_level5_source_object_obtained"),
            "source_result_id",
        ].map(safe_text)
    )


def strict_level6_source_result_ids() -> set[str]:
    verification = optional_level6_verification()
    if verification.empty:
        return set()
    return set(
        verification.loc[
            verification.get("promote_to_level6", "").map(safe_text).eq("true"),
            "source_result_id",
        ].map(safe_text)
    )


def evidence_level_for(row: pd.Series) -> tuple[int, str]:
    grounding_status = safe_text(row.get("grounding_status"))
    literal_status = safe_text(row.get("literal_number_status"))
    local_kind = safe_text(row.get("local_evidence_kind"))
    source_bib_url = safe_text(row.get("source_bib_real_world_url"))
    primary_url = safe_text(row.get("primary_real_world_url"))
    crossref_status = safe_text(row.get("crossref_resolution_status"))

    if literal_status == "literal_number_from_registry_mirror":
        return 6, "original_number_extracted"
    if literal_status in {"literal_number_from_author_output", "literal_number_from_author_table_or_log"}:
        return 6, "original_number_extracted"
    if literal_status == "literal_number_recomputed_from_raw":
        return 7, "recomputed_from_raw"
    if local_kind == "raw_local_mirror" and primary_url:
        return 5, "original_source_obtained"
    if local_kind == "internal_derived_table":
        if primary_url:
            return 4, "target_source_independently_grounded"
        if source_bib_url:
            return 1, "internal_trace_only"
        return 0, "unanchored_number"
    if primary_url and safe_text(row.get("primary_real_world_url_basis")) in {"aea_trial", "nct", "doi", "pmid", "pmcid", "dataverse_dvn"}:
        return 4, "target_source_independently_grounded"
    if primary_url and grounding_status in {
        "registry_identifier_aea_trial",
        "registry_identifier_nct",
        "represented_work_identifier_in_source_row",
        "represented_work_crossref_resolved",
        "represented_work_source_specific_resolved",
    } and crossref_status != "candidate_low_similarity":
        return 4, "target_source_independently_grounded"
    if grounding_status in {
        "registry_identifier_aea_trial",
        "registry_identifier_nct",
        "represented_work_identifier_in_source_row",
        "represented_work_crossref_resolved",
        "represented_work_source_specific_resolved",
    }:
        return 3, "external_assertion_with_target_source"
    if primary_url or source_bib_url or local_kind in {
        "external_corpus_mirror",
        "mirrored_replication_project",
        "raw_local_mirror",
    }:
        return 2, "external_source_assertion"
    return 0, "unanchored_number"


def citation_status_for(row: pd.Series) -> str:
    if safe_text(row.get("source_citation_key")) and safe_text(row.get("source_bib_real_world_url")):
        return "real_citation"
    if safe_text(row.get("generated_result_citation_key")):
        return "generated_internal"
    return "missing"


def confidence_for(row: pd.Series) -> str:
    status = safe_text(row.get("source_text_extraction_status"))
    directness = safe_text(row.get("source_directness"))
    if status != "source_cells_recovered":
        return "low"
    if directness in {"raw_ctgov_registry_row", "political_science_component_rows"}:
        return "high"
    return "medium"


def panel_for(plot_name: object) -> str:
    return safe_text(plot_name).lower().replace(" ", "_") or "unknown"


def split_pipe_values(value: object) -> list[str]:
    return [safe_text(part) for part in safe_text(value).split("|") if safe_text(part)]


def normalized_doi(value: object) -> str:
    text = safe_text(value)
    if not text:
        return ""
    text = re.sub(r"^https?://(?:dx\.)?doi\.org/", "", text, flags=re.I)
    text = re.sub(r"^doi:\s*", "", text, flags=re.I)
    return text.strip().rstrip(".")


def pmcid_url(pmcid: object) -> str:
    text = safe_text(pmcid).upper()
    if not text:
        return ""
    if not text.startswith("PMC"):
        text = f"PMC{text}"
    return f"https://pmc.ncbi.nlm.nih.gov/articles/{text}/"


def nct_url(nct: object) -> str:
    text = safe_text(nct).upper()
    return f"https://clinicaltrials.gov/study/{text}" if text else ""


def aea_trial_url(value: object) -> str:
    text = safe_text(value)
    match = re.search(r"(\d+)$", text)
    return f"https://www.socialscienceregistry.org/trials/{match.group(1)}" if match else ""


def source_version_for_access(row: pd.Series) -> str:
    byte_class = safe_text(row.get("source_byte_class"))
    content_type = safe_text(row.get("content_type")).lower()
    if byte_class == "registry_record_full":
        return "registry_record"
    if byte_class in {"dataset_file", "supplement_file"}:
        return "dataset" if byte_class == "dataset_file" else "supplement"
    if byte_class == "code_file":
        return "code"
    if byte_class == "metadata_record":
        return "metadata"
    if content_type in {"csv", "tsv", "dta", "rds", "xlsx", "sav", "json"}:
        return "dataset" if content_type != "json" else "metadata"
    if content_type in {"r", "do", "py", "ipynb"}:
        return "code"
    if content_type == "pdf":
        return "version_of_record"
    return "unknown"


def source_byte_class_for_access(row: pd.Series) -> str:
    existing = safe_text(row.get("source_byte_class"))
    if existing:
        return existing
    status = safe_text(row.get("access_status"))
    if status in {"blocked", "missing_locator", "unresolved_locator", "remote_url_not_cached", "not_applicable"}:
        return "not_retrieved"
    if status in {"login_required"}:
        return "paywall_or_login_page"
    if status in {"access_denied"}:
        return "access_denied_page"
    content_type = safe_text(row.get("content_type")).lower()
    local_path = safe_text(row.get("local_path")).lower()
    if content_type == "pdf":
        return "supplement_file" if "supplement" in local_path else "full_article_pdf"
    if content_type in {"zip", "tar", "gz"}:
        return "supplement_file"
    if content_type in {"csv", "tsv", "dta", "rds", "xlsx", "sav"}:
        return "dataset_file"
    if content_type == "json":
        return "metadata_record"
    if content_type in {"r", "do", "py", "ipynb"}:
        return "code_file"
    if content_type in {"html", "htm"}:
        return "publisher_landing_or_abstract"
    return "source_object_unclassified" if safe_text(row.get("local_path")) else "not_retrieved"


def level5_eligible_for_access(row: pd.Series) -> str:
    existing = safe_text(row.get("level5_eligible")).lower()
    if existing in {"true", "false"}:
        return existing
    byte_class = safe_text(row.get("source_byte_class"))
    local_path = safe_text(row.get("local_path"))
    value_bearing = {
        "full_article_pdf",
        "full_article_xml",
        "full_article_html",
        "author_manuscript_fulltext",
        "supplement_file",
        "dataset_file",
        "code_file",
        "registry_record_full",
        "pmc_fulltext_xml",
    }
    return bool_text(local_path.startswith("data/raw/") and byte_class in value_bearing)


def file_role_for_access(row: pd.Series) -> str:
    byte_class = safe_text(row.get("source_byte_class"))
    content_type = safe_text(row.get("content_type")).lower()
    local_path = safe_text(row.get("local_path")).lower()
    if byte_class in {"full_article_pdf", "full_article_xml", "full_article_html"}:
        return "full_article"
    if byte_class == "author_manuscript_fulltext":
        return "author_manuscript"
    if byte_class == "registry_record_full":
        return "registry_record"
    if byte_class == "supplement_file":
        return "archive" if content_type in {"zip", "tar", "tgz", "gz"} else "supplement"
    if byte_class == "dataset_file":
        return "derived_table" if local_path.startswith("data/derived/") else "dataset"
    if byte_class == "code_file":
        return "code"
    if byte_class == "metadata_record":
        return "metadata"
    if byte_class == "publisher_landing_or_abstract":
        return "landing_page"
    if byte_class == "pubmed_record_or_abstract":
        return "abstract_page"
    return "other"


def file_origin_for_access(row: pd.Series) -> str:
    local_path = safe_text(row.get("local_path")).lower()
    method = safe_text(row.get("retrieval_method"))
    final_url = safe_text(row.get("final_url")).lower() or safe_text(row.get("remote_url")).lower()
    if local_path.startswith("data/derived/"):
        return "internal_derived"
    if method == "api_download":
        return "api_response"
    if any(host in final_url for host in ["osf.io", "dataverse", "zenodo.org", "figshare", "openicpsr"]):
        return "repository_file"
    if method == "user_upload":
        return "user_upload"
    if method == "browser_manual_download":
        return "manual_browser"
    if method == "code_execution_output":
        return "code_execution_output"
    if method == "existing_local_file":
        return "existing_local_file"
    if method == "automated_download":
        return "automated_download"
    return "unknown"


def file_role_for_byte_class(byte_class: object) -> str:
    byte = safe_text(byte_class)
    if byte in {"full_article_pdf", "full_article_xml", "full_article_html", "pmc_fulltext_xml"}:
        return "full_article"
    if byte == "author_manuscript_fulltext":
        return "author_manuscript"
    if byte == "registry_record_full":
        return "registry_record"
    if byte == "supplement_file":
        return "supplement"
    if byte == "dataset_file":
        return "dataset"
    if byte == "code_file":
        return "code"
    if byte == "metadata_record":
        return "metadata"
    if byte == "pubmed_record_or_abstract":
        return "abstract_page"
    if byte == "publisher_landing_or_abstract":
        return "landing_page"
    return "other"


def file_origin_for_attempt(row: pd.Series) -> str:
    method = safe_text(row.get("retrieval_method"))
    final_url = safe_text(row.get("final_url")).lower() or safe_text(row.get("candidate_url")).lower()
    if method == "api_download":
        return "api_response"
    if any(host in final_url for host in ["osf.io", "zenodo.org", "dataverse", "figshare", "openicpsr"]):
        return "repository_file"
    if safe_text(row.get("source_byte_class")) in {"full_article_pdf", "full_article_xml", "full_article_html", "pmc_fulltext_xml"}:
        return "publisher_file" if "api." in final_url or "doi.org" in final_url else "automated_download"
    if method == "automated_download":
        return "automated_download"
    return "unknown"


def target_and_value_states(row: pd.Series) -> tuple[str, str]:
    name = safe_text(row.get("evidence_level_name"))
    if name == "unanchored_number":
        return "unanchored", "not_checked"
    if name == "internal_trace_only":
        return "external_assertion_only", "not_checked"
    if name == "external_source_assertion":
        return "target_identity_known", "corpus_assertion_only"
    if name == "external_assertion_with_target_source":
        return "target_located", "corpus_assertion_only"
    if name == "target_source_independently_grounded":
        return "target_located", "corpus_assertion_only"
    if name == "original_source_obtained":
        return "source_object_mirrored", "source_object_obtained_not_parsed"
    if name == "original_number_extracted":
        return "text_or_data_extracted", "d_n_verified_from_source"
    if name == "recomputed_from_raw":
        return "text_or_data_extracted", "d_n_verified_from_source"
    return "external_assertion_only", "not_checked"


def plot_id_for(value: object) -> str:
    text = safe_text(value)
    mapping = {
        "Plot 1": "plot1_replication",
        "Plot 2": "plot2_published",
        "Plot 3": "plot3_preregistered",
        "Plot 4": "plot4_all_sources",
    }
    return mapping.get(text, re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_") or "unknown_plot")


def plot_universe_id_for(value: object) -> str:
    text = safe_text(value)
    mapping = {
        "Plot 1": "plot1_replication_pairs",
        "Plot 2": "plot2_published_paper_d_vs_n",
        "Plot 3": "plot3_preregistered_results",
        "Plot 4": "plot4_all_source_dn_dump",
    }
    return mapping.get(text, plot_id_for(text))


def field_from_source_family(value: object) -> str:
    text = safe_text(value).lower()
    if not text:
        return ""
    if "clinicaltrials" in text or "clinical" in text or "medicine" in text or "ctgov" in text or "ying 2023" in text:
        return "Clinical medicine"
    if "political" in text or "egap" in text or "aea" in text or "tess" in text or "metaketa" in text:
        return "Political science"
    if "economic" in text or "finance" in text or "development" in text or "dime" in text or "j-pal" in text:
        return "Economics/finance"
    if "business" in text or "management" in text:
        return "Business"
    if "education" in text:
        return "Education"
    if "sociology" in text or "criminology" in text:
        return "Sociology/criminology"
    if "gwas" in text or "genome" in text or "preclinical" in text or "biology" in text:
        return "Preclinical biology"
    if "psych" in text or "score" in text or "metabus" in text or "many labs" in text or "replication" in text:
        return "Psychology/health"
    return ""


def normalize_field_label(value: object) -> str:
    text = safe_text(value)
    aliases = {
        "clinical medicine": "Clinical medicine",
        "clinical": "Clinical medicine",
        "psychology/health": "Psychology/health",
        "psychology": "Psychology/health",
        "psychology and health": "Psychology/health",
        "economics/finance": "Economics/finance",
        "economics": "Economics/finance",
        "finance": "Economics/finance",
        "preclinical biology": "Preclinical biology",
        "political science": "Political science",
        "education": "Education",
        "sociology/criminology": "Sociology/criminology",
        "business": "Business",
    }
    return aliases.get(text.lower(), text)


def field_from_row(row: pd.Series) -> tuple[str, str, str]:
    upstream, plot = row_jsons(row)
    for key in ["field", "Field", "plot_field", "discipline", "domain"]:
        value = safe_text(plot.get(key)) or safe_text(upstream.get(key))
        if value:
            return normalize_field_label(value), "plot_row_json", "high"
    family_field = field_from_source_family(row.get("source_family"))
    if family_field:
        return normalize_field_label(family_field), "inferred_from_source_family", "medium"
    return "", "", ""


def add_identifier(
    rows: list[dict[str, str]],
    seen: set[tuple[str, str, str]],
    source_id: object,
    identifier_type: str,
    identifier_value: object,
    identifier_url: object,
    identifier_source: str,
    is_primary: bool,
    confidence: str = "high",
    notes: str = "",
) -> None:
    sid = safe_text(source_id)
    value = safe_text(identifier_value)
    if identifier_type == "doi":
        value = normalized_doi(value)
    if not sid or not value:
        return
    key = (sid, identifier_type, value.lower())
    if key in seen:
        return
    seen.add(key)
    rows.append(
        {
            "source_id": sid,
            "identifier_type": identifier_type,
            "identifier_value": value,
            "identifier_url": safe_text(identifier_url),
            "identifier_source": identifier_source,
            "is_primary": bool_text(is_primary),
            "confidence": confidence,
            "notes": notes,
        }
    )


def add_classification(
    rows: list[dict[str, str]],
    seen: set[tuple[str, str, str]],
    source_id: object,
    classification_type: str,
    classification_value: object,
    classification_source: str,
    confidence: str = "medium",
    notes: str = "",
) -> None:
    sid = safe_text(source_id)
    value = safe_text(classification_value)
    if not sid or not value:
        return
    key = (sid, classification_type, value)
    if key in seen:
        return
    seen.add(key)
    rows.append(
        {
            "source_id": sid,
            "classification_type": classification_type,
            "classification_value": value,
            "classification_source": classification_source,
            "classification_confidence": confidence,
            "notes": notes,
        }
    )


def problem_suggestion(code: str) -> str:
    suggestions = {
        "source_is_derived_not_original_text": "Backfill the original paper/database/table row and keep this derived row as a sidecar source-result.",
        "missing_verbatim_effect_text": "Recover the literal effect/statistic cell from the source before promotion.",
        "missing_verbatim_n_text": "Recover the literal N/sample-size cell from the source before promotion.",
        "missing_source_locator": "Add an atomic source_access row with a direct URL or local mirror path.",
        "access_blocked": "Record the access barrier and request/manual-download path.",
        "needs_pdf_check": "Extract the table text from the mirrored PDF and cite the page/table.",
        "needs_code_execution": "Run the analysis script and preserve the generated table/log as a mirrored source file.",
        "conversion_not_defensible": "Route to native_panel unless conversion inputs are recovered.",
        "duplicate_needs_resolution": "Resolve parent/child or source/source duplicate hierarchy before plotting.",
        "missing_bibliographic_key": "Add a real source citation key and rendered citation.",
    }
    return suggestions.get(code, "Review and re-code under the provenance codebook.")


def markdown_table(headers: list[str], rows: list[list[object]]) -> str:
    def cell(value: object) -> str:
        return safe_text(value).replace("|", "\\|")

    return "\n".join(
        [
            "| " + " | ".join(headers) + " |",
            "| " + " | ".join(["---"] * len(headers)) + " |",
            *["| " + " | ".join(cell(value) for value in row) + " |" for row in rows],
        ]
    )


def make_sources(dictionary: pd.DataFrame) -> pd.DataFrame:
    out = read_tsv(SOURCE_IN)
    for column in ["pmid", "registry_id"]:
        if column not in out.columns:
            out[column] = ""
    out["source_type"] = out["source_type"].map(map_source_type)
    out["title"] = out.apply(lambda row: safe_text(row.get("title")) or safe_text(row.get("citation_key")) or safe_text(row.get("source_id")), axis=1)
    out["source_status"] = out.apply(source_status_for, axis=1)
    grounding = optional_grounding()
    if not grounding.empty and "represented_source_id" in read_tsv(SOURCE_RESULT_IN).columns:
        sr = read_tsv(SOURCE_RESULT_IN)[["source_result_id", "represented_source_id"]]
        enrich = sr.merge(grounding, on="source_result_id", how="left")
        by_source: dict[str, pd.Series] = {}
        for _, row in enrich.iterrows():
            sid = safe_text(row.get("represented_source_id"))
            if sid and sid not in by_source:
                by_source[sid] = row
        for idx, row in out.iterrows():
            sid = safe_text(row.get("source_id"))
            info = by_source.get(sid)
            if info is None:
                continue
            if not safe_text(out.at[idx, "url"]):
                out.at[idx, "url"] = safe_text(info.get("primary_real_world_url"))
            if not safe_text(out.at[idx, "doi"]):
                doi = first_pipe_value(info.get("doi_list"))
                if doi and not doi.lower().startswith("nct"):
                    out.at[idx, "doi"] = doi.replace("https://doi.org/", "")
            if "pmid" in out.columns and not safe_text(out.at[idx, "pmid"]):
                out.at[idx, "pmid"] = first_pipe_value(info.get("pmid_list"))
            if "registry_id" in out.columns and not safe_text(out.at[idx, "registry_id"]):
                out.at[idx, "registry_id"] = nct_id_from_row(info) or first_pipe_value(info.get("aea_trial_list"))
    return conform(out, dictionary, "source.tsv")


def make_access(dictionary: pd.DataFrame) -> pd.DataFrame:
    out = read_tsv(ACCESS_IN)
    out["file_member_path"] = ""
    out["final_url"] = out["remote_url"].map(safe_text) if "remote_url" in out.columns else ""
    out["http_status"] = ""
    out["redirect_chain"] = ""
    out["host"] = out["final_url"].map(lambda url: safe_text(urlparse(url).netloc))
    out["retrieval_method"] = out["retrieval_method"].map(map_retrieval_method)
    out["source_byte_class"] = out.apply(source_byte_class_for_access, axis=1)
    out["level5_eligible"] = out.apply(level5_eligible_for_access, axis=1)
    out["license_url"] = ""
    out["license_category"] = "unknown"
    out["storage_allowed"] = out["access_status"].map(lambda status: "true" if safe_text(status) in {"local_file_found", "downloaded"} else "unknown")
    out["source_version"] = out.apply(source_version_for_access, axis=1)
    out["retrieval_policy_notes"] = ""
    out["abstract_or_detail_text"] = ""
    out["abstract_or_detail_source_url"] = out["final_url"]
    out["paywall_or_login_seen"] = out["access_barrier"].map(lambda barrier: bool_text(safe_text(barrier).lower() in {"paywall", "login", "license"})) if "access_barrier" in out.columns else "false"
    out["captcha_or_bot_block_seen"] = out["access_barrier"].map(lambda barrier: bool_text("captcha" in safe_text(barrier).lower() or "bot" in safe_text(barrier).lower())) if "access_barrier" in out.columns else "false"
    out["preprint_or_repository_candidate"] = out["final_url"].map(
        lambda url: bool_text(
            any(host in safe_text(url).lower() for host in ["osf.io", "zenodo.org", "dataverse", "openicpsr", "arxiv.org", "ssrn.com"])
        )
    )
    return conform(out, dictionary, "source_access.tsv")


def access_attempt_decision(row: pd.Series) -> tuple[str, str, str]:
    status = safe_text(row.get("access_status"))
    byte_class = safe_text(row.get("source_byte_class"))
    barrier = safe_text(row.get("access_barrier")).lower()
    level5 = safe_text(row.get("level5_eligible")).lower()
    if "captcha" in barrier or "bot" in barrier or byte_class == "captcha_page":
        return "captcha_or_bot_block", "Route returned CAPTCHA/bot-check evidence.", "manual_review"
    if "paywall" in barrier or "login" in barrier or byte_class == "paywall_or_login_page":
        return "paywall_or_login", "Route returned paywall/login evidence.", "try_oa_or_manual_access"
    if status in {"access_denied", "blocked"} or byte_class in {"access_denied_page", "blocked_no_source_object"}:
        return "access_denied" if status == "access_denied" else "blocked", "Route did not yield a usable source object.", "try_alternate_route"
    if byte_class in {"metadata_record", "pubmed_record_or_abstract"}:
        return "metadata_only", "Attempt produced metadata/abstract-level evidence.", "try_fulltext_or_repository"
    if byte_class == "publisher_landing_or_abstract":
        return "abstract_or_landing_only", "Attempt produced landing/abstract detail but not a full source object.", "try_oa_or_repository"
    if status in {"local_file_found", "downloaded"} and level5 == "true":
        return "source_object_mirrored", "Attempt has a local or downloaded value-bearing source object.", "parse_or_verify"
    if status in {"local_file_found", "downloaded"}:
        return "manual_review", "Bytes exist but level-5 eligibility is not yet established.", "classify_source_object"
    if status == "remote_url_not_cached":
        return "not_retrieved", "Remote URL exists but was not mirrored in this pilot.", "download_or_resolve_lawful_copy"
    return "manual_review", "Attempt outcome needs review.", "review"


def level5_attempt_access_status(row: pd.Series) -> str:
    byte_class = safe_text(row.get("source_byte_class"))
    fetch_status = safe_text(row.get("fetch_status"))
    http_status = safe_text(row.get("http_status"))
    local_path = safe_text(row.get("local_path"))
    if byte_class == "paywall_or_login_page":
        return "login_required"
    if byte_class == "access_denied_page":
        return "access_denied"
    if byte_class in {"captcha_page", "blocked_no_source_object"} or fetch_status in {"blocked_http_status", "blocked_bot_or_captcha"}:
        return "blocked"
    if local_path:
        return "downloaded"
    if fetch_status == "request_failed":
        return "unresolved_locator"
    if http_status in {"401", "403"}:
        return "blocked"
    if http_status in {"404", "410"}:
        return "unresolved_locator"
    return "remote_url_not_cached"


def level5_attempt_decision(row: pd.Series) -> tuple[str, str, str]:
    byte_class = safe_text(row.get("source_byte_class"))
    eligible = safe_text(row.get("level5_eligible")).lower() == "true"
    if eligible:
        return "source_object_mirrored", "Level-5 resolver mirrored a plausible value-bearing source object.", "parse_or_verify"
    if byte_class == "paywall_or_login_page":
        return "paywall_or_login", "Resolver reached a paywall/login page, not a value-bearing source object.", "try_oa_or_manual_access"
    if byte_class == "captcha_page":
        return "captcha_or_bot_block", "Resolver reached CAPTCHA/bot-check page; automated retries should stop.", "manual_review"
    if byte_class == "access_denied_page":
        return "access_denied", "Resolver reached an access-denied artifact.", "try_alternate_route"
    if byte_class == "blocked_no_source_object":
        return "blocked", "Resolver was blocked before obtaining source bytes.", "try_alternate_route"
    if byte_class in {"metadata_record", "pubmed_record_or_abstract"}:
        return "metadata_only", "Resolver obtained only metadata/abstract bytes.", "try_fulltext_or_repository"
    if byte_class == "publisher_landing_or_abstract":
        return "abstract_or_landing_only", "Resolver obtained a landing/abstract page, not full source bytes.", "try_oa_or_repository"
    if byte_class == "not_retrieved":
        return "not_retrieved", "Resolver did not obtain bytes for this candidate.", "download_or_resolve_lawful_copy"
    return "manual_review", "Resolver output needs human classification before promotion.", "review"


def level5_attempt_retrieval_method(row: pd.Series) -> str:
    role = safe_text(row.get("attempt_role")).lower()
    strategy = safe_text(row.get("strategy_group"))
    byte_class = safe_text(row.get("source_byte_class"))
    if not safe_text(row.get("local_path")):
        return "not_retrieved"
    if "clinicaltrials" in role or role.endswith("_json") or "efetch" in role or strategy in {
        "pubmed_bridge",
        "pmc_fulltext",
        "crossref_metadata",
        "datacite_metadata",
        "openalex_metadata",
        "semantic_scholar_metadata",
        "europepmc_metadata",
    }:
        return "api_download"
    if byte_class in {"full_article_pdf", "full_article_xml", "full_article_html", "publisher_landing_or_abstract"}:
        return "automated_download"
    return "automated_download"


def level5_attempt_content_type_sniffed(row: pd.Series) -> str:
    byte_class = safe_text(row.get("source_byte_class"))
    content_type = safe_text(row.get("content_type")).lower()
    if byte_class.endswith("_pdf") or "pdf" in content_type:
        return "pdf"
    if byte_class.endswith("_xml") or "xml" in content_type:
        return "xml"
    if byte_class in {"full_article_html", "publisher_landing_or_abstract", "paywall_or_login_page", "captcha_page"} or "html" in content_type:
        return "html"
    if byte_class in {"registry_record_full", "metadata_record"} or "json" in content_type:
        return "json"
    return content_type or "unknown"


def level5_attempt_identity_decision(row: pd.Series) -> tuple[str, str]:
    if safe_text(row.get("level5_eligible")).lower() == "true":
        return "accepted_source_object_candidate", "Resolver classed local bytes as strict level-5 eligible; still needs value extraction for level 6."
    if safe_text(row.get("source_byte_class")) in {"blocked_no_source_object", "captcha_page", "paywall_or_login_page", "access_denied_page"}:
        return "rejected_access_blocker", "Candidate did not yield usable source bytes."
    return "needs_review", "Candidate may help routing but is not a strict source object."


def make_access_attempts(dictionary: pd.DataFrame, access: pd.DataFrame) -> pd.DataFrame:
    rows = []
    order_by_source: dict[str, int] = {}
    for _, row in access.iterrows():
        source_id = safe_text(row.get("source_id"))
        order_by_source[source_id] = order_by_source.get(source_id, 0) + 1
        decision, reason, next_action = access_attempt_decision(row)
        rows.append(
            {
                "attempt_id": "att_" + stable_hash(row.get("access_id"), source_id, row.get("remote_url"), order_by_source[source_id]),
                "source_id": source_id,
                "access_id": safe_text(row.get("access_id")),
                "attempt_group_id": "ag_" + stable_hash(source_id),
                "attempt_order": str(order_by_source[source_id]),
                "resolver_name": safe_text(row.get("access_strategy")) or "stable_url",
                "resolver_version": "pilot_backfill_v1",
                "resolver_strategy": safe_text(row.get("access_strategy")) or "stable_url",
                "candidate_rank": str(order_by_source[source_id]),
                "candidate_rank_reason": "Seeded from existing source_access row; not a full resolver-ranked candidate.",
                "candidate_url": safe_text(row.get("api_url")) or safe_text(row.get("remote_url")),
                "candidate_url_source": "source_access.tsv",
                "final_url": safe_text(row.get("final_url")) or safe_text(row.get("remote_url")),
                "host": safe_text(row.get("host")),
                "method": "local_file_check" if safe_text(row.get("local_path")) else "GET",
                "http_status": safe_text(row.get("http_status")),
                "redirect_chain": safe_text(row.get("redirect_chain")),
                "cache_key": stable_hash(row.get("access_id"), row.get("remote_url"), row.get("local_path")),
                "cache_hit_yn": "true" if safe_text(row.get("local_path")) else "false",
                "retry_count": "0",
                "retry_after_seconds": "",
                "content_type_header": "",
                "content_type_sniffed": safe_text(row.get("content_type")),
                "byte_count": safe_text(row.get("file_size_bytes")),
                "sha256": safe_text(row.get("file_sha256")),
                "local_path": safe_text(row.get("local_path")),
                "source_byte_class": safe_text(row.get("source_byte_class")),
                "access_status": safe_text(row.get("access_status")),
                "access_barrier": safe_text(row.get("access_barrier")),
                "abstract_or_detail_text": safe_text(row.get("abstract_or_detail_text")),
                "paywall_or_login_seen": safe_text(row.get("paywall_or_login_seen")) or "false",
                "captcha_or_bot_block_seen": safe_text(row.get("captcha_or_bot_block_seen")) or "false",
                "preprint_or_repository_candidate": safe_text(row.get("preprint_or_repository_candidate")) or "false",
                "license_url": safe_text(row.get("license_url")),
                "license_category": safe_text(row.get("license_category")) or "unknown",
                "storage_allowed": safe_text(row.get("storage_allowed")) or "unknown",
                "robots_status": "not_checked",
                "tdm_policy_status": "unknown",
                "title_match_score": "",
                "doi_match_score": "",
                "author_year_match_score": "",
                "identity_decision": "needs_review",
                "identity_decision_reason": "Pilot backfill did not rerun candidate identity scoring.",
                "retrieval_method": safe_text(row.get("retrieval_method")) or "not_retrieved",
                "retrieved_at": safe_text(row.get("retrieved_at")),
                "retrieved_by": safe_text(row.get("retrieved_by")) or "codex",
                "decision": decision,
                "decision_reason": reason,
                "stop_reason": "success" if decision == "source_object_mirrored" else "needs_review",
                "next_action": next_action,
                "notes": "Generated from source_access rows for the 300-row pilot; future resolver runs should add one row per candidate route.",
            }
        )
    level5_attempts = optional_level5_attempts()
    if not level5_attempts.empty:
        sr_source = read_tsv(SOURCE_RESULT_IN)[["source_result_id", "represented_source_id", "extraction_source_id"]]
        level5_attempts = level5_attempts.merge(sr_source, on="source_result_id", how="left")
        for _, row in level5_attempts.iterrows():
            source_id = safe_text(row.get("represented_source_id")) or safe_text(row.get("extraction_source_id"))
            order_by_source[source_id] = order_by_source.get(source_id, 0) + 1
            decision, reason, next_action = level5_attempt_decision(row)
            identity_decision, identity_reason = level5_attempt_identity_decision(row)
            local_path = safe_text(row.get("local_path"))
            byte_count = safe_text(row.get("content_length"))
            if local_path and Path(local_path).exists() and not byte_count:
                byte_count = str(Path(local_path).stat().st_size)
            rows.append(
                {
                    "attempt_id": "att_l5_" + stable_hash(
                        row.get("source_result_id"),
                        row.get("attempt_role"),
                        row.get("attempt_url"),
                        row.get("local_sha256"),
                        row.get("final_url"),
                    ),
                    "source_id": source_id,
                    "access_id": "",
                    "attempt_group_id": "ag_l5_" + stable_hash(row.get("source_result_id")),
                    "attempt_order": str(order_by_source[source_id]),
                    "resolver_name": safe_text(row.get("attempt_role")) or safe_text(row.get("strategy_group")) or "level5_probe",
                    "resolver_version": "push_schema_pilot_to_level5.py",
                    "resolver_strategy": safe_text(row.get("strategy_group")) or "other",
                    "candidate_rank": str(order_by_source[source_id]),
                    "candidate_rank_reason": "Candidate emitted by level-5 resolver probe; strict candidates are promoted only when level5_eligible=true.",
                    "candidate_url": safe_text(row.get("attempt_url")),
                    "candidate_url_source": safe_text(row.get("attempt_role")),
                    "final_url": safe_text(row.get("final_url")) or safe_text(row.get("attempt_url")),
                    "host": safe_text(urlparse(safe_text(row.get("final_url")) or safe_text(row.get("attempt_url"))).netloc),
                    "method": "GET",
                    "http_status": safe_text(row.get("http_status")),
                    "redirect_chain": "",
                    "cache_key": stable_hash(row.get("attempt_url"), row.get("final_url"), row.get("local_sha256")),
                    "cache_hit_yn": "false",
                    "retry_count": "0",
                    "retry_after_seconds": "",
                    "content_type_header": safe_text(row.get("content_type")),
                    "content_type_sniffed": level5_attempt_content_type_sniffed(row),
                    "byte_count": byte_count,
                    "sha256": safe_text(row.get("local_sha256")),
                    "local_path": local_path,
                    "source_byte_class": safe_text(row.get("source_byte_class")),
                    "access_status": level5_attempt_access_status(row),
                    "access_barrier": (
                        "paywall/login"
                        if safe_text(row.get("source_byte_class")) == "paywall_or_login_page"
                        else (
                            "captcha/bot"
                            if safe_text(row.get("source_byte_class")) == "captcha_page"
                            else ("http_" + safe_text(row.get("http_status")) if safe_text(row.get("fetch_status")).startswith("blocked") else "")
                        )
                    ),
                    "abstract_or_detail_text": safe_text(row.get("source_detail_text")),
                    "paywall_or_login_seen": bool_text(safe_text(row.get("source_byte_class")) == "paywall_or_login_page"),
                    "captcha_or_bot_block_seen": bool_text(safe_text(row.get("source_byte_class")) == "captcha_page"),
                    "preprint_or_repository_candidate": safe_text(row.get("strategy_is_preprint_or_repository_candidate")) or "false",
                    "license_url": "",
                    "license_category": "unknown",
                    "storage_allowed": "unknown",
                    "robots_status": "not_checked",
                    "tdm_policy_status": "unknown",
                    "title_match_score": "",
                    "doi_match_score": "",
                    "author_year_match_score": "",
                    "identity_decision": identity_decision,
                    "identity_decision_reason": identity_reason,
                    "retrieval_method": level5_attempt_retrieval_method(row),
                    "retrieved_at": TIMESTAMP,
                    "retrieved_by": "codex:push_schema_pilot_to_level5.py",
                    "decision": decision,
                    "decision_reason": reason,
                    "stop_reason": "success" if decision == "source_object_mirrored" else safe_text(row.get("fetch_status")) or "needs_review",
                    "next_action": next_action,
                    "notes": (
                        f"Level-5 probe candidate for source_result_id={safe_text(row.get('source_result_id'))}; "
                        f"previous_evidence={safe_text(row.get('previous_evidence_level_name'))}; "
                        f"fetch_note={safe_text(row.get('fetch_note'))}"
                    ),
                }
            )
    return conform(pd.DataFrame(rows), dictionary, "source_access_attempt.tsv")


def make_source_versions(dictionary: pd.DataFrame, source: pd.DataFrame, access: pd.DataFrame) -> pd.DataFrame:
    access_by_source: dict[str, pd.Series] = {}
    for _, row in access.iterrows():
        sid = safe_text(row.get("source_id"))
        if sid and sid not in access_by_source:
            access_by_source[sid] = row
    rows = []
    for _, row in source.iterrows():
        sid = safe_text(row.get("source_id"))
        access_row = access_by_source.get(sid, pd.Series(dtype=str))
        version_label = safe_text(access_row.get("source_version")) or "unknown"
        version_id = "ver_" + stable_hash(sid, version_label, row.get("doi"), row.get("url"))
        rows.append(
            {
                "source_version_id": version_id,
                "source_id": sid,
                "version_label": version_label,
                "version_number": "",
                "version_date": safe_text(row.get("publication_year")),
                "version_source": "source_access_inferred" if safe_text(access_row.get("source_version")) else "pilot_unknown",
                "is_version_of_source_id": "",
                "is_version_of_identifier": safe_text(row.get("doi")) or safe_text(row.get("registry_id")),
                "is_version_of_record": bool_text(version_label == "version_of_record"),
                "preprint_version_yn": bool_text(version_label == "preprint"),
                "accepted_manuscript_yn": bool_text(version_label in {"accepted_manuscript", "author_manuscript"}),
                "published_vor_yn": bool_text(version_label == "version_of_record"),
                "registry_version_yn": bool_text(version_label == "registry_record"),
                "repository_version_yn": bool_text(version_label in {"dataset", "code", "supplement"}),
                "correction_or_update_type": "",
                "superseded_by_source_version_id": "",
                "version_evidence_file_id": "",
                "version_evidence_text": "",
            }
        )
    return conform(pd.DataFrame(rows), dictionary, "source_version.tsv")


def make_source_files(dictionary: pd.DataFrame, access: pd.DataFrame, access_attempt: pd.DataFrame, source_version: pd.DataFrame) -> pd.DataFrame:
    attempt_by_access = dict(zip(access_attempt["access_id"].map(safe_text), access_attempt["attempt_id"].map(safe_text)))
    version_by_source = dict(zip(source_version["source_id"].map(safe_text), source_version["source_version_id"].map(safe_text)))
    rows = []
    seen_files: set[str] = set()
    for _, row in access.iterrows():
        local_path = safe_text(row.get("local_path"))
        if not local_path:
            continue
        sha = safe_text(row.get("file_sha256"))
        source_id = safe_text(row.get("source_id"))
        source_file_id = "file_" + stable_hash(sha or local_path, source_id)
        if source_file_id in seen_files:
            continue
        seen_files.add(source_file_id)
        filename = Path(local_path).name
        rows.append(
            {
                "source_file_id": source_file_id,
                "source_id": source_id,
                "access_id": safe_text(row.get("access_id")),
                "attempt_id": attempt_by_access.get(safe_text(row.get("access_id")), ""),
                "source_version_id": version_by_source.get(source_id, ""),
                "file_role": file_role_for_access(row),
                "file_origin": file_origin_for_access(row),
                "source_byte_class": safe_text(row.get("source_byte_class")),
                "url": safe_text(row.get("remote_url")) or safe_text(row.get("api_url")),
                "final_url": safe_text(row.get("final_url")),
                "storage_uri": local_path,
                "local_path": local_path,
                "filename_original": filename,
                "filename_normalized": filename,
                "media_type_reported": safe_text(row.get("content_type")),
                "media_type_sniffed": safe_text(row.get("content_type")),
                "byte_size": safe_text(row.get("file_size_bytes")),
                "sha256": sha,
                "provider_checksum_type": "",
                "provider_checksum_value": "",
                "content_fingerprint": "",
                "text_sha256": "",
                "archive_member_path": safe_text(row.get("file_member_path")),
                "parent_file_id": "",
                "page_count": "",
                "word_count": "",
                "extraction_ready_yn": bool_text(safe_text(row.get("source_byte_class")) not in {"paywall_or_login_page", "captcha_page", "access_denied_page", "not_retrieved"}),
                "level5_eligible": safe_text(row.get("level5_eligible")) or "false",
                "created_at": safe_text(row.get("retrieved_at")) or TIMESTAMP,
                "fixity_checked_at": safe_text(row.get("retrieved_at")) or TIMESTAMP,
                "notes": "Pilot source_file row generated from existing source_access local_path; future resolver should add provider checksums and extracted members.",
            }
        )
    for _, row in access_attempt.iterrows():
        local_path = safe_text(row.get("local_path"))
        if not local_path or safe_text(row.get("decision")) != "source_object_mirrored":
            continue
        source_id = safe_text(row.get("source_id"))
        sha = safe_text(row.get("sha256"))
        source_file_id = "file_l5_" + stable_hash(sha or local_path, source_id, row.get("attempt_id"))
        if source_file_id in seen_files:
            continue
        seen_files.add(source_file_id)
        filename = Path(local_path).name
        byte_size = safe_text(row.get("byte_count"))
        if local_path and Path(local_path).exists() and not byte_size:
            byte_size = str(Path(local_path).stat().st_size)
        rows.append(
            {
                "source_file_id": source_file_id,
                "source_id": source_id,
                "access_id": safe_text(row.get("access_id")),
                "attempt_id": safe_text(row.get("attempt_id")),
                "source_version_id": version_by_source.get(source_id, ""),
                "file_role": file_role_for_byte_class(row.get("source_byte_class")),
                "file_origin": file_origin_for_attempt(row),
                "source_byte_class": safe_text(row.get("source_byte_class")),
                "url": safe_text(row.get("candidate_url")),
                "final_url": safe_text(row.get("final_url")),
                "storage_uri": local_path,
                "local_path": local_path,
                "filename_original": filename,
                "filename_normalized": filename,
                "media_type_reported": safe_text(row.get("content_type_header")),
                "media_type_sniffed": safe_text(row.get("content_type_sniffed")),
                "byte_size": byte_size,
                "sha256": sha,
                "provider_checksum_type": "",
                "provider_checksum_value": "",
                "content_fingerprint": "",
                "text_sha256": "",
                "archive_member_path": "",
                "parent_file_id": "",
                "page_count": "",
                "word_count": "",
                "extraction_ready_yn": "true",
                "level5_eligible": "true",
                "created_at": safe_text(row.get("retrieved_at")) or TIMESTAMP,
                "fixity_checked_at": safe_text(row.get("retrieved_at")) or TIMESTAMP,
                "notes": "Level-5 resolver mirrored this source object; parse/extract D and N before promoting above level 5.",
            }
        )
    return conform(pd.DataFrame(rows), dictionary, "source_file.tsv")


def make_access_rights(dictionary: pd.DataFrame, source_file: pd.DataFrame, access: pd.DataFrame) -> pd.DataFrame:
    access_lookup = access.set_index("access_id", drop=False) if not access.empty else pd.DataFrame()
    rows = []
    for _, row in source_file.iterrows():
        access_id = safe_text(row.get("access_id"))
        access_row = access_lookup.loc[access_id] if access_id in getattr(access_lookup, "index", []) else pd.Series(dtype=str)
        storage_allowed = safe_text(access_row.get("storage_allowed")) or "unknown"
        license_category = safe_text(access_row.get("license_category")) or "unknown"
        file_origin = safe_text(row.get("file_origin"))
        if file_origin == "internal_derived":
            decision = "not_applicable"
            reason = "Internal derived table; original-source rights still need separate artifacts for publication-grade verification."
        elif safe_text(row.get("level5_eligible")) == "true" and license_category == "open":
            decision = "open_allowed"
            reason = "Open license/access indicated by source metadata."
        else:
            decision = "needs_review"
            reason = "Pilot backfill has not verified license/TDM/storage rights for this artifact."
        rows.append(
            {
                "access_right_id": "right_" + stable_hash(row.get("source_file_id"), access_id),
                "source_id": safe_text(row.get("source_id")),
                "source_file_id": safe_text(row.get("source_file_id")),
                "rights_scope": "source_file",
                "license_name": "",
                "license_spdx": "",
                "license_url": safe_text(access_row.get("license_url")),
                "license_category": license_category,
                "terms_url": "",
                "tdm_policy_url": "",
                "robots_status": "not_checked",
                "mirror_allowed_yn": storage_allowed,
                "text_extract_allowed_yn": "unknown",
                "redistribution_allowed_yn": "unknown",
                "share_scope": "metadata_only" if decision in {"needs_review", "not_applicable"} else "public",
                "institutional_license_yn": "false",
                "reviewed_by": "codex",
                "reviewed_at": TIMESTAMP,
                "rights_decision": decision,
                "rights_decision_reason": reason,
            }
        )
    return conform(pd.DataFrame(rows), dictionary, "source_access_right.tsv")


def make_source_results(dictionary: pd.DataFrame) -> pd.DataFrame:
    sr = read_tsv(SOURCE_RESULT_IN)
    human = read_tsv(HUMAN_IN)
    grounding = optional_grounding()
    raw_mapping = read_tsv(MAPPING_IN)
    keep = [
        "source_result_id",
        "source_directness",
        "source_family",
        "source_text_extraction_status",
        "human_check_text",
        "recovered_verbatim_effect_text",
        "recovered_verbatim_se_text",
        "recovered_verbatim_n_text",
        "recovered_verbatim_p_or_z_text",
        "recovered_transformation_explanation",
        "upstream_row_json",
        "plot_row_json",
        "recovered_raw_file_repo_relative",
        "recovered_raw_file_sha256",
    ]
    out = sr.merge(human[[column for column in keep if column in human.columns]], on="source_result_id", how="left")
    grounding_keep = [
        "source_result_id",
        "local_evidence_kind",
        "grounding_status",
        "literal_number_status",
        "crossref_resolution_status",
        "primary_real_world_url",
        "primary_real_world_url_basis",
        "source_bib_real_world_url",
        "number_verified_against_original_source",
    ]
    out = out.merge(grounding[[column for column in grounding_keep if column in grounding.columns]], on="source_result_id", how="left")
    out["result_label"] = out.apply(
        lambda row: safe_text(row.get("result_label"))
        or safe_text(row.get("outcome_label"))
        or safe_text(row.get("dot_record_id"))
        or safe_text(row.get("generated_result_citation_rendered"))
        or safe_text(row.get("source_result_id")),
        axis=1,
    )
    out["outcome_label"] = out.apply(lambda row: safe_text(row.get("outcome_label")) or safe_text(row.get("result_label")), axis=1)
    out["verbatim_source_row_text"] = out["upstream_row_json"].where(out["upstream_row_json"].map(safe_text).ne(""), out["plot_row_json"])
    out["verbatim_outcome_text"] = out["outcome_label"].where(out["outcome_label"].map(safe_text).ne(""), out["result_label"])
    out["verbatim_effect_text"] = out["recovered_verbatim_effect_text"]
    out["verbatim_se_text"] = out["recovered_verbatim_se_text"]
    out["verbatim_n_text"] = out["recovered_verbatim_n_text"]
    out["verbatim_p_text"] = out["recovered_verbatim_p_or_z_text"]
    out["native_effect_value"] = out["recovered_verbatim_effect_text"].map(numeric_text)
    out["native_effect_metric"] = out.apply(native_metric_for, axis=1)
    out["native_standard_error"] = out["recovered_verbatim_se_text"].map(numeric_text)
    out["native_ci_low"] = ""
    out["native_ci_high"] = ""
    out["native_p_value"] = out["recovered_verbatim_p_or_z_text"].map(numeric_text)
    out["native_n_total"] = out["recovered_verbatim_n_text"].map(numeric_text)
    out["standardized_effect_metric"] = "d_proxy"
    out["d_conversion_method"] = out.apply(conversion_method_for, axis=1)
    out["d_conversion_inputs"] = out.apply(
        lambda row: (
            f"verbatim_effect={safe_text(row.get('recovered_verbatim_effect_text'))}; "
            f"verbatim_n={safe_text(row.get('recovered_verbatim_n_text'))}; "
            f"verbatim_p_or_z={safe_text(row.get('recovered_verbatim_p_or_z_text'))}; "
            f"source_directness={safe_text(row.get('source_directness'))}"
        ),
        axis=1,
    )
    out["transformation_explanation"] = out["recovered_transformation_explanation"].where(
        out["recovered_transformation_explanation"].map(safe_text).ne(""),
        out["transformation_explanation"],
    )
    out["transformation_confidence"] = out.apply(confidence_for, axis=1)
    prereg_info = out.apply(prereg_kind_for, axis=1)
    out["prereg_status"] = [info[0] if is_prereg_candidate(row) else "unknown" for info, (_, row) in zip(prereg_info, out.iterrows())]
    out["prereg_timing"] = [info[1] if is_prereg_candidate(row) else "" for info, (_, row) in zip(prereg_info, out.iterrows())]
    out["prereg_mapping_id"] = out.apply(lambda row: prereg_mapping_id(row.get("source_result_id")) if is_prereg_candidate(row) else "", axis=1)
    out["prereg_source_id"] = out.apply(
        lambda row: prereg_source_id_for(row) if is_prereg_candidate(row) else "",
        axis=1,
    )
    out["prereg_url"] = out.apply(
        lambda row: prereg_artifact_url_for(row) if is_prereg_candidate(row) else "",
        axis=1,
    )
    out["prereg_registered_at"] = ""
    out["prereg_selector_locator"] = out.apply(
        lambda row: safe_text(row.get("source_locator")) if is_prereg_candidate(row) else "",
        axis=1,
    )
    out["prereg_selector_verbatim_text"] = out.apply(
        lambda row: (safe_text(row.get("verbatim_outcome_text")) or safe_text(row.get("result_label"))) if is_prereg_candidate(row) else "",
        axis=1,
    )
    out["prereg_hypothesis_id"] = ""
    out["prereg_outcome_id"] = out.apply(
        lambda row: safe_text(row.get("result_label")) if is_prereg_candidate(row) else "",
        axis=1,
    )
    out["selector_status"] = out["source_directness"].map(
        lambda directness: "database_primary_outcome" if safe_text(directness) == "raw_ctgov_registry_row" else "corpus_focal_claim"
    )
    out["selector_rule"] = out.apply(
        lambda row: (
            "ClinicalTrials.gov/AACT selected primary randomized eligible outcome"
            if nct_id_from_row(row)
            else (
                "preregistered selector asserted by source family or registry metadata"
                if is_prereg_candidate(row)
                else "corpus/database focal result as imported by upstream extractor"
            )
        ),
        axis=1,
    )
    out["selector_mapping_id"] = out["prereg_mapping_id"]
    out["replication_mapping_id"] = out.apply(
        lambda row: replication_mapping_id_from_pair(replication_pair_id_for(row), row.get("source_result_id")) if is_replication_candidate(row) else "",
        axis=1,
    )
    out["replication_role"] = out.apply(lambda row: replication_role_for(row) if is_replication_candidate(row) else "none", axis=1)
    out["replication_pair_id"] = out.apply(lambda row: replication_pair_id_for(row) if is_replication_candidate(row) else "", axis=1)
    out["replication_kind"] = out.apply(lambda row: replication_kind_for(row) if is_replication_candidate(row) else "", axis=1)
    out["replication_target_claim"] = out.apply(lambda row: replication_target_claim_for(row) if is_replication_candidate(row) else "", axis=1)
    if "mapping_id" in raw_mapping.columns and "source_result_id" in raw_mapping.columns:
        generic_lookup = dict(zip(raw_mapping["source_result_id"].map(safe_text), raw_mapping["mapping_id"].map(safe_text)))
    else:
        generic_lookup = {}
    out["source_mapping_ids"] = out.apply(
        lambda row: " | ".join(
            x
            for x in [
                generic_lookup.get(safe_text(row.get("source_result_id")), ""),
                safe_text(row.get("prereg_mapping_id")),
                safe_text(row.get("replication_mapping_id")),
            ]
            if x
        ),
        axis=1,
    )
    for pair_id, pair_rows in out[out["replication_pair_id"].map(safe_text).ne("")].groupby("replication_pair_id", dropna=False):
        original_ids = pair_rows.loc[pair_rows["replication_role"].eq("original_study"), "source_result_id"].map(safe_text).tolist()
        replication_ids = pair_rows.loc[pair_rows["replication_role"].eq("replication_study"), "source_result_id"].map(safe_text).tolist()
        if original_ids:
            out.loc[out["replication_pair_id"].eq(pair_id), "replication_original_result_id"] = " | ".join(original_ids)
        if replication_ids:
            out.loc[out["replication_pair_id"].eq(pair_id), "replication_replicating_result_id"] = " | ".join(replication_ids)
    out["extraction_confidence"] = out.apply(confidence_for, axis=1)
    out["human_check_status"] = out["source_text_extraction_status"]
    derived = {
        "plot_row_only",
        "candidate_child_numeric_row",
        "candidate_paper_numeric_row",
        "replication_pair_source_row",
        "staged_replication_pair_source_row",
    }
    out["coding_status"] = out.apply(
        lambda row: (
            "coded_with_schema_gaps"
            if safe_text(row.get("source_directness")) in derived
            or safe_text(row.get("source_text_extraction_status")) != "source_cells_recovered"
            else "fully_coded"
        ),
        axis=1,
    )
    evidence = out.apply(evidence_level_for, axis=1)
    out["evidence_level"] = [level for level, _ in evidence]
    out["evidence_level_name"] = [name for _, name in evidence]
    strict_l5_ids = strict_level5_source_result_ids()
    if strict_l5_ids:
        promote_mask = out["source_result_id"].map(safe_text).isin(strict_l5_ids) & (out["evidence_level"].astype(int) < 5)
        out.loc[promote_mask, "evidence_level"] = 5
        out.loc[promote_mask, "evidence_level_name"] = "original_source_obtained"
    strict_l6_ids = strict_level6_source_result_ids()
    if strict_l6_ids:
        promote_mask = out["source_result_id"].map(safe_text).isin(strict_l6_ids) & (out["evidence_level"].astype(int) < 6)
        out.loc[promote_mask, "evidence_level"] = 6
        out.loc[promote_mask, "evidence_level_name"] = "original_number_extracted"
    states = out.apply(target_and_value_states, axis=1)
    out["target_acquisition_state"] = [state for state, _ in states]
    out["value_verification_state"] = [state for _, state in states]
    out["source_is_original"] = out["evidence_level_name"].isin(["original_source_obtained", "original_number_extracted", "recomputed_from_raw"]).map(bool_text)
    out["number_verified_by_us"] = out["evidence_level_name"].isin(["original_number_extracted", "recomputed_from_raw"]).map(bool_text)
    out["represented_work_identified"] = out["evidence_level_name"].isin(
        [
            "external_assertion_with_target_source",
            "target_source_independently_grounded",
            "original_source_obtained",
            "original_number_extracted",
            "recomputed_from_raw",
        ]
    ).map(bool_text)
    out["source_is_external"] = out.apply(
        lambda row: bool_text(safe_text(row.get("local_evidence_kind")) not in {"", "internal_derived_table"} or int(row.get("evidence_level") or 0) >= 5),
        axis=1,
    )
    out["requires_manual_review"] = out.apply(
        lambda row: bool_text(
            int(row.get("evidence_level") or 0) < 5
            or safe_text(row.get("crossref_resolution_status")) == "candidate_low_similarity"
            or (int(row.get("evidence_level") or 0) < 6 and safe_text(row.get("coding_status")) != "fully_coded")
        ),
        axis=1,
    )
    out["conversion_verified"] = out.apply(
        lambda row: bool_text(
            int(row.get("evidence_level") or 0) >= 6
            and safe_text(row.get("d_conversion_method")) not in {"blocked_missing_inputs", "no_d_native_metric"}
        ),
        axis=1,
    )
    out["citation_status"] = out.apply(citation_status_for, axis=1)
    out["represented_source_citation_rendered"] = out["represented_source_citation_rendered"].where(
        ~out["represented_source_citation_rendered"].str.contains("PublishedSmallNStudiesDon-tMatter dot-level extraction", na=False),
        "",
    )
    out["notes"] = out.apply(
        lambda row: (
            f"human_check_text={safe_text(row.get('human_check_text'))}; "
            f"recovered_raw_file={safe_text(row.get('recovered_raw_file_repo_relative'))}; "
            f"recovered_raw_file_sha256={safe_text(row.get('recovered_raw_file_sha256'))}"
            + (
                "; level5_probe=strict source object mirrored; D/N value text not yet re-extracted from that object"
                if safe_text(row.get("source_result_id")) in strict_l5_ids and safe_text(row.get("value_verification_state")) == "source_object_obtained_not_parsed"
                else ""
            )
            + (
                "; level6_verifier=plotted D/N recomputed from mirrored source object"
                if safe_text(row.get("source_result_id")) in strict_l6_ids
                else ""
            )
        ),
        axis=1,
    )
    return conform(out, dictionary, "source_result.tsv")


def make_canonical(dictionary: pd.DataFrame, source_result: pd.DataFrame) -> pd.DataFrame:
    canonical = read_tsv(CANONICAL_IN)
    sr_lookup = source_result.set_index("source_result_id", drop=False)
    rows = []
    for _, row in canonical.iterrows():
        srid = safe_text(row.get("preferred_source_result_id"))
        sr = sr_lookup.loc[srid] if srid in sr_lookup.index else pd.Series(dtype=str)
        count = safe_text(row.get("source_result_count_in_sample")) or "1"
        rows.append(
            {
                **row.to_dict(),
                "result_label": safe_text(row.get("result_label")) or safe_text(sr.get("result_label")) or safe_text(srid),
                "source_result_count": count,
                "effect_metric_for_plot": safe_text(sr.get("standardized_effect_metric")) or "d_proxy",
                "panel": panel_for(row.get("plot_names")),
                "row_unit": safe_text(row.get("plot_names")) or "sampled_plot_dot",
                "aggregation_rule": "single sampled source-result" if count == "1" else "preferred sampled source-result",
                "D_min": row.get("D"),
                "D_median": row.get("D"),
                "D_max": row.get("D"),
                "N_min": row.get("N"),
                "N_median": row.get("N"),
                "N_max": row.get("N"),
                "resolution_status": "single_source_result" if count == "1" else "multiple_source_results_need_resolution",
            }
        )
    return conform(pd.DataFrame(rows), dictionary, "canonical_result.tsv")


def make_source_identifier(dictionary: pd.DataFrame, source: pd.DataFrame, source_result: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, str]] = []
    seen: set[tuple[str, str, str]] = set()
    primary_by_source: dict[str, str] = {}
    grounding = optional_grounding()
    sr_key = source_result[["source_result_id", "represented_source_id"]].copy()
    if not grounding.empty:
        enriched = sr_key.merge(grounding, on="source_result_id", how="left")
        for _, row in enriched.iterrows():
            sid = safe_text(row.get("represented_source_id"))
            if sid and sid not in primary_by_source:
                primary_by_source[sid] = safe_text(row.get("primary_real_world_url"))

    for _, row in source.iterrows():
        sid = safe_text(row.get("source_id"))
        primary_url = primary_by_source.get(sid, safe_text(row.get("url")))
        doi = normalized_doi(row.get("doi"))
        add_identifier(rows, seen, sid, "doi", doi, doi_url(doi), "source.tsv", bool(doi and doi_url(doi) == primary_url), "high")
        pmid = safe_text(row.get("pmid"))
        add_identifier(rows, seen, sid, "pmid", pmid, f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else "", "source.tsv", bool(pmid and pmid in primary_url), "high")
        registry_id = safe_text(row.get("registry_id"))
        if registry_id:
            if re.match(r"^NCT\d{8}$", registry_id, flags=re.I):
                add_identifier(rows, seen, sid, "nct", registry_id.upper(), nct_url(registry_id), "source.tsv", nct_url(registry_id) == primary_url, "high")
            elif registry_id.lower().startswith("trials/") or registry_id.isdigit():
                add_identifier(rows, seen, sid, "aea_trial", registry_id, aea_trial_url(registry_id), "source.tsv", aea_trial_url(registry_id) == primary_url, "high")
            else:
                add_identifier(rows, seen, sid, "other", registry_id, "", "source.tsv", False, "medium")
        url = safe_text(row.get("url"))
        add_identifier(rows, seen, sid, "url", url, url, "source.tsv", bool(url and url == primary_url), "medium")

    if not grounding.empty:
        enriched = sr_key.merge(grounding, on="source_result_id", how="left")
        for _, row in enriched.iterrows():
            sid = safe_text(row.get("represented_source_id"))
            primary_url = safe_text(row.get("primary_real_world_url"))
            for doi in split_pipe_values(row.get("doi_list")):
                doi = normalized_doi(doi)
                add_identifier(rows, seen, sid, "doi", doi, doi_url(doi), "real_world_grounding_sample_300.tsv", doi_url(doi) == primary_url, "high")
            for pmid in split_pipe_values(row.get("pmid_list")):
                add_identifier(rows, seen, sid, "pmid", pmid, f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/", "real_world_grounding_sample_300.tsv", pmid in primary_url, "high")
            for pmcid in split_pipe_values(row.get("pmcid_list")):
                value = pmcid.upper() if pmcid.upper().startswith("PMC") else f"PMC{pmcid}"
                add_identifier(rows, seen, sid, "pmcid", value, pmcid_url(value), "real_world_grounding_sample_300.tsv", pmcid_url(value) == primary_url, "high")
            for nct in split_pipe_values(row.get("nct_list")):
                add_identifier(rows, seen, sid, "nct", nct.upper(), nct_url(nct), "real_world_grounding_sample_300.tsv", nct_url(nct) == primary_url, "high")
            for aea in split_pipe_values(row.get("aea_trial_list")):
                add_identifier(rows, seen, sid, "aea_trial", aea, aea_trial_url(aea), "real_world_grounding_sample_300.tsv", aea_trial_url(aea) == primary_url, "high")
            for url in [primary_url, *split_pipe_values(row.get("url_list")), safe_text(row.get("source_bib_real_world_url"))]:
                add_identifier(rows, seen, sid, "url", url, url, "real_world_grounding_sample_300.tsv", bool(url and url == primary_url), "medium")

    return conform(pd.DataFrame(rows), dictionary, "source_identifier.tsv")


def make_source_classification(dictionary: pd.DataFrame, source_result: pd.DataFrame) -> pd.DataFrame:
    human = read_tsv(HUMAN_IN)
    rows: list[dict[str, str]] = []
    seen: set[tuple[str, str, str]] = set()
    sr_keep = ["source_result_id", "extraction_source_id", "represented_source_id"]
    merged = human.merge(source_result[[c for c in sr_keep if c in source_result.columns]], on="source_result_id", how="left")
    for _, row in merged.iterrows():
        source_family = safe_text(row.get("source_family"))
        field, field_source, field_confidence = field_from_row(row)
        for sid_key in ["represented_source_id", "extraction_source_id"]:
            sid = safe_text(row.get(sid_key))
            add_classification(rows, seen, sid, "source_family", source_family, "human_check_source_result_sample_300.tsv", "medium")
            add_classification(rows, seen, sid, "field", field, field_source, field_confidence)
        directness = safe_text(row.get("source_directness"))
        design = ""
        if directness == "raw_ctgov_registry_row":
            design = "clinical trial registry result"
        elif "replication" in directness:
            design = "replication pair"
        elif directness == "political_science_component_rows":
            design = "field experiment component row"
        elif directness in {"candidate_child_numeric_row", "candidate_paper_numeric_row"}:
            design = "corpus extracted result"
        if design:
            add_classification(rows, seen, row.get("represented_source_id"), "study_design", design, "source_directness", "medium")
    return conform(pd.DataFrame(rows), dictionary, "source_classification.tsv")


def make_canonical_membership(dictionary: pd.DataFrame, canonical: pd.DataFrame, source_result: pd.DataFrame) -> pd.DataFrame:
    preferred_lookup = dict(zip(canonical["canonical_result_id"].map(safe_text), canonical["preferred_source_result_id"].map(safe_text)))
    rows = []
    for _, row in source_result.iterrows():
        canonical_id = safe_text(row.get("canonical_result_id"))
        source_result_id = safe_text(row.get("source_result_id"))
        role = "preferred" if preferred_lookup.get(canonical_id) == source_result_id else "child"
        rows.append(
            {
                "canonical_result_id": canonical_id,
                "source_result_id": source_result_id,
                "membership_role": role,
                "included_in_collapse": "true",
                "included_in_statistics": "false",
                "aggregation_role": "preferred_source" if role == "preferred" else "sampled_child_source",
                "weight": "",
                "notes": "Pilot membership generated from sampled source_result rows; full parent-child lists are not reconstructed beyond the 300-row pilot.",
            }
        )
    return conform(pd.DataFrame(rows), dictionary, "canonical_result_membership.tsv")


def make_source_result_support(dictionary: pd.DataFrame, source_result: pd.DataFrame, source_file: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, str]] = []
    seen: set[tuple[str, str, str, str, str, str]] = set()
    file_by_access = dict(zip(source_file["access_id"].map(safe_text), source_file["source_file_id"].map(safe_text))) if not source_file.empty else {}
    file_by_local_path = dict(zip(source_file["local_path"].map(safe_text), source_file["source_file_id"].map(safe_text))) if not source_file.empty else {}

    def add_support(
        row: pd.Series,
        source_id: object,
        role: str,
        text: object,
        locator: object = "",
        confidence: object = "",
        notes: str = "",
    ) -> None:
        source_result_id = safe_text(row.get("source_result_id"))
        sid = safe_text(source_id)
        support_text = safe_text(text)
        if not source_result_id or not sid or not support_text:
            return
        access_id = safe_text(row.get("access_id"))
        loc = safe_text(locator) or safe_text(row.get("source_locator"))
        key = (source_result_id, sid, access_id, role, loc, support_text)
        if key in seen:
            return
        seen.add(key)
        rows.append(
            {
                "source_result_id": source_result_id,
                "source_id": sid,
                "access_id": access_id,
                "source_file_id": file_by_access.get(access_id, ""),
                "support_role": role,
                "support_locator": loc,
                "support_locator_type": "source_locator",
                "page_number": "",
                "section_heading": "",
                "table_number": "",
                "figure_number": "",
                "cell_locator": "",
                "char_start": "",
                "char_end": "",
                "xml_xpath": "",
                "html_css_selector": "",
                "pdf_bbox": "",
                "support_verbatim_text": support_text,
                "verbatim_snippet_hash": stable_hash(support_text, length=16),
                "copied_text_allowed_yn": "unknown",
                "support_confidence": safe_text(confidence) or safe_text(row.get("extraction_confidence")) or "medium",
                "notes": notes,
            }
        )

    for _, row in source_result.iterrows():
        extraction_source_id = safe_text(row.get("extraction_source_id"))
        represented_source_id = safe_text(row.get("represented_source_id"))
        add_support(row, extraction_source_id, "effect_text", row.get("verbatim_effect_text"))
        add_support(row, extraction_source_id, "n_text", row.get("verbatim_n_text"))
        add_support(row, extraction_source_id, "outcome_text", row.get("verbatim_outcome_text"))
        add_support(row, extraction_source_id, "conversion_input", row.get("d_conversion_inputs"), notes="Transformation input string generated from recovered source cells.")
        add_support(row, represented_source_id, "bibliographic_identity", row.get("represented_source_citation_rendered"), confidence="medium")
        if safe_text(row.get("prereg_selector_verbatim_text")):
            add_support(
                row,
                safe_text(row.get("prereg_source_id")) or extraction_source_id,
                "selector_text",
                row.get("prereg_selector_verbatim_text"),
                row.get("prereg_selector_locator"),
                "medium",
                "Pre-registration selector evidence for the represented result.",
            )
        if safe_text(row.get("replication_mapping_id")):
            add_support(
                row,
                extraction_source_id,
                "relationship_evidence",
                row.get("replication_target_claim"),
                row.get("source_locator"),
                "medium",
                "Replication relationship asserted by source corpus or package row.",
            )
    level5_attempts = optional_level5_attempts()
    if not level5_attempts.empty and not source_file.empty:
        sr_lookup = source_result.set_index("source_result_id", drop=False)
        eligible = level5_attempts[level5_attempts.get("level5_eligible", "").map(safe_text).eq("true")]
        for _, attempt in eligible.iterrows():
            srid = safe_text(attempt.get("source_result_id"))
            if srid not in sr_lookup.index:
                continue
            row = sr_lookup.loc[srid]
            local_path = safe_text(attempt.get("local_path"))
            source_file_id = file_by_local_path.get(local_path, "")
            if not source_file_id:
                continue
            sid = safe_text(row.get("represented_source_id"))
            support_text = (
                f"Strict level-5 source object mirrored from {safe_text(attempt.get('final_url')) or safe_text(attempt.get('attempt_url'))}; "
                f"byte_class={safe_text(attempt.get('source_byte_class'))}; "
                f"local_path={local_path}; sha256={safe_text(attempt.get('local_sha256'))}."
            )
            key = (srid, sid, "", "access_grounding", local_path, support_text)
            if key in seen:
                continue
            seen.add(key)
            rows.append(
                {
                    "source_result_id": srid,
                    "source_id": sid,
                    "access_id": "",
                    "source_file_id": source_file_id,
                    "support_role": "access_grounding",
                    "support_locator": safe_text(attempt.get("final_url")) or safe_text(attempt.get("attempt_url")),
                    "support_locator_type": "source_object_url",
                    "page_number": "",
                    "section_heading": "",
                    "table_number": "",
                    "figure_number": "",
                    "cell_locator": "",
                    "char_start": "",
                    "char_end": "",
                    "xml_xpath": "",
                    "html_css_selector": "",
                    "pdf_bbox": "",
                    "support_verbatim_text": support_text,
                    "verbatim_snippet_hash": stable_hash(support_text, length=16),
                    "copied_text_allowed_yn": "unknown",
                    "support_confidence": "medium",
                    "notes": "This supports level 5 acquisition only; it is not proof that the plotted D/N value has been parsed from this object.",
                }
            )
    return conform(pd.DataFrame(rows), dictionary, "source_result_support.tsv")


def make_plot_membership(dictionary: pd.DataFrame, canonical: pd.DataFrame, source_result: pd.DataFrame) -> pd.DataFrame:
    human = read_tsv(HUMAN_IN)
    sr_keep = ["source_result_id", "canonical_result_id"]
    merged = human.merge(source_result[[c for c in sr_keep if c in source_result.columns]], on="source_result_id", how="left")
    plot_rows = []
    seen: set[tuple[str, str]] = set()
    for _, row in merged.iterrows():
        canonical_id = safe_text(row.get("canonical_result_id"))
        plot_id = plot_id_for(row.get("plot_name"))
        key = (plot_id, canonical_id)
        if not canonical_id or key in seen:
            continue
        seen.add(key)
        field, _, _ = field_from_row(row)
        plot_rows.append(
            {
                "plot_id": plot_id,
                "plot_universe_id": plot_universe_id_for(row.get("plot_name")),
                "canonical_result_id": canonical_id,
                "criteria_version": f"schema_pilot_{SAMPLE_SUFFIX}",
                "decision_context_type": "current_plot",
                "eligibility_status": "included",
                "included_in_plot": "true",
                "included_in_statistics": "true",
                "passed_criteria_ids": "",
                "failed_criteria_ids": "",
                "caveat_criteria_ids": "",
                "decision_basis": "Sampled from the current plotted dot membership table; full criterion replay is staged for the YAML-backed plot universe layer.",
                "decision_source": "scripts/build_codebook_pilot_sample.py",
                "decided_at": "",
                "plot_field": field,
                "plot_source_family": safe_text(row.get("source_family")),
                "render_order_group_count": "",
                "style_group": field or safe_text(row.get("source_family")),
                "exclusion_reason": "",
                "notes": "Pilot plot membership generated from sampled plot row; render_order_group_count is computed within the 300-row pilot only.",
            }
        )
    out = pd.DataFrame(plot_rows)
    if not out.empty:
        counts = out.groupby(["plot_id", "plot_field"], dropna=False)["canonical_result_id"].transform("count")
        out["render_order_group_count"] = counts.astype(str)
    return conform(out, dictionary, "plot_membership.tsv")


def generic_relationship_type(row: pd.Series) -> str:
    directness = safe_text(row.get("source_directness"))
    family = safe_text(row.get("source_family")).lower()
    if directness == "raw_ctgov_registry_row" or "ctgov" in family or nct_id_from_row(row):
        return "database_reports_paper_result"
    if is_replication_candidate(row):
        return "corpus_asserts_result_for_paper"
    if directness in {"candidate_child_numeric_row", "candidate_paper_numeric_row"}:
        return "corpus_asserts_result_for_paper"
    if directness == "political_science_component_rows":
        return "repository_supports_paper"
    return "extraction_source_reports_result_for_represented_source"


def generic_relationship_subtype(row: pd.Series) -> str:
    directness = safe_text(row.get("source_directness"))
    family = safe_text(row.get("source_family")).lower()
    if directness == "raw_ctgov_registry_row" or "ctgov" in family or nct_id_from_row(row):
        return "trial_registry_record"
    if is_replication_candidate(row):
        return replication_kind_for(row)
    if directness in {"candidate_child_numeric_row", "candidate_paper_numeric_row"}:
        return "database_child_result"
    if directness == "political_science_component_rows":
        return "data_or_code_package"
    return "unknown"


def mapping_evidence_type_for(row: pd.Series) -> str:
    directness = safe_text(row.get("source_directness"))
    if directness in {"replication_pair_source_row", "staged_replication_pair_source_row", "political_science_component_rows"}:
        return "code_or_package_manifest"
    if directness == "plot_row_only":
        return "manual_judgment"
    return "metadata_field"


def make_mapping(dictionary: pd.DataFrame, source_result: pd.DataFrame) -> pd.DataFrame:
    base = read_tsv(MAPPING_IN)
    human = read_tsv(HUMAN_IN)
    grounding = optional_grounding()
    sr_keep = [
        "source_result_id",
        "extraction_source_id",
        "represented_source_id",
        "access_id",
        "source_locator",
        "result_label",
        "outcome_label",
        "verbatim_source_row_text",
        "verbatim_outcome_text",
        "prereg_status",
        "prereg_mapping_id",
        "prereg_source_id",
        "prereg_url",
        "prereg_registered_at",
        "prereg_timing",
        "prereg_selector_locator",
        "prereg_selector_verbatim_text",
        "prereg_hypothesis_id",
        "prereg_outcome_id",
        "replication_mapping_id",
        "replication_role",
        "replication_pair_id",
        "replication_kind",
        "replication_target_claim",
        "replication_original_result_id",
        "replication_replicating_result_id",
    ]
    merged = base.merge(source_result[[c for c in sr_keep if c in source_result.columns]], on="source_result_id", how="left")
    human_keep = [
        "source_result_id",
        "source_family",
        "source_directness",
        "human_check_text",
        "upstream_row_json",
        "plot_row_json",
    ]
    merged = merged.merge(human[[c for c in human_keep if c in human.columns]], on="source_result_id", how="left")
    grounding_keep = [
        "source_result_id",
        "doi_list",
        "pmid_list",
        "pmcid_list",
        "nct_list",
        "url_list",
        "aea_trial_list",
        "primary_real_world_url",
        "primary_real_world_url_basis",
        "local_evidence_kind",
    ]
    merged = merged.merge(grounding[[c for c in grounding_keep if c in grounding.columns]], on="source_result_id", how="left")

    generic_rows: list[dict[str, str]] = []
    for _, row in merged.iterrows():
        external_id = nct_id_from_row(row) or first_pipe_value(row.get("doi_list")) or safe_text(row.get("replication_pair_id"))
        generic_rows.append(
            {
                "mapping_id": safe_text(row.get("mapping_id")),
                "from_source_id": safe_text(row.get("from_source_id")),
                "to_source_id": safe_text(row.get("to_source_id")),
                "relationship_type": generic_relationship_type(row),
                "relationship_subtype": generic_relationship_subtype(row),
                "mapping_assertion_source_id": safe_text(row.get("extraction_source_id")) or safe_text(row.get("from_source_id")),
                "mapping_assertion_access_id": safe_text(row.get("access_id")),
                "mapping_assertion_locator": safe_text(row.get("source_locator")),
                "mapping_assertion_url": safe_text(row.get("primary_real_world_url")),
                "mapping_assertion_verbatim_text": compact_mapping_text(row),
                "mapping_evidence_type": mapping_evidence_type_for(row),
                "external_relationship_id": external_id,
                "external_relationship_url": safe_text(row.get("primary_real_world_url")) or doi_url(external_id),
                "relationship_date": "",
                "relationship_updated_at": "",
                "relationship_timing": "not_applicable",
                "collection_role": "sampled_child_result",
                "dedupe_group_id": safe_text(row.get("replication_pair_id")) or safe_text(row.get("canonical_result_id")),
                "relationship_confidence": safe_text(row.get("relationship_confidence")) or "medium",
                "notes": f"source_result_id={safe_text(row.get('source_result_id'))}; {safe_text(row.get('notes'))}",
            }
        )

    prereg_rows: list[dict[str, str]] = []
    for _, row in merged.iterrows():
        if not safe_text(row.get("prereg_mapping_id")):
            continue
        status, timing, registry, registration_id, document_type = prereg_kind_for(row)
        nct = nct_id_from_row(row)
        assertion_url = safe_text(row.get("prereg_url"))
        if nct and not assertion_url:
            assertion_url = f"https://clinicaltrials.gov/study/{nct}"
        if registry or nct:
            relationship_type = "registry_preregisters_study"
        elif document_type == "registered_report_protocol":
            relationship_type = "registered_report_protocol_for_paper"
        elif document_type == "corpus_preregistration_indicator":
            relationship_type = "corpus_asserts_preregistration_for_paper"
        else:
            relationship_type = "pre_analysis_plan_supports_study"
        subtype = "trial_registry_record" if nct else ("pre_analysis_plan" if "PAP" in document_type.upper() else "preregistration")
        prereg_rows.append(
            {
                "mapping_id": safe_text(row.get("prereg_mapping_id")),
                "from_source_id": safe_text(row.get("prereg_source_id")) or safe_text(row.get("represented_source_id")),
                "to_source_id": safe_text(row.get("represented_source_id")),
                "relationship_type": relationship_type,
                "relationship_subtype": subtype,
                "mapping_assertion_source_id": safe_text(row.get("extraction_source_id")),
                "mapping_assertion_access_id": safe_text(row.get("access_id")),
                "mapping_assertion_locator": safe_text(row.get("prereg_selector_locator")) or safe_text(row.get("source_locator")),
                "mapping_assertion_url": assertion_url,
                "mapping_assertion_verbatim_text": safe_text(row.get("prereg_selector_verbatim_text")) or compact_mapping_text(row),
                "mapping_evidence_type": "registry_link" if registry or nct else "metadata_field",
                "external_relationship_id": registration_id or nct,
                "external_relationship_url": assertion_url,
                "relationship_date": safe_text(row.get("prereg_registered_at")),
                "relationship_updated_at": "",
                "relationship_timing": timing if timing in {"pre_data_collection", "pre_analysis", "post_data_pre_results", "post_results", "not_applicable", "unknown"} else "unknown",
                "prereg_registry_name": registry,
                "prereg_registration_id": registration_id or nct,
                "prereg_document_type": document_type,
                "prereg_primary_outcome_text": safe_text(row.get("prereg_selector_verbatim_text")),
                "prereg_hypothesis_text": "",
                "collection_role": "preregistration_artifact",
                "dedupe_group_id": safe_text(row.get("represented_source_id")),
                "relationship_confidence": "high" if nct else ("medium" if registry or assertion_url else "low"),
                "notes": f"Prereg/PAP mapping inferred for source_result_id={safe_text(row.get('source_result_id'))}; status={status}.",
            }
        )

    replication_rows: dict[str, dict[str, str]] = {}
    for _, row in merged.iterrows():
        if not safe_text(row.get("replication_mapping_id")):
            continue
        upstream, plot = row_jsons(row)
        original_doi = safe_text(upstream.get("original_doi")) or safe_text(plot.get("original_doi"))
        replication_doi = safe_text(upstream.get("replication_doi")) or safe_text(plot.get("replication_doi"))
        mapping_id = safe_text(row.get("replication_mapping_id"))
        existing = replication_rows.get(mapping_id, {})
        original_ids = {x for x in safe_text(existing.get("replication_original_result_id")).split(" | ") if x}
        replicating_ids = {x for x in safe_text(existing.get("replication_replicating_result_id")).split(" | ") if x}
        if safe_text(row.get("replication_role")) == "original_study":
            original_ids.add(safe_text(row.get("source_result_id")))
        if safe_text(row.get("replication_role")) == "replication_study":
            replicating_ids.add(safe_text(row.get("source_result_id")))
        if safe_text(row.get("replication_original_result_id")):
            original_ids.update(x for x in safe_text(row.get("replication_original_result_id")).split(" | ") if x)
        if safe_text(row.get("replication_replicating_result_id")):
            replicating_ids.update(x for x in safe_text(row.get("replication_replicating_result_id")).split(" | ") if x)
        replication_rows[mapping_id] = {
            "mapping_id": mapping_id,
            "from_source_id": safe_text(row.get("extraction_source_id")),
            "to_source_id": safe_text(row.get("represented_source_id")),
            "relationship_type": "corpus_asserts_result_for_paper",
            "relationship_subtype": safe_text(row.get("replication_kind")) or replication_kind_for(row),
            "mapping_assertion_source_id": safe_text(row.get("extraction_source_id")),
            "mapping_assertion_access_id": safe_text(row.get("access_id")),
            "mapping_assertion_locator": safe_text(row.get("source_locator")),
            "mapping_assertion_url": safe_text(row.get("primary_real_world_url")) or doi_url(original_doi) or doi_url(replication_doi),
            "mapping_assertion_verbatim_text": compact_mapping_text(row),
            "mapping_evidence_type": "code_or_package_manifest",
            "external_relationship_id": safe_text(row.get("replication_pair_id")),
            "external_relationship_url": " | ".join(x for x in [doi_url(original_doi), doi_url(replication_doi)] if x),
            "relationship_date": "",
            "relationship_updated_at": "",
            "relationship_timing": "not_applicable",
            "replication_kind": safe_text(row.get("replication_kind")) or replication_kind_for(row),
            "replication_target_claim": safe_text(row.get("replication_target_claim")) or replication_target_claim_for(row),
            "replication_original_result_id": " | ".join(sorted(original_ids)),
            "replication_replicating_result_id": " | ".join(sorted(replicating_ids)),
            "replication_outcome_match": "corpus asserted matching outcome; original source text not independently verified in this pilot",
            "replication_sample_relation": "independent or larger-N replication asserted by source corpus",
            "replication_design_relation": "replication-pair relationship asserted by source corpus; design relation needs original-source verification",
            "collection_role": "replication_pair",
            "dedupe_group_id": safe_text(row.get("replication_pair_id")),
            "relationship_confidence": "medium",
            "notes": f"Replication relationship inferred from source_result_id={safe_text(row.get('source_result_id'))}; role={safe_text(row.get('replication_role'))}.",
        }

    out = pd.DataFrame([*generic_rows, *prereg_rows, *replication_rows.values()])
    return conform(out, dictionary, "source_source_mapping.tsv")


def make_events(dictionary: pd.DataFrame, source_result: pd.DataFrame) -> pd.DataFrame:
    out = read_tsv(EVENTS_IN)
    sr_to_access = dict(zip(source_result["source_result_id"].map(safe_text), source_result["access_id"].map(safe_text)))
    out.insert(0, "event_id", ["ev_" + stable_hash(i, row.get("source_result_id"), row.get("event_step"), row.get("path")) for i, row in out.iterrows()])
    out["access_id"] = out["source_result_id"].map(lambda key: sr_to_access.get(safe_text(key), ""))
    out["timestamp"] = TIMESTAMP
    out["performed_by"] = "codex"
    out["command_or_tool"] = "make schema-pilot; scripts/retrace_schema_pilot_sample.py"
    return conform(out, dictionary, "extraction_event.tsv")


def make_problems(dictionary: pd.DataFrame) -> pd.DataFrame:
    out = read_tsv(PROBLEMS_IN)
    if out.empty:
        return conform(out, dictionary, "extraction_problem.tsv")
    out.insert(0, "problem_id", ["prob_" + stable_hash(i, row.get("source_result_id"), row.get("problem_code"), row.get("detail")) for i, row in out.iterrows()])
    out["table_name"] = "source_result.tsv"
    out["column_name"] = out["problem_code"].map(
        lambda code: {
            "source_is_derived_not_original_text": "verbatim_source_row_text",
            "missing_verbatim_effect_text": "verbatim_effect_text",
            "missing_verbatim_n_text": "verbatim_n_text",
            "missing_source_locator": "source_locator",
        }.get(safe_text(code), "")
    )
    out["suggested_rework"] = out["problem_code"].map(lambda code: problem_suggestion(safe_text(code)))
    out["resolved"] = "false"
    out["resolved_by"] = ""
    out["resolved_at"] = ""
    return conform(out, dictionary, "extraction_problem.tsv")


def needed_artifact_for_row(row: pd.Series) -> tuple[str, str, str]:
    missing_effect = not safe_text(row.get("verbatim_effect_text"))
    missing_n = not safe_text(row.get("verbatim_n_text"))
    prereg_status = safe_text(row.get("prereg_status"))
    evidence_name = safe_text(row.get("evidence_level_name"))
    value_fields = []
    if missing_effect:
        value_fields.append("effect_text")
    if missing_n:
        value_fields.append("n_text")
    if evidence_name in {"external_source_assertion", "target_source_independently_grounded"}:
        value_fields.append("original_source_object")
    if prereg_status == "prereg_asserted_by_corpus_no_artifact":
        value_fields.append("prereg_artifact")
    if safe_text(row.get("replication_mapping_id")) and evidence_name in {"external_source_assertion", "target_source_independently_grounded"}:
        value_fields.append("replication_evidence")
    if missing_effect:
        return "effect_text", "|".join(value_fields), "Missing verbatim effect/statistic text blocks full promotion."
    if evidence_name in {"external_source_assertion", "target_source_independently_grounded"}:
        return "original_source_object", "|".join(value_fields), "Target is grounded but original source bytes/value text need acquisition."
    if prereg_status == "prereg_asserted_by_corpus_no_artifact":
        return "prereg_artifact", "|".join(value_fields), "Preregistration is asserted by corpus but artifact has not been obtained."
    return "other", "|".join(value_fields) or "review", "Manual review needed by pilot coding status."


def make_manual_tasks(dictionary: pd.DataFrame, source_result: pd.DataFrame, source: pd.DataFrame, problems: pd.DataFrame) -> pd.DataFrame:
    source_url = dict(zip(source["source_id"].map(safe_text), source["url"].map(safe_text))) if not source.empty else {}
    problem_counts = problems["source_result_id"].map(safe_text).value_counts().to_dict() if not problems.empty and "source_result_id" in problems.columns else {}
    rows = []
    for _, row in source_result.iterrows():
        requires = safe_text(row.get("requires_manual_review")) == "true"
        if not requires and problem_counts.get(safe_text(row.get("source_result_id")), 0) == 0:
            continue
        needed_type, value_fields, reason = needed_artifact_for_row(row)
        evidence_level = int(safe_text(row.get("evidence_level")) or 0)
        priority = 100 - evidence_level * 5
        if safe_text(row.get("evidence_level_name")) == "target_source_independently_grounded":
            priority += 25
        if needed_type == "effect_text":
            priority += 20
        if safe_text(row.get("prereg_mapping_id")):
            priority += 5
        represented_source_id = safe_text(row.get("represented_source_id"))
        urls = [safe_text(row.get("prereg_url")), source_url.get(represented_source_id, "")]
        rows.append(
            {
                "manual_task_id": "mtask_" + stable_hash(row.get("source_result_id"), needed_type),
                "source_result_id": safe_text(row.get("source_result_id")),
                "canonical_result_id": safe_text(row.get("canonical_result_id")),
                "represented_source_id": represented_source_id,
                "extraction_source_id": safe_text(row.get("extraction_source_id")),
                "needed_artifact_type": needed_type,
                "needed_value_fields": value_fields,
                "priority_score": str(priority),
                "priority_reason": reason,
                "failed_route_summary": f"current_evidence={safe_text(row.get('evidence_level_name'))}; coding_status={safe_text(row.get('coding_status'))}; problem_count={problem_counts.get(safe_text(row.get('source_result_id')), 0)}",
                "best_candidate_urls": " | ".join(url for url in urls if url),
                "acceptable_manual_routes": "try official source URL, DOI/registry/repository resolver, lawful library access, repository/preprint search, then parse source object",
                "library_access_needed_yn": "unknown",
                "ill_needed_yn": "false",
                "author_contact_needed_yn": "false",
                "repository_access_request_needed_yn": "unknown",
                "assigned_to": "",
                "status": "open",
                "opened_at": TIMESTAMP,
                "closed_at": "",
                "human_outcome": "",
                "created_source_file_id": "",
                "created_support_ids": "",
                "manual_notes": "Pilot manual task generated from 300-row schema proof; do not scale until resolver pass is implemented.",
            }
        )
    return conform(pd.DataFrame(rows), dictionary, "manual_acquisition_task.tsv")


def main() -> None:
    dictionary = read_tsv(DICTIONARY)
    source = make_sources(dictionary)
    access = make_access(dictionary)
    access_attempt = make_access_attempts(dictionary, access)
    source_version = make_source_versions(dictionary, source, access)
    source_file = make_source_files(dictionary, access, access_attempt, source_version)
    source_access_right = make_access_rights(dictionary, source_file, access)
    source_result = make_source_results(dictionary)
    canonical = make_canonical(dictionary, source_result)
    source_identifier = make_source_identifier(dictionary, source, source_result)
    source_classification = make_source_classification(dictionary, source_result)
    canonical_membership = make_canonical_membership(dictionary, canonical, source_result)
    source_result_support = make_source_result_support(dictionary, source_result, source_file)
    plot_membership = make_plot_membership(dictionary, canonical, source_result)
    mapping = make_mapping(dictionary, source_result)
    events = make_events(dictionary, source_result)
    problems = make_problems(dictionary)
    manual_tasks = make_manual_tasks(dictionary, source_result, source, problems)

    outputs = {
        "source.tsv": source,
        "source_access.tsv": access,
        "source_access_attempt.tsv": access_attempt,
        "source_file.tsv": source_file,
        "source_version.tsv": source_version,
        "source_access_right.tsv": source_access_right,
        "source_identifier.tsv": source_identifier,
        "source_classification.tsv": source_classification,
        "source_result.tsv": source_result,
        "canonical_result.tsv": canonical,
        "canonical_result_membership.tsv": canonical_membership,
        "source_result_support.tsv": source_result_support,
        "plot_membership.tsv": plot_membership,
        "source_source_mapping.tsv": mapping,
        "extraction_event.tsv": events,
        "extraction_problem.tsv": problems,
        "manual_acquisition_task.tsv": manual_tasks,
    }
    for table, frame in outputs.items():
        frame.to_csv(OUT_FILES[table], sep="\t", index=False)

    human = read_tsv(HUMAN_IN)
    summary_rows = [
        {"metric": "source_result_rows", "value": len(source_result)},
        {"metric": "source_rows", "value": len(source)},
        {"metric": "source_access_rows", "value": len(access)},
        {"metric": "source_access_attempt_rows", "value": len(access_attempt)},
        {"metric": "source_file_rows", "value": len(source_file)},
        {"metric": "source_version_rows", "value": len(source_version)},
        {"metric": "source_access_right_rows", "value": len(source_access_right)},
        {"metric": "source_identifier_rows", "value": len(source_identifier)},
        {"metric": "source_classification_rows", "value": len(source_classification)},
        {"metric": "canonical_result_membership_rows", "value": len(canonical_membership)},
        {"metric": "source_result_support_rows", "value": len(source_result_support)},
        {"metric": "plot_membership_rows", "value": len(plot_membership)},
        {"metric": "extraction_event_rows", "value": len(events)},
        {"metric": "extraction_problem_rows", "value": len(problems)},
        {"metric": "manual_acquisition_task_rows", "value": len(manual_tasks)},
        {"metric": "source_results_with_verbatim_effect_text", "value": int(source_result["verbatim_effect_text"].map(safe_text).ne("").sum())},
        {"metric": "source_results_with_verbatim_n_text", "value": int(source_result["verbatim_n_text"].map(safe_text).ne("").sum())},
        {"metric": "source_results_with_verbatim_source_row_text", "value": int(source_result["verbatim_source_row_text"].map(safe_text).ne("").sum())},
        {"metric": "source_results_with_prereg_mapping", "value": int(source_result["prereg_mapping_id"].map(safe_text).ne("").sum())},
        {"metric": "source_results_with_prereg_artifact_url", "value": int(source_result["prereg_url"].map(safe_text).ne("").sum())},
        {"metric": "source_results_with_prereg_selector_text", "value": int(source_result["prereg_selector_verbatim_text"].map(safe_text).ne("").sum())},
        {"metric": "source_results_with_replication_mapping", "value": int(source_result["replication_mapping_id"].map(safe_text).ne("").sum())},
        {"metric": "source_results_with_replication_pair_id", "value": int(source_result["replication_pair_id"].map(safe_text).ne("").sum())},
        {"metric": "source_results_marked_fully_coded", "value": int(source_result["coding_status"].eq("fully_coded").sum())},
        {"metric": "source_results_marked_coded_with_schema_gaps", "value": int(source_result["coding_status"].eq("coded_with_schema_gaps").sum())},
    ]
    for key, value in human["source_directness"].value_counts().sort_index().items():
        summary_rows.append({"metric": f"source_directness::{key}", "value": int(value)})
    for key, value in human["source_text_extraction_status"].value_counts().sort_index().items():
        summary_rows.append({"metric": f"source_text_extraction_status::{key}", "value": int(value)})
    for key, value in source_result["evidence_level_name"].value_counts().sort_index().items():
        summary_rows.append({"metric": f"evidence_level_name::{key}", "value": int(value)})
    for key, value in source_result["target_acquisition_state"].value_counts().sort_index().items():
        summary_rows.append({"metric": f"target_acquisition_state::{key}", "value": int(value)})
    for key, value in source_result["value_verification_state"].value_counts().sort_index().items():
        summary_rows.append({"metric": f"value_verification_state::{key}", "value": int(value)})
    for key, value in source_result["prereg_status"].value_counts().sort_index().items():
        summary_rows.append({"metric": f"prereg_status::{key}", "value": int(value)})
    for key, value in source_result["replication_role"].value_counts().sort_index().items():
        summary_rows.append({"metric": f"replication_role::{key}", "value": int(value)})
    for key, value in mapping["relationship_type"].value_counts().sort_index().items():
        summary_rows.append({"metric": f"mapping_relationship_type::{key}", "value": int(value)})
    for key, value in mapping["relationship_subtype"].value_counts().sort_index().items():
        summary_rows.append({"metric": f"mapping_relationship_subtype::{key}", "value": int(value)})
    for key, value in source_identifier["identifier_type"].value_counts().sort_index().items():
        summary_rows.append({"metric": f"identifier_type::{key}", "value": int(value)})
    for key, value in access_attempt["decision"].value_counts().sort_index().items():
        summary_rows.append({"metric": f"access_attempt_decision::{key}", "value": int(value)})
    for key, value in source_file["file_role"].value_counts().sort_index().items():
        summary_rows.append({"metric": f"source_file_role::{key}", "value": int(value)})
    for key, value in source_access_right["rights_decision"].value_counts().sort_index().items():
        summary_rows.append({"metric": f"rights_decision::{key}", "value": int(value)})
    for key, value in manual_tasks["needed_artifact_type"].value_counts().sort_index().items():
        summary_rows.append({"metric": f"manual_needed_artifact::{key}", "value": int(value)})
    for key, value in source_classification["classification_type"].value_counts().sort_index().items():
        summary_rows.append({"metric": f"classification_type::{key}", "value": int(value)})
    for key, value in source_result_support["support_role"].value_counts().sort_index().items():
        summary_rows.append({"metric": f"support_role::{key}", "value": int(value)})
    for key, value in plot_membership["plot_id"].value_counts().sort_index().items():
        summary_rows.append({"metric": f"plot_membership::{key}", "value": int(value)})
    for key in [
        "source_is_original",
        "number_verified_by_us",
        "represented_work_identified",
        "source_is_external",
        "requires_manual_review",
        "conversion_verified",
    ]:
        if key in source_result.columns:
            for value, count in source_result[key].value_counts().sort_index().items():
                summary_rows.append({"metric": f"{key}::{value}", "value": int(count)})
    for key, value in problems["problem_code"].value_counts().sort_index().items():
        summary_rows.append({"metric": f"problem::{key}", "value": int(value)})

    summary = pd.DataFrame(summary_rows)
    summary.to_csv(OUT_SUMMARY, sep="\t", index=False)
    report = [
        "# Codebook Pilot Learning Report",
        "",
        f"This report is generated from the {SAMPLE_N}-row retrace pilot after backfilling recovered source cells into codebook-shaped tables.",
        "",
        "## What Improved",
        "",
        f"- The {SAMPLE_N}-row pilot now has codebook-shaped source, access, file/artifact, support, mapping, plot-membership, and manual-task tables.",
        "- Synthetic repo-generated citations are kept in `generated_result_*` fields and are not used as represented-source citations.",
        "- Every retrace step has an `extraction_event` row with path, checksum where available, and matching method.",
        "",
        "## What Is Still Hard",
        "",
        "- Most rows are recoverable only to an upstream derived row, not to the original paper or registry table text.",
        "- Collapsed paper-level rows need child-result rows preserved at extraction time; reconstructing after plotting requires source-corpus/unit-id matching.",
        "- Registry-derived rows can expose p values and enrollment cleanly, but not always a native effect estimate.",
        "",
        "## Summary",
        "",
        markdown_table(["Metric", "Value"], summary.astype(str).values.tolist()),
        "",
        "## Generated Tables",
        "",
        *[f"- `{path.relative_to(ROOT)}`" for path in OUT_FILES.values()],
    ]
    OUT_REPORT.write_text("\n".join(report) + "\n", encoding="utf-8")
    print(f"Wrote codebook-shaped pilot tables to {PILOT.relative_to(ROOT)}")
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
