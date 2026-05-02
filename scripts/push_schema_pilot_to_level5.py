#!/usr/bin/env python3
"""Try to obtain original/source objects for level-4 provenance pilot rows.

This is deliberately a probing script, not a promotion script. It mirrors
reachable source objects and writes an audit TSV that can be reviewed before
any evidence levels are upgraded.
"""

from __future__ import annotations

import hashlib
import html
import json
import os
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import quote, urlparse

import pandas as pd
import requests


SAMPLE_N = int(os.environ.get("SCHEMA_PILOT_N", "300"))
ROOT = Path("data/derived/effect_inflation_dataset/schema_pilot")
GROUNDING = ROOT / f"real_world_grounding_sample_{SAMPLE_N}.tsv"
OUT_DIR = Path("data/cache/provenance_level5") / f"sample_{SAMPLE_N}"
OUT_TSV = ROOT / f"level5_fetch_attempts_sample_{SAMPLE_N}.tsv"
OUT_SUMMARY = ROOT / f"level5_fetch_summary_sample_{SAMPLE_N}.tsv"
OUT_ROW_STATUS = ROOT / f"level5_row_status_sample_{SAMPLE_N}.tsv"
OUT_TODOS = ROOT / f"level5_remaining_todos_sample_{SAMPLE_N}.tsv"
OUT_REPORT = Path("reports") / f"level5_push_sample_{SAMPLE_N}_2026-04-29.md"

USER_AGENT = (
    "PublishedSmallNStudiesDontMatter provenance audit "
    f"(mailto:{os.environ.get('PROVENANCE_CONTACT_EMAIL', 'research@example.invalid')}; noncommercial source verification)"
)
TIMEOUT = 20
MAX_BYTES = 25_000_000
SLEEP_SECONDS = 0.15
LEVEL5_WORKERS = int(os.environ.get("LEVEL5_WORKERS", "8"))
CONTACT_EMAIL = os.environ.get("PROVENANCE_CONTACT_EMAIL", "").strip()
OPENALEX_API_KEY = os.environ.get("OPENALEX_API_KEY", "").strip()
SEMANTIC_SCHOLAR_API_KEY = os.environ.get("SEMANTIC_SCHOLAR_API_KEY", "").strip()
UNPAYWALL_EMAIL = os.environ.get("UNPAYWALL_EMAIL", CONTACT_EMAIL).strip()
CORE_API_KEY = os.environ.get("CORE_API_KEY", "").strip()


DOI_RE = re.compile(r"10\.\d{4,9}/[-._;()/:A-Z0-9]+", re.I)
PMCID_RE = re.compile(r"PMC\d+", re.I)
NCT_RE = re.compile(r"NCT\d{8}", re.I)
NUMBER_RE = re.compile(r"\d")
EFFECT_TERM_RE = re.compile(
    r"\b(effect|cohen'?s?\s*d|hedges|standardi[sz]ed mean difference|smd|odds ratio|"
    r"hazard ratio|risk ratio|relative risk|mean difference|regression|coefficient|"
    r"estimate|beta|p\s*[<=>]|confidence interval|ci)\b",
    re.I,
)
N_TERM_RE = re.compile(
    r"\b(n\s*[=:]\s*\d|sample size|participants?|patients?|subjects?|respondents?|"
    r"enrolled|randomi[sz]ed|observations?)\b",
    re.I,
)

PREPRINT_OR_REPOSITORY_HOST_RE = re.compile(
    r"(arxiv\.org|biorxiv\.org|medrxiv\.org|psyarxiv\.com|socarxiv\.org|"
    r"osf\.io|preprints\.|ssrn\.com|papers\.ssrn\.com|researchsquare\.com|"
    r"zenodo\.org|figshare\.com|dataverse\.|openicpsr\.org|eprints\.|"
    r"repository\.|dash\.harvard\.edu|escholarship\.org|hdl\.handle\.net)",
    re.I,
)

STRATEGY_GROUPS = [
    "registry_clinicaltrials",
    "pubmed_bridge",
    "pmc_fulltext",
    "crossref_metadata",
    "datacite_metadata",
    "unpaywall_metadata",
    "openalex_metadata",
    "semantic_scholar_metadata",
    "europepmc_metadata",
    "oa_candidate_url",
    "preprint_repository_candidate",
    "direct_journal_or_doi_landing",
    "stable_url",
]

HOST_MIN_DELAY_SECONDS = {
    "clinicaltrials.gov": 0.35,
    "eutils.ncbi.nlm.nih.gov": 0.35,
    "www.ncbi.nlm.nih.gov": 0.5,
    "pmc.ncbi.nlm.nih.gov": 0.5,
    "api.crossref.org": 0.35,
    "api.datacite.org": 0.35,
    "api.openalex.org": 0.5,
    "api.unpaywall.org": 0.5,
    "api.semanticscholar.org": 1.0,
    "www.ebi.ac.uk": 0.5,
    "api.core.ac.uk": 1.0,
}
DEFAULT_HOST_DELAY_SECONDS = float(os.environ.get("LEVEL5_DEFAULT_HOST_DELAY", "1.5"))
_host_locks: dict[str, threading.Lock] = {}
_host_last_request: dict[str, float] = {}
_host_locks_guard = threading.Lock()


def sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def slug(text: str, max_len: int = 90) -> str:
    text = re.sub(r"^https?://", "", text.strip())
    text = re.sub(r"[^A-Za-z0-9._-]+", "_", text).strip("_")
    return (text[:max_len] or "source").lower()


def detect_kind(row: pd.Series) -> str:
    basis = row.get("primary_real_world_url_basis", "")
    url = row.get("primary_real_world_url", "")
    if row.get("nct_list", "") or basis == "nct" or NCT_RE.search(url):
        return "nct_registry"
    if row.get("pmcid_list", "") or "pmc.ncbi.nlm.nih.gov/articles/PMC" in url:
        return "pmc_fulltext"
    if row.get("pmid_list", "") or basis == "pmid" or "pubmed.ncbi.nlm.nih.gov" in url:
        return "pmid_record"
    if url.startswith("https://doi.org/"):
        return "doi_article"
    if url:
        return "other_url"
    return "missing_url"


def split_first(cell: str, regex: re.Pattern[str] | None = None) -> str:
    if not cell:
        return ""
    if regex:
        match = regex.search(cell)
        if match:
            return match.group(0)
    return re.split(r"\s*\|\s*", cell.strip())[0]


def extension_from_type(content_type: str, url: str) -> str:
    lower = content_type.lower()
    path = urlparse(url).path.lower()
    if "pdf" in lower or path.endswith(".pdf"):
        return ".pdf"
    if "json" in lower:
        return ".json"
    if "xml" in lower:
        return ".xml"
    if "html" in lower or "text/" in lower:
        return ".html"
    return ".bin"


