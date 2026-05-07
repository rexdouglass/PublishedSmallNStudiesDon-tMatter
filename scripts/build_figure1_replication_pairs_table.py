#!/usr/bin/env python3
"""Build the root Figure 1 replication-pair result table.

This root table is the pair-level bridge between corpus discovery/D-N checks
and the long-form provenance schema.  It is intentionally obvious and flat:
one row per original/replication pair, with both sides' D/N values, current
Figure 1 rule status, and enough source pointers to promote into source_result
and source_result_support later.
"""

from __future__ import annotations

import argparse
import hashlib
import math
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import yaml


ROOT = Path(__file__).resolve().parents[1]
DN_DIR = ROOT / "steps" / "corpus_results" / "figure1" / "dn_check"
DN_PAIRS = DN_DIR / "figure1-corpus-dn-check-pairs.tsv"
DN_STRICT_SIDES = DN_DIR / "figure1-corpus-dn-check-strict-result-sides.tsv"
OUT_TSV = ROOT / "FIGURE1_REPLICATION_PAIRS.tsv"
OUT_SCHEMA = ROOT / "FIGURE1_REPLICATION_PAIRS_SCHEMA.yml"
OUT_SUMMARY = ROOT / "steps" / "corpus_results" / "figure1" / "result_table" / "figure1-replication-pairs-summary.md"


COLUMNS = [
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
    "strict_verbatim_status",
    "source_result_promotion_status",
    "original_title",
    "replication_title",
    "original_doi",
    "replication_doi",
    "outcome_label",
    "D_original",
    "N_original",
    "D_replication",
    "N_replication",
    "D_smaller_N",
    "N_smaller_N",
    "D_larger_N",
    "N_larger_N",
    "smaller_N_role",
    "larger_N_role",
    "D_larger_N_minus_smaller_N",
    "original_sig_05",
    "replication_sig_05",
    "larger_n_replication",
    "d_grew",
    "d_ratio",
    "n_ratio",
    "category",
    "source_artifact_local_path",
    "source_artifact_sha256",
    "source_artifact_access_status",
    "dn_check_pairs_path",
    "dn_check_strict_sides_path",
    "strict_original_result_check_id",
    "strict_replication_result_check_id",
    "value_verification_state",
    "target_acquisition_state",
    "notes",
    "created_by",
    "created_at",
]


