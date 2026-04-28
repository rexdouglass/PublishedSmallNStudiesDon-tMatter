#!/usr/bin/env python3
"""Build conservative Plot 3 rescue-candidate queues from local public-source pulls.

These outputs are deliberately *not* appended to strict Plot 3.  They turn the
large crash-note sources into auditable work queues with candidate D/N values
and a promotion status that records the remaining blocker.
"""

from __future__ import annotations

import math
import re
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DATASET_DIR = ROOT / "data" / "derived" / "effect_inflation_dataset"

SCHEEL_TSV = ROOT / "data" / "raw" / "corpus_candidates" / "scheel_2021" / "positive_results_in_registered_reports_data.tsv"
VDA_RAW = ROOT / "data" / "raw" / "corpus_candidates" / "vandenakker_pqnvr"
VDA_STATS = VDA_RAW / "Original_Stats.xlsx"
VDA_PVNP = VDA_RAW / "PvNP_Data.xlsx"
RPCB_EFFECTS = ROOT / "data" / "raw" / "corpus_candidates" / "rpcb" / "RP_CB Final Analysis - Effect level data.csv"

SCHEEL_OUT = DATASET_DIR / "plot3_scheel_quote_stat_rescue_candidates.csv"
VDA_OUT = DATASET_DIR / "plot3_vandenakker_first_stat_candidates.csv"
RPCB_OUT = DATASET_DIR / "plot3_rpcb_preclinical_paper_level_candidates.csv"
SUMMARY_OUT = DATASET_DIR / "plot3_rescue_candidate_summary.csv"

T_RE = re.compile(r"(?i)\bt\s*\(\s*(?P<df>\d+(?:\.\d+)?)\s*\)\s*[=≈]\s*(?P<t>-?\d+(?:\.\d+)?)")
F_RE = re.compile(
    r"(?i)\bF\s*\(\s*(?P<df1>\d+(?:\.\d+)?)\s*,\s*(?P<df2>\d+(?:\.\d+)?)\s*\)\s*[=≈]\s*(?P<f>-?\d+(?:\.\d+)?)"
)
D_RE = re.compile(r"(?i)(?:cohen'?s\s+)?\bd\s*[=≈]\s*(?P<d>-?\d+(?:\.\d+)?)")
N_RE = re.compile(r"(?i)\bN\s*[=≈]\s*(?P<n>\d{2,6})")
DN_PAIR_RE = re.compile(
    r"(?i)(?:cohen'?s\s+)?\bd\s*[=≈]\s*(?P<d>[−-]?\d+(?:\.\d+)?).{0,120}?\bN\s*[=≈]\s*(?P<n>\d{2,6})"
)


def num(value: object) -> float | None:
    if pd.isna(value):
        return None
    try:
        out = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(out):
        return None
    return out


def parse_float(value: str) -> float:
    return float(value.replace("−", "-"))


def d_from_t(t_value: float, df: float) -> float | None:
    if df <= 0:
        return None
    return abs(2 * t_value / math.sqrt(df))


def d_from_f(f_value: float, df1: float, df2: float) -> float | None:
    if df1 != 1 or df2 <= 0 or f_value < 0:
        return None
    return abs(2 * math.sqrt(f_value / df2))


def d_from_r(r_value: float) -> float | None:
    if abs(r_value) >= 1:
        return None
    return abs(2 * r_value / math.sqrt(1 - r_value**2))


def compact_text(parts: list[object]) -> str:
    return " ".join(" ".join(str(part).replace("\n", " ").split()) for part in parts if not pd.isna(part)).strip()


