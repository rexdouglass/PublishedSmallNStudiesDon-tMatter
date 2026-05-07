#!/usr/bin/env python3
"""Finish local Figure 1 mining for mirrored candidates.

This script is intentionally narrow: it promotes only rows where the mirrored
local source already contains original and replication/follow-up statistics plus
N on both sides.  It does not do provenance hardening or broad source search.
"""

from __future__ import annotations

import math
import re
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from bs4 import BeautifulSoup


ROOT = Path(__file__).resolve().parents[1]
RAW_BASE = (
    ROOT
    / "data"
    / "raw"
    / "replication_projects"
    / "lead_harvest"
    / "gpt_many_replication_candidates_20260504"
)
TRANSPARENT_DIR = RAW_BASE / "transparent_replications_clearer_thinking"
CLINICAL_WORKBOOK = ROOT / "data" / "raw" / "replication_projects" / "clinical_replication" / "data - published.xlsx"

PROMOTED_DIR = ROOT / "data" / "derived" / "replication_pairs" / "harvest" / "promoted"
STAGED_DIR = ROOT / "data" / "derived" / "replication_pairs" / "harvest" / "staged"
AUDIT_DIR = ROOT / "steps" / "corpus_results" / "figure1" / "remaining_local_mining"
TRANSPARENT_PROMOTED = PROMOTED_DIR / "transparent_replications_table_rows__promoted_pairs.csv"
AUDIT_TSV = AUDIT_DIR / "transparent_replications_table_rows.tsv"
STATUS_TSV = AUDIT_DIR / "remaining-local-mining-status.tsv"
STAGED_SCAN_TSV = AUDIT_DIR / "staged-unpromoted-scan.tsv"

NUM_RE = r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:e[-+]?\d+)?"


def clean_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and math.isnan(value):
        return ""
    text = str(value)
    if text.lower() in {"nan", "none", "null", "<na>"}:
        return ""
    text = text.replace("−", "-").replace("–", "-")
    return re.sub(r"[\t\r\n ]+", " ", text).strip()


def slug(value: Any) -> str:
    text = clean_text(value).lower()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    return text.strip("_")[:90]


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except Exception:
        return str(path)


def r_to_d(value: float) -> float:
    if not np.isfinite(value) or abs(value) >= 1:
        return np.nan
    return abs(2 * value / math.sqrt(1 - value * value))


def parse_n(text: str) -> float:
    matches = list(re.finditer(r"(?i)\bN\s*=\s*([0-9][0-9,]*)|\bn\s*=\s*([0-9][0-9,]*)", text))
    if not matches:
        return np.nan
    value = matches[-1].group(1) or matches[-1].group(2)
    return float(value.replace(",", ""))


def parse_effect_and_n(text: Any) -> tuple[float, float, str]:
    source = clean_text(text)
    n = parse_n(source)

    # Prefer explicitly reported standardized effects where available.
    match = re.search(rf"(?i)(?:cohen.?s\s+)?\bd\s*=\s*({NUM_RE})", source)
    if match:
        return abs(float(match.group(1))), n, "reported_d"

    match = re.search(rf"(?i)effect\s+size\s*=\s*({NUM_RE}).{{0,80}}(?:rank|biserial|correlation|r\b)", source)
    if match:
        return r_to_d(abs(float(match.group(1)))), n, "reported_correlation_like_effect"

    match = re.search(rf"(?i)\br\s*=\s*({NUM_RE})", source)
    if match:
        return r_to_d(abs(float(match.group(1)))), n, "reported_r"

    match = re.search(rf"(?i)t\s*\(\s*({NUM_RE})\s*\)\s*=\s*({NUM_RE})", source)
    if match:
        df = float(match.group(1))
        stat_t = float(match.group(2))
        d = abs(2 * stat_t / math.sqrt(df))
        if not np.isfinite(n):
            n = df + 1
        return d, n, "t_df_to_d"

    match = re.search(
        rf"(?i)(?:χ|x|chi)[\s-]*2\s*\(\s*[^,)]*[,]?\s*N\s*=\s*([0-9][0-9,]*)\s*\)\s*=\s*({NUM_RE})",
        source,
    )
    if match:
        n = float(match.group(1).replace(",", ""))
        chi2 = float(match.group(2))
        return r_to_d(math.sqrt(abs(chi2) / n)), n, "chi2_n_to_phi_to_d"

    return np.nan, n, ""


