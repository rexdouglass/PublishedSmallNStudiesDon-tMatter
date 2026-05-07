#!/usr/bin/env python3
"""Close the corpus/dataset-level Figure 1 mining pass.

This script is intentionally an audit projection. It does not promote or edit
root result tables. Its purpose is to make the handoff boundary explicit before
moving from many-replication corpora to individual-paper mining.
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path
from typing import Any

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "steps" / "corpus_results" / "figure1" / "corpus_closure"
OUT_ACTIONS = OUT_DIR / "figure1-corpus-dataset-closure-actions.tsv"
OUT_SUMMARY = OUT_DIR / "figure1-corpus-dataset-closure-summary.tsv"
OUT_REPORT = ROOT / "reports" / "figure1_corpus_dataset_closure_2026-05-05.md"

ROOT_PAIRS = ROOT / "FIGURE1_REPLICATION_PAIRS.tsv"
DN_PAIRS = ROOT / "steps" / "corpus_results" / "figure1" / "dn_check" / "figure1-corpus-dn-check-pairs.tsv"
DN_SIDES = ROOT / "steps" / "corpus_results" / "figure1" / "dn_check" / "figure1-corpus-dn-check-strict-result-sides.tsv"
RAW_VIABILITY = ROOT / "steps" / "corpus_results" / "figure1" / "figure1-raw-viability-summary.tsv"
FORRT_SCAN = ROOT / "steps" / "corpus_results" / "figure1" / "research_followup_20260504" / "forrt-reversals-conservative-candidate-scan.tsv"
RESEARCH_TRIAGE = ROOT / "steps" / "corpus_results" / "figure1" / "research_followup_20260504" / "research-followup-triage.tsv"
RCT_SCAN = ROOT / "steps" / "corpus_results" / "figure1" / "research_followup_20260504" / "rct-duplicate-schema-scan.tsv"
LOCAL_MINING_STATUS = ROOT / "steps" / "corpus_results" / "figure1" / "remaining_local_mining" / "remaining-local-mining-status.tsv"
GPT_BATCH2_STATUS = ROOT / "steps" / "corpus_results" / "figure1" / "gpt_candidate_pair_mining" / "gpt_candidate_batch2_mining_status.tsv"
UNIVERSE_SUMMARY = ROOT / "steps" / "corpus_results" / "figure1" / "universe_coverage" / "figure1-universe-coverage-summary.tsv"
ROW_DISPOSITION = ROOT / "steps" / "corpus_results" / "figure1" / "coverage_loss_accounting" / "figure1-row-disposition.tsv"
ALT_AUDIT = ROOT / "steps" / "corpus_results" / "figure1" / "alternate_route_recheck" / "figure1-corpus-alternate-route-audit.tsv"
STAGED_SCAN = ROOT / "steps" / "corpus_results" / "figure1" / "remaining_local_mining" / "staged-unpromoted-scan.tsv"


def clean(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and math.isnan(value):
        return ""
    return str(value).replace("\t", " ").replace("\n", " ").replace("\r", " ").strip()


def read_tsv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path, sep="\t", dtype=str).fillna("")


def rel(path: Path | str) -> str:
    text = clean(path)
    if not text:
        return ""
    try:
        return str(Path(text).resolve().relative_to(ROOT))
    except Exception:
        return text


def to_int(value: Any) -> int:
    text = clean(value)
    if not text:
        return 0
    try:
        return int(float(text))
    except ValueError:
        return 0


def root_counts(source_family_key: str | None = None, source_dataset_contains: str | None = None) -> dict[str, int]:
    pairs = read_tsv(ROOT_PAIRS)
    if pairs.empty:
        return {"root_rows": 0, "strict_included_rows": 0, "strict_blocked_rows": 0}
    mask = pd.Series(True, index=pairs.index)
    if source_family_key:
        mask &= pairs["source_family_key"].eq(source_family_key)
    if source_dataset_contains:
        hay = (
            pairs.get("source_dataset", pd.Series("", index=pairs.index)).astype(str)
            + " "
            + pairs.get("project", pd.Series("", index=pairs.index)).astype(str)
            + " "
            + pairs.get("source_family_label", pd.Series("", index=pairs.index)).astype(str)
        )
        mask &= hay.str.contains(source_dataset_contains, case=False, na=False, regex=False)
    sub = pairs[mask].copy()
    return {
        "root_rows": len(sub),
        "strict_included_rows": int(sub.get("current_plot_rule_status", pd.Series()).eq("included_by_current_figure1_dn_rule").sum()),
        "strict_blocked_rows": int(sub.get("current_plot_rule_status", pd.Series()).eq("excluded_by_current_figure1_dn_rule").sum()),
    }


def dn_counts(project: str | None = None, source_dataset_contains: str | None = None) -> dict[str, int]:
    pairs = read_tsv(DN_PAIRS)
    if pairs.empty:
        return {"dn_pair_rows": 0, "dn_pairs_passing_current_rule": 0, "dn_pairs_blocked_current_rule": 0}
    mask = pd.Series(True, index=pairs.index)
    if project:
        mask &= pairs["project"].eq(project)
    if source_dataset_contains:
        mask &= pairs["source_dataset"].str.contains(source_dataset_contains, case=False, na=False, regex=False)
    sub = pairs[mask].copy()
    return {
        "dn_pair_rows": len(sub),
        "dn_pairs_passing_current_rule": int(sub.get("figure1_rule_check", pd.Series()).eq("passes_d_n_min10_and_larger_n").sum()),
        "dn_pairs_blocked_current_rule": int(sub.get("figure1_rule_check", pd.Series()).eq("blocked_by_n_rule").sum()),
    }


def strict_side_counts(parent_id: str) -> dict[str, int]:
    sides = read_tsv(DN_SIDES)
    if sides.empty:
        return {
            "strict_side_rows": 0,
            "strict_side_pair_ids": 0,
            "strict_side_rows_with_effect_and_n": 0,
        }
    sub = sides[sides["primary_parent_corpus_database_id"].eq(parent_id)].copy()
    d = pd.to_numeric(sub.get("d", pd.Series(dtype=str)), errors="coerce")
    n = pd.to_numeric(sub.get("native_n_total", pd.Series(dtype=str)), errors="coerce")
    return {
        "strict_side_rows": len(sub),
        "strict_side_pair_ids": sub.get("dn_pair_check_id", pd.Series(dtype=str)).nunique(),
        "strict_side_rows_with_effect_and_n": int((d.notna() & n.notna()).sum()),
    }


def raw_viability_counts(parent_id: str) -> dict[str, int | str]:
    raw = read_tsv(RAW_VIABILITY)
    if raw.empty:
        return {
            "raw_parsed_rows": 0,
            "raw_rows_with_effect_n_pair_context": 0,
            "raw_viability_status": "",
            "raw_viability": "",
        }
    sub = raw[raw["parent_corpus_database_id"].eq(parent_id)]
    if sub.empty:
        return {
            "raw_parsed_rows": 0,
            "raw_rows_with_effect_n_pair_context": 0,
            "raw_viability_status": "",
            "raw_viability": "",
        }
    row = sub.iloc[0]
    return {
        "raw_parsed_rows": to_int(row.get("parsed_native_rows")),
        "raw_rows_with_effect_n_pair_context": to_int(row.get("rows_with_effect_n_and_pair_context")),
        "raw_viability_status": clean(row.get("raw_viability_status")),
        "raw_viability": clean(row.get("figure1_viability")),
    }


def universe_count(bucket: str) -> int:
    summary = read_tsv(UNIVERSE_SUMMARY)
    if summary.empty:
        return 0
    sub = summary[summary["bucket"].eq(bucket)]
    if sub.empty:
        return 0
    return to_int(sub.iloc[0].get("rows"))


def row_disposition_count(disposition_id: str) -> int:
    rows = read_tsv(ROW_DISPOSITION)
    if rows.empty:
        return 0
    sub = rows[rows["disposition_id"].eq(disposition_id)]
    if sub.empty:
        return 0
    return to_int(sub.iloc[0].get("row_count"))


def forrt_counts() -> dict[str, int]:
    scan = read_tsv(FORRT_SCAN)
    if scan.empty:
        return {"candidate_rows": 0, "larger_n_candidate_rows": 0, "not_promoted_rows": 0}
    parseable = scan["conservative_parseable"].eq("True")
    return {
        "candidate_rows": int(parseable.sum()),
        "larger_n_candidate_rows": int((parseable & scan["passes_larger_n_if_parseable"].eq("True")).sum()),
        "not_promoted_rows": int(scan["decision"].str.contains("not_promoted", case=False, na=False).sum()),
    }


def triage_row(candidate_key: str) -> dict[str, str]:
    triage = read_tsv(RESEARCH_TRIAGE)
    if triage.empty:
        return {}
    sub = triage[triage["candidate_key"].eq(candidate_key)]
    if sub.empty:
        return {}
    return sub.iloc[0].to_dict()


def status_row(path: Path, key_col: str, key: str) -> dict[str, str]:
    df = read_tsv(path)
    if df.empty or key_col not in df.columns:
        return {}
    sub = df[df[key_col].eq(key)]
    if sub.empty:
        return {}
    return sub.iloc[0].to_dict()


def make_action(**kwargs: Any) -> dict[str, Any]:
    cols = {
        "closure_id": "",
        "corpus_or_dataset": "",
        "closure_bucket": "",
        "records_reviewed": 0,
        "root_rows": 0,
        "strict_included_rows": 0,
        "strict_blocked_rows": 0,
        "alternate_d_equivalent_rows": 0,
        "native_effect_rows": 0,
        "coverage_or_roster_rows": 0,
        "effect_present_n_missing_rows": 0,
        "duplicate_risk_rows": 0,
        "false_positive_rows": 0,
        "rows_promoted_by_this_closure_pass": 0,
        "decision": "",
        "reason": "",
        "next_step_before_individual_phase": "",
        "evidence_paths": "",
    }
    cols.update(kwargs)
    return cols


def build_actions() -> pd.DataFrame:
    actions: list[dict[str, Any]] = []

    rpcb_root = root_counts("rpcb")
    rpcb_dn = dn_counts("RPCB")
    rpcb_raw = raw_viability_counts("raw_corpus:rpcb")
    rpcb_sides = strict_side_counts("raw_corpus:rpcb")
    actions.append(
        make_action(
            closure_id="rpcb_effect_level_table_reconciled",
            corpus_or_dataset="Reproducibility Project: Cancer Biology / raw_corpus:rpcb",
            closure_bucket="already_represented_or_current_rule_blocked",
            records_reviewed=max(rpcb_raw["raw_parsed_rows"], rpcb_sides["strict_side_pair_ids"], rpcb_root["root_rows"]),
            root_rows=rpcb_root["root_rows"],
            strict_included_rows=rpcb_root["strict_included_rows"],
            strict_blocked_rows=rpcb_root["strict_blocked_rows"],
            decision="closed_no_new_corpus_rows",
            reason=(
                f"Local RPCB effect-level bytes were parsed ({rpcb_raw['raw_rows_with_effect_n_pair_context']} native rows with effect/N/pair context; "
                f"{rpcb_sides['strict_side_rows_with_effect_and_n']} strict side rows with copied effect and N). "
                f"The current D/N table already carries {rpcb_dn['dn_pair_rows']} RPCB pairs; "
                f"{rpcb_dn['dn_pairs_passing_current_rule']} pass the current strict rule and {rpcb_dn['dn_pairs_blocked_current_rule']} are blocked by N gates. "
                "The remaining raw assertions are missing SMD/N on at least one side, duplicate aliases, or source-support material for provenance hardening."
            ),
            next_step_before_individual_phase="none_for_corpus_mining; resume source_result/source_result_support hardening later",
            evidence_paths=" | ".join(
                [
                    rel(RAW_VIABILITY),
                    rel(DN_SIDES),
                    rel(DN_PAIRS),
                    rel(ROOT_PAIRS),
                ]
            ),
        )
    )

    ml2_root = root_counts("many_labs_2")
    ml2_dn = dn_counts("Many Labs 2")
    ml2_raw = raw_viability_counts("many_labs_2 | doi:10.1177/2515245918810225")
    ml2_sides = strict_side_counts("many_labs_2 | doi:10.1177/2515245918810225")
    actions.append(
        make_action(
            closure_id="many_labs_2_public_join_reconciled",
            corpus_or_dataset="Many Labs 2",
            closure_bucket="already_represented",
            records_reviewed=max(ml2_raw["raw_parsed_rows"], ml2_sides["strict_side_pair_ids"], ml2_root["root_rows"]),
            root_rows=ml2_root["root_rows"],
            strict_included_rows=ml2_root["strict_included_rows"],
            strict_blocked_rows=ml2_root["strict_blocked_rows"],
            decision="closed_no_new_corpus_rows",
            reason=(
                f"The ML2 public join yields {ml2_dn['dn_pair_rows']} D/N pairs, all {ml2_dn['dn_pairs_passing_current_rule']} passing the current rule. "
                f"Strict side output contains {ml2_sides['strict_side_rows']} original/replication side assertions. "
                "The larger 91-row masterkey includes metadata/original-effect rows not all used by the Figure 1 pair join."
            ),
            next_step_before_individual_phase="none_for_corpus_mining",
            evidence_paths=" | ".join([rel(RAW_VIABILITY), rel(DN_SIDES), rel(DN_PAIRS), rel(ROOT_PAIRS)]),
        )
    )

    psa_root = root_counts(source_dataset_contains="PSA-006 trolley country rows")
    actions.append(
        make_action(
            closure_id="psa_006_infosheet_false_positive_demoted",
            corpus_or_dataset="PSA-006 trolley",
            closure_bucket="false_positive_context_table",
            records_reviewed=271,
            root_rows=psa_root["root_rows"],
            strict_included_rows=psa_root["strict_included_rows"],
            strict_blocked_rows=psa_root["strict_blocked_rows"],
            false_positive_rows=271,
            decision="closed_parser_false_positive",
            reason=(
                "The 271-row table flagged in raw viability is trolley_infosheet.csv, an author/contribution/context table. "
                "It has no effect/N evidence. The actual PSA-006 country-level result rows are already represented separately in the root table."
            ),
            next_step_before_individual_phase="none_for_corpus_mining",
            evidence_paths=" | ".join([rel(RAW_VIABILITY), rel(DN_PAIRS), rel(ROOT_PAIRS)]),
        )
    )

    fc = forrt_counts()
    forrt_root = root_counts(source_dataset_contains="FORRT Reversals source-object extraction")
    actions.append(
        make_action(
            closure_id="forrt_reversals_duplicate_risk_closed",
            corpus_or_dataset="FORRT Replications and Reversals",
            closure_bucket="duplicate_risk_or_support_only",
            records_reviewed=431,
            root_rows=forrt_root["root_rows"],
            strict_included_rows=forrt_root["strict_included_rows"],
            strict_blocked_rows=forrt_root["strict_blocked_rows"],
            duplicate_risk_rows=fc["candidate_rows"],
            decision="closed_no_bulk_promotion",
            reason=(
                f"The conservative HTML scan found {fc['candidate_rows']} D/N-looking entries and {fc['larger_n_candidate_rows']} with larger replication N. "
                "One source-object-backed row is already in the root table; the remaining entries are narrative/aggregate assertions with high duplication risk against FReD/current rows."
            ),
            next_step_before_individual_phase="none; any remaining FORRT entries require individual source-object extraction, not corpus mining",
            evidence_paths=" | ".join([rel(FORRT_SCAN), rel(RESEARCH_TRIAGE), rel(ROOT_PAIRS)]),
        )
    )

    actions.append(
        make_action(
            closure_id="alternate_d_equivalent_panel_finalized",
            corpus_or_dataset="Comparative clinical/binary rows",
            closure_bucket="alternate_subplot_staged",
            records_reviewed=row_disposition_count("figure1b_binary_d_equivalent"),
            alternate_d_equivalent_rows=row_disposition_count("figure1b_binary_d_equivalent"),
            decision="closed_staged_for_figure1b_not_figure1a",
            reason=(
                "Rows with comparative binary counts can be expressed as D-equivalent using the documented log(OR)*sqrt(3)/pi route. "
                "They remain separate from strict Figure 1A because they are conversion-tier rows rather than direct D/SMD rows."
            ),
            next_step_before_individual_phase="none_for_corpus_mining; use Figure 1B/diagnostic route if plotted",
            evidence_paths=" | ".join([rel(UNIVERSE_SUMMARY), rel(ROW_DISPOSITION), rel(ALT_AUDIT)]),
        )
    )

    actions.append(
        make_action(
            closure_id="native_response_rate_panel_finalized",
            corpus_or_dataset="Native response-rate rows",
            closure_bucket="alternate_subplot_staged",
            records_reviewed=row_disposition_count("native_effect_retention"),
            native_effect_rows=row_disposition_count("native_effect_retention"),
            decision="closed_staged_for_native_panel_not_figure1a",
            reason=(
                "Native response-rate rows have N on both sides but no defensible treatment-effect D conversion under the current rule. "
                "They are retained for a native-scale diagnostic or denominator accounting, not promoted to Figure 1A."
            ),
            next_step_before_individual_phase="none_for_corpus_mining",
            evidence_paths=" | ".join([rel(UNIVERSE_SUMMARY), rel(ROW_DISPOSITION), rel(ALT_AUDIT)]),
        )
    )

    ying = triage_row("ying_pilot_full_scale")
    ying_root = root_counts("ying_2023_pilot_full_scale_trials")
    actions.append(
        make_action(
            closure_id="ying_pilot_full_scale_request_only_closed",
            corpus_or_dataset="Ying/Ehrhardt pilot-to-full-scale clinical datasets",
            closure_bucket="no_public_value_table",
            records_reviewed=row_disposition_count("roster_only_denominator"),
            root_rows=ying_root["root_rows"],
            strict_included_rows=ying_root["strict_included_rows"],
            strict_blocked_rows=ying_root["strict_blocked_rows"],
            coverage_or_roster_rows=row_disposition_count("roster_only_denominator"),
            decision="closed_until_public_or_user_supplied_data",
            reason=(
                "Public local bytes identify the pilot/full-scale family and pair roster scale, but the row-level effect/N dataset is not publicly mirrored here. "
                f"Research triage decision: {clean(ying.get('decision')) or 'not_promoted_request_or_access_only'}."
            ),
            next_step_before_individual_phase="none; request-only data is out of scope unless the user supplies files",
            evidence_paths=" | ".join([rel(RESEARCH_TRIAGE), rel(ROW_DISPOSITION)]),
        )
    )

    rct = triage_row("rct_duplicate")
    rct_scan = read_tsv(RCT_SCAN)
    actions.append(
        make_action(
            closure_id="rct_duplicate_missing_n_closed",
            corpus_or_dataset="RCT-DUPLICATE RWE emulations",
            closure_bucket="effect_present_n_missing",
            records_reviewed=int(pd.to_numeric(rct_scan.get("rows", pd.Series(dtype=str)), errors="coerce").max()) if not rct_scan.empty else 0,
            effect_present_n_missing_rows=row_disposition_count("effect_present_missing_n"),
            decision="closed_missing_public_n_columns",
            reason=(
                "Public CSVs expose trial/result effect strings and covariates but not clean original RCT or RWE-emulation sample-size columns. "
                f"Research triage decision: {clean(rct.get('decision')) or 'not_promoted_no_public_n_columns'}."
            ),
            next_step_before_individual_phase="none; needs N recovery from restricted/source-specific materials before any row can plot",
            evidence_paths=" | ".join([rel(RCT_SCAN), rel(RESEARCH_TRIAGE), rel(ROW_DISPOSITION)]),
        )
    )

    rgb = triage_row("rgb_health_behavior_family")
    actions.append(
        make_action(
            closure_id="rgb_health_behavior_no_public_master_closed",
            corpus_or_dataset="RGB pilot-vs-larger-trial health-behavior family",
            closure_bucket="no_public_value_table",
            records_reviewed=0,
            decision="closed_until_public_or_user_supplied_data",
            reason=(
                "Article/preprint pages confirm relevant pilot/larger-trial pair and effect-count claims, but no public master workbook/CSV with D/N rows was obtained. "
                f"Research triage decision: {clean(rgb.get('decision')) or 'not_promoted_no_public_master_table_mirrored'}."
            ),
            next_step_before_individual_phase="none; request/source-owner acquisition only",
            evidence_paths=rel(RESEARCH_TRIAGE),
        )
    )

    hagen_status = status_row(LOCAL_MINING_STATUS, "candidate_key", "hagen_hcsp") or status_row(GPT_BATCH2_STATUS, "candidate_key", "hagen_hcsp")
    actions.append(
        make_action(
            closure_id="hagen_deleted_sheet_closed",
            corpus_or_dataset="Hagen Cumulative Science Project I",
            closure_bucket="blocked_access_route",
            records_reviewed=0,
            decision="closed_until_archived_sheet_or_user_file",
            reason=(
                "The public code/app route was mirrored, but the Google Sheet backing data route is deleted/gone and only a codebook is accessible. "
                f"Local status: {clean(hagen_status.get('decision')) or 'blocked_access_route'}."
            ),
            next_step_before_individual_phase="none; needs archived backing sheet or maintainer-provided data",
            evidence_paths=" | ".join([rel(LOCAL_MINING_STATUS), rel(GPT_BATCH2_STATUS)]),
        )
    )

    smiles_status = status_row(LOCAL_MINING_STATUS, "candidate_key", "many_smiles") or status_row(GPT_BATCH2_STATUS, "candidate_key", "many_smiles")
    actions.append(
        make_action(
            closure_id="many_smiles_original_benchmark_closed",
            corpus_or_dataset="Many Smiles Collaboration",
            closure_bucket="missing_original_benchmark",
            records_reviewed=0,
            decision="closed_until_original_benchmark_table_found",
            reason=(
                "Mirrored replication-side data do not expose a clean original benchmark effect plus original N table. "
                f"Local status: {clean(smiles_status.get('decision')) or 'not_promoted_requires_original_benchmark_choice'}."
            ),
            next_step_before_individual_phase="none; needs a source-object with original benchmark D and N before plotting",
            evidence_paths=" | ".join([rel(LOCAL_MINING_STATUS), rel(GPT_BATCH2_STATUS)]),
        )
    )

    for key, label in [
        ("score", "SCORE"),
        ("sports_science_replications", "Sports Science Replication Centre"),
        ("loopr", "LOOPR"),
        ("many_labs_5", "Many Labs 5"),
        ("coppock_2019_generalizability_corpus", "Coppock/COVID online generalizability corpus"),
    ]:
        counts = root_counts(key)
        actions.append(
            make_action(
                closure_id=f"{key}_root_reconciled",
                corpus_or_dataset=label,
                closure_bucket="already_represented_or_current_rule_blocked",
                records_reviewed=counts["root_rows"],
                root_rows=counts["root_rows"],
                strict_included_rows=counts["strict_included_rows"],
                strict_blocked_rows=counts["strict_blocked_rows"],
                decision="closed_no_new_corpus_rows",
                reason=(
                    "The source family is already represented in the current root pair table. "
                    "Remaining local artifact review is provenance/source-object hardening or rule-blocked accounting, not a new corpus mining step."
                ),
                next_step_before_individual_phase="none_for_corpus_mining",
                evidence_paths=" | ".join([rel(ROOT_PAIRS), rel(ALT_AUDIT), rel(RAW_VIABILITY)]),
            )
        )

    staged = read_tsv(STAGED_SCAN)
    unpromoted = 0
    if not staged.empty:
        promoted = staged.get("promoted_or_related", pd.Series("", index=staged.index)).eq("True")
        complete = pd.to_numeric(staged.get("obvious_complete_dn_rows", pd.Series("0", index=staged.index)), errors="coerce").fillna(0)
        unpromoted = int((~promoted & (complete <= 0)).sum())
    actions.append(
        make_action(
            closure_id="staged_unpromoted_scan_closed",
            corpus_or_dataset="Previously staged one-row source leads",
            closure_bucket="no_obvious_complete_dn_columns",
            records_reviewed=len(staged),
            false_positive_rows=unpromoted,
            decision="closed_no_bulk_rows",
            reason=(
                f"The staged-unpromoted scan reviewed {len(staged)} staged lead files; {unpromoted} unpromoted leads had no obvious complete D/N columns. "
                "Any further value extraction is individual-paper/source-specific."
            ),
            next_step_before_individual_phase="none_for_corpus_mining",
            evidence_paths=rel(STAGED_SCAN),
        )
    )

    return pd.DataFrame(actions)


def write_summary(actions: pd.DataFrame) -> pd.DataFrame:
    numeric_cols = [
        "records_reviewed",
        "root_rows",
        "strict_included_rows",
        "strict_blocked_rows",
        "alternate_d_equivalent_rows",
        "native_effect_rows",
        "coverage_or_roster_rows",
        "effect_present_n_missing_rows",
        "duplicate_risk_rows",
        "false_positive_rows",
        "rows_promoted_by_this_closure_pass",
    ]
    for col in numeric_cols:
        actions[col] = pd.to_numeric(actions[col], errors="coerce").fillna(0).astype(int)
    summary = (
        actions.groupby(["closure_bucket", "decision"], dropna=False)[numeric_cols]
        .sum()
        .reset_index()
        .sort_values(["closure_bucket", "decision"])
    )
    return summary


def write_report(actions: pd.DataFrame, summary: pd.DataFrame) -> None:
    strict_total = universe_count("strict_current_figure1_included")
    blocked_total = universe_count("strict_dn_available_but_blocked")
    deq_total = universe_count("additional_comparative_binary_d_equivalent_rows")
    native_total = row_disposition_count("native_effect_retention")
    roster_total = row_disposition_count("roster_only_denominator")
    effect_no_n_total = row_disposition_count("effect_present_missing_n")
    promoted = int(pd.to_numeric(actions["rows_promoted_by_this_closure_pass"], errors="coerce").fillna(0).sum())

    lines = [
        "# Figure 1 Corpus/Dataset Closure Pass - 2026-05-05",
        "",
        "## Bottom Line",
        "",
        (
            "This pass closes the remaining corpus/dataset-level mining tasks before moving to individual-paper extraction. "
            f"It promoted {promoted} new strict Figure 1 rows. The current locally observable state remains "
            f"{strict_total} strict Figure 1A rows, {blocked_total} D/N rows blocked by current gates, "
            f"{deq_total} D-equivalent clinical/binary diagnostic rows, {native_total} native-effect diagnostic rows, "
            f"{roster_total} roster-only rows without public values, and {effect_no_n_total} effect-present rows missing public N."
        ),
        "",
        (
            "The remaining work is not bulk corpus mining. It is either provenance hardening for rows already represented, "
            "source-owner/user-file acquisition for request-only datasets, or individual source-object extraction."
        ),
        "",
        "## Closure Summary",
        "",
        "| Closure bucket | Decision | Records reviewed | Strict included | Strict blocked | D-equivalent | Native | Roster/coverage | Effect no N | Duplicate risk | False positives | Promoted here |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in summary.itertuples(index=False):
        lines.append(
            f"| {row.closure_bucket} | {row.decision} | {row.records_reviewed} | {row.strict_included_rows} | "
            f"{row.strict_blocked_rows} | {row.alternate_d_equivalent_rows} | {row.native_effect_rows} | "
            f"{row.coverage_or_roster_rows} | {row.effect_present_n_missing_rows} | {row.duplicate_risk_rows} | "
            f"{row.false_positive_rows} | {row.rows_promoted_by_this_closure_pass} |"
        )
    lines.extend(
        [
            "",
            "## Corpus Decisions",
            "",
            "| Corpus/dataset | Decision | Key counts | Why closed | Next step |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    for row in actions.itertuples(index=False):
        counts = (
            f"root={row.root_rows}; included={row.strict_included_rows}; blocked={row.strict_blocked_rows}; "
            f"D*={row.alternate_d_equivalent_rows}; native={row.native_effect_rows}; roster={row.coverage_or_roster_rows}; "
            f"effect-no-N={row.effect_present_n_missing_rows}; duplicate-risk={row.duplicate_risk_rows}; false-positive={row.false_positive_rows}"
        )
        lines.append(
            f"| {row.corpus_or_dataset} | {row.decision} | {counts} | {row.reason} | {row.next_step_before_individual_phase} |"
        )
    lines.extend(
        [
            "",
            "## Generated Artifacts",
            "",
            f"- `{rel(OUT_ACTIONS)}`",
            f"- `{rel(OUT_SUMMARY)}`",
            f"- `{rel(OUT_REPORT)}`",
            "",
            "This report is an audit projection only. It does not alter `FIGURE1_REPLICATION_PAIRS.tsv`, `source_result.tsv`, or any canonical result table.",
        ]
    )
    OUT_REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--replace", action="store_true")
    args = parser.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    if not args.replace:
        for path in [OUT_ACTIONS, OUT_SUMMARY, OUT_REPORT]:
            if path.exists():
                raise SystemExit(f"{path} exists; pass --replace to overwrite")

    actions = build_actions()
    summary = write_summary(actions)
    actions.to_csv(OUT_ACTIONS, sep="\t", index=False)
    summary.to_csv(OUT_SUMMARY, sep="\t", index=False)
    write_report(actions, summary)
    print(f"Wrote {rel(OUT_ACTIONS)}")
    print(f"Wrote {rel(OUT_SUMMARY)}")
    print(f"Wrote {rel(OUT_REPORT)}")


if __name__ == "__main__":
    main()
