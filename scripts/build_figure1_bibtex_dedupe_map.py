#!/usr/bin/env python3
"""Map Figure 1 individual study identities to corpus BibTeX keys."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
PAIR_CHASE_DIR = ROOT / "steps" / "individual_replication_papers" / "figure1" / "pair_chase"
DEFAULT_PAIR_WORKLIST = PAIR_CHASE_DIR / "figure1-pair-chase-worklist.tsv"
DEFAULT_STUDY_MAP = PAIR_CHASE_DIR / "figure1-individual-study-map.tsv"
DEFAULT_SIDE_MAP = PAIR_CHASE_DIR / "figure1-side-to-individual-study-map.tsv"
DEFAULT_CORPUS_REFS = ROOT / "data" / "derived" / "bibliography" / "corpus_papers.csv"
DEFAULT_BIBTEX_FILE = ROOT / "data" / "derived" / "bibliography" / "corpus_papers.bib"
DEFAULT_OUTPUT_DIR = PAIR_CHASE_DIR
SOURCE_ROW_PREFIX = "steps/individual_replication_papers/figure1/pair_chase/figure1-individual-study-map.tsv:"

STUDY_BIB_COLUMNS = [
    "figure1_individual_study_id",
    "study_dedupe_key",
    "study_dedupe_method",
    "dedupe_confidence",
    "represented_title_canonical",
    "represented_doi_canonical",
    "represented_url_canonical",
    "n_distinct_pairs",
    "n_included_pairs",
    "n_excluded_pairs",
    "current_plot_rule_statuses",
    "source_family_keys",
    "primary_bibtex_key",
    "all_bibtex_keys",
    "bibtex_file",
    "bibtex_mapping_status",
    "bibtex_entry_title",
    "bibtex_entry_doi",
    "bibtex_entry_url",
    "bibtex_metadata_source",
    "created_at",
]

SIDE_BIB_COLUMNS = [
    "source_side_target_id",
    "figure1_individual_study_id",
    "primary_bibtex_key",
    "all_bibtex_keys",
    "bibtex_file",
    "bibtex_mapping_status",
    "pair_chase_task_id",
    "figure1_replication_pair_id",
    "current_plot_rule_status",
    "included_in_current_figure1",
    "side",
    "represented_title",
    "represented_doi",
    "represented_value_D",
    "represented_value_N",
    "source_family_key",
    "side_source_object_route",
    "side_search_query",
    "pair_relation_search_query",
    "created_at",
]

PAIR_BIB_COLUMNS = [
    "figure1_pair_bibtex_map_id",
    "pair_chase_task_id",
    "figure1_replication_pair_id",
    "dn_pair_check_id",
    "plot_universe_id",
    "native_pair_id",
    "source_family_key",
    "source_family_label",
    "project",
    "source_dataset",
    "current_plot_rule_status",
    "current_plot_rule_blockers",
    "included_in_current_figure1",
    "outcome_label",
    "D_original",
    "N_original",
    "D_replication",
    "N_replication",
    "original_individual_study_id",
    "replication_individual_study_id",
    "original_bibtex_key",
    "replication_bibtex_key",
    "original_all_bibtex_keys",
    "replication_all_bibtex_keys",
    "original_study_dedupe_key",
    "replication_study_dedupe_key",
    "original_study_dedupe_method",
    "replication_study_dedupe_method",
    "original_dedupe_confidence",
    "replication_dedupe_confidence",
    "original_title",
    "replication_title",
    "original_doi",
    "replication_doi",
    "original_side_route",
    "replication_side_route",
    "pair_bibtex_mapping_status",
    "pair_identity_review_status",
    "pair_dedupe_signature",
    "same_bibtex_key_both_sides",
    "pair_chase_priority",
    "pair_chase_route",
    "next_action",
    "created_at",
]


def clean(value: object) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    if text.lower() in {"nan", "none", "null"}:
        return ""
    return text


def source_row_parts(value: object) -> list[str]:
    text = clean(value)
    if not text:
        return []
    return [part.strip() for part in text.split(";") if part.strip()]


def build_reference_lookup(refs: pd.DataFrame) -> dict[str, list[dict[str, str]]]:
    lookup: dict[str, list[dict[str, str]]] = {}
    for row in refs.to_dict("records"):
        for source_row in source_row_parts(row.get("source_rows")):
            if not source_row.startswith(SOURCE_ROW_PREFIX):
                continue
            study_id = source_row.removeprefix(SOURCE_ROW_PREFIX)
            lookup.setdefault(study_id, []).append(
                {
                    "key": clean(row.get("key")),
                    "title": clean(row.get("title")),
                    "doi": clean(row.get("doi")),
                    "url": clean(row.get("url")),
                    "metadata_source": clean(row.get("metadata_source")),
                }
            )
    return lookup


def mapping_fields(study_id: str, lookup: dict[str, list[dict[str, str]]], bibtex_file: Path) -> dict[str, str]:
    matches = lookup.get(study_id, [])
    keys = []
    seen = set()
    for match in matches:
        key = clean(match.get("key"))
        if key and key not in seen:
            keys.append(key)
            seen.add(key)
    if not keys:
        return {
            "primary_bibtex_key": "",
            "all_bibtex_keys": "",
            "bibtex_file": str(bibtex_file.relative_to(ROOT)),
            "bibtex_mapping_status": "not_mapped_to_corpus_bibliography",
            "bibtex_entry_title": "",
            "bibtex_entry_doi": "",
            "bibtex_entry_url": "",
            "bibtex_metadata_source": "",
        }
    primary = matches[0]
    return {
        "primary_bibtex_key": keys[0],
        "all_bibtex_keys": "|".join(keys),
        "bibtex_file": str(bibtex_file.relative_to(ROOT)),
        "bibtex_mapping_status": "mapped_to_corpus_bibliography",
        "bibtex_entry_title": clean(primary.get("title")),
        "bibtex_entry_doi": clean(primary.get("doi")),
        "bibtex_entry_url": clean(primary.get("url")),
        "bibtex_metadata_source": clean(primary.get("metadata_source")),
    }


def stable_id(prefix: str, *parts: object) -> str:
    payload = "||".join(clean(part) for part in parts)
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]
    return f"{prefix}_{digest}"


def weakest_confidence(values: list[str]) -> str:
    order = {"high": 0, "medium": 1, "low": 2, "very_low": 3, "": 4}
    labels = [clean(value) for value in values]
    if not labels:
        return "needs_manual_identity_review"
    worst = max(labels, key=lambda value: order.get(value, 4))
    if worst in {"low", "very_low", ""}:
        return "needs_manual_identity_review"
    return "identity_mapped"


def build_pair_bib(pair_worklist: pd.DataFrame, side_map: pd.DataFrame, study_bib: pd.DataFrame, created_at: str) -> pd.DataFrame:
    study_lookup = study_bib.set_index("figure1_individual_study_id").to_dict("index")
    side_records_by_pair: dict[str, dict[str, dict[str, str]]] = {}
    for row in side_map.to_dict("records"):
        pair_id = clean(row.get("pair_chase_task_id"))
        side = clean(row.get("side"))
        if side not in {"original", "replication"}:
            continue
        study_id = clean(row.get("figure1_individual_study_id"))
        bib = study_lookup.get(study_id, {})
        enriched = dict(row)
        enriched.update(
            {
                "primary_bibtex_key": clean(bib.get("primary_bibtex_key")),
                "all_bibtex_keys": clean(bib.get("all_bibtex_keys")),
                "bibtex_mapping_status": clean(bib.get("bibtex_mapping_status")),
            }
        )
        side_records_by_pair.setdefault(pair_id, {})[side] = enriched

    pair_rows = []
    for row in pair_worklist.to_dict("records"):
        pair_id = clean(row.get("pair_chase_task_id"))
        sides = side_records_by_pair.get(pair_id, {})
        original = sides.get("original", {})
        replication = sides.get("replication", {})
        original_key = clean(original.get("primary_bibtex_key"))
        replication_key = clean(replication.get("primary_bibtex_key"))
        original_study = clean(original.get("figure1_individual_study_id"))
        replication_study = clean(replication.get("figure1_individual_study_id"))
        if not original_key or not replication_key:
            mapping_status = "missing_original_or_replication_bibtex"
        elif original_key == replication_key:
            mapping_status = "mapped_to_shared_bibtex_key_needs_side_split"
        else:
            mapping_status = "mapped_to_distinct_original_and_replication_bibtex"
        identity_review = weakest_confidence(
            [clean(original.get("dedupe_confidence")), clean(replication.get("dedupe_confidence"))]
        )
        if not original_study or not replication_study:
            identity_review = "missing_original_or_replication_side"
        elif original_key and original_key == replication_key:
            identity_review = "needs_side_split_identity_review"
        signature_parts = [
            original_key or original_study or clean(row.get("original_doi")) or clean(row.get("original_title")),
            replication_key
            or replication_study
            or clean(row.get("replication_doi"))
            or clean(row.get("replication_title")),
            clean(row.get("outcome_label")),
        ]
        pair_dedupe_signature = "||".join(signature_parts)
        pair_rows.append(
            {
                "figure1_pair_bibtex_map_id": stable_id("figure1_pair_bibtex_map", pair_id, pair_dedupe_signature),
                "pair_chase_task_id": pair_id,
                "figure1_replication_pair_id": clean(row.get("figure1_replication_pair_id")),
                "dn_pair_check_id": clean(row.get("dn_pair_check_id")),
                "plot_universe_id": clean(row.get("plot_universe_id")),
                "native_pair_id": clean(row.get("native_pair_id")),
                "source_family_key": clean(row.get("source_family_key")),
                "source_family_label": clean(row.get("source_family_label")),
                "project": clean(row.get("project")),
                "source_dataset": clean(row.get("source_dataset")),
                "current_plot_rule_status": clean(row.get("current_plot_rule_status")),
                "current_plot_rule_blockers": clean(row.get("current_plot_rule_blockers")),
                "included_in_current_figure1": clean(row.get("included_in_current_figure1")),
                "outcome_label": clean(row.get("outcome_label")),
                "D_original": clean(row.get("D_original")),
                "N_original": clean(row.get("N_original")),
                "D_replication": clean(row.get("D_replication")),
                "N_replication": clean(row.get("N_replication")),
                "original_individual_study_id": original_study,
                "replication_individual_study_id": replication_study,
                "original_bibtex_key": original_key,
                "replication_bibtex_key": replication_key,
                "original_all_bibtex_keys": clean(original.get("all_bibtex_keys")),
                "replication_all_bibtex_keys": clean(replication.get("all_bibtex_keys")),
                "original_study_dedupe_key": clean(original.get("study_dedupe_key")),
                "replication_study_dedupe_key": clean(replication.get("study_dedupe_key")),
                "original_study_dedupe_method": clean(original.get("study_dedupe_method")),
                "replication_study_dedupe_method": clean(replication.get("study_dedupe_method")),
                "original_dedupe_confidence": clean(original.get("dedupe_confidence")),
                "replication_dedupe_confidence": clean(replication.get("dedupe_confidence")),
                "original_title": clean(original.get("represented_title")) or clean(row.get("original_title")),
                "replication_title": clean(replication.get("represented_title")) or clean(row.get("replication_title")),
                "original_doi": clean(original.get("represented_doi")) or clean(row.get("original_doi")),
                "replication_doi": clean(replication.get("represented_doi")) or clean(row.get("replication_doi")),
                "original_side_route": clean(original.get("side_source_object_route")),
                "replication_side_route": clean(replication.get("side_source_object_route")),
                "pair_bibtex_mapping_status": mapping_status,
                "pair_identity_review_status": identity_review,
                "pair_dedupe_signature": pair_dedupe_signature,
                "same_bibtex_key_both_sides": str(bool(original_key and original_key == replication_key)).lower(),
                "pair_chase_priority": clean(row.get("pair_chase_priority")),
                "pair_chase_route": clean(row.get("pair_chase_route")),
                "next_action": clean(row.get("next_action")),
                "created_at": created_at,
            }
        )
    return pd.DataFrame(pair_rows, columns=PAIR_BIB_COLUMNS)


def write_summary(study_bib: pd.DataFrame, side_bib: pd.DataFrame, pair_bib: pd.DataFrame, path: Path) -> None:
    study_mapped = study_bib["bibtex_mapping_status"].eq("mapped_to_corpus_bibliography").sum()
    side_mapped = side_bib["bibtex_mapping_status"].eq("mapped_to_corpus_bibliography").sum()
    pair_mapped = pair_bib["pair_bibtex_mapping_status"].eq(
        "mapped_to_distinct_original_and_replication_bibtex"
    ).sum()
    included_sides = side_bib["included_in_current_figure1"].eq("true").sum()
    included_sides_mapped = (
        side_bib["included_in_current_figure1"].eq("true")
        & side_bib["bibtex_mapping_status"].eq("mapped_to_corpus_bibliography")
    ).sum()
    included_pairs = pair_bib["included_in_current_figure1"].eq("true").sum()
    included_pairs_mapped = (
        pair_bib["included_in_current_figure1"].eq("true")
        & pair_bib["pair_bibtex_mapping_status"].eq("mapped_to_distinct_original_and_replication_bibtex")
    ).sum()
    lines = [
        "# Figure 1 BibTeX Dedupe Map",
        "",
        "This crosswalk maps every represented Figure 1 study/source identity and every original-replication pair to the corpus BibTeX key generated by `make bibliography`.",
        "",
        f"- Study/source rows: {len(study_bib):,}",
        f"- Study/source rows mapped to BibTeX: {int(study_mapped):,}",
        f"- Study/source rows not mapped to BibTeX: {len(study_bib) - int(study_mapped):,}",
        f"- Side-target rows: {len(side_bib):,}",
        f"- Side-target rows mapped to BibTeX: {int(side_mapped):,}",
        f"- Included side-target rows mapped to BibTeX: {int(included_sides_mapped):,} / {int(included_sides):,}",
        f"- Pair rows: {len(pair_bib):,}",
        f"- Pair rows with distinct original/replication BibTeX keys: {int(pair_mapped):,}",
        f"- Included pair rows with distinct original/replication BibTeX keys: {int(included_pairs_mapped):,} / {int(included_pairs):,}",
        "",
        "## Study Mapping Status",
        "",
        "| status | rows |",
        "| --- | ---: |",
    ]
    for status, count in study_bib["bibtex_mapping_status"].value_counts().items():
        lines.append(f"| {status} | {int(count)} |")
    lines.extend(["", "## Side Mapping Status", "", "| status | rows |", "| --- | ---: |"])
    for status, count in side_bib["bibtex_mapping_status"].value_counts().items():
        lines.append(f"| {status} | {int(count)} |")
    lines.extend(["", "## Pair Mapping Status", "", "| status | rows |", "| --- | ---: |"])
    for status, count in pair_bib["pair_bibtex_mapping_status"].value_counts().items():
        lines.append(f"| {status} | {int(count)} |")
    lines.extend(["", "## Pair Identity Review Status", "", "| status | rows |", "| --- | ---: |"])
    for status, count in pair_bib["pair_identity_review_status"].value_counts().items():
        lines.append(f"| {status} | {int(count)} |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pair-worklist", type=Path, default=DEFAULT_PAIR_WORKLIST)
    parser.add_argument("--study-map", type=Path, default=DEFAULT_STUDY_MAP)
    parser.add_argument("--side-map", type=Path, default=DEFAULT_SIDE_MAP)
    parser.add_argument("--corpus-refs", type=Path, default=DEFAULT_CORPUS_REFS)
    parser.add_argument("--bibtex-file", type=Path, default=DEFAULT_BIBTEX_FILE)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--created-at", default="2026-05-05T00:00:00")
    parser.add_argument("--replace", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    study_out = args.output_dir / "figure1-individual-study-bibtex-map.tsv"
    side_out = args.output_dir / "figure1-side-to-bibtex-map.tsv"
    pair_out = args.output_dir / "figure1-pair-bibtex-map.tsv"
    summary_out = args.output_dir / "figure1-bibtex-dedupe-map-summary.md"
    outputs = [study_out, side_out, pair_out, summary_out]
    if not args.replace:
        existing = [path for path in outputs if path.exists()]
        if existing:
            raise SystemExit(
                "Refusing to overwrite existing outputs without --replace: "
                + ", ".join(str(path) for path in existing)
            )

    pair_worklist = pd.read_csv(args.pair_worklist, sep="\t", dtype=str, keep_default_na=False)
    study_map = pd.read_csv(args.study_map, sep="\t", dtype=str, keep_default_na=False)
    side_map = pd.read_csv(args.side_map, sep="\t", dtype=str, keep_default_na=False)
    refs = pd.read_csv(args.corpus_refs, dtype=str, keep_default_na=False)
    lookup = build_reference_lookup(refs)

    study_rows = []
    for row in study_map.to_dict("records"):
        fields = mapping_fields(clean(row.get("figure1_individual_study_id")), lookup, args.bibtex_file)
        out = {col: clean(row.get(col)) for col in STUDY_BIB_COLUMNS if col in row}
        out.update(fields)
        out["created_at"] = args.created_at
        study_rows.append(out)
    study_bib = pd.DataFrame(study_rows, columns=STUDY_BIB_COLUMNS)

    side_bib = side_map.merge(
        study_bib[
            [
                "figure1_individual_study_id",
                "primary_bibtex_key",
                "all_bibtex_keys",
                "bibtex_file",
                "bibtex_mapping_status",
            ]
        ],
        on="figure1_individual_study_id",
        how="left",
    )
    for col in SIDE_BIB_COLUMNS:
        if col not in side_bib.columns:
            side_bib[col] = ""
    side_bib["created_at"] = args.created_at
    side_bib = side_bib[SIDE_BIB_COLUMNS]

    pair_bib = build_pair_bib(pair_worklist, side_map, study_bib, args.created_at)

    study_bib.to_csv(study_out, sep="\t", index=False)
    side_bib.to_csv(side_out, sep="\t", index=False)
    pair_bib.to_csv(pair_out, sep="\t", index=False)
    write_summary(study_bib, side_bib, pair_bib, summary_out)
    print(f"Wrote {len(study_bib):,} study BibTeX mappings to {study_out}")
    print(f"Wrote {len(side_bib):,} side BibTeX mappings to {side_out}")
    print(f"Wrote {len(pair_bib):,} pair BibTeX mappings to {pair_out}")
    print(f"Wrote summary to {summary_out}")


if __name__ == "__main__":
    main()
