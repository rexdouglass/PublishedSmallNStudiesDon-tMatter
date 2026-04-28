#!/usr/bin/env python3
"""Write staged and promoted rows from manually reviewed Ying reconstruction attempts."""

from __future__ import annotations

import math
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
STAGED = ROOT / "data" / "derived" / "replication_pairs" / "harvest" / "staged"
PROMOTED = ROOT / "data" / "derived" / "replication_pairs" / "harvest" / "promoted"

STAGE_PATH = STAGED / "ying_2023_partial_reconstruction__stage.csv"
PROMOTED_PATH = PROMOTED / "ying_2023_partial_reconstruction__promoted_pairs.csv"


def odds_ratio_from_counts(
    events_treatment: float,
    non_events_treatment: float,
    events_control: float,
    non_events_control: float,
) -> float:
    return (events_treatment * non_events_control) / (non_events_treatment * events_control)


def odds_ratio_to_d(value: float) -> float:
    return abs(math.log(value)) * math.sqrt(3) / math.pi


def hedges_g_from_md_ci(mean_diff: float, ci_lower: float, ci_upper: float, n_treatment: int, n_control: int) -> float:
    se = (ci_upper - ci_lower) / (2 * 1.96)
    pooled_sd = se / math.sqrt((1 / n_treatment) + (1 / n_control))
    d = abs(mean_diff) / pooled_sd
    df = n_treatment + n_control - 2
    correction = 1 - (3 / ((4 * df) - 1))
    return d * correction


def hedges_g_from_md_se(mean_diff: float, se: float, n_treatment: int, n_control: int) -> float:
    pooled_sd = se / math.sqrt((1 / n_treatment) + (1 / n_control))
    d = abs(mean_diff) / pooled_sd
    df = n_treatment + n_control - 2
    correction = 1 - (3 / ((4 * df) - 1))
    return d * correction


def hedges_g_from_summary(
    mean_treatment: float,
    sd_treatment: float,
    n_treatment: int,
    mean_control: float,
    sd_control: float,
    n_control: int,
) -> float:
    pooled_sd = math.sqrt(
        (((n_treatment - 1) * sd_treatment**2) + ((n_control - 1) * sd_control**2))
        / (n_treatment + n_control - 2)
    )
    d = abs(mean_treatment - mean_control) / pooled_sd
    df = n_treatment + n_control - 2
    correction = 1 - (3 / ((4 * df) - 1))
    return d * correction


