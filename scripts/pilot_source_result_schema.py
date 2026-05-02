#!/usr/bin/env python3
"""Pilot the source/result/source-access schema on a random dot sample.

This is intentionally diagnostic. It maps the current dot-level audit table
onto the proposed source-result model and records the places where current
extractions lack the fields the stricter schema needs.
"""

from __future__ import annotations

import hashlib
import os
import re
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DERIVED = ROOT / "data" / "derived" / "effect_inflation_dataset"
DOTS = DERIVED / "plot_dot_membership.tsv"
OUT_DIR = DERIVED / "schema_pilot"
SAMPLE_N = int(os.environ.get("SCHEMA_PILOT_N", "300"))
SAMPLE_SEED = int(os.environ.get("SCHEMA_PILOT_SEED", "20260429"))
SAMPLE_SUFFIX = f"sample_{SAMPLE_N}"


def safe_text(value: object) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    text = str(value)
    return re.sub(r"\s+", " ", text.replace("\t", " ").replace("\r", " ").replace("\n", " ")).strip()


def slugify(text: object, fallback: str = "item", max_len: int = 72) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", safe_text(text).lower()).strip("_")
    return (slug or fallback)[:max_len].strip("_") or fallback


def stable_hash(*parts: object, length: int = 12) -> str:
    payload = "\n".join(safe_text(part) for part in parts)
    return hashlib.sha1(payload.encode("utf-8", errors="ignore")).hexdigest()[:length]


