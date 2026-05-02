#!/usr/bin/env python3
"""Fan clustered review routing into downstream worklist target files."""

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
ROUTING_TSV = ROOT / "steps" / "review_cue" / "figure1_search_leads" / "reviewcue-clustered-routing-table-figure1_search_leads.tsv"
RESULT_ROOT = ROOT / "steps" / "result_tables" / "figure1"
INDIVIDUAL_ROOT = ROOT / "steps" / "individual_replication_papers" / "figure1"
RESULT_TSV = RESULT_ROOT / "result-table-worklist-from-cluster-review.tsv"
RESULT_JSON = RESULT_ROOT / "result-table-worklist-from-cluster-review.json"
INDIVIDUAL_TSV = INDIVIDUAL_ROOT / "individual-paper-worklist-from-cluster-review.tsv"
INDIVIDUAL_JSON = INDIVIDUAL_ROOT / "individual-paper-worklist-from-cluster-review.json"


def safe_text(value: object, max_len: int = 12000) -> str:
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value).replace("\t", " ")).strip()[:max_len]


def repo_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def stable_id(prefix: str, *parts: object) -> str:
    text = "\n".join(safe_text(part, 20000) for part in parts)
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]
    return f"{prefix}_{digest}"


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return [{key: safe_text(value) for key, value in row.items()} for row in csv.DictReader(handle, delimiter="\t")]


def write_tsv(path: Path, rows: list[dict[str, str]], replace: bool) -> None:
    if path.exists() and not replace:
        print(f"Skipped {repo_path(path)} because it exists. Use --replace to rebuild.")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0].keys()) if rows else [
        "worklist_task_id",
        "route_type",
        "cluster_id",
        "parent_corpus_database_id_or_key",
        "preferred_source_family_name",
    ]
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


def read_receipt_notes(receipt_path: str) -> list[dict[str, str]]:
    path = ROOT / receipt_path
    if not path.exists():
        return []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    notes: list[dict[str, str]] = []
    for note in payload.get("lead_level_notes") or []:
        if isinstance(note, dict):
            notes.append({key: safe_text(value) for key, value in note.items()})
    return notes


def worklist_row(row: dict[str, str], route_type: str) -> dict[str, str]:
    notes = read_receipt_notes(row.get("receipt_path", ""))
    if route_type == "result_table":
        relevant = [note for note in notes if note.get("suggested_disposition") in {"child_artifact", "context", "needs_more_evidence"}]
    else:
        relevant = [note for note in notes if note.get("suggested_disposition") in {"individual_paper", "context", "needs_more_evidence"}]
    return {
        "worklist_task_id": stable_id("worklist_task", route_type, row.get("cluster_id"), row.get("parent_corpus_database_id_or_key")),
        "route_type": route_type,
        "cluster_id": row.get("cluster_id", ""),
        "decision": row.get("decision", ""),
        "confidence": row.get("confidence", ""),
        "parent_corpus_database_id_or_key": row.get("parent_corpus_database_id_or_key", ""),
        "preferred_source_family_name": row.get("preferred_source_family_name", ""),
        "receipt_path": row.get("receipt_path", ""),
        "source_count": row.get("source_count", ""),
        "lead_level_note_count": row.get("lead_level_note_count", ""),
        "candidate_artifact_or_paper_notes_json": json.dumps(relevant, sort_keys=True, ensure_ascii=False),
        "reason": row.get("reason", ""),
        "next_action": row.get("next_action", ""),
        "created_at": datetime.now().isoformat(timespec="seconds"),
    }


def payload_for(rows: list[dict[str, str]], route_type: str) -> dict[str, Any]:
    return {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "routing_table": repo_path(ROUTING_TSV),
        "route_type": route_type,
        "task_count": len(rows),
        "records": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--routing-tsv", default=str(ROUTING_TSV))
    parser.add_argument("--replace", action="store_true")
    args = parser.parse_args()

    routing_path = Path(args.routing_tsv)
    if not routing_path.is_absolute():
        routing_path = ROOT / routing_path
    rows = read_tsv(routing_path)
    result_rows = [worklist_row(row, "result_table") for row in rows if row.get("needs_result_table_worklist") == "true"]
    individual_rows = [worklist_row(row, "individual_paper") for row in rows if row.get("needs_individual_paper_worklist") == "true"]

    write_tsv(RESULT_TSV, result_rows, args.replace)
    write_json(RESULT_JSON, payload_for(result_rows, "result_table"), args.replace)
    write_tsv(INDIVIDUAL_TSV, individual_rows, args.replace)
    write_json(INDIVIDUAL_JSON, payload_for(individual_rows, "individual_paper"), args.replace)
    print(f"Cluster route worklists: result_table={len(result_rows)}; individual_paper={len(individual_rows)}")


if __name__ == "__main__":
    main()
