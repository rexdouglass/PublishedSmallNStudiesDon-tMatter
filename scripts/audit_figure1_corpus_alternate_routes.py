#!/usr/bin/env python3
"""Build a corpus-centered audit of Figure 1 and alternate subplot routes.

This is intentionally a projection of existing TSV artifacts. It does not
promote rows. Its job is to make the current state readable at the corpus or
source-family level: strict Figure 1A, D-equivalent, native effect, coverage
denominator, missing-value repair, or context/no supported route.
"""

from __future__ import annotations

import argparse
import math
import re
from pathlib import Path
from typing import Any

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "steps/corpus_results/figure1/alternate_route_recheck"
OUT_TSV = OUT_DIR / "figure1-corpus-alternate-route-audit.tsv"
OUT_SUMMARY = OUT_DIR / "figure1-corpus-alternate-route-summary.tsv"
OUT_MD = ROOT / "reports/figure1_corpus_alternate_route_audit_2026-05-04.md"

CORPORA = ROOT / "CORPORA_AND_DATABASES.tsv"
ROOT_PAIRS = ROOT / "FIGURE1_REPLICATION_PAIRS.tsv"
UNIVERSE_ROWS = ROOT / "steps/corpus_results/figure1/universe_coverage/figure1-universe-coverage-rows.tsv"
UNIVERSE_SUMMARY = ROOT / "steps/corpus_results/figure1/universe_coverage/figure1-universe-coverage-summary.tsv"
RECHECK = OUT_DIR / "figure1-rejected-alternate-route-recheck.tsv"
RAW_VIABILITY = ROOT / "steps/corpus_results/figure1/figure1-raw-viability-summary.tsv"
COVERAGE_ROW_DISPOSITION = ROOT / "steps/corpus_results/figure1/coverage_loss_accounting/figure1-row-disposition.tsv"


def clean(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and math.isnan(value):
        return ""
    return re.sub(r"\s+", " ", str(value).replace("\t", " ")).strip()


def slug(value: Any) -> str:
    text = re.sub(r"[^a-z0-9]+", "_", clean(value).lower()).strip("_")
    return text[:120]


def rel(path: Path | str) -> str:
    text = clean(path)
    if not text:
        return ""
    try:
        return str(Path(text).resolve().relative_to(ROOT))
    except Exception:
        return text


def read_tsv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path, sep="\t", dtype=str).fillna("")


def as_int(value: Any) -> int:
    text = clean(value)
    if not text:
        return 0
    try:
        return int(float(text))
    except ValueError:
        return 0


def count_rows(df: pd.DataFrame) -> int:
    """Count rows, respecting row_count_override summary records."""
    if df.empty:
        return 0
    if "row_count_override" not in df.columns:
        return len(df)
    total = 0
    for _, row in df.iterrows():
        override = as_int(row.get("row_count_override"))
        total += override if override else 1
    return total


def route_priority(route: str) -> int:
    priorities = {
        "feeds_figure1a_strict_d_n": 90,
        "feeds_figure1a_and_coverage_denominator": 88,
        "route_to_d_equivalent_diagnostic_worklist": 80,
        "route_to_native_effect_diagnostic_worklist": 70,
        "strict_dn_blocked_coverage_only": 65,
        "route_to_missing_value_repair_worklist": 60,
        "route_to_coverage_denominator_catalog": 50,
        "duplicate_or_alias_support_only": 40,
        "registry_untriaged_or_context_only": 25,
        "remain_context_or_rejected_no_alternate_subplot": 10,
    }
    return priorities.get(route, 0)


