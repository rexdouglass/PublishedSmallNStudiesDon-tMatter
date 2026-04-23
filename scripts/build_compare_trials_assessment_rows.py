#!/usr/bin/env python3
"""Download and parse COMPare assessment sheets into outcome-level rows."""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

import pandas as pd
import requests


ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw" / "corpus_candidates" / "compare_trials"
MASTER_CSV = RAW_DIR / "compare_trials.csv"
ASSESSMENT_DIR = RAW_DIR / "assessments"
MANIFEST_JSON = RAW_DIR / "assessment_manifest.json"
MANIFEST_RECOVERED_JSON = RAW_DIR / "assessment_manifest_recovered.json"
RAW_OUT_CSV = RAW_DIR / "compare_trials_outcome_rows.csv"
RAW_SUMMARY_JSON = RAW_DIR / "compare_trials_assessment_summary.json"

DERIVED_DIR = ROOT / "data" / "derived" / "corpus_candidates" / "compare_trials"
OUT_CSV = DERIVED_DIR / "compare_trials_outcome_rows.csv"
OUT_PARQUET = DERIVED_DIR / "compare_trials_outcome_rows.parquet"
OUT_SUMMARY_JSON = DERIVED_DIR / "compare_trials_outcome_summary.json"

USER_AGENT = {"User-Agent": "Mozilla/5.0"}
REQUEST_TIMEOUT = 30

PRIMARY_SECTION = "prespecified_primary"
SECONDARY_SECTION = "prespecified_secondary"
NON_PRESPEC_SECTION = "non_prespecified_publication"


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def normalize_text(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).replace("\ufeff", "").replace("\xa0", " ")
    return " ".join(text.split())


def canonical_yes_no(value: str) -> str:
    lowered = normalize_text(value).lower()
    if lowered == "yes":
        return "Yes"
    if lowered == "no":
        return "No"
    if lowered == "unclear":
        return "Unclear"
    return normalize_text(value)


def missingish(value: str) -> bool:
    return normalize_text(value).lower() in {"", "nan", "none"}


def export_url_from_assessment_url(url: str) -> str | None:
    if not url:
        return None
    parsed = urlparse(url)
    query = parse_qs(parsed.query)
    path_match = re.search(r"/spreadsheets/d/([A-Za-z0-9_-]+)", parsed.path)
    if path_match:
        sheet_id = path_match.group(1)
        gid = query.get("gid", ["0"])[0]
        return f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?gid={gid}&format=csv"
    sheet_id = query.get("id", [None])[0]
    if sheet_id:
        return f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?gid=0&format=csv"
    return None


def fetch_csv(url: str) -> requests.Response:
    return requests.get(url, headers=USER_AGENT, timeout=REQUEST_TIMEOUT, allow_redirects=True)


def is_csv_like(text: str) -> bool:
    lowered = text.lower()
    return "trial info" in lowered or "prespecified primary outcome" in lowered


