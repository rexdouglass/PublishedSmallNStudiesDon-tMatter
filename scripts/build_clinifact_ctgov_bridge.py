#!/usr/bin/env python3
"""Build a CliniFact x CT.gov bridge scaffold.

The goal is not to claim that registry rows equal journal-reported results.
Instead, this creates a concrete bridge object:

1. CliniFact provides primary-outcome claims linked to PMIDs.
2. The parsed CT.gov KG provides registry-side primary-outcome rows with N,
   p-values, parameter types/values, and matched intervention/comparator groups.

The output is a best-match table at the claim-publication level plus a wider
candidate-match table for auditing the join quality.
"""

from __future__ import annotations

import ast
import math
import re
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats


ROOT = Path(__file__).resolve().parents[1]
CLINIFACT_DIR = (
    ROOT
    / "data"
    / "raw"
    / "corpus_candidates"
    / "clinifact"
    / "CliniFact"
    / "data"
    / "processed"
    / "primary_outcome_publication_dataset"
)
CTGOV_PATH = ROOT / "data" / "raw" / "corpus_candidates" / "ctgov_kg" / "efficacy_df.csv"
OUT_DIR = ROOT / "data" / "derived" / "publication_bias_direct"

LABEL_MAP = {1: "positive", 0: "inconclusive", 2: "no_info"}
STOPWORDS = {
    "the",
    "a",
    "an",
    "and",
    "or",
    "of",
    "to",
    "in",
    "for",
    "from",
    "with",
    "at",
    "on",
    "by",
    "after",
    "before",
    "during",
    "vs",
    "versus",
    "up",
    "approximately",
    "about",
    "other",
    "participants",
    "participant",
    "number",
    "count",
    "change",
    "changes",
    "baseline",
    "post",
    "treatment",
    "follow",
    "followup",
}


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def parse_year(value: object) -> float:
    if pd.isna(value):
        return np.nan
    match = re.search(r"(19|20)\d{2}", str(value))
    return float(match.group(0)) if match else np.nan


def to_num(value: object) -> float:
    if pd.isna(value):
        return np.nan
    if isinstance(value, (int, float, np.number)):
        return float(value)
    text = str(value).strip()
    if not text:
        return np.nan
    match = re.search(r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:e[-+]?\d+)?", text)
    return float(match.group(0)) if match else np.nan


def parse_listish_text(value: object) -> str:
    if pd.isna(value):
        return ""
    text = str(value).strip()
    if not text:
        return ""
    if text.startswith("[") and text.endswith("]"):
        try:
            parsed = ast.literal_eval(text)
        except Exception:
            parsed = None
        if isinstance(parsed, list):
            return " ; ".join(str(x) for x in parsed if str(x).strip())
    return text


def normalize_text(value: object) -> str:
    text = parse_listish_text(value).lower()
    text = re.sub(r"\([^)]*\)", " ", text)
    text = re.sub(r"[^a-z0-9]+", " ", text)
    parts = [p for p in text.split() if p and p not in STOPWORDS]
    return " ".join(parts)


def token_set(value: object) -> set[str]:
    text = normalize_text(value)
    return set(text.split()) if text else set()


def jaccard(a: object, b: object) -> float:
    ta = token_set(a)
    tb = token_set(b)
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


def containment(a: object, b: object) -> float:
    ta = token_set(a)
    tb = token_set(b)
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / min(len(ta), len(tb))


def similarity(a: object, b: object) -> float:
    na = normalize_text(a)
    nb = normalize_text(b)
    if not na or not nb:
        return 0.0
    exact = 1.0 if na == nb else 0.0
    substring = 1.0 if (na in nb or nb in na) else 0.0
    return max(exact, substring, jaccard(na, nb), containment(na, nb))


def parse_p_scalar(value: object) -> tuple[float, str]:
    text = parse_listish_text(value).replace("≤", "<=").replace("≥", ">=").replace("−", "-")
    text = text.strip()
    if not text:
        return np.nan, ""
    match = re.search(
        r"(?i)(<=|>=|<|>|=)?\s*([.]?\d+(?:\.\d+)?(?:e[-+]?\d+)?)",
        text,
    )
    if not match:
        return np.nan, ""
    op = match.group(1) or ""
    p = to_num(match.group(2))
    if not np.isfinite(p):
        return np.nan, ""
    if p == 0:
        p = 1e-16
    if op in {">", ">="} or p >= 1:
        return np.nan, ""
    return float(p), op


