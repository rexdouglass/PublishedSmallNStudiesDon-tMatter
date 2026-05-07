#!/usr/bin/env python3
"""Recompute the Trafimow/Hughes registered-replication focal contrast.

This script is deliberately narrow. It uses the locally mirrored OSF files for
Rife et al.'s Registered Replication Report of Trafimow and Hughes (2012) and
recomputes the word-generation exact-replication contrast:

    death/no-delay vs all other conditions

The RRR reports the focal replication on the raw death-word-count scale, while
Figure 1 currently needs a D-compatible effect. The output therefore preserves
the raw mean-difference meta-analysis and also provides two transparent
standardized summaries:

1. a participant-pooled SMD from the raw focal contrast, and
2. a random-effects meta-analysis of lab-level SMDs.

The scan/promotion layer can decide whether either standardized route is
acceptable for Figure 1.
"""

from __future__ import annotations

import csv
import hashlib
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "api_candidate_410ff1685532db83"
RAW_DIR = (
    ROOT
    / "data"
    / "raw"
    / "replication_projects"
    / "individual_search_batch006"
    / CANDIDATE_ID
    / "osf_atc39_data"
)
OUT_DIR = ROOT / "steps" / "individual_replication_papers" / "figure1" / "auto_mining"
LAB_OUT = OUT_DIR / "trafimow_hughes_rrr_lab_effects.tsv"
SUMMARY_OUT = OUT_DIR / "trafimow_hughes_rrr_summary.tsv"
INPUTS_OUT = OUT_DIR / "trafimow_hughes_rrr_input_files.tsv"
REPORT_OUT = ROOT / "reports" / "figure1_auto_mining_trafimow_hughes_rrr_2026-05-05.md"

LANGUAGE_LIST_FILES = {
    "en": "DeathWordList_English.txt",
    "nl": "DeathWordList_Dutch.txt",
    "de": "DeathWordList_German.txt",
    "tr": "DeathWordList_Turkish.txt",
    "es": "DeathWordList_Spanish.txt",
    "sk": "DeathWordList_Slovak.txt",
}
ARTICLE_TABLE4_WORD_GENERATION = {
    # Values copied from mirrored RRR PDF Table 4:
    # "Differences in Death-Thought Accessibility by Experimental/Control
    # Conditions by Lab (Word-Generation Task)".
    # Tuple order: death/no-delay M, death/no-delay SD, all-other M, all-other SD.
    "BeaudryLab": (0.14, 0.36, 0.19, 0.46),
    "BehavioralNeuroscienceLab": (0.80, 0.84, 0.19, 0.39),
    "BehavioralScienceInstitute": (0.96, 1.48, 0.92, 1.16),
    "BehaviouralScienceCentre": (0.14, 0.36, 0.11, 0.31),
    "BrainDynamicsLab": (0.09, 0.29, 0.10, 0.34),
    "BYUI": (0.00, 0.00, 0.14, 0.35),
    "CDAL": (0.29, 0.49, 0.23, 0.43),
    "CognitivePsychologyLab": (0.32, 0.85, 0.18, 0.45),
    "CoventryBOP": (0.57, 0.76, 0.13, 0.34),
    "ExperimentalPsychologyLab": (0.13, 0.35, 0.00, 0.00),
    "GRECIL": (0.21, 0.43, 0.06, 0.24),
    "KasselLab": (0.00, 0.00, 0.00, 0.00),
    "MSUCloseRelationshipsLab": (0.38, 0.59, 0.18, 0.43),
    "OzArGeGroup": (0.36, 0.66, 0.14, 0.35),
    "SPAL": (0.08, 0.29, 0.11, 0.40),
    "SPlab": (1.89, 1.64, 0.99, 1.14),
    "StigmaLab": (0.44, 0.73, 0.19, 0.40),
    "UNIPOUPJS": (0.00, 0.00, 0.04, 0.21),
    "UnivVienna": (0.25, 0.46, 0.04, 0.20),
    "WorkSocialPsychology": (0.11, 0.32, 0.08, 0.27),
    "unipoPsychLab": (0.03, 0.18, 0.03, 0.18),
}
WORD_COLUMNS = [
    "WGTASK[word1_response]",
    "WGTASK[word2_response]",
    "WGTASK[word3_response]",
    "WGTASK[word4_response]",
    "WGTASK[word5_response]",
]


