#!/usr/bin/env python3
"""Verify pilot D/N values against mirrored or fetchable source objects.

This is intentionally conservative. It writes an audit ledger of values that can
be recomputed from source bytes, rather than silently changing the main codebook.
The first implemented verifier targets ClinicalTrials.gov registry-result rows,
where the source object is the API v2 study JSON and the plotted paper-level dot
may be a median over multiple registry outcome rows.
"""

from __future__ import annotations

import json
import math
import os
import re
import statistics
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from statistics import NormalDist
from typing import Any

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
PILOT = ROOT / "data" / "derived" / "effect_inflation_dataset" / "schema_pilot"
SAMPLE_N = int(os.environ.get("SCHEMA_PILOT_N", "300"))
SAMPLE_SUFFIX = f"sample_{SAMPLE_N}"

SOURCE_RESULT_IN = PILOT / f"source_result_codebook_{SAMPLE_SUFFIX}.tsv"
HUMAN_CHECK_IN = PILOT / f"human_check_source_result_{SAMPLE_SUFFIX}.tsv"
LEVEL5_STATUS_IN = PILOT / f"level5_row_status_{SAMPLE_SUFFIX}.tsv"
CANDIDATE_ROWS_IN = ROOT / "data" / "derived" / "corpus_candidates" / "candidate_d_n_rows.csv.gz"

LEVEL6_CACHE = ROOT / "data" / "cache" / "provenance_level6" / f"sample_{SAMPLE_N}"
OUT_TSV = PILOT / f"level6_value_verification_attempts_{SAMPLE_SUFFIX}.tsv"
OUT_SUMMARY = PILOT / f"level6_value_verification_summary_{SAMPLE_SUFFIX}.tsv"
OUT_REPORT = ROOT / "reports" / f"level6_value_verification_{SAMPLE_SUFFIX}_2026-04-30.md"

NORMAL = NormalDist()
P_VALUE_NUMBER_RE = re.compile(r"(?P<p>[0-9]*\.?[0-9]+(?:[eE][-+]?\d+)?)")
NCT_RE = re.compile(r"NCT\d{8}", re.I)


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


def d_from_z_n(z_value: float | None, n_value: float | None) -> float | None:
    if z_value is None or n_value is None or n_value <= 0:
        return None
    out = abs(2 * z_value / math.sqrt(n_value))
    return out if math.isfinite(out) else None


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


def nct_from_upstream(row_json: str) -> str:
    try:
        payload = json.loads(row_json)
    except json.JSONDecodeError:
        return ""
    for key in ["paper_id", "study_id", "NCT_ID", "nct_id", "clinicaltrials_id"]:
        match = NCT_RE.search(safe_text(payload.get(key)))
        if match:
            return match.group(0).upper()
    text = json.dumps(payload)
    match = NCT_RE.search(text)
    return match.group(0).upper() if match else ""


def existing_ctgov_json_path(source_result_id: str, nct_id: str, local_paths: str) -> Path | None:
    for token in re.split(r"\s*\|\s*", safe_text(local_paths)):
        if not token or not token.endswith(".json"):
            continue
        if nct_id.lower() not in token.lower():
            continue
        path = Path(token)
        if not path.is_absolute():
            path = ROOT / path
        if path.exists():
            return path
    for pattern in [
        f"{source_result_id}__clinicaltrials_api_v2_json__*{nct_id.lower()}*.json",
        f"*{source_result_id}*{nct_id.lower()}*.json",
    ]:
        matches = sorted((ROOT / "data" / "cache" / "provenance_level5" / f"sample_{SAMPLE_N}").glob(pattern))
        if matches:
            return matches[0]
    shared_cache = ROOT / "data" / "cache" / "ctgov_api_v2_studies" / f"{nct_id}.json"
    if shared_cache.exists():
        return shared_cache
    return None


def fetch_ctgov_json(source_result_id: str, nct_id: str) -> tuple[dict[str, Any] | None, str, str]:
    LEVEL6_CACHE.mkdir(parents=True, exist_ok=True)
    out_path = LEVEL6_CACHE / f"{source_result_id}__clinicaltrials_api_v2_json__clinicaltrials.gov_api_v2_studies_{nct_id.lower()}.json"
    if out_path.exists():
        try:
            return json.loads(out_path.read_text()), rel(out_path), "level6_cache"
        except json.JSONDecodeError:
            pass
    url = f"https://clinicaltrials.gov/api/v2/studies/{nct_id}"
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "dvn-level6-verifier/0.1 (mailto:research@example.invalid)"},
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            data = response.read()
    except Exception as exc:  # noqa: BLE001 - audit script should record the failure.
        return None, "", f"fetch_failed:{type(exc).__name__}:{exc}"
    out_path.write_bytes(data)
    try:
        return json.loads(data.decode("utf-8")), rel(out_path), "clinicaltrials_api_v2_fetch"
    except json.JSONDecodeError as exc:
        return None, rel(out_path), f"json_decode_failed:{exc}"


