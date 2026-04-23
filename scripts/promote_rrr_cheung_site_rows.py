#!/usr/bin/env python3
"""Promote site-level rows from the Cheung 2016 RRR raw data bundle."""

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
    / "rrr_cheung_2016"
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


def conv(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce")


def pooled_d(a: pd.Series, b: pd.Series) -> tuple[float, int]:
    a = conv(a).dropna().astype(float)
    b = conv(b).dropna().astype(float)
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
    row = df.loc[df["source_dataset"].eq("RRR Cheung 2016 (manual)")].iloc[0]
    return {
        "D_original": float(row["D_original"]),
        "N_original": float(row["N_original"]),
    }


def score_mean(df: pd.DataFrame, cols: list[str]) -> pd.Series:
    return df[cols].apply(pd.to_numeric, errors="coerce").mean(axis=1)


def compute_overall(df: pd.DataFrame) -> pd.Series:
    exit_ = score_mean(df, ["Q2.2_1", "Q2.3_3", "Q2.4_1", "Q2.5_2", "Q2.6_2", "Q2.7_4", "Q2.8_2", "Q2.9_4", "Q2.10_1", "Q2.11_4", "Q2.12_3", "Q2.13_4"])
    neglect = score_mean(df, ["Q2.2_4", "Q2.3_2", "Q2.4_2", "Q2.5_4", "Q2.6_1", "Q2.7_2", "Q2.8_4", "Q2.9_2", "Q2.10_4", "Q2.11_1", "Q2.12_1", "Q2.13_1"])
    voice = score_mean(df, ["Q2.2_2", "Q2.3_10", "Q2.4_3", "Q2.5_1", "Q2.6_4", "Q2.7_1", "Q2.8_3", "Q2.9_3", "Q2.10_2", "Q2.11_2", "Q2.12_4", "Q2.13_3"])
    loyalty = score_mean(df, ["Q2.2_3", "Q2.3_1", "Q2.4_4", "Q2.5_3", "Q2.6_3", "Q2.7_3", "Q2.8_1", "Q2.9_1", "Q2.10_3", "Q2.11_3", "Q2.12_2", "Q2.13_2"])
    return pd.concat([8 - exit_, 8 - neglect, voice, loyalty], axis=1).mean(axis=1)


def build_rows() -> list[dict]:
    anchor = load_original_anchor()
    rows: list[dict] = []

    for path in sorted(RAW_DIR.glob("*.csv")):
        lab_name = path.stem.replace("_Data", "").replace("_data", "")
        lab_slug = ascii_slug(lab_name)

        df = pd.read_csv(path, header=None, encoding="latin1")
        df.columns = df.iloc[0].astype(str)
        df = df.iloc[2:].reset_index(drop=True)

        exclude = conv(df["Exclude"])
        condition = conv(df["Q7.1"])
        df = df.loc[exclude.isin([0, 1, 2]) & condition.isin([1, 2])].copy()
        if df.empty:
            continue

        df["Condition"] = condition.loc[df.index].map({1.0: "H", 2.0: "L"})
        overall = compute_overall(df)
        d_rep, n_rep = pooled_d(overall.loc[df["Condition"].eq("H")], overall.loc[df["Condition"].eq("L")])
        if not np.isfinite(d_rep) or n_rep <= 0:
            continue

        rows.append(
            {
                "source_dataset": "RRR Cheung 2016 site csvs",
                "project": "Registered Replication Reports",
                "pair_id": f"rrr_cheung_2016_{lab_slug}",
                "original_title": "Finkel commitment/forgiveness",
                "replication_title": f"Finkel commitment/forgiveness ({lab_name} lab)",
                "original_doi": "",
                "replication_doi": "",
                "outcome": "overall_forgiveness",
                "D_original": anchor["D_original"],
                "N_original": anchor["N_original"],
                "D_replication": d_rep,
                "N_replication": float(n_rep),
                "raw_file": str(path),
                "match_author": "finkel_commitment_forgiveness",
            }
        )

    return rows


def main() -> None:
    ensure_dir(PROMOTED)
    rows = build_rows()
    out_path = PROMOTED / "rrr_cheung_site_rows__promoted_pairs.csv"
    pd.DataFrame(rows).to_csv(out_path, index=False)
    print(f"Wrote promoted rows: {len(rows)}")
    print(f"Wrote file: {out_path}")


if __name__ == "__main__":
    main()
