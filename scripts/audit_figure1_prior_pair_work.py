#!/usr/bin/env python3
"""Compare prior ad hoc Figure 1 pair artifacts with the current scripted maps."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OLD_PAIR_DETAILS = ROOT / "data" / "derived" / "effect_inflation_dataset" / "plot1_replication_pair_details.csv"
ROOT_PAIRS = ROOT / "FIGURE1_REPLICATION_PAIRS.tsv"
SCHEMA_PILOT_DIR = ROOT / "data" / "derived" / "effect_inflation_dataset" / "schema_pilot"
PAIR_CHASE_DIR = ROOT / "steps" / "individual_replication_papers" / "figure1" / "pair_chase"
DEFAULT_OUT_DIR = PAIR_CHASE_DIR


def read_csv(path: Path, sep: str | None = None) -> pd.DataFrame:
    if sep is None:
        sep = "\t" if path.suffix == ".tsv" else ","
    return pd.read_csv(path, sep=sep, dtype=str, keep_default_na=False)


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def table_shape(path: Path, sep: str | None = None) -> tuple[int, int]:
    if not path.exists():
        return 0, 0
    df = read_csv(path, sep=sep)
    return int(len(df)), int(len(df.columns))


def count_series(series: pd.Series, n: int = 20) -> str:
    if series.empty:
        return ""
    return "; ".join(f"{idx}={val}" for idx, val in series.value_counts().head(n).items())


def build_artifact_rows() -> list[dict[str, str]]:
    specs = [
        (
            "old_pair_detail_projection",
            OLD_PAIR_DETAILS,
            "one row per old plotted pair projection",
            "prior work",
            "reuse as historical subset and value/source-family clue; do not treat as full current universe",
        ),
        (
            "current_root_pair_table",
            ROOT_PAIRS,
            "one row per current root D/N pair, included or excluded",
            "current scripted root",
            "canonical staging table for pair-level worklists",
        ),
        (
            "schema_pilot_source_result_sample",
            SCHEMA_PILOT_DIR / "source_result_codebook_sample_300.tsv",
            "300-row source_result-shaped pilot sample",
            "prior schema pilot",
            "reuse as schema precedent for source_result/source_result_support promotion",
        ),
        (
            "schema_pilot_source_sample",
            SCHEMA_PILOT_DIR / "source_codebook_sample_300.tsv",
            "source identity rows supporting the 300-row pilot",
            "prior schema pilot",
            "reuse as source/source mapping precedent",
        ),
        (
            "schema_pilot_source_source_mapping_sample",
            SCHEMA_PILOT_DIR / "source_source_mapping_codebook_sample_300.tsv",
            "relationship mapping rows supporting the 300-row pilot",
            "prior schema pilot",
            "reuse as replication/source relationship precedent",
        ),
        (
            "current_pair_chase_worklist",
            PAIR_CHASE_DIR / "figure1-pair-chase-worklist.tsv",
            "one row per current root pair task",
            "current scripted worklist",
            "use as pair-specific source-object chase and no-repull dedupe queue",
        ),
        (
            "current_pair_side_targets",
            PAIR_CHASE_DIR / "figure1-pair-source-side-targets.tsv",
            "one row per original or replication side target",
            "current scripted worklist",
            "use as side-level acquisition/extraction queue",
        ),
        (
            "current_individual_study_map",
            PAIR_CHASE_DIR / "figure1-individual-study-map.tsv",
            "one row per deduped represented study/source identity",
            "current scripted dedupe map",
            "use as first-pass dedupe registry for new individual replication candidates",
        ),
        (
            "current_side_to_individual_study_map",
            PAIR_CHASE_DIR / "figure1-side-to-individual-study-map.tsv",
            "one row per pair side to deduped represented identity",
            "current scripted dedupe map",
            "preserves pair-side grain after deduping represented sources",
        ),
        (
            "current_individual_study_bibtex_map",
            PAIR_CHASE_DIR / "figure1-individual-study-bibtex-map.tsv",
            "one row per deduped represented identity mapped to corpus BibTeX",
            "current scripted bibliography map",
            "use as BibTeX-key dedupe bridge",
        ),
        (
            "current_side_to_bibtex_map",
            PAIR_CHASE_DIR / "figure1-side-to-bibtex-map.tsv",
            "one row per pair side mapped to corpus BibTeX",
            "current scripted bibliography map",
            "use to test whether a proposed individual pair side is already represented",
        ),
        (
            "current_pair_bibtex_map",
            PAIR_CHASE_DIR / "figure1-pair-bibtex-map.tsv",
            "one row per current root pair with both side identities and BibTeX keys",
            "current scripted bibliography map",
            "use as the primary dedupe gate for new individual replication pairs",
        ),
        (
            "current_identity_disambiguation_worklist",
            PAIR_CHASE_DIR / "figure1-identity-disambiguation-worklist.tsv",
            "one row per title-only, URL-only, or weak identity that needs cite grounding",
            "current scripted disambiguation queue",
            "use as the next-step queue for resolving local labels to DOI/PMID/PMCID/stable citations",
        ),
        (
            "current_identity_disambiguation_batch001",
            PAIR_CHASE_DIR / "figure1-identity-disambiguation-batch001.tsv",
            "first bounded batch of cite-grounding tasks",
            "current scripted disambiguation queue",
            "use for the next manual/Codex/GPT grounding batch",
        ),
    ]
    rows: list[dict[str, str]] = []
    for artifact_id, path, grain, lineage, reuse in specs:
        n_rows, n_cols = table_shape(path)
        rows.append(
            {
                "artifact_id": artifact_id,
                "path": rel(path),
                "exists": str(path.exists()).lower(),
                "rows": str(n_rows),
                "columns": str(n_cols),
                "grain": grain,
                "lineage": lineage,
                "reuse_decision": reuse,
            }
        )
    return rows


def build_metric_rows() -> tuple[list[dict[str, str]], dict[str, object]]:
    old = read_csv(OLD_PAIR_DETAILS) if OLD_PAIR_DETAILS.exists() else pd.DataFrame()
    new = read_csv(ROOT_PAIRS) if ROOT_PAIRS.exists() else pd.DataFrame()

    old_ids = set(old.get("pair_id", pd.Series(dtype=str)))
    new_ids = set(new.get("native_pair_id", pd.Series(dtype=str)))
    common_ids = old_ids & new_ids
    old_only = old_ids - new_ids
    new_only = new_ids - old_ids

    rows: list[dict[str, str]] = []

    def add(metric: str, value: object, notes: str = "") -> None:
        rows.append({"metric": metric, "value": str(value), "notes": notes})

    add("old_pair_detail_rows", len(old), rel(OLD_PAIR_DETAILS))
    add("current_root_pair_rows", len(new), rel(ROOT_PAIRS))
    add("old_pair_ids_present_in_current_native_pair_id", len(common_ids), "intersection of old pair_id and current native_pair_id")
    add("old_pair_ids_missing_from_current", len(old_only), "old pair IDs not found in current native_pair_id")
    add("current_native_pair_ids_not_in_old", len(new_only), "new root pair IDs added after old pair-detail projection")
    if "current_plot_rule_status" in new.columns:
        add("current_plot_rule_status_counts", count_series(new["current_plot_rule_status"]))
    if "source_result_promotion_status" in new.columns:
        add("source_result_promotion_status_counts", count_series(new["source_result_promotion_status"]))
    if "source_family_key" in new.columns:
        add("current_source_family_counts_top20", count_series(new["source_family_key"]))
    if "source_dataset" in old.columns:
        add("old_source_dataset_counts_top20", count_series(old["source_dataset"]))

    new_only_df = new[new.get("native_pair_id", pd.Series(dtype=str)).isin(new_only)].copy() if not new.empty else pd.DataFrame()
    if "source_family_key" in new_only_df.columns:
        add("new_only_source_family_counts_top20", count_series(new_only_df["source_family_key"]))
    if "current_plot_rule_status" in new_only_df.columns:
        add("new_only_current_plot_rule_status_counts", count_series(new_only_df["current_plot_rule_status"]))

    schema_result_path = SCHEMA_PILOT_DIR / "source_result_codebook_sample_300.tsv"
    if schema_result_path.exists():
        schema_result = read_csv(schema_result_path)
        add("schema_pilot_source_result_rows", len(schema_result), rel(schema_result_path))
        if "evidence_level" in schema_result.columns:
            add("schema_pilot_evidence_level_counts", count_series(schema_result["evidence_level"]))
        if "target_acquisition_state" in schema_result.columns:
            add("schema_pilot_target_acquisition_state_counts", count_series(schema_result["target_acquisition_state"]))

    study_bib_path = PAIR_CHASE_DIR / "figure1-individual-study-bibtex-map.tsv"
    side_bib_path = PAIR_CHASE_DIR / "figure1-side-to-bibtex-map.tsv"
    pair_bib_path = PAIR_CHASE_DIR / "figure1-pair-bibtex-map.tsv"
    if study_bib_path.exists():
        study_bib = read_csv(study_bib_path)
        add("current_study_bibtex_map_rows", len(study_bib), rel(study_bib_path))
        if "bibtex_mapping_status" in study_bib.columns:
            add("current_study_bibtex_mapping_status_counts", count_series(study_bib["bibtex_mapping_status"]))
    if side_bib_path.exists():
        side_bib = read_csv(side_bib_path)
        add("current_side_bibtex_map_rows", len(side_bib), rel(side_bib_path))
        if "bibtex_mapping_status" in side_bib.columns:
            add("current_side_bibtex_mapping_status_counts", count_series(side_bib["bibtex_mapping_status"]))
    if pair_bib_path.exists():
        pair_bib = read_csv(pair_bib_path)
        add("current_pair_bibtex_map_rows", len(pair_bib), rel(pair_bib_path))
        if "pair_bibtex_mapping_status" in pair_bib.columns:
            add("current_pair_bibtex_mapping_status_counts", count_series(pair_bib["pair_bibtex_mapping_status"]))
        if "pair_identity_review_status" in pair_bib.columns:
            add("current_pair_identity_review_status_counts", count_series(pair_bib["pair_identity_review_status"]))
    disambig_path = PAIR_CHASE_DIR / "figure1-identity-disambiguation-worklist.tsv"
    if disambig_path.exists():
        disambig = read_csv(disambig_path)
        add("current_identity_disambiguation_tasks", len(disambig), rel(disambig_path))
        if "identity_disambiguation_priority" in disambig.columns:
            add("current_identity_disambiguation_priority_counts", count_series(disambig["identity_disambiguation_priority"]))
        if "identity_disambiguation_route" in disambig.columns:
            add("current_identity_disambiguation_route_counts", count_series(disambig["identity_disambiguation_route"]))

    context = {
        "old": old,
        "new": new,
        "common_ids": common_ids,
        "old_only": old_only,
        "new_only": new_only,
        "new_only_df": new_only_df,
    }
    return rows, context


def md_table_from_counts(series: pd.Series, key_label: str, value_label: str, n: int = 15) -> list[str]:
    lines = [f"| {key_label} | {value_label} |", "| --- | ---: |"]
    for key, value in series.value_counts().head(n).items():
        lines.append(f"| {key} | {value} |")
    return lines


def write_markdown(path: Path, artifact_rows: list[dict[str, str]], metric_rows: list[dict[str, str]], context: dict[str, object]) -> None:
    old = context["old"]
    new = context["new"]
    common_ids = context["common_ids"]
    old_only = context["old_only"]
    new_only = context["new_only"]
    new_only_df = context["new_only_df"]
    assert isinstance(old, pd.DataFrame)
    assert isinstance(new, pd.DataFrame)
    assert isinstance(common_ids, set)
    assert isinstance(old_only, set)
    assert isinstance(new_only, set)
    assert isinstance(new_only_df, pd.DataFrame)

    included = 0
    excluded = 0
    if "current_plot_rule_status" in new.columns:
        included = int((new["current_plot_rule_status"] == "included_by_current_figure1_dn_rule").sum())
        excluded = int((new["current_plot_rule_status"] == "excluded_by_current_figure1_dn_rule").sum())

    lines: list[str] = [
        "# Figure 1 Prior Pair Work Reconciliation",
        "",
        "This audit checks whether the current pair-chase/BibTeX work is duplicating an older Figure 1 pair mapping.",
        "",
        "## Verdict",
        "",
        (
            f"The earlier pair-detail projection has {len(old):,} rows. The current scripted root table has "
            f"{len(new):,} rows: {included:,} included by the current Figure 1 D/N rule and {excluded:,} excluded "
            "but retained as no-repull/dedupe targets."
        ),
        "",
        (
            f"By stable pair ID, {len(common_ids):,} / {len(old):,} old rows are present in the current table, "
            f"with {len(old_only):,} old-only pair IDs and {len(new_only):,} current pair IDs not present in the old projection. "
            "So the old work was real and useful, but it was a smaller plotted-pair projection rather than the full current pair universe."
        ),
        "",
        "The 300-row schema pilot is also real prior work. It should be reused as the source/source_result/schema precedent, not as a complete pair registry.",
        "",
        "## Artifact Inventory",
        "",
        "| artifact | rows | columns | lineage | reuse decision |",
        "| --- | ---: | ---: | --- | --- |",
    ]
    for row in artifact_rows:
        lines.append(
            f"| `{row['artifact_id']}` | {row['rows']} | {row['columns']} | {row['lineage']} | {row['reuse_decision']} |"
        )

    lines += [
        "",
        "## Current Additions Beyond The Old Projection",
        "",
    ]
    if not new_only_df.empty and "source_family_key" in new_only_df.columns:
        lines.extend(md_table_from_counts(new_only_df["source_family_key"], "source_family_key", "new-only rows"))
    else:
        lines.append("No source-family breakdown available.")

    lines += [
        "",
        "## Reuse Decision",
        "",
        "- Use `FIGURE1_REPLICATION_PAIRS.tsv` as the current root pair universe.",
        "- Use `figure1-pair-chase-worklist.tsv` for pair-level chase/no-repull tasks.",
        "- Use `figure1-pair-bibtex-map.tsv` as the pair-level dedupe gate before chasing new individual pairs.",
        "- Use `figure1-individual-study-map.tsv` and `figure1-individual-study-bibtex-map.tsv` as side/source identity support for that pair-level gate.",
        "- Use `figure1-identity-disambiguation-worklist.tsv` to resolve title-only, URL-only, and weak identities to real citations before source-object chasing.",
        "- Reuse the old `plot1_replication_pair_details.csv` as a historical subset and sanity check, not as the current registry.",
        "- Reuse `schema_pilot/*_codebook_sample_300.tsv` as the model for future source/source_result/source_source_mapping promotion.",
        "",
        "## Metric Rows",
        "",
        f"Machine-readable metrics: `{rel(path.with_suffix('.tsv'))}`.",
        "",
    ]

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--replace", action="store_true")
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    artifact_path = args.output_dir / "figure1-prior-pair-work-artifacts.tsv"
    metric_path = args.output_dir / "figure1-prior-pair-work-reconciliation.tsv"
    md_path = args.output_dir / "figure1-prior-pair-work-reconciliation.md"

    for path in [artifact_path, metric_path, md_path]:
        if path.exists() and not args.replace:
            raise SystemExit(f"{path} exists; use --replace")

    artifact_rows = build_artifact_rows()
    metric_rows, context = build_metric_rows()

    pd.DataFrame(artifact_rows).to_csv(artifact_path, sep="\t", index=False)
    pd.DataFrame(metric_rows).to_csv(metric_path, sep="\t", index=False)
    write_markdown(md_path, artifact_rows, metric_rows, context)

    print(f"Wrote {rel(artifact_path)}")
    print(f"Wrote {rel(metric_path)}")
    print(f"Wrote {rel(md_path)}")


if __name__ == "__main__":
    main()