def p_to_abs_z(p: float) -> float:
    if not np.isfinite(p) or p <= 0 or p >= 1:
        return np.nan
    return float(stats.norm.isf(p / 2))


def match_quality(row: pd.Series) -> str:
    if (
        row["outcome_similarity"] >= 0.95
        and row["intervention_similarity"] >= 0.8
        and row["comparator_similarity"] >= 0.8
    ):
        return "high_exactish"
    if row["outcome_similarity"] >= 0.75:
        return "high_outcome"
    if row["outcome_similarity"] >= 0.5:
        return "medium"
    return "weak"


def load_clinifact() -> pd.DataFrame:
    frames = []
    for split_name, fname in [
        ("train", "train_set.csv"),
        ("validation", "validation_set.csv"),
        ("test", "test_set.csv"),
    ]:
        df = pd.read_csv(CLINIFACT_DIR / fname)
        df["split"] = split_name
        frames.append(df)
    out = pd.concat(frames, ignore_index=True)
    out["claim_id"] = out["split"] + ":" + out["index"].astype(str)
    out["claim_support_label"] = out["label"].map(LABEL_MAP)
    out["publication_year"] = out["Publication Date"].map(parse_year)
    out["nctId"] = out["nctId"].astype(str)
    return out


def load_ctgov() -> pd.DataFrame:
    usecols = [
        "NCT_ID",
        "completion_year",
        "trial_phase",
        "enrollment_num",
        "funder_type",
        "outcome_id",
        "outcome_type",
        "outcome_title",
        "p_value",
        "method",
        "ci_lower_limit",
        "ci_upper_limit",
        "param_type",
        "param_value",
        "label",
        "intervention_group",
        "intervention_value",
        "comparator_group",
        "comparator_value",
    ]
    out = pd.read_csv(CTGOV_PATH, usecols=usecols, engine="python")
    out["NCT_ID"] = out["NCT_ID"].astype(str)
    out["enrollment_num"] = pd.to_numeric(out["enrollment_num"], errors="coerce")
    out["completion_year"] = pd.to_numeric(out["completion_year"], errors="coerce")
    out = out.rename(
        columns={
            "outcome_type": "ctgov_outcome_type",
            "outcome_title": "ctgov_outcome_title",
            "label": "ctgov_label",
        }
    )
    return out


