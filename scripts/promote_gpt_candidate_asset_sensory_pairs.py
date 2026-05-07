#!/usr/bin/env python3
"""Mine Figure 1 pair rows from the GPT candidate mirror batch.

This promotes only candidate rows with locally mirrored value-bearing sources:

* asset-market replications: Internet Appendix tables C1, D1, E1, and F1
* sensory-marketing replications: article Table 5 plus OSF analysis workbooks

The promoted CSVs are consumed automatically by
scripts/analyze_replication_pairs.py via data/derived/replication_pairs/harvest/promoted.
An audit TSV with verbatim source text is written under steps/corpus_results so
the promoted numeric D/N values can be retraced to the mirrored bytes.
"""

from __future__ import annotations

import math
import re
from io import StringIO
from pathlib import Path
from typing import Any

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RAW_BASE = (
    ROOT
    / "data"
    / "raw"
    / "replication_projects"
    / "lead_harvest"
    / "gpt_many_replication_candidates_20260504"
)
INVENTORY_DIR = ROOT / "steps" / "source_inventory" / "figure1" / "gpt_many_replication_candidates_20260504"
PROMOTED_DIR = ROOT / "data" / "derived" / "replication_pairs" / "harvest" / "promoted"
AUDIT_DIR = ROOT / "steps" / "corpus_results" / "figure1" / "gpt_candidate_pair_mining"

ASSET_APPENDIX = RAW_BASE / "asset_market_replications" / "abbd67d08a8a__q79e2.bin"
ASSET_MANUSCRIPT = RAW_BASE / "asset_market_replications" / "6fed2ea9e840__zx2uv.bin"
SENSORY_ARTICLE = RAW_BASE / "sensory_marketing_replications" / "ddde4c11a7d9__full.html"

ASSET_PROMOTED = PROMOTED_DIR / "asset_market_replications__promoted_pairs.csv"
SENSORY_PROMOTED = PROMOTED_DIR / "sensory_marketing_replications__promoted_pairs.csv"
AUDIT_TSV = AUDIT_DIR / "gpt_candidate_asset_sensory_pair_mining.tsv"

ASSET_REPLICATION_DOI = "10.2139/ssrn.5048949"
SENSORY_REPLICATION_DOI = "10.1016/j.jbusres.2022.05.006"


def clean_text(value: Any) -> str:
    if value is None:
        return ""
    text = str(value)
    if text.lower() in {"nan", "none", "null", "<na>"}:
        return ""
    return re.sub(r"[\t\r\n]+", " ", text).strip()


def compact_text(value: Any) -> str:
    return re.sub(r"\s+", " ", clean_text(value)).strip()


def slug(value: str) -> str:
    text = clean_text(value).lower()
    text = text.replace("×", "x").replace("&", "and")
    text = re.sub(r"[^a-z0-9]+", "_", text)
    return text.strip("_")[:90]


def parse_float(value: Any) -> float:
    text = clean_text(value).replace(",", "").replace("−", "-").replace("–", "")
    if not text:
        return math.nan
    try:
        return float(text)
    except ValueError:
        return math.nan


def r_to_d(value: Any) -> float:
    r = parse_float(value)
    if not math.isfinite(r) or abs(r) >= 1:
        return math.nan
    return abs(2 * r / math.sqrt(1 - r * r))


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except Exception:
        return str(path)


def ensure_dirs() -> None:
    PROMOTED_DIR.mkdir(parents=True, exist_ok=True)
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)


def common_promoted_columns(df: pd.DataFrame) -> pd.DataFrame:
    cols = [
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
        "n_source_file",
        "verbatim_n_text_original",
        "verbatim_n_text_replication",
        "verbatim_effect_text_original",
        "verbatim_effect_text_replication",
        "d_n_transformation_note",
        "match_author",
    ]
    for col in cols:
        if col not in df.columns:
            df[col] = ""
    return df[cols].copy()


