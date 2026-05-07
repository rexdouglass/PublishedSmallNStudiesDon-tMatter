#!/usr/bin/env python3
"""Build working Figure 1 review assets for the HTML manuscript.

This is a projection layer only. It reads the current root Figure 1 pair table
and the local coverage-accounting TSVs, writes PNGs under docs/_generated, and
materializes a small Quarto fragment included by docs/index.qmd.
"""

from __future__ import annotations

import math
import re
import shutil
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import gaussian_kde, norm


ROOT = Path(__file__).resolve().parents[1]
DOCS_DIR = ROOT / "docs"
FIG_DIR = DOCS_DIR / "_generated" / "figures"
FRAGMENT_OUT = DOCS_DIR / "_generated" / "figure1_replication_review.qmd"
DATASET_DERIVED = ROOT / "data" / "derived" / "effect_inflation_dataset"
PLOT1_CRITERIA_QMD = DOCS_DIR / "_generated" / "plot1_replication_criteria.qmd"
PLOT1_SOURCES_QMD = DOCS_DIR / "_generated" / "plot1_replication_sources.qmd"
DATASET_AUDIT_QMD = DOCS_DIR / "_generated" / "dataset_audit_snapshot.qmd"

ROOT_TABLE = ROOT / "FIGURE1_REPLICATION_PAIRS.tsv"
UNIVERSE_SUMMARY = (
    ROOT
    / "steps"
    / "corpus_results"
    / "figure1"
    / "universe_coverage"
    / "figure1-universe-coverage-summary.tsv"
)
UNIVERSE_PANELS = (
    ROOT
    / "steps"
    / "corpus_results"
    / "figure1"
    / "universe_coverage"
    / "figure1-universe-coverage-panels.png"
)
ROW_DISPOSITION = (
    ROOT
    / "steps"
    / "corpus_results"
    / "figure1"
    / "coverage_loss_accounting"
    / "figure1-row-disposition.tsv"
)
COVERAGE_BARS = (
    ROOT
    / "steps"
    / "corpus_results"
    / "figure1"
    / "coverage_loss_accounting"
    / "figure1-coverage-loss-bars.png"
)

STRICT_FIG = FIG_DIR / "figure1a_strict_current_d_pairs.png"
STRICT_APPROX_CI_FIG = FIG_DIR / "figure1a_strict_current_d_pairs_approx_ci.png"
STRICT_CI_COMPAT_FIG = FIG_DIR / "figure1a_original_ci_replication_compatibility.png"
STRICT_CI_DENSITY_FIG = FIG_DIR / "figure1a_original_ci_replication_density_standalone.png"
ALT_PANELS_FIG = FIG_DIR / "figure1bc_alternative_route_subplots.png"
COVERAGE_FIG = FIG_DIR / "figure1_coverage_loss_bars.png"
STRICT_APPROX_CI_TSV = DATASET_DERIVED / "figure1_strict_pairs_approx_ci.tsv"
STRICT_CI_COMPAT_TSV = DATASET_DERIVED / "figure1_strict_pairs_original_ci_compatibility.tsv"


def read_strict_rows() -> pd.DataFrame:
    if not ROOT_TABLE.exists():
        raise FileNotFoundError(ROOT_TABLE)
    df = pd.read_csv(ROOT_TABLE, sep="\t")
    strict = df.loc[df["current_plot_rule_status"].eq("included_by_current_figure1_dn_rule")].copy()
    for col in ["D_original", "D_replication", "N_original", "N_replication"]:
        strict[col] = pd.to_numeric(strict[col], errors="coerce")
    strict = strict.dropna(subset=["D_original", "D_replication", "N_original", "N_replication"])
    strict = strict.loc[
        np.isfinite(strict["D_original"])
        & np.isfinite(strict["D_replication"])
        & np.isfinite(strict["N_original"])
        & np.isfinite(strict["N_replication"])
    ].copy()
    return strict


def row_count(summary: pd.DataFrame, bucket: str) -> int:
    rows = summary.loc[summary["bucket"].eq(bucket)]
    if rows.empty:
        return 0
    return int(rows["rows"].iloc[0])


def pct(numerator: float, denominator: float) -> float:
    if denominator == 0:
        return 0.0
    return round(100.0 * float(numerator) / float(denominator), 1)


