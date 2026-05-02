#!/usr/bin/env python3
"""Re-ingest Zotero storage files against the blocked-row identity gate.

Zotero can finish attachment downloads after connector progress says a session
is done. This script treats the dedicated Zotero storage directory as a late
download cache and matches every stored PDF/XML/HTML/EPUB against the 15 blocked
rows. Only identity-accepted files are promoted.
"""

from __future__ import annotations

import importlib.util
import mimetypes
import os
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


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
ZOTERO_STORAGE = ROOT / ".local" / "zotero-oa-data" / "storage"
RUN_ID = f"zotero_storage_reingest_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
OUT_ATTEMPTS = PILOT / f"zotero_storage_reingest_attempts_{SAMPLE_SUFFIX}_{RUN_ID}.tsv"
OUT_SUMMARY = PILOT / f"zotero_storage_reingest_summary_{SAMPLE_SUFFIX}_{RUN_ID}.tsv"
OUT_REPORT = ROOT / "reports" / f"zotero_storage_reingest_{SAMPLE_SUFFIX}_{RUN_ID}.md"

resolver_path = ROOT / "scripts" / "resolve_full_article_text_candidates_pilot.py"
spec = importlib.util.spec_from_file_location("full_article_resolver", resolver_path)
resolver = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(resolver)


def storage_files() -> list[Path]:
    if not ZOTERO_STORAGE.exists():
        return []
    return sorted(
        path
        for path in ZOTERO_STORAGE.rglob("*")
        if path.is_file() and path.suffix.lower() in {".pdf", ".html", ".htm", ".xml", ".epub"}
    )


def attempt_file_for_row(path: Path, row: pd.Series, source_input: dict[str, str]) -> dict[str, object]:
    content = path.read_bytes()
    content_type = mimetypes.guess_type(path.name)[0] or ""
    byte_class, extension = resolver.classify_content(content, content_type, str(path))
    candidate_doi = resolver.normalize_doi(source_input.get("doi", ""))
    identity_decision, identity_reason, _text, title_cov = resolver.identity_check(
        source_input,
        byte_class,
        content,
        content_type,
        str(path),
        candidate_doi,
        False,
    )
    sha = resolver.sha256_bytes(content)
    local_path = ""
    if identity_decision == "accepted_full_article_text":
        local_path, sha = resolver.write_artifact(row["source_result_id"], "zotero_storage_reingest", byte_class, extension, content)
    return {
        "source_result_id": row["source_result_id"],
        "represented_source_id": row["represented_source_id"],
        "route": "zotero_storage_reingest",
        "route_family": "zotero",
        "api_url": "",
        "api_record_id": RUN_ID,
        "candidate_url": str(path),
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
        "candidate_doi": candidate_doi,
        "candidate_relation_type": "zotero_late_attachment",
        "candidate_title": source_input.get("title", ""),
        "primary_doi": source_input.get("doi", ""),
        "failure_code": "" if identity_decision == "accepted_full_article_text" else "zotero_storage_identity_failed",
        "download_attempted": "true",
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
    target_rows = [result_by_id.loc[row.source_result_id] for row in worklist.itertuples(index=False)]

    attempts = []
    candidate_rows = []
    created_at = datetime.now(timezone.utc).isoformat()
    matched_files: set[Path] = set()

    for path in storage_files():
        accepted_for_file = False
        for row in target_rows:
            if row["represented_source_id"] in article_sources:
                continue
            source_input = source_input_by_id.get(row["represented_source_id"], {})
            attempt = attempt_file_for_row(path, row, source_input)
            attempts.append(attempt)
            candidate_rows.append(resolver.candidate_ledger_row(attempt, source_input, created_at))
            if attempt["identity_decision"] == "accepted_full_article_text":
                accepted_for_file = True
                matched_files.add(path)
                print(f"accepted {path.name} -> {row['source_result_id']}", flush=True)
                break
        if not accepted_for_file:
            print(f"no match {path.name}", flush=True)

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

    summary = pd.DataFrame(
        [
            {"metric": "run_id", "value": RUN_ID},
            {"metric": "zotero_storage_files_seen", "value": len(storage_files())},
            {"metric": "matched_storage_files", "value": len(matched_files)},
            {"metric": "accepted_full_article_text_rows", "value": len(promoted)},
            {"metric": "attempt_rows", "value": len(attempts_df)},
        ]
    )
    write_tsv(summary, OUT_SUMMARY)

    lines = [
        "# Zotero Storage Re-Ingest",
        "",
        f"- Run ID: `{RUN_ID}`",
        f"- Zotero storage files seen: {len(storage_files())}",
        f"- Matched storage files: {len(matched_files)}",
        f"- Newly identity-accepted full-article text objects: {len(promoted)}",
        "",
        "## Accepted Files",
        "",
    ]
    if promoted.empty:
        lines.append("- None.")
    else:
        for _, item in promoted.iterrows():
            lines.append(f"- `{item['source_result_id']}` via `{item['route']}` -> `{item['local_path']}`")
    lines.extend(["", "## Output Files", "", f"- `{OUT_ATTEMPTS.relative_to(ROOT)}`", f"- `{OUT_SUMMARY.relative_to(ROOT)}`"])
    OUT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    OUT_REPORT.write_text("\n".join(lines) + "\n")

    print(f"Wrote {OUT_ATTEMPTS}")
    print(f"Wrote {OUT_SUMMARY}")
    print(f"Wrote {OUT_REPORT}")
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
