#!/usr/bin/env python3
"""Extract first-pass journal-side numerics from CliniFact result-PMID abstracts.

This is intentionally conservative. It does not claim that every linked PMID is a
valid trial-result publication. Instead, it:

1. Starts from the CliniFact x CT.gov bridge best matches.
2. Keeps only CliniFact rows whose PMID is a result reference
   (`claim_support_label` in {positive, inconclusive}).
3. Adds publication-link plausibility flags.
4. Extracts abstract-side p-values, confidence intervals, common ratio estimates,
   and sample-size candidates.
5. Computes journal-side z and D proxies when possible.

The result is a bridge-ready journal-side scaffold, not a finished publication-
bias corpus.
"""

from __future__ import annotations

import math
import re
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats


ROOT = Path(__file__).resolve().parents[1]
BRIDGE_PATH = ROOT / "data" / "derived" / "publication_bias_direct" / "clinifact_ctgov_bridge_best_matches.csv"
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
OUT_DIR = ROOT / "data" / "derived" / "publication_bias_direct"

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
    "up",
    "vs",
    "versus",
    "group",
    "groups",
    "baseline",
    "change",
    "changes",
    "score",
    "scores",
    "mean",
    "week",
    "weeks",
    "month",
    "months",
    "day",
    "days",
    "participants",
    "participant",
    "patients",
    "patient",
    "subjects",
    "subject",
    "treatment",
    "study",
}

TRIAL_MARKER_RE = re.compile(
    r"(?i)\b(randomi[sz]ed|clinical trial|double[- ]blind|single[- ]blind|placebo|controlled trial|multicenter|parallel-group|parallel group|assigned at random)\b"
)
REVIEW_MARKER_RE = re.compile(
    r"(?i)\b(systematic review|meta-analysis|meta analysis|review of|literature review|evidence-based guidelines|guideline|commentary|editorial)\b"
)
P_RE = re.compile(r"(?i)\bp(?:-value)?\s*(<=|>=|=|<|>)\s*([.]?\d+(?:\.\d+)?(?:e[-+]?\d+)?)")
CI_RE = re.compile(
    r"(?i)(90|95|99)\s*%?\s*(?:confidence interval|CI)\s*[,(:;\[]*\s*"
    r"([-+]?\d*\.?\d+)\s*(?:to|–|-|—)\s*([-+]?\d*\.?\d+)"
)
N_EQ_RE = re.compile(r"(?i)\bn\s*[=~]\s*(\d{2,6})\b")
N_GROUP_RE = re.compile(r"(?i)\b(\d{2,6})\s+(participants|patients|subjects|adults|children|women|men|volunteers|people|individuals|residents)\b")

EFFECT_PATTERNS = [
    ("HR", re.compile(r"(?:\b(?i:hazard ratio)\b|\bHR\b)\s*(?:\[[A-Z]+\]|\([A-Z]+\))?\s*[:=,]?\s*([-+]?\d*\.?\d+)")),
    ("OR", re.compile(r"(?:\b(?i:odds ratio)\b|\bOR\b)\s*(?:\[[A-Z]+\]|\([A-Z]+\))?\s*[:=,]?\s*([-+]?\d*\.?\d+)")),
    ("RR", re.compile(r"(?:\b(?i:risk ratio|relative risk)\b|\bRR\b)\s*(?:\[[A-Z]+\]|\([A-Z]+\))?\s*[:=,]?\s*([-+]?\d*\.?\d+)")),
    ("IRR", re.compile(r"(?:\b(?i:incidence rate ratio|rate ratio)\b|\bIRR\b)\s*(?:\[[A-Z]+\]|\([A-Z]+\))?\s*[:=,]?\s*([-+]?\d*\.?\d+)")),
    ("MD", re.compile(r"\b(?i:mean difference|least-squares mean difference|least squares mean difference|between-group difference|between group difference|estimated treatment difference)\b\s*[:=,]?\s*([-+]?\d*\.?\d+)")),
]


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def clean_text(value: object) -> str:
    if pd.isna(value):
        return ""
    text = (
        str(value)
        .replace("\xa0", " ")
        .replace(" ", " ")
        .replace("–", "-")
        .replace("—", "-")
        .replace("−", "-")
        .replace("·", ".")
        .replace("∙", ".")
    )
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def normalize_text(value: object) -> str:
    text = clean_text(value).lower()
    text = re.sub(r"\([^)]*\)", " ", text)
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return " ".join(token for token in text.split() if token and token not in STOPWORDS)