def add_strict_scatter_inset(parent_ax: plt.Axes, strict: pd.DataFrame) -> None:
    needed = {"D_original", "D_replication"}
    if not needed.issubset(strict.columns):
        return

    x = pd.to_numeric(strict["D_original"], errors="coerce")
    y = pd.to_numeric(strict["D_replication"], errors="coerce")
    mask = np.isfinite(x) & np.isfinite(y)
    x = x[mask]
    y = y[mask]
    if x.empty or y.empty:
        return

    max_axis = float(np.nanmax([x.max(), y.max(), 0.01]))
    max_axis = min(max(max_axis * 1.08, 2.5), 30.0)
    inset = parent_ax.inset_axes([0.61, 0.32, 0.46, 0.46])
    inset.set_facecolor((1, 1, 1, 0.92))
    for spine in inset.spines.values():
        spine.set_color("#CBD5E1")
        spine.set_linewidth(0.9)
    inset.scatter(x, y, s=4.4, alpha=0.16, color="#2F6F9F", edgecolors="none")
    inset.plot([0, max_axis], [0, max_axis], color="#444444", linestyle="--", linewidth=0.9)
    inset.set_xscale("symlog", linthresh=0.01, linscale=0.5)
    inset.set_yscale("symlog", linthresh=0.01, linscale=0.5)
    inset.set_xlim(0, max_axis)
    inset.set_ylim(0, max_axis)
    inset.set_box_aspect(1)
    inset.set_xticks([0, 0.1, 1, 10])
    inset.set_yticks([0, 0.1, 1, 10])
    inset.set_xticklabels(["0", ".1", "1", "10"], fontsize=8.4)
    inset.set_yticklabels(["0", ".1", "1", "10"], fontsize=8.4)
    inset.tick_params(length=2.8, pad=1.5)
    inset.grid(True, which="major", color="#E2E8F0", linewidth=0.5)
    inset.set_xlabel("Original D", fontsize=9.8, labelpad=1.0)
    inset.set_ylabel("Replication D", fontsize=9.8, labelpad=1.0)


def draw_strict_figure(strict: pd.DataFrame) -> dict[str, float | int]:
    FIG_DIR.mkdir(parents=True, exist_ok=True)

    plot_df = strict.copy()
    max_axis = float(np.nanmax([plot_df["D_original"].max(), plot_df["D_replication"].max(), 0.01]))
    max_axis = min(max(max_axis * 1.08, 2.5), 30.0)

    shrink = plot_df["D_replication"] < plot_df["D_original"]
    with np.errstate(divide="ignore", invalid="ignore"):
        ratio = plot_df["D_replication"] / plot_df["D_original"].replace(0, np.nan)
        n_ratio = plot_df["N_replication"] / plot_df["N_original"].replace(0, np.nan)
        p05_boundary = 2.0 * 1.96 / np.sqrt(plot_df["N_replication"])
    below_p05 = plot_df["D_replication"] < p05_boundary

    fig, ax = plt.subplots(figsize=(8.2, 7.1))
    ax.scatter(
        plot_df["D_original"],
        plot_df["D_replication"],
        s=14,
        alpha=0.28,
        color="#2F6F9F",
        edgecolors="none",
    )
    ax.plot([0, max_axis], [0, max_axis], color="#444444", linestyle="--", linewidth=1.3)
    ax.set_xscale("symlog", linthresh=0.01, linscale=0.5)
    ax.set_yscale("symlog", linthresh=0.01, linscale=0.5)
    ax.set_xlim(0, max_axis)
    ax.set_ylim(0, max_axis)
    ticks = [0, 0.01, 0.03, 0.1, 0.3, 1, 3, 10, 30]
    ticks = [tick for tick in ticks if tick <= max_axis]
    ax.set_xticks(ticks)
    ax.set_yticks(ticks)
    ax.set_xticklabels(["0" if tick == 0 else f"{tick:g}" for tick in ticks])
    ax.set_yticklabels(["0" if tick == 0 else f"{tick:g}" for tick in ticks])
    ax.grid(True, which="major", color="#E2E8F0", linewidth=0.8)
    ax.grid(True, which="minor", color="#EEF2F7", linewidth=0.4)
    ax.set_xlabel("Original effect magnitude D")
    ax.set_ylabel("Replication/follow-up effect magnitude D")
    ax.set_title("Figure 1A. Strict current D/N replication pairs")
    metric_text = (
        f"n = {len(plot_df):,}\n"
        f"{pct(shrink.sum(), len(plot_df)):.1f}% smaller in follow-up\n"
        f"{pct(below_p05.sum(), len(plot_df)):.1f}% below p < .05 boundary\n"
        f"median D ratio = {np.nanmedian(ratio):.2f}\n"
        f"median N ratio = {np.nanmedian(n_ratio):.1f}x"
    )
    ax.text(
        0.03,
        0.97,
        metric_text,
        transform=ax.transAxes,
        va="top",
        ha="left",
        fontsize=10,
        bbox={"facecolor": "white", "edgecolor": "#CBD5E1", "alpha": 0.86, "pad": 6},
    )
    fig.tight_layout()
    fig.savefig(STRICT_FIG, dpi=220, bbox_inches="tight")
    plt.close(fig)

    return {
        "n_pairs": int(len(plot_df)),
        "pct_smaller": pct(shrink.sum(), len(plot_df)),
        "pct_below_p05_boundary": pct(below_p05.sum(), len(plot_df)),
        "median_d_original": float(plot_df["D_original"].median()),
        "median_d_replication": float(plot_df["D_replication"].median()),
        "median_n_original": float(plot_df["N_original"].median()),
        "median_n_replication": float(plot_df["N_replication"].median()),
        "median_d_ratio": float(np.nanmedian(ratio)),
        "median_n_ratio": float(np.nanmedian(n_ratio)),
    }


