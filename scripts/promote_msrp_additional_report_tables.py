#!/usr/bin/env python3
"""Promote additional direct-replication rows from MSRP report tables.

This script adds report-table rows that are already recoverable from the
Management Science Replication Project PDFs downloaded locally.
"""

from __future__ import annotations

import math
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
HARVEST = ROOT / "data" / "raw" / "replication_projects" / "lead_harvest" / "msrp_om_2023" / "msrp_public_extra"
PROMOTED = ROOT / "data" / "derived" / "replication_pairs" / "harvest" / "promoted"


def pooled_d_from_summary(mean_a: float, sd_a: float, n_a: int, mean_b: float, sd_b: float, n_b: int) -> float:
    pooled_var = (((n_a - 1) * sd_a**2) + ((n_b - 1) * sd_b**2)) / (n_a + n_b - 2)
    return abs((mean_a - mean_b) / math.sqrt(pooled_var))


def chisq1_to_d(chi2: float, total_n: int) -> float:
    r = math.sqrt(chi2 / total_n)
    return abs((2 * r) / math.sqrt(max(1 - r * r, 1e-12)))


def mean_diff_se_to_d(mean_a: float, mean_b: float, se_diff: float, total_n: int) -> float:
    return abs(2 * (mean_a - mean_b) / (se_diff * math.sqrt(total_n)))


def coefficient_test_to_d(coef: float, se: float, n_subjects: int, null_value: float = 0.0) -> float:
    return abs((coef - null_value) / se) / math.sqrt(n_subjects)


