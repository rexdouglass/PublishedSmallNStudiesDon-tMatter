#!/usr/bin/env python3
"""Promote Figure 1 rows from the second GPT candidate mining batch.

This pass only promotes candidates where locally mirrored source bytes expose
pair-level effect and N fields.  It currently promotes REPEAT Initiative primary
ratio-measure rows and records blockers for candidate mirrors that were checked
but did not expose a defensible D/N table in this pass.
"""

from __future__ import annotations

import math
import re
import zipfile
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RAW_BASE = (
    ROOT
    / "data"
    / "raw"
    / "replication_projects"
    / "lead_harvest"
    / "gpt_many_replication_candidates_20260504"
)
PROMOTED_DIR = ROOT / "data" / "derived" / "replication_pairs" / "harvest" / "promoted"
AUDIT_DIR = ROOT / "steps" / "corpus_results" / "figure1" / "gpt_candidate_pair_mining"

REPEAT_ZIP = RAW_BASE / "repeat_initiative" / "b669f1bbabd4__w64jq.bin"
REPEAT_PROMOTED = PROMOTED_DIR / "repeat_rwe_reproductions__promoted_pairs.csv"
AUDIT_TSV = AUDIT_DIR / "gpt_candidate_batch2_pair_mining.tsv"
STATUS_TSV = AUDIT_DIR / "gpt_candidate_batch2_mining_status.tsv"

HAGEN_GITHUB_ZIP = RAW_BASE / "hagen_hcsp" / "github_master.zip"
MANY_SMILES_ZIP = RAW_BASE / "many_smiles" / "data.zip"

RATIO_MEASURES = {"hazard ratio", "odds ratio", "rate ratio", "relative risk"}
REPEAT_REPLICATION_DOI = "10.1038/s41467-022-32310-3"


def clean_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and math.isnan(value):
        return ""
    text = str(value)
    if text.lower() in {"nan", "none", "null", "<na>"}:
        return ""
    return re.sub(r"[\t\r\n]+", " ", text).strip()


def slug(value: Any) -> str:
    text = clean_text(value).lower()
    text = text.replace("&", "and")
    text = re.sub(r"[^a-z0-9]+", "_", text)
    return text.strip("_")[:90]


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except Exception:
        return str(path)


def ratio_to_d(value: Any) -> float:
    x = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
    if not np.isfinite(x) or x <= 0:
        return np.nan
    return abs(float(math.log(float(x)) * math.sqrt(3) / math.pi))


def common_promoted_columns(df: pd.DataFrame) -> pd.DataFrame:
    cols = [
        "source_dataset",
        "project",
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
        "raw_file",
        "n_source_file",
        "verbatim_n_text_original",
        "verbatim_n_text_replication",
        "verbatim_effect_text_original",
        "verbatim_effect_text_replication",
        "d_n_transformation_note",
        "match_author",
    ]
    out = df.copy()
    for col in cols:
        if col not in out.columns:
            out[col] = ""
    return out[cols].copy()


def read_repeat_tables() -> tuple[pd.DataFrame, pd.DataFrame, str, str]:
    if not REPEAT_ZIP.exists():
        raise FileNotFoundError(REPEAT_ZIP)
    with zipfile.ZipFile(REPEAT_ZIP) as zf:
        outcomes_member = next(name for name in zf.namelist() if name.endswith("/outcomes.csv"))
        sample_member = next(name for name in zf.namelist() if name.endswith("/sample size.csv"))
        outcomes = pd.read_csv(zf.open(outcomes_member), encoding="latin1")
        sample_size = pd.read_csv(zf.open(sample_member), encoding="latin1")
    return outcomes, sample_size, outcomes_member, sample_member


def sample_size_lookup(sample_size: pd.DataFrame) -> dict[tuple[int, int], pd.Series]:
    lookup: dict[tuple[int, int], pd.Series] = {}
    for _, row in sample_size.iterrows():
        key = (int(row["studyid"]), int(row["matched"]))
        lookup[key] = row
    return lookup


def singleton_study_lookup(sample_size: pd.DataFrame) -> dict[int, pd.Series]:
    lookup: dict[int, pd.Series] = {}
    for studyid, group in sample_size.groupby("studyid"):
        if len(group) == 1:
            lookup[int(studyid)] = group.iloc[0]
    return lookup


