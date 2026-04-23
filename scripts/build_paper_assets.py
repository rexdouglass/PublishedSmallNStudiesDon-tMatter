#!/usr/bin/env python3
"""Build Quarto-ready paper assets from the Claude HTML draft and local data.

This script is deliberately extraction-backed: the old HTML draft is treated as
the seed document, while current derived datasets provide the upgraded figures
and synced figure captions.
"""

from __future__ import annotations

import csv
import math
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from bs4 import BeautifulSoup, NavigableString
from scipy import stats


ROOT = Path(__file__).resolve().parents[1]
DRAFT_HTML = ROOT / "docs" / "nightmare-hellscape (3).html"
DOCS = ROOT / "docs"
GENERATED = DOCS / "_generated"
FIG_DIR = GENERATED / "figures"
TABLE_DIR = ROOT / "data" / "derived" / "paper_tables"
TABLE_FRAGMENT_DIR = GENERATED / "tables"
BODY_QMD = GENERATED / "paper_body.qmd"
CITATION_AUDIT = GENERATED / "citation_audit.csv"
TABLE_MANIFEST = TABLE_DIR / "table_manifest.csv"
INTRO_EXAMPLES = ROOT / "data" / "derived" / "paper_assets" / "figure1_intro_examples.csv"

REPLICATION_FIG = ROOT / "reports" / "corpus_candidates" / "figure2_replication_pairs_draft.png"
REPLICATION_CSV = ROOT / "data" / "derived" / "replication_pairs" / "replication_pairs_figure2_rule_subset.csv"
PUBLISHED_FIG = ROOT / "reports" / "corpus_candidates" / "candidate_published_paper_d_vs_n.png"
PUBLISHED_PAPERS = ROOT / "data" / "derived" / "corpus_candidates" / "candidate_d_n_papers.csv"
FIELD_GROUPS = ROOT / "data" / "derived" / "corpus_candidates" / "candidate_published_field_groups.csv"

Z_05 = 1.959963984540054


@dataclass(frozen=True)
class FigureSpec:
    token: str
    key: str
    path: Path
    caption: str


def as_bool(value: object) -> bool:
    text = str(value).strip().lower()
    return text in {"true", "1", "yes", "y", "t"}


def ensure_dirs() -> None:
    for path in [GENERATED, FIG_DIR, TABLE_DIR, TABLE_FRAGMENT_DIR]:
        path.mkdir(parents=True, exist_ok=True)


def text_of(node) -> str:
    return " ".join(node.get_text(" ", strip=True).split())


def slugify(value: str, fallback: str) -> str:
    value = re.sub(r"[^A-Za-z0-9]+", "_", value.strip().lower()).strip("_")
    return value or fallback


def markdown_table(rows: list[list[str]]) -> str:
    if not rows:
        return ""
    width = max(len(row) for row in rows)
    padded = [row + [""] * (width - len(row)) for row in rows]
    header, body = padded[0], padded[1:]

    def clean(cell: str) -> str:
        return str(cell).replace("\n", " ").replace("|", "\\|").strip()

    lines = [
        "| " + " | ".join(clean(cell) for cell in header) + " |",
        "| " + " | ".join(["---"] * width) + " |",
    ]
    for row in body:
        lines.append("| " + " | ".join(clean(cell) for cell in row) + " |")
    return "\n".join(lines)


def extract_tables(soup: BeautifulSoup) -> dict[str, str]:
    """Extract all HTML tables to CSV and generated Markdown fragments."""
    table_tokens: dict[str, str] = {}
    manifest_rows: list[dict[str, str | int]] = []
    tables = soup.find_all("table")

    for idx, table in enumerate(tables, start=1):
        previous_heading = table.find_previous(["h2", "h3", "h4", "h5"])
        heading = text_of(previous_heading) if previous_heading else f"Table {idx}"
        table_id = f"table_{idx:02d}_{slugify(heading, f'table_{idx:02d}')[:64]}"
        csv_path = TABLE_DIR / f"{table_id}.csv"
        fragment_path = TABLE_FRAGMENT_DIR / f"{table_id}.qmd"

        rows: list[list[str]] = []
        for tr in table.find_all("tr"):
            cells = tr.find_all(["th", "td"])
            if cells:
                rows.append([text_of(cell) for cell in cells])
        if not rows:
            rows = [[heading]]

        with csv_path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerows(rows)

        title = f"Table {idx}. {heading}"
        fragment = "\n".join(
            [
                "",
                '::: {.paper-table}',
                f"**{title}**",
                "",
                markdown_table(rows),
                ":::",
                "",
            ]
        )
        fragment_path.write_text(fragment, encoding="utf-8")

        token = f"TABLE_TOKEN_{idx:02d}"
        table_tokens[token] = fragment
        manifest_rows.append(
            {
                "table_index": idx,
                "table_id": table_id,
                "heading": heading,
                "source_class": "html_extract",
                "csv_path": str(csv_path.relative_to(ROOT)),
                "fragment_path": str(fragment_path.relative_to(ROOT)),
                "n_rows_including_header": len(rows),
                "n_columns_max": max(len(row) for row in rows),
            }
        )
        table.replace_with(NavigableString(f"\n\n{token}\n\n"))

    pd.DataFrame(manifest_rows).to_csv(TABLE_MANIFEST, index=False)
    return table_tokens


def parse_author_literals(author_text: str) -> list[dict[str, str]]:
    author_text = re.sub(r"\bet al\.?$", "", author_text.strip(), flags=re.I).strip()
    author_text = author_text.replace(" & ", ", ").replace(" and ", ", ")
    parts = [part.strip(" .") for part in author_text.split(",") if part.strip(" .")]
    return [{"literal": part} for part in parts[:12]] or [{"literal": author_text or "Unknown"}]


