#!/usr/bin/env python3
"""Summarize where Figure 1 replication-like material was retained or lost.

This is an accounting layer, not an extraction or promotion step. It combines
the strict Figure 1 pair table, alternate-route diagnostics, raw-viability
summaries, and corpus/source intake table so that row-grain objects and broader
source leads are counted separately.
"""

from __future__ import annotations

import argparse
import math
import re
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "steps/corpus_results/figure1/coverage_loss_accounting"
ROW_OUT = OUT_DIR / "figure1-row-disposition.tsv"
SOURCE_OUT = OUT_DIR / "figure1-source-coverage-status.tsv"
STAGE_OUT = OUT_DIR / "figure1-coverage-loss-stages.tsv"
PLOT_OUT = OUT_DIR / "figure1-coverage-loss-bars.png"
REPORT_OUT = ROOT / "reports/figure1_coverage_loss_accounting_2026-05-04.md"

ROOT_TABLE = ROOT / "FIGURE1_REPLICATION_PAIRS.tsv"
CORPORA_TABLE = ROOT / "CORPORA_AND_DATABASES.tsv"
UNIVERSE_SUMMARY = OUT_DIR.parent / "universe_coverage/figure1-universe-coverage-summary.tsv"
UNIVERSE_ROWS = OUT_DIR.parent / "universe_coverage/figure1-universe-coverage-rows.tsv"
RECHECK_ROWS = OUT_DIR.parent / "alternate_route_recheck/figure1-rejected-alternate-route-recheck.tsv"
RECHECK_SUMMARY = OUT_DIR.parent / "alternate_route_recheck/figure1-rejected-alternate-route-summary.tsv"
RAW_VIABILITY = OUT_DIR.parent / "figure1-raw-viability-summary.tsv"


def clean(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and math.isnan(value):
        return ""
    return re.sub(r"\s+", " ", str(value).replace("\t", " ")).strip()


def read_tsv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path, sep="\t")


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except Exception:
        return str(path)


def pct(numerator: int | float, denominator: int | float) -> float:
    if not denominator:
        return 0.0
    return round(float(numerator) / float(denominator) * 100.0, 1)


def int_bucket(summary: pd.DataFrame, bucket: str) -> int:
    if summary.empty:
        return 0
    row = summary.loc[summary["bucket"].eq(bucket)]
    if row.empty:
        return 0
    return int(row["rows"].iloc[0])


def counted_for_candidate(recheck: pd.DataFrame, candidate_key: str) -> int:
    if recheck.empty:
        return 0
    rows = recheck.loc[recheck["candidate_key"].eq(candidate_key)]
    if rows.empty:
        return 0
    return int(pd.to_numeric(rows["counted_evidence_row_count"], errors="coerce").fillna(0).sum())


def counted_for_route(recheck_summary: pd.DataFrame, decision: str) -> int:
    if recheck_summary.empty:
        return 0
    rows = recheck_summary.loc[recheck_summary["alternate_route_decision"].eq(decision)]
    if rows.empty:
        return 0
    return int(pd.to_numeric(rows["counted_evidence_rows"], errors="coerce").fillna(0).sum())


def source_count_where(df: pd.DataFrame, column: str, value: str) -> int:
    if df.empty or column not in df.columns:
        return 0
    return int(df[column].fillna("").astype(str).eq(value).sum())


def source_count_contains(df: pd.DataFrame, column: str, needle: str) -> int:
    if df.empty or column not in df.columns:
        return 0
    return int(df[column].fillna("").astype(str).str.contains(needle, regex=False).sum())


