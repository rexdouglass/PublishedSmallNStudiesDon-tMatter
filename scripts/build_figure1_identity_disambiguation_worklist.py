#!/usr/bin/env python3
"""Build a Figure 1 worklist for grounding title-only/weak identities."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
PAIR_CHASE_DIR = ROOT / "steps" / "individual_replication_papers" / "figure1" / "pair_chase"
DEFAULT_STUDY_MAP = PAIR_CHASE_DIR / "figure1-individual-study-map.tsv"
DEFAULT_STUDY_BIB = PAIR_CHASE_DIR / "figure1-individual-study-bibtex-map.tsv"
DEFAULT_PAIR_BIB = PAIR_CHASE_DIR / "figure1-pair-bibtex-map.tsv"
DEFAULT_OUTPUT_DIR = PAIR_CHASE_DIR

WORKLIST_COLUMNS = [
    "identity_disambiguation_task_id",
    "figure1_individual_study_id",
    "primary_bibtex_key",
    "all_bibtex_keys",
    "study_dedupe_key",
    "study_dedupe_method",
    "dedupe_confidence",
    "needs_manual_identity_review",
    "identity_review_reason",
    "represented_title_canonical",
    "represented_doi_canonical",
    "represented_url_canonical",
    "roles_observed",
    "n_side_targets",
    "n_distinct_pairs",
    "n_included_pairs",
    "n_excluded_pairs",
    "current_plot_rule_statuses",
    "source_family_keys",
    "pair_chase_priorities",
    "side_source_object_routes",
    "identity_disambiguation_priority",
    "identity_disambiguation_route",
    "identity_disambiguation_blocker",
    "suggested_search_query",
    "source_family_backfill_query",
    "required_resolution_fields",
    "acceptance_criteria",
    "next_action",
    "figure1_replication_pair_ids_json",
    "side_target_ids_json",
    "pair_chase_task_ids_json",
    "pair_bibtex_map_rows_json",
    "created_at",
]


def clean(value: object) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    if text.lower() in {"nan", "none", "null"}:
        return ""
    return text


def stable_id(prefix: str, *parts: object) -> str:
    payload = "||".join(clean(part) for part in parts)
    digest = hashlib.sha1(payload.encode("utf-8")).hexdigest()[:16]
    return f"{prefix}_{digest}"


def as_int(value: object) -> int:
    try:
        return int(float(clean(value)))
    except ValueError:
        return 0


def quote_query(text: str, max_len: int = 220) -> str:
    text = " ".join(clean(text).replace('"', "").split())
    if len(text) > max_len:
        text = text[:max_len].rsplit(" ", 1)[0]
    return f'"{text}"' if text else ""


def compact_query(parts: list[str], max_len: int = 500) -> str:
    text = " ".join(part for part in parts if clean(part))
    text = " ".join(text.split())
    if len(text) <= max_len:
        return text
    return text[:max_len].rsplit(" ", 1)[0]


def json_list(values: list[object]) -> str:
    out = []
    seen = set()
    for value in values:
        text = clean(value)
        if text and text not in seen:
            out.append(text)
            seen.add(text)
    return json.dumps(out, ensure_ascii=True)


def priority_route(row: dict[str, str]) -> tuple[str, str, str, str]:
    method = clean(row.get("study_dedupe_method"))
    included = as_int(row.get("n_included_pairs")) > 0
    families = clean(row.get("source_family_keys"))
    title = clean(row.get("represented_title_canonical"))

    if method == "weak_side_target":
        if included:
            return (
                "D0",
                "source_family_backfill_for_included_weak_identity",
                "weak identity has no usable title/DOI/URL",
                "Use source-family rows and local corpus artifacts to resolve the represented original or replication source to a citeable paper/report/dataset.",
            )
        return (
            "D4",
            "deferred_source_family_backfill_for_excluded_weak_identity",
            "excluded pair and weak identity",
            "Keep as no-repull target; backfill only when a new individual-pair candidate collides or analytic rules change.",
        )

    if method == "title":
        if included:
            return (
                "D1",
                "title_to_real_citation_for_included_identity",
                "title-only identity",
                "Resolve title/citation string to DOI, PMID, PMCID, stable publisher URL, or an authoritative local source object.",
            )
        return (
            "D3",
            "title_to_real_citation_for_excluded_identity",
            "excluded pair and title-only identity",
            "Resolve if cheap or if a new candidate collides; otherwise retain as no-repull dedupe evidence.",
        )

    if method == "url" and not clean(row.get("represented_doi_canonical")):
        if included:
            return (
                "D2",
                "url_to_real_citation_for_included_identity",
                "URL-backed identity lacks DOI/standard citation",
                "Inspect the URL and promote to DOI/PMID/PMCID or stable citation metadata where available.",
            )
        return (
            "D5",
            "deferred_url_to_real_citation_for_excluded_identity",
            "excluded pair and URL-backed non-DOI identity",
            "Retain URL identity; promote only if needed for dedupe collision or later source-object verification.",
        )

    if method == "doi" and "weak_title_label_present" in clean(row.get("identity_review_reason")):
        return (
            "D6",
            "doi_backed_title_metadata_cleanup",
            "DOI-backed identity has weak local display title",
            "Use DOI/Crossref/publisher metadata to replace shorthand local labels with a full citeable title while preserving the original local label as provenance text.",
        )

    return (
        "D9",
        "already_grounded_or_not_in_scope",
        "",
        "No manual identity-disambiguation action needed by this worklist.",
    )


def build_rows(study_map: pd.DataFrame, study_bib: pd.DataFrame, pair_bib: pd.DataFrame, created_at: str) -> pd.DataFrame:
    bib_cols = [
        "figure1_individual_study_id",
        "primary_bibtex_key",
        "all_bibtex_keys",
    ]
    merged = study_map.merge(study_bib[bib_cols], on="figure1_individual_study_id", how="left")
    pair_by_study: dict[str, pd.DataFrame] = {}
    for side in ["original", "replication"]:
        col = f"{side}_individual_study_id"
        if col in pair_bib.columns:
            for study_id, group in pair_bib.groupby(col, dropna=False):
                study_id = clean(study_id)
                if not study_id:
                    continue
                if study_id in pair_by_study:
                    pair_by_study[study_id] = pd.concat([pair_by_study[study_id], group], ignore_index=True)
                else:
                    pair_by_study[study_id] = group.copy()

    rows = []
    for raw in merged.to_dict("records"):
        if clean(raw.get("needs_manual_identity_review")) != "true":
            continue
        priority, route, blocker, next_action = priority_route(raw)
        if priority == "D9":
            continue
        study_id = clean(raw.get("figure1_individual_study_id"))
        pairs = pair_by_study.get(study_id, pd.DataFrame())
        pair_rows_json = "[]"
        if not pairs.empty:
            pair_rows_json = json_list(pairs.get("figure1_replication_pair_id", pd.Series(dtype=str)).tolist())
        title = clean(raw.get("represented_title_canonical"))
        families = clean(raw.get("source_family_keys"))
        query = compact_query([quote_query(title), "DOI OR PMID OR PMCID"])
        backfill_query = compact_query([families, quote_query(title), "replication original paper DOI"])
        if clean(raw.get("study_dedupe_method")) == "weak_side_target":
            backfill_query = compact_query(
                [
                    families,
                    quote_query(title),
                    clean(raw.get("roles_observed")),
                    clean(raw.get("study_dedupe_key")),
                    "original replication paper DOI source family",
                ]
            )
            query = backfill_query
        rows.append(
            {
                "identity_disambiguation_task_id": stable_id(
                    "figure1_identity_disambiguation",
                    study_id,
                    clean(raw.get("study_dedupe_key")),
                    route,
                ),
                "figure1_individual_study_id": study_id,
                "primary_bibtex_key": clean(raw.get("primary_bibtex_key")),
                "all_bibtex_keys": clean(raw.get("all_bibtex_keys")),
                "study_dedupe_key": clean(raw.get("study_dedupe_key")),
                "study_dedupe_method": clean(raw.get("study_dedupe_method")),
                "dedupe_confidence": clean(raw.get("dedupe_confidence")),
                "needs_manual_identity_review": clean(raw.get("needs_manual_identity_review")),
                "identity_review_reason": clean(raw.get("identity_review_reason")),
                "represented_title_canonical": title,
                "represented_doi_canonical": clean(raw.get("represented_doi_canonical")),
                "represented_url_canonical": clean(raw.get("represented_url_canonical")),
                "roles_observed": clean(raw.get("roles_observed")),
                "n_side_targets": clean(raw.get("n_side_targets")),
                "n_distinct_pairs": clean(raw.get("n_distinct_pairs")),
                "n_included_pairs": clean(raw.get("n_included_pairs")),
                "n_excluded_pairs": clean(raw.get("n_excluded_pairs")),
                "current_plot_rule_statuses": clean(raw.get("current_plot_rule_statuses")),
                "source_family_keys": families,
                "pair_chase_priorities": clean(raw.get("pair_chase_priorities")),
                "side_source_object_routes": clean(raw.get("side_source_object_routes")),
                "identity_disambiguation_priority": priority,
                "identity_disambiguation_route": route,
                "identity_disambiguation_blocker": blocker,
                "suggested_search_query": query,
                "source_family_backfill_query": backfill_query,
                "required_resolution_fields": "resolved_title|resolved_authors|resolved_year|resolved_venue|resolved_doi_or_pmid_or_pmcid_or_stable_url|resolution_source_url|verbatim_match_evidence",
                "acceptance_criteria": "Do not edit root pair values. Add or propose a resolved citation only when the title/label maps to a citeable source object with enough evidence to distinguish original vs replication side.",
                "next_action": next_action,
                "figure1_replication_pair_ids_json": clean(raw.get("figure1_replication_pair_ids_json")),
                "side_target_ids_json": clean(raw.get("side_target_ids_json")),
                "pair_chase_task_ids_json": clean(raw.get("pair_chase_task_ids_json")),
                "pair_bibtex_map_rows_json": pair_rows_json,
                "created_at": created_at,
            }
        )
    out = pd.DataFrame(rows, columns=WORKLIST_COLUMNS)
    if out.empty:
        return out
    priority_order = {"D0": 0, "D1": 1, "D2": 2, "D3": 3, "D4": 4, "D5": 5, "D6": 6}
    out["_priority_sort"] = out["identity_disambiguation_priority"].map(priority_order).fillna(99)
    out["_included_sort"] = pd.to_numeric(out["n_included_pairs"], errors="coerce").fillna(0) * -1
    out["_pairs_sort"] = pd.to_numeric(out["n_distinct_pairs"], errors="coerce").fillna(0) * -1
    out = out.sort_values(
        ["_priority_sort", "_included_sort", "_pairs_sort", "represented_title_canonical"],
        kind="mergesort",
    ).drop(columns=["_priority_sort", "_included_sort", "_pairs_sort"])
    return out


def counts_table(series: pd.Series) -> list[str]:
    lines = ["| value | rows |", "| --- | ---: |"]
    for value, count in series.value_counts(dropna=False).items():
        lines.append(f"| {value or '(blank)'} | {int(count)} |")
    return lines


def write_summary(worklist: pd.DataFrame, batch: pd.DataFrame, path: Path) -> None:
    included_tasks = pd.to_numeric(worklist["n_included_pairs"], errors="coerce").fillna(0).gt(0).sum() if not worklist.empty else 0
    lines = [
        "# Figure 1 Identity Disambiguation Worklist",
        "",
        "This artifact routes title-only, URL-only, and weak represented source identities toward real citeable records before individual-pair chasing.",
        "",
        f"- Disambiguation tasks: {len(worklist):,}",
        f"- Tasks touching current included Figure 1 pairs: {int(included_tasks):,}",
        f"- First bounded batch: {len(batch):,}",
        "",
        "## Priority Meaning",
        "",
        "- D0: included weak identity; backfill from source-family artifacts first.",
        "- D1: included title-only identity; resolve title/citation string to DOI/PMID/PMCID/stable source.",
        "- D2: included URL-backed non-DOI identity; inspect URL and promote standard citation metadata if possible.",
        "- D3: excluded title-only identity; retain for dedupe and resolve when cheap or colliding.",
        "- D4: excluded weak identity; deferred backfill/no-repull target.",
        "- D5: excluded URL-backed non-DOI identity; deferred URL citation promotion.",
        "- D6: DOI-backed identity already grounded, but display title needs metadata cleanup.",
        "",
        "## Priority Counts",
        "",
        *counts_table(worklist["identity_disambiguation_priority"] if not worklist.empty else pd.Series(dtype=str)),
        "",
        "## Route Counts",
        "",
        *counts_table(worklist["identity_disambiguation_route"] if not worklist.empty else pd.Series(dtype=str)),
        "",
        "## Dedupe Method Counts",
        "",
        *counts_table(worklist["study_dedupe_method"] if not worklist.empty else pd.Series(dtype=str)),
        "",
        "## Top Source Families",
        "",
    ]
    family_counts = worklist["source_family_keys"].value_counts().head(30) if not worklist.empty else pd.Series(dtype=int)
    lines.extend(["| source_family_keys | rows |", "| --- | ---: |"])
    for family, count in family_counts.items():
        lines.append(f"| {family} | {int(count)} |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--study-map", type=Path, default=DEFAULT_STUDY_MAP)
    parser.add_argument("--study-bib", type=Path, default=DEFAULT_STUDY_BIB)
    parser.add_argument("--pair-bib", type=Path, default=DEFAULT_PAIR_BIB)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--batch-size", type=int, default=200)
    parser.add_argument("--created-at", default="2026-05-05T00:00:00")
    parser.add_argument("--replace", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    worklist_path = args.output_dir / "figure1-identity-disambiguation-worklist.tsv"
    batch_path = args.output_dir / "figure1-identity-disambiguation-batch001.tsv"
    summary_path = args.output_dir / "figure1-identity-disambiguation-summary.md"
    outputs = [worklist_path, batch_path, summary_path]
    if not args.replace:
        existing = [path for path in outputs if path.exists()]
        if existing:
            raise SystemExit("Refusing to overwrite existing outputs without --replace: " + ", ".join(map(str, existing)))

    study_map = pd.read_csv(args.study_map, sep="\t", dtype=str, keep_default_na=False)
    study_bib = pd.read_csv(args.study_bib, sep="\t", dtype=str, keep_default_na=False)
    pair_bib = pd.read_csv(args.pair_bib, sep="\t", dtype=str, keep_default_na=False)
    worklist = build_rows(study_map, study_bib, pair_bib, args.created_at)
    batch = worklist.head(args.batch_size).copy()
    worklist.to_csv(worklist_path, sep="\t", index=False)
    batch.to_csv(batch_path, sep="\t", index=False)
    write_summary(worklist, batch, summary_path)
    print(f"Wrote {len(worklist):,} identity disambiguation tasks to {worklist_path}")
    print(f"Wrote {len(batch):,} batch rows to {batch_path}")
    print(f"Wrote summary to {summary_path}")


if __name__ == "__main__":
    main()
