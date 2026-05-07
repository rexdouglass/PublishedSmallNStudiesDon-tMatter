#!/usr/bin/env python3
"""Write final row-or-not dispositions for individual replication candidates."""

from __future__ import annotations

import argparse
import hashlib
import re
from pathlib import Path
from typing import Any

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
WORKLIST_DIR = ROOT / "steps" / "individual_replication_papers" / "figure1"
VALUE_SCAN = WORKLIST_DIR / "individual-paper-value-scan-batch001.tsv"
PROMOTION_PROPOSAL = WORKLIST_DIR / "individual-paper-promotion-proposal.tsv"
ROOT_PAIRS = ROOT / "FIGURE1_REPLICATION_PAIRS.tsv"

SPECIAL_ROOT_MATCHES = {
    # The search candidate names Many Labs 4 mortality-salience directly; the
    # root row is a manual local meta-analysis row rather than a DOI-title row,
    # so text matching alone does not always catch it.
    "api_candidate_6628c13a9b511007": "fig1_pair_16627351846165e7",
    # The linguistic-frame candidate is represented by the locally rebuilt
    # clean CSV rows, not by the Wiley DOI/title text.
    "api_candidate_21b882b2a3dc29de": "fig1_pair_b39698ee4a817624|fig1_pair_1ed3a5d797fe78b7|fig1_pair_0ef063a84e329f7b|fig1_pair_1c2370e84fe33ac2|fig1_pair_030e22d3cc99371a|fig1_pair_5ac42add6cce8205",
    # Galak and Nelson's Bem Study 8 replication is already represented in the
    # manual Galak et al. 2012 psi meta-analysis row.
    "api_candidate_fbe05a26e9edabb8": "fig1_pair_522390bddbfb99c0",
}


def batch_paths(batch_id: str) -> dict[str, Path]:
    return {
        "triage": WORKLIST_DIR / f"individual-paper-search-triage-{batch_id}.tsv",
        "mirror_status": WORKLIST_DIR / f"individual-paper-source-mirror-{batch_id}.tsv",
        "out_candidates": WORKLIST_DIR / f"individual-paper-row-disposition-{batch_id}.tsv",
        "out_result_options": WORKLIST_DIR / f"individual-paper-result-option-disposition-{batch_id}.tsv",
        "out_report": ROOT / "reports" / f"figure1_individual_replication_row_disposition_{batch_id}_2026-05-05.md",
    }


def clean(value: Any) -> str:
    if value is None:
        return ""
    return str(value).replace("\t", " ").replace("\n", " ").replace("\r", " ").strip()


def stable_id(prefix: str, *parts: Any) -> str:
    payload = "||".join(clean(part) for part in parts)
    return f"{prefix}_{hashlib.sha1(payload.encode('utf-8')).hexdigest()[:16]}"


def read_tsv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path, sep="\t", dtype=str, keep_default_na=False).fillna("")


def read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path, dtype=str, keep_default_na=False).fillna("")


