#!/usr/bin/env python3
"""Retrace the sampled source-result pilot through stored local breadcrumbs.

This is a reproducibility stress test. It starts from the sampled source-result
rows created by ``pilot_source_result_schema.py``, walks back through the
plotted-row files, then tries to recover the upstream source/candidate rows and
literal numeric inputs that produced the plotted D/N.
"""

from __future__ import annotations

import json
import hashlib
import math
import os
import re
from functools import lru_cache
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DERIVED = ROOT / "data" / "derived" / "effect_inflation_dataset"
PILOT = DERIVED / "schema_pilot"
SAMPLE_N = int(os.environ.get("SCHEMA_PILOT_N", "300"))
SAMPLE_SUFFIX = f"sample_{SAMPLE_N}"

DOTS = DERIVED / "plot_dot_membership.tsv"
SOURCE_RESULT_SAMPLE = PILOT / f"source_result_{SAMPLE_SUFFIX}.tsv"
OUT_RETRACE = PILOT / f"retrace_source_result_{SAMPLE_SUFFIX}.tsv"
OUT_HUMAN_CHECK = PILOT / f"human_check_source_result_{SAMPLE_SUFFIX}.tsv"
OUT_EVENTS = PILOT / f"retrace_events_{SAMPLE_SUFFIX}.tsv"
OUT_PROBLEMS = PILOT / f"retrace_problems_{SAMPLE_SUFFIX}.tsv"
OUT_SUMMARY = PILOT / f"retrace_summary_{SAMPLE_SUFFIX}.tsv"

PLOT1 = DERIVED / "plot1_replication_pair_details.csv"
PLOT2 = DERIVED / "plot2_published_paper_details.csv"
PLOT3 = DERIVED / "plot3_preregistered_results.csv"
PLOT4 = DERIVED / "plot4_all_source_dn_rows.csv"
CANDIDATE_PAPERS = ROOT / "data" / "derived" / "corpus_candidates" / "candidate_d_n_papers.csv"
CANDIDATE_ROWS = ROOT / "data" / "derived" / "corpus_candidates" / "candidate_d_n_rows.csv.gz"
STRICT_POLISCI = DERIVED / "plot3_political_science_strict_rescue_rows.csv"


