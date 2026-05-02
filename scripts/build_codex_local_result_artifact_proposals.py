#!/usr/bin/env python3
"""Materialize Codex-local result-artifact proposals from existing paths.

This handles the remaining non-GPT tail where the repo already has some local
mirror, staged CSV, workbook, archive, or paper artifact but the concrete
SOURCE_ARTIFACTS-shaped row was not yet emitted for mirror/sample/parser work.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import mimetypes
import re
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_TSV = ROOT / "SOURCE_ARTIFACTS.tsv"

SUPPORTED_EXTS = {
    ".csv",
    ".tab",
    ".tsv",
    ".txt",
    ".xlsx",
    ".xls",
    ".rds",
    ".rdata",
    ".dta",
    ".sav",
    ".zip",
    ".pdf",
    ".html",
    ".htm",
    ".json",
    ".r",
    ".rmd",
    ".py",
    ".do",
    ".md",
}
HIGH_SIGNAL = [
    "result",
    "results",
    "effect",
    "effects",
    "original",
    "replication",
    "repli",
    "pair",
    "pairs",
    "summary",
    "master",
    "combined",
    "stage",
    "table",
    "data",
    "dataset",
    "meta",
]
LOW_SIGNAL = [
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".ppt",
    ".pptx",
    ".doc",
    ".docx",
    ".qsf",
    ".rproj",
    ".log",
    ".tmp",
]


def clean(value: object, max_len: int = 12000) -> str:
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value).replace("\t", " ")).strip()[:max_len]


def repo_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def resolve_path(value: str | Path) -> Path:
    path = Path(clean(value))
    return path if path.is_absolute() else ROOT / path


def stable_id(prefix: str, *parts: object) -> str:
    text = "\n".join(clean(part, 100000) for part in parts if clean(part))
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]
    return f"{prefix}_{digest}"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_tsv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return [{key: clean(value) for key, value in row.items()} for row in csv.DictReader(handle, delimiter="\t")]


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


def source_artifact_columns() -> list[str]:
    return SCHEMA_TSV.read_text(encoding="utf-8").splitlines()[0].split("\t")


def file_type(path: Path) -> str:
    lower = path.name.lower()
    if lower.endswith(".csv.gz"):
        return "csv.gz"
    return path.suffix.lower().lstrip(".") or "unknown"


def parser_family(path: Path) -> str:
    ft = file_type(path)
    if ft in {"csv", "tab", "tsv", "txt", "csv.gz"}:
        return "csv_table_parser"
    if ft in {"xlsx", "xls"}:
        return "xlsx_workbook_parser"
    if ft in {"rds", "rdata"}:
        return "r_data_parser"
    if ft in {"dta", "sav"}:
        return "statistical_package_parser"
    if ft == "zip":
        return "zip_member_inventory"
    if ft in {"pdf", "html", "htm"}:
        return "document_context_or_source_object_review"
    if ft in {"json"}:
        return "json_metadata_inventory"
    if ft in {"r", "rmd", "py", "do", "md"}:
        return "analysis_code_inventory"
    return "unknown"


def artifact_role(path: Path) -> str:
    ft = file_type(path)
    lower = path.name.lower()
    if "codebook" in lower or "dictionary" in lower:
        return "codebook"
    if ft in {"csv", "tab", "tsv", "txt", "xlsx", "xls", "rds", "rdata", "dta", "sav", "json"}:
        return "data_file"
    if ft == "zip":
        return "archive_file"
    if ft in {"pdf", "html", "htm"}:
        return "article_or_supplement_pdf" if ft == "pdf" else "mirrored_website_result_catalog"
    if ft in {"r", "rmd", "py", "do", "md"}:
        return "code_file"
    return "context_file"


def field_evidence(path: Path) -> dict[str, str]:
    lower = path.name.lower()
    pairs = [term for term in ["original", "replication", "repli", "pair", "study"] if term in lower]
    ns = [term for term in ["sample", "_n", " n", "planned"] if term in lower]
    effects = [term for term in ["effect", "result", "estimate", "stat", "coef", "d_", "r_"] if term in lower]
    ids = [term for term in ["doi", "paper", "citation", "pmid", "nct"] if term in lower]
    return {
        "pair_field_evidence": "filename terms: " + " | ".join(pairs) if pairs else "",
        "n_field_evidence": "filename terms: " + " | ".join(ns) if ns else "",
        "effect_field_evidence": "filename terms: " + " | ".join(effects) if effects else "",
        "publication_link_evidence": "filename terms: " + " | ".join(ids) if ids else "",
    }


def file_score(path: Path) -> int:
    lower = path.name.lower()
    score = 0
    if path.suffix.lower() in {".csv", ".tab", ".tsv", ".xlsx", ".xls", ".rds", ".rdata", ".dta", ".sav"}:
        score += 50
    if path.suffix.lower() in {".pdf", ".zip", ".r", ".rmd", ".py", ".do"}:
        score += 20
    score += sum(8 for term in HIGH_SIGNAL if term in lower)
    score -= sum(25 for term in LOW_SIGNAL if lower.endswith(term) or term.strip(".") in lower)
    try:
        size = path.stat().st_size
        if size == 0:
            score -= 100
        if size > 150_000_000:
            score -= 50
    except OSError:
        score -= 100
    return score


def parse_existing_paths(text: str) -> list[Path]:
    paths = []
    seen = set()
    for part in re.split(r"\s*\|\s*", clean(text, 100000)):
        if not part:
            continue
        path = resolve_path(part)
        if path.exists() and path not in seen:
            seen.add(path)
            paths.append(path)
    return paths


def staged_referenced_paths(path: Path) -> list[Path]:
    if not path.is_file() or not path.name.endswith("__stage.csv"):
        return []
    rows = read_tsv(path) if path.suffix == ".tsv" else []
    if not rows:
        with path.open("r", encoding="utf-8", newline="") as handle:
            rows = [{key: clean(value) for key, value in row.items()} for row in csv.DictReader(handle)]
    out: list[Path] = []
    for row in rows:
        for field in ["local_raw_file", "manifest_file", "file_list_csv"]:
            value = row.get(field, "")
            if value:
                candidate = resolve_path(value)
                if candidate.exists():
                    out.append(candidate)
    return out


def candidate_files_for_path(path: Path, max_files_per_dir: int) -> list[Path]:
    if path.is_file():
        return [path] + staged_referenced_paths(path)
    if not path.is_dir():
        return []
    files = [item for item in path.rglob("*") if item.is_file() and item.suffix.lower() in SUPPORTED_EXTS]
    ranked = sorted(files, key=lambda item: (-file_score(item), str(item)))
    return ranked[:max_files_per_dir]


def artifact_row(columns: list[str], parent_id: str, path: Path, source_reason: str) -> dict[str, str]:
    stat = path.stat()
    rel = repo_path(path)
    evidence = field_evidence(path)
    row = {column: "" for column in columns}
    row.update(
        {
            "artifact_id": stable_id("source_artifact", parent_id, rel, stat.st_size, stat.st_mtime_ns),
            "parent_corpus_database_id": parent_id,
            "artifact_role": artifact_role(path),
            "provider": "local_file",
            "provider_id": rel,
            "parent_provider_id": parent_id,
            "title": path.name,
            "component_path": repo_path(path.parent),
            "file_name": path.name,
            "file_type": file_type(path),
            "mime_type": clean(mimetypes.guess_type(path.name)[0]),
            "byte_size": str(stat.st_size),
            "local_path": rel,
            "sha256": sha256_file(path),
            "inventory_status": "result_artifact_local_candidate",
            "access_status": "downloaded",
            "candidate_parser_family": parser_family(path),
            "pair_field_evidence": evidence["pair_field_evidence"],
            "n_field_evidence": evidence["n_field_evidence"],
            "effect_field_evidence": evidence["effect_field_evidence"],
            "publication_link_evidence": evidence["publication_link_evidence"],
            "blocker_codes": "",
            "next_action": "mirror_sample_and_route_parser_candidate",
            "notes": f"Codex-local artifact proposal; source_reason={source_reason}",
            "last_seen": datetime.now().date().isoformat(),
        }
    )
    return row


def build_rows(decisions: list[dict[str, str]], columns: list[str], max_files_per_dir: int) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    rows: list[dict[str, str]] = []
    audit: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for decision in decisions:
        parent_id = decision.get("corpus_database_id", "")
        if decision.get("decision") != "local_mirror_identification_still_needed":
            continue
        candidates: list[Path] = []
        for path in parse_existing_paths(decision.get("existing_local_paths", "")):
            candidates.extend(candidate_files_for_path(path, max_files_per_dir))
        candidates = sorted(set(candidates), key=lambda item: (-file_score(item), str(item)))
        for path in candidates:
            key = (parent_id, repo_path(path))
            if key in seen:
                continue
            seen.add(key)
            rows.append(artifact_row(columns, parent_id, path, "local_mirror_identification_still_needed"))
        audit.append(
            {
                "corpus_database_id": parent_id,
                "name": decision.get("name", ""),
                "existing_local_paths": decision.get("existing_local_paths", ""),
                "candidate_file_count": str(len(candidates)),
                "top_candidate_paths": " | ".join(repo_path(path) for path in candidates[:12]),
            }
        )
    return sorted(rows, key=lambda row: (row["parent_corpus_database_id"], row["file_name"], row["local_path"])), audit


def summary_rows(rows: list[dict[str, str]], audit: list[dict[str, str]]) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    for field in ["artifact_role", "candidate_parser_family", "file_type", "parent_corpus_database_id"]:
        for value, count in Counter(row.get(field, "") or "<blank>" for row in rows).most_common():
            out.append({"metric": field, "value": value, "count": str(count)})
    out.append({"metric": "total", "value": "artifact_rows", "count": str(len(rows))})
    out.append({"metric": "total", "value": "local_mirror_rows_audited", "count": str(len(audit))})
    out.append({"metric": "total", "value": "local_mirror_rows_with_candidates", "count": str(sum(1 for row in audit if row["candidate_file_count"] != "0"))})
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plot-label", default="figure1")
    parser.add_argument("--decisions", type=Path)
    parser.add_argument("--output-root", type=Path)
    parser.add_argument("--max-files-per-dir", type=int, default=25)
    parser.add_argument("--replace", action="store_true")
    args = parser.parse_args()

    root = ROOT / "steps" / "source_inventory" / args.plot_label / "result_artifact_acquisition" / "codex_local"
    decisions_path = resolve_path(args.decisions) if args.decisions else ROOT / "steps" / "source_inventory" / args.plot_label / "result_artifact_acquisition" / "followup" / "codex" / f"{args.plot_label}-result-artifact-codex-decisions.tsv"
    output_root = resolve_path(args.output_root) if args.output_root else root
    decisions = read_tsv(decisions_path)
    columns = source_artifact_columns()
    rows, audit = build_rows(decisions, columns, args.max_files_per_dir)
    prefix = f"{args.plot_label}-result-artifact-codex-local"
    write_tsv(output_root / f"{prefix}-source-artifacts-proposal.tsv", rows, columns, args.replace)
    write_tsv(output_root / f"{prefix}-source-artifacts-audit.tsv", audit, ["corpus_database_id", "name", "existing_local_paths", "candidate_file_count", "top_candidate_paths"], args.replace)
    write_tsv(output_root / f"{prefix}-source-artifacts-summary.tsv", summary_rows(rows, audit), ["metric", "value", "count"], args.replace)
    write_json(
        output_root / f"{prefix}-source-artifacts-proposal.json",
        {
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "decisions_input": repo_path(decisions_path),
            "artifact_count": len(rows),
            "audit": audit,
            "records": rows,
        },
        args.replace,
    )
    print(f"{args.plot_label} Codex-local artifact proposals: artifacts={len(rows)}; audited={len(audit)}")


if __name__ == "__main__":
    main()
