#!/usr/bin/env python3
"""Build a published-original-paper D-vs-N corpus.

This intentionally does not use BEAR as the main source. It builds the object
we need for the paper: one row per published paper, with median absolute D and
median N from extractable tests/results.
"""

from __future__ import annotations

import argparse
import math
import re
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats


STATCHECK_URL = "https://osf.io/gdr4q/download"
BRODEUR_2024_URL = "https://dataverse.harvard.edu/api/access/datafile/7884702"


def ensure_dirs(*paths: Path) -> None:
    for path in paths:
        path.mkdir(parents=True, exist_ok=True)


def boolish(series: pd.Series) -> pd.Series:
    text = series.astype(str).str.strip().str.lower()
    return text.isin(["true", "1", "yes", "t"])


def extract_chi_n(raw: pd.Series) -> pd.Series:
    # Match common statcheck fragments like "N = 159" or "n=40".
    extracted = raw.astype(str).str.extract(r"(?i)\bN\s*=\s*([0-9][0-9,\.]*)", expand=False)
    extracted = extracted.str.replace(",", "", regex=False)
    return pd.to_numeric(extracted, errors="coerce")


def download_if_missing(path: Path, url: str) -> None:
    if path.exists() and path.stat().st_size > 0:
        return
    import subprocess

    subprocess.run(["curl", "-L", "--fail", "--retry", "3", "-o", str(path), url], check=True)


def read_statcheck(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, sep=";", decimal=",", encoding="latin1", low_memory=False)


def build_statcheck(path: Path, interim_dir: Path) -> tuple[pd.DataFrame, dict[str, object]]:
    raw = read_statcheck(path)
    df = raw.copy()
    df.columns = [c.strip() for c in df.columns]

    df["paper_id"] = "statcheck_" + df["Source"].astype(str)
    df["journal"] = df["journals.jour."].astype(str)
    df["year"] = pd.to_numeric(df["years.y."], errors="coerce")
    df["statistic"] = df["Statistic"].astype(str)
    df["value"] = pd.to_numeric(df["Value"], errors="coerce")
    df["df1_num"] = pd.to_numeric(df["df1"], errors="coerce")
    df["df2_num"] = pd.to_numeric(df["df2"], errors="coerce")
    df["error_flag"] = boolish(df["Error"])
    df["decision_error_flag"] = boolish(df["DecisionError"])

    usable = df[~df["error_flag"] & ~df["decision_error_flag"]].copy()
    usable["N"] = np.nan
    usable["D"] = np.nan
    usable["D_method"] = ""

    stat = usable["statistic"].str.lower()

    t_mask = stat.eq("t") & usable["df2_num"].notna() & usable["value"].notna()
    usable.loc[t_mask, "N"] = usable.loc[t_mask, "df2_num"] + 2
    usable.loc[t_mask, "D"] = 2 * usable.loc[t_mask, "value"].abs() / np.sqrt(usable.loc[t_mask, "df2_num"])
    usable.loc[t_mask, "D_method"] = "statcheck_t_2t_sqrt_df"

    f_mask = stat.eq("f") & usable["df1_num"].eq(1) & usable["df2_num"].notna() & usable["value"].notna()
    usable.loc[f_mask, "N"] = usable.loc[f_mask, "df2_num"] + 2
    usable.loc[f_mask, "D"] = 2 * np.sqrt(usable.loc[f_mask, "value"] / usable.loc[f_mask, "df2_num"])
    usable.loc[f_mask, "D_method"] = "statcheck_f1_2sqrt_f_over_df2"

    r_mask = stat.eq("r") & usable["df2_num"].notna() & usable["value"].notna() & (usable["value"].abs() < 0.999999)
    usable.loc[r_mask, "N"] = usable.loc[r_mask, "df2_num"] + 2
    r = usable.loc[r_mask, "value"]
    usable.loc[r_mask, "D"] = (2 * r.abs()) / np.sqrt(1 - r**2)
    usable.loc[r_mask, "D_method"] = "statcheck_r_to_d"

    chi_n = extract_chi_n(usable["Raw"])
    chi_mask = (
        stat.eq("chi2")
        & usable["df1_num"].eq(1)
        & usable["value"].notna()
        & chi_n.notna()
        & (chi_n > 0)
    )
    usable.loc[chi_mask, "N"] = chi_n[chi_mask]
    phi = np.sqrt(usable.loc[chi_mask, "value"] / usable.loc[chi_mask, "N"])
    good_phi = phi < 0.999999
    chi_idx = phi[good_phi].index
    usable.loc[chi_idx, "D"] = 2 * phi.loc[chi_idx] / np.sqrt(1 - phi.loc[chi_idx] ** 2)
    usable.loc[chi_idx, "D_method"] = "statcheck_chi2_1_phi_to_d"

    tests = usable[
        np.isfinite(usable["D"])
        & np.isfinite(usable["N"])
        & (usable["N"] >= 4)
        & (usable["N"] <= 10_000_000)
        & (usable["D"] > 0)
        & (usable["D"] <= 30)
    ].copy()
    tests["corpus"] = "psychology_statcheck"
    tests["field"] = "psychology"
    tests["published_original_paper"] = True
    tests["N_method"] = np.where(
        tests["D_method"].eq("statcheck_chi2_1_phi_to_d"),
        "explicit_N_in_chi2_text",
        "df_implied_total_N",
    )

    papers = collapse_to_papers(tests)

    tests.to_csv(interim_dir / "statcheck_published_tests.csv.gz", index=False)
    papers.to_csv(interim_dir / "statcheck_published_papers.csv", index=False)

    summary = {
        "statcheck_raw_rows": len(raw),
        "statcheck_after_error_filter": len(usable),
        "statcheck_test_rows_with_D_N": len(tests),
        "statcheck_papers_with_D_N": tests["paper_id"].nunique(),
        "statcheck_paper_rows_after_collapse": len(papers),
        "statcheck_test_type_counts": tests["D_method"].value_counts().to_dict(),
    }
    return papers, summary


