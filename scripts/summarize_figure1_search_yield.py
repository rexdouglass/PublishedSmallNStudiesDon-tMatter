#!/usr/bin/env python3
"""Summarize marginal yield from Figure 1 corpus/database search manifests.

This is a diagnostic report, not a search target. Its outputs deliberately do
not use the ``corporasearch-*`` prefix because those files are reserved for
consolidation inputs to CORPORA_AND_DATABASES.tsv.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SEARCH_DIR = ROOT / "steps" / "searches" / "figure1"
ROOT_TABLE = ROOT / "CORPORA_AND_DATABASES.tsv"
SUMMARY_TSV = SEARCH_DIR / "searchyield-figure1-corpusdb-summary.tsv"
NEW_LEADS_TSV = SEARCH_DIR / "searchyield-figure1-corpusdb-expanded-new-leads.tsv"
SUMMARY_MD = SEARCH_DIR / "searchyield-figure1-corpusdb-summary.md"
DOI_RE = re.compile(r"10\.\d{4,9}/[-._;()/:A-Z0-9]+", re.I)


def safe_text(value: object, max_len: int = 8000) -> str:
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value).replace("\t", " ")).strip()[:max_len]


def slugify(value: object, fallback: str = "") -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", safe_text(value).lower()).strip("_")
    return slug or fallback


def repo_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def split_values(value: object) -> list[str]:
    text = safe_text(value)
    if not text:
        return []
    return [part for part in (safe_text(part) for part in re.split(r"\s*\|\s*|\s*;\s*", text)) if part]


def normalize_url(value: object) -> str:
    text = safe_text(value)
    if not text:
        return ""
    text = split_values(text)[0] if split_values(text) else text
    text = re.sub(r"^https?://dx\.doi\.org/", "https://doi.org/", text, flags=re.I)
    text = re.sub(r"#.*$", "", text)
    text = re.sub(r"\?.*$", "", text)
    return text.rstrip("/").lower()


def normalize_doi(value: object) -> str:
    text = safe_text(value)
    if not text:
        return ""
    text = re.sub(r"^doi:\s*", "", text, flags=re.I)
    text = re.sub(r"^https?://(?:dx\.)?doi\.org/", "", text, flags=re.I)
    match = DOI_RE.search(text)
    if not match:
        return ""
    return match.group(0).rstrip(".,;)").lower()


def row_keys(row: dict[str, Any]) -> set[str]:
    keys: set[str] = set()
    for column in ["doi", "source_key", "landing_url", "raw_url", "notes"]:
        doi = normalize_doi(row.get(column, ""))
        if doi:
            keys.add(f"doi:{doi}")
    for column in ["landing_url", "raw_url", "url"]:
        url = normalize_url(row.get(column, ""))
        if url:
            keys.add(f"url:{url}")
    for column in ["source_key", "external_id"]:
        value = safe_text(row.get(column, ""))
        if value:
            keys.add(f"{column}:{value.lower()}")
    title = slugify(row.get("name") or row.get("title"))
    if len(title) >= 12:
        keys.add(f"title:{title}")
    return keys


def lead_key(row: dict[str, Any]) -> str:
    keys = sorted(row_keys(row))
    if keys:
        preferred = [key for key in keys if key.startswith(("doi:", "url:", "source_key:", "external_id:"))]
        return (preferred or keys)[0]
    return f"title:{slugify(row.get('name') or row.get('title'), 'untitled')}"


def load_root_keys() -> set[str]:
    if not ROOT_TABLE.exists():
        return set()
    keys: set[str] = set()
    with ROOT_TABLE.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        for row in reader:
            keys.update(row_keys(row))
    return keys


def load_manifest(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    if not isinstance(payload, dict):
        return None
    return payload


def manifest_group(path: Path, payload: dict[str, Any]) -> str:
    text = f"{path.name} {payload.get('strategy_id', '')}"
    return "expanded" if "expanded" in text else "baseline"


def manifest_rows(payload: dict[str, Any], bucket: str) -> list[dict[str, Any]]:
    rows = payload.get(bucket) or []
    return [row for row in rows if isinstance(row, dict)]


def write_tsv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter="\t", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def summarize() -> tuple[list[dict[str, str]], list[dict[str, str]], str]:
    root_keys = load_root_keys()
    baseline_manifest_keys: set[str] = set()
    manifest_payloads: list[tuple[Path, dict[str, Any], str]] = []
    for path in sorted(SEARCH_DIR.glob("corporasearch-*.json")):
        payload = load_manifest(path)
        if payload is None:
            continue
        group = manifest_group(path, payload)
        manifest_payloads.append((path, payload, group))
        if group == "baseline":
            for row in manifest_rows(payload, "candidates") + manifest_rows(payload, "routed_or_rejected_leads"):
                baseline_manifest_keys.update(row_keys(row))

    seen_manifest_keys: set[str] = set()
    summary_rows: list[dict[str, str]] = []
    new_lead_rows: list[dict[str, str]] = []

    for path, payload, group in manifest_payloads:
        candidates = manifest_rows(payload, "candidates")
        routed = manifest_rows(payload, "routed_or_rejected_leads")
        all_leads = candidates + routed
        candidate_keys = [row_keys(row) for row in candidates]
        all_keys = [row_keys(row) for row in all_leads]
        unique_candidate_leads = {lead_key(row) for row in candidates}
        unique_all_leads = {lead_key(row) for row in all_leads}

        candidate_new_to_root = [row for row, keys in zip(candidates, candidate_keys) if not (keys & root_keys)]
        candidate_new_to_baseline = [row for row, keys in zip(candidates, candidate_keys) if not (keys & baseline_manifest_keys)]
        candidate_new_to_prior = [row for row, keys in zip(candidates, candidate_keys) if not (keys & seen_manifest_keys)]
        all_new_to_prior = [row for row, keys in zip(all_leads, all_keys) if not (keys & seen_manifest_keys)]
        kinds = Counter(safe_text(row.get("record_kind")) for row in candidates)
        statuses = Counter(safe_text(row.get("inventory_status")) for row in candidates)

        summary_rows.append(
            {
                "manifest_path": repo_path(path),
                "manifest_group": group,
                "strategy_id": safe_text(payload.get("strategy_id")),
                "strategy": safe_text(payload.get("strategy")),
                "providers": " | ".join(safe_text(provider) for provider in payload.get("providers", [])),
                "query_count": str(len(payload.get("queries") or [])),
                "raw_result_count": str(payload.get("raw_result_count", 0)),
                "classified_lead_count": str(payload.get("classified_lead_count", 0)),
                "candidate_count": str(len(candidates)),
                "candidate_unique_lead_count": str(len(unique_candidate_leads)),
                "candidate_new_to_root_count": str(len(candidate_new_to_root)),
                "candidate_new_to_baseline_manifest_count": str(len(candidate_new_to_baseline)),
                "candidate_new_to_prior_manifest_count": str(len(candidate_new_to_prior)),
                "all_lead_unique_count": str(len(unique_all_leads)),
                "all_lead_new_to_prior_manifest_count": str(len(all_new_to_prior)),
                "routed_or_rejected_count": str(len(routed)),
                "error_count": str(len(payload.get("errors") or [])),
                "candidate_record_kind_counts": " | ".join(f"{key}={value}" for key, value in sorted(kinds.items())),
                "candidate_status_counts": " | ".join(f"{key}={value}" for key, value in sorted(statuses.items())),
            }
        )

        if group == "expanded":
            for row in candidate_new_to_root:
                keys = row_keys(row)
                new_lead_rows.append(
                    {
                        "manifest_path": repo_path(path),
                        "name": safe_text(row.get("name")),
                        "record_kind": safe_text(row.get("record_kind")),
                        "inventory_status": safe_text(row.get("inventory_status")),
                        "new_to_baseline_manifest": "yes" if not (keys & baseline_manifest_keys) else "no",
                        "landing_url": safe_text(row.get("landing_url")),
                        "source_key": safe_text(row.get("source_key")),
                        "why_relevant": safe_text(row.get("why_relevant"), 1200),
                        "next_action": safe_text(row.get("next_action")),
                    }
                )

        for keys in all_keys:
            seen_manifest_keys.update(keys)

    markdown = render_markdown(summary_rows, new_lead_rows)
    return summary_rows, new_lead_rows, markdown


def render_markdown(summary_rows: list[dict[str, str]], new_lead_rows: list[dict[str, str]]) -> str:
    by_group: dict[str, Counter[str]] = defaultdict(Counter)
    for row in summary_rows:
        group = row["manifest_group"]
        for field in [
            "raw_result_count",
            "classified_lead_count",
            "candidate_count",
            "candidate_new_to_root_count",
            "candidate_new_to_baseline_manifest_count",
            "routed_or_rejected_count",
            "error_count",
        ]:
            by_group[group][field] += int(row[field] or 0)

    lines = [
        "# Figure 1 Corpus/Database Search Yield",
        "",
        "This diagnostic summarizes saved `corporasearch-*.json` manifests. It is not an input to root-table consolidation.",
        "",
        "## Group Totals",
        "",
        "| Group | Raw results | Classified leads | Candidate leads | Candidates new to root table | Candidates new to baseline manifests | Routed/rejected | Errors |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for group in ["baseline", "expanded"]:
        counts = by_group.get(group, Counter())
        lines.append(
            "| {group} | {raw} | {classified} | {candidate} | {new_root} | {new_baseline} | {routed} | {errors} |".format(
                group=group,
                raw=counts.get("raw_result_count", 0),
                classified=counts.get("classified_lead_count", 0),
                candidate=counts.get("candidate_count", 0),
                new_root=counts.get("candidate_new_to_root_count", 0),
                new_baseline=counts.get("candidate_new_to_baseline_manifest_count", 0),
                routed=counts.get("routed_or_rejected_count", 0),
                errors=counts.get("error_count", 0),
            )
        )

    lines.extend(
        [
            "",
            "## Manifest Detail",
            "",
            "| Manifest | Group | Raw | Candidates | New to root | New to baseline | Routed/rejected | Errors |",
            "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in summary_rows:
        lines.append(
            "| `{manifest}` | {group} | {raw} | {candidate} | {new_root} | {new_baseline} | {routed} | {errors} |".format(
                manifest=row["manifest_path"],
                group=row["manifest_group"],
                raw=row["raw_result_count"],
                candidate=row["candidate_count"],
                new_root=row["candidate_new_to_root_count"],
                new_baseline=row["candidate_new_to_baseline_manifest_count"],
                routed=row["routed_or_rejected_count"],
                errors=row["error_count"],
            )
        )

    lines.extend(["", "## Expanded Candidates New To Root", ""])
    if not new_lead_rows:
        lines.append("No expanded candidate rows were new to the current root table.")
    else:
        lines.extend(
            [
                "| Name | New to baseline manifests | Record kind | Next action |",
                "| --- | --- | --- | --- |",
            ]
        )
        for row in new_lead_rows[:50]:
            lines.append(
                "| {name} | {new_baseline} | {kind} | {next_action} |".format(
                    name=safe_text(row["name"], 160).replace("|", "\\|"),
                    new_baseline=row["new_to_baseline_manifest"],
                    kind=row["record_kind"],
                    next_action=row["next_action"],
                )
            )
        if len(new_lead_rows) > 50:
            lines.append(f"\nAdditional rows omitted from markdown; see `{repo_path(NEW_LEADS_TSV)}`.")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--replace", action="store_true", help="Replace existing summary artifacts.")
    args = parser.parse_args()
    targets = [SUMMARY_TSV, NEW_LEADS_TSV, SUMMARY_MD]
    if any(path.exists() for path in targets) and not args.replace:
        existing = ", ".join(repo_path(path) for path in targets if path.exists())
        print(f"Skipped because summary output exists: {existing}. Use --replace to rerun.")
        return
    summary_rows, new_lead_rows, markdown = summarize()
    write_tsv(
        SUMMARY_TSV,
        summary_rows,
        [
            "manifest_path",
            "manifest_group",
            "strategy_id",
            "strategy",
            "providers",
            "query_count",
            "raw_result_count",
            "classified_lead_count",
            "candidate_count",
            "candidate_unique_lead_count",
            "candidate_new_to_root_count",
            "candidate_new_to_baseline_manifest_count",
            "candidate_new_to_prior_manifest_count",
            "all_lead_unique_count",
            "all_lead_new_to_prior_manifest_count",
            "routed_or_rejected_count",
            "error_count",
            "candidate_record_kind_counts",
            "candidate_status_counts",
        ],
    )
    write_tsv(
        NEW_LEADS_TSV,
        new_lead_rows,
        [
            "manifest_path",
            "name",
            "record_kind",
            "inventory_status",
            "new_to_baseline_manifest",
            "landing_url",
            "source_key",
            "why_relevant",
            "next_action",
        ],
    )
    SUMMARY_MD.write_text(markdown, encoding="utf-8")
    print(
        "Wrote {summary}, {new_leads}, and {markdown}".format(
            summary=repo_path(SUMMARY_TSV),
            new_leads=repo_path(NEW_LEADS_TSV),
            markdown=repo_path(SUMMARY_MD),
        )
    )


if __name__ == "__main__":
    main()
