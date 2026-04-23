#!/usr/bin/env python3
"""Promote directly recoverable Wood scaffolding replication rows."""

from __future__ import annotations

import math
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "replication_projects" / "lead_harvest" / "wood_scaffolding_2025"
PROMOTED = ROOT / "data" / "derived" / "replication_pairs" / "harvest" / "promoted"


def pooled_group_summary(groups: list[tuple[int, float, float]]) -> tuple[int, float, float]:
    total_n = sum(n for n, _, _ in groups)
    mean = sum(n * mu for n, mu, _ in groups) / total_n
    ss = sum((n - 1) * (sd**2) + n * ((mu - mean) ** 2) for n, mu, sd in groups)
    sd = math.sqrt(ss / (total_n - 1))
    return total_n, mean, sd


def pooled_d_from_summary(contingent: tuple[int, float, float], rest: tuple[int, float, float]) -> float:
    n1, m1, sd1 = contingent
    n2, m2, sd2 = rest
    pooled_var = (((n1 - 1) * sd1**2) + ((n2 - 1) * sd2**2)) / (n1 + n2 - 2)
    return abs((m1 - m2) / math.sqrt(pooled_var))


def pooled_d_from_raw(a: pd.Series, b: pd.Series) -> tuple[float, int]:
    a = pd.to_numeric(a, errors="coerce").dropna().astype(float)
    b = pd.to_numeric(b, errors="coerce").dropna().astype(float)
    pooled_var = (((len(a) - 1) * a.var(ddof=1)) + ((len(b) - 1) * b.var(ddof=1))) / (len(a) + len(b) - 2)
    return abs((a.mean() - b.mean()) / math.sqrt(pooled_var)), int(len(a) + len(b))


def build_rows() -> list[dict]:
    df = pd.read_csv(RAW / "osf_02__df_for_each_participant.csv")
    df["condition_name"] = df["condition"].map({1: "contingent", 2: "demonstration", 3: "swing", 4: "verbal"})

    # Original summaries are from the replication article's reconstructions of Wood et al. (1978).
    activity_original = {
        "contingent": (8, 37.50, 15.73),
        "demonstration": (8, 24.50, 14.12),
        "swing": (8, 20.88, 8.49),
        "verbal": (8, 20.88, 13.74),
    }
    outcome_original = {
        "contingent": (8, 15.00, 3.27),
        "demonstration": (8, 2.63, 5.45),
        "swing": (8, 4.00, 4.38),
        "verbal": (8, 6.25, 6.88),
    }

    rows: list[dict] = []
    specs = [
        (
            "wood_scaffolding_activity_contingent_vs_rest",
            "Activity score",
            "Child_operations",
            activity_original,
            "Child activity score: contingent tutoring vs pooled noncontingent conditions",
            "wood_scaffolding_activity",
        ),
        (
            "wood_scaffolding_outcome_contingent_vs_rest",
            "Outcome score",
            "coruna_opers",
            outcome_original,
            "Correct unaided operations: contingent tutoring vs pooled noncontingent conditions",
            "wood_scaffolding_outcome",
        ),
    ]

    for pair_id, original_title, column, original_summary, outcome, match_author in specs:
        orig_cont = original_summary["contingent"]
        orig_rest = pooled_group_summary(
            [
                original_summary["demonstration"],
                original_summary["swing"],
                original_summary["verbal"],
            ]
        )
        rep_cont = df.loc[df["condition_name"].eq("contingent"), column]
        rep_rest = df.loc[~df["condition_name"].eq("contingent"), column]
        d_rep, n_rep = pooled_d_from_raw(rep_cont, rep_rest)
        rows.append(
            {
                "source_dataset": "Wood scaffolding participant csv",
                "project": "Other direct replications",
                "pair_id": pair_id,
                "original_title": f"Wood et al. (1978) {original_title.lower()}",
                "replication_title": f"Wood scaffolding replication ({original_title.lower()})",
                "original_doi": "",
                "replication_doi": "",
                "outcome": outcome,
                "D_original": pooled_d_from_summary(orig_cont, orig_rest),
                "N_original": 32.0,
                "D_replication": d_rep,
                "N_replication": float(n_rep),
                "raw_file": str(RAW / "osf_02__df_for_each_participant.csv"),
                "match_author": match_author,
            }
        )
    return rows


def main() -> None:
    PROMOTED.mkdir(parents=True, exist_ok=True)
    out = pd.DataFrame(build_rows())
    out_path = PROMOTED / "wood_scaffolding__promoted_pairs.csv"
    out.to_csv(out_path, index=False)
    print(f"Wrote promoted rows: {len(out)}")
    print(f"Wrote file: {out_path}")


if __name__ == "__main__":
    main()
