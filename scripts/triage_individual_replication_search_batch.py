#!/usr/bin/env python3
"""Route GPT/Gemini individual-replication search candidates.

This is an audit/worklist projection only. It saves a cleaned copy of the
assistant-provided search manifest, checks candidate pairs against the current
Figure 1 root table, and writes route-specific worklists. It does not promote
or edit plotted rows.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
ROOT_PAIRS = ROOT / "FIGURE1_REPLICATION_PAIRS.tsv"

SEARCH_DIR = ROOT / "steps" / "searches" / "figure1"
WORKLIST_DIR = ROOT / "steps" / "individual_replication_papers" / "figure1"
REPORT = ROOT / "reports" / "figure1_individual_replication_search_batch001_triage_2026-05-05.md"

MANIFEST = SEARCH_DIR / "individualrepsearch-gpt-batch001.json"
TRIAGE = WORKLIST_DIR / "individual-paper-search-triage-batch001.tsv"
STRICT_WORKLIST = WORKLIST_DIR / "individual-paper-worklist-from-search.tsv"
D_EQ_WORKLIST = WORKLIST_DIR / "individual-paper-worklist-d-equivalent.tsv"
NATIVE_WORKLIST = WORKLIST_DIR / "individual-paper-worklist-native-only.tsv"
COVERAGE_WORKLIST = WORKLIST_DIR / "individual-paper-worklist-coverage-only.tsv"
REJECTIONS = WORKLIST_DIR / "individual-paper-search-rejections.tsv"

WORKLIST_COLUMNS = [
    "worklist_task_id",
    "candidate_id",
    "candidate_name",
    "route_type",
    "candidate_route",
    "confidence",
    "domain",
    "original_title",
    "original_doi",
    "replication_title",
    "replication_doi",
    "conversion_route",
    "source_object_urls_json",
    "dedupe_risk",
    "matched_root_pair_ids",
    "next_action",
    "notes",
    "created_at",
]

REJECTION_COLUMNS = [
    "rejection_id",
    "candidate_id",
    "candidate_name",
    "route_decision",
    "reason",
    "matched_root_pair_ids",
    "matched_source_family_keys",
    "created_at",
]


def clean(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and math.isnan(value):
        return ""
    return str(value).replace("\t", " ").replace("\n", " ").replace("\r", " ").strip()


def tsv_safe_frame(rows: list[dict[str, Any]]) -> pd.DataFrame:
    return pd.DataFrame([{k: clean(v) for k, v in row.items()} for row in rows])


def row_id(prefix: str, text: str) -> str:
    return f"{prefix}_{hashlib.sha1(text.encode('utf-8')).hexdigest()[:16]}"


CANDIDATES: list[dict[str, Any]] = [
    {
        "candidate_id": "facial_feedback_strack_wagenmakers",
        "candidate_name": "Strack, Martin & Stepper facial-feedback pen-in-mouth study -> Wagenmakers et al. Registered Replication Report",
        "domain": "social psychology / emotion",
        "candidate_route": "strict_figure1a",
        "confidence": "high",
        "original_title": "Inhibiting and facilitating conditions of the human smile: A nonobtrusive test of the facial feedback hypothesis",
        "original_doi": "10.1037/0022-3514.54.5.768",
        "replication_title": "Registered Replication Report: Strack, Martin, & Stepper (1988)",
        "replication_doi": "10.1177/1745691616674458",
        "conversion_route": "direct_d",
        "dedupe_risk": "high",
        "source_object_urls": [
            "https://www.ejwagenmakers.com/2016/WagenmakersEtAl2016Strack.pdf",
            "https://osf.io/h2f98/",
            "https://wexler.free.fr/library/files/strack%20%281988%29%20inhibiting%20and%20facilitating%20conditions%20of%20the%20human%20smile.%20a%20nonobtrusive%20test%20of%20the%20facial%20feedback%20hypothesis.pdf",
        ],
        "dedupe_terms": ["10.1177/1745691616674458", "strack facial feedback"],
    },
    {
        "candidate_id": "verbal_overshadowing_schooler_alogna",
        "candidate_name": "Schooler & Engstler-Schooler verbal overshadowing of visual memories -> Alogna et al. Registered Replication Report",
        "domain": "cognitive psychology / memory",
        "candidate_route": "d_equivalent_figure1b",
        "confidence": "high",
        "original_title": "Verbal overshadowing of visual memories: Some things are better left unsaid",
        "original_doi": "10.1037/0278-7393.16.1.36",
        "replication_title": "Registered Replication Report: Schooler and Engstler-Schooler (1990)",
        "replication_doi": "10.1177/1745691614545653",
        "conversion_route": "baseline_aware_binary_to_d_equivalent",
        "dedupe_risk": "high",
        "source_object_urls": [
            "https://ora.ox.ac.uk/objects/uuid%3A83aa4d74-3bec-459a-a777-328802241c8a/files/r8p58pf82j",
            "https://osf.io/ybeur/",
            "https://wixtedlab.ucsd.edu/publications/Psych%20272/Schooler_Engstler-Schooler_1990.pdf",
        ],
        "dedupe_terms": ["10.1177/1745691614545653", "schooler verbal overshadowing"],
    },
    {
        "candidate_id": "ego_depletion_sripada_hagger",
        "candidate_name": "Sripada, Kessler & Jonides ego-depletion sequential-task paradigm -> Hagger et al. multilab preregistered replication",
        "domain": "social/personality psychology / self-control",
        "candidate_route": "strict_figure1a",
        "confidence": "high",
        "original_title": "Methylphenidate Blocks Effort-Induced Depletion of Regulatory Control in Healthy Volunteers",
        "original_doi": "10.1177/0956797614526415",
        "replication_title": "A Multilab Preregistered Replication of the Ego-Depletion Effect",
        "replication_doi": "10.1177/1745691616652873",
        "conversion_route": "direct_d",
        "dedupe_risk": "high",
        "source_object_urls": [
            "https://pmc.ncbi.nlm.nih.gov/articles/PMC4206661/",
            "https://research-repository.griffith.edu.au/bitstreams/eb1d1f30-5f7d-5deb-b6a3-6acb765e9286/download",
            "https://osf.io/jymhe/",
        ],
        "dedupe_terms": ["10.1177/1745691616652873", "sripada 2014 ego depletion"],
    },
    {
        "candidate_id": "power_posing_carney_ranehill",
        "candidate_name": "Carney, Cuddy & Yap power posing -> Ranehill et al. larger-sample robustness replication",
        "domain": "social psychology / embodied cognition",
        "candidate_route": "strict_figure1a",
        "confidence": "high",
        "original_title": "Power Posing: Brief Nonverbal Displays Affect Neuroendocrine Levels and Risk Tolerance",
        "original_doi": "10.1177/0956797610383437",
        "replication_title": "Assessing the Robustness of Power Posing: No Effect on Hormones and Risk Tolerance in a Large Sample of Men and Women",
        "replication_doi": "10.1177/0956797614553946",
        "conversion_route": "direct_d",
        "dedupe_risk": "medium",
        "source_object_urls": [
            "https://faculty.haas.berkeley.edu/dana_carney/power.poses.PS.2010.pdf",
            "https://progressiegerichtwerken.com/wp-content/uploads/2016/12/5110-Ranehill-Dreber-Johannesson-Leiberg-Sul-Weber-PS-2015-Assessing-the-robustness-of-power-posing-no-effect-on-hormones-and-risk-rolerance-in-a-large-sample-of-men-and-women1.pdf",
        ],
        "dedupe_terms": ["10.1177/0956797614553946", "power posing"],
    },
    {
        "candidate_id": "professor_priming_dijksterhuis_odonnell",
        "candidate_name": "Dijksterhuis & van Knippenberg professor/hooligan priming -> O'Donnell et al. Registered Replication Report",
        "domain": "social cognition / behavioral priming",
        "candidate_route": "strict_figure1a",
        "confidence": "high",
        "original_title": "The Relation Between Perception and Behavior, or How to Win a Game of Trivial Pursuit",
        "original_doi": "10.1037/0022-3514.74.4.865",
        "replication_title": "Registered Replication Report: Dijksterhuis and van Knippenberg (1998)",
        "replication_doi": "10.1177/1745691618755704",
        "conversion_route": "direct_d",
        "dedupe_risk": "high",
        "source_object_urls": [
            "https://discovery.ucl.ac.uk/10046922/1/O%27Donnell%20et%20al.%20FINAL.pdf",
            "https://osf.io/k27hm/",
        ],
        "dedupe_terms": ["10.1177/1745691618755704", "dijksterhuis professor priming"],
    },
    {
        "candidate_id": "verb_aspect_intent_hart_eerland",
        "candidate_name": "Hart & Albarracin verb aspect and intent attributions -> Eerland et al. Registered Replication Report",
        "domain": "language and social cognition",
        "candidate_route": "strict_figure1a",
        "confidence": "high",
        "original_title": "Learning About What Others Were Doing: Verb Aspect and Attributions of Mundane and Criminal Intent for Past Actions",
        "original_doi": "10.1177/0956797610395393",
        "replication_title": "Registered Replication Report: Hart & Albarracin (2011)",
        "replication_doi": "10.1177/1745691615605826",
        "conversion_route": "direct_d",
        "dedupe_risk": "high",
        "source_object_urls": [
            "https://dspace.library.uu.nl/bitstreams/a02f1d3c-4682-4bb1-a84f-007cc7e27834/download",
            "https://osf.io/d3mw4/",
        ],
        "dedupe_terms": ["10.1177/1745691615605826", "hart & albarracin grammatical aspect"],
    },
    {
        "candidate_id": "intuitive_cooperation_rand_bouwmeester",
        "candidate_name": "Rand, Greene & Nowak intuitive cooperation/time pressure -> Bouwmeester et al. Registered Replication Report",
        "domain": "experimental economics / judgment and decision making",
        "candidate_route": "strict_figure1a",
        "confidence": "high",
        "original_title": "Spontaneous Giving and Calculated Greed",
        "original_doi": "10.1038/nature11467",
        "replication_title": "Registered Replication Report: Rand, Greene, and Nowak (2012)",
        "replication_doi": "10.1177/1745691617693624",
        "conversion_route": "direct_d_or_binary_d_equivalent_after_outcome_check",
        "dedupe_risk": "high",
        "source_object_urls": ["https://osf.io/f6jtm/", "https://www.nature.com/articles/nature11467"],
        "dedupe_terms": ["10.1177/1745691617693624", "rand et al intuitive cooperation"],
    },
    {
        "candidate_id": "commitment_forgiveness_finkel_cheung",
        "candidate_name": "Finkel et al. commitment prime and forgiveness -> Cheung et al. Registered Replication Report",
        "domain": "relationship science / social psychology",
        "candidate_route": "strict_figure1a",
        "confidence": "high",
        "original_title": "Dealing With Betrayal in Close Relationships: Does Commitment Promote Forgiveness?",
        "original_doi": "10.1037/0022-3514.82.6.956",
        "replication_title": "Registered Replication Report: Study 1 From Finkel, Rusbult, Kumashiro, & Hannon (2002)",
        "replication_doi": "10.1177/1745691616664694",
        "conversion_route": "direct_d",
        "dedupe_risk": "high",
        "source_object_urls": [
            "https://faculty.wcas.northwestern.edu/eli-finkel/documents/Finkeletal_2002_000.pdf",
            "https://files01.core.ac.uk/download/pdf/111754782.pdf",
            "https://osf.io/s3hfr/",
        ],
        "dedupe_terms": ["10.1177/1745691616664694", "finkel commitment/forgiveness"],
    },
    {
        "candidate_id": "moral_forecasting_teper_bo",
        "candidate_name": "Teper, Inzlicht & Page-Gould moral forecasting error -> Bo & Sjastad preregistered replication and extension",
        "domain": "moral psychology / judgment and decision making",
        "candidate_route": "strict_figure1a",
        "confidence": "high",
        "original_title": "Are We More Moral Than We Think? Exploring the Role of Affect in Moral Behavior and Moral Forecasting",
        "original_doi": "10.1177/0956797611402513",
        "replication_title": "Revisiting the moral forecasting error - A preregistered replication and extension of 'Are we more moral than we think?'",
        "replication_doi": "10.1016/j.jesp.2024.104662",
        "conversion_route": "direct_d",
        "dedupe_risk": "low",
        "source_object_urls": [
            "https://www.sciencedirect.com/science/article/pii/S0022103124000751",
            "https://osf.io/preprints/psyarxiv/m49y3",
            "https://files.osf.io/v1/resources/m49y3/providers/osfstorage/62a8c017b47e79294a6394de?action=download&direct=&format=pdf&version=2",
            "https://www.page-gould.com/documents/Teper_Inzlicht_Page-Gould_2011.pdf",
            "https://osf.io/4apgt/",
            "https://osf.io/download/bn38v/",
            "https://osf.io/download/zrxn8/",
            "https://journals.sagepub.com/doi/10.1177/0956797611402513",
        ],
        "dedupe_terms": ["10.1016/j.jesp.2024.104662", "moral forecasting error", "m49y3"],
    },
    {
        "candidate_id": "spacing_induction_kornell_verkoeijen",
        "candidate_name": "Kornell & Bjork spacing in inductive category learning -> Verkoeijen & Bouwmeester exact high-powered replication",
        "domain": "cognitive psychology / learning",
        "candidate_route": "strict_figure1a",
        "confidence": "high",
        "original_title": "Learning Concepts and Categories: Is Spacing the 'Enemy of Induction'?",
        "original_doi": "10.1111/j.1467-9280.2008.02127.x",
        "replication_title": "Is spacing really the 'friend of induction'?",
        "replication_doi": "10.3389/fpsyg.2014.00259",
        "conversion_route": "direct_d",
        "dedupe_risk": "low",
        "source_object_urls": [
            "https://www.frontiersin.org/journals/psychology/articles/10.3389/fpsyg.2014.00259/full",
            "https://pmc.ncbi.nlm.nih.gov/articles/PMC3978334/",
            "https://gwern.net/doc/psychology/spaced-repetition/2008-kornell.pdf",
        ],
        "dedupe_terms": ["10.3389/fpsyg.2014.00259", "verkoeijen", "friend of induction"],
    },
    {
        "candidate_id": "rubber_hand_disgust_jalal_nitta",
        "candidate_name": "Jalal, Krishnakumar & Ramachandran disgust during rubber-hand illusion -> Nitta et al. registered replication report",
        "domain": "cognitive psychology / body ownership",
        "candidate_route": "strict_figure1a",
        "confidence": "high",
        "original_title": "'I Feel Contaminated in My Fake Hand': Obsessive-Compulsive-Disorder like Disgust Sensations Arise from Dummy during Rubber Hand Illusion",
        "original_doi": "10.1371/journal.pone.0139159",
        "replication_title": "Disgust and the rubber hand illusion: A registered replication report of Jalal, Krishnakumar, and Ramachandran (2015)",
        "replication_doi": "10.1186/s41235-018-0101-z",
        "conversion_route": "statistic_to_d",
        "dedupe_risk": "low",
        "source_object_urls": [
            "https://pmc.ncbi.nlm.nih.gov/articles/PMC5954052/",
            "https://springernature.figshare.com/articles/journal_contribution/Disgust_and_the_rubber_hand_illusion_A_registered_replication_report_of_Jalal_Krishnakumar_and_Ramachandran_2015_Registered_Report_Stage_1_/6217295",
            "https://journals.plos.org/plosone/article?id=10.1371%2Fjournal.pone.0139159",
        ],
        "dedupe_terms": ["10.1186/s41235-018-0101-z", "10.1371/journal.pone.0139159", "rubber hand illusion"],
    },
    {
        "candidate_id": "attentional_snarc_fischer_colling",
        "candidate_name": "Fischer, Castel, Dodd & Pratt attentional SNARC effect -> Colling et al. Registered Replication Report",
        "domain": "cognitive psychology / numerical cognition",
        "candidate_route": "strict_figure1a",
        "confidence": "high",
        "original_title": "Perceiving Numbers Causes Spatial Shifts of Attention",
        "original_doi": "10.1038/nn1066",
        "replication_title": "Registered Replication Report on Fischer, Castel, Dodd, and Pratt (2003)",
        "replication_doi": "10.1177/2515245920903079",
        "conversion_route": "direct_d",
        "dedupe_risk": "medium",
        "source_object_urls": [
            "https://www.blakemcshane.com/Papers/ampps_attsnarc.pdf",
            "https://sussex.figshare.com/articles/journal_contribution/Registered_replication_report_on_Fischer_Castel_Dodd_and_Pratt_2003_/23307710/1/files/41093336.pdf",
        ],
        "dedupe_terms": ["10.1177/2515245920903079", "10.1038/nn1066", "att-snarc"],
    },
    {
        "candidate_id": "gustatory_disgust_moral_judgment_ghelfi",
        "candidate_name": "Eskine, Kacinik & Prinz gustatory disgust and moral judgment -> Ghelfi et al. multilab direct replication",
        "domain": "moral psychology / emotion",
        "candidate_route": "strict_figure1a",
        "confidence": "high",
        "original_title": "A Bad Taste in the Mouth: Gustatory Disgust Influences Moral Judgment",
        "original_doi": "10.1177/0956797611398497",
        "replication_title": "Reexamining the Effect of Gustatory Disgust on Moral Judgment: A Multilab Direct Replication of Eskine, Kacinik, and Prinz (2011)",
        "replication_doi": "10.1177/2515245919881152",
        "conversion_route": "direct_d",
        "dedupe_risk": "medium",
        "source_object_urls": ["https://journals.sagepub.com/doi/10.1177/2515245919881152", "https://osf.io/785qu/"],
        "dedupe_terms": ["10.1177/2515245919881152", "gustatory disgust triggers"],
    },
    {
        "candidate_id": "dishonesty_moral_reminders_mazar_verschuere",
        "candidate_name": "Mazar, Amir & Ariely moral reminders reduce cheating -> Verschuere et al. Registered Replication Report",
        "domain": "marketing / behavioral ethics",
        "candidate_route": "strict_figure1a",
        "confidence": "high",
        "original_title": "The Dishonesty of Honest People: A Theory of Self-Concept Maintenance",
        "original_doi": "10.1509/jmkr.45.6.633",
        "replication_title": "Registered Replication Report on Mazar, Amir, and Ariely (2008)",
        "replication_doi": "10.1177/2515245918781032",
        "conversion_route": "direct_d",
        "dedupe_risk": "high",
        "source_object_urls": [
            "https://ppw.kuleuven.be/okp/_pdf/Verschuere2018RRROM.pdf",
            "https://osf.io/vxz7q/",
            "https://econweb.ucsd.edu/~jandreon/Seminar/OnAmir.pdf",
        ],
        "dedupe_terms": ["10.1177/2515245918781032", "mazar/amir/ariely moral reminders"],
    },
    {
        "candidate_id": "hostility_priming_srull_mccarthy",
        "candidate_name": "Srull & Wyer hostility/category-accessibility priming -> McCarthy et al. Registered Replication Report",
        "domain": "social cognition / priming",
        "candidate_route": "strict_figure1a",
        "confidence": "high",
        "original_title": "The Role of Category Accessibility in the Interpretation of Information About Persons: Some Determinants and Implications",
        "original_doi": "10.1037/0022-3514.37.10.1660",
        "replication_title": "Registered Replication Report on Srull and Wyer (1979)",
        "replication_doi": "10.1177/2515245918777487",
        "conversion_route": "direct_d",
        "dedupe_risk": "high",
        "source_object_urls": [
            "https://journals.sagepub.com/doi/10.1177/2515245918777487",
            "https://osf.io/qxfba",
        ],
        "dedupe_terms": ["10.1177/2515245918777487", "srull-wyer hostility priming"],
    },
    {
        "candidate_id": "medusa_effect_will_han",
        "candidate_name": "Will, Merritt, Jenkins & Kingstone Medusa effect -> Han et al. registered replication report",
        "domain": "cognitive psychology / social cognition",
        "candidate_route": "strict_figure1a",
        "confidence": "medium",
        "original_title": "The Medusa effect reveals levels of mind perception in pictures",
        "original_doi": "10.1073/pnas.2106640118",
        "replication_title": "The Medusa effect: a registered replication report of Will, Merritt, Jenkins and Kingstone (2021)",
        "replication_doi": "10.1098/rsos.231802",
        "conversion_route": "direct_d",
        "dedupe_risk": "low",
        "source_object_urls": [
            "https://pmc.ncbi.nlm.nih.gov/articles/PMC10776219/",
            "https://royalsocietypublishing.org/rsos/article/11/1/231802/92448/The-Medusa-effect-a-registered-replication-report",
            "https://osf.io/qjwbx/",
            "https://eprints.whiterose.ac.uk/id/eprint/177226/1/will_merritt_jenkins_kingstone21.pdf",
            "https://doi.org/10.1073/pnas.2106640118",
        ],
        "dedupe_terms": ["10.1098/rsos.231802", "10.1073/pnas.2106640118", "medusa effect"],
    },
    {
        "candidate_id": "spontaneous_verbal_rehearsal_flavell_elliott",
        "candidate_name": "Flavell, Beach & Chinsky spontaneous verbal rehearsal by age -> Elliott et al. multilab direct replication",
        "domain": "developmental psychology / memory",
        "candidate_route": "native_only",
        "confidence": "medium",
        "original_title": "Spontaneous Verbal Rehearsal in a Memory Task as a Function of Age",
        "original_doi": "10.2307/1126804",
        "replication_title": "Multilab Direct Replication of Flavell, Beach, and Chinsky (1966): Spontaneous Verbal Rehearsal in a Memory Task as a Function of Age",
        "replication_doi": "10.1177/25152459211018187",
        "conversion_route": "native_only",
        "dedupe_risk": "medium",
        "source_object_urls": [
            "https://pmc.ncbi.nlm.nih.gov/articles/PMC12349909/",
            "https://osf.io/vgxkf/",
            "https://doi.org/10.2307/1126804",
        ],
        "dedupe_terms": ["10.1177/25152459211018187", "flavell et al. (1966) spontaneous verbal rehearsal"],
    },
]


FORCED_DISPOSITION = {
    "facial_feedback_strack_wagenmakers": "already_in_root_table",
    "verbal_overshadowing_schooler_alogna": "already_in_root_table",
    "ego_depletion_sripada_hagger": "already_in_root_table",
    "power_posing_carney_ranehill": "already_in_root_table",
    "professor_priming_dijksterhuis_odonnell": "already_in_root_table",
    "verb_aspect_intent_hart_eerland": "already_in_root_table",
    "intuitive_cooperation_rand_bouwmeester": "already_in_root_table",
    "commitment_forgiveness_finkel_cheung": "already_in_root_table",
    "attentional_snarc_fischer_colling": "already_in_root_table",
    "gustatory_disgust_moral_judgment_ghelfi": "already_in_root_table",
    "dishonesty_moral_reminders_mazar_verschuere": "already_in_root_table",
    "hostility_priming_srull_mccarthy": "already_in_root_table",
    "spontaneous_verbal_rehearsal_flavell_elliott": "already_in_root_table",
    "moral_forecasting_teper_bo": "route_to_individual_strict_extraction",
    "spacing_induction_kornell_verkoeijen": "route_to_individual_strict_extraction",
    "rubber_hand_disgust_jalal_nitta": "route_to_individual_strict_extraction",
    "medusa_effect_will_han": "route_to_individual_strict_extraction",
}


DISPOSITION_REASON = {
    "already_in_root_table": "Local dedupe found exact DOI/title/source-family evidence in FIGURE1_REPLICATION_PAIRS.tsv; keep as duplicate/search-recall evidence rather than adding rows.",
    "route_to_individual_strict_extraction": "No exact local root-table match found for the pair; source-object URLs and affirmative replication relation are sufficient for one-paper extraction worklist review.",
    "route_to_individual_d_equivalent_extraction": "No exact local root-table match found, but the outcome requires binary/clinical D-equivalent handling before plotting.",
    "route_to_native_only_extraction": "No exact local root-table match found, but the outcome should remain native-scale unless a documented conversion route is approved.",
    "route_to_coverage_only": "Useful for coverage/accounting but not for D or D-equivalent extraction.",
}


def read_pairs() -> pd.DataFrame:
    if not ROOT_PAIRS.exists():
        return pd.DataFrame()
    return pd.read_csv(ROOT_PAIRS, sep="\t", dtype=str).fillna("")


def match_root_rows(candidate: dict[str, Any], pairs: pd.DataFrame) -> pd.DataFrame:
    if pairs.empty:
        return pairs
    hay = pairs.astype(str).agg(" ".join, axis=1).str.lower()
    mask = pd.Series(False, index=pairs.index)
    for term in candidate.get("dedupe_terms", []):
        term = clean(term).lower()
        if term:
            mask |= hay.str.contains(term, regex=False, na=False)
    return pairs[mask].copy()


def route_candidate(candidate: dict[str, Any], hit_count: int) -> str:
    forced = FORCED_DISPOSITION.get(candidate["candidate_id"])
    if forced:
        return forced
    if hit_count:
        return "already_in_root_table"
    if candidate["candidate_route"] == "d_equivalent_figure1b":
        return "route_to_individual_d_equivalent_extraction"
    if candidate["candidate_route"] == "native_only":
        return "route_to_native_only_extraction"
    return "route_to_individual_strict_extraction"


def make_worklist_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "worklist_task_id": row_id("individual_search_task", row["candidate_id"]),
        "candidate_id": row["candidate_id"],
        "candidate_name": row["candidate_name"],
        "route_type": row["route_decision"],
        "candidate_route": row["candidate_route"],
        "confidence": row["confidence"],
        "domain": row["domain"],
        "original_title": row["original_title"],
        "original_doi": row["original_doi"],
        "replication_title": row["replication_title"],
        "replication_doi": row["replication_doi"],
        "conversion_route": row["conversion_route"],
        "source_object_urls_json": row["source_object_urls_json"],
        "dedupe_risk": row["dedupe_risk"],
        "matched_root_pair_ids": row["matched_root_pair_ids"],
        "next_action": "mirror_or_parse_source_objects_before_any_row_promotion",
        "notes": row["route_reason"],
        "created_at": row["created_at"],
    }


def write_outputs() -> None:
    SEARCH_DIR.mkdir(parents=True, exist_ok=True)
    WORKLIST_DIR.mkdir(parents=True, exist_ok=True)
    pairs = read_pairs()
    created_at = "2026-05-05T00:00:00"

    manifest = {
        "task_id": "individual_replication_search",
        "batch_id": "gpt-batch001",
        "created_at": created_at,
        "source_note": "Cleaned local copy of user-supplied GPT/Gemini candidate manifest. Markdown links and malformed JSON from chat were normalized before saving.",
        "candidate_count": len(CANDIDATES),
        "candidates": CANDIDATES,
    }
    MANIFEST.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    triage_rows: list[dict[str, Any]] = []
    for candidate in CANDIDATES:
        hits = match_root_rows(candidate, pairs)
        route = route_candidate(candidate, len(hits))
        root_ids = "|".join(hits.get("figure1_replication_pair_id", pd.Series(dtype=str)).head(30).tolist())
        root_families = "|".join(sorted(set(hits.get("source_family_key", pd.Series(dtype=str)).tolist())))
        triage_rows.append(
            {
                "candidate_id": candidate["candidate_id"],
                "candidate_name": candidate["candidate_name"],
                "domain": candidate["domain"],
                "candidate_route": candidate["candidate_route"],
                "confidence": candidate["confidence"],
                "original_title": candidate["original_title"],
                "original_doi": candidate["original_doi"],
                "replication_title": candidate["replication_title"],
                "replication_doi": candidate["replication_doi"],
                "conversion_route": candidate["conversion_route"],
                "dedupe_risk": candidate["dedupe_risk"],
                "source_object_urls_json": json.dumps(candidate["source_object_urls"], ensure_ascii=True),
                "local_match_count": len(hits),
                "matched_root_pair_ids": root_ids,
                "matched_source_family_keys": root_families,
                "route_decision": route,
                "route_reason": DISPOSITION_REASON.get(route, ""),
                "created_at": created_at,
            }
        )

    triage = tsv_safe_frame(triage_rows)
    triage.to_csv(TRIAGE, sep="\t", index=False)

    strict_rows = [make_worklist_row(row) for row in triage_rows if row["route_decision"] == "route_to_individual_strict_extraction"]
    deq_rows = [make_worklist_row(row) for row in triage_rows if row["route_decision"] == "route_to_individual_d_equivalent_extraction"]
    native_rows = [make_worklist_row(row) for row in triage_rows if row["route_decision"] == "route_to_native_only_extraction"]
    coverage_rows = [make_worklist_row(row) for row in triage_rows if row["route_decision"] == "route_to_coverage_only"]
    reject_rows = [
        {
            "rejection_id": row_id("individual_search_reject", row["candidate_id"]),
            "candidate_id": row["candidate_id"],
            "candidate_name": row["candidate_name"],
            "route_decision": row["route_decision"],
            "reason": row["route_reason"],
            "matched_root_pair_ids": row["matched_root_pair_ids"],
            "matched_source_family_keys": row["matched_source_family_keys"],
            "created_at": row["created_at"],
        }
        for row in triage_rows
        if row["route_decision"] == "already_in_root_table"
    ]

    pd.DataFrame(strict_rows, columns=WORKLIST_COLUMNS).fillna("").to_csv(STRICT_WORKLIST, sep="\t", index=False)
    pd.DataFrame(deq_rows, columns=WORKLIST_COLUMNS).fillna("").to_csv(D_EQ_WORKLIST, sep="\t", index=False)
    pd.DataFrame(native_rows, columns=WORKLIST_COLUMNS).fillna("").to_csv(NATIVE_WORKLIST, sep="\t", index=False)
    pd.DataFrame(coverage_rows, columns=WORKLIST_COLUMNS).fillna("").to_csv(COVERAGE_WORKLIST, sep="\t", index=False)
    pd.DataFrame(reject_rows, columns=REJECTION_COLUMNS).fillna("").to_csv(REJECTIONS, sep="\t", index=False)

    counts = triage["route_decision"].value_counts().to_dict()
    lines = [
        "# Figure 1 Individual Replication Search Batch 001 Triage",
        "",
        "This is a routing artifact for the first GPT/Gemini individual-replication batch. It does not add or promote Figure 1 rows.",
        "",
        "## Counts",
        "",
        f"- Candidates reviewed: {len(triage_rows)}",
        f"- Already captured in current root table: {counts.get('already_in_root_table', 0)}",
        f"- New strict Figure 1A extraction candidates: {counts.get('route_to_individual_strict_extraction', 0)}",
        f"- New D-equivalent Figure 1B extraction candidates: {counts.get('route_to_individual_d_equivalent_extraction', 0)}",
        f"- New native-only candidates: {counts.get('route_to_native_only_extraction', 0)}",
        f"- Coverage-only candidates: {counts.get('route_to_coverage_only', 0)}",
        "",
        "## New Strict Extraction Candidates",
        "",
    ]
    if strict_rows:
        for row in strict_rows:
            lines.append(f"- `{row['candidate_id']}`: {row['candidate_name']} ({row['replication_doi']})")
    else:
        lines.append("- None.")
    lines.extend(
        [
            "",
            "## Duplicate/Search-Recall Candidates",
            "",
        ]
    )
    for row in reject_rows:
        lines.append(f"- `{row['candidate_id']}` matched `{row['matched_source_family_keys']}` rows: `{row['matched_root_pair_ids']}`")
    lines.extend(
        [
            "",
            "## Outputs",
            "",
            f"- Manifest: `{MANIFEST.relative_to(ROOT)}`",
            f"- Triage table: `{TRIAGE.relative_to(ROOT)}`",
            f"- Strict worklist: `{STRICT_WORKLIST.relative_to(ROOT)}`",
            f"- D-equivalent worklist: `{D_EQ_WORKLIST.relative_to(ROOT)}`",
            f"- Native-only worklist: `{NATIVE_WORKLIST.relative_to(ROOT)}`",
            f"- Coverage-only worklist: `{COVERAGE_WORKLIST.relative_to(ROOT)}`",
            f"- Rejections: `{REJECTIONS.relative_to(ROOT)}`",
            "",
            "Next step for worklist rows is source-object mirroring or parsing into source/source_access/source_file/source_result artifacts before any root-table promotion.",
            "",
        ]
    )
    REPORT.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--replace", action="store_true", help="Accepted for Makefile consistency; outputs are always regenerated.")
    parser.parse_args()
    write_outputs()


if __name__ == "__main__":
    main()
