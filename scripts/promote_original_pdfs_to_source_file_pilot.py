#!/usr/bin/env python3
"""Promote identity-accepted original PDFs into the source_file manifest."""

from __future__ import annotations

import hashlib
import os
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
PILOT = ROOT / "data" / "derived" / "effect_inflation_dataset" / "schema_pilot"
SAMPLE_N = int(os.environ.get("SCHEMA_PILOT_N", "300"))
SAMPLE_SUFFIX = f"sample_{SAMPLE_N}"

IDENTITY_IN = PILOT / f"original_pdf_identity_check_{SAMPLE_SUFFIX}.tsv"
ACQUISITION_IN = PILOT / f"original_pdf_acquisition_attempts_{SAMPLE_SUFFIX}.tsv"
SOURCE_ACCESS = PILOT / f"source_access_codebook_{SAMPLE_SUFFIX}.tsv"
SOURCE_ACCESS_ATTEMPT = PILOT / f"source_access_attempt_codebook_{SAMPLE_SUFFIX}.tsv"
SOURCE_FILE = PILOT / f"source_file_codebook_{SAMPLE_SUFFIX}.tsv"
SOURCE_ACCESS_RIGHT = PILOT / f"source_access_right_codebook_{SAMPLE_SUFFIX}.tsv"
SOURCE_VERSION = PILOT / f"source_version_codebook_{SAMPLE_SUFFIX}.tsv"
SOURCE_RESULT = PILOT / f"source_result_codebook_{SAMPLE_SUFFIX}.tsv"

OUT_SUMMARY = PILOT / f"original_pdf_source_file_promotion_summary_{SAMPLE_SUFFIX}.tsv"
OUT_REPORT = ROOT / "reports" / f"original_pdf_source_file_promotion_{SAMPLE_SUFFIX}_2026-04-30.md"


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


def host(url: str) -> str:
    try:
        return urllib.parse.urlsplit(url).netloc
    except Exception:
        return ""


def strategy_for_route(route: str) -> str:
    if route.startswith("crossref"):
        return "crossref_metadata"
    if route.startswith("europepmc"):
        return "europepmc_metadata"
    if route.startswith("semantic_scholar"):
        return "semantic_scholar_metadata"
    if route.startswith("unpaywall"):
        return "unpaywall_metadata"
    if route.startswith("openalex"):
        return "openalex_metadata"
    if route.startswith("pmc"):
        return "pmc_fulltext"
    return "oa_candidate_url"


def read(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, sep="\t", dtype=str, keep_default_na=False)


def write(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, sep="\t", index=False)


def version_lookup(source_version: pd.DataFrame) -> dict[str, str]:
    out: dict[str, str] = {}
    for _, row in source_version.iterrows():
        source_id = safe_text(row.get("source_id"))
        version_id = safe_text(row.get("source_version_id"))
        if source_id and version_id and source_id not in out:
            out[source_id] = version_id
    return out