def parse_csl_entry(entry) -> dict[str, object]:
    citekey = entry.get("id", "").replace("ref-", "", 1)
    clone = BeautifulSoup(str(entry), "html.parser")
    for backlink in clone.select(".backlink"):
        backlink.decompose()
    right = clone.select_one(".csl-right-inline") or clone
    full = text_of(right)
    full = re.sub(r"\s*↩\s*$", "", full).strip()
    year_match = re.search(r"\((\d{4}[a-z]?)\)", full)
    year = int(year_match.group(1)[:4]) if year_match else None
    before_year = full[: year_match.start()].strip(" .") if year_match else ""
    after_year = full[year_match.end() :].strip(" .") if year_match else full
    container = text_of(right.find("em")) if right.find("em") else ""
    doi_link = ""
    url = ""
    for link in right.find_all("a", href=True):
        href = link["href"]
        if "doi.org/" in href and not doi_link:
            doi_link = href
        elif href.startswith("http") and not url:
            url = href

    title = after_year
    if container and container in title:
        title = title.split(container, 1)[0].strip(" .")
    title = title or full or citekey

    item: dict[str, object] = {
        "id": citekey,
        "type": "article-journal" if container else "webpage",
        "title": title,
    }
    if before_year:
        item["author"] = parse_author_literals(before_year)
    if year:
        item["issued"] = {"date-parts": [[year]]}
    if container:
        item["container-title"] = container
    if doi_link:
        item["DOI"] = doi_link.rsplit("/", 1)[-1]
        item["URL"] = doi_link
    elif url:
        item["URL"] = url
    if full:
        item["note"] = full
    return item


def extract_bibliography(soup: BeautifulSoup) -> set[str]:
    """Return draft bibliography keys for citation auditing.

    Bibliography files are built by scripts/build_bibliography.py. This paper
    asset step should not overwrite the enriched BibTeX/CSL outputs.
    """
    entries = soup.select("div.csl-entry")
    items = [parse_csl_entry(entry) for entry in entries]
    seen: set[str] = set()
    for item in items:
        citekey = str(item["id"])
        if citekey not in seen:
            seen.add(citekey)
    return seen


def citation_markdown(cites_raw: str) -> str:
    citekeys = [cite.strip() for cite in cites_raw.split() if cite.strip()]
    if not citekeys:
        return ""
    return " [" + "; ".join(f"@{cite}" for cite in citekeys) + "]"


def replace_citation_spans(soup: BeautifulSoup) -> set[str]:
    in_text: set[str] = set()
    for span in soup.select("span.citation"):
        cites = span.get("data-cites") or span.get("cites") or ""
        for cite in cites.split():
            if cite.strip():
                in_text.add(cite.strip())
        span.replace_with(NavigableString(citation_markdown(cites)))
    return in_text


def fit_loglog(df: pd.DataFrame, d_col: str, n_col: str) -> tuple[float, float]:
    values = df[[d_col, n_col]].copy()
    values[d_col] = pd.to_numeric(values[d_col], errors="coerce")
    values[n_col] = pd.to_numeric(values[n_col], errors="coerce")
    values = values[(values[d_col] > 0) & (values[n_col] > 0)].dropna()
    x = np.log10(values[n_col].to_numpy(dtype=float))
    y = np.log10(values[d_col].to_numpy(dtype=float))
    if len(values) < 3:
        return math.nan, math.nan
    slope, intercept = np.polyfit(x, y, 1)
    return float(slope), float(intercept)


def replication_stats() -> dict[str, float | int]:
    df = pd.read_csv(REPLICATION_CSV)
    counts = df["category"].value_counts()
    all_n = np.concatenate([df["N_original"].to_numpy(dtype=float), df["N_replication"].to_numpy(dtype=float)])
    all_d = np.concatenate([df["D_original"].to_numpy(dtype=float), df["D_replication"].to_numpy(dtype=float)])
    mask = np.isfinite(all_n) & np.isfinite(all_d) & (all_n > 0) & (all_d > 0)
    slope, _ = np.polyfit(np.log10(all_n[mask]), np.log10(all_d[mask]), 1)
    orig_key = df["original_doi"].fillna("").astype(str).str.strip()
    orig_key = orig_key.where(orig_key.ne(""), df["original_title"].fillna("").astype(str).str.strip())
    rep_key = df["replication_doi"].fillna("").astype(str).str.strip()
    rep_key = rep_key.where(rep_key.ne(""), df["replication_title"].fillna("").astype(str).str.strip())
    orig_counts = orig_key.value_counts()
    rep_counts = rep_key.value_counts()
    return {
        "n_pairs": len(df),
        "n_shrunk_below": int(counts.get("shrunk_below_sig", 0)),
        "n_shrunk_still": int(counts.get("shrunk_still_sig", 0)),
        "n_grew": int(counts.get("grew", 0)),
        "pct_shrunk_below": 100 * counts.get("shrunk_below_sig", 0) / len(df),
        "pct_shrunk_any": 100 * (counts.get("shrunk_below_sig", 0) + counts.get("shrunk_still_sig", 0)) / len(df),
        "tenfold_reduction_pct": 100 * (1 - 10**slope),
        "median_d_original": float(df["D_original"].median()),
        "median_d_replication": float(df["D_replication"].median()),
        "median_n_original": float(df["N_original"].median()),
        "median_n_replication": float(df["N_replication"].median()),
        "n_unique_original_papers": int(orig_key.nunique()),
        "n_unique_replication_papers": int(rep_key.nunique()),
        "n_original_papers_multirow": int((orig_counts > 1).sum()),
        "n_replication_papers_multirow": int((rep_counts > 1).sum()),
    }


