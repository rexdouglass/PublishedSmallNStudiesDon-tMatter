#!/usr/bin/env python3
"""Render the top-of-pipeline universe search plan from the graph registry."""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
import yaml


ROOT = Path(__file__).resolve().parents[1]
SPEC_PATH = ROOT / "PROVENANCE_PIPELINE_SINGLE_SOURCE_OF_TRUTH.yml"
SPEC_ROOT_KEY = "PROVENANCE_PIPELINE_SINGLE_SOURCE_OF_TRUTH"
OUT_TSV = ROOT / "data" / "derived" / "effect_inflation_dataset" / "provenance_search_plan.tsv"
REPORT_PATH = ROOT / "reports" / "provenance_universe_search_plan.md"


def load_spec() -> dict[str, Any]:
    with SPEC_PATH.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{SPEC_PATH} did not parse to a mapping")
    if SPEC_ROOT_KEY in data:
        spec = data[SPEC_ROOT_KEY]
        if not isinstance(spec, dict):
            raise ValueError(f"{SPEC_PATH}.{SPEC_ROOT_KEY} did not parse to a mapping")
        return spec
    return data


def id_map(spec: dict[str, Any], key: str) -> dict[str, dict[str, Any]]:
    items = spec.get(key, [])
    if not isinstance(items, list):
        raise ValueError(f"{key} must be a list")
    out: dict[str, dict[str, Any]] = {}
    duplicates: list[str] = []
    for item in items:
        if not isinstance(item, dict) or not item.get("id"):
            raise ValueError(f"{key} contains an item without id")
        item_id = str(item["id"])
        if item_id in out:
            duplicates.append(item_id)
        out[item_id] = item
    if duplicates:
        raise ValueError(f"{key} contains duplicate IDs: {', '.join(sorted(set(duplicates)))}")
    return out


def as_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value]
    return [str(value)]


def flat(value: Any) -> str:
    if isinstance(value, list):
        return " | ".join(flat(item) for item in value)
    return str(value or "").replace("\t", " ").replace("\n", " ").strip()


def artifact_status(path_text: str) -> str:
    path = ROOT / path_text
    if path.exists():
        if path.is_dir():
            try:
                child_count = sum(1 for _ in path.iterdir())
            except OSError:
                child_count = -1
            count_text = "unknown" if child_count < 0 else str(child_count)
            return f"present_dir({count_text})"
        return "present_file"
    return "missing"


def target_glob_status(pattern: str) -> tuple[int, str]:
    if not pattern:
        return 0, ""
    matches = sorted(path for path in ROOT.glob(pattern) if path.is_file())
    if matches:
        return len(matches), f"present_files({len(matches)})"
    return 0, "missing"


def artifact_summary(paths: list[str]) -> tuple[int, int, str]:
    statuses = []
    present = 0
    missing = 0
    for path in paths:
        status = artifact_status(path)
        if status.startswith("present"):
            present += 1
        else:
            missing += 1
        statuses.append(f"{status}:{path}")
    return present, missing, " | ".join(statuses)


def validate(spec: dict[str, Any]) -> list[str]:
    warnings: list[str] = []
    universes = id_map(spec, "plot_universes")
    tools = id_map(spec, "search_tools")
    lead_types = id_map(spec, "lead_types")
    search_statuses = set(spec.get("state_vocabularies", {}).get("search_lead_status", []))
    plans = spec.get("universe_search_plans", [])
    if not isinstance(plans, list) or not plans:
        raise ValueError("universe_search_plans must be a non-empty list")

    seen_plan_ids: set[str] = set()
    seen_track_ids: set[str] = set()
    for plan in plans:
        if not isinstance(plan, dict):
            raise ValueError("universe_search_plans contains a non-mapping item")
        plan_id = str(plan.get("id", ""))
        if not plan_id:
            raise ValueError("universe_search_plans contains an item without id")
        if plan_id in seen_plan_ids:
            raise ValueError(f"duplicate universe_search_plans id: {plan_id}")
        seen_plan_ids.add(plan_id)

        universe_id = plan.get("universe_id")
        if universe_id not in universes:
            raise ValueError(f"search plan {plan_id} references unknown universe {universe_id!r}")
        tracks = plan.get("search_tracks", [])
        if not isinstance(tracks, list) or not tracks:
            raise ValueError(f"search plan {plan_id} must contain search_tracks")
        for track in tracks:
            track_id = str(track.get("id", ""))
            if not track_id:
                raise ValueError(f"search plan {plan_id} has a track without id")
            if track_id in seen_track_ids:
                raise ValueError(f"duplicate search track id: {track_id}")
            seen_track_ids.add(track_id)
            lead_type = track.get("lead_type")
            if lead_type not in lead_types:
                raise ValueError(f"search track {track_id} references unknown lead_type {lead_type!r}")
            status = track.get("status")
            if search_statuses and status not in search_statuses:
                raise ValueError(f"search track {track_id} references unknown status {status!r}")
            unknown_tools = sorted(tool for tool in as_list(track.get("tools")) if tool not in tools)
            if unknown_tools:
                raise ValueError(f"search track {track_id} references unknown tools: {', '.join(unknown_tools)}")
            present, missing, _summary = artifact_summary(as_list(track.get("existing_artifacts")))
            if missing:
                warnings.append(f"search track {track_id} has {missing} missing seed artifact(s)")
            if not present and track.get("status") == "seeded_from_existing_artifact":
                warnings.append(f"search track {track_id} is seeded_from_existing_artifact but no seed artifacts are present")
    return warnings