def build_row_disposition(
    universe_summary: pd.DataFrame,
    recheck: pd.DataFrame,
    recheck_summary: pd.DataFrame,
) -> tuple[pd.DataFrame, dict[str, int]]:
    strict_included = int_bucket(universe_summary, "strict_current_figure1_included")
    strict_blocked = int_bucket(universe_summary, "strict_dn_available_but_blocked")
    d_equiv = int_bucket(universe_summary, "additional_comparative_binary_d_equivalent_rows")
    roster_only = int_bucket(universe_summary, "roster_only_pairs_no_public_effect_table")
    effect_no_n = int_bucket(universe_summary, "effect_values_present_no_public_n_columns")

    native_from_recheck = counted_for_route(recheck_summary, "route_to_native_effect_diagnostic_worklist")
    native = native_from_recheck or int_bucket(universe_summary, "native_response_rate_rows_not_d_axis")
    parsed_no_values = counted_for_candidate(recheck, "lead_harvest:psa_006_trolley")
    duplicate_risk = counted_for_candidate(recheck, "forrt_reversals")

    rows = [
        {
            "disposition_id": "figure1a_strict_direct_d_axis",
            "disposition_label": "Strict Figure 1A direct D/N rows",
            "row_count": strict_included,
            "route": "figure1a_strict_current_d_axis",
            "usable_for": "main Figure 1A",
            "has_pair_mapping": "yes",
            "has_effect": "yes",
            "has_n": "yes",
            "has_common_axis": "yes",
            "definition": "Rows included by the current strict Figure 1 D/N plot rule.",
            "next_action": "Promote into source_result/source_result_support when provenance hardening resumes.",
            "source_basis": rel(UNIVERSE_SUMMARY),
        },
        {
            "disposition_id": "strict_dn_blocked_by_current_rule",
            "disposition_label": "D/N rows blocked by current Figure 1A rule",
            "row_count": strict_blocked,
            "route": "coverage_denominator_or_rule_audit",
            "usable_for": "denominator, rule audit, robustness checks",
            "has_pair_mapping": "yes",
            "has_effect": "yes",
            "has_n": "yes",
            "has_common_axis": "yes, but not current-rule eligible",
            "definition": "Root rows have D_original, D_replication, N_original, and N_replication but fail a current plot gate.",
            "next_action": "Keep out of Figure 1A unless the failed gate is intentionally changed.",
            "source_basis": rel(UNIVERSE_SUMMARY),
        },
        {
            "disposition_id": "figure1b_binary_d_equivalent",
            "disposition_label": "Comparative binary rows with D-equivalent conversion",
            "row_count": d_equiv,
            "route": "figure1b_clinical_binary_d_equivalent",
            "usable_for": "Figure 1B diagnostic",
            "has_pair_mapping": "yes",
            "has_effect": "yes",
            "has_n": "yes",
            "has_common_axis": "D-equivalent tier, not direct D",
            "definition": "Active/control count rows can be converted by log(OR) * sqrt(3) / pi.",
            "next_action": "Use only with conversion-tier fields and caption caveats.",
            "source_basis": f"{rel(UNIVERSE_SUMMARY)} | {rel(RECHECK_SUMMARY)}",
        },
        {
            "disposition_id": "native_effect_retention",
            "disposition_label": "Native-effect rows not on D axis",
            "row_count": native,
            "route": "native_scale_retention_panel_or_appendix",
            "usable_for": "native-scale diagnostic, not common-D plot",
            "has_pair_mapping": "yes",
            "has_effect": "yes",
            "has_n": "yes",
            "has_common_axis": "no",
            "definition": "Response-rate or similar rows with original/follow-up values and N but no defensible D conversion.",
            "next_action": "Retain separately; do not mix into D or D-equivalent panels.",
            "source_basis": rel(RECHECK_SUMMARY),
        },
        {
            "disposition_id": "roster_only_denominator",
            "disposition_label": "Pair roster only, public values unavailable",
            "row_count": roster_only,
            "route": "source_object_coverage_denominator",
            "usable_for": "coverage denominator only",
            "has_pair_mapping": "yes",
            "has_effect": "no",
            "has_n": "no",
            "has_common_axis": "no",
            "definition": "Rows identify original/follow-up linkage but public/local bytes do not expose effect and N values.",
            "next_action": "Do not mine further unless public value files appear or policy changes to author-request data.",
            "source_basis": rel(UNIVERSE_SUMMARY),
        },
        {
            "disposition_id": "effect_present_missing_n",
            "disposition_label": "Effect present, N missing",
            "row_count": effect_no_n,
            "route": "missing_n_repair_worklist",
            "usable_for": "repair queue and denominator",
            "has_pair_mapping": "yes",
            "has_effect": "yes",
            "has_n": "no",
            "has_common_axis": "not until N is recovered",
            "definition": "Public result rows expose effect-like values but no original/follow-up sample-size columns.",
            "next_action": "Recover N from source articles, appendices, or project owners before plotting.",
            "source_basis": rel(UNIVERSE_SUMMARY),
        },
        {
            "disposition_id": "parsed_row_grain_no_effect_n",
            "disposition_label": "Parsed row grain, no copied effect/N evidence",
            "row_count": parsed_no_values,
            "route": "parser_repair_or_demotion",
            "usable_for": "denominator with parser caveat",
            "has_pair_mapping": "unclear",
            "has_effect": "no",
            "has_n": "no",
            "has_common_axis": "no",
            "definition": "A parser found row-grain records, but current extraction did not copy effect or N evidence.",
            "next_action": "Repair parser signals or demote; do not treat as result rows.",
            "source_basis": rel(RECHECK_ROWS),
        },
        {
            "disposition_id": "duplicate_risk_dn_candidate",
            "disposition_label": "D/N-looking rows with duplicate risk",
            "row_count": duplicate_risk,
            "route": "dedupe_before_any_plot_route",
            "usable_for": "coverage denominator until deduped",
            "has_pair_mapping": "yes",
            "has_effect": "yes",
            "has_n": "yes",
            "has_common_axis": "likely, but not validated",
            "definition": "Candidate D/N-looking rows exist, but they overlap heavily with already harvested sources.",
            "next_action": "Dedupe against FReD/current rows before promotion.",
            "source_basis": rel(RECHECK_ROWS),
        },
    ]

    accounted = int(sum(row["row_count"] for row in rows))
    for row in rows:
        row["percent_of_accounted_row_grain_universe"] = pct(row["row_count"], accounted)

    metrics = {
        "accounted_row_grain_universe": accounted,
        "strict_figure1a_rows": strict_included,
        "strict_dn_blocked_rows": strict_blocked,
        "strict_dn_any_root_rows": strict_included + strict_blocked,
        "figure1b_d_equivalent_rows": d_equiv,
        "native_retention_rows": native,
        "quantitative_or_native_xy_rows": strict_included + d_equiv + native,
        "value_bearing_any_axis_or_blocked_rows": strict_included + strict_blocked + d_equiv + native,
        "denominator_or_repair_only_rows": roster_only + effect_no_n + parsed_no_values + duplicate_risk,
    }
    return pd.DataFrame(rows), metrics