def published_stats() -> dict[str, float | int]:
    papers = pd.read_csv(PUBLISHED_PAPERS)
    main = papers[papers["published_original_candidate"].astype(bool) & ~papers["comparator_only"].astype(bool)].copy()
    main = main[(main["D_median"] > 0) & (main["N_median"] > 0)].copy()
    z10 = 1.6448536269514722
    above_p10 = main["D_median"] >= (2 * z10 / np.sqrt(main["N_median"]))
    field_count = int(main["field"].nunique())
    source_count = int(main["source_corpus"].nunique())
    return {
        "n_papers": len(main),
        "field_count": field_count,
        "source_count": source_count,
        "median_d": float(main["D_median"].median()),
        "median_n": float(main["N_median"].median()),
        "pct_above_p10": 100 * float(above_p10.mean()),
        "pct_d_ge_02": 100 * float((main["D_median"] >= 0.2).mean()),
        "pct_d_ge_05": 100 * float((main["D_median"] >= 0.5).mean()),
        "pct_d_ge_08": 100 * float((main["D_median"] >= 0.8).mean()),
    }


def figure1_intro_examples() -> tuple[pd.DataFrame, pd.DataFrame]:
    examples = pd.read_csv(INTRO_EXAMPLES).fillna("")
    examples["include_in_figure1"] = examples["include_in_figure1"].map(as_bool)
    included = examples[examples["include_in_figure1"]].copy()
    included["n"] = pd.to_numeric(included["n"], errors="coerce")
    included["d"] = pd.to_numeric(included["d"], errors="coerce")
    included["label_dx"] = pd.to_numeric(included["label_dx"], errors="coerce")
    included["label_dy"] = pd.to_numeric(included["label_dy"], errors="coerce")
    included = included.dropna(subset=["n", "d", "label_dx", "label_dy"])
    return examples, included


def draw_publication_boundary(out_path: Path) -> None:
    xs = np.logspace(1, 4, 400)
    boundary = 2 * Z_05 / np.sqrt(xs)
    _, included_examples = figure1_intro_examples()

    fig, ax = plt.subplots(figsize=(8.2, 5.8), dpi=180)
    ax.fill_between(xs, boundary, 2.0, color="#e8f5ee", alpha=0.95)
    ax.fill_between(xs, 0.01, boundary, color="#fceaea", alpha=0.95)
    ax.plot(xs, boundary, color="#1a1a1a", lw=2.0)
    ax.scatter(
        included_examples["n"],
        included_examples["d"],
        s=58,
        facecolors=(42 / 255, 77 / 255, 122 / 255, 0.25),
        edgecolors="#2a4d7a",
        lw=1.8,
        zorder=4,
    )

    for row in included_examples.itertuples(index=False):
        ax.annotate(
            str(row.plot_label).replace("\\n", "\n"),
            (float(row.n), float(row.d)),
            xytext=(float(row.label_dx), float(row.label_dy)),
            textcoords="offset points",
            fontsize=8.2,
            ha=str(row.label_ha),
            va="center",
            color="#1a1a1a",
        )

    ax.axhline(0.2, color="#777777", lw=1, linestyle="--")
    ax.axvline(300, color="#777777", lw=1, linestyle="--")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlim(10, 10000)
    ax.set_ylim(0.01, 2.0)
    ax.set_xticks([10, 100, 1000, 10000])
    ax.set_xticklabels(["10", "100", "1,000", "10K"])
    ax.set_yticks([2.0, 1.0, 0.5, 0.2, 0.1, 0.05, 0.02, 0.01])
    ax.set_yticklabels(["2.0", "1.0", "0.5", "0.2", "0.1", "0.05", "0.02", "0.01"])
    ax.set_xlabel("Sample size (log scale)")
    ax.set_ylabel("Reported effect size (Cohen's d, log scale)")
    ax.set_title("The p < 0.05 publication boundary", fontweight="bold")
    ax.grid(True, which="major", alpha=0.18, linestyle=":")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    ax.text(
        0.80,
        0.41,
        "p < 0.05 effect sizes that do get published ↗",
        transform=ax.transAxes,
        rotation=-23,
        ha="center",
        va="center",
        fontsize=8.4,
        fontweight="bold",
        color="#0d6650",
    )
    ax.text(
        0.80,
        0.36,
        "↙ p > 0.05 effect sizes that don't get published",
        transform=ax.transAxes,
        rotation=-23,
        ha="center",
        va="center",
        fontsize=8.4,
        fontweight="bold",
        color="#a03030",
    )

    quad_kwargs = dict(transform=ax.transAxes, fontsize=7.8, fontweight="bold", color="#505050")
    ax.text(0.015, 0.98, "Unlikely effects + weak evidence", ha="left", va="top", **quad_kwargs)
    ax.text(0.985, 0.98, "Unlikely effects + strong evidence", ha="right", va="top", **quad_kwargs)
    ax.text(0.015, 0.02, "Common effects + weak evidence", ha="left", va="bottom", **quad_kwargs)
    ax.text(0.985, 0.02, "Common effects + strong evidence", ha="right", va="bottom", **quad_kwargs)
    fig.tight_layout()
    fig.savefig(out_path, bbox_inches="tight")
    plt.close(fig)


