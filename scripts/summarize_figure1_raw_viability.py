#!/usr/bin/env python3
"""Summarize whether mirrored Figure 1 source-family artifacts look usable.

This is an admission check, not a promotion step. It reads the source-family
inventory, mirror/sample status, parser queue, and corpus-native result rows,
then writes compact summaries of which reviewed corpora currently have raw
tables with effect and N evidence.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
INVENTORY_QUEUE_TSV = ROOT / "steps" / "source_inventory" / "figure1" / "source-family-artifact-inventory-queue.tsv"
INVENTORY_SUMMARY_TSV = ROOT / "steps" / "source_inventory" / "figure1" / "source-artifact-inventory-summary.tsv"
MIRROR_STATUS_TSV = ROOT / "steps" / "source_inventory" / "figure1" / "mirror_sample" / "source-artifact-mirror-sample-status.tsv"
PARSER_QUEUE_TSV = ROOT / "steps" / "source_inventory" / "figure1" / "parser_queue" / "source-artifact-parser-candidate-queue.tsv"
CORPUS_RESULTS_TSV = ROOT / "steps" / "corpus_results" / "figure1" / "corpus-results-proposal.tsv"
CORPUS_TABLES_TSV = ROOT / "steps" / "corpus_results" / "figure1" / "corpus-result-tables-proposal.tsv"
OUTPUT_ROOT = ROOT / "steps" / "corpus_results" / "figure1"
SUMMARY_TSV = OUTPUT_ROOT / "figure1-raw-viability-summary.tsv"
TABLE_DETAIL_TSV = OUTPUT_ROOT / "figure1-raw-viability-table-detail.tsv"
SUMMARY_MD = OUTPUT_ROOT / "figure1-raw-viability-summary.md"

PRIORITY_ORDER = {"high": 3, "medium": 2, "low": 1, "": 0}
STATUS_ORDER = {
    "parsed_result_rows_with_effect_n_and_pair_context": 0,
    "parsed_rows_with_effect_n_need_pair_mapping": 1,
    "alias_covered_by_parsed_result_parent": 2,
    "mirrored_high_priority_tables_need_parser_or_mapper": 3,
    "mirrored_high_priority_non_table_artifacts_need_custom_review": 4,
    "mirrored_lower_priority_artifacts_need_review": 5,
    "parsed_rows_but_no_effect_n_signal": 6,
    "mirrored_or_metadata_only_no_result_signal": 7,
}


def safe_text(value: object) -> str:
    if value is None:
        return ""
    return str(value).replace("\t", " ").replace("\r", " ").replace("\n", " ").strip()


def repo_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def read_tsv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return [{key: safe_text(value) for key, value in row.items()} for row in csv.DictReader(handle, delimiter="\t")]


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


def write_text(path: Path, text: str, replace: bool) -> None:
    if path.exists() and not replace:
        print(f"Skipped {repo_path(path)} because it exists. Use --replace to rebuild.")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    print(f"Wrote {repo_path(path)}")


def int_text(value: str) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return 0


def max_priority(values: Iterable[str]) -> str:
    best = ""
    for value in values:
        if PRIORITY_ORDER.get(value, 0) > PRIORITY_ORDER.get(best, 0):
            best = value
    return best


def add_unique(bucket: dict[str, set[str]], key: str, value: str) -> None:
    if value:
        bucket[key].add(value)


def join_limited(values: Iterable[str], limit: int = 6) -> str:
    cleaned = sorted({safe_text(value) for value in values if safe_text(value)})
    if len(cleaned) <= limit:
        return " | ".join(cleaned)
    return " | ".join(cleaned[:limit] + [f"... +{len(cleaned) - limit} more"])


def columns_preview(columns_json: str, limit: int = 12) -> str:
    try:
        columns = json.loads(columns_json)
    except json.JSONDecodeError:
        columns = []
    if not isinstance(columns, list):
        return ""
    values = [safe_text(column) for column in columns if safe_text(column)]
    if len(values) <= limit:
        return "; ".join(values)
    return "; ".join(values[:limit] + [f"... +{len(values) - limit} columns"])


def table_status(counter: Counter[str]) -> tuple[str, str]:
    if counter["rows_with_effect_n_and_pair_context"] > 0:
        return (
            "candidate_result_table_has_effect_n_and_pair_context",
            "Rows include effect text, N text, and at least one result/pair context field.",
        )
    if counter["rows_with_effect_and_n"] > 0:
        return (
            "candidate_result_table_has_effect_n_needs_pair_mapping",
            "Rows include effect and N text but need review to map original/replication targets.",
        )
    if counter["rows_with_effect_text"] or counter["rows_with_n_text"]:
        return (
            "partial_signal_needs_manual_review",
            "Rows include only partial effect/N evidence.",
        )
    return (
        "parsed_context_or_false_positive_table",
        "Rows parsed, but the copied fields do not contain effect and N evidence.",
    )


def parent_status(counter: Counter[str]) -> tuple[str, str, str]:
    if counter["rows_with_effect_n_and_pair_context"] > 0:
        return (
            "parsed_result_rows_with_effect_n_and_pair_context",
            "candidate_for_figure1_mapping",
            "Parsed native rows contain copied effect text, N text, and result/pair context.",
        )
    if counter["rows_with_effect_and_n"] > 0:
        return (
            "parsed_rows_with_effect_n_need_pair_mapping",
            "candidate_for_figure1_mapping_after_review",
            "Parsed native rows contain effect and N text, but pair mapping still needs review.",
        )
    if counter["alias_covered_by_parsed_parent_count"] > 0:
        return (
            "alias_covered_by_parsed_result_parent",
            "duplicate_or_alias_of_candidate_parent",
            "This key is an alias of another parent whose parsed rows already contain effect and N evidence.",
        )
    if counter["parsed_native_rows"] > 0:
        return (
            "parsed_rows_but_no_effect_n_signal",
            "not_workable_from_current_extraction",
            "Rows were parsed, but effect and N evidence was not copied from the raw table.",
        )
    if counter["high_parse_table_candidate_rows"] > 0:
        return (
            "mirrored_high_priority_tables_need_parser_or_mapper",
            "likely_candidate_needs_custom_parser_or_mapping",
            "Mirrored high-priority tables have pair/effect/N signals, but no usable native rows were emitted yet.",
        )
    if counter["high_priority_parser_candidate_rows"] > 0:
        return (
            "mirrored_high_priority_non_table_artifacts_need_custom_review",
            "possible_candidate_needs_custom_review",
            "Mirrored high-priority artifacts exist, but they are not current table-result parser outputs.",
        )
    if counter["parser_candidate_rows"] > 0:
        return (
            "mirrored_lower_priority_artifacts_need_review",
            "uncertain_candidate_needs_review",
            "Mirrored artifacts exist with lower-priority parser signals.",
        )
    return (
        "mirrored_or_metadata_only_no_result_signal",
        "not_currently_workable",
        "The current mirror/sample pass did not expose result-table evidence.",
    )


def next_action(status: str) -> str:
    if status in {
        "parsed_result_rows_with_effect_n_and_pair_context",
        "parsed_rows_with_effect_n_need_pair_mapping",
    }:
        return "Map native rows to represented original/replication sources, then extract D/N with source_result support rows."
    if status == "alias_covered_by_parsed_result_parent":
        return "Deduplicate this alias into the parsed parent before source_result mapping."
    if status == "mirrored_high_priority_tables_need_parser_or_mapper":
        return "Inspect the high-priority mirrored table samples and add a source-specific parser if they contain Figure 1 rows."
    if status == "mirrored_high_priority_non_table_artifacts_need_custom_review":
        return "Inspect code/workbook/archive artifacts for generated result tables or paired source files."
    if status == "parsed_rows_but_no_effect_n_signal":
        return "Demote or repair parser signals; do not treat the parsed rows as Figure 1 result rows without manual evidence."
    if status == "mirrored_lower_priority_artifacts_need_review":
        return "Review only if higher-priority candidates are exhausted or the parent source family is known-good."
    return "No immediate Figure 1 extraction work from current mirrored evidence."


def build_table_detail(corpus_tables: list[dict[str, str]], corpus_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    table_counts: dict[str, Counter[str]] = defaultdict(Counter)
    for row in corpus_rows:
        table_id = row["corpus_result_table_id"]
        table_counts[table_id]["parsed_native_rows"] += 1
        if row["corpus_effect_text"]:
            table_counts[table_id]["rows_with_effect_text"] += 1
        if row["corpus_n_text"]:
            table_counts[table_id]["rows_with_n_text"] += 1
        if row["corpus_original_source_text"] or row["corpus_replication_source_text"] or row["corpus_result_label_text"]:
            table_counts[table_id]["rows_with_pair_or_result_context"] += 1
        if row["corpus_effect_text"] and row["corpus_n_text"]:
            table_counts[table_id]["rows_with_effect_and_n"] += 1
        if row["corpus_effect_text"] and row["corpus_n_text"] and (
            row["corpus_original_source_text"] or row["corpus_replication_source_text"] or row["corpus_result_label_text"]
        ):
            table_counts[table_id]["rows_with_effect_n_and_pair_context"] += 1

    rows: list[dict[str, str]] = []
    for table in corpus_tables:
        counter = table_counts[table["corpus_result_table_id"]]
        status, reason = table_status(counter)
        rows.append(
            {
                "corpus_result_table_id": table["corpus_result_table_id"],
                "primary_parent_corpus_database_id": table["primary_parent_corpus_database_id"],
                "parent_corpus_database_ids": table["parent_corpus_database_ids"],
                "source_artifact_ids": table["source_artifact_ids"],
                "source_artifact_file_names": table["source_artifact_file_names"],
                "source_artifact_local_path": table["source_artifact_local_path"],
                "parser_scope": table["parser_scope"],
                "column_count": table["column_count"],
                "row_count_emitted": table["row_count_emitted"],
                "parsed_native_rows": str(counter["parsed_native_rows"]),
                "rows_with_effect_text": str(counter["rows_with_effect_text"]),
                "rows_with_n_text": str(counter["rows_with_n_text"]),
                "rows_with_effect_and_n": str(counter["rows_with_effect_and_n"]),
                "rows_with_pair_or_result_context": str(counter["rows_with_pair_or_result_context"]),
                "rows_with_effect_n_and_pair_context": str(counter["rows_with_effect_n_and_pair_context"]),
                "table_check_status": status,
                "table_check_reason": reason,
                "columns_preview": columns_preview(table["columns_json"]),
            }
        )
    return sorted(rows, key=lambda row: (STATUS_ORDER.get(row["table_check_status"], 99), row["primary_parent_corpus_database_id"], row["source_artifact_file_names"]))


def build_summary(
    inventory_queue: list[dict[str, str]],
    inventory_summary: list[dict[str, str]],
    mirror_status: list[dict[str, str]],
    parser_queue: list[dict[str, str]],
    corpus_rows: list[dict[str, str]],
    table_detail: list[dict[str, str]],
) -> list[dict[str, str]]:
    parents = set()
    names: dict[str, set[str]] = defaultdict(set)
    clusters: dict[str, set[str]] = defaultdict(set)
    priorities: dict[str, list[str]] = defaultdict(list)
    counters: dict[str, Counter[str]] = defaultdict(Counter)
    representative_files: dict[str, set[str]] = defaultdict(set)

    for row in inventory_queue:
        parent = row["parent_corpus_database_id_or_key"]
        parents.add(parent)
        add_unique(names, parent, row["preferred_source_family_name"])
        add_unique(clusters, parent, row["cluster_id"])
        priorities[parent].append(row["inventory_priority"])
        counters[parent]["inventory_task_count"] += 1

    for row in inventory_summary:
        parent = row["parent_corpus_database_id_or_key"]
        parents.add(parent)
        add_unique(names, parent, row["preferred_source_family_name"])
        add_unique(clusters, parent, row["cluster_id"])
        counters[parent]["inventory_summary_artifact_rows"] += int_text(row["artifact_rows"])
        counters[parent]["inventory_summary_parser_candidate_rows"] += int_text(row["parser_candidate_rows"])
        counters[parent]["inventory_summary_pair_evidence_rows"] += int_text(row["pair_evidence_rows"])
        counters[parent]["inventory_summary_effect_evidence_rows"] += int_text(row["effect_evidence_rows"])
        counters[parent]["inventory_summary_n_evidence_rows"] += int_text(row["n_evidence_rows"])

    mirror_artifacts: dict[str, set[str]] = defaultdict(set)
    for row in mirror_status:
        parent = row["parent_corpus_database_id"]
        parents.add(parent)
        artifact_id = row["artifact_id"]
        add_unique(mirror_artifacts, parent, artifact_id)
        counters[parent]["mirror_status_rows"] += 1
        if row["mirror_status"] in {"already_local", "downloaded"} or row["mirror_local_path"]:
            counters[parent]["local_or_mirrored_artifacts"] += 1
        if row["mirror_status"] == "downloaded":
            counters[parent]["downloaded_artifacts"] += 1
        if row["sample_status"] == "sampled":
            counters[parent]["sampled_artifacts"] += 1
        if row["sample_status"] == "sample_failed":
            counters[parent]["sample_failed_artifacts"] += 1

    for parent, artifact_ids in mirror_artifacts.items():
        counters[parent]["unique_mirror_artifacts"] = len(artifact_ids)

    for row in parser_queue:
        parent = row["parent_corpus_database_id"]
        parents.add(parent)
        counters[parent]["parser_candidate_rows"] += 1
        if row["parser_priority"] == "high":
            counters[parent]["high_priority_parser_candidate_rows"] += 1
        if row["recommended_next_stage"] == "parse_table_result_candidates":
            counters[parent]["parse_table_candidate_rows"] += 1
        if row["recommended_next_stage"] == "parse_table_result_candidates" and row["parser_priority"] == "high":
            counters[parent]["high_parse_table_candidate_rows"] += 1
        if row["recommended_next_stage"] == "inspect_sample_for_result_fields" and row["parser_priority"] == "high":
            counters[parent]["high_inspect_candidate_rows"] += 1
        if row["parser_priority"] == "high" or row["recommended_next_stage"] == "parse_table_result_candidates":
            add_unique(representative_files, parent, row["file_name"])

    known_parent_keys = set(parents)
    for detail in table_detail:
        parent = detail["primary_parent_corpus_database_id"]
        parents.add(parent)
        add_unique(representative_files, parent, detail["source_artifact_file_names"])
        counters[parent]["parsed_table_count"] += 1
        if detail["table_check_status"].startswith("candidate_result_table"):
            counters[parent]["parsed_candidate_result_table_count"] += 1
        if detail["table_check_status"] == "parsed_context_or_false_positive_table":
            counters[parent]["parsed_context_or_false_positive_table_count"] += 1
        if detail["table_check_status"].startswith("candidate_result_table"):
            for alias_parent in known_parent_keys:
                if alias_parent != parent and alias_parent in detail["parent_corpus_database_ids"]:
                    parents.add(alias_parent)
                    counters[alias_parent]["alias_covered_by_parsed_parent_count"] += 1
                    add_unique(representative_files, alias_parent, detail["source_artifact_file_names"])

    for row in corpus_rows:
        parent = row["primary_parent_corpus_database_id"]
        parents.add(parent)
        counters[parent]["parsed_native_rows"] += 1
        if row["corpus_effect_text"]:
            counters[parent]["rows_with_effect_text"] += 1
        if row["corpus_n_text"]:
            counters[parent]["rows_with_n_text"] += 1
        if row["corpus_original_source_text"] or row["corpus_replication_source_text"] or row["corpus_result_label_text"]:
            counters[parent]["rows_with_pair_or_result_context"] += 1
        if row["corpus_effect_text"] and row["corpus_n_text"]:
            counters[parent]["rows_with_effect_and_n"] += 1
        if row["corpus_effect_text"] and row["corpus_n_text"] and (
            row["corpus_original_source_text"] or row["corpus_replication_source_text"] or row["corpus_result_label_text"]
        ):
            counters[parent]["rows_with_effect_n_and_pair_context"] += 1

    output_rows: list[dict[str, str]] = []
    for parent in sorted(parents):
        counter = counters[parent]
        status, viability, reason = parent_status(counter)
        output_rows.append(
            {
                "parent_corpus_database_id": parent,
                "preferred_source_family_names": join_limited(names[parent], limit=3),
                "cluster_ids": join_limited(clusters[parent], limit=3),
                "inventory_task_count": str(counter["inventory_task_count"]),
                "max_inventory_priority": max_priority(priorities[parent]),
                "unique_mirror_artifacts": str(counter["unique_mirror_artifacts"]),
                "local_or_mirrored_artifacts": str(counter["local_or_mirrored_artifacts"]),
                "downloaded_artifacts": str(counter["downloaded_artifacts"]),
                "sampled_artifacts": str(counter["sampled_artifacts"]),
                "sample_failed_artifacts": str(counter["sample_failed_artifacts"]),
                "parser_candidate_rows": str(counter["parser_candidate_rows"]),
                "high_priority_parser_candidate_rows": str(counter["high_priority_parser_candidate_rows"]),
                "parse_table_candidate_rows": str(counter["parse_table_candidate_rows"]),
                "high_parse_table_candidate_rows": str(counter["high_parse_table_candidate_rows"]),
                "high_inspect_candidate_rows": str(counter["high_inspect_candidate_rows"]),
                "parsed_table_count": str(counter["parsed_table_count"]),
                "parsed_candidate_result_table_count": str(counter["parsed_candidate_result_table_count"]),
                "parsed_context_or_false_positive_table_count": str(counter["parsed_context_or_false_positive_table_count"]),
                "alias_covered_by_parsed_parent_count": str(counter["alias_covered_by_parsed_parent_count"]),
                "parsed_native_rows": str(counter["parsed_native_rows"]),
                "rows_with_effect_text": str(counter["rows_with_effect_text"]),
                "rows_with_n_text": str(counter["rows_with_n_text"]),
                "rows_with_effect_and_n": str(counter["rows_with_effect_and_n"]),
                "rows_with_pair_or_result_context": str(counter["rows_with_pair_or_result_context"]),
                "rows_with_effect_n_and_pair_context": str(counter["rows_with_effect_n_and_pair_context"]),
                "raw_viability_status": status,
                "figure1_viability": viability,
                "raw_viability_reason": reason,
                "next_action": next_action(status),
                "representative_files": join_limited(representative_files[parent], limit=5),
            }
        )

    return sorted(
        output_rows,
        key=lambda row: (
            STATUS_ORDER.get(row["raw_viability_status"], 99),
            -int_text(row["rows_with_effect_n_and_pair_context"]),
            -int_text(row["high_priority_parser_candidate_rows"]),
            row["parent_corpus_database_id"],
        ),
    )


def markdown(summary_rows: list[dict[str, str]], table_rows: list[dict[str, str]]) -> str:
    status_counts = Counter(row["raw_viability_status"] for row in summary_rows)
    viable = [
        row
        for row in summary_rows
        if row["raw_viability_status"]
        in {"parsed_result_rows_with_effect_n_and_pair_context", "parsed_rows_with_effect_n_need_pair_mapping"}
    ]
    parsed_rows = sum(int_text(row["parsed_native_rows"]) for row in summary_rows)
    effect_n_rows = sum(int_text(row["rows_with_effect_and_n"]) for row in summary_rows)
    mirrored = sum(int_text(row["local_or_mirrored_artifacts"]) for row in summary_rows)
    downloaded = sum(int_text(row["downloaded_artifacts"]) for row in summary_rows)

    lines = [
        "# Figure 1 Raw Viability Summary",
        "",
        "Definitions:",
        "",
        "- Corpus/source family: a reusable collection of replication or follow-up results, not just one paper.",
        "- Artifact: a concrete file, archive member, repository object, manifest, or provider record under that source family.",
        "- Mirror: a local copy or already-local raw file with a path recorded on disk.",
        "- Native result row: one copied row from a source table before converting values to D/N.",
        "- D/N: the later Figure 1 plotting fields; D is the standardized effect and N is the relevant sample size.",
        "",
        f"Checked {len(summary_rows)} parent source-family keys, {mirrored} local/mirrored artifacts, and {downloaded} newly downloaded artifacts.",
        f"The generic parser emitted {parsed_rows} native rows; {effect_n_rows} of those rows currently have both effect text and N text.",
        f"{len(viable)} parent keys currently pass the raw-data viability gate for Figure 1 mapping.",
        "",
        "Status counts:",
        "",
    ]
    for status, count in sorted(status_counts.items(), key=lambda item: STATUS_ORDER.get(item[0], 99)):
        lines.append(f"- `{status}`: {count}")

    lines.extend(
        [
            "",
            "Top parent keys by current viability:",
            "",
            "| parent | status | native rows | effect+N rows | candidate tables | representative files |",
            "| --- | --- | ---: | ---: | ---: | --- |",
        ]
    )
    for row in summary_rows[:20]:
        files = row["representative_files"].replace("|", "/")
        lines.append(
            f"| `{row['parent_corpus_database_id']}` | `{row['raw_viability_status']}` | "
            f"{row['parsed_native_rows']} | {row['rows_with_effect_and_n']} | "
            f"{row['parsed_candidate_result_table_count']} | {files} |"
        )

    false_positive_tables = [row for row in table_rows if row["table_check_status"] == "parsed_context_or_false_positive_table"]
    if false_positive_tables:
        lines.extend(["", "Parsed tables that should not be treated as Figure 1 result rows without repair:", ""])
        for row in false_positive_tables[:10]:
            lines.append(
                f"- `{row['primary_parent_corpus_database_id']}` / `{row['source_artifact_file_names']}`: "
                f"{row['table_check_reason']}"
            )

    lines.extend(
        [
            "",
            "Outputs:",
            "",
            f"- `{repo_path(SUMMARY_TSV)}`",
            f"- `{repo_path(TABLE_DETAIL_TSV)}`",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--replace", action="store_true", help="Overwrite existing outputs.")
    args = parser.parse_args()

    inventory_queue = read_tsv(INVENTORY_QUEUE_TSV)
    inventory_summary = read_tsv(INVENTORY_SUMMARY_TSV)
    mirror_status = read_tsv(MIRROR_STATUS_TSV)
    parser_queue = read_tsv(PARSER_QUEUE_TSV)
    corpus_tables = read_tsv(CORPUS_TABLES_TSV)
    corpus_rows = read_tsv(CORPUS_RESULTS_TSV)

    table_rows = build_table_detail(corpus_tables, corpus_rows)
    summary_rows = build_summary(inventory_queue, inventory_summary, mirror_status, parser_queue, corpus_rows, table_rows)

    summary_fields = [
        "parent_corpus_database_id",
        "preferred_source_family_names",
        "cluster_ids",
        "inventory_task_count",
        "max_inventory_priority",
        "unique_mirror_artifacts",
        "local_or_mirrored_artifacts",
        "downloaded_artifacts",
        "sampled_artifacts",
        "sample_failed_artifacts",
        "parser_candidate_rows",
        "high_priority_parser_candidate_rows",
        "parse_table_candidate_rows",
        "high_parse_table_candidate_rows",
        "high_inspect_candidate_rows",
        "parsed_table_count",
        "parsed_candidate_result_table_count",
        "parsed_context_or_false_positive_table_count",
        "alias_covered_by_parsed_parent_count",
        "parsed_native_rows",
        "rows_with_effect_text",
        "rows_with_n_text",
        "rows_with_effect_and_n",
        "rows_with_pair_or_result_context",
        "rows_with_effect_n_and_pair_context",
        "raw_viability_status",
        "figure1_viability",
        "raw_viability_reason",
        "next_action",
        "representative_files",
    ]
    table_fields = [
        "corpus_result_table_id",
        "primary_parent_corpus_database_id",
        "parent_corpus_database_ids",
        "source_artifact_ids",
        "source_artifact_file_names",
        "source_artifact_local_path",
        "parser_scope",
        "column_count",
        "row_count_emitted",
        "parsed_native_rows",
        "rows_with_effect_text",
        "rows_with_n_text",
        "rows_with_effect_and_n",
        "rows_with_pair_or_result_context",
        "rows_with_effect_n_and_pair_context",
        "table_check_status",
        "table_check_reason",
        "columns_preview",
    ]

    write_tsv(SUMMARY_TSV, summary_rows, summary_fields, args.replace)
    write_tsv(TABLE_DETAIL_TSV, table_rows, table_fields, args.replace)
    write_text(SUMMARY_MD, markdown(summary_rows, table_rows), args.replace)

    viable = sum(
        1
        for row in summary_rows
        if row["raw_viability_status"]
        in {"parsed_result_rows_with_effect_n_and_pair_context", "parsed_rows_with_effect_n_need_pair_mapping"}
    )
    effect_n_rows = sum(int_text(row["rows_with_effect_and_n"]) for row in summary_rows)
    print(
        "Figure 1 raw viability: "
        f"parents={len(summary_rows)}; viable_parents={viable}; "
        f"native_rows={sum(int_text(row['parsed_native_rows']) for row in summary_rows)}; "
        f"effect_n_rows={effect_n_rows}"
    )


if __name__ == "__main__":
    main()