def download_assessments() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    ensure_dir(ASSESSMENT_DIR)
    master = pd.read_csv(MASTER_CSV)

    initial_manifest: list[dict[str, Any]] = []
    final_manifest: list[dict[str, Any]] = []

    for _, row in master.iterrows():
        study_id = normalize_text(row.get("Study ID"))
        url = normalize_text(row.get("Link to Assessment"))
        if missingish(study_id):
            study_id = ""
        if missingish(url):
            url = ""
        if not study_id and not url:
            continue
        entry: dict[str, Any] = {"study_id": study_id, "url": url}
        final_entry: dict[str, Any] = dict(entry)

        export_url = None
        if "/spreadsheets/d/" in url:
            export_url = export_url_from_assessment_url(url)
            entry["export"] = export_url
            try:
                response = fetch_csv(export_url)
                entry["status"] = response.status_code
                entry["bytes"] = len(response.content)
                if response.status_code == 200 and is_csv_like(response.text):
                    (ASSESSMENT_DIR / f"study_{study_id}.csv").write_text(
                        response.text, encoding="utf-8"
                    )
            except requests.RequestException as exc:
                entry["status"] = "request_error"
                entry["error"] = str(exc)
        else:
            entry["status"] = "bad_url"

        final_entry.update(entry)
        recovered_export = export_url_from_assessment_url(url)
        if entry.get("status") == "bad_url" and recovered_export:
            final_entry["recovered_export"] = recovered_export
            try:
                response = fetch_csv(recovered_export)
                final_entry["recovered_status"] = response.status_code
                final_entry["recovered_bytes"] = len(response.content)
                if response.status_code == 200 and is_csv_like(response.text):
                    (ASSESSMENT_DIR / f"study_{study_id}.csv").write_text(
                        response.text, encoding="utf-8"
                    )
                    final_entry["status"] = 200
                    final_entry["bytes"] = len(response.content)
            except requests.RequestException as exc:
                final_entry["recovered_status"] = "request_error"
                final_entry["recovered_error"] = str(exc)

        initial_manifest.append(entry)
        final_manifest.append(final_entry)

    MANIFEST_JSON.write_text(json.dumps(initial_manifest, indent=2), encoding="utf-8")
    MANIFEST_RECOVERED_JSON.write_text(json.dumps(final_manifest, indent=2), encoding="utf-8")
    return initial_manifest, final_manifest


def detect_section(row: list[str]) -> str | None:
    first = normalize_text(row[0]).lower() if row else ""
    if first.startswith("prespecified primary outcome"):
        return PRIMARY_SECTION
    if first.startswith("prespecified secondary outcome"):
        return SECONDARY_SECTION
    if first.startswith("non-prespecified outcome in publication"):
        return NON_PRESPEC_SECTION

    lowered = [normalize_text(cell).lower() for cell in row]
    if any("correctly reported as non-pre-specified" in cell for cell in lowered):
        return NON_PRESPEC_SECTION
    return None


def header_map(row: list[str]) -> dict[int, str]:
    mapping: dict[int, str] = {}
    for idx, raw in enumerate(row):
        cell = normalize_text(raw).lower()
        if not cell:
            continue
        if "incorrectly reported" in cell:
            mapping[idx] = "incorrect_main"
        elif "correctly reported as non-pre-specified" in cell or (
            "correctly reported" in cell and "non-pre" in cell
        ):
            mapping[idx] = "correct_main"
        elif "correctly reported" in cell:
            mapping[idx] = "correct_main"
        elif "reported elswhere" in cell or "reported elsewhere" in cell:
            mapping[idx] = "reported_elsewhere"
        elif "not reported in journal publication" in cell:
            mapping[idx] = "not_reported_journal"
        elif (
            "not declared as non-prespecified" in cell
            or "not declared as non-pre-specified" in cell
            or "not reported as non-pre-specified" in cell
            or cell == "not reported"
        ):
            mapping[idx] = "not_reported_journal"
        elif "insufficiently prespecified" in cell or "not sufficiently pre-specified" in cell:
            mapping[idx] = "insufficiently_prespecified"
    return mapping