def draw_prior_comparison(out_path: Path) -> None:
    x = np.linspace(-1.8, 1.8, 600)
    gelman = stats.norm.pdf(x, loc=0, scale=0.35)
    flat = np.full_like(x, 0.22)
    fig, ax = plt.subplots(figsize=(8.2, 4.7), dpi=180)
    ax.plot(x, flat, color="#c44a1e", lw=2.3, label="implicit flat/no-shrinkage prior")
    ax.fill_between(x, flat, color="#c44a1e", alpha=0.10)
    ax.plot(x, gelman, color="#1456a0", lw=2.5, label="Normal(0, 0.35)")
    ax.fill_between(x, gelman, color="#1456a0", alpha=0.12)
    ax.axvline(0.8, color="#555555", lw=1.0, linestyle="--")
    ax.text(0.82, max(gelman) * 0.85, "d = 0.8", fontsize=9, color="#555555", ha="left")
    ax.set_xlabel("True effect size d")
    ax.set_ylabel("Prior density")
    ax.set_title("What you implicitly believe before the data", fontweight="bold")
    ax.legend(frameon=False, loc="upper left")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    fig.savefig(out_path, bbox_inches="tight")
    plt.close(fig)


def draw_published_distribution(out_path: Path) -> dict[str, float | int]:
    stats_dict = published_stats()
    papers = pd.read_csv(PUBLISHED_PAPERS)
    main = papers[papers["published_original_candidate"].astype(bool) & ~papers["comparator_only"].astype(bool)].copy()
    main = main[(main["D_median"] > 0) & (main["N_median"] > 0)].copy()
    values = main["D_median"].clip(lower=0, upper=3)
    fig, ax = plt.subplots(figsize=(8.2, 4.8), dpi=180)
    ax.hist(values, bins=np.arange(0, 3.05, 0.1), density=True, histtype="stepfilled", color="#c44a1e", alpha=0.22)
    ax.hist(values, bins=np.arange(0, 3.05, 0.1), density=True, histtype="step", color="#c44a1e", lw=2.0)
    for x, label in [(0.2, "small"), (0.5, "medium"), (0.8, "large")]:
        ax.axvline(x, color="#777777", lw=1.0, linestyle=":")
        ax.text(x, ax.get_ylim()[1] * 0.94, f"{label}\nd={x:g}", ha="center", va="top", fontsize=8, color="#555555")
    ax.axvline(stats_dict["median_d"], color="#c44a1e", lw=1.4, linestyle="--")
    ax.text(
        stats_dict["median_d"] + 0.03,
        ax.get_ylim()[1] * 0.72,
        f"median D = {stats_dict['median_d']:.2f}",
        color="#a33d18",
        fontsize=9,
        fontweight="bold",
    )
    ax.set_xlim(0, 3)
    ax.set_xlabel("Reported effect size D (paper median, clipped at 3)")
    ax.set_ylabel("Density")
    ax.set_title("Published focal-result papers as a distribution of effect sizes", fontweight="bold")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    fig.savefig(out_path, bbox_inches="tight")
    plt.close(fig)
    return stats_dict


def generate_figures() -> dict[str, FigureSpec]:
    fig1 = FIG_DIR / "figure1_publication_boundary.png"
    fig2 = FIG_DIR / "figure2_replication_combined.png"
    fig3 = FIG_DIR / "figure3_published_d_vs_n.png"
    fig4 = FIG_DIR / "figure4_prior_comparison.png"
    fig5 = FIG_DIR / "figure5_published_d_distribution.png"

    draw_publication_boundary(fig1)
    if REPLICATION_FIG.exists():
        shutil.copy2(REPLICATION_FIG, fig2)
    if PUBLISHED_FIG.exists():
        shutil.copy2(PUBLISHED_FIG, fig3)
    draw_prior_comparison(fig4)
    pub_stats = draw_published_distribution(fig5)
    repl_stats = replication_stats()

    return {
        "FIGURE_TOKEN_01": FigureSpec(
            "FIGURE_TOKEN_01",
            "fig-publication-boundary",
            fig1,
            (
                "The p < .05 publication boundary. For a two-sample test, a study only clears "
                "the conventional threshold when observed D is roughly 2 * 1.96 / sqrt(N). "
                "The labeled points are the opening-scenario examples that map cleanly onto a "
                "single-study two-sample-style D-vs-N point."
            ),
        ),
        "FIGURE_TOKEN_02": FigureSpec(
            "FIGURE_TOKEN_02",
            "fig-replication-combined",
            fig2,
            (
                f"Huge effect sizes evaporate in larger replication attempts. The current recovered "
                f"pair table contains {repl_stats['n_pairs']:,} original/replication endpoint pairs; "
                f"{repl_stats['pct_shrunk_any']:.0f}% shrink, {repl_stats['pct_shrunk_below']:.0f}% "
                f"shrink below the p < .05 boundary, and the log-log fit implies about "
                f"{repl_stats['tenfold_reduction_pct']:.0f}% lower D for each 10x increase in N. "
                "The marginal distributions replace the draft's old separate before/after distribution figure."
            ),
        ),
        "FIGURE_TOKEN_04": FigureSpec(
            "FIGURE_TOKEN_04",
            "fig-published-d-vs-n",
            fig3,
            (
                f"The small-N and huge-effect-size pattern in published journal articles. "
                f"The current paper-level corpus has {pub_stats['n_papers']:,} published-original "
                f"candidate papers across {pub_stats['source_count']} source corpora; "
                f"median D is {pub_stats['median_d']:.2f}, median N is {pub_stats['median_n']:.0f}, "
                f"and {pub_stats['pct_above_p10']:.0f}% sit above the p <= .10 boundary."
            ),
        ),
        "FIGURE_TOKEN_05": FigureSpec(
            "FIGURE_TOKEN_05",
            "fig-prior-comparison",
            fig4,
            (
                "What you implicitly believe before the data. The flat/no-shrinkage line treats "
                "large effects as no less plausible than small effects; the Normal(0, 0.35) prior "
                "puts most mass on behavioral-science effects near zero."
            ),
        ),
        "FIGURE_TOKEN_06": FigureSpec(
            "FIGURE_TOKEN_06",
            "fig-published-d-distribution",
            fig5,
            (
                f"The current published-original candidate corpus as a distribution of paper-level "
                f"effect sizes. {pub_stats['pct_d_ge_02']:.0f}% of papers have median D >= 0.2, "
                f"{pub_stats['pct_d_ge_05']:.0f}% have median D >= 0.5, and "
                f"{pub_stats['pct_d_ge_08']:.0f}% have median D >= 0.8."
            ),
        ),
    }


