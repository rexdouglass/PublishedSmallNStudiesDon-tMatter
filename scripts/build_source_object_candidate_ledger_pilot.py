#!/usr/bin/env python3
"""Build a shared source-object candidate ledger for acquisition resolvers.

This is the staging layer between route attempts and source_file promotion. A
candidate can come from a PDF route, repository API, archive lookup, dataset
relation, or manual browser capture. Only identity-accepted candidates should be
promoted into source_file.
"""

from __future__ import annotations

import hashlib
import os
import re
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
PILOT = ROOT / "data" / "derived" / "effect_inflation_dataset" / "schema_pilot"
SAMPLE_N = int(os.environ.get("SCHEMA_PILOT_N", "300"))
SAMPLE_SUFFIX = f"sample_{SAMPLE_N}"

SOURCE_RESULT = PILOT / f"source_result_codebook_{SAMPLE_SUFFIX}.tsv"
SOURCE = PILOT / f"source_codebook_{SAMPLE_SUFFIX}.tsv"
SOURCE_IDENTIFIER = PILOT / f"source_identifier_codebook_{SAMPLE_SUFFIX}.tsv"
PDF_ATTEMPTS = PILOT / f"original_pdf_acquisition_attempts_{SAMPLE_SUFFIX}.tsv"
PDF_IDENTITY = PILOT / f"original_pdf_identity_check_{SAMPLE_SUFFIX}.tsv"

OUT_TSV = PILOT / f"source_object_candidate_codebook_{SAMPLE_SUFFIX}.tsv"
OUT_SUMMARY = PILOT / f"source_object_candidate_summary_{SAMPLE_SUFFIX}.tsv"
OUT_REPORT = ROOT / "reports" / f"source_object_candidate_ledger_{SAMPLE_SUFFIX}_2026-04-30.md"

DOI_RE = re.compile(r"10\.\d{4,9}/[-._;()/:A-Z0-9]+", re.I)
PMID_RE = re.compile(r"\b\d{6,9}\b")
PMCID_RE = re.compile(r"\bPMC\d+\b", re.I)
NCT_RE = re.compile(r"\bNCT\d{8}\b", re.I)

CANDIDATE_COLUMNS = [
    "candidate_id",
    "result_id",
    "represented_source_id",
    "route_module",
    "route_family",
    "input_primary_doi",
    "input_pmid",
    "input_pmcid",
    "input_nct",
    "input_title",
    "input_first_author",
    "input_year",
    "query_used",
    "api_url",
    "api_record_id",
    "api_record_json_path",
    "candidate_url",
    "candidate_final_url",
    "candidate_repository",
    "candidate_object_type_guess",
    "candidate_relation_type",
    "candidate_doi",
    "candidate_pmid",
    "candidate_pmcid",
    "candidate_title",
    "candidate_authors",
    "candidate_year",
    "candidate_license",
    "candidate_access_status",
    "download_attempted",
    "http_status",
    "mime_type",
    "content_length",
    "local_path",
    "sha256",
    "extracted_text_path",
    "doi_in_candidate_text",
    "pmid_in_candidate_text",
    "pmcid_in_candidate_text",
    "title_similarity",
    "author_year_match",
    "identity_decision",
    "identity_reason",
    "evidence_scale_candidate",
    "failure_code",
    "failure_detail",
    "created_at",
]


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


def stable_id(prefix: str, *parts: object) -> str:
    text = "\n".join(safe_text(part) for part in parts)
    return f"{prefix}_{hashlib.sha256(text.encode('utf-8')).hexdigest()[:12]}"


def normalize_doi(value: str) -> str:
    text = safe_text(value)
    text = re.sub(r"^doi:\s*", "", text, flags=re.I)
    text = re.sub(r"^https?://(?:dx\.)?doi\.org/", "", text, flags=re.I)
    match = DOI_RE.search(text)
    if not match:
        return ""
    return re.sub(r"(10\.\d{4,9})//+", r"\1/", match.group(0).rstrip(".,;)"), flags=re.I).lower()


def first_match(regex: re.Pattern[str], value: str) -> str:
    match = regex.search(safe_text(value))
    return match.group(0) if match else ""


def host(url: str) -> str:
    try:
        return urllib.parse.urlsplit(url).netloc
    except Exception:
        return ""