def approximate_d_ci(strict: pd.DataFrame) -> pd.DataFrame:
    out = strict.copy()
    for side in ["original", "replication"]:
        d = pd.to_numeric(out[f"D_{side}"], errors="coerce")
        n = pd.to_numeric(out[f"N_{side}"], errors="coerce")
        se = np.sqrt((4.0 / n) + ((d * d) / (2.0 * (n - 2.0))))
        out[f"D_{side}_approx_se_equal_arm"] = se
        out[f"D_{side}_approx_ci95_low_equal_arm"] = d - 1.96 * se
        out[f"D_{side}_approx_ci95_high_equal_arm"] = d + 1.96 * se
    original_low = out["D_original_approx_ci95_low_equal_arm"]
    original_high = out["D_original_approx_ci95_high_equal_arm"]
    original_half_width = (original_high - original_low) / 2.0
    replication_d = out["D_replication"]
    replication_se = out["D_replication_approx_se_equal_arm"]
    original_d = out["D_original"]
    original_se = out["D_original_approx_se_equal_arm"]
    predictive_se = np.sqrt((original_se * original_se) + (replication_se * replication_se))

    out["replication_vs_original_ci_direction"] = np.select(
        [replication_d < original_low, replication_d > original_high],
        ["below_original_ci", "above_original_ci"],
        default="inside_original_ci",
    )
    out["replication_signed_gap_to_original_ci"] = np.select(
        [replication_d < original_low, replication_d > original_high],
        [replication_d - original_low, replication_d - original_high],
        default=0.0,
    )
    out["replication_signed_gap_in_original_ci_half_widths"] = (
        out["replication_signed_gap_to_original_ci"] / original_half_width.replace(0, np.nan)
    )
    out["replication_delta_in_original_ci_half_widths"] = (
        (replication_d - original_d) / original_half_width.replace(0, np.nan)
    )
    out["compatibility_predictive_se_in_original_ci_half_widths"] = (
        predictive_se / original_half_width.replace(0, np.nan)
    )
    out["replication_delta_combined_se_z"] = (replication_d - original_d) / predictive_se.replace(0, np.nan)
    out["expected_probability_inside_original_ci_under_common_effect"] = norm.cdf(
        (original_high - original_d) / predictive_se
    ) - norm.cdf((original_low - original_d) / predictive_se)
    out["replication_probability_mass_inside_original_ci"] = norm.cdf((original_high - replication_d) / replication_se) - norm.cdf(
        (original_low - replication_d) / replication_se
    )

    keep = [
        "figure1_replication_pair_id",
        "source_family_label",
        "source_dataset",
        "original_title",
        "replication_title",
        "outcome_label",
        "D_original",
        "N_original",
        "D_original_approx_se_equal_arm",
        "D_original_approx_ci95_low_equal_arm",
        "D_original_approx_ci95_high_equal_arm",
        "D_replication",
        "N_replication",
        "D_replication_approx_se_equal_arm",
        "D_replication_approx_ci95_low_equal_arm",
        "D_replication_approx_ci95_high_equal_arm",
        "replication_vs_original_ci_direction",
        "replication_signed_gap_to_original_ci",
        "replication_signed_gap_in_original_ci_half_widths",
        "replication_delta_in_original_ci_half_widths",
        "compatibility_predictive_se_in_original_ci_half_widths",
        "replication_delta_combined_se_z",
        "expected_probability_inside_original_ci_under_common_effect",
        "replication_probability_mass_inside_original_ci",
        "current_plot_rule_status",
    ]
    keep = [col for col in keep if col in out.columns]
    DATASET_DERIVED.mkdir(parents=True, exist_ok=True)
    out[keep].to_csv(STRICT_APPROX_CI_TSV, sep="\t", index=False)
    out[keep].to_csv(STRICT_CI_COMPAT_TSV, sep="\t", index=False)
    return out


