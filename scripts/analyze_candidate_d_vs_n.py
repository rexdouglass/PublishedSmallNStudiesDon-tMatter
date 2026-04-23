#!/usr/bin/env python3
"""Compute log-log D-vs-N summaries for normalized candidate corpora."""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats
from matplotlib.lines import Line2D
from matplotlib.ticker import FixedLocator, FixedFormatter, NullFormatter
from matplotlib.transforms import blended_transform_factory


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def fit_loglog(df: pd.DataFrame, d_col: str, n_col: str) -> dict[str, float | int]:
    d = df[[d_col, n_col]].copy()
    d[d_col] = pd.to_numeric(d[d_col], errors="coerce")
    d[n_col] = pd.to_numeric(d[n_col], errors="coerce")
    d = d[(d[d_col] > 0) & (d[n_col] > 0)].dropna()
    if len(d) < 3 or d[n_col].nunique() < 2:
        return {
            "n": len(d),
            "slope": np.nan,
            "intercept": np.nan,
            "slope_se": np.nan,
            "p_value": np.nan,
            "r_squared": np.nan,
            "median_D": float(d[d_col].median()) if len(d) else np.nan,
            "median_N": float(d[n_col].median()) if len(d) else np.nan,
        }
    x = np.log10(d[n_col].to_numpy(dtype=float))
    y = np.log10(d[d_col].to_numpy(dtype=float))
    X = np.column_stack([np.ones(len(x)), x])
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    yhat = X @ beta
    resid = y - yhat
    dof = len(x) - 2
    s2 = float((resid @ resid) / dof)
    se = np.sqrt(np.diag(s2 * np.linalg.inv(X.T @ X)))
    t = beta[1] / se[1]
    sst = float(((y - y.mean()) @ (y - y.mean())))
    return {
        "n": len(d),
        "slope": float(beta[1]),
        "intercept": float(beta[0]),
        "slope_se": float(se[1]),
        "p_value": float(2 * stats.t.sf(abs(t), dof)),
        "r_squared": float(1 - float(resid @ resid) / sst) if sst else np.nan,
        "median_D": float(d[d_col].median()),
        "median_N": float(d[n_col].median()),
    }


def collapse_clean_published_field(field: str) -> str:
    s = (field or "").strip().lower()
    if s in {
        "psychology",
        "psychology and health",
        "psychology_social_personality",
        "social psychology",
        "clinical psychology",
        "health psychology",
        "psychopathology",
        "gender stereotypes",
        "psychology_replication",
    }:
        return "Psychology"
    if s in {
        "cognitive psychology",
        "developmental psychology",
        "developmental_psychology",
        "differential psychology",
        "judgment and decision making",
        "linguistics",
        "experimental philosophy",
        "evolutionary psychology",
        "animal psychology",
        "social/cognitive psychology",
    }:
        return "Cognitive / Behavioral"
    if s in {
        "io_psychology_management",
        "business",
        "marketing",
        "marketing/org behavior",
        "management",
        "organizational psychology",
        "consumer psychology",
        "consumer research",
    }:
        return "Business / IO"
    if s in {"economics", "economics and finance", "economics_nudge"}:
        return "Economics"
    if s in {
        "political science",
        "political_science",
        "political psychology",
        "law",
    }:
        return "Political Science"
    if s in {
        "sociology and criminology",
        "sociology",
        "criminology",
    }:
        return "Sociology / Criminology"
    if s in {"education", "social_intervention_research", "communication science"}:
        return "Education / Social Intervention"
    if s in {"neuroscience", "preclinical_cancer_biology", "human genetics"}:
        return "Neuroscience / Biomedicine"
    if s in {"medicine_rct", "medicine_psychiatry", "medicine", "health", "sports science"}:
        return "Medicine / Clinical"
    return "Other"


