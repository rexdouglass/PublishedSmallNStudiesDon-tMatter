#!/usr/bin/env python3
"""Recheck Figure 1A rejects/blocked sources for alternate diagnostic routes."""

from __future__ import annotations

import argparse
import json
import math
import re
from pathlib import Path
from typing import Any

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "steps/corpus_results/figure1/alternate_route_recheck"
OUT_TSV = OUT_DIR / "figure1-rejected-alternate-route-recheck.tsv"
OUT_SUMMARY = OUT_DIR / "figure1-rejected-alternate-route-summary.tsv"
OUT_MD = ROOT / "reports/figure1_rejected_alternate_route_recheck_2026-05-04.md"

UNIVERSE_ROWS = ROOT / "steps/corpus_results/figure1/universe_coverage/figure1-universe-coverage-rows.tsv"
UNIVERSE_SUMMARY = ROOT / "steps/corpus_results/figure1/universe_coverage/figure1-universe-coverage-summary.tsv"
REMAINING_STATUS = ROOT / "steps/corpus_results/figure1/remaining_local_mining/remaining-local-mining-status.tsv"
GPT_STATUS = ROOT / "steps/corpus_results/figure1/gpt_candidate_pair_mining/gpt_candidate_batch2_mining_status.tsv"
FOLLOWUP_TRIAGE = ROOT / "steps/corpus_results/figure1/research_followup_20260504/research-followup-triage.tsv"
RCT_SCHEMA = ROOT / "steps/corpus_results/figure1/research_followup_20260504/rct-duplicate-schema-scan.tsv"
RAW_VIABILITY = ROOT / "steps/corpus_results/figure1/figure1-raw-viability-summary.tsv"
ROUTING_TABLE = ROOT / "steps/review_cue/figure1_search_leads/reviewcue-routing-table-figure1_search_leads.tsv"
CLUSTER_ROUTING_TABLE = ROOT / "steps/review_cue/figure1_search_leads/reviewcue-clustered-routing-table-figure1_search_leads.tsv"
YING_ROSTER = ROOT / "data/derived/replication_pairs/harvest/staged/ying_2023_pair_roster__stage.csv"


def clean(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and math.isnan(value):
        return ""
    return re.sub(r"\s+", " ", str(value).replace("\t", " ")).strip()


def rel(path: str | Path) -> str:
    text = clean(path)
    if not text:
        return ""
    try:
        return str(Path(text).resolve().relative_to(ROOT))
    except Exception:
        return text


def slug(value: Any) -> str:
    text = re.sub(r"[^a-z0-9]+", "_", clean(value).lower()).strip("_")
    return text[:120] or "candidate"


def read_tsv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path, sep="\t")


def read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def add_record(records: list[dict[str, Any]], **kwargs: Any) -> None:
    defaults = {
        "recheck_id": "",
        "record_grain": "source_or_row_bucket",
        "candidate_key": "",
        "candidate_name": "",
        "previous_surface": "",
        "previous_decision": "",
        "previous_reason_or_notes": "",
        "alternate_route_decision": "",
        "alternate_plot_universe_id": "",
        "route_to_worklist_id": "",
        "evidence_row_count": 0,
        "counted_evidence_row_count": "",
        "evidence_status": "",
        "confidence": "medium",
        "why_it_lands_or_not": "",
        "next_action": "",
        "supporting_local_paths": "",
    }
    defaults.update(kwargs)
    if defaults["counted_evidence_row_count"] == "":
        defaults["counted_evidence_row_count"] = defaults["evidence_row_count"]
    if not defaults["recheck_id"]:
        defaults["recheck_id"] = slug(f"{defaults['candidate_key']} {defaults['alternate_route_decision']}")
    for key, value in list(defaults.items()):
        if isinstance(value, str):
            defaults[key] = clean(value)
    records.append(defaults)


def row_count_from_summary(summary: pd.DataFrame, bucket: str) -> int:
    if summary.empty:
        return 0
    row = summary.loc[summary["bucket"].eq(bucket)]
    if row.empty:
        return 0
    return int(row["rows"].iloc[0])


