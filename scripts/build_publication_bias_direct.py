#!/usr/bin/env python3
"""Build D/N rows for direct publication-bias denominator datasets.

This intentionally keeps source provenance explicit. A row can be a journal
reported result, a regulatory/FDA result for a published trial, or a
regulatory/FDA result for an unpublished trial. For "published result" counts,
use result_source == "journal".
"""

from __future__ import annotations

import math
import re
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "publication_bias_direct"
DERIVED = ROOT / "data" / "derived" / "publication_bias_direct"
P10_Z = 1.6448536269514722


def as_num(x):
    return pd.to_numeric(pd.Series([x]).replace("*", np.nan), errors="coerce").iloc[0]


def clean_text(x: object) -> str:
    if pd.isna(x):
        return ""
    s = str(x).replace("\xa0", " ").strip().lower()
    s = re.sub(r"\s+", " ", s)
    return s


def normalize_turner_drug(x: object) -> str:
    return re.sub(r"[^a-z0-9]+", "", clean_text(x))


TURNER_TRIAL_ALIASES = {
    "304dvx": "304",
    "317dvx": "317",
    "304vor": "304",
    "317vor": "317",
    "f02695lp202": "f02695lp202",
    "309&317": "309&317",
}


def normalize_turner_trial(x: object) -> str:
    base = clean_text(x)
    compact = re.sub(r"[^a-z0-9&]+", "", base)
    return TURNER_TRIAL_ALIASES.get(compact, compact)


def row(
    *,
    dataset: str,
    study_id: str,
    comparison: str,
    result_source: str,
    trial_publication_status: str,
    n: float,
    estimate: float,
    se: float,
    effect_metric: str,
    row_type: str,
    native_d: float | None = None,
    notes: str = "",
    **extra,
):
    if not (pd.notna(n) and n > 0 and pd.notna(estimate) and pd.notna(se) and se > 0):
        return None
    z = estimate / se
    d_from_z = 2 * abs(z) / math.sqrt(n)
    if native_d is None:
        native_d = abs(estimate)
    if result_source == "journal":
        publication_status = "journal_published"
    elif trial_publication_status == "unpublished":
        publication_status = "regulatory_FDA_unpublished_trial"
    elif result_source.startswith("regulatory"):
        publication_status = "regulatory_FDA_published_trial"
    else:
        publication_status = trial_publication_status
    out = {
        "dataset": dataset,
        "study_id": str(study_id),
        "comparison": comparison,
        "source": result_source,
        "result_source": result_source,
        "publication_status": publication_status,
        "trial_publication_status": trial_publication_status,
        "is_journal_result": result_source == "journal",
        "n": float(n),
        "estimate": float(estimate),
        "se": float(se),
        "z": float(z),
        "d_from_z": float(d_from_z),
        "native_d": float(abs(native_d)),
        "effect_metric": effect_metric,
        "row_type": row_type,
        "notes": notes,
    }
    out.update(extra)
    return out