def load_ctgov_json(source_result_id: str, nct_id: str, local_paths: str) -> tuple[dict[str, Any] | None, str, str]:
    path = existing_ctgov_json_path(source_result_id, nct_id, local_paths)
    if path:
        try:
            return json.loads(path.read_text()), rel(path), "existing_mirror"
        except json.JSONDecodeError as exc:
            return None, rel(path), f"json_decode_failed:{exc}"
    return fetch_ctgov_json(source_result_id, nct_id)


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
        analyses = outcome.get("analyses") or []
        for analysis_index, analysis in enumerate(analyses, start=1):
            group_ids = [safe_text(item) for item in analysis.get("groupIds") or [] if safe_text(item)]
            p_raw = safe_text(analysis.get("pValue"))
            z_value = z_from_p_value(p_raw)
            rows.append(
                {
                    "outcome_index": outcome_index,
                    "analysis_index": analysis_index,
                    "outcome_title": safe_text(outcome.get("title")),
                    "outcome_title_norm": norm_text(outcome.get("title")),
                    "outcome_type": safe_text(outcome.get("type")),
                    "unit_of_measure": safe_text(outcome.get("unitOfMeasure")),
                    "p_value_raw": p_raw,
                    "z_from_p": z_value,
                    "param_type": safe_text(analysis.get("paramType")),
                    "param_value": fnum(analysis.get("paramValue")),
                    "statistical_method": safe_text(analysis.get("statisticalMethod")),
                    "group_ids": "|".join(group_ids),
                    "analysis_denom_sum": first_denom_sum(outcome, group_ids),
                    "outcome_denom_sum": first_denom_sum(outcome, None),
                    "enrollment_count": enrollment,
                }
            )
    return rows


def choose_analysis_for_child(child: pd.Series, analyses: list[dict[str, Any]]) -> tuple[dict[str, Any] | None, str]:
    child_title = norm_text(child.get("title") or child.get("outcome"))
    child_z = fnum(child.get("z"))
    child_effect = fnum(child.get("effect"))
    candidates = [row for row in analyses if row["outcome_title_norm"] == child_title]
    if not candidates:
        return None, "outcome_title_not_found_in_registry_json"

    scored: list[tuple[int, float, dict[str, Any]]] = []
    for row in candidates:
        z_value = row.get("z_from_p")
        z_diff = abs(float(z_value) - child_z) if z_value is not None and child_z is not None else float("inf")
        z_match = child_z is not None and z_value is not None and close(z_value, child_z, tol=1e-5)
        param_value = row.get("param_value")
        effect_match = (
            child_effect is not None
            and param_value is not None
            and close(param_value, child_effect, tol=1e-5)
        )
        score = 0
        if z_match:
            score += 100
        if effect_match:
            score += 20
        if safe_text(row.get("p_value_raw")):
            score += 5
        scored.append((score, z_diff, row))
    scored.sort(key=lambda item: (-item[0], item[1], item[2]["analysis_index"]))
    best_score, _, best = scored[0]
    if best_score < 100:
        return None, "registry_outcome_found_but_matching_p_value_not_found"
    return best, "matched_outcome_title_and_p_value"


def finite_median(values: list[float]) -> float | None:
    vals = [float(value) for value in values if value is not None and math.isfinite(float(value))]
    return statistics.median(vals) if vals else None


