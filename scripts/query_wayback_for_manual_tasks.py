#!/usr/bin/env python3
"""Query Wayback for pilot manual-acquisition candidate URLs.

This creates acquisition leads only. A Wayback hit is not evidence that D/N was
verified; it only tells a human or later mirroring pass that archived bytes may
exist for a landing page, registry page, abstract page, or source object.
"""

from __future__ import annotations

import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
PILOT = ROOT / "data" / "derived" / "effect_inflation_dataset" / "schema_pilot"
SAMPLE_N = int(os.environ.get("SCHEMA_PILOT_N", "300"))
SAMPLE_SUFFIX = f"sample_{SAMPLE_N}"

MANUAL_TASKS_IN = PILOT / f"manual_acquisition_task_codebook_{SAMPLE_SUFFIX}.tsv"

OUT_TSV = PILOT / f"wayback_cdx_manual_task_attempts_{SAMPLE_SUFFIX}.tsv"
OUT_SUMMARY = PILOT / f"wayback_cdx_manual_task_attempts_summary_{SAMPLE_SUFFIX}.tsv"
OUT_REPORT = ROOT / "reports" / f"wayback_cdx_manual_task_attempts_{SAMPLE_SUFFIX}_2026-04-30.md"

TASK_LIMIT = int(os.environ.get("WAYBACK_TASK_LIMIT", "20"))
URLS_PER_TASK = int(os.environ.get("WAYBACK_URLS_PER_TASK", "2"))
CAPTURES_PER_URL = int(os.environ.get("WAYBACK_CAPTURES_PER_URL", "5"))
REQUEST_DELAY_SECONDS = float(os.environ.get("WAYBACK_REQUEST_DELAY_SECONDS", "0.25"))
REQUEST_TIMEOUT_SECONDS = int(os.environ.get("WAYBACK_REQUEST_TIMEOUT_SECONDS", "5"))
LOOKUP_MODE = os.environ.get("WAYBACK_LOOKUP_MODE", "available").strip().lower()
INCLUDE_URL_VARIANTS = os.environ.get("WAYBACK_INCLUDE_URL_VARIANTS", "false").strip().lower() in {"1", "true", "yes"}
USER_AGENT = os.environ.get(
    "WAYBACK_USER_AGENT",
    "PublishedSmallNStudiesEvidenceMap/0.1 (mailto:rexdouglass@gmail.com)",
)


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


def split_candidate_urls(value: object) -> list[str]:
    text = safe_text(value)
    if not text:
        return []
    items = [item.strip() for item in re.split(r"\s+\|\s+|\|", text) if item.strip()]
    seen: set[str] = set()
    urls: list[str] = []
    for item in items:
        if not re.match(r"^https?://", item, flags=re.I):
            continue
        if item not in seen:
            urls.append(item)
            seen.add(item)
    return urls


def candidate_variants(url: str) -> list[tuple[str, str]]:
    variants = [(url, "as_listed")]

    doi_match = re.search(r"https?://(?:dx\.)?doi\.org/(10\..+)$", url, flags=re.I)
    if doi_match:
        doi = doi_match.group(1).strip()
        for variant in [f"https://doi.org/{doi}", f"http://dx.doi.org/{doi}"]:
            if all(existing != variant for existing, _ in variants):
                variants.append((variant, "doi_variant"))

    nct_match = re.search(r"(NCT\d{8})", url, flags=re.I)
    if nct_match and "clinicaltrials.gov" in url.lower():
        nct = nct_match.group(1).upper()
        for variant in [f"https://clinicaltrials.gov/study/{nct}", f"https://clinicaltrials.gov/ct2/show/{nct}"]:
            if all(existing != variant for existing, _ in variants):
                variants.append((variant, "clinicaltrials_variant"))

    return variants


def classify_url(url: str) -> str:
    lower = url.lower()
    if "doi.org/" in lower:
        return "doi_resolver"
    if "clinicaltrials.gov" in lower:
        return "clinicaltrials"
    if "pubmed.ncbi.nlm.nih.gov" in lower:
        return "pubmed"
    if "socialscienceregistry.org" in lower:
        return "aea_registry"
    if "osf.io" in lower:
        return "osf"
    return urllib.parse.urlparse(url).netloc.lower() or "unknown"