def route_family(route: str) -> str:
    lower = safe_text(route).lower()
    for name in [
        "unpaywall",
        "crossref",
        "openalex",
        "semantic_scholar",
        "europepmc",
        "pubmed",
        "pmc",
        "doi_accept",
        "fatcat",
        "wayback",
        "openaire",
        "core",
        "base",
        "osf",
        "dataverse",
        "zenodo",
        "figshare",
        "manual",
    ]:
        if lower.startswith(name) or name in lower:
            return name
    return "other"


def object_type_guess(failure_code: str, pdf_valid: str, attempt_kind: str, mime_type: str) -> str:
    failure = safe_text(failure_code).lower()
    mime = safe_text(mime_type).lower()
    if safe_text(pdf_valid).lower() == "true":
        return "full_article_pdf"
    if safe_text(attempt_kind) == "metadata":
        return "metadata_record"
    if "captcha" in failure or "bot" in failure:
        return "bot_block"
    if "403" in failure or "blocked" in failure:
        return "blocked_page"
    if "paywall" in failure or "login" in failure:
        return "paywall_or_login_page"
    if "404" in failure:
        return "missing_url"
    if "html" in failure or "html" in mime:
        return "landing_or_html_page"
    if "pdf" in mime:
        return "pdf_not_validated"
    return "unknown_candidate"


def evidence_candidate(identity_decision: str, attempt_kind: str, failure_code: str, object_type: str) -> str:
    if identity_decision == "accepted_pdf_identity":
        return "level5_candidate_full_article"
    if identity_decision.startswith("reject_"):
        return "reject_no_promotion"
    if identity_decision == "needs_manual_identity_check":
        return "manual_identity_check_before_promotion"
    if attempt_kind == "metadata" and failure_code.startswith("ok"):
        return "level4_metadata_candidate"
    if object_type in {"landing_or_html_page", "paywall_or_login_page"}:
        return "level4_or_blocker_no_source_bytes"
    return "no_promotion"


def source_inputs(sources: pd.DataFrame, identifiers: pd.DataFrame) -> dict[str, dict[str, str]]:
    out: dict[str, dict[str, str]] = {}
    source_lookup = {safe_text(row["source_id"]): row for _, row in sources.iterrows()}
    for source_id, row in source_lookup.items():
        out[source_id] = {
            "input_primary_doi": normalize_doi(safe_text(row.get("doi"))),
            "input_pmid": first_match(PMID_RE, safe_text(row.get("pmid"))),
            "input_pmcid": "",
            "input_nct": first_match(NCT_RE, safe_text(row.get("registry_id"))),
            "input_title": safe_text(row.get("title")),
            "input_first_author": "",
            "input_year": safe_text(row.get("publication_year")),
        }
    for _, row in identifiers.iterrows():
        if safe_text(row.get("is_primary")).lower() != "true":
            continue
        source_id = safe_text(row.get("source_id"))
        if source_id not in out:
            out[source_id] = {
                "input_primary_doi": "",
                "input_pmid": "",
                "input_pmcid": "",
                "input_nct": "",
                "input_title": "",
                "input_first_author": "",
                "input_year": "",
            }
        typ = safe_text(row.get("identifier_type")).lower()
        value = safe_text(row.get("identifier_value")) or safe_text(row.get("identifier_url"))
        if typ in {"doi", "url"} and not out[source_id]["input_primary_doi"]:
            out[source_id]["input_primary_doi"] = normalize_doi(value)
        if typ == "pmid" and not out[source_id]["input_pmid"]:
            out[source_id]["input_pmid"] = first_match(PMID_RE, value)
        if typ == "pmcid" and not out[source_id]["input_pmcid"]:
            out[source_id]["input_pmcid"] = first_match(PMCID_RE, value).upper()
        if typ == "nct" and not out[source_id]["input_nct"]:
            out[source_id]["input_nct"] = first_match(NCT_RE, value).upper()
    return out