def read_brodeur(path: Path) -> pd.DataFrame:
    cols = [
        "journal",
        "title",
        "table",
        "method",
        "coeff",
        "stderror",
        "year",
        "myz",
        "zstat",
        "t_stat",
        "observations",
        "samplesizenumberobservations",
        "totalnumberofobservations",
        "article_weight",
        "prereg",
        "preanalysisplan",
        "pap_power",
    ]
    return pd.read_stata(path, columns=cols, convert_categoricals=False)


def clean_numeric(series: pd.Series) -> pd.Series:
    text = series.astype(str).str.strip()
    text = text.replace({"": np.nan, ".": np.nan, "nan": np.nan, "None": np.nan})
    text = text.str.replace(",", "", regex=False)
    return pd.to_numeric(text, errors="coerce")


def build_brodeur(path: Path, interim_dir: Path) -> tuple[pd.DataFrame, dict[str, object]]:
    raw = read_brodeur(path)
    df = raw.copy()
    df["paper_id"] = "brodeur_" + df["title"].astype(str).str.strip()
    df["journal"] = df["journal"].astype(str).str.strip()
    df["year"] = pd.to_numeric(df["year"], errors="coerce")
    df["method"] = df["method"].astype(str).str.strip()
    df["z"] = pd.to_numeric(df["myz"], errors="coerce")
    z_fallback = pd.to_numeric(df["zstat"], errors="coerce")
    df.loc[df["z"].isna(), "z"] = z_fallback[df["z"].isna()]
    df["N"] = clean_numeric(df["observations"])

    registry_n = clean_numeric(df["samplesizenumberobservations"])
    total_n = clean_numeric(df["totalnumberofobservations"])
    df["N_registry_or_total"] = registry_n
    df.loc[df["N_registry_or_total"].isna(), "N_registry_or_total"] = total_n[df["N_registry_or_total"].isna()]

    # The published-table observations column is the paper/result-level N.
    # Registry N fields are retained only for diagnostics because they are study-level
    # and sparse; using them for every row would overstate row-specific precision.
    df["D"] = 2 * df["z"].abs() / np.sqrt(df["N"].where(df["N"] > 0))
    tests = df[
        np.isfinite(df["D"])
        & np.isfinite(df["N"])
        & (df["N"] >= 4)
        & (df["N"] <= 10_000_000)
        & (df["D"] > 0)
        & (df["D"] <= 30)
    ].copy()
    tests["corpus"] = "economics_brodeur_2024"
    tests["field"] = "economics"
    tests["published_original_paper"] = True
    tests["D_method"] = "brodeur_2absz_sqrt_observations"
    tests["N_method"] = "published_table_observations"

    papers = collapse_to_papers(tests)

    tests.to_csv(interim_dir / "brodeur_published_tests.csv.gz", index=False)
    papers.to_csv(interim_dir / "brodeur_published_papers.csv", index=False)

    summary = {
        "brodeur_raw_rows": len(raw),
        "brodeur_rows_with_numeric_observations": int(clean_numeric(raw["observations"]).notna().sum()),
        "brodeur_test_rows_with_D_N": len(tests),
        "brodeur_papers_with_D_N": tests["paper_id"].nunique(),
        "brodeur_paper_rows_after_collapse": len(papers),
        "brodeur_method_counts": tests["method"].value_counts().to_dict(),
    }
    return papers, summary


