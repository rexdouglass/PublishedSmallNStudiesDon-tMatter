#!/usr/bin/env python3
"""Promote a conservative subset of awesome-replicability-data paired CSVs.

This script only handles leads where the cleaned paired files expose:
- one clear binary condition column
- one clear numeric outcome column
- one original sample and one or more replication samples

The goal is to add a small but defensible batch of new direct-replication rows
without broadening the project's current effect-conversion policy.
"""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
HARVEST = ROOT / "data" / "raw" / "replication_projects" / "lead_harvest"
PROMOTED = ROOT / "data" / "derived" / "replication_pairs" / "harvest" / "promoted"


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def pooled_d_from_groups(df: pd.DataFrame, group_col: str, outcome_col: str, treat_vals: set, control_vals: set) -> tuple[float, int]:
    dat = df[[group_col, outcome_col]].copy()
    dat[outcome_col] = pd.to_numeric(dat[outcome_col], errors="coerce")
    dat = dat.dropna()
    treated = dat.loc[dat[group_col].isin(treat_vals), outcome_col].astype(float)
    control = dat.loc[dat[group_col].isin(control_vals), outcome_col].astype(float)
    if len(treated) < 2 or len(control) < 2:
        return np.nan, 0
    n1 = len(treated)
    n2 = len(control)
    sd1 = treated.std(ddof=1)
    sd2 = control.std(ddof=1)
    pooled_den = n1 + n2 - 2
    if pooled_den <= 0:
        return np.nan, 0
    pooled_var = ((n1 - 1) * sd1**2 + (n2 - 1) * sd2**2) / pooled_den
    if not (np.isfinite(pooled_var) and pooled_var > 0):
        return np.nan, 0
    d = abs((treated.mean() - control.mean()) / math.sqrt(pooled_var))
    return float(d), int(n1 + n2)


def paired_d_from_condition_means(
    df: pd.DataFrame,
    id_col: str,
    condition_col: str,
    outcome_col: str,
    treat_val: float = 1,
    control_val: float = 0,
) -> tuple[float, int]:
    dat = df[[id_col, condition_col, outcome_col]].copy()
    dat[outcome_col] = pd.to_numeric(dat[outcome_col], errors="coerce")
    dat[condition_col] = pd.to_numeric(dat[condition_col], errors="coerce")
    dat = dat.dropna()
    if dat.empty:
        return np.nan, 0

    pivot = (
        dat.groupby([id_col, condition_col])[outcome_col]
        .mean()
        .unstack()
    )
    if treat_val not in pivot.columns or control_val not in pivot.columns:
        return np.nan, 0

    diff = (pivot[treat_val] - pivot[control_val]).dropna().astype(float)
    if len(diff) < 2:
        return np.nan, int(len(diff))
    sd = diff.std(ddof=1)
    if not (np.isfinite(sd) and sd > 0):
        return np.nan, int(len(diff))
    return float(abs(diff.mean() / sd)), int(len(diff))


def read_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path)


def first_present_column(df: pd.DataFrame, *candidates: str) -> str:
    for name in candidates:
        if name in df.columns:
            return name
    raise KeyError(f"None of the candidate columns are present: {candidates}")


def repair_rotated_key_columns(df: pd.DataFrame, time_col: str) -> pd.DataFrame:
    fixed = df.copy()
    old_condition = fixed["condition"].copy()
    old_participant = fixed["participant_id"].copy()
    old_time = fixed[time_col].copy()
    fixed["condition"] = old_time
    fixed["participant_id"] = old_condition
    fixed[time_col] = old_participant
    return fixed


