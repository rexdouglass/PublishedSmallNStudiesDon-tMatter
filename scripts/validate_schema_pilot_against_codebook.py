#!/usr/bin/env python3
"""Validate the sampled provenance pilot against the formal codebook."""

from __future__ import annotations

import os
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DERIVED = ROOT / "data" / "derived" / "effect_inflation_dataset"
PILOT = DERIVED / "schema_pilot"
DATA_DICTIONARY = DERIVED / "provenance_data_dictionary.tsv"
SAMPLE_N = int(os.environ.get("SCHEMA_PILOT_N", "300"))
SAMPLE_SUFFIX = f"sample_{SAMPLE_N}"

OUT_ISSUES = PILOT / "codebook_validation_issues.tsv"
OUT_SUMMARY = PILOT / "codebook_validation_summary.tsv"
OUT_MD = PILOT / "codebook_validation_report.md"

def pilot_file(table_name: str, diagnostic_path: Path) -> Path:
    """Prefer the codebook-shaped pilot if it exists; otherwise validate diagnostics."""
    stem = table_name.removesuffix(".tsv")
    codebook_path = PILOT / f"{stem}_codebook_{SAMPLE_SUFFIX}.tsv"
    return codebook_path if codebook_path.exists() else diagnostic_path


FORMAL_FILES = {
    "source.tsv": pilot_file("source.tsv", PILOT / f"source_{SAMPLE_SUFFIX}.tsv"),
    "source_access.tsv": pilot_file("source_access.tsv", PILOT / f"source_access_{SAMPLE_SUFFIX}.tsv"),
    "source_access_attempt.tsv": pilot_file("source_access_attempt.tsv", PILOT / f"source_access_attempt_codebook_{SAMPLE_SUFFIX}.tsv"),
    "source_file.tsv": pilot_file("source_file.tsv", PILOT / f"source_file_codebook_{SAMPLE_SUFFIX}.tsv"),
    "source_version.tsv": pilot_file("source_version.tsv", PILOT / f"source_version_codebook_{SAMPLE_SUFFIX}.tsv"),
    "source_access_right.tsv": pilot_file("source_access_right.tsv", PILOT / f"source_access_right_codebook_{SAMPLE_SUFFIX}.tsv"),
    "source_identifier.tsv": pilot_file("source_identifier.tsv", PILOT / f"source_identifier_codebook_{SAMPLE_SUFFIX}.tsv"),
    "source_classification.tsv": pilot_file("source_classification.tsv", PILOT / f"source_classification_codebook_{SAMPLE_SUFFIX}.tsv"),
    "source_result.tsv": pilot_file("source_result.tsv", PILOT / f"source_result_{SAMPLE_SUFFIX}.tsv"),
    "canonical_result.tsv": pilot_file("canonical_result.tsv", PILOT / f"canonical_result_{SAMPLE_SUFFIX}.tsv"),
    "canonical_result_membership.tsv": pilot_file("canonical_result_membership.tsv", PILOT / f"canonical_result_membership_codebook_{SAMPLE_SUFFIX}.tsv"),
    "source_result_support.tsv": pilot_file("source_result_support.tsv", PILOT / f"source_result_support_codebook_{SAMPLE_SUFFIX}.tsv"),
    "plot_membership.tsv": pilot_file("plot_membership.tsv", PILOT / f"plot_membership_codebook_{SAMPLE_SUFFIX}.tsv"),
    "source_source_mapping.tsv": pilot_file("source_source_mapping.tsv", PILOT / f"source_source_mapping_{SAMPLE_SUFFIX}.tsv"),
    "extraction_event.tsv": pilot_file("extraction_event.tsv", PILOT / f"retrace_events_{SAMPLE_SUFFIX}.tsv"),
    "extraction_problem.tsv": pilot_file("extraction_problem.tsv", PILOT / f"retrace_problems_{SAMPLE_SUFFIX}.tsv"),
    "manual_acquisition_task.tsv": pilot_file("manual_acquisition_task.tsv", PILOT / f"manual_acquisition_task_codebook_{SAMPLE_SUFFIX}.tsv"),
}

REQUIRED_LEVELS = {"required", "required_for_plot", "required_for_promotion", "required_for_d_or_native"}
PROMOTION_LEVELS = {"required_for_plot", "required_for_promotion", "required_for_d_or_native"}


def safe_text(value: object) -> str:
    if value is None or pd.isna(value):
        return ""
    return str(value).strip()


def read_tsv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, sep="\t", dtype=str, keep_default_na=False)


