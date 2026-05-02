#!/usr/bin/env python3
"""Build Codex/GPT/user follow-up cues for unresolved result artifacts.

The acquisition DAG should spend deterministic automation first. This script
looks at the plot acquisition queue plus mirror/sample status files and routes
only the unresolved tail to bounded review tracks.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]


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
    path = Path(value)
    return path if path.is_absolute() else ROOT / path


def stable_id(prefix: str, *parts: object) -> str:
    import hashlib

    text = "\n".join(clean(part, 20000) for part in parts if clean(part))
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]
    return f"{prefix}_{digest}"


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


def mirror_status_paths(plot_label: str) -> list[Path]:
    root = ROOT / "steps" / "source_inventory" / plot_label / "result_artifact_acquisition"
    return sorted(root.glob("**/source-artifact-mirror-sample-status.tsv"))


def on_disk_parent_ids(status_rows: list[dict[str, str]]) -> set[str]:
    good = {"downloaded", "already_local", "component_metadata_recorded"}
    return {
        row["parent_corpus_database_id"]
        for row in status_rows
        if row.get("mirror_local_path") or row.get("mirror_status") in good
    }


def sampled_parent_ids(status_rows: list[dict[str, str]]) -> set[str]:
    return {row["parent_corpus_database_id"] for row in status_rows if row.get("sample_status") == "sampled"}


def manual_reason_by_id(manual_rows: list[dict[str, str]]) -> dict[str, str]:
    grouped: dict[str, list[str]] = {}
    for row in manual_rows:
        grouped.setdefault(row.get("corpus_database_id", ""), []).append(row.get("reason", ""))
    return {key: " | ".join(sorted(set(value for value in values if value))) for key, values in grouped.items()}


def route_followup(row: dict[str, str], *, on_disk: bool, sampled: bool, manual_reason: str) -> tuple[str, str, str, str]:
    state = row.get("result_artifact_acquisition_state", "")
    route = row.get("acquisition_route_type", "")
    host = row.get("host", "")
    if state == "local_mirror_needs_result_artifact_identification":
        return (
            "codex_local_mirror_identification",
            "codex",
            "Inspect the existing local mirror and identify which file, table, PDF, or archive member actually catalogs Figure 1 result rows.",
            "local mirror exists but result-bearing artifact is not identified",
        )
    if on_disk and sampled:
        return (
            "codex_parser_or_result_mapping",
            "codex",
            "Inspect sampled local artifacts and route result-bearing tables to parser/extraction or reject/deprioritize if they are not Figure 1 result catalogs.",
            "local sampled artifact exists but parser/result mapping may still be needed",
        )
    if route in {"osf_inventory_and_download", "dataverse_inventory_and_download", "figshare_record_file_download", "zenodo_record_file_download"}:
        return (
            "codex_provider_repair",
            "codex",
            "Repair provider inventory/download route: check component IDs, file APIs, alternate versions, stale URLs, branch names, or provider-specific access endpoints.",
            manual_reason or "provider route did not yield local result artifact",
        )
    if route in {"direct_download_or_api_snapshot", "repository_or_package_discovery"}:
        if host == "manual_tracker":
            return (
                "codex_local_tracker_resolution",
                "codex",
                "Resolve this manual-tracker lead against local raw/corpus_candidate directories and explicit source suggestions; add concrete artifact path or mark unresolved.",
                "manual tracker row points to prose tracker rather than concrete source bytes",
            )
        return (
            "codex_direct_url_repair",
            "codex",
            "Try direct URL variants, repository archive branch repair, DOI/provider redirects, and local mirror detection before escalating.",
            manual_reason or "direct route did not produce a local artifact",
        )
    if route == "article_pdf_supplement_or_data_availability_route":
        return (
            "gpt_article_supplement_data_hunt",
            "gpt",
            "Find the result-bearing artifact for this article/source family: supplement table, data/code repository, project page, PDF/HTML table, or reason none is public.",
            manual_reason or "article route still needs data/supplement/source-object research",
        )
    if route == "landing_page_inventory_or_manual_resolution":
        return (
            "gpt_landing_page_artifact_resolution",
            "gpt",
            "Inspect landing/source-family page and identify concrete downloadable artifacts, file inventories, result tables, or a reason it is not a reusable Figure 1 corpus.",
            manual_reason or "landing page needs source-object resolution",
        )
    return (
        "user_manual_or_policy_review",
        "user",
        "Manual browser/library/source-specific review is needed after Codex/GPT cannot identify a public route.",
        manual_reason or "unclassified unresolved route",
    )


def build_followup_rows(
    queue_rows: list[dict[str, str]],
    status_rows: list[dict[str, str]],
    manual_rows: list[dict[str, str]],
) -> list[dict[str, str]]:
    on_disk_ids = on_disk_parent_ids(status_rows)
    sampled_ids = sampled_parent_ids(status_rows)
    manual_reasons = manual_reason_by_id(manual_rows)
    out: list[dict[str, str]] = []
    for row in queue_rows:
        corpus_id = row.get("corpus_database_id", "")
        local_state = row.get("result_artifact_acquisition_state", "")
        existing_local = local_state in {"local_result_artifact_candidate_present", "local_mirror_needs_result_artifact_identification"}
        is_on_disk = existing_local or corpus_id in on_disk_ids
        is_sampled = existing_local or corpus_id in sampled_ids
        if local_state == "local_result_artifact_candidate_present" and corpus_id not in sampled_ids:
            continue
        if is_on_disk and local_state != "local_mirror_needs_result_artifact_identification" and corpus_id not in sampled_ids:
            continue
        if is_on_disk and is_sampled and local_state == "local_result_artifact_candidate_present":
            continue
        track, assigned_to, action, reason = route_followup(
            row,
            on_disk=is_on_disk,
            sampled=is_sampled,
            manual_reason=manual_reasons.get(corpus_id, ""),
        )
        out.append(
            {
                "followup_id": stable_id("result_artifact_followup", row.get("plot_label"), corpus_id, track),
                "plot_label": row.get("plot_label", ""),
                "corpus_database_id": corpus_id,
                "name": row.get("name", ""),
                "record_kind": row.get("record_kind", ""),
                "priority": row.get("priority", ""),
                "host": row.get("host", ""),
                "acquisition_route_type": row.get("acquisition_route_type", ""),
                "current_acquisition_state": local_state,
                "on_disk_after_automation": "yes" if is_on_disk else "no",
                "sampled_after_automation": "yes" if is_sampled else "no",
                "followup_track": track,
                "assigned_to": assigned_to,
                "reason": reason,
                "landing_url": row.get("landing_url", ""),
                "raw_url": row.get("raw_url", ""),
                "existing_local_paths": row.get("existing_local_paths", ""),
                "suggested_action": action,
                "gpt_question": gpt_question(row, track),
                "user_action": user_action(row, track),
                "notes": row.get("notes", ""),
            }
        )
    return sorted(out, key=lambda r: (assignee_rank(r["assigned_to"]), priority_rank(r["priority"]), r["followup_track"], r["name"]))


def assignee_rank(value: str) -> int:
    return {"codex": 0, "gpt": 1, "user": 2}.get(value, 9)


def priority_rank(value: str) -> int:
    return {"high": 0, "medium": 1, "lower": 2}.get(value, 9)


def gpt_question(row: dict[str, str], track: str) -> str:
    if not track.startswith("gpt_"):
        return ""
    return (
        "Does this lead have a reusable Figure 1 result-bearing source artifact "
        "(dataset/database/workbook/table/supplement/PDF table/repository file) that enumerates original-replication or follow-up result rows? "
        "Return concrete URLs/DOIs/file names and classify as corpus_database, individual_paper, context_only, duplicate, or reject."
    )


def user_action(row: dict[str, str], track: str) -> str:
    if track != "user_manual_or_policy_review":
        return ""
    return "Use browser/library/manual access only if GPT/Codex cannot find a public artifact; record route, rights basis, local path, and checksum."


def summary_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    for field in ["assigned_to", "followup_track", "priority", "acquisition_route_type", "on_disk_after_automation", "sampled_after_automation"]:
        for value, count in Counter(row.get(field, "") for row in rows).most_common():
            out.append({"metric": field, "value": value, "count": str(count)})
    out.append({"metric": "total", "value": "followup_rows", "count": str(len(rows))})
    return out


def gpt_item(row: dict[str, str]) -> dict[str, str]:
    return {
        "followup_id": row["followup_id"],
        "corpus_database_id": row["corpus_database_id"],
        "name": row["name"],
        "record_kind": row["record_kind"],
        "priority": row["priority"],
        "route": row["acquisition_route_type"],
        "host": row["host"],
        "landing_url": row["landing_url"],
        "raw_url": row["raw_url"],
        "question": row["gpt_question"],
        "reason": row["reason"],
    }


def write_gpt_batches(root: Path, gpt_rows: list[dict[str, str]], batch_size: int, replace: bool) -> None:
    gpt_root = root / "gpt"
    total = math.ceil(len(gpt_rows) / batch_size) if gpt_rows else 0
    for batch_num in range(total):
        batch = gpt_rows[batch_num * batch_size : (batch_num + 1) * batch_size]
        batch_id = f"batch{batch_num + 1:03d}"
        payload = {
            "batch_id": batch_id,
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "task": "figure1_result_artifact_resolution",
            "items": [gpt_item(row) for row in batch],
        }
        json_path = gpt_root / f"figure1-result-artifact-gpt-{batch_id}.json"
        prompt_path = gpt_root / f"figure1-result-artifact-gpt-{batch_id}-prompt.md"
        write_json(json_path, payload, replace)
        prompt = gpt_prompt(payload)
        if prompt_path.exists() and not replace:
            print(f"Skipped {repo_path(prompt_path)} because it exists. Use --replace to rebuild.")
        else:
            prompt_path.parent.mkdir(parents=True, exist_ok=True)
            prompt_path.write_text(prompt, encoding="utf-8")
            print(f"Wrote {repo_path(prompt_path)}")


def gpt_prompt(payload: dict[str, Any]) -> str:
    return f"""# Figure 1 Result-Artifact Resolution: {payload['batch_id']}