def build_bridge() -> tuple[pd.DataFrame, pd.DataFrame, dict[str, object]]:
    clin = load_clinifact()
    ct = load_ctgov()

    overlap_ids = set(clin["nctId"].dropna()) & set(ct["NCT_ID"].dropna())
    clin_overlap = clin[clin["nctId"].isin(overlap_ids)].copy()
    ct_overlap = ct[ct["NCT_ID"].isin(overlap_ids)].copy()

    merged = clin_overlap.merge(
        ct_overlap,
        left_on="nctId",
        right_on="NCT_ID",
        how="left",
        suffixes=("_clin", "_ct"),
    )

    merged["ct_primary_flag"] = merged["ctgov_outcome_type"].astype(str).str.upper().eq("PRIMARY")
    merged["outcome_similarity"] = merged.apply(
        lambda r: max(
            similarity(r["outcome_title"], r["ctgov_outcome_title"]),
            similarity(r["claim"], r["ctgov_outcome_title"]),
            similarity(r["outcome_description"], r["ctgov_outcome_title"]),
        ),
        axis=1,
    )
    merged["intervention_similarity"] = merged.apply(
        lambda r: max(
            similarity(r["intervention_group_title"], r["intervention_group"]),
            similarity(r["intervention_group_intervention_label"], r["intervention_value"]),
            similarity(r["intervention_group_description"], r["intervention_group"]),
        ),
        axis=1,
    )
    merged["comparator_similarity"] = merged.apply(
        lambda r: max(
            similarity(r["comparator_group_title"], r["comparator_group"]),
            similarity(r["comparator_group_intervention_label"], r["comparator_value"]),
            similarity(r["comparator_group_description"], r["comparator_group"]),
        ),
        axis=1,
    )
    merged["combined_match_score"] = (
        2.0 * merged["outcome_similarity"]
        + 0.75 * merged["intervention_similarity"]
        + 0.75 * merged["comparator_similarity"]
        + 0.25 * merged["ct_primary_flag"].astype(float)
    )
    merged["match_quality"] = merged.apply(match_quality, axis=1)

    parsed_p = merged["p_value"].map(parse_p_scalar)
    merged["registry_p"] = [x[0] for x in parsed_p]
    merged["registry_p_operator"] = [x[1] for x in parsed_p]
    merged["registry_abs_z"] = merged["registry_p"].map(p_to_abs_z)
    merged["registry_d_proxy"] = 2 * merged["registry_abs_z"] / np.sqrt(merged["enrollment_num"])

    merged["claim_support_positive"] = merged["claim_support_label"].eq("positive")
    merged["registry_label_positive"] = merged["ctgov_label"].astype(str).str.lower().eq("positive")

    merged = merged.sort_values(
        [
            "claim_id",
            "ct_primary_flag",
            "combined_match_score",
            "outcome_similarity",
            "intervention_similarity",
            "comparator_similarity",
        ],
        ascending=[True, False, False, False, False, False],
    )

    best = merged.groupby("claim_id", as_index=False).head(1).copy()
    best["score_rank_within_claim"] = 1

    summary = {
        "clinifact_rows": int(len(clin)),
        "clinifact_unique_nct": int(clin["nctId"].nunique()),
        "clinifact_unique_pmid": int(clin["PMID"].nunique()),
        "ctgov_rows": int(len(ct)),
        "ctgov_unique_nct": int(ct["NCT_ID"].nunique()),
        "overlap_nct": int(len(overlap_ids)),
        "overlap_claim_rows": int(len(clin_overlap)),
        "candidate_match_rows": int(len(merged)),
        "best_match_rows": int(len(best)),
        "best_primary_rows": int(best["ct_primary_flag"].sum()),
        "best_rows_with_registry_p": int(best["registry_p"].notna().sum()),
        "best_rows_with_registry_d_proxy": int(best["registry_d_proxy"].notna().sum()),
        "best_high_exactish": int(best["match_quality"].eq("high_exactish").sum()),
        "best_high_outcome": int(best["match_quality"].eq("high_outcome").sum()),
        "best_medium": int(best["match_quality"].eq("medium").sum()),
        "best_weak": int(best["match_quality"].eq("weak").sum()),
    }

    return merged, best, summary


