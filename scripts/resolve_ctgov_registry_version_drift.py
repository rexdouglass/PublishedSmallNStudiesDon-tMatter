#!/usr/bin/env python3
"""Record CT.gov source-version drift for level-6 verifier failures.

The level-6 verifier is intentionally strict: if a plotted CT.gov/AACT-derived
row cannot be recomputed from the current ClinicalTrials.gov JSON, it refuses to
promote the row. This script turns those refusals into a reusable drift ledger:
local KG/AACT values, current registry values for the same NCT/outcome, and the
next historical-source action needed.
"""

from __future__ import annotations

import json
import math
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from statistics import NormalDist
from typing import Any

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
PILOT = ROOT / "data" / "derived" / "effect_inflation_dataset" / "schema_pilot"
SAMPLE_N = int(os.environ.get("SCHEMA_PILOT_N", "300"))
SAMPLE_SUFFIX = f"sample_{SAMPLE_N}"

LEVEL6_ATTEMPTS_IN = PILOT / f"level6_value_verification_attempts_{SAMPLE_SUFFIX}.tsv"
CANDIDATE_ROWS_IN = ROOT / "data" / "derived" / "corpus_candidates" / "candidate_d_n_rows.csv.gz"
CTGOV_RAW_IN = ROOT / "data" / "raw" / "corpus_candidates" / "ctgov_kg" / "efficacy_df.csv"

OUT_TSV = PILOT / f"ctgov_registry_version_drift_{SAMPLE_SUFFIX}.tsv"
OUT_SUMMARY = PILOT / f"ctgov_registry_version_drift_summary_{SAMPLE_SUFFIX}.tsv"
OUT_REPORT = ROOT / "reports" / f"ctgov_registry_version_drift_{SAMPLE_SUFFIX}_2026-04-30.md"

NORMAL = NormalDist()
P_VALUE_NUMBER_RE = re.compile(r"(?P<p>[0-9]*\.?[0-9]+(?:[eE][-+]?\d+)?)")