def collapse_to_papers(tests: pd.DataFrame) -> pd.DataFrame:
    grouping = ["corpus", "field", "paper_id"]
    paper = (
        tests.groupby(grouping, dropna=False)
        .agg(
            D_paper=("D", "median"),
            N_paper=("N", "median"),
            n_tests_used=("D", "size"),
            year=("year", "median"),
            journal=("journal", lambda x: x.dropna().astype(str).mode().iat[0] if len(x.dropna()) else ""),
            methods=("D_method", lambda x: ";".join(sorted(set(map(str, x))))),
            N_methods=("N_method", lambda x: ";".join(sorted(set(map(str, x))))),
        )
        .reset_index()
    )
    paper["abs_z_implied"] = paper["D_paper"] * np.sqrt(paper["N_paper"]) / 2
    paper["above_two_sample_p05_curve"] = paper["D_paper"] >= (2 * 1.96 / np.sqrt(paper["N_paper"]))
    paper["above_two_sample_p10_curve"] = paper["D_paper"] >= (
        2 * 1.6448536269514722 / np.sqrt(paper["N_paper"])
    )
    paper["above_two_sample_p01_curve"] = paper["D_paper"] >= (
        2 * 2.5758293035489004 / np.sqrt(paper["N_paper"])
    )
    paper["published_original_paper"] = True
    return paper[
        np.isfinite(paper["D_paper"])
        & np.isfinite(paper["N_paper"])
        & (paper["D_paper"] > 0)
        & (paper["N_paper"] >= 4)
    ].copy()


def ols_loglog(data: pd.DataFrame) -> dict[str, float | int]:
    d = data[(data["D_paper"] > 0) & (data["N_paper"] > 0)].copy()
    x = np.log(d["N_paper"].to_numpy(dtype=float))
    y = np.log(d["D_paper"].to_numpy(dtype=float))
    valid = np.isfinite(x) & np.isfinite(y)
    x, y = x[valid], y[valid]
    n = len(x)
    if n < 3:
        return {
            "n_papers": n,
            "intercept": np.nan,
            "slope": np.nan,
            "slope_se": np.nan,
            "p_value": np.nan,
            "r_squared": np.nan,
            "pearson_r": np.nan,
            "spearman_r": np.nan,
            "tenfold_pct_reduction": np.nan,
        }
    X = np.column_stack([np.ones(n), x])
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    resid = y - X @ beta
    dof = n - 2
    s2 = float((resid @ resid) / dof)
    se = np.sqrt(np.diag(s2 * np.linalg.inv(X.T @ X)))
    p_value = 2 * stats.t.sf(abs(beta[1] / se[1]), dof)
    sst = float(((y - y.mean()) @ (y - y.mean())))
    r2 = 1 - float(resid @ resid) / sst if sst else np.nan
    return {
        "n_papers": n,
        "intercept": float(beta[0]),
        "slope": float(beta[1]),
        "slope_se": float(se[1]),
        "p_value": float(p_value),
        "r_squared": float(r2),
        "pearson_r": float(stats.pearsonr(x, y).statistic),
        "spearman_r": float(stats.spearmanr(x, y).statistic),
        "tenfold_pct_reduction": float(1 - math.exp(beta[1] * math.log(10))),
    }


