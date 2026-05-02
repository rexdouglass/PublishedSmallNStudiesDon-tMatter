#!/usr/bin/env python3
"""Build machine-readable Codex decisions for Figure 1 result-artifact cues.

This is not an LLM transcript. It is a deterministic consolidation pass over
the artifacts that automation has already mirrored/sampled. It answers:

- Which Codex follow-up rows already yielded extracted corpus-result rows?
- Which rows have local artifacts but need source-specific mapping/parser work?
- Which rows are low-value local artifacts for generic Figure 1 parsing?
- Which provider/direct repair rows are exhausted and should move to GPT/user?
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter, defaultdict
from datetime import datetime
import math
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


def parser_queue_paths(plot_label: str) -> list[Path]:
    roots = [
        ROOT / "steps" / "source_inventory" / plot_label / "parser_queue",
        ROOT / "steps" / "source_inventory" / plot_label / "result_artifact_acquisition",
    ]
    paths: list[Path] = []
    for root in roots:
        paths.extend(root.glob("**/source-artifact-parser-candidate-queue.tsv"))
    return sorted(set(paths))


def repair_attempt_paths(plot_label: str) -> list[Path]:
    root = ROOT / "steps" / "source_inventory" / plot_label / "result_artifact_acquisition"
    return sorted(root.glob("repair/*-attempts.tsv"))


def source_catalog_rows(plot_label: str) -> list[dict[str, str]]:
    catalog_path = ROOT / "data" / "derived" / "effect_inflation_dataset" / f"plot{plot_label.removeprefix('figure')}_replication_source_catalog.csv"
    if not catalog_path.exists():
        return []
    with catalog_path.open("r", encoding="utf-8", newline="") as handle:
        return [{key: clean(value) for key, value in row.items()} for row in csv.DictReader(handle)]


def extracted_artifact_ids(plot_label: str) -> set[str]:
    output_root = ROOT / "steps" / "corpus_results" / plot_label
    rows: list[dict[str, str]] = []
    for table_path in sorted(output_root.glob("**/corpus-result-tables-proposal.tsv")):
        rows.extend(read_tsv(table_path))
    ids: set[str] = set()
    for row in rows:
        for field in ["source_artifact_id", "source_artifact_ids", "artifact_id", "primary_source_artifact_id"]:
            if row.get(field):
                ids.update(part.strip() for part in re.split(r"\s*\|\s*", row[field]) if part.strip())
    return ids


def group_by(rows: list[dict[str, str]], field: str) -> dict[str, list[dict[str, str]]]:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[row.get(field, "")].append(row)
    return grouped


def join_values(rows: list[dict[str, str]], field: str, limit: int = 12) -> str:
    values = []
    seen = set()
    for row in rows:
        value = row.get(field, "")
        if value and value not in seen:
            seen.add(value)
            values.append(value)
        if len(values) >= limit:
            break
    return " | ".join(values)


def path_parts(*texts: str) -> list[Path]:
    paths: list[Path] = []
    seen: set[Path] = set()
    for text in texts:
        for part in re.split(r"\s*\|\s*", clean(text, 100000)):
            if not part:
                continue
            path = resolve_path(part)
            if path.exists() and path not in seen:
                seen.add(path)
                paths.append(path)
    return paths


def local_evidence_paths(followup: dict[str, str], parser_rows: list[dict[str, str]]) -> list[Path]:
    paths = path_parts(
        followup.get("selected_local_paths", ""),
        followup.get("existing_local_paths", ""),
        followup.get("landing_url", ""),
        followup.get("raw_url", ""),
    )
    for row in parser_rows:
        paths.extend(path_parts(row.get("mirror_local_path", ""), row.get("sample_path", "")))
    seen: set[Path] = set()
    unique: list[Path] = []
    for path in paths:
        resolved = path.resolve()
        if resolved not in seen:
            seen.add(resolved)
            unique.append(path)
    return unique


def primary_local_evidence_paths(followup: dict[str, str], parser_rows: list[dict[str, str]]) -> list[Path]:
    paths = path_parts(
        followup.get("selected_local_paths", ""),
        followup.get("existing_local_paths", ""),
        followup.get("landing_url", ""),
        followup.get("raw_url", ""),
    )
    for row in parser_rows:
        paths.extend(path_parts(row.get("mirror_local_path", "")))
    seen: set[Path] = set()
    unique: list[Path] = []
    for path in paths:
        resolved = path.resolve()
        if resolved not in seen:
            seen.add(resolved)
            unique.append(path)
    return unique


def same_or_nested(left: Path, right: Path) -> bool:
    try:
        left_resolved = left.resolve()
        right_resolved = right.resolve()
    except OSError:
        left_resolved = left
        right_resolved = right
    return (
        left_resolved == right_resolved
        or right_resolved in left_resolved.parents
        or left_resolved in right_resolved.parents
    )


def catalog_matches(
    followup: dict[str, str],
    parser_rows: list[dict[str, str]],
    catalog_rows: list[dict[str, str]],
) -> list[dict[str, str]]:
    evidence_paths = local_evidence_paths(followup, parser_rows)
    matches: list[dict[str, str]] = []
    seen: set[str] = set()
    for catalog_row in catalog_rows:
        candidate_paths: list[Path] = []
        for field in ["raw_file", "staged_paths", "promoted_paths", "raw_dirs"]:
            candidate_paths.extend(path_parts(catalog_row.get(field, "")))
        path_hit = any(
            same_or_nested(evidence_path, candidate_path)
            for evidence_path in evidence_paths
            for candidate_path in candidate_paths
        )
        name_tokens: list[str] = []
        for field in [
            "source_dataset",
            "project",
            "lead_id",
            "display_label",
            "linked_projects",
            "linked_source_datasets",
            "alias_handles",
        ]:
            name_tokens.extend(part.strip() for part in re.split(r"\s*\|\s*", catalog_row.get(field, "")) if part.strip())
        haystack = " ".join(
            [
                followup.get("corpus_database_id", ""),
                followup.get("name", ""),
                join_values(parser_rows, "file_name"),
            ]
        ).lower()
        name_hit = any(token and token.lower() in haystack for token in name_tokens)
        if not (path_hit or name_hit):
            continue
        key = catalog_row.get("canonical_source_id") or catalog_row.get("source_handle") or json.dumps(catalog_row, sort_keys=True)
        if key in seen:
            continue
        seen.add(key)
        matches.append(catalog_row)
    return matches


def catalog_basis(matches: list[dict[str, str]]) -> str:
    parts = []
    for row in matches[:6]:
        parts.append(
            (
                f"{row.get('source_dataset') or row.get('project')}: "
                f"integrated_in_build={row.get('integrated_in_build')}; "
                f"terminal_status={row.get('terminal_status')}; "
                f"classification={row.get('classification')}; "
                f"live_pair_rows={row.get('live_pair_rows')}; "
                f"catalog_usable_pair_rows={row.get('catalog_usable_pair_rows')}; "
                f"notes={row.get('source_catalog_notes') or row.get('notes')}"
            )
        )
    return " | ".join(parts)


def stage_info(*texts: str) -> dict[str, str]:
    for path in path_parts(*texts):
        if not path.name.endswith("__stage.csv"):
            continue
        rows = read_tsv(path) if path.suffix == ".tsv" else []
        if not rows:
            with path.open("r", encoding="utf-8", newline="") as handle:
                rows = [{key: clean(value) for key, value in row.items()} for row in csv.DictReader(handle)]
        if rows:
            row = rows[0]
            if "promotion_decision" in row or "analytic_status" in row:
                return {
                    "stage_path": repo_path(path),
                    "default_action": row.get("promotion_decision", "stage_table"),
                    "expected_rows": str(len(rows)),
                    "promotion_blocker": row.get("analytic_status", "") or row.get("promotion_decision", ""),
                    "notes": row.get("notes", ""),
                }
            return {
                "stage_path": repo_path(path),
                "default_action": row.get("default_action", ""),
                "expected_rows": row.get("expected_rows", ""),
                "promotion_blocker": row.get("promotion_blocker", ""),
                "notes": row.get("notes", ""),
            }
    return {}


def is_tracker_only(followup: dict[str, str], parser_rows: list[dict[str, str]]) -> bool:
    paths = path_parts(
        followup.get("selected_local_paths", ""),
        followup.get("existing_local_paths", ""),
        followup.get("landing_url", ""),
        followup.get("raw_url", ""),
    )
    if paths and all(repo_path(path) == "reports/corpus_suggestion_tracker.md" for path in paths):
        return True
    if parser_rows and all(row.get("mirror_local_path") == "reports/corpus_suggestion_tracker.md" for row in parser_rows):
        return True
    return False


def is_landing_snapshot_only(followup: dict[str, str], parser_rows: list[dict[str, str]]) -> bool:
    paths = primary_local_evidence_paths(followup, parser_rows)
    if not paths:
        return False
    landing_root = ROOT / "steps" / "source_inventory" / followup.get("plot_label", "figure1") / "result_artifact_acquisition" / "landing_snapshots"
    return all(landing_root in path.resolve().parents for path in paths if path.exists())


def is_feature_matrix_artifact(followup: dict[str, str], parser_rows: list[dict[str, str]]) -> bool:
    text = " ".join(
        [
            followup.get("name", ""),
            join_values(parser_rows, "file_name", limit=30),
            join_values(parser_rows, "columns_preview", limit=10),
        ]
    ).lower()
    return "document term and feature matrices" in text or "cats_" in text or "feature matrix" in text


def is_method_workshop_context(followup: dict[str, str], parser_rows: list[dict[str, str]]) -> bool:
    text = " ".join(
        [
            followup.get("name", ""),
            join_values(parser_rows, "file_name", limit=30),
        ]
    ).lower()
    return "workshop" in text and any(token in text for token in ["expectedpower", "power worksheet", "power_workshop", "slides"])


def is_individual_replication_report_context(followup: dict[str, str], parser_rows: list[dict[str, str]]) -> bool:
    name = followup.get("name", "").lower()
    file_text = join_values(parser_rows, "file_name", limit=30).lower()
    return (
        name.startswith("rp:p replication of")
        or name.startswith("replication study:")
        or (" replication report" in file_text and not any(row.get("parser_priority") == "high" for row in parser_rows))
    )


def is_project_publication_context(followup: dict[str, str], parser_rows: list[dict[str, str]]) -> bool:
    name = followup.get("name", "").lower()
    file_text = join_values(parser_rows, "file_name", limit=30).lower()
    return "many labs" in name and "replication project" in name and any(token in file_text for token in ["manuscript", "supplement"])


def repair_attempt_status(parent_id: str, attempts_by_parent: dict[str, list[dict[str, str]]]) -> str:
    rows = attempts_by_parent.get(parent_id, [])
    if not rows:
        return ""
    return " | ".join(f"{row.get('strategy')}:{row.get('status')}:{row.get('detail')}" for row in rows[:8])


def decide(
    followup: dict[str, str],
    parser_rows: list[dict[str, str]],
    extracted_ids: set[str],
    attempts_by_parent: dict[str, list[dict[str, str]]],
    catalog_rows: list[dict[str, str]],
) -> dict[str, str]:
    track = followup.get("followup_track", "")
    parent_id = followup.get("corpus_database_id", "")
    staged = stage_info(followup.get("selected_local_paths", ""), followup.get("existing_local_paths", ""))
    blocker = staged.get("promotion_blocker", "")
    sampled_rows = [row for row in parser_rows if row.get("sample_status") == "sampled"]
    extracted_rows = [row for row in parser_rows if row.get("artifact_id") in extracted_ids]
    high_rows = [row for row in parser_rows if row.get("parser_priority") == "high"]
    medium_rows = [row for row in parser_rows if row.get("parser_priority") == "medium"]
    inspect_rows = [
        row
        for row in parser_rows
        if row.get("recommended_next_stage") in {"inspect_sample_for_result_fields", "inspect_code_or_text_for_generated_tables"}
    ]
    low_deprioritized = parser_rows and all(
        row.get("recommended_next_stage") in {"deprioritize_for_figure1_parsing", "inventory_metadata_and_links", "repair_or_manual_inventory"}
        for row in parser_rows
    )
    catalog_hit_rows = catalog_matches(followup, parser_rows, catalog_rows)
    integrated_catalog_rows = [
        row
        for row in catalog_hit_rows
        if row.get("integrated_in_build") == "True"
        and (row.get("live_pair_rows", "0") not in {"", "0"} or row.get("catalog_usable_pair_rows", "0") not in {"", "0"})
    ]
    catalog_crosscheck_rows = [
        row
        for row in catalog_hit_rows
        if "catalog_cross_check_only" in row.get("catalog_role_codes", "")
        or "cross-check" in row.get("classification", "").lower()
        or "sidecar" in row.get("classification", "").lower()
        or "not a pair table" in (row.get("source_catalog_notes", "") + " " + row.get("notes", "")).lower()
    ]

    if extracted_rows:
        decision = "already_extracted_corpus_result_rows"
        confidence = "high"
        action = "Use the existing corpus-results proposal; next work is mapping corpus-native rows to paper/result identities."
        assign_after_codex = "none"
        gpt_needed = "no"
        basis = "At least one parser-ready artifact for this source family has already produced CORPUS_RESULTS-shaped rows."
        selected = extracted_rows
    elif integrated_catalog_rows:
        decision = "already_integrated_live_pair_source"
        confidence = "high"
        action = "Do not re-review this local artifact as a new result source; use the existing live/catalog source row and preserve this artifact as audit context."
        assign_after_codex = "none"
        gpt_needed = "no"
        basis = "Matched existing plot source catalog integrated source. " + catalog_basis(integrated_catalog_rows)
        selected = parser_rows[:8]
    elif high_rows:
        decision = "parser_ready_table_candidate"
        confidence = "high"
        action = "Run corpus-result extraction on these high-priority parser-ready tables or inspect why extraction skipped them."
        assign_after_codex = "codex"
        gpt_needed = "no"
        basis = "High parser-priority table/workbook artifact with pair/effect/N/identity field signatures."
        selected = high_rows
    elif is_tracker_only(followup, parser_rows):
        decision = "tracker_context_not_result_artifact"
        confidence = "high"
        action = "Do not spend parser/GPT time on the tracker markdown row; resolve through the named concrete corpus/source artifacts instead."
        assign_after_codex = "none"
        gpt_needed = "no"
        basis = "The only local object is reports/corpus_suggestion_tracker.md, which is a prose tracker/context file, not a result-bearing artifact."
        selected = parser_rows[:4]
    elif is_landing_snapshot_only(followup, parser_rows):
        decision = "landing_snapshot_context_not_result_artifact"
        confidence = "high"
        action = "Keep the landing snapshot as acquisition/context evidence; do not parse it as the corpus result catalog."
        assign_after_codex = "none"
        gpt_needed = "no"
        basis = "All matched local evidence paths are landing.html snapshots under result_artifact_acquisition/landing_snapshots, not source result tables."
        selected = parser_rows[:4]
    elif is_feature_matrix_artifact(followup, parser_rows):
        decision = "feature_matrix_not_result_artifact"
        confidence = "high"
        action = "Keep as auxiliary text/feature-matrix data; do not parse as a Figure 1 original-replication result catalog."
        assign_after_codex = "none"
        gpt_needed = "no"
        basis = "The matched local artifacts are document-term/feature matrix files, not corpus result rows with original/replication effect and N fields."
        selected = parser_rows[:8]
    elif is_method_workshop_context(followup, parser_rows):
        decision = "method_workshop_context_not_result_artifact"
        confidence = "high"
        action = "Keep as methods/training context; do not parse as a Figure 1 corpus result catalog."
        assign_after_codex = "none"
        gpt_needed = "no"
        basis = "The matched local artifacts are workshop power/expected-effect materials, not result-bearing source-family tables."
        selected = parser_rows[:8]
    elif is_individual_replication_report_context(followup, parser_rows):
        decision = "individual_replication_report_context"
        confidence = "high"
        action = "Route, if needed, through the individual-paper worklist; do not treat as a reusable corpus result catalog."
        assign_after_codex = "none"
        gpt_needed = "no"
        basis = "The local artifacts are an individual replication report or paper-level replication study, not a corpus/database result table."
        selected = parser_rows[:8]
    elif is_project_publication_context(followup, parser_rows):
        decision = "project_publication_context_not_result_artifact"
        confidence = "high"
        action = "Keep the paper/supplement as source-family context; use the already mirrored tabular corpus artifacts for result extraction."
        assign_after_codex = "none"
        gpt_needed = "no"
        basis = "The local artifacts are a project manuscript/supplement, not the machine-readable corpus result table."
        selected = parser_rows[:8]
    elif catalog_crosscheck_rows:
        decision = "cataloged_crosscheck_or_sidecar"
        confidence = "high"
        action = "Keep this artifact as a cataloged cross-check, sidecar, or auxiliary source; do not send to GPT or generic result extraction unless the figure definition changes."
        assign_after_codex = "none"
        gpt_needed = "no"
        basis = "Matched existing plot source catalog cross-check/sidecar finding. " + catalog_basis(catalog_crosscheck_rows)
        selected = parser_rows[:8]
    elif staged and any(
        token in blocker
        for token in [
            "source_not_pair_buildable",
            "not_original_replication_pair_table",
            "original_side_missing",
            "metric_not_on_shared_d_axis",
            "missing_machine_readable_pair_results",
            "replication_payload_missing",
            "non_d_metric",
            "stage_native_metric",
            "native_",
            "effect_conversion_policy_missing",
        ]
    ):
        decision = "staged_local_source_not_ready_for_figure1"
        confidence = "medium"
        action = "Keep staged/local files as provenance context; do not promote to corpus-result extraction until the blocker is explicitly resolved."
        assign_after_codex = "none"
        gpt_needed = "no"
        basis = (
            f"Existing staged decision at {staged.get('stage_path')} has "
            f"default_action={staged.get('default_action')}; expected_rows={staged.get('expected_rows')}; "
            f"promotion_blocker={blocker}; notes={staged.get('notes')[:500]}"
        )
        selected = parser_rows[:8]
    elif medium_rows or inspect_rows:
        decision = "local_source_specific_mapping_needed"
        confidence = "medium"
        action = "Inspect local samples/files and write a source-specific mapping or parser decision; generic parser routing is not enough."
        assign_after_codex = "codex"
        gpt_needed = "no"
        basis = "Local sampled artifacts have some Figure 1 signals but do not pass the generic result-table gate."
        selected = medium_rows or inspect_rows
    elif low_deprioritized:
        decision = "local_artifacts_not_generic_result_tables"
        confidence = "medium"
        action = "Keep local artifacts as provenance/context; do not ask GPT unless a source-family decision later makes this source high-value."
        assign_after_codex = "none"
        gpt_needed = "no"
        basis = "Sampled/local artifacts exist, but parser routing found no strong result-table evidence."
        selected = parser_rows[:8]
    elif track in {"codex_provider_repair", "codex_direct_url_repair"}:
        decision = "deterministic_repair_exhausted"
        confidence = "medium"
        action = "Escalate to GPT external artifact resolution or later user/manual route if GPT cannot find a public object."
        assign_after_codex = "gpt"
        gpt_needed = "yes"
        basis = repair_attempt_status(parent_id, attempts_by_parent) or "Provider/direct retry did not yield a sampled local result artifact."
        selected = []
    elif track == "codex_local_mirror_identification":
        decision = "local_mirror_identification_still_needed"
        confidence = "medium"
        action = "Inspect the listed local mirror directory and identify the concrete result-bearing artifact member."
        assign_after_codex = "codex"
        gpt_needed = "no"
        basis = "Queue row says local mirror exists, but no sampled parser artifact was matched to this source family."
        selected = []
    else:
        decision = "codex_review_still_needed"
        confidence = "low"
        action = "Review this row manually inside Codex; current deterministic evidence is insufficient."
        assign_after_codex = "codex"
        gpt_needed = "no"
        basis = "No decisive parser, extraction, or repair evidence found."
        selected = parser_rows[:8]

    return {
        "followup_id": followup.get("followup_id", ""),
        "plot_label": followup.get("plot_label", ""),
        "corpus_database_id": parent_id,
        "name": followup.get("name", ""),
        "followup_track": track,
        "original_assigned_to": followup.get("assigned_to", ""),
        "decision": decision,
        "confidence": confidence,
        "gpt_needed": gpt_needed,
        "assign_after_codex": assign_after_codex,
        "selected_artifact_ids": join_values(selected, "artifact_id"),
        "selected_local_paths": join_values(selected, "mirror_local_path"),
        "selected_sample_paths": join_values(selected, "sample_path"),
        "parser_evidence_counts": (
            f"parser_rows={len(parser_rows)}; sampled={len(sampled_rows)}; "
            f"high={len(high_rows)}; medium={len(medium_rows)}; extracted={len(extracted_rows)}"
        ),
        "decision_basis": basis,
        "recommended_next_action": action,
        "landing_url": followup.get("landing_url", ""),
        "raw_url": followup.get("raw_url", ""),
        "existing_local_paths": followup.get("existing_local_paths", ""),
    }


def summary_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    for field in ["decision", "gpt_needed", "assign_after_codex", "followup_track", "confidence"]:
        for value, count in Counter(row.get(field, "") or "<blank>" for row in rows).most_common():
            out.append({"metric": field, "value": value, "count": str(count)})
    out.append({"metric": "total", "value": "codex_decision_rows", "count": str(len(rows))})
    return out


def gpt_item(row: dict[str, str]) -> dict[str, str]:
    return {
        "followup_id": row["followup_id"],
        "corpus_database_id": row["corpus_database_id"],
        "name": row["name"],
        "previous_codex_decision": row["decision"],
        "decision_basis": row["decision_basis"],
        "landing_url": row["landing_url"],
        "raw_url": row["raw_url"],
        "question": (
            "Codex deterministic provider/direct repair did not find a public local result artifact. "
            "Research whether this lead has a reusable Figure 1 result-bearing artifact "
            "(dataset, workbook, source-family table, supplement, repository, PDF/HTML table, or file inventory), "
            "or classify it as individual_paper_only, context_only, duplicate, reject_not_figure1, or no_public_artifact_found."
        ),
    }


def gpt_prompt(payload: dict[str, Any]) -> str:
    return f"""# Figure 1 Codex-Exhausted Result-Artifact Resolution: {payload['batch_id']}