def build_source_status(
    corpora: pd.DataFrame,
    raw_viability: pd.DataFrame,
    recheck: pd.DataFrame,
    recheck_summary: pd.DataFrame,
) -> pd.DataFrame:
    routed_records = 0
    no_route_records = 0
    if not recheck.empty:
        no_route_mask = recheck["alternate_route_decision"].eq("remain_context_or_rejected_no_alternate_subplot")
        routed_records = int((~no_route_mask).sum())
        no_route_records = int(no_route_mask.sum())

    mapped_raw_rows = 0
    if (
        not raw_viability.empty
        and "figure1_viability" in raw_viability.columns
        and "rows_with_effect_n_and_pair_context" in raw_viability.columns
    ):
        mapped_raw_rows = int(
            pd.to_numeric(
                raw_viability.loc[
                    raw_viability["figure1_viability"].eq("candidate_for_figure1_mapping"),
                    "rows_with_effect_n_and_pair_context",
                ],
                errors="coerce",
            )
            .fillna(0)
            .sum()
        )

    rows = [
        {
            "status_bucket": "root_source_records_all",
            "source_record_count": len(corpora),
            "row_count_if_applicable": "",
            "definition": "All consolidated source/corpus/database records in CORPORA_AND_DATABASES.tsv.",
            "accounting_use": "source-level universe only; not a row denominator",
        },
        {
            "status_bucket": "root_source_records_figure1_relevant_yes",
            "source_record_count": source_count_where(corpora, "figure1_replication_relevance", "yes"),
            "row_count_if_applicable": "",
            "definition": "Records explicitly marked relevant to the Figure 1 replication-pair universe.",
            "accounting_use": "source-level coverage scope",
        },
        {
            "status_bucket": "metadata_only_search_hits",
            "source_record_count": source_count_contains(corpora, "blocker_codes", "metadata_only_search_hit"),
            "row_count_if_applicable": "",
            "definition": "Search hits retained for recall accounting but not value-bearing source objects.",
            "accounting_use": "loss reason: no local/public value object",
        },
        {
            "status_bucket": "parser_not_implemented",
            "source_record_count": source_count_contains(corpora, "blocker_codes", "parser_not_implemented"),
            "row_count_if_applicable": "",
            "definition": "Records with known or suspected data but no implemented parser path.",
            "accounting_use": "technical repair queue",
        },
        {
            "status_bucket": "conversion_policy_missing",
            "source_record_count": source_count_contains(corpora, "blocker_codes", "conversion_policy_missing"),
            "row_count_if_applicable": "",
            "definition": "Records whose native metrics need a conversion decision before any shared-axis plot use.",
            "accounting_use": "methodology gate",
        },
        {
            "status_bucket": "raw_viability_parent_families_checked",
            "source_record_count": len(raw_viability),
            "row_count_if_applicable": "",
            "definition": "Parent source families run through local raw/mirrored viability checks.",
            "accounting_use": "mirror/local-byte coverage",
        },
        {
            "status_bucket": "raw_viability_candidate_for_mapping",
            "source_record_count": source_count_where(raw_viability, "figure1_viability", "candidate_for_figure1_mapping"),
            "row_count_if_applicable": mapped_raw_rows,
            "definition": "Raw/mirrored parent families whose parsed native rows already contain effect, N, and pair context.",
            "accounting_use": "future source_result mapping",
        },
        {
            "status_bucket": "rechecked_records_with_alternate_route",
            "source_record_count": routed_records,
            "row_count_if_applicable": int(
                pd.to_numeric(
                    recheck.loc[
                        ~recheck.get("alternate_route_decision", pd.Series(dtype=str)).eq(
                            "remain_context_or_rejected_no_alternate_subplot"
                        ),
                        "counted_evidence_row_count",
                    ],
                    errors="coerce",
                )
                .fillna(0)
                .sum()
            )
            if not recheck.empty
            else 0,
            "definition": "Previously rejected/blocked records that now have a non-Figure-1A route.",
            "accounting_use": "alternative subplot or denominator",
        },
        {
            "status_bucket": "rechecked_records_no_supported_subplot_route",
            "source_record_count": no_route_records,
            "row_count_if_applicable": 0,
            "definition": "Previously rejected/blocked records still lacking any supported alternate subplot route.",
            "accounting_use": "context/exclusion evidence",
        },
    ]

    if not recheck_summary.empty:
        for _, row in recheck_summary.iterrows():
            decision = clean(row.get("alternate_route_decision")) or "blank"
            worklist = clean(row.get("route_to_worklist_id")) or "no_worklist"
            rows.append(
                {
                    "status_bucket": f"alternate_route::{decision}::{worklist}",
                    "source_record_count": int(row.get("records", 0)),
                    "row_count_if_applicable": int(row.get("counted_evidence_rows", 0)),
                    "definition": f"Alternate-route recheck summary for {decision} / {worklist}.",
                    "accounting_use": clean(row.get("alternate_plot_universe_id")) or "no alternate plot universe",
                }
            )
    return pd.DataFrame(rows)


