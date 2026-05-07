#!/usr/bin/env python3
"""Build diagnostic coverage panels for Figure 1-adjacent rows.

This script is intentionally descriptive rather than promotional: it does not
edit the root Figure 1 table. It materializes local row buckets that are useful
for estimating how much of the mirrorable row universe is already in hand.
"""

from __future__ import annotations

import argparse
import math
import re
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "steps/corpus_results/figure1/universe_coverage"
REPORT_PATH = ROOT / "reports/figure1_universe_coverage_diagnostics_2026-05-04.md"

ROOT_TABLE = ROOT / "FIGURE1_REPLICATION_PAIRS.tsv"
KERSCH_STAGE = (
    ROOT
    / "data/derived/replication_pairs/harvest/staged/"
    "kerschbaumer_2020_rheumatology_phase2_phase3__stage.csv"
)
LI_STAGE = (
    ROOT
    / "data/derived/replication_pairs/harvest/staged/"
    "li_2024_pd1_pdl1_phase2_phase3_orr__stage.csv"
)
WILS_STAGE = (
    ROOT
    / "data/derived/replication_pairs/harvest/staged/"
    "wils_2023_ibd_phase2_phase3_response_rates__stage.csv"
)
YING_ROSTER = (
    ROOT
    / "data/derived/replication_pairs/harvest/staged/"
    "ying_2023_pair_roster__stage.csv"
)
RCT_DUP_SCHEMA_SCAN = (
    ROOT
    / "steps/corpus_results/figure1/research_followup_20260504/"
    "rct-duplicate-schema-scan.tsv"
)

ROWS_OUT = OUT_DIR / "figure1-universe-coverage-rows.tsv"
SUMMARY_OUT = OUT_DIR / "figure1-universe-coverage-summary.tsv"
PANEL_OUT = OUT_DIR / "figure1-universe-coverage-panels.png"

CHINN_LOG_OR_TO_D = math.sqrt(3) / math.pi


def rel(path: Path | str | float | None) -> str:
    if path is None:
        return ""
    if isinstance(path, float) and math.isnan(path):
        return ""
    text = str(path)
    if not text:
        return ""
    try:
        return str(Path(text).resolve().relative_to(ROOT))
    except Exception:
        return text


