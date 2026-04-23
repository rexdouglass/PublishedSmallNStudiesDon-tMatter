#!/usr/bin/env python3
"""Build a draft Figure 2 from on-hand project-specific replication pair tables."""

from __future__ import annotations

import importlib.util
import math
import re
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pyreadr
from bs4 import BeautifulSoup
from matplotlib.lines import Line2D
from matplotlib.ticker import FixedFormatter, FixedLocator, NullFormatter
from matplotlib.transforms import blended_transform_factory
from scipy.stats import norm, t as student_t


ROOT = Path(__file__).resolve().parents[1]


def resolve_appendix_html() -> Path:
    preferred = ROOT / "docs" / "nightmare-hellscape (1).html"
    if preferred.exists():
        return preferred
    matches = sorted((ROOT / "docs").glob("nightmare-hellscape (*.html"))
    if matches:
        return matches[-1]
    return preferred


APPENDIX_HTML = resolve_appendix_html()
RAW_CAND = ROOT / "data" / "raw" / "corpus_candidates"
RAW_REPL = ROOT / "data" / "raw" / "replication_projects"
DERIVED = ROOT / "data" / "derived" / "replication_pairs"
REPORTS = ROOT / "reports" / "corpus_candidates"
HARVEST = DERIVED / "harvest"
HARVEST_PROMOTED = HARVEST / "promoted"
HARVEST_MANIFEST = HARVEST / "harvest_manifest.csv"
Z_05 = 1.959963984540054
Z_10 = 1.6448536269514722
Z_01 = 2.5758293035489004
NUM_RE = r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:e[-+]?\d+)?"

SITE_LEVEL_REPLICATION_SOURCES = {
    "RRR McCarthy 2018 site csvs",
    "O'Donnell 2018 site-level meta csvs",
    "Vaidis 2024 prepared data subset",
    "Alogna 2014 table 1 site counts",
    "RRR Cheung 2016 site csvs",
    "RRR Verschuere 2018 site csv",
    "Stoevenbelt 2025 combined lab csv",
    "PSA-006 trolley country rows",
    "PSA-002 object orientation lab rows",
    "Wagenmakers 2016 site csv",
    "Hagger 2016 RTV.csv",
    "Eerland 2016 Intentionality.csv",
    "Eerland 2016 Intention_attribution.csv",
    "Eerland 2016 imagery.csv",
}

MANUAL_SITE_SHADOWS = {
    "RRR O'Donnell 2018 (manual)": "O'Donnell 2018 site-level meta csvs",
    "RRR Wagenmakers 2016 (manual)": "Wagenmakers 2016 site csv",
    "RRR Cheung 2016 (manual)": "RRR Cheung 2016 site csvs",
    "RRR Verschuere 2018 (manual)": "RRR Verschuere 2018 site csv",
    "Srull-Wyer RRR paper (manual)": "RRR McCarthy 2018 site csvs",
    "RRR Hagger 2016 (manual)": "Hagger 2016 RTV.csv",
    "RRR Alogna 2014 (manual)": "Alogna 2014 table 1 site counts",
}


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def load_candidate_helpers():
    spec = importlib.util.spec_from_file_location(
        "build_candidate_d_vs_n", ROOT / "scripts" / "build_candidate_d_vs_n.py"
    )
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


HELPERS = load_candidate_helpers()


def two_sample_z_boundary(n: np.ndarray | pd.Series | float, z_crit: float) -> np.ndarray:
    n = np.asarray(n, dtype=float)
    return 2 * z_crit / np.sqrt(n)


def p10_boundary(n: np.ndarray | pd.Series | float) -> np.ndarray:
    return two_sample_z_boundary(n, Z_10)


def p05_boundary(n: np.ndarray | pd.Series | float) -> np.ndarray:
    return two_sample_z_boundary(n, Z_05)


def p01_boundary(n: np.ndarray | pd.Series | float) -> np.ndarray:
    return two_sample_z_boundary(n, Z_01)


def nice_log_upper(value: float) -> float:
    if not np.isfinite(value) or value <= 0:
        return 1.0
    exponent = math.floor(math.log10(value))
    scaled = value / (10**exponent)
    for step in (1, 2, 5, 10):
        if scaled <= step:
            return step * (10**exponent)
    return 10 ** (exponent + 1)


def nice_log_lower(value: float) -> float:
    if not np.isfinite(value) or value <= 0:
        return 0.001
    exponent = math.floor(math.log10(value))
    scaled = value / (10**exponent)
    for step in (10, 5, 2, 1):
        if scaled >= step:
            return step * (10**exponent)
    return 10 ** (exponent - 1)


def format_n_tick(value: float) -> str:
    if value >= 1_000_000:
        out = f"{value / 1_000_000:g}M"
    elif value >= 1_000:
        out = f"{value / 1_000:g}k"
    else:
        out = f"{value:g}"
    return out.replace(".0", "")


def format_d_tick(value: float) -> str:
    if value >= 1:
        return str(int(value)) if float(value).is_integer() else f"{value:g}"
    if value >= 0.01:
        return f"{value:.2f}".rstrip("0").rstrip(".")
    if value >= 0.001:
        return f"{value:.3f}".rstrip("0").rstrip(".")
    return f"{value:g}"


def slugify(text: object) -> str:
    s = str(text or "").strip().lower()
    s = re.sub(r"[^a-z0-9]+", "_", s)
    return s.strip("_") or "missing"


def scalar_r_to_d(value: float) -> float:
    if not np.isfinite(value):
        return np.nan
    return abs(HELPERS.r_to_d_scalar(value))


def fisher_z_abs_to_d(value: float) -> float:
    if not np.isfinite(value):
        return np.nan
    return scalar_r_to_d(math.tanh(abs(value)))


def log_ratio_abs(value: float) -> float:
    if not (np.isfinite(value) and value > 0):
        return np.nan
    return abs(math.log(value))


def odds_ratio_to_d(value: float) -> float:
    if not (np.isfinite(value) and value > 0):
        return np.nan
    return abs(math.log(value)) * math.sqrt(3) / math.pi


def d_from_t_df(stat_t: float, df: float) -> float:
    if not (np.isfinite(stat_t) and np.isfinite(df) and df > 0):
        return np.nan
    return abs(2 * stat_t / math.sqrt(df))


def d_from_f_df(stat_f: float, df: float) -> float:
    if not (np.isfinite(stat_f) and np.isfinite(df) and df > 0):
        return np.nan
    return abs(2 * math.sqrt(stat_f) / math.sqrt(df))


def d_from_mean_diff_se(effect: float, se: float, n_total: float) -> float:
    if not (np.isfinite(effect) and np.isfinite(se) and se > 0 and np.isfinite(n_total) and n_total > 0):
        return np.nan
    return abs(2 * effect / (se * math.sqrt(n_total)))


def pooled_d_from_summary(
    mean_1: float, sd_1: float, n_1: float, mean_2: float, sd_2: float, n_2: float
) -> float:
    vals = [mean_1, sd_1, n_1, mean_2, sd_2, n_2]
    if not all(np.isfinite(v) for v in vals):
        return np.nan
    if min(n_1, n_2) <= 1 or min(sd_1, sd_2) < 0:
        return np.nan
    pooled_den = n_1 + n_2 - 2
    if pooled_den <= 0:
        return np.nan
    pooled_var = ((n_1 - 1) * sd_1**2 + (n_2 - 1) * sd_2**2) / pooled_den
    if not (np.isfinite(pooled_var) and pooled_var > 0):
        return np.nan
    return abs((mean_1 - mean_2) / math.sqrt(pooled_var))


def clean_author_key(text: object) -> str:
    s = HELPERS.normalize_ascii_stat_text(text).strip().lower()
    if not s:
        return ""
    s = re.sub(r"^rpp\s+", "", s)
    s = re.sub(r"^study\s+\d+\s*-\s*", "", s)
    s = re.sub(r"\bet\s+al\.?.*$", "", s)
    s = s.split(",", 1)[0].strip()
    if not s:
        return ""
    parts = [part for part in re.split(r"[^a-z0-9]+", s) if part]
    if not parts:
        return ""
    if len(parts) >= 2 and all(len(part) <= 3 for part in parts[:-1]):
        return parts[-1]
    return parts[0]


def student_target_base(text: object) -> str:
    return re.sub(r"_[0-9]+$", "", str(text or "").strip().lower())


def assign_match_keys(df: pd.DataFrame, author_col: str) -> pd.DataFrame:
    out = df.copy()
    if author_col not in out.columns:
        out["match_key"] = ""
        return out

    out["_match_author"] = out[author_col].map(clean_author_key)
    nonempty = out["_match_author"].ne("")
    if nonempty.any():
        ranked = out.loc[nonempty].sort_values(
            ["project", "_match_author", "D_original", "N_original", "D_replication", "N_replication", "pair_id"],
            ascending=[True, True, False, False, False, False, True],
        )
        ranked["_match_rank"] = ranked.groupby(["project", "_match_author"]).cumcount() + 1
        out.loc[ranked.index, "_match_rank"] = ranked["_match_rank"]
    out["_match_rank"] = out["_match_rank"].fillna(0).astype(int)
    out["match_key"] = np.where(
        nonempty,
        out["project"].map(slugify) + "__" + out["_match_author"] + "__" + out["_match_rank"].astype(str),
        "",
    )
    return out.drop(columns=["_match_author", "_match_rank"])


def extract_effect_number(text: object) -> float:
    if pd.isna(text):
        return np.nan
    s = HELPERS.normalize_ascii_stat_text(text)
    if "=" in s:
        s = s.split("=", 1)[1]
    match = re.search(NUM_RE, s)
    if not match:
        return np.nan
    return float(match.group(0).replace(" ", ""))


def parse_effect_string_to_d(text: object) -> float:
    if pd.isna(text):
        return np.nan
    s = HELPERS.normalize_ascii_stat_text(text).lower().strip()
    if not s:
        return np.nan
    value = extract_effect_number(s)
    if not np.isfinite(value):
        return np.nan
    if s.startswith("partial eta2") or s.startswith("r2"):
        return scalar_r_to_d(math.sqrt(abs(value)))
    if s.startswith("dav") or re.match(r"^d\b", s):
        return abs(value)
    if re.match(r"^(r|w)\b", s):
        return scalar_r_to_d(value)
    return np.nan


def parse_test_text_to_d(text: object, n: float = np.nan) -> float:
    s = HELPERS.normalize_ascii_stat_text(text)
    d, _, _, _ = HELPERS.parse_stat_text_to_d(s, n)
    if np.isfinite(d):
        return abs(d)

    match = re.search(rf"(?i)\b(?:chi2|x2)\s*(?:\([^)]*\))?\s*=\s*({NUM_RE})", s)
    if match and np.isfinite(n) and n > 0:
        chi2 = float(match.group(1))
        return scalar_r_to_d(math.sqrt(abs(chi2) / n))

    match = re.search(rf"(?i)\bsobel(?: test)?\s*=\s*({NUM_RE})", s)
    if match and np.isfinite(n) and n > 0:
        z = float(match.group(1))
        return abs(2 * z / math.sqrt(n))

    return np.nan


def fred_effect_to_d(value: object, effect_type: object, n: float = np.nan) -> float:
    if pd.isna(value) or pd.isna(effect_type):
        return np.nan

    effect_label = str(effect_type).strip().lower()
    value_text = str(value).strip()
    numeric = pd.to_numeric(pd.Series([value_text]), errors="coerce").iloc[0]

    if effect_label in {
        "d",
        "cohen's d",
        "hedges' g",
        "smd",
        "dv",
        "dz",
        "cohen's dz",
        "standard deviation units",
    } and np.isfinite(numeric):
        return abs(float(numeric))

    if effect_label in {"f", "cohen's f"} and np.isfinite(numeric):
        # Cohen's f maps to r via r^2 = f^2 / (1 + f^2), which simplifies to d = 2f.
        return abs(2 * float(numeric))

    if effect_label in {
        "r",
        "partial correlation",
        "partial r",
        "phi",
        "cramer's v",
        "wilcoxon r",
    } and np.isfinite(numeric):
        return scalar_r_to_d(float(numeric))

    if effect_label in {
        "etasq (partial)",
        "etasq",
        "omega squared",
        "partial r-square",
        "r-squared",
    } and np.isfinite(numeric):
        x = abs(float(numeric))
        if x >= 1:
            return np.nan
        return abs(2 * math.sqrt(x / (1 - x)))

    if effect_label in {"cohen's f^2", "f-square"} and np.isfinite(numeric):
        x = abs(float(numeric))
        if x >= 1:
            return np.nan
        return abs(2 * math.sqrt(x / (1 - x)))

    if effect_label in {"or", "odds ratio", "hazard ratio"} and np.isfinite(numeric) and numeric > 0:
        if effect_label in {"or", "odds ratio"}:
            return odds_ratio_to_d(float(numeric))
        return log_ratio_abs(float(numeric))

    if effect_label == "log_odds_ratio" and np.isfinite(numeric):
        return abs(float(numeric) * math.sqrt(3) / math.pi)

    if effect_label == "relative_risk_ratio" and np.isfinite(numeric) and numeric > 0:
        return log_ratio_abs(float(numeric))

    if effect_label in {"cohen's h", "cohen's w", "kendall's w"} and np.isfinite(numeric):
        return abs(float(numeric))

    if effect_label in {"test statistic", "t"}:
        return parse_test_text_to_d(value_text, n)

    if effect_label == "z" and np.isfinite(numeric) and np.isfinite(n) and n > 0:
        return abs(2 * float(numeric) / math.sqrt(n))

    return np.nan


def sports_effect_to_d(value: object, effect_type: object) -> float:
    numeric = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
    if not np.isfinite(numeric):
        return np.nan

    effect_label = str(effect_type or "").strip().lower()
    effect_label = effect_label.replace("cohen's ", "").replace("cohen’s ", "")
    effect_label = effect_label.replace("hedges' ", "").replace("hedges’ ", "")

    if effect_label in {"d", "dav", "ds", "dz", "g"}:
        return abs(float(numeric))

    if "partial eta" in effect_label:
        x = abs(float(numeric))
        if x >= 1:
            return np.nan
        return abs(2 * math.sqrt(x / (1 - x)))

    return np.nan


def pair_frame(**kwargs) -> pd.DataFrame:
    return pd.DataFrame(kwargs)


def annotate_pair_flags(pairs: pd.DataFrame) -> pd.DataFrame:
    out = pairs.copy()
    out["original_sig_05"] = out["D_original"] >= p05_boundary(out["N_original"])
    out["replication_sig_05"] = out["D_replication"] >= p05_boundary(out["N_replication"])
    out["larger_n_replication"] = out["N_replication"] > out["N_original"]
    out["d_grew"] = out["D_replication"] > out["D_original"]
    out["d_ratio"] = np.where(out["D_original"] > 0, out["D_replication"] / out["D_original"], np.nan)
    out["n_ratio"] = out["N_replication"] / out["N_original"]
    out["category"] = np.where(
        out["d_grew"],
        "grew",
        np.where(out["replication_sig_05"], "shrunk_still_sig", "shrunk_below_sig"),
    )
    return out