def allowed_values(text: str) -> set[str]:
    return {part.strip() for part in safe_text(text).split("|") if part.strip()}


def add_issue(
    issues: list[dict[str, object]],
    table_name: str,
    file_path: Path,
    issue_code: str,
    severity: str,
    column_name: str = "",
    affected_rows: int | str = "",
    detail: str = "",
    suggested_rework: str = "",
) -> None:
    issues.append(
        {
            "table_name": table_name,
            "file_path": str(file_path.relative_to(ROOT)),
            "issue_code": issue_code,
            "severity": severity,
            "column_name": column_name,
            "affected_rows": affected_rows,
            "detail": detail,
            "suggested_rework": suggested_rework,
        }
    )


def check_table_shape(
    table_name: str,
    path: Path,
    df: pd.DataFrame,
    dictionary: pd.DataFrame,
    issues: list[dict[str, object]],
) -> None:
    expected = dictionary.loc[dictionary["table_name"].eq(table_name)].copy()
    expected_columns = expected["column_name"].tolist()
    actual_columns = df.columns.tolist()
    expected_set = set(expected_columns)
    actual_set = set(actual_columns)

    for row in expected.itertuples(index=False):
        column = row.column_name
        level = row.required_level
        if column not in actual_set:
            severity = "high" if level in REQUIRED_LEVELS else "medium" if level in {"recommended", "conditional"} else "low"
            add_issue(
                issues,
                table_name,
                path,
                "missing_codebook_column",
                severity,
                column,
                len(df),
                f"Column {column} is defined as {level} in the codebook but is absent from {path.name}.",
                "Add the column to the pilot/formal table template or document why this pilot table is diagnostic only.",
            )

    for column in actual_columns:
        if column not in expected_set:
            add_issue(
                issues,
                table_name,
                path,
                "extra_non_codebook_column",
                "low",
                column,
                "",
                f"Column {column} is present in {path.name} but is not in the formal {table_name} codebook.",
                "Keep diagnostic columns in a diagnostic table, or add them to the formal codebook if they are part of the dataset contract.",
            )

    for row in expected.itertuples(index=False):
        column = row.column_name
        level = row.required_level
        if column not in actual_set:
            continue
        blank = df[column].map(safe_text).eq("")
        if level == "required" and blank.any():
            add_issue(
                issues,
                table_name,
                path,
                "blank_required_values",
                "high",
                column,
                int(blank.sum()),
                f"{int(blank.sum())} rows have blank required field {column}.",
                "Populate this field or mark affected rows as blocked in extraction_problem.tsv.",
            )
        elif level in PROMOTION_LEVELS and blank.any():
            add_issue(
                issues,
                table_name,
                path,
                "blank_promotion_gate_values",
                "high",
                column,
                int(blank.sum()),
                f"{int(blank.sum())} rows have blank promotion-gate field {column}.",
                "Rows with this blank cannot be considered fully coded/promotable.",
            )

        allowed = allowed_values(row.allowed_values)
        if allowed and column in actual_set:
            nonblank = df[column].map(safe_text).ne("")
            invalid = nonblank & ~df[column].map(safe_text).isin(allowed)
            if invalid.any():
                add_issue(
                    issues,
                    table_name,
                    path,
                    "invalid_controlled_vocabulary",
                    "high",
                    column,
                    int(invalid.sum()),
                    f"{int(invalid.sum())} nonblank values in {column} are outside the allowed vocabulary.",
                    f"Use one of: {' | '.join(sorted(allowed))}",
                )