def slope_tables(rows: pd.DataFrame, papers: pd.DataFrame) -> pd.DataFrame:
    tables: list[pd.DataFrame] = []
    for level, df, d_col, n_col in [
        ("row", rows, "abs_D", "N"),
        ("paper", papers, "D_median", "N_median"),
    ]:
        for published_only in [False, True]:
            data = df.copy()
            if published_only:
                data = data[data["published_original_candidate"] & ~data["comparator_only"]]
            group_cols = ["source_corpus", "field", "source_kind", "published_scope"]
            out_rows = []
            for key, g in data.groupby(group_cols, dropna=False):
                result = fit_loglog(g, d_col, n_col)
                out_rows.append(
                    {
                        "level": level,
                        "subset": "published_original_candidates" if published_only else "all_usable_rows",
                        **dict(zip(group_cols, key)),
                        **result,
                    }
                )
            tables.append(pd.DataFrame(out_rows))
    return pd.concat(tables, ignore_index=True).sort_values(["level", "subset", "n"], ascending=[True, True, False])


def plot_main_papers(papers: pd.DataFrame, out_dir: Path, derived_dir: Path) -> None:
    main = papers[papers["published_original_candidate"] & ~papers["comparator_only"]].copy()
    if main.empty:
        return

    main["field_group"] = main["field"].map(collapse_clean_published_field)
    main["field_group"] = main["field_group"].replace({"Other": "Medicine / Clinical"})
    main = main[(main["N_median"] > 0) & (main["D_median"] > 0)].copy()

    field_summary = (
        main.groupby("field_group", dropna=False)
        .agg(
            n_papers=("unit_id", "size"),
            median_D=("D_median", "median"),
            median_N=("N_median", "median"),
            source_corpora=("source_corpus", lambda x: ", ".join(sorted(set(x)))),
            raw_fields=("field", lambda x: ", ".join(sorted(set(x)))),
        )
        .reset_index()
        .sort_values("n_papers", ascending=False)
    )
    field_summary.to_csv(derived_dir / "candidate_published_field_groups.csv", index=False)

    colors = {
        "Psychology": "#2b6cb0",
        "Business / IO": "#1f9d8a",
        "Political Science": "#7b3f98",
        "Sociology / Criminology": "#8e6bbd",
        "Neuroscience / Biomedicine": "#e67e22",
        "Education / Social Intervention": "#b5476d",
        "Economics": "#3f7f3f",
        "Cognitive / Behavioral": "#8a5a2b",
        "Medicine / Clinical": "#c0392b",
    }
    markers = {
        "Psychology": "o",
        "Business / IO": "s",
        "Political Science": "^",
        "Sociology / Criminology": "v",
        "Neuroscience / Biomedicine": "D",
        "Education / Social Intervention": "P",
        "Economics": "X",
        "Cognitive / Behavioral": "*",
        "Medicine / Clinical": "<",
    }
    fig, ax = plt.subplots(figsize=(10.5, 7.5))
    for field_group, g in main.groupby("field_group"):
        color = colors.get(field_group, "#666666")
        marker = markers.get(field_group, "o")
        ax.scatter(
            g["N_median"],
            g["D_median"],
            s=14,
            alpha=0.18,
            color=color,
            marker=marker,
            edgecolors="none",
            rasterized=True,
        )

    summary_rows = []
    z10 = 1.6448536269514722
    overall_sig = 100 * (main["D_median"] >= (2 * z10 / np.sqrt(main["N_median"]))).mean()
    overall_median_d = float(main["D_median"].median())
    n_fields = int(field_summary["field_group"].nunique())
    for field_group, g in main.groupby("field_group"):
        result = fit_loglog(g, "D_median", "N_median")
        above_p10 = g["D_median"] >= (2 * z10 / np.sqrt(g["N_median"]))
        summary_rows.append(
            {
                "field_group": field_group,
                "n_papers": len(g),
                "median_D": float(g["D_median"].median()),
                "median_N": float(g["N_median"].median()),
                "pct_above_p10": float(100 * above_p10.mean()),
                "slope": result["slope"],
                "slope_se": result["slope_se"],
                "r_squared": result["r_squared"],
            }
        )
    field_fit = pd.DataFrame(summary_rows).sort_values("n_papers", ascending=False)
    field_fit.to_csv(derived_dir / "candidate_published_field_group_slopes.csv", index=False)

    x_min_plot = 10
    x_max_plot = 1e5
    y_min_plot = 0.02
    y_max_plot = 5.0
    xs = np.logspace(np.log10(x_min_plot), np.log10(x_max_plot), 200)

    overall = fit_loglog(main, "D_median", "N_median")

    for row in field_fit.itertuples(index=False):
        color = colors.get(row.field_group, "#666666")
        marker = markers.get(row.field_group, "o")
        ax.scatter(
            row.median_N,
            row.median_D,
            s=110,
            marker=marker,
            facecolors="white",
            edgecolors=color,
            linewidths=1.8,
            zorder=5,
        )

    # Draw significance boundaries last so they sit on top of the point cloud.
    xaxis_text_transform = blended_transform_factory(ax.transData, ax.transAxes)
    for z, label, style in [
        (1.6448536269514722, "p=.10", ":"),
        (1.96, "p=.05", "--"),
        (2.5758293035489004, "p=.01", "-."),
    ]:
        ax.plot(
            xs,
            2 * z / np.sqrt(xs),
            style,
            color="#444444",
            linewidth=3.0,
            alpha=1.0,
            zorder=11,
        )
        x_intercept = min(x_max_plot, max(x_min_plot, (2 * z / y_min_plot) ** 2))
        ax.text(
            min(x_max_plot * 0.995, x_intercept * 1.015),
            -0.014,
            label,
            color="#444444",
            fontsize=9,
            ha="right",
            va="top",
            rotation=45,
            rotation_mode="anchor",
            transform=xaxis_text_transform,
            clip_on=False,
            zorder=12,
        )

    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlim(x_min_plot, x_max_plot)
    ax.set_ylim(y_min_plot, y_max_plot)
    x_ticks = [10, 100, 1_000, 10_000, 100_000]
    y_ticks = [0.02, 0.05, 0.1, 0.2, 0.5, 1, 2, 5]
    ax.xaxis.set_major_locator(FixedLocator(x_ticks))
    ax.xaxis.set_major_formatter(FixedFormatter(["10", "100", "1k", "10k", "100k"]))
    ax.xaxis.set_minor_formatter(NullFormatter())
    ax.yaxis.set_major_locator(FixedLocator(y_ticks))
    ax.yaxis.set_major_formatter(FixedFormatter(["0.02", "0.05", "0.1", "0.2", "0.5", "1", "2", "5"]))
    ax.yaxis.set_minor_formatter(NullFormatter())
    ax.set_xlabel("Sample size N (paper median, log scale)")
    ax.set_ylabel("Effect size D (paper median, log scale)")
    ax.set_title(
        "The Small N and Huge Effect Sizes of Published Journal Articles",
        fontsize=15,
        fontweight="bold",
        pad=28,
    )
    ax.annotate(
        (
            f"{len(main):,} papers from {n_fields} fields | "
            f"Sig. {overall_sig:.0f}% (p≤.10) | "
            f"median D = {overall_median_d:.2f}"
        ),
        xy=(0.5, 1.0),
        xycoords="axes fraction",
        xytext=(0, 2),
        textcoords="offset points",
        ha="center",
        va="bottom",
        fontsize=13,
        color="#333333",
    )
    legend_rows = field_fit.sort_values(["pct_above_p10", "n_papers"], ascending=[False, False])
    legend_handles = [
        Line2D(
            [0],
            [0],
            marker=markers.get(field_group, "o"),
            color="none",
            markerfacecolor=colors[field_group],
            markeredgecolor="none",
            markersize=8,
            alpha=0.8,
            label=f"{field_group} (n={n_papers:,}, Sig. {pct_above_p10:.0f}%)",
        )
        for field_group, n_papers, pct_above_p10 in legend_rows[
            ["field_group", "n_papers", "pct_above_p10"]
        ].itertuples(index=False)
    ]
    legend_handles.append(
        Line2D(
            [0],
            [0],
            marker="o",
            color="none",
            markerfacecolor="white",
            markeredgecolor="#333333",
            markeredgewidth=1.6,
            markersize=8,
            label="Hollow marker = field median",
        )
    )
    ax.legend(
        handles=legend_handles,
        loc="upper right",
        frameon=False,
        fontsize=10,
        borderpad=0.2,
        handletextpad=0.5,
        labelspacing=0.45,
    )
    ax.text(
        0.01,
        -0.13,
        (
            "Published-original candidate papers only. "
            "Fields are collapsed from raw tags; small categories are merged."
        ),
        transform=ax.transAxes,
        fontsize=9,
        color="#333333",
        ha="left",
    )
    ax.grid(True, which="major", alpha=0.18, linestyle=":")
    ax.grid(True, which="minor", alpha=0.06, linestyle=":")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    fig.savefig(out_dir / "candidate_published_paper_d_vs_n.png", dpi=200)
    plt.close(fig)