def add_universe_bucket_records(records: list[dict[str, Any]]) -> None:
    summary = read_tsv(UNIVERSE_SUMMARY)
    rows = read_tsv(UNIVERSE_ROWS)
    bucket_specs = [
        (
            "dn_available_blocked_by_current_rule",
            "blocked_root_dn_rows",
            "Root D/N rows blocked by current Figure 1A gate",
            "route_to_coverage_denominator_catalog",
            "plot1d_source_object_coverage_denominator",
            "",
            "D/N rows exist but failed a current plot rule; they remain useful for denominator and robustness accounting.",
            "Keep as plot1d coverage rows; do not backfill Figure 1A without passing the failed gate.",
        ),
        (
            "clinical_binary_comparator_d_equivalent",
            "clinical_binary_d_equivalent_rows",
            "Clinical binary active/control rows",
            "route_to_d_equivalent_diagnostic_worklist",
            "plot1b_clinical_binary_d_equivalent",
            "",
            "Rows expose comparative binary counts and can be shown as D-equivalent via log(OR)*sqrt(3)/pi.",
            "Use for Figure 1B diagnostic after keeping conversion-tier fields.",
        ),
        (
            "one_arm_or_treatment_arm_native_response",
            "native_response_rows",
            "Native response-rate/logit rows",
            "route_to_native_effect_diagnostic_worklist",
            "plot1c_native_effect_retention",
            "",
            "Rows have original/follow-up native response metrics and N, but no defensible treatment-effect D conversion.",
            "Use in native-scale appendix/diagnostic only.",
        ),
        (
            "roster_only_no_public_effect_values",
            "roster_only_rows",
            "Roster-only original/follow-up pair rows",
            "route_to_coverage_denominator_catalog",
            "plot1d_source_object_coverage_denominator",
            "",
            "Rows identify original/follow-up pair structure but public bytes do not expose effect and N.",
            "Keep as coverage denominator; no quantitative scatter until values are obtained.",
        ),
        (
            "effect_values_present_no_public_n_columns",
            "effect_without_n_rows",
            "Effect-present rows missing N",
            "route_to_missing_value_repair_worklist",
            "plot1d_source_object_coverage_denominator",
            "missing_n_or_value_repair_worklist",
            "Effect-like public result rows exist, but no public N columns were found.",
            "Route to missing-N repair; keep out of quantitative panels until N is acquired.",
        ),
    ]
    for bucket, key, name, decision, plot_id, worklist_id, why, action in bucket_specs:
        sub = rows.loc[rows["diagnostic_bucket"].eq(bucket)] if not rows.empty else pd.DataFrame()
        count = len(sub)
        if bucket == "clinical_binary_comparator_d_equivalent":
            # The panel plots all matched endpoints; the summary counts rows not
            # already represented by the strict root clinical phase II/III rows.
            count = row_count_from_summary(summary, "additional_comparative_binary_d_equivalent_rows")
        if bucket == "effect_values_present_no_public_n_columns":
            count = row_count_from_summary(summary, "effect_values_present_no_public_n_columns")
        add_record(
            records,
            record_grain="row_bucket",
            candidate_key=key,
            candidate_name=name,
            previous_surface="figure1_universe_coverage",
            previous_decision="not_in_strict_figure1a_or_blocked",
            alternate_route_decision=decision,
            alternate_plot_universe_id=plot_id,
            route_to_worklist_id=worklist_id,
            evidence_row_count=count,
            evidence_status="concrete_local_row_bucket",
            confidence="high",
            why_it_lands_or_not=why,
            next_action=action,
            supporting_local_paths=f"{rel(UNIVERSE_ROWS)} | {rel(UNIVERSE_SUMMARY)}",
        )


def parse_int_from_text(pattern: str, text: str) -> int:
    match = re.search(pattern, text, flags=re.I)
    if not match:
        return 0
    return int(match.group(1))


