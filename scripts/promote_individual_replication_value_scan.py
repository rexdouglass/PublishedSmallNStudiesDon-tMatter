#!/usr/bin/env python3
"""Promote ready individual-replication value-scan rows into harvested pairs.

This script is intentionally conservative. It promotes only value-scan rows
whose scan decision is `ready_for_source_result_build`; everything requiring
policy, exact-N reconciliation, or outcome multiplicity review remains in the
scan/proposal TSVs. The promoted CSV uses the existing generic harvested-pair
contract consumed by `scripts/analyze_replication_pairs.py`.
"""

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
WORKLIST = WORKLIST_DIR / "individual-paper-worklist-from-search.tsv"
INTAKE_ALL = WORKLIST_DIR / "individual-paper-search-intake-all.tsv"
INTAKE_GLOBS = [
    "individual-paper-search-triage-batch*.tsv",
]
OUT_PROMOTED = (
    ROOT
    / "data"
    / "derived"
    / "replication_pairs"
    / "harvest"
    / "promoted"
    / "individual_replication_papers__promoted_pairs.csv"
)
OUT_PROPOSAL = WORKLIST_DIR / "individual-paper-promotion-proposal.tsv"
OUT_REPORT = ROOT / "reports" / "figure1_individual_replication_ready_promotion_2026-05-05.md"


PROMOTED_COLUMNS = [
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
    "match_author",
]

PROPOSAL_COLUMNS = [
    "promotion_id",
    "value_scan_id",
    "candidate_id",
    "scan_decision",
    "promotion_decision",
    "pair_id",
    "original_title",
    "original_doi",
    "replication_title",
    "replication_doi",
    "outcome",
    "D_original",
    "N_original",
    "D_replication",
    "N_replication",
    "local_support_paths",
    "original_support_text",
    "replication_support_text",
    "conversion_or_policy_note",
    "next_action",
]


def clean(value: Any) -> str:
    if value is None:
        return ""
    return str(value).replace("\t", " ").replace("\n", " ").replace("\r", " ").strip()


def slugify(text: str, max_len: int = 96) -> str:
    text = clean(text).lower()
    text = re.sub(r"[^a-z0-9]+", "_", text).strip("_")
    return text[:max_len].strip("_") or "row"


def stable_id(prefix: str, *parts: Any) -> str:
    payload = "||".join(clean(part) for part in parts)
    return f"{prefix}_{hashlib.sha1(payload.encode('utf-8')).hexdigest()[:16]}"


def first_number(value: Any) -> str:
    text = clean(value)
    match = re.search(r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?", text)
    return match.group(0) if match else ""


def source_path_field(value: Any) -> str:
    paths: list[str] = []
    for part in re.split(r"\s+\|\s+|;", clean(value)):
        path = part.strip()
        if path and path not in paths:
            paths.append(path)
    return " ; ".join(paths)


def read_tsv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path, sep="\t", dtype=str, keep_default_na=False).fillna("")