def build_stage_table(row_metrics: dict[str, int], source_status: pd.DataFrame) -> pd.DataFrame:
    accounted = row_metrics["accounted_row_grain_universe"]
    rows = [
        {
            "stage_id": "accounted_row_grain_universe",
            "count": accounted,
            "count_type": "row-grain objects",
            "percent_of_accounted_row_grain_universe": 100.0,
            "meaning": "Working local denominator after adding alternate routes and explicit failure buckets.",
        },
        {
            "stage_id": "strict_figure1a_current",
            "count": row_metrics["strict_figure1a_rows"],
            "count_type": "rows",
            "percent_of_accounted_row_grain_universe": pct(row_metrics["strict_figure1a_rows"], accounted),
            "meaning": "Rows that hit the current strict direct-D/N Figure 1A gate.",
        },
        {
            "stage_id": "root_dn_any_current_status",
            "count": row_metrics["strict_dn_any_root_rows"],
            "count_type": "rows",
            "percent_of_accounted_row_grain_universe": pct(row_metrics["strict_dn_any_root_rows"], accounted),
            "meaning": "Rows with D/N in the root table, whether current-rule included or blocked.",
        },
        {
            "stage_id": "value_bearing_any_axis_or_blocked",
            "count": row_metrics["value_bearing_any_axis_or_blocked_rows"],
            "count_type": "rows",
            "percent_of_accounted_row_grain_universe": pct(
                row_metrics["value_bearing_any_axis_or_blocked_rows"], accounted
            ),
            "meaning": "Rows with D, D-equivalent, or native values and N, including strict-rule blocked D/N rows.",
        },
        {
            "stage_id": "quantitative_or_native_xy_not_counting_blocked_dn",
            "count": row_metrics["quantitative_or_native_xy_rows"],
            "count_type": "rows",
            "percent_of_accounted_row_grain_universe": pct(row_metrics["quantitative_or_native_xy_rows"], accounted),
            "meaning": "Rows that can appear in Figure 1A, Figure 1B, or a native-scale panel without using currently blocked D/N rows.",
        },
        {
            "stage_id": "denominator_or_repair_only",
            "count": row_metrics["denominator_or_repair_only_rows"],
            "count_type": "rows",
            "percent_of_accounted_row_grain_universe": pct(row_metrics["denominator_or_repair_only_rows"], accounted),
            "meaning": "Rows retained only as denominator, duplicate-risk, parser-repair, or missing-value evidence.",
        },
    ]

    source_lookup = {
        row["status_bucket"]: row
        for _, row in source_status.iterrows()
        if isinstance(row.get("status_bucket"), str)
    }
    for bucket in [
        "root_source_records_all",
        "root_source_records_figure1_relevant_yes",
        "rechecked_records_with_alternate_route",
        "rechecked_records_no_supported_subplot_route",
    ]:
        item = source_lookup.get(bucket)
        if item is None:
            continue
        rows.append(
            {
                "stage_id": bucket,
                "count": int(item.get("source_record_count", 0)),
                "count_type": "source/corpus records",
                "percent_of_accounted_row_grain_universe": "",
                "meaning": clean(item.get("definition")),
            }
        )
    return pd.DataFrame(rows)