def add_status_records(records: list[dict[str, Any]]) -> None:
    seen: set[str] = set()

    def emit_once(key: str, **kwargs: Any) -> None:
        if key in seen:
            return
        seen.add(key)
        add_record(records, candidate_key=key, **kwargs)

    remaining = read_tsv(REMAINING_STATUS)
    for _, row in remaining.iterrows():
        key = clean(row.get("candidate_key"))
        decision = clean(row.get("decision"))
        notes = clean(row.get("notes"))
        if decision.startswith("promoted"):
            continue
        if key == "clinical_highly_cited_workbook":
            count = parse_int_from_text(r"Remaining ORR rows=(\d+)", notes)
            emit_once(
                key,
                record_grain="source_status",
                candidate_name=row.get("candidate_name", ""),
                previous_surface=rel(REMAINING_STATUS),
                previous_decision=decision,
                previous_reason_or_notes=notes,
                alternate_route_decision="route_to_native_effect_diagnostic_worklist",
                alternate_plot_universe_id="plot1c_native_effect_retention",
                evidence_row_count=count,
                evidence_status="source_status_reports_native_orr_rows",
                confidence="medium",
                why_it_lands_or_not="Remaining ORR rows are one-arm response rates; keep in native retention, not D/D-equivalent.",
                next_action="Stage ORR rows as native response-rate rows if source workbook fields are already mirrored and deduplicated.",
                supporting_local_paths=rel(REMAINING_STATUS),
            )
        elif key == "hagen_hcsp":
            emit_once(
                key,
                record_grain="source_status",
                candidate_name=row.get("candidate_name", ""),
                previous_surface=rel(REMAINING_STATUS),
                previous_decision=decision,
                previous_reason_or_notes=notes,
                alternate_route_decision="route_to_coverage_denominator_catalog",
                alternate_plot_universe_id="plot1d_source_object_coverage_denominator",
                route_to_worklist_id="missing_n_or_value_repair_worklist",
                evidence_row_count=0,
                evidence_status="blocked_source_object_route_no_values",
                confidence="high",
                why_it_lands_or_not="The codebook confirms intended D/N-like fields, but the data sheet route is gone; this is coverage/blocker evidence, not a subplot row.",
                next_action="Keep as blocked coverage source; only move to Figure 1A/B/C if the deleted data sheet or equivalent values are recovered.",
                supporting_local_paths=rel(REMAINING_STATUS),
            )
        elif key == "many_smiles":
            emit_once(
                key,
                record_grain="source_status",
                candidate_name=row.get("candidate_name", ""),
                previous_surface=rel(REMAINING_STATUS),
                previous_decision=decision,
                previous_reason_or_notes=notes,
                alternate_route_decision="route_to_missing_value_repair_worklist",
                alternate_plot_universe_id="plot1d_source_object_coverage_denominator",
                route_to_worklist_id="missing_n_or_value_repair_worklist",
                evidence_row_count=0,
                evidence_status="replication_data_mirrored_original_benchmark_missing",
                confidence="medium",
                why_it_lands_or_not="Replication-side data are mirrored but the original benchmark effect/original N choice is unresolved.",
                next_action="Repair original benchmark effect/N source before deciding strict D or D-equivalent eligibility.",
                supporting_local_paths=rel(REMAINING_STATUS),
            )

    gpt = read_tsv(GPT_STATUS)
    for _, row in gpt.iterrows():
        key = clean(row.get("candidate_key"))
        if key in seen or clean(row.get("decision")).startswith("promoted"):
            continue
        notes = clean(row.get("notes"))
        if key == "hagen_hcsp":
            emit_once(
                key,
                record_grain="source_status",
                candidate_name=row.get("candidate_name", ""),
                previous_surface=rel(GPT_STATUS),
                previous_decision=row.get("decision", ""),
                previous_reason_or_notes=notes,
                alternate_route_decision="route_to_coverage_denominator_catalog",
                alternate_plot_universe_id="plot1d_source_object_coverage_denominator",
                route_to_worklist_id="missing_n_or_value_repair_worklist",
                evidence_row_count=0,
                evidence_status="blocked_source_object_route_no_values",
                confidence="high",
                why_it_lands_or_not="Mirrored Shiny app but the value-bearing Google Sheet is deleted/410.",
                next_action="Keep as blocked source-object route unless values are recovered elsewhere.",
                supporting_local_paths=clean(row.get("local_paths")),
            )
        elif key == "many_smiles":
            emit_once(
                key,
                record_grain="source_status",
                candidate_name=row.get("candidate_name", ""),
                previous_surface=rel(GPT_STATUS),
                previous_decision=row.get("decision", ""),
                previous_reason_or_notes=notes,
                alternate_route_decision="route_to_missing_value_repair_worklist",
                alternate_plot_universe_id="plot1d_source_object_coverage_denominator",
                route_to_worklist_id="missing_n_or_value_repair_worklist",
                evidence_row_count=0,
                evidence_status="replication_data_mirrored_original_benchmark_missing",
                confidence="medium",
                why_it_lands_or_not="Data zip is mirrored, but original benchmark effect and original N were not found.",
                next_action="Repair original benchmark source or keep as coverage/context only.",
                supporting_local_paths=clean(row.get("local_paths")),
            )

    followup = read_tsv(FOLLOWUP_TRIAGE)
    ying_count = len(read_csv(YING_ROSTER))
    rct_count = 0
    rct = read_tsv(RCT_SCHEMA)
    if not rct.empty:
        effect_no_n = rct.loc[
            rct["has_effect_like_columns"].astype(bool)
            & ~rct["has_n_like_columns"].astype(bool)
        ]
        if not effect_no_n.empty:
            rct_count = int(effect_no_n["rows"].max())
    for _, row in followup.iterrows():
        key = clean(row.get("candidate_key"))
        if key in seen:
            continue
        decision = clean(row.get("decision"))
        notes = clean(row.get("notes"))
        if key == "forrt_reversals":
            emit_once(
                key,
                record_grain="source_status",
                candidate_name=row.get("candidate_name", ""),
                previous_surface=rel(FOLLOWUP_TRIAGE),
                previous_decision=decision,
                previous_reason_or_notes=notes,
                alternate_route_decision="route_to_coverage_denominator_catalog",
                alternate_plot_universe_id="plot1d_source_object_coverage_denominator",
                evidence_row_count=int(row.get("candidate_rows_found") or 0),
                evidence_status="candidate_d_n_rows_duplicate_risk",
                confidence="medium",
                why_it_lands_or_not="Candidate D/N-looking rows exist but need dedupe/field alignment before any Figure 1A use.",
                next_action="Keep in coverage denominator and dedupe against FReD/current rows before promotion.",
                supporting_local_paths=rel(FOLLOWUP_TRIAGE),
            )
        elif key == "rct_duplicate":
            emit_once(
                key,
                record_grain="source_status",
                candidate_name=row.get("candidate_name", ""),
                previous_surface=rel(FOLLOWUP_TRIAGE),
                previous_decision=decision,
                previous_reason_or_notes=notes,
                alternate_route_decision="route_to_missing_value_repair_worklist",
                alternate_plot_universe_id="plot1d_source_object_coverage_denominator",
                route_to_worklist_id="missing_n_or_value_repair_worklist",
                evidence_row_count=rct_count,
                counted_evidence_row_count=0,
                evidence_status="effect_values_present_no_public_n_columns",
                confidence="high",
                next_action="Keep as effect-without-N repair target; do not plot until N is recovered.",
                why_it_lands_or_not="Public result CSVs expose ratio effects but not original/RWE N columns. Count is already represented by the effect-without-N row bucket.",
                supporting_local_paths=f"{rel(FOLLOWUP_TRIAGE)} | {rel(RCT_SCHEMA)}",
            )
        elif key == "ying_pilot_full_scale":
            emit_once(
                key,
                record_grain="source_status",
                candidate_name=row.get("candidate_name", ""),
                previous_surface=rel(FOLLOWUP_TRIAGE),
                previous_decision=decision,
                previous_reason_or_notes=notes,
                alternate_route_decision="route_to_coverage_denominator_catalog",
                alternate_plot_universe_id="plot1d_source_object_coverage_denominator",
                route_to_worklist_id="missing_n_or_value_repair_worklist",
                evidence_row_count=ying_count,
                counted_evidence_row_count=0,
                evidence_status="pair_roster_public_values_request_only",
                confidence="high",
                why_it_lands_or_not="Public/local bytes give a pilot/full-scale pair roster, but not the row-level D/N values. Count is already represented by the roster-only row bucket.",
                next_action="Keep roster rows in coverage denominator; no author-request route unless policy changes.",
                supporting_local_paths=f"{rel(FOLLOWUP_TRIAGE)} | {rel(YING_ROSTER)}",
            )
        elif key == "rgb_health_behavior_family":
            emit_once(
                key,
                record_grain="source_status",
                candidate_name=row.get("candidate_name", ""),
                previous_surface=rel(FOLLOWUP_TRIAGE),
                previous_decision=decision,
                previous_reason_or_notes=notes,
                alternate_route_decision="route_to_missing_value_repair_worklist",
                alternate_plot_universe_id="plot1d_source_object_coverage_denominator",
                route_to_worklist_id="missing_n_or_value_repair_worklist",
                evidence_row_count=0,
                evidence_status="source_confirms_pairs_effect_counts_but_no_public_master_table",
                confidence="medium",
                why_it_lands_or_not="Articles confirm pair/effect counts, but no public row-level master table was mirrored.",
                next_action="Keep as missing-value/source-object repair only; no quantitative panel until public/user-provided values exist.",
                supporting_local_paths=rel(FOLLOWUP_TRIAGE),
            )
        elif key == "scaleup_reviews":
            emit_once(
                key,
                record_grain="source_status",
                candidate_name=row.get("candidate_name", ""),
                previous_surface=rel(FOLLOWUP_TRIAGE),
                previous_decision=decision,
                previous_reason_or_notes=notes,
                alternate_route_decision="remain_context_or_rejected_no_alternate_subplot",
                evidence_row_count=0,
                evidence_status="context_only_no_current_pair_table",
                confidence="medium",
                why_it_lands_or_not="No D/N or native pair table was promoted, and same-estimand fit is weak.",
                next_action="Leave as context unless a structured pre-scale/scale-up table is found.",
                supporting_local_paths=rel(FOLLOWUP_TRIAGE),
            )


