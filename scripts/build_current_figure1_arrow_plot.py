#!/usr/bin/env python3
"""Refresh the arrows replication plot from the current Figure 1 root table."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
ROOT_TABLE = ROOT / "FIGURE1_REPLICATION_PAIRS.tsv"
REPORT_FIG = ROOT / "reports" / "corpus_candidates" / "figure2_replication_pairs_draft.png"
DOCS_FIG = ROOT / "docs" / "_generated" / "figures" / "figure2_replication_combined.png"
SUMMARY_OUT = ROOT / "reports" / "corpus_candidates" / "figure2_replication_pairs_draft_summary.md"


def load_plot_pairs_function():
    module_path = ROOT / "scripts" / "analyze_replication_pairs.py"
    spec = importlib.util.spec_from_file_location("analyze_replication_pairs_for_current_plot", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.plot_pairs


def current_included_pairs() -> pd.DataFrame:
    if not ROOT_TABLE.exists():
        raise FileNotFoundError(ROOT_TABLE)
    df = pd.read_csv(ROOT_TABLE, sep="\t")
    df = df.loc[df["current_plot_rule_status"].eq("included_by_current_figure1_dn_rule")].copy()
    rename = {
        "figure1_replication_pair_id": "pair_id",
        "source_family_label": "project",
        "outcome_label": "outcome",
    }
    for old, new in rename.items():
        if old in df.columns and new not in df.columns:
            df[new] = df[old]
    for col in ["D_original", "D_replication", "N_original", "N_replication"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna(subset=["D_original", "D_replication", "N_original", "N_replication", "category"])
    df = df.loc[
        np.isfinite(df["D_original"])
        & np.isfinite(df["D_replication"])
        & np.isfinite(df["N_original"])
        & np.isfinite(df["N_replication"])
        & df["N_original"].gt(0)
        & df["N_replication"].gt(0)
    ].copy()
    df["pair_id"] = df.get("pair_id", pd.Series(index=df.index, dtype=str)).fillna("").astype(str)
    df["project"] = df.get("project", pd.Series(index=df.index, dtype=str)).fillna("Current Figure 1").astype(str)
    df["outcome"] = df.get("outcome", pd.Series(index=df.index, dtype=str)).fillna("").astype(str)
    return df.reset_index(drop=True)


def clipped_plot_frame(stats_df: pd.DataFrame) -> pd.DataFrame:
    plot_df = stats_df.copy()
    x_min, x_max = 10.0, 100_000.0
    y_min, y_max = 0.02, 5.0
    plot_df["plot_N_original"] = plot_df["N_original"].clip(lower=x_min, upper=x_max)
    plot_df["plot_N_replication"] = plot_df["N_replication"].clip(lower=x_min, upper=x_max)
    plot_df["plot_D_original"] = plot_df["D_original"].clip(lower=y_min, upper=y_max)
    plot_df["plot_D_replication"] = plot_df["D_replication"].clip(lower=y_min, upper=y_max)
    plot_df["clip_n_max"] = plot_df["N_original"].gt(x_max) | plot_df["N_replication"].gt(x_max)
    plot_df["clip_d_low"] = plot_df["D_original"].lt(y_min) | plot_df["D_replication"].lt(y_min)
    plot_df["clip_d_high"] = plot_df["D_original"].gt(y_max) | plot_df["D_replication"].gt(y_max)
    return plot_df


def write_summary(stats_df: pd.DataFrame) -> None:
    counts = stats_df["category"].value_counts()
    total = len(stats_df)
    shrunk = int(counts.get("shrunk_still_sig", 0) + counts.get("shrunk_below_sig", 0))
    lines = [
        "# Current Figure 1 Arrows Plot Summary",
        "",
        f"Generated from `{ROOT_TABLE.relative_to(ROOT)}` using rows where `current_plot_rule_status == included_by_current_figure1_dn_rule`.",
        "",
        f"- Included rows: **{total:,}**",
        f"- Same/grew: **{int(counts.get('grew', 0)):,}**",
        f"- Shrunk but still significant: **{int(counts.get('shrunk_still_sig', 0)):,}**",
        f"- Shrunk below p < .05: **{int(counts.get('shrunk_below_sig', 0)):,}**",
        f"- Any shrinkage: **{shrunk:,}** ({100 * shrunk / total:.1f}%)",
        f"- Median original D: **{stats_df['D_original'].median():.3f}**",
        f"- Median replication D: **{stats_df['D_replication'].median():.3f}**",
        f"- Median original N: **{stats_df['N_original'].median():.0f}**",
        f"- Median replication N: **{stats_df['N_replication'].median():.0f}**",
        "",
    ]
    SUMMARY_OUT.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY_OUT.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    stats_df = current_included_pairs()
    plot_df = clipped_plot_frame(stats_df)
    plot_pairs = load_plot_pairs_function()
    REPORT_FIG.parent.mkdir(parents=True, exist_ok=True)
    DOCS_FIG.parent.mkdir(parents=True, exist_ok=True)
    plot_pairs(plot_df, stats_df, REPORT_FIG)
    DOCS_FIG.write_bytes(REPORT_FIG.read_bytes())
    write_summary(stats_df)
    print(f"Wrote {REPORT_FIG.relative_to(ROOT)} from {len(stats_df):,} rows")
    print(f"Wrote {DOCS_FIG.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