def figure_markdown(spec: FigureSpec) -> str:
    rel_path = spec.path.relative_to(DOCS)
    return f"\n![{spec.caption}]({rel_path.as_posix()}){{#{spec.key}}}\n"


def replace_old_figure_nodes(soup: BeautifulSoup) -> None:
    figures = soup.select("div.figure")
    for idx, fig in enumerate(figures, start=1):
        if idx == 3:
            fig.replace_with(
                NavigableString(
                    "\n\nThe current combined replication figure includes the before/after "
                    "effect-size distribution that the draft originally showed as a separate figure.\n\n"
                )
            )
        else:
            fig.replace_with(NavigableString(f"\n\nFIGURE_TOKEN_{idx:02d}\n\n"))


def replace_paragraph_containing(soup: BeautifulSoup, needle: str, replacement: str) -> None:
    for p in soup.find_all("p"):
        if needle in text_of(p):
            p.clear()
            p.append(NavigableString(replacement))
            return


def update_stale_prose(soup: BeautifulSoup, repl: dict[str, float | int], pub: dict[str, float | int]) -> None:
    replace_paragraph_containing(
        soup,
        "Below are 555 pairs",
        (
            f"Below are {repl['n_pairs']:,} recovered original/replication endpoint pairs, now using the expanded "
            "local replication-pair build rather than the smaller draft table alone."
        ),
    )
    replace_paragraph_containing(
        soup,
        "plots most of them",
        (
            f"Figure 2 summarizes the current replication build. {repl['pct_shrunk_any']:.0f}% of effects shrink, "
            f"{repl['pct_shrunk_below']:.0f}% shrink below the p < 0.05 boundary at the replication sample size, "
            f"and the fitted log-log slope implies about {repl['tenfold_reduction_pct']:.0f}% lower D for each 10x increase in N."
        ),
    )
    replace_paragraph_containing(
        soup,
        "Figure 3 shows the distribution",
        (
            "The same combined figure also shows the before/after distribution: the original claims are the selected literature, "
            "and the replication distribution is what remains when the same claims are re-measured with larger samples."
        ),
    )
    replace_paragraph_containing(
        soup,
        "What would the published record look like in that world?",
        (
            f"What would the published record look like in that world? Figure 4 now uses the expanded local published-focal corpus: "
            f"{pub['n_papers']:,} published-original candidate papers across {pub['source_count']} source corpora, each collapsed "
            f"to a paper-level median D and N. The point cloud is no longer just the older statcheck/economics draft example; "
            "it is the current cross-field Codex build."
        ),
    )
    replace_paragraph_containing(
        soup,
        "14,110 papers in Figure",
        (
            f"If you believe any one of the {pub['n_papers']:,} papers in the current published-corpus figure is a literal reading "
            "of the effect size in the world, you have to believe the process that produced the whole cloud."
        ),
    )
    replace_paragraph_containing(
        soup,
        "Discount at 5%",
        (
            "A frequentist defender would object here. A p < 0.05 finding is not claimed with certainty; "
            "the threshold itself admits a 1-in-20 false-positive rate, and p < 0.01 admits 1-in-100. "
            f"Discount the current {pub['n_papers']:,}-paper published-focal corpus by those rates and the "
            f"basic arithmetic barely changes: roughly {0.95 * pub['n_papers']:,.0f} papers remain under a 5% discount "
            f"and roughly {0.99 * pub['n_papers']:,.0f} under a 1% discount. More importantly, the p-value discount is about "
            "whether an effect exists under the null, not whether the reported magnitude is right."
        ),
    )
    replace_paragraph_containing(
        soup,
        "Across all 555 pairs",
        (
            f"The current replication-pair build contains {repl['n_pairs']:,} usable original/replication endpoint pairs. "
            f"Across those rows, {repl['pct_shrunk_any']:.0f}% of effects shrink and {repl['pct_shrunk_below']:.0f}% "
            "drop below the p < .05 boundary at the replication sample size."
        ),
    )


def replace_figure_refs(markdown: str) -> str:
    replacements = [
        (r"Figures(?:\\ | |\u00a0)2(?:\\ | |\u00a0)and(?:\\ | |\u00a0)3", "@fig-replication-combined"),
        (r"Figures(?:\\ | |\u00a0)1(?:\\ | |\u00a0)and(?:\\ | |\u00a0)5", "@fig-publication-boundary and @fig-prior-comparison"),
        (r"Figure(?:\\ | |\u00a0)1", "@fig-publication-boundary"),
        (r"Figure(?:\\ | |\u00a0)2", "@fig-replication-combined"),
        (r"Figure(?:\\ | |\u00a0)3", "@fig-replication-combined"),
        (r"Figure(?:\\ | |\u00a0)4", "@fig-published-d-vs-n"),
        (r"Figure(?:\\ | |\u00a0)5", "@fig-prior-comparison"),
        (r"Figure(?:\\ | |\u00a0)6", "@fig-published-d-distribution"),
    ]
    for pattern, replacement in replacements:
        markdown = re.sub(pattern, replacement, markdown)
    return markdown


def replace_rendered_ref_groups(markdown: str) -> str:
    def to_citation(match: re.Match[str]) -> str:
        keys = re.findall(r"#ref-([A-Za-z0-9_:\-]+)", match.group(0))
        if not keys:
            return ""
        deduped = list(dict.fromkeys(keys))
        return " [" + "; ".join(f"@{key}" for key in deduped) + "]"

    # Pandoc sees some already-rendered bibliography links as superscripted
    # inline links rather than citation spans. Convert each such group back to
    # citeproc syntax.
    markdown = re.sub(r"\^\[[^\n^]*#ref-[^\n^]*?\^", to_citation, markdown)
    return markdown


