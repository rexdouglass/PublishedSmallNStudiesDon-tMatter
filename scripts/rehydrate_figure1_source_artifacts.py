#!/usr/bin/env python3
"""Repull Figure 1 source artifacts from the tracked rehydration manifest."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any

import requests


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_TSV = ROOT / "steps" / "source_inventory" / "figure1" / "rehydration" / "figure1-rehydration-manifest.tsv"
OUTPUT_ROOT = ROOT / "steps" / "source_inventory" / "figure1" / "rehydration"
RUN_STATUS_TSV = OUTPUT_ROOT / "figure1-rehydrate-run-status.tsv"
RUN_STATUS_JSON = OUTPUT_ROOT / "figure1-rehydrate-run-status.json"
DATAVERSE_GUESTBOOK_RESPONSE = {
    "guestbookResponse": {
        "name": "Codex automated source audit",
        "email": "noreply@example.com",
        "institution": "OpenAI",
        "position": "Research assistant",
        "answers": [
            {"id": 241, "value": "Non-academic researcher"},
            {"id": 243, "value": "Meta-analysis/systematic review"},
            {
                "id": 242,
                "value": "Auditing public source files for a D-vs-N evidence map.",
            },
            {"id": 240, "value": "No"},
        ],
    }
}


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


def write_tsv(path: Path, rows: list[dict[str, str]], columns: list[str], replace: bool = True) -> None:
    if path.exists() and not replace:
        print(f"Skipped {repo_path(path)} because it exists. Use --replace to rebuild.")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {repo_path(path)}")


def write_json(path: Path, payload: dict[str, Any], replace: bool = True) -> None:
    if path.exists() and not replace:
        print(f"Skipped {repo_path(path)} because it exists. Use --replace to rebuild.")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {repo_path(path)}")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def boolish(value: str) -> bool:
    return safe_text(value).lower() in {"true", "1", "yes", "y"}


def row_allowed(row: dict[str, str], args: argparse.Namespace) -> bool:
    if row.get("repull_supported") != "true":
        return False
    if args.parent and row.get("parent_corpus_database_id") not in set(args.parent):
        return False
    if args.artifact_id and row.get("artifact_id") not in set(args.artifact_id):
        return False
    if args.target and row.get("target_local_path") not in set(args.target):
        return False
    return True


def existing_status(path: Path, expected_sha: str) -> tuple[str, str, int]:
    if not path.exists():
        return "missing", "", 0
    if not path.is_file():
        return "target_exists_not_file", "", 0
    actual_sha = sha256_file(path)
    size = path.stat().st_size
    if expected_sha and actual_sha != expected_sha:
        return "existing_checksum_mismatch", actual_sha, size
    if expected_sha:
        return "existing_verified", actual_sha, size
    return "existing_no_expected_checksum", actual_sha, size


def write_access_record(row: dict[str, str], target: Path, response: requests.Response, sha: str, bytes_written: int, error: str = "") -> str:
    metadata_path_text = safe_text(row.get("metadata_local_path"))
    if not metadata_path_text:
        return ""
    metadata_path = resolve_path(metadata_path_text)
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "ok": not error,
        "url": row.get("url", ""),
        "final_url": safe_text(response.url, 40000) if response is not None else "",
        "status_code": str(response.status_code) if response is not None else "",
        "content_type": response.headers.get("content-type", "") if response is not None else "",
        "content_length": response.headers.get("content-length", "") if response is not None else "",
        "bytes_written": bytes_written,
        "sha256": sha,
        "saved_file": str(target),
        "error": error,
        "retrieved_at": datetime.now().isoformat(timespec="seconds"),
        "rehydration_id": row.get("rehydration_id", ""),
    }
    metadata_path.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False), encoding="utf-8")
    return repo_path(metadata_path)


def dataverse_signed_url(url: str, timeout: int) -> str:
    signed_endpoint = url + ("&" if "?" in url else "?") + "signed=true"
    response = requests.post(
        signed_endpoint,
        json=DATAVERSE_GUESTBOOK_RESPONSE,
        timeout=timeout,
        headers={"User-Agent": "figure1-rehydrate/0.1"},
    )
    response.raise_for_status()
    payload = response.json()
    signed_url = safe_text((payload.get("data") or {}).get("signedUrl"), 40000)
    if not signed_url:
        raise RuntimeError("Dataverse signed-url response did not include data.signedUrl")
    return signed_url


def open_download_response(url: str, args: argparse.Namespace) -> requests.Response:
    response = requests.get(url, stream=True, timeout=args.timeout, headers={"User-Agent": "figure1-rehydrate/0.1"})
    if (
        response.status_code == 400
        and "dataverse.harvard.edu/api/access/datafile/" in url
        and not url.endswith("signed=true")
    ):
        response.close()
        signed_url = dataverse_signed_url(url, args.timeout)
        response = requests.get(signed_url, stream=True, timeout=args.timeout, headers={"User-Agent": "figure1-rehydrate/0.1"})
    response.raise_for_status()
    return response


def download_row(row: dict[str, str], args: argparse.Namespace) -> dict[str, str]:
    target = resolve_path(row.get("target_local_path", ""))
    expected_sha = row.get("expected_sha256", "")
    status, actual_sha, actual_size = existing_status(target, expected_sha)
    if status != "missing" and not args.replace:
        return {
            **base_status(row),
            "download_status": status,
            "target_local_path": repo_path(target),
            "actual_sha256": actual_sha,
            "actual_byte_size": str(actual_size),
            "access_metadata_written": "",
            "error": "",
        }
    if args.dry_run:
        return {
            **base_status(row),
            "download_status": "dry_run_would_download" if status == "missing" or args.replace else f"dry_run_{status}",
            "target_local_path": repo_path(target),
            "actual_sha256": actual_sha,
            "actual_byte_size": str(actual_size),
            "access_metadata_written": "",
            "error": "",
        }
    target.parent.mkdir(parents=True, exist_ok=True)
    bytes_written = 0
    response: requests.Response | None = None
    tmp_path = Path(tempfile.mkstemp(prefix=target.name + ".", suffix=".tmp", dir=str(target.parent))[1])
    try:
        with open_download_response(row["url"], args) as response:
            with tmp_path.open("wb") as handle:
                for chunk in response.iter_content(chunk_size=1024 * 256):
                    if not chunk:
                        continue
                    bytes_written += len(chunk)
                    if bytes_written > args.max_bytes:
                        raise RuntimeError(f"download exceeded --max-bytes ({bytes_written} > {args.max_bytes})")
                    handle.write(chunk)
        actual_sha = sha256_file(tmp_path)
        actual_size = tmp_path.stat().st_size
        if expected_sha and actual_sha != expected_sha and not args.allow_checksum_mismatch:
            metadata_written = write_access_record(row, target, response, actual_sha, actual_size, "checksum_mismatch")
            tmp_path.unlink(missing_ok=True)
            return {
                **base_status(row),
                "download_status": "downloaded_checksum_mismatch_rejected",
                "target_local_path": repo_path(target),
                "actual_sha256": actual_sha,
                "actual_byte_size": str(actual_size),
                "access_metadata_written": metadata_written,
                "error": f"expected_sha256={expected_sha}",
            }
        os.replace(tmp_path, target)
        metadata_written = write_access_record(row, target, response, actual_sha, actual_size)
        return {
            **base_status(row),
            "download_status": "downloaded_verified" if expected_sha else "downloaded_no_expected_checksum",
            "target_local_path": repo_path(target),
            "actual_sha256": actual_sha,
            "actual_byte_size": str(actual_size),
            "access_metadata_written": metadata_written,
            "error": "" if not expected_sha or actual_sha == expected_sha else f"checksum_mismatch_allowed expected_sha256={expected_sha}",
        }
    except Exception as exc:  # noqa: BLE001 - acquisition failures are data.
        tmp_path.unlink(missing_ok=True)
        return {
            **base_status(row),
            "download_status": "download_failed",
            "target_local_path": repo_path(target),
            "actual_sha256": "",
            "actual_byte_size": str(bytes_written),
            "access_metadata_written": "",
            "error": safe_text(exc, 1000),
        }


def base_status(row: dict[str, str]) -> dict[str, str]:
    return {
        "rehydration_id": row.get("rehydration_id", ""),
        "parent_corpus_database_id": row.get("parent_corpus_database_id", ""),
        "artifact_id": row.get("artifact_id", ""),
        "provider": row.get("provider", ""),
        "url": row.get("url", ""),
        "expected_sha256": row.get("expected_sha256", ""),
        "expected_byte_size": row.get("expected_byte_size", ""),
        "route_kind": row.get("route_kind", ""),
    }


def summary_rows(status_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    for field in ["download_status", "parent_corpus_database_id", "provider"]:
        counts: dict[str, int] = {}
        for row in status_rows:
            counts[row.get(field, "")] = counts.get(row.get(field, ""), 0) + 1
        for value, count in sorted(counts.items()):
            out.append({"metric": field, "value": value, "count": str(count)})
    out.append({"metric": "total", "value": "rows", "count": str(len(status_rows))})
    return out


def main() -> None:
    global OUTPUT_ROOT, RUN_STATUS_TSV, RUN_STATUS_JSON
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", default=str(MANIFEST_TSV))
    parser.add_argument("--output-root", default=str(OUTPUT_ROOT))
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--replace", action="store_true")
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--parent", action="append", help="Restrict to a parent_corpus_database_id. Can be repeated.")
    parser.add_argument("--artifact-id", action="append", help="Restrict to an artifact_id. Can be repeated.")
    parser.add_argument("--target", action="append", help="Restrict to a repo-relative target_local_path. Can be repeated.")
    parser.add_argument("--timeout", type=int, default=60)
    parser.add_argument("--max-bytes", type=int, default=2 * 1024 * 1024 * 1024)
    parser.add_argument("--allow-checksum-mismatch", action="store_true")
    args = parser.parse_args()

    manifest_path = resolve_path(args.manifest)
    OUTPUT_ROOT = resolve_path(args.output_root)
    RUN_STATUS_TSV = OUTPUT_ROOT / "figure1-rehydrate-run-status.tsv"
    RUN_STATUS_JSON = OUTPUT_ROOT / "figure1-rehydrate-run-status.json"

    rows = [row for row in read_tsv(manifest_path) if row_allowed(row, args)]
    if args.limit:
        rows = rows[: args.limit]
    status_rows = [download_row(row, args) for row in rows]
    columns = [
        "rehydration_id",
        "parent_corpus_database_id",
        "artifact_id",
        "provider",
        "url",
        "expected_sha256",
        "expected_byte_size",
        "route_kind",
        "download_status",
        "target_local_path",
        "actual_sha256",
        "actual_byte_size",
        "access_metadata_written",
        "error",
    ]
    write_tsv(RUN_STATUS_TSV, status_rows, columns, replace=True)
    write_json(
        RUN_STATUS_JSON,
        {
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "manifest": repo_path(manifest_path),
            "dry_run": boolish(str(args.dry_run)),
            "replace": boolish(str(args.replace)),
            "row_count": len(status_rows),
            "records": status_rows,
            "summary": summary_rows(status_rows),
        },
        replace=True,
    )
    failures = sum(1 for row in status_rows if row["download_status"].endswith("failed") or "mismatch_rejected" in row["download_status"])
    print(f"Figure 1 rehydrate: rows={len(status_rows)}; failures={failures}; dry_run={args.dry_run}")


if __name__ == "__main__":
    main()
