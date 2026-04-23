#!/usr/bin/env python3
"""Build paired journal-vs-registry comparison rows from the CliniFact scaffold."""

from __future__ import annotations

import math
import re
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
IN_PATH = ROOT / "data" / "derived" / "publication_bias_direct" / "clinifact_publication_numeric_extract_plausible.csv"
OUT_DIR = ROOT / "data" / "derived" / "publication_bias_direct"


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def metric_family_from_registry(value: object) -> str:
    text = str(value).lower().strip()
    if not text or text == "nan":
        return ""
    if "hazard ratio" in text or "cox proportional hazard" in text:
        return "HR"
    if "odds ratio" in text:
        return "OR"
    if "risk ratio" in text or "relative risk" in text:
        return "RR"
    if "rate ratio" in text or "irr" in text:
        return "IRR"
    if "risk difference" in text:
        return "RD"
    if "effect size d" in text:
        return "D"
    if (
        "mean difference" in text
        or "treatment difference" in text
        or "least squares" in text
        or "ls mean" in text
        or "estimated difference" in text
        or "difference of adjusted means" in text
    ):
        return "MD"
    return ""


def preferred_journal_n(row: pd.Series) -> tuple[float, str]:
    if pd.notna(row.get("journal_n_selected")) and row["journal_n_selected"] > 0:
        return float(row["journal_n_selected"]), "abstract_selected"
    if pd.notna(row.get("enrollment_num")) and row["enrollment_num"] > 0:
        return float(row["enrollment_num"]), "registry_enrollment_fallback"
    return np.nan, "missing"


def preferred_journal_d(row: pd.Series) -> tuple[float, str]:
    if pd.notna(row.get("journal_d_proxy_from_p_and_selected_n")):
        return float(row["journal_d_proxy_from_p_and_selected_n"]), "abstract_p_and_selected_n"
    if pd.notna(row.get("journal_d_proxy_from_p_and_registry_n")):
        return float(row["journal_d_proxy_from_p_and_registry_n"]), "abstract_p_and_registry_n"
    return np.nan, "missing"


def bool_from_p(value: float, threshold: float) -> object:
    if pd.isna(value):
        return np.nan
    return bool(value < threshold)


def effect_scale_value(metric_family: str, value: object) -> float:
    if pd.isna(value):
        return np.nan
    if isinstance(value, str):
        match = re.search(r"[-+]?\d*\.?\d+(?:e[-+]?\d+)?", value.strip())
        if not match:
            return np.nan
        value = match.group(0)
    value = float(value)
    if metric_family in {"HR", "OR", "RR", "IRR"}:
        if value <= 0:
            return np.nan
        return abs(math.log(value))
    if metric_family in {"MD", "D", "RD"}:
        return abs(value)
    return np.nan


def pair_quality(row: pd.Series) -> str:
    if row["publication_link_plausibility"] != "plausible_result_report":
        return "possible"
    if row["journal_p_source"] == "best_sentence" and row["journal_n_preferred_source"] == "abstract_selected":
        return "high"
    if row["has_paired_p"]:
        return "medium"
    return "low"


def build_pairs() -> pd.DataFrame:
    df = pd.read_csv(IN_PATH)

    journal_n_pref, journal_n_pref_source = zip(*df.apply(preferred_journal_n, axis=1))
    journal_d_pref, journal_d_pref_source = zip(*df.apply(preferred_journal_d, axis=1))
    df["journal_n_preferred"] = journal_n_pref
    df["journal_n_preferred_source"] = journal_n_pref_source
    df["journal_d_proxy_preferred"] = journal_d_pref
    df["journal_d_proxy_preferred_source"] = journal_d_pref_source

    df["journal_sig_05"] = df["journal_p"].map(lambda x: bool_from_p(x, 0.05))
    df["registry_sig_05"] = df["registry_p"].map(lambda x: bool_from_p(x, 0.05))
    df["journal_sig_10"] = df["journal_p"].map(lambda x: bool_from_p(x, 0.10))
    df["registry_sig_10"] = df["registry_p"].map(lambda x: bool_from_p(x, 0.10))

    for threshold in ("05", "10"):
        j = f"journal_sig_{threshold}"
        r = f"registry_sig_{threshold}"
        df[f"sig_discordant_{threshold}"] = np.where(
            df[j].notna() & df[r].notna(),
            df[j] != df[r],
            np.nan,
        )

    df["has_paired_p"] = df["journal_p"].notna() & df["registry_p"].notna()
    df["has_paired_d_proxy"] = df["journal_d_proxy_preferred"].notna() & df["registry_d_proxy"].notna()
    df["journal_abs_z_minus_registry_abs_z"] = df["journal_abs_z_from_p"] - df["registry_abs_z"]
    df["journal_d_minus_registry_d"] = df["journal_d_proxy_preferred"] - df["registry_d_proxy"]
    df["journal_to_registry_d_ratio"] = df["journal_d_proxy_preferred"] / df["registry_d_proxy"]
    df["journal_to_registry_n_ratio"] = df["journal_n_preferred"] / df["enrollment_num"]

    df["registry_metric_family"] = df["registry_param_type"].map(metric_family_from_registry)
    df["journal_metric_family"] = df["journal_effect_metric"].fillna("")
    df["metric_family_match"] = np.where(
        (df["journal_metric_family"] != "") & (df["registry_metric_family"] != ""),
        df["journal_metric_family"] == df["registry_metric_family"],
        np.nan,
    )

    df["journal_effect_scale"] = [
        effect_scale_value(metric, value)
        for metric, value in zip(df["journal_metric_family"], df["journal_effect_value"])
    ]
    df["registry_effect_scale"] = [
        effect_scale_value(metric, value)
        for metric, value in zip(df["registry_metric_family"], df["registry_param_value"])
    ]
    df["effect_scale_delta"] = df["journal_effect_scale"] - df["registry_effect_scale"]
    df["effect_scale_ratio"] = df["journal_effect_scale"] / df["registry_effect_scale"]

    df["pair_quality"] = df.apply(pair_quality, axis=1)

    keep_cols = [
        "claim_id",
        "split",
        "nctId",
        "PMID",
        "claim_support_label",
        "publication_link_plausibility",
        "pair_quality",
        "publication_year",
        "completion_year",
        "publication_minus_completion_years",
        "match_quality",
        "combined_match_score",
        "selected_sentence_score",
        "has_paired_p",
        "has_paired_d_proxy",
        "journal_p",
        "journal_p_source",
        "journal_p_raw",
        "registry_p",
        "journal_sig_05",
        "registry_sig_05",
        "sig_discordant_05",
        "journal_sig_10",
        "registry_sig_10",
        "sig_discordant_10",
        "journal_abs_z_from_p",
        "registry_abs_z",
        "journal_abs_z_minus_registry_abs_z",
        "journal_n_preferred",
        "journal_n_preferred_source",
        "enrollment_num",
        "journal_to_registry_n_ratio",
        "journal_d_proxy_preferred",
        "journal_d_proxy_preferred_source",
        "registry_d_proxy",
        "journal_d_minus_registry_d",
        "journal_to_registry_d_ratio",
        "journal_effect_metric",
        "journal_effect_value",
        "journal_effect_source",
        "registry_param_type",
        "registry_param_value",
        "registry_method",
        "journal_metric_family",
        "registry_metric_family",
        "metric_family_match",
        "journal_effect_scale",
        "registry_effect_scale",
        "effect_scale_delta",
        "effect_scale_ratio",
        "article_title",
        "selected_sentence",
        "clinifact_outcome_title",
        "registry_outcome_title",
        "intervention_group_title",
        "comparator_group_title",
    ]
    return df[keep_cols].copy()


