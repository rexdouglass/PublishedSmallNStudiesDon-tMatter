#!/usr/bin/env python3
"""Build a high-volume registered-result universe from ClinicalTrials.gov.

This is deliberately separate from the strict Plot 3 builder. Clinical trial
registration/result posting creates many real registered outcome-result rows,
but it is not the same evidentiary object as a Registered Report or PAP-locked
paper row. The outputs here preserve that distinction while making the large
clinical registry universe auditable.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from statistics import NormalDist
from typing import Any

import pandas as pd
import requests


ROOT = Path(__file__).resolve().parents[1]
RAW_CTGOV_KG = ROOT / "data" / "raw" / "corpus_candidates" / "ctgov_kg" / "efficacy_df.csv"
CACHE_DIR = ROOT / "data" / "cache" / "ctgov_api_v2_studies"
OUT_DIR = ROOT / "data" / "derived" / "effect_inflation_dataset"
ROW_OUT = OUT_DIR / "plot3_ctgov_api_registered_outcome_ratio_event_rows.csv.gz"
TRIAL_MEDIAN_OUT = OUT_DIR / "plot3_ctgov_api_registered_trial_medians.csv"
SUMMARY_OUT = OUT_DIR / "plot3_ctgov_api_registered_summary.csv"
API_BASE = "https://clinicaltrials.gov/api/v2/studies"
API_SEARCH_QUERY = "AREA[StudyType]Interventional AND AREA[DesignAllocation]Randomized AND AREA[HasResults]true"

ALLOWED_OUTCOME_TYPES = {"PRIMARY", "SECONDARY", "OTHER_PRE_SPECIFIED"}
P_VALUE_NUMBER_RE = re.compile(r"(?P<p>\d*\.?\d+(?:e[+-]?\d+)?)", re.IGNORECASE)
NORMAL = NormalDist()


def safe_text(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and math.isnan(value):
        return ""
    return str(value).strip()


def fnum(value: object) -> float | None:
    text = safe_text(value).replace(",", "")
    if not text:
        return None
    try:
        out = float(text)
    except ValueError:
        return None
    if not math.isfinite(out):
        return None
    return out


def chinn_from_ratio(value: float | None) -> float | None:
    if value is None or value <= 0:
        return None
    out = abs(math.log(value)) * math.sqrt(3) / math.pi
    return out if math.isfinite(out) else None


def parse_p_value(value: object) -> float | None:
    text = safe_text(value).lower()
    if not text:
        return None
    match = P_VALUE_NUMBER_RE.search(text)
    if not match:
        return None
    p_value = fnum(match.group("p"))
    if p_value is None:
        return None
    if p_value <= 0:
        return None
    return min(max(p_value, 1e-12), 1.0)


def d_from_two_sided_p(p_value: float | None, n_total: float | None) -> float | None:
    if p_value is None or n_total is None or n_total <= 0 or p_value >= 1:
        return None
    z_value = NORMAL.inv_cdf(1 - p_value / 2)
    out = abs(2 * z_value / math.sqrt(n_total))
    return out if math.isfinite(out) else None


def ratio_method(param_type: object) -> str | None:
    text = safe_text(param_type).lower()
    if not text or "log" in text or "reduction" in text or "efficacy" in text:
        return None
    if "odds ratio" in text or text == "or":
        return "chinn_log_odds_ratio_to_d"
    if "hazard ratio" in text or text == "hr":
        return "chinn_log_hazard_ratio_to_d"
    if "risk ratio" in text or "relative risk" in text or text == "rr":
        return "chinn_log_risk_ratio_to_d"
    return None


def binary_unit_kind(unit: object) -> str | None:
    text = safe_text(unit).lower()
    if not text:
        return None
    bad_tokens = [
        "change",
        "score",
        "scale",
        "mean",
        "median",
        "days",
        "hours",
        "minutes",
        "months",
        "years",
        "mg",
        "ml",
        "mm",
        "cells",
        "visits",
        "episodes",
        "per ",
        "/",
        "hemoglobin",
    ]
    if any(token in text for token in bad_tokens):
        return None
    entity_tokens = ["participant", "participants", "subject", "subjects", "patient", "patients", "person", "persons"]
    if not any(token in text for token in entity_tokens):
        return None
    if "percent" in text or "percentage" in text or "proportion" in text:
        return "percent"
    return "count"


def first_group_denoms(outcome: dict[str, Any], group_ids: list[str]) -> dict[str, float]:
    for denom in outcome.get("denoms") or []:
        counts = {
            safe_text(count.get("groupId")): fnum(count.get("value"))
            for count in denom.get("counts") or []
            if safe_text(count.get("groupId")) in group_ids
        }
        if len(counts) == 2 and all(value is not None and value > 0 for value in counts.values()):
            return counts  # type: ignore[return-value]
    return {}


def first_group_measurements(outcome: dict[str, Any], group_ids: list[str]) -> dict[str, float]:
    values: dict[str, float] = {}
    for class_row in outcome.get("classes") or []:
        for category in class_row.get("categories") or []:
            candidate: dict[str, float] = {}
            for measurement in category.get("measurements") or []:
                group_id = safe_text(measurement.get("groupId"))
                value = fnum(measurement.get("value"))
                if group_id in group_ids and value is not None:
                    candidate[group_id] = value
            if len(candidate) == 2:
                return candidate
            values.update({key: value for key, value in candidate.items() if key not in values})
    return values if len(values) == 2 else {}


def event_count_d(
    outcome: dict[str, Any],
    group_ids: list[str],
    denoms: dict[str, float],
) -> tuple[float | None, str | None, float | None, float | None]:
    unit_kind = binary_unit_kind(outcome.get("unitOfMeasure"))
    if unit_kind is None or len(denoms) != 2:
        return None, None, None, None
    measurements = first_group_measurements(outcome, group_ids)
    if len(measurements) != 2:
        return None, None, None, None
    group_1, group_2 = group_ids
    n1 = denoms[group_1]
    n2 = denoms[group_2]
    v1 = measurements[group_1]
    v2 = measurements[group_2]
    if unit_kind == "percent":
        events_1 = v1 * n1 / 100
        events_2 = v2 * n2 / 100
    else:
        events_1 = v1
        events_2 = v2
    if events_1 < 0 or events_2 < 0 or events_1 > n1 or events_2 > n2:
        return None, None, None, None
    non_events_1 = n1 - events_1
    non_events_2 = n2 - events_2
    odds_ratio = ((events_1 + 0.5) * (non_events_2 + 0.5)) / ((non_events_1 + 0.5) * (events_2 + 0.5))
    d_value = chinn_from_ratio(odds_ratio)
    method = f"event_count_or_to_d_from_{unit_kind}_measure"
    return d_value, method, events_1, events_2


def cache_path(nct_id: str) -> Path:
    return CACHE_DIR / f"{nct_id}.json"


def fetch_study(nct_id: str, refresh_cache: bool = False, delay: float = 0.0) -> dict[str, Any] | None:
    path = cache_path(nct_id)
    if path.exists() and not refresh_cache:
        try:
            return json.loads(path.read_text())
        except json.JSONDecodeError:
            pass
    if delay:
        time.sleep(delay)
    try:
        response = requests.get(f"{API_BASE}/{nct_id}", timeout=20)
    except requests.RequestException:
        return None
    if not response.ok:
        return None
    data = response.json()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, separators=(",", ":")))
    return data


def group_title_map(outcome: dict[str, Any]) -> dict[str, str]:
    return {safe_text(group.get("id")): safe_text(group.get("title")) for group in outcome.get("groups") or []}


def parse_study_data(data: dict[str, Any] | None, fallback_nct_id: str = "") -> list[dict[str, object]]:
    if not data:
        return []
    protocol = data.get("protocolSection", {})
    identification = protocol.get("identificationModule", {})
    design = protocol.get("designModule", {})
    status = protocol.get("statusModule", {})
    sponsor = protocol.get("sponsorCollaboratorsModule", {})
    arms = protocol.get("armsInterventionsModule", {})
    results = data.get("resultsSection", {})
    outcome_module = results.get("outcomeMeasuresModule", {})
    nct = safe_text(identification.get("nctId")) or fallback_nct_id
    rows: list[dict[str, object]] = []
    for outcome_idx, outcome in enumerate(outcome_module.get("outcomeMeasures") or [], start=1):
        outcome_type = safe_text(outcome.get("type")).upper()
        if outcome_type not in ALLOWED_OUTCOME_TYPES:
            continue
        titles = group_title_map(outcome)
        for analysis_idx, analysis in enumerate(outcome.get("analyses") or [], start=1):
            group_ids = [safe_text(value) for value in analysis.get("groupIds") or [] if safe_text(value)]
            if len(group_ids) != 2:
                continue
            denoms = first_group_denoms(outcome, group_ids)
            if len(denoms) != 2:
                continue
            group_1, group_2 = group_ids
            n1 = denoms[group_1]
            n2 = denoms[group_2]
            d_value = None
            method = None
            events_1 = None
            events_2 = None
            param_value = fnum(analysis.get("paramValue"))
            method = ratio_method(analysis.get("paramType"))
            if method:
                d_value = chinn_from_ratio(param_value)
            if d_value is None:
                d_value, method, events_1, events_2 = event_count_d(outcome, group_ids, denoms)
            if d_value is None:
                d_value = d_from_two_sided_p(parse_p_value(analysis.get("pValue")), n1 + n2)
                method = "two_sided_p_value_proxy_with_api_group_denominators" if d_value is not None else None
            if d_value is None or d_value <= 0:
                continue
            rows.append(
                {
                    "point_id": f"ctgov_api_{nct}_{outcome_idx:03d}_{analysis_idx:03d}",
                    "nct_id": nct,
                    "field": "clinical medicine",
                    "field_label": "Clinical medicine",
                    "source_family": "ClinicalTrials.gov API registered outcome results",
                    "source_layer": "registered_outcome_result_universe",
                    "study_type": safe_text(design.get("studyType")),
                    "allocation": safe_text((design.get("designInfo") or {}).get("allocation")),
                    "phases": "; ".join(design.get("phases") or []),
                    "overall_status": safe_text(status.get("overallStatus")),
                    "primary_completion_date": safe_text((status.get("primaryCompletionDateStruct") or {}).get("date")),
                    "results_first_submit_date": safe_text((status.get("resultsFirstSubmitDateStruct") or {}).get("date")),
                    "lead_sponsor_class": safe_text((sponsor.get("leadSponsor") or {}).get("class")),
                    "intervention_types": "; ".join(
                        sorted({safe_text(item.get("type")) for item in arms.get("interventions") or [] if safe_text(item.get("type"))})
                    ),
                    "outcome_type": outcome_type,
                    "outcome_title": safe_text(outcome.get("title")),
                    "outcome_time_frame": safe_text(outcome.get("timeFrame")),
                    "unit_of_measure": safe_text(outcome.get("unitOfMeasure")),
                    "statistical_method": safe_text(analysis.get("statisticalMethod")),
                    "param_type": safe_text(analysis.get("paramType")),
                    "param_value": param_value,
                    "p_value": safe_text(analysis.get("pValue")),
                    "group_1_id": group_1,
                    "group_1_title": titles.get(group_1, group_1),
                    "group_1_n": n1,
                    "group_1_events": events_1,
                    "group_2_id": group_2,
                    "group_2_title": titles.get(group_2, group_2),
                    "group_2_n": n2,
                    "group_2_events": events_2,
                    "D": d_value,
                    "N": n1 + n2,
                    "conversion_method": method,
                    "source_url": f"https://clinicaltrials.gov/study/{nct}",
                }
            )
    return rows


def parse_study(nct_id: str, refresh_cache: bool = False, delay: float = 0.0) -> list[dict[str, object]]:
    data = fetch_study(nct_id, refresh_cache=refresh_cache, delay=delay)
    return parse_study_data(data, fallback_nct_id=nct_id)


def randomized_interventional_nct_ids(limit: int | None = None) -> list[str]:
    source = pd.read_csv(
        RAW_CTGOV_KG,
        usecols=["NCT_ID", "study_type", "allocation"],
        low_memory=False,
    )
    ids = (
        source.loc[
            source["study_type"].eq("Interventional") & source["allocation"].eq("Randomized"),
            "NCT_ID",
        ]
        .dropna()
        .astype(str)
        .drop_duplicates()
        .sort_values()
        .tolist()
    )
    return ids[:limit] if limit else ids


def normalize_rows(rows: list[dict[str, object]]) -> pd.DataFrame:
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    df["D"] = pd.to_numeric(df["D"], errors="coerce")
    df["N"] = pd.to_numeric(df["N"], errors="coerce")
    df = df[(df["D"] > 0) & (df["N"] > 0)].copy()
    df = df.drop_duplicates(
        [
            "nct_id",
            "outcome_type",
            "outcome_title",
            "group_1_id",
            "group_2_id",
            "D",
            "N",
            "conversion_method",
        ]
    )
    df["log10_N"] = df["N"].map(math.log10)
    df["log10_D"] = df["D"].map(math.log10)
    return df.sort_values(["nct_id", "outcome_type", "outcome_title", "point_id"]).reset_index(drop=True)


def build_rows_from_local_seed(limit: int | None, workers: int, refresh_cache: bool, delay: float) -> pd.DataFrame:
    ids = randomized_interventional_nct_ids(limit=limit)
    rows: list[dict[str, object]] = []
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(parse_study, nct_id, refresh_cache, delay): nct_id for nct_id in ids}
        for idx, future in enumerate(as_completed(futures), start=1):
            rows.extend(future.result())
            if idx % 500 == 0:
                print(f"processed {idx:,}/{len(ids):,} studies; rows={len(rows):,}", flush=True)
    return normalize_rows(rows)


def build_rows_from_api_search(limit: int | None, page_size: int) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    params = {
        "format": "json",
        "pageSize": page_size,
        "query.term": API_SEARCH_QUERY,
    }
    page_token = None
    pages = 0
    studies_seen = 0
    while True:
        request_params = params.copy()
        if page_token:
            request_params["pageToken"] = page_token
        response = requests.get(API_BASE, params=request_params, timeout=60)
        response.raise_for_status()
        data = response.json()
        studies = data.get("studies") or []
        pages += 1
        for study in studies:
            if limit is not None and studies_seen >= limit:
                break
            rows.extend(parse_study_data(study))
            studies_seen += 1
        print(
            f"processed api page {pages:,}; studies={studies_seen:,}; rows={len(rows):,}",
            flush=True,
        )
        if limit is not None and studies_seen >= limit:
            break
        page_token = data.get("nextPageToken")
        if not page_token:
            break
    return normalize_rows(rows)


def build_rows(
    limit: int | None,
    workers: int,
    refresh_cache: bool,
    delay: float,
    source: str,
    page_size: int,
) -> pd.DataFrame:
    if source == "api-search":
        return build_rows_from_api_search(limit=limit, page_size=page_size)
    return build_rows_from_local_seed(
        limit=limit,
        workers=workers,
        refresh_cache=refresh_cache,
        delay=delay,
    )


def write_trial_medians(rows: pd.DataFrame) -> pd.DataFrame:
    if rows.empty:
        return rows
    outcome_order = {"PRIMARY": 0, "SECONDARY": 1, "OTHER_PRE_SPECIFIED": 2}
    rows = rows.copy()
    rows["_outcome_order"] = rows["outcome_type"].map(outcome_order).fillna(9)
    labels = (
        rows.sort_values(["nct_id", "_outcome_order", "outcome_title"])
        .groupby("nct_id", sort=False)
        .first()
        .reset_index()
    )
    grouped = (
        rows.groupby("nct_id", sort=False)
        .agg(
            D=("D", "median"),
            N=("N", "median"),
            registered_result_rows=("D", "size"),
            primary_rows=("outcome_type", lambda values: int((values == "PRIMARY").sum())),
            secondary_rows=("outcome_type", lambda values: int((values == "SECONDARY").sum())),
            other_prespecified_rows=("outcome_type", lambda values: int((values == "OTHER_PRE_SPECIFIED").sum())),
            conversion_methods=("conversion_method", lambda values: "; ".join(sorted(set(map(str, values))))),
        )
        .reset_index()
    )
    keep_cols = [
        "nct_id",
        "field",
        "field_label",
        "source_family",
        "study_type",
        "allocation",
        "phases",
        "overall_status",
        "primary_completion_date",
        "results_first_submit_date",
        "lead_sponsor_class",
        "intervention_types",
        "outcome_title",
        "source_url",
    ]
    out = grouped.merge(labels[keep_cols], on="nct_id", how="left")
    out.insert(0, "point_id", [f"ctgov_api_trial_median_{idx:05d}" for idx in range(1, len(out) + 1)])
    out["row_unit"] = "one_trial_median_of_registered_primary_secondary_other_prespecified_ratio_or_event_results"
    out["log10_N"] = out["N"].map(math.log10)
    out["log10_D"] = out["D"].map(math.log10)
    return out


def write_summary(rows: pd.DataFrame, trial_medians: pd.DataFrame) -> pd.DataFrame:
    summary_rows = [
        {"metric": "registered_ratio_or_event_rows", "value": len(rows)},
        {"metric": "trials_with_registered_ratio_or_event_rows", "value": rows["nct_id"].nunique() if not rows.empty else 0},
        {"metric": "trial_median_rows", "value": len(trial_medians)},
    ]
    if not rows.empty:
        for outcome_type, count in rows["outcome_type"].value_counts().items():
            summary_rows.append({"metric": f"outcome_rows_{str(outcome_type).lower()}", "value": int(count)})
        for method, count in rows["conversion_method"].value_counts().items():
            summary_rows.append({"metric": f"conversion_{safe_text(method)}", "value": int(count)})
    return pd.DataFrame(summary_rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--source",
        choices=["api-search", "local-kg"],
        default="api-search",
        help="api-search enumerates the full ClinicalTrials.gov randomized/results query; local-kg uses the older local CT.gov KG NCT seed.",
    )
    parser.add_argument("--limit", type=int, default=None, help="Optional number of studies to process.")
    parser.add_argument("--page-size", type=int, default=500, help="ClinicalTrials.gov API search page size.")
    parser.add_argument("--workers", type=int, default=24)
    parser.add_argument("--refresh-cache", action="store_true")
    parser.add_argument("--delay", type=float, default=0.0, help="Optional per-request delay in seconds.")
    args = parser.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    rows = build_rows(args.limit, args.workers, args.refresh_cache, args.delay, args.source, args.page_size)
    rows.to_csv(ROW_OUT, index=False)
    trial_medians = write_trial_medians(rows)
    trial_medians.to_csv(TRIAL_MEDIAN_OUT, index=False)
    summary = write_summary(rows, trial_medians)
    summary.to_csv(SUMMARY_OUT, index=False)
    print(f"Wrote {len(rows):,} registered outcome rows to {ROW_OUT.relative_to(ROOT)}")
    print(f"Wrote {len(trial_medians):,} trial-median rows to {TRIAL_MEDIAN_OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