def draw_approx_ci_figure(strict_ci: pd.DataFrame) -> None:
    plot_df = strict_ci.copy()
    x = pd.to_numeric(plot_df["D_original"], errors="coerce")
    y = pd.to_numeric(plot_df["D_replication"], errors="coerce")
    xlo = pd.to_numeric(plot_df["D_original_approx_ci95_low_equal_arm"], errors="coerce")
    xhi = pd.to_numeric(plot_df["D_original_approx_ci95_high_equal_arm"], errors="coerce")
    ylo = pd.to_numeric(plot_df["D_replication_approx_ci95_low_equal_arm"], errors="coerce")
    yhi = pd.to_numeric(plot_df["D_replication_approx_ci95_high_equal_arm"], errors="coerce")
    mask = np.isfinite(x) & np.isfinite(y) & np.isfinite(xlo) & np.isfinite(xhi) & np.isfinite(ylo) & np.isfinite(yhi)
    x, y, xlo, xhi, ylo, yhi = x[mask], y[mask], xlo[mask], xhi[mask], ylo[mask], yhi[mask]

    fig, ax = plt.subplots(figsize=(8.2, 7.1))
    xerr = np.vstack([(x - xlo).clip(lower=0), (xhi - x).clip(lower=0)])
    yerr = np.vstack([(y - ylo).clip(lower=0), (yhi - y).clip(lower=0)])
    ax.errorbar(
        x,
        y,
        xerr=xerr,
        yerr=yerr,
        fmt="none",
        ecolor="#64748B",
        elinewidth=0.45,
        alpha=0.085,
        zorder=1,
    )
    ax.scatter(x, y, s=10, alpha=0.30, color="#2F6F9F", edgecolors="none", zorder=2)
    axis_min = -0.75
    axis_max = min(max(float(np.nanmax([xhi.max(), yhi.max(), 3.0])) * 1.03, 3.0), 30.0)
    ax.plot([0, axis_max], [0, axis_max], color="#444444", linestyle="--", linewidth=1.2, zorder=3)
    ax.axhline(0, color="#94A3B8", linewidth=0.8)
    ax.axvline(0, color="#94A3B8", linewidth=0.8)
    ax.set_xscale("symlog", linthresh=0.1, linscale=0.8)
    ax.set_yscale("symlog", linthresh=0.1, linscale=0.8)
    ax.set_xlim(axis_min, axis_max)
    ax.set_ylim(axis_min, axis_max)
    ticks = [-0.5, 0, 0.1, 0.3, 1, 3, 10, 30]
    ticks = [tick for tick in ticks if axis_min <= tick <= axis_max]
    ax.set_xticks(ticks)
    ax.set_yticks(ticks)
    ax.set_xticklabels([f"{tick:g}" for tick in ticks])
    ax.set_yticklabels([f"{tick:g}" for tick in ticks])
    ax.grid(True, which="major", color="#E2E8F0", linewidth=0.8)
    ax.set_xlabel("Original effect magnitude D with approximate 95% CI")
    ax.set_ylabel("Replication/follow-up effect magnitude D with approximate 95% CI")
    ax.set_title("Figure 1A CI diagnostic: modeled uncertainty from D and N")
    med_orig = float(np.nanmedian(1.96 * pd.to_numeric(plot_df["D_original_approx_se_equal_arm"], errors="coerce")))
    med_rep = float(np.nanmedian(1.96 * pd.to_numeric(plot_df["D_replication_approx_se_equal_arm"], errors="coerce")))
    ax.text(
        0.03,
        0.97,
        f"n = {len(x):,}\nmedian original half-width = {med_orig:.2f}\nmedian replication half-width = {med_rep:.2f}\nnot source-reported CIs",
        transform=ax.transAxes,
        va="top",
        ha="left",
        fontsize=10,
        bbox={"facecolor": "white", "edgecolor": "#CBD5E1", "alpha": 0.88, "pad": 6},
    )
    fig.tight_layout()
    fig.savefig(STRICT_APPROX_CI_FIG, dpi=220, bbox_inches="tight")
    plt.close(fig)