def flatten_columns(table: pd.DataFrame) -> list[str]:
    columns: list[str] = []
    for col in table.columns:
        if isinstance(col, tuple):
            label = " ".join(clean_text(part) for part in col if not str(part).startswith("Unnamed"))
        else:
            label = clean_text(col)
        columns.append(label)
    return columns


def read_html_tables(path: Path) -> list[pd.DataFrame]:
    soup = BeautifulSoup(path.read_text(errors="ignore"), "html.parser")
    tables: list[pd.DataFrame] = []
    for table in soup.find_all("table"):
        header: list[str] | None = None
        body_rows: list[list[str]] = []
        for tr in table.find_all("tr"):
            cells = tr.find_all(["th", "td"])
            if not cells:
                continue
            values = [clean_text(cell.get_text(" ", strip=True)) for cell in cells]
            is_header = any(cell.name == "th" for cell in cells)
            if header is None and is_header:
                header = values
                continue
            body_rows.append(values)
        if not body_rows:
            continue
        width = max(len(row) for row in body_rows + ([header] if header else []))
        normalized_rows = [row + [""] * (width - len(row)) for row in body_rows]
        if header is None:
            columns = list(range(width))
        else:
            padded = header + [""] * (width - len(header))
            columns = [label if label else f"column_{idx}" for idx, label in enumerate(padded)]
        tables.append(pd.DataFrame(normalized_rows, columns=columns))
    return tables


