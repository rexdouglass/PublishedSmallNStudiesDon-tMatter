#!/usr/bin/env python3
"""Promote lab-level direct-replication rows from PSA-002 object orientation."""

from __future__ import annotations

import io
import math
import re
import time
from pathlib import Path

import numpy as np
import pandas as pd
import requests


ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = (
    ROOT
    / "data"
    / "raw"
    / "replication_projects"
    / "lead_harvest"
    / "psa_002_object_orientation"
)
CACHE_DIR = RAW_DIR / "component_sp_csvs"
PROMOTED = ROOT / "data" / "derived" / "replication_pairs" / "harvest" / "promoted"

NODE_IDS = ("waf48", "mnze8")
API_TIMEOUT = (20, 30)
FILE_TIMEOUT = (15, 20)

# The PSA Stage 1 proposal explicitly cites the original orientation-match effect
# as d = 0.13 for Stanfield & Zwaan (2001). The original sample size is set to 40
# based on secondary descriptions of the original experiment used in this lead pass.
ORIGINAL_D = 0.13
ORIGINAL_N = 40.0
ORIGINAL_TITLE = "Stanfield & Zwaan (2001) implied orientation match advantage"
ORIGINAL_DOI = "10.1111/1467-9280.00326"
REPLICATION_TITLE = "Chen et al. (2025) PSA-002 object-orientation replication"
REPLICATION_DOI = "10.1007/s12144-025-08304-x"


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def request_session() -> requests.Session:
    session = requests.Session()
    session.headers.update({"User-Agent": "PublishedSmallNStudiesLeadHarvester/1.0"})
    return session


def iter_osf_csvs(session: requests.Session, node_id: str) -> list[dict]:
    url = f"https://api.osf.io/v2/nodes/{node_id}/files/osfstorage/"
    rows: list[dict] = []
    while url:
        payload = session.get(url, timeout=API_TIMEOUT).json()
        for item in payload.get("data", []):
            attrs = item.get("attributes", {})
            name = attrs.get("name", "")
            if attrs.get("kind") == "file" and name.endswith(".csv") and "_SP_" in name:
                rows.append(
                    {
                        "name": name,
                        "download": item.get("links", {}).get("download", ""),
                        "node_id": node_id,
                    }
                )
        url = payload.get("links", {}).get("next")
    return rows


def download_if_missing(session: requests.Session, record: dict) -> Path:
    ensure_dir(CACHE_DIR)
    out = CACHE_DIR / record["name"]
    if out.exists() and out.stat().st_size > 0:
        return out

    last_exc: Exception | None = None
    for _ in range(3):
        try:
            response = session.get(record["download"], timeout=FILE_TIMEOUT)
            response.raise_for_status()
            out.write_bytes(response.content)
            return out
        except Exception as exc:  # pragma: no cover - network-retry guard
            last_exc = exc
            time.sleep(0.5)
    raise last_exc or RuntimeError(f"failed download: {record['name']}")


def normalize_lab_code(filename: str) -> str:
    lab = re.sub(r"_(SP|PP)_\d+\.csv$", "", filename)
    lab = lab.replace(".csv", "")
    lab = lab.replace("GRB-014", "GBR-014")
    lab = lab.replace("GBR_014", "GBR-014")
    lab = lab.replace("USA_173", "USA-173")
    return lab


def paired_d(diff: pd.Series) -> float:
    diff = pd.to_numeric(diff, errors="coerce").dropna().astype(float)
    if len(diff) < 2:
        return np.nan
    sd = diff.std(ddof=1)
    if not (np.isfinite(sd) and sd > 0):
        return np.nan
    return float(abs(diff.mean() / sd))


def parse_subject_file(path: Path) -> dict | None:
    df = pd.read_csv(path)
    required = {"Task", "Match", "correct", "avg_rt"}
    if not required.issubset(df.columns):
        return None

    verification = df.loc[df["Task"].eq("V")].copy()
    if verification.empty:
        return None

    verification["correct"] = pd.to_numeric(verification["correct"], errors="coerce")
    verification_accuracy = verification["correct"].mean()
    if not np.isfinite(verification_accuracy) or verification_accuracy < 0.70:
        return None

    critical = verification.loc[verification["Match"].isin(["Y", "N"])].copy()
    critical["avg_rt"] = pd.to_numeric(critical["avg_rt"], errors="coerce")
    critical = critical.loc[(critical["correct"] == 1) & critical["avg_rt"].notna()].copy()
    if critical.empty:
        return None

    by_match = critical.groupby("Match")["avg_rt"].median()
    if not {"Y", "N"}.issubset(by_match.index):
        return None

    return {
        "lab": normalize_lab_code(path.name),
        "file": path.name,
        "match_rt": float(by_match["Y"]),
        "mismatch_rt": float(by_match["N"]),
        "diff": float(by_match["N"] - by_match["Y"]),
    }


def build_rows(subject_rows: pd.DataFrame) -> list[dict]:
    out: list[dict] = []
    for lab, grp in subject_rows.groupby("lab", dropna=True):
        d_rep = paired_d(grp["diff"])
        if not np.isfinite(d_rep):
            continue
        out.append(
            {
                "source_dataset": "PSA-002 object orientation lab rows",
                "project": "Other direct replications",
                "pair_id": f"psa002_orientation_{lab.lower().replace('-', '_')}",
                "original_title": ORIGINAL_TITLE,
                "replication_title": REPLICATION_TITLE,
                "original_doi": ORIGINAL_DOI,
                "replication_doi": REPLICATION_DOI,
                "outcome": f"Sentence-picture orientation match advantage ({lab})",
                "D_original": ORIGINAL_D,
                "N_original": ORIGINAL_N,
                "D_replication": d_rep,
                "N_replication": float(len(grp)),
                "raw_file": str(CACHE_DIR),
                "match_author": "stanfield_zwaan_2001_implied_orientation",
            }
        )
    return out


def main() -> None:
    ensure_dir(PROMOTED)
    session = request_session()

    files: list[dict] = []
    for node_id in NODE_IDS:
        files.extend(iter_osf_csvs(session, node_id))

    subject_rows: list[dict] = []
    for record in files:
        try:
            local_path = download_if_missing(session, record)
            parsed = parse_subject_file(local_path)
            if parsed is not None:
                subject_rows.append(parsed)
        except Exception:
            continue

    subject_df = pd.DataFrame(subject_rows)
    rows = build_rows(subject_df) if not subject_df.empty else []
    out = pd.DataFrame(rows)
    out_path = PROMOTED / "psa_002_object_orientation__promoted_pairs.csv"
    out.to_csv(out_path, index=False)
    print(f"Wrote promoted rows: {len(out)}")
    print(f"Wrote file: {out_path}")


if __name__ == "__main__":
    main()
