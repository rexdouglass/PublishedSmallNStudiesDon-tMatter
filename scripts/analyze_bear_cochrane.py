#!/usr/bin/env python3
"""Analyze the BEAR Cochrane slice by source data type.

BEAR's Cochrane rows are useful for the current question because they retain a
`group` field with Cochrane source data type: published, mixed, sought, and
unpublished. For continuous outcomes, BEAR uses `measure == "SMD"` with `b` as
the effect size and `ss` as sample size.
"""

from __future__ import annotations

import argparse
import math
import subprocess
from pathlib import Path
from typing import Iterable

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats


BEAR_COLUMNS = [
    "dataset",
    "metaid",
    "studyid",
    "method",
    "measure",
    "z",
    "b",
    "se",
    "year",
    "ss",
    "subset",
    "group",
    "n",
    "source",
]


def export_cochrane_from_bear(bear_rds: Path, out_csv: Path) -> None:
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    cols = ", ".join(f'"{col}"' for col in BEAR_COLUMNS)
    r_code = f"""
bear <- readRDS({str(bear_rds)!r})
co <- bear[bear$dataset == "Cochrane", c({cols})]
write.csv(co, {str(out_csv)!r}, row.names = FALSE, na = "")
"""
    subprocess.run(["Rscript", "--vanilla", "-e", r_code], check=True)


def read_cochrane(args: argparse.Namespace) -> pd.DataFrame:
    interim = Path(args.interim)
    exported = interim / "cochrane_bear_rows.csv"
    if args.refresh_export or not exported.exists():
        export_cochrane_from_bear(Path(args.bear_rds), exported)
    return pd.read_csv(exported, dtype=str, keep_default_na=False)


