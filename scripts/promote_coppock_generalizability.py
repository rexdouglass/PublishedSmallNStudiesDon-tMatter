#!/usr/bin/env python3
"""Promote Coppock (2019) standardized original-vs-replication estimates.

The Dataverse archive contains the paper's analysis-results RData plus the
stacked study datasets. Treatment estimates are already reported with
standardized dependent variables, so the coefficients are on a Cohen's-d-like
scale for this Plot 1 harvest lane.
"""

from __future__ import annotations

import math
import re
import tempfile
import zipfile
from pathlib import Path

import pandas as pd
import pyreadr


ROOT = Path(__file__).resolve().parents[1]
RAW_ZIP = (
    ROOT
    / "data"
    / "raw"
    / "replication_projects"
    / "lead_harvest"
    / "coppock_2019"
    / "dataverse_dvn_f1cffm"
    / "dataverse_files.zip"
)
OUT = (
    ROOT
    / "data"
    / "derived"
    / "replication_pairs"
    / "harvest"
    / "promoted"
    / "coppock_generalizability__promoted_pairs.csv"
)

RESULTS_RDATA = "coppock_generalizability_analysis_results.RData"
STUDIES_RDATA = "coppock_generalizability_studies.RData"
META_RDATA = "coppock_generalizability_study_data.RData"


def slugify(value: object) -> str:
    text = str(value or "").strip().lower()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    return text.strip("_") or "missing"


def finite_abs(value: object) -> float:
    try:
        out = abs(float(value))
    except (TypeError, ValueError):
        return math.nan
    return out if math.isfinite(out) else math.nan


def complete_n(df: pd.DataFrame, sample: str, columns: list[str], filter_mask=None) -> int:
    data = df.loc[df["sample"].astype(str).eq(sample)].copy()
    if filter_mask is not None:
        data = data.loc[filter_mask(data)]
    available = [col for col in columns if col in data.columns]
    if len(available) != len(columns):
        missing = sorted(set(columns) - set(available))
        raise KeyError(f"Missing columns for {sample}: {missing}")
    return int(data[available].dropna().shape[0])