SCHEMA = {
    "purpose": (
        "Root-level Figure 1 replication-pair result table. This is the obvious "
        "flat staging table after corpus D/N checks and before promotion into "
        "source_result/source_result_support/canonical_result rows."
    ),
    "table": "FIGURE1_REPLICATION_PAIRS.tsv",
    "grain": "One original/replication result pair exposed by a local corpus, database, source-family table, or project-specific extractor.",
    "rule": (
        "Keep every pair that has finite original D, original N, replication D, "
        "and replication N. Current plot inclusion/exclusion is recorded in "
        "status columns rather than deleting rows."
    ),
    "columns": [
        {"name": "figure1_replication_pair_id", "definition": "Stable ID for this root pair row."},
        {"name": "dn_pair_check_id", "definition": "Upstream D/N check pair ID from steps/corpus_results/figure1/dn_check."},
        {"name": "plot_universe_id", "definition": "Plot universe this pair table currently supports; fixed to plot1_replication_pairs."},
        {"name": "source_family_key", "definition": "Normalized key for the source family/project label."},
        {"name": "source_family_label", "definition": "Human-readable source family/project label."},
        {"name": "project", "definition": "Project label emitted by the local pair extractor."},
        {"name": "source_dataset", "definition": "Dataset/table/package label emitted by the local pair extractor."},
        {"name": "native_pair_id", "definition": "Pair ID in the upstream local extractor."},
        {"name": "pair_result_status", "definition": "Whether the row has numeric D/N for both original and replication sides."},
        {"name": "current_plot_rule_status", "definition": "Current Figure 1 D/N inclusion status using the active N gates."},
        {"name": "current_plot_rule_blockers", "definition": "Pipe-delimited current rule blockers, such as blocked_N_lt_10 or blocked_replication_N_le_original_N."},
        {"name": "strict_verbatim_status", "definition": "Whether this exact pair is aligned to verbatim result-side rows, has only project-level strict coverage, or remains numeric-only."},
        {"name": "source_result_promotion_status", "definition": "Next provenance action before this row can become source_result/source_result_support rows."},
        {"name": "original_title", "definition": "Original/earlier or smaller-sample result title or label."},
        {"name": "replication_title", "definition": "Replication/follow-up or larger-sample result title or label."},
        {"name": "original_doi", "definition": "Original result DOI when known."},
        {"name": "replication_doi", "definition": "Replication/follow-up result DOI when known."},
        {"name": "outcome_label", "definition": "Outcome, test, claim, or contrast label."},
        {"name": "D_original", "definition": "Standardized effect-size magnitude for the original side."},
        {"name": "N_original", "definition": "Sample size for the original side."},
        {"name": "D_replication", "definition": "Standardized effect-size magnitude for the replication/follow-up side."},
        {"name": "N_replication", "definition": "Sample size for the replication/follow-up side."},
        {"name": "D_smaller_N", "definition": "D value on the smaller-N side after comparing original and replication N."},
        {"name": "N_smaller_N", "definition": "Smaller of original and replication N."},
        {"name": "D_larger_N", "definition": "D value on the larger-N side after comparing original and replication N."},
        {"name": "N_larger_N", "definition": "Larger of original and replication N."},
        {"name": "smaller_N_role", "definition": "Which side supplied D_smaller_N/N_smaller_N: original or replication."},
        {"name": "larger_N_role", "definition": "Which side supplied D_larger_N/N_larger_N: original or replication."},
        {"name": "D_larger_N_minus_smaller_N", "definition": "D_larger_N minus D_smaller_N."},
        {"name": "original_sig_05", "definition": "Whether the original side exceeds the approximate p<.05 D/N boundary used by the legacy builder."},
        {"name": "replication_sig_05", "definition": "Whether the replication side exceeds the approximate p<.05 D/N boundary used by the legacy builder."},
        {"name": "larger_n_replication", "definition": "True when replication N is larger than original N."},
        {"name": "d_grew", "definition": "True when D_replication is greater than D_original."},
        {"name": "d_ratio", "definition": "D_replication divided by D_original when defined."},
        {"name": "n_ratio", "definition": "N_replication divided by N_original when defined."},
        {"name": "category", "definition": "Legacy shrink/grow/significance category."},
        {"name": "source_artifact_local_path", "definition": "Repo-relative local file path used by the numeric extractor."},
        {"name": "source_artifact_sha256", "definition": "Checksum of the local source artifact when available."},
        {"name": "source_artifact_access_status", "definition": "Whether the local source artifact currently exists in the checkout."},
        {"name": "dn_check_pairs_path", "definition": "Repo-relative upstream D/N check pair table path."},
        {"name": "dn_check_strict_sides_path", "definition": "Repo-relative upstream strict result-side table path."},
        {"name": "strict_original_result_check_id", "definition": "Strict verbatim original-side check row ID when exact pair alignment exists."},
        {"name": "strict_replication_result_check_id", "definition": "Strict verbatim replication-side check row ID when exact pair alignment exists."},
        {"name": "value_verification_state", "definition": "Current value-verification state using the repo evidence ladder vocabulary."},
        {"name": "target_acquisition_state", "definition": "Current source-object acquisition state using the repo evidence ladder vocabulary."},
        {"name": "notes", "definition": "Short notes about provenance or promotion state."},
        {"name": "created_by", "definition": "Script that generated the row."},
        {"name": "created_at", "definition": "UTC timestamp for this generated table refresh."},
    ],
}


def clean_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and math.isnan(value):
        return ""
    text = str(value)
    text = re.sub(r"[\x00-\x1f\x7f-\x9f]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def slugify(value: Any, fallback: str = "source") -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", clean_text(value).lower()).strip("_")
    return slug[:160] or fallback


def split_source_paths(path: Any) -> list[str]:
    if path is None:
        return []
    return [part.strip() for part in str(path).split(";") if part.strip()]


def rel_one(path: Any) -> str:
    if path is None:
        return ""
    path = Path(str(path).strip())
    try:
        return str(path.resolve().relative_to(ROOT))
    except Exception:
        return str(path)


