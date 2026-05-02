#!/usr/bin/env python3
"""Build a result-bearing artifact acquisition queue for a plot universe.

This queue sits between CORPORA_AND_DATABASES.tsv and SOURCE_ARTIFACTS.tsv.
It asks a narrower question than "is the corpus known?": do we have, or know
how to get, the local artifact that actually catalogs the corpus results?
That artifact may be a database export, workbook, table, code output, PDF
supplement, article PDF containing all stats, repository package, API snapshot,
or website snapshot. The script is reusable across plot universes; Figure 1 is
one configured invocation, not a special implementation.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter
from datetime import date
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
CORPORA_TSV = ROOT / "CORPORA_AND_DATABASES.tsv"

PLOT_CONFIGS = {
    "figure1": {
        "plot_universe_id": "plot1_replication_pairs",
        "plot_label": "figure1",
        "scope_roles": [
            "figure1_candidate",
            "figure1_corpus_database_candidate",
            "figure1_repository_package_candidate",
        ],
        "relevance_field": "figure1_replication_relevance",
    },
    "figure2": {
        "plot_universe_id": "plot2_published_paper_d_vs_n",
        "plot_label": "figure2",
        "scope_roles": ["figure2_source"],
        "relevance_field": "figure2_published_relevance",
    },
    "figure3": {
        "plot_universe_id": "plot3_preregistered_results",
        "plot_label": "figure3",
        "scope_roles": ["figure3_source"],
        "relevance_field": "figure3_prereg_relevance",
    },
}

PATH_FIELDS = ["local_raw_paths", "backing_files", "staged_paths", "promoted_paths"]

QUEUE_COLUMNS = [
    "plot_label",
    "plot_universe_id",
    "corpus_database_id",
    "name",
    "record_kind",
    "inventory_status",
    "current_scope_roles",
    "plot_relevance_field",
    "plot_relevance_value",
    "access_status",
    "host",
    "landing_url",
    "raw_url",
    "existing_local_paths",
    "result_fields_available",
    "has_d_or_convertible_effect",
    "has_n",
    "has_replication_pair_mapping",
    "result_artifact_acquisition_state",
    "acquisition_route_type",
    "acceptable_result_artifact_classes",
    "target_local_root",
    "priority",
    "blocker_codes",
    "next_action",
    "notes",
    "last_seen",
]


def clean(value: object) -> str:
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value).replace("\t", " ")).strip()


def repo_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def slug(value: str) -> str:
    out = re.sub(r"[^a-zA-Z0-9]+", "_", value.lower()).strip("_")
    return out[:80] or "unknown_source"


def split_values(value: str) -> list[str]:
    if not value:
        return []
    out: list[str] = []
    for part in re.split(r"\s*\|\s*|\s*;\s*|\n+", value):
        text = clean(part)
        if text and text.lower() not in {"unknown", "na", "n/a", "none", "<blank>"}:
            out.append(text)
    return out


def resolve_local_path(value: str) -> Path:
    path_text = clean(value)
    if path_text.startswith("local:"):
        path_text = path_text[6:]
    path = Path(path_text)
    return path if path.is_absolute() else ROOT / path


def existing_paths(row: dict[str, str]) -> list[str]:
    candidates: list[str] = []
    for field in PATH_FIELDS:
        candidates.extend(split_values(row.get(field, "")))
    source_key = clean(row.get("source_key", ""))
    if source_key.startswith(("data/", "steps/", "reports/")):
        candidates.append(source_key)
    seen: set[str] = set()
    out: list[str] = []
    for candidate in candidates:
        path = resolve_local_path(candidate)
        if path.exists():
            text = repo_path(path)
            if text not in seen:
                seen.add(text)
                out.append(text)
    return out


def has_yes_or_text(value: str) -> bool:
    text = clean(value).lower()
    return bool(text and text not in {"unknown", "no", "none", "na", "n/a", "<blank>"})


def url_host(row: dict[str, str]) -> str:
    host = clean(row.get("host", ""))
    if host:
        return host.lower()
    for field in ["raw_url", "landing_url"]:
        url = clean(row.get(field, ""))
        parsed = urlparse(url)
        if parsed.netloc:
            return parsed.netloc.lower()
    return ""


def route_type(row: dict[str, str], local_paths: list[str]) -> str:
    if local_paths:
        return "local_inventory"
    host = url_host(row)
    raw_url = clean(row.get("raw_url", ""))
    landing_url = clean(row.get("landing_url", ""))
    record_kind = clean(row.get("record_kind", ""))
    if raw_url:
        return "direct_download_or_api_snapshot"
    if "osf.io" in host:
        return "osf_inventory_and_download"
    if "dataverse" in host or "doi.org/10.7910" in landing_url:
        return "dataverse_inventory_and_download"
    if "github.com" in host or "gitlab" in host:
        return "repository_clone_or_archive_download"
    if "zenodo" in host:
        return "zenodo_record_file_download"
    if "figshare" in host:
        return "figshare_record_file_download"
    if "dryad" in host:
        return "dryad_dataset_download"
    if "doi.org" in host or clean(row.get("citation_key", "")):
        return "article_pdf_supplement_or_data_availability_route"
    if record_kind == "candidate_repository_package":
        return "repository_or_package_discovery"
    return "landing_page_inventory_or_manual_resolution"


def artifact_classes(route: str) -> str:
    mapping = {
        "local_inventory": "existing local table/workbook/archive/code/PDF/website snapshot; identify result-bearing member",
        "direct_download_or_api_snapshot": "downloaded database export | API JSON snapshot | raw table | archive",
        "osf_inventory_and_download": "OSF file inventory | CSV/TSV/XLSX/RDS/SAV/DTA | ZIP member | README/code | PDF supplement",
        "dataverse_inventory_and_download": "Dataverse dataset metadata | tabular file | package ZIP | codebook | replication package member",
        "repository_clone_or_archive_download": "repository archive | data directory | code output table | package manifest | release asset",
        "zenodo_record_file_download": "Zenodo record metadata | record files | archive members | DOI-versioned snapshot",
        "figshare_record_file_download": "Figshare article metadata | public files | collection files",
        "dryad_dataset_download": "Dryad dataset metadata | data files | associated article supplement",
        "article_pdf_supplement_or_data_availability_route": "article PDF/HTML/XML containing corpus table | supplementary table | data availability repository",
        "repository_or_package_discovery": "package landing page | repository archive | data/code files | generated result tables",
        "landing_page_inventory_or_manual_resolution": "mirrored source-family webpage | linked download | manual artifact target",
    }
    return mapping.get(route, "result-bearing table/workbook/PDF/supplement/repository/API snapshot")


def acquisition_state(row: dict[str, str], local_paths: list[str]) -> str:
    fields_seen = any(
        has_yes_or_text(row.get(field, ""))
        for field in ["result_fields_available", "has_d_or_convertible_effect", "has_n", "has_replication_pair_mapping"]
    )
    if local_paths and fields_seen:
        return "local_result_artifact_candidate_present"
    if local_paths:
        return "local_mirror_needs_result_artifact_identification"
    return "needs_result_bearing_artifact_on_disk"


def priority(row: dict[str, str], state: str) -> str:
    if state == "needs_result_bearing_artifact_on_disk":
        if clean(row.get("record_kind", "")) == "candidate_corpus_or_database":
            return "high"
        if clean(row.get("record_kind", "")) == "candidate_repository_package":
            return "high"
        return "medium"
    if state == "local_mirror_needs_result_artifact_identification":
        return "medium"
    return "lower"


def next_action(state: str, route: str) -> str:
    if state == "local_result_artifact_candidate_present":
        return "inventory_local_paths_and_promote_result_bearing_members_to_SOURCE_ARTIFACTS"
    if state == "local_mirror_needs_result_artifact_identification":
        return "inspect_local_mirror_for_database_export_workbook_table_pdf_supplement_or_code_output"
    return f"run_{route}_to_get_result_bearing_artifact_on_disk"


def blockers(row: dict[str, str], local_paths: list[str]) -> str:
    out: list[str] = []
    if not local_paths:
        out.append("no_local_result_artifact")
    if not clean(row.get("raw_url", "")) and not clean(row.get("landing_url", "")) and not clean(row.get("source_key", "")):
        out.append("no_obvious_route")
    if clean(row.get("access_status", "")).lower() in {"blocked", "login_required", "paywalled"}:
        out.append(clean(row.get("access_status", "")).lower())
    return " | ".join(out)


def is_scoped_row(row: dict[str, str], scope_roles: set[str]) -> bool:
    roles = set(split_values(row.get("current_scope_roles", "")))
    return bool(roles & scope_roles)


def read_rows(path: Path) -> list[dict[str, str]]:
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


def write_json(path: Path, payload: dict[str, object], replace: bool) -> None:
    if path.exists() and not replace:
        print(f"Skipped {repo_path(path)} because it exists. Use --replace to rebuild.")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    print(f"Wrote {repo_path(path)}")


def output_paths(plot_label: str) -> tuple[Path, Path, Path]:
    output_root = ROOT / "steps" / "source_inventory" / plot_label / "result_artifact_acquisition"
    return (
        output_root / f"{plot_label}-result-artifact-acquisition-queue.tsv",
        output_root / f"{plot_label}-result-artifact-acquisition-queue.json",
        output_root / f"{plot_label}-result-artifact-acquisition-summary.tsv",
    )


def build_queue(
    plot_label: str,
    plot_universe_id: str,
    scope_roles: set[str],
    relevance_field: str,
) -> list[dict[str, str]]:
    rows = [row for row in read_rows(CORPORA_TSV) if is_scoped_row(row, scope_roles)]
    today = date.today().isoformat()
    out: list[dict[str, str]] = []
    for row in rows:
        paths = existing_paths(row)
        state = acquisition_state(row, paths)
        route = route_type(row, paths)
        source_key = clean(row.get("source_key", "")) or clean(row.get("corpus_database_id", ""))
        target_root = ROOT / "data" / "raw" / "source_artifacts" / plot_label / slug(source_key)
        out.append(
            {
                "plot_label": plot_label,
                "plot_universe_id": plot_universe_id,
                "corpus_database_id": row.get("corpus_database_id", ""),
                "name": row.get("name", ""),
                "record_kind": row.get("record_kind", ""),
                "inventory_status": row.get("inventory_status", ""),
                "current_scope_roles": row.get("current_scope_roles", ""),
                "plot_relevance_field": relevance_field,
                "plot_relevance_value": row.get(relevance_field, ""),
                "access_status": row.get("access_status", ""),
                "host": url_host(row),
                "landing_url": row.get("landing_url", ""),
                "raw_url": row.get("raw_url", ""),
                "existing_local_paths": " | ".join(paths),
                "result_fields_available": row.get("result_fields_available", ""),
                "has_d_or_convertible_effect": row.get("has_d_or_convertible_effect", ""),
                "has_n": row.get("has_n", ""),
                "has_replication_pair_mapping": row.get("has_replication_pair_mapping", ""),
                "result_artifact_acquisition_state": state,
                "acquisition_route_type": route,
                "acceptable_result_artifact_classes": artifact_classes(route),
                "target_local_root": repo_path(target_root),
                "priority": priority(row, state),
                "blocker_codes": blockers(row, paths),
                "next_action": next_action(state, route),
                "notes": "Goal is a local result-bearing artifact for this plot universe, not just a source-family landing page or bibliographic record.",
                "last_seen": today,
            }
        )
    return sorted(
        out,
        key=lambda row: (
            {"high": 0, "medium": 1, "lower": 2}.get(row["priority"], 9),
            row["result_artifact_acquisition_state"],
            row["record_kind"],
            row["name"].lower(),
        ),
    )


def summary_rows(rows: list[dict[str, str]], plot_label: str) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    for field in ["plot_label", "result_artifact_acquisition_state", "acquisition_route_type", "priority", "record_kind"]:
        for value, count in Counter(row.get(field, "") or "<blank>" for row in rows).most_common():
            out.append({"metric": field, "value": value, "count": str(count)})
    out.append({"metric": "total", "value": f"{plot_label}_scoped_rows", "count": str(len(rows))})
    out.append(
        {
            "metric": "total",
            "value": "needs_result_bearing_artifact_on_disk",
            "count": str(sum(1 for row in rows if row["result_artifact_acquisition_state"] == "needs_result_bearing_artifact_on_disk")),
        }
    )
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--plot-label",
        default="figure1",
        help="Output plot label and default config key. Built-in configs: figure1, figure2, figure3.",
    )
    parser.add_argument("--plot-universe-id", default=None)
    parser.add_argument(
        "--scope-role",
        action="append",
        default=None,
        help="current_scope_roles value to include. Repeat for multiple roles. Defaults to the built-in plot config.",
    )
    parser.add_argument(
        "--relevance-field",
        default=None,
        help="CORPORA_AND_DATABASES.tsv relevance column for this plot. Defaults to the built-in plot config.",
    )
    parser.add_argument("--replace", action="store_true")
    args = parser.parse_args()
    config = PLOT_CONFIGS.get(args.plot_label, {})
    plot_universe_id = args.plot_universe_id or config.get("plot_universe_id") or args.plot_label
    scope_roles = set(args.scope_role or config.get("scope_roles") or [args.plot_label])
    relevance_field = args.relevance_field or config.get("relevance_field") or ""
    queue_tsv, queue_json, summary_tsv = output_paths(args.plot_label)
    rows = build_queue(args.plot_label, plot_universe_id, scope_roles, relevance_field)
    summary = summary_rows(rows, args.plot_label)
    write_tsv(queue_tsv, rows, QUEUE_COLUMNS, args.replace)
    write_json(
        queue_json,
        {
            "input": repo_path(CORPORA_TSV),
            "plot_label": args.plot_label,
            "plot_universe_id": plot_universe_id,
            "scope_roles": sorted(scope_roles),
            "relevance_field": relevance_field,
            "row_count": len(rows),
            "summary": summary,
            "records": rows,
        },
        args.replace,
    )
    write_tsv(summary_tsv, summary, ["metric", "value", "count"], args.replace)
    print(f"{args.plot_label} result-artifact acquisition queue: rows={len(rows)}")


if __name__ == "__main__":
    main()