def build_stage_rows() -> list[dict[str, object]]:
    raw_file = str(STAGE_PATH)
    adhd_pilot_or = odds_ratio_from_counts(9, 7, 2, 13)
    adhd_replication_or = odds_ratio_from_counts(29, 14, 14, 29)
    neutropenic_pilot_or = odds_ratio_from_counts(4, 5, 4, 6)
    neutropenic_replication_or = odds_ratio_from_counts(27, 50, 24, 49)
    otch_pilot_g = hedges_g_from_summary(0.6, 3.9, 59, -0.9, 2.2, 46)
    otch_replication_g = hedges_g_from_md_ci(0.19, -0.33, 0.70, 540, 436)
    postpartum_pilot_g = hedges_g_from_md_ci(57, 6, 107, 15, 14)
    postpartum_replication_g = hedges_g_from_md_ci(5.97, -7.55, 19.5, 110, 105)
    tat_replication_g = hedges_g_from_md_se(1.24, 0.74, 142, 143)
    pediatric_depression_pilot_log_hr = abs(math.log(8.80))
    pediatric_depression_replication_log_hr = abs(math.log(0.313))
    return [
        {
            "source_dataset": "Ying 2023 manual partial reconstruction",
            "source_paper": "Ying 2023 dissertation roster + user-supplied extraction attempts",
            "pair_id": "ying_2023_pair_003_screen_positivity",
            "pair_number": 3,
            "original_title": "Final results of the Lung Screening Study, a randomized feasibility study of spiral CT versus chest X-ray screening for lung cancer",
            "replication_title": "Results of initial low-dose computed tomographic screening for lung cancer",
            "original_doi": "10.1016/j.lungcan.2004.06.007",
            "replication_doi": "10.1056/NEJMoa1209120",
            "outcome": "Initial screening positivity / detection yield for low-dose CT versus chest X-ray",
            "N_original": 3318,
            "N_replication": 53439,
            "D_original": 0.714,
            "D_replication": 0.729,
            "same_primary_endpoint": True,
            "larger_n_replication": True,
            "likely_in_125_effect_size_subset": True,
            "promotion_decision": "promote_live",
            "evidence_confidence": "high",
            "analytic_status": "usable_d_pair",
            "notes": "Promoted from the strongest attempt. Effect is based on low-dose CT increasing positive screens/detection yield versus chest X-ray, not on mortality benefit.",
            "source_urls": "10.1016/j.lungcan.2004.06.007 | 10.1056/NEJMoa1209120",
            "raw_file": raw_file,
        },
        {
            "source_dataset": "Ying 2023 manual partial reconstruction",
            "source_paper": "Ying 2023 dissertation roster + user-supplied extraction attempts",
            "pair_id": "ying_2023_pair_006_adhd_cbt",
            "pair_number": 6,
            "original_title": "Cognitive-behavioral therapy for ADHD in medication-treated adults with continued symptoms",
            "replication_title": "Cognitive behavioral therapy vs relaxation with educational support for medication-treated adults with ADHD and persistent symptoms",
            "original_doi": "10.1016/j.brat.2004.07.001",
            "replication_doi": "10.1001/jama.2010.1192",
            "outcome": "Adult ADHD symptom severity / clinical response",
            "N_original": 31,
            "N_replication": 86,
            "D_original": odds_ratio_to_d(adhd_pilot_or),
            "D_replication": odds_ratio_to_d(adhd_replication_or),
            "same_primary_endpoint": True,
            "larger_n_replication": True,
            "likely_in_125_effect_size_subset": True,
            "promotion_decision": "promote_live",
            "evidence_confidence": "high",
            "analytic_status": "usable_binary_response_pair",
            "notes": "Promoted from matched ADHD rating-scale responder rates. Pilot abstract reports N=31 and 56% CBT versus 13% control responders, resolved to the nearest feasible arm counts 9/16 versus 2/15. Full-scale JAMA/PMC article reports N=86, arm Ns 43/43, responder rates 67% versus 33%, and OR=4.29; counts 29/43 versus 14/43 reproduce that OR. D values use Chinn's log(OR)*sqrt(3)/pi conversion.",
            "source_urls": "10.1016/j.brat.2004.07.001 | 10.1001/jama.2010.1192 | https://pmc.ncbi.nlm.nih.gov/articles/PMC3641654/",
            "raw_file": raw_file,
        },
        {
            "source_dataset": "Ying 2023 manual partial reconstruction",
            "source_paper": "Ying 2023 dissertation roster + user-supplied extraction attempts",
            "pair_id": "ying_2023_pair_010_neutropenic_diet",
            "pair_number": 10,
            "original_title": "Feasibility and safety of a pilot randomized trial of infection rate: neutropenic diet versus standard food safety guidelines",
            "replication_title": "A randomized trial of the effectiveness of the neutropenic diet versus food safety guidelines on infection rate in pediatric oncology patients",
            "original_doi": "10.1097/01.mph.0000210412.33630.fb",
            "replication_doi": "10.1002/pbc.26711",
            "outcome": "Neutropenic infection / infection rate",
            "N_original": 19,
            "N_replication": 150,
            "D_original": odds_ratio_to_d(neutropenic_pilot_or),
            "D_replication": odds_ratio_to_d(neutropenic_replication_or),
            "same_primary_endpoint": True,
            "larger_n_replication": True,
            "likely_in_125_effect_size_subset": True,
            "promotion_decision": "promote_live",
            "evidence_confidence": "moderate_high",
            "analytic_status": "usable_binary_event_pair",
            "notes": "Promoted after local source rescue. PubMed abstract reports N=19 and four febrile-neutropenia events on each pilot diet arm; a later neutropenic-diet meta-analysis table gives pilot denominators ND n=9 and RD/FSG n=10. Full-scale PDF reports infection counts ND+FSG 27/77 versus FSG 24/73. D values use Chinn's log(OR)*sqrt(3)/pi conversion on the harm-positive infection axis.",
            "source_urls": "10.1097/01.mph.0000210412.33630.fb | 10.1002/pbc.26711 | https://pubmed.ncbi.nlm.nih.gov/16679934/ | https://awarticles.s3.amazonaws.com/28696047.pdf | https://www.omicsonline.org/open-access-pdfs/the-efficacy-of-neutropenic-diet-in-preventing-neutropenia-related-infections-among-pediatric-patients-undergoing-chemot.pdf",
            "raw_file": raw_file,
        },
        {
            "source_dataset": "Ying 2023 manual partial reconstruction",
            "source_paper": "Ying 2023 dissertation roster + user-supplied extraction attempts",
            "pair_id": "ying_2023_pair_012_otch_barthel",
            "pair_number": 12,
            "original_title": "Cluster randomized pilot controlled trial of an occupational therapy intervention for residents with stroke in UK care homes",
            "replication_title": "An occupational therapy intervention for residents with stroke related disabilities in UK care homes (OTCH)",
            "original_doi": "10.1161/01.Str.0000237124.20596.92",
            "replication_doi": "10.1136/bmj.h468",
            "outcome": "Barthel Index of Activities of Daily Living at 3 months",
            "N_original": 118,
            "N_replication": 1042,
            "D_original": otch_pilot_g,
            "D_replication": otch_replication_g,
            "same_primary_endpoint": True,
            "larger_n_replication": True,
            "likely_in_125_effect_size_subset": True,
            "promotion_decision": "promote_sensitivity",
            "evidence_confidence": "moderate",
            "analytic_status": "usable_mixed_smd_sensitivity",
            "notes": "Promoted as a sensitivity row after local PDF rescue. Pilot Table 2 gives Barthel change at 3 months: intervention +0.6 SD 3.9, n=59; control -0.9 SD 2.2, n=46, from 118 randomized residents. Full-scale BMJ/PMC Table 3 gives adjusted Barthel index mean difference 0.19, 95% CI -0.33 to 0.70, with table Ns 540 intervention and 436 control from 1042 randomized residents. Pilot D uses change-score pooled SD; replication D is inferred from the adjusted mean-difference CI and table Ns, so this is sensitivity-grade rather than a clean arm-SD SMD.",
            "source_urls": "10.1161/01.Str.0000237124.20596.92 | 10.1136/bmj.h468 | data/raw/replication_projects/pilot_full_scale_inbound/ying_rescues/otch_pilot.pdf | https://pmc.ncbi.nlm.nih.gov/articles/PMC4353312/",
            "raw_file": raw_file,
        },
        {
            "source_dataset": "Ying 2023 manual partial reconstruction",
            "source_paper": "Ying 2023 dissertation roster + user-supplied extraction attempts",
            "pair_id": "ying_2023_pair_014_postpartum_sleep",
            "pair_number": 14,
            "original_title": "A behavioral-educational intervention to promote maternal and infant sleep: a pilot randomized, controlled trial",
            "replication_title": "Effect of behavioural-educational intervention on sleep for primiparous women and their infants in early postpartum: multisite randomised controlled trial",
            "original_doi": "10.1093/sleep/29.12.1609",
            "replication_doi": "10.1136/bmj.f1164",
            "outcome": "Maternal nocturnal sleep duration in early postpartum",
            "N_original": 30,
            "N_replication": 246,
            "D_original": postpartum_pilot_g,
            "D_replication": postpartum_replication_g,
            "same_primary_endpoint": True,
            "larger_n_replication": True,
            "likely_in_125_effect_size_subset": True,
            "promotion_decision": "promote_sensitivity",
            "evidence_confidence": "moderate",
            "analytic_status": "usable_ci_derived_smd_sensitivity",
            "notes": "Promoted as a sensitivity row after local PDF rescue. Pilot Table 2 gives maternal nocturnal sleep 433 versus 376 minutes, between-group difference 57 minutes with 95% CI 6 to 107, n=15 intervention and n=14 control for sleep outcomes. Full-scale BMJ/PMC abstract gives sleep-outcome complete cases n=110 intervention and n=105 usual care and adjusted mean difference 5.97 minutes with 95% CI -7.55 to 19.5. D values are Hedges g inferred from the reported mean-difference CIs and arm Ns.",
            "source_urls": "10.1093/sleep/29.12.1609 | 10.1136/bmj.f1164 | data/raw/replication_projects/pilot_full_scale_inbound/ying_rescues/postpartum_sleep_pilot.pdf | https://pmc.ncbi.nlm.nih.gov/articles/PMC3603553/",
            "raw_file": raw_file,
        },
        {
            "source_dataset": "Ying 2023 manual partial reconstruction",
            "source_paper": "Ying 2023 dissertation roster + user-supplied extraction attempts",
            "pair_id": "ying_2023_pair_017_tat_weight_maintenance",
            "pair_number": 17,
            "original_title": "Randomized trial of two mind-body interventions for weight-loss maintenance",
            "replication_title": "Randomized trial of Tapas Acupressure Technique for weight loss maintenance",
            "original_doi": "10.1089/acm.2006.6237",
            "replication_doi": "10.1186/1472-6882-12-19",
            "outcome": "Weight-loss maintenance / weight regain",
            "N_original": 92,
            "N_replication": 285,
            "D_original": 0.48,
            "D_replication": tat_replication_g,
            "same_primary_endpoint": True,
            "larger_n_replication": True,
            "likely_in_125_effect_size_subset": True,
            "promotion_decision": "hold_stage_only",
            "evidence_confidence": "moderate_high",
            "analytic_status": "d_values_recovered_but_timepoint_model_caveat",
            "notes": "Local PDF rescue recovered the pilot denominators and variance context. Pilot Table 2 gives randomized arm Ns SDS n=31, TAT n=30, QI n=31; the full-scale PMC article states the pilot TAT-versus-social-support contrast was 0.1 versus 1.2 kg regain with SD=2.3 and Cohen's d=0.48. The full-scale trial randomized TAT n=142 and social support n=143 and reports adjusted TAT-SS weight-regain difference -1.24 kg with SE=0.74, giving Hedges g about 0.198 if the model SE is treated as the between-arm SE. Held staged because the pilot endpoint is 24 weeks and the definitive trial endpoint is 12 months, and the replication D is model-SE-derived.",
            "source_urls": "10.1089/acm.2006.6237 | 10.1186/1472-6882-12-19 | data/raw/replication_projects/pilot_full_scale_inbound/ying_rescues/tat_weight_maintenance_pilot.pdf | https://pmc.ncbi.nlm.nih.gov/articles/PMC3375195/",
            "raw_file": raw_file,
        },
        {
            "source_dataset": "Ying 2023 manual partial reconstruction",
            "source_paper": "Ying 2023 dissertation roster + local PMC full-text extraction",
            "pair_id": "ying_2023_pair_033_pediatric_depression_relapse",
            "pair_number": 33,
            "original_title": "Cognitive-behavioral therapy to prevent relapse in pediatric responders to pharmacotherapy for major depressive disorder",
            "replication_title": "Sequential treatment with fluoxetine and relapse prevention CBT to improve outcomes in pediatric depression",
            "original_doi": "10.1097/CHI.0b013e31818914a1",
            "replication_doi": "10.1176/appi.ajp.2014.13111460",
            "outcome": "Time to relapse during continuation treatment after response to fluoxetine",
            "N_original": 46,
            "N_replication": 144,
            "D_original": None,
            "D_replication": None,
            "same_primary_endpoint": True,
            "larger_n_replication": True,
            "likely_in_125_effect_size_subset": True,
            "promotion_decision": "hold_stage_only",
            "evidence_confidence": "high",
            "analytic_status": "native_log_hazard_ratio_pair",
            "notes": (
                "PMC full texts expose exact matched Cox-model relapse hazard ratios: pilot HR=8.80 for MM versus MM+CBT "
                f"(absolute log HR {pediatric_depression_pilot_log_hr:.3f}); full-scale HR=0.313 for MM+CBT versus MM "
                f"(absolute log HR {pediatric_depression_replication_log_hr:.3f}). Held out of the promoted D file because "
                "log hazard-ratio magnitudes are not Cohen's d and should be promoted only if the analysis explicitly accepts "
                "native ratio metrics or a documented HR-to-d mapping."
            ),
            "source_urls": "10.1097/CHI.0b013e31818914a1 | 10.1176/appi.ajp.2014.13111460 | https://pmc.ncbi.nlm.nih.gov/articles/PMC2826176/ | https://pmc.ncbi.nlm.nih.gov/articles/PMC4182111/",
            "raw_file": raw_file,
        },
    ]


