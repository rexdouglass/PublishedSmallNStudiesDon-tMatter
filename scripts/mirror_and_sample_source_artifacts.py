#!/usr/bin/env python3
"""Mirror and sample reviewed Figure 1 source artifacts.

This is the reality-check stage between source-family inventory and parsing. It
attempts to mirror public, eligible artifacts into a controlled local cache and
writes compact sample summaries for local files. It does not mutate
SOURCE_ARTIFACTS.tsv.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import mimetypes
import os
import re
import subprocess
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
import requests
from bs4 import BeautifulSoup

try:
    import pyreadr
except ImportError:  # pragma: no cover - optional dependency is in requirements for this repo.
    pyreadr = None

try:
    import pdfplumber
except ImportError:  # pragma: no cover - optional dependency for document sampling.
    pdfplumber = None


ROOT = Path(__file__).resolve().parents[1]
PROPOSAL_TSV = ROOT / "steps" / "source_inventory" / "figure1" / "source-artifacts-proposal.tsv"
OUTPUT_ROOT = ROOT / "steps" / "source_inventory" / "figure1" / "mirror_sample"
SAMPLE_ROOT = OUTPUT_ROOT / "artifact_samples"
MIRROR_ROOT = ROOT / "data" / "raw" / "source_artifacts" / "figure1"
STATUS_TSV = OUTPUT_ROOT / "source-artifact-mirror-sample-status.tsv"
STATUS_JSON = OUTPUT_ROOT / "source-artifact-mirror-sample-status.json"
AUGMENTED_TSV = OUTPUT_ROOT / "source-artifacts-mirrored-sampled-proposal.tsv"
SUMMARY_TSV = OUTPUT_ROOT / "source-artifact-mirror-sample-summary.tsv"

DOWNLOADABLE_ROLES = {
    "archive_file",
    "code_file",
    "codebook",
    "context_file",
    "data_file",
    "provider_file",
}
DOWNLOADABLE_TYPES = {
    "csv",
    "csv.gz",
    "dta",
    "do",
    "html",
    "htm",
    "json",
    "md",
    "pdf",
    "py",
    "r",
    "rd",
    "rdata",
    "rds",
    "rmd",
    "sample",
    "sav",
    "sps",
    "tab",
    "tsv",
    "txt",
    "xls",
    "xlsx",
    "zip",
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


def slugify(value: object, fallback: str = "item") -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", safe_text(value).lower()).strip("_")
    return slug[:120] or fallback


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return [{key: safe_text(value) for key, value in row.items()} for row in csv.DictReader(handle, delimiter="\t")]


def write_tsv(path: Path, rows: list[dict[str, str]], fieldnames: list[str], replace: bool) -> None:
    if path.exists() and not replace:
        print(f"Skipped {repo_path(path)} because it exists. Use --replace to rebuild.")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter="\t", lineterminator="\n")
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


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def file_type(path_or_name: object) -> str:
    name = safe_text(path_or_name).lower()
    if name.endswith(".csv.gz"):
        return "csv.gz"
    suffix = Path(name).suffix.lower().lstrip(".")
    return suffix or "unknown"


def sample_id(artifact_id: str) -> str:
    return slugify(artifact_id, "artifact")[:180]


def mirror_path_for(row: dict[str, str]) -> Path:
    parent = slugify(row.get("parent_corpus_database_id"), "source_family")
    artifact_id = slugify(row.get("artifact_id"), "artifact")
    component_name = Path(safe_text(row.get("component_path"))).name
    file_name = safe_text(row.get("file_name") or row.get("title") or component_name or artifact_id)
    file_name = re.sub(r"[^A-Za-z0-9._-]+", "_", file_name).strip("._") or artifact_id
    return MIRROR_ROOT / parent / f"{artifact_id}__{file_name}"


def component_metadata_path_for(row: dict[str, str]) -> Path:
    parent = slugify(row.get("parent_corpus_database_id"), "source_family")
    artifact_id = slugify(row.get("artifact_id"), "artifact")
    title = slugify(row.get("title") or row.get("file_name") or row.get("component_path") or artifact_id, "component")
    return MIRROR_ROOT / parent / f"{artifact_id}__component_metadata__{title}.json"


def known_local_path(row: dict[str, str]) -> Path | None:
    local = safe_text(row.get("local_path"))
    if not local:
        return None
    path = resolve_path(local)
    return path if path.exists() and path.is_file() else None


def should_download(row: dict[str, str]) -> tuple[bool, str]:
    if known_local_path(row):
        return False, "already_local"
    if not safe_text(row.get("raw_url")):
        return False, "no_raw_url"
    if row.get("artifact_role") not in DOWNLOADABLE_ROLES:
        return False, "metadata_or_component_role"
    ft = safe_text(row.get("file_type")) or file_type(row.get("file_name") or row.get("title") or row.get("component_path"))
    if ft not in DOWNLOADABLE_TYPES:
        if ft == "unknown" and row.get("artifact_role") == "provider_file":
            return True, "eligible_unknown_type"
        return False, f"unsupported_file_type:{ft or 'unknown'}"
    if safe_text(row.get("access_status")) not in {"public_download_seen", "mirrorable", "downloaded"}:
        return False, f"not_public_download:{row.get('access_status')}"
    return True, "eligible"


def materialize_component_metadata(row: dict[str, str], replace: bool) -> tuple[str, Path | None, str, int]:
    if known_local_path(row):
        local = known_local_path(row)
        return "already_local", local, sha256_file(local), local.stat().st_size if local else 0
    if row.get("artifact_role") != "repository_component":
        return "not_component", None, "", 0
    out_path = component_metadata_path_for(row)
    if out_path.exists() and not replace:
        return "component_metadata_recorded", out_path, sha256_file(out_path), out_path.stat().st_size
    out_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "recorded_at": datetime.now().isoformat(timespec="seconds"),
        "record_type": "repository_component_metadata",
        "note": "Component/container row has no direct source bytes. Child files should be represented by separate source artifact rows.",
        "artifact": row,
    }
    out_path.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False), encoding="utf-8")
    return "component_metadata_recorded", out_path, sha256_file(out_path), out_path.stat().st_size


def content_length(row: dict[str, str], timeout: int) -> int | None:
    if safe_text(row.get("byte_size")).isdigit():
        return int(row["byte_size"])
    url = row.get("raw_url")
    if not url:
        return None
    try:
        response = requests.head(url, allow_redirects=True, timeout=timeout, headers={"User-Agent": "figure1-artifact-mirror/0.1"})
        if response.ok and response.headers.get("content-length", "").isdigit():
            return int(response.headers["content-length"])
    except requests.RequestException:
        return None
    return None


def download(row: dict[str, str], max_bytes: int, timeout: int, replace: bool) -> tuple[str, Path | None, str, int]:
    ok, reason = should_download(row)
    if not ok:
        return reason, None, "", 0
    length = content_length(row, timeout)
    if length is not None and length > max_bytes:
        return f"skipped_large:{length}", None, "", length
    out_path = mirror_path_for(row)
    if out_path.exists() and not replace:
        return "already_mirrored_cache", out_path, sha256_file(out_path), out_path.stat().st_size
    out_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = out_path.with_suffix(out_path.suffix + ".tmp")
    bytes_written = 0
    try:
        with requests.get(row["raw_url"], stream=True, timeout=timeout, headers={"User-Agent": "figure1-artifact-mirror/0.1"}) as response:
            response.raise_for_status()
            with tmp_path.open("wb") as handle:
                for chunk in response.iter_content(chunk_size=1024 * 256):
                    if not chunk:
                        continue
                    bytes_written += len(chunk)
                    if bytes_written > max_bytes:
                        handle.close()
                        tmp_path.unlink(missing_ok=True)
                        return f"skipped_large_stream:{bytes_written}", None, "", bytes_written
                    handle.write(chunk)
        os.replace(tmp_path, out_path)
    except requests.RequestException as exc:
        tmp_path.unlink(missing_ok=True)
        return f"download_failed:{safe_text(exc, 500)}", None, "", bytes_written
    return "downloaded", out_path, sha256_file(out_path), out_path.stat().st_size


def sample_csv(path: Path, ft: str, max_rows: int) -> dict[str, Any]:
    sep = "\t" if ft in {"tsv", "tab"} else ","
    opener = gzip.open if ft == "csv.gz" else open
    line_count: int | None = None
    if path.stat().st_size < 100 * 1024 * 1024:
        try:
            with opener(path, "rt", encoding="utf-8", errors="replace", newline="") as handle:
                line_count = sum(1 for _ in handle)
        except OSError:
            line_count = None
    df = pd.read_csv(path, sep=sep, nrows=max_rows, compression="gzip" if ft == "csv.gz" else None, low_memory=False)
    return {
        "sample_kind": "delimited_table",
        "columns": [safe_text(col, 300) for col in df.columns],
        "sample_row_count": len(df),
        "estimated_data_rows": max(line_count - 1, 0) if line_count is not None else None,
        "preview_rows": json.loads(df.astype(object).where(pd.notna(df), None).to_json(orient="records")),
    }


def sample_excel(path: Path, max_rows: int) -> dict[str, Any]:
    xls = pd.ExcelFile(path)
    sheets = []
    for sheet in xls.sheet_names[:10]:
        df = pd.read_excel(xls, sheet_name=sheet, nrows=max_rows)
        sheets.append(
            {
                "sheet_name": sheet,
                "columns": [safe_text(col, 300) for col in df.columns],
                "sample_row_count": len(df),
                "preview_rows": json.loads(df.astype(object).where(pd.notna(df), None).to_json(orient="records")),
            }
        )
    return {"sample_kind": "excel_workbook", "sheet_count": len(xls.sheet_names), "sheets": sheets}


def sample_json(path: Path, max_rows: int) -> dict[str, Any]:
    if path.stat().st_size > 50 * 1024 * 1024:
        return {"sample_kind": "json", "sample_status": "skipped_large_json", "byte_size": path.stat().st_size}
    payload = json.loads(path.read_text(encoding="utf-8", errors="replace"))
    if isinstance(payload, dict):
        preview = {key: payload[key] for key in list(payload)[:20]}
        return {"sample_kind": "json_object", "keys": list(payload)[:100], "preview": preview}
    if isinstance(payload, list):
        return {"sample_kind": "json_list", "length": len(payload), "preview_items": payload[:max_rows]}
    return {"sample_kind": "json_scalar", "value": payload}


def sample_zip(path: Path) -> dict[str, Any]:
    with path.open("rb") as handle:
        magic = handle.read(8)
    if not magic.startswith(b"PK"):
        return {
            "sample_kind": "metadata_only",
            "sample_note": "zip_extension_but_file_magic_is_not_zip",
            "magic_hex": magic.hex(),
        }
    with zipfile.ZipFile(path) as zf:
        infos = zf.infolist()
        members = [
            {
                "filename": info.filename,
                "file_size": info.file_size,
                "compress_size": info.compress_size,
                "file_type": file_type(info.filename),
            }
            for info in infos[:500]
        ]
    return {
        "sample_kind": "zip_inventory",
        "member_count": len(infos),
        "members_preview": members,
    }


def sample_r_data(path: Path) -> dict[str, Any]:
    result: dict[str, Any]
    if pyreadr is None:
        result = {}
    else:
        try:
            result = pyreadr.read_r(str(path))
        except Exception:
            result = {}
    if not result:
        rscript_result = sample_r_data_with_rscript(path)
        if rscript_result:
            return rscript_result
    objects = []
    for name, obj in result.items():
        entry: dict[str, Any] = {"name": name or "value", "python_type": type(obj).__name__}
        if hasattr(obj, "shape"):
            entry["shape"] = list(obj.shape)
        if hasattr(obj, "columns"):
            entry["columns"] = [safe_text(col, 300) for col in list(obj.columns)[:200]]
            preview = obj.head(5).astype(object).where(pd.notna(obj.head(5)), None)
            entry["preview_rows"] = json.loads(preview.to_json(orient="records"))
        objects.append(entry)
    return {"sample_kind": "r_data", "object_count": len(objects), "objects": objects}


def sample_r_data_with_rscript(path: Path) -> dict[str, Any] | None:
    script = r"""