def build_asset_rows() -> pd.DataFrame:
    if not ASSET_APPENDIX.exists():
        raise FileNotFoundError(ASSET_APPENDIX)

    # Rows are copied from the mirrored Internet Appendix text extraction.  The
    # table notes state that AOL/KLS/CDP estimates are Cohen's d; EF estimates
    # are correlations.  EF original correlations are inferred from the reported
    # relative effect-size ratio because Table E1 reports replication rho and
    # Rel. ES but not the original rho as text.
    specs: list[dict[str, Any]] = [
        {
            "study": "AOL",
            "hypothesis": "HR1",
            "original_title": "Andrade, Odean, and Lin (2016) excitement treatment and relative deviation",
            "outcome": "Relative deviation (RD), Excitement vs Calm",
            "native_metric": "cohens_d",
            "orig": 1.723,
            "rep": -0.230,
            "n_orig": 39,
            "n_rep": 62,
            "source_locator": "Internet Appendix Table C1",
            "verbatim": "HR1 RD Rep. 1 t60 = -0.905 p = 0.369 n = 62 Cohen's d Orig. 1.723 Rep. -0.230 Rel. ES -13.3%",
            "verbatim_n_orig": "Manuscript: AOL replication n = 62 is 1.6 times larger than the original sample size; AOL original replicated conditions n = 39 markets.",
        },
        {
            "study": "AOL",
            "hypothesis": "HR2",
            "original_title": "Andrade, Odean, and Lin (2016) excitement treatment and peak overpricing",
            "outcome": "Peak overpricing (RDMAX), Excitement vs Calm",
            "native_metric": "cohens_d",
            "orig": 1.284,
            "rep": -0.179,
            "n_orig": 39,
            "n_rep": 62,
            "source_locator": "Internet Appendix Table C1",
            "verbatim": "HR2 RDMAX Rep. 1 t60 = -0.705 p = 0.483 n = 62 Cohen's d Orig. 1.284 Rep. -0.179 Rel. ES -13.9%",
            "verbatim_n_orig": "Manuscript: AOL replication n = 62 is 1.6 times larger than the original sample size; AOL original replicated conditions n = 39 markets.",
        },
        {
            "study": "KLS",
            "hypothesis": "HR1",
            "original_title": "Kocher, Lucks, and Schindler (2019) self-control treatment and relative deviation",
            "outcome": "Relative deviation (RD), HighSC vs LowSC",
            "native_metric": "cohens_d",
            "orig": 1.032,
            "rep": -0.129,
            "n_orig": 16,
            "n_rep": 104,
            "source_locator": "Internet Appendix Table D1",
            "verbatim": "HR1 RD Rep. 1 t102 = -0.659 p = 0.512 n = 104 Cohen's d Orig. 1.032 Rep. -0.129 Rel. ES -12.5%",
            "verbatim_n_orig": "Manuscript: KLS replication n = 104 is 6.5 times larger than the original sample size; KLS original replicated conditions n = 16 markets.",
        },
        {
            "study": "KLS",
            "hypothesis": "HR2",
            "original_title": "Kocher, Lucks, and Schindler (2019) self-control treatment and absolute deviation",
            "outcome": "Relative absolute deviation (RAD), HighSC vs LowSC",
            "native_metric": "cohens_d",
            "orig": 1.193,
            "rep": -0.148,
            "n_orig": 16,
            "n_rep": 104,
            "source_locator": "Internet Appendix Table D1",
            "verbatim": "HR2 RAD Rep. 1 t102 = -0.755 p = 0.452 n = 104 Cohen's d Orig. 1.193 Rep. -0.148 Rel. ES -12.4%",
            "verbatim_n_orig": "Manuscript: KLS replication n = 104 is 6.5 times larger than the original sample size; KLS original replicated conditions n = 16 markets.",
        },
        {
            "study": "EF",
            "hypothesis": "HR1",
            "original_title": "Eckel and Füllbrunn (2015) female-trader fraction and absolute bias",
            "outcome": "Spearman correlation, fraction female traders and absolute bias (AB)",
            "native_metric": "correlation_from_replication_rho_and_relative_es",
            "rep_r": 0.139,
            "rel_es_percent": -29.1,
            "n_orig": 35,
            "n_rep": 166,
            "source_locator": "Internet Appendix Table E1",
            "verbatim": "HR1 AB rho = 0.139 z = 1.774 p = 0.075 n = 166 Rel. ES -29.1%",
            "verbatim_n_orig": "Manuscript footnote: EF meta-analytic results aggregate data from 35 SSW markets reported in the literature.",
        },
        {
            "study": "EF",
            "hypothesis": "HR2",
            "original_title": "Eckel and Füllbrunn (2015) female-trader fraction and positive deviation",
            "outcome": "Spearman correlation, fraction female traders and positive deviation (PD)",
            "native_metric": "correlation_from_replication_rho_and_relative_es",
            "rep_r": 0.153,
            "rel_es_percent": -43.7,
            "n_orig": 35,
            "n_rep": 166,
            "source_locator": "Internet Appendix Table E1",
            "verbatim": "HR2 PD rho = 0.153 z = 1.962 p = 0.049 n = 166 Rel. ES -43.7%",
            "verbatim_n_orig": "Manuscript footnote: EF meta-analytic results aggregate data from 35 SSW markets reported in the literature.",
        },
        {
            "study": "EF",
            "hypothesis": "HR3",
            "original_title": "Eckel and Füllbrunn (2015) female-trader fraction and boom duration",
            "outcome": "Spearman correlation, fraction female traders and boom duration",
            "native_metric": "correlation_from_replication_rho_and_relative_es",
            "rep_r": 0.093,
            "rel_es_percent": -23.8,
            "n_orig": 35,
            "n_rep": 166,
            "source_locator": "Internet Appendix Table E1",
            "verbatim": "HR3 Boom rho = 0.093 z = 1.186 p = 0.234 n = 166 Rel. ES -23.8%",
            "verbatim_n_orig": "Manuscript footnote: EF meta-analytic results aggregate data from 35 SSW markets reported in the literature.",
        },
        {
            "study": "EF",
            "hypothesis": "HR4",
            "original_title": "Eckel and Füllbrunn (2015) female-trader fraction and bust duration",
            "outcome": "Spearman correlation, fraction female traders and bust duration",
            "native_metric": "correlation_from_replication_rho_and_relative_es",
            "rep_r": -0.023,
            "rel_es_percent": -4.4,
            "n_orig": 35,
            "n_rep": 166,
            "source_locator": "Internet Appendix Table E1",
            "verbatim": "HR4 Bust rho = -0.023 z = -0.299 p = 0.765 n = 166 Rel. ES -4.4%",
            "verbatim_n_orig": "Manuscript footnote: EF meta-analytic results aggregate data from 35 SSW markets reported in the literature.",
        },
        {
            "study": "CDP",
            "hypothesis": "HR1",
            "original_title": "Corgnet, Desantis, and Porter (2018) cognitive reflection and earnings",
            "outcome": "CRT association with earnings",
            "native_metric": "cohens_d",
            "orig": 0.297,
            "rep": 0.341,
            "n_orig": 167,
            "n_rep": 1542,
            "source_locator": "Internet Appendix Table F1",
            "verbatim": "HR1 CRT t165 = 6.690 p < 0.001 n = 1,542 Cohen's d Orig. 0.297 Rep. 0.341 Rel. ES 114.7%",
            "verbatim_n_orig": "Internet Appendix A: CDP original n = 167 and replication n = 1,542.",
        },
        {
            "study": "CDP",
            "hypothesis": "HR2",
            "original_title": "Corgnet, Desantis, and Porter (2018) fluid intelligence and earnings",
            "outcome": "APM association with earnings",
            "native_metric": "cohens_d",
            "orig": 0.404,
            "rep": 0.246,
            "n_orig": 167,
            "n_rep": 1542,
            "source_locator": "Internet Appendix Table F1",
            "verbatim": "HR2 APM t165 = 4.826 p < 0.001 n = 1,542 Cohen's d Orig. 0.404 Rep. 0.246 Rel. ES 60.9%",
            "verbatim_n_orig": "Internet Appendix A: CDP original n = 167 and replication n = 1,542.",
        },
        {
            "study": "CDP",
            "hypothesis": "HR3",
            "original_title": "Corgnet, Desantis, and Porter (2018) theory of mind and earnings",
            "outcome": "TOM association with earnings",
            "native_metric": "cohens_d",
            "orig": 0.355,
            "rep": 0.140,
            "n_orig": 167,
            "n_rep": 1542,
            "source_locator": "Internet Appendix Table F1",
            "verbatim": "HR3 TOM t165 = 2.742 p = 0.007 n = 1,542 Cohen's d Orig. 0.355 Rep. 0.140 Rel. ES 39.3%",
            "verbatim_n_orig": "Internet Appendix A: CDP original n = 167 and replication n = 1,542.",
        },
        {
            "study": "CDP",
            "hypothesis": "HR4",
            "original_title": "Corgnet, Desantis, and Porter (2018) theory of mind by cognitive reflection interaction",
            "outcome": "TOM x CRT interaction with earnings",
            "native_metric": "cohens_d",
            "orig": 0.270,
            "rep": -0.067,
            "n_orig": 167,
            "n_rep": 1542,
            "source_locator": "Internet Appendix Table F1",
            "verbatim": "HR4 TOM x CRT t165 = -1.318 p = 0.189 n = 1,542 Cohen's d Orig. 0.270 Rep. -0.067 Rel. ES -24.9%",
            "verbatim_n_orig": "Internet Appendix A: CDP original n = 167 and replication n = 1,542.",
        },
        {
            "study": "CDP",
            "hypothesis": "HR6",
            "original_title": "Corgnet, Desantis, and Porter (2018) heterogeneous skill by skill index interaction",
            "outcome": "HET x SI interaction with earnings",
            "native_metric": "cohens_d",
            "orig": 0.378,
            "rep": 0.029,
            "n_orig": 167,
            "n_rep": 1542,
            "source_locator": "Internet Appendix Table F1",
            "verbatim": "HR6 HET x SI t165 = 0.573 p = 0.567 n = 1,542 Cohen's d Orig. 0.378 Rep. 0.029 Rel. ES 7.7%",
            "verbatim_n_orig": "Internet Appendix A: CDP original n = 167 and replication n = 1,542.",
        },
        {
            "study": "CDP",
            "hypothesis": "HR9",
            "original_title": "Corgnet, Desantis, and Porter (2018) heterogeneous skill by theory of mind interaction",
            "outcome": "HET x TOM interaction with earnings",
            "native_metric": "cohens_d",
            "orig": 0.319,
            "rep": -0.013,
            "n_orig": 167,
            "n_rep": 1542,
            "source_locator": "Internet Appendix Table F1",
            "verbatim": "HR9 HET x TOM t165 = -0.250 p = 0.803 n = 1,542 Cohen's d Orig. 0.319 Rep. -0.013 Rel. ES -4.0%",
            "verbatim_n_orig": "Internet Appendix A: CDP original n = 167 and replication n = 1,542.",
        },
    ]

    rows: list[dict[str, Any]] = []
    for spec in specs:
        if spec["native_metric"] == "correlation_from_replication_rho_and_relative_es":
            rep_r = float(spec["rep_r"])
            rel_ratio = float(spec["rel_es_percent"]) / 100.0
            orig_r = rep_r / rel_ratio
            d_original = r_to_d(orig_r)
            d_replication = r_to_d(rep_r)
            verbatim_original = (
                f"Original rho inferred as replication rho ({rep_r}) / Rel. ES ratio ({rel_ratio:.3f}) = {orig_r:.6f}; "
                f"source row: {spec['verbatim']}"
            )
            note = (
                "EF source table reports replication rho and relative effect size; original rho is inferred from "
                "original = replication / relative_effect_size, then both correlations are mapped to d as "
                "abs(2*r/sqrt(1-r^2))."
            )
        else:
            d_original = abs(float(spec["orig"]))
            d_replication = abs(float(spec["rep"]))
            verbatim_original = spec["verbatim"]
            note = (
                "Internet Appendix table reports original and replication estimates in Cohen's d units; signed "
                "replication estimates are converted to absolute D for the Figure 1 magnitude axis."
            )

        pair_id = f"asset_market_{spec['study'].lower()}_{spec['hypothesis'].lower()}_{slug(spec['outcome'])}"
        rows.append(
            {
                "source_dataset": "Experimental asset-market replication appendix tables",
                "project": "Experimental asset-market replications",
                "pair_id": pair_id,
                "original_title": spec["original_title"],
                "replication_title": "High-powered preregistered replications of experimental asset-market results",
                "original_doi": "",
                "replication_doi": ASSET_REPLICATION_DOI,
                "outcome": spec["outcome"],
                "D_original": d_original,
                "N_original": float(spec["n_orig"]),
                "D_replication": d_replication,
                "N_replication": float(spec["n_rep"]),
                "raw_file": str(ASSET_APPENDIX),
                "n_source_file": str(ASSET_MANUSCRIPT),
                "source_locator": spec["source_locator"],
                "verbatim_n_text_original": spec["verbatim_n_orig"],
                "verbatim_n_text_replication": f"{spec['verbatim']} ; replication n = {spec['n_rep']}",
                "verbatim_effect_text_original": verbatim_original,
                "verbatim_effect_text_replication": spec["verbatim"],
                "d_n_transformation_note": note,
                "match_author": f"asset_market_{spec['study'].lower()}_{spec['hypothesis'].lower()}",
            }
        )

    return pd.DataFrame(rows)


