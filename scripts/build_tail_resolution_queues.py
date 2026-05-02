#!/usr/bin/env python3
"""Build stop-condition queues for the below-level-5 provenance tail."""

from __future__ import annotations

import os
import re
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
PILOT = ROOT / "data" / "derived" / "effect_inflation_dataset" / "schema_pilot"
SAMPLE_N = int(os.environ.get("SCHEMA_PILOT_N", "300"))
SAMPLE_SUFFIX = f"sample_{SAMPLE_N}"

SOURCE_RESULT = PILOT / f"source_result_codebook_{SAMPLE_SUFFIX}.tsv"
WORKLIST = PILOT / f"remaining_full_article_worklist_after_core_{SAMPLE_SUFFIX}.tsv"

TAIL_QUEUE = PILOT / f"tail_resolution_queue_{SAMPLE_SUFFIX}.tsv"
TAIL_SUMMARY = PILOT / f"tail_resolution_queue_summary_{SAMPLE_SUFFIX}.tsv"
MANUAL_QUEUE = PILOT / f"manual_capture_queue_{SAMPLE_SUFFIX}.tsv"
MANUAL_OR_LIBRARY_QUEUE = PILOT / f"manual_or_library_followup_queue_{SAMPLE_SUFFIX}.tsv"
REPORT = ROOT / "reports" / f"tail_resolution_queues_{SAMPLE_SUFFIX}_2026-05-01.md"


BUCKET_CONFIG = {
    "needs_metabus_or_shorthand_crosswalk": {
        "rank": 1,
        "family": "identity_blocked",
        "identity_problem_type": "metabus_or_shorthand_citation",
        "requires_identity_work_yn": "true",
        "acquisition_ready_yn": "false",
        "requires_manual_capture_yn": "false",
        "primary_next_action": "Parse shorthand citation, resolve journal/volume/issue/page to DOI or stable article identity.",
        "suggested_routes": "local_metabus_metadata; crossref_bibliographic_query; openalex_source_query; publisher_toc_manual_review",
        "stop_condition": "Promote only after unambiguous represented article identity, or mark ambiguous/manual identity review.",
    },
    "needs_identity_crosswalk": {
        "rank": 2,
        "family": "identity_blocked",
        "identity_problem_type": "corpus_specific_anonymized_id",
        "requires_identity_work_yn": "true",
        "acquisition_ready_yn": "false",
        "requires_manual_capture_yn": "false",
        "primary_next_action": "Mirror project workbooks/code and build corpus-handle to represented-source crosswalk.",
        "suggested_routes": "osf_project_inventory; workbook_search; code_search; appendix_or_author_crosswalk",
        "stop_condition": "Promote only after crosswalk identifies a represented source with independent identifier or stable URL.",
    },
    "needs_better_identifier": {
        "rank": 3,
        "family": "identity_blocked",
        "identity_problem_type": "bibliographic_identifier_repair",
        "requires_identity_work_yn": "true",
        "acquisition_ready_yn": "false",
        "requires_manual_capture_yn": "false",
        "primary_next_action": "Repair bibliographic identity from title/author/year/journal fields.",
        "suggested_routes": "crossref_title_query; openalex_title_query; datacite_query; registry_specific_lookup",
        "stop_condition": "Promote only after DOI, PMID, PMCID, registry ID, stable URL, or unambiguous independent work ID is found.",
    },
    "needs_manual_capture": {
        "rank": 4,
        "family": "acquisition_blocked",
        "identity_problem_type": "grounded_source_manual_capture_needed",
        "requires_identity_work_yn": "false",
        "acquisition_ready_yn": "true",
        "requires_manual_capture_yn": "true",
        "primary_next_action": "Use lawful browser/Zotero/library route; hash, copy, identity-gate, and rights-note accepted files.",
        "suggested_routes": "manual_browser_oa; manual_browser_institutional; library_link_resolver; zotero_storage_reingest",
        "stop_condition": "Accept as level 5 only after local value-bearing bytes pass identity gate; otherwise record access barrier.",
    },
    "public_and_core_routes_exhausted": {
        "rank": 5,
        "family": "acquisition_blocked",
        "identity_problem_type": "public_routes_exhausted",
        "requires_identity_work_yn": "false",
        "acquisition_ready_yn": "true",
        "requires_manual_capture_yn": "true",
        "primary_next_action": "Stop automated looping; decide library, author, publisher, or unresolved follow-up.",
        "suggested_routes": "library_link_resolver; interlibrary_loan; author_request; publisher_request",
        "stop_condition": "Promote if lawful source bytes are obtained and identity-gated; otherwise leave explicit manual task.",
    },
}


