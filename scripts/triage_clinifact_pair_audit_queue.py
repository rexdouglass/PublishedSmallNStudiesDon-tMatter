#!/usr/bin/env python3
"""Heuristic triage for the CliniFact journal-vs-registry audit queue."""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
IN_PATH = ROOT / "data" / "derived" / "publication_bias_direct" / "clinifact_publication_registry_pairs.csv"
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

COMPARE_RE = re.compile(
    r"(?i)\b(?:compared with|compared to|versus|vs\.?|than placebo|than control|than standard|more than|less than|greater than|lower than|difference\b|non-inferior|superior|inferior|ratio\b)\b"
)
BASELINE_RE = re.compile(
    r"(?i)\b(?:from baseline|change from baseline|compared with baseline|compared to baseline|baseline to|at \d+ (?:weeks?|months?|days?) compared to baseline)\b"
)
ASSOCIATION_RE = re.compile(
    r"(?i)\b(?:associated with|correlated with|correlation|predictor|relationship|inverse correlation)\b"
)
STRUCTURAL_RE = re.compile(
    r"(?i)^(?:the\s+)?(?:objective|objectives|aim|aims|purpose|purposes|methods|method|design|intervention|main outcome measures|main outcomes and measures|research design and methods|patients and methods)\b"
)
CONCLUSION_RE = re.compile(r"(?i)^(?:conclusion|conclusions|interpretation)\b")
RESULTS_RE = re.compile(r"(?i)^results?:")
BOTH_GROUPS_RE = re.compile(r"(?i)\b(?:in both groups|both groups)\b")
FRAGMENT_RE = re.compile(r"^[^A-Za-z]*\d")
P_RE = re.compile(r"(?i)\bp(?:-value)?\s*(<=|>=|=|<|>)\s*([.]?\d+(?:\.\d+)?(?:e[-+]?\d+)?)")


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def normalize_text(value: object) -> str:
    text = str(value).lower()
    text = re.sub(r"\([^)]*\)", " ", text)
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return " ".join(token for token in text.split() if token and token not in STOPWORDS)


def token_set(value: object) -> set[str]:
    text = normalize_text(value)
    return set(text.split()) if text else set()


def outcome_overlap(sentence: str, a: object, b: object) -> float:
    sent = token_set(sentence)
    if not sent:
        return 0.0
    best = 0.0
    for value in (a, b):
        tgt = token_set(value)
        if tgt:
            best = max(best, len(sent & tgt) / len(tgt))
    return best


def p_count(text: str) -> int:
    return len(P_RE.findall(str(text)))


