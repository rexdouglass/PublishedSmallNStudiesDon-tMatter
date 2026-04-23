#!/usr/bin/env python3
"""Promote locally harvested MSRP Schweitzer & Cachon rows."""

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
    / "msrp_public"
    / "SchweitzerCachon2000_ReplicationReport.pdf"
)


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def d_from_one_sample_t(t_value: float, n: float) -> float:
    return abs(float(t_value) / math.sqrt(float(n)))


def build_rows() -> list[dict]:
    original_n = 33.0
    replication_n = 40.0
    original_title = "Schweitzer & Cachon (2000) newsvendor pull-to-center"

    specs = [
        {
            "pair_id": "msrp_schweitzer_cachon_cornell_high_profit",
            "replication_title": "Schweitzer & Cachon MSRP Cornell high-profit",
            "outcome": "High-profit newsvendor order bias",
            "D_original": d_from_one_sample_t(6.58, original_n),
            "D_replication": d_from_one_sample_t(3.95, replication_n),
            "match_author": "schweitzer_cachon_high_profit",
        },
        {
            "pair_id": "msrp_schweitzer_cachon_cornell_low_profit",
            "replication_title": "Schweitzer & Cachon MSRP Cornell low-profit",
            "outcome": "Low-profit newsvendor order bias",
            "D_original": d_from_one_sample_t(12.15, original_n),
            "D_replication": d_from_one_sample_t(11.21, replication_n),
            "match_author": "schweitzer_cachon_low_profit",
        },
        {
            "pair_id": "msrp_schweitzer_cachon_utd_high_profit",
            "replication_title": "Schweitzer & Cachon MSRP UT Dallas high-profit",
            "outcome": "High-profit newsvendor order bias",
            "D_original": d_from_one_sample_t(6.58, original_n),
            "D_replication": d_from_one_sample_t(6.12, replication_n),
            "match_author": "schweitzer_cachon_high_profit",
        },
        {
            "pair_id": "msrp_schweitzer_cachon_utd_low_profit",
            "replication_title": "Schweitzer & Cachon MSRP UT Dallas low-profit",
            "outcome": "Low-profit newsvendor order bias",
            "D_original": d_from_one_sample_t(12.15, original_n),
            "D_replication": d_from_one_sample_t(14.54, replication_n),
            "match_author": "schweitzer_cachon_low_profit",
        },
    ]

    rows = []
    for spec in specs:
        rows.append(
            {
                "source_dataset": "MSRP Schweitzer & Cachon 2000 report",
                "project": "Management Science Replication Project",
                "pair_id": spec["pair_id"],
                "original_title": original_title,
                "replication_title": spec["replication_title"],
                "original_doi": "10.1287/mnsc.46.3.404.12070",
                "replication_doi": "10.1287/mnsc.2023.4866",
                "outcome": spec["outcome"],
                "D_original": spec["D_original"],
                "N_original": original_n,
                "D_replication": spec["D_replication"],
                "N_replication": replication_n,
                "raw_file": str(REPORT),
                "match_author": spec["match_author"],
            }
        )
    return rows


def main() -> None:
    ensure_dir(PROMOTED)
    out = pd.DataFrame(build_rows())
    out_path = PROMOTED / "msrp_schweitzer_cachon__promoted_pairs.csv"
    out.to_csv(out_path, index=False)
    print(f"Wrote promoted rows: {len(out)}")
    print(f"Wrote file: {out_path}")


if __name__ == "__main__":
    main()