def cdx_query_url(url: str) -> str:
    params = {
        "url": url,
        "output": "json",
        "fl": "timestamp,original,statuscode,mimetype,digest,length",
        "filter": "statuscode:200",
        "collapse": "digest",
        "limit": str(CAPTURES_PER_URL),
    }
    return "https://web.archive.org/cdx/search/cdx?" + urllib.parse.urlencode(params)


def available_query_url(url: str, target: datetime | None) -> str:
    timestamp = ""
    if target is not None:
        timestamp = target.strftime("%Y%m%d")
    params = {"url": url}
    if timestamp:
        params["timestamp"] = timestamp
    return "https://archive.org/wayback/available?" + urllib.parse.urlencode(params)


def fetch_cdx(url: str) -> tuple[str, list[dict[str, str]], str, str]:
    query = cdx_query_url(url)
    request = urllib.request.Request(query, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            raw = response.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        return query, [], "http_error", f"{exc.code}:{exc.reason}"
    except urllib.error.URLError as exc:
        return query, [], "url_error", safe_text(exc.reason)
    except TimeoutError as exc:
        return query, [], "timeout", safe_text(exc)
    except OSError as exc:
        return query, [], "os_error", f"{type(exc).__name__}:{exc}"

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        return query, [], "json_error", f"{type(exc).__name__}:{exc}"

    if not payload:
        return query, [], "ok", ""
    if not isinstance(payload, list) or not isinstance(payload[0], list):
        return query, [], "unexpected_payload", raw[:200]

    header = payload[0]
    captures: list[dict[str, str]] = []
    for row in payload[1:]:
        if len(row) != len(header):
            continue
        captures.append({str(key): safe_text(value) for key, value in zip(header, row)})
    return query, captures, "ok", ""


def fetch_available(url: str, target: datetime | None) -> tuple[str, list[dict[str, str]], str, str]:
    query = available_query_url(url, target)
    request = urllib.request.Request(query, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            raw = response.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        return query, [], "http_error", f"{exc.code}:{exc.reason}"
    except urllib.error.URLError as exc:
        return query, [], "url_error", safe_text(exc.reason)
    except TimeoutError as exc:
        return query, [], "timeout", safe_text(exc)
    except OSError as exc:
        return query, [], "os_error", f"{type(exc).__name__}:{exc}"

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        return query, [], "json_error", f"{type(exc).__name__}:{exc}"

    closest = payload.get("archived_snapshots", {}).get("closest") if isinstance(payload, dict) else None
    if not closest:
        return query, [], "ok", ""
    timestamp = safe_text(closest.get("timestamp"))
    capture = {
        "timestamp": timestamp,
        "original": url,
        "statuscode": safe_text(closest.get("status")),
        "mimetype": "",
        "digest": "",
        "length": "",
        "archive_url": safe_text(closest.get("url")),
    }
    return query, [capture], "ok", ""


def parse_opened_at(value: object) -> datetime | None:
    text = safe_text(value)
    if not text:
        return None
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return None


def parse_wayback_ts(value: str) -> datetime | None:
    try:
        return datetime.strptime(value, "%Y%m%d%H%M%S").replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def closest_capture(captures: list[dict[str, str]], target: datetime | None) -> dict[str, str] | None:
    if not captures:
        return None
    if target is None:
        return captures[-1]
    if target.tzinfo is None:
        target = target.replace(tzinfo=timezone.utc)
    scored: list[tuple[float, dict[str, str]]] = []
    for capture in captures:
        ts = parse_wayback_ts(capture.get("timestamp", ""))
        if ts is None:
            continue
        scored.append((abs((ts - target).total_seconds()), capture))
    if not scored:
        return captures[-1]
    scored.sort(key=lambda item: item[0])
    return scored[0][1]


def archive_url(capture: dict[str, str]) -> str:
    explicit = capture.get("archive_url", "")
    if explicit:
        return explicit
    timestamp = capture.get("timestamp", "")
    original = capture.get("original", "")
    if not timestamp or not original:
        return ""
    return f"https://web.archive.org/web/{timestamp}id_/{original}"


def main() -> None:
    all_tasks = pd.read_csv(MANUAL_TASKS_IN, sep="\t", dtype=str, keep_default_na=False)
    manual_tasks_with_urls_available = int(all_tasks["best_candidate_urls"].astype(bool).sum())
    tasks = all_tasks.copy()
    tasks["priority_score_numeric"] = pd.to_numeric(tasks["priority_score"], errors="coerce").fillna(0)
    tasks = tasks.loc[tasks["best_candidate_urls"].astype(bool)].copy()
    tasks = tasks.sort_values(["priority_score_numeric", "manual_task_id"], ascending=[False, True]).head(TASK_LIMIT)

    rows: list[dict[str, object]] = []
    for _, task in tasks.iterrows():
        opened_at = parse_opened_at(task.get("opened_at"))
        variants: list[tuple[str, str]] = []
        for listed_url in split_candidate_urls(task.get("best_candidate_urls"))[:URLS_PER_TASK]:
            if INCLUDE_URL_VARIANTS:
                variants.extend(candidate_variants(listed_url))
            else:
                variants.append((listed_url, "as_listed"))
        seen: set[str] = set()
        deduped = []
        for url, basis in variants:
            if url not in seen:
                deduped.append((url, basis))
                seen.add(url)

        if not deduped:
            rows.append(
                {
                    "manual_task_id": safe_text(task.get("manual_task_id")),
                    "source_result_id": safe_text(task.get("source_result_id")),
                    "cdx_status": "no_queryable_url",
                    "recommended_next_action": "No HTTP candidate URL available for Wayback CDX.",
                }
            )
            continue

        for candidate_url, variant_basis in deduped:
            if LOOKUP_MODE == "cdx":
                query_url, captures, status, error = fetch_cdx(candidate_url)
            else:
                query_url, captures, status, error = fetch_available(candidate_url, opened_at)
            nearest = closest_capture(captures, opened_at)
            timestamps = [capture.get("timestamp", "") for capture in captures]
            digests = [capture.get("digest", "") for capture in captures]
            archive_urls = [archive_url(capture) for capture in captures if archive_url(capture)]
            nearest_url = archive_url(nearest or {})
            recommended = (
                "Review archived capture content; mirror bytes and classify byte class before any evidence promotion."
                if captures
                else "No 200-status CDX capture in this pilot pass; continue repository/API/manual acquisition route."
            )
            rows.append(
                {
                    "manual_task_id": safe_text(task.get("manual_task_id")),
                    "source_result_id": safe_text(task.get("source_result_id")),
                    "canonical_result_id": safe_text(task.get("canonical_result_id")),
                    "represented_source_id": safe_text(task.get("represented_source_id")),
                    "extraction_source_id": safe_text(task.get("extraction_source_id")),
                    "needed_artifact_type": safe_text(task.get("needed_artifact_type")),
                    "priority_score": safe_text(task.get("priority_score")),
                    "candidate_url": candidate_url,
                    "candidate_url_kind": classify_url(candidate_url),
                    "candidate_variant_basis": variant_basis,
                    "wayback_query_url": query_url,
                    "cdx_status": status,
                    "cdx_error": error,
                    "capture_count_returned": len(captures),
                    "first_capture_timestamp": min(timestamps) if timestamps else "",
                    "latest_capture_timestamp": max(timestamps) if timestamps else "",
                    "closest_to_opened_at_timestamp": (nearest or {}).get("timestamp", ""),
                    "closest_to_opened_at_archive_url": nearest_url,
                    "target_timestamp_basis": "manual_task_opened_at_not_corpus_extraction_date" if opened_at else "",
                    "capture_timestamps": "|".join(timestamps),
                    "capture_digests": "|".join(digests),
                    "archive_urls": "|".join(archive_urls),
                    "evidence_ceiling_if_only_landing_capture": "level_3_or_4_unless_exact_value_text_present",
                    "recommended_next_action": recommended,
                }
            )
            time.sleep(REQUEST_DELAY_SECONDS)

    out = pd.DataFrame(rows)
    OUT_TSV.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT_TSV, sep="\t", index=False)

    hit_mask = out.get("capture_count_returned", pd.Series(dtype=int)).fillna(0).astype(int).gt(0)
    summary_rows: list[dict[str, object]] = [
        {"metric": "sample_n", "value": SAMPLE_N},
        {"metric": "manual_tasks_with_urls_available", "value": manual_tasks_with_urls_available},
        {"metric": "manual_tasks_queried", "value": int(tasks["manual_task_id"].nunique())},
        {"metric": "url_variants_queried", "value": int(len(out))},
        {"metric": "url_variants_with_wayback_capture", "value": int(hit_mask.sum())},
        {"metric": "manual_tasks_with_any_wayback_capture", "value": int(out.loc[hit_mask, "manual_task_id"].nunique()) if not out.empty else 0},
        {"metric": "task_limit", "value": TASK_LIMIT},
        {"metric": "urls_per_task", "value": URLS_PER_TASK},
        {"metric": "captures_per_url", "value": CAPTURES_PER_URL},
        {"metric": "lookup_mode", "value": LOOKUP_MODE},
        {"metric": "include_url_variants", "value": str(INCLUDE_URL_VARIANTS).lower()},
        {"metric": "created_at_utc", "value": datetime.now(timezone.utc).isoformat()},
    ]
    for key, value in out.get("candidate_url_kind", pd.Series(dtype=str)).value_counts().sort_index().items():
        summary_rows.append({"metric": f"candidate_url_kind::{key}", "value": int(value)})
    for key, value in out.get("cdx_status", pd.Series(dtype=str)).value_counts().sort_index().items():
        summary_rows.append({"metric": f"cdx_status::{key}", "value": int(value)})
    summary = pd.DataFrame(summary_rows)
    summary.to_csv(OUT_SUMMARY, sep="\t", index=False)

    hits = out.loc[hit_mask].copy()
    lines = [
        "# Wayback Manual-Task Lead Pass",
        "",
        f"- Sample rows: {SAMPLE_N}",
        f"- Open manual tasks with candidate URLs: {manual_tasks_with_urls_available}",
        f"- Manual tasks queried in this polite pilot pass: {int(tasks['manual_task_id'].nunique())}",
        f"- URL variants queried: {len(out)}",
        f"- URL variants with at least one Wayback capture: {int(hit_mask.sum())}",
        f"- Manual tasks with at least one capture lead: {int(hits['manual_task_id'].nunique()) if not hits.empty else 0}",
        "",
        "## Interpretation",
        "",
        "- These rows are acquisition leads only. A Wayback capture must still be mirrored, checksummed, byte-classified, and inspected before it changes any evidence level.",
        "- A landing-page or abstract capture remains level 3/4 unless the exact value-bearing D/N text is present in the archived bytes.",
        "- The target timestamp in this pilot is the manual task opening date, not the original corpus extraction date; source-version work still needs true corpus as-of dates.",
        "",
        "## First Capture Leads",
        "",
    ]
    for _, row in hits.head(25).iterrows():
        lines.append(
            f"- `{row['manual_task_id']}` `{row['candidate_url_kind']}` captures={int(row['capture_count_returned'])}; "
            f"closest `{row['closest_to_opened_at_timestamp']}` {row['closest_to_opened_at_archive_url']}"
        )
    lines.extend(["", "## Output Files", "", f"- `{rel(OUT_TSV)}`", f"- `{rel(OUT_SUMMARY)}`"])
    OUT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    OUT_REPORT.write_text("\n".join(lines) + "\n")

    print(f"Wrote {OUT_TSV}")
    print(f"Wrote {OUT_SUMMARY}")
    print(f"Wrote {OUT_REPORT}")
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
