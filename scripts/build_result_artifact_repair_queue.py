#!/usr/bin/env python3
"""Build a bounded Codex repair queue for unresolved result artifacts.

This is the automated tail after the broad acquisition pass. It selects
follow-up rows that Codex can still retry deterministically, then emits an
ordinary result-artifact acquisition queue so the same strategy runner can be
reused.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TRACKS = "codex_provider_repair,codex_direct_url_repair"


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


def summary_rows(queue_rows: list[dict[str, str]], followup_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    for field, rows in [
        ("followup_track", followup_rows),
        ("acquisition_route_type", queue_rows),
        ("host", queue_rows),
        ("priority", queue_rows),
    ]:
        for value, count in Counter(row.get(field, "") or "<blank>" for row in rows).most_common():
            out.append({"metric": field, "value": value, "count": str(count)})
    out.append({"metric": "total", "value": "repair_queue_rows", "count": str(len(queue_rows))})
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plot-label", default="figure1")
    parser.add_argument("--queue", type=Path)
    parser.add_argument("--followup", type=Path)
    parser.add_argument("--output-root", type=Path)
    parser.add_argument("--tracks", default=DEFAULT_TRACKS)
    parser.add_argument("--replace", action="store_true")
    args = parser.parse_args()

    root = ROOT / "steps" / "source_inventory" / args.plot_label / "result_artifact_acquisition"
    queue_path = resolve_path(args.queue) if args.queue else root / f"{args.plot_label}-result-artifact-acquisition-queue.tsv"
    followup_path = resolve_path(args.followup) if args.followup else root / "followup" / f"{args.plot_label}-result-artifact-followup-queue.tsv"
    output_root = resolve_path(args.output_root) if args.output_root else root / "repair"
    tracks = {track.strip() for track in args.tracks.split(",") if track.strip()}

    queue_rows = read_tsv(queue_path)
    queue_by_id = {row.get("corpus_database_id", ""): row for row in queue_rows}
    selected_followup = [
        row
        for row in read_tsv(followup_path)
        if row.get("assigned_to") == "codex"
        and row.get("on_disk_after_automation") == "no"
        and row.get("followup_track") in tracks
    ]
    selected_ids = {row.get("corpus_database_id", "") for row in selected_followup}
    repair_queue = [queue_by_id[corpus_id] for corpus_id in sorted(selected_ids) if corpus_id in queue_by_id]

    if queue_rows:
        columns = list(queue_rows[0].keys())
    else:
        columns = []
    prefix = f"{args.plot_label}-result-artifact-codex-repair"
    write_tsv(output_root / f"{prefix}-queue.tsv", repair_queue, columns, args.replace)
    write_tsv(output_root / f"{prefix}-summary.tsv", summary_rows(repair_queue, selected_followup), ["metric", "value", "count"], args.replace)
    write_json(
        output_root / f"{prefix}-queue.json",
        {
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "queue_input": repo_path(queue_path),
            "followup_input": repo_path(followup_path),
            "selected_tracks": sorted(tracks),
            "followup_rows_selected": len(selected_followup),
            "queue_rows_selected": len(repair_queue),
            "followup_records": selected_followup,
            "queue_records": repair_queue,
        },
        args.replace,
    )
    print(
        f"{args.plot_label} Codex repair queue: "
        f"followup_rows={len(selected_followup)}; queue_rows={len(repair_queue)}"
    )


if __name__ == "__main__":
    main()