def rel(path: Any) -> str:
    parts = split_source_paths(path)
    if len(parts) > 1:
        return " ; ".join(rel_one(part) for part in parts)
    return rel_one(path)


def stable_id(prefix: str, *parts: Any, size: int = 16) -> str:
    joined = "\x1f".join(clean_text(part) for part in parts)
    return f"{prefix}_{hashlib.sha256(joined.encode('utf-8')).hexdigest()[:size]}"


def to_float(value: Any) -> float:
    try:
        return float(clean_text(value))
    except ValueError:
        return np.nan


def bool_text(value: Any) -> str:
    text = clean_text(value).lower()
    if text in {"true", "1", "yes"}:
        return "true"
    if text in {"false", "0", "no"}:
        return "false"
    return clean_text(value)


def access_status(path_text: str) -> str:
    if not path_text:
        return "not_recorded"
    parts = split_source_paths(path_text)
    statuses = []
    for part in parts:
        path = ROOT / part if not Path(part).is_absolute() else Path(part)
        statuses.append(path.exists() and path.is_file())
    if not statuses:
        return "not_recorded"
    if all(statuses):
        return "local_files_present" if len(statuses) > 1 else "local_file_present"
    if any(statuses):
        return "local_files_partially_present"
    return "local_files_missing" if len(statuses) > 1 else "local_file_missing"


def current_rule_blockers(row: pd.Series) -> str:
    blockers: list[str] = []
    n_original = to_float(row.get("N_original"))
    n_replication = to_float(row.get("N_replication"))
    if not np.isfinite(n_original) or not np.isfinite(n_replication):
        blockers.append("blocked_missing_N")
    else:
        if n_original < 10 or n_replication < 10:
            blockers.append("blocked_N_lt_10")
        if n_replication <= n_original:
            blockers.append("blocked_replication_N_le_original_N")
    return " | ".join(blockers)


def smaller_larger_values(row: pd.Series) -> dict[str, Any]:
    d_original = to_float(row.get("D_original"))
    d_replication = to_float(row.get("D_replication"))
    n_original = to_float(row.get("N_original"))
    n_replication = to_float(row.get("N_replication"))
    if np.isfinite(n_original) and np.isfinite(n_replication) and n_replication < n_original:
        return {
            "D_smaller_N": d_replication,
            "N_smaller_N": n_replication,
            "D_larger_N": d_original,
            "N_larger_N": n_original,
            "smaller_N_role": "replication",
            "larger_N_role": "original",
            "D_larger_N_minus_smaller_N": d_original - d_replication,
        }
    return {
        "D_smaller_N": d_original,
        "N_smaller_N": n_original,
        "D_larger_N": d_replication,
        "N_larger_N": n_replication,
        "smaller_N_role": "original",
        "larger_N_role": "replication",
        "D_larger_N_minus_smaller_N": d_replication - d_original,
    }


def value_fingerprint(project: Any, outcome: Any, d_original: Any, n_original: Any, d_replication: Any, n_replication: Any) -> tuple[str, str, str, str, str, str]:
    def num(value: Any) -> str:
        x = to_float(value)
        if not np.isfinite(x):
            return ""
        return f"{x:.8g}"

    return (
        clean_text(project),
        clean_text(outcome).lower(),
        num(d_original),
        num(n_original),
        num(d_replication),
        num(n_replication),
    )


