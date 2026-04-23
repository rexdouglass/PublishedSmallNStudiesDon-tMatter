#!/usr/bin/env python3
"""Explore D-vs-N slopes in the Schwab/Cochrane effects data.

This is an exploratory small-study-effect screen. It uses D_proxy = z/sqrt(N)
as the main comparable effect proxy because the raw effect estimates mix log
odds ratios, standardized mean differences, and generic inverse-variance rows.
"""

from __future__ import annotations

import argparse
import math
import subprocess
from itertools import combinations
from pathlib import Path
from typing import Iterable

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats


EXPORT_COLUMNS = [
    "id",
    "study.name",
    "effect.es",
    "effect.se",
    "effect.N",
    "specialty",
    "outcome.group",
    "outcome.flag",
    "outcome.nr",
    "comparison.nr",
    "phase",
    "comparator",
    "RCT",
    "study.year",
    "z",
]


def export_cdsr(cdsr_rdata: Path, out_csv: Path) -> None:
    cols = ", ".join(f'"{c}"' for c in EXPORT_COLUMNS)
    r_code = f"""
load({str(cdsr_rdata)!r})
d <- as.data.frame(data)
d$cochrane_effects_row <- as.integer(rownames(d))
keep <- c("cochrane_effects_row", {cols})
d <- d[, keep]
write.csv(d, {str(out_csv)!r}, row.names=FALSE, na="")
"""
    subprocess.run(["Rscript", "--vanilla", "-e", r_code], check=True)


def read_inputs(args: argparse.Namespace) -> pd.DataFrame:
    interim = Path(args.interim)
    interim.mkdir(parents=True, exist_ok=True)
    exported = interim / "cdsr_effects_for_regression.csv"
    if args.refresh_export or not exported.exists():
        export_cdsr(Path(args.cdsr_rdata), exported)

    df = pd.read_csv(exported, dtype=str, keep_default_na=False)
    effects_path = Path(args.effects)
    if effects_path.exists():
        effects = pd.read_csv(
            effects_path,
            usecols=["Unnamed: 0", "study.id.sha1"],
            dtype=str,
            keep_default_na=False,
        ).rename(columns={"Unnamed: 0": "cochrane_effects_row"})
        df = df.merge(effects, how="left", on="cochrane_effects_row")

    pilot_path = Path(args.pilot_provenance)
    if pilot_path.exists():
        pilot_cols = [
            "cochrane_effects_row",
            "published_vs_unpublished",
            "journal_vs_nonjournal",
            "provenance_class",
            "numeric_source_inference_level",
        ]
        pilot = pd.read_csv(pilot_path, dtype=str, keep_default_na=False)
        pilot = pilot[[c for c in pilot_cols if c in pilot.columns]].drop_duplicates("cochrane_effects_row")
        df = df.merge(pilot, how="left", on="cochrane_effects_row")

    return df


