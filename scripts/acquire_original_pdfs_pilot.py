#!/usr/bin/env python3
"""Try lawful PDF acquisition routes for original represented sources.

This pass is narrower than the general level-5 probe: it looks for actual PDF
bytes for rows that are still below level 5. It writes a route-level ledger and
stores any valid PDF bytes under a separate cache. It does not promote rows.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import time
import urllib.parse
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from xml.etree import ElementTree

import pandas as pd
import requests


ROOT = Path(__file__).resolve().parents[1]
PILOT = ROOT / "data" / "derived" / "effect_inflation_dataset" / "schema_pilot"
SAMPLE_N = int(os.environ.get("SCHEMA_PILOT_N", "300"))
SAMPLE_SUFFIX = f"sample_{SAMPLE_N}"

SOURCE_RESULT_IN = PILOT / f"source_result_codebook_{SAMPLE_SUFFIX}.tsv"
SOURCE_IDENTIFIER_IN = PILOT / f"source_identifier_codebook_{SAMPLE_SUFFIX}.tsv"
SOURCE_IN = PILOT / f"source_codebook_{SAMPLE_SUFFIX}.tsv"

CACHE_DIR = ROOT / "data" / "cache" / "original_pdf_acquisition" / SAMPLE_SUFFIX
OUT_TSV = PILOT / f"original_pdf_acquisition_attempts_{SAMPLE_SUFFIX}.tsv"
OUT_SUMMARY = PILOT / f"original_pdf_acquisition_summary_{SAMPLE_SUFFIX}.tsv"
OUT_REPORT = ROOT / "reports" / f"original_pdf_acquisition_{SAMPLE_SUFFIX}_2026-04-30.md"

CONTACT_EMAIL = os.environ.get("PROVENANCE_CONTACT_EMAIL", "").strip()
UNPAYWALL_EMAIL = os.environ.get("UNPAYWALL_EMAIL", CONTACT_EMAIL).strip()
SEMANTIC_SCHOLAR_API_KEY = os.environ.get("SEMANTIC_SCHOLAR_API_KEY", "").strip()
OPENALEX_API_KEY = os.environ.get("OPENALEX_API_KEY", "").strip()

MAX_ROWS = int(os.environ.get("ORIGINAL_PDF_MAX_ROWS", "80"))
TIMEOUT = int(os.environ.get("ORIGINAL_PDF_TIMEOUT", "15"))
MAX_BYTES = int(os.environ.get("ORIGINAL_PDF_MAX_BYTES", str(80_000_000)))
REQUEST_DELAY_SECONDS = float(os.environ.get("ORIGINAL_PDF_REQUEST_DELAY_SECONDS", "0.2"))
STOP_AFTER_SUCCESS = os.environ.get("ORIGINAL_PDF_STOP_AFTER_SUCCESS", "true").lower() in {"1", "true", "yes"}
ENABLE_FATCAT = os.environ.get("ORIGINAL_PDF_ENABLE_FATCAT", "false").lower() in {"1", "true", "yes"}
INCLUDE_NONPRIMARY_IDENTIFIERS = (
    os.environ.get("ORIGINAL_PDF_INCLUDE_NONPRIMARY_IDENTIFIERS", "false").lower() in {"1", "true", "yes"}
)

USER_AGENT = (
    "PublishedSmallNStudiesDontMatter PDF acquisition "
    f"(mailto:{CONTACT_EMAIL or 'research@example.invalid'}; noncommercial source verification)"
)

DOI_RE = re.compile(r"10\.\d{4,9}/[-._;()/:A-Z0-9]+", re.I)
PMID_RE = re.compile(r"\b\d{6,9}\b")
PMCID_RE = re.compile(r"PMC\d+", re.I)
PDF_URL_RE = re.compile(r"\.pdf(?:[?#].*)?$", re.I)


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


def stable_hash(*parts: object, length: int = 12) -> str:
    text = "\n".join(safe_text(part) for part in parts)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:length]


def sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def redacted_url(url: str) -> str:
    parsed = urllib.parse.urlsplit(url)
    query = urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
    redacted_query = []
    for key, value in query:
        if key.lower() in {"email", "mailto", "api_key", "x-api-key"}:
            redacted_query.append((key, "<redacted>"))
        else:
            redacted_query.append((key, value))
    return urllib.parse.urlunsplit(
        (parsed.scheme, parsed.netloc, parsed.path, urllib.parse.urlencode(redacted_query), parsed.fragment)
    )


def doi_variants(raw: str) -> list[str]:
    if not raw:
        return []
    text = urllib.parse.unquote(raw.strip())
    text = re.sub(r"^https?://(?:dx\.)?doi\.org/", "", text, flags=re.I)
    text = text.strip().rstrip(".,;")
    if not text:
        return []
    match = DOI_RE.search(text)
    if not match:
        return []
    doi = match.group(0).rstrip(".,;")
    # Crossref sometimes stores accidental double slash after publisher prefix.
    cleaned = re.sub(r"(10\.\d{4,9})//+", r"\1/", doi, flags=re.I)
    variants = [doi]
    if cleaned != doi:
        variants.append(cleaned)
    return list(dict.fromkeys(variants))


def split_urls(value: str) -> list[str]:
    urls = []
    for item in re.split(r"\s*\|\s*", value or ""):
        item = item.strip()
        if item.startswith("http://") or item.startswith("https://"):
            urls.append(item)
    return list(dict.fromkeys(urls))


def collect_identifiers(source_results: pd.DataFrame, identifiers: pd.DataFrame, sources: pd.DataFrame) -> pd.DataFrame:
    id_by_source: dict[str, dict[str, list[str]]] = defaultdict(lambda: defaultdict(list))
    for _, row in identifiers.iterrows():
        if not INCLUDE_NONPRIMARY_IDENTIFIERS and safe_text(row.get("is_primary")).lower() != "true":
            continue
        source_id = safe_text(row.get("source_id"))
        typ = safe_text(row.get("identifier_type")).lower()
        value = safe_text(row.get("identifier_value"))
        url = safe_text(row.get("identifier_url"))
        if value:
            id_by_source[source_id][typ].append(value)
        if url:
            id_by_source[source_id]["url"].append(url)

    source_lookup = {safe_text(row["source_id"]): row for _, row in sources.iterrows()}
    rows: list[dict[str, object]] = []
    for _, row in source_results.iterrows():
        represented = safe_text(row.get("represented_source_id"))
        source_row = source_lookup.get(represented)
        ids = id_by_source[represented]
        doi_values: list[str] = []
        for value in ids.get("doi", []):
            doi_values.extend(doi_variants(value))
        if source_row is not None:
            doi_values.extend(doi_variants(safe_text(source_row.get("doi"))))
            if safe_text(source_row.get("pmid")):
                ids["pmid"].append(safe_text(source_row.get("pmid")))
            if safe_text(source_row.get("url")):
                ids["url"].append(safe_text(source_row.get("url")))
        for url in ids.get("url", []):
            doi_values.extend(doi_variants(url))

        pmids = []
        for value in ids.get("pmid", []):
            pmids.extend(PMID_RE.findall(value))
        pmcids = []
        for value in ids.get("pmcid", []):
            pmcids.extend(PMCID_RE.findall(value.upper()))
        for url in ids.get("url", []):
            pmids.extend(PMID_RE.findall(url) if "pubmed.ncbi.nlm.nih.gov" in url else [])
            pmcids.extend(PMCID_RE.findall(url.upper()))

        rows.append(
            {
                "source_result_id": safe_text(row.get("source_result_id")),
                "represented_source_id": represented,
                "evidence_level": safe_text(row.get("evidence_level")),
                "evidence_level_name": safe_text(row.get("evidence_level_name")),
                "source_citation_key": safe_text(row.get("source_citation_key")),
                "result_label": safe_text(row.get("result_label")),
                "represented_title": safe_text(source_row.get("title")) if source_row is not None else "",
                "doi_values": "|".join(list(dict.fromkeys(doi_values))),
                "pmid_values": "|".join(list(dict.fromkeys(pmids))),
                "pmcid_values": "|".join(list(dict.fromkeys(pmcids))),
                "candidate_urls": "|".join(list(dict.fromkeys(ids.get("url", [])))),
            }
        )
    return pd.DataFrame(rows)


def headers(accept: str = "application/pdf,*/*;q=0.8") -> dict[str, str]:
    out = {"User-Agent": USER_AGENT, "Accept": accept}
    return out


def get_bytes(url: str, accept: str = "application/pdf,*/*;q=0.8") -> dict[str, object]:
    request_headers = headers(accept)
    if "api.semanticscholar.org" in url and SEMANTIC_SCHOLAR_API_KEY:
        request_headers["x-api-key"] = SEMANTIC_SCHOLAR_API_KEY
    try:
        with requests.get(url, headers=request_headers, timeout=TIMEOUT, allow_redirects=True, stream=True) as response:
            chunks: list[bytes] = []
            total = 0
            for chunk in response.iter_content(chunk_size=128 * 1024):
                if not chunk:
                    continue
                chunks.append(chunk)
                total += len(chunk)
                if total > MAX_BYTES:
                    break
            content = b"".join(chunks)
            return {
                "ok": 200 <= response.status_code < 300,
                "status_code": response.status_code,
                "final_url": response.url,
                "content_type": response.headers.get("content-type", ""),
                "byte_count": len(content),
                "truncated": total > MAX_BYTES,
                "content": content,
                "error": "",
            }
    except Exception as exc:  # noqa: BLE001 - acquisition ledger should record all failures.
        return {
            "ok": False,
            "status_code": "",
            "final_url": "",
            "content_type": "",
            "byte_count": 0,
            "truncated": False,
            "content": b"",
            "error": f"{type(exc).__name__}:{exc}",
        }


def is_pdf(content: bytes, content_type: str, final_url: str) -> bool:
    if content.startswith(b"%PDF"):
        return True
    # Some servers prepend a tiny BOM/newline before the PDF marker.
    if content[:64].lstrip().startswith(b"%PDF"):
        return True
    lower_type = content_type.lower()
    return "application/pdf" in lower_type and len(content) > 1000 and not content.lstrip().startswith(b"<")


def classify_failure(response: dict[str, object], pdf_valid: bool) -> str:
    if pdf_valid:
        return "pdf_obtained"
    if response["error"]:
        return "request_error"
    status = str(response["status_code"])
    content = response.get("content", b"")
    if isinstance(content, bytes):
        text = content[:200_000].decode("utf-8", errors="ignore").lower()
    else:
        text = ""
    if status in {"401", "402", "403"}:
        return f"http_{status}_blocked"
    if status == "404":
        return "http_404"
    if status == "429":
        return "http_429_rate_limited"
    if "captcha" in text or "verify you are human" in text or "cloudflare" in text:
        return "captcha_or_bot_block"
    if "login" in text or "subscribe" in text or "institution" in text:
        return "login_or_paywall_html"
    if text.lstrip().startswith("<") or "html" in safe_text(response.get("content_type")).lower():
        return "html_not_pdf"
    if not response["ok"]:
        return "http_not_ok"
    return "non_pdf_bytes"


def write_pdf(source_result_id: str, route: str, doi: str, content: bytes) -> tuple[str, str]:
    sha = sha256_bytes(content)
    safe_route = re.sub(r"[^A-Za-z0-9._-]+", "_", route).strip("_").lower()
    path = CACHE_DIR / f"{source_result_id}__{safe_route}__{stable_hash(doi, sha)}.pdf"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    return rel(path), sha


def attempt_pdf(row: pd.Series, route: str, candidate_url: str, doi: str, note: str = "") -> dict[str, object]:
    time.sleep(REQUEST_DELAY_SECONDS)
    response = get_bytes(candidate_url)
    content = response.get("content", b"")
    assert isinstance(content, bytes)
    pdf_valid = is_pdf(content, safe_text(response.get("content_type")), safe_text(response.get("final_url")))
    local_path = ""
    sha = ""
    if pdf_valid:
        local_path, sha = write_pdf(row["source_result_id"], route, doi, content)
    return {
        "source_result_id": row["source_result_id"],
        "represented_source_id": row["represented_source_id"],
        "previous_evidence_level": row["evidence_level"],
        "previous_evidence_level_name": row["evidence_level_name"],
        "source_citation_key": row["source_citation_key"],
        "represented_title": row["represented_title"],
        "doi": doi,
        "route": route,
        "attempt_kind": "pdf_candidate",
        "candidate_url": redacted_url(candidate_url),
        "http_status": safe_text(response.get("status_code")),
        "final_url": redacted_url(safe_text(response.get("final_url"))),
        "content_type": safe_text(response.get("content_type")),
        "byte_count": safe_text(response.get("byte_count")),
        "pdf_valid": str(pdf_valid).lower(),
        "local_path": local_path,
        "sha256": sha,
        "failure_reason": classify_failure(response, pdf_valid),
        "route_note": note,
    }


def metadata_attempt(row: pd.Series, route: str, doi: str, url: str, status: str, note: str = "") -> dict[str, object]:
    return {
        "source_result_id": row["source_result_id"],
        "represented_source_id": row["represented_source_id"],
        "previous_evidence_level": row["evidence_level"],
        "previous_evidence_level_name": row["evidence_level_name"],
        "source_citation_key": row["source_citation_key"],
        "represented_title": row["represented_title"],
        "doi": doi,
        "route": route,
        "attempt_kind": "metadata",
        "candidate_url": redacted_url(url),
        "http_status": "",
        "final_url": "",
        "content_type": "",
        "byte_count": "",
        "pdf_valid": "false",
        "local_path": "",
        "sha256": "",
        "failure_reason": status,
        "route_note": note,
    }


def fetch_json(url: str, accept: str = "application/json") -> tuple[dict | None, str, str]:
    time.sleep(REQUEST_DELAY_SECONDS)
    response = get_bytes(url, accept=accept)
    content = response.get("content", b"")
    if not response.get("ok"):
        return None, f"http_{safe_text(response.get('status_code')) or 'request_error'}", safe_text(response.get("error"))
    try:
        assert isinstance(content, bytes)
        return json.loads(content.decode("utf-8", errors="replace")), "ok", ""
    except Exception as exc:  # noqa: BLE001
        return None, "json_parse_failed", f"{type(exc).__name__}:{exc}"


def crossref_pdf_candidates(doi: str) -> tuple[list[str], str]:
    safe = urllib.parse.quote(doi, safe="/:._;()-")
    url = f"https://api.crossref.org/works/{safe}"
    if CONTACT_EMAIL:
        url += f"?mailto={urllib.parse.quote(CONTACT_EMAIL)}"
    data, status, note = fetch_json(url)
    if not data:
        return [], f"{status}:{note}"
    urls = []
    for link in (data.get("message") or {}).get("link", []) or []:
        candidate = safe_text(link.get("URL"))
        content_type = safe_text(link.get("content-type")).lower()
        app = safe_text(link.get("intended-application")).lower()
        if candidate and ("pdf" in content_type or PDF_URL_RE.search(candidate) or app == "text-mining"):
            urls.append(candidate)
    return list(dict.fromkeys(urls)), "ok"


def unpaywall_pdf_candidates(doi: str) -> tuple[list[str], str]:
    if not UNPAYWALL_EMAIL or "example.invalid" in UNPAYWALL_EMAIL:
        return [], "skipped_no_unpaywall_email"
    safe = urllib.parse.quote(doi, safe="/:._;()-")
    url = f"https://api.unpaywall.org/v2/{safe}?email={urllib.parse.quote(UNPAYWALL_EMAIL)}"
    data, status, note = fetch_json(url)
    if not data:
        return [], f"{status}:{note}"
    locations = []
    if data.get("best_oa_location"):
        locations.append(data["best_oa_location"])
    locations.extend(data.get("oa_locations") or [])
    urls = []
    for loc in locations:
        for key in ["url_for_pdf", "url"]:
            candidate = safe_text(loc.get(key))
            if candidate and (key == "url_for_pdf" or PDF_URL_RE.search(candidate)):
                urls.append(candidate)
    return list(dict.fromkeys(urls)), "ok"


def openalex_pdf_candidates(doi: str) -> tuple[list[str], str]:
    safe = urllib.parse.quote(doi, safe="/:._;()-")
    url = f"https://api.openalex.org/works/doi:{safe}"
    params = []
    if CONTACT_EMAIL:
        params.append(("mailto", CONTACT_EMAIL))
    if OPENALEX_API_KEY:
        params.append(("api_key", OPENALEX_API_KEY))
    if params:
        url += "?" + urllib.parse.urlencode(params)
    data, status, note = fetch_json(url)
    if not data:
        return [], f"{status}:{note}"
    urls = []
    containers = [data.get("primary_location") or {}, data.get("best_oa_location") or {}]
    containers.extend(data.get("locations") or [])
    for loc in containers:
        for key in ["pdf_url", "landing_page_url"]:
            candidate = safe_text(loc.get(key))
            if candidate and (key == "pdf_url" or PDF_URL_RE.search(candidate)):
                urls.append(candidate)
    return list(dict.fromkeys(urls)), "ok"


def semantic_scholar_pdf_candidates(doi: str) -> tuple[list[str], str]:
    safe = urllib.parse.quote(doi, safe="/:._;()-")
    url = f"https://api.semanticscholar.org/graph/v1/paper/DOI:{safe}?fields=externalIds,url,openAccessPdf,title,year"
    data, status, note = fetch_json(url)
    if not data:
        return [], f"{status}:{note}"
    urls = []
    oa_pdf = data.get("openAccessPdf") or {}
    if oa_pdf.get("url"):
        urls.append(safe_text(oa_pdf.get("url")))
    return list(dict.fromkeys(urls)), "ok"


def europepmc_pdf_candidates(doi: str) -> tuple[list[str], str, list[str]]:
    safe_query = urllib.parse.quote(f'DOI:"{doi}"')
    url = f"https://www.ebi.ac.uk/europepmc/webservices/rest/search?query={safe_query}&format=json&resultType=core"
    data, status, note = fetch_json(url)
    if not data:
        return [], f"{status}:{note}", []
    urls = []
    pmcids = []
    for result in ((data.get("resultList") or {}).get("result") or []):
        pmcid = safe_text(result.get("pmcid")).upper()
        if pmcid:
            pmcids.append(pmcid)
            urls.append(f"https://europepmc.org/articles/{pmcid}?pdf=render")
        for item in ((result.get("fullTextUrlList") or {}).get("fullTextUrl") or []):
            candidate = safe_text(item.get("url"))
            if candidate and PDF_URL_RE.search(candidate):
                urls.append(candidate)
    return list(dict.fromkeys(urls)), "ok", list(dict.fromkeys(pmcids))


def fatcat_pdf_candidates(doi: str) -> tuple[list[str], str]:
    safe = urllib.parse.quote(doi, safe="")
    url = f"https://api.fatcat.wiki/v0/release/lookup?doi={safe}&expand=files,webcaptures"
    data, status, note = fetch_json(url)
    if not data:
        return [], f"{status}:{note}"
    urls = []
    for file_row in data.get("files") or []:
        for item in file_row.get("urls") or []:
            candidate = safe_text(item.get("url"))
            if candidate and PDF_URL_RE.search(candidate):
                urls.append(candidate)
        for item in file_row.get("webcaptures") or []:
            candidate = safe_text(item.get("archive_url") or item.get("url"))
            if candidate and (PDF_URL_RE.search(candidate) or "/web/" in candidate):
                urls.append(candidate)
    for item in data.get("webcaptures") or []:
        candidate = safe_text(item.get("archive_url") or item.get("url"))
        if candidate and (PDF_URL_RE.search(candidate) or "/web/" in candidate):
            urls.append(candidate)
    return list(dict.fromkeys(urls)), "ok"


def pmc_oa_pdf_candidates(pmcid: str) -> tuple[list[str], str]:
    if not pmcid:
        return [], "no_pmcid"
    url = f"https://pmc.ncbi.nlm.nih.gov/utils/oa/oa.fcgi?id={pmcid}"
    time.sleep(REQUEST_DELAY_SECONDS)
    response = get_bytes(url, accept="application/xml,text/xml,*/*;q=0.8")
    if not response.get("ok"):
        return [], f"http_{safe_text(response.get('status_code')) or 'request_error'}"
    content = response.get("content", b"")
    assert isinstance(content, bytes)
    urls = []
    try:
        root = ElementTree.fromstring(content)
        for link in root.findall(".//link"):
            href = safe_text(link.attrib.get("href"))
            fmt = safe_text(link.attrib.get("format")).lower()
            if href and ("pdf" in fmt or PDF_URL_RE.search(href)):
                urls.append(href)
    except ElementTree.ParseError:
        text = content.decode("utf-8", errors="replace")
        urls.extend(re.findall(r'https?://[^"\'<>\s]+\.pdf(?:\?[^"\'<>\s]+)?', text, flags=re.I))
    urls.append(f"https://europepmc.org/articles/{pmcid}?pdf=render")
    urls.append(f"https://pmc.ncbi.nlm.nih.gov/articles/{pmcid}/pdf/")
    return list(dict.fromkeys(urls)), "ok"


def pubmed_bridge(row: pd.Series) -> tuple[list[str], list[str], list[dict[str, object]]]:
    doi_values = []
    pmcid_values = []
    ledger = []
    for pmid in [item for item in safe_text(row.get("pmid_values")).split("|") if item]:
        url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&id={pmid}&retmode=json"
        data, status, note = fetch_json(url)
        ledger.append(metadata_attempt(row, "pubmed_esummary", "", url, status, note))
        if not data:
            continue
        item = (data.get("result") or {}).get(pmid) or {}
        for article_id in item.get("articleids") or []:
            idtype = safe_text(article_id.get("idtype")).lower()
            value = safe_text(article_id.get("value"))
            if idtype == "doi":
                doi_values.extend(doi_variants(value))
            if idtype == "pmc":
                pmcid_values.extend(PMCID_RE.findall(value.upper()))
    return list(dict.fromkeys(doi_values)), list(dict.fromkeys(pmcid_values)), ledger


ROUTES = [
    ("crossref_tdm_pdf", crossref_pdf_candidates),
    ("unpaywall_pdf", unpaywall_pdf_candidates),
    ("openalex_pdf", openalex_pdf_candidates),
    ("semantic_scholar_openaccess_pdf", semantic_scholar_pdf_candidates),
    ("europepmc_pdf", europepmc_pdf_candidates),
]
if ENABLE_FATCAT:
    ROUTES.append(("fatcat_archive_pdf", fatcat_pdf_candidates))


def acquire_for_row(row: pd.Series) -> list[dict[str, object]]:
    ledger: list[dict[str, object]] = []
    pdf_found = False
    doi_values = [item for item in safe_text(row.get("doi_values")).split("|") if item]
    pmcid_values = [item for item in safe_text(row.get("pmcid_values")).split("|") if item]

    bridged_dois, bridged_pmcids, bridge_ledger = pubmed_bridge(row)
    ledger.extend(bridge_ledger)
    doi_values = list(dict.fromkeys(doi_values + bridged_dois))
    pmcid_values = list(dict.fromkeys(pmcid_values + bridged_pmcids))

    for pmcid in pmcid_values:
        candidates, status = pmc_oa_pdf_candidates(pmcid)
        ledger.append(metadata_attempt(row, "pmc_oa_pdf_manifest", "", f"pmcid:{pmcid}", status, f"{len(candidates)} pdf candidates"))
        for candidate in candidates:
            rec = attempt_pdf(row, "pmc_oa_pdf", candidate, "", note=f"pmcid={pmcid}")
            ledger.append(rec)
            if rec["pdf_valid"] == "true":
                pdf_found = True
                break
        if pdf_found and STOP_AFTER_SUCCESS:
            return ledger

    if not doi_values and not pmcid_values:
        ledger.append(metadata_attempt(row, "target_identifier_check", "", "", "no_doi_pmid_or_pmcid", "No PDF acquisition identifier available."))
        return ledger

    for doi in doi_values:
        for route_name, candidate_fn in ROUTES:
            if pdf_found and STOP_AFTER_SUCCESS:
                return ledger
            if route_name == "europepmc_pdf":
                candidates, status, new_pmcids = candidate_fn(doi)  # type: ignore[misc]
                pmcid_values = list(dict.fromkeys(pmcid_values + new_pmcids))
            else:
                candidates, status = candidate_fn(doi)  # type: ignore[misc]
            ledger.append(metadata_attempt(row, f"{route_name}_metadata", doi, f"doi:{doi}", status, f"{len(candidates)} pdf candidates"))
            for candidate in candidates[:4]:
                rec = attempt_pdf(row, route_name, candidate, doi)
                ledger.append(rec)
                if rec["pdf_valid"] == "true":
                    pdf_found = True
                    break

        if not pdf_found:
            doi_url = f"https://doi.org/{urllib.parse.quote(doi, safe='/:._;()-')}"
            rec = attempt_pdf(row, "doi_accept_pdf", doi_url, doi, note="DOI resolver requested with Accept: application/pdf")
            ledger.append(rec)
            if rec["pdf_valid"] == "true":
                pdf_found = True

    return ledger


def main() -> None:
    source_results = pd.read_csv(SOURCE_RESULT_IN, sep="\t", dtype=str, keep_default_na=False)
    identifiers = pd.read_csv(SOURCE_IDENTIFIER_IN, sep="\t", dtype=str, keep_default_na=False)
    sources = pd.read_csv(SOURCE_IN, sep="\t", dtype=str, keep_default_na=False)

    targets = collect_identifiers(source_results, identifiers, sources)
    targets = targets[pd.to_numeric(targets["evidence_level"], errors="coerce").fillna(0).lt(5)].copy()
    targets["has_pdf_identifier"] = targets.apply(
        lambda row: bool(row["doi_values"] or row["pmid_values"] or row["pmcid_values"]),
        axis=1,
    )
    targets["sort_key"] = targets.apply(
        lambda row: (
            0 if row["evidence_level"] == "4" else 1,
            0 if row["doi_values"] else 1,
            row["source_result_id"],
        ),
        axis=1,
    )
    all_pdf_identifier_targets = targets[targets["has_pdf_identifier"]].sort_values("sort_key").copy()
    targets = all_pdf_identifier_targets.head(MAX_ROWS)

    rows: list[dict[str, object]] = []
    for index, (_, target) in enumerate(targets.iterrows(), start=1):
        row_records = acquire_for_row(target)
        rows.extend(row_records)
        row_pdf_count = sum(1 for item in row_records if item.get("pdf_valid") == "true")
        print(
            f"[{index}/{len(targets)}] {target['source_result_id']} "
            f"attempt_rows={len(row_records)} pdfs={row_pdf_count}",
            flush=True,
        )

    attempts = pd.DataFrame(rows)
    OUT_TSV.parent.mkdir(parents=True, exist_ok=True)
    attempts.to_csv(OUT_TSV, sep="\t", index=False)

    pdf_rows = attempts[attempts.get("pdf_valid", pd.Series(dtype=str)).astype(str).eq("true")].copy()
    row_success = pdf_rows.groupby("source_result_id").head(1) if not pdf_rows.empty else pd.DataFrame()
    summary_rows: list[dict[str, object]] = [
        {"metric": "sample_n", "value": SAMPLE_N},
        {"metric": "below_level5_rows", "value": int(pd.to_numeric(collect_identifiers(source_results, identifiers, sources)["evidence_level"], errors="coerce").fillna(0).lt(5).sum())},
        {"metric": "below_level5_rows_with_pdf_identifier", "value": int(all_pdf_identifier_targets["source_result_id"].nunique())},
        {"metric": "rows_attempted", "value": int(targets["source_result_id"].nunique())},
        {"metric": "attempt_rows", "value": int(len(attempts))},
        {"metric": "pdf_attempt_rows_valid", "value": int(len(pdf_rows))},
        {"metric": "rows_with_pdf_obtained", "value": int(pdf_rows["source_result_id"].nunique()) if not pdf_rows.empty else 0},
        {"metric": "unpaywall_enabled", "value": str(bool(UNPAYWALL_EMAIL and 'example.invalid' not in UNPAYWALL_EMAIL)).lower()},
        {"metric": "fatcat_enabled", "value": str(ENABLE_FATCAT).lower()},
        {"metric": "include_nonprimary_identifiers", "value": str(INCLUDE_NONPRIMARY_IDENTIFIERS).lower()},
        {"metric": "stop_after_success", "value": str(STOP_AFTER_SUCCESS).lower()},
        {"metric": "created_at_utc", "value": datetime.now(timezone.utc).isoformat()},
    ]
    if not attempts.empty:
        for key, value in attempts["route"].value_counts().sort_index().items():
            summary_rows.append({"metric": f"route_attempt_rows::{key}", "value": int(value)})
        for key, value in attempts.loc[attempts["pdf_valid"].eq("true"), "route"].value_counts().sort_index().items():
            summary_rows.append({"metric": f"route_pdf_success::{key}", "value": int(value)})
        for key, value in attempts["failure_reason"].value_counts().head(25).items():
            summary_rows.append({"metric": f"failure_reason::{key}", "value": int(value)})
    summary = pd.DataFrame(summary_rows)
    summary.to_csv(OUT_SUMMARY, sep="\t", index=False)

    lines = [
        "# Original PDF Acquisition Pilot",
        "",
        f"- Sample rows: {SAMPLE_N}",
        f"- Rows below level 5 with DOI/PMID/PMCID route attempted: {targets['source_result_id'].nunique()}",
        f"- Valid PDFs obtained: {int(pdf_rows['source_result_id'].nunique()) if not pdf_rows.empty else 0}",
        f"- Unpaywall route enabled: {str(bool(UNPAYWALL_EMAIL and 'example.invalid' not in UNPAYWALL_EMAIL)).lower()}",
        "",
        "## Route Successes",
        "",
    ]
    if row_success.empty:
        lines.append("- No valid PDFs obtained in this pass.")
    else:
        for _, row in row_success.iterrows():
            lines.append(
                f"- `{row['source_result_id']}` via `{row['route']}`; `{row['local_path']}`"
            )
    lines.extend(["", "## Failure Profile", ""])
    if not attempts.empty:
        for failure, count in attempts["failure_reason"].value_counts().head(12).items():
            lines.append(f"- `{failure}`: {int(count)}")
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- A valid PDF here is an acquisition candidate, not level-6 evidence. It still needs identity checking, access/share-scope tagging, source-file manifest promotion, parsing, exact locator support, and D/N verification.",
            "- By default this pass uses primary identifiers only. Non-primary grounding URLs can be enabled for exploratory chasing with `ORIGINAL_PDF_INCLUDE_NONPRIMARY_IDENTIFIERS=true`, but they must pass the PDF identity check before promotion.",
            "- Metadata rows are included so route failures remain visible rather than disappearing behind the first successful or blocked URL.",
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