def token_set(value: object) -> set[str]:
    text = normalize_text(value)
    return set(text.split()) if text else set()


def overlap_score(sentence: str, value: object) -> float:
    sent_tokens = token_set(sentence)
    query_tokens = token_set(value)
    if not sent_tokens or not query_tokens:
        return 0.0
    inter = sent_tokens & query_tokens
    return len(inter) / len(query_tokens)


def split_sentences(text: str) -> list[str]:
    clean = clean_text(text)
    if not clean:
        return []
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9])|\n+", clean)
    return [p.strip() for p in parts if p and p.strip()]


def sentence_score(sentence: str, row: pd.Series) -> float:
    score = 0.0
    score += 3.0 * max(
        overlap_score(sentence, row.get("clinifact_outcome_title")),
        overlap_score(sentence, row.get("outcome_title")),
    )
    score += 1.0 * overlap_score(sentence, row.get("intervention_group_title"))
    score += 1.0 * overlap_score(sentence, row.get("comparator_group_title"))
    if re.search(r"(?i)\b(primary outcome|primary endpoint|primary end point|main outcome)\b", sentence):
        score += 0.75
    if P_RE.search(sentence):
        score += 0.5
    if CI_RE.search(sentence):
        score += 0.3
    if re.search(r"(?i)\b(results?|conclusion|conclusions)\b", sentence):
        score += 0.15
    return score


def select_best_sentence(text: str, row: pd.Series) -> tuple[str, float]:
    sentences = split_sentences(text)
    if not sentences:
        return "", 0.0
    scored = [(sentence_score(sent, row), sent) for sent in sentences]
    scored.sort(key=lambda x: (x[0], len(x[1])), reverse=True)
    best_score, best_sentence = scored[0]
    return best_sentence, float(best_score)


def parse_p_matches(text: str) -> list[tuple[float, str, str]]:
    out: list[tuple[float, str, str]] = []
    for match in P_RE.finditer(clean_text(text)):
        op = match.group(1)
        raw = match.group(2)
        try:
            p = float(raw)
        except ValueError:
            continue
        if p == 0:
            p = 1e-16
        if p <= 0 or p >= 1:
            continue
        out.append((p, op, match.group(0)))
    return out


def choose_p_value(best_sentence: str, abstract: str) -> tuple[float, str, str, str]:
    best_matches = parse_p_matches(best_sentence)
    if best_matches:
        p, op, raw = best_matches[0]
        return p, op, "best_sentence", raw
    abs_matches = parse_p_matches(abstract)
    if abs_matches:
        p, op, raw = abs_matches[0]
        return p, op, "full_abstract", raw
    return np.nan, "", "missing", ""


def parse_ci(text: str) -> tuple[float, float, float, str]:
    for match in CI_RE.finditer(clean_text(text)):
        level = float(match.group(1))
        low = float(match.group(2))
        high = float(match.group(3))
        return level, low, high, match.group(0)
    return np.nan, np.nan, np.nan, ""


def choose_ci(best_sentence: str, abstract: str) -> tuple[float, float, float, str, str]:
    level, low, high, raw = parse_ci(best_sentence)
    if np.isfinite(level):
        return level, low, high, "best_sentence", raw
    level, low, high, raw = parse_ci(abstract)
    if np.isfinite(level):
        return level, low, high, "full_abstract", raw
    return np.nan, np.nan, np.nan, "missing", ""


def parse_effect(text: str) -> tuple[str, float, str]:
    clean = clean_text(text)
    for metric, pattern in EFFECT_PATTERNS:
        match = pattern.search(clean)
        if match:
            return metric, float(match.group(1)), match.group(0)
    return "", np.nan, ""


def choose_effect(best_sentence: str, abstract: str) -> tuple[str, float, str, str]:
    metric, value, raw = parse_effect(best_sentence)
    if metric:
        return metric, value, "best_sentence", raw
    metric, value, raw = parse_effect(abstract)
    if metric:
        return metric, value, "full_abstract", raw
    return "", np.nan, "missing", ""