def build_cipriani() -> list[dict]:
    p = RAW / "cipriani_griselda" / "Cipriani et al_GRISELDA_Lancet 2018_Open data.xlsx"
    df = pd.read_excel(p, header=2)
    df.columns = [str(c).strip() for c in df.columns]
    for c in [
        "No_randomised",
        "Responders",
        "N comp+imputed",
        "Mean.1",
        "SD",
        "N comp+imputed.1",
    ]:
        df[c] = pd.to_numeric(df[c].replace("*", np.nan), errors="coerce")
    df["trial_publication_status"] = np.where(
        df["Year_Published"].astype(str).str.contains("unpublished", case=False, na=False),
        "unpublished",
        "published",
    )

    out = []
    for sid, g in df.groupby("StudyID", dropna=False):
        placebo = g[g["Drug"].astype(str).str.contains(r"\bplacebo\b", case=False, regex=True, na=False)]
        if placebo.empty:
            continue
        pbo = placebo.sort_values("No_randomised", ascending=False).iloc[0]
        for _, arm in g.iterrows():
            drug = str(arm["Drug"])
            if re.search(r"\bplacebo\b", drug, re.I):
                continue
            status = str(arm["trial_publication_status"])

            n1, n0 = arm["No_randomised"], pbo["No_randomised"]
            a, c = arm["Responders"], pbo["Responders"]
            if pd.notna(n1) and pd.notna(n0) and pd.notna(a) and pd.notna(c):
                b, d = n1 - a, n0 - c
                aa, bb, cc, dd = a, b, c, d
                if min(aa, bb, cc, dd) <= 0:
                    aa, bb, cc, dd = aa + 0.5, bb + 0.5, cc + 0.5, dd + 0.5
                logor = math.log((aa * dd) / (bb * cc))
                se = math.sqrt(1 / aa + 1 / bb + 1 / cc + 1 / dd)
                rec = row(
                    dataset="Cipriani_GRISELDA_2018_response",
                    study_id=sid,
                    comparison=f"{drug} vs placebo",
                    result_source="journal_or_unpublished_meta_analysis",
                    trial_publication_status=status,
                    n=n1 + n0,
                    estimate=logor,
                    se=se,
                    native_d=logor / 1.81,
                    effect_metric="logOR_response_to_Chinn_d",
                    row_type="active_arm_vs_placebo",
                )
                if rec:
                    out.append(rec)

            m1, s1, nn1 = arm["Mean.1"], arm["SD"], arm["N comp+imputed.1"]
            m0, s0, nn0 = pbo["Mean.1"], pbo["SD"], pbo["N comp+imputed.1"]
            if all(pd.notna(x) and x > 0 for x in [s1, s0, nn1, nn0]) and pd.notna(m1) and pd.notna(m0):
                sp = math.sqrt(((nn1 - 1) * s1 * s1 + (nn0 - 1) * s0 * s0) / (nn1 + nn0 - 2))
                smd = (m0 - m1) / sp
                se = math.sqrt((nn1 + nn0) / (nn1 * nn0) + (smd * smd) / (2 * (nn1 + nn0 - 2)))
                rec = row(
                    dataset="Cipriani_GRISELDA_2018_continuous",
                    study_id=sid,
                    comparison=f"{drug} vs placebo",
                    result_source="journal_or_unpublished_meta_analysis",
                    trial_publication_status=status,
                    n=nn1 + nn0,
                    estimate=smd,
                    se=se,
                    native_d=smd,
                    effect_metric="SMD_endpoint_drug_benefit_positive",
                    row_type="active_arm_vs_placebo",
                )
                if rec:
                    out.append(rec)
    return out


