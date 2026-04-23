#!/usr/bin/env python3
"""Promote the retrieval-extinction rat direct replications from local XLSX files."""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
HARVEST = ROOT / "data" / "raw" / "replication_projects" / "lead_harvest" / "retrieval_extinction_rats_2017"
PROMOTED = ROOT / "data" / "derived" / "replication_pairs" / "harvest" / "promoted"


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def pooled_d(a: pd.Series, b: pd.Series) -> tuple[float, int]:
    a = pd.to_numeric(a, errors="coerce").dropna().astype(float)
    b = pd.to_numeric(b, errors="coerce").dropna().astype(float)
    if len(a) < 2 or len(b) < 2:
        return np.nan, int(len(a) + len(b))
    sd1 = a.std(ddof=1)
    sd2 = b.std(ddof=1)
    pooled_var = ((len(a) - 1) * sd1**2 + (len(b) - 1) * sd2**2) / (len(a) + len(b) - 2)
    if not (np.isfinite(pooled_var) and pooled_var > 0):
        return np.nan, int(len(a) + len(b))
    return float(abs((a.mean() - b.mean()) / math.sqrt(pooled_var))), int(len(a) + len(b))


def load_average_observer_block(path: Path) -> pd.DataFrame:
    x = pd.read_excel(path, sheet_name="Manual %freezing", header=None)
    col0 = x.iloc[:, 0].apply(lambda v: "" if pd.isna(v) else str(v))
    start = col0.index[col0.str.contains("Average of two observers", regex=False)][0]
    out = x.iloc[start + 2 :].copy()
    out.columns = x.iloc[start + 1]
    out = out.loc[out["Group"].astype(str).isin(["Ret", "NoRet"])].copy()
    return out.reset_index(drop=True)


def build_rows() -> list[dict]:
    specs = [
        {
            "pair_id": "retrieval_extinction_spontaneous_recovery",
            "original_title": "Monfils et al. (2009) spontaneous recovery",
            "replication_title": "Luyten & Beckers spontaneous recovery replication",
            "outcome": "Spontaneous recovery freezing (4 CSs)",
            "D_original": 1.895,
            "N_original": 16.0,
            "raw_file": HARVEST / "osf_03__LLERC02_-_Spontaneous_Recovery_-_Full_data_set.xlsx",
            "outcome_col": "Spont Rec 4 CSs (%)",
            "match_author": "monfils_spontaneous_recovery",
        },
        {
            "pair_id": "retrieval_extinction_reinstatement",
            "original_title": "Monfils et al. (2009) reinstatement",
            "replication_title": "Luyten & Beckers reinstatement replication",
            "outcome": "Reinstatement freezing (4 CSs)",
            "D_original": 1.104,
            "N_original": 24.0,
            "raw_file": HARVEST / "osf_04__LLERC03_-_Reinstatement_-_Full_data_set.xlsx",
            "outcome_col": "Reinst Test Avg 4 CSs (%)",
            "match_author": "monfils_reinstatement",
        },
        {
            "pair_id": "retrieval_extinction_renewal",
            "original_title": "Monfils et al. (2009) renewal",
            "replication_title": "Luyten & Beckers renewal replication",
            "outcome": "Renewal freezing (4 CSs)",
            "D_original": 1.738,
            "N_original": 16.0,
            "raw_file": HARVEST / "osf_02__LLERC04_-_Renewal_-_Full_data_set.xlsx",
            "outcome_col": "Renewal 4 CSs (%)",
            "match_author": "monfils_renewal",
        },
    ]

    rows: list[dict] = []
    for spec in specs:
        dat = load_average_observer_block(spec["raw_file"])
        d_rep, n_rep = pooled_d(
            dat.loc[dat["Group"].eq("Ret"), spec["outcome_col"]],
            dat.loc[dat["Group"].eq("NoRet"), spec["outcome_col"]],
        )
        if not np.isfinite(d_rep) or n_rep <= 0:
            continue
        rows.append(
            {
                "source_dataset": "Retrieval-extinction rats xlsx",
                "project": "Other direct replications",
                "pair_id": spec["pair_id"],
                "original_title": spec["original_title"],
                "replication_title": spec["replication_title"],
                "original_doi": "",
                "replication_doi": "",
                "outcome": spec["outcome"],
                "D_original": spec["D_original"],
                "N_original": spec["N_original"],
                "D_replication": d_rep,
                "N_replication": float(n_rep),
                "raw_file": str(spec["raw_file"]),
                "match_author": spec["match_author"],
            }
        )
    return rows


def main() -> None:
    ensure_dir(PROMOTED)
    out = pd.DataFrame(build_rows())
    out_path = PROMOTED / "retrieval_extinction_rats__promoted_pairs.csv"
    out.to_csv(out_path, index=False)
    print(f"Wrote promoted rows: {len(out)}")
    print(f"Wrote file: {out_path}")


if __name__ == "__main__":
    main()
