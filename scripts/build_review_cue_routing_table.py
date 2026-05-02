#!/usr/bin/env python3
"""Build machine-readable routing tables from review-cue receipt files.

Receipt files are the durable per-lead skip targets. This script fans them back
into aggregate TSV/JSON artifacts that downstream steps can consume without
having to traverse decision-specific receipt directories.
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
import yaml


ROOT = Path(__file__).resolve().parents[1]
PIPELINE_YML = ROOT / "PROVENANCE_PIPELINE_SINGLE_SOURCE_OF_TRUTH.yml"


ROUTE_MAP = {
    "keep_in_corpora_and_databases": {
        "routing_class": "advance",
        "downstream_target": "CORPORA_AND_DATABASES.tsv",
        "advances_to_root_target": "true",
        "advances_to_figure1_pair_intake": "true",
        "terminal_for_current_cue": "false",
        "next_step_family": "root_corpora_database_application",
    },
    "promote_to_corpora_and_databases": {
        "routing_class": "advance",
        "downstream_target": "CORPORA_AND_DATABASES.tsv",
        "advances_to_root_target": "true",
        "advances_to_figure1_pair_intake": "true",
        "terminal_for_current_cue": "false",
        "next_step_family": "root_corpora_database_application",
    },
    "route_to_result_table_worklist": {
        "routing_class": "route",
        "downstream_target": "future_result_table_worklist.tsv",
        "advances_to_root_target": "false",
        "advances_to_figure1_pair_intake": "true",
        "terminal_for_current_cue": "false",
        "next_step_family": "result_table_or_artifact_mapping",
    },
    "route_to_individual_replication_paper_worklist": {
        "routing_class": "route",
        "downstream_target": "future_individual_replication_pair_worklist.tsv",
        "advances_to_root_target": "false",
        "advances_to_figure1_pair_intake": "true",
        "terminal_for_current_cue": "false",
        "next_step_family": "individual_replication_pair_screening",
    },
    "keep_as_context_source": {
        "routing_class": "context",
        "downstream_target": "future_context_sources.tsv",
        "advances_to_root_target": "false",
        "advances_to_figure1_pair_intake": "false",
        "terminal_for_current_cue": "true",
        "next_step_family": "context_or_later_plot_cataloging",
    },
    "reject_irrelevant": {
        "routing_class": "reject",
        "downstream_target": "none",
        "advances_to_root_target": "false",
        "advances_to_figure1_pair_intake": "false",
        "terminal_for_current_cue": "true",
        "next_step_family": "none",
    },
    "needs_more_evidence": {
        "routing_class": "escalate",
        "downstream_target": "future_gpt_or_human_prompt_queue.tsv",
        "advances_to_root_target": "false",
        "advances_to_figure1_pair_intake": "unknown",
        "terminal_for_current_cue": "false",
        "next_step_family": "human_or_gpt_escalation",
    },
}


def safe_text(value: object, max_len: int = 12000) -> str:
    if value is None:
        return ""
    text = str(value).replace("\t", " ")
    return re.sub(r"\s+", " ", text).strip()[:max_len]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def repo_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def resolve_path(path: str) -> Path:
    value = Path(path)
    return value if value.is_absolute() else ROOT / value


def load_cue(cue_id: str) -> dict[str, Any]:
    payload = yaml.safe_load(PIPELINE_YML.read_text(encoding="utf-8")) or {}
    root = payload.get("PROVENANCE_PIPELINE_SINGLE_SOURCE_OF_TRUTH") or {}
    for cue in root.get("review_cues") or []:
        if cue.get("id") == cue_id:
            return cue
    raise ValueError(f"Unknown review cue {cue_id!r}")


def cue_root(cue: dict[str, Any]) -> Path:
    return resolve_path(str(cue.get("cue_root") or f"steps/review_cue/{cue['id']}"))


def receipt_root(cue: dict[str, Any]) -> Path:
    receipts = cue.get("route_receipts") or {}
    return resolve_path(str(receipts.get("root") or cue_root(cue) / "receipts"))


def default_output(cue: dict[str, Any], suffix: str) -> Path:
    outputs = cue.get("outputs") or {}
    configured = outputs.get(f"routing_table_{suffix}")
    if configured:
        return resolve_path(str(configured).format(cue_id=cue["id"]))
    return cue_root(cue) / f"reviewcue-routing-table-{cue['id']}.{suffix}"


def json_cell(value: Any) -> str:
    if value in (None, "", [], {}):
        return ""
    return json.dumps(value, sort_keys=True, ensure_ascii=False)


def receipt_records(cue: dict[str, Any]) -> list[dict[str, str]]:
    root = receipt_root(cue)
    rows: list[dict[str, str]] = []
    if not root.exists():
        return rows
    for path in sorted(root.glob("*/*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        decision = safe_text(payload.get("decision"))
        route = ROUTE_MAP.get(
            decision,
            {
                "routing_class": "unknown",
                "downstream_target": "unknown",
                "advances_to_root_target": "unknown",
                "advances_to_figure1_pair_intake": "unknown",
                "terminal_for_current_cue": "false",
                "next_step_family": "needs_route_mapping",
            },
        )
        rows.append(
            {
                "cue_id": safe_text(payload.get("cue_id") or cue["id"]),
                "created_at": safe_text(payload.get("created_at")),
                "decision_source": safe_text(payload.get("decision_source")),
                "receipt_path": repo_path(path),
                "receipt_decision_directory": path.parent.name,
                "review_id": safe_text(payload.get("review_id")),
                "lead_key": safe_text(payload.get("lead_key")),
                "canonical_source_key": safe_text(payload.get("canonical_source_key")),
                "duplicate_of": safe_text(payload.get("duplicate_of")),
                "decision": decision,
                "confidence": safe_text(payload.get("confidence")),
                "routing_class": route["routing_class"],
                "downstream_target": route["downstream_target"],
                "advances_to_root_target": route["advances_to_root_target"],
                "advances_to_figure1_pair_intake": route["advances_to_figure1_pair_intake"],
                "terminal_for_current_cue": route["terminal_for_current_cue"],
                "next_step_family": route["next_step_family"],
                "next_action": safe_text(payload.get("next_action")),
                "reason": safe_text(payload.get("reason")),
                "sources_checked_json": json_cell(payload.get("sources_checked") or []),
                "promote_payload_json": json_cell(payload.get("promote_payload") or {}),
                "route_payload_json": json_cell(payload.get("route_payload") or {}),
                "user_gpt_prompt_request": safe_text(payload.get("user_gpt_prompt_request")),
                "notes": safe_text(payload.get("notes")),
            }
        )
    return rows


def counts(rows: list[dict[str, str]], field: str) -> dict[str, int]:
    out: dict[str, int] = {}
    for row in rows:
        value = row.get(field, "")
        out[value] = out.get(value, 0) + 1
    return dict(sorted(out.items()))


def validate_no_conflicting_receipts(rows: list[dict[str, str]]) -> None:
    by_key: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        key = row.get("lead_key") or row.get("review_id")
        if not key:
            continue
        by_key.setdefault(key, []).append(row)
    conflicts = {key: values for key, values in by_key.items() if len(values) > 1}
    if not conflicts:
        return
    examples = []
    for key, values in sorted(conflicts.items())[:10]:
        decisions = ", ".join(sorted({value.get("decision", "") for value in values}))
        paths = ", ".join(value.get("receipt_path", "") for value in values)
        examples.append(f"{key}: {decisions}; {paths}")
    raise ValueError("Conflicting duplicate receipt(s): " + " | ".join(examples))


def write_outputs(cue: dict[str, Any], rows: list[dict[str, str]], tsv_path: Path, json_path: Path, replace: bool) -> None:
    validate_no_conflicting_receipts(rows)
    for path in [tsv_path, json_path]:
        if path.exists() and not replace:
            raise FileExistsError(f"{repo_path(path)} exists; pass --replace to rebuild")
        path.parent.mkdir(parents=True, exist_ok=True)

    df = pd.DataFrame(rows)
    df.to_csv(tsv_path, sep="\t", index=False)
    payload = {
        "created_at": utc_now(),
        "cue_id": cue["id"],
        "receipt_root": repo_path(receipt_root(cue)),
        "row_count": len(rows),
        "counts_by_decision": counts(rows, "decision"),
        "counts_by_routing_class": counts(rows, "routing_class"),
        "records": rows,
    }
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {repo_path(tsv_path)}")
    print(f"Wrote {repo_path(json_path)}")
    print(f"Review cue {cue['id']}: routing_rows={len(rows)}; decisions={payload['counts_by_decision']}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cue-id", required=True)
    parser.add_argument("--tsv-output")
    parser.add_argument("--json-output")
    parser.add_argument("--replace", action="store_true")
    args = parser.parse_args()

    cue = load_cue(args.cue_id)
    tsv_path = resolve_path(args.tsv_output) if args.tsv_output else default_output(cue, "tsv")
    json_path = resolve_path(args.json_output) if args.json_output else default_output(cue, "json")
    write_outputs(cue, receipt_records(cue), tsv_path, json_path, args.replace)


if __name__ == "__main__":
    main()
