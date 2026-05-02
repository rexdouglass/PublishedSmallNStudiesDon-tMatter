#!/usr/bin/env python3
"""Extract candidate value-bearing snippets from mirrored source objects.

This is a conservative triage pass. It does not promote rows to level 6. It
extracts text from structured XML/HTML/PDF objects, searches for linked
source-result labels and numeric values, and writes snippets that a verifier or
human can inspect next.
"""

from __future__ import annotations

import os
import re
import warnings
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning

try:
    import pdfplumber
except Exception:  # pragma: no cover - optional parser in some environments.
    pdfplumber = None


ROOT = Path(__file__).resolve().parents[1]
PILOT = ROOT / "data" / "derived" / "effect_inflation_dataset" / "schema_pilot"
SAMPLE_N = int(os.environ.get("SCHEMA_PILOT_N", "300"))
SAMPLE_SUFFIX = f"sample_{SAMPLE_N}"

WORKLIST_IN = PILOT / f"level6_source_object_extraction_worklist_{SAMPLE_SUFFIX}.tsv"
SOURCE_RESULT_IN = PILOT / f"source_result_codebook_{SAMPLE_SUFFIX}.tsv"

OUT_TSV = PILOT / f"level6_text_candidate_snippets_{SAMPLE_SUFFIX}.tsv"
OUT_SUMMARY = PILOT / f"level6_text_candidate_snippets_summary_{SAMPLE_SUFFIX}.tsv"
OUT_REPORT = ROOT / "reports" / f"level6_text_candidate_snippets_{SAMPLE_SUFFIX}_2026-04-30.md"

DEFAULT_ROUTES = "structured_xml_first,html_first"
ROUTES = {
    item.strip()
    for item in os.environ.get("LEVEL6_TEXT_CANDIDATE_ROUTES", DEFAULT_ROUTES).split(",")
    if item.strip()
}
MAX_SNIPPETS_PER_RESULT = 8
MAX_PDF_PAGES = int(os.environ.get("LEVEL6_TEXT_CANDIDATE_MAX_PDF_PAGES", "5"))

warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)


def safe_text(value: object) -> str:
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value).replace("\t", " ").replace("\r", " ").replace("\n", " ")).strip()


def norm_number(value: object) -> str:
    text = safe_text(value)
    if not text:
        return ""
    try:
        number = float(text)
    except ValueError:
        match = re.search(r"-?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?", text)
        if not match:
            return ""
        try:
            number = float(match.group(0))
        except ValueError:
            return ""
    if abs(number) >= 1000:
        return f"{number:.0f}"
    if abs(number - round(number)) < 1e-9:
        return f"{number:.0f}"
    return f"{number:.6g}"


def rel(path: Path | str) -> str:
    p = Path(path)
    if not p.is_absolute():
        p = ROOT / p
    try:
        return str(p.relative_to(ROOT))
    except ValueError:
        return str(p)


def context_snippet(text: str, start: int, end: int, width: int = 220) -> str:
    left = max(0, start - width)
    right = min(len(text), end + width)
    return safe_text(text[left:right])


def extract_text_segments(path: Path, route: str) -> tuple[list[dict[str, object]], str]:
    if route in {"structured_xml_first", "html_first"}:
        try:
            raw = path.read_bytes()
        except OSError as exc:
            return [], f"read_failed:{type(exc).__name__}:{exc}"
        # `xml` parsing needs lxml in this environment; html.parser is enough
        # for this first-pass text triage because we are not yet preserving XPath.
        soup = BeautifulSoup(raw, "html.parser")
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()
        text = soup.get_text("\n")
        return [{"locator_type": "document_text", "locator": "document", "text": text}], "text_extracted"

    if route == "pdf_cascade":
        if pdfplumber is None:
            return [], "pdfplumber_unavailable"
        segments: list[dict[str, object]] = []
        try:
            with pdfplumber.open(path) as pdf:
                for page_num, page in enumerate(pdf.pages[:MAX_PDF_PAGES], start=1):
                    text = page.extract_text(layout=True) or page.extract_text() or ""
                    if text:
                        segments.append({"locator_type": "pdf_page", "locator": str(page_num), "text": text})
        except Exception as exc:  # noqa: BLE001 - candidate extraction should record parser failures.
            return [], f"pdf_parse_failed:{type(exc).__name__}:{exc}"
        return segments, "text_extracted" if segments else "no_text_extracted"

    return [], f"unsupported_route:{route}"


