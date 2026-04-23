#!/usr/bin/env python3
"""Promote the pooled Transparent Psi Project Bem replication row."""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "replication_projects" / "lead_harvest" / "tpp_bem" / "data"
PROMOTED = ROOT / "data" / "derived" / "replication_pairs" / "harvest" / "promoted"


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def participant_level_hit_d(df: pd.DataFrame) -> tuple[float, int]:
    by_participant = (
        df.groupby("participant_ID", dropna=False)["sides_match_bool"]
        .agg(["mean", "count"])
        .rename(columns={"mean": "hit_rate"})
    )
    by_participant = by_participant.loc[by_participant["count"] > 0].copy()
    if len(by_participant) < 2:
        return np.nan, 0
    hit_sd = by_participant["hit_rate"].std(ddof=1)
    if not (np.isfinite(hit_sd) and hit_sd > 0):
        return np.nan, 0
    d_value = abs((by_participant["hit_rate"].mean() - 0.5) / hit_sd)
    return float(d_value), int(len(by_participant))


def build_rows() -> list[dict]:
    raw = pd.read_csv(RAW / "tpp_combined_raw.csv")
    exclude_lab_ids = {
        "",
        "18155ef201564afbb81f6a8b74aa9a033eac51ec6595510eca9606938ffaced3",
        "ece83ceb8611d1926746e5bb3597ed1e8cb5d336521331b31961d5c0348883cf",
        "bd2dd15be34863e9efb77fbddfe744382a9c62c6a497e8bcf3097a47905b905b",
        "fff9cb9dcc3ac735fc25a59f424e98278a731c23ccd57276d292996c2ba7784f",
    }
    raw["laboratory_ID_code"] = raw["laboratory_ID_code"].fillna("")
    data = raw.loc[~raw["laboratory_ID_code"].isin(exclude_lab_ids)].copy()
    data["row_counter"] = np.arange(1, len(data) + 1)
    data = data.loc[data["trial_number"].notna()].copy()
    data = data.loc[data["reward_type"].eq("erotic")].copy()
    data = data.iloc[:37836].copy()  # preregistered first stopping point reached
    data["sides_match_bool"] = (
        data["sides_match"]
        .astype(str)
        .str.lower()
        .map({"true": True, "false": False, "1": True, "0": False})
    )

    d_rep, n_rep = participant_level_hit_d(data)
    if not np.isfinite(d_rep) or n_rep <= 0:
        return []

    return [
        {
            "source_dataset": "Transparent Psi Project combined raw",
            "project": "Other direct replications",
            "pair_id": "tpp_bem_erotic_hit_rate_first_stop",
            "original_title": "Bem (2011) experiment 1 erotic hit rate",
            "replication_title": "Transparent Psi Project pooled replication",
            "original_doi": "",
            "replication_doi": "",
            "outcome": "Erotic trial hit rate above chance",
            "D_original": 0.25,
            "N_original": 100.0,
            "D_replication": d_rep,
            "N_replication": float(n_rep),
            "raw_file": str(RAW / "tpp_combined_raw.csv"),
            "match_author": "bem_precognition_tpp",
        }
    ]


def main() -> None:
    ensure_dir(PROMOTED)
    out = pd.DataFrame(build_rows())
    out_path = PROMOTED / "tpp_bem__promoted_pairs.csv"
    out.to_csv(out_path, index=False)
    print(f"Wrote promoted rows: {len(out)}")
    print(f"Wrote file: {out_path}")


if __name__ == "__main__":
    main()
