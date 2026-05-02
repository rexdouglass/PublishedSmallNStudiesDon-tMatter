#!/usr/bin/env python3
"""Check whether acquired PDF bytes match the represented source.

The acquisition pass answers only "did this route return PDF bytes?" This pass
answers the separate question needed before source_file promotion: "do those
PDF bytes appear to be the represented paper?"
"""

from __future__ import annotations

import hashlib
import os
import re
import subprocess
from collections import Counter, defaultdict
from datetime import datetime, timezone
from difflib import SequenceMatcher
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
PILOT = ROOT / "data" / "derived" / "effect_inflation_dataset" / "schema_pilot"
SAMPLE_N = int(os.environ.get("SCHEMA_PILOT_N", "300"))
SAMPLE_SUFFIX = f"sample_{SAMPLE_N}"

SOURCE_RESULT_IN = PILOT / f"source_result_codebook_{SAMPLE_SUFFIX}.tsv"
SOURCE_IDENTIFIER_IN = PILOT / f"source_identifier_codebook_{SAMPLE_SUFFIX}.tsv"
SOURCE_IN = PILOT / f"source_codebook_{SAMPLE_SUFFIX}.tsv"
PDF_ATTEMPTS_IN = PILOT / f"original_pdf_acquisition_attempts_{SAMPLE_SUFFIX}.tsv"

OUT_TSV = PILOT / f"original_pdf_identity_check_{SAMPLE_SUFFIX}.tsv"
OUT_SUMMARY = PILOT / f"original_pdf_identity_check_summary_{SAMPLE_SUFFIX}.tsv"
OUT_REPORT = ROOT / "reports" / f"original_pdf_identity_check_{SAMPLE_SUFFIX}_2026-04-30.md"

DOI_RE = re.compile(r"10\.\d{4,9}/[-._;()/:A-Z0-9]+", re.I)
WORD_RE = re.compile(r"[a-z0-9]+")
STOPWORDS = {
    "about",
    "after",
    "among",
    "and",
    "are",
    "between",
    "from",
    "have",
    "how",
    "into",
    "more",
    "over",
    "paper",
    "study",
    "that",
    "the",
    "their",
    "them",
    "this",
    "through",
    "using",
    "with",
}


def safe_text(value: object) -> str:
    if value is None:
        return ""
    return str(value).replace("\t", " ").replace("\r", " ").replace("\n", " ").strip()


def rel(path: Path | str) -> str:
    p = Path(path)
    if not p.is_absolute():
        p = ROOT / p
    try:
        return str(p.relative_to(ROOT))
    except ValueError:
        return str(p)


def normalize_doi(value: str) -> str:
    text = safe_text(value).strip()
    if not text:
        return ""
    text = re.sub(r"^doi:\s*", "", text, flags=re.I)
    text = re.sub(r"^https?://(?:dx\.)?doi\.org/", "", text, flags=re.I)
    text = text.strip().rstrip(".,;)")
    match = DOI_RE.search(text)
    if not match:
        return ""
    doi = match.group(0).rstrip(".,;)")
    doi = re.sub(r"(10\.\d{4,9})//+", r"\1/", doi, flags=re.I)
    return doi.lower()


def doi_values(value: str) -> list[str]:
    out = []
    for match in DOI_RE.finditer(safe_text(value)):
        doi = normalize_doi(match.group(0))
        if doi:
            out.append(doi)
    return list(dict.fromkeys(out))


def normalize_words(value: str) -> list[str]:
    return WORD_RE.findall(safe_text(value).lower())


def normalize_phrase(value: str) -> str:
    return " ".join(normalize_words(value))


def title_tokens(title: str) -> list[str]:
    return [word for word in normalize_words(title) if len(word) >= 4 and word not in STOPWORDS]


