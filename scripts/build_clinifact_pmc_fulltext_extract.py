#!/usr/bin/env python3
"""Enrich the cleaned CliniFact audit queue with PMC full-text evidence.

This pass is intentionally limited to the already-triaged queue. The goal is to
use PMC-hosted full text where available to decide whether a journal-vs-registry
disagreement is still real after moving beyond the abstract.
"""

from __future__ import annotations

import html
import math
import re
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd
import requests

from build_clinifact_publication_numeric_extract import (
    CI_RE,
    P_RE,
    choose_ci,
    choose_effect,
    choose_p_value,
    clean_text,
    extract_n_candidates,
    p_to_abs_z,
    sentence_score,
    split_sentences,
)


ROOT = Path(__file__).resolve().parents[1]
BASE_DIR = ROOT / "data" / "derived" / "publication_bias_direct"
IN_CLEAN = BASE_DIR / "clinifact_publication_registry_clean_audit_queue.csv"
IN_PAIRS = BASE_DIR / "clinifact_publication_registry_pairs.csv"
OUT_CSV = BASE_DIR / "clinifact_pmc_fulltext_extract.csv"
OUT_PARQUET = BASE_DIR / "clinifact_pmc_fulltext_extract.parquet"
OUT_RESOLVED = BASE_DIR / "clinifact_pmc_fulltext_resolved.csv"
OUT_UNRESOLVED = BASE_DIR / "clinifact_pmc_fulltext_unresolved.csv"
OUT_SUMMARY = BASE_DIR / "clinifact_pmc_fulltext_summary.md"
RAW_HTML_DIR = ROOT / "data" / "raw" / "publication_bias_direct" / "pmc_html"

EUROPEPMC_URL = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
PMC_HTML_URLS = [
    "https://pmc.ncbi.nlm.nih.gov/articles/{pmcid}/?page=1",
    "https://pmc.ncbi.nlm.nih.gov/articles/{pmcid}/",
    "https://www.ncbi.nlm.nih.gov/pmc/articles/{pmcid}/",
]
UA = {"User-Agent": "Mozilla/5.0"}

COMPARE_RE = re.compile(
    r"(?i)\b(?:compared with|compared to|versus|vs\.?|than placebo|than control|than standard|"
    r"more than|less than|greater than|lower than|difference\b|non-inferior|superior|inferior)\b"
)
PRIMARY_RE = re.compile(r"(?i)\b(?:primary outcome|primary endpoint|primary end point|main outcome)\b")
RESULTS_RE = re.compile(r"(?i)^(?:results?|findings?)\b")
STRUCTURAL_RE = re.compile(
    r"(?i)^(?:the\s+)?(?:objective|objectives|aim|aims|purpose|purposes|methods|method|"
    r"design|intervention|main outcome measures|main outcomes and measures|"
    r"research design and methods|patients and methods)\b"
)
CONCLUSION_RE = re.compile(r"(?i)^(?:conclusion|conclusions|interpretation)\b")
BASELINE_RE = re.compile(
    r"(?i)\b(?:from baseline|change from baseline|compared with baseline|compared to baseline|baseline to)\b"
)
EFFECT_TOKEN_RE = re.compile(
    r"(?i)\b(?:HR|hazard ratio|OR|odds ratio|RR|risk ratio|relative risk|IRR|rate ratio|"
    r"mean difference|least-squares mean difference|estimated treatment difference)\b"
)
NOISE_RE = re.compile(
    r"(?i)(official website|secure \.gov|share sensitive information|logged in as|dashboard|site navigation)"
)
CHALLENGE_RE = re.compile(r"(?i)(recaptcha/challengepage|gstatic|verify you are human|captcha)")


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def choose_n(candidates: list[tuple[int, str, str]], enrollment: float) -> tuple[float, str, str]:
    if not candidates:
        return np.nan, "missing", ""

    vals = [(int(v), src, raw) for v, src, raw in candidates]
    enrollment_ok = pd.notna(enrollment) and enrollment > 0

    if enrollment_ok:
        target = float(enrollment)
        best_val, best_src, best_raw = min(vals, key=lambda x: abs(x[0] - target))
        if abs(best_val - target) <= max(5.0, 0.15 * target):
            return float(best_val), f"{best_src}_closest_to_registry", best_raw

    best_val, best_src, best_raw = max(vals, key=lambda x: x[0])
    return float(best_val), f"{best_src}_max_fallback", best_raw