def extract_n_candidates(text: str) -> list[tuple[int, str, str]]:
    clean = clean_text(text)
    candidates: list[tuple[int, str, str]] = []
    for match in N_EQ_RE.finditer(clean):
        value = int(match.group(1))
        if 10 <= value <= 500000:
            candidates.append((value, "n_equals", match.group(0)))
    for match in N_GROUP_RE.finditer(clean):
        value = int(match.group(1))
        if 10 <= value <= 500000:
            candidates.append((value, "participant_count", match.group(0)))
    return candidates


def choose_n(candidates: list[tuple[int, str, str]], enrollment: float) -> tuple[float, str, str]:
    if not candidates:
        return np.nan, "missing", ""

    vals = [(int(v), src, raw) for v, src, raw in candidates]
    enrollment_ok = pd.notna(enrollment) and enrollment > 0

    if enrollment_ok:
        target = float(enrollment)
        dedup_vals = list(dict.fromkeys(v for v, _, _ in vals))
        small = [v for v in dedup_vals if v < target * 1.05]
        for k in (2, 3, 4):
            if len(small) >= k:
                best_combo = None
                best_gap = float("inf")
                for combo in combinations(small[:8], k):
                    total = sum(combo)
                    gap = abs(total - target)
                    if gap < best_gap:
                        best_combo = combo
                        best_gap = gap
                if best_combo is not None and best_gap <= max(5.0, 0.08 * target):
                    return float(sum(best_combo)), f"arm_sum_{k}", " + ".join(str(x) for x in best_combo)

        best_val, best_src, best_raw = min(vals, key=lambda x: abs(x[0] - target))
        if abs(best_val - target) <= max(5.0, 0.15 * target):
            return float(best_val), f"{best_src}_closest_to_registry", best_raw

    best_val, best_src, best_raw = max(vals, key=lambda x: x[0])
    return float(best_val), f"{best_src}_max_fallback", best_raw


def p_to_abs_z(p: float) -> float:
    if not np.isfinite(p) or p <= 0 or p >= 1:
        return np.nan
    return float(stats.norm.isf(p / 2))


def classify_link(row: pd.Series, title: str, abstract: str) -> str:
    year_ok = bool(pd.notna(row.get("publication_year")) and pd.notna(row.get("completion_year")) and row["publication_year"] + 1 >= row["completion_year"])
    combined = f"{title} {abstract}"
    has_trial_markers = bool(TRIAL_MARKER_RE.search(combined))
    looks_review = bool(REVIEW_MARKER_RE.search(combined))

    if not year_ok:
        return "suspect_precompletion"
    if looks_review:
        return "suspect_review_like"
    if has_trial_markers:
        return "plausible_result_report"
    return "possible_result_report"


def load_clinifact() -> pd.DataFrame:
    frames = []
    for split_name, fname in [
        ("train", "train_set.csv"),
        ("validation", "validation_set.csv"),
        ("test", "test_set.csv"),
    ]:
        df = pd.read_csv(CLINIFACT_DIR / fname)
        df["split"] = split_name
        df["claim_id"] = df["split"] + ":" + df["index"].astype(str)
        frames.append(df)
    return pd.concat(frames, ignore_index=True)