def build_repeat_rows() -> tuple[pd.DataFrame, pd.DataFrame]:
    outcomes, sample_size, outcomes_member, sample_member = read_repeat_tables()
    selected = outcomes[
        outcomes["primary"].eq(1) & outcomes["measure_type"].astype(str).str.lower().isin(RATIO_MEASURES)
    ].copy()

    exact_lookup = sample_size_lookup(sample_size)
    fallback_lookup = singleton_study_lookup(sample_size)
    rows: list[dict[str, Any]] = []
    audit_rows: list[dict[str, Any]] = []

    for _, row in selected.iterrows():
        studyid = int(row["studyid"])
        matched = int(row["matched"])
        sample_row = exact_lookup.get((studyid, matched))
        n_match_method = "exact_studyid_matched"
        if sample_row is None:
            sample_row = fallback_lookup.get(studyid)
            n_match_method = "fallback_single_sample_size_row_for_studyid" if sample_row is not None else "missing_sample_size_row"
        if sample_row is None:
            continue

        original_n = pd.to_numeric(sample_row["original_percent_mean"], errors="coerce")
        reproduction_n = pd.to_numeric(sample_row["reproduction_percent_mean"], errors="coerce")
        original_effect = pd.to_numeric(row["original_pt_est"], errors="coerce")
        reproduction_effect = pd.to_numeric(row["reproduction_pt_est"], errors="coerce")
        if not (
            np.isfinite(original_n)
            and np.isfinite(reproduction_n)
            and np.isfinite(original_effect)
            and np.isfinite(reproduction_effect)
            and original_n >= 4
            and reproduction_n >= 4
            and original_effect > 0
            and reproduction_effect > 0
        ):
            continue

        outcome = clean_text(row.get("original_outcome_name"))
        measure_type = clean_text(row.get("measure_type"))
        pair_id = f"repeat_study_{studyid:03d}_matched_{matched}_{slug(outcome)}"
        source_locator = f"{outcomes_member}#studyid={studyid};matched={matched};primary=1"
        n_locator = f"{sample_member}#studyid={studyid};matched={int(sample_row['matched'])};match_method={n_match_method}"
        verbatim_effect_original = (
            f"outcomes.csv studyid={studyid}; matched={matched}; measure_type={measure_type}; "
            f"original_pt_est={original_effect}; original_lower_95={row.get('original_lower_95')}; "
            f"original_upper_95={row.get('original_upper_95')}; original_p_value={row.get('original_p_value')}"
        )
        verbatim_effect_replication = (
            f"outcomes.csv studyid={studyid}; matched={matched}; measure_type={measure_type}; "
            f"reproduction_pt_est={reproduction_effect}; reproduction_lower_95={row.get('reproduction_lower_95')}; "
            f"reproduction_upper_95={row.get('reproduction_upper_95')}; reproduction_p_value={row.get('reproduction_p_value')}"
        )
        verbatim_n_original = (
            f"sample size.csv studyid={studyid}; matched={int(sample_row['matched'])}; "
            f"original_percent_mean={original_n}; descriptive_or_comparator={clean_text(sample_row.get('descriptive_or_comparator'))}; "
            f"match_method={n_match_method}"
        )
        verbatim_n_replication = (
            f"sample size.csv studyid={studyid}; matched={int(sample_row['matched'])}; "
            f"reproduction_percent_mean={reproduction_n}; descriptive_or_comparator={clean_text(sample_row.get('descriptive_or_comparator'))}; "
            f"match_method={n_match_method}"
        )
        note = (
            "REPEAT reproduced published healthcare database studies using clinical practice data. "
            "Ratio measures were converted to a D-like scale with abs(log(ratio) * sqrt(3) / pi); "
            "sample sizes are from Supplementary Data 6 sample size.csv original_percent_mean and "
            "reproduction_percent_mean. Label as same-domain real-world-evidence reproduction, not "
            "a new-lab psychology-style replication."
        )
        promoted = {
            "source_dataset": "REPEAT Supplementary Data 6 outcomes and sample sizes",
            "project": "REPEAT real-world evidence reproductions",
            "pair_id": pair_id,
            "original_title": f"REPEAT original healthcare database study {studyid}",
            "replication_title": "Wang et al. 2022 REPEAT reproduction",
            "original_doi": "",
            "replication_doi": REPEAT_REPLICATION_DOI,
            "outcome": f"{outcome} ({measure_type})",
            "D_original": ratio_to_d(original_effect),
            "N_original": float(original_n),
            "D_replication": ratio_to_d(reproduction_effect),
            "N_replication": float(reproduction_n),
            "raw_file": f"{rel(REPEAT_ZIP)}::{source_locator}",
            "n_source_file": f"{rel(REPEAT_ZIP)}::{n_locator}",
            "verbatim_n_text_original": verbatim_n_original,
            "verbatim_n_text_replication": verbatim_n_replication,
            "verbatim_effect_text_original": verbatim_effect_original,
            "verbatim_effect_text_replication": verbatim_effect_replication,
            "d_n_transformation_note": note,
            "match_author": f"repeat_study_{studyid}",
        }
        rows.append(promoted)
        audit_rows.append(
            {
                **promoted,
                "candidate_name": "REPEAT Initiative - RWE Reproducibility",
                "decision": "promoted_ratio_measure_primary_rows",
                "measure_type": measure_type,
                "source_locator": source_locator,
                "n_source_locator": n_locator,
                "n_match_method": n_match_method,
                "native_original_effect": original_effect,
                "native_replication_effect": reproduction_effect,
                "native_effect_metric": measure_type,
            }
        )

    promoted_df = common_promoted_columns(pd.DataFrame(rows))
    audit_df = pd.DataFrame(audit_rows)
    return promoted_df, audit_df