def main() -> None:
    source_result = pd.read_csv(SOURCE_RESULT, sep="\t", dtype=str, keep_default_na=False)
    sources = pd.read_csv(SOURCE, sep="\t", dtype=str, keep_default_na=False)
    identifiers = pd.read_csv(SOURCE_IDENTIFIER, sep="\t", dtype=str, keep_default_na=False)
    attempts = pd.read_csv(PDF_ATTEMPTS, sep="\t", dtype=str, keep_default_na=False)
    identity = pd.read_csv(PDF_IDENTITY, sep="\t", dtype=str, keep_default_na=False)

    input_by_source = source_inputs(sources, identifiers)
    sr_lookup = {safe_text(row["source_result_id"]): row for _, row in source_result.iterrows()}
    identity_lookup = {
        (safe_text(row["source_result_id"]), safe_text(row["local_path"])): row
        for _, row in identity.iterrows()
    }
    created_at = datetime.now(timezone.utc).isoformat()

    rows: list[dict[str, object]] = []
    for _, attempt in attempts.iterrows():
        result_id = safe_text(attempt.get("source_result_id"))
        represented_source_id = safe_text(attempt.get("represented_source_id"))
        source_input = input_by_source.get(represented_source_id, {})
        identity_row = identity_lookup.get((result_id, safe_text(attempt.get("local_path"))))
        route = safe_text(attempt.get("route"))
        attempt_kind = safe_text(attempt.get("attempt_kind"))
        failure = safe_text(attempt.get("failure_reason"))
        mime = safe_text(attempt.get("content_type"))
        pdf_valid = safe_text(attempt.get("pdf_valid"))
        local_path = safe_text(attempt.get("local_path"))
        object_guess = object_type_guess(failure, pdf_valid, attempt_kind, mime)
        identity_decision = safe_text(identity_row.get("identity_decision")) if identity_row is not None else ""
        identity_reason = safe_text(identity_row.get("identity_decision_reason")) if identity_row is not None else ""
        title_similarity = safe_text(identity_row.get("title_line_similarity")) if identity_row is not None else ""

        candidate_url = safe_text(attempt.get("candidate_url"))
        final_url = safe_text(attempt.get("final_url"))
        candidate_doi = normalize_doi(safe_text(attempt.get("doi")) or candidate_url or final_url)

        row = {
            "candidate_id": stable_id("cand", result_id, route, candidate_url, local_path, safe_text(attempt.get("sha256"))),
            "result_id": result_id,
            "represented_source_id": represented_source_id,
            "route_module": route,
            "route_family": route_family(route),
            "input_primary_doi": source_input.get("input_primary_doi", ""),
            "input_pmid": source_input.get("input_pmid", ""),
            "input_pmcid": source_input.get("input_pmcid", ""),
            "input_nct": source_input.get("input_nct", ""),
            "input_title": source_input.get("input_title", safe_text(attempt.get("represented_title"))),
            "input_first_author": source_input.get("input_first_author", ""),
            "input_year": source_input.get("input_year", ""),
            "query_used": safe_text(attempt.get("doi")) or candidate_url,
            "api_url": "",
            "api_record_id": "",
            "api_record_json_path": "",
            "candidate_url": candidate_url if candidate_url.startswith(("http://", "https://")) else "",
            "candidate_final_url": final_url,
            "candidate_repository": host(final_url or candidate_url),
            "candidate_object_type_guess": object_guess,
            "candidate_relation_type": "primary_identifier_route",
            "candidate_doi": candidate_doi,
            "candidate_pmid": "",
            "candidate_pmcid": "",
            "candidate_title": "",
            "candidate_authors": "",
            "candidate_year": "",
            "candidate_license": "",
            "candidate_access_status": failure,
            "download_attempted": str(attempt_kind == "pdf_candidate").lower(),
            "http_status": safe_text(attempt.get("http_status")),
            "mime_type": mime,
            "content_length": safe_text(attempt.get("byte_count")),
            "local_path": local_path,
            "sha256": safe_text(attempt.get("sha256")),
            "extracted_text_path": "",
            "doi_in_candidate_text": safe_text(identity_row.get("primary_doi_in_pdf_text")) if identity_row is not None else "",
            "pmid_in_candidate_text": "",
            "pmcid_in_candidate_text": "",
            "title_similarity": title_similarity,
            "author_year_match": "",
            "identity_decision": identity_decision or ("metadata_only" if attempt_kind == "metadata" else "not_downloaded_or_not_identity_checked"),
            "identity_reason": identity_reason,
            "evidence_scale_candidate": evidence_candidate(identity_decision, attempt_kind, failure, object_guess),
            "failure_code": failure,
            "failure_detail": safe_text(attempt.get("route_note")),
            "created_at": created_at,
        }
        rows.append(row)

    ledger = pd.DataFrame(rows, columns=CANDIDATE_COLUMNS)
    OUT_TSV.parent.mkdir(parents=True, exist_ok=True)
    ledger.to_csv(OUT_TSV, sep="\t", index=False)

    level_counts = source_result["evidence_level"].value_counts().sort_index()
    below_level5 = pd.to_numeric(source_result["evidence_level"], errors="coerce").fillna(0).lt(5).sum()
    summary_rows = [
        {"metric": "sample_n", "value": SAMPLE_N},
        {"metric": "candidate_rows", "value": len(ledger)},
        {"metric": "represented_results_with_candidates", "value": ledger["result_id"].nunique()},
        {"metric": "below_level5_rows_after_pdf_promotion", "value": int(below_level5)},
        {"metric": "created_at_utc", "value": created_at},
    ]
    for level, count in level_counts.items():
        summary_rows.append({"metric": f"source_result_level::{level}", "value": int(count)})
    for key, count in ledger["route_family"].value_counts().sort_index().items():
        summary_rows.append({"metric": f"route_family::{key}", "value": int(count)})
    for key, count in ledger["candidate_object_type_guess"].value_counts().sort_index().items():
        summary_rows.append({"metric": f"candidate_object_type::{key}", "value": int(count)})
    for key, count in ledger["identity_decision"].value_counts().sort_index().items():
        summary_rows.append({"metric": f"identity_decision::{key}", "value": int(count)})
    for key, count in ledger["evidence_scale_candidate"].value_counts().sort_index().items():
        summary_rows.append({"metric": f"evidence_scale_candidate::{key}", "value": int(count)})
    summary = pd.DataFrame(summary_rows)
    summary.to_csv(OUT_SUMMARY, sep="\t", index=False)

    accepted = ledger[ledger["identity_decision"].eq("accepted_pdf_identity")]
    blocked = ledger[ledger["candidate_object_type_guess"].isin(["blocked_page", "bot_block", "paywall_or_login_page"])]
    metadata = ledger[ledger["candidate_object_type_guess"].eq("metadata_record")]

    lines = [
        "# Source Object Candidate Ledger",
        "",
        f"- Candidate rows written: {len(ledger)}",
        f"- Result rows represented in candidate ledger: {ledger['result_id'].nunique()}",
        f"- Identity-accepted source-object candidates: {len(accepted)}",
        f"- Block/paywall/bot candidate rows logged: {len(blocked)}",
        f"- Metadata-only candidate rows logged: {len(metadata)}",
        f"- Rows still below level 5 after PDF promotion: {int(below_level5)}/{SAMPLE_N}",
        "",
        "## Why This Exists",
        "",
        "This ledger is the staging layer between discovery routes and `source_file` promotion. Future OpenAIRE, CORE, BASE, Fatcat/Wayback, OSF, Dataverse, Zenodo, Figshare, AACT, Paperclip, and manual-capture resolvers should append rows here first. A row does not promote just because a route found metadata or a URL; it promotes only after mirrored bytes pass the relevant identity gate.",
        "",
        "## Candidate Evidence Classes",
        "",
    ]
    for key, count in ledger["evidence_scale_candidate"].value_counts().items():
        lines.append(f"- `{key}`: {int(count)}")
    lines.extend(["", "## Route Families", ""])
    for key, count in ledger["route_family"].value_counts().items():
        lines.append(f"- `{key}`: {int(count)}")
    lines.extend(["", "## Next Resolver Modules To Add", ""])
    lines.extend(
        [
            "1. OpenAIRE/CORE/BASE repository candidates for DOI-grounded level-4 rows.",
            "2. Fatcat/Wayback candidates for 403/404/dead publisher and repository URLs.",
            "3. Crossref/DataCite related-object candidates for supplements, datasets, and preprints.",
            "4. OSF/PsyArXiv/SocArXiv candidates for psychology/social-science preprints and project files.",
            "5. AACT historical snapshot candidates for registry-version drift.",
            "6. Manual/Zotero capture candidates for rows still blocked after repository/archive routes.",
        ]
    )
    lines.extend(
        [
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


if __name__ == "__main__":
    main()
