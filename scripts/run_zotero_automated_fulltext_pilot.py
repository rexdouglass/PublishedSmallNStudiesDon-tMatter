#!/usr/bin/env python3
"""Try Zotero's automated full-text paths on blocked pilot rows.

This is intentionally scoped to the dedicated local Zotero profile/data
directory. It does not write Zotero SQLite directly. Instead it talks to:

* translation-server on localhost:1969 for DOI/title metadata translation.
* Zotero desktop connector server on localhost:23119 for saveItems/savePage.

Any downloaded attachment bytes are copied into the local cache and then passed
through the same full-article identity gate used by
resolve_full_article_text_candidates_pilot.py before promotion.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import mimetypes
import os
import shutil
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests


ROOT = Path(__file__).resolve().parents[1]
PILOT = ROOT / "data" / "derived" / "effect_inflation_dataset" / "schema_pilot"
SAMPLE_N = int(os.environ.get("SCHEMA_PILOT_N", "300"))
SAMPLE_SUFFIX = f"sample_{SAMPLE_N}"
WORKLIST = PILOT / f"remaining_full_article_worklist_after_core_{SAMPLE_SUFFIX}.tsv"
SOURCE = PILOT / f"source_codebook_{SAMPLE_SUFFIX}.tsv"
SOURCE_IDENTIFIER = PILOT / f"source_identifier_codebook_{SAMPLE_SUFFIX}.tsv"
SOURCE_RESULT = PILOT / f"source_result_codebook_{SAMPLE_SUFFIX}.tsv"
SOURCE_FILE = PILOT / f"source_file_codebook_{SAMPLE_SUFFIX}.tsv"
SOURCE_ACCESS = PILOT / f"source_access_codebook_{SAMPLE_SUFFIX}.tsv"
SOURCE_ACCESS_ATTEMPT = PILOT / f"source_access_attempt_codebook_{SAMPLE_SUFFIX}.tsv"
SOURCE_ACCESS_RIGHT = PILOT / f"source_access_right_codebook_{SAMPLE_SUFFIX}.tsv"
SOURCE_VERSION = PILOT / f"source_version_codebook_{SAMPLE_SUFFIX}.tsv"
SOURCE_OBJECT_CANDIDATE = PILOT / f"source_object_candidate_codebook_{SAMPLE_SUFFIX}.tsv"

RUN_ID = f"zotero_auto_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
ZOTERO_DATA_DIR = ROOT / ".local" / "zotero-oa-data"
ZOTERO_STORAGE = ZOTERO_DATA_DIR / "storage"
HANDOFF_CACHE = ROOT / "data" / "cache" / "manual_acquisition" / "zotero_desktop_bulk" / RUN_ID
OUT_ATTEMPTS = PILOT / f"zotero_automated_fulltext_attempts_{SAMPLE_SUFFIX}_{RUN_ID}.tsv"
OUT_SUMMARY = PILOT / f"zotero_automated_fulltext_summary_{SAMPLE_SUFFIX}_{RUN_ID}.tsv"
OUT_REPORT = ROOT / "reports" / f"zotero_automated_fulltext_{SAMPLE_SUFFIX}_{RUN_ID}.md"

TRANSLATION_SERVER = "http://127.0.0.1:1969"
ZOTERO_CONNECTOR = "http://127.0.0.1:23119"
HEADERS = {
    "X-Zotero-Version": "5.0.200",
    "X-Zotero-Connector-API-Version": "3",
}
UA = "oa-fulltext-pipeline/0.1 (mailto:rexdouglass@gmail.com)"

resolver_path = ROOT / "scripts" / "resolve_full_article_text_candidates_pilot.py"
spec = importlib.util.spec_from_file_location("full_article_resolver", resolver_path)
resolver = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(resolver)


def safe_text(value: object) -> str:
    if value is None:
        return ""
    return str(value).replace("\t", " ").replace("\r", " ").replace("\n", " ").strip()


def sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def storage_files() -> set[Path]:
    if not ZOTERO_STORAGE.exists():
        return set()
    return {
        path
        for path in ZOTERO_STORAGE.rglob("*")
        if path.is_file() and path.suffix.lower() in {".pdf", ".html", ".htm", ".xml", ".epub"}
    }


def request_translation_search(query: str) -> tuple[list[dict], str]:
    if not query:
        return [], "empty_query"
    try:
        response = requests.post(
            f"{TRANSLATION_SERVER}/search",
            data=query.encode("utf-8"),
            headers={"Content-Type": "text/plain", "User-Agent": UA},
            timeout=45,
        )
        if response.status_code != 200:
            return [], f"http_{response.status_code}"
        data = response.json()
        return data if isinstance(data, list) else [], "ok"
    except Exception as exc:  # noqa: BLE001
        return [], f"exception:{type(exc).__name__}:{exc}"


def request_translation_web(url: str) -> tuple[list[dict], str]:
    if not url:
        return [], "empty_url"
    try:
        response = requests.post(
            f"{TRANSLATION_SERVER}/web",
            data=url.encode("utf-8"),
            headers={"Content-Type": "text/plain", "User-Agent": UA},
            timeout=60,
        )
        if response.status_code != 200:
            return [], f"http_{response.status_code}"
        data = response.json()
        return data if isinstance(data, list) else [], "ok"
    except Exception as exc:  # noqa: BLE001
        return [], f"exception:{type(exc).__name__}:{exc}"


def fetch_html(url: str) -> tuple[str, str]:
    if not url:
        return "", "empty_url"
    try:
        response = requests.get(url, headers={"User-Agent": UA, "Accept": "text/html,*/*;q=0.8"}, timeout=35)
        ctype = response.headers.get("content-type", "")
        if response.status_code >= 400:
            return "", f"http_{response.status_code}"
        if "html" not in ctype.lower():
            return "", f"not_html:{ctype}"
        return response.text, "ok"
    except Exception as exc:  # noqa: BLE001
        return "", f"exception:{type(exc).__name__}:{exc}"


def poll_session(session_id: str, max_wait_seconds: int = 90) -> dict:
    deadline = time.monotonic() + max_wait_seconds
    last: dict = {}
    while time.monotonic() < deadline:
        try:
            response = requests.post(
                f"{ZOTERO_CONNECTOR}/connector/sessionProgress",
                json={"sessionID": session_id},
                headers=HEADERS,
                timeout=15,
            )
            if response.status_code == 200:
                last = response.json()
                if last.get("done"):
                    return last
        except Exception as exc:  # noqa: BLE001
            last = {"error": f"{type(exc).__name__}:{exc}"}
        time.sleep(2)
    last.setdefault("done", False)
    last.setdefault("error", "timeout")
    return last


def zotero_save_items(items: list[dict], uri: str) -> tuple[int, str, dict]:
    session_id = str(uuid.uuid4())
    payload = {"sessionID": session_id, "uri": uri, "items": items}
    try:
        response = requests.post(
            f"{ZOTERO_CONNECTOR}/connector/saveItems",
            json=payload,
            headers=HEADERS,
            timeout=120,
        )
        progress = poll_session(session_id)
        return response.status_code, response.text, progress
    except Exception as exc:  # noqa: BLE001
        return 0, f"{type(exc).__name__}:{exc}", {"done": False, "error": str(exc)}


def zotero_save_page(uri: str, html: str) -> tuple[int, str, dict]:
    session_id = str(uuid.uuid4())
    payload = {"sessionID": session_id, "uri": uri, "html": html}
    try:
        response = requests.post(
            f"{ZOTERO_CONNECTOR}/connector/savePage",
            json=payload,
            headers=HEADERS,
            timeout=120,
        )
        progress = poll_session(session_id)
        return response.status_code, response.text, progress
    except Exception as exc:  # noqa: BLE001
        return 0, f"{type(exc).__name__}:{exc}", {"done": False, "error": str(exc)}


def attachment_count(progress: dict) -> int:
    count = 0
    for item in progress.get("items") or []:
        count += len(item.get("attachments") or [])
    return count


def copy_new_files(paths: set[Path], row_id: str) -> list[Path]:
    copied = []
    dest_dir = HANDOFF_CACHE / row_id
    dest_dir.mkdir(parents=True, exist_ok=True)
    for path in sorted(paths):
        dest = dest_dir / f"{path.parent.name}_{path.name}"
        shutil.copy2(path, dest)
        copied.append(dest)
    return copied


def attempt_from_file(row: pd.Series, source_input: dict[str, str], path: Path, route: str, candidate_url: str) -> dict[str, object]:
    content = path.read_bytes()
    content_type = mimetypes.guess_type(path.name)[0] or ""
    byte_class, extension = resolver.classify_content(content, content_type, candidate_url)
    identity_decision, identity_reason, _text, title_cov = resolver.identity_check(
        source_input,
        byte_class,
        content,
        content_type,
        candidate_url,
        resolver.normalize_doi(source_input.get("doi", "")),
        False,
    )
    sha = sha256_bytes(content)
    local_path = ""
    if identity_decision == "accepted_full_article_text":
        local_path, sha = resolver.write_artifact(row["source_result_id"], route, byte_class, extension, content)
    return {
        "source_result_id": row["source_result_id"],
        "represented_source_id": row["represented_source_id"],
        "route": route,
        "route_family": "zotero",
        "api_url": ZOTERO_CONNECTOR,
        "api_record_id": RUN_ID,
        "candidate_url": candidate_url,
        "final_url": str(path),
        "http_status": "local_file",
        "content_type": content_type,
        "byte_count": str(len(content)),
        "source_byte_class": byte_class,
        "local_path": local_path,
        "sha256": sha,
        "identity_decision": identity_decision or "not_accepted",
        "identity_reason": identity_reason,
        "title_token_coverage": title_cov,
        "candidate_doi": resolver.normalize_doi(source_input.get("doi", "")),
        "candidate_relation_type": "zotero_desktop_attachment",
        "candidate_title": source_input.get("title", ""),
        "primary_doi": source_input.get("doi", ""),
        "failure_code": "" if identity_decision == "accepted_full_article_text" else "zotero_identity_failed",
        "download_attempted": "true",
    }


def metadata_attempt(row: pd.Series, source_input: dict[str, str], route: str, detail: str, status: str, candidate_url: str = "") -> dict[str, object]:
    return {
        "source_result_id": row["source_result_id"],
        "represented_source_id": row["represented_source_id"],
        "route": route,
        "route_family": "zotero",
        "api_url": ZOTERO_CONNECTOR if route.startswith("zotero_desktop") else TRANSLATION_SERVER,
        "api_record_id": RUN_ID,
        "candidate_url": candidate_url or ("https://doi.org/" + source_input.get("doi", "") if source_input.get("doi") else ""),
        "final_url": "",
        "http_status": status,
        "content_type": "application/json",
        "byte_count": "0",
        "source_byte_class": "metadata_only",
        "local_path": "",
        "sha256": "",
        "identity_decision": "not_accepted",
        "identity_reason": detail,
        "title_token_coverage": 0.0,
        "candidate_doi": source_input.get("doi", ""),
        "candidate_relation_type": "metadata_only",
        "candidate_title": source_input.get("title", ""),
        "primary_doi": source_input.get("doi", ""),
        "failure_code": detail,
        "download_attempted": "false",
    }


def write_tsv(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, sep="\t", index=False)


def main() -> None:
    worklist = pd.read_csv(WORKLIST, sep="\t", dtype=str, keep_default_na=False)
    worklist = worklist[worklist["next_bucket"].eq("needs_manual_capture")].copy()
    source_result = pd.read_csv(SOURCE_RESULT, sep="\t", dtype=str, keep_default_na=False)
    sources = pd.read_csv(SOURCE, sep="\t", dtype=str, keep_default_na=False)
    identifiers = pd.read_csv(SOURCE_IDENTIFIER, sep="\t", dtype=str, keep_default_na=False)
    source_file = pd.read_csv(SOURCE_FILE, sep="\t", dtype=str, keep_default_na=False)
    source_access = pd.read_csv(SOURCE_ACCESS, sep="\t", dtype=str, keep_default_na=False)
    source_access_attempt = pd.read_csv(SOURCE_ACCESS_ATTEMPT, sep="\t", dtype=str, keep_default_na=False)
    source_access_right = pd.read_csv(SOURCE_ACCESS_RIGHT, sep="\t", dtype=str, keep_default_na=False)
    source_version = pd.read_csv(SOURCE_VERSION, sep="\t", dtype=str, keep_default_na=False)
    candidate_ledger = pd.read_csv(SOURCE_OBJECT_CANDIDATE, sep="\t", dtype=str, keep_default_na=False)

    article_sources = set(source_file[source_file["source_byte_class"].isin(resolver.ARTICLE_CLASSES)]["source_id"])
    source_input_by_id = resolver.source_inputs(sources, identifiers)
    result_by_id = source_result.set_index("source_result_id", drop=False)
    target_worklist = []
    skipped_existing = []
    for workrow in worklist.itertuples(index=False):
        row = result_by_id.loc[workrow.source_result_id]
        if row["represented_source_id"] in article_sources:
            skipped_existing.append(row["source_result_id"])
            continue
        target_worklist.append(workrow)

    attempts: list[dict[str, object]] = []
    candidate_rows: list[dict[str, object]] = []
    created_at = datetime.now(timezone.utc).isoformat()

    for i, workrow in enumerate(target_worklist, start=1):
        row = result_by_id.loc[workrow.source_result_id]
        source_input = source_input_by_id.get(row["represented_source_id"], {})
        if not source_input:
            attempts.append(metadata_attempt(row, {}, "zotero_skip", "missing_source_input", "0"))
            write_tsv(pd.DataFrame(attempts), OUT_ATTEMPTS)
            print(f"[{i}/{len(target_worklist)}] {row['source_result_id']} skipped=missing_source_input", flush=True)
            continue
        query = source_input.get("doi") or source_input.get("title") or safe_text(workrow.title)
        doi_url = "https://doi.org/" + source_input.get("doi", "") if source_input.get("doi") else ""
        before = storage_files()
        row_attempts: list[dict[str, object]] = []

        items, status = request_translation_search(query)
        if items:
            code, text, progress = zotero_save_items(items[:1], doi_url or safe_text(items[0].get("url")))
            time.sleep(1)
            new_files = storage_files() - before
            copied = copy_new_files(new_files, row["source_result_id"])
            for path in copied:
                row_attempts.append(attempt_from_file(row, source_input, path, "zotero_desktop_save_items", doi_url or safe_text(items[0].get("url"))))
            if not copied:
                detail = "zotero_desktop_no_full_text"
                if attachment_count(progress):
                    detail = "zotero_desktop_attachment_progress_but_no_file"
                row_attempts.append(metadata_attempt(row, source_input, "zotero_desktop_save_items", detail, str(code), doi_url))
        else:
            row_attempts.append(metadata_attempt(row, source_input, "zotero_translation_search", f"translation_search_{status}", status, doi_url))

        web_items = []
        if doi_url:
            web_items, web_status = request_translation_web(doi_url)
            attachments = []
            for item in web_items:
                attachments.extend(item.get("attachments") or [])
            if attachments:
                code, _text, progress = zotero_save_items(web_items[:1], doi_url)
                time.sleep(1)
                new_files = storage_files() - before
                copied = copy_new_files(new_files, row["source_result_id"])
                for path in copied:
                    row_attempts.append(attempt_from_file(row, source_input, path, "zotero_translation_web_attachment", doi_url))
                if not copied:
                    row_attempts.append(metadata_attempt(row, source_input, "zotero_translation_web_attachment", "zotero_web_attachment_no_file", str(code), doi_url))
            else:
                row_attempts.append(metadata_attempt(row, source_input, "zotero_translation_web", f"translation_web_metadata_only:{web_status}", web_status, doi_url))

            html, html_status = fetch_html(doi_url)
            if html:
                before_page = storage_files()
                code, text, progress = zotero_save_page(doi_url, html)
                time.sleep(1)
                new_files = storage_files() - before_page
                copied = copy_new_files(new_files, row["source_result_id"])
                for path in copied:
                    row_attempts.append(attempt_from_file(row, source_input, path, "zotero_desktop_save_page", doi_url))
                if not copied:
                    row_attempts.append(metadata_attempt(row, source_input, "zotero_desktop_save_page", "zotero_save_page_no_full_text", str(code), doi_url))
            else:
                row_attempts.append(metadata_attempt(row, source_input, "zotero_desktop_save_page", f"landing_fetch_{html_status}", html_status, doi_url))

        attempts.extend(row_attempts)
        write_tsv(pd.DataFrame(attempts), OUT_ATTEMPTS)
        for attempt in row_attempts:
            candidate_rows.append(resolver.candidate_ledger_row(attempt, source_input, created_at))
        accepted = sum(1 for attempt in row_attempts if attempt["identity_decision"] == "accepted_full_article_text")
        print(f"[{i}/{len(target_worklist)}] {row['source_result_id']} attempts={len(row_attempts)} accepted={accepted}", flush=True)

    attempts_df = pd.DataFrame(attempts)
    write_tsv(attempts_df, OUT_ATTEMPTS)

    new_candidate_df = pd.DataFrame(candidate_rows)
    if not new_candidate_df.empty:
        new_candidate_df = new_candidate_df.reindex(columns=candidate_ledger.columns, fill_value="")
        candidate_ledger = pd.concat([candidate_ledger, new_candidate_df], ignore_index=True)
        candidate_ledger = candidate_ledger.drop_duplicates(subset=["candidate_id"], keep="last")
        write_tsv(candidate_ledger, SOURCE_OBJECT_CANDIDATE)

    source_result, source_file, source_access, source_access_attempt, source_access_right, promoted = resolver.promote_accepted(
        attempts, source_result, source_file, source_access, source_access_attempt, source_access_right, source_version
    )
    write_tsv(source_result, SOURCE_RESULT)
    write_tsv(source_file, SOURCE_FILE)
    write_tsv(source_access, SOURCE_ACCESS)
    write_tsv(source_access_attempt, SOURCE_ACCESS_ATTEMPT)
    write_tsv(source_access_right, SOURCE_ACCESS_RIGHT)

    summary_rows = [
        {"metric": "run_id", "value": RUN_ID},
        {"metric": "target_rows_from_worklist", "value": len(worklist)},
        {"metric": "target_rows_after_existing_full_article_skip", "value": len(target_worklist)},
        {"metric": "skipped_existing_full_article_rows", "value": len(skipped_existing)},
        {"metric": "attempt_rows", "value": len(attempts_df)},
        {"metric": "accepted_full_article_text_rows", "value": len(promoted)},
    ]
    if not attempts_df.empty:
        for key, value in attempts_df["failure_code"].value_counts().sort_index().items():
            summary_rows.append({"metric": f"failure::{key}", "value": int(value)})
        for key, value in attempts_df["route"].value_counts().sort_index().items():
            summary_rows.append({"metric": f"route::{key}", "value": int(value)})
    summary = pd.DataFrame(summary_rows)
    write_tsv(summary, OUT_SUMMARY)

    lines = [
        "# Zotero Automated Full-Text Pass",
        "",
        f"- Run ID: `{RUN_ID}`",
        f"- Target bucket: `needs_manual_capture`",
        f"- Target rows from worklist: {len(worklist)}",
        f"- Target rows after existing full-article skip: {len(target_worklist)}",
        f"- Skipped rows already mirrored: {len(skipped_existing)}",
        f"- Attempts logged: {len(attempts_df)}",
        f"- Newly identity-accepted full-article text objects: {len(promoted)}",
        "",
        "## Route Result Counts",
        "",
    ]
    if attempts_df.empty:
        lines.append("- No attempts were produced.")
    else:
        for route, count in attempts_df["route"].value_counts().sort_index().items():
            lines.append(f"- `{route}`: {int(count)}")
        lines.extend(["", "## Failure Counts", ""])
        for failure, count in attempts_df["failure_code"].value_counts().sort_index().items():
            lines.append(f"- `{failure}`: {int(count)}")
    if len(promoted):
        lines.extend(["", "## Accepted Files", ""])
        for _, item in promoted.iterrows():
            lines.append(f"- `{item['source_result_id']}` via `{item['route']}` -> `{item['local_path']}`")
    lines.extend(
        [
            "",
            "## Output Files",
            "",
            f"- `{OUT_ATTEMPTS.relative_to(ROOT)}`",
            f"- `{OUT_SUMMARY.relative_to(ROOT)}`",
            f"- `{SOURCE_OBJECT_CANDIDATE.relative_to(ROOT)}`",
            f"- `{HANDOFF_CACHE.relative_to(ROOT)}`",
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