def check_foreign_keys(frames: dict[str, pd.DataFrame], issues: list[dict[str, object]]) -> None:
    source_ids = set(frames["source.tsv"].get("source_id", pd.Series(dtype=str)).map(safe_text))
    access_ids = set(frames["source_access.tsv"].get("access_id", pd.Series(dtype=str)).map(safe_text))
    source_result_ids = set(frames["source_result.tsv"].get("source_result_id", pd.Series(dtype=str)).map(safe_text))
    canonical_ids = set(frames["canonical_result.tsv"].get("canonical_result_id", pd.Series(dtype=str)).map(safe_text))
    source_file_ids = set(frames["source_file.tsv"].get("source_file_id", pd.Series(dtype=str)).map(safe_text))
    source_version_ids = set(frames["source_version.tsv"].get("source_version_id", pd.Series(dtype=str)).map(safe_text))
    attempt_ids = set(frames["source_access_attempt.tsv"].get("attempt_id", pd.Series(dtype=str)).map(safe_text))

    checks = [
        ("source_access.tsv", "source_id", source_ids, FORMAL_FILES["source_access.tsv"]),
        ("source_access_attempt.tsv", "source_id", source_ids, FORMAL_FILES["source_access_attempt.tsv"]),
        ("source_access_attempt.tsv", "access_id", access_ids, FORMAL_FILES["source_access_attempt.tsv"]),
        ("source_file.tsv", "source_id", source_ids, FORMAL_FILES["source_file.tsv"]),
        ("source_file.tsv", "access_id", access_ids, FORMAL_FILES["source_file.tsv"]),
        ("source_file.tsv", "attempt_id", attempt_ids, FORMAL_FILES["source_file.tsv"]),
        ("source_file.tsv", "source_version_id", source_version_ids, FORMAL_FILES["source_file.tsv"]),
        ("source_version.tsv", "source_id", source_ids, FORMAL_FILES["source_version.tsv"]),
        ("source_version.tsv", "version_evidence_file_id", source_file_ids, FORMAL_FILES["source_version.tsv"]),
        ("source_access_right.tsv", "source_id", source_ids, FORMAL_FILES["source_access_right.tsv"]),
        ("source_access_right.tsv", "source_file_id", source_file_ids, FORMAL_FILES["source_access_right.tsv"]),
        ("source_identifier.tsv", "source_id", source_ids, FORMAL_FILES["source_identifier.tsv"]),
        ("source_classification.tsv", "source_id", source_ids, FORMAL_FILES["source_classification.tsv"]),
        ("source_result.tsv", "extraction_source_id", source_ids, FORMAL_FILES["source_result.tsv"]),
        ("source_result.tsv", "represented_source_id", source_ids, FORMAL_FILES["source_result.tsv"]),
        ("source_result.tsv", "access_id", access_ids, FORMAL_FILES["source_result.tsv"]),
        ("source_result.tsv", "canonical_result_id", canonical_ids, FORMAL_FILES["source_result.tsv"]),
        ("canonical_result.tsv", "represented_source_id", source_ids, FORMAL_FILES["canonical_result.tsv"]),
        ("canonical_result.tsv", "preferred_source_result_id", source_result_ids, FORMAL_FILES["canonical_result.tsv"]),
        ("canonical_result_membership.tsv", "canonical_result_id", canonical_ids, FORMAL_FILES["canonical_result_membership.tsv"]),
        ("canonical_result_membership.tsv", "source_result_id", source_result_ids, FORMAL_FILES["canonical_result_membership.tsv"]),
        ("source_result_support.tsv", "source_result_id", source_result_ids, FORMAL_FILES["source_result_support.tsv"]),
        ("source_result_support.tsv", "source_id", source_ids, FORMAL_FILES["source_result_support.tsv"]),
        ("source_result_support.tsv", "access_id", access_ids, FORMAL_FILES["source_result_support.tsv"]),
        ("source_result_support.tsv", "source_file_id", source_file_ids, FORMAL_FILES["source_result_support.tsv"]),
        ("plot_membership.tsv", "canonical_result_id", canonical_ids, FORMAL_FILES["plot_membership.tsv"]),
        ("source_source_mapping.tsv", "from_source_id", source_ids, FORMAL_FILES["source_source_mapping.tsv"]),
        ("source_source_mapping.tsv", "to_source_id", source_ids, FORMAL_FILES["source_source_mapping.tsv"]),
        ("extraction_event.tsv", "source_result_id", source_result_ids, FORMAL_FILES["extraction_event.tsv"]),
        ("extraction_problem.tsv", "source_result_id", source_result_ids, FORMAL_FILES["extraction_problem.tsv"]),
        ("manual_acquisition_task.tsv", "source_result_id", source_result_ids, FORMAL_FILES["manual_acquisition_task.tsv"]),
        ("manual_acquisition_task.tsv", "canonical_result_id", canonical_ids, FORMAL_FILES["manual_acquisition_task.tsv"]),
        ("manual_acquisition_task.tsv", "represented_source_id", source_ids, FORMAL_FILES["manual_acquisition_task.tsv"]),
        ("manual_acquisition_task.tsv", "extraction_source_id", source_ids, FORMAL_FILES["manual_acquisition_task.tsv"]),
        ("manual_acquisition_task.tsv", "created_source_file_id", source_file_ids, FORMAL_FILES["manual_acquisition_task.tsv"]),
    ]
    for table_name, column, valid_ids, path in checks:
        df = frames.get(table_name)
        if df is None or column not in df.columns:
            continue
        values = df[column].map(safe_text)
        bad = values.ne("") & ~values.isin(valid_ids)
        if bad.any():
            add_issue(
                issues,
                table_name,
                path,
                "foreign_key_missing_target",
                "high",
                column,
                int(bad.sum()),
                f"{int(bad.sum())} nonblank {column} values do not resolve to their target table.",
                "Fix IDs or add the missing source/access/source_result/canonical rows.",
            )


