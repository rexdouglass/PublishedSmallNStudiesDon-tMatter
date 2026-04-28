#!/usr/bin/env python3
"""Build BibTeX bibliographies for the Quarto paper and statistic corpora.

The paper started life as a rendered HTML draft, so the first pass bibliography
was reverse-engineered from formatted reference text. This script makes that
conversion explicit, writes BibTeX for Quarto, and creates a larger corpus
bibliography from local paper/statistic metadata.

Network lookups are optional. By default, the script is reproducible from local
data plus cached Crossref responses. Use --refresh-metadata to query Crossref
for the 219 paper references and improve author/journal/DOI fields.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import time
from functools import lru_cache
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from pathlib import Path
from typing import Iterable

import pandas as pd
import requests
from bs4 import BeautifulSoup


ROOT = Path(__file__).resolve().parents[1]
DRAFT_HTML = ROOT / "docs" / "nightmare-hellscape (3).html"
DOCS = ROOT / "docs"
PAPER_BIB = DOCS / "references.bib"
PAPER_CSL_JSON = DOCS / "references.csl.json"

BIB_DIR = ROOT / "data" / "derived" / "bibliography"
PAPER_REFERENCES_CSV = BIB_DIR / "paper_references.csv"
CORPUS_REFERENCES_CSV = BIB_DIR / "corpus_papers.csv"
CORPUS_BIB = BIB_DIR / "corpus_papers.bib"
CORPUS_SOURCE_AUDIT = BIB_DIR / "corpus_bibliography_sources.csv"
CORPUS_COVERAGE_AUDIT = BIB_DIR / "corpus_bibliography_coverage.csv"

CACHE_DIR = ROOT / "data" / "cache" / "bibliography"
CROSSREF_DIR = CACHE_DIR / "crossref"
EUROPEPMC_DIR = CACHE_DIR / "europepmc"

PUBLISHED_PAPERS = ROOT / "data" / "derived" / "corpus_candidates" / "candidate_d_n_papers.csv"
CANDIDATE_STUDIES = ROOT / "data" / "derived" / "corpus_candidates" / "candidate_d_n_studies.csv"
PEER_REVIEWED_SOURCE_LIST = ROOT / "data" / "derived" / "corpus_candidates" / "current_peer_reviewed_journal_d_n_list.csv"
REPLICATION_PAIRS = ROOT / "data" / "derived" / "replication_pairs" / "replication_pairs_figure2_draft.csv"
REPLICATION_ALL = ROOT / "data" / "derived" / "replication_pairs" / "replication_pairs_all_on_hand.csv"
PACKAGE_REFERENCE_SOURCES = ROOT / "data" / "derived" / "package_reference_sources.csv"
CLINIFACT_FULLTEXT = ROOT / "data" / "derived" / "publication_bias_direct" / "clinifact_pmc_fulltext_extract.csv"
FRED_FLORA = ROOT / "data" / "raw" / "corpus_candidates" / "fred" / "flora.csv"
SCORE_METADATA = ROOT / "data" / "raw" / "corpus_candidates" / "score" / "paper_metadata.csv"
STATCHECK_PAPERS = ROOT / "data" / "interim" / "published_papers" / "statcheck_published_papers.csv"
STATCHECK_RAW = ROOT / "data" / "raw" / "published_papers" / "statcheck_150211FullFile_AllStatcheckData_Automatic1Tail.csv"
STATCHECK_HARTGERINK_DATASET = CACHE_DIR / "statcheck_dataset.tab"
STATCHECK_EXACT_MATCHES = BIB_DIR / "psychology_statcheck_exact_matches.csv"
STATCHECK_HARTGERINK_URL = "https://ssh.datastations.nl/api/access/datafile/177131"

DOI_RE = re.compile(r"(?i)\b(?:doi:\s*|https?://(?:dx\.)?doi\.org/)?(10\.\d{4,9}/[-._;()/:A-Z0-9]+)")
YEAR_RE = re.compile(r"\b(18|19|20)\d{2}[a-z]?\b")
WHITESPACE_RE = re.compile(r"\s+")
METABUS_ARTICLE_ID_RE = re.compile(r"\b(?P<journal>JAP|PPsych)-(?P<volume>\d+)-(?P<issue>\d+)-(?P<page>\d+)\b")
IDENTITY_INDEX: dict[int, dict[str, str]] = {}
TITLE_STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "by",
    "for",
    "from",
    "in",
    "is",
    "of",
    "on",
    "or",
    "the",
    "to",
    "with",
}
METABUS_JOURNALS = {
    "JAP": "Journal of Applied Psychology",
    "PPsych": "Personnel Psychology",
}
STATCHECK_JOURNALS = {
    "DP": "Developmental Psychology",
    "FP": "Frontiers in Psychology",
    "JAP": "Journal of Applied Psychology",
    "JCCP": "Journal of Consulting and Clinical Psychology",
    "JEPG": "Journal of Experimental Psychology: General",
    "JPSP": "Journal of Personality and Social Psychology",
    "PLOS": "PLOS ONE",
    "PS": "Psychological Science",
}

MANUAL_PAPER_OVERRIDES: dict[str, dict[str, str]] = {
    "scheel2021": {
        "entry_type": "article",
        "authors": "Scheel, Anne M. and Schijen, Mitchell R. M. J. and Lakens, Daniel",
        "title": "An Excess of Positive Results: Comparing the Standard Psychology Literature With Registered Reports",
        "journal": "Advances in Methods and Practices in Psychological Science",
        "publisher": "SAGE Publications",
        "year": "2021",
        "volume": "4",
        "number": "2",
        "doi": "10.1177/25152459211007467",
        "url": "https://doi.org/10.1177/25152459211007467",
        "metadata_source": "manual",
    },
    "klein2018": {
        "entry_type": "article",
        "title": "Many Labs 2: Investigating Variation in Replicability Across Samples and Settings",
        "journal": "Advances in Methods and Practices in Psychological Science",
        "publisher": "SAGE Publications",
        "year": "2018",
        "volume": "1",
        "number": "4",
        "pages": "443-490",
        "doi": "10.1177/2515245918810225",
        "url": "https://doi.org/10.1177/2515245918810225",
        "metadata_source": "manual",
    },
    "cred2017": {
        "entry_type": "article",
        "authors": "Credé, Marcus and Tynan, Michael C. and Harms, Peter D.",
        "title": "Much ado about grit: A meta-analytic synthesis of the grit literature.",
        "journal": "Journal of Personality and Social Psychology",
        "publisher": "American Psychological Association (APA)",
        "year": "2017",
        "volume": "113",
        "number": "3",
        "pages": "492-511",
        "doi": "10.1037/pspp0000102",
        "url": "https://doi.org/10.1037/pspp0000102",
        "metadata_source": "manual",
    },
    "jonas2015": {
        "entry_type": "article",
        "title": "To what extent are surgery and invasive procedures effective beyond a placebo response? A systematic review with meta-analysis of randomised, sham controlled trials",
        "journal": "BMJ Open",
        "publisher": "BMJ",
        "year": "2015",
        "volume": "5",
        "number": "12",
        "pages": "e009655",
        "doi": "10.1136/bmjopen-2015-009655",
        "url": "https://doi.org/10.1136/bmjopen-2015-009655",
        "metadata_source": "manual",
    },
    "sethuraman2011": {
        "entry_type": "article",
        "title": "How Well Does Advertising Work? Generalizations from Meta-Analysis of Brand Advertising Elasticities",
        "journal": "Journal of Marketing Research",
        "publisher": "SAGE Publications",
        "year": "2011",
        "volume": "48",
        "number": "3",
        "pages": "457-471",
        "doi": "10.1509/jmkr.48.3.457",
        "url": "https://doi.org/10.1509/jmkr.48.3.457",
        "metadata_source": "manual",
    },
    "du2024": {
        "entry_type": "misc",
        "title": "Clinical trials efficacy results dataset (derivative of AACT)",
        "publisher": "Figshare",
        "year": "2024",
        "doi": "10.6084/m9.figshare.24225166",
        "url": "https://doi.org/10.6084/m9.figshare.24225166",
        "metadata_source": "manual",
    },
    "nhmrc2015": {
        "entry_type": "techreport",
        "authors": "National Health and Medical Research Council",
        "title": "Statement on Homeopathy",
        "publisher": "National Health and Medical Research Council",
        "year": "2015",
        "metadata_source": "manual",
    },
    "taleb2007blackswan": {
        "entry_type": "book",
        "authors": "Taleb, Nassim Nicholas",
        "title": "The Black Swan: The Impact of the Highly Improbable",
        "publisher": "Random House",
        "year": "2007",
        "metadata_source": "manual",
    },
    "gwi2023wellness": {
        "entry_type": "techreport",
        "authors": "Global Wellness Institute",
        "title": "The Global Wellness Economy: Country Rankings",
        "publisher": "Global Wellness Institute",
        "year": "2023",
        "metadata_source": "manual",
    },
    "ftc2018mlm": {
        "entry_type": "techreport",
        "authors": "Federal Trade Commission Staff",
        "title": "Business Opportunity Rule: Multi-Level Marketing and the Federal Trade Commission",
        "publisher": "Federal Trade Commission",
        "year": "2018",
        "metadata_source": "manual",
    },
    "vanzwet2026": {
        "entry_type": "misc",
        "title": "A statistical case for qualified scientific optimism",
        "year": "2026",
        "url": "https://sites.stat.columbia.edu/gelman/research/unpublished/A_statistical_case_for_qualified_scientific_optimism.pdf",
        "metadata_source": "manual",
    },
    "doucouliagos2011": {
        "entry_type": "techreport",
        "authors": "Doucouliagos, Chris",
        "title": "How Large is Large? Preliminary and Relative Guidelines for Interpreting Partial Correlations in Economics",
        "publisher": "Deakin University",
        "year": "2011",
        "metadata_source": "manual",
    },
    "chen2020": {
        "entry_type": "article",
        "title": "Taxation and subsidies on unhealthy foods",
        "journal": "Obesity Reviews",
        "year": "2020",
        "metadata_source": "manual",
    },
    "brown2024": {
        "entry_type": "techreport",
        "title": "Field experiments on digital advertising effectiveness",
        "year": "2024",
        "metadata_source": "manual",
    },
    "nickow2024": {
        "entry_type": "misc",
        "title": "The impressive effects of tutoring on pre-K to 12 learning",
        "year": "2024",
        "metadata_source": "manual",
    },
    "kraft2024": {
        "entry_type": "techreport",
        "title": "How effective are interventions to improve student achievement?",
        "year": "2024",
        "metadata_source": "manual",
    },
    "gelman2018interactions": {
        "entry_type": "misc",
        "authors": "Gelman, Andrew",
        "title": "You need 16 times the sample size to estimate an interaction than to estimate a main effect",
        "publisher": "Statistical Modeling, Causal Inference, and Social Science",
        "year": "2018",
        "metadata_source": "manual",
    },
    "npr2022astrology": {
        "entry_type": "misc",
        "authors": "Brenan, Megan",
        "title": "Three in Four Americans Hold at Least One Paranormal Belief",
        "publisher": "Gallup News",
        "year": "2005",
        "metadata_source": "manual",
    },
    "prasad2008": {
        "entry_type": "article",
        "authors": "Prasad, Ananda S. and Beck, Frances W. J. and Bao, Bin and Snell, Diane and Fitzgerald, James T.",
        "title": "Duration and Severity of Symptoms and Levels of Plasma Interleukin-1 Receptor Antagonist, Soluble Tumor Necrosis Factor Receptor, and Adhesion Molecules in Patients with Common Cold Treated with Zinc Acetate",
        "journal": "The Journal of Infectious Diseases",
        "publisher": "Oxford University Press (OUP)",
        "year": "2008",
        "volume": "197",
        "number": "6",
        "pages": "795-802",
        "doi": "10.1086/528803",
        "url": "https://doi.org/10.1086/528803",
        "metadata_source": "manual",
    },
    "petrie1989": {
        "entry_type": "article",
        "authors": "Petrie, Keith and Conaglen, J. V. and Thompson, L. and Chamberlain, Kerry",
        "title": "Effect of melatonin on jet lag after long haul flights",
        "journal": "BMJ",
        "publisher": "BMJ",
        "year": "1989",
        "volume": "298",
        "number": "6675",
        "pages": "705-707",
        "doi": "10.1136/bmj.298.6675.705",
        "url": "https://doi.org/10.1136/bmj.298.6675.705",
        "metadata_source": "manual",
    },
    "amaral2019brazilian": {
        "entry_type": "article",
        "authors": "Amaral, Olavo B. and Neves, Kleber and Wasilewska-Sampaio, Ana P. and Carneiro, Clarissa F. D.",
        "title": "The Brazilian Reproducibility Initiative",
        "journal": "eLife",
        "publisher": "eLife Sciences Publications",
        "year": "2019",
        "volume": "8",
        "pages": "e41602",
        "doi": "10.7554/eLife.41602",
        "url": "https://doi.org/10.7554/eLife.41602",
        "metadata_source": "manual",
    },
    "bago2022trolley": {
        "entry_type": "article",
        "authors": "Bago, Bence and Kovacs, Marton and Protzko, John and Nagy, Tamas and Kekecs, Zoltan and others",
        "title": "Situational factors shape moral judgements in the trolley dilemma in Eastern, Southern and Western countries in a culturally diverse sample",
        "journal": "Nature Human Behaviour",
        "publisher": "Springer Science and Business Media LLC",
        "year": "2022",
        "volume": "6",
        "number": "6",
        "pages": "880-895",
        "doi": "10.1038/s41562-022-01319-5",
        "url": "https://doi.org/10.1038/s41562-022-01319-5",
        "metadata_source": "manual",
    },
    "boyce2023studentreplication": {
        "entry_type": "article",
        "authors": "Boyce, Veronica and Mathur, Maya B. and Frank, Michael C.",
        "title": "Eleven years of student replication projects provide evidence on the correlates of replicability in psychology",
        "journal": "Royal Society Open Science",
        "publisher": "The Royal Society",
        "year": "2023",
        "volume": "10",
        "number": "11",
        "pages": "231240",
        "doi": "10.1098/rsos.231240",
        "url": "https://doi.org/10.1098/rsos.231240",
        "metadata_source": "manual",
    },
    "cova2021estimating": {
        "entry_type": "article",
        "authors": "Cova, Florian and Strickland, Brent and Abatista, Angela Gaia Felicita and Allard, Aurelien and Andow, James and others",
        "title": "Estimating the reproducibility of experimental philosophy",
        "journal": "Review of Philosophy and Psychology",
        "publisher": "Springer Science and Business Media LLC",
        "year": "2021",
        "volume": "12",
        "pages": "9-44",
        "doi": "10.1007/s13164-018-0400-9",
        "url": "https://doi.org/10.1007/s13164-018-0400-9",
        "metadata_source": "manual",
    },
    "davis2023managementscience": {
        "entry_type": "article",
        "authors": "Davis, Andrew M. and Flicker, Blair and Hyndman, Kyle and Katok, Elena and Keppler, Samantha and Leider, Stephen and Long, Xiaoyang and Tong, Jordan D.",
        "title": "A Replication Study of Operations Management Experiments in Management Science",
        "journal": "Management Science",
        "publisher": "Institute for Operations Research and the Management Sciences",
        "year": "2023",
        "volume": "69",
        "number": "9",
        "pages": "4977-4991",
        "doi": "10.1287/mnsc.2023.4866",
        "url": "https://doi.org/10.1287/mnsc.2023.4866",
        "metadata_source": "manual",
    },
    "ebersole2016manylabs3": {
        "entry_type": "article",
        "authors": "Ebersole, Charles R. and Atherton, Olivia E. and Belanger, Aimee L. and Skulborstad, Hayley M. and Allen, Jill M. and others",
        "title": "Many Labs 3: Evaluating participant pool quality across the academic semester via replication",
        "journal": "Journal of Experimental Social Psychology",
        "publisher": "Elsevier BV",
        "year": "2016",
        "volume": "67",
        "pages": "68-82",
        "doi": "10.1016/j.jesp.2015.10.012",
        "url": "https://doi.org/10.1016/j.jesp.2015.10.012",
        "metadata_source": "manual",
    },
    "holzmeister2025decisionmarket": {
        "entry_type": "article",
        "authors": "Holzmeister, Felix and Johannesson, Magnus and Camerer, Colin F. and Chen, Yiling and Ho, Teck-Hua and others",
        "title": "Examining the replicability of online experiments selected by a decision market",
        "journal": "Nature Human Behaviour",
        "publisher": "Springer Science and Business Media LLC",
        "year": "2025",
        "volume": "9",
        "pages": "316-330",
        "doi": "10.1038/s41562-024-02062-9",
        "url": "https://doi.org/10.1038/s41562-024-02062-9",
        "metadata_source": "manual",
    },
    "klein2014manylabs1": {
        "entry_type": "article",
        "authors": "Klein, Richard A. and Ratliff, Kate A. and Vianello, Michelangelo and Adams, Reginald B. and Bahnik, Stepan and others",
        "title": "Investigating variation in replicability: A Many Labs replication project",
        "journal": "Social Psychology",
        "publisher": "Hogrefe Publishing Group",
        "year": "2014",
        "volume": "45",
        "number": "3",
        "pages": "142-152",
        "doi": "10.1027/1864-9335/a000178",
        "url": "https://doi.org/10.1027/1864-9335/a000178",
        "metadata_source": "manual",
    },
    "klein2022manylabs4": {
        "entry_type": "article",
        "authors": "Klein, Richard A. and Cook, Corey L. and Ebersole, Charles R. and Vitiello, Christine and Nosek, Brian A. and others",
        "title": "Many Labs 4: Failure to Replicate Mortality Salience Effect With and Without Original Author Involvement",
        "journal": "Collabra: Psychology",
        "publisher": "University of California Press",
        "year": "2022",
        "volume": "8",
        "number": "1",
        "pages": "35271",
        "doi": "10.1525/collabra.35271",
        "url": "https://doi.org/10.1525/collabra.35271",
        "metadata_source": "manual",
    },
    "masur2025privacy": {
        "entry_type": "article",
        "authors": "Masur, Philipp K. and Ranzini, Giulia",
        "title": "Privacy calculus, privacy paradox, and context collapse: A replication of three key studies in communication privacy research",
        "journal": "Journal of Communication",
        "publisher": "Oxford University Press",
        "year": "2025",
        "doi": "10.1093/joc/jqaf007",
        "url": "https://doi.org/10.1093/joc/jqaf007",
        "metadata_source": "manual",
    },
    "protzko2024highrep": {
        "entry_type": "article",
        "authors": "Protzko, John and Krosnick, Jon and Nelson, Leif and Nosek, Brian A. and Axt, Jordan and others",
        "title": "RETRACTED ARTICLE: High replicability of newly discovered social-behavioural findings is achievable",
        "journal": "Nature Human Behaviour",
        "publisher": "Springer Science and Business Media LLC",
        "year": "2024",
        "volume": "8",
        "pages": "311-319",
        "doi": "10.1038/s41562-023-01749-9",
        "url": "https://doi.org/10.1038/s41562-023-01749-9",
        "metadata_source": "manual",
    },
    "soto2019loopr": {
        "entry_type": "article",
        "authors": "Soto, Christopher J.",
        "title": "How Replicable Are Links Between Personality Traits and Consequential Life Outcomes? The Life Outcomes of Personality Replication Project",
        "journal": "Psychological Science",
        "publisher": "SAGE Publications",
        "year": "2019",
        "volume": "30",
        "number": "5",
        "pages": "711-727",
        "doi": "10.1177/0956797619831612",
        "url": "https://doi.org/10.1177/0956797619831612",
        "metadata_source": "manual",
    },
    "bem2011": {
        "entry_type": "article",
        "authors": "Bem, Daryl J.",
        "title": "Feeling the future: Experimental evidence for anomalous retroactive influences on cognition and affect",
        "journal": "Journal of Personality and Social Psychology",
        "publisher": "American Psychological Association (APA)",
        "year": "2011",
        "volume": "100",
        "number": "3",
        "pages": "407-425",
        "doi": "10.1037/a0021524",
        "url": "https://doi.org/10.1037/a0021524",
        "metadata_source": "manual",
    },
    "douglass2026appendixD": {
        "entry_type": "misc",
        "authors": "Douglass, Rex W.",
        "title": "Appendix D supplemental replication-pair backfill table",
        "year": "2026",
        "url": "https://www.rexdouglass.com",
        "note": "Local source table moved from the main manuscript into the companion data appendices.",
        "metadata_source": "manual",
    },
    "douglass2026manualPairs": {
        "entry_type": "misc",
        "authors": "Douglass, Rex W.",
        "title": "Manual paper-grounded replication-pair recovery rows",
        "year": "2026",
        "url": "https://www.rexdouglass.com",
        "note": "Local source table for manually recovered pairs grounded to fetched supplements, DOI targets, or local project records.",
        "metadata_source": "manual",
    },
    "boyce2024rescue": {
        "entry_type": "article",
        "authors": "Boyce, Veronica and Prystawski, Ben and Abutto, Adani B. and Chen, Emily M. and Chen, Ziwen and Chiu, Howard and others",
        "title": "Estimating the Replicability of Psychology Experiments After an Initial Failure to Replicate",
        "journal": "Collabra: Psychology",
        "year": "2024",
        "doi": "10.1525/collabra.125685",
        "url": "https://doi.org/10.1525/collabra.125685",
        "metadata_source": "manual",
    },
    "peyton2021covidonline": {
        "entry_type": "article",
        "authors": "Peyton, Kyle and Huber, Gregory A. and Coppock, Alexander",
        "title": "The Generalizability of Online Experiments Conducted During the COVID-19 Pandemic",
        "journal": "Journal of Experimental Political Science",
        "year": "2021",
        "doi": "10.1017/xps.2021.17",
        "url": "https://doi.org/10.1017/xps.2021.17",
        "metadata_source": "manual",
    },
    "oppen2026contextual": {
        "entry_type": "article",
        "authors": "von Oppen, Schira and Ilie, Ilinca and Oberlader, Verena and Verschuere, Bruno",
        "title": "Contextual Bias in Verbal Credibility Assessment: A Preregistered Direct Replication of the Criteria-Based Content Analysis Condition in Bogaard Et al. (2014)",
        "journal": "Applied Cognitive Psychology",
        "year": "2026",
        "volume": "40",
        "number": "1",
        "doi": "10.1002/acp.70168",
        "url": "https://doi.org/10.1002/acp.70168",
        "metadata_source": "manual",
    },
    "arroyoaraujo2022eqipd": {
        "entry_type": "article",
        "authors": "Arroyo-Araujo, Maria and Voelkl, Bernhard and Laloux, Clement and Novak, Janja and Koopmans, Bastijn and Waldron, Ann-Marie and others",
        "title": "Systematic assessment of the replicability and generalizability of preclinical findings: Impact of protocol harmonization across laboratory sites",
        "journal": "PLOS Biology",
        "year": "2022",
        "doi": "10.1371/journal.pbio.3001886",
        "url": "https://doi.org/10.1371/journal.pbio.3001886",
        "metadata_source": "manual",
    },
    "galak2012psi": {
        "entry_type": "article",
        "authors": "Galak, Jeff and LeBoeuf, Robyn A. and Nelson, Leif D. and Simmons, Joseph P.",
        "title": "Correcting the past: Failures to replicate psi",
        "journal": "Journal of Personality and Social Psychology",
        "year": "2012",
        "volume": "103",
        "number": "6",
        "pages": "933-948",
        "doi": "10.1037/a0029709",
        "url": "https://doi.org/10.1037/a0029709",
        "metadata_source": "manual",
    },
    "balakrishnan2017greed": {
        "entry_type": "article",
        "authors": "Balakrishnan, Anjana and Palma, Paolo A. and Patenaude, Joshua and Campbell, Lorne",
        "title": "A 4-study replication of the moderating effects of greed on socioeconomic status and unethical behaviour",
        "journal": "Scientific Data",
        "year": "2017",
        "volume": "4",
        "doi": "10.1038/sdata.2016.120",
        "url": "https://doi.org/10.1038/sdata.2016.120",
        "metadata_source": "manual",
    },
    "jinAwesomeReplicabilityData": {
        "entry_type": "misc",
        "authors": "Jin, Ying",
        "title": "awesome-replicability-data: Repository of unit-level direct replication studies",
        "year": "n.d.",
        "url": "https://github.com/ying531/awesome-replicability-data",
        "note": "GitHub repository citation metadata from CITATION.cff.",
        "metadata_source": "manual",
    },
    "tonkovic2022linguisticOsf": {
        "entry_type": "article",
        "authors": "Tonković, Mirjana and Vlašiček, Denis and Dumančić, Francesca",
        "title": "Preregistered direct replication of the linguistic frame effect on perceived blame and financial liability",
        "journal": "Legal and Criminological Psychology",
        "year": "2022",
        "volume": "27",
        "number": "2",
        "pages": "354-369",
        "doi": "10.1111/lcrp.12219",
        "url": "https://doi.org/10.1111/lcrp.12219",
        "note": "OSF project with source materials and data: https://osf.io/jmknw/.",
        "metadata_source": "manual",
    },
    "odonnell2018dijksterhuis": {
        "entry_type": "article",
        "authors": "O'Donnell, Michael and Nelson, Leif D. and Ackermann, Evi and Aczel, Balazs and Akhtar, Athfah and Aldrovandi, Silvio and others",
        "title": "Registered Replication Report: Dijksterhuis and van Knippenberg (1998)",
        "journal": "Perspectives on Psychological Science",
        "year": "2018",
        "volume": "13",
        "number": "2",
        "pages": "268-294",
        "doi": "10.1177/1745691618755704",
        "url": "https://doi.org/10.1177/1745691618755704",
        "metadata_source": "manual",
    },
    "chen2025objectOrientation": {
        "entry_type": "article",
        "authors": "Chen, Sau-Chin and Buchanan, Erin M. and Kekecs, Zoltan and Miller, Jeremy K. and Szabelska, Anna and Aczel, Balazs and others",
        "title": "Investigating object orientation effects across 18 languages",
        "journal": "Current Psychology",
        "year": "2025",
        "doi": "10.1007/s12144-025-08304-x",
        "url": "https://doi.org/10.1007/s12144-025-08304-x",
        "metadata_source": "manual",
    },
    "alogna2014schooler": {
        "entry_type": "article",
        "authors": "Alogna, Vincenzo K. and Attaya, Michelle K. and Aucoin, Paul and Bahnik, Stepan and Birch, Samuel and Birt, Angela R. and others",
        "title": "Registered Replication Report: Schooler and Engstler-Schooler (1990)",
        "journal": "Perspectives on Psychological Science",
        "year": "2014",
        "volume": "9",
        "number": "5",
        "pages": "556-578",
        "doi": "10.1177/1745691614545653",
        "url": "https://doi.org/10.1177/1745691614545653",
        "metadata_source": "manual",
    },
    "bouwmeester2017rand": {
        "entry_type": "article",
        "authors": "Bouwmeester, Samantha and Verkoeijen, Peter P. J. L. and Aczel, Balazs and Barbosa, Fernando and Begue, Laurent and Branas-Garza, Pablo and others",
        "title": "Registered Replication Report: Rand, Greene, and Nowak (2012)",
        "journal": "Perspectives on Psychological Science",
        "year": "2017",
        "volume": "12",
        "number": "3",
        "pages": "527-542",
        "doi": "10.1177/1745691617693624",
        "url": "https://doi.org/10.1177/1745691617693624",
        "metadata_source": "manual",
    },
    "cheung2016finkel": {
        "entry_type": "article",
        "authors": "Cheung, Irene and Campbell, Lorne and LeBel, Etienne P. and Ackerman, Robert A. and Aykutoglu, Bulent and Bahnik, Stepan and others",
        "title": "Registered Replication Report: Study 1 From Finkel, Rusbult, Kumashiro, and Hannon (2002)",
        "journal": "Perspectives on Psychological Science",
        "year": "2016",
        "volume": "11",
        "number": "5",
        "pages": "750-764",
        "doi": "10.1177/1745691616664694",
        "url": "https://doi.org/10.1177/1745691616664694",
        "metadata_source": "manual",
    },
    "elliott2021flavell": {
        "entry_type": "article",
        "authors": "Elliott, Emily M. and Morey, Candice C. and AuBuchon, Angela M. and Cowan, Nelson and Jarrold, Chris and Adams, Eryn J. and others",
        "title": "Multilab Direct Replication of Flavell, Beach, and Chinsky (1966): Spontaneous Verbal Rehearsal in a Memory Task as a Function of Age",
        "journal": "Advances in Methods and Practices in Psychological Science",
        "year": "2021",
        "volume": "4",
        "number": "2",
        "doi": "10.1177/25152459211018187",
        "url": "https://doi.org/10.1177/25152459211018187",
        "metadata_source": "manual",
    },
    "hagger2016egodepletion": {
        "entry_type": "article",
        "authors": "Hagger, Martin S. and Chatzisarantis, Nikos L. D. and Alberts, Hugo and Anggono, Calvin O. and Batailler, Cedric and Birt, Angela R. and others",
        "title": "A Multilab Preregistered Replication of the Ego-Depletion Effect",
        "journal": "Perspectives on Psychological Science",
        "year": "2016",
        "volume": "11",
        "number": "4",
        "pages": "546-573",
        "doi": "10.1177/1745691616652873",
        "url": "https://doi.org/10.1177/1745691616652873",
        "metadata_source": "manual",
    },
    "mccarthy2018srull": {
        "entry_type": "article",
        "authors": "McCarthy, Randy J. and Skowronski, John J. and Verschuere, Bruno and Meijer, Ewout H. and Jim, Ariane and Hoogesteyn, Katherine and others",
        "title": "Registered Replication Report on Srull and Wyer (1979)",
        "journal": "Advances in Methods and Practices in Psychological Science",
        "year": "2018",
        "volume": "1",
        "number": "3",
        "pages": "321-336",
        "doi": "10.1177/2515245918777487",
        "url": "https://doi.org/10.1177/2515245918777487",
        "metadata_source": "manual",
    },
    "verschuere2018mazar": {
        "entry_type": "article",
        "authors": "Verschuere, Bruno and Meijer, Ewout H. and Jim, Ariane and Hoogesteyn, Katherine and Orthey, Robin and McCarthy, Randy J. and others",
        "title": "Registered Replication Report on Mazar, Amir, and Ariely (2008)",
        "journal": "Advances in Methods and Practices in Psychological Science",
        "year": "2018",
        "volume": "1",
        "number": "3",
        "pages": "299-317",
        "doi": "10.1177/2515245918781032",
        "url": "https://doi.org/10.1177/2515245918781032",
        "metadata_source": "manual",
    },
    "ranehill2015powerposing": {
        "entry_type": "article",
        "authors": "Ranehill, Eva and Dreber, Anna and Johannesson, Magnus and Leiberg, Susanne and Sul, Sunhae and Weber, Roberto A.",
        "title": "Assessing the Robustness of Power Posing",
        "journal": "Psychological Science",
        "year": "2015",
        "volume": "26",
        "number": "5",
        "pages": "653-656",
        "doi": "10.1177/0956797614553946",
        "url": "https://doi.org/10.1177/0956797614553946",
        "metadata_source": "manual",
    },
    "murphy2025sportsReplication": {
        "entry_type": "article",
        "authors": "Murphy, Jennifer and Caldwell, Aaron R. and Mesquida, Cristian and Ladell, Aera J. M. and Encarnacion-Martinez, Alberto and Tual, Alexandre and others",
        "title": "Estimating the Replicability of Sports and Exercise Science Research",
        "journal": "Sports Medicine",
        "year": "2025",
        "doi": "10.1007/s40279-025-02201-w",
        "url": "https://doi.org/10.1007/s40279-025-02201-w",
        "metadata_source": "manual",
    },
    "vaidis2024dissonance": {
        "entry_type": "article",
        "authors": "Vaidis, David C. and Sleegers, Willem W. A. and van Leeuwen, Florian and DeMarree, Kenneth G. and Saetrevik, Bjorn and Ross, Robert M. and others",
        "title": "A Multilab Replication of the Induced-Compliance Paradigm of Cognitive Dissonance",
        "journal": "Advances in Methods and Practices in Psychological Science",
        "year": "2024",
        "volume": "7",
        "number": "1",
        "doi": "10.1177/25152459231213375",
        "url": "https://doi.org/10.1177/25152459231213375",
        "metadata_source": "manual",
    },
    "smit2025scaffolding": {
        "entry_type": "article",
        "authors": "Smit, Nienke and de Kleijn, Renske and Wicherts, Jelte M. and van de Pol, Janneke",
        "title": "What it takes to tutor: A preregistered direct replication of the scaffolding experimental study by D. Wood et al. (1978)",
        "journal": "Journal of Educational Psychology",
        "year": "2025",
        "doi": "10.1037/edu0000965",
        "url": "https://doi.org/10.1037/edu0000965",
        "metadata_source": "manual",
    },
    "ying2023pilot": {
        "entry_type": "article",
        "authors": "Ying, Xiangji and Ehrhardt, Stephan",
        "title": "Pilot trials may improve the quality of full-scale trials: a meta-research study",
        "journal": "Journal of Clinical Epidemiology",
        "year": "2023",
        "volume": "162",
        "pages": "83-93",
        "doi": "10.1016/j.jclinepi.2023.06.017",
        "url": "https://doi.org/10.1016/j.jclinepi.2023.06.017",
        "metadata_source": "manual",
    },
    "ioannidis2005contradicted": {
        "entry_type": "article",
        "authors": "Ioannidis, John P. A.",
        "title": "Contradicted and Initially Stronger Effects in Highly Cited Clinical Research",
        "journal": "JAMA",
        "year": "2005",
        "volume": "294",
        "number": "2",
        "pages": "218-228",
        "doi": "10.1001/jama.294.2.218",
        "url": "https://doi.org/10.1001/jama.294.2.218",
        "metadata_source": "manual",
    },
    "eerland2016hart": {
        "entry_type": "article",
        "authors": "Eerland, Anita and Sherrill, Amanda M. and Magliano, Joseph P. and Zwaan, Rolf A. and Arnal, Juan D. and Aucoin, Paul and others",
        "title": "Registered Replication Report: Hart and Albarracin (2011)",
        "journal": "Perspectives on Psychological Science",
        "year": "2016",
        "volume": "11",
        "number": "1",
        "pages": "158-171",
        "doi": "10.1177/1745691615605826",
        "url": "https://doi.org/10.1177/1745691615605826",
        "metadata_source": "manual",
    },
    "schweinsberg2016pipeline": {
        "entry_type": "article",
        "authors": "Schweinsberg, Martin and Madan, Nikhil and Vianello, Michelangelo and Sommer, S. Amy and Jordan, Jennifer and Tierney, Warren and others",
        "title": "The pipeline project: Pre-publication independent replications of a single laboratory's research pipeline",
        "journal": "Journal of Experimental Social Psychology",
        "year": "2016",
        "volume": "66",
        "pages": "55-67",
        "doi": "10.1016/j.jesp.2015.10.001",
        "url": "https://doi.org/10.1016/j.jesp.2015.10.001",
        "metadata_source": "manual",
    },
    "stoevenbelt2024johns": {
        "entry_type": "misc",
        "authors": "Stoevenbelt, Andrea Helena and Flore, Paulette Carien and Wicherts, Jelte M. and Bergers, Rachel and Calin-Jageman, Robert and Gomez, Luis Angel and others",
        "title": "Registered Replication Report: Johns, Schmader, and Martens (2005)",
        "year": "2024",
        "doi": "10.31234/osf.io/qctkp",
        "url": "https://doi.org/10.31234/osf.io/qctkp",
        "metadata_source": "manual",
    },
    "kekecs2023tpp": {
        "entry_type": "article",
        "authors": "Kekecs, Zoltan and Palfi, Bence and Szaszi, Barnabas and Szecsi, Peter and Zrubka, Mark and Kovacs, Marton and others",
        "title": "Raising the value of research studies in psychological science by increasing the credibility of research reports: the transparent Psi project",
        "journal": "Royal Society Open Science",
        "year": "2023",
        "volume": "10",
        "number": "2",
        "pages": "191375",
        "doi": "10.1098/rsos.191375",
        "url": "https://doi.org/10.1098/rsos.191375",
        "metadata_source": "manual",
    },
    "wagenmakers2016strack": {
        "entry_type": "article",
        "authors": "Wagenmakers, Eric-Jan and Beek, Titia and Dijkhoff, Laura and Gronau, Quentin F. and Acosta, Aileen and Adams, Reginald B. and others",
        "title": "Registered Replication Report: Strack, Martin, and Stepper (1988)",
        "journal": "Perspectives on Psychological Science",
        "year": "2016",
        "volume": "11",
        "number": "6",
        "pages": "917-928",
        "doi": "10.1177/1745691616674458",
        "url": "https://doi.org/10.1177/1745691616674458",
        "metadata_source": "manual",
    },
    "kleinberg2018deceptive": {
        "entry_type": "article",
        "authors": "Kleinberg, Bennett and Warmelink, Lara and Arntz, Arnoud and Verschuere, Bruno",
        "title": "The first direct replication on using verbal credibility assessment for the detection of deceptive intentions",
        "journal": "Applied Cognitive Psychology",
        "year": "2018",
        "volume": "32",
        "number": "5",
        "pages": "592-599",
        "doi": "10.1002/acp.3439",
        "url": "https://doi.org/10.1002/acp.3439",
        "metadata_source": "manual",
    },
    "haim2025imagecredibility": {
        "entry_type": "article",
        "authors": "Haim, Mario and Knopfle, Philipp and Breuer, Johannes",
        "title": "Contextual Changes, Credible Conclusions? A Direct and Conceptual Replication of Shen et al.'s (2019) Study on Online Image Credibility",
        "journal": "Media Psychology",
        "year": "2025",
        "doi": "10.1080/15213269.2025.2595452",
        "url": "https://doi.org/10.1080/15213269.2025.2595452",
        "metadata_source": "manual",
    },
    "luyten2017retrievalExtinction": {
        "entry_type": "article",
        "authors": "Luyten, Laura and Beckers, Tom",
        "title": "A preregistered, direct replication attempt of the retrieval-extinction effect in cued fear conditioning in rats",
        "journal": "Neurobiology of Learning and Memory",
        "year": "2017",
        "volume": "144",
        "pages": "208-215",
        "doi": "10.1016/j.nlm.2017.07.014",
        "url": "https://doi.org/10.1016/j.nlm.2017.07.014",
        "metadata_source": "manual",
    },
    "arelbundock2026underpowered": {
        "entry_type": "article",
        "authors": "Arel-Bundock, Vincent and Briggs, Ryan C. and Doucouliagos, Hristos and Avina, Marco M. and Stanley, T. D.",
        "title": "Quantitative Political Science Research Is Greatly Underpowered",
        "journal": "The Journal of Politics",
        "year": "2026",
        "doi": "10.1086/734279",
        "url": "https://doi.org/10.1086/734279",
        "metadata_source": "manual",
    },
    "bergmann2018metalab": {
        "entry_type": "article",
        "authors": "Bergmann, Christina and Tsuji, Sho and Piccinini, Page E. and Lewis, Molly L. and Braginsky, Mika and Frank, Michael C. and others",
        "title": "Promoting Replicability in Developmental Research Through Meta-analyses: Insights From Language Acquisition Research",
        "journal": "Child Development",
        "year": "2018",
        "volume": "89",
        "number": "6",
        "pages": "1996-2009",
        "doi": "10.1111/cdev.13079",
        "url": "https://doi.org/10.1111/cdev.13079",
        "metadata_source": "manual",
    },
    "olivier2024cardioRcts": {
        "entry_type": "article",
        "authors": "Olivier, Christoph B. and Struss, Lasse and Sunnen, Nathalie and Kaier, Klaus and Heger, Lukas A. and Westermann, Dirk",
        "title": "Accuracy of Event Rate and Effect Size Estimation in Major Cardiovascular Trials",
        "journal": "JAMA Network Open",
        "year": "2024",
        "volume": "7",
        "number": "4",
        "pages": "e248818",
        "doi": "10.1001/jamanetworkopen.2024.8818",
        "url": "https://doi.org/10.1001/jamanetworkopen.2024.8818",
        "metadata_source": "manual",
    },
    "yun2024llmExtraction": {
        "entry_type": "inproceedings",
        "authors": "Yun, Hye Sun and Pogrebitskiy, David and Marshall, Iain J. and Wallace, Byron C.",
        "title": "Automatically Extracting Numerical Results from Randomized Controlled Trials with Large Language Models",
        "booktitle": "Proceedings of Machine Learning for Health",
        "year": "2024",
        "volume": "252",
        "url": "https://proceedings.mlr.press/v252/yun24a.html",
        "metadata_source": "manual",
    },
    "bosco2020metabus": {
        "entry_type": "article",
        "authors": "Bosco, Frank A. and Field, James G. and Larsen, Kai R. and Chang, Yingyi and Uggerslev, Krista L.",
        "title": "Advancing Meta-Analysis With Knowledge-Management Platforms: Using metaBUS in Psychology",
        "journal": "Advances in Methods and Practices in Psychological Science",
        "year": "2019",
        "volume": "3",
        "number": "1",
        "pages": "124-137",
        "doi": "10.1177/2515245919882693",
        "url": "https://doi.org/10.1177/2515245919882693",
        "metadata_source": "manual",
    },
    "i4rPublicWorkbook": {
        "entry_type": "misc",
        "title": "Institute for Replication public replication database workbook",
        "publisher": "Institute for Replication",
        "year": "n.d.",
        "url": "https://i4replication.org/",
        "note": "Cataloged local workbook source; not integrated because the estimate sheet is not a standardized direct-pair D/N table.",
        "metadata_source": "manual",
    },
    "pooledMarketRPackageData": {
        "entry_type": "misc",
        "title": "PooledMarketR package data object PM_data.Rdata",
        "publisher": "PooledMarketR",
        "year": "n.d.",
        "url": "https://cran.r-project.org/package=PooledMarketR",
        "note": "Cataloged market and survey metadata sidecar spanning EERP, ML2, RPP, and SSRP; retained as overlap metadata, not a pair table.",
        "metadata_source": "manual",
    },
    "angristLearningCurve2023Openicpsr": {
        "entry_type": "misc",
        "title": "Learning Curve tutoring replication openICPSR project",
        "publisher": "openICPSR",
        "year": "2023",
        "url": "https://www.openicpsr.org/openicpsr/project/189561/view",
        "note": "Harvested lead source; access required registration during audit.",
        "metadata_source": "manual",
    },
    "coppock2019generalizability": {
        "entry_type": "misc",
        "title": "Coppock 2019 generalizability corpus",
        "publisher": "Yale Institution for Social and Policy Studies",
        "year": "2019",
        "url": "https://isps.yale.edu/research/publications/isps18-07",
        "note": "Cataloged direct-pair source using survey ATE metrics; not promoted to the shared D axis.",
        "metadata_source": "manual",
    },
    "eefProjectsIndex": {
        "entry_type": "misc",
        "title": "Education Endowment Foundation projects and evaluation index",
        "publisher": "Education Endowment Foundation",
        "year": "n.d.",
        "url": "https://educationendowmentfoundation.org.uk/projects-and-evaluation/projects",
        "note": "Harvested lead index for education replication and regrant reports.",
        "metadata_source": "manual",
    },
    "ernPeRrrOpenNeuro": {
        "entry_type": "misc",
        "title": "ERN Pe psychometrics registered replication report OpenNeuro dataset",
        "publisher": "OpenNeuro",
        "year": "2023",
        "url": "https://openneuro.org/datasets/ds004602/versions/1.0.1",
        "note": "Harvested lead source; OpenNeuro access blocked automated extraction in the current audit.",
        "metadata_source": "manual",
    },
    "eyewitnessTenCountriesOsf": {
        "entry_type": "misc",
        "title": "Eyewitness memory distortion in ten countries OSF project",
        "publisher": "Open Science Framework",
        "year": "2018",
        "url": "https://osf.io/a35rx/",
        "note": "Staged harvested source; effect-conversion policy remains unresolved.",
        "metadata_source": "manual",
    },
    "ito2018eyewitnessTenCountries": {
        "entry_type": "article",
        "authors": "Ito, Hiroshi and Barzykowski, Krystian and Grzesik, Magdalena and Gülgöz, Sami and Gürdere, Ceren and Janssen, Steve M. J. and Khor, Jessie and Rowthorn, Harriet and Wade, Kimberley A. and Luna, Karlos and others",
        "title": "Eyewitness Memory Distortion Following Co-Witness Discussion: A Replication of Garry, French, Kinzett, and Mori (2008) in Ten Countries",
        "journal": "Journal of Applied Research in Memory and Cognition",
        "year": "2019",
        "volume": "8",
        "number": "1",
        "pages": "68-77",
        "doi": "10.1016/j.jarmac.2018.09.004",
        "url": "https://doi.org/10.1016/j.jarmac.2018.09.004",
        "metadata_source": "manual",
    },
    "iblReproEphysAws": {
        "entry_type": "misc",
        "title": "IBL Reproducible Ephys open data registry",
        "publisher": "AWS Open Data Registry",
        "year": "2024",
        "url": "https://registry.opendata.aws/ibl-reproducible-ephys/",
        "note": "Harvested lead source; AWS loader work remains pending.",
        "metadata_source": "manual",
    },
    "iesSystematicReplicationAwards": {
        "entry_type": "misc",
        "title": "IES research grants focused on systematic replication",
        "publisher": "Institute of Education Sciences",
        "year": "n.d.",
        "url": "https://ies.ed.gov/funding/research/programs/research-grants-focused-on-systematic-replication",
        "note": "Harvested program-index source for scattered per-award deposits.",
        "metadata_source": "manual",
    },
    "klein2016independentReplicationInitiative": {
        "entry_type": "article",
        "authors": "Tierney, Warren and Hardy, Jay H. and Ebersole, Charles R. and Leavitt, Keith and Viganola, Domenico and Clemente, Edward G. and Gordon, Michael and Dreber, Anna and Johannesson, Magnus and Pfeiffer, Thomas and others",
        "title": "Data from a pre-publication independent replication initiative examining ten moral judgement effects",
        "journal": "Scientific Data",
        "year": "2016",
        "volume": "3",
        "doi": "10.1038/sdata.2016.82",
        "url": "https://doi.org/10.1038/sdata.2016.82",
        "metadata_source": "manual",
    },
    "jaljuliKafkafi2023MousePhenome": {
        "entry_type": "misc",
        "title": "Jaljuli and Kafkafi multi-lab rodent replication Mouse Phenome Database source",
        "publisher": "Mouse Phenome Database",
        "year": "2023",
        "url": "https://phenome.jax.org/",
        "note": "Staged harvested lead; preclinical extraction policy remains pending.",
        "metadata_source": "manual",
    },
    "manyBabies3Osf": {
        "entry_type": "misc",
        "title": "ManyBabies 3 OSF project",
        "publisher": "Open Science Framework",
        "year": "n.d.",
        "url": "https://osf.io/kqu9v/",
        "note": "Downloaded lead source; local OSF file list currently contains registered-report PDFs and appendices rather than a machine-readable pair-result table.",
        "metadata_source": "manual",
    },
    "manyBabies2020Ids": {
        "entry_type": "article",
        "authors": "literal:ManyBabies Consortium",
        "title": "Quantifying Sources of Variability in Infancy Research Using the Infant-Directed-Speech Preference",
        "journal": "Advances in Methods and Practices in Psychological Science",
        "year": "2020",
        "volume": "3",
        "number": "1",
        "pages": "24--52",
        "doi": "10.1177/2515245919900809",
        "url": "https://doi.org/10.1177/2515245919900809",
        "metadata_source": "manual",
    },
    "byersHeinlein2021manybabiesBilingual": {
        "entry_type": "article",
        "authors": "Byers-Heinlein, Krista and Tsui, Angeline Sin Mei and Bergmann, Christina and Black, Alexis K. and Brown, Alison and Carbajal, Maria Julia and Durrant, Samantha and Fennell, Christopher T. and others",
        "title": "A Multilab Study of Bilingual Infants: Exploring the Preference for Infant-Directed Speech",
        "journal": "Advances in Methods and Practices in Psychological Science",
        "year": "2021",
        "volume": "4",
        "number": "1",
        "doi": "10.1177/2515245920974622",
        "url": "https://doi.org/10.1177/2515245920974622",
        "metadata_source": "manual",
    },
    "manyBabies2AnalysisRepo": {
        "entry_type": "misc",
        "title": "ManyBabies 2 analysis repository",
        "publisher": "GitHub",
        "year": "n.d.",
        "url": "https://github.com/manybabies/mb2-analysis",
        "note": "Public analysis repository and paper source for the ManyBabies 2 knowledge/ignorance anticipatory-looking registered-report project; strict D/N extraction remains blocked by native model coefficients and unavailable processed result objects.",
        "metadata_source": "manual",
    },
    "fyfe2021manyclasses1": {
        "entry_type": "article",
        "authors": "Fyfe, Emily R. and de Leeuw, Joshua R. and Carvalho, Paulo F. and Goldstone, Robert L. and Sherman, Janelle and Motz, Benjamin A. and others",
        "title": "ManyClasses 1: Assessing the Generalizable Effect of Immediate Feedback Versus Delayed Feedback Across Many College Classes",
        "journal": "Advances in Methods and Practices in Psychological Science",
        "publisher": "SAGE Publications",
        "year": "2021",
        "doi": "10.1177/25152459211027575",
        "url": "https://doi.org/10.1177/25152459211027575",
        "metadata_source": "manual",
    },
    "manyBabies4Project": {
        "entry_type": "misc",
        "title": "ManyBabies 4 helpers/hinderers project",
        "publisher": "ManyBabies",
        "year": "n.d.",
        "url": "https://manybabies.org/MB4/",
        "note": "Stage 1 and Stage 2 Registered Report project with public analysis repository; exact Plot 3 row extraction pending.",
        "metadata_source": "manual",
    },
    "vanDenAkkerPreregPractice": {
        "entry_type": "misc",
        "title": "Preregistration in practice matched hypothesis corpus",
        "publisher": "Open Science Framework",
        "year": "n.d.",
        "url": "https://osf.io/pqnvr/",
        "note": "Candidate preregistered-hypothesis/result corpus; local variable and duplicate audit pending.",
        "metadata_source": "manual",
    },
    "vanDenAkkerSelectiveHypothesis2023": {
        "entry_type": "article",
        "authors": "van den Akker, Olmo R. and van Assen, Marcel A. L. M. and Enting, Manon and de Jonge, Myrthe and Ong, How Hwee and Rueffer, Franziska and Schoenmakers, Martijn and Stoevenbelt, Andrea H. and Wicherts, Jelte M. and Bakker, Marjan",
        "title": "Selective Hypothesis Reporting in Psychology: Comparing Preregistrations and Corresponding Publications",
        "journal": "Advances in Methods and Practices in Psychological Science",
        "volume": "6",
        "number": "3",
        "pages": "25152459231187988",
        "year": "2023",
        "doi": "10.1177/25152459231187988",
        "url": "https://doi.org/10.1177/25152459231187988",
        "metadata_source": "manual",
    },
    "allenMehler2019OpenScience": {
        "entry_type": "article",
        "authors": "Allen, Christopher and Mehler, David M. A.",
        "title": "Open science challenges, benefits and tips in early career and beyond",
        "journal": "PLOS Biology",
        "volume": "17",
        "number": "5",
        "pages": "e3000246",
        "year": "2019",
        "doi": "10.1371/journal.pbio.3000246",
        "url": "https://doi.org/10.1371/journal.pbio.3000246",
        "metadata_source": "manual",
    },
    "manyClasses2Osf": {
        "entry_type": "misc",
        "title": "ManyClasses 2 OSF project",
        "publisher": "Open Science Framework",
        "year": "n.d.",
        "url": "https://osf.io/t5ma3/",
        "note": "Staged harvested source; classroom-field metric conversion remains pending.",
        "metadata_source": "manual",
    },
    "mediaPriming2017Dataverse": {
        "entry_type": "misc",
        "title": "Media priming direct replication Dataverse file",
        "publisher": "Harvard Dataverse",
        "year": "2017",
        "url": "https://dataverse.harvard.edu/dataset.xhtml?persistentId=doi:10.7910/DVN/ECGADO",
        "note": "Staged harvested source; effect-conversion policy remains unresolved.",
        "metadata_source": "manual",
    },
    "metaketaIRepo": {
        "entry_type": "misc",
        "title": "EGAP Metaketa I replication repository",
        "publisher": "GitHub",
        "year": "2019",
        "url": "https://github.com/egap/metaketa-i",
        "note": "Harvested field-experiment source used for one pooled PAP row; component/native rows remain staged.",
        "metadata_source": "manual",
    },
    "metaketaIIIProject": {
        "entry_type": "misc",
        "title": "EGAP Metaketa III OSF project",
        "publisher": "Open Science Framework",
        "year": "2021",
        "url": "https://osf.io/knje7/",
        "note": "Downloaded harvested field-experiment source used for one pooled standardized-index PAP row; component/native rows remain staged.",
        "metadata_source": "manual",
    },
    "metaketaIVProject": {
        "entry_type": "misc",
        "title": "EGAP Metaketa IV OSF project",
        "publisher": "Open Science Framework",
        "year": "2021",
        "url": "https://osf.io/tzy82/",
        "note": "Harvested field-experiment source used for one pooled standardized-index PAP row; component/native rows remain staged.",
        "metadata_source": "manual",
    },
    "tessPastStudiesArchive": {
        "entry_type": "misc",
        "title": "TESS past studies archive",
        "publisher": "Time-sharing Experiments for the Social Sciences",
        "year": "2026",
        "url": "https://tessexperiments.org/paststudies",
        "note": "Scraped as a Plot 3 political-science extraction queue; study-page index does not itself contain final D/N rows.",
        "metadata_source": "manual",
    },
    "mullinix2015Dataverse": {
        "entry_type": "misc",
        "title": "Mullinix Leeper Druckman Freese 2015 political science replication Dataverse",
        "publisher": "Harvard Dataverse",
        "year": "2015",
        "url": "https://dataverse.harvard.edu/dataverse/psrm",
        "note": "Companion TESS MTurk pair corpus; not promoted because current source rows use non-D metrics.",
        "metadata_source": "manual",
    },
    "musicianshipEegDataverse": {
        "entry_type": "misc",
        "title": "Musicianship EEG multi-site replication Dataverse",
        "publisher": "Harvard Dataverse",
        "year": "2025",
        "url": "https://dataverse.harvard.edu/dataset.xhtml?persistentId=doi:10.7910/DVN/SKOWNK",
        "note": "Staged harvested source; effect-extraction policy remains pending.",
        "metadata_source": "manual",
    },
    "newsDiscernmentReplicationOsf": {
        "entry_type": "misc",
        "title": "News discernment France Germany replication OSF project",
        "publisher": "Open Science Framework",
        "year": "n.d.",
        "url": "https://osf.io/mw4gu/",
        "note": "Harvested lead source; downloaded country workbooks and scripts are intervention datasets rather than a smaller-original larger-replication D/N pair table.",
        "metadata_source": "manual",
    },
    "nieuwland2018delong": {
        "entry_type": "article",
        "authors": "Nieuwland, Mante S. and Politzer-Ahles, Stephen and Heyselaar, Evelien and Segaert, Katrien and Darley, Emily and Kazanina, Nina and others",
        "title": "Large-scale replication study reveals a limit on probabilistic prediction in language comprehension",
        "journal": "eLife",
        "year": "2018",
        "volume": "7",
        "doi": "10.7554/eLife.33468",
        "url": "https://doi.org/10.7554/eLife.33468",
        "metadata_source": "manual",
    },
    "psa004TurriOsf": {
        "entry_type": "misc",
        "title": "PSA 004 JTB Turri OSF project",
        "publisher": "Open Science Framework",
        "year": "n.d.",
        "url": "https://osf.io/x978m/",
        "note": "Staged harvested Philosophy Science Association replication source; effect-conversion policy remains pending.",
        "metadata_source": "manual",
    },
    "wang2021psacr002": {
        "entry_type": "article",
        "authors": "Wang, Ke and Goldenberg, Amit and Dorison, Charles A. and others",
        "title": "A Multi-Country Test of Brief Reappraisal Interventions on Emotions During the COVID-19 Pandemic",
        "journal": "Nature Human Behaviour",
        "year": "2021",
        "volume": "5",
        "pages": "1089--1110",
        "doi": "10.1038/s41562-021-01173-x",
        "url": "https://doi.org/10.1038/s41562-021-01173-x",
        "metadata_source": "manual",
    },
    "hall2024psa004Turri": {
        "entry_type": "article",
        "authors": "Hall, Braeden and Schmidt, Kathleen and Wagge, Jordan and others",
        "title": "Registered Replication Report: A Large Multilab Cross-Cultural Conceptual Replication of Turri et al. (2015)",
        "journal": "Advances in Methods and Practices in Psychological Science",
        "year": "2024",
        "doi": "10.1177/25152459241267902",
        "url": "https://doi.org/10.1177/25152459241267902",
        "metadata_source": "manual",
    },
    "james2016publicAdminBlame": {
        "entry_type": "article",
        "authors": "James, Oliver and Jilke, Sebastian and Petersen, Carolyn and Van de Walle, Steven",
        "title": "Citizens' Blame of Politicians for Public Service Failure: Experimental Evidence about Blame Reduction through Delegation and Contracting",
        "journal": "Public Administration Review",
        "year": "2016",
        "volume": "76",
        "number": "1",
        "pages": "83--93",
        "doi": "10.1111/puar.12471",
        "url": "https://doi.org/10.1111/puar.12471",
        "metadata_source": "manual",
    },
    "walker2024publicAdminBlame": {
        "entry_type": "article",
        "authors": "Walker, Richard M. and James, Oliver and Moon, M. Jae and Wen, Wen",
        "title": "A cross-cultural replication of ``citizens' blame of politicians for public service failure: Experimental evidence about blame reduction through delegation and contracting''",
        "journal": "Public Administration Review",
        "year": "2024",
        "doi": "10.1111/puar.13845",
        "url": "https://doi.org/10.1111/puar.13845",
        "metadata_source": "manual",
    },
    "rrrColling2020Osf": {
        "entry_type": "article",
        "authors": "Colling, Lincoln J. and Szucs, Denes and De Marco, Daniela and Cipora, Krzysztof and Ulrich, Rolf and Nuerk, Hans-Christoph and Soltanlou, Mojtaba and Bryce, Donna and Chen, Sharlene Chia-Yin and Schroeder, Pia and Ansari, Daniel and Goffin, Caitlin and Sokolowski, H. Moriah and Hancock, Peter J. B. and Millen, Ailsa E. and Langton, Stephen R. H. and Holmes, Kevin J. and McCrink, Koleen and Castronovo, Julie and McShane, Blakeley B.",
        "title": "Registered Replication Report on Fischer, Castel, Dodd, and Pratt (2003)",
        "journal": "Advances in Methods and Practices in Psychological Science",
        "year": "2020",
        "doi": "10.1177/2515245920903079",
        "url": "https://doi.org/10.1177/2515245920903079",
        "metadata_source": "manual",
    },
    "selfControlFmriOsf": {
        "entry_type": "misc",
        "title": "Self control neuroimaging replication OSF project",
        "publisher": "Open Science Framework",
        "year": "2022",
        "url": "https://osf.io/qzyxm/",
        "note": "Staged harvested source; hypothesis-level effect mapping remains pending.",
        "metadata_source": "manual",
    },
    "strategyFitOsf": {
        "entry_type": "misc",
        "title": "Strategy situation fit replication OSF project",
        "publisher": "Open Science Framework",
        "year": "2025",
        "url": "https://osf.io/ap2ws/",
        "note": "Staged harvested source; effect-conversion policy remains pending.",
        "metadata_source": "manual",
    },
    "woodPorter2019Dataverse": {
        "entry_type": "misc",
        "authors": "Wood, Thomas and Porter, Ethan",
        "title": "Replication data for: The elusive backfire effect: mass attitudes' steadfast factual adherence",
        "publisher": "Harvard Dataverse",
        "year": "2019",
        "doi": "10.7910/DVN/AGRX5U",
        "url": "https://doi.org/10.7910/DVN/AGRX5U",
        "note": "Staged harvested source; strict direct subset requires hand pairing and current rows use non-D metrics.",
        "metadata_source": "manual",
    },
    "brodeur2020": {
        "entry_type": "article",
        "authors": "Brodeur, Abel and Cook, Nikolai and Heyes, Anthony",
        "title": "Methods Matter: p-Hacking and Publication Bias in Causal Analysis in Economics",
        "journal": "American Economic Review",
        "year": "2020",
        "volume": "110",
        "number": "11",
        "pages": "3634-3660",
        "doi": "10.1257/aer.20190687",
        "url": "https://doi.org/10.1257/aer.20190687",
        "metadata_source": "manual",
    },
    "esareyWu2016": {
        "entry_type": "article",
        "authors": "Esarey, Justin and Wu, Ahra",
        "title": "Measuring the Effects of Publication Bias in Political Science",
        "journal": "Research & Politics",
        "year": "2016",
        "volume": "3",
        "number": "3",
        "pages": "2053168016665856",
        "doi": "10.1177/2053168016665856",
        "url": "https://doi.org/10.1177/2053168016665856",
        "metadata_source": "manual",
    },
    "kuhberger2014publicationBias": {
        "entry_type": "article",
        "authors": "Kühberger, Anton and Fritz, Astrid and Scherndl, Thomas",
        "title": "Publication Bias in Psychology: A Diagnosis Based on the Correlation between Effect Size and Sample Size",
        "journal": "PLOS ONE",
        "year": "2014",
        "volume": "9",
        "number": "9",
        "pages": "e105825",
        "doi": "10.1371/journal.pone.0105825",
        "url": "https://doi.org/10.1371/journal.pone.0105825",
        "metadata_source": "manual",
    },
    "linden2024publicationBiasPsychology": {
        "entry_type": "article",
        "authors": "Linden, Audrey Helen and Pollet, Thomas V. and Hönekopp, Johannes",
        "title": "Publication Bias in Psychology: A Closer Look at the Correlation between Sample Size and Effect Size",
        "journal": "PLOS ONE",
        "year": "2024",
        "volume": "19",
        "number": "2",
        "pages": "e0297075",
        "doi": "10.1371/journal.pone.0297075",
        "url": "https://doi.org/10.1371/journal.pone.0297075",
        "metadata_source": "manual",
    },
    "motyl2017state": {
        "entry_type": "article",
        "authors": "Motyl, Matt and Demos, Alexander P. and Carsel, Timothy S. and Hanson, Brittany E. and Melton, Zachary J. and Mueller, Allison B. and Prims, J. P. and Sun, Jiaqing and Washburn, Anthony N. and Wong, Kendal M. and Yantis, Caitlyn and Skitka, Linda J.",
        "title": "The State of Social and Personality Science: Rotten to the Core, Not So Bad, Getting Better, or Getting Worse?",
        "journal": "Journal of Personality and Social Psychology",
        "year": "2017",
        "volume": "113",
        "number": "1",
        "pages": "34-58",
        "doi": "10.1037/pspa0000084",
        "url": "https://doi.org/10.1037/pspa0000084",
        "metadata_source": "manual",
    },
    "schaefer2019meaningfulness": {
        "entry_type": "article",
        "authors": "Schäfer, Thomas and Schwarz, Marcus A.",
        "title": "The Meaningfulness of Effect Sizes in Psychological Research: Differences Between Sub-Disciplines and the Impact of Potential Biases",
        "journal": "Frontiers in Psychology",
        "year": "2019",
        "volume": "10",
        "pages": "813",
        "doi": "10.3389/fpsyg.2019.00813",
        "url": "https://doi.org/10.3389/fpsyg.2019.00813",
        "metadata_source": "manual",
    },
    "olsson2023publicationBias": {
        "entry_type": "article",
        "authors": "Olsson, Tina M. and Sundell, Knut",
        "title": "Publication Bias, Time-Lag Bias, and Place-of-Publication Bias in Social Intervention Research: An Exploratory Study of 527 Swedish Articles Published between 1990-2019",
        "journal": "PLOS ONE",
        "year": "2023",
        "volume": "18",
        "number": "2",
        "pages": "e0281110",
        "doi": "10.1371/journal.pone.0281110",
        "url": "https://doi.org/10.1371/journal.pone.0281110",
        "metadata_source": "manual",
    },
    "zhang2025clinifact": {
        "entry_type": "article",
        "authors": "Zhang, Boya and Bornet, Alban and Yazdani, Anthony and Khlebnikov, Philipp and Milutinovic, Marija and Rouhizadeh, Hossein and Amini, Poorya and Teodoro, Douglas",
        "title": "A Dataset for Evaluating Clinical Research Claims in Large Language Models",
        "journal": "Scientific Data",
        "year": "2025",
        "volume": "12",
        "number": "1",
        "pages": "86",
        "doi": "10.1038/s41597-025-04417-x",
        "url": "https://doi.org/10.1038/s41597-025-04417-x",
        "metadata_source": "manual",
    },
    "havranekArmingtonData": {
        "entry_type": "article",
        "authors": "Bajzik, Josef and Havranek, Tomas and Irsova, Zuzana and Schwarz, Jiri",
        "title": "Estimating the Armington Elasticity: The Importance of Study Design and Publication Bias",
        "journal": "Journal of International Economics",
        "year": "2020",
        "volume": "127",
        "pages": "103383",
        "doi": "10.1016/j.jinteco.2020.103383",
        "url": "https://doi.org/10.1016/j.jinteco.2020.103383",
        "note": "Source data mirrored at https://meta-analysis.cz/armington/.",
        "metadata_source": "manual",
    },
    "havranekGasolineIncomeData": {
        "entry_type": "article",
        "authors": "Havranek, Tomas and Kokes, Ondrej",
        "title": "Income Elasticity of Gasoline Demand: A Meta-Analysis",
        "journal": "Energy Economics",
        "year": "2015",
        "volume": "47",
        "pages": "77-86",
        "doi": "10.1016/j.eneco.2014.11.004",
        "url": "https://doi.org/10.1016/j.eneco.2014.11.004",
        "note": "Source data mirrored at https://meta-analysis.cz/gasoline/.",
        "metadata_source": "manual",
    },
    "havranekFrischData": {
        "entry_type": "misc",
        "authors": "Elminejad, Ali and Havranek, Tomas and Horvath, Roman",
        "title": "Publication and Identification Biases in Measuring the Intertemporal Substitution of Labor Supply",
        "publisher": "EconStor",
        "year": "2021",
        "url": "https://hdl.handle.net/10419/232534",
        "note": "Working paper and source data mirrored at https://meta-analysis.cz/frisch/.",
        "metadata_source": "manual",
    },
}

SUPPLEMENTAL_PAPER_REFERENCE_KEYS = (
    "prasad2008",
    "petrie1989",
    "amaral2019brazilian",
    "bago2022trolley",
    "boyce2023studentreplication",
    "boyce2024rescue",
    "cova2021estimating",
    "davis2023managementscience",
    "du2024",
    "ebersole2016manylabs3",
    "holzmeister2025decisionmarket",
    "klein2014manylabs1",
    "klein2022manylabs4",
    "masur2025privacy",
    "protzko2024highrep",
    "soto2019loopr",
    "douglass2026appendixD",
    "douglass2026manualPairs",
    "peyton2021covidonline",
    "oppen2026contextual",
    "arroyoaraujo2022eqipd",
    "galak2012psi",
    "balakrishnan2017greed",
    "jinAwesomeReplicabilityData",
    "tonkovic2022linguisticOsf",
    "odonnell2018dijksterhuis",
    "chen2025objectOrientation",
    "alogna2014schooler",
    "bouwmeester2017rand",
    "cheung2016finkel",
    "elliott2021flavell",
    "hagger2016egodepletion",
    "mccarthy2018srull",
    "verschuere2018mazar",
    "ranehill2015powerposing",
    "murphy2025sportsReplication",
    "vaidis2024dissonance",
    "smit2025scaffolding",
    "ying2023pilot",
    "ioannidis2005contradicted",
    "eerland2016hart",
    "schweinsberg2016pipeline",
    "stoevenbelt2024johns",
    "kekecs2023tpp",
    "wagenmakers2016strack",
    "kleinberg2018deceptive",
    "haim2025imagecredibility",
    "luyten2017retrievalExtinction",
    "arelbundock2026underpowered",
    "bergmann2018metalab",
    "olivier2024cardioRcts",
    "yun2024llmExtraction",
    "bosco2020metabus",
    "brodeur2020",
    "esareyWu2016",
    "kuhberger2014publicationBias",
    "linden2024publicationBiasPsychology",
    "motyl2017state",
    "schaefer2019meaningfulness",
    "olsson2023publicationBias",
    "zhang2025clinifact",
    "havranekArmingtonData",
    "havranekGasolineIncomeData",
    "havranekFrischData",
    "i4rPublicWorkbook",
    "pooledMarketRPackageData",
    "angristLearningCurve2023Openicpsr",
    "coppock2019generalizability",
    "eefProjectsIndex",
    "ernPeRrrOpenNeuro",
    "eyewitnessTenCountriesOsf",
    "ito2018eyewitnessTenCountries",
    "iblReproEphysAws",
    "iesSystematicReplicationAwards",
    "klein2016independentReplicationInitiative",
    "jaljuliKafkafi2023MousePhenome",
    "manyBabies2020Ids",
    "byersHeinlein2021manybabiesBilingual",
    "manyBabies2AnalysisRepo",
    "manyBabies3Osf",
    "manyBabies4Project",
    "fyfe2021manyclasses1",
    "allenMehler2019OpenScience",
    "vanDenAkkerSelectiveHypothesis2023",
    "manyClasses2Osf",
    "mediaPriming2017Dataverse",
    "metaketaIRepo",
    "metaketaIIIProject",
    "metaketaIVProject",
    "tessPastStudiesArchive",
    "mullinix2015Dataverse",
    "musicianshipEegDataverse",
    "newsDiscernmentReplicationOsf",
    "nieuwland2018delong",
    "psa004TurriOsf",
    "wang2021psacr002",
    "hall2024psa004Turri",
    "vanDenAkkerPreregPractice",
    "james2016publicAdminBlame",
    "walker2024publicAdminBlame",
    "rrrColling2020Osf",
    "selfControlFmriOsf",
    "strategyFitOsf",
    "woodPorter2019Dataverse",
)


@dataclass
class BibEntry:
    key: str
    entry_type: str = "article"
    title: str = ""
    authors: str = ""
    year: str = ""
    journal: str = ""
    booktitle: str = ""
    publisher: str = ""
    volume: str = ""
    number: str = ""
    pages: str = ""
    doi: str = ""
    url: str = ""
    pmid: str = ""
    pmcid: str = ""
    note: str = ""
    metadata_source: str = "local"
    source_rows: set[str] = field(default_factory=set)
    crossref_score: float | None = None

    def merge(self, other: "BibEntry") -> None:
        """Fill blanks from a duplicate entry and union source notes."""
        for attr in [
            "title",
            "authors",
            "year",
            "journal",
            "booktitle",
            "publisher",
            "volume",
            "number",
            "pages",
            "doi",
            "url",
            "pmid",
            "pmcid",
            "note",
        ]:
            if not getattr(self, attr) and getattr(other, attr):
                setattr(self, attr, getattr(other, attr))
        if self.metadata_source in {"local", "local_placeholder"} and other.metadata_source not in {"local", "local_placeholder"}:
            self.metadata_source = other.metadata_source
        elif self.metadata_source == "local_placeholder" and other.metadata_source == "local":
            self.metadata_source = "local"
        if self.crossref_score is None and other.crossref_score is not None:
            self.crossref_score = other.crossref_score
        self.source_rows.update(other.source_rows)


def ensure_dirs() -> None:
    for path in [BIB_DIR, CROSSREF_DIR, EUROPEPMC_DIR]:
        path.mkdir(parents=True, exist_ok=True)


def clean_text(value: object) -> str:
    if value is None or pd.isna(value):
        return ""
    text = str(value).replace("\xa0", " ")
    return WHITESPACE_RE.sub(" ", text).strip()


def as_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if value is None or pd.isna(value):
        return False
    text = clean_text(value).lower()
    return text in {"true", "1", "yes", "y", "t"}


def tagged_identifier(tag: str, *values: object) -> str:
    pattern = re.compile(rf"(?i)\b{re.escape(tag)}\s*:\s*([A-Z0-9._/-]+)")
    for value in values:
        text = clean_text(value)
        if not text:
            continue
        match = pattern.search(text)
        if match:
            return match.group(1)
    return ""


def extract_pmid(*values: object) -> str:
    return tagged_identifier("PMID", *values)


def extract_pmcid(*values: object) -> str:
    pmcid = tagged_identifier("PMCID", *values)
    if pmcid and pmcid.isdigit():
        return f"PMC{pmcid}"
    return pmcid


def compact_year(value: object) -> str:
    year = clean_text(value)
    if year.endswith(".0"):
        year = year[:-2]
    return year


def page_start(page_text: object) -> str:
    text = clean_text(page_text)
    match = re.search(r"\d+", text)
    return match.group(0) if match else ""


def statcheck_paper_id(value: object) -> str:
    source_id = compact_year(value)
    return f"statcheck_{source_id}" if source_id else ""


def statcheck_published_lookup() -> dict[str, set[tuple[str, str]]]:
    if not STATCHECK_PAPERS.exists():
        return {}
    df = pd.read_csv(STATCHECK_PAPERS, usecols=["paper_id", "journal", "year"]).fillna("")
    lookup: dict[str, set[tuple[str, str]]] = {}
    for row in df.to_dict("records"):
        paper_id = clean_text(row.get("paper_id"))
        if not paper_id:
            continue
        journal_code = clean_text(row.get("journal"))
        year = compact_year(row.get("year"))
        lookup.setdefault(paper_id, set()).add((journal_code, year))
    return lookup


def statcheck_source_multiplicity() -> dict[str, int]:
    if not STATCHECK_RAW.exists():
        return {}
    raw = pd.read_csv(
        STATCHECK_RAW,
        sep=";",
        encoding="latin1",
        usecols=["Source", "journals.jour.", "years.y."],
    ).drop_duplicates()
    counts: dict[str, int] = {}
    for row in raw.to_dict("records"):
        base_id = statcheck_paper_id(row.get("Source"))
        if base_id:
            counts[base_id] = counts.get(base_id, 0) + 1
    return counts


def statcheck_inventory_paper_id(
    source_id: object,
    journal_code: object,
    year: object,
    published_lookup: dict[str, set[tuple[str, str]]],
    multiplicity: dict[str, int],
) -> str:
    base_id = statcheck_paper_id(source_id)
    journal = clean_text(journal_code)
    year_text = compact_year(year)
    if not base_id:
        return ""
    if multiplicity.get(base_id, 0) <= 1:
        return base_id
    if (journal, year_text) in published_lookup.get(base_id, set()):
        return base_id
    suffix = "_".join(part for part in [slugify(journal.lower(), "journal", 12), year_text or "unknown"] if part)
    return f"{base_id}_{suffix}"


def normalize_statcheck_raw(value: object) -> str:
    return clean_text(value).strip('"')


def statcheck_signature(raw_values: Iterable[object]) -> str:
    normalized = sorted(value for value in (normalize_statcheck_raw(raw) for raw in raw_values) if value)
    return hashlib.sha1("\n".join(normalized).encode("utf-8")).hexdigest() if normalized else ""


def statcheck_paper_id_from_entry(entry: BibEntry) -> str:
    for source_row in entry.source_rows:
        if source_row.startswith("psychology_statcheck:"):
            return source_row.split(":", 1)[1]
    match = re.search(r"\bstatcheck_\d+\b", entry.title)
    if match:
        return match.group(0)
    match = re.match(r"^statcheck_(statcheck_\d+)(?:_\d+)?$", entry.key)
    return match.group(1) if match else ""


def parse_metabus_article_id(article_id: object) -> dict[str, str]:
    text = clean_text(article_id)
    match = METABUS_ARTICLE_ID_RE.search(text)
    if not match:
        return {}
    journal_code = match.group("journal")
    return {
        "article_id": text,
        "journal_code": journal_code,
        "journal": METABUS_JOURNALS.get(journal_code, journal_code),
        "volume": match.group("volume"),
        "issue": match.group("issue"),
        "page": match.group("page"),
    }


def entry_has_source(entry: BibEntry, prefixes: Iterable[str]) -> bool:
    return any(source_row == prefix or source_row.startswith(prefix + ":") for source_row in entry.source_rows for prefix in prefixes)


def strip_doi_punctuation(doi: str) -> str:
    doi = clean_text(doi)
    doi = re.sub(r"(?i)^doi:\s*", "", doi)
    doi = re.sub(r"(?i)^https?://(?:dx\.)?doi\.org/", "", doi)
    doi = doi.strip().rstrip(".,;)")
    while doi.count("(") < doi.count(")") and doi.endswith(")"):
        doi = doi[:-1]
    return doi


def extract_doi(*values: object) -> str:
    for value in values:
        text = clean_text(value)
        if not text:
            continue
        match = DOI_RE.search(text)
        if match:
            return strip_doi_punctuation(match.group(1))
    return ""


def first_year(*values: object) -> str:
    for value in values:
        text = clean_text(value)
        match = YEAR_RE.search(text)
        if match:
            return match.group(0)[:4]
    return ""


def slugify(value: str, fallback: str = "entry", max_len: int = 72) -> str:
    value = clean_text(value).lower()
    value = re.sub(r"[^a-z0-9]+", "_", value).strip("_")
    value = re.sub(r"_+", "_", value)
    return (value[:max_len].strip("_") or fallback).replace("__", "_")


def normalize_title(value: str) -> str:
    value = clean_text(value).lower()
    value = re.sub(r"https?://\S+", "", value)
    value = DOI_RE.sub("", value)
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return WHITESPACE_RE.sub(" ", value).strip()


def similarity(a: str, b: str) -> float:
    a_norm = normalize_title(a)
    b_norm = normalize_title(b)
    if not a_norm or not b_norm:
        return 0.0
    return SequenceMatcher(None, a_norm, b_norm).ratio()


def title_tokens(value: str) -> set[str]:
    return {token for token in normalize_title(value).split() if len(token) > 2 and token not in TITLE_STOPWORDS}


def crossref_match_score(entry: BibEntry, item: dict) -> float:
    candidate_title = " ".join(item.get("title") or [])
    title_score = similarity(entry.title, candidate_title)
    entry_tokens = title_tokens(entry.title)
    candidate_tokens = title_tokens(candidate_title)
    if entry_tokens and candidate_tokens:
        containment = len(entry_tokens & candidate_tokens) / min(len(entry_tokens), len(candidate_tokens))
        title_score = max(title_score, 0.82 * containment)

    bonus = 0.0
    item_year = issued_year(item)
    if entry.year and item_year and entry.year == item_year:
        bonus += 0.05
    entry_authors = clean_text(entry.authors).lower()
    for author in item.get("author") or []:
        family = clean_text(author.get("family")).lower()
        if family and family in entry_authors:
            bonus += 0.08
            break
    entry_journal = normalize_title(entry.journal)
    item_journal = normalize_title(" ".join(item.get("container-title") or []))
    if entry_journal and item_journal and (entry_journal in item_journal or item_journal in entry_journal):
        bonus += 0.05
    return min(1.0, title_score + bonus)


def text_of(node) -> str:
    return " ".join(node.get_text(" ", strip=True).split())


def parse_author_literals(author_text: str) -> str:
    author_text = re.sub(r"\bet al\.?$", "and others", clean_text(author_text), flags=re.I)
    author_text = author_text.replace(" & ", " and ")
    author_text = re.sub(r"\s*,\s*and\s+", " and ", author_text)
    return author_text.strip(" .")


def parse_rendered_reference(entry) -> BibEntry:
    """Parse one rendered CSL entry as a local fallback."""
    citekey = entry.get("id", "").replace("ref-", "", 1)
    clone = BeautifulSoup(str(entry), "html.parser")
    for backlink in clone.select(".backlink"):
        backlink.decompose()
    right = clone.select_one(".csl-right-inline") or clone
    full = text_of(right)
    full = re.sub(r"\s*↩\s*$", "", full).strip()

    year = first_year(full)
    year_match = re.search(r"\((\d{4}[a-z]?)\)", full)
    before_year = full[: year_match.start()].strip(" .") if year_match else ""
    after_year = full[year_match.end() :].strip(" .") if year_match else full
    container = text_of(right.find("em")) if right.find("em") else ""
    doi = extract_doi(full, *[a.get("href", "") for a in right.find_all("a", href=True)])
    url = ""
    for link in right.find_all("a", href=True):
        href = clean_text(link["href"])
        if href.startswith("http") and "doi.org/" not in href:
            url = href
            break

    title = after_year
    if container and container in title:
        title = title.split(container, 1)[0].strip(" .")
    title = DOI_RE.sub("", title).strip(" .")
    return BibEntry(
        key=citekey,
        entry_type="article" if container else "misc",
        title=title or full or citekey,
        authors=parse_author_literals(before_year),
        year=year,
        journal=container,
        doi=doi,
        url=f"https://doi.org/{doi}" if doi else url,
        note=full,
        metadata_source="draft_html",
    )


def parse_draft_references() -> list[BibEntry]:
    soup = BeautifulSoup(DRAFT_HTML.read_text(encoding="utf-8"), "html.parser")
    entries = [parse_rendered_reference(entry) for entry in soup.select("div.csl-entry")]
    deduped: dict[str, BibEntry] = {}
    for entry in entries:
        if entry.key not in deduped:
            deduped[entry.key] = entry
    for key in SUPPLEMENTAL_PAPER_REFERENCE_KEYS:
        if key not in deduped:
            fields = MANUAL_PAPER_OVERRIDES[key]
            deduped[key] = BibEntry(key=key, **{field: value for field, value in fields.items() if field != "metadata_source"})
    return list(deduped.values())


def cache_path(prefix: str, value: str, cache_dir: Path = CROSSREF_DIR) -> Path:
    digest = hashlib.sha1(value.encode("utf-8")).hexdigest()
    return cache_dir / f"{prefix}_{digest}.json"


def request_json_cached(
    url: str,
    params: dict[str, object] | None,
    refresh: bool,
    cache_dir: Path,
    prefix: str,
    cache_key: str,
    headers: dict[str, str] | None = None,
) -> dict | None:
    path = cache_path(prefix, cache_key, cache_dir=cache_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and not refresh:
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return None
    if not refresh:
        return None
    try:
        response = requests.get(url, params=params, headers=headers, timeout=20)
        if response.status_code == 404:
            return None
        response.raise_for_status()
        data = response.json()
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        time.sleep(0.06)
        return data
    except requests.RequestException:
        return None


def request_crossref(url: str, params: dict[str, object] | None, refresh: bool, cache_key: str) -> dict | None:
    return request_json_cached(
        url,
        params,
        refresh,
        cache_dir=CROSSREF_DIR,
        prefix="crossref",
        cache_key=cache_key,
        headers={"User-Agent": "PublishedSmallNStudiesDontMatter bibliography builder (mailto:metadata@example.invalid)"},
    )


def crossref_by_doi(doi: str, refresh: bool) -> dict | None:
    doi = strip_doi_punctuation(doi)
    if not doi:
        return None
    url = f"https://api.crossref.org/works/{requests.utils.quote(doi, safe='')}"
    data = request_crossref(url, None, refresh, f"doi:{doi.lower()}")
    if data and isinstance(data.get("message"), dict):
        return data["message"]
    return None


def crossref_by_title(entry: BibEntry, refresh: bool) -> tuple[dict | None, float | None]:
    query_parts = [entry.title, entry.authors, entry.year]
    query = " ".join(part for part in query_parts if part)
    if not query.strip():
        return None, None
    common_select = "DOI,title,author,issued,published-print,published-online,container-title,volume,issue,page,type,URL,publisher,score"
    params = {
        "query.bibliographic": query,
        "rows": 5,
        "select": common_select,
    }
    data = request_crossref("https://api.crossref.org/works", params, refresh, f"title:{query}")
    items = (((data or {}).get("message") or {}).get("items") or []) if isinstance(data, dict) else []
    title_params = {
        "query.title": entry.title,
        "rows": 8,
        "select": common_select,
    }
    title_data = request_crossref("https://api.crossref.org/works", title_params, refresh, f"title-only:{entry.title}")
    items.extend((((title_data or {}).get("message") or {}).get("items") or []) if isinstance(title_data, dict) else [])
    best: tuple[dict | None, float] = (None, 0.0)
    for item in items:
        score = crossref_match_score(entry, item)
        if entry.year:
            item_year = issued_year(item)
            if item_year and item_year != entry.year:
                score -= 0.10
        if score > best[1]:
            best = (item, score)
    if best[0] is not None and best[1] >= 0.78:
        return best[0], best[1]
    return None, best[1] if best[0] is not None else None


def issued_year(item: dict) -> str:
    for key in ["issued", "published-print", "published-online"]:
        date_parts = ((item.get(key) or {}).get("date-parts") or [])
        if date_parts and date_parts[0]:
            return str(date_parts[0][0])
    return ""


def crossref_authors(authors: list[dict]) -> str:
    names: list[str] = []
    for author in authors or []:
        family = clean_text(author.get("family"))
        given = clean_text(author.get("given"))
        literal = clean_text(author.get("name"))
        if family and given:
            names.append(f"{family}, {given}")
        elif family:
            names.append(family)
        elif literal:
            names.append(literal)
    return " and ".join(names)


def entry_from_crossref(base_key: str, item: dict, score: float | None = None) -> BibEntry:
    title = " ".join(item.get("title") or [])
    container = " ".join(item.get("container-title") or [])
    item_type = clean_text(item.get("type"))
    entry_type = "article" if "journal" in item_type or container else "misc"
    if "book" in item_type and "chapter" not in item_type:
        entry_type = "book"
    elif "proceedings" in item_type or "conference" in item_type:
        entry_type = "inproceedings"
    doi = strip_doi_punctuation(clean_text(item.get("DOI")))
    return BibEntry(
        key=base_key,
        entry_type=entry_type,
        title=title,
        authors=crossref_authors(item.get("author") or []),
        year=issued_year(item),
        journal=container if entry_type == "article" else "",
        booktitle=container if entry_type == "inproceedings" else "",
        publisher=clean_text(item.get("publisher")),
        volume=clean_text(item.get("volume")),
        number=clean_text(item.get("issue")),
        pages=clean_text(item.get("page")),
        doi=doi,
        url=clean_text(item.get("URL")) or (f"https://doi.org/{doi}" if doi else ""),
        metadata_source="crossref",
        crossref_score=score,
    )


def request_europepmc(params: dict[str, object], refresh: bool, cache_key: str) -> dict | None:
    return request_json_cached(
        "https://www.ebi.ac.uk/europepmc/webservices/rest/search",
        params,
        refresh,
        cache_dir=EUROPEPMC_DIR,
        prefix="europepmc",
        cache_key=cache_key,
    )


def europepmc_by_pmcid(pmcid: str, refresh: bool) -> dict | None:
    pmcid = clean_text(pmcid).upper()
    if not pmcid:
        return None
    if not pmcid.startswith("PMC"):
        pmcid = f"PMC{pmcid}"
    data = request_europepmc({"query": f"PMCID:{pmcid}", "format": "json", "pageSize": 1}, refresh, f"pmcid:{pmcid}")
    results = ((((data or {}).get("resultList") or {}).get("result")) or []) if isinstance(data, dict) else []
    return results[0] if results else None


def parse_author_string(author_text: str) -> str:
    names: list[str] = []
    for chunk in clean_text(author_text).rstrip(".").split(","):
        piece = clean_text(chunk)
        if not piece:
            continue
        parts = piece.split()
        if len(parts) >= 2:
            family = " ".join(parts[:-1])
            given = parts[-1].rstrip(".")
            names.append(f"{family}, {given}")
        else:
            names.append(piece)
    return " and ".join(names)


def entry_from_europepmc(base_key: str, item: dict) -> BibEntry:
    doi = strip_doi_punctuation(clean_text(item.get("doi")))
    pmcid = clean_text(item.get("pmcid")).upper()
    if pmcid and not pmcid.startswith("PMC"):
        pmcid = f"PMC{pmcid}"
    return BibEntry(
        key=base_key,
        entry_type="article",
        title=clean_text(item.get("title")),
        authors=parse_author_string(clean_text(item.get("authorString"))),
        year=clean_text(item.get("pubYear")),
        journal=clean_text(item.get("journalTitle")),
        volume=clean_text(item.get("journalVolume")),
        pages=clean_text(item.get("pageInfo")),
        doi=doi,
        url=f"https://doi.org/{doi}" if doi else f"https://pmc.ncbi.nlm.nih.gov/articles/{pmcid}/" if pmcid else "",
        pmid=clean_text(item.get("pmid")),
        pmcid=pmcid,
        metadata_source="europepmc",
    )


def ensure_statcheck_hartgerink_dataset() -> bool:
    if STATCHECK_HARTGERINK_DATASET.exists():
        return True
    STATCHECK_HARTGERINK_DATASET.parent.mkdir(parents=True, exist_ok=True)
    try:
        response = requests.get(STATCHECK_HARTGERINK_URL, stream=True, timeout=30)
        response.raise_for_status()
        with STATCHECK_HARTGERINK_DATASET.open("wb") as handle:
            for chunk in response.iter_content(chunk_size=1 << 20):
                if chunk:
                    handle.write(chunk)
        return True
    except requests.RequestException:
        return False


def parse_hartgerink_authors(author_text: object, author_count: object = "") -> str:
    text = clean_text(author_text).strip("[]")
    if not text:
        return ""
    tokens = text.split()
    expected = 0
    try:
        expected = int(float(clean_text(author_count)))
    except ValueError:
        expected = 0
    if expected <= 1:
        return f"{tokens[-1]}, {' '.join(tokens[:-1])}".strip(", ") if len(tokens) >= 2 else text
    if expected > len(tokens):
        return ""

    def segment_score(segment: list[str]) -> float:
        if len(segment) < 2 or len(segment) > 4:
            return -1e9
        if segment[-1].endswith("."):
            return -1e9
        score = 6.0 - abs(len(segment) - 3)
        for token in segment[:-1]:
            if token.endswith("."):
                score += 0.4
            elif token[0].isupper():
                score += 0.1
        return score

    @lru_cache(maxsize=None)
    def solve(index: int, remaining: int) -> tuple[float, tuple[tuple[str, ...], ...]] | None:
        if remaining == 0:
            return (0.0, ()) if index == len(tokens) else None
        best: tuple[float, tuple[tuple[str, ...], ...]] | None = None
        for width in range(2, 5):
            end = index + width
            if end > len(tokens):
                break
            remaining_tokens = len(tokens) - end
            if remaining_tokens < 2 * (remaining - 1) or remaining_tokens > 4 * (remaining - 1):
                continue
            segment = tokens[index:end]
            tail = solve(end, remaining - 1)
            if tail is None:
                continue
            total_score = segment_score(segment) + tail[0]
            if best is None or total_score > best[0]:
                best = (total_score, (tuple(segment),) + tail[1])
        return best

    solved = solve(0, expected)
    if solved is None:
        return ""
    names: list[str] = []
    for segment in solved[1]:
        family = segment[-1]
        given = " ".join(segment[:-1])
        names.append(f"{family}, {given}")
    return " and ".join(names)


def load_statcheck_exact_match_lookup(refresh: bool) -> dict[str, dict[str, str]]:
    if STATCHECK_EXACT_MATCHES.exists() and not refresh:
        cached = pd.read_csv(STATCHECK_EXACT_MATCHES).fillna("")
        return {clean_text(row["paper_id"]): row for row in cached.to_dict("records") if clean_text(row.get("paper_id"))}
    if not STATCHECK_RAW.exists() or not ensure_statcheck_hartgerink_dataset():
        return {}
    published_lookup = statcheck_published_lookup()
    multiplicity = statcheck_source_multiplicity()

    local = pd.read_csv(
        STATCHECK_RAW,
        sep=";",
        encoding="latin1",
        usecols=["Source", "Raw", "journals.jour.", "years.y."],
    )
    local = local[local["journals.jour."].isin(STATCHECK_JOURNALS)].copy()
    local["paper_id"] = local.apply(
        lambda row: statcheck_inventory_paper_id(
            row["Source"],
            row["journals.jour."],
            row["years.y."],
            published_lookup,
            multiplicity,
        ),
        axis=1,
    )
    local["year"] = local["years.y."].map(compact_year)
    local["journal"] = local["journals.jour."].map(STATCHECK_JOURNALS)
    local["Raw"] = local["Raw"].map(normalize_statcheck_raw)
    local_groups = (
        local.groupby(["paper_id", "journal", "year"], dropna=False)["Raw"]
        .apply(list)
        .reset_index(name="raw_values")
    )
    local_groups["signature"] = local_groups["raw_values"].map(statcheck_signature)
    local_groups["n_tests"] = local_groups["raw_values"].map(len)

    hartgerink = pd.read_csv(
        STATCHECK_HARTGERINK_DATASET,
        sep="\t",
        usecols=["Source", "Raw", "journal", "year", "title", "authors", "author_count"],
        dtype=str,
    )
    hartgerink = hartgerink[hartgerink["journal"].isin(set(STATCHECK_JOURNALS.values()))].copy()
    hartgerink["year"] = hartgerink["year"].map(compact_year)
    hartgerink["Raw"] = hartgerink["Raw"].map(normalize_statcheck_raw)
    hart_groups = (
        hartgerink.groupby(["journal", "year", "Source", "title", "authors", "author_count"], dropna=False)["Raw"]
        .apply(list)
        .reset_index(name="raw_values")
    )
    hart_groups["signature"] = hart_groups["raw_values"].map(statcheck_signature)
    hart_groups["n_tests"] = hart_groups["raw_values"].map(len)

    signature_lookup: dict[tuple[str, str, str], list[dict[str, str]]] = {}
    for row in hart_groups.to_dict("records"):
        key = (clean_text(row.get("journal")), clean_text(row.get("year")), clean_text(row.get("signature")))
        signature_lookup.setdefault(key, []).append(row)

    matches: list[dict[str, object]] = []
    for row in local_groups.to_dict("records"):
        key = (clean_text(row.get("journal")), clean_text(row.get("year")), clean_text(row.get("signature")))
        hits = signature_lookup.get(key, [])
        if len(hits) != 1:
            continue
        hit = hits[0]
        matches.append(
            {
                "paper_id": clean_text(row.get("paper_id")),
                "journal": clean_text(row.get("journal")),
                "year": clean_text(row.get("year")),
                "doi": strip_doi_punctuation(clean_text(hit.get("Source"))),
                "title": clean_text(hit.get("title")),
                "authors_raw": clean_text(hit.get("authors")),
                "author_count": clean_text(hit.get("author_count")),
                "n_tests": row.get("n_tests", ""),
                "match_method": "exact_raw_signature",
            }
        )
    write_csv(STATCHECK_EXACT_MATCHES, matches)
    return {clean_text(row["paper_id"]): row for row in matches if clean_text(row.get("paper_id"))}


def entry_from_statcheck_match(base_key: str, match: dict[str, str]) -> BibEntry:
    doi = strip_doi_punctuation(clean_text(match.get("doi")))
    crossref_item = crossref_by_doi(doi, refresh=False) if doi else None
    if crossref_item is not None:
        entry = entry_from_crossref(base_key, crossref_item, 1.0)
    else:
        entry = BibEntry(
            key=base_key,
            entry_type="article",
            title=clean_text(match.get("title")) or doi,
            authors=parse_hartgerink_authors(match.get("authors_raw"), match.get("author_count")),
            year=clean_text(match.get("year")),
            journal=clean_text(match.get("journal")),
            doi=doi,
            url=f"https://doi.org/{doi}" if doi else "",
            metadata_source="hartgerink_statcheck",
            note="Matched to Hartgerink statcheck metadata via exact raw-stat signature.",
            source_rows={"hartgerink_statcheck_exact"},
        )
    entry.source_rows.add("hartgerink_statcheck_exact")
    return entry


def crossref_match_score_from_biblio(
    item: dict,
    journal: str,
    year: str,
    volume: str,
    issue: str,
    first_page: str,
) -> float:
    score = 0.0
    item_journal = normalize_title(" ".join(item.get("container-title") or []))
    if normalize_title(journal) == item_journal:
        score += 0.45
    elif normalize_title(journal) and item_journal and normalize_title(journal) in item_journal:
        score += 0.30
    if year and issued_year(item) == year:
        score += 0.15
    if volume and clean_text(item.get("volume")) == volume:
        score += 0.15
    if issue and clean_text(item.get("issue")) == issue:
        score += 0.10
    if first_page and page_start(item.get("page")) == first_page:
        score += 0.20
    return min(1.0, score)


def crossref_by_metabus_article(article_id: str, year: str, refresh: bool) -> tuple[dict | None, float | None]:
    info = parse_metabus_article_id(article_id)
    if not info:
        return None, None
    query = f"\"{info['journal']}\" {info['volume']} {info['issue']} {info['page']} {year}"
    params = {
        "query.bibliographic": query,
        "rows": 5,
        "select": "DOI,title,author,issued,published-print,published-online,container-title,volume,issue,page,type,URL,publisher,score",
    }
    data = request_crossref("https://api.crossref.org/works", params, refresh, f"metabus:{article_id}:{year}")
    items = (((data or {}).get("message") or {}).get("items") or []) if isinstance(data, dict) else []
    best: tuple[dict | None, float] = (None, 0.0)
    for item in items:
        score = crossref_match_score_from_biblio(item, info["journal"], year, info["volume"], info["issue"], info["page"])
        if score > best[1]:
            best = (item, score)
    if best[0] is not None and best[1] >= 0.80:
        return best[0], best[1]
    return None, best[1] if best[0] is not None else None


def enrich_paper_references(entries: list[BibEntry], refresh: bool) -> list[BibEntry]:
    enriched: list[BibEntry] = []
    for entry in entries:
        item = crossref_by_doi(entry.doi, refresh) if entry.doi else None
        score: float | None = 1.0 if item is not None else None
        if item is None:
            item, score = crossref_by_title(entry, refresh)
        if item is not None:
            crossref_entry = entry_from_crossref(entry.key, item, score)
            crossref_entry.note = entry.note
            entry.merge(crossref_entry)
            # Prefer Crossref's structured title/authors/container when present.
            for attr in ["entry_type", "title", "authors", "year", "journal", "booktitle", "publisher", "volume", "number", "pages", "doi", "url"]:
                value = getattr(crossref_entry, attr)
                if value:
                    setattr(entry, attr, value)
            entry.metadata_source = "crossref"
            entry.crossref_score = score
        enriched.append(entry)
    return enriched


def apply_manual_paper_overrides(entries: list[BibEntry]) -> list[BibEntry]:
    for entry in entries:
        override = MANUAL_PAPER_OVERRIDES.get(entry.key)
        if override:
            for attr, value in override.items():
                setattr(entry, attr, value)

        if entry.key == "klein2018" and not entry.authors:
            entry.authors = "Klein, Richard A. and others"
        if entry.key == "jonas2015" and not entry.authors:
            entry.authors = "Jonas, Wayne B. and others"
        if entry.key == "sethuraman2011" and not entry.authors:
            entry.authors = "Sethuraman, Raj and Tellis, Gerard J. and Briesch, Richard A."

        # Clean up obvious residuals from rendered-reference parsing.
        if entry.entry_type == "article" and entry.journal.endswith(").") and entry.title.endswith(entry.journal[:-1]):
            entry.title = entry.title[: -len(entry.journal[:-1])].strip(" .,:;")
        if entry.entry_type in {"techreport", "book", "misc"}:
            entry.journal = ""
        if entry.entry_type == "book":
            entry.booktitle = ""
        if entry.entry_type == "misc" and not entry.url and entry.doi:
            entry.url = f"https://doi.org/{entry.doi}"
    return entries


def bibtex_escape(value: object) -> str:
    text = clean_text(value)
    text = text.replace("\\", "\\textbackslash{}")
    replacements = {
        "{": "\\{",
        "}": "\\}",
        "&": "\\&",
        "%": "\\%",
        "$": "\\$",
        "#": "\\#",
        "_": "\\_",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text


def bibtex_entry(entry: BibEntry) -> str:
    fields = [
        ("author", entry.authors),
        ("title", entry.title),
        ("journal", entry.journal),
        ("booktitle", entry.booktitle),
        ("publisher", entry.publisher),
        ("year", entry.year),
        ("volume", entry.volume),
        ("number", entry.number),
        ("pages", entry.pages),
        ("doi", entry.doi),
        ("url", entry.url),
        ("pmid", entry.pmid),
        ("pmcid", entry.pmcid),
        ("note", entry.note if entry.metadata_source != "crossref" else ""),
        ("keywords", "; ".join(sorted(entry.source_rows))),
    ]
    rendered = [f"@{entry.entry_type}{{{entry.key},"]
    for field_name, value in fields:
        if field_name == "author" and clean_text(value).startswith("literal:"):
            value_text = "{" + clean_text(value).removeprefix("literal:") + "}"
        else:
            value_text = bibtex_escape(value)
        if value_text:
            rendered.append(f"  {field_name} = {{{value_text}}},")
    if rendered[-1].endswith(","):
        rendered[-1] = rendered[-1][:-1]
    rendered.append("}")
    return "\n".join(rendered)


def write_bib(path: Path, entries: Iterable[BibEntry]) -> None:
    path.write_text("\n\n".join(bibtex_entry(entry) for entry in entries) + "\n", encoding="utf-8")


def entries_to_rows(entries: Iterable[BibEntry]) -> list[dict[str, object]]:
    rows = []
    for entry in entries:
        rows.append(
            {
                "key": entry.key,
                "entry_type": entry.entry_type,
                "title": entry.title,
                "authors": entry.authors,
                "year": entry.year,
                "journal": entry.journal,
                "volume": entry.volume,
                "number": entry.number,
                "pages": entry.pages,
                "doi": entry.doi,
                "url": entry.url,
                "pmid": entry.pmid,
                "pmcid": entry.pmcid,
                "metadata_source": entry.metadata_source,
                "crossref_score": entry.crossref_score,
                "source_rows": "; ".join(sorted(entry.source_rows)),
            }
        )
    return rows


def parse_citation_like_title(text: str) -> tuple[str, str, str, str]:
    """Return authors, year, title, journal from common APA-ish strings."""
    text = clean_text(text)
    text = DOI_RE.sub("", text).strip(" .")
    year = first_year(text)
    authors = ""
    title = text
    journal = ""
    match = re.match(r"^(?P<authors>.+?)\s*\((?P<year>\d{4}[a-z]?)\)\.\s*(?P<rest>.+)$", text)
    if match:
        authors = parse_author_literals(match.group("authors"))
        year = match.group("year")[:4]
        rest = match.group("rest")
        parts = [part.strip() for part in re.split(r"\.\s+", rest, maxsplit=2) if part.strip()]
        if parts:
            title = parts[0].strip(" .")
        if len(parts) > 1:
            journal = parts[1].strip(" .")
    return authors, year, title, journal


def local_entry_key(prefix: str, *parts: object) -> str:
    raw = "_".join(clean_text(part) for part in parts if clean_text(part))
    base = slugify(raw, prefix, max_len=90)
    return f"{slugify(prefix, 'corpus', 24)}_{base}"


def add_entry(entries: dict[str, BibEntry], entry: BibEntry) -> None:
    identity = entry.doi.lower() if entry.doi else normalize_title(entry.title) + "|" + entry.year
    if not identity.strip("|"):
        identity = entry.key
    index = IDENTITY_INDEX.setdefault(id(entries), {})
    if not index and entries:
        for key, current in entries.items():
            current_identity = current.doi.lower() if current.doi else normalize_title(current.title) + "|" + current.year
            index[current_identity] = key
    existing_key = index.get(identity)
    if existing_key:
        entries[existing_key].merge(entry)
        return
    original_key = entry.key
    suffix = 2
    while entry.key in entries:
        entry.key = f"{original_key}_{suffix}"
        suffix += 1
    entries[entry.key] = entry
    index[identity] = entry.key


def placeholder_title(source_name: str, unit_id: str, year: str = "", journal: str = "") -> str:
    parts = [f"[Unresolved local metadata] {source_name}", unit_id]
    if journal:
        parts.append(journal)
    if year:
        parts.append(year)
    return " | ".join(part for part in parts if part)


def candidate_entry_from_row(row, row_source: str) -> BibEntry | None:
    source_corpus = clean_text(getattr(row, "source_corpus", ""))
    unit_id = clean_text(getattr(row, "unit_id", ""))
    title_raw = clean_text(getattr(row, "title", ""))
    journal_raw = clean_text(getattr(row, "journal", ""))
    year_raw = compact_year(getattr(row, "year", ""))
    title_is_placeholder = not bool(title_raw)

    if title_raw:
        authors, parsed_year, parsed_title, parsed_journal = parse_citation_like_title(title_raw)
        title = parsed_title or title_raw
        year = year_raw or parsed_year
        journal = journal_raw or parsed_journal
    else:
        authors = ""
        year = year_raw
        journal = journal_raw
        title = placeholder_title(source_corpus or row_source, unit_id or "unknown_unit", year, journal)

    doi = extract_doi(title_raw, unit_id)
    pmid = extract_pmid(title_raw, unit_id)
    pmcid = extract_pmcid(title_raw, unit_id)
    key = local_entry_key("corpus", source_corpus or row_source, unit_id, title[:40])
    entry_type = "article" if journal or year or pmid or pmcid or doi else "misc"
    source_rows = {f"{row_source}:{source_corpus or 'unknown'}"}
    if title_is_placeholder:
        source_rows.add(f"{row_source}_untitled:{source_corpus or 'unknown'}")
    if as_bool(getattr(row, "published_original_candidate", False)) and not as_bool(getattr(row, "comparator_only", False)):
        source_rows.add(f"{row_source}_main:{source_corpus or 'unknown'}")
    note = (
        f"D-vs-N corpus source: {source_corpus}; unit_id: {unit_id}; "
        f"published_original_candidate={as_bool(getattr(row, 'published_original_candidate', False))}; "
        f"comparator_only={as_bool(getattr(row, 'comparator_only', False))}"
    )
    if title_is_placeholder:
        note += "; title missing in local candidate table"
    return BibEntry(
        key=key,
        entry_type=entry_type,
        title=title,
        authors=authors,
        year=year,
        journal=journal,
        doi=doi,
        url=f"https://doi.org/{doi}" if doi else "",
        pmid=pmid,
        pmcid=pmcid,
        note=note,
        metadata_source="local_placeholder" if title_is_placeholder else "local",
        source_rows=source_rows,
    )


def corpus_from_candidate_papers(entries: dict[str, BibEntry], audit: list[dict[str, object]]) -> None:
    if not PUBLISHED_PAPERS.exists():
        return
    df = pd.read_csv(PUBLISHED_PAPERS)
    before = len(entries)
    titled_rows = 0
    untitled_rows = 0
    main_rows = 0
    for row in df.itertuples(index=False):
        entry = candidate_entry_from_row(row, "candidate_d_n_papers")
        if entry is None:
            continue
        if entry.metadata_source == "local_placeholder":
            untitled_rows += 1
        else:
            titled_rows += 1
        if as_bool(getattr(row, "published_original_candidate", False)) and not as_bool(getattr(row, "comparator_only", False)):
            main_rows += 1
        add_entry(entries, entry)
    audit.append(
        {
            "source": "candidate_d_n_papers_all",
            "input_rows": len(df),
            "candidate_entries": len(entries) - before,
            "titled_rows": titled_rows,
            "untitled_rows": untitled_rows,
            "main_subset_rows": main_rows,
        }
    )


def corpus_from_candidate_studies(entries: dict[str, BibEntry], audit: list[dict[str, object]]) -> None:
    if not CANDIDATE_STUDIES.exists():
        return
    df = pd.read_csv(CANDIDATE_STUDIES)
    before = len(entries)
    candidate_entries = 0
    for row in df.itertuples(index=False):
        title_raw = clean_text(getattr(row, "title", ""))
        if not title_raw:
            continue
        entry = candidate_entry_from_row(row, "candidate_d_n_studies")
        if entry is None:
            continue
        current_len = len(entries)
        add_entry(entries, entry)
        if len(entries) > current_len:
            candidate_entries += 1
    audit.append({"source": "candidate_d_n_studies_title_fallback", "input_rows": len(df), "candidate_entries": candidate_entries})


def corpus_from_replication_pairs(entries: dict[str, BibEntry], audit: list[dict[str, object]]) -> None:
    paths = [path for path in [REPLICATION_PAIRS, REPLICATION_ALL] if path.exists()]
    input_rows = 0
    candidate_entries = 0
    for path in paths:
        df = pd.read_csv(path)
        input_rows += len(df)
        for row in df.itertuples(index=False):
            source = clean_text(getattr(row, "source_dataset", "replication_pairs"))
            pair_id = clean_text(getattr(row, "pair_id", ""))
            for role in ["original", "replication"]:
                title = clean_text(getattr(row, f"{role}_title", ""))
                doi = extract_doi(getattr(row, f"{role}_doi", ""))
                if not title and not doi:
                    continue
                title_for_parse = title or doi
                authors, year, parsed_title, journal = parse_citation_like_title(title_for_parse)
                key = local_entry_key(f"repl_{role}", source, pair_id, parsed_title or title or doi)
                entry = BibEntry(
                    key=key,
                    entry_type="article",
                    title=parsed_title or title or doi,
                    authors=authors,
                    year=year,
                    journal=journal,
                    doi=doi,
                    url=f"https://doi.org/{doi}" if doi else "",
                    note=f"Replication-pair {role} paper; source_dataset: {source}; pair_id: {pair_id}",
                    source_rows={f"{path.relative_to(ROOT)}:{role}"},
                )
                add_entry(entries, entry)
                candidate_entries += 1
    audit.append({"source": "replication_pairs", "input_rows": input_rows, "candidate_entries": candidate_entries})


def corpus_from_package_reference_sources(entries: dict[str, BibEntry], audit: list[dict[str, object]]) -> None:
    if not PACKAGE_REFERENCE_SOURCES.exists():
        return
    df = pd.read_csv(PACKAGE_REFERENCE_SOURCES)
    candidate_entries = 0
    for row in df.itertuples(index=False):
        title = clean_text(getattr(row, "reference_title", ""))
        dois = clean_text(getattr(row, "dois", ""))
        pmids = clean_text(getattr(row, "pmids", ""))
        doi_values = [strip_doi_punctuation(x) for x in re.findall(DOI_RE, dois)]
        if not doi_values and dois:
            doi_values = [strip_doi_punctuation(x) for x in re.split(r"[;,]\s*", dois) if x.strip()]
        if not title and not doi_values and not pmids:
            continue
        for idx, doi in enumerate(doi_values or [""]):
            key = local_entry_key("cochrane_ref", title[:60], doi or pmids or idx)
            entry = BibEntry(
                key=key,
                entry_type="article",
                title=title or doi or pmids,
                doi=doi,
                url=f"https://doi.org/{doi}" if doi else "",
                pmid=pmids,
                note="Cochrane package reference source",
                source_rows={"package_reference_sources"},
            )
            add_entry(entries, entry)
            candidate_entries += 1
    audit.append({"source": "package_reference_sources", "input_rows": len(df), "candidate_entries": candidate_entries})


def corpus_from_clinifact(entries: dict[str, BibEntry], audit: list[dict[str, object]]) -> None:
    if not CLINIFACT_FULLTEXT.exists():
        return
    df = pd.read_csv(CLINIFACT_FULLTEXT)
    candidate_entries = 0
    for row in df.itertuples(index=False):
        title = clean_text(getattr(row, "article_title", ""))
        pmid = clean_text(getattr(row, "PMID", ""))
        pmcid = clean_text(getattr(row, "pmcid", ""))
        doi = extract_doi(getattr(row, "doi", ""))
        if not title and not pmid and not doi:
            continue
        key = local_entry_key("clinifact", pmid or doi or title[:60])
        entry = BibEntry(
            key=key,
            entry_type="article",
            title=title or doi or pmid,
            year=first_year(getattr(row, "publication_year", "")),
            doi=doi,
            url=f"https://doi.org/{doi}" if doi else "",
            pmid=pmid,
            pmcid=pmcid,
            note="CliniFact publication-bias direct-denominator source",
            source_rows={"clinifact_pmc_fulltext_extract"},
        )
        add_entry(entries, entry)
        candidate_entries += 1
    audit.append({"source": "clinifact_pmc_fulltext_extract", "input_rows": len(df), "candidate_entries": candidate_entries})


def corpus_from_fred(entries: dict[str, BibEntry], audit: list[dict[str, object]]) -> None:
    if not FRED_FLORA.exists():
        return
    df = pd.read_csv(FRED_FLORA)
    candidate_entries = 0
    for row in df.itertuples(index=False):
        for role in ["o", "r"]:
            title = clean_text(getattr(row, f"title_{role}", ""))
            doi = extract_doi(getattr(row, f"doi_{role}", ""), getattr(row, f"doi_{role}_alt", ""))
            if not title and not doi:
                continue
            key = local_entry_key(f"fred_{role}", doi or title[:60])
            year = clean_text(getattr(row, f"year_{role}", ""))
            if year.endswith(".0"):
                year = year[:-2]
            entry = BibEntry(
                key=key,
                entry_type="article",
                title=title or doi,
                authors=parse_author_literals(clean_text(getattr(row, f"author_{role}", ""))),
                year=year,
                journal=clean_text(getattr(row, f"journal_{role}", "")),
                volume=clean_text(getattr(row, f"volume_{role}", "")),
                number=clean_text(getattr(row, f"issue_{role}", "")),
                pages=clean_text(getattr(row, f"pages_{role}", "")),
                doi=doi,
                url=f"https://doi.org/{doi}" if doi else "",
                note=f"FReD/FLORA {'original' if role == 'o' else 'replication'} paper",
                source_rows={f"fred_flora:{role}"},
            )
            add_entry(entries, entry)
            candidate_entries += 1
    audit.append({"source": "fred_flora", "input_rows": len(df), "candidate_entries": candidate_entries})


def corpus_from_score(entries: dict[str, BibEntry], audit: list[dict[str, object]]) -> None:
    if not SCORE_METADATA.exists():
        return
    df = pd.read_csv(SCORE_METADATA)
    candidate_entries = 0
    for row in df.itertuples(index=False):
        title = clean_text(getattr(row, "title", ""))
        doi = extract_doi(getattr(row, "DOI", ""))
        if not title and not doi:
            continue
        last = clean_text(getattr(row, "author_last", ""))
        first = clean_text(getattr(row, "author_first", ""))
        authors = f"{last}, {first}".strip(", ") if last or first else ""
        key = local_entry_key("score", getattr(row, "paper_id", ""), doi or title[:60])
        entry = BibEntry(
            key=key,
            entry_type="article",
            title=title or doi,
            authors=authors,
            year=first_year(getattr(row, "pub_year", "")),
            volume=clean_text(getattr(row, "volume", "")),
            number=clean_text(getattr(row, "issue", "")),
            pages=clean_text(getattr(row, "pg", "")),
            doi=doi,
            url=f"https://doi.org/{doi}" if doi else "",
            note="SCORE/COS claims paper metadata",
            source_rows={"score_paper_metadata"},
        )
        add_entry(entries, entry)
        candidate_entries += 1
    audit.append({"source": "score_paper_metadata", "input_rows": len(df), "candidate_entries": candidate_entries})


def corpus_from_statcheck(entries: dict[str, BibEntry], audit: list[dict[str, object]]) -> None:
    if STATCHECK_PAPERS.exists():
        df = pd.read_csv(STATCHECK_PAPERS)
        before = len(entries)
        for row in df.itertuples(index=False):
            paper_id = clean_text(getattr(row, "paper_id", ""))
            journal_code = clean_text(getattr(row, "journal", ""))
            journal = STATCHECK_JOURNALS.get(journal_code, journal_code)
            year = compact_year(getattr(row, "year", ""))
            title = placeholder_title("psychology_statcheck", paper_id or "unknown_paper", year, journal)
            key = local_entry_key("statcheck", paper_id or title[:40])
            entry = BibEntry(
                key=key,
                entry_type="article" if journal or year else "misc",
                title=title,
                year=year,
                journal=journal,
                note="Local statcheck paper inventory row; source file has journal/year/paper_id but no title or DOI metadata.",
                metadata_source="local_placeholder",
                source_rows={"psychology_statcheck", "statcheck_published_papers", f"psychology_statcheck:{paper_id}"},
            )
            add_entry(entries, entry)
        audit.append({"source": "statcheck_published_papers", "input_rows": len(df), "candidate_entries": len(entries) - before})

    if STATCHECK_RAW.exists():
        raw = pd.read_csv(
            STATCHECK_RAW,
            sep=";",
            encoding="latin1",
            usecols=["Source", "journals.jour.", "years.y."],
        ).drop_duplicates()
        raw = raw.rename(columns={"journals.jour.": "journal_code", "years.y.": "year_value"})
        published_lookup = statcheck_published_lookup()
        multiplicity = statcheck_source_multiplicity()
        before = len(entries)
        for row in raw.to_dict("records"):
            journal_code = clean_text(row.get("journal_code"))
            paper_id = statcheck_inventory_paper_id(
                row.get("Source"),
                journal_code,
                row.get("year_value"),
                published_lookup,
                multiplicity,
            )
            journal = STATCHECK_JOURNALS.get(journal_code, journal_code)
            year = compact_year(row.get("year_value"))
            title = placeholder_title("psychology_statcheck", paper_id or "unknown_paper", year, journal)
            key = local_entry_key("statcheck", paper_id or title[:40])
            entry = BibEntry(
                key=key,
                entry_type="article" if journal or year else "misc",
                title=title,
                year=year,
                journal=journal,
                note="Local raw statcheck inventory row; source file has journal/year/paper_id but no title or DOI metadata.",
                metadata_source="local_placeholder",
                source_rows={"psychology_statcheck", "statcheck_raw_inventory", f"psychology_statcheck:{paper_id}"},
            )
            add_entry(entries, entry)
        audit.append({"source": "statcheck_raw_inventory", "input_rows": len(raw), "candidate_entries": len(entries) - before})


def apply_structured_enrichment(target: BibEntry, enriched: BibEntry) -> None:
    enriched.note = target.note
    target.merge(enriched)
    for attr in [
        "entry_type",
        "title",
        "authors",
        "year",
        "journal",
        "booktitle",
        "publisher",
        "volume",
        "number",
        "pages",
        "doi",
        "url",
        "pmid",
        "pmcid",
    ]:
        value = getattr(enriched, attr)
        if value:
            setattr(target, attr, value)
    target.metadata_source = enriched.metadata_source
    target.crossref_score = enriched.crossref_score


def metabus_article_id_from_entry(entry: BibEntry) -> str:
    for candidate in [entry.title, entry.note, " ".join(sorted(entry.source_rows))]:
        match = METABUS_ARTICLE_ID_RE.search(clean_text(candidate))
        if match:
            return match.group(0)
    return ""


def enrich_corpus_entries(entries: list[BibEntry], refresh: bool) -> list[BibEntry]:
    metabus_cache: dict[str, BibEntry | None] = {}
    pmcid_cache: dict[str, BibEntry | None] = {}
    statcheck_matches = load_statcheck_exact_match_lookup(refresh=refresh)
    statcheck_cache: dict[str, BibEntry | None] = {}
    for entry in entries:
        if entry.metadata_source != "local_placeholder":
            continue
        if entry_has_source(entry, ["candidate_d_n_papers:metabus_open_bosco", "candidate_d_n_studies:metabus_open_bosco"]):
            article_id = metabus_article_id_from_entry(entry)
            if article_id not in metabus_cache:
                item, score = crossref_by_metabus_article(article_id, entry.year, refresh)
                metabus_cache[article_id] = entry_from_crossref(entry.key, item, score) if item is not None else None
            enriched = metabus_cache.get(article_id)
            if enriched is not None:
                apply_structured_enrichment(entry, enriched)
        elif entry_has_source(entry, ["candidate_d_n_papers:yun_llm_meta_analysis", "candidate_d_n_studies:yun_llm_meta_analysis"]):
            pmcid = clean_text(entry.pmcid).upper()
            if not pmcid:
                continue
            if pmcid not in pmcid_cache:
                europe_item = europepmc_by_pmcid(pmcid, refresh)
                enriched: BibEntry | None = None
                if europe_item is not None:
                    europe_entry = entry_from_europepmc(entry.key, europe_item)
                    crossref_item = crossref_by_doi(europe_entry.doi, refresh) if europe_entry.doi else None
                    if crossref_item is not None:
                        enriched = entry_from_crossref(entry.key, crossref_item, 1.0)
                        enriched.pmid = europe_entry.pmid
                        enriched.pmcid = europe_entry.pmcid
                    else:
                        enriched = europe_entry
                pmcid_cache[pmcid] = enriched
            enriched = pmcid_cache.get(pmcid)
            if enriched is not None:
                apply_structured_enrichment(entry, enriched)
        elif entry_has_source(entry, ["psychology_statcheck", "statcheck_published_papers"]):
            paper_id = statcheck_paper_id_from_entry(entry)
            if not paper_id:
                continue
            if paper_id not in statcheck_cache:
                match = statcheck_matches.get(paper_id)
                statcheck_cache[paper_id] = entry_from_statcheck_match(entry.key, match) if match is not None else None
            enriched = statcheck_cache.get(paper_id)
            if enriched is not None:
                apply_structured_enrichment(entry, enriched)
                if entry.metadata_source == "hartgerink_statcheck":
                    entry.note = "Matched to Hartgerink statcheck metadata via exact raw-stat signature."
    return entries


def build_corpus_bibliography(refresh: bool = False) -> tuple[list[BibEntry], list[dict[str, object]]]:
    entries: dict[str, BibEntry] = {}
    audit: list[dict[str, object]] = []
    corpus_from_candidate_papers(entries, audit)
    corpus_from_candidate_studies(entries, audit)
    corpus_from_replication_pairs(entries, audit)
    corpus_from_package_reference_sources(entries, audit)
    corpus_from_clinifact(entries, audit)
    corpus_from_fred(entries, audit)
    corpus_from_score(entries, audit)
    corpus_from_statcheck(entries, audit)
    return sorted(enrich_corpus_entries(list(entries.values()), refresh), key=lambda x: x.key), audit


def source_row_membership(entry: BibEntry, prefixes: Iterable[str]) -> bool:
    return entry_has_source(entry, prefixes)


def build_corpus_coverage(entries: list[BibEntry], harvest_audit: list[dict[str, object]]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    peer_lookup: dict[str, dict[str, object]] = {}
    if PEER_REVIEWED_SOURCE_LIST.exists():
        peer_df = pd.read_csv(PEER_REVIEWED_SOURCE_LIST).fillna("")
        for row in peer_df.to_dict("records"):
            source = clean_text(row.get("source_corpus"))
            if source:
                peer_lookup[source] = row
            elif clean_text(row.get("name")):
                rows.append(
                    {
                        "source_name": clean_text(row.get("name")),
                        "source_type": "peer_reviewed_inventory_only",
                        "input_rows": row.get("n_rows", ""),
                        "n_papers_reported": row.get("n_papers", ""),
                        "bib_entries": 0,
                        "placeholder_entries": 0,
                        "status": "unresolved_source_only",
                        "notes": clean_text(row.get("notes")),
                    }
                )

    candidate_df = pd.read_csv(PUBLISHED_PAPERS) if PUBLISHED_PAPERS.exists() else pd.DataFrame()
    sources = set(candidate_df["source_corpus"].dropna().astype(str)) if not candidate_df.empty else set()
    sources.update(peer_lookup)
    for source in sorted(source for source in sources if clean_text(source)):
        sub = candidate_df[candidate_df["source_corpus"].fillna("") == source].copy() if not candidate_df.empty else pd.DataFrame()
        titles = sub["title"].fillna("").astype(str).str.strip() if not sub.empty else pd.Series(dtype=str)
        input_rows = len(sub)
        titled_rows = int(titles.ne("").sum()) if not sub.empty else 0
        untitled_rows = int(titles.eq("").sum()) if not sub.empty else 0
        tagged_prefixes = [f"candidate_d_n_papers:{source}", f"candidate_d_n_studies:{source}"]
        if source == "psychology_statcheck":
            tagged_prefixes.extend(["psychology_statcheck", "statcheck_published_papers", "statcheck_raw_inventory"])
            if STATCHECK_RAW.exists():
                statcheck_df = pd.read_csv(
                    STATCHECK_RAW,
                    sep=";",
                    encoding="latin1",
                    usecols=["Source", "journals.jour.", "years.y."],
                ).drop_duplicates()
                input_rows = len(statcheck_df)
                titled_rows = 0
                untitled_rows = input_rows
            elif STATCHECK_PAPERS.exists():
                statcheck_df = pd.read_csv(STATCHECK_PAPERS, usecols=["paper_id"])
                input_rows = len(statcheck_df)
                titled_rows = 0
                untitled_rows = input_rows
        matching_entries = [entry for entry in entries if source_row_membership(entry, tagged_prefixes)]
        placeholder_entries = sum(1 for entry in matching_entries if entry.metadata_source == "local_placeholder")
        peer_row = peer_lookup.get(source, {})
        if source == "szucs_ioannidis_2017":
            status = "blocked_no_local_paper_ids"
            if not input_rows:
                input_rows = peer_row.get("n_rows", "")
        elif matching_entries and 0 < placeholder_entries < len(matching_entries):
            status = "covered_mixed_real_and_placeholder"
        elif matching_entries and placeholder_entries == len(matching_entries):
            status = "covered_with_placeholders_only"
        elif matching_entries:
            status = "covered_with_local_metadata"
        else:
            status = "not_harvested"
        note_bits = [clean_text(peer_row.get("notes"))]
        if untitled_rows:
            if source == "psychology_statcheck":
                note_bits.append(
                    f"{untitled_rows} local statcheck inventory rows lack titles locally; {placeholder_entries} remain placeholder entries after enrichment."
                )
            else:
                note_bits.append(
                    f"{untitled_rows} candidate-paper rows lack titles locally; {placeholder_entries} remain placeholder entries after enrichment."
                )
        if source == "psychology_statcheck":
            exact_matches = sum(1 for entry in matching_entries if source_row_membership(entry, ["hartgerink_statcheck_exact"]))
            if exact_matches:
                note_bits.append(f"{exact_matches} papers matched to the Hartgerink statcheck metadata deposit by exact raw-stat signature.")
        if source == "szucs_ioannidis_2017":
            note_bits.append("Local source only exposes row-level test statistics; paper grouping and titles are not decoded yet.")
        rows.append(
            {
                "source_name": source,
                "source_type": "candidate_source_corpus",
                "input_rows": input_rows,
                "n_papers_reported": peer_row.get("n_papers", ""),
                "bib_entries": len(matching_entries),
                "placeholder_entries": placeholder_entries,
                "titled_rows": titled_rows,
                "untitled_rows": untitled_rows,
                "status": status,
                "notes": " ".join(bit for bit in note_bits if bit),
            }
        )

    extra_counts = {
        "replication_pairs": sum(1 for entry in entries if source_row_membership(entry, [str(REPLICATION_PAIRS.relative_to(ROOT)), str(REPLICATION_ALL.relative_to(ROOT))])),
        "package_reference_sources": sum(1 for entry in entries if source_row_membership(entry, ["package_reference_sources"])),
        "clinifact_pmc_fulltext_extract": sum(1 for entry in entries if source_row_membership(entry, ["clinifact_pmc_fulltext_extract"])),
        "fred_flora": sum(1 for entry in entries if source_row_membership(entry, ["fred_flora"])),
        "score_paper_metadata": sum(1 for entry in entries if source_row_membership(entry, ["score_paper_metadata"])),
        "statcheck_raw_inventory": sum(1 for entry in entries if source_row_membership(entry, ["statcheck_raw_inventory"])),
        "hartgerink_statcheck_exact": sum(1 for entry in entries if source_row_membership(entry, ["hartgerink_statcheck_exact"])),
    }
    audit_lookup = {clean_text(row.get("source")): row for row in harvest_audit}
    for source_name, bib_entries in extra_counts.items():
        audit_row = audit_lookup.get(source_name, {})
        if not bib_entries and not audit_row:
            continue
        placeholder_entries = sum(
            1
            for entry in entries
            if entry.metadata_source == "local_placeholder"
            and source_row_membership(entry, [source_name, "statcheck_published_papers"] if source_name == "psychology_statcheck" else [source_name])
        )
        rows.append(
            {
                "source_name": source_name,
                "source_type": "auxiliary_harvest",
                "input_rows": audit_row.get("input_rows", ""),
                "n_papers_reported": "",
                "bib_entries": bib_entries,
                "placeholder_entries": placeholder_entries,
                "titled_rows": "",
                "untitled_rows": "",
                "status": "covered_with_placeholders_only" if placeholder_entries and placeholder_entries == bib_entries else "covered_with_local_metadata",
                "notes": clean_text(
                    "Local statcheck paper inventory rows lack titles/DOIs."
                    if source_name == "psychology_statcheck"
                    else "Full raw statcheck inventory rows harvested from the original Source/journal/year file, including papers outside the filtered analysis subset."
                    if source_name == "statcheck_raw_inventory"
                    else "Exact raw-stat signature matches between local psychology_statcheck IDs and the Hartgerink statcheck metadata deposit."
                    if source_name == "hartgerink_statcheck_exact"
                    else ""
                ),
            }
        )
    return rows


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames: list[str] = []
    seen: set[str] = set()
    for row in rows:
        for key in row.keys():
            if key not in seen:
                seen.add(key)
                fieldnames.append(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_csl_json(entries: list[BibEntry]) -> None:
    """Keep the old CSL JSON output around for comparison/debugging."""
    items = []
    for entry in entries:
        item = {
            "id": entry.key,
            "type": "article-journal" if entry.entry_type == "article" else "webpage",
            "title": entry.title,
        }
        if entry.authors:
            author_text = entry.authors.removeprefix("literal:")
            item["author"] = [{"literal": part.strip()} for part in re.split(r"\s+and\s+", author_text) if part.strip()]
        if entry.year:
            item["issued"] = {"date-parts": [[int(entry.year)]]} if entry.year.isdigit() else {"raw": entry.year}
        if entry.journal:
            item["container-title"] = entry.journal
        if entry.doi:
            item["DOI"] = entry.doi
        if entry.url:
            item["URL"] = entry.url
        items.append(item)
    PAPER_CSL_JSON.write_text(json.dumps(items, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--refresh-metadata",
        action="store_true",
        help="Query Crossref for paper-reference metadata and update data/cache/bibliography.",
    )
    parser.add_argument(
        "--refresh-corpus-metadata",
        action="store_true",
        help="Refresh targeted corpus metadata caches for identifiable placeholder sources such as metabus and PMCID-based corpora.",
    )
    args = parser.parse_args()

    ensure_dirs()
    paper_entries = enrich_paper_references(parse_draft_references(), refresh=args.refresh_metadata)
    paper_entries = apply_manual_paper_overrides(paper_entries)
    write_bib(PAPER_BIB, paper_entries)
    write_csl_json(paper_entries)
    write_csv(PAPER_REFERENCES_CSV, entries_to_rows(paper_entries))

    corpus_entries, audit = build_corpus_bibliography(refresh=args.refresh_corpus_metadata)
    write_bib(CORPUS_BIB, corpus_entries)
    write_csv(CORPUS_REFERENCES_CSV, entries_to_rows(corpus_entries))
    write_csv(CORPUS_SOURCE_AUDIT, audit)
    write_csv(CORPUS_COVERAGE_AUDIT, build_corpus_coverage(corpus_entries, audit))

    crossref_count = sum(1 for entry in paper_entries if entry.metadata_source == "crossref")
    doi_count = sum(1 for entry in paper_entries if entry.doi)
    corpus_doi_count = sum(1 for entry in corpus_entries if entry.doi)
    print(
        "Built bibliographies: "
        f"{len(paper_entries)} paper refs ({crossref_count} Crossref-enriched, {doi_count} with DOI); "
        f"{len(corpus_entries)} corpus refs ({corpus_doi_count} with DOI)."
    )


if __name__ == "__main__":
    main()