def write_summary(slopes: pd.DataFrame, out_dir: Path) -> None:
    top = slopes[
        (slopes["level"].eq("paper"))
        & (slopes["subset"].eq("published_original_candidates"))
        & (slopes["n"] >= 10)
    ].sort_values("slope")
    lines = [
        "# Candidate D-vs-N Slopes",
        "",
        "Log-log model: `log10(D) ~ log10(N)`. Slopes near -0.5 are the boundary-hugging pattern from the current paper figure.",
        "",
        "## Published Original Candidates, Paper Level",
        "",
        top[
            [
                "source_corpus",
                "field",
                "n",
                "slope",
                "slope_se",
                "r_squared",
                "median_D",
                "median_N",
            ]
        ].to_markdown(index=False, floatfmt=".4g"),
        "",
        "## Notes",
        "",
        "- Paper-level slopes are more comparable to the current statcheck/economics figure.",
        "- Row-level slopes are also written to CSV, but they overweight many-test papers and dense catalogs.",
        "- Szucs is absent from paper-level results until its MATLAB journal/paper grouping is decoded.",
    ]
    (out_dir / "candidate_d_n_slopes.md").write_text("\n".join(lines) + "\n")


def write_p10_report(papers: pd.DataFrame, slopes: pd.DataFrame, derived_dir: Path) -> None:
    main = papers[papers["published_original_candidate"] & ~papers["comparator_only"]].copy()
    if main.empty:
        return
    z10 = 1.6448536269514722
    main["above_p10"] = main["D_median"] >= 2 * z10 / np.sqrt(main["N_median"])
    p10 = (
        main.groupby(["source_corpus", "field", "source_kind", "published_scope"], dropna=False)
        .agg(
            pct_above_p10=("above_p10", lambda x: 100 * x.mean()),
            median_D=("D_median", "median"),
            median_N=("N_median", "median"),
        )
        .reset_index()
    )
    slope_bits = slopes[
        (slopes["level"].eq("paper")) & (slopes["subset"].eq("published_original_candidates"))
    ][["source_corpus", "field", "source_kind", "published_scope", "n", "slope", "slope_se", "r_squared"]]
    out = slope_bits.merge(p10, on=["source_corpus", "field", "source_kind", "published_scope"], how="left")
    out = out.sort_values(["n", "source_corpus"], ascending=[False, True])
    out.to_csv(derived_dir / "candidate_d_n_published_p10_report.csv", index=False)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--derived-dir", type=Path, default=Path("data/derived/corpus_candidates"))
    parser.add_argument("--report-dir", type=Path, default=Path("reports/corpus_candidates"))
    args = parser.parse_args()
    ensure_dir(args.report_dir)

    rows = pd.read_parquet(args.derived_dir / "candidate_d_n_rows.parquet")
    papers = pd.read_parquet(args.derived_dir / "candidate_d_n_papers.parquet")
    slopes = slope_tables(rows, papers)
    slopes.to_csv(args.derived_dir / "candidate_d_n_loglog_slopes.csv", index=False)
    slopes.to_csv(args.report_dir / "candidate_d_n_loglog_slopes.csv", index=False)
    write_p10_report(papers, slopes, args.derived_dir)
    write_summary(slopes, args.report_dir)
    plot_main_papers(papers, args.report_dir, args.derived_dir)
    print(f"Wrote slope analysis to {args.report_dir}")


if __name__ == "__main__":
    main()