def make_summaries(papers: pd.DataFrame, out_dir: Path) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for name, data in [("all", papers)] + list(papers.groupby("corpus", dropna=False)):
        fit = ols_loglog(data)
        rows.append(
            {
                "corpus": name,
                "n_papers": len(data),
                "n_tests_used": int(data["n_tests_used"].sum()),
                "median_N": float(data["N_paper"].median()),
                "median_D": float(data["D_paper"].median()),
                "p90_D": float(data["D_paper"].quantile(0.9)),
                "pct_above_p05_curve": float(data["above_two_sample_p05_curve"].mean()),
                "pct_above_p10_curve": float(data["above_two_sample_p10_curve"].mean()),
                "pct_above_p01_curve": float(data["above_two_sample_p01_curve"].mean()),
                **fit,
            }
        )
    summary = pd.DataFrame(rows)
    summary.to_csv(out_dir / "published_original_paper_d_vs_n_summary.csv", index=False)
    return summary


def plot_papers(papers: pd.DataFrame, summary: pd.DataFrame, out_path: Path) -> None:
    fig, ax = plt.subplots(figsize=(9, 6))
    colors = {
        "psychology_statcheck": "#2a4d7a",
        "economics_brodeur_2024": "#0d6650",
    }
    labels = {
        "psychology_statcheck": "psychology statcheck",
        "economics_brodeur_2024": "economics Brodeur raw",
    }
    for corpus, group in papers.groupby("corpus"):
        color = colors.get(corpus, "#777777")
        ax.scatter(
            group["N_paper"],
            group["D_paper"],
            s=8 if corpus == "psychology_statcheck" else 18,
            alpha=0.14 if corpus == "psychology_statcheck" else 0.35,
            color=color,
            edgecolors="none",
            label=f"{labels.get(corpus, corpus)} papers",
        )
        row = summary[summary["corpus"].eq(corpus)]
        if not row.empty and np.isfinite(row["slope"].iloc[0]):
            intercept = row["intercept"].iloc[0]
            slope = row["slope"].iloc[0]
            xs = np.logspace(np.log10(max(group["N_paper"].min(), 4)), np.log10(group["N_paper"].max()), 200)
            ys = np.exp(intercept) * xs**slope
            ax.plot(xs, ys, color=color, linewidth=2, label=f"{labels.get(corpus, corpus)} slope {slope:.2f}")

    xs = np.logspace(np.log10(max(papers["N_paper"].min(), 4)), np.log10(papers["N_paper"].max()), 240)
    ax.plot(xs, 2 * 1.6448536269514722 / np.sqrt(xs), color="black", linestyle=":", linewidth=1.1, label="two-sample p<0.10")
    ax.plot(xs, 2 * 1.96 / np.sqrt(xs), color="black", linestyle="--", linewidth=1.1, label="two-sample p<0.05")
    ax.plot(xs, 2 * 2.5758293035489004 / np.sqrt(xs), color="black", linestyle="-.", linewidth=1.1, label="two-sample p<0.01")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("Published-paper median N (log scale)")
    ax.set_ylabel("Published-paper median |D| (log scale)")
    ax.set_title("Published original papers: D vs N")
    ax.grid(alpha=0.25, which="both")
    ax.legend(fontsize=8, ncol=2)
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=180)
    plt.close(fig)