Codex has already run deterministic provider/direct acquisition and mirror/sample attempts for these rows. Do not repeat generic search blindly. For each item, identify a concrete reusable result-bearing artifact if one exists, or explain why the public route appears unavailable.

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


def write_gpt_handoff(output_root: Path, rows: list[dict[str, str]], batch_size: int, replace: bool) -> None:
    gpt_rows = [row for row in rows if row.get("gpt_needed") == "yes"]
    gpt_root = output_root / "codex_exhausted_gpt"
    total = math.ceil(len(gpt_rows) / batch_size) if gpt_rows else 0
    for batch_num in range(total):
        batch = gpt_rows[batch_num * batch_size : (batch_num + 1) * batch_size]
        batch_id = f"batch{batch_num + 1:03d}"
        payload = {
            "batch_id": batch_id,
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "task": "figure1_codex_exhausted_result_artifact_resolution",
            "items": [gpt_item(row) for row in batch],
        }
        json_path = gpt_root / f"figure1-result-artifact-codex-exhausted-gpt-{batch_id}.json"
        prompt_path = gpt_root / f"figure1-result-artifact-codex-exhausted-gpt-{batch_id}-prompt.md"
        write_json(json_path, payload, replace)
        if prompt_path.exists() and not replace:
            print(f"Skipped {repo_path(prompt_path)} because it exists. Use --replace to rebuild.")
        else:
            prompt_path.parent.mkdir(parents=True, exist_ok=True)
            prompt_path.write_text(gpt_prompt(payload), encoding="utf-8")
            print(f"Wrote {repo_path(prompt_path)}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plot-label", default="figure1")
    parser.add_argument("--followup", type=Path)
    parser.add_argument("--output-root", type=Path)
    parser.add_argument("--gpt-batch-size", type=int, default=30)
    parser.add_argument("--replace", action="store_true")
    args = parser.parse_args()

    root = ROOT / "steps" / "source_inventory" / args.plot_label / "result_artifact_acquisition"
    followup_path = resolve_path(args.followup) if args.followup else root / "followup" / "codex" / f"{args.plot_label}-result-artifact-codex-queue.tsv"
    output_root = resolve_path(args.output_root) if args.output_root else root / "followup" / "codex"

    followup_rows = read_tsv(followup_path)
    parser_rows: list[dict[str, str]] = []
    parser_inputs = parser_queue_paths(args.plot_label)
    for path in parser_inputs:
        parser_rows.extend(read_tsv(path))
    parser_by_parent = group_by(parser_rows, "parent_corpus_database_id")

    attempts: list[dict[str, str]] = []
    attempt_inputs = repair_attempt_paths(args.plot_label)
    for path in attempt_inputs:
        attempts.extend(read_tsv(path))
    attempts_by_parent = group_by(attempts, "corpus_database_id")
    extracted_ids = extracted_artifact_ids(args.plot_label)
    catalog_rows = source_catalog_rows(args.plot_label)

    decisions = [
        decide(row, parser_by_parent.get(row.get("corpus_database_id", ""), []), extracted_ids, attempts_by_parent, catalog_rows)
        for row in followup_rows
    ]
    columns = [
        "followup_id",
        "plot_label",
        "corpus_database_id",
        "name",
        "followup_track",
        "original_assigned_to",
        "decision",
        "confidence",
        "gpt_needed",
        "assign_after_codex",
        "selected_artifact_ids",
        "selected_local_paths",
        "selected_sample_paths",
        "parser_evidence_counts",
        "decision_basis",
        "recommended_next_action",
        "landing_url",
        "raw_url",
        "existing_local_paths",
    ]
    prefix = f"{args.plot_label}-result-artifact-codex-decisions"
    write_tsv(output_root / f"{prefix}.tsv", decisions, columns, args.replace)
    write_tsv(output_root / f"{prefix}-summary.tsv", summary_rows(decisions), ["metric", "value", "count"], args.replace)
    write_tsv(
        output_root / f"{args.plot_label}-result-artifact-codex-active-queue.tsv",
        [row for row in decisions if row.get("assign_after_codex") == "codex"],
        columns,
        args.replace,
    )
    write_tsv(
        output_root / f"{args.plot_label}-result-artifact-codex-gpt-queue.tsv",
        [row for row in decisions if row.get("gpt_needed") == "yes"],
        columns,
        args.replace,
    )
    write_json(
        output_root / f"{prefix}.json",
        {
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "followup_input": repo_path(followup_path),
            "parser_inputs": [repo_path(path) for path in parser_inputs],
            "repair_attempt_inputs": [repo_path(path) for path in attempt_inputs],
            "source_catalog_rows": len(catalog_rows),
            "extracted_artifact_count": len(extracted_ids),
            "decision_count": len(decisions),
            "records": decisions,
        },
        args.replace,
    )
    write_gpt_handoff(output_root, decisions, args.gpt_batch_size, args.replace)
    counts = Counter(row["decision"] for row in decisions)
    print(
        f"{args.plot_label} Codex artifact decisions: "
        f"rows={len(decisions)}; "
        + "; ".join(f"{key}={value}" for key, value in counts.most_common())
    )


if __name__ == "__main__":
    main()