def build_extract() -> pd.DataFrame:
    bridge = pd.read_csv(BRIDGE_PATH)
    clinifact = load_clinifact()
    df = bridge.merge(
        clinifact[
            [
                "claim_id",
                "article_title",
                "article_abstract",
                "pValues",
                "statisticalMethods",
                "nonInferiorityTypes",
            ]
        ],
        on="claim_id",
        how="left",
        suffixes=("", "_cf"),
    )

    # Keep only rows with result PMIDs. In CliniFact, `no_info` rows are
    # background references rather than result publications.
    df = df[df["claim_support_label"].isin(["positive", "inconclusive"])].copy()

    records: list[dict] = []
    for _, row in df.iterrows():
        title = clean_text(row.get("article_title_cf") or row.get("article_title"))
        abstract = clean_text(row.get("article_abstract"))
        best_sentence, best_score = select_best_sentence(abstract, row)
        p_value, p_op, p_source, p_raw = choose_p_value(best_sentence, abstract)
        ci_level, ci_low, ci_high, ci_source, ci_raw = choose_ci(best_sentence, abstract)
        effect_metric, effect_value, effect_source, effect_raw = choose_effect(best_sentence, abstract)
        n_candidates = extract_n_candidates(f"{title} {abstract}")
        n_selected, n_source, n_raw = choose_n(n_candidates, row.get("enrollment_num"))
        abs_z = p_to_abs_z(p_value)
        d_from_selected_n = 2 * abs_z / math.sqrt(n_selected) if np.isfinite(abs_z) and np.isfinite(n_selected) and n_selected > 0 else np.nan
        d_from_registry_n = 2 * abs_z / math.sqrt(row["enrollment_num"]) if np.isfinite(abs_z) and pd.notna(row.get("enrollment_num")) and row["enrollment_num"] > 0 else np.nan
        link_class = classify_link(row, title, abstract)
        trial_markers = bool(TRIAL_MARKER_RE.search(f"{title} {abstract}"))
        review_markers = bool(REVIEW_MARKER_RE.search(f"{title} {abstract}"))
        year_ok = bool(pd.notna(row.get("publication_year")) and pd.notna(row.get("completion_year")) and row["publication_year"] + 1 >= row["completion_year"])

        records.append(
            {
                "claim_id": row["claim_id"],
                "split": row["split"],
                "nctId": row["nctId"],
                "PMID": row["PMID"],
                "claim_support_label": row["claim_support_label"],
                "publication_year": row["publication_year"],
                "completion_year": row["completion_year"],
                "publication_minus_completion_years": row["publication_year"] - row["completion_year"] if pd.notna(row.get("publication_year")) and pd.notna(row.get("completion_year")) else np.nan,
                "match_quality": row["match_quality"],
                "combined_match_score": row["combined_match_score"],
                "outcome_similarity": row["outcome_similarity"],
                "intervention_similarity": row["intervention_similarity"],
                "comparator_similarity": row["comparator_similarity"],
                "publication_year_plausible": year_ok,
                "trial_design_markers": trial_markers,
                "review_like_markers": review_markers,
                "publication_link_plausibility": link_class,
                "article_title": title,
                "article_abstract": abstract,
                "selected_sentence": best_sentence,
                "selected_sentence_score": best_score,
                "journal_p": p_value,
                "journal_p_operator": p_op,
                "journal_p_source": p_source,
                "journal_p_raw": p_raw,
                "journal_abs_z_from_p": abs_z,
                "journal_n_selected": n_selected,
                "journal_n_source": n_source,
                "journal_n_raw": n_raw,
                "journal_d_proxy_from_p_and_selected_n": d_from_selected_n,
                "journal_d_proxy_from_p_and_registry_n": d_from_registry_n,
                "journal_ci_level": ci_level,
                "journal_ci_lower": ci_low,
                "journal_ci_upper": ci_high,
                "journal_ci_source": ci_source,
                "journal_ci_raw": ci_raw,
                "journal_effect_metric": effect_metric,
                "journal_effect_value": effect_value,
                "journal_effect_source": effect_source,
                "journal_effect_raw": effect_raw,
                "registry_p": row.get("registry_p"),
                "registry_abs_z": row.get("registry_abs_z"),
                "registry_d_proxy": row.get("registry_d_proxy"),
                "registry_param_type": row.get("param_type"),
                "registry_param_value": row.get("param_value"),
                "registry_method": row.get("method"),
                "enrollment_num": row.get("enrollment_num"),
                "trial_phase": row.get("trial_phase"),
                "funder_type": row.get("funder_type"),
                "clinifact_outcome_title": row.get("clinifact_outcome_title"),
                "registry_outcome_title": row.get("outcome_title"),
                "outcome_description": row.get("outcome_description"),
                "intervention_group_title": row.get("intervention_group_title"),
                "comparator_group_title": row.get("comparator_group_title"),
                "pValues_registry_metadata": row.get("pValues"),
                "statisticalMethods_registry_metadata": row.get("statisticalMethods"),
                "nonInferiorityTypes_registry_metadata": row.get("nonInferiorityTypes"),
            }
        )

    return pd.DataFrame.from_records(records)


