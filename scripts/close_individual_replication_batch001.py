#!/usr/bin/env python3
"""Close an individual-replication search batch.

The row-disposition step decides whether every candidate is a row, already
represented, rejected, unresolved, or held. This closeout step turns that into
the operational artifacts needed before the next batch:

- a manual acquisition queue for source-blocked candidates;
- a dedupe baseline for exact pair/result re-pulls;
- a next-batch starter seed/exclusion table.
"""

from __future__ import annotations

import argparse
import hashlib
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
WORKLIST_DIR = ROOT / "steps" / "individual_replication_papers" / "figure1"

TRIAGE = WORKLIST_DIR / "individual-paper-search-triage-batch001.tsv"
ROW_DISPOSITION = WORKLIST_DIR / "individual-paper-row-disposition-batch001.tsv"
RESULT_DISPOSITION = WORKLIST_DIR / "individual-paper-result-option-disposition-batch001.tsv"
PROMOTION_PROPOSAL = WORKLIST_DIR / "individual-paper-promotion-proposal.tsv"

OUT_MANUAL = WORKLIST_DIR / "individual-paper-manual-acquisition-task-batch001.tsv"
OUT_DEDUPE = WORKLIST_DIR / "individual-paper-dedupe-baseline-batch001.tsv"
OUT_BATCH002 = WORKLIST_DIR / "individual-paper-batch002-dedupe-seed.tsv"
OUT_REPORT = ROOT / "reports" / "figure1_individual_replication_batch001_closeout_2026-05-05.md"
BATCH_ID = "batch001"
NEXT_BATCH_ID = "batch002"


def next_batch_id(batch_id: str) -> str:
    match = re.fullmatch(r"batch(\d+)", batch_id)
    if not match:
        return f"{batch_id}_next"
    return f"batch{int(match.group(1)) + 1:03d}"


def configure_batch(batch_id: str) -> None:
    global TRIAGE, ROW_DISPOSITION, RESULT_DISPOSITION, OUT_MANUAL, OUT_DEDUPE, OUT_BATCH002, OUT_REPORT, BATCH_ID, NEXT_BATCH_ID
    BATCH_ID = batch_id
    NEXT_BATCH_ID = next_batch_id(batch_id)
    TRIAGE = WORKLIST_DIR / f"individual-paper-search-triage-{batch_id}.tsv"
    ROW_DISPOSITION = WORKLIST_DIR / f"individual-paper-row-disposition-{batch_id}.tsv"
    RESULT_DISPOSITION = WORKLIST_DIR / f"individual-paper-result-option-disposition-{batch_id}.tsv"
    OUT_MANUAL = WORKLIST_DIR / f"individual-paper-manual-acquisition-task-{batch_id}.tsv"
    OUT_DEDUPE = WORKLIST_DIR / f"individual-paper-dedupe-baseline-{batch_id}.tsv"
    OUT_BATCH002 = WORKLIST_DIR / f"individual-paper-{NEXT_BATCH_ID}-dedupe-seed.tsv"
    OUT_REPORT = ROOT / f"reports/figure1_individual_replication_{batch_id}_closeout_2026-05-05.md"


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