def write_plot(row_disposition: pd.DataFrame) -> None:
    plot_df = row_disposition.copy()
    plot_df = plot_df.sort_values("row_count", ascending=True)

    colors = {
        "figure1a_strict_direct_d_axis": "#2b7a78",
        "strict_dn_blocked_by_current_rule": "#7f8c8d",
        "figure1b_binary_d_equivalent": "#3366aa",
        "native_effect_retention": "#b45f06",
        "roster_only_denominator": "#8e7cc3",
        "effect_present_missing_n": "#cc0000",
        "parsed_row_grain_no_effect_n": "#a64d79",
        "duplicate_risk_dn_candidate": "#666666",
    }
    fig, ax = plt.subplots(figsize=(11, 6.5))
    ax.barh(
        plot_df["disposition_label"],
        plot_df["row_count"],
        color=[colors.get(key, "#777777") for key in plot_df["disposition_id"]],
    )
    for idx, row in enumerate(plot_df.itertuples(index=False)):
        ax.text(row.row_count + 12, idx, f"{int(row.row_count):,}", va="center", fontsize=9)
    ax.set_xlabel("Row-grain objects")
    ax.set_title("Figure 1 Replication-Like Material: Current Use or Loss Bucket")
    ax.grid(axis="x", color="#dddddd", linewidth=0.8)
    ax.set_axisbelow(True)
    max_count = max(1, int(plot_df["row_count"].max()))
    ax.set_xlim(0, max_count * 1.18)
    fig.tight_layout()
    fig.savefig(PLOT_OUT, dpi=180)
    plt.close(fig)