def weak_title(title: str) -> bool:
    text = safe_text(title)
    if not text:
        return True
    lower = text.lower()
    tokens = title_tokens(text)
    alpha_chars = sum(1 for ch in lower if ch.isalpha())
    digit_or_symbol = sum(1 for ch in lower if ch.isdigit() or ch in "=<>_/:")
    if lower.startswith("http://") or lower.startswith("https://"):
        return True
    if re.search(r"\bf\s*\(\s*\d+\s*,\s*\d+\s*\)\s*=", lower):
        return True
    if len(tokens) < 4:
        return True
    if alpha_chars and digit_or_symbol / max(alpha_chars, 1) > 0.6:
        return True
    return False


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run_text_command(args: list[str], timeout: int = 25) -> tuple[str, str]:
    try:
        proc = subprocess.run(
            args,
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            check=False,
        )
    except Exception as exc:  # noqa: BLE001 - diagnostic row should capture failures.
        return "", f"{type(exc).__name__}:{exc}"
    if proc.returncode != 0 and not proc.stdout:
        return "", safe_text(proc.stderr) or f"returncode_{proc.returncode}"
    return proc.stdout or "", safe_text(proc.stderr)


def extract_pdf_text(path: Path) -> tuple[str, str]:
    # The first pages usually contain the DOI/title and keep this pass fast.
    text, err = run_text_command(["pdftotext", "-f", "1", "-l", "5", "-layout", str(path), "-"])
    if text.strip():
        return text, "ok"
    text, err2 = run_text_command(["pdftotext", "-f", "1", "-l", "5", str(path), "-"])
    if text.strip():
        return text, "ok_no_layout"
    return "", err2 or err or "no_text_extracted"


def pdfinfo_title(path: Path) -> str:
    text, _ = run_text_command(["pdfinfo", str(path)], timeout=10)
    for line in text.splitlines():
        if line.lower().startswith("title:"):
            return line.split(":", 1)[1].strip()
    return ""


def best_title_line_similarity(title: str, text: str, info_title: str) -> float:
    norm_title = normalize_phrase(title)
    if not norm_title:
        return 0.0
    candidates = [normalize_phrase(info_title)] if info_title else []
    for line in text.splitlines()[:120]:
        line_norm = normalize_phrase(line)
        if 8 <= len(line_norm) <= 260:
            candidates.append(line_norm)
    best = 0.0
    for candidate in candidates:
        if not candidate:
            continue
        best = max(best, SequenceMatcher(None, norm_title, candidate).ratio())
    return round(best, 3)


def title_token_coverage(title: str, text: str) -> float:
    tokens = title_tokens(title)
    if not tokens:
        return 0.0
    text_words = set(normalize_words(text))
    hits = sum(1 for token in tokens if token in text_words)
    return round(hits / len(tokens), 3)


def title_exact_present(title: str, text: str) -> bool:
    phrase = normalize_phrase(title)
    if len(phrase) < 24:
        return False
    return phrase in normalize_phrase(text)


def build_primary_doi_lookup(sources: pd.DataFrame, identifiers: pd.DataFrame) -> dict[str, list[str]]:
    by_source: dict[str, list[str]] = defaultdict(list)
    for _, row in sources.iterrows():
        source_id = safe_text(row.get("source_id"))
        doi = normalize_doi(safe_text(row.get("doi")))
        if source_id and doi:
            by_source[source_id].append(doi)
    for _, row in identifiers.iterrows():
        source_id = safe_text(row.get("source_id"))
        if not source_id:
            continue
        if safe_text(row.get("is_primary")).lower() != "true":
            continue
        typ = safe_text(row.get("identifier_type")).lower()
        values = []
        if typ == "doi":
            values.append(safe_text(row.get("identifier_value")))
            values.append(safe_text(row.get("identifier_url")))
        elif typ == "url":
            # Only primary URL identifiers can promote a DOI URL to the primary DOI set.
            values.append(safe_text(row.get("identifier_value")))
            values.append(safe_text(row.get("identifier_url")))
        for value in values:
            doi = normalize_doi(value)
            if doi:
                by_source[source_id].append(doi)
    return {key: list(dict.fromkeys(values)) for key, values in by_source.items()}