def normalize_pandoc_markdown(markdown: str) -> str:
    # Pandoc converts pre-rendered citation links into spans if any escaped ones
    # survive. Strip those remnants so citeproc owns the final references.
    markdown = re.sub(r"\[\^\[[^\]]+\]\([^)]+\)[^\]]*\]\{\.citation[^}]*\}", "", markdown)
    markdown = re.sub(r"\\\[(@[A-Za-z0-9_:\-]+(?:; @?[A-Za-z0-9_:\-]+)*)\\\]", r"[\1]", markdown)
    markdown = replace_rendered_ref_groups(markdown)
    markdown = markdown.replace("::: {#title-block-header}", "")
    markdown = markdown.replace("555-pair corpus", "replication-pair corpus")
    markdown = markdown.replace("555-row table", "replication-pair table")
    return markdown


def rewrite_opening_scenario(markdown: str) -> str:
    original = (
        "Your morning starts with wild swings in trust for your spouse: up 11% from holding a warm cup of coffee, "
        "[@williams2008] then down 30% from the smell of last night's kitchen trash. [@lee2012] Uncertain about "
        "your marriage, you pick out a red shirt for the 10% bump on the attractiveness scale [@elliot2008] and "
        "head to work. There a power pose jacks your testosterone 30%, [@carney2010] and putting your feet up on "
        "the desk makes you 43% more likely to take a risky bet. [@yap2013] Your inevitable meeting with HR is "
        "all but guaranteed by a dim break-room light that made you cheat on your reimbursement forms 47% above "
        "baseline. [@zhong2010lamps] To save your job and protect your health, you duck out of work early and head "
        "to the bar. The bottle of red wine reduces your cardiovascular mortality 30% and your all-cause mortality "
        "20%. [@ronksley2011] Somehow you make it home and vow to do better the next day. You swallow a fistful of "
        "vitamin C, [@pauling1970] echinacea, [@shah2007] zinc, [@hemila2017] and melatonin, [@herxheimer2002] "
        "all guaranteed to halve various medical and sleep problems. Exhausted, you doze off to a podcast about "
        "there being yet another study proving the existence of ESP. [@bem2011]"
    )
    revised = (
        "Your morning starts with wild swings in trust for your spouse: up 11% from holding a warm cup of coffee, "
        "[@williams2008] then down 30% from the smell of last night's kitchen trash. [@lee2012] Uncertain about "
        "your marriage, you pick out a red shirt for the 10% bump on the attractiveness scale [@elliot2008] and "
        "head to work. There a power pose jacks your testosterone 30%, and putting your feet up on the desk makes "
        "you 43% more likely to take a risky bet. [@carney2010] Your inevitable meeting with HR is all but "
        "guaranteed by a dim room light that made you cheat on your reimbursement forms 47% above baseline. "
        "[@zhong2010lamps] To save your job and protect your health, you duck out of work early and head to the "
        "bar. The bottle of red wine reduces your cardiovascular mortality 30% and your all-cause mortality 20%. "
        "[@ronksley2011] Somehow you make it home and vow to do better the next day. You swallow a fistful of "
        "vitamin C, [@pauling1970] echinacea, [@shah2007] zinc, [@hemila2017] and melatonin, [@herxheimer2002] "
        "all guaranteed to halve various medical and sleep problems. Exhausted, you doze off to a podcast about "
        "there being yet another study proving the existence of ESP. [@bem2011]"
    )
    return markdown.replace(original, revised, 1)


def find_top_level_section(markdown: str, heading: str) -> tuple[str, str, int, int]:
    match = re.search(rf"(?m)^## {re.escape(heading)}(?:\s|$)", markdown)
    if not match:
        raise RuntimeError(f"Could not find section heading: {heading}")
    start = match.start()
    line_end = markdown.find("\n", match.start())
    if line_end == -1:
        raise RuntimeError(f"Malformed section heading: {heading}")
    next_match = re.search(r"(?m)^## ", markdown[line_end + 1 :])
    end = line_end + 1 + next_match.start() if next_match else len(markdown)
    heading_line = markdown[start:line_end]
    body = markdown[line_end + 1 : end].strip()
    return heading_line, body, start, end


def restructure_sections(markdown: str) -> str:
    most_heading, most_body, most_start, most_end = find_top_level_section(markdown, "Most Effect Sizes Must be Small")
    large_heading, large_body, large_start, large_end = find_top_level_section(
        markdown, "Because Large Effects Are Special, They Require Special Evidence"
    )

    large_blocks = [block.strip() for block in large_body.split("\n\n") if block.strip()]
    if len(large_blocks) < 6:
        raise RuntimeError("Large-effects section structure changed unexpectedly")

    moved_block = "\n\n".join(large_blocks)
    anchor = (
        "Three independent empirical literatures then confirm the total size of the resulting gap: "
        "coordinated replication projects, large-*N* replications of specific famous findings, and cross-literature effect-size censuses. "
        "The full argument is [Appendix\u00a0F](#appendix-f-why-most-effects-must-be-small)."
    )
    if anchor not in most_body:
        raise RuntimeError("Most-effects section anchor changed unexpectedly")
    new_most_body = most_body.replace(anchor, moved_block + "\n\n" + anchor, 1)

    new_large_body = (
        "The point is not that large effects never happen. It is that real large effects look like vaccines, "
        "antibiotics, and other interventions whose targets visibly collapse under coarse measurement and large-scale "
        "replication, not like vague primes in 42 undergraduates.\n\n"
        "That is why the burden of evidence rises with the size of the claim. If a result is supposed to live in the "
        "thin tail of @fig-prior-comparison, then the evidence has to look tail-worthy too: large samples, hard outcomes, "
        "active controls, repeated success across sites, or effects obvious enough to see without statistical heroics."
    )

    rebuilt_most = f"{most_heading}\n\n{new_most_body}\n\n"
    rebuilt_large = f"{large_heading}\n\n{new_large_body}\n\n"
    markdown = markdown[:most_start] + rebuilt_most + markdown[most_end:large_start] + rebuilt_large + markdown[large_end:]
    return markdown


