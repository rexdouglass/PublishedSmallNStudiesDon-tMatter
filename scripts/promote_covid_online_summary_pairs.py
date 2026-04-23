#!/usr/bin/env python3
"""Promote non-conjoint original-vs-YCLS summary pairs from the COVID archive."""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd
import pyreadr


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "data" / "raw" / "replication_projects" / "lead_harvest" / "covid_online_2021" / "unpacked_work"
PROMOTED = ROOT / "data" / "derived" / "replication_pairs" / "harvest" / "promoted"


def read_rds(path: Path) -> pd.DataFrame:
    return next(iter(pyreadr.read_r(str(path)).values()))


def clean_text(value: str) -> str:
    text = str(value).replace("\n", " ").replace("¬†", " ")
    text = re.sub(r"\s+", " ", text).strip()
    text = text.replace("Richs'", "Rich's")
    text = text.replace("Econ. System Justification", "Economic System Justification")
    return text


def summary_pair(summary_df: pd.DataFrame, detail: str) -> tuple[float, float]:
    sub = summary_df.loc[summary_df["study_group_detail"] == detail].copy()
    orig = float(sub.loc[sub["study"] == "Pre-COVID summary", "estimate"].iloc[0])
    rep = float(sub.loc[sub["study"] == "YCLS summary", "estimate"].iloc[0])
    return abs(orig), abs(rep)


def n_from_df(series: pd.Series) -> int:
    vals = pd.to_numeric(series, errors="coerce").dropna()
    return int(round((vals + 2).sum()))


def slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")


def rows_from_est(df: pd.DataFrame, detail_col: str, detail_map: dict[str, str]) -> list[tuple[str, int, int]]:
    out = []
    df = df.copy()
    df["detail_key"] = df[detail_col].map(clean_text)
    if "estimate_type" in df.columns:
        df = df.loc[df["estimate_type"] == "Standardized"].copy()
    for detail_key, detail_name in detail_map.items():
        sub = df.loc[df["detail_key"] == detail_key].copy()
        orig_n = n_from_df(sub.loc[sub["study"] == "Pre-COVID", "df"])
        rep_n = n_from_df(sub.loc[sub["study"] == "Replication", "df"])
        out.append((detail_name, orig_n, rep_n))
    return out


