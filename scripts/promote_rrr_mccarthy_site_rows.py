#!/usr/bin/env python3
"""Promote site-level rows from the McCarthy 2018 Srull-Wyer RRR bundle."""

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
    / "rrr_mccarthy_2018"
    / "unpacked_data"
    / "SW_Script_and_Data"
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


def conv(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce")


def pooled_d(m1: float, s1: float, n1: int, m2: float, s2: float, n2: int) -> float:
    pooled_var = ((n1 - 1) * s1**2 + (n2 - 1) * s2**2) / (n1 + n2 - 2)
    if not (np.isfinite(pooled_var) and pooled_var > 0):
        return np.nan
    return float(abs((m1 - m2) / math.sqrt(pooled_var)))


def load_original_anchor() -> dict[str, float]:
    df = pd.read_csv(ALL_PAIRS)
    row = df.loc[df["source_dataset"].eq("Srull-Wyer RRR paper (manual)")].iloc[0]
    return {
        "D_original": float(row["D_original"]),
        "N_original": float(row["N_original"]),
    }


def harmonize_lab_name(name: str) -> str:
    out = str(name)
    if out == "Nahari":
        out = "klein Selle & Rozmann"
    if out == "klein Selle":
        out = "klein Selle & Rozmann"
    if out == "LoschelderMechtel":
        out = "Loschelder"
    if out == "Voracek":
        out = "Tran"
    out = out.replace("\\", "")
    return out.upper()


def derive_outcomes(df: pd.DataFrame) -> pd.DataFrame:
    for col in [c for c in df.columns if c.startswith("ron") or c.startswith("behavior") or c == "age"]:
        df[col] = conv(df[col])

    df["ron.kindR"] = 10 - df["ron.kind"]
    df["ron.considerateR"] = 10 - df["ron.considerate"]
    df["ron.thoughtfulR"] = 10 - df["ron.thoughtful"]

    trait_cols = [
        "ron.hostile",
        "ron.unfriendly",
        "ron.dislikable",
        "ron.kindR",
        "ron.considerateR",
        "ron.thoughtfulR",
    ]
    behavior_cols = ["behavior2", "behavior5", "behavior8", "behavior10", "behavior13"]

    df["trait_missing"] = df[trait_cols].isna().sum(axis=1)
    df["behavior_missing"] = df[behavior_cols].isna().sum(axis=1)
    df["hostility"] = np.where(df["trait_missing"] > 0, np.nan, df[trait_cols].mean(axis=1))
    df["ambiguous_behaviors"] = np.where(
        df["behavior_missing"] > 0,
        np.nan,
        df[behavior_cols].mean(axis=1),
    )
    return df


def final_sample(df: pd.DataFrame, outcome_kind: str) -> pd.DataFrame:
    base_keep = (
        df["sw.prime.complete"].eq("complete")
        & df["inclusion"].isin(["inclusion Srull only", "inclusion both RRR"])
    )
    if outcome_kind == "trait_ratings":
        keep = base_keep & df["trait_missing"].eq(0)
    else:
        keep = base_keep & df["behavior_missing"].eq(0)
    return df.loc[keep].copy()


def summarize_by_condition(df: pd.DataFrame, outcome_col: str) -> tuple[float, int] | None:
    grouped = df.groupby("sw.prime.cond")[outcome_col].agg(["count", "mean", "std"])
    if "hostile" not in grouped.index or "neutral" not in grouped.index:
        return None

    n1, m1, s1 = grouped.loc["hostile", ["count", "mean", "std"]]
    n2, m2, s2 = grouped.loc["neutral", ["count", "mean", "std"]]
    if n1 < 100 or n2 < 100:
        return None
    if not all(np.isfinite(x) for x in [m1, s1, m2, s2]):
        return None

    d_rep = pooled_d(float(m1), float(s1), int(n1), float(m2), float(s2), int(n2))
    if not np.isfinite(d_rep):
        return None
    return float(d_rep), int(n1 + n2)


def build_rows() -> list[dict]:
    anchor = load_original_anchor()
    rows: list[dict] = []

    for path in sorted(RAW_DIR.glob("*_Final.csv")):
        df = pd.read_csv(path, dtype=str, encoding="latin1")
        if "lab.name" not in df.columns:
            continue

        df["lab.name"] = df["lab.name"].map(harmonize_lab_name)
        df = derive_outcomes(df)

        trait_df = final_sample(df, "trait_ratings")
        behavior_df = final_sample(df, "behavior_ratings")

        lab_name = (
            trait_df["lab.name"].dropna().iloc[0]
            if not trait_df["lab.name"].dropna().empty
            else harmonize_lab_name(path.stem.replace("_Final", ""))
        )
        lab_slug = ascii_slug(lab_name)

        for outcome_key, outcome_col, outcome_label, match_author in [
            ("trait_ratings", "hostility", "trait_ratings", "srull_wyer_trait_ratings"),
            ("behavior_ratings", "ambiguous_behaviors", "behavior_ratings", "srull_wyer_behavior_ratings"),
        ]:
            sample = trait_df if outcome_key == "trait_ratings" else behavior_df
            summary = summarize_by_condition(sample, outcome_col)
            if summary is None:
                continue
            d_rep, n_rep = summary
            rows.append(
                {
                    "source_dataset": "RRR McCarthy 2018 site csvs",
                    "project": "Registered Replication Reports",
                    "pair_id": f"rrr_mccarthy_2018_{lab_slug}_{outcome_key}",
                    "original_title": "Srull & Wyer hostility priming",
                    "replication_title": f"Srull & Wyer hostility priming ({lab_name} lab)",
                    "original_doi": "",
                    "replication_doi": "",
                    "outcome": outcome_label,
                    "D_original": anchor["D_original"],
                    "N_original": anchor["N_original"],
                    "D_replication": d_rep,
                    "N_replication": float(n_rep),
                    "raw_file": str(path),
                    "match_author": match_author,
                }
            )

    return rows


def main() -> None:
    ensure_dir(PROMOTED)
    rows = build_rows()
    out_path = PROMOTED / "rrr_mccarthy_site_rows__promoted_pairs.csv"
    pd.DataFrame(rows).to_csv(out_path, index=False)
    print(f"Wrote promoted rows: {len(rows)}")
    print(f"Wrote file: {out_path}")


if __name__ == "__main__":
    main()