def prepare(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for col in ["effect.es", "effect.se", "effect.N", "z", "outcome.nr", "comparison.nr", "study.year"]:
        out[col] = pd.to_numeric(out[col], errors="coerce")
    out["N"] = out["effect.N"]
    out["log10_N"] = np.log10(out["N"].where(out["N"] > 0))
    out["inv_sqrt_N"] = 1 / np.sqrt(out["N"].where(out["N"] > 0))
    out["abs_z"] = out["z"].abs()

    # Comparable proxy under the rough z ~= D * sqrt(N) relationship.
    out["D_proxy"] = out["z"] / np.sqrt(out["N"].where(out["N"] > 0))
    out["abs_D_proxy"] = out["D_proxy"].abs()

    # Best-effort transformed raw effect. This is only useful within outcome.flag strata.
    out["D_transformed"] = np.nan
    dich = out["outcome.flag"].eq("DICH") & (out["effect.es"] > 0)
    out.loc[dich, "D_transformed"] = np.log(out.loc[dich, "effect.es"])
    nondich = ~out["outcome.flag"].eq("DICH")
    out.loc[nondich, "D_transformed"] = out.loc[nondich, "effect.es"]
    out["abs_D_transformed"] = out["D_transformed"].abs()

    out["primary_efficacy_rct_row"] = (
        out["RCT"].eq("yes")
        & out["outcome.group"].eq("efficacy")
        & out["outcome.nr"].eq(1)
        & (out["abs_z"] < 20)
    )

    out["primary_efficacy_rct_one_per_study"] = False
    if "study.id.sha1" in out.columns:
        mask = out["primary_efficacy_rct_row"] & out["study.id.sha1"].fillna("").ne("")
        first_idx = (
            out.loc[mask]
            .sort_values(["study.id.sha1", "cochrane_effects_row"])
            .drop_duplicates("study.id.sha1", keep="first")
            .index
        )
        out.loc[first_idx, "primary_efficacy_rct_one_per_study"] = True

    for col in [
        "published_vs_unpublished",
        "journal_vs_nonjournal",
        "provenance_class",
        "numeric_source_inference_level",
    ]:
        if col not in out.columns:
            out[col] = ""
        out[col] = out[col].fillna("").replace("", "unmatched_or_unknown")

    return out


def ols_line(data: pd.DataFrame, x_col: str, y_col: str) -> dict[str, float | str | int]:
    x = pd.to_numeric(data[x_col], errors="coerce").to_numpy(dtype=float)
    y = pd.to_numeric(data[y_col], errors="coerce").to_numpy(dtype=float)
    valid = np.isfinite(x) & np.isfinite(y)
    x = x[valid]
    y = y[valid]
    n = len(x)
    if n < 3 or np.nanstd(x) == 0:
        return {
            "n_rows": n,
            "intercept": np.nan,
            "slope": np.nan,
            "slope_se": np.nan,
            "p_value": np.nan,
            "r_squared": np.nan,
            "pearson_r": np.nan,
            "spearman_r": np.nan,
            "x_min": np.nan,
            "x_max": np.nan,
            "y_mean": np.nan,
            "y_median": np.nan,
        }
    X = np.column_stack([np.ones(n), x])
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    yhat = X @ beta
    resid = y - yhat
    dof = n - 2
    s2 = float((resid @ resid) / dof)
    xtx_inv = np.linalg.inv(X.T @ X)
    se = np.sqrt(np.diag(s2 * xtx_inv))
    t_stat = beta[1] / se[1]
    p = 2 * stats.t.sf(abs(t_stat), dof)
    sst = float(((y - y.mean()) @ (y - y.mean())))
    r2 = 1 - float(resid @ resid) / sst if sst else np.nan
    pearson = stats.pearsonr(x, y).statistic if n >= 3 else np.nan
    spearman = stats.spearmanr(x, y).statistic if n >= 3 else np.nan
    return {
        "n_rows": n,
        "intercept": float(beta[0]),
        "slope": float(beta[1]),
        "slope_se": float(se[1]),
        "p_value": float(p),
        "r_squared": float(r2),
        "pearson_r": float(pearson),
        "spearman_r": float(spearman),
        "x_min": float(np.min(x)),
        "x_max": float(np.max(x)),
        "y_mean": float(np.mean(y)),
        "y_median": float(np.median(y)),
    }


def subset_frames(df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    base = df[(df["N"] > 0) & np.isfinite(df["D_proxy"]) & (df["abs_z"] < 20)].copy()
    return {
        "all_abs_z_lt_20": base,
        "rct_yes_abs_z_lt_20": base[base["RCT"].eq("yes")],
        "rct_no_abs_z_lt_20": base[base["RCT"].eq("no")],
        "primary_efficacy_rct_all_rows": base[base["primary_efficacy_rct_row"]],
        "primary_efficacy_rct_one_per_study": base[base["primary_efficacy_rct_one_per_study"]],
        "pilot_exact_provenance_rows": base[base["published_vs_unpublished"].ne("unmatched_or_unknown")],
    }


def run_grouped_lines(
    frames: dict[str, pd.DataFrame],
    group_specs: list[tuple[str, ...]],
    min_rows: int,
) -> pd.DataFrame:
    y_cols = ["abs_D_proxy", "D_proxy", "abs_D_transformed", "D_transformed"]
    x_cols = ["log10_N", "inv_sqrt_N"]
    rows: list[dict[str, object]] = []
    for subset_name, frame in frames.items():
        specs = [()] + group_specs
        for group_cols in specs:
            if group_cols and not all(col in frame.columns for col in group_cols):
                continue
            if group_cols:
                grouped: Iterable[tuple[object, pd.DataFrame]] = frame.groupby(list(group_cols), dropna=False)
            else:
                grouped = [(("all",), frame)]
            for key, group in grouped:
                if len(group) < min_rows:
                    continue
                if not isinstance(key, tuple):
                    key = (key,)
                group_label = "all" if not group_cols else " | ".join(f"{c}={v}" for c, v in zip(group_cols, key))
                for y_col in y_cols:
                    for x_col in x_cols:
                        result = ols_line(group, x_col, y_col)
                        if result["n_rows"] < min_rows:
                            continue
                        rows.append(
                            {
                                "subset": subset_name,
                                "grouping": "+".join(group_cols) if group_cols else "none",
                                "group": group_label,
                                "x": x_col,
                                "y": y_col,
                                **result,
                            }
                        )
    return pd.DataFrame(rows)


def top_slope_tables(summary: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    main = summary[(summary["x"].eq("log10_N")) & (summary["y"].eq("abs_D_proxy"))].copy()
    main = main[main["n_rows"] >= 100]
    negative = main.sort_values(["slope", "n_rows"], ascending=[True, False]).head(30)
    positive = main.sort_values(["slope", "n_rows"], ascending=[False, False]).head(20)
    provenance = main[
        main["grouping"].isin(["published_vs_unpublished", "journal_vs_nonjournal", "provenance_class"])
        | main["subset"].eq("pilot_exact_provenance_rows")
    ].sort_values(["subset", "grouping", "group"])
    return negative, positive, provenance


def plot_group_lines(df: pd.DataFrame, out_path: Path, title: str, group_col: str | None = None) -> None:
    data = df[(df["N"] > 0) & np.isfinite(df["abs_D_proxy"]) & (df["abs_z"] < 20)].copy()
    if data.empty:
        return
    if len(data) > 80000:
        data = data.sample(80000, random_state=123)

    fig, ax = plt.subplots(figsize=(9, 6))
    if group_col and group_col in data.columns:
        values = [v for v in data[group_col].dropna().unique() if str(v)]
        values = sorted(values, key=str)[:8]
    else:
        values = ["all"]
        data["_plot_group"] = "all"
        group_col = "_plot_group"

    colors = plt.cm.tab10(np.linspace(0, 1, max(len(values), 1)))
    for color, value in zip(colors, values):
        g = data[data[group_col].eq(value)]
        if len(g) < 10:
            continue
        ax.scatter(g["N"], g["abs_D_proxy"], s=5, alpha=0.08, color=color, label=f"{value} rows")
        fit = ols_line(g, "log10_N", "abs_D_proxy")
        if np.isfinite(fit["slope"]):
            xs = np.logspace(np.log10(max(g["N"].min(), 1)), np.log10(g["N"].max()), 100)
            ys = fit["intercept"] + fit["slope"] * np.log10(xs)
            ax.plot(xs, ys, color=color, linewidth=2, label=f"{value}: slope {fit['slope']:.4g}")

    ax.set_xscale("log")
    ax.set_xlabel("N (log scale)")
    ax.set_ylabel("|D proxy| = |z| / sqrt(N)")
    ax.set_title(title)
    ax.legend(fontsize=8)
    ax.grid(alpha=0.25)
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=160)
    plt.close(fig)


def write_markdown(
    out_path: Path,
    summary: pd.DataFrame,
    negative: pd.DataFrame,
    positive: pd.DataFrame,
    provenance: pd.DataFrame,
) -> None:
    def markdown_table(frame: pd.DataFrame) -> str:
        if frame.empty:
            return "_No rows._"
        cols = list(frame.columns)
        lines = [
            "| " + " | ".join(cols) + " |",
            "| " + " | ".join(["---"] * len(cols)) + " |",
        ]
        for _, row in frame.iterrows():
            values = [str(row[col]).replace("\n", " ") for col in cols]
            lines.append("| " + " | ".join(values) + " |")
        return "\n".join(lines)

    def fmt_table(df: pd.DataFrame, cols: list[str], n: int = 15) -> str:
        if df.empty:
            return "_No rows._"
        show = df[cols].head(n).copy()
        for col in ["slope", "intercept", "r_squared", "p_value", "spearman_r"]:
            if col in show.columns:
                show[col] = show[col].map(lambda x: "" if pd.isna(x) else f"{float(x):.4g}")
        return markdown_table(show)

    overall = summary[
        summary["subset"].eq("all_abs_z_lt_20")
        & summary["grouping"].eq("none")
        & summary["x"].eq("log10_N")
        & summary["y"].isin(["abs_D_proxy", "D_proxy"])
    ].copy()
    primary = summary[
        summary["subset"].isin(["primary_efficacy_rct_all_rows", "primary_efficacy_rct_one_per_study"])
        & summary["grouping"].eq("none")
        & summary["x"].eq("log10_N")
        & summary["y"].isin(["abs_D_proxy", "D_proxy"])
    ].copy()

    lines = [
        "# D vs N Regression Scan",
        "",
        "Definition: `D_proxy = z / sqrt(effect.N)`. The main small-study screen is `|D_proxy| ~ log10(N)`.",
        "A publication-bias-like small-study pattern is a negative slope for `|D_proxy| ~ log10(N)`.",
        "Rows are filtered to `N > 0`, finite `D_proxy`, and `|z| < 20`.",
        "",
        "## Overall Lines",
        "",
        fmt_table(overall, ["subset", "y", "n_rows", "intercept", "slope", "r_squared", "p_value", "spearman_r"]),
        "",
        "## Primary Efficacy RCT Lines",
        "",
        fmt_table(primary, ["subset", "y", "n_rows", "intercept", "slope", "r_squared", "p_value", "spearman_r"]),
        "",
        "## Most Negative Slopes",
        "",
        fmt_table(
            negative,
            ["subset", "grouping", "group", "n_rows", "slope", "r_squared", "p_value", "spearman_r"],
            20,
        ),
        "",
        "## Most Positive Slopes",
        "",
        fmt_table(
            positive,
            ["subset", "grouping", "group", "n_rows", "slope", "r_squared", "p_value", "spearman_r"],
            12,
        ),
        "",
        "## Provenance Pilot Slopes",
        "",
        fmt_table(
            provenance,
            ["subset", "grouping", "group", "n_rows", "slope", "r_squared", "p_value", "spearman_r"],
            40,
        ),
        "",
        "## Caution",
        "",
        "This is not a formal publication-bias model. `|D_proxy|` naturally declines with N even without selective publication because sampling variation is larger in smaller studies. The useful question here is comparative: whether provenance/source-related strata show materially different slopes.",
        "",
    ]
    out_path.write_text("\n".join(lines))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cdsr-rdata", default="data/raw/osf/CDSR.RData")
    parser.add_argument("--effects", default="data/raw/osf/CochraneEffects.csv")
    parser.add_argument("--pilot-provenance", default="data/derived/package_effect_provenance_pilot.csv")
    parser.add_argument("--out", default="data/derived")
    parser.add_argument("--reports", default="reports/d_vs_n")
    parser.add_argument("--interim", default="data/interim")
    parser.add_argument("--refresh-export", action="store_true")
    parser.add_argument("--min-rows", type=int, default=100)
    args = parser.parse_args()

    out_dir = Path(args.out)
    report_dir = Path(args.reports)
    out_dir.mkdir(parents=True, exist_ok=True)
    report_dir.mkdir(parents=True, exist_ok=True)

    df = prepare(read_inputs(args))
    frames = subset_frames(df)

    group_specs = [
        ("RCT",),
        ("outcome.group",),
        ("outcome.flag",),
        ("comparator",),
        ("phase",),
        ("RCT", "outcome.group"),
        ("outcome.group", "outcome.flag"),
        ("RCT", "outcome.group", "outcome.flag"),
        ("comparator", "outcome.group"),
        ("published_vs_unpublished",),
        ("journal_vs_nonjournal",),
        ("provenance_class",),
    ]
    summary = run_grouped_lines(frames, group_specs, args.min_rows)
    summary.to_csv(out_dir / "d_vs_n_regression_summary.csv", index=False)

    negative, positive, provenance = top_slope_tables(summary)
    negative.to_csv(out_dir / "d_vs_n_most_negative_slopes.csv", index=False)
    positive.to_csv(out_dir / "d_vs_n_most_positive_slopes.csv", index=False)
    provenance.to_csv(out_dir / "d_vs_n_provenance_slopes.csv", index=False)
    write_markdown(out_dir / "d_vs_n_regression_summary.md", summary, negative, positive, provenance)

    base = frames["all_abs_z_lt_20"]
    plot_group_lines(base, report_dir / "all_abs_d_proxy_by_n.png", "All rows: |D proxy| vs N")
    plot_group_lines(base, report_dir / "outcome_group_abs_d_proxy_by_n.png", "By outcome group: |D proxy| vs N", "outcome.group")
    plot_group_lines(frames["primary_efficacy_rct_all_rows"], report_dir / "primary_efficacy_abs_d_proxy_by_n.png", "Primary efficacy RCT rows: |D proxy| vs N")
    plot_group_lines(frames["pilot_exact_provenance_rows"], report_dir / "provenance_pilot_abs_d_proxy_by_n.png", "Pilot provenance rows: |D proxy| vs N", "published_vs_unpublished")

    print(f"Rows available: {len(df):,}")
    print(f"Rows after main filter: {len(base):,}")
    print(f"Regression lines written: {len(summary):,}")
    print(f"Wrote {out_dir / 'd_vs_n_regression_summary.md'}")
    print(f"Wrote plots under {report_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