def build_promoted_rows() -> list[dict[str, object]]:
    adhd_pilot_or = odds_ratio_from_counts(9, 7, 2, 13)
    adhd_replication_or = odds_ratio_from_counts(29, 14, 14, 29)
    neutropenic_pilot_or = odds_ratio_from_counts(4, 5, 4, 6)
    neutropenic_replication_or = odds_ratio_from_counts(27, 50, 24, 49)
    otch_pilot_g = hedges_g_from_summary(0.6, 3.9, 59, -0.9, 2.2, 46)
    otch_replication_g = hedges_g_from_md_ci(0.19, -0.33, 0.70, 540, 436)
    postpartum_pilot_g = hedges_g_from_md_ci(57, 6, 107, 15, 14)
    postpartum_replication_g = hedges_g_from_md_ci(5.97, -7.55, 19.5, 110, 105)
    return [
        {
            "source_dataset": "Ying 2023 manual partial reconstruction",
            "project": "Ying 2023 pilot-full-scale trials",
            "pair_id": "ying_2023_pair_003_screen_positivity",
            "original_title": "Final results of the Lung Screening Study, a randomized feasibility study of spiral CT versus chest X-ray screening for lung cancer",
            "replication_title": "Results of initial low-dose computed tomographic screening for lung cancer",
            "original_doi": "10.1016/j.lungcan.2004.06.007",
            "replication_doi": "10.1056/NEJMoa1209120",
            "outcome": "Initial screening positivity / detection yield for low-dose CT versus chest X-ray",
            "D_original": 0.714,
            "N_original": 3318,
            "D_replication": 0.729,
            "N_replication": 53439,
            "raw_file": str(STAGE_PATH),
            "match_author": "ying_gohagan_nlst_screen_positivity",
        },
        {
            "source_dataset": "Ying 2023 manual partial reconstruction",
            "project": "Ying 2023 pilot-full-scale trials",
            "pair_id": "ying_2023_pair_006_adhd_cbt",
            "original_title": "Cognitive-behavioral therapy for ADHD in medication-treated adults with continued symptoms",
            "replication_title": "Cognitive behavioral therapy vs relaxation with educational support for medication-treated adults with ADHD and persistent symptoms",
            "original_doi": "10.1016/j.brat.2004.07.001",
            "replication_doi": "10.1001/jama.2010.1192",
            "outcome": "Adult ADHD rating-scale clinical response",
            "D_original": odds_ratio_to_d(adhd_pilot_or),
            "N_original": 31,
            "D_replication": odds_ratio_to_d(adhd_replication_or),
            "N_replication": 86,
            "raw_file": str(STAGE_PATH),
            "match_author": "ying_safren_jama_adhd_response",
        },
        {
            "source_dataset": "Ying 2023 manual partial reconstruction",
            "project": "Ying 2023 pilot-full-scale trials",
            "pair_id": "ying_2023_pair_010_neutropenic_diet",
            "original_title": "Feasibility and safety of a pilot randomized trial of infection rate: neutropenic diet versus standard food safety guidelines",
            "replication_title": "A randomized trial of the effectiveness of the neutropenic diet versus food safety guidelines on infection rate in pediatric oncology patients",
            "original_doi": "10.1097/01.mph.0000210412.33630.fb",
            "replication_doi": "10.1002/pbc.26711",
            "outcome": "Febrile neutropenia / neutropenic infection under neutropenic diet versus food-safety guidelines",
            "D_original": odds_ratio_to_d(neutropenic_pilot_or),
            "N_original": 19,
            "D_replication": odds_ratio_to_d(neutropenic_replication_or),
            "N_replication": 150,
            "raw_file": str(STAGE_PATH),
            "match_author": "ying_moody_neutropenic_diet_infection",
        },
        {
            "source_dataset": "Ying 2023 manual partial reconstruction",
            "project": "Ying 2023 pilot-full-scale trials",
            "pair_id": "ying_2023_pair_012_otch_barthel",
            "original_title": "Cluster randomized pilot controlled trial of an occupational therapy intervention for residents with stroke in UK care homes",
            "replication_title": "Occupational therapy for residents with stroke-related disabilities in UK care homes",
            "original_doi": "10.1161/01.Str.0000237124.20596.92",
            "replication_doi": "10.1136/bmj.h468",
            "outcome": "Barthel Index of Activities of Daily Living at 3 months; sensitivity SMD reconstruction",
            "D_original": otch_pilot_g,
            "N_original": 118,
            "D_replication": otch_replication_g,
            "N_replication": 1042,
            "raw_file": str(STAGE_PATH),
            "match_author": "ying_sackley_otch_barthel_sensitivity",
            "notes": "Sensitivity row. Pilot D uses 3-month Barthel change means/SDs among survivors: +0.6 SD 3.9 n=59 versus -0.9 SD 2.2 n=46. Full-scale D is inferred from adjusted Barthel mean difference 0.19, 95% CI -0.33 to 0.70, using table Ns 540/436. Plot Ns use randomized totals 118 and 1042.",
        },
        {
            "source_dataset": "Ying 2023 manual partial reconstruction",
            "project": "Ying 2023 pilot-full-scale trials",
            "pair_id": "ying_2023_pair_014_postpartum_sleep",
            "original_title": "A behavioral-educational intervention to promote maternal and infant sleep: a pilot randomized, controlled trial",
            "replication_title": "Effect of behavioural-educational intervention on sleep for primiparous women and their infants in early postpartum",
            "original_doi": "10.1093/sleep/29.12.1609",
            "replication_doi": "10.1136/bmj.f1164",
            "outcome": "Maternal nocturnal sleep duration; Hedges g inferred from mean-difference CIs",
            "D_original": postpartum_pilot_g,
            "N_original": 30,
            "D_replication": postpartum_replication_g,
            "N_replication": 246,
            "raw_file": str(STAGE_PATH),
            "match_author": "ying_stremler_postpartum_sleep_ci_sensitivity",
            "notes": "Sensitivity row. Pilot: 57-minute maternal nocturnal sleep benefit, 95% CI 6 to 107, sleep-outcome Ns 15/14. Full-scale: adjusted 5.97-minute benefit, 95% CI -7.55 to 19.5, sleep-outcome complete-case Ns 110/105. D values are CI-derived Hedges g.",
        },
    ]


def main() -> None:
    STAGED.mkdir(parents=True, exist_ok=True)
    PROMOTED.mkdir(parents=True, exist_ok=True)

    stage_df = pd.DataFrame(build_stage_rows())
    promoted_df = pd.DataFrame(build_promoted_rows())

    stage_df.to_csv(STAGE_PATH, index=False)
    promoted_df.to_csv(PROMOTED_PATH, index=False)

    print(f"Wrote staged rows: {len(stage_df)} -> {STAGE_PATH}")
    print(f"Wrote promoted rows: {len(promoted_df)} -> {PROMOTED_PATH}")


if __name__ == "__main__":
    main()