def choose_route(rec: dict[str, Any]) -> tuple[str, str, str]:
    strict = as_int(rec.get("strict_figure1a_rows"))
    blocked = as_int(rec.get("strict_dn_blocked_rows"))
    deq = as_int(rec.get("d_equivalent_rows"))
    native = as_int(rec.get("native_effect_rows"))
    effect_no_n = as_int(rec.get("effect_present_n_missing_rows"))
    roster = as_int(rec.get("roster_only_rows"))
    repair = as_int(rec.get("repair_or_parser_rows"))
    duplicate = as_int(rec.get("duplicate_or_alias_rows"))

    if strict and blocked:
        return (
            "feeds_figure1a_and_coverage_denominator",
            "plot1_replication_pairs | plot1d_source_object_coverage_denominator",
            "Strict D/N rows already feed Figure 1A; additional D/N rows are blocked by current gates and remain denominator/accounting rows.",
        )
    if strict:
        return (
            "feeds_figure1a_strict_d_n",
            "plot1_replication_pairs",
            "This corpus/source family already feeds strict Figure 1A with D and N.",
        )
    if deq:
        return (
            "route_to_d_equivalent_diagnostic_worklist",
            "plot1b_clinical_binary_d_equivalent",
            "Comparative binary rows can feed the D-equivalent clinical/binary panel using explicit conversion-tier fields.",
        )
    if native:
        return (
            "route_to_native_effect_diagnostic_worklist",
            "plot1c_native_effect_retention",
            "Native response/rate rows can be retained outside the D axis.",
        )
    if blocked:
        return (
            "strict_dn_blocked_coverage_only",
            "plot1d_source_object_coverage_denominator",
            "D/N rows exist but are blocked by current Figure 1A gates, so they support denominator/robustness accounting rather than alternate value panels.",
        )
    if effect_no_n or repair:
        return (
            "route_to_missing_value_repair_worklist",
            "plot1d_source_object_coverage_denominator",
            "Effect-like or pair-like rows exist, but missing N/value/source-object issues prevent quantitative plotting.",
        )
    if roster:
        return (
            "route_to_coverage_denominator_catalog",
            "plot1d_source_object_coverage_denominator",
            "The corpus identifies pair structure but not public row-level values; it belongs in the universe denominator.",
        )
    if duplicate:
        return (
            "duplicate_or_alias_support_only",
            "plot1d_source_object_coverage_denominator",
            "Rows or artifacts look duplicative/aliasing and should support dedupe/provenance, not add new plotted dots.",
        )
    return (
        clean(rec.get("best_route")) or "remain_context_or_rejected_no_alternate_subplot",
        clean(rec.get("plot_universe_route")),
        clean(rec.get("route_reason")) or "No current local evidence supports Figure 1A, D-equivalent, native, denominator, or repair rows.",
    )


def empty_record(source: str, key: str, name: str) -> dict[str, Any]:
    return {
        "audit_record_id": slug(f"{source}:{key or name}"),
        "audit_source": source,
        "object_key": clean(key),
        "object_name": clean(name),
        "source_record_id": "",
        "figure1_replication_relevance": "",
        "inventory_status": "",
        "record_kind": "",
        "parser_status": "",
        "blocker_codes": "",
        "strict_figure1a_rows": 0,
        "strict_dn_blocked_rows": 0,
        "d_equivalent_rows": 0,
        "native_effect_rows": 0,
        "roster_only_rows": 0,
        "effect_present_n_missing_rows": 0,
        "repair_or_parser_rows": 0,
        "duplicate_or_alias_rows": 0,
        "context_or_rejected_records": 0,
        "best_route": "",
        "plot_universe_route": "",
        "worklist_route": "",
        "route_status": "",
        "route_reason": "",
        "next_action": "",
        "evidence_paths": "",
        "mapping_confidence": "direct",
    }


def merge_record(records: dict[str, dict[str, Any]], key: str, rec: dict[str, Any]) -> None:
    if key not in records:
        records[key] = rec
        return
    current = records[key]
    for col in [
        "strict_figure1a_rows",
        "strict_dn_blocked_rows",
        "d_equivalent_rows",
        "native_effect_rows",
        "roster_only_rows",
        "effect_present_n_missing_rows",
        "repair_or_parser_rows",
        "duplicate_or_alias_rows",
        "context_or_rejected_records",
    ]:
        current[col] = as_int(current.get(col)) + as_int(rec.get(col))
    for col in [
        "object_name",
        "source_record_id",
        "figure1_replication_relevance",
        "inventory_status",
        "record_kind",
        "parser_status",
        "blocker_codes",
        "worklist_route",
        "next_action",
        "evidence_paths",
    ]:
        old = clean(current.get(col))
        new = clean(rec.get(col))
        if new and new not in old.split(" | "):
            current[col] = f"{old} | {new}" if old else new
    old_route = clean(current.get("best_route"))
    new_route = clean(rec.get("best_route"))
    if route_priority(new_route) > route_priority(old_route):
        current["best_route"] = new_route
        current["plot_universe_route"] = rec.get("plot_universe_route", "")
        current["route_reason"] = rec.get("route_reason", "")
    if clean(rec.get("mapping_confidence")) != "direct":
        current["mapping_confidence"] = rec.get("mapping_confidence", current.get("mapping_confidence", "direct"))