def markdown_table(df: pd.DataFrame, columns: list[str]) -> list[str]:
    header = "| " + " | ".join(columns) + " |"
    sep = "| " + " | ".join("---" for _ in columns) + " |"
    lines = [header, sep]
    for _, row in df.iterrows():
        values = []
        for column in columns:
            values.append(clean(row.get(column)).replace("|", "\\|"))
        lines.append("| " + " | ".join(values) + " |")
    return lines


def write_report(
    row_disposition: pd.DataFrame,
    source_status: pd.DataFrame,
    stage_table: pd.DataFrame,
    metrics: dict[str, int],
) -> None:
    accounted = metrics["accounted_row_grain_universe"]
    strict = metrics["strict_figure1a_rows"]
    dn_any = metrics["strict_dn_any_root_rows"]
    value_any = metrics["value_bearing_any_axis_or_blocked_rows"]
    xy_any = metrics["quantitative_or_native_xy_rows"]
    repair = metrics["denominator_or_repair_only_rows"]

    source_all = int(
        source_status.loc[source_status["status_bucket"].eq("root_source_records_all"), "source_record_count"].iloc[0]
    )
    source_relevant = int(
        source_status.loc[
            source_status["status_bucket"].eq("root_source_records_figure1_relevant_yes"),
            "source_record_count",
        ].iloc[0]
    )
    rechecked_alt = int(
        source_status.loc[
            source_status["status_bucket"].eq("rechecked_records_with_alternate_route"),
            "source_record_count",
        ].iloc[0]
    )
    rechecked_none = int(
        source_status.loc[
            source_status["status_bucket"].eq("rechecked_records_no_supported_subplot_route"),
            "source_record_count",
        ].iloc[0]
    )

    lines = [
        "# Figure 1 Coverage and Loss Accounting",
        "",
        "Date: 2026-05-04",
        "",
        "## Definitions",
        "",
        "- A source/corpus record is a discovered paper, database, project, repository, package, or registry-like object in the intake table.",
        "- A row-grain object is a local unit that could plausibly become one original-vs-replication or original-vs-follow-up comparison row.",
        "- Figure 1A means the strict direct D/N panel.",
        "- Figure 1B means the alternative D-equivalent clinical/binary panel.",
        "- Native retention means values are kept on their native scale because forcing them onto D would be misleading.",
        "- Denominator-only means the object supports a coverage statement but is not currently a plotted quantitative row.",
        "",
        "## Headline Accounting",
        "",
        f"The current local accounted row-grain universe is **{accounted:,}** objects. "
        f"Of those, **{strict:,}** rows (**{pct(strict, accounted)}%**) pass the strict Figure 1A D/N gate. "
        f"The root table already contains D/N values for **{dn_any:,}** rows (**{pct(dn_any, accounted)}%**) when current-rule blocked D/N rows are counted as audited value-bearing material. "
        f"Across strict Figure 1A, Figure 1B D-equivalent, and native-scale retention, **{xy_any:,}** rows (**{pct(xy_any, accounted)}%**) can be shown in some x/y quantitative panel without using currently blocked D/N rows. "
        f"If currently blocked D/N rows are counted as value-bearing but not main-panel eligible, **{value_any:,}** rows (**{pct(value_any, accounted)}%**) have values and N in hand. "
        f"The remaining **{repair:,}** rows (**{pct(repair, accounted)}%**) are retained only as denominator, duplicate-risk, parser-repair, or missing-value evidence.",
        "",
        "At the source/corpus level, the intake table contains "
        f"**{source_all:,}** source/corpus records, including **{source_relevant:,}** marked Figure 1 relevant. "
        f"The alternate-route recheck covered **{rechecked_alt + rechecked_none:,}** rejected or blocked records: "
        f"**{rechecked_alt:,}** gained an alternate route and **{rechecked_none:,}** remained context-only or rejected with no supported subplot route.",
        "",
        "This supports a coverage claim about the public, locally discovered, and mirrorable many-replication corpus universe. "
        "It should not be phrased as all possible science-wide follow-up studies, because request-only clinical datasets and one-off paper mining remain outside this local row denominator.",
        "",
        "## Row Disposition",
        "",
    ]
    lines.extend(
        markdown_table(
            row_disposition[
                [
                    "disposition_label",
                    "row_count",
                    "percent_of_accounted_row_grain_universe",
                    "usable_for",
                    "definition",
                ]
            ],
            [
                "disposition_label",
                "row_count",
                "percent_of_accounted_row_grain_universe",
                "usable_for",
                "definition",
            ],
        )
    )
    lines.extend(["", "## Stage Summary", ""])
    lines.extend(
        markdown_table(
            stage_table[
                [
                    "stage_id",
                    "count",
                    "count_type",
                    "percent_of_accounted_row_grain_universe",
                    "meaning",
                ]
            ],
            ["stage_id", "count", "count_type", "percent_of_accounted_row_grain_universe", "meaning"],
        )
    )
    lines.extend(["", "## Source/Candidate Status", ""])
    lines.extend(
        markdown_table(
            source_status[["status_bucket", "source_record_count", "row_count_if_applicable", "accounting_use"]],
            ["status_bucket", "source_record_count", "row_count_if_applicable", "accounting_use"],
        )
    )
    lines.extend(
        [
            "",
            "## Main Loss Reasons",
            "",
            "- Current-rule gate failure: D/N exists, but the row does not pass the strict Figure 1A inclusion rule.",
            "- Metric gate failure: native response/proportion rows have values and N but no defensible D conversion.",
            "- Public-value gap: pair rosters identify original/follow-up links, but public bytes do not expose row-level effect and N.",
            "- Missing-N gap: effects are public, but sample sizes are not in the mirrored result tables.",
            "- Parser gap: row-grain records were parsed, but effect/N evidence was not copied.",
            "- Duplicate-risk gap: D/N-looking rows exist but likely overlap with FReD/current rows and need dedupe before promotion.",
            "- Context-only/exclusion: source records are replication-adjacent but do not expose a supported row route for Figure 1A, Figure 1B, native retention, or denominator accounting.",
            "",
            "## Generated Artifacts",
            "",
            f"- `{rel(ROW_OUT)}`",
            f"- `{rel(SOURCE_OUT)}`",
            f"- `{rel(STAGE_OUT)}`",
            f"- `{rel(PLOT_OUT)}`",
            "",
        ]
    )
    REPORT_OUT.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--replace", action="store_true", help="Overwrite existing outputs")
    args = parser.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for path in [ROW_OUT, SOURCE_OUT, STAGE_OUT, PLOT_OUT, REPORT_OUT]:
        if path.exists() and not args.replace:
            raise FileExistsError(f"{path} exists; pass --replace to overwrite")

    universe_summary = read_tsv(UNIVERSE_SUMMARY)
    recheck = read_tsv(RECHECK_ROWS)
    recheck_summary = read_tsv(RECHECK_SUMMARY)
    corpora = read_tsv(CORPORA_TABLE)
    raw_viability = read_tsv(RAW_VIABILITY)

    if universe_summary.empty:
        raise FileNotFoundError(f"Missing or empty input: {UNIVERSE_SUMMARY}")
    if recheck.empty:
        raise FileNotFoundError(f"Missing or empty input: {RECHECK_ROWS}")
    if corpora.empty:
        raise FileNotFoundError(f"Missing or empty input: {CORPORA_TABLE}")

    row_disposition, metrics = build_row_disposition(universe_summary, recheck, recheck_summary)
    source_status = build_source_status(corpora, raw_viability, recheck, recheck_summary)
    stage_table = build_stage_table(metrics, source_status)

    row_disposition.to_csv(ROW_OUT, sep="\t", index=False)
    source_status.to_csv(SOURCE_OUT, sep="\t", index=False)
    stage_table.to_csv(STAGE_OUT, sep="\t", index=False)
    write_plot(row_disposition)
    write_report(row_disposition, source_status, stage_table, metrics)

    print(f"Wrote {ROW_OUT.relative_to(ROOT)}")
    print(f"Wrote {SOURCE_OUT.relative_to(ROOT)}")
    print(f"Wrote {STAGE_OUT.relative_to(ROOT)}")
    print(f"Wrote {PLOT_OUT.relative_to(ROOT)}")
    print(f"Wrote {REPORT_OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