def draw_original_ci_compatibility_figure(strict_ci: pd.DataFrame) -> None:
    df = strict_ci.copy()
    direction_order = ["below_original_ci", "inside_original_ci", "above_original_ci"]
    direction_labels = {
        "below_original_ci": "Below original CI",
        "inside_original_ci": "Inside original CI",
        "above_original_ci": "Above original CI",
    }
    direction_colors = {
        "below_original_ci": "#B94840",
        "inside_original_ci": "#2D8B7D",
        "above_original_ci": "#C8741F",
    }
    counts = df["replication_vs_original_ci_direction"].value_counts().reindex(direction_order, fill_value=0)
    percentages = counts / len(df) * 100.0

    delta_ci_units = pd.to_numeric(df["replication_delta_in_original_ci_half_widths"], errors="coerce")
    delta_ci_units = delta_ci_units[np.isfinite(delta_ci_units)]
    predictive_sigma_units = pd.to_numeric(
        df["compatibility_predictive_se_in_original_ci_half_widths"], errors="coerce"
    )
    predictive_sigma_units = predictive_sigma_units[
        np.isfinite(predictive_sigma_units) & (predictive_sigma_units > 0)
    ]
    prob_inside = pd.to_numeric(df["replication_probability_mass_inside_original_ci"], errors="coerce")
    prob_inside = prob_inside[np.isfinite(prob_inside)].clip(lower=0, upper=1)

    top_sources = df["source_family_label"].fillna("Unknown").value_counts().head(10).index.tolist()
    source_df = df.loc[df["source_family_label"].isin(top_sources)].copy()
    source_counts = (
        source_df.groupby(["source_family_label", "replication_vs_original_ci_direction"])
        .size()
        .unstack(fill_value=0)
        .reindex(columns=direction_order, fill_value=0)
    )
    source_pct = source_counts.div(source_counts.sum(axis=1), axis=0).sort_values("below_original_ci", ascending=True)

    fig, axes = plt.subplots(2, 2, figsize=(12.5, 8.8))
    ax_a, ax_b, ax_c, ax_d = axes.flatten()

    # Panel A: overall counts.
    bottom = 0
    for direction in direction_order:
        ax_a.barh(
            ["All strict rows"],
            [percentages[direction]],
            left=bottom,
            color=direction_colors[direction],
            label=direction_labels[direction],
        )
        if percentages[direction] >= 5:
            ax_a.text(
                bottom + percentages[direction] / 2,
                0,
                f"{counts[direction]:,}\n{percentages[direction]:.0f}%",
                ha="center",
                va="center",
                color="white",
                fontsize=10,
                fontweight="bold",
            )
        bottom += percentages[direction]
    ax_a.set_xlim(0, 100)
    ax_a.set_xlabel("Percent of strict rows")
    ax_a.set_title("A. Replication point estimate vs original 95% CI")
    ax_a.legend(frameon=False, loc="lower center", bbox_to_anchor=(0.5, -0.38), ncol=3, fontsize=8)

    # Panel B: observed replication locations against the predictive density implied by modeled CIs.
    grid = np.linspace(-5, 5, 500)
    expected_density = np.zeros_like(grid)
    sigma_values = predictive_sigma_units.to_numpy(dtype=float)
    if len(sigma_values):
        # Mixture of row-specific predictive normals under the common-effect compatibility model.
        for chunk in np.array_split(sigma_values, max(1, math.ceil(len(sigma_values) / 250))):
            expected_density += norm.pdf(grid[:, None], loc=0.0, scale=chunk).mean(axis=1) * (len(chunk) / len(sigma_values))
    observed_in_view = delta_ci_units.loc[delta_ci_units.between(-5, 5)]
    bins = np.linspace(-5, 5, 51)
    ax_b.hist(
        observed_in_view,
        bins=bins,
        density=True,
        color="#5B7FA6",
        alpha=0.26,
        label="Observed replications",
    )
    if len(observed_in_view) > 1 and observed_in_view.nunique() > 1:
        kde = gaussian_kde(observed_in_view.to_numpy(dtype=float))
        ax_b.plot(grid, kde(grid), color="#234E70", linewidth=2.0, label="Observed density")
    if len(sigma_values):
        ax_b.plot(grid, expected_density, color="#C8741F", linewidth=2.0, label="Compatibility-implied density")
    ax_b.axvspan(-1, 1, color="#2D8B7D", alpha=0.08, label="Original 95% CI")
    ax_b.axvline(-1, color="#333333", linestyle="--", linewidth=1.0)
    ax_b.axvline(1, color="#333333", linestyle="--", linewidth=1.0)
    ax_b.axvline(0, color="#333333", linestyle=":", linewidth=1.0)
    ax_b.set_xlabel("Replication location in original-CI half-widths")
    ax_b.set_ylabel("Density")
    ax_b.set_title("B. Empirical vs compatibility-implied distribution")
    outside_view = len(delta_ci_units) - len(observed_in_view)
    panel_b_note = "-1 to +1 = inside original CI\nnegative = smaller than original\norange = expected if compatible"
    if outside_view:
        panel_b_note += f"\n{outside_view:,} rows outside shown range"
    ax_b.text(
        0.03,
        0.96,
        panel_b_note,
        transform=ax_b.transAxes,
        va="top",
        fontsize=9,
        bbox={"facecolor": "white", "edgecolor": "#CBD5E1", "alpha": 0.86, "pad": 5},
    )
    ax_b.legend(frameon=False, loc="lower right", fontsize=8)

    # Panel C: probability mass inside original CI.
    ax_c.hist(prob_inside, bins=np.linspace(0, 1, 41), color="#6B5CA5", alpha=0.85)
    ax_c.axvline(float(np.nanmedian(prob_inside)), color="#333333", linestyle="--", linewidth=1.2)
    ax_c.set_xlabel("Replication probability mass inside original CI")
    ax_c.set_ylabel("Rows")
    ax_c.set_title("C. Modeled overlap probability")
    ax_c.text(
        0.97,
        0.94,
        f"median = {np.nanmedian(prob_inside):.2f}",
        transform=ax_c.transAxes,
        ha="right",
        va="top",
        fontsize=10,
        bbox={"facecolor": "white", "edgecolor": "#CBD5E1", "alpha": 0.86, "pad": 5},
    )

    # Panel D: top source families.
    left = np.zeros(len(source_pct))
    y = np.arange(len(source_pct))
    labels = [label[:36] + ("..." if len(label) > 36 else "") for label in source_pct.index]
    for direction in direction_order:
        vals = source_pct[direction].to_numpy(dtype=float) * 100.0
        ax_d.barh(y, vals, left=left, color=direction_colors[direction], label=direction_labels[direction])
        left += vals
    ax_d.set_yticks(y)
    ax_d.set_yticklabels(labels, fontsize=8)
    ax_d.set_xlim(0, 100)
    ax_d.set_xlabel("Percent of rows in source family")
    ax_d.set_title("D. Same classification by largest source families")

    fig.suptitle("Original-CI / Replication Compatibility Diagnostic", fontsize=15)
    fig.tight_layout(rect=[0, 0, 1, 0.96])
    fig.savefig(STRICT_CI_COMPAT_FIG, dpi=220, bbox_inches="tight")
    plt.close(fig)