def safe_text(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and math.isnan(value):
        return ""
    return re.sub(r"\s+", " ", str(value).replace("\t", " ").replace("\r", " ").replace("\n", " ")).strip()


def one_line_frame(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for column in out.columns:
        if pd.api.types.is_object_dtype(out[column]) or pd.api.types.is_string_dtype(out[column]):
            out[column] = out[column].map(safe_text)
    return out


def numeric(value: object) -> float | None:
    try:
        if safe_text(value) == "":
            return None
        return float(value)
    except Exception:
        return None


def close_number(left: object, right: object, tol: float = 1e-8) -> bool:
    a = numeric(left)
    b = numeric(right)
    if a is None or b is None:
        return False
    return abs(a - b) <= tol * max(1.0, abs(a), abs(b))


def rel(path: Path | str) -> str:
    p = Path(path)
    if not p.is_absolute():
        p = ROOT / p
    try:
        return str(p.relative_to(ROOT))
    except ValueError:
        return str(p)


def file_sha256(path: Path, chunk_size: int = 1024 * 1024) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(chunk_size), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def file_metadata(path: Path | None) -> dict[str, object]:
    if not path or not path.exists() or not path.is_file():
        return {"file_size_bytes": "", "file_sha256": ""}
    return {"file_size_bytes": path.stat().st_size, "file_sha256": file_sha256(path)}


def path_from_locator(locator: object) -> Path | None:
    text = safe_text(locator)
    if not text:
        return None
    first = text.split(";", 1)[0].strip()
    if first.startswith(("data/", "docs/", "reports/", "scripts/", "/")):
        token = first
    else:
        match = re.search(r"((?:data|docs|reports|scripts)/[^;,\s]+)", first)
        token = match.group(1) if match else first
    if token.startswith("http"):
        return None
    p = Path(token)
    if not p.is_absolute():
        p = ROOT / p
    return p


@lru_cache(maxsize=128)
def read_table(path_string: str) -> pd.DataFrame:
    path = Path(path_string)
    if not path.is_absolute():
        path = ROOT / path
    suffixes = "".join(path.suffixes).lower()
    if suffixes.endswith(".tsv"):
        return pd.read_csv(path, sep="\t", dtype=str, keep_default_na=False)
    if suffixes.endswith(".csv.gz"):
        return pd.read_csv(path, dtype=str, keep_default_na=False)
    if suffixes.endswith(".csv"):
        return pd.read_csv(path, dtype=str, keep_default_na=False)
    if suffixes.endswith(".xlsx"):
        return pd.read_excel(path, dtype=str).fillna("")
    if suffixes.endswith(".dta"):
        return pd.read_stata(path, convert_categoricals=False).fillna("").astype(str)
    raise ValueError(f"Unsupported table type: {path}")


@lru_cache(maxsize=1)
def candidate_row_indices() -> tuple[pd.DataFrame, dict[tuple[str, str], list[int]], dict[tuple[str, str], list[int]]]:
    """Index the large candidate-row table once for repeated pilot lookups."""
    print(f"Indexing candidate child rows from {CANDIDATE_ROWS.relative_to(ROOT)}...", flush=True)
    rows = read_table(str(CANDIDATE_ROWS))
    title_rows = rows.loc[rows["title"].map(safe_text).ne(""), ["source_corpus", "title"]]
    paper_rows = rows.loc[rows["paper_id"].map(safe_text).ne(""), ["source_corpus", "paper_id"]]
    # Use .groups rather than .indices here. .indices is positional within the
    # filtered frame, so applying it back to the full rows table can silently
    # attach an unrelated child result to a paper median.
    by_title = {tuple(key): list(value) for key, value in title_rows.groupby(["source_corpus", "title"], sort=False).groups.items()}
    by_paper_id = {tuple(key): list(value) for key, value in paper_rows.groupby(["source_corpus", "paper_id"], sort=False).groups.items()}
    print(f"Indexed {len(rows)} candidate child rows ({len(by_title)} title keys, {len(by_paper_id)} paper-id keys).", flush=True)
    return rows, by_title, by_paper_id


def json_row(row: pd.Series, limit: int = 12000) -> str:
    payload = {
        str(k): safe_text(v)
        for k, v in row.to_dict().items()
        if safe_text(v) != ""
    }
    text = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    return text if len(text) <= limit else text[:limit] + "...[truncated]"


def add_event(events: list[dict[str, object]], source_result_id: str, step: str, path: Path | None, status: str, method: str, notes: str = "") -> None:
    metadata = file_metadata(path)
    events.append(
        {
            "source_result_id": source_result_id,
            "event_step": step,
            "path": rel(path) if path else "",
            "path_exists": bool(path and path.exists()),
            "file_size_bytes": metadata["file_size_bytes"],
            "file_sha256": metadata["file_sha256"],
            "status": status,
            "match_method": method,
            "notes": notes,
        }
    )


def add_problem(problems: list[dict[str, object]], source_result_id: str, code: str, severity: str, detail: str) -> None:
    problems.append(
        {
            "source_result_id": source_result_id,
            "problem_code": code,
            "severity": severity,
            "detail": detail,
        }
    )


def find_plot_row(source_result: pd.Series, dot: pd.Series, events: list[dict[str, object]], problems: list[dict[str, object]]) -> tuple[pd.Series | None, Path | None, str]:
    srid = safe_text(source_result["source_result_id"])
    plot_name = safe_text(dot.get("plot_name"))
    dot_id = safe_text(dot.get("dot_record_id"))

    if plot_name == "Plot 4":
        df = read_table(str(PLOT4))
        match = df.loc[df["point_id"].astype(str).eq(dot_id)]
        add_event(events, srid, "find_plot_row", PLOT4, "found" if len(match) == 1 else "not_found", "plot4.point_id == dot_record_id", f"matches={len(match)}")
        return (match.iloc[0] if len(match) else None), PLOT4, "plot4"

    if plot_name == "Plot 3":
        df = read_table(str(PLOT3))
        match = df.loc[df["point_id"].astype(str).eq(dot_id)]
        add_event(events, srid, "find_plot_row", PLOT3, "found" if len(match) == 1 else "not_found", "plot3.point_id == dot_record_id", f"matches={len(match)}")
        return (match.iloc[0] if len(match) else None), PLOT3, "plot3"

    if plot_name == "Plot 2":
        df = read_table(str(PLOT2))
        paper_id = dot_id.removeprefix("plot2::")
        match = df.loc[df["paper_id"].astype(str).eq(paper_id)]
        add_event(events, srid, "find_plot_row", PLOT2, "found" if len(match) == 1 else "not_found", "plot2.paper_id from dot_record_id", f"matches={len(match)}")
        return (match.iloc[0] if len(match) else None), PLOT2, "plot2"

    if plot_name == "Plot 1":
        df = read_table(str(PLOT1))
        if "::" in dot_id:
            pair_id, side = dot_id.rsplit("::", 1)
            match = df.loc[df["pair_id"].astype(str).eq(pair_id)]
            add_event(events, srid, "find_plot_row", PLOT1, "found" if len(match) == 1 else "not_found", f"plot1.pair_id == {pair_id}; side={side}", f"matches={len(match)}")
            row = match.iloc[0].copy() if len(match) else None
            if row is not None:
                row["__plot1_side"] = side
            return row, PLOT1, "plot1"
    add_problem(problems, srid, "plot_row_not_found", "high", f"Could not resolve plot row for {plot_name} / {dot_id}.")
    return None, None, ""


def match_candidate_paper(dot: pd.Series, plot_row: pd.Series | None, events: list[dict[str, object]], problems: list[dict[str, object]], srid: str) -> tuple[pd.Series | None, pd.DataFrame]:
    cand = read_table(str(CANDIDATE_PAPERS))
    title = safe_text(dot.get("paper_title")) or safe_text(plot_row.get("row_label") if plot_row is not None else "")
    row_label = safe_text(plot_row.get("row_label") if plot_row is not None else "") or title
    d_value = dot.get("D")
    n_value = dot.get("N")
    source_family = safe_text(dot.get("source_family")) or safe_text(plot_row.get("source_family") if plot_row is not None else "")
    point_id = safe_text(plot_row.get("point_id") if plot_row is not None else dot.get("dot_record_id"))
    parsed_source_corpus = ""
    parsed_unit_id = ""
    if point_id.startswith("published::") and point_id.count("::") >= 2:
        _, parsed_source_corpus, parsed_unit_id = point_id.split("::", 2)
    parenthetical_unit = ""
    parenthetical_match = re.search(r"\(([^()]+)\)\s*$", row_label)
    if parenthetical_match:
        parenthetical_unit = parenthetical_match.group(1)

    match = cand.loc[cand["title"].astype(str).eq(title)].copy()
    if "source_corpus" in cand.columns and source_family:
        corpus_match = match.loc[match["source_corpus"].astype(str).eq(source_family)]
        if len(corpus_match):
            match = corpus_match
    if len(match) == 0 and parsed_source_corpus and parsed_unit_id:
        match = cand.loc[
            cand["source_corpus"].astype(str).eq(parsed_source_corpus)
            & cand["unit_id"].astype(str).eq(parsed_unit_id)
        ].copy()
    if len(match) == 0 and row_label:
        match = cand.loc[cand["unit_id"].astype(str).eq(row_label)].copy()
    if len(match) == 0 and parenthetical_unit:
        match = cand.loc[cand["unit_id"].astype(str).eq(parenthetical_unit)].copy()
    if len(match) > 1:
        exact = match.loc[match["D_median"].map(lambda x: close_number(x, d_value)) & match["N_median"].map(lambda x: close_number(x, n_value))]
        if len(exact):
            match = exact
    if len(match) == 0 and plot_row is not None:
        # Plot 2 stores source_key/paper_id rather than only title.
        source_key = safe_text(plot_row.get("source_key"))
        paper_id = safe_text(plot_row.get("paper_id"))
        match = cand.loc[cand["source_corpus"].astype(str).eq(source_key) & cand["unit_id"].astype(str).eq(paper_id)].copy()
    if len(match) > 1:
        exact = match.loc[match["D_median"].map(lambda x: close_number(x, d_value)) & match["N_median"].map(lambda x: close_number(x, n_value))]
        if len(exact):
            match = exact
    add_event(
        events,
        srid,
        "match_candidate_paper",
        CANDIDATE_PAPERS,
        "found" if len(match) else "not_found",
        "title/source/D/N, parsed published::source::unit_id, row_label unit_id, parenthetical unit_id, or source_key/unit_id",
        f"matches={len(match)}; parsed_source_corpus={parsed_source_corpus}; parsed_unit_id={parsed_unit_id}; parenthetical_unit={parenthetical_unit}",
    )
    if len(match) == 0:
        return None, pd.DataFrame()

    paper_row = match.iloc[0]
    rows, by_title, by_paper_id = candidate_row_indices()
    source_corpus = safe_text(paper_row.get("source_corpus"))
    title_key = safe_text(paper_row.get("title"))
    paper_id_key = safe_text(paper_row.get("unit_id"))
    # Prefer the paper/unit identifier before the title. Outcome titles are
    # frequently reused across trial registry rows, so title-first matching can
    # attach a child result from a different NCT with the same outcome label.
    child_indices = by_paper_id.get((source_corpus, paper_id_key), [])
    child = rows.loc[child_indices].copy() if child_indices else pd.DataFrame()
    if len(child) == 0:
        child_indices = by_title.get((source_corpus, title_key), [])
        child = rows.loc[child_indices].copy() if child_indices else pd.DataFrame()
    if len(child):
        d_exact = child.loc[child["D"].map(lambda x: close_number(x, d_value)) & child["N"].map(lambda x: close_number(x, n_value))]
        if len(d_exact):
            child = d_exact
    add_event(events, srid, "match_candidate_rows", CANDIDATE_ROWS, "found" if len(child) else "not_found", "source_corpus/title or source_corpus/paper_id; D/N narrowed", f"matches={len(child)}")
    return paper_row, child


def match_ctgov_raw(dot: pd.Series, events: list[dict[str, object]], srid: str) -> pd.DataFrame:
    path = ROOT / "data/raw/corpus_candidates/ctgov_kg/efficacy_df.csv"
    df = read_table(str(path))
    haystack = " ".join([safe_text(dot.get("dot_record_id")), safe_text(dot.get("paper_key")), safe_text(dot.get("paper_title"))])
    nct_match = re.search(r"NCT\d{8}", haystack, re.IGNORECASE)
    nct = nct_match.group(0).upper() if nct_match else ""
    title = safe_text(dot.get("paper_title"))
    match = df.loc[df["NCT_ID"].astype(str).str.upper().eq(nct)].copy() if nct else pd.DataFrame()
    if len(match) and title:
        exact = match.loc[match["outcome_title"].astype(str).eq(title)]
        if len(exact):
            match = exact
    add_event(events, srid, "match_ctgov_raw", path, "found" if len(match) else "not_found", "NCT_ID plus outcome_title", f"nct={nct}; matches={len(match)}")
    return match


def match_replication_pair(dot: pd.Series, events: list[dict[str, object]], srid: str) -> pd.Series | None:
    path = ROOT / "data/derived/replication_pairs/replication_pairs_all_on_hand.csv"
    df = read_table(str(path))
    dot_id = safe_text(dot.get("dot_record_id"))
    pair = ""
    side = ""
    if dot_id.startswith("replication::") and dot_id.count("::") >= 2:
        _, pair, side = dot_id.split("::", 2)
    elif "::" in dot_id:
        pair, side = dot_id.rsplit("::", 1)
    match = df.loc[df["pair_id"].astype(str).eq(pair)].copy() if pair else pd.DataFrame()
    add_event(events, srid, "match_replication_pair_source", path, "found" if len(match) else "not_found", "pair_id from dot_record_id", f"pair_id={pair}; side={side}; matches={len(match)}")
    return match.iloc[0] if len(match) else None


def match_staged_replication_pair(path: Path, dot: pd.Series, events: list[dict[str, object]], srid: str) -> pd.Series | None:
    df = read_table(str(path))
    dot_id = safe_text(dot.get("dot_record_id"))
    pair = ""
    if dot_id.startswith("staged::") and dot_id.count("::") >= 2:
        parts = dot_id.split("::")
        if len(parts) >= 3:
            pair = parts[2]
    match = df.loc[df["pair_id"].astype(str).eq(pair)].copy() if pair and "pair_id" in df.columns else pd.DataFrame()
    add_event(events, srid, "match_staged_replication_pair_source", path, "found" if len(match) else "not_found", "pair_id from staged dot_record_id", f"pair_id={pair}; matches={len(match)}")
    return match.iloc[0] if len(match) else None


def match_strict_polisci(dot: pd.Series, events: list[dict[str, object]], srid: str) -> pd.DataFrame:
    df = read_table(str(STRICT_POLISCI))
    row_numbers = [part.strip() for part in safe_text(dot.get("source_row_number")).split(";") if part.strip()]
    match = pd.DataFrame()
    if row_numbers and "source_row_number" in df.columns:
        match = df.loc[df["source_row_number"].astype(str).isin(row_numbers)].copy()
    if len(match) == 0 and safe_text(dot.get("paper_title")):
        title = safe_text(dot.get("paper_title")).replace(" - paper median of 3 preregistered result rows", "")
        match = df.loc[df["row_label"].astype(str).str.contains(re.escape(title), case=False, na=False)].copy()
    add_event(events, srid, "match_political_science_strict_rows", STRICT_POLISCI, "found" if len(match) else "not_found", "source_row_number list or row_label", f"matches={len(match)}")
    return match


def selected_candidate_child_fields(child: pd.DataFrame) -> dict[str, str]:
    if child.empty:
        return {}
    row = child.iloc[0]
    fields = [
        "row_id",
        "paper_id",
        "study_id",
        "outcome",
        "effect_type",
        "effect",
        "se",
        "z",
        "abs_z",
        "N",
        "D",
        "D_method",
        "N_method",
        "raw_file",
        "notes",
    ]
    return {f"candidate_{field}": safe_text(row.get(field)) for field in fields if field in child.columns}


def source_text_status(row: pd.Series) -> str:
    has_effect = bool(safe_text(row.get("recovered_verbatim_effect_text")))
    has_n = bool(safe_text(row.get("recovered_verbatim_n_text")))
    if has_effect and has_n:
        return "source_cells_recovered"
    if has_n:
        return "n_only_recovered"
    return "plot_summary_only"


def human_check_text(row: pd.Series) -> str:
    status = source_text_status(row)
    parts: list[str] = []
    if status == "plot_summary_only":
        parts.append("PLOT-ONLY: no upstream effect/statistic cell recovered")
    parts.extend(
        [
            f"label={safe_text(row.get('result_label'))}",
            f"source_directness={safe_text(row.get('source_directness'))}",
        ]
    )
    if safe_text(row.get("recovered_verbatim_effect_text")):
        parts.append(f"effect_or_stat={safe_text(row.get('recovered_verbatim_effect_text'))}")
    if safe_text(row.get("recovered_verbatim_se_text")):
        parts.append(f"se={safe_text(row.get('recovered_verbatim_se_text'))}")
    if safe_text(row.get("recovered_verbatim_n_text")):
        parts.append(f"N_text={safe_text(row.get('recovered_verbatim_n_text'))}")
    if safe_text(row.get("recovered_verbatim_p_or_z_text")):
        parts.append(f"p_or_z={safe_text(row.get('recovered_verbatim_p_or_z_text'))}")
    parts.extend(
        [
            f"plotted_D={safe_text(row.get('d'))}",
            f"plotted_N={safe_text(row.get('standardized_n'))}",
        ]
    )
    if safe_text(row.get("recovered_transformation_explanation")):
        parts.append(f"transform={safe_text(row.get('recovered_transformation_explanation'))}")
    source_path = safe_text(row.get("recovered_raw_file_repo_relative")) or safe_text(row.get("ultimate_source_path"))
    if source_path:
        parts.append(f"source_file={source_path}")
    return " | ".join(part for part in parts if part)


def main() -> None:
    pilot = read_table(str(SOURCE_RESULT_SAMPLE))
    dots = read_table(str(DOTS))
    retraced: list[dict[str, object]] = []
    events: list[dict[str, object]] = []
    problems: list[dict[str, object]] = []

    for row_number, (_, source_result) in enumerate(pilot.iterrows(), start=1):
        if row_number == 1 or row_number % 25 == 0:
            print(f"Retracing pilot row {row_number}/{len(pilot)}", flush=True)
        srid = safe_text(source_result["source_result_id"])
        original_line = int(float(source_result["original_dot_table_row"]))
        dot_index = original_line - 2
        dot = dots.iloc[dot_index].copy()
        add_event(events, srid, "recover_dot_membership_row", DOTS, "found", "original_dot_table_row - 2", f"dot_index={dot_index}")

        plot_row, plot_path, plot_kind = find_plot_row(source_result, dot, events, problems)
        if plot_row is None:
            add_problem(problems, srid, "cannot_continue_without_plot_row", "high", "No plot-level row was found from the stored dot identifier.")
            continue

        ultimate_path = path_from_locator(plot_row.get("source_file") if "source_file" in plot_row.index else dot.get("source_file_or_catalog"))
        if ultimate_path:
            ultimate_meta = file_metadata(ultimate_path)
            add_event(
                events,
                srid,
                "resolve_ultimate_source_locator",
                ultimate_path,
                "found" if ultimate_path.exists() else "missing",
                "first path in source_file/source_file_or_catalog",
                safe_text(plot_row.get("source_file") if "source_file" in plot_row.index else dot.get("source_file_or_catalog")),
            )
        else:
            add_problem(problems, srid, "ultimate_source_locator_missing", "medium", "No local source path could be parsed from the plot/source locator.")

        candidate_paper = None
        candidate_children = pd.DataFrame()
        ctgov_raw = pd.DataFrame()
        replication_pair = None
        staged_replication_pair = None
        strict_polisci = pd.DataFrame()

        if ultimate_path and ultimate_path.name == "candidate_d_n_papers.csv":
            candidate_paper, candidate_children = match_candidate_paper(dot, plot_row, events, problems, srid)
        elif plot_kind == "plot2":
            candidate_paper, candidate_children = match_candidate_paper(dot, plot_row, events, problems, srid)
        elif ultimate_path and ultimate_path.name == "efficacy_df.csv":
            ctgov_raw = match_ctgov_raw(dot, events, srid)
        elif ultimate_path and ultimate_path.name == "replication_pairs_all_on_hand.csv":
            replication_pair = match_replication_pair(dot, events, srid)
        elif ultimate_path and ultimate_path.name == "plot1_replication_pair_details.csv":
            replication_pair = match_replication_pair(dot, events, srid)
        elif ultimate_path and ultimate_path.name.endswith("__stage.csv"):
            staged_replication_pair = match_staged_replication_pair(ultimate_path, dot, events, srid)

        if "political_science_unlock" in safe_text(dot.get("source_file_or_catalog")) or "source_row_number" in dot.index and ";" in safe_text(dot.get("source_row_number")):
            strict_polisci = match_strict_polisci(dot, events, srid)

        source_directness = "plot_row_only"
        if not candidate_children.empty:
            source_directness = "candidate_child_numeric_row"
        elif candidate_paper is not None:
            source_directness = "candidate_paper_numeric_row"
        if not ctgov_raw.empty:
            source_directness = "raw_ctgov_registry_row"
        if replication_pair is not None:
            source_directness = "replication_pair_source_row"
        if staged_replication_pair is not None:
            source_directness = "staged_replication_pair_source_row"
        if not strict_polisci.empty:
            source_directness = "political_science_component_rows"

        verbatim_effect = ""
        verbatim_n = safe_text(dot.get("N"))
        verbatim_p = ""
        verbatim_se = ""
        raw_file = ""
        transformation = safe_text(source_result.get("transformation_explanation"))
        source_row_json = json_row(plot_row)
        upstream_row_json = ""

        if not candidate_children.empty:
            child = candidate_children.iloc[0]
            verbatim_effect = safe_text(child.get("effect")) or safe_text(child.get("D"))
            verbatim_se = safe_text(child.get("se"))
            verbatim_n = safe_text(child.get("N"))
            verbatim_p = safe_text(child.get("z"))
            raw_file = safe_text(child.get("raw_file"))
            transformation = f"{safe_text(child.get('D_method'))}; N: {safe_text(child.get('N_method'))}"
            upstream_row_json = json_row(child)
        elif candidate_paper is not None:
            verbatim_effect = safe_text(candidate_paper.get("D_median"))
            verbatim_n = safe_text(candidate_paper.get("N_median"))
            verbatim_p = safe_text(candidate_paper.get("abs_z_median"))
            raw_file = rel(CANDIDATE_PAPERS)
            transformation = f"paper-level candidate row; D: {safe_text(candidate_paper.get('D_methods'))}; N: {safe_text(candidate_paper.get('N_methods'))}; n_rows={safe_text(candidate_paper.get('n_rows'))}"
            upstream_row_json = json_row(candidate_paper)
        elif not ctgov_raw.empty:
            raw = ctgov_raw.iloc[0]
            verbatim_effect = safe_text(raw.get("param_value")) or safe_text(raw.get("ci_lower_limit")) or safe_text(raw.get("p_value"))
            verbatim_n = safe_text(raw.get("enrollment_num"))
            verbatim_p = safe_text(raw.get("p_value"))
            raw_file = rel(ROOT / "data/raw/corpus_candidates/ctgov_kg/efficacy_df.csv")
            transformation = "registry p-value/enrollment to D proxy; raw row recovered with NCT_ID/outcome_title"
            upstream_row_json = json_row(raw)
        elif replication_pair is not None:
            side = safe_text(dot.get("side")) or safe_text(plot_row.get("__plot1_side"))
            if side in {"original", "replication", "followup"}:
                if side == "original":
                    verbatim_effect = safe_text(replication_pair.get("D_original"))
                    verbatim_n = safe_text(replication_pair.get("N_original"))
                else:
                    verbatim_effect = safe_text(replication_pair.get("D_replication"))
                    verbatim_n = safe_text(replication_pair.get("N_replication"))
            raw_file = safe_text(replication_pair.get("raw_file"))
            transformation = "replication-pair D/N imported from integrated replication pair source row"
            upstream_row_json = json_row(replication_pair)
        elif staged_replication_pair is not None:
            side = safe_text(dot.get("side")) or safe_text(plot_row.get("__plot1_side"))
            if not side and "::" in safe_text(dot.get("dot_record_id")):
                side = safe_text(dot.get("dot_record_id")).rsplit("::", 1)[-1]
            if side == "original":
                verbatim_effect = safe_text(staged_replication_pair.get("D_original"))
                verbatim_n = safe_text(staged_replication_pair.get("N_original"))
            elif side in {"replication", "followup"}:
                verbatim_effect = safe_text(staged_replication_pair.get("D_replication"))
                verbatim_n = safe_text(staged_replication_pair.get("N_replication"))
            raw_file = safe_text(staged_replication_pair.get("raw_file"))
            transformation = safe_text(staged_replication_pair.get("analytic_status")) or "staged replication-pair D/N imported from staged source row"
            upstream_row_json = json_row(staged_replication_pair)
        elif not strict_polisci.empty:
            raw = strict_polisci.iloc[0]
            for field in ["D_signed", "D", "native_coefficient", "table4_adjusted_ate", "raw_risk_difference"]:
                if safe_text(raw.get(field)):
                    verbatim_effect = safe_text(raw.get(field))
                    break
            for field in ["N", "table4_adjusted_n", "study_total_respondents", "treatment_n"]:
                if safe_text(raw.get(field)):
                    verbatim_n = safe_text(raw.get(field))
                    break
            for field in ["SE", "table4_adjusted_se", "native_se_pp"]:
                if safe_text(raw.get(field)):
                    verbatim_se = safe_text(raw.get(field))
                    break
            verbatim_p = safe_text(raw.get("p")) or safe_text(raw.get("native_p")) or safe_text(raw.get("table4_adjusted_p"))
            raw_file = safe_text(raw.get("source_file"))
            transformation = safe_text(raw.get("conversion")) or "political-science strict rescue component row(s); possible paper median if multiple"
            upstream_row_json = json_row(raw)

        # Raw file existence for second-hop breadcrumbs.
        raw_path_exists = ""
        raw_path_repo_relative = ""
        raw_path_size = ""
        raw_path_sha256 = ""
        if raw_file:
            raw_path = path_from_locator(raw_file) or Path(raw_file)
            if not raw_path.is_absolute():
                raw_path = ROOT / raw_path
            raw_path_exists = str(raw_path.exists())
            raw_path_repo_relative = rel(raw_path)
            raw_meta = file_metadata(raw_path)
            raw_path_size = safe_text(raw_meta["file_size_bytes"])
            raw_path_sha256 = safe_text(raw_meta["file_sha256"])
            add_event(events, srid, "resolve_second_hop_raw_file", raw_path, "found" if raw_path.exists() else "missing", "raw_file field from recovered upstream row", raw_file)

        if not verbatim_effect:
            add_problem(problems, srid, "missing_verbatim_effect_text", "high", "Retrace found plot/source rows but no upstream effect/statistic cell.")
        if not verbatim_n:
            add_problem(problems, srid, "missing_verbatim_n_text", "high", "Retrace found plot/source rows but no upstream N/sample-size cell.")
        if source_directness in {"plot_row_only", "candidate_child_numeric_row", "candidate_paper_numeric_row", "replication_pair_source_row", "staged_replication_pair_source_row"}:
            add_problem(problems, srid, "source_is_derived_not_original_text", "medium", f"Best recovered source row is {source_directness}; this is not guaranteed to be original paper/database text.")
        if raw_file and raw_path_exists == "False":
            add_problem(problems, srid, "missing_source_locator", "medium", f"Recovered raw_file path does not exist: {raw_file}")

        row_out = {
            "source_result_id": srid,
            "plot_name": dot.get("plot_name"),
            "dot_record_id": dot.get("dot_record_id"),
            "result_label": source_result.get("result_label") or dot.get("paper_title"),
            "outcome_label": source_result.get("outcome_label") or dot.get("paper_title"),
            "paper_title": dot.get("paper_title"),
            "source_family": dot.get("source_family"),
            "source_locator": dot.get("source_file_or_catalog"),
            "d": dot.get("D"),
            "standardized_n": dot.get("N"),
            "plot_row_path": rel(plot_path) if plot_path else "",
            "plot_row_found": True,
            "ultimate_source_path": rel(ultimate_path) if ultimate_path else "",
            "ultimate_source_exists": bool(ultimate_path and ultimate_path.exists()),
            "ultimate_source_file_size_bytes": ultimate_meta["file_size_bytes"] if ultimate_path else "",
            "ultimate_source_file_sha256": ultimate_meta["file_sha256"] if ultimate_path else "",
            "source_directness": source_directness,
            "recovered_verbatim_effect_text": verbatim_effect,
            "recovered_verbatim_se_text": verbatim_se,
            "recovered_verbatim_n_text": verbatim_n,
            "recovered_verbatim_p_or_z_text": verbatim_p,
            "recovered_transformation_explanation": transformation,
            "recovered_raw_file": raw_file,
            "recovered_raw_file_repo_relative": raw_path_repo_relative,
            "recovered_raw_file_exists": raw_path_exists,
            "recovered_raw_file_size_bytes": raw_path_size,
            "recovered_raw_file_sha256": raw_path_sha256,
            "candidate_child_rows_matched": len(candidate_children),
            "candidate_paper_rows_matched": 1 if candidate_paper is not None else 0,
            "ctgov_raw_rows_matched": len(ctgov_raw),
            "staged_replication_pair_rows_matched": 1 if staged_replication_pair is not None else 0,
            "strict_polisci_rows_matched": len(strict_polisci),
            "upstream_row_json": upstream_row_json,
            "plot_row_json": source_row_json,
        }
        row_out.update(selected_candidate_child_fields(candidate_children))
        retraced.append(row_out)

    retraced_df = pd.DataFrame(retraced)
    if not retraced_df.empty:
        retraced_df["source_text_extraction_status"] = retraced_df.apply(source_text_status, axis=1)
        retraced_df["human_check_text"] = retraced_df.apply(human_check_text, axis=1)
    problems_df = pd.DataFrame(problems)
    events_df = pd.DataFrame(events)

    summary_rows = [
        {"metric": "sample_n", "value": len(retraced_df)},
        {"metric": "plot_rows_recovered", "value": int(retraced_df["plot_row_found"].sum())},
        {"metric": "ultimate_source_paths_existing", "value": int(retraced_df["ultimate_source_exists"].sum())},
        {"metric": "rows_with_recovered_effect_text", "value": int(retraced_df["recovered_verbatim_effect_text"].map(bool).sum())},
        {"metric": "rows_with_recovered_n_text", "value": int(retraced_df["recovered_verbatim_n_text"].map(bool).sum())},
        {"metric": "rows_with_second_hop_raw_file", "value": int(retraced_df["recovered_raw_file"].map(bool).sum())},
        {"metric": "rows_with_existing_second_hop_raw_file", "value": int(retraced_df["recovered_raw_file_exists"].eq("True").sum())},
    ]
    for status, count in retraced_df["source_directness"].value_counts().sort_index().items():
        summary_rows.append({"metric": f"source_directness::{status}", "value": int(count)})
    for status, count in retraced_df["source_text_extraction_status"].value_counts().sort_index().items():
        summary_rows.append({"metric": f"source_text_extraction_status::{status}", "value": int(count)})
    if not problems_df.empty:
        for code, count in problems_df["problem_code"].value_counts().sort_index().items():
            summary_rows.append({"metric": f"problem::{code}", "value": int(count)})
        for severity, count in problems_df["severity"].value_counts().sort_index().items():
            summary_rows.append({"metric": f"severity::{severity}", "value": int(count)})

    human_check_columns = [
        "source_result_id",
        "plot_name",
        "dot_record_id",
        "result_label",
        "outcome_label",
        "source_family",
        "source_directness",
        "source_text_extraction_status",
        "human_check_text",
        "recovered_verbatim_effect_text",
        "recovered_verbatim_se_text",
        "recovered_verbatim_n_text",
        "recovered_verbatim_p_or_z_text",
        "d",
        "standardized_n",
        "recovered_transformation_explanation",
        "ultimate_source_path",
        "ultimate_source_file_sha256",
        "recovered_raw_file_repo_relative",
        "recovered_raw_file_sha256",
        "source_locator",
        "upstream_row_json",
        "plot_row_json",
    ]
    human_check = retraced_df[[column for column in human_check_columns if column in retraced_df.columns]].copy()

    one_line_frame(retraced_df).to_csv(OUT_RETRACE, sep="\t", index=False)
    one_line_frame(human_check).to_csv(OUT_HUMAN_CHECK, sep="\t", index=False)
    one_line_frame(events_df).to_csv(OUT_EVENTS, sep="\t", index=False)
    one_line_frame(problems_df).to_csv(OUT_PROBLEMS, sep="\t", index=False)
    one_line_frame(pd.DataFrame(summary_rows)).to_csv(OUT_SUMMARY, sep="\t", index=False)

    print(f"Wrote retrace outputs to {PILOT.relative_to(ROOT)}")
    print(pd.DataFrame(summary_rows).to_string(index=False))


if __name__ == "__main__":
    main()
