#!/usr/bin/env python3
"""Promote paper-fallback Hedges-g rows from the ten-country eyewitness study.

The OSF payload remains unresolved locally, but the accepted manuscript's
forest plot reports original New Zealand N/g and country-level replication
N/g/CI values. Hedges' g is already on the D-compatible axis, so this promotes
the five countries whose analyzed replication N is larger than the original
N = 40. It intentionally does not also promote the aggregate row to avoid
nested/non-independent duplication.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = (
    ROOT
    / "data"
    / "raw"
    / "replication_projects"
    / "lead_harvest"
    / "eyewitness_ten_countries_2018"
)
PROMOTED_DIR = ROOT / "data" / "derived" / "replication_pairs" / "harvest" / "promoted"
SOURCE_TABLE = RAW_DIR / "eyewitness_ten_country_accepted_manuscript_figure3.csv"
PROMOTED = PROMOTED_DIR / "eyewitness_ten_country_paper_table_rescue__promoted_pairs.csv"

REPLICATION_DOI = "10.1016/j.jarmac.2018.09.004"


def main() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    PROMOTED_DIR.mkdir(parents=True, exist_ok=True)

    original_n = 40
    original_g = 1.46
    original_ci_low = 0.85
    original_ci_high = 2.07

    country_rows = [
        ("canada", "Canada", 41, 1.15, 0.59, 1.71),
        ("malaysia", "Malaysia", 51, 1.80, 1.25, 2.35),
        ("poland", "Poland", 55, 1.92, 1.28, 2.56),
        ("turkey", "Turkey", 49, 2.28, 1.66, 2.90),
        ("united_kingdom", "United Kingdom", 49, 1.75, 1.13, 2.38),
    ]

    source_rows = []
    promoted_rows = []
    for key, country, replication_n, replication_g, ci_low, ci_high in country_rows:
        source_rows.append(
            {
                "row_id": f"eyewitness_garry2008_{key}",
                "original_source": "Garry, French, Kinzett, and Mori (2008), New Zealand original",
                "original_n": original_n,
                "original_hedges_g": original_g,
                "original_ci_low": original_ci_low,
                "original_ci_high": original_ci_high,
                "replication_country": country,
                "replication_n": replication_n,
                "replication_hedges_g": replication_g,
                "replication_ci_low": ci_low,
                "replication_ci_high": ci_high,
                "gate_note": "Promoted because the country analyzed N is greater than the original N=40. Hedges' g is already D-compatible.",
            }
        )
        promoted_rows.append(
            {
                "source_dataset": "Eyewitness ten-country paper table rescue",
                "project": "Eyewitness memory distortion in ten countries",
                "pair_id": f"eyewitness_garry2008_{key}",
                "original_title": "Garry et al. (2008) co-witness memory distortion original New Zealand study",
                "replication_title": f"Ito et al. (2018) co-witness memory distortion replication ({country})",
                "original_doi": "",
                "replication_doi": REPLICATION_DOI,
                "outcome": f"Discussed versus non-discussed correct-response Hedges' g ({country})",
                "D_original": original_g,
                "N_original": original_n,
                "D_replication": replication_g,
                "N_replication": replication_n,
                "raw_file": str(SOURCE_TABLE),
                "match_author": "garry_2008_cowitness_memory_distortion",
            }
        )

    pd.DataFrame(source_rows).to_csv(SOURCE_TABLE, index=False)
    pd.DataFrame(promoted_rows).to_csv(PROMOTED, index=False)
    print(f"Wrote source reconstruction: {SOURCE_TABLE}")
    print(f"Wrote promoted rows: {PROMOTED}")


if __name__ == "__main__":
    main()
