#!/usr/bin/env python3
"""Acquire full article text candidates beyond direct PDF routes.

This pass targets represented sources that do not yet have full article text in
source_file. It tries reliable open routes from the research pass:

* Europe PMC fullTextXML by DOI/PMCID.
* Crossref TDM/full-text links, accepting PDF/XML/full-article HTML.
* OpenAIRE Graph instance URLs, especially repository/direct-PDF URLs.
* Wayback CDX PDF captures for blocked/missing URLs already in the candidate ledger.

Accepted candidates are promoted into source_file. All route outcomes are
appended to source_object_candidate_codebook_sample_300.tsv.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
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

SOURCE_RESULT = PILOT / f"source_result_codebook_{SAMPLE_SUFFIX}.tsv"
SOURCE = PILOT / f"source_codebook_{SAMPLE_SUFFIX}.tsv"
SOURCE_IDENTIFIER = PILOT / f"source_identifier_codebook_{SAMPLE_SUFFIX}.tsv"
SOURCE_FILE = PILOT / f"source_file_codebook_{SAMPLE_SUFFIX}.tsv"
SOURCE_ACCESS = PILOT / f"source_access_codebook_{SAMPLE_SUFFIX}.tsv"
SOURCE_ACCESS_ATTEMPT = PILOT / f"source_access_attempt_codebook_{SAMPLE_SUFFIX}.tsv"
SOURCE_ACCESS_RIGHT = PILOT / f"source_access_right_codebook_{SAMPLE_SUFFIX}.tsv"
SOURCE_VERSION = PILOT / f"source_version_codebook_{SAMPLE_SUFFIX}.tsv"
SOURCE_OBJECT_CANDIDATE = PILOT / f"source_object_candidate_codebook_{SAMPLE_SUFFIX}.tsv"

CACHE_DIR = ROOT / "data" / "cache" / "full_article_text_acquisition" / SAMPLE_SUFFIX
RUN_LABEL = re.sub(r"[^A-Za-z0-9._-]+", "_", os.environ.get("FULL_ARTICLE_RUN_LABEL", "").strip()).strip("_")
RUN_SUFFIX = f"_{RUN_LABEL}" if RUN_LABEL else ""
OUT_ATTEMPTS = PILOT / f"full_article_text_acquisition_attempts_{SAMPLE_SUFFIX}{RUN_SUFFIX}.tsv"
OUT_SUMMARY = PILOT / f"full_article_text_acquisition_summary_{SAMPLE_SUFFIX}{RUN_SUFFIX}.tsv"
OUT_REPORT = ROOT / "reports" / f"full_article_text_acquisition_{SAMPLE_SUFFIX}{RUN_SUFFIX}_2026-04-30.md"

CONTACT_EMAIL = os.environ.get("PROVENANCE_CONTACT_EMAIL", "rexdouglass@gmail.com").strip()
CORE_API_KEY = os.environ.get("CORE_API_KEY", "").strip()
TIMEOUT = int(os.environ.get("FULL_ARTICLE_TIMEOUT", "18"))
REQUEST_DELAY = float(os.environ.get("FULL_ARTICLE_REQUEST_DELAY_SECONDS", "0.25"))
MAX_BYTES = int(os.environ.get("FULL_ARTICLE_MAX_BYTES", str(90_000_000)))
MAX_ROWS = int(os.environ.get("FULL_ARTICLE_MAX_ROWS", "300"))
MAX_CANDIDATES_PER_ROUTE = int(os.environ.get("FULL_ARTICLE_MAX_CANDIDATES_PER_ROUTE", "4"))
ENABLE_WAYBACK = os.environ.get("FULL_ARTICLE_ENABLE_WAYBACK", "true").lower() in {"1", "true", "yes"}
ENABLE_OPENAIRE = os.environ.get("FULL_ARTICLE_ENABLE_OPENAIRE", "true").lower() in {"1", "true", "yes"}
ENABLE_CORE = bool(CORE_API_KEY) and os.environ.get("FULL_ARTICLE_ENABLE_CORE", "true").lower() in {"1", "true", "yes"}
ONLY_RESULT_IDS = {
    item.strip()
    for item in os.environ.get("FULL_ARTICLE_ONLY_RESULT_IDS", "").split(",")
    if item.strip()
}

USER_AGENT = (
    "PublishedSmallNStudiesDontMatter full-article acquisition "
    f"(mailto:{CONTACT_EMAIL}; noncommercial source verification)"
)

ARTICLE_CLASSES = {
    "full_article_pdf",
    "full_article_xml",
    "full_article_html",
    "pmc_fulltext_xml",
    "author_manuscript_fulltext",
}
DOI_RE = re.compile(r"10\.\d{4,9}/[-._;()/:A-Z0-9]+", re.I)
PMID_RE = re.compile(r"\b\d{6,9}\b")
PMCID_RE = re.compile(r"\bPMC\d+\b", re.I)
NCT_RE = re.compile(r"\bNCT\d{8}\b", re.I)
WORD_RE = re.compile(r"[a-z0-9]+")
PDF_URL_RE = re.compile(r"\.pdf(?:[?#].*)?$", re.I)

STOPWORDS = {
    "about",
    "after",
    "among",
    "and",
    "article",
    "between",
    "from",
    "have",
    "into",
    "more",
    "paper",
    "study",
    "that",
    "the",
    "their",
    "them",
    "this",
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


def stable_id(prefix: str, *parts: object) -> str:
    text = "\n".join(safe_text(part) for part in parts)
    return f"{prefix}_{hashlib.sha256(text.encode('utf-8')).hexdigest()[:12]}"


def sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def normalize_doi(value: str) -> str:
    text = safe_text(value)
    text = re.sub(r"^doi:\s*", "", text, flags=re.I)
    text = re.sub(r"^https?://(?:dx\.)?doi\.org/", "", text, flags=re.I)
    match = DOI_RE.search(text)
    if not match:
        return ""
    return re.sub(r"(10\.\d{4,9})//+", r"\1/", match.group(0).rstrip(".,;)"), flags=re.I).lower()


def extract_dois(value: str) -> list[str]:
    out = []
    for match in DOI_RE.finditer(safe_text(value)):
        doi = normalize_doi(match.group(0))
        if doi:
            out.append(doi)
    return list(dict.fromkeys(out))


def first_match(regex: re.Pattern[str], value: str) -> str:
    match = regex.search(safe_text(value))
    return match.group(0) if match else ""


def host(url: str) -> str:
    try:
        return urllib.parse.urlsplit(url).netloc
    except Exception:
        return ""


def normalize_words(value: str) -> list[str]:
    return WORD_RE.findall(safe_text(value).lower())


def title_tokens(title: str) -> list[str]:
    return [word for word in normalize_words(title) if len(word) >= 4 and word not in STOPWORDS]


def title_token_coverage(title: str, text: str) -> float:
    tokens = title_tokens(title)
    if not tokens:
        return 0.0
    words = set(normalize_words(text))
    hits = sum(1 for token in tokens if token in words)
    return round(hits / len(tokens), 3)


def source_inputs(sources: pd.DataFrame, identifiers: pd.DataFrame) -> dict[str, dict[str, str]]:
    out: dict[str, dict[str, str]] = {}
    for _, row in sources.iterrows():
        sid = safe_text(row.get("source_id"))
        title = safe_text(row.get("title"))
        out[sid] = {
            "doi": normalize_doi(safe_text(row.get("doi"))),
            "pmid": first_match(PMID_RE, safe_text(row.get("pmid"))),
            "pmcid": "",
            "nct": first_match(NCT_RE, safe_text(row.get("registry_id"))).upper(),
            "title": title,
            "year": safe_text(row.get("publication_year")),
            "source_type": safe_text(row.get("source_type")),
            "urls": [],
        }
        if title.startswith(("http://", "https://")):
            out[sid]["urls"].append(title)
    for _, row in identifiers.iterrows():
        sid = safe_text(row.get("source_id"))
        if sid not in out:
            out[sid] = {"doi": "", "pmid": "", "pmcid": "", "nct": "", "title": "", "year": "", "source_type": "", "urls": []}
        typ = safe_text(row.get("identifier_type")).lower()
        value = safe_text(row.get("identifier_value")) or safe_text(row.get("identifier_url"))
        is_primary = safe_text(row.get("is_primary")).lower() == "true"
        if typ == "url":
            url = safe_text(row.get("identifier_url")) or value
            if url.startswith(("http://", "https://")) and url not in out[sid]["urls"]:
                out[sid]["urls"].append(url)
        if not is_primary:
            continue
        if typ in {"doi", "url"} and not out[sid]["doi"]:
            out[sid]["doi"] = normalize_doi(value)
        elif typ == "pmid" and not out[sid]["pmid"]:
            out[sid]["pmid"] = first_match(PMID_RE, value)
        elif typ == "pmcid" and not out[sid]["pmcid"]:
            out[sid]["pmcid"] = first_match(PMCID_RE, value).upper()
        elif typ == "nct" and not out[sid]["nct"]:
            out[sid]["nct"] = first_match(NCT_RE, value).upper()
    return out


def get_bytes(url: str, accept: str = "*/*") -> dict[str, object]:
    time.sleep(REQUEST_DELAY)
    try:
        with requests.get(
            url,
            headers={"User-Agent": USER_AGENT, "Accept": accept},
            timeout=TIMEOUT,
            allow_redirects=True,
            stream=True,
        ) as response:
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
                "status": response.status_code,
                "final_url": response.url,
                "content_type": response.headers.get("content-type", ""),
                "byte_count": len(content),
                "content": content,
                "truncated": total > MAX_BYTES,
                "error": "",
            }
    except Exception as exc:  # noqa: BLE001
        return {
            "ok": False,
            "status": "",
            "final_url": "",
            "content_type": "",
            "byte_count": 0,
            "content": b"",
            "truncated": False,
            "error": f"{type(exc).__name__}:{exc}",
        }


def fetch_json(url: str) -> tuple[dict | None, str]:
    resp = get_bytes(url, accept="application/json,*/*;q=0.8")
    if not resp["ok"]:
        return None, f"http_{safe_text(resp.get('status')) or 'request_error'}:{safe_text(resp.get('error'))}"
    try:
        content = resp["content"]
        assert isinstance(content, bytes)
        return json.loads(content.decode("utf-8", errors="replace")), "ok"
    except Exception as exc:  # noqa: BLE001
        return None, f"json_parse_failed:{type(exc).__name__}:{exc}"


def run_text_command(args: list[str], timeout: int = 25) -> str:
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
    except Exception:
        return ""
    return proc.stdout or ""


def decode_text(content: bytes) -> str:
    return content[:4_000_000].decode("utf-8", errors="ignore")


def classify_content(content: bytes, content_type: str, url: str) -> tuple[str, str]:
    lower_type = safe_text(content_type).lower()
    lower_url = safe_text(url).lower()
    head = content[:512].lstrip().lower()
    if content[:64].lstrip().startswith(b"%PDF") or "application/pdf" in lower_type or PDF_URL_RE.search(lower_url):
        return "full_article_pdf", ".pdf"
    if head.startswith(b"<?xml") or "xml" in lower_type or lower_url.endswith(".xml"):
        return "full_article_xml", ".xml"
    if b"<html" in head or "html" in lower_type:
        return "full_article_html", ".html"
    return "unknown_candidate", ".bin"


def looks_like_public_direct_url(url: str) -> bool:
    parsed = urllib.parse.urlsplit(url)
    h = parsed.netloc.lower()
    if not h or "doi.org" in h or "clinicaltrials.gov" in h:
        return False
    if "scholar.google" in h or "researchgate.net" in h or "academia.edu" in h:
        return False
    if "pubmed.ncbi.nlm.nih.gov" in h:
        return False
    path = parsed.path.lower()
    return (
        PDF_URL_RE.search(url)
        or path.endswith((".xml", ".html", ".htm"))
        or "osf.io" in h
        or "arxiv.org" in h
        or "biorxiv.org" in h
        or "medrxiv.org" in h
    )


def article_plausibility(byte_class: str, text: str, url: str) -> tuple[bool, str]:
    words = normalize_words(text)
    word_count = len(words)
    lower = text.lower()
    if byte_class == "full_article_pdf":
        return True, "pdf_bytes"
    if byte_class == "full_article_xml":
        if "<article" in lower or "<body" in lower or "<sec" in lower or word_count >= 1800:
            return True, f"xml_article_like_words={word_count}"
        return False, f"xml_too_short_or_metadata_only_words={word_count}"
    if byte_class == "full_article_html":
        has_body_terms = sum(term in lower for term in ["method", "results", "discussion", "references", "abstract"])
        if word_count >= 2500 and has_body_terms >= 3:
            return True, f"html_article_like_words={word_count}"
        return False, f"html_landing_or_too_short_words={word_count}_body_terms={has_body_terms}"
    return False, "unsupported_byte_class"


def pdf_text_from_bytes(content: bytes, suffix_hint: str) -> str:
    tmp = CACHE_DIR / "_tmp_identity" / f"{hashlib.sha256(content).hexdigest()[:16]}{suffix_hint}"
    tmp.parent.mkdir(parents=True, exist_ok=True)
    tmp.write_bytes(content)
    text = run_text_command(["pdftotext", "-f", "1", "-l", "5", "-layout", str(tmp), "-"])
    if not text.strip():
        text = run_text_command(["pdftotext", "-f", "1", "-l", "5", str(tmp), "-"])
    return text[:300_000]


def identity_check(
    source_input: dict[str, str],
    byte_class: str,
    content: bytes,
    content_type: str,
    url: str,
    candidate_doi: str = "",
    relation_to_primary: bool = False,
) -> tuple[str, str, str, float]:
    doi = source_input.get("doi", "")
    title = source_input.get("title", "")
    if byte_class == "full_article_pdf":
        text = pdf_text_from_bytes(content, ".pdf")
    else:
        text = decode_text(content)
    text_dois = set(extract_dois(text))
    url_dois = set(extract_dois(url))
    cov = title_token_coverage(title, text)
    plaus, plaus_reason = article_plausibility(byte_class, text, url)
    if not plaus:
        return "reject_not_full_article_text", plaus_reason, text, cov
    if doi and (doi in text_dois):
        return "accepted_full_article_text", "primary DOI appears in candidate text", text, cov
    if doi and (doi in url_dois) and cov >= 0.48:
        return "accepted_full_article_text", f"primary DOI route and title token coverage {cov}", text, cov
    if doi and normalize_doi(candidate_doi) == doi and cov >= 0.82:
        return "accepted_full_article_text", f"resolver metadata DOI matches primary DOI and title token coverage {cov}", text, cov
    if relation_to_primary and cov >= 0.82:
        return "accepted_full_article_text", f"resolver relation/version route to primary source and title token coverage {cov}", text, cov
    if not doi and cov >= 0.82:
        return "needs_manual_identity_check", f"no primary DOI but strong title token coverage {cov}", text, cov
    if doi and cov >= 0.82:
        return "needs_manual_identity_check", f"title match strong but DOI not found in candidate text; coverage {cov}", text, cov
    if doi and text_dois and doi not in text_dois:
        return "reject_wrong_doi", f"candidate text DOI(s) {sorted(text_dois)[:4]} do not include primary DOI {doi}", text, cov
    return "needs_manual_identity_check", f"insufficient identity signal; coverage {cov}; text_dois={sorted(text_dois)[:4]}", text, cov


def write_artifact(result_id: str, route: str, byte_class: str, extension: str, content: bytes) -> tuple[str, str]:
    sha = sha256_bytes(content)
    safe_route = re.sub(r"[^A-Za-z0-9._-]+", "_", route).strip("_").lower()
    path = CACHE_DIR / f"{result_id}__{safe_route}__{stable_id('art', sha)[4:16]}{extension}"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    return rel(path), sha


def route_to_strategy(route: str) -> str:
    lower = route.lower()
    if lower.startswith("crossref"):
        return "crossref_metadata"
    if lower.startswith("core"):
        return "preprint_repository_candidate"
    if lower.startswith("europepmc"):
        return "europepmc_metadata"
    if lower.startswith("openaire"):
        return "oa_candidate_url"
    if lower.startswith("openalex"):
        return "openalex_metadata"
    if lower.startswith("hal"):
        return "preprint_repository_candidate"
    if lower.startswith("arxiv") or lower.startswith("biorxiv") or lower.startswith("medrxiv") or lower.startswith("osf"):
        return "preprint_repository_candidate"
    if lower.startswith("wayback"):
        return "stable_url"
    if lower.startswith("direct"):
        return "stable_url"
    return "oa_candidate_url"


def failure_from_response(resp: dict[str, object], byte_class: str, identity_decision: str) -> str:
    if identity_decision.startswith("accepted"):
        return "full_article_text_obtained"
    if safe_text(resp.get("error")):
        return "request_error"
    status = safe_text(resp.get("status"))
    if status in {"401", "402", "403"}:
        return f"http_{status}_blocked"
    if status == "404":
        return "http_404"
    if status == "429":
        return "http_429_rate_limited"
    content = resp.get("content", b"")
    lower = content[:200_000].decode("utf-8", errors="ignore").lower() if isinstance(content, bytes) else ""
    if "captcha" in lower or "cloudflare" in lower or "verify you are human" in lower:
        return "captcha_or_bot_block"
    if "login" in lower or "subscribe" in lower or "institution" in lower:
        return "login_or_paywall_html"
    if byte_class == "full_article_html":
        return "html_not_full_article"
    if byte_class == "unknown_candidate":
        return "unknown_or_non_article_bytes"
    return "identity_or_plausibility_failed"


def europepmc_candidates(source_input: dict[str, str]) -> list[dict[str, str]]:
    urls = []
    pmcid = source_input.get("pmcid", "")
    doi = source_input.get("doi", "")
    if pmcid:
        urls.append({"route": "europepmc_fulltext_xml", "url": f"https://www.ebi.ac.uk/europepmc/webservices/rest/{pmcid}/fullTextXML", "api_url": "", "record_id": pmcid})
    if doi:
        query = urllib.parse.quote(f'DOI:"{doi}"')
        api = f"https://www.ebi.ac.uk/europepmc/webservices/rest/search?query={query}&format=json&resultType=core"
        data, status = fetch_json(api)
        if data:
            for result in ((data.get("resultList") or {}).get("result") or [])[:3]:
                rid = safe_text(result.get("pmcid") or result.get("id"))
                if result.get("pmcid"):
                    urls.append({"route": "europepmc_fulltext_xml", "url": f"https://www.ebi.ac.uk/europepmc/webservices/rest/{rid}/fullTextXML", "api_url": api, "record_id": rid})
                for item in ((result.get("fullTextUrlList") or {}).get("fullTextUrl") or []):
                    candidate = safe_text(item.get("url"))
                    if candidate and candidate not in [u["url"] for u in urls]:
                        urls.append({"route": "europepmc_fulltext_url", "url": candidate, "api_url": api, "record_id": rid})
    return urls


def crossref_candidates(source_input: dict[str, str]) -> list[dict[str, str]]:
    doi = source_input.get("doi", "")
    if not doi:
        return []
    safe = urllib.parse.quote(doi, safe="/:._;()-")
    api = f"https://api.crossref.org/works/{safe}"
    if CONTACT_EMAIL:
        api += f"?mailto={urllib.parse.quote(CONTACT_EMAIL)}"
    data, status = fetch_json(api)
    urls = []
    if not data:
        return []
    for link in ((data.get("message") or {}).get("link") or []):
        candidate = safe_text(link.get("URL"))
        if not candidate:
            continue
        ctype = safe_text(link.get("content-type")).lower()
        app = safe_text(link.get("intended-application")).lower()
        if "pdf" in ctype or "xml" in ctype or "html" in ctype or app == "text-mining" or PDF_URL_RE.search(candidate):
            urls.append({"route": "crossref_fulltext_link", "url": candidate, "api_url": api, "record_id": doi})
    relation = (data.get("message") or {}).get("relation") or {}
    relation_keys = {
        "has-preprint",
        "is-preprint-of",
        "has-version",
        "is-version-of",
        "is-identical-to",
        "has-supplement",
        "is-supplement-to",
    }
    for rel_type, rel_items in relation.items():
        if rel_type not in relation_keys:
            continue
        for rel in rel_items or []:
            rel_doi = normalize_doi(safe_text(rel.get("id") or rel.get("DOI")))
            if not rel_doi or rel_doi == doi:
                continue
            urls.append(
                {
                    "route": "crossref_relation_doi",
                    "url": "https://doi.org/" + rel_doi,
                    "api_url": api,
                    "record_id": doi,
                    "candidate_doi": rel_doi,
                    "relation_to_primary": "true",
                    "candidate_relation_type": rel_type,
                }
            )
    return urls


def openaire_candidates(source_input: dict[str, str]) -> list[dict[str, str]]:
    if not ENABLE_OPENAIRE:
        return []
    doi = source_input.get("doi", "")
    title = source_input.get("title", "")
    api = ""
    if doi:
        api = f"https://api.openaire.eu/graph/v1/researchProducts?pid={urllib.parse.quote(doi, safe='/:._;()-')}"
    elif title:
        api = f"https://api.openaire.eu/graph/v1/researchProducts?type=publication&search={urllib.parse.quote(title)}"
    if not api:
        return []
    data, status = fetch_json(api)
    urls = []
    if not data:
        return []
    for result in (data.get("results") or [])[:3]:
        rid = safe_text(result.get("id"))
        for inst in result.get("instances") or []:
            inst_dois = {normalize_doi(pid.get("value", "")) for pid in (inst.get("pids") or []) if safe_text(pid.get("scheme")).lower() == "doi"}
            inst_dois |= {normalize_doi(pid.get("value", "")) for pid in (inst.get("alternateIdentifiers") or []) if safe_text(pid.get("scheme")).lower() == "doi"}
            for candidate in inst.get("urls") or []:
                candidate = safe_text(candidate)
                if not candidate or "doi.org/" in candidate.lower() or candidate.startswith("http://dx.doi.org"):
                    continue
                # Prefer likely direct full text first; repository pages are still attempted but rarely promote.
                urls.append({"route": "openaire_instance_url", "url": candidate, "api_url": api, "record_id": rid, "candidate_doi": next(iter(inst_dois), "")})
    dedup = []
    seen = set()
    for item in urls:
        if item["url"] in seen:
            continue
        seen.add(item["url"])
        dedup.append(item)
    return dedup


def openalex_candidates(source_input: dict[str, str]) -> list[dict[str, str]]:
    doi = source_input.get("doi", "")
    title = source_input.get("title", "")
    if doi:
        work_id = "https://doi.org/" + doi
        api_base = "https://api.openalex.org/works/" + urllib.parse.quote(work_id, safe="")
        params = {"select": "id,doi,title,open_access,primary_location,best_oa_location,locations"}
    elif title and not title.startswith(("http://", "https://")):
        api_base = "https://api.openalex.org/works"
        params = {
            "search": title,
            "per-page": "3",
            "select": "id,doi,title,open_access,primary_location,best_oa_location,locations",
        }
    else:
        return []
    if CONTACT_EMAIL:
        params["mailto"] = CONTACT_EMAIL
    api = api_base + "?" + urllib.parse.urlencode(params)
    data, status = fetch_json(api)
    if not data:
        return []
    urls = []

    def add_location(loc: dict, route: str, record_id: str, record_doi: str, record_title: str, relation: bool) -> None:
        if not isinstance(loc, dict):
            return
        for key in ["pdf_url", "landing_page_url"]:
            candidate = safe_text(loc.get(key))
            if candidate and not candidate.lower().startswith("https://doi.org/"):
                urls.append(
                    {
                        "route": route,
                        "url": candidate,
                        "api_url": api,
                        "record_id": record_id,
                        "candidate_doi": record_doi or doi,
                        "candidate_title": record_title,
                        "relation_to_primary": str(relation).lower(),
                        "candidate_relation_type": "openalex_title_or_doi_match",
                    }
                )

    records = [data] if "results" not in data else data.get("results") or []
    for rec in records[:3]:
        rec_title = safe_text(rec.get("title"))
        rec_doi = normalize_doi(safe_text(rec.get("doi")))
        relation = bool((doi and rec_doi == doi) or (not doi and title_token_coverage(title, rec_title) >= 0.75))
        if not relation and not doi:
            continue
        add_location(rec.get("best_oa_location") or {}, "openalex_location_url", safe_text(rec.get("id")), rec_doi, rec_title, relation)
        add_location(rec.get("primary_location") or {}, "openalex_location_url", safe_text(rec.get("id")), rec_doi, rec_title, relation)
        for loc in (rec.get("locations") or [])[:8]:
            add_location(loc, "openalex_location_url", safe_text(rec.get("id")), rec_doi, rec_title, relation)
    dedup, seen = [], set()
    for item in urls:
        if item["url"] in seen:
            continue
        seen.add(item["url"])
        dedup.append(item)
    return dedup


def core_json(url: str, params: dict[str, str] | None = None) -> tuple[dict | None, str]:
    if not ENABLE_CORE:
        return None, "core_disabled_or_missing_key"
    time.sleep(REQUEST_DELAY)
    try:
        response = requests.get(
            url,
            params=params or {},
            headers={"User-Agent": USER_AGENT, "Authorization": f"Bearer {CORE_API_KEY}"},
            timeout=TIMEOUT,
        )
    except Exception as exc:  # noqa: BLE001
        return None, f"request_error:{type(exc).__name__}:{exc}"
    if not (200 <= response.status_code < 300):
        return None, f"http_{response.status_code}"
    try:
        return response.json(), "ok"
    except Exception as exc:  # noqa: BLE001
        return None, f"json_parse_failed:{type(exc).__name__}:{exc}"


def core_candidates(source_input: dict[str, str]) -> list[dict[str, str]]:
    if not ENABLE_CORE:
        return []
    doi = source_input.get("doi", "")
    title = source_input.get("title", "")
    queries = []
    if doi:
        queries.append(f'doi:"{doi}"')
    if title and not title.startswith(("http://", "https://")):
        queries.append(f'title:"{title}"')
        queries.append(title)
    urls = []
    seen_work_ids = set()
    for query in queries[:3]:
        search_url = "https://api.core.ac.uk/v3/search/works"
        data, status = core_json(search_url, {"q": query, "limit": "3"})
        for work in (data or {}).get("results") or []:
            work_id = safe_text(work.get("id"))
            if work_id in seen_work_ids:
                continue
            seen_work_ids.add(work_id)
            work_doi = normalize_doi(safe_text(work.get("doi"))) or doi
            work_title = safe_text(work.get("title"))
            relation = bool((doi and work_doi == doi) or (not doi and title_token_coverage(title, work_title) >= 0.75))
            if not relation:
                continue
            candidate_urls = []
            for key in ["downloadUrl"]:
                candidate_urls.append(safe_text(work.get(key)))
            candidate_urls.extend(safe_text(u) for u in work.get("sourceFulltextUrls") or [])
            # Output records often contain richer repository URLs than the work record.
            for output_url in (work.get("outputs") or [])[:3]:
                output_data, _ = core_json(safe_text(output_url))
                if not output_data:
                    continue
                output_doi = normalize_doi(safe_text(output_data.get("doi"))) or work_doi
                output_title = safe_text(output_data.get("title")) or work_title
                output_relation = bool((doi and output_doi == doi) or (not doi and title_token_coverage(title, output_title) >= 0.75))
                if not output_relation:
                    continue
                candidate_urls.append(safe_text(output_data.get("downloadUrl")))
                candidate_urls.extend(safe_text(u) for u in output_data.get("sourceFulltextUrls") or [])
                candidate_urls.extend(safe_text(u) for u in output_data.get("urls") or [])
            for candidate in candidate_urls:
                candidate = safe_text(candidate)
                if not candidate.startswith(("http://", "https://")):
                    continue
                lower = candidate.lower()
                if "doi.org/" in lower or "dx.doi.org/" in lower or "core.ac.uk/works/" in lower or "core.ac.uk/outputs/" in lower:
                    continue
                urls.append(
                    {
                        "route": "core_fulltext_url",
                        "url": candidate,
                        "api_url": search_url,
                        "record_id": work_id,
                        "candidate_doi": work_doi,
                        "candidate_title": work_title,
                        "relation_to_primary": str(relation).lower(),
                        "candidate_relation_type": "core_work_or_output_match",
                    }
                )
    dedup, seen = [], set()
    for item in urls:
        if item["url"] in seen:
            continue
        seen.add(item["url"])
        dedup.append(item)
    return dedup


def semantic_scholar_candidates(source_input: dict[str, str]) -> list[dict[str, str]]:
    doi = source_input.get("doi", "")
    title = source_input.get("title", "")
    if doi:
        api = (
            "https://api.semanticscholar.org/graph/v1/paper/"
            + urllib.parse.quote("DOI:" + doi, safe="")
            + "?fields=externalIds,title,year,openAccessPdf"
        )
    elif title and not title.startswith(("http://", "https://")):
        api = (
            "https://api.semanticscholar.org/graph/v1/paper/search/match?"
            + urllib.parse.urlencode({"query": title, "fields": "externalIds,title,year,openAccessPdf"})
        )
    else:
        return []
    data, status = fetch_json(api)
    records = []
    if data and isinstance(data.get("data"), list):
        records = data.get("data") or []
    elif data and data.get("paperId"):
        records = [data]
    urls = []
    for rec in records[:3]:
        rec_title = safe_text(rec.get("title"))
        rec_doi = normalize_doi(safe_text((rec.get("externalIds") or {}).get("DOI"))) or doi
        relation = bool((doi and rec_doi == doi) or (not doi and title_token_coverage(title, rec_title) >= 0.75))
        if not relation:
            continue
        oa = rec.get("openAccessPdf") or {}
        candidate = safe_text(oa.get("url"))
        if candidate:
            urls.append(
                {
                    "route": "semantic_scholar_openaccess_pdf",
                    "url": candidate,
                    "api_url": api,
                    "record_id": safe_text(rec.get("paperId")),
                    "candidate_doi": rec_doi,
                    "candidate_title": rec_title,
                    "relation_to_primary": str(relation).lower(),
                    "candidate_relation_type": "semantic_scholar_open_access_pdf",
                }
            )
    return urls


def hal_candidates(source_input: dict[str, str]) -> list[dict[str, str]]:
    doi = source_input.get("doi", "")
    title = source_input.get("title", "")
    if doi:
        q = f'doiId_s:"{doi}"'
    elif title:
        q = f'title_t:"{title}"'
    else:
        return []
    api = (
        "https://api.archives-ouvertes.fr/search/?"
        + urllib.parse.urlencode(
            {
                "q": q,
                "fl": "halId_s,fileMain_s,uri_s,doiId_s,title_s,authFullName_s,producedDateY_i",
                "wt": "json",
                "rows": "5",
            }
        )
    )
    data, status = fetch_json(api)
    urls = []
    docs = ((data or {}).get("response") or {}).get("docs") or []
    for doc in docs:
        candidate = safe_text(doc.get("fileMain_s"))
        if not candidate:
            continue
        urls.append(
            {
                "route": "hal_file_main",
                "url": candidate,
                "api_url": api,
                "record_id": safe_text(doc.get("halId_s")),
                "candidate_doi": normalize_doi(safe_text(doc.get("doiId_s"))) or doi,
            }
        )
    return urls


def arxiv_candidates(source_input: dict[str, str]) -> list[dict[str, str]]:
    doi = source_input.get("doi", "")
    title = source_input.get("title", "")
    if doi:
        query = f'doi:"{doi}"'
    elif title:
        query = f'ti:"{title}"'
    else:
        return []
    api = "https://export.arxiv.org/api/query?" + urllib.parse.urlencode({"search_query": query, "max_results": "3"})
    time.sleep(max(REQUEST_DELAY, 0.35))
    try:
        resp = requests.get(api, headers={"User-Agent": USER_AGENT}, timeout=TIMEOUT)
    except Exception:
        return []
    if not (200 <= resp.status_code < 300):
        return []
    root = ElementTree.fromstring(resp.content)
    ns = {"atom": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}
    urls = []
    for entry in root.findall("atom:entry", ns):
        arxiv_id = safe_text(entry.findtext("atom:id", default="", namespaces=ns)).rsplit("/", 1)[-1]
        entry_doi = normalize_doi(entry.findtext("arxiv:doi", default="", namespaces=ns))
        relation = bool(doi and entry_doi and entry_doi == doi)
        for link in entry.findall("atom:link", ns):
            if safe_text(link.attrib.get("type")) == "application/pdf":
                urls.append(
                    {
                        "route": "arxiv_pdf",
                        "url": safe_text(link.attrib.get("href")),
                        "api_url": api,
                        "record_id": arxiv_id,
                        "candidate_doi": entry_doi or doi,
                        "relation_to_primary": str(relation).lower(),
                        "candidate_relation_type": "preprint_or_version",
                    }
                )
    return urls


def biorxiv_medrxiv_candidates(source_input: dict[str, str]) -> list[dict[str, str]]:
    doi = source_input.get("doi", "")
    if not doi:
        return []
    urls = []
    for server in ["biorxiv", "medrxiv"]:
        api = f"https://api.biorxiv.org/pubs/{server}/{urllib.parse.quote(doi, safe='')}"
        data, status = fetch_json(api)
        for rec in (data or {}).get("collection") or []:
            preprint_doi = normalize_doi(safe_text(rec.get("preprint_doi") or rec.get("doi")))
            if not preprint_doi:
                continue
            version = safe_text(rec.get("preprint_version") or rec.get("version") or "1").lstrip("v") or "1"
            base = f"https://www.{server}.org/content/{preprint_doi}v{version}"
            urls.append(
                {
                    "route": f"{server}_preprint_pdf",
                    "url": base + ".full.pdf",
                    "api_url": api,
                    "record_id": preprint_doi,
                    "candidate_doi": preprint_doi,
                    "relation_to_primary": "true",
                    "candidate_relation_type": "preprint_of_primary",
                }
            )
            urls.append(
                {
                    "route": f"{server}_preprint_xml",
                    "url": base + ".source.xml",
                    "api_url": api,
                    "record_id": preprint_doi,
                    "candidate_doi": preprint_doi,
                    "relation_to_primary": "true",
                    "candidate_relation_type": "preprint_of_primary",
                }
            )
    return urls


def osf_guid_from_url(url: str) -> str:
    parsed = urllib.parse.urlsplit(url)
    if "osf.io" not in parsed.netloc.lower():
        return ""
    parts = [p for p in parsed.path.split("/") if p]
    if not parts:
        return ""
    guid = parts[0]
    return guid if re.fullmatch(r"[a-z0-9]{5}", guid, flags=re.I) else ""


def osf_file_candidates_for_guid(guid: str, source_input: dict[str, str], api_source: str = "", candidate_title: str = "") -> list[dict[str, str]]:
    if not guid:
        return []
    out = []
    queue = [f"https://api.osf.io/v2/nodes/{guid}/files/osfstorage/"]
    seen = set()
    while queue and len(out) < 8:
        api = queue.pop(0)
        if api in seen:
            continue
        seen.add(api)
        data, status = fetch_json(api)
        for item in (data or {}).get("data") or []:
            attrs = item.get("attributes") or {}
            links = item.get("links") or {}
            name = safe_text(attrs.get("name"))
            kind = safe_text(attrs.get("kind"))
            if kind == "folder":
                related = (((item.get("relationships") or {}).get("files") or {}).get("links") or {}).get("related") or {}
                href = safe_text(related.get("href"))
                if href:
                    queue.append(href)
                continue
            download = safe_text(links.get("download"))
            if not download:
                continue
            lower_name = name.lower()
            if not lower_name.endswith((".pdf", ".html", ".htm", ".xml")):
                continue
            out.append(
                {
                    "route": "osf_file_download",
                    "url": download,
                    "api_url": api_source or api,
                    "record_id": safe_text(item.get("id")),
                    "candidate_doi": source_input.get("doi", ""),
                    "candidate_title": candidate_title,
                    "relation_to_primary": "true",
                    "candidate_relation_type": "osf_project_file",
                }
            )
        next_url = safe_text(((data or {}).get("links") or {}).get("next"))
        if next_url:
            queue.append(next_url)
    return out


def osf_candidates(source_input: dict[str, str]) -> list[dict[str, str]]:
    urls = []
    for url in source_input.get("urls", []) or []:
        guid = osf_guid_from_url(safe_text(url))
        if guid:
            node_data, _ = fetch_json(f"https://api.osf.io/v2/nodes/{guid}/")
            node_title = safe_text((((node_data or {}).get("data") or {}).get("attributes") or {}).get("title"))
            urls.extend(osf_file_candidates_for_guid(guid, source_input, url, node_title))
    # OSF search is noisy, so only use it when there is no DOI route or the title itself names an OSF record.
    title = source_input.get("title", "")
    if title and (not source_input.get("doi") or "osf.io" in title.lower() or "replication" in title.lower()):
        api = "https://api.osf.io/v2/search/?" + urllib.parse.urlencode({"q": title, "page[size]": "3"})
        data, status = fetch_json(api)
        for item in (data or {}).get("data") or []:
            if not isinstance(item, dict):
                continue
            typ = safe_text(item.get("type"))
            if typ not in {"nodes", "registrations"}:
                continue
            guid = safe_text(item.get("id"))
            item_title = safe_text((item.get("attributes") or {}).get("title"))
            urls.extend(osf_file_candidates_for_guid(guid, source_input, api, item_title))
    dedup, seen = [], set()
    for item in urls:
        if item["url"] in seen:
            continue
        seen.add(item["url"])
        dedup.append(item)
    return dedup


def direct_url_candidates(source_input: dict[str, str]) -> list[dict[str, str]]:
    urls = []
    for url in source_input.get("urls", []) or []:
        url = safe_text(url)
        if not looks_like_public_direct_url(url) or osf_guid_from_url(url):
            continue
        urls.append(
            {
                "route": "direct_source_url",
                "url": url,
                "api_url": "",
                "record_id": "",
                "candidate_doi": source_input.get("doi", ""),
                "candidate_relation_type": "direct_identifier_url",
            }
        )
    return urls


def wayback_candidates(result_id: str, source_input: dict[str, str], candidate_ledger: pd.DataFrame) -> list[dict[str, str]]:
    if not ENABLE_WAYBACK or candidate_ledger.empty:
        return []
    subset = candidate_ledger[
        candidate_ledger["result_id"].eq(result_id)
        & candidate_ledger["candidate_url"].str.startswith(("http://", "https://"), na=False)
        & candidate_ledger["failure_code"].isin(["http_403_blocked", "http_404", "http_404:", "login_or_paywall_html", "html_not_pdf", "captcha_or_bot_block"])
    ].copy()
    urls = []
    for candidate_url in subset["candidate_url"].drop_duplicates().head(3):
        cdx = "https://web.archive.org/cdx/search/cdx?" + urllib.parse.urlencode(
            {
                "url": candidate_url,
                "output": "json",
                "filter": "statuscode:200",
                "collapse": "digest",
                "fl": "timestamp,original,mimetype,statuscode,digest,length",
                "limit": "5",
            }
        )
        data, status = fetch_json(cdx)
        if not data or len(data) < 2:
            continue
        headers = data[0]
        for row in data[1:]:
            rec = dict(zip(headers, row))
            mimetype = safe_text(rec.get("mimetype")).lower()
            original = safe_text(rec.get("original")) or candidate_url
            if "pdf" not in mimetype and "html" not in mimetype and not PDF_URL_RE.search(original):
                continue
            ts = safe_text(rec.get("timestamp"))
            archive_url = f"https://web.archive.org/web/{ts}id_/{original}"
            route = "wayback_cdx_pdf" if "pdf" in mimetype or PDF_URL_RE.search(original) else "wayback_cdx_html"
            urls.append({"route": route, "url": archive_url, "api_url": cdx, "record_id": ts, "candidate_doi": source_input.get("doi", "")})
            break
    return urls


def attempt_candidate(row: pd.Series, source_input: dict[str, str], candidate: dict[str, str]) -> dict[str, object]:
    route = candidate["route"]
    url = candidate["url"]
    accept = "application/pdf,application/xml,text/xml,text/html,*/*;q=0.8"
    resp = get_bytes(url, accept=accept)
    content = resp.get("content", b"")
    assert isinstance(content, bytes)
    byte_class, extension = classify_content(content, safe_text(resp.get("content_type")), safe_text(resp.get("final_url") or url))
    identity_decision = ""
    identity_reason = ""
    text = ""
    title_cov = 0.0
    local_path = ""
    sha = ""
    if resp.get("ok") and content:
        check_input = dict(source_input)
        candidate_title = safe_text(candidate.get("candidate_title"))
        if candidate_title and (not safe_text(check_input.get("title")) or safe_text(check_input.get("title")).startswith(("http://", "https://"))):
            check_input["title"] = candidate_title
        identity_decision, identity_reason, text, title_cov = identity_check(
            check_input,
            byte_class,
            content,
            safe_text(resp.get("content_type")),
            safe_text(resp.get("final_url") or url),
            normalize_doi(safe_text(candidate.get("candidate_doi"))),
            safe_text(candidate.get("relation_to_primary")).lower() == "true",
        )
        if identity_decision == "accepted_full_article_text":
            local_path, sha = write_artifact(row["source_result_id"], route, byte_class, extension, content)
        else:
            sha = sha256_bytes(content) if content else ""
    failure = failure_from_response(resp, byte_class, identity_decision)
    return {
        "source_result_id": row["source_result_id"],
        "represented_source_id": row["represented_source_id"],
        "route": route,
        "route_family": route.split("_", 1)[0],
        "api_url": safe_text(candidate.get("api_url")),
        "api_record_id": safe_text(candidate.get("record_id")),
        "candidate_url": url,
        "final_url": safe_text(resp.get("final_url")),
        "http_status": safe_text(resp.get("status")),
        "content_type": safe_text(resp.get("content_type")),
        "byte_count": safe_text(resp.get("byte_count")),
        "source_byte_class": byte_class,
        "local_path": local_path,
        "sha256": sha,
        "identity_decision": identity_decision or "not_accepted",
        "identity_reason": identity_reason,
        "title_token_coverage": title_cov,
        "candidate_doi": normalize_doi(safe_text(candidate.get("candidate_doi")) or url),
        "candidate_relation_type": safe_text(candidate.get("candidate_relation_type")),
        "candidate_title": safe_text(candidate.get("candidate_title")),
        "primary_doi": source_input.get("doi", ""),
        "failure_code": failure,
        "download_attempted": "true",
    }


def candidate_ledger_row(attempt: dict[str, object], source_input: dict[str, str], created_at: str) -> dict[str, object]:
    accepted = safe_text(attempt["identity_decision"]) == "accepted_full_article_text"
    object_guess = safe_text(attempt["source_byte_class"])
    if object_guess == "unknown_candidate":
        failure = safe_text(attempt["failure_code"])
        if "403" in failure or "blocked" in failure:
            object_guess = "blocked_page"
        elif "paywall" in failure or "login" in failure:
            object_guess = "paywall_or_login_page"
        elif "404" in failure:
            object_guess = "missing_url"
    if accepted:
        evidence = "level5_candidate_full_article"
    elif safe_text(attempt["identity_decision"]).startswith("reject"):
        evidence = "reject_no_promotion"
    else:
        evidence = "no_promotion"
    return {
        "candidate_id": stable_id("cand", attempt["source_result_id"], attempt["route"], attempt["candidate_url"], attempt["sha256"]),
        "result_id": attempt["source_result_id"],
        "represented_source_id": attempt["represented_source_id"],
        "route_module": attempt["route"],
        "route_family": attempt["route_family"],
        "input_primary_doi": source_input.get("doi", ""),
        "input_pmid": source_input.get("pmid", ""),
        "input_pmcid": source_input.get("pmcid", ""),
        "input_nct": source_input.get("nct", ""),
        "input_title": source_input.get("title", ""),
        "input_first_author": "",
        "input_year": source_input.get("year", ""),
        "query_used": source_input.get("doi") or source_input.get("title", ""),
        "api_url": attempt["api_url"],
        "api_record_id": attempt["api_record_id"],
        "api_record_json_path": "",
        "candidate_url": attempt["candidate_url"],
        "candidate_final_url": attempt["final_url"],
        "candidate_repository": host(safe_text(attempt["final_url"]) or safe_text(attempt["candidate_url"])),
        "candidate_object_type_guess": object_guess,
        "candidate_relation_type": safe_text(attempt.get("candidate_relation_type")) or "primary_identifier_or_repository_route",
        "candidate_doi": attempt["candidate_doi"],
        "candidate_pmid": "",
        "candidate_pmcid": "",
        "candidate_title": safe_text(attempt.get("candidate_title")),
        "candidate_authors": "",
        "candidate_year": "",
        "candidate_license": "",
        "candidate_access_status": attempt["failure_code"],
        "download_attempted": "true",
        "http_status": attempt["http_status"],
        "mime_type": attempt["content_type"],
        "content_length": attempt["byte_count"],
        "local_path": attempt["local_path"],
        "sha256": attempt["sha256"],
        "extracted_text_path": "",
        "doi_in_candidate_text": str("primary DOI appears" in safe_text(attempt["identity_reason"])).lower(),
        "pmid_in_candidate_text": "",
        "pmcid_in_candidate_text": "",
        "title_similarity": safe_text(attempt["title_token_coverage"]),
        "author_year_match": "",
        "identity_decision": attempt["identity_decision"],
        "identity_reason": attempt["identity_reason"],
        "evidence_scale_candidate": evidence,
        "failure_code": attempt["failure_code"],
        "failure_detail": attempt["identity_reason"],
        "created_at": created_at,
    }


def promote_accepted(attempts: list[dict[str, object]], source_result: pd.DataFrame, source_file: pd.DataFrame, source_access: pd.DataFrame, source_access_attempt: pd.DataFrame, source_access_right: pd.DataFrame, source_version: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    accepted = [item for item in attempts if item["identity_decision"] == "accepted_full_article_text" and item["local_path"]]
    if not accepted:
        return source_result, source_file, source_access, source_access_attempt, source_access_right, pd.DataFrame()
    now = datetime.now(timezone.utc).isoformat()
    ver_by_source = {
        safe_text(row["source_id"]): safe_text(row["source_version_id"])
        for _, row in source_version.iterrows()
        if safe_text(row.get("source_id")) and safe_text(row.get("source_version_id"))
    }
    access_rows, attempt_rows, file_rows, rights_rows, promo_rows = [], [], [], [], []
    for item in accepted:
        result_id = safe_text(item["source_result_id"])
        source_id = safe_text(item["represented_source_id"])
        sha = safe_text(item["sha256"])
        access_id = stable_id("acc", "full_article_text", source_id, sha)
        attempt_id = stable_id("att", "full_article_text", result_id, source_id, sha)
        file_id = stable_id("file", "full_article_text", source_id, sha)
        right_id = stable_id("right", "full_article_text", source_id, file_id)
        group_id = stable_id("ag", "full_article_text", source_id)
        local_path = safe_text(item["local_path"])
        filename = Path(local_path).name
        strategy = route_to_strategy(safe_text(item["route"]))
        access_rows.append(
            {
                "access_id": access_id,
                "source_id": source_id,
                "access_role": "mirrored_file",
                "remote_url": item["candidate_url"],
                "api_url": item["api_url"],
                "final_url": item["final_url"],
                "http_status": item["http_status"],
                "redirect_chain": "",
                "host": host(safe_text(item["final_url"]) or safe_text(item["candidate_url"])),
                "local_path": local_path,
                "file_member_path": "",
                "content_type": item["content_type"],
                "file_sha256": sha,
                "file_size_bytes": item["byte_count"],
                "retrieved_at": now,
                "retrieved_by": "codex",
                "retrieval_method": "automated_download",
                "access_status": "local_file_found",
                "access_strategy": strategy,
                "source_byte_class": item["source_byte_class"],
                "level5_eligible": "true",
                "license_url": "",
                "license_category": "unknown",
                "storage_allowed": "true",
                "source_version": "unknown",
                "retrieval_policy_notes": "Local internal artifact only; do not redistribute full document.",
                "abstract_or_detail_text": "",
                "abstract_or_detail_source_url": "",
                "paywall_or_login_seen": "false",
                "captcha_or_bot_block_seen": "false",
                "preprint_or_repository_candidate": str(safe_text(item["route"]).startswith("openaire")).lower(),
                "access_barrier": "",
                "access_notes": f"Promoted by full article text acquisition: {item['identity_reason']}",
            }
        )
        attempt_rows.append(
            {
                "attempt_id": attempt_id,
                "source_id": source_id,
                "access_id": access_id,
                "attempt_group_id": group_id,
                "attempt_order": "1",
                "resolver_name": "full_article_text_acquisition",
                "resolver_version": "pilot_repository_archive_v1",
                "resolver_strategy": strategy,
                "candidate_rank": "1",
                "candidate_rank_reason": "Identity-accepted full article text candidate.",
                "candidate_url": item["candidate_url"],
                "candidate_url_source": item["route"],
                "final_url": item["final_url"],
                "host": host(safe_text(item["final_url"]) or safe_text(item["candidate_url"])),
                "method": "GET",
                "http_status": item["http_status"],
                "redirect_chain": "",
                "cache_key": stable_id("cache", item["candidate_url"], sha),
                "cache_hit_yn": "false",
                "retry_count": "0",
                "retry_after_seconds": "",
                "content_type_header": item["content_type"],
                "content_type_sniffed": item["source_byte_class"],
                "byte_count": item["byte_count"],
                "sha256": sha,
                "local_path": local_path,
                "source_byte_class": item["source_byte_class"],
                "access_status": "local_file_found",
                "access_barrier": "",
                "abstract_or_detail_text": "",
                "paywall_or_login_seen": "false",
                "captcha_or_bot_block_seen": "false",
                "preprint_or_repository_candidate": str(safe_text(item["route"]).startswith("openaire")).lower(),
                "license_url": "",
                "license_category": "unknown",
                "storage_allowed": "true",
                "robots_status": "not_checked",
                "tdm_policy_status": "unknown",
                "title_match_score": item["title_token_coverage"],
                "doi_match_score": "1.0" if "primary DOI" in safe_text(item["identity_reason"]) else "",
                "author_year_match_score": "",
                "identity_decision": "accepted_full_article_text",
                "identity_decision_reason": item["identity_reason"],
                "retrieval_method": "automated_download",
                "retrieved_at": now,
                "retrieved_by": "codex",
                "decision": "source_object_mirrored",
                "decision_reason": "Identity-accepted full article text mirrored locally.",
                "stop_reason": "success",
                "next_action": "parse_or_verify",
                "notes": "Generated by full article text resolver pass.",
            }
        )
        file_rows.append(
            {
                "source_file_id": file_id,
                "source_id": source_id,
                "access_id": access_id,
                "attempt_id": attempt_id,
                "source_version_id": ver_by_source.get(source_id, ""),
                "file_role": "full_article",
                "file_origin": "automated_download",
                "source_byte_class": item["source_byte_class"],
                "url": item["candidate_url"],
                "final_url": item["final_url"],
                "storage_uri": local_path,
                "local_path": local_path,
                "filename_original": filename,
                "filename_normalized": filename,
                "media_type_reported": item["content_type"],
                "media_type_sniffed": item["source_byte_class"],
                "byte_size": item["byte_count"],
                "sha256": sha,
                "provider_checksum_type": "",
                "provider_checksum_value": "",
                "content_fingerprint": "",
                "text_sha256": "",
                "archive_member_path": "",
                "parent_file_id": "",
                "page_count": "",
                "word_count": "",
                "extraction_ready_yn": "true",
                "level5_eligible": "true",
                "created_at": now,
                "fixity_checked_at": now,
                "notes": f"Identity-accepted full article text for {result_id}; {item['identity_reason']}",
            }
        )
        rights_rows.append(
            {
                "access_right_id": right_id,
                "source_id": source_id,
                "source_file_id": file_id,
                "rights_scope": "source_file",
                "license_name": "",
                "license_spdx": "",
                "license_url": "",
                "license_category": "unknown",
                "terms_url": "",
                "tdm_policy_url": "",
                "robots_status": "not_checked",
                "mirror_allowed_yn": "true",
                "text_extract_allowed_yn": "true",
                "redistribution_allowed_yn": "false",
                "share_scope": "internal_only",
                "institutional_license_yn": "false",
                "reviewed_by": "codex",
                "reviewed_at": now,
                "rights_decision": "internal_only",
                "rights_decision_reason": "Project policy: keep local bytes out of git; publish only routes/checksums and short evidence windows, not full documents.",
            }
        )
        promo_rows.append({"source_result_id": result_id, "access_id": access_id, "source_file_id": file_id, "sha256": sha, "local_path": local_path, "route": item["route"]})
    # idempotent remove by IDs.
    source_access = source_access[~source_access["access_id"].isin({r["access_id"] for r in access_rows})]
    source_access_attempt = source_access_attempt[~source_access_attempt["attempt_id"].isin({r["attempt_id"] for r in attempt_rows})]
    source_file = source_file[~source_file["source_file_id"].isin({r["source_file_id"] for r in file_rows})]
    source_access_right = source_access_right[~source_access_right["access_right_id"].isin({r["access_right_id"] for r in rights_rows})]
    source_access = pd.concat([source_access, pd.DataFrame(access_rows, columns=source_access.columns)], ignore_index=True)
    source_access_attempt = pd.concat([source_access_attempt, pd.DataFrame(attempt_rows, columns=source_access_attempt.columns)], ignore_index=True)
    source_file = pd.concat([source_file, pd.DataFrame(file_rows, columns=source_file.columns)], ignore_index=True)
    source_access_right = pd.concat([source_access_right, pd.DataFrame(rights_rows, columns=source_access_right.columns)], ignore_index=True)
    promo = pd.DataFrame(promo_rows)
    promo_by_result = {row["source_result_id"]: row for row in promo.to_dict(orient="records")}
    for idx, row in source_result[source_result["source_result_id"].isin(promo_by_result)].iterrows():
        pr = promo_by_result[safe_text(row["source_result_id"])]
        source_result.at[idx, "access_id"] = pr["access_id"]
        source_result.at[idx, "evidence_level"] = "5"
        source_result.at[idx, "evidence_level_name"] = "original_source_obtained"
        source_result.at[idx, "target_acquisition_state"] = "source_object_mirrored"
        source_result.at[idx, "value_verification_state"] = "source_object_obtained_not_parsed"
        source_result.at[idx, "source_is_original"] = "true"
        source_result.at[idx, "number_verified_by_us"] = "false"
        source_result.at[idx, "represented_work_identified"] = "true"
        source_result.at[idx, "source_is_external"] = "true"
        source_result.at[idx, "requires_manual_review"] = "true"
        source_result.at[idx, "conversion_verified"] = "false"
        note = safe_text(row.get("notes"))
        addition = (
            f"full_article_source_file={pr['source_file_id']}; full_article_local_path={pr['local_path']}; "
            f"full_article_sha256={pr['sha256']}; full_article_identity=accepted; "
            "level5_probe=identity-accepted full article text mirrored; D/N value text not yet re-extracted"
        )
        source_result.at[idx, "notes"] = f"{note}; {addition}" if note else addition
    return source_result, source_file, source_access, source_access_attempt, source_access_right, promo


def write_tsv(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, sep="\t", index=False)


def main() -> None:
    source_result = pd.read_csv(SOURCE_RESULT, sep="\t", dtype=str, keep_default_na=False)
    sources = pd.read_csv(SOURCE, sep="\t", dtype=str, keep_default_na=False)
    identifiers = pd.read_csv(SOURCE_IDENTIFIER, sep="\t", dtype=str, keep_default_na=False)
    source_file = pd.read_csv(SOURCE_FILE, sep="\t", dtype=str, keep_default_na=False)
    source_access = pd.read_csv(SOURCE_ACCESS, sep="\t", dtype=str, keep_default_na=False)
    source_access_attempt = pd.read_csv(SOURCE_ACCESS_ATTEMPT, sep="\t", dtype=str, keep_default_na=False)
    source_access_right = pd.read_csv(SOURCE_ACCESS_RIGHT, sep="\t", dtype=str, keep_default_na=False)
    source_version = pd.read_csv(SOURCE_VERSION, sep="\t", dtype=str, keep_default_na=False)
    candidate_ledger = pd.read_csv(SOURCE_OBJECT_CANDIDATE, sep="\t", dtype=str, keep_default_na=False) if SOURCE_OBJECT_CANDIDATE.exists() else pd.DataFrame()

    source_input = source_inputs(sources, identifiers)
    article_sources = set(source_file[source_file["source_byte_class"].isin(ARTICLE_CLASSES)]["source_id"])
    source_type_by_id = {safe_text(row["source_id"]): safe_text(row.get("source_type")) for _, row in sources.iterrows()}
    targets = []
    for _, row in source_result.iterrows():
        if ONLY_RESULT_IDS and safe_text(row["source_result_id"]) not in ONLY_RESULT_IDS:
            continue
        sid = safe_text(row["represented_source_id"])
        if sid in article_sources:
            continue
        if source_type_by_id.get(sid) not in {"paper", "other"}:
            continue
        inp = source_input.get(sid, {})
        if not (inp.get("doi") or inp.get("pmid") or inp.get("pmcid") or inp.get("title")):
            continue
        targets.append(row)
    targets = targets[:MAX_ROWS]

    attempts: list[dict[str, object]] = []
    candidate_rows = []
    created_at = datetime.now(timezone.utc).isoformat()
    newly_accepted_sources: set[str] = set()

    for index, row in enumerate(targets, start=1):
        sid = safe_text(row["represented_source_id"])
        if sid in newly_accepted_sources:
            continue
        inp = source_input[sid]
        candidates = []
        candidates.extend(osf_candidates(inp))
        candidates.extend(direct_url_candidates(inp))
        candidates.extend(europepmc_candidates(inp))
        candidates.extend(crossref_candidates(inp))
        candidates.extend(openalex_candidates(inp))
        candidates.extend(core_candidates(inp))
        candidates.extend(semantic_scholar_candidates(inp))
        candidates.extend(openaire_candidates(inp))
        candidates.extend(hal_candidates(inp))
        candidates.extend(arxiv_candidates(inp))
        candidates.extend(biorxiv_medrxiv_candidates(inp))
        candidates.extend(wayback_candidates(safe_text(row["source_result_id"]), inp, candidate_ledger))
        dedup = []
        seen = set()
        for candidate in candidates:
            if candidate["url"] in seen:
                continue
            seen.add(candidate["url"])
            dedup.append(candidate)
        row_attempts = []
        accepted = False
        for candidate in dedup[:MAX_CANDIDATES_PER_ROUTE * 4]:
            attempt = attempt_candidate(row, inp, candidate)
            row_attempts.append(attempt)
            candidate_rows.append(candidate_ledger_row(attempt, inp, created_at))
            if attempt["identity_decision"] == "accepted_full_article_text":
                accepted = True
                newly_accepted_sources.add(sid)
                break
        attempts.extend(row_attempts)
        print(f"[{index}/{len(targets)}] {row['source_result_id']} candidates={len(dedup)} attempts={len(row_attempts)} accepted={int(accepted)}", flush=True)

    attempts_df = pd.DataFrame(attempts)
    write_tsv(attempts_df, OUT_ATTEMPTS)

    new_candidate_df = pd.DataFrame(candidate_rows)
    if not new_candidate_df.empty:
        # Match existing ledger column order if present.
        if not candidate_ledger.empty:
            for col in candidate_ledger.columns:
                if col not in new_candidate_df.columns:
                    new_candidate_df[col] = ""
            new_candidate_df = new_candidate_df[candidate_ledger.columns]
            candidate_ledger = candidate_ledger[~candidate_ledger["candidate_id"].isin(set(new_candidate_df["candidate_id"]))]
            combined_ledger = pd.concat([candidate_ledger, new_candidate_df], ignore_index=True)
        else:
            combined_ledger = new_candidate_df
        write_tsv(combined_ledger, SOURCE_OBJECT_CANDIDATE)

    source_result, source_file, source_access, source_access_attempt, source_access_right, promoted = promote_accepted(
        attempts, source_result, source_file, source_access, source_access_attempt, source_access_right, source_version
    )
    write_tsv(source_result, SOURCE_RESULT)
    write_tsv(source_file, SOURCE_FILE)
    write_tsv(source_access, SOURCE_ACCESS)
    write_tsv(source_access_attempt, SOURCE_ACCESS_ATTEMPT)
    write_tsv(source_access_right, SOURCE_ACCESS_RIGHT)

    article_sources_after = set(source_file[source_file["source_byte_class"].isin(ARTICLE_CLASSES)]["source_id"])
    source_result["represented_has_full_article"] = source_result["represented_source_id"].isin(article_sources_after)
    full_article_rows = int(source_result["represented_has_full_article"].sum())
    full_article_paper_other = int(
        source_result[source_result["represented_source_id"].map(lambda sid: source_type_by_id.get(sid, "") in {"paper", "other"})]["represented_has_full_article"].sum()
    )
    summary_rows = [
        {"metric": "sample_n", "value": SAMPLE_N},
        {"metric": "targets_considered", "value": len(targets)},
        {"metric": "attempt_rows", "value": len(attempts_df)},
        {"metric": "accepted_full_article_text_rows", "value": len(promoted)},
        {"metric": "accepted_unique_sha256", "value": promoted["sha256"].nunique() if not promoted.empty else 0},
        {"metric": "rows_with_represented_full_article_after", "value": full_article_rows},
        {"metric": "paper_or_other_rows_with_full_article_after", "value": full_article_paper_other},
        {"metric": "created_at_utc", "value": created_at},
    ]
    if not attempts_df.empty:
        for key, value in attempts_df["route"].value_counts().sort_index().items():
            summary_rows.append({"metric": f"route_attempt::{key}", "value": int(value)})
        for key, value in attempts_df.loc[attempts_df["identity_decision"].eq("accepted_full_article_text"), "route"].value_counts().sort_index().items():
            summary_rows.append({"metric": f"route_accepted::{key}", "value": int(value)})
        for key, value in attempts_df["failure_code"].value_counts().head(20).items():
            summary_rows.append({"metric": f"failure_code::{key}", "value": int(value)})
    summary = pd.DataFrame(summary_rows)
    write_tsv(summary, OUT_SUMMARY)

    lines = [
        "# Full Article Text Acquisition Pass",
        "",
        f"- Targets considered: {len(targets)}",
        f"- Route attempt rows: {len(attempts_df)}",
        f"- Newly accepted full-article text objects: {len(promoted)}",
        f"- Rows with represented full article after pass: {full_article_rows}/{SAMPLE_N}",
        f"- Paper/other represented rows with full article after pass: {full_article_paper_other}",
        "",
        "## Accepted Rows",
        "",
    ]
    if promoted.empty:
        lines.append("- None.")
    else:
        for _, row in promoted.iterrows():
            lines.append(f"- `{row['source_result_id']}` -> `{row['source_file_id']}` via `{row['route']}`; `{row['local_path']}`")
    lines.extend(["", "## Failure Profile", ""])
    if not attempts_df.empty:
        for key, value in attempts_df["failure_code"].value_counts().head(15).items():
            lines.append(f"- `{key}`: {int(value)}")
    lines.extend(
        [
            "",
            "## Notes",
            "",
            "- This pass accepts PDF, XML/JATS, or full-article HTML when the primary DOI/title identity gate passes.",
            "- Repository and archive routes are treated as candidate generators. Landing pages and metadata-only hits stay in the candidate ledger and do not promote.",
            "- CORE and BASE are not included here because CORE is currently rate-limiting/key-gated in this environment and BASE requires whitelisting.",
            "",
            "## Output Files",
            "",
            f"- `{rel(OUT_ATTEMPTS)}`",
            f"- `{rel(OUT_SUMMARY)}`",
            f"- `{rel(SOURCE_OBJECT_CANDIDATE)}`",
            f"- `{rel(SOURCE_FILE)}`",
            f"- `{rel(SOURCE_RESULT)}`",
        ]
    )
    OUT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    OUT_REPORT.write_text("\n".join(lines) + "\n")

    print(f"Wrote {OUT_ATTEMPTS}")
    print(f"Wrote {OUT_SUMMARY}")
    print(f"Wrote {OUT_REPORT}")
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