def add_raw_viability_records(records: list[dict[str, Any]]) -> None:
    raw = read_tsv(RAW_VIABILITY)
    existing = {clean(r["candidate_key"]) for r in records}
    for _, row in raw.iterrows():
        key = clean(row.get("parent_corpus_database_id"))
        if key in existing:
            continue
        status = clean(row.get("raw_viability_status"))
        fig_status = clean(row.get("figure1_viability"))
        name = clean(row.get("preferred_source_family_names"))
        reason = clean(row.get("raw_viability_reason"))
        next_action = clean(row.get("next_action"))
        parsed_rows = int(row.get("parsed_native_rows") or 0)
        pair_rows = int(row.get("rows_with_effect_n_and_pair_context") or 0)
        if fig_status in {"candidate_for_figure1_mapping", "duplicate_or_alias_of_candidate_parent"}:
            continue
        if status == "parsed_rows_but_no_effect_n_signal":
            decision = "route_to_coverage_denominator_catalog"
            plot_id = "plot1d_source_object_coverage_denominator"
            worklist = "missing_n_or_value_repair_worklist"
            confidence = "high"
            why = "Parsed row grain exists, but current extraction did not copy effect/N evidence."
            count = parsed_rows
        elif "non_table_artifacts_need_custom_review" in status:
            decision = "route_to_coverage_denominator_catalog"
            plot_id = "plot1d_source_object_coverage_denominator"
            worklist = "missing_n_or_value_repair_worklist"
            confidence = "medium"
            why = "Mirrored artifacts exist, but no current parser output exposes row-level effect/N."
            count = pair_rows or parsed_rows
        elif "lower_priority_artifacts_need_review" in status:
            decision = "route_to_coverage_denominator_catalog"
            plot_id = "plot1d_source_object_coverage_denominator"
            worklist = "missing_n_or_value_repair_worklist"
            confidence = "low"
            why = "Mirrored lower-priority artifacts exist but have not produced current row-level effect/N."
            count = pair_rows or parsed_rows
        else:
            decision = "remain_context_or_rejected_no_alternate_subplot"
            plot_id = ""
            worklist = ""
            confidence = "medium"
            why = "Current mirror/sample pass did not expose a row-level value route."
            count = 0
        add_record(
            records,
            record_grain="source_family_raw_viability",
            candidate_key=key,
            candidate_name=name,
            previous_surface=rel(RAW_VIABILITY),
            previous_decision=fig_status,
            previous_reason_or_notes=f"{status}. {reason}",
            alternate_route_decision=decision,
            alternate_plot_universe_id=plot_id,
            route_to_worklist_id=worklist,
            evidence_row_count=count,
            evidence_status=status,
            confidence=confidence,
            why_it_lands_or_not=why,
            next_action=next_action,
            supporting_local_paths=clean(row.get("representative_files")),
        )