def label_terms(row: pd.Series) -> list[str]:
    terms: list[str] = []
    for col in ["result_label", "outcome_label", "verbatim_outcome_text"]:
        text = safe_text(row.get(col))
        if len(text) >= 20:
            terms.append(text[:160])
    return list(dict.fromkeys(terms))


def numeric_terms(row: pd.Series) -> list[tuple[str, str]]:
    terms: list[tuple[str, str]] = []
    for col in [
        "verbatim_effect_text",
        "native_effect_value",
        "verbatim_p_text",
        "native_p_value",
        "verbatim_n_text",
        "native_n_total",
        "standardized_n",
        "d",
        "standardized_effect_value",
    ]:
        text = norm_number(row.get(col))
        if not text:
            continue
        # Tiny integers are too common to be useful as standalone source hits.
        if re.fullmatch(r"\d{1,2}", text):
            continue
        terms.append((col, text))
    return list(dict.fromkeys(terms))


def find_hits(text: str, term: str, max_hits: int = 3) -> list[tuple[int, int]]:
    if not term:
        return []
    flags = re.I
    escaped = re.escape(term)
    if re.fullmatch(r"-?\d+(?:\.\d+)?", term):
        pattern = rf"(?<![\d.]){escaped}(?![\d.])"
    else:
        pattern = escaped
    hits: list[tuple[int, int]] = []
    for match in re.finditer(pattern, text, flags):
        hits.append((match.start(), match.end()))
        if len(hits) >= max_hits:
            break
    return hits