@dataclass
class MetaEstimate:
    estimate: float
    se: float
    ci_low: float
    ci_high: float
    q: float
    tau2: float
    k: int


def clean_cell(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and math.isnan(value):
        return ""
    return str(value).strip()


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def write_tsv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter="\t", extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: clean_cell(row.get(key, "")) for key in fieldnames})


def load_death_words() -> dict[str, set[str]]:
    out: dict[str, set[str]] = {}
    for language, filename in LANGUAGE_LIST_FILES.items():
        path = RAW_DIR / filename
        words = {
            line.strip().lower().replace(" ", "")
            for line in path.read_text(encoding="utf-8", errors="replace").splitlines()
            if line.strip()
        }
        out[language] = words
    return out


def read_coding_file(path: Path) -> pd.DataFrame:
    """Return id/exclude rows from a coding file.

    Blank decisions are treated as no exclusion because the downloaded OSF
    coding files are mostly uncompleted placeholders. Completed files with
    numeric 0/1 or y/n decisions are applied.
    """

    first_line = path.read_text(encoding="utf-8", errors="replace").splitlines()[0]
    sep = ";" if first_line.count(";") > first_line.count(",") else ","
    df = pd.read_csv(path, sep=sep, dtype=str, keep_default_na=False)
    if df.empty:
        return pd.DataFrame(columns=["id", "manual_exclude", "manual_decision_source"])
    id_col = df.columns[0]
    decision_cols = [col for col in df.columns if "decision" in col.lower()]
    if not decision_cols:
        return pd.DataFrame(columns=["id", "manual_exclude", "manual_decision_source"])
    decision_col = decision_cols[0]

    rows: list[dict[str, Any]] = []
    for _, row in df.iterrows():
        participant_id = clean_cell(row.get(id_col))
        decision = clean_cell(row.get(decision_col)).lower()
        if not participant_id or not decision:
            continue
        if decision in {"0", "n", "no", "exclude", "excluded", "false"}:
            exclude = 1
        elif decision in {"1", "y", "yes", "include", "included", "true"}:
            exclude = 0
        else:
            continue
        rows.append(
            {
                "id": participant_id,
                "manual_exclude": exclude,
                "manual_decision_source": f"{path.name}:{decision_col}={decision}",
            }
        )
    return pd.DataFrame(rows, columns=["id", "manual_exclude", "manual_decision_source"])


def coding_for_lab(lab: str) -> pd.DataFrame:
    candidates = [
        RAW_DIR / f"{lab}_coding_Completed.csv",
        RAW_DIR / f"CodingSheet_{lab}_completed.csv",
        RAW_DIR / f"{lab}_coding.csv",
    ]
    frames = [read_coding_file(path) for path in candidates if path.exists()]
    frames = [frame for frame in frames if not frame.empty]
    if not frames:
        return pd.DataFrame(columns=["id", "manual_exclude", "manual_decision_source"])
    combined = pd.concat(frames, ignore_index=True)
    # Completed files appear before placeholder coding files; keep the first
    # nonblank decision for each participant.
    return combined.drop_duplicates("id", keep="first")


def death_word_count(row: pd.Series, death_words: dict[str, set[str]]) -> int:
    language = clean_cell(row.get("startlanguage")).lower()
    words = death_words.get(language, set())
    count = 0
    for col in WORD_COLUMNS:
        word = clean_cell(row.get(col)).lower().replace(" ", "")
        if word and word in words:
            count += 1
    return count