def mirrored_local_path_by_download_id(candidate_key: str) -> dict[str, Path]:
    status = pd.read_csv(INVENTORY_DIR / "mirror-status.tsv", sep="\t")
    out: dict[str, Path] = {}
    for row in status[status["candidate_key"].eq(candidate_key)].itertuples(index=False):
        url = clean_text(getattr(row, "url", ""))
        local = clean_text(getattr(row, "local_path", ""))
        match = re.search(r"/download/([^/]+)/", url)
        if match and local:
            out[match.group(1)] = ROOT / local
    return out


def workbook_n_map() -> dict[str, tuple[int, Path, str]]:
    local_by_id = mirrored_local_path_by_download_id("sensory_marketing_replications")
    study_to_download = {
        "Klink (2000), Study 1": ("74bj8", "klink_analysis.xlsx"),
        "Shrum et al. (2012), Experiment 1a, 1b, 1c": ("ume59", "shrum_analysis.xlsx"),
        "Hagtvedt and Brasel (2017), Study 3": ("csgku", "saturation_analysis.xlsx"),
        "Romero and Biswas (2016), Study 1B": ("d2mvj", "Romero_analysis.xlsx"),
        "Yorkston and Menon (2004), Study 1": ("tjwnp", "yorkston_menon_analysis.xlsx"),
        "Elder and Krishna (2011), Study 4": ("634562ff31d6531a012dc7a9", "Elder_Krishna_analysis.xlsx"),
        "Jiang et al. (2015), Experiment 1": ("6345637c0db48e2699e10aeb", "Jian_analysis.xlsx"),
        "Chae and Hoegg (2013), Study 2": ("62spv", "Chae_Hoegg_analysis.xlsx"),
        "Cian et al. (2014), Study 1": ("fzpmt", "Cian_analysis.xlsx"),
        "Madzharov and Block (2010), Study 1A": ("unqx3", "Madzharov_Block_analysis.xlsx"),
    }
    out: dict[str, tuple[int, Path, str]] = {}
    for study, (download_id, source_name) in study_to_download.items():
        path = local_by_id.get(download_id)
        if path is None or not path.exists():
            raise FileNotFoundError(f"Missing mirrored workbook for {study}: {download_id}")
        workbook = pd.ExcelFile(path)
        table = pd.read_excel(path, sheet_name=workbook.sheet_names[0])
        out[study] = (int(len(table)), path, source_name)
    return out