def markdown_table(frame: pd.DataFrame) -> str:
    show = frame.copy()
    for col in show.columns:
        if pd.api.types.is_float_dtype(show[col]):
            show[col] = show[col].map(lambda x: "" if pd.isna(x) else f"{x:.4g}")
    lines = [
        "| " + " | ".join(show.columns) + " |",
        "| " + " | ".join(["---"] * len(show.columns)) + " |",
    ]
    for _, row in show.iterrows():
        lines.append("| " + " | ".join(str(row[col]) for col in show.columns) + " |")
    return "\n".join(lines)


def write_report(out_path: Path, summary: pd.DataFrame, build_summary: dict[str, object]) -> None:
    show_cols = [
        "corpus",
        "n_papers",
        "n_tests_used",
        "median_N",
        "median_D",
        "p90_D",
        "pct_above_p05_curve",
        "slope",
        "r_squared",
        "tenfold_pct_reduction",
    ]
    lines = [
        "# Published Original Paper D vs N",
        "",
        "Unit: one row per published paper, using the median absolute D and median N across extractable tests/results in that paper.",
        "",
        "## Regression Summary",
        "",
        markdown_table(summary[show_cols]),
        "",
        "## Build Counts",
        "",
    ]
    for key, value in build_summary.items():
        lines.append(f"- `{key}`: {value}")
    lines += [
        "",
        "## Caveats",
        "",
        "- The statcheck corpus uses APA-style text-reported tests from psychology papers; t-tests are treated as two-sample by default.",
        "- The Brodeur economics corpus uses the raw Dataverse `merged.dta` from the 2024 preregistration/p-hacking paper. `observations` is treated as the row-level sample size; rows without numeric observations are excluded.",
        "- These are published-paper corpora, unlike BEAR's registry, Cochrane, replication, and meta-analysis-derived rows.",
        "",
    ]
    out_path.write_text("\n".join(lines))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw", default="data/raw/published_papers")
    parser.add_argument("--interim", default="data/interim/published_papers")
    parser.add_argument("--out", default="data/derived/published_papers")
    parser.add_argument("--reports", default="reports/published_papers")
    parser.add_argument("--download", action="store_true")
    args = parser.parse_args()

    raw_dir = Path(args.raw)
    interim_dir = Path(args.interim)
    out_dir = Path(args.out)
    report_dir = Path(args.reports)
    ensure_dirs(raw_dir, interim_dir, out_dir, report_dir)

    statcheck_path = raw_dir / "statcheck_150211FullFile_AllStatcheckData_Automatic1Tail.csv"
    brodeur_path = raw_dir / "brodeur_2024_merged.dta"
    if args.download:
        download_if_missing(statcheck_path, STATCHECK_URL)
        download_if_missing(brodeur_path, BRODEUR_2024_URL)

    statcheck_papers, statcheck_summary = build_statcheck(statcheck_path, interim_dir)
    brodeur_papers, brodeur_summary = build_brodeur(brodeur_path, interim_dir)
    papers = pd.concat([statcheck_papers, brodeur_papers], ignore_index=True)
    papers.to_csv(out_dir / "published_original_paper_d_vs_n.csv", index=False)

    summary = make_summaries(papers, out_dir)
    plot_papers(papers, summary, report_dir / "published_original_paper_d_vs_n.png")

    build_summary = {**statcheck_summary, **brodeur_summary}
    write_report(out_dir / "published_original_paper_d_vs_n_summary.md", summary, build_summary)

    print(f"Wrote {out_dir / 'published_original_paper_d_vs_n.csv'}")
    print(f"Wrote {out_dir / 'published_original_paper_d_vs_n_summary.csv'}")
    print(f"Wrote {out_dir / 'published_original_paper_d_vs_n_summary.md'}")
    print(f"Wrote {report_dir / 'published_original_paper_d_vs_n.png'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