def pooled_sd(n1: int, sd1: float, n0: int, sd0: float) -> float:
    if n1 < 2 or n0 < 2:
        return float("nan")
    numerator = (n1 - 1) * sd1**2 + (n0 - 1) * sd0**2
    denominator = n1 + n0 - 2
    if denominator <= 0:
        return float("nan")
    return math.sqrt(numerator / denominator)


def mean_sd(values: pd.Series) -> tuple[float, float]:
    if values.empty:
        return float("nan"), float("nan")
    return float(values.mean()), float(values.std(ddof=1))


def mean_difference_se(n1: int, sd1: float, n0: int, sd0: float) -> float:
    if n1 < 2 or n0 < 2:
        return float("nan")
    return math.sqrt(sd1**2 / n1 + sd0**2 / n0)


def smd_se(d: float, n1: int, n0: int) -> float:
    if n1 < 2 or n0 < 2:
        return float("nan")
    var = (n1 + n0) / (n1 * n0) + (d**2 / (2 * (n1 + n0 - 2)))
    return math.sqrt(var)


def random_effects(values: list[float], ses: list[float]) -> MetaEstimate:
    valid = [(v, se) for v, se in zip(values, ses) if math.isfinite(v) and math.isfinite(se) and se > 0]
    k = len(valid)
    if k == 0:
        return MetaEstimate(float("nan"), float("nan"), float("nan"), float("nan"), float("nan"), float("nan"), 0)
    vals = [v for v, _ in valid]
    variances = [se**2 for _, se in valid]
    weights = [1 / var for var in variances]
    fixed = sum(w * v for w, v in zip(weights, vals)) / sum(weights)
    q = sum(w * (v - fixed) ** 2 for w, v in zip(weights, vals))
    c = sum(weights) - (sum(w**2 for w in weights) / sum(weights))
    tau2 = max(0.0, (q - (k - 1)) / c) if c > 0 else 0.0
    random_weights = [1 / (var + tau2) for var in variances]
    estimate = sum(w * v for w, v in zip(random_weights, vals)) / sum(random_weights)
    se = math.sqrt(1 / sum(random_weights))
    return MetaEstimate(estimate, se, estimate - 1.96 * se, estimate + 1.96 * se, q, tau2, k)


def load_analysis_rows(death_words: dict[str, set[str]]) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    for main_path in sorted(RAW_DIR.glob("*_main.csv")):
        lab = main_path.name.removesuffix("_main.csv")
        main = pd.read_csv(main_path, dtype=str, keep_default_na=False)
        coding = coding_for_lab(lab)
        if not coding.empty:
            main = main.merge(coding, on="id", how="left")
        else:
            main["manual_exclude"] = 0
            main["manual_decision_source"] = ""
        main["manual_exclude"] = pd.to_numeric(main["manual_exclude"], errors="coerce").fillna(0).astype(int)
        main["analysis_lab"] = lab
        frames.append(main)

    data = pd.concat(frames, ignore_index=True, sort=False)
    data["Gender_num"] = pd.to_numeric(data["Gender"], errors="coerce")
    data["Age_num"] = pd.to_numeric(data["Age"], errors="coerce")
    data["Understand_num"] = pd.to_numeric(data["Understand"], errors="coerce")
    data["interviewtime_num"] = pd.to_numeric(data["interviewtime"], errors="coerce")
    data["essayGroup_num"] = pd.to_numeric(data["essayGroup"], errors="coerce")
    data["delayGroup_num"] = pd.to_numeric(data["delayGroup"], errors="coerce")
    data["dvGroup_num"] = pd.to_numeric(data["dvGroup"], errors="coerce")
    data["death_word_count_dv1"] = data.apply(lambda row: death_word_count(row, death_words), axis=1)

    mask = (
        data["Gender_num"].notna()
        & data["Age_num"].notna()
        & data["Understand_num"].eq(0)
        & data["interviewtime_num"].gt(300)
        & data["manual_exclude"].eq(0)
        & data["dvGroup_num"].eq(1)
        & data["analysis_lab"].ne("METAlab")
    )
    analysis = data.loc[mask].copy()
    analysis["focal_group"] = "control_all_other"
    analysis.loc[
        analysis["essayGroup_num"].eq(1) & analysis["delayGroup_num"].eq(2),
        "focal_group",
    ] = "death_no_delay"
    return analysis


