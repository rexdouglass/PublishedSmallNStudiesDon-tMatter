#!/usr/bin/env python3
"""Build Quarto-ready paper assets from the Claude HTML draft and local data.

This script is deliberately extraction-backed: the old HTML draft is treated as
the seed document, while current derived datasets provide the upgraded figures
and synced figure captions.
"""

from __future__ import annotations

import ast
import csv
import hashlib
import io
import math
import os
import re
import shutil
import subprocess
import tempfile
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urljoin
from urllib.request import Request, urlopen

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from bs4 import BeautifulSoup, NavigableString
from matplotlib.lines import Line2D
from matplotlib.ticker import FixedFormatter, FixedLocator, NullFormatter
from matplotlib.transforms import blended_transform_factory
from scipy import stats


ROOT = Path(__file__).resolve().parents[1]
DRAFT_HTML = ROOT / "docs" / "nightmare-hellscape (3).html"
DOCS = ROOT / "docs"
REFERENCES_BIB = DOCS / "references.bib"
GENERATED = DOCS / "_generated"
FIG_DIR = GENERATED / "figures"
TABLE_DIR = ROOT / "data" / "derived" / "paper_tables"
TABLE_FRAGMENT_DIR = GENERATED / "tables"
DATASET_DERIVED_DIR = ROOT / "data" / "derived" / "effect_inflation_dataset"
TESS_STUDY_INDEX = DATASET_DERIVED_DIR / "plot3_tess_study_index_candidates.csv"
POLISCI_RESCUE_WORKLIST = DATASET_DERIVED_DIR / "plot3_political_science_rescue_worklist.csv"
POLISCI_STRICT_RESCUE_ROWS = DATASET_DERIVED_DIR / "plot3_political_science_strict_rescue_rows.csv"
POLISCI_PAPER_PROJECT_MEDIANS = DATASET_DERIVED_DIR / "plot3_political_science_paper_project_medians.csv"
AEA_GOVERNANCE_CANDIDATES = DATASET_DERIVED_DIR / "plot3_aea_registry_governance_candidates.csv"
POLISCI_UNLOCK_RAW = ROOT / "data" / "raw" / "corpus_candidates" / "political_science_unlock"
GOOD_POLITICIANS_ZIP = POLISCI_UNLOCK_RAW / "zenodo" / "10086096" / "gulzarkhan20240105.zip"
GHANA_DEBATES_TAB = POLISCI_UNLOCK_RAW / "dataverse" / "OJA7YS" / "BKO_debates_main.tab"
VIETNAM_LEGISLATOR_OUTCOMES = POLISCI_UNLOCK_RAW / "dataverse" / "RXA4JB" / "pooled-outcomes.xlsx"
VIETNAM_MAIN_SURVEY_OUTCOMES = POLISCI_UNLOCK_RAW / "dataverse" / "4WNEE9" / "survey-outcomes.xlsx"
VIETNAM_MAIN_EXPERIMENTAL_ANALYSES = POLISCI_UNLOCK_RAW / "dataverse" / "4WNEE9" / "experimental-analyses.Rds"
GOLDEN_PS_MASTER = POLISCI_UNLOCK_RAW / "dataverse" / "9PWQZT" / "99_ps_master.tab"
KALLA_BROOCKMAN_MINIMAL_EFFECTS = POLISCI_UNLOCK_RAW / "dataverse" / "RAMHWP" / "master_sheet_output.tab"
LOCAL_ELITES_OPENICPSR_ZIP = ROOT / "data" / "raw" / "147561-V3.zip"
HEWITT_CAMPAIGN_ARCHIVE_ZIP = ROOT / "data" / "raw" / "replication_archive.zip"
POLITICAL_ACTIVISTS_ZIP = POLISCI_UNLOCK_RAW / "dataverse" / "2KLNFX" / "2KLNFX.zip"
CHINA_AID_ATTITUDES_ZIP = POLISCI_UNLOCK_RAW / "dataverse" / "3VVWPL" / "3VVWPL.zip"
SENEGAL_ACCOUNTABILITY_ZIP = POLISCI_UNLOCK_RAW / "dataverse" / "QAJQXP" / "QAJQXP.zip"
PUBLIC_SERVICE_JOB_ZIP = POLISCI_UNLOCK_RAW / "dataverse" / "P0XSAU" / "P0XSAU.zip"
BANGLADESH_ELECTION_ZIP = POLISCI_UNLOCK_RAW / "zenodo" / "10059860" / "3-replication-package_ufvur.zip"
POLITICAL_ACTIVISTS_FREERIDING_ZIP = (
    POLISCI_UNLOCK_RAW / "zenodo" / "7663389" / "political_activists_zenodo.zip"
)
POLICING_PATRIARCHY_DIR = POLISCI_UNLOCK_RAW / "dataverse" / "R75XVZ"
POLICING_PATRIARCHY_CCTV = POLICING_PATRIARCHY_DIR / "cctv_full_data.tab"
POLICING_PATRIARCHY_TABLE2 = POLICING_PATRIARCHY_DIR / "Table2.tex"
AZEVEDO_JEPS_ANALYSIS_HTML = POLISCI_UNLOCK_RAW / "dataverse" / "ETUUOD" / "analysis_manuscript.html"
VOTE_BUYING_RADIO_ZIP = POLISCI_UNLOCK_RAW / "dataverse" / "VPGE7F" / "VPGE7F.zip"
INTERETHNIC_CONTACT_ZIP = POLISCI_UNLOCK_RAW / "dataverse" / "NQKPGY" / "NQKPGY.zip"
IMMIGRATION_BELIEFS_ZIP = POLISCI_UNLOCK_RAW / "dataverse" / "8DM8KG" / "8DM8KG.zip"
COVID_TOGETHERNESS_ZIP = POLISCI_UNLOCK_RAW / "dataverse" / "1LIIDV" / "1LIIDV.zip"
MEDICINE_THEFT_ZIP = POLISCI_UNLOCK_RAW / "dataverse" / "KRFPVU" / "KRFPVU.zip"
REFUGEE_DESTINATION_ZIP = POLISCI_UNLOCK_RAW / "zenodo" / "15322600" / "PNAS_replication_package.zip"
BARAZA_ANCOVA_RESULTS = (
    POLISCI_UNLOCK_RAW / "github" / "baraza" / "report" / "results" / "final" / "df_ancova.Rd"
)
DIRECT_AID_SURVEYS = (
    POLISCI_UNLOCK_RAW
    / "github"
    / "Direct-Aid-Replication-Materials"
    / "Replication Materials"
    / "Data"
    / "surveysDataset.dta"
)
BANGLADESH_WASH_ZIP = POLISCI_UNLOCK_RAW / "dataverse" / "U9I4Z2" / "Replication_Folder_only.zip"
COVID_EMPEROR_ZIP = POLISCI_UNLOCK_RAW / "osf" / "covid_emperor_tejmf" / "replication.zip"
VACCINE_HESITANCY_ZIP = (
    POLISCI_UNLOCK_RAW / "osf" / "vaccine_hesitancy_c8dvm" / "data__Reddinger_Levine_Charness_vaccination_rct.zip"
)
MOUSA_D_CANDIDATES = DATASET_DERIVED_DIR / "plot3_mousa2020_soccer_d_candidates.csv"
BODY_QMD = GENERATED / "paper_body.qmd"
DATA_APPENDICES_QMD = GENERATED / "data_appendices.qmd"
DATASET_AUDIT_QMD = GENERATED / "dataset_audit_snapshot.qmd"
PLOT1_SOURCES_QMD = GENERATED / "plot1_replication_sources.qmd"
PLOT1_CRITERIA_QMD = GENERATED / "plot1_replication_criteria.qmd"
PLOT2_SOURCES_QMD = GENERATED / "plot2_published_sources.qmd"
PLOT2_CRITERIA_QMD = GENERATED / "plot2_published_criteria.qmd"
PLOT3_SOURCES_QMD = GENERATED / "plot3_preregistered_sources.qmd"
PLOT3_CRITERIA_QMD = GENERATED / "plot3_preregistered_criteria.qmd"
PLOT4_SOURCES_QMD = GENERATED / "plot4_all_source_dump_sources.qmd"
PLOT_STATUS_QMD = GENERATED / "plot_catalog_status.qmd"
PROVENANCE_SCHEMA_QMD = GENERATED / "provenance_schema_pilot.qmd"
SOURCE_CITATION_GAPS_QMD = GENERATED / "source_citation_gaps.qmd"
CITATION_AUDIT = GENERATED / "citation_audit.csv"
TABLE_MANIFEST = TABLE_DIR / "table_manifest.csv"
INTRO_EXAMPLES = ROOT / "data" / "derived" / "paper_assets" / "figure1_intro_examples.csv"

REPLICATION_FIG = ROOT / "reports" / "corpus_candidates" / "figure2_replication_pairs_draft.png"
REPLICATION_CSV = ROOT / "data" / "derived" / "replication_pairs" / "replication_pairs_figure2_rule_subset.csv"
FIGURE1_ROOT_TABLE = ROOT / "FIGURE1_REPLICATION_PAIRS.tsv"
REPLICATION_ALL = ROOT / "data" / "derived" / "replication_pairs" / "replication_pairs_all_on_hand.csv"
REPLICATION_SOURCE_AUDIT = ROOT / "data" / "derived" / "replication_pairs" / "replication_source_audit.csv"
REPLICATION_SOURCE_WORKLIST = ROOT / "data" / "derived" / "replication_pairs" / "replication_source_worklist.csv"
REPLICATION_SOURCE_INVENTORY = ROOT / "data" / "derived" / "replication_pairs" / "replication_source_evidence_inventory.csv"
REPLICATION_SOURCE_CATALOG = ROOT / "data" / "derived" / "replication_pairs" / "replication_pair_source_catalog.csv"
REPLICATION_APPENDIX_COVERAGE = ROOT / "data" / "derived" / "replication_pairs" / "replication_pairs_appendix_coverage.csv"
PUBLISHED_FIG = ROOT / "reports" / "corpus_candidates" / "candidate_published_paper_d_vs_n.png"
PUBLISHED_PAPERS = ROOT / "data" / "derived" / "corpus_candidates" / "candidate_d_n_papers.csv"
CANDIDATE_ROWS = ROOT / "data" / "derived" / "corpus_candidates" / "candidate_d_n_rows.csv.gz"
PUBLISHED_PAPER_SUMMARY = ROOT / "data" / "derived" / "published_papers" / "published_original_paper_d_vs_n.csv"
FIELD_GROUPS = ROOT / "data" / "derived" / "corpus_candidates" / "candidate_published_field_groups.csv"
PUBLISHED_SOURCE_LIST = ROOT / "data" / "derived" / "corpus_candidates" / "current_peer_reviewed_journal_d_n_list.csv"
PUBLISHED_SOURCE_STATUS = ROOT / "data" / "derived" / "corpus_candidates" / "current_peer_reviewed_main_result_status.csv"
PREREG_TABLE_40 = ROOT / "data" / "derived" / "paper_tables" / "table_40_preregistered_hypotheses_scheel_2021_psa_cr001_corpus.csv"
PREREG_TABLE_41 = ROOT / "data" / "derived" / "paper_tables" / "table_41_added_preregistered_rows_from_psa_cr001_dorison_et_al_2022.csv"
HARVEST_STAGED_DIR = ROOT / "data" / "derived" / "replication_pairs" / "harvest" / "staged"
HARVEST_PROMOTED_DIR = ROOT / "data" / "derived" / "replication_pairs" / "harvest" / "promoted"
SCHAEFER_PREREG_RAW = ROOT / "data" / "raw" / "corpus_candidates" / "schaefer_schwarz_2019" / "studies_with_prereg.csv"
SCHAEFER_NON_PREREG_RAW = ROOT / "data" / "raw" / "corpus_candidates" / "schaefer_schwarz_2019" / "studies_without_prereg.xlsx"
SCORE_ORIG_PREREG = ROOT / "data" / "raw" / "corpus_candidates" / "score" / "orig_prereg-indicated.csv"
SCORE_PAPER_METADATA = ROOT / "data" / "raw" / "corpus_candidates" / "score" / "paper_metadata.csv"
CTGOV_EFFICACY_RAW = ROOT / "data" / "raw" / "corpus_candidates" / "ctgov_kg" / "efficacy_df.csv"
COMPARE_OUTCOME_ROWS = ROOT / "data" / "derived" / "corpus_candidates" / "compare_trials" / "compare_trials_outcome_rows.csv"
COMPARE_TRIALS = ROOT / "data" / "raw" / "corpus_candidates" / "compare_trials" / "compare_trials.csv"
PROTZKO_PROMOTED = HARVEST_PROMOTED_DIR / "protzko_nhb_pairs__promoted_pairs.csv"
PREREG_RESULTS = DATASET_DERIVED_DIR / "plot3_preregistered_results.csv"
PREREG_RESULTS_TSV = DATASET_DERIVED_DIR / "plot3_preregistered_results.tsv"
PREREG_DISPLAY_TABLE_TSV = DATASET_DERIVED_DIR / "plot3_preregistered_display_table.tsv"
PREREG_SENSITIVITY_RESULTS = DATASET_DERIVED_DIR / "plot3_preregistered_sensitivity_sidecar_rows.csv"
BRODEUR_PREREG_PAPER_MEDIANS = DATASET_DERIVED_DIR / "plot3_brodeur_preregistered_pap_paper_medians.csv"
PREREG_CTGOV_PRIMARY_RANDOMIZED_RESULTS = DATASET_DERIVED_DIR / "plot3_ctgov_phase2plus_primary_randomized_sidecar_rows.csv"
CTGOV_API_REGISTERED_ROWS = DATASET_DERIVED_DIR / "plot3_ctgov_api_registered_outcome_ratio_event_rows.csv.gz"
CTGOV_API_REGISTERED_TRIAL_MEDIANS = DATASET_DERIVED_DIR / "plot3_ctgov_api_registered_trial_medians.csv"
SCHEEL_QUOTE_RESCUE_CANDIDATES = DATASET_DERIVED_DIR / "plot3_scheel_quote_stat_rescue_candidates.csv"
VANDENAKKER_RESCUE_CANDIDATES = DATASET_DERIVED_DIR / "plot3_vandenakker_first_stat_candidates.csv"
VANDENAKKER_MEDIAN_CANDIDATES = DATASET_DERIVED_DIR / "plot3_vandenakker_matched_result_median_candidates.csv"
RPCB_PRECLINICAL_CANDIDATES = DATASET_DERIVED_DIR / "plot3_rpcb_preclinical_paper_level_candidates.csv"
SCORE_TEXT_CLAIM_CANDIDATES = DATASET_DERIVED_DIR / "plot3_score_text_claim_rescue_candidates.csv"
ALL_SOURCE_DN_ROWS = DATASET_DERIVED_DIR / "plot4_all_source_dn_rows.csv"
PLOT1_PAIR_DETAILS = DATASET_DERIVED_DIR / "plot1_replication_pair_details.csv"
PLOT2_PAPER_DETAILS = DATASET_DERIVED_DIR / "plot2_published_paper_details.csv"
PLOT_DOT_MEMBERSHIP = DATASET_DERIVED_DIR / "plot_dot_membership.tsv"
PLOT_DOT_REFERENCES_BIB = DATASET_DERIVED_DIR / "plot_dot_references.bib"
PLOT_PAPER_MEMBERSHIP = DATASET_DERIVED_DIR / "plot_paper_membership.tsv"
PLOT_PAPER_SUMMARY = DATASET_DERIVED_DIR / "plot_paper_summary.tsv"
PLOT_PAPER_EXCLUSIVITY_AUDIT = DATASET_DERIVED_DIR / "plot_paper_exclusivity_audit.tsv"
PLOT_RESULT_PARENT_CHILD = DATASET_DERIVED_DIR / "plot_result_parent_child.tsv"
PLOT_SOURCE_FAMILY_MEMBERSHIP = DATASET_DERIVED_DIR / "plot_source_family_membership.tsv"
PLOT_ASSIGNMENT_RULES = DATASET_DERIVED_DIR / "plot_assignment_rules.tsv"
PREREG_FIG = FIG_DIR / "plot3_preregistered_d_vs_n.png"
PREREG_SENSITIVITY_FIG = FIG_DIR / "plot3_preregistered_sensitivity_sidecar.png"
PREREG_CTGOV_PRIMARY_RANDOMIZED_FIG = FIG_DIR / "plot3_ctgov_phase2plus_primary_randomized_sidecar.png"
CTGOV_API_REGISTERED_TRIAL_MEDIAN_FIG = FIG_DIR / "plot3_ctgov_api_registered_trial_medians.png"
ALL_SOURCE_FIG = FIG_DIR / "plot4_all_source_dn_dump.png"

Z_05 = 1.959963984540054
DN_AXIS_X_CAP = 100_000.0
DN_AXIS_Y_MIN = 0.02
DN_AXIS_Y_MAX = 5.0


@dataclass(frozen=True)
class FigureSpec:
    token: str
    key: str
    path: Path
    caption: str


def as_bool(value: object) -> bool:
    text = str(value).strip().lower()
    return text in {"true", "1", "yes", "y", "t"}


def ensure_dirs() -> None:
    for path in [GENERATED, FIG_DIR, TABLE_DIR, TABLE_FRAGMENT_DIR, DATASET_DERIVED_DIR]:
        path.mkdir(parents=True, exist_ok=True)


def text_of(node) -> str:
    return " ".join(node.get_text(" ", strip=True).split())


def slugify(value: str, fallback: str) -> str:
    value = re.sub(r"[^A-Za-z0-9]+", "_", value.strip().lower()).strip("_")
    return value or fallback


def markdown_table(rows: list[list[str]]) -> str:
    if not rows:
        return ""
    width = max(len(row) for row in rows)
    padded = [row + [""] * (width - len(row)) for row in rows]
    header, body = padded[0], padded[1:]

    def clean(cell: str) -> str:
        return str(cell).replace("\n", " ").replace("|", "\\|").strip()

    lines = [
        "| " + " | ".join(clean(cell) for cell in header) + " |",
        "| " + " | ".join(["---"] * width) + " |",
    ]
    for row in body:
        lines.append("| " + " | ".join(clean(cell) for cell in row) + " |")
    return "\n".join(lines)


def markdown_table_block(rows: list[list[str]], classes: str) -> str:
    class_tokens = []
    for token in classes.split():
        class_tokens.append(token if token.startswith(".") else f".{token}")
    return "\n".join(
        [
            f"::: {{{' '.join(class_tokens)}}}",
            "",
            markdown_table(rows),
            "",
            ":::",
        ]
    )


PLOT2_STATUS_TO_CORPUS = {
    "statcheck psychology": "psychology_statcheck",
    "brodeur raw economics 2024": "economics_brodeur_2024",
    "szucs & ioannidis 2017": "szucs_ioannidis_2017",
    "dellavigna/linos academic nudge journals": "dellavigna_linos_2022",
    "turner antidepressant journal rows": "turner_antidepressants_2022",
    "yun rct numerical extraction": "yun_llm_meta_analysis",
    "metabus open bosco subset": "metabus_open_bosco",
    "rpcb cancer biology original effects": "rpcb_cancer_biology",
    "darpa score / cos claims": "score_cos_claims",
    "forrt fred": "forrt_fred",
    "replication-pair original-side bridge": "replication_pair_originals_bridge",
    "button/nord neuroscience": "button_nord_neuroscience",
    "metalab": "metalab",
    "havranek/meta-analysis.cz economics series": "havranek_eis",
    "kühberger psychology main results": "kuhberger_2014_main_results",
    "kuhberger psychology main results": "kuhberger_2014_main_results",
    "linden focal effects": "linden_2024_focal_effects",
    "schäfer/schwarz psychology articles (without preregistration)": "schaefer_schwarz_2019_without_prereg",
    "schaefer/schwarz psychology articles (without preregistration)": "schaefer_schwarz_2019_without_prereg",
    "schäfer/schwarz preregistered psychology articles": "schaefer_schwarz_2019_with_prereg",
    "schaefer/schwarz preregistered psychology articles": "schaefer_schwarz_2019_with_prereg",
    "motyl social/personality critical tests": "motyl_2017_critical_tests",
    "olsson/sundell social interventions": "olsson_sundell_2023_social_interventions",
    "esarey/wu political science main findings": "esarey_wu_2016_political_science_main_findings",
    "clinifact published primary pairs": "clinifact_published_primary_pairs",
    "havránek gasoline-income meta-analysis": "havranek_gasoline_income",
    "havranek gasoline-income meta-analysis": "havranek_gasoline_income",
    "havránek substitution meta-analysis": "havranek_substitution",
    "havranek substitution meta-analysis": "havranek_substitution",
    "havránek armington meta-analysis": "havranek_armington",
    "havranek armington meta-analysis": "havranek_armington",
    "havránek frisch extensive-margin meta-analysis": "havranek_frisch_extensive",
    "havranek frisch extensive-margin meta-analysis": "havranek_frisch_extensive",
    "havránek frisch intensive-margin meta-analysis": "havranek_frisch_intensive",
    "havranek frisch intensive-margin meta-analysis": "havranek_frisch_intensive",
    "gechert/havránek sigma meta-analysis": "havranek_sigma",
    "gechert/havranek sigma meta-analysis": "havranek_sigma",
    "gwas catalog": "gwas_catalog",
    "olivier 2024 cardiovascular rcts": "olivier_2024_cardio_rcts",
    "aact x pubmed primary outcomes": "aact_pubmed_primary_outcomes",
    "arelbundock political science via bear": "arelbundock_political_science_bear",
}

PLOT1_CITATION_KEYS = {
    "FReD filtered pair table": "tosh2024",
    "RPP canonical OSF csv": "collaboration2015",
    "Many Labs 2 public join": "klein2018",
    "Many Labs 5 overarching analyses": "ebersole2020manylabs5",
    "Altmejd harmonized Many Labs 1": "klein2014manylabs1",
    "Altmejd harmonized Many Labs 3": "ebersole2016manylabs3",
    "SCORE analyst join": "tyner2026",
    "LOOPR coding workbook": "soto2019loopr",
    "Boyce student replication corpus": "boyce2023studentreplication",
    "BRI primary t experiment table": "amaral2019brazilian",
    "Decision-market pair table": "holzmeister2025decisionmarket",
    "EPRP complete data": "cova2021estimating",
    "Communication privacy replication corpus": "masur2025privacy",
    "Communication privacy SEM paths": "masur2025privacy",
    "Coppock 2019 generalizability corpus": "coppock2019generalizability",
    "Management Science Replication Project": "davis2023managementscience",
    "PSA 006 trolley Greene": "bago2022trolley",
    "Doyen et al. 2012 article (manual)": "doyen2012priming",
    "Many Labs 4 local meta-analysis (manual)": "klein2022manylabs4",
    "Protzko 2023 NHB": "protzko2024highrep",
    "Protzko NHB asymmetry writeup": "protzko2024highrep",
    "Protzko NHB labels writeup": "protzko2024highrep",
    "Protzko NHB referrals writeup": "protzko2024highrep",
    "ReplicationSuccess SSRP.rda": "camerer2018",
    "ReplicationSuccess SSRP alias (manual)": "camerer2018",
    "ReplicationSuccess RProjects.rda": "camerer2016",
    "EERP — ReplicationSuccess RProjects.rda": "camerer2016",
    "EERP 2016 supplement (manual)": "camerer2016",
    "EERP effectdata.py": "camerer2016",
    "EERP marketdata.zip": "camerer2016",
    "SSRP 2018 supplement (manual)": "camerer2018",
    "SSRP D3": "camerer2018",
    "SSRP D6 beliefs": "camerer2018",
    "RPP project record alias (manual)": "collaboration2015",
    "RPP converted": "collaboration2015",
    "RPP jtLeek mirror": "collaboration2015",
    "I4R public workbook": "i4rPublicWorkbook",
    "ML1 summary workbook": "klein2014manylabs1",
    "ML3 manuscript tables bundle": "ebersole2016manylabs3",
    "ML4 public site results": "klein2022manylabs4",
    "PooledMarketR PM_data.Rdata": "pooledMarketRPackageData",
    "RPCB": "errington2021",
    "Border 2019": "border2019",
    "Marek 2022 BWAS paper (manual)": "marek2022",
    "251 Rescue Projects": "boyce2024rescue",
    "251 Rescue parsed data": "boyce2024rescue",
    "Appendix D supplemental": "douglass2026appendixD",
    "COVID online experiment replications": "peyton2021covidonline",
    "COVID online experiments YCLS summaries": "peyton2021covidonline",
    "Contextual bias in verbal credibility assessment": "oppen2026contextual",
    "Contextual bias in verbal credibility (OSF raw)": "oppen2026contextual",
    "EQIPD stagewise open-field lab contrasts": "arroyoaraujo2022eqipd",
    "Galak et al. 2012 psi meta-analysis (manual)": "galak2012psi",
    "Greed by SES replications": "balakrishnan2017greed",
    "Greed x SES meta-analysis script": "balakrishnan2017greed",
    "Lie and language": "jinAwesomeReplicabilityData",
    "Awesome lie-language paired raw csvs": "jinAwesomeReplicabilityData",
    "Awesome replicability-data repository": "jinAwesomeReplicabilityData",
    "Linguistic frame effect on blame and liability": "tonkovic2022linguisticOsf",
    "Linguistic frame liability clean csvs": "tonkovic2022linguisticOsf",
    "Mind body self centrality": "jinAwesomeReplicabilityData",
    "Awesome mind-body paired raw csvs": "jinAwesomeReplicabilityData",
    "O'Donnell 2018 site-level meta csvs": "odonnell2018dijksterhuis",
    "PSA 002 object orientation": "chen2025objectOrientation",
    "PSA-002 object orientation lab rows": "chen2025objectOrientation",
    "RRR Alogna 2014 (manual)": "alogna2014schooler",
    "Alogna 2014 table 1 site counts": "alogna2014schooler",
    "RRR Bouwmeester 2017": "bouwmeester2017rand",
    "RRR Bouwmeester 2017 (manual)": "bouwmeester2017rand",
    "RRR Cheung 2016": "cheung2016finkel",
    "RRR Cheung 2016 site csvs": "cheung2016finkel",
    "RRR Elliott 2021": "elliott2021flavell",
    "RRR Elliott 2021 aggregate table rows": "elliott2021flavell",
    "RRR Hagger 2016 (manual)": "hagger2016egodepletion",
    "Hagger 2016 RTV.csv": "hagger2016egodepletion",
    "RRR McCarthy 2018": "mccarthy2018srull",
    "RRR McCarthy 2018 site csvs": "mccarthy2018srull",
    "Srull-Wyer RRR paper (manual)": "mccarthy2018srull",
    "RRR Verschuere 2018": "verschuere2018mazar",
    "RRR Verschuere 2018 site csv": "verschuere2018mazar",
    "Ranehill 2015 power posing (manual)": "ranehill2015powerposing",
    "Sports science supplemental outcomes table": "murphy2025sportsReplication",
    "Vaidis 2024 prepared data subset": "vaidis2024dissonance",
    "Wood scaffolding direct replication": "smit2025scaffolding",
    "Wood scaffolding participant csv": "smit2025scaffolding",
    "Ying 2023 pilot-full-scale trials": "ying2023pilot",
    "Ying 2023 manual partial reconstruction": "ying2023pilot",
    "Awesome replicability paired raw csvs": "jinAwesomeReplicabilityData",
    "Clinical published replication workbook": "ioannidis2005contradicted",
    "Eerland 2016 Intention_attribution.csv": "eerland2016hart",
    "Eerland 2016 Intentionality.csv": "eerland2016hart",
    "Eerland 2016 imagery.csv": "eerland2016hart",
    "Pipeline supplement + packet data": "schweinsberg2016pipeline",
    "Stoevenbelt 2025 combined lab csv": "stoevenbelt2024johns",
    "Transparent Psi Project combined raw": "kekecs2023tpp",
    "Transparent Psi Project": "kekecs2023tpp",
    "Wagenmakers 2016 site csv": "wagenmakers2016strack",
    "Deceptive intentions verbal credibility replication": "kleinberg2018deceptive",
    "Deceptive intentions verbal credibility (OSF raw)": "kleinberg2018deceptive",
    "Online image credibility": "haim2025imagecredibility",
    "Online image credibility README equivalence table": "haim2025imagecredibility",
    "Retrieval extinction fear conditioning in rats": "luyten2017retrievalExtinction",
    "Retrieval-extinction rats xlsx": "luyten2017retrievalExtinction",
    "Manual paper-grounded pairs": "douglass2026manualPairs",
    "lead::angrist_learning_curve_2023": "angristLearningCurve2023Openicpsr",
    "lead::awesome_body_dissatisfaction": "jinAwesomeReplicabilityData",
    "lead::awesome_cleanliness_moral": "jinAwesomeReplicabilityData",
    "lead::awesome_climate_misinfo": "jinAwesomeReplicabilityData",
    "lead::awesome_emdr_misinfo": "jinAwesomeReplicabilityData",
    "lead::awesome_pain_coop": "jinAwesomeReplicabilityData",
    "lead::awesome_pain_tolerance": "jinAwesomeReplicabilityData",
    "lead::awesome_priming_exercise": "jinAwesomeReplicabilityData",
    "lead::awesome_queue": "jinAwesomeReplicabilityData",
    "lead::awesome_time_honest": "jinAwesomeReplicabilityData",
    "lead::border_2019": "border2019",
    "lead::coppock_2019": "coppock2019generalizability",
    "lead::eef_regrants": "eefProjectsIndex",
    "lead::eqipd_2022": "arroyoaraujo2022eqipd",
    "lead::ern_pe_rrr_openneuro": "ernPeRrrOpenNeuro",
    "Eyewitness ten-country paper table rescue": "ito2018eyewitnessTenCountries",
    "Eyewitness memory distortion in ten countries": "ito2018eyewitnessTenCountries",
    "lead::eyewitness_ten_countries_2018": "eyewitnessTenCountriesOsf",
    "lead::fred_diff_2024": "tosh2024",
    "lead::ibl_repro_ephys_2024": "iblReproEphysAws",
    "lead::ies_systematic_replication": "iesSystematicReplicationAwards",
    "lead::independent_replication_initiative": "klein2016independentReplicationInitiative",
    "lead::jaljuli_kafkafi_2023": "jaljuliKafkafi2023MousePhenome",
    "ManyBabies 3": "manyBabies3Osf",
    "lead::manybabies_3": "manyBabies3Osf",
    "lead::manyclasses_2": "manyClasses2Osf",
    "lead::media_priming_2017": "mediaPriming2017Dataverse",
    "lead::metaketa_i_2019": "metaketaIRepo",
    "lead::metaketa_iii_2021": "metaketaIIIProject",
    "lead::metaketa_iv_2021": "metaketaIVProject",
    "lead::mullinix_2015": "mullinix2015Dataverse",
    "lead::musicianship_eeg_2025": "musicianshipEegDataverse",
    "News discernment replication": "newsDiscernmentReplicationOsf",
    "lead::news_discernment_replication": "newsDiscernmentReplicationOsf",
    "lead::nieuwland_2018_delong": "nieuwland2018delong",
    "PSA 004 Turri article table rescue": "hall2024psa004Turri",
    "PSA 004 JTB Turri": "hall2024psa004Turri",
    "lead::psa_004_turri": "psa004TurriOsf",
    "Public-admin blame Wiley table reconstruction": "walker2024publicAdminBlame",
    "Public-administration blame experiment replication": "walker2024publicAdminBlame",
    "lead::public_admin_blame": "walker2024publicAdminBlame",
    "lead::rescue17_28classics": "boyce2024rescue",
    "lead::rpcb_e5nvr": "errington2021",
    "RRR Colling 2020 Att-SNARC table reconstruction": "rrrColling2020Osf",
    "RRR Colling 2020": "rrrColling2020Osf",
    "lead::rrr_colling_2020": "rrrColling2020Osf",
    "lead::self_control_fmri_2022": "selfControlFmriOsf",
    "lead::strategy_fit_2025": "strategyFitOsf",
    "lead::tpp_bem": "kekecs2023tpp",
    "lead::tyner_nosek_2026": "tyner2026",
    "lead::wood_porter_2019": "woodPorter2019Dataverse",
    "Clinical phase II to phase III pairs": "internalKerschbaumerPhaseIiIiiRheumatology",
    "Kerschbaumer 2020 rheumatology phase II/III": "internalKerschbaumerPhaseIiIiiRheumatology",
    "Li 2024 PD-1/PD-L1 phase II/III oncology": "internalLiPd1Pdl1PhaseIiIiiOncology",
    "Marcus Four Lab Replication Hcmv7": "internalMarcusFourLabReplicationLead",
    "lead::marcus_four_lab_replication_hcmv7": "internalMarcusFourLabReplicationLead",
    "Wils 2023 IBD phase II/III": "internalWilsIbdPhaseIiIii",
}

PLOT1_DISPLAY_LABELS = {
    "FReD filtered pair table": "FReD",
    "RPCB": "Reproducibility Project: Cancer Biology",
    "RPP canonical OSF csv": "Reproducibility Project: Psychology",
    "Many Labs 2 public join": "Many Labs 2",
    "Many Labs 5 overarching analyses": "Many Labs 5",
    "SCORE analyst join": "SCORE project",
    "LOOPR coding workbook": "LOOPR",
    "Boyce student replication corpus": "Student Replication Projects",
    "251 Rescue parsed data": "251 Rescue Projects",
    "BRI primary t experiment table": "Brazilian Reproducibility Initiative",
    "EPRP complete data": "EPRP",
    "Decision-market pair table": "Decision-Market Replication Project",
    "Communication privacy SEM paths": "Communication privacy replications",
    "Sports science supplemental outcomes table": "Sports science replications",
    "ReplicationSuccess SSRP.rda": "Social Sciences Replication Project",
    "ReplicationSuccess SSRP alias (manual)": "Social Sciences Replication Project",
    "ReplicationSuccess RProjects.rda": "Experimental Economics Replication Project",
    "EERP — ReplicationSuccess RProjects.rda": "Experimental Economics Replication Project",
}

PLOT1_LEAD_DISPLAY_LABELS = {
    "lead::angrist_learning_curve_2023": "Angrist learning-curve replication corpus",
    "lead::awesome_body_dissatisfaction": "Body dissatisfaction direct replication",
    "lead::awesome_cleanliness_moral": "Cleanliness and moral judgment",
    "lead::awesome_climate_misinfo": "Climate misinformation direct replication",
    "lead::awesome_emdr_misinfo": "EMDR and misinformation",
    "lead::awesome_pain_coop": "Pain and cooperation",
    "lead::awesome_pain_tolerance": "Pain tolerance direct replication",
    "lead::awesome_priming_exercise": "Priming and exercise direct replication",
    "lead::awesome_queue": "Queue design and worker productivity",
    "lead::awesome_time_honest": "Honesty and time pressure",
    "lead::border_2019": "Border 2019 candidate-gene replication",
    "lead::coppock_2019": "Coppock 2019 generalizability corpus",
    "lead::eef_regrants": "EEF regrants systematic replication candidates",
    "lead::eqipd_2022": "EQIPD Arroyo-Araujo 2022",
    "lead::ern_pe_rrr_openneuro": "ERN/Pe RRR OpenNeuro",
    "lead::eyewitness_ten_countries_2018": "Eyewitness memory distortion in ten countries",
    "lead::fred_diff_2024": "FReD differential-effects supplement",
    "lead::ibl_repro_ephys_2024": "IBL reproducible electrophysiology",
    "lead::ies_systematic_replication": "IES systematic replication awards",
    "lead::independent_replication_initiative": "Independent Replication Initiative",
    "lead::jaljuli_kafkafi_2023": "Jaljuli-Kafkafi multi-lab rodent replication",
    "lead::manybabies_3": "ManyBabies 3",
    "lead::manyclasses_2": "ManyClasses 2",
    "lead::media_priming_2017": "Media priming direct replication",
    "lead::metaketa_i_2019": "EGAP Metaketa I",
    "lead::metaketa_iii_2021": "EGAP Metaketa III",
    "lead::metaketa_iv_2021": "EGAP Metaketa IV",
    "lead::mullinix_2015": "Mullinix-Leeper-Druckman-Freese generalizability experiments",
    "lead::musicianship_eeg_2025": "Musicianship EEG multi-site replication",
    "lead::news_discernment_replication": "News discernment replication",
    "lead::nieuwland_2018_delong": "Nieuwland 2018 DeLong replication",
    "lead::psa_004_turri": "PSA 004 JTB Turri",
    "lead::public_admin_blame": "Public-administration blame experiment replication",
    "lead::rescue17_28classics": "251 Rescue Projects",
    "lead::rpcb_e5nvr": "Reproducibility Project: Cancer Biology E5/NVR materials",
    "lead::rrr_colling_2020": "RRR Colling 2020",
    "lead::self_control_fmri_2022": "Self-control neuroimaging replication",
    "lead::strategy_fit_2025": "Strategy-situation fit replication",
    "lead::tpp_bem": "Transparent Psi Project",
    "lead::tyner_nosek_2026": "SCORE project lead materials",
    "lead::wood_porter_2019": "Wood and Porter backfire-effect replication",
}

PLOT1_FAMILY_LABEL_OVERRIDES = {
    "FReD filtered pair table": "FReD",
    "lead::fred_diff_2024": "FReD",
    "SCORE analyst join": "SCORE project",
    "lead::tyner_nosek_2026": "SCORE project",
    "RPCB": "Reproducibility Project: Cancer Biology",
    "lead::rpcb_e5nvr": "Reproducibility Project: Cancer Biology",
    "RPP canonical OSF csv": "Reproducibility Project: Psychology",
    "RPP project record alias (manual)": "Reproducibility Project: Psychology",
    "RPP converted": "Reproducibility Project: Psychology",
    "RPP jtLeek mirror": "Reproducibility Project: Psychology",
    "ReplicationSuccess SSRP.rda": "Social Sciences Replication Project",
    "ReplicationSuccess SSRP alias (manual)": "Social Sciences Replication Project",
    "SSRP 2018 supplement (manual)": "Social Sciences Replication Project",
    "SSRP D3": "Social Sciences Replication Project",
    "SSRP D6 beliefs": "Social Sciences Replication Project",
    "ReplicationSuccess RProjects.rda": "Experimental Economics Replication Project",
    "EERP — ReplicationSuccess RProjects.rda": "Experimental Economics Replication Project",
    "EERP 2016 supplement (manual)": "Experimental Economics Replication Project",
    "EERP effectdata.py": "Experimental Economics Replication Project",
    "EERP marketdata.zip": "Experimental Economics Replication Project",
    "Altmejd harmonized Many Labs 1": "Many Labs 1",
    "ML1 summary workbook": "Many Labs 1",
    "Altmejd harmonized Many Labs 3": "Many Labs 3",
    "ML3 manuscript tables bundle": "Many Labs 3",
    "Many Labs 4 local meta-analysis (manual)": "Many Labs 4",
    "ML4 public site results": "Many Labs 4",
    "Alogna 2014 table 1 site counts": "RRR Alogna 2014",
    "RRR Alogna 2014 (manual)": "RRR Alogna 2014",
    "Hagger 2016 RTV.csv": "RRR Hagger 2016",
    "RRR Hagger 2016 (manual)": "RRR Hagger 2016",
    "RRR Bouwmeester 2017": "RRR Bouwmeester 2017",
    "RRR Bouwmeester 2017 (manual)": "RRR Bouwmeester 2017",
    "RRR McCarthy 2018": "RRR McCarthy 2018",
    "Srull-Wyer RRR paper (manual)": "RRR McCarthy 2018",
    "RRR Cheung 2016": "RRR Cheung 2016",
    "RRR Elliott 2021": "RRR Elliott 2021",
    "RRR Verschuere 2018": "RRR Verschuere 2018",
    "Eerland 2016 Intention_attribution.csv": "Eerland 2016 Hart intention-attribution replications",
    "Eerland 2016 Intentionality.csv": "Eerland 2016 Hart intention-attribution replications",
    "Eerland 2016 imagery.csv": "Eerland 2016 Hart intention-attribution replications",
    "Awesome lie-language paired raw csvs": "Awesome replicability-data repository",
    "Lie and language": "Awesome replicability-data repository",
    "Awesome mind-body paired raw csvs": "Awesome replicability-data repository",
    "Mind body self centrality": "Awesome replicability-data repository",
    "Awesome replicability paired raw csvs": "Awesome replicability-data repository",
    "Cleanliness and moral judgment": "Awesome replicability-data repository",
    "EMDR and misinformation": "Awesome replicability-data repository",
    "Pain and cooperation": "Awesome replicability-data repository",
    "Queue design and worker productivity": "Awesome replicability-data repository",
    "Honesty and time pressure": "Awesome replicability-data repository",
    "lead::awesome_body_dissatisfaction": "Awesome replicability-data repository",
    "lead::awesome_cleanliness_moral": "Awesome replicability-data repository",
    "lead::awesome_climate_misinfo": "Awesome replicability-data repository",
    "lead::awesome_emdr_misinfo": "Awesome replicability-data repository",
    "lead::awesome_pain_coop": "Awesome replicability-data repository",
    "lead::awesome_pain_tolerance": "Awesome replicability-data repository",
    "lead::awesome_priming_exercise": "Awesome replicability-data repository",
    "lead::awesome_queue": "Awesome replicability-data repository",
    "lead::awesome_time_honest": "Awesome replicability-data repository",
    "PSA-002 object orientation lab rows": "PSA 002 object orientation",
    "Online image credibility README equivalence table": "Online image credibility",
    "Deceptive intentions verbal credibility (OSF raw)": "Deceptive intentions verbal credibility replication",
    "Retrieval-extinction rats xlsx": "Retrieval extinction fear conditioning in rats",
    "Communication privacy SEM/spec-curve paths": "Communication privacy replications",
    "Communication privacy SEM paths": "Communication privacy replications",
    "Communication privacy replication corpus": "Communication privacy replications",
    "COVID online experiments YCLS summaries": "COVID online experiment replications",
    "Contextual bias in verbal credibility (OSF raw)": "Contextual bias in verbal credibility assessment",
    "Linguistic frame liability clean csvs": "Linguistic frame effect on blame and liability",
    "Public-admin blame Wiley table reconstruction": "Public-administration blame experiment replication",
    "lead::public_admin_blame": "Public-administration blame experiment replication",
    "RRR Colling 2020 Att-SNARC table reconstruction": "RRR Colling 2020",
    "Greed x SES meta-analysis script": "Greed by SES replications",
    "Wood scaffolding participant csv": "Wood scaffolding direct replication",
    "Ying 2023 manual partial reconstruction": "Ying 2023 pilot-full-scale trials",
    "lead::eqipd_2022": "EQIPD stagewise open-field lab contrasts",
    "lead::rescue17_28classics": "251 Rescue Projects",
    "Transparent Psi Project combined raw": "Transparent Psi Project",
    "lead::tpp_bem": "Transparent Psi Project",
}

PLOT1_SOURCE_FAMILY_DESCRIPTIONS = {
    "FReD": "FORRT/FReD is a living replication database that aggregates large-scale replication projects, public replication lists, and individual submissions. Rows pair a replication study with the original study it targets, mostly psychology and adjacent social/behavioral claims.",
    "SCORE project": "DARPA SCORE/COS social and behavioral reproducibility corpus. The local join links original paper claims to version-of-record replication outcomes from the SCORE evaluation workflow.",
    "LOOPR": "Life Outcomes of Personality Replication project workbook. It codes original and replication effects for personality-outcome associations, with Fisher-z and bounded numeric fallbacks converted into D/N pair rows.",
    "Reproducibility Project: Psychology": "Open Science Collaboration psychology replication project: 100 psychology studies sampled from three journals and replicated by many teams. Local rows come from the canonical OSF data plus a small manual project-record fallback.",
    "Reproducibility Project: Cancer Biology": "Cancer Biology replication project: preclinical experimental claims selected from influential cancer-biology papers and replicated by independent laboratories. Local rows use the project effect-level analysis file.",
    "Student Replication Projects": "Boyce/Mathur/Frank student replication corpus: classroom and training-course replications of published social/behavioral findings, curated as target-versus-replication effect pairs.",
    "251 Rescue Projects": "Rescue-project corpus of classic psychology findings and replication attempts. Local rows come from parsed rescue files after removing exact overlap with the Boyce student-replication source.",
    "Many Labs 1": "Many Labs 1 multi-lab psychology replication project, harmonized by Altmejd. It contains many-site replications of classic psychology effects with aggregate original and replication effect information.",
    "Many Labs 2": "Many Labs 2 multi-lab psychology replication project. The local join combines public replication summary rows with original-effect files to form original-versus-replication pairs.",
    "Many Labs 3": "Many Labs 3 multi-lab psychology replication project, using Altmejd's harmonized project tables where effect sizes and sample sizes are pair-buildable.",
    "Many Labs 4": "Many Labs 4 multi-lab psychology replication project. Local rows are recovered from public site/meta-analysis outputs where both original and replication sides can be paired.",
    "Many Labs 5": "Many Labs 5 multi-lab psychology replication project. Local rows use the public figure data and single-effect files for version-specific sample sizes.",
    "Brazilian Reproducibility Initiative": "Brazilian Reproducibility Initiative: coordinated replications of experimental psychology findings by Brazilian labs. Local rows use project primary-analysis outputs and exclude sensitivity variants.",
    "EPRP": "Experimental Philosophy Replicability Project: coordinated replications of experimental-philosophy findings. Local rows use the project complete-data file and recover effect sizes from reported statistics where needed.",
    "Decision-Market Replication Project": "Decision-market replication project in experimental economics and behavioral science. The public table contains original and replication D/N fields plus market forecasts.",
    "Experimental Economics Replication Project": "Experimental Economics Replication Project, a coordinated replication of laboratory economics findings. Local rows use the Experimental Economics subset of the ReplicationSuccess RProjects object plus manual supplement rows.",
    "Social Sciences Replication Project": "Social Sciences Replication Project: coordinated replications of social-science studies from high-profile journals. Local rows use ReplicationSuccess plus a few manual/support rows.",
    "Management Science Replication Project": "Management Science Replication Project: replications of operations and management-science experiments. Local rows are parsed from project report tables into original-versus-replication effect pairs.",
    "Sports science replications": "Sports-science replication corpus. Public supplemental reported-effect tables are joined to sample-size workbooks and kept where both original and replication sides are numeric.",
    "Communication privacy replications": "Communication-privacy replication corpus covering SEM/specification-curve paths in media and communication research. Local rows are promoted from project source files into pair-level D/N rows.",
    "Coppock 2019 generalizability corpus": "Coppock's political-science generalizability project reanalyzes published survey experiments in new MTurk and GfK samples. The Dataverse archive includes standardized original and replication treatment-effect estimates plus stacked study data for model-specific sample sizes.",
    "Pipeline Project": "Many-analysts Pipeline Project source material. Local rows convert key-test statistics from the supplement and packet data into comparable pair rows.",
    "Awesome replicability-data repository": "Jin/Ying awesome-replicability-data is a GitHub collection of cleaned paired original-and-replication raw datasets for individual direct-replication examples. Local rows use source-specific parsers for the paired CSVs that expose a clear condition, outcome, original sample, and replication sample.",
    "Awesome replicability paired raw CSVs": "Jin/Ying awesome-replicability-data is a GitHub collection of cleaned paired original-and-replication raw datasets for individual direct-replication examples. Local rows use source-specific parsers for the paired CSVs that expose a clear condition, outcome, original sample, and replication sample.",
    "Clinical published replication workbook": "Clinical highly cited replication workbook. It pairs highly cited clinical findings with later larger or contradictory evidence where OR/RR/HR metrics and sample sizes can be converted.",
    "EQIPD stagewise open-field lab contrasts": "EQIPD preclinical multi-lab project on replicability and generalizability of open-field findings under protocol harmonization. Local rows are stagewise lab contrasts converted to D/N where possible.",
    "Appendix D supplemental": "Hand-built appendix source used as a coverage floor for undercovered replication families. It is a support/fallback source rather than an independent corpus.",
    "COVID online experiment replications": "COVID-era online experiment replication source. Local rows use public summary files that pair original claims with online replication results.",
    "Contextual bias in verbal credibility assessment": "Direct replication source for contextual bias in verbal credibility assessment, a forensic/psychology credibility-judgment effect.",
    "Linguistic frame effect on blame and liability": "Preregistered direct replication of the linguistic frame effect on perceived blame and financial liability in legal/psychology judgment.",
    "PSA 006 trolley Greene": "Psychological Science Accelerator trolley-problem replication project, with country-level rows for the Greene trolley dilemma effect.",
    "I4R public workbook": "Institute for Replication public meta-database workbook covering computational reproducibility, coding errors, and robustness checks for economics and political-science papers. It is large and useful context, but its estimate-level sheet is coefficient/SE robustness material rather than new-sample original-versus-replication D/N pairs.",
    "Manual paper-grounded pairs": "Manual recovery layer grounded in supplements, DOI targets, project records, and downloaded papers where automated tables missed appendix-aligned pairs.",
    "PooledMarketR PM_data.Rdata": "PooledMarketR package data with outcome, prediction-market, and survey metadata across EERP, Many Labs 2, RPP, and SSRP-style replication projects. It supports market/forecast checks and overlap audits, but it is not a richer original-versus-replication effect-size pair table.",
    "Clinical highly cited replications": "Clinical-medicine replication workbook pairing highly cited early clinical findings with later larger or contradictory evidence; local rows keep medical effects where OR, RR, or HR plus sample sizes can be converted.",
    "Eerland 2016 Hart intention-attribution replications": "Eerland/Hart direct-replication source in social psychology, covering intention-attribution, intentionality, and imagery experiments with public per-study CSVs.",
    "Wood scaffolding direct replication": "Direct replication source for a behavioral wood-scaffolding effect; local rows use participant-level source material where original and replication D/N can be paired.",
    "Doyen et al. 2012 article (manual)": "Manual extraction from Doyen et al.'s social-priming replication of elderly-prime walking-speed effects, used as a paper-grounded direct replication pair.",
    "Galak et al. 2012 psi meta-analysis (manual)": "Manual extraction from Galak et al.'s replication/meta-analysis of Bem-style psi effects, a parapsychology limit-case direct-replication source.",
    "Greed by SES replications": "Social-psychology direct-replication source testing the reported relationship between socioeconomic status and greed-related behavior.",
    "Lie and language": "Direct-replication source from the awesome-replicability-data collection for a language-and-deception effect.",
    "Marek 2022 BWAS": "Large-sample brain-wide association study source used as a high-N comparison for brain-behavior association claims.",
    "Mind body self centrality": "Direct-replication source from the awesome-replicability-data collection for a mind-body/self-centrality effect.",
    "O'Donnell 2018 site-level meta csvs": "Registered-replication-style psychology source with site-level meta-analytic rows for the O'Donnell/Dijksterhuis target effect.",
    "Protzko 2023 NHB": "High-replicability psychology replication source from Protzko and colleagues, with local rows recovered from project writeups.",
    "Ranehill 2015 power posing (manual)": "Manual extraction from the Ranehill et al. replication of power-posing effects on hormones and risk taking.",
    "Stoevenbelt 2025 combined lab csv": "Participant-level multi-lab replication source for stereotype-threat effects; local rows use the combined lab CSV and registered exclusions.",
    "Transparent Psi Project combined raw": "Transparent Psi Project is a high-powered multi-lab replication of Bem-style precognition/psi effects. Local rows use the combined raw project data to build the pooled erotic-trial hit-rate comparison against the original Bem study.",
    "Vaidis 2024 prepared data subset": "Participant-level multi-lab cognitive-dissonance replication source, converted into per-lab induced-compliance contrasts.",
    "Wagenmakers 2016 site csv": "Registered Replication Report source for the Strack facial-feedback hypothesis, using public site-level rows.",
    "Ying 2023 pilot-full-scale trials": "Pilot-versus-full-scale trial source reconstructed from Ying's dissertation materials. One pilot/full-scale D/N pair is live; a local PubMed/open-access probe tightened five more candidate notes without finding enough public arm/variance information for promotion.",
    "Deceptive intentions verbal credibility replication": "Forensic psychology direct-replication source on deceptive intentions and verbal credibility assessment.",
    "Online image credibility": "Media and communication direct-replication source testing online image-credibility judgments.",
    "Retrieval extinction fear conditioning in rats": "Preclinical animal replication source for retrieval-extinction fear-conditioning effects in rats.",
    "Independent Replication Initiative": "Independent Replication Initiative source family, a collection of independently run psychology/social-science direct replications.",
    "Jaljuli Kafkafi multi lab rodent replication": "Preclinical multi-lab rodent replication source from the Jaljuli/Kafkafi mouse-phenome materials.",
    "Angrist learning-curve replication corpus": "Angrist and colleagues' education replication corpus follows targeted-instruction implementation across country trials. The OpenICPSR package is now local with three Stata monitoring datasets, code, figures, and one output table.",
    "Border 2019 candidate gene replication": "Border et al. 2019 re-tests historical candidate-gene claims for major depression using large-scale GWAS-style genetic data. The local PDF is useful for native genetic summaries, but it is not a direct small-original larger-replication D/N table.",
    "EGAP Metaketa III": "EGAP Metaketa III is a coordinated natural-resource-governance field-experiment project. The local harvest now includes the parent replication package and Uganda, Brazil, and Costa Rica component payloads with R/Stata outputs.",
    "EGAP Metaketa IV": "EGAP Metaketa IV is the community-policing Metaketa. The local harvest now includes integrated OSF xqd3v RDS result outputs, article tables, and selected processed country files.",
    "ERN Pe RRR OpenNeuro": "Registered Replication Report material for ERN/Pe psychometrics. OpenNeuro provides raw EEG and OSF 8cbua provides summary and analysis artifacts, but these are native ERP materials rather than a compact pair table.",
    "ManyBabies 3": "ManyBabies 3 is a multi-lab developmental-psychology replication of Marcus-style infant rule learning. The local OSF pull contains registered-report PDFs, appendices, and a lab manual; the public mb3-rules GitHub archive adds stimuli, pilot materials, syllable ratings, and analysis notebooks. A 2026 manuscript/preprint trail appears to exist, but no public machine-readable final result repository is confirmed locally.",
    "ManyClasses 2": "ManyClasses 2 is a multi-classroom education experiment that repeated the same classroom intervention across course sections. The local files contain Terracotta-style participant outcomes and Bayesian analysis scripts, but not an explicit original-versus-replication D/N pair table.",
    "Media priming direct replication": "Political-communication/media-psychology preregistered replication data for one media-priming target effect. Dataverse identifies the intended Excel file, but the file is restricted; the public Cambridge appendix is local as a paper fallback and appears to recover replication N, not the target effect estimate.",
    "Mullinix Leeper Druckman Freese 2015": "Mullinix, Leeper, Druckman, and Freese's survey-experiment generalizability project compares treatment effects across convenience, student, staff, MTurk, and TESS/GfK samples. The public Dataverse bundle contains combined data, scripts, and result logs, but the effects remain native survey-scale contrasts.",
    "Musicianship EEG multi site replication": "Large-scale multi-site neuroscience study of whether musical training is associated with early auditory neural encoding. The local GitHub zip contains MATLAB analysis code and processed EEG summaries rather than a smaller-original/larger-replication pair table.",
    "Self control neuroimaging replication": "Self-control neuroimaging replication source for the Hare et al. dietary self-control fMRI paradigm. OSF materials, OpenNeuro raw-data leads, and an open paper mirror are local, but no final pair-results table is exposed.",
    "News discernment replication": "OSF materials for a France/Germany news-discernment or misinformation intervention replication, with country-level clean survey workbooks and analysis scripts. The downloaded files are intervention datasets rather than a ready smaller-original/larger-replication D/N pair table.",
    "Nieuwland 2018 DeLong replication": "Psycholinguistics multi-lab replication source for the DeLong sentence-comprehension effect.",
    "Public-administration blame experiment replication": "Public-administration replication of the James et al. blame-attribution experiment. Local rows are paper-table reconstructions from the original James et al. 2016 regression table and Walker et al. 2024 England, Hong Kong, and South Korea replication tables.",
    "RRR Colling 2020": "Registered Replication Report for the Att-SNARC effect from Fischer et al. The local GitHub archive contains Fischer original estimates, processed replication meta-analysis outputs, and raw participant files; promoted rows use a within-subject dz-compatible table reconstruction.",
    "Strategy situation fit replication": "Social/personality psychology replication source for strategy-situation fit effects.",
    "Transparent Psi Project": "Transparent Psi Project is a high-powered multi-lab replication of Bem-style precognition/psi effects. Local rows use the combined raw project data to build the pooled erotic-trial hit-rate comparison against the original Bem study.",
    "Wood and Porter elusive backfire effect": "Political-communication replication source for Wood and Porter's elusive backfire-effect experiments. The Dataverse bundle is local with survey and correction files plus R scripts; the suggested OSF pes2y mirror was checked and is a different fake-news memory project.",
    "Eyewitness memory distortion in ten countries": "Cross-national eyewitness-memory replication/generalizability source on memory distortion across ten countries. The checked a35rx OSF node still has empty public storage, but the accepted-manuscript forest plot reports original New Zealand and country-level Hedges-g/N values, allowing a five-row paper-table rescue.",
    "PSA 004 JTB Turri": "Psychological Science Accelerator replication source for the Turri justified-true-belief vignette effect. The checked erm92 project exposes a codebook while its data and analysis children are empty; n5b3w provides original/pretest support, but the published article tables allow one strict Darrel/Squirrel OR-based row rescue.",
}

PLOT1_WHY_OVERRIDES = {
    "Angrist learning-curve replication corpus": "The downloaded OpenICPSR package is a real machine-readable payload, but it reproduces implementation-monitoring outputs rather than original-versus-replication treatment-effect D/N rows.",
    "Border 2019 candidate gene replication": "The primary PDF is local and the source is real, but the AJP supplemental endpoint returned 403 here. The visible results are native genetic association summaries, not direct original-versus-replication D/N rows.",
    "EGAP Metaketa III": "The parent replication package and several component payloads are now local, including site-estimate and R/Stata files. They are useful native field-experiment evidence, but not an original-versus-replication D/N table for this figure.",
    "EGAP Metaketa IV": "Integrated OSF xqd3v RDS outputs and article tables are now local. They are native community-policing field-experiment estimates and therefore belong in a native-metric or field-experiment lane, not the current original-versus-replication D/N plot.",
    "ERN Pe RRR OpenNeuro": "Raw EEG and OSF summary artifacts are local, but they are replication-side ERP materials on native metrics. The original-side D/N anchor is still missing from the machine-readable payload.",
    "Eyewitness memory distortion in ten countries": "The OSF payload remains unresolved, but the accepted manuscript reports Hedges-g values and analyzed Ns. Five country-level paper-fallback rows now pass the current gates; the nested aggregate row is intentionally not added.",
    "ManyBabies 3": "The public materials are useful for protocol and pilot auditing, but the final infant site-level result data are not public in the checked locations. The reported mb3-analysis repository returned 404; a final manuscript/preprint trail improves the lead but still does not provide a confirmed row-ready repository.",
    "Media priming direct replication": "The Dataverse metadata identifies media_priming.xls, but the file is restricted and the direct API returns a blocked payload. The public Cambridge DOCX appendix is local as a fallback and appears to recover N_rep=104, but not the effect estimate needed for a D/N row.",
    "PSA 004 JTB Turri": "The final Stage 2 OSF payload is still unresolved for region-level extraction, but the published article reports original OR/N and Darrel-vignette replication counts. One strict Darrel/Squirrel row is now promoted from article tables; the expected region rows still need OSF/analysis-folder extraction.",
    "Public-administration blame experiment replication": "The OSF registration did not expose raw respondent data, but the Wiley article and supporting tables report matched treatment-contrast t statistics and balanced arm sizes. Those tables now supply 9 promoted D/N reconstruction rows.",
    "RRR Colling 2020": "The local GitHub archive includes Fischer original dz values and the Colling et al. selected Model 1 fixed-effect z statistics. Four Att-SNARC ISI rows are now promoted using abs(z)/sqrt(N) as a within-subject dz-compatible replication proxy.",
    "Self control neuroimaging replication": "OSF materials, raw fMRI leads, and an open paper mirror are local, but no final machine-readable table pairs the Hare original result with the replication on the shared D/N axis.",
    "Wood and Porter elusive backfire effect": "The Dataverse bundle is local and rich, but the direct original-target pairing and shared-D conversion policy still need a native-metric or hand-extraction pass. The suggested OSF pes2y mirror was not this project.",
}

PLOT2_CITATION_KEYS = {
    "statcheck psychology": "hartgerink2016",
    "psychology_statcheck": "hartgerink2016",
    "Brodeur raw economics 2024": "brodeur2020",
    "economics_brodeur_2024": "brodeur2020",
    "Szucs & Ioannidis 2017": "szucs2017",
    "szucs_ioannidis_2017": "szucs2017",
    "DellaVigna/Linos academic nudge journals": "dellavigna2022",
    "academic nudge journals": "dellavigna2022",
    "dellavigna_linos_2022": "dellavigna2022",
    "Turner antidepressant journal rows": "turner2008",
    "antidepressant journal rows": "turner2008",
    "turner_antidepressants_2022": "turner2008",
    "DARPA SCORE / COS claims": "tyner2026",
    "DARPA SCORE extracted claims": "tyner2026",
    "DARPA SCORE structured original outcomes": "tyner2026",
    "score_cos_claims": "tyner2026",
    "FORRT FReD": "tosh2024",
    "forrt_fred": "tosh2024",
    "Button/Nord neuroscience": "button2013",
    "button_nord_neuroscience": "button2013",
    "GWAS Catalog": "yengo2022",
    "gwas_catalog": "yengo2022",
    "Havranek/meta-analysis.cz economics series": "havranek2015",
    "Havranek EIS": "havranek2015",
    "Havranek substitution meta-analysis": "havranek2015",
    "Havranek Armington meta-analysis": "havranekArmingtonData",
    "Havranek gasoline-income meta-analysis": "havranekGasolineIncomeData",
    "Havranek Frisch extensive-margin meta-analysis": "havranekFrischData",
    "Havranek Frisch intensive-margin meta-analysis": "havranekFrischData",
    "Gechert/Havranek sigma meta-analysis": "gechert2022",
    "havranek_eis": "havranek2015",
    "havranek_substitution": "havranek2015",
    "havranek_armington": "havranekArmingtonData",
    "havranek_gasoline_income": "havranekGasolineIncomeData",
    "havranek_frisch_extensive": "havranekFrischData",
    "havranek_frisch_intensive": "havranekFrischData",
    "havranek_sigma": "gechert2022",
    "RPCB cancer biology original effects": "errington2021",
    "rpcb_cancer_biology": "errington2021",
    "AACT x PubMed primary outcomes": "du2024",
    "ArelBundock political science via BEAR": "arelbundock2026underpowered",
    "MetaLab": "bergmann2018metalab",
    "metalab": "bergmann2018metalab",
    "Olivier 2024 cardiovascular RCTs": "olivier2024cardioRcts",
    "Yun RCT numerical extraction": "yun2024llmExtraction",
    "yun_llm_meta_analysis": "yun2024llmExtraction",
    "metaBUS open Bosco subset": "bosco2020metabus",
    "metabus_open_bosco": "bosco2020metabus",
    "Esarey/Wu political science main findings": "esareyWu2016",
    "esarey_wu_2016_political_science_main_findings": "esareyWu2016",
    "Kuehberger psychology main results": "kuhberger2014publicationBias",
    "Kühberger psychology main results": "kuhberger2014publicationBias",
    "kuhberger_2014_main_results": "kuhberger2014publicationBias",
    "Linden focal effects": "linden2024publicationBiasPsychology",
    "linden_2024_focal_effects": "linden2024publicationBiasPsychology",
    "Motyl social/personality critical tests": "motyl2017state",
    "motyl_2017_critical_tests": "motyl2017state",
    "Schaefer/Schwarz psychology articles (without preregistration)": "schaefer2019meaningfulness",
    "Schaefer/Schwarz preregistered psychology articles": "schaefer2019meaningfulness",
    "Schäfer/Schwarz psychology articles (without preregistration)": "schaefer2019meaningfulness",
    "Schäfer/Schwarz preregistered psychology articles": "schaefer2019meaningfulness",
    "schaefer_schwarz_2019_without_prereg": "schaefer2019meaningfulness",
    "schaefer_schwarz_2019_with_prereg": "schaefer2019meaningfulness",
    "Olsson/Sundell social interventions": "olsson2023publicationBias",
    "olsson_sundell_2023_social_interventions": "olsson2023publicationBias",
    "CliniFact published primary pairs": "zhang2025clinifact",
    "clinifact_published_primary_pairs": "zhang2025clinifact",
    "ClinicalTrials.gov registry-results comparator": "du2024",
    "ctgov_finer_grained_kg": "du2024",
    "Linden random-effect comparator rows": "linden2024publicationBiasPsychology",
    "linden_2024_random_effects": "linden2024publicationBiasPsychology",
    "replication-pair original-side bridge": "internalPlot2ReplicationPairOriginalsBridge",
    "replication_pair_originals_bridge": "internalPlot2ReplicationPairOriginalsBridge",
    "Aczel negative-claim t-test comparator": "internalAczelNegativeClaimComparator",
    "aczel_2018_negative_claim_ttests": "internalAczelNegativeClaimComparator",
}

PLOT2_DISPLAY_LABELS = {
    "statcheck psychology": "statcheck psychology corpus",
    "psychology_statcheck": "statcheck psychology corpus",
    "Brodeur raw economics 2024": "Brodeur economics corpus",
    "economics_brodeur_2024": "Brodeur economics corpus",
    "Szucs & Ioannidis 2017": "Szucs and Ioannidis test-statistic corpus",
    "szucs_ioannidis_2017": "Szucs and Ioannidis test-statistic corpus",
    "DellaVigna/Linos academic nudge journals": "academic nudge journals",
    "dellavigna_linos_2022": "academic nudge journals",
    "Turner antidepressant journal rows": "antidepressant journal rows",
    "turner_antidepressants_2022": "antidepressant journal rows",
    "DARPA SCORE / COS claims": "DARPA SCORE / COS claims",
    "score_cos_claims": "DARPA SCORE / COS claims",
    "FORRT FReD": "FORRT FReD",
    "forrt_fred": "FORRT FReD",
    "replication_pair_originals_bridge": "replication-pair original-side bridge",
    "button_nord_neuroscience": "Button/Nord neuroscience",
    "metabus_open_bosco": "metaBUS open Bosco subset",
    "metalab": "MetaLab",
    "rpcb_cancer_biology": "RPCB cancer biology original effects",
    "yun_llm_meta_analysis": "Yun RCT numerical extraction",
    "esarey_wu_2016_political_science_main_findings": "Esarey/Wu political science main findings",
    "kuhberger_2014_main_results": "Kühberger psychology main results",
    "linden_2024_focal_effects": "Linden focal effects",
    "motyl_2017_critical_tests": "Motyl social/personality critical tests",
    "schaefer_schwarz_2019_without_prereg": "Schäfer/Schwarz psychology articles (without preregistration)",
    "schaefer_schwarz_2019_with_prereg": "Schäfer/Schwarz preregistered psychology articles",
    "olsson_sundell_2023_social_interventions": "Olsson/Sundell social interventions",
    "clinifact_published_primary_pairs": "CliniFact published primary pairs",
    "havranek_eis": "Havránek EIS",
    "havranek_substitution": "Havránek substitution meta-analysis",
    "havranek_armington": "Havránek Armington meta-analysis",
    "havranek_gasoline_income": "Havránek gasoline-income meta-analysis",
    "havranek_frisch_extensive": "Havránek Frisch extensive-margin meta-analysis",
    "havranek_frisch_intensive": "Havránek Frisch intensive-margin meta-analysis",
    "havranek_sigma": "Gechert/Havránek sigma meta-analysis",
    "gwas_catalog": "GWAS Catalog",
    "olivier_2024_cardio_rcts": "Olivier 2024 cardiovascular RCTs",
    "aact_pubmed_primary_outcomes": "AACT x PubMed primary outcomes",
    "arelbundock_political_science_bear": "ArelBundock political science via BEAR",
    "aczel_2018_negative_claim_ttests": "Aczel negative-claim t-test comparator",
    "ctgov_finer_grained_kg": "ClinicalTrials.gov registry-results comparator",
    "linden_2024_random_effects": "Linden random-effect comparator rows",
}

PLOT2_SOURCE_DESCRIPTIONS = {
    "score_cos_claims": "Social and behavioral claims sampled for DARPA SCORE/COS. Possible Plot 2 candidate because the sampled journal claims expose enough N/effect/p text to reconstruct paper-level D/N, though many rows are claim-level rather than declared headline results.",
    "metabus_open_bosco": "Open metaBUS subset for Journal of Applied Psychology and Personnel Psychology correlations. Possible candidate because the rows are peer-reviewed article effects with r and N; the caveat is that they are correlational personnel-psychology effects rather than treatment or headline-result rows.",
    "forrt_fred": "FORRT/FReD original findings selected for documented replications. Possible candidate because original-side titles, DOIs, N, and effects are available for many replication targets; the caveat is replication-target selection rather than broad journal sampling.",
    "schaefer_schwarz_2019_without_prereg": "Schäfer/Schwarz non-preregistered psychology-article sample. Possible candidate because each sampled paper has a coded key-question effect with recoverable D/N.",
    "button_nord_neuroscience": "Primary studies appearing in neuroscience meta-analyses. Possible candidate because D/N is recoverable at the published-study level; the caveat is meta-analysis mediation rather than direct paper-main-result extraction.",
    "motyl_2017_critical_tests": "Motyl social/personality article sample with coded critical hypothesized tests. Possible candidate because the tests are close to focal claims, though some papers contribute multiple study-level tests.",
    "kuhberger_2014_main_results": "Kühberger psychology main-result corpus. Possible candidate because it is a random psychology-article sample with one coded main-question result per paper and recoverable D/N.",
    "replication_pair_originals_bridge": "Internal bridge from Plot 1 originals. Possible candidate because every plotted replication pair has an original-side D/N; the bridge adds only original DOI/title targets not already represented in Plot 2.",
    "clinifact_published_primary_pairs": "Published clinical-trial reports linked to registry primary outcomes through the local CliniFact bridge. Possible candidate because the rows are journal-side primary-outcome proxies with recoverable D/N.",
    "olsson_sundell_2023_social_interventions": "Published Swedish social-intervention effectiveness articles. Possible candidate because primary-outcome flags identify the plotted paper-level effectiveness results.",
    "economics_brodeur_2024": "Published top-journal economics table tests from Brodeur-style p-value data. Possible candidate because RCT/IV/DID rows have N and test statistics, but no paper-main-result selector is available.",
    "metalab": "MetaLab developmental-psychology database. Possible candidate because peer-reviewed flags and D/N exist, but rows are curated through a meta-analytic database rather than direct journal extraction.",
    "esarey_wu_2016_political_science_main_findings": "Esarey/Wu political-science main-finding sample. Possible candidate because the source explicitly codes published article main findings and the local parser keeps the authors' focal model restriction.",
    "linden_2024_focal_effects": "Linden psychology focal-effect sample. Possible candidate because author-coded focal effects are recoverable with D/N, while non-focal random-effect rows remain comparator-only.",
    "schaefer_schwarz_2019_with_prereg": "Schäfer/Schwarz preregistered psychology-article sample. Possible candidate because each sampled paper has coded key-question effects with D/N and preregistration status.",
    "yun_llm_meta_analysis": "Numerical intervention-comparator-outcome rows extracted from PMC RCT full texts. Possible candidate because arm-level RCT statistics can yield D/N; the remaining caveat is missing primary-outcome selection.",
    "havranek_gasoline_income": "Published-source estimates from the Havránek gasoline-income meta-analysis. Possible candidate because observations and effect estimates are present, but the rows are meta-analysis mediated rather than direct paper-main results.",
    "dellavigna_linos_2022": "Academic nudge RCT rows from DellaVigna/Linos. Possible candidate because journal-published treatment-arm effects have outcome and arm fields; the strongest available selector is most-significant arm, not prespecified primary outcome.",
    "havranek_eis": "Economics source estimates from the Havránek EIS/meta-analysis.cz series. Possible candidate because D/N can be reconstructed for published estimates, but rows are meta-analysis mediated and not paper-main-result selected.",
    "havranek_substitution": "Economics source estimates from a Havránek substitution meta-analysis. Possible candidate because publication flags and observation counts exist, but rows are meta-analysis mediated.",
    "havranek_armington": "Economics source estimates from the Havránek Armington meta-analysis. Possible candidate because publication flags and observation counts exist, but rows are meta-analysis mediated.",
    "turner_antidepressants_2022": "Published antidepressant efficacy rows from Turner-style journal/regulatory comparisons. Possible candidate because journal-side trial efficacy effects are clean, small, and D/N-ready.",
    "rpcb_cancer_biology": "Original published preclinical cancer-biology effects selected for RPCB replication. Possible candidate because they are key original claims with D/N, but they are project-selected rather than broad journal-sampled.",
    "havranek_frisch_extensive": "Economics source estimates from the Havránek Frisch extensive-margin meta-analysis. Possible candidate because publication flags and observation counts exist, but rows are meta-analysis mediated.",
    "havranek_frisch_intensive": "Economics source estimates from the Havránek Frisch intensive-margin meta-analysis. Possible candidate because publication flags and observation counts exist, but rows are meta-analysis mediated.",
    "havranek_sigma": "Economics source estimates from the Gechert/Havránek sigma meta-analysis. Possible candidate because publication flags and observation counts exist, but rows are meta-analysis mediated.",
    "psychology_statcheck": "All extractable APA-style significance tests from psychology journal articles. Possible candidate because it is direct journal text with test statistics and N/df, but it lacks paper-main-result selection.",
    "gwas_catalog": "Curated published genome-wide-significant association hits. Possible candidate for a large D/N surface because sample sizes and effects exist, but it is not a sampled article-level treatment/result corpus.",
    "szucs_ioannidis_2017": "Szucs/Ioannidis cognitive-neuroscience and psychology test-statistic corpus. Possible candidate because journal test statistics can be converted to D/N; it stays out until paper grouping and main-result selection are decoded.",
    "olivier_2024_cardio_rcts": "Olivier cardiovascular RCT corpus. Possible candidate because the article reports 344 major cardiovascular RCTs with primary endpoints and 263 superiority effect-size rows; it stays out until a public row-level file or local reconstruction exists.",
    "aact_pubmed_primary_outcomes": "AACT/PubMed registered-primary-outcome bridge. Possible candidate because registry primary outcomes can identify focal medical endpoints, but this is not yet a journal-extracted article-result table.",
    "arelbundock_political_science_bear": "Political-science estimates routed through BEAR/meta-analytic sources. Possible candidate because effects and Ns can exist, but source rows mix journals, reports, and working papers and lack direct main-result flags.",
    "aczel_2018_negative_claim_ttests": "Aczel et al. null-hypothesis/negative-claim psychology audit. Possible candidate because the public table contains published article t tests with recoverable D/N; the caveat is that rows are selected from negative or nonsignificant claims rather than focal published claims.",
    "ctgov_finer_grained_kg": "ClinicalTrials.gov registry-results extraction. Possible D/N comparator because registry primary-result rows expose N and p-value-derived effect proxies, but it is registry evidence rather than published-paper endpoints.",
    "linden_2024_random_effects": "Random-effect counterpart from the Linden psychology sample. Possible candidate because it has one random effect per sampled paper with D/N, but it is intentionally held out as a comparator to the focal-effect selection used in Plot 2.",
}

PLOT2_COMPARATOR_ONLY_SOURCE_NOTES = {
    "aczel_2018_negative_claim_ttests": {
        "status_label": "comparator-only negative-claim audit",
        "why": "local D/N comparator, excluded by policy",
        "why_detail": (
            "Public Aczel et al. null-hypothesis support audit yields 62 usable t-test D/N rows "
            "across 30 paper units after applying the authors' strict analyzable-subset rule. "
            "It is not included because the selection rule targets negative or nonsignificant claims, "
            "not focal published-paper endpoints."
        ),
    },
    "ctgov_finer_grained_kg": {
        "status_label": "registry-results comparator",
        "why": "local D/N comparator, excluded by policy",
        "why_detail": (
            "The finer-grained ClinicalTrials.gov results extraction has primary registry-result "
            "D/N proxies for 7,722 trial/outcome units. It is not included because Plot 2 is a "
            "published-paper endpoint plot, while these rows are registry results rather than "
            "journal-published article endpoints."
        ),
    },
    "linden_2024_random_effects": {
        "status_label": "random-effect comparator from an included source",
        "why": "local D/N comparator, excluded by policy",
        "why_detail": (
            "The Linden random-effect rows cover the same 158 sampled psychology papers as the "
            "included focal-effect rows, but they are deliberately non-focal within-paper "
            "comparator effects. Plot 2 keeps the author-coded focal effects and excludes these "
            "random-effect counterparts."
        ),
    },
}

PLOT3_CITATION_KEYS = {
    "Scheel et al. 2021 preregistered-hypotheses corpus": "scheel2021",
    "Dorison et al. 2022 PSA-CR001 pooled preregistered rows": "dorison2022",
    "PSA-CR002 cognitive reappraisal preregistered hypotheses": "wang2021psacr002",
    "PSA004 true-belief/Gettier pooled preregistered row": "hall2024psa004Turri",
    "ManyBabies 1 infant-directed speech pooled preregistered row": "manyBabies2020Ids",
    "ManyBabies 1 Bilingual infant-directed speech pooled preregistered row": "byersHeinlein2021manybabiesBilingual",
    "ManyClasses 1 feedback pooled preregistered row": "fyfe2021manyclasses1",
    "Schäfer/Schwarz 2019 preregistered psychology articles": "schaefer2019meaningfulness",
    "Schäfer/Schwarz 2019 non-preregistered psychology articles": "schaefer2019meaningfulness",
    "SCORE/COS preregistration-indicated original papers": "tyner2026",
    "Allen and Mehler 2019 Registered Reports support-rate review": "allenMehler2019OpenScience",
    "van den Akker matched preregistered-result paper medians": "vanDenAkkerSelectiveHypothesis2023",
    "van den Akker selective-hypothesis-reporting psychology corpus": "vanDenAkkerSelectiveHypothesis2023",
    "Protzko et al. 2024 High-Replicability Research project": "protzko2024highrep",
    "AACT x PubMed registered primary outcomes": "du2024",
    "ClinicalTrials.gov registry-result D/N comparator": "du2024",
    "ClinicalTrials.gov API registered outcome-result universe": "du2024",
    "ClinicalTrials.gov phase-2+ primary randomized registry rows": "du2024",
    "CliniFact published trial primary-outcome rows": "zhang2025clinifact",
    "Brodeur et al. 2024 preregistered/PAP economics table tests": "brodeur2020",
    "Transparent Psi Project / Bem preregistered replication": "kekecs2023tpp",
    "ManyBabies 2 knowledge/ignorance registered-report materials": "manyBabies2AnalysisRepo",
    "ManyBabies 3 rule-learning registered-report materials": "manyBabies3Osf",
    "ManyBabies 4 helpers/hinderers registered-report materials": "manyBabies4Project",
    "van den Akker preregistration-in-practice matched hypothesis corpus": "vanDenAkkerPreregPractice",
    "ERN/Pe RRR OpenNeuro and OSF analysis hubs": "ernPeRrrOpenNeuro",
    "Linden et al. 2024 focal/random psychology sample": "linden2024publicationBiasPsychology",
    "ManyClasses 2 classroom registered-report materials": "manyClasses2Osf",
    "EGAP Metaketa I information/accountability pooled PAP row": "metaketaIRepo",
    "EGAP Metaketa III natural-resource monitoring pooled PAP row": "metaketaIIIProject",
    "EGAP Metaketa IV community-policing pooled PAP row": "metaketaIVProject",
    "Mousa 2020 Iraq soccer social-cohesion preregistered field experiment": "mousa2020soccerZenodo",
    "Good Politicians preregistered political-candidacy field experiment": "goodPoliticiansZenodo",
    "Ghana debates preregistered candidate-debates field experiment": "ghanaDebatesDataverse",
    "Vietnam legislator-responsiveness preregistered field experiment": "vietnamLegislatorResponsivenessDataverse",
    "Vietnam National Assembly main responsiveness preregistered field experiment": "vietnamMainResponsivenessDataverse",
    "Golden Gulzar Sonnet political-responsiveness preregistered field experiment": "goldenGulzarSonnetDataverse",
    "Kalla Broockman 2018 preregistered campaign-contact field-experiment archive": "kallaBroockman2018Dataverse",
    "Local Elites state-capacity tax-compliance preregistered field experiment": "localElitesOpenicpsr",
    "Hewitt et al. campaign-ad persuasion preregistered experiment archive": "hewittCampaignExperimentsDataverse",
    "Hensel Rink political-activist motivation preregistered field experiment": "henselRinkPoliticalActivistsDataverse",
    "Wood Hoy Pryke China-aid attitudes preregistered survey experiment": "woodHoyPrykeChinaAidDataverse",
    "Senegal learning-accountability preregistered information field experiment": "senegalLearningAccountabilityDataverse",
    "Public-service job-attributes preregistered conjoint experiment": "publicServiceJobAttributesDataverse",
    "Bangladesh authoritarian-election information-campaign preregistered field experiment": "bangladeshElectionZenodo",
    "Political Activists as Free-Riders preregistered canvassing field experiment": "politicalActivistsFreeridingZenodo",
    "Policing in patriarchy Women Help Desks preregistered field experiment": "policingPatriarchyDataverse",
    "India anti-vote-buying radio-campaign preregistered field experiment": "voteBuyingRadioDataverse",
    "Kotsadam Keller Elwert interethnic-contact preregistered field experiment": "interethnicContactDataverse",
    "Immigration message-or-messenger preregistered survey experiment": "immigrationBeliefsDataverse",
    "Favero Pedersen COVID information-cue preregistered survey experiment": "covidTogethernessDataverse",
    "Medicine-theft remote-tracking preregistered governance field experiment": "medicineTheftDataverse",
    "Ukrainian-refugee destination-choice preregistered conjoint experiment": "refugeeDestinationZenodo",
    "Baraza public-service delivery preregistered community-monitoring field experiment": "barazaGithub",
    "Direct-aid humanitarian-governance preregistered field experiment": "directAidGithub",
    "Bangladesh school-WASH transparency preregistered field experiment": "bangladeshWashDataverse",
    "COVID Emperor social-norm preregistered survey experiment": "covidEmperorOsf",
    "COVID vaccine-hesitancy targeted-message preregistered survey experiment": "vaccineHesitancyOsf",
    "Liberia Partnership Schools preregistered education-governance field experiment": "liberiaPslAeaRegistry",
    "Azevedo et al. JEPS preregistered political-knowledge replication": "azevedoJepsDataverse",
    "TESS Graham 1155 explicit-PAP political-behavior survey experiment": "tessGraham1155",
    "TESS Johnson 1389 explicit-PAP school-choice survey experiment": "tessJohnson1389",
    "EGAP Metaketa I information/accountability native ATE rows": "metaketaIRepo",
    "EGAP Metaketa III natural-resource monitoring native rows": "metaketaIIIProject",
    "EGAP Metaketa IV community-policing native rows": "metaketaIVProject",
    "TESS peer-reviewed survey-experiment archive": "tessPastStudiesArchive",
    "RPCB eLife Registered Report replication effects": "errington2021",
    "Communication privacy preregistered replication corpus": "masur2025privacy",
    "Retrieval-extinction rats preregistered replication": "luyten2017retrievalExtinction",
    "COMPare prespecified clinical-trial outcome audit": "internalCompareClinicalOutcomeAudit",
    "FORRT FReD / Replication Database": "tosh2024",
    "FReD archived workflow workbook / OSF Registries queue": "tosh2024",
    "Many Labs 1-5 project-level replication rows": "internalManyLabsProjectLevelAudit",
    "Nordic trial registration-publication linkage database": "internalNordicTrialPublicationLinkage",
    "Political-science PAP Dataverse/DIME/SCORE rescue worklist": "internalPoliticalScienceRescueWorklist",
    "Psychological Science Accelerator replication-pair rows": "internalPsaReplicationPairRows",
    "Registered Replication Reports Plot 1 pair rows": "internalRrrPlot1PairRows",
    "Registered Replication Reports per-lab rows": "internalRrrPerLabRows",
    "Self-control fMRI preregistered replication materials": "selfControlFmriOsf",
    "Twomey et al. 2021 kinesiology article audit": "internalTwomeyKinesiologyAudit",
}

PLOT3_DISPLAY_LABELS = {
    "Scheel et al. 2021 preregistered-hypotheses corpus": "Registered Reports preregistered-hypotheses corpus",
    "Dorison et al. 2022 PSA-CR001 pooled preregistered rows": "PSA-CR001 pooled preregistered rows",
    "PSA-CR002 cognitive reappraisal preregistered hypotheses": "PSA-CR002 cognitive reappraisal hypotheses",
    "PSA004 true-belief/Gettier pooled preregistered row": "PSA004 true-belief/Gettier pooled row",
    "ManyBabies 1 infant-directed speech pooled preregistered row": "ManyBabies 1 IDS pooled row",
    "ManyBabies 1 Bilingual infant-directed speech pooled preregistered row": "ManyBabies 1 bilingual IDS pooled row",
    "ManyClasses 1 feedback pooled preregistered row": "ManyClasses 1 feedback pooled row",
    "Schäfer/Schwarz 2019 preregistered psychology articles": "Schäfer/Schwarz preregistered psychology articles",
    "Schäfer/Schwarz 2019 non-preregistered psychology articles": "Schäfer/Schwarz non-preregistered comparator",
    "SCORE/COS preregistration-indicated original papers": "SCORE/COS preregistration-indicated papers",
    "Allen and Mehler 2019 Registered Reports support-rate review": "Allen/Mehler RR support-rate review",
    "van den Akker matched preregistered-result paper medians": "van den Akker matched-result medians",
    "van den Akker selective-hypothesis-reporting psychology corpus": "van den Akker selective-hypothesis-reporting corpus",
    "Protzko et al. 2024 High-Replicability Research project": "High-Replicability Research project",
    "AACT x PubMed registered primary outcomes": "AACT x PubMed registered primary outcomes",
    "ClinicalTrials.gov registry-result D/N comparator": "ClinicalTrials.gov registry-result D/N comparator",
    "CliniFact published trial primary-outcome rows": "CliniFact published trial primary-outcome rows",
    "ClinicalTrials.gov phase-2+ primary randomized registry rows": "CT.gov phase-2+ primary randomized rows",
    "Brodeur et al. 2024 preregistered/PAP economics table tests": "Brodeur preregistered/PAP table tests",
    "Registered Replication Reports per-lab rows": "Registered Replication Reports per-lab rows",
    "Registered Replication Reports Plot 1 pair rows": "Registered Replication Reports Plot 1 pair rows",
    "Many Labs 1-5 project-level replication rows": "Many Labs 1-5 project-level replication rows",
    "Psychological Science Accelerator replication-pair rows": "PSA replication-pair rows",
    "Transparent Psi Project / Bem preregistered replication": "Transparent Psi Project / Bem row",
    "ManyBabies 2 knowledge/ignorance registered-report materials": "ManyBabies 2 native model-coefficient materials",
    "ManyBabies 3 rule-learning registered-report materials": "ManyBabies 3 registered-report materials",
    "ManyBabies 4 helpers/hinderers registered-report materials": "ManyBabies 4 helpers/hinderers RR materials",
    "van den Akker preregistration-in-practice matched hypothesis corpus": "van den Akker preregistration-in-practice corpus",
    "ERN/Pe RRR OpenNeuro and OSF analysis hubs": "ERN/Pe RRR OpenNeuro/OSF hubs",
    "Self-control fMRI preregistered replication materials": "Self-control fMRI preregistered materials",
    "Twomey et al. 2021 kinesiology article audit": "Twomey kinesiology article audit",
    "Linden et al. 2024 focal/random psychology sample": "Linden focal/random psychology sample",
    "Nordic trial registration-publication linkage database": "Nordic trial registration-publication linkage",
    "FORRT FReD / Replication Database": "FORRT FReD / Replication Database",
    "FReD archived workflow workbook / OSF Registries queue": "FReD archived workflow rescue queue",
    "ManyClasses 2 classroom registered-report materials": "ManyClasses 2 classroom materials",
    "EGAP Metaketa I information/accountability pooled PAP row": "EGAP Metaketa I pooled PAP row",
    "EGAP Metaketa III natural-resource monitoring pooled PAP row": "EGAP Metaketa III pooled PAP row",
    "EGAP Metaketa IV community-policing pooled PAP row": "EGAP Metaketa IV pooled PAP row",
    "Mousa 2020 Iraq soccer social-cohesion preregistered field experiment": "Mousa 2020 Iraq soccer field experiment",
    "Good Politicians preregistered political-candidacy field experiment": "Good Politicians field experiment",
    "Ghana debates preregistered candidate-debates field experiment": "Ghana debates field experiment",
    "Vietnam legislator-responsiveness preregistered field experiment": "Vietnam legislator responsiveness",
    "Vietnam National Assembly main responsiveness preregistered field experiment": "Vietnam National Assembly responsiveness",
    "Golden Gulzar Sonnet political-responsiveness preregistered field experiment": "Golden/Gulzar/Sonnet responsiveness",
    "Kalla Broockman 2018 preregistered campaign-contact field-experiment archive": "Kalla/Broockman campaign contact",
    "Local Elites state-capacity tax-compliance preregistered field experiment": "Local Elites tax compliance",
    "Hewitt et al. campaign-ad persuasion preregistered experiment archive": "Campaign-ad persuasion archive",
    "Hensel Rink political-activist motivation preregistered field experiment": "Political activists field experiment",
    "Wood Hoy Pryke China-aid attitudes preregistered survey experiment": "China-aid attitudes survey experiment",
    "Senegal learning-accountability preregistered information field experiment": "Senegal accountability field experiment",
    "Public-service job-attributes preregistered conjoint experiment": "Public-service job-attributes experiment",
    "Bangladesh authoritarian-election information-campaign preregistered field experiment": "Bangladesh election information field experiment",
    "Political Activists as Free-Riders preregistered canvassing field experiment": "Political activists free-riding experiment",
    "Policing in patriarchy Women Help Desks preregistered field experiment": "Policing in patriarchy field experiment",
    "Azevedo et al. JEPS preregistered political-knowledge replication": "JEPS political-knowledge replication",
    "TESS Graham 1155 explicit-PAP political-behavior survey experiment": "TESS Graham 1155 survey experiment",
    "TESS Johnson 1389 explicit-PAP school-choice survey experiment": "TESS Johnson 1389 survey experiment",
    "COVID Emperor social-norm preregistered survey experiment": "COVID Emperor social-norm experiment",
    "COVID vaccine-hesitancy targeted-message preregistered survey experiment": "COVID vaccine-hesitancy message experiment",
    "Liberia Partnership Schools preregistered education-governance field experiment": "Liberia Partnership Schools",
    "EGAP Metaketa I information/accountability native ATE rows": "EGAP Metaketa I native ATE rows",
    "EGAP Metaketa III natural-resource monitoring native rows": "EGAP Metaketa III native rows",
    "EGAP Metaketa IV community-policing native rows": "EGAP Metaketa IV native rows",
    "TESS peer-reviewed survey-experiment archive": "TESS survey-experiment archive",
    "Political-science PAP Dataverse/DIME/SCORE rescue worklist": "Political-science rescue worklist",
    "RPCB eLife Registered Report replication effects": "RPCB Registered Report replication effects",
    "Communication privacy preregistered replication corpus": "Communication privacy preregistered corpus",
    "Retrieval-extinction rats preregistered replication": "Retrieval-extinction rats preregistered replication",
    "COMPare prespecified clinical-trial outcome audit": "COMPare prespecified outcome audit",
}


def citation_gap_priority(plot_name: str, inclusion_status: str, label: str) -> str:
    if "replication-pair" in label.lower() and "bridge" in label.lower():
        return "low"
    artifact_like = bool(re.search(r"\b(csv|xlsx|zip|py|rdata|workbook|table|mirror|supplement|raw)\b", label, flags=re.I))
    if plot_name in {"Plot 1", "Plot 2", "Plot 3"} and inclusion_status in {"included", "included_live_rows"} and not artifact_like:
        return "high"
    if inclusion_status in {"included", "included_live_rows", "support_only", "support_only_not_row_contributing", "integrated_not_plotted"}:
        return "medium"
    return "low"


def yes_no(value: bool) -> str:
    return "yes" if bool(value) else "no"


def safe_text(value: object) -> str:
    if pd.isna(value):
        return ""
    return str(value).strip()


def first_nonempty(values: object) -> str:
    for value in values:
        text = safe_text(value)
        if text:
            return text
    return ""


def normalize_doi_value(value: object) -> str:
    text = safe_text(value).lower()
    text = re.sub(r"^https?://(?:dx\.)?doi\.org/", "", text)
    text = re.sub(r"^doi:\s*", "", text)
    text = re.sub(r"^doi\.org/", "", text)
    text = re.sub(r"^doi:", "", text)
    return text.strip().rstrip(".")


def plot3_default_field(source_family: object) -> str:
    text = safe_text(source_family).lower()
    if "manyclasses" in text or "learning and instruction" in text:
        return "education"
    if "metaketa" in text or "egap" in text or "tess" in text:
        return "political science"
    if "cancer biology" in text or "rpcb" in text or "preclinical" in text:
        return "preclinical biology"
    if "score" in text:
        return "mixed social/behavioral science"
    return "psychology and health"


def display_field_label(value: object) -> str:
    text = safe_text(value) or "unknown field"
    return {
        "psychology and health": "Psychology/health",
        "political science": "Political science",
        "economics and finance": "Economics/finance",
        "sociology and criminology": "Sociology/criminology",
        "business": "Business",
        "education": "Education",
        "preclinical biology": "Preclinical biology",
        "clinical medicine": "Clinical medicine",
        "mixed social/behavioral science": "Mixed social/behavioral science",
    }.get(text, text.replace("_", " ").title())


def fmt_int(value: object) -> str:
    if pd.isna(value) or value == "":
        return ""
    return f"{int(value):,}"


def fmt_number(value: object, digits: int = 2) -> str:
    if pd.isna(value) or value == "":
        return ""
    return f"{float(value):,.{digits}f}"


def groups_by_descending_count(df: pd.DataFrame, column: str) -> list[tuple[object, pd.DataFrame]]:
    counts = df[column].value_counts(dropna=False)
    groups: list[tuple[object, pd.DataFrame]] = []
    for value in counts.index:
        mask = df[column].isna() if pd.isna(value) else df[column].eq(value)
        groups.append((value, df.loc[mask].copy()))
    return groups


def point_alpha_for_count(count: int, base: float = 0.64) -> float:
    if count >= 1000:
        return min(base, 0.34)
    if count >= 100:
        return min(base, 0.50)
    return min(base, 0.68)


def build_tess_study_index() -> pd.DataFrame:
    """Scrape the public TESS past-studies index into a stable extraction queue."""
    url = "https://tessexperiments.org/paststudies"
    columns = [
        "source_family",
        "year",
        "study_slug",
        "title",
        "study_url",
        "sample_size",
        "field_period",
        "data_materials_url",
        "pap_urls",
        "manuscript_or_publication_urls",
        "has_hypotheses",
        "has_outcomes",
        "has_summary_results",
        "summary_result_stat_flags",
        "summary_results_text",
        "row_status",
        "prereg_evidence",
        "d_n_status",
        "notes",
    ]
    if TESS_STUDY_INDEX.exists() and os.environ.get("REFRESH_TESS_INDEX") != "1":
        cached = pd.read_csv(TESS_STUDY_INDEX)
        for column in columns:
            if column not in cached.columns:
                cached[column] = "" if column not in {"has_hypotheses", "has_outcomes", "has_summary_results"} else False
        cached = cached[columns]
        cached.to_csv(TESS_STUDY_INDEX, index=False)
        return cached

    try:
        request = Request(url, headers={"User-Agent": "Mozilla/5.0"})
        html = urlopen(request, timeout=30).read().decode("utf-8", "replace")
    except Exception:
        if TESS_STUDY_INDEX.exists():
            cached = pd.read_csv(TESS_STUDY_INDEX)
            for column in columns:
                if column not in cached.columns:
                    cached[column] = "" if column not in {"has_hypotheses", "has_outcomes", "has_summary_results"} else False
            cached = cached[columns]
            cached.to_csv(TESS_STUDY_INDEX, index=False)
            return cached
        return pd.DataFrame(columns=columns)

    soup = BeautifulSoup(html, "html.parser")
    rows: list[dict[str, object]] = []
    current_year = ""
    for node in soup.find_all(["h3", "a"]):
        if node.name == "h3":
            year_text = node.get_text(" ", strip=True)
            if re.fullmatch(r"20\d{2}", year_text):
                current_year = year_text
            continue
        href = node.get("href") or ""
        if "./study/" not in href and not href.startswith("/study/") and "/study/" not in href:
            continue
        study_url = urljoin(url, href)
        match = re.search(r"/study/([^/?#]+)", study_url)
        if not match:
            continue
        rows.append(
            {
                "source_family": "TESS peer-reviewed survey-experiment archive",
                "year": current_year,
                "study_slug": match.group(1),
                "title": node.get_text(" ", strip=True),
                "study_url": study_url,
                "sample_size": "",
                "field_period": "",
                "data_materials_url": "",
                "pap_urls": "",
                "manuscript_or_publication_urls": "",
                "has_hypotheses": False,
                "has_outcomes": False,
                "has_summary_results": False,
                "summary_result_stat_flags": "",
                "summary_results_text": "",
                "row_status": "candidate_queue_only",
                "prereg_evidence": "TESS peer-reviewed proposal/study page predates fielding at the platform level; verify per study before promotion",
                "d_n_status": "missing final paper-level D/N until linked publication or Roper/data extraction",
                "notes": "Do not plot from this queue until the linked final publication/result and analytic N are extracted.",
            }
        )
    out = pd.DataFrame(rows, columns=columns)
    if not out.empty:
        out = out.drop_duplicates("study_slug", keep="first").sort_values(
            ["year", "study_slug"], ascending=[False, True]
        )
        refresh_pages = os.environ.get("REFRESH_TESS_PAGES") == "1"
        enrich_slugs = {
            slug.strip()
            for slug in os.environ.get("TESS_ENRICH_SLUGS", "").split(",")
            if slug.strip()
        }

        def section_text(lines: list[str], start: str, stops: set[str]) -> str:
            try:
                start_idx = lines.index(start)
            except ValueError:
                return ""
            collected: list[str] = []
            for line in lines[start_idx + 1 :]:
                if line in stops:
                    break
                collected.append(line)
            return " ".join(collected).strip()

        def value_after_label(lines: list[str], label: str) -> str:
            for idx, line in enumerate(lines):
                if line.rstrip(":").lower() == label.lower() and idx + 1 < len(lines):
                    return lines[idx + 1].strip()
            return ""

        def enrich_study(row: dict[str, object]) -> dict[str, object]:
            try:
                request = Request(safe_text(row["study_url"]), headers={"User-Agent": "Mozilla/5.0"})
                html = urlopen(request, timeout=6).read().decode("utf-8", "replace")
            except Exception as exc:
                row["notes"] = f"{row['notes']} Page-enrichment failed: {type(exc).__name__}."
                return row
            soup = BeautifulSoup(html, "html.parser")
            text = soup.get_text("\n", strip=True)
            lines = [line.strip() for line in text.splitlines() if line.strip()]
            all_urls = sorted(set(re.findall(r"https?://[^\s),.]+/?", text)))
            link_urls = [
                urljoin(safe_text(row["study_url"]), a.get("href"))
                for a in soup.select("a[href]")
                if a.get("href")
            ]
            data_url = ""
            for a in soup.select("a[href]"):
                label = a.get_text(" ", strip=True).lower()
                if "download data" in label or "study materials" in label:
                    data_url = urljoin(safe_text(row["study_url"]), a.get("href"))
                    break
            pap_urls = [
                found
                for found in all_urls
                if "osf.io" in found.lower()
                and found.rstrip("/") != data_url.rstrip("/")
                and re.search(r"(pre[- ]analysis|analysis plan|pap|plan)", text[max(text.find(found) - 80, 0) : text.find(found) + 120], flags=re.I)
            ]
            pub_urls = [
                found
                for found in sorted(set(all_urls + link_urls))
                if any(token in found.lower() for token in ["doi.org", "preprints", "socarxiv", "cambridge.org", "journals", "springer", "science.org"])
            ]
            sample_size = value_after_label(lines, "Sample size")
            field_period = value_after_label(lines, "Field period")
            summary = section_text(lines, "Summary of Results", {"Additional Information", "links"})
            stat_flags = []
            for label, pattern in [
                ("B/SE", r"\bB\s*=|s\.?e\.?\s*="),
                ("chi-square", r"chi[- ]square|test statistic\s*="),
                ("F", r"\bF\s*\("),
                ("p", r"\bp\s*[<=>]"),
                ("d", r"\bd\s*="),
            ]:
                if re.search(pattern, summary, flags=re.I):
                    stat_flags.append(label)
            row["sample_size"] = sample_size.replace(",", "")
            row["field_period"] = field_period
            row["data_materials_url"] = data_url
            row["pap_urls"] = ";".join(sorted(set(pap_urls)))
            row["manuscript_or_publication_urls"] = ";".join(sorted(set(pub_urls)))
            row["has_hypotheses"] = "Hypotheses" in lines
            row["has_outcomes"] = "Outcomes" in lines
            row["has_summary_results"] = bool(summary)
            row["summary_result_stat_flags"] = ";".join(stat_flags)
            row["summary_results_text"] = summary[:1200]
            if sample_size and summary and stat_flags:
                row["row_status"] = "native_metric_rescue_candidate"
                row["d_n_status"] = "sample size and native summary statistic surfaced; D conversion still requires raw outcomes, SDs, arm probabilities, or a justified test-statistic conversion"
            return row

        if refresh_pages or enrich_slugs:
            if refresh_pages:
                to_enrich = out
            else:
                to_enrich = out.loc[out["study_slug"].astype(str).isin(enrich_slugs)].copy()
            enriched_by_slug: dict[str, dict[str, object]] = {}
            with ThreadPoolExecutor(max_workers=8) as executor:
                futures = [executor.submit(enrich_study, row.to_dict()) for _, row in to_enrich.iterrows()]
                for future in as_completed(futures):
                    enriched = future.result()
                    enriched_by_slug[safe_text(enriched.get("study_slug"))] = enriched
            if enriched_by_slug:
                out = out.copy()
                out["_study_slug"] = out["study_slug"].astype(str)
                base_rows = []
                for _, row in out.iterrows():
                    slug = safe_text(row.get("_study_slug"))
                    base_rows.append(enriched_by_slug.get(slug, row.drop(labels=["_study_slug"]).to_dict()))
                out = pd.DataFrame(base_rows, columns=columns)
        out = out.sort_values(["year", "study_slug"], ascending=[False, True])
    TESS_STUDY_INDEX.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(TESS_STUDY_INDEX, index=False)
    return out.reset_index(drop=True)


def build_political_science_rescue_worklist() -> pd.DataFrame:
    """Concrete political-science PAP/result rescue targets from the source memos."""
    rows = [
        {
            "row_id": "aea_registry_snapshot_intake",
            "source_family": "AEA RCT Registry",
            "paper_or_project": "AEA RCT Registry public Dataverse snapshot intake",
            "field": "economics and political science",
            "prereg_url": "https://www.socialscienceregistry.org/AEA_RCT_Registry_Data_Elements_Definitions.pdf",
            "result_url": "https://dataverse.harvard.edu/dataset.xhtml?persistentId=doi:10.7910/DVN/OHBI3I",
            "data_url": "https://dataverse.harvard.edu/api/datasets/:persistentId/?persistentId=doi:10.7910/DVN/OHBI3I",
            "candidate_status": "sidecar_registry_intake",
            "known_n_or_units": "Dataverse API verified 4 files: data dictionary, schema, trials.csv, trials.json; snapshot covers registrations through 2025-10-01.",
            "known_effect_summary": "No effect estimates in registry snapshot; this is the scalable PAP/paper/data/program-link intake layer.",
            "strict_blocker": "Registry metadata alone lacks final effect estimates and PAP-to-result extraction.",
            "next_action": "Download trials.csv, filter for PAP/analysis-plan plus paper/data/program URLs, then route each matched paper/package into row rescue.",
        },
        {
            "row_id": "tess_graham1155",
            "source_family": "TESS",
            "paper_or_project": "A Conditional Commitment? Partisan Identity and Support for Democracy in the United States",
            "field": "political science",
            "prereg_url": "https://osf.io/gw493/",
            "result_url": "https://tessexperiments.org/study/graham1155",
            "data_url": "https://osf.io/qzd3f/",
            "candidate_status": "native_metric_rescue_candidate",
            "known_n_or_units": "4027",
            "known_effect_summary": "TESS summary reports covariate-adjusted B=-0.007, SE=0.008 for support for undemocratic co-partisans; manipulation-check B=0.042, SE=0.027.",
            "strict_blocker": "No baseline probability, event counts, or outcome SD on the study page; stage native unless OSF data are parsed.",
            "next_action": "Download OSF data and compute the PAP outcome arm probabilities or standardized difference.",
        },
        {
            "row_id": "tess_johnson1389",
            "source_family": "TESS",
            "paper_or_project": "Optimizing Schools? Public Perceptions of Algorithmic versus Status Quo Prioritization in K-12 Schooling",
            "field": "political science",
            "prereg_url": "https://osf.io/vx7de/",
            "result_url": "https://tessexperiments.org/study/johnson1389",
            "data_url": "https://osf.io/v3bfk/",
            "candidate_status": "native_metric_rescue_candidate",
            "known_n_or_units": "5643 overall; 5606 in abstract; 4368 K-12 parent oversample",
            "known_effect_summary": "TESS summary reports H1 chi-square tests for algorithm fairness versus parent requests, simple rule, counselor discretion, and weighted lottery.",
            "strict_blocker": "Per-contrast denominators/event counts are not on the page; OSF data required for D conversion.",
            "next_action": "Download OSF data and reconstruct planned binary outcome contrasts from the PAP.",
        },
        {
            "row_id": "tess_jackson002",
            "source_family": "TESS",
            "paper_or_project": "An Experiment in the Measurement of Social and Economic Ideology",
            "field": "political science",
            "prereg_url": "TESS accepted proposal/study page; not full PAP-grade preregistration without additional verification",
            "result_url": "https://tessexperiments.org/study/jackson002",
            "data_url": "https://osf.io/z6gts/",
            "candidate_status": "sidecar_screen_candidate",
            "known_n_or_units": "1108; field period 5/2/2010-8/17/2010",
            "known_effect_summary": "TESS summary states about 30% provided different social/economic ideology placements and that multidimensional measures improved prediction for some respondents; no numeric effect on the page.",
            "strict_blocker": "TESS page has hypotheses/outcome and OSF materials but no numeric D/native estimate; TESS proposals are weaker than full PAPs unless a paper-specific preregistration is verified.",
            "next_action": "Download OSF/Roper data or linked paper and extract the planned contrast for separate social/economic ideology placements.",
        },
        {
            "row_id": "score_azevedo_jeps_replication",
            "source_family": "SCORE/JEPS",
            "paper_or_project": "Azevedo et al. JEPS SCORE preregistered replication of candidate-portrait effects",
            "field": "political science",
            "prereg_url": "https://osf.io/nxrg7/",
            "result_url": "https://www.cambridge.org/core/journals/journal-of-experimental-political-science/article/does-stereotype-threat-contribute-to-the-political-knowledge-gender-gap-a-preregistered-replication-study-of-ihme-and-tausendpfund-2018/1021AEEB971D486933CE265040CD0C95",
            "data_url": "https://doi.org/10.7910/DVN/ETUUOD",
            "candidate_status": "row_rescue_promising",
            "known_n_or_units": "N=671 and N=831 components; pooled N=1502 reported in memo",
            "known_effect_summary": "Reported F statistic / partial eta-squared style results.",
            "strict_blocker": "Need exact contrast, df, and eta-squared conversion check.",
            "next_action": "Download Dataverse package and article tables; convert eta-squared to r/d only for the preregistered simple contrast.",
        },
        {
            "row_id": "score_brodeur_zenodo_17792605",
            "source_family": "SCORE/Brodeur raw-code route",
            "paper_or_project": "Reproducibility and robustness of economics and political science research raw reproduction archive",
            "field": "economics and political science",
            "prereg_url": "https://osf.io/8wsqx/",
            "result_url": "https://www.cos.io/score",
            "data_url": "https://zenodo.org/records/17792605",
            "candidate_status": "sidecar_raw_code_route",
            "known_n_or_units": "110 reproduced economics/political-science articles reported by memo; local row count not verified.",
            "known_effect_summary": "Top-level SCORE/Brodeur summary metrics are not absolute D values; raw Stata/R reproduction scripts are the extraction target.",
            "strict_blocker": "Broad SCORE is claim/reproducibility-oriented, not a PAP-linked confirmatory-result corpus; only individual papers with independent PAP evidence can promote.",
            "next_action": "Use the archive only as a DOI/code locator, then extract paper-specific coefficient/SE/N rows after matching PAP/registry evidence.",
        },
        {
            "row_id": "dime_rio_safe_space",
            "source_family": "DIME",
            "paper_or_project": "Kondylis et al. demand for safe spaces in transport",
            "field": "public policy",
            "prereg_url": "RIDIE/AEA link to verify",
            "result_url": "https://github.com/worldbank/rio-safe-space",
            "data_url": "https://microdata.worldbank.org/index.php/catalog/3745",
            "candidate_status": "stage_native_metric",
            "known_n_or_units": "363 women and more than 22000 rides reported in memo",
            "known_effect_summary": "RCT ATE / percent-reduction style safety and travel outcomes.",
            "strict_blocker": "PAP link and D conversion inputs not yet verified.",
            "next_action": "Match RIDIE/AEA preregistration, then parse GitHub tables for ATE/SE/N and arm probabilities if available.",
        },
        {
            "row_id": "cps_golden_gulzar_sonnet_2025",
            "source_family": "CPS/Dataverse",
            "paper_or_project": "Golden, Gulzar & Sonnet political responsiveness and information provision",
            "field": "political science",
            "prereg_url": "https://egap.org/registration/2476 ; https://osf.io/vadwn",
            "result_url": "Comparative Political Studies article",
            "data_url": "https://dataverse.harvard.edu/dataset.xhtml?persistentid=doi:10.7910/DVN/9PWQZT",
            "candidate_status": "row_rescue_promising",
            "known_n_or_units": "paper/package required",
            "known_effect_summary": "Service-delivery / political responsiveness ATEs.",
            "strict_blocker": "Two PAPs and likely native ATE metrics; avoid pilot/scale-up double-counting.",
            "next_action": "Download Dataverse package, identify PAP primary outcomes, and stage ATE/SE/N.",
        },
        {
            "row_id": "apsr_campaign_experiments_archive",
            "source_family": "APSR/Dataverse",
            "paper_or_project": "How Experiments Help Campaigns Persuade Voters",
            "field": "political science",
            "prereg_url": "https://osf.io/q276a/ ; https://osf.io/5c9hx/",
            "result_url": "APSR article",
            "data_url": "https://doi.org/10.7910/DVN/LBPSSV",
            "candidate_status": "row_rescue_promising",
            "known_n_or_units": "paper/package required",
            "known_effect_summary": "Campaign persuasion/vote-choice estimates.",
            "strict_blocker": "Multiple campaigns/experiments; hierarchy must collapse to one paper dot or a component panel.",
            "next_action": "Download Dataverse package and reconstruct PAP primary vote-choice contrasts.",
        },
        {
            "row_id": "ajps_ghana_debates_ofosu_brierley_kramon",
            "source_family": "AJPS/Dataverse",
            "paper_or_project": "Ofosu, Brierley & Kramon candidate debates in Ghana",
            "field": "political science",
            "prereg_url": "https://osf.io/2qhg6/",
            "result_url": "AJPS article",
            "data_url": "https://doi.org/10.7910/DVN/OJA7YS",
            "candidate_status": "row_rescue_promising",
            "known_n_or_units": "paper/package required",
            "known_effect_summary": "Debate exposure, vote-choice, and accountability outcomes.",
            "strict_blocker": "Need PAP primary selector and arm/event-count or standardized-index inputs.",
            "next_action": "Download Dataverse package and extract PAP primary outcome estimate/N.",
        },
        {
            "row_id": "aea_good_politicians_trial_685",
            "source_family": "AEA/Zenodo",
            "paper_or_project": "Good Politicians: Experimental Evidence on Motivations for Political Candidacy and Government Performance",
            "field": "political science",
            "prereg_url": "https://www.socialscienceregistry.org/trials/685",
            "result_url": "https://academic.oup.com/restud/article/92/1/339/7627149",
            "data_url": "https://doi.org/10.5281/zenodo.10086096",
            "candidate_status": "native_metric_rescue_candidate",
            "known_n_or_units": "Article-level memo reports 9,310 citizens across 192 villages; registry final N fields must be parsed.",
            "known_effect_summary": "Primary political-entry outcomes are candidacy and election/winning office; likely binary ITT coefficients.",
            "strict_blocker": "D conversion requires arm event counts or log-OR inputs; clustered village design should enter native first.",
            "next_action": "Download Zenodo package and AEA trial page, then extract candidacy/election ITT coefficient, SE, respondent N, and cluster N.",
        },
        {
            "row_id": "metaketa_ii_tax_meta",
            "source_family": "EGAP Metaketa II",
            "paper_or_project": "Fiscal Contracts? A six-country randomized experiment on information, assistance, and tax compliance",
            "field": "economics and political science",
            "prereg_url": "Metaketa II amended meta-analysis PAP embedded in public PDF; verify final registry/PAP URL",
            "result_url": "https://egap.org/our-work/the-metaketa-initiative/roundtwo-taxation/",
            "data_url": "paper/package not yet verified",
            "candidate_status": "row_rescue_promising",
            "known_n_or_units": "six component projects; pooled final publication/package status not verified locally",
            "known_effect_summary": "Tax formalization/compliance pooled ATEs or coefficients.",
            "strict_blocker": "Pooled final paper/package status and exact primary selector are not verified to the same standard as Metaketa I/III/IV.",
            "next_action": "Locate final pooled paper and replication package, then stage pooled ATE/SE/N as native unless standardized outcomes are documented.",
        },
        {
            "row_id": "metaketa_ii_state_capacity_ceiling_3818",
            "source_family": "AEA/Metaketa II",
            "paper_or_project": "The State Capacity Ceiling on Tax Rates: Evidence from Randomized Tax Abatement in the D.R. Congo",
            "field": "development economics",
            "prereg_url": "https://www.socialscienceregistry.org/trials/3818",
            "result_url": "https://www.nber.org/system/files/working_papers/w31685/revisions/w31685.rev0.pdf",
            "data_url": "paper/package required",
            "candidate_status": "stage_native_metric",
            "known_n_or_units": "paper/package required",
            "known_effect_summary": "Tax-rate, compliance, and revenue coefficients from randomized tax abatement.",
            "strict_blocker": "Policy coefficients and clustered SEs are not D-convertible without outcome SDs, event counts, or baseline probabilities.",
            "next_action": "Parse AEA trial page and paper tables for preregistered primary tax outcome coefficient/SE/N.",
        },
        {
            "row_id": "metaketa_ii_local_elites_state_capacity",
            "source_family": "OpenICPSR/Metaketa II",
            "paper_or_project": "Local Elites as State Capacity: How City Chiefs Use Local Information to Increase Tax Compliance in the D.R. Congo",
            "field": "development economics",
            "prereg_url": "AEA/EGAP registration to verify from paper/package",
            "result_url": "paper/article required",
            "data_url": "https://www.openicpsr.org/openicpsr/project/147561/version/V1/view",
            "candidate_status": "row_rescue_promising",
            "known_n_or_units": "paper/package required",
            "known_effect_summary": "Tax-compliance / city-chief enforcement ATEs.",
            "strict_blocker": "PAP join and primary selector still need verification; likely native ATE metrics.",
            "next_action": "Download OpenICPSR package, identify the matched registry/PAP, and extract primary coefficient/SE/N.",
        },
    ]
    out = pd.DataFrame(rows)
    POLISCI_RESCUE_WORKLIST.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(POLISCI_RESCUE_WORKLIST, index=False)
    return out


def fmt_year(value: object) -> str:
    if pd.isna(value) or value == "":
        return ""
    return str(int(float(value)))


def numeric_series(series: pd.Series) -> pd.Series:
    cleaned = series.astype(str).str.replace(",", "", regex=False).str.strip()
    cleaned = cleaned.replace({"": pd.NA, "nan": pd.NA, "None": pd.NA})
    return pd.to_numeric(cleaned, errors="coerce")


def source_key_badge(label: object, machine_key: object, citation_key: object = "") -> str:
    label_text = safe_text(label)
    cite_text = safe_text(citation_key)
    if cite_text:
        return f"{label_text} [@{cite_text}]"
    return label_text


def doi_url(doi: object) -> str:
    doi_text = safe_text(doi)
    if not doi_text:
        return ""
    doi_text = re.sub(r"^https?://(?:dx\.)?doi\.org/", "", doi_text, flags=re.I).strip()
    return f"https://doi.org/{doi_text}" if doi_text else ""


def paper_ref(title: object, doi: object = "") -> str:
    title_text = safe_text(title) or safe_text(doi) or "untitled paper"
    url = doi_url(doi)
    if url:
        return f"[{title_text}]({url})"
    return title_text


def citation_key_from(mapping: dict[str, str], *labels: object) -> str:
    for label in labels:
        key = mapping.get(safe_text(label))
        if key:
            return key
    return ""


def plot1_citation_key(*labels: object) -> str:
    return citation_key_from(PLOT1_CITATION_KEYS, *labels)


def plot1_display_label_for_row(row: pd.Series, label_counts: pd.Series) -> str:
    canonical = safe_text(row.get("canonical_source_label"))
    project = safe_text(row.get("project"))
    project_display = project if project and project != "Multi-project" else ""
    if canonical == "FReD filtered pair table":
        return project_display or PLOT1_DISPLAY_LABELS[canonical]
    if canonical in PLOT1_DISPLAY_LABELS:
        return PLOT1_DISPLAY_LABELS[canonical]
    if label_counts.get(canonical, 0) > 1 and project_display:
        return f"{project_display} — {canonical}"
    return canonical or safe_text(row.get("canonical_source_id"))


def humanize_source_identifier(value: object) -> str:
    text = safe_text(value)
    if text.startswith("lead::"):
        text = text.split("lead::", 1)[1]
    text = re.sub(r"[_-]+", " ", text).strip()
    token_map = {
        "bri": "BRI",
        "core": "CORE",
        "eeg": "EEG",
        "eerp": "EERP",
        "eef": "EEF",
        "egap": "EGAP",
        "emdr": "EMDR",
        "eprp": "EPRP",
        "ern": "ERN",
        "fmri": "fMRI",
        "forrt": "FORRT",
        "fred": "FReD",
        "ibl": "IBL",
        "ies": "IES",
        "jtb": "JTB",
        "ml": "ML",
        "nvr": "NVR",
        "osf": "OSF",
        "pe": "Pe",
        "psa": "PSA",
        "rpcb": "RPCB",
        "rpp": "RPP",
        "rrr": "RRR",
        "sem": "SEM",
        "ses": "SES",
        "ssrp": "SSRP",
    }
    words = []
    for word in text.split():
        lowered = word.lower()
        words.append(token_map.get(lowered, word[:1].upper() + word[1:]))
    return " ".join(words)


def plot1_source_family_label_for_row(row: pd.Series) -> str:
    canonical = safe_text(row.get("canonical_source_label"))
    source_dataset = safe_text(row.get("source_dataset"))
    project = safe_text(row.get("project"))
    display_label = safe_text(row.get("display_label"))
    lead_id = safe_text(row.get("lead_id"))

    for label in [canonical, source_dataset, display_label, lead_id]:
        override = PLOT1_FAMILY_LABEL_OVERRIDES.get(label)
        if override:
            return override

    if canonical.startswith("lead::"):
        if project and project != "Multi-project":
            return project
        return PLOT1_LEAD_DISPLAY_LABELS.get(canonical, humanize_source_identifier(canonical))

    if project.startswith("FReD"):
        return "FReD"
    if project and project not in {"Multi-project", "Other direct replications", "Registered Replication Reports"}:
        return PLOT1_DISPLAY_LABELS.get(canonical, project)
    if canonical in PLOT1_DISPLAY_LABELS:
        return PLOT1_DISPLAY_LABELS[canonical]
    return display_label or humanize_source_identifier(canonical or source_dataset or lead_id)


def plot1_family_key(label: object, citation_key: object) -> str:
    label_text = safe_text(label)
    cite_text = safe_text(citation_key)
    return f"{slugify(label_text, 'source')}::{cite_text or 'uncited'}"


def plot1_source_family_description(row: pd.Series) -> str:
    family_label = safe_text(row.get("display_family_label"))
    if family_label in PLOT1_SOURCE_FAMILY_DESCRIPTIONS:
        return PLOT1_SOURCE_FAMILY_DESCRIPTIONS[family_label]

    lower = family_label.lower()
    audit_status = safe_text(row.get("audit_status"))
    classification = safe_text(row.get("classification"))
    if classification:
        classification_text = classification.replace("harvest-promoted", "harvest-promoted").strip()
    else:
        classification_text = ""

    if family_label.startswith("RRR ") or "registered replication" in lower:
        return f"{family_label} is a registered-replication source in psychology, normally a multi-lab direct replication of one target effect; local rows use public site, aggregate, or manual source files where D/N is recoverable."
    if family_label.startswith("PSA "):
        return f"{family_label} is a Psychological Science Accelerator replication source: a multi-site psychology project with country/lab-level replication data for a named target effect."
    if "awesome" in lower or safe_text(row.get("canonical_source_label")).startswith("lead::awesome"):
        return f"{family_label} is a direct-replication source from the awesome-replicability-data collection; local evidence is unit-level or project-level raw data awaiting or using source-specific promotion."
    if "metaketa" in lower:
        return f"{family_label} is an EGAP Metaketa political-science field-experiment source; it is cataloged for replication/generalizability evidence but is not currently on the shared D/N pair axis."
    if "manybabies" in lower:
        return f"{family_label} is a multi-lab developmental-psychology replication source, cataloged as a candidate direct-replication family."
    if "manyclasses" in lower:
        return f"{family_label} is a multi-classroom education/generalizability source, cataloged as a candidate replication family."
    if "candidate-gene" in lower or "border" in lower:
        return f"{family_label} is a genetics replication source, focused on candidate-gene claims rather than a broad journal-result sample."
    if "eqipd" in lower:
        return PLOT1_SOURCE_FAMILY_DESCRIPTIONS["EQIPD stagewise open-field lab contrasts"]
    if "neuro" in lower or "eeg" in lower or "fmri" in lower or "electrophysiology" in lower:
        return f"{family_label} is a neuroscience replication/generalizability source, cataloged for potential pair construction where a common effect-size and N policy is available."
    if "learning" in lower or "education" in lower or re.search(r"\b(eef|ies)\b", lower):
        return f"{family_label} is an education or learning-intervention replication source, cataloged as a potential pair family rather than a broad paper sample."
    if "public administration" in lower or "coppock" in lower or "mullinix" in lower:
        return f"{family_label} is a political-science/public-administration replication or generalizability source, cataloged for possible direct-replication pair extraction."

    artifact_text = {
        "raw_artifact_only": "The local evidence is currently raw source material, not a structured D/N pair table.",
        "staged_only": "The local evidence has been staged but still needs parser, metric, or conversion work before promotion.",
        "catalog_not_integrated": "The source is cataloged as real source material but is retained as a cross-check or sidecar.",
        "integrated_live": "The source contributes structured original-versus-replication D/N rows.",
        "catalog_integrated": "The source is retained as support or fallback material for integrated rows.",
    }.get(audit_status, "The source is cataloged in the replication-pair audit.")
    if classification_text:
        return f"{family_label} is a {classification_text} source. {artifact_text}"
    return f"{family_label} is a cataloged replication or generalizability source. {artifact_text}"


def plot2_display_label(label: object) -> str:
    label_text = safe_text(label)
    return PLOT2_DISPLAY_LABELS.get(label_text, label_text)


def plot3_display_label(label: object) -> str:
    label_text = safe_text(label)
    return PLOT3_DISPLAY_LABELS.get(label_text, label_text)


def score_prereg_indicated_paper_rows(published: pd.DataFrame | None = None) -> tuple[pd.DataFrame, int, int]:
    """Return SCORE paper-level D/N rows whose original papers indicate preregistration."""
    if published is None:
        published = pd.read_csv(PUBLISHED_PAPERS) if PUBLISHED_PAPERS.exists() else pd.DataFrame()
    if published.empty or not SCORE_ORIG_PREREG.exists() or not SCORE_PAPER_METADATA.exists():
        return pd.DataFrame(), 0, 0

    prereg = pd.read_csv(SCORE_ORIG_PREREG)
    if "prereg" not in prereg.columns or "paper_id" not in prereg.columns:
        return pd.DataFrame(), 0, 0
    prereg_true = prereg.loc[prereg["prereg"].astype(str).str.lower().eq("true")].copy()
    prereg_true = prereg_true.drop_duplicates("paper_id")
    prereg_count = int(len(prereg_true))

    metadata = pd.read_csv(SCORE_PAPER_METADATA)
    if "DOI" not in metadata.columns or "paper_id" not in metadata.columns:
        return pd.DataFrame(), prereg_count, 0
    metadata = metadata.copy()
    metadata["doi_norm"] = metadata["DOI"].astype(str).str.lower().str.strip()

    score = published.loc[published["source_corpus"].eq("score_cos_claims")].copy()
    if score.empty:
        return pd.DataFrame(), prereg_count, 0
    score = score[
        (numeric_series(score.get("D_median", pd.Series(dtype=float))) > 0)
        & (numeric_series(score.get("N_median", pd.Series(dtype=float))) > 0)
    ].copy()
    score["doi_norm"] = score["unit_id"].astype(str).str.replace(r"^DOI:", "", regex=True).str.lower().str.strip()
    score = score.merge(
        metadata[["paper_id", "doi_norm", "DOI", "publication_standard", "pub_year"]],
        on="doi_norm",
        how="left",
    )
    score = score.merge(prereg_true[["paper_id", "prereg"]], on="paper_id", how="inner")
    if score.empty:
        return pd.DataFrame(), prereg_count, 0

    source_kind = score.get("source_kind", pd.Series("", index=score.index)).astype(str)
    score["_source_priority"] = np.where(source_kind.eq("score_structured_orig_outcomes"), 0, 1)
    score["_n_rows_numeric"] = numeric_series(score.get("n_rows", pd.Series(0, index=score.index))).fillna(0)
    score = score.sort_values(["unit_id", "_source_priority", "_n_rows_numeric"], ascending=[True, True, False])
    score = score.drop_duplicates("unit_id", keep="first").drop(columns=["_source_priority", "_n_rows_numeric"])
    return score.reset_index(drop=True), prereg_count, prereg_count - int(len(score))


def score_text_claim_rescue_rows() -> pd.DataFrame:
    """Return extra SCORE preregistration-indicated rows parsed from extracted claim text."""
    if not SCORE_TEXT_CLAIM_CANDIDATES.exists():
        return pd.DataFrame()
    rows = pd.read_csv(SCORE_TEXT_CLAIM_CANDIDATES)
    if rows.empty or "strict_append_ready" not in rows.columns:
        return pd.DataFrame()
    ready = rows.loc[rows["strict_append_ready"].astype(str).str.lower().eq("true")].copy()
    ready = ready[
        (numeric_series(ready.get("D_candidate", pd.Series(dtype=float))) > 0)
        & (numeric_series(ready.get("N_candidate", pd.Series(dtype=float))) > 0)
    ].copy()
    if ready.empty:
        return ready
    ready["_paper_id"] = ready.get("paper_id", pd.Series("", index=ready.index)).astype(str)
    ready = ready.sort_values(["_paper_id", "candidate_id"]).drop_duplicates("_paper_id", keep="first")
    if SCORE_PAPER_METADATA.exists() and "paper_id" in ready.columns:
        metadata = pd.read_csv(SCORE_PAPER_METADATA, usecols=["paper_id", "COS_pub_category"])
        ready = ready.merge(metadata, on="paper_id", how="left")
    return ready.drop(columns=["_paper_id"]).reset_index(drop=True)


def vandenakker_matched_median_rows() -> pd.DataFrame:
    """Return paper-level median rows from matched preregistered-result statistics."""
    if not VANDENAKKER_MEDIAN_CANDIDATES.exists():
        return pd.DataFrame()
    rows = pd.read_csv(VANDENAKKER_MEDIAN_CANDIDATES)
    if rows.empty or "strict_append_ready" not in rows.columns:
        return pd.DataFrame()
    ready = rows.loc[rows["strict_append_ready"].astype(str).str.lower().eq("true")].copy()
    ready = ready[
        (numeric_series(ready.get("D_candidate", pd.Series(dtype=float))) > 0)
        & (numeric_series(ready.get("N_candidate", pd.Series(dtype=float))) > 0)
    ].copy()
    if ready.empty:
        return ready
    ready["_psp"] = numeric_series(ready.get("PSP", pd.Series(dtype=float)))
    ready = ready.sort_values(["_psp", "candidate_id"]).drop_duplicates("_psp", keep="first")
    return ready.drop(columns=["_psp"]).reset_index(drop=True)


def rpcb_registered_report_median_rows() -> pd.DataFrame:
    """Return preclinical Registered Report paper medians from RPCB."""
    if not RPCB_PRECLINICAL_CANDIDATES.exists():
        return pd.DataFrame()
    rows = pd.read_csv(RPCB_PRECLINICAL_CANDIDATES)
    if rows.empty or "strict_append_ready" not in rows.columns:
        return pd.DataFrame()
    ready = rows.loc[rows["strict_append_ready"].astype(str).str.lower().eq("true")].copy()
    ready = ready[
        (numeric_series(ready.get("D_candidate", pd.Series(dtype=float))) > 0)
        & (numeric_series(ready.get("N_candidate", pd.Series(dtype=float))) > 0)
    ].copy()
    if ready.empty:
        return ready
    ready["_paper_number"] = numeric_series(ready.get("paper_number", pd.Series(dtype=float)))
    ready = ready.sort_values(["_paper_number", "candidate_id"]).drop_duplicates("_paper_number", keep="first")
    return ready.drop(columns=["_paper_number"]).reset_index(drop=True)


def plot3_paper_group_key(row: pd.Series) -> str:
    """Stable paper/project key for Plot 3's one-dot-per-paper rule."""
    source_family = safe_text(row.get("source_family")).lower()
    field = safe_text(row.get("field")).lower()
    point_id = safe_text(row.get("point_id"))
    if "psa-cr001" in source_family:
        return "psa-cr001:dorison2022"
    if "psa-cr002" in source_family:
        return "psa-cr002:wang2021"
    if "scheel et al. 2021" in source_family:
        paper_stub = re.split(r"\s+[—-]\s+", safe_text(row.get("row_label")), maxsplit=1)[0]
        return f"scheel2021:{paper_stub.lower() or point_id}"
    if field == "political science" or plot3_default_field(source_family) == "political science":
        if source_family.startswith("brodeur et al. 2024"):
            return point_id or f"brodeur:{row.name}"
        if source_family.startswith("score/cos"):
            return point_id or f"score:{row.name}"
        return f"political-science:{source_family}"
    return point_id or f"row:{row.name}"


def plot3_paper_project_type(row: pd.Series) -> str:
    source_family = safe_text(row.get("source_family")).lower()
    if source_family.startswith("brodeur et al. 2024"):
        return "brodeur_extracted_paper"
    if source_family.startswith("score/cos"):
        return "score_original_paper"
    if source_family.startswith("egap metaketa"):
        return "pooled_metaketa_round_paper"
    if "hewitt et al." in source_family or "kalla broockman" in source_family:
        return "single_paper_campaign_archive"
    return "single_paper_or_project"


def write_political_science_paper_project_medians(precollapse: pd.DataFrame, collapsed: pd.DataFrame) -> None:
    """Audit table for the political-science median-per-paper/project layer."""
    if precollapse.empty:
        pd.DataFrame().to_csv(POLISCI_PAPER_PROJECT_MEDIANS, index=False)
        return
    work = precollapse.copy()
    if "field" not in work.columns:
        work["field"] = ""
    field_text = work["field"].fillna("").astype(str).str.strip()
    inferred_field = work["source_family"].map(plot3_default_field)
    work["_field_for_group"] = field_text.where(field_text.ne(""), inferred_field)
    work = work.loc[work["_field_for_group"].eq("political science")].copy()
    if work.empty:
        pd.DataFrame().to_csv(POLISCI_PAPER_PROJECT_MEDIANS, index=False)
        return
    work["paper_project_key"] = work.apply(plot3_paper_group_key, axis=1)
    rows: list[dict[str, object]] = []
    for key, group in work.groupby("paper_project_key", sort=False):
        first = group.iloc[0]
        d_values = numeric_series(group["D"])
        n_values = numeric_series(group["N"])
        rows.append(
            {
                "paper_project_key": key,
                "source_family": first.get("source_family"),
                "source_label": first.get("source_label"),
                "paper_project_label": first.get("row_label")
                if key.startswith(("brodeur", "score"))
                else first.get("source_label"),
                "citation_key": first.get("citation_key"),
                "paper_project_unit_type": plot3_paper_project_type(first),
                "rows_collapsed": int(len(group)),
                "median_D": float(d_values.median()),
                "median_N": float(n_values.median()),
                "min_N": float(n_values.min()),
                "max_N": float(n_values.max()),
                "row_units_collapsed": " | ".join(sorted(group["row_unit"].dropna().astype(str).unique())),
                "example_result_labels": " || ".join(group["row_label"].dropna().astype(str).head(8).tolist()),
                "source_files_collapsed": " || ".join(group["source_file"].dropna().astype(str).drop_duplicates().head(5).tolist()),
            }
        )
    out = pd.DataFrame(rows).sort_values(
        ["rows_collapsed", "source_family", "paper_project_label"],
        ascending=[False, True, True],
        kind="stable",
    )
    out.to_csv(POLISCI_PAPER_PROJECT_MEDIANS, index=False)


def collapse_plot3_to_one_dot_per_paper(df: pd.DataFrame) -> pd.DataFrame:
    """Collapse explicit multi-result paper/project clusters to median D/N rows."""
    if df.empty:
        return df
    work = df.copy()
    work["_paper_group_key"] = work.apply(plot3_paper_group_key, axis=1)
    collapsed_rows: list[pd.Series] = []
    for _, group in work.groupby("_paper_group_key", sort=False):
        group = group.copy()
        first = group.iloc[0].copy()
        field = safe_text(first.get("field")).lower()
        source_family = safe_text(first.get("source_family")).lower()
        is_political_science = (
            field == "political science"
            or plot3_default_field(source_family) == "political science"
        )
        if len(group) == 1:
            row_unit = safe_text(first.get("row_unit")).lower()
            if is_political_science and ("component" in row_unit or "contrast" in row_unit):
                first["row_unit"] = "paper_median_of_preregistered_results"
                first["row_label"] = (
                    f"{safe_text(first.get('source_label'))} - "
                    "single preregistered paper/project result"
                )
                first["source_file"] = (
                    f"{safe_text(first.get('source_file'))}; single-row "
                    "paper/project collapse from political-science component audit"
                )
            collapsed_rows.append(first)
            continue
        source_slug = slugify(safe_text(first.get("source_label")), "plot3_paper")
        first["point_id"] = f"{source_slug}_paper_median_{len(collapsed_rows) + 1:03d}"
        first["row_unit"] = "paper_median_of_preregistered_results"
        first["row_label"] = (
            f"{safe_text(first.get('source_label'))} - paper median of "
            f"{len(group)} preregistered result rows"
        )
        first["D"] = float(pd.to_numeric(group["D"], errors="coerce").median())
        first["N"] = float(pd.to_numeric(group["N"], errors="coerce").median())
        support_values = sorted(set(group["supported"].fillna("").astype(str).str.strip().str.lower()) - {""})
        first["supported"] = support_values[0] if len(support_values) == 1 else "mixed"
        row_numbers = ";".join(group["source_row_number"].astype(str).tolist())
        first["source_row_number"] = row_numbers
        first["source_file"] = (
            f"{safe_text(first.get('source_file'))}; median collapse of "
            f"{len(group)} preregistered result rows"
        )
        collapsed_rows.append(first)
    out = pd.DataFrame(collapsed_rows).drop(columns=["_paper_group_key"], errors="ignore")
    return out.reset_index(drop=True)


def write_qmd_with_table(path: Path, lines: list[str]) -> None:
    path.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")


def extract_tables(soup: BeautifulSoup) -> dict[str, str]:
    """Extract all HTML tables to CSV and generated Markdown fragments."""
    table_tokens: dict[str, str] = {}
    manifest_rows: list[dict[str, str | int]] = []
    tables = soup.find_all("table")

    for idx, table in enumerate(tables, start=1):
        previous_heading = table.find_previous(["h2", "h3", "h4", "h5"])
        heading = text_of(previous_heading) if previous_heading else f"Table {idx}"
        table_id = f"table_{idx:02d}_{slugify(heading, f'table_{idx:02d}')[:64]}"
        csv_path = TABLE_DIR / f"{table_id}.csv"
        fragment_path = TABLE_FRAGMENT_DIR / f"{table_id}.qmd"

        rows: list[list[str]] = []
        for tr in table.find_all("tr"):
            cells = tr.find_all(["th", "td"])
            if cells:
                rows.append([text_of(cell) for cell in cells])
        if not rows:
            rows = [[heading]]

        with csv_path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerows(rows)

        title = f"Table {idx}. {heading}"
        fragment = "\n".join(
            [
                "",
                '::: {.paper-table}',
                f"**{title}**",
                "",
                markdown_table(rows),
                ":::",
                "",
            ]
        )
        fragment_path.write_text(fragment, encoding="utf-8")

        token = f"TABLE_TOKEN_{idx:02d}"
        table_tokens[token] = fragment
        manifest_rows.append(
            {
                "table_index": idx,
                "table_id": table_id,
                "heading": heading,
                "source_class": "html_extract",
                "csv_path": str(csv_path.relative_to(ROOT)),
                "fragment_path": str(fragment_path.relative_to(ROOT)),
                "n_rows_including_header": len(rows),
                "n_columns_max": max(len(row) for row in rows),
            }
        )
        table.replace_with(NavigableString(f"\n\n{token}\n\n"))

    pd.DataFrame(manifest_rows).to_csv(TABLE_MANIFEST, index=False)
    return table_tokens


def parse_author_literals(author_text: str) -> list[dict[str, str]]:
    author_text = re.sub(r"\bet al\.?$", "", author_text.strip(), flags=re.I).strip()
    author_text = author_text.replace(" & ", ", ").replace(" and ", ", ")
    parts = [part.strip(" .") for part in author_text.split(",") if part.strip(" .")]
    return [{"literal": part} for part in parts[:12]] or [{"literal": author_text or "Unknown"}]


def parse_csl_entry(entry) -> dict[str, object]:
    citekey = entry.get("id", "").replace("ref-", "", 1)
    clone = BeautifulSoup(str(entry), "html.parser")
    for backlink in clone.select(".backlink"):
        backlink.decompose()
    right = clone.select_one(".csl-right-inline") or clone
    full = text_of(right)
    full = re.sub(r"\s*↩\s*$", "", full).strip()
    year_match = re.search(r"\((\d{4}[a-z]?)\)", full)
    year = int(year_match.group(1)[:4]) if year_match else None
    before_year = full[: year_match.start()].strip(" .") if year_match else ""
    after_year = full[year_match.end() :].strip(" .") if year_match else full
    container = text_of(right.find("em")) if right.find("em") else ""
    doi_link = ""
    url = ""
    for link in right.find_all("a", href=True):
        href = link["href"]
        if "doi.org/" in href and not doi_link:
            doi_link = href
        elif href.startswith("http") and not url:
            url = href

    title = after_year
    if container and container in title:
        title = title.split(container, 1)[0].strip(" .")
    title = title or full or citekey

    item: dict[str, object] = {
        "id": citekey,
        "type": "article-journal" if container else "webpage",
        "title": title,
    }
    if before_year:
        item["author"] = parse_author_literals(before_year)
    if year:
        item["issued"] = {"date-parts": [[year]]}
    if container:
        item["container-title"] = container
    if doi_link:
        item["DOI"] = doi_link.rsplit("/", 1)[-1]
        item["URL"] = doi_link
    elif url:
        item["URL"] = url
    if full:
        item["note"] = full
    return item


def extract_bibliography(soup: BeautifulSoup) -> set[str]:
    """Return draft bibliography keys for citation auditing.

    Bibliography files are built by scripts/build_bibliography.py. This paper
    asset step should not overwrite the enriched BibTeX/CSL outputs.
    """
    entries = soup.select("div.csl-entry")
    items = [parse_csl_entry(entry) for entry in entries]
    seen: set[str] = set()
    for item in items:
        citekey = str(item["id"])
        if citekey not in seen:
            seen.add(citekey)
    return seen


def citation_markdown(cites_raw: str) -> str:
    citekeys = [cite.strip() for cite in cites_raw.split() if cite.strip()]
    if not citekeys:
        return ""
    return " [" + "; ".join(f"@{cite}" for cite in citekeys) + "]"


def replace_citation_spans(soup: BeautifulSoup) -> set[str]:
    in_text: set[str] = set()
    for span in soup.select("span.citation"):
        cites = span.get("data-cites") or span.get("cites") or ""
        for cite in cites.split():
            if cite.strip():
                in_text.add(cite.strip())
        span.replace_with(NavigableString(citation_markdown(cites)))
    return in_text


def fit_loglog(df: pd.DataFrame, d_col: str, n_col: str) -> tuple[float, float]:
    values = df[[d_col, n_col]].copy()
    values[d_col] = pd.to_numeric(values[d_col], errors="coerce")
    values[n_col] = pd.to_numeric(values[n_col], errors="coerce")
    values = values[(values[d_col] > 0) & (values[n_col] > 0)].dropna()
    x = np.log10(values[n_col].to_numpy(dtype=float))
    y = np.log10(values[d_col].to_numpy(dtype=float))
    if len(values) < 3:
        return math.nan, math.nan
    slope, intercept = np.polyfit(x, y, 1)
    return float(slope), float(intercept)


def load_replication_stats_table() -> pd.DataFrame:
    if FIGURE1_ROOT_TABLE.exists():
        df = pd.read_csv(FIGURE1_ROOT_TABLE, sep="\t")
        df = df.loc[df["current_plot_rule_status"].eq("included_by_current_figure1_dn_rule")].copy()
        return df
    return pd.read_csv(REPLICATION_CSV)


def replication_stats() -> dict[str, float | int]:
    df = load_replication_stats_table()
    counts = df["category"].value_counts()
    all_n = np.concatenate([df["N_original"].to_numpy(dtype=float), df["N_replication"].to_numpy(dtype=float)])
    all_d = np.concatenate([df["D_original"].to_numpy(dtype=float), df["D_replication"].to_numpy(dtype=float)])
    mask = np.isfinite(all_n) & np.isfinite(all_d) & (all_n > 0) & (all_d > 0)
    slope, _ = np.polyfit(np.log10(all_n[mask]), np.log10(all_d[mask]), 1)
    orig_key = df["original_doi"].fillna("").astype(str).str.strip()
    orig_key = orig_key.where(orig_key.ne(""), df["original_title"].fillna("").astype(str).str.strip())
    rep_key = df["replication_doi"].fillna("").astype(str).str.strip()
    rep_key = rep_key.where(rep_key.ne(""), df["replication_title"].fillna("").astype(str).str.strip())
    orig_counts = orig_key.value_counts()
    rep_counts = rep_key.value_counts()
    return {
        "n_pairs": len(df),
        "n_shrunk_below": int(counts.get("shrunk_below_sig", 0)),
        "n_shrunk_still": int(counts.get("shrunk_still_sig", 0)),
        "n_grew": int(counts.get("grew", 0)),
        "pct_shrunk_below": 100 * counts.get("shrunk_below_sig", 0) / len(df),
        "pct_shrunk_any": 100 * (counts.get("shrunk_below_sig", 0) + counts.get("shrunk_still_sig", 0)) / len(df),
        "tenfold_reduction_pct": 100 * (1 - 10**slope),
        "median_d_original": float(df["D_original"].median()),
        "median_d_replication": float(df["D_replication"].median()),
        "median_n_original": float(df["N_original"].median()),
        "median_n_replication": float(df["N_replication"].median()),
        "n_unique_original_papers": int(orig_key.nunique()),
        "n_unique_replication_papers": int(rep_key.nunique()),
        "n_original_papers_multirow": int((orig_counts > 1).sum()),
        "n_replication_papers_multirow": int((rep_counts > 1).sum()),
    }


def published_stats() -> dict[str, float | int]:
    papers = pd.read_csv(PUBLISHED_PAPERS)
    main = papers[papers["published_original_candidate"].astype(bool) & ~papers["comparator_only"].astype(bool)].copy()
    main = main[(main["D_median"] > 0) & (main["N_median"] > 0)].copy()
    z10 = 1.6448536269514722
    above_p10 = main["D_median"] >= (2 * z10 / np.sqrt(main["N_median"]))
    n_d_ge_02 = int((main["D_median"] >= 0.2).sum())
    n_d_ge_05 = int((main["D_median"] >= 0.5).sum())
    n_d_ge_08 = int((main["D_median"] >= 0.8).sum())
    field_count = int(main["field"].nunique())
    source_count = int(main["source_corpus"].nunique())
    return {
        "n_papers": len(main),
        "field_count": field_count,
        "source_count": source_count,
        "median_d": float(main["D_median"].median()),
        "median_n": float(main["N_median"].median()),
        "pct_above_p10": 100 * float(above_p10.mean()),
        "pct_d_ge_02": 100 * n_d_ge_02 / len(main),
        "pct_d_ge_05": 100 * n_d_ge_05 / len(main),
        "pct_d_ge_08": 100 * n_d_ge_08 / len(main),
        "n_d_ge_02": n_d_ge_02,
        "n_d_ge_05": n_d_ge_05,
        "n_d_ge_08": n_d_ge_08,
    }


MANUAL_PREREGISTERED_ADDITIONS: list[dict[str, object]] = [
    {
        "point_id": "psacr002_h1a_negative_photo",
        "source_family": "PSA-CR002 cognitive reappraisal preregistered hypotheses",
        "source_label": "PSA-CR002 cognitive reappraisal hypotheses",
        "citation_key": "wang2021psacr002",
        "row_unit": "preregistered_hypothesis_table_row",
        "row_label": "H1a: reappraisal versus control reduces negative emotions in response to photos",
        "D": 0.392,
        "N": 21644,
        "supported": "yes",
        "journal": "Nature Human Behaviour",
        "source_file": "Table 2/3 in Wang et al. 2021; DOI 10.1038/s41562-021-01173-x",
        "source_row_number": 2,
    },
    {
        "point_id": "psacr002_h1b_negative_state",
        "source_family": "PSA-CR002 cognitive reappraisal preregistered hypotheses",
        "source_label": "PSA-CR002 cognitive reappraisal hypotheses",
        "citation_key": "wang2021psacr002",
        "row_unit": "preregistered_hypothesis_table_row",
        "row_label": "H1b: reappraisal versus control reduces negative state emotions",
        "D": 0.313,
        "N": 21644,
        "supported": "yes",
        "journal": "Nature Human Behaviour",
        "source_file": "Table 2/3 in Wang et al. 2021; DOI 10.1038/s41562-021-01173-x",
        "source_row_number": 3,
    },
    {
        "point_id": "psacr002_h1c_negative_covid",
        "source_family": "PSA-CR002 cognitive reappraisal preregistered hypotheses",
        "source_label": "PSA-CR002 cognitive reappraisal hypotheses",
        "citation_key": "wang2021psacr002",
        "row_unit": "preregistered_hypothesis_table_row",
        "row_label": "H1c: reappraisal versus control reduces negative emotions about COVID-19",
        "D": 0.239,
        "N": 21644,
        "supported": "yes",
        "journal": "Nature Human Behaviour",
        "source_file": "Table 2/3 in Wang et al. 2021; DOI 10.1038/s41562-021-01173-x",
        "source_row_number": 4,
    },
    {
        "point_id": "psacr002_h2a_positive_photo",
        "source_family": "PSA-CR002 cognitive reappraisal preregistered hypotheses",
        "source_label": "PSA-CR002 cognitive reappraisal hypotheses",
        "citation_key": "wang2021psacr002",
        "row_unit": "preregistered_hypothesis_table_row",
        "row_label": "H2a: reappraisal versus control increases positive emotions in response to photos",
        "D": 0.590,
        "N": 21644,
        "supported": "yes",
        "journal": "Nature Human Behaviour",
        "source_file": "Table 2/3 in Wang et al. 2021; DOI 10.1038/s41562-021-01173-x",
        "source_row_number": 5,
    },
    {
        "point_id": "psacr002_h2b_positive_state",
        "source_family": "PSA-CR002 cognitive reappraisal preregistered hypotheses",
        "source_label": "PSA-CR002 cognitive reappraisal hypotheses",
        "citation_key": "wang2021psacr002",
        "row_unit": "preregistered_hypothesis_table_row",
        "row_label": "H2b: reappraisal versus control increases positive state emotions",
        "D": 0.326,
        "N": 21644,
        "supported": "yes",
        "journal": "Nature Human Behaviour",
        "source_file": "Table 2/3 in Wang et al. 2021; DOI 10.1038/s41562-021-01173-x",
        "source_row_number": 6,
    },
    {
        "point_id": "psacr002_h2c_positive_covid",
        "source_family": "PSA-CR002 cognitive reappraisal preregistered hypotheses",
        "source_label": "PSA-CR002 cognitive reappraisal hypotheses",
        "citation_key": "wang2021psacr002",
        "row_unit": "preregistered_hypothesis_table_row",
        "row_label": "H2c: reappraisal versus control increases positive emotions about COVID-19",
        "D": 0.266,
        "N": 21644,
        "supported": "yes",
        "journal": "Nature Human Behaviour",
        "source_file": "Table 2/3 in Wang et al. 2021; DOI 10.1038/s41562-021-01173-x",
        "source_row_number": 7,
    },
    {
        "point_id": "psacr002_h3a_reconstrual_photo_negative",
        "source_family": "PSA-CR002 cognitive reappraisal preregistered hypotheses",
        "source_label": "PSA-CR002 cognitive reappraisal hypotheses",
        "citation_key": "wang2021psacr002",
        "row_unit": "preregistered_hypothesis_table_row",
        "row_label": "H3a: reconstrual versus repurposing, negative photo emotions",
        "D": -0.043,
        "N": 10499,
        "supported": "no",
        "journal": "Nature Human Behaviour",
        "source_file": "Table 2/3 in Wang et al. 2021; DOI 10.1038/s41562-021-01173-x",
        "source_row_number": 8,
    },
    {
        "point_id": "psacr002_h3b_reconstrual_state_negative",
        "source_family": "PSA-CR002 cognitive reappraisal preregistered hypotheses",
        "source_label": "PSA-CR002 cognitive reappraisal hypotheses",
        "citation_key": "wang2021psacr002",
        "row_unit": "preregistered_hypothesis_table_row",
        "row_label": "H3b: reconstrual versus repurposing, negative state emotions",
        "D": -0.008,
        "N": 10499,
        "supported": "no",
        "journal": "Nature Human Behaviour",
        "source_file": "Table 2/3 in Wang et al. 2021; DOI 10.1038/s41562-021-01173-x",
        "source_row_number": 9,
    },
    {
        "point_id": "psacr002_h3c_reconstrual_covid_negative",
        "source_family": "PSA-CR002 cognitive reappraisal preregistered hypotheses",
        "source_label": "PSA-CR002 cognitive reappraisal hypotheses",
        "citation_key": "wang2021psacr002",
        "row_unit": "preregistered_hypothesis_table_row",
        "row_label": "H3c: reconstrual versus repurposing, negative COVID-19 emotions",
        "D": 0.067,
        "N": 10499,
        "supported": "yes",
        "journal": "Nature Human Behaviour",
        "source_file": "Table 2/3 in Wang et al. 2021; DOI 10.1038/s41562-021-01173-x",
        "source_row_number": 10,
    },
    {
        "point_id": "psacr002_h4a_repurposing_photo_positive",
        "source_family": "PSA-CR002 cognitive reappraisal preregistered hypotheses",
        "source_label": "PSA-CR002 cognitive reappraisal hypotheses",
        "citation_key": "wang2021psacr002",
        "row_unit": "preregistered_hypothesis_table_row",
        "row_label": "H4a: repurposing versus reconstrual, positive photo emotions",
        "D": 0.114,
        "N": 10499,
        "supported": "yes",
        "journal": "Nature Human Behaviour",
        "source_file": "Table 2/3 in Wang et al. 2021; DOI 10.1038/s41562-021-01173-x",
        "source_row_number": 11,
    },
    {
        "point_id": "psacr002_h4b_repurposing_state_positive",
        "source_family": "PSA-CR002 cognitive reappraisal preregistered hypotheses",
        "source_label": "PSA-CR002 cognitive reappraisal hypotheses",
        "citation_key": "wang2021psacr002",
        "row_unit": "preregistered_hypothesis_table_row",
        "row_label": "H4b: repurposing versus reconstrual, positive state emotions",
        "D": -0.011,
        "N": 10499,
        "supported": "no",
        "journal": "Nature Human Behaviour",
        "source_file": "Table 2/3 in Wang et al. 2021; DOI 10.1038/s41562-021-01173-x",
        "source_row_number": 12,
    },
    {
        "point_id": "psacr002_h4c_repurposing_covid_positive",
        "source_family": "PSA-CR002 cognitive reappraisal preregistered hypotheses",
        "source_label": "PSA-CR002 cognitive reappraisal hypotheses",
        "citation_key": "wang2021psacr002",
        "row_unit": "preregistered_hypothesis_table_row",
        "row_label": "H4c: repurposing versus reconstrual, positive COVID-19 emotions",
        "D": -0.047,
        "N": 10499,
        "supported": "no",
        "journal": "Nature Human Behaviour",
        "source_file": "Table 2/3 in Wang et al. 2021; DOI 10.1038/s41562-021-01173-x",
        "source_row_number": 13,
    },
    {
        "point_id": "psa004_jtb_gettier_pooled",
        "source_family": "PSA004 true-belief/Gettier pooled preregistered row",
        "source_label": "PSA004 true-belief/Gettier pooled row",
        "citation_key": "hall2024psa004Turri",
        "row_unit": "pooled_preregistered_project_effect",
        "row_label": "Pooled standard justified-true-belief versus Gettier knowledge attribution",
        "D": math.log(1.86) * math.sqrt(3) / math.pi,
        "N": 4724,
        "supported": "yes",
        "journal": "Advances in Methods and Practices in Psychological Science",
        "source_file": "PSA004 project page and Hall et al. 2024; OR=1.86 converted with Chinn log-OR-to-d",
        "source_row_number": 1,
    },
    {
        "point_id": "manybabies1_ids_preference_pooled",
        "source_family": "ManyBabies 1 infant-directed speech pooled preregistered row",
        "source_label": "ManyBabies 1 IDS pooled row",
        "citation_key": "manyBabies2020Ids",
        "row_unit": "pooled_primary_preregistered_project_effect",
        "row_label": "Infant-directed speech versus adult-directed speech pooled preference effect",
        "D": 0.35,
        "N": 2329,
        "supported": "yes",
        "journal": "Advances in Methods and Practices in Psychological Science",
        "source_file": "ManyBabies 1 project page and ManyBabies Consortium 2020; DOI 10.1177/2515245919900809",
        "source_row_number": 1,
    },
    {
        "point_id": "manybabies1_bilingual_ids_preference_pooled",
        "source_family": "ManyBabies 1 Bilingual infant-directed speech pooled preregistered row",
        "source_label": "ManyBabies 1 bilingual IDS pooled row",
        "citation_key": "byersHeinlein2021manybabiesBilingual",
        "row_unit": "pooled_primary_preregistered_project_effect",
        "row_label": "Bilingual infants' infant-directed speech versus adult-directed speech pooled preference effect",
        "D": 0.26,
        "N": 324,
        "supported": "yes",
        "journal": "Advances in Methods and Practices in Psychological Science",
        "source_file": "Byers-Heinlein et al. 2021; DOI 10.1177/2515245920974622; full-dataset bilingual dz=0.26 and local processed usable N=324",
        "source_row_number": 1,
    },
    {
        "point_id": "manyclasses1_feedback_timing_pooled",
        "source_family": "ManyClasses 1 feedback pooled preregistered row",
        "source_label": "ManyClasses 1 feedback pooled row",
        "citation_key": "fyfe2021manyclasses1",
        "row_unit": "pooled_primary_preregistered_project_effect",
        "row_label": "Immediate versus delayed feedback timing pooled classroom-learning effect",
        "D": 0.002,
        "N": 2081,
        "supported": "no",
        "journal": "Advances in Methods and Practices in Psychological Science",
        "source_file": "Fyfe et al. 2021; DOI 10.1177/25152459211027575; Δz=0.002, N=2,081",
        "source_row_number": 1,
    },
    {
        "point_id": "metaketa1_information_accountability_pooled_median",
        "source_family": "EGAP Metaketa I information/accountability pooled PAP row",
        "source_label": "EGAP Metaketa I pooled PAP row",
        "citation_key": "metaketaIRepo",
        "row_unit": "pooled_project_median_of_preregistered_binary_outcomes",
        "row_label": "Information/accountability pooled vote-choice and turnout effects",
        "D": 0.03945133390306835,
        "N": 26778.5,
        "supported": "not coded",
        "journal": "Science Advances",
        "field": "political science",
        "source_file": "data/raw/replication_projects/lead_harvest/metaketa_i_2019/github_metaketa_i/metaketa-i-main.zip; tab_11.1_main_effects.tex; Chinn conversion from overall binary ATE plus control mean, median of vote choice and turnout",
        "source_row_number": 1,
    },
    {
        "point_id": "metaketa3_natural_resource_monitoring_pooled_median",
        "source_family": "EGAP Metaketa III natural-resource monitoring pooled PAP row",
        "source_label": "EGAP Metaketa III pooled PAP row",
        "citation_key": "metaketaIIIProject",
        "row_unit": "pooled_project_median_of_preregistered_standardized_indices",
        "row_label": "Natural-resource monitoring pooled standardized index effects",
        "D": 0.06627377,
        "N": 16177,
        "supported": "not coded",
        "journal": "Proceedings of the National Academy of Sciences",
        "field": "political science",
        "source_file": "data/raw/replication_projects/lead_harvest/metaketa_iii_2021/osf_259yz/Replication.zip; site_estimates.Rdata and respondent_vars.Rdata; local random-effects pooling of Cov site ITTs, median of four standardized indices",
        "source_row_number": 1,
    },
    {
        "point_id": "metaketa4_community_policing_pooled_median",
        "source_family": "EGAP Metaketa IV community-policing pooled PAP row",
        "source_label": "EGAP Metaketa IV pooled PAP row",
        "citation_key": "metaketaIVProject",
        "row_unit": "pooled_project_median_of_preregistered_standardized_indices",
        "row_label": "Community-policing pooled standardized primary-index effects",
        "D": 0.01757533,
        "N": 18382,
        "supported": "not coded",
        "journal": "Science",
        "field": "political science",
        "source_file": "data/raw/replication_projects/lead_harvest/metaketa_iv_2021/osf_xqd3v_outputs/patrick_roach/data-examples-new/integrated RDS outputs/meta-estimates-main-hypotheses.RDS; median of eight primary standardized index estimates; respondent N from article/source",
        "source_row_number": 1,
    },
    {
        "point_id": "mousa2020_iraq_soccer_social_cohesion_median",
        "source_family": "Mousa 2020 Iraq soccer social-cohesion preregistered field experiment",
        "source_label": "Mousa 2020 Iraq soccer field experiment",
        "citation_key": "mousa2020soccerZenodo",
        "row_unit": "paper_median_of_preregistered_behavioral_and_attitudinal_outcomes",
        "row_label": "Soccer-team social cohesion median behavioral/attitudinal effect",
        "D": 0.23500410794013252,
        "N": 232,
        "supported": "not coded",
        "journal": "Science",
        "field": "political science",
        "source_file": "data/derived/effect_inflation_dataset/plot3_mousa2020_soccer_d_candidates.csv; generated from data/raw/corpus_candidates/political_science_unlock/zenodo/3942437; binary outcomes converted with Chinn from arm event counts and attitudinal indices as mean difference over control SD; median absolute D and median outcome N",
        "source_row_number": 1,
    },
]


BRODEUR_POLITICAL_SCIENCE_TITLE_RE = re.compile(
    r"("
    r"accountability|\baid\b|bureaucrat|candidac|\bcampaign\b|clientel|compliance|corruption|"
    r"debate|e-governance|\belections?\b|electoral|ethnically biased|foreign aid|"
    r"food distribution|governance|government|immigration|information campaign|"
    r"politic|protest|public|redistribution|service delivery|social programs|"
    r"selection of talent|state capacity|subsidized|tax|vot"
    r")",
    flags=re.I,
)


def brodeur_preregistered_field_for_title(title: object) -> str:
    """Route governance/political-economy Brodeur rows out of the generic economics bucket."""
    text = safe_text(title)
    if BRODEUR_POLITICAL_SCIENCE_TITLE_RE.search(text):
        return "political science"
    return "economics and finance"


def chinn_d_from_event_counts(
    treatment_events: float,
    treatment_n: float,
    control_events: float,
    control_n: float,
) -> float:
    """Convert a binary two-arm contrast to d via Chinn's log-OR approximation."""
    a = float(treatment_events)
    b = float(treatment_n) - a
    c = float(control_events)
    d = float(control_n) - c
    if min(a, b, c, d) <= 0:
        a += 0.5
        b += 0.5
        c += 0.5
        d += 0.5
    log_or = math.log((a * d) / (b * c))
    return log_or * math.sqrt(3) / math.pi


def d_from_t_statistic(t_statistic: float, n: float) -> float:
    return 2 * abs(float(t_statistic)) / math.sqrt(float(n))


def d_from_chi_square_1df(chi_square: float, n: float) -> float:
    r = math.sqrt(float(chi_square) / float(n))
    if r >= 1:
        return float("nan")
    return abs(2 * r / math.sqrt(1 - r**2))


def base_political_science_rescue_row(
    *,
    point_id: str,
    source_family: str,
    source_label: str,
    citation_key: str,
    row_unit: str,
    row_label: str,
    d_value: float,
    n_value: float,
    journal: str,
    source_file: str,
    source_row_number: int,
) -> dict[str, object]:
    return {
        "point_id": point_id,
        "source_family": source_family,
        "source_label": source_label,
        "field": "political science",
        "citation_key": citation_key,
        "row_unit": row_unit,
        "row_label": row_label,
        "D": float(d_value),
        "N": float(n_value),
        "supported": "not coded",
        "journal": journal,
        "source_file": source_file,
        "source_row_number": source_row_number,
    }


def local_elites_state_capacity_components(zip_path: Path) -> tuple[pd.DataFrame, dict[str, object]]:
    """Reconstruct the main central-vs-local tax compliance contrast from OpenICPSR 147561."""

    admin_base = "Replication Materials - Updated October 2025/Data/01_base/admin_data/"
    survey_base = "Replication Materials - Updated October 2025/Data/01_base/survey_data/"
    pilot_a7 = {200, 201, 202, 203, 207, 208, 210}

    def read_stata(archive: zipfile.ZipFile, member: str) -> pd.DataFrame:
        return pd.read_stata(io.BytesIO(archive.read(member)), convert_categoricals=False)

    with zipfile.ZipFile(zip_path) as archive:
        fliers = read_stata(archive, admin_base + "fliers_campaign.dta")
        fliers = fliers[~fliers["a7"].isin(pilot_a7)].copy()
        fliers = fliers[["code", "treatment_fr", "rate"]].rename(
            columns={
                "code": "compound1",
                "rate": "assign_flier_rate",
                "treatment_fr": "assign_treatment_fr",
            }
        )
        compound_text = fliers["compound1"].astype("Int64").astype(str)
        fliers["a7"] = np.where(compound_text.str.len() == 6, compound_text.str[:3], compound_text.str[:4]).astype(float)
        fliers["pilot"] = 0
        fliers["compound1"] = fliers["compound1"].astype(float)

        stratum = read_stata(archive, admin_base + "stratum.dta")[["a7", "stratum"]]

        assignment = read_stata(archive, admin_base + "randomization_schedule.dta")[["a7", "treatment", "month"]].copy()
        assignment.loc[assignment["a7"].eq(654), "treatment"] = 2
        assignment = assignment.rename(columns={"treatment": "tmt"})

        registration = read_stata(archive, admin_base + "registration_noPII.dta")
        registration = registration[registration["tot_complete"].eq(1)].copy()
        registration = registration.rename(columns={"today": "today_carto"})
        registration = registration[["compound1", "house", "mm_rate", "exempt", "today_carto"]]
        registration["compound1"] = registration["compound1"].astype(float)

        taxroll = read_stata(archive, admin_base + "taxroll_noPII.dta")[["compound1"]].drop_duplicates()
        taxroll["compound1"] = taxroll["compound1"].astype(float)

        midline = read_stata(archive, survey_base + "midline_noPII.dta")
        midline = midline.rename(
            columns={
                "compound": "compound1",
                "today": "today_monitoring",
                "exempt": "exempt_monitoring",
            }
        )
        possible_compound = midline["possible_compound"]
        midline.loc[possible_compound.isin([0, 999999, 9999999]) | possible_compound.isna(), "possible_compound"] = np.nan
        guessed_compound = midline["compound1"].eq(999999) & midline["possible_compound"].notna()
        midline.loc[guessed_compound, "compound1"] = midline.loc[guessed_compound, "possible_compound"]
        midline = midline[midline["compound1"].notna() & ~midline["compound1"].eq(999999)].copy()
        midline["max_tot_complete"] = midline.groupby("compound1")["tot_complete"].transform("max")
        midline = midline[midline["tot_complete"].eq(midline["max_tot_complete"])].copy()
        midline = midline.sort_values(["compound1", "start", "end"], kind="mergesort")
        midline = midline.groupby("compound1", as_index=False, sort=False).tail(1)
        midline = midline[["compound1", "code_same"]]
        midline["compound1"] = midline["compound1"].astype(float)

        payments = read_stata(archive, admin_base + "tax_payments_noPII.dta")
        payments = payments.rename(columns={"date": "date_TDM", "colcode": "colcode_TDM"})
        payments = payments[payments["unmatched_compound"].ne(1) & payments["compound1"].notna()].copy()
        payments = payments[["compound1", "date_TDM", "amountCF"]]
        payments["compound1"] = payments["compound1"].astype(float)

    data = fliers.merge(stratum, on="a7", how="left")
    data = data.merge(assignment, on="a7", how="left")
    data = data.merge(registration, on="compound1", how="outer", indicator="_merge_flier_carto")
    data["_merge_flier_carto_code"] = data["_merge_flier_carto"].map({"left_only": 1, "right_only": 2, "both": 3}).astype(int)
    data = data.merge(taxroll, on="compound1", how="outer", indicator="_merge_flier_carto_rep")
    data["_merge_flier_carto_rep_code"] = (
        data["_merge_flier_carto_rep"].map({"left_only": 1, "right_only": 2, "both": 3}).astype(int)
    )
    data = data.merge(midline, on="compound1", how="outer", indicator="_merge_flier_carto_rep_monit")
    data["_merge_flier_carto_rep_monit_code"] = (
        data["_merge_flier_carto_rep_monit"].map({"left_only": 1, "right_only": 2, "both": 3}).astype(int)
    )
    data = data[data["_merge_flier_carto_rep_monit_code"].ne(2)].copy()
    data = data.merge(payments, on="compound1", how="outer", indicator="_merge_payment")
    data["_merge_payment_code"] = data["_merge_payment"].map({"left_only": 1, "right_only": 2, "both": 3}).astype(int)
    unmatched_all = (
        data["_merge_flier_carto_code"].eq(1)
        & data["_merge_flier_carto_rep_code"].eq(1)
        & data["_merge_flier_carto_rep_monit_code"].eq(1)
    )
    data = data[~unmatched_all].copy()

    data["taxes_paid"] = 0
    data.loc[data["_merge_payment_code"].eq(3), "taxes_paid"] = 1
    data.loc[data["taxes_paid"].eq(0) & data["code_same"].eq(1), "taxes_paid"] = 1
    data.loc[
        data["house"].eq(1)
        & data["_merge_payment_code"].eq(3)
        & data["amountCF"].notna()
        & data["assign_flier_rate"].notna()
        & data["assign_flier_rate"].gt(data["amountCF"]),
        "taxes_paid",
    ] = 0
    data.loc[
        data["house"].eq(2)
        & data["_merge_payment_code"].eq(3)
        & data["amountCF"].notna()
        & data["mm_rate"].notna()
        & data["mm_rate"].gt(data["amountCF"]),
        "taxes_paid",
    ] = 0

    data["rate"] = np.nan
    data.loc[data["house"].eq(1), "rate"] = data.loc[data["house"].eq(1), "assign_flier_rate"]
    data.loc[data["house"].eq(2), "rate"] = data.loc[data["house"].eq(2), "mm_rate"]
    data = data[data["house"].ne(3)].copy()
    data = data[data["pilot"].ne(1)].copy()
    data = data[~data["a7"].isin(pilot_a7)].copy()
    data = data[data["rate"].notna()].copy()
    data["t_l"] = data["tmt"].eq(2).astype(int)

    central_local = data[data["tmt"].isin([1, 2])].copy()
    tab = central_local.groupby("tmt")["taxes_paid"].agg(["sum", "count", "mean"])
    control_events = float(tab.loc[1, "sum"])
    control_n = int(tab.loc[1, "count"])
    treatment_events = float(tab.loc[2, "sum"])
    treatment_n = int(tab.loc[2, "count"])
    raw_d = chinn_d_from_event_counts(treatment_events, treatment_n, control_events, control_n)

    components = pd.DataFrame(
        [
            {
                "source": "local_elites_state_capacity",
                "component": "local_vs_central_tax_compliance_raw_event_counts",
                "D_signed": raw_d,
                "D": abs(raw_d),
                "N": treatment_n + control_n,
                "treatment_events": treatment_events,
                "treatment_n": treatment_n,
                "treatment_mean": float(tab.loc[2, "mean"]),
                "control_events": control_events,
                "control_n": control_n,
                "control_mean": float(tab.loc[1, "mean"]),
                "raw_risk_difference": float(tab.loc[2, "mean"] - tab.loc[1, "mean"]),
                "cluster_n": int(central_local["a7"].nunique()),
                "append_to_plot": False,
            }
        ]
    )

    native: dict[str, object] = {}
    try:
        import statsmodels.formula.api as smf

        analysis = data.copy()
        analysis.loc[analysis["date_TDM"] < pd.Timestamp("2018-06-15"), "date_TDM"] = pd.NaT
        analysis.loc[(analysis["tmt"].eq(3)) & (analysis["date_TDM"] < pd.Timestamp("2018-07-16")), "date_TDM"] = pd.NaT
        carto_replacements = {
            112: "2018-11-28",
            219: "2018-11-28",
            224: "2018-11-29",
            238: "2018-12-03",
            327: "2018-12-06",
            343: "2018-11-30",
            356: "2018-11-30",
            510: "2018-12-03",
            512: "2018-12-03",
            514: "2018-11-26",
            533: "2018-11-28",
            538: "2018-11-29",
            544: "2018-11-29",
            588: "2018-11-27",
            596: "2018-11-29",
            658: "2018-11-27",
            664: "2018-11-28",
            669: "2018-12-01",
            678: "2018-11-29",
            204: "2018-08-09",
            624: "2018-06-21",
            6104: "2018-08-08",
            231: "2018-06-18",
            300: "2018-06-16",
            312: "2018-09-17",
            313: "2018-06-15",
            502: "2018-07-18",
            507: "2018-08-08",
            557: "2018-08-08",
            563: "2018-06-25",
            571: "2018-08-18",
            577: "2018-08-08",
            595: "2018-12-11",
            597: "2018-07-19",
            619: "2018-08-08",
            635: "2018-08-08",
            647: "2018-11-07",
            701: "2018-09-07",
            6103: "2018-11-06",
        }
        for a7, date_text in carto_replacements.items():
            analysis.loc[analysis["a7"].eq(a7) & analysis["today_carto"].isna(), "today_carto"] = pd.Timestamp(date_text)
        analysis.loc[
            analysis["a7"].eq(694)
            & analysis["compound1"].isin([694001, 694002, 694003, 694004])
            & analysis["today_carto"].isna(),
            "today_carto",
        ] = pd.Timestamp("2018-11-05")
        analysis.loc[analysis["a7"].eq(694) & analysis["today_carto"].isna(), "today_carto"] = pd.Timestamp("2018-11-06")

        analysis = analysis.sort_values(["a7", "compound1"], kind="mergesort").copy()
        previous_carto = analysis.groupby("a7")["today_carto"].shift(1)
        next_carto = analysis.groupby("a7")["today_carto"].shift(-1)
        rank = analysis.groupby("a7").cumcount() + 1
        max_rank = analysis.groupby("a7")["compound1"].transform("size")
        missing_between = analysis["today_carto"].isna() & previous_carto.notna() & next_carto.notna()
        same_neighbors = missing_between & previous_carto.eq(next_carto)
        analysis.loc[same_neighbors, "today_carto"] = previous_carto[same_neighbors]
        different_neighbors = missing_between & previous_carto.ne(next_carto)
        analysis.loc[different_neighbors & rank.eq(max_rank), "today_carto"] = previous_carto[different_neighbors & rank.eq(max_rank)]
        analysis.loc[different_neighbors & rank.ne(max_rank), "today_carto"] = next_carto[different_neighbors & rank.ne(max_rank)]

        min_tdm = analysis.groupby("a7")["date_TDM"].transform("min")
        max_carto = analysis.groupby("a7")["today_carto"].transform("max")
        analysis["today_alt"] = min_tdm
        analysis.loc[analysis["today_alt"].isna() & max_carto.notna(), "today_alt"] = max_carto
        origin = pd.Timestamp("1960-01-01")
        cut_bounds = [origin + pd.Timedelta(days=day) for day in [21355, 21415, 21475, 21532]]
        model_sample = analysis[analysis["tmt"].isin([1, 2])].copy()
        model_sample["time_FE_tdm_2mo_CvL"] = pd.cut(
            model_sample["today_alt"],
            bins=cut_bounds,
            right=False,
            labels=False,
            include_lowest=True,
        )
        model_sample = model_sample.dropna(
            subset=["taxes_paid", "t_l", "stratum", "house", "time_FE_tdm_2mo_CvL", "a7"]
        ).copy()
        model = smf.ols(
            "taxes_paid ~ t_l + C(stratum) + C(house) + C(time_FE_tdm_2mo_CvL)",
            data=model_sample,
        ).fit(cov_type="cluster", cov_kwds={"groups": model_sample["a7"]})
        native = {
            "table4_adjusted_ate": float(model.params["t_l"]),
            "table4_adjusted_se": float(model.bse["t_l"]),
            "table4_adjusted_p": float(model.pvalues["t_l"]),
            "table4_adjusted_n": int(model.nobs),
            "table4_adjusted_cluster_n": int(model_sample["a7"].nunique()),
        }
    except Exception as exc:
        native = {"table4_adjusted_blocker": safe_text(exc)}

    return components, native


def hewitt_campaign_experiments_components(zip_path: Path) -> tuple[pd.DataFrame, dict[str, object]]:
    """Build D-ready treatment-arm contrasts from the Hewitt et al. campaign-experiment archive."""

    import pyreadr

    members = [
        "replication_archive/output/processed_data/responses.RDS",
        "replication_archive/output/processed_data/regression_ates.RDS",
        "replication_archive/output/processed_data/studies.RDS",
    ]
    with tempfile.TemporaryDirectory() as tmpdir:
        with zipfile.ZipFile(zip_path) as archive:
            for member in members:
                archive.extract(member, tmpdir)
        processed = Path(tmpdir) / "replication_archive" / "output" / "processed_data"
        responses = pyreadr.read_r(str(processed / "responses.RDS"))[None]
        ates = pyreadr.read_r(str(processed / "regression_ates.RDS"))[None]
        studies = pyreadr.read_r(str(processed / "studies.RDS"))[None]

    rows: list[dict[str, object]] = []
    for outcome in ["favorability", "votechoice"]:
        values = responses[["study_id", "content_id", "treat", outcome]].copy()
        values["study_id"] = values["study_id"].astype(str)
        values["content_id"] = values["content_id"].astype(str)
        values["treat"] = pd.to_numeric(values["treat"], errors="coerce")
        values[outcome] = pd.to_numeric(values[outcome], errors="coerce")
        values = values.dropna(subset=[outcome])

        controls = (
            values[values["treat"].eq(0)]
            .groupby("study_id")[outcome]
            .agg(control_n="count", control_mean="mean", control_sd=lambda x: x.std(ddof=1))
            .reset_index()
        )
        treatments = (
            values[values["treat"].eq(1)]
            .groupby(["study_id", "content_id"])[outcome]
            .agg(treatment_n="count", treatment_mean="mean")
            .reset_index()
        )
        outcome_ates = ates[ates["outcome"].astype(str).eq(outcome)].copy()
        outcome_ates["study_id"] = outcome_ates["study_id"].astype(str)
        outcome_ates["content_id"] = outcome_ates["content_id"].astype(str)
        merged = outcome_ates.merge(treatments, on=["study_id", "content_id"], how="inner")
        merged = merged.merge(controls, on="study_id", how="inner")
        merged = merged[merged["control_sd"].gt(0) & merged["treatment_n"].gt(1) & merged["control_n"].gt(1)].copy()
        merged["D_signed"] = (merged["treatment_mean"] - merged["control_mean"]) / merged["control_sd"]
        merged["D"] = merged["D_signed"].abs()
        merged["N"] = merged["treatment_n"] + merged["control_n"]

        for _, component in merged.iterrows():
            rows.append(
                {
                    "source": "hewitt_campaign_experiments",
                    "component": f"{component['study_id']}:{component['content_id']}:{outcome}",
                    "study_id": component["study_id"],
                    "content_id": component["content_id"],
                    "outcome": outcome,
                    "D_signed": float(component["D_signed"]),
                    "D": float(component["D"]),
                    "N": int(component["N"]),
                    "treatment_n": int(component["treatment_n"]),
                    "control_n": int(component["control_n"]),
                    "treatment_mean": float(component["treatment_mean"]),
                    "control_mean": float(component["control_mean"]),
                    "control_sd": float(component["control_sd"]),
                    "native_estimate_pp": float(component["estimate"]),
                    "native_se_pp": float(component["std.error"]),
                    "native_p": float(component["p.value"]),
                    "append_to_plot": False,
                }
            )

    components = pd.DataFrame(rows)
    summary = {
        "studies_n": int(studies["study_id"].nunique()),
        "study_total_respondents": int(pd.to_numeric(studies["n_responses_study"], errors="coerce").sum()),
        "component_contrasts_n": int(len(components)),
    }
    return components, summary


def political_science_strict_rescue_rows() -> pd.DataFrame:
    """Extraction-backed strict Plot 3 rows unlocked from the political-science queue."""
    plot_rows: list[dict[str, object]] = []
    audit_rows: list[dict[str, object]] = []

    def ols_coefficients(y: pd.Series, design: pd.DataFrame) -> pd.Series:
        beta = np.linalg.lstsq(design.to_numpy(dtype=float), y.to_numpy(dtype=float), rcond=None)[0]
        return pd.Series(beta, index=design.columns)

    if GOOD_POLITICIANS_ZIP.exists():
        try:
            with zipfile.ZipFile(GOOD_POLITICIANS_ZIP) as archive:
                with archive.open("replication/cand_final.dta") as handle:
                    good = pd.read_stata(io.BytesIO(handle.read()))
            components: list[dict[str, object]] = []
            for outcome in ["filer", "elect"]:
                outcome_values = numeric_series(good[outcome])
                for treatment_arm in ["tv_social", "tv_personal"]:
                    control_mask = numeric_series(good["tv_neutral"]).eq(1) & outcome_values.notna()
                    treatment_mask = numeric_series(good[treatment_arm]).eq(1) & outcome_values.notna()
                    control_n = int(control_mask.sum())
                    treatment_n = int(treatment_mask.sum())
                    control_events = float(outcome_values.loc[control_mask].sum())
                    treatment_events = float(outcome_values.loc[treatment_mask].sum())
                    component_d = chinn_d_from_event_counts(
                        treatment_events,
                        treatment_n,
                        control_events,
                        control_n,
                    )
                    components.append(
                        {
                            "source": "good_politicians",
                            "component": f"{outcome}:{treatment_arm}_vs_neutral",
                            "D_signed": component_d,
                            "D": abs(component_d),
                            "N": treatment_n + control_n,
                            "treatment_events": treatment_events,
                            "treatment_n": treatment_n,
                            "control_events": control_events,
                            "control_n": control_n,
                            "append_to_plot": False,
                        }
                    )
            if components:
                component_df = pd.DataFrame(components)
                row = base_political_science_rescue_row(
                    point_id="good_politicians_candidacy_election_chinn_median",
                    source_family="Good Politicians preregistered political-candidacy field experiment",
                    source_label="Good Politicians field experiment",
                    citation_key="goodPoliticiansZenodo",
                    row_unit="paper_median_of_preregistered_binary_primary_outcomes",
                    row_label="Political candidacy and election median raw arm-count effect",
                    d_value=float(component_df["D"].median()),
                    n_value=float(component_df["N"].median()),
                    journal="Review of Economic Studies",
                    source_file=(
                        f"{GOOD_POLITICIANS_ZIP.relative_to(ROOT)}; replication/cand_final.dta; "
                        "Chinn conversion from raw arm event counts for preregistered candidacy/election outcomes"
                    ),
                    source_row_number=1,
                )
                plot_rows.append(row)
                audit_rows.extend(components)
                audit_rows.append({**row, "source": "good_politicians", "append_to_plot": True})
        except Exception as exc:
            audit_rows.append(
                {
                    "source": "good_politicians",
                    "append_to_plot": False,
                    "blocker": f"failed to parse {GOOD_POLITICIANS_ZIP.relative_to(ROOT)}: {exc}",
                }
            )

    if GHANA_DEBATES_TAB.exists():
        try:
            ghana = pd.read_csv(GHANA_DEBATES_TAB, sep="\t", low_memory=False)
            treatment = numeric_series(ghana["T"]).eq(1)
            control = numeric_series(ghana["T"]).eq(0)
            outcome_values = numeric_series(ghana["overall_"])
            overall_t = treatment & outcome_values.notna()
            overall_c = control & outcome_values.notna()
            overall_d = (
                float(outcome_values.loc[overall_t].mean() - outcome_values.loc[overall_c].mean())
                / float(outcome_values.loc[overall_c].std(ddof=1))
            )
            support_values = numeric_series(ghana["support"])
            support_t = treatment & support_values.notna()
            support_c = control & support_values.notna()
            support_d = chinn_d_from_event_counts(
                float(support_values.loc[support_t].sum()),
                int(support_t.sum()),
                float(support_values.loc[support_c].sum()),
                int(support_c.sum()),
            )
            components = [
                {
                    "source": "ghana_debates",
                    "component": "overall_candidate_evaluation_mean_diff_control_sd",
                    "D_signed": overall_d,
                    "D": abs(overall_d),
                    "N": int(overall_t.sum() + overall_c.sum()),
                    "append_to_plot": False,
                },
                {
                    "source": "ghana_debates",
                    "component": "support_binary_chinn_log_or",
                    "D_signed": support_d,
                    "D": abs(support_d),
                    "N": int(support_t.sum() + support_c.sum()),
                    "append_to_plot": False,
                },
            ]
            component_df = pd.DataFrame(components)
            row = base_political_science_rescue_row(
                point_id="ghana_debates_candidate_evaluation_support_median",
                source_family="Ghana debates preregistered candidate-debates field experiment",
                source_label="Ghana debates field experiment",
                citation_key="ghanaDebatesDataverse",
                row_unit="paper_median_of_table3_primary_outcomes",
                row_label="Candidate debates median effect on candidate evaluation and support",
                d_value=float(component_df["D"].median()),
                n_value=float(component_df["N"].median()),
                journal="American Journal of Political Science",
                source_file=(
                    f"{GHANA_DEBATES_TAB.relative_to(ROOT)}; BKO_Debates_Replication_Code.do Table 3; "
                    "overall_ as mean difference/control SD and support via Chinn from raw arm event counts"
                ),
                source_row_number=2,
            )
            plot_rows.append(row)
            audit_rows.extend(components)
            audit_rows.append({**row, "source": "ghana_debates", "append_to_plot": True})
        except Exception as exc:
            audit_rows.append(
                {
                    "source": "ghana_debates",
                    "append_to_plot": False,
                    "blocker": f"failed to parse {GHANA_DEBATES_TAB.relative_to(ROOT)}: {exc}",
                }
            )

    if VIETNAM_LEGISLATOR_OUTCOMES.exists():
        try:
            vietnam = pd.read_excel(VIETNAM_LEGISLATOR_OUTCOMES)
            components: list[dict[str, object]] = []
            for outcome in ["Spoke", "said_citizen_related", "said_firm_related"]:
                outcome_values = numeric_series(vietnam[outcome])
                treatment_values = vietnam["Treatment"].fillna("").astype(str)
                for treatment_arm in ["Citizen", "Firm"]:
                    treatment_mask = treatment_values.eq(treatment_arm) & outcome_values.notna()
                    control_mask = treatment_values.eq("Control") & outcome_values.notna()
                    component_d = chinn_d_from_event_counts(
                        float(outcome_values.loc[treatment_mask].sum()),
                        int(treatment_mask.sum()),
                        float(outcome_values.loc[control_mask].sum()),
                        int(control_mask.sum()),
                    )
                    components.append(
                        {
                            "source": "vietnam_legislator_responsiveness",
                            "component": f"{outcome}:{treatment_arm}_vs_control",
                            "D_signed": component_d,
                            "D": abs(component_d),
                            "N": int(treatment_mask.sum() + control_mask.sum()),
                            "append_to_plot": False,
                        }
                    )
            component_df = pd.DataFrame(components)
            row = base_political_science_rescue_row(
                point_id="vietnam_legislator_responsiveness_speech_content_chinn_median",
                source_family="Vietnam legislator-responsiveness preregistered field experiment",
                source_label="Vietnam legislator responsiveness",
                citation_key="vietnamLegislatorResponsivenessDataverse",
                row_unit="paper_median_of_preregistered_binary_speech_outcomes",
                row_label="Legislator responsiveness median speaking/content effect",
                d_value=float(component_df["D"].median()),
                n_value=float(component_df["N"].median()),
                journal="Journal of Politics",
                source_file=(
                    f"{VIETNAM_LEGISLATOR_OUTCOMES.relative_to(ROOT)}; AEA RCT Registry trial 1608; "
                    "Chinn conversion from raw Citizen/Firm versus Control event counts for speech and content outcomes"
                ),
                source_row_number=3,
            )
            plot_rows.append(row)
            audit_rows.extend(components)
            audit_rows.append({**row, "source": "vietnam_legislator_responsiveness", "append_to_plot": True})
        except Exception as exc:
            audit_rows.append(
                {
                    "source": "vietnam_legislator_responsiveness",
                    "append_to_plot": False,
                    "blocker": f"failed to parse {VIETNAM_LEGISLATOR_OUTCOMES.relative_to(ROOT)}: {exc}",
                }
            )

    if VIETNAM_MAIN_SURVEY_OUTCOMES.exists():
        try:
            vietnam_main = pd.read_excel(VIETNAM_MAIN_SURVEY_OUTCOMES)
            components = []
            outcome_values = numeric_series(vietnam_main["Q1"])
            treatment_values = vietnam_main["Treatment"].fillna("").astype(str)
            for treatment_arm in ["Citizen", "Firm"]:
                treatment_mask = treatment_values.eq(treatment_arm) & outcome_values.notna()
                control_mask = treatment_values.eq("Control") & outcome_values.notna()
                component_d = chinn_d_from_event_counts(
                    float(outcome_values.loc[treatment_mask].sum()),
                    int(treatment_mask.sum()),
                    float(outcome_values.loc[control_mask].sum()),
                    int(control_mask.sum()),
                )
                components.append(
                    {
                        "source": "vietnam_main_responsiveness",
                        "component": f"Q1_prepared_for_debate:{treatment_arm}_vs_control",
                        "D_signed": component_d,
                        "D": abs(component_d),
                        "N": int(treatment_mask.sum() + control_mask.sum()),
                        "treatment_events": float(outcome_values.loc[treatment_mask].sum()),
                        "treatment_n": int(treatment_mask.sum()),
                        "control_events": float(outcome_values.loc[control_mask].sum()),
                        "control_n": int(control_mask.sum()),
                        "append_to_plot": False,
                    }
                )
            component_df = pd.DataFrame(components)
            row = base_political_science_rescue_row(
                point_id="vietnam_main_responsiveness_prepared_debate_chinn_median",
                source_family="Vietnam National Assembly main responsiveness preregistered field experiment",
                source_label="Vietnam National Assembly responsiveness",
                citation_key="vietnamMainResponsivenessDataverse",
                row_unit="paper_median_of_preregistered_binary_delegate_survey_outcome",
                row_label="Vietnam National Assembly delegate preparedness median Citizen/Firm treatment effect",
                d_value=float(component_df["D"].median()),
                n_value=float(component_df["N"].median()),
                journal="Journal of Politics",
                source_file=(
                    f"{VIETNAM_MAIN_SURVEY_OUTCOMES.relative_to(ROOT)}; "
                    f"{VIETNAM_MAIN_EXPERIMENTAL_ANALYSES.relative_to(ROOT)}; AEA RCT Registry trial 1608; "
                    "Q1 delegate-survey preparedness outcome converted with Chinn from raw Citizen/Firm versus Control event counts"
                ),
                source_row_number=4,
            )
            plot_rows.append(row)
            audit_rows.extend(components)
            audit_rows.append({**row, "source": "vietnam_main_responsiveness", "append_to_plot": True})
        except Exception as exc:
            audit_rows.append(
                {
                    "source": "vietnam_main_responsiveness",
                    "append_to_plot": False,
                    "blocker": f"failed to parse {VIETNAM_MAIN_SURVEY_OUTCOMES.relative_to(ROOT)}: {exc}",
                }
            )

    if GOLDEN_PS_MASTER.exists():
        try:
            golden = pd.read_csv(GOLDEN_PS_MASTER, sep="\t", low_memory=False).copy()
            ki_cols = [
                "ki_improve_schools_any_sum_endline",
                "ki_improve_roads_any_sum_endline",
                "ki_improve_healthfacilities_any_sum_endline",
                "ki_improve_employment_any_sum_endline",
                "ki_improve_electricityinfrastructure_any_sum_endline",
                "ki_improve_gasinfrastructure_any_sum_endline",
                "ki_improve_drinkingwater_any_sum_endline",
                "ki_improve_rubbish_any_sum_endline",
                "ki_improve_security_any_sum_endline",
            ]
            ki_effort_sum = golden[ki_cols].apply(pd.to_numeric, errors="coerce").sum(axis=1)
            golden = golden.assign(
                ki_effort_sum=ki_effort_sum,
                ki_any_effort=(ki_effort_sum > 0).astype(float),
            )
            components = []
            continuous_outcomes = [
                ("mpa_share_mamoor_2018", "top_20_treated"),
                ("turnout_2018", "top_20_treated"),
                ("ki_effort_sum", "treated_ps"),
                ("ki_mpa_visit_june_avg_endline", "treated_ps"),
            ]
            for outcome, treatment_col in continuous_outcomes:
                outcome_values = numeric_series(golden[outcome])
                treatment_values = numeric_series(golden[treatment_col])
                treatment_mask = treatment_values.eq(1) & outcome_values.notna()
                control_mask = treatment_values.eq(0) & outcome_values.notna()
                control_sd = float(outcome_values.loc[control_mask].std(ddof=1))
                component_d = (
                    float(outcome_values.loc[treatment_mask].mean() - outcome_values.loc[control_mask].mean())
                    / control_sd
                    if control_sd > 0
                    else float("nan")
                )
                components.append(
                    {
                        "source": "golden_gulzar_sonnet",
                        "component": outcome,
                        "D_signed": component_d,
                        "D": abs(component_d),
                        "N": int(treatment_mask.sum() + control_mask.sum()),
                        "append_to_plot": False,
                    }
                )
            any_effort = numeric_series(golden["ki_any_effort"])
            treatment_values = numeric_series(golden["treated_ps"])
            treatment_mask = treatment_values.eq(1) & any_effort.notna()
            control_mask = treatment_values.eq(0) & any_effort.notna()
            any_effort_d = chinn_d_from_event_counts(
                float(any_effort.loc[treatment_mask].sum()),
                int(treatment_mask.sum()),
                float(any_effort.loc[control_mask].sum()),
                int(control_mask.sum()),
            )
            components.append(
                {
                    "source": "golden_gulzar_sonnet",
                    "component": "ki_any_effort",
                    "D_signed": any_effort_d,
                    "D": abs(any_effort_d),
                    "N": int(treatment_mask.sum() + control_mask.sum()),
                    "append_to_plot": False,
                }
            )
            component_df = pd.DataFrame(components)
            row = base_political_science_rescue_row(
                point_id="golden_gulzar_sonnet_responsiveness_primary_median",
                source_family="Golden Gulzar Sonnet political-responsiveness preregistered field experiment",
                source_label="Golden/Gulzar/Sonnet responsiveness",
                citation_key="goldenGulzarSonnetDataverse",
                row_unit="paper_median_of_preregistered_polling_station_outcomes",
                row_label="Political responsiveness and information provision median primary effect",
                d_value=float(component_df["D"].median()),
                n_value=float(component_df["N"].median()),
                journal="Comparative Political Studies",
                source_file=(
                    f"{GOLDEN_PS_MASTER.relative_to(ROOT)}; EGAP registration 2476 and OSF PAP vadwn; "
                    "vote-share/turnout/effort outcomes as mean difference over control SD, binary any-effort via Chinn"
                ),
                source_row_number=4,
            )
            plot_rows.append(row)
            audit_rows.extend(components)
            audit_rows.append({**row, "source": "golden_gulzar_sonnet", "append_to_plot": True})
        except Exception as exc:
            audit_rows.append(
                {
                    "source": "golden_gulzar_sonnet",
                    "append_to_plot": False,
                    "blocker": f"failed to parse {GOLDEN_PS_MASTER.relative_to(ROOT)}: {exc}",
                }
            )

    if KALLA_BROOCKMAN_MINIMAL_EFFECTS.exists():
        try:
            kb = pd.read_csv(KALLA_BROOCKMAN_MINIMAL_EFFECTS, sep="\t", low_memory=False)
            coef = numeric_series(kb["Candidate.Effect.with.Covars"])
            se = numeric_series(kb["Candidate.Effect.SE.with.Covars"])
            n_values = numeric_series(kb["t1.N"])
            valid = coef.notna() & se.gt(0) & n_values.gt(0)
            component_d = 2 * (coef.loc[valid] / se.loc[valid]).abs() / np.sqrt(n_values.loc[valid])
            components = []
            for idx in component_d.index:
                components.append(
                    {
                        "source": "kalla_broockman_2018",
                        "component": safe_text(kb.loc[idx, "ExperimentName"]) or safe_text(kb.loc[idx, "Experiment"]),
                        "D": float(component_d.loc[idx]),
                        "N": float(n_values.loc[idx]),
                        "append_to_plot": False,
                    }
                )
            audit_rows.extend(components)
            for component_idx, component in enumerate(components, start=1):
                experiment_label = safe_text(component.get("component")) or f"experiment {component_idx}"
                row = base_political_science_rescue_row(
                    point_id=f"kalla_broockman_2018_campaign_contact_experiment_{component_idx:03d}",
                    source_family="Kalla Broockman 2018 preregistered campaign-contact field-experiment archive",
                    source_label="Kalla/Broockman campaign contact",
                    citation_key="kallaBroockman2018Dataverse",
                    row_unit="component_campaign_experiment_candidate_effect",
                    row_label=f"Minimal persuasive effects campaign experiment: {experiment_label}",
                    d_value=float(component["D"]),
                    n_value=float(component["N"]),
                    journal="American Political Science Review",
                    source_file=(
                        f"{KALLA_BROOCKMAN_MINIMAL_EFFECTS.relative_to(ROOT)}; Harvard Dataverse doi:10.7910/DVN/RAMHWP; "
                        "experiment-level candidate-effect t-statistic converted as 2|t|/sqrt(N)"
                    ),
                    source_row_number=5000 + component_idx,
                )
                plot_rows.append(row)
                audit_rows.append(
                    {
                        **row,
                        "source": "kalla_broockman_2018",
                        "component": experiment_label,
                        "append_to_plot": True,
                    }
                )
        except Exception as exc:
            audit_rows.append(
                {
                    "source": "kalla_broockman_2018",
                    "append_to_plot": False,
                    "blocker": f"failed to parse {KALLA_BROOCKMAN_MINIMAL_EFFECTS.relative_to(ROOT)}: {exc}",
                }
            )

    if LOCAL_ELITES_OPENICPSR_ZIP.exists():
        try:
            component_df, native_stats = local_elites_state_capacity_components(LOCAL_ELITES_OPENICPSR_ZIP)
            if not component_df.empty:
                row = base_political_science_rescue_row(
                    point_id="local_elites_state_capacity_tax_compliance_chinn",
                    source_family="Local Elites state-capacity tax-compliance preregistered field experiment",
                    source_label="Local Elites tax compliance",
                    citation_key="localElitesOpenicpsr",
                    row_unit="paper_primary_binary_tax_compliance_outcome",
                    row_label="Local chiefs versus central collectors tax-compliance effect",
                    d_value=float(component_df["D"].median()),
                    n_value=float(component_df["N"].median()),
                    journal="OpenICPSR replication package",
                    source_file=(
                        f"{LOCAL_ELITES_OPENICPSR_ZIP.relative_to(ROOT)}; Dofiles/2_Data_Construction.do "
                        "and Dofiles/Tables_Figures/Table4.do; Chinn conversion from reconstructed raw "
                        "central/local tax-compliance event counts; adjusted native Table 4 ATE retained in audit"
                    ),
                    source_row_number=6,
                )
                plot_rows.append(row)
                audit_rows.extend({**dict(component), **native_stats} for component in component_df.to_dict("records"))
                audit_rows.append(
                    {
                        **row,
                        **native_stats,
                        "source": "local_elites_state_capacity",
                        "append_to_plot": True,
                    }
                )
        except Exception as exc:
            audit_rows.append(
                {
                    "source": "local_elites_state_capacity",
                    "append_to_plot": False,
                    "blocker": f"failed to parse {LOCAL_ELITES_OPENICPSR_ZIP.relative_to(ROOT)}: {exc}",
                }
            )

    if HEWITT_CAMPAIGN_ARCHIVE_ZIP.exists():
        try:
            component_df, summary = hewitt_campaign_experiments_components(HEWITT_CAMPAIGN_ARCHIVE_ZIP)
            if not component_df.empty:
                audit_rows.extend({**dict(component), **summary} for component in component_df.to_dict("records"))
                study_rows = (
                    component_df.groupby(["study_id", "content_id"], sort=True)
                    .agg(
                        D=("D", "median"),
                        N=("N", "median"),
                        component_contrasts_n=("D", "size"),
                    )
                    .reset_index()
                )
                for study_idx, study in study_rows.iterrows():
                    study_number = int(study_idx) + 1
                    row = base_political_science_rescue_row(
                        point_id=f"hewitt_campaign_experiments_study_content_{study_number:03d}",
                        source_family="Hewitt et al. campaign-ad persuasion preregistered experiment archive",
                        source_label="Campaign-ad persuasion archive",
                        citation_key="hewittCampaignExperimentsDataverse",
                        row_unit="component_campaign_study_content_median_of_votechoice_favorability_outcomes",
                        row_label=(
                            "Campaign-ad persuasion archive study-content contrast "
                            f"{safe_text(study['study_id'])}/{safe_text(study['content_id'])}"
                        ),
                        d_value=float(study["D"]),
                        n_value=float(study["N"]),
                        journal="American Political Science Review",
                        source_file=(
                            f"{HEWITT_CAMPAIGN_ARCHIVE_ZIP.relative_to(ROOT)}; "
                            "output/processed_data/responses.RDS and regression_ates.RDS; "
                            "study-content-level median of preregistered vote-choice/favorability outcomes; "
                            "D computed as treatment-control mean difference over within-study control SD"
                        ),
                        source_row_number=7000 + study_number,
                    )
                    plot_rows.append(row)
                    audit_rows.append(
                        {
                            **row,
                            **summary,
                            "source": "hewitt_campaign_experiments",
                            "study_id": safe_text(study["study_id"]),
                            "content_id": safe_text(study["content_id"]),
                            "component_outcomes_in_study_content": int(study["component_contrasts_n"]),
                            "append_to_plot": True,
                        }
                    )
        except Exception as exc:
            audit_rows.append(
                {
                    "source": "hewitt_campaign_experiments",
                    "append_to_plot": False,
                    "blocker": f"failed to parse {HEWITT_CAMPAIGN_ARCHIVE_ZIP.relative_to(ROOT)}: {exc}",
                }
            )

    if POLITICAL_ACTIVISTS_ZIP.exists():
        try:
            with zipfile.ZipFile(POLITICAL_ACTIVISTS_ZIP) as archive:
                with archive.open("Replication_JOP_final/data/clean/clean_all.dta") as handle:
                    activists = pd.read_stata(io.BytesIO(handle.read()))
            components = []
            treatment_values = activists["treatment"].astype(str)
            primary_outcomes = [
                ("canvass_any_main_unres", "binary_any_canvassing"),
                ("days_unres_main", "days_canvassed"),
                ("doors_unres_main_wins", "doors_knocked_winsorized"),
            ]
            for outcome, label in primary_outcomes:
                outcome_values = numeric_series(activists[outcome])
                treatment_mask = treatment_values.eq("treatment") & outcome_values.notna()
                control_mask = treatment_values.eq("control") & outcome_values.notna()
                if set(pd.unique(outcome_values.dropna())).issubset({0, 1, 0.0, 1.0}):
                    component_d = chinn_d_from_event_counts(
                        float(outcome_values.loc[treatment_mask].sum()),
                        int(treatment_mask.sum()),
                        float(outcome_values.loc[control_mask].sum()),
                        int(control_mask.sum()),
                    )
                    conversion = "chinn_binary_event_counts"
                else:
                    control_sd = float(outcome_values.loc[control_mask].std(ddof=1))
                    component_d = (
                        float(outcome_values.loc[treatment_mask].mean() - outcome_values.loc[control_mask].mean())
                        / control_sd
                    )
                    conversion = "mean_difference_over_control_sd"
                components.append(
                    {
                        "source": "political_activists",
                        "component": label,
                        "D_signed": component_d,
                        "D": abs(component_d),
                        "N": int(treatment_mask.sum() + control_mask.sum()),
                        "treatment_n": int(treatment_mask.sum()),
                        "control_n": int(control_mask.sum()),
                        "treatment_mean": float(outcome_values.loc[treatment_mask].mean()),
                        "control_mean": float(outcome_values.loc[control_mask].mean()),
                        "conversion": conversion,
                        "append_to_plot": False,
                    }
                )
            component_df = pd.DataFrame(components)
            row = base_political_science_rescue_row(
                point_id="hensel_rink_political_activists_canvassing_median",
                source_family="Hensel Rink political-activist motivation preregistered field experiment",
                source_label="Political activists field experiment",
                citation_key="henselRinkPoliticalActivistsDataverse",
                row_unit="paper_median_of_preregistered_canvassing_effort_outcomes",
                row_label="Political activists median treatment effect on canvassing effort",
                d_value=float(component_df["D"].median()),
                n_value=float(component_df["N"].median()),
                journal="Journal of Politics",
                source_file=(
                    f"{POLITICAL_ACTIVISTS_ZIP.relative_to(ROOT)}; Replication_JOP_final/data/clean/clean_all.dta; "
                    "Table 1 primary canvassing outcomes reconstructed from raw treatment/control groups"
                ),
                source_row_number=10,
            )
            plot_rows.append(row)
            audit_rows.extend(components)
            audit_rows.append({**row, "source": "political_activists", "append_to_plot": True})
        except Exception as exc:
            audit_rows.append(
                {
                    "source": "political_activists",
                    "append_to_plot": False,
                    "blocker": f"failed to parse {POLITICAL_ACTIVISTS_ZIP.relative_to(ROOT)}: {exc}",
                }
            )

    if CHINA_AID_ATTITUDES_ZIP.exists():
        try:
            with zipfile.ZipFile(CHINA_AID_ATTITUDES_ZIP) as archive:
                with archive.open("2 NZ data JEPS FINAL.dta") as handle:
                    china_aid = pd.read_stata(io.BytesIO(handle.read()), convert_categoricals=False)
            components = []
            for outcome, label in [
                ("toomuchaid", "too_much_aid"),
                ("morepac", "more_aid_to_pacific"),
                ("favournz", "aid_should_favour_national_interest"),
            ]:
                outcome_values = numeric_series(china_aid[outcome])
                treatment_values = numeric_series(china_aid["treatment"])
                treatment_mask = treatment_values.eq(1) & outcome_values.notna()
                control_mask = treatment_values.eq(0) & outcome_values.notna()
                component_d = chinn_d_from_event_counts(
                    float(outcome_values.loc[treatment_mask].sum()),
                    int(treatment_mask.sum()),
                    float(outcome_values.loc[control_mask].sum()),
                    int(control_mask.sum()),
                )
                components.append(
                    {
                        "source": "china_aid_attitudes",
                        "component": label,
                        "D_signed": component_d,
                        "D": abs(component_d),
                        "N": int(treatment_mask.sum() + control_mask.sum()),
                        "treatment_n": int(treatment_mask.sum()),
                        "control_n": int(control_mask.sum()),
                        "treatment_mean": float(outcome_values.loc[treatment_mask].mean()),
                        "control_mean": float(outcome_values.loc[control_mask].mean()),
                        "append_to_plot": False,
                    }
                )
            component_df = pd.DataFrame(components)
            row = base_political_science_rescue_row(
                point_id="wood_hoy_pryke_china_aid_attitudes_nz_median",
                source_family="Wood Hoy Pryke China-aid attitudes preregistered survey experiment",
                source_label="China-aid attitudes survey experiment",
                citation_key="woodHoyPrykeChinaAidDataverse",
                row_unit="paper_median_of_preregistered_binary_aid_attitude_outcomes",
                row_label="China aid vignette median effect on New Zealand aid-policy attitudes",
                d_value=float(component_df["D"].median()),
                n_value=float(component_df["N"].median()),
                journal="Journal of Experimental Political Science",
                source_file=(
                    f"{CHINA_AID_ATTITUDES_ZIP.relative_to(ROOT)}; 2 NZ data JEPS FINAL.dta; "
                    "AEA RCT Registry trial 5055 primary outcomes; Chinn conversion from raw vignette/control event counts"
                ),
                source_row_number=11,
            )
            plot_rows.append(row)
            audit_rows.extend(components)
            audit_rows.append({**row, "source": "china_aid_attitudes", "append_to_plot": True})
        except Exception as exc:
            audit_rows.append(
                {
                    "source": "china_aid_attitudes",
                    "append_to_plot": False,
                    "blocker": f"failed to parse {CHINA_AID_ATTITUDES_ZIP.relative_to(ROOT)}: {exc}",
                }
            )

    if SENEGAL_ACCOUNTABILITY_ZIP.exists():
        try:
            with zipfile.ZipFile(SENEGAL_ACCOUNTABILITY_ZIP) as archive:
                with archive.open("Panel_Survey.dta") as handle:
                    senegal = pd.read_stata(io.BytesIO(handle.read()))
            treatment_values = numeric_series(senegal["T_any_perf"])
            control_values = senegal["treatment_group"].astype(str)
            components = []
            primary_outcomes = [
                ("mp_good_post", "incumbent_performance_rating"),
                ("mp_good_compare_post", "incumbent_performance_comparison"),
                ("fut_perf_inc_post", "future_incumbent_performance_expectation"),
                ("vote_inc_post", "would_vote_for_incumbent"),
                ("ICW_incumbent_support_post", "incumbent_support_index"),
                ("want_inc_visit_post", "wants_incumbent_visit"),
                ("want_inc_express_post", "wants_to_express_view_to_incumbent"),
                ("ICW_behavior_post", "behavior_index"),
            ]
            for outcome, label in primary_outcomes:
                outcome_values = numeric_series(senegal[outcome])
                treatment_mask = treatment_values.eq(1) & outcome_values.notna()
                control_mask = control_values.eq("Control") & outcome_values.notna()
                unique_values = set(pd.unique(outcome_values.dropna()))
                if unique_values.issubset({0, 1, 0.0, 1.0}):
                    component_d = chinn_d_from_event_counts(
                        float(outcome_values.loc[treatment_mask].sum()),
                        int(treatment_mask.sum()),
                        float(outcome_values.loc[control_mask].sum()),
                        int(control_mask.sum()),
                    )
                    conversion = "chinn_binary_event_counts"
                else:
                    control_sd = float(outcome_values.loc[control_mask].std(ddof=1))
                    component_d = (
                        float(outcome_values.loc[treatment_mask].mean() - outcome_values.loc[control_mask].mean())
                        / control_sd
                    )
                    conversion = "mean_difference_over_control_sd"
                components.append(
                    {
                        "source": "senegal_learning_accountability",
                        "component": label,
                        "D_signed": component_d,
                        "D": abs(component_d),
                        "N": int(treatment_mask.sum() + control_mask.sum()),
                        "treatment_n": int(treatment_mask.sum()),
                        "control_n": int(control_mask.sum()),
                        "treatment_mean": float(outcome_values.loc[treatment_mask].mean()),
                        "control_mean": float(outcome_values.loc[control_mask].mean()),
                        "conversion": conversion,
                        "append_to_plot": False,
                    }
                )
            component_df = pd.DataFrame(components)
            row = base_political_science_rescue_row(
                point_id="senegal_learning_accountability_performance_info_median",
                source_family="Senegal learning-accountability preregistered information field experiment",
                source_label="Senegal accountability field experiment",
                citation_key="senegalLearningAccountabilityDataverse",
                row_unit="paper_median_of_table3_performance_information_outcomes",
                row_label="Senegal learning accountability median performance-information effect",
                d_value=float(component_df["D"].median()),
                n_value=float(component_df["N"].median()),
                journal="American Journal of Political Science",
                source_file=(
                    f"{SENEGAL_ACCOUNTABILITY_ZIP.relative_to(ROOT)}; Panel_Survey.dta; Analysis code.do Table 3; "
                    "AEA RCT Registry trial 2324; any-performance-information treatment versus control raw reconstruction"
                ),
                source_row_number=13,
            )
            plot_rows.append(row)
            audit_rows.extend(components)
            audit_rows.append({**row, "source": "senegal_learning_accountability", "append_to_plot": True})
        except Exception as exc:
            audit_rows.append(
                {
                    "source": "senegal_learning_accountability",
                    "append_to_plot": False,
                    "blocker": f"failed to parse {SENEGAL_ACCOUNTABILITY_ZIP.relative_to(ROOT)}: {exc}",
                }
            )

    if PUBLIC_SERVICE_JOB_ZIP.exists():
        try:
            import pyreadr

            with tempfile.TemporaryDirectory() as tmpdir:
                with zipfile.ZipFile(PUBLIC_SERVICE_JOB_ZIP) as archive:
                    archive.extract("P4P_Clean.rda", tmpdir)
                conjoint = pyreadr.read_r(str(Path(tmpdir) / "P4P_Clean.rda"))["P4P_Clean"]
            conjoint = conjoint.copy()
            binary_recodes = {
                "Total pay binary": (
                    "Total pay",
                    "Slightly below average",
                    "About average and Slightly above average",
                ),
                "Current community involvement binary": (
                    "Current community involvement",
                    "Rare participation",
                    "Moderate and Frequent participation",
                ),
                "Community income binary": ("Community income", "Low income", "Average and High income"),
                "Community demographics binary": ("Community demographics", "Mostly white", "Non-White"),
                "Overtime work binary": ("Overtime work", "Never required", "Occasionally and Frequently required"),
                "Key job task binary": (
                    "Key job task",
                    "Analysis identifying community needs",
                    "Interaction with community and organizational members",
                ),
            }
            for new_col, (source_col, reference, non_reference) in binary_recodes.items():
                if new_col not in conjoint.columns:
                    conjoint[new_col] = np.where(
                        conjoint[source_col].astype(str).eq(reference), reference, non_reference
                    )
            attributes = [
                ("Total pay binary", "About average and Slightly above average", "Slightly below average"),
                ("Performance bonuses binary", "Yes (bonuses)", "No (fixed salary)"),
                ("Goal based evaluation", "Yes (goal based)", "No (supervisor based)"),
                (
                    "Current community involvement binary",
                    "Moderate and Frequent participation",
                    "Rare participation",
                ),
                ("Community income binary", "Average and High income", "Low income"),
                ("Community demographics binary", "Non-White", "Mostly white"),
                ("Overtime work binary", "Occasionally and Frequently required", "Never required"),
                (
                    "Key job task binary",
                    "Interaction with community and organizational members",
                    "Analysis identifying community needs",
                ),
            ]
            choice_values = numeric_series(conjoint["Chosen_Job"])
            respondent_n = int(pd.Series(conjoint["ID"]).nunique())
            components = []
            for attribute, treatment_level, reference_level in attributes:
                attribute_values = conjoint[attribute].astype(str)
                treatment_mask = attribute_values.eq(treatment_level) & choice_values.notna()
                control_mask = attribute_values.eq(reference_level) & choice_values.notna()
                component_d = chinn_d_from_event_counts(
                    float(choice_values.loc[treatment_mask].sum()),
                    int(treatment_mask.sum()),
                    float(choice_values.loc[control_mask].sum()),
                    int(control_mask.sum()),
                )
                components.append(
                    {
                        "source": "public_service_job_attributes",
                        "component": attribute,
                        "D_signed": component_d,
                        "D": abs(component_d),
                        "N": respondent_n,
                        "profile_rows": int(treatment_mask.sum() + control_mask.sum()),
                        "treatment_profile_n": int(treatment_mask.sum()),
                        "control_profile_n": int(control_mask.sum()),
                        "treatment_mean": float(choice_values.loc[treatment_mask].mean()),
                        "control_mean": float(choice_values.loc[control_mask].mean()),
                        "conversion": "chinn_profile_event_counts_with_respondent_n",
                        "append_to_plot": False,
                    }
                )
            component_df = pd.DataFrame(components)
            row = base_political_science_rescue_row(
                point_id="public_service_job_attributes_choice_median",
                source_family="Public-service job-attributes preregistered conjoint experiment",
                source_label="Public-service job-attributes experiment",
                citation_key="publicServiceJobAttributesDataverse",
                row_unit="paper_median_of_preregistered_binary_job_choice_attribute_effects",
                row_label="Public-service job-attribute median effect on job choice",
                d_value=float(component_df["D"].median()),
                n_value=float(respondent_n),
                journal="Public Administration",
                source_file=(
                    f"{PUBLIC_SERVICE_JOB_ZIP.relative_to(ROOT)}; P4P_Clean.rda; P4P_Analysis2.R baseline AMCE; "
                    "AEA RCT Registry trial 7666; Chinn conversion from randomized profile-level choice event counts with respondent N"
                ),
                source_row_number=17,
            )
            plot_rows.append(row)
            audit_rows.extend(components)
            audit_rows.append({**row, "source": "public_service_job_attributes", "append_to_plot": True})
        except Exception as exc:
            audit_rows.append(
                {
                    "source": "public_service_job_attributes",
                    "append_to_plot": False,
                    "blocker": f"failed to parse {PUBLIC_SERVICE_JOB_ZIP.relative_to(ROOT)}: {exc}",
                }
            )

    if BANGLADESH_ELECTION_ZIP.exists():
        try:
            with zipfile.ZipFile(BANGLADESH_ELECTION_ZIP) as archive:
                with archive.open("Data/Election_project_data_full_sample.dta") as handle:
                    bangladesh = pd.read_stata(io.BytesIO(handle.read()), convert_categoricals=False)
            bangladesh = bangladesh.copy()
            bangladesh["dummy_al"] = numeric_series(bangladesh["Status_code"]).eq(1)
            bangladesh["dummy_bnp"] = numeric_series(bangladesh["Status_code"]).eq(2)
            bangladesh["legit"] = (
                numeric_series(bangladesh["treatAL"]).eq(1) | numeric_series(bangladesh["treatBNP"]).eq(1)
            )
            bangladesh["policy"] = (
                numeric_series(bangladesh["treatAL"]).eq(2) | numeric_series(bangladesh["treatBNP"]).eq(2)
            )
            bangladesh["control"] = ~(bangladesh["legit"] | bangladesh["policy"])
            panel_mask = numeric_series(bangladesh["Pre_survey1"]).eq(1) & numeric_series(
                bangladesh["Post_survey1"]
            ).eq(1)
            bangladesh = bangladesh.loc[panel_mask].copy()
            bangladesh["vote1"] = numeric_series(bangladesh["r5_01"])
            bangladesh["vote2"] = numeric_series(bangladesh["r5_02"])
            bangladesh["ink1"] = numeric_series(bangladesh["r6_01"])
            bangladesh["ink2"] = numeric_series(bangladesh["r6_02"])
            components = []
            for village_type, village_mask_col in [
                ("AL_government_villages", "dummy_al"),
                ("BNP_opposition_villages", "dummy_bnp"),
            ]:
                for treatment_arm in ["policy", "legit"]:
                    for outcome, label in [
                        ("ink1", "respondent_ink_mark"),
                        ("ink2", "spouse_ink_mark"),
                        ("vote1", "respondent_self_reported_voting"),
                        ("vote2", "spouse_self_reported_voting"),
                    ]:
                        outcome_values = numeric_series(bangladesh[outcome])
                        base_mask = bangladesh[village_mask_col].eq(True) & outcome_values.notna()
                        treatment_mask = base_mask & bangladesh[treatment_arm].eq(True)
                        control_mask = base_mask & bangladesh["control"].eq(True)
                        component_d = chinn_d_from_event_counts(
                            float(outcome_values.loc[treatment_mask].sum()),
                            int(treatment_mask.sum()),
                            float(outcome_values.loc[control_mask].sum()),
                            int(control_mask.sum()),
                        )
                        components.append(
                            {
                                "source": "bangladesh_election_information",
                                "component": f"{village_type}:{treatment_arm}:{label}",
                                "D_signed": component_d,
                                "D": abs(component_d),
                                "N": int(treatment_mask.sum() + control_mask.sum()),
                                "treatment_n": int(treatment_mask.sum()),
                                "control_n": int(control_mask.sum()),
                                "treatment_mean": float(outcome_values.loc[treatment_mask].mean()),
                                "control_mean": float(outcome_values.loc[control_mask].mean()),
                                "conversion": "chinn_binary_event_counts",
                                "append_to_plot": False,
                            }
                        )
            component_df = pd.DataFrame(components)
            row = base_political_science_rescue_row(
                point_id="bangladesh_election_information_turnout_vote_median",
                source_family="Bangladesh authoritarian-election information-campaign preregistered field experiment",
                source_label="Bangladesh election information field experiment",
                citation_key="bangladeshElectionZenodo",
                row_unit="paper_median_of_table2_turnout_vote_outcomes",
                row_label="Bangladesh information campaign median turnout/vote effect",
                d_value=float(component_df["D"].median()),
                n_value=float(component_df["N"].median()),
                journal="Economic Journal",
                source_file=(
                    f"{BANGLADESH_ELECTION_ZIP.relative_to(ROOT)}; Data/Election_project_data_full_sample.dta; "
                    "Main_figures_and_tables.do Table 2; AEA RCT Registry trial 3509; raw Policy/Legitimacy versus control "
                    "event-count reconstruction for ink-mark and self-reported voting outcomes"
                ),
                source_row_number=14,
            )
            plot_rows.append(row)
            audit_rows.extend(components)
            audit_rows.append({**row, "source": "bangladesh_election_information", "append_to_plot": True})
        except Exception as exc:
            audit_rows.append(
                {
                    "source": "bangladesh_election_information",
                    "append_to_plot": False,
                    "blocker": f"failed to parse {BANGLADESH_ELECTION_ZIP.relative_to(ROOT)}: {exc}",
                }
            )

    if POLITICAL_ACTIVISTS_FREERIDING_ZIP.exists():
        try:
            with zipfile.ZipFile(POLITICAL_ACTIVISTS_FREERIDING_ZIP) as archive:
                with archive.open("3 replication package/Data/peers_freeriding_final.dta") as handle:
                    freeriding = pd.read_stata(io.BytesIO(handle.read()))
            treatment_values = freeriding["treatment"].astype(str)
            components = []
            primary_outcomes = [
                ("canvassing_yes", "self_reported_intends_any_canvassing"),
                ("days", "self_reported_intended_canvassing_days"),
                ("canvass_any_main_unres", "app_any_canvassing"),
                ("days_unres_main", "app_canvassing_days"),
                ("doors_unres_main_wins", "app_doors_knocked_winsorized"),
            ]
            for outcome, label in primary_outcomes:
                outcome_values = numeric_series(freeriding[outcome])
                treatment_mask = treatment_values.eq("Treatment group") & outcome_values.notna()
                control_mask = treatment_values.eq("Control group") & outcome_values.notna()
                unique_values = set(pd.unique(outcome_values.dropna()))
                if unique_values.issubset({0, 1, 0.0, 1.0}):
                    component_d = chinn_d_from_event_counts(
                        float(outcome_values.loc[treatment_mask].sum()),
                        int(treatment_mask.sum()),
                        float(outcome_values.loc[control_mask].sum()),
                        int(control_mask.sum()),
                    )
                    conversion = "chinn_binary_event_counts"
                else:
                    control_sd = float(outcome_values.loc[control_mask].std(ddof=1))
                    component_d = (
                        float(outcome_values.loc[treatment_mask].mean() - outcome_values.loc[control_mask].mean())
                        / control_sd
                    )
                    conversion = "mean_difference_over_control_sd"
                components.append(
                    {
                        "source": "political_activists_freeriding",
                        "component": label,
                        "D_signed": component_d,
                        "D": abs(component_d),
                        "N": int(treatment_mask.sum() + control_mask.sum()),
                        "treatment_n": int(treatment_mask.sum()),
                        "control_n": int(control_mask.sum()),
                        "treatment_mean": float(outcome_values.loc[treatment_mask].mean()),
                        "control_mean": float(outcome_values.loc[control_mask].mean()),
                        "conversion": conversion,
                        "append_to_plot": False,
                    }
                )
            component_df = pd.DataFrame(components)
            row = base_political_science_rescue_row(
                point_id="political_activists_freeriding_canvassing_median",
                source_family="Political Activists as Free-Riders preregistered canvassing field experiment",
                source_label="Political activists free-riding experiment",
                citation_key="politicalActivistsFreeridingZenodo",
                row_unit="paper_median_of_preregistered_canvassing_intention_and_behavior_outcomes",
                row_label="Political activists free-riding median canvassing effect",
                d_value=float(component_df["D"].median()),
                n_value=float(component_df["N"].median()),
                journal="Economic Journal",
                source_file=(
                    f"{POLITICAL_ACTIVISTS_FREERIDING_ZIP.relative_to(ROOT)}; "
                    "3 replication package/Data/peers_freeriding_final.dta; Experimental_design.pdf; "
                    "Tab1_main_result.do; preregistered canvassing-intention and app-observed behavior outcomes"
                ),
                source_row_number=15,
            )
            plot_rows.append(row)
            audit_rows.extend(components)
            audit_rows.append({**row, "source": "political_activists_freeriding", "append_to_plot": True})
        except Exception as exc:
            audit_rows.append(
                {
                    "source": "political_activists_freeriding",
                    "append_to_plot": False,
                    "blocker": (
                        f"failed to parse {POLITICAL_ACTIVISTS_FREERIDING_ZIP.relative_to(ROOT)}: {exc}"
                    ),
                }
            )

    if POLICING_PATRIARCHY_CCTV.exists() and POLICING_PATRIARCHY_TABLE2.exists():
        try:
            policing = pd.read_csv(POLICING_PATRIARCHY_CCTV, sep="\t", low_memory=False)
            control_mask = numeric_series(policing["treatment"]).eq(0)
            outcome_sds = {
                "eavg_women": float(numeric_series(policing.loc[control_mask, "eavg_women"]).std(ddof=1)),
                "eavg_wprop": float(numeric_series(policing.loc[control_mask, "eavg_wprop"]).std(ddof=1)),
            }
            table2_components = [
                ("combined_whd_female_visitors_count", "eavg_women", -0.590, 1832),
                ("combined_whd_female_visitors_share", "eavg_wprop", 0.005, 1831),
                ("regular_whd_female_visitors_count", "eavg_women", -0.811, 1832),
                ("regular_whd_female_visitors_share", "eavg_wprop", 0.009, 1831),
                ("woman_run_whd_female_visitors_count", "eavg_women", -0.402, 1832),
                ("woman_run_whd_female_visitors_share", "eavg_wprop", 0.001, 1831),
            ]
            components = []
            for label, outcome, coefficient, n_value in table2_components:
                component_d = coefficient / outcome_sds[outcome]
                components.append(
                    {
                        "source": "policing_patriarchy",
                        "component": label,
                        "D_signed": component_d,
                        "D": abs(component_d),
                        "N": n_value,
                        "native_coefficient": coefficient,
                        "control_sd": outcome_sds[outcome],
                        "conversion": "table2_adjusted_coefficient_over_control_sd",
                        "append_to_plot": False,
                    }
                )
            component_df = pd.DataFrame(components)
            row = base_political_science_rescue_row(
                point_id="policing_patriarchy_women_help_desks_cctv_median",
                source_family="Policing in patriarchy Women Help Desks preregistered field experiment",
                source_label="Policing in patriarchy field experiment",
                citation_key="policingPatriarchyDataverse",
                row_unit="paper_median_of_table2_primary_cctv_outcomes",
                row_label="Women Help Desks median effect on female police-station visitors",
                d_value=float(component_df["D"].median()),
                n_value=float(component_df["N"].median()),
                journal="Harvard Dataverse replication package",
                source_file=(
                    f"{POLICING_PATRIARCHY_TABLE2.relative_to(ROOT)}; "
                    f"{POLICING_PATRIARCHY_CCTV.relative_to(ROOT)}; AEA RCT Registry trial 3357; "
                    "Table 2 adjusted CCTV coefficients divided by control-group outcome SDs from the downloaded analysis data"
                ),
                source_row_number=16,
            )
            plot_rows.append(row)
            audit_rows.extend(components)
            audit_rows.append({**row, "source": "policing_patriarchy", "append_to_plot": True})
        except Exception as exc:
            audit_rows.append(
                {
                    "source": "policing_patriarchy",
                    "append_to_plot": False,
                    "blocker": f"failed to parse {POLICING_PATRIARCHY_DIR.relative_to(ROOT)}: {exc}",
                }
            )

    if VOTE_BUYING_RADIO_ZIP.exists():
        try:
            with zipfile.ZipFile(VOTE_BUYING_RADIO_ZIP) as archive:
                with archive.open("ReplicationZip/Table 2/table2_data.csv") as handle:
                    vote_buying = pd.read_csv(handle)
            treatment_values = numeric_series(vote_buying["treat"])
            components = []
            for outcome, label in [
                ("voteshare_crime_2014", "vote_share_candidates_accused_of_crimes"),
                ("voteshare_rich_2014", "vote_share_wealthiest_candidates"),
                ("voteshare_events_2014", "vote_share_candidates_with_campaign_events"),
                ("voteshare_volunteers_2014", "vote_share_candidates_using_volunteers"),
                ("voteshare_spend_2014", "vote_share_high_spending_candidates"),
                ("voteshare_win_2014", "vote_share_winning_candidates"),
            ]:
                outcome_values = numeric_series(vote_buying[outcome])
                treatment_mask = treatment_values.eq(1) & outcome_values.notna()
                control_mask = treatment_values.eq(0) & outcome_values.notna()
                control_sd = float(outcome_values.loc[control_mask].std(ddof=1))
                component_d = (
                    float(outcome_values.loc[treatment_mask].mean() - outcome_values.loc[control_mask].mean())
                    / control_sd
                )
                components.append(
                    {
                        "source": "vote_buying_radio",
                        "component": label,
                        "D_signed": component_d,
                        "D": abs(component_d),
                        "N": int(treatment_mask.sum() + control_mask.sum()),
                        "treatment_n": int(treatment_mask.sum()),
                        "control_n": int(control_mask.sum()),
                        "treatment_mean": float(outcome_values.loc[treatment_mask].mean()),
                        "control_mean": float(outcome_values.loc[control_mask].mean()),
                        "control_sd": control_sd,
                        "conversion": "assembly-constituency_vote_share_mean_difference_over_control_sd",
                        "append_to_plot": False,
                    }
                )
            component_df = pd.DataFrame(components)
            row = base_political_science_rescue_row(
                point_id="india_vote_buying_radio_candidate_vote_share_median",
                source_family="India anti-vote-buying radio-campaign preregistered field experiment",
                source_label="India vote-buying radio campaign",
                citation_key="voteBuyingRadioDataverse",
                row_unit="paper_median_of_table2_candidate_vote_share_outcomes",
                row_label="India anti-vote-buying radio campaign median candidate-vote-share effect",
                d_value=float(component_df["D"].median()),
                n_value=float(component_df["N"].median()),
                journal="American Economic Review",
                source_file=(
                    f"{VOTE_BUYING_RADIO_ZIP.relative_to(ROOT)}; ReplicationZip/Table 2/table2_data.csv; "
                    "AEA RCT Registry trial 377; Table 2 candidate-characteristic vote-share outcomes reconstructed "
                    "as treatment-control mean differences over control-group SDs"
                ),
                source_row_number=18,
            )
            plot_rows.append(row)
            audit_rows.extend(components)
            audit_rows.append({**row, "source": "vote_buying_radio", "append_to_plot": True})
        except Exception as exc:
            audit_rows.append(
                {
                    "source": "vote_buying_radio",
                    "append_to_plot": False,
                    "blocker": f"failed to parse {VOTE_BUYING_RADIO_ZIP.relative_to(ROOT)}: {exc}",
                }
            )

    if INTERETHNIC_CONTACT_ZIP.exists():
        try:
            with zipfile.ZipFile(INTERETHNIC_CONTACT_ZIP) as archive:
                with archive.open("Replication_ajs.dta") as handle:
                    interethnic = pd.read_stata(io.BytesIO(handle.read()), convert_categoricals=False)
            components = []
            for outcome, label in [
                ("roma_friend", "has_roma_friend"),
                ("lend", "would_lend_to_classmate"),
            ]:
                outcome_values = numeric_series(interethnic[outcome])
                base_mask = numeric_series(interethnic["roma"]).eq(0) & outcome_values.notna()
                treatment_mask = base_mask & numeric_series(interethnic["dm_roma"]).eq(1)
                control_mask = base_mask & numeric_series(interethnic["dm_roma"]).eq(0)
                component_d = chinn_d_from_event_counts(
                    float(outcome_values.loc[treatment_mask].sum()),
                    int(treatment_mask.sum()),
                    float(outcome_values.loc[control_mask].sum()),
                    int(control_mask.sum()),
                )
                components.append(
                    {
                        "source": "interethnic_contact",
                        "component": label,
                        "D_signed": component_d,
                        "D": abs(component_d),
                        "N": int(treatment_mask.sum() + control_mask.sum()),
                        "treatment_n": int(treatment_mask.sum()),
                        "control_n": int(control_mask.sum()),
                        "treatment_mean": float(outcome_values.loc[treatment_mask].mean()),
                        "control_mean": float(outcome_values.loc[control_mask].mean()),
                        "conversion": "chinn_binary_event_counts_non_roma_students",
                        "append_to_plot": False,
                    }
                )
            component_df = pd.DataFrame(components)
            row = base_political_science_rescue_row(
                point_id="interethnic_contact_roma_deskmate_friend_lend_median",
                source_family="Kotsadam Keller Elwert interethnic-contact preregistered field experiment",
                source_label="Roma deskmate interethnic contact",
                citation_key="interethnicContactDataverse",
                row_unit="paper_median_of_main_binary_interethnic_relation_outcomes",
                row_label="Roma deskmate median effect on friendship/lending outcomes",
                d_value=float(component_df["D"].median()),
                n_value=float(component_df["N"].median()),
                journal="American Journal of Sociology",
                source_file=(
                    f"{INTERETHNIC_CONTACT_ZIP.relative_to(ROOT)}; Replication_ajs.dta; AEA RCT Registry trial 2795; "
                    "Table 3 main outcomes for non-Roma students reconstructed from raw Roma-deskmate/control event counts"
                ),
                source_row_number=19,
            )
            plot_rows.append(row)
            audit_rows.extend(components)
            audit_rows.append({**row, "source": "interethnic_contact", "append_to_plot": True})
        except Exception as exc:
            audit_rows.append(
                {
                    "source": "interethnic_contact",
                    "append_to_plot": False,
                    "blocker": f"failed to parse {INTERETHNIC_CONTACT_ZIP.relative_to(ROOT)}: {exc}",
                }
            )

    if IMMIGRATION_BELIEFS_ZIP.exists():
        try:
            with zipfile.ZipFile(IMMIGRATION_BELIEFS_ZIP) as archive:
                with archive.open("1_clean_data.dta") as handle:
                    immigration = pd.read_stata(io.BytesIO(handle.read()), convert_categoricals=False)
            sample_mask = numeric_series(immigration["sample"]).eq(1)
            components = []
            for arm, outcome, label in [
                (5, "ln1_prob_index_anti", "anti_immigration_message_trump_source"),
                (6, "ln1_prob_index_anti", "anti_immigration_message_obama_source"),
                (7, "ln1_prob_index_anti", "anti_immigration_message_actor_trump_source"),
                (8, "ln1_prob_index_anti", "anti_immigration_message_actor_obama_source"),
                (1, "ln1_prob_index_pro", "pro_immigration_message_trump_source"),
                (2, "ln1_prob_index_pro", "pro_immigration_message_obama_source"),
                (3, "ln1_prob_index_pro", "pro_immigration_message_actor_trump_source"),
                (4, "ln1_prob_index_pro", "pro_immigration_message_actor_obama_source"),
            ]:
                outcome_values = numeric_series(immigration[outcome])
                treatment_mask = sample_mask & numeric_series(immigration["treatment"]).eq(arm) & outcome_values.notna()
                control_mask = sample_mask & numeric_series(immigration["treatment"]).eq(0) & outcome_values.notna()
                control_sd = float(outcome_values.loc[control_mask].std(ddof=1))
                component_d = (
                    float(outcome_values.loc[treatment_mask].mean() - outcome_values.loc[control_mask].mean())
                    / control_sd
                )
                components.append(
                    {
                        "source": "immigration_beliefs",
                        "component": label,
                        "D_signed": component_d,
                        "D": abs(component_d),
                        "N": int(treatment_mask.sum() + control_mask.sum()),
                        "treatment_n": int(treatment_mask.sum()),
                        "control_n": int(control_mask.sum()),
                        "treatment_mean": float(outcome_values.loc[treatment_mask].mean()),
                        "control_mean": float(outcome_values.loc[control_mask].mean()),
                        "control_sd": control_sd,
                        "conversion": "message_arm_mean_difference_over_control_sd",
                        "append_to_plot": False,
                    }
                )
            component_df = pd.DataFrame(components)
            row = base_political_science_rescue_row(
                point_id="immigration_message_messenger_belief_index_median",
                source_family="Immigration message-or-messenger preregistered survey experiment",
                source_label="Immigration message/messenger experiment",
                citation_key="immigrationBeliefsDataverse",
                row_unit="paper_median_of_preregistered_message_source_belief_index_outcomes",
                row_label="Immigration message/messenger median effect on belief indices",
                d_value=float(component_df["D"].median()),
                n_value=float(component_df["N"].median()),
                journal="Harvard Dataverse replication package",
                source_file=(
                    f"{IMMIGRATION_BELIEFS_ZIP.relative_to(ROOT)}; 1_clean_data.dta; AEA RCT Registry trial 6552; "
                    "message-source arms versus control on logged immigration-belief indices, divided by control SD"
                ),
                source_row_number=20,
            )
            plot_rows.append(row)
            audit_rows.extend(components)
            audit_rows.append({**row, "source": "immigration_beliefs", "append_to_plot": True})
        except Exception as exc:
            audit_rows.append(
                {
                    "source": "immigration_beliefs",
                    "append_to_plot": False,
                    "blocker": f"failed to parse {IMMIGRATION_BELIEFS_ZIP.relative_to(ROOT)}: {exc}",
                }
            )

    if COVID_TOGETHERNESS_ZIP.exists():
        try:
            with zipfile.ZipFile(COVID_TOGETHERNESS_ZIP) as archive:
                with archive.open("covid19perceptions.dta") as handle:
                    covid = pd.read_stata(io.BytesIO(handle.read()), convert_categoricals=False)
            if "ResponseId" in covid.columns:
                covid = covid[covid["ResponseId"].astype(str).ne("R_1FJTuRyeH7msWDG")].copy()
            maxweeks_cols = [c for c in covid.columns if c.startswith("maxweeks") and c != "maxweeks"]
            covid["maxweeks_constructed"] = covid[maxweeks_cols].apply(pd.to_numeric, errors="coerce").mean(axis=1)
            covid.loc[covid["maxweeks_constructed"].gt(104), "maxweeks_constructed"] = 104
            covid["socdist_constructed"] = (
                (10 - numeric_series(covid["socdist1_1"]))
                + numeric_series(covid["socdist2_1"])
                + (10 - numeric_series(covid["socdist3_1"]))
                + numeric_series(covid["socdist4_1"])
                + numeric_series(covid["socdist5_1"])
            )
            arm_values = covid["arm"].astype(str)
            components = []
            for outcome, label_prefix in [
                ("maxweeks_constructed", "weeks_willing_to_isolate"),
                ("socdist_constructed", "intended_social_distancing_index"),
            ]:
                outcome_values = numeric_series(covid[outcome])
                control_mask = arm_values.eq("control") & outcome_values.notna()
                control_sd = float(outcome_values.loc[control_mask].std(ddof=1))
                for arm in ["treatment1", "treatment2", "treatment3", "treatment4"]:
                    treatment_mask = arm_values.eq(arm) & outcome_values.notna()
                    component_d = (
                        float(outcome_values.loc[treatment_mask].mean() - outcome_values.loc[control_mask].mean())
                        / control_sd
                    )
                    components.append(
                        {
                            "source": "covid_togetherness",
                            "component": f"{label_prefix}:{arm}",
                            "D_signed": component_d,
                            "D": abs(component_d),
                            "N": int(treatment_mask.sum() + control_mask.sum()),
                            "treatment_n": int(treatment_mask.sum()),
                            "control_n": int(control_mask.sum()),
                            "treatment_mean": float(outcome_values.loc[treatment_mask].mean()),
                            "control_mean": float(outcome_values.loc[control_mask].mean()),
                            "control_sd": control_sd,
                            "conversion": "survey_treatment_arm_mean_difference_over_control_sd",
                            "append_to_plot": False,
                        }
                    )
            component_df = pd.DataFrame(components)
            row = base_political_science_rescue_row(
                point_id="covid_togetherness_social_distancing_cue_median",
                source_family="Favero Pedersen COVID information-cue preregistered survey experiment",
                source_label="COVID togetherness information-cue experiment",
                citation_key="covidTogethernessDataverse",
                row_unit="paper_median_of_social_distancing_primary_outcomes",
                row_label="COVID togetherness cue median effect on distancing outcomes",
                d_value=float(component_df["D"].median()),
                n_value=float(component_df["N"].median()),
                journal="Journal of Behavioral Public Administration",
                source_file=(
                    f"{COVID_TOGETHERNESS_ZIP.relative_to(ROOT)}; covid19perceptions.dta; AEA RCT Registry trial 5611; "
                    "analysis.do primary social-distancing outcomes reconstructed as each treatment arm versus control"
                ),
                source_row_number=21,
            )
            plot_rows.append(row)
            audit_rows.extend(components)
            audit_rows.append({**row, "source": "covid_togetherness", "append_to_plot": True})
        except Exception as exc:
            audit_rows.append(
                {
                    "source": "covid_togetherness",
                    "append_to_plot": False,
                    "blocker": f"failed to parse {COVID_TOGETHERNESS_ZIP.relative_to(ROOT)}: {exc}",
                }
            )

    if MEDICINE_THEFT_ZIP.exists():
        try:
            with zipfile.ZipFile(MEDICINE_THEFT_ZIP) as archive:
                with archive.open("sentinel_file_anonymized.csv") as handle:
                    medicine = pd.read_csv(handle)
            treatment_values = numeric_series(medicine["treatment"])
            components = []
            for outcome, label in [
                ("missed_delivery", "missed_delivery"),
                ("nottrace_any_sighting", "not_traced_at_any_sighting"),
            ]:
                outcome_values = numeric_series(medicine[outcome])
                treatment_mask = treatment_values.eq(1) & outcome_values.notna()
                control_mask = treatment_values.eq(0) & outcome_values.notna()
                component_d = chinn_d_from_event_counts(
                    float(outcome_values.loc[treatment_mask].sum()),
                    int(treatment_mask.sum()),
                    float(outcome_values.loc[control_mask].sum()),
                    int(control_mask.sum()),
                )
                components.append(
                    {
                        "source": "medicine_theft",
                        "component": label,
                        "D_signed": component_d,
                        "D": abs(component_d),
                        "N": int(treatment_mask.sum() + control_mask.sum()),
                        "treatment_n": int(treatment_mask.sum()),
                        "control_n": int(control_mask.sum()),
                        "treatment_mean": float(outcome_values.loc[treatment_mask].mean()),
                        "control_mean": float(outcome_values.loc[control_mask].mean()),
                        "conversion": "chinn_binary_event_counts",
                        "append_to_plot": False,
                    }
                )
            component_df = pd.DataFrame(components)
            row = base_political_science_rescue_row(
                point_id="medicine_theft_remote_tracking_detection_median",
                source_family="Medicine-theft remote-tracking preregistered governance field experiment",
                source_label="Medicine theft remote-tracking field experiment",
                citation_key="medicineTheftDataverse",
                row_unit="paper_median_of_delivery_trace_binary_outcomes",
                row_label="Medicine remote-tracking median effect on delivery trace outcomes",
                d_value=float(component_df["D"].median()),
                n_value=float(component_df["N"].median()),
                journal="Harvard Dataverse replication package",
                source_file=(
                    f"{MEDICINE_THEFT_ZIP.relative_to(ROOT)}; sentinel_file_anonymized.csv; "
                    "AEA RCT Registry trial 8989; binary delivery-trace outcomes reconstructed from raw event counts"
                ),
                source_row_number=22,
            )
            plot_rows.append(row)
            audit_rows.extend(components)
            audit_rows.append({**row, "source": "medicine_theft", "append_to_plot": True})
        except Exception as exc:
            audit_rows.append(
                {
                    "source": "medicine_theft",
                    "append_to_plot": False,
                    "blocker": f"failed to parse {MEDICINE_THEFT_ZIP.relative_to(ROOT)}: {exc}",
                }
            )

    if REFUGEE_DESTINATION_ZIP.exists():
        try:
            import pyreadr

            with tempfile.TemporaryDirectory() as tmpdir:
                with zipfile.ZipFile(REFUGEE_DESTINATION_ZIP) as archive:
                    archive.extract("PNAS_replication_package/Data/cj_clean.rds", tmpdir)
                conjoint = pyreadr.read_r(
                    str(Path(tmpdir) / "PNAS_replication_package" / "Data" / "cj_clean.rds")
                )[None]
            chosen_values = numeric_series(conjoint["chosen"])
            respondent_n = int(pd.Series(conjoint["responseid"]).nunique())
            attribute_contrasts = [
                ("location", "More than 500 km", "Less than 500 km"),
                ("family_or_friends", "There are family or friends", "No family or friends"),
                ("language", "Know national language", "No knowledge of national language"),
                ("find_job", "Easy to find", "Difficult to find"),
            ]
            components = []
            for attribute, treatment_level, control_level in attribute_contrasts:
                attribute_values = conjoint[attribute].astype(str)
                treatment_mask = attribute_values.eq(treatment_level) & chosen_values.notna()
                control_mask = attribute_values.eq(control_level) & chosen_values.notna()
                component_d = chinn_d_from_event_counts(
                    float(chosen_values.loc[treatment_mask].sum()),
                    int(treatment_mask.sum()),
                    float(chosen_values.loc[control_mask].sum()),
                    int(control_mask.sum()),
                )
                components.append(
                    {
                        "source": "refugee_destination_choice",
                        "component": attribute,
                        "D_signed": component_d,
                        "D": abs(component_d),
                        "N": respondent_n,
                        "profile_rows": int(treatment_mask.sum() + control_mask.sum()),
                        "treatment_profile_n": int(treatment_mask.sum()),
                        "control_profile_n": int(control_mask.sum()),
                        "treatment_mean": float(chosen_values.loc[treatment_mask].mean()),
                        "control_mean": float(chosen_values.loc[control_mask].mean()),
                        "conversion": "chinn_profile_event_counts_with_respondent_n",
                        "append_to_plot": False,
                    }
                )
            component_df = pd.DataFrame(components)
            row = base_political_science_rescue_row(
                point_id="ukrainian_refugee_destination_choice_conjoint_median",
                source_family="Ukrainian-refugee destination-choice preregistered conjoint experiment",
                source_label="Ukrainian refugee destination-choice conjoint",
                citation_key="refugeeDestinationZenodo",
                row_unit="paper_median_of_main_binary_destination_attribute_effects",
                row_label="Ukrainian refugee destination-choice median attribute effect",
                d_value=float(component_df["D"].median()),
                n_value=float(respondent_n),
                journal="PNAS",
                source_file=(
                    f"{REFUGEE_DESTINATION_ZIP.relative_to(ROOT)}; PNAS_replication_package/Data/cj_clean.rds; "
                    "AEA RCT Registry trial 1233; Figure 1 main conjoint attributes reconstructed from raw profile choices"
                ),
                source_row_number=23,
            )
            plot_rows.append(row)
            audit_rows.extend(components)
            audit_rows.append({**row, "source": "refugee_destination_choice", "append_to_plot": True})
        except Exception as exc:
            audit_rows.append(
                {
                    "source": "refugee_destination_choice",
                    "append_to_plot": False,
                    "blocker": f"failed to parse {REFUGEE_DESTINATION_ZIP.relative_to(ROOT)}: {exc}",
                }
            )

    if BARAZA_ANCOVA_RESULTS.exists():
        try:
            r_code = """
args <- commandArgs(trailingOnly=TRUE)
load(args[1])
index_outcomes <- c(7, 13, 21, 29, 30)
index_labels <- c("agriculture_index", "infrastructure_index", "health_index", "education_index", "overall_public_service_index")
contrast_labels <- c("subcounty_baraza", "information", "deliberation", "district_baraza_vs_control")
rows <- data.frame()
for (i in seq_along(index_outcomes)) {
  outcome_index <- index_outcomes[i]
  for (contrast_index in 1:4) {
    rows <- rbind(rows, data.frame(
      component=paste(index_labels[i], contrast_labels[contrast_index], sep=":"),
      D_signed=df_ancova[1, contrast_index, outcome_index],
      D=abs(df_ancova[1, contrast_index, outcome_index]),
      N=df_ancova[6, contrast_index, outcome_index],
      SE=df_ancova[2, contrast_index, outcome_index],
      p=df_ancova[3, contrast_index, outcome_index]
    ))
  }
}
write.csv(rows, stdout(), row.names=FALSE)
"""
            completed = subprocess.run(
                ["Rscript", "-e", r_code, str(BARAZA_ANCOVA_RESULTS)],
                check=True,
                capture_output=True,
                text=True,
            )
            component_df = pd.read_csv(io.StringIO(completed.stdout))
            components = []
            for _, component in component_df.iterrows():
                components.append(
                    {
                        "source": "baraza_public_service_delivery",
                        "component": safe_text(component["component"]),
                        "D_signed": float(component["D_signed"]),
                        "D": float(component["D"]),
                        "N": float(component["N"]),
                        "SE": float(component["SE"]),
                        "p": float(component["p"]),
                        "conversion": "precomputed_author_ancova_index_effect_in_sd_units",
                        "append_to_plot": False,
                    }
                )
            component_df = pd.DataFrame(components)
            row = base_political_science_rescue_row(
                point_id="baraza_public_service_delivery_index_median",
                source_family="Baraza public-service delivery preregistered community-monitoring field experiment",
                source_label="Baraza public-service delivery",
                citation_key="barazaGithub",
                row_unit="paper_median_of_preregistered_public_service_index_effects",
                row_label="Uganda Baraza median effect on public-service delivery indices",
                d_value=float(component_df["D"].median()),
                n_value=float(component_df["N"].median()),
                journal="GitHub replication package",
                source_file=(
                    f"{BARAZA_ANCOVA_RESULTS.relative_to(ROOT)}; analysis_report.R Figure impact_summary_ancova; "
                    "five preregistered sector/overall public-service indices and four planned intervention contrasts, "
                    "using author ANCOVA effects labeled in SD units"
                ),
                source_row_number=24,
            )
            plot_rows.append(row)
            audit_rows.extend(components)
            audit_rows.append({**row, "source": "baraza_public_service_delivery", "append_to_plot": True})
        except Exception as exc:
            audit_rows.append(
                {
                    "source": "baraza_public_service_delivery",
                    "append_to_plot": False,
                    "blocker": f"failed to parse {BARAZA_ANCOVA_RESULTS.relative_to(ROOT)}: {exc}",
                }
            )

    if DIRECT_AID_SURVEYS.exists():
        try:
            direct_aid = pd.read_stata(DIRECT_AID_SURVEYS, convert_categoricals=False)
            analysis_mask = (
                numeric_series(direct_aid["round"]).isin([1, 2])
                & numeric_series(direct_aid["t"]).ne(0)
                & direct_aid["treatment"].notna()
            )
            direct_aid = direct_aid.loc[analysis_mask].copy()
            treatment_values = numeric_series(direct_aid["treatment"])
            components = []
            for outcome in ["nutrition_index", "econ_index", "tax_index"]:
                outcome_values = numeric_series(direct_aid[outcome])
                treatment_mask = treatment_values.eq(1) & outcome_values.notna()
                control_mask = treatment_values.eq(0) & outcome_values.notna()
                control_sd = float(outcome_values.loc[control_mask].std(ddof=1))
                component_d = (
                    float(outcome_values.loc[treatment_mask].mean() - outcome_values.loc[control_mask].mean())
                    / control_sd
                    if control_sd > 0
                    else float("nan")
                )
                components.append(
                    {
                        "source": "direct_aid_afghan_women",
                        "component": outcome,
                        "D_signed": component_d,
                        "D": abs(component_d),
                        "N": int(treatment_mask.sum() + control_mask.sum()),
                        "treatment_n": int(treatment_mask.sum()),
                        "control_n": int(control_mask.sum()),
                        "treatment_mean": float(outcome_values.loc[treatment_mask].mean()),
                        "control_mean": float(outcome_values.loc[control_mask].mean()),
                        "control_sd": control_sd,
                        "conversion": "first_two_followup_rounds_index_mean_difference_over_control_sd",
                        "append_to_plot": False,
                    }
                )
            component_df = pd.DataFrame(components)
            row = base_political_science_rescue_row(
                point_id="direct_aid_afghan_women_index_median",
                source_family="Direct-aid humanitarian-governance preregistered field experiment",
                source_label="Direct Aid to Afghan Women",
                citation_key="directAidGithub",
                row_unit="paper_median_of_preregistered_food_security_economic_informal_tax_indices",
                row_label="Digital aid median effect on food-security, economic, and informal-tax indices",
                d_value=float(component_df["D"].median()),
                n_value=float(component_df["N"].median()),
                journal="GitHub replication package",
                source_file=(
                    f"{DIRECT_AID_SURVEYS.relative_to(ROOT)}; Table_2_A3.do and Table_3_A7.do; "
                    "AEA RCT Registry AEARCTR-0010189; first two follow-up rounds, source index outcomes "
                    "reconstructed as treatment-control mean differences over the control-group SD"
                ),
                source_row_number=25,
            )
            plot_rows.append(row)
            audit_rows.extend(components)
            audit_rows.append({**row, "source": "direct_aid_afghan_women", "append_to_plot": True})
        except Exception as exc:
            audit_rows.append(
                {
                    "source": "direct_aid_afghan_women",
                    "append_to_plot": False,
                    "blocker": f"failed to parse {DIRECT_AID_SURVEYS.relative_to(ROOT)}: {exc}",
                }
            )

    if BANGLADESH_WASH_ZIP.exists():
        try:
            def tex_row_numbers(tex: str, label: str) -> list[float]:
                for line in tex.splitlines():
                    if label in line:
                        return [float(value) for value in re.findall(r"-?\d+(?:\.\d+)?", line)]
                return []

            with zipfile.ZipFile(BANGLADESH_WASH_ZIP) as archive:
                table_a = archive.read("Replication_Folder_only/tables/table_analysis_A.tex").decode(
                    "utf-8", "replace"
                )
                table_b = archive.read("Replication_Folder_only/tables/table_analysis_B.tex").decode(
                    "utf-8", "replace"
                )
            table_a_effects = tex_row_numbers(table_a, "Treatment $\\times$ post")
            table_a_ns = tex_row_numbers(table_a, "N")
            table_b_effects = tex_row_numbers(table_b, "Treatment $\\times$ post")
            table_b_ns = tex_row_numbers(table_b, "N")
            components = []
            table_a_labels = [
                "headteacher_knowledge",
                "teacher_knowledge_male",
                "teacher_knowledge_female",
                "student_knowledge_male",
                "student_knowledge_female",
                "institutional_quality",
            ]
            for label, effect, n_value in zip(table_a_labels, table_a_effects, table_a_ns):
                components.append(
                    {
                        "source": "bangladesh_school_wash",
                        "component": f"table_a:{label}",
                        "D_signed": float(effect),
                        "D": abs(float(effect)),
                        "N": float(n_value),
                        "conversion": "published_table_treatment_x_post_standardized_index_effect",
                        "append_to_plot": False,
                    }
                )
            for idx, label in [(3, "wash_quality_male"), (4, "wash_quality_female")]:
                if idx < len(table_b_effects) and idx < len(table_b_ns):
                    components.append(
                        {
                            "source": "bangladesh_school_wash",
                            "component": f"table_b:{label}",
                            "D_signed": float(table_b_effects[idx]),
                            "D": abs(float(table_b_effects[idx])),
                            "N": float(table_b_ns[idx]),
                            "conversion": "published_table_treatment_x_post_wash_quality_index_effect",
                            "append_to_plot": False,
                        }
                    )
            component_df = pd.DataFrame(components)
            row = base_political_science_rescue_row(
                point_id="bangladesh_school_wash_transparency_index_median",
                source_family="Bangladesh school-WASH transparency preregistered field experiment",
                source_label="Bangladesh school WASH transparency",
                citation_key="bangladeshWashDataverse",
                row_unit="paper_median_of_preregistered_wash_knowledge_quality_index_effects",
                row_label="School WASH transparency median effect on knowledge and WASH-quality indices",
                d_value=float(component_df["D"].median()),
                n_value=float(component_df["N"].median()),
                journal="Journal of Development Economics",
                source_file=(
                    f"{BANGLADESH_WASH_ZIP.relative_to(ROOT)}; table_analysis_A.tex and table_analysis_B.tex; "
                    "AEA RCT Registry AEARCTR-0003111; published treatment-by-post effects for source-standardized "
                    "knowledge/institutional-quality and WASH-quality index outcomes"
                ),
                source_row_number=26,
            )
            plot_rows.append(row)
            audit_rows.extend(components)
            audit_rows.append({**row, "source": "bangladesh_school_wash", "append_to_plot": True})
        except Exception as exc:
            audit_rows.append(
                {
                    "source": "bangladesh_school_wash",
                    "append_to_plot": False,
                    "blocker": f"failed to parse {BANGLADESH_WASH_ZIP.relative_to(ROOT)}: {exc}",
                }
            )

    if COVID_EMPEROR_ZIP.exists():
        try:
            with zipfile.ZipFile(COVID_EMPEROR_ZIP) as archive:
                covid = pd.read_stata(
                    io.BytesIO(archive.read("replication/data/data_use_rep.dta")),
                    convert_categoricals=False,
                )
            controls = [
                "negshock",
                "wkend_0",
                "pref_saitama",
                "pref_chiba",
                "pref_tokyo",
                "pref_kanagawa",
                "pref_osaka",
                "pref_hyogo",
                "pref_fukuoka",
            ]
            treatment_terms = ["treat2_ab", "treat2_be", "treat4_ab", "treat4_be", "treat3_ab", "treat3_be"]
            components = []
            for outcome in ["wkend_post", "wkend_unnecout_post"]:
                columns = [outcome, "above_median", *treatment_terms, *controls, "treat1"]
                model = covid[columns].apply(pd.to_numeric, errors="coerce").dropna().copy()
                design = pd.DataFrame({"const": 1.0}, index=model.index)
                for column in ["above_median", *treatment_terms, *controls]:
                    design[column] = model[column].astype(float)
                coefficients = ols_coefficients(model[outcome].astype(float), design)
                for term in treatment_terms:
                    segment_value = 1 if term.endswith("_ab") else 0
                    control_mask = model["treat1"].eq(1) & model["above_median"].eq(segment_value)
                    control_sd = float(model.loc[control_mask, outcome].std(ddof=1))
                    if control_sd <= 0 or not math.isfinite(control_sd):
                        continue
                    component_d = float(coefficients[term]) / control_sd
                    components.append(
                        {
                            "source": "covid_emperor_social_norms",
                            "component": f"{outcome}:{term}",
                            "D_signed": component_d,
                            "D": abs(component_d),
                            "N": int(len(model)),
                            "coefficient_minutes": float(coefficients[term]),
                            "control_sd_minutes": control_sd,
                            "control_mean_minutes": float(model.loc[control_mask, outcome].mean()),
                            "conversion": "author_table_1_model_coefficient_divided_by_matching_omitted_group_sd",
                            "append_to_plot": False,
                        }
                    )
            component_df = pd.DataFrame(components)
            row = base_political_science_rescue_row(
                point_id="covid_emperor_social_norm_outing_median",
                source_family="COVID Emperor social-norm preregistered survey experiment",
                source_label="COVID Emperor social-norm experiment",
                citation_key="covidEmperorOsf",
                row_unit="paper_median_of_preregistered_outing_behavior_effects",
                row_label="COVID Emperor median effect on weekend outing and unnecessary-outing time",
                d_value=float(component_df["D"].median()),
                n_value=float(component_df["N"].median()),
                journal="OSF replication package",
                source_file=(
                    f"{COVID_EMPEROR_ZIP.relative_to(ROOT)}; replication/data/data_use_rep.dta; "
                    "make_tables_rep.do Tables A.7/1 model with baseline Group A; treatment-cell coefficients divided "
                    "by the matching omitted control-cell outcome SD reported by the source script"
                ),
                source_row_number=27,
            )
            plot_rows.append(row)
            audit_rows.extend(components)
            audit_rows.append({**row, "source": "covid_emperor_social_norms", "append_to_plot": True})
        except Exception as exc:
            audit_rows.append(
                {
                    "source": "covid_emperor_social_norms",
                    "append_to_plot": False,
                    "blocker": f"failed to parse {COVID_EMPEROR_ZIP.relative_to(ROOT)}: {exc}",
                }
            )

    if VACCINE_HESITANCY_ZIP.exists():
        try:
            with zipfile.ZipFile(VACCINE_HESITANCY_ZIP) as archive:
                csv_member = next(member for member in archive.namelist() if member.endswith(".csv"))
                vaccine = pd.read_csv(archive.open(csv_member), low_memory=False)
            vaccine["finished_rev"] = np.where(
                vaccine["finished"].notna(),
                pd.to_numeric(vaccine["finished"], errors="coerce").eq(0).astype(float),
                np.nan,
            )
            vaccine["survey_clock_dt"] = pd.to_datetime(
                vaccine["survey_clock"], format="%d%b%Y %H:%M:%S", errors="coerce"
            )
            vaccine = vaccine.sort_values(
                ["subject_id", "finished_rev", "survey_clock_dt"], na_position="last"
            ).copy()
            vaccine["dup_pid"] = vaccine.groupby("subject_id").cumcount() + 1
            subject_counts = vaccine.groupby("subject_id")["subject_id"].transform("size")
            vaccine.loc[subject_counts.eq(1), "dup_pid"] = 0
            vaccine = vaccine.loc[vaccine["dup_pid"].lt(2)].copy()
            vaccine = vaccine.sort_values("ipaddr_id", na_position="last").copy()
            vaccine["ipaddr_seq"] = vaccine.groupby("ipaddr_id").cumcount() + 1
            ip_counts = vaccine.groupby("ipaddr_id")["ipaddr_id"].transform("size")
            vaccine.loc[ip_counts.eq(1), "ipaddr_seq"] = 0
            duplicate_ip = vaccine["ipaddr_seq"].gt(0) & vaccine["ipaddr_id"].notna()
            vaccine = vaccine.loc[
                ~(duplicate_ip | pd.to_numeric(vaccine["excluded"], errors="coerce").eq(1))
            ].copy()

            finished = pd.to_numeric(vaccine["finished"], errors="coerce").eq(1)
            for column in [
                "d_b",
                "d_l",
                "d_c",
                "d_r",
                "d_p",
                "t_spanish",
                "screen_vaxdose",
                "vax_delay",
                "manip_chk",
                "vax_likely",
                "vax_child",
            ]:
                vaccine[column] = pd.to_numeric(vaccine[column], errors="coerce")
            vaccine["subseg"] = (
                16 * vaccine["d_b"] + 8 * vaccine["d_l"] + 4 * vaccine["d_c"] + 2 * vaccine["d_r"] + vaccine["d_p"]
            )
            vaccine["num_segs"] = vaccine[["d_b", "d_l", "d_c", "d_r", "d_p"]].sum(axis=1)
            vaccine["zero_segs"] = vaccine["num_segs"].eq(0)
            vaccine["screen_novax"] = vaccine["screen_vaxdose"].eq(2)
            vaccine["survey_novax"] = vaccine["vax_delay"].ne(1) & vaccine["vax_delay"].notna()

            def shown_message(column: str) -> pd.Series:
                if column not in vaccine.columns:
                    return pd.Series(0.0, index=vaccine.index)
                return (vaccine[column].notna() & finished).astype(float)

            messages = {
                suffix: shown_message(f"t_{suffix}_pagesubmit")
                for suffix in [
                    "popl_b",
                    "popl_l",
                    "comm_b",
                    "comm_l",
                    "comm_c",
                    "chrc_r",
                    "chld_p",
                    "chld_p_l",
                    "eldr_c",
                    "eldr_r",
                    "eldr_p",
                    "prtx_c",
                    "gthr_l",
                    "gthr_r",
                    "gthr_p",
                    "frdm_c_r",
                    "avyl_r",
                    "avyl_p",
                ]
            }
            rec_messages = {
                suffix: shown_message(f"t_rec_{suffix}_pagesubmit")
                for suffix in [
                    "lebronb",
                    "kizzy",
                    "obama",
                    "trump",
                    "warnockb",
                    "pope",
                    "fernandez",
                    "jlo",
                    "badbunny",
                    "rickwarren",
                ]
            }
            frdm_both = (
                messages["frdm_c_r"].astype(bool) & vaccine["d_c"].eq(1) & vaccine["d_r"].eq(1)
            ).astype(float)
            rec_b = (
                rec_messages["lebronb"].astype(bool)
                | rec_messages["kizzy"].astype(bool)
                | rec_messages["obama"].astype(bool)
                | rec_messages["warnockb"].astype(bool)
            ).astype(float)
            rec_l = (
                rec_messages["fernandez"].astype(bool)
                | rec_messages["jlo"].astype(bool)
                | rec_messages["badbunny"].astype(bool)
            ).astype(float)
            rec_c = rec_messages["trump"]
            rec_r = (
                rec_messages["warnockb"].astype(bool)
                | rec_messages["pope"].astype(bool)
                | rec_messages["rickwarren"].astype(bool)
            ).astype(float)
            rec_b_r = (rec_b.astype(bool) & rec_r.astype(bool)).astype(float)
            concord_recommended = (
                vaccine["d_b"] * rec_b
                + vaccine["d_l"] * rec_l
                + vaccine["d_c"] * rec_c
                + vaccine["d_r"] * rec_r
                - vaccine["d_b"] * vaccine["d_r"] * rec_b_r
            )
            concordant_messages = (
                messages["comm_b"]
                + messages["comm_l"]
                + messages["comm_c"]
                + messages["chrc_r"]
                + messages["popl_b"]
                + messages["popl_l"]
                + messages["chld_p"]
                + messages["chld_p_l"]
                + messages["eldr_c"]
                + messages["eldr_r"]
                + messages["eldr_p"]
                + messages["prtx_c"]
                + messages["gthr_l"]
                + messages["gthr_r"]
                + messages["gthr_p"]
                + frdm_both
                + messages["avyl_r"]
                + messages["avyl_p"]
                + concord_recommended
            )
            vaccine["concordant_score"] = concordant_messages + vaccine["t_spanish"].fillna(0)
            sample_a = vaccine.loc[
                vaccine["screen_novax"]
                & finished
                & vaccine["dup_pid"].eq(0)
                & vaccine["survey_novax"]
                & vaccine["manip_chk"].eq(5)
                & vaccine["vax_likely"].notna()
                & vaccine["vax_likely"].ne(0)
            ].copy()
            sample_b = sample_a.loc[~sample_a["zero_segs"]].copy()
            subsegment_counts = sample_b["subseg"].value_counts()
            sample_b = sample_b.loc[sample_b["subseg"].map(subsegment_counts).ge(10)].copy()
            sample_c = sample_a.loc[
                sample_a["d_p"].eq(1) & sample_a["vax_child"].notna() & sample_a["vax_child"].ne(0)
            ].copy()
            subsegment_counts = sample_c["subseg"].value_counts()
            sample_c = sample_c.loc[sample_c["subseg"].map(subsegment_counts).ge(10)].copy()

            components = []
            for sample_name, sample, outcome in [
                ("sampleB_self", sample_b, "vax_likely"),
                ("sampleC_child", sample_c, "vax_child"),
            ]:
                outcome_values = sample[outcome].astype(float)
                design = pd.DataFrame(
                    {
                        "const": 1.0,
                        "concordant_score": sample["concordant_score"].astype(float),
                    },
                    index=sample.index,
                )
                design = pd.concat(
                    [
                        design,
                        pd.get_dummies(
                            sample["subseg"].astype(int).astype(str),
                            prefix="subseg",
                            drop_first=True,
                            dtype=float,
                        ),
                    ],
                    axis=1,
                )
                coefficients = ols_coefficients(outcome_values, design)
                outcome_sd = float(outcome_values.std(ddof=1))
                component_d = float(coefficients["concordant_score"]) / outcome_sd
                components.append(
                    {
                        "source": "vaccine_hesitancy_concordant_score",
                        "component": sample_name,
                        "D_signed": component_d,
                        "D": abs(component_d),
                        "N": int(len(sample)),
                        "coefficient_likert_points": float(coefficients["concordant_score"]),
                        "outcome_sd": outcome_sd,
                        "subsegments": int(sample["subseg"].nunique()),
                        "conversion": "source_ols_concordant_score_coefficient_divided_by_outcome_sd",
                        "append_to_plot": False,
                    }
                )
            component_df = pd.DataFrame(components)
            row = base_political_science_rescue_row(
                point_id="vaccine_hesitancy_concordant_message_median",
                source_family="COVID vaccine-hesitancy targeted-message preregistered survey experiment",
                source_label="COVID vaccine-hesitancy message experiment",
                citation_key="vaccineHesitancyOsf",
                row_unit="paper_median_of_preregistered_concordant_score_outcomes",
                row_label="COVID vaccine hesitancy median concordant-message effect on self/child intent",
                d_value=float(component_df["D"].median()),
                n_value=float(component_df["N"].median()),
                journal="OSF replication package",
                source_file=(
                    f"{VACCINE_HESITANCY_ZIP.relative_to(ROOT)}; Reddinger_Levine_Charness_vaccination_rct.csv; "
                    "programs__sampling.do and programs__concordant_score.do; exact source samples B/C "
                    "reconstructed (N=2621 and N=1032), OLS concordant-score effects divided by outcome SD"
                ),
                source_row_number=28,
            )
            plot_rows.append(row)
            audit_rows.extend(components)
            audit_rows.append({**row, "source": "vaccine_hesitancy_concordant_score", "append_to_plot": True})
        except Exception as exc:
            audit_rows.append(
                {
                    "source": "vaccine_hesitancy_concordant_score",
                    "append_to_plot": False,
                    "blocker": f"failed to parse {VACCINE_HESITANCY_ZIP.relative_to(ROOT)}: {exc}",
                }
            )

    if AEA_GOVERNANCE_CANDIDATES.exists():
        try:
            aea_candidates = pd.read_csv(AEA_GOVERNANCE_CANDIDATES, low_memory=False)
            psl_rows = aea_candidates.loc[
                aea_candidates["RCT_ID"].astype(str).eq("AEARCTR-0001501")
            ]
            if not psl_rows.empty:
                psl = psl_rows.iloc[0]
                row = base_political_science_rescue_row(
                    point_id="liberia_partnership_schools_test_score_sd",
                    source_family="Liberia Partnership Schools preregistered education-governance field experiment",
                    source_label="Liberia Partnership Schools",
                    citation_key="liberiaPslAeaRegistry",
                    row_unit="paper_reported_standardized_primary_learning_effect",
                    row_label="Liberia school-outsourcing effect on English/math test scores",
                    d_value=0.18,
                    n_value=3700.0,
                    journal="American Economic Review",
                    source_file=(
                        f"{AEA_GOVERNANCE_CANDIDATES.relative_to(ROOT)}; AEA RCT Registry AEARCTR-0001501; "
                        "registry-linked final paper abstract reports students in outsourced schools scored 0.18 sigma "
                        "higher in English and mathematics; planned student sample is 20 per 185 schools = 3,700; "
                        "Dataverse 10.7910/DVN/5OPIYU remains guestbook-blocked locally"
                    ),
                    source_row_number=29,
                )
                plot_rows.append(row)
                audit_rows.append(
                    {
                        **row,
                        "source": "liberia_partnership_schools",
                        "trial_url": safe_text(psl.get("Url")),
                        "replication_url": safe_text(psl.get("Public data url")),
                        "append_to_plot": True,
                    }
                )
        except Exception as exc:
            audit_rows.append(
                {
                    "source": "liberia_partnership_schools",
                    "append_to_plot": False,
                    "blocker": f"failed to parse {AEA_GOVERNANCE_CANDIDATES.relative_to(ROOT)}: {exc}",
                }
            )

    if PLOT1_PAIR_DETAILS.exists() and AZEVEDO_JEPS_ANALYSIS_HTML.exists():
        try:
            pairs = pd.read_csv(PLOT1_PAIR_DETAILS, low_memory=False)
            mask = pairs["pair_id"].fillna("").astype(str).eq("fred_xybo_single_trace_2147")
            if not mask.any():
                mask = pairs["replication_title"].fillna("").astype(str).str.contains(
                    "Does Stereotype Threat Contribute to the Political Knowledge Gender Gap",
                    case=False,
                    regex=False,
                )
            azevedo = pairs.loc[mask].iloc[0]
            row = base_political_science_rescue_row(
                point_id="azevedo_jeps_political_knowledge_replication_d",
                source_family="Azevedo et al. JEPS preregistered political-knowledge replication",
                source_label="JEPS political-knowledge replication",
                citation_key="azevedoJepsDataverse",
                row_unit="paper_preregistered_replication_main_effect",
                row_label="Political knowledge gender-gap preregistered replication effect",
                d_value=float(abs(azevedo["D_larger_N"])),
                n_value=float(azevedo["N_larger_N"]),
                journal="Journal of Experimental Political Science",
                source_file=(
                    f"{PLOT1_PAIR_DETAILS.relative_to(ROOT)}; {AZEVEDO_JEPS_ANALYSIS_HTML.relative_to(ROOT)}; "
                    "OSF preregistration nxrg7; FReD/SCORE curated replication effect for the preregistered political-knowledge replication"
                ),
                source_row_number=12,
            )
            plot_rows.append(row)
            audit_rows.append(
                {
                    **row,
                    "source": "azevedo_jeps_replication",
                    "original_d": float(azevedo["D_smaller_N"]),
                    "original_n": float(azevedo["N_smaller_N"]),
                    "append_to_plot": True,
                }
            )
        except Exception as exc:
            audit_rows.append(
                {
                    "source": "azevedo_jeps_replication",
                    "append_to_plot": False,
                    "blocker": f"failed to parse {PLOT1_PAIR_DETAILS.relative_to(ROOT)}: {exc}",
                }
            )

    graham_n = 4027
    graham_beta = -0.007
    graham_se = 0.008
    graham_row = base_political_science_rescue_row(
        point_id="tess_graham1155_undemocratic_copartisan_t_to_d",
        source_family="TESS Graham 1155 explicit-PAP political-behavior survey experiment",
        source_label="TESS Graham 1155 survey experiment",
        citation_key="tessGraham1155",
        row_unit="study_page_preregistered_primary_result",
        row_label="Support for undemocratic co-partisan after electoral-fairness treatment",
        d_value=d_from_t_statistic(graham_beta / graham_se, graham_n),
        n_value=graham_n,
        journal="TESS study page",
        source_file=(
            "https://tessexperiments.org/study/graham1155; PAP https://osf.io/gw493/; "
            "TESS results summary B=-0.007, SE=0.008, N=4,027 converted as 2|t|/sqrt(N)"
        ),
        source_row_number=8,
    )
    plot_rows.append(graham_row)
    audit_rows.append({**graham_row, "source": "tess_graham1155", "append_to_plot": True})

    johnson_n = 5606
    johnson_chi2 = [44.24, 134.59, 37.66, 1086.4]
    johnson_ds = [d_from_chi_square_1df(value, johnson_n) for value in johnson_chi2]
    johnson_row = base_political_science_rescue_row(
        point_id="tess_johnson1389_school_choice_fairness_chi2_median",
        source_family="TESS Johnson 1389 explicit-PAP school-choice survey experiment",
        source_label="TESS Johnson 1389 survey experiment",
        citation_key="tessJohnson1389",
        row_unit="study_page_preregistered_h1_median_result",
        row_label="Algorithmic school assignment fairness median H1 contrast",
        d_value=float(np.nanmedian(johnson_ds)),
        n_value=johnson_n,
        journal="TESS study page",
        source_file=(
            "https://tessexperiments.org/study/johnson1389; PAP https://osf.io/vx7de/; "
            "TESS H1 chi-square results 44.24, 134.59, 37.66, 1086.4 converted from 1-df chi-square to r to d"
        ),
        source_row_number=9,
    )
    plot_rows.append(johnson_row)
    audit_rows.extend(
        {
            "source": "tess_johnson1389",
            "component": f"h1_chi_square_{idx + 1}",
            "chi_square": value,
            "D": johnson_ds[idx],
            "N": johnson_n,
            "append_to_plot": False,
        }
        for idx, value in enumerate(johnson_chi2)
    )
    audit_rows.append({**johnson_row, "source": "tess_johnson1389", "append_to_plot": True})

    # Keep package-derived numeric component contrasts in the rescue audit. The
    # final Plot 3 feeder collapses political-science sources back to one median
    # row per paper/project after this function returns. Kalla/Broockman is
    # excluded here because it is already emitted as experiment-level rows.
    audit_df_for_components = pd.DataFrame(audit_rows)
    component_families: set[str] = set()
    if not audit_df_for_components.empty and "source" in audit_df_for_components.columns:
        component_d = numeric_series(audit_df_for_components.get("D", pd.Series(index=audit_df_for_components.index)))
        component_n = numeric_series(audit_df_for_components.get("N", pd.Series(index=audit_df_for_components.index)))
        append_flags = (
            audit_df_for_components.get("append_to_plot", pd.Series(False, index=audit_df_for_components.index))
            .astype(str)
            .str.lower()
            .isin({"true", "1"})
        )
        component_candidates = audit_df_for_components.loc[
            ~append_flags
            & component_d.gt(0)
            & component_n.gt(0)
            & audit_df_for_components["source"].notna()
            & ~audit_df_for_components["source"].astype(str).eq("kalla_broockman_2018")
        ].copy()
        if not component_candidates.empty:
            component_candidates["D_component_plot"] = component_d.loc[component_candidates.index]
            component_candidates["N_component_plot"] = component_n.loc[component_candidates.index]
            meta_rows = audit_df_for_components.loc[
                append_flags
                & audit_df_for_components["source"].notna()
                & audit_df_for_components.get("source_family", pd.Series("", index=audit_df_for_components.index)).notna()
            ].copy()
            source_meta = {
                safe_text(row["source"]): row
                for _, row in meta_rows.drop_duplicates("source", keep="first").iterrows()
            }
            component_sources = [
                source
                for source in sorted(component_candidates["source"].dropna().astype(str).unique())
                if source in source_meta
            ]
            component_families = {
                safe_text(source_meta[source].get("source_family"))
                for source in component_sources
                if safe_text(source_meta[source].get("source_family"))
            }
            if component_families:
                plot_rows = [
                    row
                    for row in plot_rows
                    if safe_text(row.get("source_family")) not in component_families
                ]

            component_plot_counter = 0
            for source in component_sources:
                meta = source_meta[source]
                family = safe_text(meta.get("source_family"))
                source_components = component_candidates.loc[
                    component_candidates["source"].astype(str).eq(source)
                ].copy()
                for component_idx, component in enumerate(source_components.itertuples(index=False), start=1):
                    component_plot_counter += 1
                    component_label = safe_text(getattr(component, "component", "")) or f"component {component_idx}"
                    point_id = f"{source}_component_contrast_{component_idx:03d}"
                    row = base_political_science_rescue_row(
                        point_id=point_id,
                        source_family=family,
                        source_label=safe_text(meta.get("source_label")),
                        citation_key=safe_text(meta.get("citation_key")),
                        row_unit="component_preregistered_treatment_outcome_contrast",
                        row_label=f"{safe_text(meta.get('source_label'))}: {component_label}",
                        d_value=float(getattr(component, "D_component_plot")),
                        n_value=float(getattr(component, "N_component_plot")),
                        journal=safe_text(meta.get("journal")),
                        source_file=(
                            f"{safe_text(meta.get('source_file'))}; component contrast {component_label}; "
                            "promoted from package-derived political-science rescue audit rows"
                        ),
                        source_row_number=11000 + component_plot_counter,
                    )
                    plot_rows.append(row)
                    audit_rows.append(
                        {
                            **row,
                            "source": source,
                            "component": component_label,
                            "append_to_plot": True,
                            "component_layer": "promoted_component_contrast",
                        }
                    )

    out = pd.DataFrame(audit_rows)
    if component_families and not out.empty and "source_family" in out.columns:
        audit_append_flags = out.get("append_to_plot", pd.Series(False, index=out.index)).astype(str).str.lower().isin(
            {"true", "1"}
        )
        component_layer = out.get("component_layer", pd.Series("", index=out.index)).fillna("").astype(str)
        replaced_medians = (
            audit_append_flags
            & out["source_family"].fillna("").astype(str).isin(component_families)
            & component_layer.ne("promoted_component_contrast")
        )
        out.loc[replaced_medians, "append_to_plot"] = False
        out.loc[replaced_medians, "component_layer"] = "replaced_by_component_contrasts"
    out.to_csv(POLISCI_STRICT_RESCUE_ROWS, index=False)
    return pd.DataFrame(plot_rows)


def brodeur_preregistered_paper_medians() -> pd.DataFrame:
    if not CANDIDATE_ROWS.exists():
        out = pd.DataFrame()
        out.to_csv(BRODEUR_PREREG_PAPER_MEDIANS, index=False)
        return out
    try:
        candidate_rows = pd.read_csv(CANDIDATE_ROWS, low_memory=False)
    except Exception:
        out = pd.DataFrame()
        out.to_csv(BRODEUR_PREREG_PAPER_MEDIANS, index=False)
        return out

    brodeur = candidate_rows.loc[
        candidate_rows.get("source_corpus", pd.Series(dtype=object)).eq("economics_brodeur_2024")
    ].copy()
    if brodeur.empty:
        out = pd.DataFrame()
        out.to_csv(BRODEUR_PREREG_PAPER_MEDIANS, index=False)
        return out

    notes = brodeur.get("notes", pd.Series("", index=brodeur.index)).fillna("").astype(str)
    prereg_flag = notes.str.extract(r"prereg=([^;]+)", expand=False).fillna("").str.strip().str.lower()
    pap_flag = notes.str.extract(r"preanalysisplan=([^;]+)", expand=False).fillna("").str.strip().str.lower()
    pap_power_flag = notes.str.extract(r"pap_power=([^;]+)", expand=False).fillna("").str.strip().str.lower()
    truthy = {"1", "1.0", "true", "yes"}
    is_prereg = prereg_flag.isin(truthy)
    is_pap = pap_flag.isin(truthy)
    is_pap_power = pap_power_flag.isin(truthy)
    d_values = numeric_series(brodeur.get("abs_D", brodeur.get("D", pd.Series(index=brodeur.index)))).abs()
    n_values = numeric_series(brodeur.get("N", pd.Series(index=brodeur.index)))
    keep = (is_prereg | is_pap | is_pap_power) & (d_values > 0) & (n_values > 0)
    brodeur = brodeur.loc[keep].copy()
    if brodeur.empty:
        out = pd.DataFrame()
        out.to_csv(BRODEUR_PREREG_PAPER_MEDIANS, index=False)
        return out

    brodeur["D_plot"] = d_values.loc[brodeur.index]
    brodeur["N_plot"] = n_values.loc[brodeur.index]
    brodeur["is_prereg"] = is_prereg.loc[brodeur.index].astype(int)
    brodeur["is_pap"] = is_pap.loc[brodeur.index].astype(int)
    brodeur["is_pap_power"] = is_pap_power.loc[brodeur.index].astype(int)
    group_key = brodeur["paper_id"].fillna("").astype(str)
    group_key = group_key.mask(group_key.eq(""), brodeur["title"].fillna("").astype(str))
    brodeur["paper_group_key"] = group_key
    medians = (
        brodeur.groupby("paper_group_key", sort=False)
        .agg(
            paper_id=("paper_id", "first"),
            title=("title", "first"),
            journal=("journal", "first"),
            year=("year", "first"),
            D=("D_plot", "median"),
            N=("N_plot", "median"),
            table_test_rows=("D_plot", "size"),
            prereg_flag=("is_prereg", "max"),
            preanalysisplan_flag=("is_pap", "max"),
            pap_power_flag=("is_pap_power", "max"),
        )
        .reset_index(drop=True)
    )
    medians = medians.sort_values(["title", "paper_id"], kind="stable").reset_index(drop=True)
    medians.insert(0, "point_id", [f"brodeur_prereg_pap_paper_median_{i + 1:03d}" for i in range(len(medians))])
    medians["source_family"] = "Brodeur et al. 2024 preregistered/PAP economics table tests"
    medians["source_label"] = "Brodeur et al. 2024 preregistered/PAP economics table tests"
    medians["citation_key"] = "brodeur2020"
    medians["row_unit"] = "paper_median_of_preregistered_or_pap_table_tests"
    medians["supported"] = "not coded"
    medians["source_file"] = str(CANDIDATE_ROWS.relative_to(ROOT))
    medians["source_row_number"] = medians.index + 1
    medians.to_csv(BRODEUR_PREREG_PAPER_MEDIANS, index=False)
    return medians


def normalize_preregistered_results() -> pd.DataFrame:
    table40 = pd.read_csv(PREREG_TABLE_40)
    table41 = pd.read_csv(PREREG_TABLE_41)
    rows: list[dict[str, object]] = []
    included_doi_norms: set[str] = set()

    for _, row in table40.iterrows():
        row_number = int(row["#"])
        rows.append(
            {
                "point_id": f"scheel2021_registered_report_{row_number:03d}",
                "plot_name": "Plot 3",
                "source_layer": "preregistered_confirmatory_result",
                "source_family": "Scheel et al. 2021 preregistered-hypotheses corpus",
                "source_label": "Registered Reports preregistered-hypotheses corpus",
                "citation_key": "scheel2021",
                "row_unit": "registered_report_first_preregistered_hypothesis",
                "row_label": safe_text(row["Study"]),
                "D": float(row["|d|"]),
                "N": float(row["N"]),
                "supported": safe_text(row["Supported"]).lower(),
                "journal": safe_text(row["Journal"]),
                "source_file": str(PREREG_TABLE_40.relative_to(ROOT)),
                "source_row_number": row_number,
            }
        )

    for _, row in table41.iterrows():
        row_number = int(row["#"])
        rows.append(
            {
                "point_id": f"dorison2022_psacr001_{row_number:03d}",
                "plot_name": "Plot 3",
                "source_layer": "preregistered_confirmatory_result",
                "source_family": "Dorison et al. 2022 PSA-CR001 pooled preregistered rows",
                "source_label": "PSA-CR001 pooled preregistered rows",
                "citation_key": "dorison2022",
                "row_unit": "pooled_primary_preregistered_hypothesis",
                "row_label": safe_text(row["Primary hypothesis (preregistered)"]),
                "D": float(row["Pooled |d|"]),
                "N": float(str(row["Pooled N"]).replace(",", "")),
                "supported": safe_text(row["Supported"]).lower(),
                "journal": "Affective Science",
                "source_file": str(PREREG_TABLE_41.relative_to(ROOT)),
                "source_row_number": row_number,
            }
        )

    for row in MANUAL_PREREGISTERED_ADDITIONS:
        if row["point_id"] == "mousa2020_iraq_soccer_social_cohesion_median" and MOUSA_D_CANDIDATES.exists():
            mousa_outcomes = pd.read_csv(MOUSA_D_CANDIDATES)
            mousa_outcomes = mousa_outcomes.loc[
                ~mousa_outcomes["row_id"].astype(str).str.contains("paper_median", case=False, na=False)
            ].copy()
            for component_number, outcome_row in enumerate(mousa_outcomes.itertuples(index=False), start=1):
                d_value = float(getattr(outcome_row, "abs_D_candidate", np.nan))
                n_value = float(getattr(outcome_row, "analytic_n", np.nan))
                if not (np.isfinite(d_value) and np.isfinite(n_value) and d_value > 0 and n_value > 0):
                    continue
                outcome = safe_text(getattr(outcome_row, "outcome", ""))
                outcome_label = safe_text(getattr(outcome_row, "outcome_label", "")) or outcome
                conversion = safe_text(getattr(outcome_row, "conversion_method", ""))
                source_file = safe_text(getattr(outcome_row, "source_file", ""))
                rows.append(
                    {
                        "point_id": safe_text(getattr(outcome_row, "row_id", "")) or f"mousa2020_component_{component_number:03d}",
                        "plot_name": "Plot 3",
                        "source_layer": "preregistered_confirmatory_result",
                        "source_family": row["source_family"],
                        "source_label": row["source_label"],
                        "field": safe_text(row.get("field")),
                        "citation_key": row["citation_key"],
                        "row_unit": "component_preregistered_behavioral_or_attitudinal_outcome",
                        "row_label": f"Mousa soccer social cohesion: {outcome_label}",
                        "D": d_value,
                        "N": n_value,
                        "supported": row["supported"],
                        "journal": row["journal"],
                        "source_file": (
                            f"{MOUSA_D_CANDIDATES.relative_to(ROOT)}; generated from "
                            "data/raw/corpus_candidates/political_science_unlock/zenodo/3942437; "
                            f"component outcome {outcome}; source file {source_file}; conversion={conversion}; "
                            "paper median retained only inside the candidate audit file"
                        ),
                        "source_row_number": 9000 + component_number,
                    }
                )
            continue
        rows.append(
            {
                "point_id": row["point_id"],
                "plot_name": "Plot 3",
                "source_layer": "preregistered_confirmatory_result",
                "source_family": row["source_family"],
                "source_label": row["source_label"],
                "field": safe_text(row.get("field")),
                "citation_key": row["citation_key"],
                "row_unit": row["row_unit"],
                "row_label": row["row_label"],
                "D": float(row["D"]),
                "N": float(row["N"]),
                "supported": row["supported"],
                "journal": row["journal"],
                "source_file": row["source_file"],
                "source_row_number": row["source_row_number"],
            }
        )

    brodeur_medians = brodeur_preregistered_paper_medians()
    for _, row in brodeur_medians.iterrows():
        title = safe_text(row.get("title")) or safe_text(row.get("paper_id")) or safe_text(row.get("point_id"))
        rows.append(
            {
                "point_id": row["point_id"],
                "plot_name": "Plot 3",
                "source_layer": "preregistered_confirmatory_result",
                "source_family": row["source_family"],
                "source_label": row["source_label"],
                "field": brodeur_preregistered_field_for_title(title),
                "citation_key": row["citation_key"],
                "row_unit": row["row_unit"],
                "row_label": title,
                "D": float(row["D"]),
                "N": float(row["N"]),
                "supported": row["supported"],
                "journal": safe_text(row.get("journal")),
                "source_file": (
                    f"{row['source_file']}; paper-level median across {int(row['table_test_rows'])} "
                    "preregistration/PAP-flagged extracted table tests"
                ),
                "source_row_number": int(row["source_row_number"]),
            }
        )

    political_rescues = political_science_strict_rescue_rows()
    for _, row in political_rescues.iterrows():
        rows.append(
            {
                "point_id": row["point_id"],
                "plot_name": "Plot 3",
                "source_layer": "preregistered_confirmatory_result",
                "source_family": row["source_family"],
                "source_label": row["source_label"],
                "field": row["field"],
                "citation_key": row["citation_key"],
                "row_unit": row["row_unit"],
                "row_label": row["row_label"],
                "D": float(row["D"]),
                "N": float(row["N"]),
                "supported": row["supported"],
                "journal": row["journal"],
                "source_file": row["source_file"],
                "source_row_number": row["source_row_number"],
            }
        )

    if PREREG_CTGOV_PRIMARY_RANDOMIZED_RESULTS.exists():
        ctgov_primary = pd.read_csv(PREREG_CTGOV_PRIMARY_RANDOMIZED_RESULTS)
    else:
        ctgov_primary = normalize_ctgov_primary_randomized_sidecar_rows()
    if not ctgov_primary.empty:
        ctgov_primary = ctgov_primary.loc[
            (numeric_series(ctgov_primary.get("D", pd.Series(index=ctgov_primary.index))) > 0)
            & (numeric_series(ctgov_primary.get("N", pd.Series(index=ctgov_primary.index))) > 0)
        ].copy()
        for _, row in ctgov_primary.iterrows():
            unit_id = safe_text(row.get("unit_id")) or safe_text(row.get("point_id"))
            rows.append(
                {
                    "point_id": f"ctgov_primary_randomized_strict_{unit_id.lower()}",
                    "plot_name": "Plot 3",
                    "source_layer": "registered_confirmatory_result",
                    "source_family": "ClinicalTrials.gov phase-2+ primary randomized registry rows",
                    "source_label": "ClinicalTrials.gov phase-2+ primary randomized registry rows",
                    "field": "clinical medicine",
                    "citation_key": "du2024",
                    "row_unit": "one_primary_registered_outcome_per_randomized_trial",
                    "row_label": safe_text(row.get("row_label")) or unit_id,
                    "D": float(row["D"]),
                    "N": float(row["N"]),
                    "supported": safe_text(row.get("support_or_significance")) or "registry p-value proxy",
                    "journal": "ClinicalTrials.gov",
                    "source_file": (
                        f"{row.get('source_file')}; phase-2+ randomized interventional trial with exactly one "
                        "eligible registered primary two-group outcome; D reconstructed from registry p-value and enrollment"
                    ),
                    "source_row_number": int(row.get("source_row_number", 0) or 0),
                }
            )

    if PUBLISHED_PAPERS.exists():
        published = pd.read_csv(PUBLISHED_PAPERS)
        schaefer = published.loc[
            published["source_corpus"].eq("schaefer_schwarz_2019_with_prereg")
            & (numeric_series(published["D_median"]) > 0)
            & (numeric_series(published["N_median"]) > 0)
        ].copy()
        schaefer = schaefer.sort_values("unit_id", kind="stable").reset_index(drop=True)
        for idx, row in schaefer.iterrows():
            unit_id = safe_text(row.get("unit_id")) or f"row_{idx + 1}"
            year = safe_text(row.get("year"))
            year_label = ""
            if year:
                try:
                    year_label = str(int(float(year)))
                except ValueError:
                    year_label = year
            rows.append(
                {
                    "point_id": f"schaefer2019_preregistered_{idx + 1:03d}",
                    "plot_name": "Plot 3",
                    "source_layer": "preregistered_confirmatory_result",
                    "source_family": "Schäfer/Schwarz 2019 preregistered psychology articles",
                    "source_label": "Schäfer/Schwarz preregistered psychology articles",
                    "citation_key": "schaefer2019meaningfulness",
                    "row_unit": "preregistered_key_question_effect",
                    "row_label": f"{year_label} preregistered key-question effect ({unit_id})".strip(),
                    "D": float(row["D_median"]),
                    "N": float(row["N_median"]),
                    "supported": "not coded",
                    "journal": "not coded",
                    "source_file": str(PUBLISHED_PAPERS.relative_to(ROOT)),
                    "source_row_number": idx + 1,
                }
            )

        score_prereg, _, _ = score_prereg_indicated_paper_rows(published)
        for idx, row in score_prereg.iterrows():
            unit_id = safe_text(row.get("unit_id")) or f"row_{idx + 1}"
            score_doi_norm = normalize_doi_value(row.get("DOI")) or normalize_doi_value(unit_id)
            if score_doi_norm:
                included_doi_norms.add(score_doi_norm)
            title = safe_text(row.get("title"))
            year = safe_text(row.get("year"))
            year_label = ""
            if year:
                try:
                    year_label = str(int(float(year)))
                except ValueError:
                    year_label = year
            label_parts = [part for part in [year_label, title or unit_id] if part]
            rows.append(
                {
                    "point_id": f"score_cos_prereg_indicated_{idx + 1:03d}",
                    "plot_name": "Plot 3",
                    "source_layer": "preregistered_confirmatory_result",
                    "source_family": "SCORE/COS preregistration-indicated original papers",
                    "source_label": "SCORE/COS preregistration-indicated original papers",
                    "field": safe_text(row.get("field")) or plot3_default_field("SCORE/COS preregistration-indicated original papers"),
                    "citation_key": "tyner2026",
                    "row_unit": "paper_level_preregistration_indicated_claim_effect",
                    "row_label": " - ".join(label_parts),
                    "D": float(row["D_median"]),
                    "N": float(row["N_median"]),
                    "supported": "not coded",
                    "journal": safe_text(row.get("journal")),
                    "source_file": f"{PUBLISHED_PAPERS.relative_to(ROOT)}; {SCORE_ORIG_PREREG.relative_to(ROOT)}",
                    "source_row_number": idx + 1,
                }
            )

        score_text_rescue = score_text_claim_rescue_rows()
        for idx, row in score_text_rescue.iterrows():
            year = safe_text(row.get("pub_year"))
            year_label = ""
            if year:
                try:
                    year_label = str(int(float(year)))
                except ValueError:
                    year_label = year
            title = safe_text(row.get("title"))
            paper_id = safe_text(row.get("paper_id"))
            label_parts = [part for part in [year_label, title or paper_id] if part]
            rows.append(
                {
                    "point_id": f"score_cos_prereg_text_rescue_{idx + 1:03d}",
                    "plot_name": "Plot 3",
                    "source_layer": "preregistered_confirmatory_result",
                    "source_family": "SCORE/COS preregistration-indicated original papers",
                    "source_label": "SCORE/COS preregistration-indicated original papers",
                    "field": safe_text(row.get("COS_pub_category")) or plot3_default_field("SCORE/COS preregistration-indicated original papers"),
                    "citation_key": "tyner2026",
                    "row_unit": "paper_level_preregistration_indicated_claim_effect",
                    "row_label": " - ".join(label_parts),
                    "D": float(row["D_candidate"]),
                    "N": float(row["N_candidate"]),
                    "supported": "not coded",
                    "journal": safe_text(row.get("journal")),
                    "source_file": f"{SCORE_TEXT_CLAIM_CANDIDATES.relative_to(ROOT)}; data/raw/corpus_candidates/score/extracted_claims.csv.gz",
                    "source_row_number": idx + 1,
                }
            )

    vandenakker_medians = vandenakker_matched_median_rows()
    if not vandenakker_medians.empty and included_doi_norms:
        vandenakker_medians["_doi_norm"] = vandenakker_medians.get("doi", pd.Series("", index=vandenakker_medians.index)).map(normalize_doi_value)
        vandenakker_medians = vandenakker_medians.loc[~vandenakker_medians["_doi_norm"].isin(included_doi_norms)].copy()
        vandenakker_medians = vandenakker_medians.drop(columns=["_doi_norm"])
    for idx, row in vandenakker_medians.iterrows():
        psp = safe_text(row.get("PSP")) or str(idx + 1)
        title = safe_text(row.get("title"))
        doi = safe_text(row.get("doi"))
        matched_rows = safe_text(row.get("matched_result_rows"))
        label_parts = [part for part in [title or f"PSP {psp}", f"{matched_rows} matched prereg result(s)"] if part]
        rows.append(
            {
                "point_id": f"vandenakker_matched_prereg_median_{idx + 1:03d}",
                "plot_name": "Plot 3",
                "source_layer": "preregistered_confirmatory_result",
                "source_family": "van den Akker matched preregistered-result paper medians",
                "source_label": "van den Akker matched preregistered-result paper medians",
                "citation_key": "vanDenAkkerSelectiveHypothesis2023",
                "row_unit": "paper_median_of_matched_preregistered_result_statistics",
                "row_label": " - ".join(label_parts),
                "D": float(row["D_candidate"]),
                "N": float(row["N_candidate"]),
                "supported": "not coded",
                "journal": safe_text(row.get("journal")),
                "source_file": f"{VANDENAKKER_MEDIAN_CANDIDATES.relative_to(ROOT)}; DOI={doi}",
                "source_row_number": idx + 1,
            }
        )

    rpcb_medians = rpcb_registered_report_median_rows()
    for idx, row in rpcb_medians.iterrows():
        paper_number = safe_text(row.get("paper_number")) or str(idx + 1)
        registered_rows = safe_text(row.get("registered_result_rows"))
        label_parts = [
            f"RPCB paper {paper_number}",
            f"{registered_rows} registered effect(s)" if registered_rows else "registered effect median",
            safe_text(row.get("effect_description")),
        ]
        rows.append(
            {
                "point_id": f"rpcb_registered_report_median_{idx + 1:03d}",
                "plot_name": "Plot 3",
                "source_layer": "preregistered_confirmatory_result",
                "source_family": "RPCB eLife Registered Report replication effects",
                "source_label": "RPCB Registered Report replication effects",
                "citation_key": "errington2021",
                "row_unit": "paper_median_of_registered_report_replication_effects",
                "row_label": " - ".join(part for part in label_parts if part),
                "D": float(row["D_candidate"]),
                "N": float(row["N_candidate"]),
                "supported": "not coded",
                "journal": "eLife",
                "field": "preclinical biology",
                "source_file": str(RPCB_PRECLINICAL_CANDIDATES.relative_to(ROOT)),
                "source_row_number": idx + 1,
            }
        )

    df = pd.DataFrame(rows)
    df["D"] = numeric_series(df["D"]).abs()
    df["N"] = numeric_series(df["N"])
    df = df[(df["D"] > 0) & (df["N"] > 0)].copy()
    precollapse_df = df.copy()
    df = collapse_plot3_to_one_dot_per_paper(df)
    write_political_science_paper_project_medians(precollapse_df, df)
    if "field" not in df.columns:
        df["field"] = ""
    field_text = df["field"].fillna("").astype(str).str.strip()
    df["field"] = field_text.where(field_text.ne(""), df["source_family"].map(plot3_default_field))
    df["field_label"] = df["field"].map(display_field_label)
    df["log10_N"] = np.log10(df["N"])
    df["log10_D"] = np.log10(df["D"])
    df["two_sample_p05_boundary_D"] = 2 * Z_05 / np.sqrt(df["N"])
    df["above_two_sample_p05_curve"] = df["D"] >= df["two_sample_p05_boundary_D"]
    df.to_csv(PREREG_RESULTS, index=False)
    clean_tsv_frame(df).to_csv(PREREG_RESULTS_TSV, sep="\t", index=False)
    return df


def normalize_preregistered_sensitivity_sidecar_rows() -> pd.DataFrame:
    """Rows that are preregistered-like but outside the strict Plot 3 gate."""
    rows: list[dict[str, object]] = []

    if PUBLISHED_PAPERS.exists():
        published = pd.read_csv(PUBLISHED_PAPERS)
        ctgov = published.loc[
            published["source_corpus"].eq("ctgov_finer_grained_kg")
            & (numeric_series(published["D_median"]) > 0)
            & (numeric_series(published["N_median"]) > 0)
        ].copy()
        ctgov = ctgov.sort_values("unit_id", kind="stable").reset_index(drop=True)
        for idx, row in ctgov.iterrows():
            unit_id = safe_text(row.get("unit_id")) or f"ctgov_{idx + 1}"
            rows.append(
                {
                    "point_id": f"ctgov_registry_trial_{idx + 1:05d}",
                    "plot_name": "Plot 3 sensitivity",
                    "source_layer": "registered_or_preregistered_sidecar",
                    "source_family": "ClinicalTrials.gov registry-result D/N comparator",
                    "source_label": "ClinicalTrials.gov registry-result D/N comparator",
                    "citation_key": "du2024",
                    "row_unit": "registry_trial_median",
                    "unit_id": unit_id,
                    "row_label": safe_text(row.get("title")) or unit_id,
                    "D": float(row["D_median"]),
                    "N": float(row["N_median"]),
                    "support_or_significance": "registry p-value proxy",
                    "source_file": str(PUBLISHED_PAPERS.relative_to(ROOT)),
                    "source_row_number": idx + 1,
                    "admission_reason": "registered registry-result D/N sidecar; excluded from strict Plot 3 because it is registry evidence rather than a published analytic preregistration row",
                }
            )

    if CANDIDATE_ROWS.exists():
        try:
            candidate_rows = pd.read_csv(CANDIDATE_ROWS, low_memory=False)
        except Exception:
            candidate_rows = pd.DataFrame()
        brodeur = candidate_rows.loc[candidate_rows.get("source_corpus", pd.Series(dtype=object)).eq("economics_brodeur_2024")].copy()
        if not brodeur.empty:
            notes = brodeur.get("notes", pd.Series("", index=brodeur.index)).fillna("").astype(str)
            prereg_flag = notes.str.extract(r"prereg=([^;]+)", expand=False).fillna("").str.strip().str.lower()
            pap_flag = notes.str.extract(r"preanalysisplan=([^;]+)", expand=False).fillna("").str.strip().str.lower()
            pap_power_flag = notes.str.extract(r"pap_power=([^;]+)", expand=False).fillna("").str.strip().str.lower()
            truthy = {"1", "1.0", "true", "yes"}
            flagged = prereg_flag.isin(truthy) | pap_flag.isin(truthy) | pap_power_flag.isin(truthy)
            d_values = numeric_series(brodeur.get("abs_D", brodeur.get("D", pd.Series(index=brodeur.index)))).abs()
            n_values = numeric_series(brodeur.get("N", pd.Series(index=brodeur.index)))
            brodeur = brodeur.loc[flagged & (d_values > 0) & (n_values > 0)].copy()
            brodeur["D_plot"] = d_values.loc[brodeur.index]
            brodeur["N_plot"] = n_values.loc[brodeur.index]
            brodeur["prereg_flag"] = prereg_flag.loc[brodeur.index]
            brodeur["preanalysisplan_flag"] = pap_flag.loc[brodeur.index]
            brodeur["pap_power_flag"] = pap_power_flag.loc[brodeur.index]
            brodeur = brodeur.sort_values(["paper_id", "row_id"], kind="stable").reset_index(drop=True)
            for idx, row in brodeur.iterrows():
                row_id = safe_text(row.get("row_id")) or f"brodeur_{idx + 1}"
                rows.append(
                    {
                        "point_id": f"brodeur_prereg_pap_table_test_{idx + 1:05d}",
                        "plot_name": "Plot 3 sensitivity",
                        "source_layer": "registered_or_preregistered_sidecar",
                        "source_family": "Brodeur et al. 2024 preregistered/PAP economics table tests",
                        "source_label": "Brodeur preregistered/PAP economics table tests",
                        "citation_key": "brodeur2020",
                        "row_unit": "preregistered_or_pap_extracted_table_test",
                        "unit_id": row_id,
                        "row_label": safe_text(row.get("title")) or safe_text(row.get("paper_id")) or row_id,
                        "D": float(row["D_plot"]),
                        "N": float(row["N_plot"]),
                        "support_or_significance": "published table-test statistic",
                        "source_file": str(CANDIDATE_ROWS.relative_to(ROOT)),
                        "source_row_number": idx + 1,
                        "admission_reason": (
                            "preregistration/PAP-flagged economics table-test sidecar; excluded from strict Plot 3 "
                            "because no focal/main-result selector identifies a confirmatory row per paper"
                        ),
                        "prereg_flag": safe_text(row.get("prereg_flag")),
                        "preanalysisplan_flag": safe_text(row.get("preanalysisplan_flag")),
                        "pap_power_flag": safe_text(row.get("pap_power_flag")),
                    }
                )

    df = pd.DataFrame(rows)
    if df.empty:
        df.to_csv(PREREG_SENSITIVITY_RESULTS, index=False)
        return df
    df["D"] = numeric_series(df["D"]).abs()
    df["N"] = numeric_series(df["N"])
    df = df[(df["D"] > 0) & (df["N"] > 0)].copy()
    df["log10_N"] = np.log10(df["N"])
    df["log10_D"] = np.log10(df["D"])
    df["two_sample_p05_boundary_D"] = 2 * Z_05 / np.sqrt(df["N"])
    df["above_two_sample_p05_curve"] = df["D"] >= df["two_sample_p05_boundary_D"]
    df.to_csv(PREREG_SENSITIVITY_RESULTS, index=False)
    return df


def ctgov_literal_list_len(value: object) -> float:
    try:
        parsed = ast.literal_eval(str(value))
    except Exception:
        return float("nan")
    if isinstance(parsed, list):
        return float(len(parsed))
    return float("nan")


def ctgov_p_value_to_abs_z(values: pd.Series) -> pd.Series:
    p_text = values.fillna("").astype(str)
    p_values = pd.to_numeric(
        p_text.str.extract(r"([0-9]*\.?[0-9]+(?:[eE][-+]?\d+)?)", expand=False),
        errors="coerce",
    )
    valid = (p_values > 0) & (p_values < 1)
    z = pd.Series(np.nan, index=values.index, dtype=float)
    z.loc[valid] = stats.norm.isf(p_values.loc[valid] / 2)
    return z


def normalize_ctgov_primary_randomized_sidecar_rows() -> pd.DataFrame:
    """Cleaner CT.gov sub-sidecar: one eligible phase-2+ primary randomized registry outcome per trial."""
    if not CTGOV_EFFICACY_RAW.exists():
        df = pd.DataFrame()
        df.to_csv(PREREG_CTGOV_PRIMARY_RANDOMIZED_RESULTS, index=False)
        return df

    source = pd.read_csv(CTGOV_EFFICACY_RAW, low_memory=False)
    source["_p_abs_z"] = ctgov_p_value_to_abs_z(source.get("p_value", pd.Series("", index=source.index)))
    source["_N"] = numeric_series(source.get("enrollment_num", pd.Series(index=source.index)))
    source["_group_count"] = source.get("groups", pd.Series("", index=source.index)).map(ctgov_literal_list_len)
    phase_text = source.get("trial_phase", pd.Series("", index=source.index)).fillna("").astype(str).str.lower()
    source["_phase_2plus_flag"] = phase_text.isin({"phase 2", "phase 2/phase 3", "phase 3", "phase 3/phase 4", "phase 4"})
    eligible = (
        source.get("study_type", pd.Series("", index=source.index)).astype(str).str.lower().eq("interventional")
        & source.get("allocation", pd.Series("", index=source.index)).astype(str).str.lower().eq("randomized")
        & source.get("outcome_type", pd.Series("", index=source.index)).astype(str).str.lower().eq("primary")
        & source.get("completion_year", pd.Series(index=source.index)).notna()
        & source["_phase_2plus_flag"]
        & source["_group_count"].eq(2)
        & source["_p_abs_z"].notna()
        & source["_N"].gt(0)
    )
    subset = source.loc[eligible].copy()
    if subset.empty:
        df = pd.DataFrame()
        df.to_csv(PREREG_CTGOV_PRIMARY_RANDOMIZED_RESULTS, index=False)
        return df

    # Keep only trials whose local record exposes exactly one eligible primary row.
    # This avoids choosing among multiple primaries by significance or arbitrary row order.
    per_trial = subset.groupby("NCT_ID").size()
    single_primary_nct = set(per_trial.loc[per_trial.eq(1)].index.astype(str))
    subset = subset.loc[subset["NCT_ID"].astype(str).isin(single_primary_nct)].copy()
    subset["_D"] = (2 * subset["_p_abs_z"] / np.sqrt(subset["_N"])).abs()
    subset = subset.loc[subset["_D"].gt(0) & subset["_N"].gt(0)].sort_values("NCT_ID", kind="stable").reset_index()

    rows: list[dict[str, object]] = []
    for idx, row in subset.iterrows():
        nct_id = safe_text(row.get("NCT_ID")) or f"ctgov_primary_{idx + 1}"
        rows.append(
            {
                "point_id": f"ctgov_primary_randomized_{idx + 1:05d}",
                "plot_name": "Plot 3 sensitivity",
                "source_layer": "registered_primary_randomized_sidecar",
                "source_family": "ClinicalTrials.gov phase-2+ primary randomized one-row-per-trial sub-sidecar",
                "source_label": "CT.gov phase-2+ primary randomized registry rows",
                "citation_key": "du2024",
                "row_unit": "one_primary_registry_outcome_per_randomized_trial",
                "unit_id": nct_id,
                "row_label": safe_text(row.get("outcome_title")) or nct_id,
                "D": float(row["_D"]),
                "N": float(row["_N"]),
                "support_or_significance": "registry p-value proxy",
                "source_file": str(CTGOV_EFFICACY_RAW.relative_to(ROOT)),
                "source_row_number": int(row["index"]) + 1,
                "study_type": safe_text(row.get("study_type")),
                "allocation": safe_text(row.get("allocation")),
                "trial_phase": safe_text(row.get("trial_phase")),
                "completion_year": row.get("completion_year"),
                "outcome_type": safe_text(row.get("outcome_type")),
                "outcome_id": row.get("outcome_id"),
                "p_value": safe_text(row.get("p_value")),
                "method": safe_text(row.get("method")),
                "param_type": safe_text(row.get("param_type")),
                "param_value": row.get("param_value"),
                "phase_2plus_flag": bool(row["_phase_2plus_flag"]),
                "admission_reason": (
                    "cleaner CT.gov registry sidecar: phase-2+ randomized interventional trial with exactly one locally "
                    "eligible primary two-group outcome; still excluded from strict Plot 3 because D is a "
                    "registry p-value/enrollment proxy and no protocol/SAP timing audit is attached"
                ),
            }
        )

    df = pd.DataFrame(rows)
    if not df.empty:
        df["D"] = numeric_series(df["D"]).abs()
        df["N"] = numeric_series(df["N"])
        df["log10_N"] = np.log10(df["N"])
        df["log10_D"] = np.log10(df["D"])
        df["two_sample_p05_boundary_D"] = 2 * Z_05 / np.sqrt(df["N"])
        df["above_two_sample_p05_curve"] = df["D"] >= df["two_sample_p05_boundary_D"]
    df.to_csv(PREREG_CTGOV_PRIMARY_RANDOMIZED_RESULTS, index=False)
    return df


def compact_axis_label(value: float) -> str:
    if value >= 1_000_000:
        return f"{value / 1_000_000:g}M"
    if value >= 1_000:
        return f"{value / 1_000:g}k"
    return f"{value:g}"


def sidecar_log_axis_bounds(df: pd.DataFrame, x_cap: float) -> tuple[float, float, float, float]:
    x_min_data = float(df["N"].min())
    x_min = 10.0 if x_min_data >= 10 else 1.0
    x_max = x_cap
    return x_min, x_max, DN_AXIS_Y_MIN, DN_AXIS_Y_MAX


def apply_general_results_axes(
    ax: plt.Axes,
    *,
    x_min: float,
    x_max: float,
    y_min: float,
    y_max: float,
    xlabel: str,
    ylabel: str,
) -> None:
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlim(x_min, x_max)
    ax.set_ylim(y_min, y_max)

    x_candidates = [1, 10, 100, 1_000, 10_000, 100_000, 1_000_000, 10_000_000]
    x_ticks = [tick for tick in x_candidates if x_min <= tick <= x_max]
    ax.xaxis.set_major_locator(FixedLocator(x_ticks))
    ax.xaxis.set_major_formatter(FixedFormatter([compact_axis_label(float(tick)) for tick in x_ticks]))
    ax.xaxis.set_minor_formatter(NullFormatter())

    y_candidates = [1e-5, 1e-4, 1e-3, 0.01, 0.02, 0.05, 0.1, 0.2, 0.5, 1, 2, 5, 10]
    y_ticks = [tick for tick in y_candidates if y_min <= tick <= y_max]
    ax.yaxis.set_major_locator(FixedLocator(y_ticks))
    ax.yaxis.set_major_formatter(FixedFormatter([f"{tick:g}" for tick in y_ticks]))
    ax.yaxis.set_minor_formatter(NullFormatter())

    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.grid(True, which="major", alpha=0.18, linestyle=":")
    ax.grid(True, which="minor", alpha=0.06, linestyle=":")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)


def draw_general_results_thresholds(ax: plt.Axes, xs: np.ndarray, *, x_min: float, x_max: float, y_min: float) -> None:
    label_y_reference = max(y_min, 0.02)
    for z, label, style, y_multiplier in [
        (1.6448536269514722, "p=.10", ":", 0.95),
        (Z_05, "p=.05", "--", 1.05),
        (2.5758293035489004, "p=.01", "-.", 1.15),
    ]:
        ax.plot(
            xs,
            2 * z / np.sqrt(xs),
            style,
            color="#444444",
            linewidth=3.0,
            alpha=1.0,
            zorder=11,
        )
        x_intercept = min(x_max, max(x_min, (2 * z / label_y_reference) ** 2))
        x_label = min(max(x_min * 12, x_intercept), x_max / 1.7)
        y_label = max(y_min * 1.1, 2 * z / np.sqrt(x_label) * y_multiplier)
        ax.text(
            x_label,
            y_label,
            label,
            color="#444444",
            fontsize=9,
            ha="left",
            va="bottom",
            rotation=-28,
            rotation_mode="anchor",
            bbox=dict(facecolor="white", edgecolor="none", alpha=0.78, pad=0.35),
            clip_on=True,
            zorder=12,
        )


def draw_general_results_histogram_references(
    ax_hist: plt.Axes,
    *,
    median_d: float | None,
    median_color: str,
) -> None:
    for x, label in [(0.2, "small"), (0.5, "medium"), (0.8, "large")]:
        ax_hist.axvline(x, color="#777777", lw=0.9, linestyle=":", alpha=0.75)
        ax_hist.text(
            x,
            0.94,
            f"{label}\nd={x:g}",
            transform=blended_transform_factory(ax_hist.transData, ax_hist.transAxes),
            ha="center",
            va="top",
            fontsize=7.6,
            color="#555555",
        )
    if median_d is not None and np.isfinite(median_d):
        median_clip = float(np.clip(median_d, 0.0, 3.0))
        ax_hist.axvline(median_clip, color=median_color, lw=1.1, linestyle="--")
        ax_hist.annotate(
            rf"$\tilde{{D}}={median_d:.2f}$",
            xy=(median_clip, 1.0),
            xycoords=blended_transform_factory(ax_hist.transData, ax_hist.transAxes),
            xytext=(0, 2),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=7.8,
            color=median_color,
            clip_on=False,
        )


def finish_general_results_histogram(ax_hist: plt.Axes) -> None:
    ax_hist.set_xlim(0, 3.0)
    linear_ticks = np.arange(0, 3.0 + 0.001, 0.5)
    linear_tick_labels = [f"{tick:g}" for tick in linear_ticks]
    linear_tick_labels[-1] = "3+"
    ax_hist.set_xticks(linear_ticks)
    ax_hist.set_xticklabels(linear_tick_labels)
    ax_hist.set_ylabel("Density")
    ax_hist.set_xlabel("Effect size magnitude D (linear scale, clipped at 3)")
    ax_hist.grid(False)
    for spine in ["top", "right"]:
        ax_hist.spines[spine].set_visible(False)


def normalize_staged_harvest_dn_rows(live_pair_ids: set[str]) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for path in sorted(HARVEST_STAGED_DIR.glob("*.csv")):
        try:
            staged = pd.read_csv(path)
        except Exception:
            continue
        required = {"D_original", "N_original", "D_replication", "N_replication"}
        if not required.issubset(staged.columns):
            continue

        staged = staged.copy()
        for col in required:
            staged[col] = numeric_series(staged[col])
        if "promotion_decision" in staged.columns:
            staged = staged[
                staged["promotion_decision"].fillna("").astype(str).str.lower().ne("promote_live")
            ].copy()
        if "pair_id" in staged.columns:
            staged = staged[~staged["pair_id"].fillna("").astype(str).isin(live_pair_ids)].copy()

        for idx, row in staged.iterrows():
            pair_id = safe_text(row.get("pair_id")) or f"{path.stem}_{idx}"
            source_family = (
                safe_text(row.get("source_dataset"))
                or safe_text(row.get("source_family"))
                or safe_text(row.get("project"))
                or path.stem
            )
            base = {
                "source_family": source_family,
                "source_file": str(path.relative_to(ROOT)),
                "row_unit": "staged_replication_pair_side",
                "source_status": safe_text(row.get("promotion_decision")) or safe_text(row.get("analytic_status")) or "staged",
                "row_label": safe_text(row.get("outcome")) or safe_text(row.get("replication_title")) or pair_id,
            }
            if pd.notna(row["D_original"]) and pd.notna(row["N_original"]) and row["D_original"] > 0 and row["N_original"] > 0:
                rows.append(
                    {
                        **base,
                        "point_id": f"staged::{path.stem}::{pair_id}::original",
                        "source_layer": "staged_harvest_original",
                        "side": "original",
                        "D": float(abs(row["D_original"])),
                        "N": float(row["N_original"]),
                    }
                )
            if (
                pd.notna(row["D_replication"])
                and pd.notna(row["N_replication"])
                and row["D_replication"] > 0
                and row["N_replication"] > 0
            ):
                rows.append(
                    {
                        **base,
                        "point_id": f"staged::{path.stem}::{pair_id}::followup",
                        "source_layer": "staged_harvest_followup",
                        "side": "followup",
                        "D": float(abs(row["D_replication"])),
                        "N": float(row["N_replication"]),
                    }
                )
    return pd.DataFrame(rows)


def normalize_all_source_dn_rows(prereg: pd.DataFrame | None = None) -> pd.DataFrame:
    if prereg is None:
        prereg = normalize_preregistered_results()

    rows: list[dict[str, object]] = []
    rep = pd.read_csv(REPLICATION_ALL)
    rep["D_original"] = numeric_series(rep["D_original"]).abs()
    rep["D_replication"] = numeric_series(rep["D_replication"]).abs()
    rep["N_original"] = numeric_series(rep["N_original"])
    rep["N_replication"] = numeric_series(rep["N_replication"])
    live_pair_ids = set(rep["pair_id"].fillna("").astype(str))

    for _, row in rep.iterrows():
        pair_id = safe_text(row.get("pair_id")) or safe_text(row.get("match_key")) or f"rep_pair_{len(rows)}"
        common = {
            "plot_name": "Plot 4",
            "source_family": safe_text(row.get("source_dataset")) or safe_text(row.get("project")) or "replication_pairs",
            "source_file": str(REPLICATION_ALL.relative_to(ROOT)),
            "row_unit": "replication_pair_side",
            "source_status": "integrated_live_pair",
            "row_label": safe_text(row.get("outcome")) or safe_text(row.get("original_title")) or pair_id,
        }
        if pd.notna(row["D_original"]) and pd.notna(row["N_original"]) and row["D_original"] > 0 and row["N_original"] > 0:
            rows.append(
                {
                    **common,
                    "point_id": f"replication::{pair_id}::original",
                    "source_layer": "replication_pair_original",
                    "side": "original",
                    "D": float(row["D_original"]),
                    "N": float(row["N_original"]),
                }
            )
        if (
            pd.notna(row["D_replication"])
            and pd.notna(row["N_replication"])
            and row["D_replication"] > 0
            and row["N_replication"] > 0
        ):
            rows.append(
                {
                    **common,
                    "point_id": f"replication::{pair_id}::followup",
                    "source_layer": "replication_pair_followup",
                    "side": "followup",
                    "D": float(row["D_replication"]),
                    "N": float(row["N_replication"]),
                }
            )

    pub = pd.read_csv(PUBLISHED_PAPERS)
    pub["D_median"] = numeric_series(pub["D_median"]).abs()
    pub["N_median"] = numeric_series(pub["N_median"])
    pub = pub[(pub["D_median"] > 0) & (pub["N_median"] > 0)].copy()
    for idx, row in pub.iterrows():
        unit_id = safe_text(row.get("unit_id")) or f"published_candidate_{idx}"
        source_corpus = safe_text(row.get("source_corpus")) or "published_candidate_papers"
        is_original = as_bool(row.get("published_original_candidate")) and not as_bool(row.get("comparator_only"))
        rows.append(
            {
                "plot_name": "Plot 4",
                "point_id": f"published::{source_corpus}::{unit_id}",
                "source_layer": "published_candidate_paper",
                "source_family": source_corpus,
                "source_file": str(PUBLISHED_PAPERS.relative_to(ROOT)),
                "row_unit": safe_text(row.get("collapse_unit")) or "paper_or_study_unit",
                "source_status": "published_original_candidate" if is_original else "published_comparator_or_other_candidate",
                "row_label": safe_text(row.get("title")) or unit_id,
                "side": "paper",
                "D": float(row["D_median"]),
                "N": float(row["N_median"]),
            }
        )

    for _, row in prereg.iterrows():
        rows.append(
            {
                "plot_name": "Plot 4",
                "point_id": f"preregistered::{safe_text(row.get('point_id'))}",
                "source_layer": "preregistered_confirmatory_result",
                "source_family": safe_text(row.get("source_family")),
                "source_file": safe_text(row.get("source_file")),
                "row_unit": safe_text(row.get("row_unit")),
                "source_status": "included_preregistered_result",
                "row_label": safe_text(row.get("row_label")),
                "side": "result",
                "D": float(row["D"]),
                "N": float(row["N"]),
            }
        )

    staged = normalize_staged_harvest_dn_rows(live_pair_ids)
    if not staged.empty:
        for _, row in staged.iterrows():
            rows.append(
                {
                    "plot_name": "Plot 4",
                    "point_id": safe_text(row.get("point_id")),
                    "source_layer": safe_text(row.get("source_layer")),
                    "source_family": safe_text(row.get("source_family")),
                    "source_file": safe_text(row.get("source_file")),
                    "row_unit": safe_text(row.get("row_unit")),
                    "source_status": safe_text(row.get("source_status")),
                    "row_label": safe_text(row.get("row_label")),
                    "side": safe_text(row.get("side")),
                    "D": float(row["D"]),
                    "N": float(row["N"]),
                }
            )

    df = pd.DataFrame(rows)
    df["D"] = numeric_series(df["D"]).abs()
    df["N"] = numeric_series(df["N"])
    df = df[(df["D"] > 0) & (df["N"] > 0)].copy()
    df["log10_N"] = np.log10(df["N"])
    df["log10_D"] = np.log10(df["D"])
    df["two_sample_p05_boundary_D"] = 2 * Z_05 / np.sqrt(df["N"])
    df["above_two_sample_p05_curve"] = df["D"] >= df["two_sample_p05_boundary_D"]
    df.to_csv(ALL_SOURCE_DN_ROWS, index=False)
    return df


def figure1_intro_examples() -> tuple[pd.DataFrame, pd.DataFrame]:
    examples = pd.read_csv(INTRO_EXAMPLES).fillna("")
    examples["include_in_figure1"] = examples["include_in_figure1"].map(as_bool)
    included = examples[examples["include_in_figure1"]].copy()
    included["n"] = pd.to_numeric(included["n"], errors="coerce")
    included["d"] = pd.to_numeric(included["d"], errors="coerce")
    included["label_dx"] = pd.to_numeric(included["label_dx"], errors="coerce")
    included["label_dy"] = pd.to_numeric(included["label_dy"], errors="coerce")
    included = included.dropna(subset=["n", "d", "label_dx", "label_dy"])
    return examples, included


def draw_publication_boundary(out_path: Path) -> None:
    xs = np.logspace(1, 4, 400)
    boundary = 2 * Z_05 / np.sqrt(xs)
    _, included_examples = figure1_intro_examples()
    ymax = 4.0 if float(included_examples["d"].max()) > 2.0 else 2.0

    fig, ax = plt.subplots(figsize=(8.2, 5.8), dpi=180)
    ax.fill_between(xs, boundary, ymax, color="#e8f5ee", alpha=0.95)
    ax.fill_between(xs, 0.01, boundary, color="#fceaea", alpha=0.95)
    ax.plot(xs, boundary, color="#1a1a1a", lw=2.0)
    ax.scatter(
        included_examples["n"],
        included_examples["d"],
        s=58,
        facecolors=(42 / 255, 77 / 255, 122 / 255, 0.25),
        edgecolors="#2a4d7a",
        lw=1.8,
        zorder=4,
    )

    for row in included_examples.itertuples(index=False):
        ax.annotate(
            str(row.plot_label).replace("\\n", "\n"),
            (float(row.n), float(row.d)),
            xytext=(float(row.label_dx), float(row.label_dy)),
            textcoords="offset points",
            fontsize=8.2,
            ha=str(row.label_ha),
            va="center",
            color="#1a1a1a",
        )

    ax.axhline(0.2, color="#777777", lw=1, linestyle="--")
    ax.axvline(300, color="#777777", lw=1, linestyle="--")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlim(10, 10000)
    ax.set_ylim(0.01, ymax)
    ax.set_xticks([10, 100, 1000, 10000])
    ax.set_xticklabels(["10", "100", "1,000", "10K"])
    y_ticks = [4.0, 2.0, 1.0, 0.5, 0.2, 0.1, 0.05, 0.02, 0.01] if ymax > 2.0 else [2.0, 1.0, 0.5, 0.2, 0.1, 0.05, 0.02, 0.01]
    ax.set_yticks(y_ticks)
    ax.set_yticklabels([f"{tick:.1f}" if tick >= 1.0 else f"{tick:g}" for tick in y_ticks])
    ax.set_xlabel("Sample size (log scale)")
    ax.set_ylabel("Reported effect size (Cohen's d, log scale)")
    ax.set_title("The p < 0.05 publication boundary", fontweight="bold")
    ax.grid(True, which="major", alpha=0.18, linestyle=":")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    ax.text(
        0.80,
        0.41,
        "p < 0.05 effect sizes that do get published ↗",
        transform=ax.transAxes,
        rotation=-23,
        ha="center",
        va="center",
        fontsize=8.4,
        fontweight="bold",
        color="#0d6650",
    )
    ax.text(
        0.80,
        0.36,
        "↙ p > 0.05 effect sizes that don't get published",
        transform=ax.transAxes,
        rotation=-23,
        ha="center",
        va="center",
        fontsize=8.4,
        fontweight="bold",
        color="#a03030",
    )

    quad_kwargs = dict(transform=ax.transAxes, fontsize=7.8, fontweight="bold", color="#505050")
    ax.text(0.015, 0.98, "Unlikely effects + weak evidence", ha="left", va="top", **quad_kwargs)
    ax.text(0.985, 0.98, "Unlikely effects + strong evidence", ha="right", va="top", **quad_kwargs)
    ax.text(0.015, 0.02, "Common effects + weak evidence", ha="left", va="bottom", **quad_kwargs)
    ax.text(0.985, 0.02, "Common effects + strong evidence", ha="right", va="bottom", **quad_kwargs)
    fig.savefig(out_path, bbox_inches="tight")
    plt.close(fig)


def draw_prior_comparison(out_path: Path) -> None:
    x = np.linspace(-1.8, 1.8, 600)
    gelman = stats.norm.pdf(x, loc=0, scale=0.35)
    flat = np.full_like(x, 0.22)
    fig = plt.figure(figsize=(8.2, 6.6), dpi=180)
    gs = fig.add_gridspec(2, 1, height_ratios=[3.0, 1.45], hspace=0.34)
    ax = fig.add_subplot(gs[0, 0])
    ax_bottom = fig.add_subplot(gs[1, 0])

    ax.plot(x, flat, color="#c44a1e", lw=2.3, label="implicit flat/no-shrinkage prior")
    ax.fill_between(x, flat, color="#c44a1e", alpha=0.10)
    ax.plot(x, gelman, color="#1456a0", lw=2.5, label="Normal(0, 0.35)")
    ax.fill_between(x, gelman, color="#1456a0", alpha=0.12)
    ax.axvline(0.8, color="#555555", lw=1.0, linestyle="--")
    ax.text(0.82, max(gelman) * 0.85, "d = 0.8", fontsize=9, color="#555555", ha="left")
    ax.set_xlabel("True effect size d")
    ax.set_ylabel("Prior density")
    ax.set_title("What you implicitly believe before the data", fontweight="bold")
    ax.legend(frameon=False, loc="upper left")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    repl = pd.read_csv(REPLICATION_CSV)
    d_repl = pd.to_numeric(repl["D_replication"], errors="coerce").dropna().abs()
    linear_d_max = 3.0
    linear_bin_width = 0.1
    linear_bins = np.arange(0, linear_d_max + linear_bin_width, linear_bin_width)
    d_repl_linear = d_repl.clip(lower=0, upper=linear_d_max)
    d_repl_med = float(d_repl.median()) if len(d_repl) else math.nan

    ax_bottom.hist(
        d_repl_linear,
        bins=linear_bins,
        density=True,
        histtype="stepfilled",
        color="#1456a0",
        alpha=0.14,
    )
    ax_bottom.hist(
        d_repl_linear,
        bins=linear_bins,
        density=True,
        histtype="step",
        linewidth=1.6,
        color="#1456a0",
        label="Larger-N replications",
    )
    ax_bottom.set_xlim(0, linear_d_max)
    linear_ticks = np.arange(0, linear_d_max + 0.001, 0.5)
    linear_tick_labels = [f"{tick:g}" for tick in linear_ticks]
    linear_tick_labels[-1] = "3+"
    ax_bottom.set_xticks(linear_ticks)
    ax_bottom.set_xticklabels(linear_tick_labels)
    ax_bottom.set_ylabel("Density")
    ax_bottom.set_xlabel("Replication effect size magnitude (|Cohen's d|, linear scale)", fontweight="bold")

    if np.isfinite(d_repl_med):
        d_repl_med_linear = float(np.clip(d_repl_med, 0.0, linear_d_max))
        ax_bottom.axvline(
            d_repl_med_linear,
            color="#1456a0",
            lw=1.0,
            linestyle="--",
            alpha=0.9,
            zorder=1,
        )
        bottom_label_transform = blended_transform_factory(ax_bottom.transData, ax_bottom.transAxes)
        ax_bottom.annotate(
            rf"$\tilde{{x}}={d_repl_med:.2f}$",
            xy=(d_repl_med_linear, 1.0),
            xycoords=bottom_label_transform,
            xytext=(0, 2),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=7.8,
            color="#1456a0",
            clip_on=False,
        )

    ax_bottom.legend(
        loc="upper right",
        bbox_to_anchor=(0.995, 0.995),
        frameon=False,
        fontsize=7.8,
        handlelength=2.2,
        borderaxespad=0.15,
    )
    ax_bottom.grid(False)
    for spine in ["top", "right"]:
        ax_bottom.spines[spine].set_visible(False)

    fig.savefig(out_path, bbox_inches="tight")
    plt.close(fig)


def draw_published_distribution(out_path: Path) -> dict[str, float | int]:
    stats_dict = published_stats()
    papers = pd.read_csv(PUBLISHED_PAPERS)
    main = papers[papers["published_original_candidate"].astype(bool) & ~papers["comparator_only"].astype(bool)].copy()
    main = main[(main["D_median"] > 0) & (main["N_median"] > 0)].copy()
    values = main["D_median"].clip(lower=0, upper=3)
    fig, ax = plt.subplots(figsize=(8.2, 4.8), dpi=180)
    ax.hist(values, bins=np.arange(0, 3.05, 0.1), density=True, histtype="stepfilled", color="#c44a1e", alpha=0.22)
    ax.hist(values, bins=np.arange(0, 3.05, 0.1), density=True, histtype="step", color="#c44a1e", lw=2.0)
    for x, label in [(0.2, "small"), (0.5, "medium"), (0.8, "large")]:
        ax.axvline(x, color="#777777", lw=1.0, linestyle=":")
        ax.text(x, ax.get_ylim()[1] * 0.94, f"{label}\nd={x:g}", ha="center", va="top", fontsize=8, color="#555555")
    ax.axvline(stats_dict["median_d"], color="#c44a1e", lw=1.4, linestyle="--")
    ax.text(
        stats_dict["median_d"] + 0.03,
        ax.get_ylim()[1] * 0.72,
        f"median D = {stats_dict['median_d']:.2f}",
        color="#a33d18",
        fontsize=9,
        fontweight="bold",
    )
    ax.set_xlim(0, 3)
    ax.set_xlabel("Reported effect size D (paper median, clipped at 3)")
    ax.set_ylabel("Density")
    ax.set_title("Published focal-result papers as a distribution of effect sizes", fontweight="bold")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    fig.savefig(out_path, bbox_inches="tight")
    plt.close(fig)
    return stats_dict


def draw_preregistered_results(out_path: Path) -> dict[str, float | int]:
    df = normalize_preregistered_results()
    colors = {
        "psychology and health": "#2a4d7a",
        "education": "#b56b00",
        "political science": "#0b6e5f",
        "economics and finance": "#7a4d9b",
        "sociology and criminology": "#8b6f21",
        "business": "#c44a1e",
        "preclinical biology": "#6f6a1f",
        "clinical medicine": "#9a6324",
        "mixed social/behavioral science": "#555555",
    }
    markers = {
        "psychology and health": "o",
        "education": "s",
        "political science": "^",
        "economics and finance": "D",
        "sociology and criminology": "P",
        "business": "X",
        "preclinical biology": "*",
        "clinical medicine": "h",
        "mixed social/behavioral science": "v",
    }

    x_min_plot = 10
    x_max_plot = DN_AXIS_X_CAP
    y_min_plot = DN_AXIS_Y_MIN
    y_max_plot = DN_AXIS_Y_MAX
    xs = np.logspace(np.log10(x_min_plot), np.log10(x_max_plot), 400)

    fig = plt.figure(figsize=(10.5, 9.3), dpi=180)
    gs = fig.add_gridspec(2, 1, height_ratios=[5.1, 1.55], hspace=0.34)
    ax = fig.add_subplot(gs[0, 0])
    ax_hist = fig.add_subplot(gs[1, 0])

    for field, group in groups_by_descending_count(df, "field"):
        color = colors.get(field, "#444444")
        ax.scatter(
            group["N"],
            group["D"],
            s=34,
            marker=markers.get(field, "o"),
            color=color,
            edgecolors="none",
            alpha=point_alpha_for_count(len(group), base=0.62),
            rasterized=True,
            zorder=3,
        )

    median_d = float(df["D"].median())
    median_n = float(df["N"].median())
    z10 = 1.6448536269514722
    pct_above_p10 = 100 * float((df["D"] >= (2 * z10 / np.sqrt(df["N"]))).mean())

    medians = (
        df.groupby("field", sort=False)
        .agg(
            field_label=("field_label", "first"),
            median_N=("N", "median"),
            median_D=("D", "median"),
            n_rows=("D", "size"),
            n_sources=("source_family", "nunique"),
        )
        .reset_index()
    )

    for z, label, style, x_label_target, y_multiplier in [
        (1.6448536269514722, "p=.10", ":", 95_000.0, 0.95),
        (1.96, "p=.05", "--", 140_000.0, 1.05),
        (2.5758293035489004, "p=.01", "-.", 210_000.0, 1.15),
    ]:
        ax.plot(
            xs,
            2 * z / np.sqrt(xs),
            style,
            color="#444444",
            linewidth=2.2,
            alpha=0.82,
            zorder=6,
        )
        x_label = min(max(x_min_plot * 12, x_label_target), x_max_plot / 1.7)
        y_label = max(y_min_plot * 1.1, 2 * z / np.sqrt(x_label) * y_multiplier)
        ax.text(
            x_label,
            y_label,
            label,
            color="#444444",
            fontsize=9,
            ha="left",
            va="bottom",
            rotation=-28,
            rotation_mode="anchor",
            bbox=dict(facecolor="white", edgecolor="none", alpha=0.78, pad=0.35),
            clip_on=True,
            zorder=7,
        )

    for row in medians.sort_values("n_rows", ascending=False).itertuples(index=False):
        color = colors.get(row.field, "#444444")
        marker = markers.get(row.field, "o")
        ax.scatter(
            row.median_N,
            row.median_D,
            s=250,
            marker=marker,
            facecolors="white",
            edgecolors="#111111",
            linewidths=3.1,
            zorder=20,
        )
        ax.scatter(
            row.median_N,
            row.median_D,
            s=165,
            marker=marker,
            facecolors="white",
            edgecolors=color,
            linewidths=2.3,
            zorder=21,
        )

    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlim(x_min_plot, x_max_plot)
    ax.set_ylim(y_min_plot, y_max_plot)
    x_ticks = [10, 100, 1_000, 10_000, 100_000]
    y_ticks = [0.02, 0.05, 0.1, 0.2, 0.5, 1, 2, 5]
    ax.xaxis.set_major_locator(FixedLocator(x_ticks))
    ax.xaxis.set_major_formatter(FixedFormatter(["10", "100", "1k", "10k", "100k"]))
    ax.xaxis.set_minor_formatter(NullFormatter())
    ax.yaxis.set_major_locator(FixedLocator(y_ticks))
    ax.yaxis.set_major_formatter(FixedFormatter(["0.02", "0.05", "0.1", "0.2", "0.5", "1", "2", "5"]))
    ax.yaxis.set_minor_formatter(NullFormatter())
    ax.set_xlabel("Sample size N (result row, log scale)")
    ax.set_ylabel("Effect size magnitude D (log scale)")
    ax.set_title(
        "Preregistered Confirmatory Results: Sample Size and Effect Size",
        fontsize=15,
        fontweight="bold",
        pad=28,
    )
    ax.annotate(
        (
            f"{len(df):,} rows across {df['field'].nunique():,} fields | "
            f"Sig. {pct_above_p10:.0f}% (p≤.10) | "
            f"median D = {median_d:.2f}"
        ),
        xy=(0.5, 1.0),
        xycoords="axes fraction",
        xytext=(0, 2),
        textcoords="offset points",
        ha="center",
        va="bottom",
        fontsize=13,
        color="#333333",
    )
    legend_handles = []
    for row in medians.sort_values("n_rows", ascending=False).itertuples(index=False):
        color = colors.get(row.field, "#444444")
        marker = markers.get(row.field, "o")
        legend_handles.append(
            Line2D(
                [0],
                [0],
                marker=marker,
                color="none",
                markerfacecolor=color,
                markeredgecolor="none",
                markersize=8,
                alpha=point_alpha_for_count(int(row.n_rows), base=0.78),
                label=f"{safe_text(row.field_label)} (n={fmt_int(row.n_rows)}, {fmt_int(row.n_sources)} source families)",
            )
        )
    legend_handles.append(
        Line2D(
            [0],
            [0],
            marker="o",
            color="none",
            markerfacecolor="white",
            markeredgecolor="#333333",
            markeredgewidth=1.6,
            markersize=8,
            label="Hollow marker = field median",
        )
    )
    ax.legend(
        handles=legend_handles,
        loc="upper right",
        frameon=False,
        fontsize=9.4,
        borderpad=0.2,
        handletextpad=0.5,
        labelspacing=0.45,
    )
    ax.text(
        0.01,
        -0.105,
        (
            "Both panels use the same preregistered confirmatory result rows; "
            "axes are capped at N=100k and D=0.02-5 for comparability; statistics use all rows."
        ),
        transform=ax.transAxes,
        fontsize=8.8,
        color="#333333",
        ha="left",
    )
    ax.grid(True, which="major", alpha=0.18, linestyle=":")
    ax.grid(True, which="minor", alpha=0.06, linestyle=":")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    linear_d_max = 3.0
    linear_bin_width = 0.1
    linear_bins = np.arange(0, linear_d_max + linear_bin_width, linear_bin_width)
    values = df["D"].dropna()
    clipped = values.clip(lower=0, upper=linear_d_max)
    if len(clipped):
        ax_hist.hist(
            clipped,
            bins=linear_bins,
            density=True,
            histtype="stepfilled",
            color="#0b6e5f",
            alpha=0.18,
            label=f"Preregistered result rows (n={len(values):,})",
        )
        ax_hist.hist(
            clipped,
            bins=linear_bins,
            density=True,
            histtype="step",
            linewidth=1.6,
            color="#0b6e5f",
        )
    for x, label in [(0.2, "small"), (0.5, "medium"), (0.8, "large")]:
        ax_hist.axvline(x, color="#777777", lw=0.9, linestyle=":", alpha=0.75)
        ax_hist.text(
            x,
            0.94,
            f"{label}\nd={x:g}",
            transform=blended_transform_factory(ax_hist.transData, ax_hist.transAxes),
            ha="center",
            va="top",
            fontsize=7.6,
            color="#555555",
        )
    median_d_clip = float(np.clip(median_d, 0.0, linear_d_max))
    ax_hist.axvline(median_d_clip, color="#0b6e5f", lw=1.1, linestyle="--")
    ax_hist.annotate(
        rf"$\tilde{{D}}={median_d:.2f}$",
        xy=(median_d_clip, 1.0),
        xycoords=blended_transform_factory(ax_hist.transData, ax_hist.transAxes),
        xytext=(0, 2),
        textcoords="offset points",
        ha="center",
        va="bottom",
        fontsize=7.8,
        color="#075346",
        clip_on=False,
    )
    ax_hist.set_xlim(0, linear_d_max)
    linear_ticks = np.arange(0, linear_d_max + 0.001, 0.5)
    linear_tick_labels = [f"{tick:g}" for tick in linear_ticks]
    linear_tick_labels[-1] = "3+"
    ax_hist.set_xticks(linear_ticks)
    ax_hist.set_xticklabels(linear_tick_labels)
    ax_hist.set_ylabel("Density")
    ax_hist.set_xlabel("Effect size magnitude D (linear scale, clipped at 3)")
    ax_hist.legend(frameon=False, loc="upper right", fontsize=8, handlelength=2.3)
    ax_hist.grid(False)
    for spine in ["top", "right"]:
        ax_hist.spines[spine].set_visible(False)

    fig.savefig(out_path, bbox_inches="tight")
    plt.close(fig)
    return {
        "n_rows": len(df),
        "n_sources": int(df["field"].nunique()),
        "median_d": median_d,
        "median_n": median_n,
        "pct_above_p05": 100 * float(df["above_two_sample_p05_curve"].mean()),
        "pct_above_p10": pct_above_p10,
    }


def draw_preregistered_sensitivity_sidecar(out_path: Path) -> dict[str, float | int]:
    df = normalize_preregistered_sensitivity_sidecar_rows()
    colors = {
        "ClinicalTrials.gov registry-result D/N comparator": "#2f6f9f",
        "Brodeur et al. 2024 preregistered/PAP economics table tests": "#b86b2b",
    }
    markers = {
        "ClinicalTrials.gov registry-result D/N comparator": "o",
        "Brodeur et al. 2024 preregistered/PAP economics table tests": "^",
    }

    if df.empty:
        fig, ax = plt.subplots(figsize=(9, 5), dpi=180)
        ax.text(0.5, 0.5, "No sensitivity sidecar rows available", ha="center", va="center")
        ax.axis("off")
        fig.savefig(out_path, bbox_inches="tight")
        plt.close(fig)
        return {
            "n_rows": 0,
            "n_sources": 0,
            "median_d": float("nan"),
            "median_n": float("nan"),
            "pct_above_p10": float("nan"),
        }

    x_min, x_max, y_min, y_max = sidecar_log_axis_bounds(df, x_cap=DN_AXIS_X_CAP)
    xs = np.logspace(np.log10(x_min), np.log10(x_max), 500)

    fig = plt.figure(figsize=(10.5, 8.7), dpi=180)
    gs = fig.add_gridspec(2, 1, height_ratios=[5.1, 1.45], hspace=0.32)
    ax = fig.add_subplot(gs[0, 0])
    ax_hist = fig.add_subplot(gs[1, 0])

    draw_general_results_thresholds(ax, xs, x_min=x_min, x_max=x_max, y_min=y_min)

    medians = (
        df.groupby("source_family", sort=False)
        .agg(
            source_label=("source_label", "first"),
            median_N=("N", "median"),
            median_D=("D", "median"),
            n_rows=("D", "size"),
        )
        .reset_index()
    )
    for source_family, group in groups_by_descending_count(df, "source_family"):
        color = colors.get(source_family, "#444444")
        ax.scatter(
            group["N"],
            group["D"],
            s=10 if "ClinicalTrials.gov" in source_family else 13,
            marker=markers.get(source_family, "o"),
            color=color,
            edgecolors="none",
            alpha=0.18 if "ClinicalTrials.gov" in source_family else point_alpha_for_count(len(group), base=0.42),
            rasterized=True,
            zorder=3,
        )

    for row in medians.sort_values("n_rows", ascending=False).itertuples(index=False):
        color = colors.get(row.source_family, "#444444")
        ax.scatter(
            row.median_N,
            row.median_D,
            s=140,
            marker=markers.get(row.source_family, "o"),
            facecolors="white",
            edgecolors=color,
            linewidths=2.0,
            zorder=5,
        )

    pct_above_p10 = 100 * float((df["D"] >= (2 * 1.6448536269514722 / np.sqrt(df["N"]))).mean())
    apply_general_results_axes(
        ax,
        x_min=x_min,
        x_max=x_max,
        y_min=y_min,
        y_max=y_max,
        xlabel="Sample size N (log scale)",
        ylabel="Effect size D (log scale)",
    )
    ax.set_title(
        "Registry and Table-Test Comparator Rows",
        fontsize=15,
        fontweight="bold",
        pad=28,
    )
    ax.annotate(
        (
            f"{len(df):,} comparator rows | p≤.10 proxy {pct_above_p10:.0f}% | "
            f"median D = {df['D'].median():.2f}"
        ),
        xy=(0.5, 1.0),
        xycoords="axes fraction",
        xytext=(0, 2),
        textcoords="offset points",
        ha="center",
        va="bottom",
        fontsize=13,
        color="#333333",
    )

    medians["pct_above_p10"] = medians["source_family"].map(
        df.groupby("source_family").apply(
            lambda g: 100 * float((g["D"] >= (2 * 1.6448536269514722 / np.sqrt(g["N"]))).mean())
        )
    )
    ax.legend(
        handles=[
            Line2D(
                [0],
                [0],
                marker=markers.get(row.source_family, "o"),
                color="none",
                markerfacecolor=colors.get(row.source_family, "#444444"),
                markeredgecolor="none",
                markersize=8,
                alpha=0.8,
                label=f"{safe_text(row.source_label)} (n={fmt_int(row.n_rows)}, p≤.10 proxy {row.pct_above_p10:.0f}%)",
            )
            for row in medians.sort_values("n_rows", ascending=False).itertuples(index=False)
        ]
        + [
            Line2D(
                [0],
                [0],
                marker="o",
                color="none",
                markerfacecolor="white",
                markeredgecolor="#333333",
                markeredgewidth=1.6,
                markersize=8,
                label="Hollow marker = source median",
            )
        ],
        loc="upper right",
        frameon=False,
        fontsize=9.3,
        borderpad=0.2,
        handletextpad=0.5,
        labelspacing=0.45,
    )
    ax.text(
        0.01,
        -0.105,
        (
            "Both panels use D/N rows that fail the strict Figure 3 gate; "
            "axes are capped at N=100k and D=0.02-5 for comparability; statistics use all rows."
        ),
        transform=ax.transAxes,
        fontsize=8.8,
        color="#333333",
        ha="left",
    )

    linear_d_max = 3.0
    linear_bin_width = 0.1
    linear_bins = np.arange(0, linear_d_max + linear_bin_width, linear_bin_width)
    for source_family, group in groups_by_descending_count(df, "source_family"):
        color = colors.get(source_family, "#444444")
        ax_hist.hist(
            group["D"].clip(lower=0, upper=linear_d_max),
            bins=linear_bins,
            density=True,
            histtype="stepfilled",
            color=color,
            alpha=0.18,
        )
        ax_hist.hist(
            group["D"].clip(lower=0, upper=linear_d_max),
            bins=linear_bins,
            density=True,
            histtype="step",
            linewidth=1.3,
            color=color,
            label=safe_text(group["source_label"].iloc[0]),
        )
    draw_general_results_histogram_references(ax_hist, median_d=float(df["D"].median()), median_color="#444444")
    finish_general_results_histogram(ax_hist)
    ax_hist.legend(frameon=False, loc="upper right", fontsize=8, handlelength=2.3)

    fig.savefig(out_path, bbox_inches="tight")
    plt.close(fig)
    return {
        "n_rows": len(df),
        "n_sources": int(df["source_family"].nunique()),
        "median_d": float(df["D"].median()),
        "median_n": float(df["N"].median()),
        "pct_above_p10": 100 * float((df["D"] >= (2 * 1.6448536269514722 / np.sqrt(df["N"]))).mean()),
    }


def draw_ctgov_primary_randomized_sidecar(out_path: Path) -> dict[str, float | int]:
    df = normalize_ctgov_primary_randomized_sidecar_rows()
    if df.empty:
        fig, ax = plt.subplots(figsize=(9, 5), dpi=180)
        ax.text(0.5, 0.5, "No CT.gov primary randomized sidecar rows available", ha="center", va="center")
        ax.axis("off")
        fig.savefig(out_path, bbox_inches="tight")
        plt.close(fig)
        return {"n_rows": 0, "median_d": float("nan"), "median_n": float("nan")}

    x_min, x_max, y_min, y_max = sidecar_log_axis_bounds(df, x_cap=DN_AXIS_X_CAP)
    xs = np.logspace(np.log10(x_min), np.log10(x_max), 500)

    fig = plt.figure(figsize=(10.5, 8.7), dpi=180)
    gs = fig.add_gridspec(2, 1, height_ratios=[5.1, 1.45], hspace=0.32)
    ax = fig.add_subplot(gs[0, 0])
    ax_hist = fig.add_subplot(gs[1, 0])

    draw_general_results_thresholds(ax, xs, x_min=x_min, x_max=x_max, y_min=y_min)

    color = "#2f6f9f"
    phase2plus = df["phase_2plus_flag"].astype(bool) if "phase_2plus_flag" in df.columns else pd.Series(True, index=df.index)
    if (~phase2plus).sum() > 0:
        ax.scatter(
            df.loc[~phase2plus, "N"],
            df.loc[~phase2plus, "D"],
            s=10,
            color="#8aa9b5",
            edgecolors="none",
            alpha=0.24,
            rasterized=True,
            label=f"Other/unspecified phase (n={fmt_int((~phase2plus).sum())})",
            zorder=3,
        )
    ax.scatter(
        df.loc[phase2plus, "N"],
        df.loc[phase2plus, "D"],
        s=10,
        color=color,
        edgecolors="none",
        alpha=0.30,
        rasterized=True,
        label=f"Phase 2+ trials (n={fmt_int(phase2plus.sum())})",
        zorder=4,
    )
    ax.scatter(
        df["N"].median(),
        df["D"].median(),
        s=150,
        facecolors="white",
        edgecolors=color,
        linewidths=2.1,
        zorder=6,
    )

    pct_above_p10 = 100 * float((df["D"] >= (2 * 1.6448536269514722 / np.sqrt(df["N"]))).mean())
    apply_general_results_axes(
        ax,
        x_min=x_min,
        x_max=x_max,
        y_min=y_min,
        y_max=y_max,
        xlabel="Sample size N (log scale)",
        ylabel="Effect size D (log scale)",
    )
    ax.set_title("ClinicalTrials.gov Phase-2+ Primary-Outcome Comparators", fontsize=15, fontweight="bold", pad=28)
    ax.annotate(
        (
            f"{len(df):,} one-row-per-trial registry rows | "
            f"p≤.10 proxy {pct_above_p10:.0f}% | median D = {df['D'].median():.2f}"
        ),
        xy=(0.5, 1.0),
        xycoords="axes fraction",
        xytext=(0, 2),
        textcoords="offset points",
        ha="center",
        va="bottom",
        fontsize=13,
        color="#333333",
    )
    ax.legend(
        handles=[
            Line2D(
                [0],
                [0],
                marker="o",
                color="none",
                markerfacecolor=color,
                markeredgecolor="none",
                markersize=8,
                alpha=0.8,
                label=f"Phase 2+ trials (n={fmt_int(phase2plus.sum())}, p≤.10 proxy {pct_above_p10:.0f}%)",
            ),
            Line2D(
                [0],
                [0],
                marker="o",
                color="none",
                markerfacecolor="white",
                markeredgecolor="#333333",
                markeredgewidth=1.6,
                markersize=8,
                label="Hollow marker = median",
            ),
        ],
        frameon=False,
        loc="upper right",
        fontsize=10,
        borderpad=0.2,
        handletextpad=0.5,
        labelspacing=0.45,
    )
    ax.text(
        0.01,
        -0.105,
        (
            "One phase-2+ randomized primary registry outcome per trial; "
            "axes are capped at N=100k and D=0.02-5 for comparability; statistics use all rows."
        ),
        transform=ax.transAxes,
        fontsize=8.8,
        color="#333333",
        ha="left",
    )

    linear_d_max = 3.0
    linear_bin_width = 0.1
    linear_bins = np.arange(0, linear_d_max + linear_bin_width, linear_bin_width)
    ax_hist.hist(
        df["D"].clip(lower=0, upper=linear_d_max),
        bins=linear_bins,
        density=True,
        histtype="stepfilled",
        color=color,
        alpha=0.18,
    )
    ax_hist.hist(
        df["D"].clip(lower=0, upper=linear_d_max),
        bins=linear_bins,
        density=True,
        histtype="step",
        linewidth=1.4,
        color=color,
        label=f"CT.gov phase-2+ primary rows (n={len(df):,})",
    )
    draw_general_results_histogram_references(ax_hist, median_d=float(df["D"].median()), median_color=color)
    finish_general_results_histogram(ax_hist)
    ax_hist.legend(frameon=False, loc="upper right", fontsize=8, handlelength=2.3)

    fig.savefig(out_path, bbox_inches="tight")
    plt.close(fig)
    return {
        "n_rows": len(df),
        "median_d": float(df["D"].median()),
        "median_n": float(df["N"].median()),
        "phase2plus_rows": int(phase2plus.sum()),
    }


def draw_ctgov_api_registered_trial_medians(out_path: Path) -> dict[str, float | int]:
    if not CTGOV_API_REGISTERED_TRIAL_MEDIANS.exists():
        fig, ax = plt.subplots(figsize=(9, 5), dpi=180)
        ax.text(0.5, 0.5, "No CT.gov API registered-result trial medians available", ha="center", va="center")
        ax.axis("off")
        fig.savefig(out_path, bbox_inches="tight")
        plt.close(fig)
        return {"n_rows": 0, "median_d": float("nan"), "median_n": float("nan")}

    df = pd.read_csv(CTGOV_API_REGISTERED_TRIAL_MEDIANS)
    df["D"] = numeric_series(df["D"])
    df["N"] = numeric_series(df["N"])
    df = df[(df["D"] > 0) & (df["N"] > 0)].copy()
    if df.empty:
        fig, ax = plt.subplots(figsize=(9, 5), dpi=180)
        ax.text(0.5, 0.5, "No CT.gov API registered-result trial medians available", ha="center", va="center")
        ax.axis("off")
        fig.savefig(out_path, bbox_inches="tight")
        plt.close(fig)
        return {"n_rows": 0, "median_d": float("nan"), "median_n": float("nan")}

    row_level_n = 0
    primary_row_n = 0
    direct_row_n = 0
    if CTGOV_API_REGISTERED_ROWS.exists():
        ctgov_rows = pd.read_csv(CTGOV_API_REGISTERED_ROWS, usecols=["outcome_type", "conversion_method"])
        row_level_n = len(ctgov_rows)
        primary_row_n = int(ctgov_rows["outcome_type"].eq("PRIMARY").sum())
        direct_row_n = int(
            (~ctgov_rows["conversion_method"].eq("two_sided_p_value_proxy_with_api_group_denominators")).sum()
        )

    x_min, x_max, y_min, y_max = sidecar_log_axis_bounds(df, x_cap=DN_AXIS_X_CAP)
    xs = np.logspace(np.log10(x_min), np.log10(x_max), 500)

    fig = plt.figure(figsize=(10.5, 8.7), dpi=180)
    gs = fig.add_gridspec(2, 1, height_ratios=[5.1, 1.45], hspace=0.32)
    ax = fig.add_subplot(gs[0, 0])
    ax_hist = fig.add_subplot(gs[1, 0])

    draw_general_results_thresholds(ax, xs, x_min=x_min, x_max=x_max, y_min=y_min)
    color = "#8b3f1f"
    primary_any = df["primary_rows"].fillna(0) > 0 if "primary_rows" in df.columns else pd.Series(True, index=df.index)
    if (~primary_any).sum() > 0:
        ax.scatter(
            df.loc[~primary_any, "N"],
            df.loc[~primary_any, "D"],
            s=9,
            color="#8c8c8c",
            edgecolors="none",
            alpha=0.22,
            rasterized=True,
            label=f"secondary/other-only trial medians (n={fmt_int((~primary_any).sum())})",
            zorder=3,
        )
    ax.scatter(
        df.loc[primary_any, "N"],
        df.loc[primary_any, "D"],
        s=10,
        color=color,
        edgecolors="none",
        alpha=0.30,
        rasterized=True,
        label=f"trial medians with primary rows (n={fmt_int(primary_any.sum())})",
        zorder=4,
    )
    ax.scatter(
        df["N"].median(),
        df["D"].median(),
        s=150,
        facecolors="white",
        edgecolors=color,
        linewidths=2.1,
        zorder=6,
    )

    pct_above_p10 = 100 * float((df["D"] >= (2 * 1.6448536269514722 / np.sqrt(df["N"]))).mean())
    apply_general_results_axes(
        ax,
        x_min=x_min,
        x_max=x_max,
        y_min=y_min,
        y_max=y_max,
        xlabel="Sample size N (log scale)",
        ylabel="Effect size D (log scale)",
    )
    ax.set_title("ClinicalTrials.gov Registered Outcome-Result Trial Medians", fontsize=15, fontweight="bold", pad=28)
    ax.annotate(
        (
            f"{len(df):,} trial medians from {fmt_int(row_level_n)} registered outcome rows | "
            f"{fmt_int(primary_row_n)} primary rows | median D = {df['D'].median():.2f}"
        ),
        xy=(0.5, 1.0),
        xycoords="axes fraction",
        xytext=(0, 2),
        textcoords="offset points",
        ha="center",
        va="bottom",
        fontsize=13,
        color="#333333",
    )
    ax.legend(
        handles=[
            Line2D(
                [0],
                [0],
                marker="o",
                color="none",
                markerfacecolor=color,
                markeredgecolor="none",
                markersize=8,
                alpha=0.8,
                label=f"Clinical trial medians (n={fmt_int(len(df))}, p≤.10 proxy {pct_above_p10:.0f}%)",
            ),
            Line2D(
                [0],
                [0],
                marker="o",
                color="none",
                markerfacecolor="white",
                markeredgecolor="#333333",
                markeredgewidth=1.6,
                markersize=8,
                label="Hollow marker = median",
            ),
        ],
        frameon=False,
        loc="upper right",
        fontsize=10,
        borderpad=0.2,
        handletextpad=0.5,
        labelspacing=0.45,
    )
    ax.text(
        0.01,
        -0.105,
        (
            "One median row per randomized interventional trial; row-level file keeps all registered primary, secondary, "
            "and other pre-specified outcome-analysis rows. Axes are capped at N=100k and D=0.02-5; statistics use all rows."
        ),
        transform=ax.transAxes,
        fontsize=8.8,
        color="#333333",
        ha="left",
    )

    linear_d_max = 3.0
    linear_bin_width = 0.1
    linear_bins = np.arange(0, linear_d_max + linear_bin_width, linear_bin_width)
    ax_hist.hist(
        df["D"].clip(lower=0, upper=linear_d_max),
        bins=linear_bins,
        density=True,
        histtype="stepfilled",
        color=color,
        alpha=0.18,
    )
    ax_hist.hist(
        df["D"].clip(lower=0, upper=linear_d_max),
        bins=linear_bins,
        density=True,
        histtype="step",
        linewidth=1.4,
        color=color,
        label=f"CT.gov API trial medians (n={len(df):,}; {fmt_int(direct_row_n)} direct rows)",
    )
    draw_general_results_histogram_references(ax_hist, median_d=float(df["D"].median()), median_color=color)
    finish_general_results_histogram(ax_hist)
    ax_hist.legend(frameon=False, loc="upper right", fontsize=8, handlelength=2.3)

    fig.savefig(out_path, bbox_inches="tight")
    plt.close(fig)
    return {
        "n_rows": len(df),
        "row_level_rows": row_level_n,
        "median_d": float(df["D"].median()),
        "median_n": float(df["N"].median()),
    }


def draw_all_source_dn_dump(out_path: Path) -> dict[str, float | int]:
    prereg = normalize_preregistered_results()
    df = normalize_all_source_dn_rows(prereg)
    layer_specs = {
        "published_candidate_paper": ("Published candidate paper/unit", "#5b6770", 10, 0.18),
        "replication_pair_original": ("Replication-pair original side", "#b84a3a", 15, 0.34),
        "replication_pair_followup": ("Replication-pair follow-up side", "#2f6f9f", 15, 0.34),
        "preregistered_confirmatory_result": ("Preregistered confirmatory result", "#0b6e5f", 30, 0.82),
        "staged_harvest_original": ("Staged harvest original side", "#7d5a9b", 22, 0.7),
        "staged_harvest_followup": ("Staged harvest follow-up side", "#7d5a9b", 22, 0.7),
    }

    x_min = 1.0
    x_max = 10 ** math.ceil(math.log10(float(df["N"].max()) * 1.1))
    y_min = 10 ** math.floor(math.log10(float(df["D"].min()) * 0.9))
    y_max = 10 ** math.ceil(math.log10(float(df["D"].max()) * 1.1))
    x_max = min(max(x_max, 100000.0), 1_000_000_000.0)
    y_min = max(min(y_min, 0.001), 0.00001)
    y_max = min(max(y_max, 3.0), 100.0)
    xs = np.logspace(math.log10(x_min), math.log10(x_max), 500)
    boundary_05 = 2 * Z_05 / np.sqrt(xs)
    boundary_10 = 2 * 1.6448536269514722 / np.sqrt(xs)

    fig, ax = plt.subplots(figsize=(9.4, 6.1), dpi=180)
    ax.fill_between(xs, boundary_05, y_max, color="#e8f5ee", alpha=0.42, zorder=0)
    ax.fill_between(xs, y_min, boundary_05, color="#fceaea", alpha=0.34, zorder=0)
    ax.plot(xs, boundary_05, color="#1f1f1f", lw=1.5, label="two-sample p < .05 boundary", zorder=1)
    ax.plot(xs, boundary_10, color="#606060", lw=1.0, linestyle="--", label="two-sample p < .10 boundary", zorder=1)

    layer_counts = df["source_layer"].value_counts()
    ordered_layers = sorted(layer_specs, key=lambda layer: layer_counts.get(layer, 0), reverse=True)
    for order_index, layer in enumerate(ordered_layers):
        label, color, size, alpha = layer_specs[layer]
        group = df[df["source_layer"].eq(layer)]
        if group.empty:
            continue
        ax.scatter(
            group["N"],
            group["D"],
            s=size,
            color=color,
            alpha=alpha,
            linewidths=0,
            rasterized=True,
            label=f"{label} ({len(group):,})",
            zorder=2 + order_index * 0.05,
        )

    median_d = float(df["D"].median())
    median_n = float(df["N"].median())
    ax.text(
        0.03,
        0.04,
        f"{len(df):,} D/N side-points or paper units\n{df['source_family'].nunique():,} source families; median |D| = {median_d:.2f}; median N = {median_n:,.0f}",
        transform=ax.transAxes,
        fontsize=8.4,
        color="#1a1a1a",
        bbox={"boxstyle": "round,pad=0.35", "facecolor": "white", "edgecolor": "#d8e3df", "alpha": 0.92},
    )
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlim(x_min, x_max)
    ax.set_ylim(y_min, y_max)
    ax.set_xlabel("Sample size N (log scale)")
    ax.set_ylabel("Effect magnitude |D| (log scale)")
    ax.set_title("All recoverable D/N rows currently on hand", fontweight="bold")
    ax.grid(True, which="major", alpha=0.14, linestyle=":")
    ax.legend(frameon=False, loc="upper right", fontsize=7.6, markerscale=1.4)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    fig.savefig(out_path, bbox_inches="tight")
    plt.close(fig)
    return {
        "n_rows": len(df),
        "n_sources": int(df["source_family"].nunique()),
        "median_d": median_d,
        "median_n": median_n,
        "pct_above_p05": 100 * float(df["above_two_sample_p05_curve"].mean()),
    }


def generate_figures() -> dict[str, FigureSpec]:
    fig1 = FIG_DIR / "figure1_publication_boundary.png"
    fig2 = FIG_DIR / "figure2_replication_combined.png"
    fig3 = FIG_DIR / "figure3_published_d_vs_n.png"
    fig4 = FIG_DIR / "figure4_prior_comparison.png"
    fig5 = FIG_DIR / "figure5_published_d_distribution.png"

    draw_publication_boundary(fig1)
    if REPLICATION_FIG.exists():
        shutil.copy2(REPLICATION_FIG, fig2)
    if PUBLISHED_FIG.exists():
        shutil.copy2(PUBLISHED_FIG, fig3)
    draw_prior_comparison(fig4)
    pub_stats = draw_published_distribution(fig5)
    draw_preregistered_results(PREREG_FIG)
    draw_preregistered_sensitivity_sidecar(PREREG_SENSITIVITY_FIG)
    draw_ctgov_primary_randomized_sidecar(PREREG_CTGOV_PRIMARY_RANDOMIZED_FIG)
    draw_ctgov_api_registered_trial_medians(CTGOV_API_REGISTERED_TRIAL_MEDIAN_FIG)
    draw_all_source_dn_dump(ALL_SOURCE_FIG)
    repl_stats = replication_stats()

    return {
        "FIGURE_TOKEN_01": FigureSpec(
            "FIGURE_TOKEN_01",
            "fig-publication-boundary",
            fig1,
            (
                "The p < .05 publication boundary. For a two-sample test, a study only clears "
                "the conventional threshold when observed D is roughly 2 * 1.96 / sqrt(N). "
                "The labeled points are the opening-scenario examples that map cleanly onto a "
                "single-study two-sample-style D-vs-N point."
            ),
        ),
        "FIGURE_TOKEN_02": FigureSpec(
            "FIGURE_TOKEN_02",
            "fig-replication-combined",
            fig2,
            (
                f"Huge effect sizes evaporate in larger replication attempts. The current recovered "
                f"pair table contains {repl_stats['n_pairs']:,} original/replication endpoint pairs; "
                f"{repl_stats['pct_shrunk_any']:.0f}% shrink, {repl_stats['pct_shrunk_below']:.0f}% "
                f"shrink below the p < .05 boundary, and the log-log fit implies about "
                f"{repl_stats['tenfold_reduction_pct']:.0f}% lower D for each 10x increase in N. "
                "The marginal distributions replace the draft's old separate before/after distribution figure."
            ),
        ),
        "FIGURE_TOKEN_04": FigureSpec(
            "FIGURE_TOKEN_04",
            "fig-published-d-vs-n",
            fig3,
            (
                f"The small-N and huge-effect-size pattern in published journal articles. "
                f"The top panel shows {pub_stats['n_papers']:,} published-original "
                f"candidate papers across {pub_stats['source_count']} source corpora as paper/unit medians; "
                f"the lower panel shows the distribution of those same published paper/unit estimates. "
                f"The paper-level median D is {pub_stats['median_d']:.2f}, median N is {pub_stats['median_n']:.0f}, "
                f"and {pub_stats['pct_above_p10']:.0f}% sit above the p <= .10 boundary."
            ),
        ),
        "FIGURE_TOKEN_05": FigureSpec(
            "FIGURE_TOKEN_05",
            "fig-prior-comparison",
            fig4,
            (
                "What you implicitly believe before the data. The flat/no-shrinkage line treats "
                "large effects as no less plausible than small effects; the Normal(0, 0.35) prior "
                "puts most mass on behavioral-science effects near zero. The lower panel shows the "
                "linear-scale distribution of larger-N replication effect sizes, with the median marked."
            ),
        ),
        "FIGURE_TOKEN_06": FigureSpec(
            "FIGURE_TOKEN_06",
            "fig-published-d-distribution",
            fig5,
            (
                f"The current published-original candidate corpus as a distribution of paper-level "
                f"effect sizes. {pub_stats['pct_d_ge_02']:.0f}% of papers have median D >= 0.2, "
                f"{pub_stats['pct_d_ge_05']:.0f}% have median D >= 0.5, and "
                f"{pub_stats['pct_d_ge_08']:.0f}% have median D >= 0.8."
            ),
        ),
    }


def figure_markdown(spec: FigureSpec) -> str:
    rel_path = spec.path.relative_to(DOCS)
    return f"\n![{spec.caption}]({rel_path.as_posix()}){{#{spec.key}}}\n"


def replace_old_figure_nodes(soup: BeautifulSoup) -> None:
    figures = soup.select("div.figure")
    for idx, fig in enumerate(figures, start=1):
        if idx == 3:
            fig.replace_with(
                NavigableString(
                    "\n\nThe current combined replication figure includes the before/after "
                    "effect-size distribution that the draft originally showed as a separate figure.\n\n"
                )
            )
        else:
            fig.replace_with(NavigableString(f"\n\nFIGURE_TOKEN_{idx:02d}\n\n"))


def replace_paragraph_containing(soup: BeautifulSoup, needle: str, replacement: str) -> None:
    for p in soup.find_all("p"):
        if needle in text_of(p):
            p.clear()
            p.append(NavigableString(replacement))
            return


def update_stale_prose(soup: BeautifulSoup, repl: dict[str, float | int], pub: dict[str, float | int]) -> None:
    replace_paragraph_containing(
        soup,
        "Below are 555 pairs",
        (
            f"Below are {repl['n_pairs']:,} recovered original/replication endpoint pairs, now using the expanded "
            "local replication-pair build rather than the smaller draft table alone."
        ),
    )
    replace_paragraph_containing(
        soup,
        "plots most of them",
        (
            f"Figure 2 summarizes the current replication build. {repl['pct_shrunk_any']:.0f}% of effects shrink, "
            f"{repl['pct_shrunk_below']:.0f}% shrink below the p < 0.05 boundary at the replication sample size, "
            f"and the fitted log-log slope implies about {repl['tenfold_reduction_pct']:.0f}% lower D for each 10x increase in N."
        ),
    )
    replace_paragraph_containing(
        soup,
        "Figure 3 shows the distribution",
        (
            "The same combined figure also shows the before/after distribution: the original claims are the selected literature, "
            "and the replication distribution is what remains when the same claims are re-measured with larger samples."
        ),
    )
    replace_paragraph_containing(
        soup,
        "What would the published record look like in that world?",
        (
            f"What would the published record look like in that world? Figure 4 now uses the expanded local published-focal corpus: "
            f"{pub['n_papers']:,} published-original candidate papers across {pub['source_count']} source corpora, each collapsed "
            f"to a paper-level median D and N. The point cloud is no longer just the older statcheck/economics draft example; "
            "it is the current cross-field Codex build."
        ),
    )
    replace_paragraph_containing(
        soup,
        "14,110 papers in Figure",
        (
            f"If you believe any one of the {pub['n_papers']:,} papers in the current published-corpus figure is a literal reading "
            "of the effect size in the world, you have to believe the process that produced the whole cloud."
        ),
    )
    replace_paragraph_containing(
        soup,
        "Discount at 5%",
        (
            "A frequentist defender would object here. A p < 0.05 finding is not claimed with certainty; "
            "the threshold itself admits a 1-in-20 false-positive rate, and p < 0.01 admits 1-in-100. "
            f"Discount the current {pub['n_papers']:,}-paper published-focal corpus by those rates and the "
            f"basic arithmetic barely changes: roughly {0.95 * pub['n_papers']:,.0f} papers remain under a 5% discount "
            f"and roughly {0.99 * pub['n_papers']:,.0f} under a 1% discount. More importantly, the p-value discount is about "
            "whether an effect exists under the null, not whether the reported magnitude is right."
        ),
    )
    replace_paragraph_containing(
        soup,
        "Across all 555 pairs",
        (
            f"The current replication-pair build contains {repl['n_pairs']:,} usable original/replication endpoint pairs. "
            f"Across those rows, {repl['pct_shrunk_any']:.0f}% of effects shrink and {repl['pct_shrunk_below']:.0f}% "
            "drop below the p < .05 boundary at the replication sample size."
        ),
    )


def replace_figure_refs(markdown: str) -> str:
    replacements = [
        (r"Figures(?:\\ | |\u00a0)2(?:\\ | |\u00a0)and(?:\\ | |\u00a0)3", "@fig-replication-combined"),
        (r"Figures(?:\\ | |\u00a0)1(?:\\ | |\u00a0)and(?:\\ | |\u00a0)5", "@fig-publication-boundary and @fig-prior-comparison"),
        (r"Figure(?:\\ | |\u00a0)1", "@fig-publication-boundary"),
        (r"Figure(?:\\ | |\u00a0)2", "@fig-replication-combined"),
        (r"Figure(?:\\ | |\u00a0)3", "@fig-replication-combined"),
        (r"Figure(?:\\ | |\u00a0)4", "@fig-published-d-vs-n"),
        (r"Figure(?:\\ | |\u00a0)5", "@fig-prior-comparison"),
        (r"Figure(?:\\ | |\u00a0)6", "@fig-published-d-distribution"),
    ]
    for pattern, replacement in replacements:
        markdown = re.sub(pattern, replacement, markdown)
    return markdown


def replace_rendered_ref_groups(markdown: str) -> str:
    def to_citation(match: re.Match[str]) -> str:
        keys = re.findall(r"#ref-([A-Za-z0-9_:\-]+)", match.group(0))
        if not keys:
            return ""
        deduped = list(dict.fromkeys(keys))
        return " [" + "; ".join(f"@{key}" for key in deduped) + "]"

    # Pandoc sees some already-rendered bibliography links as superscripted
    # inline links rather than citation spans. Convert each such group back to
    # citeproc syntax.
    markdown = re.sub(r"\^\[[^\n^]*#ref-[^\n^]*?\^", to_citation, markdown)
    return markdown


def normalize_pandoc_markdown(markdown: str) -> str:
    # Pandoc converts pre-rendered citation links into spans if any escaped ones
    # survive. Strip those remnants so citeproc owns the final references.
    markdown = re.sub(r"\[\^\[[^\]]+\]\([^)]+\)[^\]]*\]\{\.citation[^}]*\}", "", markdown)
    markdown = re.sub(r"\\\[(@[A-Za-z0-9_:\-]+(?:; @?[A-Za-z0-9_:\-]+)*)\\\]", r"[\1]", markdown)
    markdown = replace_rendered_ref_groups(markdown)
    markdown = markdown.replace("::: {#title-block-header}", "")
    markdown = markdown.replace("555-pair corpus", "replication-pair corpus")
    markdown = markdown.replace("555-row table", "replication-pair table")
    return markdown


def rewrite_opening_scenario(markdown: str) -> str:
    original = (
        "Your morning starts with wild swings in trust for your spouse: up 11% from holding a warm cup of coffee, "
        "[@williams2008] then down 30% from the smell of last night's kitchen trash. [@lee2012] Uncertain about "
        "your marriage, you pick out a red shirt for the 10% bump on the attractiveness scale [@elliot2008] and "
        "head to work. There a power pose jacks your testosterone 30%, [@carney2010] and putting your feet up on "
        "the desk makes you 43% more likely to take a risky bet. [@yap2013] Your inevitable meeting with HR is "
        "all but guaranteed by a dim break-room light that made you cheat on your reimbursement forms 47% above "
        "baseline. [@zhong2010lamps] To save your job and protect your health, you duck out of work early and head "
        "to the bar. The bottle of red wine reduces your cardiovascular mortality 30% and your all-cause mortality "
        "20%. [@ronksley2011] Somehow you make it home and vow to do better the next day. You swallow a fistful of "
        "vitamin C, [@pauling1970] echinacea, [@shah2007] zinc, [@hemila2017] and melatonin, [@herxheimer2002] "
        "all guaranteed to halve various medical and sleep problems. Exhausted, you doze off to a podcast about "
        "there being yet another study proving the existence of ESP. [@bem2011]"
    )
    revised = (
        "Your morning starts with wild swings in trust for your spouse: up 11% from holding a warm cup of coffee, "
        "[@williams2008] then down 30% from the smell of last night's kitchen trash. [@lee2012] Uncertain about "
        "your marriage, you pick out a red shirt for the 10% bump on the attractiveness scale [@elliot2008] and "
        "head to work. There a power pose jacks your testosterone 30%, and putting your feet up on the desk makes "
        "you 43% more likely to take a risky bet. [@carney2010] Your inevitable meeting with HR is all but "
        "guaranteed by a dim room light that made you cheat on your reimbursement forms 47% above baseline. "
        "[@zhong2010lamps] To save your job and protect your health, you duck out of work early and head to the "
        "bar. The bottle of red wine reduces your cardiovascular mortality 30% and your all-cause mortality 20%. "
        "[@ronksley2011] Somehow you make it home and vow to do better the next day. You swallow a fistful of "
        "vitamin C, [@pauling1970] echinacea, [@shah2007] zinc lozenges, [@prasad2008] and melatonin, [@petrie1989] "
        "all guaranteed to slash your colds and jet lag. Exhausted, you doze off to a podcast about "
        "there being yet another study proving the existence of ESP. [@bem2011]"
    )
    markdown = markdown.replace(original, revised, 1)
    return markdown.replace(
        "All six intro findings plotted here sit in the top-left quadrant: unlikely effect sizes propped up by weak evidence.",
        "The intro findings plotted here all sit in the top-left quadrant: unlikely effect sizes propped up by weak evidence.",
        1,
    )


def find_top_level_section(markdown: str, heading: str) -> tuple[str, str, int, int]:
    match = re.search(rf"(?m)^## {re.escape(heading)}(?:\s|$)", markdown)
    if not match:
        raise RuntimeError(f"Could not find section heading: {heading}")
    start = match.start()
    line_end = markdown.find("\n", match.start())
    if line_end == -1:
        raise RuntimeError(f"Malformed section heading: {heading}")
    next_match = re.search(r"(?m)^## ", markdown[line_end + 1 :])
    end = line_end + 1 + next_match.start() if next_match else len(markdown)
    heading_line = markdown[start:line_end]
    body = markdown[line_end + 1 : end].strip()
    return heading_line, body, start, end


def top_level_sections(markdown: str) -> list[tuple[str, str, int, int]]:
    matches = list(re.finditer(r"(?m)^## .+$", markdown))
    sections: list[tuple[str, str, int, int]] = []
    for idx, match in enumerate(matches):
        start = match.start()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(markdown)
        heading_line = match.group(0)
        body = markdown[match.end() : end].strip()
        sections.append((heading_line, body, start, end))
    return sections


def restructure_sections(markdown: str) -> str:
    most_heading, most_body, most_start, most_end = find_top_level_section(markdown, "Most Effect Sizes Must be Small")
    large_heading, large_body, large_start, large_end = find_top_level_section(
        markdown, "Because Large Effects Are Special, They Require Special Evidence"
    )

    large_blocks = [block.strip() for block in large_body.split("\n\n") if block.strip()]
    if len(large_blocks) < 6:
        raise RuntimeError("Large-effects section structure changed unexpectedly")

    moved_block = "\n\n".join(large_blocks)
    anchor = (
        "Three independent empirical literatures then confirm the total size of the resulting gap: "
        "coordinated replication projects, large-*N* replications of specific famous findings, and cross-literature effect-size censuses. "
        "The full argument is [Appendix\u00a0F](#appendix-f-why-most-effects-must-be-small)."
    )
    if anchor not in most_body:
        raise RuntimeError("Most-effects section anchor changed unexpectedly")
    new_most_body = most_body.replace(anchor, moved_block + "\n\n" + anchor, 1)

    new_large_body = (
        "The point is not that large effects never happen. It is that real large effects look like vaccines, "
        "antibiotics, and other interventions whose targets visibly collapse under coarse measurement and large-scale "
        "replication, not like vague primes in 42 undergraduates.\n\n"
        "That is why the burden of evidence rises with the size of the claim. If a result is supposed to live in the "
        "thin tail of @fig-prior-comparison, then the evidence has to look tail-worthy too: large samples, hard outcomes, "
        "active controls, repeated success across sites, or effects obvious enough to see without statistical heroics."
    )

    rebuilt_most = f"{most_heading}\n\n{new_most_body}\n\n"
    rebuilt_large = f"{large_heading}\n\n{new_large_body}\n\n"
    markdown = markdown[:most_start] + rebuilt_most + markdown[most_end:large_start] + rebuilt_large + markdown[large_end:]
    return markdown


def rewrite_most_effects_section(markdown: str, repl: dict[str, float | int]) -> str:
    heading, _body, start, end = find_top_level_section(markdown, "Most Effect Sizes Must be Small")

    tau = 0.35
    n_small = 40.0
    n_large = 400.0
    s_small = 2 / math.sqrt(n_small)
    s_large = 2 / math.sqrt(n_large)
    w_small = tau**2 / (tau**2 + s_small**2)
    w_large = tau**2 / (tau**2 + s_large**2)
    post_small = w_small * 0.80
    post_large = w_large * 0.80

    body = f"""
The right question is not whether a published estimate crossed *p* < .05. The right question is: given what real effects usually look like, and given that this estimate survived a publication process that rewards large significant estimates, what should I now believe about the true effect?

The first input to that judgment is empirical, not philosophical. **@fig-replication-combined** gives us {int(repl['n_pairs']):,} recovered original/replication endpoint pairs, all on a common $D$ scale, all with both sample sizes known, and all with the replication larger than the original. In that sample, {repl['pct_shrunk_any']:.0f}% of effects shrink, {repl['pct_shrunk_below']:.0f}% shrink below the original *p* < .05 boundary at the replication sample size, and the fitted log-log relationship implies about {repl['tenfold_reduction_pct']:.0f}% lower $D$ for each 10x increase in $N$. That distribution is not an oracle, but it is the least-filtered empirical prior available here: larger samples, direct retests, and far less room for the original publication boundary to select the observed magnitude.

The second input is structural. Appendix F lays out eleven reasons most effects must be small before we ever look at a *p*-value. The short version is that behavioral, biomedical, educational, and social outcomes are bounded noisy aggregates. They are produced by many causes, mediated through partial mechanisms, measured with finite reliability, diluted by active controls and counterfactual exposure, averaged across heterogeneous people and settings, and eroded by site-to-site voltage drop and scale-up decay [@tosh2024; @pearl2001mediation; @mackinnon2002mediation; @spearman1904; @hedge2018reliability; @bryan2021heterogeneity; @klein2018; @alubaydli2017scalability; @pereira2012largeeffects]. Ordinary interventions usually push on one weak edge in a dense causal graph, not on a single unconstrained bottleneck.

The third input is statistical. A published estimate is not just a noisy draw from the world. It is a noisy draw that survived a significance filter. Gelman and Carlin's Type M framework, van Zwet and Cator's significance-filter analysis, and the broader winner's-curse literature all imply the same direction of correction: conditional on significance, small noisy studies exaggerate magnitude [@gelman2014beyondpower; @zwet2021; @ioannidis2008inflation; @loken2017measurement]. So a rational reader needs shrinkage, not just standard errors.

That is what **@fig-prior-comparison** is for. The flat line is the implicit no-shrinkage prior: every effect from $d = 0.01$ to $d = 1{','}000$ treated as no less plausible than every other. The blue curve is the weakly informative Normal$(0, 0.35)$ prior. It does not ban large effects. It says they are rare enough to pay an evidentiary tax. About 95% of that prior lies inside $|d| < 0.69$. That is a reasonable public-facing approximation to what the replication distribution is already telling us.

![What you implicitly believe before the data. The flat/no-shrinkage line treats large effects as no less plausible than small effects; the Normal(0, 0.35) prior puts most mass on behavioral-science effects near zero. The lower panel shows the linear-scale distribution of larger-N replication effect sizes, with the median marked.](_generated/figures/figure4_prior_comparison.png){{#fig-prior-comparison}}

Write the update the simple way:

$$
d \\sim N(0, \\tau^2), \\qquad \\hat d \\mid d, s \\sim N(d, s^2)
$$

$$
E[d \\mid \\hat d, s] = \\frac{{\\tau^2}}{{\\tau^2 + s^2}} \\hat d
$$

with $\\tau = 0.35$. For a balanced two-group design, a useful approximation is $s \\approx 2 / \\sqrt{{N}}$. That makes the reader-facing lesson immediate: large studies have small $s$, so the data dominate; small studies have large $s$, so the estimate shrinks hard toward zero. The prior does not make large effects impossible. It makes small-$N$ large effects earn their keep.

Take the kind of result this essay keeps attacking: a 40-person study reporting $\\hat d = 0.80$. Then $s \\approx 2 / \\sqrt{{40}} \\approx {s_small:.3f}$. Under the Normal$(0, 0.35)$ prior, the shrinkage weight is

$$
w = \\frac{{0.35^2}}{{0.35^2 + {s_small:.3f}^2}} \\approx {w_small:.2f}
$$

so the posterior mean is not $0.80$. It is about ${post_small:.2f}$. Run the same observed estimate at $N = 400$, where $s \\approx {s_large:.2f}$, and the weight rises to about {w_large:.2f}, giving a posterior mean of about ${post_large:.2f}$. That is the whole argument in one contrast. The prior is not saying “big effects never happen.” It is saying “a huge effect from a tiny study is mostly evidence about noise plus selection unless the underlying causal story is extraordinary.”

And that is exactly what the replication evidence shows. Small-$N$ literatures produce large selected estimates; larger replication attempts pull them back toward the effect-size range the world actually allows. Our Figure 2 estimate --- {repl['pct_shrunk_any']:.0f}% shrinking, {repl['pct_shrunk_below']:.0f}% shrinking below the original significance boundary, and about {repl['tenfold_reduction_pct']:.0f}% lower $D$ per 10x increase in $N$ --- is not a side fact. It is the empirical prior the rest of the paper is asking the reader to use.

Real large effects still exist. But when they are real, they look like vaccines, antibiotics, or other interventions whose targets visibly collapse under coarse measurement and large-scale replication, not like vague primes in 42 undergraduates. That is why the burden of evidence rises with the size of the claim. If a result is supposed to live in the thin tail of @fig-prior-comparison, then the evidence has to look tail-worthy too: large samples, hard outcomes, active controls, repeated success across sites, or effects obvious enough to see without statistical heroics.
""".strip()

    rebuilt = f"{heading}\n\n{body}\n\n"
    return markdown[:start] + rebuilt + markdown[end:]


def restructure_post_section4(markdown: str) -> str:
    pub = published_stats()
    sec5_heading, sec5_body, sec5_start, _ = find_top_level_section(
        markdown, "A World In Which Most Published Research Was True Would Be A Nightmare Hellscape"
    )
    _sec6_heading, _sec6_body, _sec6_start, _sec6_end = find_top_level_section(
        markdown, "Because Large Effects Are Special, They Require Special Evidence"
    )
    _sec7_heading, sec7_body, _sec7_start, _sec7_end = find_top_level_section(
        markdown, "A world where everything mattered would be terrifying"
    )
    _sec8_heading, sec8_body, _sec8_start, _sec8_end = find_top_level_section(
        markdown, "Mysticisms about extreme agency and helplessness are common throughout human culture"
    )
    _sec9_heading, sec9_body, _sec9_start, _sec9_end = find_top_level_section(
        markdown, "Science's version of this mysticism is small-*N* frequentism (a cult of the naive and the criminally negligent)"
    )
    _sec10_heading, _sec10_body, _sec10_start, _sec10_end = find_top_level_section(
        markdown, "A Sane Belief System that Matches Our Actual World"
    )
    objections_heading, objections_body, _obj_start, _obj_end = find_top_level_section(markdown, "Objections")
    _sec12_heading, _sec12_body, _sec12_start, _sec12_end = find_top_level_section(
        markdown, "What this means for reading research"
    )
    _sec13_heading, _sec13_body, _sec13_start, _sec13_end = find_top_level_section(
        markdown, "What this means for doing research"
    )
    _sec14_heading, sec14_body, _sec14_start, _sec14_end = find_top_level_section(
        markdown, "The real distribution --- effect sizes across science"
    )
    _appb_heading, appb_body, _appb_start, _appb_end = find_top_level_section(
        markdown, "When the world gives you large effects"
    )
    _appc_heading, appc_body, _appc_start, _appc_end = find_top_level_section(
        markdown, "The hellscape catalog --- effects the literature claimed"
    )
    appd_heading, appd_body, appd_start, appd_end = find_top_level_section(
        markdown, "Appendix D --- Replication pairs: original vs.\u00a0large-N replication"
    )

    fig4_match = re.search(
        r"!\[.*?\]\(_generated/figures/figure3_published_d_vs_n\.png\)\{#fig-published-d-vs-n\}",
        sec5_body,
        flags=re.DOTALL,
    )
    if not fig4_match:
        raise RuntimeError("Could not find published D-vs-N figure block in Section 5")
    fig4_block = fig4_match.group(0)

    r_02 = 0.2 / math.sqrt(0.2**2 + 4)
    r_05 = 0.5 / math.sqrt(0.5**2 + 4)
    r_08 = 0.8 / math.sqrt(0.8**2 + 4)
    r2_02 = (0.2**2) / (0.2**2 + 4)
    r2_05 = (0.5**2) / (0.5**2 + 4)
    r2_08 = (0.8**2) / (0.8**2 + 4)
    p_sup_05 = stats.norm.cdf(0.5 / math.sqrt(2))
    p_sup_08 = stats.norm.cdf(0.8 / math.sqrt(2))
    share_large = pub["pct_d_ge_08"] / 100.0
    crossref_journal_records = 123_100_000
    annual_se_articles = 3_300_000
    large_claims_crossref_02 = share_large * 0.02 * crossref_journal_records
    large_claims_crossref_04 = share_large * 0.04 * crossref_journal_records
    large_claims_crossref_10 = share_large * 0.10 * crossref_journal_records
    large_claims_crossref_25 = share_large * 0.25 * crossref_journal_records
    large_claims_annual_10 = share_large * 0.10 * annual_se_articles
    large_claims_annual_25 = share_large * 0.25 * annual_se_articles
    unique_large_crossref_10_m5 = large_claims_crossref_10 / 5
    unique_large_crossref_25_m5 = large_claims_crossref_25 / 5
    additive_ks = [1, 5, 10, 20, 50, 100]
    additive_rows = "\n".join(
        [
            f"| {k} | {math.sqrt(1 + 0.16 * k):.2f}x | {0.8 / math.sqrt(1 + 0.16 * k):.2f} |"
            for k in additive_ks
        ]
    )
    log_or_08 = 0.8 * math.pi / math.sqrt(3)
    or_08 = math.exp(log_or_08)
    baseline_odds = 0.10 / 0.90
    binary_ks = [1, 2, 3, 4, 7]
    binary_rows = "\n".join(
        [
            f"| {k} | {100 * ((baseline_odds * (or_08**k)) / (1 + baseline_odds * (or_08**k))):.2f}% |"
            for k in binary_ks
        ]
    )
    p_over_1_control = 1 - stats.norm.cdf(1)
    p_over_1_shifted = 1 - stats.norm.cdf(1 - 0.8)
    p_over_2_control = 1 - stats.norm.cdf(2)
    p_over_2_shifted = 1 - stats.norm.cdf(2 - 0.8)
    heterogeneity_rows = "\n".join(
        [
            "| 100% | 0.8 |",
            "| 50% | 1.6 |",
            "| 20% | 4.0 |",
            "| 10% | 8.0 |",
        ]
    )

    sec7_body = re.sub(
        r"^### A world where everything mattered would be terrifying\s*\n+",
        "",
        sec7_body.strip(),
        flags=re.MULTILINE,
    )

    polished_sec5_body = f"""
Take the published literature at face value for a moment. Suppose large effect sizes did not require large evidence, and a 40-person undergraduate study reporting *d* = 0.8 were about as informative about reality as a 40,000-person preregistered RCT reporting the same thing. In that world, sample size would be a cost consideration, not an epistemic one.

But then this is not just a cloud of papers. It is a map of a world.

What would the published record look like in that world? @fig-published-d-vs-n shows {pub['n_papers']:,} published-original candidate papers across {pub['source_count']} source corpora, with each paper represented by its median $D$ and median $N$ in the top panel and the same published paper-level estimates summarized underneath.

{fig4_block}

In this corpus, {pub['pct_d_ge_02']:.1f}% of papers have median $D \\ge 0.2$, {pub['pct_d_ge_05']:.1f}% have median $D \\ge 0.5$, and {pub['pct_d_ge_08']:.1f}% have median $D \\ge 0.8$. That is {pub['n_d_ge_02']:,} nontrivial effects, {pub['n_d_ge_05']:,} medium-or-larger effects, and {pub['n_d_ge_08']:,} conventionally large effects. Read literally, the literature is not saying that large effects sometimes happen. It is saying that large effects are ordinary.

But {pub['n_d_ge_08']:,} is not the implication. It is only the sample count. If this published distribution were a truthful window into the indexed scientific literature, it would scale into a claim about hundreds of thousands to millions of large-effect papers.

Let $J$ be the number of journal articles in the indexed literature and $q$ the fraction of them that are relevant empirical effect-estimating papers. Taking Crossref's roughly 123.1 million journal DOI records and the current {pub['pct_d_ge_08']:.1f}% large-effect share as an order-of-magnitude benchmark, the implied number of paper-level $D \\ge 0.8$ claims is

$$
L_{{0.8}} = {share_large:.3f} q J.
$$

| Universe assumption | Relevant empirical / effect papers | Implied $D \\ge 0.8$ paper-level large-effect claims |
| --- | ---: | ---: |
| Crossref journal records, only 2% relevant | {int(round(0.02 * crossref_journal_records)):,} | {int(round(large_claims_crossref_02)):,} |
| Crossref journal records, only 4% relevant | {int(round(0.04 * crossref_journal_records)):,} | {int(round(large_claims_crossref_04)):,} |
| Crossref journal records, 10% relevant | {int(round(0.10 * crossref_journal_records)):,} | {int(round(large_claims_crossref_10)):,} |
| Crossref journal records, 25% relevant | {int(round(0.25 * crossref_journal_records)):,} | {int(round(large_claims_crossref_25)):,} |
| 2023 worldwide S&E output, 10% relevant | {int(round(0.10 * annual_se_articles)):,} / year | {int(round(large_claims_annual_10)):,} / year |
| 2023 worldwide S&E output, 25% relevant | {int(round(0.25 * annual_se_articles)):,} / year | {int(round(large_claims_annual_25)):,} / year |

The “millions” claim does not require pretending that all science is psychology or medicine. If only 4% of indexed journal articles are in the relevant class, the published distribution implies about {int(round(large_claims_crossref_04)):,} paper-level $D \\ge 0.8$ claims. If 10% are relevant, it implies about {int(round(large_claims_crossref_10)):,}. If 25% are relevant, it implies about {int(round(large_claims_crossref_25)):,}. At the annual scale, even a 10% relevant-share assumption implies roughly {int(round(large_claims_annual_10)):,} new conventionally large effects per year.

Some of those papers are studying the same underlying effect, so paper-level claims are not the same thing as unique causal levers. But duplication has to be enormous to save the literal interpretation. If each genuine large effect generated five papers, the 10% Crossref scenario still implies about {int(round(unique_large_crossref_10_m5)):,} unique $D \\ge 0.8$ effects, and the 25% scenario still implies about {int(round(unique_large_crossref_25_m5)):,}. The exact duplication correction is unknown. The scale is the point.

That is a data-generating-process claim, not just a bibliometric one. For a balanced two-group comparison,

$$
r = \\frac{{d}}{{\\sqrt{{d^2 + 4}}}}, \\qquad R^2 = \\frac{{d^2}}{{d^2 + 4}}.
$$

So a $d = 0.2$ effect corresponds to about $r = {r_02:.2f}$ and explains about {100 * r2_02:.1f}% of outcome variance. A $d = 0.5$ effect corresponds to about $r = {r_05:.2f}$ and explains about {100 * r2_05:.1f}% of outcome variance. A $d = 0.8$ effect corresponds to about $r = {r_08:.2f}$ and explains about {100 * r2_08:.1f}% of outcome variance. Roughly one hundred independent $d = 0.2$ levers, seventeen independent $d = 0.5$ levers, or seven independent $d = 0.8$ levers pointed at the same outcome would use up essentially the whole variance budget. The exact arithmetic changes with dependence, heterogeneity, and measurement, but the qualitative point does not: you cannot have a world in which every small intervention is a giant intervention. The variance has to come from somewhere.

Nor is $d = 0.8$ a subtle effect. Under the usual equal-variance model,

$$
P(Y_T > Y_C) = \\Phi(d / \\sqrt{{2}}).
$$

At $d = 0.5$, a random treated observation beats a random control observation about {100 * p_sup_05:.0f}% of the time. At $d = 0.8$, it is about {100 * p_sup_08:.0f}%. One large effect is survivable. But it is no longer a nudge. It is a major axis of the outcome.

The problem is accumulation. In an unbounded additive model, let

$$
Y = dT + \\epsilon,
$$

with balanced treatment assignment and $\\epsilon$ variance fixed at 1. Then one $d = 0.8$ lever raises the outcome variance from 1 to $1 + .25d^2 = 1.16$, so the outcome SD rises by about 7.7%. But with $K$ independent $d = 0.8$ levers,

$$
\\operatorname{{Var}}(Y) = 1 + 0.16K.
$$

| Independent $d = 0.8$ levers | New SD if residual SD stays fixed | Apparent $d$ of each original lever after variance inflation |
| ---: | ---: | ---: |
{additive_rows}

That table is the DGP problem in miniature. If you keep adding real independent $d = 0.8$ effects, either the outcome variance balloons or each effect stops being $d = 0.8$ relative to the new world. You cannot have thousands of simultaneously real, independent, population-level $d = 0.8$ levers on ordinary stable outcomes.

Most real outcomes do not have arbitrary variance. Test scores, depression scales, blood pressure, turnout, BMI, cholesterol, trust ratings, and reaction times have empirically stable distributions. In that fixed-variance world, a large effect does not inflate the outcome. It spends the variance budget instead. A $d = 0.8$ causal variable explaining {100 * r2_08:.1f}% of outcome variance is not “one more thing that matters.” It is one of the main things that matters. Seven independent effects that large exhaust almost the whole budget. Seventeen $d = 0.5$ effects do the same. In a fixed-variance world, a large effect is not a nudge. It is a pillar of the DGP.

The same point looks even harsher for binary outcomes. Using the standard logistic approximation,

$$
\\log(OR) \\approx d \\frac{{\\pi}}{{\\sqrt{{3}}}}.
$$

So $d = 0.8$ corresponds to an odds ratio of about {or_08:.2f}. Start with a 10% event probability and apply repeated independent $d = 0.8$ levers:

| Number of independent $d = 0.8$ levers | Probability after applying $OR \\approx {or_08:.2f}$ each |
| ---: | ---: |
{binary_rows}

For a binary DGP, “explosion” means saturation. Probabilities race toward 0 or 1. After a handful of large effects, the outcome is no longer a noisy, resistant human outcome. It is almost determined.

The same is true on bounded scales. If controls are normally distributed with mean 0 and SD 1, then $P(Y > 1)$ is {100 * p_over_1_control:.1f}% and $P(Y > 2)$ is {100 * p_over_2_control:.1f}%. After a $d = 0.8$ shift those become {100 * p_over_1_shifted:.1f}% and {100 * p_over_2_shifted:.1f}%. A large effect does not merely move the average. It turns rare states into common states. If thousands of ordinary interventions did that, everyday distributions would visibly lurch toward ceilings and floors whenever ordinary inputs changed.

And the large-effect claim does not get rescued by heterogeneity. If only fraction $h$ of people are true responders and everyone else has zero effect, then an average $d = 0.8$ requires a responder-only shift of roughly $0.8 / h$:

| Responding fraction | Responder-only effect needed for average $d = 0.8$ |
| ---: | ---: |
{heterogeneity_rows}

If the effect is broad, it consumes the population variance budget. If it is narrow, then responders have to move by multiple standard deviations. Either way, it should be obvious.

The small-$N$ publication boundary explains why the literature can look this way without that world existing. For a balanced two-group design,

$$
s_{{\\hat d}} \\approx \\frac{{2}}{{\\sqrt{{N}}}}, \\qquad |\\hat d| \\gtrsim \\frac{{3.92}}{{\\sqrt{{N}}}} \\text{{ for two-sided }} p < 0.05.
$$

That makes the significance rule itself an effect-size filter. At total $N = 20$, the minimum publishable $|\\hat d|$ is about $0.88$. At $N = 40$, it is about $0.62$. At $N = 80$, about $0.44$. At $N = 200$, about $0.28$. At $N = 400$, about $0.20$. At small $N$, “statistically significant” already means “observed effect size large enough to look exciting.”

This is why three different empirical literatures keep converging on the same correction. Szucs and Ioannidis found that published cognitive-neuroscience and psychology papers were packed with large nominal effects and low power [@szucs2017]. Pereira, Horwitz, and Ioannidis found that very large medical effects usually came from small first trials and shrank sharply as more evidence accumulated [@pereira2012largeeffects]. Registered Reports cut the positive-result rate dramatically once publication decisions were made before the data were known [@scheel2021], and the antidepressant-trial record shows the same thing from the registry side: the published literature looked much more positive than the underlying FDA file [@turner2008]. The point is not that one field cheated more than another. The point is that small samples plus a significance filter manufacture a literature full of apparently large, apparently decisive effects.

{sec7_body.strip()}

So the nightmare world is a reductio. If the published small-$N$ effect-size distribution were literal, reality would be packed with hundreds of thousands to millions of large, easy, high-variance causal levers. Ordinary DGPs cannot absorb that. They either inflate in variance, saturate at boundaries, collapse probabilities toward 0 or 1, or reveal that the supposedly independent effects are really the same few mechanisms wearing different names. The sane alternative is the boring one: most published small-$N$ large effects are not real large effects. We are lucky the literature is mostly not true.
""".strip()

    sec9_body = sec9_body.split(
        "### What the published distribution actually looks like {#what-the-published-distribution-looks-like}",
        1,
    )[0].strip()

    merged_culture_heading = (
        "## How This Weirdly Unscientific Culture Became Normal "
        "{#how-this-weirdly-unscientific-culture-became-normal}"
    )
    merged_culture_body = (
        sec8_body.strip()
        + "\n\n"
        + sec9_body
        + "\n\n"
        + "Once that worldview is culturally normal, the rest of the machinery is easy to justify: tiny studies, "
          "huge estimates, confident prose, and a literature calibrated to discovery theater rather than measurement."
    )

    appendix_a_heading = "## Appendix A --- The real distribution --- effect sizes across science"
    appendix_b_heading = "## Appendix B --- When the world gives you large effects"
    appendix_c_heading = "## Appendix C --- The hellscape catalog --- effects the literature claimed"

    rebuilt_middle = "\n\n".join(
        [
            f"{sec5_heading}\n\n{polished_sec5_body.strip()}",
            f"{merged_culture_heading}\n\n{merged_culture_body.strip()}",
            f"{objections_heading}\n\n{objections_body.strip()}",
            f"{appendix_a_heading}\n\n{sec14_body.strip()}",
            f"{appendix_b_heading}\n\n{appb_body.strip()}",
            f"{appendix_c_heading}\n\n{appc_body.strip()}",
        ]
    )

    suffix = markdown[appd_start:appd_end] + markdown[appd_end:]
    return markdown[:sec5_start] + rebuilt_middle + "\n\n" + suffix.lstrip()


def insert_replication_selection_callout(markdown: str, repl: dict[str, float | int]) -> str:
    selection_callout = (
        "::: {.callout .blue}\n"
        "**Selection criteria for Figure 2.** We keep only recovered original/replication effect pairs where "
        "both sides have a usable common-metric effect size on our shared $D$ axis, both sample sizes are known "
        "and at least 10, and the replication attempt is larger than the original ($N_r > N_o$). We also collapse "
        "obvious site-level repeats to one row per original paper × replication study × endpoint anchor, using summed "
        "replication $N$ and an $N$-weighted replication $D$. The unit here is therefore a paper-endpoint pair, not a paper: the current "
        f"{int(repl['n_pairs']):,}-row table comes from {int(repl['n_unique_original_papers']):,} unique original papers, "
        f"and {int(repl['n_original_papers_multirow']):,} of those originals contribute more than one row. "
        "That many-to-one structure is expected because one original paper can contribute several claims or outcomes, "
        "and some claims are re-tested by multiple labs or samples.\n"
        ":::\n"
    )
    metric_callout = (
        "::: {.callout .teal}\n"
        "**Why use $D$ here, and what are its limits?** We use a shared $D$ axis because Figure 2 needs one magnitude scale "
        "that can compare many different literatures and endpoint types. Raw percent changes, relative improvements, and other "
        "denominator-sensitive summaries often explode when the baseline is tiny, so they are not stable enough for a cross-study "
        "distribution. A standardized effect like $D$ is a cleaner common axis for asking one narrow question: how large did the "
        "original claim look, and how large did the larger follow-up look, on the same scale? But $D$ is not neutral. It can be "
        "inflated when the pooled SD is unusually small, noisy, range-restricted, or measured in a selected subgroup. It also "
        "throws away natural units and can blur baseline risk or clinical importance. And when $D$ is back-converted from odds "
        "ratios, hazard ratios, cluster-adjusted models, or adjusted mean differences, the conversion adds another layer of "
        "assumptions. So we use $D$ here because it is the least bad common axis for this figure, not because it is a perfect one.\n"
        ":::\n"
    )
    callout = selection_callout + "\n" + metric_callout
    figure_block = r"(!\[.*?\]\(_generated/figures/figure2_replication_combined\.png\)\{#fig-replication-combined\})"
    if not re.search(figure_block, markdown, flags=re.DOTALL):
        return markdown
    return re.sub(figure_block, r"\1\n\n" + callout, markdown, count=1, flags=re.DOTALL)


def split_main_and_data_appendices(markdown: str, figure_specs: dict[str, FigureSpec]) -> tuple[str, str]:
    sections = top_level_sections(markdown)
    moved_sections: list[tuple[str, str, int, int]] = []
    for section in sections:
        heading_line = section[0]
        if re.match(r"^## Appendix [A-E] ---", heading_line):
            moved_sections.append(section)
    if not moved_sections:
        raise RuntimeError("Could not find Appendix A-E sections to move into the data paper.")

    main_markdown = markdown
    for _, _, start, end in sorted(moved_sections, key=lambda item: item[2], reverse=True):
        main_markdown = main_markdown[:start].rstrip() + "\n\n" + main_markdown[end:].lstrip()
    main_markdown = re.sub(r"\n{3,}", "\n\n", main_markdown).strip()

    appendix_intro = (
        "This generated archive preserves appendix material moved out of the main manuscript. It is not rendered "
        "inline in the companion dataset page until each section has been sorted into the plot-specific source "
        "audits. Use it as an integration backlog rather than as a reader-facing appendix.\n"
    )
    moved_markdown = "\n\n".join(f"{heading}\n\n{body}".strip() for heading, body, _, _ in moved_sections)
    data_appendices = (appendix_intro + "\n\n" + moved_markdown).strip()
    data_appendices = data_appendices.replace(
        "## Appendix E --- Material retired from the main flow (pending placement) {#appendix-e-placeholder}",
        "## Appendix E --- Material retired from the main flow (reference archive) {#appendix-e-reference-archive}",
        1,
    )
    data_appendices = data_appendices.replace(
        "The four subsections below were previously cited by figures in the main text. The figures they document have been removed from the current flow; the data and notes are kept here so the analysis is not lost. Disposition of this material is still being decided --- likely some of it will return as standalone figures (the Cochrane medicine data, for example, needs a provenance-stratified treatment before it can be used; see the companion essay on the Cochrane p-hacking debate) and some of it may stay as reference material only.",
        "The four subsections below were previously cited by figures in the main text. The figures they document have been removed from the current flow, but the data and notes are kept here as a deliberate reference archive so the analysis is not lost. Some of it may later return as standalone figures or medicine-specific supplements, but it no longer sits in the main manuscript as an unresolved placeholder.",
        1,
    )
    data_appendices = data_appendices.replace(
        "The combined preregistered corpus thus contains 36 rows. Their median \\|*d*\\| is 0.31 --- between the replicated (0.28) and the original (0.60) distributions, which is what the shrinkage hypothesis predicts. The four PSA-CR001 rows sit near the low end of the combined distribution (\\|*d*\\| between 0.02 and 0.10 at very large *N*), consistent with what a genuinely preregistered study across 52 countries produces when no file-drawer filter is present.",
        "This archived 36-row seed has now been expanded in the active Plot 3 build by adding 89 Schäfer/Schwarz preregistered psychology key-effect rows. The current plotted preregistered-results file therefore contains 125 rows. The four PSA-CR001 rows still sit near the low end of the distribution (\\|*d*\\| between 0.02 and 0.10 at very large *N*), while the Schäfer/Schwarz rows enter with support status marked as not coded.",
        1,
    )
    data_appendices = data_appendices.replace(
        "These rows are the single-study preregistered hypotheses from the Scheel / Lakens and PSA-CR001 corpora. They were previously displayed as a purple dashed curve alongside the 555 originals and replications; in the current flow they are not plotted. They are not original--replication pairs, so they do not appear in the main replication-pair table above. Rows 1--32 are from Scheel, Schijen & Lakens [@scheel2021]: each is one hypothesis from a published psychology Registered Report, showing what the preregistered confirmatory test returned with no replication attempt. Rows 33--36 are from PSA-CR001 (Dorison et al. 2022) [@dorison2022]: each is one of four primary preregistered hypotheses tested across 52 countries, pooled to a single effect size and sample count. Supported = the hypothesis was judged supported by the authors of the original report.",
        "These archived rows are the original 36-row preregistered seed from the Scheel / Lakens and PSA-CR001 corpora. In the active data-paper flow they are plotted as part of Plot 3, alongside the newly added Schäfer/Schwarz preregistered psychology key-effect rows. Rows 1--32 are from Scheel, Schijen & Lakens [@scheel2021]: each is one hypothesis from a published psychology Registered Report, showing what the preregistered confirmatory test returned with no replication attempt. Rows 33--36 are from PSA-CR001 (Dorison et al. 2022) [@dorison2022]: each is one of four primary preregistered hypotheses tested across 52 countries, pooled to a single effect size and sample count. Supported = the hypothesis was judged supported by the authors of the original report; the Schäfer/Schwarz extension has D/N but no support-status coding.",
        1,
    )
    return main_markdown, data_appendices


def write_dataset_audit_snapshot() -> None:
    audit = pd.read_csv(REPLICATION_SOURCE_AUDIT)
    inventory = pd.read_csv(REPLICATION_SOURCE_INVENTORY)
    catalog = pd.read_csv(REPLICATION_SOURCE_CATALOG)
    worklist = pd.read_csv(REPLICATION_SOURCE_WORKLIST)
    all_pairs = pd.read_csv(REPLICATION_ALL)
    fig2 = pd.read_csv(REPLICATION_CSV)
    appendix_coverage = pd.read_csv(REPLICATION_APPENDIX_COVERAGE)

    integrated_sources = int(audit["integrated_in_build"].fillna(False).astype(bool).sum())
    staged_present = int(audit["staged_present"].fillna(False).astype(bool).sum())
    promoted_present = int(audit["promoted_present"].fillna(False).astype(bool).sum())
    raw_dir_present = int(audit["raw_dir_present"].fillna(False).astype(bool).sum())
    manual_backfill = int(audit["needs_manual_backfill"].fillna(False).astype(bool).sum())

    status_counts = (
        audit["audit_status"].fillna("unknown").value_counts().rename_axis("audit_status").reset_index(name="source_families")
    )
    coverage_rows = appendix_coverage[
        ["appendix_family", "appendix_target_rows", "capped_appendix_coverage", "remaining_gap"]
    ].copy()
    worklist_top = worklist[["canonical_source_label", "recommended_next_step", "worklist_priority"]].head(10).copy()

    lines = [
        "## Current Audit Snapshot",
        "",
        "Every checked replication source should now be traceable through the canonical audit files listed below. "
        "In practice, `cataloged` means the source shows up in the non-lossy evidence inventory, the canonical "
        "source-family audit, the build-known source catalog, or the unresolved worklist as appropriate.",
        "",
        f"- Canonical source-family audit rows: `{len(audit):,}` in [replication_source_audit.csv](../data/derived/replication_pairs/replication_source_audit.csv)",
        f"- Non-lossy evidence-surface rows: `{len(inventory):,}` in [replication_source_evidence_inventory.csv](../data/derived/replication_pairs/replication_source_evidence_inventory.csv)",
        f"- Source datasets known to the current build: `{len(catalog):,}` in [replication_pair_source_catalog.csv](../data/derived/replication_pairs/replication_pair_source_catalog.csv)",
        f"- Prioritized unresolved checked sources: `{len(worklist):,}` in [replication_source_worklist.csv](../data/derived/replication_pairs/replication_source_worklist.csv)",
        f"- Live integrated pair rows: `{len(all_pairs):,}` in [replication_pairs_all_on_hand.csv](../data/derived/replication_pairs/replication_pairs_all_on_hand.csv)",
        f"- Figure 2 rule-qualified rows: `{len(fig2):,}` in [replication_pairs_figure2_rule_subset.csv](../data/derived/replication_pairs/replication_pairs_figure2_rule_subset.csv)",
        f"- Audit rows with integrated live data: `{integrated_sources:,}`",
        f"- Audit rows with staged artifacts: `{staged_present:,}`",
        f"- Audit rows with promoted artifacts: `{promoted_present:,}`",
        f"- Audit rows with raw directories present: `{raw_dir_present:,}`",
        f"- Audit rows flagged for manual backfill: `{manual_backfill:,}`",
        f"- Legacy Appendix D target coverage: `{int(appendix_coverage['capped_appendix_coverage'].sum()):,}` / `{int(appendix_coverage['appendix_target_rows'].sum()):,}` rows, leaving a gap of `{int(appendix_coverage['remaining_gap'].sum()):,}`",
        "",
        "### Canonical audit status counts",
        "",
        markdown_table_block(
            [["Audit status", "Source families"]]
            + [[str(row.audit_status), f"{int(row.source_families):,}"] for row in status_counts.itertuples(index=False)],
            "dataset-table compact-count-table",
        ),
        "",
        "### Legacy Appendix D family coverage",
        "",
        markdown_table_block(
            [["Appendix family", "Target rows", "Covered rows", "Remaining gap"]]
            + [
                [
                    str(row.appendix_family),
                    f"{int(row.appendix_target_rows):,}",
                    f"{int(row.capped_appendix_coverage):,}",
                    f"{int(row.remaining_gap):,}",
                ]
                for row in coverage_rows.itertuples(index=False)
            ],
            "dataset-table compact-count-table",
        ),
        "",
        "### Highest-priority unresolved checked sources",
        "",
        markdown_table_block(
            [["Source", "Recommended next step", "Priority"]]
            + [
                [str(row.canonical_source_label), str(row.recommended_next_step), f"{int(row.worklist_priority):,}"]
                for row in worklist_top.itertuples(index=False)
            ],
            "dataset-table worklist-table",
        ),
    ]
    DATASET_AUDIT_QMD.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")


def write_plot1_source_catalog() -> None:
    audit = pd.read_csv(REPLICATION_SOURCE_AUDIT)
    worklist = pd.read_csv(REPLICATION_SOURCE_WORKLIST)
    source_catalog = pd.read_csv(REPLICATION_SOURCE_CATALOG)
    all_pairs = pd.read_csv(REPLICATION_ALL)
    fig2 = pd.read_csv(REPLICATION_CSV)
    out_csv = DATASET_DERIVED_DIR / "plot1_replication_source_catalog.csv"
    display_csv = DATASET_DERIVED_DIR / "plot1_replication_source_display_table.csv"
    normalization_csv = DATASET_DERIVED_DIR / "plot1_replication_source_normalization_worklist.csv"

    joined = audit.merge(
        worklist[["canonical_source_id", "recommended_next_step", "worklist_priority"]],
        on="canonical_source_id",
        how="left",
    )
    catalog_slim = source_catalog[
        ["project", "source_dataset", "classification", "raw_file", "notes"]
    ].rename(columns={"notes": "source_catalog_notes"})
    joined = joined.merge(catalog_slim, on=["project", "source_dataset"], how="left")
    joined["plot_name"] = "Plot 1"
    joined["plot_inclusion_status"] = np.where(joined["audit_status"] == "integrated_live", "included", "not_included")
    joined["plot_role"] = np.select(
        [
            joined["audit_status"] == "integrated_live",
            joined["audit_status"] == "catalog_integrated",
        ],
        [
            "included_live_rows",
            "support_only_not_row_contributing",
        ],
        default="considered_not_included",
    )
    label_counts = joined["canonical_source_label"].fillna("").astype(str).value_counts()
    joined["display_label"] = joined.apply(lambda r: plot1_display_label_for_row(r, label_counts), axis=1)
    joined["source_key"] = joined.apply(
        lambda r: safe_text(r.get("source_dataset")) or safe_text(r.get("canonical_source_id")),
        axis=1,
    )
    joined["citation_key"] = joined.apply(
        lambda r: plot1_citation_key(
            r.get("canonical_source_label"),
            r.get("source_dataset"),
            r.get("display_label"),
            r.get("source_key"),
        ),
        axis=1,
    )
    joined["display_family_label"] = joined.apply(plot1_source_family_label_for_row, axis=1)
    joined["display_family_key"] = joined.apply(
        lambda r: plot1_family_key(r.get("display_family_label"), r.get("citation_key")),
        axis=1,
    )

    def source_mask_for_table(table: pd.DataFrame, row: pd.Series) -> pd.Series:
        source_datasets = {
            part.strip()
            for part in safe_text(row.get("linked_source_datasets")).split("|")
            if part.strip()
        }
        linked_projects = {
            part.strip()
            for part in safe_text(row.get("linked_projects")).split("|")
            if part.strip()
        }
        source_dataset = safe_text(row.get("source_dataset"))
        if source_dataset:
            source_datasets.add(source_dataset)
        if not source_datasets:
            return pd.Series(False, index=table.index)
        mask = table["source_dataset"].fillna("").astype(str).isin(source_datasets)
        project = safe_text(row.get("project"))
        if project and len(linked_projects) <= 1 and project != "Multi-project" and "project" in table.columns:
            project_mask = table["project"].fillna("").astype(str) == project
            if project_mask.any():
                mask &= project_mask
        return mask

    def figure_count_for_source(row: pd.Series) -> int:
        role = safe_text(row.get("plot_role"))
        is_appendix_fallback = safe_text(row.get("canonical_source_label")) == "Appendix D supplemental"
        if role != "included_live_rows" and not is_appendix_fallback:
            return 0
        mask = source_mask_for_table(fig2, row)
        return int(mask.sum())

    def gate_counts_for_source(row: pd.Series) -> pd.Series:
        role = safe_text(row.get("plot_role"))
        if role != "included_live_rows":
            return pd.Series(
                {
                    "kept_for_figure": figure_count_for_source(row),
                    "blocked_no_DZ": 0,
                    "blocked_no_N": 0,
                    "blocked_N_lt_10": 0,
                    "blocked_replication_N_le_original_N": 0,
                }
            )
        group = all_pairs.loc[source_mask_for_table(all_pairs, row)]
        has_effect = group["D_original"].notna() & group["D_replication"].notna()
        no_dz = ~has_effect
        no_n = has_effect & (group["N_original"].isna() | group["N_replication"].isna())
        has_both_sides = has_effect & group["N_original"].notna() & group["N_replication"].notna()
        n_lt_10 = has_both_sides & ((group["N_original"] < 10) | (group["N_replication"] < 10))
        replication_n_le_original_n = has_both_sides & ~n_lt_10 & (group["N_replication"] <= group["N_original"])
        return pd.Series(
            {
                "kept_for_figure": figure_count_for_source(row),
                "blocked_no_DZ": int(no_dz.sum()),
                "blocked_no_N": int(no_n.sum()),
                "blocked_N_lt_10": int(n_lt_10.sum()),
                "blocked_replication_N_le_original_N": int(replication_n_le_original_n.sum()),
            }
        )

    def source_kind(row: pd.Series) -> str:
        role = safe_text(row.get("plot_role"))
        status = safe_text(row.get("audit_status"))
        if role == "included_live_rows":
            return "Integrated replication-pair source with common D and N on both sides."
        if role == "support_only_not_row_contributing":
            return "Support, alias, or cross-check catalog source; not a plotted row source."
        if status == "catalog_not_integrated":
            return "Cataloged replication source not integrated into the live pair build."
        if status == "staged_only":
            return "Staged harvested source with a current promotion blocker."
        if status == "raw_artifact_only":
            return "Raw harvested lead artifact not yet staged into structured rows."
        return safe_text(row.get("status_explanation")) or status

    joined["plot_rows_made_in"] = joined.apply(figure_count_for_source, axis=1)
    gate_counts = joined.apply(gate_counts_for_source, axis=1)
    joined = pd.concat([joined, gate_counts], axis=1)
    joined["plot_inclusion_status"] = np.select(
        [
            joined["plot_rows_made_in"] > 0,
            joined["plot_role"] == "included_live_rows",
            joined["plot_role"] == "support_only_not_row_contributing",
        ],
        [
            "included",
            "integrated_not_plotted",
            "support_only",
        ],
        default="not_included",
    )
    joined["corpus_what_it_is"] = joined.apply(source_kind, axis=1)
    joined.loc[
        (joined["plot_role"] == "support_only_not_row_contributing") & (joined["plot_rows_made_in"] > 0),
        "corpus_what_it_is",
    ] = "Support/fallback source that contributes plotted rows for undercovered project families."
    joined["source_family_description"] = joined.apply(plot1_source_family_description, axis=1)

    def split_pipe_values(values: object) -> list[str]:
        out: list[str] = []
        for value in values:
            for part in safe_text(value).split("|"):
                part = part.strip()
                if part:
                    out.append(part)
        return out

    def expected_rows_from_staged_paths(values: object) -> int:
        total = 0
        seen_paths: set[Path] = set()
        for text in split_pipe_values(values):
            path = Path(text)
            if not path.is_absolute():
                path = ROOT / path
            if path in seen_paths or not path.exists() or path.suffix.lower() != ".csv":
                continue
            seen_paths.add(path)
            try:
                staged = pd.read_csv(path, nrows=25)
            except Exception:
                continue
            if "expected_rows" in staged.columns:
                vals = pd.to_numeric(staged["expected_rows"], errors="coerce").dropna()
                if not vals.empty:
                    total += int(vals.max())
        return total

    def pair_count_basis(record: dict[str, object], group: pd.DataFrame) -> str:
        expected = int(record.get("expected_candidate_rows") or 0)
        live = int(record.get("live_pair_rows") or 0)
        kept = int(record.get("kept_for_figure") or 0)
        catalog_rows = int(pd.to_numeric(group["catalog_file_rows"], errors="coerce").fillna(0).sum())
        catalog_usable = int(pd.to_numeric(group["catalog_usable_pair_rows"], errors="coerce").fillna(0).sum())

        if live:
            return (
                f"Pair-count basis: {live:,} structured local original/replication row(s) are in the live build; "
                f"{kept:,} pass the current Figure 2 rule."
            )
        if expected:
            return f"Pair-count basis: the staged lead manifest expected {expected:,} possible pair row(s)."
        if catalog_usable:
            return (
                f"Pair-count basis: the source catalog marks {catalog_usable:,} usable pair row(s) "
                f"out of {catalog_rows:,} cataloged row(s)."
            )
        if catalog_rows:
            return f"Pair-count basis: {catalog_rows:,} catalog row(s) were checked, but none are marked usable pair rows."
        return "Pair-count basis: no concrete pair-row count was verified before checking the source."

    def family_candidate_description(record: dict[str, object], group: pd.DataFrame) -> str:
        status = safe_text(record.get("plot_inclusion_status"))
        description = safe_text(record.get("corpus_what_it_is"))
        if status == "included":
            rationale = (
                "Candidate rationale: treated as a likely pair source because it explicitly links original findings "
                "to replication or follow-up estimates."
            )
        elif status == "integrated_not_plotted":
            rationale = (
                "Candidate rationale: treated as a likely pair source because structured local pair rows exist, "
                "even though none pass this plot's current gates."
            )
        elif status == "support_only":
            rationale = (
                "Candidate rationale: retained as a candidate support source because it can validate, alias, "
                "or backfill already represented pair families."
            )
        else:
            rationale = (
                "Candidate rationale: tracked because the source was described in the audit trail as a replication, "
                "direct-replication, multi-lab, pilot/full-scale, or repeated-study source that might contain pairable evidence."
            )
        return " ".join([part for part in [description, rationale, pair_count_basis(record, group)] if part])

    def display_material_label(row: pd.Series) -> str:
        display_label = safe_text(row.get("display_label"))
        canonical = safe_text(row.get("canonical_source_label"))
        if display_label.startswith("lead::") or canonical.startswith("lead::"):
            return safe_text(row.get("display_family_label"))
        return display_label or safe_text(row.get("display_family_label"))

    joined["display_material_label"] = joined.apply(display_material_label, axis=1)
    family_sizes = joined["display_family_key"].value_counts()

    def normalization_issue(row: pd.Series) -> str:
        issues: list[str] = []
        family_label = safe_text(row.get("display_family_label"))
        display_label = safe_text(row.get("display_label"))
        canonical = safe_text(row.get("canonical_source_label"))
        source_dataset = safe_text(row.get("source_dataset"))
        if display_label and family_label and display_label != family_label:
            issues.append("aliased_to_source_family")
        if canonical.startswith("lead::") or safe_text(row.get("source_handle")).startswith("lead::"):
            issues.append("lead_handle_normalized")
        artifact_text = " ".join([display_label, canonical, source_dataset]).lower()
        artifact_tokens = [" rda", ".rda", ".csv", ".xlsx", ".zip", "workbook", "manual", "alias", "supplement"]
        if any(token in artifact_text for token in artifact_tokens):
            issues.append("artifact_label_retained_in_full_audit")
        if family_sizes.get(safe_text(row.get("display_family_key")), 0) > 1:
            issues.append("multiple_audit_rows_roll_up_to_family")
        return "; ".join(dict.fromkeys(issues))

    joined["normalization_issue"] = joined.apply(normalization_issue, axis=1)
    normalization_cols = [
        "display_family_label",
        "display_label",
        "canonical_source_label",
        "source_dataset",
        "project",
        "audit_status",
        "plot_inclusion_status",
        "citation_key",
        "normalization_issue",
        "recommended_next_step",
    ]
    joined.loc[joined["normalization_issue"].astype(str) != "", normalization_cols].sort_values(
        ["display_family_label", "display_label", "canonical_source_label"]
    ).to_csv(normalization_csv, index=False)
    joined = joined.sort_values(
        ["plot_rows_made_in", "plot_role", "display_label"],
        ascending=[False, True, True],
    )
    joined.to_csv(out_csv, index=False)

    detail_cols = [
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
        "original_sig_05",
        "replication_sig_05",
        "n_ratio",
        "d_ratio",
        "category",
        "appendix_row_num",
    ]
    fig2_details = fig2[[col for col in detail_cols if col in fig2.columns]].copy()
    original_n = numeric_series(fig2_details.get("N_original", pd.Series(index=fig2_details.index)))
    replication_n = numeric_series(fig2_details.get("N_replication", pd.Series(index=fig2_details.index)))
    original_is_smaller = (original_n <= replication_n).fillna(True)
    fig2_details["smaller_N_paper_title"] = fig2_details["original_title"].where(
        original_is_smaller, fig2_details["replication_title"]
    )
    fig2_details["larger_N_paper_title"] = fig2_details["replication_title"].where(
        original_is_smaller, fig2_details["original_title"]
    )
    fig2_details["smaller_N_paper_doi"] = fig2_details["original_doi"].where(
        original_is_smaller, fig2_details["replication_doi"]
    )
    fig2_details["larger_N_paper_doi"] = fig2_details["replication_doi"].where(
        original_is_smaller, fig2_details["original_doi"]
    )
    fig2_details["D_smaller_N"] = numeric_series(fig2_details["D_original"]).where(
        original_is_smaller, numeric_series(fig2_details["D_replication"])
    )
    fig2_details["N_smaller_N"] = numeric_series(fig2_details["N_original"]).where(original_is_smaller, replication_n)
    fig2_details["D_larger_N"] = numeric_series(fig2_details["D_replication"]).where(
        original_is_smaller, numeric_series(fig2_details["D_original"])
    )
    fig2_details["N_larger_N"] = replication_n.where(original_is_smaller, original_n)
    fig2_details["D_larger_N_minus_smaller_N"] = fig2_details["D_larger_N"] - fig2_details["D_smaller_N"]
    fig2_details.to_csv(PLOT1_PAIR_DETAILS, index=False)

    def clean_included_reason(row: pd.Series) -> str:
        label = safe_text(row.get("canonical_source_label"))
        project = safe_text(row.get("project"))
        notes = safe_text(row.get("notes"))
        if notes:
            parts = [p.strip() for p in notes.split(" | ") if p.strip()]
            ignore_fragments = (
                "live integrated source summary",
                "generic_stage_csv",
                "promoted pair table",
                "raw lead-harvest artifact directory present",
                "downloaded_payload_present",
            )
            for part in parts:
                if not any(fragment in part for fragment in ignore_fragments):
                    if part == "Auto-discovered promoted harvested lead source.":
                        if "Ying 2023" in label:
                            return "Manual reconstruction recovered one promotable D/N pilot-full-scale pair from a larger staged family that still contains roster-only and native-metric rows."
                        return "Public harvested source was staged and promoted into live D/N pair rows after source-specific parsing."
                    return part
        if "FReD filtered pair table" in label:
            if project:
                return f"{project}-specific slice of the FReD pair corpus after overlap filtering and retention of rows that clear the shared D/N pair rules."
            return "Filtered slice of the FReD pair corpus retaining rows that clear the shared D/N pair rules."
        if "Ying 2023" in label:
            return "Manual reconstruction recovered one promotable D/N pilot-full-scale pair from a larger staged family that still contains roster-only and native-metric rows."
        return safe_text(row.get("status_explanation"))

    def unique_nonempty(values: object, limit: int | None = None) -> str:
        seen: list[str] = []
        for value in values:
            text = safe_text(value)
            if text and text not in seen:
                seen.append(text)
        if limit is not None and len(seen) > limit:
            return "; ".join(seen[:limit]) + f"; +{len(seen) - limit} more"
        return "; ".join(seen)

    def citation_cluster(values: object) -> str:
        cites = [cite for cite in unique_nonempty(values).split("; ") if cite]
        if not cites:
            return ""
        if len(cites) == 1:
            return cites[0]
        return "; @".join(cites)

    def family_status(group: pd.DataFrame, kept: int) -> str:
        roles = set(group["plot_role"].fillna("").astype(str))
        if kept > 0:
            return "included"
        if "included_live_rows" in roles:
            return "integrated_not_plotted"
        if "support_only_not_row_contributing" in roles:
            return "support_only"
        return "not_included"

    def human_blockers(values: object) -> str:
        labels = {
            "parser_not_implemented": "parser not implemented",
            "conversion_policy_missing": "conversion policy missing",
            "effect_conversion_policy_missing": "effect-conversion policy missing",
            "metric_not_on_shared_d_axis": "metric not on the shared D axis",
            "non_d_metric": "metric not on the shared D axis",
            "missing_machine_readable_pair_results": "machine-readable pair results missing",
            "original_side_missing": "original-side effect/N missing",
            "source_not_pair_buildable": "not an original-versus-replication pair table",
            "access_restriction": "access restriction",
            "overlap_or_dedup_required": "overlap/deduplication unresolved",
            "needs_primary_pdf_confirmation": "primary PDF confirmation needed",
        }
        blockers: list[str] = []
        for value in values:
            for part in safe_text(value).split("|"):
                part = part.strip()
                if part:
                    blockers.append(labels.get(part, part.replace("_", " ")))
        return "; ".join(dict.fromkeys(blockers))

    def code_set(values: object) -> set[str]:
        codes: set[str] = set()
        for part in split_pipe_values(values):
            codes.add(part)
        return codes

    def step_set(values: object) -> set[str]:
        return {safe_text(value) for value in values if safe_text(value)}

    def family_reason(record: dict[str, object], group: pd.DataFrame) -> str:
        label = safe_text(record.get("display_label"))
        status = safe_text(record.get("plot_inclusion_status"))
        expected = int(record.get("expected_candidate_rows") or 0)
        live_rows = int(record.get("live_pair_rows") or 0)
        kept = int(record.get("kept_for_figure") or 0)
        gate_limits = []
        if int(record.get("blocked_no_DZ") or 0):
            gate_limits.append("some rows lack a D/Z-convertible effect on both sides")
        if int(record.get("blocked_no_N") or 0):
            gate_limits.append("some rows lack N on both sides")
        if int(record.get("blocked_N_lt_10") or 0):
            gate_limits.append("some rows are below the minimum-N floor")
        if int(record.get("blocked_replication_N_le_original_N") or 0):
            gate_limits.append("some follow-up samples are not larger than the original")
        gate_clause = "; ".join(dict.fromkeys(gate_limits))
        expected_clause = f" The staged candidate count was {expected:,} possible row(s)." if expected else ""
        override_detail = PLOT1_WHY_OVERRIDES.get(label, "")

        if status == "included":
            seed_group = group.sort_values("kept_for_figure", ascending=False).iloc[0]
            reason_seed = clean_included_reason(seed_group)
            detail = override_detail or reason_seed
            detail_clause = f" Source-specific note: {detail}" if detail else ""
            if live_rows == 0 and kept:
                catalog_usable = int(pd.to_numeric(group["catalog_usable_pair_rows"], errors="coerce").fillna(0).sum())
                catalog_clause = f" from {catalog_usable:,} cataloged usable row(s)" if catalog_usable else ""
                return (
                    f"Confirmed usable fallback: {kept:,} row(s){catalog_clause} pass the Figure 2 rule through "
                    f"the catalog/backfill route rather than a separate live source table.{detail_clause}"
                )
            if label == "FReD":
                return (
                    f"Confirmed usable: {live_rows:,} structured local pair row(s) were present and {kept:,} pass "
                    "the Figure 2 D/N and size gates. FReD is not a random journal-paper denominator, so only "
                    "D/N-convertible rows that clear the size gates are plotted."
                )
            if gate_clause:
                return (
                    f"Confirmed usable with exclusions: {live_rows:,} structured local pair row(s) were present and "
                    f"{kept:,} pass the Figure 2 rule; rows outside the plot fail because {gate_clause}.{detail_clause}"
                )
            if reason_seed:
                if "Public harvested source was staged" in reason_seed:
                    return (
                        f"Confirmed usable: the public materials were reduced to {live_rows:,} auditable "
                        f"original-versus-replication D/Z and N pair row(s), with {kept:,} passing the figure gates."
                        f"{detail_clause}"
                    )
                if "Manual reconstruction recovered one promotable D/N pilot-full-scale pair" in reason_seed:
                    return (
                        f"Confirmed partly usable: manual reconstruction recovered {live_rows:,} pilot/full-scale "
                        f"D/N pair row(s), and {kept:,} pass the figure gates; the remaining source material is "
                        "roster-only, native-metric, or missing compatible variance."
                    )
                return (
                    f"Confirmed usable: {live_rows:,} structured local pair row(s) were present and {kept:,} pass "
                    f"the Figure 2 rule. Source-specific note: {reason_seed}"
                )
            return (
                f"Confirmed usable: {live_rows:,} structured local pair row(s) were present and {kept:,} pass "
                "the Figure 2 D/N and size gates."
            )

        if status == "integrated_not_plotted":
            if gate_clause:
                return (
                    f"Confirmed present but not usable for this figure: {live_rows:,} structured D/N pair row(s) "
                    f"exist, but zero pass the Figure 2 rule because {gate_clause}."
                )
            return (
                f"Confirmed present but not usable for this figure: {live_rows:,} structured D/N pair row(s) "
                "exist, but none survive the current Figure 2 gate."
            )

        if status == "support_only":
            materials = unique_nonempty(group["display_label"], limit=3)
            return (
                "Confirmed support-only rather than independent pair evidence: the material is useful as fallback, "
                f"alias, or cross-check data, but overlaps with or supplements rows represented elsewhere. Local material: {materials}."
            )

        blockers = code_set(group["blocker_codes"])
        steps = step_set(group["recommended_next_step"])
        raw_statuses = code_set(group["raw_payload_statuses"])
        blocker_text = human_blockers(group["blocker_codes"])
        step_text = unique_nonempty([step.replace("_", " ") for step in steps], limit=2)
        detail_clause = f" Source-specific note: {override_detail}" if override_detail else ""
        if "access_restriction" in blockers or "resolve_access_block" in steps:
            if "metric_not_on_shared_d_axis" in blockers:
                return (
                    "Could not confirm usable pairs: access to the actual row-ready data is restricted, and the "
                    f"visible materials also appear to use a native metric outside the shared D/Z axis.{expected_clause}{detail_clause}"
                )
            return (
                "Could not confirm usable pairs: access or download resolution is still blocked for the actual "
                f"data payload.{expected_clause}{detail_clause}"
            )
        if "download_public_payload" in steps:
            return (
                "Could not confirm usable pairs yet: the public payload has not been downloaded and checked deeply "
                f"enough to audit row-level D/Z and N.{expected_clause}{detail_clause}"
            )
        if "stage_downloaded_payload" in steps:
            return (
                "Could not confirm usable pairs yet: downloaded materials exist, but they have not been staged into "
                f"structured source rows, so row-level D/Z and N fit is still unverified.{expected_clause}{detail_clause}"
            )
        if "locate_machine_readable_payload" in steps or "missing_machine_readable_pair_results" in blockers:
            if "manifest_only" in raw_statuses:
                return (
                    "Confirmed no usable pair payload at the checked location: the public manifest/storage listing "
                    f"did not expose a machine-readable original-versus-replication result table.{expected_clause}{detail_clause}"
                )
            if "downloaded_payload_present" in raw_statuses:
                return (
                    "Confirmed present but not usable: downloaded materials exist, but they do not contain a "
                    f"machine-readable original-versus-replication pair-results table for this plot.{expected_clause}{detail_clause}"
                )
            return (
                "Could not confirm usable pairs: the audit trail points to a candidate source, but no machine-readable "
                f"pair-results payload is currently on hand.{expected_clause}{detail_clause}"
            )
        if "parser_not_implemented" in blockers:
            return (
                "Could not confirm usable pairs yet: source materials appear relevant, but the parser is not "
                f"implemented, so row-level D/Z and N have not been audited.{expected_clause}{detail_clause}"
            )
        if "conversion_policy_missing" in blockers or "effect_conversion_policy_missing" in blockers:
            return (
                "Confirmed present but not usable on the current axis: the source looks relevant, but the effect-size "
                f"conversion policy is not settled enough to put it on the shared D/Z scale.{expected_clause}{detail_clause}"
            )
        if "metric_not_on_shared_d_axis" in blockers or "non_d_metric" in blockers:
            return (
                "Confirmed present but not usable on the current axis: the source is real, but its native metric "
                f"does not sit cleanly on the shared D/Z scale and is better suited to a native-metric lane.{expected_clause}{detail_clause}"
            )
        if "missing_machine_readable_pair_results" in blockers:
            return (
                "Confirmed present but not usable: the local download is report, appendix, code, or native material "
                f"rather than a machine-readable original-versus-replication result table.{expected_clause}{detail_clause}"
            )
        if "original_side_missing" in blockers:
            return (
                "Confirmed one-sided or incomplete: local files do not provide both the original-study side and a "
                f"defensible shared-D conversion for this figure.{expected_clause}{detail_clause}"
            )
        if "source_not_pair_buildable" in blockers:
            return (
                "Confirmed not pair-buildable for this plot: the checked files are not an original-versus-replication "
                f"D/N pair table.{expected_clause}{detail_clause}"
            )
        if "review_catalog_source_for_integration" in steps:
            return (
                "Confirmed auxiliary rather than row-ready: the cataloged source is useful context, but the current "
                f"files are better treated as metadata, sidecar, or validation material than as a cleaner D/N pair table.{expected_clause}{detail_clause}"
            )
        if blocker_text and step_text:
            return f"Could not confirm usable pairs under current rules: {blocker_text}; next step is {step_text}.{expected_clause}{detail_clause}"
        if blocker_text:
            return f"Could not confirm usable pairs under current rules: {blocker_text}.{expected_clause}{detail_clause}"
        if step_text:
            return f"Could not confirm usable pairs yet: fit is unresolved until we {step_text}.{expected_clause}{detail_clause}"
        catalog_rows = int(pd.to_numeric(group["catalog_file_rows"], errors="coerce").fillna(0).sum())
        catalog_usable = int(pd.to_numeric(group["catalog_usable_pair_rows"], errors="coerce").fillna(0).sum())
        if catalog_rows and not catalog_usable:
            return (
                f"Confirmed no usable pair rows in the checked catalog: {catalog_rows:,} catalog row(s) were present, "
                "but none were marked as auditable original-versus-replication D/Z and N pairs for this figure."
            )
        return (
            "Could not confirm usable pairs yet: the source is checked but not currently promoted to auditable "
            f"row-level D/Z and N pairs for this figure.{expected_clause}{detail_clause}"
        )

    display_records: list[dict[str, object]] = []
    for _, group in joined.groupby("display_family_key", sort=False):
        group = group.copy()
        group_sorted = group.sort_values(
            ["kept_for_figure", "plot_rows_made_in", "display_label"],
            ascending=[False, False, True],
        )
        first = group_sorted.iloc[0]
        kept = int(pd.to_numeric(group["kept_for_figure"], errors="coerce").fillna(0).sum())
        status = family_status(group, kept)
        record = {
            "plot_name": "Plot 1",
            "display_family_key": safe_text(first.get("display_family_key")),
            "display_label": safe_text(first.get("display_family_label")),
            "source_key": safe_text(first.get("display_family_key")),
            "citation_key": citation_cluster(group["citation_key"]),
            "plot_inclusion_status": status,
            "audit_row_count": len(group),
            "source_materials": unique_nonempty(group["display_material_label"], limit=8),
            "canonical_source_labels": unique_nonempty(group["display_material_label"], limit=8),
            "corpus_what_it_is": safe_text(first.get("source_family_description")),
            "plot_rows_made_in": kept,
            "kept_for_figure": kept,
            "blocked_no_DZ": int(pd.to_numeric(group["blocked_no_DZ"], errors="coerce").fillna(0).sum()),
            "blocked_no_N": int(pd.to_numeric(group["blocked_no_N"], errors="coerce").fillna(0).sum()),
            "blocked_N_lt_10": int(pd.to_numeric(group["blocked_N_lt_10"], errors="coerce").fillna(0).sum()),
            "blocked_replication_N_le_original_N": int(
                pd.to_numeric(group["blocked_replication_N_le_original_N"], errors="coerce").fillna(0).sum()
            ),
            "live_pair_rows": int(pd.to_numeric(group["live_pair_rows"], errors="coerce").fillna(0).sum()),
            "expected_candidate_rows": expected_rows_from_staged_paths(group["staged_paths"]),
            "audit_statuses": unique_nonempty(group["audit_status"], limit=5),
            "normalization_issues": unique_nonempty(group["normalization_issue"], limit=5),
        }
        record["corpus_what_it_is_why_possible_candidate"] = family_candidate_description(record, group)
        record["why_in_out"] = family_reason(record, group)
        display_records.append(record)

    corpus_rows = pd.DataFrame(display_records)
    status_order = {"included": 0, "integrated_not_plotted": 1, "support_only": 2, "not_included": 3}
    corpus_rows["status_sort"] = corpus_rows["plot_inclusion_status"].map(status_order).fillna(9)
    corpus_rows = corpus_rows.sort_values(
        ["kept_for_figure", "status_sort", "display_label"],
        ascending=[False, True, True],
    )
    corpus_rows.drop(columns=["status_sort"]).to_csv(display_csv, index=False)
    plotted = corpus_rows.loc[corpus_rows["plot_inclusion_status"] == "included"].copy()
    integrated_not_plotted = corpus_rows.loc[corpus_rows["plot_inclusion_status"] == "integrated_not_plotted"].copy()
    support = corpus_rows.loc[corpus_rows["plot_inclusion_status"] == "support_only"].copy()
    excluded = corpus_rows.loc[corpus_rows["plot_inclusion_status"] == "not_included"].copy()
    preview = fig2_details.sort_values(["source_dataset", "project", "pair_id"]).head(12)

    lines = [
        "## Corpora Considered",
        "",
        f"Machine-readable display table: [plot1_replication_source_display_table.csv](../data/derived/effect_inflation_dataset/{display_csv.name})",
        "",
        f"Full audit catalog: [plot1_replication_source_catalog.csv](../data/derived/effect_inflation_dataset/{out_csv.name}); normalization worklist: [plot1_replication_source_normalization_worklist.csv](../data/derived/effect_inflation_dataset/{normalization_csv.name})",
        "",
        f"Plot 1 currently includes `{len(plotted):,}` source families in the rendered Figure 2 rule subset, has `{len(integrated_not_plotted):,}` integrated live source families that contribute zero rows after the rule gate, tracks `{len(support):,}` support-only integrated sources, and leaves `{len(excluded):,}` checked families out of the rendered plot.",
        "",
        "This table is normalized to source families for reading. The full audit catalog keeps lower-level artifacts, aliases, lead handles, and project slices so the roll-up is reversible.",
        "",
        markdown_table_block(
            [["Source considered", "What it is/Why Possible Candidate", "Why in/out", "Kept<br>for Figure", "No<br>D/Z", "No<br>N", "N<br>< 10", "Rep N <=<br>Orig N"]]
            + [
                [
                    source_key_badge(row.display_label, row.source_key, row.citation_key),
                    safe_text(row.corpus_what_it_is_why_possible_candidate),
                    safe_text(row.why_in_out),
                    fmt_int(row.kept_for_figure),
                    fmt_int(row.blocked_no_DZ),
                    fmt_int(row.blocked_no_N),
                    fmt_int(row.blocked_N_lt_10),
                    fmt_int(row.blocked_replication_N_le_original_N),
                ]
                for row in corpus_rows.itertuples(index=False)
            ],
            "dataset-table source-audit-table combined-source-audit-table",
        ),
        "",
        "## Specific Observations Included",
        "",
        f"Machine-readable pair-level file: [plot1_replication_pair_details.csv](../data/derived/effect_inflation_dataset/{PLOT1_PAIR_DETAILS.name})",
        "",
        f"The specific-observation layer has `{len(fig2_details):,}` Figure 2 rows. It records the source, smaller-`N` and larger-`N` paper labels/DOIs where available, endpoint, each side's `D` and `N`, and `D_larger_N_minus_smaller_N`.",
        "",
        "Preview of the first specific pair rows in source order:",
        "",
        markdown_table_block(
            [["Source", "Smaller-N paper", "Larger-N paper", "Outcome", "Smaller-N D/N", "Larger-N D/N", "D diff"]]
            + [
                [
                    source_key_badge(
                        row.source_dataset,
                        row.source_dataset,
                        plot1_citation_key(row.source_dataset),
                    ),
                    paper_ref(safe_text(row.smaller_N_paper_title)[:90], row.smaller_N_paper_doi),
                    paper_ref(safe_text(row.larger_N_paper_title)[:90], row.larger_N_paper_doi),
                    safe_text(row.outcome)[:70],
                    f"{fmt_number(row.D_smaller_N)} / {fmt_int(row.N_smaller_N)}",
                    f"{fmt_number(row.D_larger_N)} / {fmt_int(row.N_larger_N)}",
                    fmt_number(row.D_larger_N_minus_smaller_N),
                ]
                for row in preview.itertuples(index=False)
            ],
            "dataset-table specific-observation-table replication-observation-table",
        ),
        "",
        "### What Is Still Missing",
        "",
        "- The remaining Plot 1 work is now substantive: access blocks, native-metric decisions, or missing machine-readable pair payloads.",
        "- A few integrated families still retain artifact-level detail in the full audit catalog, but the reader-facing table is normalized to source families.",
        "- Some support-only and cross-check sources still need a sharper distinction between `does not contribute rows` and `duplicate validation source`.",
    ]
    write_qmd_with_table(PLOT1_SOURCES_QMD, lines)


def write_plot1_criteria_matrix() -> None:
    all_pairs = pd.read_csv(REPLICATION_ALL)
    fig2 = pd.read_csv(REPLICATION_CSV)
    out_csv = DATASET_DERIVED_DIR / "plot1_replication_criteria_matrix.csv"
    column_criteria_csv = DATASET_DERIVED_DIR / "plot1_replication_source_column_criteria.csv"

    source_rows: list[dict[str, object]] = []
    source_datasets = sorted(
        set(all_pairs["source_dataset"].fillna("").astype(str)) | set(fig2["source_dataset"].fillna("").astype(str))
    )
    for source_dataset in source_datasets:
        dataset_label = safe_text(source_dataset)
        group = all_pairs.loc[all_pairs["source_dataset"].fillna("").astype(str) == dataset_label].copy()
        has_effect = group["D_original"].notna() & group["D_replication"].notna()
        no_dz = ~has_effect
        no_n = has_effect & (group["N_original"].isna() | group["N_replication"].isna())
        has_both_sides = has_effect & group["N_original"].notna() & group["N_replication"].notna()
        n_lt_10 = has_both_sides & ((group["N_original"] < 10) | (group["N_replication"] < 10))
        replication_n_le_original_n = has_both_sides & ~n_lt_10 & (group["N_replication"] <= group["N_original"])
        fig2_rows = int((fig2["source_dataset"] == source_dataset).sum())
        source_rows.append(
            {
                "source_dataset": dataset_label,
                "display_label": PLOT1_DISPLAY_LABELS.get(dataset_label, dataset_label),
                "citation_key": plot1_citation_key(dataset_label),
                "live_rows": len(group),
                "kept_for_figure": fig2_rows,
                "blocked_no_DZ": int(no_dz.sum()),
                "blocked_no_N": int(no_n.sum()),
                "blocked_N_lt_10": int(n_lt_10.sum()),
                "blocked_replication_N_le_original_N": int(replication_n_le_original_n.sum()),
            }
        )

    matrix = pd.DataFrame(source_rows).sort_values(
        ["kept_for_figure", "blocked_no_DZ", "blocked_no_N", "blocked_N_lt_10", "blocked_replication_N_le_original_N", "source_dataset"],
        ascending=[False, False, False, False, False, True],
    )
    matrix.to_csv(out_csv, index=False)

    total_rows = len(all_pairs)
    total_fig2 = len(fig2)
    has_effect = all_pairs["D_original"].notna() & all_pairs["D_replication"].notna()
    no_dz = ~has_effect
    no_n = has_effect & (all_pairs["N_original"].isna() | all_pairs["N_replication"].isna())
    has_both_sides = has_effect & all_pairs["N_original"].notna() & all_pairs["N_replication"].notna()
    n_lt_10 = has_both_sides & ((all_pairs["N_original"] < 10) | (all_pairs["N_replication"] < 10))
    replication_n_le_original_n = has_both_sides & ~n_lt_10 & (
        all_pairs["N_replication"] <= all_pairs["N_original"]
    )
    live_rows_kept = int((has_both_sides & ~n_lt_10 & ~replication_n_le_original_n).sum())
    appendix_fallback_kept = max(0, total_fig2 - live_rows_kept)

    column_criteria = pd.DataFrame(
        [
            {
                "column": "Source considered",
                "criterion": (
                    "Use the reader-facing canonical source family after alias normalization. Cite the family-level "
                    "bibliographic key. Do not list every raw artifact here; artifact-level provenance belongs in the full audit catalog."
                ),
            },
            {
                "column": "What it is/Why Possible Candidate",
                "criterion": (
                    "State what the source is, then state why it was treated as a possible pair source. The rationale must say whether "
                    "the source explicitly links original findings to replications/follow-ups, is a direct-replication or multi-lab project, "
                    "is a pilot/full-scale or repeated-study source, or is retained as support/cross-check material. End with a pair-count "
                    "basis: live structured rows, staged expected rows, catalog usable rows, catalog rows checked, or no concrete count verified."
                ),
            },
            {
                "column": "Why in/out",
                "criterion": (
                    "Report the audit outcome under the current Plot 1 rules. Use explicit status language: confirmed usable; confirmed usable "
                    "with exclusions; confirmed usable fallback; confirmed present but not usable; confirmed no usable pair payload at the checked "
                    "location; could not confirm usable pairs because access/download/parser/data are blocked; support-only; or no usable pair rows "
                    "in the checked catalog. If rows or payloads exist but are not used, say why: native metric, conversion policy missing, original side "
                    "missing, not pair-buildable, no machine-readable pair table, or access restriction."
                ),
            },
            {
                "column": "Kept for Figure",
                "criterion": (
                    "Count source-family rows that pass all Plot 1 row gates and appear in the rendered figure. Includes any approved catalog/backfill "
                    "fallback rows. Zero means no row from that source family appears in the figure, not necessarily that no local material exists."
                ),
            },
            {
                "column": "No D/Z",
                "criterion": (
                    "For live integrated pair rows, count rows failing first because either original or replication side lacks a common D/Z-convertible "
                    "effect. This gate is evaluated before sample-size gates. Non-integrated staged-only sources usually show zero here; their blockers "
                    "are described in Why in/out."
                ),
            },
            {
                "column": "No N",
                "criterion": (
                    "For live integrated pair rows that have D/Z on both sides, count rows failing because either original or replication N is missing. "
                    "Rows already counted under No D/Z are not counted here."
                ),
            },
            {
                "column": "N < 10",
                "criterion": (
                    "For live integrated pair rows with D/Z and N on both sides, count rows failing because at least one side has N below 10. Rows already "
                    "counted under No D/Z or No N are not counted here."
                ),
            },
            {
                "column": "Rep N <= Orig N",
                "criterion": (
                    "For live integrated pair rows with D/Z, N on both sides, and both N values at least 10, count rows failing because the replication or "
                    "follow-up N is not larger than the original N. This is the last row gate, so these counts are mutually exclusive with the earlier gate columns."
                ),
            },
        ]
    )
    column_criteria.to_csv(column_criteria_csv, index=False)

    lines = [
        "## Inclusion Criteria",
        "",
        "Plot 1 keeps a row in the rendered Figure 2 subset when:",
        "",
        "1. the row has an original side and a follow-up side with a common `D`/`Z`-convertible effect measure,",
        "2. both sides have `N`,",
        "3. both sides have `N >= 10`,",
        "4. and the follow-up/replication `N` is larger than the original `N`.",
        "",
        f"Across the `{total_rows:,}` live Plot 1 pair rows, `{live_rows_kept:,}` pass those gates, `{int(no_dz.sum()):,}` are blocked by missing `D`/`Z`-convertible effects, `{int(no_n.sum()):,}` are blocked by missing `N`, `{int(n_lt_10.sum()):,}` are blocked by `N < 10`, and `{int(replication_n_le_original_n.sum()):,}` are blocked because replication `N <=` original `N`. The rendered figure has `{total_fig2:,}` rows because `{appendix_fallback_kept:,}` Appendix D fallback rows are already plot-ready and are counted directly as kept.",
        "",
        f"Machine-readable gate matrix: [plot1_replication_criteria_matrix.csv](../data/derived/effect_inflation_dataset/{out_csv.name})",
        "",
        f"Machine-readable source-table column criteria: [plot1_replication_source_column_criteria.csv](../data/derived/effect_inflation_dataset/{column_criteria_csv.name})",
        "",
        "### Source-table column criteria",
        "",
        "These definitions govern the `Corpora Considered` table below. They are intentionally explicit so source-audit language does not drift as new leads are checked.",
        "",
        markdown_table_block(
            [["Column", "Criterion"]]
            + [[str(row.column), str(row.criterion)] for row in column_criteria.itertuples(index=False)],
            "dataset-table dataset-criteria-table source-column-criteria-table",
        ),
        "",
        "The source-by-source gate counts are folded into the combined `Corpora Considered` table below so the qualitative inclusion notes and quantitative rule outcomes stay on the same row.",
    ]
    write_qmd_with_table(PLOT1_CRITERIA_QMD, lines)


def plot2_candidate_description(row: object) -> str:
    source_corpus = safe_text(getattr(row, "source_corpus", ""))
    source_label = safe_text(getattr(row, "source_label", "")) or safe_text(getattr(row, "display_label", ""))
    source_key = safe_text(getattr(row, "source_key", ""))
    for key in [source_corpus, source_key, source_label, plot2_display_label(source_corpus or source_label)]:
        if key in PLOT2_SOURCE_DESCRIPTIONS:
            return PLOT2_SOURCE_DESCRIPTIONS[key]
    what_it_is = safe_text(getattr(row, "corpus_what_it_is", ""))
    why_detail = safe_text(getattr(row, "why_detail", ""))
    if what_it_is and why_detail:
        return f"{what_it_is} Possible candidate because {why_detail[:1].lower() + why_detail[1:]}"
    return what_it_is or why_detail or "Candidate source family considered for Plot 2 paper-level D/N extraction."


def plot2_gate_phrase(label: str, value: object, denominator: object) -> str:
    if pd.isna(value) or safe_text(value) == "":
        return f"{label}: unknown"
    count = int(value)
    if count <= 0:
        return f"{label}: no"
    if not pd.isna(denominator) and safe_text(denominator) != "":
        denom = int(denominator)
        if denom > 0 and count != denom:
            return f"{label}: {count:,}/{denom:,}"
    return f"{label}: yes ({count:,})"


def plot2_confirmed_fields(row: object) -> str:
    known_papers = getattr(row, "known_paper_units", pd.NA)
    known_tests = getattr(row, "known_test_rows", pd.NA)
    scope_parts = []
    if not pd.isna(known_papers):
        scope_parts.append(f"{int(known_papers):,} paper units")
    if not pd.isna(known_tests):
        scope_parts.append(f"{int(known_tests):,} test/effect rows")
    if not scope_parts:
        scope_parts.append("source count not confirmed locally")
    gate_parts = [
        plot2_gate_phrase("journal provenance", getattr(row, "rows_with_direct_journal_provenance", pd.NA), known_papers),
        plot2_gate_phrase("paper grouping", getattr(row, "rows_with_paper_grouping", pd.NA), known_papers),
        plot2_gate_phrase("paper D/N", getattr(row, "rows_with_paper_level_dn", pd.NA), known_papers),
        plot2_gate_phrase("main selector", getattr(row, "rows_with_explicit_main_selector", pd.NA), known_papers),
    ]
    return f"Known: {', '.join(scope_parts)}. Confirmed: {'; '.join(gate_parts)}."


def plot2_inclusion_rationale(row: object) -> str:
    included = safe_text(getattr(row, "plot_inclusion_status", "")) == "included"
    status = safe_text(getattr(row, "status_label", ""))
    detail = safe_text(getattr(row, "why_detail", "")) or safe_text(getattr(row, "why", ""))
    decision = "Included" if included else "Not included"
    if status and detail:
        return f"{decision}: {status}. {detail}"
    if status:
        return f"{decision}: {status}."
    if detail:
        return f"{decision}: {detail}"
    return f"{decision}: no additional source-specific note recorded."


def build_plot2_criteria_matrix_frame(
    plot2: pd.DataFrame,
    source_list: pd.DataFrame,
    source_status: pd.DataFrame,
) -> pd.DataFrame:
    list_lookup = {
        safe_text(row.source_corpus): row
        for row in source_list.itertuples(index=False)
        if safe_text(row.source_corpus)
    }
    status_lookup = {
        safe_text(row.source).lower(): row
        for row in source_status.itertuples(index=False)
        if safe_text(row.source)
    }
    for row in source_status.itertuples(index=False):
        source_corpus = PLOT2_STATUS_TO_CORPUS.get(safe_text(row.source).lower(), "")
        if source_corpus:
            status_lookup[source_corpus] = row

    override_counts = {
        "olivier 2024 cardiovascular rcts": {"known_paper_units": 344, "paper_level_dn_rows": 263},
    }

    matrix_rows: list[dict[str, object]] = []
    for row in plot2.itertuples(index=False):
        label = safe_text(row.source_label)
        corpus = safe_text(row.source_corpus)
        status_row = status_lookup.get(label.lower()) or status_lookup.get(corpus)
        list_row = list_lookup.get(corpus) if corpus else None
        override = override_counts.get(label.lower(), {})

        known_paper_units = pd.NA
        known_test_rows = pd.NA
        if list_row is not None and not pd.isna(getattr(list_row, "n_papers", pd.NA)):
            known_paper_units = int(getattr(list_row, "n_papers"))
        elif not pd.isna(row.papers_contributed) and int(row.papers_contributed) > 0:
            known_paper_units = int(row.papers_contributed)
        if not pd.isna(row.papers_contributed) and int(row.papers_contributed) > 0:
            known_paper_units = max(
                0 if pd.isna(known_paper_units) else int(known_paper_units),
                int(row.papers_contributed),
            )
        if "known_paper_units" in override:
            known_paper_units = int(override["known_paper_units"])

        if list_row is not None and not pd.isna(getattr(list_row, "n_rows", pd.NA)):
            known_test_rows = int(getattr(list_row, "n_rows"))
        elif not pd.isna(row.tests_or_rows_contributed) and int(row.tests_or_rows_contributed) > 0:
            known_test_rows = int(row.tests_or_rows_contributed)
        if not pd.isna(row.tests_or_rows_contributed) and int(row.tests_or_rows_contributed) > 0:
            known_test_rows = max(
                0 if pd.isna(known_test_rows) else int(known_test_rows),
                int(row.tests_or_rows_contributed),
            )
        if "known_test_rows" in override:
            known_test_rows = int(override["known_test_rows"])

        if status_row is not None:
            peer_review_status = safe_text(status_row.peer_reviewed_journal_plus_D_N).lower()
            main_result_status = safe_text(status_row.can_identify_main_treatment_result).lower()
        else:
            peer_review_status = ""
            main_result_status = ""
        source_kind_text = safe_text(getattr(row, "source_kind", "")).lower()
        published_scope_text = safe_text(getattr(row, "published_scope", "")).lower()
        if not peer_review_status:
            if (
                "published_article" in source_kind_text
                or "published_original_psychology_article" in source_kind_text
                or "sampled_psychology_articles" in published_scope_text
                or "random_sample_psychology_articles" in published_scope_text
            ):
                peer_review_status = "yes"
            elif "registry_results" in source_kind_text or "clinicaltrials_gov_results" in published_scope_text:
                peer_review_status = "no"

        rows_with_direct_journal_provenance = (
            int(known_paper_units) if not pd.isna(known_paper_units) and peer_review_status in {"yes", "probably"} else 0
        )
        rows_with_paper_grouping = int(known_paper_units) if not pd.isna(known_paper_units) else 0
        rows_with_paper_level_dn = (
            int(known_paper_units)
            if list_row is not None
            and not pd.isna(getattr(list_row, "median_D", pd.NA))
            and not pd.isna(getattr(list_row, "median_N", pd.NA))
            else 0
        )
        if "paper_level_dn_rows" in override:
            rows_with_paper_level_dn = int(override["paper_level_dn_rows"])
        elif int(row.papers_contributed or 0) > 0:
            rows_with_paper_level_dn = max(rows_with_paper_level_dn, int(row.papers_contributed))

        rows_with_explicit_main_selector = (
            int(known_paper_units)
            if not pd.isna(known_paper_units) and main_result_status in {"yes", "yes-ish"}
            else 0
        )
        rows_with_implemented_paper_collapse = int(row.papers_contributed or 0)

        matrix_rows.append(
            {
                "source_label": label,
                "source_corpus": corpus,
                "source_key": safe_text(getattr(row, "source_key", "")) or corpus or slugify(label, "plot2_source"),
                "known_paper_units": known_paper_units,
                "known_test_rows": known_test_rows,
                "rows_with_direct_journal_provenance": rows_with_direct_journal_provenance,
                "rows_with_paper_grouping": rows_with_paper_grouping,
                "rows_with_paper_level_dn": rows_with_paper_level_dn,
                "rows_with_explicit_main_selector": rows_with_explicit_main_selector,
                "rows_with_implemented_paper_collapse": rows_with_implemented_paper_collapse,
                "rows_currently_plotted": int(row.papers_contributed or 0) if row.plot_inclusion_status == "included" else 0,
                "plot_inclusion_status": safe_text(row.plot_inclusion_status),
                "status_label": safe_text(row.status_label),
                "why_detail": safe_text(row.why_detail),
            }
        )

    matrix = pd.DataFrame(matrix_rows).sort_values(
        ["rows_currently_plotted", "rows_with_paper_level_dn", "known_paper_units", "source_label"],
        ascending=[False, False, False, True],
    )
    matrix["display_label"] = matrix.apply(
        lambda r: plot2_display_label(safe_text(r.get("source_corpus")) or safe_text(r.get("source_label"))),
        axis=1,
    )
    matrix["citation_key"] = matrix.apply(
        lambda r: citation_key_from(
            PLOT2_CITATION_KEYS,
            r.get("source_label"),
            r.get("source_corpus"),
            r.get("display_label"),
            r.get("source_key"),
        ),
        axis=1,
    )
    return matrix


def write_plot2_source_catalog() -> None:
    papers = pd.read_csv(PUBLISHED_PAPERS)
    source_list = pd.read_csv(PUBLISHED_SOURCE_LIST)
    source_status = pd.read_csv(PUBLISHED_SOURCE_STATUS)
    out_csv = DATASET_DERIVED_DIR / "plot2_published_source_catalog.csv"

    papers["D_median"] = numeric_series(papers["D_median"]).abs()
    papers["N_median"] = numeric_series(papers["N_median"])
    papers["n_rows"] = numeric_series(papers["n_rows"]) if "n_rows" in papers.columns else 1
    main = papers[
        papers["published_original_candidate"].map(as_bool)
        & ~papers["comparator_only"].map(as_bool)
    ].copy()
    main = main[(main["D_median"] > 0) & (main["N_median"] > 0)].copy()

    def compact_unique(values: Iterable[object], limit: int = 4) -> str:
        unique = [safe_text(value) for value in values if safe_text(value)]
        deduped = list(dict.fromkeys(unique))
        if len(deduped) > limit:
            return "; ".join(deduped[:limit]) + f"; +{len(deduped) - limit} more"
        return "; ".join(deduped)

    def humanize(value: object) -> str:
        return safe_text(value).replace("_", " ")

    included_counts = (
        main.groupby("source_corpus", dropna=False)
        .agg(
            papers_contributed=("unit_id", "count"),
            tests_used=("n_rows", "sum"),
            median_D=("D_median", "median"),
            median_N=("N_median", "median"),
            fields=("field", compact_unique),
            source_kind=("source_kind", compact_unique),
            published_scope=("published_scope", compact_unique),
        )
        .reset_index()
    )
    included_counts["source_corpus"] = included_counts["source_corpus"].fillna("").astype(str)
    included_corpora = set(included_counts["source_corpus"].dropna().astype(str))
    all_candidate_counts = (
        papers[(papers["D_median"] > 0) & (papers["N_median"] > 0)]
        .groupby("source_corpus", dropna=False)
        .agg(
            papers_contributed=("unit_id", "count"),
            tests_used=("n_rows", "sum"),
            median_D=("D_median", "median"),
            median_N=("N_median", "median"),
            fields=("field", compact_unique),
            source_kind=("source_kind", compact_unique),
            published_scope=("published_scope", compact_unique),
        )
        .reset_index()
    )
    all_candidate_counts["source_corpus"] = all_candidate_counts["source_corpus"].fillna("").astype(str)

    status_by_corpus: dict[str, object] = {}
    for row in source_status.itertuples(index=False):
        source_key = safe_text(row.source).lower()
        source_corpus = PLOT2_STATUS_TO_CORPUS.get(source_key, "")
        if source_corpus and source_corpus not in status_by_corpus:
            status_by_corpus[source_corpus] = row

    list_by_corpus: dict[str, object] = {}
    for row in source_list.itertuples(index=False):
        source_corpus = safe_text(row.source_corpus)
        if source_corpus and source_corpus not in list_by_corpus:
            list_by_corpus[source_corpus] = row

    rows: list[dict[str, object]] = []
    seen_keys: set[str] = set()

    def add_row(source_label: str, source_corpus: str, inclusion_status: str, why: str, why_detail: str, **extra: object) -> None:
        display_key = plot2_display_label(source_corpus or source_label).lower()
        candidate_keys = {
            source_corpus.lower() if source_corpus else "",
            source_label.lower(),
            display_key,
        }
        candidate_keys = {key for key in candidate_keys if key}
        if seen_keys.intersection(candidate_keys):
            return
        seen_keys.update(candidate_keys)
        rows.append(
            {
                "plot_name": "Plot 2",
                "plot_inclusion_status": inclusion_status,
                "source_label": source_label,
                "source_corpus": source_corpus,
                "papers_contributed": extra.get("papers_contributed", 0),
                "tests_or_rows_contributed": extra.get("tests_or_rows_contributed", 0),
                "why": why,
                "why_detail": why_detail,
                "status_label": extra.get("status_label", ""),
                "fields": extra.get("fields", ""),
                "source_kind": extra.get("source_kind", ""),
                "published_scope": extra.get("published_scope", ""),
                "median_D": extra.get("median_D", pd.NA),
                "median_N": extra.get("median_N", pd.NA),
            }
        )

    for match in included_counts.sort_values(["papers_contributed", "source_corpus"], ascending=[False, True]).itertuples(index=False):
        source_corpus = safe_text(match.source_corpus)
        source_label = plot2_display_label(source_corpus)
        status_row = status_by_corpus.get(source_corpus)
        list_row = list_by_corpus.get(source_corpus)
        status_label = (
            safe_text(getattr(status_row, "current_status", ""))
            or safe_text(getattr(list_row, "status", ""))
            or "included candidate source"
        )
        detail = (
            safe_text(getattr(status_row, "why", ""))
            or safe_text(getattr(list_row, "notes", ""))
            or (
                f"{humanize(match.source_kind)}; scope: {humanize(match.published_scope)}; "
                f"field(s): {humanize(match.fields)}"
            )
        )
        add_row(
            source_label,
            source_corpus,
            "included",
            "current published-paper figure includes this source corpus",
            detail,
            papers_contributed=int(match.papers_contributed),
            tests_or_rows_contributed=int(match.tests_used),
            status_label=status_label,
            fields=match.fields,
            source_kind=match.source_kind,
            published_scope=match.published_scope,
            median_D=match.median_D,
            median_N=match.median_N,
        )

    for row in source_status.itertuples(index=False):
        source_label = safe_text(row.source)
        source_key = source_label.lower()
        source_corpus = PLOT2_STATUS_TO_CORPUS.get(source_key, "")
        matched = included_counts.loc[included_counts["source_corpus"] == source_corpus]
        if not matched.empty:
            match = matched.iloc[0]
            add_row(
                source_label,
                source_corpus,
                "included",
                "current published-paper figure includes this source corpus",
                safe_text(row.why),
                papers_contributed=int(match["papers_contributed"]),
                tests_or_rows_contributed=int(match["tests_used"]),
                status_label=safe_text(row.current_status),
            )
        else:
            add_row(
                source_label,
                source_corpus,
                "not_included",
                safe_text(row.current_status),
                safe_text(row.why),
                status_label=safe_text(row.current_status),
            )

    for row in source_list.itertuples(index=False):
        source_label = safe_text(row.name)
        source_corpus = safe_text(row.source_corpus)
        matched = included_counts.loc[included_counts["source_corpus"] == source_corpus]
        if not matched.empty:
            match = matched.iloc[0]
            add_row(
                source_label,
                source_corpus,
                "included",
                safe_text(row.status),
                safe_text(row.notes),
                papers_contributed=int(match["papers_contributed"]),
                tests_or_rows_contributed=int(match["tests_used"]),
                status_label=safe_text(row.status),
            )
        else:
            add_row(
                source_label,
                source_corpus,
                "not_included",
                safe_text(row.status),
                safe_text(row.notes),
                papers_contributed=int(row.n_papers) if not pd.isna(row.n_papers) else 0,
                tests_or_rows_contributed=int(row.n_rows) if not pd.isna(row.n_rows) else 0,
                status_label=safe_text(row.status),
            )

    for match in all_candidate_counts.sort_values(["papers_contributed", "source_corpus"], ascending=[False, True]).itertuples(index=False):
        source_corpus = safe_text(match.source_corpus)
        if not source_corpus or source_corpus in included_corpora:
            continue
        note = PLOT2_COMPARATOR_ONLY_SOURCE_NOTES.get(source_corpus, {})
        source_label = plot2_display_label(source_corpus)
        detail = (
            safe_text(note.get("why_detail", ""))
            or (
                f"{humanize(match.source_kind)}; scope: {humanize(match.published_scope)}; "
                f"field(s): {humanize(match.fields)}. Local D/N rows exist, but this corpus is not "
                "eligible for the published-paper endpoint figure under the current inclusion policy."
            )
        )
        add_row(
            source_label,
            source_corpus,
            "not_included",
            safe_text(note.get("why", "")) or "local D/N comparator, excluded by policy",
            detail,
            papers_contributed=int(match.papers_contributed),
            tests_or_rows_contributed=int(match.tests_used),
            status_label=safe_text(note.get("status_label", "")) or "local comparator-only source",
            fields=match.fields,
            source_kind=match.source_kind,
            published_scope=match.published_scope,
            median_D=match.median_D,
            median_N=match.median_N,
        )

    plot2 = pd.DataFrame(rows)
    plot2["display_label"] = plot2.apply(
        lambda r: plot2_display_label(safe_text(r.get("source_corpus")) or safe_text(r.get("source_label"))),
        axis=1,
    )
    plot2["source_key"] = plot2.apply(
        lambda r: safe_text(r.get("source_corpus")) or slugify(safe_text(r.get("source_label")), "plot2_source"),
        axis=1,
    )
    plot2["citation_key"] = plot2.apply(
        lambda r: citation_key_from(
            PLOT2_CITATION_KEYS,
            r.get("source_label"),
            r.get("source_corpus"),
            r.get("display_label"),
            r.get("source_key"),
        ),
        axis=1,
    )
    plot2["corpus_what_it_is"] = plot2.apply(
        lambda r: (
            (
                f"{humanize(r.get('source_kind'))}; scope: {humanize(r.get('published_scope'))}; "
                f"field(s): {humanize(r.get('fields'))}."
            )
            if safe_text(r.get("plot_inclusion_status")) == "included"
            else safe_text(r.get("status_label")) or safe_text(r.get("why"))
        ),
        axis=1,
    )
    plot2["plot_rows_made_in"] = np.where(plot2["plot_inclusion_status"] == "included", plot2["papers_contributed"], 0)
    plot2 = plot2.sort_values(["plot_rows_made_in", "source_label"], ascending=[False, True])
    matrix = build_plot2_criteria_matrix_frame(plot2, source_list, source_status)
    matrix.to_csv(DATASET_DERIVED_DIR / "plot2_published_criteria_matrix.csv", index=False)
    gate_cols = [
        "source_key",
        "known_paper_units",
        "known_test_rows",
        "rows_with_direct_journal_provenance",
        "rows_with_paper_grouping",
        "rows_with_paper_level_dn",
        "rows_with_explicit_main_selector",
        "rows_with_implemented_paper_collapse",
        "rows_currently_plotted",
    ]
    plot2_with_gates = plot2.merge(matrix[gate_cols], on="source_key", how="left")
    plot2_with_gates["what_it_is_why_possible_candidate"] = plot2_with_gates.apply(plot2_candidate_description, axis=1)
    plot2_with_gates["confirmed_fields"] = plot2_with_gates.apply(plot2_confirmed_fields, axis=1)
    plot2_with_gates["why_in_out"] = plot2_with_gates.apply(plot2_inclusion_rationale, axis=1)
    plot2_with_gates["n_obs_in"] = numeric_series(plot2_with_gates["plot_rows_made_in"]).fillna(0).astype(int)
    plot2_with_gates.to_csv(out_csv, index=False)

    paper_details = pd.DataFrame(
        {
            "corpus": main["source_corpus"].fillna("").astype(str),
            "field": main.get("field", pd.Series("", index=main.index)).fillna("").astype(str),
            "paper_id": main.get("unit_id", pd.Series("", index=main.index)).fillna("").astype(str),
            "title": main.get("title", pd.Series("", index=main.index)).fillna("").astype(str),
            "D_paper": main["D_median"],
            "N_paper": main["N_median"],
            "n_tests_used": numeric_series(main.get("n_rows", pd.Series(1, index=main.index))).fillna(1).astype(int),
            "year": numeric_series(main.get("year", pd.Series(index=main.index))),
            "journal": main.get("journal", pd.Series("", index=main.index)).fillna("").astype(str),
            "source_kind": main.get("source_kind", pd.Series("", index=main.index)).fillna("").astype(str),
            "published_scope": main.get("published_scope", pd.Series("", index=main.index)).fillna("").astype(str),
            "D_methods": main.get("D_methods", pd.Series("", index=main.index)).fillna("").astype(str),
            "N_methods": main.get("N_methods", pd.Series("", index=main.index)).fillna("").astype(str),
            "abs_z_implied": numeric_series(main.get("abs_z_median", pd.Series(index=main.index))),
        }
    )
    paper_details["above_two_sample_p05_curve"] = paper_details["D_paper"] >= (2 * Z_05 / np.sqrt(paper_details["N_paper"]))
    paper_details["above_two_sample_p10_curve"] = paper_details["D_paper"] >= (2 * 1.6448536269514722 / np.sqrt(paper_details["N_paper"]))
    paper_details["source_label"] = paper_details["corpus"].map(plot2_display_label)
    paper_details["source_key"] = paper_details["corpus"].map(lambda v: safe_text(v) or slugify(safe_text(v), "plot2_source"))
    paper_details["citation_key"] = paper_details.apply(
        lambda r: citation_key_from(PLOT2_CITATION_KEYS, r.get("corpus"), r.get("source_label"), r.get("source_key")),
        axis=1,
    )
    paper_details.to_csv(PLOT2_PAPER_DETAILS, index=False)

    included = plot2_with_gates.loc[plot2_with_gates["plot_inclusion_status"] == "included"].copy()
    included = included.sort_values(["papers_contributed", "source_label"], ascending=[False, True])
    excluded = plot2_with_gates.loc[plot2_with_gates["plot_inclusion_status"] == "not_included"].copy()
    excluded = excluded.sort_values(["source_label"])
    corpus_rows = pd.concat([included, excluded], ignore_index=True)
    corpus_rows = corpus_rows.sort_values(["plot_rows_made_in", "source_label"], ascending=[False, True])
    preview = (
        paper_details.assign(has_reference=paper_details["title"].fillna("").astype(str).str.strip().ne(""))
        .sort_values(["has_reference", "corpus", "paper_id"], ascending=[False, True, True])
        .head(12)
    )

    lines = [
        "## Corpora Considered",
        "",
        f"Machine-readable catalog: [plot2_published_source_catalog.csv](../data/derived/effect_inflation_dataset/{out_csv.name})",
        "",
        f"Machine-readable gate matrix: [plot2_published_criteria_matrix.csv](../data/derived/effect_inflation_dataset/plot2_published_criteria_matrix.csv)",
        "",
        f"Plot 2 currently uses `{len(included):,}` source corpora in the rendered paper-level cloud and keeps `{len(excluded):,}` considered journal-result sources out of the current figure.",
        "",
        "This is the corpus-level admission audit for Plot 2. It combines the qualitative source note with the current gate counts so the reader can see why each source was considered, what was actually confirmed, why it is in or out, and how many paper/unit rows enter the plotted cloud.",
        "",
        markdown_table_block(
            [["Corpus considered", "What it is / why possible candidate", "Confirmed fields", "Why in/out", "# obs in"]]
            + [
                [
                    source_key_badge(row.display_label or row.source_label or row.source_corpus, row.source_key, row.citation_key),
                    row.what_it_is_why_possible_candidate,
                    row.confirmed_fields,
                    row.why_in_out,
                    fmt_int(row.n_obs_in),
                ]
                for row in corpus_rows.itertuples(index=False)
            ],
            "dataset-table source-audit-table plot2-source-audit-table",
        ),
        "",
        "## Specific Observations Included",
        "",
        f"Machine-readable paper-level file: [plot2_published_paper_details.csv](../data/derived/effect_inflation_dataset/{PLOT2_PAPER_DETAILS.name})",
        "",
        f"The specific-observation layer has `{len(paper_details):,}` plotted paper/unit rows. It records corpus citation, paper/unit id, paper reference text, field, journal/year where available, paper-level `D`, paper-level `N`, and the number of source tests used in the collapse.",
        "",
        "Preview of the first specific paper rows in source order:",
        "",
        markdown_table_block(
            [["Corpus", "Paper/unit id", "Paper/reference", "Field", "Journal/year", "D/N", "Tests used"]]
            + [
                [
                    source_key_badge(row.source_label or row.corpus, row.source_key, row.citation_key),
                    safe_text(row.paper_id)[:80],
                    safe_text(row.title)[:110],
                    safe_text(row.field),
                    f"{safe_text(row.journal)[:50]} {fmt_year(row.year)}".strip(),
                    f"{fmt_number(row.D_paper)} / {fmt_int(row.N_paper)}",
                    fmt_int(row.n_tests_used),
                ]
                for row in preview.itertuples(index=False)
            ],
            "dataset-table specific-observation-table published-observation-table",
        ),
        "",
        "### What Is Still Missing",
        "",
        "- The source-family admission table is now centralized, but several included sources still need more detailed source-specific collapse-rule prose.",
        "- Some included corpora remain paper-level proxies without explicit main-result selectors; those caveats are recorded in the `Why in/out` column rather than hidden.",
        "- The largest excluded candidates need either parser work, a public row-level payload, or a policy decision before they can move into the plotted paper-level cloud.",
    ]
    write_qmd_with_table(PLOT2_SOURCES_QMD, lines)


def write_plot2_criteria_matrix() -> None:
    source_list = pd.read_csv(PUBLISHED_SOURCE_LIST)
    source_status = pd.read_csv(PUBLISHED_SOURCE_STATUS)
    plot2 = pd.read_csv(DATASET_DERIVED_DIR / "plot2_published_source_catalog.csv")
    out_csv = DATASET_DERIVED_DIR / "plot2_published_criteria_matrix.csv"
    matrix = build_plot2_criteria_matrix_frame(plot2, source_list, source_status)
    matrix.to_csv(out_csv, index=False)

    total_plot_papers = int(matrix["rows_currently_plotted"].sum())
    total_plot_sources = int((matrix["rows_currently_plotted"] > 0).sum())
    total_main_selector_ready = int(matrix["rows_with_explicit_main_selector"].sum())
    column_criteria = pd.DataFrame(
        [
            {
                "column": "Corpus considered",
                "criterion": "Name the source family evaluated for Plot 2. Use the canonical display label and citation when available.",
            },
            {
                "column": "What it is / why possible candidate",
                "criterion": "Describe the source type and why it looked like it could contribute published paper-level D/N point estimates.",
            },
            {
                "column": "Confirmed fields",
                "criterion": "Report the local evidence counts: known paper units, known test/effect rows, direct journal provenance, paper grouping, paper-level D/N, and main-result selector availability.",
            },
            {
                "column": "Why in/out",
                "criterion": "State the current Plot 2 decision. If included, name the remaining caveat; if excluded, name the blocking gate rather than just saying unavailable.",
            },
            {
                "column": "# obs in",
                "criterion": "Count plotted paper/unit rows entering the current Plot 2 cloud. Zero means the source is considered but contributes no plotted paper point right now.",
            },
        ]
    )

    lines = [
        f"Machine-readable matrix: [plot2_published_criteria_matrix.csv](../data/derived/effect_inflation_dataset/{out_csv.name})",
        "",
        "The counts below are strict current-layer counts, not best-case theoretical recoverability. If a source only has a `partial` flag for journal provenance or main-result identification, that criterion is counted as `0` here and left to the notes column rather than silently rounded up.",
        "",
        f"Under the current Plot 2 build, `{total_plot_papers:,}` paper points are plotted from `{total_plot_sources:,}` source corpora. Only `{total_main_selector_ready:,}` known paper units come from corpora that already carry an explicit or near-explicit main-result selector, which is why the current figure is still a paper-level published-result cloud rather than a clean main-result-only figure.",
        "",
        "### Source-table column criteria",
        "",
        "These definitions govern the `Corpora Considered` table below. They are intentionally explicit so source-audit language does not drift as new Plot 2 leads are checked.",
        "",
        markdown_table_block(
            [["Column", "Criterion"]]
            + [[str(row.column), str(row.criterion)] for row in column_criteria.itertuples(index=False)],
            "dataset-table dataset-criteria-table source-column-criteria-table",
        ),
        "",
        "The source-by-source gate counts are folded into the combined `Corpora Considered` table below so the qualitative admission note and quantitative rule outcomes stay on the same row.",
    ]
    write_qmd_with_table(PLOT2_CRITERIA_QMD, lines)


def write_plot3_source_catalog() -> None:
    table40 = pd.read_csv(PREREG_TABLE_40)
    table41 = pd.read_csv(PREREG_TABLE_41)
    published = pd.read_csv(PUBLISHED_PAPERS) if PUBLISHED_PAPERS.exists() else pd.DataFrame()
    rep_all = pd.read_csv(REPLICATION_ALL) if REPLICATION_ALL.exists() else pd.DataFrame()

    def replication_rows(projects: set[str] | None = None, source_patterns: list[str] | None = None) -> int:
        if rep_all.empty:
            return 0
        mask = pd.Series(False, index=rep_all.index)
        if projects:
            mask = mask | rep_all.get("project", pd.Series("", index=rep_all.index)).isin(projects)
        if source_patterns:
            text = rep_all[[c for c in ["project", "source_dataset", "pair_id"] if c in rep_all.columns]].astype(str).agg(" ".join, axis=1)
            pattern = "|".join(source_patterns)
            mask = mask | text.str.contains(pattern, case=False, regex=True, na=False)
        return int(mask.sum())

    many_labs_pair_rows = replication_rows(
        {"Many Labs 1", "Many Labs 2", "Many Labs 3", "Many Labs 4", "Many Labs 5"}
    )
    rrr_pair_rows = replication_rows({"Registered Replication Reports", "FReD new RRR"})
    psa_pair_rows = replication_rows(
        source_patterns=[
            r"PSA-002 object orientation",
            r"PSA-006 trolley",
            r"PSA 004 Turri article table rescue",
        ]
    )
    tpp_pair_rows = replication_rows(source_patterns=[r"Transparent Psi Project"])
    rpcb_pair_rows = replication_rows(projects={"RPCB"}, source_patterns=[r"RPCB", r"Cancer Biology"])

    twomey_path = ROOT / "data" / "raw" / "corpus_candidates" / "twomey_2021" / "df_all.csv"
    if twomey_path.exists():
        twomey = pd.read_csv(twomey_path)
        twomey_considered = len(twomey)
        twomey_prereg = int(twomey.get("prereg", pd.Series(dtype=object)).astype(str).str.lower().eq("yes").sum())
        twomey_n_rows = int(numeric_series(twomey.get("n", pd.Series(dtype=float))).gt(0).sum())
    else:
        twomey_considered = 300
        twomey_prereg = 27
        twomey_n_rows = 0

    linden_focal = (
        published.loc[published["source_corpus"].eq("linden_2024_focal_effects")].copy()
        if not published.empty
        else pd.DataFrame()
    )
    linden_random = (
        published.loc[published["source_corpus"].eq("linden_2024_random_effects")].copy()
        if not published.empty
        else pd.DataFrame()
    )
    linden_dn_rows = len(linden_focal) + len(linden_random)
    schaefer_prereg = (
        published.loc[published["source_corpus"].eq("schaefer_schwarz_2019_with_prereg")].copy()
        if not published.empty
        else pd.DataFrame()
    )
    schaefer_prereg = schaefer_prereg[
        (numeric_series(schaefer_prereg.get("D_median", pd.Series(dtype=float))) > 0)
        & (numeric_series(schaefer_prereg.get("N_median", pd.Series(dtype=float))) > 0)
    ].copy()
    schaefer_no_prereg = (
        published.loc[published["source_corpus"].eq("schaefer_schwarz_2019_without_prereg")].copy()
        if not published.empty
        else pd.DataFrame()
    )
    schaefer_no_prereg = schaefer_no_prereg[
        (numeric_series(schaefer_no_prereg.get("D_median", pd.Series(dtype=float))) > 0)
        & (numeric_series(schaefer_no_prereg.get("N_median", pd.Series(dtype=float))) > 0)
    ].copy()
    schaefer_prereg_considered = len(pd.read_csv(SCHAEFER_PREREG_RAW)) if SCHAEFER_PREREG_RAW.exists() else max(len(schaefer_prereg), 93)
    try:
        schaefer_no_prereg_considered = len(pd.read_excel(SCHAEFER_NON_PREREG_RAW)) if SCHAEFER_NON_PREREG_RAW.exists() else max(len(schaefer_no_prereg), 900)
    except Exception:
        schaefer_no_prereg_considered = max(len(schaefer_no_prereg), 900)
    score_prereg, score_prereg_count, score_prereg_left_out = score_prereg_indicated_paper_rows(published)
    manual_prereg = pd.DataFrame(MANUAL_PREREGISTERED_ADDITIONS)
    manual_source_counts = manual_prereg["source_family"].value_counts().to_dict()
    plot3_current = normalize_preregistered_results()
    plot3_source_counts = plot3_current["source_family"].value_counts().to_dict()

    def plot3_source_count(source_family: str) -> int:
        return int(plot3_source_counts.get(source_family, 0))

    scheel_contributed = plot3_source_count("Scheel et al. 2021 preregistered-hypotheses corpus")
    psacr001_contributed = plot3_source_count("Dorison et al. 2022 PSA-CR001 pooled preregistered rows")
    psacr002_contributed = plot3_source_count("PSA-CR002 cognitive reappraisal preregistered hypotheses")
    metaketa_i_contributed = plot3_source_count("EGAP Metaketa I information/accountability pooled PAP row")
    metaketa_iii_contributed = plot3_source_count("EGAP Metaketa III natural-resource monitoring pooled PAP row")
    metaketa_iv_contributed = plot3_source_count("EGAP Metaketa IV community-policing pooled PAP row")
    mousa_contributed = plot3_source_count("Mousa 2020 Iraq soccer social-cohesion preregistered field experiment")
    scheel_quote_candidates = pd.read_csv(SCHEEL_QUOTE_RESCUE_CANDIDATES) if SCHEEL_QUOTE_RESCUE_CANDIDATES.exists() else pd.DataFrame()
    scheel_quote_candidate_rows = len(scheel_quote_candidates)
    scheel_quote_candidates_with_n = int(scheel_quote_candidates.get("N_candidate", pd.Series(dtype=float)).notna().sum()) if not scheel_quote_candidates.empty else 0
    vandenakker_rescue_candidates = pd.read_csv(VANDENAKKER_RESCUE_CANDIDATES) if VANDENAKKER_RESCUE_CANDIDATES.exists() else pd.DataFrame()
    vandenakker_rescue_candidate_rows = len(vandenakker_rescue_candidates)
    vandenakker_median_candidates = pd.read_csv(VANDENAKKER_MEDIAN_CANDIDATES) if VANDENAKKER_MEDIAN_CANDIDATES.exists() else pd.DataFrame()
    vandenakker_median_ready = vandenakker_matched_median_rows()
    vandenakker_median_candidate_rows = len(vandenakker_median_candidates)
    vandenakker_median_ready_rows = len(vandenakker_median_ready)
    vandenakker_median_multi_paper_rows = int(
        (pd.to_numeric(vandenakker_median_ready.get("matched_result_rows", pd.Series(dtype=float)), errors="coerce") > 1).sum()
    ) if not vandenakker_median_ready.empty else 0
    rpcb_preclinical_candidates = pd.read_csv(RPCB_PRECLINICAL_CANDIDATES) if RPCB_PRECLINICAL_CANDIDATES.exists() else pd.DataFrame()
    rpcb_preclinical_candidate_rows = len(rpcb_preclinical_candidates)
    rpcb_preclinical_ready = rpcb_registered_report_median_rows()
    rpcb_preclinical_contributed_rows = len(rpcb_preclinical_ready)
    rpcb_preclinical_registered_result_rows = int(
        pd.to_numeric(
            rpcb_preclinical_ready.get("registered_result_rows", pd.Series(dtype=float)),
            errors="coerce",
        )
        .fillna(0)
        .sum()
    ) if not rpcb_preclinical_ready.empty else 0
    score_text_candidates = pd.read_csv(SCORE_TEXT_CLAIM_CANDIDATES) if SCORE_TEXT_CLAIM_CANDIDATES.exists() else pd.DataFrame()
    score_text_candidate_rows = len(score_text_candidates)
    score_text_ready = score_text_claim_rescue_rows()
    score_text_ready_rows = len(score_text_ready)
    score_total_contributed = len(score_prereg) + score_text_ready_rows
    score_included_papers = set(score_prereg.get("paper_id", pd.Series(dtype=object)).dropna().astype(str))
    score_included_dois = {
        doi
        for doi in (
            score_prereg.get("DOI", pd.Series(dtype=object)).map(normalize_doi_value)
            if not score_prereg.empty
            else pd.Series(dtype=object)
        )
        if doi
    }
    if not score_text_ready.empty:
        score_included_papers.update(score_text_ready.get("paper_id", pd.Series(dtype=object)).dropna().astype(str))
    score_left_out = max(score_prereg_count - len(score_included_papers), 0)
    if not vandenakker_median_ready.empty and score_included_dois:
        vandenakker_median_contributed = vandenakker_median_ready.copy()
        vandenakker_median_contributed["_doi_norm"] = vandenakker_median_contributed.get(
            "doi", pd.Series("", index=vandenakker_median_contributed.index)
        ).map(normalize_doi_value)
        vandenakker_median_contributed = vandenakker_median_contributed.loc[
            ~vandenakker_median_contributed["_doi_norm"].isin(score_included_dois)
        ].copy()
    else:
        vandenakker_median_contributed = vandenakker_median_ready.copy()
    vandenakker_median_contributed_rows = len(vandenakker_median_contributed)
    vandenakker_median_score_duplicates = vandenakker_median_ready_rows - vandenakker_median_contributed_rows

    if COMPARE_OUTCOME_ROWS.exists():
        compare_outcomes = pd.read_csv(COMPARE_OUTCOME_ROWS)
        compare_outcome_rows = len(compare_outcomes)
        compare_primary = int(compare_outcomes.get("section", pd.Series(dtype=object)).astype(str).eq("prespecified_primary").sum())
        compare_secondary = int(compare_outcomes.get("section", pd.Series(dtype=object)).astype(str).eq("prespecified_secondary").sum())
        compare_nonprespec = int(compare_outcomes.get("section", pd.Series(dtype=object)).astype(str).eq("non_prespecified_publication").sum())
    else:
        compare_outcome_rows = 0
        compare_primary = 0
        compare_secondary = 0
        compare_nonprespec = 0
    compare_trials = len(pd.read_csv(COMPARE_TRIALS)) if COMPARE_TRIALS.exists() else 0
    compare_prespecified = compare_primary + compare_secondary

    protzko_local_dn = len(pd.read_csv(PROTZKO_PROMOTED)) if PROTZKO_PROMOTED.exists() else 0
    ctgov_registry = (
        published.loc[published["source_corpus"].eq("ctgov_finer_grained_kg")].copy()
        if not published.empty
        else pd.DataFrame()
    )
    ctgov_dn_rows = int(
        (
            numeric_series(ctgov_registry.get("D_median", pd.Series(dtype=float))) > 0
        )
        .mul(numeric_series(ctgov_registry.get("N_median", pd.Series(dtype=float))) > 0)
        .sum()
    )
    if PREREG_CTGOV_PRIMARY_RANDOMIZED_RESULTS.exists():
        ctgov_clean = pd.read_csv(PREREG_CTGOV_PRIMARY_RANDOMIZED_RESULTS)
    else:
        ctgov_clean = normalize_ctgov_primary_randomized_sidecar_rows()
    ctgov_clean_rows = len(ctgov_clean)
    ctgov_clean_phase2plus = int(
        ctgov_clean.get("phase_2plus_flag", pd.Series(dtype=bool)).astype(bool).sum()
    ) if not ctgov_clean.empty else 0
    ctgov_api = pd.read_csv(CTGOV_API_REGISTERED_ROWS) if CTGOV_API_REGISTERED_ROWS.exists() else pd.DataFrame()
    ctgov_api_medians = (
        pd.read_csv(CTGOV_API_REGISTERED_TRIAL_MEDIANS)
        if CTGOV_API_REGISTERED_TRIAL_MEDIANS.exists()
        else pd.DataFrame()
    )
    ctgov_api_rows = len(ctgov_api)
    ctgov_api_trials = int(ctgov_api["nct_id"].nunique()) if not ctgov_api.empty and "nct_id" in ctgov_api.columns else 0
    ctgov_api_primary_rows = int((ctgov_api.get("outcome_type", pd.Series(dtype=object)) == "PRIMARY").sum())
    ctgov_api_direct_rows = int(
        (
            ctgov_api.get("conversion_method", pd.Series(dtype=object))
            != "two_sided_p_value_proxy_with_api_group_denominators"
        ).sum()
    ) if not ctgov_api.empty else 0
    ctgov_api_p_proxy_rows = max(ctgov_api_rows - ctgov_api_direct_rows, 0)
    clinifact = (
        published.loc[published["source_corpus"].eq("clinifact_published_primary_pairs")].copy()
        if not published.empty
        else pd.DataFrame()
    )
    clinifact_dn_rows = int(
        (
            numeric_series(clinifact.get("D_median", pd.Series(dtype=float))) > 0
        )
        .mul(numeric_series(clinifact.get("N_median", pd.Series(dtype=float))) > 0)
        .sum()
    )
    brodeur_rows = 0
    brodeur_flagged_rows = 0
    brodeur_flagged_papers = 0
    brodeur_prereg_rows = 0
    brodeur_pap_rows = 0
    brodeur_pap_power_rows = 0
    if CANDIDATE_ROWS.exists():
        try:
            candidate_rows = pd.read_csv(
                CANDIDATE_ROWS,
                usecols=["source_corpus", "paper_id", "notes", "D", "N"],
                low_memory=False,
            )
            brodeur = candidate_rows.loc[candidate_rows["source_corpus"].eq("economics_brodeur_2024")].copy()
            brodeur_rows = len(brodeur)
            if not brodeur.empty:
                notes = brodeur.get("notes", pd.Series("", index=brodeur.index)).fillna("").astype(str)
                prereg_flag = notes.str.extract(r"prereg=([^;]+)", expand=False).fillna("").str.strip().str.lower()
                pap_flag = notes.str.extract(r"preanalysisplan=([^;]+)", expand=False).fillna("").str.strip().str.lower()
                pap_power_flag = notes.str.extract(r"pap_power=([^;]+)", expand=False).fillna("").str.strip().str.lower()
                truthy = {"1", "1.0", "true", "yes"}
                is_prereg = prereg_flag.isin(truthy)
                is_pap = pap_flag.isin(truthy)
                is_pap_power = pap_power_flag.isin(truthy)
                flagged = is_prereg | is_pap | is_pap_power
                dn_ready = (numeric_series(brodeur["D"]) > 0) & (numeric_series(brodeur["N"]) > 0)
                brodeur_prereg_rows = int((is_prereg & dn_ready).sum())
                brodeur_pap_rows = int((is_pap & dn_ready).sum())
                brodeur_pap_power_rows = int((is_pap_power & dn_ready).sum())
                brodeur_flagged_rows = int((flagged & dn_ready).sum())
                brodeur_flagged_papers = int(brodeur.loc[flagged & dn_ready, "paper_id"].astype(str).nunique())
        except Exception:
            brodeur_rows = 0
            brodeur_flagged_rows = 0
            brodeur_flagged_papers = 0
            brodeur_prereg_rows = 0
            brodeur_pap_rows = 0
            brodeur_pap_power_rows = 0
    fred_published = (
        published.loc[published["source_corpus"].eq("forrt_fred")].copy()
        if not published.empty
        else pd.DataFrame()
    )
    fred_published_dn_rows = int(
        (
            numeric_series(fred_published.get("D_median", pd.Series(dtype=float))) > 0
        )
        .mul(numeric_series(fred_published.get("N_median", pd.Series(dtype=float))) > 0)
        .sum()
    )
    fred_pair_rows = replication_rows(source_patterns=[r"FReD"])
    nordic_publications_path = (
        ROOT
        / "data"
        / "raw"
        / "publication_bias_direct"
        / "nordic_trial_reporting"
        / "nordic-trial-reporting"
        / "data"
        / "4-created-database"
        / "publications-searches-2023-11-27-corrected-2024-10-01.csv"
    )
    if nordic_publications_path.exists():
        nordic = pd.read_csv(nordic_publications_path, low_memory=False)
        nordic_rows = len(nordic)
        nordic_journal_publications = int(nordic.get("publication_type", pd.Series(dtype=object)).astype(str).eq("Journal publication").sum())
    else:
        nordic_rows = 0
        nordic_journal_publications = 0
    staged_counts: dict[str, dict[str, object]] = {}
    for stage_name in [
        "manyclasses_2__stage.csv",
        "metaketa_iii_2021__stage.csv",
        "metaketa_iv_2021__stage.csv",
        "communication_privacy_2025__stage.csv",
        "retrieval_extinction_rats_2017__stage.csv",
    ]:
        stage_path = HARVEST_STAGED_DIR / stage_name
        if stage_path.exists():
            stage = pd.read_csv(stage_path)
            row = stage.iloc[0].to_dict() if len(stage) else {}
            staged_counts[stage_name] = {
                "path": stage_path,
                "expected_rows": int(pd.to_numeric(pd.Series([row.get("expected_rows", 0)]), errors="coerce").fillna(0).iloc[0]),
                "downloaded_file_count": int(pd.to_numeric(pd.Series([row.get("downloaded_file_count", 0)]), errors="coerce").fillna(0).iloc[0]),
                "promotion_blocker": safe_text(row.get("promotion_blocker", "")),
                "notes": safe_text(row.get("notes", "")),
            }
        else:
            staged_counts[stage_name] = {
                "path": stage_path,
                "expected_rows": 0,
                "downloaded_file_count": 0,
                "promotion_blocker": "",
                "notes": "",
            }
    tess_index = build_tess_study_index()
    tess_index_rows = len(tess_index)
    tess_with_n = int(numeric_series(tess_index.get("sample_size", pd.Series(dtype=float))).gt(0).sum()) if not tess_index.empty else 0
    tess_with_pap = int(tess_index.get("pap_urls", pd.Series(dtype=object)).fillna("").astype(str).str.strip().ne("").sum()) if not tess_index.empty else 0
    tess_with_results = int(tess_index.get("has_summary_results", pd.Series(dtype=bool)).astype(str).str.lower().isin({"true", "1"}).sum()) if not tess_index.empty else 0
    tess_native_candidates = int(tess_index.get("row_status", pd.Series(dtype=object)).astype(str).eq("native_metric_rescue_candidate").sum()) if not tess_index.empty else 0
    polisci_rescue_worklist = build_political_science_rescue_worklist()
    polisci_rescue_rows = len(polisci_rescue_worklist)
    out_csv = DATASET_DERIVED_DIR / "plot3_preregistered_source_catalog.csv"

    plot3 = pd.DataFrame(
        [
            {
                "plot_name": "Plot 3",
                "plot_inclusion_status": "included",
                "source_label": "Schäfer/Schwarz 2019 preregistered psychology articles",
                "corpus_what_it_is": "Preregistered psychology-article key-question effects from the public Schäfer/Schwarz 2019 corpus.",
                "what_it_is_why_possible_candidate": "Preregistered psychology-article key-question effects from Schäfer/Schwarz. Possible Plot 3 candidate because the public coded sample separates preregistered from non-preregistered articles and already provides N plus a converted r/d effect for each usable preregistered key effect.",
                "confirmed_fields": f"Known: {fmt_int(schaefer_prereg_considered)} preregistered coded rows, {fmt_int(len(schaefer_prereg))} D/N-ready rows. Confirmed: analytic preregistration flag: yes ({fmt_int(schaefer_prereg_considered)}); paper grouping: yes ({fmt_int(schaefer_prereg_considered)}); paper D/N: yes ({fmt_int(len(schaefer_prereg))}); support status: not coded.",
                "backing_file": str(PUBLISHED_PAPERS.relative_to(ROOT)),
                "rows_considered": schaefer_prereg_considered,
                "rows_preregistered_equivalent": schaefer_prereg_considered,
                "rows_with_public_local_backing": schaefer_prereg_considered,
                "rows_with_extractable_DN": len(schaefer_prereg),
                "rows_with_non_retracted_source": schaefer_prereg_considered,
                "rows_contributed": len(schaefer_prereg),
                "rows_left_out_within_source": schaefer_prereg_considered - len(schaefer_prereg),
                "why": "included as preregistered key-question effects with local D/N; support status is not coded, so the plot marks them separately",
                "why_in_out": f"Included: {fmt_int(len(schaefer_prereg))} preregistered key-effect rows enter as support-not-coded preregistered results. The {fmt_int(schaefer_prereg_considered - len(schaefer_prereg))} remaining coded rows lack usable positive D/N.",
            },
            {
                "plot_name": "Plot 3",
                "plot_inclusion_status": "included",
                "source_label": "Scheel et al. 2021 preregistered-hypotheses corpus",
                "corpus_what_it_is": "Registered Reports/preregistered-hypothesis table with a recoverable D/N subset.",
                "what_it_is_why_possible_candidate": "Published psychology Registered Reports coded by Scheel et al. as preregistered hypotheses. Possible Plot 3 candidate because each row is an analytically preregistered confirmatory hypothesis and the local appendix table recovers D/N for the extractable subset.",
                "confirmed_fields": f"Known: 71 preregistered hypothesis rows, {fmt_int(len(table40))} D/N-ready result rows, collapsed to {fmt_int(scheel_contributed)} paper dots under the one-dot-per-paper rule. Confirmed: analytic preregistration: yes (71); support status: yes ({fmt_int(len(table40))}); journal provenance: yes ({fmt_int(len(table40))}); paper D/N: yes ({fmt_int(len(table40))}). New quote-stat rescue queue: {fmt_int(scheel_quote_candidate_rows)} candidate statistic rows, {fmt_int(scheel_quote_candidates_with_n)} with candidate N, all marked not strict-ready pending PDF/focal checks.",
                "backing_file": f"{PREREG_TABLE_40.relative_to(ROOT)}; {SCHEEL_QUOTE_RESCUE_CANDIDATES.relative_to(ROOT)}",
                "rows_considered": 71,
                "rows_preregistered_equivalent": 71,
                "rows_with_public_local_backing": 71,
                "rows_with_extractable_DN": len(table40),
                "rows_with_non_retracted_source": 71,
                "rows_contributed": scheel_contributed,
                "rows_left_out_within_source": 71 - len(table40),
                "why": "base preregistered-results corpus already on disk; 32 hypotheses have extractable D/N rows and 39 do not",
                "why_in_out": f"Included: {fmt_int(scheel_contributed)} paper-level median rows enter from {fmt_int(len(table40))} D/N-ready hypotheses. The remaining {fmt_int(71 - len(table40))} Scheel rows are real preregistered hypotheses. The local quote-stat pass now identifies {fmt_int(scheel_quote_candidate_rows)} rescue candidates, but they remain outside strict Plot 3 until their article PDFs verify the exact preregistered-result row and analytic N.",
            },
            {
                "plot_name": "Plot 3",
                "plot_inclusion_status": "included",
                "source_label": "Dorison et al. 2022 PSA-CR001 pooled preregistered rows",
                "corpus_what_it_is": "Pooled primary preregistered PSA-CR001 confirmatory rows.",
                "what_it_is_why_possible_candidate": "PSA-CR001 was a preregistered 52-country COVID-19 framing project. Possible Plot 3 candidate because four primary confirmatory outcomes can be represented as pooled D/N rows rather than as nested country cells.",
                "confirmed_fields": f"Known: {fmt_int(len(table41))} pooled primary outcomes, collapsed to {fmt_int(psacr001_contributed)} paper dot under the one-dot-per-paper rule. Confirmed: analytic preregistration: yes ({fmt_int(len(table41))}); support status: yes ({fmt_int(len(table41))}); pooled N: yes ({fmt_int(len(table41))}); pooled D: yes ({fmt_int(len(table41))}).",
                "backing_file": str(PREREG_TABLE_41.relative_to(ROOT)),
                "rows_considered": len(table41),
                "rows_preregistered_equivalent": len(table41),
                "rows_with_public_local_backing": len(table41),
                "rows_with_extractable_DN": len(table41),
                "rows_with_non_retracted_source": len(table41),
                "rows_contributed": psacr001_contributed,
                "rows_left_out_within_source": 0,
                "why": "adds pooled confirmatory preregistered rows that belong in the same comparison layer",
                "why_in_out": "Included: the four primary PSA-CR001 confirmatory outcomes are represented by one paper median. Country-level cells stay collapsed here to avoid nested non-independent Plot 3 rows.",
            },
            {
                "plot_name": "Plot 3",
                "plot_inclusion_status": "included",
                "source_label": "PSA-CR002 cognitive reappraisal preregistered hypotheses",
                "corpus_what_it_is": "Psychological Science Accelerator COVID-19 cognitive-reappraisal project with article-reported preregistered hypothesis rows.",
                "what_it_is_why_possible_candidate": "PSA-CR002 was considered because the article explicitly labels Table 2 as effect sizes and statistics for each preregistered hypothesis, while Table 3 reports the relevant arm sample sizes after preregistered exclusions.",
                "confirmed_fields": "Known: 12 Table 2 preregistered hypothesis rows, collapsed to 1 paper dot under the one-dot-per-paper rule. Confirmed: analytic preregistration: yes (12); source result selector: Table 2 preregistered hypothesis rows; reported Cohen's d: yes (12); arm/sample N: yes from Table 3 (12); support status: yes.",
                "backing_file": "Wang et al. 2021 Tables 2-3; DOI 10.1038/s41562-021-01173-x",
                "rows_considered": 12,
                "rows_preregistered_equivalent": 12,
                "rows_with_public_local_backing": 12,
                "rows_with_extractable_DN": manual_source_counts.get("PSA-CR002 cognitive reappraisal preregistered hypotheses", 0),
                "rows_with_non_retracted_source": 12,
                "rows_contributed": psacr002_contributed,
                "rows_left_out_within_source": 0,
                "why": "included because it has explicit preregistered hypothesis rows, reported D, and source-reported arm Ns",
                "why_in_out": "Included: 12 preregistered PSA-CR002 Table 2 hypotheses are represented by one paper median. The signs of the reported effects are hypothesis-direction-coded in the article; the plotted D axis uses magnitudes.",
            },
            {
                "plot_name": "Plot 3",
                "plot_inclusion_status": "included",
                "source_label": "PSA004 true-belief/Gettier pooled preregistered row",
                "corpus_what_it_is": "Psychological Science Accelerator true-belief/Gettier cross-cultural conceptual-replication project.",
                "what_it_is_why_possible_candidate": "PSA004 was considered because the public PSA project page and Hall et al. article report a pooled preregistered cross-cultural contrast for standard justified true belief versus Gettier-type cases, with N and an odds ratio.",
                "confirmed_fields": "Known: one pooled standard JTB-versus-Gettier project effect. Confirmed: preregistered PSA project: yes; focal pooled effect: yes; N: 4,724; OR: 1.86; D conversion: yes via Chinn log-OR-to-d.",
                "backing_file": "PSA004 project page and Hall et al. 2024; DOI 10.1177/25152459241267902",
                "rows_considered": 1,
                "rows_preregistered_equivalent": 1,
                "rows_with_public_local_backing": 1,
                "rows_with_extractable_DN": manual_source_counts.get("PSA004 true-belief/Gettier pooled preregistered row", 0),
                "rows_with_non_retracted_source": 1,
                "rows_contributed": manual_source_counts.get("PSA004 true-belief/Gettier pooled preregistered row", 0),
                "rows_left_out_within_source": 1 - manual_source_counts.get("PSA004 true-belief/Gettier pooled preregistered row", 0),
                "why": "included as a pooled preregistered project effect with N and an OR-to-D conversion",
                "why_in_out": "Included: one pooled PSA004 standard JTB-versus-Gettier row enters. This is related to, but not identical with, the Darrel-vignette PSA004 Plot 1 replication-pair rescue; the source catalog flags the cross-plot overlap risk.",
            },
            {
                "plot_name": "Plot 3",
                "plot_inclusion_status": "included",
                "source_label": "ManyBabies 1 infant-directed speech pooled preregistered row",
                "corpus_what_it_is": "ManyBabies 1 pooled infant-directed-speech versus adult-directed-speech preference project.",
                "what_it_is_why_possible_candidate": "ManyBabies 1 was considered because the project page documents a large preregistered many-lab infant study and the AMPPS article reports the pooled primary infant-directed-speech preference effect with N and Cohen's d.",
                "confirmed_fields": "Known: one pooled primary IDS-versus-ADS effect. Confirmed: preregistered many-lab project: yes; focal pooled primary effect: yes; N: 2,329 babies tested; reported Cohen's d: 0.35; Plot 1 duplicate check: no local ManyBabies 1 pair row found.",
                "backing_file": "ManyBabies 1 project page and ManyBabies Consortium 2020; DOI 10.1177/2515245919900809",
                "rows_considered": 1,
                "rows_preregistered_equivalent": 1,
                "rows_with_public_local_backing": 1,
                "rows_with_extractable_DN": manual_source_counts.get("ManyBabies 1 infant-directed speech pooled preregistered row", 0),
                "rows_with_non_retracted_source": 1,
                "rows_contributed": manual_source_counts.get("ManyBabies 1 infant-directed speech pooled preregistered row", 0),
                "rows_left_out_within_source": 1 - manual_source_counts.get("ManyBabies 1 infant-directed speech pooled preregistered row", 0),
                "why": "included as a pooled preregistered many-lab primary result with N and reported D",
                "why_in_out": "Included: one pooled ManyBabies 1 infant-directed-speech preference row enters. Lab, method, age, and language moderator rows are deliberately not added to avoid nested non-independent Plot 3 rows.",
            },
            {
                "plot_name": "Plot 3",
                "plot_inclusion_status": "included",
                "source_label": "ManyBabies 1 Bilingual infant-directed speech pooled preregistered row",
                "corpus_what_it_is": "ManyBabies 1 Bilingual pooled infant-directed-speech versus adult-directed-speech preference project.",
                "what_it_is_why_possible_candidate": "ManyBabies 1 Bilingual was considered because it is the preregistered companion project to ManyBabies 1 and reports the bilingual-infant pooled IDS-versus-ADS preference effect with a standardized within-infant effect size.",
                "confirmed_fields": "Known: one pooled primary bilingual IDS-versus-ADS effect. Confirmed locally from the public analysis repository: preregistered many-lab project: yes; focal pooled bilingual effect: yes; usable bilingual full-dataset N: 324 infants; reported full-dataset bilingual dz: 0.26; Plot 1 duplicate check: no local ManyBabies 1 Bilingual pair row found.",
                "backing_file": "Byers-Heinlein et al. 2021; DOI 10.1177/2515245920974622; public mb1b-analysis repository processed_data/04_full_dataset_diff.csv",
                "rows_considered": 1,
                "rows_preregistered_equivalent": 1,
                "rows_with_public_local_backing": 1,
                "rows_with_extractable_DN": manual_source_counts.get("ManyBabies 1 Bilingual infant-directed speech pooled preregistered row", 0),
                "rows_with_non_retracted_source": 1,
                "rows_contributed": manual_source_counts.get("ManyBabies 1 Bilingual infant-directed speech pooled preregistered row", 0),
                "rows_left_out_within_source": 1 - manual_source_counts.get("ManyBabies 1 Bilingual infant-directed speech pooled preregistered row", 0),
                "why": "included as a pooled preregistered many-lab primary result with usable N and reported standardized effect",
                "why_in_out": "Included: one pooled ManyBabies 1 Bilingual infant-directed-speech preference row enters. The monolingual comparison rows and site/moderator rows are deliberately not added to avoid nested non-independent Plot 3 rows.",
            },
            {
                "plot_name": "Plot 3",
                "plot_inclusion_status": "included",
                "source_label": "ManyClasses 1 feedback pooled preregistered row",
                "corpus_what_it_is": "ManyClasses 1 pooled immediate-versus-delayed-feedback classroom-learning project.",
                "what_it_is_why_possible_candidate": "ManyClasses 1 was considered because the article documents a time-stamped preregistration, public materials/data/scripts, and a single pooled primary classroom-learning estimate for immediate versus delayed feedback timing.",
                "confirmed_fields": "Known: one pooled primary feedback-timing effect across 38 classes. Confirmed: preregistration: yes (OSF registration dated July 22, 2019); source focal selector: overall feedback-timing estimate; N: 2,081 participating students; standardized pooled effect: Δz = 0.002 with 95% HDI [-0.05, 0.05]; support status: no.",
                "backing_file": "Fyfe et al. 2021; DOI 10.1177/25152459211027575",
                "rows_considered": 1,
                "rows_preregistered_equivalent": 1,
                "rows_with_public_local_backing": 1,
                "rows_with_extractable_DN": manual_source_counts.get("ManyClasses 1 feedback pooled preregistered row", 0),
                "rows_with_non_retracted_source": 1,
                "rows_contributed": manual_source_counts.get("ManyClasses 1 feedback pooled preregistered row", 0),
                "rows_left_out_within_source": 1 - manual_source_counts.get("ManyClasses 1 feedback pooled preregistered row", 0),
                "why": "included as a pooled preregistered project result with a standardized Δz effect and source-reported N",
                "why_in_out": "Included: one pooled ManyClasses 1 immediate-versus-delayed-feedback row enters. Class-level estimates and moderator rows are deliberately not added to avoid nested non-independent Plot 3 rows.",
            },
            {
                "plot_name": "Plot 3",
                "plot_inclusion_status": "included",
                "source_label": "EGAP Metaketa I information/accountability pooled PAP row",
                "corpus_what_it_is": "EGAP Metaketa I coordinated information-and-accountability field experiments with a harmonized meta-pre-analysis plan.",
                "what_it_is_why_possible_candidate": "Metaketa I was promoted because the local GitHub archive contains the preregistered pooled binary outcomes, observations, control means, and SEs in the CUP/Science Advances meta-analysis table. Under the one-dot-per-project rule, the plotted value is the median of the two overall pooled binary endpoints after a documented Chinn conversion.",
                "confirmed_fields": "Verified locally in `tab_11.1_main_effects.tex`: overall vote-choice ATE=0.003, control mean=0.369, N=25,820; overall turnout ATE=0.017, control mean=0.837, N=27,737. Confirmed: meta-PAP/preregistered coordinated source: yes; pooled focal outcomes: yes; D conversion: yes, from binary ATE plus control probability via log-OR/Chinn; paper/project median: yes.",
                "backing_file": "data/raw/replication_projects/lead_harvest/metaketa_i_2019/github_metaketa_i/metaketa-i-main.zip; CUP_Book/ch11_meta-analysis/tables/tab_11.1_main_effects.tex",
                "rows_considered": 1,
                "rows_preregistered_equivalent": 1,
                "rows_with_public_local_backing": 1,
                "rows_with_extractable_DN": 1,
                "rows_with_non_retracted_source": 1,
                "rows_contributed": metaketa_i_contributed,
                "rows_left_out_within_source": 1 - metaketa_i_contributed,
                "why": "included as a pooled PAP-locked field-experiment project median with auditable binary-outcome conversion",
                "why_in_out": "Included: one Metaketa I pooled paper/project dot enters. Component-country rows stay staged so the pooled round and its components are not mixed as independent dots in the same strict layer.",
            },
            {
                "plot_name": "Plot 3",
                "plot_inclusion_status": "included",
                "source_label": "EGAP Metaketa III natural-resource monitoring pooled PAP row",
                "corpus_what_it_is": "EGAP Metaketa III coordinated natural-resource-monitoring field experiments with public OSF replication materials.",
                "what_it_is_why_possible_candidate": "Metaketa III was promoted because the local OSF replication archive contains site-level preregistered ITT estimates for standardized resource, satisfaction, knowledge, and stewardship indices plus respondent counts. Under the one-dot-per-project rule, the plotted row is the median of locally pooled standardized-index estimates.",
                "confirmed_fields": "Verified locally in `site_estimates.Rdata` and `respondent_vars.Rdata`: Cov ITT site estimates exist for resource, satisfaction, knowledge, and stewardship indices across six countries; respondent N sums to 16,177. Confirmed: meta-PAP/preregistered coordinated source: yes; standardized index effects: yes; N: yes; paper/project median: yes.",
                "backing_file": "data/raw/replication_projects/lead_harvest/metaketa_iii_2021/osf_259yz/Replication.zip; Replication/Combined/site_estimates.Rdata; Replication/Combined/respondent_vars.Rdata",
                "rows_considered": 1,
                "rows_preregistered_equivalent": 1,
                "rows_with_public_local_backing": 1,
                "rows_with_extractable_DN": 1,
                "rows_with_non_retracted_source": 1,
                "rows_contributed": metaketa_iii_contributed,
                "rows_left_out_within_source": 1 - metaketa_iii_contributed,
                "why": "included as a pooled PAP-locked field-experiment project median with standardized index effects",
                "why_in_out": "Included: one Metaketa III pooled paper/project dot enters. Native component outcomes such as forest cover, pollution concentration, and site-specific ATEs remain staged rather than force-converted.",
            },
            {
                "plot_name": "Plot 3",
                "plot_inclusion_status": "included",
                "source_label": "EGAP Metaketa IV community-policing pooled PAP row",
                "corpus_what_it_is": "EGAP Metaketa IV community-policing field experiments with integrated public OSF result outputs.",
                "what_it_is_why_possible_candidate": "Metaketa IV was promoted because the local integrated OSF RDS output has the preregistered pooled meta-analysis estimates for the eight primary standardized indices. Under the one-dot-per-project rule, the plotted row is the median of those eight primary pooled standardized effects.",
                "confirmed_fields": "Verified locally in `meta-estimates-main-hypotheses.RDS`: 16 meta-analysis rows, of which the first 8 are primary standardized-index outcomes; median absolute primary estimate is 0.0176. Confirmed: EGAP registration/meta-PAP source: yes; pooled standardized effects: yes; N: 18,382 citizens from article/source; paper/project median: yes.",
                "backing_file": "data/raw/replication_projects/lead_harvest/metaketa_iv_2021/osf_xqd3v_outputs/patrick_roach/data-examples-new/integrated RDS outputs/meta-estimates-main-hypotheses.RDS",
                "rows_considered": 1,
                "rows_preregistered_equivalent": 1,
                "rows_with_public_local_backing": 1,
                "rows_with_extractable_DN": 1,
                "rows_with_non_retracted_source": 1,
                "rows_contributed": metaketa_iv_contributed,
                "rows_left_out_within_source": 1 - metaketa_iv_contributed,
                "why": "included as a pooled PAP-locked field-experiment project median with source-standardized index effects",
                "why_in_out": "Included: one Metaketa IV pooled paper/project dot enters. Country/site rows and police/cluster-specific native rows stay staged to avoid nested non-independent Plot 3 dots.",
            },
            {
                "plot_name": "Plot 3",
                "plot_inclusion_status": "included",
                "source_label": "SCORE/COS preregistration-indicated original papers",
                "corpus_what_it_is": "SCORE/COS sampled social-behavioral papers whose original paper IDs are flagged as preregistration-indicated.",
                "what_it_is_why_possible_candidate": "The SCORE/COS claim corpus was rechecked because its public OSF files expose separate original-study effect sizes, effective-N fields, and `orig_prereg-indicated.csv`; the later SCORE replicability package at OSF g5sny also exposes an `analyst data.RData` object with original and replication outcome tables. The local SCORE D/N parser already reconstructs paper-level D/N for a subset of preregistration-indicated papers.",
                "confirmed_fields": f"Known: {fmt_int(score_prereg_count)} unique SCORE paper IDs marked `prereg=True`, {fmt_int(len(score_prereg))} deduplicated paper-level D/N rows from the paper-level candidate join plus {fmt_int(score_text_ready_rows)} text-claim rescue rows. Confirmed: paper-level preregistration indication: yes ({fmt_int(score_prereg_count)}); public flat payloads: `orig_outcomes.csv`, `orig_prereg-indicated.csv`, and `extracted_claims.csv`; text-claim rescue queue: {fmt_int(score_text_candidate_rows)} parsed D/N candidates; D/N entering strict layer: yes ({fmt_int(score_total_contributed)}); claim-specific preregistration mapping: no; support status: not coded.",
                "backing_file": f"{PUBLISHED_PAPERS.relative_to(ROOT)}; {SCORE_ORIG_PREREG.relative_to(ROOT)}; {SCORE_TEXT_CLAIM_CANDIDATES.relative_to(ROOT)}",
                "rows_considered": score_prereg_count,
                "rows_preregistered_equivalent": score_prereg_count,
                "rows_with_public_local_backing": score_prereg_count,
                "rows_with_extractable_DN": score_total_contributed,
                "rows_with_non_retracted_source": score_prereg_count,
                "rows_contributed": score_total_contributed,
                "rows_left_out_within_source": score_left_out,
                "why": "included as a paper-level preregistration-indicated SCORE subset; journal TOP-factor preregistration-policy scores are deliberately ignored",
                "why_in_out": f"Included: {fmt_int(score_total_contributed)} paper-level rows enter ({fmt_int(len(score_prereg))} from the existing paper-level join and {fmt_int(score_text_ready_rows)} from parsed extracted-claim text). The remaining {fmt_int(score_left_out)} preregistration-indicated SCORE paper IDs do not currently have a deduplicated positive D/N row that passes the local parser. Caveat: the public files are split across claim-level effect sizes, claim-level effective-N rows, and paper-level preregistration flags, so the table does not assert that every extracted claim was the exact preregistered primary hypothesis.",
            },
            {
                "plot_name": "Plot 3",
                "plot_inclusion_status": "included",
                "source_label": "Mousa 2020 Iraq soccer social-cohesion preregistered field experiment",
                "corpus_what_it_is": "AEA-registered Iraq field experiment testing whether mixed Christian-Muslim soccer teams changed social-cohesion behaviors and attitudes.",
                "what_it_is_why_possible_candidate": "The Zenodo replication files are public and contain the main analysis script plus outcome-level CSVs. The row uses the one-paper median of nine main outcomes: six binary behavioral outcomes converted from arm event counts with the Chinn log-OR-to-d rule and three attitudinal indices converted as treated-control mean difference over the control SD.",
                "confirmed_fields": "Verified locally: AEA trial AEARCTR-0003540 exists in the registry snapshot with an analysis-plan date; Zenodo record 10.5281/zenodo.3942437 downloaded; main-analyses.R names the focal outcome set; raw CSV files contain treated/control assignments and outcome values; median absolute D=0.235 and median outcome N=232. Caveat: this is a raw-data reconstruction rather than the covariate-adjusted clustered model table.",
                "backing_file": "data/raw/corpus_candidates/political_science_unlock/zenodo/3942437",
                "rows_considered": 1,
                "rows_preregistered_equivalent": 1,
                "rows_with_public_local_backing": 1,
                "rows_with_extractable_DN": 1,
                "rows_with_non_retracted_source": 1,
                "rows_contributed": mousa_contributed,
                "rows_left_out_within_source": 1 - mousa_contributed,
                "why": "included as a preregistered field-experiment paper median with raw-data D/N reconstruction",
                "why_in_out": "Included: one paper-level dot enters. Outcome-level rows remain child calculations; a future Stata/R-compatible extractor could replace the raw arm-count reconstruction with the exact covariate-adjusted published estimates.",
            },
            {
                "plot_name": "Plot 3",
                "plot_inclusion_status": "not_included",
                "source_label": "Schäfer/Schwarz 2019 non-preregistered psychology articles",
                "corpus_what_it_is": "Matched non-preregistered psychology-article sample from the same Schäfer/Schwarz corpus.",
                "what_it_is_why_possible_candidate": "The non-preregistered arm of Schäfer/Schwarz is useful as a within-source comparator because it has the same coded key-question-effect structure as the preregistered sample.",
                "confirmed_fields": f"Known: {fmt_int(schaefer_no_prereg_considered)} coded non-preregistered rows, {fmt_int(len(schaefer_no_prereg))} D/N-ready rows. Confirmed: analytic preregistration: no; paper grouping: yes ({fmt_int(schaefer_no_prereg_considered)}); paper D/N: yes ({fmt_int(len(schaefer_no_prereg))}); support status: not coded.",
                "backing_file": str(PUBLISHED_PAPERS.relative_to(ROOT)),
                "rows_considered": schaefer_no_prereg_considered,
                "rows_preregistered_equivalent": 0,
                "rows_with_public_local_backing": schaefer_no_prereg_considered,
                "rows_with_extractable_DN": len(schaefer_no_prereg),
                "rows_with_non_retracted_source": schaefer_no_prereg_considered,
                "rows_contributed": 0,
                "rows_left_out_within_source": schaefer_no_prereg_considered,
                "why": "not included because these rows are explicitly non-preregistered; they remain a Plot 2 comparator source",
                "why_in_out": f"Not included: {fmt_int(len(schaefer_no_prereg))} D/N-ready rows exist and are already eligible for the published-paper endpoint surface, but the rows fail the analytic-preregistration gate for Plot 3.",
            },
            {
                "plot_name": "Plot 3",
                "plot_inclusion_status": "not_included",
                "source_label": "Allen and Mehler 2019 Registered Reports support-rate review",
                "corpus_what_it_is": "Registered Reports support-rate review used to estimate how often published RR hypotheses are unsupported.",
                "what_it_is_why_possible_candidate": "Allen and Mehler looked like a Plot 3 rescue source because the article surveyed published biomedical and psychological Registered Reports and counted clearly stated a priori hypotheses.",
                "confirmed_fields": "Known from the article: 127 published RRs were surveyed, 113 were included, and the authors extracted 296 a priori hypotheses (153 replication-attempt hypotheses and 143 original-research hypotheses). Confirmed: Registered Report provenance: yes; support/null status: yes; exact D/N result statistics: no.",
                "backing_file": "Allen and Mehler 2019 article and S1 Data; DOI 10.1371/journal.pbio.3000246",
                "rows_considered": 113,
                "rows_preregistered_equivalent": 113,
                "rows_with_public_local_backing": 113,
                "rows_with_extractable_DN": 0,
                "rows_with_non_retracted_source": 113,
                "rows_contributed": 0,
                "rows_left_out_within_source": 113,
                "why": "not included because it is a support-rate/count dataset, not a row-level effect-size and N table",
                "why_in_out": "Not included: this is useful RR-universe evidence and overlaps conceptually with Scheel, but the public article/supporting data count supported versus unsupported hypotheses rather than exposing the exact statistic, effect size, and analytic N for each hypothesis.",
            },
            {
                "plot_name": "Plot 3",
                "plot_inclusion_status": "not_included",
                "source_label": "Many Labs 1-5 project-level replication rows",
                "corpus_what_it_is": "Coordinated Many Labs project-level original-vs-replication rows already represented in Plot 1.",
                "what_it_is_why_possible_candidate": "Many Labs 1-5 looked like Plot 3 candidates because the projects are coordinated large-sample replication efforts with preregistered or protocol-locked analyses and local D/N rows.",
                "confirmed_fields": f"Known locally: {fmt_int(many_labs_pair_rows)} project-level D/N pair rows across Many Labs 1-5 in the replication-pair file. Confirmed: replication protocol status: yes; original and replication D/N: yes; independent single-result Plot 3 table: no.",
                "backing_file": str(REPLICATION_ALL.relative_to(ROOT)),
                "rows_considered": many_labs_pair_rows,
                "rows_preregistered_equivalent": many_labs_pair_rows,
                "rows_with_public_local_backing": many_labs_pair_rows,
                "rows_with_extractable_DN": many_labs_pair_rows,
                "rows_with_non_retracted_source": many_labs_pair_rows,
                "rows_contributed": 0,
                "rows_left_out_within_source": many_labs_pair_rows,
                "why": "not included because these are already Plot 1 original-vs-replication arrows, not independent preregistered confirmatory-result rows",
                "why_in_out": "Not included: local D/N rows exist, but they are already consumed by the replication-pair plot. Adding them here would double-count replication-side evidence unless Plot 3 gets a separate multi-lab-replication lane.",
            },
            {
                "plot_name": "Plot 3",
                "plot_inclusion_status": "not_included",
                "source_label": "Registered Replication Reports Plot 1 pair rows",
                "corpus_what_it_is": "Registered Replication Report rows already normalized as original-vs-replication evidence.",
                "what_it_is_why_possible_candidate": "The live RRR rows looked like Plot 3 candidates because they come from preregistered replication reports and have local D/N encodings.",
                "confirmed_fields": f"Known locally: {fmt_int(rrr_pair_rows)} RRR/FReD-RRR D/N pair rows in the replication-pair file. Confirmed: preregistered replication status: yes; original and replication D/N: yes; independence from Plot 1: no.",
                "backing_file": str(REPLICATION_ALL.relative_to(ROOT)),
                "rows_considered": rrr_pair_rows,
                "rows_preregistered_equivalent": rrr_pair_rows,
                "rows_with_public_local_backing": rrr_pair_rows,
                "rows_with_extractable_DN": rrr_pair_rows,
                "rows_with_non_retracted_source": rrr_pair_rows,
                "rows_contributed": 0,
                "rows_left_out_within_source": rrr_pair_rows,
                "why": "not included because these rows are direct-replication pair evidence already plotted in Plot 1",
                "why_in_out": "Not included: the rows are real preregistered replication evidence with D/N, but their current role is original-vs-replication comparison. Plot 3 is reserved for standalone preregistered confirmatory result rows.",
            },
            {
                "plot_name": "Plot 3",
                "plot_inclusion_status": "not_included",
                "source_label": "Psychological Science Accelerator replication-pair rows",
                "corpus_what_it_is": "PSA multi-site replication/generality rows already promoted to Plot 1 where pairable.",
                "what_it_is_why_possible_candidate": "PSA projects looked eligible because they are preregistered, multi-site confirmatory projects. The local repo has PSA-002, PSA-004, and PSA-006 D/N pair rows.",
                "confirmed_fields": f"Known locally: {fmt_int(psa_pair_rows)} PSA D/N pair rows (PSA-002 object orientation, PSA-004 Turri, PSA-006 trolley) in the replication-pair file. Confirmed: preregistered/multi-site status: yes; original and replication D/N: yes; standalone non-pair Plot 3 table: no.",
                "backing_file": str(REPLICATION_ALL.relative_to(ROOT)),
                "rows_considered": psa_pair_rows,
                "rows_preregistered_equivalent": psa_pair_rows,
                "rows_with_public_local_backing": psa_pair_rows,
                "rows_with_extractable_DN": psa_pair_rows,
                "rows_with_non_retracted_source": psa_pair_rows,
                "rows_contributed": 0,
                "rows_left_out_within_source": psa_pair_rows,
                "why": "not included because these rows are original-vs-replication or country-level pair rows already represented in Plot 1",
                "why_in_out": "Not included: the PSA pair rows are already part of the replication-pair evidence. PSA-CR001 is the exception because it contributes four pooled preregistered confirmatory outcomes without an original-vs-replication arrow.",
            },
            {
                "plot_name": "Plot 3",
                "plot_inclusion_status": "not_included",
                "source_label": "Transparent Psi Project / Bem preregistered replication",
                "corpus_what_it_is": "Preregistered large-sample Bem/psi replication with a local D/N pair row.",
                "what_it_is_why_possible_candidate": "The Transparent Psi Project looked eligible because it is explicitly preregistered and the local combined raw data promoted one first-stopping-point D/N row.",
                "confirmed_fields": f"Known locally: {fmt_int(tpp_pair_rows)} promoted D/N pair row. Confirmed: preregistered replication: yes; original and replication D/N: yes; standalone confirmatory-result source independent of Plot 1: no.",
                "backing_file": str((HARVEST_PROMOTED_DIR / "tpp_bem__promoted_pairs.csv").relative_to(ROOT)),
                "rows_considered": tpp_pair_rows,
                "rows_preregistered_equivalent": tpp_pair_rows,
                "rows_with_public_local_backing": tpp_pair_rows,
                "rows_with_extractable_DN": tpp_pair_rows,
                "rows_with_non_retracted_source": tpp_pair_rows,
                "rows_contributed": 0,
                "rows_left_out_within_source": tpp_pair_rows,
                "why": "not included because it is already a Plot 1 direct-replication row",
                "why_in_out": "Not included: this is a clean preregistered replication row, but its current analytic role is a shrinkage arrow against Bem's original result, not a standalone preregistered-result observation.",
            },
            {
                "plot_name": "Plot 3",
                "plot_inclusion_status": "included",
                "source_label": "RPCB eLife Registered Report replication effects",
                "corpus_what_it_is": "Reproducibility Project: Cancer Biology effect-level replication dataset from eLife Registered Reports and replication studies.",
                "what_it_is_why_possible_candidate": "RPCB was rechecked because its replication protocols were submitted as Registered Reports before experimental work and the public OSF effect-level table contains replication sample sizes and SMD-like effect-size columns.",
                "confirmed_fields": f"Known locally: 188 effect-level rows in the RPCB final effect table and {fmt_int(rpcb_pair_rows)} RPCB rows already in the replication-pair file. Confirmed from local table: replication sample size is present for 188 effects; replication SMD effect size is present for 159 effects; original sample size is numeric for 140 effects; original SMD effect size is numeric for 135 effects. The relaxed median-per-paper rule yields {fmt_int(rpcb_preclinical_contributed_rows)} preclinical paper medians from {fmt_int(rpcb_preclinical_registered_result_rows)} registered effect rows. Confirmed: Registered Report replication protocol status: yes; domain caveat: preclinical biology.",
                "backing_file": f"data/raw/corpus_candidates/rpcb/RP_CB Final Analysis - Effect level data.csv; {RPCB_PRECLINICAL_CANDIDATES.relative_to(ROOT)}; https://osf.io/e5nvr/",
                "rows_considered": 188,
                "rows_preregistered_equivalent": 188,
                "rows_with_public_local_backing": 188,
                "rows_with_extractable_DN": 159,
                "rows_with_non_retracted_source": 188,
                "rows_contributed": rpcb_preclinical_contributed_rows,
                "rows_left_out_within_source": max(188 - rpcb_preclinical_registered_result_rows, 0),
                "why": "included as preclinical Registered Report replication evidence under the relaxed median-per-paper policy",
                "why_in_out": f"Included: {fmt_int(rpcb_preclinical_contributed_rows)} paper medians enter as a separate preclinical-biology field. The source has {fmt_int(rpcb_preclinical_registered_result_rows)} numeric registered effect rows, but the plot uses one median row per replicated paper to avoid within-paper effect inflation. These rows are cross-plot related to RPCB replication-pair evidence, so the preclinical field label is retained.",
            },
            {
                "plot_name": "Plot 3",
                "plot_inclusion_status": "not_included",
                "source_label": "ManyBabies 2 knowledge/ignorance registered-report materials",
                "corpus_what_it_is": "ManyBabies 2 multi-lab registered-report analysis of anticipatory-looking sensitivity to knowledge versus ignorance.",
                "what_it_is_why_possible_candidate": "ManyBabies 2 was rechecked because it is a many-lab registered-report-style project with a public analysis repository and a paper-source first-test-trial confirmatory analysis for toddlers and adults.",
                "confirmed_fields": "Verified from the public analysis repository and paper source: included N is 521 toddlers and 703 adults; the preregistered first-test-trial models report four primary condition coefficients: first-look logit coefficients for toddlers and adults plus proportional-looking coefficients for toddlers and adults. The repository gitignores raw/processed data and model-output directories, and the paper does not report a source-standardized D or residual SD needed for a lossless D conversion.",
                "backing_file": "https://github.com/manybabies/mb2-analysis; local audit of paper/mb2-paper.tex and 007a-aoi-analysis.R",
                "rows_considered": 4,
                "rows_preregistered_equivalent": 4,
                "rows_with_public_local_backing": 4,
                "rows_with_extractable_DN": 0,
                "rows_with_non_retracted_source": 4,
                "rows_contributed": 0,
                "rows_left_out_within_source": 4,
                "why": "not included because the checked public payload reports native Bayesian/logit/proportion model coefficients rather than D/N-ready standardized result rows",
                "why_in_out": "Not included: the lead is real and preregistered, but the strict Plot 3 D axis should not be populated by an ad hoc conversion from model coefficients without the processed analysis data, model residual scale, or a source-reported standardized effect. Keep as native/staged unless the processed result objects or a paper supplement exposes a defensible D conversion.",
            },
            {
                "plot_name": "Plot 3",
                "plot_inclusion_status": "not_included",
                "source_label": "ManyBabies 3 rule-learning registered-report materials",
                "corpus_what_it_is": "ManyBabies 3 registered-report materials and public code/materials archive.",
                "what_it_is_why_possible_candidate": "ManyBabies 3 looked eligible because it is a preregistered infant rule-learning multi-lab project. The repo has the OSF registered-report PDFs and public GitHub materials cached.",
                "confirmed_fields": "Known: target project expected roughly 15 lab/result rows in the harvest worklist. Confirmed: preregistered project materials: yes; final machine-readable site-level D/N result payload: no; promoted rows: 0.",
                "backing_file": str((HARVEST_STAGED_DIR / "manybabies_3__stage.csv").relative_to(ROOT)),
                "rows_considered": 15,
                "rows_preregistered_equivalent": 15,
                "rows_with_public_local_backing": 0,
                "rows_with_extractable_DN": 0,
                "rows_with_non_retracted_source": 15,
                "rows_contributed": 0,
                "rows_left_out_within_source": 15,
                "why": "not included because the public materials are document/code/stimulus artifacts without final site-level result rows",
                "why_in_out": "Not included: preregistered materials are local, but the checked OSF archive and public GitHub repository did not expose final machine-readable infant result rows.",
            },
            {
                "plot_name": "Plot 3",
                "plot_inclusion_status": "not_included",
                "source_label": "ManyBabies 4 helpers/hinderers registered-report materials",
                "corpus_what_it_is": "ManyBabies 4 Stage 1/Stage 2 Registered Report materials and public analysis repository for infant helpers/hinderers preferences.",
                "what_it_is_why_possible_candidate": "ManyBabies 4 looked eligible because it is a Stage 1 and Stage 2 Registered Report, reports N tested and N included, and exposes public analysis/data files. It is a plausible one-row pooled primary-result rescue.",
                "confirmed_fields": "Known from the research pass: N tested = 1,018, N included = 567, public analysis repo names clean_data.csv and analysis qmd files. Confirmed: Registered Report status: yes; final machine-readable data likely public; exact Stage 1 focal contrast and exact denominators: not yet locally verified.",
                "backing_file": "https://manybabies.org/MB4/; https://github.com/manybabies/mb4-analysis",
                "rows_considered": 1,
                "rows_preregistered_equivalent": 1,
                "rows_with_public_local_backing": 1,
                "rows_with_extractable_DN": 0,
                "rows_with_non_retracted_source": 1,
                "rows_contributed": 0,
                "rows_left_out_within_source": 1,
                "why": "not included yet because the exact primary contrast and denominators still need file-level verification",
                "why_in_out": "Not included yet: this is a strong near-row, but the current repo has not verified the Stage 1 focal contrast or exact counts from clean_data.csv. Rounded abstract percentages are not enough for strict Plot 3.",
            },
            {
                "plot_name": "Plot 3",
                "plot_inclusion_status": "included",
                "source_label": "van den Akker matched preregistered-result paper medians",
                "corpus_what_it_is": "Preregistration-in-practice / selective-hypothesis-reporting workbook collapsed to paper medians of publication results explicitly coded as matching preregistered hypotheses.",
                "what_it_is_why_possible_candidate": "This corpus became admissible under the updated row rule because `Data_SHR.xlsx` marks publication result texts that match preregistered hypotheses, and `PvNP_Data.xlsx` supplies publication-level N for the 193-study preregistered-vs-non-preregistered sample. The strict plotted unit is now one paper median, not one arbitrary extracted statistic.",
                "confirmed_fields": f"Verified from local OSF downloads: `PvNP Data.xlsx` has 193 publication rows with N; `Data SHR.xlsx` exposes hypothesis/reporting match fields; the matched-result parser finds {fmt_int(vandenakker_median_candidate_rows)} paper-level median D/N candidates, of which {fmt_int(vandenakker_median_contributed_rows)} enter strict Plot 3 after {fmt_int(vandenakker_median_score_duplicates)} DOI duplicate(s) already covered by SCORE are withheld. {fmt_int(vandenakker_median_multi_paper_rows)} included papers have more than one matched preregistered result and are collapsed by median D. The older broad `Original Stats.xlsx` parser still yields {fmt_int(vandenakker_rescue_candidate_rows)} first-convertible-stat candidates but remains staged because it is not match-filtered.",
                "backing_file": f"{VANDENAKKER_MEDIAN_CANDIDATES.relative_to(ROOT)}; data/raw/corpus_candidates/vandenakker_pqnvr/Data_SHR.xlsx; data/raw/corpus_candidates/vandenakker_pqnvr/PvNP_Data.xlsx",
                "rows_considered": 193,
                "rows_preregistered_equivalent": 193,
                "rows_with_public_local_backing": 193,
                "rows_with_extractable_DN": vandenakker_median_ready_rows,
                "rows_with_non_retracted_source": 193,
                "rows_contributed": vandenakker_median_contributed_rows,
                "rows_left_out_within_source": 193 - vandenakker_median_contributed_rows,
                "why": "included under the paper-median policy because each contributing statistic is source-coded as a matched preregistered result and the plotted unit is one median row per paper",
                "why_in_out": f"Included: {fmt_int(vandenakker_median_contributed_rows)} paper medians enter. The median collapse allows multiple preregistered hypothesis results within a paper while preventing within-paper row inflation. The remaining {fmt_int(193 - vandenakker_median_contributed_rows)} PvNP papers are either not parseable by the matched-result D/N parser or already covered by another strict source.",
            },
            {
                "plot_name": "Plot 3",
                "plot_inclusion_status": "not_included",
                "source_label": "van den Akker selective-hypothesis-reporting psychology corpus",
                "corpus_what_it_is": "Large psychology preregistration-to-publication hypothesis-matching corpus from Selective Hypothesis Reporting in Psychology.",
                "what_it_is_why_possible_candidate": "The selective-hypothesis-reporting corpus was separated from the 193-study preregistration-in-practice sample because the paper and local workbook expose a much larger study/hypothesis matching surface that can drive a later strict row-rescue pass.",
                "confirmed_fields": "Known from the article: 459 preregistered studies and 2,119 identified hypotheses. Verified locally in `Data SHR.xlsx`: 484 PSP IDs total, 446 PSP IDs marked `Inclusion=Yes`, 5,723 filled preregistered-hypothesis cells among included PSP IDs, and 3,342 publication-match cells beginning with `Yes`. Confirmed: preregistration/publication hypothesis matching: yes; support/match status: yes; source-provided D/N: no.",
                "backing_file": "data/raw/corpus_candidates/vandenakker_pqnvr/Data_SHR.xlsx (downloaded audit copy); https://doi.org/10.1177/25152459231187988",
                "rows_considered": 459,
                "rows_preregistered_equivalent": 459,
                "rows_with_public_local_backing": 446,
                "rows_with_extractable_DN": 0,
                "rows_with_non_retracted_source": 459,
                "rows_contributed": 0,
                "rows_left_out_within_source": 459,
                "why": "not included yet because it is a hypothesis/reporting-match corpus, not a ready effect-size and analytic-N table",
                "why_in_out": "Not included yet: this is the strongest large-volume psychology rescue surface from the crash notes, but the workbook identifies and matches hypotheses rather than providing one strict focal D/N row per study. Promotion requires selecting a preregistered focal hypothesis, linking it to an exact result statistic, converting the statistic to D, recovering analytic N, and deduplicating against existing Plot 3 psychology corpora.",
            },
            {
                "plot_name": "Plot 3",
                "plot_inclusion_status": "not_included",
                "source_label": "ERN/Pe RRR OpenNeuro and OSF analysis hubs",
                "corpus_what_it_is": "OpenNeuro/OSF materials for an EEG Registered Replication Report.",
                "what_it_is_why_possible_candidate": "ERN/Pe looked eligible because it is a Registered Replication Report with public OpenNeuro raw EEG and OSF analysis artifacts.",
                "confirmed_fields": "Known: OpenNeuro raw EEG plus OSF summary/analysis artifacts are local. Confirmed: preregistered replication status: yes; replication-side native metrics: yes; compact original-vs-replication D/N row table: no.",
                "backing_file": str((HARVEST_STAGED_DIR / "ern_pe_rrr_openneuro__stage.csv").relative_to(ROOT)),
                "rows_considered": 1,
                "rows_preregistered_equivalent": 1,
                "rows_with_public_local_backing": 0,
                "rows_with_extractable_DN": 0,
                "rows_with_non_retracted_source": 1,
                "rows_contributed": 0,
                "rows_left_out_within_source": 1,
                "why": "not included because it is currently a native EEG/replication-side source rather than a compact D/N result corpus",
                "why_in_out": "Not included: source is real and local, but it lacks a compact D/N table and the original-side result is missing from the local artifact set.",
            },
            {
                "plot_name": "Plot 3",
                "plot_inclusion_status": "not_included",
                "source_label": "Self-control fMRI preregistered replication materials",
                "corpus_what_it_is": "Preregistration, scripts, paper mirror, and OpenNeuro-backed fMRI replication materials.",
                "what_it_is_why_possible_candidate": "The self-control fMRI replication looked eligible because the OSF node contains preregistration/scripts and the paper/OpenNeuro materials are local.",
                "confirmed_fields": "Known: four expected candidate rows in the harvest worklist. Confirmed: preregistration materials: yes; raw fMRI/paper mirror: yes; machine-readable D/N result table: no; native neuroimaging metrics: unresolved.",
                "backing_file": str((HARVEST_STAGED_DIR / "self_control_fmri_2022__stage.csv").relative_to(ROOT)),
                "rows_considered": 4,
                "rows_preregistered_equivalent": 4,
                "rows_with_public_local_backing": 0,
                "rows_with_extractable_DN": 0,
                "rows_with_non_retracted_source": 4,
                "rows_contributed": 0,
                "rows_left_out_within_source": 4,
                "why": "not included because the local files are preregistration/raw-neuroimaging materials without a D/N-ready confirmatory table",
                "why_in_out": "Not included: the source is documented and useful, but the current local payload does not provide Plot 3-ready confirmatory D/N rows.",
            },
            {
                "plot_name": "Plot 3",
                "plot_inclusion_status": "not_included",
                "source_label": "Twomey et al. 2021 kinesiology article audit",
                "corpus_what_it_is": "Kinesiology article audit with preregistration, RCT, sample-size, and support flags.",
                "what_it_is_why_possible_candidate": "Twomey looked eligible because its public article-level table includes a preregistration flag and sample size for 300 recent kinesiology articles.",
                "confirmed_fields": f"Known: {fmt_int(twomey_considered)} article rows, {fmt_int(twomey_prereg)} marked preregistered, {fmt_int(twomey_n_rows)} with sample size. Confirmed: article grouping: yes; preregistration flag: yes; exact effect/test statistic for D conversion: no.",
                "backing_file": str(twomey_path.relative_to(ROOT)) if twomey_path.exists() else "data/raw/corpus_candidates/twomey_2021/df_all.csv",
                "rows_considered": twomey_considered,
                "rows_preregistered_equivalent": twomey_prereg,
                "rows_with_public_local_backing": twomey_considered,
                "rows_with_extractable_DN": 0,
                "rows_with_non_retracted_source": twomey_considered,
                "rows_contributed": 0,
                "rows_left_out_within_source": twomey_considered,
                "why": "not included because preregistration and N exist but exact effect/test-statistic fields do not",
                "why_in_out": "Not included: this is a real public preregistration-aware article audit, but the released p-value fields are reporting-format/threshold metadata rather than exact numeric statistics for D/N reconstruction.",
            },
            {
                "plot_name": "Plot 3",
                "plot_inclusion_status": "not_included",
                "source_label": "Linden et al. 2024 focal/random psychology sample",
                "corpus_what_it_is": "Psychology focal/random effect sample with local D/N rows and a preregistered meta-research study artifact.",
                "what_it_is_why_possible_candidate": "Linden was rechecked because the raw OSF materials include a preregistration artifact and the parsed focal/random effect rows are D/N-ready.",
                "confirmed_fields": f"Known locally: {fmt_int(len(linden_focal))} focal D/N rows and {fmt_int(len(linden_random))} random-effect D/N rows. Confirmed: D/N: yes ({fmt_int(linden_dn_rows)}); preregistration applies to the meta-research coding study, not to the sampled article findings.",
                "backing_file": str(PUBLISHED_PAPERS.relative_to(ROOT)),
                "rows_considered": linden_dn_rows,
                "rows_preregistered_equivalent": 0,
                "rows_with_public_local_backing": linden_dn_rows,
                "rows_with_extractable_DN": linden_dn_rows,
                "rows_with_non_retracted_source": linden_dn_rows,
                "rows_contributed": 0,
                "rows_left_out_within_source": linden_dn_rows,
                "why": "not included because the preregistration is for the meta-research sampling/extraction study, not for each underlying published article result",
                "why_in_out": "Not included: the focal rows remain in the published-result layer and the random rows remain a comparator. The OSF preregistration does not make the sampled source articles analytically preregistered confirmatory results.",
            },
            {
                "plot_name": "Plot 3",
                "plot_inclusion_status": "not_included",
                "source_label": "Protzko et al. 2024 High-Replicability Research project",
                "corpus_what_it_is": "Preregistered high-replicability project considered as a counter-pattern source.",
                "what_it_is_why_possible_candidate": "High-Replicability Research was considered because it was designed as a preregistered counter-pattern source with many planned high-replicability findings.",
                "confirmed_fields": f"Known: 48 project findings claimed in the audit trail; {fmt_int(protzko_local_dn)} local D/N pair rows recovered in the replication-harvest sidecar. Confirmed: analytic preregistration: yes; D/N: partial ({fmt_int(protzko_local_dn)}); non-retracted status: no.",
                "backing_file": "documented in moved appendix material",
                "rows_considered": 48,
                "rows_preregistered_equivalent": 48,
                "rows_with_public_local_backing": protzko_local_dn,
                "rows_with_extractable_DN": protzko_local_dn,
                "rows_with_non_retracted_source": 0,
                "rows_contributed": 0,
                "rows_left_out_within_source": 48,
                "why": "considered as a preregistered counter-pattern dataset but excluded because the Nature Human Behaviour paper was retracted",
                "why_in_out": "Not included: the source fails the non-retraction gate, so even locally recovered rows stay out of Plot 3.",
            },
            {
                "plot_name": "Plot 3",
                "plot_inclusion_status": "not_included",
                "source_label": "AACT x PubMed registered primary outcomes",
                "corpus_what_it_is": "Registered biomedical primary-outcome publication linkage, not analytic preregistration.",
                "what_it_is_why_possible_candidate": "ClinicalTrials.gov/AACT primary-outcome linkages were considered because trial registration can identify focal biomedical outcomes at scale.",
                "confirmed_fields": "Known: 2,720 registered primary-outcome rows in the earlier audit. Confirmed: trial registration: yes; analytic preregistration plan: no/insufficient; local Plot 3 D/N result rows: no.",
                "backing_file": "documented in moved appendix material",
                "rows_considered": 2720,
                "rows_preregistered_equivalent": 0,
                "rows_with_public_local_backing": 0,
                "rows_with_extractable_DN": 0,
                "rows_with_non_retracted_source": 2720,
                "rows_contributed": 0,
                "rows_left_out_within_source": 2720,
                "why": "considered as a biomedical comparator, but registration is not the same as analytic preregistration and the current layer is not yet a clean preregistered-results source family",
                "why_in_out": "Not included: registry metadata can support a comparator layer, but these rows are not yet analytic-preregistration result rows on the shared D/N axis.",
            },
            {
                "plot_name": "Plot 3",
                "plot_inclusion_status": "not_included",
                "source_label": "COMPare prespecified clinical-trial outcome audit",
                "corpus_what_it_is": "Outcome-reporting audit for clinical trials in top medical journals, parsed into prespecified and non-prespecified outcome rows.",
                "what_it_is_why_possible_candidate": "COMPare looked like a missing Plot 3 source because the local parser recovers outcome-level rows and explicitly separates prespecified primary outcomes, prespecified secondary outcomes, and non-prespecified published outcomes.",
                "confirmed_fields": f"Known locally: {fmt_int(compare_trials)} trial reports and {fmt_int(compare_outcome_rows)} outcome rows: {fmt_int(compare_primary)} prespecified primary, {fmt_int(compare_secondary)} prespecified secondary, {fmt_int(compare_nonprespec)} non-prespecified publication outcomes. Confirmed: prespecified-outcome status: yes; trial/publication provenance: yes; effect estimate and N fields: no.",
                "backing_file": str(COMPARE_OUTCOME_ROWS.relative_to(ROOT)) if COMPARE_OUTCOME_ROWS.exists() else "data/derived/corpus_candidates/compare_trials/compare_trials_outcome_rows.csv",
                "rows_considered": compare_outcome_rows,
                "rows_preregistered_equivalent": compare_prespecified,
                "rows_with_public_local_backing": compare_outcome_rows,
                "rows_with_extractable_DN": 0,
                "rows_with_non_retracted_source": compare_outcome_rows,
                "rows_contributed": 0,
                "rows_left_out_within_source": compare_outcome_rows,
                "why": "not included because it audits whether prespecified outcomes were reported, but does not contain effect estimates or analytic sample sizes",
                "why_in_out": "Not included: the prespecified-outcome labels are exactly the kind of audit trail we wanted to check, but the parsed rows stop at outcome text/reporting status. There is no D/N layer to plot.",
            },
            {
                "plot_name": "Plot 3",
                "plot_inclusion_status": "included",
                "source_label": "ClinicalTrials.gov phase-2+ primary randomized registry rows",
                "corpus_what_it_is": "Cleaner ClinicalTrials.gov registered-primary-outcome subset: phase-2+ randomized interventional trials with exactly one locally eligible primary two-group registry result.",
                "what_it_is_why_possible_candidate": "This subset was promoted because it supplies the missing scale source without coefficient-level inflation: each row is one randomized trial, the outcome is registered as primary, the trial is phase 2 or later, and the local record exposes exactly one eligible two-group primary outcome with enrollment and an exact registry p-value.",
                "confirmed_fields": f"Known locally: {fmt_int(ctgov_clean_rows)} phase-2+ randomized one-primary-outcome trial rows. Confirmed: registered primary outcome: yes; randomized interventional design: yes; phase-2+ filter: yes ({fmt_int(ctgov_clean_phase2plus)} rows); D/N: yes via registry p-value and enrollment proxy; published-paper endpoint: no.",
                "backing_file": str(PREREG_CTGOV_PRIMARY_RANDOMIZED_RESULTS.relative_to(ROOT)),
                "rows_considered": ctgov_clean_rows,
                "rows_preregistered_equivalent": ctgov_clean_rows,
                "rows_with_public_local_backing": ctgov_clean_rows,
                "rows_with_extractable_DN": ctgov_clean_rows,
                "rows_with_non_retracted_source": ctgov_clean_rows,
                "rows_contributed": ctgov_clean_rows,
                "rows_left_out_within_source": 0,
                "why": "included as one registered primary randomized trial dot per trial",
                "why_in_out": f"Included: {fmt_int(ctgov_clean_rows)} phase-2+ randomized trials have exactly one locally eligible registered primary two-group result, so they can enter Plot 3 as trial-level registered confirmatory dots. These are registry-result D proxies, not journal-published paper extractions, and are labeled separately as clinical medicine.",
            },
            {
                "plot_name": "Plot 3",
                "plot_inclusion_status": "not_included",
                "source_label": "ClinicalTrials.gov API registered outcome-result universe",
                "corpus_what_it_is": "ClinicalTrials.gov API v2 result records parsed into registered primary, secondary, and other pre-specified two-group outcome-analysis rows with API denominators.",
                "what_it_is_why_possible_candidate": "ClinicalTrials.gov is the scale source. The official API exposes result outcome measures, comparison groups, denominators, measurements, p-values, and ratio estimates in one JSON record. A dedicated local API pull now recovers the real-world registered-results universe rather than only the older p-value-proxy KG sidecar.",
                "confirmed_fields": f"Known locally from the API pull: {fmt_int(ctgov_api_rows)} registered outcome-analysis D/N rows across {fmt_int(ctgov_api_trials)} randomized interventional trials, collapsed to {fmt_int(len(ctgov_api_medians))} one-trial median rows for non-inflated plotting. The row-level file includes {fmt_int(ctgov_api_primary_rows)} primary-outcome rows; {fmt_int(ctgov_api_direct_rows)} rows use direct ratio/event-count conversion and {fmt_int(ctgov_api_p_proxy_rows)} use a p-value-to-D proxy with actual API group denominators. Older local sidecars remain available: {fmt_int(len(ctgov_registry))} KG trial medians and {fmt_int(ctgov_clean_rows)} cleaner phase-2+ primary randomized trial medians.",
                "backing_file": f"{CTGOV_API_REGISTERED_ROWS.relative_to(ROOT)}; {CTGOV_API_REGISTERED_TRIAL_MEDIANS.relative_to(ROOT)}; {PUBLISHED_PAPERS.relative_to(ROOT)}",
                "rows_considered": ctgov_api_rows or len(ctgov_registry),
                "rows_preregistered_equivalent": len(ctgov_api_medians) or ctgov_clean_rows,
                "rows_with_public_local_backing": ctgov_api_rows or len(ctgov_registry),
                "rows_with_extractable_DN": ctgov_api_rows or ctgov_dn_rows,
                "rows_with_non_retracted_source": ctgov_api_rows or len(ctgov_registry),
                "rows_contributed": 0,
                "rows_left_out_within_source": ctgov_api_rows or len(ctgov_registry),
                "why": "not included because this is a registered outcome-result universe, not the current standalone published analytic-preregistration layer",
                "why_in_out": f"Not included in strict Plot 3: the {fmt_int(ctgov_api_rows)} API rows are real registered medical outcome results and solve the scale problem, but they are registry-result rows rather than paper-level analytic preregistration rows. They should be plotted as a clinical registered-results field layer or as one-trial medians, not silently merged with Registered Reports and matched psychology preregistration corpora.",
            },
            {
                "plot_name": "Plot 3",
                "plot_inclusion_status": "not_included",
                "source_label": "CliniFact published trial primary-outcome rows",
                "corpus_what_it_is": "Published clinical-trial reports linked to ClinicalTrials.gov primary outcomes.",
                "what_it_is_why_possible_candidate": "CliniFact was rechecked because these rows are journal-side clinical trial primary-outcome proxies with D/N on disk, so they are closer to published preregistered work than raw registry rows.",
                "confirmed_fields": f"Known locally: {fmt_int(len(clinifact))} published trial primary-outcome rows, {fmt_int(clinifact_dn_rows)} D/N-ready rows. Confirmed: journal provenance: yes; primary-outcome registry linkage: yes; D/N: yes; article-level analytic preregistration/hypothesis text: not confirmed.",
                "backing_file": str(PUBLISHED_PAPERS.relative_to(ROOT)),
                "rows_considered": len(clinifact),
                "rows_preregistered_equivalent": 0,
                "rows_with_public_local_backing": len(clinifact),
                "rows_with_extractable_DN": clinifact_dn_rows,
                "rows_with_non_retracted_source": len(clinifact),
                "rows_contributed": 0,
                "rows_left_out_within_source": len(clinifact),
                "why": "not included under the current narrow Plot 3 rule; retained in Plot 2 as published clinical-trial primary-outcome evidence",
                "why_in_out": f"Not included here: {fmt_int(clinifact_dn_rows)} D/N rows exist and are already represented in the published-paper endpoint surface. The current Plot 3 gate requires explicit analytic preregistered confirmatory rows, not only registry-linked primary outcomes.",
            },
            {
                "plot_name": "Plot 3",
                "plot_inclusion_status": "included",
                "source_label": "Brodeur et al. 2024 preregistered/PAP economics table tests",
                "corpus_what_it_is": "Top-journal economics table-test extraction with row-level preregistration, pre-analysis-plan, and PAP-power flags in the local raw notes.",
                "what_it_is_why_possible_candidate": "The Brodeur economics corpus is the largest local source of preregistration-flagged D/N rows: many extracted table tests are from studies marked as preregistered, having a pre-analysis plan, or reporting PAP power calculations. The plotted layer now applies the same one-dot-per-paper rule used elsewhere by collapsing each flagged paper to the median absolute D and median analytic N across its flagged table-test rows.",
                "confirmed_fields": f"Known locally: {fmt_int(brodeur_rows)} extracted economics test rows, {fmt_int(brodeur_flagged_rows)} D/N-ready rows with preregistration/PAP/PAP-power flags, collapsing to {fmt_int(brodeur_flagged_papers)} paper medians. Confirmed: preregistration flag rows: {fmt_int(brodeur_prereg_rows)}; pre-analysis-plan flag rows: {fmt_int(brodeur_pap_rows)}; PAP-power flag rows: {fmt_int(brodeur_pap_power_rows)}; D/N: yes; exact test-level PAP-to-outcome mapping: no, so source-level notes mark the median selector.",
                "backing_file": str(CANDIDATE_ROWS.relative_to(ROOT)) if CANDIDATE_ROWS.exists() else "data/derived/corpus_candidates/candidate_d_n_rows.csv.gz",
                "rows_considered": brodeur_rows,
                "rows_preregistered_equivalent": brodeur_flagged_rows,
                "rows_with_public_local_backing": brodeur_rows,
                "rows_with_extractable_DN": brodeur_flagged_rows,
                "rows_with_non_retracted_source": brodeur_rows,
                "rows_contributed": brodeur_flagged_papers,
                "rows_left_out_within_source": max(brodeur_flagged_rows - brodeur_flagged_papers, 0),
                "why": "included as one paper-level median per preregistration/PAP-flagged economics paper",
                "why_in_out": f"Included: the preregistration/PAP flags account for {fmt_int(brodeur_flagged_rows)} D/N-ready extracted table-test rows. To avoid coefficient-level inflation, Plot 3 contributes {fmt_int(brodeur_flagged_papers)} paper-level median dots rather than all table tests. These rows remain flagged as median selectors, not exact PAP-outcome matches.",
            },
            {
                "plot_name": "Plot 3",
                "plot_inclusion_status": "not_included",
                "source_label": "Nordic trial registration-publication linkage database",
                "corpus_what_it_is": "Clinical-trial registration/publication linkage audit with trial IDs, publication status, DOI/PMID, and matching criteria.",
                "what_it_is_why_possible_candidate": "The Nordic trial-reporting database looked like the missing large clinical-trial preregistration source because it has thousands of trial-registration to publication links and records whether publications matched the registered design, population, intervention, comparator, and any outcome.",
                "confirmed_fields": f"Known locally: {fmt_int(nordic_rows)} registry-publication search rows, {fmt_int(nordic_journal_publications)} journal-publication rows. Confirmed: trial registration IDs: yes; publication DOI/PMID: yes where found; outcome/effect/N fields for D conversion: no.",
                "backing_file": str(nordic_publications_path.relative_to(ROOT)) if nordic_publications_path.exists() else "data/raw/publication_bias_direct/nordic_trial_reporting/...",
                "rows_considered": nordic_rows,
                "rows_preregistered_equivalent": 0,
                "rows_with_public_local_backing": nordic_rows,
                "rows_with_extractable_DN": 0,
                "rows_with_non_retracted_source": nordic_rows,
                "rows_contributed": 0,
                "rows_left_out_within_source": nordic_rows,
                "why": "not included because it is a publication-linkage/outcome-reporting audit rather than an effect-size table",
                "why_in_out": "Not included: the rows confirm publication linkage and matching metadata, but they do not contain exact result statistics or D/N fields for the preregistered point-estimate plot.",
            },
            {
                "plot_name": "Plot 3",
                "plot_inclusion_status": "not_included",
                "source_label": "FORRT FReD / Replication Database",
                "corpus_what_it_is": "Replication Database/FReD original-replication pairs and original-side published target claims.",
                "what_it_is_why_possible_candidate": "FReD was rechecked because it is a large replication database and the local clean export contributes many D/N rows to the replication and published-result layers.",
                "confirmed_fields": f"Known locally: {fmt_int(fred_pair_rows)} FReD pair rows in the replication-pair file and {fmt_int(fred_published_dn_rows)} original published-target D/N rows in the published corpus. Confirmed: D/N: yes; original-replication pairing: yes; analytic preregistration flag for each source result: no.",
                "backing_file": str(PUBLISHED_PAPERS.relative_to(ROOT)),
                "rows_considered": fred_pair_rows,
                "rows_preregistered_equivalent": 0,
                "rows_with_public_local_backing": fred_pair_rows,
                "rows_with_extractable_DN": fred_pair_rows,
                "rows_with_non_retracted_source": fred_pair_rows,
                "rows_contributed": 0,
                "rows_left_out_within_source": fred_pair_rows,
                "why": "not included because FReD is a replication-pair database rather than a preregistered-results corpus",
                "why_in_out": "Not included: FReD is already represented through Plot 1 pair evidence and Plot 2 original-target published evidence. The clean export does not make those rows standalone preregistered confirmatory results.",
            },
            {
                "plot_name": "Plot 3",
                "plot_inclusion_status": "not_included",
                "source_label": "FReD archived workflow workbook / OSF Registries queue",
                "corpus_what_it_is": "Archived FReD workflow workbook with additional converted/N-complete rows absent from the current clean FReD export.",
                "what_it_is_why_possible_candidate": "The FReD archive was rechecked because the freshness report found a possible rescue queue, including OSF Registries, ML1, RRR, Boyce, submissions, and OpenMKT-like sources.",
                "confirmed_fields": "Known locally: 343 converted/N-complete archive rows absent from the current clean export. A follow-up archive scan found 425 validated complete non-excluded rows overall, including 15 rows sourced from OSF Registries and 107 rows with a nonempty replication-preregistration field. Confirmed: N/effect conversion: partial; clean current-export status: no; duplicate/workflow filtering: unresolved; analytic preregistration: mixed/not confirmed.",
                "backing_file": "reports/corpus_candidates/fred_freshness_check_2026-04-27.md",
                "rows_considered": 343,
                "rows_preregistered_equivalent": 0,
                "rows_with_public_local_backing": 343,
                "rows_with_extractable_DN": 343,
                "rows_with_non_retracted_source": 343,
                "rows_contributed": 0,
                "rows_left_out_within_source": 343,
                "why": "not included because it is an archived workflow artifact, not a deduplicated current source table",
                "why_in_out": "Not included: the archive does contain preregistration-linked replication rows, including 15 OSF Registries rows, but they are replication-pair evidence rather than standalone Plot 3 result rows. Promoting them requires duplicate handling against existing FReD, Many Labs, RRR, and OSF-registries rows.",
            },
            {
                "plot_name": "Plot 3",
                "plot_inclusion_status": "not_included",
                "source_label": "ManyClasses 2 classroom registered-report materials",
                "corpus_what_it_is": "ManyClasses 2 OSF classroom intervention materials and scripts.",
                "what_it_is_why_possible_candidate": "ManyClasses 2 was rechecked because it is a coordinated preregistered classroom project with public OSF materials and a reported pooled prequestion-learning effect. The surfaced confirmatory result is a hierarchical log-odds/OR learning effect rather than a direct standardized D row.",
                "confirmed_fields": f"Known locally: {fmt_int(staged_counts['manyclasses_2__stage.csv']['expected_rows'])} expected rows, {fmt_int(staged_counts['manyclasses_2__stage.csv']['downloaded_file_count'])} downloaded files. Confirmed: public OSF payload: yes; Terracotta/classroom data and scripts: yes; N reported in the literature as 1,571; pooled log-odds/OR result surfaced; direct D/N confirmatory result table: no.",
                "backing_file": str(staged_counts["manyclasses_2__stage.csv"]["path"].relative_to(ROOT)),
                "rows_considered": staged_counts["manyclasses_2__stage.csv"]["expected_rows"],
                "rows_preregistered_equivalent": staged_counts["manyclasses_2__stage.csv"]["expected_rows"],
                "rows_with_public_local_backing": staged_counts["manyclasses_2__stage.csv"]["expected_rows"],
                "rows_with_extractable_DN": 0,
                "rows_with_non_retracted_source": staged_counts["manyclasses_2__stage.csv"]["expected_rows"],
                "rows_contributed": 0,
                "rows_left_out_within_source": staged_counts["manyclasses_2__stage.csv"]["expected_rows"],
                "why": "not included because the local payload is a classroom intervention analysis source, not a D/N-ready confirmatory result table",
                "why_in_out": "Not included: the best surfaced row is native log-odds/OR from a hierarchical classroom design. It stays staged until the project has an explicit, defensible OR-to-D policy and one-row-per-project extraction.",
            },
            {
                "plot_name": "Plot 3",
                "plot_inclusion_status": "not_included",
                "source_label": "TESS peer-reviewed survey-experiment archive",
                "corpus_what_it_is": "Time-sharing Experiments for the Social Sciences archive of fielded survey experiments with peer-reviewed proposals/study pages.",
                "what_it_is_why_possible_candidate": "TESS was added as a political-science survey-experiment extraction queue because its public past-studies index is finite, scrapeable, and organized around pre-fielding peer-reviewed study proposals. The final research pass weakened its status: TESS proposals are useful transparency evidence, but TESS itself is not uniformly PAP-grade preregistration, and the index does not contain final article effect sizes or analytic Ns.",
                "confirmed_fields": f"Verified by scraping `https://tessexperiments.org/paststudies` plus study pages: {fmt_int(tess_index_rows)} unique study URLs; {fmt_int(tess_with_n)} pages expose sample size; {fmt_int(tess_with_pap)} pages surface a likely PAP/pre-analysis-plan URL; {fmt_int(tess_with_results)} pages include a Summary of Results section; {fmt_int(tess_native_candidates)} pages expose enough N/native-stat text to enter the native-metric rescue queue. Confirmed: public index: yes; proposal/study page: yes at platform level; explicit full PAP-grade preregistration: not guaranteed; extractable final D/N in the index: no.",
                "backing_file": str(TESS_STUDY_INDEX.relative_to(ROOT)),
                "rows_considered": tess_index_rows,
                "rows_preregistered_equivalent": tess_index_rows,
                "rows_with_public_local_backing": tess_index_rows,
                "rows_with_extractable_DN": 0,
                "rows_with_non_retracted_source": tess_index_rows,
                "rows_contributed": 0,
                "rows_left_out_within_source": tess_index_rows,
                "why": "not included yet because the archive is a discovery queue, not a D/N result table",
                "why_in_out": "Not included yet: TESS likely contains many useful survey-experiment rescue candidates, but each dot still needs case-level verification that the proposal/preregistration is strong enough, plus paper/result linkage, D or native effect extraction, and analytic N. The generated CSV is the work queue for that screen, not evidence to plot today.",
            },
            {
                "plot_name": "Plot 3",
                "plot_inclusion_status": "not_included",
                "source_label": "Political-science PAP Dataverse/DIME/SCORE rescue worklist",
                "corpus_what_it_is": "Concrete political-science PAP/preregistration rescue targets from AEA, EGAP/Metaketa, TESS, SCORE/JEPS, DIME, APSR/AJPS/CPS Dataverse, OpenICPSR, Zenodo, and OSF links.",
                "what_it_is_why_possible_candidate": "The worklist was added because the political-science passes named specific row-level targets with visible preregistration URLs or verification targets, result pages, and data/package URLs. These are not broad registry metadata rows; they are extraction tickets with enough detail to drive package parsing.",
                "confirmed_fields": f"Known locally: {fmt_int(polisci_rescue_rows)} concrete rescue tickets. Confirmed for each ticket: prereg/PAP URL or verification target: yes; result or article URL: yes; data/package URL where known: yes; final strict D/N: no, pending package/table extraction.",
                "backing_file": str(POLISCI_RESCUE_WORKLIST.relative_to(ROOT)),
                "rows_considered": polisci_rescue_rows,
                "rows_preregistered_equivalent": polisci_rescue_rows,
                "rows_with_public_local_backing": polisci_rescue_rows,
                "rows_with_extractable_DN": 0,
                "rows_with_non_retracted_source": polisci_rescue_rows,
                "rows_contributed": 0,
                "rows_left_out_within_source": polisci_rescue_rows,
                "why": "not included yet because these are package-level extraction tickets, not completed D/N rows",
                "why_in_out": "Not included yet: these named AEA/EGAP/TESS/Dataverse/DIME/SCORE/OpenICPSR/Zenodo targets are the next extraction queue. They need package downloads, PAP selector checks, and either D conversion inputs or native ATE/SE/N extraction before they can enter a plot panel.",
            },
            {
                "plot_name": "Plot 3",
                "plot_inclusion_status": "not_included",
                "source_label": "EGAP Metaketa I information/accountability native ATE rows",
                "corpus_what_it_is": "Coordinated EGAP Metaketa I information-and-accountability field experiments with a harmonized meta-pre-analysis plan and native ATE tables.",
                "what_it_is_why_possible_candidate": "Metaketa I was rechecked because the local GitHub archive contains the CUP Book chapter 11 meta-analysis scripts and tables for the preregistered information/accountability experiments. The pooled primary vote-choice estimate is a strong PAP/native-metric candidate.",
                "confirmed_fields": "Verified locally in `tab_11.1_main_effects.tex`: the overall vote-choice treatment estimate is 0.003 with SE 0.010, 25,820 observations, and control mean 0.369; good-news and bad-news vote-choice columns report 13,196 and 12,531 observations. Confirmed: coordinated PAP/native primary outcome: yes; N/observations and SE: yes; source-provided standardized D: no.",
                "backing_file": "data/raw/replication_projects/lead_harvest/metaketa_i_2019/github_metaketa_i/metaketa-i-main.zip; CUP_Book/ch11_meta-analysis/tables/tab_11.1_main_effects.tex",
                "rows_considered": 1,
                "rows_preregistered_equivalent": 1,
                "rows_with_public_local_backing": 1,
                "rows_with_extractable_DN": 0,
                "rows_with_non_retracted_source": 1,
                "rows_contributed": 0,
                "rows_left_out_within_source": 1,
                "why": "not included as separate native/component rows because the pooled project dot is now included and component ATE rows need a native-metric lane",
                "why_in_out": "Not included as component/native rows: the pooled Metaketa I paper/project median now enters strict Plot 3. Separate good-news, bad-news, country, and adjusted ATE rows stay staged because mixing them with the pooled row would double-count nested evidence and some component metrics are native clustered ATEs.",
            },
            {
                "plot_name": "Plot 3",
                "plot_inclusion_status": "not_included",
                "source_label": "EGAP Metaketa III natural-resource monitoring native rows",
                "corpus_what_it_is": "EGAP Metaketa III coordinated natural-resource-monitoring field experiments with public OSF replication materials.",
                "what_it_is_why_possible_candidate": "Metaketa III was recovered from the crash notes because the local staged harvest already documents public parent and component replication packages with site-estimate RData and Stata/R payloads.",
                "confirmed_fields": f"Known locally: {fmt_int(staged_counts['metaketa_iii_2021__stage.csv']['expected_rows'])} expected native field-experiment rows and {fmt_int(staged_counts['metaketa_iii_2021__stage.csv']['downloaded_file_count'])} downloaded files. Confirmed: public field-experiment replication package: yes; native ATE/site-estimate files: yes; source-provided standardized D/N row table: no.",
                "backing_file": str(staged_counts["metaketa_iii_2021__stage.csv"]["path"].relative_to(ROOT)),
                "rows_considered": staged_counts["metaketa_iii_2021__stage.csv"]["expected_rows"],
                "rows_preregistered_equivalent": staged_counts["metaketa_iii_2021__stage.csv"]["expected_rows"],
                "rows_with_public_local_backing": staged_counts["metaketa_iii_2021__stage.csv"]["expected_rows"],
                "rows_with_extractable_DN": 0,
                "rows_with_non_retracted_source": staged_counts["metaketa_iii_2021__stage.csv"]["expected_rows"],
                "rows_contributed": 0,
                "rows_left_out_within_source": staged_counts["metaketa_iii_2021__stage.csv"]["expected_rows"],
                "why": "not included as separate native/component rows because the pooled standardized-index project dot is now included",
                "why_in_out": "Not included as component/native rows: the pooled Metaketa III paper/project median now enters strict Plot 3. Site-specific ATEs and native resource outcomes such as forest cover and pollution concentration stay staged for a native-metric or component panel.",
            },
            {
                "plot_name": "Plot 3",
                "plot_inclusion_status": "not_included",
                "source_label": "EGAP Metaketa IV community-policing native rows",
                "corpus_what_it_is": "EGAP Metaketa IV coordinated community-policing field experiments with integrated public OSF result outputs.",
                "what_it_is_why_possible_candidate": "Metaketa IV was recovered from the crash notes because the local staged harvest includes an integrated OSF results tree with study-estimate and meta-estimate RDS outputs.",
                "confirmed_fields": f"Known locally: {fmt_int(staged_counts['metaketa_iv_2021__stage.csv']['expected_rows'])} expected native field-experiment rows and {fmt_int(staged_counts['metaketa_iv_2021__stage.csv']['downloaded_file_count'])} downloaded files. Confirmed: public field-experiment result outputs: yes; native study/meta estimates: yes; source-provided standardized D/N row table: no.",
                "backing_file": str(staged_counts["metaketa_iv_2021__stage.csv"]["path"].relative_to(ROOT)),
                "rows_considered": staged_counts["metaketa_iv_2021__stage.csv"]["expected_rows"],
                "rows_preregistered_equivalent": staged_counts["metaketa_iv_2021__stage.csv"]["expected_rows"],
                "rows_with_public_local_backing": staged_counts["metaketa_iv_2021__stage.csv"]["expected_rows"],
                "rows_with_extractable_DN": 0,
                "rows_with_non_retracted_source": staged_counts["metaketa_iv_2021__stage.csv"]["expected_rows"],
                "rows_contributed": 0,
                "rows_left_out_within_source": staged_counts["metaketa_iv_2021__stage.csv"]["expected_rows"],
                "why": "not included as separate native/component rows because the pooled standardized-index project dot is now included",
                "why_in_out": "Not included as component/native rows: the pooled Metaketa IV paper/project median now enters strict Plot 3. Country/site rows, police rows, cluster-level rows, and native administrative outcomes stay staged to avoid nested non-independent evidence in the main layer.",
            },
            {
                "plot_name": "Plot 3",
                "plot_inclusion_status": "not_included",
                "source_label": "Communication privacy preregistered replication corpus",
                "corpus_what_it_is": "Preregistered three-study communication privacy replication with public data and analysis artifacts.",
                "what_it_is_why_possible_candidate": "The communication privacy corpus was rechecked because it has an explicit preregistration PDF, local cleaned data, and many SEM/path outputs in the replication-pair file.",
                "confirmed_fields": f"Known locally: {fmt_int(replication_rows(source_patterns=[r'Communication privacy']))} promoted/staged path rows and {fmt_int(staged_counts['communication_privacy_2025__stage.csv']['downloaded_file_count'])} downloaded source files. Confirmed: preregistration: yes; D/N or path-like rows: yes in Plot 1 context; standalone confirmatory result table for Plot 3: no; metric conversion policy: unresolved.",
                "backing_file": str(staged_counts["communication_privacy_2025__stage.csv"]["path"].relative_to(ROOT)),
                "rows_considered": replication_rows(source_patterns=[r"Communication privacy"]),
                "rows_preregistered_equivalent": replication_rows(source_patterns=[r"Communication privacy"]),
                "rows_with_public_local_backing": replication_rows(source_patterns=[r"Communication privacy"]),
                "rows_with_extractable_DN": replication_rows(source_patterns=[r"Communication privacy"]),
                "rows_with_non_retracted_source": replication_rows(source_patterns=[r"Communication privacy"]),
                "rows_contributed": 0,
                "rows_left_out_within_source": replication_rows(source_patterns=[r"Communication privacy"]),
                "why": "not included because those rows currently serve as replication-pair/path evidence and need a separate SEM/path metric policy",
                "why_in_out": "Not included: the preregistered corpus is real and local, but adding the path rows here would mix SEM/path metrics with the D/N confirmatory-result layer and double-count Plot 1-adjacent evidence.",
            },
            {
                "plot_name": "Plot 3",
                "plot_inclusion_status": "not_included",
                "source_label": "Retrieval-extinction rats preregistered replication",
                "corpus_what_it_is": "Preregistered direct replication attempt of the retrieval-extinction effect in cued fear conditioning in rats.",
                "what_it_is_why_possible_candidate": "This source was rechecked because it is explicitly preregistered and the local harvest already promoted three original-vs-replication outcome rows.",
                "confirmed_fields": f"Known locally: {fmt_int(replication_rows(source_patterns=[r'Retrieval-extinction rats']))} D/N pair rows. Confirmed: preregistered replication: yes; D/N: yes; independent standalone Plot 3 row family: no.",
                "backing_file": str(staged_counts["retrieval_extinction_rats_2017__stage.csv"]["path"].relative_to(ROOT)),
                "rows_considered": replication_rows(source_patterns=[r"Retrieval-extinction rats"]),
                "rows_preregistered_equivalent": replication_rows(source_patterns=[r"Retrieval-extinction rats"]),
                "rows_with_public_local_backing": replication_rows(source_patterns=[r"Retrieval-extinction rats"]),
                "rows_with_extractable_DN": replication_rows(source_patterns=[r"Retrieval-extinction rats"]),
                "rows_with_non_retracted_source": replication_rows(source_patterns=[r"Retrieval-extinction rats"]),
                "rows_contributed": 0,
                "rows_left_out_within_source": replication_rows(source_patterns=[r"Retrieval-extinction rats"]),
                "why": "not included because it is already direct-replication pair evidence rather than a standalone preregistered-result corpus",
                "why_in_out": "Not included: the three rows are valid and already handled as original-vs-replication evidence. Plot 3 excludes them to avoid double-counting replication-pair arrows.",
            },
            {
                "plot_name": "Plot 3",
                "plot_inclusion_status": "not_included",
                "source_label": "Registered Replication Reports per-lab rows",
                "corpus_what_it_is": "Per-lab rows from major published Registered Replication Reports documented in the appendix audit.",
                "what_it_is_why_possible_candidate": "The RRR lab-level audit was considered because these are preregistered multi-lab replication analyses and the appendix documents recoverable per-lab D/N-style rows.",
                "confirmed_fields": "Known: 205 verified per-lab rows documented in the appendix across 10 RRRs. Confirmed: preregistered replication status: yes; current dedicated Plot 3 local source table: no; independence from Plot 1 pair rows: no.",
                "backing_file": "documented in moved appendix material",
                "rows_considered": 205,
                "rows_preregistered_equivalent": 205,
                "rows_with_public_local_backing": 0,
                "rows_with_extractable_DN": 0,
                "rows_with_non_retracted_source": 205,
                "rows_contributed": 0,
                "rows_left_out_within_source": 205,
                "why": "not included because the same RRR evidence is already represented in Plot 1 replication pairs and the lab-level artifact is not yet a deduplicated Plot 3 source table",
                "why_in_out": "Not included: real preregistered replication evidence, but adding lab rows here would double-count replication evidence already represented in Plot 1 until a separate within-project heterogeneity policy is written.",
            },
        ]
    )
    prereg_details = normalize_preregistered_results()
    actual_counts_by_source = prereg_details["source_family"].value_counts().to_dict()
    rows_considered_by_source: dict[str, int] = {}
    if POLISCI_PAPER_PROJECT_MEDIANS.exists():
        polisci_medians = pd.read_csv(POLISCI_PAPER_PROJECT_MEDIANS)
        if not polisci_medians.empty:
            rows_considered_by_source.update(
                polisci_medians.groupby("source_family")["rows_collapsed"].sum().astype(int).to_dict()
            )

    for idx, row in plot3.loc[plot3["plot_inclusion_status"].eq("included")].iterrows():
        source_label = safe_text(row.get("source_label"))
        if source_label not in actual_counts_by_source:
            continue
        actual_count = int(actual_counts_by_source[source_label])
        considered_count = max(
            int(pd.to_numeric(pd.Series([row.get("rows_considered", 0)]), errors="coerce").fillna(0).iloc[0]),
            int(rows_considered_by_source.get(source_label, actual_count)),
        )
        plot3.loc[idx, "rows_considered"] = considered_count
        plot3.loc[idx, "rows_preregistered_equivalent"] = max(
            int(pd.to_numeric(pd.Series([row.get("rows_preregistered_equivalent", 0)]), errors="coerce").fillna(0).iloc[0]),
            considered_count,
        )
        plot3.loc[idx, "rows_with_public_local_backing"] = max(
            int(pd.to_numeric(pd.Series([row.get("rows_with_public_local_backing", 0)]), errors="coerce").fillna(0).iloc[0]),
            considered_count,
        )
        plot3.loc[idx, "rows_with_extractable_DN"] = max(
            int(pd.to_numeric(pd.Series([row.get("rows_with_extractable_DN", 0)]), errors="coerce").fillna(0).iloc[0]),
            actual_count,
        )
        plot3.loc[idx, "rows_with_non_retracted_source"] = max(
            int(pd.to_numeric(pd.Series([row.get("rows_with_non_retracted_source", 0)]), errors="coerce").fillna(0).iloc[0]),
            considered_count,
        )
        plot3.loc[idx, "rows_contributed"] = actual_count
        plot3.loc[idx, "rows_left_out_within_source"] = max(0, considered_count - actual_count)

    known_source_labels = set(plot3["source_label"].dropna().astype(str))
    missing_included_sources = [
        source_family
        for source_family in actual_counts_by_source
        if source_family not in known_source_labels
    ]
    if missing_included_sources:
        source_rows = []
        for source_family in missing_included_sources:
            group = prereg_details.loc[prereg_details["source_family"].eq(source_family)]
            first = group.iloc[0]
            actual_count = int(len(group))
            considered_count = int(rows_considered_by_source.get(source_family, actual_count))
            source_rows.append(
                {
                    "plot_name": "Plot 3",
                    "plot_inclusion_status": "included",
                    "source_label": source_family,
                    "corpus_what_it_is": safe_text(first.get("source_label")) or source_family,
                    "what_it_is_why_possible_candidate": (
                        "Included from the extraction-backed preregistered political-science "
                        "rescue layer after the one-dot-per-paper/project median collapse."
                    ),
                    "confirmed_fields": (
                        f"Confirmed locally: {fmt_int(considered_count)} extracted preregistered "
                        f"component/result row(s) collapse to {fmt_int(actual_count)} plotted "
                        "paper/project median row(s); D, N, source files, and selector notes are "
                        "stored in the result CSV and political-science median audit table."
                    ),
                    "backing_file": safe_text(first.get("source_file")),
                    "rows_considered": considered_count,
                    "rows_preregistered_equivalent": considered_count,
                    "rows_with_public_local_backing": considered_count,
                    "rows_with_extractable_DN": actual_count,
                    "rows_with_non_retracted_source": considered_count,
                    "rows_contributed": actual_count,
                    "rows_left_out_within_source": max(0, considered_count - actual_count),
                    "why": "included as paper/project median from the political-science rescue layer",
                    "why_in_out": (
                        "Included: extraction-backed political-science source family enters the "
                        "strict plotted layer as one median row per paper/project; underlying "
                        "component rows remain in the audit files rather than inflating the plot."
                    ),
                }
            )
        plot3 = pd.concat([plot3, pd.DataFrame(source_rows)], ignore_index=True)

    plot3["display_label"] = plot3["source_label"].map(plot3_display_label)
    plot3["source_key"] = plot3.apply(
        lambda r: safe_text(r.get("source_label")) and slugify(safe_text(r.get("source_label")), "plot3_source"),
        axis=1,
    )
    plot3["citation_key"] = plot3["source_label"].map(PLOT3_CITATION_KEYS).fillna("")
    plot3["plot_rows_made_in"] = np.where(plot3["plot_inclusion_status"] == "included", plot3["rows_contributed"], 0)
    plot3 = plot3.sort_values(["plot_rows_made_in", "source_label"], ascending=[False, True])
    plot3.to_csv(out_csv, index=False)

    field_summary = (
        prereg_details.groupby(["field", "field_label"], sort=False)
        .agg(
            rows=("D", "size"),
            source_families=("source_family", "nunique"),
            median_D=("D", "median"),
            median_N=("N", "median"),
        )
        .reset_index()
        .sort_values(["rows", "field_label"], ascending=[False, True])
    )
    included = plot3.loc[plot3["plot_inclusion_status"] == "included"].copy()
    excluded = plot3.loc[plot3["plot_inclusion_status"] == "not_included"].copy()
    corpus_rows = pd.concat([included, excluded], ignore_index=True)
    corpus_rows = corpus_rows.sort_values(["plot_rows_made_in", "source_label"], ascending=[False, True])
    source_rendered_citations = read_bibtex_rendered_citations(REFERENCES_BIB)
    display_rows = []
    sorted_prereg_details = prereg_details.sort_values(["field", "source_family", "source_row_number"]).copy()
    for row in sorted_prereg_details.itertuples(index=False):
        citation_key = safe_text(row.citation_key)
        display_rows.append(
            {
                "field": safe_text(row.field_label),
                "source": safe_text(row.source_label),
                "source_family": safe_text(row.source_family),
                "source_citation_key": citation_key,
                "source_citation_ref": f"@{citation_key}" if citation_key else "",
                "source_citation_rendered": source_rendered_citations.get(citation_key, ""),
                "source_citation_bibtex_file": str(REFERENCES_BIB.relative_to(ROOT)),
                "specific_paper_result": safe_text(row.row_label),
                "specific_paper_result_display": safe_text(row.row_label)[:90],
                "journal": safe_text(row.journal),
                "D": row.D,
                "N": row.N,
                "D_N_display": f"{fmt_number(row.D, 3)} / {fmt_int(row.N)}",
                "source_row_number": safe_text(row.source_row_number),
            }
        )
    clean_tsv_frame(pd.DataFrame(display_rows)).to_csv(PREREG_DISPLAY_TABLE_TSV, sep="\t", index=False)

    lines = [
        "## Corpora Considered",
        "",
        f"Machine-readable catalog: [plot3_preregistered_source_catalog.csv](../data/derived/effect_inflation_dataset/{out_csv.name})",
        "",
        f"At the moment Plot 3 has `{len(included):,}` included source families and `{len(excluded):,}` explicitly considered but not included source families.",
        "",
        "This table is the corpus-level admission audit: what was considered, why it looked eligible, what fields were actually confirmed, why it is in or out, and how many observations made it into the plotted layer.",
        "",
        markdown_table_block(
            [["Corpus considered", "What it is / why possible candidate", "Confirmed fields", "Why in/out", "# obs in"]]
            + [
                [
                    source_key_badge(row.display_label or row.source_label, row.source_key, row.citation_key),
                    safe_text(row.what_it_is_why_possible_candidate),
                    safe_text(row.confirmed_fields),
                    safe_text(row.why_in_out),
                    fmt_int(row.plot_rows_made_in),
                ]
                for row in corpus_rows.itertuples(index=False)
            ],
            "dataset-table source-audit-table plot3-source-audit-table",
        ),
        "",
        "## Specific Observations Included",
        "",
        f"Machine-readable result-level file: [plot3_preregistered_results.tsv](../data/derived/effect_inflation_dataset/{PREREG_RESULTS_TSV.name}) "
        f"(CSV mirror: [plot3_preregistered_results.csv](../data/derived/effect_inflation_dataset/{PREREG_RESULTS.name})).",
        "",
        f"Machine-readable display-table file: [plot3_preregistered_display_table.tsv](../data/derived/effect_inflation_dataset/{PREREG_DISPLAY_TABLE_TSV.name})",
        "",
        f"The specific-observation layer has `{len(prereg_details):,}` plotted preregistered result/project dots. Admission now uses the relaxed planned-result rule plus one-dot-per-paper/project median collapse where a source exposes multiple planned outcomes, treatment arms, sites, or archive components. Political-science extraction packages retain their component contrasts in the audit files, but the plotted political-science layer is collapsed to paper/project medians. For plotting, rows are collapsed by broad field rather than raw source family. The result-level CSV still records source citation, result label, journal, `D`, `N`, and the source row number for auditability. Support calls are retained in the CSV as metadata but are not used for admission or visual encoding, because they mostly track the preregistered decision rule rather than a distinct effect-size concept.",
        "",
        markdown_table_block(
            [["Field", "Rows", "Source families", "Median D", "Median N"]]
            + [
                [
                    safe_text(row.field_label),
                    fmt_int(row.rows),
                    fmt_int(row.source_families),
                    fmt_number(row.median_D, 3),
                    fmt_int(row.median_N),
                ]
                for row in field_summary.itertuples(index=False)
            ],
            "dataset-table field-summary-table preregistered-field-summary-table",
        ),
        "",
        markdown_table_block(
            [["Field", "Source", "Specific paper/result", "Journal", "D/N"]]
            + [
                [
                    safe_text(row.field_label),
                    source_key_badge(row.source_label, row.source_family, row.citation_key),
                    safe_text(row.row_label)[:90],
                    safe_text(row.journal),
                    f"{fmt_number(row.D, 3)} / {fmt_int(row.N)}",
                ]
                for row in sorted_prereg_details.itertuples(index=False)
            ],
            "dataset-table specific-observation-table preregistered-observation-table",
        ),
        "",
        "### What Is Still Missing",
        "",
        "- The included core now combines Registered Reports, PSA-CR001 and PSA-CR002 pooled/preregistered hypothesis rows, PSA004 pooled Gettier evidence, ManyBabies 1 and ManyBabies 1 Bilingual, ManyClasses 1, pooled EGAP Metaketa I/III/IV PAP rows, the Schäfer/Schwarz preregistered key-effect sample, SCORE preregistration-indicated paper-level rows, van den Akker matched preregistered-result paper medians, and RPCB preclinical Registered Report paper medians.",
        "- The expanded considered-but-not-included list now names the major local preregistered-like sidecars separately: enriched TESS study-page extraction queue, concrete AEA/EGAP/Dataverse/DIME/SCORE political-science worklist, Many Labs, RRR pair rows, PSA replication rows, Transparent Psi, Allen/Mehler RR support-rate evidence, ManyBabies 3, ManyBabies 4, ManyClasses 2, EGAP Metaketa I/III/IV native/component ATE rows, ERN/Pe, self-control fMRI, Twomey, Linden, Protzko, AACT/ClinicalTrials.gov, CliniFact, Brodeur preregistered/PAP economics table tests, Nordic trial reporting, FReD, communication privacy, retrieval-extinction rats, and the larger van den Akker selective-hypothesis-reporting corpus.",
        "- Most of those extra local sources are out because they are already Plot 1 replication-pair evidence, registry metadata rather than analytic preregistration, publication-linkage metadata without effect statistics, document/native-metric payloads without a compact D/N result table, or extracted table-test corpora without a focal/main-result selector.",
        "- The considered list is still a working audit, not a claim that every preregistered-like source on the web has been exhausted.",
    ]
    write_qmd_with_table(PLOT3_SOURCES_QMD, lines)


def write_plot3_criteria_matrix() -> None:
    plot3 = pd.read_csv(DATASET_DERIVED_DIR / "plot3_preregistered_source_catalog.csv")
    out_csv = DATASET_DERIVED_DIR / "plot3_preregistered_criteria_matrix.csv"

    matrix = plot3.copy()
    for column in [
        "rows_preregistered_equivalent",
        "rows_with_public_local_backing",
        "rows_with_extractable_DN",
        "rows_with_non_retracted_source",
    ]:
        if column not in matrix.columns:
            matrix[column] = 0
        matrix[column] = numeric_series(matrix[column]).fillna(0).astype(int)
    matrix["rows_currently_included"] = np.where(
        matrix["plot_inclusion_status"] == "included",
        matrix["rows_contributed"],
        0,
    )
    matrix = matrix.sort_values(
        ["rows_currently_included", "rows_with_extractable_DN", "rows_considered", "source_label"],
        ascending=[False, False, False, True],
    )
    matrix["display_label"] = matrix["source_label"].map(plot3_display_label)
    matrix.to_csv(out_csv, index=False)

    total_considered = int(matrix["rows_considered"].sum())
    total_dn_ready = int(matrix["rows_with_extractable_DN"].sum())
    total_included = int(matrix["rows_currently_included"].sum())

    lines = [
        f"Machine-readable matrix: [plot3_preregistered_criteria_matrix.csv](../data/derived/effect_inflation_dataset/{out_csv.name})",
        "",
        "These counts separate discovery from admission. `Extractable D/N rows` means the project has local numeric D/N rows somewhere for that source; `Currently included` means those rows also survive the analytic-preregistration, non-retraction, independence/deduplication, and current-layer policy gates. Under the relaxed rule, a source may expose multiple planned preregistered results per paper/project, but the plotted layer uses a median collapse when that within-paper result set is explicit.",
        "",
        f"Across the currently named Plot 3 source families, `{total_dn_ready:,}` / `{total_considered:,}` considered rows already have local D/N encoding somewhere in the project, and `{total_included:,}` rows enter the preregistered-results plot after the gates are applied.",
        "",
        "Source-table column criteria:",
        "",
        markdown_table_block(
            [["Column", "Criterion used"]]
            + [
                ["Corpus considered", "One source family or deliberately tracked comparator family audited for Plot 3 admission."],
                ["What it is / why possible candidate", "Brief source identity plus the concrete reason we thought it might contain preregistered confirmatory D/N rows."],
                ["Confirmed fields", "Only fields verified locally or documented in the current audit: row counts, preregistration/registration status, D/N availability, support-status availability, and key caveats."],
                ["Why in/out", "Final current gate call: included, excluded by analytic-preregistration, excluded by retraction, excluded as duplicate/nested evidence, or blocked by missing local row table. The focal-selector gate is now a planned-result gate plus median collapse, not a single-main-result-only gate."],
                ["# obs in", "Number of result rows from that source family entering `plot3_preregistered_results.csv` and therefore the plotted figure."],
            ],
            "dataset-table dataset-criteria-table source-column-criteria-table",
        ),
        "",
        '::: {.dataset-table .dataset-criteria-table}',
        "",
        markdown_table(
            [["Source family", "Rows considered", "Preregistered-confirmatory equivalent", "Public local backing", "Extractable D/N rows", "Non-retracted source", "Currently included"]]
            + [
                [
                    source_key_badge(row.display_label or row.source_label, row.source_label, row.citation_key),
                    fmt_int(row.rows_considered),
                    fmt_int(row.rows_preregistered_equivalent),
                    fmt_int(row.rows_with_public_local_backing),
                    fmt_int(row.rows_with_extractable_DN),
                    fmt_int(row.rows_with_non_retracted_source),
                    fmt_int(row.rows_currently_included),
                ]
                for row in matrix.itertuples(index=False)
            ]
        ),
        "",
        ":::",
        "",
        "For Plot 3, the real bottleneck is not discovery. It is converting conceptually relevant preregistered-like sources into local auditable source tables that survive the non-retraction and analytic-preregistration gates.",
    ]
    write_qmd_with_table(PLOT3_CRITERIA_QMD, lines)


def write_plot4_source_catalog() -> None:
    rep = pd.read_csv(REPLICATION_ALL)
    pub = pd.read_csv(PUBLISHED_PAPERS)
    all_source = normalize_all_source_dn_rows()
    layer_counts = all_source.groupby("source_layer").size().to_dict()
    staged_count = len(list(HARVEST_STAGED_DIR.glob("*.csv")))
    promoted_count = len(list(HARVEST_PROMOTED_DIR.glob("*.csv")))
    out_csv = DATASET_DERIVED_DIR / "plot4_all_source_dump_catalog.csv"

    plot4 = pd.DataFrame(
        [
            {
                "plot_name": "Plot 4",
                "plot_inclusion_status": "included",
                "source_label": "Replication-pairs live corpus",
                "citation_key": "internalPlot4AllSourceDump",
                "corpus_what_it_is": "Original and follow-up sides from the live replication-pair corpus.",
                "backing_path": str(REPLICATION_ALL.relative_to(ROOT)),
                "rows_available": 2 * len(rep),
                "rows_in_dump": int(layer_counts.get("replication_pair_original", 0) + layer_counts.get("replication_pair_followup", 0)),
                "inclusion_rule": "split each live endpoint pair into original-side and follow-up-side D/N points",
                "remaining_caveat": "side-level points intentionally duplicate pair membership; this layer is descriptive, not an inferential paired analysis",
            },
            {
                "plot_name": "Plot 4",
                "plot_inclusion_status": "included",
                "source_label": "Published-paper endpoint candidate corpus",
                "citation_key": "internalPlot4AllSourceDump",
                "corpus_what_it_is": "Paper/unit-level published endpoint candidates with recoverable D and N.",
                "backing_path": str(PUBLISHED_PAPERS.relative_to(ROOT)),
                "rows_available": len(pub),
                "rows_in_dump": int(layer_counts.get("published_candidate_paper", 0)),
                "inclusion_rule": "include every candidate paper/study unit with positive D and N from the current candidate paper-level file",
                "remaining_caveat": "mixes published-original candidates, comparator-only rows, and other paper-level candidates; source_status carries that distinction",
            },
            {
                "plot_name": "Plot 4",
                "plot_inclusion_status": "included",
                "source_label": "Preregistered-results tables",
                "citation_key": "internalPlot4AllSourceDump",
                "corpus_what_it_is": "Normalized preregistered confirmatory result rows from Plot 3.",
                "backing_path": f"{PREREG_TABLE_40.relative_to(ROOT)} | {PREREG_TABLE_41.relative_to(ROOT)}",
                "rows_available": int(layer_counts.get("preregistered_confirmatory_result", 0)),
                "rows_in_dump": int(layer_counts.get("preregistered_confirmatory_result", 0)),
                "inclusion_rule": "include each normalized preregistered confirmatory D/N result from Plot 3",
                "remaining_caveat": "small curated layer; not an exhaustive registry of preregistered science",
            },
            {
                "plot_name": "Plot 4",
                "plot_inclusion_status": "included_sidecar",
                "source_label": "Staged replication harvest artifacts",
                "citation_key": "internalPlot4AllSourceDump",
                "corpus_what_it_is": "Non-promoted staged harvest rows that already expose positive D and N for a side.",
                "backing_path": str(HARVEST_STAGED_DIR.relative_to(ROOT)),
                "rows_available": staged_count,
                "rows_in_dump": int(layer_counts.get("staged_harvest_original", 0) + layer_counts.get("staged_harvest_followup", 0)),
                "inclusion_rule": "include non-promoted staged rows only when a positive D and N are already present for a side",
                "remaining_caveat": "most staged files are roster-only, native-metric, or otherwise D-blocked and therefore remain out of this D/N figure",
            },
            {
                "plot_name": "Plot 4",
                "plot_inclusion_status": "not_included",
                "source_label": "Promoted harvest pair tables",
                "citation_key": "internalPlot4AllSourceDump",
                "corpus_what_it_is": "Source-specific promoted harvest outputs already folded into the live replication-pair table.",
                "backing_path": str(HARVEST_PROMOTED_DIR.relative_to(ROOT)),
                "rows_available": promoted_count,
                "rows_in_dump": 0,
                "inclusion_rule": "not separately loaded",
                "remaining_caveat": "promoted rows are already folded into the live replication-pairs corpus above, so direct inclusion would duplicate them",
            },
        ]
    )
    plot4 = plot4.sort_values(["rows_in_dump", "source_label"], ascending=[False, True])
    plot4.to_csv(out_csv, index=False)

    included = plot4.loc[plot4["plot_inclusion_status"].isin(["included", "included_sidecar"])].copy()
    excluded = plot4.loc[plot4["plot_inclusion_status"] == "not_included"].copy()
    corpus_rows = pd.concat([included, excluded], ignore_index=True)
    corpus_rows = corpus_rows.sort_values(["rows_in_dump", "source_label"], ascending=[False, True])
    layer_summary = (
        all_source.groupby("source_layer", dropna=False)
        .agg(points=("point_id", "count"), source_families=("source_family", "nunique"), median_D=("D", "median"), median_N=("N", "median"))
        .reset_index()
        .sort_values(["points", "source_layer"], ascending=[False, True])
    )
    top_families = (
        all_source.groupby(["source_layer", "source_family"], dropna=False)
        .size()
        .reset_index(name="points")
        .sort_values(["points", "source_layer", "source_family"], ascending=[False, True, True])
        .head(15)
    )

    def feeder_reason(row: pd.Series) -> str:
        return "; ".join(part for part in [safe_text(row.get("inclusion_rule")), safe_text(row.get("remaining_caveat"))] if part)

    lines = [
        "## Corpora Considered",
        "",
        f"Machine-readable catalog: [plot4_all_source_dump_catalog.csv](../data/derived/effect_inflation_dataset/{out_csv.name})",
        "",
        f"Machine-readable normalized row dump: [plot4_all_source_dn_rows.csv](../data/derived/effect_inflation_dataset/{ALL_SOURCE_DN_ROWS.name})",
        "",
        f"Plot 4 now has a first-pass all-source D/N surface map with `{len(all_source):,}` positive-D/N points. It is intentionally a descriptive dump, not a clean inferential layer.",
        "",
        "This first table is the feeder-corpus admission audit: what was considered, what it is, why it is in or out of the all-source dump, and how many observations made it in.",
        "",
        markdown_table_block(
            [["Corpus considered", "What it is", "Why in/out", "# obs in"]]
            + [
                [
                    safe_text(row.source_label),
                    safe_text(row.corpus_what_it_is),
                    (
                        "included"
                        if safe_text(row.plot_inclusion_status) == "included"
                        else (
                            "sidecar included"
                            if safe_text(row.plot_inclusion_status) == "included_sidecar"
                            else "not separately included"
                        )
                    )
                    + f": {feeder_reason(pd.Series(row._asdict()))}",
                    fmt_int(row.rows_in_dump),
                ]
                for row in corpus_rows.itertuples(index=False)
            ],
            "dataset-table source-audit-table",
        ),
        "",
        "## Specific Observations Included",
        "",
        f"Machine-readable row-level file: [plot4_all_source_dn_rows.csv](../data/derived/effect_inflation_dataset/{ALL_SOURCE_DN_ROWS.name})",
        "",
        f"The specific-row layer has `{len(all_source):,}` positive-`D`/`N` points. It records source family, source file, row unit, row label, point id, source layer, side, `D`, `N`, and publication-boundary flags.",
        "",
        "Layer summary:",
        "",
        markdown_table_block(
            [["Source layer", "Points", "Source families", "Median D", "Median N"]]
            + [
                [
                    safe_text(row.source_layer),
                    fmt_int(row.points),
                    fmt_int(row.source_families),
                    fmt_number(row.median_D),
                    fmt_int(row.median_N),
                ]
                for row in layer_summary.itertuples(index=False)
            ],
            "dataset-table compact-count-table",
        ),
        "",
        "Largest specific source families in the dump:",
        "",
        markdown_table_block(
            [["Source layer", "Source family", "Points"]]
            + [
                [safe_text(row.source_layer), safe_text(row.source_family), fmt_int(row.points)]
                for row in top_families.itertuples(index=False)
            ],
            "dataset-table compact-count-table",
        ),
        "",
        "### What Is Still Missing",
        "",
        "- Plot 4 now has a practical side-point/paper-unit schema, but it still needs a formal deduplication audit across overlapping source families.",
        "- Native-metric rows are still excluded from this D/N-only figure; they need either a parallel dump or explicit facet policy.",
        "- The all-source layer intentionally mixes paper-level candidate rows with pair-side rows, so it should not be read as a single exchangeable statistical sample.",
    ]
    write_qmd_with_table(PLOT4_SOURCES_QMD, lines)


def normalize_identifier_text(value: object) -> str:
    text = safe_text(value).strip()
    text = re.sub(r"^https?://(dx\.)?doi\.org/", "", text, flags=re.IGNORECASE)
    text = re.sub(r"^doi:\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s+", " ", text).strip().lower()
    return text


def paper_membership_key(
    *,
    plot_prefix: str,
    doi: object = "",
    title: object = "",
    fallback: object = "",
    nct: object = "",
) -> tuple[str, str]:
    doi_text = normalize_identifier_text(doi)
    if doi_text and doi_text not in {"nan", "none"}:
        return f"doi:{doi_text}", "doi"
    nct_text = safe_text(nct).strip().upper()
    if re.fullmatch(r"NCT\d{8}", nct_text):
        return f"nct:{nct_text.lower()}", "registry_id"
    title_text = normalize_identifier_text(title)
    if title_text and title_text not in {"nan", "none", "not coded"}:
        return f"title:{slugify(title_text, 'untitled')}", "title"
    fallback_text = safe_text(fallback).strip()
    return f"{plot_prefix}:{slugify(fallback_text, 'unit')}", "source_row_fallback"


def count_rows_represented(row: pd.Series, default: int = 1) -> int:
    for column in ["rows_collapsed", "n_tests_used", "table_test_rows", "matched_result_rows"]:
        if column in row.index:
            value = pd.to_numeric(pd.Series([row.get(column)]), errors="coerce").fillna(np.nan).iloc[0]
            if pd.notna(value) and int(value) > 0:
                return int(value)
    text = " ".join(
        safe_text(row.get(column))
        for column in ["row_label", "source_file", "confirmed_fields"]
        if column in row.index
    )
    for pattern in [
        r"paper median of\s+([0-9,]+)\s+preregistered result rows",
        r"([0-9,]+)\s+matched prereg result",
        r"([0-9,]+)\s+extracted preregistered component/result row",
        r"median collapse of\s+([0-9,]+)\s+preregistered result rows",
    ]:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return int(match.group(1).replace(",", ""))
    source_row_number = safe_text(row.get("source_row_number"))
    if ";" in source_row_number:
        return len([part for part in source_row_number.split(";") if part.strip()])
    return default


def clean_tsv_frame(df: pd.DataFrame) -> pd.DataFrame:
    """Keep TSV outputs one physical line per row."""
    if df.empty:
        return df
    out = df.copy()
    object_cols = [
        column
        for column in out.columns
        if pd.api.types.is_object_dtype(out[column]) or pd.api.types.is_string_dtype(out[column])
    ]
    for column in object_cols:
        out[column] = (
            out[column]
            .fillna("")
            .astype(str)
            .str.replace(r"[\r\n\t]+", " ", regex=True)
            .str.replace(r"\s{2,}", " ", regex=True)
            .str.strip()
        )
    return out


def read_bibtex_keys(path: Path = REFERENCES_BIB) -> set[str]:
    if not path.exists():
        return set()
    text = path.read_text(encoding="utf-8", errors="ignore")
    return set(re.findall(r"@\w+\{\s*([^,\s]+)", text))


def clean_bibtex_value(value: str) -> str:
    text = safe_text(value)
    for old, new in [
        ("\\&", "&"),
        ("\\%", "%"),
        ("\\_", "_"),
        ("\\{", "{"),
        ("\\}", "}"),
        ("\\textbackslash{}", "\\"),
    ]:
        text = text.replace(old, new)
    text = text.strip("{} ")
    return re.sub(r"\s{2,}", " ", text).strip()


def read_bibtex_rendered_citations(path: Path = REFERENCES_BIB) -> dict[str, str]:
    """Render a compact plain-text citation from local one-line BibTeX fields."""
    if not path.exists():
        return {}
    rendered: dict[str, str] = {}
    current_key = ""
    fields: dict[str, str] = {}

    def flush() -> None:
        if not current_key:
            return
        author = clean_bibtex_value(fields.get("author") or fields.get("authors") or "")
        title = clean_bibtex_value(fields.get("title", ""))
        year = clean_bibtex_value(fields.get("year", ""))
        venue = clean_bibtex_value(fields.get("journal") or fields.get("booktitle") or fields.get("publisher") or "")
        doi = clean_bibtex_value(fields.get("doi", ""))
        url = clean_bibtex_value(fields.get("url", ""))
        pieces: list[str] = []
        if author and year:
            pieces.append(f"{author} ({year}).")
        elif author:
            pieces.append(f"{author}.")
        elif year:
            pieces.append(f"({year}).")
        if title:
            pieces.append(f"{title}.")
        if venue:
            pieces.append(f"{venue}.")
        if doi:
            pieces.append(f"doi:{doi}.")
        elif url:
            pieces.append(url)
        rendered[current_key] = " ".join(pieces).strip() or current_key

    field_re = re.compile(r"^\s*([A-Za-z][A-Za-z0-9_-]*)\s*=\s*\{(.*)\},?\s*$")
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        entry = re.match(r"@\w+\{\s*([^,\s]+)", line)
        if entry:
            flush()
            current_key = entry.group(1)
            fields = {}
            continue
        match = field_re.match(line)
        if current_key and match:
            fields[match.group(1).lower()] = match.group(2).rstrip(",")
    flush()
    return rendered


def add_bibtex_mapping_columns(
    df: pd.DataFrame,
    bibtex_keys: set[str],
    bibtex_file: Path = REFERENCES_BIB,
    rendered_citations: dict[str, str] | None = None,
) -> pd.DataFrame:
    """Add explicit citation-to-BibTeX mapping columns to an audit TSV frame."""
    out = df.copy()
    if "citation_key" not in out.columns:
        out["citation_key"] = ""
    out["citation_key"] = out["citation_key"].fillna("").astype(str).str.strip()
    out["citation_ref"] = out["citation_key"].map(lambda key: f"@{key}" if key else "")
    rendered_citations = rendered_citations or {}
    out["citation_rendered"] = out["citation_key"].map(lambda key: rendered_citations.get(key, ""))
    out["citation_bibtex_file"] = str(bibtex_file.relative_to(ROOT))
    out["citation_in_bibtex"] = out["citation_key"].map(lambda key: bool(key and key in bibtex_keys))
    out["citation_bibtex_status"] = np.where(
        out["citation_key"].eq(""),
        "missing_citation_key",
        np.where(out["citation_in_bibtex"], "present_in_bibtex_file", "missing_from_bibtex_file"),
    )
    return out


def resolve_any_plot_citation(*labels: object, fallback: str = "") -> str:
    """Resolve a source label against all plot citation maps."""
    return (
        citation_key_from(PLOT3_CITATION_KEYS, *labels)
        or citation_key_from(PLOT2_CITATION_KEYS, *labels)
        or plot1_citation_key(*labels)
        or fallback
    )


DOT_BIB_BEGIN = "% BEGIN GENERATED DOT-LEVEL REFERENCES"
DOT_BIB_END = "% END GENERATED DOT-LEVEL REFERENCES"


def dot_level_citation_key(row: pd.Series) -> str:
    """Stable unique citation key for one rendered dot."""
    plot_slug = slugify(safe_text(row.get("plot_name")).lower(), "plot")
    source_slug = slugify(safe_text(row.get("source_family")).lower(), "source")[:32]
    identity = "|".join(
        safe_text(row.get(column))
        for column in [
            "plot_name",
            "dot_record_id",
            "source_layer",
            "source_family",
            "paper_key",
            "paper_title",
            "side",
            "D",
            "N",
        ]
    )
    digest = hashlib.sha1(identity.encode("utf-8", errors="ignore")).hexdigest()[:12]
    return f"dot_{plot_slug}_{source_slug}_{digest}"


def bibtex_escape_local(value: object) -> str:
    text = safe_text(value)
    text = re.sub(r"[\r\n\t]+", " ", text)
    text = re.sub(r"\s{2,}", " ", text).strip()
    replacements = {
        "\\": "\\textbackslash{}",
        "{": "\\{",
        "}": "\\}",
        "&": "\\&",
        "%": "\\%",
        "_": "\\_",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text


def doi_from_dot_row(row: pd.Series) -> str:
    for column in ["paper_doi", "paper_title", "dot_record_id", "paper_key"]:
        doi = normalize_doi_value(row.get(column))
        if doi.startswith("10."):
            return doi
    match = re.search(r"(?i)\b(10\.\d{4,9}/[-._;()/:A-Z0-9]+)", " ".join(safe_text(row.get(c)) for c in ["paper_title", "dot_record_id", "paper_key"]))
    return normalize_doi_value(match.group(1)) if match else ""


def replace_dot_level_bibtex_entries(dot_membership: pd.DataFrame) -> None:
    """Write one child-result BibTeX record per rendered dot outside the manuscript bibliography."""
    existing = REFERENCES_BIB.read_text(encoding="utf-8", errors="ignore") if REFERENCES_BIB.exists() else ""
    pattern = re.compile(
        rf"\n?{re.escape(DOT_BIB_BEGIN)}.*?{re.escape(DOT_BIB_END)}\n?",
        flags=re.DOTALL,
    )
    stripped = pattern.sub("\n", existing).rstrip()
    if stripped != existing.rstrip():
        REFERENCES_BIB.write_text(stripped + "\n", encoding="utf-8")

    entries: list[str] = []
    for _, row in dot_membership.iterrows():
        key = safe_text(row.get("citation_key"))
        title = safe_text(row.get("paper_title")) or safe_text(row.get("dot_record_id")) or "Rendered D/N dot"
        title = title[:800]
        doi = doi_from_dot_row(row)
        url = doi_url(doi)
        note_parts = [
            f"Rendered D/N dot in {safe_text(row.get('plot_name'))}",
            f"source_family={safe_text(row.get('source_family'))}",
            f"source_layer={safe_text(row.get('source_layer'))}",
            f"dot_record_id={safe_text(row.get('dot_record_id'))}",
            f"D={safe_text(row.get('D'))}",
            f"N={safe_text(row.get('N'))}",
        ]
        source_citation_key = safe_text(row.get("source_citation_key"))
        if source_citation_key:
            note_parts.append(f"source_citation=@{source_citation_key}")
        fields = [
            f"  title = {{{bibtex_escape_local(title)}}}",
            "  author = {{PublishedSmallNStudiesDon-tMatter dot-level extraction}}",
            "  year = {2026}",
            f"  note = {{{bibtex_escape_local('; '.join(note_parts))}}}",
        ]
        if doi:
            fields.append(f"  doi = {{{bibtex_escape_local(doi)}}}")
        if url:
            fields.append(f"  url = {{{bibtex_escape_local(url)}}}")
        entries.append(f"@misc{{{key},\n" + ",\n".join(fields) + "\n}")

    block = DOT_BIB_BEGIN + "\n" + "\n\n".join(entries) + "\n" + DOT_BIB_END
    PLOT_DOT_REFERENCES_BIB.write_text(block + "\n", encoding="utf-8")


def add_source_citation_mapping_columns(df: pd.DataFrame, bibtex_keys: set[str]) -> pd.DataFrame:
    out = df.copy()
    rendered_citations = read_bibtex_rendered_citations(REFERENCES_BIB)
    if "source_citation_key" not in out.columns:
        out["source_citation_key"] = ""
    out["source_citation_key"] = out["source_citation_key"].fillna("").astype(str).str.strip()
    out["source_citation_ref"] = out["source_citation_key"].map(lambda key: f"@{key}" if key else "")
    out["source_citation_rendered"] = out["source_citation_key"].map(lambda key: rendered_citations.get(key, ""))
    out["source_citation_bibtex_file"] = str(REFERENCES_BIB.relative_to(ROOT))
    out["source_citation_in_bibtex"] = out["source_citation_key"].map(lambda key: bool(key and key in bibtex_keys))
    out["source_citation_bibtex_status"] = np.where(
        out["source_citation_key"].eq(""),
        "missing_source_citation_key",
        np.where(out["source_citation_in_bibtex"], "present_in_bibtex_file", "missing_from_bibtex_file"),
    )
    return out


def write_plot_dot_membership_tsv() -> None:
    """Write one TSV row per plotted D/N dot across the rendered plot data files."""
    dot_rows: list[dict[str, object]] = []

    def add_dot(
        *,
        plot_name: str,
        dot_record_id: object,
        source_layer: object,
        source_family: object,
        source_label: object,
        source_citation_key: object,
        paper_key: object,
        paper_key_quality: object,
        paper_title: object,
        paper_doi: object = "",
        row_unit: object = "",
        side: object = "",
        D: object = "",
        N: object = "",
        source_file_or_catalog: object = "",
        source_row_number: object = "",
        paper_level_unit: object = "",
        paper_level_note: object = "",
    ) -> None:
        dot_rows.append(
            {
                "plot_name": plot_name,
                "dot_record_id": dot_record_id,
                "source_layer": source_layer,
                "source_family": source_family,
                "source_label": source_label,
                "source_citation_key": source_citation_key,
                "paper_key": paper_key,
                "paper_key_quality": paper_key_quality,
                "paper_title": paper_title,
                "paper_doi": paper_doi,
                "row_unit": row_unit,
                "side": side,
                "D": D,
                "N": N,
                "source_file_or_catalog": source_file_or_catalog,
                "source_row_number": source_row_number,
                "paper_level_unit": paper_level_unit,
                "paper_level_note": paper_level_note,
            }
        )

    if PLOT1_PAIR_DETAILS.exists():
        plot1 = pd.read_csv(PLOT1_PAIR_DETAILS)
        side_specs = [
            ("original", "original_title", "original_doi", "D_original", "N_original"),
            ("replication", "replication_title", "replication_doi", "D_replication", "N_replication"),
        ]
        for _, row in plot1.iterrows():
            source_family = safe_text(row.get("source_dataset"))
            source_label = safe_text(row.get("project"))
            citation_key = resolve_any_plot_citation(source_family, source_label, fallback="internalPlot4AllSourceDump")
            for side, title_col, doi_col, d_col, n_col in side_specs:
                paper_key, key_quality = paper_membership_key(
                    plot_prefix=f"plot1_{side}",
                    doi=row.get(doi_col),
                    title=row.get(title_col),
                    fallback=f"{source_family} {source_label} {row.get('pair_id')} {side}",
                )
                add_dot(
                    plot_name="Plot 1",
                    dot_record_id=f"{safe_text(row.get('pair_id'))}::{side}",
                    source_layer="replication_pair",
                    source_family=source_family,
                    source_label=source_label,
                    source_citation_key=citation_key,
                    paper_key=paper_key,
                    paper_key_quality=key_quality,
                    paper_title=row.get(title_col),
                    paper_doi=row.get(doi_col),
                    row_unit=f"replication_pair_{side}_paper_side",
                    side=side,
                    D=row.get(d_col),
                    N=row.get(n_col),
                    source_file_or_catalog=str(PLOT1_PAIR_DETAILS.relative_to(ROOT)),
                    paper_level_unit=True,
                    paper_level_note="Plot 1 dot is a paper side of a replication pair; repeated papers can appear in multiple pair/outcome dots and are collapsed in plot_paper_membership.tsv.",
                )

    if PLOT2_PAPER_DETAILS.exists():
        plot2 = pd.read_csv(PLOT2_PAPER_DETAILS)
        for idx, row in plot2.iterrows():
            source_family = row.get("source_label") or row.get("corpus")
            citation_key = safe_text(row.get("citation_key")) or resolve_any_plot_citation(
                source_family,
                row.get("source_key"),
                row.get("corpus"),
                fallback="internalPlot4AllSourceDump",
            )
            paper_key, key_quality = paper_membership_key(
                plot_prefix="plot2",
                title=row.get("title"),
                fallback=f"{row.get('corpus')} {row.get('paper_id')} {idx}",
            )
            add_dot(
                plot_name="Plot 2",
                dot_record_id=f"plot2::{safe_text(row.get('paper_id')) or idx}",
                source_layer="published_paper_endpoint",
                source_family=source_family,
                source_label=source_family,
                source_citation_key=citation_key,
                paper_key=paper_key,
                paper_key_quality=key_quality,
                paper_title=row.get("title"),
                row_unit=row.get("source_kind"),
                D=row.get("D_paper"),
                N=row.get("N_paper"),
                source_file_or_catalog=str(PLOT2_PAPER_DETAILS.relative_to(ROOT)),
                paper_level_unit=True,
                paper_level_note="Plot 2 dot is the paper-level published endpoint row after the source-specific collapse rule.",
            )

    if PREREG_RESULTS.exists():
        plot3 = pd.read_csv(PREREG_RESULTS)
        for idx, row in plot3.iterrows():
            nct_match = re.search(r"(NCT\d{8}|nct\d{8})", safe_text(row.get("point_id")))
            nct = nct_match.group(1).upper() if nct_match else ""
            paper_key, key_quality = paper_membership_key(
                plot_prefix="plot3",
                nct=nct,
                title=row.get("row_label"),
                fallback=row.get("point_id") or f"{row.get('source_family')} {idx}",
            )
            add_dot(
                plot_name="Plot 3",
                dot_record_id=row.get("point_id") or f"plot3::{idx}",
                source_layer=row.get("source_layer"),
                source_family=row.get("source_family"),
                source_label=row.get("source_label"),
                source_citation_key=safe_text(row.get("citation_key")) or resolve_any_plot_citation(
                    row.get("source_family"),
                    row.get("source_label"),
                    fallback="internalPlot4AllSourceDump",
                ),
                paper_key=paper_key,
                paper_key_quality=key_quality,
                paper_title=row.get("row_label"),
                row_unit=row.get("row_unit"),
                D=row.get("D"),
                N=row.get("N"),
                source_file_or_catalog=row.get("source_file"),
                source_row_number=row.get("source_row_number"),
                paper_level_unit=True,
                paper_level_note="Plot 3 dot is the admitted preregistered paper/project/trial row after source-specific median collapse where required.",
            )

    if ALL_SOURCE_DN_ROWS.exists():
        plot4 = pd.read_csv(ALL_SOURCE_DN_ROWS)
        for idx, row in plot4.iterrows():
            source_family = row.get("source_family")
            citation_key = resolve_any_plot_citation(
                source_family,
                row.get("source_file"),
                row.get("source_layer"),
                fallback="internalPlot4AllSourceDump",
            )
            paper_key, key_quality = paper_membership_key(
                plot_prefix="plot4",
                title=row.get("row_label"),
                fallback=row.get("point_id") or f"{source_family} {idx}",
            )
            row_unit = safe_text(row.get("row_unit"))
            source_layer = safe_text(row.get("source_layer"))
            add_dot(
                plot_name="Plot 4",
                dot_record_id=row.get("point_id") or f"plot4::{idx}",
                source_layer=source_layer,
                source_family=source_family,
                source_label=source_family,
                source_citation_key=citation_key,
                paper_key=paper_key,
                paper_key_quality=key_quality,
                paper_title=row.get("row_label"),
                row_unit=row_unit,
                side=row.get("side"),
                D=row.get("D"),
                N=row.get("N"),
                source_file_or_catalog=row.get("source_file"),
                source_row_number=idx + 2,
                paper_level_unit=row_unit == "paper_id" or source_layer == "published_candidate_paper",
                paper_level_note=(
                    "Plot 4 is a descriptive all-source D/N dump. This row records the plotted dot, "
                    "but Plot 4 is not part of the mutually exclusive paper-ownership contract."
                ),
            )

    dot_membership = pd.DataFrame(dot_rows)
    if dot_membership.empty:
        dot_membership = add_bibtex_mapping_columns(
            dot_membership,
            read_bibtex_keys(PLOT_DOT_REFERENCES_BIB),
            PLOT_DOT_REFERENCES_BIB,
            read_bibtex_rendered_citations(PLOT_DOT_REFERENCES_BIB),
        )
        clean_tsv_frame(dot_membership).to_csv(PLOT_DOT_MEMBERSHIP, sep="\t", index=False)
        pd.DataFrame().to_csv(PLOT_RESULT_PARENT_CHILD, sep="\t", index=False)
        return

    dot_membership.insert(1, "dot_index", np.arange(1, len(dot_membership) + 1))
    dot_membership["citation_key"] = dot_membership.apply(dot_level_citation_key, axis=1)
    duplicated = dot_membership["citation_key"].duplicated(keep=False)
    if duplicated.any():
        dot_membership.loc[duplicated, "citation_key"] = dot_membership.loc[duplicated].apply(
            lambda row: f"{row['citation_key']}_{int(row['dot_index'])}",
            axis=1,
        )
    replace_dot_level_bibtex_entries(dot_membership)
    manuscript_bibtex_keys = read_bibtex_keys()
    dot_bibtex_keys = read_bibtex_keys(PLOT_DOT_REFERENCES_BIB)
    dot_rendered_citations = read_bibtex_rendered_citations(PLOT_DOT_REFERENCES_BIB)
    dot_membership = add_source_citation_mapping_columns(dot_membership, manuscript_bibtex_keys)
    dot_membership = add_bibtex_mapping_columns(dot_membership, dot_bibtex_keys, PLOT_DOT_REFERENCES_BIB, dot_rendered_citations)
    dot_membership["result_level_unit"] = True
    clean_tsv_frame(dot_membership).to_csv(PLOT_DOT_MEMBERSHIP, sep="\t", index=False)

    parent_child = pd.DataFrame(
        {
            "plot_name": dot_membership["plot_name"],
            "parent_collection_key": dot_membership["source_citation_key"].where(
                dot_membership["source_citation_key"].astype(str).str.len() > 0,
                dot_membership["source_family"].map(lambda value: slugify(value, "source_collection")),
            ),
            "parent_collection_label": dot_membership["source_family"],
            "parent_source_label": dot_membership["source_label"],
            "parent_citation_key": dot_membership["source_citation_key"],
            "parent_citation_ref": dot_membership["source_citation_ref"],
            "parent_citation_rendered": dot_membership["source_citation_rendered"],
            "parent_citation_bibtex_status": dot_membership["source_citation_bibtex_status"],
            "child_result_key": dot_membership["citation_key"],
            "child_result_ref": dot_membership["citation_ref"],
            "child_result_rendered": dot_membership["citation_rendered"],
            "child_result_bibtex_status": dot_membership["citation_bibtex_status"],
            "child_paper_key": dot_membership["paper_key"],
            "child_paper_key_quality": dot_membership["paper_key_quality"],
            "child_title": dot_membership["paper_title"],
            "dot_record_id": dot_membership["dot_record_id"],
            "source_layer": dot_membership["source_layer"],
            "row_unit": dot_membership["row_unit"],
            "relationship_type": "parent_collection_contains_child_result_dot",
            "source_file_or_catalog": dot_membership["source_file_or_catalog"],
        }
    )
    clean_tsv_frame(parent_child).to_csv(PLOT_RESULT_PARENT_CHILD, sep="\t", index=False)

    summary_rows: list[dict[str, object]] = []
    numeric = dot_membership.copy()
    numeric["_D_numeric"] = pd.to_numeric(numeric["D"], errors="coerce")
    numeric["_N_numeric"] = pd.to_numeric(numeric["N"], errors="coerce")
    for paper_key, group in numeric.groupby("paper_key", sort=False):
        d_values = group["_D_numeric"].dropna()
        n_values = group["_N_numeric"].dropna()
        child_keys = list(dict.fromkeys(group["citation_key"].dropna().astype(str)))
        parent_keys = list(dict.fromkeys(group["source_citation_key"].dropna().astype(str)))
        summary_rows.append(
            {
                "paper_key": paper_key,
                "paper_key_quality": " | ".join(sorted(set(group["paper_key_quality"].dropna().astype(str)))),
                "paper_title": first_nonempty(group["paper_title"]),
                "paper_doi": first_nonempty(group["paper_doi"]) if "paper_doi" in group.columns else "",
                "plots_present": " | ".join(sorted(set(group["plot_name"].dropna().astype(str)))),
                "plot_count": int(group["plot_name"].nunique()),
                "result_dot_count": int(len(group)),
                "paper_level_dot_count": int(group["paper_level_unit"].astype(str).str.lower().eq("true").sum()),
                "parent_collection_count": int(group["source_citation_key"].nunique()),
                "parent_collection_labels": " | ".join(list(dict.fromkeys(group["source_family"].dropna().astype(str)))[:30]),
                "parent_citation_keys": " | ".join(parent_keys[:60]),
                "parent_citation_key_count": len(parent_keys),
                "child_result_keys": " | ".join(child_keys[:120]),
                "child_result_key_count": len(child_keys),
                "representative_child_result_key": child_keys[0] if child_keys else "",
                "representative_child_result_ref": f"@{child_keys[0]}" if child_keys else "",
                "representative_child_result_rendered": first_nonempty(group["citation_rendered"]) if "citation_rendered" in group.columns else "",
                "D_min": float(d_values.min()) if not d_values.empty else "",
                "D_median": float(d_values.median()) if not d_values.empty else "",
                "D_max": float(d_values.max()) if not d_values.empty else "",
                "N_min": float(n_values.min()) if not n_values.empty else "",
                "N_median": float(n_values.median()) if not n_values.empty else "",
                "N_max": float(n_values.max()) if not n_values.empty else "",
                "row_units": " | ".join(sorted(set(group["row_unit"].dropna().astype(str)))[:20]),
                "source_layers": " | ".join(sorted(set(group["source_layer"].dropna().astype(str)))[:20]),
                "collapse_rule": "Collapsed over all rendered child result dots sharing this normalized paper key; D and N columns report min, median, and max over those child results.",
            }
        )
    paper_summary = pd.DataFrame(summary_rows)
    clean_tsv_frame(paper_summary).to_csv(PLOT_PAPER_SUMMARY, sep="\t", index=False)


def write_plot_membership_audits() -> None:
    """Write explicit cross-plot paper/unit ownership and source-family membership TSVs."""
    rows: list[dict[str, object]] = []
    bibtex_keys = read_bibtex_keys()
    manuscript_rendered_citations = read_bibtex_rendered_citations()
    write_plot_dot_membership_tsv()

    if PLOT1_PAIR_DETAILS.exists():
        plot1 = pd.read_csv(PLOT1_PAIR_DETAILS)
        plot1_catalog_path = DATASET_DERIVED_DIR / "plot1_replication_source_catalog.csv"
        plot1_citation_by_source: dict[tuple[str, str], str] = {}
        plot1_citation_by_label: dict[str, str] = {}
        if plot1_catalog_path.exists():
            plot1_catalog = pd.read_csv(plot1_catalog_path)
            for _, cat_row in plot1_catalog.iterrows():
                citation_key = safe_text(cat_row.get("citation_key"))
                if not citation_key:
                    citation_key = plot1_citation_key(
                        cat_row.get("source_dataset"),
                        cat_row.get("project"),
                        cat_row.get("display_label"),
                        cat_row.get("canonical_source_label"),
                    )
                if not citation_key:
                    continue
                source_dataset = safe_text(cat_row.get("source_dataset"))
                project = safe_text(cat_row.get("project"))
                if source_dataset or project:
                    plot1_citation_by_source[(source_dataset, project)] = citation_key
                for label in [
                    cat_row.get("source_dataset"),
                    cat_row.get("project"),
                    cat_row.get("display_label"),
                    cat_row.get("canonical_source_label"),
                    cat_row.get("canonical_source_id"),
                    cat_row.get("source_key"),
                ]:
                    label_text = safe_text(label)
                    if label_text:
                        plot1_citation_by_label[label_text] = citation_key

        def resolve_plot1_membership_citation(row: pd.Series) -> str:
            source_dataset = safe_text(row.get("source_dataset"))
            project = safe_text(row.get("project"))
            return (
                plot1_citation_by_source.get((source_dataset, project))
                or plot1_citation_by_label.get(source_dataset)
                or plot1_citation_by_label.get(project)
                or plot1_citation_key(source_dataset, project)
            )

        side_specs = [
            ("original", "replicated_original_or_target", "original_title", "original_doi", "D_original", "N_original"),
            ("replication", "replication_attempt", "replication_title", "replication_doi", "D_replication", "N_replication"),
        ]
        for side, role, title_col, doi_col, d_col, n_col in side_specs:
            work = plot1.copy()
            work["_paper_title"] = work.get(title_col, pd.Series("", index=work.index)).fillna("")
            work["_paper_doi"] = work.get(doi_col, pd.Series("", index=work.index)).fillna("")
            key_values = work.apply(
                lambda r: paper_membership_key(
                    plot_prefix=f"plot1_{side}",
                    doi=r.get("_paper_doi"),
                    title=r.get("_paper_title"),
                    fallback=f"{r.get('source_dataset')} {r.get('project')} {r.get('pair_id')} {side}",
                ),
                axis=1,
            )
            work["_paper_key"] = [item[0] for item in key_values]
            work["_key_quality"] = [item[1] for item in key_values]
            group_cols = ["_paper_key", "_key_quality", "source_dataset", "project", "_paper_title", "_paper_doi"]
            for group_key, group in work.groupby(group_cols, dropna=False, sort=False):
                paper_key, key_quality, source_dataset, project, paper_title, paper_doi = group_key
                citation_key = resolve_plot1_membership_citation(group.iloc[0])
                rows.append(
                    {
                        "paper_key": paper_key,
                        "paper_key_quality": key_quality,
                        "plot_owner": "Plot 1",
                        "plot_owner_label": "Replication pairs",
                        "assignment_role": role,
                        "exclusive_primary_plot": True,
                        "source_family": source_dataset,
                        "source_label": project,
                        "citation_key": citation_key,
                        "paper_title": paper_title,
                        "paper_doi": paper_doi,
                        "unit_id": ";".join(group["pair_id"].dropna().astype(str).head(8)),
                        "row_unit": f"replication_pair_{side}_paper_side",
                        "rows_represented": int(len(group)),
                        "D_median": float(pd.to_numeric(group[d_col], errors="coerce").median()),
                        "N_median": float(pd.to_numeric(group[n_col], errors="coerce").median()),
                        "collapse_or_selection_rule": (
                            "Paper-side membership from Plot 1 replication-pair rows; multiple "
                            "outcome/pair rows for the same paper side are summarized here by median D/N."
                        ),
                        "source_file_or_catalog": str(PLOT1_PAIR_DETAILS.relative_to(ROOT)),
                        "example_row_labels": " || ".join(group["outcome"].dropna().astype(str).head(5)),
                    }
                )

    if PLOT2_PAPER_DETAILS.exists():
        plot2 = pd.read_csv(PLOT2_PAPER_DETAILS)
        for row in plot2.itertuples(index=False):
            row_s = pd.Series(row._asdict())
            paper_key, key_quality = paper_membership_key(
                plot_prefix="plot2",
                title=row_s.get("title"),
                fallback=f"{row_s.get('corpus')} {row_s.get('paper_id')}",
            )
            rows.append(
                {
                    "paper_key": paper_key,
                    "paper_key_quality": key_quality,
                    "plot_owner": "Plot 2",
                    "plot_owner_label": "Published non-preregistered endpoints",
                    "assignment_role": "published_journal_article_not_preregistered_layer",
                    "exclusive_primary_plot": True,
                    "source_family": row_s.get("source_label") or row_s.get("corpus"),
                    "source_label": row_s.get("source_label") or row_s.get("corpus"),
                    "citation_key": row_s.get("citation_key"),
                    "paper_title": row_s.get("title"),
                    "paper_doi": "",
                    "unit_id": row_s.get("paper_id"),
                    "row_unit": row_s.get("source_kind"),
                    "rows_represented": count_rows_represented(row_s),
                    "D_median": row_s.get("D_paper"),
                    "N_median": row_s.get("N_paper"),
                    "collapse_or_selection_rule": (
                        "Plot 2 owns published journal/article endpoints that are not treated as "
                        "analytic preregistered confirmatory rows or replication-pair rows."
                    ),
                    "source_file_or_catalog": str(PLOT2_PAPER_DETAILS.relative_to(ROOT)),
                    "example_row_labels": row_s.get("title"),
                }
            )

    if PREREG_RESULTS.exists():
        plot3 = pd.read_csv(PREREG_RESULTS)
        for row in plot3.itertuples(index=False):
            row_s = pd.Series(row._asdict())
            nct_match = re.search(r"(NCT\d{8}|nct\d{8})", safe_text(row_s.get("point_id")))
            nct = nct_match.group(1).upper() if nct_match else ""
            paper_key, key_quality = paper_membership_key(
                plot_prefix="plot3",
                nct=nct,
                title=row_s.get("row_label"),
                fallback=row_s.get("point_id") or row_s.get("source_family"),
            )
            rows.append(
                {
                    "paper_key": paper_key,
                    "paper_key_quality": key_quality,
                    "plot_owner": "Plot 3",
                    "plot_owner_label": "Preregistered confirmatory results",
                    "assignment_role": "preregistered_confirmatory_paper_project_or_trial",
                    "exclusive_primary_plot": True,
                    "source_family": row_s.get("source_family"),
                    "source_label": row_s.get("source_label"),
                    "citation_key": row_s.get("citation_key"),
                    "paper_title": row_s.get("row_label"),
                    "paper_doi": "",
                    "unit_id": row_s.get("point_id"),
                    "row_unit": row_s.get("row_unit"),
                    "rows_represented": count_rows_represented(row_s),
                    "D_median": row_s.get("D"),
                    "N_median": row_s.get("N"),
                    "collapse_or_selection_rule": (
                        "Plot 3 owns preregistered confirmatory papers/projects/trials. "
                        "When a source exposes multiple planned outcomes, arms, sites, or "
                        "archive components for one paper/project, the plotted row is a median "
                        "paper/project dot and the component rows stay in source-specific audits."
                    ),
                    "source_file_or_catalog": row_s.get("source_file"),
                    "example_row_labels": row_s.get("row_label"),
                }
            )

    membership = pd.DataFrame(rows)
    if membership.empty:
        membership = add_bibtex_mapping_columns(membership, bibtex_keys, REFERENCES_BIB, manuscript_rendered_citations)
        clean_tsv_frame(membership).to_csv(PLOT_PAPER_MEMBERSHIP, sep="\t", index=False)
        pd.DataFrame().to_csv(PLOT_PAPER_EXCLUSIVITY_AUDIT, sep="\t", index=False)
    else:
        membership = membership.sort_values(
            ["plot_owner", "source_family", "paper_key", "assignment_role"],
            kind="stable",
        ).reset_index(drop=True)
        membership = add_bibtex_mapping_columns(membership, bibtex_keys, REFERENCES_BIB, manuscript_rendered_citations)
        clean_tsv_frame(membership).to_csv(PLOT_PAPER_MEMBERSHIP, sep="\t", index=False)

        audit_rows: list[dict[str, object]] = []
        for paper_key, group in membership.groupby("paper_key", sort=False):
            plots = sorted(group["plot_owner"].dropna().astype(str).unique())
            key_quality = " | ".join(sorted(group["paper_key_quality"].dropna().astype(str).unique()))
            citation_keys = sorted(set(group["citation_key"].dropna().astype(str).str.strip()) - {""})
            citation_refs = [f"@{key}" for key in citation_keys]
            citation_statuses = sorted(set(group["citation_bibtex_status"].dropna().astype(str)))
            audit_rows.append(
                {
                    "paper_key": paper_key,
                    "paper_key_quality": key_quality,
                    "exclusive_status": "exclusive_to_one_plot"
                    if len(plots) == 1
                    else "cross_plot_overlap_needs_manual_review",
                    "needs_manual_review": bool(len(plots) > 1 or "source_row_fallback" in key_quality),
                    "plots_present": " | ".join(plots),
                    "plot_count": len(plots),
                    "membership_rows": int(len(group)),
                    "total_rows_represented": int(pd.to_numeric(group["rows_represented"], errors="coerce").fillna(0).sum()),
                    "source_families": " | ".join(sorted(group["source_family"].dropna().astype(str).unique())[:12]),
                    "citation_keys": " | ".join(citation_keys),
                    "citation_refs": " | ".join(citation_refs),
                    "citation_bibtex_statuses": " | ".join(citation_statuses),
                    "paper_titles": " | ".join(group["paper_title"].dropna().astype(str).drop_duplicates().head(8)),
                    "paper_dois": " | ".join(group["paper_doi"].dropna().astype(str).drop_duplicates().head(8)),
                    "rule_note": (
                        "Primary paper/unit owner should be exactly one of Plot 1, Plot 2, or Plot 3. "
                        "Corpora may appear in several source catalogs, but this audit checks plotted "
                        "paper/unit ownership where identifiers are available."
                    ),
                }
            )
        exclusivity = pd.DataFrame(audit_rows).sort_values(
            ["exclusive_status", "plot_count", "paper_key"],
            ascending=[True, False, True],
            kind="stable",
        )
        clean_tsv_frame(exclusivity).to_csv(PLOT_PAPER_EXCLUSIVITY_AUDIT, sep="\t", index=False)

    source_rows: list[dict[str, object]] = []

    def add_source_membership(
        path: Path,
        plot_name: str,
        label_col: str,
        status_col: str,
        rows_col: str,
        considered_col: str | None = None,
    ) -> None:
        if not path.exists():
            return
        df = pd.read_csv(path)
        for row in df.itertuples(index=False):
            row_s = pd.Series(row._asdict())
            source_label = safe_text(row_s.get(label_col))
            source_rows.append(
                {
                    "source_key": safe_text(row_s.get("source_key")) or slugify(source_label, "source"),
                    "source_label": source_label,
                    "plot_name": plot_name,
                    "plot_inclusion_status": row_s.get(status_col),
                    "rows_contributed_to_plot": row_s.get(rows_col, 0),
                    "rows_considered_or_available": row_s.get(considered_col, row_s.get(rows_col, 0)) if considered_col else row_s.get(rows_col, 0),
                    "citation_key": row_s.get("citation_key"),
                    "why_or_status": row_s.get("why_in_out") or row_s.get("status_explanation") or row_s.get("why_detail") or row_s.get("inclusion_rule"),
                    "catalog_file": str(path.relative_to(ROOT)),
                }
            )

    add_source_membership(
        DATASET_DERIVED_DIR / "plot1_replication_source_catalog.csv",
        "Plot 1",
        "display_label",
        "plot_inclusion_status",
        "plot_rows_made_in",
        "catalog_file_rows",
    )
    add_source_membership(
        DATASET_DERIVED_DIR / "plot2_published_source_catalog.csv",
        "Plot 2",
        "source_label",
        "plot_inclusion_status",
        "plot_rows_made_in",
        "known_paper_units",
    )
    add_source_membership(
        DATASET_DERIVED_DIR / "plot3_preregistered_source_catalog.csv",
        "Plot 3",
        "source_label",
        "plot_inclusion_status",
        "plot_rows_made_in",
        "rows_considered",
    )
    add_source_membership(
        DATASET_DERIVED_DIR / "plot4_all_source_dump_catalog.csv",
        "Plot 4",
        "source_label",
        "plot_inclusion_status",
        "rows_in_dump",
        "rows_available",
    )
    source_membership = pd.DataFrame(source_rows).sort_values(
        ["source_label", "plot_name"],
        kind="stable",
    )
    source_membership = add_bibtex_mapping_columns(source_membership, bibtex_keys, REFERENCES_BIB, manuscript_rendered_citations)
    clean_tsv_frame(source_membership).to_csv(PLOT_SOURCE_FAMILY_MEMBERSHIP, sep="\t", index=False)

    rules = pd.DataFrame(
        [
            {
                "rule_id": "plot1_owns_replication_pairs",
                "applies_to": "Plot 1",
                "unit_owned": "original and replication paper sides in a replication-pair row",
                "rule": "If a paper appears as an original target or replication attempt in the replication-pair dataset, that paper/unit is owned by Plot 1 for the mutually exclusive main plots.",
                "audit_file": str(PLOT1_PAIR_DETAILS.relative_to(ROOT)),
            },
            {
                "rule_id": "plot2_owns_nonprereg_published_endpoints",
                "applies_to": "Plot 2",
                "unit_owned": "published article/paper endpoint",
                "rule": "If a paper contributes a published journal/article endpoint and is not being treated as a replication-pair side or analytic preregistered confirmatory result, it is owned by Plot 2.",
                "audit_file": str(PLOT2_PAPER_DETAILS.relative_to(ROOT)),
            },
            {
                "rule_id": "plot3_owns_preregistered_confirmatory_units",
                "applies_to": "Plot 3",
                "unit_owned": "preregistered paper, project, trial, or registered-report confirmatory row",
                "rule": "If a paper/project/trial is admitted as a preregistered confirmatory result, it is owned by Plot 3 and should not also appear as a Plot 2 non-preregistered endpoint.",
                "audit_file": str(PREREG_RESULTS.relative_to(ROOT)),
            },
            {
                "rule_id": "within_paper_median_collapse",
                "applies_to": "paper summary tables and Plot 2/3 source collapses",
                "unit_owned": "paper/project with multiple eligible effects",
                "rule": "When a source exposes multiple planned outcomes, treatment arms, sites, claims, or archive components for one paper/project, retain the result-dot children and separately publish a paper-level summary with D/N min, median, and max.",
                "audit_file": str(PLOT_PAPER_SUMMARY.relative_to(ROOT)),
            },
            {
                "rule_id": "parent_child_mapping",
                "applies_to": "all plots",
                "unit_owned": "relationship between collection/corpus source and child result dot",
                "rule": "A parent collection, corpus, or source table can contain many child result dots; the same normalized child paper/result key can appear under more than one parent collection and must be represented by explicit parent-child rows.",
                "audit_file": str(PLOT_RESULT_PARENT_CHILD.relative_to(ROOT)),
            },
            {
                "rule_id": "corpora_can_be_considered_multiple_times",
                "applies_to": "source catalogs",
                "unit_owned": "source family/corpus",
                "rule": "A corpus can appear in more than one source catalog if it was considered for more than one plot. That does not imply the same individual paper/unit is plotted more than once in Plots 1-3.",
                "audit_file": str(PLOT_SOURCE_FAMILY_MEMBERSHIP.relative_to(ROOT)),
            },
            {
                "rule_id": "plot4_is_not_mutually_exclusive",
                "applies_to": "Plot 4",
                "unit_owned": "descriptive all-source D/N point",
                "rule": "Plot 4 is a descriptive all-source dump and is not part of the mutually exclusive Plot 1/2/3 ownership contract.",
                "audit_file": str(ALL_SOURCE_DN_ROWS.relative_to(ROOT)),
            },
        ]
    )
    clean_tsv_frame(rules).to_csv(PLOT_ASSIGNMENT_RULES, sep="\t", index=False)


def write_plot_catalog_status() -> None:
    plot1 = pd.read_csv(DATASET_DERIVED_DIR / "plot1_replication_source_display_table.csv")
    plot2 = pd.read_csv(DATASET_DERIVED_DIR / "plot2_published_source_catalog.csv")
    plot3 = pd.read_csv(DATASET_DERIVED_DIR / "plot3_preregistered_source_catalog.csv")
    plot4 = pd.read_csv(DATASET_DERIVED_DIR / "plot4_all_source_dump_catalog.csv")
    out_csv = DATASET_DERIVED_DIR / "plot_catalog_status.csv"

    rows = [
        {
            "plot_name": "Plot 1 — Replication Pairs",
            "catalog_maturity": "mature_audit",
            "included_sources": int((plot1["plot_inclusion_status"] == "included").sum()),
            "support_only_sources": int((plot1["plot_inclusion_status"] == "support_only").sum()),
            "considered_not_included": int(plot1["plot_inclusion_status"].isin(["integrated_not_plotted", "not_included"]).sum()),
            "main_missing_piece": "Resolve the remaining raw/staged lead families by parser, metric-conversion, access, or native-metric-lane decision.",
        },
        {
            "plot_name": "Plot 2 — Published Paper Endpoints",
            "catalog_maturity": "source_audit_built",
            "included_sources": int((plot2["plot_inclusion_status"] == "included").sum()),
            "support_only_sources": 0,
            "considered_not_included": int((plot2["plot_inclusion_status"] == "not_included").sum()),
            "main_missing_piece": "Add source-specific collapse-rule prose and resolve high-yield excluded candidates by parser, access, or policy decision.",
        },
        {
            "plot_name": "Plot 3 — Preregistered Results",
            "catalog_maturity": "first_figure_built_audit_partial",
            "included_sources": int((plot3["plot_inclusion_status"] == "included").sum()),
            "support_only_sources": 0,
            "considered_not_included": int((plot3["plot_inclusion_status"] == "not_included").sum()),
            "main_missing_piece": "Expand the considered-source sweep and add a formal preregistered-source evidence inventory.",
        },
        {
            "plot_name": "Plot 4 — All-Source D/N Dump",
            "catalog_maturity": "first_pass_surface_map",
            "included_sources": int(plot4["plot_inclusion_status"].isin(["included", "included_sidecar"]).sum()),
            "support_only_sources": int((plot4["plot_inclusion_status"] == "included_sidecar").sum()),
            "considered_not_included": int((plot4["plot_inclusion_status"] == "not_included").sum()),
            "main_missing_piece": "Formalize deduplication rules and a native-metric sidecar policy before using this layer inferentially.",
        },
    ]
    status = pd.DataFrame(rows)
    status.to_csv(out_csv, index=False)
    maturity_display = {
        "mature_audit": "mature audit",
        "audit_partial": "partial audit",
        "source_audit_built": "source audit built",
        "first_figure_built_audit_partial": "first figure / partial audit",
        "first_pass_surface_map": "first-pass surface map",
    }

    lines = [
        "## Plot Catalog Status",
        "",
        f"Machine-readable summary: [plot_catalog_status.csv](../data/derived/effect_inflation_dataset/{out_csv.name})",
        "",
        "Cross-plot ownership ledgers:",
        "",
        f"- [plot_dot_membership.tsv](../data/derived/effect_inflation_dataset/{PLOT_DOT_MEMBERSHIP.name}) records every rendered D/N result dot across Plots 1-4, with its own result-level citation key and rendered citation string in [plot_dot_references.bib](../data/derived/effect_inflation_dataset/{PLOT_DOT_REFERENCES_BIB.name}), plus the parent source citation key/rendered citation in `docs/references.bib`.",
        f"- [plot_result_parent_child.tsv](../data/derived/effect_inflation_dataset/{PLOT_RESULT_PARENT_CHILD.name}) records the parent collection / corpus / plot source to child result-dot mapping, allowing the same child result or paper to appear in more than one parent collection.",
        f"- [plot_paper_summary.tsv](../data/derived/effect_inflation_dataset/{PLOT_PAPER_SUMMARY.name}) collapses child result dots to normalized paper/unit keys and reports result counts plus D/N min, median, and max.",
        f"- [plot_paper_membership.tsv](../data/derived/effect_inflation_dataset/{PLOT_PAPER_MEMBERSHIP.name}) records the paper/unit-level owner for Plots 1-3, including source, citation key, `@key` citation ref, BibTeX presence in `docs/references.bib`, row unit, D/N median, rows represented, and the collapse or selection rule.",
        f"- [plot_paper_exclusivity_audit.tsv](../data/derived/effect_inflation_dataset/{PLOT_PAPER_EXCLUSIVITY_AUDIT.name}) groups the membership ledger by normalized paper/unit key and flags any cross-plot overlaps or weak fallback keys for review; citation keys are carried through for each grouped unit.",
        f"- [plot_source_family_membership.tsv](../data/derived/effect_inflation_dataset/{PLOT_SOURCE_FAMILY_MEMBERSHIP.name}) records which source families/corpora were considered by which plot catalogs, with BibTeX mapping status.",
        f"- [plot_assignment_rules.tsv](../data/derived/effect_inflation_dataset/{PLOT_ASSIGNMENT_RULES.name}) states the current mutually exclusive plot-assignment rules.",
        "",
        markdown_table_block(
            [["Plot", "Catalog maturity", "Included", "Support-only", "Considered out", "Main missing piece"]]
            + [
                [
                    safe_text(row.plot_name),
                    maturity_display.get(safe_text(row.catalog_maturity), safe_text(row.catalog_maturity)),
                    f"{int(row.included_sources):,}",
                    f"{int(row.support_only_sources):,}",
                    f"{int(row.considered_not_included):,}",
                    safe_text(row.main_missing_piece),
                ]
                for row in status.itertuples(index=False)
            ],
            "dataset-table dataset-status-table",
        ),
    ]
    write_qmd_with_table(PLOT_STATUS_QMD, lines)


def write_provenance_schema_pilot_status() -> None:
    """Document the source/result provenance standard and current retrace test."""
    pilot_dir = DATASET_DERIVED_DIR / "schema_pilot"
    pilot_sample = "sample_300"
    summary_path = pilot_dir / f"retrace_summary_{pilot_sample}.tsv"
    initial_summary_path = pilot_dir / f"coding_summary_{pilot_sample}.tsv"
    retrace_path = pilot_dir / f"retrace_source_result_{pilot_sample}.tsv"
    human_check_path = pilot_dir / f"human_check_source_result_{pilot_sample}.tsv"
    events_path = pilot_dir / f"retrace_events_{pilot_sample}.tsv"
    problems_path = pilot_dir / f"retrace_problems_{pilot_sample}.tsv"
    source_result_path = pilot_dir / f"source_result_{pilot_sample}.tsv"
    source_path = pilot_dir / f"source_{pilot_sample}.tsv"
    access_path = pilot_dir / f"source_access_{pilot_sample}.tsv"
    canonical_path = pilot_dir / f"canonical_result_{pilot_sample}.tsv"
    mapping_path = pilot_dir / f"source_source_mapping_{pilot_sample}.tsv"
    codebook_path = DATASET_DERIVED_DIR / "provenance_codebook.tsv"
    data_dictionary_path = DATASET_DERIVED_DIR / "provenance_data_dictionary.tsv"
    template_dir = DATASET_DERIVED_DIR / "schema_templates"

    metric_rows: list[list[str]] = []
    if summary_path.exists():
        summary = pd.read_csv(summary_path, sep="\t")
        wanted = [
            "sample_n",
            "plot_rows_recovered",
            "ultimate_source_paths_existing",
            "rows_with_recovered_effect_text",
            "rows_with_recovered_n_text",
            "rows_with_second_hop_raw_file",
            "rows_with_existing_second_hop_raw_file",
            "source_directness::candidate_child_numeric_row",
            "source_directness::raw_ctgov_registry_row",
            "source_directness::replication_pair_source_row",
            "source_directness::political_science_component_rows",
            "source_directness::plot_row_only",
            "problem::missing_verbatim_effect_text",
            "problem::source_is_derived_not_original_text",
            "source_text_extraction_status::source_cells_recovered",
            "source_text_extraction_status::n_only_recovered",
            "source_text_extraction_status::plot_summary_only",
        ]
        by_metric = {safe_text(row.metric): row.value for row in summary.itertuples(index=False)}
        metric_rows = [[metric, fmt_int(by_metric.get(metric, ""))] for metric in wanted if metric in by_metric]

    lines = [
        "## Provenance Schema And 300-Row Retrace Pilot",
        "",
        "The dataset is moving toward a source-result provenance model. The lowest-level row should be a result asserted by a specific extraction source, not merely a plotted dot. That row must preserve original text, parsed native values, standardized `D`/`N`, source access details, and the transformation explanation.",
        "",
        "The current target tables are:",
        "",
        "- `source.tsv`: citeable or computational source objects such as papers, registries, corpora, repositories, databases, PDFs, and reports.",
        "- `source_access.tsv`: exact retrieval route and local mirror, including direct URL/API URL, repo-relative local path, content type, file size, checksum, retrieval method, and access barrier.",
        "- `source_result.tsv`: one extraction-source assertion of one result, including verbatim effect/N/p/CI/outcome text, parsed native values, standardized values, and transformation notes.",
        "- `canonical_result.tsv`: deduplicated result selected or summarized from one or more source-result rows.",
        "- `source_source_mapping.tsv`: relationships such as corpus contains paper, database reports paper, package supports paper, or registry preregisters trial.",
        "- `extraction_event.tsv`: download, user upload, unzip, PDF/table extraction, code execution, failure, and other work needed to obtain the bytes.",
        "",
        "Synthetic `dot_plot_...` citations are internal audit records for rendered dots. They are kept as `generated_result_citation_*` fields and should not be treated as bibliographic citations for the represented paper, trial, registry record, or dataset.",
        "",
        "The 300-row pilot is a reproducibility stress test: start from sampled plotted rows, retrace them through the plot files, then try to recover the upstream local source rows and literal numeric inputs. Inspect the human-check table first; the initial source-result table is a structural mapping and intentionally keeps labels separate from unrecovered verbatim text.",
        "",
        "Machine-readable pilot files:",
        "",
        f"- Formal table codebook: [provenance_codebook.tsv](../data/derived/effect_inflation_dataset/{codebook_path.name})",
        f"- Field data dictionary: [provenance_data_dictionary.tsv](../data/derived/effect_inflation_dataset/{data_dictionary_path.name})",
        f"- Empty TSV templates: [schema_templates/](../data/derived/effect_inflation_dataset/{template_dir.name}/)",
        f"- Human-check extraction rows: [{human_check_path.name}](../data/derived/effect_inflation_dataset/schema_pilot/{human_check_path.name})",
        f"- Initial source-result coding: [{source_result_path.name}](../data/derived/effect_inflation_dataset/schema_pilot/{source_result_path.name})",
        f"- Source objects: [{source_path.name}](../data/derived/effect_inflation_dataset/schema_pilot/{source_path.name})",
        f"- Access objects: [{access_path.name}](../data/derived/effect_inflation_dataset/schema_pilot/{access_path.name})",
        f"- Canonical results: [{canonical_path.name}](../data/derived/effect_inflation_dataset/schema_pilot/{canonical_path.name})",
        f"- Source mappings: [{mapping_path.name}](../data/derived/effect_inflation_dataset/schema_pilot/{mapping_path.name})",
        f"- Retraced source-result rows: [{retrace_path.name}](../data/derived/effect_inflation_dataset/schema_pilot/{retrace_path.name})",
        f"- Retrace events: [{events_path.name}](../data/derived/effect_inflation_dataset/schema_pilot/{events_path.name})",
        f"- Retrace problems: [{problems_path.name}](../data/derived/effect_inflation_dataset/schema_pilot/{problems_path.name})",
        f"- Initial coding summary: [{initial_summary_path.name}](../data/derived/effect_inflation_dataset/schema_pilot/{initial_summary_path.name})",
        f"- Retrace summary: [{summary_path.name}](../data/derived/effect_inflation_dataset/schema_pilot/{summary_path.name})",
        "",
    ]
    if metric_rows:
        lines.extend(
            [
                markdown_table_block(
                    [["Pilot metric", "Value"]] + metric_rows,
                    "dataset-table provenance-pilot-summary-table",
                ),
                "",
                "The pilot result is mixed in exactly the useful way: the plotted rows are reproducible, but the current pipeline still often reaches a derived numeric row rather than the original human-readable table/API text. Future extractors should write source-result rows at extraction time so the verbatim cells are preserved before collapsing, cleaning, or converting to `D`.",
            ]
        )
    else:
        lines.extend(
            [
                "The pilot output files have not been generated yet. Run `make schema-pilot` to create them.",
            ]
        )
    write_qmd_with_table(PROVENANCE_SCHEMA_QMD, lines)


def write_source_citation_gaps() -> None:
    out_csv = DATASET_DERIVED_DIR / "source_citation_gaps.csv"

    plot1 = pd.read_csv(DATASET_DERIVED_DIR / "plot1_replication_source_catalog.csv")
    plot2 = pd.read_csv(DATASET_DERIVED_DIR / "plot2_published_source_catalog.csv")
    plot3 = pd.read_csv(DATASET_DERIVED_DIR / "plot3_preregistered_source_catalog.csv")

    rows: list[dict[str, object]] = []

    def add_rows(df: pd.DataFrame, plot_name: str, label_col: str, status_col: str) -> None:
        for row in df.itertuples(index=False):
            citation_key = safe_text(getattr(row, "citation_key", ""))
            if citation_key:
                continue
            label = safe_text(getattr(row, label_col, ""))
            inclusion_status = safe_text(getattr(row, status_col, ""))
            source_key = safe_text(getattr(row, "source_key", "")) or safe_text(getattr(row, "canonical_source_label", ""))
            rows.append(
                {
                    "plot_name": plot_name,
                    "display_label": label,
                    "inclusion_status": inclusion_status,
                    "source_key": source_key,
                    "citation_gap_priority": citation_gap_priority(plot_name, inclusion_status, label),
                    "citation_gap_reason": "no_citation_key_mapped",
                }
            )

    add_rows(plot1, "Plot 1", "display_label", "plot_inclusion_status")
    add_rows(plot2, "Plot 2", "display_label", "plot_inclusion_status")
    add_rows(plot3, "Plot 3", "display_label", "plot_inclusion_status")

    gap_columns = [
        "plot_name",
        "display_label",
        "inclusion_status",
        "source_key",
        "citation_gap_priority",
        "citation_gap_reason",
    ]
    gaps = pd.DataFrame(rows, columns=gap_columns)
    priority_order = {"high": 0, "medium": 1, "low": 2}
    if not gaps.empty:
        gaps["_priority_order"] = gaps["citation_gap_priority"].map(priority_order).fillna(99)
        gaps = gaps.sort_values(
            ["_priority_order", "plot_name", "inclusion_status", "display_label"],
            ascending=[True, True, True, True],
        ).drop(columns=["_priority_order"])
    gaps.to_csv(out_csv, index=False)

    if gaps.empty:
        counts = pd.DataFrame(columns=["plot_name", "citation_gap_priority", "uncited_rows"])
    else:
        counts = (
            gaps.groupby(["plot_name", "citation_gap_priority"], dropna=False)
            .size()
            .rename("uncited_rows")
            .reset_index()
            .sort_values(["plot_name", "citation_gap_priority"])
        )
    top = gaps.head(25).copy()

    lines = [
        "## Source Citation Coverage",
        "",
        f"Machine-readable gap log: [source_citation_gaps.csv](../data/derived/effect_inflation_dataset/{out_csv.name})",
        "",
        "Any source row that renders without an inline citation is now tracked explicitly here. This turns missing citations into a concrete cataloging queue rather than a visual annoyance caught in screenshots.",
        "",
        f"Current uncited source rows: `{len(gaps):,}` across Plot 1-3 source catalogs.",
        "",
        "### Uncited-row counts by plot and priority",
        "",
        markdown_table_block(
            [["Plot", "Priority", "Uncited rows"]]
            + [
                [safe_text(row.plot_name), safe_text(row.citation_gap_priority), fmt_int(row.uncited_rows)]
                for row in counts.itertuples(index=False)
            ],
            "dataset-table compact-count-table",
        ),
        "",
        "### Highest-priority uncited rows",
        "",
        markdown_table_block(
            [["Plot", "Source row", "Inclusion status", "Priority", "Gap reason"]]
            + [
                [
                    safe_text(row.plot_name),
                    safe_text(row.display_label),
                    safe_text(row.inclusion_status),
                    safe_text(row.citation_gap_priority),
                    safe_text(row.citation_gap_reason),
                ]
                for row in top.itertuples(index=False)
            ],
            "dataset-table source-gap-table",
        ),
        "",
        "High-priority rows are included source families whose visible labels look like project titles rather than file artifacts. Those are the best low-hanging fruit for tightening citation coverage without changing plot logic.",
    ]
    write_qmd_with_table(SOURCE_CITATION_GAPS_QMD, lines)


def build_body(soup: BeautifulSoup, table_tokens: dict[str, str], figure_specs: dict[str, FigureSpec]) -> None:
    body_html = str(soup.body)
    proc = subprocess.run(
        ["pandoc", "-f", "html", "-t", "markdown-citations", "--wrap=none"],
        input=body_html,
        text=True,
        check=True,
        capture_output=True,
    )
    markdown = normalize_pandoc_markdown(proc.stdout)
    markdown = rewrite_opening_scenario(markdown)
    markdown = replace_figure_refs(markdown)

    for token, fragment in table_tokens.items():
        markdown = markdown.replace(token, fragment)
    for token, spec in figure_specs.items():
        markdown = markdown.replace(token, figure_markdown(spec))

    # Remove any leftover old draft figure token intentionally superseded by the combined figure.
    markdown = markdown.replace("FIGURE_TOKEN_03", "")
    markdown = restructure_sections(markdown)
    repl = replication_stats()
    markdown = rewrite_most_effects_section(markdown, repl)
    markdown = insert_replication_selection_callout(markdown, repl)
    markdown = restructure_post_section4(markdown)
    markdown = re.sub(r"\n{3,}", "\n\n", markdown)
    main_markdown, data_appendices = split_main_and_data_appendices(markdown, figure_specs)
    BODY_QMD.write_text(main_markdown.strip() + "\n", encoding="utf-8")
    DATA_APPENDICES_QMD.write_text(data_appendices.strip() + "\n", encoding="utf-8")
    write_dataset_audit_snapshot()
    write_plot1_criteria_matrix()
    write_plot1_source_catalog()
    write_plot2_source_catalog()
    write_plot2_criteria_matrix()
    write_plot3_source_catalog()
    write_plot3_criteria_matrix()
    write_plot4_source_catalog()
    write_plot_membership_audits()
    write_plot_catalog_status()
    write_provenance_schema_pilot_status()
    write_source_citation_gaps()


def write_citation_audit(in_text: set[str], bibliography: set[str]) -> None:
    all_keys = sorted(in_text | bibliography)
    rows = [
        {
            "citekey": key,
            "in_text": key in in_text,
            "in_bibliography": key in bibliography,
            "status": "ok" if key in in_text and key in bibliography else "orphan_bib" if key in bibliography else "missing_bib",
        }
        for key in all_keys
    ]
    pd.DataFrame(rows).to_csv(CITATION_AUDIT, index=False)
    missing = [row["citekey"] for row in rows if row["status"] == "missing_bib"]
    if missing:
        raise RuntimeError(f"Missing bibliography entries for citekeys: {', '.join(missing[:20])}")


def main() -> None:
    ensure_dirs()
    html = DRAFT_HTML.read_text(encoding="utf-8")
    soup = BeautifulSoup(html, "html.parser")

    expected_figures = len(soup.select("div.figure"))
    expected_tables = len(soup.select("table"))
    expected_refs = len(soup.select("div.csl-entry"))
    if (expected_figures, expected_tables, expected_refs) != (6, 44, 219):
        raise RuntimeError(
            "Draft extraction count changed: "
            f"figures={expected_figures}, tables={expected_tables}, refs={expected_refs}"
        )

    bibliography = extract_bibliography(soup)
    in_text = replace_citation_spans(soup)
    write_citation_audit(in_text, bibliography)

    for selector in ["nav.doc-toc", "header#title-block-header", "div.byline", "script", "style"]:
        for node in soup.select(selector):
            node.decompose()
    refs = soup.select_one("#refs")
    if refs:
        refs.decompose()
    bib_heading = soup.find(id="bibliography")
    if bib_heading:
        bib_heading.decompose()

    repl = replication_stats()
    pub = published_stats()
    update_stale_prose(soup, repl, pub)
    table_tokens = extract_tables(soup)
    replace_old_figure_nodes(soup)
    figure_specs = generate_figures()
    build_body(soup, table_tokens, figure_specs)

    print(
        "Built paper assets: "
        f"{expected_figures} source figures, {expected_tables} tables, {expected_refs} references"
    )


if __name__ == "__main__":
    main()
