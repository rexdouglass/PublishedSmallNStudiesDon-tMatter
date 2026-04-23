#!/usr/bin/env python3
"""Promote directly recoverable OSF-hosted replication pairs.

This script handles leads where the local harvest already contains either:
- original + replication raw data with a clear, reproduced effect definition, or
- replication clean data plus an original effect size explicitly documented in the
  preregistration / analysis materials harvested alongside the dataset.
"""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.formula.api import ols


ROOT = Path(__file__).resolve().parents[1]
HARVEST = ROOT / "data" / "raw" / "replication_projects" / "lead_harvest"
PROMOTED = ROOT / "data" / "derived" / "replication_pairs" / "harvest" / "promoted"


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def paired_d(a: pd.Series, b: pd.Series) -> tuple[float, int]:
    diff = pd.to_numeric(a, errors="coerce") - pd.to_numeric(b, errors="coerce")
    diff = diff.dropna().astype(float)
    if len(diff) < 2:
        return np.nan, 0
    sd = diff.std(ddof=1)
    if not (np.isfinite(sd) and sd > 0):
        return np.nan, 0
    return float(abs(diff.mean() / sd)), int(len(diff))


def pooled_d(df: pd.DataFrame, outcome: str, group: str, treat: str, control: str) -> tuple[float, int]:
    dat = df.dropna(subset=[outcome, group]).copy()
    a = pd.to_numeric(dat.loc[dat[group] == treat, outcome], errors="coerce").dropna().astype(float)
    b = pd.to_numeric(dat.loc[dat[group] == control, outcome], errors="coerce").dropna().astype(float)
    if len(a) < 2 or len(b) < 2:
        return np.nan, 0
    sd1 = a.std(ddof=1)
    sd2 = b.std(ddof=1)
    pooled_var = ((len(a) - 1) * sd1**2 + (len(b) - 1) * sd2**2) / (len(a) + len(b) - 2)
    if not (np.isfinite(pooled_var) and pooled_var > 0):
        return np.nan, 0
    d = abs((a.mean() - b.mean()) / math.sqrt(pooled_var))
    return float(d), int(len(a) + len(b))


def eta2_to_d(eta2: float) -> float:
    if not (np.isfinite(eta2) and 0 <= eta2 < 1):
        return np.nan
    r = math.sqrt(eta2)
    denom = max(1 - r * r, 1e-12)
    return float(abs((2 * r) / math.sqrt(denom)))


