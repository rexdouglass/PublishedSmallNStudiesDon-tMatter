#!/usr/bin/env python3
"""Audit replay-critical provenance fields for mirrored pilot artifacts.

This is intentionally diagnostic. It does not change evidence levels. The goal
is to make concrete which level-5-ish byte objects can be replayed from local
storage today, and which still need stronger upstream snapshot/version metadata
before the pipeline is ready to scale.
"""

from __future__ import annotations

import hashlib
import os
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
PILOT = ROOT / "data" / "derived" / "effect_inflation_dataset" / "schema_pilot"
SAMPLE_N = int(os.environ.get("SCHEMA_PILOT_N", "300"))
SAMPLE_SUFFIX = f"sample_{SAMPLE_N}"

SOURCE_FILE_IN = PILOT / f"source_file_codebook_{SAMPLE_SUFFIX}.tsv"
SOURCE_ATTEMPT_IN = PILOT / f"source_access_attempt_codebook_{SAMPLE_SUFFIX}.tsv"
SOURCE_VERSION_IN = PILOT / f"source_version_codebook_{SAMPLE_SUFFIX}.tsv"

OUT_TSV = PILOT / f"artifact_snapshot_provenance_audit_{SAMPLE_SUFFIX}.tsv"
OUT_SUMMARY = PILOT / f"artifact_snapshot_provenance_audit_summary_{SAMPLE_SUFFIX}.tsv"
OUT_REPORT = ROOT / "reports" / f"artifact_snapshot_provenance_audit_{SAMPLE_SUFFIX}_2026-04-30.md"


WEAK_VERSION_SOURCES = {"", "pilot_unknown", "source_access_inferred"}
WEAK_VERSION_LABELS = {"", "unknown", "dataset"}


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


def resolve_local_path(value: object) -> Path | None:
    text = safe_text(value)
    if not text:
        return None
    path = Path(text)
    if not path.is_absolute():
        path = ROOT / path
    return path


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def to_int(value: object) -> int | None:
    text = safe_text(value)
    if not text:
        return None
    try:
        return int(float(text))
    except ValueError:
        return None


def version_has_upstream_snapshot(row: pd.Series) -> bool:
    version_source = safe_text(row.get("version_source"))
    version_label = safe_text(row.get("version_label"))
    version_number = safe_text(row.get("version_number"))
    version_date = safe_text(row.get("version_date"))
    evidence = safe_text(row.get("version_evidence_text"))
    if version_source in WEAK_VERSION_SOURCES and version_label in WEAK_VERSION_LABELS and not version_number and not version_date:
        return False
    if version_date or version_number:
        return True
    if version_source and version_source not in WEAK_VERSION_SOURCES:
        return True
    return bool(evidence)


def snapshot_timestamp(row: pd.Series) -> tuple[str, str]:
    for col, basis in [
        ("retrieved_at", "access_attempt_retrieved_at"),
        ("created_at", "source_file_created_at"),
        ("fixity_checked_at", "source_file_fixity_checked_at"),
    ]:
        value = safe_text(row.get(col))
        if value:
            return value, basis
    return "", ""


