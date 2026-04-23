#!/usr/bin/env python3
"""Promote the greed x SES interaction replications from the local OSF bundle."""

from __future__ import annotations

import math
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
PROMOTED = ROOT / "data" / "derived" / "replication_pairs" / "harvest" / "promoted"
SCRIPT = (
    ROOT
    / "data"
    / "raw"
    / "replication_projects"
    / "lead_harvest"
    / "greed_ses_2016"
    / "osf_06__Meta-analysis_and_forest_plot.R"
)


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def t_to_d(beta: float, se: float, n: float, predictors: int = 7) -> float:
    t_value = float(beta) / float(se)
    df = float(n) - predictors - 1.0
    if df <= 0:
        raise ValueError(f"Non-positive df for n={n}")
    r = math.sqrt((t_value * t_value) / (t_value * t_value + df))
    return abs((2.0 * r) / math.sqrt(1.0 - r * r))


def build_rows() -> list[dict]:
    original_beta = -0.238
    original_se = 0.102
    original_n = 90.0
    original_d = t_to_d(original_beta, original_se, original_n)

    reps = [
        ("rep1", "Greed x SES replication 1", 0.110, 0.066, 264.0),
        ("rep2", "Greed x SES replication 2", -0.060, 0.050, 257.0),
        ("rep3", "Greed x SES replication 3", 0.008, 0.056, 306.0),
        ("rep4", "Greed x SES replication 4", 0.095, 0.100, 114.0),
    ]

    rows = []
    for slug, title, beta, se, n_rep in reps:
        rows.append(
            {
                "source_dataset": "Greed x SES meta-analysis script",
                "project": "Other direct replications",
                "pair_id": f"greed_ses_{slug}",
                "original_title": "Piff et al. (2012) greed x SES interaction",
                "replication_title": title,
                "original_doi": "10.1073/pnas.1118373109",
                "replication_doi": "10.1038/sdata.2016.120",
                "outcome": "SES x greed prime interaction on unethical behavior",
                "D_original": original_d,
                "N_original": original_n,
                "D_replication": t_to_d(beta, se, n_rep),
                "N_replication": n_rep,
                "raw_file": str(SCRIPT),
                "match_author": "piff_greed_ses_interaction",
            }
        )
    return rows


def main() -> None:
    ensure_dir(PROMOTED)
    out = pd.DataFrame(build_rows())
    out_path = PROMOTED / "greed_ses_replications__promoted_pairs.csv"
    out.to_csv(out_path, index=False)
    print(f"Wrote promoted rows: {len(out)}")
    print(f"Wrote file: {out_path}")


if __name__ == "__main__":
    main()