def build_scheel_candidates() -> pd.DataFrame:
    if not SCHEEL_TSV.exists():
        return pd.DataFrame()
    df = pd.read_csv(SCHEEL_TSV, sep="\t")
    rr = df[(df["is_RR"] == 1) & (df["include_in_analysis"] == 1)].copy()
    rows: list[dict[str, object]] = []

    for _, row in rr.iterrows():
        quote = compact_text([row.get("hypothesis_quote"), row.get("result_quote"), row.get("finding"), row.get("conclusion")])
        n_match = N_RE.search(quote)
        n_quote = int(n_match.group("n")) if n_match else None

        candidates: list[dict[str, object]] = []
        dn_pairs = list(DN_PAIR_RE.finditer(quote))
        if dn_pairs:
            for pair in dn_pairs:
                d_val = abs(parse_float(pair.group("d")))
                candidates.append(
                    {
                        "stat_type": "reported_d",
                        "stat_value": d_val,
                        "df1": None,
                        "df2": None,
                        "D_candidate": d_val,
                        "N_candidate": int(pair.group("n")),
                        "N_candidate_basis": "quote_d_n_pair",
                        "conversion_method": "reported_d",
                    }
                )
        else:
            d_match = D_RE.search(quote)
            if d_match:
                d_val = abs(parse_float(d_match.group("d")))
                candidates.append(
                    {
                        "stat_type": "reported_d",
                        "stat_value": d_val,
                        "df1": None,
                        "df2": None,
                        "D_candidate": d_val,
                        "N_candidate": n_quote,
                        "N_candidate_basis": "quote_N" if n_quote else "missing",
                        "conversion_method": "reported_d",
                    }
                )

        f_match = F_RE.search(quote)
        if f_match:
            df1 = float(f_match.group("df1"))
            df2 = float(f_match.group("df2"))
            f_val = float(f_match.group("f"))
            d_val = d_from_f(f_val, df1, df2)
            if d_val is not None:
                candidates.append(
                    {
                        "stat_type": "F",
                        "stat_value": f_val,
                        "df1": df1,
                        "df2": df2,
                        "D_candidate": d_val,
                        "N_candidate": n_quote or int(round(df2 + 2)),
                        "N_candidate_basis": "quote_N" if n_quote else "df2_plus_2_approx",
                        "conversion_method": "F_1_df_to_d",
                    }
                )

        t_match = T_RE.search(quote)
        if t_match:
            df_t = float(t_match.group("df"))
            t_val = float(t_match.group("t"))
            d_val = d_from_t(t_val, df_t)
            if d_val is not None:
                candidates.append(
                    {
                        "stat_type": "t",
                        "stat_value": t_val,
                        "df1": df_t,
                        "df2": None,
                        "D_candidate": d_val,
                        "N_candidate": n_quote or int(round(df_t + 2)),
                        "N_candidate_basis": "quote_N" if n_quote else "df_plus_2_approx",
                        "conversion_method": "t_df_to_d",
                    }
                )

        for i, candidate in enumerate(candidates, start=1):
            has_exact_n = candidate["N_candidate_basis"] in {"quote_N", "quote_d_n_pair"}
            rows.append(
                {
                    "candidate_id": f"scheel_rr_{int(row['id']):03d}_{i}",
                    "source_family": "Scheel et al. 2021 Registered Reports corpus",
                    "source_file": str(SCHEEL_TSV.relative_to(ROOT)),
                    "scheel_id": row.get("id"),
                    "title": row.get("title"),
                    "doi": row.get("doi"),
                    "support_binary": row.get("support_binary"),
                    "candidate_status": "needs_pdf_n_check" if not has_exact_n else "needs_pdf_focal_check",
                    "strict_append_ready": False,
                    "remaining_blocker": (
                        "N is approximated from test degrees of freedom; verify analytic N and first-hypothesis mapping in the article."
                        if not has_exact_n
                        else "Quote contains a candidate D/N, but article PDF still needs first-hypothesis and analytic-N verification."
                    ),
                    "quote": quote,
                    **candidate,
                }
            )

    out = pd.DataFrame(rows)
    if not out.empty:
        out = out.sort_values(["scheel_id", "candidate_id"]).reset_index(drop=True)
    return out