def decision_for_row(row: pd.Series) -> tuple[str, str]:
    primary_dois = [doi for doi in safe_text(row["primary_dois"]).split("|") if doi]
    acquired_doi = safe_text(row["acquired_doi"])
    text_dois = [doi for doi in safe_text(row["pdf_text_dois"]).split("|") if doi]
    primary_set = set(primary_dois)
    text_set = set(text_dois)
    candidate_matches_primary = safe_text(row["candidate_url_matches_primary_doi"]).lower() == "true"
    final_matches_primary = safe_text(row["final_url_matches_primary_doi"]).lower() == "true"
    acquired_matches_primary = acquired_doi in primary_set if acquired_doi else False
    text_contains_primary = bool(primary_set & text_set)
    title_exact = safe_text(row["title_exact_present"]).lower() == "true"
    title_similarity = float(row["title_line_similarity"] or 0)
    token_coverage = float(row["title_token_coverage"] or 0)
    title_is_weak = safe_text(row["weak_represented_title"]).lower() == "true"
    text_status = safe_text(row["text_status"])

    title_strong = (not title_is_weak) and (
        title_exact or title_similarity >= 0.84 or (token_coverage >= 0.72 and title_similarity >= 0.55)
    )

    if primary_dois:
        if acquired_matches_primary or candidate_matches_primary or final_matches_primary:
            if text_contains_primary:
                return "accepted_pdf_identity", "primary DOI route matches and primary DOI appears in extracted PDF text"
            if title_strong:
                return "accepted_pdf_identity", "primary DOI route matches and represented title matches extracted PDF text"
            if text_status.startswith("ok"):
                return "accepted_pdf_identity", "primary DOI route matches; PDF text extracted but DOI/title signal is incomplete"
            return "needs_manual_identity_check", "primary DOI route matches, but text extraction did not confirm title or DOI"
        if text_contains_primary:
            return "accepted_pdf_identity", "primary DOI appears in extracted PDF text despite route DOI mismatch"
        if acquired_doi and acquired_doi not in primary_set:
            return "reject_wrong_doi", f"acquired DOI {acquired_doi} is not one of the primary represented-source DOIs"
        if title_strong:
            return "needs_manual_identity_check", "represented title matches PDF text but primary DOI route did not match"
        return "needs_manual_identity_check", "primary DOI exists, but acquired PDF did not match DOI or title checks"

    if title_strong:
        if acquired_doi and acquired_doi in text_set:
            return "accepted_pdf_identity", "no primary DOI; represented title matches and acquired DOI appears in PDF text"
        return "accepted_pdf_identity", "no primary DOI; represented title matches extracted PDF text"
    if acquired_doi and acquired_doi in text_set and not title_is_weak:
        return "needs_manual_identity_check", "acquired DOI appears in PDF text but represented title match is weak"
    return "needs_manual_identity_check", "no primary DOI and title evidence is insufficient"


