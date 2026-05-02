#!/usr/bin/env python3
"""Run automated result-artifact acquisition strategies for a plot queue.

The script is intentionally proposal-only. It discovers downloadable or local
candidate artifacts and writes SOURCE_ARTIFACTS.tsv-shaped rows plus an attempt
ledger. Mirroring/sampling is handled by mirror_and_sample_source_artifacts.py.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import mimetypes
import re
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, quote, unquote, urljoin, urlparse

import requests


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_TSV = ROOT / "SOURCE_ARTIFACTS.tsv"

USER_AGENT = "result-artifact-acquisition/0.1 (research provenance; contact local project maintainer)"
DOWNLOADABLE_EXTS = {
    "csv",
    "tsv",
    "tab",
    "txt",
    "xlsx",
    "xls",
    "json",
    "md",
    "zip",
    "rds",
    "rdata",
    "dta",
    "sav",
    "pdf",
    "html",
    "htm",
    "r",
    "rmd",
    "py",
    "do",
    "sps",
}
PAIR_TERMS = ["original", "replication", "repli", "paired", "study_pair", "claim_id", "target", "followup", "follow-up"]
N_TERMS = ["sample", "sample size", "participants", "subjects", " n", "_n", "n_"]
EFFECT_TERMS = ["effect", "smd", "cohen", "hedges", "stat", "p_value", "p value", "estimate", "coef", "ci", "confidence"]
PUBLICATION_TERMS = ["doi", "pmid", "pmcid", "citation", "journal", "publication", "article", "paper"]


def clean(value: object, max_len: int = 12000) -> str:
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value).replace("\t", " ")).strip()[:max_len]


def repo_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def resolve_path(value: str) -> Path:
    path = Path(clean(value))
    return path if path.is_absolute() else ROOT / path


def slug(value: object, fallback: str = "item") -> str:
    out = re.sub(r"[^a-zA-Z0-9]+", "_", clean(value).lower()).strip("_")
    return out[:100] or fallback


def stable_id(prefix: str, *parts: object) -> str:
    text = "\n".join(clean(part, 20000) for part in parts if clean(part))
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]
    return f"{prefix}_{digest}"


def today() -> str:
    return datetime.now().date().isoformat()


def source_artifact_columns() -> list[str]:
    with SCHEMA_TSV.open("r", encoding="utf-8") as handle:
        return handle.readline().rstrip("\n").split("\t")


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return [{key: clean(value) for key, value in row.items()} for row in csv.DictReader(handle, delimiter="\t")]


def write_tsv(path: Path, rows: list[dict[str, str]], columns: list[str], replace: bool) -> None:
    if path.exists() and not replace:
        print(f"Skipped {repo_path(path)} because it exists. Use --replace to rebuild.")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {repo_path(path)}")


def write_json(path: Path, payload: dict[str, Any], replace: bool) -> None:
    if path.exists() and not replace:
        print(f"Skipped {repo_path(path)} because it exists. Use --replace to rebuild.")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {repo_path(path)}")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def file_type(name_or_url: str) -> str:
    path = urlparse(clean(name_or_url)).path
    name = unquote(Path(path).name or clean(name_or_url))
    if name.lower().endswith(".csv.gz"):
        return "csv.gz"
    suffix = Path(name).suffix.lower().lstrip(".")
    return suffix or "unknown"


def parser_family(name_or_url: str) -> str:
    ft = file_type(name_or_url)
    if ft in {"csv", "tsv", "tab", "txt", "csv.gz"}:
        return "csv_table_parser"
    if ft in {"xlsx", "xls"}:
        return "xlsx_workbook_parser"
    if ft == "json":
        return "json_metadata_inventory"
    if ft == "md":
        return "analysis_code_inventory"
    if ft == "zip":
        return "zip_member_inventory"
    if ft in {"rds", "rdata"}:
        return "r_data_parser"
    if ft in {"dta", "sav"}:
        return "statistical_package_parser"
    if ft in {"r", "rmd", "py", "do", "sps"}:
        return "analysis_code_inventory"
    if ft in {"pdf", "html", "htm"}:
        return "document_context_or_source_object_review"
    return "unknown"


def artifact_role(name_or_url: str, default: str = "provider_file") -> str:
    ft = file_type(name_or_url)
    lower = clean(name_or_url).lower()
    if "codebook" in lower or "dictionary" in lower:
        return "codebook"
    if ft in {"csv", "tsv", "tab", "xlsx", "xls", "json", "rds", "rdata", "dta", "sav"}:
        return "data_file"
    if ft in {"r", "rmd", "py", "do", "sps", "md"}:
        return "code_file"
    if ft == "zip":
        return "archive_file"
    if ft in {"pdf", "html", "htm"}:
        return "article_or_supplement_pdf" if ft == "pdf" else "mirrored_website_result_catalog"
    return default


def field_evidence(text: str) -> dict[str, str]:
    lower = clean(text).lower()

    def match(terms: list[str]) -> str:
        hits = [term for term in terms if term in lower]
        return "terms: " + " | ".join(hits[:12]) if hits else ""

    return {
        "pair_field_evidence": match(PAIR_TERMS),
        "n_field_evidence": match(N_TERMS),
        "effect_field_evidence": match(EFFECT_TERMS),
        "publication_link_evidence": match(PUBLICATION_TERMS),
    }


def empty_artifact(columns: list[str]) -> dict[str, str]:
    return {column: "" for column in columns}


def artifact_from_remote(
    columns: list[str],
    queue_row: dict[str, str],
    *,
    provider: str,
    provider_id: str,
    title: str,
    url: str,
    raw_url: str = "",
    doi: str = "",
    file_name: str = "",
    byte_size: str = "",
    mime_type: str = "",
    role: str = "",
    notes: str = "",
) -> dict[str, str]:
    file_name = clean(file_name) or unquote(Path(urlparse(raw_url or url).path).name) or slug(title)
    text = " ".join([title, file_name, url, raw_url, notes])
    evidence = field_evidence(text)
    row = empty_artifact(columns)
    row.update(
        {
            "artifact_id": stable_id("source_artifact", queue_row["corpus_database_id"], provider, provider_id, raw_url or url, file_name),
            "parent_corpus_database_id": queue_row["corpus_database_id"],
            "artifact_role": role or artifact_role(file_name or raw_url or url),
            "provider": provider,
            "provider_id": provider_id,
            "parent_provider_id": queue_row["corpus_database_id"],
            "title": title or file_name,
            "url": url,
            "raw_url": raw_url,
            "doi": doi,
            "component_path": "",
            "file_name": file_name,
            "file_type": file_type(file_name or raw_url or url),
            "mime_type": mime_type,
            "byte_size": byte_size,
            "inventory_status": "mirrorable" if raw_url else "inventoried_metadata_only",
            "access_status": "public_download_seen" if raw_url else "public_metadata",
            "candidate_parser_family": parser_family(file_name or raw_url or url),
            "pair_field_evidence": evidence["pair_field_evidence"],
            "n_field_evidence": evidence["n_field_evidence"],
            "effect_field_evidence": evidence["effect_field_evidence"],
            "publication_link_evidence": doi or evidence["publication_link_evidence"],
            "blocker_codes": "needs_download" if raw_url else "metadata_only",
            "next_action": "mirror_sample_and_route_parser_candidate" if raw_url else "inspect_metadata_for_downloadable_result_artifacts",
            "notes": clean(notes),
            "last_seen": today(),
        }
    )
    return row


def artifact_from_local(columns: list[str], queue_row: dict[str, str], path: Path, notes: str = "") -> dict[str, str]:
    stat = path.stat()
    checksum = sha256_file(path)
    rel = repo_path(path)
    evidence = field_evidence(path.name)
    row = empty_artifact(columns)
    row.update(
        {
            "artifact_id": stable_id("source_artifact", queue_row["corpus_database_id"], rel, checksum),
            "parent_corpus_database_id": queue_row["corpus_database_id"],
            "artifact_role": artifact_role(path.name, default="local_mirror"),
            "provider": "local_file",
            "provider_id": rel,
            "parent_provider_id": queue_row["corpus_database_id"],
            "title": path.name,
            "component_path": repo_path(path.parent),
            "file_name": path.name,
            "file_type": file_type(path.name),
            "mime_type": clean(mimetypes.guess_type(path.name)[0]),
            "byte_size": str(stat.st_size),
            "local_path": rel,
            "sha256": checksum,
            "inventory_status": "mirrored",
            "access_status": "downloaded",
            "candidate_parser_family": parser_family(path.name),
            "pair_field_evidence": evidence["pair_field_evidence"],
            "n_field_evidence": evidence["n_field_evidence"],
            "effect_field_evidence": evidence["effect_field_evidence"],
            "publication_link_evidence": evidence["publication_link_evidence"],
            "blocker_codes": "",
            "next_action": "sample_and_route_parser_candidate",
            "notes": clean(notes),
            "last_seen": today(),
        }
    )
    return row


def make_session() -> requests.Session:
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT, "Accept": "application/json,text/html;q=0.8,*/*;q=0.5"})
    return session


def get_json(session: requests.Session, url: str, timeout: int = 30) -> tuple[dict[str, Any] | list[Any] | None, str, int]:
    try:
        response = session.get(url, timeout=timeout)
        status = response.status_code
        if not response.ok:
            return None, clean(response.text, 1000), status
        return response.json(), "", status
    except (requests.RequestException, json.JSONDecodeError) as exc:
        return None, clean(exc, 1000), 0


def extract_osf_guid(url: str) -> str:
    guids = extract_osf_guids(url)
    return guids[0] if guids else ""


def extract_osf_guids(text: str) -> list[str]:
    seen: set[str] = set()
    guids: list[str] = []
    for match in re.finditer(r"osf\.io/(?:download/)?([a-z0-9]{5})", clean(text), flags=re.IGNORECASE):
        guid = match.group(1).lower()
        if guid not in seen:
            seen.add(guid)
            guids.append(guid)
    return guids


def osf_file_rows(
    session: requests.Session,
    columns: list[str],
    queue_row: dict[str, str],
    *,
    max_files: int,
) -> tuple[list[dict[str, str]], dict[str, str]]:
    guids = extract_osf_guids(" | ".join([queue_row.get("landing_url", ""), queue_row.get("raw_url", ""), queue_row.get("source_key", "")]))
    if not guids:
        return [], attempt(queue_row, "osf_inventory", "failed", "no_osf_guid")
    rows: list[dict[str, str]] = []
    details: list[str] = []
    stack: list[tuple[str, str, str]] = []
    for guid in guids:
        providers_url = f"https://api.osf.io/v2/nodes/{guid}/files/"
        payload, error, status = get_json(session, providers_url)
        if not isinstance(payload, dict):
            details.append(f"{guid}:failed:{error or f'http_status={status}'}")
            continue
        details.append(f"{guid}:providers={len(payload.get('data') or [])}")
        for provider in payload.get("data") or []:
            provider_name = clean((provider.get("attributes") or {}).get("name")) or clean(provider.get("id"))
            related = (((provider.get("relationships") or {}).get("files") or {}).get("links") or {}).get("related", {})
            href = clean(related.get("href") if isinstance(related, dict) else related)
            if href:
                stack.append((guid, provider_name, href))
    seen_urls: set[str] = set()
    while stack and len(rows) < max_files:
        guid, provider_name, listing_url = stack.pop()
        if listing_url in seen_urls:
            continue
        seen_urls.add(listing_url)
        listing, error, status = get_json(session, listing_url)
        if not isinstance(listing, dict):
            continue
        for item in listing.get("data") or []:
            attrs = item.get("attributes") or {}
            links = item.get("links") or {}
            relationships = item.get("relationships") or {}
            kind = clean(attrs.get("kind"))
            name = clean(attrs.get("name") or item.get("id"))
            path = clean(attrs.get("path"))
            if kind == "folder":
                files_link = ((relationships.get("files") or {}).get("links") or {}).get("related", {})
                href = clean(files_link.get("href") if isinstance(files_link, dict) else files_link)
                if href:
                    stack.append((guid, provider_name, href))
                continue
            download_url = clean(links.get("download"))
            html_url = clean(links.get("html") or links.get("info"))
            rows.append(
                artifact_from_remote(
                    columns,
                    queue_row,
                    provider="osf",
                    provider_id=clean(item.get("id")),
                    title=name,
                    url=html_url or listing_url,
                    raw_url=download_url,
                    file_name=name,
                    byte_size=clean(attrs.get("size")),
                    role="data_file" if file_type(name) in DOWNLOADABLE_EXTS else "provider_file",
                    notes=f"osf_node={guid}; osf_provider={provider_name}; osf_path={path}",
                )
            )
            if len(rows) >= max_files:
                break
        next_link = (listing.get("links") or {}).get("next")
        if next_link:
            stack.append((guid, provider_name, clean(next_link)))
    status_text = "success" if rows else "no_files_found"
    return rows, attempt(queue_row, "osf_inventory", status_text, " | ".join(details + [f"files={len(rows)}"]))


def extract_dataverse_pid(row: dict[str, str]) -> str:
    text = " ".join([row.get("landing_url", ""), row.get("raw_url", ""), row.get("source_key", "")])
    match = re.search(r"10\.7910/DVN/[A-Za-z0-9_.-]+", text, flags=re.IGNORECASE)
    return match.group(0) if match else ""


def dataverse_file_rows(session: requests.Session, columns: list[str], queue_row: dict[str, str]) -> tuple[list[dict[str, str]], dict[str, str]]:
    pid = extract_dataverse_pid(queue_row)
    if not pid:
        return [], attempt(queue_row, "dataverse_inventory", "failed", "no_dataverse_persistent_id")
    api = f"https://dataverse.harvard.edu/api/datasets/:persistentId?persistentId=doi:{pid}"
    payload, error, status = get_json(session, api)
    if not isinstance(payload, dict) or payload.get("status") != "OK":
        return [], attempt(queue_row, "dataverse_inventory", "failed", error or f"http_status={status}", api)
    dataset = payload.get("data") or {}
    version = dataset.get("latestVersion") or {}
    rows: list[dict[str, str]] = []
    for file_item in version.get("files") or []:
        data_file = file_item.get("dataFile") or {}
        file_id = clean(data_file.get("id"))
        label = clean(data_file.get("filename") or data_file.get("label") or file_id)
        raw_url = f"https://dataverse.harvard.edu/api/access/datafile/{file_id}?format=original" if file_id else ""
        rows.append(
            artifact_from_remote(
                columns,
                queue_row,
                provider="dataverse",
                provider_id=file_id,
                title=label,
                url=f"https://dataverse.harvard.edu/file.xhtml?fileId={file_id}" if file_id else api,
                raw_url=raw_url,
                doi=f"doi:{pid}",
                file_name=label,
                byte_size=clean(data_file.get("filesize")),
                mime_type=clean(data_file.get("contentType")),
                notes=f"dataverse_pid=doi:{pid}",
            )
        )
    return rows, attempt(queue_row, "dataverse_inventory", "success" if rows else "no_files_found", f"files={len(rows)}", api)


def extract_zenodo_record_id(row: dict[str, str]) -> str:
    text = " ".join([row.get("landing_url", ""), row.get("raw_url", ""), row.get("source_key", "")])
    for pattern in [r"zenodo\.(?:org|record)/records?/(\d+)", r"10\.5281/zenodo\.(\d+)"]:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return match.group(1)
    return ""


def zenodo_file_rows(session: requests.Session, columns: list[str], queue_row: dict[str, str]) -> tuple[list[dict[str, str]], dict[str, str]]:
    record_id = extract_zenodo_record_id(queue_row)
    if not record_id:
        return [], attempt(queue_row, "zenodo_inventory", "failed", "no_zenodo_record_id")
    api = f"https://zenodo.org/api/records/{record_id}"
    payload, error, status = get_json(session, api)
    if not isinstance(payload, dict):
        return [], attempt(queue_row, "zenodo_inventory", "failed", error or f"http_status={status}", api)
    rows = []
    doi = clean(payload.get("doi"))
    for item in payload.get("files") or []:
        links = item.get("links") or {}
        key = clean(item.get("key"))
        rows.append(
            artifact_from_remote(
                columns,
                queue_row,
                provider="zenodo",
                provider_id=f"{record_id}:{key}",
                title=key,
                url=clean(links.get("self") or (payload.get("links") or {}).get("html")),
                raw_url=clean(links.get("self")),
                doi=doi,
                file_name=key,
                byte_size=clean(item.get("size")),
                notes=f"zenodo_record={record_id}; provider_checksum={clean(item.get('checksum'))}",
            )
        )
    return rows, attempt(queue_row, "zenodo_inventory", "success" if rows else "no_files_found", f"files={len(rows)}", api)


def extract_figshare_article_id(row: dict[str, str]) -> str:
    text = " ".join([row.get("landing_url", ""), row.get("raw_url", ""), row.get("source_key", "")])
    match = re.search(r"figshare\.com/articles/(?:[^/]+/)?(\d+)", text, flags=re.IGNORECASE)
    return match.group(1) if match else ""


def figshare_file_rows(session: requests.Session, columns: list[str], queue_row: dict[str, str]) -> tuple[list[dict[str, str]], dict[str, str]]:
    article_id = extract_figshare_article_id(queue_row)
    if not article_id:
        return [], attempt(queue_row, "figshare_inventory", "failed", "no_figshare_article_id")
    api = f"https://api.figshare.com/v2/articles/{article_id}"
    payload, error, status = get_json(session, api)
    if not isinstance(payload, dict):
        return [], attempt(queue_row, "figshare_inventory", "failed", error or f"http_status={status}", api)
    rows = []
    doi = clean(payload.get("doi"))
    for item in payload.get("files") or []:
        name = clean(item.get("name"))
        rows.append(
            artifact_from_remote(
                columns,
                queue_row,
                provider="figshare",
                provider_id=clean(item.get("id")),
                title=name,
                url=clean(item.get("download_url") or payload.get("url_public_html") or api),
                raw_url=clean(item.get("download_url")),
                doi=doi,
                file_name=name,
                byte_size=clean(item.get("size")),
                notes=f"figshare_article={article_id}",
            )
        )
    return rows, attempt(queue_row, "figshare_inventory", "success" if rows else "no_files_found", f"files={len(rows)}", api)


def doi_from_url(url: str) -> str:
    text = clean(url)
    match = re.search(r"10\.\d{4,9}/[^\s|]+", text, flags=re.IGNORECASE)
    if not match:
        return ""
    return match.group(0).rstrip(").,;")


def article_link_rows(
    session: requests.Session,
    columns: list[str],
    queue_row: dict[str, str],
    *,
    max_links: int,
    timeout: int,
) -> tuple[list[dict[str, str]], dict[str, str]]:
    doi = doi_from_url(queue_row.get("landing_url", "")) or doi_from_url(queue_row.get("raw_url", ""))
    url = queue_row.get("landing_url") or queue_row.get("raw_url")
    candidates: list[tuple[str, str, str]] = []
    errors: list[str] = []
    if doi:
        crossref_url = f"https://api.crossref.org/works/{quote(doi, safe='')}"
        payload, error, status = get_json(session, crossref_url, timeout=timeout)
        if isinstance(payload, dict):
            message = payload.get("message") or {}
            for link in message.get("link") or []:
                link_url = clean(link.get("URL"))
                if link_url:
                    candidates.append((link_url, clean(link.get("content-type")), "crossref_link"))
            for rel_type, rels in (message.get("relation") or {}).items():
                for rel in rels:
                    rel_id = clean(rel.get("id"))
                    if rel_id.startswith("10."):
                        candidates.append((f"https://doi.org/{rel_id}", "", f"crossref_relation:{rel_type}"))
        elif error:
            errors.append(f"crossref={error}")
    if url:
        try:
            response = session.get(url, timeout=timeout, headers={"Accept": "text/html,*/*;q=0.8"})
            final_url = response.url
            if response.ok:
                html_text = response.text[:2_000_000]
                hrefs = re.findall(r"""href=["']([^"']+)["']""", html_text, flags=re.IGNORECASE)
                for href in hrefs:
                    full = html.unescape(urljoin(final_url, href))
                    lower = full.lower()
                    anchor_context = full
                    if any(token in lower for token in ["supp", "data", "download", "osf.io", "figshare", "zenodo", "dataverse", "dryad", "github", ".csv", ".xlsx", ".zip", ".pdf"]):
                        candidates.append((full, "", "landing_page_link"))
            else:
                errors.append(f"landing_http={response.status_code}")
        except requests.RequestException as exc:
            errors.append(f"landing={clean(exc, 500)}")
    seen: set[str] = set()
    rows: list[dict[str, str]] = []
    for link_url, content_type, source in candidates:
        if link_url in seen or len(rows) >= max_links:
            continue
        seen.add(link_url)
        parsed = urlparse(link_url)
        name = unquote(Path(parsed.path).name) or slug(link_url)
        ft = file_type(link_url)
        raw_url = link_url if ft in DOWNLOADABLE_EXTS else ""
        host = parsed.netloc.lower()
        provider = "article_link"
        if "osf.io" in host:
            provider = "osf"
        elif "figshare" in host:
            provider = "figshare"
        elif "zenodo" in host:
            provider = "zenodo"
        elif "dataverse" in host:
            provider = "dataverse"
        elif "github.com" in host:
            provider = "github"
        rows.append(
            artifact_from_remote(
                columns,
                queue_row,
                provider=provider,
                provider_id=link_url,
                title=name,
                url=link_url,
                raw_url=raw_url,
                doi=doi,
                file_name=name,
                mime_type=content_type,
                role=artifact_role(link_url, default="source_family_page"),
                notes=f"{source}; source_doi={doi}",
            )
        )
    status_text = "success" if rows else "no_candidate_links"
    return rows, attempt(queue_row, "article_pdf_supplement_or_data_availability", status_text, " | ".join(errors) or f"links={len(rows)}", url)


def direct_rows(columns: list[str], queue_row: dict[str, str]) -> tuple[list[dict[str, str]], dict[str, str]]:
    rows: list[dict[str, str]] = []
    for value in [queue_row.get("raw_url", ""), queue_row.get("landing_url", ""), queue_row.get("existing_local_paths", "")]:
        for part in re.split(r"\s*\|\s*", clean(value)):
            if not part:
                continue
            path = resolve_path(part)
            if path.exists() and path.is_file():
                rows.append(artifact_from_local(columns, queue_row, path, notes="direct local path from acquisition queue"))
            elif urlparse(part).scheme in {"http", "https"}:
                rows.append(
                    artifact_from_remote(
                        columns,
                        queue_row,
                        provider="direct_url",
                        provider_id=part,
                        title=unquote(Path(urlparse(part).path).name) or queue_row.get("name", ""),
                        url=part,
                        raw_url=part,
                        file_name=unquote(Path(urlparse(part).path).name),
                        notes="direct URL from acquisition queue",
                    )
                )
    return rows, attempt(queue_row, "direct_download_or_api_snapshot", "success" if rows else "no_direct_artifact", f"artifacts={len(rows)}")


def landing_snapshot_row(session: requests.Session, columns: list[str], queue_row: dict[str, str], out_root: Path, timeout: int) -> tuple[list[dict[str, str]], dict[str, str]]:
    url = queue_row.get("landing_url") or queue_row.get("raw_url")
    if not url or urlparse(url).scheme not in {"http", "https"}:
        return [], attempt(queue_row, "landing_page_snapshot", "failed", "no_http_url")
    target_dir = out_root / "landing_snapshots" / slug(queue_row["corpus_database_id"])
    target_dir.mkdir(parents=True, exist_ok=True)
    out_path = target_dir / "landing.html"
    meta_path = target_dir / "landing_metadata.json"
    try:
        response = session.get(url, timeout=timeout, headers={"Accept": "text/html,*/*;q=0.8"})
        payload = response.text
        out_path.write_text(payload, encoding="utf-8", errors="replace")
        meta_path.write_text(
            json.dumps(
                {
                    "url": url,
                    "final_url": response.url,
                    "status_code": response.status_code,
                    "content_type": response.headers.get("content-type", ""),
                    "retrieved_at": datetime.now().isoformat(timespec="seconds"),
                },
                indent=2,
                sort_keys=True,
            ),
            encoding="utf-8",
        )
    except requests.RequestException as exc:
        return [], attempt(queue_row, "landing_page_snapshot", "failed", clean(exc, 1000), url)
    row = artifact_from_local(columns, queue_row, out_path, notes=f"landing page snapshot; original_url={url}")
    row["artifact_role"] = "mirrored_website_result_catalog"
    row["url"] = url
    row["raw_url"] = ""
    row["candidate_parser_family"] = "document_context_or_source_object_review"
    row["blocker_codes"] = "needs_result_catalog_review"
    row["next_action"] = "inspect_landing_snapshot_for_downloads_or_result_table"
    return [row], attempt(queue_row, "landing_page_snapshot", "success", f"status={response.status_code}", url)


def attempt(queue_row: dict[str, str], strategy: str, status: str, detail: str = "", url: str = "") -> dict[str, str]:
    return {
        "attempt_id": stable_id("result_artifact_attempt", queue_row["plot_label"], queue_row["corpus_database_id"], strategy, url, status),
        "plot_label": queue_row.get("plot_label", ""),
        "corpus_database_id": queue_row.get("corpus_database_id", ""),
        "name": queue_row.get("name", ""),
        "acquisition_route_type": queue_row.get("acquisition_route_type", ""),
        "strategy": strategy,
        "status": status,
        "detail": clean(detail, 3000),
        "url": url,
        "attempted_at": datetime.now().isoformat(timespec="seconds"),
    }


def merge_artifacts(rows: list[dict[str, str]], columns: list[str]) -> list[dict[str, str]]:
    by_key: dict[str, dict[str, str]] = {}
    for row in rows:
        key = f"{row.get('parent_corpus_database_id')}::{row.get('raw_url') or row.get('local_path') or row.get('url') or row.get('artifact_id')}"
        if key not in by_key:
            by_key[key] = {column: row.get(column, "") for column in columns}
            continue
        existing = by_key[key]
        for column in columns:
            if not existing.get(column) and row.get(column):
                existing[column] = row[column]
        if row.get("notes") and row["notes"] not in existing.get("notes", ""):
            existing["notes"] = " | ".join(part for part in [existing.get("notes"), row.get("notes")] if part)
    return sorted(by_key.values(), key=lambda row: (row.get("parent_corpus_database_id", ""), row.get("file_name", ""), row.get("raw_url", "")))


def manual_task(queue_row: dict[str, str], reason: str) -> dict[str, str]:
    return {
        "manual_task_id": stable_id("manual_result_artifact_task", queue_row["plot_label"], queue_row["corpus_database_id"], reason),
        "plot_label": queue_row.get("plot_label", ""),
        "corpus_database_id": queue_row.get("corpus_database_id", ""),
        "name": queue_row.get("name", ""),
        "route": queue_row.get("acquisition_route_type", ""),
        "reason": reason,
        "landing_url": queue_row.get("landing_url", ""),
        "raw_url": queue_row.get("raw_url", ""),
        "suggested_action": queue_row.get("next_action", ""),
        "notes": "Manual/browser/library/source-specific work needed to identify the local result-bearing artifact.",
    }


def run_for_row(
    session: requests.Session,
    columns: list[str],
    queue_row: dict[str, str],
    out_root: Path,
    args: argparse.Namespace,
) -> tuple[list[dict[str, str]], list[dict[str, str]], list[dict[str, str]]]:
    route = queue_row.get("acquisition_route_type", "")
    artifacts: list[dict[str, str]] = []
    attempts: list[dict[str, str]] = []
    manual: list[dict[str, str]] = []
    if route == "osf_inventory_and_download":
        rows, att = osf_file_rows(session, columns, queue_row, max_files=args.max_files_per_source)
        artifacts.extend(rows)
        attempts.append(att)
    elif route == "dataverse_inventory_and_download":
        rows, att = dataverse_file_rows(session, columns, queue_row)
        artifacts.extend(rows)
        attempts.append(att)
    elif route == "zenodo_record_file_download":
        rows, att = zenodo_file_rows(session, columns, queue_row)
        artifacts.extend(rows)
        attempts.append(att)
    elif route == "figshare_record_file_download":
        rows, att = figshare_file_rows(session, columns, queue_row)
        artifacts.extend(rows)
        attempts.append(att)
    elif route in {"direct_download_or_api_snapshot", "repository_or_package_discovery"}:
        rows, att = direct_rows(columns, queue_row)
        artifacts.extend(rows)
        attempts.append(att)
    elif route == "article_pdf_supplement_or_data_availability_route":
        rows, att = article_link_rows(session, columns, queue_row, max_links=args.max_links_per_article, timeout=args.timeout)
        artifacts.extend(rows)
        attempts.append(att)
        if not any(row.get("raw_url") for row in rows):
            manual.append(manual_task(queue_row, "article_route_no_downloadable_result_artifact_found"))
    elif route == "landing_page_inventory_or_manual_resolution":
        rows, att = landing_snapshot_row(session, columns, queue_row, out_root, args.timeout)
        artifacts.extend(rows)
        attempts.append(att)
        manual.append(manual_task(queue_row, "landing_page_snapshot_needs_human_or_codex_review"))
    else:
        manual.append(manual_task(queue_row, f"route_not_implemented:{route}"))
        attempts.append(attempt(queue_row, route or "unknown", "not_implemented"))
    if not artifacts and not manual:
        manual.append(manual_task(queue_row, "no_artifacts_found"))
    return artifacts, attempts, manual


def output_paths(plot_label: str, output_root: Path | None = None, output_prefix: str = "") -> tuple[Path, Path, Path, Path, Path, Path]:
    root = output_root or ROOT / "steps" / "source_inventory" / plot_label / "result_artifact_acquisition"
    prefix = output_prefix or f"{plot_label}-result-artifact-acquisition"
    return (
        root,
        root / f"{prefix}-artifacts-proposal.tsv",
        root / f"{prefix}-artifacts-proposal.json",
        root / f"{prefix}-attempts.tsv",
        root / f"{prefix}-manual-tasks.tsv",
        root / f"{prefix}-strategy-summary.tsv",
    )


def summary_rows(artifacts: list[dict[str, str]], attempts: list[dict[str, str]], manual: list[dict[str, str]]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for field, source_rows in [
        ("attempt_status", attempts),
        ("attempt_strategy", attempts),
        ("artifact_provider", artifacts),
        ("artifact_role", artifacts),
        ("candidate_parser_family", artifacts),
        ("manual_reason", manual),
    ]:
        key_field = {
            "attempt_status": "status",
            "attempt_strategy": "strategy",
            "artifact_provider": "provider",
            "artifact_role": "artifact_role",
            "candidate_parser_family": "candidate_parser_family",
            "manual_reason": "reason",
        }[field]
        counts: dict[str, int] = {}
        for row in source_rows:
            key = row.get(key_field, "") or "<blank>"
            counts[key] = counts.get(key, 0) + 1
        for key, count in sorted(counts.items()):
            rows.append({"metric": field, "value": key, "count": str(count)})
    rows.extend(
        [
            {"metric": "total", "value": "artifact_rows", "count": str(len(artifacts))},
            {"metric": "total", "value": "attempt_rows", "count": str(len(attempts))},
            {"metric": "total", "value": "manual_task_rows", "count": str(len(manual))},
            {"metric": "total", "value": "downloadable_artifact_rows", "count": str(sum(1 for row in artifacts if row.get("raw_url")))},
        ]
    )
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plot-label", default="figure1")
    parser.add_argument("--queue", default="")
    parser.add_argument("--output-root", default="")
    parser.add_argument("--output-prefix", default="")
    parser.add_argument("--replace", action="store_true")
    parser.add_argument("--max-sources", type=int, default=0, help="Optional cap for quick smoke runs.")
    parser.add_argument("--max-files-per-source", type=int, default=250)
    parser.add_argument("--max-links-per-article", type=int, default=30)
    parser.add_argument("--timeout", type=int, default=25)
    args = parser.parse_args()

    queue_path = resolve_path(args.queue) if args.queue else ROOT / "steps" / "source_inventory" / args.plot_label / "result_artifact_acquisition" / f"{args.plot_label}-result-artifact-acquisition-queue.tsv"
    out_root_override = resolve_path(args.output_root) if args.output_root else None
    out_root, proposal_tsv, proposal_json, attempts_tsv, manual_tsv, summary_tsv = output_paths(args.plot_label, out_root_override, args.output_prefix)
    columns = source_artifact_columns()
    queue_rows = [
        row
        for row in read_tsv(queue_path)
        if row.get("result_artifact_acquisition_state") == "needs_result_bearing_artifact_on_disk"
    ]
    if args.max_sources:
        queue_rows = queue_rows[: args.max_sources]
    session = make_session()
    artifacts: list[dict[str, str]] = []
    attempts: list[dict[str, str]] = []
    manual: list[dict[str, str]] = []
    for row in queue_rows:
        new_artifacts, new_attempts, new_manual = run_for_row(session, columns, row, out_root, args)
        artifacts.extend(new_artifacts)
        attempts.extend(new_attempts)
        manual.extend(new_manual)
    artifacts = merge_artifacts(artifacts, columns)
    attempt_columns = ["attempt_id", "plot_label", "corpus_database_id", "name", "acquisition_route_type", "strategy", "status", "detail", "url", "attempted_at"]
    manual_columns = ["manual_task_id", "plot_label", "corpus_database_id", "name", "route", "reason", "landing_url", "raw_url", "suggested_action", "notes"]
    summary = summary_rows(artifacts, attempts, manual)
    write_tsv(proposal_tsv, artifacts, columns, args.replace)
    write_json(
        proposal_json,
        {
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "queue": repo_path(queue_path),
            "queue_rows_processed": len(queue_rows),
            "artifact_rows": len(artifacts),
            "attempt_rows": len(attempts),
            "manual_task_rows": len(manual),
            "artifacts": artifacts,
            "attempts": attempts,
            "manual_tasks": manual,
        },
        args.replace,
    )
    write_tsv(attempts_tsv, attempts, attempt_columns, args.replace)
    write_tsv(manual_tsv, manual, manual_columns, args.replace)
    write_tsv(summary_tsv, summary, ["metric", "value", "count"], args.replace)
    print(
        f"{args.plot_label} result-artifact strategies: "
        f"queue_rows={len(queue_rows)}; artifacts={len(artifacts)}; "
        f"downloadable={sum(1 for row in artifacts if row.get('raw_url'))}; manual_tasks={len(manual)}"
    )


if __name__ == "__main__":
    main()
