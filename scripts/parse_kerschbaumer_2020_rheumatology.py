#!/usr/bin/env python3
"""Parse Kerschbaumer 2020 phase-2/phase-3 rheumatology response tables.

The source PDF supplement has matched phase 2 and phase 3 ACR responder
counts.  This script writes a broad staged table with all extracted ACR20,
ACR50, and ACR70 response-rate rows, plus a conservative promoted table for
ACR20 active-vs-placebo treatment effects when a same-family placebo row can
be matched in both phases.
"""

from __future__ import annotations

import math
import re
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw" / "replication_projects" / "pilot_full_scale_inbound"
PDF_PATH = RAW_DIR / "kerschbaumer_2020_natmed_supp.pdf"
STAGED = ROOT / "data" / "derived" / "replication_pairs" / "harvest" / "staged"
PROMOTED = ROOT / "data" / "derived" / "replication_pairs" / "harvest" / "promoted"
STAGE_PATH = STAGED / "kerschbaumer_2020_rheumatology_phase2_phase3__stage.csv"
PROMOTED_PATH = PROMOTED / "kerschbaumer_2020_rheumatology_phase2_phase3_acr20__promoted_pairs.csv"

SOURCE_DATASET = "Kerschbaumer 2020 rheumatology phase II/III"
PROJECT = "Clinical phase II to phase III pairs"
LANDING_URL = "https://www.nature.com/articles/s41591-020-0833-4"
SUPPLEMENT_URL = (
    "https://static-content.springer.com/esm/art%3A10.1038%2Fs41591-020-0833-4/"
    "MediaObjects/41591_2020_833_MOESM1_ESM.pdf"
)

FRACTION_RE = re.compile(r"(?<!\d)(\d+)\s*/\s*(\d+)")


def clean_text(value: object) -> str:
    if value is None:
        return ""
    text = str(value).replace("\n", " ")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def slugify(value: object) -> str:
    text = clean_text(value).lower()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    return text.strip("_") or "missing"


def first_fraction(cells: list[object], start: int, stop: int) -> tuple[int, int] | None:
    for cell in cells[start:stop]:
        text = clean_text(cell)
        match = FRACTION_RE.search(text)
        if match:
            return int(match.group(1)), int(match.group(2))
    return None


def fraction_slots(row: list[object]) -> dict[str, dict[str, tuple[int, int] | None]]:
    """Return endpoint -> phase -> responder/denominator tuple."""

    width = len(row)
    if width >= 33:
        ranges = {
            "ACR20": {"phase2": (15, 18), "phase3": (18, 21)},
            "ACR50": {"phase2": (21, 24), "phase3": (24, 27)},
            "ACR70": {"phase2": (27, 30), "phase3": (30, 33)},
        }
    else:
        ranges = {
            "ACR20": {"phase2": (11, 14), "phase3": (14, 17)},
            "ACR50": {"phase2": (17, 20), "phase3": (20, 23)},
            "ACR70": {"phase2": (23, 26), "phase3": (26, 29)},
        }
    return {
        endpoint: {
            phase: first_fraction(row, start, min(stop, width))
            for phase, (start, stop) in endpoint_ranges.items()
        }
        for endpoint, endpoint_ranges in ranges.items()
    }


def row_text(row: list[object], start: int, stop: int) -> str:
    return clean_text(" ".join(clean_text(cell) for cell in row[start:stop] if clean_text(cell)))


def regimen_fragment(row: list[object]) -> str:
    return row_text(row, 0, min(3, len(row)))


def phase2_study(row: list[object]) -> str:
    if len(row) >= 33:
        return row_text(row, 3, 7)
    return row_text(row, 3, 7)


def phase3_study(row: list[object]) -> str:
    if len(row) >= 33:
        return row_text(row, 8, 13)
    return row_text(row, 7, 11)


def has_any_fraction(slots: dict[str, dict[str, tuple[int, int] | None]]) -> bool:
    return any(value is not None for endpoint in slots.values() for value in endpoint.values())


def is_percentage_only(row: list[object]) -> bool:
    text = row_text(row, 0, len(row))
    return bool(text) and not FRACTION_RE.search(text) and "%" in text


def family_key(regimen: str) -> str:
    tokens = re.findall(r"[A-Za-z]+", regimen)
    if not tokens:
        return ""
    return tokens[0].lower()


