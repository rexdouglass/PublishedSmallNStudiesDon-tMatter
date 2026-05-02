#!/usr/bin/env python3
"""Build a level-6 extraction worklist from mirrored pilot source objects.

This does not promote rows. It makes the next parsing work explicit: which
mirrored objects exist, what parser stack should touch them first, and which
pilot source-result rows they can plausibly verify.
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
PILOT = ROOT / "data" / "derived" / "effect_inflation_dataset" / "schema_pilot"
SAMPLE_N = int(os.environ.get("SCHEMA_PILOT_N", "300"))
SAMPLE_SUFFIX = f"sample_{SAMPLE_N}"

SOURCE_FILE_IN = PILOT / f"source_file_codebook_{SAMPLE_SUFFIX}.tsv"
SOURCE_RESULT_IN = PILOT / f"source_result_codebook_{SAMPLE_SUFFIX}.tsv"
LEVEL6_ATTEMPTS_IN = PILOT / f"level6_value_verification_attempts_{SAMPLE_SUFFIX}.tsv"

OUT_TSV = PILOT / f"level6_source_object_extraction_worklist_{SAMPLE_SUFFIX}.tsv"
OUT_SUMMARY = PILOT / f"level6_source_object_extraction_worklist_summary_{SAMPLE_SUFFIX}.tsv"
OUT_REPORT = ROOT / "reports" / f"level6_source_object_extraction_worklist_{SAMPLE_SUFFIX}_2026-04-30.md"


PARSER_PLAN = {
    "full_article_xml": ("structured_xml_first", "lxml/JATS/TEI XPath table parser; regex numeric candidate pass"),
    "pmc_fulltext_xml": ("structured_xml_first", "lxml/PMC JATS XPath table parser; BioC fallback"),
    "full_article_html": ("html_first", "readability/BeautifulSoup DOM parser; retain CSS/XPath selectors"),
    "full_article_pdf": ("pdf_cascade", "GROBID TEI, then PyMuPDF/pdfplumber page text and coordinates, then Camelot/Docling table triage"),
    "supplement_file": ("supplement_first", "archive inventory, pandas/openpyxl/readstat for tabular files, PDF parser for supplement PDFs"),
    "dataset_file": ("table_or_corpus_file", "pandas/readstat/openpyxl with exact row/cell provenance; verify whether this is corpus evidence or original evidence"),
    "registry_record_full": ("registry_json", "already handled by CT.gov verifier where du2024; JSONPath verifier for other registries"),
    "source_object_unclassified": ("classify_first", "sniff media type, archive members, then route to PDF/XML/HTML/table parser"),
}

PRIORITY = {
    "structured_xml_first": 1,
    "registry_json": 1,
    "supplement_first": 2,
    "table_or_corpus_file": 2,
    "html_first": 3,
    "pdf_cascade": 4,
    "classify_first": 5,
}


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


def existing_file(path_value: object) -> bool:
    text = safe_text(path_value)
    if not text:
        return False
    path = Path(text)
    if not path.is_absolute():
        path = ROOT / path
    return path.exists()


def link_source_results(source_files: pd.DataFrame, source_results: pd.DataFrame) -> pd.DataFrame:
    source_result_links: list[dict[str, object]] = []
    for _, file_row in source_files.iterrows():
        source_id = safe_text(file_row.get("source_id"))
        if not source_id:
            matched = pd.DataFrame()
        else:
            matched = source_results.loc[
                source_results["represented_source_id"].eq(source_id)
                | source_results["extraction_source_id"].eq(source_id)
            ].copy()
        source_result_links.append(
            {
                "source_file_id": safe_text(file_row.get("source_file_id")),
                "linked_source_result_count": int(len(matched)),
                "linked_source_result_ids": "|".join(matched["source_result_id"].head(20).astype(str)),
                "linked_result_labels": " || ".join(matched["result_label"].head(5).astype(str)),
                "linked_evidence_levels": "|".join(sorted(set(matched["evidence_level"].astype(str)))) if not matched.empty else "",
                "linked_unverified_result_count": int(
                    matched["number_verified_by_us"].astype(str).str.lower().ne("true").sum()
                )
                if not matched.empty
                else 0,
            }
        )
    return source_files.merge(pd.DataFrame(source_result_links), on="source_file_id", how="left")


def main() -> None:
    source_files = pd.read_csv(SOURCE_FILE_IN, sep="\t", dtype=str, keep_default_na=False)
    source_results = pd.read_csv(SOURCE_RESULT_IN, sep="\t", dtype=str, keep_default_na=False)
    level6 = pd.read_csv(LEVEL6_ATTEMPTS_IN, sep="\t", dtype=str, keep_default_na=False) if LEVEL6_ATTEMPTS_IN.exists() else pd.DataFrame()

    work = source_files.copy()
    work["local_file_exists"] = work["local_path"].apply(existing_file)
    work["parser_route"] = work["source_byte_class"].map(lambda item: PARSER_PLAN.get(item, ("classify_first", ""))[0])
    work["recommended_parser_stack"] = work["source_byte_class"].map(lambda item: PARSER_PLAN.get(item, ("classify_first", PARSER_PLAN["source_object_unclassified"][1]))[1])
    work["parser_priority_rank"] = work["parser_route"].map(PRIORITY).fillna(99).astype(int)
    work["level6_track"] = work["source_byte_class"].map(
        {
            "registry_record_full": "registry_value_verifier",
            "dataset_file": "corpus_or_tabular_value_verifier",
            "full_article_xml": "original_article_value_verifier",
            "pmc_fulltext_xml": "original_article_value_verifier",
            "full_article_html": "original_article_value_verifier",
            "full_article_pdf": "original_article_value_verifier",
            "supplement_file": "supplement_value_verifier",
            "source_object_unclassified": "artifact_classification",
        }
    ).fillna("artifact_classification")
    work = link_source_results(work, source_results)

    if not level6.empty:
        verified_ids = set(level6.loc[level6["promote_to_level6"].astype(str).eq("true"), "source_result_id"])
        work["all_linked_results_already_level6"] = work["linked_source_result_ids"].apply(
            lambda value: bool(value) and all(item in verified_ids for item in str(value).split("|") if item)
        )
    else:
        work["all_linked_results_already_level6"] = False

    work["worklist_status"] = "needs_extraction"
    work.loc[~work["local_file_exists"], "worklist_status"] = "missing_local_file"
    work.loc[work["all_linked_results_already_level6"], "worklist_status"] = "already_verified_for_linked_results"
    work.loc[work["source_byte_class"].eq("registry_record_full") & work["all_linked_results_already_level6"], "worklist_status"] = "handled_by_ctgov_verifier"
    work["next_action"] = work.apply(
        lambda row: (
            "No action for linked pilot rows; CT.gov verifier already recomputed D/N."
            if row["worklist_status"] in {"handled_by_ctgov_verifier", "already_verified_for_linked_results"}
            else f"Run {row['parser_route']} route and create source_result_support rows with exact locator/snippet/cell provenance."
        ),
        axis=1,
    )

    ordered_cols = [
        "source_file_id",
        "source_id",
        "source_byte_class",
        "file_role",
        "media_type_sniffed",
        "byte_size",
        "local_path",
        "local_file_exists",
        "parser_priority_rank",
        "parser_route",
        "recommended_parser_stack",
        "level6_track",
        "linked_source_result_count",
        "linked_unverified_result_count",
        "linked_evidence_levels",
        "linked_source_result_ids",
        "linked_result_labels",
        "worklist_status",
        "next_action",
    ]
    work = work.sort_values(
        ["worklist_status", "parser_priority_rank", "source_byte_class", "linked_unverified_result_count"],
        ascending=[True, True, True, False],
    )
    work[ordered_cols].to_csv(OUT_TSV, sep="\t", index=False)

    summary_rows: list[dict[str, object]] = [
        {"metric": "sample_n", "value": SAMPLE_N},
        {"metric": "source_files_total", "value": int(len(work))},
        {"metric": "source_files_with_local_bytes", "value": int(work["local_file_exists"].sum())},
        {"metric": "source_files_needing_extraction", "value": int(work["worklist_status"].eq("needs_extraction").sum())},
        {"metric": "created_at_utc", "value": datetime.now(timezone.utc).isoformat()},
    ]
    for key, value in work["source_byte_class"].value_counts().sort_index().items():
        summary_rows.append({"metric": f"source_byte_class::{key}", "value": int(value)})
    for key, value in work["parser_route"].value_counts().sort_index().items():
        summary_rows.append({"metric": f"parser_route::{key}", "value": int(value)})
    for key, value in work["worklist_status"].value_counts().sort_index().items():
        summary_rows.append({"metric": f"worklist_status::{key}", "value": int(value)})
    summary = pd.DataFrame(summary_rows)
    summary.to_csv(OUT_SUMMARY, sep="\t", index=False)

    needs = work.loc[work["worklist_status"].eq("needs_extraction")].copy()
    lines = [
        "# Level-6 Source-Object Extraction Worklist",
        "",
        f"- Sample rows: {SAMPLE_N}",
        f"- Source-file artifacts: {len(work)}",
        f"- Artifacts with local bytes present: {int(work['local_file_exists'].sum())}",
        f"- Artifacts still needing extraction work: {len(needs)}",
        "",
        "## Parser Routes",
        "",
    ]
    for route, count in work["parser_route"].value_counts().sort_index().items():
        lines.append(f"- `{route}`: {int(count)}")
    lines.extend(["", "## Highest-Priority Remaining Objects", ""])
    for _, row in needs.head(25).iterrows():
        lines.append(
            f"- `{row['source_file_id']}` `{row['source_byte_class']}` -> `{row['parser_route']}`; "
            f"linked unverified results={row['linked_unverified_result_count']}; `{row['local_path']}`"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- This is a parser worklist, not evidence promotion. A row only moves to level 6 after exact value-bearing text/table/data is linked through `source_result_support` and the plotted D/N transformation is verified.",
            "- Registry JSON is already high-yield for CT.gov rows; the remaining registry blocker is source-version drift, handled separately in the CT.gov drift ledger.",
            "- Dataset/corpus files can verify what a corpus says, but they do not by themselves verify the represented original paper unless the represented-source bytes are also obtained and parsed.",
            "",
            "## Output Files",
            "",
            f"- `{rel(OUT_TSV)}`",
            f"- `{rel(OUT_SUMMARY)}`",
        ]
    )
    OUT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    OUT_REPORT.write_text("\n".join(lines) + "\n")

    print(f"Wrote {OUT_TSV}")
    print(f"Wrote {OUT_SUMMARY}")
    print(f"Wrote {OUT_REPORT}")
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
