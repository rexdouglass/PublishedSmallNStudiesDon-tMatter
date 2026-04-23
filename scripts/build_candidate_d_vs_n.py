#!/usr/bin/env python3
"""Normalize acquired candidate corpora into D-vs-N analysis files.

The output is intentionally conservative. It keeps row-level results for every
corpus where D and N can be derived, then marks which rows are plausible
published-original-paper evidence versus registry, replication, or meta-analysis
comparators.
"""

from __future__ import annotations

import argparse
import csv
import math
import re
import subprocess
from pathlib import Path
from typing import Callable

import numpy as np
import pandas as pd
from scipy import stats
from scipy.io import loadmat

try:
    import pyreadstat
except ImportError:  # pragma: no cover - optional local dependency
    pyreadstat = None


ROOT = Path(__file__).resolve().parents[1]


COMMON_COLUMNS = [
    "source_corpus",
    "field",
    "source_kind",
    "published_scope",
    "published_original_candidate",
    "comparator_only",
    "row_id",
    "paper_id",
    "study_id",
    "title",
    "journal",
    "year",
    "outcome",
    "effect_type",
    "effect",
    "se",
    "z",
    "abs_z",
    "N",
    "D",
    "abs_D",
    "D_method",
    "N_method",
    "main_result_flag",
    "published_flag",
    "raw_file",
    "notes",
]


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def to_num(x: object) -> float:
    if pd.isna(x):
        return np.nan
    if isinstance(x, (int, float, np.number)):
        return float(x)
    text = str(x).strip()
    if not text or text.lower() in {"nan", "nr", "na", "n/a", "none", "missing", "[redacted]"}:
        return np.nan
    text = text.replace(",", "")
    match = re.search(r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?", text)
    return float(match.group(0)) if match else np.nan


def numeric(series: pd.Series) -> pd.Series:
    return series.map(to_num)


def sum_sample_size_text(value: object) -> float:
    """Sum all integer-looking sample-size counts in a text field."""
    if pd.isna(value):
        return np.nan
    text = str(value)
    nums = [int(n.replace(",", "")) for n in re.findall(r"\b\d[\d,]*\b", text)]
    if not nums:
        return np.nan
    # Drop obvious years. This field is usually a list of ancestry counts; years
    # occasionally appear in prose but should not dominate the sum.
    filtered = [n for n in nums if not (1800 <= n <= 2100)]
    return float(sum(filtered or nums))


def p_to_abs_z(p: pd.Series, pvalue_mlog: pd.Series | None = None) -> pd.Series:
    p_num = pd.to_numeric(p, errors="coerce")
    out = pd.Series(np.nan, index=p.index, dtype=float)
    finite = p_num.gt(0) & p_num.lt(1)
    out.loc[finite] = stats.norm.isf(p_num.loc[finite] / 2)

    if pvalue_mlog is not None:
        mlog = pd.to_numeric(pvalue_mlog, errors="coerce")
        need = out.isna() & mlog.gt(0)
        moderate = need & mlog.le(300)
        out.loc[moderate] = stats.norm.isf(np.power(10.0, -mlog.loc[moderate]) / 2)
        extreme = need & mlog.gt(300)
        # Leading-order normal tail inversion. It is plenty accurate for a
        # plotting proxy and avoids underflow for GWAS-scale p-values.
        out.loc[extreme] = np.sqrt(2 * np.log(10) * mlog.loc[extreme])
    return out


def scalar_p_to_abs_z(p: float, tails: object = None) -> float:
    if not np.isfinite(p) or p <= 0 or p >= 1:
        return np.nan
    tails_text = str(tails or "").lower()
    if "one" in tails_text or tails_text.strip() == "1":
        return float(stats.norm.isf(p))
    return float(stats.norm.isf(p / 2))


def parse_p_scalar(value: object, p_type: object = None) -> tuple[float, str]:
    """Return a usable p-value and operator. Greater-than p-values are not usable."""
    text = "" if pd.isna(value) else str(value)
    ptype = "" if pd.isna(p_type) else str(p_type).lower()
    text = text.replace("≤", "<=").replace("≥", ">=").replace("−", "-")
    op = ""
    number = np.nan
    match = re.search(
        r"(?i)\bp(?:\s*[- ]?\s*value)?\s*(<=|>=|<|>|=)?\s*([.]?\d+(?:\.\d+)?(?:e[-+]?\d+)?)",
        text,
    )
    if not match:
        stripped = text.strip()
        match = re.fullmatch(r"(<=|>=|<|>|=)?\s*([.]?\d+(?:\.\d+)?(?:e[-+]?\d+)?)", stripped)
    if match:
        op = match.group(1) or ""
        number = to_num(match.group(2))
    if not np.isfinite(number):
        return np.nan, ""
    if "less" in ptype or "l (<" in ptype or ptype.strip() in {"<", "le", "le (<=)", "threshold"}:
        op = "<"
    if "greater" in ptype or "g (>" in ptype or ptype.strip() in {">", ">=", "ge", "ge (>=)"}:
        return np.nan, "greater_than_unusable"
    if op in {">", ">="}:
        return np.nan, "greater_than_unusable"
    if number == 0:
        number = 1e-16
    if number >= 1:
        return np.nan, ""
    return float(number), op or ("=" if "exact" in ptype or "e (=" in ptype else "")


def extract_main_n(value: object) -> float:
    """Extract an analytic sample size from free text without summing years/waves."""
    if pd.isna(value):
        return np.nan
    text = str(value).replace("\u00a0", " ")
    patterns = [
        r"(?i)\bN\s*[=:]\s*([0-9][0-9,]*)\b",
        r"(?i)\bobservations?\s*[=:]\s*([0-9][0-9,]*)\b",
        r"(?i)\btotal\s+of\s+([0-9][0-9,]*)\s+observations?\b",
        r"(?i)\b([0-9][0-9,]*)\s+(?:participants?|subjects?|students?|children|respondents?|firms?|trials?|patients?|observations?|cases?|schools?|counties|countries|households?)\b",
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            n = to_num(match.group(1))
            if np.isfinite(n) and n >= 4:
                return n
    nums = [int(x.replace(",", "")) for x in re.findall(r"\b[0-9][0-9,]*\b", text)]
    nums = [x for x in nums if x >= 4 and not (1800 <= x <= 2100)]
    return float(max(nums)) if nums else np.nan


def normalize_ascii_stat_text(value: object) -> str:
    """Repair common mojibake and normalize stats text into parseable ASCII."""
    if pd.isna(value):
        return ""
    s = str(value)
    replacements = {
        "≤": "<=",
        "≥": ">=",
        "−": "-",
        "–": "-",
        "—": "-",
        "β": "beta",
        "Β": "beta",
        "η": "eta",
        "χ": "chi",
        "Χ": "chi",
        "α": "alpha",
        "²": "2",
        "’": "'",
        "‘": "'",
        "“": '"',
        "”": '"',
    }
    for old, new in replacements.items():
        s = s.replace(old, new)
    try:
        repaired = s.encode("latin1").decode("utf-8")
        s = repaired
        for old, new in replacements.items():
            s = s.replace(old, new)
    except Exception:
        pass
    s = s.encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", s).strip()


def r_to_d_scalar(r: float) -> float:
    if not np.isfinite(r) or abs(r) >= 0.999999:
        return np.nan
    return float(2 * abs(r) / math.sqrt(1 - r**2))


def ratio_to_d_scalar(ratio: float) -> float:
    if not np.isfinite(ratio) or ratio <= 0:
        return np.nan
    return float(abs(math.log(ratio)) * math.sqrt(3) / math.pi)


def effect_type_value_to_d(effect_type: object, effect_value: object) -> tuple[float, str, str]:
    etype = "" if pd.isna(effect_type) else str(effect_type).lower()
    value = to_num(effect_value)
    if not np.isfinite(value):
        return np.nan, "", ""
    if any(key in etype for key in ["cohen_d", "cohen's d", "cohens d", "hedges", "smd"]) or etype.strip() in {"d", "dz", "cohen d", "cohen's d"}:
        return abs(value), "standardized_mean_difference", "reported_d_or_g"
    if any(key in etype for key in ["pearson", "partial r", "part_cor", "correlation", "spearman", "rank_bis", "point-bis", "phi", "cramer"]):
        d = r_to_d_scalar(value)
        return d, "correlation_converted_to_d", "r_like_to_d"
    if any(key in etype for key in ["eta_squared", "etasq", "eta-squared", "omega squared"]):
        if 0 <= value < 1:
            return r_to_d_scalar(math.sqrt(value)), "variance_explained_converted_to_d", "eta_squared_to_r_to_d"
    if any(key in etype for key in ["odds_ratio", "hazard_ratio", "relative_risk", "risk_ratio", "incidence_rate_ratio"]) or etype.strip() in {"or", "hr", "rr"}:
        return ratio_to_d_scalar(value), "ratio_converted_to_d", "log_ratio_times_sqrt3_over_pi"
    return np.nan, "", ""


def parse_stat_text_to_d(text: object, n: float = np.nan) -> tuple[float, float, str, str]:
    """Parse common test-statistic strings into D, z, effect_type, D_method."""
    if pd.isna(text):
        return np.nan, np.nan, "", ""
    raw = str(text)
    s = raw.replace("−", "-").replace("–", "-").replace("—", "-")
    num = r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:e[-+]?\d+)?"

    # Direct standardized effects first.
    for pattern, effect_type, method in [
        (rf"(?i)(?:cohen'?s\s*)?\bdz?\b\s*(?:=|:)\s*({num})", "standardized_mean_difference", "reported_d_or_dz"),
        (rf"(?i)\bhedges'?s?\s*g\s*(?:=|:)\s*({num})", "standardized_mean_difference", "reported_hedges_g"),
        (rf"(?i)\b(?:smd|standardized mean difference)\b\s*(?:=|:)\s*({num})", "standardized_mean_difference", "reported_smd"),
    ]:
        match = re.search(pattern, s)
        if match:
            return abs(to_num(match.group(1))), np.nan, effect_type, method

    for pattern in [
        rf"(?i)\b(?:pearson'?s\s*)?r\s*(?:=|:)\s*({num})",
        rf"(?i)\bcorrelation(?: coefficient)?\s*(?:=|:)\s*({num})",
    ]:
        match = re.search(pattern, s)
        if match:
            d = r_to_d_scalar(to_num(match.group(1)))
            return d, np.nan, "correlation_converted_to_d", "r_to_d"

    for pattern, label in [
        (rf"(?i)\b(?:odds ratio|OR)\s*(?:=|:)\s*({num})", "odds_ratio_converted_to_d"),
        (rf"(?i)\b(?:hazard ratio|HR)\s*(?:=|:)\s*({num})", "hazard_ratio_converted_to_d"),
        (rf"(?i)\b(?:risk ratio|relative risk|RR)\s*(?:=|:)\s*({num})", "risk_ratio_converted_to_d"),
    ]:
        match = re.search(pattern, s)
        if match:
            d = ratio_to_d_scalar(to_num(match.group(1)))
            return d, np.nan, label, "log_ratio_times_sqrt3_over_pi"

    match = re.search(rf"(?i)\bt\s*\(\s*({num})\s*\)\s*(?:=|:)?\s*({num})", s)
    if match:
        dfree = to_num(match.group(1))
        t = to_num(match.group(2))
        if np.isfinite(dfree) and dfree > 0 and np.isfinite(t):
            return float(2 * abs(t) / math.sqrt(dfree)), t, "t_statistic_derived_d", "2_abs_t_over_sqrt_df"

    match = re.search(rf"(?i)\bF\s*\(\s*({num})\s*,\s*({num})\s*\)\s*(?:=|:)?\s*({num})", s)
    if match:
        df1 = to_num(match.group(1))
        df2 = to_num(match.group(2))
        fval = to_num(match.group(3))
        if np.isfinite(df1) and abs(df1 - 1) < 1e-9 and np.isfinite(df2) and df2 > 0 and np.isfinite(fval) and fval >= 0:
            return float(2 * math.sqrt(fval / df2)), math.sqrt(fval), "f1_statistic_derived_d", "2_sqrt_f_over_df2"

    match = re.search(rf"(?i)\b(?:z|Z)\s*(?:=|:)\s*({num})", s)
    if match and np.isfinite(n) and n > 0:
        z = to_num(match.group(1))
        if np.isfinite(z):
            return float(2 * abs(z) / math.sqrt(n)), z, "z_statistic_derived_d_proxy", "2_abs_z_over_sqrtN"

    match = re.search(rf"(?i)(?:coef(?:ficient)?|beta|b)\s*(?:=|:)\s*({num}).{{0,80}}?(?:se|s\.e\.|standard error)\s*(?:=|:)?\s*({num})", s)
    if match and np.isfinite(n) and n > 0:
        coef = to_num(match.group(1))
        se = to_num(match.group(2))
        if np.isfinite(coef) and np.isfinite(se) and se > 0:
            z = coef / se
            return float(2 * abs(z) / math.sqrt(n)), z, "coef_se_derived_d_proxy", "coef_over_se_to_2absz_sqrtN"

    return np.nan, np.nan, "", ""


def p_to_d_proxy_from_text(p_value: object, n: float, p_type: object = None, tails: object = None) -> tuple[float, float, str]:
    if not np.isfinite(n) or n <= 0:
        return np.nan, np.nan, ""
    p, op = parse_p_scalar(p_value, p_type)
    if not np.isfinite(p):
        return np.nan, np.nan, ""
    z = scalar_p_to_abs_z(p, tails)
    if not np.isfinite(z):
        return np.nan, np.nan, ""
    method = "p_value_to_2absz_sqrtN"
    if op in {"<", "<="} or "less" in str(p_type).lower():
        method = "p_value_threshold_lower_bound_to_2absz_sqrtN"
    return float(2 * z / math.sqrt(n)), z, method


def finalize(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for col in COMMON_COLUMNS:
        if col not in out.columns:
            out[col] = np.nan
    out["effect"] = pd.to_numeric(out["effect"], errors="coerce")
    out["se"] = pd.to_numeric(out["se"], errors="coerce")
    out["z"] = pd.to_numeric(out["z"], errors="coerce")
    out["N"] = pd.to_numeric(out["N"], errors="coerce")
    out["D"] = pd.to_numeric(out["D"], errors="coerce")
    out.loc[out["abs_z"].isna(), "abs_z"] = out["z"].abs()
    out.loc[out["abs_D"].isna(), "abs_D"] = out["D"].abs()
    out["year"] = pd.to_numeric(out["year"], errors="coerce")
    out["published_original_candidate"] = out["published_original_candidate"].fillna(False).astype(bool)
    out["comparator_only"] = out["comparator_only"].fillna(False).astype(bool)
    valid = (
        out["N"].gt(0)
        & out["D"].notna()
        & np.isfinite(out["D"])
        & out["D"].abs().gt(0)
        & out["D"].abs().le(100)
        & out["N"].le(1_000_000_000)
    )
    out = out.loc[valid, COMMON_COLUMNS].copy()
    for col in [
        "source_corpus",
        "field",
        "source_kind",
        "published_scope",
        "row_id",
        "paper_id",
        "study_id",
        "title",
        "journal",
        "outcome",
        "effect_type",
        "D_method",
        "N_method",
        "main_result_flag",
        "published_flag",
        "raw_file",
        "notes",
    ]:
        out[col] = out[col].fillna("").astype(str)
    return out


def combine_binary_yun(df: pd.DataFrame, path: Path) -> pd.DataFrame:
    d = df[df["outcome_type"].astype(str).str.lower().eq("binary")].copy()
    for col in [
        "intervention_events",
        "intervention_group_size",
        "comparator_events",
        "comparator_group_size",
    ]:
        d[col] = numeric(d[col])
    a = d["intervention_events"]
    n1 = d["intervention_group_size"]
    c = d["comparator_events"]
    n0 = d["comparator_group_size"]
    b = n1 - a
    dd = n0 - c
    ok = n1.gt(0) & n0.gt(0) & a.ge(0) & c.ge(0) & b.ge(0) & dd.ge(0)
    d = d.loc[ok].copy()
    a = d["intervention_events"]
    n1 = d["intervention_group_size"]
    c = d["comparator_events"]
    n0 = d["comparator_group_size"]
    b = n1 - a
    dd = n0 - c
    zero = (a == 0) | (b == 0) | (c == 0) | (dd == 0)
    a = a + zero * 0.5
    b = b + zero * 0.5
    c = c + zero * 0.5
    dd = dd + zero * 0.5
    log_or = np.log((a * dd) / (b * c))
    se = np.sqrt(1 / a + 1 / b + 1 / c + 1 / dd)
    z = log_or / se
    N = n1 + n0
    D = 2 * z.abs() / np.sqrt(N)
    return pd.DataFrame(
        {
            "source_corpus": "yun_llm_meta_analysis",
            "field": "medicine_rct",
            "source_kind": "published_original_rct_fulltext",
            "published_scope": "published_pmc_rct",
            "published_original_candidate": True,
            "comparator_only": False,
            "row_id": "yun_" + d["id"].astype(str),
            "paper_id": "PMCID:" + d["pmcid"].astype(str),
            "study_id": "PMCID:" + d["pmcid"].astype(str),
            "title": "",
            "journal": "",
            "year": np.nan,
            "outcome": d["outcome"],
            "effect_type": "log_odds_ratio",
            "effect": log_or,
            "se": se,
            "z": z,
            "N": N,
            "D": D,
            "D_method": "binary_log_or_z_to_2absz_sqrtN",
            "N_method": "two_arm_group_sizes",
            "main_result_flag": "ico_row_not_primary_flagged",
            "published_flag": "published",
            "raw_file": str(path),
            "notes": "continuity correction 0.5 only when a 2x2 cell is zero",
        }
    )


def combine_continuous_yun(df: pd.DataFrame, path: Path) -> pd.DataFrame:
    d = df[df["outcome_type"].astype(str).str.lower().eq("continuous")].copy()
    for col in [
        "intervention_group_size",
        "comparator_group_size",
        "intervention_mean",
        "intervention_standard_deviation",
        "comparator_mean",
        "comparator_standard_deviation",
    ]:
        d[col] = numeric(d[col])
    n1 = d["intervention_group_size"]
    n0 = d["comparator_group_size"]
    sd1 = d["intervention_standard_deviation"]
    sd0 = d["comparator_standard_deviation"]
    ok = n1.gt(1) & n0.gt(1) & sd1.gt(0) & sd0.gt(0)
    d = d.loc[ok].copy()
    n1 = d["intervention_group_size"]
    n0 = d["comparator_group_size"]
    N = n1 + n0
    pooled = np.sqrt(((n1 - 1) * d["intervention_standard_deviation"] ** 2 + (n0 - 1) * d["comparator_standard_deviation"] ** 2) / (N - 2))
    smd = (d["intervention_mean"] - d["comparator_mean"]) / pooled
    se = np.sqrt(N / (n1 * n0) + (smd**2) / (2 * (N - 2)))
    z = smd / se
    return pd.DataFrame(
        {
            "source_corpus": "yun_llm_meta_analysis",
            "field": "medicine_rct",
            "source_kind": "published_original_rct_fulltext",
            "published_scope": "published_pmc_rct",
            "published_original_candidate": True,
            "comparator_only": False,
            "row_id": "yun_" + d["id"].astype(str),
            "paper_id": "PMCID:" + d["pmcid"].astype(str),
            "study_id": "PMCID:" + d["pmcid"].astype(str),
            "title": "",
            "journal": "",
            "year": np.nan,
            "outcome": d["outcome"],
            "effect_type": "standardized_mean_difference",
            "effect": smd,
            "se": se,
            "z": z,
            "N": N,
            "D": smd.abs(),
            "D_method": "continuous_two_arm_smd",
            "N_method": "two_arm_group_sizes",
            "main_result_flag": "ico_row_not_primary_flagged",
            "published_flag": "published",
            "raw_file": str(path),
            "notes": "",
        }
    )


def build_yun(raw_dir: Path) -> pd.DataFrame:
    path = raw_dir / "yun_llm_meta_analysis/llm-meta-analysis/evaluation/data/annotated_rct_dataset.csv"
    if not path.exists():
        return pd.DataFrame()
    df = pd.read_csv(path)
    return finalize(pd.concat([combine_binary_yun(df, path), combine_continuous_yun(df, path)], ignore_index=True))


def build_clinifact_published_primary_pairs(_: Path) -> pd.DataFrame:
    path = ROOT / "data/derived/publication_bias_direct/clinifact_publication_registry_pairs.csv"
    if not path.exists():
        return pd.DataFrame()

    d = pd.read_csv(path, low_memory=False)
    d = d[
        d["publication_link_plausibility"].astype(str).eq("plausible_result_report")
        & d["pair_quality"].astype(str).isin(["high", "medium"])
    ].copy()

    if d.empty:
        return pd.DataFrame()

    d["journal_n_preferred"] = numeric(d["journal_n_preferred"])
    d["journal_d_proxy_preferred"] = numeric(d["journal_d_proxy_preferred"])
    d["journal_abs_z_from_p"] = numeric(d["journal_abs_z_from_p"])
    d["selected_sentence_score"] = numeric(d.get("selected_sentence_score", pd.Series(index=d.index))).fillna(0)
    d["combined_match_score"] = numeric(d.get("combined_match_score", pd.Series(index=d.index))).fillna(0)
    d["metric_family_match"] = numeric(d.get("metric_family_match", pd.Series(index=d.index))).fillna(-1)
    d = d[d["journal_n_preferred"].gt(0) & d["journal_d_proxy_preferred"].gt(0)].copy()

    if d.empty:
        return pd.DataFrame()

    # One row per PMID. The selector stays on extraction and match quality,
    # rather than on significance or positive/inconclusive support labels.
    d["pair_rank"] = d["pair_quality"].astype(str).map({"high": 2, "medium": 1}).fillna(0)
    d["metric_rank"] = d["metric_family_match"].clip(lower=0)
    d["p_rank"] = d.get("journal_p_source", pd.Series("", index=d.index)).astype(str).map({"best_sentence": 2, "full_abstract": 1}).fillna(0)
    d["n_rank"] = d.get("journal_n_preferred_source", pd.Series("", index=d.index)).astype(str).map({"abstract_selected": 2, "registry_enrollment_fallback": 1}).fillna(0)
    d["d_rank"] = d.get("journal_d_proxy_preferred_source", pd.Series("", index=d.index)).astype(str).map({"abstract_p_and_selected_n": 2, "abstract_p_and_registry_n": 1}).fillna(0)
    d["sel_score"] = (
        100 * d["pair_rank"]
        + 10 * d["metric_rank"]
        + 3 * d["p_rank"]
        + 2 * d["n_rank"]
        + 2 * d["d_rank"]
        + d["selected_sentence_score"]
        + d["combined_match_score"] / 10
        + np.log10(d["journal_n_preferred"].clip(lower=1)) / 100
    )

    d["pmid_text"] = d["PMID"].map(to_num)
    d["pmid_text"] = np.where(d["pmid_text"].notna(), d["pmid_text"].round().astype(int).astype(str), d["PMID"].fillna("").astype(str).str.strip())
    d["pmid_text"] = pd.Series(d["pmid_text"], index=d.index).astype(str).str.replace(r"\.0$", "", regex=True)

    d = (
        d.sort_values(
            ["pmid_text", "sel_score", "selected_sentence_score", "combined_match_score", "journal_n_preferred"],
            ascending=[True, False, False, False, False],
        )
        .drop_duplicates("pmid_text")
        .copy()
    )

    outcome = d.get("clinifact_outcome_title", pd.Series("", index=d.index)).fillna("")
    outcome = outcome.where(outcome.astype(str).str.strip().ne(""), d.get("registry_outcome_title", pd.Series("", index=d.index)).fillna(""))

    notes = (
        "pair_quality="
        + d["pair_quality"].fillna("").astype(str)
        + "; match_quality="
        + d.get("match_quality", pd.Series("", index=d.index)).fillna("").astype(str)
        + "; journal_p_source="
        + d.get("journal_p_source", pd.Series("", index=d.index)).fillna("").astype(str)
        + "; journal_n_source="
        + d.get("journal_n_preferred_source", pd.Series("", index=d.index)).fillna("").astype(str)
        + "; journal_d_source="
        + d.get("journal_d_proxy_preferred_source", pd.Series("", index=d.index)).fillna("").astype(str)
        + "; metric_match="
        + d["metric_family_match"].fillna(-1).astype(str)
        + "; sentence_score="
        + d["selected_sentence_score"].round(3).astype(str)
        + "; combined_match_score="
        + d["combined_match_score"].round(3).astype(str)
        + "; claim_id="
        + d.get("claim_id", pd.Series("", index=d.index)).fillna("").astype(str)
        + "; nctId="
        + d.get("nctId", pd.Series("", index=d.index)).fillna("").astype(str)
    )

    return finalize(
        pd.DataFrame(
            {
                "source_corpus": "clinifact_published_primary_pairs",
                "field": "medicine_rct",
                "source_kind": "published_trial_result_registry_linked_primary_outcome",
                "published_scope": "published_trial_reports_linked_to_ctgov_primary_outcomes",
                "published_original_candidate": True,
                "comparator_only": False,
                "row_id": "clinifact_pubpair_" + d.get("claim_id", pd.Series("", index=d.index)).fillna("").astype(str),
                "paper_id": "PMID:" + d["pmid_text"],
                "study_id": "NCT:" + d.get("nctId", pd.Series("", index=d.index)).fillna("").astype(str) + "::" + d.get("claim_id", pd.Series("", index=d.index)).fillna("").astype(str),
                "title": d.get("article_title", pd.Series("", index=d.index)).fillna("").astype(str),
                "journal": "",
                "year": numeric(d.get("publication_year", pd.Series(index=d.index))),
                "outcome": outcome.astype(str),
                "effect_type": "p_value_derived_d_proxy",
                "effect": d["journal_d_proxy_preferred"],
                "se": np.nan,
                "z": d["journal_abs_z_from_p"],
                "N": d["journal_n_preferred"],
                "D": d["journal_d_proxy_preferred"],
                "D_method": "clinifact_journal_paired_primary_outcome_p_to_2absz_sqrtN",
                "N_method": d.get("journal_n_preferred_source", pd.Series("", index=d.index)).fillna("").astype(str),
                "main_result_flag": "clinifact_conservative_best_primary_outcome_match_per_pmid",
                "published_flag": "published_journal",
                "raw_file": str(path),
                "notes": notes,
            }
        )
    )


def build_dellavigna(raw_dir: Path) -> pd.DataFrame:
    base = raw_dir / "dellavigna_linos/unzipped/cleaned_data"
    frames: list[pd.DataFrame] = []
    for file_name, source_kind, published_scope in [
        ("AcademicJournals.dta", "published_original_rct_journal", "published_academic_journals"),
        ("NudgeUnits.dta", "nudge_unit_trial_report", "mixed_published_unpublished_reports"),
    ]:
        path = base / file_name
        if not path.exists():
            continue
        d = pd.read_stata(path, convert_categoricals=False)
        n = numeric(d.get("controlN", pd.Series(index=d.index))) + numeric(d.get("treatmentN", pd.Series(index=d.index)))
        if "N" in d.columns:
            n = n.fillna(numeric(d["N"]))
        if "trialN" in d.columns:
            n = n.fillna(numeric(d["trialN"]))
        z = numeric(d.get("t", pd.Series(index=d.index)))
        effect = numeric(d.get("treatmenteffect", pd.Series(index=d.index)))
        se = numeric(d.get("SE", pd.Series(index=d.index)))
        pub = d.get("publication", pd.Series(1, index=d.index))
        pub_text = pub.map(lambda x: "published" if to_num(x) == 1 else ("unpublished" if to_num(x) == 0 else "unknown"))
        is_academic = file_name == "AcademicJournals.dta"
        published_candidate = pd.Series(is_academic, index=d.index) | pub_text.eq("published")
        comparator_only = pd.Series(False if is_academic else True, index=d.index) & ~pub_text.eq("published")
        frames.append(
            pd.DataFrame(
                {
                    "source_corpus": "dellavigna_linos_2022",
                    "field": "economics_nudge",
                    "source_kind": source_kind,
                    "published_scope": published_scope,
                    "published_original_candidate": published_candidate,
                    "comparator_only": comparator_only,
                    "row_id": "dellavigna_" + file_name.replace(".dta", "") + "_" + d.index.astype(str),
                    "paper_id": d.get("trialtitle", pd.Series(index=d.index)).astype(str),
                    "study_id": d.get("trialnumber", pd.Series(index=d.index)).astype(str),
                    "title": d.get("trialtitle", pd.Series(index=d.index)).astype(str),
                    "journal": d.get("journal", pd.Series("", index=d.index)).astype(str),
                    "year": numeric(d.get("year", pd.Series(index=d.index))),
                    "outcome": d.get("outcomedescription", pd.Series(index=d.index)).astype(str),
                    "effect_type": "percentage_point_or_log_or_reported_by_source",
                    "effect": effect,
                    "se": se,
                    "z": z,
                    "N": n,
                    "D": 2 * z.abs() / np.sqrt(n),
                    "D_method": "reported_t_to_2absz_sqrtN",
                    "N_method": "controlN_plus_treatmentN_else_N",
                    "main_result_flag": "source_selected_treatment_arm",
                    "published_flag": pub_text,
                    "raw_file": str(path),
                    "notes": d.get("notes", pd.Series("", index=d.index)).astype(str),
                }
            )
        )
    return finalize(pd.concat(frames, ignore_index=True)) if frames else pd.DataFrame()


def build_brodeur_2024(_: Path) -> pd.DataFrame:
    path = ROOT / "data/raw/published_papers/brodeur_2024_merged.dta"
    if not path.exists():
        return pd.DataFrame()

    cols = [
        "journal",
        "title",
        "table",
        "method",
        "coeff",
        "stderror",
        "year",
        "myz",
        "zstat",
        "t_stat",
        "observations",
        "samplesizenumberobservations",
        "totalnumberofobservations",
        "doinumber",
        "prereg",
        "preanalysisplan",
        "pap_power",
    ]
    d = pd.read_stata(path, columns=cols, convert_categoricals=False)
    d["title"] = d["title"].fillna("").astype(str).str.strip()
    d["journal"] = d["journal"].fillna("").astype(str).str.strip()
    d["doi"] = d.get("doinumber", pd.Series("", index=d.index)).fillna("").astype(str).str.strip()
    d["z"] = numeric(d.get("myz", pd.Series(index=d.index)))
    z_fallback = numeric(d.get("zstat", pd.Series(index=d.index)))
    d.loc[d["z"].isna(), "z"] = z_fallback[d["z"].isna()]
    d["N"] = numeric(d.get("observations", pd.Series(index=d.index)))
    d["D"] = 2 * d["z"].abs() / np.sqrt(d["N"].where(d["N"] > 0))
    d = d[
        np.isfinite(d["D"])
        & np.isfinite(d["N"])
        & d["N"].between(4, 10_000_000)
        & d["D"].gt(0)
        & d["D"].le(30)
        & d["title"].ne("")
    ].copy()

    if d.empty:
        return pd.DataFrame()

    notes = (
        "method="
        + d.get("method", pd.Series("", index=d.index)).fillna("").astype(str)
        + "; prereg="
        + d.get("prereg", pd.Series("", index=d.index)).fillna("").astype(str)
        + "; preanalysisplan="
        + d.get("preanalysisplan", pd.Series("", index=d.index)).fillna("").astype(str)
        + "; pap_power="
        + d.get("pap_power", pd.Series("", index=d.index)).fillna("").astype(str)
    )

    return finalize(
        pd.DataFrame(
            {
                "source_corpus": "economics_brodeur_2024",
                "field": "economics",
                "source_kind": "published_economics_extracted_tests",
                "published_scope": "published_top_journal_economics_tables",
                "published_original_candidate": True,
                "comparator_only": False,
                "row_id": "brodeur_2024_" + d.index.astype(str),
                "paper_id": np.where(d["doi"].ne(""), "DOI:" + d["doi"], "Brodeur2024:" + d["title"]),
                "study_id": np.where(d["doi"].ne(""), "DOI:" + d["doi"], "Brodeur2024:" + d["title"]) + "::table:" + d.get("table", pd.Series("", index=d.index)).fillna("").astype(str),
                "title": d["title"],
                "journal": d["journal"],
                "year": numeric(d.get("year", pd.Series(index=d.index))),
                "outcome": d.get("table", pd.Series("", index=d.index)).fillna("").astype(str),
                "effect_type": "z_statistic_derived_d_proxy",
                "effect": d["D"],
                "se": np.nan,
                "z": d["z"],
                "N": d["N"],
                "D": d["D"],
                "D_method": "brodeur_2024_2absz_sqrt_observations",
                "N_method": "published_table_observations",
                "main_result_flag": "published_table_extracted_test_not_main_selected",
                "published_flag": "published_journal",
                "raw_file": str(path),
                "notes": notes,
            }
        )
    )


def build_turner(raw_dir: Path) -> pd.DataFrame:
    path = raw_dir / "turner_antidepressants/supplements/pmed.1003886.s018"
    if not path.exists():
        return pd.DataFrame()
    frames: list[pd.DataFrame] = []
    xl = pd.ExcelFile(path)
    for sheet in xl.sheet_names:
        d = pd.read_excel(path, sheet_name=sheet)
        is_journal = sheet.lower().startswith("journal")
        effect_col = "g_corr" if "g_corr" in d.columns else "g_corrected"
        se_col = "se_corr" if "se_corr" in d.columns else "se_g"
        study_col = "study" if "study" in d.columns else ("studynumber" if "studynumber" in d.columns else "study_number")
        effect = numeric(d[effect_col])
        se = numeric(d[se_col])
        n = numeric(d["n1n2"])
        z = effect / se
        frames.append(
            pd.DataFrame(
                {
                    "source_corpus": "turner_antidepressants_2022",
                    "field": "medicine_psychiatry",
                    "source_kind": "journal_publication" if is_journal else "fda_regulatory",
                    "published_scope": "published_journal" if is_journal else "fda_regulatory_all",
                    "published_original_candidate": is_journal,
                    "comparator_only": not is_journal,
                    "row_id": "turner_" + sheet.replace(" ", "_") + "_" + d.index.astype(str),
                    "paper_id": d.get("publication", d[study_col]).astype(str),
                    "study_id": d.get("drug", pd.Series(index=d.index)).astype(str) + "_" + d[study_col].astype(str),
                    "title": d.get("publication", pd.Series("", index=d.index)).astype(str),
                    "journal": "",
                    "year": np.nan,
                    "outcome": "antidepressant efficacy",
                    "effect_type": "hedges_g",
                    "effect": effect,
                    "se": se,
                    "z": z,
                    "N": n,
                    "D": effect.abs(),
                    "D_method": "reported_corrected_g",
                    "N_method": "n_drug_plus_n_placebo",
                    "main_result_flag": "trial_primary_efficacy",
                    "published_flag": "published" if is_journal else "regulatory",
                    "raw_file": str(path),
                    "notes": sheet,
                }
            )
        )
    return finalize(pd.concat(frames, ignore_index=True))


def export_metalab_with_r(path: Path, out_csv: Path) -> bool:
    if out_csv.exists():
        return True
    r_code = f"""
load({str(path)!r})
keep <- intersect(names(metalab_data), c("unique_row", "study_ID", "long_cite", "short_cite", "peer_reviewed", "n", "n_1", "n_2", "d", "d_var", "dataset", "domain", "year"))
write.csv(metalab_data[, keep], {str(out_csv)!r}, row.names=FALSE, na="")
"""
    try:
        subprocess.run(["Rscript", "--vanilla", "-e", r_code], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except Exception:
        return False
    return out_csv.exists()


def build_metalab(raw_dir: Path, interim_dir: Path) -> pd.DataFrame:
    path = raw_dir / "metalab/metalab.Rdata"
    if not path.exists():
        return pd.DataFrame()
    ensure_dir(interim_dir)
    csv_path = interim_dir / "metalab_data.csv"
    if not export_metalab_with_r(path, csv_path):
        return pd.DataFrame()
    d = pd.read_csv(csv_path, low_memory=False)
    effect = numeric(d["d"])
    n = numeric(d["n"])
    se = np.sqrt(numeric(d["d_var"]))
    z = effect / se
    peer = d.get("peer_reviewed", pd.Series("", index=d.index)).astype(str).str.lower()
    return finalize(
        pd.DataFrame(
            {
                "source_corpus": "metalab",
                "field": "developmental_psychology",
                "source_kind": "meta_analysis_curated_primary_studies",
                "published_scope": "peer_reviewed_flag_available",
                "published_original_candidate": peer.eq("yes"),
                "comparator_only": False,
                "row_id": "metalab_" + d.get("unique_row", pd.Series(d.index, index=d.index)).astype(str),
                "paper_id": d["study_ID"].astype(str),
                "study_id": d["study_ID"].astype(str),
                "title": d.get("long_cite", pd.Series("", index=d.index)).astype(str),
                "journal": "",
                "year": numeric(d.get("year", pd.Series(index=d.index))),
                "outcome": d.get("dataset", pd.Series("", index=d.index)).astype(str),
                "effect_type": "cohens_d",
                "effect": effect,
                "se": se,
                "z": z,
                "N": n,
                "D": effect.abs(),
                "D_method": "reported_d",
                "N_method": "reported_n",
                "main_result_flag": "meta_analysis_effect_row",
                "published_flag": np.where(peer.eq("yes"), "peer_reviewed", np.where(peer.eq("no"), "not_peer_reviewed", "unknown")),
                "raw_file": str(path),
                "notes": d.get("domain", pd.Series("", index=d.index)).astype(str),
            }
        )
    )


def build_metabus(raw_dir: Path) -> pd.DataFrame:
    path = raw_dir / "metabus/Ver2-08_MasterDB_JAP-PPsych_1980-2010.xlsx"
    if not path.exists():
        return pd.DataFrame()
    d = pd.read_excel(path, sheet_name="DATA")
    n_by_article = numeric(d["N"]).groupby(d["ArticleID"]).median()
    inferred_n = d["ArticleID"].map(n_by_article)
    r = numeric(d["r"])
    n = inferred_n
    ok = r.abs().lt(0.999999)
    r = r.where(ok)
    effect = 2 * r / np.sqrt(1 - r**2)
    se_r_z = 1 / np.sqrt(n - 3)
    z = np.arctanh(r) / se_r_z
    return finalize(
        pd.DataFrame(
            {
                "source_corpus": "metabus_open_bosco",
                "field": "io_psychology_management",
                "source_kind": "published_original_journal_correlation_matrix",
                "published_scope": "published_jap_personnel_psychology",
                "published_original_candidate": True,
                "comparator_only": False,
                "row_id": "metabus_" + d["RowID"].astype(str),
                "paper_id": d["ArticleID"].astype(str),
                "study_id": d["ArticleID"].astype(str),
                "title": "",
                "journal": d["ArticleID"].astype(str).str.extract(r"^(JAP|PPsych)", expand=False).fillna(""),
                "year": numeric(d["Year"]),
                "outcome": d.get("VariableName", pd.Series("", index=d.index)).astype(str),
                "effect_type": "pearson_r_converted_to_d",
                "effect": effect,
                "se": np.nan,
                "z": z,
                "N": n,
                "D": effect.abs(),
                "D_method": "pearson_r_to_d",
                "N_method": "article_median_reported_matrix_N",
                "main_result_flag": "correlation_matrix_row",
                "published_flag": "published",
                "raw_file": str(path),
                "notes": "",
            }
        )
    )


def build_button_nord(raw_dir: Path) -> pd.DataFrame:
    path = raw_dir / "button_nord_neuroscience/Effect_Sizes_opendata.xlsx"
    if not path.exists():
        return pd.DataFrame()
    frames: list[pd.DataFrame] = []
    d = pd.read_excel(path, sheet_name="Sheet2")
    n = numeric(d["N (experimental)"]) + numeric(d["N (control)"])
    effect = numeric(d["Overall d"])
    frames.append(
        pd.DataFrame(
            {
                "source_corpus": "button_nord_neuroscience",
                "field": "neuroscience",
                "source_kind": "published_meta_analysis_primary_studies",
                "published_scope": "published_primary_studies",
                "published_original_candidate": True,
                "comparator_only": False,
                "row_id": "button_smd_" + d.index.astype(str),
                "paper_id": d["Meta-analysis"].ffill().astype(str) + "_" + d.index.astype(str),
                "study_id": d["Meta-analysis"].ffill().astype(str) + "_" + d.index.astype(str),
                "title": "",
                "journal": "",
                "year": numeric(d["Date"]),
                "outcome": d["Meta-analysis"].ffill().astype(str),
                "effect_type": "cohens_d",
                "effect": effect,
                "se": np.nan,
                "z": np.nan,
                "N": n,
                "D": effect.abs(),
                "D_method": "reported_overall_d",
                "N_method": "experimental_plus_control_N",
                "main_result_flag": "meta_analysis_primary_study_row",
                "published_flag": "published",
                "raw_file": str(path),
                "notes": "Sheet2 SMD rows",
            }
        )
    )
    d = pd.read_excel(path, sheet_name="Sheet3")
    n = numeric(d["Total N"]).fillna(numeric(d["N (exp)"]) + numeric(d["N (control)"]))
    log_or = np.log(numeric(d["Pooled OR"]))
    effect = log_or * math.sqrt(3) / math.pi
    frames.append(
        pd.DataFrame(
            {
                "source_corpus": "button_nord_neuroscience",
                "field": "neuroscience",
                "source_kind": "published_meta_analysis_primary_studies",
                "published_scope": "published_primary_studies",
                "published_original_candidate": True,
                "comparator_only": False,
                "row_id": "button_or_" + d.index.astype(str),
                "paper_id": d["Meta-analysis"].ffill().astype(str) + "_" + d.index.astype(str),
                "study_id": d["Meta-analysis"].ffill().astype(str) + "_" + d.index.astype(str),
                "title": "",
                "journal": "",
                "year": numeric(d["Date of study"]),
                "outcome": d["Meta-analysis"].ffill().astype(str),
                "effect_type": "odds_ratio_converted_to_d",
                "effect": effect,
                "se": np.nan,
                "z": np.nan,
                "N": n,
                "D": effect.abs(),
                "D_method": "log_or_times_sqrt3_over_pi",
                "N_method": "reported_total_N",
                "main_result_flag": "meta_analysis_primary_study_row",
                "published_flag": "published",
                "raw_file": str(path),
                "notes": "Sheet3 OR rows",
            }
        )
    )
    return finalize(pd.concat(frames, ignore_index=True))


def build_rpcb(raw_dir: Path) -> pd.DataFrame:
    path = raw_dir / "rpcb/RP_CB Final Analysis - Effect level data.csv"
    if not path.exists():
        return pd.DataFrame()
    d = pd.read_csv(path)
    frames: list[pd.DataFrame] = []
    for prefix, kind, sample_col, effect_col, se_col in [
        ("original", "published_original_preclinical", "Original sample size", "Original effect size (SMD)", "Original standard error (SMD)"),
        ("replication", "registered_replication", "Replication sample size", "Replication effect size (SMD)", "Replication standard error (SMD)"),
    ]:
        effect = numeric(d[effect_col])
        se = numeric(d[se_col])
        z = effect / se
        frames.append(
            pd.DataFrame(
                {
                    "source_corpus": "rpcb_cancer_biology",
                    "field": "preclinical_cancer_biology",
                    "source_kind": kind,
                    "published_scope": "original_published_vs_registered_replication",
                    "published_original_candidate": prefix == "original",
                    "comparator_only": prefix != "original",
                    "row_id": "rpcb_" + prefix + "_" + d.index.astype(str),
                    "paper_id": "paper_" + d["Paper #"].astype(str),
                    "study_id": "paper_" + d["Paper #"].astype(str) + "_experiment_" + d["Experiment #"].astype(str),
                    "title": "",
                    "journal": "",
                    "year": np.nan,
                    "outcome": d["Effect description"].astype(str),
                    "effect_type": "standardized_mean_difference",
                    "effect": effect,
                    "se": se,
                    "z": z,
                    "N": numeric(d[sample_col]),
                    "D": effect.abs(),
                    "D_method": "reported_smd",
                    "N_method": sample_col,
                    "main_result_flag": "replication_project_effect_row",
                    "published_flag": "published_original" if prefix == "original" else "replication",
                    "raw_file": str(path),
                    "notes": "",
                }
            )
        )
    return finalize(pd.concat(frames, ignore_index=True))


def build_szucs(raw_dir: Path) -> pd.DataFrame:
    path = raw_dir / "szucs_ioannidis_2017/szucs_ioannidis_2017_s1_data.mat"
    if not path.exists():
        return pd.DataFrame()
    mat = loadmat(path, squeeze_me=True, struct_as_record=False)
    data = mat["D"]
    t = pd.Series(np.asarray(data.tvalues, dtype=float))
    dfree = pd.Series(np.asarray(data.df, dtype=float))
    n = dfree + 2
    D = 2 * t.abs() / np.sqrt(dfree)
    return finalize(
        pd.DataFrame(
            {
                "source_corpus": "szucs_ioannidis_2017",
                "field": "cognitive_neuroscience_psychology",
                "source_kind": "published_original_journal_test_statistics",
                "published_scope": "published_18_journals",
                "published_original_candidate": True,
                "comparator_only": False,
                "row_id": "szucs_" + t.index.astype(str),
                "paper_id": "",
                "study_id": "",
                "title": "",
                "journal": "",
                "year": np.nan,
                "outcome": "",
                "effect_type": "t_statistic_derived_d",
                "effect": D,
                "se": np.nan,
                "z": t,
                "N": n,
                "D": D,
                "D_method": "2_abs_t_over_sqrt_df",
                "N_method": "df_plus_2_approximation",
                "main_result_flag": "all_extracted_tests",
                "published_flag": "published",
                "raw_file": str(path),
                "notes": "MATLAB table with journal/paper grouping not decoded yet; row-level only",
            }
        )
    )


def build_score(raw_dir: Path) -> pd.DataFrame:
    base = raw_dir / "score"
    metadata_path = base / "paper_metadata.csv"
    meta = pd.DataFrame()
    if metadata_path.exists():
        meta = pd.read_csv(metadata_path, low_memory=False)
        meta = meta.rename(columns={"DOI": "doi", "pub_year": "year", "COS_pub_category": "field_category"})
        meta["paper_id"] = meta["paper_id"].astype(str)

    frames: list[pd.DataFrame] = []

    structured_path = base / "orig_outcomes.csv"
    if structured_path.exists():
        d = pd.read_csv(structured_path, low_memory=False)
        d["paper_id"] = d["paper_id"].astype(str)
        if not meta.empty:
            d = d.merge(
                meta[["paper_id", "doi", "title", "publication_standard", "year", "field_category", "citation"]],
                on="paper_id",
                how="left",
            )
        n = numeric(d["orig_sample_size_value"]).fillna(numeric(d.get("original_effective_sample_size", pd.Series(index=d.index))))
        D = pd.Series(np.nan, index=d.index, dtype=float)
        z = pd.Series(np.nan, index=d.index, dtype=float)
        effect_type = pd.Series("", index=d.index, dtype=object)
        method = pd.Series("", index=d.index, dtype=object)

        conv_r = numeric(d.get("orig_conv_r", pd.Series(index=d.index)))
        r_ok = conv_r.abs().lt(0.999999)
        D.loc[r_ok] = conv_r.loc[r_ok].map(r_to_d_scalar)
        effect_type.loc[r_ok] = "partial_r_converted_to_d"
        method.loc[r_ok] = "score_orig_conv_r_to_d"

        for i in d.index[D.isna()]:
            dd, etype, m = effect_type_value_to_d(d.at[i, "orig_effect_size_type_repro"], d.at[i, "orig_effect_size_value_repro"])
            if np.isfinite(dd):
                D.at[i] = dd
                effect_type.at[i] = etype
                method.at[i] = m

        for i in d.index[D.isna()]:
            stat_type = str(d.at[i, "orig_stat_type"]).lower()
            stat_value = to_num(d.at[i, "orig_stat_value"])
            df1 = to_num(d.at[i, "orig_stat_dof_1"])
            df2 = to_num(d.at[i, "orig_stat_dof_2"])
            ni = n.at[i]
            if stat_type == "t" and np.isfinite(stat_value):
                if np.isfinite(df2) and df2 > 0:
                    D.at[i] = 2 * abs(stat_value) / math.sqrt(df2)
                    z.at[i] = stat_value
                    effect_type.at[i] = "t_statistic_derived_d"
                    method.at[i] = "2_abs_t_over_sqrt_df"
                elif np.isfinite(ni) and ni > 0:
                    D.at[i] = 2 * abs(stat_value) / math.sqrt(ni)
                    z.at[i] = stat_value
                    effect_type.at[i] = "t_statistic_derived_d_proxy"
                    method.at[i] = "2_abs_t_over_sqrtN"
            elif stat_type == "z" and np.isfinite(stat_value) and np.isfinite(ni) and ni > 0:
                D.at[i] = 2 * abs(stat_value) / math.sqrt(ni)
                z.at[i] = stat_value
                effect_type.at[i] = "z_statistic_derived_d_proxy"
                method.at[i] = "2_abs_z_over_sqrtN"
            elif stat_type == "f" and np.isfinite(stat_value) and np.isfinite(df1) and abs(df1 - 1) < 1e-9 and np.isfinite(df2) and df2 > 0:
                D.at[i] = 2 * math.sqrt(stat_value / df2)
                z.at[i] = math.sqrt(stat_value)
                effect_type.at[i] = "f1_statistic_derived_d"
                method.at[i] = "2_sqrt_f_over_df2"
            elif stat_type in {"chi_squared", "chi-square", "chisq"} and np.isfinite(stat_value) and np.isfinite(ni) and ni > 0:
                r = math.sqrt(max(stat_value, 0) / ni)
                D.at[i] = r_to_d_scalar(r)
                effect_type.at[i] = "chi_square_phi_converted_to_d"
                method.at[i] = "chi_square_over_N_to_phi_to_d"

        for i in d.index[D.isna()]:
            coef = to_num(d.at[i, "orig_coef_value"])
            se = to_num(d.at[i, "orig_coef_se"])
            ni = n.at[i]
            if np.isfinite(coef) and np.isfinite(se) and se > 0 and np.isfinite(ni) and ni > 0:
                zi = coef / se
                D.at[i] = 2 * abs(zi) / math.sqrt(ni)
                z.at[i] = zi
                effect_type.at[i] = "coef_se_derived_d_proxy"
                method.at[i] = "coef_over_se_to_2absz_sqrtN"

        for i in d.index[D.isna()]:
            dd, zi, m = p_to_d_proxy_from_text(d.at[i, "orig_p_value"], n.at[i], d.at[i, "orig_p_value_type"], d.at[i, "orig_p_value_tails"])
            if np.isfinite(dd):
                D.at[i] = dd
                z.at[i] = zi
                effect_type.at[i] = "p_value_derived_d_proxy"
                method.at[i] = m

        frames.append(
            pd.DataFrame(
                {
                    "source_corpus": "score_cos_claims",
                    "field": d.get("field_category", pd.Series("social_behavioral", index=d.index)).fillna("social_behavioral").astype(str),
                    "source_kind": "score_structured_orig_outcomes",
                    "published_scope": "sampled_social_behavioral_journal_claims",
                    "published_original_candidate": True,
                    "comparator_only": False,
                    "row_id": "score_orig_" + d["claim_id"].astype(str),
                    "paper_id": np.where(d.get("doi", pd.Series("", index=d.index)).fillna("").astype(str).ne(""), "DOI:" + d.get("doi", pd.Series("", index=d.index)).fillna("").astype(str), "SCORE:" + d["paper_id"].astype(str)),
                    "study_id": "SCORE:" + d["claim_id"].astype(str),
                    "title": d.get("title", pd.Series("", index=d.index)).fillna("").astype(str),
                    "journal": d.get("publication_standard", pd.Series("", index=d.index)).fillna("").astype(str),
                    "year": numeric(d.get("year", pd.Series(index=d.index))),
                    "outcome": d.get("orig_effect_size_text", pd.Series("", index=d.index)).fillna("").astype(str),
                    "effect_type": effect_type,
                    "effect": D,
                    "se": np.nan,
                    "z": z,
                    "N": n,
                    "D": D,
                    "D_method": method,
                    "N_method": "score_orig_sample_size_value",
                    "main_result_flag": "score_structured_focal_claim",
                    "published_flag": "published_journal",
                    "raw_file": str(structured_path),
                    "notes": d.get("orig_effect_size_text", pd.Series("", index=d.index)).fillna("").astype(str),
                }
            )
        )

    claims_path = base / "extracted_claims.csv"
    if claims_path.exists():
        d = pd.read_csv(claims_path, low_memory=False)
        d["paper_id"] = d["paper_id"].astype(str)
        if not meta.empty:
            d = d.merge(
                meta[["paper_id", "doi", "title", "publication_standard", "year", "field_category", "citation"]],
                on="paper_id",
                how="left",
            )
        n = d.get("coded_sample_size", pd.Series(index=d.index)).fillna(d.get("sample_size", pd.Series(index=d.index))).map(extract_main_n)
        D = pd.Series(np.nan, index=d.index, dtype=float)
        z = pd.Series(np.nan, index=d.index, dtype=float)
        effect_type = pd.Series("", index=d.index, dtype=object)
        method = pd.Series("", index=d.index, dtype=object)
        text = (
            d.get("coded_effect_size", pd.Series("", index=d.index)).fillna("").astype(str)
            + " | "
            + d.get("coded_stat_evidence", pd.Series("", index=d.index)).fillna("").astype(str)
            + " | "
            + d.get("coded_claim4", pd.Series("", index=d.index)).fillna("").astype(str)
        )
        for i, value in text.items():
            dd, zi, etype, m = parse_stat_text_to_d(value, n.at[i])
            if np.isfinite(dd):
                D.at[i] = dd
                z.at[i] = zi
                effect_type.at[i] = etype
                method.at[i] = "score_free_text_" + m
        for i in d.index[D.isna()]:
            dd, zi, m = p_to_d_proxy_from_text(d.at[i, "coded_p_value"] if "coded_p_value" in d.columns else np.nan, n.at[i])
            if not np.isfinite(dd):
                dd, zi, m = p_to_d_proxy_from_text(d.at[i, "p_value"] if "p_value" in d.columns else np.nan, n.at[i])
            if np.isfinite(dd):
                D.at[i] = dd
                z.at[i] = zi
                effect_type.at[i] = "p_value_derived_d_proxy"
                method.at[i] = "score_free_text_" + m

        frames.append(
            pd.DataFrame(
                {
                    "source_corpus": "score_cos_claims",
                    "field": d.get("field_category", pd.Series("social_behavioral", index=d.index)).fillna("social_behavioral").astype(str),
                    "source_kind": "score_extracted_claims_free_text",
                    "published_scope": "sampled_social_behavioral_journal_claims",
                    "published_original_candidate": True,
                    "comparator_only": False,
                    "row_id": "score_claim_" + d["unique_claim_id"].astype(str),
                    "paper_id": np.where(d.get("doi", pd.Series("", index=d.index)).fillna("").astype(str).ne(""), "DOI:" + d.get("doi", pd.Series("", index=d.index)).fillna("").astype(str), "SCORE:" + d["paper_id"].astype(str)),
                    "study_id": "SCORE:" + d["unique_claim_id"].astype(str),
                    "title": d.get("title", pd.Series("", index=d.index)).fillna("").astype(str),
                    "journal": d.get("publication_standard", pd.Series("", index=d.index)).fillna("").astype(str),
                    "year": numeric(d.get("year", pd.Series(index=d.index))),
                    "outcome": d.get("coded_claim3", pd.Series("", index=d.index)).fillna("").astype(str),
                    "effect_type": effect_type,
                    "effect": D,
                    "se": np.nan,
                    "z": z,
                    "N": n,
                    "D": D,
                    "D_method": method,
                    "N_method": "score_free_text_sample_size_parse",
                    "main_result_flag": "score_extracted_representative_claim",
                    "published_flag": "published_journal",
                    "raw_file": str(claims_path),
                    "notes": text,
                }
            )
        )

    return finalize(pd.concat(frames, ignore_index=True)) if frames else pd.DataFrame()


def build_fred(raw_dir: Path) -> pd.DataFrame:
    path = raw_dir / "fred/FReD.xlsx"
    if not path.exists():
        return pd.DataFrame()
    d = pd.read_excel(path)
    n = numeric(d["n_o"])
    D = pd.Series(np.nan, index=d.index, dtype=float)
    z = pd.Series(np.nan, index=d.index, dtype=float)
    effect_type = pd.Series("", index=d.index, dtype=object)
    method = pd.Series("", index=d.index, dtype=object)

    for i in d.index:
        dd, etype, m = effect_type_value_to_d(d.at[i, "es_type_o"], d.at[i, "es_value_o"])
        if np.isfinite(dd):
            D.at[i] = dd
            effect_type.at[i] = etype
            method.at[i] = "fred_" + m
            continue
        dd, zi, etype, m = parse_stat_text_to_d(d.at[i, "es_value_o"], n.at[i])
        if np.isfinite(dd):
            D.at[i] = dd
            z.at[i] = zi
            effect_type.at[i] = etype
            method.at[i] = "fred_" + m
            continue
        dd, zi, m = p_to_d_proxy_from_text(d.at[i, "pval_value_o"], n.at[i], d.at[i, "pval_type_o"], d.at[i, "pval_tails_o"])
        if np.isfinite(dd):
            D.at[i] = dd
            z.at[i] = zi
            effect_type.at[i] = "p_value_derived_d_proxy"
            method.at[i] = "fred_" + m

    doi = d["doi_o"].fillna("").astype(str)
    return finalize(
        pd.DataFrame(
            {
                "source_corpus": "forrt_fred",
                "field": d.get("discipline", pd.Series("psychology_replication", index=d.index)).fillna("psychology_replication").astype(str),
                "source_kind": "replication_target_original_claim",
                "published_scope": "published_original_claims_selected_for_replication",
                "published_original_candidate": True,
                "comparator_only": False,
                "row_id": "fred_" + d["entry_id"].astype(str) + "_" + d["effect_id"].astype(str),
                "paper_id": np.where(doi.ne(""), "DOI:" + doi, "FReD:" + d["entry_id"].astype(str)),
                "study_id": "FReD:" + d["fred_id"].fillna("").astype(str) + "_" + d["effect_id"].astype(str),
                "title": d.get("title_o", pd.Series("", index=d.index)).fillna("").astype(str),
                "journal": d.get("journal_o", pd.Series("", index=d.index)).fillna("").astype(str),
                "year": numeric(d.get("year_o", pd.Series(index=d.index))),
                "outcome": d.get("description", pd.Series("", index=d.index)).fillna("").astype(str),
                "effect_type": effect_type,
                "effect": D,
                "se": np.nan,
                "z": z,
                "N": n,
                "D": D,
                "D_method": method,
                "N_method": "fred_original_n",
                "main_result_flag": "replication_target_focal_claim",
                "published_flag": "published_journal",
                "raw_file": str(path),
                "notes": d.get("claim_text_o", pd.Series("", index=d.index)).fillna("").astype(str),
            }
        )
    )


def build_esarey_wu_2016(raw_dir: Path) -> pd.DataFrame:
    zip_path = raw_dir / "esarey_wu_2016/pub-bias-replication-files.zip"
    if not zip_path.exists():
        return pd.DataFrame()

    import zipfile

    with zipfile.ZipFile(zip_path) as zf:
        dta_name = next(
            (
                name
                for name in zf.namelist()
                if name.lower().endswith("publication_data_2016-5-29.dta")
            ),
            None,
        )
        if dta_name is None:
            return pd.DataFrame()
        with zf.open(dta_name) as handle:
            d = pd.read_stata(handle)

    # Esarey & Wu's own replication code keeps one main-finding row per paper by
    # restricting to the first model and the first dependent variable.
    d = d[(numeric(d.get("model", pd.Series(index=d.index))) == 1) & (numeric(d.get("number_of_dv", pd.Series(index=d.index))) == 1)].copy()

    n = numeric(d.get("sample_size", pd.Series(index=d.index)))
    estimate = numeric(d.get("estimate", pd.Series(index=d.index)))
    se = numeric(d.get("se", pd.Series(index=d.index)))
    z = (estimate / se).abs()
    D = 2 * z / np.sqrt(n)

    doi = d.get("doi", pd.Series("", index=d.index)).fillna("").astype(str).str.strip()
    title = d.get("title", pd.Series("", index=d.index)).fillna("").astype(str)
    journal = d.get("journal", pd.Series("", index=d.index)).fillna("").astype(str)
    year = numeric(d.get("year", pd.Series(index=d.index)))
    order = numeric(d.get("order", pd.Series(index=d.index))).fillna(0).astype(int).astype(str)

    return finalize(
        pd.DataFrame(
            {
                "source_corpus": "esarey_wu_2016_political_science_main_findings",
                "field": "political_science",
                "source_kind": "published_article_author_coded_main_finding",
                "published_scope": "sampled_political_science_journal_main_findings",
                "published_original_candidate": True,
                "comparator_only": False,
                "row_id": np.where(
                    doi.ne(""),
                    "esarey_wu_2016:" + doi,
                    "esarey_wu_2016:" + title.str[:80] + ":" + order,
                ),
                "paper_id": np.where(
                    doi.ne(""),
                    "DOI:" + doi,
                    "EsareyWu2016:" + title.str[:120],
                ),
                "study_id": np.where(
                    doi.ne(""),
                    "EsareyWu2016:" + doi,
                    "EsareyWu2016:" + title.str[:120] + ":" + order,
                ),
                "title": title,
                "journal": journal,
                "year": year,
                "outcome": d.get("key_variable", pd.Series("", index=d.index)).fillna("").astype(str),
                "effect_type": "coefficient_over_se_to_2absz_sqrtN",
                "effect": estimate,
                "se": se,
                "z": z,
                "N": n,
                "D": D,
                "D_method": "esarey_wu_2016_abs_beta_over_se_to_2absz_sqrtN",
                "N_method": "esarey_wu_2016_sample_size",
                "main_result_flag": "author_coded_main_finding_model1_dv1",
                "published_flag": "published_journal",
                "raw_file": str(zip_path) + "::" + dta_name,
                "notes": (
                    "location="
                    + d.get("location", pd.Series("", index=d.index)).fillna("").astype(str)
                    + "; tails="
                    + d.get("tails", pd.Series("", index=d.index)).fillna("").astype(str)
                    + "; num_ivs="
                    + d.get("num_ivs", pd.Series("", index=d.index)).fillna("").astype(str)
                ),
            }
        )
    )


def havranek_frame(
    d: pd.DataFrame,
    source_corpus: str,
    field: str,
    raw_file: Path,
    estimate_col: str,
    se_col: str | None,
    z_col: str | None,
    n_col: str,
    paper_col: str,
    study_col: str,
    year_col: str | None,
    published_col: str | None,
    outcome: str,
) -> pd.DataFrame:
    n = numeric(d[n_col])
    effect = numeric(d[estimate_col])
    se = numeric(d[se_col]) if se_col and se_col in d.columns else pd.Series(np.nan, index=d.index)
    z = numeric(d[z_col]) if z_col and z_col in d.columns else effect / se
    pub = numeric(d[published_col]) if published_col and published_col in d.columns else pd.Series(1, index=d.index)
    pub_flag = np.where(pub.eq(1), "published", np.where(pub.eq(0), "unpublished_or_working_paper", "unknown"))
    return pd.DataFrame(
        {
            "source_corpus": source_corpus,
            "field": field,
            "source_kind": "economics_meta_analysis_primary_estimates",
            "published_scope": "published_flag_when_available",
            "published_original_candidate": pub.eq(1),
            "comparator_only": False,
            "row_id": source_corpus + "_" + d.index.astype(str),
            "paper_id": d[paper_col].astype(str) if paper_col in d.columns else d[study_col].astype(str),
            "study_id": d[study_col].astype(str) if study_col in d.columns else d[paper_col].astype(str),
            "title": d[paper_col].astype(str) if paper_col in d.columns else "",
            "journal": "",
            "year": numeric(d[year_col]) if year_col and year_col in d.columns else np.nan,
            "outcome": outcome,
            "effect_type": estimate_col,
            "effect": effect,
            "se": se,
            "z": z,
            "N": n,
            "D": 2 * z.abs() / np.sqrt(n),
            "D_method": "estimate_or_t_to_2absz_sqrtN",
            "N_method": n_col,
            "main_result_flag": "meta_analysis_estimate_row",
            "published_flag": pub_flag,
            "raw_file": str(raw_file),
            "notes": "",
        }
    )


def build_havranek(raw_dir: Path) -> pd.DataFrame:
    base = raw_dir / "havranek_meta_analysis"
    specs: list[tuple[Path, dict[str, object]]] = [
        (
            base / "eis/eis_unzipped/eis/eis.dta",
            dict(source_corpus="havranek_eis", field="economics", estimate_col="eis", se_col="se", z_col=None, n_col="obs", paper_col="study", study_col="idstudy", year_col="pubyear", published_col="top", outcome="intertemporal elasticity of substitution"),
        ),
        (
            base / "substitution/eis_det.dta",
            dict(source_corpus="havranek_substitution", field="economics", estimate_col="eis", se_col="se", z_col=None, n_col="obs", paper_col="study", study_col="idstudy", year_col="pubyear", published_col="top", outcome="cross-country intertemporal elasticity of substitution"),
        ),
        (
            base / "sigma/sigma.dta",
            dict(source_corpus="havranek_sigma", field="economics", estimate_col="sigma", se_col="se", z_col="t", n_col="nobs", paper_col="study", study_col="idstudy", year_col="pubyear", published_col="top", outcome="capital-labor substitution elasticity"),
        ),
        (
            base / "armington/armington.xlsx",
            dict(source_corpus="havranek_armington", field="economics", estimate_col="armel", se_col="se", z_col="tstats", n_col="nobs", paper_col="author", study_col="idstudy", year_col="pubyear", published_col="pblshd", outcome="Armington trade elasticity"),
        ),
        (
            base / "frisch/frisch_data_unzipped/data_extensive.xlsx",
            dict(source_corpus="havranek_frisch_extensive", field="economics", estimate_col="frisch", se_col="se", z_col=None, n_col="no_obs", paper_col="paper", study_col="idstudy", year_col="pub_year", published_col="published", outcome="Frisch extensive labor supply elasticity"),
        ),
        (
            base / "frisch/frisch_data_unzipped/data_intensive.xlsx",
            dict(source_corpus="havranek_frisch_intensive", field="economics", estimate_col="frisch", se_col="se", z_col="tstat", n_col="obs", paper_col="paper", study_col="idstudy", year_col="pubyear", published_col="published", outcome="Frisch intensive labor supply elasticity"),
        ),
        (
            base / "gasoline/data_unzipped/gas_income_revision.dta",
            dict(source_corpus="havranek_gasoline_income", field="economics", estimate_col="e", se_col=None, z_col="tstat", n_col="Observations", paper_col="Study", study_col="Studyid", year_col="Pubyear", published_col="Published", outcome="gasoline income elasticity"),
        ),
    ]
    frames: list[pd.DataFrame] = []
    for path, kwargs in specs:
        if not path.exists():
            continue
        if path.suffix == ".dta":
            d = pd.read_stata(path, convert_categoricals=False)
        else:
            d = pd.read_excel(path)
        frames.append(havranek_frame(d, raw_file=path, **kwargs))
    return finalize(pd.concat(frames, ignore_index=True)) if frames else pd.DataFrame()


def build_gwas(raw_dir: Path) -> pd.DataFrame:
    path = raw_dir / "gwas_catalog/gwas-catalog-download-associations-alt-full.tsv"
    if not path.exists():
        return pd.DataFrame()
    usecols = [
        "PUBMEDID",
        "FIRST AUTHOR",
        "DATE",
        "JOURNAL",
        "STUDY",
        "DISEASE/TRAIT",
        "INITIAL SAMPLE SIZE",
        "REPLICATION SAMPLE SIZE",
        "P-VALUE",
        "PVALUE_MLOG",
        "P-VALUE (TEXT)",
        "OR or BETA",
        "95% CI (TEXT)",
        "STUDY ACCESSION",
    ]
    chunks: list[pd.DataFrame] = []
    for i, d in enumerate(pd.read_csv(path, sep="\t", usecols=usecols, chunksize=100_000, low_memory=False)):
        n = d["INITIAL SAMPLE SIZE"].map(sum_sample_size_text)
        abs_z = p_to_abs_z(d["P-VALUE"], d["PVALUE_MLOG"])
        effect = numeric(d["OR or BETA"])
        date = pd.to_datetime(d["DATE"], errors="coerce")
        chunks.append(
            pd.DataFrame(
                {
                    "source_corpus": "gwas_catalog",
                    "field": "genetics_biomedicine",
                    "source_kind": "gwas_catalog_curated_association",
                    "published_scope": "curated_genomewide_significant_hits_not_article_results",
                    "published_original_candidate": False,
                    "comparator_only": True,
                    "row_id": "gwas_" + (i * 100_000 + np.arange(len(d))).astype(str),
                    "paper_id": "PMID:" + d["PUBMEDID"].astype(str),
                    "study_id": d["STUDY ACCESSION"].astype(str),
                    "title": d["STUDY"].astype(str),
                    "journal": d["JOURNAL"].astype(str),
                    "year": date.dt.year,
                    "outcome": d["DISEASE/TRAIT"].astype(str),
                    "effect_type": "p_value_derived_z_gwas_catalog",
                    "effect": effect,
                    "se": np.nan,
                    "z": abs_z,
                    "abs_z": abs_z,
                    "N": n,
                    "D": 2 * abs_z / np.sqrt(n),
                    "D_method": "two_sided_p_to_absz_to_2absz_sqrtN",
                    "N_method": "sum_initial_sample_size_counts",
                    "main_result_flag": "gwas_catalog_significant_association",
                    "published_flag": "published",
                    "raw_file": str(path),
                    "notes": d["P-VALUE (TEXT)"].fillna("").astype(str),
                }
            )
        )
    return finalize(pd.concat(chunks, ignore_index=True)) if chunks else pd.DataFrame()


def build_ctgov_kg(raw_dir: Path) -> pd.DataFrame:
    path = raw_dir / "ctgov_kg/efficacy_df.csv"
    if not path.exists():
        return pd.DataFrame()
    d = pd.read_csv(path, low_memory=False)
    primary = d["outcome_type"].astype(str).str.lower().eq("primary")
    p = d["p_value"].astype(str).str.extract(r"([0-9]*\.?[0-9]+(?:[eE][-+]?\d+)?)", expand=False)
    abs_z = p_to_abs_z(pd.to_numeric(p, errors="coerce"))
    n = numeric(d["enrollment_num"])
    return finalize(
        pd.DataFrame(
            {
                "source_corpus": "ctgov_finer_grained_kg",
                "field": "clinical_trials_registry",
                "source_kind": "registry_results",
                "published_scope": "clinicaltrials_gov_results",
                "published_original_candidate": False,
                "comparator_only": True,
                "row_id": "ctgovkg_" + d.index.astype(str),
                "paper_id": d["NCT_ID"].astype(str),
                "study_id": d["NCT_ID"].astype(str),
                "title": d["outcome_title"].astype(str),
                "journal": "",
                "year": numeric(d["completion_year"]),
                "outcome": d["outcome_title"].astype(str),
                "effect_type": "registry_p_value_derived_z",
                "effect": numeric(d["param_value"]),
                "se": np.nan,
                "z": abs_z,
                "abs_z": abs_z,
                "N": n,
                "D": 2 * abs_z / np.sqrt(n),
                "D_method": "registry_p_to_absz_to_2absz_sqrtN",
                "N_method": "trial_enrollment",
                "main_result_flag": np.where(primary, "primary_registry_outcome", "nonprimary_registry_outcome"),
                "published_flag": "registry",
                "raw_file": str(path),
                "notes": d["method"].fillna("").astype(str),
            }
        )
    )


def build_kuhberger(raw_dir: Path) -> pd.DataFrame:
    path = raw_dir / "kuhberger_2014/pone.0105825.s002.sav"
    if pyreadstat is None or not path.exists():
        return pd.DataFrame()

    d, meta = pyreadstat.read_sav(path, apply_value_formats=False)
    n = numeric(d.get("filter_N", pd.Series(index=d.index))).fillna(
        numeric(d.get("Nreported", pd.Series(index=d.index)))
    )
    reported_r = numeric(d.get("r", pd.Series(index=d.index)))
    reported_z = numeric(d.get("z", pd.Series(index=d.index)))
    d_from_r = reported_r.map(r_to_d_scalar)
    d_from_z = 2 * reported_z.abs() / np.sqrt(n)

    def labeled(series: pd.Series, variable: str) -> pd.Series:
        label_name = meta.variable_to_label.get(variable)
        label_map = meta.value_labels.get(label_name, {}) if label_name else {}
        values = numeric(series)
        return values.map(lambda x: label_map.get(float(x), "") if np.isfinite(x) else "")

    area = labeled(d.get("area", pd.Series(index=d.index)), "area")
    analysis = labeled(d.get("analysis", pd.Series(index=d.index)), "analysis")

    notes = (
        "area="
        + area.fillna("")
        + "; analysis="
        + analysis.fillna("")
    )
    use_r = d_from_r.notna()
    code = numeric(d.get("code1", pd.Series(index=d.index)))
    fallback_code = pd.Series(d.index, index=d.index, dtype=float)
    paper_id = "kuhberger_" + code.fillna(fallback_code).astype(int).astype(str)
    return finalize(
        pd.DataFrame(
            {
                "source_corpus": "kuhberger_2014_main_results",
                "field": "psychology",
                "source_kind": "published_original_psychology_article_main_result",
                "published_scope": "random_sample_psychology_articles",
                "published_original_candidate": True,
                "comparator_only": False,
                "row_id": paper_id,
                "paper_id": paper_id,
                "study_id": paper_id,
                "title": "",
                "journal": "",
                "year": np.nan,
                "outcome": "main result chosen to address article's main research question",
                "effect_type": np.where(use_r, "correlation_converted_to_d", "z_statistic_derived_d_proxy"),
                "effect": np.where(use_r, reported_r, reported_z),
                "se": np.nan,
                "z": reported_z,
                "N": n,
                "D": d_from_r.fillna(d_from_z),
                "D_method": np.where(use_r, "reported_r_to_d", "reported_p_to_z_to_2absz_sqrtN"),
                "N_method": np.where(d.get("filter_N", pd.Series(index=d.index)).notna(), "reported_filtered_n", "reported_n"),
                "main_result_flag": "article_main_result_selected_by_coders",
                "published_flag": "published",
                "raw_file": str(path),
                "notes": notes.str.strip("; "),
            }
        )
    )


def build_linden(raw_dir: Path) -> pd.DataFrame:
    path = raw_dir / "linden_2024/ATJ_Study2_ESs_and_Ns.sav"
    if pyreadstat is None or not path.exists():
        return pd.DataFrame()

    d, meta = pyreadstat.read_sav(path, apply_value_formats=False)
    es_label_name = meta.variable_to_label.get("ES_type")
    es_label_map = meta.value_labels.get(es_label_name, {}) if es_label_name else {}
    es_type = numeric(d.get("ES_type", pd.Series(index=d.index))).map(
        lambda x: es_label_map.get(float(x), "") if np.isfinite(x) else ""
    )
    paper_id = d["Year"].astype(int).astype(str) + "_" + d["Paper"].astype(int).astype(str)

    frames: list[pd.DataFrame] = []
    for source_corpus, d_col, n_col, source_kind, comparator_only, flag in [
        (
            "linden_2024_focal_effects",
            "d_JH",
            "N_JH",
            "published_original_psychology_article_focal_effect",
            False,
            "focal_effect_selected_by_authors",
        ),
        (
            "linden_2024_random_effects",
            "d_random",
            "N_random",
            "published_original_psychology_article_random_effect",
            True,
            "random_effect_same_paper",
        ),
    ]:
        effect = numeric(d.get(d_col, pd.Series(index=d.index)))
        n = numeric(d.get(n_col, pd.Series(index=d.index)))
        frames.append(
            pd.DataFrame(
                {
                    "source_corpus": source_corpus,
                    "field": "psychology",
                    "source_kind": source_kind,
                    "published_scope": "random_sample_psychology_articles",
                    "published_original_candidate": True,
                    "comparator_only": comparator_only,
                    "row_id": source_corpus + "_" + paper_id,
                    "paper_id": "linden_" + paper_id,
                    "study_id": "linden_" + paper_id,
                    "title": "",
                    "journal": "",
                    "year": numeric(d.get("Year", pd.Series(index=d.index))),
                    "outcome": "focal effect" if not comparator_only else "random effect",
                    "effect_type": "author_converted_d",
                    "effect": effect,
                    "se": np.nan,
                    "z": np.nan,
                    "N": n,
                    "D": effect.abs(),
                    "D_method": "reported_author_converted_d",
                    "N_method": "reported_sample_size",
                    "main_result_flag": flag,
                    "published_flag": "published",
                    "raw_file": str(path),
                    "notes": "es_type=" + es_type.fillna(""),
                }
            )
        )
    return finalize(pd.concat(frames, ignore_index=True))


def build_motyl(raw_dir: Path) -> pd.DataFrame:
    path = raw_dir / "motyl_2017/ScienceStatus_C.csv"
    if not path.exists():
        return pd.DataFrame()

    with path.open("r", encoding="latin1", newline="") as f:
        rows = list(csv.reader(f))
    if not rows:
        return pd.DataFrame()
    d = pd.DataFrame(rows[1:], columns=rows[0])
    keep = numeric(d.get("Keep", pd.Series(index=d.index))).eq(1)
    d = d.loc[keep].copy()
    if d.empty:
        return pd.DataFrame()

    n = numeric(d.get("sample.size", pd.Series(index=d.index)))
    stat_text = d.get("copied.statistic", pd.Series("", index=d.index)).map(normalize_ascii_stat_text)
    effect_text = d.get("effect.size", pd.Series("", index=d.index)).map(normalize_ascii_stat_text)
    p_text = d.get("p.exact.value", pd.Series("", index=d.index)).map(normalize_ascii_stat_text)
    p_type = d.get("p.exact", pd.Series("", index=d.index)).map(normalize_ascii_stat_text)

    stat_parsed = pd.DataFrame(
        [parse_stat_text_to_d(text, n_val) for text, n_val in zip(stat_text, n, strict=False)],
        index=d.index,
        columns=["D_stat", "z_stat", "effect_type_stat", "D_method_stat"],
    )
    effect_parsed = pd.DataFrame(
        [effect_type_value_to_d(text, text) for text in effect_text],
        index=d.index,
        columns=["D_effect", "effect_type_effect", "D_method_effect"],
    )
    p_parsed = pd.DataFrame(
        [
            p_to_d_proxy_from_text(p_val, n_val, p_kind, None)
            for p_val, n_val, p_kind in zip(p_text, n, p_type, strict=False)
        ],
        index=d.index,
        columns=["D_p", "z_p", "D_method_p"],
    )

    D = stat_parsed["D_stat"].fillna(effect_parsed["D_effect"]).fillna(p_parsed["D_p"])
    z = stat_parsed["z_stat"].fillna(p_parsed["z_p"])
    effect_type = (
        stat_parsed["effect_type_stat"]
        .where(stat_parsed["D_stat"].notna())
        .fillna(effect_parsed["effect_type_effect"].where(effect_parsed["D_effect"].notna()))
        .fillna(pd.Series(np.where(p_parsed["D_p"].notna(), "p_value_derived_d_proxy", ""), index=d.index))
    )
    d_method = (
        stat_parsed["D_method_stat"]
        .where(stat_parsed["D_stat"].notna())
        .fillna(effect_parsed["D_method_effect"].where(effect_parsed["D_effect"].notna()))
        .fillna(p_parsed["D_method_p"])
    )
    direct_effect = numeric(effect_text)
    effect_value = direct_effect.where(effect_parsed["D_effect"].notna()).fillna(z)

    article_id = d.get("article.id", pd.Series(d.index, index=d.index)).astype(str).str.strip()
    study_num = d.get("study.number", pd.Series("", index=d.index)).astype(str).str.strip()
    fallback_study = d.index.astype(str)
    study_num = study_num.mask(study_num.eq(""), fallback_study)
    paper_id = "motyl_article_" + article_id
    study_id = paper_id + "_study_" + study_num
    notes = (
        "type="
        + d.get("type", pd.Series("", index=d.index)).fillna("").astype(str)
        + "; test="
        + d.get("which.statistical.test", pd.Series("", index=d.index)).fillna("").astype(str)
        + "; design="
        + d.get("design", pd.Series("", index=d.index)).fillna("").astype(str)
        + "; study_number="
        + study_num
    )

    return finalize(
        pd.DataFrame(
            {
                "source_corpus": "motyl_2017_critical_tests",
                "field": "psychology_social_personality",
                "source_kind": "published_original_article_critical_hypothesized_test",
                "published_scope": "sampled_social_personality_journal_articles",
                "published_original_candidate": True,
                "comparator_only": False,
                "row_id": study_id,
                "paper_id": paper_id,
                "study_id": study_id,
                "title": d.get("citation", pd.Series("", index=d.index)).astype(str),
                "journal": d.get("journal", pd.Series("", index=d.index)).astype(str),
                "year": numeric(d.get("year", pd.Series(index=d.index))),
                "outcome": "critical hypothesized test selected by coders",
                "effect_type": effect_type,
                "effect": effect_value,
                "se": np.nan,
                "z": z,
                "N": n,
                "D": D,
                "D_method": d_method,
                "N_method": "reported_sample_size",
                "main_result_flag": "critical_hypothesized_test_per_study_selected_by_coders",
                "published_flag": "published",
                "raw_file": str(path),
                "notes": notes,
            }
        )
    )


def build_schaefer_schwarz(raw_dir: Path) -> pd.DataFrame:
    base = raw_dir / "schaefer_schwarz_2019"
    without_path = base / "studies_without_prereg.xlsx"
    with_path = base / "studies_with_prereg.xlsx"
    if not without_path.exists() and not with_path.exists():
        return pd.DataFrame()

    frames: list[pd.DataFrame] = []

    if without_path.exists():
        d = pd.read_excel(without_path)
        paper_id = "schaefer_2019_np_" + d["ID"].astype(str)
        r_total = numeric(d.get("r_total", pd.Series(index=d.index)))
        notes = (
            "subdiscipline="
            + d.get("subdiscipline", pd.Series("", index=d.index)).fillna("").astype(str)
            + "; study_type="
            + d.get("study_type", pd.Series("", index=d.index)).fillna("").astype(str)
            + "; population="
            + d.get("population", pd.Series("", index=d.index)).fillna("").astype(str)
            + "; design="
            + d.get("design", pd.Series("", index=d.index)).fillna("").astype(str)
            + "; reported_effect_size="
            + numeric(d.get("effect_size", pd.Series(index=d.index))).fillna(-1).astype(int).astype(str)
        )
        frames.append(
            pd.DataFrame(
                {
                    "source_corpus": "schaefer_schwarz_2019_without_prereg",
                    "field": "psychology",
                    "source_kind": "published_original_psychology_article_key_effect",
                    "published_scope": "random_sample_psychology_articles",
                    "published_original_candidate": True,
                    "comparator_only": False,
                    "row_id": paper_id,
                    "paper_id": paper_id,
                    "study_id": paper_id,
                    "title": "",
                    "journal": "",
                    "year": numeric(d.get("year", pd.Series(index=d.index))),
                    "outcome": "first effect tied to the article's key research question",
                    "effect_type": "pearson_r_converted_to_d",
                    "effect": r_total,
                    "se": np.nan,
                    "z": np.nan,
                    "N": numeric(d.get("N", pd.Series(index=d.index))),
                    "D": r_total.map(r_to_d_scalar),
                    "D_method": "reported_or_derived_r_total_to_d",
                    "N_method": "reported_n",
                    "main_result_flag": "key_research_question_first_effect_selected_by_authors",
                    "published_flag": "published",
                    "raw_file": str(without_path),
                    "notes": notes,
                }
            )
        )

    if with_path.exists():
        d = pd.read_excel(with_path)
        paper_id = "schaefer_2019_preg_" + d.index.astype(str)
        r_total = numeric(d.get("r_total", pd.Series(index=d.index)))
        notes = (
            "study_type="
            + d.get("study_type", pd.Series("", index=d.index)).fillna("").astype(str)
            + "; study_kind="
            + d.get("study_kind", pd.Series("", index=d.index)).fillna("").astype(str)
            + "; registered_report="
            + numeric(d.get("registered_report", pd.Series(index=d.index))).fillna(-1).astype(int).astype(str)
            + "; population="
            + d.get("population", pd.Series("", index=d.index)).fillna("").astype(str)
            + "; designs="
            + d.get("designs", pd.Series("", index=d.index)).fillna("").astype(str)
            + "; reported_effect_size="
            + numeric(d.get("effect_size", pd.Series(index=d.index))).fillna(-1).astype(int).astype(str)
        )
        frames.append(
            pd.DataFrame(
                {
                    "source_corpus": "schaefer_schwarz_2019_with_prereg",
                    "field": "psychology",
                    "source_kind": "published_original_psychology_article_key_effect",
                    "published_scope": "sampled_preregistered_psychology_articles",
                    "published_original_candidate": True,
                    "comparator_only": False,
                    "row_id": paper_id,
                    "paper_id": paper_id,
                    "study_id": paper_id,
                    "title": "",
                    "journal": "",
                    "year": numeric(d.get("year", pd.Series(index=d.index))),
                    "outcome": "first effect tied to the article's key research question",
                    "effect_type": "pearson_r_converted_to_d",
                    "effect": r_total,
                    "se": np.nan,
                    "z": np.nan,
                    "N": numeric(d.get("N", pd.Series(index=d.index))),
                    "D": r_total.map(r_to_d_scalar),
                    "D_method": "reported_or_derived_r_total_to_d",
                    "N_method": "reported_n",
                    "main_result_flag": "key_research_question_first_effect_selected_by_authors",
                    "published_flag": "published",
                    "raw_file": str(with_path),
                    "notes": notes,
                }
            )
        )

    return finalize(pd.concat(frames, ignore_index=True)) if frames else pd.DataFrame()


def build_aczel_2018(raw_dir: Path) -> pd.DataFrame:
    path = raw_dir / "aczel_2018/non_significant_table.xlsx"
    if not path.exists():
        return pd.DataFrame()

    d = pd.read_excel(path, sheet_name="Table")
    if d.empty:
        return pd.DataFrame()

    type_col = d.get("Type of statistics", pd.Series("", index=d.index)).fillna("").astype(str)
    keep = type_col.isin(
        [
            "One Sample T-Test",
            "Paired Samples T-Test",
            "Independent Samples T-Test",
        ]
    )
    d = d.loc[keep].copy()
    if d.empty:
        return pd.DataFrame()

    n1 = numeric(d.get("N1", pd.Series(index=d.index)))
    n2 = numeric(d.get("N2", pd.Series(index=d.index))).fillna(0)
    t = numeric(d.get("t", pd.Series(index=d.index)))
    independent = type_col.loc[d.index].eq("Independent Samples T-Test") & n2.gt(0)
    dfree = pd.Series(np.nan, index=d.index, dtype=float)
    dfree.loc[independent] = n1.loc[independent] + n2.loc[independent] - 2
    paired_or_one = ~independent
    dfree.loc[paired_or_one & n1.gt(1)] = n1.loc[paired_or_one & n1.gt(1)] - 1
    n_total = (n1 + n2).where(independent, n1)

    D_t = 2 * t.abs() / np.sqrt(dfree)
    p = numeric(d.get("p", pd.Series(index=d.index)))
    p_parsed = pd.DataFrame(
        [p_to_d_proxy_from_text(p_val, n_val) for p_val, n_val in zip(p, n_total, strict=False)],
        index=d.index,
        columns=["D_p", "z_p", "D_method_p"],
    )

    D = D_t.fillna(p_parsed["D_p"])
    z = p_parsed["z_p"]
    d_method = pd.Series(np.where(D_t.notna(), "2_abs_t_over_sqrt_inferred_df", ""), index=d.index)
    d_method = d_method.where(D_t.notna(), p_parsed["D_method_p"])
    notes = (
        "type_of_statistics="
        + type_col.loc[d.index]
        + "; category="
        + d.get("Category", pd.Series("", index=d.index)).fillna("").astype(str)
        + "; p="
        + d.get("p", pd.Series("", index=d.index)).fillna("").astype(str)
    )

    article_id = d.get("Article ID", pd.Series(d.index, index=d.index)).astype(str).str.strip()
    statement_id = d.get("Statement ID", pd.Series("", index=d.index)).astype(str).str.strip()
    stat_id = d.get("Stat ID", pd.Series("", index=d.index)).astype(str).str.strip()
    row_id = (
        "aczel_2018_article_"
        + article_id
        + "_statement_"
        + statement_id
        + "_stat_"
        + stat_id
    )
    paper_id = "aczel_2018_article_" + article_id
    year = (
        d.get("Reference", pd.Series("", index=d.index))
        .astype(str)
        .str.extract(r"\((\d{4})\)", expand=False)
        .map(to_num)
    )

    return finalize(
        pd.DataFrame(
            {
                "source_corpus": "aczel_2018_negative_claim_ttests",
                "field": "psychology",
                "source_kind": "published_article_negative_claim_ttest",
                "published_scope": "sampled_psychology_articles_with_negative_abstract_claims",
                "published_original_candidate": False,
                "comparator_only": True,
                "row_id": row_id,
                "paper_id": paper_id,
                "study_id": row_id,
                "title": d.get("Reference", pd.Series("", index=d.index)).astype(str),
                "journal": "",
                "year": year,
                "outcome": "negative abstract/result claim linked to a nonsignificant t-test",
                "effect_type": "t_statistic_derived_d",
                "effect": t,
                "se": np.nan,
                "z": z,
                "N": n_total,
                "D": D,
                "D_method": d_method,
                "N_method": "reported_n1_n2_or_n1_only",
                "main_result_flag": "negative_claim_linked_ttest_selected_by_authors",
                "published_flag": "published",
                "raw_file": str(path),
                "notes": notes,
            }
        )
    )


def build_olsson_sundell_2023(raw_dir: Path) -> pd.DataFrame:
    path = raw_dir / "olsson_sundell_2023" / "pone.0281110.s003.xlsx"
    if not path.exists():
        path = ROOT / "data" / "raw" / "publication_bias_direct" / "olsson_sundell_2023" / "pone.0281110.s003.xlsx"
    if not path.exists():
        return pd.DataFrame()

    d = pd.read_excel(path, sheet_name="NEW")
    if d.empty:
        return pd.DataFrame()

    n = numeric(d.get("Nanalys", pd.Series(index=d.index)))
    effect = numeric(d.get("Cohens_d", pd.Series(index=d.index)))
    primary = numeric(d.get("f7_prim_outcome", pd.Series(index=d.index))).fillna(0).eq(1)
    rct = numeric(d.get("rct", pd.Series(index=d.index))).fillna(0).eq(1)
    sign_flag = numeric(d.get("f25_Sign_effekt", pd.Series(index=d.index)))
    rct_text = pd.Series(np.where(rct, "1", "0"), index=d.index)
    primary_text = pd.Series(np.where(primary, "1", "0"), index=d.index)

    notes = (
        "rct="
        + rct_text
        + "; primary_outcome="
        + primary_text
        + "; significant_effect="
        + sign_flag.fillna(-1).astype(int).astype(str)
        + "; age="
        + d.get("age", pd.Series("", index=d.index)).fillna("").astype(str)
        + "; prevention_type="
        + d.get("f12_prevtyp", pd.Series("", index=d.index)).fillna("").astype(str)
        + "; publication_months="
        + d.get("pubmon", pd.Series("", index=d.index)).fillna("").astype(str)
    )

    return finalize(
        pd.DataFrame(
            {
                "source_corpus": "olsson_sundell_2023_social_interventions",
                "field": "social_intervention_research",
                "source_kind": "published_original_article_effectiveness_result",
                "published_scope": "published_swedish_social_intervention_articles",
                "published_original_candidate": primary,
                "comparator_only": ~primary,
                "row_id": "olsson_sundell_2023_" + d["Obs"].astype(str),
                "paper_id": "olsson_sundell_2023_" + d["Obs"].astype(str),
                "study_id": "olsson_sundell_2023_" + d["Obs"].astype(str),
                "title": "",
                "journal": "",
                "year": np.nan,
                "outcome": np.where(primary, "primary outcome effectiveness result", "effectiveness result not flagged primary"),
                "effect_type": "cohens_d",
                "effect": effect,
                "se": np.nan,
                "z": np.nan,
                "N": n,
                "D": effect.abs(),
                "D_method": "reported_cohens_d",
                "N_method": "reported_analytic_sample_size",
                "main_result_flag": np.where(
                    primary,
                    "primary_outcome_flagged_by_coders",
                    "not_primary_outcome_flagged_by_coders",
                ),
                "published_flag": "published",
                "raw_file": str(path),
                "notes": notes,
            }
        )
    )


BUILDERS: list[tuple[str, Callable[[Path], pd.DataFrame]]] = [
    ("score_cos_claims", build_score),
    ("forrt_fred", build_fred),
    ("esarey_wu_2016_political_science_main_findings", build_esarey_wu_2016),
    ("kuhberger_2014_main_results", build_kuhberger),
    ("linden_2024_focal_effects", build_linden),
    ("motyl_2017_critical_tests", build_motyl),
    ("schaefer_schwarz_2019", build_schaefer_schwarz),
    ("aczel_2018_negative_claim_ttests", build_aczel_2018),
    ("olsson_sundell_2023_social_interventions", build_olsson_sundell_2023),
    ("yun_llm_meta_analysis", build_yun),
    ("clinifact_published_primary_pairs", build_clinifact_published_primary_pairs),
    ("dellavigna_linos_2022", build_dellavigna),
    ("economics_brodeur_2024", build_brodeur_2024),
    ("turner_antidepressants_2022", build_turner),
    ("metabus_open_bosco", build_metabus),
    ("button_nord_neuroscience", build_button_nord),
    ("rpcb_cancer_biology", build_rpcb),
    ("szucs_ioannidis_2017", build_szucs),
    ("havranek_meta_analysis", build_havranek),
    ("gwas_catalog", build_gwas),
    ("ctgov_finer_grained_kg", build_ctgov_kg),
]


def collapse_rows(rows: pd.DataFrame, group_col: str) -> pd.DataFrame:
    data = rows[rows[group_col].astype(str).ne("")].copy()
    if data.empty:
        return pd.DataFrame()
    group_cols = ["source_corpus", "field", "source_kind", "published_scope", group_col]
    out = (
        data.groupby(group_cols, dropna=False)
        .agg(
            D_median=("abs_D", "median"),
            N_median=("N", "median"),
            abs_z_median=("abs_z", "median"),
            n_rows=("abs_D", "size"),
            published_original_candidate=("published_original_candidate", "max"),
            comparator_only=("comparator_only", "max"),
            title=("title", lambda x: x.dropna().astype(str).iloc[0] if len(x.dropna()) else ""),
            journal=("journal", lambda x: x.dropna().astype(str).mode().iloc[0] if len(x.dropna()) else ""),
            year=("year", "median"),
            D_methods=("D_method", lambda x: ";".join(sorted(set(x.dropna().astype(str))))),
            N_methods=("N_method", lambda x: ";".join(sorted(set(x.dropna().astype(str))))),
        )
        .reset_index()
    )
    out = out.rename(columns={group_col: "unit_id"})
    out["collapse_unit"] = group_col
    out["log10_N"] = np.log10(out["N_median"].where(out["N_median"] > 0))
    out["log10_D"] = np.log10(out["D_median"].where(out["D_median"] > 0))
    return out


def corpus_summary(rows: pd.DataFrame) -> pd.DataFrame:
    def med(x: pd.Series) -> float:
        values = pd.to_numeric(x, errors="coerce").dropna()
        return float(values.median()) if len(values) else np.nan

    return (
        rows.groupby(["source_corpus", "field", "source_kind", "published_scope"], dropna=False)
        .agg(
            n_rows=("abs_D", "size"),
            n_papers=("paper_id", lambda x: x.astype(str).replace("", np.nan).nunique()),
            n_studies=("study_id", lambda x: x.astype(str).replace("", np.nan).nunique()),
            median_D=("abs_D", med),
            median_N=("N", med),
            median_abs_z=("abs_z", med),
            published_original_rows=("published_original_candidate", "sum"),
            comparator_rows=("comparator_only", "sum"),
        )
        .reset_index()
        .sort_values(["published_original_rows", "n_rows"], ascending=False)
    )


def covariate_medians(rows: pd.DataFrame) -> pd.DataFrame:
    covars = ["source_corpus", "field", "source_kind", "published_scope", "effect_type", "main_result_flag", "published_flag"]
    frames = []
    for covar in covars:
        g = (
            rows.groupby(covar, dropna=False)
            .agg(n_rows=("abs_D", "size"), median_D=("abs_D", "median"), median_N=("N", "median"), median_abs_z=("abs_z", "median"))
            .reset_index()
            .rename(columns={covar: "value"})
        )
        g.insert(0, "covariate", covar)
        frames.append(g)
    return pd.concat(frames, ignore_index=True).sort_values(["covariate", "n_rows"], ascending=[True, False])


def write_outputs(rows: pd.DataFrame, out_dir: Path) -> None:
    ensure_dir(out_dir)
    rows.to_csv(out_dir / "candidate_d_n_rows.csv.gz", index=False)
    rows.to_parquet(out_dir / "candidate_d_n_rows.parquet", index=False)

    papers = collapse_rows(rows, "paper_id")
    studies = collapse_rows(rows, "study_id")
    papers.to_csv(out_dir / "candidate_d_n_papers.csv", index=False)
    papers.to_parquet(out_dir / "candidate_d_n_papers.parquet", index=False)
    studies.to_csv(out_dir / "candidate_d_n_studies.csv", index=False)

    summary = corpus_summary(rows)
    covars = covariate_medians(rows)
    summary.to_csv(out_dir / "candidate_d_n_corpus_summary.csv", index=False)
    covars.to_csv(out_dir / "candidate_d_n_covariate_medians.csv", index=False)

    main_rows = rows[rows["published_original_candidate"] & ~rows["comparator_only"]].copy()
    main_papers = papers[papers["published_original_candidate"] & ~papers["comparator_only"]].copy()

    lines = [
        "# Candidate D-vs-N Build Summary",
        "",
        f"Row-level usable D/N rows: {len(rows):,}",
        f"Published-original-candidate rows: {len(main_rows):,}",
        f"Collapsed paper units: {len(papers):,}",
        f"Published-original-candidate paper units: {len(main_papers):,}",
        "",
        "## Corpus Coverage",
        "",
        summary.to_markdown(index=False),
        "",
        "## Important Caveats",
        "",
        "- `published_original_candidate` means the row can plausibly serve the main published-paper D-vs-N question. It does not mean the row is already selected as the primary outcome.",
        "- GWAS rows are curated genome-wide-significant association hits linked to published papers, not sampled article-level journal results. They are retained as a threshold-selection comparator, not as a main published-paper corpus.",
        "- Szucs & Ioannidis rows are usable as row-level test statistics, but journal/paper grouping from the MATLAB table is not decoded yet.",
        "- SCORE rows are focal/representative social-behavioral claims. The structured `orig_outcomes` rows are more reliable than the larger free-text extracted-claims rows; free-text p-threshold rows are lower-bound D proxies.",
        "- FReD rows are original claims selected for replication. They are closer to focal claims than all-reported-test corpora, but they are not a random sample of journal articles and not always treatment effects.",
        "- Cochrane, ClinicalTrials.gov, Turner FDA rows, RPCB replications, and unpublished Nudge Unit rows are retained as comparators, not as the main published-paper cloud.",
        "- Havranek datasets are meta-analysis extracted estimates; rows with the local published flag are marked as published candidates, but the paper should describe that they are curated meta-analysis source estimates.",
        "",
        "## Files",
        "",
        "- `candidate_d_n_rows.csv.gz`: row-level normalized results.",
        "- `candidate_d_n_papers.csv`: median D/N by `paper_id`.",
        "- `candidate_d_n_studies.csv`: median D/N by `study_id`.",
        "- `candidate_d_n_corpus_summary.csv`: corpus-level counts and medians.",
        "- `candidate_d_n_covariate_medians.csv`: one-way medians for available covariates.",
    ]
    (out_dir / "candidate_d_n_summary.md").write_text("\n".join(lines) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-dir", type=Path, default=Path("data/raw/corpus_candidates"))
    parser.add_argument("--out-dir", type=Path, default=Path("data/derived/corpus_candidates"))
    parser.add_argument("--interim-dir", type=Path, default=Path("data/interim/corpus_candidates"))
    parser.add_argument("--skip-gwas", action="store_true", help="Skip the large GWAS TSV parser.")
    parser.add_argument("--skip-ctgov", action="store_true", help="Skip the registry comparator parser.")
    args = parser.parse_args()

    ensure_dir(args.interim_dir)
    frames: list[pd.DataFrame] = []
    failures: list[str] = []
    for name, builder in BUILDERS:
        if args.skip_gwas and name == "gwas_catalog":
            continue
        if args.skip_ctgov and name == "ctgov_finer_grained_kg":
            continue
        try:
            if name == "metalab":
                frame = build_metalab(args.raw_dir, args.interim_dir)
            else:
                # build_metalab has a different signature; it is not listed in
                # BUILDERS because it needs the interim directory.
                frame = builder(args.raw_dir)
        except Exception as exc:
            failures.append(f"{name}: {type(exc).__name__}: {exc}")
            continue
        if frame is not None and not frame.empty:
            frames.append(frame)

    metalab = build_metalab(args.raw_dir, args.interim_dir)
    if not metalab.empty:
        frames.append(metalab)
    else:
        failures.append("metalab: skipped or failed RData export")

    if not frames:
        raise SystemExit("No candidate corpora produced usable D/N rows.")
    rows = pd.concat(frames, ignore_index=True)
    write_outputs(rows, args.out_dir)

    if failures:
        failure_path = args.out_dir / "candidate_d_n_failures.txt"
        failure_path.write_text("\n".join(failures) + "\n")
        print(f"Wrote failures to {failure_path}")
    else:
        failure_path = args.out_dir / "candidate_d_n_failures.txt"
        if failure_path.exists():
            failure_path.unlink()
    print(f"Wrote {len(rows):,} normalized D/N rows to {args.out_dir}")


if __name__ == "__main__":
    main()