We are building a reproducible provenance pipeline for a plot of original-vs-replication/follow-up result pairs.

For each item below, research whether the lead has a reusable result-bearing artifact for Figure 1. A valid artifact can be a dataset, database export, workbook, CSV/TSV, code/data repository, supplement table, PDF/HTML table, API snapshot, or source-family file inventory that enumerates original-replication/follow-up result rows. Do not promote ordinary one-paper "replication package" material unless it actually reports an independent replication/follow-up result or contains a multi-row source-family table.

Return machine-readable JSON only with this shape:

```json
{{
  "batch_id": "{payload['batch_id']}",
  "decisions": [
    {{
      "followup_id": "...",
      "corpus_database_id": "...",
      "decision": "artifact_found | no_public_artifact_found | individual_paper_only | context_only | duplicate | reject_not_figure1 | needs_user_manual_access",
      "result_artifact_urls": ["..."],
      "result_artifact_file_names": ["..."],
      "source_family_url": "...",
      "publication_or_project_doi": "...",
      "classification_reason": "...",
      "recommended_next_action": "...",
      "confidence": "high | medium | low",
      "sources_checked": ["..."]
    }}
  ]
}}
```

Items:

```json
{json.dumps(payload["items"], indent=2, ensure_ascii=False)}
```
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plot-label", default="figure1")
    parser.add_argument("--queue", type=Path)
    parser.add_argument("--manual-tasks", type=Path)
    parser.add_argument("--status", action="append", default=[])
    parser.add_argument("--output-root", type=Path)
    parser.add_argument("--gpt-batch-size", type=int, default=30)
    parser.add_argument("--replace", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    root = ROOT / "steps" / "source_inventory" / args.plot_label / "result_artifact_acquisition"
    queue_path = resolve_path(args.queue) if args.queue else root / f"{args.plot_label}-result-artifact-acquisition-queue.tsv"
    manual_path = resolve_path(args.manual_tasks) if args.manual_tasks else root / f"{args.plot_label}-result-artifact-acquisition-manual-tasks.tsv"
    output_root = resolve_path(args.output_root) if args.output_root else root / "followup"
    status_paths = [resolve_path(path) for path in args.status] if args.status else mirror_status_paths(args.plot_label)
    queue_rows = read_tsv(queue_path)
    manual_rows = read_tsv(manual_path)
    status_rows: list[dict[str, str]] = []
    for path in status_paths:
        status_rows.extend(read_tsv(path))
    followup = build_followup_rows(queue_rows, status_rows, manual_rows)
    columns = [
        "followup_id",
        "plot_label",
        "corpus_database_id",
        "name",
        "record_kind",
        "priority",
        "host",
        "acquisition_route_type",
        "current_acquisition_state",
        "on_disk_after_automation",
        "sampled_after_automation",
        "followup_track",
        "assigned_to",
        "reason",
        "landing_url",
        "raw_url",
        "existing_local_paths",
        "suggested_action",
        "gpt_question",
        "user_action",
        "notes",
    ]
    write_tsv(output_root / f"{args.plot_label}-result-artifact-followup-queue.tsv", followup, columns, args.replace)
    write_json(
        output_root / f"{args.plot_label}-result-artifact-followup-queue.json",
        {
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "queue_input": repo_path(queue_path),
            "manual_tasks_input": repo_path(manual_path),
            "status_inputs": [repo_path(path) for path in status_paths],
            "followup_count": len(followup),
            "records": followup,
        },
        args.replace,
    )
    write_tsv(output_root / f"{args.plot_label}-result-artifact-followup-summary.tsv", summary_rows(followup), ["metric", "value", "count"], args.replace)
    write_tsv(output_root / "codex" / f"{args.plot_label}-result-artifact-codex-queue.tsv", [r for r in followup if r["assigned_to"] == "codex"], columns, args.replace)
    write_tsv(output_root / "user" / f"{args.plot_label}-result-artifact-user-queue.tsv", [r for r in followup if r["assigned_to"] == "user"], columns, args.replace)
    write_gpt_batches(output_root, [r for r in followup if r["assigned_to"] == "gpt"], args.gpt_batch_size, args.replace)
    counts = Counter(row["assigned_to"] for row in followup)
    print(
        "Follow-up cue rows: "
        f"total={len(followup)}; codex={counts.get('codex', 0)}; "
        f"gpt={counts.get('gpt', 0)}; user={counts.get('user', 0)}"
    )


if __name__ == "__main__":
    main()
