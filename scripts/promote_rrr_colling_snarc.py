#!/usr/bin/env python3
"""Promote Att-SNARC RRR rows from the local Colling et al. archive.

The Colling repository includes Fischer et al. original estimates as Cohen's
within-subject dz and the selected Model 1 multilevel fixed effects for the
replication. For the replication side, use |z| / sqrt(N) as a conservative
within-subject dz-compatible proxy from the reported fixed-effect z statistic.
"""

from __future__ import annotations

import math
import re
import subprocess
import tempfile
import zipfile
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RAW_ARCHIVE = (
    ROOT
    / "data"
    / "raw"
    / "replication_projects"
    / "lead_harvest"
    / "rrr_colling_2020"
    / "github_attentional_snarc"
    / "attentional_snarc-master.zip"
)
RAW_DIR = ROOT / "data" / "raw" / "replication_projects" / "lead_harvest" / "rrr_colling_2020"
PROMOTED_DIR = ROOT / "data" / "derived" / "replication_pairs" / "harvest" / "promoted"
SOURCE_TABLE = RAW_DIR / "colling_snarc_table_reconstruction.csv"
PROMOTED = PROMOTED_DIR / "rrr_colling_snarc__promoted_pairs.csv"

ORIGINAL_DOI = "10.1038/nn1066"
REPLICATION_DOI = "10.1177/2515245920903079"


R_EXTRACTOR = r"""
args <- commandArgs(trailingOnly = TRUE)
load(args[[1]])
aic <- fit.stats$AIC
idx <- which.min(aic[, "EAMMCS"])
model_name <- rownames(aic)[idx]
fe <- estimates$EAMMCS[[model_name]]$fe.estimates
out <- data.frame(
  condition = rownames(fe),
  replication_estimate_ms = fe[, "Estimate"],
  replication_se_ms = fe[, "SE"],
  replication_z = fe[, "Estimate"] / fe[, "SE"],
  selected_model = model_name,
  selected_model_aic = aic[idx, "EAMMCS"]
)
write.csv(out, args[[2]], row.names = FALSE)
"""


def delay_from_condition(value: object) -> int:
    match = re.search(r"d(\d+)", str(value))
    if not match:
        raise ValueError(f"Could not parse ISI delay from {value!r}")
    return int(match.group(1))


def extract_replication_fixed_effects(zip_path: Path) -> pd.DataFrame:
    with tempfile.TemporaryDirectory() as tmp:
        tmpdir = Path(tmp)
        rdata = tmpdir / "results1.Rdata"
        out_csv = tmpdir / "model1_fixed_effects.csv"
        with zipfile.ZipFile(zip_path) as zf:
            with zf.open("attentional_snarc-master/data/processed_rdata/results1.Rdata") as src:
                rdata.write_bytes(src.read())
        subprocess.run(["Rscript", "-e", R_EXTRACTOR, str(rdata), str(out_csv)], check=True)
        return pd.read_csv(out_csv)


def main() -> None:
    if not RAW_ARCHIVE.exists():
        raise FileNotFoundError(RAW_ARCHIVE)

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    PROMOTED_DIR.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(RAW_ARCHIVE) as zf:
        with zf.open("attentional_snarc-master/other_info/Original_estimates.csv") as src:
            original = pd.read_csv(src)
        with zf.open("attentional_snarc-master/data/meta_data/model1.meta.csv") as src:
            meta = pd.read_csv(src)

    original["delay"] = original["delay"].astype(int)
    rep = extract_replication_fixed_effects(RAW_ARCHIVE)
    rep["delay"] = rep["condition"].map(delay_from_condition)

    n_by_delay = (
        meta.assign(delay=meta["DependentVariable"].map(delay_from_condition))
        .groupby("delay", as_index=False)["Freq"]
        .sum()
        .rename(columns={"Freq": "replication_n"})
    )

    source = (
        original.merge(rep, on="delay", how="inner")
        .merge(n_by_delay, on="delay", how="left")
        .sort_values("delay")
        .reset_index(drop=True)
    )
    source["original_n"] = source["df"].astype(int) + 1
    source["original_dz_abs"] = source["dz"].abs()
    source["replication_dz_proxy_abs"] = source.apply(
        lambda r: abs(float(r["replication_z"])) / math.sqrt(float(r["replication_n"])),
        axis=1,
    )
    source["conversion_note"] = (
        "Original side uses the repository's Fischer et al. dz column. "
        "Replication side uses abs(fixed-effect z) / sqrt(N) from the selected Model 1 EAMMCS meta-analytic fixed effect."
    )

    source.to_csv(SOURCE_TABLE, index=False)

    promoted_rows = []
    for row in source.itertuples(index=False):
        promoted_rows.append(
            {
                "source_dataset": "RRR Colling 2020 Att-SNARC table reconstruction",
                "project": "Registered Replication Reports",
                "pair_id": f"rrr_colling_att_snarc_{int(row.delay)}ms",
                "original_title": "Fischer et al. (2003) perceiving numbers causes spatial shifts of attention",
                "replication_title": "Colling et al. (2020) Registered Replication Report on Fischer, Castel, Dodd, and Pratt (2003)",
                "original_doi": ORIGINAL_DOI,
                "replication_doi": REPLICATION_DOI,
                "outcome": f"Att-SNARC congruency effect at {int(row.delay)} ms ISI",
                "D_original": float(row.original_dz_abs),
                "N_original": int(row.original_n),
                "D_replication": float(row.replication_dz_proxy_abs),
                "N_replication": int(row.replication_n),
                "raw_file": str(SOURCE_TABLE),
                "match_author": f"fischer_2003_att_snarc_{int(row.delay)}ms",
            }
        )

    pd.DataFrame(promoted_rows).to_csv(PROMOTED, index=False)
    print(f"Wrote source reconstruction: {SOURCE_TABLE}")
    print(f"Wrote promoted rows: {PROMOTED}")


if __name__ == "__main__":
    main()