def checked_candidate_status(repeat_rows: int) -> pd.DataFrame:
    rows = [
        {
            "candidate_key": "repeat_initiative",
            "candidate_name": "REPEAT Initiative",
            "decision": "promoted_to_result_table",
            "rows_promoted": repeat_rows,
            "local_mirror_status": "value_bearing_zip_mirrored",
            "working_urls_recorded": "https://osf.io/my5gn/ | https://www.nature.com/articles/s41467-022-32310-3",
            "local_paths": rel(REPEAT_ZIP),
            "notes": "Promoted primary HR/OR/RR/rate-ratio rows with original and reproduction sample sizes.",
        },
        {
            "candidate_key": "hagen_hcsp",
            "candidate_name": "Hagen Cumulative Science Project I",
            "decision": "blocked_access_route",
            "rows_promoted": 0,
            "local_mirror_status": "github_shiny_app_mirrored_google_sheet_deleted",
            "working_urls_recorded": "https://github.com/pandorica-opens/Hagen-Cumulative-Science-Project-I/archive/refs/heads/master.zip",
            "local_paths": rel(HAGEN_GITHUB_ZIP) if HAGEN_GITHUB_ZIP.exists() else "",
            "notes": "The mirrored Shiny app points to Google Sheets 1VBnEG... and 1f5QYC..., but both Google export routes returned file-deleted/410 in this environment.",
        },
        {
            "candidate_key": "many_smiles",
            "candidate_name": "Many Smiles Collaboration",
            "decision": "mirrored_context_not_promoted",
            "rows_promoted": 0,
            "local_mirror_status": "data_zip_mirrored",
            "working_urls_recorded": "https://osf.io/download/qd2s3/",
            "local_paths": rel(MANY_SMILES_ZIP) if MANY_SMILES_ZIP.exists() else "",
            "notes": "Mirrored data expose replication participant/source data, but this pass did not find a defensible original benchmark effect and original N table in the zip.",
        },
    ]
    return pd.DataFrame(rows)


def main() -> None:
    PROMOTED_DIR.mkdir(parents=True, exist_ok=True)
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)

    repeat_promoted, repeat_audit = build_repeat_rows()
    repeat_promoted.to_csv(REPEAT_PROMOTED, index=False)
    repeat_audit.to_csv(AUDIT_TSV, sep="\t", index=False)
    checked_candidate_status(len(repeat_promoted)).to_csv(STATUS_TSV, sep="\t", index=False)

    print(f"Wrote {len(repeat_promoted)} REPEAT promoted rows: {REPEAT_PROMOTED}")
    print(f"Wrote audit TSV: {AUDIT_TSV}")
    print(f"Wrote mining status TSV: {STATUS_TSV}")


if __name__ == "__main__":
    main()