def build_n_map(studies: dict[str, pd.DataFrame], results: pd.DataFrame) -> pd.DataFrame:
    """Recreate the model-frame Ns used by the archived analysis script."""

    model_specs = {
        ("concealed_carry", "dv_gun_s"): (
            "concealed_carry_stacked",
            ["dv_gun_s", "Z_gun", "weights"],
            None,
        ),
        ("immigration", "brader_num_imm_s"): (
            "immigration_stacked",
            ["brader_num_imm_s", "Z_brader_pos_neg", "weights"],
            lambda d: d["Z_brader_pos_neg"].astype(str).ne("control"),
        ),
        ("immigration", "brader_neg_impact_s"): (
            "immigration_stacked",
            ["brader_neg_impact_s", "Z_brader_pos_neg", "weights"],
            lambda d: d["Z_brader_pos_neg"].astype(str).ne("control"),
        ),
        ("death_penalty", "CP_dv_s"): (
            "death_penalty_stacked",
            ["CP_dv_s", "Z_CP_3", "weights"],
            lambda d: d["Z_CP_3"].astype(str).ne("control"),
        ),
        ("superordinate_id", "willing_s"): (
            "superordinate_id_stacked",
            ["willing_s", "Z_identity", "Z_particularism"],
            None,
        ),
        ("patriot_act", "PA_support_s"): (
            "patriot_act_stacked",
            ["PA_support_s", "T1_condition_name", "weights"],
            None,
        ),
        ("elite_endorsements", "imm_dv_s"): (
            "elite_endorsements_stacked",
            ["imm_dv_s", "Z_imm_match", "pid_3", "weights"],
            lambda d: d["Z_imm_match"].astype(str).ne("control"),
        ),
        ("elite_endorsements", "fore_dv_s"): (
            "elite_endorsements_stacked",
            ["fore_dv_s", "Z_fore_match", "pid_3", "weights"],
            lambda d: d["Z_fore_match"].astype(str).ne("control"),
        ),
        ("mental_illness", "mcginty_magazines_s"): (
            "mental_illness_stacked",
            ["mcginty_magazines_s", "Z_mcginty_news", "Z_mcginty_policy", "weights"],
            None,
        ),
        ("mental_illness", "mcginty_SMI_danger_s"): (
            "mental_illness_stacked",
            ["mcginty_SMI_danger_s", "Z_mcginty_news", "Z_mcginty_policy", "weights"],
            None,
        ),
        ("system_threat", "craig_num_imm_s"): (
            "system_threat_stacked",
            ["craig_num_imm_s", "Z_craig", "weights"],
            None,
        ),
        ("system_threat", "craig_wol_s"): (
            "system_threat_stacked",
            ["craig_wol_s", "Z_craig", "weights"],
            None,
        ),
        ("expert_economists", "agree_1_s"): (
            "expert_economists_stacked",
            ["agree_1_s", "Z_expert_1", "weights"],
            None,
        ),
        ("expert_economists", "agree_2_s"): (
            "expert_economists_stacked",
            ["agree_2_s", "Z_expert_2", "weights"],
            None,
        ),
        ("expert_economists", "agree_3_s"): (
            "expert_economists_stacked",
            ["agree_3_s", "Z_expert_3", "weights"],
            None,
        ),
        ("expert_economists", "agree_4_s"): (
            "expert_economists_stacked",
            ["agree_4_s", "Z_expert_4", "weights"],
            None,
        ),
        ("expert_economists", "agree_5_s"): (
            "expert_economists_stacked",
            ["agree_5_s", "Z_expert_5", "weights"],
            None,
        ),
        ("free_trade", "Y_Hiscox_s"): (
            "free_trade_stacked",
            ["Y_Hiscox_s", "Z_Hiscox_expert", "Z_Hiscox_valence", "weights"],
            None,
        ),
        ("polarization", "L_ex_s"): (
            "polarization_stacked",
            ["L_ex_s", "Z_Levendusky", "weights"],
            lambda d: d["Z_Levendusky"].astype(str).ne("placebo"),
        ),
        ("polarization", "L_dif_s"): (
            "polarization_stacked",
            ["L_dif_s", "Z_Levendusky", "weights"],
            lambda d: d["Z_Levendusky"].astype(str).ne("placebo"),
        ),
        ("frame_breadth", "Y_crime_s"): (
            "frame_breadth_stacked",
            ["Y_crime_s", "Z_crime_Y_crime", "weights"],
            None,
        ),
        ("frame_breadth", "Y_health_s"): (
            "frame_breadth_stacked",
            ["Y_health_s", "Z_health_Y_health", "weights"],
            None,
        ),
        ("frame_breadth", "Y_stimulus_s"): (
            "frame_breadth_stacked",
            ["Y_stimulus_s", "Z_stimulus_Y_stimulus", "weights"],
            None,
        ),
        ("frame_breadth", "Y_terror_s"): (
            "frame_breadth_stacked",
            ["Y_terror_s", "Z_terror_Y_terror", "weights"],
            None,
        ),
    }

    rows: list[dict[str, object]] = []
    for (study, dv), group in results.groupby(["study", "dv"], sort=False):
        data_name, columns, filter_mask = model_specs[(study, dv)]
        data = studies[data_name]
        for sample in sorted(group["sample"].astype(str).unique()):
            n = complete_n(data, sample, columns, filter_mask=filter_mask)
            for term in sorted(group.loc[group["sample"].astype(str).eq(sample), "term"].astype(str).unique()):
                rows.append({"study": study, "dv": dv, "sample": sample, "term": term, "nobs": n})
    return pd.DataFrame(rows)