def draw_original_ci_density_standalone(strict_ci: pd.DataFrame) -> None:
    df = strict_ci.copy()
    delta_ci_units = pd.to_numeric(df["replication_delta_in_original_ci_half_widths"], errors="coerce")
    delta_ci_units = delta_ci_units[np.isfinite(delta_ci_units)]
    predictive_sigma_units = pd.to_numeric(
        df["compatibility_predictive_se_in_original_ci_half_widths"], errors="coerce"
    )
    predictive_sigma_units = predictive_sigma_units[
        np.isfinite(predictive_sigma_units) & (predictive_sigma_units > 0)
    ]
    direction_counts = df["replication_vs_original_ci_direction"].value_counts()
    below = int(direction_counts.get("below_original_ci", 0))
    inside = int(direction_counts.get("inside_original_ci", 0))
    above = int(direction_counts.get("above_original_ci", 0))

    grid = np.linspace(-4, 4, 800)
    expected_density = np.zeros_like(grid)
    sigma_values = predictive_sigma_units.to_numpy(dtype=float)
    if len(sigma_values):
        for chunk in np.array_split(sigma_values, max(1, math.ceil(len(sigma_values) / 250))):
            expected_density += norm.pdf(grid[:, None], loc=0.0, scale=chunk).mean(axis=1) * (len(chunk) / len(sigma_values))
    if len(sigma_values):
        rng = np.random.default_rng(20260504)
        component_sigmas = rng.choice(sigma_values, size=250_000, replace=True)
        implied_samples = rng.normal(loc=0.0, scale=component_sigmas)
        implied_tail_low, implied_tail_high = np.quantile(implied_samples, [0.025, 0.975])
    else:
        implied_tail_low, implied_tail_high = np.nan, np.nan

    observed_in_view = delta_ci_units.loc[delta_ci_units.between(-4, 4)]
    outside_view = len(delta_ci_units) - len(observed_in_view)
    observed_median = float(np.nanmedian(delta_ci_units)) if len(delta_ci_units) else float("nan")
    expected_inside = pd.to_numeric(
        df["expected_probability_inside_original_ci_under_common_effect"], errors="coerce"
    )
    expected_inside = expected_inside[np.isfinite(expected_inside)]
    observed_inside_rate = inside / len(delta_ci_units) if len(delta_ci_units) else float("nan")
    expected_inside_rate = float(np.nanmean(expected_inside)) if len(expected_inside) else float("nan")
    observed_left_tail_rate = (
        float(np.mean(delta_ci_units <= implied_tail_low))
        if len(delta_ci_units) and np.isfinite(implied_tail_low)
        else float("nan")
    )

    fig, ax = plt.subplots(figsize=(8.2, 5.3))
    observed_density = np.full_like(grid, np.nan, dtype=float)
    if len(observed_in_view) > 1 and observed_in_view.nunique() > 1:
        kde = gaussian_kde(observed_in_view.to_numpy(dtype=float))
        observed_density = kde(grid)
        observed_median_height = float(kde(observed_median)[0]) if np.isfinite(observed_median) else 0.0
        ax.plot(grid, observed_density, color="#234E70", linewidth=2.9, zorder=4)
        ax.vlines(
            observed_median,
            0,
            observed_median_height,
            color="#234E70",
            linestyle="-.",
            linewidth=1.35,
            alpha=0.95,
            zorder=5,
        )
    if len(sigma_values):
        implied_center_height = float(np.interp(0.0, grid, expected_density))
        low_tail = grid <= implied_tail_low
        high_tail = grid >= implied_tail_high
        ax.fill_between(
            grid[low_tail],
            0,
            expected_density[low_tail],
            color="#C8741F",
            alpha=0.18,
            linewidth=0,
            zorder=1,
        )
        ax.fill_between(
            grid[high_tail],
            0,
            expected_density[high_tail],
            color="#C8741F",
            alpha=0.18,
            linewidth=0,
            zorder=1,
        )
        observed_left_tail_excess = (
            np.isfinite(observed_density)
            & (grid <= implied_tail_low)
            & (observed_density > expected_density)
        )
        if np.any(observed_left_tail_excess):
            ax.fill_between(
                grid,
                expected_density,
                observed_density,
                where=observed_left_tail_excess,
                interpolate=True,
                color="#234E70",
                alpha=0.18,
                linewidth=0,
                zorder=2,
            )
        ax.plot(grid, expected_density, color="#C8741F", linewidth=2.9, zorder=4)
        ax.vlines(
            [implied_tail_low, implied_tail_high],
            0,
            np.interp([implied_tail_low, implied_tail_high], grid, expected_density),
            color="#C8741F",
            linestyle=":",
            linewidth=1.05,
            alpha=0.8,
            zorder=5,
        )
        ax.vlines(
            0,
            0,
            implied_center_height,
            color="#C8741F",
            linestyle=":",
            linewidth=1.35,
            alpha=0.95,
            zorder=5,
        )

    ax.set_xlim(-4, 4)
    ax.set_ylim(bottom=0)
    ax.set_xlabel("Replication location relative to original 95% CI (original-CI half-width units)")
    ax.set_ylabel("Density (area = 1)")
    title = "Published Confidence Intervals Systematically Overstate Coverage and Symmetry"
    subtitle = (
        f"n = {len(delta_ci_units):,} replications; "
        f"{observed_inside_rate:.0%} inside interval vs {expected_inside_rate:.0%} expected; "
        f"median shift = {observed_median:.2f} half-widths"
    )
    fig.text(0.5, 0.975, title, ha="center", va="top", fontsize=13.2, fontweight="bold")
    fig.text(0.5, 0.925, subtitle, ha="center", va="top", fontsize=10.5)
    ax.grid(axis="y", color="#E2E8F0", linewidth=0.8)
    ax.spines[["top", "right"]].set_visible(False)

    ax.text(
        -2.55,
        0.56,
        "Actual replications",
        color="#234E70",
        fontsize=12.2,
        fontweight="bold",
    )
    ax.text(
        0.48,
        0.655,
        "Implied confidence intervals",
        color="#C8741F",
        fontsize=12.2,
        fontweight="bold",
    )
    if np.isfinite(observed_left_tail_rate):
        ax.text(
            -3.82,
            0.105,
            f"2.5% left-tail events\noccur in {observed_left_tail_rate:.0%}\nof replications",
            color="#234E70",
            fontsize=10.2,
            fontweight="bold",
            ha="left",
            va="center",
        )
    add_strict_scatter_inset(ax, df)
    fig.tight_layout(rect=[0, 0, 1, 0.88])
    fig.savefig(STRICT_CI_DENSITY_FIG, dpi=220, bbox_inches="tight")
    plt.close(fig)


