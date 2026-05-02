#!/usr/bin/env python3
"""Build reusable Codex/GPT review cues from configured provenance leads.

The root YAML defines each cue. This script only materializes deterministic
queue artifacts and bounded prompt batches; it does not call any LLM and it
does not apply decisions back into root tables.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
import yaml


ROOT = Path(__file__).resolve().parents[1]
PIPELINE_YML = ROOT / "PROVENANCE_PIPELINE_SINGLE_SOURCE_OF_TRUTH.yml"


def safe_text(value: object, max_len: int = 6000) -> str:
    if value is None:
        return ""
    text = re.sub(r"\s+", " ", str(value).replace("\t", " ")).strip()
    return text[:max_len]


def slugify(value: object, fallback: str = "lead") -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", safe_text(value).lower()).strip("_")
    return slug[:120] or fallback


def filesystem_slug(value: object, fallback: str = "lead") -> str:
    return slugify(value, fallback=fallback)[:160]


def stable_id(prefix: str, *parts: object) -> str:
    text = "\n".join(safe_text(part, max_len=10000) for part in parts)
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]
    label = slugify(next((part for part in parts if safe_text(part)), prefix))
    return f"{prefix}_{label}_{digest}"


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


def split_values(value: object) -> list[str]:
    text = safe_text(value)
    if not text:
        return []
    return [part.strip() for part in re.split(r"\s*\|\s*|\s*;\s*", text) if part.strip()]


def lead_key(row: dict[str, str]) -> str:
    name = safe_text(row.get("name") or row.get("title") or row.get("lead_title"))
    if name:
        return f"title:{slugify(name)}"
    for field in ["landing_url", "raw_url", "source_key", "external_id", "url"]:
        value = safe_text(row.get(field))
        if value:
            return f"{field}:{value.lower()}"
    return stable_id("lead_key", row.get("review_id"), row.get("description"), row.get("manifest_path"))


def load_yaml() -> dict[str, Any]:
    payload = yaml.safe_load(PIPELINE_YML.read_text(encoding="utf-8")) or {}
    return payload.get("PROVENANCE_PIPELINE_SINGLE_SOURCE_OF_TRUTH") or {}


def load_cue(cue_id: str) -> dict[str, Any]:
    for cue in load_yaml().get("review_cues") or []:
        if cue.get("id") == cue_id:
            return cue
    raise ValueError(f"Unknown review cue {cue_id!r} in {repo_path(PIPELINE_YML)}")


def target_keys(cue: dict[str, Any]) -> set[str]:
    context = cue.get("target_context") or {}
    root_table = safe_text(context.get("root_table"))
    if not root_table:
        return set()
    path = resolve_path(root_table)
    if not path.exists():
        return set()
    df = pd.read_csv(path, sep="\t", dtype=str, keep_default_na=False)
    keys: set[str] = set()
    skip_columns = context.get("skip_key_columns") or ["landing_url", "source_key"]
    for row in df.to_dict(orient="records"):
        row = {key: safe_text(value) for key, value in row.items()}
        keys.add(lead_key(row))
        for column in skip_columns:
            for value in split_values(row.get(column)):
                keys.add(f"{column}:{value.lower()}")
    return keys


def reviewed_keys(cue: dict[str, Any]) -> set[str]:
    keys: set[str] = set()
    for pattern in cue.get("reviewed_decision_globs") or []:
        for path in sorted(ROOT.glob(pattern)):
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                continue
            for item in payload.get("decisions", []):
                if not isinstance(item, dict):
                    continue
                key = safe_text(item.get("lead_key") or item.get("review_id"))
                if key:
                    keys.add(key)
    return keys


def receipt_key_values(item: dict[str, Any]) -> set[str]:
    keys: set[str] = set()
    for field in ["lead_key", "review_id", "canonical_source_key", "duplicate_of"]:
        value = safe_text(item.get(field))
        if value:
            keys.add(value)
    return keys


def existing_receipt_keys(cue: dict[str, Any]) -> set[str]:
    """Return reviewed keys based on materialized per-lead receipt files."""
    keys: set[str] = set()
    receipts = cue.get("route_receipts") or {}
    root = receipts.get("root")
    if not root:
        return keys
    root_path = resolve_path(str(root))
    if not root_path.exists():
        return keys
    for path in root_path.glob("*/*.json"):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        keys.update(receipt_key_values(payload))
    return keys


def receipt_path_for(cue: dict[str, Any], row: dict[str, str], decision: str) -> Path:
    receipts = cue.get("route_receipts") or {}
    root = resolve_path(str(receipts.get("root") or f"steps/review_cue/{cue['id']}/receipts"))
    routes = receipts.get("decision_directories") or {}
    directory = safe_text(routes.get(decision) or routes.get("default") or "needs_more_evidence")
    key = filesystem_slug(row.get("lead_key") or row.get("review_id"))
    return root / directory / f"{key}.json"


def manifest_leads(cue: dict[str, Any]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for source in cue.get("source_inputs") or []:
        pattern = safe_text(source.get("glob"))
        buckets = source.get("buckets") or ["candidates", "routed_or_rejected_leads"]
        if not pattern:
            continue
        for path in sorted(ROOT.glob(pattern)):
            payload = json.loads(path.read_text(encoding="utf-8"))
            for bucket in buckets:
                for item in payload.get(bucket, []):
                    if not isinstance(item, dict):
                        continue
                    row = {key: safe_text(value) for key, value in item.items()}
                    row["cue_id"] = safe_text(cue.get("id"))
                    row["source_input_id"] = safe_text(source.get("id"))
                    row["manifest_path"] = repo_path(path)
                    row["manifest_bucket"] = safe_text(bucket)
                    row["lead_key"] = lead_key(row)
                    row["review_id"] = stable_id(
                        "review",
                        cue.get("id"),
                        row.get("lead_key"),
                        row.get("record_kind"),
                        row.get("landing_url"),
                        row.get("source_key"),
                    )
                    receipt_decision = "keep_in_corpora_and_databases" if row.get("record_kind") in set((cue.get("target_context") or {}).get("root_record_kinds") or []) else "needs_more_evidence"
                    row["route_receipt_candidate_path"] = repo_path(receipt_path_for(cue, row, receipt_decision))
                    rows.append(row)
    deduped: dict[str, dict[str, str]] = {}
    for row in rows:
        key = row["lead_key"]
        existing = deduped.get(key)
        if not existing:
            deduped[key] = row
            continue
        for field in ["manifest_path", "manifest_bucket", "discovery_source", "source_key", "landing_url"]:
            values: list[str] = []
            for value in split_values(existing.get(field)) + split_values(row.get(field)):
                if value not in values:
                    values.append(value)
            existing[field] = " | ".join(values)
    return list(deduped.values())


def review_status(row: dict[str, str], cue: dict[str, Any], known_target_keys: set[str], known_reviewed: set[str]) -> str:
    if row["lead_key"] in known_reviewed or row["review_id"] in known_reviewed:
        return "already_reviewed"
    context = cue.get("target_context") or {}
    root_kinds = set(context.get("root_record_kinds") or [])
    root_review_statuses = set(context.get("root_review_statuses") or [])
    record_kind = row.get("record_kind")
    inventory_status = row.get("inventory_status")
    if record_kind in root_kinds:
        if inventory_status in root_review_statuses:
            return "needs_root_candidate_review"
        return "already_root_candidate"
    if row["lead_key"] in known_target_keys:
        return "already_in_root_target"
    if inventory_status in set(cue.get("deterministic_skip_statuses") or []):
        return "deterministically_skipped"
    if record_kind not in set(cue.get("review_record_kinds") or []):
        return "not_review_record_kind"
    return "needs_review"


def priority(row: dict[str, str], cue: dict[str, Any]) -> tuple[int, str]:
    order = cue.get("priority_order") or []
    ranks = {kind: index for index, kind in enumerate(order)}
    rank = ranks.get(row.get("record_kind"), len(ranks) + 10)
    if row.get("triage_queue_status") == "needs_root_candidate_review":
        rank -= 20
    if row.get("inventory_status") == "needs_triage_search_lead":
        rank -= 2
    return rank, row.get("name", "").lower()


def build_queue(cue: dict[str, Any]) -> tuple[list[dict[str, str]], dict[str, int], int]:
    known_target_keys = target_keys(cue)
    known_reviewed = reviewed_keys(cue) | existing_receipt_keys(cue)
    leads = manifest_leads(cue)
    queue: list[dict[str, str]] = []
    skip_counts: dict[str, int] = {}
    for row in leads:
        status = review_status(row, cue, known_target_keys, known_reviewed)
        row["triage_queue_status"] = status
        if status in {"needs_review", "needs_root_candidate_review"}:
            queue.append(row)
        else:
            skip_counts[status] = skip_counts.get(status, 0) + 1
    queue.sort(key=lambda row: priority(row, cue))
    return queue, skip_counts, len(leads)


def output_path(cue: dict[str, Any], key: str, **values: str) -> Path:
    outputs = cue.get("outputs") or {}
    pattern = outputs.get(key)
    if not pattern:
        root = cue.get("cue_root") or f"steps/review_cue/{cue['id']}"
        pattern = f"{root}/reviewcue-{key}-{cue['id']}.json"
    text = str(pattern).format(**values)
    return resolve_path(text)


def decision_contract(cue: dict[str, Any]) -> dict[str, Any]:
    contract = cue.get("decision_contract") or {}
    return {
        "allowed_decisions": contract.get("allowed_decisions") or [
            "keep_in_current_target",
            "promote_to_current_target",
            "route_to_other_worklist",
            "keep_as_context_source",
            "reject_irrelevant",
            "needs_more_evidence",
        ],
        "required_fields": contract.get("required_fields") or [
            "review_id",
            "lead_key",
            "decision",
            "confidence",
            "reason",
            "next_action",
        ],
        "optional_fields": contract.get("optional_fields") or [
            "sources_checked",
            "promote_payload",
            "route_payload",
            "user_gpt_prompt_request",
        ],
        "allowed_confidence": contract.get("allowed_confidence") or ["high", "medium", "low"],
        "decision_specific_requirements": contract.get("decision_specific_requirements") or {},
    }


def lead_lines(rows: list[dict[str, str]]) -> list[str]:
    lines: list[str] = []
    for i, row in enumerate(rows, start=1):
        lines.extend(
            [
                f"{i}. review_id: {row['review_id']}",
                f"   lead_key: {row['lead_key']}",
                f"   queue_status: {row.get('triage_queue_status', '')}",
                f"   name: {row.get('name', '')}",
                f"   record_kind: {row.get('record_kind', '')}",
                f"   inventory_status: {row.get('inventory_status', '')}",
                f"   url: {row.get('landing_url', '')}",
                f"   source_key: {row.get('source_key', '')}",
                f"   description: {row.get('description', '')}",
                f"   current heuristic reason: {row.get('why_relevant', '')}",
                "",
            ]
        )
    return lines


def codex_prompt(cue: dict[str, Any], rows: list[dict[str, str]], decision_path: Path) -> str:
    contract = decision_contract(cue)
    lines = [
        f"You are a Codex background reviewer for review cue `{cue['id']}`.",
        safe_text(cue.get("purpose")),
        "",
        "Work only this bounded batch. Investigate URLs and source metadata when useful.",
        "Do not edit root tables. Return or save JSON decisions using the contract below.",
        "Each accepted decision will later be applied as a per-lead receipt file, so future cue builds can skip it by checking for that target file.",
        "If you are not confident, set decision to `needs_more_evidence` and include `user_gpt_prompt_request` with a compact prompt the user can give to GPT Pro.",
        "",
        f"Save decisions as: `{repo_path(decision_path)}`",
        "",
        "Allowed decisions:",
    ]
    lines.extend(f"- {decision}" for decision in contract["allowed_decisions"])
    lines.extend(
        [
            "",
            "Each decision requires:",
            ", ".join(contract["required_fields"]),
            "",
            "Decision-specific requirements:",
            json.dumps(contract.get("decision_specific_requirements") or {}, indent=2, sort_keys=True),
            "",
            "Return JSON in this shape:",
            '{"decisions": [{"review_id": "...", "lead_key": "...", "decision": "...", "confidence": "high|medium|low", "reason": "...", "next_action": "...", "sources_checked": [], "promote_payload": {}, "route_payload": {}, "user_gpt_prompt_request": ""}]}',
            "",
            "Leads:",
        ]
    )
    lines.extend(lead_lines(rows))
    return "\n".join(lines)


def gpt_prompt(cue: dict[str, Any], rows: list[dict[str, str]], decision_path: Path) -> str:
    contract = decision_contract(cue)
    lines = [
        f"You are reviewing `{cue['id']}` leads for a provenance pipeline.",
        "Use web research if needed. Do not infer relevance from search terms alone.",
        "Classify up to 50 leads. Be conservative: reject or route away if the source is only an individual paper, method paper, or irrelevant false positive.",
        "Each decision will later become a per-lead receipt file, so future cue builds can skip reviewed items by target-file existence.",
        "",
        f"The user will save your JSON as: `{repo_path(decision_path)}`",
        "",
        "Allowed decisions:",
    ]
    lines.extend(f"- {decision}" for decision in contract["allowed_decisions"])
    lines.extend(
        [
            "",
            "Return JSON only, with a `decisions` array. Required fields:",
            ", ".join(contract["required_fields"]),
            "",
            "Decision-specific requirements:",
            json.dumps(contract.get("decision_specific_requirements") or {}, indent=2, sort_keys=True),
            "",
            "For `needs_more_evidence`, say exactly what source, page, file, or identifier should be checked next.",
            "",
            "Leads:",
        ]
    )
    lines.extend(lead_lines(rows))
    return "\n".join(lines)


def write_json(path: Path, payload: dict[str, Any], replace: bool) -> bool:
    if path.exists() and not replace:
        print(f"Skipped {repo_path(path)} because it exists. Use --replace to rebuild.")
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    print(f"Wrote {repo_path(path)}")
    return True


def write_text(path: Path, text: str, replace: bool) -> bool:
    if path.exists() and not replace:
        print(f"Skipped {repo_path(path)} because it exists. Use --replace to rebuild.")
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    print(f"Wrote {repo_path(path)}")
    return True


def write_batch(
    *,
    cue: dict[str, Any],
    queue: list[dict[str, str]],
    batch_id: str,
    reviewer: str,
    batch_size: int,
    offset: int,
    replace: bool,
) -> None:
    rows = queue[max(offset, 0) : max(offset, 0) + max(batch_size, 0)]
    decision_path = output_path(cue, "decision_json_pattern", cue_id=cue["id"], batch_id=batch_id, reviewer=reviewer)
    batch_path = output_path(cue, f"{reviewer}_batch_json_pattern", cue_id=cue["id"], batch_id=batch_id)
    prompt_path = output_path(cue, f"{reviewer}_prompt_md_pattern", cue_id=cue["id"], batch_id=batch_id)
    prompt = codex_prompt(cue, rows, decision_path) if reviewer == "codex" else gpt_prompt(cue, rows, decision_path)
    payload = {
        "created_at": utc_now(),
        "cue_id": cue["id"],
        "reviewer": reviewer,
        "batch_id": batch_id,
        "batch_size": len(rows),
        "offset": offset,
        "remaining_after_batch": max(len(queue) - (max(offset, 0) + len(rows)), 0),
        "decision_output": repo_path(decision_path),
        "review_instructions": decision_contract(cue),
        "prompt": prompt,
        "leads": rows,
    }
    write_json(batch_path, payload, replace)
    title = f"# {cue['id']} {reviewer.title()} Review Prompt"
    body = "\n".join([title, "", f"Save returned JSON as `{repo_path(decision_path)}`.", "", "```text", prompt, "```", ""])
    write_text(prompt_path, body, replace)


def write_index(cue: dict[str, Any], queue_path: Path, queue: list[dict[str, str]], skip_counts: dict[str, int]) -> None:
    cue_root = resolve_path(cue.get("cue_root") or f"steps/review_cue/{cue['id']}")
    path = cue_root / f"reviewcue-index-{cue['id']}.md"
    lines = [
        f"# Review Cue: {cue['id']}",
        "",
        safe_text(cue.get("purpose")),
        "",
        f"- Queue: `{repo_path(queue_path)}`",
        f"- Open items: {len(queue)}",
        f"- Skip counts: `{json.dumps(skip_counts, sort_keys=True)}`",
        "",
        "Run:",
        "",
        f"```bash\npython scripts/build_review_cue.py --cue-id {cue['id']} --replace\n```",
        "",
        "Codex can work a small batch and write decisions. GPT Pro handoff prompts are generated as Markdown prompt files in this directory.",
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {repo_path(path)}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cue-id", required=True)
    parser.add_argument("--batch-id", default="batch001")
    parser.add_argument("--codex-batch-size", type=int, default=None)
    parser.add_argument("--gpt-batch-size", type=int, default=None)
    parser.add_argument("--codex-offset", type=int, default=0)
    parser.add_argument("--gpt-offset", type=int, default=0)
    parser.add_argument("--mode", choices=["both", "codex", "gpt", "queue"], default="both")
    parser.add_argument("--replace", action="store_true")
    args = parser.parse_args()

    cue = load_cue(args.cue_id)
    replace = args.replace or os.environ.get("REPLACE_REVIEW_CUE_TARGETS") == "1"
    queue, skip_counts, total_leads = build_queue(cue)
    queue_path = output_path(cue, "queue_json", cue_id=cue["id"])
    queue_payload = {
        "created_at": utc_now(),
        "cue_id": cue["id"],
        "purpose": safe_text(cue.get("purpose")),
        "total_input_leads": total_leads,
        "open_review_count": len(queue),
        "skip_counts": skip_counts,
        "queue": queue,
    }
    write_json(queue_path, queue_payload, replace=True)

    batch_policy = cue.get("batch_policy") or {}
    codex_size = args.codex_batch_size if args.codex_batch_size is not None else int(batch_policy.get("codex_batch_size", 20))
    gpt_size = args.gpt_batch_size if args.gpt_batch_size is not None else int(batch_policy.get("gpt_batch_size", 50))

    if args.mode in {"both", "codex"}:
        write_batch(
            cue=cue,
            queue=queue,
            batch_id=args.batch_id,
            reviewer="codex",
            batch_size=codex_size,
            offset=args.codex_offset,
            replace=replace,
        )
    if args.mode in {"both", "gpt"}:
        write_batch(
            cue=cue,
            queue=queue,
            batch_id=args.batch_id,
            reviewer="gpt",
            batch_size=gpt_size,
            offset=args.gpt_offset,
            replace=replace,
        )
    write_index(cue, queue_path, queue, skip_counts)
    print(f"Review cue {cue['id']}: {len(queue)} open item(s); skips: {skip_counts}")


if __name__ == "__main__":
    main()