def extract_archive() -> tuple[pd.DataFrame, dict[str, pd.DataFrame], pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    if not RAW_ZIP.exists():
        raise FileNotFoundError(f"Missing Dataverse archive: {RAW_ZIP}")

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        with zipfile.ZipFile(RAW_ZIP) as zf:
            for name in [RESULTS_RDATA, STUDIES_RDATA, META_RDATA]:
                zf.extract(name, tmp_path)

        results = pyreadr.read_r(str(tmp_path / RESULTS_RDATA))["results"]
        studies = dict(pyreadr.read_r(str(tmp_path / STUDIES_RDATA)))
        meta = pyreadr.read_r(str(tmp_path / META_RDATA))
        return results, studies, meta["study_df"], meta["dvs_df"], meta["coefficients_df"]


def main() -> None:
    results, studies, study_df, dvs_df, coefficients_df = extract_archive()
    results = results.copy()
    for col in ["study", "sample", "term", "dv"]:
        results[col] = results[col].astype(str)

    n_map = build_n_map(studies, results)
    annotated = results.merge(n_map, on=["study", "sample", "dv", "term"], how="left", validate="one_to_one")
    if annotated["nobs"].isna().any():
        missing = annotated.loc[annotated["nobs"].isna(), ["study", "sample", "dv", "term"]]
        raise RuntimeError(f"Missing model Ns:\n{missing.to_string(index=False)}")

    study_labels = dict(zip(study_df["study"].astype(str), study_df["study_label"].astype(str)))
    dv_labels = dict(zip(dvs_df["dv"].astype(str), dvs_df["dv_name"].astype(str)))
    coef_labels = dict(zip(coefficients_df["term"].astype(str), coefficients_df["coef_name"].astype(str)))

    original = annotated.loc[annotated["sample"].eq("original")].copy()
    replications = annotated.loc[~annotated["sample"].eq("original")].copy()
    paired = original.merge(
        replications,
        on=["study", "dv", "term"],
        suffixes=("_original", "_replication"),
        validate="one_to_many",
    )

    rows: list[dict[str, object]] = []
    for row in paired.itertuples(index=False):
        sample = getattr(row, "sample_replication")
        study = getattr(row, "study")
        dv = getattr(row, "dv")
        term = getattr(row, "term")
        study_label = study_labels.get(study, study)
        sample_label = {"mt": "MTurk", "gfk": "GfK"}.get(sample, sample.upper())
        outcome = f"{dv_labels.get(dv, dv)}: {coef_labels.get(term, term)}"
        rows.append(
            {
                "source_dataset": "Coppock 2019 generalizability corpus",
                "project": "Coppock 2019 generalizability corpus",
                "pair_id": f"coppock_2019_{slugify(study)}_{slugify(dv)}_{slugify(term)}_{slugify(sample)}",
                "original_title": f"{study_label} original survey experiment",
                "replication_title": f"Coppock (2019) {sample_label} replication of {study_label}",
                "original_doi": "",
                "replication_doi": "",
                "outcome": outcome,
                "D_original": finite_abs(getattr(row, "est_original")),
                "N_original": int(getattr(row, "nobs_original")),
                "D_replication": finite_abs(getattr(row, "est_replication")),
                "N_replication": int(getattr(row, "nobs_replication")),
                "raw_file": str(RAW_ZIP),
                "match_author": f"coppock_2019_{study}_{dv}_{term}_{sample}",
            }
        )

    out = pd.DataFrame(rows).sort_values(["source_dataset", "N_replication", "pair_id"], ascending=[True, False, True])
    OUT.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT, index=False)
    kept = int(((out["N_original"] >= 10) & (out["N_replication"] > out["N_original"])).sum())
    print(f"Wrote {len(out)} Coppock rows to {OUT}")
    print(f"{kept} rows pass the Plot 1 N gates before duplicate collapsing/significance filters")


if __name__ == "__main__":
    main()
