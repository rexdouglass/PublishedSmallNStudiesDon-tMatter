#!/usr/bin/env python3
"""Promote paper-table contrasts from Walker et al. public-admin blame replication.

The source article and online supplement report the original James et al. (2016)
regression table and the England, Hong Kong, and South Korea replication tables.
No raw respondent file is public locally, so this is a paper-table reconstruction.
Effects are converted from reported treatment-contrast t statistics using the
balanced two-arm contrast formula d = |t| * sqrt(1 / n1 + 1 / n2).
"""

from __future__ import annotations

import math
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw" / "replication_projects" / "lead_harvest" / "public_admin_blame"
PROMOTED_DIR = ROOT / "data" / "derived" / "replication_pairs" / "harvest" / "promoted"
SOURCE_TABLE = RAW_DIR / "wiley_public_admin_blame_table_reconstruction.csv"
PROMOTED = PROMOTED_DIR / "public_admin_blame_wiley_table_reconstruction__promoted_pairs.csv"

ORIGINAL_DOI = "10.1111/puar.12471"
REPLICATION_DOI = "10.1111/puar.13845"


def d_from_t(t_stat: float, n_per_arm: int) -> float:
    return abs(float(t_stat)) * math.sqrt((1 / n_per_arm) + (1 / n_per_arm))


def main() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    PROMOTED_DIR.mkdir(parents=True, exist_ok=True)

    contrasts = [
        {
            "contrast_id": "politicians_manage_vs_no_information",
            "outcome": "Politicians manage delivery cue versus no information cue; citizens' blame of local politicians",
            "original_model": "James et al. (2016) Table 1 Model 1",
            "original_t": 2.78,
            "original_coef": 5.16,
            "replication_models": {
                "england": ("Walker et al. (2024) Table 2 Model 1", 3.29, 4.87),
                "hong_kong": ("Walker et al. (2024) Table 2 Model 5", 1.78, 2.57),
                "south_korea": ("Walker et al. (2024) Table 2 Model 9", 1.45, 2.25),
            },
        },
        {
            "contrast_id": "delegation_within_government_vs_politicians_manage",
            "outcome": "Delegated unit within local government cue versus politicians manage delivery cue; citizens' blame of local politicians",
            "original_model": "James et al. (2016) Table 1 Model 3",
            "original_t": -2.25,
            "original_coef": -4.16,
            "replication_models": {
                "england": ("Walker et al. (2024) Table 2 Model 3", -3.14, -4.65),
                "hong_kong": ("Walker et al. (2024) Table 2 Model 7", -2.27, -3.28),
                "south_korea": ("Walker et al. (2024) Table 2 Model 11", -0.41, -0.64),
            },
        },
        {
            "contrast_id": "contract_private_company_vs_politicians_manage",
            "outcome": "Contract with private company cue versus politicians manage delivery cue; citizens' blame of local politicians",
            "original_model": "James et al. (2016) Table 1 Model 3",
            "original_t": -1.46,
            "original_coef": -2.70,
            "replication_models": {
                "england": ("Walker et al. (2024) Table 2 Model 3", -4.49, -6.65),
                "hong_kong": ("Walker et al. (2024) Table 2 Model 7", -3.28, -4.73),
                "south_korea": ("Walker et al. (2024) Table 2 Model 11", -2.80, -4.36),
            },
        },
    ]

    original_per_arm = 250
    replication_per_arm = 300
    original_contrast_n = original_per_arm * 2
    replication_contrast_n = replication_per_arm * 2

    source_rows: list[dict[str, object]] = []
    promoted_rows: list[dict[str, object]] = []
    country_labels = {
        "england": "England",
        "hong_kong": "Hong Kong",
        "south_korea": "South Korea",
    }

    for contrast in contrasts:
        d_original = d_from_t(float(contrast["original_t"]), original_per_arm)
        for country_key, (rep_model, rep_t, rep_coef) in contrast["replication_models"].items():
            d_replication = d_from_t(float(rep_t), replication_per_arm)
            source_rows.append(
                {
                    "contrast_id": contrast["contrast_id"],
                    "replication_context": country_labels[country_key],
                    "original_model": contrast["original_model"],
                    "replication_model": rep_model,
                    "original_coef": contrast["original_coef"],
                    "original_t": contrast["original_t"],
                    "original_n_per_arm": original_per_arm,
                    "original_contrast_n": original_contrast_n,
                    "original_d_from_t": d_original,
                    "replication_coef": rep_coef,
                    "replication_t": rep_t,
                    "replication_n_per_arm": replication_per_arm,
                    "replication_contrast_n": replication_contrast_n,
                    "replication_d_from_t": d_replication,
                    "conversion_note": "d = abs(t) * sqrt(1/n1 + 1/n2), using balanced focal contrast arms from the article and supplement tables.",
                }
            )
            promoted_rows.append(
                {
                    "source_dataset": "Public-admin blame Wiley table reconstruction",
                    "project": "Other direct replications",
                    "pair_id": f"public_admin_blame_{contrast['contrast_id']}_{country_key}",
                    "original_title": "James et al. (2016) citizens' blame of politicians experiment",
                    "replication_title": f"Walker et al. (2024) public-admin blame replication ({country_labels[country_key]})",
                    "original_doi": ORIGINAL_DOI,
                    "replication_doi": REPLICATION_DOI,
                    "outcome": f"{contrast['outcome']} ({country_labels[country_key]})",
                    "D_original": d_original,
                    "N_original": original_contrast_n,
                    "D_replication": d_replication,
                    "N_replication": replication_contrast_n,
                    "raw_file": str(SOURCE_TABLE),
                    "match_author": f"james_2016_public_admin_blame_{contrast['contrast_id']}",
                }
            )

    pd.DataFrame(source_rows).to_csv(SOURCE_TABLE, index=False)
    pd.DataFrame(promoted_rows).to_csv(PROMOTED, index=False)
    print(f"Wrote source reconstruction: {SOURCE_TABLE}")
    print(f"Wrote promoted rows: {PROMOTED}")


if __name__ == "__main__":
    main()