def build_lab_effects(analysis: pd.DataFrame) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for lab, group in sorted(analysis.groupby("analysis_lab")):
        exp = group[group["focal_group"].eq("death_no_delay")]["death_word_count_dv1"]
        ctrl = group[group["focal_group"].eq("control_all_other")]["death_word_count_dv1"]
        n_exp = int(exp.shape[0])
        n_ctrl = int(ctrl.shape[0])
        mean_exp, sd_exp = mean_sd(exp)
        mean_ctrl, sd_ctrl = mean_sd(ctrl)
        mean_diff = mean_exp - mean_ctrl
        md_se = mean_difference_se(n_exp, sd_exp, n_ctrl, sd_ctrl)
        psd = pooled_sd(n_exp, sd_exp, n_ctrl, sd_ctrl)
        d = mean_diff / psd if math.isfinite(psd) and psd > 0 else float("nan")
        d_se = smd_se(d, n_exp, n_ctrl)
        rows.append(
            {
                "candidate_id": CANDIDATE_ID,
                "lab": lab,
                "n_death_no_delay": n_exp,
                "mean_death_no_delay": mean_exp,
                "sd_death_no_delay": sd_exp,
                "n_all_other": n_ctrl,
                "mean_all_other": mean_ctrl,
                "sd_all_other": sd_ctrl,
                "mean_difference_death_no_delay_minus_all_other": mean_diff,
                "mean_difference_se": md_se,
                "pooled_sd": psd,
                "cohen_d_death_no_delay_minus_all_other": d,
                "cohen_d_se": d_se,
            }
        )
    return rows


