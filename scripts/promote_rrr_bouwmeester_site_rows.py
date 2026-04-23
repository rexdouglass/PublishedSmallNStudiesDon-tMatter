#!/usr/bin/env python3
"""Promote site-level rows from the Bouwmeester 2017 RRR raw data bundle."""

from __future__ import annotations

import math
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = (
    ROOT
    / "data"
    / "raw"
    / "replication_projects"
    / "lead_harvest"
    / "rrr_bouwmeester_2017"
    / "unpacked_data"
    / "Data"
)
PROMOTED = ROOT / "data" / "derived" / "replication_pairs" / "harvest" / "promoted"
ALL_PAIRS = ROOT / "data" / "derived" / "replication_pairs" / "replication_pairs_all_on_hand.csv"


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def ascii_slug(text: str) -> str:
    norm = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    norm = norm.lower().replace("-", "_").replace(" ", "_")
    norm = "".join(ch if ch.isalnum() or ch == "_" else "_" for ch in norm)
    while "__" in norm:
        norm = norm.replace("__", "_")
    return norm.strip("_")


def pooled_d(tp: pd.Series, fd: pd.Series) -> tuple[float, int]:
    tp = pd.to_numeric(tp, errors="coerce").dropna().astype(float)
    fd = pd.to_numeric(fd, errors="coerce").dropna().astype(float)
    if len(tp) < 2 or len(fd) < 2:
        return np.nan, int(len(tp) + len(fd))
    s1 = tp.std(ddof=1)
    s2 = fd.std(ddof=1)
    pooled_var = ((len(tp) - 1) * s1**2 + (len(fd) - 1) * s2**2) / (len(tp) + len(fd) - 2)
    if not (np.isfinite(pooled_var) and pooled_var > 0):
        return np.nan, int(len(tp) + len(fd))
    return float(abs((tp.mean() - fd.mean()) / math.sqrt(pooled_var))), int(len(tp) + len(fd))


def conv(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce")


def load_original_anchor() -> dict[str, float]:
    df = pd.read_csv(ALL_PAIRS)
    row = df.loc[df["source_dataset"].eq("RRR Bouwmeester 2017 (manual)")].iloc[0]
    return {
        "D_original": float(row["D_original"]),
        "N_original": float(row["N_original"]),
    }


def build_rows() -> list[dict]:
    anchor = load_original_anchor()
    rows: list[dict] = []

    for path in sorted(RAW_DIR.glob("*_PAEX_Rand_Data.csv")):
        lab_name = path.name.replace("_PAEX_Rand_Data.csv", "")
        lab_slug = ascii_slug(lab_name)

        df = pd.read_csv(path, header=None, encoding="latin1")
        df.columns = df.iloc[0].astype(str)
        df = df.iloc[2:].reset_index(drop=True)

        tp18 = conv(df.iloc[:, 17])
        tp19 = conv(df.iloc[:, 18])
        fd24 = conv(df.iloc[:, 23])
        fd25 = conv(df.iloc[:, 24])
        keep = (tp18.isna() == tp19.isna()) & (fd24.isna() == fd25.isna())
        df = df.loc[keep].copy().reset_index(drop=True)

        year_born = conv(df.iloc[:, 84]) + 1919
        age = 2015 - year_born
        df = df.loc[(age >= 18) & (age <= 34)].copy().reset_index(drop=True)

        tp0 = conv(df.iloc[:, 17])
        fd0 = conv(df.iloc[:, 23])
        total = max(tp0.max(skipna=True), fd0.max(skipna=True))
        if not np.isfinite(total) or total <= 0:
            continue

        tp = tp0 / total * 100.0
        fd = fd0 / total * 100.0
        d_rep, n_rep = pooled_d(tp, fd)
        if not np.isfinite(d_rep) or n_rep <= 0:
            continue

        rows.append(
            {
                "source_dataset": "RRR Bouwmeester 2017 site csvs",
                "project": "Registered Replication Reports",
                "pair_id": f"rrr_bouwmeester_2017_{lab_slug}",
                "original_title": "Rand et al intuitive cooperation",
                "replication_title": f"Rand et al intuitive cooperation ({lab_name} lab)",
                "original_doi": "",
                "replication_doi": "",
                "outcome": "contribution_percent",
                "D_original": anchor["D_original"],
                "N_original": anchor["N_original"],
                "D_replication": d_rep,
                "N_replication": float(n_rep),
                "raw_file": str(path),
                "match_author": "rand_bouwmeester",
            }
        )

    return rows


def main() -> None:
    ensure_dir(PROMOTED)
    rows = build_rows()
    out_path = PROMOTED / "rrr_bouwmeester_site_rows__promoted_pairs.csv"
    pd.DataFrame(rows).to_csv(out_path, index=False)
    print(f"Wrote promoted rows: {len(rows)}")
    print(f"Wrote file: {out_path}")


if __name__ == "__main__":
    main()