def clean_cell(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and math.isnan(value):
        return ""
    text = str(value).replace("\t", " ").replace("\n", " ").replace("\r", " ")
    return re.sub(r"\s+", " ", text).strip()


def finite(value: Any) -> bool:
    try:
        return math.isfinite(float(value))
    except Exception:
        return False


def slug(text: str) -> str:
    text = re.sub(r"[^A-Za-z0-9]+", "_", text.lower()).strip("_")
    return text[:90] or "row"


def odds_ratio_to_d_from_counts(
    responders_active: float,
    n_active: float,
    responders_control: float,
    n_control: float,
) -> tuple[float, str]:
    non_active = n_active - responders_active
    non_control = n_control - responders_control
    cells = [responders_active, non_active, responders_control, non_control]
    if any(not math.isfinite(cell) for cell in cells) or min(cells) < 0:
        return math.nan, "invalid 2x2 counts"
    warning = ""
    if min(cells) == 0:
        responders_active += 0.5
        non_active += 0.5
        responders_control += 0.5
        non_control += 0.5
        warning = "Haldane-Anscombe 0.5 continuity correction applied"
    odds_ratio = (responders_active * non_control) / (non_active * responders_control)
    if odds_ratio <= 0 or not math.isfinite(odds_ratio):
        return math.nan, "invalid odds ratio from 2x2 counts"
    return abs(math.log(odds_ratio)) * CHINN_LOG_OR_TO_D, warning


def make_record(
    *,
    diagnostic_row_id: str,
    diagnostic_bucket: str,
    diagnostic_panel: str,
    source_family: str,
    source_dataset: str,
    pair_id: str,
    original_label: str = "",
    replication_label: str = "",
    outcome_label: str = "",
    x_value: float | str = "",
    y_value: float | str = "",
    x_axis_label: str = "",
    y_axis_label: str = "",
    n_original: float | str = "",
    n_replication: float | str = "",
    main_figure1_status: str = "",
    effect_family: str = "",
    d_equivalent_tier: str = "",
    d_equivalent_method: str = "",
    is_comparative_effect: str = "",
    is_single_arm: str = "",
    conversion_warning: str = "",
    source_artifact_local_path: str = "",
    notes: str = "",
) -> dict[str, Any]:
    return {
        "diagnostic_row_id": diagnostic_row_id,
        "diagnostic_bucket": diagnostic_bucket,
        "diagnostic_panel": diagnostic_panel,
        "source_family": clean_cell(source_family),
        "source_dataset": clean_cell(source_dataset),
        "pair_id": clean_cell(pair_id),
        "original_label": clean_cell(original_label),
        "replication_label": clean_cell(replication_label),
        "outcome_label": clean_cell(outcome_label),
        "x_value": x_value,
        "y_value": y_value,
        "x_axis_label": clean_cell(x_axis_label),
        "y_axis_label": clean_cell(y_axis_label),
        "N_original": n_original,
        "N_replication": n_replication,
        "main_figure1_status": clean_cell(main_figure1_status),
        "effect_family": clean_cell(effect_family),
        "d_equivalent_tier": clean_cell(d_equivalent_tier),
        "d_equivalent_method": clean_cell(d_equivalent_method),
        "is_comparative_effect": clean_cell(is_comparative_effect),
        "is_single_arm": clean_cell(is_single_arm),
        "conversion_warning": clean_cell(conversion_warning),
        "source_artifact_local_path": clean_cell(source_artifact_local_path),
        "notes": clean_cell(notes),
    }


def load_root_rows() -> tuple[pd.DataFrame, list[dict[str, Any]]]:
    if not ROOT_TABLE.exists():
        raise FileNotFoundError(ROOT_TABLE)
    df = pd.read_csv(ROOT_TABLE, sep="\t")
    records: list[dict[str, Any]] = []
    for _, row in df.iterrows():
        if not (finite(row.get("D_original")) and finite(row.get("D_replication"))):
            continue
        status = clean_cell(row.get("current_plot_rule_status"))
        records.append(
            make_record(
                diagnostic_row_id=f"root_{clean_cell(row.get('figure1_replication_pair_id'))}",
                diagnostic_bucket=(
                    "strict_current_figure1"
                    if status == "included_by_current_figure1_dn_rule"
                    else "dn_available_blocked_by_current_rule"
                ),
                diagnostic_panel=(
                    "A_strict_current_figure1_d_axis"
                    if status == "included_by_current_figure1_dn_rule"
                    else "D_counts_not_main_scatter"
                ),
                source_family=row.get("source_family_label", ""),
                source_dataset=row.get("source_dataset", ""),
                pair_id=row.get("figure1_replication_pair_id", ""),
                original_label=row.get("original_title", ""),
                replication_label=row.get("replication_title", ""),
                outcome_label=row.get("outcome_label", ""),
                x_value=float(row["D_original"]),
                y_value=float(row["D_replication"]),
                x_axis_label="D_original",
                y_axis_label="D_replication",
                n_original=row.get("N_original", ""),
                n_replication=row.get("N_replication", ""),
                main_figure1_status=status,
                effect_family="current_root_d_axis",
                d_equivalent_tier="current_root_value",
                d_equivalent_method="as_recorded_in_root_table",
                is_comparative_effect="mixed_or_source_specific",
                is_single_arm="no_or_not_applicable",
                source_artifact_local_path=row.get("source_artifact_local_path", ""),
                notes=row.get("notes", ""),
            )
        )
    return df, records


def matched_kersch_rows() -> list[dict[str, Any]]:
    if not KERSCH_STAGE.exists():
        return []
    df = pd.read_csv(KERSCH_STAGE)
    active = df.loc[~df["is_placebo_row"].astype(bool)].copy()
    placebos = df.loc[df["is_placebo_row"].astype(bool)].copy()
    records: list[dict[str, Any]] = []
    for _, row in active.iterrows():
        candidates = placebos.loc[
            placebos["disease"].eq(row["disease"])
            & placebos["endpoint"].eq(row["endpoint"])
            & placebos["family_key"].eq(row["family_key"])
            & placebos["background_key"].eq(row["background_key"])
            & placebos["phase2_study_key"].eq(row["phase2_study_key"])
            & placebos["phase3_study_key"].eq(row["phase3_study_key"])
        ].copy()
        if candidates.empty:
            candidates = placebos.loc[
                placebos["disease"].eq(row["disease"])
                & placebos["endpoint"].eq(row["endpoint"])
                & placebos["family_key"].eq(row["family_key"])
                & placebos["background_key"].eq(row["background_key"])
                & placebos["phase3_study_key"].eq(row["phase3_study_key"])
            ].copy()
        if candidates.empty:
            continue
        placebo = candidates.iloc[0]
        d_original, warn_original = odds_ratio_to_d_from_counts(
            float(row["phase2_responders"]),
            float(row["phase2_n"]),
            float(placebo["phase2_responders"]),
            float(placebo["phase2_n"]),
        )
        d_replication, warn_replication = odds_ratio_to_d_from_counts(
            float(row["phase3_responders"]),
            float(row["phase3_n"]),
            float(placebo["phase3_responders"]),
            float(placebo["phase3_n"]),
        )
        if not (finite(d_original) and finite(d_replication)):
            continue
        n_original = float(row["phase2_n"]) + float(placebo["phase2_n"])
        n_replication = float(row["phase3_n"]) + float(placebo["phase3_n"])
        pair = (
            f"{row['disease']}|{row['regimen']}|{row['endpoint']}|"
            f"{row['phase2_study_key']}|{row['phase3_study_key']}"
        )
        main_status = (
            "partly_present_in_root_acr20_promoted_subset"
            if row["endpoint"] == "ACR20"
            else "diagnostic_extension_not_in_strict_root"
        )
        warning = "; ".join(w for w in [warn_original, warn_replication] if w)
        records.append(
            make_record(
                diagnostic_row_id=f"kersch_{slug(pair)}",
                diagnostic_bucket="clinical_binary_comparator_d_equivalent",
                diagnostic_panel="B_clinical_binary_d_equivalent",
                source_family="Clinical phase II to phase III pairs",
                source_dataset="kerschbaumer_2020_rheumatology_phase2_phase3",
                pair_id=pair,
                original_label=clean_cell(row["phase2_study"]),
                replication_label=clean_cell(row["phase3_study"]),
                outcome_label=clean_cell(row["endpoint"]),
                x_value=d_original,
                y_value=d_replication,
                x_axis_label="D*_phase2_active_vs_placebo",
                y_axis_label="D*_phase3_active_vs_placebo",
                n_original=n_original,
                n_replication=n_replication,
                main_figure1_status=main_status,
                effect_family="binary_comparative",
                d_equivalent_tier="2_log_or_to_d_equivalent",
                d_equivalent_method="active-vs-placebo 2x2 odds ratio converted using log(OR)*sqrt(3)/pi",
                is_comparative_effect="yes",
                is_single_arm="no",
                conversion_warning=warning,
                source_artifact_local_path=row.get("raw_file", ""),
                notes=(
                    "Diagnostic all-endpoint extension from staged Kerschbaumer table. "
                    "The current root table promoted only a strict ACR20 subset."
                ),
            )
        )
    return records


def native_response_rows() -> list[dict[str, Any]]:
    specs = [
        (
            LI_STAGE,
            "li_2024_pd1_pdl1_phase2_phase3_orr",
            "Clinical one-arm oncology ORR",
            "one_arm_or_treatment_arm_native_response",
            "one-arm ORR logit; not a treatment-vs-control effect",
            "yes",
        ),
        (
            WILS_STAGE,
            "wils_2023_ibd_phase2_phase3_response_rates",
            "IBD treatment-arm response rates",
            "one_arm_or_treatment_arm_native_response",
            "treatment-arm response-rate logit; lacks paired control arm",
            "yes",
        ),
    ]
    records: list[dict[str, Any]] = []
    for path, dataset, family, bucket, warning, single_arm in specs:
        if not path.exists():
            continue
        df = pd.read_csv(path)
        for _, row in df.iterrows():
            if not (finite(row.get("native_effect_original")) and finite(row.get("native_effect_replication"))):
                continue
            records.append(
                make_record(
                    diagnostic_row_id=f"native_{dataset}_{slug(clean_cell(row.get('pair_id', 'row')))}",
                    diagnostic_bucket=bucket,
                    diagnostic_panel="C_native_response_signal_not_d_axis",
                    source_family=family,
                    source_dataset=dataset,
                    pair_id=row.get("pair_id", ""),
                    original_label=row.get("phase2_study", ""),
                    replication_label=row.get("phase3_study", ""),
                    outcome_label=row.get("outcome", ""),
                    x_value=float(row["native_effect_original"]),
                    y_value=float(row["native_effect_replication"]),
                    x_axis_label=clean_cell(row.get("native_effect_metric", "native_logit_original")),
                    y_axis_label=clean_cell(row.get("native_effect_metric", "native_logit_replication")),
                    n_original=row.get("N_original", ""),
                    n_replication=row.get("N_replication", ""),
                    main_figure1_status="excluded_native_response_no_defensible_d_axis",
                    effect_family="native_response_rate",
                    d_equivalent_tier="5_native_only_do_not_use_in_main_d_panel",
                    d_equivalent_method="native logit response rate retained for diagnostic signal only",
                    is_comparative_effect="no",
                    is_single_arm=single_arm,
                    conversion_warning=warning,
                    source_artifact_local_path=row.get("raw_file", ""),
                    notes=row.get("analytic_status", ""),
                )
            )
    return records


def nonplottable_counts() -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    if YING_ROSTER.exists():
        df = pd.read_csv(YING_ROSTER)
        for _, row in df.iterrows():
            records.append(
                make_record(
                    diagnostic_row_id=f"ying_roster_{clean_cell(row.get('pair_id'))}",
                    diagnostic_bucket="roster_only_no_public_effect_values",
                    diagnostic_panel="D_counts_not_main_scatter",
                    source_family="Ying 2023 pilot-full-scale trials",
                    source_dataset="ying_2023_pair_roster",
                    pair_id=row.get("pair_id", ""),
                    original_label=row.get("pilot_citation_text", ""),
                    replication_label=row.get("full_scale_citation_text", ""),
                    main_figure1_status="not_plottable_public_roster_only",
                    effect_family="roster_only",
                    d_equivalent_tier="not_applicable",
                    d_equivalent_method="no public effect/N table exposed in roster",
                    is_comparative_effect="unknown",
                    is_single_arm="unknown",
                    source_artifact_local_path=row.get("public_source_path", ""),
                    notes=row.get("analytic_row_status", ""),
                )
            )
    if RCT_DUP_SCHEMA_SCAN.exists():
        scan = pd.read_csv(RCT_DUP_SCHEMA_SCAN, sep="\t")
        effect_no_n = scan.loc[
            scan["has_effect_like_columns"].astype(bool)
            & ~scan["has_n_like_columns"].astype(bool)
        ].copy()
        if not effect_no_n.empty:
            max_rows = int(effect_no_n["rows"].max())
            records.append(
                make_record(
                    diagnostic_row_id="rct_duplicate_public_result_tables_effect_only",
                    diagnostic_bucket="effect_values_present_no_public_n_columns",
                    diagnostic_panel="D_counts_not_main_scatter",
                    source_family="RCT-DUPLICATE / HTE in RWE",
                    source_dataset="rct_duplicate_public_result_tables",
                    pair_id="public_result_rows_max_unique_file_count",
                    main_figure1_status="not_plottable_missing_public_N",
                    effect_family="hazard_ratio_or_ratio_measure",
                    d_equivalent_tier="not_applicable_without_N",
                    d_equivalent_method="effect estimates found in public CSVs; N columns absent",
                    is_comparative_effect="yes",
                    is_single_arm="no",
                    source_artifact_local_path="; ".join(effect_no_n["local_path"].map(clean_cell)),
                    notes=f"Count represents the largest public effect-like result file ({max_rows} rows), not the sum across duplicate/corrected files.",
                )
            )
            records[-1]["row_count_override"] = max_rows
    return records


def build_summary(rows: pd.DataFrame, root: pd.DataFrame) -> pd.DataFrame:
    included = int(root["current_plot_rule_status"].eq("included_by_current_figure1_dn_rule").sum())
    blocked = int(root["current_plot_rule_status"].eq("excluded_by_current_figure1_dn_rule").sum())
    kersch = rows.loc[rows["diagnostic_bucket"].eq("clinical_binary_comparator_d_equivalent")].copy()
    kersch_root_count = int(root["source_family_label"].eq("Clinical phase II to phase III pairs").sum())
    kersch_extra = max(int(len(kersch)) - kersch_root_count, 0)
    native = int(rows["diagnostic_bucket"].eq("one_arm_or_treatment_arm_native_response").sum())
    roster = int(rows["diagnostic_bucket"].eq("roster_only_no_public_effect_values").sum())
    rct_rows = rows.loc[rows["diagnostic_bucket"].eq("effect_values_present_no_public_n_columns")]
    rct_effect_only = 0
    if not rct_rows.empty and "row_count_override" in rct_rows.columns:
        rct_effect_only = int(pd.to_numeric(rct_rows["row_count_override"], errors="coerce").max())

    local_row_universe = included + blocked + kersch_extra + native + roster + rct_effect_only
    strict_dn_any = included + blocked
    diagnostic_xy = included + kersch_extra + native
    rows_out = [
        {
            "bucket": "strict_current_figure1_included",
            "rows": included,
            "percent_of_local_observable_row_universe": pct(included, local_row_universe),
            "definition": "Rows included by the current strict Figure 1 D/N rule.",
            "use_in_main": "Figure 1A",
        },
        {
            "bucket": "strict_dn_available_but_blocked",
            "rows": blocked,
            "percent_of_local_observable_row_universe": pct(blocked, local_row_universe),
            "definition": "Root rows with D/N values that fail the current plot rule, usually because the larger-N side is not the replication/follow-up side or another gate blocks inclusion.",
            "use_in_main": "No; audit/robustness only",
        },
        {
            "bucket": "additional_comparative_binary_d_equivalent_rows",
            "rows": kersch_extra,
            "percent_of_local_observable_row_universe": pct(kersch_extra, local_row_universe),
            "definition": "Extra locally staged comparative binary rows that can be mapped to D* by active-vs-placebo odds ratio conversion but are not already represented by current root-table clinical phase II/III rows.",
            "use_in_main": "Candidate Figure 1B diagnostic, not Figure 1A",
        },
        {
            "bucket": "native_response_rate_rows_not_d_axis",
            "rows": native,
            "percent_of_local_observable_row_universe": pct(native, local_row_universe),
            "definition": "Local rows with native response-rate/logit signal and N on both sides, but no defensible treatment-effect D conversion.",
            "use_in_main": "Supplement/native-scale diagnostic only",
        },
        {
            "bucket": "roster_only_pairs_no_public_effect_table",
            "rows": roster,
            "percent_of_local_observable_row_universe": pct(roster, local_row_universe),
            "definition": "Local pilot/full-scale pair roster rows where public bytes identify linked pairs but do not expose effect and N values.",
            "use_in_main": "No; denominator/context only",
        },
        {
            "bucket": "effect_values_present_no_public_n_columns",
            "rows": rct_effect_only,
            "percent_of_local_observable_row_universe": pct(rct_effect_only, local_row_universe),
            "definition": "Public result rows with effect estimates but no N columns, counted once by the largest public result table to avoid duplicate corrected-file inflation.",
            "use_in_main": "No; needs N acquisition",
        },
        {
            "bucket": "local_observable_row_universe",
            "rows": local_row_universe,
            "percent_of_local_observable_row_universe": 100.0 if local_row_universe else 0.0,
            "definition": "Working denominator for rows already mirrored/staged locally at some meaningful grain; not a science-wide estimate.",
            "use_in_main": "Denominator diagnostic",
        },
        {
            "bucket": "strict_dn_any_root_status",
            "rows": strict_dn_any,
            "percent_of_local_observable_row_universe": pct(strict_dn_any, local_row_universe),
            "definition": "All current root rows with D/N values, whether included or excluded by the current Figure 1 rule.",
            "use_in_main": "Main plus excluded audit",
        },
        {
            "bucket": "diagnostic_xy_rows_strict_plus_extra_plus_native",
            "rows": diagnostic_xy,
            "percent_of_local_observable_row_universe": pct(diagnostic_xy, local_row_universe),
            "definition": "Rows that can be shown in an x/y panel using either D, D*, or native logit response units.",
            "use_in_main": "Figure plus diagnostic panels",
        },
    ]
    return pd.DataFrame(rows_out)


def pct(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 0.0
    return round(100 * numerator / denominator, 1)


def plot_panels(rows: pd.DataFrame, summary: pd.DataFrame) -> None:
    plt.style.use("default")
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    ax_a, ax_b, ax_c, ax_d = axes.flatten()

    # Panel A: strict current D-axis rows.
    a = rows.loc[
        rows["diagnostic_panel"].eq("A_strict_current_figure1_d_axis")
        & pd.to_numeric(rows["x_value"], errors="coerce").gt(0)
        & pd.to_numeric(rows["y_value"], errors="coerce").gt(0)
    ].copy()
    ax_a.scatter(a["x_value"].astype(float), a["y_value"].astype(float), s=10, alpha=0.30, color="#2F6F9F", edgecolors="none")
    add_identity(ax_a, a)
    ax_a.set_xscale("log")
    ax_a.set_yscale("log")
    ax_a.set_title("A. Strict current D/N rows")
    ax_a.set_xlabel("D original")
    ax_a.set_ylabel("D replication/follow-up")
    ax_a.text(0.02, 0.98, f"plotted n = {len(a):,}", transform=ax_a.transAxes, va="top", fontsize=10)

    # Panel B: clinical/binary D-equivalent rows.
    b = rows.loc[
        rows["diagnostic_panel"].eq("B_clinical_binary_d_equivalent")
        & pd.to_numeric(rows["x_value"], errors="coerce").gt(0)
        & pd.to_numeric(rows["y_value"], errors="coerce").gt(0)
    ].copy()
    colors = {"ACR20": "#D95F02", "ACR50": "#1B9E77", "ACR70": "#7570B3"}
    for outcome, sub in b.groupby("outcome_label"):
        ax_b.scatter(
            sub["x_value"].astype(float),
            sub["y_value"].astype(float),
            s=28,
            alpha=0.70,
            label=outcome,
            color=colors.get(outcome, "#666666"),
            edgecolors="none",
        )
    add_identity(ax_b, b)
    ax_b.set_xscale("log")
    ax_b.set_yscale("log")
    ax_b.set_title("B. Comparative binary D-equivalent")
    ax_b.set_xlabel("D* original / phase II")
    ax_b.set_ylabel("D* replication / phase III")
    ax_b.legend(frameon=False, fontsize=8)
    extra = int(
        summary.loc[
            summary["bucket"].eq("additional_comparative_binary_d_equivalent_rows"),
            "rows",
        ].iloc[0]
    )
    ax_b.text(0.02, 0.98, f"plotted n = {len(b):,}\noutside root = {extra:,}", transform=ax_b.transAxes, va="top", fontsize=10)

    # Panel C: native response signal only.
    c = rows.loc[
        rows["diagnostic_panel"].eq("C_native_response_signal_not_d_axis")
        & pd.to_numeric(rows["x_value"], errors="coerce").notna()
        & pd.to_numeric(rows["y_value"], errors="coerce").notna()
    ].copy()
    native_colors = {
        "Clinical one-arm oncology ORR": "#E7298A",
        "IBD treatment-arm response rates": "#66A61E",
    }
    for family, sub in c.groupby("source_family"):
        ax_c.scatter(
            sub["x_value"].astype(float),
            sub["y_value"].astype(float),
            s=28,
            alpha=0.70,
            label=family,
            color=native_colors.get(family, "#666666"),
            edgecolors="none",
        )
    if not c.empty:
        vals = pd.concat([c["x_value"].astype(float), c["y_value"].astype(float)])
        lo, hi = float(vals.min()), float(vals.max())
        pad = (hi - lo) * 0.05 if hi > lo else 0.5
        ax_c.plot([lo - pad, hi + pad], [lo - pad, hi + pad], color="#555555", linewidth=1, linestyle="--")
        ax_c.set_xlim(lo - pad, hi + pad)
        ax_c.set_ylim(lo - pad, hi + pad)
    ax_c.set_title("C. Native response signal only")
    ax_c.set_xlabel("Native logit original / phase II")
    ax_c.set_ylabel("Native logit replication / phase III")
    ax_c.legend(frameon=False, fontsize=8)
    ax_c.text(0.02, 0.98, f"n = {len(c):,}", transform=ax_c.transAxes, va="top", fontsize=10)

    # Panel D: row bucket counts.
    plot_buckets = [
        ("strict_current_figure1_included", "Strict included"),
        ("strict_dn_available_but_blocked", "D/N blocked"),
        ("additional_comparative_binary_d_equivalent_rows", "Extra D*"),
        ("native_response_rate_rows_not_d_axis", "Native rate"),
        ("roster_only_pairs_no_public_effect_table", "Roster only"),
        ("effect_values_present_no_public_n_columns", "Effect, no N"),
    ]
    counts = []
    labels = []
    for bucket, label in plot_buckets:
        row = summary.loc[summary["bucket"].eq(bucket)]
        counts.append(int(row["rows"].iloc[0]) if not row.empty else 0)
        labels.append(label)
    ax_d.barh(labels, counts, color=["#2F6F9F", "#9AA5B1", "#D95F02", "#A6761D", "#7570B3", "#E7298A"])
    ax_d.set_title("D. Local row buckets")
    ax_d.set_xlabel("Rows")
    for idx, count in enumerate(counts):
        ax_d.text(count + max(counts) * 0.01, idx, f"{count:,}", va="center", fontsize=9)
    ax_d.set_xlim(0, max(counts) * 1.18 if counts else 1)

    fig.suptitle("Figure 1 Coverage Diagnostics From Local Mirrored/Staged Rows", fontsize=14)
    fig.tight_layout(rect=[0, 0, 1, 0.97])
    fig.savefig(PANEL_OUT, dpi=220)
    plt.close(fig)


def add_identity(ax: plt.Axes, df: pd.DataFrame) -> None:
    if df.empty:
        return
    values = pd.concat([df["x_value"].astype(float), df["y_value"].astype(float)])
    values = values[np.isfinite(values) & (values > 0)]
    if values.empty:
        return
    lo = float(values.quantile(0.01))
    hi = float(values.quantile(0.99))
    lo = max(lo, float(values.min()))
    hi = max(hi, lo * 1.1)
    ax.plot([lo, hi], [lo, hi], color="#555555", linewidth=1, linestyle="--")


def write_report(rows: pd.DataFrame, summary: pd.DataFrame) -> None:
    lookup = {row["bucket"]: row for _, row in summary.iterrows()}

    def count(bucket: str) -> int:
        return int(lookup[bucket]["rows"])

    def percent(bucket: str) -> float:
        return float(lookup[bucket]["percent_of_local_observable_row_universe"])

    local_total = count("local_observable_row_universe")
    strict = count("strict_current_figure1_included")
    blocked = count("strict_dn_available_but_blocked")
    extra = count("additional_comparative_binary_d_equivalent_rows")
    native = count("native_response_rate_rows_not_d_axis")
    roster = count("roster_only_pairs_no_public_effect_table")
    effect_no_n = count("effect_values_present_no_public_n_columns")
    strict_any = count("strict_dn_any_root_status")

    lines = [
        "# Figure 1 Universe Coverage Diagnostics",
        "",
        f"Generated by `scripts/build_figure1_universe_coverage_diagnostics.py` on 2026-05-04.",
        "",
        "## Definitions",
        "",
        "- **Strict Figure 1 row**: a row included by the current D/N rule in `FIGURE1_REPLICATION_PAIRS.tsv`.",
        "- **D/N available but blocked**: a root-table row with numeric D and N values that does not satisfy the current inclusion rule.",
        "- **D-equivalent row**: a comparative binary endpoint converted to a standardized latent-scale effect using `log(OR) * sqrt(3) / pi`. These are candidates for a separate Figure 1B-style panel, not direct Figure 1A evidence.",
        "- **Native response signal**: a row with original/follow-up response rates and N on both sides, retained in native logit units because it is not a treatment-effect D.",
        "- **Local observable row universe**: a bookkeeping denominator for rows already mirrored or staged locally at some meaningful grain. It is not a science-wide denominator.",
        "",
        "## Current Local Denominator",
        "",
        f"- Local observable row universe: **{local_total:,} rows**.",
        f"- Strict current Figure 1 included rows: **{strict:,}** ({percent('strict_current_figure1_included')}%).",
        f"- Root rows with D/N values whether included or blocked: **{strict_any:,}** ({percent('strict_dn_any_root_status')}%).",
        f"- D/N rows blocked by the current plot rule: **{blocked:,}** ({percent('strict_dn_available_but_blocked')}%).",
        f"- Additional comparative binary D-equivalent rows from local staged data: **{extra:,}** ({percent('additional_comparative_binary_d_equivalent_rows')}%).",
        f"- Native response-rate/logit rows not suitable for the D axis: **{native:,}** ({percent('native_response_rate_rows_not_d_axis')}%).",
        f"- Roster-only linked pairs without public effect/N values: **{roster:,}** ({percent('roster_only_pairs_no_public_effect_table')}%).",
        f"- Effect-value rows with no public N columns: **{effect_no_n:,}** ({percent('effect_values_present_no_public_n_columns')}%).",
        "",
        "## Interpretation",
        "",
        "The current strict Figure 1 table captures a majority of the locally observable row universe, but not all locally meaningful source objects. The main lost mass is not a hidden set of clean D/N rows; it is mostly rows that either fail the current inclusion rule, expose only native response rates, expose only pair rosters, or expose effect estimates without N.",
        "",
        "A separate Figure 1B-style diagnostic is defensible for comparative binary endpoints where both sides have active/control counts. The local Kerschbaumer rheumatology stage file has enough counts to compute D-equivalent values for ACR20, ACR50, and ACR70. The root table currently includes a strict promoted ACR20 subset; the diagnostic panel shows all locally matched endpoints, and the summary counts only rows not already represented by current root-table clinical phase II/III rows as extra D-equivalent coverage.",
        "",
        "One-arm ORR and treatment-arm-only response rates should remain out of the main D-equivalent panel. The diagnostic keeps them in native logit units so the data are visible without pretending they are treatment-effect D values.",
        "",
        "## Generated Artifacts",
        "",
        f"- Row-level diagnostic table: `{rel(ROWS_OUT)}`",
        f"- Bucket summary: `{rel(SUMMARY_OUT)}`",
        f"- Subplot image: `{rel(PANEL_OUT)}`",
    ]
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--replace", action="store_true", help="Overwrite existing diagnostic artifacts.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for path in [ROWS_OUT, SUMMARY_OUT, PANEL_OUT, REPORT_PATH]:
        if path.exists() and not args.replace:
            raise SystemExit(f"{path} exists; pass --replace to overwrite")

    root, records = load_root_rows()
    records.extend(matched_kersch_rows())
    records.extend(native_response_rows())
    records.extend(nonplottable_counts())
    rows = pd.DataFrame(records)
    rows.to_csv(ROWS_OUT, sep="\t", index=False)
    summary = build_summary(rows, root)
    summary.to_csv(SUMMARY_OUT, sep="\t", index=False)
    plot_panels(rows, summary)
    write_report(rows, summary)

    print(f"Wrote {len(rows):,} diagnostic rows -> {rel(ROWS_OUT)}")
    print(f"Wrote summary -> {rel(SUMMARY_OUT)}")
    print(f"Wrote panel image -> {rel(PANEL_OUT)}")
    print(f"Wrote report -> {rel(REPORT_PATH)}")


if __name__ == "__main__":
    main()