def main() -> None:
    source_results = pd.read_csv(SOURCE_RESULT_IN, sep="\t", dtype=str, keep_default_na=False)
    identifiers = pd.read_csv(SOURCE_IDENTIFIER_IN, sep="\t", dtype=str, keep_default_na=False)
    sources = pd.read_csv(SOURCE_IN, sep="\t", dtype=str, keep_default_na=False)
    attempts = pd.read_csv(PDF_ATTEMPTS_IN, sep="\t", dtype=str, keep_default_na=False)

    primary_dois = build_primary_doi_lookup(sources, identifiers)
    source_result_levels = {
        safe_text(row["source_result_id"]): safe_text(row.get("evidence_level"))
        for _, row in source_results.iterrows()
    }

    pdf_rows = attempts[attempts["pdf_valid"].astype(str).str.lower().eq("true")].copy()
    out_rows: list[dict[str, object]] = []
    text_cache: dict[str, tuple[str, str, str]] = {}

    for _, row in pdf_rows.iterrows():
        local_path = ROOT / safe_text(row.get("local_path"))
        represented_source_id = safe_text(row.get("represented_source_id"))
        acquired_doi = normalize_doi(safe_text(row.get("doi")))
        file_exists = local_path.exists()
        actual_sha = sha256_file(local_path) if file_exists else ""
        sha_matches = bool(actual_sha and actual_sha == safe_text(row.get("sha256")).lower())

        if file_exists and safe_text(row.get("local_path")) not in text_cache:
            text, text_status = extract_pdf_text(local_path)
            info_title = pdfinfo_title(local_path)
            text_cache[safe_text(row.get("local_path"))] = (text[:250_000], text_status, info_title)
        elif file_exists:
            text, text_status, info_title = text_cache[safe_text(row.get("local_path"))]
        else:
            text, text_status, info_title = "", "missing_local_pdf", ""

        text_dois = doi_values(text)
        cand_dois = doi_values(safe_text(row.get("candidate_url")))
        final_dois = doi_values(safe_text(row.get("final_url")))
        primary = primary_dois.get(represented_source_id, [])
        primary_set = set(primary)
        represented_title = safe_text(row.get("represented_title"))

        out = {
            "source_result_id": safe_text(row.get("source_result_id")),
            "represented_source_id": represented_source_id,
            "previous_evidence_level": safe_text(row.get("previous_evidence_level"))
            or source_result_levels.get(safe_text(row.get("source_result_id")), ""),
            "represented_title": represented_title,
            "weak_represented_title": str(weak_title(represented_title)).lower(),
            "primary_dois": "|".join(primary),
            "acquired_doi": acquired_doi,
            "route": safe_text(row.get("route")),
            "candidate_url": safe_text(row.get("candidate_url")),
            "final_url": safe_text(row.get("final_url")),
            "local_path": safe_text(row.get("local_path")),
            "ledger_sha256": safe_text(row.get("sha256")),
            "actual_sha256": actual_sha,
            "sha256_matches_ledger": str(sha_matches).lower(),
            "file_exists": str(file_exists).lower(),
            "text_status": text_status,
            "text_chars_checked": len(text),
            "pdfinfo_title": info_title,
            "pdf_text_dois": "|".join(text_dois[:8]),
            "primary_doi_in_pdf_text": str(bool(primary_set & set(text_dois))).lower(),
            "acquired_doi_in_pdf_text": str(bool(acquired_doi and acquired_doi in set(text_dois))).lower(),
            "candidate_url_dois": "|".join(cand_dois),
            "final_url_dois": "|".join(final_dois),
            "candidate_url_matches_primary_doi": str(bool(primary_set & set(cand_dois))).lower(),
            "final_url_matches_primary_doi": str(bool(primary_set & set(final_dois))).lower(),
            "acquired_doi_matches_primary_doi": str(bool(acquired_doi and acquired_doi in primary_set)).lower(),
            "title_exact_present": str(title_exact_present(represented_title, text)).lower(),
            "title_token_coverage": title_token_coverage(represented_title, text),
            "title_line_similarity": best_title_line_similarity(represented_title, text, info_title),
        }
        decision, reason = decision_for_row(pd.Series(out))
        out["identity_decision"] = decision
        out["identity_decision_reason"] = reason
        out_rows.append(out)

    checks = pd.DataFrame(out_rows)
    OUT_TSV.parent.mkdir(parents=True, exist_ok=True)
    checks.to_csv(OUT_TSV, sep="\t", index=False)

    accepted = checks[checks["identity_decision"].eq("accepted_pdf_identity")].copy()
    rejected = checks[checks["identity_decision"].str.startswith("reject_")].copy()
    manual = checks[checks["identity_decision"].eq("needs_manual_identity_check")].copy()
    accepted_source_results = accepted["source_result_id"].nunique() if not accepted.empty else 0
    below_level5 = pd.to_numeric(source_results["evidence_level"], errors="coerce").fillna(0).lt(5).sum()
    current_level5_plus = pd.to_numeric(source_results["evidence_level"], errors="coerce").fillna(0).ge(5).sum()

    summary_rows = [
        {"metric": "sample_n", "value": SAMPLE_N},
        {"metric": "pdf_candidate_rows_checked", "value": len(checks)},
        {"metric": "pdf_candidate_source_results_checked", "value": checks["source_result_id"].nunique() if not checks.empty else 0},
        {"metric": "accepted_pdf_identity_rows", "value": len(accepted)},
        {"metric": "accepted_pdf_identity_source_results", "value": accepted_source_results},
        {"metric": "rejected_pdf_identity_rows", "value": len(rejected)},
        {"metric": "manual_identity_check_rows", "value": len(manual)},
        {"metric": "accepted_unique_pdf_sha256", "value": accepted["actual_sha256"].nunique() if not accepted.empty else 0},
        {"metric": "current_level5_plus_rows", "value": int(current_level5_plus)},
        {"metric": "below_level5_rows", "value": int(below_level5)},
        {"metric": "projected_level5_plus_if_accepted_promoted", "value": int(current_level5_plus + accepted_source_results)},
        {"metric": "created_at_utc", "value": datetime.now(timezone.utc).isoformat()},
    ]
    for key, value in checks["identity_decision"].value_counts().sort_index().items():
        summary_rows.append({"metric": f"identity_decision::{key}", "value": int(value)})
    for key, value in checks["route"].value_counts().sort_index().items():
        summary_rows.append({"metric": f"route_checked::{key}", "value": int(value)})
    for key, value in accepted["route"].value_counts().sort_index().items():
        summary_rows.append({"metric": f"route_accepted::{key}", "value": int(value)})
    for key, value in rejected["route"].value_counts().sort_index().items():
        summary_rows.append({"metric": f"route_rejected::{key}", "value": int(value)})
    summary = pd.DataFrame(summary_rows)
    summary.to_csv(OUT_SUMMARY, sep="\t", index=False)

    lines = [
        "# Original PDF Identity Check",
        "",
        f"- PDF candidate rows checked: {len(checks)}",
        f"- Source-result rows checked: {checks['source_result_id'].nunique() if not checks.empty else 0}",
        f"- Accepted as matching represented source: {accepted_source_results}",
        f"- Rejected as wrong source: {len(rejected)}",
        f"- Needs manual identity check: {len(manual)}",
        f"- Projected level >=5 after accepted promotions only: {int(current_level5_plus + accepted_source_results)}/300",
        "",
        "## Decision Counts",
        "",
    ]
    for decision, count in checks["identity_decision"].value_counts().items():
        lines.append(f"- `{decision}`: {int(count)}")
    lines.extend(["", "## Accepted Routes", ""])
    if accepted.empty:
        lines.append("- None.")
    else:
        for route, count in accepted["route"].value_counts().items():
            lines.append(f"- `{route}`: {int(count)}")
    lines.extend(["", "## Rejected Examples", ""])
    if rejected.empty:
        lines.append("- None.")
    else:
        for _, row in rejected.head(12).iterrows():
            primary = safe_text(row["primary_dois"]) or "no primary DOI"
            lines.append(
                f"- `{row['source_result_id']}`: acquired `{row['acquired_doi']}` but represented primary is `{primary}`; "
                f"title `{safe_text(row['represented_title'])[:110]}`"
            )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- This is the gate between PDF acquisition and source_file promotion. A row can download a PDF and still be rejected here if the route came from a non-primary DOI or another weak lead.",
            "- Primary DOIs come from `source.tsv` and primary `source_identifier` rows only. Non-primary grounding URLs are preserved as leads, but they do not count as identity anchors.",
            "- Manual rows are not failures; they need human confirmation because the represented source has a weak/synthetic title, no primary DOI, or an incomplete text signal.",
            "",
            "## Output Files",
            "",
            f"- `{rel(OUT_TSV)}`",
            f"- `{rel(OUT_SUMMARY)}`",
        ]
    )
    OUT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    OUT_REPORT.write_text("\n".join(lines) + "\n")

    print(f"Wrote {OUT_TSV}")
    print(f"Wrote {OUT_SUMMARY}")
    print(f"Wrote {OUT_REPORT}")
    print(summary.to_string(index=False))

    if not rejected.empty:
        wrong_dois = Counter(rejected["acquired_doi"])
        print("\nTop rejected acquired DOIs:")
        for doi, count in wrong_dois.most_common(8):
            print(f"{doi}\t{count}")


if __name__ == "__main__":
    main()