def background_key(regimen: str) -> str:
    text = clean_text(regimen).lower()
    fam = family_key(text)
    if fam:
        text = re.sub(rf"^{re.escape(fam)}\b", "", text).strip()
    text = re.sub(r"\bplacebo\b", "", text)
    text = re.sub(r"\b\d+(?:\.\d+)?\s*(?:mg/kg|mg|mcg|g)\b", "", text)
    text = re.sub(r"\b(?:qd|bid|biw|qw|q2w|q4w)\b", "", text)
    text = re.sub(r"\b\d+(?:\.\d+)?\b", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip(" +-") or "none"


def study_key(study: str) -> str:
    text = clean_text(study).lower()
    text = re.sub(r"\b\d{2,4}\b", " ", text)
    text = re.sub(r"[^a-z]+", " ", text)
    tokens = [tok for tok in text.split() if tok not in {"a", "b"}]
    return " ".join(tokens[:3])


def odds_ratio_to_d_from_counts(
    responders_active: int,
    n_active: int,
    responders_control: int,
    n_control: int,
) -> float:
    non_active = n_active - responders_active
    non_control = n_control - responders_control
    cells = [responders_active, non_active, responders_control, non_control]
    if min(cells) < 0:
        return math.nan
    # Haldane-Anscombe correction only when a cell is zero.
    if min(cells) == 0:
        responders_active += 0.5
        non_active += 0.5
        responders_control += 0.5
        non_control += 0.5
    odds_ratio = (responders_active * non_control) / (non_active * responders_control)
    return abs(math.log(odds_ratio)) * math.sqrt(3) / math.pi


def extract_rows() -> pd.DataFrame:
    try:
        import pdfplumber
    except ModuleNotFoundError as exc:
        raise SystemExit(
            "pdfplumber is required. In this repo, run with `.venv/bin/python "
            "scripts/parse_kerschbaumer_2020_rheumatology.py`."
        ) from exc

    records: list[dict[str, object]] = []

    # pdfplumber uses zero-based page indexes. These are the pages containing
    # Table S4 (rheumatoid arthritis) and Table S5 (psoriatic arthritis).
    page_specs = [
        (14, "rheumatoid_arthritis"),
        (15, "rheumatoid_arthritis"),
        (16, "rheumatoid_arthritis"),
        (17, "rheumatoid_arthritis"),
        (18, "psoriatic_arthritis"),
    ]

    current: dict[str, object] | None = None
    last_created_indexes: list[int] = []

    with pdfplumber.open(PDF_PATH) as pdf:
        for page_index, disease in page_specs:
            tables = pdf.pages[page_index].extract_tables()
            if not tables:
                continue
            table = tables[0]
            for row_index, row in enumerate(table):
                row = list(row)
                if any(clean_text(cell).lower() in {"regimen", "study"} for cell in row[:5]):
                    continue
                slots = fraction_slots(row)
                fragment = regimen_fragment(row)

                if not has_any_fraction(slots):
                    if fragment:
                        for rec_index in last_created_indexes:
                            records[rec_index]["regimen"] = clean_text(
                                f"{records[rec_index]['regimen']} {fragment}"
                            )
                        if current is not None:
                            current["regimen"] = clean_text(f"{current['regimen']} {fragment}")
                    continue

                p2_study = phase2_study(row)
                p3_study = phase3_study(row)
                if fragment:
                    regimen = fragment
                elif current is not None:
                    regimen = str(current["regimen"])
                else:
                    regimen = "unknown_regimen"

                # Update phase-2 context when this row exposes phase-2 counts.
                p2_counts = {
                    endpoint: values["phase2"]
                    for endpoint, values in slots.items()
                    if values["phase2"] is not None
                }
                if p2_counts:
                    current = {
                        "regimen": regimen,
                        "phase2_study": p2_study,
                        "phase2_counts": p2_counts,
                    }

                last_created_indexes = []
                for endpoint, values in slots.items():
                    phase2 = values["phase2"]
                    phase3 = values["phase3"]
                    if phase2 is None and current is not None:
                        phase2 = dict(current["phase2_counts"]).get(endpoint)
                        p2_study = str(current.get("phase2_study") or p2_study)
                        regimen = str(current.get("regimen") or regimen)
                    if phase2 is None or phase3 is None:
                        continue

                    phase2_resp, phase2_n = phase2
                    phase3_resp, phase3_n = phase3
                    record = {
                        "source_dataset": SOURCE_DATASET,
                        "source_paper": "Kerschbaumer et al. 2020 Nature Medicine supplement Tables S4/S5",
                        "disease": disease,
                        "regimen": clean_text(regimen),
                        "endpoint": endpoint,
                        "phase2_study": clean_text(p2_study),
                        "phase3_study": clean_text(p3_study),
                        "phase2_study_key": study_key(p2_study),
                        "phase3_study_key": study_key(p3_study),
                        "phase2_responders": phase2_resp,
                        "phase2_n": phase2_n,
                        "phase3_responders": phase3_resp,
                        "phase3_n": phase3_n,
                        "phase2_response_rate": phase2_resp / phase2_n,
                        "phase3_response_rate": phase3_resp / phase3_n,
                        "family_key": family_key(regimen),
                        "background_key": background_key(regimen),
                        "is_placebo_row": "placebo" in clean_text(regimen).lower(),
                        "landing_url": LANDING_URL,
                        "source_urls": f"{LANDING_URL} | {SUPPLEMENT_URL}",
                        "raw_file": str(PDF_PATH),
                        "page_index_zero_based": page_index,
                        "table_row_index": row_index,
                    }
                    records.append(record)
                    last_created_indexes.append(len(records) - 1)

    out = pd.DataFrame(records)
    if not out.empty:
        out["regimen"] = out["regimen"].map(clean_text)
        out["family_key"] = out["regimen"].map(family_key)
        out["background_key"] = out["regimen"].map(background_key)
        out["is_placebo_row"] = out["regimen"].str.lower().str.contains("placebo", na=False)
        out["phase2_study_key"] = out["phase2_study"].map(study_key)
        out["phase3_study_key"] = out["phase3_study"].map(study_key)
    return out


def build_promoted(stage_df: pd.DataFrame) -> pd.DataFrame:
    acr20 = stage_df.loc[stage_df["endpoint"].eq("ACR20")].copy()
    placebos = acr20.loc[acr20["is_placebo_row"]].copy()
    active = acr20.loc[~acr20["is_placebo_row"]].copy()

    rows: list[dict[str, object]] = []
    for _, row in active.iterrows():
        candidates = placebos.loc[
            placebos["disease"].eq(row["disease"])
            & placebos["family_key"].eq(row["family_key"])
            & placebos["background_key"].eq(row["background_key"])
            & placebos["phase2_study_key"].eq(row["phase2_study_key"])
            & placebos["phase3_study_key"].eq(row["phase3_study_key"])
        ]
        if candidates.empty:
            candidates = placebos.loc[
                placebos["disease"].eq(row["disease"])
                & placebos["family_key"].eq(row["family_key"])
                & placebos["background_key"].eq(row["background_key"])
                & placebos["phase3_study_key"].eq(row["phase3_study_key"])
            ]
        if candidates.empty:
            continue
        placebo = candidates.iloc[0]

        n_original = int(row["phase2_n"] + placebo["phase2_n"])
        n_replication = int(row["phase3_n"] + placebo["phase3_n"])
        if n_replication <= n_original:
            continue

        d_original = odds_ratio_to_d_from_counts(
            int(row["phase2_responders"]),
            int(row["phase2_n"]),
            int(placebo["phase2_responders"]),
            int(placebo["phase2_n"]),
        )
        d_replication = odds_ratio_to_d_from_counts(
            int(row["phase3_responders"]),
            int(row["phase3_n"]),
            int(placebo["phase3_responders"]),
            int(placebo["phase3_n"]),
        )
        if not (math.isfinite(d_original) and math.isfinite(d_replication)):
            continue

        pair_slug = slugify(f"{row['disease']}_{row['regimen']}_{row['phase3_study']}_acr20")
        rows.append(
            {
                "source_dataset": SOURCE_DATASET,
                "project": PROJECT,
                "pair_id": f"kerschbaumer_2020_{pair_slug}",
                "original_title": f"Phase 2 {row['disease']} trial: {row['regimen']} versus {placebo['regimen']}",
                "replication_title": f"Phase 3 {row['disease']} trial: {row['regimen']} versus {placebo['regimen']}",
                "original_doi": "",
                "replication_doi": "",
                "outcome": "ACR20 responder odds for active regimen versus matched placebo/control row",
                "D_original": d_original,
                "N_original": n_original,
                "D_replication": d_replication,
                "N_replication": n_replication,
                "raw_file": str(STAGE_PATH),
                "match_author": pair_slug,
                "notes": (
                    f"Phase 2 counts: active {int(row['phase2_responders'])}/{int(row['phase2_n'])}, "
                    f"control {int(placebo['phase2_responders'])}/{int(placebo['phase2_n'])}. "
                    f"Phase 3 counts: active {int(row['phase3_responders'])}/{int(row['phase3_n'])}, "
                    f"control {int(placebo['phase3_responders'])}/{int(placebo['phase3_n'])}. "
                    "D values use Chinn log(OR)*sqrt(3)/pi. Extracted from Kerschbaumer 2020 supplement."
                ),
            }
        )
    return pd.DataFrame(rows)


def main() -> None:
    STAGED.mkdir(parents=True, exist_ok=True)
    PROMOTED.mkdir(parents=True, exist_ok=True)

    stage_df = extract_rows()
    promoted_df = build_promoted(stage_df)

    stage_df.to_csv(STAGE_PATH, index=False)
    promoted_df.to_csv(PROMOTED_PATH, index=False)

    print(f"Wrote staged rows: {len(stage_df)} -> {STAGE_PATH}")
    print(f"Wrote promoted ACR20 rows: {len(promoted_df)} -> {PROMOTED_PATH}")


if __name__ == "__main__":
    main()