def build_rows() -> list[dict]:
    rows: list[dict] = []

    # EMDR and misinformation
    base = HARVEST / "awesome_emdr_misinfo"
    orig = read_csv(base / "github_01__original_clean.csv")
    rep = read_csv(base / "github_02__replication_clean.csv")
    for outcome_col, outcome_label in [
        ("totalmisinfo", "Total misinformation recalled"),
        ("totalcorrect", "Total correct answers"),
    ]:
        d_orig, n_orig = pooled_d_from_groups(orig, "condition", outcome_col, {1}, {0})
        d_rep, n_rep = pooled_d_from_groups(rep, "condition", outcome_col, {1}, {0})
        rows.append(
            {
                "source_dataset": "Awesome replicability paired raw csvs",
                "project": "Other direct replications",
                "pair_id": f"awesome_emdr_misinfo_{outcome_col}",
                "original_title": "Houben et al. EMDR misinformation (original)",
                "replication_title": "Calvillo et al. EMDR misinformation (replication)",
                "original_doi": "",
                "replication_doi": "",
                "outcome": outcome_label,
                "D_original": d_orig,
                "N_original": n_orig,
                "D_replication": d_rep,
                "N_replication": n_rep,
                "raw_file": str(base / "github_02__replication_clean.csv"),
                "match_author": "houben",
            }
        )

    # Cleanliness and moral judgment: two experiments
    base = HARVEST / "awesome_cleanliness_moral"
    for exp_num, orig_name, rep_name in [
        ("exp1", "github_01__original_exp1_clean.csv", "github_04__replication_exp1_clean.csv"),
        ("exp2", "github_02__original_exp2_clean.csv", "github_03__replication_exp2_clean.csv"),
    ]:
        orig = read_csv(base / orig_name)
        rep = read_csv(base / rep_name)
        outcome_col_orig = first_present_column(orig, "vignettes", "vignette")
        outcome_col_rep = first_present_column(rep, "vignettes", "vignette")
        d_orig, n_orig = pooled_d_from_groups(orig, "condition", outcome_col_orig, {1}, {0})
        d_rep, n_rep = pooled_d_from_groups(rep, "condition", outcome_col_rep, {1}, {0})
        rows.append(
            {
                "source_dataset": "Awesome replicability paired raw csvs",
                "project": "Other direct replications",
                "pair_id": f"awesome_cleanliness_moral_{exp_num}_vignettes",
                "original_title": f"Cleanliness and moral judgment ({exp_num}, original)",
                "replication_title": f"Cleanliness and moral judgment ({exp_num}, replication)",
                "original_doi": "",
                "replication_doi": "",
                "outcome": outcome_col_rep,
                "D_original": d_orig,
                "N_original": n_orig,
                "D_replication": d_rep,
                "N_replication": n_rep,
                "raw_file": str(base / rep_name),
                "match_author": "cleanliness_moral",
            }
        )

    # Pain and cooperation: two replications against one original
    base = HARVEST / "awesome_pain_coop"
    orig = read_csv(base / "github_01__original_clean.csv")
    d_orig, n_orig = pooled_d_from_groups(orig, "condition", "cooperation", {1}, {0})
    for rep_num, rep_name in [
        ("pilot", "github_02__replication1_clean.csv"),
        ("registered", "github_03__replication2_clean.csv"),
    ]:
        rep = read_csv(base / rep_name)
        d_rep, n_rep = pooled_d_from_groups(rep, "condition", "cooperation", {1}, {0})
        rows.append(
            {
                "source_dataset": "Awesome replicability paired raw csvs",
                "project": "Other direct replications",
                "pair_id": f"awesome_pain_coop_{rep_num}_cooperation",
                "original_title": "Shared pain and cooperation (original)",
                "replication_title": f"Shared pain and cooperation ({rep_num} replication)",
                "original_doi": "",
                "replication_doi": "",
                "outcome": "cooperation",
                "D_original": d_orig,
                "N_original": n_orig,
                "D_replication": d_rep,
                "N_replication": n_rep,
                "raw_file": str(base / rep_name),
                "match_author": "pain_coop",
            }
        )

    # Honesty and time pressure: original + 2 replications
    base = HARVEST / "awesome_time_honest"
    orig = read_csv(base / "github_01__original_cleaned.csv")
    d_orig, n_orig = pooled_d_from_groups(orig, "Treatment", "Dice_report", {1}, {0})
    for rep_num, rep_name in [
        ("exp1", "github_03__replication1_cleaned.csv"),
        ("exp2", "github_02__replication2_cleaned.csv"),
    ]:
        rep = read_csv(base / rep_name)
        d_rep, n_rep = pooled_d_from_groups(rep, "Treatment", "Dice_report", {1}, {0})
        rows.append(
            {
                "source_dataset": "Awesome replicability paired raw csvs",
                "project": "Other direct replications",
                "pair_id": f"awesome_time_honest_{rep_num}_dice_report",
                "original_title": "Honesty under time pressure (original)",
                "replication_title": f"Honesty under time pressure ({rep_num} replication)",
                "original_doi": "",
                "replication_doi": "",
                "outcome": "Dice_report",
                "D_original": d_orig,
                "N_original": n_orig,
                "D_replication": d_rep,
                "N_replication": n_rep,
                "raw_file": str(base / rep_name),
                "match_author": "time_honest",
            }
        )

    # Queue design and worker productivity: conservative overall comparison
    base = HARVEST / "awesome_queue"
    orig = read_csv(base / "github_01__original_clean.csv")
    rep = read_csv(base / "github_02__replication_clean.csv")
    d_orig, n_orig = pooled_d_from_groups(orig, "structure", "median_speed", {"Single"}, {"Parallel"})
    d_rep, n_rep = pooled_d_from_groups(rep, "structure", "median_speed", {"Single"}, {"Parallel"})
    rows.append(
        {
            "source_dataset": "Awesome replicability paired raw csvs",
            "project": "Other direct replications",
            "pair_id": "awesome_queue_median_speed",
            "original_title": "Queue design and worker productivity (original)",
            "replication_title": "Queue design and worker productivity (replication)",
            "original_doi": "",
            "replication_doi": "",
            "outcome": "median_speed",
            "D_original": d_orig,
            "N_original": n_orig,
            "D_replication": d_rep,
            "N_replication": n_rep,
            "raw_file": str(base / "github_02__replication_clean.csv"),
            "match_author": "queue_design",
        }
    )

    # Mind-body practice increases self-centrality: two repeated-measures studies.
    # Two of the published cleaned CSVs have the first three key columns rotated,
    # but the paired structure is recoverable from the companion processing scripts.
    base = HARVEST / "awesome_mindbody_selfcentrality"
    yoga_original = repair_rotated_key_columns(
        read_csv(base / "github_02__yoga_original_cleaned.csv"),
        "assessment_time",
    )
    yoga_replication = read_csv(base / "github_01__yoga_replication_cleaned.csv")
    meditation_original = read_csv(base / "github_03__meditation_original_cleaned.csv")
    meditation_replication = repair_rotated_key_columns(
        read_csv(base / "github_04__meditation_replication_cleaned.csv"),
        "assessment_time",
    )

    for pair_id, original_title, replication_title, orig_df, rep_df, raw_file, match_author in [
        (
            "awesome_mindbody_yoga_self_centrality",
            "Mind-body practice self-centrality yoga study (original)",
            "Mind-body practice self-centrality yoga study (replication)",
            yoga_original,
            yoga_replication,
            base / "github_01__yoga_replication_cleaned.csv",
            "mindbody_selfcentrality_yoga",
        ),
        (
            "awesome_mindbody_meditation_self_centrality",
            "Mind-body practice self-centrality meditation study (original)",
            "Mind-body practice self-centrality meditation study (replication)",
            meditation_original,
            meditation_replication,
            base / "github_04__meditation_replication_cleaned.csv",
            "mindbody_selfcentrality_meditation",
        ),
    ]:
        d_orig, n_orig = paired_d_from_condition_means(
            orig_df,
            "participant_id",
            "condition",
            "z_self_centrality",
        )
        d_rep, n_rep = paired_d_from_condition_means(
            rep_df,
            "participant_id",
            "condition",
            "z_self_centrality",
        )
        rows.append(
            {
                "source_dataset": "Awesome mind-body paired raw csvs",
                "project": "Other direct replications",
                "pair_id": pair_id,
                "original_title": original_title,
                "replication_title": replication_title,
                "original_doi": "",
                "replication_doi": "",
                "outcome": "Within-participant self-centrality difference (practice vs control assessment)",
                "D_original": d_orig,
                "N_original": n_orig,
                "D_replication": d_rep,
                "N_replication": n_rep,
                "raw_file": str(raw_file),
                "match_author": match_author,
            }
        )

    return rows


def main() -> None:
    ensure_dir(PROMOTED)
    rows = build_rows()
    df = pd.DataFrame(rows)
    out_path = PROMOTED / "awesome_replicability_paired__promoted_pairs.csv"
    df.to_csv(out_path, index=False)
    print(f"Wrote promoted rows: {len(df)}")
    print(f"Wrote file: {out_path}")


if __name__ == "__main__":
    main()
