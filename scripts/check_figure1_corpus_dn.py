#!/usr/bin/env python3
"""Build a proposal-only Figure 1 D/N check over locally mirrored corpora.

This stage is deliberately not a source_result promotion.  It records which
local corpus/project extractors currently yield D and N for both original and
replication results, and it emits stricter verbatim-backed side rows for the
corpora whose mirrored native rows can be checked directly here.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import re
import warnings
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "steps" / "corpus_results" / "figure1" / "dn_check"
CORPUS_RESULTS = ROOT / "steps" / "corpus_results" / "figure1" / "corpus-results-proposal.tsv"
ML2_DIR = ROOT / "data" / "raw" / "replication_projects" / "ml2"
PLOT1_PAIR_DETAILS = ROOT / "data" / "derived" / "effect_inflation_dataset" / "plot1_replication_pair_details.csv"

PAIR_OUTPUT = OUT_DIR / "figure1-corpus-dn-check-pairs.tsv"
STRICT_SIDE_OUTPUT = OUT_DIR / "figure1-corpus-dn-check-strict-result-sides.tsv"
PROJECT_SUMMARY_OUTPUT = OUT_DIR / "figure1-corpus-dn-check-project-summary.tsv"
SUMMARY_OUTPUT = OUT_DIR / "figure1-corpus-dn-check-summary.tsv"
REPORT_OUTPUT = OUT_DIR / "figure1-corpus-dn-check.md"

NA_STRINGS = {"", "na", "n/a", "nan", "none", "null", "<na>"}


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def split_source_paths(path: Path | str | None) -> list[str]:
    if not path:
        return []
    return [part.strip() for part in str(path).split(";") if part.strip()]


def rel_one(path: Path | str | None) -> str:
    if not path:
        return ""
    p = Path(str(path).strip())
    try:
        return str(p.resolve().relative_to(ROOT))
    except Exception:
        return str(path)


def rel(path: Path | str | None) -> str:
    parts = split_source_paths(path)
    if len(parts) > 1:
        return " ; ".join(rel_one(part) for part in parts)
    return rel_one(path)


def clean_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and math.isnan(value):
        return ""
    text = str(value)
    if text.lower() in NA_STRINGS:
        return ""
    return re.sub(r"[\t\r\n]+", " ", text).strip()


def to_float(value: Any) -> float:
    text = clean_text(value)
    if not text:
        return np.nan
    try:
        return float(text)
    except ValueError:
        return np.nan


def is_finite(value: Any) -> bool:
    return bool(np.isfinite(to_float(value)))


def r_to_d(value: Any) -> float:
    r = to_float(value)
    if not np.isfinite(r) or abs(r) >= 1:
        return np.nan
    return abs(2 * r / math.sqrt(1 - r * r))


def stable_id(prefix: str, *parts: Any, size: int = 16) -> str:
    joined = "\x1f".join(clean_text(part) for part in parts)
    digest = hashlib.sha256(joined.encode("utf-8")).hexdigest()[:size]
    return f"{prefix}_{digest}"


def sha256_file(path_text: str) -> str:
    if not path_text:
        return ""
    parts = split_source_paths(path_text)
    if len(parts) > 1:
        digests = [sha256_file(part) for part in parts]
        return " ; ".join(digests) if any(digests) else ""
    path = Path(path_text)
    if not path.is_absolute():
        path = ROOT / path
    if not path.exists() or not path.is_file():
        return ""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def source_path_from_locator(locator: str) -> str:
    text = clean_text(locator)
    if "#row=" in text:
        text = text.split("#row=", 1)[0]
    return text


def load_pair_builder() -> Any:
    spec = importlib.util.spec_from_file_location(
        "analyze_replication_pairs", ROOT / "scripts" / "analyze_replication_pairs.py"
    )
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def append_current_plot_backfill(mod: Any, pairs: pd.DataFrame) -> pd.DataFrame:
    """Add legacy Appendix D rows needed to reproduce current Plot 1 details."""
    if not PLOT1_PAIR_DETAILS.exists():
        return pairs
    plot = pd.read_csv(PLOT1_PAIR_DETAILS, dtype=str, keep_default_na=False)
    base_keys = set(zip(pairs["project"].astype(str), pairs["source_dataset"].astype(str), pairs["pair_id"].astype(str)))
    missing_keys = set(zip(plot["project"].astype(str), plot["source_dataset"].astype(str), plot["pair_id"].astype(str))) - base_keys
    if not missing_keys:
        return pairs
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        appendix = mod.build_appendix_pairs()
    appendix_keys = list(zip(appendix["project"].astype(str), appendix["source_dataset"].astype(str), appendix["pair_id"].astype(str)))
    missing = appendix[[key in missing_keys for key in appendix_keys]].copy()
    if missing.empty:
        fallback = plot[[key in missing_keys for key in zip(plot["project"].astype(str), plot["source_dataset"].astype(str), plot["pair_id"].astype(str))]].copy()
        fallback["raw_file"] = rel(PLOT1_PAIR_DETAILS)
        fallback["match_author"] = fallback.get("original_title", "")
        fallback["match_key"] = fallback["project"].map(clean_text).str.lower() + "__" + fallback["pair_id"].map(clean_text).str.lower()
        fallback["component_rows"] = "1"
        missing = fallback
    for col in pairs.columns:
        if col not in missing.columns:
            missing[col] = ""
    return pd.concat([pairs, missing[pairs.columns]], ignore_index=True)


def build_numeric_pair_checks() -> pd.DataFrame:
    mod = load_pair_builder()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        pairs = mod.build_all_pairs()
    pairs = append_current_plot_backfill(mod, pairs)
    out = pairs.copy()
    for col in ["D_original", "D_replication", "N_original", "N_replication"]:
        out[col] = pd.to_numeric(out[col], errors="coerce")
    out["dn_pair_check_id"] = [
        stable_id("dn_pair", row.project, row.source_dataset, row.pair_id, row.outcome)
        for row in out.itertuples(index=False)
    ]
    out["dn_check_evidence_mode"] = np.where(
        out["source_dataset"].astype(str).eq("Appendix D supplemental"),
        "legacy_appendix_d_backfill",
        "legacy_project_specific_local_builder",
    )
    out["dn_check_status"] = "passed_numeric_dn_check"
    out["figure1_min_n_check"] = np.where(
        (out["N_original"] >= 10) & (out["N_replication"] >= 10),
        "passes_min_original_and_replication_n_10",
        "fails_min_original_or_replication_n_10",
    )
    out["figure1_larger_n_check"] = np.where(
        out["N_replication"] > out["N_original"],
        "passes_replication_n_larger_than_original",
        "fails_replication_n_not_larger_than_original",
    )
    out["figure1_rule_check"] = np.where(
        (out["N_original"] >= 10) & (out["N_replication"] >= 10) & (out["N_replication"] > out["N_original"]),
        "passes_d_n_min10_and_larger_n",
        "blocked_by_n_rule",
    )
    out["source_artifact_local_path"] = out["raw_file"].map(rel)
    sha_cache: dict[str, str] = {}
    out["source_artifact_sha256"] = [
        sha_cache.setdefault(path, sha256_file(path)) for path in out["source_artifact_local_path"].fillna("")
    ]
    out["d_n_transformation_note"] = np.where(
        out["dn_check_evidence_mode"].eq("legacy_appendix_d_backfill"),
        (
            "Numeric D/N values are carried from the legacy Appendix D supplemental backfill used by the current "
            "Plot 1 pair-detail table; source_result promotion still needs verbatim support rows."
        ),
        (
            "Numeric D/N values are produced by scripts/analyze_replication_pairs.py project-specific local builders. "
            "Use strict-result-side rows or later source_result_support rows for verbatim source text before final promotion."
        ),
    )

    keep = [
        "dn_pair_check_id",
        "dn_check_evidence_mode",
        "dn_check_status",
        "figure1_min_n_check",
        "figure1_larger_n_check",
        "figure1_rule_check",
        "project",
        "source_dataset",
        "pair_id",
        "original_title",
        "replication_title",
        "original_doi",
        "replication_doi",
        "outcome",
        "D_original",
        "N_original",
        "D_replication",
        "N_replication",
        "original_sig_05",
        "replication_sig_05",
        "larger_n_replication",
        "d_grew",
        "d_ratio",
        "n_ratio",
        "category",
        "source_artifact_local_path",
        "source_artifact_sha256",
        "match_author",
        "match_key",
        "component_rows",
        "d_n_transformation_note",
    ]
    for col in keep:
        if col not in out.columns:
            out[col] = ""
    return out[keep].copy()


def strict_side_row(
    *,
    mode: str,
    parent_key: str,
    project: str,
    source_dataset: str,
    pair_id: str,
    result_side: str,
    result_label: str,
    outcome: str,
    native_effect_value: Any,
    native_effect_metric: str,
    native_n_total: Any,
    d_value: float,
    d_conversion_method: str,
    d_conversion_inputs: str,
    verbatim_source_row_text: str,
    verbatim_effect_text: str,
    verbatim_n_text: str,
    source_locator: str,
    source_artifact_local_path: str,
    source_artifact_sha256: str,
    source_row_json: dict[str, Any],
    corpus_result_id: str = "",
) -> dict[str, Any]:
    n_value = to_float(native_n_total)
    effect_value = to_float(native_effect_value)
    status = "dn_checked_ready_for_mapping"
    blockers = []
    if not np.isfinite(d_value):
        blockers.append("missing_or_unconvertible_d")
    if not np.isfinite(n_value):
        blockers.append("missing_n")
    if blockers:
        status = "blocked_" + "_and_".join(blockers)
    return {
        "dn_result_check_id": stable_id("dn_result", parent_key, pair_id, result_side, source_locator),
        "dn_pair_check_id": stable_id("dn_pair", parent_key, pair_id, source_dataset),
        "dn_check_evidence_mode": mode,
        "primary_parent_corpus_database_id": parent_key,
        "project": project,
        "source_dataset": source_dataset,
        "pair_id": pair_id,
        "result_side": result_side,
        "result_label": result_label,
        "outcome_label": outcome,
        "corpus_result_id": corpus_result_id,
        "source_locator": source_locator,
        "source_artifact_local_path": source_artifact_local_path,
        "source_artifact_sha256": source_artifact_sha256,
        "verbatim_source_row_text": verbatim_source_row_text,
        "verbatim_effect_text": verbatim_effect_text,
        "verbatim_n_text": verbatim_n_text,
        "native_effect_value": effect_value if np.isfinite(effect_value) else "",
        "native_effect_metric": native_effect_metric,
        "native_n_total": n_value if np.isfinite(n_value) else "",
        "standardized_effect_metric": "D",
        "standardized_effect_value": d_value if np.isfinite(d_value) else "",
        "standardized_n": n_value if np.isfinite(n_value) else "",
        "d": d_value if np.isfinite(d_value) else "",
        "d_conversion_method": d_conversion_method,
        "d_conversion_inputs": d_conversion_inputs,
        "dn_check_status": status,
        "blocker_codes": ";".join(blockers),
        "transformation_explanation": (
            "D is the absolute standardized effect magnitude for Figure 1. "
            "The signed native value is preserved in native_effect_value and verbatim_effect_text."
        ),
        "source_row_json": json.dumps(source_row_json, sort_keys=True, ensure_ascii=False),
    }


def choose_reported_d(row: dict[str, Any], d_keys: list[str], r_keys: list[str]) -> tuple[float, str, str, str, Any]:
    for key in d_keys:
        value = row.get(key, "")
        numeric = to_float(value)
        if np.isfinite(numeric):
            return abs(float(numeric)), "reported_d", f"{key}={clean_text(value)}", "cohens_d", value
    for key in r_keys:
        value = row.get(key, "")
        converted = r_to_d(value)
        if np.isfinite(converted):
            return converted, "r_to_d", f"{key}={clean_text(value)}; D=2*r/sqrt(1-r^2)", "correlation_r", value
    return np.nan, "missing_or_unconvertible", "", "", ""


def build_rpcb_strict_sides() -> pd.DataFrame:
    if not CORPUS_RESULTS.exists():
        return pd.DataFrame()
    data = pd.read_csv(CORPUS_RESULTS, sep="\t", dtype=str, keep_default_na=False)
    rows = data[
        (data["primary_parent_corpus_database_id"] == "raw_corpus:rpcb")
        & data["source_artifact_file_names"].str.contains("Effect level", na=False)
    ].copy()

    out: list[dict[str, Any]] = []
    sha_cache: dict[str, str] = {}
    for source_row in rows.itertuples(index=False):
        row = json.loads(getattr(source_row, "corpus_native_row_json") or "{}")
        paper = clean_text(row.get("Paper #"))
        experiment = clean_text(row.get("Experiment #"))
        effect = clean_text(row.get("Effect #"))
        internal = clean_text(row.get("Internal replication #"))
        pair_id = f"rpcb_p{paper}_e{experiment}_effect{effect}_internal{internal}"
        outcome = clean_text(row.get("Effect description"))
        locator = clean_text(getattr(source_row, "source_locator"))
        local_path = rel(source_path_from_locator(locator))
        sha = sha_cache.setdefault(local_path, sha256_file(local_path))
        source_text = clean_text(getattr(source_row, "corpus_native_row_text"))

        orig_d, orig_method, orig_inputs, orig_metric, orig_native = choose_reported_d(
            row,
            ["Original effect size (SMD)"],
            [],
        )
        repl_d, repl_method, repl_inputs, repl_metric, repl_native = choose_reported_d(
            row,
            ["Replication effect size (SMD)"],
            [],
        )

        out.append(
            strict_side_row(
                mode="strict_verbatim_native_parser",
                parent_key="raw_corpus:rpcb",
                project="RPCB",
                source_dataset="RP_CB Final Analysis - Effect level data.csv",
                pair_id=pair_id,
                result_side="original",
                result_label=f"RPCB paper {paper} experiment {experiment} effect {effect} original",
                outcome=outcome,
                native_effect_value=orig_native,
                native_effect_metric=orig_metric or clean_text(row.get("Effect size type (SMD)") or row.get("Effect size type")),
                native_n_total=row.get("Original sample size", ""),
                d_value=orig_d,
                d_conversion_method=orig_method,
                d_conversion_inputs=orig_inputs,
                verbatim_source_row_text=source_text,
                verbatim_effect_text=(
                    f"Effect size type (SMD)={clean_text(row.get('Effect size type (SMD)'))}; "
                    f"Original effect size (SMD)={clean_text(row.get('Original effect size (SMD)'))}"
                ),
                verbatim_n_text=f"Original sample size={clean_text(row.get('Original sample size'))}",
                source_locator=locator,
                source_artifact_local_path=local_path,
                source_artifact_sha256=sha,
                source_row_json=row,
                corpus_result_id=clean_text(getattr(source_row, "corpus_result_id")),
            )
        )
        out.append(
            strict_side_row(
                mode="strict_verbatim_native_parser",
                parent_key="raw_corpus:rpcb",
                project="RPCB",
                source_dataset="RP_CB Final Analysis - Effect level data.csv",
                pair_id=pair_id,
                result_side="replication",
                result_label=f"RPCB paper {paper} experiment {experiment} effect {effect} replication",
                outcome=outcome,
                native_effect_value=repl_native,
                native_effect_metric=repl_metric or clean_text(row.get("Effect size type (SMD)") or row.get("Effect size type")),
                native_n_total=row.get("Replication sample size", ""),
                d_value=repl_d,
                d_conversion_method=repl_method,
                d_conversion_inputs=repl_inputs,
                verbatim_source_row_text=source_text,
                verbatim_effect_text=(
                    f"Effect size type (SMD)={clean_text(row.get('Effect size type (SMD)'))}; "
                    f"Replication effect size (SMD)={clean_text(row.get('Replication effect size (SMD)'))}"
                ),
                verbatim_n_text=f"Replication sample size={clean_text(row.get('Replication sample size'))}",
                source_locator=locator,
                source_artifact_local_path=local_path,
                source_artifact_sha256=sha,
                source_row_json=row,
                corpus_result_id=clean_text(getattr(source_row, "corpus_result_id")),
            )
        )
    return pd.DataFrame(out)


def build_ml2_strict_sides() -> pd.DataFrame:
    table_path = ML2_DIR / "table5data_RM.csv"
    orig_path = ML2_DIR / "ML2_OriginalEffects.csv"
    fig_path = ML2_DIR / "Data_Figure_NOweird_oriEffects.csv"
    if not (table_path.exists() and orig_path.exists() and fig_path.exists()):
        return pd.DataFrame()

    table = pd.read_csv(table_path, dtype=str, keep_default_na=False)
    orig = pd.read_csv(orig_path, dtype=str, keep_default_na=False)
    fig = pd.read_csv(fig_path, dtype=str, keep_default_na=False)
    table["_table_row_number"] = np.arange(1, len(table) + 1)
    orig["_orig_row_number"] = np.arange(1, len(orig) + 1)
    fig["_fig_row_number"] = np.arange(1, len(fig) + 1)

    merged = table.merge(
        orig[["_orig_row_number", "study.analysis", "N", "ESCI.d", "ESCI.r", "testInfo.p.value"]],
        left_on="ori_ML2analysis",
        right_on="study.analysis",
        how="left",
    )
    merged = merged.merge(
        fig[["_fig_row_number", "study.analysis", "usethisES"]].rename(
            columns={"study.analysis": "study.analysis.fig"}
        ),
        left_on="ori_ML2analysis",
        right_on="study.analysis.fig",
        how="left",
    )

    table_sha = sha256_file(rel(table_path))
    orig_sha = sha256_file(rel(orig_path))
    fig_sha = sha256_file(rel(fig_path))
    out: list[dict[str, Any]] = []
    for row in merged.to_dict(orient="records"):
        analysis = clean_text(row.get("analysis"))
        orig_analysis = clean_text(row.get("ori_ML2analysis"))
        pair_id = f"ml2_{analysis}"
        outcome = analysis
        row_json = {k: clean_text(v) for k, v in row.items()}
        table_locator = f"{rel(table_path)}#row={clean_text(row.get('_table_row_number'))}"
        orig_locator = f"{rel(orig_path)}#row={clean_text(row.get('_orig_row_number'))}"
        fig_locator = f"{rel(fig_path)}#row={clean_text(row.get('_fig_row_number'))}"

        orig_d, orig_method, orig_inputs, orig_metric, orig_native = choose_reported_d(
            row,
            ["ESCI.d"],
            ["ESCI.r", "usethisES"],
        )
        repl_d, repl_method, repl_inputs, repl_metric, repl_native = choose_reported_d(
            row,
            ["ML2_d"],
            ["ML2_r"],
        )

        original_source_text = (
            f"table5data_RM row {clean_text(row.get('_table_row_number'))}: study={clean_text(row.get('study'))}; "
            f"analysis={analysis}; ori_ML2analysis={orig_analysis}; ori_N={clean_text(row.get('ori_N'))}; "
            f"joined ML2_OriginalEffects row {clean_text(row.get('_orig_row_number'))}: "
            f"N={clean_text(row.get('N'))}; ESCI.d={clean_text(row.get('ESCI.d'))}; "
            f"ESCI.r={clean_text(row.get('ESCI.r'))}; usethisES={clean_text(row.get('usethisES'))}"
        )
        replication_source_text = (
            f"table5data_RM row {clean_text(row.get('_table_row_number'))}: study={clean_text(row.get('study'))}; "
            f"analysis={analysis}; ML2_N={clean_text(row.get('ML2_N'))}; "
            f"ML2_d={clean_text(row.get('ML2_d'))}; ML2_r={clean_text(row.get('ML2_r'))}; "
            f"ML2_pval={clean_text(row.get('ML2_pval'))}"
        )

        out.append(
            strict_side_row(
                mode="strict_verbatim_custom_local_join",
                parent_key="many_labs_2 | doi:10.1177/2515245918810225",
                project="Many Labs 2",
                source_dataset="Many Labs 2 public join",
                pair_id=pair_id,
                result_side="original",
                result_label=f"Many Labs 2 target {orig_analysis} original",
                outcome=outcome,
                native_effect_value=orig_native,
                native_effect_metric=orig_metric,
                native_n_total=row.get("N", ""),
                d_value=orig_d,
                d_conversion_method=orig_method,
                d_conversion_inputs=orig_inputs,
                verbatim_source_row_text=original_source_text,
                verbatim_effect_text=(
                    f"ESCI.d={clean_text(row.get('ESCI.d'))}; ESCI.r={clean_text(row.get('ESCI.r'))}; "
                    f"usethisES={clean_text(row.get('usethisES'))}"
                ),
                verbatim_n_text=f"N={clean_text(row.get('N'))}",
                source_locator=f"{table_locator}; join {orig_locator}; fallback {fig_locator}",
                source_artifact_local_path=rel(table_path),
                source_artifact_sha256=f"{table_sha};{orig_sha};{fig_sha}",
                source_row_json=row_json,
            )
        )
        out.append(
            strict_side_row(
                mode="strict_verbatim_custom_local_join",
                parent_key="many_labs_2 | doi:10.1177/2515245918810225",
                project="Many Labs 2",
                source_dataset="Many Labs 2 public join",
                pair_id=pair_id,
                result_side="replication",
                result_label=f"Many Labs 2 target {analysis} replication",
                outcome=outcome,
                native_effect_value=repl_native,
                native_effect_metric=repl_metric,
                native_n_total=row.get("ML2_N", ""),
                d_value=repl_d,
                d_conversion_method=repl_method,
                d_conversion_inputs=repl_inputs,
                verbatim_source_row_text=replication_source_text,
                verbatim_effect_text=f"ML2_d={clean_text(row.get('ML2_d'))}; ML2_r={clean_text(row.get('ML2_r'))}",
                verbatim_n_text=f"ML2_N={clean_text(row.get('ML2_N'))}",
                source_locator=table_locator,
                source_artifact_local_path=rel(table_path),
                source_artifact_sha256=table_sha,
                source_row_json=row_json,
            )
        )
    return pd.DataFrame(out)


def strict_pair_summary(strict_sides: pd.DataFrame) -> pd.DataFrame:
    if strict_sides.empty:
        return pd.DataFrame(columns=["project", "strict_verbatim_pair_rows", "strict_verbatim_rule_pair_rows"])
    ready = strict_sides[strict_sides["dn_check_status"] == "dn_checked_ready_for_mapping"].copy()
    if ready.empty:
        return pd.DataFrame(columns=["project", "strict_verbatim_pair_rows", "strict_verbatim_rule_pair_rows"])
    pivot = ready.pivot_table(
        index=["project", "pair_id"],
        columns="result_side",
        values=["d", "standardized_n"],
        aggfunc="first",
    )
    rows = []
    for (project, pair_id), vals in pivot.iterrows():
        try:
            d_original = to_float(vals[("d", "original")])
            d_replication = to_float(vals[("d", "replication")])
            n_original = to_float(vals[("standardized_n", "original")])
            n_replication = to_float(vals[("standardized_n", "replication")])
        except Exception:
            continue
        if all(np.isfinite(x) for x in [d_original, d_replication, n_original, n_replication]):
            rows.append(
                {
                    "project": project,
                    "pair_id": pair_id,
                    "strict_verbatim_pair_ready": True,
                    "strict_verbatim_rule_ready": bool(
                        n_original >= 10 and n_replication >= 10 and n_replication > n_original
                    ),
                }
            )
    if not rows:
        return pd.DataFrame(columns=["project", "strict_verbatim_pair_rows", "strict_verbatim_rule_pair_rows"])
    pairs = pd.DataFrame(rows)
    return (
        pairs.groupby("project")
        .agg(
            strict_verbatim_pair_rows=("strict_verbatim_pair_ready", "sum"),
            strict_verbatim_rule_pair_rows=("strict_verbatim_rule_ready", "sum"),
        )
        .reset_index()
    )


def build_project_summary(pairs: pd.DataFrame, strict_sides: pd.DataFrame) -> pd.DataFrame:
    summary = (
        pairs.groupby("project")
        .agg(
            numeric_dn_pair_rows=("dn_pair_check_id", "size"),
            figure1_rule_pair_rows=("figure1_rule_check", lambda s: int((s == "passes_d_n_min10_and_larger_n").sum())),
            source_dataset_count=("source_dataset", "nunique"),
            source_file_count=("source_artifact_local_path", lambda s: int(pd.Series(s).replace("", np.nan).nunique())),
        )
        .reset_index()
    )
    strict = strict_pair_summary(strict_sides)
    if not strict.empty:
        summary = summary.merge(strict, on="project", how="left")
    else:
        summary["strict_verbatim_pair_rows"] = 0
        summary["strict_verbatim_rule_pair_rows"] = 0
    for col in ["strict_verbatim_pair_rows", "strict_verbatim_rule_pair_rows"]:
        summary[col] = pd.to_numeric(summary[col], errors="coerce").fillna(0).astype(int)
    summary["dn_check_stage_status"] = np.where(
        summary["strict_verbatim_pair_rows"] > 0,
        "strict_verbatim_dn_checked",
        "numeric_dn_checked_provenance_hardening_needed",
    )
    return summary.sort_values(["strict_verbatim_pair_rows", "numeric_dn_pair_rows"], ascending=[False, False])


def metric_rows(pairs: pd.DataFrame, strict_sides: pd.DataFrame, project_summary: pd.DataFrame) -> pd.DataFrame:
    strict_projects = int((project_summary["strict_verbatim_pair_rows"] > 0).sum()) if not project_summary.empty else 0
    strict_pairs = int(project_summary["strict_verbatim_pair_rows"].sum()) if not project_summary.empty else 0
    strict_rule_pairs = int(project_summary["strict_verbatim_rule_pair_rows"].sum()) if not project_summary.empty else 0
    return pd.DataFrame(
        [
            {
                "metric": "local_project_labels_with_numeric_dn_pairs",
                "value": int(pairs["project"].nunique()),
                "definition": "Distinct project labels from existing local project-specific builders with finite original and replication D/N.",
            },
            {
                "metric": "numeric_dn_pair_rows",
                "value": len(pairs),
                "definition": "Original/replication pair rows with numeric D_original, N_original, D_replication, and N_replication.",
            },
            {
                "metric": "numeric_dn_pairs_passing_min10_and_larger_n",
                "value": int((pairs["figure1_rule_check"] == "passes_d_n_min10_and_larger_n").sum()),
                "definition": "Numeric D/N pair rows where original N and replication N are at least 10 and replication N is larger.",
            },
            {
                "metric": "strict_verbatim_project_labels",
                "value": strict_projects,
                "definition": "Project labels with D/N rows backed by copied native row text in this stage.",
            },
            {
                "metric": "strict_verbatim_pair_rows",
                "value": strict_pairs,
                "definition": "Pairs with original and replication D/N both ready and backed by copied native row text in this stage.",
            },
            {
                "metric": "strict_verbatim_pairs_passing_min10_and_larger_n",
                "value": strict_rule_pairs,
                "definition": "Strict verbatim-backed pairs also passing the current Figure 1 N rule check.",
            },
            {
                "metric": "strict_verbatim_result_side_rows",
                "value": len(strict_sides),
                "definition": "Original-side plus replication-side rows with copied effect/N text where currently available.",
            },
        ]
    )


def write_report(metrics: pd.DataFrame, project_summary: pd.DataFrame) -> None:
    values = {row.metric: row.value for row in metrics.itertuples(index=False)}
    lines = [
        "# Figure 1 Corpus D/N Check",
        "",
        "Definitions:",
        "",
        "- D is the standardized effect-size magnitude used on the Figure 1 axis. Signed native effect text is preserved where this stage has verbatim rows.",
        "- N is the sample size attached to that original or replication effect.",
        "- Numeric D/N checked means a local project-specific extractor produced finite original and replication D/N values.",
        "- Strict verbatim D/N checked means this stage also copied the native row text containing the effect and N values.",
        "",
        f"- Local project labels with numeric D/N pairs: **{values.get('local_project_labels_with_numeric_dn_pairs', 0):,}**",
        f"- Numeric D/N pair rows: **{values.get('numeric_dn_pair_rows', 0):,}**",
        f"- Numeric pairs passing min-10 and larger-replication-N checks: **{values.get('numeric_dn_pairs_passing_min10_and_larger_n', 0):,}**",
        f"- Strict verbatim project labels: **{values.get('strict_verbatim_project_labels', 0):,}**",
        f"- Strict verbatim pair rows: **{values.get('strict_verbatim_pair_rows', 0):,}**",
        f"- Strict verbatim pairs passing min-10 and larger-replication-N checks: **{values.get('strict_verbatim_pairs_passing_min10_and_larger_n', 0):,}**",
        "",
        "## Project Summary",
        "",
        "| Project | Numeric D/N pairs | Rule-pass pairs | Strict verbatim pairs | Strict rule-pass pairs | Status |",
        "|---|---:|---:|---:|---:|---|",
    ]
    for row in project_summary.itertuples(index=False):
        lines.append(
            f"| {clean_text(row.project)} | {int(row.numeric_dn_pair_rows):,} | "
            f"{int(row.figure1_rule_pair_rows):,} | {int(row.strict_verbatim_pair_rows):,} | "
            f"{int(row.strict_verbatim_rule_pair_rows):,} | {clean_text(row.dn_check_stage_status)} |"
        )
    REPORT_OUTPUT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def normalize_for_tsv(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for col in out.columns:
        if out[col].dtype == object:
            out[col] = out[col].map(clean_text)
    return out


def run(*, replace: bool) -> None:
    ensure_dir(OUT_DIR)
    outputs = [PAIR_OUTPUT, STRICT_SIDE_OUTPUT, PROJECT_SUMMARY_OUTPUT, SUMMARY_OUTPUT, REPORT_OUTPUT]
    if not replace:
        existing = [path for path in outputs if path.exists()]
        if existing:
            names = ", ".join(str(path) for path in existing)
            raise SystemExit(f"Refusing to overwrite existing outputs without --replace: {names}")

    pairs = build_numeric_pair_checks()
    strict_sides = pd.concat([build_rpcb_strict_sides(), build_ml2_strict_sides()], ignore_index=True)
    project_summary = build_project_summary(pairs, strict_sides)
    metrics = metric_rows(pairs, strict_sides, project_summary)

    normalize_for_tsv(pairs).to_csv(PAIR_OUTPUT, sep="\t", index=False)
    normalize_for_tsv(strict_sides).to_csv(STRICT_SIDE_OUTPUT, sep="\t", index=False)
    normalize_for_tsv(project_summary).to_csv(PROJECT_SUMMARY_OUTPUT, sep="\t", index=False)
    normalize_for_tsv(metrics).to_csv(SUMMARY_OUTPUT, sep="\t", index=False)
    write_report(metrics, project_summary)

    print(f"Wrote numeric D/N pairs: {PAIR_OUTPUT}")
    print(f"Wrote strict D/N side rows: {STRICT_SIDE_OUTPUT}")
    print(f"Wrote project summary: {PROJECT_SUMMARY_OUTPUT}")
    print(f"Wrote report: {REPORT_OUTPUT}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--replace", action="store_true", help="Overwrite existing outputs.")
    args = parser.parse_args()
    run(replace=args.replace)


if __name__ == "__main__":
    main()
