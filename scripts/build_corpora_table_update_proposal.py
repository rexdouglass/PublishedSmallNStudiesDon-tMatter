#!/usr/bin/env python3
"""Build a safe CORPORA_AND_DATABASES.tsv update proposal from review-cue routing.

This is the last-mile proposal step. It does not mutate the root table. It
turns validated review-cue receipts into:

- a proposed row-level update table,
- a validation table,
- an updated preview table, and
- a GPT/human field-coding cue for accepted rows whose prose/semantic fields
  need source-aware coding.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
import yaml


ROOT = Path(__file__).resolve().parents[1]
PIPELINE_YML = ROOT / "PROVENANCE_PIPELINE_SINGLE_SOURCE_OF_TRUTH.yml"
MASTER_TSV = ROOT / "CORPORA_AND_DATABASES.tsv"
SCHEMA_YML = ROOT / "CORPORA_AND_DATABASES_SCHEMA.yml"

ADVANCE_DECISIONS = {"keep_in_corpora_and_databases", "promote_to_corpora_and_databases"}
ROUTE_DECISIONS = {
    "route_to_result_table_worklist",
    "route_to_individual_replication_paper_worklist",
}

STATUS_BY_DECISION = {
    "keep_in_corpora_and_databases": "needs_source_inventory",
    "promote_to_corpora_and_databases": "needs_source_inventory",
    "route_to_result_table_worklist": "routed_to_result_table_worklist",
    "route_to_individual_replication_paper_worklist": "routed_to_individual_replication_worklist",
    "keep_as_context_source": "catalog_only_context_lead",
    "reject_irrelevant": "rejected_irrelevant_search_hit",
    "needs_more_evidence": "needs_more_evidence",
}

FIELDS_FOR_GPT_CODING = [
    "source_family",
    "domain_or_field",
    "description",
    "why_relevant",
    "result_fields_available",
    "has_d_or_convertible_effect",
    "has_n",
    "has_replication_pair_mapping",
    "has_publication_links",
    "parser_family",
    "blocker_codes",
    "next_action",
    "notes",
]

PROPOSAL_META_COLUMNS = [
    "proposal_action",
    "coding_task_id",
    "lead_key",
    "review_id",
    "decision",
    "routing_class",
    "receipt_path",
    "matched_existing_row",
    "matched_existing_corpus_database_id",
    "field_coding_required",
    "fields_requiring_coding",
    "proposal_basis",
]


def safe_text(value: object, max_len: int = 12000) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and pd.isna(value):
        return ""
    text = str(value).replace("\t", " ")
    return re.sub(r"\s+", " ", text).strip()[:max_len]


def slugify(value: object, fallback: str = "source") -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", safe_text(value).lower()).strip("_")
    return slug[:160] or fallback


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


def output_root(cue: dict[str, Any]) -> Path:
    return cue_root(cue) / "apply_to_CORPORA_AND_DATABASES"


def read_master() -> tuple[list[str], list[dict[str, str]]]:
    with MASTER_TSV.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        return list(reader.fieldnames or []), [{key: safe_text(value) for key, value in row.items()} for row in reader]


def read_routing(cue: dict[str, Any]) -> list[dict[str, str]]:
    path = cue_root(cue) / f"reviewcue-routing-table-{cue['id']}.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    return [{key: safe_text(value) for key, value in row.items()} for row in payload.get("records", [])]


def lead_key_for_name(name: str) -> str:
    return f"title:{slugify(name)}"


def split_values(value: object) -> list[str]:
    text = safe_text(value)
    if not text:
        return []
    return [part.strip() for part in re.split(r"\s*\|\s*|\s*;\s*", text) if part.strip()]


def merge_pipe(*values: object) -> str:
    seen: list[str] = []
    for value in values:
        for part in split_values(value):
            if part not in seen:
                seen.append(part)
    return " | ".join(seen)


def master_indexes(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    index: dict[str, dict[str, str]] = {}
    for row in rows:
        name_key = lead_key_for_name(row.get("name", ""))
        if name_key != "title:source":
            index.setdefault(name_key, row)
        for field in ["source_key", "landing_url", "raw_url"]:
            for value in split_values(row.get(field)):
                index.setdefault(f"{field}:{value.lower()}", row)
                index.setdefault(value.lower(), row)
    return index


def find_master_row(routing_row: dict[str, str], index: dict[str, dict[str, str]]) -> dict[str, str] | None:
    candidates = [
        routing_row.get("lead_key", ""),
        routing_row.get("canonical_source_key", ""),
        f"source_key:{routing_row.get('canonical_source_key', '').lower()}",
        f"landing_url:{routing_row.get('canonical_source_key', '').lower()}",
    ]
    for key in candidates:
        if key and key in index:
            return index[key]
    canonical = routing_row.get("canonical_source_key", "").lower()
    if canonical:
        for row in index.values():
            haystack = " | ".join(row.get(field, "").lower() for field in ["source_key", "landing_url", "raw_url"])
            if canonical in haystack:
                return row
    return None


def status_for_decision(decision: str) -> str:
    return STATUS_BY_DECISION.get(decision, "needs_more_evidence")


def proposal_action(decision: str, matched: bool) -> str:
    if decision in ADVANCE_DECISIONS:
        return "update_existing_root_candidate" if matched else "append_root_candidate"
    if decision in ROUTE_DECISIONS:
        return "update_existing_route_status" if matched else "append_routed_lead"
    if decision == "keep_as_context_source":
        return "update_existing_context_status" if matched else "append_context_lead"
    if decision == "reject_irrelevant":
        return "update_existing_rejection_status" if matched else "append_rejected_lead"
    return "defer_needs_more_evidence"


def default_row(columns: list[str]) -> dict[str, str]:
    return {column: "" for column in columns}


def apply_decision_to_row(columns: list[str], routing: dict[str, str], existing: dict[str, str] | None) -> dict[str, str]:
    row = default_row(columns)
    if existing:
        row.update({column: existing.get(column, "") for column in columns})
    name_from_lead = routing.get("lead_key", "").removeprefix("title:").replace("_", " ").strip().title()
    decision = routing.get("decision", "")
    is_advance = decision in ADVANCE_DECISIONS
    is_route = decision in ROUTE_DECISIONS
    row["name"] = row.get("name") or name_from_lead
    row["corpus_database_id"] = row.get("corpus_database_id") or f"reviewcue_{slugify(routing.get('lead_key') or routing.get('review_id'))}"
    row["record_kind"] = row.get("record_kind") or ("candidate_corpus_or_database" if is_advance else "candidate_repository_package")
    row["inventory_status"] = status_for_decision(decision)
    if is_advance or is_route:
        row["plot_universe_ids"] = merge_pipe(row.get("plot_universe_ids"), "plot1_replication_pairs")
        row["figure1_replication_relevance"] = "yes"
    elif decision in {"keep_as_context_source", "reject_irrelevant"}:
        row["figure1_replication_relevance"] = "no"
    if is_advance:
        row["current_scope_roles"] = merge_pipe(row.get("current_scope_roles"), "figure1_candidate")
        row["parser_status"] = row.get("parser_status") or "not_started"
    elif decision == "route_to_result_table_worklist":
        row["current_scope_roles"] = merge_pipe(row.get("current_scope_roles"), "figure1_routed_result_table")
    elif decision == "route_to_individual_replication_paper_worklist":
        row["current_scope_roles"] = merge_pipe(row.get("current_scope_roles"), "figure1_routed_individual_replication")
    elif decision == "keep_as_context_source":
        row["current_scope_roles"] = merge_pipe(row.get("current_scope_roles"), "context_source")
    elif decision == "reject_irrelevant":
        row["current_scope_roles"] = merge_pipe(row.get("current_scope_roles"), "search_rejected")
    row["source_key"] = merge_pipe(row.get("source_key"), routing.get("canonical_source_key"))
    row["next_action"] = routing.get("next_action") or row.get("next_action")
    row["notes"] = merge_pipe(
        row.get("notes"),
        f"review_cue={routing.get('cue_id')}; decision={decision}; confidence={routing.get('confidence')}; reason={routing.get('reason')}",
    )
    row["last_seen"] = utc_now()[:10]
    return row


def field_needs_coding(field: str, value: str, decision: str) -> bool:
    text = safe_text(value).lower()
    if decision not in ADVANCE_DECISIONS:
        return False
    if field in {"description", "domain_or_field", "source_family", "result_fields_available", "parser_family"}:
        return not text or text in {"unknown", "not_assigned", "not_started"}
    if field in {"has_d_or_convertible_effect", "has_n", "has_replication_pair_mapping", "has_publication_links"}:
        return not text or text == "unknown"
    if field == "why_relevant":
        return (not text) or text.startswith("matched figure 1")
    if field in {"next_action", "notes"}:
        return not text
    return False


def coding_fields_for(row: dict[str, str], decision: str) -> list[str]:
    return [field for field in FIELDS_FOR_GPT_CODING if field_needs_coding(field, row.get(field, ""), decision)]


def build_proposal_rows(
    columns: list[str],
    master_rows: list[dict[str, str]],
    routing_rows: list[dict[str, str]],
) -> list[dict[str, str]]:
    index = master_indexes(master_rows)
    rows: list[dict[str, str]] = []
    for routing in routing_rows:
        decision = routing.get("decision", "")
        existing = find_master_row(routing, index)
        proposed = apply_decision_to_row(columns, routing, existing)
        fields_requiring_coding = coding_fields_for(proposed, decision)
        meta = {
            "proposal_action": proposal_action(decision, bool(existing)),
            "coding_task_id": f"fieldcode_{slugify(routing.get('lead_key') or routing.get('review_id'))}",
            "lead_key": routing.get("lead_key", ""),
            "review_id": routing.get("review_id", ""),
            "decision": decision,
            "routing_class": routing.get("routing_class", ""),
            "receipt_path": routing.get("receipt_path", ""),
            "matched_existing_row": "yes" if existing else "no",
            "matched_existing_corpus_database_id": existing.get("corpus_database_id", "") if existing else "",
            "field_coding_required": "yes" if fields_requiring_coding else "no",
            "fields_requiring_coding": " | ".join(fields_requiring_coding),
            "proposal_basis": routing.get("reason", ""),
        }
        rows.append({**meta, **proposed})
    return rows


def validation_rows(proposals: list[dict[str, str]], columns: list[str]) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    seen_ids: set[str] = set()
    for row in proposals:
        issues: list[str] = []
        if row["decision"] in ADVANCE_DECISIONS:
            for field in ["name", "record_kind", "inventory_status", "why_relevant", "next_action"]:
                if not row.get(field):
                    issues.append(f"missing_required_advance_field:{field}")
            if not (row.get("landing_url") or row.get("source_key")):
                issues.append("missing_required_advance_identifier")
        if row.get("corpus_database_id") in seen_ids:
            issues.append("duplicate_proposed_corpus_database_id")
        seen_ids.add(row.get("corpus_database_id", ""))
        extra_columns = sorted(set(row) - set(PROPOSAL_META_COLUMNS) - set(columns))
        if extra_columns:
            issues.append("unexpected_columns:" + ",".join(extra_columns))
        out.append(
            {
                "lead_key": row.get("lead_key", ""),
                "decision": row.get("decision", ""),
                "proposal_action": row.get("proposal_action", ""),
                "validation_status": "ok" if not issues else "blocked",
                "issues": " | ".join(issues),
                "field_coding_required": row.get("field_coding_required", ""),
                "fields_requiring_coding": row.get("fields_requiring_coding", ""),
            }
        )
    return out


def preview_rows(master_rows: list[dict[str, str]], proposals: list[dict[str, str]], columns: list[str]) -> list[dict[str, str]]:
    by_id = {row.get("corpus_database_id", ""): dict(row) for row in master_rows}
    for proposal in proposals:
        row = {column: proposal.get(column, "") for column in columns}
        by_id[row["corpus_database_id"]] = row
    return sorted(by_id.values(), key=lambda row: (row.get("record_kind", ""), row.get("name", "").lower()))


def gpt_needed_rows(proposals: list[dict[str, str]], output_dir: Path, batch_id: str) -> list[dict[str, str]]:
    target_response = output_dir / f"gpt-field-coding-response-{batch_id}.json"
    rows: list[dict[str, str]] = []
    for row in proposals:
        if row.get("field_coding_required") != "yes":
            continue
        evidence_packet = {
            "lead_key": row.get("lead_key"),
            "name": row.get("name"),
            "decision": row.get("decision"),
            "proposal_basis": row.get("proposal_basis"),
            "landing_url": row.get("landing_url"),
            "source_key": row.get("source_key"),
            "current_description": row.get("description"),
            "current_why_relevant": row.get("why_relevant"),
            "current_notes": row.get("notes"),
        }
        rows.append(
            {
                "coding_task_id": row.get("coding_task_id", ""),
                "lead_key": row.get("lead_key", ""),
                "name": row.get("name", ""),
                "landing_url": row.get("landing_url", ""),
                "source_key": row.get("source_key", ""),
                "decision": row.get("decision", ""),
                "fields_to_code": row.get("fields_requiring_coding", ""),
                "target_response_path": repo_path(target_response),
                "evidence_packet_json": json.dumps(evidence_packet, sort_keys=True),
            }
        )
    return rows


def prompt_text(cue_id: str, coding_rows: list[dict[str, str]], response_path: Path) -> str:
    lines = [
        f"# GPT Field-Coding Prompt: {cue_id}",
        "",
        "You are coding rows for `CORPORA_AND_DATABASES.tsv` in a provenance pipeline.",
        "Use web research only to support the requested fields. Do not invent file contents, row counts, column names, or parser status.",
        "If a field requires artifact/file inspection rather than surface metadata, set it to `unknown` and say what must be inspected next.",
        "",
        f"Return JSON only. The user will save it as `{repo_path(response_path)}`.",
        "",
        "JSON shape:",
        "",
        "```json",
        json.dumps(
            {
                "field_coding_decisions": [
                    {
                        "coding_task_id": "...",
                        "lead_key": "...",
                        "field_values": {field: "..." for field in FIELDS_FOR_GPT_CODING},
                        "field_basis": {field: "short evidence basis or unknown rationale" for field in FIELDS_FOR_GPT_CODING},
                        "field_confidence": {field: "high|medium|low" for field in FIELDS_FOR_GPT_CODING},
                        "sources_checked": ["URL or file path"],
                    }
                ]
            },
            indent=2,
        ),
        "```",
        "",
        "Allowed yes/no fields must use `yes`, `no`, or `unknown`: `has_d_or_convertible_effect`, `has_n`, `has_replication_pair_mapping`, `has_publication_links`.",
        "",
        "Rows to code:",
    ]
    for idx, row in enumerate(coding_rows, start=1):
        lines.extend(
            [
                "",
                f"## {idx}. {row['name']}",
                f"- coding_task_id: `{row['coding_task_id']}`",
                f"- lead_key: `{row['lead_key']}`",
                f"- landing_url: `{row['landing_url']}`",
                f"- source_key: `{row['source_key']}`",
                f"- fields_to_code: `{row['fields_to_code']}`",
                "",
                "Evidence packet:",
                "",
                "```json",
                json.dumps(json.loads(row["evidence_packet_json"]), indent=2, sort_keys=True),
                "```",
            ]
        )
    return "\n".join(lines) + "\n"


def write_tsv(path: Path, rows: list[dict[str, str]], columns: list[str], replace: bool) -> None:
    if path.exists() and not replace:
        print(f"Skipped {repo_path(path)} because it exists. Use --replace to rebuild.")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {repo_path(path)}")


def write_text(path: Path, text: str, replace: bool) -> None:
    if path.exists() and not replace:
        print(f"Skipped {repo_path(path)} because it exists. Use --replace to rebuild.")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    print(f"Wrote {repo_path(path)}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cue-id", default="figure1_search_leads")
    parser.add_argument("--batch-id", default="reset001")
    parser.add_argument("--replace", action="store_true")
    args = parser.parse_args()

    cue = load_cue(args.cue_id)
    columns, master_rows = read_master()
    routing_rows = read_routing(cue)
    out_dir = output_root(cue)

    proposals = build_proposal_rows(columns, master_rows, routing_rows)
    validations = validation_rows(proposals, columns)
    preview = preview_rows(master_rows, proposals, columns)
    coding_rows = gpt_needed_rows(proposals, out_dir, args.batch_id)

    proposal_path = out_dir / "corpora-table-update-proposal.tsv"
    validation_path = out_dir / "corpora-table-update-validation.tsv"
    preview_path = out_dir / "corpora-table-updated-preview.tsv"
    coding_path = out_dir / "gpt-field-coding-needed.tsv"
    response_path = out_dir / f"gpt-field-coding-response-{args.batch_id}.json"
    prompt_path = out_dir / f"gpt-field-coding-prompt-{args.batch_id}.md"

    write_tsv(proposal_path, proposals, PROPOSAL_META_COLUMNS + columns, args.replace)
    write_tsv(validation_path, validations, list(validations[0].keys()) if validations else ["lead_key"], args.replace)
    write_tsv(preview_path, preview, columns, args.replace)
    write_tsv(coding_path, coding_rows, list(coding_rows[0].keys()) if coding_rows else ["coding_task_id"], args.replace)
    write_text(prompt_path, prompt_text(args.cue_id, coding_rows, response_path), args.replace)

    blocked = sum(1 for row in validations if row.get("validation_status") == "blocked")
    print(
        f"Proposal rows={len(proposals)}; validation_blocked={blocked}; "
        f"gpt_field_coding_rows={len(coding_rows)}"
    )


if __name__ == "__main__":
    main()
