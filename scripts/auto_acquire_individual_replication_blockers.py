#!/usr/bin/env python3
"""Try open-source acquisition routes for unresolved individual-replication blockers.

This is a bounded follow-up to the manual acquisition TSVs produced by the
individual-replication search pipeline. It does not promote rows. It queries
open metadata services for each blocker DOI, mirrors candidate PDF/HTML source
objects when possible, and writes an auditable attempt ledger for GPT/human
follow-up.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import time
from pathlib import Path
from typing import Any
from urllib.parse import quote, urlparse

import pandas as pd
import requests


ROOT = Path(__file__).resolve().parents[1]
WORKLIST_DIR = ROOT / "steps" / "individual_replication_papers" / "figure1"
DEFAULT_MANUAL = WORKLIST_DIR / "individual-paper-manual-acquisition-task-batch007.tsv"
PROMOTED = ROOT / "data" / "derived" / "replication_pairs" / "harvest" / "promoted" / "individual_replication_papers__promoted_pairs.csv"
OUT_DIR = ROOT / "steps" / "individual_replication_papers" / "figure1" / "auto_mining"
RAW_DIR = ROOT / "data" / "raw" / "replication_projects" / "individual_auto_mining_blockers"
OUT_ATTEMPTS = OUT_DIR / "individual-paper-auto-acquisition-attempts.tsv"
OUT_REPORT = ROOT / "reports" / "figure1_individual_replication_auto_acquisition_2026-05-05.md"

EMAIL = "figure1-mining@example.com"
HEADERS = {
    "User-Agent": f"figure1-individual-replication-miner/0.1 (mailto:{EMAIL})",
    "Accept": "text/html,application/pdf,application/json;q=0.9,*/*;q=0.8",
}
DOI_RE = re.compile(r"10\.\d{4,9}/[^\s\"<>]+", re.I)
BLOCKED_TERMS = [
    "access denied",
    "cookie absent",
    "enable cookies",
    "captcha",
    "are you a robot",
    "not authorized",
    "purchase access",
    "institutional login",
]


ATTEMPT_FIELDS = [
    "candidate_id",
    "candidate_name",
    "source_role",
    "doi",
    "metadata_service",
    "candidate_url",
    "http_status",
    "content_type",
    "bytes",
    "sha256",
    "local_path",
    "access_state",
    "error_or_note",
]


def clean(value: Any) -> str:
    if value is None:
        return ""
    return str(value).replace("\t", " ").replace("\n", " ").replace("\r", " ").strip()


def normalize_doi(value: str) -> str:
    value = clean(value).lower()
    value = value.replace("https://doi.org/", "")
    value = value.replace("http://dx.doi.org/", "")
    value = value.replace("doi:", "")
    value = value.strip(" .;,)]}")
    return value


def doi_values(row: pd.Series) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for role, field in [("original", "original_doi"), ("replication", "replication_doi")]:
        doi = normalize_doi(row.get(field, ""))
        if DOI_RE.match(doi):
            out.append((role, doi))
    try:
        urls = json.loads(clean(row.get("source_object_urls_json")) or "[]")
    except json.JSONDecodeError:
        urls = []
    for url in urls:
        for match in DOI_RE.findall(clean(url)):
            doi = normalize_doi(match)
            role = "source_url"
            if doi and (role, doi) not in out:
                out.append((role, doi))
    deduped: list[tuple[str, str]] = []
    seen = set()
    for role, doi in out:
        key = (role, doi)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(key)
    return deduped


def request_json(url: str, *, params: dict[str, Any] | None = None) -> dict[str, Any]:
    try:
        r = requests.get(url, params=params, headers=HEADERS, timeout=30)
        if r.status_code != 200:
            return {"_error": f"http_{r.status_code}", "_text": r.text[:300]}
        return r.json()
    except Exception as exc:  # noqa: BLE001
        return {"_error": repr(exc)}


def candidate_urls_for_doi(doi: str) -> list[tuple[str, str]]:
    urls: list[tuple[str, str]] = [("doi_resolver", f"https://doi.org/{doi}")]

    openalex = request_json(f"https://api.openalex.org/works/doi:{quote(doi, safe='')}")
    if not openalex.get("_error"):
        oa = openalex.get("open_access") or {}
        if oa.get("oa_url"):
            urls.append(("openalex_oa_url", oa["oa_url"]))
        for location in [openalex.get("primary_location") or {}, *(openalex.get("locations") or [])]:
            pdf_url = location.get("pdf_url")
            landing = location.get("landing_page_url")
            if pdf_url:
                urls.append(("openalex_pdf_url", pdf_url))
            if landing:
                urls.append(("openalex_landing_page_url", landing))
    else:
        urls.append(("openalex_error", f"metadata_error:{openalex.get('_error')}"))

    unpaywall = request_json(f"https://api.unpaywall.org/v2/{quote(doi, safe='')}", params={"email": EMAIL})
    if not unpaywall.get("_error"):
        locations = []
        if isinstance(unpaywall.get("best_oa_location"), dict):
            locations.append(unpaywall["best_oa_location"])
        locations.extend(unpaywall.get("oa_locations") or [])
        for location in locations:
            pdf_url = location.get("url_for_pdf")
            landing = location.get("url_for_landing_page")
            if pdf_url:
                urls.append(("unpaywall_pdf_url", pdf_url))
            if landing:
                urls.append(("unpaywall_landing_page_url", landing))
    else:
        urls.append(("unpaywall_error", f"metadata_error:{unpaywall.get('_error')}"))

    s2 = request_json(
        f"https://api.semanticscholar.org/graph/v1/paper/DOI:{quote(doi, safe='')}",
        params={"fields": "title,externalIds,url,openAccessPdf"},
    )
    if not s2.get("_error"):
        pdf = s2.get("openAccessPdf") or {}
        if pdf.get("url"):
            urls.append(("semantic_scholar_open_access_pdf", pdf["url"]))
        if s2.get("url"):
            urls.append(("semantic_scholar_landing_page", s2["url"]))
    else:
        urls.append(("semantic_scholar_error", f"metadata_error:{s2.get('_error')}"))

    deduped: list[tuple[str, str]] = []
    seen = set()
    for service, url in urls:
        if url.startswith("metadata_error:"):
            key = (service, url)
        else:
            key = url
        if key in seen:
            continue
        seen.add(key)
        deduped.append((service, url))
    return deduped


def safe_name(value: str, max_len: int = 88) -> str:
    value = re.sub(r"[^a-zA-Z0-9]+", "_", value).strip("_").lower()
    return (value[:max_len].strip("_") or "source")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def classify_access(status: int | str, content_type: str, data: bytes, url: str) -> tuple[str, str]:
    if isinstance(status, str):
        return "metadata_error", status
    if status >= 400:
        return "blocked_or_not_found", f"http_{status}"
    sample = data[:5000].decode("utf-8", errors="ignore").lower()
    if any(term in sample for term in BLOCKED_TERMS):
        return "blocked_or_access_wall", "blocked_terms_in_response"
    if data.startswith(b"%PDF") or "pdf" in content_type.lower():
        return "mirrored_pdf", ""
    if "html" in content_type.lower() or sample.lstrip().startswith("<"):
        if "doi.org" in urlparse(url).netloc.lower():
            return "mirrored_landing_or_resolver_html", "resolver_or_metadata_html"
        return "mirrored_html", ""
    return "mirrored_other", ""


def download_candidate(candidate_id: str, doi: str, service: str, url: str) -> dict[str, Any]:
    if url.startswith("metadata_error:"):
        return {
            "metadata_service": service,
            "candidate_url": url,
            "http_status": "",
            "content_type": "",
            "bytes": "",
            "sha256": "",
            "local_path": "",
            "access_state": "metadata_error",
            "error_or_note": url,
        }
    try:
        r = requests.get(url, headers=HEADERS, timeout=45, allow_redirects=True)
        content = r.content or b""
        content_type = clean(r.headers.get("content-type"))
        state, note = classify_access(r.status_code, content_type, content, url)
        parsed = urlparse(r.url)
        ext = ".pdf" if state == "mirrored_pdf" else ".html" if "html" in content_type.lower() else ".bin"
        local_path = ""
        digest = ""
        if r.status_code < 400 and content and state.startswith("mirrored"):
            digest = sha256_bytes(content)
            out_dir = RAW_DIR / candidate_id
            out_dir.mkdir(parents=True, exist_ok=True)
            filename = f"{safe_name(service)}__{safe_name(doi)}__{safe_name(parsed.netloc)}__{digest[:12]}{ext}"
            path = out_dir / filename
            path.write_bytes(content)
            local_path = str(path.relative_to(ROOT))
        return {
            "metadata_service": service,
            "candidate_url": r.url,
            "http_status": r.status_code,
            "content_type": content_type,
            "bytes": len(content),
            "sha256": digest,
            "local_path": local_path,
            "access_state": state,
            "error_or_note": note,
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "metadata_service": service,
            "candidate_url": url,
            "http_status": "",
            "content_type": "",
            "bytes": "",
            "sha256": "",
            "local_path": "",
            "access_state": "request_error",
            "error_or_note": repr(exc),
        }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manual-task", type=Path, default=DEFAULT_MANUAL)
    parser.add_argument("--replace", action="store_true")
    args = parser.parse_args()
    if not args.manual_task.exists():
        raise FileNotFoundError(args.manual_task)

    manual = pd.read_csv(args.manual_task, sep="\t", dtype=str, keep_default_na=False).fillna("")
    promoted = pd.read_csv(PROMOTED, dtype=str, keep_default_na=False).fillna("") if PROMOTED.exists() else pd.DataFrame()
    promoted_candidates = set(promoted.get("match_author", pd.Series(dtype=str)).astype(str))

    rows: list[dict[str, Any]] = []
    for _, task in manual.iterrows():
        candidate_id = clean(task.get("candidate_id"))
        if candidate_id in promoted_candidates:
            continue
        dois = doi_values(task)
        if not dois:
            rows.append(
                {
                    "candidate_id": candidate_id,
                    "candidate_name": clean(task.get("candidate_name")),
                    "source_role": "",
                    "doi": "",
                    "metadata_service": "no_doi_available",
                    "candidate_url": "",
                    "http_status": "",
                    "content_type": "",
                    "bytes": "",
                    "sha256": "",
                    "local_path": "",
                    "access_state": "needs_title_or_manual_search",
                    "error_or_note": "No DOI-like identifier in manual task row.",
                }
            )
            continue
        for source_role, doi in dois:
            for service, url in candidate_urls_for_doi(doi):
                attempt = download_candidate(candidate_id, doi, service, url)
                attempt.update(
                    {
                        "candidate_id": candidate_id,
                        "candidate_name": clean(task.get("candidate_name")),
                        "source_role": source_role,
                        "doi": doi,
                    }
                )
                rows.append(attempt)
                time.sleep(0.15)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with OUT_ATTEMPTS.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=ATTEMPT_FIELDS, delimiter="\t", extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: clean(row.get(field, "")) for field in ATTEMPT_FIELDS})

    df = pd.DataFrame(rows)
    success = df[df["access_state"].astype(str).str.startswith("mirrored_pdf|mirrored_html", na=False)] if not df.empty else df
    pdf_count = int(df["access_state"].eq("mirrored_pdf").sum()) if not df.empty else 0
    html_count = int(df["access_state"].eq("mirrored_html").sum()) if not df.empty else 0
    blocked_count = int(df["access_state"].astype(str).str.contains("blocked|error|not_found", na=False).sum()) if not df.empty else 0
    by_candidate = df.groupby("candidate_id")["access_state"].apply(lambda s: ", ".join(sorted(set(map(str, s))))).to_dict() if not df.empty else {}
    lines = [
        "# Individual Replication Blocker Auto-Acquisition",
        "",
        f"- Manual task input: `{args.manual_task.relative_to(ROOT)}`",
        f"- Attempt ledger: `{OUT_ATTEMPTS.relative_to(ROOT)}`",
        f"- Mirrored raw directory: `{RAW_DIR.relative_to(ROOT)}`",
        f"- Attempts: {len(rows):,}",
        f"- Mirrored PDFs: {pdf_count:,}",
        f"- Mirrored non-resolver HTML pages: {html_count:,}",
        f"- Blocked/error/not-found attempts: {blocked_count:,}",
        "",
        "## Candidate States",
        "",
    ]
    for candidate_id, states in sorted(by_candidate.items()):
        lines.append(f"- `{candidate_id}`: {states}")
    if not by_candidate:
        lines.append("- None.")
    OUT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    OUT_REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {OUT_ATTEMPTS.relative_to(ROOT)}")
    print(f"Wrote {OUT_REPORT.relative_to(ROOT)}")
    print(f"Mirrored PDFs: {pdf_count}; mirrored HTML: {html_count}; attempts: {len(rows)}")


if __name__ == "__main__":
    main()