def classify_review_route(row: pd.Series) -> tuple[str, str, str, int, str, str, str]:
    decision = clean(row.get("decision"))
    text = " ".join(
        clean(row.get(col))
        for col in ["reason", "next_action", "notes", "lead_key", "canonical_source_key"]
    ).lower()
    if "lacks sample size" in text or "unless n" in text or "no effect sizes" in text:
        return (
            "route_to_missing_value_repair_worklist",
            "plot1d_source_object_coverage_denominator",
            "missing_n_or_value_repair_worklist",
            0,
            "source_mentions_missing_values_or_N",
            "The previous decision already points to missing N/effect values rather than irrelevance.",
            "Keep as repair/context only until row-level values are found.",
        )
    if "denominator" in text or "publication-status scaffold" in text or "search index" in text or "registry/database" in text:
        return (
            "route_to_coverage_denominator_catalog",
            "plot1d_source_object_coverage_denominator",
            "",
            0,
            "source_context_may_help_denominator_or_discovery",
            "This can help denominator/search coverage but does not expose a quantitative subplot row.",
            "Catalog under coverage/context; do not parse as Figure 1A.",
        )
    if "one-arm" in text or "response rate" in text or "orr" in text:
        return (
            "route_to_native_effect_diagnostic_worklist",
            "plot1c_native_effect_retention",
            "",
            0,
            "native_metric_possible_but_no_local_rows_confirmed",
            "The text points to native response metrics, but no row-level values are confirmed here.",
            "Use native route only if row-level original/follow-up values are obtained.",
        )
    if decision == "reject_irrelevant":
        return (
            "remain_context_or_rejected_no_alternate_subplot",
            "",
            "",
            0,
            "rechecked_no_pair_or_value_route",
            "The prior rejection describes no original/follow-up pair mapping and no value-bearing route.",
            "Leave rejected for current Figure 1 and alternate subplot routes.",
        )
    return (
        "remain_context_or_rejected_no_alternate_subplot",
        "",
        "",
        0,
        "context_only_no_current_subplot_route",
        "The source may be useful context, but no alternate subplot row route is supported by the receipt.",
        "Leave as context unless later source bytes expose row-level values.",
    )