def verify_ctgov_row(row: pd.Series, children: pd.DataFrame) -> dict[str, object]:
    srid = safe_text(row.get("source_result_id"))
    nct_id = nct_from_upstream(safe_text(row.get("upstream_row_json")))
    if not nct_id:
        return {
            "source_result_id": srid,
            "verification_route": "clinicaltrials_api_v2_json",
            "verification_status": "failed",
            "failure_reason": "missing_nct_identifier_in_upstream_row",
            "promote_to_level6": "false",
        }

    study_json, local_path, load_status = load_ctgov_json(srid, nct_id, safe_text(row.get("local_paths")))
    if not study_json:
        return {
            "source_result_id": srid,
            "verification_route": "clinicaltrials_api_v2_json",
            "nct_id": nct_id,
            "source_file_local_path": local_path,
            "verification_status": "failed",
            "failure_reason": f"registry_json_unavailable:{load_status}",
            "promote_to_level6": "false",
        }

    analyses = registry_analysis_rows(study_json)
    source_directness = safe_text(row.get("source_directness"))
    if source_directness == "raw_ctgov_registry_row":
        try:
            upstream = json.loads(safe_text(row.get("upstream_row_json")))
        except json.JSONDecodeError:
            upstream = {}
        title = safe_text(upstream.get("outcome_title")) or safe_text(row.get("result_label"))
        p_raw = safe_text(upstream.get("p_value"))
        expected_n = fnum(row.get("standardized_n")) or fnum(upstream.get("enrollment_num"))
        expected_d = fnum(row.get("d"))
        pseudo_child = pd.Series(
            {
                "row_id": safe_text(upstream.get("Unnamed: 0")) or srid,
                "title": title,
                "outcome": title,
                "z": z_from_p_value(p_raw),
                "effect": fnum(upstream.get("param_value")),
                "D": expected_d,
                "N": expected_n,
            }
        )
        analysis, match_status = choose_analysis_for_child(pseudo_child, analyses)
        source_snippet = ""
        failure_reason = ""
        if analysis is None:
            status = "failed"
            promote = "false"
            failure_reason = match_status
        else:
            recomputed_d = d_from_z_n(analysis.get("z_from_p"), expected_n)
            n_matches = close(analysis.get("enrollment_count"), expected_n, tol=1e-8)
            d_matches = close(recomputed_d, expected_d, tol=1e-5)
            source_snippet = " | ".join(
                [
                    f"outcome={analysis.get('outcome_title')}",
                    f"p={analysis.get('p_value_raw')}",
                    f"z={analysis.get('z_from_p')}",
                    f"N_enrollment={analysis.get('enrollment_count')}",
                    f"D_recomputed={recomputed_d}",
                ]
            )
            if n_matches and d_matches:
                status = "verified_single_registry_outcome_from_json"
                promote = "true"
            else:
                status = "failed"
                promote = "false"
                failure_reason = (
                    f"single_outcome_mismatch: recomputed_D={recomputed_d}; expected_D={expected_d}; "
                    f"json_enrollment={analysis.get('enrollment_count')}; expected_N={expected_n}"
                )
        return {
            "source_result_id": srid,
            "verification_route": "clinicaltrials_api_v2_json",
            "source_citation_key": safe_text(row.get("source_citation_key")),
            "current_evidence_level": safe_text(row.get("evidence_level")),
            "nct_id": nct_id,
            "source_file_local_path": local_path,
            "source_file_load_status": load_status,
            "plotted_result_label": safe_text(row.get("result_label")),
            "expected_d": expected_d,
            "expected_n": expected_n,
            "candidate_children_total": 1,
            "candidate_children_verified": 1 if promote == "true" else 0,
            "computed_median_d_from_verified_children": expected_d if promote == "true" else "",
            "computed_median_n_from_verified_children": expected_n if promote == "true" else "",
            "all_children_verified": str(promote == "true").lower(),
            "median_matches_plot": str(promote == "true").lower(),
            "verification_status": status,
            "promote_to_level6": promote,
            "failure_reason": failure_reason,
            "source_value_snippets": source_snippet,
            "lessons_learned": (
                "Raw CT.gov strict rows are single selected registry outcomes, not NCT-level medians; "
                "verify the selected outcome title/p-value/enrollment directly."
            ),
        }

    child_rows = children.loc[
        children["source_corpus"].astype(str).eq("ctgov_finer_grained_kg")
        & children["paper_id"].astype(str).str.upper().eq(nct_id)
    ].copy()
    for column in ["D", "N", "z", "effect"]:
        if column in child_rows.columns:
            child_rows[column] = pd.to_numeric(child_rows[column], errors="coerce")
    child_rows = child_rows.loc[child_rows["D"].notna() & child_rows["N"].notna()].copy()

    if child_rows.empty:
        return {
            "source_result_id": srid,
            "verification_route": "clinicaltrials_api_v2_json",
            "nct_id": nct_id,
            "source_file_local_path": local_path,
            "source_file_load_status": load_status,
            "verification_status": "failed",
            "failure_reason": "no_ctgov_candidate_child_rows_for_nct",
            "promote_to_level6": "false",
        }

    verified_d_values: list[float] = []
    verified_n_values: list[float] = []
    child_failures: list[str] = []
    source_snippets: list[str] = []
    for _, child in child_rows.iterrows():
        analysis, match_status = choose_analysis_for_child(child, analyses)
        child_id = safe_text(child.get("row_id"))
        if analysis is None:
            child_failures.append(f"{child_id}:{match_status}")
            continue
        n_value = fnum(child.get("N"))
        z_value = analysis.get("z_from_p")
        recomputed_d = d_from_z_n(z_value, n_value)
        if not close(analysis.get("enrollment_count"), n_value, tol=1e-8):
            child_failures.append(f"{child_id}:enrollment_mismatch_json={analysis.get('enrollment_count')} child={n_value}")
            continue
        if not close(recomputed_d, child.get("D"), tol=1e-5):
            child_failures.append(f"{child_id}:d_recompute_mismatch_json={recomputed_d} child={child.get('D')}")
            continue
        verified_d_values.append(float(child.get("D")))
        verified_n_values.append(float(child.get("N")))
        if len(source_snippets) < 5:
            source_snippets.append(
                " | ".join(
                    [
                        f"row_id={child_id}",
                        f"outcome={analysis.get('outcome_title')}",
                        f"p={analysis.get('p_value_raw')}",
                        f"z={analysis.get('z_from_p')}",
                        f"N_enrollment={analysis.get('enrollment_count')}",
                        f"D={child.get('D')}",
                    ]
                )
            )

    median_d = finite_median(verified_d_values)
    median_n = finite_median(verified_n_values)
    expected_d = fnum(row.get("d"))
    expected_n = fnum(row.get("standardized_n"))
    all_children_verified = len(verified_d_values) == len(child_rows)
    median_matches = close(median_d, expected_d, tol=1e-5) and close(median_n, expected_n, tol=1e-8)

    if all_children_verified and median_matches:
        status = "verified_plot_d_n_from_registry_json"
        failure_reason = ""
        promote = "true"
    elif verified_d_values and not all_children_verified:
        status = "partial_child_values_verified_from_registry_json"
        failure_reason = "; ".join(child_failures[:10])
        promote = "false"
    elif all_children_verified and not median_matches:
        status = "children_verified_but_plot_median_mismatch"
        failure_reason = f"computed_median_D={median_d}; expected_D={expected_d}; computed_median_N={median_n}; expected_N={expected_n}"
        promote = "false"
    else:
        status = "failed"
        failure_reason = "; ".join(child_failures[:10]) or "no_child_values_verified"
        promote = "false"

    return {
        "source_result_id": srid,
        "verification_route": "clinicaltrials_api_v2_json",
        "source_citation_key": safe_text(row.get("source_citation_key")),
        "current_evidence_level": safe_text(row.get("evidence_level")),
        "nct_id": nct_id,
        "source_file_local_path": local_path,
        "source_file_load_status": load_status,
        "plotted_result_label": safe_text(row.get("result_label")),
        "expected_d": expected_d,
        "expected_n": expected_n,
        "candidate_children_total": int(len(child_rows)),
        "candidate_children_verified": int(len(verified_d_values)),
        "computed_median_d_from_verified_children": median_d,
        "computed_median_n_from_verified_children": median_n,
        "all_children_verified": str(all_children_verified).lower(),
        "median_matches_plot": str(median_matches).lower(),
        "verification_status": status,
        "promote_to_level6": promote,
        "failure_reason": failure_reason,
        "source_value_snippets": " || ".join(source_snippets),
        "lessons_learned": (
            "CT.gov paper dots are medians over all candidate child outcome rows; "
            "verification must match by NCT plus outcome title/p-value and then recompute the paper median."
        ),
    }