def copy_existing_figures() -> None:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    if UNIVERSE_PANELS.exists():
        shutil.copy2(UNIVERSE_PANELS, ALT_PANELS_FIG)
    if COVERAGE_BARS.exists():
        shutil.copy2(COVERAGE_BARS, COVERAGE_FIG)


def markdown_table(df: pd.DataFrame, columns: list[str], limit: int | None = None) -> str:
    if limit is not None:
        df = df.head(limit)
    if df.empty:
        return "_No rows available._"
    header = "| " + " | ".join(columns) + " |"
    sep = "| " + " | ".join(["---"] * len(columns)) + " |"
    lines = [header, sep]
    for _, row in df.iterrows():
        vals = []
        for col in columns:
            text = "" if pd.isna(row[col]) else str(row[col])
            text = text.replace("|", "\\|").replace("\n", " ")
            vals.append(text)
        lines.append("| " + " | ".join(vals) + " |")
    return "\n".join(lines)


def write_fragment(stats: dict[str, float | int]) -> None:
    summary = pd.read_csv(UNIVERSE_SUMMARY, sep="\t") if UNIVERSE_SUMMARY.exists() else pd.DataFrame()
    disposition = pd.read_csv(ROW_DISPOSITION, sep="\t") if ROW_DISPOSITION.exists() else pd.DataFrame()

    panel_total = row_count(summary, "local_observable_row_universe") if not summary.empty else 0
    accounted_total = int(pd.to_numeric(disposition.get("row_count", pd.Series(dtype=float)), errors="coerce").fillna(0).sum())
    strict = int(stats["n_pairs"])
    d_equiv = row_count(summary, "additional_comparative_binary_d_equivalent_rows") if not summary.empty else 0
    native = row_count(summary, "native_response_rate_rows_not_d_axis") if not summary.empty else 0
    blocked = row_count(summary, "strict_dn_available_but_blocked") if not summary.empty else 0

    disposition_table = ""
    if not disposition.empty:
        slim = disposition[
            [
                "disposition_label",
                "row_count",
                "usable_for",
                "has_effect",
                "has_n",
                "has_common_axis",
            ]
        ].copy()
        disposition_table = markdown_table(
            slim,
            [
                "disposition_label",
                "row_count",
                "usable_for",
                "has_effect",
                "has_n",
                "has_common_axis",
            ],
        )

    lines = [
        "## Working Figure 1 Review {.unnumbered}",
        "",
        "This temporary review block is generated from local TSV/PNG artifacts so the plotted routes can be checked in the HTML before any manuscript wording is hardened.",
        "",
        f"- Strict Figure 1A direct D/N rows: **{strict:,}**.",
        f"- Additional binary clinical D-equivalent diagnostic rows: **{d_equiv:,}**.",
        f"- Native response/logit rows retained off the D axis: **{native:,}**.",
        f"- D/N rows currently blocked from Figure 1A by a rule gate: **{blocked:,}**.",
        f"- Local row universe shown in the subplot buckets: **{panel_total:,}**.",
        f"- Full accounting denominator including parser-repair and duplicate-risk rows: **{accounted_total:,}**.",
        "",
        "<figure class=\"working-figure-review\">",
        "<img src=\"_generated/figures/figure1a_strict_current_d_pairs.png\" alt=\"Working strict Figure 1A direct D panel\" style=\"width:100%; max-width:980px; display:block; margin:auto;\">",
        "<figcaption>Working Figure 1A: strict direct-D panel. Axes use a symmetric log scale so zero-effect rows remain visible. The dashed line marks equality between original and follow-up effect magnitudes.</figcaption>",
        "</figure>",
        "",
        "<figure class=\"working-figure-review\">",
        "<img src=\"_generated/figures/figure1a_original_ci_replication_density_standalone.png\" alt=\"Standalone original confidence interval and replication compatibility density diagnostic\" style=\"width:100%; max-width:1180px; display:block; margin:auto;\">",
        "<figcaption>Standalone original-CI / replication compatibility density diagnostic. Replication point estimates are expressed in original-CI half-width units: -1 to +1 is the modeled original 95% interval and 0 is the original point estimate. The blue curve is the empirical observed density and the orange curve is the compatibility-implied predictive density from the modeled original and replication uncertainty; shaded orange regions mark the implied 2.5% tails, and blue shading marks observed excess density beyond the lower implied 95% cutoff. The inset shows the strict Figure 1A D/N scatter. These are not extracted source-reported confidence intervals.</figcaption>",
        "</figure>",
        "",
        "<figure class=\"working-figure-review\">",
        "<img src=\"_generated/figures/figure1bc_alternative_route_subplots.png\" alt=\"Working additional Figure 1 route panels\" style=\"width:100%; max-width:1180px; display:block; margin:auto;\">",
        "<figcaption>Additional Figure 1 route panels. Panel B keeps comparative binary endpoints on a D-equivalent axis; Panel C keeps response-rate rows on a native logit axis; Panel D shows local row buckets.</figcaption>",
        "</figure>",
        "",
        "<figure class=\"working-figure-review\">",
        "<img src=\"_generated/figures/figure1_coverage_loss_bars.png\" alt=\"Working Figure 1 coverage-loss accounting bars\" style=\"width:100%; max-width:980px; display:block; margin:auto;\">",
        "<figcaption>Coverage-loss accounting across strict Figure 1A, alternate diagnostic routes, repair queues, and denominator-only rows.</figcaption>",
        "</figure>",
        "",
        "### Working Route Table {.unnumbered}",
        "",
        disposition_table or "_Coverage accounting has not been generated._",
        "",
        "<hr>",
        "",
    ]
    FRAGMENT_OUT.parent.mkdir(parents=True, exist_ok=True)
    FRAGMENT_OUT.write_text("\n".join(lines), encoding="utf-8")


