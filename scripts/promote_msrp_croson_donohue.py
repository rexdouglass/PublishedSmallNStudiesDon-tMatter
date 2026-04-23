#!/usr/bin/env python3
"""Promote Croson and Donohue 2006 MSRP site rows from the report table."""

from __future__ import annotations

import math
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
PROMOTED = ROOT / "data" / "derived" / "replication_pairs" / "harvest" / "promoted"
REPORT = (
    ROOT
    / "data"
    / "raw"
    / "replication_projects"
    / "lead_harvest"
    / "msrp_om_2023"
    / "msrp_public_extra"
    / "CrosonDonohue2006_ReplicationReport.pdf"
)


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def pooled_d(m1: float, s1: float, n1: int, m2: float, s2: float, n2: int) -> float:
    pooled_var = ((n1 - 1) * s1**2 + (n2 - 1) * s2**2) / (n1 + n2 - 2)
    return abs((m1 - m2) / math.sqrt(pooled_var))


def build_rows() -> list[dict]:
    original_title = "Croson and Donohue (2006) bullwhip effect inventory information"
    original_d = pooled_d(32.59, 35.21, 44, 21.67, 23.04, 44)

    specs = [
        {
            "pair_id": "msrp_croson_donohue_utd_hyp3",
            "replication_title": "Croson and Donohue MSRP UT Dallas",
            "D_replication": pooled_d(8434.06, 27620.0, 124, 4346.71, 21671.0, 136),
            "N_replication": 260.0,
        },
        {
            "pair_id": "msrp_croson_donohue_uw_hyp3",
            "replication_title": "Croson and Donohue MSRP UW-Madison",
            "D_replication": pooled_d(1147.99, 6609.0, 112, 4646.85, 22490.0, 112),
            "N_replication": 224.0,
        },
    ]

    rows = []
    for spec in specs:
        rows.append(
            {
                "source_dataset": "MSRP Croson and Donohue 2006 report",
                "project": "Management Science Replication Project",
                "pair_id": spec["pair_id"],
                "original_title": original_title,
                "replication_title": spec["replication_title"],
                "original_doi": "",
                "replication_doi": "10.1287/mnsc.2023.4866",
                "outcome": "order_variance_hypothesis_3",
                "D_original": original_d,
                "N_original": 88.0,
                "D_replication": spec["D_replication"],
                "N_replication": spec["N_replication"],
                "raw_file": str(REPORT),
                "match_author": "croson_donohue_hyp3",
            }
        )
    return rows


def main() -> None:
    ensure_dir(PROMOTED)
    out = pd.DataFrame(build_rows())
    out_path = PROMOTED / "msrp_croson_donohue__promoted_pairs.csv"
    out.to_csv(out_path, index=False)
    print(f"Wrote promoted rows: {len(out)}")
    print(f"Wrote file: {out_path}")


if __name__ == "__main__":
    main()