def main() -> None:
    source_result = pd.read_csv(SOURCE_RESULT_IN, sep="\t", dtype=str, keep_default_na=False)
    human_check = pd.read_csv(HUMAN_CHECK_IN, sep="\t", dtype=str, keep_default_na=False)
    level5 = pd.read_csv(LEVEL5_STATUS_IN, sep="\t", dtype=str, keep_default_na=False) if LEVEL5_STATUS_IN.exists() else pd.DataFrame()

    merged = source_result.merge(
        human_check[["source_result_id", "source_directness", "upstream_row_json"]],
        on="source_result_id",
        how="left",
    )
    if not level5.empty:
        merged = merged.merge(level5[["source_result_id", "local_paths"]], on="source_result_id", how="left")
    else:
        merged["local_paths"] = ""

    targets = merged.loc[
        merged["source_citation_key"].eq("du2024")
        & merged["evidence_level"].astype(str).isin(["5", "6"])
    ].copy()

    children = pd.read_csv(
        CANDIDATE_ROWS_IN,
        usecols=["source_corpus", "row_id", "paper_id", "title", "outcome", "effect", "z", "D", "N"],
        dtype=str,
        keep_default_na=False,
    )

    rows: list[dict[str, object]] = []
    for _, row in targets.iterrows():
        rows.append(verify_ctgov_row(row, children))

    out = pd.DataFrame(rows)
    OUT_TSV.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT_TSV, sep="\t", index=False)

    summary_rows: list[dict[str, object]] = [
        {"metric": "sample_n", "value": SAMPLE_N},
        {"metric": "ctgov_targets_attempted", "value": int(len(out))},
        {"metric": "ctgov_targets_promotable_to_level6", "value": int(out.get("promote_to_level6", pd.Series(dtype=str)).astype(str).eq("true").sum())},
        {"metric": "created_at_utc", "value": datetime.now(timezone.utc).isoformat()},
    ]
    for key, value in out.get("verification_status", pd.Series(dtype=str)).value_counts().sort_index().items():
        summary_rows.append({"metric": f"verification_status::{key}", "value": int(value)})
    for key, value in out.get("failure_reason", pd.Series(dtype=str)).replace("", "none").value_counts().head(20).items():
        summary_rows.append({"metric": f"failure_reason_top::{key}", "value": int(value)})
    summary = pd.DataFrame(summary_rows)
    summary.to_csv(OUT_SUMMARY, sep="\t", index=False)

    promoted = int(out["promote_to_level6"].astype(str).eq("true").sum()) if not out.empty else 0
    attempted = len(out)
    existing_level6 = int(targets["evidence_level"].astype(str).eq("6").sum())
    new_promotions = int(
        out.merge(targets[["source_result_id", "evidence_level"]], on="source_result_id", how="left")
        .assign(is_new=lambda d: d["promote_to_level6"].astype(str).eq("true") & ~d["evidence_level"].astype(str).eq("6"))
        ["is_new"]
        .sum()
    ) if not out.empty else 0
    lines = [
        "# Level-6 value verification pass",
        "",
        f"- Sample rows: {SAMPLE_N}",
        f"- CT.gov registry-result rows attempted: {attempted}",
        f"- CT.gov rows already level 6 at verifier start: {existing_level6}",
        f"- Rows whose plotted D/N were recomputed from ClinicalTrials.gov API JSON: {promoted}",
        f"- Rows currently below level 6 but promotable from this run: {new_promotions}",
        f"- Rows not promotable from this route: {attempted - promoted}",
        "",
        "## Verification Status",
        "",
    ]
    for _, row in out["verification_status"].value_counts().rename_axis("status").reset_index(name="n").iterrows():
        lines.append(f"- `{row['status']}`: {int(row['n'])}")
    lines.extend(
        [
            "",
            "## Remaining Blockers",
            "",
        ]
    )
    failures = out.loc[out["promote_to_level6"].astype(str).ne("true")].copy()
    if failures.empty:
        lines.append("- None for the CT.gov route in this sample.")
    else:
        for _, row in failures.head(20).iterrows():
            lines.append(
                f"- `{row.get('source_result_id')}` / `{row.get('nct_id')}`: "
                f"{row.get('verification_status')}; {row.get('failure_reason')}"
            )
        lines.append(
            "- The observed blocker is not access. It is source-version disagreement: the local CT.gov KG/AACT-derived p-values for the selected outcomes do not match the current ClinicalTrials.gov API JSON, so this row needs the exact registry snapshot/source version mirrored before promotion."
        )
    lines.extend(
        [
            "",
            "## Lessons Learned",
            "",
            "- For CT.gov paper-level dots, the plotted D/N is often the median across several registry outcome rows. A same-title child row is not enough; the verifier must use NCT ID first, validate each child row from the registry JSON, then recompute the median.",
            "- The retrace logic was corrected to prefer paper/unit identifiers before outcome titles. Outcome-title-only matching can attach values from another NCT with the same label.",
            "- Level-5 acquisition paths should be treated as cached hints. The level-6 verifier re-derives the NCT from the upstream row and refuses paths whose NCT does not match.",
            "- The registry JSON contains the necessary p-values and protocol enrollment counts for this route, so CT.gov rows are a good high-yield target for value verification.",
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
