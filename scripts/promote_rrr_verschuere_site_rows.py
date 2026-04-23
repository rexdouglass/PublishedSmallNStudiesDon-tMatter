#!/usr/bin/env python3
"""Promote site-level rows from the Verschuere 2018 moral-reminders RRR."""

from __future__ import annotations

import math
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RAW_FILE = (
    ROOT
    / "data"
    / "raw"
    / "replication_projects"
    / "lead_harvest"
    / "rrr_verschuere_2018"
    / "vrrr_raw_data_corrected_MAA.csv"
)
PROMOTED = ROOT / "data" / "derived" / "replication_pairs" / "harvest" / "promoted"
ALL_PAIRS = ROOT / "data" / "derived" / "replication_pairs" / "replication_pairs_all_on_hand.csv"


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def ascii_slug(text: str) -> str:
    norm = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    norm = norm.lower().replace("-", "_").replace(" ", "_").replace("&", "and")
    norm = "".join(ch if ch.isalnum() or ch == "_" else "_" for ch in norm)
    while "__" in norm:
        norm = norm.replace("__", "_")
    return norm.strip("_")


def pooled_d(a: pd.Series, b: pd.Series) -> tuple[float, int]:
    a = pd.to_numeric(a, errors="coerce").dropna().astype(float)
    b = pd.to_numeric(b, errors="coerce").dropna().astype(float)
    if len(a) < 2 or len(b) < 2:
        return np.nan, int(len(a) + len(b))
    s1 = a.std(ddof=1)
    s2 = b.std(ddof=1)
    pooled_var = ((len(a) - 1) * s1**2 + (len(b) - 1) * s2**2) / (len(a) + len(b) - 2)
    if not (np.isfinite(pooled_var) and pooled_var > 0):
        return np.nan, int(len(a) + len(b))
    return float(abs((a.mean() - b.mean()) / math.sqrt(pooled_var))), int(len(a) + len(b))


def load_original_anchor() -> dict[str, float]:
    df = pd.read_csv(ALL_PAIRS)
    row = df.loc[df["source_dataset"].eq("RRR Verschuere 2018 (manual)")].iloc[0]
    return {
        "D_original": float(row["D_original"]),
        "N_original": float(row["N_original"]),
    }


def build_rows() -> list[dict]:
    anchor = load_original_anchor()
    df = pd.read_csv(RAW_FILE)
    df = df.loc[df["inclusion"].isin(["inclusion Mazar only", "inclusion both RRR"])].copy()
    excluded_labs = {"Acar", "Baskin", "Blatz", "Huntgens", "Pennington", "Roets", "Tran"}
    df = df.loc[~df["lab.name"].isin(excluded_labs)].copy()
    df["dv"] = np.where(
        df["maz.cheat.cond"].eq("cheat"),
        pd.to_numeric(df["num.boxes"], errors="coerce"),
        pd.to_numeric(df["num.boxes.correct"], errors="coerce"),
    )

    rows: list[dict] = []
    for lab_name, sub in df.groupby("lab.name"):
        d_rep, n_rep = pooled_d(
            sub.loc[sub["maz.prime.cond"].eq("commandments"), "dv"],
            sub.loc[sub["maz.prime.cond"].eq("books"), "dv"],
        )
        if not np.isfinite(d_rep) or n_rep <= 0:
            continue
        rows.append(
            {
                "source_dataset": "RRR Verschuere 2018 site csv",
                "project": "Registered Replication Reports",
                "pair_id": f"rrr_verschuere_2018_{ascii_slug(lab_name)}",
                "original_title": "Mazar/Amir/Ariely moral reminders",
                "replication_title": f"Mazar/Amir/Ariely moral reminders ({lab_name} lab)",
                "original_doi": "",
                "replication_doi": "",
                "outcome": "Mazar/Amir/Ariely moral reminders",
                "D_original": anchor["D_original"],
                "N_original": anchor["N_original"],
                "D_replication": d_rep,
                "N_replication": float(n_rep),
                "raw_file": str(RAW_FILE),
                "match_author": "Mazar/Amir/Ariely moral reminders",
            }
        )
    return rows


def main() -> None:
    ensure_dir(PROMOTED)
    rows = build_rows()
    out_path = PROMOTED / "rrr_verschuere_site_rows__promoted_pairs.csv"
    pd.DataFrame(rows).to_csv(out_path, index=False)
    print(f"Wrote promoted rows: {len(rows)}")
    print(f"Wrote file: {out_path}")


if __name__ == "__main__":
    main()
