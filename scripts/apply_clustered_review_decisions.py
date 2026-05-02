#!/usr/bin/env python3
"""Apply clustered Figure 1 review decisions to durable routing targets.

Cluster review is intentionally separate from per-lead review. A cluster can
decide that many aliases/files belong under one source family, or that an
individual paper/package should be routed away from corpus intake. This script
materializes those decisions as target files and aggregate routing tables, but
it never edits CORPORA_AND_DATABASES.tsv.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
REVIEW_ROOT = ROOT / "steps" / "review_cue" / "figure1_search_leads"
INVENTORY_ROOT = ROOT / "steps" / "source_inventory" / "figure1"

DEFAULT_ROUTING_TSV = REVIEW_ROOT / "reviewcue-clustered-routing-table-figure1_search_leads.tsv"
DEFAULT_ROUTING_JSON = REVIEW_ROOT / "reviewcue-clustered-routing-table-figure1_search_leads.json"
DEFAULT_INVENTORY_QUEUE_TSV = INVENTORY_ROOT / "source-family-artifact-inventory-queue.tsv"
DEFAULT_INVENTORY_QUEUE_JSON = INVENTORY_ROOT / "source-family-artifact-inventory-queue.json"

ROUTE_MAP = {
    "inventory_source_family_artifacts": {
        "route_target": "source_family_artifact_inventory",
        "needs_source_family_inventory": "true",
        "needs_root_candidate_review": "false",
        "needs_result_table_worklist": "false",
        "needs_individual_paper_worklist": "false",
        "context_only": "false",
        "terminal_for_cluster_review": "false",
    },
    "keep_source_family_candidate": {
        "route_target": "corpora_update_proposal_then_source_family_inventory",
        "needs_source_family_inventory": "true",
        "needs_root_candidate_review": "true",
        "needs_result_table_worklist": "false",
        "needs_individual_paper_worklist": "false",
        "context_only": "false",
        "terminal_for_cluster_review": "false",
    },
    "route_cluster_to_result_table_worklist": {
        "route_target": "result_table_worklist",
        "needs_source_family_inventory": "false",
        "needs_root_candidate_review": "false",
        "needs_result_table_worklist": "true",
        "needs_individual_paper_worklist": "false",
        "context_only": "false",
        "terminal_for_cluster_review": "false",
    },
    "route_cluster_to_individual_replication_paper_worklist": {
        "route_target": "individual_replication_paper_worklist",
        "needs_source_family_inventory": "false",
        "needs_root_candidate_review": "false",
        "needs_result_table_worklist": "false",
        "needs_individual_paper_worklist": "true",
        "context_only": "false",
        "terminal_for_cluster_review": "false",
    },
    "keep_cluster_as_context": {
        "route_target": "context_only",
        "needs_source_family_inventory": "false",
        "needs_root_candidate_review": "false",
        "needs_result_table_worklist": "false",
        "needs_individual_paper_worklist": "false",
        "context_only": "true",
        "terminal_for_cluster_review": "true",
    },
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def safe_text(value: object, max_len: int = 12000) -> str:
    if value is None:
        return ""
    text = str(value).replace("\t", " ")
    return re.sub(r"\s+", " ", text).strip()[:max_len]


def repo_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def resolve_path(path: str | None) -> Path | None:
    if not path:
        return None
    value = Path(path)
    return value if value.is_absolute() else ROOT / value


def latest_decision_file() -> Path:
    candidates = sorted(
        REVIEW_ROOT.glob("reviewcue-clustered-decisions-figure1_search_leads-codex-*.json"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    if not candidates:
        raise FileNotFoundError(
            "No clustered decision file found under "
            f"{repo_path(REVIEW_ROOT)}. Pass --decision-file explicitly."
        )
    return candidates[0]


def decision_file_for_batch(batch_id: str) -> Path:
    return REVIEW_ROOT / f"reviewcue-clustered-decisions-figure1_search_leads-codex-{batch_id}.json"


def load_decisions(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    decisions = payload.get("cluster_decisions")
    if not isinstance(decisions, list):
        raise ValueError(f"{repo_path(path)} does not contain cluster_decisions list")
    return payload


def json_cell(value: Any) -> str:
    if value in (None, "", [], {}):
        return ""
    return json.dumps(value, sort_keys=True, ensure_ascii=False)


def stable_id(*parts: object, prefix: str) -> str:
    text = "\n".join(safe_text(part) for part in parts)
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]
    return f"{prefix}_{digest}"


def receipt_path(batch_id: str, cluster_id: str) -> Path:
    slug = re.sub(r"[^a-z0-9_]+", "_", safe_text(cluster_id).lower()).strip("_")
    return REVIEW_ROOT / "cluster_receipts" / batch_id / f"{slug or 'cluster'}.json"


def route_for(decision: str) -> dict[str, str]:
    return ROUTE_MAP.get(
        decision,
        {
            "route_target": "needs_route_mapping",
            "needs_source_family_inventory": "unknown",
            "needs_root_candidate_review": "unknown",
            "needs_result_table_worklist": "unknown",
            "needs_individual_paper_worklist": "unknown",
            "context_only": "unknown",
            "terminal_for_cluster_review": "false",
        },
    )


def write_receipts(
    payload: dict[str, Any],
    decision_source: Path,
    batch_id: str,
    replace: bool,
) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    created_at = utc_now()
    for decision in payload.get("cluster_decisions") or []:
        if not isinstance(decision, dict):
            continue
        cluster_id = safe_text(decision.get("cluster_id"))
        if not cluster_id:
            continue
        out_path = receipt_path(batch_id, cluster_id)
        if out_path.exists() and not replace:
            receipt = json.loads(out_path.read_text(encoding="utf-8"))
        else:
            receipt = {
                "created_at": created_at,
                "batch_id": batch_id,
                "decision_source": repo_path(decision_source),
                "cluster_id": cluster_id,
                "decision": safe_text(decision.get("decision")),
                "confidence": safe_text(decision.get("confidence")),
                "preferred_source_family_name": safe_text(decision.get("preferred_source_family_name")),
                "parent_corpus_database_id_or_key": safe_text(decision.get("parent_corpus_database_id_or_key")),
                "reason": safe_text(decision.get("reason")),
                "next_action": safe_text(decision.get("next_action")),
                "sources_checked": decision.get("sources_checked") or [],
                "lead_level_notes": decision.get("lead_level_notes") or [],
                "lead_level_note_count": len(decision.get("lead_level_notes") or []),
            }
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(json.dumps(receipt, indent=2, sort_keys=True, ensure_ascii=False), encoding="utf-8")
            print(f"Wrote {repo_path(out_path)}")
        rows.append(receipt_to_row(receipt, out_path))
    return rows


def all_receipt_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    root = REVIEW_ROOT / "cluster_receipts"
    if not root.exists():
        return rows
    for path in sorted(root.glob("*/*.json")):
        try:
            receipt = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        if isinstance(receipt, dict):
            rows.append(receipt_to_row(receipt, path))
    return rows


def receipt_to_row(receipt: dict[str, Any], path: Path) -> dict[str, str]:
    decision = safe_text(receipt.get("decision"))
    route = route_for(decision)
    return {
        "batch_id": safe_text(receipt.get("batch_id")),
        "cluster_id": safe_text(receipt.get("cluster_id")),
        "decision": decision,
        "confidence": safe_text(receipt.get("confidence")),
        "preferred_source_family_name": safe_text(receipt.get("preferred_source_family_name")),
        "parent_corpus_database_id_or_key": safe_text(receipt.get("parent_corpus_database_id_or_key")),
        "route_target": route["route_target"],
        "needs_source_family_inventory": route["needs_source_family_inventory"],
        "needs_root_candidate_review": route["needs_root_candidate_review"],
        "needs_result_table_worklist": route["needs_result_table_worklist"],
        "needs_individual_paper_worklist": route["needs_individual_paper_worklist"],
        "context_only": route["context_only"],
        "terminal_for_cluster_review": route["terminal_for_cluster_review"],
        "source_count": str(len(receipt.get("sources_checked") or [])),
        "lead_level_note_count": str(receipt.get("lead_level_note_count") or len(receipt.get("lead_level_notes") or [])),
        "receipt_path": repo_path(path),
        "reason": safe_text(receipt.get("reason")),
        "next_action": safe_text(receipt.get("next_action")),
        "sources_checked_json": json_cell(receipt.get("sources_checked") or []),
    }


def write_tsv(path: Path, rows: list[dict[str, str]], replace: bool) -> None:
    if path.exists() and not replace:
        print(f"Skipped {repo_path(path)} because it exists. Use --replace to rebuild.")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0].keys()) if rows else ["batch_id", "cluster_id", "decision"]
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


def inventory_rows(routing_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for row in routing_rows:
        if row.get("needs_source_family_inventory") != "true":
            continue
        task_id = stable_id(
            row.get("cluster_id"),
            row.get("parent_corpus_database_id_or_key"),
            row.get("preferred_source_family_name"),
            prefix="inventory_task",
        )
        rows.append(
            {
                "inventory_task_id": task_id,
                "cluster_id": row["cluster_id"],
                "parent_corpus_database_id_or_key": row["parent_corpus_database_id_or_key"],
                "preferred_source_family_name": row["preferred_source_family_name"],
                "route_target": row["route_target"],
                "inventory_priority": "high" if row.get("confidence") == "high" else "medium",
                "confidence": row.get("confidence", ""),
                "source_count": row.get("source_count", ""),
                "lead_level_note_count": row.get("lead_level_note_count", ""),
                "decision_receipt_path": row.get("receipt_path", ""),
                "inventory_reason": row.get("reason", ""),
                "next_action": row.get("next_action", ""),
            }
        )
    return rows


def counts(rows: list[dict[str, str]], field: str) -> dict[str, int]:
    out: dict[str, int] = {}
    for row in rows:
        key = row.get(field, "")
        out[key] = out.get(key, 0) + 1
    return dict(sorted(out.items()))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--decision-file")
    parser.add_argument("--batch-id", default="clustered001")
    parser.add_argument("--routing-tsv", default=str(DEFAULT_ROUTING_TSV))
    parser.add_argument("--routing-json", default=str(DEFAULT_ROUTING_JSON))
    parser.add_argument("--inventory-queue-tsv", default=str(DEFAULT_INVENTORY_QUEUE_TSV))
    parser.add_argument("--inventory-queue-json", default=str(DEFAULT_INVENTORY_QUEUE_JSON))
    parser.add_argument("--replace", action="store_true")
    args = parser.parse_args()

    decision_path = resolve_path(args.decision_file) if args.decision_file else decision_file_for_batch(args.batch_id)
    if not decision_path or not decision_path.exists():
        decision_path = latest_decision_file()
    payload = load_decisions(decision_path)

    write_receipts(payload, decision_path, args.batch_id, args.replace)
    routing_rows = all_receipt_rows()
    inventory_queue_rows = inventory_rows(routing_rows)

    routing_payload = {
        "created_at": utc_now(),
        "decision_source": repo_path(decision_path),
        "batch_id": args.batch_id,
        "routing_scope": "all_cluster_receipts",
        "cluster_count": len(routing_rows),
        "counts_by_decision": counts(routing_rows, "decision"),
        "counts_by_route_target": counts(routing_rows, "route_target"),
        "records": routing_rows,
    }
    inventory_payload = {
        "created_at": utc_now(),
        "decision_source": repo_path(decision_path),
        "batch_id": args.batch_id,
        "routing_scope": "all_cluster_receipts",
        "task_count": len(inventory_queue_rows),
        "records": inventory_queue_rows,
    }

    write_tsv(resolve_path(args.routing_tsv) or DEFAULT_ROUTING_TSV, routing_rows, args.replace)
    write_json(resolve_path(args.routing_json) or DEFAULT_ROUTING_JSON, routing_payload, args.replace)
    write_tsv(resolve_path(args.inventory_queue_tsv) or DEFAULT_INVENTORY_QUEUE_TSV, inventory_queue_rows, args.replace)
    write_json(resolve_path(args.inventory_queue_json) or DEFAULT_INVENTORY_QUEUE_JSON, inventory_payload, args.replace)
    print(
        "Cluster review routing: "
        f"clusters={len(routing_rows)}; inventory_tasks={len(inventory_queue_rows)}; "
        f"decisions={routing_payload['counts_by_decision']}"
    )


if __name__ == "__main__":
    main()