def content_sniff(content: bytes, content_type: str, url: str) -> str:
    lower_type = content_type.lower()
    path = urlparse(url).path.lower()
    head = content[:1024].lstrip()
    if head.startswith(b"%PDF") or "pdf" in lower_type or path.endswith(".pdf"):
        return "pdf"
    if head.startswith(b"{") or "json" in lower_type:
        return "json"
    if head.startswith(b"<?xml") or "xml" in lower_type:
        return "xml"
    if b"<html" in head.lower() or "html" in lower_type:
        return "html"
    return "binary"


def clean_text(text: str, max_len: int = 1400) -> str:
    text = html.unescape(text)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) > max_len:
        return text[: max_len - 3].rstrip() + "..."
    return text


def reconstruct_openalex_abstract(data: dict) -> str:
    inverted = data.get("abstract_inverted_index") or {}
    if not isinstance(inverted, dict) or not inverted:
        return ""
    positioned: list[tuple[int, str]] = []
    for word, positions in inverted.items():
        if not isinstance(positions, list):
            continue
        for pos in positions:
            try:
                positioned.append((int(pos), str(word)))
            except Exception:
                continue
    if not positioned:
        return ""
    return " ".join(word for _, word in sorted(positioned))


def first_metadata_description(data: dict) -> str:
    descriptions = ((data.get("data") or {}).get("attributes") or {}).get("descriptions") or []
    for item in descriptions:
        if str(item.get("descriptionType", "")).lower() == "abstract" and item.get("description"):
            return str(item["description"])
    for item in descriptions:
        if item.get("description"):
            return str(item["description"])
    return ""