def build_contextual_bias_rows() -> list[dict]:
    base = HARVEST / "contextual_bias_2026"

    orig = pd.read_spss(base / "osf_01__Original_Dataset.sav")
    orig = orig.loc[orig["conditie"].eq("cbca")].copy()
    rep = pd.read_excel(base / "osf_02__FinalData.xlsx")

    for prefix, side in [("S", "neg"), ("O", "pos")]:
        for idx in [1, 2]:
            cols = [f"{prefix}{idx}CBCA{i}" for i in range(1, 20)]
            orig[f"sum_score_{side}{idx}"] = orig[cols].sum(axis=1)

    orig["mean_score_pos"] = orig[["sum_score_pos1", "sum_score_pos2"]].mean(axis=1)
    orig["mean_score_neg"] = orig[["sum_score_neg1", "sum_score_neg2"]].mean(axis=1)
    orig["mean_final_pos"] = orig[["onschuldig1", "onschuldig2"]].mean(axis=1)
    orig["mean_final_neg"] = orig[["schuldig1", "schuldig2"]].mean(axis=1)

    d_orig_cbca, n_orig_cbca = paired_d(orig["mean_score_pos"], orig["mean_score_neg"])
    d_rep_cbca, n_rep_cbca = paired_d(rep["mean_score_pos"], rep["mean_score_neg"])
    d_orig_cred, n_orig_cred = paired_d(orig["mean_final_pos"], orig["mean_final_neg"])
    d_rep_cred, n_rep_cred = paired_d(rep["mean_final_pos"], rep["mean_final_neg"])

    rows = [
        {
            "source_dataset": "Contextual bias in verbal credibility (OSF raw)",
            "project": "Other direct replications",
            "pair_id": "contextual_bias_cbca_scores",
            "original_title": "Bogaard et al. (2014) CBCA scoring",
            "replication_title": "Contextual Bias in Verbal Credibility Assessment (2026)",
            "original_doi": "",
            "replication_doi": "",
            "outcome": "CBCA score difference (positive vs negative context)",
            "D_original": d_orig_cbca,
            "N_original": n_orig_cbca,
            "D_replication": d_rep_cbca,
            "N_replication": n_rep_cbca,
            "raw_file": str(base / "osf_02__FinalData.xlsx"),
            "match_author": "bogaard_contextual_bias",
        },
        {
            "source_dataset": "Contextual bias in verbal credibility (OSF raw)",
            "project": "Other direct replications",
            "pair_id": "contextual_bias_final_credibility",
            "original_title": "Bogaard et al. (2014) final credibility judgment",
            "replication_title": "Contextual Bias in Verbal Credibility Assessment (2026)",
            "original_doi": "",
            "replication_doi": "",
            "outcome": "Final credibility judgment difference (positive vs negative context)",
            "D_original": d_orig_cred,
            "N_original": n_orig_cred,
            "D_replication": d_rep_cred,
            "N_replication": n_rep_cred,
            "raw_file": str(base / "osf_02__FinalData.xlsx"),
            "match_author": "bogaard_contextual_bias",
        },
    ]

    statement_specs = [
        (
            1,
            "contextual_bias_cbca_statement1",
            "Bogaard et al. (2014) CBCA scoring statement 1",
            "CBCA score difference for statement 1 (positive vs negative context)",
            "sum_score_pos1",
            "sum_score_neg1",
            "sumscore_pos1",
            "sumscore_neg1",
        ),
        (
            2,
            "contextual_bias_cbca_statement2",
            "Bogaard et al. (2014) CBCA scoring statement 2",
            "CBCA score difference for statement 2 (positive vs negative context)",
            "sum_score_pos2",
            "sum_score_neg2",
            "sumscore_pos2",
            "sumscore_neg2",
        ),
        (
            1,
            "contextual_bias_final_credibility_statement1",
            "Bogaard et al. (2014) final credibility judgment statement 1",
            "Final credibility judgment difference for statement 1 (positive vs negative context)",
            "onschuldig1",
            "schuldig1",
            "Positive1",
            "Negative1",
        ),
        (
            2,
            "contextual_bias_final_credibility_statement2",
            "Bogaard et al. (2014) final credibility judgment statement 2",
            "Final credibility judgment difference for statement 2 (positive vs negative context)",
            "onschuldig2",
            "schuldig2",
            "Positive2",
            "Negative2",
        ),
    ]

    for _, pair_id, original_title, outcome, orig_pos, orig_neg, rep_pos, rep_neg in statement_specs:
        d_orig, n_orig = paired_d(orig[orig_pos], orig[orig_neg])
        d_rep, n_rep = paired_d(rep[rep_pos], rep[rep_neg])
        rows.append(
            {
                "source_dataset": "Contextual bias in verbal credibility (OSF raw)",
                "project": "Other direct replications",
                "pair_id": pair_id,
                "original_title": original_title,
                "replication_title": "Contextual Bias in Verbal Credibility Assessment (2026)",
                "original_doi": "",
                "replication_doi": "",
                "outcome": outcome,
                "D_original": d_orig,
                "N_original": n_orig,
                "D_replication": d_rep,
                "N_replication": n_rep,
                "raw_file": str(base / "osf_02__FinalData.xlsx"),
                "match_author": "bogaard_contextual_bias",
            }
        )

    return rows


def build_deceptive_intentions_rows() -> list[dict]:
    base = HARVEST / "deceptive_intentions_2018"
    df = pd.read_table(base / "osf_03__main_data.txt")
    df = df.loc[df["instructions"] == 1].copy()
    df = df.loc[~df["participant"].isin([47, 84])].copy()

    d_rep, n_rep = pooled_d(df, "q1_specifictimes.y", "condition", "t", "d")

    # Warmelink et al. (2013), as documented in the replication analysis script:
    # t = 2.49, n1 = 42, n2 = 42 for the original specific-times comparison.
    d_orig = abs(2.49 * math.sqrt((1 / 42) + (1 / 42)))

    return [
        {
            "source_dataset": "Deceptive intentions verbal credibility (OSF raw)",
            "project": "Other direct replications",
            "pair_id": "deceptive_intentions_specific_times",
            "original_title": "Warmelink et al. (2013) specific time references",
            "replication_title": "Kleinberg et al. (2018) deceptive intentions replication",
            "original_doi": "",
            "replication_doi": "",
            "outcome": "Specific time references",
            "D_original": d_orig,
            "N_original": 84,
            "D_replication": d_rep,
            "N_replication": n_rep,
            "raw_file": str(base / "osf_03__main_data.txt"),
            "match_author": "warmelink_deceptive_intentions",
        }
    ]