def prepare(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for col in ["z", "b", "se", "year", "ss", "n"]:
        out[col] = pd.to_numeric(out[col], errors="coerce")

    out["source_type"] = out["group"].replace("", "unknown")
    out["method_type"] = out["method"].replace("", "unknown")
    out["abs_z"] = out["z"].abs()
    out["abs_b"] = out["b"].abs()
    out["d_proxy2"] = 2 * out["abs_z"] / np.sqrt(out["ss"].where(out["ss"] > 0))
    out["ln_ss"] = np.log(out["ss"].where(out["ss"] > 0))
    out["ln_abs_b"] = np.log(out["abs_b"].where(out["abs_b"] > 0))
    out["ln_d_proxy2"] = np.log(out["d_proxy2"].where(out["d_proxy2"] > 0))
    out["log10_ss"] = np.log10(out["ss"].where(out["ss"] > 0))
    out["significant_p05"] = out["abs_z"] >= 1.96
    out["above_two_sample_p05_curve"] = out["abs_b"] >= (2 * 1.96 / np.sqrt(out["ss"].where(out["ss"] > 0)))
    out["above_two_sample_p10_curve"] = out["abs_b"] >= (2 * 1.6448536269514722 / np.sqrt(out["ss"].where(out["ss"] > 0)))
    out["above_two_sample_p01_curve"] = out["abs_b"] >= (2 * 2.5758293035489004 / np.sqrt(out["ss"].where(out["ss"] > 0)))
    out["bear_source_note"] = np.where(
        out["source_type"].eq("published"),
        "published-source study data, not necessarily a strict one-journal-paper row",
        np.where(
            out["source_type"].eq("sought"),
            "published data with unpublished data sought but not used",
            np.where(
                out["source_type"].eq("mixed"),
                "published and unpublished data mixed",
                np.where(out["source_type"].eq("unpublished"), "unpublished-source study data", "unknown source type"),
            ),
        ),
    )
    return out


def dproxy_plot_window(data: pd.DataFrame) -> pd.Series:
    return (
        data["ss"].between(10, 1_000_000)
        & data["d_proxy2"].between(0.01, 5)
        & (data["abs_z"] < 20)
        & np.isfinite(data["ln_ss"])
        & np.isfinite(data["ln_d_proxy2"])
    )


def ols_line(data: pd.DataFrame, x_col: str, y_col: str) -> dict[str, float | int]:
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
    p_value = 2 * stats.t.sf(abs(t_stat), dof)
    sst = float(((y - y.mean()) @ (y - y.mean())))
    r2 = 1 - float(resid @ resid) / sst if sst else np.nan

    return {
        "n_rows": n,
        "intercept": float(beta[0]),
        "slope": float(beta[1]),
        "slope_se": float(se[1]),
        "p_value": float(p_value),
        "r_squared": float(r2),
        "pearson_r": float(stats.pearsonr(x, y).statistic),
        "spearman_r": float(stats.spearmanr(x, y).statistic),
    }


def summarize_group(data: pd.DataFrame) -> dict[str, float | int]:
    valid = data[np.isfinite(data["abs_b"]) & (data["ss"] > 0)]
    n_rows = len(valid)
    return {
        "n_rows": n_rows,
        "n_reviews": int(valid["metaid"].nunique()),
        "n_studies": int(valid[["metaid", "studyid"]].drop_duplicates().shape[0]),
        "median_ss": float(valid["ss"].median()) if n_rows else np.nan,
        "median_abs_b": float(valid["abs_b"].median()) if n_rows else np.nan,
        "pct_abs_z_ge_1_96": float(valid["significant_p05"].mean()) if n_rows else np.nan,
        "pct_above_two_sample_p05_curve": float(valid["above_two_sample_p05_curve"].mean()) if n_rows else np.nan,
        "pct_above_two_sample_p10_curve": float(valid["above_two_sample_p10_curve"].mean()) if n_rows else np.nan,
        "pct_above_two_sample_p01_curve": float(valid["above_two_sample_p01_curve"].mean()) if n_rows else np.nan,
    }


def slice_specs(df: pd.DataFrame) -> Iterable[tuple[str, pd.DataFrame]]:
    smd = df[df["measure"].eq("SMD")].copy()
    smd_main = smd[(smd["ss"] > 0) & (smd["abs_b"] > 0) & (smd["se"] > 0) & (smd["abs_z"] < 20)].copy()
    smd_plausible = smd_main[smd_main["abs_b"] <= 10].copy()

    yield "smd_all_abs_z_lt_20", smd_main
    yield "smd_abs_b_le_10_abs_z_lt_20", smd_plausible

    for source in sorted(smd_main["source_type"].dropna().unique()):
        yield f"smd_source_{source}_abs_z_lt_20", smd_main[smd_main["source_type"].eq(source)]
    for method in sorted(smd_main["method_type"].dropna().unique()):
        yield f"smd_method_{method}_abs_z_lt_20", smd_main[smd_main["method_type"].eq(method)]

    for source in sorted(smd_main["source_type"].dropna().unique()):
        for method in sorted(smd_main["method_type"].dropna().unique()):
            yield (
                f"smd_source_{source}_method_{method}_abs_z_lt_20",
                smd_main[smd_main["source_type"].eq(source) & smd_main["method_type"].eq(method)],
            )

    for source in sorted(smd_plausible["source_type"].dropna().unique()):
        yield f"smd_abs_b_le_10_source_{source}_abs_z_lt_20", smd_plausible[smd_plausible["source_type"].eq(source)]
    for source in sorted(smd_plausible["source_type"].dropna().unique()):
        for method in sorted(smd_plausible["method_type"].dropna().unique()):
            yield (
                f"smd_abs_b_le_10_source_{source}_method_{method}_abs_z_lt_20",
                smd_plausible[
                    smd_plausible["source_type"].eq(source) & smd_plausible["method_type"].eq(method)
                ],
            )


def build_regression_table(df: pd.DataFrame, min_rows: int) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for slice_name, data in slice_specs(df):
        if len(data) < min_rows:
            continue
        summary = summarize_group(data)
        for x_col, y_col, model_name in [
            ("ln_ss", "ln_abs_b", "loglog"),
            ("log10_ss", "abs_b", "semilog_abs_b"),
            ("log10_ss", "abs_z", "semilog_abs_z"),
        ]:
            fit = ols_line(data, x_col, y_col)
            if fit["n_rows"] < min_rows:
                continue
            source_values = sorted(v for v in data["source_type"].dropna().unique() if v)
            method_values = sorted(v for v in data["method_type"].dropna().unique() if v)
            rows.append(
                {
                    "slice": slice_name,
                    "model": model_name,
                    "x": x_col,
                    "y": y_col,
                    "source_types": ";".join(source_values),
                    "method_types": ";".join(method_values),
                    **summary,
                    **fit,
                    "tenfold_multiplier": float(math.exp(fit["slope"] * math.log(10)))
                    if model_name == "loglog" and np.isfinite(fit["slope"])
                    else np.nan,
                    "tenfold_pct_reduction": float(1 - math.exp(fit["slope"] * math.log(10)))
                    if model_name == "loglog" and np.isfinite(fit["slope"])
                    else np.nan,
                }
            )
    return pd.DataFrame(rows)


def build_dproxy_bridge_table(df: pd.DataFrame, min_rows: int) -> pd.DataFrame:
    rows: list[dict[str, object]] = []

    def add_row(slice_name: str, data: pd.DataFrame) -> None:
        if len(data) < min_rows:
            return
        plotted = data[dproxy_plot_window(data)].copy()
        fit = ols_line(plotted, "ln_ss", "ln_d_proxy2")
        if fit["n_rows"] < min_rows:
            return
        rows.append(
            {
                "slice": slice_name,
                "n_rows": len(data),
                "plot_n": len(plotted),
                "n_reviews": int(data["metaid"].nunique()),
                "n_studies": int(data[["metaid", "studyid"]].drop_duplicates().shape[0]),
                "median_ss": float(data["ss"].median()),
                "median_abs_d_proxy": float(data["d_proxy2"].median()),
                "pct_abs_z_ge_1_96": float(100 * data["significant_p05"].mean()),
                **fit,
                "tenfold_pct_reduction": float(100 * (1 - math.exp(fit["slope"] * math.log(10))))
                if np.isfinite(fit["slope"])
                else np.nan,
            }
        )

    base = df[(df["ss"] > 0) & np.isfinite(df["d_proxy2"])].copy()
    add_row("bear_all_cont_dich_dproxy", base)
    for measure in sorted(base["measure"].dropna().unique()):
        add_row(f"bear_measure_{measure}_dproxy", base[base["measure"].eq(measure)])
    for source in sorted(base["source_type"].dropna().unique()):
        add_row(f"bear_source_{source}_dproxy", base[base["source_type"].eq(source)])
    for method in sorted(base["method_type"].dropna().unique()):
        add_row(f"bear_method_{method}_dproxy", base[base["method_type"].eq(method)])
    for source in sorted(base["source_type"].dropna().unique()):
        for method in sorted(base["method_type"].dropna().unique()):
            add_row(
                f"bear_source_{source}_method_{method}_dproxy",
                base[base["source_type"].eq(source) & base["method_type"].eq(method)],
            )
    return pd.DataFrame(rows)


def interaction_tests(df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    smd = df[
        df["measure"].eq("SMD")
        & (df["ss"] > 0)
        & (df["abs_b"] > 0)
        & (df["se"] > 0)
        & (df["abs_z"] < 20)
    ].copy()

    for label, data in [
        ("smd_all_abs_z_lt_20", smd),
        ("smd_abs_b_le_10_abs_z_lt_20", smd[smd["abs_b"] <= 10].copy()),
    ]:
        if len(data) < 20:
            continue

        for factor, baseline, compare in [
            ("source_type", "published", "mixed"),
            ("source_type", "published", "sought"),
            ("source_type", "published", "unpublished"),
            ("method_type", "unknown", "RCT"),
        ]:
            sub = data[data[factor].isin([baseline, compare])].copy()
            sub = sub[np.isfinite(sub["ln_ss"]) & np.isfinite(sub["ln_abs_b"])]
            if len(sub) < 20 or sub[factor].nunique() < 2:
                continue
            indicator = sub[factor].eq(compare).astype(float).to_numpy()
            x = sub["ln_ss"].to_numpy(dtype=float)
            y = sub["ln_abs_b"].to_numpy(dtype=float)
            X = np.column_stack([np.ones(len(sub)), x, indicator, x * indicator])
            beta, *_ = np.linalg.lstsq(X, y, rcond=None)
            resid = y - X @ beta
            dof = len(sub) - X.shape[1]
            s2 = float((resid @ resid) / dof)
            vcov = s2 * np.linalg.inv(X.T @ X)
            se = np.sqrt(np.diag(vcov))
            t_stat = beta[3] / se[3]
            p_value = 2 * stats.t.sf(abs(t_stat), dof)
            rows.append(
                {
                    "slice": label,
                    "factor": factor,
                    "baseline": baseline,
                    "compare": compare,
                    "n_rows": len(sub),
                    "baseline_slope": float(beta[1]),
                    "compare_slope": float(beta[1] + beta[3]),
                    "slope_difference_compare_minus_baseline": float(beta[3]),
                    "slope_difference_se": float(se[3]),
                    "p_value": float(p_value),
                }
            )
    return pd.DataFrame(rows)


def plot_source_lines(df: pd.DataFrame, out_path: Path) -> None:
    data = df[
        df["measure"].eq("SMD")
        & (df["ss"] > 0)
        & (df["abs_b"] > 0)
        & (df["se"] > 0)
        & (df["abs_z"] < 20)
        & (df["abs_b"] <= 10)
    ].copy()
    if data.empty:
        return

    fig, ax = plt.subplots(figsize=(9, 6))
    palette = {
        "published": "#1f77b4",
        "mixed": "#d62728",
        "sought": "#2ca02c",
        "unpublished": "#9467bd",
        "unknown": "#7f7f7f",
    }
    for source in ["published", "mixed", "sought", "unpublished", "unknown"]:
        group = data[data["source_type"].eq(source)]
        if len(group) < 5:
            continue
        plot_group = group
        if len(plot_group) > 20000:
            plot_group = plot_group.sample(20000, random_state=123)
        color = palette.get(source, "#7f7f7f")
        ax.scatter(
            plot_group["ss"],
            plot_group["abs_b"],
            s=10 if source != "published" else 6,
            alpha=0.28 if source != "published" else 0.14,
            color=color,
            label=f"{source} rows",
            edgecolors="none",
        )
        fit = ols_line(group, "ln_ss", "ln_abs_b")
        if np.isfinite(fit["slope"]):
            xs = np.logspace(np.log10(max(group["ss"].min(), 1)), np.log10(group["ss"].max()), 160)
            ys = np.exp(fit["intercept"]) * xs ** fit["slope"]
            ax.plot(xs, ys, color=color, linewidth=2.0, label=f"{source}: slope {fit['slope']:.3f}")

    xs = np.logspace(np.log10(max(data["ss"].min(), 2)), np.log10(data["ss"].max()), 200)
    ax.plot(xs, 2 * 1.6448536269514722 / np.sqrt(xs), color="black", linestyle=":", linewidth=1.1, label="two-sample p<0.10")
    ax.plot(xs, 2 * 1.96 / np.sqrt(xs), color="black", linestyle="--", linewidth=1.1, label="two-sample p<0.05")
    ax.plot(xs, 2 * 2.5758293035489004 / np.sqrt(xs), color="black", linestyle="-.", linewidth=1.1, label="two-sample p<0.01")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("Sample size `ss` (log scale)")
    ax.set_ylabel("|SMD| from BEAR Cochrane (log scale)")
    ax.set_title("BEAR Cochrane continuous outcomes by source data type")
    ax.grid(alpha=0.25, which="both")
    ax.legend(fontsize=8, ncol=2)
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=180)
    plt.close(fig)


def markdown_table(frame: pd.DataFrame, cols: list[str], n: int | None = None) -> str:
    if frame.empty:
        return "_No rows._"
    show = frame[cols].copy()
    if n is not None:
        show = show.head(n)
    for col in show.columns:
        if pd.api.types.is_float_dtype(show[col]):
            show[col] = show[col].map(lambda x: "" if pd.isna(x) else f"{float(x):.4g}")
    lines = [
        "| " + " | ".join(show.columns) + " |",
        "| " + " | ".join(["---"] * len(show.columns)) + " |",
    ]
    for _, row in show.iterrows():
        lines.append("| " + " | ".join(str(row[col]).replace("\n", " ") for col in show.columns) + " |")
    return "\n".join(lines)


def write_summary(out_path: Path, df: pd.DataFrame, regs: pd.DataFrame, interactions: pd.DataFrame) -> None:
    co = df[df["dataset"].eq("Cochrane")].copy()
    smd = co[co["measure"].eq("SMD")].copy()
    counts = (
        co.groupby(["group", "method", "measure"], dropna=False)
        .size()
        .reset_index(name="n")
        .sort_values(["group", "method", "measure"])
    )
    loglog = regs[regs["model"].eq("loglog")].copy()
    keep_slices = [
        "smd_all_abs_z_lt_20",
        "smd_abs_b_le_10_abs_z_lt_20",
        "smd_source_published_abs_z_lt_20",
        "smd_source_mixed_abs_z_lt_20",
        "smd_source_sought_abs_z_lt_20",
        "smd_source_unpublished_abs_z_lt_20",
        "smd_source_published_method_RCT_abs_z_lt_20",
        "smd_source_published_method_unknown_abs_z_lt_20",
        "smd_abs_b_le_10_source_published_method_RCT_abs_z_lt_20",
        "smd_abs_b_le_10_source_published_method_unknown_abs_z_lt_20",
    ]
    highlights = loglog[loglog["slice"].isin(keep_slices)].copy()
    highlights["pct_abs_z_ge_1_96"] *= 100
    highlights["pct_above_two_sample_p05_curve"] *= 100
    highlights["tenfold_pct_reduction"] *= 100

    lines = [
        "# BEAR Cochrane Source-Type SMD Analysis",
        "",
        f"Rows in BEAR Cochrane slice: {len(co):,}.",
        f"SMD rows: {len(smd):,}.",
        "",
        "`group` is BEAR's retained Cochrane source data type: `published`, `mixed`, `sought`, or `unpublished`.",
        "`measure == SMD` is the continuous-outcome slice; `b` is the effect size and `ss` is sample size.",
        "`method` is BEAR's RCT flag. It has `RCT` and `unknown`, not a validated observational-study flag.",
        "",
        "## Counts",
        "",
        markdown_table(counts, ["group", "method", "measure", "n"]),
        "",
        "## Main Log-Log Lines",
        "",
        "Model: `ln(|b|) ~ ln(ss)`, filtered to SMD rows with `ss > 0`, `se > 0`, `|b| > 0`, and `|z| < 20`.",
        "",
        markdown_table(
            highlights,
            [
                "slice",
                "n_rows",
                "n_reviews",
                "n_studies",
                "median_ss",
                "median_abs_b",
                "slope",
                "r_squared",
                "p_value",
                "tenfold_pct_reduction",
                "pct_abs_z_ge_1_96",
                "pct_above_two_sample_p05_curve",
            ],
        ),
        "",
        "## Interaction Tests",
        "",
        "Interaction model: `ln(|b|) ~ ln(ss) * factor`.",
        "",
        markdown_table(
            interactions,
            [
                "slice",
                "factor",
                "baseline",
                "compare",
                "n_rows",
                "baseline_slope",
                "compare_slope",
                "slope_difference_compare_minus_baseline",
                "p_value",
            ],
        ),
        "",
        "## Bridge To Draft Cochrane Proxy",
        "",
        "The old draft's Cochrane appendix used a cross-outcome proxy close to `d = 2|z|/sqrt(N)`. The script also writes `cochrane_allrows_dproxy2_source_loglog.csv` with the same proxy applied to all BEAR Cochrane continuous/dichotomous rows. This is separate from the raw SMD analysis above.",
        "",
        "## Interpretation Notes",
        "",
        "- `published` is a Cochrane/RevMan source-data category, not proof of a strict journal-article-only row.",
        "- `sought` means published data were used after unpublished data were sought but not used, so it is closer to published-only than to mixed/unpublished.",
        "- This BEAR snapshot is a 2025/2026 processed CDSR extraction, not the older OSF Schwab historical extract.",
        "- The source-type split is still directly useful because it tests whether the published-source continuous Cochrane rows show the same small-study slope as the mixed/unpublished rows.",
        "",
    ]
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bear-rds", default="data/raw/bear/BEAR.rds")
    parser.add_argument("--interim", default="data/interim/bear")
    parser.add_argument("--out", default="data/derived/bear")
    parser.add_argument("--reports", default="reports/d_vs_n")
    parser.add_argument("--refresh-export", action="store_true")
    parser.add_argument("--min-rows", type=int, default=20)
    args = parser.parse_args()

    out_dir = Path(args.out)
    report_dir = Path(args.reports)
    out_dir.mkdir(parents=True, exist_ok=True)
    report_dir.mkdir(parents=True, exist_ok=True)

    df = prepare(read_cochrane(args))
    df.to_csv(out_dir / "cochrane_bear_rows_annotated.csv.gz", index=False)
    smd = df[df["measure"].eq("SMD")].copy()
    smd.to_csv(out_dir / "cochrane_bear_smd_rows_annotated.csv.gz", index=False)

    regs = build_regression_table(df, min_rows=args.min_rows)
    regs.to_csv(out_dir / "cochrane_smd_source_loglog.csv", index=False)

    dproxy = build_dproxy_bridge_table(df, min_rows=args.min_rows)
    dproxy.to_csv(out_dir / "cochrane_allrows_dproxy2_source_loglog.csv", index=False)

    interactions = interaction_tests(df)
    interactions.to_csv(out_dir / "cochrane_smd_source_rct_interactions.csv", index=False)

    plot_source_lines(df, report_dir / "bear_cochrane_smd_source_loglog.png")
    write_summary(out_dir / "cochrane_bear_source_summary.md", df, regs, interactions)

    print(f"BEAR Cochrane rows: {len(df):,}")
    print(f"SMD rows: {len(smd):,}")
    print(f"Wrote {out_dir / 'cochrane_smd_source_loglog.csv'}")
    print(f"Wrote {out_dir / 'cochrane_allrows_dproxy2_source_loglog.csv'}")
    print(f"Wrote {out_dir / 'cochrane_bear_source_summary.md'}")
    print(f"Wrote {report_dir / 'bear_cochrane_smd_source_loglog.png'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