def load_strict_alignment() -> tuple[dict[tuple[str, str], dict[str, str]], dict[tuple[str, str, str, str, str, str], dict[str, str]], set[str]]:
    if not DN_STRICT_SIDES.exists():
        return {}, {}, set()
    sides = pd.read_csv(DN_STRICT_SIDES, sep="\t", dtype=str, keep_default_na=False)
    ready = sides[sides["dn_check_status"] == "dn_checked_ready_for_mapping"].copy()
    projects = set(ready["project"].map(clean_text))
    aligned: dict[tuple[str, str], dict[str, str]] = {}
    fingerprint_candidates: dict[tuple[str, str, str, str, str, str], list[dict[str, str]]] = {}
    for (project, pair_id), group in ready.groupby(["project", "pair_id"], dropna=False):
        side_ids = {
            clean_text(row.result_side): clean_text(row.dn_result_check_id)
            for row in group.itertuples(index=False)
        }
        if side_ids.get("original") and side_ids.get("replication"):
            aligned[(clean_text(project), clean_text(pair_id))] = side_ids
            original = group[group["result_side"] == "original"].iloc[0]
            replication = group[group["result_side"] == "replication"].iloc[0]
            fp = value_fingerprint(
                project,
                original.get("outcome_label", ""),
                original.get("d", ""),
                original.get("standardized_n", ""),
                replication.get("d", ""),
                replication.get("standardized_n", ""),
            )
            fingerprint_candidates.setdefault(fp, []).append(side_ids)
    fingerprint_aligned = {
        fp: rows[0]
        for fp, rows in fingerprint_candidates.items()
        if len(rows) == 1
    }
    return aligned, fingerprint_aligned, projects


def build_rows() -> pd.DataFrame:
    if not DN_PAIRS.exists():
        raise FileNotFoundError(f"Missing D/N pair check table: {DN_PAIRS}")
    pairs = pd.read_csv(DN_PAIRS, sep="\t", dtype=str, keep_default_na=False)
    aligned, fingerprint_aligned, strict_projects = load_strict_alignment()
    created_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()

    rows: list[dict[str, Any]] = []
    for _, row in pairs.iterrows():
        project = clean_text(row.get("project"))
        source_dataset = clean_text(row.get("source_dataset"))
        native_pair_id = clean_text(row.get("pair_id"))
        key = (project, native_pair_id)
        side_ids = aligned.get(key, {})
        alignment_method = "strict_pair_id"
        if not side_ids:
            side_ids = fingerprint_aligned.get(
                value_fingerprint(
                    project,
                    row.get("outcome"),
                    row.get("D_original"),
                    row.get("N_original"),
                    row.get("D_replication"),
                    row.get("N_replication"),
                ),
                {},
            )
            alignment_method = "strict_outcome_d_n_fingerprint" if side_ids else ""
        blockers = current_rule_blockers(row)
        rule_status = "included_by_current_figure1_dn_rule" if not blockers else "excluded_by_current_figure1_dn_rule"
        if side_ids:
            strict_status = "strict_verbatim_pair_aligned" if alignment_method == "strict_pair_id" else "strict_verbatim_pair_aligned_by_outcome_d_n"
            promotion_status = "ready_for_source_result_side_promotion"
            verification_state = "value-bearing source text found"
            notes = f"Original and replication strict result-side rows are available; alignment_method={alignment_method}."
        elif project in strict_projects:
            strict_status = "strict_verbatim_available_project_level_not_pair_aligned"
            promotion_status = "needs_pair_alignment_to_strict_side_rows"
            verification_state = "source object obtained but not parsed"
            notes = "Strict result-side rows exist for this project, but exact pair IDs are not aligned in this root table yet."
        else:
            strict_status = "numeric_only_needs_verbatim_support"
            promotion_status = "needs_verbatim_source_result_support"
            verification_state = "corpus assertion only"
            notes = "Numeric D/N values come from an existing local project-specific extractor; source_result promotion still needs verbatim support rows."
        values = smaller_larger_values(row)
        out = {
            "figure1_replication_pair_id": stable_id("fig1_pair", project, source_dataset, native_pair_id, row.get("outcome")),
            "dn_pair_check_id": clean_text(row.get("dn_pair_check_id")),
            "plot_universe_id": "plot1_replication_pairs",
            "source_family_key": slugify(project),
            "source_family_label": project,
            "project": project,
            "source_dataset": source_dataset,
            "native_pair_id": native_pair_id,
            "pair_result_status": "dn_checked_numeric_pair",
            "current_plot_rule_status": rule_status,
            "current_plot_rule_blockers": blockers,
            "strict_verbatim_status": strict_status,
            "source_result_promotion_status": promotion_status,
            "original_title": clean_text(row.get("original_title")),
            "replication_title": clean_text(row.get("replication_title")),
            "original_doi": clean_text(row.get("original_doi")),
            "replication_doi": clean_text(row.get("replication_doi")),
            "outcome_label": clean_text(row.get("outcome")),
            "D_original": to_float(row.get("D_original")),
            "N_original": to_float(row.get("N_original")),
            "D_replication": to_float(row.get("D_replication")),
            "N_replication": to_float(row.get("N_replication")),
            **values,
            "original_sig_05": bool_text(row.get("original_sig_05")),
            "replication_sig_05": bool_text(row.get("replication_sig_05")),
            "larger_n_replication": bool_text(row.get("larger_n_replication")),
            "d_grew": bool_text(row.get("d_grew")),
            "d_ratio": clean_text(row.get("d_ratio")),
            "n_ratio": clean_text(row.get("n_ratio")),
            "category": clean_text(row.get("category")),
            "source_artifact_local_path": clean_text(row.get("source_artifact_local_path")),
            "source_artifact_sha256": clean_text(row.get("source_artifact_sha256")),
            "source_artifact_access_status": access_status(row.get("source_artifact_local_path")),
            "dn_check_pairs_path": rel(DN_PAIRS),
            "dn_check_strict_sides_path": rel(DN_STRICT_SIDES),
            "strict_original_result_check_id": side_ids.get("original", ""),
            "strict_replication_result_check_id": side_ids.get("replication", ""),
            "value_verification_state": verification_state,
            "target_acquisition_state": "source object mirrored" if clean_text(row.get("source_artifact_sha256")) else "source object obtained but not checksummed",
            "notes": notes,
            "created_by": "scripts/build_figure1_replication_pairs_table.py",
            "created_at": created_at,
        }
        rows.append(out)
    return pd.DataFrame(rows, columns=COLUMNS)