def add_root_pair_records(records: dict[str, dict[str, Any]]) -> None:
    pairs = read_tsv(ROOT_PAIRS)
    if pairs.empty:
        return
    for (key, label), sub in pairs.groupby(["source_family_key", "source_family_label"], dropna=False):
        rec = empty_record("root_pair_source_family", key, label)
        rec["strict_figure1a_rows"] = int(sub["current_plot_rule_status"].eq("included_by_current_figure1_dn_rule").sum())
        rec["strict_dn_blocked_rows"] = int(sub["current_plot_rule_status"].eq("excluded_by_current_figure1_dn_rule").sum())
        rec["evidence_paths"] = rel(ROOT_PAIRS)
        rec["best_route"], rec["plot_universe_route"], rec["route_reason"] = choose_route(rec)
        merge_record(records, f"root:{slug(key)}", rec)


def add_universe_records(records: dict[str, dict[str, Any]]) -> None:
    rows = read_tsv(UNIVERSE_ROWS)
    if rows.empty:
        return
    for family, sub in rows.groupby("source_family", dropna=False):
        rec = empty_record("universe_coverage_source_family", family, family)
        rec["strict_figure1a_rows"] = count_rows(sub.loc[sub["diagnostic_bucket"].eq("strict_current_figure1")])
        rec["strict_dn_blocked_rows"] = count_rows(sub.loc[sub["diagnostic_bucket"].eq("dn_available_blocked_by_current_rule")])
        rec["d_equivalent_rows"] = count_rows(sub.loc[sub["diagnostic_bucket"].eq("clinical_binary_comparator_d_equivalent")])
        rec["native_effect_rows"] = count_rows(sub.loc[sub["diagnostic_bucket"].eq("one_arm_or_treatment_arm_native_response")])
        rec["roster_only_rows"] = count_rows(sub.loc[sub["diagnostic_bucket"].eq("roster_only_no_public_effect_values")])
        rec["effect_present_n_missing_rows"] = count_rows(sub.loc[sub["diagnostic_bucket"].eq("effect_values_present_no_public_n_columns")])
        rec["evidence_paths"] = f"{rel(UNIVERSE_ROWS)} | {rel(UNIVERSE_SUMMARY)}"
        rec["best_route"], rec["plot_universe_route"], rec["route_reason"] = choose_route(rec)
        merge_record(records, f"universe:{slug(family)}", rec)


def add_recheck_records(records: dict[str, dict[str, Any]]) -> None:
    recheck = read_tsv(RECHECK)
    if recheck.empty:
        return
    for _, row in recheck.iterrows():
        key = clean(row.get("candidate_key"))
        name = clean(row.get("candidate_name")) or key
        rec = empty_record("alternate_route_recheck", key, name)
        route = clean(row.get("alternate_route_decision"))
        rec["best_route"] = route
        rec["plot_universe_route"] = clean(row.get("alternate_plot_universe_id"))
        rec["worklist_route"] = clean(row.get("route_to_worklist_id"))
        rec["route_status"] = clean(row.get("evidence_status"))
        rec["route_reason"] = clean(row.get("why_it_lands_or_not"))
        rec["next_action"] = clean(row.get("next_action"))
        rec["evidence_paths"] = clean(row.get("supporting_local_paths")) or rel(RECHECK)
        counted = as_int(row.get("counted_evidence_row_count"))
        raw = as_int(row.get("evidence_row_count"))
        count = counted if counted else raw
        if route == "route_to_d_equivalent_diagnostic_worklist":
            rec["d_equivalent_rows"] = count
        elif route == "route_to_native_effect_diagnostic_worklist":
            rec["native_effect_rows"] = count
        elif route == "route_to_missing_value_repair_worklist":
            rec["repair_or_parser_rows"] = count
        elif route == "route_to_coverage_denominator_catalog":
            if "duplicate" in clean(row.get("evidence_status")).lower():
                rec["duplicate_or_alias_rows"] = count
            else:
                rec["roster_only_rows"] = count
        elif route == "remain_context_or_rejected_no_alternate_subplot":
            rec["context_or_rejected_records"] = 1
        merge_record(records, f"recheck:{slug(key)}", rec)


