#!/usr/bin/env python3
"""Filter SOURCE_ARTIFACTS-shaped proposals into parser-first worksets.

This keeps the DAG target-file pattern explicit: broad acquisition can discover
many candidate artifacts, then narrower mirror/sample steps can consume a
deterministic subset instead of trying every PDF, landing page, and metadata
record at once.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
TABLE_FIRST_TYPES = {
    "csv",
    "csv.gz",
    "tsv",
    "tab",
    "txt",
    "xlsx",
    "xls",
    "json",
    "zip",
    "rds",
    "rdata",
    "dta",
    "sav",
    "r",
    "rmd",
    "py",
    "do",
    "sps",
}
DOCUMENT_FIRST_TYPES = {"pdf", "html", "htm"}


def clean(value: object) -> str:
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value).replace("\t", " ")).strip()


def repo_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def read_tsv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        rows = [{key: clean(value) for key, value in row.items()} for row in reader]
        return list(reader.fieldnames or []), rows


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


def write_summary(path: Path, rows: list[dict[str, str]], input_count: int, replace: bool) -> None:
    summary_rows: list[dict[str, str]] = [
        {"metric": "total", "value": "input_rows", "count": str(input_count)},
        {"metric": "total", "value": "kept_rows", "count": str(len(rows))},
    ]
    for field in ["artifact_role", "provider", "candidate_parser_family", "file_type", "parent_corpus_database_id"]:
        for value, count in Counter(row.get(field, "") or "blank" for row in rows).most_common():
            summary_rows.append({"metric": field, "value": value, "count": str(count)})
    write_tsv(path, summary_rows, ["metric", "value", "count"], replace)


def keep_row(row: dict[str, str], mode: str) -> bool:
    if mode not in {"result-table-first", "document-first", "remaining-downloadable"}:
        raise ValueError(f"Unsupported mode: {mode}")
    file_type = clean(row.get("file_type")).lower()
    has_materializable_route = bool(clean(row.get("raw_url")) or clean(row.get("local_path")))
    if not has_materializable_route:
        return False
    if mode == "result-table-first":
        return file_type in TABLE_FIRST_TYPES
    if mode == "document-first":
        return file_type in DOCUMENT_FIRST_TYPES
    return file_type not in TABLE_FIRST_TYPES | DOCUMENT_FIRST_TYPES


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--json-output", type=Path)
    parser.add_argument("--summary", type=Path)
    parser.add_argument(
        "--mode",
        default="result-table-first",
        choices=["result-table-first", "document-first", "remaining-downloadable"],
    )
    parser.add_argument("--replace", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    columns, rows = read_tsv(args.input)
    kept = [row for row in rows if keep_row(row, args.mode)]
    write_tsv(args.output, kept, columns, args.replace)
    if args.json_output:
        write_json(args.json_output, {"mode": args.mode, "rows": kept}, args.replace)
    if args.summary:
        write_summary(args.summary, kept, len(rows), args.replace)
    print(f"Filtered source artifacts: input={len(rows)}; kept={len(kept)}; mode={args.mode}")


if __name__ == "__main__":
    main()