def build_turner_2022() -> list[dict]:
    s18 = RAW / "turner_2022" / "pmed.1003886.s018"
    s13 = RAW / "turner_2022" / "pmed.1003886.s013"
    meta = pd.read_excel(s13)
    meta = meta[meta["cohort_txt"].astype(str).str.lower().eq("newer")].copy()
    meta["drug_key"] = meta["drug"].map(normalize_turner_drug)
    meta["trial_key"] = meta["trial_num"].map(normalize_turner_trial)

    meta_fields = ["fda_pos_neg", "jo_otcm_w_unpub", "published", "spun", "trial_num"]
    meta_lookup = {
        (r["drug_key"], r["trial_key"]): {k: r.get(k) for k in meta_fields}
        for _, r in meta.iterrows()
    }

    def lookup_turner_meta(drug: object, trial: object) -> tuple[dict, str]:
        drug_key = normalize_turner_drug(drug)
        trial_key = normalize_turner_trial(trial)
        hit = meta_lookup.get((drug_key, trial_key))
        if hit is not None:
            return hit, "exact"
        if "&" in trial_key:
            parts = [p for p in trial_key.split("&") if p]
            part_hits = [meta_lookup.get((drug_key, p)) for p in parts]
            if part_hits and all(h is not None for h in part_hits):
                first = part_hits[0]
                same = all(
                    all((h.get(f) == first.get(f)) or (pd.isna(h.get(f)) and pd.isna(first.get(f))) for f in ["fda_pos_neg", "jo_otcm_w_unpub", "published", "spun"])
                    for h in part_hits[1:]
                )
                if same:
                    merged = dict(first)
                    merged["trial_num"] = "&".join(str(h.get("trial_num")) for h in part_hits)
                    return merged, "combined_exact"
        return {}, "unmatched"

    out = []
    specs = [
        ("FDA data, Broad dose criteria", "regulatory_FDA", "g_corrected", "se_g", "studynumber"),
        ("Journal data, Broad dose crit.", "journal", "g_corr", "se_corr", "study"),
        ("FDA data, Narrow dose criteria", "regulatory_FDA", "g_corrected", "se_g", "study_number"),
        ("Journal data, Narrow criteria", "journal", "g_corr", "se_corr", "study"),
    ]
    for sheet, source, gcol, secol, studycol in specs:
        df = pd.read_excel(s18, sheet_name=sheet)
        sheet_pref = "narrow" if "narrow" in sheet.lower() else "broad"
        for _, r in df.iterrows():
            g = as_num(r.get(gcol))
            se = as_num(r.get(secol))
            n = as_num(r.get("n1n2"))
            meta_row, match_type = lookup_turner_meta(r.get("drug"), r.get(studycol))
            trial_key = normalize_turner_trial(r.get(studycol))
            drug_key = normalize_turner_drug(r.get("drug"))
            study = f"{drug_key}:{trial_key}"
            trial_status = "published"
            if source != "journal":
                published_flag = meta_row.get("published")
                if pd.notna(published_flag):
                    trial_status = "published" if int(published_flag) == 1 else "unpublished"
                else:
                    trial_status = "unknown"
            notes = (
                f"sheet={sheet}; match={match_type}; "
                f"fda_pos_neg={meta_row.get('fda_pos_neg', '')}; "
                f"journal_outcome={meta_row.get('jo_otcm_w_unpub', '')}; "
                f"spun={meta_row.get('spun', '')}"
            )
            rec = row(
                dataset="Turner_2022_newer_antidepressants",
                study_id=study,
                comparison=f"{r.get('drug')} vs placebo",
                result_source=source,
                trial_publication_status=trial_status,
                n=n,
                estimate=g,
                se=se,
                native_d=g,
                effect_metric="Hedges_g",
                row_type=sheet,
                notes=notes,
                study_preference=sheet_pref,
                source_trial_label=str(r.get(studycol)),
                source_publication=str(r.get("publication", "")),
                fda_pos_neg=str(meta_row.get("fda_pos_neg", "")),
                journal_outcome=str(meta_row.get("jo_otcm_w_unpub", "")),
                published_flag=meta_row.get("published"),
                spun_flag=meta_row.get("spun"),
                join_match_type=match_type,
            )
            if rec:
                out.append(rec)
    return out


def parse_stata_metan_table(path: Path, source: str) -> list[dict]:
    rows = []
    drug = None
    for line in path.read_text(errors="ignore").splitlines():
        s = line.strip()
        if not s:
            continue
        if s in {
            "aripiprazole",
            "iloperidone",
            "olanzapine",
            "paliperidone",
            "quetiapine",
            "risp_depot",
            "risperidone",
            "ziprasidone",
        }:
            drug = s
            continue
        m = re.match(r"^(.+?)\s+\|\s+(-?\d+\.\d+)\s+(-?\d+\.\d+)\s+(-?\d+\.\d+)\s+(\d+\.\d+)", s)
        if not m:
            continue
        study, est, lo, hi, weight = m.groups()
        study = re.sub(r"\s+", " ", study.strip())
        if study.startswith("D+L pooled") or study.startswith("Sub-total") or study == "Overall":
            continue
        se = (float(hi) - float(lo)) / (2 * 1.959963984540054)
        rows.append(
            {
                "drug": drug,
                "study": study,
                "estimate": float(est),
                "ci_low": float(lo),
                "ci_high": float(hi),
                "se": se,
                "weight": float(weight),
                "source": source,
            }
        )
    return rows