def build_rows(spec: dict[str, Any]) -> list[dict[str, str]]:
    universe_by_id = id_map(spec, "plot_universes")
    rows: list[dict[str, str]] = []
    for plan in spec["universe_search_plans"]:
        universe = universe_by_id[plan["universe_id"]]
        minimum_fields = as_list(plan.get("minimum_lead_fields"))
        for track in plan["search_tracks"]:
            artifacts = as_list(track.get("existing_artifacts"))
            present, missing, status_text = artifact_summary(artifacts)
            target_file = flat(track.get("target_file", ""))
            target_glob = flat(track.get("target_glob", ""))
            if target_file:
                target_file_status = artifact_status(target_file)
                target_file_count = "1" if target_file_status.startswith("present") else "0"
            elif target_glob:
                target_count, target_file_status = target_glob_status(target_glob)
                target_file_count = str(target_count)
            else:
                target_file_status = ""
                target_file_count = "0"
            rows.append(
                {
                    "plan_id": flat(plan["id"]),
                    "universe_id": flat(plan["universe_id"]),
                    "universe_result_target_kind": flat(universe.get("result_target_kind", "")),
                    "plan_result_target_kind": flat(plan.get("result_target_kind", "")),
                    "search_direction": flat(plan.get("search_direction", "")),
                    "search_space_id": flat(track["id"]),
                    "search_query_family_id": f"{flat(track['id'])}_queries",
                    "track_id": flat(track["id"]),
                    "track_rank": flat(track.get("rank", "")),
                    "lead_type": flat(track.get("lead_type", "")),
                    "lead_status": flat(track.get("status", "")),
                    "search_tools": flat(track.get("tools", [])),
                    "seed_queries": flat(track.get("seed_queries", [])),
                    "existing_artifacts": flat(artifacts),
                    "existing_artifact_present_count": str(present),
                    "existing_artifact_missing_count": str(missing),
                    "existing_artifact_status": status_text,
                    "target_file": target_file,
                    "target_glob": target_glob,
                    "target_examples": flat(track.get("target_examples", [])),
                    "target_file_count": target_file_count,
                    "target_file_status": target_file_status,
                    "target_file_policy": flat(track.get("target_file_policy", "")),
                    "minimum_lead_fields": flat(minimum_fields),
                    "promotion_gate_to_result_target": flat(plan.get("promotion_gate_to_result_target", "")),
                    "accept_if": flat(track.get("accept_if", [])),
                    "reject_if": flat(track.get("reject_if", [])),
                    "stop_conditions": flat(track.get("stop_conditions", [])),
                    "outputs": flat(track.get("outputs", [])),
                    "plan_goal": flat(plan.get("goal", "")),
                }
            )
    return rows


def markdown_table(rows: list[dict[str, Any]], columns: list[tuple[str, str]]) -> list[str]:
    header = "| " + " | ".join(label for _, label in columns) + " |"
    sep = "| " + " | ".join("---" for _ in columns) + " |"
    lines = [header, sep]
    for row in rows:
        values = []
        for key, _label in columns:
            value = flat(row.get(key, ""))
            value = value.replace("|", "\\|")
            values.append(value)
        lines.append("| " + " | ".join(values) + " |")
    return lines


