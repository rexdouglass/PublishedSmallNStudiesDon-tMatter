#!/usr/bin/env python3
"""Promote conservative EQIPD Stage 1 -> Stage 2 lab-level pair rows.

This keeps the extraction narrow and within the current project policy:
- same outcome: open-field total distance travelled (log cm)
- same contrast: MK-801 0.2 mg/kg versus saline
- same lab on both sides
- Stage 1 treated as the baseline/original leg and Stage 2 variants as the
  replication legs
"""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "replication_projects" / "lead_harvest" / "eqipd_2022"
PROMOTED = ROOT / "data" / "derived" / "replication_pairs" / "harvest" / "promoted"
OUT = PROMOTED / "eqipd_stage2_lab_rows__promoted_pairs.csv"

STAGE_FILES = {
    "stage1": RAW / "osf_05__Stage_1_data.csv",
    "localization2": RAW / "osf_01__Stage_2_local_protocol_data.csv",
    "harmonized": RAW / "osf_02__Stage_2_harmonized_cohort_data.csv",
    "heterogenized": RAW / "osf_03__Stage_2_heterogenized_cohort_data.csv",
}

REPLICATION_DOI = "10.1371/journal.pbio.3001886"
OUTCOME_LABEL = "Open-field total distance travelled (log cm), MK-801 0.2 mg/kg vs saline"


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def pooled_d(df: pd.DataFrame) -> tuple[float, int] | tuple[float, int, float, float]:
    treated = df.loc[df["DrugDose"].eq("MK-801-0.2mg/kg"), "logOutc_value"].astype(float)
    control = df.loc[df["DrugDose"].eq("Saline"), "logOutc_value"].astype(float)
    n1 = len(treated)
    n2 = len(control)
    if n1 < 2 or n2 < 2:
        return np.nan, 0
    sd1 = treated.std(ddof=1)
    sd2 = control.std(ddof=1)
    pooled_den = n1 + n2 - 2
    if pooled_den <= 0:
        return np.nan, 0
    pooled_var = ((n1 - 1) * sd1**2 + (n2 - 1) * sd2**2) / pooled_den
    if not (np.isfinite(pooled_var) and pooled_var > 0):
        return np.nan, 0
    d_value = abs((treated.mean() - control.mean()) / math.sqrt(pooled_var))
    return float(d_value), int(n1 + n2)


def load_stage(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    df = df.loc[df["Outc_varname"].astype(str).str.contains("distance", case=False, na=False)].copy()
    df["ContributorID"] = df["ContributorID"].astype(str).str.strip()
    df["DrugDose"] = df["DrugDose"].astype(str).str.strip()
    df["logOutc_value"] = pd.to_numeric(df["logOutc_value"], errors="coerce")
    return df.loc[df["logOutc_value"].notna()].copy()


def stage_display_name(stage_key: str) -> str:
    return {
        "localization2": "Stage 2 localization",
        "harmonized": "Stage 2 harmonized cohort",
        "heterogenized": "Stage 2 heterogenized cohort",
    }[stage_key]


def slugify_lab(lab: str) -> str:
    return lab.lower().replace(" ", "_").replace("-", "_")


def build_rows() -> list[dict]:
    stage1 = load_stage(STAGE_FILES["stage1"])
    baseline: dict[str, tuple[float, int]] = {}
    for lab, grp in stage1.groupby("ContributorID", dropna=True):
        d_value, n_value = pooled_d(grp)
        if np.isfinite(d_value) and n_value > 0:
            baseline[lab] = (float(d_value), int(n_value))

    rows: list[dict] = []
    for stage_key in ("localization2", "harmonized", "heterogenized"):
        stage_df = load_stage(STAGE_FILES[stage_key])
        for lab, grp in stage_df.groupby("ContributorID", dropna=True):
            if lab not in baseline:
                continue
            d_replication, n_replication = pooled_d(grp)
            if not (np.isfinite(d_replication) and n_replication > 0):
                continue
            d_original, n_original = baseline[lab]
            rows.append(
                {
                    "source_dataset": "EQIPD stagewise open-field lab contrasts",
                    "project": "Other direct replications",
                    "pair_id": f"eqipd_{stage_key}_{slugify_lab(lab)}",
                    "original_title": f"EQIPD Stage 1 localization baseline ({lab})",
                    "replication_title": f"EQIPD {stage_display_name(stage_key)} ({lab})",
                    "original_doi": "",
                    "replication_doi": REPLICATION_DOI,
                    "outcome": OUTCOME_LABEL,
                    "D_original": d_original,
                    "N_original": float(n_original),
                    "D_replication": float(d_replication),
                    "N_replication": float(n_replication),
                    "raw_file": str(STAGE_FILES[stage_key]),
                    "match_author": f"eqipd_{slugify_lab(lab)}",
                }
            )
    return rows


def main() -> None:
    ensure_dir(PROMOTED)
    out = pd.DataFrame(build_rows())
    out.to_csv(OUT, index=False)
    print(f"Wrote promoted rows: {len(out)}")
    print(f"Wrote file: {OUT}")


if __name__ == "__main__":
    main()
