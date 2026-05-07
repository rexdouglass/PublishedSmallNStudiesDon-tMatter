#!/usr/bin/env python3
"""Triage mirrored follow-up research candidates for strict Figure 1 mining."""

from __future__ import annotations

import csv
import math
import re
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from bs4 import BeautifulSoup


ROOT = Path(__file__).resolve().parents[1]
RAW_ROOT = ROOT / "data/raw/replication_projects/lead_harvest/figure1_research_followup_20260504"
STATUS_ROOT = ROOT / "steps/source_inventory/figure1/research_followup_20260504"
MIRROR_STATUS = STATUS_ROOT / "mirror-status.tsv"
OUT_ROOT = ROOT / "steps/corpus_results/figure1/research_followup_20260504"
TRIAGE_TSV = OUT_ROOT / "research-followup-triage.tsv"
FORRT_SCAN_TSV = OUT_ROOT / "forrt-reversals-conservative-candidate-scan.tsv"
RCT_SCHEMA_TSV = OUT_ROOT / "rct-duplicate-schema-scan.tsv"

NUM_RE = r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)"


def clean_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and math.isnan(value):
        return ""
    text = str(value).replace("−", "-").replace("–", "-")
    return re.sub(r"[\t\r\n ]+", " ", text).strip()


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except Exception:
        return str(path)


def latest_mirror(candidate_key: str, role_contains: str = "") -> Path | None:
    if not MIRROR_STATUS.exists():
        return None
    status = pd.read_csv(MIRROR_STATUS, sep="\t")
    subset = status[(status["candidate_key"].eq(candidate_key)) & (status["status"].eq("mirrored"))].copy()
    if role_contains:
        subset = subset[subset["expected_role"].astype(str).str.contains(role_contains, case=False, na=False)]
    if subset.empty:
        return None
    local_path = subset.iloc[0]["local_path"]
    return ROOT / str(local_path)


def section(text: str, start: str, end: str | None = None) -> str:
    lower = text.lower()
    idx = lower.find(start.lower())
    if idx < 0:
        return ""
    end_idx = len(text) if end is None else lower.find(end.lower(), idx + len(start))
    if end_idx < 0:
        end_idx = len(text)
    return text[idx:end_idx]


def extract_d_values(text: str) -> list[float]:
    values: list[float] = []
    pattern = rf"(?i)(?:hedges.?\s*g|cohen.?\s*d|\bd\b|_d\s*_|_d_|d_)\s*=\s*({NUM_RE})"
    for match in re.finditer(pattern, text):
        try:
            values.append(float(match.group(1)))
        except ValueError:
            pass
    return values


def scan_forrt() -> pd.DataFrame:
    path = latest_mirror("forrt_reversals", "html_database")
    if path is None or not path.exists():
        return pd.DataFrame()
    soup = BeautifulSoup(path.read_text(errors="ignore"), "html.parser")
    rows: list[dict[str, Any]] = []
    for entry_index, li in enumerate(soup.find_all("li")):
        text = clean_text(li.get_text(" ", strip=True))
        if "Original paper" not in text or "Original effect size" not in text or "Replication effect size" not in text:
            continue
        original_info = section(text, "Original paper", "Critique") or section(text, "Original study", "Critique")
        critique_info = section(text, "Critique", "Original effect size")
        original_effect_text = section(text, "Original effect size", "Replication effect size")
        replication_effect_text = section(text, "Replication effect size")
        original_ns = [int(value.replace(",", "")) for value in re.findall(r"(?i)\bn\s*=\s*([0-9][0-9,]*)", original_info)]
        critique_ns = [int(value.replace(",", "")) for value in re.findall(r"(?i)\bn\s*=\s*([0-9][0-9,]*)", critique_info)]
        original_ds = extract_d_values(original_effect_text)
        replication_ds = extract_d_values(replication_effect_text)
        conservative_parseable = len(original_ns) == 1 and len(critique_ns) == 1 and len(original_ds) == 1 and len(replication_ds) == 1
        rows.append(
            {
                "entry_index": entry_index,
                "local_path": rel(path),
                "label": text.split(" Statistics Status:", 1)[0][:160],
                "status_text": section(text, "Status:", "Original paper")[:120],
                "original_n_count": len(original_ns),
                "replication_n_count": len(critique_ns),
                "original_d_count": len(original_ds),
                "replication_d_count": len(replication_ds),
                "conservative_parseable": conservative_parseable,
                "passes_larger_n_if_parseable": bool(conservative_parseable and critique_ns[0] > original_ns[0]),
                "D_original_if_parseable": original_ds[0] if len(original_ds) == 1 else np.nan,
                "N_original_if_parseable": original_ns[0] if len(original_ns) == 1 else np.nan,
                "D_replication_if_parseable": replication_ds[0] if len(replication_ds) == 1 else np.nan,
                "N_replication_if_parseable": critique_ns[0] if len(critique_ns) == 1 else np.nan,
                "decision": "candidate_not_promoted_duplicate_risk_and_narrative_alignment_needed"
                if conservative_parseable
                else "not_parseable_by_conservative_single_row_rule",
                "snippet": text[:600],
            }
        )
    return pd.DataFrame(rows)