def build_linguistic_frame_rows() -> list[dict]:
    base = HARVEST / "linguistic_frame_liability" / "manual"

    rows: list[dict] = []

    # Original study 1 effect sizes documented in the stage-1 manuscript.
    original_study1_n = 116 + 120
    original_blame_d = 0.53
    original_fine_d = 0.52

    study1_specs = [
        ("study_1a.csv", "Croatian", 10200),
        ("study_1b.csv", "English", 4500),
    ]
    for fn, label, fine_limit in study1_specs:
        df = pd.read_csv(base / fn)
        df = df.loc[df["informed_consent"] == True].copy()
        fine = pd.to_numeric(df["assess_fine"], errors="coerce")
        df = df.loc[fine.isna() | (fine <= fine_limit)].copy()

        d_blame, n_blame = pooled_d(df, "assess_blame", "experimental_situation", "agentive", "nonagentive")
        d_fine, n_fine = pooled_d(df, "assess_fine", "experimental_situation", "agentive", "nonagentive")

        rows.extend(
            [
                {
                    "source_dataset": "Linguistic frame liability clean csvs",
                    "project": "Other direct replications",
                    "pair_id": f"linguistic_frame_{label.lower()}_study1_blame",
                    "original_title": "Fausey & Boroditsky (2010) study 1 blame",
                    "replication_title": f"Linguistic frame replication study 1 ({label})",
                    "original_doi": "",
                    "replication_doi": "",
                    "outcome": "Perceived blame",
                    "D_original": original_blame_d,
                    "N_original": original_study1_n,
                    "D_replication": d_blame,
                    "N_replication": n_blame,
                    "raw_file": str(base / fn),
                    "match_author": "fausey_boroditsky_blame",
                },
                {
                    "source_dataset": "Linguistic frame liability clean csvs",
                    "project": "Other direct replications",
                    "pair_id": f"linguistic_frame_{label.lower()}_study1_fine",
                    "original_title": "Fausey & Boroditsky (2010) study 1 fine",
                    "replication_title": f"Linguistic frame replication study 1 ({label})",
                    "original_doi": "",
                    "replication_doi": "",
                    "outcome": "Financial liability / fine",
                    "D_original": original_fine_d,
                    "N_original": original_study1_n,
                    "D_replication": d_fine,
                    "N_replication": n_fine,
                    "raw_file": str(base / fn),
                    "match_author": "fausey_boroditsky_fine",
                },
            ]
        )

    # Original study 2 linguistic-cues main effect documented in the stage-1 manuscript.
    # Original eta^2 = .03 for the language main effect on financial liability, N = 179.
    original_study2_d = eta2_to_d(0.03)
    original_study2_n = 179

    study2_specs = [
        ("study_2a.csv", "Croatian", 10200),
        ("study_2b.csv", "English", 4500),
    ]
    for fn, label, fine_limit in study2_specs:
        df = pd.read_csv(base / fn)
        df = df.loc[df["informed_consent"] == True].copy()
        fine = pd.to_numeric(df["assess_fine"], errors="coerce")
        df = df.loc[fine.isna() | (fine <= fine_limit)].copy()
        df = df.dropna(subset=["assess_fine", "agency", "blame_level"]).copy()

        model = ols("assess_fine ~ C(agency) * C(blame_level)", data=df).fit()
        anova = sm.stats.anova_lm(model, typ=2)
        ss_agency = float(anova.loc["C(agency)", "sum_sq"])
        ss_resid = float(anova.loc["Residual", "sum_sq"])
        eta_p = ss_agency / (ss_agency + ss_resid)
        d_rep = eta2_to_d(eta_p)

        rows.append(
            {
                "source_dataset": "Linguistic frame liability clean csvs",
                "project": "Other direct replications",
                "pair_id": f"linguistic_frame_{label.lower()}_study2_fine",
                "original_title": "Fausey & Boroditsky (2010) study 2 fine",
                "replication_title": f"Linguistic frame replication study 2 ({label})",
                "original_doi": "",
                "replication_doi": "",
                "outcome": "Financial liability / fine main effect of agency",
                "D_original": original_study2_d,
                "N_original": original_study2_n,
                "D_replication": d_rep,
                "N_replication": int(len(df)),
                "raw_file": str(base / fn),
                "match_author": "fausey_boroditsky_fine_study2",
            }
        )

    return rows


def main() -> None:
    ensure_dir(PROMOTED)
    rows = []
    rows.extend(build_contextual_bias_rows())
    rows.extend(build_deceptive_intentions_rows())
    rows.extend(build_linguistic_frame_rows())
    out = pd.DataFrame(rows)
    out_path = PROMOTED / "local_osf_direct_replications__promoted_pairs.csv"
    out.to_csv(out_path, index=False)
    print(f"Wrote promoted rows: {len(out)}")
    print(f"Wrote file: {out_path}")


if __name__ == "__main__":
    main()
