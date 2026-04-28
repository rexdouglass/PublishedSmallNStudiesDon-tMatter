#!/usr/bin/env python3
"""Build Quarto-ready paper assets from the Claude HTML draft and local data.

This script is deliberately extraction-backed: the old HTML draft is treated as
the seed document, while current derived datasets provide the upgraded figures
and synced figure captions.
"""

from __future__ import annotations

import ast
import csv
import math
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

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
GENERATED = DOCS / "_generated"
FIG_DIR = GENERATED / "figures"
TABLE_DIR = ROOT / "data" / "derived" / "paper_tables"
TABLE_FRAGMENT_DIR = GENERATED / "tables"
DATASET_DERIVED_DIR = ROOT / "data" / "derived" / "effect_inflation_dataset"
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
SOURCE_CITATION_GAPS_QMD = GENERATED / "source_citation_gaps.qmd"
CITATION_AUDIT = GENERATED / "citation_audit.csv"
TABLE_MANIFEST = TABLE_DIR / "table_manifest.csv"
INTRO_EXAMPLES = ROOT / "data" / "derived" / "paper_assets" / "figure1_intro_examples.csv"

REPLICATION_FIG = ROOT / "reports" / "corpus_candidates" / "figure2_replication_pairs_draft.png"
REPLICATION_CSV = ROOT / "data" / "derived" / "replication_pairs" / "replication_pairs_figure2_rule_subset.csv"
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
PREREG_SENSITIVITY_RESULTS = DATASET_DERIVED_DIR / "plot3_preregistered_sensitivity_sidecar_rows.csv"
PREREG_CTGOV_PRIMARY_RANDOMIZED_RESULTS = DATASET_DERIVED_DIR / "plot3_ctgov_phase2plus_primary_randomized_sidecar_rows.csv"
ALL_SOURCE_DN_ROWS = DATASET_DERIVED_DIR / "plot4_all_source_dn_rows.csv"
PLOT1_PAIR_DETAILS = DATASET_DERIVED_DIR / "plot1_replication_pair_details.csv"
PLOT2_PAPER_DETAILS = DATASET_DERIVED_DIR / "plot2_published_paper_details.csv"
PREREG_FIG = FIG_DIR / "plot3_preregistered_d_vs_n.png"
PREREG_SENSITIVITY_FIG = FIG_DIR / "plot3_preregistered_sensitivity_sidecar.png"
PREREG_CTGOV_PRIMARY_RANDOMIZED_FIG = FIG_DIR / "plot3_ctgov_phase2plus_primary_randomized_sidecar.png"
ALL_SOURCE_FIG = FIG_DIR / "plot4_all_source_dn_dump.png"

Z_05 = 1.959963984540054


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
    "Schäfer/Schwarz 2019 preregistered psychology articles": "schaefer2019meaningfulness",
    "Schäfer/Schwarz 2019 non-preregistered psychology articles": "schaefer2019meaningfulness",
    "SCORE/COS preregistration-indicated original papers": "tyner2026",
    "Protzko et al. 2024 High-Replicability Research project": "protzko2024highrep",
    "AACT x PubMed registered primary outcomes": "du2024",
    "ClinicalTrials.gov registry-result D/N comparator": "du2024",
    "CliniFact published trial primary-outcome rows": "zhang2025clinifact",
    "Brodeur et al. 2024 preregistered/PAP economics table tests": "brodeur2020",
    "Transparent Psi Project / Bem preregistered replication": "kekecs2023tpp",
    "ManyBabies 3 rule-learning registered-report materials": "manyBabies3Osf",
    "ERN/Pe RRR OpenNeuro and OSF analysis hubs": "ernPeRrrOpenNeuro",
    "Linden et al. 2024 focal/random psychology sample": "linden2024publicationBiasPsychology",
    "ManyClasses 2 classroom registered-report materials": "manyClasses2Osf",
    "Communication privacy preregistered replication corpus": "masur2025privacy",
    "Retrieval-extinction rats preregistered replication": "luyten2017retrievalExtinction",
}