def table_with_possible_header(table: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    columns = flatten_columns(table)
    if any("original" in col.lower() for col in columns):
        return table, columns
    if table.empty:
        return table, columns
    first = [clean_text(value) for value in table.iloc[0].tolist()]
    if any("original" in cell.lower() for cell in first) and any(
        "our result" in cell.lower() or "replication" in cell.lower() for cell in first
    ):
        return table.iloc[1:].reset_index(drop=True).copy(), first
    return table, columns


def report_title_from_page(path: Path) -> str:
    text = path.read_text(errors="ignore")
    match = re.search(r"<title>(.*?)</title>", text, flags=re.I | re.S)
    if not match:
        return path.stem
    title = re.sub(r"<[^>]+>", " ", match.group(1))
    title = clean_text(title)
    return re.sub(r"^»\s*", "", title)


def doi_from_page(path: Path) -> str:
    text = path.read_text(errors="ignore")
    dois = re.findall(r"https?://doi\.org/([^\"<\s]+)", text, flags=re.I)
    for doi in dois:
        norm = doi.strip().strip(").,").lower()
        if not norm.startswith("10.5281/zenodo"):
            return norm
    return ""


def build_transparent_rows() -> tuple[pd.DataFrame, pd.DataFrame]:
    rows: list[dict[str, Any]] = []
    seen_pages: set[str] = set()
    for path in sorted(TRANSPARENT_DIR.glob("replication-*.html")):
        page_key = path.name.lower()
        if page_key in seen_pages:
            continue
        seen_pages.add(page_key)
        tables = read_html_tables(path)
        if not tables:
            continue
        report_title = report_title_from_page(path)
        original_doi = doi_from_page(path)

        for table_index, raw_table in enumerate(tables):
            table, columns = table_with_possible_header(raw_table)
            original_cols = [i for i, col in enumerate(columns) if "original" in col.lower()]
            replication_cols = [
                i
                for i, col in enumerate(columns)
                if "our result" in col.lower() or "replication data" in col.lower() or "replication result" in col.lower()
            ]
            if not original_cols or not replication_cols:
                continue
            original_col = original_cols[0]
            replication_col = replication_cols[0]
            for row_index, table_row in table.iterrows():
                if original_col >= len(table_row) or replication_col >= len(table_row):
                    continue
                original_text = clean_text(table_row.iloc[original_col])
                replication_text = clean_text(table_row.iloc[replication_col])
                if not original_text or not replication_text:
                    continue
                d_original, n_original, original_metric = parse_effect_and_n(columns[original_col] + " " + original_text)
                d_replication, n_replication, replication_metric = parse_effect_and_n(
                    columns[replication_col] + " " + replication_text
                )
                if not (
                    np.isfinite(d_original)
                    and np.isfinite(d_replication)
                    and np.isfinite(n_original)
                    and np.isfinite(n_replication)
                ):
                    continue

                outcome = clean_text(table_row.iloc[0])
                pair_id = f"transparent_{slug(path.stem)}_table_{table_index}_row_{row_index}_{slug(outcome)}"
                note = (
                    "Transparent Replications report table row. Reported d values are used directly; "
                    "reported r/rank-biserial effects are converted with d = 2r/sqrt(1-r^2); "
                    "t(df) is converted with d = abs(2*t/sqrt(df)); chi-square rows use phi = sqrt(chi2/N) "
                    "then d = 2phi/sqrt(1-phi^2). This is local mining only; later provenance hardening "
                    "should split multi-stat cells where needed."
                )
                row = {
                    "source_dataset": "Transparent Replications mirrored report tables",
                    "project": "Transparent Replications by Clearer Thinking",
                    "pair_id": pair_id,
                    "original_title": report_title,
                    "replication_title": report_title,
                    "original_doi": original_doi,
                    "replication_doi": "",
                    "outcome": outcome,
                    "D_original": d_original,
                    "N_original": n_original,
                    "D_replication": d_replication,
                    "N_replication": n_replication,
                    "raw_file": f"{rel(path)}#table={table_index};row={row_index};original_col={columns[original_col]};replication_col={columns[replication_col]}",
                    "n_source_file": f"{rel(path)}#table={table_index};row={row_index}",
                    "verbatim_n_text_original": columns[original_col] + " " + original_text,
                    "verbatim_n_text_replication": columns[replication_col] + " " + replication_text,
                    "verbatim_effect_text_original": original_text,
                    "verbatim_effect_text_replication": replication_text,
                    "d_n_transformation_note": note,
                    "match_author": report_title,
                    "candidate_name": "Transparent Replications by Clearer Thinking",
                    "table_index": table_index,
                    "row_index": row_index,
                    "original_metric_parser": original_metric,
                    "replication_metric_parser": replication_metric,
                }
                rows.append(row)

    df = pd.DataFrame(rows)
    promoted_cols = [
        "source_dataset",
        "project",
        "pair_id",
        "original_title",
        "replication_title",
        "original_doi",
        "replication_doi",
        "outcome",
        "D_original",
        "N_original",
        "D_replication",
        "N_replication",
        "raw_file",
        "n_source_file",
        "verbatim_n_text_original",
        "verbatim_n_text_replication",
        "verbatim_effect_text_original",
        "verbatim_effect_text_replication",
        "d_n_transformation_note",
        "match_author",
    ]
    for col in promoted_cols:
        if col not in df.columns:
            df[col] = ""
    return df[promoted_cols].copy(), df.copy()


def clinical_extra_status() -> dict[str, Any]:
    if not CLINICAL_WORKBOOK.exists():
        return {
            "candidate_key": "clinical_highly_cited_workbook",
            "candidate_name": "Clinical highly cited replication workbook",
            "decision": "not_checked_missing_workbook",
            "rows_promoted": 0,
            "notes": "Workbook was not present locally.",
        }
    data = pd.read_excel(CLINICAL_WORKBOOK, sheet_name="Replications")
    risk_counts = data["Risk.Measure"].value_counts(dropna=False).to_dict()
    remaining_orr = int(data["Risk.Measure"].eq("ORR").sum())
    return {
        "candidate_key": "clinical_highly_cited_workbook",
        "candidate_name": "Clinical highly cited replication workbook",
        "decision": "no_extra_rows_without_relaxing_conversion_rule",
        "rows_promoted": 0,
        "notes": (
            f"Existing builder already promotes the {int(data['Risk.Measure'].isin(['OR', 'RR', 'HR']).sum())} "
            f"OR/RR/HR rows. Remaining ORR rows={remaining_orr}; one-arm response rates are not converted to D "
            f"under the current Figure 1 mining rule. Risk measure counts: {risk_counts}."
        ),
    }


def scan_staged_unpromoted() -> pd.DataFrame:
    promoted_keys = {p.name.split("__promoted_pairs.csv")[0] for p in PROMOTED_DIR.glob("*__promoted_pairs.csv")}
    complete_dn_sets = [
        ("D_original", "N_original", "D_replication", "N_replication"),
        ("d_original", "n_original", "d_replication", "n_replication"),
        ("original_d", "original_n", "replication_d", "replication_n"),
        ("D_smaller_N", "N_smaller_N", "D_larger_N", "N_larger_N"),
    ]
    rows: list[dict[str, Any]] = []
    for path in sorted(STAGED_DIR.glob("*__stage.csv")):
        stage_key = path.name.split("__stage.csv")[0]
        try:
            data = pd.read_csv(path)
            read_status = "read_ok"
        except Exception as exc:
            rows.append(
                {
                    "stage_key": stage_key,
                    "stage_path": rel(path),
                    "scan_status": "read_error",
                    "rows": 0,
                    "promoted_or_related": "",
                    "obvious_complete_dn_rows": 0,
                    "effect_nish_column_count": 0,
                    "first_columns": "",
                    "notes": clean_text(exc),
                }
            )
            continue

        columns = list(data.columns)
        obvious_complete_rows = 0
        for colset in complete_dn_sets:
            if not all(col in columns for col in colset):
                continue
            mask = pd.Series(True, index=data.index)
            for col in colset:
                mask &= pd.to_numeric(data[col], errors="coerce").notna()
            obvious_complete_rows = max(obvious_complete_rows, int(mask.sum()))
        promoted_or_related = stage_key in promoted_keys or any(stage_key in key or key in stage_key for key in promoted_keys)
        effect_nish_count = sum(
            any(token in col.lower() for token in ["effect", "cohen", "sample", "_n", " n ", "d_"])
            for col in columns
        )
        rows.append(
            {
                "stage_key": stage_key,
                "stage_path": rel(path),
                "scan_status": read_status,
                "rows": len(data),
                "promoted_or_related": promoted_or_related,
                "obvious_complete_dn_rows": obvious_complete_rows,
                "effect_nish_column_count": effect_nish_count,
                "first_columns": ",".join(columns[:12]),
                "notes": (
                    "No obvious complete D/N columns found."
                    if obvious_complete_rows == 0
                    else "Contains complete D/N-shaped columns; inspect before assuming eligible."
                ),
            }
        )
    return pd.DataFrame(rows)


def main() -> None:
    PROMOTED_DIR.mkdir(parents=True, exist_ok=True)
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)

    transparent_promoted, transparent_audit = build_transparent_rows()
    transparent_promoted.to_csv(TRANSPARENT_PROMOTED, index=False)
    transparent_audit.to_csv(AUDIT_TSV, sep="\t", index=False)
    staged_scan = scan_staged_unpromoted()
    staged_scan.to_csv(STAGED_SCAN_TSV, sep="\t", index=False)

    status_rows = [
        {
            "candidate_key": "transparent_replications_clearer_thinking",
            "candidate_name": "Transparent Replications by Clearer Thinking",
            "decision": "promoted_report_table_rows",
            "rows_promoted": len(transparent_promoted),
            "notes": "Promoted mirrored HTML table rows with parseable original and replication/follow-up D/N.",
        },
        clinical_extra_status(),
        {
            "candidate_key": "hagen_hcsp",
            "candidate_name": "Hagen Cumulative Science Project I",
            "decision": "blocked_access_route",
            "rows_promoted": 0,
            "notes": "Still blocked: mirrored Shiny app's Google Sheet data route is gone/410.",
        },
        {
            "candidate_key": "many_smiles",
            "candidate_name": "Many Smiles Collaboration",
            "decision": "not_promoted_requires_original_benchmark_choice",
            "rows_promoted": 0,
            "notes": "Mirrored replication data do not expose a clean original benchmark effect plus original N table.",
        },
    ]
    pd.DataFrame(status_rows).to_csv(STATUS_TSV, sep="\t", index=False)

    print(f"Wrote {len(transparent_promoted)} Transparent Replications rows: {TRANSPARENT_PROMOTED}")
    print(f"Wrote audit TSV: {AUDIT_TSV}")
    print(f"Wrote status TSV: {STATUS_TSV}")
    print(f"Wrote staged scan TSV: {STAGED_SCAN_TSV}")


if __name__ == "__main__":
    main()