def extract_html_detail_text(text: str) -> tuple[str, str]:
    meta_patterns = [
        r'<meta[^>]+(?:name|property)=["\']citation_abstract["\'][^>]+content=["\']([^"\']+)["\']',
        r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+(?:name|property)=["\']citation_abstract["\']',
        r'<meta[^>]+(?:name|property)=["\']description["\'][^>]+content=["\']([^"\']+)["\']',
        r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+(?:name|property)=["\']description["\']',
        r'<meta[^>]+(?:name|property)=["\']og:description["\'][^>]+content=["\']([^"\']+)["\']',
        r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+(?:name|property)=["\']og:description["\']',
        r'<meta[^>]+(?:name|property)=["\']dc\.description["\'][^>]+content=["\']([^"\']+)["\']',
        r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+(?:name|property)=["\']dc\.description["\']',
        r'<meta[^>]+(?:name|property)=["\']twitter:description["\'][^>]+content=["\']([^"\']+)["\']',
        r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+(?:name|property)=["\']twitter:description["\']',
    ]
    for pat in meta_patterns:
        match = re.search(pat, text, flags=re.I | re.S)
        if match:
            detail = clean_text(match.group(1))
            if detail:
                return "html_meta_abstract_or_description", detail
    abstract_patterns = [
        r'<(?:section|div)[^>]+(?:id|class)=["\'][^"\']*abstract[^"\']*["\'][^>]*>(.*?)</(?:section|div)>',
        r'<abstract[^>]*>(.*?)</abstract>',
    ]
    for pat in abstract_patterns:
        match = re.search(pat, text, flags=re.I | re.S)
        if match:
            detail = clean_text(match.group(1))
            if detail:
                return "html_visible_abstract", detail
    title_match = re.search(r"<title[^>]*>(.*?)</title>", text, flags=re.I | re.S)
    if title_match:
        detail = clean_text(title_match.group(1))
        if detail:
            return "html_title_only", detail
    return "", ""


def extract_detail_text(role: str, content: bytes, source_byte_class: str, content_type: str, final_url: str) -> tuple[str, str]:
    sniff = content_sniff(content, content_type, final_url)
    text = content[:2_000_000].decode("utf-8", errors="ignore")
    if sniff == "json":
        try:
            data = json.loads(text)
        except Exception:
            return "", ""
        detail = ""
        kind = "json_metadata_detail"
        if role.endswith("crossref_work_json"):
            message = data.get("message") or {}
            detail = message.get("abstract") or " ".join(message.get("title") or [])
            kind = "crossref_abstract_or_title"
        elif role.endswith("datacite_work_json"):
            detail = first_metadata_description(data)
            if not detail:
                detail = str((((data.get("data") or {}).get("attributes") or {}).get("titles") or [{}])[0].get("title", ""))
            kind = "datacite_description_or_title"
        elif role.endswith("openalex_work_json"):
            detail = reconstruct_openalex_abstract(data) or str(data.get("display_name", ""))
            kind = "openalex_abstract_or_title"
        elif role.endswith("unpaywall_work_json"):
            detail = str(data.get("title", ""))
            kind = "unpaywall_title"
        elif role.endswith("semantic_scholar_work_json"):
            detail = str(data.get("abstract") or data.get("title") or "")
            kind = "semantic_scholar_abstract_or_title"
        elif role.endswith("europepmc_search_json"):
            results = (data.get("resultList") or {}).get("result", []) or []
            if results:
                detail = str(results[0].get("abstractText") or results[0].get("title") or "")
            kind = "europepmc_abstract_or_title"
        elif role.startswith("clinicaltrials_"):
            protocol = data.get("protocolSection") or {}
            ident = protocol.get("identificationModule") or {}
            desc = protocol.get("descriptionModule") or {}
            detail = " ".join(
                x for x in [
                    ident.get("briefTitle", ""),
                    desc.get("briefSummary", ""),
                    desc.get("detailedDescription", ""),
                ]
                if x
            )
            kind = "clinicaltrials_summary"
        detail = clean_text(detail)
        return (kind, detail) if detail else ("", "")
    if sniff == "xml":
        abstract_match = re.search(r"<abstract[^>]*>(.*?)</abstract>", text, flags=re.I | re.S)
        if abstract_match:
            return "xml_abstract", clean_text(abstract_match.group(1))
        title_match = re.search(r"<article-title[^>]*>(.*?)</article-title>", text, flags=re.I | re.S)
        if title_match:
            return "xml_title_only", clean_text(title_match.group(1))
        pubmed_abstract = re.search(r"<AbstractText[^>]*>(.*?)</AbstractText>", text, flags=re.I | re.S)
        if pubmed_abstract:
            return "pubmed_xml_abstract", clean_text(pubmed_abstract.group(1))
    if sniff == "html":
        return extract_html_detail_text(text)
    if source_byte_class in {"full_article_pdf", "source_object_unclassified"}:
        return "binary_source_object_no_text_extracted", ""
    return "", ""


def html_has_fulltext_markers(text: str, final_url: str) -> bool:
    lower_url = final_url.lower()
    lower = text[:1_500_000].lower()
    if any(domain in lower_url for domain in ["journals.plos.org", "elifesciences.org"]):
        return True
    markers = [
        "article full text",
        "article__body",
        "article-section__content",
        "c-article-body",
        "id=\"bodymatter\"",
        "class=\"article-body",
        "section class=\"article",
        "data-article-section",
        "<h2>methods",
        "<h2>results",
        "references</h2>",
    ]
    return sum(marker in lower for marker in markers) >= 2


def is_preprint_or_repository_url(url: str) -> bool:
    return bool(PREPRINT_OR_REPOSITORY_HOST_RE.search(url or ""))


def strategy_group(role: str, url: str, final_url: str = "") -> str:
    role = role or ""
    route_url = final_url or url or ""
    if role.startswith("clinicaltrials_"):
        return "registry_clinicaltrials"
    if role == "stable_url":
        return "preprint_repository_candidate" if is_preprint_or_repository_url(route_url) else "stable_url"
    if role == "doi_publisher_html_last_resort" or "publisher_html" in role:
        return "direct_journal_or_doi_landing"
    if "_source_url_" in role:
        return "preprint_repository_candidate" if is_preprint_or_repository_url(route_url) else "oa_candidate_url"
    if role.startswith("pmc_") or "_pmc_" in role:
        return "pmc_fulltext"
    if role.endswith("crossref_work_json"):
        return "crossref_metadata"
    if role.endswith("datacite_work_json"):
        return "datacite_metadata"
    if role.endswith("unpaywall_work_json"):
        return "unpaywall_metadata"
    if role.endswith("openalex_work_json"):
        return "openalex_metadata"
    if role.endswith("semantic_scholar_work_json"):
        return "semantic_scholar_metadata"
    if role.endswith("europepmc_search_json"):
        return "europepmc_metadata"
    if role.startswith("pubmed_") or "pubmed_doi_" in role:
        return "pubmed_bridge"
    return "other"


def classify_source_object(role: str, content: bytes, status: int, content_type: str, final_url: str) -> tuple[str, str, str, bool]:
    """Return fetch_status, source_byte_class, note, strict level-5 eligibility."""
    text = content[:250_000].decode("utf-8", errors="ignore").lower()
    sniff = content_sniff(content, content_type, final_url)
    if status in {401, 402, 403}:
        return "blocked_http_status", "blocked_no_source_object", f"http_{status}", False
    if "captcha" in text or ("cloudflare" in text and "checking your browser" in text) or "verify you are human" in text:
        return "blocked_bot_or_captcha", "captcha_page", "captcha_or_bot_check", False
    if "access denied" in text or "forbidden" in text:
        return "blocked_access_denied_text", "access_denied_page", "access_denied_text", False
    if "login" in text and ("institution" in text or "subscribe" in text or "sign in" in text):
        return "landing_or_paywall_obtained", "paywall_or_login_page", "login_or_subscription_text_seen", False
    if "doi.org" in urlparse(final_url).netloc:
        return "doi_resolver_not_article", "metadata_record", "ended_at_doi_resolver", False
    metadata_role_suffixes = (
        "pubmed_esummary_json",
        "openalex_work_json",
        "crossref_work_json",
        "datacite_work_json",
        "unpaywall_work_json",
        "semantic_scholar_work_json",
        "europepmc_search_json",
        "pmc_oa_manifest_xml",
    )
    if any(role.endswith(suffix) for suffix in metadata_role_suffixes):
        return "support_metadata_obtained", "metadata_record", "", False
    if role.startswith("clinicaltrials_"):
        return "source_object_obtained", "registry_record_full", "", True
    if role.startswith("pubmed_efetch"):
        return "support_metadata_obtained", "pubmed_record_or_abstract", "pubmed_abstract_not_full_article", False
    if role.startswith("pmc_efetch"):
        if b"<article" in content[:200_000] or b"<pmc-articleset" in content[:200_000]:
            return "source_object_obtained", "pmc_fulltext_xml", "", True
        return "support_metadata_obtained", "metadata_record", "pmc_efetch_without_article_xml", False
    if sniff == "pdf":
        return "source_object_obtained", "full_article_pdf", "", True
    if sniff == "xml":
        return "source_object_obtained", "full_article_xml", "", True
    if sniff == "html":
        fulltext = html_has_fulltext_markers(content.decode("utf-8", errors="ignore"), final_url)
        if fulltext:
            return "source_object_obtained", "full_article_html", "", True
        return "landing_or_abstract_obtained", "publisher_landing_or_abstract", "html_without_fulltext_markers", False
    return "source_object_obtained", "source_object_unclassified", "", True


def host_delay_seconds(host: str) -> float:
    return HOST_MIN_DELAY_SECONDS.get(host, DEFAULT_HOST_DELAY_SECONDS)


def polite_wait(url: str) -> None:
    host = urlparse(url).netloc.lower()
    with _host_locks_guard:
        lock = _host_locks.setdefault(host, threading.Lock())
    with lock:
        now = time.monotonic()
        last = _host_last_request.get(host, 0.0)
        wait = host_delay_seconds(host) - (now - last)
        if wait > 0:
            time.sleep(wait)
        _host_last_request[host] = time.monotonic()


def classify_block_text(content: bytes, status: int, final_url: str) -> tuple[str, str]:
    text = content[:200_000].decode("utf-8", errors="ignore").lower()
    if status in {401, 402, 403}:
        return "blocked_http_status", f"http_{status}"
    if "captcha" in text or "cloudflare" in text and "checking your browser" in text:
        return "blocked_bot_or_captcha", "captcha_or_bot_check"
    if "access denied" in text or "forbidden" in text:
        return "blocked_access_denied_text", "access_denied_text"
    if "login" in text and ("institution" in text or "subscribe" in text):
        return "landing_or_paywall_obtained", "login_or_subscription_text_seen"
    if "doi.org" in urlparse(final_url).netloc:
        return "doi_resolver_not_article", "ended_at_doi_resolver"
    return "source_object_obtained", ""


def request_bytes(url: str) -> dict[str, str | int | bool]:
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/pdf,application/json;q=0.9,*/*;q=0.8",
    }
    if "api.semanticscholar.org" in url and SEMANTIC_SCHOLAR_API_KEY:
        headers["x-api-key"] = SEMANTIC_SCHOLAR_API_KEY
    if "api.core.ac.uk" in url and CORE_API_KEY:
        headers["Authorization"] = f"Bearer {CORE_API_KEY}"
    polite_wait(url)
    try:
        with requests.get(url, headers=headers, timeout=TIMEOUT, allow_redirects=True, stream=True) as resp:
            chunks: list[bytes] = []
            total = 0
            for chunk in resp.iter_content(chunk_size=65536):
                if not chunk:
                    continue
                chunks.append(chunk)
                total += len(chunk)
                if total > MAX_BYTES:
                    break
            content = b"".join(chunks)
            truncated = total > MAX_BYTES
            return {
                "ok": 200 <= resp.status_code < 300 and len(content) > 0,
                "status_code": resp.status_code,
                "final_url": resp.url,
                "content_type": resp.headers.get("content-type", ""),
                "content_length": len(content),
                "truncated": truncated,
                "content": content,
                "error": "",
            }
    except Exception as exc:  # noqa: BLE001 - audit script should record any failure.
        return {
            "ok": False,
            "status_code": "",
            "final_url": "",
            "content_type": "",
            "content_length": 0,
            "truncated": False,
            "content": b"",
            "error": repr(exc),
        }


def write_mirror(row_id: str, role: str, url: str, result: dict[str, str | int | bool]) -> tuple[str, str]:
    content = result["content"]
    assert isinstance(content, bytes)
    ext = extension_from_type(str(result["content_type"]), str(result["final_url"] or url))
    path = OUT_DIR / f"{row_id}__{role}__{slug(url)}{ext}"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    return str(path), sha256_bytes(content)


def fetch_and_record(row: pd.Series, role: str, url: str) -> dict[str, str]:
    result = request_bytes(url)
    content = result["content"]
    assert isinstance(content, bytes)
    local_path = ""
    local_sha = ""
    fetch_status = "request_failed"
    source_byte_class = "not_retrieved"
    level5_eligible = "false"
    note = str(result["error"])
    detail_kind = ""
    detail_text = ""
    if result["ok"]:
        fetch_status, source_byte_class, note, eligible = classify_source_object(
            role,
            content,
            int(result["status_code"]),
            str(result["content_type"]),
            str(result["final_url"]),
        )
        level5_eligible = str(eligible).lower()
        detail_kind, detail_text = extract_detail_text(
            role,
            content,
            source_byte_class,
            str(result["content_type"]),
            str(result["final_url"]),
        )
        if fetch_status not in {"blocked_bot_or_captcha", "blocked_access_denied_text", "doi_resolver_not_article"}:
            local_path, local_sha = write_mirror(str(row.source_result_id), role, url, result)
    elif str(result["status_code"]) in {"401", "402", "403"}:
        fetch_status = "blocked_http_status"
        source_byte_class = "blocked_no_source_object"
        note = f"http_{result['status_code']}"
        detail_kind, detail_text = extract_detail_text(
            role,
            content,
            source_byte_class,
            str(result["content_type"]),
            str(result["final_url"] or url),
        )
    group = strategy_group(role, url, str(result["final_url"]))
    detail_source = ""
    if detail_text:
        detail_source = str(result["final_url"]) or url
    return {
        "attempt_role": role,
        "strategy_group": group,
        "strategy_is_preprint_or_repository_candidate": str(group == "preprint_repository_candidate").lower(),
        "strategy_is_direct_journal_attempt": str(group == "direct_journal_or_doi_landing").lower(),
        "attempt_url": url,
        "http_status": str(result["status_code"]),
        "final_url": str(result["final_url"]),
        "content_type": str(result["content_type"]),
        "content_length": str(result["content_length"]),
        "truncated": str(result["truncated"]).lower(),
        "fetch_status": fetch_status,
        "source_byte_class": source_byte_class,
        "level5_eligible": level5_eligible,
        "local_path": local_path,
        "local_sha256": local_sha,
        "fetch_note": note,
        "source_detail_kind": detail_kind,
        "source_detail_text": detail_text,
        "source_detail_url": detail_source,
        "detail_contains_number": str(bool(NUMBER_RE.search(detail_text))).lower(),
        "detail_contains_effect_term": str(bool(EFFECT_TERM_RE.search(detail_text))).lower(),
        "detail_contains_n_term": str(bool(N_TERM_RE.search(detail_text))).lower(),
    }


def doi_from_pubmed_html(content: bytes) -> str:
    text = content.decode("utf-8", errors="ignore")
    for pat in [
        r'name="citation_doi"\s+content="([^"]+)"',
        r'data-ga-action="DOI"\s+href="https?://doi\.org/([^"]+)"',
    ]:
        match = re.search(pat, text, flags=re.I)
        if match:
            return match.group(1).strip()
    match = DOI_RE.search(text)
    return match.group(0).rstrip(".") if match else ""


def ids_from_pubmed_summary(content: bytes, pmid: str) -> tuple[str, str]:
    try:
        data = json.loads(content.decode("utf-8", errors="ignore"))
        item = data.get("result", {}).get(pmid, {})
        doi = ""
        pmcid = ""
        for article_id in item.get("articleids", []):
            idtype = str(article_id.get("idtype", "")).lower()
            value = str(article_id.get("value", "")).strip()
            if idtype == "doi" and value:
                doi = value
            if idtype == "pmc" and value:
                pmcid = value.upper()
        return doi, pmcid
    except Exception:
        return "", ""


def doi_from_row(row: pd.Series) -> str:
    primary = row.get("primary_real_world_url", "")
    if row.get("crossref_resolved_doi", ""):
        return row.get("crossref_resolved_doi", "")
    if row.get("doi_list", ""):
        return split_first(row.get("doi_list", ""), DOI_RE)
    if primary.startswith("https://doi.org/"):
        return primary.replace("https://doi.org/", "", 1)
    return split_first(primary, DOI_RE)


def openalex_urls(content: bytes) -> list[str]:
    try:
        data = json.loads(content.decode("utf-8", errors="ignore"))
    except Exception:
        return []
    urls: list[str] = []
    for container in [data.get("primary_location") or {}, data.get("best_oa_location") or {}]:
        for key in ["pdf_url", "landing_page_url"]:
            value = container.get(key)
            if value:
                urls.append(str(value))
    oa_url = (data.get("open_access") or {}).get("oa_url")
    if oa_url:
        urls.append(str(oa_url))
    for loc in data.get("locations", []) or []:
        for key in ["pdf_url", "landing_page_url"]:
            value = loc.get(key)
            if value:
                urls.append(str(value))
    seen: set[str] = set()
    out: list[str] = []
    for url in urls:
        if url and url not in seen and not url.startswith("https://doi.org/"):
            seen.add(url)
            out.append(url)
    return out[:3]


def unpaywall_urls(content: bytes) -> list[str]:
    try:
        data = json.loads(content.decode("utf-8", errors="ignore"))
    except Exception:
        return []
    urls: list[str] = []
    locations = []
    if data.get("best_oa_location"):
        locations.append(data["best_oa_location"])
    locations.extend(data.get("oa_locations") or [])
    for loc in locations:
        for key in ["url_for_pdf", "url", "url_for_landing_page"]:
            value = loc.get(key)
            if value:
                urls.append(str(value))
    seen: set[str] = set()
    out: list[str] = []
    for url in urls:
        if url and url not in seen:
            seen.add(url)
            out.append(url)
    return out[:3]


def semantic_scholar_urls(content: bytes) -> list[str]:
    try:
        data = json.loads(content.decode("utf-8", errors="ignore"))
    except Exception:
        return []
    urls: list[str] = []
    oa_pdf = data.get("openAccessPdf") or {}
    if oa_pdf.get("url"):
        urls.append(str(oa_pdf["url"]))
    if data.get("url"):
        urls.append(str(data["url"]))
    seen: set[str] = set()
    out: list[str] = []
    for url in urls:
        if url and url not in seen:
            seen.add(url)
            out.append(url)
    return out[:2]


def europepmc_urls_and_pmcids(content: bytes) -> tuple[list[str], list[str]]:
    try:
        data = json.loads(content.decode("utf-8", errors="ignore"))
    except Exception:
        return [], []
    urls: list[str] = []
    pmcids: list[str] = []
    for result in (data.get("resultList") or {}).get("result", []) or []:
        pmcid = str(result.get("pmcid", "")).strip()
        if pmcid:
            pmcids.append(pmcid.upper())
        full_text_urls = (result.get("fullTextUrlList") or {}).get("fullTextUrl", []) or []
        for item in full_text_urls:
            url = item.get("url")
            if url:
                urls.append(str(url))
    seen: set[str] = set()
    uniq_urls: list[str] = []
    for url in urls:
        if url and url not in seen:
            seen.add(url)
            uniq_urls.append(url)
    return uniq_urls[:3], list(dict.fromkeys(pmcids))[:2]


def crossref_candidate_urls(content: bytes) -> list[str]:
    try:
        data = json.loads(content.decode("utf-8", errors="ignore"))
    except Exception:
        return []
    urls: list[str] = []
    message = data.get("message") or {}
    for link in message.get("link", []) or []:
        url = link.get("URL")
        if url:
            urls.append(str(url))
    return list(dict.fromkeys(urls))[:3]


def row_has_source_object(records: list[dict[str, str]]) -> bool:
    return any(
        rec.get("local_path")
        and rec.get("level5_eligible") == "true"
        for rec in records
    )


def fetch_candidate_urls(row: pd.Series, records: list[dict[str, str]], prefix: str, urls: list[str]) -> None:
    for i, url in enumerate(urls, start=1):
        if not url or row_has_source_object(records):
            break
        rec = fetch_and_record(row, f"{prefix}_source_url_{i}", url)
        records.append(rec)
        time.sleep(SLEEP_SECONDS)


def fetch_doi_metadata_routes(row: pd.Series, records: list[dict[str, str]], doi: str, prefix: str = "") -> None:
    if not doi:
        return
    safe = quote(doi, safe="/:._;()-")
    route_prefix = f"{prefix}_" if prefix else ""
    metadata_routes: list[tuple[str, str]] = [
        (f"{route_prefix}crossref_work_json", f"https://api.crossref.org/works/{safe}" + (f"?mailto={quote(CONTACT_EMAIL)}" if CONTACT_EMAIL else "")),
        (f"{route_prefix}datacite_work_json", f"https://api.datacite.org/dois/{safe}"),
    ]
    if UNPAYWALL_EMAIL and "example.invalid" not in UNPAYWALL_EMAIL:
        metadata_routes.append((f"{route_prefix}unpaywall_work_json", f"https://api.unpaywall.org/v2/{safe}?email={quote(UNPAYWALL_EMAIL)}"))
    openalex_url = f"https://api.openalex.org/works/doi:{safe}"
    if OPENALEX_API_KEY:
        openalex_url += f"?api_key={quote(OPENALEX_API_KEY)}"
    metadata_routes.append((f"{route_prefix}openalex_work_json", openalex_url))
    metadata_routes.append((
        f"{route_prefix}semantic_scholar_work_json",
        f"https://api.semanticscholar.org/graph/v1/paper/DOI:{safe}?fields=externalIds,url,openAccessPdf,title,abstract,year,authors",
    ))
    metadata_routes.append((
        f"{route_prefix}europepmc_search_json",
        f"https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=DOI:%22{safe}%22&format=json&resultType=core",
    ))
    for role, url in metadata_routes:
        if row_has_source_object(records):
            break
        rec = fetch_and_record(row, role, url)
        records.append(rec)
        if rec["local_path"]:
            content = Path(rec["local_path"]).read_bytes()
            if role.endswith("crossref_work_json"):
                fetch_candidate_urls(row, records, role, crossref_candidate_urls(content))
            elif role.endswith("unpaywall_work_json"):
                fetch_candidate_urls(row, records, role, unpaywall_urls(content))
            elif role.endswith("openalex_work_json"):
                fetch_candidate_urls(row, records, role, openalex_urls(content))
            elif role.endswith("semantic_scholar_work_json"):
                fetch_candidate_urls(row, records, role, semantic_scholar_urls(content))
            elif role.endswith("europepmc_search_json"):
                urls, pmcids = europepmc_urls_and_pmcids(content)
                fetch_candidate_urls(row, records, role, urls)
                for pmcid in pmcids:
                    if row_has_source_object(records):
                        break
                    pmc_num = re.sub(r"^PMC", "", pmcid, flags=re.I)
                    for pmc_role, pmc_url in [
                        (f"{role}_pmc_efetch_xml", f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pmc&id={pmc_num}&retmode=xml"),
                        (f"{role}_pmc_oa_manifest_xml", f"https://www.ncbi.nlm.nih.gov/pmc/utils/oa/oa.fcgi?id={pmcid}"),
                    ]:
                        pmc_rec = fetch_and_record(row, pmc_role, pmc_url)
                        records.append(pmc_rec)
                        time.sleep(SLEEP_SECONDS)
        time.sleep(SLEEP_SECONDS)


def fetch_row(row: pd.Series) -> list[dict[str, str]]:
    target_kind = detect_kind(row)
    attempts: list[tuple[str, str]] = []
    primary = row.get("primary_real_world_url", "")
    if target_kind == "nct_registry":
        nct = split_first(row.get("nct_list", ""), NCT_RE) or split_first(primary, NCT_RE)
        attempts.append(("clinicaltrials_api_v2_json", f"https://clinicaltrials.gov/api/v2/studies/{nct}"))
        attempts.append(("clinicaltrials_html", f"https://clinicaltrials.gov/study/{nct}"))
    elif target_kind == "pmc_fulltext":
        pmcid = split_first(row.get("pmcid_list", ""), PMCID_RE) or split_first(primary, PMCID_RE)
        pmc_num = re.sub(r"^PMC", "", pmcid, flags=re.I)
        attempts.append(("pmc_efetch_xml", f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pmc&id={pmc_num}&retmode=xml"))
        attempts.append(("pmc_oa_manifest_xml", f"https://www.ncbi.nlm.nih.gov/pmc/utils/oa/oa.fcgi?id={pmcid}"))
        attempts.append(("pmc_fulltext_html", f"https://pmc.ncbi.nlm.nih.gov/articles/{pmcid}/"))
    elif target_kind == "pmid_record":
        pmid = split_first(row.get("pmid_list", ""), re.compile(r"\d+")) or split_first(primary, re.compile(r"\d+"))
        attempts.append(("pubmed_esummary_json", f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&id={pmid}&retmode=json"))
        attempts.append(("pubmed_efetch_xml", f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id={pmid}&retmode=xml"))
    elif target_kind == "doi_article":
        doi = doi_from_row(row)
        attempts.append(("doi_metadata_seed", doi))
    elif primary:
        attempts.append(("stable_url", primary))

    records: list[dict[str, str]] = []
    pubmed_doi = ""
    pubmed_pmcid = ""
    for role, url in attempts:
        if role == "doi_metadata_seed":
            fetch_doi_metadata_routes(row, records, url)
            continue
        if not url or url in {"https://doi.org/", "https://pubmed.ncbi.nlm.nih.gov//", "https://pmc.ncbi.nlm.nih.gov/articles//"}:
            continue
        rec = fetch_and_record(row, role, url)
        records.append(rec)
        if role == "pubmed_esummary_json" and rec["local_path"]:
            pmid = split_first(row.get("pmid_list", ""), re.compile(r"\d+")) or split_first(primary, re.compile(r"\d+"))
            content = Path(rec["local_path"]).read_bytes()
            pubmed_doi, pubmed_pmcid = ids_from_pubmed_summary(content, pmid)
        time.sleep(SLEEP_SECONDS)

    if pubmed_doi:
        fetch_doi_metadata_routes(row, records, pubmed_doi, prefix="pubmed_doi")
    if pubmed_pmcid and not row_has_source_object(records):
        pmc_num = re.sub(r"^PMC", "", pubmed_pmcid, flags=re.I)
        for role, url in [
            ("pmc_efetch_xml_from_pubmed", f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pmc&id={pmc_num}&retmode=xml"),
            ("pmc_oa_manifest_xml_from_pubmed", f"https://www.ncbi.nlm.nih.gov/pmc/utils/oa/oa.fcgi?id={pubmed_pmcid}"),
        ]:
            rec = fetch_and_record(row, role, url)
            records.append(rec)
            time.sleep(SLEEP_SECONDS)

    if target_kind == "doi_article" and not row_has_source_object(records):
        doi = doi_from_row(row)
        if doi:
            rec = fetch_and_record(
                row,
                "doi_publisher_html_last_resort",
                f"https://doi.org/{quote(doi, safe='/:._;()-')}",
            )
            records.append(rec)
            time.sleep(SLEEP_SECONDS)

    if not records:
        records.append(
            {
                "attempt_role": "",
                "strategy_group": "other",
                "strategy_is_preprint_or_repository_candidate": "false",
                "strategy_is_direct_journal_attempt": "false",
                "attempt_url": "",
                "http_status": "",
                "final_url": "",
                "content_type": "",
                "content_length": "0",
                "truncated": "false",
                "fetch_status": "no_attemptable_url",
                "source_byte_class": "not_retrieved",
                "level5_eligible": "false",
                "local_path": "",
                "local_sha256": "",
                "fetch_note": "No URL or supported identifier was available.",
                "source_detail_kind": "",
                "source_detail_text": "",
                "source_detail_url": "",
                "detail_contains_number": "false",
                "detail_contains_effect_term": "false",
                "detail_contains_n_term": "false",
            }
        )

    enriched: list[dict[str, str]] = []
    for rec in records:
        out = {
            "source_result_id": row.get("source_result_id", ""),
            "result_label": row.get("result_label", ""),
            "source_family": row.get("source_family", ""),
            "target_kind": target_kind,
            "primary_real_world_url": row.get("primary_real_world_url", ""),
            "primary_real_world_url_basis": row.get("primary_real_world_url_basis", ""),
            "previous_evidence_level": row.get("evidence_level", ""),
            "previous_evidence_level_name": row.get("evidence_level_name", ""),
            "represented_source_title": row.get("crossref_resolved_title", "") or row.get("source_bib_title", ""),
        }
        out.update(rec)
        enriched.append(out)
    return enriched


def unique_nonempty(values: pd.Series, limit: int = 8) -> str:
    out: list[str] = []
    for value in pd.unique(values.astype(str)):
        if value and value != "nan":
            out.append(value)
        if len(out) >= limit:
            break
    return " | ".join(out)


def best_attempt_row(group: pd.DataFrame) -> pd.Series:
    if group.empty:
        return pd.Series(dtype=str)
    ranked = group.assign(
        _eligible=group["level5_eligible"].astype(str).eq("true"),
        _has_local=group["local_path"].astype(str).ne(""),
        _has_detail=group["source_detail_text"].astype(str).ne(""),
    ).sort_values(["_eligible", "_has_local", "_has_detail"], ascending=[False, False, False], kind="stable")
    return ranked.iloc[0]


def strategy_status(group: pd.DataFrame) -> str:
    if group.empty:
        return "not_tried"
    if group["level5_eligible"].astype(str).eq("true").any():
        return "level5_source_object_obtained"
    classes = set(group["source_byte_class"].astype(str))
    statuses = set(group["fetch_status"].astype(str))
    if "captcha_page" in classes or "blocked_bot_or_captcha" in statuses:
        return "captcha_or_bot_block"
    if "paywall_or_login_page" in classes or "landing_or_paywall_obtained" in statuses:
        return "paywall_or_login"
    if "publisher_landing_or_abstract" in classes:
        return "landing_or_abstract_obtained"
    if group["source_detail_text"].astype(str).ne("").any():
        return "abstract_or_detail_obtained"
    if "blocked_http_status" in statuses:
        return "blocked_http_status"
    if group["local_path"].astype(str).ne("").any():
        return "metadata_or_noneligible_bytes_obtained"
    if "request_failed" in statuses:
        return "request_failed"
    return unique_nonempty(group["fetch_status"], limit=3) or "attempted"


def summarize_strategy_columns(group: pd.DataFrame) -> dict[str, str]:
    out: dict[str, str] = {
        "unpaywall_configured": str(bool(UNPAYWALL_EMAIL and "example.invalid" not in UNPAYWALL_EMAIL)).lower(),
        "openalex_api_key_configured": str(bool(OPENALEX_API_KEY)).lower(),
        "semantic_scholar_api_key_configured": str(bool(SEMANTIC_SCHOLAR_API_KEY)).lower(),
        "core_api_key_configured": str(bool(CORE_API_KEY)).lower(),
    }
    for strategy in STRATEGY_GROUPS:
        subset = group[group["strategy_group"].astype(str).eq(strategy)]
        prefix = f"strategy_{strategy}"
        best = best_attempt_row(subset)
        out[f"{prefix}_tried"] = str(not subset.empty).lower()
        out[f"{prefix}_status"] = strategy_status(subset)
        out[f"{prefix}_attempt_count"] = str(len(subset))
        out[f"{prefix}_http_statuses"] = unique_nonempty(subset["http_status"], limit=5) if not subset.empty else ""
        out[f"{prefix}_byte_classes"] = unique_nonempty(subset["source_byte_class"], limit=5) if not subset.empty else ""
        out[f"{prefix}_best_url"] = str(best.get("final_url") or best.get("attempt_url") or "") if not best.empty else ""
        out[f"{prefix}_best_local_path"] = str(best.get("local_path", "")) if not best.empty else ""

    detail_rows = group[group["source_detail_text"].astype(str).ne("")]
    detail_texts = [clean_text(x, max_len=1400) for x in pd.unique(detail_rows["source_detail_text"].astype(str)) if x][:3]
    out["abstract_or_detail_obtained"] = str(bool(detail_texts)).lower()
    out["abstract_or_detail_kinds"] = unique_nonempty(detail_rows["source_detail_kind"], limit=5) if not detail_rows.empty else ""
    out["abstract_or_detail_sources"] = unique_nonempty(detail_rows["source_detail_url"], limit=5) if not detail_rows.empty else ""
    out["abstract_or_detail_text"] = " || ".join(detail_texts)
    out["detail_contains_number"] = str(group["detail_contains_number"].astype(str).eq("true").any()).lower()
    out["detail_contains_effect_term"] = str(group["detail_contains_effect_term"].astype(str).eq("true").any()).lower()
    out["detail_contains_n_term"] = str(group["detail_contains_n_term"].astype(str).eq("true").any()).lower()
    out["paywall_or_login_seen"] = str(group["source_byte_class"].astype(str).isin(["paywall_or_login_page"]).any()).lower()
    out["publisher_landing_or_abstract_seen"] = str(group["source_byte_class"].astype(str).isin(["publisher_landing_or_abstract"]).any()).lower()
    out["captcha_or_bot_block_seen"] = str(group["source_byte_class"].astype(str).isin(["captcha_page"]).any()).lower()
    out["access_denied_seen"] = str(group["source_byte_class"].astype(str).isin(["access_denied_page"]).any()).lower()
    out["blocked_http_status_seen"] = str(group["fetch_status"].astype(str).eq("blocked_http_status").any()).lower()
    candidate_rows = group[group["strategy_group"].astype(str).isin(["oa_candidate_url", "preprint_repository_candidate"])]
    out["oa_or_preprint_candidate_urls_attempted"] = unique_nonempty(
        candidate_rows["final_url"].where(candidate_rows["final_url"].astype(str).ne(""), candidate_rows["attempt_url"]),
        limit=10,
    ) if not candidate_rows.empty else ""
    out["preprint_or_repository_candidate_seen"] = str(
        group["strategy_group"].astype(str).eq("preprint_repository_candidate").any()
    ).lower()
    return out


def main() -> None:
    df = pd.read_csv(GROUNDING, sep="\t", dtype=str, keep_default_na=False)
    targets = df[df["evidence_level_name"].eq("target_source_independently_grounded")].copy()
    rows: list[dict[str, str]] = []
    target_rows = [row for _, row in targets.iterrows()]
    with ThreadPoolExecutor(max_workers=LEVEL5_WORKERS) as executor:
        futures = {executor.submit(fetch_row, row): row.get("source_result_id", "") for row in target_rows}
        for future in as_completed(futures):
            rows.extend(future.result())
    attempts = pd.DataFrame(rows)
    attempts = attempts.sort_values(["source_result_id", "attempt_role", "attempt_url"], kind="stable")
    attempts.to_csv(OUT_TSV, sep="\t", index=False)

    strategy_rows = []
    for source_result_id, group in attempts.groupby("source_result_id", dropna=False):
        strategy_rows.append({"source_result_id": source_result_id, **summarize_strategy_columns(group)})
    strategy_df = pd.DataFrame(strategy_rows)

    best = attempts.assign(
        obtained=attempts["local_path"].astype(str).ne("") & attempts["level5_eligible"].eq("true"),
        noneligible_bytes=attempts["local_path"].astype(str).ne("") & ~attempts["level5_eligible"].eq("true"),
    )
    per_row = (
        best.groupby("source_result_id", dropna=False)
        .agg(
            any_level5_obtained=("obtained", "max"),
            any_source_object=("obtained", "max"),
            any_noneligible_bytes=("noneligible_bytes", "max"),
            any_landing_paywall=("source_byte_class", lambda s: bool(s.isin(["paywall_or_login_page", "publisher_landing_or_abstract"]).any())),
            best_status=("fetch_status", lambda s: " | ".join(pd.unique(s.astype(str))[:4])),
            source_byte_classes=("source_byte_class", lambda s: " | ".join(pd.unique(s.astype(str))[:8])),
            attempts=("source_result_id", "size"),
            target_kind=("target_kind", "first"),
            source_family=("source_family", "first"),
            result_label=("result_label", "first"),
            primary_real_world_url=("primary_real_world_url", "first"),
            represented_source_title=("represented_source_title", "first"),
            local_paths=("local_path", lambda s: " | ".join([x for x in pd.unique(s.astype(str)) if x][:8])),
            final_urls=("final_url", lambda s: " | ".join([x for x in pd.unique(s.astype(str)) if x][:8])),
            attempt_roles=("attempt_role", lambda s: " | ".join(pd.unique(s.astype(str))[:8])),
        )
        .reset_index()
    )
    per_row = per_row.merge(strategy_df, on="source_result_id", how="left")
    per_row["level5_candidate_quality"] = per_row.apply(
        lambda r: "strict_level5_source_object_obtained"
        if r.any_source_object
        else ("noneligible_bytes_obtained" if r.any_noneligible_bytes else "not_obtained"),
        axis=1,
    )
    per_row["manual_next_step"] = per_row.apply(
        lambda r: "review mirrored eligible source object and promote to level 5 if identity matches the represented target source"
        if r.any_source_object
        else (
            "review noneligible bytes for routing clues; do not promote unless a value-bearing source object is found"
            if r.any_noneligible_bytes
            else "manual source acquisition needed: publisher 403/captcha/no OA route found"
        ),
        axis=1,
    )
    per_row.to_csv(OUT_ROW_STATUS, sep="\t", index=False)
    per_row[~per_row["any_level5_obtained"]].to_csv(OUT_TODOS, sep="\t", index=False)
    summary_parts = [
        pd.DataFrame(
            [
                {"metric": "existing_rows_level5_or_higher_before_probe", "value": int(df["evidence_level"].astype(int).ge(5).sum())},
                {"metric": "level4_rows_attempted", "value": len(targets)},
                {"metric": "rows_with_strict_level5_source_object_obtained", "value": int(per_row["any_level5_obtained"].sum())},
                {"metric": "rows_with_noneligible_bytes_only", "value": int((~per_row["any_level5_obtained"] & per_row["any_noneligible_bytes"]).sum())},
                {"metric": "rows_still_below_level5_after_probe", "value": int((~per_row["any_level5_obtained"]).sum())},
                {"metric": "rows_with_no_bytes_at_all", "value": int((~per_row["any_level5_obtained"] & ~per_row["any_noneligible_bytes"]).sum())},
                {"metric": "strict_total_level5_or_higher_after_review", "value": int(df["evidence_level"].astype(int).ge(5).sum()) + int(per_row["any_level5_obtained"].sum())},
                {"metric": "fetch_attempts", "value": len(attempts)},
                {"metric": "rows_with_abstract_or_detail_obtained", "value": int(per_row["abstract_or_detail_obtained"].astype(str).eq("true").sum())},
                {"metric": "rows_with_detail_containing_number", "value": int(per_row["detail_contains_number"].astype(str).eq("true").sum())},
                {"metric": "rows_with_detail_containing_effect_term", "value": int(per_row["detail_contains_effect_term"].astype(str).eq("true").sum())},
                {"metric": "rows_with_detail_containing_n_term", "value": int(per_row["detail_contains_n_term"].astype(str).eq("true").sum())},
                {"metric": "rows_with_paywall_or_login_seen", "value": int(per_row["paywall_or_login_seen"].astype(str).eq("true").sum())},
                {"metric": "rows_with_captcha_or_bot_block_seen", "value": int(per_row["captcha_or_bot_block_seen"].astype(str).eq("true").sum())},
                {"metric": "rows_with_preprint_or_repository_candidate_seen", "value": int(per_row["preprint_or_repository_candidate_seen"].astype(str).eq("true").sum())},
            ]
        ),
        per_row.groupby(["target_kind", "any_level5_obtained"]).size().reset_index(name="value").assign(
            metric=lambda d: "by_kind::" + d["target_kind"] + "::obtained_" + d["any_level5_obtained"].astype(str)
        )[["metric", "value"]],
        attempts.groupby("strategy_group").size().reset_index(name="value").assign(
            metric=lambda d: "strategy_attempts::" + d["strategy_group"]
        )[["metric", "value"]],
        per_row.groupby(["strategy_direct_journal_or_doi_landing_status"]).size().reset_index(name="value").assign(
            metric=lambda d: "direct_journal_status::" + d["strategy_direct_journal_or_doi_landing_status"]
        )[["metric", "value"]],
        per_row.groupby(["strategy_preprint_repository_candidate_status"]).size().reset_index(name="value").assign(
            metric=lambda d: "preprint_repository_status::" + d["strategy_preprint_repository_candidate_status"]
        )[["metric", "value"]],
        attempts.groupby("fetch_status").size().reset_index(name="value").assign(
            metric=lambda d: "fetch_status::" + d["fetch_status"]
        )[["metric", "value"]],
    ]
    summary = pd.concat(summary_parts, ignore_index=True)
    summary.to_csv(OUT_SUMMARY, sep="\t", index=False)

    obtained = int(per_row["any_level5_obtained"].sum())
    target_n = len(targets)
    existing_ge5 = int(df["evidence_level"].astype(int).ge(5).sum())
    projected_ge5 = existing_ge5 + obtained
    quality_counts = per_row["level5_candidate_quality"].value_counts().to_dict()
    by_kind = per_row.groupby(["target_kind", "any_level5_obtained"]).size().reset_index(name="n")
    md = [
        f"# Level-5 Push Probe For {SAMPLE_N}-Row Provenance Pilot",
        "",
        "This probe tries to mirror strict level-5 source objects for rows that were already at level 4 (`target_source_independently_grounded`). It does not promote rows automatically; it writes auditable fetch attempts.",
        "",
        "## Result",
        "",
        f"- Rows already at level >=5 before the probe: {existing_ge5}/{SAMPLE_N} ({existing_ge5 / SAMPLE_N:.1%})",
        f"- Level-4 rows attempted: {target_n}",
        f"- Rows with at least one strict level-5-eligible source object mirrored: {obtained}/{target_n} ({obtained / target_n:.1%})",
        f"- Rows still below level 5 after this probe: {target_n - obtained}/{target_n} ({(target_n - obtained) / target_n:.1%})",
        f"- Projected level >=5 after review/promotion of strict candidates: {projected_ge5}/{SAMPLE_N} ({projected_ge5 / SAMPLE_N:.1%})",
        "",
        "Row-level quality:",
        "",
        f"- strict level-5 source object obtained: {quality_counts.get('strict_level5_source_object_obtained', 0)}",
        f"- noneligible bytes obtained: {quality_counts.get('noneligible_bytes_obtained', 0)}",
        f"- not obtained: {quality_counts.get('not_obtained', 0)}",
        "",
        "By identifier route:",
        "",
    ]
    for _, row in by_kind.iterrows():
        status = "obtained" if bool(row.any_level5_obtained) else "not_obtained"
        md.append(f"- {row.target_kind}::{status}: {row.n}")
    md.extend([
        "",
        "## Files",
        "",
        f"- `{OUT_TSV}`",
        f"- `{OUT_SUMMARY}`",
        f"- `{OUT_ROW_STATUS}`",
        f"- `{OUT_TODOS}`",
        f"- mirrored bytes under `{OUT_DIR}/`",
        "",
        "## Route Strategy Columns",
        "",
        "The row-status TSV records acquisition routes separately instead of flattening every fetch into one status:",
        "",
        "- `strategy_direct_journal_or_doi_landing_*`: direct DOI/publisher attempt, including paywall, abstract page, bot block, or HTTP block.",
        "- `strategy_oa_candidate_url_*`: candidate full-text/PDF/XML URLs exposed by Crossref, OpenAlex, Semantic Scholar, Europe PMC, or Unpaywall-style metadata.",
        "- `strategy_preprint_repository_candidate_*`: repository, preprint, author-manuscript, or institutional-archive candidates discovered through metadata routes.",
        "- `abstract_or_detail_*`: short abstract, title, description, registry summary, or other lawful detail text extracted from metadata or returned landing pages. This is grounding evidence only; it does not make a row level 5 unless the object itself is value-bearing.",
        "- `paywall_or_login_seen`, `captcha_or_bot_block_seen`, `blocked_http_status_seen`, and `publisher_landing_or_abstract_seen`: blocker flags for manual follow-up.",
        "",
        "## Summary",
        "",
    ])
    for _, row in summary.iterrows():
        md.append(f"- {row.metric}: {row.value}")
    OUT_REPORT.write_text("\n".join(md) + "\n")

    print(f"Wrote {OUT_TSV}")
    print(f"Wrote {OUT_SUMMARY}")
    print(f"Wrote {OUT_REPORT}")
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
