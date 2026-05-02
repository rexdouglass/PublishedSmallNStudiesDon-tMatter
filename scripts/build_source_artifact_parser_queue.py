#!/usr/bin/env python3
"""Build a parser-candidate queue from mirrored/sampled Figure 1 artifacts.

This is intentionally a conservative routing layer. It does not parse result
values. It reads mirror/sample status plus compact sample JSONs and prioritizes
artifacts whose columns, file names, or previews contain original/replication
pair, effect/statistic, sample-size, and bibliographic identity signals.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
STATUS_TSV = ROOT / "steps" / "source_inventory" / "figure1" / "mirror_sample" / "source-artifact-mirror-sample-status.tsv"
QUEUE_TSV = ROOT / "steps" / "source_inventory" / "figure1" / "parser_queue" / "source-artifact-parser-candidate-queue.tsv"
QUEUE_JSON = ROOT / "steps" / "source_inventory" / "figure1" / "parser_queue" / "source-artifact-parser-candidate-queue.json"
SUMMARY_TSV = ROOT / "steps" / "source_inventory" / "figure1" / "parser_queue" / "source-artifact-parser-candidate-summary.tsv"

DATA_SAMPLE_KINDS = {
    "delimited_table",
    "excel_workbook",
    "json_list",
    "json_object",
    "r_data",
    "stata",
}
TEXT_SAMPLE_KINDS = {"text", "html_text", "pdf_text"}
INVENTORY_SAMPLE_KINDS = {"zip_inventory"}

PAIR_PATTERNS = [
    r"\borig(?:inal)?\b",
    r"\brepl(?:ication|icated|icate|i)?\b",
    r"\breplication\b",
    r"\btarget\b",
    r"\bclaim\b",
    r"\bfinding\b",
    r"\bstudy[_ -]?id\b",
    r"\bpairs?\b",
    r"\bfollow[_ -]?up\b",
]
EFFECT_PATTERNS = [
    r"\beffect\b",
    r"\beffect[_ -]?size\b",
    r"\bcohen",
    r"\bhedges\b",
    r"\bsmd\b",
    r"\bestimate\b",
    r"\bcoef",
    r"\bbeta\b",
    r"\bate\b",
    r"\bodds\b",
    r"\bor\b",
    r"\brr\b",
    r"\bmean\b",
    r"\bsd\b",
    r"\bse\b",
    r"\bci\b",
    r"\bp[_ -]?value\b",
    r"\bpval\b",
    r"\bt[_ -]?stat\b",
    r"\bz[_ -]?stat\b",
]
N_PATTERNS = [
    r"\bn\b",
    r"\bN\b",
    r"\bsample\b",
    r"\bsample[_ -]?size\b",
    r"\bparticipants?\b",
    r"\bsubjects?\b",
    r"\bobservations?\b",
    r"\bobs\b",
    r"\banalyzed\b",
    r"\brandomi[sz]ed\b",
    r"\blabs?\b",
    r"\bsites?\b",
]
IDENTITY_PATTERNS = [
    r"\bdoi\b",
    r"\bpmid\b",
    r"\bpmcid\b",
    r"\btitle\b",
    r"\bauthor\b",
    r"\byear\b",
    r"\bjournal\b",
    r"\bpublication\b",
    r"\burl\b",
    r"\bpaper[_ -]?id\b",
]


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


def load_sample(path_value: str) -> dict[str, Any]:
    if not path_value:
        return {}
    path = resolve_path(path_value)
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except json.JSONDecodeError:
        return {}


def sample_columns(sample: dict[str, Any]) -> list[str]:
    kind = sample.get("sample_kind")
    if kind in {"delimited_table", "stata"}:
        return [safe_text(col, 300) for col in sample.get("columns", [])]
    if kind == "excel_workbook":
        columns: list[str] = []
        for sheet in sample_object_records(sample.get("sheets", [])):
            columns.extend(safe_text(col, 300) for col in sheet.get("columns", []))
        return columns
    if kind == "r_data":
        columns = []
        for obj in sample_object_records(sample.get("objects", [])):
            columns.extend(safe_text(col, 300) for col in obj.get("columns", []))
        return columns
    if kind == "json_object":
        return [safe_text(key, 300) for key in sample.get("keys", [])]
    if kind == "json_list":
        keys: list[str] = []
        for item in sample.get("preview_items", []):
            if isinstance(item, dict):
                keys.extend(safe_text(key, 300) for key in item)
        return sorted(set(keys))
    return []


def sample_object_records(value: object) -> list[dict[str, Any]]:
    if isinstance(value, dict):
        return [item for item in value.values() if isinstance(item, dict)]
    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]
    return []


def preview_text(sample: dict[str, Any]) -> str:
    parts: list[str] = []
    for key in [
        "preview_rows",
        "preview_items",
        "preview",
        "line_preview",
        "pages_preview",
        "links_preview",
        "members_preview",
        "objects",
        "sheets",
    ]:
        if key in sample:
            parts.append(safe_text(json.dumps(sample[key], ensure_ascii=False), 30000))
    return " ".join(parts)[:80000]


def count_patterns(text: str, patterns: list[str]) -> int:
    if not text:
        return 0
    return sum(1 for pattern in patterns if re.search(pattern, text, flags=re.IGNORECASE))


def count_column_patterns(columns: list[str], patterns: list[str]) -> int:
    joined = " ".join(columns)
    return count_patterns(joined, patterns)


def estimated_rows(sample: dict[str, Any]) -> str:
    if sample.get("estimated_data_rows") is not None:
        return str(sample["estimated_data_rows"])
    if sample.get("sample_row_count") is not None:
        return str(sample["sample_row_count"])
    if sample.get("sample_kind") == "json_list" and sample.get("length") is not None:
        return str(sample["length"])
    if sample.get("sample_kind") == "zip_inventory" and sample.get("member_count") is not None:
        return str(sample["member_count"])
    if sample.get("sample_kind") == "excel_workbook":
        counts = [
            sheet.get("sample_row_count")
            for sheet in sample_object_records(sample.get("sheets", []))
            if sheet.get("sample_row_count") is not None
        ]
        return str(max(counts)) if counts else ""
    if sample.get("sample_kind") == "r_data":
        shapes = [obj.get("shape") for obj in sample_object_records(sample.get("objects", [])) if obj.get("shape")]
        return str(max(shape[0] for shape in shapes if shape)) if shapes else ""
    return ""


def score_row(status: dict[str, str], sample: dict[str, Any]) -> dict[str, str]:
    columns = sample_columns(sample)
    text = " ".join([status.get("file_name", ""), status.get("artifact_role", ""), status.get("candidate_parser_family", ""), " ".join(columns), preview_text(sample)])
    pair_cols = count_column_patterns(columns, PAIR_PATTERNS)
    effect_cols = count_column_patterns(columns, EFFECT_PATTERNS)
    n_cols = count_column_patterns(columns, N_PATTERNS)
    identity_cols = count_column_patterns(columns, IDENTITY_PATTERNS)
    pair_hits = max(pair_cols, count_patterns(text, PAIR_PATTERNS))
    effect_hits = max(effect_cols, count_patterns(text, EFFECT_PATTERNS))
    n_hits = max(n_cols, count_patterns(text, N_PATTERNS))
    identity_hits = max(identity_cols, count_patterns(text, IDENTITY_PATTERNS))
    sample_kind = status.get("sample_kind", "")
    is_data = sample_kind in DATA_SAMPLE_KINDS
    is_text = sample_kind in TEXT_SAMPLE_KINDS
    is_inventory = sample_kind in INVENTORY_SAMPLE_KINDS
    role = status.get("artifact_role", "")
    file_name_lower = status.get("file_name", "").lower()
    metadata_like = (
        role == "source_access_metadata"
        or any(token in file_name_lower for token in ["metadata", "manifest", "file_list", "download", "probe", "status", "tracking"])
    )

    score = 0
    if is_data:
        score += 20
    if role in {"data_file", "codebook", "file_inventory"}:
        score += 8
    if pair_cols:
        score += 18
    elif pair_hits:
        score += 8
    if effect_cols:
        score += 15
    elif effect_hits:
        score += 6
    if n_cols:
        score += 12
    elif n_hits:
        score += 5
    if identity_cols:
        score += 8
    elif identity_hits:
        score += 3
    if status.get("sample_status") == "sample_failed":
        score -= 10
    if status.get("sample_status") == "metadata_only":
        score -= 12
    if status.get("sample_status") == "not_sampled":
        score -= 20
    if metadata_like:
        score -= 12
    if is_text:
        score -= 4
    if is_inventory:
        score -= 2

    if metadata_like and not (pair_cols and effect_cols and n_cols):
        route = "inventory_metadata_and_links"
    elif is_data and pair_cols and (effect_cols or n_cols):
        route = "parse_table_result_candidates"
    elif is_data and (pair_cols or effect_cols or n_cols or pair_hits or effect_hits or n_hits):
        route = "inspect_sample_for_result_fields"
    elif role == "codebook" and status.get("sample_status") == "sampled":
        route = "pair_with_data_table_for_parser"
    elif is_text and (pair_hits or effect_hits or n_hits):
        route = "inspect_code_or_text_for_generated_tables"
    elif sample_kind in {"json_object", "json_list", "zip_inventory"}:
        route = "inventory_metadata_and_links"
    elif status.get("sample_status") in {"sample_failed", "not_sampled"}:
        route = "repair_or_manual_inventory"
    else:
        route = "deprioritize_for_figure1_parsing"

    priority = "high" if score >= 48 else "medium" if score >= 28 else "low"
    if route == "parse_table_result_candidates" and score >= 38:
        priority = "high"
    reason_bits = []
    if pair_hits:
        reason_bits.append(f"pair_signals={pair_hits}")
    if effect_hits:
        reason_bits.append(f"effect_signals={effect_hits}")
    if n_hits:
        reason_bits.append(f"n_signals={n_hits}")
    if identity_hits:
        reason_bits.append(f"identity_signals={identity_hits}")
    if not reason_bits:
        reason_bits.append("no strong field signatures")

    return {
        "artifact_id": status.get("artifact_id", ""),
        "parent_corpus_database_id": status.get("parent_corpus_database_id", ""),
        "artifact_role": role,
        "file_name": status.get("file_name", ""),
        "sample_kind": sample_kind,
        "sample_status": status.get("sample_status", ""),
        "candidate_parser_family": status.get("candidate_parser_family", ""),
        "mirror_local_path": status.get("mirror_local_path", ""),
        "sample_path": status.get("sample_path", ""),
        "estimated_rows_or_members": estimated_rows(sample),
        "column_count": str(len(columns)),
        "columns_preview": safe_text("; ".join(columns[:40]), 4000),
        "pair_signal_count": str(pair_hits),
        "effect_signal_count": str(effect_hits),
        "n_signal_count": str(n_hits),
        "identity_signal_count": str(identity_hits),
        "priority_score": str(score),
        "parser_priority": priority,
        "recommended_next_stage": route,
        "routing_basis": "; ".join(reason_bits),
        "queued_at": datetime.now().isoformat(timespec="seconds"),
    }


def summary_rows(queue_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for field in ["parser_priority", "recommended_next_stage", "parent_corpus_database_id", "sample_kind"]:
        for value, count in sorted(Counter(row.get(field, "") for row in queue_rows).items()):
            rows.append({"metric": field, "value": value, "artifact_count": str(count)})
    rows.append({"metric": "total", "value": "parser_queue_artifacts", "artifact_count": str(len(queue_rows))})
    rows.append(
        {
            "metric": "total",
            "value": "high_priority_parse_table_result_candidates",
            "artifact_count": str(
                sum(
                    1
                    for row in queue_rows
                    if row["parser_priority"] == "high" and row["recommended_next_stage"] == "parse_table_result_candidates"
                )
            ),
        }
    )
    return rows


def main() -> None:
    global QUEUE_TSV, QUEUE_JSON, SUMMARY_TSV
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--status", default=str(STATUS_TSV))
    parser.add_argument("--output-root", default=str(QUEUE_TSV.parent))
    parser.add_argument("--replace", action="store_true")
    args = parser.parse_args()

    output_root = resolve_path(args.output_root)
    QUEUE_TSV = output_root / "source-artifact-parser-candidate-queue.tsv"
    QUEUE_JSON = output_root / "source-artifact-parser-candidate-queue.json"
    SUMMARY_TSV = output_root / "source-artifact-parser-candidate-summary.tsv"

    status_rows = read_tsv(resolve_path(args.status))
    queue_rows = [score_row(row, load_sample(row.get("sample_path", ""))) for row in status_rows]
    queue_rows.sort(key=lambda row: (-int(row["priority_score"]), row["parent_corpus_database_id"], row["file_name"]))
    columns = [
        "artifact_id",
        "parent_corpus_database_id",
        "artifact_role",
        "file_name",
        "sample_kind",
        "sample_status",
        "candidate_parser_family",
        "mirror_local_path",
        "sample_path",
        "estimated_rows_or_members",
        "column_count",
        "columns_preview",
        "pair_signal_count",
        "effect_signal_count",
        "n_signal_count",
        "identity_signal_count",
        "priority_score",
        "parser_priority",
        "recommended_next_stage",
        "routing_basis",
        "queued_at",
    ]
    write_tsv(QUEUE_TSV, queue_rows, columns, args.replace)
    write_json(
        QUEUE_JSON,
        {
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "status_input": repo_path(resolve_path(args.status)),
            "artifact_count": len(queue_rows),
            "records": queue_rows,
        },
        args.replace,
    )
    write_tsv(SUMMARY_TSV, summary_rows(queue_rows), ["metric", "value", "artifact_count"], args.replace)
    high = sum(1 for row in queue_rows if row["parser_priority"] == "high")
    parse_tables = sum(1 for row in queue_rows if row["recommended_next_stage"] == "parse_table_result_candidates")
    print(f"Parser queue artifacts: artifacts={len(queue_rows)}; high_priority={high}; parse_table_candidates={parse_tables}")


if __name__ == "__main__":
    main()
