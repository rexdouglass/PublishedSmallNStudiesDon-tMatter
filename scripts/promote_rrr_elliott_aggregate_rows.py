#!/usr/bin/env python3
"""Promote aggregate Elliott et al. (2021) / Flavell et al. RRR rows.

The published RRR reports the same three age comparisons as Flavell et al.
(1966): 5 vs 7, 5 vs 10, and 7 vs 10 years old. The outcome is whether the
child ever showed speech behavior during the memory task, with "sometimes" and
"usually" counted as speech producers.

Replication counts are from Elliott et al. Table 2. Original proportions are
from the article's description of Flavell et al.'s Table 1: 5yo = 10%,
7yo = 60%, 10yo = 85%, with 20 children per original age group.
"""

from __future__ import annotations

import math
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUT = (
    ROOT
    / "data/derived/replication_pairs/harvest/promoted/"
    / "rrr_elliott_aggregate_rows__promoted_pairs.csv"
)


SCHEMA = [
    "source_dataset",
    "project",
    "pair_id",
    "original_title",
    "replication_title",
    "original_doi",
    "replication_doi",
    "outcome",
    "D_original",
    "N_original",
    "D_replication",
    "N_replication",
    "raw_file",
    "match_author",
]


def or_to_d(speaker_a: float, nonspeaker_a: float, speaker_b: float, nonspeaker_b: float) -> float:
    cells = [speaker_a, nonspeaker_a, speaker_b, nonspeaker_b]
    if any(c <= 0 for c in cells):
        speaker_a, nonspeaker_a, speaker_b, nonspeaker_b = [c + 0.5 for c in cells]
    odds_ratio = (speaker_b / nonspeaker_b) / (speaker_a / nonspeaker_a)
    return float(abs(math.log(odds_ratio)) * math.sqrt(3) / math.pi)


def main() -> None:
    original = {
        "5yo": (2, 18),
        "7yo": (12, 8),
        "10yo": (17, 3),
    }
    replication = {
        "5yo": (167, 53),
        "7yo": (250, 19),
        "10yo": (221, 14),
    }
    comparisons = [("5yo", "7yo"), ("5yo", "10yo"), ("7yo", "10yo")]

    rows = []
    for low, high in comparisons:
        os_low, on_low = original[low]
        os_high, on_high = original[high]
        rs_low, rn_low = replication[low]
        rs_high, rn_high = replication[high]
        rows.append(
            {
                "source_dataset": "RRR Elliott 2021 aggregate table rows",
                "project": "Registered Replication Reports",
                "pair_id": f"elliott_flavell_speech_{low}_vs_{high}",
                "original_title": "Flavell et al. (1966) spontaneous verbal rehearsal",
                "replication_title": "Elliott et al. (2021) Flavell RRR aggregate",
                "original_doi": "",
                "replication_doi": "10.1177/25152459211018187",
                "outcome": f"Any speech behavior: {low} vs {high}",
                "D_original": or_to_d(os_low, on_low, os_high, on_high),
                "N_original": os_low + on_low + os_high + on_high,
                "D_replication": or_to_d(rs_low, rn_low, rs_high, rn_high),
                "N_replication": rs_low + rn_low + rs_high + rn_high,
                "raw_file": str(
                    Path("data/raw/replication_projects/lead_harvest/rrr_elliott_2021/missing_labs")
                ),
                "match_author": f"flavell_spontaneous_verbal_rehearsal_{low}_{high}",
            }
        )

    OUT.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows, columns=SCHEMA).to_csv(OUT, index=False)
    print(f"wrote {len(rows)} rows to {OUT}")
    for row in rows:
        print(row["pair_id"], row["D_original"], row["D_replication"])


if __name__ == "__main__":
    main()
