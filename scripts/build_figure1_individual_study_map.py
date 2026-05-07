#!/usr/bin/env python3
"""Build a dedupe registry of individual studies represented in Figure 1.

Inputs come from the Figure 1 pair-chase lane. The output grain is one row per
represented individual source/study identity, deduped by DOI first, URL second,
and normalized title third. It is deliberately a staging/dedupe artifact: no root
plot rows or provenance source_result rows are mutated here.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
from collections import Counter
from pathlib import Path
from typing import Iterable
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
PAIR_CHASE_DIR = ROOT / "steps" / "individual_replication_papers" / "figure1" / "pair_chase"
DEFAULT_SIDE_TARGETS = PAIR_CHASE_DIR / "figure1-pair-source-side-targets.tsv"
DEFAULT_PAIR_WORKLIST = PAIR_CHASE_DIR / "figure1-pair-chase-worklist.tsv"
DEFAULT_OUTPUT_DIR = PAIR_CHASE_DIR

STUDY_COLUMNS = [
    "figure1_individual_study_id",
    "study_dedupe_key",
    "study_dedupe_method",
    "dedupe_confidence",
    "represented_title_canonical",
    "represented_doi_canonical",
    "represented_url_canonical",
    "doi_url",
    "is_url_title",
    "roles_observed",
    "n_side_targets",
    "n_distinct_pairs",
    "n_included_pairs",
    "n_excluded_pairs",
    "n_original_side_targets",
    "n_replication_side_targets",
    "current_plot_rule_statuses",
    "current_plot_rule_blockers",
    "source_family_keys",
    "source_family_labels",
    "pair_chase_priorities",
    "pair_chase_routes",
    "side_source_object_routes",
    "side_source_object_priorities",
    "D_min",
    "D_max",
    "N_min",
    "N_max",
    "side_target_ids_json",
    "figure1_replication_pair_ids_json",
    "pair_chase_task_ids_json",
    "source_object_seed_urls_json",
    "side_search_queries_json",
    "pair_relation_search_queries_json",
    "needs_manual_identity_review",
    "identity_review_reason",
    "next_action",
    "created_at",
]

MAPPING_COLUMNS = [
    "source_side_target_id",
    "figure1_individual_study_id",
    "study_dedupe_key",
    "study_dedupe_method",
    "dedupe_confidence",
    "pair_chase_task_id",
    "figure1_replication_pair_id",
    "current_plot_rule_status",
    "current_plot_rule_blockers",
    "included_in_current_figure1",
    "side",
    "represented_title",
    "represented_doi",
    "represented_value_D",
    "represented_value_N",
    "strict_result_check_id",
    "source_family_key",
    "source_family_label",
    "side_source_object_route",
    "side_source_object_priority",
    "target_source_object_seed_url",
    "side_search_query",
    "pair_relation_search_query",
    "needed_verbatim_fields",
    "pair_chase_priority",
    "pair_chase_route",
    "created_at",
]

SCHEMA = {
    "figure1_individual_study_id": "Stable ID for the deduped represented individual study/source row.",
    "study_dedupe_key": "Machine key used to group side targets. DOI keys are preferred, then URL, then normalized title.",
    "study_dedupe_method": "Dedupe method: doi, url, title, or weak_side_target.",
    "dedupe_confidence": "High for DOI, medium for URL, low for title-only, very_low for weak fallback.",
    "represented_title_canonical": "Most useful nonblank title/label for this represented source identity.",
    "represented_doi_canonical": "Canonical normalized DOI when any side target in the group has a DOI.",
    "represented_url_canonical": "Canonical URL seed when available from DOI, source URL, or represented URL label.",
    "doi_url": "https://doi.org URL for the canonical DOI.",
    "is_url_title": "True when any side target used a URL as its represented title/label.",
    "roles_observed": "Pipe-delimited observed roles among original and replication.",
    "n_side_targets": "Number of side-target rows collapsed into this study/source row.",
    "n_distinct_pairs": "Number of distinct plotted Figure 1 pairs touching this study/source row.",
    "n_included_pairs": "Number of distinct pair rows touching this study/source that are included under the current Figure 1 rule.",
    "n_excluded_pairs": "Number of distinct pair rows touching this study/source that are excluded under the current Figure 1 rule but retained for dedupe.",
    "n_original_side_targets": "Count of original-side target rows in this group.",
    "n_replication_side_targets": "Count of replication/follow-up-side target rows in this group.",
    "current_plot_rule_statuses": "Pipe-delimited current plot-rule statuses observed among pair sides touching this study/source.",
    "current_plot_rule_blockers": "Pipe-delimited plot-rule blockers observed for excluded pairs touching this study/source.",
    "source_family_keys": "Pipe-delimited source families that asserted rows touching this study/source.",
    "source_family_labels": "Pipe-delimited source-family labels.",
    "pair_chase_priorities": "Pipe-delimited pair-chase priority codes observed for this study/source.",
    "pair_chase_routes": "Pipe-delimited pair-chase routes observed for this study/source.",
    "side_source_object_routes": "Pipe-delimited side-level acquisition/search routes.",
    "side_source_object_priorities": "Pipe-delimited side-level acquisition/search priorities.",
    "D_min": "Minimum represented D value among side targets in this group.",
    "D_max": "Maximum represented D value among side targets in this group.",
    "N_min": "Minimum represented N value among side targets in this group.",
    "N_max": "Maximum represented N value among side targets in this group.",
    "side_target_ids_json": "JSON array of source_side_target_id values collapsed into this row.",
    "figure1_replication_pair_ids_json": "JSON array of plotted pair IDs touching this study/source.",
    "pair_chase_task_ids_json": "JSON array of pair-chase task IDs touching this study/source.",
    "source_object_seed_urls_json": "JSON array of DOI/source URL seeds to try for local mirroring.",
    "side_search_queries_json": "JSON array of side-specific search queries.",
    "pair_relation_search_queries_json": "JSON array of pair-relation search queries.",
    "needs_manual_identity_review": "True when the dedupe identity is title-only/weak or otherwise likely ambiguous.",
    "identity_review_reason": "Compact reason for manual identity review.",
    "next_action": "Recommended next source-object/value-verification action for this study/source.",
    "created_at": "Generation timestamp for this deterministic artifact.",
}


def clean(value: object) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    if text.lower() in {"nan", "none", "null"}:
        return ""
    return text


def stable_id(prefix: str, parts: Iterable[object], length: int = 16) -> str:
    raw = "||".join(clean(part) for part in parts)
    digest = hashlib.sha1(raw.encode("utf-8")).hexdigest()[:length]
    return f"{prefix}_{digest}"


def normalize_doi(value: object) -> str:
    text = clean(value)
    if not text:
        return ""
    lowered = text.lower()
    for prefix in ("https://doi.org/", "http://doi.org/", "doi:"):
        if lowered.startswith(prefix):
            text = text[len(prefix) :]
            break
    return text.strip().rstrip(".").lower()


def doi_url(value: object) -> str:
    doi = normalize_doi(value)
    return f"https://doi.org/{doi}" if doi else ""


def is_url(value: object) -> bool:
    text = clean(value).lower()
    return text.startswith("http://") or text.startswith("https://")


def normalize_url(value: object) -> str:
    text = clean(value)
    if not is_url(text):
        return ""
    split = urlsplit(text)
    query_pairs = [
        (k, v)
        for k, v in parse_qsl(split.query, keep_blank_values=True)
        if not k.lower().startswith("utm_")
    ]
    query = urlencode(query_pairs, doseq=True)
    path = split.path.rstrip("/") or split.path
    return urlunsplit((split.scheme.lower(), split.netloc.lower(), path, query, "")).strip()


def title_key(value: object) -> str:
    text = html.unescape(clean(value))
    text = text.replace("&amp;", "&")
    text = re.sub(r"https?://\S+", " ", text)
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def looks_weak_title(value: object) -> bool:
    text = clean(value)
    key = title_key(text)
    if not key or len(key) < 8:
        return True
    weak_patterns = [
        r"^paper \d+",
        r"^study \d+",
        r"^experiment \d+",
        r"^replication$",
        r"^original$",
        r"^unknown$",
    ]
    return any(re.search(pattern, key) for pattern in weak_patterns)


def identity_for(row: pd.Series) -> tuple[str, str, str, str]:
    doi = normalize_doi(row.get("represented_doi"))
    if doi:
        return f"doi:{doi}", "doi", "high", ""

    url = normalize_url(row.get("target_source_object_seed_url")) or normalize_url(
        row.get("represented_title")
    )
    if url:
        return f"url:{url}", "url", "medium", ""

    title = clean(row.get("represented_title"))
    key = title_key(title)
    if key and not looks_weak_title(title):
        return f"title:{key}", "title", "low", "title_only_identity"

    fallback = clean(row.get("source_side_target_id"))
    return (
        f"weak_side_target:{fallback}",
        "weak_side_target",
        "very_low",
        "weak_or_missing_title_and_no_doi_or_url",
    )


def unique_nonblank(values: Iterable[object]) -> list[str]:
    seen = []
    existing = set()
    for value in values:
        text = clean(value)
        if text and text not in existing:
            seen.append(text)
            existing.add(text)
    return seen


def pipe_join(values: Iterable[object]) -> str:
    return "|".join(unique_nonblank(values))


def json_list(values: Iterable[object]) -> str:
    return json.dumps(unique_nonblank(values), ensure_ascii=True)


def most_common_nonblank(values: Iterable[object], prefer_not_url: bool = False) -> str:
    cleaned = [clean(v) for v in values if clean(v)]
    if prefer_not_url:
        non_url = [v for v in cleaned if not is_url(v)]
        if non_url:
            cleaned = non_url
    if not cleaned:
        return ""
    return Counter(cleaned).most_common(1)[0][0]


def numeric_minmax(values: pd.Series) -> tuple[str, str]:
    nums = pd.to_numeric(values, errors="coerce").dropna()
    if nums.empty:
        return "", ""
    return f"{nums.min():.12g}", f"{nums.max():.12g}"


def next_action_for(group: pd.DataFrame, method: str) -> str:
    included = group["included_in_current_figure1"].eq("true").any()
    if not included:
        return "Keep as a no-repull dedupe target for excluded Figure 1 pairs; defer source-object/value extraction unless analytic rules change or a new candidate collides."
    routes = set(group["side_source_object_route"].map(clean))
    if "existing_value_text_promotion" in routes:
        return "Promote existing value-bearing rows into source_result/source_result_support; then chase represented source objects where missing."
    if "doi_source_object_acquisition" in routes:
        return "Resolve DOI(s), mirror value-bearing source object(s), and extract verbatim D/N/result text."
    if "url_source_object_acquisition" in routes:
        return "Mirror represented URL source object(s) and extract verbatim D/N/result text if value-bearing."
    if method == "title":
        return "Run title search to locate DOI/OA source object before value verification."
    return "Backfill bibliographic identity from source family before source-object acquisition."


def manual_review_reason(group: pd.DataFrame, method: str, base_reason: str) -> str:
    reasons = []
    if base_reason:
        reasons.append(base_reason)
    if method in {"title", "weak_side_target"}:
        reasons.append("dedupe_not_doi_based")
    if group["source_family_key"].nunique() > 1 and method != "doi":
        reasons.append("non_doi_identity_spans_source_families")
    if group["represented_title"].map(looks_weak_title).any():
        reasons.append("weak_title_label_present")
    return "|".join(dict.fromkeys(reasons))


def build_maps(side_targets: pd.DataFrame, pair_worklist: pd.DataFrame, created_at: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    pair_cols = [
        "pair_chase_task_id",
        "pair_chase_priority",
        "pair_chase_route",
    ]
    merged = side_targets.merge(pair_worklist[pair_cols], on="pair_chase_task_id", how="left")

    identities = merged.apply(identity_for, axis=1, result_type="expand")
    identities.columns = [
        "study_dedupe_key",
        "study_dedupe_method",
        "dedupe_confidence",
        "identity_base_review_reason",
    ]
    merged = pd.concat([merged, identities], axis=1)
    merged["figure1_individual_study_id"] = merged.apply(
        lambda row: stable_id("figure1_individual_study", [row["study_dedupe_key"]]),
        axis=1,
    )

    study_rows = []
    for _, group in merged.groupby("figure1_individual_study_id", sort=False):
        first = group.iloc[0]
        method = clean(first["study_dedupe_method"])
        doi = most_common_nonblank(group["represented_doi"].map(normalize_doi))
        title = most_common_nonblank(group["represented_title"], prefer_not_url=True)
        url = (
            doi_url(doi)
            or most_common_nonblank(group["target_source_object_seed_url"].map(normalize_url))
            or most_common_nonblank(group["represented_title"].map(normalize_url))
        )
        d_min, d_max = numeric_minmax(group["represented_value_D"])
        n_min, n_max = numeric_minmax(group["represented_value_N"])
        reason = manual_review_reason(group, method, clean(first["identity_base_review_reason"]))
        needs_review = "true" if reason else "false"
        study_rows.append(
            {
                "figure1_individual_study_id": clean(first["figure1_individual_study_id"]),
                "study_dedupe_key": clean(first["study_dedupe_key"]),
                "study_dedupe_method": method,
                "dedupe_confidence": clean(first["dedupe_confidence"]),
                "represented_title_canonical": title,
                "represented_doi_canonical": doi,
                "represented_url_canonical": url,
                "doi_url": doi_url(doi),
                "is_url_title": "true" if group["represented_title"].map(is_url).any() else "false",
                "roles_observed": pipe_join(sorted(group["side"].unique())),
                "n_side_targets": str(len(group)),
                "n_distinct_pairs": str(group["figure1_replication_pair_id"].nunique()),
                "n_included_pairs": str(
                    group.loc[
                        group["included_in_current_figure1"].eq("true"),
                        "figure1_replication_pair_id",
                    ].nunique()
                ),
                "n_excluded_pairs": str(
                    group.loc[
                        group["included_in_current_figure1"].ne("true"),
                        "figure1_replication_pair_id",
                    ].nunique()
                ),
                "n_original_side_targets": str((group["side"] == "original").sum()),
                "n_replication_side_targets": str((group["side"] == "replication").sum()),
                "current_plot_rule_statuses": pipe_join(
                    sorted(group["current_plot_rule_status"].unique())
                ),
                "current_plot_rule_blockers": pipe_join(
                    sorted(group["current_plot_rule_blockers"].unique())
                ),
                "source_family_keys": pipe_join(sorted(group["source_family_key"].unique())),
                "source_family_labels": pipe_join(sorted(group["source_family_label"].unique())),
                "pair_chase_priorities": pipe_join(sorted(group["pair_chase_priority"].unique())),
                "pair_chase_routes": pipe_join(sorted(group["pair_chase_route"].unique())),
                "side_source_object_routes": pipe_join(sorted(group["side_source_object_route"].unique())),
                "side_source_object_priorities": pipe_join(sorted(group["side_source_object_priority"].unique())),
                "D_min": d_min,
                "D_max": d_max,
                "N_min": n_min,
                "N_max": n_max,
                "side_target_ids_json": json_list(group["source_side_target_id"]),
                "figure1_replication_pair_ids_json": json_list(group["figure1_replication_pair_id"]),
                "pair_chase_task_ids_json": json_list(group["pair_chase_task_id"]),
                "source_object_seed_urls_json": json_list(
                    list(group["target_source_object_seed_url"]) + ([url] if url else [])
                ),
                "side_search_queries_json": json_list(group["side_search_query"]),
                "pair_relation_search_queries_json": json_list(group["pair_relation_search_query"]),
                "needs_manual_identity_review": needs_review,
                "identity_review_reason": reason,
                "next_action": next_action_for(group, method),
                "created_at": created_at,
            }
        )

    study_map = pd.DataFrame(study_rows, columns=STUDY_COLUMNS)
    mapping = merged[MAPPING_COLUMNS].copy()
    return study_map, mapping


def write_schema(path: Path) -> None:
    lines = [
        f"purpose: {json.dumps('Deduped represented individual-study/source registry for current root Figure 1 pairs, including excluded no-repull targets.')}",
        "table: figure1-individual-study-map.tsv",
        f"grain: {json.dumps('One deduped represented individual source/study identity touched by at least one Figure 1 pair side.')}",
        f"dedupe_rule: {json.dumps('DOI first, represented/source URL second, normalized title third, weak side-target fallback only when no useful identifier exists.')}",
        "columns:",
    ]
    for name in STUDY_COLUMNS:
        definition = SCHEMA.get(name, "")
        lines.append(f"- name: {name}")
        lines.append(f"  definition: {json.dumps(definition)}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def counts_table(series: pd.Series) -> list[str]:
    lines = ["| value | rows |", "| --- | ---: |"]
    for value, count in series.fillna("").value_counts(dropna=False).items():
        lines.append(f"| {value or '(blank)'} | {int(count)} |")
    return lines


def write_summary(study_map: pd.DataFrame, mapping: pd.DataFrame, path: Path) -> None:
    doi_count = study_map["represented_doi_canonical"].str.strip().ne("").sum()
    url_count = study_map["represented_url_canonical"].str.strip().ne("").sum()
    review_count = study_map["needs_manual_identity_review"].eq("true").sum()
    multi_pair = pd.to_numeric(study_map["n_distinct_pairs"], errors="coerce").fillna(0).gt(1).sum()
    included_touch = pd.to_numeric(study_map["n_included_pairs"], errors="coerce").fillna(0).gt(0).sum()
    excluded_only = pd.to_numeric(study_map["n_included_pairs"], errors="coerce").fillna(0).eq(0).sum()

    lines = [
        "# Figure 1 Individual Study Map",
        "",
        "This artifact collapses all root Figure 1 pair sides, included and excluded, into represented individual source/study identities for dedupe and source-object chasing.",
        "",
        f"- Individual study/source rows: {len(study_map):,}",
        f"- Side-to-study mapping rows: {len(mapping):,}",
        f"- Study/source rows touching current included Figure 1 pairs: {included_touch:,}",
        f"- Excluded-only study/source rows retained for no-repull dedupe: {excluded_only:,}",
        f"- DOI-backed study/source rows: {doi_count:,}",
        f"- URL-backed study/source rows, including DOI URLs: {url_count:,}",
        f"- Rows touching more than one plotted pair: {multi_pair:,}",
        f"- Rows needing manual identity review: {review_count:,}",
        "",
        "## Dedupe Methods",
        "",
        *counts_table(study_map["study_dedupe_method"]),
        "",
        "## Dedupe Confidence",
        "",
        *counts_table(study_map["dedupe_confidence"]),
        "",
        "## Side Routes",
        "",
        *counts_table(mapping["side_source_object_route"]),
        "",
        "## Top Source Families By Side Target",
        "",
        "| source_family_key | side targets |",
        "| --- | ---: |",
    ]
    for value, count in mapping["source_family_key"].value_counts().head(30).items():
        lines.append(f"| {value} | {int(count)} |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--side-targets", type=Path, default=DEFAULT_SIDE_TARGETS)
    parser.add_argument("--pair-worklist", type=Path, default=DEFAULT_PAIR_WORKLIST)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--batch-size", type=int, default=300)
    parser.add_argument("--created-at", default="2026-05-05T00:00:00")
    parser.add_argument("--replace", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    study_path = args.output_dir / "figure1-individual-study-map.tsv"
    mapping_path = args.output_dir / "figure1-side-to-individual-study-map.tsv"
    batch_path = args.output_dir / "figure1-individual-study-map-batch001.tsv"
    schema_path = args.output_dir / "figure1-individual-study-map-schema.yml"
    summary_path = args.output_dir / "figure1-individual-study-map-summary.md"

    outputs = [study_path, mapping_path, batch_path, schema_path, summary_path]
    if not args.replace:
        existing = [path for path in outputs if path.exists()]
        if existing:
            raise SystemExit(
                "Refusing to overwrite existing outputs without --replace: "
                + ", ".join(str(path) for path in existing)
            )

    side_targets = pd.read_csv(args.side_targets, sep="\t", dtype=str, keep_default_na=False)
    pair_worklist = pd.read_csv(args.pair_worklist, sep="\t", dtype=str, keep_default_na=False)
    study_map, mapping = build_maps(side_targets, pair_worklist, args.created_at)

    method_order = {"doi": 0, "url": 1, "title": 2, "weak_side_target": 3}
    study_map["_method_sort"] = study_map["study_dedupe_method"].map(method_order).fillna(99)
    study_map["_review_sort"] = study_map["needs_manual_identity_review"].map({"false": 0, "true": 1}).fillna(9)
    study_map["_pairs_sort"] = pd.to_numeric(study_map["n_distinct_pairs"], errors="coerce").fillna(0) * -1
    study_map = study_map.sort_values(
        ["_method_sort", "_review_sort", "_pairs_sort", "represented_title_canonical"],
        kind="stable",
    ).drop(columns=["_method_sort", "_review_sort", "_pairs_sort"])

    order = {
        study_id: idx for idx, study_id in enumerate(study_map["figure1_individual_study_id"].tolist())
    }
    mapping["_study_sort"] = mapping["figure1_individual_study_id"].map(order).fillna(10**9)
    mapping["_side_sort"] = mapping["side"].map({"original": 0, "replication": 1}).fillna(9)
    mapping = mapping.sort_values(
        ["_study_sort", "_side_sort", "figure1_replication_pair_id"], kind="stable"
    ).drop(columns=["_study_sort", "_side_sort"])

    study_map.to_csv(study_path, sep="\t", index=False)
    mapping.to_csv(mapping_path, sep="\t", index=False)
    study_map.head(args.batch_size).to_csv(batch_path, sep="\t", index=False)
    write_schema(schema_path)
    write_summary(study_map, mapping, summary_path)

    print(f"Wrote {len(study_map):,} individual study/source rows to {study_path}")
    print(f"Wrote {len(mapping):,} side-to-study mapping rows to {mapping_path}")
    print(f"Wrote schema to {schema_path}")
    print(f"Wrote summary to {summary_path}")


if __name__ == "__main__":
    main()