def scan_rct_duplicate() -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    if not MIRROR_STATUS.exists():
        return pd.DataFrame()
    status = pd.read_csv(MIRROR_STATUS, sep="\t")
    subset = status[(status["candidate_key"].eq("rct_duplicate")) & (status["status"].eq("mirrored"))].copy()
    for _, mirror in subset.iterrows():
        path = ROOT / str(mirror["local_path"])
        try:
            data = pd.read_csv(path, sep=";")
            read_status = "read_ok"
        except Exception as exc:
            rows.append(
                {
                    "local_path": rel(path),
                    "read_status": "read_error",
                    "rows": 0,
                    "columns": "",
                    "has_effect_like_columns": False,
                    "has_n_like_columns": False,
                    "decision": "not_promoted_read_error",
                    "notes": clean_text(exc),
                }
            )
            continue
        columns = list(data.columns)
        has_effect = any(col.lower() in {"pe_95ci", "margin"} or "result" in col.lower() for col in columns)
        has_n = any(re.search(r"(?i)(^n$|sample|participants|cohort|eligible|rct_n|rwe_n)", col) for col in columns)
        rows.append(
            {
                "local_path": rel(path),
                "read_status": read_status,
                "rows": len(data),
                "columns": ",".join(columns),
                "has_effect_like_columns": has_effect,
                "has_n_like_columns": has_n,
                "decision": "not_promoted_no_public_n_columns" if has_effect and not has_n else "needs_review",
                "notes": "Public RCT-DUPLICATE CSV exposes ratio result strings/covariates but no clean original/RWE N columns.",
            }
        )
    return pd.DataFrame(rows)


def triage_rows(forrt: pd.DataFrame, rct: pd.DataFrame) -> pd.DataFrame:
    mirror = pd.read_csv(MIRROR_STATUS, sep="\t") if MIRROR_STATUS.exists() else pd.DataFrame()
    def mirrored_count(key: str) -> int:
        if mirror.empty:
            return 0
        return int(((mirror["candidate_key"] == key) & (mirror["status"] == "mirrored")).sum())

    forrt_parseable = int(forrt["conservative_parseable"].sum()) if not forrt.empty else 0
    forrt_larger = int(forrt["passes_larger_n_if_parseable"].sum()) if not forrt.empty else 0
    rct_no_n = int((rct["decision"] == "not_promoted_no_public_n_columns").sum()) if not rct.empty else 0
    rows = [
        {
            "candidate_key": "forrt_reversals",
            "candidate_name": "FORRT Replications and Reversals",
            "decision": "not_promoted_candidate_scan_only",
            "rows_promoted": 0,
            "mirrored_urls": mirrored_count("forrt_reversals"),
            "candidate_rows_found": forrt_parseable,
            "candidate_rows_passing_larger_n": forrt_larger,
            "notes": "HTML has narrative entries with some D/N-looking rows, but it overlaps heavily with FReD/current rows and needs dedupe plus field alignment before promotion.",
        },
        {
            "candidate_key": "rct_duplicate",
            "candidate_name": "RCT-DUPLICATE RWE emulations",
            "decision": "not_promoted_no_public_n_columns",
            "rows_promoted": 0,
            "mirrored_urls": mirrored_count("rct_duplicate"),
            "candidate_rows_found": 0,
            "candidate_rows_passing_larger_n": 0,
            "notes": f"Mirrored GitHub CSVs; {rct_no_n} result/covariate files lack clean original and RWE sample-size columns.",
        },
        {
            "candidate_key": "ying_pilot_full_scale",
            "candidate_name": "Ying/Ehrhardt pilot-to-full-scale datasets",
            "decision": "not_promoted_request_or_access_only",
            "rows_promoted": 0,
            "mirrored_urls": mirrored_count("ying_bmj_ebm") + mirrored_count("ying_dissertation") + mirrored_count("ying_jama_feasibility"),
            "candidate_rows_found": 0,
            "candidate_rows_passing_larger_n": 0,
            "notes": "DOI/JHU/JAMA routes were blocked or landing-only here; research suggests data are available on request rather than public D/N table.",
        },
        {
            "candidate_key": "rgb_health_behavior_family",
            "candidate_name": "Beets/von Klinggraeff RGB pilot-vs-larger-trial family",
            "decision": "not_promoted_no_public_master_table_mirrored",
            "rows_promoted": 0,
            "mirrored_urls": mirrored_count("beets_childhood_rgb") + mirrored_count("adult_obesity_rgb") + mirrored_count("health_behavior_rgb_pubmed") + mirrored_count("health_behavior_rgb_researchsquare"),
            "candidate_rows_found": 0,
            "candidate_rows_passing_larger_n": 0,
            "notes": "Articles/preprint pages confirm pair/effect counts, but this pass did not obtain a public master D/N workbook or CSV.",
        },
        {
            "candidate_key": "scaleup_reviews",
            "candidate_name": "Physical activity and nutrition scale-up reviews",
            "decision": "not_promoted_context_only",
            "rows_promoted": 0,
            "mirrored_urls": mirrored_count("scaleup_physical_activity") + mirrored_count("scaleup_nutrition"),
            "candidate_rows_found": 0,
            "candidate_rows_passing_larger_n": 0,
            "notes": "Scale-up comparisons are lower-yield and may violate same-estimand rules; no D/N table was promoted.",
        },
    ]
    return pd.DataFrame(rows)


def main() -> None:
    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    forrt = scan_forrt()
    forrt.to_csv(FORRT_SCAN_TSV, sep="\t", index=False)
    rct = scan_rct_duplicate()
    rct.to_csv(RCT_SCHEMA_TSV, sep="\t", index=False)
    triage = triage_rows(forrt, rct)
    triage.to_csv(TRIAGE_TSV, sep="\t", index=False)
    print(f"Wrote {TRIAGE_TSV}")
    print(f"Wrote {FORRT_SCAN_TSV}")
    print(f"Wrote {RCT_SCHEMA_TSV}")


if __name__ == "__main__":
    main()