def sensory_original_n_text() -> dict[str, tuple[int, str, str]]:
    if not SENSORY_ARTICLE.exists():
        raise FileNotFoundError(SENSORY_ARTICLE)
    tables = pd.read_html(StringIO(SENSORY_ARTICLE.read_text(errors="ignore")))
    selected = tables[0]
    text_by_author: dict[str, tuple[str, str]] = {}
    for row in selected.itertuples(index=False):
        author = compact_text(row[0])
        sample_text = clean_text(row[1])
        effect_text = clean_text(row[3])
        text_by_author[author] = (sample_text, effect_text)
    return {
        "Klink (2000), Study 1": (
            265,
            f"{text_by_author['Klink (2000) Marketing Letters 491 citations'][0]} ; {text_by_author['Klink (2000) Marketing Letters 491 citations'][1]}",
            "Klink (2000) Marketing Letters 491 citations",
        ),
        "Shrum et al. (2012), Experiment 1a, 1b, 1c": (
            369,
            f"{text_by_author['Shrum et al. (2012) International Journal of Research in Marketing 133 citations'][0]} ; effect-test text: {text_by_author['Shrum et al. (2012) International Journal of Research in Marketing 133 citations'][1]} ; N uses F(1, 367) df + 2 = 369 for the reported interaction effect.",
            "Shrum et al. (2012) International Journal of Research in Marketing 133 citations",
        ),
        "Hagtvedt and Brasel (2017), Study 3": (
            77,
            f"{text_by_author['Hagtvedt and Brasel (2017) Journal of Consumer Research 105 citations'][0]} ; {text_by_author['Hagtvedt and Brasel (2017) Journal of Consumer Research 105 citations'][1]}",
            "Hagtvedt and Brasel (2017) Journal of Consumer Research 105 citations",
        ),
        "Romero and Biswas (2016), Study 1B": (
            93,
            f"{text_by_author['Romero and Biswas (2016) Journal of Consumer Research 117 citations'][0]} ; {text_by_author['Romero and Biswas (2016) Journal of Consumer Research 117 citations'][1]}",
            "Romero and Biswas (2016) Journal of Consumer Research 117 citations",
        ),
        "Yorkston and Menon (2004), Study 1": (
            126,
            f"{text_by_author['Yorkston and Menon (2004) Journal of Consumer Research 528 citations'][0]} ; {text_by_author['Yorkston and Menon (2004) Journal of Consumer Research 528 citations'][1]}",
            "Yorkston and Menon (2004) Journal of Consumer Research 528 citations",
        ),
        "Elder and Krishna (2011), Study 4": (
            78,
            f"{text_by_author['Elder and Krishna (2011) Journal of Consumer Research 341 citations'][0]} ; {text_by_author['Elder and Krishna (2011) Journal of Consumer Research 341 citations'][1]}",
            "Elder and Krishna (2011) Journal of Consumer Research 341 citations",
        ),
        "Jiang et al. (2015), Experiment 1": (
            109,
            f"{text_by_author['Jiang et al. (2015) Journal of Consumer Research 221 citations'][0]} ; {text_by_author['Jiang et al. (2015) Journal of Consumer Research 221 citations'][1]}",
            "Jiang et al. (2015) Journal of Consumer Research 221 citations",
        ),
        "Chae and Hoegg (2013), Study 2": (
            194,
            f"{text_by_author['Chae and Hoegg (2013) Journal of Consumer Research 200 citations'][0]} ; {text_by_author['Chae and Hoegg (2013) Journal of Consumer Research 200 citations'][1]}",
            "Chae and Hoegg (2013) Journal of Consumer Research 200 citations",
        ),
        "Cian et al. (2014), Study 1": (
            74,
            f"{text_by_author['Cian et al. (2014) Journal of Marketing Research 229 citations'][0]} ; {text_by_author['Cian et al. (2014) Journal of Marketing Research 229 citations'][1]}",
            "Cian et al. (2014) Journal of Marketing Research 229 citations",
        ),
        "Madzharov and Block (2010), Study 1A": (
            37,
            f"{text_by_author['Madzharov and Block (2010) Journal of Consumer Psychology 161 citations'][0]} ; {text_by_author['Madzharov and Block (2010) Journal of Consumer Psychology 161 citations'][1]}",
            "Madzharov and Block (2010) Journal of Consumer Psychology 161 citations",
        ),
    }


