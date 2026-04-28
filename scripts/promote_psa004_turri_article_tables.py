#!/usr/bin/env python3
"""Promote one PSA 004 Turri row from article-reported table values.

The Stage-2 data payload remains unresolved locally, but Hall et al. (2024)
reports enough article-table information for a strict Darrel/Squirrel row:
Turri et al. Experiment 1 reports original OR = 2.00 with N = 98, and the
PSA replication Table 7 gives Darrel knowledge/gettier counts.

Odds ratios are mapped to a Cohen's-d-compatible axis with the Chinn
approximation, d = abs(log(OR)) * sqrt(3) / pi.
"""

from __future__ import annotations

import math
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw" / "replication_projects" / "lead_harvest" / "psa_004_turri"
PROMOTED_DIR = ROOT / "data" / "derived" / "replication_pairs" / "harvest" / "promoted"
SOURCE_TABLE = RAW_DIR / "psa004_turri_article_table_reconstruction.csv"
PROMOTED = PROMOTED_DIR / "psa004_turri_article_table_rescue__promoted_pairs.csv"

ORIGINAL_DOI = "10.1371/journal.pone.0121537"
REPLICATION_DOI = "10.1177/25152459241267902"


def odds_ratio_to_d(odds_ratio: float) -> float:
    return abs(math.log(float(odds_ratio))) * math.sqrt(3) / math.pi


def main() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    PROMOTED_DIR.mkdir(parents=True, exist_ok=True)

    original_or = 2.00
    original_n = 98

    replication_knows_knowledge = 1126
    replication_believes_knowledge = 454
    replication_knows_gettier = 923
    replication_believes_gettier = 615
    replication_n = (
        replication_knows_knowledge
        + replication_believes_knowledge
        + replication_knows_gettier
        + replication_believes_gettier
    )
    replication_or = (
        replication_knows_knowledge
        * replication_believes_gettier
        / (replication_believes_knowledge * replication_knows_gettier)
    )

    source = pd.DataFrame(
        [
            {
                "row_id": "psa_004_turri_darrel_direct",
                "original_source": "Turri et al. (2015) Experiment 1, Darrel/Squirrel knowledge versus Gettier",
                "original_n": original_n,
                "original_effect_metric": "OR",
                "original_or": original_or,
                "original_d_chinn": odds_ratio_to_d(original_or),
                "replication_source": "Hall et al. (2024) PSA 004 Table 7, Darrel vignette knowledge versus Gettier",
                "replication_knows_knowledge": replication_knows_knowledge,
                "replication_believes_knowledge": replication_believes_knowledge,
                "replication_knows_gettier": replication_knows_gettier,
                "replication_believes_gettier": replication_believes_gettier,
                "replication_n": replication_n,
                "replication_effect_metric": "OR reconstructed from 2x2 counts",
                "replication_or": replication_or,
                "replication_d_chinn": odds_ratio_to_d(replication_or),
                "conversion_note": "d = abs(log(OR)) * sqrt(3) / pi. This rescues one strict Darrel/Squirrel row from article tables; it does not recover the expected region-level rows.",
            }
        ]
    )
    source.to_csv(SOURCE_TABLE, index=False)

    promoted = pd.DataFrame(
        [
            {
                "source_dataset": "PSA 004 Turri article table rescue",
                "project": "PSA 004 JTB Turri",
                "pair_id": "psa_004_turri_darrel_direct",
                "original_title": "Turri et al. (2015) Experiment 1 Darrel/Squirrel knowledge attribution",
                "replication_title": "Hall et al. (2024) PSA 004 Darrel vignette replication",
                "original_doi": ORIGINAL_DOI,
                "replication_doi": REPLICATION_DOI,
                "outcome": "Darrel/Squirrel knowledge versus Gettier condition odds of knowledge attribution",
                "D_original": odds_ratio_to_d(original_or),
                "N_original": original_n,
                "D_replication": odds_ratio_to_d(replication_or),
                "N_replication": replication_n,
                "raw_file": str(SOURCE_TABLE),
                "match_author": "turri_2015_darrel_squirrel_knowledge_gettier",
            }
        ]
    )
    promoted.to_csv(PROMOTED, index=False)
    print(f"Wrote source reconstruction: {SOURCE_TABLE}")
    print(f"Wrote promoted rows: {PROMOTED}")


if __name__ == "__main__":
    main()
