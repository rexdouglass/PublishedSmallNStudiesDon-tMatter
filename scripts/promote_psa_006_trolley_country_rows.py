#!/usr/bin/env python3
"""Promote country-level direct-replication rows from PSA-006 trolley data."""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pandas as pd
import pyreadr
import statsmodels.api as sm
from statsmodels.formula.api import ols


ROOT = Path(__file__).resolve().parents[1]
PROMOTED = ROOT / "data" / "derived" / "replication_pairs" / "harvest" / "promoted"
RAW_RDA = (
    ROOT
    / "data"
    / "raw"
    / "replication_projects"
    / "lead_harvest"
    / "psa_006_trolley"
    / "unzipped"
    / "trolleyMultilabReplication-master"
    / "data"
    / "trolley.rda"
)


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def pooled_d(a: pd.Series, b: pd.Series) -> float:
    a = pd.to_numeric(a, errors="coerce").dropna().astype(float)
    b = pd.to_numeric(b, errors="coerce").dropna().astype(float)
    if len(a) < 2 or len(b) < 2:
        return np.nan
    sd1 = a.std(ddof=1)
    sd2 = b.std(ddof=1)
    pooled_var = ((len(a) - 1) * sd1**2 + (len(b) - 1) * sd2**2) / (len(a) + len(b) - 2)
    if not (np.isfinite(pooled_var) and pooled_var > 0):
        return np.nan
    return float(abs((a.mean() - b.mean()) / math.sqrt(pooled_var)))


def eta2_to_d(eta2: float) -> float:
    if not (np.isfinite(eta2) and 0 <= eta2 < 1):
        return np.nan
    r = math.sqrt(eta2)
    denom = max(1 - r * r, 1e-12)
    return float(abs((2 * r) / math.sqrt(denom)))


def load_trolley() -> pd.DataFrame:
    return pyreadr.read_r(RAW_RDA)["trolley"]


def build_study1_rows(df: pd.DataFrame, study: str) -> list[dict]:
    if study == "study1a":
        mask_col = "include_study1a"
        cols = ("trolley_1_rate", "trolley_2_rate")
        original_title = "Greene et al. (2009) trolley personal-force effect"
        outcome_template = "Trolley personal-force effect ({country})"
        d_original = 0.40
        n_original = 232.0
        match_author = "greene_2009_trolley_personal_force"
    elif study == "study1b":
        mask_col = "include_study1b"
        cols = ("speedboat_1_rate", "speedboat_2_rate")
        original_title = "Greene et al. (2009) speedboat personal-force effect"
        outcome_template = "Speedboat personal-force effect ({country})"
        d_original = 0.69
        n_original = 91.0
        match_author = "greene_2009_speedboat_personal_force"
    else:
        raise ValueError(study)

    sub = df.loc[df[mask_col].fillna(False).astype(bool)].copy()
    rows: list[dict] = []
    for country, grp in sub.groupby("country3", dropna=True):
        d_rep = pooled_d(grp[cols[0]], grp[cols[1]])
        if not np.isfinite(d_rep):
            continue
        rows.append(
            {
                "source_dataset": "PSA-006 trolley country rows",
                "project": "Other direct replications",
                "pair_id": f"psa006_{study}_{country.lower()}",
                "original_title": original_title,
                "replication_title": "Bago et al. (2022) PSA-006 trolley country replication",
                "original_doi": "10.1016/j.cognition.2009.02.001",
                "replication_doi": "10.1038/s41562-022-01319-5",
                "outcome": outcome_template.format(country=country),
                "D_original": d_original,
                "N_original": n_original,
                "D_replication": d_rep,
                "N_replication": float(len(grp)),
                "raw_file": str(RAW_RDA),
                "match_author": match_author,
            }
        )
    return rows


def build_study2a_rows(df: pd.DataFrame) -> list[dict]:
    sub = df.loc[df["include_study2a"].fillna(False).astype(bool)].copy()
    rows: list[dict] = []
    for country, grp in sub.groupby("country3", dropna=True):
        long_parts = []
        for cond, col in [("3", "trolley_3_rate"), ("4", "trolley_4_rate"), ("5", "trolley_5_rate"), ("6", "trolley_6_rate")]:
            tmp = grp[[col]].copy()
            tmp = tmp.rename(columns={col: "rate"})
            tmp["condition"] = cond
            long_parts.append(tmp)
        long_df = pd.concat(long_parts, ignore_index=True)
        long_df["rate"] = pd.to_numeric(long_df["rate"], errors="coerce")
        long_df = long_df.dropna(subset=["rate"]).copy()
        long_df["personal_force"] = long_df["condition"].isin(["4", "6"]).astype(int)
        long_df["intention"] = long_df["condition"].isin(["4", "5"]).astype(int)
        if long_df.groupby(["personal_force", "intention"]).size().shape[0] < 4:
            continue

        try:
            model = ols("rate ~ C(personal_force) * C(intention)", data=long_df).fit()
            anova = sm.stats.anova_lm(model, typ=2)
            ss_interaction = float(anova.loc["C(personal_force):C(intention)", "sum_sq"])
            ss_resid = float(anova.loc["Residual", "sum_sq"])
            eta2 = ss_interaction / (ss_interaction + ss_resid)
            d_rep = eta2_to_d(eta2)
        except Exception:
            continue

        if not np.isfinite(d_rep):
            continue

        rows.append(
            {
                "source_dataset": "PSA-006 trolley country rows",
                "project": "Other direct replications",
                "pair_id": f"psa006_study2a_{country.lower()}",
                "original_title": "Greene et al. (2009) trolley intention × personal-force interaction",
                "replication_title": "Bago et al. (2022) PSA-006 trolley country replication",
                "original_doi": "10.1016/j.cognition.2009.02.001",
                "replication_doi": "10.1038/s41562-022-01319-5",
                "outcome": f"Trolley intention × personal-force interaction ({country})",
                "D_original": eta2_to_d(0.02),
                "N_original": 366.0,
                "D_replication": d_rep,
                "N_replication": float(len(grp)),
                "raw_file": str(RAW_RDA),
                "match_author": "greene_2009_trolley_interaction",
            }
        )
    return rows


def main() -> None:
    ensure_dir(PROMOTED)
    df = load_trolley()
    rows: list[dict] = []
    rows.extend(build_study1_rows(df, "study1a"))
    rows.extend(build_study1_rows(df, "study1b"))
    rows.extend(build_study2a_rows(df))
    out = pd.DataFrame(rows)
    out_path = PROMOTED / "psa_006_trolley_country_rows__promoted_pairs.csv"
    out.to_csv(out_path, index=False)
    print(f"Wrote promoted rows: {len(out)}")
    print(f"Wrote file: {out_path}")


if __name__ == "__main__":
    main()
