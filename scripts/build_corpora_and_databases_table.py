#!/usr/bin/env python3
"""Build or merge the root corpora/databases inventory table.

This is intentionally simpler than the full provenance schema. It is the first
place a discovered corpus, database, source table, registry database, or
replication-project source goes, even if it is later rejected, blocked, staged,
or split into detailed source/source_result rows.

The step-level search outputs live under ``steps/searches/figure1``. Each
concrete search writes a target file named ``corporasearch-*.tsv/csv/json``.
Existing local artifacts flow directly into ``CORPORA_AND_DATABASES.tsv``.
This script also safely merges any concrete search target files into that root
table without creating duplicate intermediate mirrors of the master table.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
from datetime import date
from pathlib import Path
from typing import Iterable

import pandas as pd
import yaml


ROOT = Path(__file__).resolve().parents[1]
TODAY = date.today().isoformat()

OUT_TSV = ROOT / "CORPORA_AND_DATABASES.tsv"
OUT_SCHEMA_YML = ROOT / "CORPORA_AND_DATABASES_SCHEMA.yml"
SEARCH_OUTPUT_DIR = ROOT / "steps/searches/figure1"
SEARCH_OUTPUT_GLOB = "corporasearch-*"
DOI_RE = re.compile(r"10\.\d{4,9}/[-._;()/:A-Z0-9]+", re.I)
GENERIC_TITLE_KEYS = {
    "replication",
    "direct_replication",
    "study_1_direct_replication",
    "study_2_direct_replication",
    "replication_data",
    "original_study",
    "replication_study",
    "pilot_study",
    "original",
    "replication_project",
}

SOURCES = {
    "plot1_source_catalog": ROOT / "data/derived/effect_inflation_dataset/plot1_replication_source_catalog.csv",
    "plot2_source_catalog": ROOT / "data/derived/effect_inflation_dataset/plot2_published_source_catalog.csv",
    "plot3_source_catalog": ROOT / "data/derived/effect_inflation_dataset/plot3_preregistered_source_catalog.csv",
    "plot4_source_catalog": ROOT / "data/derived/effect_inflation_dataset/plot4_all_source_dump_catalog.csv",
    "replication_lead_registry": ROOT / "data/raw/replication_projects/lead_registry.csv",
    "replication_source_worklist": ROOT / "data/derived/replication_pairs/replication_source_worklist.csv",
}

COLUMNS = [
    "corpus_database_id",
    "merge_key",
    "merge_basis",
    "name",
    "record_kind",
    "inventory_status",
    "source_family",
    "domain_or_field",
    "description",
    "why_relevant",
    "plot_universe_ids",
    "current_scope_roles",
    "figure1_replication_relevance",
    "figure2_published_relevance",
    "figure3_prereg_relevance",
    "discovery_source",
    "discovery_source_path",
    "source_key",
    "citation_key",
    "landing_url",
    "raw_url",
    "host",
    "access_class",
    "access_status",
    "local_raw_paths",
    "backing_files",
    "staged_paths",
    "promoted_paths",
    "expected_rows",
    "known_rows",
    "known_pair_rows",
    "known_paper_units",
    "known_test_rows",
    "result_fields_available",
    "has_d_or_convertible_effect",
    "has_n",
    "has_replication_pair_mapping",
    "has_prereg_or_planning_info",
    "has_publication_links",
    "parser_family",
    "parser_status",
    "blocker_codes",
    "next_action",
    "notes",
    "last_seen",
]

SCHEMA = {
    "corpus_database_id": "Stable ID for this corpus/database inventory row.",
    "merge_key": "Internal consolidation key used to dedupe search outputs and local seed rows.",
    "merge_basis": "Evidence basis for merge_key, such as doi, normalized_url, source_key, or search_title.",
    "name": "Human-readable corpus, database, project, registry, or source-table name.",
    "record_kind": "Coarse kind. Search outputs may be candidate_corpus_or_database, candidate_repository_package, candidate_bibliographic_paper, candidate_individual_paper_or_package, candidate_context_or_methods_paper, or rejected_irrelevant_search_hit before later triage promotes a true corpus/database.",
    "inventory_status": "Current disposition: discovered, discovered_search_lead, needs_triage_search_lead, routed_to_individual_paper_search, catalog_only_context_lead, rejected_irrelevant_search_hit, raw_available, staged, integrated, blocked, excluded, needs_triage, or deprecated_duplicate.",
    "source_family": "Source-family label used by plot/source catalogs when available.",
    "domain_or_field": "Domain or field label when available.",
    "description": "What the source is.",
    "why_relevant": "Why this source may matter for one or more current/future plot universes.",
    "plot_universe_ids": "Pipe-delimited plot universes this source may support.",
    "current_scope_roles": "Pipe-delimited roles such as figure1_candidate, figure2_source, figure3_source, diagnostic_catalog, or future_seed.",
    "figure1_replication_relevance": "yes/no/unknown for original/replication pair discovery.",
    "figure2_published_relevance": "yes/no/unknown for eventually published D/N endpoint discovery.",
    "figure3_prereg_relevance": "yes/no/unknown for preregistered/planned result discovery.",
    "discovery_source": "Which local catalog or inventory exposed this row.",
    "discovery_source_path": "Repo-relative path to the catalog/inventory file or raw directory.",
    "source_key": "Existing source key, handle, lead ID, or canonical source ID if available.",
    "citation_key": "Citation key if already known.",
    "landing_url": "Stable landing page, project page, article page, registry page, or repository URL.",
    "raw_url": "Direct raw/package/download URL if known.",
    "host": "Host, provider, or repository platform.",
    "access_class": "Access class such as public, yes_login, restricted, local_only, or unknown.",
    "access_status": "Observed status such as downloaded, raw_available, integrated, blocked, or unknown.",
    "local_raw_paths": "Pipe-delimited repo-relative raw directories or files already present.",
    "backing_files": "Pipe-delimited repo-relative files or paths that back the catalog/source.",
    "staged_paths": "Pipe-delimited staged parser outputs.",
    "promoted_paths": "Pipe-delimited promoted outputs.",
    "expected_rows": "Expected row count when known.",
    "known_rows": "Known candidate/result rows available now.",
    "known_pair_rows": "Known original/replication pair rows available now.",
    "known_paper_units": "Known paper/study/trial units available now.",
    "known_test_rows": "Known test/effect/outcome rows available now.",
    "result_fields_available": "Compact description of available result fields.",
    "has_d_or_convertible_effect": "yes/no/unknown.",
    "has_n": "yes/no/unknown.",
    "has_replication_pair_mapping": "yes/no/unknown.",
    "has_prereg_or_planning_info": "yes/no/unknown.",
    "has_publication_links": "yes/no/unknown.",
    "parser_family": "Parser family or expected parser if known.",
    "parser_status": "Parser state such as not_started, staged, promoted, integrated, blocked, or unknown.",
    "blocker_codes": "Pipe-delimited blockers.",
    "next_action": "Next action needed.",
    "notes": "Short human notes.",
    "last_seen": "Date this inventory row was generated or refreshed.",
}


def safe_text(value: object) -> str:
    if value is None or pd.isna(value):
        return ""
    return re.sub(r"\s+", " ", str(value).replace("\t", " ")).strip()


def slugify(value: object, fallback: str = "source") -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", safe_text(value).lower()).strip("_")
    return slug or fallback


def repo_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def first_nonblank(*values: object) -> str:
    for value in values:
        text = safe_text(value)
        if text:
            return text
    return ""


def split_values(value: object) -> list[str]:
    text = safe_text(value)
    if not text:
        return []
    parts = re.split(r"\s*\|\s*|\s*;\s*", text)
    return [part for part in (safe_text(part) for part in parts) if part]


def merge_pipe(existing: str, new: str) -> str:
    seen: list[str] = []
    for value in split_values(existing) + split_values(new):
        if value and value not in seen:
            seen.append(value)
    return " | ".join(seen)


def normalize_doi(value: object) -> str:
    text = safe_text(value)
    text = re.sub(r"^doi:\s*", "", text, flags=re.I)
    text = re.sub(r"^https?://(?:dx\.)?doi\.org/", "", text, flags=re.I)
    match = DOI_RE.search(text)
    if not match:
        return ""
    return re.sub(r"(10\.\d{4,9})//+", r"\1/", match.group(0).rstrip(".,;)"), flags=re.I).lower()


def first_doi(*values: object) -> str:
    for value in values:
        doi = normalize_doi(value)
        if doi:
            return doi
    return ""


def normalize_url(value: object) -> str:
    text = safe_text(value)
    if not text:
        return ""
    urls = split_values(text)
    url = urls[0] if urls else text
    url = re.sub(r"^https?://dx\.doi\.org/", "https://doi.org/", url, flags=re.I)
    url = re.sub(r"#.*$", "", url)
    url = re.sub(r"\?.*$", "", url)
    url = url.rstrip("/")
    return url.lower()


def title_key(value: object) -> str:
    key = slugify(value)
    if len(key) < 12 or key in GENERIC_TITLE_KEYS:
        return ""
    return key


def is_search_lead(row: dict[str, str]) -> bool:
    return any(source.startswith("figure1_") for source in split_values(row.get("discovery_source", "")))


def row_merge_key(row: dict[str, str]) -> tuple[str, str]:
    key = title_key(row.get("name"))
    if key and is_search_lead(row):
        return f"search_title:{key}", "search_title"
    doi = first_doi(row.get("source_key"), row.get("landing_url"), row.get("raw_url"), row.get("notes"))
    if doi:
        return f"doi:{doi}", "doi"
    for column in ["landing_url", "raw_url"]:
        url = normalize_url(row.get(column))
        if url:
            return f"url:{url}", f"normalized_{column}"
    source_key = safe_text(row.get("source_key"))
    if source_key:
        return f"source_key:{source_key.lower()}", "source_key"
    return row.get("corpus_database_id") or row_id(row.get("name")), "corpus_database_id"


def status_rank(status: str) -> int:
    order = {
        "integrated": 90,
        "promoted": 85,
        "staged": 80,
        "raw_available": 70,
        "discovered_search_lead": 60,
        "discovered": 55,
        "needs_triage_search_lead": 50,
        "needs_triage": 45,
        "routed_to_individual_paper_search": 40,
        "catalog_only_context_lead": 35,
        "blocked": 30,
        "excluded": 20,
        "deprecated_duplicate": 10,
        "rejected_irrelevant_search_hit": 5,
    }
    return order.get(safe_text(status), 40 if status else 0)


def merge_truth(existing: str, new: str) -> str:
    if existing == "yes" or new == "yes":
        return "yes"
    if existing == "no" or new == "no":
        return "no"
    return existing or new


def yes_if_nonzero(value: object) -> str:
    text = safe_text(value)
    if not text:
        return "unknown"
    try:
        return "yes" if float(text) > 0 else "no"
    except ValueError:
        return "yes"


def row_id(*values: object, prefix: str = "corpus_db") -> str:
    key = first_nonblank(*values)
    return f"{prefix}_{slugify(key)}"


def base_row(**values: object) -> dict[str, str]:
    row = {column: "" for column in COLUMNS}
    row.update({key: safe_text(value) for key, value in values.items() if key in row})
    row["last_seen"] = TODAY
    return row


def read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path, dtype=str, keep_default_na=False)


def rows_from_plot1(path: Path) -> Iterable[dict[str, str]]:
    df = read_csv(path)
    for _, item in df.iterrows():
        name = first_nonblank(item.get("canonical_source_label"), item.get("display_label"), item.get("project"))
        if not name:
            continue
        known_pair_rows = first_nonblank(item.get("live_pair_rows"), item.get("catalog_usable_pair_rows"))
        yield base_row(
            corpus_database_id=row_id(item.get("source_key"), item.get("canonical_source_id"), item.get("lead_id"), name),
            name=name,
            record_kind="replication_project",
            inventory_status=first_nonblank(item.get("audit_status"), item.get("plot_inclusion_status"), "needs_triage"),
            source_family=first_nonblank(item.get("source_family_description"), item.get("source_dataset"), item.get("project")),
            description=first_nonblank(item.get("corpus_what_it_is"), item.get("status_explanation")),
            why_relevant=first_nonblank(item.get("status_explanation"), item.get("included_reason_code"), item.get("excluded_reason_code")),
            plot_universe_ids="plot1_replication_pairs",
            current_scope_roles="figure1_candidate",
            figure1_replication_relevance="yes",
            figure2_published_relevance="unknown",
            figure3_prereg_relevance="unknown",
            discovery_source="plot1_source_catalog",
            discovery_source_path=repo_path(path),
            source_key=first_nonblank(item.get("source_key"), item.get("canonical_source_id"), item.get("source_handle"), item.get("lead_id")),
            citation_key=item.get("citation_key"),
            access_status=first_nonblank(item.get("terminal_status"), item.get("raw_payload_statuses"), item.get("audit_status")),
            local_raw_paths=item.get("raw_dirs"),
            backing_files=first_nonblank(item.get("raw_file"), item.get("evidence_surfaces")),
            staged_paths=item.get("staged_paths"),
            promoted_paths=item.get("promoted_paths"),
            known_rows=first_nonblank(item.get("live_pair_rows"), item.get("catalog_file_rows")),
            known_pair_rows=known_pair_rows,
            has_d_or_convertible_effect="unknown" if item.get("blocked_no_DZ") else yes_if_nonzero(known_pair_rows),
            has_n="unknown" if item.get("blocked_no_N") else yes_if_nonzero(known_pair_rows),
            has_replication_pair_mapping=yes_if_nonzero(known_pair_rows),
            parser_status=first_nonblank(item.get("terminal_status"), item.get("audit_status")),
            blocker_codes=item.get("blocker_codes"),
            next_action=first_nonblank(item.get("recommended_next_step"), item.get("next_action")),
            notes=first_nonblank(item.get("source_catalog_notes"), item.get("notes")),
        )


def rows_from_plot2(path: Path) -> Iterable[dict[str, str]]:
    df = read_csv(path)
    for _, item in df.iterrows():
        name = first_nonblank(item.get("source_label"), item.get("display_label"), item.get("source_corpus"))
        if not name:
            continue
        source_kind = safe_text(item.get("source_kind")).lower()
        record_kind = "registry_database" if "registry" in source_kind else "corpus_or_database"
        yield base_row(
            corpus_database_id=row_id(item.get("source_key"), item.get("source_corpus"), name),
            name=name,
            record_kind=record_kind,
            inventory_status=first_nonblank(item.get("plot_inclusion_status"), item.get("status_label"), "needs_triage"),
            source_family=item.get("source_corpus"),
            domain_or_field=item.get("fields"),
            description=item.get("corpus_what_it_is"),
            why_relevant=first_nonblank(item.get("why"), item.get("why_detail"), item.get("what_it_is_why_possible_candidate")),
            plot_universe_ids="plot2_published_paper_d_vs_n",
            current_scope_roles="figure2_source",
            figure1_replication_relevance="unknown",
            figure2_published_relevance="yes",
            figure3_prereg_relevance="unknown",
            discovery_source="plot2_source_catalog",
            discovery_source_path=repo_path(path),
            source_key=first_nonblank(item.get("source_key"), item.get("source_corpus")),
            citation_key=item.get("citation_key"),
            known_rows=first_nonblank(item.get("rows_currently_plotted"), item.get("tests_or_rows_contributed"), item.get("n_obs_in")),
            known_paper_units=first_nonblank(item.get("known_paper_units"), item.get("papers_contributed")),
            known_test_rows=first_nonblank(item.get("known_test_rows"), item.get("tests_or_rows_contributed")),
            result_fields_available=item.get("confirmed_fields"),
            has_d_or_convertible_effect=yes_if_nonzero(first_nonblank(item.get("rows_with_paper_level_dn"), item.get("rows_currently_plotted"))),
            has_n=yes_if_nonzero(first_nonblank(item.get("rows_with_paper_level_dn"), item.get("rows_currently_plotted"))),
            has_publication_links="yes",
            next_action=item.get("why_in_out"),
            notes=first_nonblank(item.get("why_detail"), item.get("source_kind")),
        )


def rows_from_plot3(path: Path) -> Iterable[dict[str, str]]:
    df = read_csv(path)
    for _, item in df.iterrows():
        name = first_nonblank(item.get("source_label"), item.get("display_label"), item.get("source_key"))
        if not name:
            continue
        yield base_row(
            corpus_database_id=row_id(item.get("source_key"), name),
            name=name,
            record_kind="corpus_or_database",
            inventory_status=first_nonblank(item.get("plot_inclusion_status"), "needs_triage"),
            description=item.get("corpus_what_it_is"),
            why_relevant=first_nonblank(item.get("why"), item.get("what_it_is_why_possible_candidate")),
            plot_universe_ids="plot3_preregistered_results",
            current_scope_roles="figure3_source",
            figure1_replication_relevance="unknown",
            figure2_published_relevance="unknown",
            figure3_prereg_relevance="yes",
            discovery_source="plot3_source_catalog",
            discovery_source_path=repo_path(path),
            source_key=item.get("source_key"),
            citation_key=item.get("citation_key"),
            backing_files=item.get("backing_file"),
            known_rows=first_nonblank(item.get("rows_contributed"), item.get("rows_considered")),
            result_fields_available=item.get("confirmed_fields"),
            has_d_or_convertible_effect=yes_if_nonzero(item.get("rows_with_extractable_DN")),
            has_n=yes_if_nonzero(item.get("rows_with_extractable_DN")),
            has_prereg_or_planning_info=yes_if_nonzero(item.get("rows_preregistered_equivalent")),
            has_publication_links="yes",
            next_action=item.get("why_in_out"),
            notes=item.get("why"),
        )


def rows_from_plot4(path: Path) -> Iterable[dict[str, str]]:
    df = read_csv(path)
    for _, item in df.iterrows():
        name = safe_text(item.get("source_label"))
        if not name:
            continue
        yield base_row(
            corpus_database_id=row_id(name),
            name=name,
            record_kind="candidate_result_table",
            inventory_status=first_nonblank(item.get("plot_inclusion_status"), "catalog_only"),
            description=item.get("corpus_what_it_is"),
            why_relevant=item.get("inclusion_rule"),
            plot_universe_ids="plot4_all_source_dn_dump",
            current_scope_roles="diagnostic_catalog | future_seed",
            figure1_replication_relevance="unknown",
            figure2_published_relevance="unknown",
            figure3_prereg_relevance="unknown",
            discovery_source="plot4_source_catalog",
            discovery_source_path=repo_path(path),
            citation_key=item.get("citation_key"),
            backing_files=item.get("backing_path"),
            known_rows=first_nonblank(item.get("rows_in_dump"), item.get("rows_available")),
            has_d_or_convertible_effect="yes",
            has_n="yes",
            notes=item.get("remaining_caveat"),
        )


def rows_from_lead_registry(path: Path) -> Iterable[dict[str, str]]:
    df = read_csv(path)
    for _, item in df.iterrows():
        name = first_nonblank(item.get("project"), item.get("lead_id"))
        if not name:
            continue
        yield base_row(
            corpus_database_id=row_id(item.get("lead_id"), name, prefix="lead"),
            name=name,
            record_kind="replication_project",
            inventory_status=first_nonblank(item.get("default_action"), "discovered"),
            source_family=item.get("source_family"),
            why_relevant=item.get("notes"),
            plot_universe_ids="plot1_replication_pairs",
            current_scope_roles="figure1_candidate",
            figure1_replication_relevance="yes",
            figure2_published_relevance="unknown",
            figure3_prereg_relevance="unknown",
            discovery_source="replication_lead_registry",
            discovery_source_path=repo_path(path),
            source_key=item.get("lead_id"),
            landing_url=item.get("landing_url"),
            raw_url=item.get("raw_url"),
            host=item.get("host"),
            access_class=item.get("access_class"),
            expected_rows=item.get("expected_rows"),
            result_fields_available=item.get("metric_class"),
            has_d_or_convertible_effect="yes" if "d" in safe_text(item.get("metric_class")).lower() else "unknown",
            has_replication_pair_mapping="yes" if safe_text(item.get("directness_class")) else "unknown",
            parser_family=item.get("parser_family"),
            parser_status=item.get("default_action"),
            next_action=item.get("default_action"),
            notes=item.get("notes"),
        )


def rows_from_worklist(path: Path) -> Iterable[dict[str, str]]:
    df = read_csv(path)
    for _, item in df.iterrows():
        name = first_nonblank(item.get("canonical_source_label"), item.get("canonical_source_id"))
        if not name:
            continue
        yield base_row(
            corpus_database_id=row_id(item.get("canonical_source_id"), name),
            name=name,
            record_kind="replication_project",
            inventory_status=first_nonblank(item.get("audit_status"), "needs_triage"),
            source_family=first_nonblank(item.get("linked_source_datasets"), item.get("linked_projects")),
            why_relevant=item.get("worklist_rationale"),
            plot_universe_ids="plot1_replication_pairs",
            current_scope_roles="figure1_candidate",
            figure1_replication_relevance="yes",
            discovery_source="replication_source_worklist",
            discovery_source_path=repo_path(path),
            source_key=item.get("canonical_source_id"),
            access_status=item.get("raw_payload_statuses"),
            local_raw_paths=item.get("raw_dirs"),
            staged_paths=item.get("staged_paths"),
            promoted_paths=item.get("promoted_paths"),
            known_pair_rows=item.get("live_pair_rows"),
            has_replication_pair_mapping=yes_if_nonzero(item.get("live_pair_rows")),
            blocker_codes=item.get("blocker_codes"),
            next_action=item.get("recommended_next_step"),
            notes=item.get("worklist_rationale"),
        )


def rows_from_raw_dirs(root: Path) -> Iterable[dict[str, str]]:
    if not root.exists():
        return
    for path in sorted(item for item in root.iterdir() if item.is_dir()):
        yield base_row(
            corpus_database_id=row_id(path.name),
            name=path.name.replace("_", " ").title(),
            record_kind="raw_inventory_dir",
            inventory_status="raw_available",
            plot_universe_ids="unknown_future_or_current",
            current_scope_roles="future_seed",
            figure1_replication_relevance="unknown",
            figure2_published_relevance="unknown",
            figure3_prereg_relevance="unknown",
            discovery_source="raw_corpus_candidates_dir",
            discovery_source_path=repo_path(path),
            source_key=path.name,
            access_status="local_raw_dir_present",
            local_raw_paths=repo_path(path),
            next_action="triage_for_plot_universe",
        )


def merge_rows(rows: Iterable[dict[str, str]]) -> list[dict[str, str]]:
    merged: dict[str, dict[str, str]] = {}
    for row in rows:
        row = {column: safe_text(row.get(column, "")) for column in COLUMNS}
        key, basis = row_merge_key(row)
        row["merge_key"] = row["merge_key"] or key
        row["merge_basis"] = row["merge_basis"] or basis
        row["corpus_database_id"] = row["corpus_database_id"] or row_id(row["name"])
        if key not in merged:
            merged[key] = row
            continue
        existing = merged[key]
        for column in COLUMNS:
            if column in {
                "merge_basis",
                "plot_universe_ids",
                "current_scope_roles",
                "discovery_source",
                "discovery_source_path",
                "source_key",
                "citation_key",
                "landing_url",
                "raw_url",
                "host",
                "local_raw_paths",
                "backing_files",
                "staged_paths",
                "promoted_paths",
                "blocker_codes",
                "notes",
            }:
                existing[column] = merge_pipe(existing[column], row[column])
            elif column == "inventory_status":
                if status_rank(row[column]) > status_rank(existing[column]):
                    existing[column] = row[column]
            elif column in {
                "figure1_replication_relevance",
                "figure2_published_relevance",
                "figure3_prereg_relevance",
                "has_d_or_convertible_effect",
                "has_n",
                "has_replication_pair_mapping",
                "has_prereg_or_planning_info",
                "has_publication_links",
            }:
                existing[column] = merge_truth(existing[column], row[column])
            elif not existing[column] and row[column]:
                existing[column] = row[column]
        existing["last_seen"] = TODAY
    return sorted(merged.values(), key=lambda item: (item["record_kind"], item["name"].lower()))


def local_inventory_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    rows.extend(rows_from_plot1(SOURCES["plot1_source_catalog"]))
    rows.extend(rows_from_plot2(SOURCES["plot2_source_catalog"]))
    rows.extend(rows_from_plot3(SOURCES["plot3_source_catalog"]))
    rows.extend(rows_from_plot4(SOURCES["plot4_source_catalog"]))
    rows.extend(rows_from_lead_registry(SOURCES["replication_lead_registry"]))
    rows.extend(rows_from_worklist(SOURCES["replication_source_worklist"]))
    rows.extend(rows_from_raw_dirs(ROOT / "data/raw/corpus_candidates") or [])
    return merge_rows(rows)


def normalize_row(row: dict[str, object], source_path: Path) -> dict[str, str]:
    out = {column: safe_text(row.get(column, "")) for column in COLUMNS}
    if not out["corpus_database_id"]:
        out["corpus_database_id"] = row_id(
            out.get("source_key"),
            out.get("landing_url"),
            out.get("raw_url"),
            out.get("name"),
        )
    if not out["discovery_source_path"]:
        out["discovery_source_path"] = repo_path(source_path)
    if not out["last_seen"]:
        out["last_seen"] = TODAY
    return out


def read_search_output(path: Path) -> list[dict[str, str]]:
    suffix = path.suffix.lower()
    if suffix == ".json":
        payload = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(payload, dict):
            data = payload.get("candidates", payload.get("rows", []))
        else:
            data = payload
        if not isinstance(data, list):
            raise ValueError(f"{path} JSON payload must be a list or contain candidates/rows")
        return [normalize_row(dict(item), path) for item in data if isinstance(item, dict)]
    if suffix == ".csv":
        frame = pd.read_csv(path, dtype=str, keep_default_na=False)
    elif suffix in {".tsv", ".txt"}:
        frame = pd.read_csv(path, sep="\t", dtype=str, keep_default_na=False)
    else:
        return []
    return [normalize_row(row.to_dict(), path) for _, row in frame.iterrows()]


def search_output_paths() -> list[Path]:
    if not SEARCH_OUTPUT_DIR.exists():
        return []
    allowed = {".tsv", ".csv", ".json"}
    return sorted(
        path
        for path in SEARCH_OUTPUT_DIR.glob(SEARCH_OUTPUT_GLOB)
        if path.is_file() and path.suffix.lower() in allowed
    )


def search_output_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for path in search_output_paths():
        rows.extend(read_search_output(path))
    return merge_rows(rows)


def existing_master_rows() -> list[dict[str, str]]:
    if not OUT_TSV.exists():
        return []
    return read_search_output(OUT_TSV)


def write_tsv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=COLUMNS, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_schema() -> None:
    payload = {
        "CORPORA_AND_DATABASES_SCHEMA": {
            "purpose": (
                "One consolidated root-level table for every corpus, database, registry database, "
                "replication project, source table, or repository package we discover."
            ),
            "table": OUT_TSV.name,
            "grain": "One corpus/database/source-family lead or inventory object.",
            "rule": "Any discovered corpus or database-like source goes here before it is split into detailed provenance tables.",
            "columns": [{"name": column, "definition": SCHEMA[column]} for column in COLUMNS],
        }
    }
    OUT_SCHEMA_YML.write_text(yaml.safe_dump(payload, sort_keys=False, width=100), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--replace",
        action="store_true",
        help="Rebuild CORPORA_AND_DATABASES.tsv from current upstream inputs, ignoring existing master rows.",
    )
    parser.add_argument(
        "--replace-master",
        action="store_true",
        help="Rebuild CORPORA_AND_DATABASES.tsv from current upstream inputs, ignoring existing master rows.",
    )
    args = parser.parse_args()
    replace_master = (
        args.replace
        or args.replace_master
        or os.environ.get("REPLACE_CORPORA_DATABASES") == "1"
    )

    local_rows = local_inventory_rows()
    target_rows = search_output_rows()
    source_rows = local_rows + target_rows
    if not replace_master:
        source_rows = existing_master_rows() + source_rows
    rows = merge_rows(source_rows)
    write_tsv(OUT_TSV, rows)
    write_schema()
    print(f"Merged {len(local_rows)} local inventory row(s) directly into {OUT_TSV.relative_to(ROOT)}")
    print(f"Read {len(search_output_paths())} concrete search output file(s) from {SEARCH_OUTPUT_DIR.relative_to(ROOT)}")
    print(f"Wrote {OUT_TSV.relative_to(ROOT)} ({len(rows)} rows)")
    print(f"Wrote {OUT_SCHEMA_YML.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