def add_raw_viability_records(records: dict[str, dict[str, Any]]) -> None:
    raw = read_tsv(RAW_VIABILITY)
    if raw.empty:
        return
    for _, row in raw.iterrows():
        key = clean(row.get("parent_corpus_database_id"))
        name = clean(row.get("preferred_source_family_names")) or key
        rec = empty_record("raw_viability_parent", key, name)
        rec["route_status"] = clean(row.get("raw_viability_status"))
        rec["route_reason"] = clean(row.get("raw_viability_reason"))
        rec["next_action"] = clean(row.get("next_action"))
        rec["evidence_paths"] = clean(row.get("representative_files")) or rel(RAW_VIABILITY)
        parsed = as_int(row.get("parsed_native_rows"))
        pair_context = as_int(row.get("rows_with_effect_n_and_pair_context"))
        effect_n_pair = as_int(row.get("rows_with_effect_n_and_pair_context"))
        fig = clean(row.get("figure1_viability"))
        status = clean(row.get("raw_viability_status"))
        if fig == "candidate_for_figure1_mapping":
            rec["repair_or_parser_rows"] = effect_n_pair or pair_context or parsed
            rec["best_route"] = "route_to_missing_value_repair_worklist"
            rec["plot_universe_route"] = "plot1d_source_object_coverage_denominator"
            rec["worklist_route"] = "missing_n_or_value_repair_worklist"
            rec["route_reason"] = "Raw parser found candidate pair/value structure, but this audit does not promote it directly to root tables."
        elif status in {
            "parsed_rows_but_no_effect_n_signal",
            "mirrored_high_priority_non_table_artifacts_need_custom_review",
            "mirrored_lower_priority_artifacts_need_review",
        }:
            rec["repair_or_parser_rows"] = pair_context or parsed
            rec["best_route"] = "route_to_missing_value_repair_worklist" if parsed else "route_to_coverage_denominator_catalog"
            rec["plot_universe_route"] = "plot1d_source_object_coverage_denominator"
            rec["worklist_route"] = "missing_n_or_value_repair_worklist"
        elif "duplicate" in fig:
            rec["duplicate_or_alias_rows"] = parsed or pair_context
            rec["best_route"] = "duplicate_or_alias_support_only"
            rec["plot_universe_route"] = "plot1d_source_object_coverage_denominator"
        else:
            rec["best_route"] = "remain_context_or_rejected_no_alternate_subplot"
            rec["context_or_rejected_records"] = 1
        merge_record(records, f"raw:{slug(key)}", rec)


def add_corpora_records(records: dict[str, dict[str, Any]]) -> None:
    corpora = read_tsv(CORPORA)
    if corpora.empty:
        return
    for _, row in corpora.iterrows():
        key = clean(row.get("corpus_database_id"))
        name = clean(row.get("name")) or key
        relevance = clean(row.get("figure1_replication_relevance"))
        rec = empty_record("corpora_registry", key, name)
        rec["source_record_id"] = key
        rec["figure1_replication_relevance"] = relevance
        rec["inventory_status"] = clean(row.get("inventory_status"))
        rec["record_kind"] = clean(row.get("record_kind"))
        rec["parser_status"] = clean(row.get("parser_status"))
        rec["blocker_codes"] = clean(row.get("blocker_codes"))
        known_pairs = as_int(row.get("known_pair_rows"))
        rec["strict_figure1a_rows"] = known_pairs if clean(row.get("parser_status")) in {"integrated", "staged"} else 0
        rec["evidence_paths"] = rel(CORPORA)

        blockers = rec["blocker_codes"].lower()
        next_action = clean(row.get("next_action"))
        rec["next_action"] = next_action
        if rec["strict_figure1a_rows"]:
            rec["best_route"], rec["plot_universe_route"], rec["route_reason"] = choose_route(rec)
        elif "metric_not_on_shared_d_axis" in blockers or "consider_native_metric_lane" in next_action:
            rec["best_route"] = "route_to_native_effect_diagnostic_worklist"
            rec["plot_universe_route"] = "plot1c_native_effect_retention"
            rec["route_reason"] = "Registry metadata says the source is not on the shared D axis; it may only feed a native lane if row-level native values are parsed."
        elif "conversion_policy_missing" in blockers:
            rec["best_route"] = "route_to_d_equivalent_diagnostic_worklist"
            rec["plot_universe_route"] = "plot1b_clinical_binary_d_equivalent"
            rec["route_reason"] = "Registry metadata says conversion policy was the blocker; after the new routing, this belongs in D-equivalent review if row-level fields exist."
        elif "missing_machine_readable_pair_results" in blockers or "roster_only" in blockers:
            rec["best_route"] = "route_to_coverage_denominator_catalog"
            rec["plot_universe_route"] = "plot1d_source_object_coverage_denominator"
            rec["route_reason"] = "Registry metadata indicates pair/context evidence but no machine-readable values."
        elif rec["inventory_status"] in {"catalog_not_integrated", "catalog_integrated"}:
            rec["best_route"] = "duplicate_or_alias_support_only"
            rec["plot_universe_route"] = "plot1d_source_object_coverage_denominator"
            rec["route_reason"] = "Catalog record appears useful for support/dedupe but does not add a current subplot row."
        elif relevance == "yes":
            rec["best_route"] = "registry_untriaged_or_context_only"
            rec["route_reason"] = "Known Figure 1-relevant registry/search record, but no current local value route is confirmed in this projection."
        else:
            rec["best_route"] = "remain_context_or_rejected_no_alternate_subplot"
            rec["route_reason"] = "No current Figure 1 relevance or value route is recorded."
        rec["mapping_confidence"] = "source_record"
        merge_record(records, f"corpora:{slug(key)}", rec)


