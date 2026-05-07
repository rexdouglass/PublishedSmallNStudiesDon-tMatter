#!/usr/bin/env python3
"""Record the automatically extractable Azar dishonesty replication values.

The original full article remains paywalled/blocked in this automatic pass, so
the original D below is not a fresh extraction from the original PDF. It is a
transparent inference from the mirrored replication paper's power statement:
the authors say 214 observations were enough to test 50% of the original effect
size, i.e. d = .403. The implied original d is therefore 2 * .403 = .806.
"""

from __future__ import annotations

import csv
import hashlib
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = (
    ROOT
    / "data"
    / "raw"
    / "replication_projects"
    / "individual_auto_mining_blockers"
    / "api_candidate_c90e8b5ff29bcd78"
)
OUT_DIR = ROOT / "steps" / "individual_replication_papers" / "figure1" / "auto_mining"
SUMMARY_TSV = OUT_DIR / "azar_dishonesty_replication_summary.tsv"
INPUTS_TSV = OUT_DIR / "azar_dishonesty_replication_input_files.tsv"
REPORT_MD = ROOT / "reports" / "figure1_auto_mining_azar_dishonesty_2026-05-05.md"


FILES = [
    RAW_DIR
    / "semantic_scholar_open_access_pdf__10_1016_j_socec_2020_101617__is_muni_cz__ef07f120f571.pdf",
    RAW_DIR / "openalex_oa_url__10_1016_j_socec_2020_101617__is_muni_cz__41f85db8766a.html",
    RAW_DIR / "openalex_oa_url__10_1016_j_socec_2020_101617__is_muni_cz__bf3a3b34979d.html",
    RAW_DIR / "original_attempts" / "03_0c0c38a1125d.html",
]


def clean(text: object) -> str:
    return str(text).replace("\t", " ").replace("\n", " ").replace("\r", " ").strip()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_tsv(path: Path, rows: list[dict[str, object]], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({column: clean(row.get(column, "")) for column in columns})


def main() -> None:
    low_n = 120
    high_n = 99
    replication_t = 3.01
    replication_d = replication_t * math.sqrt(1 / low_n + 1 / high_n)
    original_half_d = 0.403
    original_d = 2 * original_half_d

    summary_rows = [
        {
            "result_id": "original_inferred_from_replication_power_statement",
            "represented_source": "Azar, Yosef, and Bar-Eli (2013)",
            "represented_doi": "10.1016/j.jebo.2013.03.031",
            "n_total": 192,
            "effect_metric": "cohens_d_inferred",
            "effect_value": f"{original_d:.6f}",
            "native_effect_text": "Replication paper reports the high-change condition increased return by 21.7 percentage points, compared with 17.4 percentage points in the original study.",
            "n_text": "Original source metadata/abstract reports 128 out of 192 customers did not return excessive change.",
            "formula": "2 * 0.403, because the replication paper says 214 observations allowed testing 50% of the original effect size, i.e. d = .403.",
            "support_locator": "replication PDF lines 212-219; replication abstract lines 37-45; BGU original metadata abstract line 394",
        },
        {
            "result_id": "replication_t_to_d",
            "represented_source": "Prochazka, Fedoseeva, and Houdek (2021)",
            "represented_doi": "10.1016/j.socec.2020.101617",
            "n_total": 219,
            "effect_metric": "cohens_d_from_independent_t",
            "effect_value": f"{replication_d:.6f}",
            "native_effect_text": "High-change return rate 80%, low-change return rate 62%; t(217) = 3.01, p = .003; linear probability high-change coefficient 21.69 percentage points.",
            "n_text": "Final sample consisted of 219 guests; 120 received 20 CZK and 99 received 100 CZK excess change.",
            "formula": "t * sqrt(1/n_low + 1/n_high) = 3.01 * sqrt(1/120 + 1/99)",
            "support_locator": "replication PDF lines 212-219, 276-282, and 446-454",
        },
        {
            "result_id": "replication_native_return_difference",
            "represented_source": "Prochazka, Fedoseeva, and Houdek (2021)",
            "represented_doi": "10.1016/j.socec.2020.101617",
            "n_total": 219,
            "effect_metric": "percentage_point_difference",
            "effect_value": "21.69",
            "native_effect_text": "High-change condition increased the chance of returning excess change by 21.7 percentage points; original study 17.4 percentage points.",
            "n_text": "Final sample N = 219.",
            "formula": "Native linear-probability coefficient retained as support, not the plotted D value.",
            "support_locator": "replication PDF lines 37-45 and 446-454",
        },
    ]

    input_rows = []
    for path in FILES:
        input_rows.append(
            {
                "repo_relative_path": path.relative_to(ROOT),
                "exists": path.exists(),
                "bytes": path.stat().st_size if path.exists() else "",
                "sha256": sha256(path) if path.exists() else "",
            }
        )

    write_tsv(
        SUMMARY_TSV,
        summary_rows,
        [
            "result_id",
            "represented_source",
            "represented_doi",
            "n_total",
            "effect_metric",
            "effect_value",
            "native_effect_text",
            "n_text",
            "formula",
            "support_locator",
        ],
    )
    write_tsv(INPUTS_TSV, input_rows, ["repo_relative_path", "exists", "bytes", "sha256"])

    REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
    REPORT_MD.write_text(
        "\n".join(
            [
                "# Azar Dishonesty Registered Replication Auto-Mining",
                "",
                "## Summary",
                "",
                "- Original represented paper: Azar, Yosef, and Bar-Eli (2013), DOI `10.1016/j.jebo.2013.03.031`.",
                "- Replication represented paper: Prochazka, Fedoseeva, and Houdek (2021), DOI `10.1016/j.socec.2020.101617`.",
                f"- Original plotted D: `{original_d:.6f}` from the replication paper's statement that `d = .403` is 50% of the original effect size.",
                "- Original plotted N: `192`, from mirrored BGU source metadata/abstract.",
                f"- Replication plotted D: `{replication_d:.6f}`, recomputed as `3.01 * sqrt(1/120 + 1/99)`.",
                "- Replication plotted N: `219`, from the mirrored replication PDF.",
                "",
                "## Caveat",
                "",
                "The original full article was not mirrored automatically. This row is auditable because the original N and original native effect are present in mirrored source text and the original D is an explicit inference from the replication paper's power statement. A future pass should still mirror the original article or supplementary table and replace the inferred D if the original event counts/table support a better route.",
                "",
                "## Artifacts",
                "",
                f"- `{SUMMARY_TSV.relative_to(ROOT)}`",
                f"- `{INPUTS_TSV.relative_to(ROOT)}`",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