def safe_text(value: object) -> str:
    if value is None:
        return ""
    return str(value).replace("\t", " ").replace("\r", " ").replace("\n", " ").strip()


def parse_shorthand(row: pd.Series) -> dict[str, str]:
    text = " ".join(
        [
            safe_text(row.get("title")),
            safe_text(row.get("represented_source_id")),
        ]
    )
    patterns = [
        re.compile(r"(?P<journal>[A-Za-z]{2,10})-(?P<volume>\d+)-(?P<issue>\d+)-(?P<page>\d+)"),
        re.compile(
            r"(?:bosco_)?(?P<journal>jap|pp)_(?P<volume>\d+)_(?P<issue>\d+)_(?P<page>\d+)(?:_(?P<effect_id>\d+))?",
            re.IGNORECASE,
        ),
    ]
    for pattern in patterns:
        match = pattern.search(text)
        if not match:
            continue
        groups = {key: safe_text(value) for key, value in match.groupdict(default="").items()}
        return {
            "parsed_journal_abbrev": groups.get("journal", "").upper(),
            "parsed_volume": groups.get("volume", ""),
            "parsed_issue": groups.get("issue", ""),
            "parsed_first_page": groups.get("page", ""),
            "parsed_effect_id": groups.get("effect_id", ""),
        }
    return {
        "parsed_journal_abbrev": "",
        "parsed_volume": "",
        "parsed_issue": "",
        "parsed_first_page": "",
        "parsed_effect_id": "",
    }


def manual_route_type(bucket: str) -> str:
    if bucket == "needs_manual_capture":
        return "manual_browser_oa_or_institutional"
    if bucket == "public_and_core_routes_exhausted":
        return "library_author_or_publisher_required"
    return ""


def build_tail_queue() -> pd.DataFrame:
    source_result = pd.read_csv(SOURCE_RESULT, sep="\t", dtype=str, keep_default_na=False)
    worklist = pd.read_csv(WORKLIST, sep="\t", dtype=str, keep_default_na=False)
    current = source_result[
        [
            "source_result_id",
            "represented_source_id",
            "evidence_level",
            "target_acquisition_state",
            "value_verification_state",
            "source_is_original",
            "number_verified_by_us",
            "d",
            "standardized_n",
            "result_label",
            "outcome_label",
            "notes",
        ]
    ].copy()
    active_ids = set(source_result[source_result["evidence_level"].astype(int).lt(5)]["source_result_id"])
    active = worklist[worklist["source_result_id"].isin(active_ids)].copy()
    active = active.drop(columns=["evidence_level"], errors="ignore").merge(current, on=["source_result_id", "represented_source_id"], how="left")
    rows = []
    created_at = datetime.now(timezone.utc).isoformat()
    for _, row in active.iterrows():
        bucket = safe_text(row.get("next_bucket"))
        config = BUCKET_CONFIG.get(bucket, {})
        parsed = parse_shorthand(row)
        rank = config.get("rank", 99)
        rows.append(
            {
                "queue_id": f"tailq_{rank:02d}_{safe_text(row.get('source_result_id'))}",
                "source_result_id": safe_text(row.get("source_result_id")),
                "represented_source_id": safe_text(row.get("represented_source_id")),
                "source_type": safe_text(row.get("source_type")),
                "current_evidence_level": safe_text(row.get("evidence_level")),
                "target_acquisition_state": safe_text(row.get("target_acquisition_state")),
                "value_verification_state": safe_text(row.get("value_verification_state")),
                "source_is_original": safe_text(row.get("source_is_original")),
                "number_verified_by_us": safe_text(row.get("number_verified_by_us")),
                "doi": safe_text(row.get("doi")),
                "pmid": safe_text(row.get("pmid")),
                "title": safe_text(row.get("title")),
                "result_label": safe_text(row.get("result_label")),
                "outcome_label": safe_text(row.get("outcome_label")),
                "d": safe_text(row.get("d")),
                "standardized_n": safe_text(row.get("standardized_n")),
                "next_bucket": bucket,
                "tail_problem_family": config.get("family", "unclassified"),
                "identity_problem_type": config.get("identity_problem_type", ""),
                "rank": rank,
                "requires_identity_work_yn": config.get("requires_identity_work_yn", ""),
                "acquisition_ready_yn": config.get("acquisition_ready_yn", ""),
                "requires_manual_capture_yn": config.get("requires_manual_capture_yn", ""),
                **parsed,
                "suggested_routes": config.get("suggested_routes", ""),
                "primary_next_action": config.get("primary_next_action", ""),
                "stop_condition": config.get("stop_condition", ""),
                "failed_public_routes_seen": safe_text(row.get("failed_public_routes_seen")),
                "manual_route_type": manual_route_type(bucket),
                "queue_created_at": created_at,
                "queue_status": "open",
                "notes": safe_text(row.get("notes")),
            }
        )
    out = pd.DataFrame(rows)
    return out.sort_values(["rank", "source_type", "title", "source_result_id"]).reset_index(drop=True)


