#!/usr/bin/env python3
"""Build pair-specific source-object chase worklists for Figure 1 rows.

This is intentionally a worklist/provenance-routing artifact, not a root-table
promotion step. It takes the currently included Figure 1 D/N pairs and creates:

* one row per plotted pair, prioritized for source-object/value chasing
* one row per pair side (original and replication/follow-up), for DOI/title
  acquisition and value-text extraction
* a small first batch for bounded manual/Codex work
* a Markdown summary with counts by route and source family
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Iterable

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "FIGURE1_REPLICATION_PAIRS.tsv"
DEFAULT_OUTPUT_DIR = ROOT / "steps" / "individual_replication_papers" / "figure1" / "pair_chase"
INCLUDED_STATUS = "included_by_current_figure1_dn_rule"
EXCLUDED_STATUS = "excluded_by_current_figure1_dn_rule"

PAIR_COLUMNS = [
    "pair_chase_task_id",
    "figure1_replication_pair_id",
    "dn_pair_check_id",
    "plot_universe_id",
    "source_family_key",
    "source_family_label",
    "project",
    "source_dataset",
    "native_pair_id",
    "pair_result_status",
    "current_plot_rule_status",
    "current_plot_rule_blockers",
    "included_in_current_figure1",
    "original_title",
    "replication_title",
    "original_doi",
    "replication_doi",
    "outcome_label",
    "D_original",
    "N_original",
    "D_replication",
    "N_replication",
    "D_larger_N_minus_smaller_N",
    "d_ratio",
    "n_ratio",
    "source_result_promotion_status",
    "value_verification_state",
    "target_acquisition_state",
    "source_artifact_local_path",
    "source_artifact_sha256",
    "source_artifact_access_status",
    "strict_original_result_check_id",
    "strict_replication_result_check_id",
    "pair_chase_priority",
    "pair_chase_route",
    "pair_chase_blocker",
    "next_action",
    "source_object_seed_urls_json",
    "local_corpus_artifact_paths_json",
    "search_query_original",
    "search_query_replication",
    "search_query_pair",
    "created_at",
]

SIDE_COLUMNS = [
    "source_side_target_id",
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
    "created_at",
]


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
    return text.strip().rstrip(".")


def doi_url(value: object) -> str:
    doi = normalize_doi(value)
    return f"https://doi.org/{doi}" if doi else ""


def is_url(value: object) -> bool:
    text = clean(value).lower()
    return text.startswith("http://") or text.startswith("https://")


def quote_query(text: str, max_len: int = 180) -> str:
    text = " ".join(clean(text).replace('"', "").split())
    if not text:
        return ""
    if len(text) > max_len:
        text = text[:max_len].rsplit(" ", 1)[0]
    return f'"{text}"'


def compact_query(parts: Iterable[str], max_len: int = 450) -> str:
    text = " ".join(part for part in parts if clean(part))
    text = " ".join(text.split())
    if len(text) <= max_len:
        return text
    return text[:max_len].rsplit(" ", 1)[0]


def has_informative_title(value: object) -> bool:
    text = clean(value)
    if len(text) < 8:
        return False
    weak = {
        "unknown",
        "not reported",
        "missing",
        "na",
        "n/a",
        "original",
        "replication",
    }
    return text.lower() not in weak


def pair_priority_and_route(row: pd.Series) -> tuple[str, str, str, str]:
    promotion = clean(row.get("source_result_promotion_status"))
    value_state = clean(row.get("value_verification_state"))
    plot_status = clean(row.get("current_plot_rule_status"))
    orig_doi = normalize_doi(row.get("original_doi"))
    rep_doi = normalize_doi(row.get("replication_doi"))
    orig_title = has_informative_title(row.get("original_title"))
    rep_title = has_informative_title(row.get("replication_title"))

    if plot_status == EXCLUDED_STATUS:
        # Still chase identity for dedupe, but source-object/value extraction can
        # wait behind currently plotted rows unless it is already ready.
        if (
            promotion != "ready_for_source_result_side_promotion"
            and value_state != "value-bearing source text found"
        ):
            if orig_doi or rep_doi:
                return (
                    "P6",
                    "excluded_pair_identity_map_and_deferred_source_chase",
                    clean(row.get("current_plot_rule_blockers")),
                    "Map represented source identities for dedupe; defer value extraction unless this excluded pair becomes analytically needed.",
                )
            return (
                "P7",
                "excluded_pair_title_or_family_identity_backfill",
                clean(row.get("current_plot_rule_blockers")) or "excluded and weak identifiers",
                "Keep in the no-repull dedupe registry; backfill identity only if a new candidate collides with this label.",
            )

    if (
        promotion == "ready_for_source_result_side_promotion"
        or value_state == "value-bearing source text found"
    ):
        return (
            "P0",
            "promote_existing_value_text_to_source_result",
            "",
            "Promote existing value-bearing side rows into source_result/source_result_support before any new source chase.",
        )

    if (
        promotion == "needs_pair_alignment_to_strict_side_rows"
        or value_state == "source object obtained but not parsed"
    ):
        return (
            "P1",
            "align_existing_side_rows_and_parse_mirrored_object",
            "",
            "Align existing strict side rows, then extract verbatim D/N support from the mirrored object.",
        )

    if orig_doi and rep_doi:
        return (
            "P2",
            "acquire_original_and_replication_source_objects_by_doi",
            "",
            "Acquire/mirror both target source objects by DOI, then extract verbatim D/N support.",
        )

    if orig_doi or rep_doi:
        missing = "replication DOI" if orig_doi and not rep_doi else "original DOI"
        return (
            "P3",
            "acquire_known_doi_side_then_title_search_missing_side",
            missing,
            "Mirror the DOI-bearing side and title-search the missing side before value extraction.",
        )

    if orig_title and rep_title:
        return (
            "P4",
            "title_pair_search_then_acquire_source_objects",
            "no DOI in Figure 1 pair table",
            "Search the original/replication title pair, mirror source objects, then extract verbatim D/N support.",
        )

    return (
        "P5",
        "source_family_backfill_before_individual_chase",
        "weak bibliographic identifiers",
        "Backfill source-family identifiers before attempting individual paper source-object acquisition.",
    )


def source_seed_urls(row: pd.Series) -> list[str]:
    urls = []
    for col in ("original_doi", "replication_doi"):
        url = doi_url(row.get(col))
        if url:
            urls.append(url)
    for col in ("original_title", "replication_title"):
        title = clean(row.get(col))
        if is_url(title):
            urls.append(title)
    return urls


def local_artifacts(row: pd.Series) -> list[str]:
    text = clean(row.get("source_artifact_local_path"))
    if not text:
        return []
    # Some rows contain semicolon-joined local file lists.
    return [part.strip() for part in text.split(";") if part.strip()]


def build_queries(row: pd.Series) -> tuple[str, str, str]:
    orig_doi = normalize_doi(row.get("original_doi"))
    rep_doi = normalize_doi(row.get("replication_doi"))
    orig_title = clean(row.get("original_title"))
    rep_title = clean(row.get("replication_title"))
    orig_title_q = orig_title if is_url(orig_title) else quote_query(orig_title)
    rep_title_q = rep_title if is_url(rep_title) else quote_query(rep_title)

    if orig_doi:
        original_query = orig_doi
    else:
        original_query = compact_query([orig_title_q, "effect size sample size"])

    if rep_doi:
        replication_query = rep_doi
    else:
        replication_query = compact_query([rep_title_q, "replication effect size sample size"])

    if orig_doi and rep_doi:
        pair_query = compact_query([orig_doi, rep_doi, "replication"])
    elif orig_doi or rep_doi:
        pair_query = compact_query(
            [
                orig_doi or orig_title_q,
                rep_doi or rep_title_q,
                "replication original effect sample size",
            ]
        )
    else:
        pair_query = compact_query(
            [
                orig_title_q,
                rep_title_q,
                "replication original effect sample size",
            ]
        )
    return original_query, replication_query, pair_query


def side_route(doi: str, title: str, pair_priority: str) -> tuple[str, str, str, str]:
    if pair_priority == "P0":
        return (
            "S0",
            "existing_value_text_promotion",
            doi_url(doi) or (title if is_url(title) else ""),
            "Promote already-found value support; still mirror represented source object if absent.",
        )
    if normalize_doi(doi):
        return (
            "S1",
            "doi_source_object_acquisition",
            doi_url(doi),
            "Resolve DOI to value-bearing source object, mirror bytes, and extract verbatim D/N text.",
        )
    if is_url(title):
        return (
            "S1",
            "url_source_object_acquisition",
            title,
            "Mirror the represented source URL and extract verbatim D/N text if it is value-bearing.",
        )
    if has_informative_title(title):
        return (
            "S2",
            "title_source_object_search",
            "",
            "Search by represented title, mirror value-bearing source object, and extract verbatim D/N text.",
        )
    return (
        "S3",
        "source_family_identifier_backfill",
        "",
        "Backfill bibliographic identity from source family/corpus before source-object acquisition.",
    )


REPLICATION_SIDE_SOURCE_OVERRIDES = {
    "many_labs_1": {
        "title": "Investigating variation in replicability: A Many Labs replication project",
        "doi": "10.1027/1864-9335/a000178",
    },
    "many_labs_3": {
        "title": "Many Labs 3: Evaluating participant pool quality across the academic semester via replication",
        "doi": "10.1016/j.jesp.2015.10.012",
    },
    "loopr": {
        "title": "How Replicable Are Links Between Personality Traits and Consequential Life Outcomes? The Life Outcomes of Personality Replication Project",
        "doi": "10.1177/0956797619831612",
    },
    "rpcb": {
        "title": "Investigating the replicability of preclinical cancer biology",
        "doi": "10.7554/eLife.71601",
    },
}


def represented_side_identity(row: pd.Series, side: str) -> tuple[str, str]:
    title = clean(row.get(f"{side}_title"))
    doi = normalize_doi(row.get(f"{side}_doi"))
    if side != "replication":
        return title, doi

    source_family = clean(row.get("source_family_key"))
    override = REPLICATION_SIDE_SOURCE_OVERRIDES.get(source_family)
    if not override:
        return title, doi

    # Several project-level corpora carry the focal original-effect title on
    # both sides of the root D/N row. The replication-side source object is the
    # project-level paper/table, not a second copy of the original paper.
    return clean(override.get("title")) or title, normalize_doi(override.get("doi")) or doi


def build_pair_rows(df: pd.DataFrame, created_at: str) -> pd.DataFrame:
    rows = []
    for _, row in df.iterrows():
        task_id = stable_id(
            "figure1_pair_chase",
            [
                row.get("figure1_replication_pair_id"),
                row.get("dn_pair_check_id"),
                row.get("native_pair_id"),
            ],
        )
        priority, route, blocker, next_action = pair_priority_and_route(row)
        q_orig, q_rep, q_pair = build_queries(row)
        out = {col: clean(row.get(col)) for col in PAIR_COLUMNS if col in row.index}
        out.update(
            {
                "pair_chase_task_id": task_id,
                "included_in_current_figure1": (
                    "true"
                    if clean(row.get("current_plot_rule_status")) == INCLUDED_STATUS
                    else "false"
                ),
                "pair_chase_priority": priority,
                "pair_chase_route": route,
                "pair_chase_blocker": blocker,
                "next_action": next_action,
                "source_object_seed_urls_json": json.dumps(source_seed_urls(row), ensure_ascii=True),
                "local_corpus_artifact_paths_json": json.dumps(local_artifacts(row), ensure_ascii=True),
                "search_query_original": q_orig,
                "search_query_replication": q_rep,
                "search_query_pair": q_pair,
                "created_at": created_at,
            }
        )
        rows.append(out)
    return pd.DataFrame(rows, columns=PAIR_COLUMNS)


def build_side_rows(pair_rows: pd.DataFrame, created_at: str) -> pd.DataFrame:
    rows = []
    for _, row in pair_rows.iterrows():
        for side in ("original", "replication"):
            d_col = "D_original" if side == "original" else "D_replication"
            n_col = "N_original" if side == "original" else "N_replication"
            check_col = (
                "strict_original_result_check_id"
                if side == "original"
                else "strict_replication_result_check_id"
            )
            title, doi = represented_side_identity(row, side)
            side_priority, route, seed_url, needed = side_route(
                doi, title, clean(row.get("pair_chase_priority"))
            )
            if doi:
                side_query = doi
            elif is_url(title):
                side_query = title
            else:
                side_query = compact_query([quote_query(title), "effect size sample size"])
            rows.append(
                {
                    "source_side_target_id": stable_id(
                        "figure1_source_side",
                        [
                            row.get("pair_chase_task_id"),
                            side,
                            title,
                            doi,
                        ],
                    ),
                    "pair_chase_task_id": clean(row.get("pair_chase_task_id")),
                    "figure1_replication_pair_id": clean(row.get("figure1_replication_pair_id")),
                    "side": side,
                    "represented_title": title,
                    "represented_doi": doi,
                    "represented_value_D": clean(row.get(d_col)),
                    "represented_value_N": clean(row.get(n_col)),
                    "strict_result_check_id": clean(row.get(check_col)),
                    "source_family_key": clean(row.get("source_family_key")),
                    "source_family_label": clean(row.get("source_family_label")),
                    "current_plot_rule_status": clean(row.get("current_plot_rule_status")),
                    "current_plot_rule_blockers": clean(row.get("current_plot_rule_blockers")),
                    "included_in_current_figure1": clean(row.get("included_in_current_figure1")),
                    "side_source_object_route": route,
                    "side_source_object_priority": side_priority,
                    "target_source_object_seed_url": seed_url,
                    "side_search_query": side_query,
                    "pair_relation_search_query": clean(row.get("search_query_pair")),
                    "needed_verbatim_fields": needed,
                    "created_at": created_at,
                }
            )
    return pd.DataFrame(rows, columns=SIDE_COLUMNS)


def counts_md(title: str, series: pd.Series) -> str:
    lines = [f"### {title}", "", "| value | rows |", "| --- | ---: |"]
    for value, count in series.fillna("").value_counts(dropna=False).items():
        lines.append(f"| {value or '(blank)'} | {int(count)} |")
    return "\n".join(lines)


def write_summary(pair_rows: pd.DataFrame, side_rows: pd.DataFrame, path: Path, batch_n: int) -> None:
    priority_counts = pair_rows["pair_chase_priority"].value_counts().sort_index()
    route_counts = pair_rows["pair_chase_route"].value_counts()
    family_counts = pair_rows["source_family_key"].value_counts().head(30)
    side_route_counts = side_rows["side_source_object_route"].value_counts()
    status_counts = pair_rows["current_plot_rule_status"].value_counts()
    included_n = int(pair_rows["included_in_current_figure1"].eq("true").sum())
    doi_original = pair_rows["original_doi"].str.strip().ne("").sum()
    doi_replication = pair_rows["replication_doi"].str.strip().ne("").sum()
    both_doi = (
        pair_rows["original_doi"].str.strip().ne("")
        & pair_rows["replication_doi"].str.strip().ne("")
    ).sum()
    neither_doi = (
        pair_rows["original_doi"].str.strip().eq("")
        & pair_rows["replication_doi"].str.strip().eq("")
    ).sum()

    lines = [
        "# Figure 1 Pair-Chase Worklist",
        "",
        "This artifact enumerates every root Figure 1 D/N pair row as an individual source-object chase or no-repull dedupe task. It does not promote or edit root rows.",
        "",
        f"- Pair rows: {len(pair_rows):,}",
        f"- Included in current Figure 1 rule: {included_n:,}",
        f"- Excluded by current Figure 1 rule but retained for dedupe: {len(pair_rows) - included_n:,}",
        f"- Side target rows: {len(side_rows):,}",
        f"- Original DOI present: {doi_original:,}",
        f"- Replication/follow-up DOI present: {doi_replication:,}",
        f"- Both-side DOI present: {both_doi:,}",
        f"- Neither-side DOI present: {neither_doi:,}",
        f"- First bounded batch size: {batch_n:,} pair tasks",
        "",
        "## Priority Meaning",
        "",
        "- P0: existing value-bearing text can be promoted to `source_result`/`source_result_support` before new searching.",
        "- P1: existing strict side rows or mirrored objects need alignment/parsing.",
        "- P2: both original and replication/follow-up DOIs are available for source-object acquisition.",
        "- P3: one side has a DOI; title-search the missing side.",
        "- P4: no DOI in the Figure 1 table; search by title pair.",
        "- P5: weak bibliographic identity; backfill from the source family before individual source-object acquisition.",
        "- P6: excluded pair with at least one DOI; keep identity mapped and defer value/source chase.",
        "- P7: excluded pair with weak or title-only identity; keep as no-repull dedupe/background target.",
        "",
        counts_md("Current Plot Rule Status Counts", pair_rows["current_plot_rule_status"]),
        "",
        counts_md("Pair Priority Counts", pair_rows["pair_chase_priority"]),
        "",
        counts_md("Pair Route Counts", pair_rows["pair_chase_route"]),
        "",
        counts_md("Side Source-Object Route Counts", side_rows["side_source_object_route"]),
        "",
        "### Top Source Families",
        "",
        "| source_family_key | pair rows |",
        "| --- | ---: |",
    ]
    for value, count in family_counts.items():
        lines.append(f"| {value} | {int(count)} |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--batch-size", type=int, default=150)
    parser.add_argument(
        "--scope",
        choices=["all", "included"],
        default="all",
        help="Rows to enumerate from FIGURE1_REPLICATION_PAIRS.tsv. Default keeps excluded rows for no-repull dedupe.",
    )
    parser.add_argument("--created-at", default="2026-05-05T00:00:00")
    parser.add_argument("--replace", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    input_path = args.input
    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    pairs_path = output_dir / "figure1-pair-chase-worklist.tsv"
    sides_path = output_dir / "figure1-pair-source-side-targets.tsv"
    batch_path = output_dir / "figure1-pair-chase-batch001.tsv"
    batch_sides_path = output_dir / "figure1-pair-source-side-targets-batch001.tsv"
    summary_path = output_dir / "figure1-pair-chase-summary.md"

    outputs = [pairs_path, sides_path, batch_path, batch_sides_path, summary_path]
    if not args.replace:
        existing = [path for path in outputs if path.exists()]
        if existing:
            raise SystemExit(
                "Refusing to overwrite existing outputs without --replace: "
                + ", ".join(str(path) for path in existing)
            )

    df = pd.read_csv(input_path, sep="\t", dtype=str, keep_default_na=False)
    if args.scope == "included":
        df = df[df["current_plot_rule_status"].eq(INCLUDED_STATUS)].copy()
    pair_rows = build_pair_rows(df, args.created_at)
    side_rows = build_side_rows(pair_rows, args.created_at)

    priority_order = {f"P{i}": i for i in range(10)}
    pair_rows["_priority_sort"] = pair_rows["pair_chase_priority"].map(priority_order).fillna(99)
    pair_rows = pair_rows.sort_values(
        ["_priority_sort", "source_family_key", "figure1_replication_pair_id"],
        kind="stable",
    ).drop(columns=["_priority_sort"])

    pair_order = {
        task_id: idx for idx, task_id in enumerate(pair_rows["pair_chase_task_id"].tolist())
    }
    side_rows["_pair_sort"] = side_rows["pair_chase_task_id"].map(pair_order).fillna(10**9)
    side_rows["_side_sort"] = side_rows["side"].map({"original": 0, "replication": 1}).fillna(9)
    side_rows = side_rows.sort_values(["_pair_sort", "_side_sort"], kind="stable").drop(
        columns=["_pair_sort", "_side_sort"]
    )

    batch = pair_rows.head(args.batch_size).copy()
    batch_ids = set(batch["pair_chase_task_id"])
    batch_sides = side_rows[side_rows["pair_chase_task_id"].isin(batch_ids)].copy()

    pair_rows.to_csv(pairs_path, sep="\t", index=False)
    side_rows.to_csv(sides_path, sep="\t", index=False)
    batch.to_csv(batch_path, sep="\t", index=False)
    batch_sides.to_csv(batch_sides_path, sep="\t", index=False)
    write_summary(pair_rows, side_rows, summary_path, args.batch_size)

    print(f"Wrote {len(pair_rows):,} pair tasks to {pairs_path}")
    print(f"Wrote {len(side_rows):,} side targets to {sides_path}")
    print(f"Wrote {len(batch):,} pair tasks to {batch_path}")
    print(f"Wrote summary to {summary_path}")


if __name__ == "__main__":
    main()
