#!/usr/bin/env python3
"""Build bounded Codex review batches for unresolved Figure 1 search leads.

This is a deterministic pre-triage step. It does not ask an LLM anything.
It reads concrete search manifests, removes leads that are already in the root
corpus/database target or already reviewed, and writes a moderate-size JSON
batch for on-demand Codex review.
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


ROOT = Path(__file__).resolve().parents[1]
SEARCH_DIR = ROOT / "steps" / "searches" / "figure1"
SEARCH_GLOB = "corporasearch-*.json"
OUT_DIR = ROOT / "steps" / "triage" / "figure1"
ROOT_TABLE = ROOT / "CORPORA_AND_DATABASES.tsv"

QUEUE_TARGET = OUT_DIR / "codextriage-queue-figure1-search-leads.json"
DEFAULT_BATCH_TARGET = OUT_DIR / "codextriage-batch001-figure1-search-leads.json"
DECISION_GLOB = "codextriage-decisions-figure1-*.json"

ROOT_RECORD_KINDS = {
    "candidate_corpus_or_database",
    "candidate_repository_package",
}

REVIEW_RECORD_KINDS = {
    "candidate_corpus_or_database",
    "candidate_repository_package",
    "candidate_result_table",
    "candidate_bibliographic_paper",
    "candidate_context_or_methods_paper",
    "candidate_individual_paper_or_package",
}

ROOT_REVIEW_STATUSES = {
    "needs_triage_search_lead",
}


def safe_text(value: object, max_len: int = 4000) -> str:
    if value is None:
        return ""
    text = re.sub(r"\s+", " ", str(value).replace("\t", " ")).strip()
    return text[:max_len]


def slugify(value: object, fallback: str = "lead") -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", safe_text(value).lower()).strip("_")
    return slug[:100] or fallback


def stable_id(prefix: str, *parts: object) -> str:
    text = "\n".join(safe_text(part, max_len=8000) for part in parts)
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]
    return f"{prefix}_{slugify(next((part for part in parts if safe_text(part)), prefix))}_{digest}"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def split_values(value: object) -> list[str]:
    text = safe_text(value)
    if not text:
        return []
    return [part.strip() for part in re.split(r"\s*\|\s*|\s*;\s*", text) if part.strip()]


def title_key(value: object) -> str:
    return slugify(value)


def lead_key(row: dict[str, str]) -> str:
    title = title_key(row.get("name"))
    if title:
        return f"title:{title}"
    for field in ["landing_url", "source_key"]:
        value = safe_text(row.get(field))
        if value:
            return f"{field}:{value.lower()}"
    return stable_id("lead_key", row.get("name"), row.get("landing_url"), row.get("source_key"))


def root_table_keys() -> set[str]:
    if not ROOT_TABLE.exists():
        return set()
    df = pd.read_csv(ROOT_TABLE, sep="\t", dtype=str, keep_default_na=False)
    keys: set[str] = set()
    for row in df.to_dict(orient="records"):
        keys.add(lead_key(row))
        for url in split_values(row.get("landing_url")):
            keys.add(f"landing_url:{url.lower()}")
        for source_key in split_values(row.get("source_key")):
            keys.add(f"source_key:{source_key.lower()}")
    return keys


def decision_keys() -> set[str]:
    keys: set[str] = set()
    for path in sorted(OUT_DIR.glob(DECISION_GLOB)):
        payload = json.loads(path.read_text(encoding="utf-8"))
        for item in payload.get("decisions", []):
            key = safe_text(item.get("lead_key") or item.get("review_id"))
            if key:
                keys.add(key)
    return keys


def manifest_leads() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for path in sorted(SEARCH_DIR.glob(SEARCH_GLOB)):
        payload = json.loads(path.read_text(encoding="utf-8"))
        for bucket in ["candidates", "routed_or_rejected_leads"]:
            for item in payload.get(bucket, []):
                if not isinstance(item, dict):
                    continue
                row = {key: safe_text(value) for key, value in item.items()}
                row["manifest_path"] = str(path.relative_to(ROOT))
                row["manifest_bucket"] = bucket
                row["lead_key"] = lead_key(row)
                row["review_id"] = stable_id(
                    "codex_review",
                    row.get("lead_key"),
                    row.get("record_kind"),
                    row.get("landing_url"),
                    row.get("source_key"),
                )
                rows.append(row)
    deduped: dict[str, dict[str, str]] = {}
    for row in rows:
        key = row["lead_key"]
        existing = deduped.get(key)
        if not existing:
            deduped[key] = row
            continue
        for field in ["manifest_path", "manifest_bucket", "discovery_source", "source_key", "landing_url"]:
            values = []
            for value in split_values(existing.get(field)) + split_values(row.get(field)):
                if value not in values:
                    values.append(value)
            existing[field] = " | ".join(values)
    return list(deduped.values())


def should_review(row: dict[str, str], target_keys: set[str], reviewed: set[str]) -> tuple[bool, str]:
    if row["lead_key"] in reviewed or row["review_id"] in reviewed:
        return False, "already_codex_reviewed"
    if row.get("record_kind") in ROOT_RECORD_KINDS:
        if row.get("inventory_status") in ROOT_REVIEW_STATUSES:
            return True, "needs_root_candidate_review"
        return False, "already_root_candidate"
    if row["lead_key"] in target_keys:
        return False, "already_in_root_target"
    if row.get("inventory_status") == "rejected_irrelevant_search_hit":
        return False, "deterministically_rejected"
    if row.get("record_kind") not in REVIEW_RECORD_KINDS:
        return False, "not_codex_review_kind"
    return True, "needs_codex_review"


def priority(row: dict[str, str]) -> tuple[int, str]:
    status = row.get("inventory_status")
    kind = row.get("record_kind")
    if kind in ROOT_RECORD_KINDS:
        rank = 1
    elif kind == "candidate_result_table":
        rank = 8
    elif kind == "candidate_bibliographic_paper":
        rank = 10
    elif kind == "candidate_context_or_methods_paper":
        rank = 20
    elif kind == "candidate_individual_paper_or_package":
        rank = 30
    else:
        rank = 99
    if status == "needs_triage_search_lead":
        rank -= 2
    return rank, row.get("name", "").lower()


def prompt_text(batch_rows: list[dict[str, str]]) -> str:
    lines = [
        "You are reviewing Figure 1 search leads for a provenance pipeline.",
        "Classify each lead. Do not assume search terms make it relevant.",
        "",
        "Allowed decisions:",
        "- keep_in_corpora_and_databases",
        "- promote_to_corpora_and_databases",
        "- route_to_individual_replication_paper_worklist",
        "- keep_as_context_source",
        "- reject_irrelevant",
        "- needs_more_evidence",
        "",
        "Figure 1 wants sources that can expose original/replication or follow-up pairs, ideally multi-row corpora, databases, repository packages, or source tables.",
        "Return JSON with a decisions array. Each decision needs review_id, lead_key, decision, confidence, reason, and next_action.",
        "",
        "Leads:",
    ]
    for i, row in enumerate(batch_rows, start=1):
        lines.extend(
            [
                f"{i}. review_id: {row['review_id']}",
                f"   lead_key: {row['lead_key']}",
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
    return "\n".join(lines)


def write_json(path: Path, payload: dict[str, Any], replace: bool) -> bool:
    if path.exists() and not replace:
        print(f"Skipped {path.relative_to(ROOT)} because it exists. Use --replace to rebuild.")
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    print(f"Wrote {path.relative_to(ROOT)}")
    return True


def write_text(path: Path, content: str, replace: bool) -> bool:
    if path.exists() and not replace:
        print(f"Skipped {path.relative_to(ROOT)} because it exists. Use --replace to rebuild.")
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    print(f"Wrote {path.relative_to(ROOT)}")
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--batch-size", type=int, default=20)
    parser.add_argument("--batch-id", default="batch001")
    parser.add_argument("--replace", action="store_true")
    args = parser.parse_args()
    replace = args.replace or os.environ.get("REPLACE_SEARCH_TARGETS") == "1"

    target_keys = root_table_keys()
    reviewed = decision_keys()
    leads = manifest_leads()
    queue_rows: list[dict[str, str]] = []
    skip_counts: dict[str, int] = {}
    for row in leads:
        keep, reason = should_review(row, target_keys, reviewed)
        row["triage_queue_status"] = reason
        if keep:
            queue_rows.append(row)
        else:
            skip_counts[reason] = skip_counts.get(reason, 0) + 1
    queue_rows.sort(key=priority)

    queue_payload = {
        "created_at": utc_now(),
        "source_glob": str((SEARCH_DIR / SEARCH_GLOB).relative_to(ROOT)),
        "root_target": str(ROOT_TABLE.relative_to(ROOT)),
        "total_manifest_leads": len(leads),
        "needs_codex_review_count": len(queue_rows),
        "skip_counts": skip_counts,
        "queue": queue_rows,
    }
    write_json(QUEUE_TARGET, queue_payload, replace=True)

    batch_rows = queue_rows[: max(args.batch_size, 0)]
    batch_target = OUT_DIR / f"codextriage-{args.batch_id}-figure1-search-leads.json"
    batch_payload = {
        "created_at": utc_now(),
        "batch_id": args.batch_id,
        "batch_size": len(batch_rows),
        "remaining_after_batch": max(len(queue_rows) - len(batch_rows), 0),
        "input_queue": str(QUEUE_TARGET.relative_to(ROOT)),
        "review_instructions": {
            "allowed_decisions": [
                "keep_in_corpora_and_databases",
                "promote_to_corpora_and_databases",
                "route_to_individual_replication_paper_worklist",
                "keep_as_context_source",
                "reject_irrelevant",
                "needs_more_evidence",
            ],
            "required_fields": ["review_id", "lead_key", "decision", "confidence", "reason", "next_action"],
        },
        "prompt": prompt_text(batch_rows),
        "leads": batch_rows,
    }
    write_json(batch_target, batch_payload, replace=replace)
    prompt_target = OUT_DIR / f"codextriage-{args.batch_id}-figure1-search-leads-prompt.md"
    prompt_body = "\n".join(
        [
            "# Figure 1 Search Lead Triage Prompt",
            "",
            "Copy/paste the prompt below into GPT/Codex, then save the returned JSON as:",
            "",
            f"`steps/triage/figure1/codextriage-decisions-figure1-{args.batch_id}.json`",
            "",
            "```text",
            batch_payload["prompt"],
            "```",
            "",
        ]
    )
    write_text(prompt_target, prompt_body, replace=replace)
    print(
        f"Queue: {len(queue_rows)} needs Codex review; "
        f"batch {args.batch_id}: {len(batch_rows)}; skips: {skip_counts}"
    )


if __name__ == "__main__":
    main()