args <- commandArgs(trailingOnly = TRUE)
path <- args[[1]]
out <- args[[2]]
obj <- tryCatch(readRDS(path), error = function(e) NULL)
if (is.null(obj)) {
  env <- new.env(parent = emptyenv())
  loaded <- tryCatch(load(path, envir = env), error = function(e) character())
  if (length(loaded) > 0) {
    obj <- as.list(env)
  }
}
summarize_one <- function(name, x) {
  out <- list(name = name, r_class = paste(class(x), collapse = "|"))
  if (!is.null(dim(x))) out$shape <- as.integer(dim(x))
  if (is.data.frame(x)) {
    out$columns <- names(x)
    out$preview_rows <- utils::head(x, 5)
  } else if (is.list(x) && length(x) > 0 && !is.data.frame(x)) {
    out$list_names <- names(x)[seq_len(min(length(x), 100))]
  } else if (is.atomic(x)) {
    out$length <- length(x)
    out$preview_values <- utils::head(x, 20)
  }
  out
}
if (is.null(obj)) {
  payload <- list(sample_kind = "r_data", sample_status = "rscript_read_failed")
} else if (is.list(obj) && !is.data.frame(obj) && length(obj) > 0 && !is.null(names(obj))) {
  payload <- list(sample_kind = "r_data", reader = "Rscript", object_count = length(obj), objects = Map(summarize_one, names(obj), obj))
} else {
  payload <- list(sample_kind = "r_data", reader = "Rscript", object_count = 1, objects = list(summarize_one("value", obj)))
}
jsonlite::write_json(payload, out, auto_unbox = TRUE, na = "null", dataframe = "rows")
"""
    if not shutil_which("Rscript"):
        return None
    with tempfile.TemporaryDirectory() as tmpdir:
        script_path = Path(tmpdir) / "sample_r_data.R"
        out_path = Path(tmpdir) / "sample.json"
        script_path.write_text(script, encoding="utf-8")
        try:
            subprocess.run(["Rscript", str(script_path), str(path), str(out_path)], check=True, timeout=60, capture_output=True, text=True)
            return json.loads(out_path.read_text(encoding="utf-8"))
        except (subprocess.SubprocessError, json.JSONDecodeError, OSError):
            return None


def shutil_which(name: str) -> str | None:
    for directory in os.environ.get("PATH", "").split(os.pathsep):
        candidate = Path(directory) / name
        if candidate.exists() and os.access(candidate, os.X_OK):
            return str(candidate)
    return None


def sample_stata(path: Path, max_rows: int) -> dict[str, Any]:
    errors: list[str] = []
    try:
        reader = pd.read_stata(path, iterator=True)
        df = reader.read(max_rows)
    except Exception as exc:
        errors.append(f"default_read={safe_text(exc, 500)}")
        try:
            reader = pd.read_stata(path, iterator=True, convert_dates=False)
            df = reader.read(max_rows)
        except Exception as second_exc:
            errors.append(f"convert_dates_false={safe_text(second_exc, 500)}")
            return {
                "sample_kind": "metadata_only",
                "sample_note": "stata_parse_failed_but_file_is_local",
                "parse_errors": errors,
            }
    return {
        "sample_kind": "stata",
        "columns": [safe_text(col, 300) for col in df.columns],
        "sample_row_count": len(df),
        "preview_rows": json.loads(df.astype(str).where(pd.notna(df), None).to_json(orient="records")),
    }


def sample_text(path: Path, max_lines: int = 80) -> dict[str, Any]:
    lines: list[str] = []
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for _, line in zip(range(max_lines), handle):
            lines.append(line.rstrip("\n")[:1000])
    return {"sample_kind": "text", "line_preview": lines, "line_preview_count": len(lines)}


def sample_html(path: Path, max_lines: int = 80) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8", errors="replace")
    soup = BeautifulSoup(text, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    links = []
    for link in soup.find_all("a", href=True):
        label = safe_text(link.get_text(" ", strip=True), 300)
        href = safe_text(link.get("href"), 1000)
        if href:
            links.append({"text": label, "href": href})
    body_lines = [line for line in (safe_text(part, 1000) for part in soup.get_text("\n").splitlines()) if line]
    return {
        "sample_kind": "html_text",
        "line_preview": body_lines[:max_lines],
        "line_preview_count": min(len(body_lines), max_lines),
        "link_count": len(links),
        "links_preview": links[:200],
    }


def sample_pdf(path: Path, max_pages: int = 6) -> dict[str, Any]:
    if pdfplumber is None:
        return {"sample_kind": "metadata_only", "sample_note": "pdfplumber_unavailable"}
    pages = []
    with pdfplumber.open(path) as pdf:
        for idx, page in enumerate(pdf.pages[:max_pages], start=1):
            text = safe_text(page.extract_text() or "", 10000)
            pages.append({"page_number": idx, "text_preview": text[:5000]})
        return {
            "sample_kind": "pdf_text",
            "page_count": len(pdf.pages),
            "sampled_page_count": len(pages),
            "pages_preview": pages,
        }


def sample_file(path: Path, row: dict[str, str], max_rows: int) -> tuple[str, dict[str, Any]]:
    ft = safe_text(row.get("file_type")) or file_type(row.get("file_name") or row.get("title") or row.get("component_path")) or file_type(path)
    if ft == "unknown":
        ft = file_type(path)
    base: dict[str, Any] = {
        "artifact_id": row.get("artifact_id"),
        "parent_corpus_database_id": row.get("parent_corpus_database_id"),
        "file_name": row.get("file_name") or path.name,
        "local_path": repo_path(path),
        "file_type": ft,
        "byte_size": path.stat().st_size,
        "sha256": sha256_file(path),
        "sampled_at": datetime.now().isoformat(timespec="seconds"),
    }
    try:
        if ft in {"csv", "tsv", "tab", "csv.gz"}:
            base.update(sample_csv(path, ft, max_rows))
        elif ft in {"xlsx", "xls"}:
            base.update(sample_excel(path, max_rows))
        elif ft == "json":
            try:
                base.update(sample_json(path, max_rows))
            except json.JSONDecodeError:
                text_payload = sample_text(path)
                text_payload["sample_kind"] = "text"
                text_payload["sample_note"] = "json_extension_but_json_parse_failed"
                base.update(text_payload)
        elif ft == "zip":
            base.update(sample_zip(path))
        elif ft in {"rds", "rdata"}:
            base.update(sample_r_data(path))
        elif ft == "dta":
            base.update(sample_stata(path, max_rows))
        elif ft == "pdf":
            base.update(sample_pdf(path))
        elif ft in {"html", "htm"}:
            base.update(sample_html(path))
        elif ft in {"r", "rmd", "py", "do", "sps", "txt", "md", "rd", "tex", "sample"}:
            base.update(sample_text(path))
        else:
            base.update({"sample_kind": "metadata_only", "sample_note": f"no sampler for file_type={ft}"})
    except Exception as exc:  # noqa: BLE001 - sample failures are recorded as data.
        base.update({"sample_kind": "sample_failed", "sample_error": safe_text(exc, 1000)})
        return "sample_failed", base
    status = "sampled" if base.get("sample_kind") not in {"metadata_only", "sample_failed"} else safe_text(base.get("sample_kind"))
    return status, base


def process_row(row: dict[str, str], args: argparse.Namespace) -> tuple[dict[str, str], dict[str, str]]:
    local = known_local_path(row)
    mirror_status = "already_local" if local else ""
    mirror_sha = safe_text(row.get("sha256"))
    mirror_bytes = safe_text(row.get("byte_size"))
    if local is None:
        if row.get("artifact_role") == "repository_component" and not safe_text(row.get("raw_url")):
            mirror_status, local, mirror_sha, bytes_written = materialize_component_metadata(row, args.replace)
        else:
            mirror_status, local, mirror_sha, bytes_written = download(row, args.max_bytes, args.timeout, args.replace)
        mirror_bytes = str(bytes_written) if bytes_written else mirror_bytes
    sample_status = "not_sampled"
    sample_path = ""
    sample_payload: dict[str, Any] = {}
    if local and local.exists() and local.is_file():
        sample_status, sample_payload = sample_file(local, row, args.sample_rows)
        sample_out = SAMPLE_ROOT / f"{sample_id(row.get('artifact_id', 'artifact'))}.json"
        write_json(sample_out, sample_payload, args.replace)
        sample_path = repo_path(sample_out)
        mirror_sha = sample_payload.get("sha256") or mirror_sha
        mirror_bytes = str(sample_payload.get("byte_size") or mirror_bytes)
    status = {
        "artifact_id": row.get("artifact_id", ""),
        "parent_corpus_database_id": row.get("parent_corpus_database_id", ""),
        "artifact_role": row.get("artifact_role", ""),
        "candidate_parser_family": row.get("candidate_parser_family", ""),
        "file_type": row.get("file_type", ""),
        "file_name": row.get("file_name", ""),
        "raw_url": row.get("raw_url", ""),
        "source_local_path": row.get("local_path", ""),
        "mirror_status": mirror_status,
        "mirror_local_path": repo_path(local) if local else "",
        "mirror_sha256": mirror_sha,
        "mirror_byte_size": mirror_bytes,
        "sample_status": sample_status,
        "sample_path": sample_path,
        "sample_kind": safe_text(sample_payload.get("sample_kind")),
        "sample_error": safe_text(sample_payload.get("sample_error")),
    }
    augmented = dict(row)
    if local:
        augmented["local_path"] = repo_path(local)
    augmented["sha256"] = mirror_sha or row.get("sha256", "")
    augmented["byte_size"] = mirror_bytes or row.get("byte_size", "")
    augmented["inventory_status"] = "mirrored" if local and row.get("artifact_role") != "source_access_metadata" else row.get("inventory_status", "")
    augmented["access_status"] = "downloaded" if local else row.get("access_status", "")
    for extra in ["mirror_status", "sample_status", "sample_path", "sample_kind", "sample_error"]:
        augmented[extra] = status[extra]
    return status, augmented


def summary_rows(status_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    def count_by(field: str) -> dict[str, int]:
        out: dict[str, int] = {}
        for row in status_rows:
            key = row.get(field, "")
            out[key] = out.get(key, 0) + 1
        return dict(sorted(out.items()))

    rows: list[dict[str, str]] = []
    for field in ["parent_corpus_database_id", "mirror_status", "sample_status", "sample_kind", "candidate_parser_family"]:
        for value, count in count_by(field).items():
            rows.append({"metric": field, "value": value, "artifact_count": str(count)})
    rows.append({"metric": "total", "value": "artifacts", "artifact_count": str(len(status_rows))})
    rows.append({"metric": "total", "value": "mirrored_or_local", "artifact_count": str(sum(1 for row in status_rows if row.get("mirror_local_path")))})
    rows.append({"metric": "total", "value": "sampled", "artifact_count": str(sum(1 for row in status_rows if row.get("sample_status") == "sampled"))})
    return rows


def main() -> None:
    global OUTPUT_ROOT, SAMPLE_ROOT, MIRROR_ROOT, STATUS_TSV, STATUS_JSON, AUGMENTED_TSV, SUMMARY_TSV
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--proposal", default=str(PROPOSAL_TSV))
    parser.add_argument("--output-root", default=str(OUTPUT_ROOT))
    parser.add_argument("--mirror-root", default=str(MIRROR_ROOT))
    parser.add_argument("--replace", action="store_true")
    parser.add_argument("--max-bytes", type=int, default=50 * 1024 * 1024)
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("--sample-rows", type=int, default=5)
    args = parser.parse_args()

    OUTPUT_ROOT = resolve_path(args.output_root)
    SAMPLE_ROOT = OUTPUT_ROOT / "artifact_samples"
    MIRROR_ROOT = resolve_path(args.mirror_root)
    STATUS_TSV = OUTPUT_ROOT / "source-artifact-mirror-sample-status.tsv"
    STATUS_JSON = OUTPUT_ROOT / "source-artifact-mirror-sample-status.json"
    AUGMENTED_TSV = OUTPUT_ROOT / "source-artifacts-mirrored-sampled-proposal.tsv"
    SUMMARY_TSV = OUTPUT_ROOT / "source-artifact-mirror-sample-summary.tsv"

    proposal_path = resolve_path(args.proposal)
    rows = read_tsv(proposal_path)
    status_rows: list[dict[str, str]] = []
    augmented_rows: list[dict[str, str]] = []
    for row in rows:
        status, augmented = process_row(row, args)
        status_rows.append(status)
        augmented_rows.append(augmented)

    status_columns = [
        "artifact_id",
        "parent_corpus_database_id",
        "artifact_role",
        "candidate_parser_family",
        "file_type",
        "file_name",
        "raw_url",
        "source_local_path",
        "mirror_status",
        "mirror_local_path",
        "mirror_sha256",
        "mirror_byte_size",
        "sample_status",
        "sample_path",
        "sample_kind",
        "sample_error",
    ]
    augmented_columns = list(rows[0].keys()) + ["mirror_status", "sample_status", "sample_path", "sample_kind", "sample_error"] if rows else []
    write_tsv(STATUS_TSV, status_rows, status_columns, args.replace)
    write_json(
        STATUS_JSON,
        {
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "proposal": repo_path(proposal_path),
            "artifact_count": len(status_rows),
            "sample_dir": repo_path(SAMPLE_ROOT),
            "mirror_root": repo_path(MIRROR_ROOT),
            "records": status_rows,
        },
        args.replace,
    )
    write_tsv(AUGMENTED_TSV, augmented_rows, augmented_columns, args.replace)
    write_tsv(SUMMARY_TSV, summary_rows(status_rows), ["metric", "value", "artifact_count"], args.replace)
    downloaded = sum(1 for row in status_rows if row["mirror_status"] == "downloaded")
    sampled = sum(1 for row in status_rows if row["sample_status"] == "sampled")
    local = sum(1 for row in status_rows if row["mirror_local_path"])
    print(f"Mirror/sample artifacts: artifacts={len(status_rows)}; local_or_mirrored={local}; downloaded={downloaded}; sampled={sampled}")


if __name__ == "__main__":
    main()