def build_sensory_rows() -> pd.DataFrame:
    if not SENSORY_ARTICLE.exists():
        raise FileNotFoundError(SENSORY_ARTICLE)

    tables = pd.read_html(StringIO(SENSORY_ARTICLE.read_text(errors="ignore")))
    table = tables[4].copy()
    original_n = sensory_original_n_text()
    rep_n = workbook_n_map()

    current_study = ""
    rows: list[dict[str, Any]] = []
    for idx, row in table.iterrows():
        values = [clean_text(value) for value in row.tolist()]
        label = values[0]
        orig_r = parse_float(values[1])
        rep_r = parse_float(values[4])
        if not math.isfinite(orig_r) or not math.isfinite(rep_r):
            if label:
                current_study = label
            continue
        if current_study not in original_n:
            raise KeyError(f"Unexpected sensory study label: {current_study}")
        n_orig, n_orig_text, author_title = original_n[current_study]
        n_rep, workbook_path, workbook_name = rep_n[current_study]
        pair_id = f"sensory_marketing_{slug(current_study)}_{slug(label)}"
        rows.append(
            {
                "source_dataset": "Sensory marketing article Table 5 and OSF workbooks",
                "project": "Sensory-marketing replications",
                "pair_id": pair_id,
                "original_title": author_title,
                "replication_title": "Evaluating replicability of ten influential sensory marketing studies",
                "original_doi": "",
                "replication_doi": SENSORY_REPLICATION_DOI,
                "outcome": f"{current_study}: {label}",
                "D_original": r_to_d(orig_r),
                "N_original": float(n_orig),
                "D_replication": r_to_d(rep_r),
                "N_replication": float(n_rep),
                "raw_file": str(SENSORY_ARTICLE),
                "n_source_file": str(workbook_path),
                "source_locator": f"Article Table 5 row {idx}; replication N from {workbook_name}",
                "verbatim_n_text_original": n_orig_text,
                "verbatim_n_text_replication": f"{workbook_name} mirrored locally has {n_rep} data rows in its first worksheet.",
                "verbatim_effect_text_original": (
                    f"Article Table 5 {current_study} / {label}: original r = {values[1]}, "
                    f"95% CI [{values[2]}, {values[3]}]"
                ),
                "verbatim_effect_text_replication": (
                    f"Article Table 5 {current_study} / {label}: replication r = {values[4]}, "
                    f"95% CI [{values[5]}, {values[6]}]"
                ),
                "d_n_transformation_note": (
                    "Article Table 5 reports original and replication effect sizes as r. Both sides are mapped "
                    "to the Figure 1 D axis as abs(2*r/sqrt(1-r^2)); original N comes from article Table 1 "
                    "sample-size/statistic text and replication N from the mirrored OSF analysis workbook row count."
                ),
                "match_author": f"sensory_{slug(current_study)}",
            }
        )

    return pd.DataFrame(rows)


def main() -> None:
    ensure_dirs()

    asset = common_promoted_columns(build_asset_rows())
    sensory = common_promoted_columns(build_sensory_rows())

    asset.to_csv(ASSET_PROMOTED, index=False)
    sensory.to_csv(SENSORY_PROMOTED, index=False)

    audit = pd.concat(
        [
            build_asset_rows().assign(promoted_file=rel(ASSET_PROMOTED)),
            build_sensory_rows().assign(promoted_file=rel(SENSORY_PROMOTED)),
        ],
        ignore_index=True,
        sort=False,
    )
    audit["raw_file"] = audit["raw_file"].map(lambda path: rel(Path(path)))
    audit["n_source_file"] = audit["n_source_file"].map(lambda path: rel(Path(path)) if clean_text(path) else "")
    audit.to_csv(AUDIT_TSV, sep="\t", index=False)

    print(f"Wrote asset-market promoted rows: {len(asset)} -> {ASSET_PROMOTED}")
    print(f"Wrote sensory-marketing promoted rows: {len(sensory)} -> {SENSORY_PROMOTED}")
    print(f"Wrote mining audit rows: {len(audit)} -> {AUDIT_TSV}")


if __name__ == "__main__":
    main()