def add_review_receipt_records(records: list[dict[str, Any]]) -> None:
    routing = read_tsv(ROUTING_TABLE)
    if routing.empty:
        return
    candidates = routing.loc[routing["decision"].isin(["reject_irrelevant", "keep_as_context_source", "needs_more_evidence"])].copy()
    for _, row in candidates.iterrows():
        route, plot_id, worklist, count, status, why, action = classify_review_route(row)
        add_record(
            records,
            record_grain="review_receipt",
            candidate_key=row.get("lead_key", ""),
            candidate_name=row.get("lead_key", ""),
            previous_surface=rel(ROUTING_TABLE),
            previous_decision=row.get("decision", ""),
            previous_reason_or_notes=row.get("reason", ""),
            alternate_route_decision=route,
            alternate_plot_universe_id=plot_id,
            route_to_worklist_id=worklist,
            evidence_row_count=count,
            evidence_status=status,
            confidence="low" if route != "remain_context_or_rejected_no_alternate_subplot" else "medium",
            why_it_lands_or_not=why,
            next_action=action,
            supporting_local_paths=row.get("receipt_path", ""),
        )


def add_cluster_records(records: list[dict[str, Any]]) -> None:
    clusters = read_tsv(CLUSTER_ROUTING_TABLE)
    if clusters.empty:
        return
    for _, row in clusters.iterrows():
        decision = clean(row.get("decision"))
        if decision not in {"route_cluster_to_individual_replication_paper_worklist", "keep_context_source", "reject_irrelevant"}:
            continue
        text = " ".join(clean(row.get(col)) for col in ["reason", "next_action", "preferred_source_family_name"]).lower()
        if "single" in text or "individual" in text:
            route = "remain_context_or_rejected_no_alternate_subplot"
            plot_id = ""
            worklist = ""
            status = "individual_package_not_many_row_alt_subplot"
            why = "Cluster was routed away because it is a one-off/individual package, not a many-row alternate subplot source."
            action = "Leave in individual-paper worklist; do not count as corpus subplot coverage."
        else:
            route = "route_to_coverage_denominator_catalog"
            plot_id = "plot1d_source_object_coverage_denominator"
            worklist = ""
            status = "cluster_context_or_coverage_candidate"
            why = "Cluster was not a root Figure 1A corpus but may still be useful as coverage/context."
            action = "Keep as coverage/context unless row-level values are found."
        add_record(
            records,
            record_grain="cluster_receipt",
            candidate_key=row.get("cluster_id", ""),
            candidate_name=row.get("preferred_source_family_name", ""),
            previous_surface=rel(CLUSTER_ROUTING_TABLE),
            previous_decision=decision,
            previous_reason_or_notes=row.get("reason", ""),
            alternate_route_decision=route,
            alternate_plot_universe_id=plot_id,
            route_to_worklist_id=worklist,
            evidence_row_count=0,
            evidence_status=status,
            confidence="medium",
            why_it_lands_or_not=why,
            next_action=action,
            supporting_local_paths=row.get("receipt_path", ""),
        )