def finalize(records: dict[str, dict[str, Any]]) -> pd.DataFrame:
    finalized: list[dict[str, Any]] = []
    for rec in records.values():
        route, plot, reason = choose_route(rec)
        if route_priority(route) >= route_priority(clean(rec.get("best_route"))):
            rec["best_route"] = route
            rec["plot_universe_route"] = plot
            rec["route_reason"] = reason
        rec["route_status"] = clean(rec.get("route_status")) or rec["best_route"]
        finalized.append(rec)
    df = pd.DataFrame(finalized)
    if df.empty:
        return df
    sort_cols = ["best_route", "strict_figure1a_rows", "d_equivalent_rows", "native_effect_rows", "roster_only_rows"]
    df["_priority"] = df["best_route"].map(route_priority)
    df = df.sort_values(["_priority", *sort_cols[1:], "object_name"], ascending=[False, False, False, False, False, True])
    return df.drop(columns=["_priority"])


def build_summary(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()
    disposition = read_tsv(COVERAGE_ROW_DISPOSITION)
    disposition_counts = {
        clean(row.get("disposition_label")): as_int(row.get("row_count"))
        for _, row in disposition.iterrows()
    }
    canonical_rows_by_route = {
        "feeds_figure1a_strict_d_n": disposition_counts.get("Strict Figure 1A direct D/N rows", 0),
        "feeds_figure1a_and_coverage_denominator": disposition_counts.get("Strict Figure 1A direct D/N rows", 0),
        "route_to_d_equivalent_diagnostic_worklist": disposition_counts.get("Comparative binary rows with D-equivalent conversion", 0),
        "route_to_native_effect_diagnostic_worklist": disposition_counts.get("Native-effect rows not on D axis", 0),
        "strict_dn_blocked_coverage_only": disposition_counts.get("D/N rows blocked by current Figure 1A rule", 0),
        "route_to_coverage_denominator_catalog": (
            disposition_counts.get("D/N rows blocked by current Figure 1A rule", 0)
            + disposition_counts.get("Pair roster only, public values unavailable", 0)
            + disposition_counts.get("D/N-looking rows with duplicate risk", 0)
        ),
        "route_to_missing_value_repair_worklist": (
            disposition_counts.get("Effect present, N missing", 0)
            + disposition_counts.get("Parsed row grain, no copied effect/N evidence", 0)
        ),
    }
    canonical_basis_by_route = {
        "feeds_figure1a_strict_d_n": rel(COVERAGE_ROW_DISPOSITION),
        "feeds_figure1a_and_coverage_denominator": rel(COVERAGE_ROW_DISPOSITION),
        "route_to_d_equivalent_diagnostic_worklist": rel(COVERAGE_ROW_DISPOSITION),
        "route_to_native_effect_diagnostic_worklist": rel(COVERAGE_ROW_DISPOSITION),
        "strict_dn_blocked_coverage_only": rel(COVERAGE_ROW_DISPOSITION),
        "route_to_coverage_denominator_catalog": rel(COVERAGE_ROW_DISPOSITION),
        "route_to_missing_value_repair_worklist": rel(COVERAGE_ROW_DISPOSITION),
    }
    rows = []
    for route, sub in df.groupby("best_route", dropna=False):
        rows.append(
            {
                "best_route": route,
                "records": len(sub),
                "canonical_counted_rows_for_route": canonical_rows_by_route.get(route, ""),
                "canonical_count_basis": canonical_basis_by_route.get(route, ""),
                "strict_figure1a_rows": int(sub["strict_figure1a_rows"].map(as_int).sum()),
                "strict_dn_blocked_rows": int(sub["strict_dn_blocked_rows"].map(as_int).sum()),
                "d_equivalent_rows": int(sub["d_equivalent_rows"].map(as_int).sum()),
                "native_effect_rows": int(sub["native_effect_rows"].map(as_int).sum()),
                "roster_only_rows": int(sub["roster_only_rows"].map(as_int).sum()),
                "effect_present_n_missing_rows": int(sub["effect_present_n_missing_rows"].map(as_int).sum()),
                "repair_or_parser_rows": int(sub["repair_or_parser_rows"].map(as_int).sum()),
                "duplicate_or_alias_rows": int(sub["duplicate_or_alias_rows"].map(as_int).sum()),
                "context_or_rejected_records": int(sub["context_or_rejected_records"].map(as_int).sum()),
            }
        )
    summary = pd.DataFrame(rows)
    summary["_priority"] = summary["best_route"].map(route_priority)
    return summary.sort_values(["_priority", "records"], ascending=[False, False]).drop(columns=["_priority"])


def write_report(df: pd.DataFrame, summary: pd.DataFrame) -> None:
    route_counts = {r["best_route"]: r for _, r in summary.iterrows()}

    def fmt(route: str, field: str = "records") -> int:
        row = route_counts.get(route)
        return int(row[field]) if row is not None else 0

    def canonical(route: str) -> int:
        row = route_counts.get(route)
        return as_int(row.get("canonical_counted_rows_for_route")) if row is not None else 0

    lines = [
        "# Figure 1 Corpus Alternate Route Audit",
        "",
        "Generated by `scripts/audit_figure1_corpus_alternate_routes.py` on 2026-05-04.",
        "",
        "This is a corpus/source-family projection over the existing row diagnostics. It does not promote rows into root tables.",
        "",
        "## Summary",
        "",
        f"- Strict Figure 1A source-family/source-record routes: {fmt('feeds_figure1a_strict_d_n') + fmt('feeds_figure1a_and_coverage_denominator')} records.",
        f"- D-equivalent route records: {fmt('route_to_d_equivalent_diagnostic_worklist')} records; {canonical('route_to_d_equivalent_diagnostic_worklist'):,} canonical counted rows.",
        f"- Native-effect route records: {fmt('route_to_native_effect_diagnostic_worklist')} records; {canonical('route_to_native_effect_diagnostic_worklist'):,} canonical counted rows.",
        f"- Missing-value/parser repair records: {fmt('route_to_missing_value_repair_worklist')} records.",
        f"- Coverage/denominator-only records: {fmt('route_to_coverage_denominator_catalog') + fmt('strict_dn_blocked_coverage_only')} records.",
        f"- Context/rejected/untriaged records: {fmt('remain_context_or_rejected_no_alternate_subplot') + fmt('registry_untriaged_or_context_only')} records.",
        "",
        "The TSV keeps raw audit-row count columns because a corpus can appear in several projections. Use `canonical_counted_rows_for_route` for route-level counts.",
        "",
        "## Interpretation",
        "",
        "The second pass does not expose another large hidden alternate-plot source. The only concrete value-bearing alternate routes remain the comparative clinical/binary D-equivalent rows and the native response-rate rows. The large remaining corpora mostly land in coverage denominator or missing-value repair because they have pair rosters, effect values without N, deleted/request-only sheets, metric mismatch, or context-only registry records.",
        "",
        "## Generated Artifacts",
        "",
        f"- Corpus audit table: `{rel(OUT_TSV)}`",
        f"- Corpus audit summary: `{rel(OUT_SUMMARY)}`",
        f"- Row-level alternate recheck: `{rel(RECHECK)}`",
        f"- Universe coverage rows: `{rel(UNIVERSE_ROWS)}`",
    ]
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

    records: dict[str, dict[str, Any]] = {}
    add_root_pair_records(records)
    add_universe_records(records)
    add_recheck_records(records)
    add_raw_viability_records(records)
    add_corpora_records(records)

    df = finalize(records)
    summary = build_summary(df)
    df.to_csv(OUT_TSV, sep="\t", index=False)
    summary.to_csv(OUT_SUMMARY, sep="\t", index=False)
    write_report(df, summary)
    print(f"Wrote {len(df):,} corpus audit records -> {rel(OUT_TSV)}")
    print(f"Wrote summary -> {rel(OUT_SUMMARY)}")
    print(f"Wrote report -> {rel(OUT_MD)}")


if __name__ == "__main__":
    main()