def check_promotion_readiness(frames: dict[str, pd.DataFrame], issues: list[dict[str, object]]) -> None:
    path = FORMAL_FILES["source_result.tsv"]
    sr = frames["source_result.tsv"].copy()
    human_path = PILOT / f"human_check_source_result_{SAMPLE_SUFFIX}.tsv"
    if human_path.exists():
        human = read_tsv(human_path)
        if "source_result_id" in human.columns:
            keep = [
                "source_result_id",
                "source_text_extraction_status",
                "recovered_verbatim_effect_text",
                "recovered_verbatim_n_text",
                "recovered_transformation_explanation",
                "upstream_row_json",
            ]
            sr = sr.merge(human[[c for c in keep if c in human.columns]], on="source_result_id", how="left")

    gate_checks = {
        "verbatim_source_row_text": "direct copied source row text",
        "verbatim_effect_text": "direct copied effect/statistic text",
        "verbatim_n_text": "direct copied N/sample-size text",
        "native_effect_value": "parsed native effect value",
        "native_effect_metric": "native effect metric",
        "native_n_total": "parsed native N",
        "extraction_confidence": "extraction confidence",
        "human_check_status": "human-check status",
        "prereg_status": "preregistration status where applicable",
        "selector_status": "focal selector status",
    }
    for column, detail in gate_checks.items():
        if column not in sr.columns:
            continue
        blank = sr[column].map(safe_text).eq("")
        if blank.any():
            add_issue(
                issues,
                "source_result.tsv",
                path,
                "source_result_not_fully_coded",
                "high",
                column,
                int(blank.sum()),
                f"{int(blank.sum())} source-result rows lack {detail}.",
                "Backfill from human-check retrace rows where possible; otherwise mark staged/blocked and add extraction_problem rows.",
            )

    if "source_text_extraction_status" in sr.columns:
        not_cells = sr["source_text_extraction_status"].map(safe_text).ne("source_cells_recovered")
        if not_cells.any():
            add_issue(
                issues,
                "source_result.tsv",
                path,
                "not_human_checkable_source_cells",
                "high",
                "source_text_extraction_status",
                int(not_cells.sum()),
                f"{int(not_cells.sum())} pilot rows do not have recovered source effect+N cells in the human-check retrace.",
                "These rows need original source extraction, not only plot-level D/N recovery.",
            )

    if "coding_status" in sr.columns:
        not_fully = sr["coding_status"].map(safe_text).ne("fully_coded")
        if not_fully.any():
            add_issue(
                issues,
                "source_result.tsv",
                path,
                "rows_still_coded_with_schema_gaps",
                "medium",
                "coding_status",
                int(not_fully.sum()),
                f"{int(not_fully.sum())} source-result rows are explicitly marked as not fully coded/promotable yet.",
                "Keep these rows as auditable staged rows; backfill original source text before treating them as fully promoted.",
            )

    fully = sr["coding_status"].map(safe_text).eq("fully_coded") if "coding_status" in sr.columns else pd.Series(False, index=sr.index)
    if fully.any():
        missing_verbatim = (
            sr.get("verbatim_effect_text", pd.Series("", index=sr.index)).map(safe_text).eq("")
            | sr.get("verbatim_n_text", pd.Series("", index=sr.index)).map(safe_text).eq("")
        )
        bad = fully & missing_verbatim
        if bad.any():
            add_issue(
                issues,
                "source_result.tsv",
                path,
                "fully_coded_without_verbatim_evidence",
                "high",
                "coding_status",
                int(bad.sum()),
                "Rows are marked fully_coded but lack verbatim effect/N evidence.",
                "Downgrade coding_status or backfill verbatim fields.",
            )


def markdown_table(headers: list[str], rows: list[list[object]]) -> str:
    def cell(value: object) -> str:
        return safe_text(value).replace("|", "\\|").replace("\n", " ")

    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    lines.extend("| " + " | ".join(cell(value) for value in row) + " |" for row in rows)
    return "\n".join(lines)