def main() -> None:
    worklist = pd.read_csv(WORKLIST_IN, sep="\t", dtype=str, keep_default_na=False)
    source_results = pd.read_csv(SOURCE_RESULT_IN, sep="\t", dtype=str, keep_default_na=False)
    by_srid = {safe_text(row["source_result_id"]): row for _, row in source_results.iterrows()}

    targets = worklist.loc[
        worklist["worklist_status"].eq("needs_extraction")
        & worklist["parser_route"].isin(ROUTES)
        & worklist["local_file_exists"].astype(str).str.lower().eq("true")
    ].copy()

    rows: list[dict[str, object]] = []
    for _, file_row in targets.iterrows():
        path = Path(safe_text(file_row.get("local_path")))
        if not path.is_absolute():
            path = ROOT / path
        route = safe_text(file_row.get("parser_route"))
        segments, extraction_status = extract_text_segments(path, route)
        linked_ids = [item for item in safe_text(file_row.get("linked_source_result_ids")).split("|") if item]
        if not linked_ids:
            rows.append(
                {
                    "source_file_id": safe_text(file_row.get("source_file_id")),
                    "source_result_id": "",
                    "parser_route": route,
                    "local_path": rel(path),
                    "extraction_status": extraction_status,
                    "candidate_status": "no_linked_source_result",
                }
            )
            continue
        for srid in linked_ids:
            result_row = by_srid.get(srid)
            if result_row is None:
                continue
            if not segments:
                rows.append(
                    {
                        "source_file_id": safe_text(file_row.get("source_file_id")),
                        "source_result_id": srid,
                        "parser_route": route,
                        "local_path": rel(path),
                        "extraction_status": extraction_status,
                        "candidate_status": "parse_failed_or_no_text",
                    }
                )
                continue
            snippets_added = 0
            label_hit_count = 0
            numeric_hit_count = 0
            for segment in segments:
                text = str(segment["text"])
                for term in label_terms(result_row):
                    for start, end in find_hits(text, term, max_hits=1):
                        label_hit_count += 1
                        if snippets_added < MAX_SNIPPETS_PER_RESULT:
                            rows.append(
                                {
                                    "source_file_id": safe_text(file_row.get("source_file_id")),
                                    "source_result_id": srid,
                                    "parser_route": route,
                                    "local_path": rel(path),
                                    "extraction_status": extraction_status,
                                    "candidate_status": "label_hit",
                                    "match_kind": "label",
                                    "match_field": "result_or_outcome_label",
                                    "match_value": term,
                                    "locator_type": segment["locator_type"],
                                    "locator": segment["locator"],
                                    "char_start": start,
                                    "char_end": end,
                                    "snippet": context_snippet(text, start, end),
                                }
                            )
                            snippets_added += 1
                for field, term in numeric_terms(result_row):
                    for start, end in find_hits(text, term, max_hits=2):
                        numeric_hit_count += 1
                        if snippets_added < MAX_SNIPPETS_PER_RESULT:
                            rows.append(
                                {
                                    "source_file_id": safe_text(file_row.get("source_file_id")),
                                    "source_result_id": srid,
                                    "parser_route": route,
                                    "local_path": rel(path),
                                    "extraction_status": extraction_status,
                                    "candidate_status": "numeric_hit",
                                    "match_kind": "numeric",
                                    "match_field": field,
                                    "match_value": term,
                                    "locator_type": segment["locator_type"],
                                    "locator": segment["locator"],
                                    "char_start": start,
                                    "char_end": end,
                                    "snippet": context_snippet(text, start, end),
                                }
                            )
                            snippets_added += 1
            if snippets_added == 0:
                rows.append(
                    {
                        "source_file_id": safe_text(file_row.get("source_file_id")),
                        "source_result_id": srid,
                        "parser_route": route,
                        "local_path": rel(path),
                        "extraction_status": extraction_status,
                        "candidate_status": "text_extracted_no_label_or_numeric_hit",
                        "label_hit_count": label_hit_count,
                        "numeric_hit_count": numeric_hit_count,
                    }
                )

    out = pd.DataFrame(rows)
    OUT_TSV.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT_TSV, sep="\t", index=False)

    summary_rows: list[dict[str, object]] = [
        {"metric": "sample_n", "value": SAMPLE_N},
        {"metric": "routes_attempted", "value": ",".join(sorted(ROUTES))},
        {"metric": "pdf_pages_cap", "value": MAX_PDF_PAGES},
        {"metric": "source_files_attempted", "value": int(len(targets))},
        {"metric": "snippet_rows", "value": int(len(out))},
        {
            "metric": "source_results_with_any_candidate_hit",
            "value": int(out.loc[out.get("candidate_status", pd.Series(dtype=str)).isin(["label_hit", "numeric_hit"]), "source_result_id"].nunique()),
        },
        {"metric": "created_at_utc", "value": datetime.now(timezone.utc).isoformat()},
    ]
    for key, value in out.get("candidate_status", pd.Series(dtype=str)).value_counts().sort_index().items():
        summary_rows.append({"metric": f"candidate_status::{key}", "value": int(value)})
    for key, value in out.get("parser_route", pd.Series(dtype=str)).value_counts().sort_index().items():
        summary_rows.append({"metric": f"parser_route::{key}", "value": int(value)})
    summary = pd.DataFrame(summary_rows)
    summary.to_csv(OUT_SUMMARY, sep="\t", index=False)

    hit_results = int(summary.loc[summary["metric"].eq("source_results_with_any_candidate_hit"), "value"].iloc[0])
    lines = [
        "# Level-6 Text Candidate Snippets",
        "",
        f"- Sample rows: {SAMPLE_N}",
        f"- Parser routes attempted: {', '.join(sorted(ROUTES))}",
        f"- PDF pages cap if `pdf_cascade` is enabled: {MAX_PDF_PAGES}",
        f"- Source files attempted: {len(targets)}",
        f"- Snippet/status rows written: {len(out)}",
        f"- Linked source-result rows with at least one label or numeric candidate hit: {hit_results}",
        "",
        "## Candidate Status",
        "",
    ]
    for _, row in out.get("candidate_status", pd.Series(dtype=str)).value_counts().rename_axis("status").reset_index(name="n").iterrows():
        lines.append(f"- `{row['status']}`: {int(row['n'])}")
    lines.extend(["", "## Interpretation", ""])
    lines.append(
        "- Candidate hits are not level-6 evidence. They are triage snippets for the next verifier pass; promotion still requires exact source-result support and D/N recomputation."
    )
    lines.append(
        "- Numeric-only hits are especially weak unless the surrounding snippet identifies the same outcome/table/contrast."
    )
    lines.extend(["", "## Output Files", "", f"- `{rel(OUT_TSV)}`", f"- `{rel(OUT_SUMMARY)}`"])
    OUT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    OUT_REPORT.write_text("\n".join(lines) + "\n")

    print(f"Wrote {OUT_TSV}")
    print(f"Wrote {OUT_SUMMARY}")
    print(f"Wrote {OUT_REPORT}")
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
