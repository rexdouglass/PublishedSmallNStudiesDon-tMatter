#!/usr/bin/env python3
"""Promote the lie-language direct replication from awesome-replicability-data.

The paired CSVs contain within-subject reaction-time means by language and
truth/lie status. The target effect is the interaction reported in the
replication description: the lie-truth RT cost is smaller in the foreign
language than in the native language. We code the absolute within-subject
standardized contrast:

    (native_lie - native_truth) - (foreign_lie - foreign_truth)
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data/raw/replication_projects/lead_harvest/awesome_lie_language"
OUT = (
    ROOT
    / "data/derived/replication_pairs/harvest/promoted/"
    / "awesome_lie_language__promoted_pairs.csv"
)


SCHEMA = [
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


def paired_d(values: pd.Series) -> tuple[float, int]:
    x = pd.to_numeric(values, errors="coerce").dropna().astype(float)
    if len(x) < 2:
        return np.nan, int(len(x))
    sd = x.std(ddof=1)
    if not np.isfinite(sd) or sd <= 0:
        return np.nan, int(len(x))
    return float(abs(x.mean() / sd)), int(len(x))


def language_lie_cost_d(path: Path, native_language: str, foreign_language: str) -> tuple[float, int]:
    df = pd.read_csv(path)
    required = {"ID", "Language", "Veracity", "meanRT"}
    missing = required.difference(df.columns)
    if missing:
        raise ValueError(f"{path} is missing columns: {sorted(missing)}")

    pivot = df.pivot_table(
        index="ID",
        columns=["Language", "Veracity"],
        values="meanRT",
        aggfunc="mean",
    )
    needed = [
        (native_language, "Lie"),
        (native_language, "Truth"),
        (foreign_language, "Lie"),
        (foreign_language, "Truth"),
    ]
    missing_cols = [col for col in needed if col not in pivot.columns]
    if missing_cols:
        raise ValueError(f"{path} is missing language/veracity cells: {missing_cols}")

    contrast = (
        (pivot[(native_language, "Lie")] - pivot[(native_language, "Truth")])
        - (pivot[(foreign_language, "Lie")] - pivot[(foreign_language, "Truth")])
    )
    return paired_d(contrast)


def main() -> None:
    original_file = RAW / "github_01__original_clean.csv"
    replication_file = RAW / "github_02__replication_clean.csv"
    d_original, n_original = language_lie_cost_d(original_file, "German", "English")
    d_replication, n_replication = language_lie_cost_d(replication_file, "Dutch", "English")

    rows = [
        {
            "source_dataset": "Awesome lie-language paired raw csvs",
            "project": "Other direct replications",
            "pair_id": "awesome_lie_language_native_minus_foreign_lie_truth_rt",
            "original_title": "Suchotzki and Gamer foreign-language lying original",
            "replication_title": "Frank et al. foreign-language lying replication",
            "original_doi": "",
            "replication_doi": "10.1080/02699931.2018.1553148",
            "outcome": "Native minus foreign lie-truth reaction-time cost",
            "D_original": d_original,
            "N_original": n_original,
            "D_replication": d_replication,
            "N_replication": n_replication,
            "raw_file": str(replication_file.relative_to(ROOT)),
            "match_author": "suchotzki_gamer_foreign_language_lying",
        }
    ]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows, columns=SCHEMA).to_csv(OUT, index=False)
    print(f"wrote {len(rows)} row to {OUT}")
    print(f"D_original={d_original:.6g} N_original={n_original}")
    print(f"D_replication={d_replication:.6g} N_replication={n_replication}")


if __name__ == "__main__":
    main()