def normalize_for_tsv(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for col in out.columns:
        if out[col].dtype == object:
            out[col] = out[col].map(clean_text)
    return out


def write_summary(df: pd.DataFrame) -> None:
    OUT_SUMMARY.parent.mkdir(parents=True, exist_ok=True)
    included = int((df["current_plot_rule_status"] == "included_by_current_figure1_dn_rule").sum())
    strict_exact = int((df["strict_verbatim_status"] == "strict_verbatim_pair_aligned").sum())
    strict_ready = int((df["source_result_promotion_status"] == "ready_for_source_result_side_promotion").sum())
    projects = int(df["project"].nunique())
    lines = [
        "# Figure 1 Replication Pairs Root Table",
        "",
        f"- Root pair rows: **{len(df):,}**",
        f"- Project/source-family labels: **{projects:,}**",
        f"- Rows included by current Figure 1 D/N rule: **{included:,}**",
        f"- Rows ready for source_result side promotion: **{strict_ready:,}**",
        f"- Rows with exact strict pair-ID alignment: **{strict_exact:,}**",
        "",
        "| Status | Rows |",
        "|---|---:|",
    ]
    for status, count in df["source_result_promotion_status"].value_counts().items():
        lines.append(f"| {clean_text(status)} | {int(count):,} |")
    lines.extend(
        [
            "",
            "Root table:",
            "",
            f"- `{rel(OUT_TSV)}`",
            f"- `{rel(OUT_SCHEMA)}`",
        ]
    )
    OUT_SUMMARY.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run(*, replace: bool) -> None:
    outputs = [OUT_TSV, OUT_SCHEMA, OUT_SUMMARY]
    if not replace:
        existing = [path for path in outputs if path.exists()]
        if existing:
            names = ", ".join(str(path) for path in existing)
            raise SystemExit(f"Refusing to overwrite existing outputs without --replace: {names}")
    df = build_rows()
    normalize_for_tsv(df).to_csv(OUT_TSV, sep="\t", index=False)
    OUT_SCHEMA.write_text(yaml.safe_dump(SCHEMA, sort_keys=False, allow_unicode=True), encoding="utf-8")
    write_summary(df)
    print(f"Wrote Figure 1 replication pairs: {OUT_TSV}")
    print(f"Wrote schema: {OUT_SCHEMA}")
    print(f"Wrote summary: {OUT_SUMMARY}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--replace", action="store_true", help="Overwrite existing outputs.")
    args = parser.parse_args()
    run(replace=args.replace)


if __name__ == "__main__":
    main()