def patch_data_paper_plot1_fragments(strict: pd.DataFrame) -> None:
    total_root = len(pd.read_csv(ROOT_TABLE, sep="\t")) if ROOT_TABLE.exists() else len(strict)
    blocked_root = max(total_root - len(strict), 0)

    criteria_lines = [
        "## Inclusion Criteria",
        "",
        "Plot 1 / Figure 1A keeps a row in the strict direct-`D` panel when:",
        "",
        "1. the row has an original side and a follow-up/replication side with a common `D`/`Z`-convertible effect measure,",
        "2. both sides have `N`,",
        "3. both sides have `N >= 10`,",
        "4. and the follow-up/replication `N` is larger than the original `N`.",
        "",
        f"The current root table has `{total_root:,}` D/N pair rows in [FIGURE1_REPLICATION_PAIRS.tsv](../FIGURE1_REPLICATION_PAIRS.tsv). "
        f"`{len(strict):,}` rows pass the current strict Figure 1A rule and `{blocked_root:,}` D/N rows are retained for rule-audit or robustness work but excluded from the strict panel. "
        "The older `replication_pairs_figure2_rule_subset.csv` is retained as a legacy derived input, but the rendered arrows plot and current audit language now use the root table.",
        "",
        "Machine-readable route accounting: [figure1-row-disposition.tsv](../steps/corpus_results/figure1/coverage_loss_accounting/figure1-row-disposition.tsv)",
        "",
        "Machine-readable coverage summary: [figure1-universe-coverage-summary.tsv](../steps/corpus_results/figure1/universe_coverage/figure1-universe-coverage-summary.tsv)",
        "",
    ]
    PLOT1_CRITERIA_QMD.write_text("\n".join(criteria_lines), encoding="utf-8")

    if DATASET_AUDIT_QMD.exists():
        text = DATASET_AUDIT_QMD.read_text(encoding="utf-8")
        text = re.sub(
            r"- Figure 2 rule-qualified rows: `[\d,]+` in \[replication_pairs_figure2_rule_subset\.csv\]\(\.\./data/derived/replication_pairs/replication_pairs_figure2_rule_subset\.csv\)",
            f"- Current strict Figure 1A / Plot 1 rows: `{len(strict):,}` in [FIGURE1_REPLICATION_PAIRS.tsv](../FIGURE1_REPLICATION_PAIRS.tsv)",
            text,
        )
        DATASET_AUDIT_QMD.write_text(text, encoding="utf-8")

    if PLOT1_SOURCES_QMD.exists():
        text = PLOT1_SOURCES_QMD.read_text(encoding="utf-8")
        text = text.replace(
            "Machine-readable pair-level file: [plot1_replication_pair_details.csv](../data/derived/effect_inflation_dataset/plot1_replication_pair_details.csv)",
            "Machine-readable current pair-level file: [FIGURE1_REPLICATION_PAIRS.tsv](../FIGURE1_REPLICATION_PAIRS.tsv)",
        )
        text = re.sub(
            r"The specific-observation layer has `[\d,]+` Figure 2 rows\.",
            f"The current strict Plot 1 / Figure 1A layer has `{len(strict):,}` rows.",
            text,
        )
        PLOT1_SOURCES_QMD.write_text(text, encoding="utf-8")


def main() -> None:
    strict = read_strict_rows()
    strict_ci = approximate_d_ci(strict)
    stats = draw_strict_figure(strict_ci)
    draw_approx_ci_figure(strict_ci)
    draw_original_ci_compatibility_figure(strict_ci)
    draw_original_ci_density_standalone(strict_ci)
    copy_existing_figures()
    write_fragment(stats)
    patch_data_paper_plot1_fragments(strict)
    print(f"Wrote {STRICT_FIG.relative_to(ROOT)}")
    print(f"Wrote {FRAGMENT_OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