def rewrite_most_effects_section(markdown: str, repl: dict[str, float | int]) -> str:
    heading, _body, start, end = find_top_level_section(markdown, "Most Effect Sizes Must be Small")

    tau = 0.35
    n_small = 40.0
    n_large = 400.0
    s_small = 2 / math.sqrt(n_small)
    s_large = 2 / math.sqrt(n_large)
    w_small = tau**2 / (tau**2 + s_small**2)
    w_large = tau**2 / (tau**2 + s_large**2)
    post_small = w_small * 0.80
    post_large = w_large * 0.80

    body = f"""
The right question is not whether a published estimate crossed *p* < .05. The right question is: given what real effects usually look like, and given that this estimate survived a publication process that rewards large significant estimates, what should I now believe about the true effect?

The first input to that judgment is empirical, not philosophical. **@fig-replication-combined** gives us {int(repl['n_pairs']):,} recovered original/replication endpoint pairs, all on a common $D$ scale, all with both sample sizes known, and all with the replication larger than the original. In that sample, {repl['pct_shrunk_any']:.0f}% of effects shrink, {repl['pct_shrunk_below']:.0f}% shrink below the original *p* < .05 boundary at the replication sample size, and the fitted log-log relationship implies about {repl['tenfold_reduction_pct']:.0f}% lower $D$ for each 10x increase in $N$. That distribution is not an oracle, but it is the least-filtered empirical prior available here: larger samples, direct retests, and far less room for the original publication boundary to select the observed magnitude.

The second input is structural. Appendix F lays out eleven reasons most effects must be small before we ever look at a *p*-value. The short version is that behavioral, biomedical, educational, and social outcomes are bounded noisy aggregates. They are produced by many causes, mediated through partial mechanisms, measured with finite reliability, diluted by active controls and counterfactual exposure, averaged across heterogeneous people and settings, and eroded by site-to-site voltage drop and scale-up decay [@tosh2024; @pearl2001mediation; @mackinnon2002mediation; @spearman1904; @hedge2018reliability; @bryan2021heterogeneity; @klein2018; @alubaydli2017scalability; @pereira2012largeeffects]. Ordinary interventions usually push on one weak edge in a dense causal graph, not on a single unconstrained bottleneck.

The third input is statistical. A published estimate is not just a noisy draw from the world. It is a noisy draw that survived a significance filter. Gelman and Carlin's Type M framework, van Zwet and Cator's significance-filter analysis, and the broader winner's-curse literature all imply the same direction of correction: conditional on significance, small noisy studies exaggerate magnitude [@gelman2014beyondpower; @zwet2021; @ioannidis2008inflation; @loken2017measurement]. So a rational reader needs shrinkage, not just standard errors.

That is what **@fig-prior-comparison** is for. The flat line is the implicit no-shrinkage prior: every effect from $d = 0.01$ to $d = 1{','}000$ treated as no less plausible than every other. The blue curve is the weakly informative Normal$(0, 0.35)$ prior. It does not ban large effects. It says they are rare enough to pay an evidentiary tax. About 95% of that prior lies inside $|d| < 0.69$. That is a reasonable public-facing approximation to what the replication distribution is already telling us.

![What you implicitly believe before the data. The flat/no-shrinkage line treats large effects as no less plausible than small effects; the Normal(0, 0.35) prior puts most mass on behavioral-science effects near zero.](_generated/figures/figure4_prior_comparison.png){{#fig-prior-comparison}}

Write the update the simple way:

$$
d \\sim N(0, \\tau^2), \\qquad \\hat d \\mid d, s \\sim N(d, s^2)
$$

$$
E[d \\mid \\hat d, s] = \\frac{{\\tau^2}}{{\\tau^2 + s^2}} \\hat d
$$

with $\\tau = 0.35$. For a balanced two-group design, a useful approximation is $s \\approx 2 / \\sqrt{{N}}$. That makes the reader-facing lesson immediate: large studies have small $s$, so the data dominate; small studies have large $s$, so the estimate shrinks hard toward zero. The prior does not make large effects impossible. It makes small-$N$ large effects earn their keep.

Take the kind of result this essay keeps attacking: a 40-person study reporting $\\hat d = 0.80$. Then $s \\approx 2 / \\sqrt{{40}} \\approx {s_small:.3f}$. Under the Normal$(0, 0.35)$ prior, the shrinkage weight is

$$
w = \\frac{{0.35^2}}{{0.35^2 + {s_small:.3f}^2}} \\approx {w_small:.2f}
$$

so the posterior mean is not $0.80$. It is about ${post_small:.2f}$. Run the same observed estimate at $N = 400$, where $s \\approx {s_large:.2f}$, and the weight rises to about {w_large:.2f}, giving a posterior mean of about ${post_large:.2f}$. That is the whole argument in one contrast. The prior is not saying “big effects never happen.” It is saying “a huge effect from a tiny study is mostly evidence about noise plus selection unless the underlying causal story is extraordinary.”

And that is exactly what the replication evidence shows. Small-$N$ literatures produce large selected estimates; larger replication attempts pull them back toward the effect-size range the world actually allows. Our Figure 2 estimate --- {repl['pct_shrunk_any']:.0f}% shrinking, {repl['pct_shrunk_below']:.0f}% shrinking below the original significance boundary, and about {repl['tenfold_reduction_pct']:.0f}% lower $D$ per 10x increase in $N$ --- is not a side fact. It is the empirical prior the rest of the paper is asking the reader to use.

Real large effects still exist. But when they are real, they look like vaccines, antibiotics, or other interventions whose targets visibly collapse under coarse measurement and large-scale replication, not like vague primes in 42 undergraduates. That is why the burden of evidence rises with the size of the claim. If a result is supposed to live in the thin tail of @fig-prior-comparison, then the evidence has to look tail-worthy too: large samples, hard outcomes, active controls, repeated success across sites, or effects obvious enough to see without statistical heroics.
""".strip()

    rebuilt = f"{heading}\n\n{body}\n\n"
    return markdown[:start] + rebuilt + markdown[end:]