PLOT3_DISPLAY_LABELS = {
    "Scheel et al. 2021 preregistered-hypotheses corpus": "Registered Reports preregistered-hypotheses corpus",
    "Dorison et al. 2022 PSA-CR001 pooled preregistered rows": "PSA-CR001 pooled preregistered rows",
    "Schäfer/Schwarz 2019 preregistered psychology articles": "Schäfer/Schwarz preregistered psychology articles",
    "Schäfer/Schwarz 2019 non-preregistered psychology articles": "Schäfer/Schwarz non-preregistered comparator",
    "SCORE/COS preregistration-indicated original papers": "SCORE/COS preregistration-indicated papers",
    "Protzko et al. 2024 High-Replicability Research project": "High-Replicability Research project",
    "AACT x PubMed registered primary outcomes": "AACT x PubMed registered primary outcomes",
    "ClinicalTrials.gov registry-result D/N comparator": "ClinicalTrials.gov registry-result D/N comparator",
    "CliniFact published trial primary-outcome rows": "CliniFact published trial primary-outcome rows",
    "Brodeur et al. 2024 preregistered/PAP economics table tests": "Brodeur preregistered/PAP table tests",
    "Registered Replication Reports per-lab rows": "Registered Replication Reports per-lab rows",
    "Registered Replication Reports Plot 1 pair rows": "Registered Replication Reports Plot 1 pair rows",
    "Many Labs 1-5 project-level replication rows": "Many Labs 1-5 project-level replication rows",
    "Psychological Science Accelerator replication-pair rows": "PSA replication-pair rows",
    "Transparent Psi Project / Bem preregistered replication": "Transparent Psi Project / Bem row",
    "ManyBabies 3 rule-learning registered-report materials": "ManyBabies 3 registered-report materials",
    "ERN/Pe RRR OpenNeuro and OSF analysis hubs": "ERN/Pe RRR OpenNeuro/OSF hubs",
    "Self-control fMRI preregistered replication materials": "Self-control fMRI preregistered materials",
    "Twomey et al. 2021 kinesiology article audit": "Twomey kinesiology article audit",
    "Linden et al. 2024 focal/random psychology sample": "Linden focal/random psychology sample",
    "Nordic trial registration-publication linkage database": "Nordic trial registration-publication linkage",
    "FORRT FReD / Replication Database": "FORRT FReD / Replication Database",
    "FReD archived workflow workbook / OSF Registries queue": "FReD archived workflow rescue queue",
    "ManyClasses 2 classroom registered-report materials": "ManyClasses 2 classroom materials",
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


def fmt_int(value: object) -> str:
    if pd.isna(value) or value == "":
        return ""
    return f"{int(value):,}"


def fmt_number(value: object, digits: int = 2) -> str:
    if pd.isna(value) or value == "":
        return ""
    return f"{float(value):,.{digits}f}"


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


def replication_stats() -> dict[str, float | int]:
    df = pd.read_csv(REPLICATION_CSV)
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


def normalize_preregistered_results() -> pd.DataFrame:
    table40 = pd.read_csv(PREREG_TABLE_40)
    table41 = pd.read_csv(PREREG_TABLE_41)
    rows: list[dict[str, object]] = []

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

    df = pd.DataFrame(rows)
    df["D"] = numeric_series(df["D"]).abs()
    df["N"] = numeric_series(df["N"])
    df = df[(df["D"] > 0) & (df["N"] > 0)].copy()
    df["log10_N"] = np.log10(df["N"])
    df["log10_D"] = np.log10(df["D"])
    df["two_sample_p05_boundary_D"] = 2 * Z_05 / np.sqrt(df["N"])
    df["above_two_sample_p05_curve"] = df["D"] >= df["two_sample_p05_boundary_D"]
    df.to_csv(PREREG_RESULTS, index=False)
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
    x_max_data = float(df["N"].max())
    y_min_data = float(df["D"].min())
    y_max_data = float(df["D"].max())
    x_min = 10.0 if x_min_data >= 10 else 1.0
    x_max = min(10 ** math.ceil(math.log10(x_max_data * 1.15)), x_cap)
    y_min = min(0.02, 10 ** math.floor(math.log10(max(y_min_data * 0.8, 1e-8))))
    y_min = max(y_min, 1e-5)
    y_max = max(5.0, 10 ** math.ceil(math.log10(y_max_data * 1.1)))
    y_max = min(y_max, 20.0)
    return x_min, x_max, y_min, y_max


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
        "Scheel et al. 2021 preregistered-hypotheses corpus": "#2a4d7a",
        "Dorison et al. 2022 PSA-CR001 pooled preregistered rows": "#0b6e5f",
        "Schäfer/Schwarz 2019 preregistered psychology articles": "#7a4d9b",
        "SCORE/COS preregistration-indicated original papers": "#555555",
    }
    markers = {
        "Scheel et al. 2021 preregistered-hypotheses corpus": "o",
        "Dorison et al. 2022 PSA-CR001 pooled preregistered rows": "s",
        "Schäfer/Schwarz 2019 preregistered psychology articles": "^",
        "SCORE/COS preregistration-indicated original papers": "o",
    }

    x_min_plot = 10
    x_max_plot = max(100000, float(df["N"].max()) * 1.15)
    y_min_plot = 0.005
    y_max_plot = 3.0
    xs = np.logspace(np.log10(x_min_plot), np.log10(x_max_plot), 400)

    fig = plt.figure(figsize=(10.5, 9.3), dpi=180)
    gs = fig.add_gridspec(2, 1, height_ratios=[5.1, 1.55], hspace=0.34)
    ax = fig.add_subplot(gs[0, 0])
    ax_hist = fig.add_subplot(gs[1, 0])

    for source_family, group in df.groupby("source_family", sort=False):
        color = colors.get(source_family, "#444444")
        display = safe_text(group["source_label"].iloc[0]) or source_family
        ax.scatter(
            group["N"],
            group["D"],
            s=34,
            marker=markers.get(source_family, "o"),
            color=color,
            edgecolors="none",
            alpha=0.78,
            rasterized=True,
            zorder=3,
        )

    median_d = float(df["D"].median())
    median_n = float(df["N"].median())
    z10 = 1.6448536269514722
    pct_above_p10 = 100 * float((df["D"] >= (2 * z10 / np.sqrt(df["N"]))).mean())

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

    for row in medians.itertuples(index=False):
        color = colors.get(row.source_family, "#444444")
        marker = markers.get(row.source_family, "o")
        ax.scatter(
            row.median_N,
            row.median_D,
            s=120,
            marker=marker,
            facecolors="white",
            edgecolors=color,
            linewidths=1.8,
            zorder=5,
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
            linewidth=2.7,
            alpha=1.0,
            zorder=11,
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
            zorder=12,
        )

    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlim(x_min_plot, x_max_plot)
    ax.set_ylim(y_min_plot, y_max_plot)
    x_ticks = [10, 100, 1_000, 10_000, 100_000]
    y_ticks = [0.005, 0.01, 0.02, 0.05, 0.1, 0.2, 0.5, 1, 2]
    ax.xaxis.set_major_locator(FixedLocator(x_ticks))
    ax.xaxis.set_major_formatter(FixedFormatter(["10", "100", "1k", "10k", "100k"]))
    ax.xaxis.set_minor_formatter(NullFormatter())
    ax.yaxis.set_major_locator(FixedLocator(y_ticks))
    ax.yaxis.set_major_formatter(FixedFormatter(["0.005", "0.01", "0.02", "0.05", "0.1", "0.2", "0.5", "1", "2"]))
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
            f"{len(df):,} rows from {df['source_family'].nunique():,} source families | "
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
        color = colors.get(row.source_family, "#444444")
        marker = markers.get(row.source_family, "o")
        legend_handles.append(
            Line2D(
                [0],
                [0],
                marker=marker,
                color="none",
                markerfacecolor=color,
                markeredgecolor="none",
                markersize=8,
                alpha=0.82,
                label=f"{safe_text(row.source_label)} (n={fmt_int(row.n_rows)})",
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
            label="Hollow marker = source median",
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
            "the lower panel shows the same point estimates on a linear D axis."
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
        "n_sources": int(df["source_family"].nunique()),
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

    x_min, x_max, y_min, y_max = sidecar_log_axis_bounds(df, x_cap=10_000_000.0)
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
    for source_family, group in df.groupby("source_family", sort=False):
        color = colors.get(source_family, "#444444")
        ax.scatter(
            group["N"],
            group["D"],
            s=10 if "ClinicalTrials.gov" in source_family else 13,
            marker=markers.get(source_family, "o"),
            color=color,
            edgecolors="none",
            alpha=0.22 if "ClinicalTrials.gov" in source_family else 0.30,
            rasterized=True,
            zorder=3,
        )

    for row in medians.itertuples(index=False):
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
            "the lower panel shows the same comparator estimates on a linear D axis."
        ),
        transform=ax.transAxes,
        fontsize=8.8,
        color="#333333",
        ha="left",
    )

    linear_d_max = 3.0
    linear_bin_width = 0.1
    linear_bins = np.arange(0, linear_d_max + linear_bin_width, linear_bin_width)
    for source_family, group in df.groupby("source_family", sort=False):
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

    x_min, x_max, y_min, y_max = sidecar_log_axis_bounds(df, x_cap=100_000.0)
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
            "the lower panel shows the same comparator estimates on a linear D axis."
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

    for layer, (label, color, size, alpha) in layer_specs.items():
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
            zorder=2 if "published" in layer else 3,
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
                "confirmed_fields": f"Known: 71 preregistered hypothesis rows, {fmt_int(len(table40))} D/N-ready rows. Confirmed: analytic preregistration: yes (71); support status: yes ({fmt_int(len(table40))}); journal provenance: yes ({fmt_int(len(table40))}); paper D/N: yes ({fmt_int(len(table40))}).",
                "backing_file": str(PREREG_TABLE_40.relative_to(ROOT)),
                "rows_considered": 71,
                "rows_preregistered_equivalent": 71,
                "rows_with_public_local_backing": 71,
                "rows_with_extractable_DN": len(table40),
                "rows_with_non_retracted_source": 71,
                "rows_contributed": len(table40),
                "rows_left_out_within_source": 71 - len(table40),
                "why": "base preregistered-results corpus already on disk; 32 hypotheses have extractable D/N rows and 39 do not",
                "why_in_out": f"Included: {fmt_int(len(table40))} hypotheses enter. The remaining {fmt_int(71 - len(table40))} Scheel rows are real preregistered hypotheses but do not have local D/N rows in the current table.",
            },
            {
                "plot_name": "Plot 3",
                "plot_inclusion_status": "included",
                "source_label": "Dorison et al. 2022 PSA-CR001 pooled preregistered rows",
                "corpus_what_it_is": "Pooled primary preregistered PSA-CR001 confirmatory rows.",
                "what_it_is_why_possible_candidate": "PSA-CR001 was a preregistered 52-country COVID-19 framing project. Possible Plot 3 candidate because four primary confirmatory outcomes can be represented as pooled D/N rows rather than as nested country cells.",
                "confirmed_fields": f"Known: {fmt_int(len(table41))} pooled primary outcomes. Confirmed: analytic preregistration: yes ({fmt_int(len(table41))}); support status: yes ({fmt_int(len(table41))}); pooled N: yes ({fmt_int(len(table41))}); pooled D: yes ({fmt_int(len(table41))}).",
                "backing_file": str(PREREG_TABLE_41.relative_to(ROOT)),
                "rows_considered": len(table41),
                "rows_preregistered_equivalent": len(table41),
                "rows_with_public_local_backing": len(table41),
                "rows_with_extractable_DN": len(table41),
                "rows_with_non_retracted_source": len(table41),
                "rows_contributed": len(table41),
                "rows_left_out_within_source": 0,
                "why": "adds pooled confirmatory preregistered rows that belong in the same comparison layer",
                "why_in_out": "Included: the four primary PSA-CR001 confirmatory outcomes enter as pooled rows. Country-level cells stay collapsed here to avoid nested non-independent Plot 3 rows.",
            },
            {
                "plot_name": "Plot 3",
                "plot_inclusion_status": "included",
                "source_label": "SCORE/COS preregistration-indicated original papers",
                "corpus_what_it_is": "SCORE/COS sampled social-behavioral papers whose original paper IDs are flagged as preregistration-indicated.",
                "what_it_is_why_possible_candidate": "The SCORE/COS claim corpus was rechecked because its OSF manifest includes `orig_prereg-indicated.csv`. That file flags original papers with apparent preregistration, and the existing SCORE D/N parser already reconstructs paper-level D/N for a subset of those papers.",
                "confirmed_fields": f"Known: {fmt_int(score_prereg_count)} unique SCORE paper IDs marked `prereg=True`, {fmt_int(len(score_prereg))} deduplicated paper-level D/N rows. Confirmed: paper-level preregistration indication: yes ({fmt_int(score_prereg_count)}); paper grouping: yes; D/N: yes ({fmt_int(len(score_prereg))}); claim-specific preregistration mapping: no; support status: not coded.",
                "backing_file": f"{PUBLISHED_PAPERS.relative_to(ROOT)}; {SCORE_ORIG_PREREG.relative_to(ROOT)}",
                "rows_considered": score_prereg_count,
                "rows_preregistered_equivalent": score_prereg_count,
                "rows_with_public_local_backing": score_prereg_count,
                "rows_with_extractable_DN": len(score_prereg),
                "rows_with_non_retracted_source": score_prereg_count,
                "rows_contributed": len(score_prereg),
                "rows_left_out_within_source": score_prereg_left_out,
                "why": "included as a paper-level preregistration-indicated SCORE subset; journal TOP-factor preregistration-policy scores are deliberately ignored",
                "why_in_out": f"Included: {fmt_int(len(score_prereg))} paper-level rows enter. The remaining {fmt_int(score_prereg_left_out)} preregistration-indicated SCORE paper IDs do not currently have a deduplicated positive D/N row in the local SCORE candidate build. Caveat: the available flag is paper-level, so the table does not assert that every extracted claim was the exact preregistered primary hypothesis.",
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
                "plot_inclusion_status": "not_included",
                "source_label": "ClinicalTrials.gov registry-result D/N comparator",
                "corpus_what_it_is": "Finer-grained ClinicalTrials.gov results extraction with D/N proxies for registry outcome rows.",
                "what_it_is_why_possible_candidate": "ClinicalTrials.gov results were rechecked because they are the largest local preregistered-like bucket: trial records have registered outcomes and the parser recovers N plus p-value/effect-size proxies. A cleaner sub-sidecar now isolates phase-2+ randomized interventional trials with exactly one locally eligible primary two-group row.",
                "confirmed_fields": f"Known locally: broad sidecar has {fmt_int(len(ctgov_registry))} trial-median registry rows and {fmt_int(ctgov_dn_rows)} D/N-ready rows. Cleaner local sub-sidecar has {fmt_int(ctgov_clean_rows)} phase-2+ one-primary randomized rows. Confirmed: outcome type: yes in raw file; study type/allocation/phase: yes in raw file; N/effect proxy: yes; direct arm-level D: no; protocol/SAP timing audit: no.",
                "backing_file": str(PUBLISHED_PAPERS.relative_to(ROOT)),
                "rows_considered": len(ctgov_registry),
                "rows_preregistered_equivalent": ctgov_clean_rows,
                "rows_with_public_local_backing": len(ctgov_registry),
                "rows_with_extractable_DN": ctgov_dn_rows,
                "rows_with_non_retracted_source": len(ctgov_registry),
                "rows_contributed": 0,
                "rows_left_out_within_source": len(ctgov_registry),
                "why": "not included because this is registry-result evidence, not the current standalone published/preregistered confirmatory-result layer",
                "why_in_out": f"Not included in strict Plot 3: {fmt_int(ctgov_dn_rows)} broad D/N rows and {fmt_int(ctgov_clean_rows)} cleaner one-primary randomized rows are real and local, but the current D is a registry p-value/enrollment proxy and no protocol/SAP pre-measurement audit proves exact analytic prespecification. The cleaner subset remains a named sensitivity sidecar.",
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
                "plot_inclusion_status": "not_included",
                "source_label": "Brodeur et al. 2024 preregistered/PAP economics table tests",
                "corpus_what_it_is": "Top-journal economics table-test extraction with row-level preregistration, pre-analysis-plan, and PAP-power flags in the local raw notes.",
                "what_it_is_why_possible_candidate": "The Brodeur economics corpus was rechecked because it is the other local source that produces thousands of preregistration-flagged D/N rows: many extracted table tests are from studies marked as preregistered or having a pre-analysis plan.",
                "confirmed_fields": f"Known locally: {fmt_int(brodeur_rows)} extracted economics test rows, {fmt_int(brodeur_flagged_rows)} D/N-ready rows with preregistration/PAP/PAP-power flags, collapsing to {fmt_int(brodeur_flagged_papers)} papers. Confirmed: preregistration flag rows: {fmt_int(brodeur_prereg_rows)}; pre-analysis-plan flag rows: {fmt_int(brodeur_pap_rows)}; PAP-power flag rows: {fmt_int(brodeur_pap_power_rows)}; D/N: yes; focal/main-result selector: no; exact test-level PAP mapping: no.",
                "backing_file": str(CANDIDATE_ROWS.relative_to(ROOT)) if CANDIDATE_ROWS.exists() else "data/derived/corpus_candidates/candidate_d_n_rows.csv.gz",
                "rows_considered": brodeur_rows,
                "rows_preregistered_equivalent": brodeur_flagged_rows,
                "rows_with_public_local_backing": brodeur_rows,
                "rows_with_extractable_DN": brodeur_flagged_rows,
                "rows_with_non_retracted_source": brodeur_rows,
                "rows_contributed": 0,
                "rows_left_out_within_source": brodeur_flagged_rows,
                "why": "not included because these are preregistration/PAP-flagged extracted table tests without a paper-level focal or main-result selector",
                "why_in_out": f"Not included: the preregistration/PAP flags are real and account for {fmt_int(brodeur_flagged_rows)} D/N-ready extracted table-test rows, but the flags are not enough to prove that each coefficient/test is the exact prespecified confirmatory hypothesis. No focal/main-result selector is available, so this remains a sensitivity lane rather than strict Plot 3 evidence.",
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
                "what_it_is_why_possible_candidate": "ManyClasses 2 was rechecked because it is a coordinated classroom project with public OSF materials and a staged worklist estimate of multiple classroom result rows.",
                "confirmed_fields": f"Known locally: {fmt_int(staged_counts['manyclasses_2__stage.csv']['expected_rows'])} expected rows, {fmt_int(staged_counts['manyclasses_2__stage.csv']['downloaded_file_count'])} downloaded files. Confirmed: public OSF payload: yes; Terracotta/classroom data and scripts: yes; compact D/N confirmatory result table: no.",
                "backing_file": str(staged_counts["manyclasses_2__stage.csv"]["path"].relative_to(ROOT)),
                "rows_considered": staged_counts["manyclasses_2__stage.csv"]["expected_rows"],
                "rows_preregistered_equivalent": staged_counts["manyclasses_2__stage.csv"]["expected_rows"],
                "rows_with_public_local_backing": staged_counts["manyclasses_2__stage.csv"]["expected_rows"],
                "rows_with_extractable_DN": 0,
                "rows_with_non_retracted_source": staged_counts["manyclasses_2__stage.csv"]["expected_rows"],
                "rows_contributed": 0,
                "rows_left_out_within_source": staged_counts["manyclasses_2__stage.csv"]["expected_rows"],
                "why": "not included because the local payload is a classroom intervention analysis source, not a D/N-ready confirmatory result table",
                "why_in_out": "Not included: source files are local, but they require a separate education/classroom parser and metric policy before any Plot 3 points can be admitted.",
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
    plot3["display_label"] = plot3["source_label"].map(plot3_display_label)
    plot3["source_key"] = plot3.apply(
        lambda r: safe_text(r.get("source_label")) and slugify(safe_text(r.get("source_label")), "plot3_source"),
        axis=1,
    )
    plot3["citation_key"] = plot3["source_label"].map(PLOT3_CITATION_KEYS).fillna("")
    plot3["plot_rows_made_in"] = np.where(plot3["plot_inclusion_status"] == "included", plot3["rows_contributed"], 0)
    plot3 = plot3.sort_values(["plot_rows_made_in", "source_label"], ascending=[False, True])
    plot3.to_csv(out_csv, index=False)

    prereg_details = normalize_preregistered_results()
    included = plot3.loc[plot3["plot_inclusion_status"] == "included"].copy()
    excluded = plot3.loc[plot3["plot_inclusion_status"] == "not_included"].copy()
    corpus_rows = pd.concat([included, excluded], ignore_index=True)
    corpus_rows = corpus_rows.sort_values(["plot_rows_made_in", "source_label"], ascending=[False, True])

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
        f"Machine-readable result-level file: [plot3_preregistered_results.csv](../data/derived/effect_inflation_dataset/{PREREG_RESULTS.name})",
        "",
        f"The specific-observation layer has `{len(prereg_details):,}` plotted preregistered result rows. It records source citation, result label, journal, `D`, `N`, and the source row number. Support calls are retained in the CSV as metadata but are not used for admission or visual encoding, because they mostly track the preregistered decision rule rather than a distinct effect-size concept.",
        "",
        markdown_table_block(
            [["Source", "Specific paper/result", "Journal", "D/N"]]
            + [
                [
                    source_key_badge(row.source_label, row.source_family, row.citation_key),
                    safe_text(row.row_label)[:90],
                    safe_text(row.journal),
                    f"{fmt_number(row.D)} / {fmt_int(row.N)}",
                ]
                for row in prereg_details.sort_values(["source_family", "source_row_number"]).itertuples(index=False)
            ],
            "dataset-table specific-observation-table preregistered-observation-table",
        ),
        "",
        "### What Is Still Missing",
        "",
        "- The included core now combines Registered Reports, PSA-CR001 pooled preregistered outcomes, and the Schäfer/Schwarz preregistered key-effect sample.",
        "- The expanded considered-but-not-included list now names the major local preregistered-like sidecars separately: Many Labs, RRR pair rows, PSA replication rows, Transparent Psi, ManyBabies 3, ManyClasses 2, ERN/Pe, self-control fMRI, Twomey, Linden, Protzko, AACT/ClinicalTrials.gov, CliniFact, Brodeur preregistered/PAP economics table tests, Nordic trial reporting, FReD, communication privacy, and retrieval-extinction rats.",
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
        "These counts separate discovery from admission. `Extractable D/N rows` means the project has local numeric D/N rows somewhere for that source; `Currently included` means those rows also survive the analytic-preregistration, non-retraction, independence/deduplication, and current-layer policy gates.",
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
                ["Why in/out", "Final current gate call: included, excluded by analytic-preregistration, excluded by retraction, excluded as duplicate/nested evidence, or blocked by missing local row table."],
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
    write_plot_catalog_status()
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