def norm_text(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", " ", clean(value).lower()).strip()


def root_haystack(root: pd.DataFrame) -> pd.Series:
    if root.empty:
        return pd.Series(dtype=str)
    return root.astype(str).agg(" ".join, axis=1).str.lower()


def match_root(row: pd.Series, root: pd.DataFrame, hay: pd.Series) -> tuple[str, str]:
    if root.empty:
        return "", ""
    candidate_id = clean(row.get("candidate_id"))
    if candidate_id in SPECIAL_ROOT_MATCHES and "figure1_replication_pair_id" in root.columns:
        pair_ids = [part for part in SPECIAL_ROOT_MATCHES[candidate_id].split("|") if part]
        hits = root[root["figure1_replication_pair_id"].isin(pair_ids)]
        if not hits.empty:
            pair_id = "|".join(sorted(set(hits["figure1_replication_pair_id"].astype(str))))
            datasets = "|".join(sorted(set(hits["source_dataset"].astype(str))))
            return pair_id, datasets
    masks = []
    for field in ["original_doi", "replication_doi"]:
        value = clean(row.get(field)).lower()
        if value:
            masks.append(hay.str.contains(value, regex=False, na=False))
    title_masks = []
    for field in ["original_title", "replication_title"]:
        value = norm_text(row.get(field))
        if len(value) >= 18:
            title_masks.append(hay.str.contains(value, regex=False, na=False))
    mask = pd.Series(False, index=root.index)
    if masks:
        for item in masks:
            mask |= item
    if not mask.any() and title_masks:
        for item in title_masks:
            mask |= item
    hits = root[mask]
    if hits.empty:
        return "", ""
    pair_ids = "|".join(sorted(set(hits["figure1_replication_pair_id"].astype(str))))
    datasets = "|".join(sorted(set(hits["source_dataset"].astype(str))))
    return pair_ids, datasets


def classify_false_positive(row: pd.Series) -> bool:
    text = norm_text(row.get("candidate_name"))
    seed_only_terms = [
        "kinds of replication",
        "replication matters",
        "publication bias",
        "supplemental material",
        "making replication mainstream",
        "philosophy of science",
        "registered reports",
        "visualization effect size and replication of measurement invariance",
        "meta analysis",
        "systematic review",
        "protocol",
        "commentary",
    ]
    return any(term in text for term in seed_only_terms)


def build_dispositions(batch_id: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    paths = batch_paths(batch_id)
    triage = read_tsv(paths["triage"])
    mirror = read_tsv(paths["mirror_status"])
    scan = read_tsv(VALUE_SCAN)
    proposal = read_tsv(PROMOTION_PROPOSAL)
    root = read_tsv(ROOT_PAIRS)
    hay = root_haystack(root)
    triage_candidate_ids = set(triage["candidate_id"].astype(str)) if not triage.empty and "candidate_id" in triage.columns else set()
    if triage_candidate_ids and not proposal.empty and "candidate_id" in proposal.columns:
        proposal = proposal[proposal["candidate_id"].isin(triage_candidate_ids)].copy()

    mirror_summary = pd.DataFrame()
    if not mirror.empty:
        mirror_summary = (
            mirror.assign(mirrored_int=mirror["mirror_status"].eq("mirrored").astype(int))
            .groupby("candidate_id", as_index=False)
            .agg(
                source_url_count=("source_url", "count"),
                mirrored_source_count=("mirrored_int", "sum"),
                mirror_errors=("error_or_blocker", lambda s: "|".join(sorted({clean(v) for v in s if clean(v)}))),
            )
        )
    proposal_summary = pd.DataFrame()
    if not proposal.empty:
        proposal_summary = (
            proposal.assign(promoted_int=proposal["promotion_decision"].eq("promote_to_harvested_pair_contract").astype(int))
            .groupby("candidate_id", as_index=False)
            .agg(
                result_option_count=("value_scan_id", "count"),
                promoted_result_option_count=("promoted_int", "sum"),
                held_result_option_count=("promoted_int", lambda s: int((s == 0).sum())),
                scan_decisions=("scan_decision", lambda s: " | ".join(sorted({clean(v) for v in s if clean(v)}))),
                held_next_actions=("next_action", lambda s: " | ".join(sorted({clean(v) for v in s if clean(v)}))),
                promoted_pair_ids=("pair_id", lambda s: "|".join(sorted({clean(v) for v in s if clean(v)}))),
            )
        )

    rows: list[dict[str, Any]] = []
    for _, row in triage.iterrows():
        candidate_id = clean(row.get("candidate_id"))
        root_pair_ids, root_datasets = match_root(row, root, hay)
        local_match_ids = clean(row.get("matched_root_pair_ids"))
        if local_match_ids and not root_pair_ids:
            root_pair_ids = local_match_ids

        prop = proposal_summary[proposal_summary["candidate_id"].eq(candidate_id)] if not proposal_summary.empty else pd.DataFrame()
        mir = mirror_summary[mirror_summary["candidate_id"].eq(candidate_id)] if not mirror_summary.empty else pd.DataFrame()
        promoted_count = int(prop["promoted_result_option_count"].iloc[0]) if not prop.empty else 0
        held_count = int(prop["held_result_option_count"].iloc[0]) if not prop.empty else 0
        result_count = int(prop["result_option_count"].iloc[0]) if not prop.empty else 0
        mirrored_count = int(mir["mirrored_source_count"].iloc[0]) if not mir.empty else 0
        source_count = int(mir["source_url_count"].iloc[0]) if not mir.empty else 0
        mirror_errors = clean(mir["mirror_errors"].iloc[0]) if not mir.empty else ""
        held_next = clean(prop["held_next_actions"].iloc[0]) if not prop.empty else ""
        scan_decisions = clean(prop["scan_decisions"].iloc[0]) if not prop.empty else ""
        scan_decision_parts = [part.strip() for part in scan_decisions.split("|") if part.strip()]

        route_decision = clean(row.get("route_decision"))
        candidate_route = clean(row.get("candidate_route"))
        manifest_path = clean(row.get("manifest_path"))
        original_title = clean(row.get("original_title"))
        candidate_name = clean(row.get("candidate_name"))

        if promoted_count:
            final_status = "promoted_to_current_root_row"
            final_reason = f"{promoted_count} result option(s) promoted and rebuilt into FIGURE1_REPLICATION_PAIRS.tsv."
        elif root_pair_ids:
            final_status = "already_in_current_root_table"
            final_reason = "Current root table already contains a matching DOI/title/source-family row; no new row needed."
        elif held_count:
            if scan_decision_parts and all(part.startswith("not_row_") for part in scan_decision_parts):
                final_status = "not_row_rejected_after_value_scan"
                final_reason = held_next or "Value scan found relation evidence but no current Figure 1 row under the extraction/routing policy."
            elif scan_decision_parts and any(
                part.startswith("source_blocked")
                or part.startswith("manual_acquisition")
                or part.startswith("needs_event_counts")
                for part in scan_decision_parts
            ):
                final_status = "not_row_source_blocked_or_manual_acquisition"
                final_reason = held_next or "Value scan found a plausible row but source-object acquisition or event-count extraction is still blocked."
            else:
                final_status = "held_not_row_value_or_policy_blocker"
                final_reason = held_next or "Value scan found a real target but promotion is blocked by exact-N, effect-policy, or source-object work."
        elif classify_false_positive(row):
            final_status = "not_row_rejected_seed_or_non_pair"
            final_reason = "Search hit is a review/methodology/supplement/context item, not an individual original-vs-replication result pair."
        elif route_decision == "route_to_coverage_only" and ("unresolved original target" in candidate_name.lower() or not original_title):
            final_status = "not_row_unresolved_original_target"
            final_reason = "Metadata hit has replication language but no resolved original paper/result target; retained only as a no-repull/search lead."
        elif route_decision == "route_to_coverage_only":
            final_status = "held_not_row_needs_value_extraction"
            final_reason = "Relation target is plausible, but source values/Ns are not extracted or verified."
        elif route_decision.startswith("route_to_"):
            final_status = "held_not_row_no_value_scan_yet"
            final_reason = "Candidate is routed to a worklist but no promoted value-scan row exists yet."
        else:
            final_status = "not_row_rejected_or_duplicate"
            final_reason = clean(row.get("route_reason")) or "No row route remains after dedupe/triage."

        rows.append(
            {
                "candidate_disposition_id": stable_id("row_disposition", candidate_id, final_status),
                "candidate_id": candidate_id,
                "candidate_name": candidate_name,
                "manifest_path": manifest_path,
                "candidate_route": candidate_route,
                "route_decision": route_decision,
                "final_row_status": final_status,
                "final_row_reason": final_reason,
                "promoted_result_option_count": promoted_count,
                "held_result_option_count": held_count,
                "value_scanned_result_option_count": result_count,
                "current_root_pair_ids": root_pair_ids,
                "current_root_source_datasets": root_datasets,
                "source_url_count": source_count,
                "mirrored_source_count": mirrored_count,
                "mirror_errors": mirror_errors,
                "next_action": "" if final_status in {"promoted_to_current_root_row", "already_in_current_root_table", "not_row_rejected_seed_or_non_pair", "not_row_rejected_after_value_scan"} else final_reason,
            }
        )

    result_rows: list[dict[str, Any]] = []
    if not proposal.empty:
        root_by_native = root.set_index("native_pair_id", drop=False) if not root.empty and "native_pair_id" in root.columns else pd.DataFrame()
        for _, row in proposal.iterrows():
            pair_id = clean(row.get("pair_id"))
            root_pair_id = ""
            if not root_by_native.empty and pair_id in root_by_native.index:
                hit = root_by_native.loc[pair_id]
                if isinstance(hit, pd.DataFrame):
                    root_pair_id = "|".join(sorted(set(hit["figure1_replication_pair_id"].astype(str))))
                else:
                    root_pair_id = clean(hit.get("figure1_replication_pair_id"))
            promotion = clean(row.get("promotion_decision"))
            scan_decision = clean(row.get("scan_decision"))
            if root_pair_id:
                final_result_status = "row_in_current_root_table"
            elif scan_decision.startswith("not_row_"):
                final_result_status = "not_row_rejected_after_value_scan"
            elif (
                scan_decision.startswith("source_blocked")
                or scan_decision.startswith("manual_acquisition")
                or scan_decision.startswith("needs_event_counts")
            ):
                final_result_status = "not_row_source_blocked_or_manual_acquisition"
            else:
                final_result_status = "not_row_held"
            result_rows.append(
                {
                    "result_option_disposition_id": stable_id("result_disposition", row.get("value_scan_id"), row.get("candidate_id")),
                    "value_scan_id": clean(row.get("value_scan_id")),
                    "candidate_id": clean(row.get("candidate_id")),
                    "outcome": clean(row.get("outcome")),
                    "promotion_decision": promotion,
                    "final_result_status": final_result_status,
                    "root_pair_id": root_pair_id,
                    "D_original": clean(row.get("D_original")),
                    "N_original": clean(row.get("N_original")),
                    "D_replication": clean(row.get("D_replication")),
                    "N_replication": clean(row.get("N_replication")),
                    "next_action": clean(row.get("next_action")),
                }
            )
    return pd.DataFrame(rows).fillna(""), pd.DataFrame(result_rows).fillna("")


def write_report(candidates: pd.DataFrame, result_options: pd.DataFrame, batch_id: str) -> None:
    paths = batch_paths(batch_id)
    lines = [
        f"# Figure 1 Individual Replication Row Disposition - {batch_id}",
        "",
        "This report answers whether each individual-replication candidate is a current row, already represented, held, or not a row.",
        "",
        "## Candidate Summary",
        "",
    ]
    for status, count in candidates["final_row_status"].value_counts().sort_index().items():
        lines.append(f"- `{status}`: {count:,}")
    lines.extend(["", "## Result-Option Summary", ""])
    if result_options.empty:
        lines.append("- No result-option value-scan rows.")
    else:
        for status, count in result_options["final_result_status"].value_counts().sort_index().items():
            lines.append(f"- `{status}`: {count:,}")
    lines.extend(
        [
            "",
            "## Current Promoted Rows",
            "",
        ]
    )
    promoted = result_options[result_options["final_result_status"].eq("row_in_current_root_table")] if not result_options.empty else pd.DataFrame()
    if promoted.empty:
        lines.append("- None.")
    else:
        for row in promoted.itertuples(index=False):
            lines.append(
                f"- `{row.root_pair_id}` / `{row.candidate_id}`: {row.outcome}; "
                f"D {row.D_original} -> {row.D_replication}; N {row.N_original} -> {row.N_replication}."
            )
    lines.extend(
        [
            "",
            "## Artifacts",
            "",
            f"- `{paths['out_candidates'].relative_to(ROOT)}`",
            f"- `{paths['out_result_options'].relative_to(ROOT)}`",
        ]
    )
    paths["out_report"].write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch-id", default="batch001")
    parser.add_argument("--replace", action="store_true")
    args = parser.parse_args()
    paths = batch_paths(args.batch_id)
    paths["out_candidates"].parent.mkdir(parents=True, exist_ok=True)
    paths["out_report"].parent.mkdir(parents=True, exist_ok=True)
    candidates, result_options = build_dispositions(args.batch_id)
    candidates.to_csv(paths["out_candidates"], sep="\t", index=False)
    result_options.to_csv(paths["out_result_options"], sep="\t", index=False)
    write_report(candidates, result_options, args.batch_id)
    print(f"Wrote {paths['out_candidates']} ({len(candidates)} candidates)")
    print(f"Wrote {paths['out_result_options']} ({len(result_options)} result options)")
    print(f"Wrote {paths['out_report']}")


if __name__ == "__main__":
    main()