def build_turner_2012() -> list[dict]:
    """Add D/N rows from Turner 2012 antipsychotics.

    N values are transcribed from article Table 1. They sum FDA-approved study
    drug arms plus placebo and exclude active comparators. The two risperidone
    204 site-split rows do not have N in Table 1, so they are intentionally
    skipped for D/N.
    """

    n_map = {
        "93202": 68,
        "94202": 162,
        "97201": 301,
        "97202": 297,
        "138001": 410,
        "3101": 423,
        "3000 (SCZ and SA)": 232,
        "3004 (SCZ and SA)": 301,
        "3005 (SCZ and SA)": 523,
        "HGAD": 189,
        "HGAP": 98,
        "303": 500,
        "304": 326,
        "305": 479,
        "0001/0008": 280,
        "0006": 106,
        "0013": 254,
        "Ris-USA-121": 283,
        "201": 104,
        "104": 149,
        "106": 131,
        "114": 298,
        "115": 324,
    }
    unpublished = {"93202", "94202", "104", "115"}

    files = [
        (DERIVED / "text_extracts" / "journal.pmed.1001189.s002.txt", "regulatory_FDA"),
        (DERIVED / "text_extracts" / "journal.pmed.1001189.s003.txt", "journal"),
    ]
    out = []
    skipped = []
    for path, source in files:
        for r in parse_stata_metan_table(path, source):
            study = r["study"]
            n = n_map.get(study)
            if n is None:
                skipped.append({**r, "reason": "no_N_in_article_table"})
                continue
            trial_status = "unpublished" if study in unpublished else "published"
            rec = row(
                dataset="Turner_2012_antipsychotics",
                study_id=f"{r['drug']}:{study}",
                comparison=f"{r['drug']} vs placebo",
                result_source=source,
                trial_publication_status=trial_status,
                n=n,
                estimate=r["estimate"],
                se=r["se"],
                native_d=r["estimate"],
                effect_metric="Hedges_g_from_CI",
                row_type="FDA_or_journal_metan_table",
                notes="N transcribed from PLOS article Table 1; active comparators excluded",
            )
            if rec:
                rec["ci_low"] = r["ci_low"]
                rec["ci_high"] = r["ci_high"]
                out.append(rec)
    if skipped:
        pd.DataFrame(skipped).to_csv(DERIVED / "turner_2012_antipsychotics_skipped_rows.csv", index=False)
    return out


