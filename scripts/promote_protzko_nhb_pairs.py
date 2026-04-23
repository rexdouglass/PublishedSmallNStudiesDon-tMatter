#!/usr/bin/env python3
"""Promote directly recoverable Protzko et al. NHB replication rows."""

from __future__ import annotations

import math
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "replication_projects" / "lead_harvest" / "protzko_nhb_2023"
PROMOTED = ROOT / "data" / "derived" / "replication_pairs" / "harvest" / "promoted"


def t_to_d(t_value: float, df: float) -> float:
    r = math.sqrt((t_value * t_value) / (t_value * t_value + df))
    return abs((2.0 * r) / math.sqrt(max(1.0 - r * r, 1e-12)))


def z_to_d(z_value: float, n_value: float) -> float:
    r = abs(z_value) / math.sqrt(n_value)
    return abs((2.0 * r) / math.sqrt(max(1.0 - r * r, 1e-12)))


def build_rows() -> list[dict]:
    asymmetry_writeup = RAW / "asymmetry_writeup.docx"
    labels_writeup = RAW / "labels_writeup.docx"
    referrals_writeup = RAW / "referrals_writeup.docx"

    return [
        {
            "source_dataset": "Protzko NHB asymmetry writeup",
            "project": "Other direct replications",
            "pair_id": "protzko_asymmetry_without_cause_wave2",
            "original_title": "Asymmetry Without Cause (wave 1 original)",
            "replication_title": "Asymmetry Without Cause (wave 2 replication)",
            "original_doi": "",
            "replication_doi": "",
            "outcome": "Responsibility rating difference: mildly bad vs extremely good act",
            "D_original": 0.27,
            "N_original": 1261.0,
            "D_replication": 0.29,
            "N_replication": 1021.0,
            "raw_file": str(asymmetry_writeup),
            "match_author": "protzko_asymmetry_without_cause",
        },
        {
            "source_dataset": "Protzko NHB labels writeup",
            "project": "Other direct replications",
            "pair_id": "protzko_labels_wave2",
            "original_title": "Labels effect (wave 1 original)",
            "replication_title": "Labels effect (wave 2 replication)",
            "original_doi": "",
            "replication_doi": "",
            "outcome": "Belief that the researcher believes global warming is happening",
            "D_original": t_to_d(7.62, 1005.0),
            "N_original": 1024.0,
            "D_replication": t_to_d(6.38, 1066.0),
            "N_replication": 1086.0,
            "raw_file": str(labels_writeup),
            "match_author": "protzko_labels_climate_change_deniers",
        },
        {
            "source_dataset": "Protzko NHB referrals writeup",
            "project": "Other direct replications",
            "pair_id": "protzko_referrals_wave2",
            "original_title": "Referrals key test (wave 1 original)",
            "replication_title": "Referrals key test (wave 2 replication)",
            "original_doi": "",
            "replication_doi": "",
            "outcome": "Quality ratings: incentive effect among receivers (key test)",
            "D_original": z_to_d(3.15, 837.0),
            "N_original": 837.0,
            "D_replication": z_to_d(0.18, 755.0),
            "N_replication": 755.0,
            "raw_file": str(referrals_writeup),
            "match_author": "protzko_referrals_quality_receivers",
        },
    ]


def main() -> None:
    PROMOTED.mkdir(parents=True, exist_ok=True)
    out = pd.DataFrame(build_rows())
    out_path = PROMOTED / "protzko_nhb_pairs__promoted_pairs.csv"
    out.to_csv(out_path, index=False)
    print(f"Wrote promoted rows: {len(out)}")
    print(f"Wrote file: {out_path}")


if __name__ == "__main__":
    main()