def filter_usable_pairs(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for col in ["D_original", "D_replication", "N_original", "N_replication"]:
        out[col] = pd.to_numeric(out[col], errors="coerce")
    ok = (
        np.isfinite(out["D_original"])
        & np.isfinite(out["D_replication"])
        & np.isfinite(out["N_original"])
        & np.isfinite(out["N_replication"])
        & (out["N_original"] >= 4)
        & (out["N_replication"] >= 4)
        & (out["D_original"] >= 0)
        & (out["D_replication"] >= 0)
    )
    return out.loc[ok].copy()


def stable_original_key(df: pd.DataFrame) -> pd.Series:
    doi = df["original_doi"].fillna("").astype(str).str.strip()
    title = df["original_title"].fillna("").astype(str).str.strip()
    return doi.where(doi.ne(""), title)


def stable_replication_anchor(df: pd.DataFrame) -> pd.Series:
    doi = df["replication_doi"].fillna("").astype(str).str.strip()
    title = df["replication_title"].fillna("").astype(str).str.strip()
    source = df["source_dataset"].fillna("").astype(str).str.strip()
    return doi.where(doi.ne(""), source.where(source.isin(SITE_LEVEL_REPLICATION_SOURCES), title))


def stable_endpoint_key(df: pd.DataFrame) -> pd.Series:
    outcome = df["outcome"].fillna("").astype(str).str.strip()
    repl_title = df["replication_title"].fillna("").astype(str).str.strip()
    orig_title = df["original_title"].fillna("").astype(str).str.strip()
    return outcome.where(outcome.ne(""), repl_title.where(repl_title.ne(""), orig_title))


def drop_shadowed_manual_aggregates(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df.copy()
    out = df.copy()
    if "_orig_key" not in out.columns:
        out["_orig_key"] = stable_original_key(out)

    keep = np.ones(len(out), dtype=bool)
    for idx, (_, row) in enumerate(out.iterrows()):
        site_source = MANUAL_SITE_SHADOWS.get(str(row["source_dataset"]))
        if not site_source:
            continue
        has_site = (
            (out["_orig_key"] == row["_orig_key"])
            & (out["project"] == row["project"])
            & (out["source_dataset"] == site_source)
        ).any()
        if has_site:
            keep[idx] = False
    return out.loc[keep].copy()


def collapse_endpoint_pairs(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df.copy()

    out = df.copy()
    out["_orig_key"] = stable_original_key(out)
    out["_rep_anchor"] = stable_replication_anchor(out)
    out["_endpoint_key"] = stable_endpoint_key(out)

    group_cols = ["project", "_orig_key", "_rep_anchor", "_endpoint_key", "D_original", "N_original"]
    rows: list[pd.Series] = []

    for _, g in out.groupby(group_cols, dropna=False, sort=False):
        if len(g) == 1:
            row = g.iloc[0].copy()
            row["component_rows"] = 1
            rows.append(row)
            continue

        row = g.iloc[0].copy()
        weights = pd.to_numeric(g["N_replication"], errors="coerce").to_numpy(dtype=float)
        effects = pd.to_numeric(g["D_replication"], errors="coerce").to_numpy(dtype=float)
        valid = np.isfinite(weights) & np.isfinite(effects) & (weights > 0)
        if valid.any():
            d_rep = float(np.average(effects[valid], weights=weights[valid]))
        else:
            d_rep = float(np.nanmean(effects))

        row["pair_id"] = f"{row['pair_id']}__endpoint"
        row["D_replication"] = abs(d_rep)
        row["N_replication"] = float(np.nansum(pd.to_numeric(g["N_replication"], errors="coerce")))
        row["component_rows"] = len(g)
        rows.append(row)

    collapsed = pd.DataFrame(rows)
    collapsed = drop_shadowed_manual_aggregates(collapsed)
    collapsed = collapsed.drop(columns=["_orig_key", "_rep_anchor", "_endpoint_key"], errors="ignore")
    return collapsed.reset_index(drop=True)


def build_harvested_lead_pairs() -> pd.DataFrame:
    required_cols = [
        "source_dataset",
        "project",
        "pair_id",
        "original_title",
        "replication_title",
        "original_doi",
        "replication_doi",
        "outcome",
        "D_original",
        "N_original",
        "D_replication",
        "N_replication",
        "raw_file",
        "match_author",
    ]
    frames: list[pd.DataFrame] = []
    if not HARVEST_PROMOTED.exists():
        return pair_frame(**{col: [] for col in required_cols})

    for path in sorted(HARVEST_PROMOTED.glob("*.csv")):
        try:
            d = pd.read_csv(path)
        except Exception:
            continue
        if d.empty:
            continue

        d = d.copy()
        if "source_dataset" not in d.columns:
            d["source_dataset"] = path.stem
        if "project" not in d.columns:
            d["project"] = "Harvested leads"
        if "pair_id" not in d.columns:
            d["pair_id"] = [f"{path.stem}_{i}" for i in range(len(d))]
        if "original_title" not in d.columns:
            d["original_title"] = ""
        if "replication_title" not in d.columns:
            d["replication_title"] = ""
        if "original_doi" not in d.columns:
            d["original_doi"] = ""
        if "replication_doi" not in d.columns:
            d["replication_doi"] = ""
        if "outcome" not in d.columns:
            d["outcome"] = ""
        if "raw_file" not in d.columns:
            d["raw_file"] = str(path)
        else:
            d["raw_file"] = d["raw_file"].fillna("").replace("", str(path))
        if "match_author" not in d.columns:
            d["match_author"] = d.get("original_title", pd.Series("", index=d.index)).fillna("").astype(str)

        d = filter_usable_pairs(d)
        if d.empty:
            continue
        for col in required_cols:
            if col not in d.columns:
                d[col] = ""
        frames.append(d[required_cols].copy())

    if not frames:
        return pair_frame(**{col: [] for col in required_cols})
    return assign_match_keys(pd.concat(frames, ignore_index=True), "match_author")


def build_rpp_pairs() -> pd.DataFrame:
    path = RAW_REPL / "rpp" / "rpp_data_osf.csv"
    d = pd.read_csv(path, encoding="latin1", low_memory=False)
    out = pair_frame(
        source_dataset="RPP canonical OSF csv",
        project="OSC 2015",
        pair_id="rpp_" + d["Study Num"].astype(str),
        original_title=d["Study Title (O)"].fillna("").astype(str),
        replication_title=d["Project URL"].fillna("").astype(str),
        original_doi="",
        replication_doi="",
        outcome=d.get("Description of effect (O)", pd.Series("", index=d.index)).fillna("").astype(str),
        D_original=HELPERS.numeric(d["T_r..O."]).apply(scalar_r_to_d),
        N_original=HELPERS.numeric(d["T_N..O."]),
        D_replication=HELPERS.numeric(d["T_r..R."]).apply(scalar_r_to_d),
        N_replication=HELPERS.numeric(d["T_N..R."]),
        raw_file=str(path),
        match_author=d.get("1st author (O)", pd.Series("", index=d.index)).fillna("").astype(str),
    )
    return assign_match_keys(filter_usable_pairs(out), "match_author")


def build_ssrp_pairs() -> pd.DataFrame:
    path = RAW_REPL / "replicationsuccess" / "SSRP.rda"
    d = next(iter(pyreadr.read_r(path).values()))

    rep_r = pd.to_numeric(d["rr"], errors="coerce").fillna(pd.to_numeric(d["ri"], errors="coerce"))
    rep_n = pd.to_numeric(d["nr"], errors="coerce").fillna(pd.to_numeric(d["ni"], errors="coerce"))
    out = pair_frame(
        source_dataset="ReplicationSuccess SSRP.rda",
        project="SSRP",
        pair_id="ssrp_" + d.index.astype(str),
        original_title=d["study"].fillna("").astype(str),
        replication_title=d["study"].fillna("").astype(str) + " (SSRP)",
        original_doi="",
        replication_doi="",
        outcome=d["study"].fillna("").astype(str),
        D_original=pd.to_numeric(d["ro"], errors="coerce").apply(scalar_r_to_d),
        N_original=pd.to_numeric(d["no"], errors="coerce"),
        D_replication=rep_r.apply(scalar_r_to_d),
        N_replication=rep_n,
        raw_file=str(path),
        match_author=d["study"].fillna("").astype(str),
    )
    return assign_match_keys(filter_usable_pairs(out), "match_author")


def build_ml2_pairs() -> pd.DataFrame:
    table_path = RAW_REPL / "ml2" / "table5data_RM.csv"
    orig_path = RAW_REPL / "ml2" / "ML2_OriginalEffects.csv"
    fig_path = RAW_REPL / "ml2" / "Data_Figure_NOweird_oriEffects.csv"

    table = pd.read_csv(table_path)
    orig = pd.read_csv(orig_path)
    fig = pd.read_csv(fig_path)

    merged = table.merge(
        orig[["study.analysis", "N", "ESCI.d", "ESCI.r", "testInfo.p.value"]],
        left_on="ori_ML2analysis",
        right_on="study.analysis",
        how="left",
    )
    merged = merged.merge(
        fig[["study.analysis", "usethisES"]].rename(columns={"study.analysis": "study.analysis.fig"}),
        left_on="ori_ML2analysis",
        right_on="study.analysis.fig",
        how="left",
    )

    d_original = pd.to_numeric(merged["ESCI.d"], errors="coerce").abs()
    d_original = d_original.fillna(pd.to_numeric(merged["ESCI.r"], errors="coerce").apply(scalar_r_to_d))
    d_original = d_original.fillna(pd.to_numeric(merged["usethisES"], errors="coerce").apply(scalar_r_to_d))

    d_replication = pd.to_numeric(merged["ML2_d"], errors="coerce").abs()
    d_replication = d_replication.fillna(pd.to_numeric(merged["ML2_r"], errors="coerce").apply(scalar_r_to_d))

    out = pair_frame(
        source_dataset="Many Labs 2 public join",
        project="Many Labs 2",
        pair_id="ml2_" + merged["analysis"].astype(str),
        original_title=merged["study"].fillna("").astype(str),
        replication_title="Many Labs 2 - " + merged["analysis"].astype(str),
        original_doi="",
        replication_doi="",
        outcome=merged["analysis"].fillna("").astype(str),
        D_original=d_original,
        N_original=pd.to_numeric(merged["N"], errors="coerce"),
        D_replication=d_replication,
        N_replication=pd.to_numeric(merged["ML2_N"], errors="coerce"),
        raw_file=str(table_path),
    )
    return filter_usable_pairs(out)


def build_eprp_pairs() -> pd.DataFrame:
    path = RAW_REPL / "eprp" / "XPhiReplicability_CompleteData.csv"
    d = pd.read_csv(path)

    d_original = d["OriginalEFFECTSIZE"].apply(parse_effect_string_to_d)
    d_original = d_original.where(np.isfinite(d_original), d.apply(lambda r: parse_test_text_to_d(r["OriginalANALYSIS"], HELPERS.to_num(r["OriginalN_Effect"])), axis=1))

    d_replication = d["ReplicationEFFECTSIZE"].apply(parse_effect_string_to_d)
    d_replication = d_replication.where(
        np.isfinite(d_replication),
        d.apply(lambda r: parse_test_text_to_d(r["ReplicationANALYSIS"], HELPERS.to_num(r["ReplicationN_Effect"])), axis=1),
    )

    out = pair_frame(
        source_dataset="EPRP complete data",
        project="EPRP",
        pair_id="eprp_" + d["PAPER_ID"].map(slugify),
        original_title=d["PAPER_ID"].fillna("").astype(str),
        replication_title=d["OSF"].fillna("").astype(str),
        original_doi="",
        replication_doi="",
        outcome=d["EffectTYPE"].fillna("").astype(str),
        D_original=d_original,
        N_original=pd.to_numeric(d["OriginalN_Effect"], errors="coerce"),
        D_replication=d_replication,
        N_replication=pd.to_numeric(d["ReplicationN_Effect"], errors="coerce"),
        raw_file=str(path),
    )
    return filter_usable_pairs(out)


class EERPDummy:
    def __init__(self, values: dict[str, float]):
        self.values = values

    def getdf2(self) -> float:
        return self.values.get("df2", np.nan)


def eval_eerp_expression(expr: str, objects: dict[str, dict[str, float]]) -> float:
    expr = expr.strip()
    if "#" in expr:
        expr = expr.split("#", 1)[0].strip()
    try:
        return float(expr)
    except ValueError:
        env = {"__builtins__": {}, "norm": norm, "t": student_t, "abs": abs}
        env.update({name: EERPDummy(values) for name, values in objects.items()})
        return float(eval(expr, env, {}))


def eerp_effect_to_d(values: dict[str, float]) -> float:
    stat_type = str(values.get("type", "")).lower()
    stat = HELPERS.to_num(values.get("stat"))
    n = HELPERS.to_num(values.get("N"))
    df2 = HELPERS.to_num(values.get("df2"))
    if not (np.isfinite(stat) and np.isfinite(n) and n > 0):
        return np.nan
    if stat_type == "t":
        denom = df2 if np.isfinite(df2) and df2 > 0 else n
        return abs(2 * stat / math.sqrt(denom))
    if stat_type == "z":
        return abs(2 * stat / math.sqrt(n))
    if stat_type == "chi2":
        return scalar_r_to_d(math.sqrt(abs(stat) / n))
    return np.nan


def build_eerp_pairs() -> pd.DataFrame:
    path = RAW_REPL / "replicationsuccess" / "RProjects.rda"
    d = next(iter(pyreadr.read_r(path).values()))
    d = d.loc[d["project"].eq("Experimental Economics")].copy()
    out = pair_frame(
        source_dataset="ReplicationSuccess RProjects.rda",
        project="EERP",
        pair_id="eerp_" + d.index.astype(str),
        original_title=d["study"].fillna("").astype(str),
        replication_title=d["study"].fillna("").astype(str) + " (EERP)",
        original_doi="",
        replication_doi="",
        outcome=d["study"].fillna("").astype(str),
        D_original=pd.to_numeric(d["ro"], errors="coerce").apply(scalar_r_to_d),
        N_original=pd.to_numeric(d["no"], errors="coerce"),
        D_replication=pd.to_numeric(d["rr"], errors="coerce").apply(scalar_r_to_d),
        N_replication=pd.to_numeric(d["nr"], errors="coerce"),
        raw_file=str(path),
        match_author=d["study"].fillna("").astype(str),
    )
    return assign_match_keys(filter_usable_pairs(out), "match_author")


def build_rpcb_pairs() -> pd.DataFrame:
    path = RAW_CAND / "rpcb" / "RP_CB Final Analysis - Effect level data.csv"
    d = pd.read_csv(path)
    out = pair_frame(
        source_dataset="RPCB",
        project="RPCB",
        pair_id="rpcb_" + d.index.astype(str),
        original_title="paper_" + d["Paper #"].astype(str) + "_experiment_" + d["Experiment #"].astype(str),
        replication_title="paper_" + d["Paper #"].astype(str) + "_experiment_" + d["Experiment #"].astype(str),
        original_doi="",
        replication_doi="",
        outcome=d["Effect description"].fillna("").astype(str),
        D_original=HELPERS.numeric(d["Original effect size (SMD)"]).abs(),
        N_original=HELPERS.numeric(d["Original sample size"]),
        D_replication=HELPERS.numeric(d["Replication effect size (SMD)"]).abs(),
        N_replication=HELPERS.numeric(d["Replication sample size"]),
        raw_file=str(path),
    )
    return filter_usable_pairs(out)


def build_score_pairs() -> pd.DataFrame:
    orig_path = RAW_CAND / "score" / "orig_outcomes.csv"
    repl_path = RAW_CAND / "score" / "repli_outcomes.csv"
    papers_path = RAW_CAND / "score" / "paper_metadata.csv"
    claims_path = RAW_CAND / "score" / "extracted_claims.csv"

    orig = pd.read_csv(orig_path)
    repl = pd.read_csv(repl_path)
    papers = pd.read_csv(papers_path, usecols=["paper_id", "title", "citation", "DOI"])
    claims = pd.read_csv(
        claims_path,
        usecols=["unique_claim_id", "coded_claim2", "claim2_abstract", "coded_claim3", "claim3_hyp", "coded_claim4"],
    ).rename(columns={"unique_claim_id": "claim_id"})

    repl = repl[repl["repli_version_of_record"].fillna(False)].copy()
    merged = orig.merge(repl, on=["paper_id", "claim_id"], how="inner", suffixes=("_orig", "_repl"))
    merged = merged.merge(papers.drop_duplicates("paper_id"), on="paper_id", how="left")
    merged = merged.merge(claims.drop_duplicates("claim_id"), on="claim_id", how="left")

    paper_label = (
        merged[["citation", "title"]]
        .replace("", np.nan)
        .bfill(axis=1)
        .iloc[:, 0]
        .fillna("paper_" + merged["paper_id"].astype(str))
    )
    outcome = (
        merged[["coded_claim2", "claim2_abstract", "coded_claim3", "claim3_hyp", "coded_claim4"]]
        .replace("", np.nan)
        .bfill(axis=1)
        .iloc[:, 0]
        .fillna("claim_" + merged["claim_id"].astype(str))
    )

    out = pair_frame(
        source_dataset="SCORE analyst join",
        project="SCORE",
        pair_id="score_" + merged["claim_id"].astype(str) + "_" + merged["report_id"].astype(str),
        original_title=paper_label.astype(str),
        replication_title=paper_label.astype(str) + " (SCORE " + merged["report_id"].astype(str) + ")",
        original_doi=merged["DOI"].fillna("").astype(str),
        replication_doi="",
        outcome=outcome.astype(str),
        D_original=pd.to_numeric(merged["orig_conv_r"], errors="coerce").apply(scalar_r_to_d),
        N_original=pd.to_numeric(merged["orig_sample_size_value"], errors="coerce"),
        D_replication=pd.to_numeric(merged["repli_conv_r"], errors="coerce").apply(scalar_r_to_d),
        N_replication=pd.to_numeric(merged["repli_sample_size_value"], errors="coerce"),
        raw_file=str(orig_path) + " ; " + str(repl_path),
    )
    return filter_usable_pairs(out)


def build_altmejd_project_pairs(project_code: str, project_name: str) -> pd.DataFrame:
    path = RAW_REPL / "altmejd" / "data.csv"
    d = pd.read_csv(path)
    keep = (d["project"] == project_code) & d["aggregated"].fillna(False) & ~d["drop"].fillna(False)
    d = d.loc[keep].copy()
    out = pair_frame(
        source_dataset=f"Altmejd harmonized {project_name}",
        project=project_name,
        pair_id=d["id"].astype(str),
        original_title=d["title"].fillna("").astype(str),
        replication_title=d["title"].fillna("").astype(str),
        original_doi="",
        replication_doi="",
        outcome=d["effect_type"].fillna("").astype(str),
        D_original=pd.to_numeric(d["effect_size.o"], errors="coerce").apply(scalar_r_to_d),
        N_original=pd.to_numeric(d["n.o"], errors="coerce"),
        D_replication=pd.to_numeric(d["effect_size.r"], errors="coerce").apply(scalar_r_to_d),
        N_replication=pd.to_numeric(d["n.r"], errors="coerce"),
        raw_file=str(path),
    )
    return filter_usable_pairs(out)


def build_ml1_pairs() -> pd.DataFrame:
    return build_altmejd_project_pairs("ml1", "Many Labs 1")


def build_ml3_pairs() -> pd.DataFrame:
    return build_altmejd_project_pairs("ml3", "Many Labs 3")


def build_ml5_pairs() -> pd.DataFrame:
    es_path = RAW_REPL / "ml5" / "ML5FigureData.csv"
    n_path = RAW_REPL / "ml5" / "Summary Effect Sizes - Single Effects (including Orig and RPP).csv"
    es = pd.read_csv(es_path)
    ns = pd.read_csv(n_path)

    es_wide = es.pivot(index="Study", columns="Version", values="ES")
    n_wide = (
        ns.groupby(["Figure3StudyLabel", "Version"], as_index=False)["N"]
        .sum()
        .pivot(index="Figure3StudyLabel", columns="Version", values="N")
    )
    n_wide = n_wide.add_suffix("_n")
    merged = es_wide.join(n_wide, how="inner")
    merged = merged.reset_index().rename(columns={"Study": "study"})

    base = merged[["study", "Original", "ML5 RP:P", "ML5 Revised", "Original_n", "RP:P_n", "Revised_n"]].copy()
    base.columns = [
        "study",
        "es_original",
        "es_ml5_rpp",
        "es_ml5_revised",
        "n_original",
        "n_ml5_rpp",
        "n_ml5_revised",
    ]

    rpp = pair_frame(
        source_dataset="Many Labs 5 overarching analyses",
        project="Many Labs 5",
        pair_id="ml5_" + base["study"].map(slugify) + "_rpp",
        original_title=base["study"],
        replication_title=base["study"] + " (ML5 RP:P)",
        original_doi="",
        replication_doi="",
        outcome=base["study"],
        D_original=pd.to_numeric(base["es_original"], errors="coerce").apply(scalar_r_to_d),
        N_original=pd.to_numeric(base["n_original"], errors="coerce"),
        D_replication=pd.to_numeric(base["es_ml5_rpp"], errors="coerce").apply(scalar_r_to_d),
        N_replication=pd.to_numeric(base["n_ml5_rpp"], errors="coerce"),
        raw_file=str(es_path),
    )
    revised = pair_frame(
        source_dataset="Many Labs 5 overarching analyses",
        project="Many Labs 5",
        pair_id="ml5_" + base["study"].map(slugify) + "_revised",
        original_title=base["study"],
        replication_title=base["study"] + " (ML5 Revised)",
        original_doi="",
        replication_doi="",
        outcome=base["study"],
        D_original=pd.to_numeric(base["es_original"], errors="coerce").apply(scalar_r_to_d),
        N_original=pd.to_numeric(base["n_original"], errors="coerce"),
        D_replication=pd.to_numeric(base["es_ml5_revised"], errors="coerce").apply(scalar_r_to_d),
        N_replication=pd.to_numeric(base["n_ml5_revised"], errors="coerce"),
        raw_file=str(es_path),
    )
    return filter_usable_pairs(pd.concat([rpp, revised], ignore_index=True))


def build_pipeline_pairs() -> pd.DataFrame:
    supp_path = RAW_REPL / "pipeline" / "00.Supplemental_Materials_Pipeline_Project_Final_10_24_2015.pdf"
    packet1_path = RAW_REPL / "pipeline" / "PIPR_1.csv"

    p1 = pd.read_csv(packet1_path, encoding="latin1", low_memory=False)
    repl_mask = pd.to_numeric(p1["datacollection"], errors="coerce").ne(0)
    ie = p1.loc[repl_mask].copy()
    ie_cond = pd.to_numeric(ie["ie_condition"], errors="coerce")
    ie_fair = pd.Series(np.nan, index=ie.index, dtype=float)
    ie_good = pd.Series(np.nan, index=ie.index, dtype=float)
    ie_fair.loc[ie_cond.eq(1)] = 8 - pd.to_numeric(ie.loc[ie_cond.eq(1), "ie1_taxesf"], errors="coerce").replace(0, np.nan)
    ie_good.loc[ie_cond.eq(1)] = pd.to_numeric(ie.loc[ie_cond.eq(1), "ie1_taxesg"], errors="coerce").replace(0, np.nan)
    ie_fair.loc[ie_cond.eq(2)] = pd.to_numeric(ie.loc[ie_cond.eq(2), "ie2_htxf"], errors="coerce").replace(0, np.nan)
    ie_good.loc[ie_cond.eq(2)] = pd.to_numeric(ie.loc[ie_cond.eq(2), "ie2_htxg"], errors="coerce").replace(0, np.nan)
    ie_valid = ie_fair.notna() & ie_good.notna()
    ie_r_repl = ie_fair.loc[ie_valid].corr(ie_good.loc[ie_valid])
    ie_n_repl = int(ie_valid.sum())

    rows = [
        {
            "source_dataset": "Pipeline supplement + packet data",
            "project": "Pipeline Project",
            "pair_id": "pipeline_bigot_misanthrope",
            "original_title": "Bigot-misanthrope (Uhlmann)",
            "replication_title": "Pipeline Project 2016",
            "outcome": "Person judgments, bigot vs misanthrope",
            "D_original": d_from_t_df(6.07, 45),
            "N_original": 46,
            "D_replication": d_from_t_df(64.57, 2956),
            "N_replication": 2957,
        },
        {
            "source_dataset": "Pipeline supplement + packet data",
            "project": "Pipeline Project",
            "pair_id": "pipeline_moral_cliff",
            "original_title": "Moral cliff (Zhu & Uhlmann)",
            "replication_title": "Pipeline Project 2016",
            "outcome": "Dishonesty composite, Photoshop vs control",
            "D_original": d_from_f_df(49.01, 105),
            "N_original": 106,
            "D_replication": d_from_f_df(135.65, 3467),
            "N_replication": 3468,
        },
        {
            "source_dataset": "Pipeline supplement + packet data",
            "project": "Pipeline Project",
            "pair_id": "pipeline_cold_hearted_prosociality",
            "original_title": "Cold-hearted prosociality (Uhlmann)",
            "replication_title": "Pipeline Project 2016",
            "outcome": "Moral traits relative judgment",
            "D_original": d_from_t_df(5.40, 78),
            "N_original": 79,
            "D_replication": d_from_t_df(24.89, 2934),
            "N_replication": 2935,
        },
        {
            "source_dataset": "Pipeline supplement + packet data",
            "project": "Pipeline Project",
            "pair_id": "pipeline_higher_standards_charity",
            "original_title": "Higher standards, charity (Srinivasan)",
            "replication_title": "Pipeline Project 2016",
            "outcome": "Candidate evaluations, charity small perk vs cash",
            "D_original": d_from_t_df(3.95, 73),
            "N_original": 75,
            "D_replication": d_from_t_df(13.31, 923),
            "N_replication": 925,
        },
        {
            "source_dataset": "Pipeline supplement + packet data",
            "project": "Pipeline Project",
            "pair_id": "pipeline_intuitive_economics",
            "original_title": "Intuitive economics (Uhlmann-Diermeier)",
            "replication_title": "Pipeline Project 2016",
            "outcome": "High taxes fairness-goodness correlation",
            "D_original": scalar_r_to_d(0.39),
            "N_original": 225,
            "D_replication": scalar_r_to_d(ie_r_repl),
            "N_replication": ie_n_repl,
        },
        {
            "source_dataset": "Pipeline supplement + packet data",
            "project": "Pipeline Project",
            "pair_id": "pipeline_moral_inversion",
            "original_title": "Moral inversion (Uhlmann)",
            "replication_title": "Pipeline Project 2016",
            "outcome": "Company evaluations, publicized charity vs no charity",
            "D_original": d_from_t_df(2.92, 56),
            "N_original": 58,
            "D_replication": d_from_t_df(10.34, 3126),
            "N_replication": 3128,
        },
        {
            "source_dataset": "Pipeline supplement + packet data",
            "project": "Pipeline Project",
            "pair_id": "pipeline_bad_tipper",
            "original_title": "Bad tipper (Uhlmann)",
            "replication_title": "Pipeline Project 2016",
            "outcome": "Person judgments, pennies vs bills",
            "D_original": d_from_t_df(2.79, 75),
            "N_original": 77,
            "D_replication": d_from_t_df(18.96, 3645),
            "N_replication": 3647,
        },
        {
            "source_dataset": "Pipeline supplement + packet data",
            "project": "Pipeline Project",
            "pair_id": "pipeline_burn_in_hell",
            "original_title": "Burn in hell (Uhlmann-Diermeier)",
            "replication_title": "Pipeline Project 2016",
            "outcome": "Executives vs vandals burn-in-hell estimates",
            "D_original": d_from_t_df(2.82, 152),
            "N_original": 153,
            "D_replication": d_from_t_df(13.66, 3211),
            "N_replication": 3212,
        },
        {
            "source_dataset": "Pipeline supplement + packet data",
            "project": "Pipeline Project",
            "pair_id": "pipeline_belief_act_inconsistency",
            "original_title": "Belief-act inconsistency (Uhlmann)",
            "replication_title": "Pipeline Project 2016",
            "outcome": "Moral blame, animal-rights vs big-game-hunting advocate",
            "D_original": d_from_t_df(2.11, 124),
            "N_original": 126,
            "D_replication": d_from_t_df(7.57, 2065),
            "N_replication": 2067,
        },
        {
            "source_dataset": "Pipeline supplement + packet data",
            "project": "Pipeline Project",
            "pair_id": "pipeline_higher_standards_company",
            "original_title": "Higher standards, company (Srinivasan)",
            "replication_title": "Pipeline Project 2016",
            "outcome": "Candidate evaluations, company small perk vs cash",
            "D_original": d_from_t_df(1.64, 88),
            "N_original": 90,
            "D_replication": d_from_t_df(15.72, 912),
            "N_replication": 914,
        },
    ]

    out = pair_frame(
        source_dataset=[row["source_dataset"] for row in rows],
        project=[row["project"] for row in rows],
        pair_id=[row["pair_id"] for row in rows],
        original_title=[row["original_title"] for row in rows],
        replication_title=[row["replication_title"] for row in rows],
        original_doi=["" for _ in rows],
        replication_doi=["" for _ in rows],
        outcome=[row["outcome"] for row in rows],
        D_original=[row["D_original"] for row in rows],
        N_original=[row["N_original"] for row in rows],
        D_replication=[row["D_replication"] for row in rows],
        N_replication=[row["N_replication"] for row in rows],
        raw_file=[str(supp_path) for _ in rows],
    )
    out.loc[out["pair_id"].eq("pipeline_intuitive_economics"), "raw_file"] = str(supp_path) + " ; " + str(packet1_path)
    return filter_usable_pairs(out)


def build_decision_market_pairs() -> pd.DataFrame:
    path = RAW_REPL / "decision_market" / "data_to_use.csv"
    d = pd.read_csv(path)

    out = pair_frame(
        source_dataset="Decision-market pair table",
        project="Decision-Market Replication Project",
        pair_id="dmrp_" + d["sref"].fillna("").map(slugify),
        original_title=d["study"].fillna("").astype(str),
        replication_title=d["study"].fillna("").astype(str) + " (Decision-Market)",
        original_doi="",
        replication_doi="",
        outcome=d["study"].fillna("").astype(str),
        D_original=pd.to_numeric(d["d_os"], errors="coerce").abs(),
        N_original=pd.to_numeric(d["n_os"], errors="coerce"),
        D_replication=pd.to_numeric(d["d_rs"], errors="coerce").abs(),
        N_replication=pd.to_numeric(d["n_rs"], errors="coerce"),
        raw_file=str(path),
        match_author=d["study"].fillna("").astype(str),
    )
    return assign_match_keys(filter_usable_pairs(out), "match_author")


def build_loopr_pairs() -> pd.DataFrame:
    path = RAW_REPL / "loopr" / "Replication coding and results.xlsx"
    d = pd.read_excel(path, sheet_name="Results")

    orig_n = pd.to_numeric(d["OriginalSampleSizeByOutcome"], errors="coerce").fillna(
        pd.to_numeric(d["OriginalSampleSize"], errors="coerce")
    )
    repl_n = pd.to_numeric(d["ReplicationSampleSizeByOutcome"], errors="coerce").fillna(
        pd.to_numeric(d["ReplicationSampleSize"], errors="coerce")
    )

    orig_fz = pd.to_numeric(d["OriginalFisheredEffectSizeByOutcome"], errors="coerce")
    repl_fz = pd.to_numeric(d["ReplicationFisheredEffectSizeByOutcome"], errors="coerce")
    orig_effect = pd.to_numeric(d["OriginalEffect"], errors="coerce")
    repl_effect = pd.to_numeric(d["ReplicationEffect"], errors="coerce")

    orig_d = orig_fz.apply(fisher_z_abs_to_d)
    orig_d = orig_d.where(
        np.isfinite(orig_d),
        orig_effect.where(orig_effect.abs() < 1).apply(scalar_r_to_d),
    )

    repl_d = repl_fz.apply(fisher_z_abs_to_d)
    repl_d = repl_d.where(
        np.isfinite(repl_d),
        repl_effect.where(repl_effect.abs() < 1).apply(scalar_r_to_d),
    )

    outcome = d["OutcomeName"].fillna("").astype(str)
    if "TraitPredicted" in d.columns:
        trait = d["TraitPredicted"].fillna("").astype(str)
        outcome = np.where(trait.ne(""), outcome + " - " + trait, outcome)

    out = pair_frame(
        source_dataset="LOOPR coding workbook",
        project="LOOPR",
        pair_id="loopr_" + d["ResultsOrder"].astype(str),
        original_title=d["OriginalStudyCitation"].fillna("").astype(str),
        replication_title=d["OriginalStudyCitation"].fillna("").astype(str) + " (LOOPR)",
        original_doi="",
        replication_doi="",
        outcome=pd.Series(outcome, index=d.index).astype(str),
        D_original=orig_d,
        N_original=orig_n,
        D_replication=repl_d,
        N_replication=repl_n,
        raw_file=str(path),
        match_author=d["OriginalStudyCitation"].fillna("").astype(str),
    )
    return assign_match_keys(filter_usable_pairs(out), "match_author")


def build_boyce_pairs() -> pd.DataFrame:
    path = RAW_REPL / "boyce_student" / "boyce_2023_data.csv"
    d = pd.read_csv(path)
    d = d.loc[d["status"].eq("done")].copy()

    out = pair_frame(
        source_dataset="Boyce student replication corpus",
        project="Student Replication Projects",
        pair_id="boyce_" + d.index.astype(str),
        original_title=d["target_lastauthor_year"].fillna("").astype(str),
        replication_title=d["target_lastauthor_year"].fillna("").astype(str) + " (student replication)",
        original_doi="",
        replication_doi="",
        outcome=d["target_raw_stat"].fillna("").astype(str),
        D_original=pd.to_numeric(d["target_d_calc"], errors="coerce").abs(),
        N_original=pd.to_numeric(d["target_N"], errors="coerce"),
        D_replication=pd.to_numeric(d["rep_d_calc"], errors="coerce").abs(),
        N_replication=pd.to_numeric(d["replication_N"], errors="coerce"),
        raw_file=str(path),
        match_author=d["target_lastauthor_year"].fillna("").astype(str),
    )
    return assign_match_keys(filter_usable_pairs(out), "match_author")


def build_rescue_pairs() -> pd.DataFrame:
    parsed_path = RAW_REPL / "rescue_251" / "parsed_data.csv"
    combined_path = RAW_REPL / "rescue_251" / "combined_data.csv"
    boyce_path = RAW_REPL / "boyce_student" / "boyce_2023_data.csv"

    parsed = pd.read_csv(parsed_path)
    combined = pd.read_csv(combined_path)
    boyce = pd.read_csv(boyce_path)

    boyce = boyce.loc[boyce["status"].eq("done")].copy()
    boyce["base_target"] = boyce["target_lastauthor_year"].map(student_target_base)
    boyce_overlap = filter_usable_pairs(
        pair_frame(
            D_original=pd.to_numeric(boyce["target_d_calc"], errors="coerce").abs(),
            N_original=pd.to_numeric(boyce["target_N"], errors="coerce"),
            D_replication=pd.to_numeric(boyce["rep_d_calc"], errors="coerce").abs(),
            N_replication=pd.to_numeric(boyce["replication_N"], errors="coerce"),
        )
    )
    boyce_overlap["base_target"] = boyce.loc[boyce_overlap.index, "base_target"].values
    boyce_overlap_keys = {
        (
            row.base_target,
            round(float(row.N_replication), 3),
            round(float(row.D_replication), 6),
        )
        for row in boyce_overlap.itertuples(index=False)
    }

    orig = parsed.loc[parsed["type"].eq("original"), ["target_lastauthor_year", "N", "calc_d_calc"]].rename(
        columns={"N": "N_original", "calc_d_calc": "D_original"}
    )
    reps = parsed.loc[parsed["type"].isin(["rep1", "rescue", "additional"]), ["target_lastauthor_year", "type", "N", "calc_d_calc", "raw_stat"]].rename(
        columns={"N": "N_replication", "calc_d_calc": "D_replication", "raw_stat": "replication_raw_stat"}
    )
    meta = combined.loc[
        combined["type"].isin(["rep1", "rescue", "additional"]),
        ["target_lastauthor_year", "type", "name_pretty", "target_cite", "article_link"],
    ].drop_duplicates(["target_lastauthor_year", "type"])

    merged = reps.merge(orig, on="target_lastauthor_year", how="left").merge(
        meta, on=["target_lastauthor_year", "type"], how="left"
    )
    merged["base_target"] = merged["target_lastauthor_year"].map(student_target_base)
    merged["overlap_key"] = list(
        zip(
            merged["base_target"],
            pd.to_numeric(merged["N_replication"], errors="coerce").round(3),
            pd.to_numeric(merged["D_replication"], errors="coerce").abs().round(6),
        )
    )
    merged = merged.loc[~merged["overlap_key"].isin(boyce_overlap_keys)].copy()

    title = merged["name_pretty"].fillna("").astype(str)
    title = title.where(title.ne(""), merged["target_lastauthor_year"].fillna("").astype(str))

    out = pair_frame(
        source_dataset="251 Rescue parsed data",
        project="251 Rescue Projects",
        pair_id="rescue_" + merged["target_lastauthor_year"].map(slugify) + "_" + merged["type"].map(slugify),
        original_title=title,
        replication_title=title + " (" + merged["type"].astype(str) + ")",
        original_doi="",
        replication_doi="",
        outcome=merged["replication_raw_stat"].fillna("").astype(str),
        D_original=pd.to_numeric(merged["D_original"], errors="coerce").abs(),
        N_original=pd.to_numeric(merged["N_original"], errors="coerce"),
        D_replication=pd.to_numeric(merged["D_replication"], errors="coerce").abs(),
        N_replication=pd.to_numeric(merged["N_replication"], errors="coerce"),
        raw_file=str(parsed_path) + " ; " + str(combined_path),
        match_author=title,
    )
    return assign_match_keys(filter_usable_pairs(out), "match_author")


def build_clinical_pairs() -> pd.DataFrame:
    path = RAW_REPL / "clinical_replication" / "data - published.xlsx"
    d = pd.read_excel(path, sheet_name="Replications")
    d = d.loc[d["Risk.Measure"].isin(["OR", "HR", "RR"])].copy()

    est_orig = pd.to_numeric(d["Estimate.HC"], errors="coerce")
    est_repl = pd.to_numeric(d["Estimate.REP"], errors="coerce")
    risk_measure = d["Risk.Measure"].fillna("").astype(str)

    d_orig = pd.Series(np.nan, index=d.index, dtype=float)
    d_repl = pd.Series(np.nan, index=d.index, dtype=float)

    or_mask = risk_measure.eq("OR")
    hr_mask = risk_measure.eq("HR")
    rr_mask = risk_measure.eq("RR")

    d_orig.loc[or_mask] = est_orig.loc[or_mask].apply(odds_ratio_to_d)
    d_repl.loc[or_mask] = est_repl.loc[or_mask].apply(odds_ratio_to_d)
    d_orig.loc[hr_mask | rr_mask] = est_orig.loc[hr_mask | rr_mask].apply(log_ratio_abs)
    d_repl.loc[hr_mask | rr_mask] = est_repl.loc[hr_mask | rr_mask].apply(log_ratio_abs)

    out = pair_frame(
        source_dataset="Clinical published replication workbook",
        project="Clinical highly cited replications",
        pair_id="clinical_" + d.index.astype(str),
        original_title=d["Title.HC"].fillna("").astype(str),
        replication_title=d["Title.REP"].fillna("").astype(str),
        original_doi=d["DOI.HC"].fillna("").astype(str),
        replication_doi=d["DOI.REP"].fillna("").astype(str),
        outcome=d["Risk.Measure"].fillna("").astype(str),
        D_original=d_orig,
        N_original=pd.to_numeric(d["N.HC"], errors="coerce"),
        D_replication=d_repl,
        N_replication=pd.to_numeric(d["N.REP.Total"], errors="coerce"),
        raw_file=str(path),
        match_author=d["Title.HC"].fillna("").astype(str),
    )
    return assign_match_keys(filter_usable_pairs(out), "match_author")


def build_bri_pairs() -> pd.DataFrame:
    assess_path = RAW_REPL / "bri" / "output_primary_t" / "Replication Assessment by Experiment.tsv"
    predictor_path = RAW_REPL / "bri" / "predictor-data.xlsx"
    summary_dir = RAW_REPL / "bri" / "summaries"

    assess = pd.read_csv(assess_path, sep="\t")
    assess["EXP"] = assess["EXP"].fillna("").astype(str)
    assess = assess.loc[~assess["EXP"].str.contains("ALT", na=False)].copy()

    rep_n_rows = []
    for exp in assess["EXP"]:
        summary_path = summary_dir / f"Summary per EXP - {exp}.tsv"
        if not summary_path.exists():
            rep_n_rows.append({"EXP": exp, "N_replication": np.nan})
            continue
        summary = pd.read_csv(summary_path, sep="\t")
        n_group_1 = pd.to_numeric(summary.get("n_group_1"), errors="coerce")
        n_group_2 = pd.to_numeric(summary.get("n_group_2"), errors="coerce")
        rep_n_rows.append({"EXP": exp, "N_replication": (n_group_1 + n_group_2).sum()})
    rep_n = pd.DataFrame(rep_n_rows)

    predictor = pd.read_excel(predictor_path, sheet_name="Extraction Sheet")
    predictor["EXP"] = predictor["EXP"].fillna("").astype(str)
    predictor["N_original"] = pd.to_numeric(
        predictor["Assumed Control Sample Size"], errors="coerce"
    ) + pd.to_numeric(predictor["Assumed Treated Sample Size"], errors="coerce")

    merged = assess.merge(
        predictor[
            [
                "EXP",
                "DOI",
                "Method",
                "Figure/Table",
                "Cohen’s d",
                "N_original",
            ]
        ],
        on="EXP",
        how="left",
    ).merge(rep_n, on="EXP", how="left")

    outcome = (
        merged["Method"].fillna("").astype(str).str.strip()
        + " | "
        + merged["Figure/Table"].fillna("").astype(str).str.strip()
    ).str.strip(" |")
    original_title = np.where(
        merged["DOI"].fillna("").astype(str).str.strip().ne(""),
        merged["DOI"].fillna("").astype(str).str.strip(),
        "BRI " + merged["EXP"],
    )

    out = pair_frame(
        source_dataset="BRI primary t experiment table",
        project="Brazilian Reproducibility Initiative",
        pair_id="bri_" + merged["EXP"].map(slugify),
        original_title=original_title,
        replication_title="BRI " + merged["EXP"].astype(str),
        original_doi=merged["DOI"].fillna("").astype(str),
        replication_doi="",
        outcome=outcome,
        D_original=pd.to_numeric(merged["original_es"], errors="coerce").abs(),
        N_original=pd.to_numeric(merged["N_original"], errors="coerce"),
        D_replication=pd.to_numeric(merged["replication_es"], errors="coerce").abs(),
        N_replication=pd.to_numeric(merged["N_replication"], errors="coerce"),
        raw_file=str(assess_path),
        match_author=merged["DOI"].fillna(merged["EXP"]).astype(str),
    )
    return assign_match_keys(filter_usable_pairs(out), "match_author")


def build_fred_pairs() -> pd.DataFrame:
    path = RAW_REPL / "fred" / "FReD.xlsx"
    d = pd.read_excel(path)

    d["fred_prefix"] = (
        d["fred_id"].astype(str).str.extract(r"^([A-Za-z]+)")[0].fillna("misc").str.lower()
    )
    fred_text = (
        d[
            [
                "title_r",
                "journal_r",
                "ref_r",
                "reported_success_quote",
                "title_o",
                "description",
                "claim_text_o",
            ]
        ]
        .fillna("")
        .astype(str)
        .agg(" || ".join, axis=1)
        .str.lower()
    )
    excluded_prefixes = {"boyce", "osc", "xphi", "manylabs", "camereretal", "jcre"}
    excluded_fred_ids = {"RRR_cognitivedissonance"}
    non_new_sample_patterns = [
        "secondary data replication",
        "secondary data",
        "syntax and output files",
        "re-analysis",
        "reanalysis",
        "computational reproduction",
        "same dataset",
        "same data",
        "same sample",
    ]
    exclude_mask = d["fred_prefix"].isin(excluded_prefixes) | d["fred_id"].isin(excluded_fred_ids)
    for pattern in non_new_sample_patterns:
        exclude_mask |= fred_text.str.contains(pattern, regex=False)
    d = d.loc[~exclude_mask].copy()

    project_map = {
        "core": "FReD CORE",
        "curatescience": "FReD CurateScience",
        "soscisubmission": "FReD SoSci submissions",
        "openmkt": "FReD OpenMKT",
        "jcre": "FReD JCRE",
        "forrt": "FReD FORRT",
        "rrr": "FReD new RRR",
    }

    outcome = d["description"].fillna("").astype(str)
    outcome = outcome.where(outcome.ne(""), d["claim_text_o"].fillna("").astype(str))
    outcome = outcome.where(outcome.ne(""), d["fred_id"].fillna("").astype(str))

    original_title = d["title_o"].fillna("").astype(str)
    original_title = original_title.where(original_title.ne(""), d["ref_o"].fillna("").astype(str))

    replication_title = d["title_r"].fillna("").astype(str)
    replication_title = replication_title.where(replication_title.ne(""), d["ref_r"].fillna("").astype(str))

    out = pair_frame(
        source_dataset="FReD filtered pair table",
        project=d["fred_prefix"].map(project_map).fillna("FReD other additions"),
        pair_id="fred_" + d["fred_id"].fillna("").map(slugify) + "_" + d["effect_id"].astype(str),
        original_title=original_title,
        replication_title=replication_title,
        original_doi=d["doi_o"].fillna("").astype(str),
        replication_doi=d["doi_r"].fillna("").astype(str),
        outcome=outcome,
        D_original=[
            fred_effect_to_d(v, t, n)
            for v, t, n in zip(d["es_value_o"], d["es_type_o"], pd.to_numeric(d["n_o"], errors="coerce"))
        ],
        N_original=pd.to_numeric(d["n_o"], errors="coerce"),
        D_replication=[
            fred_effect_to_d(v, t, n)
            for v, t, n in zip(d["es_value_r"], d["es_type_r"], pd.to_numeric(d["n_r"], errors="coerce"))
        ],
        N_replication=pd.to_numeric(d["n_r"], errors="coerce"),
        raw_file=str(path),
        match_author=original_title,
    )
    return assign_match_keys(filter_usable_pairs(out), "match_author")


def build_vaidis_rrr_pairs() -> pd.DataFrame:
    data_path = RAW_REPL / "rrr" / "vaidis_2024_prepared_data_subset.csv"
    fred_path = RAW_REPL / "fred" / "FReD.xlsx"
    data = pd.read_csv(data_path)
    fred = pd.read_excel(fred_path)
    anchor = fred.loc[fred["fred_id"].astype(str).eq("RRR_cognitivedissonance")]
    if anchor.empty:
        return pair_frame()
    anchor_row = anchor.iloc[0]

    attrition = (
        data.groupby("lab")
        .apply(
            lambda g: (
                (
                    g["exclude_participant"].eq("yes")
                    | g["exclude_session"].eq("yes")
                    | g["refused_essay"].eq("yes")
                ).sum()
                / len(g)
            )
        )
        .rename("attrition_rate")
        .reset_index()
    )
    data = data.merge(attrition, on="lab", how="left")
    data = data.loc[
        data["university_next_year"].eq("yes")
        & data["debriefing_exclude"].eq(0)
        & data["exclude_participant"].eq("no")
        & data["exclude_session"].eq("no")
        & (pd.to_numeric(data["attrition_rate"], errors="coerce") < 0.25)
    ].copy()

    # Exclusion specified in the public analysis script.
    data = data.loc[~((pd.to_numeric(data["lab_number"], errors="coerce") == 60) & data["condition"].eq("HC-NE"))].copy()

    data = data.loc[data["condition"].isin(["HC-CE", "LC-CE"])].copy()

    rows = []
    for (lab_number, lab, lab_university), g in data.groupby(
        ["lab_number", "lab", "lab_university"], dropna=False
    ):
        hc = pd.to_numeric(g.loc[g["condition"].eq("HC-CE"), "attitude_1"], errors="coerce").dropna()
        lc = pd.to_numeric(g.loc[g["condition"].eq("LC-CE"), "attitude_1"], errors="coerce").dropna()
        if len(hc) < 2 or len(lc) < 2:
            continue
        pooled_sd_num = ((len(hc) - 1) * hc.std(ddof=1) ** 2) + ((len(lc) - 1) * lc.std(ddof=1) ** 2)
        pooled_sd_den = len(hc) + len(lc) - 2
        pooled_sd = math.sqrt(pooled_sd_num / pooled_sd_den) if pooled_sd_den > 0 else np.nan
        if not (np.isfinite(pooled_sd) and pooled_sd > 0):
            continue
        d_rep = abs((hc.mean() - lc.mean()) / pooled_sd)
        rows.append(
            {
                "source_dataset": "Vaidis 2024 prepared data subset",
                "project": "Registered Replication Reports",
                "pair_id": f"vaidis_2024_choice_lab_{int(lab_number)}",
                "original_title": str(anchor_row["title_o"]),
                "replication_title": f"A Multilab Replication of the Induced-Compliance Paradigm of Cognitive Dissonance - {lab_university}",
                "original_doi": str(anchor_row["doi_o"]),
                "replication_doi": str(anchor_row["doi_r"]),
                "outcome": "HC-CE vs LC-CE on attitude_1",
                "D_original": fred_effect_to_d(anchor_row["es_value_o"], anchor_row["es_type_o"], float(anchor_row["n_o"])),
                "N_original": float(anchor_row["n_o"]),
                "D_replication": d_rep,
                "N_replication": float(len(hc) + len(lc)),
                "raw_file": str(data_path),
                "match_author": str(anchor_row["title_o"]),
            }
        )

    if not rows:
        return pair_frame()
    out = pd.DataFrame(rows)
    return assign_match_keys(filter_usable_pairs(out), "match_author")


def build_stoevenbelt_rrr_pairs() -> pd.DataFrame:
    data_path = RAW_REPL / "rrr" / "stoevenbelt_data_ST_RRR_combined.csv"
    preprint_path = RAW_REPL / "rrr" / "stoevenbelt_preprint_qctkp.pdf"
    if not data_path.exists():
        return pair_frame()

    data = pd.read_csv(data_path, encoding="latin1")

    # Reproduce the main exclusion logic from the public analysis script before
    # computing the women-only stereotype-threat vs low-threat contrast per lab.
    data["BYnumcorrect"] = pd.to_numeric(data.get("BYnumcorrect"), errors="coerce")
    data["Exc"] = pd.to_numeric(data.get("Exc"), errors="coerce")
    data["Exc.3.easy"] = pd.to_numeric(data.get("Exc.3.easy"), errors="coerce").fillna(0)
    data["Exc.3.reg"] = pd.to_numeric(data.get("Exc.3.reg"), errors="coerce").fillna(0)
    data["Total.test.score"] = pd.to_numeric(data.get("Total.test.score"), errors="coerce")

    attempted = np.where(
        data["Lab"].astype(str).eq("BYUI"),
        data["BYnumcorrect"],
        data["Exc.3.easy"] + data["Exc.3.reg"],
    )
    data["attempted"] = pd.to_numeric(attempted, errors="coerce")
    data = data.loc[(data["BYnumcorrect"] > 5) | data["BYnumcorrect"].isna()].copy()
    data = data.loc[data["Exc"].eq(0)].copy()
    data["Accuracy"] = data["Total.test.score"] / data["attempted"]
    data = data.loc[
        data["gender"].astype(str).eq("F")
        & data["Accuracy"].replace([np.inf, -np.inf], np.nan).notna()
        & data["treatment"].astype(str).isin(["ST", "TI", "PS"])
    ].copy()

    lab_labels = {
        "Universität Wien, Phillips": "Pietschnig",
        "UVT.ENG": "Stoevenbelt (ENG)",
        "UVT.NL": "Stoevenbelt (NL)",
        "University of Amsterdam": "Verschuere",
        "TU Dortmund University": "Huffmeier",
        "Dominican University": "Calin-Jageman",
        "BYUI": "Martin",
        "UNIPO": "Ropovik",
        "University of California Los Angeles, Pan/Imundo": "Pan",
    }

    original_title = "Knowing is half the battle: Teaching stereotype threat as a means of improving women's math performance"
    original_doi = "10.1177/0956797604271307"
    original_n = 45.0
    original_d = 0.82
    replication_title = "Registered Replication Report: Johns, Schmader, & Martens (2005)"
    replication_doi = "10.31234/osf.io/qctkp"

    rows = []
    for lab, g in data.groupby("Lab", dropna=False):
        st = pd.to_numeric(g.loc[g["treatment"].astype(str).eq("ST"), "Accuracy"], errors="coerce").dropna()
        control = pd.to_numeric(g.loc[~g["treatment"].astype(str).eq("ST"), "Accuracy"], errors="coerce").dropna()
        if len(st) < 2 or len(control) < 2:
            continue
        pooled_sd_num = ((len(st) - 1) * st.std(ddof=1) ** 2) + ((len(control) - 1) * control.std(ddof=1) ** 2)
        pooled_sd_den = len(st) + len(control) - 2
        pooled_sd = math.sqrt(pooled_sd_num / pooled_sd_den) if pooled_sd_den > 0 else np.nan
        if not (np.isfinite(pooled_sd) and pooled_sd > 0):
            continue
        d_rep = abs((st.mean() - control.mean()) / pooled_sd)
        label = lab_labels.get(str(lab), str(lab))
        rows.append(
            {
                "source_dataset": "Stoevenbelt 2025 combined lab csv",
                "project": "Registered Replication Reports",
                "pair_id": f"stoevenbelt_2025_lab_{slugify(label)}",
                "original_title": original_title,
                "replication_title": f"{replication_title} - {label}",
                "original_doi": original_doi,
                "replication_doi": replication_doi,
                "outcome": "Women only: stereotype threat vs low-threat controls on math-test accuracy",
                "D_original": original_d,
                "N_original": original_n,
                "D_replication": d_rep,
                "N_replication": float(len(st) + len(control)),
                "raw_file": str(preprint_path if preprint_path.exists() else data_path),
                "match_author": "Johns Schmader Martens stereotype threat",
            }
        )

    if not rows:
        return pair_frame()
    out = pd.DataFrame(rows)
    return assign_match_keys(filter_usable_pairs(out), "match_author")


def build_odonnell_rrr_pairs() -> pd.DataFrame:
    meta_dir = RAW_REPL / "rrr" / "odonnell_meta"
    if not meta_dir.exists():
        return pair_frame()

    original_title = "Dijksterhuis professor priming"
    replication_title = "Registered Replication Report: Dijksterhuis and van Knippenberg (1998)"

    rows = []
    for path in sorted(meta_dir.glob("*_data_meta.csv")):
        lab_label = path.stem.replace("_data_meta", "")
        data = pd.read_csv(path)
        main = data.loc[data["label"].astype(str).eq("main")].copy()
        if len(main) != 1:
            continue
        row = main.iloc[0]
        n1 = pd.to_numeric(row.get("n1"), errors="coerce")
        n2 = pd.to_numeric(row.get("n2"), errors="coerce")
        effect = pd.to_numeric(row.get("effect"), errors="coerce")
        se = pd.to_numeric(row.get("se"), errors="coerce")
        n_total = n1 + n2
        d_rep = d_from_mean_diff_se(effect, se, n_total)
        if not np.isfinite(d_rep):
            continue
        rows.append(
            {
                "source_dataset": "O'Donnell 2018 site-level meta csvs",
                "project": "Registered Replication Reports",
                "pair_id": f"odonnell_2018_lab_{slugify(lab_label)}",
                "original_title": original_title,
                "replication_title": f"{replication_title} - {lab_label}",
                "original_doi": "",
                "replication_doi": "10.1177/1745691618755704",
                "outcome": "Professor minus hooligan trivia-score difference (main analysis)",
                "D_original": 0.51,
                "N_original": 80.0,
                "D_replication": d_rep,
                "N_replication": float(n_total),
                "raw_file": str(path),
                "match_author": original_title,
            }
        )

    if not rows:
        return pair_frame()
    out = pd.DataFrame(rows)
    return assign_match_keys(filter_usable_pairs(out), "match_author")


def build_schooler_rrr_pairs() -> pd.DataFrame:
    path = RAW_REPL / "rrr" / "schooler_table1.xlsx"
    if not path.exists():
        return pair_frame()

    table = pd.read_excel(path)
    table.columns = [f"c{i}" for i in range(table.shape[1])]

    rows = []
    for _, row in table.iloc[3:].iterrows():
        lab_label = str(row["c0"] or "").strip()
        if not lab_label or lab_label.lower() == "nan":
            continue
        vd_total = pd.to_numeric(row["c7"], errors="coerce")
        vd_correct = pd.to_numeric(row["c8"], errors="coerce")
        ctl_total = pd.to_numeric(row["c15"], errors="coerce")
        ctl_correct = pd.to_numeric(row["c16"], errors="coerce")
        if not all(np.isfinite([vd_total, vd_correct, ctl_total, ctl_correct])):
            continue
        vd_fail = vd_total - vd_correct
        ctl_fail = ctl_total - ctl_correct
        if min(vd_correct, vd_fail, ctl_correct, ctl_fail) <= 0:
            continue
        or_value = (ctl_correct * vd_fail) / (ctl_fail * vd_correct)
        d_rep = odds_ratio_to_d(or_value)
        if not np.isfinite(d_rep):
            continue
        rows.append(
            {
                "source_dataset": "Alogna 2014 table 1 site counts",
                "project": "Registered Replication Reports",
                "pair_id": f"schooler_2014_lab_{slugify(lab_label)}",
                "original_title": "Schooler verbal overshadowing",
                "replication_title": f"Registered Replication Report: verbal overshadowing - {lab_label}",
                "original_doi": "",
                "replication_doi": "10.1177/1745691614545653",
                "outcome": "Correct identification: control vs verbal-description condition",
                "D_original": 0.80,
                "N_original": 90.0,
                "D_replication": d_rep,
                "N_replication": float(vd_total + ctl_total),
                "raw_file": str(path),
                "match_author": "Schooler verbal overshadowing",
            }
        )

    if not rows:
        return pair_frame()
    out = pd.DataFrame(rows)
    return assign_match_keys(filter_usable_pairs(out), "match_author")


def build_hagger_rrr_pairs() -> pd.DataFrame:
    path = RAW_REPL / "rrr" / "hagger" / "RTV.csv"
    if not path.exists():
        return pair_frame()

    data = pd.read_csv(path, encoding="latin1")
    data.columns = [str(c).strip() for c in data.columns]
    if data.empty:
        return pair_frame()

    original = data.iloc[0]
    d_original = pooled_d_from_summary(
        pd.to_numeric(original.get("Ego Depletion Mean"), errors="coerce"),
        pd.to_numeric(original.get("Ego Depletion Std Dev"), errors="coerce"),
        pd.to_numeric(original.get("Ego Depletion Sample size"), errors="coerce"),
        pd.to_numeric(original.get("Control Mean"), errors="coerce"),
        pd.to_numeric(original.get("Control Std-Dev"), errors="coerce"),
        pd.to_numeric(original.get("Control Sample size"), errors="coerce"),
    )
    n_original = (
        pd.to_numeric(original.get("Ego Depletion Sample size"), errors="coerce")
        + pd.to_numeric(original.get("Control Sample size"), errors="coerce")
    )
    if not (np.isfinite(d_original) and np.isfinite(n_original)):
        return pair_frame()

    rows = []
    for _, row in data.iloc[1:].iterrows():
        d_rep = pooled_d_from_summary(
            pd.to_numeric(row.get("Ego Depletion Mean"), errors="coerce"),
            pd.to_numeric(row.get("Ego Depletion Std Dev"), errors="coerce"),
            pd.to_numeric(row.get("Ego Depletion Sample size"), errors="coerce"),
            pd.to_numeric(row.get("Control Mean"), errors="coerce"),
            pd.to_numeric(row.get("Control Std-Dev"), errors="coerce"),
            pd.to_numeric(row.get("Control Sample size"), errors="coerce"),
        )
        n_rep = pd.to_numeric(row.get("Ego Depletion Sample size"), errors="coerce") + pd.to_numeric(
            row.get("Control Sample size"), errors="coerce"
        )
        study_name = str(row.get("Study name") or "").strip()
        if not study_name:
            continue
        rows.append(
            {
                "source_dataset": "Hagger 2016 RTV.csv",
                "project": "Registered Replication Reports",
                "pair_id": f"hagger_2016_lab_{slugify(study_name)}",
                "original_title": "Sripada 2014 ego depletion RTV",
                "replication_title": f"Registered Replication Report: ego depletion - {study_name}",
                "original_doi": "",
                "replication_doi": "10.1177/1745691616652873",
                "outcome": "RTV score on crossed-out-e task",
                "D_original": d_original,
                "N_original": n_original,
                "D_replication": d_rep,
                "N_replication": n_rep,
                "raw_file": str(path),
                "match_author": "Sripada ego depletion RTV",
            }
        )

    if not rows:
        return pair_frame()
    out = pd.DataFrame(rows)
    return assign_match_keys(filter_usable_pairs(out), "match_author")


def build_eerland_rrr_pairs() -> pd.DataFrame:
    base = RAW_REPL / "rrr" / "eerland"
    specs = [
        (
            "Intentionality.csv",
            "Hart & Albarracin grammatical aspect - intentionality",
            "Imperfective vs perfective framing on criminal intentionality judgments",
        ),
        (
            "Intention_attribution.csv",
            "Hart & Albarracin grammatical aspect - intention attribution",
            "Imperfective vs perfective framing on intention-attribution ratings",
        ),
        (
            "imagery.csv",
            "Hart & Albarracin grammatical aspect - imagery",
            "Imperfective vs perfective framing on imagery / processing ratings",
        ),
    ]

    rows = []
    for filename, original_title, outcome in specs:
        path = base / filename
        if not path.exists():
            continue
        data = pd.read_csv(path)
        if len(data) < 13:
            continue
        original = data.iloc[0]
        d_original = pooled_d_from_summary(
            pd.to_numeric(original.get("mimp"), errors="coerce"),
            pd.to_numeric(original.get("sdimp"), errors="coerce"),
            pd.to_numeric(original.get("nimp"), errors="coerce"),
            pd.to_numeric(original.get("mperf"), errors="coerce"),
            pd.to_numeric(original.get("sdperf"), errors="coerce"),
            pd.to_numeric(original.get("nperf"), errors="coerce"),
        )
        n_original = pd.to_numeric(original.get("nimp"), errors="coerce") + pd.to_numeric(
            original.get("nperf"), errors="coerce"
        )
        if not (np.isfinite(d_original) and np.isfinite(n_original)):
            continue

        for _, row in data.iloc[2:13].iterrows():
            author = str(row.get("Author") or "").strip()
            if not author:
                continue
            d_rep = pooled_d_from_summary(
                pd.to_numeric(row.get("mimp"), errors="coerce"),
                pd.to_numeric(row.get("sdimp"), errors="coerce"),
                pd.to_numeric(row.get("nimp"), errors="coerce"),
                pd.to_numeric(row.get("mperf"), errors="coerce"),
                pd.to_numeric(row.get("sdperf"), errors="coerce"),
                pd.to_numeric(row.get("nperf"), errors="coerce"),
            )
            n_rep = pd.to_numeric(row.get("nimp"), errors="coerce") + pd.to_numeric(
                row.get("nperf"), errors="coerce"
            )
            rows.append(
                {
                    "source_dataset": f"Eerland 2016 {filename}",
                    "project": "Registered Replication Reports",
                    "pair_id": f"eerland_2016_{slugify(filename)}_{slugify(author)}",
                    "original_title": original_title,
                    "replication_title": f"Registered Replication Report: Hart & Albarracin - {author}",
                    "original_doi": "",
                    "replication_doi": "10.1177/1745691615605826",
                    "outcome": outcome,
                    "D_original": d_original,
                    "N_original": n_original,
                    "D_replication": d_rep,
                    "N_replication": n_rep,
                    "raw_file": str(path),
                    "match_author": original_title,
                }
            )

    if not rows:
        return pair_frame()
    out = pd.DataFrame(rows)
    return assign_match_keys(filter_usable_pairs(out), "match_author")


def build_wagenmakers_rrr_pair() -> pd.DataFrame:
    path = RAW_REPL / "rrr" / "Wagenmakers_Data.csv"
    if not path.exists():
        return pair_frame()

    data = pd.read_csv(path, encoding="latin1").iloc[1:].copy()
    condition_col = "Condition\r1= SMILE 0 = POUT"
    task_col = "Task performed correctly? \r 1 = YES   0 = NO"
    rating_col = "Ratings"
    if any(col not in data.columns for col in [condition_col, task_col, rating_col]):
        return pair_frame()

    task_ok = pd.to_numeric(data[task_col], errors="coerce").eq(1)
    subset = data.loc[task_ok].copy()
    smile = pd.to_numeric(
        subset.loc[pd.to_numeric(subset[condition_col], errors="coerce").eq(1), rating_col], errors="coerce"
    ).dropna()
    pout = pd.to_numeric(
        subset.loc[pd.to_numeric(subset[condition_col], errors="coerce").eq(0), rating_col], errors="coerce"
    ).dropna()
    if len(smile) < 2 or len(pout) < 2:
        return pair_frame()

    d_rep = pooled_d_from_summary(smile.mean(), smile.std(ddof=1), len(smile), pout.mean(), pout.std(ddof=1), len(pout))
    n_rep = float(len(smile) + len(pout))
    out = pair_frame(
        source_dataset=["Wagenmakers 2016 site csv"],
        project=["Registered Replication Reports"],
        pair_id=["wagenmakers_2016_site_main"],
        original_title=["Strack pen-in-teeth"],
        replication_title=["Registered Replication Report: Strack facial feedback"],
        original_doi=[""],
        replication_doi=["10.1177/1745691616674458"],
        outcome=["Total cartoon-funniness rating (task-correct subset)"],
        D_original=[0.82],
        N_original=[92.0],
        D_replication=[d_rep],
        N_replication=[n_rep],
        raw_file=[str(path)],
        match_author=["Strack pen-in-teeth"],
    )
    return assign_match_keys(filter_usable_pairs(out), "match_author")


def build_sports_replication_pairs() -> pd.DataFrame:
    import xml.etree.ElementTree as ET
    import zipfile

    supp_path = RAW_REPL / "sports" / "sports_supp_table1.docx"
    sample_path = RAW_REPL / "sports" / "sports_sample_size_calculations.xlsx"
    selected_path = RAW_REPL / "sports" / "sports_allselectedstudies.xlsx"
    if not (supp_path.exists() and sample_path.exists() and selected_path.exists()):
        return pair_frame()

    ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    effect_rows = []
    with zipfile.ZipFile(supp_path) as zf:
        root = ET.fromstring(zf.read("word/document.xml"))
    for tbl in root.findall(".//w:tbl", ns):
        effect_section = None
        for row_index, tr in enumerate(tbl.findall("./w:tr", ns)):
            cells = []
            for tc in tr.findall("./w:tc", ns):
                texts = [t.text or "" for t in tc.findall(".//w:t", ns)]
                cells.append("".join(texts).strip())
            if not any(cells):
                continue
            if len(cells) == 1 and cells[0] and "Original Study" not in cells[0]:
                effect_section = cells[0]
                continue
            if row_index < 2 or not effect_section or len(cells) < 3:
                continue
            cells += [""] * (7 - len(cells))
            effect_rows.append(
                {
                    "effect_section": effect_section,
                    "study": cells[0],
                    "orig_es_raw": cells[1],
                    "rep_es_raw": cells[2],
                    "compatibility": cells[6],
                }
            )
    effects = pd.DataFrame(effect_rows)
    if effects.empty:
        return pair_frame()

    sizes = pd.read_excel(sample_path)
    selected = pd.read_excel(selected_path)

    def norm_title(text: object) -> str:
        s = str(text or "").lower().replace("\n", " ")
        s = re.sub(r"[^a-z0-9]+", " ", s)
        return " ".join(s.split())

    def normalize_doi(text: object) -> str:
        if pd.isna(text):
            return ""
        s = str(text).strip()
        if not s:
            return ""
        s = s.replace("\n", " ")
        s = re.sub(r"^https?://(?:dx\.)?doi\.org/", "", s, flags=re.I)
        return s.strip()

    sizes["norm_title"] = sizes["Study Title"].map(norm_title)
    effects["norm_title"] = effects["study"].map(norm_title)
    selected_title_col = "Copy and paste the study title"
    selected_doi_col = "Copy and paste the study DOI"
    selected["norm_title"] = selected[selected_title_col].map(norm_title)

    merged = effects.merge(
        sizes[
            [
                "norm_title",
                "Study Title",
                "Original Author",
                "Original Sample Size",
                "Final Actual Replication Sample Size",
                "ES type",
            ]
        ],
        on="norm_title",
        how="left",
    ).merge(
        selected[[selected_title_col, selected_doi_col, "norm_title"]],
        on="norm_title",
        how="left",
    )

    original_title = merged[selected_title_col].fillna(merged["Study Title"]).fillna(merged["study"]).astype(str)
    original_doi = merged[selected_doi_col].map(normalize_doi).fillna("")
    effect_family = merged["ES type"].fillna(merged["effect_section"]).astype(str)
    orig_vals = pd.to_numeric(merged["orig_es_raw"], errors="coerce")
    rep_vals = pd.to_numeric(merged["rep_es_raw"], errors="coerce")

    out = pair_frame(
        source_dataset="Sports science supplemental outcomes table",
        project="Sports science replications",
        pair_id="sports_" + merged["norm_title"].map(slugify),
        original_title=original_title,
        replication_title=original_title + " (Sports Science Replication Centre)",
        original_doi=original_doi,
        replication_doi="10.1007/s40279-025-02201-w",
        outcome=effect_family.str.strip() + " | " + merged["compatibility"].fillna("").astype(str).str.strip(),
        D_original=[sports_effect_to_d(v, t) for v, t in zip(orig_vals, effect_family)],
        N_original=pd.to_numeric(merged["Original Sample Size"], errors="coerce"),
        D_replication=[sports_effect_to_d(v, t) for v, t in zip(rep_vals, effect_family)],
        N_replication=pd.to_numeric(merged["Final Actual Replication Sample Size"], errors="coerce"),
        raw_file=str(supp_path) + " ; " + str(sample_path),
        match_author=original_title,
    )
    return assign_match_keys(filter_usable_pairs(out), "match_author")


def build_verified_manual_pairs() -> pd.DataFrame:
    manual_dir = RAW_REPL / "manual_papers"
    rows = [
        {
            "source_dataset": "SSRP 2018 supplement (manual)",
            "project": "SSRP",
            "pair_id": "manual_ssrp_aviezer_body_emotions",
            "original_title": "Aviezer body emotions (Science)",
            "replication_title": "SSRP Camerer 2018",
            "outcome": "Aviezer body emotions (Science)",
            "D_original": 2.67,
            "N_original": 15.0,
            "D_replication": 1.50,
            "N_replication": 400.0,
            "raw_file": str(manual_dir / "ssrp_2018_supplement.pdf"),
            "match_author": "Aviezer body emotions (Science)",
        },
        {
            "source_dataset": "SSRP 2018 supplement (manual)",
            "project": "SSRP",
            "pair_id": "manual_ssrp_janssen_commons",
            "original_title": "Janssen commons (Science)",
            "replication_title": "SSRP Camerer 2018",
            "outcome": "Janssen commons (Science)",
            "D_original": 1.22,
            "N_original": 224.0,
            "D_replication": 0.95,
            "N_replication": 1200.0,
            "raw_file": str(manual_dir / "ssrp_2018_supplement.pdf"),
            "match_author": "Janssen commons (Science)",
        },
        {
            "source_dataset": "EERP 2016 supplement (manual)",
            "project": "EERP",
            "pair_id": "manual_eerp_kessler_roth_matching_markets",
            "original_title": "Kessler-Roth matching markets",
            "replication_title": "EERP 2016",
            "outcome": "Kessler-Roth matching markets",
            "D_original": 0.62,
            "N_original": 120.0,
            "D_replication": 0.55,
            "N_replication": 385.0,
            "raw_file": str(manual_dir / "eerp_2016_supplement.pdf"),
            "match_author": "Kessler-Roth matching markets",
        },
        {
            "source_dataset": "EERP 2016 supplement (manual)",
            "project": "EERP",
            "pair_id": "manual_eerp_friedman_continuous_time_games",
            "original_title": "Friedman continuous-time games",
            "replication_title": "EERP 2016",
            "outcome": "Friedman continuous-time games",
            "D_original": 0.60,
            "N_original": 120.0,
            "D_replication": 0.50,
            "N_replication": 385.0,
            "raw_file": str(manual_dir / "eerp_2016_supplement.pdf"),
            "match_author": "Friedman continuous-time games",
        },
        {
            "source_dataset": "EERP 2016 supplement (manual)",
            "project": "EERP",
            "pair_id": "manual_eerp_duffy_puzzello_endogenous_institutions",
            "original_title": "Duffy-Puzzello endogenous institutions",
            "replication_title": "EERP 2016",
            "outcome": "Duffy-Puzzello endogenous institutions",
            "D_original": 0.55,
            "N_original": 240.0,
            "D_replication": 0.48,
            "N_replication": 770.0,
            "raw_file": str(manual_dir / "eerp_2016_supplement.pdf"),
            "match_author": "Duffy-Puzzello endogenous institutions",
        },
        {
            "source_dataset": "EERP 2016 supplement (manual)",
            "project": "EERP",
            "pair_id": "manual_eerp_dulleck_expert_markets",
            "original_title": "Dulleck expert markets",
            "replication_title": "EERP 2016",
            "outcome": "Dulleck expert markets",
            "D_original": 0.50,
            "N_original": 288.0,
            "D_replication": 0.40,
            "N_replication": 920.0,
            "raw_file": str(manual_dir / "eerp_2016_supplement.pdf"),
            "match_author": "Dulleck expert markets",
        },
        {
            "source_dataset": "EERP 2016 supplement (manual)",
            "project": "EERP",
            "pair_id": "manual_eerp_kogan_dual_action",
            "original_title": "Kogan dual-action",
            "replication_title": "EERP 2016",
            "outcome": "Kogan dual-action",
            "D_original": 0.45,
            "N_original": 216.0,
            "D_replication": 0.07,
            "N_replication": 690.0,
            "raw_file": str(manual_dir / "eerp_2016_supplement.pdf"),
            "match_author": "Kogan dual-action",
        },
        {
            "source_dataset": "EERP 2016 supplement (manual)",
            "project": "EERP",
            "pair_id": "manual_eerp_de_clippel_choice_consistency",
            "original_title": "de Clippel choice consistency",
            "replication_title": "EERP 2016",
            "outcome": "de Clippel choice consistency",
            "D_original": 0.40,
            "N_original": 144.0,
            "D_replication": 0.05,
            "N_replication": 460.0,
            "raw_file": str(manual_dir / "eerp_2016_supplement.pdf"),
            "match_author": "de Clippel choice consistency",
        },
        {
            "source_dataset": "EERP 2016 supplement (manual)",
            "project": "EERP",
            "pair_id": "manual_eerp_chen_allocation_fairness",
            "original_title": "Chen allocation fairness",
            "replication_title": "EERP 2016",
            "outcome": "Chen allocation fairness",
            "D_original": 0.35,
            "N_original": 200.0,
            "D_replication": 0.08,
            "N_replication": 650.0,
            "raw_file": str(manual_dir / "eerp_2016_supplement.pdf"),
            "match_author": "Chen allocation fairness",
        },
        {
            "source_dataset": "Ranehill 2015 power posing (manual)",
            "project": "Other direct replications",
            "pair_id": "manual_power_pose_ranehill_2015",
            "original_title": "Carney power pose",
            "replication_title": "Ranehill 2015",
            "outcome": "Carney power pose",
            "D_original": 0.65,
            "N_original": 42.0,
            "D_replication": 0.02,
            "N_replication": 200.0,
            "raw_file": str(manual_dir / "ranehill_2015_power_pose.pdf"),
            "match_author": "Carney power pose",
        },
        {
            "source_dataset": "Galak et al. 2012 psi meta-analysis (manual)",
            "project": "Other direct replications",
            "pair_id": "manual_bem_precognition_galak_2012",
            "original_title": "Bem precognition",
            "replication_title": "Galak 2012",
            "outcome": "Bem precognition",
            "D_original": 0.22,
            "N_original": 100.0,
            "D_replication": 0.01,
            "N_replication": 3289.0,
            "raw_file": str(manual_dir / "galak_2012_psi.pdf"),
            "match_author": "Bem precognition",
        },
        {
            "source_dataset": "Doyen et al. 2012 article (manual)",
            "project": "Other direct replications",
            "pair_id": "manual_bargh_elderly_priming_doyen_2012",
            "original_title": "Bargh elderly priming",
            "replication_title": "Doyen 2012",
            "outcome": "Bargh elderly priming",
            "D_original": 0.70,
            "N_original": 30.0,
            "D_replication": 0.02,
            "N_replication": 120.0,
            "raw_file": "https://pmc.ncbi.nlm.nih.gov/articles/PMC3261136/",
            "match_author": "Bargh elderly priming",
        },
        {
            "source_dataset": "RRR Wagenmakers 2016 (manual)",
            "project": "Registered Replication Reports",
            "pair_id": "manual_rrr_strack_pen_in_teeth_wagenmakers_2016",
            "original_title": "Strack pen-in-teeth",
            "replication_title": "RRR Wagenmakers 2016",
            "outcome": "Strack pen-in-teeth",
            "D_original": 0.82,
            "N_original": 92.0,
            "D_replication": 0.03,
            "N_replication": 1894.0,
            "raw_file": "https://doi.org/10.1177/1745691616674458",
            "match_author": "Strack pen-in-teeth",
        },
        {
            "source_dataset": "RRR Hagger 2016 (manual)",
            "project": "Registered Replication Reports",
            "pair_id": "manual_rrr_baumeister_ego_depletion_hagger_2016",
            "original_title": "Baumeister radishes/ego depletion",
            "replication_title": "RRR Hagger 2016",
            "outcome": "Baumeister radishes/ego depletion",
            "D_original": 1.76,
            "N_original": 67.0,
            "D_replication": 0.04,
            "N_replication": 2141.0,
            "raw_file": str(manual_dir / "hagger_2016_ego_depletion.pdf"),
            "match_author": "Baumeister radishes/ego depletion",
        },
        {
            "source_dataset": "RRR Alogna 2014 (manual)",
            "project": "Registered Replication Reports",
            "pair_id": "manual_rrr_schooler_verbal_overshadowing_alogna_2014_r1",
            "original_title": "Schooler verbal overshadowing (RRR1)",
            "replication_title": "RRR Alogna 2014",
            "outcome": "Schooler verbal overshadowing (RRR1)",
            "D_original": 0.80,
            "N_original": 90.0,
            "D_replication": 0.03,
            "N_replication": 2319.0,
            "raw_file": "https://doi.org/10.1177/1745691614545653",
            "match_author": "Schooler verbal overshadowing (RRR1)",
        },
        {
            "source_dataset": "RRR Alogna 2014 (manual)",
            "project": "Registered Replication Reports",
            "pair_id": "manual_rrr_schooler_verbal_overshadowing_alogna_2014_r2",
            "original_title": "Schooler verbal overshadowing (RRR2)",
            "replication_title": "RRR Alogna 2014 v2",
            "outcome": "Schooler verbal overshadowing (RRR2)",
            "D_original": 0.80,
            "N_original": 90.0,
            "D_replication": 0.16,
            "N_replication": 3026.0,
            "raw_file": "https://doi.org/10.1177/1745691614545653",
            "match_author": "Schooler verbal overshadowing (RRR2)",
        },
        {
            "source_dataset": "RRR O'Donnell 2018 (manual)",
            "project": "Registered Replication Reports",
            "pair_id": "manual_rrr_dijksterhuis_professor_priming_odonnell_2018",
            "original_title": "Dijksterhuis professor priming",
            "replication_title": "RRR O'Donnell 2018",
            "outcome": "Dijksterhuis professor priming",
            "D_original": 0.51,
            "N_original": 80.0,
            "D_replication": 0.01,
            "N_replication": 4493.0,
            "raw_file": str(manual_dir / "odonnell_2018_professor_priming.pdf"),
            "match_author": "Dijksterhuis professor priming",
        },
        {
            "source_dataset": "RRR Verschuere 2018 (manual)",
            "project": "Registered Replication Reports",
            "pair_id": "manual_rrr_moral_reminders_verschuere_2018",
            "original_title": "Mazar/Amir/Ariely moral reminders",
            "replication_title": "RRR Verschuere 2018",
            "outcome": "Mazar/Amir/Ariely moral reminders",
            "D_original": 0.48,
            "N_original": 229.0,
            "D_replication": 0.02,
            "N_replication": 5786.0,
            "raw_file": "https://doi.org/10.1177/2515245918781032",
            "match_author": "Mazar/Amir/Ariely moral reminders",
        },
        {
            "source_dataset": "RRR Bouwmeester 2017 (manual)",
            "project": "Registered Replication Reports",
            "pair_id": "manual_rrr_intuitive_cooperation_bouwmeester_2017",
            "original_title": "Rand et al intuitive cooperation",
            "replication_title": "RRR Bouwmeester 2017",
            "outcome": "Rand et al intuitive cooperation",
            "D_original": 0.40,
            "N_original": 343.0,
            "D_replication": 0.01,
            "N_replication": 3596.0,
            "raw_file": "https://doi.org/10.1177/1745691617693624",
            "match_author": "Rand et al intuitive cooperation",
        },
        {
            "source_dataset": "RRR Cheung 2016 (manual)",
            "project": "Registered Replication Reports",
            "pair_id": "manual_rrr_commitment_forgiveness_cheung_2016",
            "original_title": "Finkel commitment/forgiveness",
            "replication_title": "RRR Cheung 2016",
            "outcome": "Finkel commitment/forgiveness",
            "D_original": 0.40,
            "N_original": 98.0,
            "D_replication": 0.28,
            "N_replication": 5070.0,
            "raw_file": "https://doi.org/10.1177/1745691616664694",
            "match_author": "Finkel commitment/forgiveness",
        },
        {
            "source_dataset": "Srull-Wyer RRR paper (manual)",
            "project": "Registered Replication Reports",
            "pair_id": "manual_rrr_srull_wyer_hostility_priming",
            "original_title": "Srull-Wyer hostility priming",
            "replication_title": "RRR McCarthy 2018",
            "outcome": "Srull-Wyer hostility priming",
            "D_original": 0.35,
            "N_original": 96.0,
            "D_replication": 0.06,
            "N_replication": 7300.0,
            "raw_file": str(RAW_REPL / "rrr" / "srull_wyer_1979_rrr.pdf"),
            "match_author": "Srull-Wyer hostility priming",
        },
        {
            "source_dataset": "RPP project record alias (manual)",
            "project": "OSC 2015",
            "pair_id": "manual_osc_mckinstry_2008_motion",
            "original_title": "RPP McKinstry 2008 motion",
            "replication_title": "RPP 2015",
            "outcome": "RPP McKinstry 2008 motion",
            "D_original": 1.32,
            "N_original": 28.0,
            "D_replication": 1.01,
            "N_replication": 110.0,
            "raw_file": "https://osf.io/d0n81/",
            "match_author": "RPP McKinstry 2008 motion",
        },
        {
            "source_dataset": "ReplicationSuccess SSRP alias (manual)",
            "project": "OSC 2015",
            "pair_id": "manual_osc_morewedge_2008_imagined",
            "original_title": "RPP Morewedge 2008 imagined",
            "replication_title": "RPP 2015",
            "outcome": "RPP Morewedge 2008 imagined",
            "D_original": 1.32,
            "N_original": 52.0,
            "D_replication": 0.63,
            "N_replication": 160.0,
            "raw_file": str(RAW_REPL / "replicationsuccess" / "SSRP.rda"),
            "match_author": "RPP Morewedge 2008 imagined",
        },
        {
            "source_dataset": "RPP project record alias (manual)",
            "project": "OSC 2015",
            "pair_id": "manual_osc_rule_2008_face_perception",
            "original_title": "RPP Rule 2008 face perception",
            "replication_title": "RPP 2015",
            "outcome": "RPP Rule 2008 face perception",
            "D_original": 1.32,
            "N_original": 50.0,
            "D_replication": 0.87,
            "N_replication": 155.0,
            "raw_file": "https://osf.io/r5gpv/",
            "match_author": "RPP Rule 2008 face perception",
        },
        {
            "source_dataset": "RPP project record alias (manual)",
            "project": "OSC 2015",
            "pair_id": "manual_osc_nurmsoo_2008_children_trust",
            "original_title": "RPP Nurmsoo 2008 children trust",
            "replication_title": "RPP 2015",
            "outcome": "RPP Nurmsoo 2008 children trust",
            "D_original": 1.15,
            "N_original": 40.0,
            "D_replication": 0.45,
            "N_replication": 120.0,
            "raw_file": "https://osf.io/aczvt/",
            "match_author": "RPP Nurmsoo 2008 children trust",
        },
        {
            "source_dataset": "ReplicationSuccess SSRP alias (manual)",
            "project": "OSC 2015",
            "pair_id": "manual_osc_duncan_2008_memory",
            "original_title": "RPP Duncan 2008 memory",
            "replication_title": "RPP 2015",
            "outcome": "RPP Duncan 2008 memory",
            "D_original": 1.01,
            "N_original": 45.0,
            "D_replication": 0.41,
            "N_replication": 180.0,
            "raw_file": str(RAW_REPL / "replicationsuccess" / "SSRP.rda"),
            "match_author": "RPP Duncan 2008 memory",
        },
        {
            "source_dataset": "RPP project record alias (manual)",
            "project": "OSC 2015",
            "pair_id": "manual_osc_mirman_2008_phonology",
            "original_title": "RPP Mirman 2008 phonology",
            "replication_title": "RPP 2015",
            "outcome": "RPP Mirman 2008 phonology",
            "D_original": 0.93,
            "N_original": 55.0,
            "D_replication": 0.70,
            "N_replication": 170.0,
            "raw_file": "https://osf.io/rvkc5/",
            "match_author": "RPP Mirman 2008 phonology",
        },
        {
            "source_dataset": "ReplicationSuccess SSRP alias (manual)",
            "project": "OSC 2015",
            "pair_id": "manual_osc_ackerman_2010_haptic",
            "original_title": "RPP Ackerman 2010 haptic",
            "replication_title": "RPP 2015",
            "outcome": "RPP Ackerman 2010 haptic",
            "D_original": 0.87,
            "N_original": 80.0,
            "D_replication": 0.08,
            "N_replication": 320.0,
            "raw_file": str(RAW_REPL / "replicationsuccess" / "SSRP.rda"),
            "match_author": "RPP Ackerman 2010 haptic",
        },
        {
            "source_dataset": "Many Labs 4 local meta-analysis (manual)",
            "project": "Many Labs 4",
            "pair_id": "manual_ml4_mortality_salience_greenberg_1994",
            "original_title": "Mortality salience (Greenberg 1994)",
            "replication_title": "Many Labs 4",
            "outcome": "Mortality salience (Greenberg 1994)",
            "D_original": 0.60,
            "N_original": 124.0,
            "D_replication": 0.03,
            "N_replication": 2281.0,
            "raw_file": str(RAW_REPL / "ml4" / "results.RData"),
            "match_author": "Mortality salience (Greenberg 1994)",
        },
        {
            "source_dataset": "Marek 2022 BWAS paper (manual)",
            "project": "Marek 2022 BWAS",
            "pair_id": "manual_marek_2022_bwas",
            "original_title": "Brain-behavior r (BWAS pre-2022)",
            "replication_title": "Marek 2022 BWAS",
            "outcome": "Brain-behavior r (BWAS pre-2022)",
            "D_original": 1.50,
            "N_original": 25.0,
            "D_replication": 0.16,
            "N_replication": 50000.0,
            "raw_file": str(manual_dir / "marek_2022_bwas.pdf"),
            "match_author": "Brain-behavior r (BWAS pre-2022)",
        },
    ]

    out = pair_frame(
        source_dataset=[row["source_dataset"] for row in rows],
        project=[row["project"] for row in rows],
        pair_id=[row["pair_id"] for row in rows],
        original_title=[row["original_title"] for row in rows],
        replication_title=[row["replication_title"] for row in rows],
        original_doi=["" for _ in rows],
        replication_doi=["" for _ in rows],
        outcome=[row["outcome"] for row in rows],
        D_original=[row["D_original"] for row in rows],
        N_original=[row["N_original"] for row in rows],
        D_replication=[row["D_replication"] for row in rows],
        N_replication=[row["N_replication"] for row in rows],
        raw_file=[row["raw_file"] for row in rows],
        match_author=[row["match_author"] for row in rows],
    )
    return assign_match_keys(filter_usable_pairs(out), "match_author")


def build_all_pairs() -> pd.DataFrame:
    pairs = pd.concat(
        [
            build_rpp_pairs(),
            build_ssrp_pairs(),
            build_ml1_pairs(),
            build_ml2_pairs(),
            build_ml3_pairs(),
            build_eprp_pairs(),
            build_eerp_pairs(),
            build_ml5_pairs(),
            build_rpcb_pairs(),
            build_score_pairs(),
            build_pipeline_pairs(),
            build_decision_market_pairs(),
            build_loopr_pairs(),
            build_boyce_pairs(),
            build_rescue_pairs(),
            build_clinical_pairs(),
            build_bri_pairs(),
            build_fred_pairs(),
            build_odonnell_rrr_pairs(),
            build_schooler_rrr_pairs(),
            build_hagger_rrr_pairs(),
            build_eerland_rrr_pairs(),
            build_wagenmakers_rrr_pair(),
            build_vaidis_rrr_pairs(),
            build_stoevenbelt_rrr_pairs(),
            build_sports_replication_pairs(),
            build_verified_manual_pairs(),
            build_harvested_lead_pairs(),
        ],
        ignore_index=True,
    )
    pairs = collapse_endpoint_pairs(pairs)
    pairs = assign_match_keys(pairs, "match_author")
    return annotate_pair_flags(pairs)


def appendix_replication_to_project(replication: str) -> str:
    if replication.startswith("RRR "):
        return "Registered Replication Reports"
    if replication == "Many Labs 1":
        return "Many Labs 1"
    if replication == "Many Labs 2":
        return "Many Labs 2"
    if replication == "Many Labs 3":
        return "Many Labs 3"
    if replication == "Many Labs 4":
        return "Many Labs 4"
    if replication == "Many Labs 5":
        return "Many Labs 5"
    if replication == "SSRP":
        return "SSRP"
    if replication == "EERP 2016":
        return "EERP"
    if replication == "RPP 2015":
        return "OSC 2015"
    if replication == "RP:CB 2021":
        return "RPCB"
    if replication.startswith("SCORE "):
        return "SCORE"
    if replication == "Cova 2018 xphi":
        return "EPRP"
    if replication == "Pipeline Project 2016":
        return "Pipeline Project"
    if replication == "DellaVigna-Linos 2022":
        return "DellaVigna-Linos 2022"
    if replication == "Marek 2022 BWAS":
        return "Marek 2022 BWAS"
    return "Other direct replications"


def build_appendix_pairs() -> pd.DataFrame:
    soup = BeautifulSoup(APPENDIX_HTML.read_text(), "html.parser")
    table = soup.find("table", {"class": "replpairs"})
    if table is None:
        raise FileNotFoundError(f"Could not find Appendix D replication table in {APPENDIX_HTML}")

    rows = []
    for tr in table.find_all("tr")[1:]:
        cells = [cell.get_text(" ", strip=True) for cell in tr.find_all("td")]
        if len(cells) != 7:
            continue
        idx, study, n_orig, d_orig, n_repl, d_repl, replication = cells
        rows.append(
            {
                "source_dataset": "Appendix D supplemental",
                "project": appendix_replication_to_project(replication),
                "pair_id": f"appendix_{idx}",
                "original_title": study,
                "replication_title": replication,
                "original_doi": "",
                "replication_doi": "",
                "outcome": study,
                "D_original": abs(float(d_orig.replace(",", ""))),
                "N_original": float(n_orig.replace(",", "")),
                "D_replication": abs(float(d_repl.replace(",", ""))),
                "N_replication": float(n_repl.replace(",", "")),
                "raw_file": str(APPENDIX_HTML),
                "appendix_row_num": int(idx),
                "pair_origin": "appendix_backfill",
                "match_author": study,
            }
        )

    appendix = assign_match_keys(filter_usable_pairs(pd.DataFrame(rows)), "match_author")
    return annotate_pair_flags(appendix)


def build_rule_subset(pairs: pd.DataFrame) -> pd.DataFrame:
    return pairs[
        pairs["larger_n_replication"]
        & (pairs["N_original"] >= 10)
        & (pairs["N_replication"] >= 10)
    ].copy()


def build_plot_subset(pairs: pd.DataFrame) -> pd.DataFrame:
    rule = build_rule_subset(pairs).copy()
    x_min = 10.0
    x_max = 100_000.0
    y_min = 0.02
    y_max = 5.0

    rule["clip_n_max"] = (rule["N_original"] > x_max) | (rule["N_replication"] > x_max)
    rule["clip_d_low"] = (rule["D_original"] < y_min) | (rule["D_replication"] < y_min)
    rule["clip_d_high"] = (rule["D_original"] > y_max) | (rule["D_replication"] > y_max)
    rule["plot_clipped"] = rule[["clip_n_max", "clip_d_low", "clip_d_high"]].any(axis=1)

    rule["plot_N_original"] = rule["N_original"].clip(lower=x_min, upper=x_max)
    rule["plot_N_replication"] = rule["N_replication"].clip(lower=x_min, upper=x_max)
    rule["plot_D_original"] = rule["D_original"].clip(lower=y_min, upper=y_max)
    rule["plot_D_replication"] = rule["D_replication"].clip(lower=y_min, upper=y_max)
    return rule


def apply_appendix_project_floor(current_pairs: pd.DataFrame, appendix_pairs: pd.DataFrame) -> pd.DataFrame:
    current = current_pairs.copy()
    appendix = appendix_pairs.copy()
    if "pair_origin" not in current.columns:
        current["pair_origin"] = "source_recovered"
    if "pair_origin" not in appendix.columns:
        appendix["pair_origin"] = "appendix_backfill"
    if "match_key" not in current.columns:
        current["match_key"] = ""
    if "match_key" not in appendix.columns:
        appendix["match_key"] = ""

    projects = sorted(set(current["project"]).union(set(appendix["project"])))
    chunks: list[pd.DataFrame] = []

    for project in projects:
        cur = current.loc[current["project"] == project].copy()
        app = appendix.loc[appendix["project"] == project].copy()
        target = len(app)

        if target == 0:
            if not cur.empty:
                chunks.append(cur)
            continue
        if len(cur) >= target:
            chunks.append(cur)
            continue
        if cur.empty:
            chunks.append(app)
            continue

        cur = cur.sort_values(
            ["D_original", "N_original", "D_replication", "N_replication", "pair_id"],
            ascending=[False, False, False, False, True],
        )
        app = app.sort_values(
            ["D_original", "N_original", "D_replication", "N_replication", "pair_id"],
            ascending=[False, False, False, False, True],
        )

        current_keys = {key for key in cur["match_key"].astype(str) if key}
        residual = app.loc[~app["match_key"].astype(str).isin(current_keys)].copy()

        if len(residual) < (target - len(cur)):
            residual = app.iloc[len(cur) :].copy()

        need = max(target - len(cur), 0)
        take_appendix = residual.head(need).copy()
        chunks.append(pd.concat([cur, take_appendix], ignore_index=True))

    enhanced = pd.concat(chunks, ignore_index=True)
    return enhanced.sort_values(["project", "N_original", "D_original", "pair_id"]).reset_index(drop=True)


def normalized_log_hist(values: pd.Series | np.ndarray, vmin: float, vmax: float, bins: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    vals = pd.to_numeric(pd.Series(values), errors="coerce")
    vals = vals[np.isfinite(vals)]
    if vals.empty:
        return bins, np.zeros(len(bins) - 1, dtype=float)

    vals = vals.clip(lower=vmin, upper=vmax).to_numpy(dtype=float)
    counts, edges = np.histogram(vals, bins=bins)
    counts = counts.astype(float)
    peak = float(np.nanmax(counts)) if np.size(counts) else 0.0
    if peak > 0:
        counts = counts / peak
    return edges, counts


def plot_pairs(df: pd.DataFrame, stats_df: pd.DataFrame, out_png: Path) -> None:
    ensure_dir(out_png.parent)

    colors = {
        "shrunk_still_sig": "#c8741f",
        "shrunk_below_sig": "#b94840",
        "grew": "#2d8b7d",
    }
    density_colors = {
        "original": "#2b2b2b",
        "replication": "#4e72b8",
    }
    ols_color = "#7a3db8"

    x_min = 10.0
    x_max = 100_000.0
    y_min = 0.02
    y_max = 5.0

    fig = plt.figure(figsize=(8.4, 8.9), dpi=180)
    outer = fig.add_gridspec(
        2,
        2,
        height_ratios=[6.8, 2.1],
        width_ratios=[6.0, 0.8],
        hspace=0.16,
        wspace=0.02,
    )
    upper = outer[0, :].subgridspec(
        2,
        2,
        height_ratios=[0.8, 6.0],
        width_ratios=[6.0, 0.8],
        hspace=0.01,
        wspace=0.02,
    )
    ax_top = fig.add_subplot(upper[0, 0])
    ax = fig.add_subplot(upper[1, 0], sharex=ax_top)
    ax_right = fig.add_subplot(upper[1, 1], sharey=ax)
    ax_bottom = fig.add_subplot(outer[1, 0])
    ax_bottom_blank = fig.add_subplot(outer[1, 1])
    ax_bottom_blank.axis("off")
    ax_bottom.set_zorder(0)
    ax_bottom.patch.set_visible(False)
    ax.set_zorder(2)
    ax_right.set_zorder(2)
    ax_top.set_zorder(2)

    for cat in ["shrunk_still_sig", "shrunk_below_sig", "grew"]:
        g = df[df["category"] == cat]
        for row in g.itertuples(index=False):
            ax.annotate(
                "",
                xy=(row.plot_N_replication, row.plot_D_replication),
                xytext=(row.plot_N_original, row.plot_D_original),
                arrowprops=dict(
                    arrowstyle="->",
                    color=colors[cat],
                    lw=0.7,
                    alpha=0.34,
                    shrinkA=0,
                    shrinkB=0,
                    mutation_scale=5.2,
                ),
                zorder=1,
            )

    x = np.logspace(np.log10(x_min), np.log10(x_max), 400)
    boundary_specs = [
        ("p=.10", p10_boundary, ":", Z_10),
        ("p=.05", p05_boundary, "--", Z_05),
        ("p=.01", p01_boundary, "-.", Z_01),
    ]
    label_transform = blended_transform_factory(ax.transData, ax.transAxes)
    for label, fn, linestyle, z_crit in boundary_specs:
        ax.plot(x, fn(x), color="#2a2a2a", linestyle=linestyle, lw=1.2, zorder=3)
        label_x = min(max(((2 * z_crit / y_min) ** 2) * 0.78, x_min * 1.05), x_max / 1.08)
        ax.text(
            label_x,
            -0.045,
            label,
            color="#606060",
            fontsize=8.2,
            rotation=53,
            ha="center",
            va="top",
            transform=label_transform,
            rotation_mode="anchor",
            zorder=4,
        )

    all_n = np.concatenate(
        [
            pd.to_numeric(stats_df["N_original"], errors="coerce").to_numpy(),
            pd.to_numeric(stats_df["N_replication"], errors="coerce").to_numpy(),
        ]
    )
    all_d = np.concatenate(
        [
            pd.to_numeric(stats_df["D_original"], errors="coerce").to_numpy(),
            pd.to_numeric(stats_df["D_replication"], errors="coerce").to_numpy(),
        ]
    )
    ols_mask = np.isfinite(all_n) & np.isfinite(all_d) & (all_n > 0) & (all_d > 0)
    ols_slope, ols_intercept = np.polyfit(np.log10(all_n[ols_mask]), np.log10(all_d[ols_mask]), 1)
    ols_y = 10 ** (ols_intercept + ols_slope * np.log10(x))
    ols_factor_10x = 10 ** ols_slope
    ols_pct_change_10x = (1 - ols_factor_10x) * 100
    ax.plot(x, ols_y, color=ols_color, lw=1.6, alpha=0.98, zorder=3.4)
    ax.plot(
        [0.03, 0.095],
        [0.965, 0.965],
        transform=ax.transAxes,
        color=ols_color,
        lw=1.7,
        solid_capstyle="round",
        clip_on=False,
        zorder=4.4,
    )
    ax.text(
        0.105,
        0.965,
        f"log-log OLS: {ols_pct_change_10x:.0f}% lower D per 10x N",
        transform=ax.transAxes,
        ha="left",
        va="center",
        fontsize=8.1,
        color=ols_color,
        bbox=dict(facecolor="white", edgecolor="none", alpha=0.8, pad=1.8),
        zorder=4.5,
    )

    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlim(x_min, x_max)
    ax.set_ylim(y_min, y_max)
    ax.set_axisbelow(True)
    ax.set_xlabel("Sample size N (log scale)", fontweight="bold", labelpad=2)
    ax.set_ylabel("Reported effect size D (log scale)")
    counts = stats_df["category"].value_counts()
    total = len(stats_df)
    shrunk_count = counts.get("shrunk_still_sig", 0) + counts.get("shrunk_below_sig", 0)
    shrunk_pct = 100 * shrunk_count / total if total else np.nan
    turn_insig_pct = 100 * counts.get("shrunk_below_sig", 0) / total if total else np.nan
    if np.isfinite(ols_pct_change_10x) and ols_pct_change_10x >= 0:
        tenfold_phrase = f"Effect Sizes Shrink {ols_pct_change_10x:.0f}% for each 10x in N"
    elif np.isfinite(ols_pct_change_10x):
        tenfold_phrase = f"Effect Sizes Grow {abs(ols_pct_change_10x):.0f}% for each 10x in N"
    else:
        tenfold_phrase = "Effect-size change per 10x in N unavailable"
    d_orig_med_summary = float(pd.to_numeric(stats_df["D_original"], errors="coerce").median())
    d_repl_med_summary = float(pd.to_numeric(stats_df["D_replication"], errors="coerce").median())

    fig.suptitle(
        f"Huge Effect Sizes Evaporate In Larger Replication Attempts ({len(stats_df):,} replications)",
        fontsize=12.2,
        fontweight="bold",
        y=0.968,
    )
    fig.text(
        0.5,
        0.933,
        f"{tenfold_phrase}; {shrunk_pct:.0f}% of effects shrink; {turn_insig_pct:.0f}% of effects turn insig.",
        ha="center",
        va="center",
        fontsize=10.0,
        color="#333333",
    )

    x_bins = np.logspace(np.log10(x_min), np.log10(x_max), 32)
    y_bins = np.logspace(np.log10(y_min), np.log10(y_max), 28)
    n_orig_edges, n_orig_hist = normalized_log_hist(stats_df["N_original"], x_min, x_max, x_bins)
    n_repl_edges, n_repl_hist = normalized_log_hist(stats_df["N_replication"], x_min, x_max, x_bins)
    d_orig_edges, d_orig_hist = normalized_log_hist(stats_df["D_original"], y_min, y_max, y_bins)
    d_repl_edges, d_repl_hist = normalized_log_hist(stats_df["D_replication"], y_min, y_max, y_bins)

    def top_hist_xy(edges: np.ndarray, counts: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        x_vals = np.r_[edges[0], np.repeat(edges, 2)[1:-1], edges[-1]]
        y_vals = np.r_[0.0, np.repeat(counts, 2), 0.0]
        return x_vals, y_vals

    def right_hist_xy(edges: np.ndarray, counts: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        x_vals = np.r_[0.0, np.repeat(counts, 2), 0.0]
        y_vals = np.r_[edges[0], np.repeat(edges, 2)[1:-1], edges[-1]]
        return x_vals, y_vals

    x_orig_plot, y_orig_plot = top_hist_xy(n_orig_edges, n_orig_hist)
    x_repl_plot, y_repl_plot = top_hist_xy(n_repl_edges, n_repl_hist)
    x_right_orig, y_right_orig = right_hist_xy(d_orig_edges, d_orig_hist)
    x_right_repl, y_right_repl = right_hist_xy(d_repl_edges, d_repl_hist)

    ax_top.plot(x_orig_plot, y_orig_plot, color=density_colors["original"], lw=1.3, alpha=0.98)
    ax_top.plot(x_repl_plot, y_repl_plot, color=density_colors["replication"], lw=1.3, alpha=0.98)
    ax_right.plot(x_right_orig, y_right_orig, color=density_colors["original"], lw=1.3, alpha=0.98)
    ax_right.plot(x_right_repl, y_right_repl, color=density_colors["replication"], lw=1.3, alpha=0.98)
    ax_top.axhline(0, color="#5a5a5a", lw=0.8, zorder=0)
    ax_right.axvline(0, color="#5a5a5a", lw=0.8, zorder=0)

    n_orig_med = float(pd.to_numeric(stats_df["N_original"], errors="coerce").median())
    n_repl_med = float(pd.to_numeric(stats_df["N_replication"], errors="coerce").median())
    d_orig_med = float(pd.to_numeric(stats_df["D_original"], errors="coerce").median())
    d_repl_med = float(pd.to_numeric(stats_df["D_replication"], errors="coerce").median())
    top_label_transform = blended_transform_factory(ax_top.transData, ax_top.transAxes)
    right_label_transform = blended_transform_factory(ax_right.transAxes, ax_right.transData)

    if np.isfinite(n_orig_med):
        n_orig_med_clip = float(np.clip(n_orig_med, x_min, x_max))
        ax_top.axvline(
            n_orig_med_clip,
            color=density_colors["original"],
            lw=1.0,
            linestyle="--",
            alpha=0.9,
            zorder=1,
        )
        ax_top.annotate(
            f"N\u0303 = {format_n_tick(n_orig_med)}",
            xy=(n_orig_med_clip, 1.0),
            xycoords=top_label_transform,
            xytext=(0, 2),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=7.4,
            color=density_colors["original"],
            clip_on=False,
        )
    if np.isfinite(n_repl_med):
        n_repl_med_clip = float(np.clip(n_repl_med, x_min, x_max))
        ax_top.axvline(
            n_repl_med_clip,
            color=density_colors["replication"],
            lw=1.0,
            linestyle="--",
            alpha=0.9,
            zorder=1,
        )
        ax_top.annotate(
            f"N\u0303 = {format_n_tick(n_repl_med)}",
            xy=(n_repl_med_clip, 1.0),
            xycoords=top_label_transform,
            xytext=(0, 2),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=7.4,
            color=density_colors["replication"],
            clip_on=False,
        )
    if np.isfinite(d_orig_med):
        d_orig_med_clip = float(np.clip(d_orig_med, y_min, y_max))
        ax_right.axhline(
            d_orig_med_clip,
            color=density_colors["original"],
            lw=1.0,
            linestyle="--",
            alpha=0.9,
            zorder=1,
        )
        ax_right.annotate(
            rf"$\tilde{{x}}={format_d_tick(d_orig_med)}$",
            xy=(1.0, d_orig_med_clip),
            xycoords=right_label_transform,
            xytext=(2, 0),
            textcoords="offset points",
            ha="left",
            va="center",
            fontsize=7.4,
            color=density_colors["original"],
            clip_on=False,
        )
    if np.isfinite(d_repl_med):
        d_repl_med_clip = float(np.clip(d_repl_med, y_min, y_max))
        ax_right.axhline(
            d_repl_med_clip,
            color=density_colors["replication"],
            lw=1.0,
            linestyle="--",
            alpha=0.9,
            zorder=1,
        )
        ax_right.annotate(
            rf"$\tilde{{x}}={format_d_tick(d_repl_med)}$",
            xy=(1.0, d_repl_med_clip),
            xycoords=right_label_transform,
            xytext=(2, 0),
            textcoords="offset points",
            ha="left",
            va="center",
            fontsize=7.4,
            color=density_colors["replication"],
            clip_on=False,
        )

    ax_top.set_ylim(0, 1.08)
    ax_right.set_xlim(0, 1.08)
    ax_top.tick_params(axis="x", which="both", bottom=False, labelbottom=False)
    ax_top.tick_params(axis="y", which="both", left=False, labelleft=False)
    ax_right.tick_params(axis="x", which="both", bottom=False, labelbottom=False)
    ax_right.tick_params(axis="y", which="both", left=False, labelleft=False)
    for spine in ["top", "right", "left", "bottom"]:
        ax_top.spines[spine].set_visible(False)
        ax_right.spines[spine].set_visible(False)
    ax_top.grid(False)
    ax_right.grid(False)
    ax_top.set_facecolor("none")
    ax_right.set_facecolor("none")
    ax_top.legend(
        [
            Line2D([0], [0], color=density_colors["original"], lw=1.4),
            Line2D([0], [0], color=density_colors["replication"], lw=1.4),
        ],
        ["Original", "Replication"],
        loc="upper right",
        frameon=False,
        fontsize=7.8,
        handlelength=2.2,
        borderaxespad=0.2,
    )

    linear_d_max = 3.0
    linear_bin_width = 0.1
    linear_bins = np.arange(0, linear_d_max + linear_bin_width, linear_bin_width)
    d_orig_linear = pd.to_numeric(stats_df["D_original"], errors="coerce").dropna().clip(lower=0, upper=linear_d_max)
    d_repl_linear = pd.to_numeric(stats_df["D_replication"], errors="coerce").dropna().clip(lower=0, upper=linear_d_max)

    ax_bottom.hist(
        d_repl_linear,
        bins=linear_bins,
        density=True,
        histtype="step",
        linewidth=1.6,
        color=density_colors["replication"],
        label="Replications",
    )
    ax_bottom.hist(
        d_orig_linear,
        bins=linear_bins,
        density=True,
        histtype="step",
        linewidth=1.6,
        color=density_colors["original"],
        label="Originals",
    )
    ax_bottom.set_xlim(0, linear_d_max)
    linear_ticks = np.arange(0, linear_d_max + 0.001, 0.5)
    linear_tick_labels = [f"{tick:g}" for tick in linear_ticks]
    linear_tick_labels[-1] = "3+"
    ax_bottom.set_xticks(linear_ticks)
    ax_bottom.set_xticklabels(linear_tick_labels)
    ax_bottom.set_ylabel("Density")
    ax_bottom.set_xlabel("Reported effect size magnitude (|Cohen's d|, linear scale)", fontweight="bold")
    bottom_label_transform = blended_transform_factory(ax_bottom.transData, ax_bottom.transAxes)
    if np.isfinite(d_orig_med):
        d_orig_med_linear = float(np.clip(d_orig_med, 0.0, linear_d_max))
        ax_bottom.axvline(
            d_orig_med_linear,
            color=density_colors["original"],
            lw=1.0,
            linestyle="--",
            alpha=0.9,
            zorder=1,
        )
        ax_bottom.annotate(
            rf"$\tilde{{x}}={format_d_tick(d_orig_med)}$",
            xy=(d_orig_med_linear, 1.0),
            xycoords=bottom_label_transform,
            xytext=(0, 2),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=7.4,
            color=density_colors["original"],
            clip_on=False,
        )
    if np.isfinite(d_repl_med):
        d_repl_med_linear = float(np.clip(d_repl_med, 0.0, linear_d_max))
        ax_bottom.axvline(
            d_repl_med_linear,
            color=density_colors["replication"],
            lw=1.0,
            linestyle="--",
            alpha=0.9,
            zorder=1,
        )
        ax_bottom.annotate(
            rf"$\tilde{{x}}={format_d_tick(d_repl_med)}$",
            xy=(d_repl_med_linear, 1.0),
            xycoords=bottom_label_transform,
            xytext=(0, 2),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=7.4,
            color=density_colors["replication"],
            clip_on=False,
        )
    ax_bottom.legend(
        [
            Line2D([0], [0], color=density_colors["original"], lw=1.6),
            Line2D([0], [0], color=density_colors["replication"], lw=1.6),
        ],
        ["Original", "Replication"],
        loc="upper right",
        bbox_to_anchor=(0.995, 0.995),
        frameon=False,
        fontsize=7.8,
        handlelength=2.2,
        borderaxespad=0.15,
    )
    ax_bottom.grid(False)
    for spine in ["top", "right"]:
        ax_bottom.spines[spine].set_visible(False)

    x_ticks = [10, 100, 1000, 10000, 100000, 1000000, 10000000, 100000000]
    x_ticks = [tick for tick in x_ticks if x_min <= tick <= x_max]
    ax.xaxis.set_major_locator(FixedLocator(x_ticks))
    ax.xaxis.set_major_formatter(FixedFormatter([format_n_tick(tick) for tick in x_ticks]))
    ax.xaxis.set_minor_formatter(NullFormatter())
    y_ticks = [0.001, 0.002, 0.005, 0.01, 0.02, 0.05, 0.1, 0.2, 0.5, 1, 2, 5, 10, 20, 50, 100]
    y_ticks = [tick for tick in y_ticks if y_min <= tick <= y_max]
    ax.yaxis.set_major_locator(FixedLocator(y_ticks))
    ax.yaxis.set_major_formatter(FixedFormatter([format_d_tick(tick) for tick in y_ticks]))
    ax.yaxis.set_minor_formatter(NullFormatter())
    ax.grid(True, which="major", color="#dddddd", lw=0.7, alpha=0.7, zorder=0)
    ax.grid(False, which="minor")
    for spine in ["top", "right"]:
        ax.spines[spine].set_visible(False)

    handles = [
        Line2D([0], [0], color=colors["grew"], lw=1.2, alpha=0.75, marker=">", markersize=3),
        Line2D([0], [0], color=colors["shrunk_still_sig"], lw=1.2, alpha=0.75, marker=">", markersize=3),
        Line2D([0], [0], color=colors["shrunk_below_sig"], lw=1.2, alpha=0.75, marker=">", markersize=3),
    ]
    labels = [
        f"same/grew ({counts.get('grew', 0):,}, {counts.get('grew', 0) / total:.0%})",
        f"shrank but still sig ({counts.get('shrunk_still_sig', 0):,}, {counts.get('shrunk_still_sig', 0) / total:.0%})",
        f"shrunk below p < .05 ({counts.get('shrunk_below_sig', 0):,}, {counts.get('shrunk_below_sig', 0) / total:.0%})",
    ]
    ax.legend(
        handles,
        labels,
        loc="upper right",
        bbox_to_anchor=(1.01, 0.995),
        ncol=1,
        frameon=False,
        fontsize=8.4,
        handlelength=2.6,
        labelspacing=0.55,
        borderaxespad=0.2,
    )

    clip_n = int(df.get("clip_n_max", pd.Series(False, index=df.index)).sum())
    clip_d_low = int(df.get("clip_d_low", pd.Series(False, index=df.index)).sum())
    clip_d_high = int(df.get("clip_d_high", pd.Series(False, index=df.index)).sum())
    fig.subplots_adjust(bottom=0.12, top=0.885, left=0.10, right=0.93)
    fig.text(
        0.5,
        0.025,
        f"Clipped to plotting window: 10 <= N <= 100k and 0.02 <= D <= 5 "
        f"(N>100k {clip_n}, D<0.02 {clip_d_low}, D>5 {clip_d_high}).",
        ha="center",
        va="center",
        fontsize=8.2,
        color="#555555",
    )
    fig.savefig(out_png, bbox_inches="tight")
    plt.close(fig)


def write_summary(
    all_pairs: pd.DataFrame,
    source_rule_pairs: pd.DataFrame,
    source_fig_pairs: pd.DataFrame,
    rule_pairs: pd.DataFrame,
    fig_pairs: pd.DataFrame,
    out_md: Path,
) -> None:
    ensure_dir(out_md.parent)
    all_project_counts = all_pairs.groupby("project").size().sort_values(ascending=False)
    rule_project_counts = rule_pairs.groupby("project").size().sort_values(ascending=False)
    fig_project_counts = fig_pairs.groupby("project").size().sort_values(ascending=False)
    appendix_rule_added = len(rule_pairs) - len(source_rule_pairs)
    appendix_fig_added = len(fig_pairs) - len(source_fig_pairs)
    lines = [
        "# Draft Figure 2 Summary",
        "",
        f"- All on-hand source-recovered pair rows with usable original and replication D/N: **{len(all_pairs):,}**",
        f"- Source-recovered Figure 2 subset before Appendix D backfill: **{len(source_rule_pairs):,}**",
        f"- Figure 2 subset after Appendix D backfill: **{len(rule_pairs):,}**",
        f"- Source-recovered plotted subset before Appendix D backfill: **{len(source_fig_pairs):,}**",
        f"- Plotted subset after Appendix D backfill: **{len(fig_pairs):,}**",
        f"- Appendix D rows added to the rule subset: **{appendix_rule_added:,}**",
        f"- Appendix D rows added to the plotted subset: **{appendix_fig_added:,}**",
        f"- Projects represented in the plotted subset: **{fig_pairs['project'].nunique()}**",
        "",
        "## All usable pairs by project",
        "",
    ]
    for project, n in all_project_counts.items():
        lines.append(f"- {project}: **{n:,}**")
    lines += [
        "",
        "## Rule-qualified subset by project",
        "",
    ]
    for project, n in rule_project_counts.items():
        lines.append(f"- {project}: **{n:,}**")
    lines += [
        "",
        "## Plotted subset by project",
        "",
    ]
    for project, n in fig_project_counts.items():
        lines.append(f"- {project}: **{n:,}**")
    lines += [
        "",
        "## Rule-Qualified Arrow Categories",
        "",
        f"- shrunk, still significant: **{rule_pairs['category'].value_counts().get('shrunk_still_sig', 0):,}**",
        f"- shrunk below p < .05: **{rule_pairs['category'].value_counts().get('shrunk_below_sig', 0):,}**",
        f"- grew: **{rule_pairs['category'].value_counts().get('grew', 0):,}**",
        "",
        "## Pair Origins In The Plotted Subset",
        "",
    ]
    for origin, n in fig_pairs["pair_origin"].value_counts().items():
        lines.append(f"- {origin}: **{n:,}**")
    lines += [
        "",
        "## Notes",
        "",
        "- This draft now uses source-recovered rows for OSC 2015, SSRP, Many Labs 1-5, EPRP, EERP, RPCB, SCORE, the Pipeline Project, the Decision-Market Replication Project, LOOPR, the Boyce student-replication corpus, the de-duplicated 251 Rescue rows, and the clinical highly cited-replication workbook, plus a manual paper-grounded tail for the remaining unresolved appendix aliases.",
        "- Vaidis et al. 2024 now contributes per-lab rows for the HC-CE vs LC-CE induced-compliance contrast, anchored to the original Croyle & Cooper (1983) effect and replacing the pooled FReD row for that replication.",
        "- Stoevenbelt et al. 2025 now contributes one women-only stereotype-threat-versus-control effect-size row per lab, reconstructed from the public combined participant CSV and anchored to the original Johns, Schmader, & Martens (2005) contrast reported in the public preprint.",
        "- The sports-science replication corpus now contributes study-level original-versus-replication pairs recovered from the public supplemental outcomes table joined to the public sample-size workbook; only rows with numeric original and replication effect values are retained.",
        "- FReD now contributes only rows whose original and replication effect metrics can be converted defensibly onto the common `D` axis, after excluding obvious legacy-overlap prefixes plus rows that read as secondary-data, syntax/output, reanalysis, or otherwise non-new-sample replications.",
        "- The currently pulled I4R Meta Database workbook is intentionally left out of the Figure 2 build path because the public workbook is dominated by computational-reproduction and robustness-check coefficient/SE tables rather than new-sample direct-replication effect-size pairs.",
        "- EERP is now built from the `Experimental Economics` subset of `ReplicationSuccess::RProjects`, with `effectdata.py` retained as a local cross-check.",
        "- SSRP is now built from the full `ReplicationSuccess::SSRP` object, with the public project CSV retained as a cross-check.",
        "- EPRP rows fall back to test-statistic parsing when the effect-size field is blank but the analysis string is numeric enough to recover D.",
        "- ML1 and ML3 are integrated from the public Altmejd harmonized file because the project summary tables do not expose a ready one-row original-N structure.",
        "- ML5 contributes two new replication arrows per original: `ML5 RP:P` and `ML5 Revised`.",
        "- Pipeline contributes 10 project-level rows recovered from the public supplement and packet files; nine use supplement-reported test statistics and Intuitive Economics uses the packet CSV to recover the replication correlation directly.",
        "- SCORE contributes the version-of-record analyst join: `309` merged claim rows, `282` usable rows after requiring original and replication `N` plus converted `r` on both sides.",
        "- The Decision-Market corpus adds the harmonized 26-row `data_to_use.csv` table directly from OSF.",
        "- LOOPR is integrated conservatively from the public coding workbook using the outcome-level Fisher-z columns first and only falling back to bounded numeric effect estimates when the Fisher-z field is blank.",
        "- The Boyce student-replication corpus currently uses only rows with explicit `target_d_calc` and `rep_d_calc`; raw-stat and `*_ES` fallbacks are not used unless they are already standardized and unambiguous.",
        "- The 251 Rescue rows are merged from `parsed_data.csv` and `combined_data.csv` and then de-duplicated against exact Boyce overlap keys before entering the corpus.",
        "- Clinical highly cited-replication rows are limited to `OR`, `RR`, and `HR` outcomes from the public workbook; `OR` is converted to a d-like scale and `RR`/`HR` are preserved as absolute log-ratio magnitudes.",
        "- The Brazilian Reproducibility Initiative is integrated from the public primary-analysis experiment table generated from the public repo; it excludes `ALT*` sensitivity variants and preserves the project-native experiment effect metric (`ROM`/`MD`) rather than forcing a d conversion.",
        "- The current all-pairs count is broader than the hand-built Appendix D table for some families, especially RPCB and ML5, so use the appendix coverage report for apples-to-apples comparison against `555`.",
        "- The build now collapses obvious site-level repeats to one row per original-paper × replication-study × endpoint anchor, using summed replication `N` and an `N`-weighted replication `D`; it does not use within-paper medians.",
        "- The Figure 2 rule keeps all recovered endpoint pairs with `N_replication > N_original` and `N >= 10` on both sides.",
        "- Category statistics and legend percentages use the full rule-qualified larger-`N` subset (`N >= 10` on both sides), not just what is easy to see inside the plotting window.",
        "- The plotted figure uses a visual window of `10 <= N <= 100k` and `0.02 <= D <= 5`; pairs outside that window are clipped to the nearest plot edge rather than dropped.",
        "- Undercovered project families now preserve any recovered source rows first and use Appendix D only for the unresolved residual gap.",
        "- Zero-effect rows are retained in the rule-qualified statistics and are shown at the lower plot boundary when they fall below the log-scale floor.",
    ]
    out_md.write_text("\n".join(lines))


def build_source_catalog(all_pairs: pd.DataFrame) -> pd.DataFrame:
    counts = all_pairs.groupby("source_dataset").size().to_dict()
    rows = [
        {
            "project": "Multi-project",
            "source_dataset": "I4R public workbook",
            "classification": "inspected public workbook / not yet pair-buildable for D-vs-N",
            "integrated_in_build": False,
            "file_rows": 110 + 26 + 6583,
            "usable_pair_rows": 0,
            "raw_file": str(RAW_REPL / "i4r" / "meta_database.xlsx"),
            "notes": "Public workbook is real and current, but the estimate-level sheet is a robustness-check coefficient/SE table rather than a standardized effect-size pair table.",
        },
        {
            "project": "Multi-project",
            "source_dataset": "FReD filtered pair table",
            "classification": "harmonized effect-level pair table",
            "integrated_in_build": True,
            "file_rows": 2164,
            "usable_pair_rows": counts.get("FReD filtered pair table", 0),
            "raw_file": str(RAW_REPL / "fred" / "FReD.xlsx"),
            "notes": "Build keeps only FReD rows whose original and replication effect types can be converted to the common D-like axis, while excluding obvious legacy-overlap prefixes and rows that look like secondary-data, syntax/output, reanalysis, or other non-new-sample replications.",
        },
        {
            "project": "Registered Replication Reports",
            "source_dataset": "Vaidis 2024 prepared data subset",
            "classification": "participant-level direct replication converted to per-lab pair rows",
            "integrated_in_build": True,
            "file_rows": 4898,
            "usable_pair_rows": counts.get("Vaidis 2024 prepared data subset", 0),
            "raw_file": str(RAW_REPL / "rrr" / "vaidis_2024_prepared_data_subset.csv"),
            "notes": "Public prepared-data CSV is filtered with the project analysis-script exclusions and converted into one HC-CE vs LC-CE Cohen's d row per lab, anchored to the original Croyle & Cooper (1983) effect.",
        },
        {
            "project": "Registered Replication Reports",
            "source_dataset": "Stoevenbelt 2025 combined lab csv",
            "classification": "participant-level direct replication converted to per-lab pair rows",
            "integrated_in_build": True,
            "file_rows": 1709,
            "usable_pair_rows": counts.get("Stoevenbelt 2025 combined lab csv", 0),
            "raw_file": str(RAW_REPL / "rrr" / "stoevenbelt_data_ST_RRR_combined.csv"),
            "notes": "Public combined participant CSV is filtered with the registered exclusion logic, converted into women-only stereotype-threat versus low-threat control Cohen's d rows per lab, and anchored to the original Johns, Schmader, & Martens (2005) effect reported in the public preprint.",
        },
        {
            "project": "Sports science replications",
            "source_dataset": "Sports science supplemental outcomes table",
            "classification": "public supplemental pair table joined to public sample-size workbook",
            "integrated_in_build": True,
            "file_rows": 25,
            "usable_pair_rows": counts.get("Sports science supplemental outcomes table", 0),
            "raw_file": str(RAW_REPL / "sports" / "sports_supp_table1.docx"),
            "notes": "Build joins the public reported-effect supplemental table to the public sample-size workbook and retains only rows with numeric original and replication effect values; partial eta squared is converted onto the common D-like axis and standardized-mean-difference variants are preserved on that scale.",
        },
        {
            "project": "Multi-project",
            "source_dataset": "Appendix D supplemental",
            "classification": "canonical hand-built pair table / floor source",
            "integrated_in_build": True,
            "file_rows": 555,
            "usable_pair_rows": 555,
            "raw_file": str(APPENDIX_HTML),
            "notes": "Used as a floor source for undercovered project families in the Figure 2 rule and plotted subsets.",
        },
        {
            "project": "Multi-project",
            "source_dataset": "Manual paper-grounded pairs",
            "classification": "manual primary-source recovery",
            "integrated_in_build": True,
            "file_rows": counts.get("SSRP 2018 supplement (manual)", 0)
            + counts.get("EERP 2016 supplement (manual)", 0)
            + counts.get("RRR Wagenmakers 2016 (manual)", 0)
            + counts.get("RRR Hagger 2016 (manual)", 0)
            + counts.get("RRR Alogna 2014 (manual)", 0)
            + counts.get("RRR O'Donnell 2018 (manual)", 0)
            + counts.get("RRR Verschuere 2018 (manual)", 0)
            + counts.get("RRR Bouwmeester 2017 (manual)", 0)
            + counts.get("RRR Cheung 2016 (manual)", 0)
            + counts.get("Ranehill 2015 power posing (manual)", 0)
            + counts.get("Galak et al. 2012 psi meta-analysis (manual)", 0)
            + counts.get("Doyen et al. 2012 article (manual)", 0)
            + counts.get("Srull-Wyer RRR paper (manual)", 0)
            + counts.get("RPP project record alias (manual)", 0)
            + counts.get("ReplicationSuccess SSRP alias (manual)", 0)
            + counts.get("Many Labs 4 local meta-analysis (manual)", 0)
            + counts.get("Marek 2022 BWAS paper (manual)", 0),
            "usable_pair_rows": counts.get("SSRP 2018 supplement (manual)", 0)
            + counts.get("EERP 2016 supplement (manual)", 0)
            + counts.get("RRR Wagenmakers 2016 (manual)", 0)
            + counts.get("RRR Hagger 2016 (manual)", 0)
            + counts.get("RRR Alogna 2014 (manual)", 0)
            + counts.get("RRR O'Donnell 2018 (manual)", 0)
            + counts.get("RRR Verschuere 2018 (manual)", 0)
            + counts.get("RRR Bouwmeester 2017 (manual)", 0)
            + counts.get("RRR Cheung 2016 (manual)", 0)
            + counts.get("Ranehill 2015 power posing (manual)", 0)
            + counts.get("Galak et al. 2012 psi meta-analysis (manual)", 0)
            + counts.get("Doyen et al. 2012 article (manual)", 0)
            + counts.get("Srull-Wyer RRR paper (manual)", 0)
            + counts.get("RPP project record alias (manual)", 0)
            + counts.get("ReplicationSuccess SSRP alias (manual)", 0)
            + counts.get("Many Labs 4 local meta-analysis (manual)", 0)
            + counts.get("Marek 2022 BWAS paper (manual)", 0),
            "raw_file": str(RAW_REPL / "manual_papers"),
            "notes": "Manual rows grounded to fetched supplements, stable DOI targets, local project records, or downloaded papers where the automated project tables still missed the appendix-aligned pair.",
        },
        {
            "project": "OSC 2015",
            "source_dataset": "RPP converted",
            "classification": "direct pair table",
            "integrated_in_build": False,
            "file_rows": 168,
            "usable_pair_rows": 0,
            "raw_file": str(RAW_CAND / "rpp" / "RPPdataConverted.xlsx"),
            "notes": "Legacy converted workbook retained as a local schema cross-check; build now uses the canonical raw CSV instead.",
        },
        {
            "project": "OSC 2015",
            "source_dataset": "RPP canonical OSF csv",
            "classification": "overlap / schema-variant mirror",
            "integrated_in_build": True,
            "file_rows": 168,
            "usable_pair_rows": counts.get("RPP canonical OSF csv", 0),
            "raw_file": str(RAW_REPL / "rpp" / "rpp_data_osf.csv"),
            "notes": "Canonical raw CSV; build now reads the `T_r..O.`/`T_r..R.` and `T_N..O.`/`T_N..R.` columns directly.",
        },
        {
            "project": "OSC 2015",
            "source_dataset": "RPP jtLeek mirror",
            "classification": "overlap / archival mirror",
            "integrated_in_build": False,
            "file_rows": 168,
            "usable_pair_rows": 0,
            "raw_file": str(RAW_REPL / "rpp" / "rpp_data_jtleek.csv"),
            "notes": "Archival mirror of the canonical OSF CSV.",
        },
        {
            "project": "SSRP",
            "source_dataset": "ReplicationSuccess SSRP.rda",
            "classification": "direct pair table",
            "integrated_in_build": True,
            "file_rows": 21,
            "usable_pair_rows": counts.get("ReplicationSuccess SSRP.rda", 0),
            "raw_file": str(RAW_REPL / "replicationsuccess" / "SSRP.rda"),
            "notes": "Full 21-row SSRP object with original and replication r, Fisher-z, p-values, and Ns.",
        },
        {
            "project": "SSRP",
            "source_dataset": "SSRP D3",
            "classification": "project-specific CSV / cross-check",
            "integrated_in_build": False,
            "file_rows": 21,
            "usable_pair_rows": 0,
            "raw_file": str(RAW_REPL / "ssrp" / "D3 - ReplicationResults.csv"),
            "notes": "Public SSRP CSV retained as a cross-check against the packaged 21-row harmonized object.",
        },
        {
            "project": "SSRP",
            "source_dataset": "SSRP D6 beliefs",
            "classification": "auxiliary / beliefs only",
            "integrated_in_build": False,
            "file_rows": 21,
            "usable_pair_rows": 0,
            "raw_file": str(RAW_REPL / "ssrp" / "D6 - MeanPeerBeliefs.csv"),
            "notes": "Prediction-market / beliefs sidecar, not a pair table.",
        },
        {
            "project": "EERP / EPRP / RPP / SSRP",
            "source_dataset": "ReplicationSuccess RProjects.rda",
            "classification": "overlap / harmonized cross-check",
            "integrated_in_build": False,
            "file_rows": 143,
            "usable_pair_rows": 0,
            "raw_file": str(RAW_REPL / "replicationsuccess" / "RProjects.rda"),
            "notes": "Contains 18 EERP, 31 EPRP, 73 psychology, 21 social-science rows; retained as cross-check.",
        },
        {
            "project": "Many Labs 1",
            "source_dataset": "Altmejd harmonized Many Labs 1",
            "classification": "harmonized aggregated pair table",
            "integrated_in_build": True,
            "file_rows": 16,
            "usable_pair_rows": counts.get("Altmejd harmonized Many Labs 1", 0),
            "raw_file": str(RAW_REPL / "altmejd" / "data.csv"),
            "notes": "Used because the ML1 summary workbook does not expose a clean original-N row for every effect.",
        },
        {
            "project": "Many Labs 1",
            "source_dataset": "ML1 summary workbook",
            "classification": "pair-buildable / cross-check",
            "integrated_in_build": False,
            "file_rows": 26,
            "usable_pair_rows": 0,
            "raw_file": str(RAW_REPL / "ml1" / "ML-_Summary_Statistics.xlsx"),
            "notes": "Pulled and inspected; strong cross-check for aggregated ES, but not used as the direct pair table.",
        },
        {
            "project": "Many Labs 2",
            "source_dataset": "Many Labs 2 public join",
            "classification": "project-specific joined pair table",
            "integrated_in_build": True,
            "file_rows": 28,
            "usable_pair_rows": counts.get("Many Labs 2 public join", 0),
            "raw_file": str(RAW_REPL / "ml2" / "table5data_RM.csv"),
            "notes": "Built from public replication summary plus original-effects files.",
        },
        {
            "project": "Many Labs 3",
            "source_dataset": "Altmejd harmonized Many Labs 3",
            "classification": "harmonized aggregated pair table",
            "integrated_in_build": True,
            "file_rows": 10,
            "usable_pair_rows": counts.get("Altmejd harmonized Many Labs 3", 0),
            "raw_file": str(RAW_REPL / "altmejd" / "data.csv"),
            "notes": "Used because the ML3 manuscript tables expose ES cleanly but not a ready original-N row structure.",
        },
        {
            "project": "Many Labs 3",
            "source_dataset": "ML3 manuscript tables bundle",
            "classification": "pair-buildable / cross-check",
            "integrated_in_build": False,
            "file_rows": 10,
            "usable_pair_rows": 0,
            "raw_file": str(RAW_REPL / "ml3" / "Many Labs 3 Manuscript Tables.txt"),
            "notes": "Pulled txt/pdf/xlsx/zip bundle and verified the project-level effect table.",
        },
        {
            "project": "Many Labs 4",
            "source_dataset": "ML4 public site results",
            "classification": "replication-side near-hit",
            "integrated_in_build": False,
            "file_rows": 17,
            "usable_pair_rows": 0,
            "raw_file": str(RAW_REPL / "ml4" / "combinedresults1.csv"),
            "notes": "Site-level replication results and meta objects are public; original-side pair row still needs a clean source.",
        },
        {
            "project": "Many Labs 5",
            "source_dataset": "Many Labs 5 overarching analyses",
            "classification": "direct pair-buildable",
            "integrated_in_build": True,
            "file_rows": 20,
            "usable_pair_rows": counts.get("Many Labs 5 overarching analyses", 0),
            "raw_file": str(RAW_REPL / "ml5" / "ML5FigureData.csv"),
            "notes": "Build uses `ML5FigureData.csv` for ES and the single-effects file for version-specific Ns; adds ML5 RP:P and ML5 Revised arrows.",
        },
        {
            "project": "EPRP",
            "source_dataset": "EPRP complete data",
            "classification": "direct pair table",
            "integrated_in_build": True,
            "file_rows": 40,
            "usable_pair_rows": counts.get("EPRP complete data", 0),
            "raw_file": str(RAW_REPL / "eprp" / "XPhiReplicability_CompleteData.csv"),
            "notes": "Direct project CSV; effect sizes are parsed directly or recovered from numeric analysis strings.",
        },
        {
            "project": "EERP",
            "source_dataset": "ReplicationSuccess RProjects.rda",
            "classification": "harmonized project-specific pair table",
            "integrated_in_build": True,
            "file_rows": 18,
            "usable_pair_rows": counts.get("ReplicationSuccess RProjects.rda", 0),
            "raw_file": str(RAW_REPL / "replicationsuccess" / "RProjects.rda"),
            "notes": "Uses the Experimental Economics subset of the harmonized 143-row RProjects object.",
        },
        {
            "project": "EERP",
            "source_dataset": "EERP effectdata.py",
            "classification": "project-specific code route / cross-check",
            "integrated_in_build": False,
            "file_rows": 18,
            "usable_pair_rows": 0,
            "raw_file": str(RAW_REPL / "eerp" / "effectdata.py"),
            "notes": "Parsed and verified locally; retained as a cross-check on the EERP subset from RProjects.",
        },
        {
            "project": "EERP",
            "source_dataset": "EERP marketdata.zip",
            "classification": "auxiliary market / survey data",
            "integrated_in_build": False,
            "file_rows": 6,
            "usable_pair_rows": 0,
            "raw_file": str(RAW_REPL / "eerp" / "marketdata.zip"),
            "notes": "Public zip is real but carries market/survey side data, not a richer pair table.",
        },
        {
            "project": "RPCB",
            "source_dataset": "RPCB",
            "classification": "direct effect-level pair table",
            "integrated_in_build": True,
            "file_rows": 188,
            "usable_pair_rows": counts.get("RPCB", 0),
            "raw_file": str(RAW_CAND / "rpcb" / "RP_CB Final Analysis - Effect level data.csv"),
            "notes": "Still the canonical local effect-level replication file.",
        },
        {
            "project": "SCORE",
            "source_dataset": "SCORE analyst join",
            "classification": "direct version-of-record claim join",
            "integrated_in_build": True,
            "file_rows": 309,
            "usable_pair_rows": counts.get("SCORE analyst join", 0),
            "raw_file": str(RAW_CAND / "score" / "orig_outcomes.csv"),
            "notes": "Built from `orig_outcomes.csv` joined to version-of-record rows in `repli_outcomes.csv`; reproduces the 282-row appendix-style join exactly.",
        },
        {
            "project": "Decision-Market Replication Project",
            "source_dataset": "Decision-market pair table",
            "classification": "direct pair table",
            "integrated_in_build": True,
            "file_rows": 41,
            "usable_pair_rows": counts.get("Decision-market pair table", 0),
            "raw_file": str(RAW_REPL / "decision_market" / "data_to_use.csv"),
            "notes": "Uses the harmonized public decision-market replication table with original and replication d and N columns.",
        },
        {
            "project": "LOOPR",
            "source_dataset": "LOOPR coding workbook",
            "classification": "direct pair-buildable workbook",
            "integrated_in_build": True,
            "file_rows": 121,
            "usable_pair_rows": counts.get("LOOPR coding workbook", 0),
            "raw_file": str(RAW_REPL / "loopr" / "Replication coding and results.xlsx"),
            "notes": "Integrated from the public coding workbook using outcome-level Fisher-z columns first, then bounded numeric effect fallbacks.",
        },
        {
            "project": "Student Replication Projects",
            "source_dataset": "Boyce student replication corpus",
            "classification": "direct pair corpus",
            "integrated_in_build": True,
            "file_rows": 176,
            "usable_pair_rows": counts.get("Boyce student replication corpus", 0),
            "raw_file": str(RAW_REPL / "boyce_student" / "boyce_2023_data.csv"),
            "notes": "Current integration is conservative: only rows with explicit `target_d_calc`, `rep_d_calc`, and both sample sizes are used.",
        },
        {
            "project": "251 Rescue Projects",
            "source_dataset": "251 Rescue parsed data",
            "classification": "direct triplet-derived pair table",
            "integrated_in_build": True,
            "file_rows": 57,
            "usable_pair_rows": counts.get("251 Rescue parsed data", 0),
            "raw_file": str(RAW_REPL / "rescue_251" / "parsed_data.csv"),
            "notes": "Built from parsed and combined rescue files, then de-duplicated against exact Boyce overlap keys before integration.",
        },
        {
            "project": "Clinical highly cited replications",
            "source_dataset": "Clinical published replication workbook",
            "classification": "direct pair workbook",
            "integrated_in_build": True,
            "file_rows": 10,
            "usable_pair_rows": counts.get("Clinical published replication workbook", 0),
            "raw_file": str(RAW_REPL / "clinical_replication" / "data - published.xlsx"),
            "notes": "Limited to rows with convertible `OR`, `RR`, or `HR` outcomes plus both original and replication sample sizes.",
        },
        {
            "project": "Brazilian Reproducibility Initiative",
            "source_dataset": "BRI primary t experiment table",
            "classification": "generated project-specific experiment table",
            "integrated_in_build": True,
            "file_rows": 45,
            "usable_pair_rows": counts.get("BRI primary t experiment table", 0),
            "raw_file": str(RAW_REPL / "bri" / "output_primary_t" / "Replication Assessment by Experiment.tsv"),
            "notes": "Built from the public BRI repo plus locally generated primary-analysis output; excludes `ALT*` sensitivity variants and preserves the project-native experiment effect metric (`ROM`/`MD`).",
        },
        {
            "project": "Pipeline Project",
            "source_dataset": "Pipeline supplement + packet data",
            "classification": "direct project supplement plus packet-level cross-check",
            "integrated_in_build": True,
            "file_rows": 10,
            "usable_pair_rows": counts.get("Pipeline supplement + packet data", 0),
            "raw_file": str(RAW_REPL / "pipeline" / "00.Supplemental_Materials_Pipeline_Project_Final_10_24_2015.pdf"),
            "notes": "Nine rows are converted from supplement-reported key-test statistics; Intuitive Economics uses the packet CSV to recover the replication-side correlation directly.",
        },
        {
            "project": "Multi-project",
            "source_dataset": "PooledMarketR PM_data.Rdata",
            "classification": "overlap / market metadata",
            "integrated_in_build": False,
            "file_rows": 111,
            "usable_pair_rows": 0,
            "raw_file": str(RAW_REPL / "pooledmarketr" / "PM_data.Rdata"),
            "notes": "Outcome / market / survey metadata for EERP, ML2, RPP, and SSRP; not a richer pair table.",
        },
    ]
    catalog = pd.DataFrame(rows)
    known_sources = set(catalog["source_dataset"])
    extra_rows = []
    for source_dataset, group in all_pairs.groupby("source_dataset", dropna=False):
        if source_dataset in known_sources:
            continue
        raw_file = ""
        if "raw_file" in group.columns:
            raw_candidates = group["raw_file"].dropna().astype(str).replace("", np.nan).dropna()
            if not raw_candidates.empty:
                raw_file = raw_candidates.iloc[0]
        project = "Harvested leads"
        if "project" in group.columns:
            project_candidates = group["project"].dropna().astype(str).replace("", np.nan).dropna()
            if not project_candidates.empty:
                project = project_candidates.iloc[0]
        notes = "Auto-discovered promoted harvested lead source."
        if str(raw_file).startswith(str(HARVEST_PROMOTED)):
            notes = "Promoted harvested lead table integrated via the generic harvest pipeline."
        extra_rows.append(
            {
                "project": project,
                "source_dataset": source_dataset,
                "classification": "harvest-promoted pair table",
                "integrated_in_build": True,
                "file_rows": len(group),
                "usable_pair_rows": len(group),
                "raw_file": raw_file,
                "notes": notes,
            }
        )
    if extra_rows:
        catalog = pd.concat([catalog, pd.DataFrame(extra_rows)], ignore_index=True)
    return catalog


def build_appendix_family_coverage(all_pairs: pd.DataFrame) -> pd.DataFrame:
    appendix_targets = [
        ("Registered Replication Reports", 9),
        ("Other direct replications", 3),
        ("Many Labs 1", 13),
        ("Many Labs 2", 28),
        ("Many Labs 3", 8),
        ("Many Labs 4", 1),
        ("Many Labs 5", 6),
        ("SSRP", 20),
        ("EERP", 18),
        ("RPP / OSC 2015", 98),
        ("RP:CB", 24),
        ("SCORE", 282),
        ("Experimental philosophy / x-phi", 33),
        ("Pipeline Project", 10),
        ("DellaVigna-Linos 2022", 1),
        ("Marek 2022 BWAS", 1),
    ]

    current_counts = {
        "Registered Replication Reports": 0,
        "Other direct replications": 0,
        "Many Labs 1": int((all_pairs["project"] == "Many Labs 1").sum()),
        "Many Labs 2": int((all_pairs["project"] == "Many Labs 2").sum()),
        "Many Labs 3": int((all_pairs["project"] == "Many Labs 3").sum()),
        "Many Labs 4": 0,
        "Many Labs 5": int((all_pairs["project"] == "Many Labs 5").sum()),
        "SSRP": int((all_pairs["project"] == "SSRP").sum()),
        "EERP": int((all_pairs["project"] == "EERP").sum()),
        "RPP / OSC 2015": int((all_pairs["project"] == "OSC 2015").sum()),
        "RP:CB": int((all_pairs["project"] == "RPCB").sum()),
        "SCORE": int((all_pairs["project"] == "SCORE").sum()),
        "Experimental philosophy / x-phi": int((all_pairs["project"] == "EPRP").sum()),
        "Pipeline Project": 0,
        "DellaVigna-Linos 2022": 0,
        "Marek 2022 BWAS": 0,
    }

    rows = []
    for family, target in appendix_targets:
        current = current_counts.get(family, 0)
        covered = min(current, target)
        rows.append(
            {
                "appendix_family": family,
                "appendix_target_rows": target,
                "current_recovered_rows": current,
                "capped_appendix_coverage": covered,
                "remaining_gap": max(target - current, 0),
                "over_target": max(current - target, 0),
            }
        )
    return pd.DataFrame(rows)


def write_appendix_family_coverage(df: pd.DataFrame, out_csv: Path, out_md: Path) -> None:
    ensure_dir(out_csv.parent)
    ensure_dir(out_md.parent)
    df.to_csv(out_csv, index=False)

    target_total = int(df["appendix_target_rows"].sum())
    covered_total = int(df["capped_appendix_coverage"].sum())
    gap_total = int(df["remaining_gap"].sum())

    lines = [
        "# Appendix D Coverage",
        "",
        f"- Appendix D target rows: **{target_total:,}**",
        f"- Covered by currently pulled sources after capping broad families to the appendix target: **{covered_total:,}**",
        f"- Remaining gap to the appendix target: **{gap_total:,}**",
        "",
        "| Appendix family | Appendix target | Current recovered | Capped coverage | Remaining gap | Over target |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for row in df.itertuples(index=False):
        lines.append(
            f"| {row.appendix_family} | {row.appendix_target_rows} | {row.current_recovered_rows} | "
            f"{row.capped_appendix_coverage} | {row.remaining_gap} | {row.over_target} |"
        )
    out_md.write_text("\n".join(lines))


def write_source_catalog(catalog: pd.DataFrame, out_csv: Path, out_md: Path) -> None:
    ensure_dir(out_csv.parent)
    ensure_dir(out_md.parent)
    catalog.to_csv(out_csv, index=False)

    lines = [
        "# Replication Pair Source Catalog",
        "",
        "This catalog records every source pulled in the latest replication-pair sweep, including overlap files and near-hits.",
        "",
        "| Project | Source dataset | Classification | Integrated | File rows | Usable pair rows | Notes |",
        "|---|---|---|---:|---:|---:|---|",
    ]
    for row in catalog.itertuples(index=False):
        lines.append(
            f"| {row.project} | {row.source_dataset} | {row.classification} | "
            f"{'yes' if row.integrated_in_build else 'no'} | {row.file_rows} | {row.usable_pair_rows} | {row.notes} |"
        )
    out_md.write_text("\n".join(lines))


def main() -> None:
    ensure_dir(DERIVED)
    ensure_dir(REPORTS)

    all_pairs = build_all_pairs()
    source_rule_pairs = build_rule_subset(all_pairs)
    source_fig_pairs = build_plot_subset(all_pairs)
    appendix_pairs = build_appendix_pairs()
    appendix_rule_pairs = build_rule_subset(appendix_pairs)
    appendix_fig_pairs = build_plot_subset(appendix_pairs)
    rule_pairs = apply_appendix_project_floor(source_rule_pairs, appendix_rule_pairs)
    fig_pairs = apply_appendix_project_floor(source_fig_pairs, appendix_fig_pairs)

    all_csv = DERIVED / "replication_pairs_all_on_hand.csv"
    rule_csv = DERIVED / "replication_pairs_figure2_rule_subset.csv"
    fig_csv = DERIVED / "replication_pairs_figure2_draft.csv"
    appendix_csv = DERIVED / "replication_pairs_appendix_backfill.csv"
    all_pairs.to_csv(all_csv, index=False)
    rule_pairs.to_csv(rule_csv, index=False)
    fig_pairs.to_csv(fig_csv, index=False)
    appendix_pairs.to_csv(appendix_csv, index=False)

    out_png = REPORTS / "figure2_replication_pairs_draft.png"
    plot_pairs(fig_pairs, rule_pairs, out_png)

    write_summary(
        all_pairs,
        source_rule_pairs,
        source_fig_pairs,
        rule_pairs,
        fig_pairs,
        REPORTS / "figure2_replication_pairs_draft_summary.md",
    )

    catalog = build_source_catalog(all_pairs)
    write_source_catalog(
        catalog,
        DERIVED / "replication_pair_source_catalog.csv",
        REPORTS / "replication_pair_source_catalog.md",
    )
    appendix_coverage = build_appendix_family_coverage(all_pairs)
    write_appendix_family_coverage(
        appendix_coverage,
        DERIVED / "replication_pairs_appendix_coverage.csv",
        REPORTS / "replication_pairs_appendix_coverage.md",
    )

    print(f"Wrote all pairs: {all_csv}")
    print(f"Wrote rule subset: {rule_csv}")
    print(f"Wrote figure subset: {fig_csv}")
    print(f"Wrote appendix backfill table: {appendix_csv}")
    print(f"Wrote figure: {out_png}")


if __name__ == "__main__":
    main()