def build_roest_2015() -> list[dict]:
    """Add Roest 2015 anxiety-disorder antidepressant trials.

    The public JAMA Psychiatry article does not provide a spreadsheet. Table 1
    gives trial-level N and publication/bias status; the article/supplement
    forest plots give Hedges g and 95% CIs separately for FDA and literature
    sources. Values below are transcribed from those public tables/figures.
    Multi-dose trials count the shared placebo arm once plus approved drug arms,
    matching the paper's stated meta-analysis convention.
    """

    # disorder, study_id, total N, Hedges g, CI low, CI high, publication status
    fda_rows = [
        ("GAD", "MD-05", 252, 0.25, -0.00, 0.50, "published"),
        ("GAD", "MD-06", 281, 0.26, 0.02, 0.50, "published"),
        ("GAD", "MD-07", 307, 0.52, 0.28, 0.76, "published"),
        ("GAD", "641", 368, 0.36, 0.18, 0.54, "published"),
        ("GAD", "642", 324, 0.30, 0.08, 0.52, "published"),
        ("GAD", "637", 364, 0.11, -0.09, 0.31, "unpublished"),
        ("GAD", "HMBR", 507, 0.49, 0.31, 0.67, "published"),
        ("GAD", "HMDT", 319, 0.26, 0.04, 0.48, "published"),
        ("GAD", "HMDU", 307, 0.31, 0.09, 0.53, "published"),
        ("GAD", "210", 349, 0.26, 0.02, 0.50, "published"),
        ("GAD", "214", 272, 0.31, 0.06, 0.56, "published"),
        ("PD", "120", 141, 0.38, 0.05, 0.71, "published"),
        ("PD", "108", 120, 0.44, 0.09, 0.79, "published"),
        ("PD", "187", 246, 0.37, 0.12, 0.62, "published"),
        ("PD", "223", 145, -0.10, -0.43, 0.23, "unpublished"),
        ("PD", "494", 251, 0.37, 0.12, 0.62, "published"),
        ("PD", "495", 259, 0.15, -0.09, 0.39, "published"),
        ("PD", "497", 262, 0.19, -0.05, 0.43, "published"),
        ("PD", "629", 166, 0.49, 0.18, 0.80, "published"),
        ("PD", "630", 176, 0.23, -0.06, 0.52, "published"),
        ("PD", "529", 171, 0.25, -0.10, 0.60, "published"),
        ("PD", "514", 150, 0.18, -0.19, 0.55, "unpublished"),
        ("PD", "398", 469, 0.48, 0.28, 0.68, "published"),
        ("PD", "399", 473, 0.42, 0.22, 0.62, "published"),
        ("PD", "353", 310, 0.22, 0.00, 0.44, "published"),
        ("PD", "391", 328, 0.05, -0.17, 0.27, "published"),
        ("SAD", "3107", 235, 0.56, 0.31, 0.81, "published"),
        ("SAD", "3108", 274, 0.28, 0.04, 0.52, "published"),
        ("SAD", "502", 281, 0.42, 0.18, 0.66, "published"),
        ("SAD", "382", 182, 0.63, 0.34, 0.92, "published"),
        ("SAD", "454", 360, 0.38, 0.14, 0.62, "published"),
        ("SAD", "790", 369, 0.55, 0.33, 0.77, "published"),
        ("SAD", "R-0601", 401, 0.33, 0.13, 0.53, "published"),
        ("SAD", "94-004", 203, 0.49, 0.20, 0.78, "published"),
        ("SAD", "95-003", 387, 0.09, -0.11, 0.29, "published"),
        ("SAD", "387", 271, 0.40, 0.16, 0.64, "published"),
        ("SAD", "393", 261, 0.37, 0.13, 0.61, "published"),
        ("PTSD", "641", 166, -0.08, -0.39, 0.23, "published"),
        ("PTSD", "682", 188, -0.02, -0.31, 0.27, "unpublished"),
        ("PTSD", "640", 202, 0.29, 0.02, 0.56, "published"),
        ("PTSD", "671", 183, 0.36, 0.07, 0.65, "published"),
        ("PTSD", "651", 489, 0.52, 0.32, 0.72, "published"),
        ("PTSD", "648", 269, 0.48, 0.24, 0.72, "published"),
        ("PTSD", "627", 313, 0.24, 0.02, 0.46, "unpublished"),
        ("OCD", "HCEP1", 186, 0.59, 0.26, 0.92, "published"),
        ("OCD", "HCEP2", 163, 0.86, 0.49, 1.23, "published"),
        ("OCD", "E079", 214, 0.25, -0.06, 0.56, "published"),
        ("OCD", "5529", 159, 0.60, 0.29, 0.91, "unpublished"),
        ("OCD", "5534", 155, 0.40, 0.09, 0.71, "published"),
        ("OCD", "3103", 232, 0.44, 0.19, 0.69, "published"),
        ("OCD", "116", 254, 0.43, 0.18, 0.68, "published"),
        ("OCD", "118", 154, 0.14, -0.17, 0.45, "unpublished"),
        ("OCD", "136", 297, 0.30, 0.06, 0.54, "published"),
        ("OCD", "237/248", 87, 0.41, -0.02, 0.84, "published"),
        ("OCD", "371/372", 324, 0.35, 0.10, 0.60, "published"),
        ("OCD", "546", 164, 0.41, 0.10, 0.72, "published"),
        ("OCD", "495", 170, 0.13, -0.16, 0.42, "unpublished"),
    ]

    # disorder, study_id, total N, Hedges g, CI low, CI high
    journal_rows = [
        ("GAD", "MD-05", 252, 0.28, 0.03, 0.53),
        ("GAD", "MD-06", 281, 0.27, 0.03, 0.51),
        ("GAD", "MD-07", 307, 0.52, 0.28, 0.76),
        ("GAD", "641", 368, 0.35, 0.17, 0.53),
        ("GAD", "642", 324, 0.30, 0.08, 0.52),
        ("GAD", "HMBR", 507, 0.48, 0.30, 0.66),
        ("GAD", "HMDT", 319, 0.25, 0.03, 0.47),
        ("GAD", "HMDU", 307, 0.30, 0.08, 0.52),
        ("GAD", "210", 349, 0.26, 0.02, 0.50),
        ("GAD", "214", 272, 0.31, 0.06, 0.56),
        ("PD", "120", 141, 0.84, 0.43, 1.25),
        ("PD", "108", 120, 0.45, 0.06, 0.84),
        ("PD", "187", 246, 0.40, 0.15, 0.65),
        ("PD", "494/495/497", 772, 0.20, 0.06, 0.34),
        ("PD", "629", 166, 0.34, 0.03, 0.65),
        ("PD", "630", 176, 0.39, 0.10, 0.68),
        ("PD", "529", 171, 0.55, 0.20, 0.90),
        ("PD", "398", 469, 0.45, 0.25, 0.65),
        ("PD", "399", 473, 0.40, 0.20, 0.60),
        ("PD", "353", 310, 0.18, -0.04, 0.40),
        ("PD", "391", 328, 0.05, -0.17, 0.27),
        ("SAD", "3107", 235, 0.58, 0.33, 0.83),
        ("SAD", "3108", 274, 0.27, 0.03, 0.51),
        ("SAD", "502", 281, 0.42, 0.18, 0.66),
        ("SAD", "382", 182, 0.63, 0.34, 0.92),
        ("SAD", "454", 360, 0.39, 0.15, 0.63),
        ("SAD", "790", 369, 0.55, 0.33, 0.77),
        ("SAD", "R-0601", 401, 0.33, 0.13, 0.53),
        ("SAD", "94-004", 203, 0.45, 0.16, 0.74),
        ("SAD", "95-003", 387, 0.38, 0.16, 0.60),
        ("SAD", "387", 271, 0.40, 0.16, 0.64),
        ("SAD", "393", 261, 0.37, 0.13, 0.61),
        ("PTSD", "641", 166, -0.08, -0.39, 0.23),
        ("PTSD", "640", 202, 0.29, 0.02, 0.56),
        ("PTSD", "671", 183, 0.35, 0.06, 0.64),
        ("PTSD", "651", 489, 0.49, 0.31, 0.67),
        ("PTSD", "648", 269, 0.42, 0.18, 0.66),
        ("OCD", "HCEP1/HCEP2", 349, 0.76, 0.51, 1.01),
        ("OCD", "E079", 214, 0.25, -0.06, 0.56),
        ("OCD", "5534", 155, 0.40, 0.09, 0.71),
        ("OCD", "3103", 232, 0.43, 0.18, 0.68),
        ("OCD", "116", 254, 0.61, 0.32, 0.90),
        ("OCD", "136", 297, 0.38, 0.14, 0.62),
        ("OCD", "237/248", 87, 0.42, -0.01, 0.85),
        ("OCD", "371/372", 324, 0.35, 0.10, 0.60),
        ("OCD", "546", 164, 0.42, 0.11, 0.73),
    ]

    out = []
    note = "N/status transcribed from JAMA Psychiatry Table 1; effects from public forest plots"
    for disorder, study, n, est, lo, hi, status in fda_rows:
        se = (hi - lo) / (2 * 1.959963984540054)
        rec = row(
            dataset="Roest_2015_anxiety_antidepressants",
            study_id=f"{disorder}:{study}",
            comparison=f"{disorder} antidepressant vs placebo",
            result_source="regulatory_FDA",
            trial_publication_status=status,
            n=n,
            estimate=est,
            se=se,
            native_d=est,
            effect_metric="Hedges_g_from_CI",
            row_type="FDA_forest_plot",
            notes=note,
        )
        if rec:
            rec["ci_low"] = lo
            rec["ci_high"] = hi
            out.append(rec)
    for disorder, study, n, est, lo, hi in journal_rows:
        se = (hi - lo) / (2 * 1.959963984540054)
        rec = row(
            dataset="Roest_2015_anxiety_antidepressants",
            study_id=f"{disorder}:{study}",
            comparison=f"{disorder} antidepressant vs placebo",
            result_source="journal",
            trial_publication_status="published",
            n=n,
            estimate=est,
            se=se,
            native_d=est,
            effect_metric="Hedges_g_from_CI",
            row_type="journal_forest_plot",
            notes=note,
        )
        if rec:
            rec["ci_low"] = lo
            rec["ci_high"] = hi
            out.append(rec)
    return out