def build_summary(analysis: pd.DataFrame, lab_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    exp = analysis[analysis["focal_group"].eq("death_no_delay")]["death_word_count_dv1"]
    ctrl = analysis[analysis["focal_group"].eq("control_all_other")]["death_word_count_dv1"]
    n_exp = int(exp.shape[0])
    n_ctrl = int(ctrl.shape[0])
    mean_exp, sd_exp = mean_sd(exp)
    mean_ctrl, sd_ctrl = mean_sd(ctrl)
    raw_md = mean_exp - mean_ctrl
    raw_psd = pooled_sd(n_exp, sd_exp, n_ctrl, sd_ctrl)
    raw_d = raw_md / raw_psd
    md_meta = random_effects(
        [float(row["mean_difference_death_no_delay_minus_all_other"]) for row in lab_rows],
        [float(row["mean_difference_se"]) for row in lab_rows],
    )
    d_meta = random_effects(
        [float(row["cohen_d_death_no_delay_minus_all_other"]) for row in lab_rows],
        [float(row["cohen_d_se"]) for row in lab_rows],
    )
    table4_rows = []
    for row in lab_rows:
        lab = str(row["lab"])
        if lab not in ARTICLE_TABLE4_WORD_GENERATION:
            continue
        table_m1, table_sd1, table_m0, table_sd0 = ARTICLE_TABLE4_WORD_GENERATION[lab]
        table_n1 = int(row["n_death_no_delay"])
        table_n0 = int(row["n_all_other"])
        table_md = table_m1 - table_m0
        table_md_se = mean_difference_se(table_n1, table_sd1, table_n0, table_sd0)
        table_psd = pooled_sd(table_n1, table_sd1, table_n0, table_sd0)
        table_d = table_md / table_psd if math.isfinite(table_psd) and table_psd > 0 else float("nan")
        table_d_se = smd_se(table_d, table_n1, table_n0)
        table4_rows.append(
            {
                "lab": lab,
                "n1": table_n1,
                "n0": table_n0,
                "m1": table_m1,
                "sd1": table_sd1,
                "m0": table_m0,
                "sd0": table_sd0,
                "md": table_md,
                "md_se": table_md_se,
                "d": table_d,
                "d_se": table_d_se,
            }
        )
    table4_md_meta = random_effects([row["md"] for row in table4_rows], [row["md_se"] for row in table4_rows])
    table4_d_meta = random_effects([row["d"] for row in table4_rows], [row["d_se"] for row in table4_rows])
    table4_n1 = sum(row["n1"] for row in table4_rows)
    table4_n0 = sum(row["n0"] for row in table4_rows)
    table4_m1 = sum(row["n1"] * row["m1"] for row in table4_rows) / table4_n1
    table4_m0 = sum(row["n0"] * row["m0"] for row in table4_rows) / table4_n0
    table4_ss1 = sum((row["n1"] - 1) * row["sd1"] ** 2 + row["n1"] * (row["m1"] - table4_m1) ** 2 for row in table4_rows)
    table4_ss0 = sum((row["n0"] - 1) * row["sd0"] ** 2 + row["n0"] * (row["m0"] - table4_m0) ** 2 for row in table4_rows)
    table4_sd1 = math.sqrt(table4_ss1 / (table4_n1 - 1))
    table4_sd0 = math.sqrt(table4_ss0 / (table4_n0 - 1))
    table4_psd = pooled_sd(table4_n1, table4_sd1, table4_n0, table4_sd0)
    table4_d_pooled = (table4_m1 - table4_m0) / table4_psd
    article_md = 0.08
    article_standardized_by_raw_pooled_sd = article_md / raw_psd
    return [
        {
            "summary_id": "participant_pooled_raw_focal_contrast",
            "candidate_id": CANDIDATE_ID,
            "n_death_no_delay": n_exp,
            "n_all_other": n_ctrl,
            "n_total": n_exp + n_ctrl,
            "mean_death_no_delay": mean_exp,
            "sd_death_no_delay": sd_exp,
            "mean_all_other": mean_ctrl,
            "sd_all_other": sd_ctrl,
            "effect": raw_d,
            "effect_scale": "cohen_d_from_participant_pooled_word_generation_counts",
            "raw_mean_difference": raw_md,
            "raw_mean_difference_se": mean_difference_se(n_exp, sd_exp, n_ctrl, sd_ctrl),
            "tau2": "",
            "q": "",
            "k_labs": len(lab_rows),
            "ci_low": "",
            "ci_high": "",
            "notes": "Computed directly from mirrored OSF participant CSVs after RRR exclusions approximated from available coding files; METAlab excluded for exact word-generation replication.",
        },
        {
            "summary_id": "lab_random_effects_raw_mean_difference",
            "candidate_id": CANDIDATE_ID,
            "n_death_no_delay": n_exp,
            "n_all_other": n_ctrl,
            "n_total": n_exp + n_ctrl,
            "mean_death_no_delay": "",
            "sd_death_no_delay": "",
            "mean_all_other": "",
            "sd_all_other": "",
            "effect": md_meta.estimate,
            "effect_scale": "death_word_count_mean_difference_random_effects",
            "raw_mean_difference": md_meta.estimate,
            "raw_mean_difference_se": md_meta.se,
            "tau2": md_meta.tau2,
            "q": md_meta.q,
            "k_labs": md_meta.k,
            "ci_low": md_meta.ci_low,
            "ci_high": md_meta.ci_high,
            "notes": "Random-effects meta-analysis of lab-level raw mean differences, recomputed from mirrored OSF participant CSVs.",
        },
        {
            "summary_id": "lab_random_effects_smd",
            "candidate_id": CANDIDATE_ID,
            "n_death_no_delay": n_exp,
            "n_all_other": n_ctrl,
            "n_total": n_exp + n_ctrl,
            "mean_death_no_delay": "",
            "sd_death_no_delay": "",
            "mean_all_other": "",
            "sd_all_other": "",
            "effect": d_meta.estimate,
            "effect_scale": "cohen_d_random_effects_across_lab_smds",
            "raw_mean_difference": "",
            "raw_mean_difference_se": d_meta.se,
            "tau2": d_meta.tau2,
            "q": d_meta.q,
            "k_labs": d_meta.k,
            "ci_low": d_meta.ci_low,
            "ci_high": d_meta.ci_high,
            "notes": "Random-effects meta-analysis of independent-groups Cohen d values by lab; approximate SMD route for Figure 1 review.",
        },
        {
            "summary_id": "article_reported_mean_difference_standardized_by_raw_pooled_sd",
            "candidate_id": CANDIDATE_ID,
            "n_death_no_delay": n_exp,
            "n_all_other": n_ctrl,
            "n_total": n_exp + n_ctrl,
            "mean_death_no_delay": "",
            "sd_death_no_delay": "",
            "mean_all_other": "",
            "sd_all_other": "",
            "effect": article_standardized_by_raw_pooled_sd,
            "effect_scale": "article_mean_difference_0_08_divided_by_recomputed_raw_pooled_sd",
            "raw_mean_difference": article_md,
            "raw_mean_difference_se": "",
            "tau2": "",
            "q": "",
            "k_labs": "",
            "ci_low": "",
            "ci_high": "",
            "notes": "Hybrid sensitivity route: RRR text reports 0.08 more death-related words, 95% CI [0.01, 0.14]; denominator is the participant-pooled SD recomputed from mirrored OSF raw data.",
        },
        {
            "summary_id": "article_table4_lab_random_effects_raw_mean_difference",
            "candidate_id": CANDIDATE_ID,
            "n_death_no_delay": table4_n1,
            "n_all_other": table4_n0,
            "n_total": table4_n1 + table4_n0,
            "mean_death_no_delay": "",
            "sd_death_no_delay": "",
            "mean_all_other": "",
            "sd_all_other": "",
            "effect": table4_md_meta.estimate,
            "effect_scale": "article_table4_death_word_count_mean_difference_random_effects",
            "raw_mean_difference": table4_md_meta.estimate,
            "raw_mean_difference_se": table4_md_meta.se,
            "tau2": table4_md_meta.tau2,
            "q": table4_md_meta.q,
            "k_labs": table4_md_meta.k,
            "ci_low": table4_md_meta.ci_low,
            "ci_high": table4_md_meta.ci_high,
            "notes": "Random-effects meta-analysis of article Table 4 raw means/SDs using focal cell Ns recomputed from mirrored OSF participant CSVs. BYUI is absent because no BYUI main CSV was available in the mirrored data package.",
        },
        {
            "summary_id": "article_table4_lab_random_effects_smd",
            "candidate_id": CANDIDATE_ID,
            "n_death_no_delay": table4_n1,
            "n_all_other": table4_n0,
            "n_total": table4_n1 + table4_n0,
            "mean_death_no_delay": "",
            "sd_death_no_delay": "",
            "mean_all_other": "",
            "sd_all_other": "",
            "effect": table4_d_meta.estimate,
            "effect_scale": "article_table4_cohen_d_random_effects_across_lab_smds",
            "raw_mean_difference": "",
            "raw_mean_difference_se": table4_d_meta.se,
            "tau2": table4_d_meta.tau2,
            "q": table4_d_meta.q,
            "k_labs": table4_d_meta.k,
            "ci_low": table4_d_meta.ci_low,
            "ci_high": table4_d_meta.ci_high,
            "notes": "Random-effects meta-analysis of article Table 4 lab-level SMDs, using focal cell Ns recomputed from mirrored OSF participant CSVs. This is the most direct D-scale reconstruction from source table means/SDs.",
        },
        {
            "summary_id": "article_table4_participant_pooled_smd",
            "candidate_id": CANDIDATE_ID,
            "n_death_no_delay": table4_n1,
            "n_all_other": table4_n0,
            "n_total": table4_n1 + table4_n0,
            "mean_death_no_delay": table4_m1,
            "sd_death_no_delay": table4_sd1,
            "mean_all_other": table4_m0,
            "sd_all_other": table4_sd0,
            "effect": table4_d_pooled,
            "effect_scale": "article_table4_participant_pooled_smd",
            "raw_mean_difference": table4_m1 - table4_m0,
            "raw_mean_difference_se": mean_difference_se(table4_n1, table4_sd1, table4_n0, table4_sd0),
            "tau2": "",
            "q": "",
            "k_labs": len(table4_rows),
            "ci_low": "",
            "ci_high": "",
            "notes": "Participant-pooled SMD reconstructed from article Table 4 means/SDs and focal cell Ns recomputed from mirrored OSF participant CSVs.",
        },
    ]


def build_input_manifest() -> list[dict[str, Any]]:
    paths = sorted(
        [
            *RAW_DIR.glob("*_main.csv"),
            *RAW_DIR.glob("*_coding.csv"),
            *RAW_DIR.glob("*_coding_Completed.csv"),
            *RAW_DIR.glob("CodingSheet_*_completed.csv"),
            *[RAW_DIR / filename for filename in LANGUAGE_LIST_FILES.values()],
            RAW_DIR / "Analyses.R",
            RAW_DIR / "requirements.R",
            RAW_DIR / "README.md",
        ]
    )
    rows = []
    for path in paths:
        if not path.exists():
            continue
        rows.append(
            {
                "candidate_id": CANDIDATE_ID,
                "local_path": str(path.relative_to(ROOT)),
                "sha256": sha256(path),
                "bytes": path.stat().st_size,
            }
        )
    return rows


def write_report(summary_rows: list[dict[str, Any]], lab_rows: list[dict[str, Any]]) -> None:
    by_id = {row["summary_id"]: row for row in summary_rows}
    pooled = by_id["participant_pooled_raw_focal_contrast"]
    md = by_id["lab_random_effects_raw_mean_difference"]
    dmeta = by_id["lab_random_effects_smd"]
    hybrid = by_id["article_reported_mean_difference_standardized_by_raw_pooled_sd"]
    table4_md = by_id["article_table4_lab_random_effects_raw_mean_difference"]
    table4_d = by_id["article_table4_lab_random_effects_smd"]
    table4_pooled = by_id["article_table4_participant_pooled_smd"]
    lines = [
        "# Trafimow/Hughes RRR Auto-Mining Recompute",
        "",
        "This artifact recomputes the exact word-generation replication contrast from the locally mirrored OSF package for Rife et al. (2025), the Registered Replication Report of Study 3 from Trafimow and Hughes (2012).",
        "",
        "## Source Objects",
        "",
        f"- Raw OSF files: `{RAW_DIR.relative_to(ROOT)}`",
        f"- Lab effects TSV: `{LAB_OUT.relative_to(ROOT)}`",
        f"- Summary TSV: `{SUMMARY_OUT.relative_to(ROOT)}`",
        f"- Input manifest TSV: `{INPUTS_OUT.relative_to(ROOT)}`",
        "",
        "## Recomputed Focal Values",
        "",
        f"- Focal analyzed N from mirrored word-generation participant files, excluding METAlab: {pooled['n_total']} ({pooled['n_death_no_delay']} death/no-delay; {pooled['n_all_other']} all other conditions).",
        f"- Participant-pooled raw mean difference: {float(pooled['raw_mean_difference']):.6f} death-related words.",
        f"- Participant-pooled Cohen d: {float(pooled['effect']):.6f}.",
        f"- Lab random-effects raw mean difference: {float(md['effect']):.6f}, SE {float(md['raw_mean_difference_se']):.6f}, 95% CI [{float(md['ci_low']):.6f}, {float(md['ci_high']):.6f}], k = {md['k_labs']}.",
        f"- Lab random-effects Cohen d: {float(dmeta['effect']):.6f}, SE {float(dmeta['raw_mean_difference_se']):.6f}, 95% CI [{float(dmeta['ci_low']):.6f}, {float(dmeta['ci_high']):.6f}], k = {dmeta['k_labs']}.",
        f"- Article reported raw mean difference 0.08 standardized by recomputed participant-pooled SD: d = {float(hybrid['effect']):.6f}.",
        f"- Article Table 4 random-effects raw mean difference using recomputed focal Ns: {float(table4_md['effect']):.6f}, SE {float(table4_md['raw_mean_difference_se']):.6f}, 95% CI [{float(table4_md['ci_low']):.6f}, {float(table4_md['ci_high']):.6f}], k = {table4_md['k_labs']}.",
        f"- Article Table 4 random-effects Cohen d using recomputed focal Ns: {float(table4_d['effect']):.6f}, SE {float(table4_d['raw_mean_difference_se']):.6f}, 95% CI [{float(table4_d['ci_low']):.6f}, {float(table4_d['ci_high']):.6f}], k = {table4_d['k_labs']}.",
        f"- Article Table 4 participant-pooled Cohen d using recomputed focal Ns: {float(table4_pooled['effect']):.6f}.",
        "",
        "## Figure 1 Promotion Status",
        "",
        "This recomputation resolves the local raw-data path but does not by itself choose the final plotted D. The most direct D-scale reconstruction is `article_table4_lab_random_effects_smd`; the more conservative hybrid sensitivity is the article-reported raw mean difference standardized by the recomputed pooled SD.",
        "",
        "## Method Notes",
        "",
        "- The participant filters mirror the downloaded `Analyses.R` plan as closely as possible from the downloaded files: manual exclusion decisions where completed coding files provide them, complete Gender/Age, `Understand == 0`, `interviewtime > 300`, word-generation task only, and METAlab excluded for the exact word-generation replication.",
        "- Blank coding-file decisions are treated as non-exclusions because the downloaded coding files are mostly placeholder exports.",
        "- BYUI appears in the article table but no BYUI main participant CSV was available through the mirrored OSF package, so article-table reconstructions using raw focal Ns exclude BYUI.",
        f"- Lab rows written: {len(lab_rows)}.",
    ]
    REPORT_OUT.parent.mkdir(parents=True, exist_ok=True)
    REPORT_OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    if not RAW_DIR.exists():
        raise FileNotFoundError(f"Missing mirrored OSF directory: {RAW_DIR}")
    death_words = load_death_words()
    analysis = load_analysis_rows(death_words)
    lab_rows = build_lab_effects(analysis)
    summary_rows = build_summary(analysis, lab_rows)
    input_rows = build_input_manifest()

    write_tsv(
        LAB_OUT,
        lab_rows,
        [
            "candidate_id",
            "lab",
            "n_death_no_delay",
            "mean_death_no_delay",
            "sd_death_no_delay",
            "n_all_other",
            "mean_all_other",
            "sd_all_other",
            "mean_difference_death_no_delay_minus_all_other",
            "mean_difference_se",
            "pooled_sd",
            "cohen_d_death_no_delay_minus_all_other",
            "cohen_d_se",
        ],
    )
    write_tsv(
        SUMMARY_OUT,
        summary_rows,
        [
            "summary_id",
            "candidate_id",
            "n_death_no_delay",
            "n_all_other",
            "n_total",
            "mean_death_no_delay",
            "sd_death_no_delay",
            "mean_all_other",
            "sd_all_other",
            "effect",
            "effect_scale",
            "raw_mean_difference",
            "raw_mean_difference_se",
            "tau2",
            "q",
            "k_labs",
            "ci_low",
            "ci_high",
            "notes",
        ],
    )
    write_tsv(INPUTS_OUT, input_rows, ["candidate_id", "local_path", "sha256", "bytes"])
    write_report(summary_rows, lab_rows)
    print(f"Wrote {LAB_OUT.relative_to(ROOT)}")
    print(f"Wrote {SUMMARY_OUT.relative_to(ROOT)}")
    print(f"Wrote {INPUTS_OUT.relative_to(ROOT)}")
    print(f"Wrote {REPORT_OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