def insert_replication_selection_callout(markdown: str, repl: dict[str, float | int]) -> str:
    callout = (
        "::: {.callout .blue}\n"
        "**Selection criteria for Figure 2.** We keep only recovered original/replication effect pairs where "
        "both sides have a usable common-metric effect size on our shared $D$ axis, both sample sizes are known "
        "and at least 10, and the replication attempt is larger than the original ($N_r > N_o$). We also collapse "
        "obvious site-level repeats to one row per original paper × replication study × endpoint anchor, using summed "
        "replication $N$ and an $N$-weighted replication $D$. The unit here is therefore a paper-endpoint pair, not a paper: the current "
        f"{int(repl['n_pairs']):,}-row table comes from {int(repl['n_unique_original_papers']):,} unique original papers, "
        f"and {int(repl['n_original_papers_multirow']):,} of those originals contribute more than one row. "
        "That many-to-one structure is expected because one original paper can contribute several claims or outcomes, "
        "and some claims are re-tested by multiple labs or samples.\n"
        ":::\n"
    )
    figure_block = r"(!\[.*?\]\(_generated/figures/figure2_replication_combined\.png\)\{#fig-replication-combined\})"
    if not re.search(figure_block, markdown, flags=re.DOTALL):
        return markdown
    return re.sub(figure_block, r"\1\n\n" + callout, markdown, count=1, flags=re.DOTALL)


def build_body(soup: BeautifulSoup, table_tokens: dict[str, str], figure_specs: dict[str, FigureSpec]) -> None:
    body_html = str(soup.body)
    proc = subprocess.run(
        ["pandoc", "-f", "html", "-t", "markdown-citations", "--wrap=none"],
        input=body_html,
        text=True,
        check=True,
        capture_output=True,
    )
    markdown = normalize_pandoc_markdown(proc.stdout)
    markdown = rewrite_opening_scenario(markdown)
    markdown = replace_figure_refs(markdown)

    for token, fragment in table_tokens.items():
        markdown = markdown.replace(token, fragment)
    for token, spec in figure_specs.items():
        markdown = markdown.replace(token, figure_markdown(spec))

    # Remove any leftover old draft figure token intentionally superseded by the combined figure.
    markdown = markdown.replace("FIGURE_TOKEN_03", "")
    markdown = restructure_sections(markdown)
    repl = replication_stats()
    markdown = rewrite_most_effects_section(markdown, repl)
    markdown = insert_replication_selection_callout(markdown, repl)
    markdown = re.sub(r"\n{3,}", "\n\n", markdown)
    BODY_QMD.write_text(markdown.strip() + "\n", encoding="utf-8")


def write_citation_audit(in_text: set[str], bibliography: set[str]) -> None:
    all_keys = sorted(in_text | bibliography)
    rows = [
        {
            "citekey": key,
            "in_text": key in in_text,
            "in_bibliography": key in bibliography,
            "status": "ok" if key in in_text and key in bibliography else "orphan_bib" if key in bibliography else "missing_bib",
        }
        for key in all_keys
    ]
    pd.DataFrame(rows).to_csv(CITATION_AUDIT, index=False)
    missing = [row["citekey"] for row in rows if row["status"] == "missing_bib"]
    if missing:
        raise RuntimeError(f"Missing bibliography entries for citekeys: {', '.join(missing[:20])}")


def main() -> None:
    ensure_dirs()
    html = DRAFT_HTML.read_text(encoding="utf-8")
    soup = BeautifulSoup(html, "html.parser")

    expected_figures = len(soup.select("div.figure"))
    expected_tables = len(soup.select("table"))
    expected_refs = len(soup.select("div.csl-entry"))
    if (expected_figures, expected_tables, expected_refs) != (6, 44, 219):
        raise RuntimeError(
            "Draft extraction count changed: "
            f"figures={expected_figures}, tables={expected_tables}, refs={expected_refs}"
        )

    bibliography = extract_bibliography(soup)
    in_text = replace_citation_spans(soup)
    write_citation_audit(in_text, bibliography)

    for selector in ["nav.doc-toc", "header#title-block-header", "div.byline", "script", "style"]:
        for node in soup.select(selector):
            node.decompose()
    refs = soup.select_one("#refs")
    if refs:
        refs.decompose()
    bib_heading = soup.find(id="bibliography")
    if bib_heading:
        bib_heading.decompose()

    repl = replication_stats()
    pub = published_stats()
    update_stale_prose(soup, repl, pub)
    table_tokens = extract_tables(soup)
    replace_old_figure_nodes(soup)
    figure_specs = generate_figures()
    build_body(soup, table_tokens, figure_specs)

    print(
        "Built paper assets: "
        f"{expected_figures} source figures, {expected_tables} tables, {expected_refs} references"
    )


if __name__ == "__main__":
    main()