def safe_text(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and math.isnan(value):
        return ""
    return re.sub(r"\s+", " ", str(value).replace("\t", " ").replace("\r", " ").replace("\n", " ")).strip()


def norm_text(value: object) -> str:
    text = safe_text(value).lower()
    return re.sub(r"[^a-z0-9]+", " ", text).strip()


def fnum(value: object) -> float | None:
    text = safe_text(value)
    if not text or text.lower() in {"nan", "none", "null"}:
        return None
    try:
        out = float(text)
    except ValueError:
        match = P_VALUE_NUMBER_RE.search(text)
        if not match:
            return None
        try:
            out = float(match.group("p"))
        except ValueError:
            return None
    return out if math.isfinite(out) else None


def parse_p_value(value: object) -> float | None:
    text = safe_text(value)
    if not text:
        return None
    match = P_VALUE_NUMBER_RE.search(text)
    if not match:
        return None
    p_value = fnum(match.group("p"))
    if p_value is None or p_value <= 0:
        return None
    return min(max(p_value, 1e-12), 1.0)


def z_from_p_value(value: object) -> float | None:
    p_value = parse_p_value(value)
    if p_value is None or p_value >= 1:
        return None
    return NORMAL.inv_cdf(1 - p_value / 2)


def p_from_abs_z(value: object) -> float | None:
    z_value = fnum(value)
    if z_value is None:
        return None
    return 2 * (1 - NORMAL.cdf(abs(z_value)))


def close(left: object, right: object, tol: float = 1e-6) -> bool:
    a = fnum(left)
    b = fnum(right)
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


def enrollment_count(study_json: dict[str, Any]) -> float | None:
    return fnum(
        (((study_json.get("protocolSection") or {}).get("designModule") or {}).get("enrollmentInfo") or {}).get("count")
    )


def first_denom_sum(outcome: dict[str, Any], group_ids: list[str] | None = None) -> float | None:
    wanted = {safe_text(item) for item in group_ids or [] if safe_text(item)}
    for denom in outcome.get("denoms") or []:
        values: list[float] = []
        for count in denom.get("counts") or []:
            group_id = safe_text(count.get("groupId"))
            if wanted and group_id not in wanted:
                continue
            value = fnum(count.get("value"))
            if value is not None:
                values.append(value)
        if values:
            return float(sum(values))
    return None


def registry_analysis_rows(study_json: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    enrollment = enrollment_count(study_json)
    outcomes = (
        ((study_json.get("resultsSection") or {}).get("outcomeMeasuresModule") or {}).get("outcomeMeasures") or []
    )
    for outcome_index, outcome in enumerate(outcomes, start=1):
        for analysis_index, analysis in enumerate(outcome.get("analyses") or [], start=1):
            group_ids = [safe_text(item) for item in analysis.get("groupIds") or [] if safe_text(item)]
            rows.append(
                {
                    "current_outcome_index": outcome_index,
                    "current_analysis_index": analysis_index,
                    "current_outcome_title": safe_text(outcome.get("title")),
                    "current_outcome_title_norm": norm_text(outcome.get("title")),
                    "current_outcome_type": safe_text(outcome.get("type")),
                    "current_p_value": safe_text(analysis.get("pValue")),
                    "current_z_from_p": z_from_p_value(analysis.get("pValue")),
                    "current_param_type": safe_text(analysis.get("paramType")),
                    "current_param_value": fnum(analysis.get("paramValue")),
                    "current_statistical_method": safe_text(analysis.get("statisticalMethod")),
                    "current_group_ids": "|".join(group_ids),
                    "current_analysis_denom_sum": first_denom_sum(outcome, group_ids),
                    "current_outcome_denom_sum": first_denom_sum(outcome, None),
                    "current_enrollment_count": enrollment,
                }
            )
    return rows


def load_json(path_value: object) -> dict[str, Any] | None:
    path = Path(safe_text(path_value))
    if not path.is_absolute():
        path = ROOT / path
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError:
        return None


def failed_child_ids(failure_reason: str) -> list[str]:
    ids: list[str] = []
    for part in safe_text(failure_reason).split(";"):
        match = re.search(r"(ctgovkg_\d+)", part)
        if match:
            ids.append(match.group(1))
    return ids


def read_raw_ctgov_rows(child_ids: set[str]) -> pd.DataFrame:
    # `candidate_d_n_rows.row_id` uses the physical row number in efficacy_df.csv,
    # not the source file's `Unnamed: 0` column. Those differ for some records.
    physical_rows = sorted(
        int(item.replace("ctgovkg_", ""))
        for item in child_ids
        if re.fullmatch(r"ctgovkg_\d+", item)
    )
    if not physical_rows:
        return pd.DataFrame()
    usecols = [
        "Unnamed: 0",
        "NCT_ID",
        "completion_year",
        "enrollment_num",
        "outcome_id",
        "outcome_type",
        "outcome_title",
        "p_value",
        "method",
        "method_desc",
        "param_type",
        "param_value",
        "info",
        "trial_phase",
        "allocation",
    ]
    raw = pd.read_csv(CTGOV_RAW_IN, usecols=usecols, dtype=str, keep_default_na=False)
    valid_rows = [rownum for rownum in physical_rows if 0 <= rownum < len(raw)]
    if not valid_rows:
        return pd.DataFrame(columns=usecols + ["row_id"])
    out = raw.iloc[valid_rows].copy()
    out["row_id"] = [f"ctgovkg_{rownum}" for rownum in valid_rows]
    return out


def candidate_rows_for_nct(nct_ids: set[str]) -> pd.DataFrame:
    usecols = ["source_corpus", "row_id", "paper_id", "title", "outcome", "effect", "z", "D", "N", "notes", "year"]
    chunks: list[pd.DataFrame] = []
    for chunk in pd.read_csv(CANDIDATE_ROWS_IN, usecols=usecols, dtype=str, keep_default_na=False, chunksize=250_000):
        hit = chunk.loc[
            chunk["source_corpus"].eq("ctgov_finer_grained_kg")
            & chunk["paper_id"].str.upper().isin(nct_ids)
        ].copy()
        if not hit.empty:
            chunks.append(hit)
    return pd.concat(chunks, ignore_index=True) if chunks else pd.DataFrame(columns=usecols)


def main() -> None:
    attempts = pd.read_csv(LEVEL6_ATTEMPTS_IN, sep="\t", dtype=str, keep_default_na=False)
    failed = attempts.loc[
        attempts["verification_route"].eq("clinicaltrials_api_v2_json")
        & attempts["promote_to_level6"].astype(str).ne("true")
        & attempts["nct_id"].astype(str).str.startswith("NCT")
    ].copy()

    nct_ids = set(failed["nct_id"].str.upper())
    children = candidate_rows_for_nct(nct_ids)
    needed_child_ids = set(children["row_id"]) | {
        child_id for reason in failed["failure_reason"] for child_id in failed_child_ids(reason)
    }
    raw_rows = read_raw_ctgov_rows(needed_child_ids)
    raw_by_id = {safe_text(row["row_id"]): row for _, row in raw_rows.iterrows()}

    out_rows: list[dict[str, object]] = []
    for _, attempt in failed.iterrows():
        nct_id = safe_text(attempt.get("nct_id")).upper()
        study_json = load_json(attempt.get("source_file_local_path"))
        current_analyses = registry_analysis_rows(study_json or {})
        child_rows = children.loc[children["paper_id"].str.upper().eq(nct_id)].copy()
        if child_rows.empty:
            out_rows.append(
                {
                    "source_result_id": safe_text(attempt.get("source_result_id")),
                    "nct_id": nct_id,
                    "drift_status": "no_local_child_rows_found",
                    "next_action": "Recover the local corpus child rows before trying historical AACT snapshots.",
                }
            )
            continue

        failed_ids = set(failed_child_ids(safe_text(attempt.get("failure_reason"))))
        if failed_ids:
            child_rows = child_rows.loc[child_rows["row_id"].isin(failed_ids)].copy()
        for _, child in child_rows.iterrows():
            child_id = safe_text(child.get("row_id"))
            raw = raw_by_id.get(child_id)
            raw_title = safe_text(raw.get("outcome_title")) if raw is not None else safe_text(child.get("outcome"))
            local_z = fnum(child.get("z"))
            local_p = parse_p_value(raw.get("p_value")) if raw is not None else p_from_abs_z(local_z)
            title_matches = [
                item for item in current_analyses if item["current_outcome_title_norm"] == norm_text(raw_title)
            ]
            matching_values = [
                item for item in title_matches if close(item.get("current_z_from_p"), local_z, tol=1e-5)
            ]
            if matching_values:
                drift_status = "matches_current_json"
                next_action = "No version-drift action needed for this child row."
            elif title_matches:
                drift_status = "same_outcome_title_different_analysis_values"
                next_action = (
                    "Current ClinicalTrials.gov has the outcome title but not the local p/statistic. "
                    "Load AACT monthly/daily snapshots or the CT.gov history/archive around the upstream KG build date."
                )
            else:
                drift_status = "outcome_title_missing_from_current_json"
                next_action = (
                    "Current ClinicalTrials.gov no longer exposes this outcome title. "
                    "Search AACT snapshots and CT.gov history/archive for an older result version."
                )
            current_values = " || ".join(
                [
                    "; ".join(
                        [
                            f"analysis={item['current_analysis_index']}",
                            f"p={item['current_p_value']}",
                            f"z={item['current_z_from_p']}",
                            f"param={item['current_param_type']} {item['current_param_value']}",
                            f"method={item['current_statistical_method']}",
                            f"N_enrollment={item['current_enrollment_count']}",
                        ]
                    )
                    for item in title_matches
                ]
            )
            out_rows.append(
                {
                    "source_result_id": safe_text(attempt.get("source_result_id")),
                    "nct_id": nct_id,
                    "local_child_row_id": child_id,
                    "local_outcome_title": raw_title,
                    "local_outcome_type": safe_text(raw.get("outcome_type")) if raw is not None else "",
                    "local_p_value": safe_text(raw.get("p_value")) if raw is not None else local_p,
                    "local_z_from_p_or_candidate": local_z,
                    "local_param_type": safe_text(raw.get("param_type")) if raw is not None else "",
                    "local_param_value": safe_text(raw.get("param_value")) if raw is not None else safe_text(child.get("effect")),
                    "local_method": safe_text(raw.get("method")) if raw is not None else safe_text(child.get("notes")),
                    "local_method_desc": safe_text(raw.get("method_desc")) if raw is not None else "",
                    "local_enrollment_num": safe_text(raw.get("enrollment_num")) if raw is not None else safe_text(child.get("N")),
                    "local_completion_year": safe_text(raw.get("completion_year")) if raw is not None else safe_text(child.get("year")),
                    "current_registry_json_path": safe_text(attempt.get("source_file_local_path")),
                    "current_matching_title_analysis_count": len(title_matches),
                    "current_matching_value_analysis_count": len(matching_values),
                    "current_values_for_same_title": current_values,
                    "drift_status": drift_status,
                    "historical_source_needed": str(drift_status != "matches_current_json").lower(),
                    "candidate_history_url": f"https://clinicaltrials.gov/study/{nct_id}?tab=history",
                    "candidate_archive_url": f"https://clinicaltrials.gov/archive/{nct_id}",
                    "recommended_aact_route": (
                        "Use AACT permanent monthly snapshots first; compare outcome_measurements/outcome_analyses/"
                        "result_groups for this NCT and outcome title against the local p/statistic."
                    ),
                    "next_action": next_action,
                }
            )

    out = pd.DataFrame(out_rows)
    OUT_TSV.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT_TSV, sep="\t", index=False)

    summary_rows: list[dict[str, object]] = [
        {"metric": "sample_n", "value": SAMPLE_N},
        {"metric": "ctgov_level6_failures_with_nct", "value": int(len(failed))},
        {"metric": "drift_child_rows_recorded", "value": int(len(out))},
        {"metric": "created_at_utc", "value": datetime.now(timezone.utc).isoformat()},
    ]
    for key, value in out.get("drift_status", pd.Series(dtype=str)).value_counts().sort_index().items():
        summary_rows.append({"metric": f"drift_status::{key}", "value": int(value)})
    summary = pd.DataFrame(summary_rows)
    summary.to_csv(OUT_SUMMARY, sep="\t", index=False)

    lines = [
        "# CT.gov Registry Version Drift Ledger",
        "",
        f"- Sample rows: {SAMPLE_N}",
        f"- CT.gov level-6 verifier failures with NCT IDs: {len(failed)}",
        f"- Local child rows requiring historical-source handling: {len(out)}",
        "",
        "## Status Counts",
        "",
    ]
    if out.empty:
        lines.append("- No CT.gov version-drift rows found.")
    else:
        for _, row in out["drift_status"].value_counts().rename_axis("status").reset_index(name="n").iterrows():
            lines.append(f"- `{row['status']}`: {int(row['n'])}")
    lines.extend(["", "## Rows", ""])
    for _, row in out.iterrows():
        lines.append(
            f"- `{row['source_result_id']}` / `{row['nct_id']}` / `{row['local_child_row_id']}`: "
            f"{row['drift_status']}; local p={row['local_p_value']}, local param="
            f"{row['local_param_type']} {row['local_param_value']}; current same-title analyses: "
            f"{row['current_values_for_same_title'] or 'none'}"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- This ledger is not a failed acquisition list. The current registry JSON was mirrored successfully.",
            "- A row marked `same_outcome_title_different_analysis_values` means the represented trial/outcome exists, but the current registry values do not reproduce the local corpus values. It needs a historical AACT/ClinicalTrials.gov version before promotion.",
            "- The next scalable implementation is an AACT snapshot comparator keyed by NCT ID, outcome title, analysis p-value/statistic, group codes, and enrollment.",
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
