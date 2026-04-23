#!/usr/bin/env python3
"""Promote direct-replication claim rows from the online-image credibility bundle."""

from __future__ import annotations

import math
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
PROMOTED = ROOT / "data" / "derived" / "replication_pairs" / "harvest" / "promoted"


def f_to_r(f_value: float, df1: int, df2: int) -> float:
    num = f_value * (df1 / df2)
    den = ((f_value * df1) / df2) + 1
    return math.sqrt(num / den) * math.sqrt(1 / df1)


def r_to_d_abs(r_value: float) -> float:
    denom = max(1 - r_value * r_value, 1e-12)
    return abs((2 * r_value) / math.sqrt(denom))


def build_rows() -> list[dict]:
    claims = [
        ("H1", 1.64, 1, 3449, 3476, 0.1166333, 1, 629, 629),
        ("H2a_b", 1.75, 2, 3449, 3476, 0.7159753, 2, 629, 629),
        ("H3", 0.97, 2, 3449, 3476, 0.7912164, 2, 629, 629),
        ("H4", 0.04, 1, 3449, 3476, 2.1428978, 1, 629, 629),
        ("H5a", 12.38, 1, 3449, 3476, 9.5589533, 1, 629, 629),
        ("H5b", 6.79, 1, 3449, 3476, 8.8237975, 1, 629, 629),
        ("H6a", 0.86, 1, 1535, 1535, 8.6894516, 1, 282, 282),
        ("H6b", 5.98, 1, 999, 999, 11.7490880, 1, 226, 226),
        ("H7_1", 9.00, 1, 3449, 3476, 2.0760706, 1, 629, 629),
        ("H7_2", 10.94, 1, 1701, 1713, 5.8794645, 1, 308, 308),
        ("H7_3", 8.74, 1, 1535, 1535, 4.9123399, 1, 282, 282),
    ]

    rows = []
    for claim, f_orig, df1_orig, df2_orig, n_orig, f_rep, df1_rep, df2_rep, n_rep in claims:
        rows.append(
            {
                "source_dataset": "Online image credibility README equivalence table",
                "project": "Other direct replications",
                "pair_id": f"online_image_credibility_direct_{claim.lower()}",
                "original_title": f"Shen et al. (2019) {claim}",
                "replication_title": f"Online image credibility direct replication {claim}",
                "original_doi": "",
                "replication_doi": "",
                "outcome": f"Claim {claim}",
                "D_original": r_to_d_abs(f_to_r(f_orig, df1_orig, df2_orig)),
                "N_original": n_orig,
                "D_replication": r_to_d_abs(f_to_r(f_rep, df1_rep, df2_rep)),
                "N_replication": n_rep,
                "raw_file": str(
                    ROOT
                    / "data"
                    / "raw"
                    / "replication_projects"
                    / "lead_harvest"
                    / "online_image_credibility"
                    / "osf_04__README.Rmd"
                ),
                "match_author": "shen_online_image_credibility",
            }
        )
    return rows


def main() -> None:
    PROMOTED.mkdir(parents=True, exist_ok=True)
    out_path = PROMOTED / "online_image_credibility__promoted_pairs.csv"
    pd.DataFrame(build_rows()).to_csv(out_path, index=False)
    print(f"Wrote promoted rows: {len(build_rows())}")
    print(f"Wrote file: {out_path}")


if __name__ == "__main__":
    main()