def build_triage() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    df = pd.read_csv(IN_PATH)
    df = df[df["pair_quality"].isin(["high", "medium"])].copy()
    df["abs_d_delta"] = df["journal_d_minus_registry_d"].abs()

    sentence = df["selected_sentence"].fillna("").astype(str).str.strip()
    df["sentence_outcome_overlap"] = [
        outcome_overlap(s, a, b)
        for s, a, b in zip(sentence, df["clinifact_outcome_title"], df["registry_outcome_title"])
    ]
    df["sentence_p_count"] = sentence.map(p_count)
    df["has_compare_marker"] = sentence.str.contains(COMPARE_RE, regex=True)
    df["has_baseline_marker"] = sentence.str.contains(BASELINE_RE, regex=True)
    df["has_association_marker"] = sentence.str.contains(ASSOCIATION_RE, regex=True)
    df["has_structural_start"] = sentence.str.contains(STRUCTURAL_RE, regex=True)
    df["has_conclusion_start"] = sentence.str.contains(CONCLUSION_RE, regex=True)
    df["has_results_start"] = sentence.str.contains(RESULTS_RE, regex=True)
    df["has_both_groups_marker"] = sentence.str.contains(BOTH_GROUPS_RE, regex=True)
    df["is_fragment_sentence"] = sentence.str.contains(FRAGMENT_RE, regex=True)

    df["flag_wrong_outcome_sentence"] = df["sentence_outcome_overlap"] < 0.2
    df["flag_association_sentence"] = df["has_association_marker"]
    df["flag_baseline_within_group"] = df["has_baseline_marker"] & (~df["has_compare_marker"])
    df["flag_both_groups_no_between_group"] = df["has_both_groups_marker"] & (~df["has_compare_marker"])
    df["flag_structural_nonresult_sentence"] = df["has_structural_start"] & (~df["has_results_start"])
    df["flag_conclusion_without_p"] = df["has_conclusion_start"] & (df["sentence_p_count"] == 0) & (~df["has_results_start"])
    df["flag_truncated_fragment"] = df["is_fragment_sentence"] & (df["sentence_outcome_overlap"] < 0.3)
    df["flag_multi_p_ambiguous"] = (df["sentence_p_count"] >= 2) & (df["sentence_outcome_overlap"] < 0.4)

    false_positive_flags = [
        "flag_wrong_outcome_sentence",
        "flag_association_sentence",
        "flag_baseline_within_group",
        "flag_both_groups_no_between_group",
        "flag_structural_nonresult_sentence",
        "flag_conclusion_without_p",
        "flag_truncated_fragment",
        "flag_multi_p_ambiguous",
    ]
    df["likely_noncomparable"] = df[false_positive_flags].any(axis=1)

    reasons = []
    for _, row in df.iterrows():
        row_reasons = []
        for flag in false_positive_flags:
            if bool(row[flag]):
                row_reasons.append(flag.replace("flag_", ""))
        reasons.append(";".join(row_reasons))
    df["triage_reason"] = reasons

    df["keep_for_manual_audit"] = (
        (
            df["sig_discordant_05"].fillna(False).astype(bool)
            | (df["abs_d_delta"] >= 0.25)
        )
        & (~df["likely_noncomparable"])
    )

    cleaned = df[df["keep_for_manual_audit"]].copy()
    cleaned = cleaned.sort_values(
        ["pair_quality", "sig_discordant_05", "abs_d_delta", "selected_sentence_score"],
        ascending=[False, False, False, False],
    )
    cleaned = cleaned.drop_duplicates(
        subset=["nctId", "PMID", "selected_sentence", "journal_p", "registry_p"],
        keep="first",
    )

    likely_false = df[df["likely_noncomparable"]].copy()
    likely_false = likely_false.sort_values(
        ["pair_quality", "sig_discordant_05", "abs_d_delta", "sentence_outcome_overlap"],
        ascending=[False, False, False, True],
    )
    likely_false = likely_false.drop_duplicates(
        subset=["nctId", "PMID", "selected_sentence", "journal_p", "registry_p"],
        keep="first",
    )

    keep_cols = [
        "claim_id",
        "nctId",
        "PMID",
        "pair_quality",
        "journal_p",
        "registry_p",
        "sig_discordant_05",
        "sig_discordant_10",
        "journal_d_proxy_preferred",
        "registry_d_proxy",
        "journal_d_minus_registry_d",
        "abs_d_delta",
        "sentence_outcome_overlap",
        "sentence_p_count",
        "likely_noncomparable",
        "triage_reason",
        "article_title",
        "selected_sentence",
        "clinifact_outcome_title",
        "registry_outcome_title",
    ]
    return df[keep_cols].copy(), cleaned[keep_cols].copy(), likely_false[keep_cols].copy()


def write_summary(full: pd.DataFrame, cleaned: pd.DataFrame, likely_false: pd.DataFrame) -> None:
    lines = [
        "# CliniFact Pair Triage",
        "",
        "Last updated: 2026-04-20",
        "",
        "This file heuristically triages the high/medium-quality pair rows into",
        "manual-audit candidates versus likely non-comparable abstract matches.",
        "",
        "## Counts",
        "",
        f"- High/medium pair rows triaged: {len(full):,}",
        f"- Cleaned manual-audit rows: {len(cleaned):,}",
        f"- Likely non-comparable rows: {len(likely_false):,}",
        f"- Cleaned rows with `sig_discordant_05`: {int(cleaned['sig_discordant_05'].fillna(False).astype(bool).sum()):,}",
        f"- Cleaned rows with `abs_d_delta >= 0.25`: {int((cleaned['abs_d_delta'] >= 0.25).sum()):,}",
        "",
        "## Output Files",
        "",
        "- `data/derived/publication_bias_direct/clinifact_publication_registry_triage.csv`",
        "- `data/derived/publication_bias_direct/clinifact_publication_registry_clean_audit_queue.csv`",
        "- `data/derived/publication_bias_direct/clinifact_publication_registry_likely_noncomparable.csv`",
        "- `data/derived/publication_bias_direct/clinifact_publication_registry_triage_summary.md`",
    ]
    (OUT_DIR / "clinifact_publication_registry_triage_summary.md").write_text("\n".join(lines) + "\n")


def main() -> None:
    ensure_dir(OUT_DIR)
    full, cleaned, likely_false = build_triage()
    full.to_csv(OUT_DIR / "clinifact_publication_registry_triage.csv", index=False)
    cleaned.to_csv(OUT_DIR / "clinifact_publication_registry_clean_audit_queue.csv", index=False)
    likely_false.to_csv(OUT_DIR / "clinifact_publication_registry_likely_noncomparable.csv", index=False)
    write_summary(full, cleaned, likely_false)
    print(
        f"Wrote {len(full):,} triaged rows, {len(cleaned):,} cleaned audit rows, "
        f"and {len(likely_false):,} likely non-comparable rows to {OUT_DIR}"
    )


if __name__ == "__main__":
    main()