def render_report(spec: dict[str, Any], rows: list[dict[str, str]], warnings: list[str]) -> str:
    generated = datetime.now(timezone.utc).isoformat()
    status_counts = Counter(row["lead_status"] for row in rows)
    universe_counts = Counter(row["universe_id"] for row in rows)
    total_present = sum(int(row["existing_artifact_present_count"]) for row in rows)
    total_missing = sum(int(row["existing_artifact_missing_count"]) for row in rows)
    target_files_present = sum(int(row.get("target_file_count") or 0) for row in rows)
    target_tracks_missing = sum(
        1
        for row in rows
        if (row.get("target_file") or row.get("target_glob")) and int(row.get("target_file_count") or 0) == 0
    )

    lines: list[str] = [
        "# Provenance Universe Search Plan",
        "",
        f"- Generated: {generated}",
        f"- Spec: `{SPEC_PATH.relative_to(ROOT)}`",
        f"- Spec root: `{SPEC_ROOT_KEY}`",
        f"- TSV: `{OUT_TSV.relative_to(ROOT)}`",
        f"- Search tracks: {len(rows)}",
        f"- Present seed artifacts: {total_present}",
        f"- Missing seed artifacts: {total_missing}",
        f"- Present target files: {target_files_present}",
        f"- Target tracks with no files yet: {target_tracks_missing}",
        "",
        "This report is the top of the pipeline: plot universe, search space, search query family, search lead, then later result target. It makes the old hand-built search surface explicit before locating, obtaining, or verification strategies run.",
        "",
    ]
    if warnings:
        lines.extend(["## Warnings", ""])
        for warning in warnings:
            lines.append(f"- {warning}")
        lines.append("")

    lines.extend(["## Summary", ""])
    lines.extend(
        markdown_table(
            [
                {
                    "universe_id": universe_id,
                    "tracks": count,
                }
                for universe_id, count in sorted(universe_counts.items())
            ],
            [("universe_id", "Universe"), ("tracks", "Search Tracks")],
        )
    )
    lines.append("")
    lines.extend(
        markdown_table(
            [{"status": status, "tracks": count} for status, count in sorted(status_counts.items())],
            [("status", "Lead Status"), ("tracks", "Search Tracks")],
        )
    )
    lines.append("")

    for plan in spec["universe_search_plans"]:
        plan_rows = [row for row in rows if row["plan_id"] == plan["id"]]
        lines.extend([f"## {plan['universe_id']}", ""])
        lines.append(f"Goal: {flat(plan.get('goal', ''))}")
        lines.append("")
        lines.append(f"Promotion gate: {flat(plan.get('promotion_gate_to_result_target', ''))}")
        lines.append("")
        lines.append(f"Minimum lead fields: {flat(plan.get('minimum_lead_fields', []))}")
        lines.append("")
        lines.extend(
            markdown_table(
                plan_rows,
                [
                    ("track_rank", "Rank"),
                    ("track_id", "Track"),
                    ("lead_status", "Status"),
                    ("lead_type", "Lead Type"),
                    ("search_direction", "Direction"),
                    ("search_tools", "Tools"),
                    ("target_file_status", "Target"),
                    ("existing_artifact_present_count", "Present Seeds"),
                    ("existing_artifact_missing_count", "Missing Seeds"),
                ],
            )
        )
        lines.append("")
        for row in sorted(plan_rows, key=lambda item: int(item["track_rank"] or 0)):
            lines.extend([f"### {row['track_id']}", ""])
            lines.append(f"Seed queries: {row['seed_queries']}")
            lines.append("")
            lines.append(f"Accept if: {row['accept_if']}")
            lines.append("")
            lines.append(f"Reject if: {row['reject_if']}")
            lines.append("")
            lines.append(f"Stop conditions: {row['stop_conditions']}")
            lines.append("")
            lines.append(f"Seed artifacts: {row['existing_artifact_status']}")
            lines.append("")
            if row.get("target_file"):
                lines.append(f"Target file: `{row['target_file']}` ({row['target_file_status']}; {row['target_file_policy']})")
                lines.append("")
            elif row.get("target_glob"):
                lines.append(f"Target glob: `{row['target_glob']}` ({row['target_file_status']}; {row['target_file_policy']})")
                lines.append("")
                if row.get("target_examples"):
                    lines.append(f"Example target files: {row['target_examples']}")
                    lines.append("")
            lines.append(f"Outputs: {row['outputs']}")
            lines.append("")

    lines.extend(
        [
            "## Operating Notes",
            "",
            "- This file does not run broad external scraping. It centralizes what should be searched and what a lead must contain.",
            "- Search executors should write each track's target file first, then update the consolidated output table. If the target file already exists, skip the track unless an explicit replace flag is set.",
            "- A future executor can consume `provenance_search_plan.tsv`, emit one target manifest per track, update the consolidated intake table, and then hand promoted leads to identity, locating, and acquisition strategies.",
            "- Search failures and rejected leads should stay append-only. They prevent repeated ad hoc searches from looking like new work.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    spec = load_spec()
    warnings = validate(spec)
    rows = build_rows(spec)
    OUT_TSV.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(OUT_TSV, sep="\t", index=False)
    REPORT_PATH.write_text(render_report(spec, rows, warnings), encoding="utf-8")
    print(f"Wrote {OUT_TSV.relative_to(ROOT)} ({len(rows)} search tracks)")
    print(f"Wrote {REPORT_PATH.relative_to(ROOT)}")
    if warnings:
        print(f"Warnings: {len(warnings)}")


if __name__ == "__main__":
    main()