def build_manual_queue(tail: pd.DataFrame, include_exhausted: bool) -> pd.DataFrame:
    buckets = {"needs_manual_capture", "public_and_core_routes_exhausted"} if include_exhausted else {"needs_manual_capture"}
    manual = tail[tail["next_bucket"].isin(buckets)].copy()
    rows = []
    for _, row in manual.iterrows():
        rows.append(
            {
                "source_result_id": row["source_result_id"],
                "represented_source_id": row["represented_source_id"],
                "doi": row["doi"],
                "title": row["title"],
                "source_type": row["source_type"],
                "current_evidence_level": row["current_evidence_level"],
                "first_failed_route_summary": row["failed_public_routes_seen"],
                "manual_route_status": "not_started",
                "manual_route_type": row["manual_route_type"],
                "operator_id": "",
                "started_at": "",
                "completed_at": "",
                "access_basis": "",
                "institutional_access_used": "",
                "browser_used": "",
                "zotero_used": "",
                "download_url_observed": "",
                "landing_url_observed": "",
                "referrer_url_observed": "",
                "candidate_local_temp_path": "",
                "accepted_local_path": "",
                "sha256": "",
                "byte_size": "",
                "mime_type": "",
                "source_byte_class": "",
                "identity_check_status": "",
                "identity_check_basis": "",
                "rights_storage_notes": "",
                "redistribution_allowed": "",
                "internal_audit_only": "true",
                "manual_notes": row["primary_next_action"],
            }
        )
    return pd.DataFrame(rows)


def write_report(tail: pd.DataFrame, manual: pd.DataFrame, manual_or_library: pd.DataFrame) -> None:
    summary = tail.groupby(["rank", "next_bucket", "tail_problem_family"], dropna=False).size().reset_index(name="rows")
    lines = [
        "# Tail Resolution Queues",
        "",
        f"- Generated: {datetime.now(timezone.utc).isoformat()}",
        f"- Active below-level-5 rows: {len(tail)}",
        f"- Active manual-capture rows: {len(manual)}",
        f"- Active manual/library/author follow-up rows: {len(manual_or_library)}",
        "",
        "## Bucket Counts",
        "",
    ]
    for _, row in summary.sort_values(["rank", "next_bucket"]).iterrows():
        lines.append(f"- `{row['next_bucket']}` ({row['tail_problem_family']}): {int(row['rows'])}")
    lines.extend(
        [
            "",
            "## Note",
            "",
            "The older full-article worklist still contains two Zotero-promoted rows. This queue is built from current `source_result_codebook_sample_300.tsv` evidence levels, so those rows are excluded from the active tail.",
            "",
            "## Outputs",
            "",
            f"- `{TAIL_QUEUE.relative_to(ROOT)}`",
            f"- `{TAIL_SUMMARY.relative_to(ROOT)}`",
            f"- `{MANUAL_QUEUE.relative_to(ROOT)}`",
            f"- `{MANUAL_OR_LIBRARY_QUEUE.relative_to(ROOT)}`",
        ]
    )
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(lines) + "\n")


def main() -> None:
    tail = build_tail_queue()
    manual = build_manual_queue(tail, include_exhausted=False)
    manual_or_library = build_manual_queue(tail, include_exhausted=True)
    summary = tail.groupby(["rank", "next_bucket", "tail_problem_family"], dropna=False).size().reset_index(name="rows")

    TAIL_QUEUE.parent.mkdir(parents=True, exist_ok=True)
    tail.to_csv(TAIL_QUEUE, sep="\t", index=False)
    summary.to_csv(TAIL_SUMMARY, sep="\t", index=False)
    manual.to_csv(MANUAL_QUEUE, sep="\t", index=False)
    manual_or_library.to_csv(MANUAL_OR_LIBRARY_QUEUE, sep="\t", index=False)
    write_report(tail, manual, manual_or_library)

    print(f"Wrote {TAIL_QUEUE}")
    print(f"Wrote {TAIL_SUMMARY}")
    print(f"Wrote {MANUAL_QUEUE}")
    print(f"Wrote {MANUAL_OR_LIBRARY_QUEUE}")
    print(f"Wrote {REPORT}")
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
