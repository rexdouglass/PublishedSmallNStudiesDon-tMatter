#!/usr/bin/env python3
"""Inventory reviewed Figure 1 source-family child artifacts.

This consumes the clustered source-family artifact inventory queue and writes
proposal artifacts for SOURCE_ARTIFACTS.tsv. It is deliberately proposal-only:
root tables are not modified here.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import mimetypes
import re
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
QUEUE_TSV = ROOT / "steps" / "source_inventory" / "figure1" / "source-family-artifact-inventory-queue.tsv"
REVIEW_ROOT = ROOT / "steps" / "review_cue" / "figure1_search_leads"
OUTPUT_ROOT = ROOT / "steps" / "source_inventory" / "figure1"
SCHEMA_TSV = ROOT / "SOURCE_ARTIFACTS.tsv"

AGGREGATE_TSV = OUTPUT_ROOT / "source-artifacts-proposal.tsv"
AGGREGATE_JSON = OUTPUT_ROOT / "source-artifacts-proposal.json"
SUMMARY_TSV = OUTPUT_ROOT / "source-artifact-inventory-summary.tsv"
VALIDATION_TSV = OUTPUT_ROOT / "source-artifacts-proposal-validation.tsv"

SKIP_NAMES = {".DS_Store", "Thumbs.db"}
PAIR_TERMS = [
    "original",
    "orig_",
    "orig ",
    "replication",
    "repli",
    "repeat",
    "rr_id",
    "claim_id",
    "paper_id",
    "study_pair",
    "internal replication",
]
N_TERMS = ["sample", "sample_size", "sample size", "effective_sample", "n_", "_n", " n", "participants", "subjects"]
EFFECT_TERMS = [
    "effect",
    "smd",
    "cohen",
    "hedges",
    "pearson",
    " r",
    "_r",
    "coef",
    "stat",
    "p_value",
    "p value",
    "ci_",
    "confidence",
    "raw difference",
]
PUBLICATION_TERMS = ["doi", "pmid", "pmcid", "paper_id", "citation", "title", "journal", "publication", "article"]


def safe_text(value: object, max_len: int = 12000) -> str:
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value).replace("\t", " ")).strip()[:max_len]


def repo_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def resolve_repo_path(value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else ROOT / path


def slugify(value: object, fallback: str = "source_family") -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", safe_text(value).lower()).strip("_")
    return slug[:120] or fallback


def stable_id(prefix: str, *parts: object) -> str:
    text = "\n".join(safe_text(part, 20000) for part in parts if safe_text(part))
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]
    return f"{prefix}_{digest}"


def today() -> str:
    return datetime.now().date().isoformat()


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return [{key: safe_text(value) for key, value in row.items()} for row in csv.DictReader(handle, delimiter="\t")]


def write_tsv(path: Path, rows: list[dict[str, str]], columns: list[str], replace: bool) -> None:
    if path.exists() and not replace:
        print(f"Skipped {repo_path(path)} because it exists. Use --replace to rebuild.")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {repo_path(path)}")


def write_json(path: Path, payload: dict[str, Any], replace: bool) -> None:
    if path.exists() and not replace:
        print(f"Skipped {repo_path(path)} because it exists. Use --replace to rebuild.")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {repo_path(path)}")


def source_artifact_columns() -> list[str]:
    with SCHEMA_TSV.open("r", encoding="utf-8") as handle:
        return handle.readline().rstrip("\n").split("\t")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def file_type(path: Path) -> str:
    name = path.name.lower()
    if name.endswith(".csv.gz"):
        return "csv.gz"
    suffix = path.suffix.lower().lstrip(".")
    return suffix or "unknown"


def parser_family(path: Path) -> str:
    ft = file_type(path)
    name = path.name.lower()
    if name.endswith(("manifest.json", "file_list.csv", "contents_file_list.csv", "contents_manifest.json")):
        return "provider_file_inventory"
    if ft in {"csv", "tsv", "txt"}:
        return "csv_table_parser"
    if ft == "csv.gz":
        return "compressed_csv_table_parser"
    if ft in {"xlsx", "xls"}:
        return "xlsx_workbook_parser"
    if ft in {"r", "rmd", "py", "do", "sps"}:
        return "analysis_code_inventory"
    if ft in {"json"}:
        return "json_metadata_inventory"
    if ft in {"zip"}:
        return "zip_member_inventory"
    if ft in {"rds", "rdata"}:
        return "r_data_parser"
    if ft in {"dta", "sav"}:
        return "statistical_package_parser"
    if ft in {"pdf", "docx", "html", "htm"}:
        return "document_context_or_source_object_review"
    if ft == "bin":
        return "binary_probe_context"
    return "unknown"


def artifact_role(path: Path) -> str:
    name = path.name.lower()
    ft = file_type(path)
    if "manifest" in name or "file_list" in name or "contents_file_list" in name:
        return "file_inventory"
    if name.endswith("_download.json") or name.endswith("_probe.json") or "landing_probe" in name:
        return "source_access_metadata"
    if "dictionary" in name or "codebook" in name:
        return "codebook"
    if ft in {"csv", "tsv", "csv.gz", "xlsx", "xls", "dta", "sav", "rds", "rdata"}:
        return "data_file"
    if ft in {"r", "rmd", "py", "do", "sps"}:
        return "code_file"
    if ft in {"zip"}:
        return "archive_file"
    if ft in {"pdf", "docx", "html", "htm"}:
        return "context_file"
    return "local_mirror"


def provider_for(path: Path, parent_key: str) -> str:
    text = " ".join([parent_key.lower(), str(path).lower(), path.name.lower()])
    if "github:" in parent_key.lower() or "github" in text or "awesome_" in text:
        return "github"
    if "osf" in text or "rpcb" in text or "score" in text:
        return "osf"
    if "zenodo:" in parent_key.lower():
        return "zenodo"
    return "local_file"


def metadata_sidecars(paths: list[Path]) -> dict[str, dict[str, str]]:
    by_saved: dict[str, dict[str, str]] = {}
    for path in paths:
        if not path.name.endswith("_download.json"):
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        saved = safe_text(payload.get("saved_file"))
        if not saved:
            continue
        saved_path = repo_path(resolve_repo_path(saved))
        by_saved[saved_path] = {key: safe_text(value) for key, value in payload.items()}
    return by_saved


def read_header(path: Path) -> list[str]:
    ft = file_type(path)
    if ft not in {"csv", "tsv", "csv.gz", "txt"}:
        return []
    opener = gzip.open if ft == "csv.gz" else open
    try:
        with opener(path, "rt", encoding="utf-8", errors="replace", newline="") as handle:
            sample = handle.readline().strip("\ufeff\r\n")
    except (OSError, UnicodeDecodeError):
        return []
    if not sample:
        return []
    delimiter = "\t" if ft == "tsv" else ","
    try:
        return [safe_text(part, 200) for part in next(csv.reader([sample], delimiter=delimiter))]
    except csv.Error:
        return [safe_text(part, 200) for part in sample.split(delimiter)]


def evidence_from_header(path: Path) -> dict[str, str]:
    header = read_header(path)
    if not header:
        return {
            "pair_field_evidence": "",
            "n_field_evidence": "",
            "effect_field_evidence": "",
            "publication_link_evidence": "",
        }
    header_text = " | ".join(header[:80])
    lower = header_text.lower()

    def matching(terms: list[str]) -> str:
        if not any(term in lower for term in terms):
            return ""
        hits = [col for col in header if any(term in col.lower() for term in terms)]
        return "header: " + " | ".join(hits[:20])

    return {
        "pair_field_evidence": matching(PAIR_TERMS),
        "n_field_evidence": matching(N_TERMS),
        "effect_field_evidence": matching(EFFECT_TERMS),
        "publication_link_evidence": matching(PUBLICATION_TERMS),
    }


def empty_row(columns: list[str]) -> dict[str, str]:
    return {column: "" for column in columns}


def local_file_row(path: Path, parent_key: str, task: dict[str, str], columns: list[str], sidecars: dict[str, dict[str, str]]) -> dict[str, str]:
    rel = repo_path(path)
    meta = sidecars.get(rel, {})
    stat = path.stat()
    ft = file_type(path)
    mime = safe_text(meta.get("content_type")) or safe_text(mimetypes.guess_type(path.name)[0])
    checksum = safe_text(meta.get("sha256")) or sha256_file(path)
    evidence = evidence_from_header(path)
    provider = provider_for(path, parent_key)
    row = empty_row(columns)
    row.update(
        {
            "artifact_id": stable_id("source_artifact", parent_key, checksum, rel),
            "parent_corpus_database_id": parent_key,
            "artifact_role": artifact_role(path),
            "provider": provider,
            "provider_id": rel if provider == "local_file" else safe_text(meta.get("url")) or rel,
            "parent_provider_id": parent_key,
            "title": path.name,
            "url": safe_text(meta.get("url")) or safe_text(meta.get("final_url")),
            "raw_url": safe_text(meta.get("final_url")) or safe_text(meta.get("url")),
            "doi": "",
            "component_path": repo_path(path.parent),
            "file_name": path.name,
            "file_type": ft,
            "mime_type": mime,
            "byte_size": str(stat.st_size),
            "local_path": rel,
            "sha256": checksum,
            "inventory_status": "mirrored" if artifact_role(path) != "source_access_metadata" else "inventoried_metadata_only",
            "access_status": "downloaded" if meta.get("ok") == "True" or meta.get("ok") == "true" or path.exists() else "unknown",
            "candidate_parser_family": parser_family(path),
            "pair_field_evidence": evidence["pair_field_evidence"],
            "n_field_evidence": evidence["n_field_evidence"],
            "effect_field_evidence": evidence["effect_field_evidence"],
            "publication_link_evidence": evidence["publication_link_evidence"],
            "blocker_codes": "" if evidence["pair_field_evidence"] or evidence["effect_field_evidence"] else "needs_artifact_inspection",
            "next_action": next_action_for(path, evidence),
            "notes": f"generated_from_inventory_task={task.get('inventory_task_id')}; cluster_id={task.get('cluster_id')}",
            "last_seen": today(),
        }
    )
    return row


def next_action_for(path: Path, evidence: dict[str, str]) -> str:
    role = artifact_role(path)
    parser = parser_family(path)
    if role == "file_inventory":
        return "use_inventory_to_map_provider_files_and_local_mirrors"
    if role == "source_access_metadata":
        return "attach_as_access_metadata_to_matching_artifact"
    if parser in {"csv_table_parser", "compressed_csv_table_parser", "xlsx_workbook_parser"}:
        if evidence["pair_field_evidence"] and (evidence["effect_field_evidence"] or evidence["n_field_evidence"]):
            return "inspect_table_for_original_replication_pair_rows"
        return "inspect_table_header_and_codebook_before_parser_assignment"
    if parser == "analysis_code_inventory":
        return "inspect_code_for_table_inputs_outputs_and_conversion_logic"
    if parser == "zip_member_inventory":
        return "inventory_archive_members"
    return "keep_as_context_or_assign_parser_after_review"


def local_sources_from_receipt(task: dict[str, str]) -> list[Path]:
    receipt_path = resolve_repo_path(task.get("decision_receipt_path", ""))
    paths: list[Path] = []
    if receipt_path.exists():
        payload = json.loads(receipt_path.read_text(encoding="utf-8"))
        for source in payload.get("sources_checked") or []:
            text = safe_text(source)
            if text.startswith("local:"):
                paths.append(resolve_repo_path(text.removeprefix("local:")))
    return paths


def candidate_local_sources(task: dict[str, str]) -> list[Path]:
    paths = local_sources_from_receipt(task)
    parent = task.get("parent_corpus_database_id_or_key", "").lower()
    if "rpcb" in parent:
        paths.extend([ROOT / "data/raw/replication_projects/lead_harvest/rpcb_e5nvr", ROOT / "data/raw/corpus_candidates/rpcb"])
    if "covid_online_2021" in parent:
        paths.append(ROOT / "data/raw/replication_projects/lead_harvest/covid_online_2021")
    if "many_labs_2" in parent or "many_labs_2" in task.get("preferred_source_family_name", "").lower():
        paths.extend([ROOT / "data/raw/replication_projects/ml2", ROOT / "data/raw/publication_bias_direct/many_labs_2"])
    if "political_science_unlock" in parent:
        paths.append(ROOT / "data/raw/corpus_candidates/political_science_unlock")
    if parent == "score":
        paths.append(ROOT / "data/raw/corpus_candidates/score")
    if "awesome-replicability-data" in parent:
        paths.extend(ROOT.glob("data/raw/replication_projects/lead_harvest/awesome_*"))
    return sorted(dict.fromkeys(path for path in paths if path.exists()), key=lambda path: str(path))


def iter_files(paths: list[Path]) -> tuple[list[Path], list[str]]:
    files: list[Path] = []
    skipped: list[str] = []
    for path in paths:
        if path.is_file():
            candidates = [path]
        else:
            candidates = [candidate for candidate in path.rglob("*") if candidate.is_file()]
        for candidate in candidates:
            if candidate.name in SKIP_NAMES or "__pycache__" in candidate.parts:
                skipped.append(repo_path(candidate))
                continue
            files.append(candidate)
    return sorted(dict.fromkeys(files), key=lambda item: repo_path(item)), skipped


def provider_manifest_rows(path: Path, parent_key: str, task: dict[str, str], columns: list[str]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    name = path.name.lower()
    if name.endswith("osf_file_manifest.csv") or name.endswith("osf_file_list.csv"):
        with path.open("r", encoding="utf-8", newline="") as handle:
            for item in csv.DictReader(handle):
                rows.append(osf_manifest_item_row(item, path, parent_key, task, columns))
    elif name.endswith("github_contents_file_list.csv"):
        with path.open("r", encoding="utf-8", newline="") as handle:
            for item in csv.DictReader(handle):
                rows.append(github_manifest_item_row(item, path, parent_key, task, columns))
    return [row for row in rows if row]


def osf_manifest_item_row(item: dict[str, str], source_path: Path, parent_key: str, task: dict[str, str], columns: list[str]) -> dict[str, str]:
    path = safe_text(item.get("materialized_path") or item.get("path"))
    title = safe_text(item.get("name")) or safe_text(Path(path).name)
    if title in SKIP_NAMES:
        return {}
    kind = safe_text(item.get("kind"))
    ft = file_type(Path(title))
    row = empty_row(columns)
    row.update(
        {
            "artifact_id": stable_id("source_artifact", parent_key, "osf", item.get("id"), path, title),
            "parent_corpus_database_id": parent_key,
            "artifact_role": "repository_component" if kind == "folder" else ("data_file" if ft in {"csv", "xlsx", "xls"} else "provider_file"),
            "provider": "osf",
            "provider_id": safe_text(item.get("id")),
            "parent_provider_id": parent_key,
            "title": title,
            "url": safe_text(item.get("html_url") or item.get("iri") or item.get("api_url") or item.get("api")),
            "raw_url": safe_text(item.get("download_url") or item.get("download")),
            "component_path": path,
            "file_name": title,
            "file_type": ft,
            "byte_size": safe_text(item.get("size")),
            "inventory_status": "inventoried_metadata_only",
            "access_status": "public_download_seen" if safe_text(item.get("download_url") or item.get("download")) else "public_metadata",
            "candidate_parser_family": parser_family(Path(title)),
            "blocker_codes": "needs_local_mirror" if safe_text(item.get("download_url") or item.get("download")) else "metadata_only",
            "next_action": "match_provider_item_to_local_mirror_or_download_if_needed",
            "notes": f"provider_manifest={repo_path(source_path)}; inventory_task={task.get('inventory_task_id')}",
            "last_seen": today(),
        }
    )
    return row


def github_manifest_item_row(item: dict[str, str], source_path: Path, parent_key: str, task: dict[str, str], columns: list[str]) -> dict[str, str]:
    title = safe_text(item.get("name"))
    if title in SKIP_NAMES:
        return {}
    path = safe_text(item.get("path"))
    ft = file_type(Path(title))
    row = empty_row(columns)
    row.update(
        {
            "artifact_id": stable_id("source_artifact", parent_key, "github", item.get("path"), item.get("sha")),
            "parent_corpus_database_id": parent_key,
            "artifact_role": "data_file" if ft in {"csv", "xlsx", "xls"} else "provider_file",
            "provider": "github",
            "provider_id": path,
            "parent_provider_id": parent_key,
            "title": title,
            "url": safe_text(item.get("html_url")),
            "raw_url": safe_text(item.get("download_url")),
            "component_path": str(Path(path).parent) if path else "",
            "file_name": title,
            "file_type": ft,
            "byte_size": safe_text(item.get("size")),
            "inventory_status": "inventoried_metadata_only",
            "access_status": "public_download_seen" if safe_text(item.get("download_url")) else "public_metadata",
            "candidate_parser_family": parser_family(Path(title)),
            "blocker_codes": "needs_local_mirror" if safe_text(item.get("download_url")) else "metadata_only",
            "next_action": "match_provider_item_to_local_mirror_or_download_if_needed",
            "notes": f"provider_manifest={repo_path(source_path)}; inventory_task={task.get('inventory_task_id')}",
            "last_seen": today(),
        }
    )
    return row


def fetch_zenodo_record(parent_key: str, family_dir: Path, replace: bool) -> Path | None:
    match = re.search(r"zenodo:(\d+)", parent_key)
    if not match:
        return None
    record_id = match.group(1)
    out_path = family_dir / f"inventory-zenodo-record-{record_id}.json"
    if out_path.exists() and not replace:
        return out_path
    url = f"https://zenodo.org/api/records/{record_id}"
    req = urllib.request.Request(url, headers={"User-Agent": "figure1-source-family-inventory/0.1"})
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        error_path = family_dir / f"inventory-zenodo-record-{record_id}-error.json"
        write_json(error_path, {"url": url, "error": safe_text(exc), "last_seen": today()}, replace=True)
        return error_path
    write_json(out_path, payload, replace=True)
    return out_path


def zenodo_rows(path: Path, parent_key: str, task: dict[str, str], columns: list[str]) -> list[dict[str, str]]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    if "error" in payload:
        row = empty_row(columns)
        row.update(
            {
                "artifact_id": stable_id("source_artifact", parent_key, repo_path(path), "zenodo_error"),
                "parent_corpus_database_id": parent_key,
                "artifact_role": "source_access_metadata",
                "provider": "zenodo",
                "provider_id": parent_key,
                "title": "Zenodo metadata fetch error",
                "local_path": repo_path(path),
                "inventory_status": "blocked_access",
                "access_status": "unknown",
                "candidate_parser_family": "json_metadata_inventory",
                "blocker_codes": "provider_metadata_fetch_failed",
                "next_action": "retry_zenodo_metadata_or_inspect_landing_page",
                "notes": safe_text(payload.get("error")),
                "last_seen": today(),
            }
        )
        return [row]
    rows: list[dict[str, str]] = []
    meta = payload.get("metadata") or {}
    links = payload.get("links") or {}
    record_row = empty_row(columns)
    record_id = safe_text(payload.get("id"))
    record_row.update(
        {
            "artifact_id": stable_id("source_artifact", parent_key, "zenodo_record", record_id),
            "parent_corpus_database_id": parent_key,
            "artifact_role": "source_family_page",
            "provider": "zenodo",
            "provider_id": record_id,
            "parent_provider_id": parent_key,
            "title": safe_text(meta.get("title")),
            "url": safe_text(links.get("html") or payload.get("doi_url")),
            "raw_url": safe_text(links.get("self")),
            "doi": safe_text(payload.get("doi")),
            "local_path": repo_path(path),
            "file_type": "json",
            "inventory_status": "inventoried_metadata_only",
            "access_status": "public_metadata",
            "candidate_parser_family": "zenodo_record_inventory",
            "pair_field_evidence": "metadata mentions replication project" if "replication" in safe_text(meta).lower() else "",
            "publication_link_evidence": safe_text(payload.get("doi")),
            "blocker_codes": "needs_file_inventory",
            "next_action": "inspect_zenodo_files_and_linked_gitlab_repository",
            "notes": f"inventory_task={task.get('inventory_task_id')}",
            "last_seen": today(),
        }
    )
    rows.append(record_row)
    for file_item in payload.get("files") or []:
        file_links = file_item.get("links") or {}
        key = safe_text(file_item.get("key"))
        row = empty_row(columns)
        row.update(
            {
                "artifact_id": stable_id("source_artifact", parent_key, "zenodo_file", record_id, key),
                "parent_corpus_database_id": parent_key,
                "artifact_role": "archive_file" if key.lower().endswith(".zip") else "provider_file",
                "provider": "zenodo",
                "provider_id": f"{record_id}:{key}",
                "parent_provider_id": record_id,
                "title": key,
                "url": safe_text(file_links.get("self")),
                "raw_url": safe_text(file_links.get("self")),
                "doi": safe_text(payload.get("doi")),
                "file_name": key,
                "file_type": file_type(Path(key)),
                "mime_type": safe_text(file_item.get("type")),
                "byte_size": safe_text(file_item.get("size")),
                "sha256": safe_text(file_item.get("checksum")).removeprefix("sha256:"),
                "inventory_status": "mirrorable",
                "access_status": "public_download_seen",
                "candidate_parser_family": parser_family(Path(key)),
                "blocker_codes": "needs_download",
                "next_action": "download_or_inventory_archive_members",
                "notes": f"inventory_task={task.get('inventory_task_id')}; provider_checksum={safe_text(file_item.get('checksum'))}",
                "last_seen": today(),
            }
        )
        rows.append(row)
    return rows


def merge_rows(rows: list[dict[str, str]], columns: list[str]) -> list[dict[str, str]]:
    by_key: dict[str, dict[str, str]] = {}
    for row in rows:
        key = row.get("raw_url") or row.get("url") or row.get("sha256") or row.get("local_path") or row.get("artifact_id")
        key = f"{row.get('parent_corpus_database_id')}::{key}"
        if key not in by_key:
            by_key[key] = row
            continue
        existing = by_key[key]
        for column in columns:
            if not existing.get(column) and row.get(column):
                existing[column] = row[column]
        existing["notes"] = " | ".join(part for part in [existing.get("notes"), row.get("notes")] if part)
    for row in by_key.values():
        if row.get("local_path"):
            row["inventory_status"] = "mirrored" if row.get("artifact_role") != "source_access_metadata" else "inventoried_metadata_only"
            if row.get("access_status") in {"", "public_download_seen", "unknown"}:
                row["access_status"] = "downloaded"
            blockers = [part for part in row.get("blocker_codes", "").split(" | ") if part and part != "needs_local_mirror"]
            row["blocker_codes"] = " | ".join(blockers)
    return sorted(by_key.values(), key=lambda row: (row.get("parent_corpus_database_id", ""), row.get("local_path", ""), row.get("title", "")))


def validation_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    seen_ids: set[str] = set()
    for row in rows:
        errors: list[str] = []
        if not row.get("artifact_id"):
            errors.append("missing_artifact_id")
        if row.get("artifact_id") in seen_ids:
            errors.append("duplicate_artifact_id")
        seen_ids.add(row.get("artifact_id", ""))
        if not row.get("parent_corpus_database_id"):
            errors.append("missing_parent_corpus_database_id")
        if not row.get("artifact_role"):
            errors.append("missing_artifact_role")
        if not (row.get("url") or row.get("raw_url") or row.get("local_path")):
            errors.append("missing_access_or_local_path")
        out.append(
            {
                "artifact_id": row.get("artifact_id", ""),
                "parent_corpus_database_id": row.get("parent_corpus_database_id", ""),
                "file_name": row.get("file_name", ""),
                "validation_status": "pass" if not errors else "fail",
                "validation_errors": " | ".join(errors),
            }
        )
    return out


def summary_for(task: dict[str, str], rows: list[dict[str, str]], skipped: list[str]) -> dict[str, str]:
    parser_counts: dict[str, int] = {}
    role_counts: dict[str, int] = {}
    for row in rows:
        parser_counts[row.get("candidate_parser_family", "")] = parser_counts.get(row.get("candidate_parser_family", ""), 0) + 1
        role_counts[row.get("artifact_role", "")] = role_counts.get(row.get("artifact_role", ""), 0) + 1
    return {
        "inventory_task_id": task.get("inventory_task_id", ""),
        "cluster_id": task.get("cluster_id", ""),
        "parent_corpus_database_id_or_key": task.get("parent_corpus_database_id_or_key", ""),
        "preferred_source_family_name": task.get("preferred_source_family_name", ""),
        "artifact_rows": str(len(rows)),
        "local_mirrored_rows": str(sum(1 for row in rows if row.get("local_path"))),
        "parser_candidate_rows": str(sum(1 for row in rows if "parser" in row.get("candidate_parser_family", ""))),
        "pair_evidence_rows": str(sum(1 for row in rows if row.get("pair_field_evidence"))),
        "effect_evidence_rows": str(sum(1 for row in rows if row.get("effect_field_evidence"))),
        "n_evidence_rows": str(sum(1 for row in rows if row.get("n_field_evidence"))),
        "skipped_files": str(len(skipped)),
        "role_counts_json": json.dumps(role_counts, sort_keys=True),
        "parser_counts_json": json.dumps(parser_counts, sort_keys=True),
    }


def inventory_task(task: dict[str, str], columns: list[str], fetch_network: bool, replace: bool) -> tuple[list[dict[str, str]], dict[str, Any], dict[str, str]]:
    parent_key = task.get("parent_corpus_database_id_or_key", "")
    family_dir = OUTPUT_ROOT / slugify(parent_key or task.get("preferred_source_family_name"), "source_family")
    family_dir.mkdir(parents=True, exist_ok=True)
    sources = candidate_local_sources(task)
    files, skipped = iter_files(sources)
    sidecars = metadata_sidecars(files)
    rows = [local_file_row(path, parent_key, task, columns, sidecars) for path in files]
    for path in files:
        rows.extend(provider_manifest_rows(path, parent_key, task, columns))
    if fetch_network and parent_key.startswith("zenodo:"):
        zenodo_path = fetch_zenodo_record(parent_key, family_dir, replace)
        if zenodo_path:
            rows.extend(zenodo_rows(zenodo_path, parent_key, task, columns))
    rows = merge_rows(rows, columns)
    task_slug = slugify(task.get("inventory_task_id"), "inventory_task")
    family_payload = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "task": task,
        "local_sources": [repo_path(path) for path in sources],
        "skipped_files": skipped,
        "artifact_count": len(rows),
        "artifacts": rows,
    }
    write_json(family_dir / f"inventory-source-artifacts-proposal-{task_slug}.json", family_payload, replace)
    write_tsv(family_dir / f"inventory-source-artifacts-proposal-{task_slug}.tsv", rows, columns, replace)
    return rows, family_payload, summary_for(task, rows, skipped)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--queue", default=str(QUEUE_TSV))
    parser.add_argument("--replace", action="store_true")
    parser.add_argument("--fetch-network", action="store_true", help="Fetch lightweight provider metadata such as Zenodo record JSON.")
    args = parser.parse_args()

    queue_path = resolve_repo_path(args.queue)
    columns = source_artifact_columns()
    all_rows: list[dict[str, str]] = []
    summaries: list[dict[str, str]] = []
    family_payloads: list[dict[str, Any]] = []
    for task in read_tsv(queue_path):
        rows, payload, summary = inventory_task(task, columns, args.fetch_network, args.replace)
        all_rows.extend(rows)
        summaries.append(summary)
        family_payloads.append(payload)
    all_rows = merge_rows(all_rows, columns)
    validation = validation_rows(all_rows)
    aggregate = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "queue": repo_path(queue_path),
        "task_count": len(summaries),
        "artifact_count": len(all_rows),
        "validation_fail_count": sum(1 for row in validation if row["validation_status"] != "pass"),
        "artifacts": all_rows,
    }
    write_tsv(AGGREGATE_TSV, all_rows, columns, args.replace)
    write_json(AGGREGATE_JSON, aggregate, args.replace)
    write_tsv(
        SUMMARY_TSV,
        summaries,
        [
            "inventory_task_id",
            "cluster_id",
            "parent_corpus_database_id_or_key",
            "preferred_source_family_name",
            "artifact_rows",
            "local_mirrored_rows",
            "parser_candidate_rows",
            "pair_evidence_rows",
            "effect_evidence_rows",
            "n_evidence_rows",
            "skipped_files",
            "role_counts_json",
            "parser_counts_json",
        ],
        args.replace,
    )
    write_tsv(VALIDATION_TSV, validation, ["artifact_id", "parent_corpus_database_id", "file_name", "validation_status", "validation_errors"], args.replace)
    print(
        "Source-family artifact inventory: "
        f"tasks={len(summaries)}; artifacts={len(all_rows)}; "
        f"validation_failures={aggregate['validation_fail_count']}"
    )


if __name__ == "__main__":
    main()
