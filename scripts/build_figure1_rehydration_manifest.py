#!/usr/bin/env python3
"""Build a rehydration manifest for Figure 1 mirrored source artifacts.

The large raw mirrors under data/raw are intentionally not suitable for Git.
This script records the stable URLs that actually succeeded during source
artifact acquisition and maps them back to artifact IDs and expected local
paths, so a fresh checkout can repull the mirrorable bytes by script.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SOURCE_INVENTORY_ROOT = ROOT / "steps" / "source_inventory" / "figure1"
PROPOSAL_TSV = SOURCE_INVENTORY_ROOT / "source-artifacts-proposal.tsv"
STATUS_TSV = SOURCE_INVENTORY_ROOT / "mirror_sample" / "source-artifact-mirror-sample-status.tsv"
OUTPUT_ROOT = SOURCE_INVENTORY_ROOT / "rehydration"
WORKING_URLS_TSV = OUTPUT_ROOT / "figure1-working-urls.tsv"
WORKING_URLS_JSON = OUTPUT_ROOT / "figure1-working-urls.json"
MANIFEST_TSV = OUTPUT_ROOT / "figure1-rehydration-manifest.tsv"
MANIFEST_JSON = OUTPUT_ROOT / "figure1-rehydration-manifest.json"
GAPS_TSV = OUTPUT_ROOT / "figure1-rehydration-gaps.tsv"
SUMMARY_TSV = OUTPUT_ROOT / "figure1-rehydration-summary.tsv"
SKIP_NAMES = {".DS_Store", "Thumbs.db"}


def safe_text(value: object, max_len: int = 12000) -> str:
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value).replace("\t", " ")).strip()[:max_len]


def repo_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def resolve_path(value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else ROOT / path


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


def stable_id(prefix: str, *parts: object) -> str:
    text = "\n".join(safe_text(part, 20000) for part in parts if safe_text(part))
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]
    return f"{prefix}_{digest}"


def load_json(path: Path) -> dict[str, Any] | list[Any] | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def as_repo_path(value: object) -> str:
    text = safe_text(value, 40000)
    if not text:
        return ""
    return repo_path(resolve_path(text))


def file_type(name: str) -> str:
    lower = name.lower()
    if lower.endswith(".csv.gz"):
        return "csv.gz"
    suffix = Path(lower).suffix.lstrip(".")
    return suffix or "unknown"


def looks_temporary_url(url: str) -> bool:
    lower = url.lower()
    return any(
        token in lower
        for token in [
            "x-amz-signature=",
            "x-amz-credential=",
            "dvn-cloud-iqss.s3.amazonaws.com",
            "storage.googleapis.com/cos-osf-prod-files",
            "response-content-disposition=",
        ]
    )


def provider_from_url(url: str, fallback: str = "") -> str:
    lower = url.lower()
    if "github.com" in lower or "raw.githubusercontent.com" in lower:
        return "github"
    if "osf.io" in lower or "cos-osf" in lower:
        return "osf"
    if "dataverse" in lower or "dvn-cloud" in lower:
        return "dataverse"
    if "zenodo" in lower:
        return "zenodo"
    return fallback


def preferred_artifact_url(row: dict[str, str]) -> tuple[str, str, str]:
    raw_url = safe_text(row.get("raw_url"), 40000)
    url = safe_text(row.get("url"), 40000)
    if raw_url and not looks_temporary_url(raw_url):
        return raw_url, "raw_url", "false"
    if url:
        return url, "url", "false" if not looks_temporary_url(url) else "true"
    return raw_url, "raw_url", "true" if raw_url else ""


def inventory_roots(source_inventory_root: Path) -> list[Path]:
    roots: list[Path] = []
    for path in source_inventory_root.glob("*/inventory-source-artifacts-proposal-*.json"):
        payload = load_json(path)
        if not isinstance(payload, dict):
            continue
        for local_source in payload.get("local_sources") or []:
            local_path = resolve_path(safe_text(local_source))
            if local_path.exists():
                roots.append(local_path)
    return sorted(dict.fromkeys(roots), key=lambda item: repo_path(item))


def sidecar_paths(roots: list[Path]) -> list[Path]:
    paths: list[Path] = []
    for root in roots:
        candidates = [root] if root.is_file() else list(root.rglob("*"))
        for path in candidates:
            if not path.is_file():
                continue
            name = path.name.lower()
            if name.endswith("_download.json") or name.endswith("_probe.json"):
                paths.append(path)
    return sorted(dict.fromkeys(paths), key=lambda item: repo_path(item))


def all_files(roots: list[Path]) -> list[Path]:
    paths: list[Path] = []
    for root in roots:
        candidates = [root] if root.is_file() else list(root.rglob("*"))
        paths.extend(path for path in candidates if path.is_file())
    return sorted(dict.fromkeys(paths), key=lambda item: repo_path(item))


def build_indexes(
    proposal_rows: list[dict[str, str]],
    status_rows: list[dict[str, str]],
) -> tuple[dict[str, dict[str, str]], dict[str, str], dict[str, str], dict[str, str]]:
    proposal_by_artifact = {row["artifact_id"]: row for row in proposal_rows}
    artifact_by_path: dict[str, str] = {}
    artifact_by_sha: dict[str, str] = {}
    parent_by_path: dict[str, str] = {}
    for row in proposal_rows:
        artifact_id = row.get("artifact_id", "")
        parent = row.get("parent_corpus_database_id", "")
        for field in ["local_path"]:
            local = as_repo_path(row.get(field))
            if local:
                artifact_by_path.setdefault(local, artifact_id)
                parent_by_path.setdefault(local, parent)
        sha = safe_text(row.get("sha256"))
        if sha:
            artifact_by_sha.setdefault(sha, artifact_id)
    for row in status_rows:
        artifact_id = row.get("artifact_id", "")
        parent = row.get("parent_corpus_database_id", "")
        for field in ["source_local_path", "mirror_local_path"]:
            local = as_repo_path(row.get(field))
            if local:
                artifact_by_path.setdefault(local, artifact_id)
                parent_by_path.setdefault(local, parent)
        sha = safe_text(row.get("mirror_sha256"))
        if sha:
            artifact_by_sha.setdefault(sha, artifact_id)
    return proposal_by_artifact, artifact_by_path, artifact_by_sha, parent_by_path


def basename_index(paths: list[Path]) -> dict[str, list[str]]:
    index: dict[str, list[str]] = {}
    for path in paths:
        index.setdefault(path.name, []).append(repo_path(path))
    for values in index.values():
        values.sort()
    return index


def target_for_manifest_item(metadata_path: Path, item_name: str, path_hint: str, basename_to_paths: dict[str, list[str]]) -> str:
    base = metadata_path.parent
    name = Path(item_name).name if item_name else Path(path_hint).name
    clean_hint = safe_text(path_hint).strip("/")
    candidates: list[Path] = []
    if clean_hint:
        candidates.extend([base / clean_hint, base / clean_hint.replace("/", "__")])
    if name:
        candidates.append(base / name)
    for candidate in candidates:
        if candidate.exists() and candidate.is_file():
            return repo_path(candidate)
    if name:
        base_repo = repo_path(base)
        for candidate in basename_to_paths.get(name, []):
            if candidate.startswith(base_repo + "/"):
                return candidate
        suffix = "__" + name
        for paths in basename_to_paths.values():
            for candidate in paths:
                if candidate.startswith(base_repo + "/") and Path(candidate).name.endswith(suffix):
                    return candidate
    if clean_hint:
        return repo_path(base / clean_hint.replace("/", "__"))
    if name:
        return repo_path(base / name)
    return ""


def provider_manifest_paths(paths: list[Path]) -> list[Path]:
    out: list[Path] = []
    for path in paths:
        name = path.name.lower()
        if name in {
            "osf_file_manifest.csv",
            "osf_file_list.csv",
            "github_contents_file_list.csv",
            "dataverse_file_list.csv",
        }:
            out.append(path)
        elif name.endswith("manifest.json") or name.endswith("metadata.json") or name.endswith("_files.json"):
            out.append(path)
    return sorted(dict.fromkeys(out), key=lambda item: repo_path(item))


def manifest_row(
    metadata_path: Path,
    route_kind: str,
    url: str,
    item_name: str,
    path_hint: str,
    byte_size: str,
    content_type: str,
    checksum: str,
    checksum_type: str,
    basename_to_paths: dict[str, list[str]],
    artifact_by_path: dict[str, str],
    artifact_by_sha: dict[str, str],
    parent_by_path: dict[str, str],
    proposal_by_artifact: dict[str, dict[str, str]],
) -> dict[str, str] | None:
    stable_url = safe_text(url, 40000)
    if not stable_url:
        return None
    if Path(item_name).name in SKIP_NAMES:
        return None
    target = target_for_manifest_item(metadata_path, item_name, path_hint, basename_to_paths)
    sha = checksum if checksum_type.lower() == "sha256" else ""
    artifact_id = artifact_by_path.get(target) or artifact_by_sha.get(sha, "")
    artifact = proposal_by_artifact.get(artifact_id, {})
    parent = artifact.get("parent_corpus_database_id") or parent_by_path.get(target, "")
    if not parent:
        parent = parent_from_metadata_path(metadata_path)
    notes = f"provider_manifest={repo_path(metadata_path)}"
    if checksum and checksum_type and checksum_type.lower() != "sha256":
        notes += f"; provider_checksum={checksum_type}:{checksum}"
    return {
        "working_url_id": stable_id("figure1_working_url", route_kind, stable_url, target, repo_path(metadata_path)),
        "route_kind": route_kind,
        "parent_corpus_database_id": parent,
        "artifact_id": artifact_id,
        "provider": provider_from_url(stable_url, artifact.get("provider", "")),
        "url": stable_url,
        "url_field": "provider_manifest",
        "final_url": "",
        "url_is_temporary": "true" if looks_temporary_url(stable_url) else "false",
        "target_local_path": target,
        "access_metadata_path": repo_path(metadata_path),
        "status_code": "",
        "content_type": content_type,
        "content_length": byte_size,
        "byte_size": byte_size,
        "sha256": sha,
        "repull_supported": "true" if target and not looks_temporary_url(stable_url) else "false",
        "source_evidence": repo_path(metadata_path),
        "notes": notes,
    }


def parent_from_metadata_path(path: Path) -> str:
    rel = repo_path(path)
    if "data/raw/corpus_candidates/political_science_unlock/" in rel:
        return "raw_corpus:political_science_unlock"
    if "data/raw/corpus_candidates/rpcb/" in rel:
        return "raw_corpus:rpcb"
    if "data/raw/replication_projects/lead_harvest/rpcb_e5nvr/" in rel:
        return "raw_corpus:rpcb"
    if "data/raw/corpus_candidates/score/" in rel:
        return "score"
    if "data/raw/replication_projects/lead_harvest/covid_online_2021/" in rel:
        return "lead_harvest:covid_online_2021"
    if "data/raw/replication_projects/lead_harvest/awesome_" in rel:
        return "github:ying531/awesome-replicability-data"
    return ""


def csv_provider_manifest_rows(
    path: Path,
    basename_to_paths: dict[str, list[str]],
    artifact_by_path: dict[str, str],
    artifact_by_sha: dict[str, str],
    parent_by_path: dict[str, str],
    proposal_by_artifact: dict[str, dict[str, str]],
) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    try:
        with path.open("r", encoding="utf-8", newline="") as handle:
            items = list(csv.DictReader(handle))
    except (OSError, csv.Error, UnicodeDecodeError):
        return rows
    name = path.name.lower()
    for item in items:
        if name == "github_contents_file_list.csv":
            url = safe_text(item.get("download_url"))
            item_name = safe_text(item.get("name"))
            path_hint = safe_text(item.get("path"))
            byte_size = safe_text(item.get("size"))
            content_type = ""
        elif name == "dataverse_file_list.csv":
            url = safe_text(item.get("download_url"))
            item_name = safe_text(item.get("label") or item.get("name"))
            path_hint = item_name
            byte_size = safe_text(item.get("size"))
            content_type = safe_text(item.get("content_type"))
        else:
            url = safe_text(item.get("download_url") or item.get("download"))
            item_name = safe_text(item.get("name") or Path(safe_text(item.get("path"))).name)
            path_hint = safe_text(item.get("materialized_path") or item.get("path") or item_name)
            byte_size = safe_text(item.get("size"))
            content_type = ""
        row = manifest_row(
            path,
            "recorded_provider_manifest",
            url,
            item_name,
            path_hint,
            byte_size,
            content_type,
            "",
            "",
            basename_to_paths,
            artifact_by_path,
            artifact_by_sha,
            parent_by_path,
            proposal_by_artifact,
        )
        if row:
            rows.append(row)
    return rows


def dataverse_file_rows(payload: dict[str, Any]) -> list[dict[str, str]]:
    version = (payload.get("data") or {}).get("latestVersion") or {}
    rows: list[dict[str, str]] = []
    for item in version.get("files") or []:
        data_file = item.get("dataFile") or {}
        file_id = safe_text(data_file.get("id"))
        filename = safe_text(data_file.get("filename") or item.get("label"))
        directory = safe_text(data_file.get("directoryLabel") or item.get("directoryLabel"))
        checksum_payload = data_file.get("checksum") or {}
        rows.append(
            {
                "url": f"https://dataverse.harvard.edu/api/access/datafile/{file_id}" if file_id else "",
                "name": filename,
                "path": f"{directory}/{filename}" if directory else filename,
                "size": safe_text(data_file.get("filesize") or item.get("size")),
                "content_type": safe_text(data_file.get("contentType")),
                "checksum": safe_text(checksum_payload.get("value") or data_file.get("md5")),
                "checksum_type": safe_text(checksum_payload.get("type") or ("MD5" if data_file.get("md5") else "")),
            }
        )
    return rows


def json_provider_manifest_rows(
    path: Path,
    payload: dict[str, Any] | list[Any],
    basename_to_paths: dict[str, list[str]],
    artifact_by_path: dict[str, str],
    artifact_by_sha: dict[str, str],
    parent_by_path: dict[str, str],
    proposal_by_artifact: dict[str, dict[str, str]],
) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    items: list[dict[str, str]] = []
    if isinstance(payload, list):
        for item in payload:
            if isinstance(item, dict):
                items.append(
                    {
                        "url": safe_text(item.get("download") or item.get("download_url")),
                        "name": safe_text(item.get("name")),
                        "path": safe_text(item.get("path") or item.get("materialized_path") or item.get("name")),
                        "size": safe_text(item.get("size")),
                        "content_type": "",
                        "checksum": "",
                        "checksum_type": "",
                    }
                )
    elif isinstance(payload, dict) and "files" in payload:
        for item in payload.get("files") or []:
            if not isinstance(item, dict):
                continue
            links = item.get("links") or {}
            checksum = safe_text(item.get("checksum"))
            checksum_type = ""
            checksum_value = checksum
            if ":" in checksum:
                checksum_type, checksum_value = checksum.split(":", 1)
            items.append(
                {
                    "url": safe_text(links.get("self") or links.get("download")),
                    "name": safe_text(item.get("key") or item.get("filename")),
                    "path": safe_text(item.get("key") or item.get("filename")),
                    "size": safe_text(item.get("size")),
                    "content_type": safe_text(item.get("type")),
                    "checksum": checksum_value,
                    "checksum_type": checksum_type,
                }
            )
    elif isinstance(payload, dict) and isinstance(payload.get("data"), dict) and (payload.get("data") or {}).get("latestVersion"):
        items.extend(dataverse_file_rows(payload))
    elif isinstance(payload, dict) and isinstance(payload.get("data"), list):
        for item in payload.get("data") or []:
            if not isinstance(item, dict):
                continue
            attrs = item.get("attributes") or {}
            links = item.get("links") or {}
            hashes = (attrs.get("extra") or {}).get("hashes") or {}
            items.append(
                {
                    "url": safe_text(links.get("download")),
                    "name": safe_text(attrs.get("name")),
                    "path": safe_text(attrs.get("materialized_path") or attrs.get("path") or attrs.get("name")),
                    "size": safe_text(attrs.get("size")),
                    "content_type": "",
                    "checksum": safe_text(hashes.get("sha256")),
                    "checksum_type": "sha256" if hashes.get("sha256") else "",
                }
            )
    for item in items:
        row = manifest_row(
            path,
            "recorded_provider_manifest",
            item.get("url", ""),
            item.get("name", ""),
            item.get("path", ""),
            item.get("size", ""),
            item.get("content_type", ""),
            item.get("checksum", ""),
            item.get("checksum_type", ""),
            basename_to_paths,
            artifact_by_path,
            artifact_by_sha,
            parent_by_path,
            proposal_by_artifact,
        )
        if row:
            rows.append(row)
    rows.extend(dataverse_dataset_zip_rows(path, payload, artifact_by_path, parent_by_path, proposal_by_artifact))
    return rows


def dataverse_dataset_zip_rows(
    path: Path,
    payload: dict[str, Any] | list[Any],
    artifact_by_path: dict[str, str],
    parent_by_path: dict[str, str],
    proposal_by_artifact: dict[str, dict[str, str]],
) -> list[dict[str, str]]:
    if not isinstance(payload, dict) or (payload.get("status") or "").upper() != "OK":
        return []
    data = payload.get("data") or {}
    identifier = safe_text(data.get("identifier"))
    if not identifier.startswith("DVN/"):
        return []
    code = identifier.split("/", 1)[1]
    target = path.parent.parent / "dataverse" / code / f"{code}.zip"
    if not target.exists():
        return []
    target_rel = repo_path(target)
    artifact_id = artifact_by_path.get(target_rel, "")
    artifact = proposal_by_artifact.get(artifact_id, {})
    parent = artifact.get("parent_corpus_database_id") or parent_by_path.get(target_rel) or parent_from_metadata_path(path)
    url = f"https://dataverse.harvard.edu/api/access/dataset/:persistentId/?persistentId=doi:10.7910/DVN/{code}"
    return [
        {
            "working_url_id": stable_id("figure1_working_url", "recorded_dataverse_dataset_zip", url, target_rel, repo_path(path)),
            "route_kind": "recorded_dataverse_dataset_zip",
            "parent_corpus_database_id": parent,
            "artifact_id": artifact_id,
            "provider": "dataverse",
            "url": url,
            "url_field": "dataverse_dataset_access_api",
            "final_url": "",
            "url_is_temporary": "false",
            "target_local_path": target_rel,
            "access_metadata_path": repo_path(path),
            "status_code": "",
            "content_type": "application/zip",
            "content_length": str(target.stat().st_size),
            "byte_size": str(target.stat().st_size),
            "sha256": "",
            "repull_supported": "true",
            "source_evidence": repo_path(path),
            "notes": "dataset-level Dataverse access route inferred from successful local dataset zip and metadata persistent ID",
        }
    ]


def working_urls_from_provider_manifests(
    paths: list[Path],
    basename_to_paths: dict[str, list[str]],
    artifact_by_path: dict[str, str],
    artifact_by_sha: dict[str, str],
    parent_by_path: dict[str, str],
    proposal_by_artifact: dict[str, dict[str, str]],
) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for path in provider_manifest_paths(paths):
        if path.suffix.lower() == ".csv":
            rows.extend(csv_provider_manifest_rows(path, basename_to_paths, artifact_by_path, artifact_by_sha, parent_by_path, proposal_by_artifact))
            continue
        payload = load_json(path)
        if isinstance(payload, (dict, list)):
            rows.extend(json_provider_manifest_rows(path, payload, basename_to_paths, artifact_by_path, artifact_by_sha, parent_by_path, proposal_by_artifact))
    return rows


def working_url_from_sidecar(
    path: Path,
    payload: dict[str, Any],
    artifact_by_path: dict[str, str],
    artifact_by_sha: dict[str, str],
    parent_by_path: dict[str, str],
    proposal_by_artifact: dict[str, dict[str, str]],
) -> dict[str, str] | None:
    ok = payload.get("ok")
    status_code = safe_text(payload.get("status_code"))
    if ok not in {True, "true", "True", "1", 1}:
        return None
    if status_code and not status_code.startswith(("2", "3")):
        return None
    stable_url = safe_text(payload.get("url"), 40000)
    if not stable_url:
        return None
    saved_file = as_repo_path(payload.get("saved_file"))
    saved_preview = as_repo_path(payload.get("saved_preview"))
    target = saved_file or saved_preview
    route_kind = "recorded_download_json" if saved_file else "recorded_probe_json"
    sha = safe_text(payload.get("sha256"))
    artifact_id = artifact_by_path.get(target) or artifact_by_sha.get(sha, "")
    artifact = proposal_by_artifact.get(artifact_id, {})
    parent = artifact.get("parent_corpus_database_id") or parent_by_path.get(target, "")
    return {
        "working_url_id": stable_id("figure1_working_url", route_kind, stable_url, target, repo_path(path)),
        "route_kind": route_kind,
        "parent_corpus_database_id": parent,
        "artifact_id": artifact_id,
        "provider": provider_from_url(stable_url, artifact.get("provider", "")),
        "url": stable_url,
        "url_field": "url",
        "final_url": safe_text(payload.get("final_url"), 40000),
        "url_is_temporary": "true" if looks_temporary_url(stable_url) else "false",
        "target_local_path": target,
        "access_metadata_path": repo_path(path),
        "status_code": status_code,
        "content_type": safe_text(payload.get("content_type")),
        "content_length": safe_text(payload.get("content_length")),
        "byte_size": safe_text(payload.get("bytes_written") or payload.get("content_length")),
        "sha256": sha,
        "repull_supported": "true" if saved_file and not looks_temporary_url(stable_url) else "false",
        "source_evidence": repo_path(path),
        "notes": "stable provider URL from successful local access sidecar",
    }


def working_urls_from_status(
    status_rows: list[dict[str, str]],
    proposal_by_artifact: dict[str, dict[str, str]],
) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for status in status_rows:
        artifact = proposal_by_artifact.get(status.get("artifact_id", ""), {})
        url, url_field, url_is_temporary = preferred_artifact_url(artifact)
        if not url:
            url = safe_text(status.get("raw_url"), 40000)
            url_field = "status.raw_url"
            url_is_temporary = "true" if looks_temporary_url(url) else "false"
        target = as_repo_path(status.get("mirror_local_path") or status.get("source_local_path"))
        if not url or not target:
            continue
        mirror_status = safe_text(status.get("mirror_status"))
        if mirror_status not in {"downloaded", "already_local", "already_mirrored_cache"}:
            continue
        rows.append(
            {
                "working_url_id": stable_id("figure1_working_url", "source_artifact_status", url, target, status.get("artifact_id")),
                "route_kind": "source_artifact_status",
                "parent_corpus_database_id": status.get("parent_corpus_database_id", ""),
                "artifact_id": status.get("artifact_id", ""),
                "provider": provider_from_url(url, artifact.get("provider", "")),
                "url": url,
                "url_field": url_field,
                "final_url": safe_text(artifact.get("raw_url"), 40000) if looks_temporary_url(safe_text(artifact.get("raw_url"), 40000)) else "",
                "url_is_temporary": url_is_temporary,
                "target_local_path": target,
                "access_metadata_path": "",
                "status_code": "",
                "content_type": safe_text(artifact.get("mime_type")),
                "content_length": safe_text(artifact.get("byte_size")),
                "byte_size": safe_text(status.get("mirror_byte_size") or artifact.get("byte_size")),
                "sha256": safe_text(status.get("mirror_sha256") or artifact.get("sha256")),
                "repull_supported": "true" if url_is_temporary != "true" else "false",
                "source_evidence": repo_path(STATUS_TSV),
                "notes": f"mirror_status={mirror_status}",
            }
        )
    return rows


def dedupe_working_urls(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    by_key: dict[tuple[str, str, str, str], dict[str, str]] = {}
    for row in rows:
        key = (row.get("url", ""), row.get("target_local_path", ""), row.get("sha256", ""), row.get("route_kind", ""))
        if key not in by_key:
            by_key[key] = row
            continue
        existing = by_key[key]
        for field, value in row.items():
            if not existing.get(field) and value:
                existing[field] = value
        existing["notes"] = " | ".join(part for part in [existing.get("notes"), row.get("notes")] if part)
    return sorted(by_key.values(), key=lambda row: (row.get("parent_corpus_database_id", ""), row.get("target_local_path", ""), row.get("route_kind", ""), row.get("url", "")))


def manifest_rows(
    working_rows: list[dict[str, str]],
    proposal_by_artifact: dict[str, dict[str, str]],
) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for row in working_rows:
        if row.get("repull_supported") != "true":
            continue
        artifact = proposal_by_artifact.get(row.get("artifact_id", ""), {})
        target = row.get("target_local_path", "")
        if not target:
            continue
        file_name = artifact.get("file_name") or Path(target).name
        rehydration_id = stable_id("figure1_rehydrate", row.get("url"), target, row.get("sha256"))
        metadata_local_path = row.get("access_metadata_path", "")
        if row.get("route_kind") != "recorded_download_json":
            metadata_local_path = f"steps/source_inventory/figure1/rehydration/access_events/{rehydration_id}.json"
        rows.append(
            {
                "rehydration_id": rehydration_id,
                "parent_corpus_database_id": row.get("parent_corpus_database_id", ""),
                "artifact_id": row.get("artifact_id", ""),
                "provider": row.get("provider", ""),
                "artifact_role": artifact.get("artifact_role", ""),
                "file_name": file_name,
                "file_type": artifact.get("file_type") or file_type(file_name),
                "url": row.get("url", ""),
                "url_field": row.get("url_field", ""),
                "final_url": row.get("final_url", ""),
                "target_local_path": target,
                "metadata_local_path": metadata_local_path,
                "expected_sha256": row.get("sha256", ""),
                "expected_byte_size": row.get("byte_size", ""),
                "content_type": row.get("content_type", ""),
                "route_kind": row.get("route_kind", ""),
                "repull_supported": row.get("repull_supported", ""),
                "source_evidence": row.get("source_evidence", ""),
                "notes": row.get("notes", ""),
            }
        )
    by_key: dict[tuple[str, str, str], dict[str, str]] = {}
    for row in rows:
        key = (row["target_local_path"], row["url"], row["expected_sha256"])
        if key not in by_key:
            by_key[key] = row
            continue
        existing = by_key[key]
        for field, value in row.items():
            if not existing.get(field) and value:
                existing[field] = value
    return sorted(by_key.values(), key=lambda row: (row["parent_corpus_database_id"], row["target_local_path"], row["url"]))


def gap_reason(local_path: str, row: dict[str, str]) -> tuple[str, str]:
    lower = local_path.lower()
    name = Path(local_path).name.lower()
    if row.get("mirror_status") == "component_metadata_recorded":
        return "generated_component_metadata", "rerun make source-artifact-mirror-sample from tracked proposal"
    if name.endswith(("_download.json", "_probe.json")) or "landing_probe" in name or "raw_probe" in name:
        return "access_metadata_sidecar", "recreated as access records by rehydrate script where matching working URL exists"
    if name.endswith("_preview.bin") or "landing_preview" in name or "raw_preview" in name:
        return "probe_preview_bytes", "refetch from corresponding probe URL only if preview bytes are needed"
    if "unpacked" in lower or "/analysis/" in lower or "/osf_xqd3v_outputs/" in lower:
        return "derived_or_unpacked_local_file", "rerun package-specific unpack/build step from parent archive"
    return "missing_stable_download_route", "add or recover provider download URL before this local artifact is repullable"


def gap_rows(
    status_rows: list[dict[str, str]],
    proposal_by_artifact: dict[str, dict[str, str]],
    downloadable_targets: set[str],
) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for status in status_rows:
        target = as_repo_path(status.get("mirror_local_path") or status.get("source_local_path"))
        if not target or target in downloadable_targets:
            continue
        artifact = proposal_by_artifact.get(status.get("artifact_id", ""), {})
        reason, recovery = gap_reason(target, status)
        rows.append(
            {
                "artifact_id": status.get("artifact_id", ""),
                "parent_corpus_database_id": status.get("parent_corpus_database_id", ""),
                "artifact_role": status.get("artifact_role", ""),
                "file_name": status.get("file_name", ""),
                "local_path": target,
                "sha256": status.get("mirror_sha256", ""),
                "byte_size": status.get("mirror_byte_size", ""),
                "gap_reason": reason,
                "candidate_recovery_route": recovery,
                "notes": artifact.get("notes", ""),
            }
        )
    return sorted(rows, key=lambda row: (row["gap_reason"], row["parent_corpus_database_id"], row["local_path"]))


def summary_rows(working: list[dict[str, str]], manifest: list[dict[str, str]], gaps: list[dict[str, str]]) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []

    def add(metric: str, value: str, count: int) -> None:
        out.append({"metric": metric, "value": value, "count": str(count)})

    add("total", "working_urls", len(working))
    add("total", "repull_manifest_rows", len(manifest))
    add("total", "rehydration_gaps", len(gaps))
    add("total", "downloadable_targets", len({row["target_local_path"] for row in manifest}))
    for field, rows in [("route_kind", working), ("parent_corpus_database_id", manifest), ("gap_reason", gaps)]:
        counts: dict[str, int] = {}
        for row in rows:
            key = row.get(field, "")
            counts[key] = counts.get(key, 0) + 1
        for value, count in sorted(counts.items()):
            add(field, value, count)
    return out


def main() -> None:
    global OUTPUT_ROOT, WORKING_URLS_TSV, WORKING_URLS_JSON, MANIFEST_TSV, MANIFEST_JSON, GAPS_TSV, SUMMARY_TSV
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--proposal", default=str(PROPOSAL_TSV))
    parser.add_argument("--status", default=str(STATUS_TSV))
    parser.add_argument("--source-inventory-root", default=str(SOURCE_INVENTORY_ROOT))
    parser.add_argument("--output-root", default=str(OUTPUT_ROOT))
    parser.add_argument("--replace", action="store_true")
    args = parser.parse_args()

    proposal_path = resolve_path(args.proposal)
    status_path = resolve_path(args.status)
    source_inventory_root = resolve_path(args.source_inventory_root)
    OUTPUT_ROOT = resolve_path(args.output_root)
    WORKING_URLS_TSV = OUTPUT_ROOT / "figure1-working-urls.tsv"
    WORKING_URLS_JSON = OUTPUT_ROOT / "figure1-working-urls.json"
    MANIFEST_TSV = OUTPUT_ROOT / "figure1-rehydration-manifest.tsv"
    MANIFEST_JSON = OUTPUT_ROOT / "figure1-rehydration-manifest.json"
    GAPS_TSV = OUTPUT_ROOT / "figure1-rehydration-gaps.tsv"
    SUMMARY_TSV = OUTPUT_ROOT / "figure1-rehydration-summary.tsv"

    proposal_rows = read_tsv(proposal_path)
    status_rows = read_tsv(status_path)
    proposal_by_artifact, artifact_by_path, artifact_by_sha, parent_by_path = build_indexes(proposal_rows, status_rows)
    roots = inventory_roots(source_inventory_root)
    local_files = all_files(roots)
    basename_to_paths = basename_index(local_files)

    working_rows = working_urls_from_status(status_rows, proposal_by_artifact)
    for path in sidecar_paths(roots):
        payload = load_json(path)
        if isinstance(payload, dict):
            row = working_url_from_sidecar(path, payload, artifact_by_path, artifact_by_sha, parent_by_path, proposal_by_artifact)
            if row:
                working_rows.append(row)
    working_rows.extend(
        working_urls_from_provider_manifests(
            local_files,
            basename_to_paths,
            artifact_by_path,
            artifact_by_sha,
            parent_by_path,
            proposal_by_artifact,
        )
    )
    working_rows = dedupe_working_urls(working_rows)
    manifest = manifest_rows(working_rows, proposal_by_artifact)
    downloadable_targets = {row["target_local_path"] for row in manifest}
    gaps = gap_rows(status_rows, proposal_by_artifact, downloadable_targets)
    summary = summary_rows(working_rows, manifest, gaps)

    working_columns = [
        "working_url_id",
        "route_kind",
        "parent_corpus_database_id",
        "artifact_id",
        "provider",
        "url",
        "url_field",
        "final_url",
        "url_is_temporary",
        "target_local_path",
        "access_metadata_path",
        "status_code",
        "content_type",
        "content_length",
        "byte_size",
        "sha256",
        "repull_supported",
        "source_evidence",
        "notes",
    ]
    manifest_columns = [
        "rehydration_id",
        "parent_corpus_database_id",
        "artifact_id",
        "provider",
        "artifact_role",
        "file_name",
        "file_type",
        "url",
        "url_field",
        "final_url",
        "target_local_path",
        "metadata_local_path",
        "expected_sha256",
        "expected_byte_size",
        "content_type",
        "route_kind",
        "repull_supported",
        "source_evidence",
        "notes",
    ]
    gap_columns = [
        "artifact_id",
        "parent_corpus_database_id",
        "artifact_role",
        "file_name",
        "local_path",
        "sha256",
        "byte_size",
        "gap_reason",
        "candidate_recovery_route",
        "notes",
    ]
    write_tsv(WORKING_URLS_TSV, working_rows, working_columns, args.replace)
    write_json(
        WORKING_URLS_JSON,
        {
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "proposal": repo_path(proposal_path),
            "status": repo_path(status_path),
            "inventory_roots": [repo_path(path) for path in roots],
            "records": working_rows,
        },
        args.replace,
    )
    write_tsv(MANIFEST_TSV, manifest, manifest_columns, args.replace)
    write_json(
        MANIFEST_JSON,
        {
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "manifest": manifest,
        },
        args.replace,
    )
    write_tsv(GAPS_TSV, gaps, gap_columns, args.replace)
    write_tsv(SUMMARY_TSV, summary, ["metric", "value", "count"], args.replace)
    print(
        "Figure 1 rehydration manifest: "
        f"working_urls={len(working_rows)}; repull_rows={len(manifest)}; "
        f"downloadable_targets={len(downloadable_targets)}; gaps={len(gaps)}"
    )


if __name__ == "__main__":
    main()