def build_amarilyo_2016() -> list[dict]:
    """Add paired FDA-vs-publication RA biologics rows from Amarilyyo 2016.

    The public PLOS ONE workbook exposes 2x2 efficacy and withdrawal counts for
    FDA reports and matched journal publications. Trial publication status is
    inferred conservatively at the study-ID level: if any row for that study has
    publication counts in either sheet, the study is treated as published;
    otherwise it is treated as unpublished.
    """

    path = RAW / "amarilyo_2016" / "pone.0147556.s001.xlsx"
    if not path.exists():
        return []

    def normalize_study_id(x: object) -> str:
        return str(x).replace("\xa0", " ").strip()

    def log_or_row(a: float, n1: float, c: float, n0: float) -> tuple[float, float]:
        b = n1 - a
        d = n0 - c
        aa, bb, cc, dd = a, b, c, d
        if min(aa, bb, cc, dd) <= 0:
            aa, bb, cc, dd = aa + 0.5, bb + 0.5, cc + 0.5, dd + 0.5
        log_or = math.log((aa * dd) / (bb * cc))
        se = math.sqrt(1 / aa + 1 / bb + 1 / cc + 1 / dd)
        return log_or, se

    sheet_specs = {
        "ACR20": {
            "outcome": "ACR20 response",
            "benefit_direction": "higher_is_better",
            "fda_cols": (
                "events bio \nFDA\nACR20",
                "N bio \nFDA\nACR20",
                "events placebo \nFDA\nACR20",
                "N placebo\n FDA\nACR20",
            ),
            "pub_cols": (
                "events bio \npub.\nACR20",
                "N bio \npub.\nACR20",
                "events placebo \npub.\nACR20",
                "N placebo \npub.\nACR20",
            ),
        },
        "WdAE": {
            "outcome": "withdrawal due to adverse events",
            "benefit_direction": "lower_is_better",
            "fda_cols": (
                "events bio \nFDA\nWdAE",
                "N bio \nFDA\nWdAE",
                "events placebo \nFDA\nWdAE",
                "N placebo\n FDA\nWdAE",
            ),
            "pub_cols": (
                "events bio \npub.\nWdAE",
                "N bio \npub.\nWdAE",
                "events placebo \npub.\nWdAE",
                "N placebo \npub.\nWdAE",
            ),
        },
    }

    trial_pub_status: dict[str, str] = {}
    for sheet, spec in sheet_specs.items():
        df = pd.read_excel(path, sheet_name=sheet)
        pub_cols = list(spec["pub_cols"])
        has_pub = df[pub_cols].notna().all(axis=1)
        study_ids = df["Company \nStudy ID"].map(normalize_study_id)
        for sid, value in zip(study_ids, has_pub, strict=False):
            trial_pub_status[sid] = "published" if value or trial_pub_status.get(sid) == "published" else "unpublished"

    out = []
    for sheet, spec in sheet_specs.items():
        df = pd.read_excel(path, sheet_name=sheet).copy()
        df["study_id_clean"] = df["Company \nStudy ID"].map(normalize_study_id)
        for prefix, source, cols in [
            ("fda", "regulatory_FDA", spec["fda_cols"]),
            ("pub", "journal", spec["pub_cols"]),
        ]:
            ev_treat, n_treat, ev_ctrl, n_ctrl = cols
            counts = df[[ev_treat, n_treat, ev_ctrl, n_ctrl]].apply(pd.to_numeric, errors="coerce")
            ok = counts.notna().all(axis=1)
            for idx in df.index[ok]:
                a = float(counts.at[idx, ev_treat])
                n1 = float(counts.at[idx, n_treat])
                c = float(counts.at[idx, ev_ctrl])
                n0 = float(counts.at[idx, n_ctrl])
                if min(n1, n0) <= 0 or a < 0 or c < 0 or a > n1 or c > n0:
                    continue
                estimate, se = log_or_row(a, n1, c, n0)
                sid = df.at[idx, "study_id_clean"]
                trial_status = "published" if source == "journal" else trial_pub_status.get(sid, "unpublished")
                drug = str(df.at[idx, "Drug"]).strip()
                dose = str(df.at[idx, "DRUG/dose"]).strip()
                outcome = spec["outcome"]
                comparison = f"{drug} {dose} vs placebo"
                notes = (
                    f"sheet={sheet}; benefit_direction={spec['benefit_direction']}; "
                    f"company_study_id={sid}; source={prefix}"
                )
                rec = row(
                    dataset="Amarilyo_2016_RA_biologics",
                    study_id=f"{sid}:{dose}:{sheet}",
                    comparison=comparison,
                    result_source=source,
                    trial_publication_status=trial_status,
                    n=n1 + n0,
                    estimate=estimate,
                    se=se,
                    native_d=estimate * math.sqrt(3) / math.pi,
                    effect_metric="logOR_to_Chinn_d",
                    row_type=f"{sheet}_{prefix}_counts",
                    notes=notes,
                    outcome=outcome,
                    company_study_id=sid,
                    drug=drug,
                    dose=dose,
                    events_treat=a,
                    n_treat=n1,
                    events_control=c,
                    n_control=n0,
                )
                if rec:
                    out.append(rec)
    return out