def build_promotions() -> tuple[pd.DataFrame, pd.DataFrame]:
    scan = read_tsv(VALUE_SCAN)
    worklist = read_tsv(WORKLIST)
    intake = read_tsv(INTAKE_ALL)
    intake_frames = [intake, worklist]
    for pattern in INTAKE_GLOBS:
        for path in sorted(WORKLIST_DIR.glob(pattern)):
            intake_frames.append(read_tsv(path))
    if scan.empty:
        raise FileNotFoundError(f"No value-scan rows found at {VALUE_SCAN}")
    if all(frame.empty for frame in intake_frames):
        raise FileNotFoundError(f"No individual-paper candidate metadata found at {WORKLIST_DIR}")

    meta_frame = pd.concat([frame for frame in intake_frames if not frame.empty], ignore_index=True, sort=False).fillna("")
    meta = meta_frame.drop_duplicates("candidate_id", keep="last").set_index("candidate_id", drop=False).to_dict(orient="index")
    proposals: list[dict[str, Any]] = []
    promoted: list[dict[str, Any]] = []

    for _, row in scan.iterrows():
        candidate_id = clean(row.get("candidate_id"))
        candidate = meta.get(candidate_id, {})
        decision = clean(row.get("scan_decision"))
        d_original = first_number(row.get("original_effect_value"))
        d_replication = first_number(row.get("replication_effect_value"))
        n_original = first_number(row.get("original_n_for_effect"))
        n_replication = first_number(row.get("replication_n_for_effect"))
        outcome = clean(row.get("result_option_label"))
        pair_id = f"individual_{slugify(candidate_id, 48)}_{slugify(outcome, 48)}"
        promotion_decision = "promote_to_harvested_pair_contract"
        next_action = "run_analyze_replication_pairs_then_downstream_figure1_rebuild"
        if decision != "ready_for_source_result_build":
            promotion_decision = "hold_for_policy_or_value_reconciliation"
            next_action = clean(row.get("next_action"))
        elif not all([d_original, d_replication, n_original, n_replication]):
            promotion_decision = "hold_missing_numeric_promoted_field"
            next_action = "repair_value_scan_numeric_fields_before_promotion"

        proposal = {
            "promotion_id": stable_id("individual_promotion", row.get("value_scan_id"), candidate_id, outcome),
            "value_scan_id": clean(row.get("value_scan_id")),
            "candidate_id": candidate_id,
            "scan_decision": decision,
            "promotion_decision": promotion_decision,
            "pair_id": pair_id,
            "original_title": clean(row.get("original_title_override")) or clean(candidate.get("original_title")),
            "original_doi": clean(row.get("original_doi_override")) or clean(candidate.get("original_doi")),
            "replication_title": clean(row.get("replication_title_override")) or clean(candidate.get("replication_title")),
            "replication_doi": clean(row.get("replication_doi_override")) or clean(candidate.get("replication_doi")),
            "outcome": outcome,
            "D_original": d_original,
            "N_original": n_original,
            "D_replication": d_replication,
            "N_replication": n_replication,
            "local_support_paths": clean(row.get("local_support_paths")),
            "original_support_text": clean(row.get("original_support_text")),
            "replication_support_text": clean(row.get("replication_support_text")),
            "conversion_or_policy_note": clean(row.get("conversion_or_policy_note")),
            "next_action": next_action,
        }
        proposals.append(proposal)

        if promotion_decision != "promote_to_harvested_pair_contract":
            continue
        promoted.append(
            {
                "source_dataset": "Individual replication paper value scan",
                "project": "Other direct replications",
                "pair_id": pair_id,
                "original_title": proposal["original_title"],
                "replication_title": proposal["replication_title"],
                "original_doi": proposal["original_doi"],
                "replication_doi": proposal["replication_doi"],
                "outcome": outcome,
                "D_original": d_original,
                "N_original": n_original,
                "D_replication": d_replication,
                "N_replication": n_replication,
                "raw_file": source_path_field(proposal["local_support_paths"]),
                "match_author": candidate_id,
            }
        )

    return (
        pd.DataFrame(promoted, columns=PROMOTED_COLUMNS).fillna(""),
        pd.DataFrame(proposals, columns=PROPOSAL_COLUMNS).fillna(""),
    )


def write_report(promoted: pd.DataFrame, proposals: pd.DataFrame) -> None:
    held = proposals[proposals["promotion_decision"].ne("promote_to_harvested_pair_contract")]
    lines = [
        "# Figure 1 Individual Replication Ready Promotion",
        "",
        "This step promotes only individual-replication value-scan rows marked `ready_for_source_result_build`.",
        "It does not resolve rows needing exact N, paired-effect conversion policy, or outcome multiplicity decisions.",
        "",
        "## Summary",
        "",
        f"- Promoted rows: {len(promoted):,}",
        f"- Held rows: {len(held):,}",
        "",
        "## Promoted",
        "",
    ]
    if promoted.empty:
        lines.append("- None.")
    else:
        for row in promoted.itertuples(index=False):
            lines.append(
                f"- `{row.pair_id}`: {row.original_title} -> {row.replication_title}; "
                f"{row.outcome}; D {row.D_original} -> {row.D_replication}; "
                f"N {row.N_original} -> {row.N_replication}."
            )
    lines.extend(["", "## Held", ""])
    if held.empty:
        lines.append("- None.")
    else:
        for row in held.itertuples(index=False):
            lines.append(f"- `{row.candidate_id}` / {row.outcome}: {row.promotion_decision}; next: {row.next_action}.")
    lines.extend(
        [
            "",
            "## Artifacts",
            "",
            f"- `{OUT_PROMOTED.relative_to(ROOT)}`",
            f"- `{OUT_PROPOSAL.relative_to(ROOT)}`",
        ]
    )
    OUT_REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--replace", action="store_true", help="Accepted for Makefile consistency; outputs are regenerated.")
    parser.parse_args()
    OUT_PROMOTED.parent.mkdir(parents=True, exist_ok=True)
    OUT_PROPOSAL.parent.mkdir(parents=True, exist_ok=True)
    OUT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    promoted, proposals = build_promotions()
    promoted.to_csv(OUT_PROMOTED, index=False)
    proposals.to_csv(OUT_PROPOSAL, sep="\t", index=False)
    write_report(promoted, proposals)
    print(f"Wrote {OUT_PROMOTED} ({len(promoted)} promoted rows)")
    print(f"Wrote {OUT_PROPOSAL} ({len(proposals)} proposal rows)")


if __name__ == "__main__":
    main()