def parse_assessment_csv(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        rows = [[normalize_text(cell) for cell in row] for row in csv.reader(handle)]

    meta: dict[str, str] = {
        "week": "",
        "study_id_sheet": "",
        "journal_name": "",
        "trial_title": "",
        "trial_link": "",
        "publication_date": "",
        "registry_link": "",
        "registry_id": "",
        "protocol_link": "",
    }
    meta_keys = {
        "week": "week",
        "study id": "study_id_sheet",
        "journal name": "journal_name",
        "trial title": "trial_title",
        "trial link": "trial_link",
        "publication date": "publication_date",
        "registry link": "registry_link",
        "registry id": "registry_id",
        "protocol link, if available": "protocol_link",
    }

    current_section: str | None = None
    current_headers: dict[int, str] = {}
    parsed: list[dict[str, Any]] = []

    for row in rows:
        first = normalize_text(row[0]) if row else ""
        first_lower = first.lower()

        if first_lower in meta_keys:
            meta[meta_keys[first_lower]] = normalize_text(row[1] if len(row) > 1 else "")
            continue

        if first_lower.startswith("complications to trial"):
            break

        section = detect_section(row)
        if section:
            current_section = section
            current_headers = header_map(row)
            continue

        if not current_section:
            continue
        if not first:
            continue
        if first_lower.startswith("total"):
            continue
        if not re.fullmatch(r"\d+[A-Za-z]*", first):
            continue

        outcome_text = normalize_text(row[1] if len(row) > 1 else "")
        if not outcome_text:
            continue

        record: dict[str, Any] = {
            "source_file": path.name,
            "study_id": path.stem.replace("study_", ""),
            "study_id_sheet": meta["study_id_sheet"],
            "week": meta["week"],
            "journal_name": meta["journal_name"],
            "trial_title": meta["trial_title"],
            "trial_link": meta["trial_link"],
            "publication_date": meta["publication_date"],
            "registry_link": meta["registry_link"],
            "registry_id": meta["registry_id"],
            "protocol_link": meta["protocol_link"],
            "section": current_section,
            "outcome_index": first,
            "outcome_text": outcome_text,
            "correct_main": "",
            "incorrect_main": "",
            "reported_elsewhere": "",
            "not_reported_journal": "",
            "insufficiently_prespecified": "",
        }
        for idx, field in current_headers.items():
            if idx < len(row):
                record[field] = canonical_yes_no(row[idx])
        parsed.append(record)

    return parsed


def build_outcome_rows() -> tuple[pd.DataFrame, dict[str, Any]]:
    ensure_dir(DERIVED_DIR)
    rows: list[dict[str, Any]] = []
    file_stats: list[dict[str, Any]] = []

    for path in sorted(ASSESSMENT_DIR.glob("study_*.csv")):
        parsed = parse_assessment_csv(path)
        rows.extend(parsed)
        study_id_sheet = parsed[0]["study_id_sheet"] if parsed else ""
        file_stats.append(
            {
                "file": path.name,
                "parsed_rows": len(parsed),
                "study_id": study_id_sheet or path.stem.replace("study_", ""),
            }
        )

    df = pd.DataFrame(rows)
    if not df.empty:
        df = df.sort_values(["study_id", "section", "outcome_index", "source_file"]).reset_index(
            drop=True
        )
        df.to_csv(RAW_OUT_CSV, index=False)
        df.to_csv(OUT_CSV, index=False)
        df.to_parquet(OUT_PARQUET, index=False)

    summary: dict[str, Any] = {
        "n_files": len(file_stats),
        "n_rows": int(len(df)),
        "section_counts": df["section"].value_counts().to_dict() if not df.empty else {},
        "status_counts": {},
        "file_stats": file_stats,
    }
    for column in [
        "correct_main",
        "incorrect_main",
        "reported_elsewhere",
        "not_reported_journal",
        "insufficiently_prespecified",
    ]:
        if column in df.columns:
            counts = df[column].replace("", pd.NA).dropna().value_counts().to_dict()
            summary["status_counts"][column] = counts

    RAW_SUMMARY_JSON.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    OUT_SUMMARY_JSON.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return df, summary


def main() -> None:
    initial_manifest, final_manifest = download_assessments()
    df, summary = build_outcome_rows()

    n_initial_ok = sum(1 for row in initial_manifest if row.get("status") == 200)
    n_final_ok = sum(1 for row in final_manifest if row.get("status") == 200)
    failed = [
        str(row.get("study_id"))
        for row in final_manifest
        if row.get("study_id")
        and row.get("status") != 200
        and row.get("recovered_status") != 200
    ]

    print(
        f"Downloaded {n_final_ok} COMPare assessment sheets "
        f"({n_initial_ok} direct, {n_final_ok - n_initial_ok} recovered)."
    )
    print(f"Remaining inaccessible study IDs: {', '.join(failed) if failed else 'none'}")
    print(
        f"Parsed {summary['n_rows']} outcome rows from {summary['n_files']} assessment sheets "
        f"into {OUT_CSV.relative_to(ROOT)}."
    )


if __name__ == "__main__":
    main()