def main() -> None:
    dictionary = read_tsv(DATA_DICTIONARY)
    frames = {table_name: read_tsv(path) for table_name, path in FORMAL_FILES.items()}
    issues: list[dict[str, object]] = []

    for table_name, path in FORMAL_FILES.items():
        check_table_shape(table_name, path, frames[table_name], dictionary, issues)
    check_foreign_keys(frames, issues)
    check_promotion_readiness(frames, issues)

    issues_df = pd.DataFrame(issues)
    if issues_df.empty:
        issues_df = pd.DataFrame(
            columns=[
                "table_name",
                "file_path",
                "issue_code",
                "severity",
                "column_name",
                "affected_rows",
                "detail",
                "suggested_rework",
            ]
        )

    table_rows = []
    for table_name, path in FORMAL_FILES.items():
        df = frames[table_name]
        table_issues = issues_df.loc[issues_df["table_name"].eq(table_name)]
        high = int(table_issues["severity"].eq("high").sum()) if not table_issues.empty else 0
        medium = int(table_issues["severity"].eq("medium").sum()) if not table_issues.empty else 0
        low = int(table_issues["severity"].eq("low").sum()) if not table_issues.empty else 0
        table_rows.append(
            {
                "table_name": table_name,
                "file_path": str(path.relative_to(ROOT)),
                "rows": len(df),
                "columns": len(df.columns),
                "high_issue_types": high,
                "medium_issue_types": medium,
                "low_issue_types": low,
                "passes_codebook_for_full_promotion": high == 0 and medium == 0 and low == 0,
            }
        )
    summary_df = pd.DataFrame(table_rows)

    issue_counts = (
        issues_df.groupby(["severity", "issue_code"], dropna=False)
        .size()
        .reset_index(name="issue_type_count")
        .sort_values(["severity", "issue_code"], kind="stable")
        if not issues_df.empty
        else pd.DataFrame(columns=["severity", "issue_code", "issue_type_count"])
    )

    OUT_ISSUES.parent.mkdir(parents=True, exist_ok=True)
    issues_df.to_csv(OUT_ISSUES, sep="\t", index=False)
    summary_df.to_csv(OUT_SUMMARY, sep="\t", index=False)

    md = [
        f"# Codebook Validation For {SAMPLE_N}-Row Provenance Pilot",
        "",
        f"This validates the existing {SAMPLE_N}-row pilot files against `provenance_data_dictionary.tsv`. It distinguishes retrace reproducibility from full codebook conformance.",
        "",
        "## Bottom Line",
        "",
    ]
    if bool(summary_df["high_issue_types"].eq(0).all()):
        md.append("All formal pilot tables pass required codebook shape checks. Rows with explicit medium issues are auditable but not fully promotable yet.")
    else:
        md.append(f"The {SAMPLE_N}-row pilot is **not** correctly coded as a fully promotable dataset yet. The codebook-shaped tables exist, but some rows still fail promotion gates such as source locators, verbatim source-result fields, original-source evidence, or explicit problem coding.")
    md.extend(
        [
            "",
            "## Table Summary",
            "",
            markdown_table(
                ["Table", "Rows", "Columns", "High issue types", "Medium", "Low", "Passes full promotion"],
                [
                    [
                        row.table_name,
                        row.rows,
                        row.columns,
                        row.high_issue_types,
                        row.medium_issue_types,
                        row.low_issue_types,
                        row.passes_codebook_for_full_promotion,
                    ]
                    for row in summary_df.itertuples(index=False)
                ],
            ),
            "",
            "## Issue Type Counts",
            "",
            markdown_table(
                ["Severity", "Issue code", "Issue type count"],
                [[row.severity, row.issue_code, row.issue_type_count] for row in issue_counts.itertuples(index=False)],
            )
            if not issue_counts.empty
            else "No issues found.",
            "",
            "## Machine-Readable Outputs",
            "",
            f"- `{OUT_SUMMARY.relative_to(ROOT)}`",
            f"- `{OUT_ISSUES.relative_to(ROOT)}`",
        ]
    )
    OUT_MD.write_text("\n".join(md) + "\n", encoding="utf-8")

    print(f"Wrote {OUT_SUMMARY.relative_to(ROOT)}")
    print(f"Wrote {OUT_ISSUES.relative_to(ROOT)}")
    print(f"Wrote {OUT_MD.relative_to(ROOT)}")
    print(summary_df.to_string(index=False))
    if not issue_counts.empty:
        print("\nIssue type counts:")
        print(issue_counts.to_string(index=False))


if __name__ == "__main__":
    main()