def norm_text(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", " ", clean(value).lower()).strip()


def collapse(series: pd.Series, sep: str = " | ") -> str:
    return sep.join(sorted({clean(value) for value in series if clean(value)}))


def load_joined() -> pd.DataFrame:
    triage = read_tsv(TRIAGE)
    dispositions = read_tsv(ROW_DISPOSITION)
    if triage.empty or dispositions.empty:
        raise FileNotFoundError("Run the individual-replication triage and row-disposition steps before closeout.")
    joined = dispositions.merge(
        triage[
            [
                "candidate_id",
                "domain",
                "confidence",
                "original_title",
                "original_doi",
                "replication_title",
                "replication_doi",
                "conversion_route",
                "dedupe_risk",
                "source_object_urls_json",
                "relationship_evidence_json",
                "value_availability_json",
                "route_reason",
            ]
        ],
        on="candidate_id",
        how="left",
    ).fillna("")
    return joined


def proposal_summary() -> pd.DataFrame:
    proposal = read_tsv(PROMOTION_PROPOSAL)
    if proposal.empty:
        return pd.DataFrame()
    return (
        proposal.groupby("candidate_id", as_index=False)
        .agg(
            value_scan_ids=("value_scan_id", collapse),
            scan_decisions=("scan_decision", collapse),
            result_option_labels=("outcome", collapse),
            proposal_original_titles=("original_title", collapse),
            proposal_original_dois=("original_doi", collapse),
            proposal_replication_titles=("replication_title", collapse),
            proposal_replication_dois=("replication_doi", collapse),
            local_support_paths=("local_support_paths", collapse),
            original_support_text=("original_support_text", collapse),
            replication_support_text=("replication_support_text", collapse),
            conversion_or_policy_note=("conversion_or_policy_note", collapse),
            proposal_next_actions=("next_action", collapse),
        )
        .fillna("")
    )


def blocker_category(scan_decisions: str, next_action: str) -> str:
    text = f"{scan_decisions} {next_action}".lower()
    if "event_count" in text or "mortality" in text or "trial" in text or "nejm" in text:
        return "event_counts_or_trial_source_needed"
    if "original_n" in text or "original n" in text:
        return "original_n_needed"
    if "source_blocked" in text or "manual_acquisition" in text or "pdf" in text or "supplement" in text:
        return "value_bearing_source_object_needed"
    if "native" in text:
        return "native_only_policy_not_current_figure1"
    return "manual_review_needed"


def priority(row: pd.Series, scan_decisions: str, next_action: str) -> str:
    route = clean(row.get("candidate_route"))
    text = f"{scan_decisions} {next_action}".lower()
    if route in {"strict_figure1a", "d_equivalent_figure1b"} and "source" in text:
        return "high"
    if "event_count" in text or "trial" in text:
        return "high"
    if route in {"native_only", "native_scale_subplot"}:
        return "medium"
    return "medium"


def dedupe_action(status: str) -> str:
    if status == "promoted_to_current_root_row":
        return "skip_exact_pair_result_current_row"
    if status == "already_in_current_root_table":
        return "skip_exact_pair_already_represented"
    if status in {
        "held_not_row_source_blocked_or_manual_acquisition",
        "not_row_source_blocked_or_manual_acquisition",
    }:
        return "route_to_manual_acquisition_not_new_search"
    if status == "not_row_rejected_after_value_scan":
        return "skip_under_current_figure1_policy"
    if status == "not_row_unresolved_original_target":
        return "skip_until_original_target_resolved"
    if status == "not_row_rejected_seed_or_non_pair":
        return "skip_seed_or_non_pair"
    return "manual_review_before_repull"


def build_artifacts() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    joined = load_joined()
    prop = proposal_summary()
    if not prop.empty:
        joined = joined.merge(prop, on="candidate_id", how="left").fillna("")
    else:
        for col in [
            "value_scan_ids",
            "scan_decisions",
            "result_option_labels",
            "proposal_original_titles",
            "proposal_original_dois",
            "proposal_replication_titles",
            "proposal_replication_dois",
            "local_support_paths",
            "original_support_text",
            "replication_support_text",
            "conversion_or_policy_note",
            "proposal_next_actions",
        ]:
            joined[col] = ""

    now = datetime.now(timezone.utc).isoformat(timespec="seconds")

    manual_rows: list[dict[str, Any]] = []
    held = joined[
        joined["final_row_status"].isin(
            [
                "held_not_row_source_blocked_or_manual_acquisition",
                "not_row_source_blocked_or_manual_acquisition",
            ]
        )
    ]
    for _, row in held.iterrows():
        next_action = clean(row.get("next_action")) or clean(row.get("proposal_next_actions"))
        scan_decisions = clean(row.get("scan_decisions"))
        manual_rows.append(
            {
                "manual_acquisition_task_id": stable_id("manual_acq", row.get("candidate_id"), next_action),
                "candidate_id": clean(row.get("candidate_id")),
                "priority": priority(row, scan_decisions, next_action),
                "blocker_category": blocker_category(scan_decisions, next_action),
                "candidate_route": clean(row.get("candidate_route")),
                "candidate_name": clean(row.get("candidate_name")),
                "domain": clean(row.get("domain")),
                "original_title": clean(row.get("proposal_original_titles")) or clean(row.get("original_title")),
                "original_doi": clean(row.get("proposal_original_dois")) or clean(row.get("original_doi")),
                "replication_title": clean(row.get("proposal_replication_titles")) or clean(row.get("replication_title")),
                "replication_doi": clean(row.get("proposal_replication_dois")) or clean(row.get("replication_doi")),
                "result_option_labels": clean(row.get("result_option_labels")),
                "scan_decisions": scan_decisions,
                "needed_evidence": next_action,
                "source_object_urls_json": clean(row.get("source_object_urls_json")),
                "mirrored_source_count": clean(row.get("mirrored_source_count")),
                "mirror_errors": clean(row.get("mirror_errors")),
                "local_support_paths": clean(row.get("local_support_paths")),
                "relationship_evidence_json": clean(row.get("relationship_evidence_json")),
                "conversion_or_policy_note": clean(row.get("conversion_or_policy_note")),
                "created_at": now,
            }
        )

    dedupe_rows: list[dict[str, Any]] = []
    for _, row in joined.iterrows():
        candidate_id = clean(row.get("candidate_id"))
        original_title = clean(row.get("proposal_original_titles")) or clean(row.get("original_title"))
        original_doi = clean(row.get("proposal_original_dois")) or clean(row.get("original_doi"))
        replication_title = clean(row.get("proposal_replication_titles")) or clean(row.get("replication_title"))
        replication_doi = clean(row.get("proposal_replication_dois")) or clean(row.get("replication_doi"))
        status = clean(row.get("final_row_status"))
        dedupe_rows.append(
            {
                "dedupe_baseline_id": stable_id("dedupe", candidate_id, original_doi, replication_doi, status),
                "candidate_id": candidate_id,
                "candidate_name": clean(row.get("candidate_name")),
                "candidate_route": clean(row.get("candidate_route")),
                "final_row_status": status,
                "dedupe_action": dedupe_action(status),
                "original_title": original_title,
                "original_doi": original_doi,
                "replication_title": replication_title,
                "replication_doi": replication_doi,
                "result_option_labels": clean(row.get("result_option_labels")),
                "current_root_pair_ids": clean(row.get("current_root_pair_ids")),
                "current_root_source_datasets": clean(row.get("current_root_source_datasets")),
                "value_scan_ids": clean(row.get("value_scan_ids")),
                "scan_decisions": clean(row.get("scan_decisions")),
                "dedupe_key_text": norm_text(" ".join([original_doi, replication_doi, original_title, replication_title, clean(row.get("candidate_name"))])),
                "source_object_urls_json": clean(row.get("source_object_urls_json")),
                "created_at": now,
            }
        )

    batch002_rows: list[dict[str, Any]] = []
    for row in dedupe_rows:
        status = clean(row["final_row_status"])
        if status in {"promoted_to_current_root_row", "already_in_current_root_table"}:
            action = "exclude_exact_pair_result_unless_new_outcome_or_new_source_family"
        elif status in {
            "held_not_row_source_blocked_or_manual_acquisition",
            "not_row_source_blocked_or_manual_acquisition",
        }:
            action = "do_not_repull_via_search_send_to_manual_acquisition_queue"
        elif status == "not_row_rejected_after_value_scan":
            action = "exclude_under_current_policy_unless_policy_changes"
        elif status == "not_row_unresolved_original_target":
            action = "exclude_until_query_resolves_specific_original_target"
        else:
            action = "exclude_context_or_seed_hit"
        batch002_rows.append(
            {
                f"{NEXT_BATCH_ID}_seed_id": stable_id(f"{NEXT_BATCH_ID}_seed", row["candidate_id"], action),
                "candidate_id": row["candidate_id"],
                f"{NEXT_BATCH_ID}_action": action,
                "dedupe_action": row["dedupe_action"],
                "final_row_status": status,
                "original_doi": row["original_doi"],
                "replication_doi": row["replication_doi"],
                "original_title": row["original_title"],
                "replication_title": row["replication_title"],
                "current_root_pair_ids": row["current_root_pair_ids"],
                "dedupe_key_text": row["dedupe_key_text"],
                "created_at": now,
            }
        )

    return (
        pd.DataFrame(manual_rows).fillna(""),
        pd.DataFrame(dedupe_rows).fillna(""),
        pd.DataFrame(batch002_rows).fillna(""),
    )


def write_report(manual: pd.DataFrame, dedupe: pd.DataFrame, batch002: pd.DataFrame) -> None:
    lines = [
        f"# Figure 1 Individual Replication {BATCH_ID} Closeout",
        "",
        f"{BATCH_ID} is closed for row-finding. Remaining work is either manual acquisition/source extraction or a future policy/native-route question.",
        "",
        "## Outputs",
        "",
        f"- Manual acquisition tasks: `{OUT_MANUAL.relative_to(ROOT)}` ({len(manual):,} rows)",
        f"- Dedupe baseline: `{OUT_DEDUPE.relative_to(ROOT)}` ({len(dedupe):,} rows)",
        f"- {NEXT_BATCH_ID} dedupe seed: `{OUT_BATCH002.relative_to(ROOT)}` ({len(batch002):,} rows)",
        "",
        "## Manual Acquisition Queue",
        "",
    ]
    if manual.empty:
        lines.append("- None.")
    else:
        for category, count in manual["blocker_category"].value_counts().sort_index().items():
            lines.append(f"- `{category}`: {count:,}")
        lines.extend(["", "### Tasks", ""])
        for row in manual.itertuples(index=False):
            lines.append(
                f"- `{row.candidate_id}` ({row.priority}, {row.blocker_category}): "
                f"{row.needed_evidence}"
            )
    lines.extend(["", "## Dedupe Status", ""])
    for status, count in dedupe["final_row_status"].value_counts().sort_index().items():
        lines.append(f"- `{status}`: {count:,}")
    lines.extend(["", f"## {NEXT_BATCH_ID} Use", ""])
    lines.append(
        f"Use `{OUT_BATCH002.name}` as an exclusion/manual-acquisition seed before screening new paper-level hits."
    )
    OUT_REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch-id", default="batch001")
    parser.add_argument("--replace", action="store_true", help="Accepted for Makefile consistency; outputs are regenerated.")
    args = parser.parse_args()
    configure_batch(args.batch_id)
    OUT_MANUAL.parent.mkdir(parents=True, exist_ok=True)
    OUT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    manual, dedupe, batch002 = build_artifacts()
    manual.to_csv(OUT_MANUAL, sep="\t", index=False)
    dedupe.to_csv(OUT_DEDUPE, sep="\t", index=False)
    batch002.to_csv(OUT_BATCH002, sep="\t", index=False)
    write_report(manual, dedupe, batch002)
    print(f"Wrote {OUT_MANUAL} ({len(manual)} manual acquisition tasks)")
    print(f"Wrote {OUT_DEDUPE} ({len(dedupe)} dedupe baseline rows)")
    print(f"Wrote {OUT_BATCH002} ({len(batch002)} {NEXT_BATCH_ID} seed rows)")


if __name__ == "__main__":
    main()