def europepmc_meta(pmid: str) -> dict[str, object]:
    params = {"query": f"EXT_ID:{pmid} AND SRC:MED", "format": "json"}
    response = requests.get(EUROPEPMC_URL, params=params, headers=UA, timeout=30)
    response.raise_for_status()
    data = response.json()
    result = ((data.get("resultList") or {}).get("result") or [{}])[0]
    return {
        "pmid": result.get("pmid"),
        "pmcid": result.get("pmcid"),
        "doi": result.get("doi"),
        "isOpenAccess": result.get("isOpenAccess"),
        "inPMC": result.get("inPMC"),
        "inEPMC": result.get("inEPMC"),
        "hasPDF": result.get("hasPDF"),
        "hasSuppl": result.get("hasSuppl"),
        "epmc_title": result.get("title"),
    }


def fetch_pmc_html(pmcid: str) -> str:
    ensure_dir(RAW_HTML_DIR)
    path = RAW_HTML_DIR / f"{pmcid}.html"
    if path.exists():
        cached = path.read_text(encoding="utf-8", errors="ignore")
        if html_access_status(cached) == "article_html":
            return cached

    best_text = ""
    best_status = "missing"
    for template in PMC_HTML_URLS:
        response = requests.get(template.format(pmcid=pmcid), headers=UA, timeout=30)
        response.raise_for_status()
        text = response.text
        status = html_access_status(text)
        if status == "article_html":
            path.write_text(text, encoding="utf-8")
            return text
        if not best_text or best_status == "missing":
            best_text = text
            best_status = status

    if best_text:
        path.write_text(best_text, encoding="utf-8")
    return best_text


def html_access_status(html_text: str) -> str:
    if not html_text:
        return "missing"
    lowered = html_text.lower()
    paragraph_count = len(re.findall(r"<p[^>]*>", lowered))
    article_markers = (
        "pmc_sec_title" in lowered
        or "<article" in lowered
        or "<section" in lowered
        or re.search(r"(?i)\babstract\b", html_text)
        or re.search(r"(?i)\bresults?\b", html_text)
        or re.search(r"(?i)\bmethods?\b", html_text)
    )
    if paragraph_count >= 20 or (paragraph_count >= 8 and article_markers):
        return "article_html"
    if CHALLENGE_RE.search(html_text):
        return "challenge_page"
    if "<p" in lowered:
        return "other_html"
    return "other_html"


def extract_paragraphs(html_text: str) -> list[str]:
    paragraphs: list[str] = []
    for raw in re.findall(r"<p[^>]*>(.*?)</p>", html_text, flags=re.S | re.I):
        text = " ".join(html.unescape(re.sub(r"<[^>]+>", " ", raw)).split())
        if len(text) < 40:
            continue
        if NOISE_RE.search(text):
            continue
        paragraphs.append(text)
    return paragraphs


def candidate_windows(paragraphs: Iterable[str]) -> list[str]:
    windows: list[str] = []
    for paragraph in paragraphs:
        sentences = split_sentences(paragraph)
        for i, sentence in enumerate(sentences):
            windows.append(sentence)
            if i + 1 < len(sentences):
                windows.append(f"{sentence} {sentences[i + 1]}")
    return list(dict.fromkeys(windows))


def window_score(window: str, row: pd.Series) -> float:
    score = sentence_score(window, row)
    if P_RE.search(window):
        score += 0.8
    if CI_RE.search(window):
        score += 0.3
    if EFFECT_TOKEN_RE.search(window):
        score += 0.5
    if COMPARE_RE.search(window):
        score += 0.4
    if PRIMARY_RE.search(window):
        score += 0.4
    if RESULTS_RE.search(window):
        score += 0.2
    if BASELINE_RE.search(window) and not COMPARE_RE.search(window):
        score -= 0.3
    if STRUCTURAL_RE.search(window):
        score -= 1.0
    if CONCLUSION_RE.search(window) and not P_RE.search(window):
        score -= 0.6
    return float(score)


def pick_best_window(windows: list[str], row: pd.Series) -> tuple[str, float]:
    if not windows:
        return "", 0.0
    scored = [(window_score(window, row), window) for window in windows]
    scored.sort(key=lambda x: (x[0], len(x[1])), reverse=True)
    p_windows = [(score, window) for score, window in scored if P_RE.search(window)]
    if p_windows:
        p_windows.sort(key=lambda x: (x[0], len(x[1])), reverse=True)
        return p_windows[0][1], float(p_windows[0][0])
    return scored[0][1], float(scored[0][0])