def build_vandenakker_candidates() -> pd.DataFrame:
    if not (VDA_STATS.exists() and VDA_PVNP.exists()):
        return pd.DataFrame()
    stats = pd.read_excel(VDA_STATS)
    pvnp = pd.read_excel(VDA_PVNP)
    stats = stats.reset_index(names="source_row")
    merged = stats.merge(
        pvnp[["ID", "TitleOriginal", "DOIOriginal", "JournalOriginal", "NOriginal", "PositiveOriginal"]],
        left_on="PSP",
        right_on="ID",
        how="left",
    )

    rows: list[dict[str, object]] = []
    for _, row in merged.iterrows():
        n = num(row.get("NOriginal"))
        if n is None or n <= 0:
            continue

        d_val = None
        method = None
        stat_type = None
        stat_value = None
        df1 = num(row.get("df1"))
        df2 = num(row.get("df2"))
        t_val = num(row.get("t"))
        f_val = num(row.get("F"))
        r_val = num(row.get("cor"))

        if t_val is not None and df1 is not None:
            d_val = d_from_t(t_val, df1)
            method = "t_df_to_d"
            stat_type = "t"
            stat_value = t_val
        elif f_val is not None and df1 == 1 and df2 is not None:
            d_val = d_from_f(f_val, df1, df2)
            method = "F_1_df_to_d"
            stat_type = "F"
            stat_value = f_val
        elif r_val is not None and abs(r_val) > 1e-12:
            d_val = d_from_r(r_val)
            method = "r_to_d"
            stat_type = "r"
            stat_value = r_val

        if d_val is None:
            continue
        rows.append(
            {
                "candidate_id": f"vandenakker_psp_{int(row['PSP']):03d}_row_{int(row['source_row']) + 2}",
                "source_family": "van den Akker preregistration-in-practice parsed original statistics",
                "source_file": str(VDA_STATS.relative_to(ROOT)),
                "PSP": row.get("PSP"),
                "source_row": int(row["source_row"]) + 2,
                "title": row.get("TitleOriginal"),
                "doi": row.get("DOIOriginal"),
                "journal": row.get("JournalOriginal"),
                "candidate_status": "stage_focal_selector_needed",
                "strict_append_ready": False,
                "remaining_blocker": "First convertible statistic per PSP is not yet proven to be the first preregistered confirmatory hypothesis; DOI-level deduplication is also pending.",
                "statistical_statement": compact_text([row.get("Statistical statement")]),
                "stat_type": stat_type,
                "stat_value": stat_value,
                "df1": df1,
                "df2": df2,
                "D_candidate": d_val,
                "N_candidate": n,
                "conversion_method": method,
                "positive_original": row.get("PositiveOriginal"),
            }
        )

    out = pd.DataFrame(rows)
    if out.empty:
        return out
    out = out.sort_values(["PSP", "source_row"]).drop_duplicates("PSP", keep="first").reset_index(drop=True)
    return out


def build_rpcb_candidates() -> pd.DataFrame:
    if not RPCB_EFFECTS.exists():
        return pd.DataFrame()
    df = pd.read_csv(RPCB_EFFECTS)
    rows = df[
        df["Replication sample size"].notna()
        & df["Replication effect size (SMD)"].notna()
        & df["Paper #"].notna()
    ].copy()
    rows = rows.sort_values(["Paper #", "Experiment #", "Effect #", "Internal replication #"])
    rows = rows.drop_duplicates("Paper #", keep="first").reset_index(drop=True)

    out = pd.DataFrame(
        {
            "candidate_id": rows["Paper #"].astype(int).map(lambda value: f"rpcb_paper_{value:02d}_first_effect"),
            "source_family": "Reproducibility Project: Cancer Biology Stage-2 Registered Report effects",
            "source_file": str(RPCB_EFFECTS.relative_to(ROOT)),
            "paper_number": rows["Paper #"],
            "experiment_number": rows["Experiment #"],
            "effect_number": rows["Effect #"],
            "effect_description": rows["Effect description"],
            "candidate_status": "preclinical_domain_stage",
            "strict_append_ready": False,
            "remaining_blocker": "D/N are row-ready, but the preclinical domain should be accepted explicitly or staged separately from the psychology/social-science strict layer.",
            "stat_type": rows["Effect size type (SMD)"],
            "stat_value": rows["Replication effect size (SMD)"],
            "D_candidate": rows["Replication effect size (SMD)"].abs(),
            "N_candidate": rows["Replication sample size"],
            "conversion_method": "reported_replication_smd",
            "replication_p_value": rows["Replication p value (SMD)"],
        }
    )
    return out


def write_outputs() -> None:
    DATASET_DIR.mkdir(parents=True, exist_ok=True)
    outputs = {
        "scheel_quote_stat_candidates": (build_scheel_candidates(), SCHEEL_OUT),
        "vandenakker_first_stat_candidates": (build_vandenakker_candidates(), VDA_OUT),
        "rpcb_preclinical_paper_level_candidates": (build_rpcb_candidates(), RPCB_OUT),
    }
    summary_rows = []
    for name, (df, path) in outputs.items():
        df.to_csv(path, index=False)
        summary_rows.append(
            {
                "candidate_table": name,
                "path": str(path.relative_to(ROOT)),
                "rows": len(df),
                "rows_with_D": int(df["D_candidate"].notna().sum()) if "D_candidate" in df else 0,
                "rows_with_N": int(df["N_candidate"].notna().sum()) if "N_candidate" in df else 0,
                "strict_append_ready": int(df["strict_append_ready"].sum()) if "strict_append_ready" in df else 0,
                "candidate_statuses": "; ".join(
                    f"{status}={count}"
                    for status, count in (
                        df["candidate_status"].value_counts().sort_index().items()
                        if "candidate_status" in df
                        else []
                    )
                ),
            }
        )
    pd.DataFrame(summary_rows).to_csv(SUMMARY_OUT, index=False)


def main() -> None:
    write_outputs()


if __name__ == "__main__":
    main()
