#!/usr/bin/env python3
"""Execute scriptable individual-replication metadata/source-object search batches."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import quote

import pandas as pd
import requests
import yaml


ROOT = Path(__file__).resolve().parents[1]
SEARCH_DIR = ROOT / "steps" / "searches" / "figure1"
DESIGN_YML = SEARCH_DIR / "individualrepsearch-design.yml"
QUERY_BANK = SEARCH_DIR / "individualrepsearch-vast-query-bank.tsv"
RECALL_PROBES = SEARCH_DIR / "individualrepsearch-known-good-recall-probes.tsv"

BATCH_ID = "batch001"
RUN_ID = ""
RUN_DIR = SEARCH_DIR
RAW_DIR = RUN_DIR / "raw"
QUERY_LOG = SEARCH_DIR / "individualrepsearch-query-log-batch001.tsv"
SCREENED_HITS = SEARCH_DIR / "individualrepsearch-screening-hits-batch001.tsv"
RECALL_RESULTS = SEARCH_DIR / "individualrepsearch-recall-probe-results-batch001.tsv"
MANIFEST = SEARCH_DIR / "individualrepsearch-api-batch001.json"
REPORT = ROOT / "reports" / "figure1_individual_replication_vast_search_execution_batch001_2026-05-05.md"

CONTACT_EMAIL = os.environ.get("PROVENANCE_CONTACT_EMAIL", "rexdouglass@gmail.com").strip()
USER_AGENT = (
    "PublishedSmallNStudiesDontMatter individual replication search "
    f"(mailto:{CONTACT_EMAIL}; noncommercial provenance research)"
)
TIMEOUT = (15, 45)
REQUEST_DELAY = float(os.environ.get("INDIVIDUAL_REPLICATION_SEARCH_DELAY_SECONDS", "0.25"))


def configure_batch(batch_id: str) -> None:
    """Configure batch-scoped output paths.

    Batch 001 is kept as the default for backward-compatible Make targets.
    Later batches should pass --batch-id so raw API bytes and triage manifests
    remain auditable instead of overwriting earlier runs.
    """

    global BATCH_ID, RUN_ID, RUN_DIR, RAW_DIR, QUERY_LOG, SCREENED_HITS, RECALL_RESULTS, MANIFEST, REPORT
    BATCH_ID = batch_id
    RUN_ID = f"2026-05-05_individual_replication_vast_search_{batch_id}"
    RUN_DIR = SEARCH_DIR / f"individualrepsearch_api_{batch_id}"
    RAW_DIR = RUN_DIR / "raw"
    QUERY_LOG = SEARCH_DIR / f"individualrepsearch-query-log-{batch_id}.tsv"
    SCREENED_HITS = SEARCH_DIR / f"individualrepsearch-screening-hits-{batch_id}.tsv"
    RECALL_RESULTS = SEARCH_DIR / f"individualrepsearch-recall-probe-results-{batch_id}.tsv"
    MANIFEST = SEARCH_DIR / f"individualrepsearch-api-{batch_id}.json"
    REPORT = ROOT / "reports" / f"figure1_individual_replication_vast_search_execution_{batch_id}_2026-05-05.md"


configure_batch(BATCH_ID)

RELATION_PATTERNS = [
    (5, "title_registered_replication_report", re.compile(r"\bregistered replication report\b", re.I), "title"),
    (5, "title_exact_replication", re.compile(r"\b(direct|exact|close|independent|failed|pre-registered|preregistered)\s+replication\b", re.I), "title"),
    (5, "title_exact_replication", re.compile(r"\b(replication of|failure to replicate|failed to replicate|unsuccessful attempts to replicate)\b", re.I), "title"),
    (4, "abstract_direct_replication", re.compile(r"\b(directly replicated|direct replication|exact replication|replication attempt|we replicated|we attempted to replicate)\b", re.I), "abstract"),
    (4, "abstract_failed_replication", re.compile(r"\b(failed to replicate|did not replicate|could not replicate|unable to replicate|not replicated|no evidence for)\b", re.I), "abstract"),
    (4, "abstract_independent_validation", re.compile(r"\b(independent validation|external validation|replication cohort|validation cohort|discovery cohort)\b", re.I), "abstract"),
    (4, "clinical_confirmatory_trial", re.compile(r"\b(failed to confirm|did not confirm|confirmatory trial|multicenter randomized trial|larger randomized trial)\b", re.I), "abstract"),
    (3, "methods_original_study_mapping", re.compile(r"\b(study\s+\d+\s+from|experiment\s+\d+\s+from|original materials|same materials|same protocol)\b", re.I), "abstract"),
]

NEGATIVE_PATTERNS = [
    re.compile(r"\b(reanalysis|same data|same dataset|multiverse analysis|robustness check|analyst variability|reproduced the code)\b", re.I),
    re.compile(r"\b(systematic review|meta-analysis|editorial|commentary|protocol)\b", re.I),
]

VALUE_PATTERNS = [
    re.compile(r"\b(cohen'?s d|hedges'? g|standardized mean difference|smd|effect size)\b", re.I),
    re.compile(r"\b(sample size|total n|n\s*=|participants|patients)\b", re.I),
    re.compile(r"\b(odds ratio|risk ratio|relative risk|risk difference|event counts|mortality|2x2)\b", re.I),
    re.compile(r"\b(means? and standard deviations?|means? and sds?|t\s*\(|f\s*\(|r\s*=)\b", re.I),
]


def clean(value: Any, max_len: int = 20000) -> str:
    if value is None:
        return ""
    text = str(value).replace("\t", " ").replace("\n", " ").replace("\r", " ")
    text = re.sub(r"\s+", " ", text).strip()
    return text[:max_len]


def slugify(value: str, max_len: int = 90) -> str:
    text = re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")
    return (text or "missing")[:max_len]


def sha_id(prefix: str, *parts: Any) -> str:
    payload = "||".join(clean(part, max_len=5000) for part in parts)
    return f"{prefix}_{hashlib.sha1(payload.encode('utf-8')).hexdigest()[:16]}"


def request_json(session: requests.Session, url: str, params: dict[str, Any] | None = None) -> tuple[dict[str, Any], str, str]:
    response = session.get(url, params=params, timeout=TIMEOUT)
    final_url = response.url
    status = str(response.status_code)
    response.raise_for_status()
    return response.json(), final_url, status


def invert_abstract(index: dict[str, list[int]] | None) -> str:
    if not isinstance(index, dict) or not index:
        return ""
    words: list[tuple[int, str]] = []
    for word, positions in index.items():
        for pos in positions:
            words.append((int(pos), word))
    return " ".join(word for _, word in sorted(words))


def normalize_openalex(item: dict[str, Any]) -> dict[str, Any]:
    authors = []
    for authorship in item.get("authorships") or []:
        author = authorship.get("author") or {}
        if author.get("display_name"):
            authors.append(clean(author.get("display_name")))
    doi = clean(item.get("doi")).replace("https://doi.org/", "")
    locations = item.get("locations") or []
    urls = []
    for location in locations:
        source_url = clean((location.get("source") or {}).get("homepage_url"))
        landing_url = clean(location.get("landing_page_url"))
        pdf_url = clean(location.get("pdf_url"))
        for url in [pdf_url, landing_url, source_url]:
            if url and url not in urls:
                urls.append(url)
    primary = item.get("primary_location") or {}
    for url in [clean(primary.get("pdf_url")), clean(primary.get("landing_page_url")), clean(item.get("id"))]:
        if url and url not in urls:
            urls.append(url)
    return {
        "surface": "openalex",
        "work_id": clean(item.get("id")),
        "doi": doi.lower().rstrip(".,);]"),
        "title": clean(item.get("title") or item.get("display_name")),
        "abstract": invert_abstract(item.get("abstract_inverted_index")),
        "year": clean(item.get("publication_year")),
        "journal": clean(((primary.get("source") or {}).get("display_name"))),
        "authors": authors,
        "url": clean(item.get("id")),
        "source_object_urls": urls,
        "raw": item,
    }


def normalize_crossref(item: dict[str, Any]) -> dict[str, Any]:
    title = clean((item.get("title") or [""])[0])
    journal = clean((item.get("container-title") or [""])[0])
    authors = []
    for author in item.get("author") or []:
        name = " ".join(part for part in [clean(author.get("given")), clean(author.get("family"))] if part)
        if name:
            authors.append(name)
    issued = item.get("issued", {}).get("date-parts") or []
    year = clean(issued[0][0] if issued and issued[0] else "")
    doi = clean(item.get("DOI")).lower().rstrip(".,);]")
    url = clean(item.get("URL")) or (f"https://doi.org/{doi}" if doi else "")
    return {
        "surface": "crossref",
        "work_id": doi or url,
        "doi": doi,
        "title": title,
        "abstract": clean(item.get("abstract")),
        "year": year,
        "journal": journal,
        "authors": authors,
        "url": url,
        "source_object_urls": [url] if url else [],
        "raw": item,
    }


def normalize_europepmc(item: dict[str, Any]) -> dict[str, Any]:
    doi = clean(item.get("doi")).lower().rstrip(".,);]")
    pmid = clean(item.get("pmid"))
    pmcid = clean(item.get("pmcid"))
    urls = []
    if doi:
        urls.append(f"https://doi.org/{doi}")
    if pmcid:
        urls.append(f"https://pmc.ncbi.nlm.nih.gov/articles/{pmcid}/")
    if pmid:
        urls.append(f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/")
    return {
        "surface": "europepmc",
        "work_id": pmcid or pmid or doi,
        "doi": doi,
        "title": clean(item.get("title")),
        "abstract": clean(item.get("abstractText")),
        "year": clean(item.get("pubYear")),
        "journal": clean(item.get("journalTitle")),
        "authors": [clean(a) for a in clean(item.get("authorString")).split(",") if clean(a)],
        "url": urls[0] if urls else "",
        "source_object_urls": urls,
        "raw": item,
    }


def normalize_plos(item: dict[str, Any]) -> dict[str, Any]:
    title = clean((item.get("title") or [""])[0] if isinstance(item.get("title"), list) else item.get("title"))
    abstract = clean((item.get("abstract") or [""])[0] if isinstance(item.get("abstract"), list) else item.get("abstract"))
    doi = clean(item.get("id")).lower().rstrip(".,);]")
    url = f"https://doi.org/{doi}" if doi.startswith("10.") else ""
    return {
        "surface": "plos",
        "work_id": doi,
        "doi": doi if doi.startswith("10.") else "",
        "title": title,
        "abstract": abstract,
        "year": clean(item.get("publication_date"))[:4],
        "journal": clean((item.get("journal") or [""])[0] if isinstance(item.get("journal"), list) else item.get("journal")),
        "authors": [clean(a) for a in item.get("author_display") or []],
        "url": url,
        "source_object_urls": [url] if url else [],
        "raw": item,
    }


def normalize_datacite(item: dict[str, Any]) -> dict[str, Any]:
    attrs = item.get("attributes") or {}
    doi = clean(attrs.get("doi")).lower().rstrip(".,);]")
    titles = attrs.get("titles") or []
    descriptions = attrs.get("descriptions") or []
    creators = attrs.get("creators") or []
    title = ""
    if titles and isinstance(titles[0], dict):
        title = clean(titles[0].get("title"))
    abstract = " ".join(clean(desc.get("description")) for desc in descriptions if isinstance(desc, dict))
    authors = []
    for creator in creators:
        if isinstance(creator, dict):
            name = clean(creator.get("name"))
            if name:
                authors.append(name)
    url = clean(attrs.get("url"))
    urls = []
    if doi:
        urls.append(f"https://doi.org/{doi}")
    if url and url not in urls:
        urls.append(url)
    if clean(item.get("id")) and clean(item.get("id")) not in urls:
        urls.append(clean(item.get("id")))
    types = attrs.get("types") or {}
    return {
        "surface": "datacite",
        "work_id": clean(item.get("id")) or doi or url,
        "doi": doi,
        "title": title,
        "abstract": clean(abstract),
        "year": clean(attrs.get("publicationYear")),
        "journal": clean(attrs.get("publisher") or types.get("resourceTypeGeneral")),
        "authors": authors,
        "url": url or (f"https://doi.org/{doi}" if doi else ""),
        "source_object_urls": urls,
        "raw": item,
    }


def query_openalex(session: requests.Session, query: str, rows: int) -> tuple[list[dict[str, Any]], dict[str, Any], str, str]:
    params = {
        "search": query,
        "filter": "from_publication_date:1990-01-01,type:article",
        "per-page": rows,
        "mailto": CONTACT_EMAIL,
        "select": "id,doi,title,display_name,publication_year,authorships,abstract_inverted_index,primary_location,locations,type,cited_by_count",
    }
    payload, final_url, status = request_json(session, "https://api.openalex.org/works", params=params)
    return [normalize_openalex(item) for item in payload.get("results") or []], payload, final_url, status


def query_crossref(session: requests.Session, query: str, rows: int) -> tuple[list[dict[str, Any]], dict[str, Any], str, str]:
    params = {
        "query.bibliographic": query,
        "filter": "type:journal-article,from-pub-date:1990-01-01",
        "rows": rows,
        "select": "DOI,title,author,issued,container-title,abstract,URL,type",
        "mailto": CONTACT_EMAIL,
    }
    payload, final_url, status = request_json(session, "https://api.crossref.org/works", params=params)
    return [normalize_crossref(item) for item in (payload.get("message") or {}).get("items") or []], payload, final_url, status


def query_europepmc(session: requests.Session, query: str, rows: int) -> tuple[list[dict[str, Any]], dict[str, Any], str, str]:
    params = {
        "query": f'({query}) AND FIRST_PDATE:[1990-01-01 TO 2026-12-31]',
        "format": "json",
        "pageSize": rows,
        "resultType": "core",
    }
    payload, final_url, status = request_json(session, "https://www.ebi.ac.uk/europepmc/webservices/rest/search", params=params)
    return [normalize_europepmc(item) for item in (payload.get("resultList") or {}).get("result") or []], payload, final_url, status


def query_plos(session: requests.Session, query: str, rows: int) -> tuple[list[dict[str, Any]], dict[str, Any], str, str]:
    params = {
        "q": query,
        "fl": "id,title,abstract,author_display,journal,publication_date",
        "rows": rows,
        "wt": "json",
    }
    payload, final_url, status = request_json(session, "https://api.plos.org/search", params=params)
    return [normalize_plos(item) for item in (payload.get("response") or {}).get("docs") or []], payload, final_url, status


def query_datacite(session: requests.Session, query: str, rows: int) -> tuple[list[dict[str, Any]], dict[str, Any], str, str]:
    params = {
        "query": query,
        "page[size]": rows,
        "sort": "relevance",
    }
    payload, final_url, status = request_json(session, "https://api.datacite.org/dois", params=params)
    return [normalize_datacite(item) for item in payload.get("data") or []], payload, final_url, status


SURFACE_RUNNERS = {
    "openalex": query_openalex,
    "crossref": query_crossref,
    "europepmc": query_europepmc,
    "plos": query_plos,
    "datacite": query_datacite,
}


def score_hit(hit: dict[str, Any]) -> dict[str, Any]:
    title = clean(hit.get("title"))
    abstract = clean(hit.get("abstract"))
    hay = f"{title} {abstract}"
    negative = any(pattern.search(hay) for pattern in NEGATIVE_PATTERNS)
    best_score = -5 if negative else 0
    best_type = "same_data_or_review_negative" if negative else "no_relation_evidence"
    best_quote = ""
    for score, evidence_type, pattern, scope in RELATION_PATTERNS:
        text = title if scope == "title" else abstract
        match = pattern.search(text)
        if match and score > best_score:
            best_score = score
            best_type = evidence_type
            start = max(match.start() - 120, 0)
            end = min(match.end() + 220, len(text))
            best_quote = text[start:end]
    value_score = 0
    for pattern in VALUE_PATTERNS:
        if pattern.search(hay):
            value_score += 1
    return {
        "relation_score": best_score,
        "relation_evidence_type": best_type,
        "relation_quote": clean(best_quote, max_len=800),
        "value_score": min(value_score, 4),
        "negative_flag": negative,
    }


def infer_original_target(title: str) -> str:
    patterns = [
        r"Registered Replication Report:?\s*(.+)$",
        r"(?:Direct|Exact|Close|Independent|First Direct)\s+Replication\s+of\s+(.+?)(?:\:|$)",
        r"Replication\s+of\s+['\"]?(.+?)['\"]?(?:\:|$)",
        r"Failed\s+Replication\s+of\s+(.+?)(?:\:|$)",
        r"Failure\s+to\s+Replicate\s+(.+?)(?:\:|$)",
        r"Multilab Direct Replication of\s+(.+?)(?:\:|$)",
        r"Registered Replication Report on\s+(.+?)(?:\:|$)",
    ]
    for pattern in patterns:
        match = re.search(pattern, title, flags=re.I)
        if match:
            return clean(match.group(1), max_len=300)
    return ""


def route_from_query_bias(route_bias: str, hit: dict[str, Any], score: dict[str, Any]) -> str:
    if score["relation_score"] < 4 or score["negative_flag"]:
        return "reject"
    title_target = infer_original_target(clean(hit.get("title")))
    if title_target and score["value_score"] >= 3 and route_bias in {"strict_figure1a", "d_equivalent_figure1b", "native_only"}:
        return route_bias
    return "coverage_only"


def candidate_from_hit(hit: dict[str, Any], query_row: dict[str, str], score: dict[str, Any], raw_path: str) -> dict[str, Any]:
    route = route_from_query_bias(query_row.get("candidate_route_bias", ""), hit, score)
    target = infer_original_target(clean(hit.get("title")))
    doi = clean(hit.get("doi")).lower().rstrip(".,);]")
    source_urls = [url for url in hit.get("source_object_urls") or [] if clean(url)]
    candidate_id = sha_id("api_candidate", hit.get("surface"), doi or hit.get("work_id"), query_row.get("query_id"), target)
    return {
        "candidate_id": candidate_id,
        "candidate_name": f"{target or 'unresolved original target'} -> {clean(hit.get('title'))}",
        "domain": "metadata_api_search",
        "candidate_route": route,
        "confidence": "medium" if score["relation_score"] >= 5 else "low",
        "candidate_unit_key": sha_id("candidate_unit", target, doi, clean(hit.get("title")), "unresolved_outcome"),
        "screening_status": "api_relation_screened",
        "query_ids": [query_row.get("query_id", "")],
        "surfaces": [clean(hit.get("surface"))],
        "raw_record_paths": [raw_path],
        "original_title": target,
        "original_doi": "",
        "replication_title": clean(hit.get("title")),
        "replication_doi": doi,
        "replication_or_followup": {
            "title": clean(hit.get("title")),
            "authors_year": f"{'; '.join(hit.get('authors') or [])} ({clean(hit.get('year'))})",
            "doi": doi,
            "url": clean(hit.get("url")) or (f"https://doi.org/{doi}" if doi else ""),
            "source_object_urls": source_urls,
            "effect_text_or_table_hint": "metadata search hit; fetch full text/source object before value extraction",
            "n_text_or_table_hint": "metadata search hit; fetch full text/source object before value extraction",
        },
        "source_object_urls": source_urls,
        "source_objects_to_mirror_first": [
            {"url": url, "object_type": "metadata_or_article_landing", "why_needed": "Resolve full text, original target, and value-bearing source objects."}
            for url in source_urls[:4]
        ],
        "relationship_evidence": {
            "replication_kind": "metadata_relation_candidate",
            "where_seen": score["relation_evidence_type"],
            "verbatim_or_paraphrased_basis": score["relation_quote"],
            "relation_score": score["relation_score"],
            "value_score": score["value_score"],
        },
        "value_availability": {
            "has_original_effect": "unclear",
            "has_replication_or_followup_effect": "unclear",
            "has_original_n": "unclear",
            "has_replication_or_followup_n": "unclear",
            "effect_metric": "unknown",
            "conversion_route": "unknown_until_full_text",
            "replication_n_larger_than_original_n": "unclear",
        },
        "relation_score": score["relation_score"],
        "value_score": score["value_score"],
        "relation_evidence_type": score["relation_evidence_type"],
        "relation_evidence_strength": score["relation_score"],
        "dedupe_risk": "high" if target else "medium",
        "blockers": ["resolve_original_target", "fetch_full_text_or_source_object", "extract_effect_and_n"],
        "recommended_next_action": "resolve_original_target_or_fetch_full_text",
    }


def save_raw(surface: str, query_id: str, payload: dict[str, Any]) -> str:
    path = RAW_DIR / surface / f"{slugify(query_id)}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return str(path.relative_to(ROOT))


DEFAULT_INCLUDED_PHASES = {
    "01_metadata_replication_language",
    "02_open_full_text_value_language",
    "03_repository_source_object_search",
    "04_psychology_long_tail",
    "05_behavioral_econ_marketing_management",
    "06_education_health_sports",
    "07_clinical_d_equivalent_followup",
    "08_genetics_validation_native",
}


def query_rows_for_batch(max_query_priority: int, campaign_phases: set[str] | None = None) -> list[dict[str, str]]:
    df = pd.read_csv(QUERY_BANK, sep="\t", dtype=str).fillna("")
    df["priority_int"] = pd.to_numeric(df["priority"], errors="coerce").fillna(99).astype(int)
    allowed_phases = campaign_phases or DEFAULT_INCLUDED_PHASES
    rows = df[(df["priority_int"] <= max_query_priority) & (df["campaign_phase"].isin(allowed_phases))]
    return rows.drop(columns=["priority_int"]).to_dict(orient="records")


def surface_list_for_query(query_row: dict[str, str]) -> list[str]:
    surface = query_row.get("surface", "").lower()
    surfaces: list[str] = []
    if "openalex" in surface:
        surfaces.append("openalex")
    if "crossref" in surface:
        surfaces.append("crossref")
    if "europepmc" in surface or "pmc" in surface or "pubmed" in surface:
        surfaces.append("europepmc")
    if "plos" in surface:
        surfaces.append("plos")
    if any(token in surface for token in ["datacite", "figshare", "zenodo", "dataverse", "osf", "dryad", "repository"]):
        surfaces.append("datacite")
    deduped: list[str] = []
    for item in surfaces:
        if item in SURFACE_RUNNERS and item not in deduped:
            deduped.append(item)
    return deduped


def execute_queries(session: requests.Session, rows: list[dict[str, str]], rows_per_query: int) -> tuple[list[dict[str, Any]], list[dict[str, str]], list[dict[str, Any]]]:
    hit_rows: list[dict[str, Any]] = []
    log_rows: list[dict[str, str]] = []
    candidates_by_key: dict[str, dict[str, Any]] = {}
    for query_row in rows:
        surfaces = surface_list_for_query(query_row)
        for surface in surfaces:
            query_id = f"{query_row['query_id']}__{surface}"
            started = datetime.now(timezone.utc).isoformat()
            raw_path = ""
            final_url = ""
            status = ""
            error = ""
            normalized: list[dict[str, Any]] = []
            n_new_candidates = 0
            try:
                normalized, payload, final_url, status = SURFACE_RUNNERS[surface](session, query_row["query"], rows_per_query)
                raw_path = save_raw(surface, query_id, payload)
                for rank, hit in enumerate(normalized, start=1):
                    score = score_hit(hit)
                    hit_row = {
                        "run_id": RUN_ID,
                        "query_id": query_id,
                        "surface": surface,
                        "rank": rank,
                        "title": clean(hit.get("title")),
                        "doi": clean(hit.get("doi")),
                        "year": clean(hit.get("year")),
                        "journal": clean(hit.get("journal")),
                        "url": clean(hit.get("url")),
                        "relation_score": score["relation_score"],
                        "relation_evidence_type": score["relation_evidence_type"],
                        "relation_quote": score["relation_quote"],
                        "value_score": score["value_score"],
                        "negative_flag": score["negative_flag"],
                        "raw_record_path": raw_path,
                    }
                    hit_rows.append(hit_row)
                    if score["relation_score"] >= 4 and not score["negative_flag"]:
                        candidate = candidate_from_hit(hit, query_row, score, raw_path)
                        candidates_by_key.setdefault(candidate["candidate_unit_key"], candidate)
                        n_new_candidates += 1
            except Exception as exc:
                error = f"{type(exc).__name__}: {exc}"
            log_rows.append(
                {
                    "query_id": query_id,
                    "run_id": RUN_ID,
                    "surface": surface,
                    "endpoint_or_engine": surface,
                    "query_family": query_row.get("campaign_phase", ""),
                    "query_string": query_row.get("query", ""),
                    "params_json": json.dumps({"rows_per_query": rows_per_query}, sort_keys=True),
                    "date_run": started,
                    "cursor_or_page": "page1",
                    "rank_start": "1",
                    "rank_end": str(rows_per_query),
                    "n_returned": str(len(normalized)),
                    "n_new_work_ids": str(len({clean(hit.get("work_id")) or clean(hit.get("doi")) for hit in normalized})),
                    "n_new_candidate_pairs": str(n_new_candidates),
                    "raw_output_path": raw_path,
                    "notes": error or f"status={status}; final_url={final_url}",
                }
            )
            time.sleep(REQUEST_DELAY)
    return hit_rows, log_rows, list(candidates_by_key.values())


def run_recall_probes(session: requests.Session, rows_per_probe: int) -> list[dict[str, str]]:
    probes = pd.read_csv(RECALL_PROBES, sep="\t", dtype=str).fillna("").to_dict(orient="records")
    out: list[dict[str, str]] = []
    for probe in probes:
        query = f"{probe['replication_search_terms']} {probe['original_search_terms']}"
        for surface in ["openalex", "crossref"]:
            query_id = f"recall_{probe['probe_id']}__{surface}"
            found = False
            titles: list[str] = []
            raw_path = ""
            error = ""
            try:
                normalized, payload, _, _ = SURFACE_RUNNERS[surface](session, query, rows_per_probe)
                raw_path = save_raw(surface, query_id, payload)
                expected = clean(probe["replication_search_terms"]).lower()
                expected_tokens = [token for token in re.findall(r"[a-z0-9]+", expected) if len(token) > 3]
                for hit in normalized:
                    title = clean(hit.get("title"))
                    titles.append(title)
                    title_norm = title.lower()
                    if expected_tokens and sum(1 for token in expected_tokens if token in title_norm) >= max(2, min(4, len(expected_tokens))):
                        found = True
            except Exception as exc:
                error = f"{type(exc).__name__}: {exc}"
            out.append(
                {
                    "run_id": RUN_ID,
                    "probe_id": probe["probe_id"],
                    "surface": surface,
                    "query": query,
                    "expected_route": probe["expected_route"],
                    "found_expected_replication": str(found).lower(),
                    "top_titles_json": json.dumps(titles[:5], ensure_ascii=True),
                    "raw_output_path": raw_path,
                    "notes": error,
                }
            )
            time.sleep(REQUEST_DELAY)
    return out


def write_manifest(candidates: list[dict[str, Any]], rows: list[dict[str, str]], recall_rows: list[dict[str, str]]) -> None:
    payload = {
        "task_id": f"individual_replication_api_search_{BATCH_ID}",
        "batch_id": BATCH_ID,
        "strategy_id": "figure1_individual_replication_paper_level_search",
        "run_id": RUN_ID,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "candidates": candidates,
        "searches_run": [
            {
                "query_or_route": row["query_string"],
                "source": row["surface"],
                "useful_hits": int(row["n_new_candidate_pairs"] or "0"),
                "notes": f"query_id={row['query_id']}; raw={row['raw_output_path']}; {row['notes']}",
            }
            for row in rows
        ],
        "recall_probe_results_path": str(RECALL_RESULTS.relative_to(ROOT)),
        "high_confidence_rejections": [],
    }
    MANIFEST.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def write_report(hit_rows: list[dict[str, Any]], log_rows: list[dict[str, str]], candidates: list[dict[str, Any]], recall_rows: list[dict[str, str]]) -> None:
    recall_total = len(recall_rows)
    recall_found = sum(1 for row in recall_rows if row["found_expected_replication"] == "true")
    failed_query_calls = sum(1 for row in log_rows if not clean(row.get("notes")).startswith("status="))
    route_counts = pd.Series([candidate["candidate_route"] for candidate in candidates]).value_counts().to_dict() if candidates else {}
    surface_counts = pd.Series([row["surface"] for row in hit_rows]).value_counts().to_dict() if hit_rows else {}
    query_surface_counts = pd.Series([row["surface"] for row in log_rows]).value_counts().to_dict() if log_rows else {}
    lines = [
        f"# Figure 1 Individual Replication Vast Search Execution - {BATCH_ID}",
        "",
        f"- Run ID: `{RUN_ID}`",
        f"- Query calls logged: {len(log_rows):,}",
        f"- Query calls with API errors: {failed_query_calls:,}",
        f"- Raw hits screened: {len(hit_rows):,}",
        f"- Relation-scored candidate units emitted: {len(candidates):,}",
        f"- Recall probe surface checks passed: {recall_found:,}/{recall_total:,}",
        "",
        "## Route Counts",
        "",
    ]
    for route, count in sorted(route_counts.items()):
        lines.append(f"- `{route}`: {count:,}")
    lines.extend(["", "## Surface Hit Counts", ""])
    for surface, count in sorted(surface_counts.items()):
        lines.append(f"- `{surface}`: {count:,}")
    lines.extend(["", "## Query Surface Counts", ""])
    for surface, count in sorted(query_surface_counts.items()):
        lines.append(f"- `{surface}`: {count:,}")
    if failed_query_calls:
        lines.extend(["", "## API Errors", ""])
        for row in log_rows:
            notes = clean(row.get("notes"))
            if not notes.startswith("status="):
                lines.append(f"- `{row.get('surface')}` `{row.get('query_id')}`: {notes[:300]}")
    lines.extend(
        [
            "",
            "## Outputs",
            "",
            f"- Query log: `{QUERY_LOG.relative_to(ROOT)}`",
            f"- Screened hits: `{SCREENED_HITS.relative_to(ROOT)}`",
            f"- Recall probe results: `{RECALL_RESULTS.relative_to(ROOT)}`",
            f"- Candidate manifest: `{MANIFEST.relative_to(ROOT)}`",
            f"- Raw API responses: `{RUN_DIR.relative_to(ROOT)}/raw/`",
            "",
            "## Interpretation",
            "",
            "This first execution is a metadata/API pass. It establishes relation-candidate discovery and recall logging, but it does not by itself verify values from local source bytes. Candidates emitted here should be resolved to original targets and full text/source objects before any row promotion.",
        ]
    )
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch-id", default="batch001")
    parser.add_argument("--replace", action="store_true")
    parser.add_argument("--rows-per-query", type=int, default=8)
    parser.add_argument("--rows-per-probe", type=int, default=8)
    parser.add_argument("--max-query-priority", type=int, default=2)
    parser.add_argument(
        "--campaign-phase",
        action="append",
        default=[],
        help="Restrict to one or more campaign_phase values from the query bank. Repeat for multiple phases.",
    )
    parser.add_argument("--skip-recall", action="store_true")
    parser.add_argument("--report-only", action="store_true", help="Regenerate the markdown report from existing batch artifacts.")
    args = parser.parse_args()
    configure_batch(args.batch_id)

    RUN_DIR.mkdir(parents=True, exist_ok=True)
    if not DESIGN_YML.exists():
        raise SystemExit("Run make figure1-individual-replication-search-strategy first.")
    yaml.safe_load(DESIGN_YML.read_text(encoding="utf-8"))

    if args.report_only:
        hit_rows = pd.read_csv(SCREENED_HITS, sep="\t", dtype=str, keep_default_na=False).to_dict(orient="records") if SCREENED_HITS.exists() else []
        log_rows = pd.read_csv(QUERY_LOG, sep="\t", dtype=str, keep_default_na=False).to_dict(orient="records") if QUERY_LOG.exists() else []
        recall_rows = pd.read_csv(RECALL_RESULTS, sep="\t", dtype=str, keep_default_na=False).to_dict(orient="records") if RECALL_RESULTS.exists() else []
        candidates = []
        if MANIFEST.exists():
            payload = json.loads(MANIFEST.read_text(encoding="utf-8"))
            candidates = payload.get("candidates") or []
        write_report(hit_rows, log_rows, candidates, recall_rows)
        print(f"Wrote {REPORT}")
        return

    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})
    rows = query_rows_for_batch(args.max_query_priority, set(args.campaign_phase) if args.campaign_phase else None)
    hit_rows, log_rows, candidates = execute_queries(session, rows, args.rows_per_query)
    recall_rows = [] if args.skip_recall else run_recall_probes(session, args.rows_per_probe)

    pd.DataFrame(log_rows).fillna("").to_csv(QUERY_LOG, sep="\t", index=False)
    pd.DataFrame(hit_rows).fillna("").to_csv(SCREENED_HITS, sep="\t", index=False)
    pd.DataFrame(recall_rows).fillna("").to_csv(RECALL_RESULTS, sep="\t", index=False)
    write_manifest(candidates, log_rows, recall_rows)
    write_report(hit_rows, log_rows, candidates, recall_rows)

    print(f"Wrote {QUERY_LOG} ({len(log_rows)} query calls)")
    print(f"Wrote {SCREENED_HITS} ({len(hit_rows)} hits)")
    print(f"Wrote {MANIFEST} ({len(candidates)} candidates)")
    print(f"Wrote {REPORT}")


if __name__ == "__main__":
    main()