def pick_best_numeric_sentence(window: str, row: pd.Series) -> tuple[str, float]:
    sentences = split_sentences(window)
    numeric = [s for s in sentences if P_RE.search(s) or CI_RE.search(s) or EFFECT_TOKEN_RE.search(s)]
    if not numeric:
        return window, window_score(window, row)
    scored = [(window_score(sentence, row), sentence) for sentence in numeric]
    scored.sort(key=lambda x: (x[0], len(x[1])), reverse=True)
    return scored[0][1], float(scored[0][0])


def bool_from_p(value: float, threshold: float) -> object:
    if pd.isna(value):
        return np.nan
    return bool(value < threshold)


def resolution_status(row: pd.Series) -> str:
    pmcid = row.get("pmcid")
    if pd.isna(pmcid) or str(pmcid).strip().lower() in {"", "nan", "none"}:
        return "no_pmc_fulltext"
    if row.get("pmc_access_status") in {"challenge_page", "fetch_error", "other_html"}:
        return "pmc_access_blocked"
    if pd.isna(row.get("fulltext_p")):
        return "pmc_fulltext_no_numeric"
    if bool(row.get("sig_discordant_05", False)):
        if bool(row.get("fulltext_sig_agrees_registry_05", False)):
            return "resolved_toward_registry"
        if bool(row.get("fulltext_sig_agrees_abstract_05", False)):
            return "supports_abstract_disagreement"
        return "still_sig_discordant_after_fulltext"
    if pd.notna(row.get("fulltext_abs_d_delta_vs_registry")) and pd.notna(row.get("abs_d_delta")):
        if row["fulltext_abs_d_delta_vs_registry"] + 0.05 < row["abs_d_delta"]:
            return "reduced_gap_toward_registry"
        if row["fulltext_abs_d_delta_vs_registry"] > row["abs_d_delta"] + 0.05:
            return "larger_gap_after_fulltext"
    return "pmc_fulltext_inconclusive"


