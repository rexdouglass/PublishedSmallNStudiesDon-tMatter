#!/usr/bin/env python3
"""Parse Li 2024 PD-1/PD-L1 early-phase/phase-III ORR pairs.

Supplementary Table 1 gives matched early-phase and phase-III objective
response-rate rows with responder/total counts. These are one-arm ORR values,
not randomized treatment effects, so they are staged as a native oncology
response-rate lane rather than promoted to the strict D-axis plot.
"""

from __future__ import annotations

import math
import re
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = (
    ROOT
    / "data"
    / "raw"
    / "replication_projects"
    / "pilot_full_scale_inbound"
    / "li_2024_pd1_pdl1"
)
PDF_PATH = RAW_DIR / "inline-supplementary-material-3.pdf"
STAGED = ROOT / "data" / "derived" / "replication_pairs" / "harvest" / "staged"
STAGE_PATH = STAGED / "li_2024_pd1_pdl1_phase2_phase3_orr__stage.csv"

LANDING_URL = "https://jitc.bmj.com/content/12/1/e007959"
SUPPLEMENT_URL = (
    "https://jitc.bmj.com/content/jitc/12/1/e007959/DC3/"
    "embed/inline-supplementary-material-3.pdf?download=true"
)

FRACTION_RE = re.compile(r"^\s*(\d+)\s*/\s*(\d+)\s*$")
PERCENT_RE = re.compile(r"^\s*(\d+(?:\.\d+)?)\s*%\s*$")


def clean(value: object) -> str:
    if value is None:
        return ""
    text = str(value).replace("\n", " ")
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"\s+([),])", r"\1", text)
    text = re.sub(r"([(+/])\s+", r"\1", text)
    return text.strip()


def slug(value: object) -> str:
    text = clean(value).lower()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    return text.strip("_") or "unknown"


def parse_fraction(value: str) -> tuple[int, int] | None:
    match = FRACTION_RE.match(clean(value))
    if not match:
        return None
    return int(match.group(1)), int(match.group(2))


def parse_percent(value: str) -> float | None:
    match = PERCENT_RE.match(clean(value))
    if not match:
        return None
    return float(match.group(1)) / 100


def logit_rate(responders: int, total: int) -> float:
    failures = total - responders
    if failures < 0:
        return math.nan
    # Haldane-Anscombe correction only for boundary rates.
    if responders == 0 or failures == 0:
        return math.log((responders + 0.5) / (failures + 0.5))
    return math.log(responders / failures)


def append_continuation(previous: dict[str, object], row: list[str]) -> None:
    """Patch the one row split over pages in the PDF table."""

    append_map = {
        "regimen": 0,
        "phase2_study": 4,
        "phase2_assessing_criteria": 7,
        "phase3_study": 8,
        "phase3_assessing_criteria": 11,
    }
    for field, index in append_map.items():
        if index < len(row) and clean(row[index]):
            previous[field] = clean(f"{previous[field]} {clean(row[index])}")


def parse() -> pd.DataFrame:
    try:
        import pdfplumber
    except ModuleNotFoundError as exc:
        raise SystemExit(
            "pdfplumber is required. Run with `.venv/bin/python "
            "scripts/parse_li_2024_pd1_pdl1_phase_pairs.py`."
        ) from exc

    rows: list[dict[str, object]] = []

    with pdfplumber.open(PDF_PATH) as pdf:
        for page_index in range(3):
            table = pdf.pages[page_index].extract_tables()[0]
            for table_row_index, raw_row in enumerate(table):
                row = [clean(cell) for cell in raw_row]
                if not row or row[0] == "Regimen" or row[4] == "Phase2":
                    continue

                phase2_counts = parse_fraction(row[6] if len(row) > 6 else "")
                phase3_counts = parse_fraction(row[10] if len(row) > 10 else "")
                if phase2_counts is None or phase3_counts is None:
                    if rows and clean(row[0]) and not any(clean(x) for x in row[1:4]):
                        append_continuation(rows[-1], row)
                    continue

                phase2_responders, phase2_total = phase2_counts
                phase3_responders, phase3_total = phase3_counts
                phase2_rate = phase2_responders / phase2_total
                phase3_rate = phase3_responders / phase3_total
                phase2_pct = parse_percent(row[5])
                phase3_pct = parse_percent(row[9])

                pair_id = "_".join(
                    [
                        "li_2024",
                        slug(row[0]),
                        slug(row[1]),
                        slug(row[2]),
                        slug(row[3]),
                        slug(row[4]),
                        slug(row[8]),
                    ]
                )

                rows.append(
                    {
                        "source_dataset": "Li 2024 PD-1/PD-L1 phase II/III oncology",
                        "source_paper": "Li et al. 2024 J Immunother Cancer supplementary Table 1",
                        "pair_id": pair_id,
                        "regimen": row[0],
                        "cancer_type": row[1],
                        "line": row[2],
                        "biomarker": row[3],
                        "phase2_study": row[4],
                        "phase3_study": row[8],
                        "outcome": "objective_response_rate",
                        "N_original": phase2_total,
                        "N_replication": phase3_total,
                        "phase2_responders": phase2_responders,
                        "phase3_responders": phase3_responders,
                        "phase2_nonresponders": phase2_total - phase2_responders,
                        "phase3_nonresponders": phase3_total - phase3_responders,
                        "phase2_orr": phase2_rate,
                        "phase3_orr": phase3_rate,
                        "phase2_percent_reported": phase2_pct,
                        "phase3_percent_reported": phase3_pct,
                        "phase2_assessing_criteria": row[7],
                        "phase3_assessing_criteria": row[11],
                        "native_effect_metric": "one_arm_logit_objective_response_rate",
                        "native_effect_original": logit_rate(phase2_responders, phase2_total),
                        "native_effect_replication": logit_rate(phase3_responders, phase3_total),
                        "orr_difference_original_minus_replication": phase2_rate - phase3_rate,
                        "D_original": None,
                        "D_replication": None,
                        "promotion_decision": "stage_native_metric",
                        "analytic_status": "native_one_arm_orr_not_randomized_treatment_contrast",
                        "landing_url": LANDING_URL,
                        "source_urls": f"{LANDING_URL} | {SUPPLEMENT_URL}",
                        "raw_file": str(PDF_PATH),
                        "page_index_zero_based": page_index,
                        "table_row_index": table_row_index,
                        "notes": (
                            "Staged only: matched early-phase/phase-III ORR responder counts, "
                            "but ORR is a one-arm oncology activity metric rather than a "
                            "randomized active-vs-control treatment effect."
                        ),
                    }
                )

    return pd.DataFrame(rows)


def main() -> None:
    STAGED.mkdir(parents=True, exist_ok=True)
    df = parse()
    df.to_csv(STAGE_PATH, index=False)
    print(f"Wrote staged rows: {len(df)} -> {STAGE_PATH}")


if __name__ == "__main__":
    main()
