#!/usr/bin/env python3
"""Extract corpus-native result rows from parser-ready Figure 1 artifacts.

This emits CORPUS_RESULTS.tsv-shaped proposal rows. It deliberately does not
standardize effects, choose plotted Ns, collapse original/replication pairs, or
promote rows into source_result.tsv. Its job is to preserve each corpus/table
row as a durable assertion that downstream mappers can chase back to original
papers or studies.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import re
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

try:
    import pyreadr
except ImportError:  # pragma: no cover - optional dependency.
    pyreadr = None


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_YML = ROOT / "CORPUS_RESULTS_SCHEMA.yml"
PARSER_QUEUE_TSV = ROOT / "steps" / "source_inventory" / "figure1" / "parser_queue" / "source-artifact-parser-candidate-queue.tsv"
MIRROR_STATUS_TSV = ROOT / "steps" / "source_inventory" / "figure1" / "mirror_sample" / "source-artifact-mirror-sample-status.tsv"
OUTPUT_ROOT = ROOT / "steps" / "corpus_results" / "figure1"
PROPOSAL_TSV = OUTPUT_ROOT / "corpus-results-proposal.tsv"
PROPOSAL_JSON = OUTPUT_ROOT / "corpus-results-proposal.json"
TABLES_TSV = OUTPUT_ROOT / "corpus-result-tables-proposal.tsv"
SUMMARY_TSV = OUTPUT_ROOT / "corpus-results-summary.tsv"

PARSER_VERSION = "corpus_result_native_row_v1"

KEY_PATTERNS = [
    r"^id$",
    r"paper.?id",
    r"study.?id",
    r"unique.?claim.?id",
    r"claim.?id",
    r"rr.?id",
    r"experiment.?#",
    r"effect.?#",
    r"unique.?id",
]
ORIGINAL_SOURCE_PATTERNS = [
    r"original.*title",
    r"original.*paper",
    r"original.*journal",
    r"orig.*title",
    r"orig.*paper",
    r"source.*paper",
]
ORIGINAL_ID_PATTERNS = [
    r"original.*doi",
    r"orig.*doi",
    r"doi.*orig",
    r"original.*url",
    r"original.*link",
    r"original.*id",
]
REPLICATION_SOURCE_PATTERNS = [
    r"replication.*title",
    r"replication.*paper",
    r"replication.*journal",
    r"repli.*paper",
    r"rr.*pdf",
    r"rr.*type",
    r"replication.*study",
]
REPLICATION_ID_PATTERNS = [
    r"replication.*doi",
    r"repli.*doi",
    r"rr.?id",
    r"report.?id",
    r"replication.*url",
    r"replication.*link",
]
RESULT_LABEL_PATTERNS = [
    r"paper.?#",
    r"experiment.?#",
    r"effect.?#",
    r"study.?name",
    r"study.?analysis",
    r"study.?id",
    r"claim.?id",
    r"unique.?claim.?id",
    r"effect.*description",
]
OUTCOME_PATTERNS = [
    r"outcome",
    r"claim",
    r"hyp",
    r"figure",
    r"effect.*description",
    r"dependent",
    r"measure",
]
EFFECT_PATTERNS = [
    r"effect",
    r"estimate",
    r"statistic",
    r"cohen",
    r"hedges",
    r"\bd\b",
    r"\bg\b",
    r"\br\b",
    r"odds",
    r"beta",
    r"coef",
    r"raw difference",
    r"observed difference",
]
N_PATTERNS = [
    r"\bn\b",
    r"sample",
    r"analytic.*sample",
    r"original.*sample",
    r"replication.*sample",
    r"participants",
    r"subjects",
]
P_PATTERNS = [r"p.?value", r"\bp\b", r"significance", r"statistical.*significance"]
CI_PATTERNS = [r"ci", r"confidence"]
SE_PATTERNS = [r"se$", r"std.?error", r"standard.?error"]
CONTEXT_PATTERNS = [
    r"year",
    r"journal",
    r"title",
    r"doi",
    r"url",
    r"link",
    r"expected",
    r"observed",
    r"replication",
    r"original",
]


def safe_text(value: object, max_len: int = 30000) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and pd.isna(value):
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


def stable_id(prefix: str, *parts: object) -> str:
    text = "\n".join(safe_text(part, 100000) for part in parts if safe_text(part))
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]
    return f"{prefix}_{digest}"


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


def schema_columns() -> list[str]:
    payload = yaml.safe_load(SCHEMA_YML.read_text(encoding="utf-8"))
    return [item["name"] for item in payload["CORPUS_RESULTS_SCHEMA"]["columns"]]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_table(path: Path, file_name: str, max_rows: int | None) -> pd.DataFrame:
    lower = file_name.lower()
    if lower.endswith(".csv.gz"):
        return pd.read_csv(path, dtype=str, keep_default_na=False, nrows=max_rows, compression="gzip", low_memory=False)
    if lower.endswith((".tsv", ".tab")):
        return pd.read_csv(path, sep="\t", dtype=str, keep_default_na=False, nrows=max_rows, low_memory=False)
    if lower.endswith((".xlsx", ".xls")):
        return pd.read_excel(path, dtype=str, keep_default_na=False, nrows=max_rows)
    if lower.endswith((".rds", ".rdata")):
        if pyreadr is None:
            raise RuntimeError("pyreadr is required to parse RDS/RData files")
        parsed = pyreadr.read_r(str(path))
        frames = [value for value in parsed.values() if isinstance(value, pd.DataFrame)]
        if not frames:
            raise ValueError(f"No data frame object found in {path}")
        frame = frames[0].astype(str)
        return frame.head(max_rows) if max_rows else frame
    return pd.read_csv(path, dtype=str, keep_default_na=False, nrows=max_rows, low_memory=False)


def table_content_fingerprint(path: Path, file_name: str) -> str:
    df = read_table(path, file_name, max_rows=None)
    columns = [safe_text(col, 1000) for col in df.columns]
    records = [
        {safe_text(key, 1000): safe_text(value) for key, value in record.items()}
        for record in df.astype(str).to_dict(orient="records")
    ]
    payload = json.dumps({"columns": columns, "records": records}, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def matching_fields(row: dict[str, str], patterns: list[str]) -> dict[str, str]:
    out: dict[str, str] = {}
    for key, value in row.items():
        key_text = safe_text(key, 1000)
        if any(re.search(pattern, key_text, flags=re.IGNORECASE) for pattern in patterns):
            text = safe_text(value)
            if text:
                out[key_text] = text
    return out


def fields_text(fields: dict[str, str]) -> str:
    return " | ".join(f"{key}={value}" for key, value in fields.items())


def native_row_text(row: dict[str, str]) -> str:
    return " | ".join(f"{safe_text(key, 1000)}={safe_text(value, 2000)}" for key, value in row.items() if safe_text(value))


def row_key(row: dict[str, str], row_number: int) -> str:
    parts: list[str] = []
    for patterns in [KEY_PATTERNS, RESULT_LABEL_PATTERNS]:
        fields = matching_fields(row, patterns)
        for key, value in fields.items():
            parts.append(f"{key}={value}")
    return " | ".join(parts[:8]) or f"row_{row_number}"


def load_candidates(
    scope: set[str],
    parser_queue_tsv: Path,
    mirror_status_tsv: Path,
    min_priority: str,
) -> tuple[list[dict[str, str]], dict[str, dict[str, str]]]:
    ranks = {"low": 0, "medium": 1, "high": 2}
    min_rank = ranks.get(min_priority, 0)
    queue = [
        row
        for row in read_tsv(parser_queue_tsv)
        if row.get("recommended_next_stage") in scope
        and ranks.get(row.get("parser_priority", "low"), 0) >= min_rank
    ]
    status = {row["artifact_id"]: row for row in read_tsv(mirror_status_tsv)}
    return queue, status


def group_candidates(queue: list[dict[str, str]], status: dict[str, dict[str, str]]) -> list[dict[str, Any]]:
    grouped: dict[str, dict[str, Any]] = {}
    for row in queue:
        artifact_id = row["artifact_id"]
        status_row = status.get(artifact_id, {})
        path_text = row.get("mirror_local_path") or status_row.get("mirror_local_path")
        if not path_text:
            continue
        path = resolve_path(path_text)
        if not path.exists():
            continue
        sha = status_row.get("mirror_sha256") or sha256_file(path)
        file_name = row.get("file_name") or path.name
        try:
            group_key = f"table::{table_content_fingerprint(path, file_name)}"
        except Exception:
            group_key = f"bytes::{sha}"
        grouped.setdefault(
            group_key,
            {
                "table_fingerprint": group_key,
                "primary_sha256": sha,
                "sha256s": set(),
                "path": path,
                "rows": [],
                "parent_ids": set(),
                "artifact_ids": set(),
                "file_names": set(),
                "sample_paths": set(),
                "parser_families": set(),
                "stages": set(),
            },
        )
        group = grouped[group_key]
        group["rows"].append(row)
        group["sha256s"].add(sha)
        group["parent_ids"].add(row.get("parent_corpus_database_id", ""))
        group["artifact_ids"].add(artifact_id)
        group["file_names"].add(file_name)
        group["sample_paths"].add(row.get("sample_path", ""))
        group["parser_families"].add(row.get("candidate_parser_family", ""))
        group["stages"].add(row.get("recommended_next_stage", ""))
    return sorted(grouped.values(), key=lambda group: (str(group["path"]), group["table_fingerprint"]))


def corpus_result_rows_for_group(group: dict[str, Any], max_rows: int | None) -> tuple[list[dict[str, str]], dict[str, str]]:
    path: Path = group["path"]
    file_names = sorted(item for item in group["file_names"] if item)
    file_name = file_names[0] if file_names else path.name
    df = read_table(path, file_name, max_rows=max_rows)
    columns = [safe_text(col, 1000) for col in df.columns]
    parent_ids = sorted(item for item in group["parent_ids"] if item)
    artifact_ids = sorted(item for item in group["artifact_ids"] if item)
    sample_paths = sorted(item for item in group["sample_paths"] if item)
    parser_families = sorted(item for item in group["parser_families"] if item)
    stages = sorted(item for item in group["stages"] if item)
    sha256s = sorted(item for item in group["sha256s"] if item)
    primary_parent = parent_ids[0] if parent_ids else ""
    table_id = stable_id("corpus_result_table", group["table_fingerprint"], " | ".join(file_names))
    now = datetime.now().isoformat(timespec="seconds")
    out: list[dict[str, str]] = []
    for idx, record in enumerate(df.astype(str).to_dict(orient="records"), start=1):
        clean_record = {safe_text(key, 1000): safe_text(value) for key, value in record.items()}
        row_json = json.dumps(clean_record, sort_keys=True, ensure_ascii=False)
        key = row_key(clean_record, idx)
        result_id = stable_id("corpus_result", table_id, idx, key, row_json)
        source_locator = f"{repo_path(path)}#row={idx}"
        row = {
            "corpus_result_id": result_id,
            "corpus_result_table_id": table_id,
            "primary_parent_corpus_database_id": primary_parent,
            "parent_corpus_database_ids": " | ".join(parent_ids),
            "source_artifact_ids": " | ".join(artifact_ids),
            "source_artifact_file_names": " | ".join(file_names),
            "source_artifact_local_path": repo_path(path),
            "source_artifact_sha256": " | ".join(sha256s),
            "source_artifact_sample_path": " | ".join(sample_paths),
            "parser_family": " | ".join(parser_families),
            "parser_name": "extract_corpus_results_from_artifacts.py",
            "parser_version": PARSER_VERSION,
            "parser_status": "parsed_native_row",
            "parser_scope": " | ".join(stages),
            "corpus_native_row_number": str(idx),
            "corpus_native_row_key": key,
            "source_locator": source_locator,
            "corpus_native_columns_json": json.dumps(columns, ensure_ascii=False),
            "corpus_native_row_json": row_json,
            "corpus_native_row_text": native_row_text(clean_record),
            "corpus_original_source_text": fields_text(matching_fields(clean_record, ORIGINAL_SOURCE_PATTERNS)),
            "corpus_original_identifier_text": fields_text(matching_fields(clean_record, ORIGINAL_ID_PATTERNS)),
            "corpus_replication_source_text": fields_text(matching_fields(clean_record, REPLICATION_SOURCE_PATTERNS)),
            "corpus_replication_identifier_text": fields_text(matching_fields(clean_record, REPLICATION_ID_PATTERNS)),
            "corpus_result_label_text": fields_text(matching_fields(clean_record, RESULT_LABEL_PATTERNS)),
            "corpus_outcome_text": fields_text(matching_fields(clean_record, OUTCOME_PATTERNS)),
            "corpus_effect_text": fields_text(matching_fields(clean_record, EFFECT_PATTERNS)),
            "corpus_n_text": fields_text(matching_fields(clean_record, N_PATTERNS)),
            "corpus_p_text": fields_text(matching_fields(clean_record, P_PATTERNS)),
            "corpus_ci_text": fields_text(matching_fields(clean_record, CI_PATTERNS)),
            "corpus_se_text": fields_text(matching_fields(clean_record, SE_PATTERNS)),
            "corpus_context_text": fields_text(matching_fields(clean_record, CONTEXT_PATTERNS)),
            "candidate_original_result_id": "",
            "candidate_replication_result_id": "",
            "candidate_pair_id": "",
            "transformation_status": "not_started",
            "source_result_promotion_status": "not_started",
            "evidence_level": "3",
            "evidence_level_name": "external_assertion_with_target_source",
            "review_status": "needs_mapping_review",
            "blocker_codes": "",
            "next_action": "map_corpus_row_to_original_and_replication_sources",
            "notes": "Corpus-native row proposal; no D/N transformation or original-source verification has been performed.",
            "created_at": now,
        }
        out.append(row)
    table_summary = {
        "corpus_result_table_id": table_id,
        "primary_parent_corpus_database_id": primary_parent,
        "parent_corpus_database_ids": " | ".join(parent_ids),
        "source_artifact_ids": " | ".join(artifact_ids),
        "source_artifact_file_names": " | ".join(file_names),
        "source_artifact_local_path": repo_path(path),
        "source_artifact_sha256": " | ".join(sha256s),
        "parser_scope": " | ".join(stages),
        "column_count": str(len(columns)),
        "row_count_emitted": str(len(out)),
        "columns_json": json.dumps(columns, ensure_ascii=False),
    }
    return out, table_summary


def summary_rows(result_rows: list[dict[str, str]], table_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for field in ["primary_parent_corpus_database_id", "parser_scope", "parser_status", "review_status"]:
        for value, count in sorted(Counter(row.get(field, "") for row in result_rows).items()):
            rows.append({"metric": field, "value": value, "count": str(count)})
    rows.append({"metric": "total", "value": "corpus_result_rows", "count": str(len(result_rows))})
    rows.append({"metric": "total", "value": "corpus_result_tables", "count": str(len(table_rows))})
    rows.append({"metric": "total", "value": "rows_with_effect_text", "count": str(sum(1 for row in result_rows if row.get("corpus_effect_text")))})
    rows.append({"metric": "total", "value": "rows_with_n_text", "count": str(sum(1 for row in result_rows if row.get("corpus_n_text")))})
    rows.append({"metric": "total", "value": "rows_with_original_source_text", "count": str(sum(1 for row in result_rows if row.get("corpus_original_source_text")))})
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--replace", action="store_true")
    parser.add_argument(
        "--scope",
        action="append",
        default=["parse_table_result_candidates"],
        help="Parser queue recommended_next_stage to extract. Repeat for multiple scopes.",
    )
    parser.add_argument("--parser-queue", default=str(PARSER_QUEUE_TSV))
    parser.add_argument("--status", default=str(MIRROR_STATUS_TSV))
    parser.add_argument("--output-root", default=str(OUTPUT_ROOT))
    parser.add_argument("--max-rows-per-table", type=int, default=None)
    parser.add_argument("--min-parser-priority", choices=["low", "medium", "high"], default="low")
    args = parser.parse_args()

    columns = schema_columns()
    parser_queue_tsv = resolve_path(args.parser_queue)
    mirror_status_tsv = resolve_path(args.status)
    output_root = resolve_path(args.output_root)
    proposal_tsv = output_root / "corpus-results-proposal.tsv"
    proposal_json = output_root / "corpus-results-proposal.json"
    tables_tsv = output_root / "corpus-result-tables-proposal.tsv"
    summary_tsv = output_root / "corpus-results-summary.tsv"
    queue, status = load_candidates(set(args.scope), parser_queue_tsv, mirror_status_tsv, args.min_parser_priority)
    groups = group_candidates(queue, status)
    result_rows: list[dict[str, str]] = []
    table_rows: list[dict[str, str]] = []
    skipped: list[dict[str, str]] = []
    for group in groups:
        try:
            rows, table = corpus_result_rows_for_group(group, args.max_rows_per_table)
        except Exception as exc:  # noqa: BLE001 - route failures are written as data.
            skipped.append(
                {
                    "source_artifact_local_path": repo_path(group["path"]),
                    "source_artifact_sha256": " | ".join(sorted(group["sha256s"])),
                    "error": safe_text(exc, 2000),
                }
            )
            continue
        result_rows.extend(rows)
        table_rows.append(table)

    write_tsv(proposal_tsv, result_rows, columns, args.replace)
    write_json(
        proposal_json,
        {
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "parser_version": PARSER_VERSION,
            "scope": args.scope,
            "input_parser_queue": repo_path(parser_queue_tsv),
            "input_mirror_status": repo_path(mirror_status_tsv),
            "min_parser_priority": args.min_parser_priority,
            "corpus_result_count": len(result_rows),
            "corpus_result_table_count": len(table_rows),
            "skipped_count": len(skipped),
            "skipped": skipped,
            "records": result_rows,
        },
        args.replace,
    )
    table_columns = [
        "corpus_result_table_id",
        "primary_parent_corpus_database_id",
        "parent_corpus_database_ids",
        "source_artifact_ids",
        "source_artifact_file_names",
        "source_artifact_local_path",
        "source_artifact_sha256",
        "parser_scope",
        "column_count",
        "row_count_emitted",
        "columns_json",
    ]
    write_tsv(tables_tsv, table_rows, table_columns, args.replace)
    write_tsv(summary_tsv, summary_rows(result_rows, table_rows), ["metric", "value", "count"], args.replace)
    print(
        "Corpus-result extraction: "
        f"tables={len(table_rows)}; corpus_results={len(result_rows)}; skipped={len(skipped)}"
    )


if __name__ == "__main__":
    main()