def summarize(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (dataset, source, status), g in df.groupby(["dataset", "result_source", "trial_publication_status"]):
        gg = g.dropna(subset=["n", "d_from_z", "z"])
        gg = gg[(gg["n"] > 0) & (gg["d_from_z"] > 0)]
        slope = np.nan
        if len(gg) >= 5 and gg["n"].nunique() > 1:
            slope = np.polyfit(np.log10(gg["n"]), np.log10(gg["d_from_z"]), 1)[0]
        rows.append(
            {
                "dataset": dataset,
                "result_source": source,
                "trial_publication_status": status,
                "rows": len(gg),
                "studies": gg["study_id"].nunique(),
                "median_n": gg["n"].median(),
                "median_d": gg["d_from_z"].median(),
                "pct_above_p10": (gg["z"].abs() >= P10_Z).mean() * 100 if len(gg) else np.nan,
                "slope": slope,
            }
        )
    return pd.DataFrame(rows).sort_values(["dataset", "result_source", "trial_publication_status"])


def collapse_preferred_rows(df: pd.DataFrame) -> pd.DataFrame:
    data = df.copy()
    data["selection_priority"] = 1
    turner_mask = data["dataset"].eq("Turner_2022_newer_antidepressants")
    data.loc[turner_mask & data["study_preference"].astype(str).str.lower().eq("broad"), "selection_priority"] = 1
    data.loc[turner_mask & data["study_preference"].astype(str).str.lower().eq("narrow"), "selection_priority"] = 2
    data["abs_z"] = data["z"].abs()
    data["collapse_group_rows"] = data.groupby(
        ["dataset", "study_id", "result_source", "trial_publication_status"], dropna=False
    )["study_id"].transform("size")
    data = data.sort_values(
        [
            "dataset",
            "study_id",
            "result_source",
            "trial_publication_status",
            "selection_priority",
            "n",
            "abs_z",
            "comparison",
        ],
        ascending=[True, True, True, True, False, False, True, True],
    )
    collapsed = data.groupby(
        ["dataset", "study_id", "result_source", "trial_publication_status"], dropna=False, as_index=False
    ).head(1).copy()
    collapsed["collapse_rule"] = np.where(
        collapsed["dataset"].eq("Turner_2022_newer_antidepressants"),
        "prefer_narrow_then_larger_n_then_smaller_abs_z",
        "prefer_larger_n_then_smaller_abs_z",
    )
    return collapsed.drop(columns=["selection_priority", "abs_z"])


def main() -> None:
    DERIVED.mkdir(parents=True, exist_ok=True)
    rows = []
    rows.extend(build_cipriani())
    rows.extend(build_turner_2022())
    rows.extend(build_turner_2012())
    rows.extend(build_roest_2015())
    rows.extend(build_amarilyo_2016())
    df = pd.DataFrame(rows)
    for c in df.select_dtypes("object").columns:
        df[c] = df[c].astype(str)
    df.to_csv(DERIVED / "direct_publication_bias_d_ready_rows.csv", index=False)
    df.to_parquet(DERIVED / "direct_publication_bias_d_ready_rows.parquet", index=False)
    summary = summarize(df)
    summary.to_csv(DERIVED / "direct_publication_bias_summary.csv", index=False)
    collapsed = collapse_preferred_rows(df)
    collapsed.to_csv(DERIVED / "direct_publication_bias_study_collapsed_rows.csv", index=False)
    collapsed.to_parquet(DERIVED / "direct_publication_bias_study_collapsed_rows.parquet", index=False)
    collapsed_summary = summarize(collapsed)
    collapsed_summary.to_csv(DERIVED / "direct_publication_bias_study_collapsed_summary.csv", index=False)
    print(summary.round(3).to_string(index=False))
    print(f"\nwrote {len(df)} raw rows")
    print(f"wrote {len(collapsed)} collapsed study-level rows")


if __name__ == "__main__":
    main()
