#!/usr/bin/env python3
"""Promote communication-privacy original/replication SEM path rows."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
PROMOTED = ROOT / "data" / "derived" / "replication_pairs" / "harvest" / "promoted"
RAW_DIR = ROOT / "data" / "raw" / "replication_projects" / "lead_harvest" / "communication_privacy_2025"


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def build_rows() -> list[dict]:
    rows: list[dict] = []

    # Study 1 / Krasnova: the harvested OSF payload is missing the original
    # `3-1_study1_krasnovaetal.r` script, but the saved `results1` specr object
    # contains one pure study-1 path under the default "all" / "no covariates"
    # specification. Promote only that directly matched path.
    rows.append(
        {
            "source_dataset": "Communication privacy SEM/spec-curve paths",
            "project": "Other direct replications",
            "pair_id": "communication_privacy_krasnova_self_disclosure_01",
            "original_title": "Krasnova et al. (2010) privacy calculus SEM path",
            "replication_title": "Privacy calculus/privacy paradox/context collapse replication (Krasnova spec-curve row)",
            "original_doi": "10.1057/JIT.2010.6",
            "replication_doi": "10.1093/joc/jqaf007",
            "outcome": "privacy risks → self-disclosure (no covariates, all-sample spec-curve row)",
            "D_original": 0.460,
            "N_original": 259.0,
            "D_replication": 0.644,
            "N_replication": 796.0,
            "raw_file": str(RAW_DIR / "manual__results1.Rdata"),
            "match_author": "krasnova_privacy_calculus_paths",
        }
    )

    study2_paths = [
        ("privacy setting → disclosure", 0.07, 0.136, "amount_of_disclosure"),
        ("privacy concerns → disclosure", -0.28, 0.362, "amount_of_disclosure"),
        ("audience → disclosure", 0.18, 0.026, "amount_of_disclosure"),
        ("disclosure → social capital", 0.25, 0.548, "amount_of_disclosure"),
        ("audience → social capital", 0.16, 0.239, "amount_of_disclosure"),
        ("audience → privacy setting", 0.15, 0.163, "amount_of_disclosure"),
        ("privacy setting → disclosure", 0.13, 0.043, "intentional_disclosure"),
        ("privacy concerns → disclosure", -0.11, 0.356, "intentional_disclosure"),
        ("audience → disclosure", 0.12, 0.215, "intentional_disclosure"),
        ("disclosure → social capital", 0.29, 0.509, "intentional_disclosure"),
        ("audience → social capital", 0.17, 0.165, "intentional_disclosure"),
        ("audience → privacy setting", 0.15, 0.181, "intentional_disclosure"),
    ]
    for i, (path_label, orig, rep, model) in enumerate(study2_paths, start=1):
        rows.append(
            {
                "source_dataset": "Communication privacy SEM paths",
                "project": "Other direct replications",
                "pair_id": f"communication_privacy_vitak_{model}_{i:02d}",
                "original_title": "Vitak (2012) context collapse/privacy SEM path",
                "replication_title": "Privacy calculus/privacy paradox/context collapse replication (Vitak model)",
                "original_doi": "10.1080/08838151.2012.732140",
                "replication_doi": "10.1093/joc/jqaf007",
                "outcome": f"{model}: {path_label}",
                "D_original": abs(float(orig)),
                "N_original": 364.0,
                "D_replication": abs(float(rep)),
                "N_replication": 797.0,
                "raw_file": str(RAW_DIR / "osf_05__3-2_study2_vitak.R"),
                "match_author": "vitak_context_collapse_paths",
            }
        )

    study3_paths = [
        ("Informational Privacy", "intention → behavior", 0.65, 0.768),
        ("Informational Privacy", "attitudes → behavior", 0.11, 0.133),
        ("Informational Privacy", "attitudes → intention", 0.68, 0.708),
        ("Informational Privacy", "concerns → attitudes", 0.42, 0.117),
        ("Informational Privacy", "ind1", 0.44, 0.544),
        ("Informational Privacy", "ind2", 0.23, 0.079),
        ("Social Privacy", "intention → behavior", 0.45, 0.734),
        ("Social Privacy", "attitudes → behavior", 0.20, 0.061),
        ("Social Privacy", "attitudes → intention", 0.61, 0.348),
        ("Social Privacy", "concerns → attitudes", 0.33, 0.153),
        ("Social Privacy", "ind1", 0.28, 0.256),
        ("Social Privacy", "ind2", 0.16, 0.048),
        ("Psychological Privacy", "intention → behavior", 0.79, 1.012),
        ("Psychological Privacy", "attitudes → behavior", 0.08, -0.060),
        ("Psychological Privacy", "attitudes → intention", 0.58, 0.711),
        ("Psychological Privacy", "concerns → attitudes", 0.25, 0.038),
        ("Psychological Privacy", "ind1", 0.46, 0.719),
        ("Psychological Privacy", "ind2", 0.14, 0.025),
    ]
    for i, (model, path_label, orig, rep) in enumerate(study3_paths, start=1):
        rows.append(
            {
                "source_dataset": "Communication privacy SEM paths",
                "project": "Other direct replications",
                "pair_id": f"communication_privacy_dienlin_{model.lower().replace(' ', '_')}_{i:02d}",
                "original_title": "Dienlin & Trepte (2015) privacy paradox SEM path",
                "replication_title": "Privacy calculus/privacy paradox/context collapse replication (Dienlin & Trepte model)",
                "original_doi": "10.1002/ejsp.2040",
                "replication_doi": "10.1093/joc/jqaf007",
                "outcome": f"{model}: {path_label}",
                "D_original": abs(float(orig)),
                "N_original": 595.0,
                "D_replication": abs(float(rep)),
                "N_replication": 797.0,
                "raw_file": str(RAW_DIR / "osf_06__3-3_study3_dienlintrepte.R"),
                "match_author": "dienlin_trepte_privacy_paths",
            }
        )

    return rows


def main() -> None:
    ensure_dir(PROMOTED)
    out = pd.DataFrame(build_rows())
    out_path = PROMOTED / "communication_privacy_paths__promoted_pairs.csv"
    out.to_csv(out_path, index=False)
    print(f"Wrote promoted rows: {len(out)}")
    print(f"Wrote file: {out_path}")


if __name__ == "__main__":
    main()