def write_summary(best: pd.DataFrame, summary: dict[str, object]) -> None:
    lines = [
        "# CliniFact x CT.gov Bridge",
        "",
        "Last updated: 2026-04-20",
        "",
        "This scaffold links CliniFact primary-outcome publication claims to the",
        "parsed CT.gov efficacy rows by NCT ID, then picks the best registry-side",
        "candidate match using outcome-title and arm-label similarity.",
        "",
        "## Counts",
        "",
        f"- CliniFact claim-publication rows: {summary['clinifact_rows']:,}",
        f"- Unique CliniFact NCT IDs: {summary['clinifact_unique_nct']:,}",
        f"- Unique CliniFact PMIDs: {summary['clinifact_unique_pmid']:,}",
        f"- CT.gov KG rows loaded: {summary['ctgov_rows']:,}",
        f"- Unique CT.gov KG NCT IDs: {summary['ctgov_unique_nct']:,}",
        f"- Exact NCT overlap: {summary['overlap_nct']:,}",
        f"- CliniFact rows on overlapping NCT IDs: {summary['overlap_claim_rows']:,}",
        f"- Candidate merged rows: {summary['candidate_match_rows']:,}",
        f"- Best-match rows: {summary['best_match_rows']:,}",
        f"- Best matches on CT.gov primary outcomes: {summary['best_primary_rows']:,}",
        f"- Best matches with registry p-values: {summary['best_rows_with_registry_p']:,}",
        f"- Best matches with registry D proxy: {summary['best_rows_with_registry_d_proxy']:,}",
        "",
        "## Best-Match Quality",
        "",
        f"- `high_exactish`: {summary['best_high_exactish']:,}",
        f"- `high_outcome`: {summary['best_high_outcome']:,}",
        f"- `medium`: {summary['best_medium']:,}",
        f"- `weak`: {summary['best_weak']:,}",
        "",
        "## Notes",
        "",
        "- This is a bridge/scaffold, not a finished publication-bias corpus.",
        "- The CT.gov side contributes registry-side primary outcome rows with",
        "  enrollment and p-values; the CliniFact side contributes linked PMIDs,",
        "  abstracts, and claim polarity labels.",
        "- The registry D proxy is `2*|z|/sqrt(enrollment_num)` from CT.gov",
        "  p-values, not a journal-side effect size.",
        "- The next step is to use the linked PMIDs to extract or audit the",
        "  journal-side numeric result for the matched primary outcome.",
        "",
        "## Output Files",
        "",
        "- `data/derived/publication_bias_direct/clinifact_ctgov_bridge_candidate_matches.csv.gz`",
        "- `data/derived/publication_bias_direct/clinifact_ctgov_bridge_candidate_matches.parquet`",
        "- `data/derived/publication_bias_direct/clinifact_ctgov_bridge_best_matches.csv`",
        "- `data/derived/publication_bias_direct/clinifact_ctgov_bridge_best_matches.parquet`",
        "- `data/derived/publication_bias_direct/clinifact_ctgov_bridge_summary.md`",
    ]

    if not best.empty:
        quality = (
            best.groupby("match_quality", dropna=False)["registry_d_proxy"]
            .agg(["count", "median"])
            .reset_index()
        )
        lines.extend(["", "## Registry D Proxy By Match Quality", ""])
        for _, row in quality.iterrows():
            med = row["median"]
            med_text = "NA" if pd.isna(med) else f"{med:.3f}"
            lines.append(f"- `{row['match_quality']}`: n={int(row['count'])}, median registry D proxy={med_text}")

    (OUT_DIR / "clinifact_ctgov_bridge_summary.md").write_text("\n".join(lines) + "\n")


def main() -> None:
    ensure_dir(OUT_DIR)
    candidates, best, summary = build_bridge()

    candidate_cols = [
        "claim_id",
        "split",
        "nctId",
        "PMID",
        "publication_year",
        "claim_support_label",
        "claim",
        "article_title",
        "outcome_title",
        "outcome_description",
        "intervention_group_title",
        "comparator_group_title",
        "NCT_ID",
        "outcome_id",
        "ctgov_outcome_type",
        "ctgov_outcome_title",
        "trial_phase",
        "completion_year",
        "funder_type",
        "enrollment_num",
        "p_value",
        "registry_p",
        "registry_abs_z",
        "registry_d_proxy",
        "param_type",
        "param_value",
        "method",
        "ctgov_label",
        "intervention_group",
        "intervention_value",
        "comparator_group",
        "comparator_value",
        "ct_primary_flag",
        "outcome_similarity",
        "intervention_similarity",
        "comparator_similarity",
        "combined_match_score",
        "match_quality",
    ]
    rename_map = {
        "outcome_title": "clinifact_outcome_title",
        "ctgov_outcome_type": "outcome_type",
        "ctgov_outcome_title": "outcome_title",
    }

    candidates = candidates[candidate_cols].rename(columns=rename_map)
    best = best[candidate_cols].rename(columns=rename_map)

    candidates.to_csv(OUT_DIR / "clinifact_ctgov_bridge_candidate_matches.csv.gz", index=False)
    candidates.to_parquet(OUT_DIR / "clinifact_ctgov_bridge_candidate_matches.parquet", index=False)
    best.to_csv(OUT_DIR / "clinifact_ctgov_bridge_best_matches.csv", index=False)
    best.to_parquet(OUT_DIR / "clinifact_ctgov_bridge_best_matches.parquet", index=False)
    write_summary(best, summary)
    print(f"Wrote {len(best):,} best matches and {len(candidates):,} candidate matches to {OUT_DIR}")


if __name__ == "__main__":
    main()