def build_extract() -> pd.DataFrame:
    clean = pd.read_csv(IN_CLEAN)
    pairs = pd.read_csv(IN_PAIRS)[
        [
            "claim_id",
            "enrollment_num",
            "journal_n_preferred",
            "journal_n_preferred_source",
            "journal_p_source",
            "registry_d_proxy",
            "registry_p",
            "journal_d_proxy_preferred",
            "selected_sentence_score",
            "combined_match_score",
            "match_quality",
        ]
    ]
    df = clean.merge(pairs, on="claim_id", how="left", suffixes=("", "_pairs"))

    meta_rows = {}
    for pmid in df["PMID"].astype(str).drop_duplicates():
        meta_rows[pmid] = europepmc_meta(pmid)

    records: list[dict[str, object]] = []
    for _, row in df.iterrows():
        pmid = str(row["PMID"])
        meta = meta_rows.get(pmid, {})
        pmcid = meta.get("pmcid")
        fulltext_window = ""
        fulltext_window_score = np.nan
        fulltext_numeric_sentence = ""
        fulltext_numeric_sentence_score = np.nan
        fulltext_p = np.nan
        fulltext_p_operator = ""
        fulltext_p_source = "missing"
        fulltext_p_raw = ""
        fulltext_ci_level = np.nan
        fulltext_ci_lower = np.nan
        fulltext_ci_upper = np.nan
        fulltext_ci_source = "missing"
        fulltext_ci_raw = ""
        fulltext_effect_metric = ""
        fulltext_effect_value = np.nan
        fulltext_effect_source = "missing"
        fulltext_effect_raw = ""
        fulltext_n_selected = np.nan
        fulltext_n_source = "missing"
        fulltext_n_raw = ""
        html_available = False
        pmc_access_status = "no_pmcid"

        if pmcid:
            try:
                html_text = fetch_pmc_html(str(pmcid))
                pmc_access_status = html_access_status(html_text)
                if pmc_access_status == "article_html":
                    html_available = True
                    paragraphs = extract_paragraphs(html_text)
                    windows = candidate_windows(paragraphs)
                    fulltext_window, fulltext_window_score = pick_best_window(windows, row)
                    fulltext_numeric_sentence, fulltext_numeric_sentence_score = pick_best_numeric_sentence(fulltext_window, row)

                    p_val, p_op, _, p_raw = choose_p_value(fulltext_numeric_sentence, fulltext_window)
                    fulltext_p = p_val
                    fulltext_p_operator = p_op
                    fulltext_p_source = "numeric_sentence" if np.isfinite(p_val) else "missing"
                    fulltext_p_raw = p_raw

                    ci_level, ci_low, ci_high, _, ci_raw = choose_ci(fulltext_numeric_sentence, fulltext_window)
                    fulltext_ci_level = ci_level
                    fulltext_ci_lower = ci_low
                    fulltext_ci_upper = ci_high
                    fulltext_ci_source = "numeric_sentence" if np.isfinite(ci_level) else "missing"
                    fulltext_ci_raw = ci_raw

                    effect_metric, effect_value, _, effect_raw = choose_effect(fulltext_numeric_sentence, fulltext_window)
                    fulltext_effect_metric = effect_metric
                    fulltext_effect_value = effect_value
                    fulltext_effect_source = "numeric_sentence" if effect_metric else "missing"
                    fulltext_effect_raw = effect_raw

                    n_candidates = extract_n_candidates(fulltext_window)
                    n_selected, n_source, n_raw = choose_n(n_candidates, row.get("enrollment_num"))
                    fulltext_n_selected = n_selected
                    fulltext_n_source = n_source
                    fulltext_n_raw = n_raw
            except Exception:
                html_available = False
                pmc_access_status = "fetch_error"

        fulltext_abs_z = p_to_abs_z(fulltext_p)
        fulltext_d_selected = (
            2 * fulltext_abs_z / math.sqrt(fulltext_n_selected)
            if np.isfinite(fulltext_abs_z) and np.isfinite(fulltext_n_selected) and fulltext_n_selected > 0
            else np.nan
        )
        fulltext_d_registry = (
            2 * fulltext_abs_z / math.sqrt(row["enrollment_num"])
            if np.isfinite(fulltext_abs_z) and pd.notna(row.get("enrollment_num")) and row["enrollment_num"] > 0
            else np.nan
        )
        fulltext_d_preferred = fulltext_d_selected if np.isfinite(fulltext_d_selected) else fulltext_d_registry
        fulltext_sig_05 = bool_from_p(fulltext_p, 0.05)
        fulltext_sig_10 = bool_from_p(fulltext_p, 0.10)
        registry_sig_05 = bool_from_p(row.get("registry_p"), 0.05)
        abstract_sig_05 = bool_from_p(row.get("journal_p"), 0.05)
        sig_agree_registry = (
            bool(fulltext_sig_05 == registry_sig_05)
            if pd.notna(fulltext_sig_05) and pd.notna(registry_sig_05)
            else np.nan
        )
        sig_agree_abstract = (
            bool(fulltext_sig_05 == abstract_sig_05)
            if pd.notna(fulltext_sig_05) and pd.notna(abstract_sig_05)
            else np.nan
        )

        rec = row.to_dict()
        rec.update(
            {
                "pmcid": pmcid,
                "doi": meta.get("doi"),
                "isOpenAccess": meta.get("isOpenAccess"),
                "inPMC": meta.get("inPMC"),
                "inEPMC": meta.get("inEPMC"),
                "hasPDF": meta.get("hasPDF"),
                "hasSuppl": meta.get("hasSuppl"),
                "pmc_html_available": html_available,
                "pmc_access_status": pmc_access_status,
                "fulltext_window": fulltext_window,
                "fulltext_window_score": fulltext_window_score,
                "fulltext_numeric_sentence": fulltext_numeric_sentence,
                "fulltext_numeric_sentence_score": fulltext_numeric_sentence_score,
                "fulltext_p": fulltext_p,
                "fulltext_p_operator": fulltext_p_operator,
                "fulltext_p_source": fulltext_p_source,
                "fulltext_p_raw": fulltext_p_raw,
                "fulltext_abs_z": fulltext_abs_z,
                "fulltext_sig_05": fulltext_sig_05,
                "fulltext_sig_10": fulltext_sig_10,
                "fulltext_ci_level": fulltext_ci_level,
                "fulltext_ci_lower": fulltext_ci_lower,
                "fulltext_ci_upper": fulltext_ci_upper,
                "fulltext_ci_source": fulltext_ci_source,
                "fulltext_ci_raw": fulltext_ci_raw,
                "fulltext_effect_metric": fulltext_effect_metric,
                "fulltext_effect_value": fulltext_effect_value,
                "fulltext_effect_source": fulltext_effect_source,
                "fulltext_effect_raw": fulltext_effect_raw,
                "fulltext_n_selected": fulltext_n_selected,
                "fulltext_n_source": fulltext_n_source,
                "fulltext_n_raw": fulltext_n_raw,
                "fulltext_d_proxy_selected_n": fulltext_d_selected,
                "fulltext_d_proxy_registry_n": fulltext_d_registry,
                "fulltext_d_proxy_preferred": fulltext_d_preferred,
                "fulltext_abs_d_delta_vs_registry": abs(fulltext_d_preferred - row["registry_d_proxy"])
                if np.isfinite(fulltext_d_preferred) and pd.notna(row.get("registry_d_proxy"))
                else np.nan,
                "fulltext_abs_d_delta_vs_abstract": abs(fulltext_d_preferred - row["journal_d_proxy_preferred"])
                if np.isfinite(fulltext_d_preferred) and pd.notna(row.get("journal_d_proxy_preferred"))
                else np.nan,
                "fulltext_sig_agrees_registry_05": sig_agree_registry,
                "fulltext_sig_agrees_abstract_05": sig_agree_abstract,
            }
        )
        records.append(rec)

    out = pd.DataFrame.from_records(records)
    out["resolution_status"] = out.apply(resolution_status, axis=1)
    return out