def main() -> None:
    source_files = pd.read_csv(SOURCE_FILE_IN, sep="\t", dtype=str, keep_default_na=False)
    attempts = pd.read_csv(SOURCE_ATTEMPT_IN, sep="\t", dtype=str, keep_default_na=False)
    versions = pd.read_csv(SOURCE_VERSION_IN, sep="\t", dtype=str, keep_default_na=False)

    attempt_cols = [
        "attempt_id",
        "retrieved_at",
        "retrieval_method",
        "resolver_name",
        "resolver_version",
        "candidate_url",
        "final_url",
        "decision",
    ]
    version_cols = [
        "source_version_id",
        "version_label",
        "version_number",
        "version_date",
        "version_source",
        "version_evidence_text",
    ]
    work = source_files.merge(attempts[attempt_cols], on="attempt_id", how="left")
    work = work.merge(versions[version_cols], on="source_version_id", how="left")

    rows: list[dict[str, object]] = []
    for _, row in work.iterrows():
        path = resolve_local_path(row.get("local_path"))
        local_file_exists = bool(path and path.exists() and path.is_file())
        computed_size: int | None = None
        computed_sha = ""
        read_error = ""
        if local_file_exists and path is not None:
            try:
                computed_size = path.stat().st_size
                computed_sha = sha256_file(path)
            except OSError as exc:
                read_error = f"{type(exc).__name__}:{exc}"

        recorded_size = to_int(row.get("byte_size"))
        recorded_sha = safe_text(row.get("sha256"))
        timestamp, timestamp_basis = snapshot_timestamp(row)
        source_version_id = safe_text(row.get("source_version_id"))
        upstream_snapshot_present = version_has_upstream_snapshot(row)
        extractor_version_present = False

        size_matches = recorded_size is not None and computed_size is not None and recorded_size == computed_size
        sha_present = bool(recorded_sha)
        sha_matches = bool(recorded_sha and computed_sha and recorded_sha.lower() == computed_sha.lower())
        source_version_id_present = bool(source_version_id)
        snapshot_timestamp_present = bool(timestamp)
        minimum_replay_fields_complete = local_file_exists and sha_matches and size_matches and snapshot_timestamp_present
        strict_source_version_fields_complete = minimum_replay_fields_complete and source_version_id_present and upstream_snapshot_present

        gaps: list[str] = []
        if not local_file_exists:
            gaps.append("local_file_missing")
        if not size_matches:
            gaps.append("byte_size_missing_or_mismatch")
        if not sha_present:
            gaps.append("sha256_missing")
        elif not sha_matches:
            gaps.append("sha256_mismatch")
        if not snapshot_timestamp_present:
            gaps.append("snapshot_timestamp_missing")
        if not source_version_id_present:
            gaps.append("source_version_id_missing")
        if not upstream_snapshot_present:
            gaps.append("upstream_snapshot_id_or_version_date_missing")
        if not extractor_version_present:
            gaps.append("extractor_version_missing_until_value_parser_runs")

        next_action = "Ready for local byte replay; add parser/extractor event before level-6 promotion."
        if not minimum_replay_fields_complete:
            next_action = "Repair local-byte replay fields before relying on this artifact."
        elif not upstream_snapshot_present:
            next_action = "Add upstream snapshot/version identifier before scaling this artifact family."

        rows.append(
            {
                "source_file_id": safe_text(row.get("source_file_id")),
                "source_id": safe_text(row.get("source_id")),
                "source_byte_class": safe_text(row.get("source_byte_class")),
                "file_role": safe_text(row.get("file_role")),
                "file_origin": safe_text(row.get("file_origin")),
                "attempt_id": safe_text(row.get("attempt_id")),
                "resolver_name": safe_text(row.get("resolver_name")),
                "resolver_version": safe_text(row.get("resolver_version")),
                "source_version_id": source_version_id,
                "version_label": safe_text(row.get("version_label")),
                "version_number": safe_text(row.get("version_number")),
                "version_date": safe_text(row.get("version_date")),
                "version_source": safe_text(row.get("version_source")),
                "local_path": rel(path or ""),
                "local_file_exists": local_file_exists,
                "recorded_byte_size": recorded_size if recorded_size is not None else "",
                "computed_byte_size": computed_size if computed_size is not None else "",
                "byte_size_matches": size_matches,
                "recorded_sha256": recorded_sha,
                "computed_sha256": computed_sha,
                "sha256_present": sha_present,
                "sha256_matches_local_file": sha_matches,
                "provider_checksum_present": bool(safe_text(row.get("provider_checksum_value"))),
                "content_fingerprint_present": bool(safe_text(row.get("content_fingerprint"))),
                "text_sha256_present": bool(safe_text(row.get("text_sha256"))),
                "retrieved_at": safe_text(row.get("retrieved_at")),
                "created_at": safe_text(row.get("created_at")),
                "fixity_checked_at": safe_text(row.get("fixity_checked_at")),
                "snapshot_timestamp": timestamp,
                "snapshot_timestamp_basis": timestamp_basis,
                "snapshot_timestamp_present": snapshot_timestamp_present,
                "source_version_id_present": source_version_id_present,
                "upstream_snapshot_id_present": upstream_snapshot_present,
                "extractor_version_present": extractor_version_present,
                "minimum_replay_fields_complete": minimum_replay_fields_complete,
                "strict_source_version_fields_complete": strict_source_version_fields_complete,
                "read_error": read_error,
                "gap_summary": "|".join(gaps) if gaps else "none",
                "recommended_next_action": next_action,
            }
        )

    out = pd.DataFrame(rows)
    OUT_TSV.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT_TSV, sep="\t", index=False)

    bool_metrics = [
        "local_file_exists",
        "byte_size_matches",
        "sha256_present",
        "sha256_matches_local_file",
        "snapshot_timestamp_present",
        "source_version_id_present",
        "upstream_snapshot_id_present",
        "extractor_version_present",
        "minimum_replay_fields_complete",
        "strict_source_version_fields_complete",
    ]
    summary_rows: list[dict[str, object]] = [
        {"metric": "sample_n", "value": SAMPLE_N},
        {"metric": "source_file_artifacts_total", "value": int(len(out))},
        {"metric": "created_at_utc", "value": datetime.now(timezone.utc).isoformat()},
    ]
    for metric in bool_metrics:
        summary_rows.append({"metric": metric, "value": int(out[metric].sum())})
    for key, value in out["source_byte_class"].value_counts().sort_index().items():
        summary_rows.append({"metric": f"source_byte_class::{key}", "value": int(value)})
    for key, value in out["gap_summary"].value_counts().head(20).items():
        summary_rows.append({"metric": f"gap_summary::{key}", "value": int(value)})
    summary = pd.DataFrame(summary_rows)
    summary.to_csv(OUT_SUMMARY, sep="\t", index=False)

    total = len(out)
    sha_ok = int(out["sha256_matches_local_file"].sum())
    minimum_ok = int(out["minimum_replay_fields_complete"].sum())
    upstream_ok = int(out["upstream_snapshot_id_present"].sum())
    strict_ok = int(out["strict_source_version_fields_complete"].sum())
    lines = [
        "# Artifact Snapshot Provenance Audit",
        "",
        f"- Sample rows: {SAMPLE_N}",
        f"- Source-file artifacts audited: {total}",
        f"- Local byte files present: {int(out['local_file_exists'].sum())}/{total}",
        f"- SHA-256 values matching local bytes: {sha_ok}/{total}",
        f"- Minimum local replay fields complete: {minimum_ok}/{total}",
        f"- Upstream snapshot/version metadata present: {upstream_ok}/{total}",
        f"- Strict source-version replay fields complete: {strict_ok}/{total}",
        "",
        "## Interpretation",
        "",
        "- The pilot already has local byte fixity for most artifacts through `source_file.sha256`; the field is named `sha256`, not `bytes_sha256`.",
        "- The larger scaling gap is upstream source-version provenance: most rows use local source-version placeholders, not concrete AACT/OpenAlex/Unpaywall/S2/PubMed/Crossref snapshot identifiers.",
        "- `extractor_version` is not an artifact-level field yet. It should be recorded on parser/extraction events and source-result support rows when a parser creates value evidence.",
        "",
        "## Top Gap Patterns",
        "",
    ]
    for gap, count in out["gap_summary"].value_counts().head(10).items():
        lines.append(f"- `{gap}`: {int(count)}")
    lines.extend(["", "## Output Files", "", f"- `{rel(OUT_TSV)}`", f"- `{rel(OUT_SUMMARY)}`"])
    OUT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    OUT_REPORT.write_text("\n".join(lines) + "\n")

    print(f"Wrote {OUT_TSV}")
    print(f"Wrote {OUT_SUMMARY}")
    print(f"Wrote {OUT_REPORT}")
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