def write_summary(df: pd.DataFrame) -> None:
    paired_p = df[df["has_paired_p"]].copy()
    paired_d = df[df["has_paired_d_proxy"]].copy()
    metric_match = df[df["metric_family_match"].eq(True)].copy()

    def agreement(series: pd.Series) -> str:
        clean = series.dropna()
        if clean.empty:
            return "NA"
        clean = clean.astype(bool)
        return f"{float((~clean).mean()):.3f}"

    lines = [
        "# CliniFact Journal-vs-Registry Pairs",
        "",
        "Last updated: 2026-04-20",
        "",
        "This file pairs the plausible-result publication extract against the",
        "matched CT.gov registry row for the same NCT-linked primary outcome.",
        "",
        "## Counts",
        "",
        f"- Plausible publication rows: {len(df):,}",
        f"- Rows with paired journal and registry p-values: {len(paired_p):,}",
        f"- Rows with paired journal and registry D proxies: {len(paired_d):,}",
        f"- Rows with matched journal and registry effect families: {len(metric_match):,}",
        "",
        "## Significance Agreement",
        "",
        f"- Agreement at `p < .05`: {agreement(df['sig_discordant_05'])}",
        f"- Agreement at `p < .10`: {agreement(df['sig_discordant_10'])}",
        "",
        "## D Proxy Comparison",
        "",
        f"- Median preferred journal D proxy: {paired_d['journal_d_proxy_preferred'].median():.3f}" if len(paired_d) else "- Median preferred journal D proxy: NA",
        f"- Median registry D proxy: {paired_d['registry_d_proxy'].median():.3f}" if len(paired_d) else "- Median registry D proxy: NA",
        f"- Median journal minus registry D proxy: {paired_d['journal_d_minus_registry_d'].median():.3f}" if len(paired_d) else "- Median journal minus registry D proxy: NA",
        f"- Median journal / registry D ratio: {paired_d['journal_to_registry_d_ratio'].median():.3f}" if len(paired_d) else "- Median journal / registry D ratio: NA",
        "",
        "## Quality Tiers",
        "",
    ]

    quality = df["pair_quality"].value_counts(dropna=False)
    for key, value in quality.items():
        lines.append(f"- `{key}`: {int(value):,}")

    lines.extend(
        [
            "",
            "## Output Files",
            "",
            "- `data/derived/publication_bias_direct/clinifact_publication_registry_pairs.csv`",
            "- `data/derived/publication_bias_direct/clinifact_publication_registry_pairs.parquet`",
            "- `data/derived/publication_bias_direct/clinifact_publication_registry_pairs_summary.md`",
        ]
    )
    (OUT_DIR / "clinifact_publication_registry_pairs_summary.md").write_text("\n".join(lines) + "\n")


def main() -> None:
    ensure_dir(OUT_DIR)
    df = build_pairs()
    df.to_csv(OUT_DIR / "clinifact_publication_registry_pairs.csv", index=False)
    df.to_parquet(OUT_DIR / "clinifact_publication_registry_pairs.parquet", index=False)
    write_summary(df)
    print(f"Wrote {len(df):,} paired publication-vs-registry rows to {OUT_DIR}")


if __name__ == "__main__":
    main()
