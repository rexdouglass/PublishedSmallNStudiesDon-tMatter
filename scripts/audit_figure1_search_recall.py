#!/usr/bin/env python3
"""Audit whether Figure 1 search manifests rediscover known-good sources.

This is a recall test for search infrastructure.  The answer key is the current
Plot 1 source catalog: included source families/tables with at least one kept
Figure 1 row.  The retrieval set is the saved Figure 1 ``corporasearch-*.json``
manifests.  Outputs are diagnostic only; they do not edit root tables.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SEARCH_DIR = ROOT / "steps" / "searches" / "figure1"
CATALOG = ROOT / "data/derived/effect_inflation_dataset/plot1_replication_source_catalog.csv"
OUT_TSV = SEARCH_DIR / "searchrecall-figure1-known-sources.tsv"
SUMMARY_TSV = SEARCH_DIR / "searchrecall-figure1-known-sources-summary.tsv"
SUMMARY_MD = SEARCH_DIR / "searchrecall-figure1-known-sources.md"

DOI_RE = re.compile(r"10\.\d{4,9}/[-._;()/:A-Z0-9]+", re.I)

GENERIC_LABEL_WORDS = {
    "manual",
    "csv",
    "table",
    "workbook",
    "data",
    "dataset",
    "project",
    "source",
    "pair",
    "pairs",
    "replication",
    "replications",
    "replicability",
    "repository",
    "corpus",
    "canonical",
    "public",
    "join",
    "local",
    "parsed",
    "supplement",
}

KNOWN_ALIAS_MAP = {
    "FReD filtered pair table": ["FReD", "FORRT Replication Database", "Replication Database"],
    "SCORE analyst join": ["SCORE", "DARPA SCORE", "Systematizing Confidence in Open Research and Evidence"],
    "LOOPR coding workbook": ["LOOPR", "Life Outcomes of Personality Replication"],
    "RPP canonical OSF csv": ["Reproducibility Project: Psychology", "RPP", "OSC 2015"],
    "RPCB": ["Reproducibility Project: Cancer Biology", "RP:CB", "RPCB"],
    "Many Labs 2 public join": ["Many Labs 2", "Investigating Variation in Replicability Across Samples and Settings"],
    "Many Labs 5 overarching analyses": ["Many Labs 5"],
    "ReplicationSuccess SSRP.rda": ["Social Sciences Replication Project", "SSRP"],
    "ReplicationSuccess RProjects.rda": ["Experimental Economics Replication Project", "EERP"],
    "Decision-market pair table": ["Decision Markets", "decision market", "Decision Markets Predict Replicability"],
    "BRI primary t experiment table": ["Brazilian Reproducibility Initiative", "BRI", "reprodutibilidade"],
    "Awesome replicability-data repository": ["awesome-replicability-data", "ying531"],
    "Sports science supplemental outcomes table": ["Sports Science Replication Centre", "sports science replications"],
    "EPRP complete data": ["Experimental Philosophy Replicability Project", "X-Phi Replicability Project", "EPRP"],
}


def safe_text(value: object, max_len: int = 20000) -> str:
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value).replace("\t", " ")).strip()[:max_len]


def repo_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def norm_phrase(value: object) -> str:
    text = safe_text(value).lower()
    text = re.sub(r"https?://(?:dx\.)?doi\.org/", "", text)
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def compact(value: object) -> str:
    return re.sub(r"[^a-z0-9]+", "", norm_phrase(value))


def normalize_url(value: object) -> str:
    text = safe_text(value)
    if not text:
        return ""
    text = re.split(r"\s*\|\s*|\s*;\s*", text)[0]
    text = re.sub(r"^https?://dx\.doi\.org/", "https://doi.org/", text, flags=re.I)
    text = re.sub(r"[?#].*$", "", text)
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


def split_multi(value: object) -> list[str]:
    text = safe_text(value)
    if not text:
        return []
    return [part.strip() for part in re.split(r"\s*\|\s*|\s*;\s*", text) if part.strip()]


def source_aliases(row: dict[str, str]) -> list[str]:
    aliases: list[str] = []
    for field in [
        "canonical_source_label",
        "display_label",
        "source_key",
        "citation_key",
        "display_family_label",
        "source_handle",
    ]:
        value = safe_text(row.get(field))
        if value:
            aliases.append(value)
    aliases.extend(KNOWN_ALIAS_MAP.get(safe_text(row.get("canonical_source_label")), []))
    aliases.extend(KNOWN_ALIAS_MAP.get(safe_text(row.get("display_label")), []))

    out: list[str] = []
    for alias in aliases:
        normalized = norm_phrase(alias)
        if not normalized:
            continue
        words = [word for word in normalized.split() if word not in GENERIC_LABEL_WORDS]
        stripped = " ".join(words)
        for candidate in [normalized, stripped]:
            if len(candidate) >= 4 and candidate not in out:
                out.append(candidate)
    return out


def source_keys(row: dict[str, str]) -> tuple[set[str], set[str], list[str]]:
    urls = {normalize_url(value) for field in ["landing_final_urls", "raw_file", "raw_dirs"] for value in split_multi(row.get(field))}
    urls = {url for url in urls if url}
    dois = {normalize_doi(value) for field in ["landing_final_urls", "raw_file", "raw_dirs", "notes"] for value in split_multi(row.get(field))}
    dois = {doi for doi in dois if doi}
    aliases = source_aliases(row)
    return urls, dois, aliases


def recall_scope(row: dict[str, str]) -> str:
    text = norm_phrase(
        " ".join(
            safe_text(row.get(field))
            for field in [
                "canonical_source_label",
                "display_label",
                "source_family_description",
                "source_catalog_notes",
                "notes",
            ]
        )
    )
    if "hand built appendix" in text or "coverage floor" in text or norm_phrase(row.get("canonical_source_label")) == "appendix d supplemental":
        return "internal_support_not_expected"
    return "external_searchable"


def iter_manifest_records() -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for path in sorted(SEARCH_DIR.glob("corporasearch-*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        if not isinstance(payload, dict):
            continue
        for bucket in ["candidates", "routed_or_rejected_leads", "raw_results"]:
            rows = payload.get(bucket) or []
            if not isinstance(rows, list):
                continue
            for index, row in enumerate(rows):
                if not isinstance(row, dict):
                    continue
                text = json.dumps(row, sort_keys=True, ensure_ascii=False)
                records.append(
                    {
                        "manifest_path": repo_path(path),
                        "strategy_id": safe_text(payload.get("strategy_id")),
                        "bucket": bucket,
                        "row_index": index,
                        "name": safe_text(row.get("name") or row.get("title") or row.get("display_name")),
                        "landing_url": safe_text(row.get("landing_url") or row.get("url") or row.get("raw_url")),
                        "source_key": safe_text(row.get("source_key") or row.get("external_id")),
                        "text": text,
                        "text_norm": norm_phrase(text),
                        "text_compact": compact(text),
                        "doi_values": {normalize_doi(value) for value in DOI_RE.findall(text)},
                        "url_values": {normalize_url(value) for value in re.findall(r"https?://[^\s\"'<>]+", text)},
                    }
                )
    return records


def best_match(row: dict[str, str], records: list[dict[str, Any]]) -> dict[str, Any]:
    urls, dois, aliases = source_keys(row)
    best: dict[str, Any] = {
        "score": 0,
        "match_type": "missed",
        "matched_alias": "",
        "records": [],
    }
    compact_aliases = [(alias, compact(alias)) for alias in aliases if len(compact(alias)) >= 6]

    for record in records:
        score = 0
        match_type = ""
        matched_alias = ""
        if dois and (dois & set(record["doi_values"])):
            score = 100
            match_type = "doi"
            matched_alias = " | ".join(sorted(dois & set(record["doi_values"])))
        elif urls and (urls & set(record["url_values"])):
            score = 95
            match_type = "url"
            matched_alias = " | ".join(sorted(urls & set(record["url_values"])))
        else:
            for alias, alias_compact in compact_aliases:
                if len(alias_compact) < 8:
                    continue
                if alias_compact in record["text_compact"]:
                    score_candidate = min(90, 50 + len(alias_compact) // 2)
                    if score_candidate > score:
                        score = score_candidate
                        match_type = "alias"
                        matched_alias = alias
            if score == 0:
                # Token-overlap fallback for short but distinctive source labels.
                source_tokens = set()
                for alias in aliases:
                    source_tokens.update(word for word in alias.split() if len(word) >= 5 and word not in GENERIC_LABEL_WORDS)
                if len(source_tokens) >= 2:
                    text_tokens = set(record["text_norm"].split())
                    overlap = source_tokens & text_tokens
                    if len(overlap) >= min(3, len(source_tokens)):
                        score = 40 + len(overlap)
                        match_type = "token_overlap"
                        matched_alias = " ".join(sorted(overlap))

        if score > best["score"]:
            best = {
                "score": score,
                "match_type": match_type,
                "matched_alias": matched_alias,
                "records": [record],
            }
        elif score and score == best["score"] and len(best["records"]) < 5:
            best["records"].append(record)

    return best


def load_answer_key() -> list[dict[str, str]]:
    with CATALOG.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        rows = []
        for row in reader:
            try:
                kept = float(row.get("kept_for_figure") or 0)
            except ValueError:
                kept = 0.0
            if row.get("plot_inclusion_status") == "included" and kept > 0:
                rows.append(row)
        return rows


def write_tsv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter="\t", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def render_markdown(rows: list[dict[str, object]], summary_rows: list[dict[str, object]]) -> str:
    missed = [row for row in rows if row["recall_status"] == "missed"]
    missed_external = [row for row in missed if row.get("recall_scope") == "external_searchable"]
    weak = [row for row in rows if row["recall_status"] == "weak_match"]
    found = [row for row in rows if row["recall_status"] == "rediscovered"]
    lines = [
        "# Figure 1 Search Recall Audit",
        "",
        "This diagnostic checks whether saved Figure 1 search manifests rediscover known-good Figure 1 source collections.",
        "",
        "Definitions:",
        "",
        "- Known-good source: an included Plot 1 source-family/source-table row with at least one kept Figure 1 pair.",
        "- Rediscovered: a saved `corporasearch-*.json` row matched the known source by DOI, URL, alias, or distinctive token overlap.",
        "- Weak match: matched only by low-specificity token overlap and should be manually checked.",
        "- Missed: no saved search manifest row matched the known source.",
        "- Internal support source: a hand-built/local audit artifact that is useful for Figure 1 but is not expected to be rediscovered by external search.",
        "",
        "## Summary",
        "",
        "| Metric | Value |",
        "| --- | ---: |",
    ]
    for row in summary_rows:
        lines.append(f"| {row['metric']} | {row['value']} |")

    lines.extend(["", "## Missed External Sources", ""])
    if not missed_external:
        lines.append("No externally searchable known-good sources were missed.")
    else:
        lines.extend(["| Source | Kept Figure 1 Rows | Citation Key | Best Available URL/Path |", "| --- | ---: | --- | --- |"])
        for row in missed_external:
            lines.append(
                "| {source} | {kept} | {citation} | `{path}` |".format(
                    source=safe_text(row["canonical_source_label"], 120).replace("|", "\\|"),
                    kept=row["kept_for_figure"],
                    citation=safe_text(row["citation_key"], 80).replace("|", "\\|"),
                    path=safe_text(row["best_source_location"], 140).replace("|", "\\|"),
                )
            )

    internal_missed = [row for row in missed if row.get("recall_scope") == "internal_support_not_expected"]
    if internal_missed:
        lines.extend(["", "## Internal Support Sources Not Expected In Search", "", "| Source | Kept Figure 1 Rows | Reason |", "| --- | ---: | --- |"])
        for row in internal_missed:
            lines.append(
                "| {source} | {kept} | internal hand-built/support artifact |".format(
                    source=safe_text(row["canonical_source_label"], 120).replace("|", "\\|"),
                    kept=row["kept_for_figure"],
                )
            )

    if weak:
        lines.extend(["", "## Weak Matches To Check", "", "| Source | Match Type | Matched Alias | Search Row |", "| --- | --- | --- | --- |"])
        for row in weak[:30]:
            lines.append(
                "| {source} | {kind} | {alias} | {match} |".format(
                    source=safe_text(row["canonical_source_label"], 100).replace("|", "\\|"),
                    kind=row["match_type"],
                    alias=safe_text(row["matched_alias"], 100).replace("|", "\\|"),
                    match=safe_text(row["matched_record_names"], 160).replace("|", "\\|"),
                )
            )

    lines.extend(["", "## Top Rediscovered Sources", "", "| Source | Kept Figure 1 Rows | Match Type | Search Row |", "| --- | ---: | --- | --- |"])
    for row in sorted(found, key=lambda item: float(item["kept_for_figure"]), reverse=True)[:25]:
        lines.append(
            "| {source} | {kept} | {kind} | {match} |".format(
                source=safe_text(row["canonical_source_label"], 100).replace("|", "\\|"),
                kept=row["kept_for_figure"],
                kind=row["match_type"],
                match=safe_text(row["matched_record_names"], 160).replace("|", "\\|"),
            )
        )
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--replace", action="store_true", help="Replace existing audit outputs.")
    args = parser.parse_args()
    targets = [OUT_TSV, SUMMARY_TSV, SUMMARY_MD]
    if any(path.exists() for path in targets) and not args.replace:
        existing = ", ".join(repo_path(path) for path in targets if path.exists())
        print(f"Skipped because output exists: {existing}. Use --replace to rerun.")
        return

    answer_key = load_answer_key()
    records = iter_manifest_records()
    out_rows: list[dict[str, object]] = []
    for row in answer_key:
        match = best_match(row, records)
        scope = recall_scope(row)
        score = int(match["score"])
        if score >= 50:
            status = "rediscovered"
        elif score > 0:
            status = "weak_match"
        else:
            status = "missed"
        matched_records = match["records"]
        out_rows.append(
            {
                "canonical_source_id": row.get("canonical_source_id", ""),
                "canonical_source_label": row.get("canonical_source_label", ""),
                "display_label": row.get("display_label", ""),
                "source_key": row.get("source_key", ""),
                "citation_key": row.get("citation_key", ""),
                "kept_for_figure": row.get("kept_for_figure", ""),
                "live_pair_rows": row.get("live_pair_rows", ""),
                "recall_scope": scope,
                "recall_status": status,
                "best_match_score": score,
                "match_type": match["match_type"],
                "matched_alias": match["matched_alias"],
                "matched_manifest_paths": " | ".join(record["manifest_path"] for record in matched_records),
                "matched_buckets": " | ".join(record["bucket"] for record in matched_records),
                "matched_record_names": " | ".join(record["name"] or record["source_key"] or record["landing_url"] for record in matched_records),
                "best_source_location": row.get("landing_final_urls") or row.get("raw_file") or row.get("raw_dirs") or "",
            }
        )

    counts = Counter(row["recall_status"] for row in out_rows)
    scope_counts = Counter(row["recall_scope"] for row in out_rows)
    searchable_rows = [row for row in out_rows if row["recall_scope"] == "external_searchable"]
    searchable_counts = Counter(row["recall_status"] for row in searchable_rows)
    kept_total = sum(float(row["kept_for_figure"] or 0) for row in out_rows)
    kept_found = sum(float(row["kept_for_figure"] or 0) for row in out_rows if row["recall_status"] == "rediscovered")
    summary_rows: list[dict[str, object]] = [
        {"metric": "known_good_sources", "value": len(out_rows)},
        {"metric": "rediscovered_sources", "value": counts["rediscovered"]},
        {"metric": "weak_match_sources", "value": counts["weak_match"]},
        {"metric": "missed_sources", "value": counts["missed"]},
        {"metric": "source_recall_percent", "value": f"{counts['rediscovered'] / len(out_rows) * 100:.1f}" if out_rows else "0.0"},
        {"metric": "external_searchable_sources", "value": scope_counts["external_searchable"]},
        {"metric": "external_searchable_rediscovered_sources", "value": searchable_counts["rediscovered"]},
        {"metric": "external_searchable_missed_sources", "value": searchable_counts["missed"]},
        {
            "metric": "external_searchable_source_recall_percent",
            "value": f"{searchable_counts['rediscovered'] / len(searchable_rows) * 100:.1f}" if searchable_rows else "0.0",
        },
        {"metric": "internal_support_sources_not_expected_in_search", "value": scope_counts["internal_support_not_expected"]},
        {"metric": "kept_figure1_rows_total", "value": f"{kept_total:.0f}"},
        {"metric": "kept_figure1_rows_rediscovered", "value": f"{kept_found:.0f}"},
        {"metric": "kept_row_recall_percent", "value": f"{kept_found / kept_total * 100:.1f}" if kept_total else "0.0"},
        {"metric": "search_manifest_records", "value": len(records)},
    ]

    write_tsv(
        OUT_TSV,
        out_rows,
        [
            "canonical_source_id",
            "canonical_source_label",
            "display_label",
            "source_key",
            "citation_key",
            "kept_for_figure",
            "live_pair_rows",
            "recall_scope",
            "recall_status",
            "best_match_score",
            "match_type",
            "matched_alias",
            "matched_manifest_paths",
            "matched_buckets",
            "matched_record_names",
            "best_source_location",
        ],
    )
    write_tsv(SUMMARY_TSV, summary_rows, ["metric", "value"])
    SUMMARY_MD.write_text(render_markdown(out_rows, summary_rows), encoding="utf-8")
    print(f"Wrote {repo_path(OUT_TSV)}, {repo_path(SUMMARY_TSV)}, and {repo_path(SUMMARY_MD)}")


if __name__ == "__main__":
    main()