def build_rows() -> list[dict]:
    summary_df = read_rds(BASE / "summary_dat_export.rds")
    summary_df["study_group_detail"] = summary_df["study_group_detail"].map(clean_text)
    summary_df["study_group"] = summary_df["study_group"].map(clean_text)

    n_pairs: list[tuple[str, int, int]] = []

    # Studies 1-4, 6-7 are one-row summaries.
    one_row_map = {
        "est_study_1.rds": "Russian reporters",
        "est_study_2.rds": "Cheap v. Expensive Framing",
        "est_study_3.rds": "Gain v. Loss Framing",
        "est_study_4.rds": "Welfare v. Aid to Poor",
        "est_study_6.rds": "Foreign aid misperceptions",
        "est_study_7.rds": "Perceived Intentionality",
    }
    for filename, detail in one_row_map.items():
        df = read_rds(BASE / filename)
        if "estimate_type" in df.columns:
            df = df.loc[df["estimate_type"] == "Standardized"].copy()
        n_pairs.append(
            (
                detail,
                n_from_df(df.loc[df["study"] == "Pre-COVID", "df"]),
                n_from_df(df.loc[df["study"] == "Replication", "df"]),
            )
        )

    # Study 5
    est5 = read_rds(BASE / "est_study_5.rds")
    n_pairs.extend(
        rows_from_est(
            est5,
            "AD_Z_party_sure_thing",
            {
                "Republicans' Program": "Republicans' Program",
                "Democrats' Program": "Democrats' Program",
                "Program A": "Program A",
            },
        )
    )

    # Study 8a
    est8a = read_rds(BASE / "est_study_8a.rds")
    est8a = est8a.loc[est8a["estimate_type"] == "Standardized"].copy()
    est8a["detail_key"] = est8a["outcome_group"].map(clean_text).astype(str) + " | " + est8a["term"].map(clean_text).astype(str)
    for key, detail in {
        "Approve Nuclear Use | 90/45": "Approve Nukes (90/45)",
        "Approve Nuclear Use | 90/70": "Approve Nukes (90/70)",
        "Prefer Nuclear Use | 90/45": "Prefer Nukes (90/45)",
        "Prefer Nuclear Use | 90/70": "Prefer Nukes (90/70)",
    }.items():
        sub = est8a.loc[est8a["detail_key"] == key].copy()
        n_pairs.append(
            (
                detail,
                n_from_df(sub.loc[sub["study"] == "Pre-COVID", "df"]),
                n_from_df(sub.loc[sub["study"] == "Replication", "df"]),
            )
        )

    # Study 8b
    est8b = read_rds(BASE / "est_study_8b.rds")
    est8b = est8b.loc[est8b["estimate_type"] == "Standardized"].copy()
    n_pairs.extend(
        rows_from_est(
            est8b,
            "outcome_group",
            {
                "Approve Strike": "Approve Strike (Nuclear)",
                "Ethical Strike": "Ethical Strike (Nuclear)",
            },
        )
    )

    # Study 10
    est10 = read_rds(BASE / "est_study_10.rds")
    n_pairs.extend(
        rows_from_est(
            est10,
            "outcome_label",
            {
                "DC pizza restaurant concealed sex dungeon used by Democratic elites": "D.C. Pizzagate",
                "John Podesta implicated in disappearance of Madeleine McCann": "Podesta",
                "Russian government hacks Vermont power plant": "Russian hackers",
                "Anthony Scaramucci subject of Senate Russia investigation": "Scaramucci",
                "President Trump orders crackdown on sex trafficking": "Sex trafficking",
                "President Obama fakes birth certificate": "Obama Birtherism",
            },
        )
    )

    # Study 11
    est11 = read_rds(BASE / "est_study_11.rds")
    n_pairs.extend(
        rows_from_est(
            est11,
            "outcome_factor",
            {
                "Inequality increased": "Inequality increased",
                "Rich's share of income changed": "Rich's share of income changed",
                "System Justification": "System Justification",
                "Institutional Trust": "Institutional Trust",
                "Economic System Justification": "Economic System Justification",
            },
        )
    )

    # Study 12
    est12 = read_rds(BASE / "est_study_12.rds")
    n_pairs.extend(
        rows_from_est(
            est12,
            "outcome",
            {
                "Trust in Government": "Trust in Government",
                "Support for Redistribution": "Redistribution",
            },
        )
    )

    rows = []
    for detail, orig_n, rep_n in n_pairs:
        d_orig, d_rep = summary_pair(summary_df, detail)
        study_group = summary_df.loc[summary_df["study_group_detail"] == detail, "study_group"].iloc[0]
        rows.append(
            {
                "source_dataset": "COVID online experiments YCLS summaries",
                "project": "Other direct replications",
                "pair_id": f"covid_online_{slug(detail)}",
                "original_title": study_group,
                "replication_title": f"YCLS / COVID online replication summary - {detail}",
                "original_doi": "",
                "replication_doi": "",
                "outcome": detail,
                "D_original": d_orig,
                "N_original": orig_n,
                "D_replication": d_rep,
                "N_replication": rep_n,
                "raw_file": str(BASE / "summary_dat_export.rds"),
                "match_author": "covid_online_ycls",
            }
        )
    return rows


def main() -> None:
    PROMOTED.mkdir(parents=True, exist_ok=True)
    rows = build_rows()
    out = pd.DataFrame(rows)
    out_path = PROMOTED / "covid_online_summary_pairs__promoted_pairs.csv"
    out.to_csv(out_path, index=False)
    print(f"Wrote promoted rows: {len(out)}")
    print(f"Wrote file: {out_path}")


if __name__ == "__main__":
    main()
