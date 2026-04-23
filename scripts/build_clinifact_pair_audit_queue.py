#!/usr/bin/env python3
"""Build a manual-audit priority queue from the CliniFact pair table."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
IN_PATH = ROOT / "data" / "derived" / "publication_bias_direct" / "clinifact_publication_registry_pairs.csv"
OUT_DIR = ROOT / "data" / "derived" / "publication_bias_direct"


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def build_queue() -> tuple[pd.DataFrame, pd.DataFrame]:
    df = pd.read_csv(IN_PATH)
    df = df[df["pair_quality"].isin(["high", "medium"])].copy()
    df["abs_d_delta"] = df["journal_d_minus_registry_d"].abs()
    df["sig_discordant_05"] = df["sig_discordant_05"].fillna(False).astype(bool)
    df["sig_discordant_10"] = df["sig_discordant_10"].fillna(False).astype(bool)
    df["metric_family_match"] = df["metric_family_match"].fillna(False).astype(bool)

    reasons = []
    for _, row in df.iterrows():
        row_reasons = []
        if row["sig_discordant_05"]:
            row_reasons.append("sig_discordant_05")
        if row["sig_discordant_10"]:
            row_reasons.append("sig_discordant_10")
        if pd.notna(row["abs_d_delta"]) and row["abs_d_delta"] >= 0.25:
            row_reasons.append("large_d_gap")
        if (
            row["journal_effect_metric"] != ""
            and row["registry_metric_family"] != ""
            and not row["metric_family_match"]
        ):
            row_reasons.append("effect_family_mismatch")
        reasons.append(";".join(row_reasons))
    df["audit_reason"] = reasons

    quality_score = {"high": 2, "medium": 1}
    df["quality_score"] = df["pair_quality"].map(quality_score).fillna(0)
    df["priority_score"] = (
        3 * df["sig_discordant_05"].astype(int)
        + 1 * df["sig_discordant_10"].astype(int)
        + 2 * (df["abs_d_delta"] >= 0.25).astype(int)
        + 1 * (~df["metric_family_match"] & df["journal_effect_metric"].fillna("").ne("") & df["registry_metric_family"].fillna("").ne("")).astype(int)
        + df["quality_score"]
    )

    queue = df[
        (df["audit_reason"] != "")
        | (df["priority_score"] >= 3)
    ].copy()

    queue = queue.sort_values(
        ["priority_score", "quality_score", "sig_discordant_05", "abs_d_delta", "selected_sentence_score"],
        ascending=[False, False, False, False, False],
    )

    keep_cols = [
        "claim_id",
        "nctId",
        "PMID",
        "pair_quality",
        "priority_score",
        "audit_reason",
        "journal_p",
        "registry_p",
        "sig_discordant_05",
        "sig_discordant_10",
        "journal_d_proxy_preferred",
        "registry_d_proxy",
        "journal_d_minus_registry_d",
        "abs_d_delta",
        "journal_effect_metric",
        "registry_metric_family",
        "metric_family_match",
        "article_title",
        "selected_sentence",
        "clinifact_outcome_title",
        "registry_outcome_title",
    ]
    queue = queue[keep_cols].copy()
    top200 = queue.head(200).copy()
    return queue, top200


def write_summary(queue: pd.DataFrame, top200: pd.DataFrame) -> None:
    lines = [
        "# CliniFact Pair Audit Queue",
        "",
        "Last updated: 2026-04-20",
        "",
        "This queue prioritizes plausible publication-vs-registry pairs for manual",
        "audit. It is restricted to the `high` and `medium` pair-quality rows and",
        "prioritizes significance discordance, large D-proxy gaps, and metric-family",
        "mismatches.",
        "",
        "## Counts",
        "",
        f"- Full audit queue rows: {len(queue):,}",
        f"- Top-200 audit slice rows: {len(top200):,}",
        f"- Rows with `sig_discordant_05`: {int(queue['sig_discordant_05'].sum()):,}",
        f"- Rows with `abs_d_delta >= 0.25`: {int((queue['abs_d_delta'] >= 0.25).sum()):,}",
        "",
        "## Output Files",
        "",
        "- `data/derived/publication_bias_direct/clinifact_publication_registry_audit_queue.csv`",
        "- `data/derived/publication_bias_direct/clinifact_publication_registry_audit_top200.csv`",
        "- `data/derived/publication_bias_direct/clinifact_publication_registry_audit_summary.md`",
    ]
    (OUT_DIR / "clinifact_publication_registry_audit_summary.md").write_text("\n".join(lines) + "\n")


def main() -> None:
    ensure_dir(OUT_DIR)
    queue, top200 = build_queue()
    queue.to_csv(OUT_DIR / "clinifact_publication_registry_audit_queue.csv", index=False)
    top200.to_csv(OUT_DIR / "clinifact_publication_registry_audit_top200.csv", index=False)
    write_summary(queue, top200)
    print(f"Wrote {len(queue):,} audit rows and {len(top200):,} top-priority rows to {OUT_DIR}")


if __name__ == "__main__":
    main()