def build_rows() -> list[dict]:
    rows: list[dict] = []

    chen_pdf = HARVEST / "ChenEtAl2013_ReplicationReport.pdf"
    chen_original_d = pooled_d_from_summary(11.728, 1.392, 29, 9.749, 1.058, 21)
    chen_original_n = 50
    chen_replications = [
        ("michigan_online", "University of Michigan (Online)", 10.864, 2.330, 27, 9.965, 2.288, 25),
        ("utd_online", "University of Texas-Dallas (Online)", 11.285, 2.577, 25, 9.866, 2.224, 25),
        ("michigan_inperson", "University of Michigan (In Person)", 10.962, 3.188, 25, 9.834, 1.660, 27),
    ]
    for suffix, label, m_o, sd_o, n_o, m_c, sd_c, n_c in chen_replications:
        rows.append(
            {
                "source_dataset": "MSRP Chen et al. 2013 report table",
                "project": "Management Science Replication Project",
                "pair_id": f"msrp_chen_payment_scheme_{suffix}",
                "original_title": "Chen et al. (2013) payment schemes on inventory decisions",
                "replication_title": f"MSRP Chen et al. replication ({label})",
                "original_doi": "",
                "replication_doi": "",
                "outcome": "Order quantity difference between order financing and cash treatment",
                "D_original": chen_original_d,
                "N_original": chen_original_n,
                "D_replication": pooled_d_from_summary(m_o, sd_o, n_o, m_c, sd_c, n_c),
                "N_replication": n_o + n_c,
                "raw_file": str(chen_pdf),
                "match_author": "chen_payment_schemes_inventory",
            }
        )

    davis_pdf = HARVEST / "DavisEtAl2011_ReplicationReport.pdf"
    davis_original_d = coefficient_test_to_d(3.311, 0.104, 20)
    davis_specs = [
        ("wisconsin", "Wisconsin", 3.200, 0.093, 41),
        ("michigan", "Michigan", 2.791, 0.098, 40),
    ]
    for suffix, label, coef, se, n_subjects in davis_specs:
        rows.append(
            {
                "source_dataset": "MSRP Davis et al. 2011 report table",
                "project": "Management Science Replication Project",
                "pair_id": f"msrp_davis_reserve_price_{suffix}",
                "original_title": "Davis et al. (2011) auction reserve prices",
                "replication_title": f"MSRP Davis et al. replication ({label})",
                "original_doi": "",
                "replication_doi": "",
                "outcome": "Reserve-price coefficient for number of bidders",
                "D_original": davis_original_d,
                "N_original": 20,
                "D_replication": coefficient_test_to_d(coef, se, n_subjects),
                "N_replication": n_subjects,
                "raw_file": str(davis_pdf),
                "match_author": "davis_auction_reserve_prices",
            }
        )

    ho_pdf = HARVEST / "HoZhang2008_ReplicationReport.pdf"
    ho_original_d = pooled_d_from_summary(76.37, 36.18, 242, 69.51, 41.27, 264)
    ho_original_n = 242 + 264
    ho_replications = [
        ("utd", "UT Dallas", 63.18, 42.35, 715, 63.61, 40.95, 726),
        ("michigan", "Michigan", 75.35, 34.03, 319, 70.73, 38.68, 310),
    ]
    for suffix, label, m_qd, sd_qd, n_qd, m_tpt, sd_tpt, n_tpt in ho_replications:
        rows.append(
            {
                "source_dataset": "MSRP Ho & Zhang 2008 report table",
                "project": "Management Science Replication Project",
                "pair_id": f"msrp_ho_zhang_efficiency_{suffix}",
                "original_title": "Ho & Zhang (2008) supply-chain efficiency under QD vs TPT",
                "replication_title": f"MSRP Ho & Zhang replication ({label})",
                "original_doi": "",
                "replication_doi": "",
                "outcome": "Overall efficiency difference between QD and TPT contracts",
                "D_original": ho_original_d,
                "N_original": ho_original_n,
                "D_replication": pooled_d_from_summary(m_qd, sd_qd, n_qd, m_tpt, sd_tpt, n_tpt),
                "N_replication": n_qd + n_tpt,
                "raw_file": str(ho_pdf),
                "match_author": "ho_zhang_contract_efficiency",
            }
        )

    kremer_etal_pdf = HARVEST / "KremerEtAl2011_ReplicationReport.pdf"
    kremer_etal_specs = [
        (
            "condition1_utd",
            "Condition 1, UT Dallas",
            "Condition 1 forecast-weight deviation from rational benchmark",
            0.39,
            0.04,
            43,
            0.367,
            0.050,
            65,
        ),
        (
            "condition1_michigan",
            "Condition 1, Michigan",
            "Condition 1 forecast-weight deviation from rational benchmark",
            0.39,
            0.04,
            43,
            0.286,
            0.028,
            69,
        ),
        (
            "condition5_utd",
            "Condition 5, UT Dallas",
            "Condition 5 forecast-weight deviation from rational benchmark",
            0.70,
            0.03,
            43,
            0.790,
            0.036,
            70,
        ),
        (
            "condition5_michigan",
            "Condition 5, Michigan",
            "Condition 5 forecast-weight deviation from rational benchmark",
            0.70,
            0.03,
            43,
            0.786,
            0.032,
            70,
        ),
    ]
    for suffix, label, outcome, orig_coef, orig_se, orig_n, rep_coef, rep_se, rep_n in kremer_etal_specs:
        rows.append(
            {
                "source_dataset": "MSRP Kremer et al. 2011 report table",
                "project": "Management Science Replication Project",
                "pair_id": f"msrp_kremer_etal_system_neglect_{suffix}",
                "original_title": "Kremer et al. (2011) demand forecasting system neglect",
                "replication_title": f"MSRP Kremer et al. replication ({label})",
                "original_doi": "",
                "replication_doi": "",
                "outcome": outcome,
                "D_original": coefficient_test_to_d(orig_coef, orig_se, orig_n, null_value=0.94),
                "N_original": orig_n,
                "D_replication": coefficient_test_to_d(rep_coef, rep_se, rep_n, null_value=0.94),
                "N_replication": rep_n,
                "raw_file": str(kremer_etal_pdf),
                "match_author": "kremer_etal_system_neglect",
            }
        )

    kremer_pdf = HARVEST / "KremerDebo2016_ReplicationReport.pdf"
    kremer_original_d = chisq1_to_d(74.34, 100)
    kremer_specs = [
        ("south_carolina", "Primary Site (South Carolina)", 5.35, 100),
        ("michigan", "Secondary Site (Michigan)", 57.72, 104),
    ]
    for suffix, label, chi2, n_total in kremer_specs:
        rows.append(
            {
                "source_dataset": "MSRP Kremer & Debo 2016 report table",
                "project": "Management Science Replication Project",
                "pair_id": f"msrp_kremer_debo_waittime_interaction_{suffix}",
                "original_title": "Kremer & Debo (2016) wait time x informed consumers interaction",
                "replication_title": f"MSRP Kremer & Debo replication ({label})",
                "original_doi": "",
                "replication_doi": "",
                "outcome": "Interaction of wait time and informed-consumer condition on purchase",
                "D_original": kremer_original_d,
                "N_original": 100,
                "D_replication": chisq1_to_d(chi2, n_total),
                "N_replication": n_total,
                "raw_file": str(kremer_pdf),
                "match_author": "kremer_debo_waittime_interaction",
            }
        )

    ozer_pdf = HARVEST / "OzerEtAl2011_ReplicationReport.pdf"
    ozer_specs = [
        (
            "cornell_report_forecast",
            "Cornell manufacturer report",
            "Manufacturer report sensitivity to private forecast",
            0.643,
            0.052,
            8,
            0.716,
            0.046,
            44,
        ),
        (
            "michigan_report_forecast",
            "Michigan manufacturer report",
            "Manufacturer report sensitivity to private forecast",
            0.643,
            0.052,
            8,
            0.749,
            0.046,
            46,
        ),
        (
            "cornell_capacity_report",
            "Cornell supplier capacity",
            "Supplier capacity sensitivity to manufacturer report",
            0.662,
            0.070,
            8,
            0.609,
            0.051,
            44,
        ),
        (
            "michigan_capacity_report",
            "Michigan supplier capacity",
            "Supplier capacity sensitivity to manufacturer report",
            0.662,
            0.070,
            8,
            0.587,
            0.051,
            46,
        ),
    ]
    for suffix, label, outcome, orig_coef, orig_se, orig_n, rep_coef, rep_se, rep_n in ozer_specs:
        rows.append(
            {
                "source_dataset": "MSRP Ozer et al. 2011 report table",
                "project": "Management Science Replication Project",
                "pair_id": f"msrp_ozer_forecast_sharing_{suffix}",
                "original_title": "Ozer et al. (2011) trust in forecast information sharing",
                "replication_title": f"MSRP Ozer et al. replication ({label})",
                "original_doi": "",
                "replication_doi": "",
                "outcome": outcome,
                "D_original": coefficient_test_to_d(orig_coef, orig_se, orig_n),
                "N_original": orig_n,
                "D_replication": coefficient_test_to_d(rep_coef, rep_se, rep_n),
                "N_replication": rep_n,
                "raw_file": str(ozer_pdf),
                "match_author": "ozer_forecast_information_sharing",
            }
        )

    ewk_pdf = HARVEST / "EngelbrechtWiggansKatok2008_ReplicationReport.pdf"
    ewk_original_d = pooled_d_from_summary(0.7263, 0.0529, 32, 0.7660, 0.0479, 32)
    ewk_specs = [
        ("online_wisconsin", "Online Wisconsin", 0.7267, 0.0651, 36, 0.7418, 0.0901, 34),
        ("online_cornell", "Online Cornell", 0.7251, 0.0733, 41, 0.7482, 0.0811, 40),
        ("inperson_wisconsin", "In-person Wisconsin", 0.7260, 0.0625, 35, 0.7435, 0.0578, 32),
        ("inperson_cornell", "In-person Cornell", 0.7124, 0.0751, 33, 0.7458, 0.0829, 33),
    ]
    for suffix, label, both_m, both_sd, both_n, regret_m, regret_sd, regret_n in ewk_specs:
        rows.append(
            {
                "source_dataset": "MSRP Engelbrecht-Wiggans & Katok 2008 report table",
                "project": "Management Science Replication Project",
                "pair_id": f"msrp_ewk_bid_value_{suffix}",
                "original_title": "Engelbrecht-Wiggans & Katok (2008) regret feedback auction",
                "replication_title": f"MSRP Engelbrecht-Wiggans & Katok replication ({label})",
                "original_doi": "",
                "replication_doi": "",
                "outcome": "Average bid/value, both feedback vs loser's-regret feedback",
                "D_original": ewk_original_d,
                "N_original": 64,
                "D_replication": pooled_d_from_summary(both_m, both_sd, both_n, regret_m, regret_sd, regret_n),
                "N_replication": both_n + regret_n,
                "raw_file": str(ewk_pdf),
                "match_author": "engelbrecht_wiggans_katok_regret_feedback",
            }
        )

    shunko_pdf = HARVEST / "ShunkoEtAl2018_ReplicationReport.pdf"
    shunko_original_d = mean_diff_se_to_d(15.63, 18.00, math.sqrt(0.75**2 + 0.97**2), 113)
    shunko_specs = [
        ("wisconsin", "Wisconsin primary M-Turk", 21.72, 1.10, 122, 21.94, 1.34, 124),
        ("usc", "USC secondary M-Turk", 24.60, 1.67, 130, 24.24, 0.98, 122),
    ]
    for suffix, label, parallel_m, parallel_se, parallel_n, single_m, single_se, single_n in shunko_specs:
        rows.append(
            {
                "source_dataset": "MSRP Shunko et al. 2018 report table",
                "project": "Management Science Replication Project",
                "pair_id": f"msrp_shunko_service_time_{suffix}",
                "original_title": "Shunko et al. (2018) queue structure and service time",
                "replication_title": f"MSRP Shunko et al. replication ({label})",
                "original_doi": "",
                "replication_doi": "",
                "outcome": "Second-half median service time, parallel vs single queue",
                "D_original": shunko_original_d,
                "N_original": 113,
                "D_replication": mean_diff_se_to_d(
                    parallel_m,
                    single_m,
                    math.sqrt(parallel_se**2 + single_se**2),
                    parallel_n + single_n,
                ),
                "N_replication": parallel_n + single_n,
                "raw_file": str(shunko_pdf),
                "match_author": "shunko_queue_service_time",
            }
        )

    return rows


def main() -> None:
    PROMOTED.mkdir(parents=True, exist_ok=True)
    out_path = PROMOTED / "msrp_additional_report_tables__promoted_pairs.csv"
    out = pd.DataFrame(build_rows())
    out.to_csv(out_path, index=False)
    print(f"Wrote promoted rows: {len(out)}")
    print(f"Wrote file: {out_path}")


if __name__ == "__main__":
    main()