def build_summary(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()
    groups = (
        df.groupby(["alternate_route_decision", "alternate_plot_universe_id", "route_to_worklist_id"], dropna=False)
        .agg(records=("recheck_id", "count"), evidence_rows=("evidence_row_count", "sum"))
        .rename(columns={"evidence_rows": "raw_evidence_rows"})
        .reset_index()
        .sort_values(["alternate_route_decision", "records"], ascending=[True, False])
    )
    counted = (
        df.groupby(["alternate_route_decision", "alternate_plot_universe_id", "route_to_worklist_id"], dropna=False)
        .agg(counted_evidence_rows=("counted_evidence_row_count", "sum"))
        .reset_index()
    )
    groups = groups.merge(
        counted,
        on=["alternate_route_decision", "alternate_plot_universe_id", "route_to_worklist_id"],
        how="left",
    )
    return groups


def write_report(df: pd.DataFrame, summary: pd.DataFrame) -> None:
    concrete = df.loc[df["evidence_row_count"].astype(int).gt(0)].copy()
    by_route = {row["alternate_route_decision"]: row for _, row in summary.iterrows()}

    def route_line(route: str) -> str:
        sub = summary.loc[summary["alternate_route_decision"].eq(route)]
        if sub.empty:
            return f"- `{route}`: 0 records, 0 evidence rows"
        records = int(sub["records"].sum())
        rows = int(sub["counted_evidence_rows"].sum())
        raw_rows = int(sub["raw_evidence_rows"].sum())
        suffix = f" ({raw_rows} raw source-level row claims before de-duplicating row buckets)" if raw_rows != rows else ""
        return f"- `{route}`: {records} records, {rows} counted evidence rows{suffix}"

    lines = [
        "# Figure 1 Rejected/Blocked Alternate Route Recheck",
        "",
        "Generated by `scripts/recheck_figure1_rejected_for_alternative_routes.py` on 2026-05-04.",
        "",
        "## Scope",
        "",
        "This recheck asks whether sources or rows previously blocked from strict Figure 1A should land in a different route instead: Figure 1B D-equivalent, native-effect retention, coverage denominator, or missing-value repair. It does not promote rows into the root Figure 1A pair table.",
        "",
        "## Route Summary",
        "",
        route_line("route_to_d_equivalent_diagnostic_worklist"),
        route_line("route_to_native_effect_diagnostic_worklist"),
        route_line("route_to_coverage_denominator_catalog"),
        route_line("route_to_missing_value_repair_worklist"),
        route_line("remain_context_or_rejected_no_alternate_subplot"),
        "",
        "## Concrete Row-Level Findings",
        "",
    ]
    concrete_counted = concrete.loc[concrete["counted_evidence_row_count"].astype(int).gt(0)].copy()
    if concrete_counted.empty:
        lines.append("No concrete row-level alternate-route candidates were found.")
    else:
        for _, row in concrete_counted.sort_values(["alternate_route_decision", "counted_evidence_row_count"], ascending=[True, False]).iterrows():
            lines.append(
                f"- **{clean(row['candidate_name'])}**: {int(row['counted_evidence_row_count']):,} rows -> "
                f"`{clean(row['alternate_route_decision'])}`"
                + (f" / `{clean(row['alternate_plot_universe_id'])}`" if clean(row["alternate_plot_universe_id"]) else "")
                + f". {clean(row['why_it_lands_or_not'])}"
            )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "The recheck does not reveal a large hidden pile of strict Figure 1A rows. The useful salvage routes are mostly diagnostic: comparative binary D-equivalent rows, native response-rate rows, roster-only denominators, and missing-N repair targets.",
            "",
            "The most concrete quantitative alternate panel is the clinical binary D-equivalent route. Native response-rate rows are also concrete, but they should stay off the D axis. RCT-DUPLICATE and Ying-style pilot/full-scale leads mostly improve the denominator and repair worklists rather than adding plotted rows immediately.",
            "",
            "## Generated Artifacts",
            "",
            f"- Recheck table: `{rel(OUT_TSV)}`",
            f"- Summary table: `{rel(OUT_SUMMARY)}`",
        ]
    )
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--replace", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for path in [OUT_TSV, OUT_SUMMARY, OUT_MD]:
        if path.exists() and not args.replace:
            raise SystemExit(f"{path} exists; pass --replace")
    records: list[dict[str, Any]] = []
    add_universe_bucket_records(records)
    add_status_records(records)
    add_raw_viability_records(records)
    add_review_receipt_records(records)
    add_cluster_records(records)
    df = pd.DataFrame(records)
    df.to_csv(OUT_TSV, sep="\t", index=False)
    summary = build_summary(df)
    summary.to_csv(OUT_SUMMARY, sep="\t", index=False)
    write_report(df, summary)
    print(f"Wrote {len(df):,} recheck records -> {rel(OUT_TSV)}")
    print(f"Wrote summary -> {rel(OUT_SUMMARY)}")
    print(f"Wrote report -> {rel(OUT_MD)}")


if __name__ == "__main__":
    main()
