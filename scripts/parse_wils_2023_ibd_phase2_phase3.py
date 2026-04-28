#!/usr/bin/env python3
"""Parse Wils 2023 IBD phase 2/3 treatment-arm response-rate tables.

The PMC supplement exposes phase 2 and phase 3 treatment-arm sample sizes and
success counts for clinical remission and response. These are not
active-versus-placebo contrasts, so the rows are staged as native response-rate
pairs rather than promoted to the current strict D-axis plot.
"""

from __future__ import annotations

import math
import re
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZipFile

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RAW = (
    ROOT
    / "data"
    / "raw"
    / "replication_projects"
    / "pilot_full_scale_inbound"
    / "wils_2023_ibd"
    / "UEG2-11-797-s002.docx"
)
STAGED = ROOT / "data" / "derived" / "replication_pairs" / "harvest" / "staged"
STAGE_PATH = STAGED / "wils_2023_ibd_phase2_phase3_response_rates__stage.csv"

NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}


def cell_text(cell: ET.Element) -> str:
    return " ".join(t.text for t in cell.findall(".//w:t", NS) if t.text).strip()


def rows_from_table(table: ET.Element) -> list[list[str]]:
    return [[cell_text(tc) for tc in tr.findall("./w:tc", NS)] for tr in table.findall("./w:tr", NS)]


def first_int(value: str) -> int | None:
    match = re.search(r"\d+", str(value))
    return int(match.group(0)) if match else None


def slug(value: str) -> str:
    out = re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")
    return out or "unknown"


def logit_rate(successes: int, total: int) -> float:
    failures = total - successes
    return math.log(successes / failures)


def parse() -> pd.DataFrame:
    with ZipFile(RAW) as zf:
        root = ET.fromstring(zf.read("word/document.xml"))

    tables = root.findall(".//w:tbl", NS)
    configs = {
        2: "all_phase3_matches",
        3: "one_to_one_sensitivity",
    }

    rows: list[dict[str, object]] = []
    for table_index, analysis_set in configs.items():
        current_drug = ""
        current_phase2_n: int | None = None
        current_phase2 = {
            "clinical_remission": (None, None),
            "clinical_response": (None, None),
        }

        for row_index, row in enumerate(rows_from_table(tables[table_index])):
            if row_index < 2 or not row:
                continue
            if row[0].startswith("Total number"):
                continue

            if row[0]:
                current_drug = row[0]
            if len(row) > 1 and row[1]:
                current_phase2_n = first_int(row[1])

            phase3_label = row[2] if len(row) > 2 else ""
            phase3_n = first_int(phase3_label)
            if not current_drug or current_phase2_n is None or phase3_n is None:
                continue

            outcome_slots = {
                "clinical_remission": (3, 4, 5, 6),
                "clinical_response": (7, 8, 9, 10),
            }

            for outcome, (p2_pct_i, p2_success_i, p3_pct_i, p3_success_i) in outcome_slots.items():
                phase2_success = first_int(row[p2_success_i]) if len(row) > p2_success_i and row[p2_success_i] else None
                phase2_pct = first_int(row[p2_pct_i]) if len(row) > p2_pct_i and row[p2_pct_i] else None
                if phase2_success is not None:
                    current_phase2[outcome] = (phase2_pct, phase2_success)
                else:
                    phase2_pct, phase2_success = current_phase2[outcome]

                phase3_success = first_int(row[p3_success_i]) if len(row) > p3_success_i and row[p3_success_i] else None
                phase3_pct = first_int(row[p3_pct_i]) if len(row) > p3_pct_i and row[p3_pct_i] else None
                if phase2_success is None or phase3_success is None:
                    continue

                rows.append(
                    {
                        "source_dataset": "Wils 2023 IBD phase II/III",
                        "source_paper": "Wils et al. 2023 UEG Journal supplement Table S1",
                        "pair_id": f"wils_2023_{analysis_set}_{slug(current_drug)}_{slug(phase3_label)}_{outcome}",
                        "analysis_set": analysis_set,
                        "drug_trial": current_drug,
                        "phase3_trial_label": phase3_label,
                        "outcome": outcome,
                        "N_original": current_phase2_n,
                        "N_replication": phase3_n,
                        "phase2_successes": phase2_success,
                        "phase3_successes": phase3_success,
                        "phase2_response_rate": phase2_success / current_phase2_n,
                        "phase3_response_rate": phase3_success / phase3_n,
                        "phase2_percent_reported": phase2_pct,
                        "phase3_percent_reported": phase3_pct,
                        "native_effect_metric": "treatment_arm_logit_response_rate",
                        "native_effect_original": logit_rate(phase2_success, current_phase2_n),
                        "native_effect_replication": logit_rate(phase3_success, phase3_n),
                        "D_original": None,
                        "D_replication": None,
                        "promotion_decision": "stage_native_metric",
                        "analytic_status": "native_treatment_arm_response_rate_not_treatment_contrast",
                        "landing_url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC10576605/",
                        "source_urls": "https://pmc.ncbi.nlm.nih.gov/articles/PMC10576605/ | https://pmc.ncbi.nlm.nih.gov/articles/instance/10576605/bin/UEG2-11-797-s002.docx",
                        "raw_file": str(RAW),
                        "table_index_zero_based": table_index,
                        "table_row_index": row_index,
                        "notes": "Staged only: the table compares treatment-arm response rates across phase 2 and phase 3 trials, not active-vs-placebo effects.",
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