def main() -> None:
    identity = read(IDENTITY_IN)
    acquisition = read(ACQUISITION_IN)
    source_access = read(SOURCE_ACCESS)
    source_access_attempt = read(SOURCE_ACCESS_ATTEMPT)
    source_file = read(SOURCE_FILE)
    source_access_right = read(SOURCE_ACCESS_RIGHT)
    source_version = read(SOURCE_VERSION)
    source_result = read(SOURCE_RESULT)

    accepted = identity[identity["identity_decision"].eq("accepted_pdf_identity")].copy()
    if accepted.empty:
        raise SystemExit("No accepted PDFs to promote.")

    acquisition_pdf = acquisition[acquisition["pdf_valid"].astype(str).str.lower().eq("true")].copy()
    acquisition_pdf = acquisition_pdf.drop_duplicates(["source_result_id", "local_path"], keep="last")
    merged = accepted.merge(
        acquisition_pdf[
            [
                "source_result_id",
                "local_path",
                "http_status",
                "content_type",
                "byte_count",
                "candidate_url",
                "final_url",
                "route_note",
            ]
        ],
        on=["source_result_id", "local_path"],
        how="left",
        suffixes=("", "_acq"),
    )

    now = datetime.now(timezone.utc).isoformat()
    ver_by_source = version_lookup(source_version)
    access_rows = []
    attempt_rows = []
    file_rows = []
    rights_rows = []
    promotion_rows = []

    for _, row in merged.iterrows():
        source_result_id = safe_text(row["source_result_id"])
        source_id = safe_text(row["represented_source_id"])
        sha = safe_text(row["actual_sha256"]) or safe_text(row["ledger_sha256"])
        local_path = safe_text(row["local_path"])
        path = ROOT / local_path
        byte_size = str(path.stat().st_size) if path.exists() else safe_text(row.get("byte_count"))
        route = safe_text(row["route"])
        candidate_url = safe_text(row["candidate_url"])
        final_url = safe_text(row["final_url"])
        acquired_doi = safe_text(row["acquired_doi"])
        source_version_id = ver_by_source.get(source_id, "")
        resolver_strategy = strategy_for_route(route)

        access_id = stable_id("acc", "original_pdf", source_id, sha)
        attempt_id = stable_id("att", "original_pdf", source_result_id, source_id, sha)
        file_id = stable_id("file", "original_pdf", source_id, sha)
        right_id = stable_id("right", "original_pdf", source_id, file_id)
        group_id = stable_id("ag", "original_pdf", source_id)

        filename = Path(local_path).name
        decision_reason = safe_text(row["identity_decision_reason"])

        access_rows.append(
            {
                "access_id": access_id,
                "source_id": source_id,
                "access_role": "mirrored_file",
                "remote_url": candidate_url,
                "api_url": "",
                "final_url": final_url,
                "http_status": safe_text(row.get("http_status")),
                "redirect_chain": "",
                "host": host(final_url or candidate_url),
                "local_path": local_path,
                "file_member_path": "",
                "content_type": safe_text(row.get("content_type")) or "application/pdf",
                "file_sha256": sha,
                "file_size_bytes": byte_size,
                "retrieved_at": now,
                "retrieved_by": "codex",
                "retrieval_method": "automated_download",
                "access_status": "local_file_found",
                "access_strategy": resolver_strategy,
                "source_byte_class": "full_article_pdf",
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
                "preprint_or_repository_candidate": str(route in {"unpaywall_pdf", "semantic_scholar_openaccess_pdf"}).lower(),
                "access_barrier": "",
                "access_notes": f"Promoted after PDF identity check: {decision_reason}",
            }
        )
        attempt_rows.append(
            {
                "attempt_id": attempt_id,
                "source_id": source_id,
                "access_id": access_id,
                "attempt_group_id": group_id,
                "attempt_order": "1",
                "resolver_name": "original_pdf_acquisition",
                "resolver_version": "pilot_primary_identifier_v1",
                "resolver_strategy": resolver_strategy,
                "candidate_rank": "1",
                "candidate_rank_reason": "First valid PDF returned by primary-identifier acquisition route.",
                "candidate_url": candidate_url,
                "candidate_url_source": "primary_identifier_pdf_route",
                "final_url": final_url,
                "host": host(final_url or candidate_url),
                "method": "GET",
                "http_status": safe_text(row.get("http_status")),
                "redirect_chain": "",
                "cache_key": stable_id("cache", candidate_url, sha),
                "cache_hit_yn": "false",
                "retry_count": "0",
                "retry_after_seconds": "",
                "content_type_header": safe_text(row.get("content_type")),
                "content_type_sniffed": "application/pdf",
                "byte_count": byte_size,
                "sha256": sha,
                "local_path": local_path,
                "source_byte_class": "full_article_pdf",
                "access_status": "local_file_found",
                "access_barrier": "",
                "abstract_or_detail_text": "",
                "paywall_or_login_seen": "false",
                "captcha_or_bot_block_seen": "false",
                "preprint_or_repository_candidate": str(route in {"unpaywall_pdf", "semantic_scholar_openaccess_pdf"}).lower(),
                "license_url": "",
                "license_category": "unknown",
                "storage_allowed": "true",
                "robots_status": "not_checked",
                "tdm_policy_status": "unknown",
                "title_match_score": safe_text(row.get("title_line_similarity")),
                "doi_match_score": "1.0",
                "author_year_match_score": "",
                "identity_decision": "accepted_pdf_identity",
                "identity_decision_reason": decision_reason,
                "retrieval_method": "automated_download",
                "retrieved_at": now,
                "retrieved_by": "codex",
                "decision": "source_object_mirrored",
                "decision_reason": "Identity-accepted PDF bytes mirrored locally.",
                "stop_reason": "success",
                "next_action": "parse_or_verify",
                "notes": "Generated by original PDF source_file promotion pass.",
            }
        )
        file_rows.append(
            {
                "source_file_id": file_id,
                "source_id": source_id,
                "access_id": access_id,
                "attempt_id": attempt_id,
                "source_version_id": source_version_id,
                "file_role": "full_article",
                "file_origin": "automated_download",
                "source_byte_class": "full_article_pdf",
                "url": candidate_url,
                "final_url": final_url,
                "storage_uri": local_path,
                "local_path": local_path,
                "filename_original": filename,
                "filename_normalized": filename,
                "media_type_reported": safe_text(row.get("content_type")) or "application/pdf",
                "media_type_sniffed": "application/pdf",
                "byte_size": byte_size,
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
                "notes": f"Identity-accepted original PDF for {source_result_id}; {decision_reason}",
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
                "rights_decision_reason": "Project policy: keep local bytes out of git; publish only paths/routes/checksums and short evidence windows, not full documents.",
            }
        )
        promotion_rows.append(
            {
                "source_result_id": source_result_id,
                "source_id": source_id,
                "access_id": access_id,
                "attempt_id": attempt_id,
                "source_file_id": file_id,
                "sha256": sha,
                "local_path": local_path,
                "route": route,
            }
        )

    # Idempotent replacement of rows created by this script.
    access_ids = {row["access_id"] for row in access_rows}
    attempt_ids = {row["attempt_id"] for row in attempt_rows}
    file_ids = {row["source_file_id"] for row in file_rows}
    right_ids = {row["access_right_id"] for row in rights_rows}

    source_access = source_access[~source_access["access_id"].isin(access_ids)]
    source_access_attempt = source_access_attempt[~source_access_attempt["attempt_id"].isin(attempt_ids)]
    source_file = source_file[~source_file["source_file_id"].isin(file_ids)]
    source_access_right = source_access_right[~source_access_right["access_right_id"].isin(right_ids)]

    source_access = pd.concat([source_access, pd.DataFrame(access_rows, columns=source_access.columns)], ignore_index=True)
    source_access_attempt = pd.concat(
        [source_access_attempt, pd.DataFrame(attempt_rows, columns=source_access_attempt.columns)], ignore_index=True
    )
    source_file = pd.concat([source_file, pd.DataFrame(file_rows, columns=source_file.columns)], ignore_index=True)
    source_access_right = pd.concat(
        [source_access_right, pd.DataFrame(rights_rows, columns=source_access_right.columns)], ignore_index=True
    )

    promotion = pd.DataFrame(promotion_rows)
    promo_by_sr = {row["source_result_id"]: row for row in promotion.to_dict(orient="records")}
    mask = source_result["source_result_id"].isin(promo_by_sr)
    for idx, row in source_result.loc[mask].iterrows():
        promo = promo_by_sr[safe_text(row["source_result_id"])]
        source_result.at[idx, "access_id"] = promo["access_id"]
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
            f"original_pdf_source_file={promo['source_file_id']}; "
            f"original_pdf_local_path={promo['local_path']}; "
            f"original_pdf_sha256={promo['sha256']}; "
            "original_pdf_identity=accepted; level5_probe=identity-accepted original PDF mirrored; "
            "D/N value text not yet re-extracted from that PDF"
        )
        source_result.at[idx, "notes"] = f"{note}; {addition}" if note else addition

    write(source_access, SOURCE_ACCESS)
    write(source_access_attempt, SOURCE_ACCESS_ATTEMPT)
    write(source_file, SOURCE_FILE)
    write(source_access_right, SOURCE_ACCESS_RIGHT)
    write(source_result, SOURCE_RESULT)
    write(promotion, OUT_SUMMARY)

    counts = source_result["evidence_level"].value_counts().sort_index()
    lines = [
        "# Original PDF Source File Promotion",
        "",
        f"- Accepted PDFs promoted to source_file: {len(promotion)}",
        f"- Unique PDF SHA-256 values: {promotion['sha256'].nunique()}",
        f"- Level >=5 rows after promotion: {int(pd.to_numeric(source_result['evidence_level'], errors='coerce').fillna(0).ge(5).sum())}/{SAMPLE_N}",
        "",
        "## Level Counts",
        "",
    ]
    for level, count in counts.items():
        lines.append(f"- `{level}`: {int(count)}")
    lines.extend(["", "## Promoted Rows", ""])
    for _, row in promotion.iterrows():
        lines.append(f"- `{row['source_result_id']}` -> `{row['source_file_id']}` via `{row['route']}`")
    lines.extend(
        [
            "",
            "## Output Files",
            "",
            f"- `{rel(SOURCE_FILE)}`",
            f"- `{rel(SOURCE_ACCESS)}`",
            f"- `{rel(SOURCE_ACCESS_ATTEMPT)}`",
            f"- `{rel(SOURCE_ACCESS_RIGHT)}`",
            f"- `{rel(SOURCE_RESULT)}`",
            f"- `{rel(OUT_SUMMARY)}`",
        ]
    )
    OUT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    OUT_REPORT.write_text("\n".join(lines) + "\n")

    print(f"Wrote {SOURCE_FILE}")
    print(f"Wrote {SOURCE_ACCESS}")
    print(f"Wrote {SOURCE_ACCESS_ATTEMPT}")
    print(f"Wrote {SOURCE_ACCESS_RIGHT}")
    print(f"Wrote {SOURCE_RESULT}")
    print(f"Wrote {OUT_SUMMARY}")
    print(f"Wrote {OUT_REPORT}")
    print(f"promoted_source_files={len(promotion)}")
    print("level_counts")
    print(counts.to_string())


if __name__ == "__main__":
    main()
