#!/usr/bin/env python3
"""Probe, download, and stage replication-lead sources for overnight harvesting.

This script does not force every source into the current D-vs-N figure build.
Instead it classifies each known lead into one of three durable terminal states:

- promoted: a parser produced pair rows in the main pair schema
- staged: source files or manifests were captured but promotion is blocked
- probed: access, overlap, or policy checks were recorded without download/promotion

The current implementation focuses on durable bookkeeping and unattended access
checks. Source-specific parsers can be added incrementally without changing the
manifest or reporting contract.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, unquote, urlparse

import pandas as pd
import requests


ROOT = Path(__file__).resolve().parents[1]
RAW_REPL = ROOT / "data" / "raw" / "replication_projects"
LEAD_REGISTRY = RAW_REPL / "lead_registry.csv"
RAW_HARVEST = RAW_REPL / "lead_harvest"
HARVEST_DERIVED = ROOT / "data" / "derived" / "replication_pairs" / "harvest"
PROMOTED_DIR = HARVEST_DERIVED / "promoted"
STAGED_DIR = HARVEST_DERIVED / "staged"
MANIFEST_PATH = HARVEST_DERIVED / "harvest_manifest.csv"
QUEUE_STATUS_CSV = HARVEST_DERIVED / "lead_queue_status.csv"
QUEUE_STATUS_MD = ROOT / "reports" / "corpus_candidates" / "replication_lead_queue.md"

TIMEOUT = (20, 60)
TEXT_PREVIEW_BYTES = 131072
DOWNLOAD_MAX_BYTES = 200 * 1024 * 1024
MAX_FILE_DOWNLOAD_BYTES = 50 * 1024 * 1024
MAX_LEAD_DOWNLOAD_BYTES = 150 * 1024 * 1024
MAX_LEAD_DOWNLOAD_FILES = 12
USER_AGENT = "PublishedSmallNStudiesLeadHarvester/1.0"
DOWNLOADABLE_SUFFIXES = {
    ".csv",
    ".tsv",
    ".tab",
    ".txt",
    ".json",
    ".md",
    ".r",
    ".rmd",
    ".do",
    ".py",
    ".xlsx",
    ".xls",
    ".pdf",
    ".zip",
    ".sav",
    ".dta",
    ".rds",
    ".doc",
    ".docx",
    ".ppt",
    ".pptx",
}

PAIR_SCHEMA_COLUMNS = [
    "source_dataset",
    "project",
    "pair_id",
    "original_title",
    "replication_title",
    "original_doi",
    "replication_doi",
    "outcome",
    "D_original",
    "N_original",
    "D_replication",
    "N_replication",
    "raw_file",
    "match_author",
]


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def slugify(text: object) -> str:
    s = str(text or "").strip().lower()
    s = re.sub(r"[^a-z0-9]+", "_", s)
    return s.strip("_") or "missing"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def sanitize_filename(name: str) -> str:
    name = re.sub(r"[^\w.\-]+", "_", name.strip())
    return name or "download.bin"


def filename_from_response(response: requests.Response, fallback_url: str) -> str:
    disposition = response.headers.get("content-disposition", "")
    match = re.search(r'filename\*?=(?:UTF-8\'\')?"?([^";]+)"?', disposition, flags=re.I)
    if match:
        return sanitize_filename(match.group(1))
    path_name = Path(urlparse(response.url or fallback_url).path).name
    if path_name:
        return sanitize_filename(path_name)
    return "download.bin"


def request_session() -> requests.Session:
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})
    return session


def request_json(session: requests.Session, url: str) -> dict[str, Any]:
    response = session.get(url, timeout=TIMEOUT, allow_redirects=True)
    response.raise_for_status()
    return response.json()


def iter_osf_pages(session: requests.Session, url: str) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    next_url = url
    while next_url:
        payload = request_json(session, next_url)
        items.extend(payload.get("data", []))
        next_url = payload.get("links", {}).get("next")
    return items


def probe_url(session: requests.Session, url: str, artifact_dir: Path, prefix: str) -> dict[str, Any]:
    out: dict[str, Any] = {
        "url": url,
        "final_url": "",
        "ok": False,
        "status_code": "",
        "content_type": "",
        "content_length": "",
        "saved_preview": "",
        "error": "",
    }
    if not url:
        out["error"] = "missing_url"
        return out

    try:
        response = session.get(url, timeout=TIMEOUT, allow_redirects=True, stream=True)
        out["status_code"] = str(response.status_code)
        out["final_url"] = response.url
        out["content_type"] = response.headers.get("content-type", "")
        out["content_length"] = response.headers.get("content-length", "")
        out["ok"] = bool(response.ok)

        preview_path = artifact_dir / f"{prefix}_preview.bin"
        preview_bytes = b""
        for chunk in response.iter_content(chunk_size=8192):
            if not chunk:
                continue
            preview_bytes += chunk
            if len(preview_bytes) >= TEXT_PREVIEW_BYTES:
                preview_bytes = preview_bytes[:TEXT_PREVIEW_BYTES]
                break

        if preview_bytes:
            preview_path.write_bytes(preview_bytes)
            out["saved_preview"] = str(preview_path)

        response.close()
    except Exception as exc:  # pragma: no cover - defensive
        out["error"] = f"{type(exc).__name__}: {exc}"

    (artifact_dir / f"{prefix}_probe.json").write_text(json.dumps(out, indent=2, sort_keys=True))
    return out


def download_url(session: requests.Session, url: str, artifact_dir: Path, prefix: str) -> dict[str, Any]:
    out: dict[str, Any] = {
        "url": url,
        "final_url": "",
        "ok": False,
        "status_code": "",
        "content_type": "",
        "content_length": "",
        "saved_file": "",
        "sha256": "",
        "bytes_written": 0,
        "error": "",
    }
    if not url:
        out["error"] = "missing_url"
        return out

    try:
        response = session.get(url, timeout=TIMEOUT, allow_redirects=True, stream=True)
        out["status_code"] = str(response.status_code)
        out["final_url"] = response.url
        out["content_type"] = response.headers.get("content-type", "")
        out["content_length"] = response.headers.get("content-length", "")
        if not response.ok:
            out["error"] = f"http_{response.status_code}"
            response.close()
            (artifact_dir / f"{prefix}_download.json").write_text(json.dumps(out, indent=2, sort_keys=True))
            return out

        content_length = response.headers.get("content-length")
        if content_length:
            try:
                if int(content_length) > DOWNLOAD_MAX_BYTES:
                    out["error"] = "file_too_large"
                    response.close()
                    (artifact_dir / f"{prefix}_download.json").write_text(json.dumps(out, indent=2, sort_keys=True))
                    return out
            except ValueError:
                pass

        filename = filename_from_response(response, url)
        path = artifact_dir / f"{prefix}__{filename}"
        hasher = hashlib.sha256()
        bytes_written = 0
        with path.open("wb") as fh:
            for chunk in response.iter_content(chunk_size=65536):
                if not chunk:
                    continue
                bytes_written += len(chunk)
                if bytes_written > DOWNLOAD_MAX_BYTES:
                    fh.close()
                    path.unlink(missing_ok=True)
                    response.close()
                    out["error"] = "file_too_large"
                    (artifact_dir / f"{prefix}_download.json").write_text(json.dumps(out, indent=2, sort_keys=True))
                    return out
                fh.write(chunk)
                hasher.update(chunk)
        response.close()

        out["ok"] = True
        out["saved_file"] = str(path)
        out["sha256"] = hasher.hexdigest()
        out["bytes_written"] = bytes_written
    except Exception as exc:  # pragma: no cover - defensive
        out["error"] = f"{type(exc).__name__}: {exc}"

    (artifact_dir / f"{prefix}_download.json").write_text(json.dumps(out, indent=2, sort_keys=True))
    return out


def extract_related_urls(preview_path: str) -> list[str]:
    if not preview_path:
        return []
    try:
        text = Path(preview_path).read_text(errors="ignore")
    except Exception:
        return []
    matches = re.findall(r"https?://[^\s\"'<>]+", text)
    cleaned = []
    for url in matches:
        url = url.rstrip(").,;")
        if any(host in url for host in ["osf.io/", "github.com/", "dataverse.harvard.edu/", "openicpsr.org/"]):
            cleaned.append(url)
    seen = set()
    out = []
    for url in cleaned:
        if url not in seen:
            seen.add(url)
            out.append(url)
    return out


def choose_downloadable_files(files: list[dict[str, Any]]) -> list[dict[str, Any]]:
    def score(row: dict[str, Any]) -> tuple[int, int, int, str]:
        name = str(row.get("name", "")).lower()
        suffix = Path(name).suffix.lower()
        if suffix in {".csv", ".tsv", ".tab", ".xlsx", ".xls", ".sav", ".dta", ".rds"}:
            pri = 0
        elif suffix in {".json", ".txt", ".md", ".r", ".rmd", ".do", ".py"}:
            pri = 1
        elif suffix in {".zip", ".pdf", ".doc", ".docx", ".ppt", ".pptx"}:
            pri = 2
        else:
            pri = 3
        size = int(row.get("size") or 0)
        return (pri, size, len(name), name)

    total_bytes = 0
    out: list[dict[str, Any]] = []
    for row in sorted(files, key=score):
        size = int(row.get("size") or 0)
        suffix = Path(str(row.get("name", ""))).suffix.lower()
        if suffix not in DOWNLOADABLE_SUFFIXES:
            continue
        if size <= 0 or size > MAX_FILE_DOWNLOAD_BYTES:
            continue
        if len(out) >= MAX_LEAD_DOWNLOAD_FILES:
            break
        if total_bytes + size > MAX_LEAD_DOWNLOAD_BYTES:
            continue
        out.append(row)
        total_bytes += size
    return out


def download_file_records(
    session: requests.Session, files: list[dict[str, Any]], artifact_dir: Path, prefix: str
) -> list[dict[str, Any]]:
    downloads: list[dict[str, Any]] = []
    for idx, row in enumerate(files, start=1):
        url = str(row.get("download_url", "")).strip()
        if not url:
            continue
        dl = download_url(session, url, artifact_dir, f"{prefix}_{idx:02d}")
        dl["name"] = row.get("name", "")
        dl["materialized_path"] = row.get("materialized_path", "")
        downloads.append(dl)
    return downloads


def osf_node_id_from_url(url: str) -> str:
    parts = [part for part in urlparse(url).path.split("/") if part]
    return parts[0] if parts else ""


def walk_osf_files(
    session: requests.Session,
    listing_url: str,
    rows: list[dict[str, Any]],
    *,
    node_id: str,
    node_title: str,
) -> None:
    for item in iter_osf_pages(session, listing_url):
        attrs = item.get("attributes", {})
        kind = attrs.get("kind", "")
        row = {
            "node_id": node_id,
            "node_title": node_title,
            "id": item.get("id", ""),
            "name": attrs.get("name", ""),
            "kind": kind,
            "size": attrs.get("size", 0) or 0,
            "materialized_path": attrs.get("materialized_path", ""),
            "download_url": item.get("links", {}).get("download", ""),
            "html_url": item.get("links", {}).get("html", ""),
            "iri": item.get("links", {}).get("iri", ""),
            "provider": attrs.get("provider", ""),
            "api_url": item.get("links", {}).get("self", ""),
        }
        rows.append(row)
        if kind == "folder":
            child_url = item.get("relationships", {}).get("files", {}).get("links", {}).get("related", {}).get("href", "")
            if child_url:
                walk_osf_files(session, child_url, rows, node_id=node_id, node_title=node_title)


def walk_osf_node(
    session: requests.Session,
    node_id: str,
    rows: list[dict[str, Any]],
    storage_rows: list[dict[str, Any]],
    visited: set[str],
) -> None:
    if not node_id or node_id in visited:
        return
    visited.add(node_id)

    node_payload = request_json(session, f"https://api.osf.io/v2/nodes/{node_id}/")
    node_data = node_payload.get("data", {})
    node_title = node_data.get("attributes", {}).get("title", "") or node_id

    storages = request_json(session, f"https://api.osf.io/v2/nodes/{node_id}/files/")
    for storage in storages.get("data", []):
        related = storage.get("relationships", {}).get("files", {}).get("links", {}).get("related", {}).get("href", "")
        storage_rows.append(
            {
                "node_id": node_id,
                "node_title": node_title,
                "id": storage.get("id", ""),
                "name": storage.get("attributes", {}).get("name", ""),
                "related": related,
            }
        )
        if related:
            walk_osf_files(session, related, rows, node_id=node_id, node_title=node_title)

    for child in iter_osf_pages(session, f"https://api.osf.io/v2/nodes/{node_id}/children/"):
        child_id = child.get("id", "")
        if child_id:
            walk_osf_node(session, child_id, rows, storage_rows, visited)


def harvest_osf(session: requests.Session, url: str, artifact_dir: Path, probe_only: bool) -> dict[str, Any]:
    node_id = osf_node_id_from_url(url)
    out = {
        "handler": "osf",
        "manifest_file": "",
        "file_list_csv": "",
        "discovered_file_count": 0,
        "downloaded_files": [],
        "primary_file": "",
        "error": "",
    }
    if not node_id:
        out["error"] = "missing_osf_node_id"
        return out
    try:
        rows: list[dict[str, Any]] = []
        storage_rows = []
        walk_osf_node(session, node_id, rows, storage_rows, set())
        manifest = {"node_id": node_id, "storages": storage_rows, "files": rows}
        manifest_path = artifact_dir / "osf_manifest.json"
        manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True))
        file_list_path = artifact_dir / "osf_file_list.csv"
        pd.DataFrame(rows).to_csv(file_list_path, index=False)
        out["manifest_file"] = str(manifest_path)
        out["file_list_csv"] = str(file_list_path)
        out["discovered_file_count"] = len(rows)
        if not probe_only:
            downloads = download_file_records(session, choose_downloadable_files(rows), artifact_dir, "osf")
            out["downloaded_files"] = downloads
            if downloads:
                out["primary_file"] = downloads[0].get("saved_file", "")
    except Exception as exc:  # pragma: no cover - defensive
        out["error"] = f"{type(exc).__name__}: {exc}"
    return out


def persistent_id_from_url(url: str) -> str:
    parsed = urlparse(url)
    query = parse_qs(parsed.query)
    if "persistentId" in query and query["persistentId"]:
        return query["persistentId"][0]
    match = re.search(r"(doi:10\.\d{4,9}/[A-Za-z0-9._-]+/[A-Za-z0-9._-]+)", unquote(url))
    if match:
        return match.group(1)
    return ""


def dataverse_download_url(base_url: str, file_id: int) -> str:
    parsed = urlparse(base_url)
    origin = f"{parsed.scheme}://{parsed.netloc}"
    return f"{origin}/api/access/datafile/{file_id}"


def harvest_dataverse(session: requests.Session, url: str, artifact_dir: Path, probe_only: bool) -> dict[str, Any]:
    persistent_id = persistent_id_from_url(url)
    out = {
        "handler": "dataverse",
        "manifest_file": "",
        "file_list_csv": "",
        "discovered_file_count": 0,
        "downloaded_files": [],
        "primary_file": "",
        "error": "",
    }
    if not persistent_id:
        out["error"] = "missing_persistent_id"
        return out
    parsed = urlparse(url)
    origin = f"{parsed.scheme}://{parsed.netloc}" if parsed.scheme and parsed.netloc else "https://dataverse.harvard.edu"
    api_url = f"{origin}/api/datasets/:persistentId?persistentId={persistent_id}"
    try:
        payload = request_json(session, api_url)
        files = []
        for item in payload.get("data", {}).get("latestVersion", {}).get("files", []):
            data_file = item.get("dataFile", {})
            files.append(
                {
                    "id": data_file.get("id", ""),
                    "name": data_file.get("filename", "") or item.get("label", ""),
                    "label": item.get("label", ""),
                    "size": data_file.get("filesize", 0) or 0,
                    "download_url": dataverse_download_url(origin, data_file.get("id", 0)),
                    "description": item.get("description", ""),
                    "restricted": item.get("restricted", False),
                    "content_type": data_file.get("contentType", ""),
                }
            )
        manifest_path = artifact_dir / "dataverse_manifest.json"
        manifest_path.write_text(json.dumps(payload, indent=2, sort_keys=True))
        file_list_path = artifact_dir / "dataverse_file_list.csv"
        pd.DataFrame(files).to_csv(file_list_path, index=False)
        out["manifest_file"] = str(manifest_path)
        out["file_list_csv"] = str(file_list_path)
        out["discovered_file_count"] = len(files)
        if not probe_only:
            downloads = download_file_records(session, choose_downloadable_files(files), artifact_dir, "dataverse")
            out["downloaded_files"] = downloads
            if downloads:
                out["primary_file"] = downloads[0].get("saved_file", "")
    except Exception as exc:  # pragma: no cover - defensive
        out["error"] = f"{type(exc).__name__}: {exc}"
    return out


def parse_github_raw(url: str) -> tuple[str, str, str, str]:
    parsed = urlparse(url)
    parts = [part for part in parsed.path.split("/") if part]
    if parsed.netloc != "raw.githubusercontent.com" or len(parts) < 5:
        return "", "", "", ""
    owner, repo, branch = parts[0], parts[1], parts[2]
    path = "/".join(parts[3:])
    return owner, repo, branch, path


def github_api_headers(session: requests.Session) -> dict[str, str]:
    return dict(session.headers)


def harvest_github_contents(session: requests.Session, raw_url: str, artifact_dir: Path, probe_only: bool) -> dict[str, Any]:
    owner, repo, branch, path = parse_github_raw(raw_url)
    out = {
        "handler": "github_contents",
        "manifest_file": "",
        "file_list_csv": "",
        "discovered_file_count": 0,
        "downloaded_files": [],
        "primary_file": "",
        "error": "",
    }
    if not all([owner, repo, branch, path]):
        out["error"] = "unsupported_github_raw_url"
        return out

    dir_path = str(Path(path).parent)
    api_url = f"https://api.github.com/repos/{owner}/{repo}/contents/{dir_path}?ref={branch}"
    try:
        response = session.get(api_url, timeout=TIMEOUT, headers=github_api_headers(session))
        response.raise_for_status()
        payload = response.json()
        rows = []
        for item in payload:
            rows.append(
                {
                    "name": item.get("name", ""),
                    "path": item.get("path", ""),
                    "size": item.get("size", 0) or 0,
                    "download_url": item.get("download_url", ""),
                    "html_url": item.get("html_url", ""),
                    "type": item.get("type", ""),
                }
            )
        manifest_path = artifact_dir / "github_contents_manifest.json"
        manifest_path.write_text(json.dumps(payload, indent=2, sort_keys=True))
        file_list_path = artifact_dir / "github_contents_file_list.csv"
        pd.DataFrame(rows).to_csv(file_list_path, index=False)
        out["manifest_file"] = str(manifest_path)
        out["file_list_csv"] = str(file_list_path)
        out["discovered_file_count"] = len(rows)
        downloadable = [row for row in rows if row.get("type") == "file"]
        if not probe_only:
            downloads = download_file_records(session, choose_downloadable_files(downloadable), artifact_dir, "github")
            out["downloaded_files"] = downloads
            if downloads:
                out["primary_file"] = downloads[0].get("saved_file", "")
    except Exception as exc:  # pragma: no cover - defensive
        out["error"] = f"{type(exc).__name__}: {exc}"
    return out


def harvest_host_specific(
    session: requests.Session,
    lead: pd.Series,
    landing_probe: dict[str, Any],
    artifact_dir: Path,
    probe_only: bool,
) -> dict[str, Any]:
    parser_family = str(lead.get("parser_family", "")).strip()
    landing_url = str(lead.get("landing_url", "")).strip()
    raw_url = str(lead.get("raw_url", "")).strip()
    related_urls = extract_related_urls(landing_probe.get("saved_preview", ""))

    if landing_url.startswith("https://osf.io/") or any(url.startswith("https://osf.io/") for url in related_urls):
        osf_url = landing_url if landing_url.startswith("https://osf.io/") else next(url for url in related_urls if url.startswith("https://osf.io/"))
        return harvest_osf(session, osf_url, artifact_dir, probe_only)
    if "dataverse" in landing_url or "dataverse" in raw_url or any("dataverse" in url for url in related_urls):
        dv_url = landing_url or raw_url or next(url for url in related_urls if "dataverse" in url)
        return harvest_dataverse(session, dv_url, artifact_dir, probe_only)
    if raw_url.startswith("https://raw.githubusercontent.com/"):
        return harvest_github_contents(session, raw_url, artifact_dir, probe_only)
    if parser_family == "github_repo" and raw_url:
        # repo archive zip path already lives in raw_url; generic download covers it
        return {"handler": "github_repo_zip", "manifest_file": "", "file_list_csv": "", "discovered_file_count": 0, "downloaded_files": [], "primary_file": "", "error": ""}
    return {"handler": "", "manifest_file": "", "file_list_csv": "", "discovered_file_count": 0, "downloaded_files": [], "primary_file": "", "error": ""}


def should_attempt_download(lead: pd.Series, probe_only: bool) -> bool:
    if probe_only:
        return False
    return bool(lead.get("raw_url")) and str(lead.get("access_class", "")).strip() in {"public", "public_js"}


def infer_stage_blocker(lead: pd.Series) -> str:
    access_class = str(lead.get("access_class", "")).strip()
    default_action = str(lead.get("default_action", "")).strip()
    overlap_risk = str(lead.get("overlap_risk", "")).strip()
    directness_class = str(lead.get("directness_class", "")).strip()
    metric_class = str(lead.get("metric_class", "")).strip()

    if access_class == "yes_login":
        return "requires_login"
    if access_class == "manual":
        return "manual_navigation_required"
    if overlap_risk == "high":
        return "possible_duplicate"
    if directness_class not in {"direct", "direct_multisite"}:
        return "directness_needs_review"
    if metric_class == "non_d_summary":
        return "non_d_metric"
    if metric_class == "unknown":
        return "effect_conversion_policy_missing"
    if default_action == "probe_only":
        return "probe_only_by_policy"
    return "parser_family_not_implemented"


def stage_stub_row(
    lead: pd.Series,
    blocker: str,
    local_raw_file: str = "",
    manifest_file: str = "",
    file_list_csv: str = "",
    downloaded_file_count: int = 0,
) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "lead_id": lead["lead_id"],
                "project": lead["project"],
                "source_family": lead["source_family"],
                "priority": lead["priority"],
                "default_action": lead["default_action"],
                "expected_rows": lead["expected_rows"],
                "landing_url": lead["landing_url"],
                "raw_url": lead["raw_url"],
                "local_raw_file": local_raw_file,
                "manifest_file": manifest_file,
                "file_list_csv": file_list_csv,
                "downloaded_file_count": downloaded_file_count,
                "promotion_blocker": blocker,
                "notes": lead["notes"],
            }
        ]
    )


def write_stage_stub(
    lead: pd.Series,
    blocker: str,
    local_raw_file: str = "",
    manifest_file: str = "",
    file_list_csv: str = "",
    downloaded_file_count: int = 0,
) -> str:
    ensure_dir(STAGED_DIR)
    out_path = STAGED_DIR / f"{lead['lead_id']}__stage.csv"
    stage_stub_row(
        lead,
        blocker,
        local_raw_file=local_raw_file,
        manifest_file=manifest_file,
        file_list_csv=file_list_csv,
        downloaded_file_count=downloaded_file_count,
    ).to_csv(out_path, index=False)
    return str(out_path)


def try_promote_downloaded_file(lead: pd.Series, local_file: str) -> tuple[str, str, str]:
    """Return terminal_status, blocker, promoted_csv_path.

    The only generic promotion supported today is a fully formed pair-table CSV
    that already matches the main build schema. Everything else is staged.
    """

    if not local_file:
        return "staged", "raw_file_missing", ""

    parser_family = str(lead.get("parser_family", "")).strip()
    if parser_family != "pair_table_csv":
        return "staged", "parser_family_not_implemented", ""

    path = Path(local_file)
    if path.suffix.lower() != ".csv":
        return "staged", "unsupported_promote_file_type", ""

    try:
        df = pd.read_csv(path)
    except Exception as exc:  # pragma: no cover - defensive
        return "staged", f"promote_read_failed:{type(exc).__name__}", ""

    missing = [col for col in PAIR_SCHEMA_COLUMNS if col not in df.columns]
    if missing:
        return "staged", "pair_schema_missing_columns", ""

    ensure_dir(PROMOTED_DIR)
    promoted_path = PROMOTED_DIR / f"{lead['lead_id']}__promoted_pairs.csv"
    df.to_csv(promoted_path, index=False)
    return "promoted", "", str(promoted_path)


def process_lead(session: requests.Session, lead: pd.Series, probe_only: bool) -> dict[str, Any]:
    artifact_dir = RAW_HARVEST / lead["lead_id"]
    ensure_dir(artifact_dir)

    landing_probe = probe_url(session, str(lead.get("landing_url", "")).strip(), artifact_dir, "landing")
    raw_probe: dict[str, Any] = {}
    raw_download: dict[str, Any] = {}
    if lead.get("raw_url"):
        raw_probe = probe_url(session, str(lead.get("raw_url", "")).strip(), artifact_dir, "raw")
        if should_attempt_download(lead, probe_only):
            raw_download = download_url(session, str(lead.get("raw_url", "")).strip(), artifact_dir, "raw")

    host_harvest = harvest_host_specific(session, lead, landing_probe, artifact_dir, probe_only)
    harvested_downloads = host_harvest.get("downloaded_files", []) or []
    local_raw_file = raw_download.get("saved_file", "") if raw_download else ""
    if not local_raw_file and harvested_downloads:
        local_raw_file = harvested_downloads[0].get("saved_file", "")
    promoted_file = ""
    staged_file = ""
    blocker = ""
    terminal_status = ""
    manifest_file = host_harvest.get("manifest_file", "")
    file_list_csv = host_harvest.get("file_list_csv", "")
    downloaded_file_count = len(harvested_downloads) + (1 if raw_download.get("saved_file", "") else 0)

    default_action = str(lead.get("default_action", "")).strip()
    if default_action == "auto_integrate":
        if local_raw_file:
            terminal_status, blocker, promoted_file = try_promote_downloaded_file(lead, local_raw_file)
            if terminal_status != "promoted":
                staged_file = write_stage_stub(
                    lead,
                    blocker,
                    local_raw_file=local_raw_file,
                    manifest_file=manifest_file,
                    file_list_csv=file_list_csv,
                    downloaded_file_count=downloaded_file_count,
                )
        else:
            blocker = infer_stage_blocker(lead)
            terminal_status = "staged"
            staged_file = write_stage_stub(
                lead,
                blocker,
                local_raw_file=local_raw_file,
                manifest_file=manifest_file,
                file_list_csv=file_list_csv,
                downloaded_file_count=downloaded_file_count,
            )
    elif default_action == "stage_only":
        blocker = infer_stage_blocker(lead)
        terminal_status = "staged"
        staged_file = write_stage_stub(
            lead,
            blocker,
            local_raw_file=local_raw_file,
            manifest_file=manifest_file,
            file_list_csv=file_list_csv,
            downloaded_file_count=downloaded_file_count,
        )
    else:
        blocker = infer_stage_blocker(lead)
        terminal_status = "probed" if blocker not in {"requires_login", "manual_navigation_required"} else "blocked"

    next_action = blocker
    if blocker == "parser_family_not_implemented":
        next_action = f"implement_parser:{lead.get('parser_family', '')}"
    elif blocker == "possible_duplicate":
        next_action = "dedupe_against_existing_corpus"
    elif blocker == "non_d_metric":
        next_action = "define_effect_conversion_policy"
    elif blocker == "effect_conversion_policy_missing":
        next_action = "inspect_downloaded_files_and_define_mapping"
    elif blocker == "requires_login":
        next_action = "manual_login_and_download"
    elif blocker == "probe_only_by_policy":
        next_action = "keep_as_probe_only"

    return {
        "run_utc": utc_now_iso(),
        "lead_id": lead["lead_id"],
        "project": lead["project"],
        "source_family": lead["source_family"],
        "priority": int(lead["priority"]),
        "default_action": default_action,
        "terminal_status": terminal_status,
        "access_class": lead["access_class"],
        "overlap_risk": lead["overlap_risk"],
        "directness_class": lead["directness_class"],
        "metric_class": lead["metric_class"],
        "expected_rows": lead["expected_rows"],
        "parser_family": lead["parser_family"],
        "landing_url": lead["landing_url"],
        "raw_url": lead["raw_url"],
        "landing_http_status": landing_probe.get("status_code", ""),
        "raw_http_status": raw_probe.get("status_code", ""),
        "landing_final_url": landing_probe.get("final_url", ""),
        "raw_final_url": raw_probe.get("final_url", ""),
        "downloaded_raw_file": local_raw_file,
        "downloaded_raw_bytes": raw_download.get("bytes_written", 0) if raw_download else 0,
        "downloaded_raw_sha256": raw_download.get("sha256", "") if raw_download else "",
        "manifest_file": manifest_file,
        "file_list_csv": file_list_csv,
        "discovered_file_count": host_harvest.get("discovered_file_count", 0),
        "downloaded_file_count": downloaded_file_count,
        "host_handler": host_harvest.get("handler", ""),
        "host_handler_error": host_harvest.get("error", ""),
        "artifact_dir": str(artifact_dir),
        "promoted_file": promoted_file,
        "staged_file": staged_file,
        "promotion_blocker": blocker,
        "next_action": next_action,
        "notes": lead["notes"],
    }


def render_queue_markdown(status_df: pd.DataFrame) -> str:
    total = len(status_df)
    counts = status_df["terminal_status"].value_counts().to_dict()

    lines = [
        "# Replication Lead Queue",
        "",
        "Generated from `lead_registry.csv` plus the latest harvest manifest.",
        "",
        f"- Total leads tracked: **{total}**",
        f"- Promoted: **{counts.get('promoted', 0)}**",
        f"- Staged: **{counts.get('staged', 0)}**",
        f"- Probed only: **{counts.get('probed', 0)}**",
        f"- Blocked: **{counts.get('blocked', 0)}**",
        "",
        "| Priority | Lead | Project | Action | Status | Files | Downloads | Blocker | Next action | Expected rows |",
        "|---:|---|---|---|---|---:|---:|---|---|---:|",
    ]

    for row in status_df.sort_values(["priority", "lead_id"]).itertuples(index=False):
        lines.append(
            f"| {row.priority} | {row.lead_id} | {row.project} | {row.default_action} | "
            f"{row.terminal_status} | {getattr(row, 'discovered_file_count', 0)} | {getattr(row, 'downloaded_file_count', 0)} | "
            f"{row.promotion_blocker or ''} | {row.next_action or ''} | {row.expected_rows} |"
        )
    return "\n".join(lines)


def load_registry() -> pd.DataFrame:
    if not LEAD_REGISTRY.exists():
        raise FileNotFoundError(f"Lead registry not found: {LEAD_REGISTRY}")
    registry = pd.read_csv(LEAD_REGISTRY).fillna("")
    registry["priority"] = pd.to_numeric(registry["priority"], errors="coerce").fillna(9999).astype(int)
    registry["expected_rows"] = pd.to_numeric(registry["expected_rows"], errors="coerce").fillna(0).astype(int)
    return registry.sort_values(["priority", "lead_id"]).reset_index(drop=True)


def select_registry_rows(registry: pd.DataFrame, lead_ids: list[str], limit: int | None) -> pd.DataFrame:
    out = registry
    if lead_ids:
        wanted = set(lead_ids)
        out = out.loc[out["lead_id"].isin(wanted)].copy()
    if limit is not None:
        out = out.head(limit).copy()
    return out.reset_index(drop=True)


def run(lead_ids: list[str], limit: int | None, probe_only: bool) -> pd.DataFrame:
    registry = load_registry()
    selected = select_registry_rows(registry, lead_ids, limit)
    if selected.empty:
        raise SystemExit("No matching leads selected.")

    ensure_dir(RAW_HARVEST)
    ensure_dir(HARVEST_DERIVED)
    ensure_dir(PROMOTED_DIR)
    ensure_dir(STAGED_DIR)
    ensure_dir(QUEUE_STATUS_MD.parent)

    session = request_session()
    manifest_rows = [process_lead(session, row, probe_only) for _, row in selected.iterrows()]
    manifest = pd.DataFrame(manifest_rows).sort_values(["priority", "lead_id"]).reset_index(drop=True)
    manifest.to_csv(MANIFEST_PATH, index=False)
    manifest.to_csv(QUEUE_STATUS_CSV, index=False)
    QUEUE_STATUS_MD.write_text(render_queue_markdown(manifest))
    return manifest


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lead-id", action="append", default=[], help="Run only the named lead id(s).")
    parser.add_argument("--limit", type=int, default=None, help="Run only the first N leads by priority.")
    parser.add_argument("--probe-only", action="store_true", help="Probe URLs and write queue status without downloading raw files.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    manifest = run(args.lead_id, args.limit, args.probe_only)
    print(f"Wrote manifest: {MANIFEST_PATH}")
    print(f"Wrote lead queue csv: {QUEUE_STATUS_CSV}")
    print(f"Wrote lead queue report: {QUEUE_STATUS_MD}")
    print(f"Processed leads: {len(manifest)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