def write_summary(df: pd.DataFrame) -> None:
    pmcid_rows = int(df["pmcid"].notna().sum())
    fulltext_p_rows = int(df["fulltext_p"].notna().sum())
    resolved = df["resolution_status"].isin(["resolved_toward_registry", "reduced_gap_toward_registry"]).sum()
    unresolved = df["resolution_status"].isin(
        [
            "no_pmc_fulltext",
            "pmc_access_blocked",
            "pmc_fulltext_no_numeric",
            "still_sig_discordant_after_fulltext",
            "supports_abstract_disagreement",
            "larger_gap_after_fulltext",
        ]
    ).sum()
    lines = [
        "# CliniFact PMC Full-Text Enrichment",
        "",
        "Last updated: 2026-04-21",
        "",
        "This pass enriches the cleaned CliniFact audit queue with PMC metadata and,",
        "where possible, a full-text numeric sentence/window for the linked primary",
        "outcome result.",
        "",
        "## Counts",
        "",
        f"- Cleaned audit rows in: {len(df):,}",
        f"- Unique PMIDs: {df['PMID'].nunique():,}",
        f"- Rows with PMCID: {pmcid_rows:,}",
        f"- Rows with article-like PMC HTML fetched: {int(df['pmc_html_available'].fillna(False).sum()):,}",
        f"- Rows with PMC challenge/blocked HTML: {int(df['pmc_access_status'].eq('challenge_page').sum()):,}",
        f"- Rows with full-text p-values: {fulltext_p_rows:,}",
        f"- Rows with full-text effect metrics: {int(df['fulltext_effect_value'].notna().sum()):,}",
        f"- Rows resolved toward registry after full text: {int(resolved):,}",
        f"- Rows still unresolved / still external-data dependent: {int(unresolved):,}",
        "",
        "## Resolution Status",
        "",
    ]
    for status, count in df["resolution_status"].value_counts().items():
        lines.append(f"- `{status}`: {int(count):,}")
    lines += [
        "",
        "## Output Files",
        "",
        "- `data/derived/publication_bias_direct/clinifact_pmc_fulltext_extract.csv`",
        "- `data/derived/publication_bias_direct/clinifact_pmc_fulltext_extract.parquet`",
        "- `data/derived/publication_bias_direct/clinifact_pmc_fulltext_resolved.csv`",
        "- `data/derived/publication_bias_direct/clinifact_pmc_fulltext_unresolved.csv`",
        "- `data/derived/publication_bias_direct/clinifact_pmc_fulltext_summary.md`",
    ]
    OUT_SUMMARY.write_text("\n".join(lines) + "\n")


def main() -> None:
    ensure_dir(RAW_HTML_DIR)
    df = build_extract()
    resolved = df[df["resolution_status"].isin(["resolved_toward_registry", "reduced_gap_toward_registry"])].copy()
    unresolved = df[
        df["resolution_status"].isin(
            [
                "no_pmc_fulltext",
                "pmc_access_blocked",
                "pmc_fulltext_no_numeric",
                "still_sig_discordant_after_fulltext",
                "supports_abstract_disagreement",
                "larger_gap_after_fulltext",
            ]
        )
    ].copy()
    df.to_csv(OUT_CSV, index=False)
    df.to_parquet(OUT_PARQUET, index=False)
    resolved.to_csv(OUT_RESOLVED, index=False)
    unresolved.to_csv(OUT_UNRESOLVED, index=False)
    write_summary(df)
    print(
        f"Wrote {len(df):,} PMC-enriched rows, {len(resolved):,} resolved rows, "
        f"and {len(unresolved):,} unresolved rows."
    )


if __name__ == "__main__":
    main()