def write_summary(df: pd.DataFrame) -> None:
    plausible = df["publication_link_plausibility"].isin(["plausible_result_report", "possible_result_report"])
    lines = [
        "# CliniFact Journal-Side Numeric Extract",
        "",
        "Last updated: 2026-04-20",
        "",
        "This pass extracts first-pass journal-side numerics from CliniFact result-",
        "PMID rows linked to registry primary outcomes through the bridge. It is an",
        "abstract-only scaffold with explicit plausibility flags.",
        "",
        "## Counts",
        "",
        f"- Result-PMID rows processed: {len(df):,}",
        f"- Rows with plausible publication year (`publication_year + 1 >= completion_year`): {int(df['publication_year_plausible'].sum()):,}",
        f"- Rows with trial-design markers in title/abstract: {int(df['trial_design_markers'].sum()):,}",
        f"- Rows flagged review-like: {int(df['review_like_markers'].sum()):,}",
        f"- Rows classified `plausible_result_report`: {int(df['publication_link_plausibility'].eq('plausible_result_report').sum()):,}",
        f"- Rows classified `possible_result_report`: {int(df['publication_link_plausibility'].eq('possible_result_report').sum()):,}",
        f"- Rows classified `suspect_review_like`: {int(df['publication_link_plausibility'].eq('suspect_review_like').sum()):,}",
        f"- Rows classified `suspect_precompletion`: {int(df['publication_link_plausibility'].eq('suspect_precompletion').sum()):,}",
        "",
        "## Abstract Numeric Coverage",
        "",
        f"- Rows with journal p-values: {int(df['journal_p'].notna().sum()):,}",
        f"- Rows with abstract-selected N: {int(df['journal_n_selected'].notna().sum()):,}",
        f"- Rows with both journal p and abstract N: {int((df['journal_p'].notna() & df['journal_n_selected'].notna()).sum()):,}",
        f"- Rows with journal D proxy using abstract N: {int(df['journal_d_proxy_from_p_and_selected_n'].notna().sum()):,}",
        f"- Rows with journal D proxy using registry N fallback: {int(df['journal_d_proxy_from_p_and_registry_n'].notna().sum()):,}",
        f"- Rows with CI extracted: {int(df['journal_ci_level'].notna().sum()):,}",
        f"- Rows with effect estimate extracted: {int(df['journal_effect_value'].notna().sum()):,}",
        "",
        "## Plausible-Result Subset",
        "",
        f"- Plausible rows (`plausible_result_report` or `possible_result_report`): {int(plausible.sum()):,}",
        f"- Plausible rows with journal p-values: {int((plausible & df['journal_p'].notna()).sum()):,}",
        f"- Plausible rows with abstract-selected N: {int((plausible & df['journal_n_selected'].notna()).sum()):,}",
        f"- Plausible rows with abstract D proxy: {int((plausible & df['journal_d_proxy_from_p_and_selected_n'].notna()).sum()):,}",
        "",
        "## Notes",
        "",
        "- `claim_support_label` is restricted to `positive` or `inconclusive`, which",
        "  correspond to CliniFact result-PMID rows. `no_info` rows are background",
        "  references and are excluded here.",
        "- `publication_link_plausibility` is heuristic. It is meant to separate",
        "  likely result papers from obvious review-like or pre-completion links.",
        "- The journal-side D proxy is based on abstract p-values and either an",
        "  abstract-selected N or registry enrollment as fallback.",
        "- The extracted effect metric is deliberately narrow and only covers common",
        "  abstract patterns like HR/OR/RR/MD.",
        "",
        "## Output Files",
        "",
        "- `data/derived/publication_bias_direct/clinifact_publication_numeric_extract.csv`",
        "- `data/derived/publication_bias_direct/clinifact_publication_numeric_extract.parquet`",
        "- `data/derived/publication_bias_direct/clinifact_publication_numeric_extract_plausible.csv`",
        "- `data/derived/publication_bias_direct/clinifact_publication_numeric_extract_summary.md`",
    ]
    (OUT_DIR / "clinifact_publication_numeric_extract_summary.md").write_text("\n".join(lines) + "\n")


def main() -> None:
    ensure_dir(OUT_DIR)
    df = build_extract()
    plausible = df[df["publication_link_plausibility"].isin(["plausible_result_report", "possible_result_report"])].copy()
    df.to_csv(OUT_DIR / "clinifact_publication_numeric_extract.csv", index=False)
    df.to_parquet(OUT_DIR / "clinifact_publication_numeric_extract.parquet", index=False)
    plausible.to_csv(OUT_DIR / "clinifact_publication_numeric_extract_plausible.csv", index=False)
    write_summary(df)
    print(
        "Wrote "
        f"{len(df):,} journal-side result-PMID rows and {len(plausible):,} plausible result-report rows "
        f"to {OUT_DIR}"
    )


if __name__ == "__main__":
    main()