def file_sha256(path: Path, chunk_size: int = 1024 * 1024) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(chunk_size), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def one_line_frame(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for column in out.columns:
        if pd.api.types.is_object_dtype(out[column]) or pd.api.types.is_string_dtype(out[column]):
            out[column] = out[column].map(safe_text)
    return out


def compact_number(value: object) -> str:
    text = safe_text(value)
    if not text:
        return ""
    try:
        number = float(text)
    except ValueError:
        return text
    return f"{number:.12g}"


def source_id_for(kind: str, label: object, key: object = "") -> str:
    base = safe_text(key) or safe_text(label)
    return f"{kind}_{slugify(base, kind)}"


def represented_source_type(row: pd.Series) -> str:
    layer = safe_text(row.get("source_layer")).lower()
    unit = safe_text(row.get("row_unit")).lower()
    quality = safe_text(row.get("paper_key_quality")).lower()
    family = safe_text(row.get("source_family")).lower()
    if "clinicaltrials" in family or "ctgov" in family or "registry" in unit:
        return "registry_trial_or_result"
    if "claim" in unit or "claim" in layer:
        return "claim"
    if "paper" in quality or "doi" in quality or safe_text(row.get("paper_doi")):
        return "paper"
    if "project" in unit or "study" in unit:
        return "project_or_study"
    if safe_text(row.get("paper_title")):
        return "paper_like_work"
    return "unknown_represented_work"


def is_generated_dot_citation(key: object) -> bool:
    return safe_text(key).startswith("dot_")


def extraction_source_type(row: pd.Series) -> str:
    family = safe_text(row.get("source_family")).lower()
    locator = safe_text(row.get("source_file_or_catalog")).lower()
    if "clinicaltrials" in family or "ctgov" in family:
        return "database_or_registry"
    if "dataverse" in family or "osf" in family or "openicpsr" in family or "zenodo" in family:
        return "repository_or_package"
    if "score" in family or "corpus" in family or "database" in family or "catalog" in locator:
        return "corpus_or_database"
    if "plot" in family or "internal" in family:
        return "internal_derived_dataset"
    return "source_family_or_collection"


def parse_access_locator(raw: object) -> dict[str, str]:
    locator = safe_text(raw)
    pieces = [part.strip() for part in locator.split(";") if part.strip()]
    first_piece = pieces[0] if pieces else ""
    match = re.search(r"(https?://\S+|(?:data|docs|reports|scripts)/[^;,\s]+)", locator)
    access_url = ""
    local_path = ""
    if match:
        token = match.group(1).rstrip(").,;")
        if token.startswith("http"):
            access_url = token
        else:
            local_path = token
    elif first_piece.startswith("http"):
        access_url = first_piece
    elif first_piece.startswith(("data/", "docs/", "reports/", "scripts/")):
        local_path = first_piece

    content_type = ""
    if local_path:
        name = Path(local_path).name.lower()
        if name.endswith(".csv.gz"):
            content_type = "csv.gz"
        elif "." in name:
            content_type = name.rsplit(".", 1)[-1]
    elif access_url:
        content_type = "url"

    if local_path:
        status = "local_file_found" if (ROOT / local_path).exists() else "local_path_missing"
        method = "existing_local_file"
    elif access_url:
        status = "remote_url_not_cached"
        method = "remote_url"
    elif locator:
        status = "unresolved_locator"
        method = "catalog_or_prose_locator"
    else:
        status = "missing_locator"
        method = "missing"

    if len(pieces) > 1 and status == "local_file_found":
        method = "existing_local_file_plus_notes"
    elif len(pieces) > 1 and status != "missing_locator":
        method = "mixed_locator_and_notes"

    return {
        "locator_raw": locator,
        "remote_url": access_url,
        "local_path": local_path,
        "content_type": content_type,
        "access_status": status,
        "retrieval_method": method,
        "locator_piece_count": str(len(pieces)),
    }


def infer_transformation(row: pd.Series) -> tuple[str, str, str]:
    family = safe_text(row.get("source_family")).lower()
    locator = safe_text(row.get("source_file_or_catalog")).lower()
    unit = safe_text(row.get("row_unit")).lower()
    if "clinicaltrials" in family or "ctgov" in family:
        return (
            "d_proxy_from_registry_result",
            "D was imported as a registry-result proxy reconstructed upstream from ClinicalTrials.gov/AACT result fields, p-values, or enrollment; the current dot table does not preserve the verbatim p-value/effect cells.",
            "medium",
        )
    if "score" in family or "score" in locator:
        return (
            "source_specific_statistic_to_d",
            "D was imported from the SCORE/COS extraction layer after source-specific statistic parsing; the current dot table does not preserve the exact F/t/p text used for conversion.",
            "medium",
        )
    if "metaketa" in family or "political" in family or "field experiment" in family:
        return (
            "curated_project_extraction_to_d_or_native_proxy",
            "D/N were imported from the curated political-science rescue layer; component/native extraction details need to be represented in source_result fields rather than only in source_file notes.",
            "medium",
        )
    if "median" in unit or "paper_level" in unit:
        return (
            "within_paper_or_project_median",
            "This row is a collapsed paper/project result; D is the retained median or selected representative effect from upstream eligible result rows.",
            "medium",
        )
    return (
        "upstream_source_import",
        "D/N were imported from an upstream corpus-specific extractor; the current dot table records the final plotted D/N but not the full verbatim native-to-standardized transformation.",
        "low",
    )


def problem_rows_for(row: pd.Series, access: dict[str, str], canonical_count: int) -> list[dict[str, str]]:
    problems: list[dict[str, str]] = []
    srid = safe_text(row["_source_result_id"])

    def add(code: str, severity: str, detail: str) -> None:
        problems.append(
            {
                "source_result_id": srid,
                "problem_code": code,
                "severity": severity,
                "detail": detail,
                "suggested_rework": SUGGESTED_REWORK.get(code, ""),
            }
        )

    if not safe_text(row.get("paper_title")):
        add("missing_result_label", "high", "No paper/result label is available in the dot row.")
    add(
        "missing_verbatim_effect_text",
        "high",
        "The current dot table stores numeric D but not the literal effect/statistic text copied from the source.",
    )
    add(
        "missing_verbatim_n_text",
        "high",
        "The current dot table stores numeric N but not the literal N/sample-size text copied from the source.",
    )
    if access["access_status"] in {"missing_locator", "unresolved_locator", "local_path_missing", "remote_url_not_cached"}:
        add(
            f"access_{access['access_status']}",
            "medium",
            f"Access locator status is {access['access_status']}: {access['locator_raw'][:180]}",
        )
    if int(access["locator_piece_count"] or "0") > 1:
        add(
            "locator_mixes_path_and_notes",
            "medium",
            "source_file_or_catalog combines a path or URL with prose notes; source_access needs atomic URL/path rows and extraction notes elsewhere.",
        )
    if not safe_text(row.get("paper_doi")) and safe_text(row.get("paper_key_quality")) not in {"doi", "pubmed_id"}:
        add(
            "represented_source_not_doi_keyed",
            "medium",
            f"Represented source is keyed by {safe_text(row.get('paper_key_quality')) or 'blank'} rather than DOI or another durable bibliographic ID.",
        )
    if not safe_text(row.get("citation_rendered")):
        add(
            "missing_child_rendered_citation",
            "medium",
            "The represented result/work lacks a rendered child citation in this row.",
        )
    if canonical_count > 1:
        add(
            "duplicate_canonical_result_in_sample",
            "low",
            f"{canonical_count} sampled source-result rows map to the same canonical result.",
        )
    return problems


SUGGESTED_REWORK = {
    "missing_result_label": "Require a plotted/source result label and, separately, direct verbatim source text when recovered.",
    "missing_verbatim_effect_text": "Carry raw copied effect/statistic cells before parsing or D conversion.",
    "missing_verbatim_n_text": "Carry raw copied sample-size cells before parsing or N normalization.",
    "access_missing_locator": "Add source_access rows for the exact local file or direct URL.",
    "access_unresolved_locator": "Split prose catalog notes from the retrievable path/URL.",
    "access_local_path_missing": "Cache the source file under data/raw or record an explicit access barrier.",
    "access_remote_url_not_cached": "Download/cache the file when possible and record local_path/checksum.",
    "locator_mixes_path_and_notes": "Normalize source_file_or_catalog into source_access plus extraction_event notes.",
    "represented_source_not_doi_keyed": "Add DOI, PMID, registry ID, or other stable represented_source identifier where available.",
    "missing_child_rendered_citation": "Populate represented source citations, not only parent/corpus citations.",
    "duplicate_canonical_result_in_sample": "Use canonical_result resolution to choose the preferred extraction and preserve alternates.",
}


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    dots = pd.read_csv(DOTS, sep="\t", dtype=str, keep_default_na=False)
    sample = dots.sample(n=min(SAMPLE_N, len(dots)), random_state=SAMPLE_SEED).copy()
    sample = sample.reset_index(drop=False).rename(columns={"index": "original_dot_table_row"})

    source_result_rows: list[dict[str, object]] = []
    source_rows: dict[str, dict[str, object]] = {}
    access_rows: dict[str, dict[str, object]] = {}
    mapping_rows: list[dict[str, object]] = []

    canonical_ids: list[str] = []
    for idx, row in sample.iterrows():
        canonical_id = "cr_" + stable_hash(
            row.get("paper_key"),
            row.get("paper_title"),
            row.get("paper_doi"),
            row.get("row_unit"),
            compact_number(row.get("D")),
            compact_number(row.get("N")),
        )
        canonical_ids.append(canonical_id)
    sample["_canonical_result_id"] = canonical_ids
    canonical_counts = sample["_canonical_result_id"].value_counts().to_dict()

    problem_rows: list[dict[str, str]] = []
    for idx, row in sample.iterrows():
        extraction_source_id = source_id_for("src", row.get("source_family"), row.get("source_citation_key"))
        represented_seed = row.get("paper_key") or row.get("paper_doi") or row.get("paper_title")
        represented_source_id = source_id_for("work", represented_seed, represented_seed)
        canonical_id = row["_canonical_result_id"]
        source_result_id = "sr_" + stable_hash(
            row.get("plot_name"),
            row.get("dot_record_id"),
            row.get("source_family"),
            row.get("paper_key"),
            row.get("paper_title"),
            row.get("D"),
            row.get("N"),
        )
        sample.at[idx, "_source_result_id"] = source_result_id
        access = parse_access_locator(row.get("source_file_or_catalog"))
        access_id = "acc_" + stable_hash(extraction_source_id, access["remote_url"], access["local_path"], access["locator_raw"])
        method, explanation, confidence = infer_transformation(row)

        source_rows[extraction_source_id] = {
            "source_id": extraction_source_id,
            "source_type": extraction_source_type(row),
            "source_role_in_sample": "extraction_source",
            "title": row.get("source_label") or row.get("source_family"),
            "citation_key": row.get("source_citation_key"),
            "citation_ref": row.get("source_citation_ref"),
            "citation_rendered": row.get("source_citation_rendered"),
            "bibtex_file": row.get("source_citation_bibtex_file"),
            "doi": "",
            "url": "",
            "notes": "Parent/corpus/source-family record inferred from plot_dot_membership.tsv.",
        }
        source_rows.setdefault(
            represented_source_id,
            {
                "source_id": represented_source_id,
                "source_type": represented_source_type(row),
                "source_role_in_sample": "represented_source",
                "title": row.get("paper_title"),
                "citation_key": "" if is_generated_dot_citation(row.get("citation_key")) else row.get("citation_key"),
                "citation_ref": "" if is_generated_dot_citation(row.get("citation_key")) else row.get("citation_ref"),
                "citation_rendered": "" if is_generated_dot_citation(row.get("citation_key")) else row.get("citation_rendered"),
                "bibtex_file": "" if is_generated_dot_citation(row.get("citation_key")) else row.get("citation_bibtex_file"),
                "doi": row.get("paper_doi"),
                "url": "",
                "notes": (
                    "Represented research work/result inferred from plot_dot_membership.tsv. "
                    "Synthetic dot-level audit citations are kept on source_result rows as generated_result_* fields, "
                    "not as represented-source bibliographic citations."
                ),
            },
        )

        access_rows[access_id] = {
            "access_id": access_id,
            "source_id": extraction_source_id,
            "access_role": "source_file_or_catalog",
            "remote_url": access["remote_url"],
            "api_url": "",
            "local_path": access["local_path"],
            "content_type": access["content_type"],
            "file_sha256": file_sha256(ROOT / access["local_path"]) if access["local_path"] and (ROOT / access["local_path"]).exists() else "",
            "file_size_bytes": (ROOT / access["local_path"]).stat().st_size if access["local_path"] and (ROOT / access["local_path"]).exists() else "",
            "retrieved_at": "",
            "retrieved_by": "preexisting_pipeline_or_unknown",
            "retrieval_method": access["retrieval_method"],
            "access_status": access["access_status"],
            "access_barrier": "",
            "access_notes": access["locator_raw"],
        }

        source_result_rows.append(
            {
                "source_result_id": source_result_id,
                "sample_seed": SAMPLE_SEED,
                "sample_row_index": idx + 1,
                "original_dot_table_row": int(row.get("original_dot_table_row", 0)) + 2,
                "plot_name": row.get("plot_name"),
                "dot_record_id": row.get("dot_record_id"),
                "canonical_result_id": canonical_id,
                "extraction_source_id": extraction_source_id,
                "represented_source_id": represented_source_id,
                "access_id": access_id,
                "source_locator": row.get("source_file_or_catalog"),
                "result_label": row.get("paper_title"),
                "outcome_label": row.get("paper_title"),
                "verbatim_source_row_text": "",
                "verbatim_outcome_text": "",
                "verbatim_effect_text": "",
                "verbatim_se_text": "",
                "verbatim_n_text": "",
                "verbatim_p_text": "",
                "native_effect_value": "",
                "native_effect_metric": "",
                "native_standard_error": "",
                "native_n_total": row.get("N"),
                "native_n_treatment": "",
                "native_n_control": "",
                "native_cluster_n": "",
                "standardized_effect_value": row.get("D"),
                "standardized_effect_metric": "d_or_d_proxy",
                "standardized_n": row.get("N"),
                "d": row.get("D"),
                "d_conversion_method": method,
                "d_conversion_inputs": "",
                "transformation_explanation": explanation,
                "transformation_confidence": confidence,
                "source_citation_key": row.get("source_citation_key"),
                "represented_source_citation_key": "" if is_generated_dot_citation(row.get("citation_key")) else row.get("citation_key"),
                "represented_source_citation_rendered": "" if is_generated_dot_citation(row.get("citation_key")) else row.get("citation_rendered"),
                "generated_result_citation_key": row.get("citation_key"),
                "generated_result_citation_rendered": row.get("citation_rendered"),
                "generated_result_citation_note": "Synthetic dot-level audit citation, not a bibliographic citation for the represented work.",
            }
        )
        mapping_rows.append(
            {
                "mapping_id": "map_" + stable_hash(source_result_id, extraction_source_id, represented_source_id),
                "source_result_id": source_result_id,
                "from_source_id": extraction_source_id,
                "to_source_id": represented_source_id,
                "relationship_type": "extraction_source_reports_result_for_represented_source",
                "relationship_confidence": "medium",
                "notes": "Inferred from dot-level parent source family and represented paper/result key.",
            }
        )
        problem_rows.extend(problem_rows_for(sample.loc[idx], access, int(canonical_counts.get(canonical_id, 1))))

    source_result = pd.DataFrame(source_result_rows)
    problems = pd.DataFrame(problem_rows)
    problem_counts = problems.groupby("source_result_id").size().to_dict() if not problems.empty else {}
    source_result["problem_count"] = source_result["source_result_id"].map(lambda key: int(problem_counts.get(key, 0)))
    source_result["coding_status"] = source_result["problem_count"].map(lambda n: "coded_with_schema_gaps" if n else "fully_coded")

    canonical_rows = []
    for canonical_id, group in source_result.groupby("canonical_result_id", sort=False):
        first = group.iloc[0]
        canonical_rows.append(
            {
                "canonical_result_id": canonical_id,
                "represented_source_id": first["represented_source_id"],
                "preferred_source_result_id": first["source_result_id"],
                "source_result_count_in_sample": len(group),
                "result_label": first["result_label"],
                "D": first["d"],
                "N": first["standardized_n"],
                "plot_names": "; ".join(sorted(set(group["plot_name"].map(safe_text)))),
                "resolution_status": "single_source_result_in_sample" if len(group) == 1 else "multiple_source_results_need_resolution",
                "resolution_notes": f"Pilot canonicalization; full pass should resolve duplicates across all rows, not only the {SAMPLE_N}-row sample.",
            }
        )

    summary_rows = [
        {"metric": "sample_n", "value": len(source_result)},
        {"metric": "sample_seed", "value": SAMPLE_SEED},
        {"metric": "unique_extraction_sources", "value": source_result["extraction_source_id"].nunique()},
        {"metric": "unique_represented_sources", "value": source_result["represented_source_id"].nunique()},
        {"metric": "unique_canonical_results", "value": source_result["canonical_result_id"].nunique()},
        {"metric": "source_results_fully_coded_without_problem_flags", "value": int((source_result["problem_count"] == 0).sum())},
        {"metric": "source_results_with_problem_flags", "value": int((source_result["problem_count"] > 0).sum())},
    ]
    if not problems.empty:
        for code, count in problems["problem_code"].value_counts().sort_index().items():
            summary_rows.append({"metric": f"problem::{code}", "value": int(count)})
        for severity, count in problems["severity"].value_counts().sort_index().items():
            summary_rows.append({"metric": f"severity::{severity}", "value": int(count)})

    outputs = {
        f"source_result_{SAMPLE_SUFFIX}.tsv": source_result,
        f"source_{SAMPLE_SUFFIX}.tsv": pd.DataFrame(source_rows.values()),
        f"source_access_{SAMPLE_SUFFIX}.tsv": pd.DataFrame(access_rows.values()),
        f"canonical_result_{SAMPLE_SUFFIX}.tsv": pd.DataFrame(canonical_rows),
        f"source_source_mapping_{SAMPLE_SUFFIX}.tsv": pd.DataFrame(mapping_rows),
        f"coding_problems_{SAMPLE_SUFFIX}.tsv": problems,
        f"coding_summary_{SAMPLE_SUFFIX}.tsv": pd.DataFrame(summary_rows),
    }
    for name, frame in outputs.items():
        one_line_frame(frame).to_csv(OUT_DIR / name, sep="\t", index=False)

    print(f"Wrote schema pilot sample to {OUT_DIR.relative_to(ROOT)}")
    print(pd.DataFrame(summary_rows).to_string(index=False))


if __name__ == "__main__":
    main()
